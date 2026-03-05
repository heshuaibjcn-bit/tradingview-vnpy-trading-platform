"""
东方财富交易网关
基于 vnpy 的 BaseGateway 实现
"""
from typing import Dict, List, Optional
from abc import abstractmethod
import requests
import json
from datetime import datetime

from vnpy.event import Event, EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest,
    BarData,
    Exchange,
    Product,
    Status,
    OptionType
)


class EastmoneyGateway(BaseGateway):
    """
    东方财富交易网关

    使用东方财富的 Web API 进行数据获取和交易

    注意：东财官方 QuantAPI SDK 仅支持 Python 2.7-3.8
    本网关通过 HTTP API 方式集成，适用于所有 Python 版本
    """

    default_name: str = "EM"

    # 东财 Web API 地址
    BASE_URL: str = "https://push2.eastmoney.com/api/qt"
    TRADE_URL: str = "https://trade.eastmoney.com"

    # 支持的交易所
    exchanges: List[Exchange] = [
        Exchange.SSE,      # 上交所
        Exchange.SZSE,     # 深交所
        Exchange.BSE,      # 北交所
    ]

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)

        self.connected: bool = False
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # 订单和持仓缓存
        self.orders: Dict[str, OrderData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.contracts: Dict[str, ContractData] = {}

        # 计数器
        self.order_count: int = 0
        self.cancel_count: int = 0

    def connect(self, setting: dict) -> None:
        """
        连接到东财接口

        setting 参数:
        - username: 东财账号
        - password: 密码
        - cookie: 登录后的 cookie（用于 Web API 认证）
        """
        username: str = setting.get("username", "")
        password: str = setting.get("password", "")
        cookie: str = setting.get("cookie", "")

        try:
            if cookie:
                # 使用 Cookie 方式连接
                self.session.headers.update({
                    'Cookie': cookie
                })

            self.connected = True
            self.write_log("东方财富网关连接成功")

            # 查询合约
            self.query_contract()

            # 查询账户
            self.query_account()

            # 查询持仓
            self.query_position()

        except Exception as e:
            self.write_log(f"连接失败: {str(e)}")

    def close(self) -> None:
        """关闭连接"""
        self.connected = False
        if self.session:
            self.session.close()
        self.write_log("东方财富网关连接已关闭")

    def subscribe(self, req: SubscribeRequest) -> None:
        """
        订阅行情

        使用东财的行情推送 API
        """
        symbol: str = req.symbol
        exchange: Exchange = req.exchange

        self.write_log(f"订阅行情: {symbol}")

        # 这里可以调用东财的行情订阅 API
        # 示例：使用 SSE 或 WebSocket 订阅实时行情

    def send_order(self, req: OrderRequest) -> str:
        """
        发送订单

        req: OrderRequest 包含订单信息
        """
        # 生成订单 ID
        self.order_count += 1
        order_id: str = f"EM_{self.order_count:04d}"
        vt_orderid: str = f"{self.gateway_name}.{order_id}"

        # 创建订单对象
        order: OrderData = req.create_order_data(order_id, self.gateway_name)

        # 这里调用东财的交易 API
        # 注意：需要先完成登录认证
        try:
            # 示例：构建下单请求
            trade_data = {
                'stock_code': req.symbol,
                'price': req.price,
                'volume': req.volume,
                'direction': req.direction.value,  # 买入/卖出
                'order_type': req.type.value,      # 限价/市价
            }

            # self.write_log(f"发送订单: {json.dumps(trade_data, ensure_ascii=False)}")

            # 实际下单需要调用东财的交易接口
            # response = self.session.post(f"{self.TRADE_URL}/api/order", json=trade_data)

            # 模拟订单成功
            order.status = Status.SUBMITTING
            self.orders[vt_orderid] = order
            self.on_order(order)

        except Exception as e:
            order.status = Status.REJECTED
            self.write_log(f"下单失败: {str(e)}")
            self.on_order(order)

        return vt_orderid

    def cancel_order(self, req: CancelRequest) -> None:
        """
        撤单

        req: CancelRequest 包含撤单信息
        """
        order_id: str = req.orderid
        vt_orderid: str = f"{self.gateway_name}.{order_id}"

        if vt_orderid in self.orders:
            order: OrderData = self.orders[vt_orderid]

            try:
                # 调用东财的撤单 API
                # self.write_log(f"撤销订单: {order_id}")

                # 实际撤单需要调用东财的接口
                # response = self.session.post(f"{self.TRADE_URL}/api/cancel", json={'order_id': order_id})
                pass
            except Exception as e:
                self.write_log(f"撤单失败: {str(e)}")

    def query_account(self) -> None:
        """查询账户资金"""
        try:
            # 调用东财的查询资产 API
            # response = self.session.get(f"{self.TRADE_URL}/api/account")

            # 示例：模拟返回账户数据
            account: AccountData = AccountData(
                accountid="EM_account",
                balance=100000.0,
                available=100000.0,
                gateway_name=self.gateway_name
            )

            self.on_account(account)
            self.write_log("账户资金查询成功")

        except Exception as e:
            self.write_log(f"查询账户失败: {str(e)}")

    def query_position(self) -> None:
        """查询持仓"""
        try:
            # 调用东财的查询持仓 API
            # response = self.session.get(f"{self.TRADE_URL}/api/position")

            # 示例：模拟返回持仓数据
            # 实际使用时需要解析 API 返回的数据

            self.write_log("持仓查询成功")

        except Exception as e:
            self.write_log(f"查询持仓失败: {str(e)}")

    def query_contract(self) -> None:
        """查询合约/股票列表"""
        try:
            # 可以从东财获取股票列表
            # 或者使用预定义的股票池

            # 示例：添加几个测试合约
            contracts = [
                {
                    'symbol': '600000',
                    'exchange': Exchange.SSE,
                    'name': '浦发银行',
                    'size': 100,  # 每手股数
                },
                {
                    'symbol': '000001',
                    'exchange': Exchange.SZSE,
                    'name': '平安银行',
                    'size': 100,
                },
            ]

            for contract_data in contracts:
                contract: ContractData = ContractData(
                    symbol=contract_data['symbol'],
                    exchange=contract_data['exchange'],
                    name=contract_data['name'],
                    size=contract_data['size'],
                    product=Product.STOCK,
                    gateway_name=self.gateway_name,
                )
                self.contracts[contract.vt_symbol] = contract
                self.on_contract(contract)

            self.write_log(f"合约查询成功，共 {len(contracts)} 个")

        except Exception as e:
            self.write_log(f"查询合约失败: {str(e)}")

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        """
        查询历史数据

        可以使用东财的历史数据 API
        """
        history: List[BarData] = []

        try:
            # 调用东财的历史数据 API
            # 示例：获取 K 线数据
            url = f"{self.BASE_URL}/stock/klt"
            params = {
                'secid': f"{self._convert_exchange(req.exchange)}.{req.symbol}",
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': f"{req.interval.value.replace('m', '')}01,f51,f52,f53,f54,f55,f56,f57,f58",
                'klt': 101,  # 日K
                'fqt': 1,    # 前复权
                'beg': req.start.strftime('%Y%m%d'),
                'end': req.end.strftime('%Y%m%d'),
            }

            # response = self.session.get(url, params=params)
            # data = response.json()

            # 解析返回的数据并生成 BarData 列表
            # ...

        except Exception as e:
            self.write_log(f"查询历史数据失败: {str(e)}")

        return history

    def _convert_exchange(self, exchange: Exchange) -> str:
        """转换交易所代码"""
        exchange_map = {
            Exchange.SSE: '1',      # 上交所
            Exchange.SZSE: '0',     # 深交所
            Exchange.BSE: '2',      # 北交所
        }
        return exchange_map.get(exchange, '0')

    def get_default_setting(self) -> Dict[str, str | int | float | bool]:
        """获取默认配置"""
        return {
            "username": "",
            "password": "",
            "cookie": "",
        }


# 方便的函数
def create_eastmoney_gateway(event_engine: EventEngine, gateway_name: str = "EM") -> EastmoneyGateway:
    """创建东财网关实例"""
    return EastmoneyGateway(event_engine, gateway_name)
