/**
 * Market Data Data Access Layer
 * Handles all database operations for market data caching
 */

import { createClient } from '@/lib/supabase/server';
import { MarketData, MarketDataInsert } from '@/types/database';

export class MarketDataError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'MarketDataError';
  }
}

// ============================================================================
// MARKET DATA
// ============================================================================

/**
 * Get latest market data for a symbol
 */
export async function getLatestMarketData(symbol: string): Promise<MarketData | null> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('market_data')
    .select('*')
    .eq('symbol', symbol)
    .order('timestamp', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw new MarketDataError(error.message, 'database_error');
  return data;
}

/**
 * Get market data for multiple symbols
 */
export async function getMarketDataForSymbols(symbols: string[]): Promise<MarketData[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('market_data')
    .select('*')
    .in('symbol', symbols)
    .order('timestamp', { ascending: false });

  if (error) throw new MarketDataError(error.message, 'database_error');

  // Get only the latest data for each symbol
  const latestBySymbol = new Map<string, MarketData>();
  for (const item of data || []) {
    if (!latestBySymbol.has(item.symbol)) {
      latestBySymbol.set(item.symbol, item);
    }
  }

  return Array.from(latestBySymbol.values());
}

/**
 * Get historical market data for a symbol
 */
export async function getHistoricalMarketData(
  symbol: string,
  startDate: Date,
  endDate: Date = new Date()
): Promise<MarketData[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('market_data')
    .select('*')
    .eq('symbol', symbol)
    .gte('timestamp', startDate.toISOString())
    .lte('timestamp', endDate.toISOString())
    .order('timestamp', { ascending: true });

  if (error) throw new MarketDataError(error.message, 'database_error');
  return data || [];
}

/**
 * Get market data for a specific time range
 */
export async function getMarketDataByTimeRange(
  symbol: string,
  hours: number = 24
): Promise<MarketData[]> {
  const startDate = new Date();
  startDate.setHours(startDate.getHours() - hours);

  return getHistoricalMarketData(symbol, startDate);
}

/**
 * Create or update market data
 */
export async function upsertMarketData(data: Omit<MarketDataInsert, 'id'>): Promise<MarketData> {
  const supabase = await createClient();

  const { data: result, error } = await supabase
    .from('market_data')
    .upsert(data, { onConflict: 'symbol,timestamp' })
    .select()
    .single();

  if (error) throw new MarketDataError(error.message, 'database_error');
  return result;
}

/**
 * Batch insert market data
 */
export async function batchInsertMarketData(items: Omit<MarketDataInsert, 'id'>[]): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('market_data')
    .insert(items);

  if (error) throw new MarketDataError(error.message, 'database_error');
}

/**
 * Delete old market data (cleanup)
 */
export async function deleteOldMarketData(daysToKeep = 30): Promise<void> {
  const supabase = await createClient();

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

  const { error } = await supabase
    .from('market_data')
    .delete()
    .lt('timestamp', cutoffDate.toISOString());

  if (error) throw new MarketDataError(error.message, 'database_error');
}

/**
 * Get market data statistics for a symbol
 */
export async function getMarketDataStatistics(symbol: string, hours = 24): Promise<{
  latest: MarketData | null;
  high: number;
  low: number;
  average: number;
  change: number;
  changePercent: number;
}> {
  const data = await getMarketDataByTimeRange(symbol, hours);

  if (data.length === 0) {
    return {
      latest: null,
      high: 0,
      low: 0,
      average: 0,
      change: 0,
      changePercent: 0,
    };
  }

  const latest = data[0];
  const previous = data[data.length > 1 ? 1 : 0];

  const high = Math.max(...data.map((d) => d.high_price || 0));
  const low = Math.min(...data.map((d) => d.low_price || 0));
  const average = data.reduce((sum, d) => sum + (d.close_price || 0), 0) / data.length;

  const change = (latest.close_price || 0) - (previous.close_price || 0);
  const changePercent = previous.close_price ? (change / previous.close_price) * 100 : 0;

  return {
    latest,
    high,
    low,
    average,
    change,
    changePercent,
  };
}

/**
 * Get top gainers from cached market data
 */
export async function getTopGainers(limit = 10): Promise<Array<{
  symbol: string;
  changePercent: number;
  price: number;
}>> {
  const supabase = await createClient();

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from('market_data')
    .select('*')
    .gte('timestamp', today.toISOString())
    .order('timestamp', { ascending: true });

  if (error) throw new MarketDataError(error.message, 'database_error');

  // Group by symbol and calculate change
  const bySymbol = new Map<string, MarketData[]>();
  for (const item of data || []) {
    if (!bySymbol.has(item.symbol)) {
      bySymbol.set(item.symbol, []);
    }
    bySymbol.get(item.symbol)!.push(item);
  }

  const gainers: Array<{
    symbol: string;
    changePercent: number;
    price: number;
  }> = [];

  for (const [symbol, items] of bySymbol.entries()) {
    if (items.length < 2) continue;

    const open = items[0].open_price || 0;
    const close = items[items.length - 1].close_price || 0;
    const changePercent = open > 0 ? ((close - open) / open) * 100 : 0;

    gainers.push({
      symbol,
      changePercent,
      price: close,
    });
  }

  return gainers
    .sort((a, b) => b.changePercent - a.changePercent)
    .slice(0, limit);
}

/**
 * Get top losers from cached market data
 */
export async function getTopLosers(limit = 10): Promise<Array<{
  symbol: string;
  changePercent: number;
  price: number;
}>> {
  const gainers = await getTopGainers(100);

  return gainers
    .filter((g) => g.changePercent < 0)
    .sort((a, b) => a.changePercent - b.changePercent)
    .slice(0, limit);
}
