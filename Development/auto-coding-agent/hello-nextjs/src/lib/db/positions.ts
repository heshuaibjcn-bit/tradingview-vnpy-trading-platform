/**
 * Positions Data Access Layer
 * Handles all database operations for stock positions
 */

import { createClient } from '@/lib/supabase/server';
import { Position, PositionInsert, PositionUpdate, Order } from '@/types/database';

export class PositionError extends Error {
  constructor(
    message: string,
    public code: 'not_found' | 'unauthorized' | 'database_error' | 'validation_error' = 'database_error'
  ) {
    super(message);
    this.name = 'PositionError';
  }
}

// ============================================================================
// POSITIONS
// ============================================================================

/**
 * Get all positions for a user
 */
export async function getPositions(userId: string): Promise<Position[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('positions')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new PositionError(error.message, 'database_error');
  return data || [];
}

/**
 * Get a single position by symbol
 */
export async function getPositionBySymbol(symbol: string, userId: string): Promise<Position | null> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('positions')
    .select('*')
    .eq('symbol', symbol)
    .eq('user_id', userId)
    .maybeSingle();

  if (error) throw new PositionError(error.message, 'database_error');
  return data;
}

/**
 * Get positions with related orders
 */
export async function gettingsWithOrders(userId: string): Promise<(Position & { orders: Order[] })[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('positions')
    .select(`
      *,
      orders(*)
    `)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw new PositionError(error.message, 'database_error');
  return data || [];
}

/**
 * Create or update a position
 */
export async function upsertPosition(
  userId: string,
  position: Omit<PositionInsert, 'user_id' | 'id'>
): Promise<Position> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('positions')
    .upsert({ ...position, user_id: userId })
    .select()
    .single();

  if (error) throw new PositionError(error.message, 'database_error');
  return data;
}

/**
 * Update current price and P/L for a position
 */
export async function updatePositionPrice(
  symbol: string,
  userId: string,
  currentPrice: number
): Promise<Position> {
  const position = await getPositionBySymbol(symbol, userId);
  if (!position) {
    throw new PositionError('Position not found', 'not_found');
  }

  const profitLoss = (currentPrice - position.cost_price) * position.quantity;
  const profitLossRatio = ((currentPrice - position.cost_price) / position.cost_price) * 100;

  return updatePosition(symbol, userId, {
    current_price: currentPrice,
    profit_loss: profitLoss,
    profit_loss_ratio: profitLossRatio,
  });
}

/**
 * Update a position
 */
export async function updatePosition(
  symbol: string,
  userId: string,
  updates: PositionUpdate
): Promise<Position> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from('positions')
    .update(updates)
    .eq('symbol', symbol)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) {
    if (error.code === 'PGRST116') throw new PositionError('Position not found', 'not_found');
    throw new PositionError(error.message, 'database_error');
  }

  return data;
}

/**
 * Update position quantity (after buy/sell)
 */
export async function updatePositionQuantity(
  symbol: string,
  userId: string,
  quantityDelta: number,
  newCostPrice?: number
): Promise<Position> {
  const position = await getPositionBySymbol(symbol, userId);

  if (!position) {
    // Create new position if it doesn't exist
    if (quantityDelta > 0) {
      return upsertPosition(userId, {
        symbol,
        quantity: quantityDelta,
        cost_price: newCostPrice || 0,
      });
    }
    throw new PositionError('Position not found', 'not_found');
  }

  const newQuantity = position.quantity + quantityDelta;

  if (newQuantity <= 0) {
    // Delete position if quantity is zero or negative
    await deletePosition(symbol, userId);
    return position;
  }

  // Update cost price if buying
  let costPrice = position.cost_price;
  if (quantityDelta > 0 && newCostPrice) {
    // Calculate new average cost price
    const totalCost = position.cost_price * position.quantity + newCostPrice * quantityDelta;
    costPrice = totalCost / newQuantity;
  }

  return updatePosition(symbol, userId, {
    quantity: newQuantity,
    cost_price: costPrice,
  });
}

/**
 * Delete a position
 */
export async function deletePosition(symbol: string, userId: string): Promise<void> {
  const supabase = await createClient();

  const { error } = await supabase
    .from('positions')
    .delete()
    .eq('symbol', symbol)
    .eq('user_id', userId);

  if (error) throw new PositionError(error.message, 'database_error');
}

/**
 * Get total portfolio value
 */
export async function getPortfolioValue(userId: string): Promise<{
  totalValue: number;
  totalCost: number;
  totalProfitLoss: number;
  totalProfitLossRatio: number;
}> {
  const positions = await getPositions(userId);

  let totalValue = 0;
  let totalCost = 0;

  for (const position of positions) {
    const currentValue = (position.current_price || position.cost_price) * position.quantity;
    totalValue += currentValue;
    totalCost += position.cost_price * position.quantity;
  }

  const totalProfitLoss = totalValue - totalCost;
  const totalProfitLossRatio = totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0;

  return {
    totalValue,
    totalCost,
    totalProfitLoss,
    totalProfitLossRatio,
  };
}
