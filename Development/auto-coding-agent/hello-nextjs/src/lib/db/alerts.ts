/**
 * Alerts Data Access Layer
 * Handles all database operations for market monitoring alerts
 */

import { createClient } from '@/lib/supabase/server';
import { Alert, AlertInsert, AlertUpdate } from '@/types/database';

export class AlertError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'AlertError';
  }
}

// ============================================================================
// ALERTS
// ============================================================================

/**
 * Get all alerts for a user
 */
export async function getAlerts(userId: string, includeTriggered = false): Promise<Alert[]> {
  const supabase = await createClient();

  let query = supabase
    .from('alerts')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (!includeTriggered) {
    query = query.eq('triggered', false);
  }

  const { data, error } = await query;

  if (error) throw new AlertError(error.message, 'database_error');
  return data || [];
}

/**
 * Get alerts for a specific symbol
 */
export async function getAlertsBySymbol(symbol: string, userId: string): Promise<Alert[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('symbol', symbol)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new AlertError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single alert by ID
 */
export async function getAlertById(id: string, userId: string): Promise<Alert> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('id', id)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new AlertError('Alert not found', 'not_found');
    throw new AlertError(error.message, 'database_error');
  }

  return data;
}

/**
 * Get pending (untriggered) alerts for a user
 */
export async function getPendingAlerts(userId: string): Promise<Alert[]> {
  return getAlerts(userId, false);
}

/**
 * Get triggered alerts for a user
 */
export async function getTriggeredAlerts(userId: string): Promise<Alert[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('user_id', userId)
    .eq('triggered', true)
    .order('triggered_at', { ascending: false });

  if (error) throw new AlertError(error.message, 'database_error');
  return data || [];
}

/**
 * Create a new alert
 */
export async function createAlert(userId: string, alert: Omit<AlertInsert, 'user_id' | 'id' | 'triggered' | 'triggered_at' | 'created_at'>): Promise<Alert> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .insert({
      ...alert,
      user_id: userId,
      triggered: false,
      triggered_at: null,
    })
    .select()
    .single();

  if (error) throw new AlertError(error.message, 'database_error');
  return data;
}

/**
 * Update an alert
 */
export async function updateAlert(id: string, userId: string, updates: AlertUpdate): Promise<Alert> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .update(updates)
    .eq('id', id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new AlertError('Alert not found', 'not_found');
    throw new AlertError(error.message, 'database_error');
  }

  return data;
}

/**
 * Trigger an alert
 */
export async function triggerAlert(id: string, userId: string, message: string): Promise<Alert> {
  return updateAlert(id, userId, {
    triggered: true,
    triggered_at: new Date().toISOString(),
    message,
  });
}

/**
 * Delete an alert
 */
export async function deleteAlert(id: string, userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('alerts')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);

  if (error) throw new AlertError(error.message, 'database_error');
}

/**
 * Delete triggered alerts for a user
 */
export async function deleteTriggeredAlerts(userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('alerts')
    .delete()
    .eq('user_id', userId)
    .eq('triggered', true);

  if (error) throw new AlertError(error.message, 'database_error');
}

/**
 * Delete old triggered alerts (older than specified days)
 */
export async function deleteOldTriggeredAlerts(userId: string, days = 7): Promise<void> {
  const supabase = await createClient();

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  const { error } = await supabase
    .from('alerts')
    .delete()
    .eq('user_id', userId)
    .eq('triggered', true)
    .lt('triggered_at', cutoffDate.toISOString());

  if (error) throw new AlertError(error.message, 'database_error');
}

/**
 * Get alerts for a specific symbol that should be checked
 */
export async function getAlertsToCheck(symbol: string): Promise<Alert[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('symbol', symbol)
    .eq('triggered', false);

  if (error) throw new AlertError(error.message, 'database_error');
  return data || [];
}

/**
 * Check alerts for multiple symbols
 */
export async function getAlertsForSymbols(symbols: string[]): Promise<Alert[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .in('symbol', symbols)
    .eq('triggered', false);

  if (error) throw new AlertError(error.message, 'database_error');
  return data || [];
}
