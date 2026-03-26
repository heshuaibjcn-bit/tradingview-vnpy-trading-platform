/**
 * Policy Data Freshness Badge
 * Displays the freshness status of policy data
 *
 * Usage:
 *   <PolicyFreshnessBadge
 *     lastVerifiedAt={policy.last_verified_at}
 *     confidenceScore={policy.confidence_score}
 *   />
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import {
  formatDaysSinceVerification,
  getFreshnessBadgeColor,
  getFreshnessBadgeText,
  getPolicyFreshness,
} from '@/lib/monitoring/policy-monitor';
import type { CityPolicy } from '@/types/database';

interface PolicyFreshnessBadgeProps {
  lastVerifiedAt: string | null;
  confidenceScore: number;
  className?: string;
  showDaysSince?: boolean;
}

export function PolicyFreshnessBadge({
  lastVerifiedAt,
  confidenceScore,
  className = '',
  showDaysSince = false,
}: PolicyFreshnessBadgeProps) {
  // Create a minimal policy object for freshness calculation
  const policy: CityPolicy = {
    id: 'dummy',
    city_name: 'dummy',
    province_code: 'XX',
    province_name: 'dummy',
    peak_price: 0,
    valley_price: 0,
    flat_price: 0,
    peak_hours: '',
    valley_hours: '',
    subsidy_amount: 0,
    source_url: '',
    effective_date: '',
    last_verified_at: lastVerifiedAt,
    verification_method: 'manual',
    confidence_score: confidenceScore,
    created_at: '',
    updated_at: '',
  };

  const freshness = getPolicyFreshness(policy);
  const badgeColor = getFreshnessBadgeColor(freshness.status);
  const badgeText = getFreshnessBadgeText(freshness.status);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Badge variant={badgeColor} className="text-xs">
        {badgeText}
      </Badge>

      {showDaysSince && freshness.days_since_verification !== null && (
        <span className="text-xs text-muted-foreground">
          ({formatDaysSinceVerification(freshness.days_since_verification)})
        </span>
      )}

      {freshness.confidence_score !== null && freshness.confidence_score < 4 && (
        <span
          className="text-xs text-muted-foreground"
          title={`数据可信度: ${freshness.confidence_score}/5`}
        >
          可信度 {freshness.confidence_score}/5
        </span>
      )}
    </div>
  );
}
