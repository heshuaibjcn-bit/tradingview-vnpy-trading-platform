#!/usr/bin/env python3
"""
验证K线数据生成逻辑
"""

def simulate_candlestick_generation():
    """模拟JavaScript的K线数据生成逻辑"""
    data = []
    base_price = 10.0
    previous_close = base_price

    import datetime
    now = datetime.datetime.now()

    for i in range(10):  # 只生成10天用于演示
        time = now - datetime.timedelta(days=i)

        # 开盘价 = 前一根K线的收盘价
        open_price = previous_close

        # 生成当天的价格变动（-3% 到 +3%）
        import random
        change = (random.random() - 0.5) * 0.06
        close = open_price * (1 + change)

        # 最高价和最低价
        high = max(open_price, close) * (1 + random.random() * 0.01)
        low = min(open_price, close) * (1 - random.random() * 0.01)

        candle = {
            'date': time.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
        }

        # 验证数据逻辑
        assert candle['high'] >= max(candle['open'], candle['close']), \
            f"最高价必须 >= 开盘价和收盘价: {candle}"
        assert candle['low'] <= min(candle['open'], candle['close']), \
            f"最低价必须 <= 开盘价和收盘价: {candle}"

        data.append(candle)
        previous_close = close

    return data

def print_candlestick_data(data):
    """打印K线数据"""
    print("K线数据验证:")
    print("-" * 80)
    print(f"{'日期':<12} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} {'涨跌':>8} {'连续性':>10}")
    print("-" * 80)

    prev_close = None
    for candle in data:
        change = ((candle['close'] - candle['open']) / candle['open'] * 100)

        # 检查连续性
        continuity = "✓"
        if prev_close is not None:
            if abs(candle['open'] - prev_close) > 0.01:
                continuity = f"✗ (差值: {candle['open'] - prev_close:.4f})"

        print(f"{candle['date']:<12} "
              f"{candle['open']:>8.2f} "
              f"{candle['high']:>8.2f} "
              f"{candle['low']:>8.2f} "
              f"{candle['close']:>8.2f} "
              f"{change:>7.2f}% "
              f"{continuity:>10}")

        prev_close = candle['close']

    print("-" * 80)

    # 验证统计数据
    print("\n数据验证:")
    print(f"  总K线数: {len(data)}")

    continuity_errors = 0
    prev_close = None
    for candle in data:
        if prev_close is not None:
            if abs(candle['open'] - prev_close) > 0.01:
                continuity_errors += 1
        prev_close = candle['close']

    print(f"  连续性错误: {continuity_errors}")

    # 验证价格逻辑
    logic_errors = 0
    for candle in data:
        if candle['high'] < max(candle['open'], candle['close']):
            logic_errors += 1
            print(f"  ✗ {candle['date']}: 最高价 < max(开盘, 收盘)")
        if candle['low'] > min(candle['open'], candle['close']):
            logic_errors += 1
            print(f"  ✗ {candle['date']}: 最低价 > min(开盘, 收盘)")

    if logic_errors == 0:
        print(f"  价格逻辑: ✓ 所有K线的OHLC关系正确")

if __name__ == "__main__":
    data = simulate_candlestick_generation()
    print_candlestick_data(data)
