/**
 * Policy Monitoring API
 * GET - Get monitoring summary and cities needing verification
 * POST - Run monitoring check or mark policies as verified
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getMonitoringSummary,
  getCitiesNeedingVerification,
  runBatchMonitoringCheck,
  markPolicyAsVerified,
  bulkMarkPoliciesAsVerified,
} from '@/lib/monitoring/policy-monitor';

/**
 * GET /api/monitoring/policies
 * Get monitoring summary and cities needing verification
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action');

    if (action === 'needs-verification') {
      // Get cities needing verification
      const limit = parseInt(searchParams.get('limit') || '20', 10);
      const cities = await getCitiesNeedingVerification(limit);

      return NextResponse.json({
        cities,
        count: cities.length,
      });
    }

    // Default: return monitoring summary
    const summary = await getMonitoringSummary();

    return NextResponse.json(summary);
  } catch (error) {
    console.error('Monitoring API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch monitoring data' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/monitoring/policies
 * Actions:
 * - run-check: Run batch monitoring check
 * - verify: Mark policies as verified
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    switch (action) {
      case 'run-check': {
        // Run batch monitoring check
        const results = await runBatchMonitoringCheck();

        const changedCount = results.filter((r) => r.changed).length;
        const errorCount = results.filter((r) => r.error).length;

        return NextResponse.json({
          checked: results.length,
          changed: changedCount,
          errors: errorCount,
          results,
        });
      }

      case 'verify': {
        // Mark policies as verified
        const { policyIds, verifiedBy, confidenceScore, notes } = body;

        if (!Array.isArray(policyIds) || policyIds.length === 0) {
          return NextResponse.json(
            { error: 'policyIds must be a non-empty array' },
            { status: 400 }
          );
        }

        if (!verifiedBy) {
          return NextResponse.json(
            { error: 'verifiedBy is required' },
            { status: 400 }
          );
        }

        if (typeof confidenceScore !== 'number' || confidenceScore < 1 || confidenceScore > 5) {
          return NextResponse.json(
            { error: 'confidenceScore must be between 1 and 5' },
            { status: 400 }
          );
        }

        if (policyIds.length === 1) {
          // Single verification
          await markPolicyAsVerified(
            policyIds[0],
            verifiedBy,
            confidenceScore,
            notes
          );

          return NextResponse.json({
            success: true,
            verified: 1,
          });
        } else {
          // Bulk verification
          const result = await bulkMarkPoliciesAsVerified(
            policyIds,
            verifiedBy,
            confidenceScore
          );

          return NextResponse.json({
            success: true,
            verified: result.success.length,
            failed: result.failed.length,
            failedPolicies: result.failed,
          });
        }
      }

      default:
        return NextResponse.json(
          { error: 'Invalid action. Use "run-check" or "verify"' },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Monitoring POST error:', error);
    return NextResponse.json(
      { error: 'Failed to process monitoring action' },
      { status: 500 }
    );
  }
}
