/**
 * Strategy Signals API Route
 * GET /api/strategies/[id]/signals - Get signals for a strategy
 */

import { createClient } from '@/lib/supabase/server';
import { getStrategySignals } from '@/lib/db/strategies';
import { StrategyError } from '@/lib/db/strategies';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id } = await params;
    const signals = await getStrategySignals(id, user.id);

    return NextResponse.json({ signals });
  } catch (error) {
    console.error('Error fetching signals:', error);
    if (error instanceof StrategyError) {
      if (error.code === 'not_found') {
        return NextResponse.json({ error: error.message }, { status: 404 });
      }
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
    return NextResponse.json({ error: 'Failed to fetch signals' }, { status: 500 });
  }
}
