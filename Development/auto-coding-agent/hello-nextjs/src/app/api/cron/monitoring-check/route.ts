/**
 * Cron Job Endpoint: Policy Monitoring Check
 *
 * This endpoint is designed to be called by a cron job service (e.g., Vercel Cron, GitHub Actions)
 * to run automated policy monitoring checks.
 *
 * Recommended schedule: Daily at 2 AM UTC
 *
 * Example Vercel Cron configuration in vercel.json:
 * {
 *   "crons": [
 *     {
 *       "path": "/api/cron/monitoring-check",
 *       "schedule": "0 2 * * *"
 *     }
 *   ]
 * }
 *
 * Security: This endpoint should be protected with a secret API key in production.
 */

import { NextRequest, NextResponse } from 'next/server';
import { runBatchMonitoringCheck } from '@/lib/monitoring/policy-monitor';

// Secret key to prevent unauthorized access (set in environment variables)
const CRON_SECRET = process.env.CRON_MONITORING_SECRET || '';

export async function GET(request: NextRequest) {
  // Verify secret key
  const authHeader = request.headers.get('authorization');
  if (!CRON_SECRET) {
    return NextResponse.json(
      { error: 'Cron secret not configured' },
      { status: 500 }
    );
  }

  const providedSecret = authHeader?.replace('Bearer ', '');
  if (providedSecret !== CRON_SECRET) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  console.log(`[Cron] Starting policy monitoring check at ${new Date().toISOString()}`);

  try {
    // Run batch monitoring check
    const results = await runBatchMonitoringCheck();

    const changedCount = results.filter((r) => r.changed).length;
    const errorCount = results.filter((r) => r.error).length;
    const successCount = results.filter((r) => r.checked && !r.error).length;

    console.log(`[Cron] Monitoring check completed:`, {
      checked: results.length,
      success: successCount,
      changed: changedCount,
      errors: errorCount,
    });

    // If there are changes, you could send email notifications here
    if (changedCount > 0) {
      console.log(`[Cron] ⚠️  Policy changes detected: ${changedCount} cities`);
      // TODO: Send email notification to admins
      // Example: await sendChangeNotificationEmail(results.filter(r => r.changed));
    }

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      summary: {
        checked: results.length,
        success: successCount,
        changed: changedCount,
        errors: errorCount,
      },
      results,
    });
  } catch (error) {
    console.error('[Cron] Monitoring check failed:', error);
    return NextResponse.json(
      {
        success: false,
        error: (error as Error).message,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
