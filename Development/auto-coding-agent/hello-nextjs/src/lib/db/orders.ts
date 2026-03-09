/**
 * Orders Data Access Layer
 * Handles all database operations for trading orders
 */

import { createClient } from '@/lib/supabase/server';
import { Order, OrderInsert, OrderUpdate, Trade } from '@/types/database';

export class OrderError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'OrderError';
  }
}

// ============================================================================
// ORDERS
// ============================================================================

/**
 * Get all orders for a user
 */
export async function getOrders(userId: string, limit = 50): Promise<Order[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) throw new OrderError(error.message, 'database_error');
  return data || [];
}

/**
 * Get orders by status
 */
export async function getOrdersByStatus(userId: string, status: Order['status']): Promise<Order[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('user_id', userId)
    .eq('status', status)
    .order('created_at', { ascending: false });

  if (error) throw new OrderError(error.message, 'database_error');
  return data || [];
}

/**
 * Get orders for a specific position
 */
export async function getOrdersByPosition(positionId: string): Promise<Order[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('position_id', positionId)
    .order('created_at', { ascending: false });

  if (error) throw new OrderError(error.message, 'database_error');
  return data || [];
}

/**
 * Get orders for a specific symbol
 */
export async function getOrdersBySymbol(symbol: string, userId: string): Promise<Order[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('symbol', symbol)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new OrderError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single order by ID
 */
export async function getOrderById(id: string, userId: string): Promise<Order> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('id', id)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new OrderError('Order not found', 'not_found');
    throw new OrderError(error.message, 'database_error');
  }

  return data;
}

/**
 * Get order with trades
 */
export async function getOrderWithTrades(orderId: string, userId: string): Promise<Order & { trades: Trade[] }> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .select(`
      *,
      trades(*)
    `)
    .eq('id', orderId)
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new OrderError('Order not found', 'not_found');
    throw new OrderError(error.message, 'database_error');
  }

  return data as Order & { trades: Trade[] };
}

/**
 * Create a new order
 */
export async function createOrder(userId: string, order: Omit<OrderInsert, 'user_id' | 'id'>): Promise<Order> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .insert({ ...order, user_id: userId })
    .select()
    .single();

  if (error) throw new OrderError(error.message, 'database_error');
  return data;
}

/**
 * Update an order
 */
export async function updateOrder(id: string, userId: string, updates: OrderUpdate): Promise<Order> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('orders')
    .update(updates)
    .eq('id', id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new OrderError('Order not found', 'not_found');
    throw new OrderError(error.message, 'database_error');
  }

  return data;
}

/**
 * Update order status
 */
export async function updateOrderStatus(
  id: string,
  userId: string,
  status: OrderInsert['status'],
  filledQuantity?: number,
  filledPrice?: number
): Promise<Order> {
  const updates: OrderUpdate = { status };

  if (filledQuantity !== undefined) {
    updates.filled_quantity = filledQuantity;
  }

  if (filledPrice !== undefined) {
    updates.filled_price = filledPrice;
  }

  return updateOrder(id, userId, updates);
}

/**
 * Cancel an order
 */
export async function cancelOrder(id: string, userId: string): Promise<Order> {
  return updateOrder(id, userId, { status: 'cancelled' });
}

/**
 * Delete an order
 */
export async function deleteOrder(id: string, userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('orders')
    .delete()
    .eq('id', id)
    .eq('user_id', userId);

  if (error) throw new OrderError(error.message, 'database_error');
}

/**
 * Get today's orders for a user
 */
export async function getTodayOrders(userId: string): Promise<Order[]> {
  const supabase = await createClient();

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .eq('user_id', userId)
    .gte('created_at', today.toISOString())
    .order('created_at', { ascending: false });

  if (error) throw new OrderError(error.message, 'database_error');
  return data || [];
}

/**
 * Get pending orders for a user
 */
export async function getPendingOrders(userId: string): Promise<Order[]> {
  return getOrdersByStatus(userId, 'pending');
}

/**
 * Get submitted orders for a user
 */
export async function getSubmittedOrders(userId: string): Promise<Order[]> {
  return getOrdersByStatus(userId, 'submitted');
}

/**
 * Get filled orders for a user
 */
export async function getFilledOrders(userId: string): Promise<Order[]> {
  return getOrdersByStatus(userId, 'filled');
}
