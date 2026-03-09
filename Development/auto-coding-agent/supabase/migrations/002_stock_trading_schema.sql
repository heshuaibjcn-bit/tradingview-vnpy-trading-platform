-- StockAutoTrader - Stock Trading Schema
-- Migration: 002_stock_trading_schema
-- Description: Creates tables for stock auto-trading system

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Strategy type enum
CREATE TYPE strategy_type AS ENUM (
    'ma',        -- Moving Average (均线策略)
    'macd',      -- MACD Strategy
    'kdj',       -- KDJ Strategy
    'breakout',  -- Breakout Strategy (突破策略)
    'grid'       -- Grid Trading Strategy (网格交易策略)
);

-- Order status enum
CREATE TYPE order_status AS ENUM (
    'pending',           -- Pending submission (待提交)
    'submitted',         -- Submitted to exchange (已提交)
    'partial_filled',    -- Partially filled (部分成交)
    'filled',            -- Fully filled (全部成交)
    'cancelled',         -- Cancelled (已撤销)
    'failed'             -- Failed (失败)
);

-- Order side enum
CREATE TYPE order_side AS ENUM ('buy', 'sell');

-- Alert condition type enum
CREATE TYPE alert_condition_type AS ENUM (
    'price_above',       -- Price above threshold
    'price_below',       -- Price below threshold
    'volume_spike',      -- Volume spike
    'percent_change',    -- Percent change
    'indicator'          -- Technical indicator based
);

-- ============================================================================
-- STRATEGIES TABLE (策略配置)
-- ============================================================================

CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type strategy_type NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for strategies
CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_type ON strategies(type);
CREATE INDEX idx_strategies_enabled ON strategies(enabled);

-- RLS Policies
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own strategies"
    ON strategies FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own strategies"
    ON strategies FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own strategies"
    ON strategies FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own strategies"
    ON strategies FOR DELETE
    USING (auth.uid() = user_id);

-- Auto-update trigger
CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STRATEGY SIGNALS TABLE (策略信号)
-- ============================================================================

CREATE TABLE strategy_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('buy', 'sell')),
    price NUMERIC(12, 4),
    metadata JSONB DEFAULT '{}',
    executed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for strategy_signals
CREATE INDEX idx_strategy_signals_strategy_id ON strategy_signals(strategy_id);
CREATE INDEX idx_strategy_signals_symbol ON strategy_signals(symbol);
CREATE INDEX idx_strategy_signals_executed ON strategy_signals(executed);
CREATE INDEX idx_strategy_signals_created_at ON strategy_signals(created_at DESC);

-- RLS Policies
ALTER TABLE strategy_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view signals from their own strategies"
    ON strategy_signals FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM strategies
            WHERE strategies.id = strategy_signals.strategy_id
            AND strategies.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert signals for their own strategies"
    ON strategy_signals FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM strategies
            WHERE strategies.id = strategy_signals.strategy_id
            AND strategies.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update signals from their own strategies"
    ON strategy_signals FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM strategies
            WHERE strategies.id = strategy_signals.strategy_id
            AND strategies.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete signals from their own strategies"
    ON strategy_signals FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM strategies
            WHERE strategies.id = strategy_signals.strategy_id
            AND strategies.user_id = auth.uid()
        )
    );

-- ============================================================================
-- POSITIONS TABLE (持仓信息)
-- ============================================================================

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    cost_price NUMERIC(12, 4) NOT NULL CHECK (cost_price > 0),
    current_price NUMERIC(12, 4),
    profit_loss NUMERIC(12, 4),
    profit_loss_ratio NUMERIC(8, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one position per symbol per user
    UNIQUE(user_id, symbol)
);

-- Indexes for positions
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- RLS Policies
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own positions"
    ON positions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own positions"
    ON positions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own positions"
    ON positions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own positions"
    ON positions FOR DELETE
    USING (auth.uid() = user_id);

-- Auto-update trigger
CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ORDERS TABLE (委托记录)
-- ============================================================================

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,
    order_id VARCHAR(50),  -- External order ID from trading platform
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(12, 4) NOT NULL CHECK (price > 0),
    status order_status NOT NULL DEFAULT 'pending',
    filled_quantity INTEGER NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
    filled_price NUMERIC(12, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for orders
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_position_id ON orders(position_id);
CREATE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- RLS Policies
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own orders"
    ON orders FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own orders"
    ON orders FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own orders"
    ON orders FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own orders"
    ON orders FOR DELETE
    USING (auth.uid() = user_id);

-- Auto-update trigger
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TRADES TABLE (成交记录)
-- ============================================================================

CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    trade_id VARCHAR(50),  -- External trade ID from trading platform
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(12, 4) NOT NULL CHECK (price > 0),
    commission NUMERIC(12, 4) NOT NULL DEFAULT 0 CHECK (commission >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for trades
CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_trade_id ON trades(trade_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_created_at ON trades(created_at DESC);

-- RLS Policies
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own trades"
    ON trades FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own trades"
    ON trades FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- MARKET DATA TABLE (行情数据缓存)
-- ============================================================================

CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    open_price NUMERIC(12, 4),
    high_price NUMERIC(12, 4),
    low_price NUMERIC(12, 4),
    close_price NUMERIC(12, 4),
    volume BIGINT,
    amount NUMERIC(20, 2),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One record per symbol per minute (for caching)
    UNIQUE(symbol, timestamp)
);

-- Indexes for market_data
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);

-- RLS Policies - Market data can be viewed by all authenticated users
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view market data"
    ON market_data FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Auto-delete old market data (older than 30 days)
CREATE OR REPLACE FUNCTION delete_old_market_data()
RETURNS void AS $$
BEGIN
    DELETE FROM market_data
    WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ALERTS TABLE (提醒记录)
-- ============================================================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    condition_type alert_condition_type NOT NULL,
    condition JSONB NOT NULL,  -- Flexible condition storage
    triggered BOOLEAN NOT NULL DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for alerts
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_symbol ON alerts(symbol);
CREATE INDEX idx_alerts_triggered ON alerts(triggered);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

-- RLS Policies
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own alerts"
    ON alerts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own alerts"
    ON alerts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own alerts"
    ON alerts FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own alerts"
    ON alerts FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- BACKTESTS TABLE (回测结果)
-- ============================================================================

CREATE TABLE backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    strategy_type strategy_type NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(15, 2) NOT NULL CHECK (initial_capital > 0),
    final_capital NUMERIC(15, 2) CHECK (final_capital > 0),
    total_return NUMERIC(8, 4),
    max_drawdown NUMERIC(8, 4),
    sharpe_ratio NUMERIC(8, 4),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    detailed_results JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for backtests
CREATE INDEX idx_backtests_user_id ON backtests(user_id);
CREATE INDEX idx_backtests_strategy_type ON backtests(strategy_type);
CREATE INDEX idx_backtests_created_at ON backtests(created_at DESC);

-- RLS Policies
ALTER TABLE backtests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own backtests"
    ON backtests FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own backtests"
    ON backtests FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own backtests"
    ON backtests FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- STORAGE BUCKET
-- ============================================================================

-- Insert storage bucket for trading screenshots
INSERT INTO storage.buckets (id, name, public)
VALUES ('trading-screenshots', 'trading-screenshots', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for trading-screenshots bucket
CREATE POLICY "Users can upload screenshots to their own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'trading-screenshots'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can view screenshots in their own folder"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'trading-screenshots'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can delete screenshots in their own folder"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'trading-screenshots'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE strategies IS 'Trading strategies configuration created by users';
COMMENT ON TABLE strategy_signals IS 'Buy/sell signals generated by strategies';
COMMENT ON TABLE positions IS 'Current stock positions held by users';
COMMENT ON TABLE orders IS 'Order records submitted to trading platform';
COMMENT ON TABLE trades IS 'Executed trade records';
COMMENT ON TABLE market_data IS 'Cached market data (OHLCV) from external APIs or screen reading';
COMMENT ON TABLE alerts IS 'User-configured market monitoring alerts';
COMMENT ON TABLE backtests IS 'Backtest results for strategy testing';

COMMENT ON COLUMN strategies.parameters IS 'Strategy-specific parameters (e.g., MA periods, MACD settings)';
COMMENT ON COLUMN orders.filled_quantity IS 'Quantity that has been executed';
COMMENT ON COLUMN orders.filled_price IS 'Average price of filled shares';
COMMENT ON COLUMN trades.commission IS 'Trading commission/fees';
COMMENT ON COLUMN alerts.condition IS 'Alert condition (e.g., {threshold: 10.0, operator: ">"})';
COMMENT ON COLUMN backtests.detailed_results IS 'Detailed backtest data including trade history, equity curve, etc.';
