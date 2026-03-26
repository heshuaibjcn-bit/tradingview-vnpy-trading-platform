/**
 * Step 6: Calculation Results
 */

'use client';

import { InvestmentAnalysis } from '@/types/investment';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface CalculationResultsStepProps {
  analysis: InvestmentAnalysis;
}

export function CalculationResultsStep({ analysis }: CalculationResultsStepProps) {
  const metrics = analysis.metrics;

  const formatCurrency = (value: number) => {
    if (Math.abs(value) >= 100000000) {
      return `${(value / 100000000).toFixed(2)} 亿元`;
    } else if (Math.abs(value) >= 10000) {
      return `${(value / 10000).toFixed(0)} 万元`;
    } else {
      return `${value.toFixed(0)} 元`;
    }
  };

  const getRecommendationBadge = () => {
    if (analysis.is_recommendable) {
      return <Badge className="bg-green-500">推荐投资</Badge>;
    } else {
      return <Badge variant="destructive">不推荐投资</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Recommendation Header */}
      <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">投资结论</h3>
            <p className="text-sm text-muted-foreground">
              {analysis.city_name} • {analysis.storage_system.capacity_mwh}MWh 储能项目
            </p>
          </div>
          {getRecommendationBadge()}
        </div>
        <p className="text-sm mt-3">{analysis.recommendation_reason}</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              内部收益率
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {metrics.irr_percent.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">IRR</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              净现值
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${metrics.npv >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(metrics.npv)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">NPV</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              投资回收期
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.payback_period_years === Infinity
                ? '无法回收'
                : `${metrics.payback_period_years.toFixed(1)} 年`}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Payback Period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              投资回报率
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.roi_percent.toFixed(0)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">ROI</p>
          </CardContent>
        </Card>
      </div>

      {/* Investment Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Revenue Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>年收入构成</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">套利收入</span>
                <span className="font-semibold">
                  {formatCurrency(metrics.annual_arbitrage_revenue)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">峰谷价差收益</span>
                <span className="font-semibold">
                  {formatCurrency(metrics.annual_peak_shaving_revenue)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">补贴收入</span>
                <span className="font-semibold">
                  {formatCurrency(metrics.annual_subsidy_revenue)}
                </span>
              </div>
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">总收入</span>
                  <span className="font-bold text-green-600">
                    {formatCurrency(metrics.annual_total_revenue)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Costs & Profit */}
        <Card>
          <CardHeader>
            <CardTitle>成本与利润</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">总投资 (CAPEX)</span>
                <span className="font-semibold">
                  {formatCurrency(metrics.total_capex)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">年运营成本</span>
                <span className="font-semibold text-red-600">
                  {formatCurrency(metrics.annual_operating_cost)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">年净利润</span>
                <span className="font-semibold text-primary">
                  {formatCurrency(metrics.annual_net_cash_flow)}
                </span>
              </div>
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">总利润</span>
                  <span className="font-bold text-primary">
                    {formatCurrency(metrics.total_profit)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cash Flow Table (First 10 years) */}
      <Card>
        <CardHeader>
          <CardTitle>现金流预测 (前10年)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3">年份</th>
                  <th className="text-right py-2 px-3">收入</th>
                  <th className="text-right py-2 px-3">成本</th>
                  <th className="text-right py-2 px-3">净现金流</th>
                  <th className="text-right py-2 px-3">累计现金流</th>
                </tr>
              </thead>
              <tbody>
                {analysis.cash_flows.slice(0, 10).map((cf) => (
                  <tr key={cf.year} className="border-b">
                    <td className="py-2 px-3">第{cf.year}年</td>
                    <td className="text-right py-2 px-3 text-green-600">
                      {formatCurrency(cf.total_revenue)}
                    </td>
                    <td className="text-right py-2 px-3 text-red-600">
                      {formatCurrency(cf.total_costs)}
                    </td>
                    <td
                      className={`text-right py-2 px-3 font-medium ${
                        cf.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {formatCurrency(cf.net_cash_flow)}
                    </td>
                    <td className="text-right py-2 px-3">
                      {formatCurrency(cf.cumulative_cash_flow)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {analysis.cash_flows.length > 10 && (
            <p className="text-xs text-muted-foreground mt-2">
              * 仅显示前10年，完整周期为 {analysis.cash_flows.length} 年
            </p>
          )}
        </CardContent>
      </Card>

      {/* System & Rates Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>系统规格</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">装机容量</span>
                <span className="font-medium">{analysis.storage_system.capacity_mwh} MWh</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">额定功率</span>
                <span className="font-medium">{analysis.storage_system.power_mw} MW</span>
              </div>
              {analysis.storage_system.daily_cycles !== undefined && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">每日循环</span>
                  <span className="font-medium">{analysis.storage_system.daily_cycles} 次</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">充放电效率</span>
                <span className="font-medium">
                  {analysis.storage_system.discharge_efficiency
                    ? `${(analysis.storage_system.discharge_efficiency * 100).toFixed(0)}%`
                    : '-'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">循环寿命</span>
                <span className="font-medium">
                  {analysis.storage_system.cycle_life
                    ? `${analysis.storage_system.cycle_life.toLocaleString()} 次`
                    : '-'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>电价政策</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">城市</span>
                <span className="font-medium">{analysis.electricity_rate.city_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">峰时电价</span>
                <span className="font-medium">
                  {analysis.electricity_rate.peak_price} 元/kWh
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">谷时电价</span>
                <span className="font-medium">
                  {analysis.electricity_rate.valley_price} 元/kWh
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">补贴</span>
                <span className="font-medium">
                  {analysis.electricity_rate.subsidy_amount} 元/kWh
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Disclaimer */}
      <div className="p-4 bg-muted rounded-md">
        <p className="text-xs text-muted-foreground">
          <strong>免责声明:</strong> 本计算结果基于当前可获得的数据和假设，
          仅供投资参考之用。实际投资决策需综合考虑更多因素。
          本系统不构成任何投资建议，投资者需自行承担投资风险。
        </p>
      </div>
    </div>
  );
}
