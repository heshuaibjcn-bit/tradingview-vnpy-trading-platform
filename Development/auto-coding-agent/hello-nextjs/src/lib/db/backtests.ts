/**
 * Backtests Data Access Layer
 * Handles all database operations for strategy backtesting
 */

import { createClient } from '@/lib/supabase/server';
import { Backtest, BacktestInsert, Json } from '@/types/database';

export class BacktestError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'BacktestError';
  }
}

// ============================================================================
// BACKTESTS
// ============================================================================

/**
 * Get all backtests for a user
 */
export async function getBacktests(userId: string, limit = 20): Promise<Backtest[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) throw new BacktestError(error.message, 'database_error');
  return data || [];
}

/**
 * Get backtests by strategy type
 */
export async function getBacktestsByStrategy(userId: string, strategyType: Backtest['strategy_type']): Promise<Backtest[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .select('*')
    .eq('user_id', userId)
    .eq('strategy_type', strategyType)
    .order('created_at', { ascending: false });

  if (error) throw new BacktestError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single backtest by ID
 */
export async function getBacktestById(id: string, userId: string): Promise<Backtest> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .select('*')
    .eq('id', id)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new BacktestError('Backtest not found', 'not_found');
    throw new BacktestError(error.message, 'database_error');
  }

  return data;
}

/**
 * Create a new backtest
 */
export async function createBacktest(
  userId: string,
  backtest: Omit<BacktestInsert, 'user_id' | 'id' | 'created_at'>
): Promise<Backtest> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .insert({ ...backtest, user_id: userId })
    .select()
    .single();

  if (error) throw new BacktestError(error.message, 'database_error');
  return data;
}

/**
 * Update backtest results
 */
export async function updateBacktestResults(
  id: string,
  userId: string,
  results: {
    final_capital: number;
    total_return: number;
    max_drawdown: number;
    sharpe_ratio: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    detailed_results?: Json;
  }
): Promise<Backtest> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .update(results)
    .eq('id', id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new BacktestError('Backtest not found', 'not_found');
    throw new BacktestError(error.message, 'database_error');
  }

  return data;
}

/**
 * Delete a backtest
 */
export async function deleteBacktest(id: string, userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('backtests')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);

  if (error) throw new BacktestError(error.message, 'database_error');
}

/**
 * Get backtest statistics for a user
 */
export async function getBacktestStatistics(userId: string): Promise<{
  totalBacktests: number;
  byStrategyType: Record<string, number>;
  averageReturn: number;
  bestReturn: number;
  worstReturn: number;
  averageSharpeRatio: number;
}> {
  const backtests = await getBacktests(userId, 1000);

  const byStrategyType: Record<string, number> = {};
  let totalReturn = 0;
  let bestReturn = -Infinity;
  let worstReturn = Infinity;
  let totalSharpeRatio = 0;
  let sharpeRatioCount = 0;

  for (const backtest of backtests) {
    // Count by strategy type
    if (!byStrategyType[backtest.strategy_type]) {
      byStrategyType[backtest.strategy_type] = 0;
    }
    byStrategyType[backtest.strategy_type]++;

    // Calculate statistics
    if (backtest.total_return !== null) {
      totalReturn += backtest.total_return;
      bestReturn = Math.max(bestReturn, backtest.total_return);
      worstReturn = Math.min(worstReturn, backtest.total_return);
    }

    if (backtest.sharpe_ratio !== null) {
      totalSharpeRatio += backtest.sharpe_ratio;
      sharpeRatioCount++;
    }
  }

  return {
    totalBacktests: backtests.length,
    byStrategyType,
    averageReturn: backtests.length > 0 ? totalReturn / backtests.length : 0,
    bestReturn: bestReturn !== -Infinity ? bestReturn : 0,
    worstReturn: worstReturn !== Infinity ? worstReturn : 0,
    averageSharpeRatio: sharpeRatioCount > 0 ? totalSharpeRatio / sharpeRatioCount : 0,
  };
}

/**
 * Compare backtests
 */
export async function compareBacktests(
  userId: string,
  backtestIds: string[]
): Promise<Backtest[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('backtests')
    .select('*')
    .in('id', backtestIds)
    .eq('user_id', userId);

  if (error) throw new BacktestError(error.message, 'database_error');
  return data || [];
}

/**
 * Get recent backtests for a user
 */
export async function getRecentBacktests(userId: string, days = 7): Promise<Backtest[]> {
  const supabase = await createClient();

  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  startDate.setHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from('backtests')
    .select('*')
    .eq('user_id', userId)
    .gte('created_at', startDate.toISOString())
    .order('created_at', { ascending: false });

  if (error) throw new BacktestError(error.message, 'database_error');
  return data || [];
}

/**
 * Get best performing backtests
 */
export async function getBestBacktests(userId: string, strategyType?: Backtest['strategy_type'], limit = 5): Promise<Backtest[]> {
  const supabase = await createClient();

  let query = supabase
    .from('backtests')
    .select('*')
    .eq('user_id', userId)
    .not('total_return', 'is', null)
    .order('total_return', { ascending: false })
    .limit(limit);

  if (strategyType) {
    query = query.eq('strategy_type', strategyType);
  }

  const { data, error } = await query;

  if (error) throw new BacktestError(error.message, 'database_error');
  return data || [];
}
