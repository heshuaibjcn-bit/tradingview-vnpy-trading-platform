#!/usr/bin/env python3
"""
TradingView Web 整合服务器 - 使用端口 8080
以 TradingView Web 界面为主框架，整合 vnpy 完整功能
"""
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import logging
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest, SubscribeRequest
from vnpy.trader.constant import Exchange, Direction, OrderType
from vnpy_gateway_eastmoney import EastmoneyGateway

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnpy-tradingview-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
main_engine = None
gateway_name = "EM"


class VnpyTradingService:
    """vnpy 交易服务"""

    def __init__(self):
        self.main_engine = None
        self.connected = False
        self.init_vnpy()

    def init_vnpy(self):
        """初始化 vnpy"""
        try:
            logger.info("=" * 60)
            logger.info("初始化 vnpy 主引擎...")
            self.main_engine = MainEngine()
            self.main_engine.add_gateway(EastmoneyGateway)
            logger.info("✅ vnpy 初始化成功")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ vnpy 初始化失败: {e}")

    def connect_gateway(self, setting):
        """连接网关"""
        try:
            logger.info("正在连接东财网关...")
            self.main_engine.connect(setting, gateway_name)
            self.connected = True
            logger.info("✅ 网关连接成功")
            return True, "连接成功"
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False, str(e)

    def send_order(self, order_data):
        """发送订单"""
        try:
            logger.info(f"创建订单: {order_data}")
            order_req = OrderRequest(
                symbol=order_data['symbol'],
                exchange=Exchange(order_data['exchange']),
                direction=Direction(order_data['direction']),
                type=OrderType(order_data.get('type', 'LIMIT')),
                volume=int(order_data['volume']),
                price=float(order_data['price'])
            )

            vt_orderid = self.main_engine.send_order(order_req, gateway_name)
            logger.info(f"✅ 订单已发送: {vt_orderid}")
            return True, {'orderid': vt_orderid}

        except Exception as e:
            logger.error(f"❌ 下单失败: {e}")
            return False, str(e)

    def cancel_order(self, orderid, symbol, exchange):
        """撤销订单"""
        try:
            from vnpy.trader.object import CancelRequest
            cancel_req = CancelRequest(
                orderid=orderid,
                symbol=symbol,
                exchange=Exchange(exchange)
            )
            self.main_engine.cancel_order(cancel_req, gateway_name)
            logger.info(f"✅ 撤单请求已发送: {orderid}")
            return True, "撤单请求已发送"
        except Exception as e:
            logger.error(f"❌ 撤单失败: {e}")
            return False, str(e)

    def get_account(self):
        """获取账户信息"""
        try:
            self.main_engine.query_account(gateway_name)
            accounts = self.main_engine.get_all_accounts()
            return [acc.__dict__ for acc in accounts]
        except Exception as e:
            logger.error(f"❌ 查询账户失败: {e}")
            return []

    def get_position(self):
        """获取持仓"""
        try:
            self.main_engine.query_position(gateway_name)
            positions = self.main_engine.get_all_positions()
            return [pos.__dict__ for pos in positions]
        except Exception as e:
            logger.error(f"❌ 查询持仓失败: {e}")
            return []

    def get_orders(self):
        """获取订单"""
        try:
            orders = self.main_engine.get_all_orders()
            return [order.__dict__ for order in orders]
        except Exception as e:
            logger.error(f"❌ 查询订单失败: {e}")
            return []


# 创建服务实例
trading_service = VnpyTradingService()
main_engine = trading_service.main_engine


# ==================== Flask 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('tradingview_integrated.html')


@app.route('/api/status')
def api_status():
    """系统状态"""
    return jsonify({
        'status': 'running',
        'vnpy_connected': trading_service.main_engine is not None,
        'gateway_connected': trading_service.connected,
        'version': '1.0.0'
    })


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """连接网关"""
    data = request.get_json()
    setting = {
        'username': data.get('username', ''),
        'password': data.get('password', ''),
        'cookie': data.get('cookie', '')
    }

    logger.info(f"收到连接请求: {data.get('username')}")
    success, message = trading_service.connect_gateway(setting)
    return jsonify({'success': success, 'message': message})


@app.route('/api/account')
def api_account():
    """获取账户"""
    accounts = trading_service.get_account()
    return jsonify({'accounts': accounts})


@app.route('/api/position')
def api_position():
    """获取持仓"""
    positions = trading_service.get_position()
    return jsonify({'positions': positions})


@app.route('/api/orders')
def api_orders():
    """获取订单"""
    orders = trading_service.get_orders()
    return jsonify({'orders': orders})


@app.route('/api/order', methods=['POST'])
def api_send_order():
    """发送订单"""
    data = request.get_json()
    success, result = trading_service.send_order(data)
    return jsonify({'success': success, 'result': result})


@app.route('/api/cancel', methods=['POST'])
def api_cancel_order():
    """撤销订单"""
    data = request.get_json()
    success, result = trading_service.cancel_order(
        data['orderid'],
        data['symbol'],
        data['exchange']
    )
    return jsonify({'success': success, 'message': result})


@app.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    """订阅行情"""
    try:
        data = request.get_json()
        req = SubscribeRequest(
            symbol=data['symbol'],
            exchange=Exchange(data['exchange'])
        )
        main_engine.subscribe(req, gateway_name)
        logger.info(f"订阅行情: {data['symbol']}")
        return jsonify({'success': True, 'message': '订阅成功'})
    except Exception as e:
        logger.error(f"订阅失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ==================== WebSocket 事件 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info('✅ WebSocket 客户端已连接')
    emit('response', {'message': '已连接到服务器', 'type': 'info'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    logger.info('WebSocket 客户端已断开')


@socketio.on('refresh_data')
def handle_refresh():
    """刷新数据"""
    logger.info('刷新数据请求')

    # 发送账户信息
    accounts = trading_service.get_account()
    emit('account', {'accounts': accounts})

    # 发送持仓信息
    positions = trading_service.get_position()
    emit('position', {'positions': positions})

    # 发送订单信息
    orders = trading_service.get_orders()
    emit('orders', {'orders': orders})


# ==================== 主程序 ====================

def main():
    """主函数"""
    port = 8080
    logger.info("=" * 60)
    logger.info("TradingView + vnpy Web 整合服务器")
    logger.info("=" * 60)
    logger.info(f"服务器地址: http://localhost:{port}")
    logger.info(f"API 文档: http://localhost:{port}/api/status")
    logger.info("=" * 60)
    logger.info("✅ 服务器启动中...")
    logger.info("按 Ctrl+C 停止服务器")
    logger.info("=" * 60)

    # 启动服务器
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("服务器已停止")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
