'use client';

/**
 * Policy Monitoring Dashboard
 * Admin panel for monitoring policy data freshness and verifying policies
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { PolicyFreshnessBadge } from '@/components/policy/PolicyFreshnessBadge';
import { AlertCircle, CheckCircle, RefreshCw, AlertTriangle } from 'lucide-react';
import type { CityPolicy, MonitoringSummary } from '@/types/database';

interface MonitoringResult {
  checked: number;
  changed: number;
  errors: number;
  results?: Array<{
    city_policy_id: string;
    city_name: string;
    checked: boolean;
    changed: boolean;
    error?: string;
  }>;
}

export function MonitoringDashboard() {
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [needsVerification, setNeedsVerification] = useState<CityPolicy[]>([]);
  const [selectedPolicies, setSelectedPolicies] = useState<Set<string>>(new Set());
  const [isRunningCheck, setIsRunningCheck] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [checkResult, setCheckResult] = useState<MonitoringResult | null>(null);
  const [verifiedBy, setVerifiedBy] = useState('admin');

  // Load monitoring data on mount
  useEffect(() => {
    loadMonitoringData();
  }, []);

  const loadMonitoringData = async () => {
    try {
      // Load summary
      const summaryRes = await fetch('/api/monitoring/policies');
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Load cities needing verification
      const citiesRes = await fetch('/api/monitoring/policies?action=needs-verification&limit=20');
      const citiesData = await citiesRes.json();
      setNeedsVerification(citiesData.cities);
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    }
  };

  const runMonitoringCheck = async () => {
    setIsRunningCheck(true);
    setCheckResult(null);

    try {
      const res = await fetch('/api/monitoring/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'run-check' }),
      });

      const result: MonitoringResult = await res.json();
      setCheckResult(result);

      // Reload data after check
      await loadMonitoringData();
    } catch (error) {
      console.error('Failed to run monitoring check:', error);
      alert('监控检查失败: ' + (error as Error).message);
    } finally {
      setIsRunningCheck(false);
    }
  };

  const markAsVerified = async () => {
    if (selectedPolicies.size === 0) {
      alert('请选择要验证的策略');
      return;
    }

    setIsVerifying(true);

    try {
      const res = await fetch('/api/monitoring/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'verify',
          policyIds: Array.from(selectedPolicies),
          verifiedBy,
          confidenceScore: 5, // Manual verification gets highest score
          notes: 'Admin verified via monitoring dashboard',
        }),
      });

      const result = await res.json();

      if (res.ok) {
        alert(`成功验证 ${result.verified} 个策略`);
        setSelectedPolicies(new Set());
        await loadMonitoringData();
      } else {
        alert(`验证失败: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to verify policies:', error);
      alert('验证失败: ' + (error as Error).message);
    } finally {
      setIsVerifying(false);
    }
  };

  const togglePolicySelection = (policyId: string) => {
    const newSelected = new Set(selectedPolicies);
    if (newSelected.has(policyId)) {
      newSelected.delete(policyId);
    } else {
      newSelected.add(policyId);
    }
    setSelectedPolicies(newSelected);
  };

  const selectAll = () => {
    setSelectedPolicies(new Set(needsVerification.map((p) => p.id)));
  };

  const deselectAll = () => {
    setSelectedPolicies(new Set());
  };

  if (!summary) {
    return <div>加载中...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Monitoring Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">总策略数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_policies}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">数据最新</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {summary.fresh_policies}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">可能过时</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {summary.warning_policies}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">已过时/未验证</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {summary.stale_policies + summary.unknown_policies}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>监控操作</CardTitle>
          <CardDescription>
            运行监控检查以检测政策变化，或标记策略为已验证
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button
              onClick={runMonitoringCheck}
              disabled={isRunningCheck}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRunningCheck ? 'animate-spin' : ''}`} />
              {isRunningCheck ? '检查中...' : '运行监控检查'}
            </Button>
          </div>

          {checkResult && (
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>
                  检查完成: 检查了 {checkResult.checked} 个策略，
                  发现 {checkResult.changed} 个变化，
                  {checkResult.errors} 个错误
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cities Needing Verification */}
      <Card>
        <CardHeader>
          <CardTitle>需要验证的策略</CardTitle>
          <CardDescription>
            以下策略数据已过时或从未验证，需要人工验证
          </CardDescription>
        </CardHeader>
        <CardContent>
          {needsVerification.length === 0 ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-8">
              <CheckCircle className="h-4 w-4" />
              <span>所有策略数据都是最新的</span>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm text-muted-foreground">
                  已选择 {selectedPolicies.size} / {needsVerification.length} 个策略
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={selectAll}>
                    全选
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={deselectAll}
                    disabled={selectedPolicies.size === 0}
                  >
                    取消全选
                  </Button>
                  <Button
                    size="sm"
                    onClick={markAsVerified}
                    disabled={selectedPolicies.size === 0 || isVerifying}
                  >
                    {isVerifying ? '验证中...' : '标记为已验证'}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                {needsVerification.map((policy) => (
                  <div
                    key={policy.id}
                    className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50"
                  >
                    <Checkbox
                      checked={selectedPolicies.has(policy.id)}
                      onCheckedChange={() => togglePolicySelection(policy.id)}
                    />

                    <div className="flex-1">
                      <div className="font-medium">{policy.city_name}</div>
                      <div className="text-sm text-muted-foreground">
                        {policy.province_name} - 峰时电价: ¥{policy.peak_price}/kWh
                      </div>
                    </div>

                    <PolicyFreshnessBadge
                      lastVerifiedAt={policy.last_verified_at}
                      confidenceScore={policy.confidence_score}
                      showDaysSince
                    />

                    <a
                      href={policy.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline"
                    >
                      查看官方来源
                    </a>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
