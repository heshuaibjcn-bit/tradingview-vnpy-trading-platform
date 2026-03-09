/**
 * Strategies Data Access Layer
 * Handles all database operations for trading strategies
 */

import { createClient } from '@/lib/supabase/server';
import { Strategy, StrategyInsert, StrategyUpdate, StrategySignal, StrategySignalInsert } from '@/types/database';

export class StrategyError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'StrategyError';
  }
}

// ============================================================================
// STRATEGIES
// ============================================================================

/**
 * Get all strategies for a user
 */
export async function getStrategies(userId: string): Promise<Strategy[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new StrategyError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single strategy by ID
 */
export async function getStrategyById(id: string, userId: string): Promise<Strategy> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .select('*')
    .eq('id', id)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new StrategyError('Strategy not found', 'not_found');
    throw new StrategyError(error.message, 'database_error');
  }

  return data;
}

/**
 * Get strategies with signals
 */
export async function getStrategiesWithSignals(userId: string): Promise<(Strategy & { signals: StrategySignal[] })[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .select(`
      *,
      strategy_signals(*)
    `)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new StrategyError(error.message, 'database_error');

  // Map strategy_signals to signals
  return (data || []).map((item: any) => ({
    ...item,
    signals: item.strategy_signals || [],
  }));
}

/**
 * Get enabled strategies for a user
 */
export async function getEnabledStrategies(userId: string): Promise<Strategy[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .select('*')
    .eq('user_id', userId)
    .eq('enabled', true)
    .order('created_at', { ascending: false });

  if (error) throw new StrategyError(error.message, 'database_error');
  return data || [];
}

/**
 * Create a new strategy
 */
export async function createStrategy(userId: string, strategy: Omit<StrategyInsert, 'user_id'>): Promise<Strategy> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .insert({ ...strategy, user_id: userId })
    .select()
    .single();

  if (error) throw new StrategyError(error.message, 'database_error');
  return data;
}

/**
 * Update a strategy
 */
export async function updateStrategy(id: string, userId: string, updates: StrategyUpdate): Promise<Strategy> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategies')
    .update(updates)
    .eq('id', id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new StrategyError('Strategy not found', 'not_found');
    throw new StrategyError(error.message, 'database_error');
  }

  return data;
}

/**
 * Enable a strategy
 */
export async function enableStrategy(id: string, userId: string): Promise<Strategy> {
  return updateStrategy(id, userId, { enabled: true });
}

/**
 * Disable a strategy
 */
export async function disableStrategy(id: string, userId: string): Promise<Strategy> {
  return updateStrategy(id, userId, { enabled: false });
}

/**
 * Delete a strategy
 */
export async function deleteStrategy(id: string, userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('strategies')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);

  if (error) throw new StrategyError(error.message, 'database_error');
}

// ============================================================================
// STRATEGY SIGNALS
// ============================================================================

/**
 * Get signals for a strategy
 */
export async function getStrategySignals(strategyId: string, userId: string): Promise<StrategySignal[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategy_signals')
    .select('*')
    .eq('strategy_id', strategyId)
    .order('created_at', { ascending: false });

  if (error) throw new StrategyError(error.message, 'database_error');

  // Verify ownership
  const strategy = await getStrategyById(strategyId, userId);
  if (!strategy) throw new StrategyError('Strategy not found', 'not_found');

  return data || [];
}

/**
 * Get pending (unexecuted) signals for enabled strategies
 */
export async function getPendingSignals(userId: string): Promise<StrategySignal[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategy_signals')
    .select('*, strategies(*)')
    .eq('executed', false)
    .eq('strategies.user_id', userId)
    .eq('strategies.enabled', true)
    .order('created_at', { ascending: false });

  if (error) throw new StrategyError(error.message, 'database_error');
  return data || [];
}

/**
 * Create a new signal
 */
export async function createSignal(signal: Omit<StrategySignalInsert, 'id'>): Promise<StrategySignal> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('strategy_signals')
    .insert(signal)
    .select()
    .single();

  if (error) throw new StrategyError(error.message, 'database_error');
  return data;
}

/**
 * Mark a signal as executed
 */
export async function markSignalExecuted(signalId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('strategy_signals')
    .update({ executed: true })
    .eq('id', signalId);

  if (error) throw new StrategyError(error.message, 'database_error');
}

/**
 * Delete old signals (older than 30 days)
 */
export async function deleteOldSignals(): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('strategy_signals')
    .delete()
    .lt('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString());

  if (error) throw new StrategyError(error.message, 'database_error');
}
