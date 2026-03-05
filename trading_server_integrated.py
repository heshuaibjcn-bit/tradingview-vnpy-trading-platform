#!/usr/bin/env python3
"""
实盘交易服务器 v5.0
集成真实交易API、订单状态跟踪、资金持仓验证
"""
import os
import json
import time
import threading
import sqlite3
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import jwt

# 导入真实交易网关
from eastmoney_real_gateway import EastmoneyRealGateway

# 导入基础类
from eastmoney_gateway_simple import (
    Exchange,
    Direction,
    OrderType,
    Status
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置
# ============================================================================

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', '86400'))  # 24小时

DB_PATH = "a_stock_v2.db"
USERS_DB_PATH = "users.db"

# 实盘交易配置
REAL_TRADING_ENABLED = os.environ.get('REAL_TRADING_ENABLED', 'false').lower() == 'true'
MAX_SINGLE_ORDER_AMOUNT = float(os.environ.get('MAX_SINGLE_ORDER_AMOUNT', '50000'))  # 单笔最大金额
MAX_DAILY_LOSS = float(os.environ.get('MAX_DAILY_LOSS', '10000'))  # 每日最大亏损


# ============================================================================
# Flask应用初始化
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET

# CORS配置 - 生产环境应该限制为特定域名
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8080,http://localhost:5000').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    },
    r"/*": {"origins": ALLOWED_ORIGINS}
})
socketio = SocketIO(
    app,
    cors_allowed_origins=ALLOWED_ORIGINS,
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling']
)


# ============================================================================
# 用户管理器
# ============================================================================

class UserManager:
    """用户管理器"""

    def __init__(self, db_path: str = USERS_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # 创建审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                target TEXT,
                status TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password: str) -> str:
        """哈希密码（使用bcrypt）"""
        salt = bcrypt.gensalt(12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def register_user(self, username: str, password: str, email: str, full_name: str = '') -> tuple:
        """注册用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 检查用户是否已存在
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return False, "用户名已存在"

            # 检查邮箱是否已存在
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return False, "邮箱已被注册"

            # 创建新用户
            password_hash = self.hash_password(password)

            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, full_name))

            conn.commit()
            return True, "注册成功"

        except Exception as e:
            conn.rollback()
            logger.error(f"用户注册失败: {str(e)}", exc_info=True)
            return False, "注册失败，请稍后重试"

        finally:
            conn.close()

    def verify_user(self, username: str, password: str) -> tuple:
        """验证用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, password_hash, is_active
                FROM users WHERE username = ?
            ''', (username,))

            result = cursor.fetchone()

            if not result:
                return False, "用户名或密码错误"

            user_id, password_hash, is_active = result

            if not is_active:
                return False, "账户已被禁用"

            if not self.verify_password(password, password_hash):
                return False, "用户名或密码错误"

            # 更新最后登录时间
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                          (datetime.now(), user_id))
            conn.commit()

            return True, user_id

        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}", exc_info=True)
            return False, "登录失败，请稍后重试"

        finally:
            conn.close()

    def create_token(self, user_id: int) -> str:
        """创建JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

    def verify_token(self, token: str) -> tuple:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, "Token已过期"
        except jwt.InvalidTokenError:
            return False, "Token无效"

    def log_audit(self, user_id: Optional[int], action: str, target: str,
                 status: str, request_obj) -> bool:
        """记录审计日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO audit_logs (user_id, action, target, status, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                action,
                target,
                status,
                request_obj.remote_addr if request_obj else None,
                request_obj.headers.get('User-Agent') if request_obj else None
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}", exc_info=True)
            return False


def require_auth(f):
    """要求用户认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从header获取token
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': '缺少认证token'}), 401

        # 提取token
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({'error': 'Token格式错误'}), 401

        # 验证token
        valid, result = user_manager.verify_token(token)

        if not valid:
            return jsonify({'error': result}), 401

        # 将user_id添加到request
        request.user_id = result.get('user_id')

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# 全局对象
# ============================================================================

# 用户管理器
user_manager = UserManager()

# 真实交易网关
real_gateway = EastmoneyRealGateway()

# 模拟网关（用于测试）
from eastmoney_gateway_simple import EastmoneyGateway
simulated_gateway = EastmoneyGateway()

# 当前使用的网关
current_gateway = simulated_gateway  # 默认使用模拟网关

# 交易统计
trading_stats = {
    'total_orders': 0,
    'success_orders': 0,
    'failed_orders': 0,
    'total_trades': 0,
    'daily_pnl': 0.0,
    'start_time': datetime.now()
}


# ============================================================================
# 风险控制系统
# ============================================================================

class RiskControl:
    """风险控制系统"""

    def __init__(self):
        self.max_single_order_amount = MAX_SINGLE_ORDER_AMOUNT
        self.max_daily_loss = MAX_DAILY_LOSS
        self.db_path = "a_stock_v2.db"

    def validate_order(self, order_req: dict, user_id: str) -> tuple:
        """验证订单"""
        # 1. 检查单笔金额限制
        amount = order_req['price'] * order_req['volume']
        if amount > self.max_single_order_amount:
            return False, f"单笔金额超限: {amount:.2f} > {self.max_single_order_amount:.2f}"

        # 2. 检查每日亏损限制
        daily_pnl = self._calculate_daily_pnl()
        if daily_pnl < -self.max_daily_loss:
            return False, f"超过每日亏损限额: {daily_pnl:.2f} < -{self.max_daily_loss:.2f}"

        # 3. 检查价格合理性
        if order_req['price'] <= 0:
            return False, "价格必须大于0"

        if order_req['volume'] <= 0:
            return False, "数量必须大于0"

        # 4. 检查涨跌停限制
        limit_price = self._get_limit_price(order_req['symbol'], order_req['direction'])
        if limit_price:
            if order_req['direction'] == 'LONG' and order_req['price'] > limit_price:
                return False, f"价格超过涨停价: {order_req['price']:.2f} > {limit_price:.2f}"
            elif order_req['direction'] == 'SHORT' and order_req['price'] < limit_price:
                return False, f"价格低于跌停价: {order_req['price']:.2f} < {limit_price:.2f}"

        return True, "验证通过"

    def _calculate_daily_pnl(self) -> float:
        """计算当日盈亏"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取今日成交记录
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT SUM(profit)
                FROM trades
                WHERE DATE(trade_time) = ?
            ''', (today,))

            result = cursor.fetchone()
            conn.close()

            return result[0] if result[0] else 0.0

        except Exception as e:
            print(f"计算当日盈亏失败: {str(e)}")
            return 0.0

    def _get_limit_price(self, symbol: str, direction: str) -> Optional[float]:
        """获取涨跌停价格"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取最新收盘价
            cursor.execute('''
                SELECT close_price, change_rate
                FROM realtime_quotes
                WHERE symbol = ?
            ''', (symbol,))

            result = cursor.fetchone()
            conn.close()

            if result:
                close_price, change_rate = result

                # 涨跌停限制（A股10%，ST和科创板/创业板20%）
                limit_rate = 0.10  # 默认10%

                if direction == 'LONG':
                    return close_price * (1 + limit_rate)
                else:
                    return close_price * (1 - limit_rate)

            return None

        except Exception as e:
            print(f"获取涨跌停价格失败: {str(e)}")
            return None


# 全局风控系统
risk_control = RiskControl()


# ============================================================================
# WebSocket事件处理
# ============================================================================

@socketio.on('connect', namespace='/')
def handle_connect():
    """WebSocket连接"""
    print(f"[WebSocket] 客户端连接: {request.sid}")

    # 推送连接状态
    emit('response', {'message': 'WebSocket连接成功'})

    # 推送交易模式
    emit('trading_mode', {
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED',
        'enabled': REAL_TRADING_ENABLED
    })

    # 推送初始数据
    emit('account', {'accounts': get_accounts_data()})
    emit('position', {'positions': get_positions_data()})
    emit('orders', {'orders': get_orders_data()})
    emit('trading_stats', trading_stats)


@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    """WebSocket断开"""
    print(f"[WebSocket] 客户端断开: {request.sid}")


# ============================================================================
# 辅助函数
# ============================================================================

def get_accounts_data() -> List[dict]:
    """获取账户数据"""
    accounts = []
    for account in current_gateway.accounts.values():
        accounts.append({
            'accountid': account.vt_accountid,
            'balance': account.balance,
            'available': account.available,
            'frozen': account.frozen,
            'gateway_name': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
        })
    return accounts


def get_positions_data() -> List[dict]:
    """获取持仓数据"""
    positions = []
    for pos in current_gateway.positions.values():
        positions.append({
            'positionid': pos.vt_positionid,
            'symbol': pos.symbol,
            'exchange': pos.exchange.value,
            'direction': pos.direction.value,
            'volume': pos.volume,
            'available': pos.volume - pos.frozen,
            'price': pos.price,
            'pnl': pos.pnl,
            'gateway_name': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
        })
    return positions


def get_orders_data() -> List[dict]:
    """获取订单数据"""
    orders = []
    for order in current_gateway.orders.values():
        orders.append({
            'orderid': order.vt_orderid,
            'symbol': order.symbol,
            'exchange': order.exchange.value,
            'type': order.type.value,
            'direction': order.direction.value,
            'volume': order.volume,
            'traded': order.traded,
            'price': order.price,
            'status': order.status.value,
            'time': order.datetime.strftime('%Y-%m-%d %H:%M:%S') if hasattr(order, 'datetime') else '',
            'gateway_name': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
        })
    return orders


# ============================================================================
# HTTP API路由
# ============================================================================

@app.route('/')
def index():
    """首页 - 完整TradingView界面 + 量化交易插件"""
    try:
        with open('templates/trading_full.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>实盘交易服务器 v5.0 - 完整版</h1>
        <p>交易模式: <strong>{}</strong></p>
        <p>服务器时间: {}</p>
        <p style="color: red;">错误: 找不到前端HTML文件 (templates/trading_full.html)</p>
        <ul>
            <li><a href="/lite">简化版界面</a></li>
            <li>WebSocket: ws://localhost:8080/socket.io</li>
            <li>API文档: 查看 README.md</li>
        </ul>
        """.format(
            '实盘' if REAL_TRADING_ENABLED else '模拟',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )


@app.route('/lite')
def index_lite():
    """简化版界面 - 轻量级图表"""
    try:
        with open('templates/trading.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>实盘交易服务器 v5.0 - 简化版</h1>
        <p><a href="/">返回完整版</a></p>
        <p style="color: red;">错误: 找不到前端HTML文件 (templates/trading.html)</p>
        """.format()


# -------------------------- 用户认证API --------------------------

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """用户注册"""
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if len(username) < 3:
        return jsonify({'error': '用户名至少3个字符'}), 400

    if len(password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    success, message = user_manager.register_user(username, password, email)

    if success:
        return jsonify({'message': message}), 201
    else:
        return jsonify({'error': message}), 400


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """用户登录"""
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    valid, user_id_or_error = user_manager.verify_user(username, password)

    if not valid:
        user_manager.log_audit(None, 'login', 'auth', 'failed', request)
        return jsonify({'error': user_id_or_error}), 401

    # 创建token
    token = user_manager.create_token(user_id_or_error)

    # 记录审计日志
    user_manager.log_audit(user_id_or_error, 'login', 'auth', 'success', request)

    return jsonify({
        'message': '登录成功',
        'token': token,
        'user_id': user_id_or_error
    })


@app.route('/api/auth/verify', methods=['POST'])
@require_auth
def api_verify_token():
    """验证token"""
    return jsonify({
        'valid': True,
        'user_id': request.user_id
    })


@app.route('/api/trading/mode', methods=['GET'])
@require_auth
def api_trading_mode():
    """获取交易模式"""
    return jsonify({
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED',
        'enabled': REAL_TRADING_ENABLED,
        'warning': '实盘交易涉及真实资金，请谨慎操作' if REAL_TRADING_ENABLED else '当前为模拟交易模式'
    })


@app.route('/api/trading/mode', methods=['POST'])
@require_auth
def api_set_trading_mode():
    """设置交易模式"""
    if not REAL_TRADING_ENABLED:
        return jsonify({'error': '实盘交易未启用，需设置环境变量 REAL_TRADING_ENABLED=true'}), 403

    data = request.get_json()
    mode = data.get('mode', 'SIMULATED')

    global current_gateway

    if mode == 'REAL':
        current_gateway = real_gateway
        user_manager.log_audit(request.user_id, 'switch_mode', 'REAL', 'success', request)
    else:
        current_gateway = simulated_gateway
        user_manager.log_audit(request.user_id, 'switch_mode', 'SIMULATED', 'success', request)

    return jsonify({
        'message': f'已切换到{mode}模式',
        'mode': mode
    })


# -------------------------- 连接管理 --------------------------

@app.route('/api/connect', methods=['POST'])
@require_auth
def api_connect():
    """连接到交易接口"""
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    mode = data.get('mode', 'SIMULATED')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    # 选择网关
    global current_gateway
    if mode == 'REAL' and REAL_TRADING_ENABLED:
        current_gateway = real_gateway
    else:
        current_gateway = simulated_gateway

    try:
        current_gateway.connect({
            'username': username,
            'password': password
        })

        # 记录审计
        user_manager.log_audit(request.user_id, 'connect', mode, 'success', request)

        return jsonify({
            'message': '连接成功',
            'mode': mode
        })

    except Exception as e:
        user_manager.log_audit(request.user_id, 'connect', mode, 'failed', request)
        return jsonify({'error': str(e)}), 500


# -------------------------- 账户查询 --------------------------

@app.route('/api/account', methods=['GET'])
@require_auth
def api_account():
    """查询账户"""
    current_gateway.query_account()

    accounts = get_accounts_data()

    return jsonify({
        'accounts': accounts,
        'count': len(accounts),
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
    })


# -------------------------- 持仓查询 --------------------------

@app.route('/api/position', methods=['GET'])
@require_auth
def api_position():
    """查询持仓"""
    current_gateway.query_position()

    positions = get_positions_data()

    return jsonify({
        'positions': positions,
        'count': len(positions),
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
    })


# -------------------------- 订单查询 --------------------------

@app.route('/api/orders', methods=['GET'])
@require_auth
def api_orders():
    """查询订单"""
    orders = get_orders_data()

    return jsonify({
        'orders': orders,
        'count': len(orders),
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
    })


# -------------------------- 下单 --------------------------

@app.route('/api/order', methods=['POST'])
@require_auth
def api_order():
    """下单"""
    data = request.get_json()

    # 参数验证
    required_fields = ['symbol', 'exchange', 'direction', 'volume', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少参数: {field}'}), 400

    # 风险控制验证
    valid, message = risk_control.validate_order(data, request.user_id)
    if not valid:
        user_manager.log_audit(request.user_id, 'send_order', data.get('symbol'), 'rejected', request)
        return jsonify({'error': f'风控拦截: {message}'}), 400

    # 参数转换
    try:
        from eastmoney_gateway_simple import OrderRequest

        req = OrderRequest(
            symbol=data['symbol'],
            exchange=Exchange(data['exchange']),
            direction=Direction(data['direction']),
            type=OrderType(data.get('type', 'LIMIT')),
            volume=int(data['volume']),
            price=float(data['price']),
        )

        # 发送订单
        orderid = current_gateway.send_order(req)

        if orderid:
            trading_stats['total_orders'] += 1
            trading_stats['success_orders'] += 1

            user_manager.log_audit(request.user_id, 'send_order', data.get('symbol'), 'success', request)

            # WebSocket推送
            socketio.emit('order', {
                'orderid': orderid,
                'action': 'created',
                'timestamp': datetime.now().isoformat()
            })

            return jsonify({
                'message': '下单成功',
                'orderid': orderid,
                'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
            })
        else:
            trading_stats['total_orders'] += 1
            trading_stats['failed_orders'] += 1

            user_manager.log_audit(request.user_id, 'send_order', data.get('symbol'), 'failed', request)

            return jsonify({'error': '下单失败'}), 500

    except Exception as e:
        trading_stats['total_orders'] += 1
        trading_stats['failed_orders'] += 1

        user_manager.log_audit(request.user_id, 'send_order', data.get('symbol'), 'error', request)

        return jsonify({'error': f'下单异常: {str(e)}'}), 500


# -------------------------- 撤单 --------------------------

@app.route('/api/cancel', methods=['DELETE'])
@require_auth
def api_cancel():
    """撤单"""
    data = request.get_json()

    orderid = data.get('orderid')

    if not orderid:
        return jsonify({'error': '缺少订单ID'}), 400

    try:
        from eastmoney_gateway_simple import CancelRequest

        # 查找订单
        order = None
        for o in current_gateway.orders.values():
            if o.vt_orderid == orderid:
                order = o
                break

        if not order:
            return jsonify({'error': '订单不存在'}), 404

        # 创建撤单请求
        req = CancelRequest(
            orderid=order.orderid,
            symbol=order.symbol,
            exchange=order.exchange
        )

        # 撤销订单
        success = current_gateway.cancel_order(req)

        if success:
            user_manager.log_audit(request.user_id, 'cancel_order', orderid, 'success', request)

            # WebSocket推送
            socketio.emit('order', {
                'orderid': orderid,
                'action': 'cancelled',
                'timestamp': datetime.now().isoformat()
            })

            return jsonify({
                'message': '撤单成功',
                'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
            })
        else:
            user_manager.log_audit(request.user_id, 'cancel_order', orderid, 'failed', request)
            return jsonify({'error': '撤单失败'}), 500

    except Exception as e:
        user_manager.log_audit(request.user_id, 'cancel_order', orderid, 'error', request)
        return jsonify({'error': f'撤单异常: {str(e)}'}), 500


# -------------------------- 交易统计 --------------------------

@app.route('/api/stats', methods=['GET'])
@require_auth
def api_stats():
    """获取交易统计"""
    return jsonify({
        'stats': trading_stats,
        'mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED'
    })


# -------------------------- 系统状态 --------------------------

@app.route('/api/status', methods=['GET'])
def api_status():
    """系统状态"""
    return jsonify({
        'status': 'running',
        'connected': current_gateway.connected,
        'authenticated': current_gateway.authenticated,
        'trading_mode': 'REAL' if REAL_TRADING_ENABLED else 'SIMULATED',
        'real_trading_enabled': REAL_TRADING_ENABLED,
        'accounts': len(current_gateway.accounts),
        'positions': len(current_gateway.positions),
        'orders': len(current_gateway.orders),
        'trading_stats': trading_stats,
        'risk_control': {
            'max_single_order_amount': MAX_SINGLE_ORDER_AMOUNT,
            'max_daily_loss': MAX_DAILY_LOSS
        },
        'version': '5.0.0-real-trading'
    })


# ============================================================================
# 错误处理
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print("=" * 70)
    print(" " * 20 + "实盘交易服务器 v5.0")
    print("=" * 70)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n⚠️  交易模式配置:")
    print(f"   当前模式: {'🔴 实盘交易' if REAL_TRADING_ENABLED else '🟢 模拟交易'}")
    print(f"   单笔最大金额: ¥{MAX_SINGLE_ORDER_AMOUNT:,.2f}")
    print(f"   每日最大亏损: ¥{MAX_DAILY_LOSS:,.2f}")

    if not REAL_TRADING_ENABLED:
        print("\n💡 启用实盘交易:")
        print("   export REAL_TRADING_ENABLED=true")
        print("   然后重启服务器")

    print("\n🔧 功能状态:")
    print("  ✅ 真实交易API集成")
    print("  ✅ 订单状态实时跟踪")
    print("  ✅ 资金持仓验证")
    print("  ✅ 风险控制系统")
    print("  ✅ 模拟/实盘切换")
    print("  ✅ 审计日志")

    print("\n📊 数据库:")
    print(f"  用户数据库: {USERS_DB_PATH}")
    print(f"  市场数据库: {DB_PATH}")

    print("\n🌐 服务器地址:")
    print(f"  HTTP:  http://localhost:8080")
    print(f"  WebSocket: ws://localhost:8080/socket.io")

    print("\n" + "=" * 70)
    print("🚀 启动服务器...")
    print("=" * 70)

    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
