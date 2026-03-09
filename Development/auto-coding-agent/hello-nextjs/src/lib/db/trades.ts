/**
 * Trades Data Access Layer
 * Handles all database operations for executed trades
 */

import { createClient } from '@/lib/supabase/server';
import { Trade, TradeInsert } from '@/types/database';

export class TradeError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'TradeError';
  }
}

// ============================================================================
// TRADES
// ============================================================================

/**
 * Get all trades for a user
 */
export async function getTrades(userId: string, limit = 50): Promise<Trade[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) throw new TradeError(error.message, 'database_error');
  return data || [];
}

/**
 * Get trades for a specific order
 */
export async function getTradesByOrder(orderId: string): Promise<Trade[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('order_id', orderId)
    .order('created_at', { ascending: false });

  if (error) throw new TradeError(error.message, 'database_error');
  return data || [];
}

/**
 * Get trades for a specific symbol
 */
export async function getTradesBySymbol(symbol: string, userId: string): Promise<Trade[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('symbol', symbol)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new TradeError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single trade by ID
 */
export async function getTradeById(id: string, userId: string): Promise<Trade> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('id', id)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new TradeError('Trade not found', 'not_found');
    throw new TradeError(error.message, 'database_error');
  }

  return data;
}

/**
 * Create a new trade
 */
export async function createTrade(userId: string, trade: Omit<TradeInsert, 'user_id' | 'id'>): Promise<Trade> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('trades')
    .insert({ ...trade, user_id: userId })
    .select()
    .single();

  if (error) throw new TradeError(error.message, 'database_error');
  return data;
}

/**
 * Get today's trades for a user
 */
export async function getTodayTrades(userId: string): Promise<Trade[]> {
  const supabase = await createClient();

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .gte('created_at', today.toISOString())
    .order('created_at', { ascending: false });

  if (error) throw new TradeError(error.message, 'database_error');
  return data || [];
}

/**
 * Get trade statistics for a user
 */
export async function getTradeStatistics(userId: string, days = 30): Promise<{
  totalTrades: number;
  totalBuyTrades: number;
  totalSellTrades: number;
  totalVolume: number;
  totalAmount: number;
  totalCommission: number;
}> {
  const supabase = await createClient();

  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  startDate.setHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .gte('created_at', startDate.toISOString());

  if (error) throw new TradeError(error.message, 'database_error');

  const trades = data || [];

  let totalBuyTrades = 0;
  let totalSellTrades = 0;
  let totalVolume = 0;
  let totalAmount = 0;
  let totalCommission = 0;

  for (const trade of trades) {
    if (trade.side === 'buy') {
      totalBuyTrades++;
    } else {
      totalSellTrades++;
    }

    totalVolume += trade.quantity;
    totalAmount += trade.price * trade.quantity;
    totalCommission += trade.commission;
  }

  return {
    totalTrades: trades.length,
    totalBuyTrades,
    totalSellTrades,
    totalVolume,
    totalAmount,
    totalCommission,
  };
}

/**
 * Get trades grouped by symbol
 */
export async function getTradesGroupedBySymbol(userId: string): Promise<
  Array<{
    symbol: string;
    trades: Trade[];
    totalBuyQuantity: number;
    totalSellQuantity: number;
    totalBuyAmount: number;
    totalSellAmount: number;
  }>
> {
  const trades = await getTrades(userId, 1000);

  const grouped = new Map<string, Trade[]>();

  for (const trade of trades) {
    if (!grouped.has(trade.symbol)) {
      grouped.set(trade.symbol, []);
    }
    grouped.get(trade.symbol)!.push(trade);
  }

  return Array.from(grouped.entries()).map(([symbol, trades]) => {
    let totalBuyQuantity = 0;
    let totalSellQuantity = 0;
    let totalBuyAmount = 0;
    let totalSellAmount = 0;

    for (const trade of trades) {
      if (trade.side === 'buy') {
        totalBuyQuantity += trade.quantity;
        totalBuyAmount += trade.price * trade.quantity;
      } else {
        totalSellQuantity += trade.quantity;
        totalSellAmount += trade.price * trade.quantity;
      }
    }

    return {
      symbol,
      trades,
      totalBuyQuantity,
      totalSellQuantity,
      totalBuyAmount,
      totalSellAmount,
    };
  });
}
