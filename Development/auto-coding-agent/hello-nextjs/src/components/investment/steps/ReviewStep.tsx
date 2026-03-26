/**
 * Step 5: Review and Confirm
 */

'use client';

import { CityData } from '@/lib/investment/cities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface ReviewStepProps {
  city: CityData;
  systemSpecs: {
    capacity_mwh: number;
    power_mw: number;
    discharge_efficiency: number;
    cycle_life: number;
    daily_cycles: number;
  };
  financialParams: {
    equipment_cost_per_mwh: number;
    installation_cost_per_mwh: number;
    grid_connection_cost: number;
    annual_maintenance_cost_percent: number;
    insurance_cost_percent: number;
    project_lifetime_years: number;
    discount_rate: number;
    inflation_rate: number;
  };
  scenario: string;
}

export function ReviewStep({
  city,
  systemSpecs,
  financialParams,
  scenario,
}: ReviewStepProps) {
  const totalCAPEX =
    systemSpecs.capacity_mwh *
    (financialParams.equipment_cost_per_mwh + financialParams.installation_cost_per_mwh) +
    financialParams.grid_connection_cost;

  const scenarioNames = {
    optimistic: '乐观情景',
    base: '基准情景',
    conservative: '保守情景',
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">确认信息</h3>
        <p className="text-sm text-muted-foreground">
          请确认以下信息无误后，点击"开始计算"
        </p>
      </div>

      {/* City & Scenario */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">投资地点 & 情景</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">城市</p>
              <p className="font-semibold">{city.name}</p>
              <p className="text-xs text-muted-foreground">{city.province}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">分析情景</p>
              <p className="font-semibold">{scenarioNames[scenario as keyof typeof scenarioNames]}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Specs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">系统规格</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">装机容量</p>
              <p className="font-semibold">{systemSpecs.capacity_mwh} MWh</p>
            </div>
            <div>
              <p className="text-muted-foreground">额定功率</p>
              <p className="font-semibold">{systemSpecs.power_mw} MW</p>
            </div>
            <div>
              <p className="text-muted-foreground">充放电效率</p>
              <p className="font-semibold">{(systemSpecs.discharge_efficiency * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-muted-foreground">循环寿命</p>
              <p className="font-semibold">{systemSpecs.cycle_life.toLocaleString()} 次</p>
            </div>
            <div>
              <p className="text-muted-foreground">每日循环</p>
              <p className="font-semibold">{systemSpecs.daily_cycles} 次</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Financial Params */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">财务参数</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">设备成本</p>
              <p className="font-semibold">
                {(financialParams.equipment_cost_per_mwh / 10000).toFixed(0)} 万元/MWh
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">安装成本</p>
              <p className="font-semibold">
                {(financialParams.installation_cost_per_mwh / 10000).toFixed(0)} 万元/MWh
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">电网接入</p>
              <p className="font-semibold">
                {(financialParams.grid_connection_cost / 10000).toFixed(0)} 万元
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">项目寿命</p>
              <p className="font-semibold">{financialParams.project_lifetime_years} 年</p>
            </div>
          </div>

          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm">总投资 (CAPEX)</span>
              <span className="text-xl font-bold text-primary">
                {(totalCAPEX / 10000).toFixed(0)} 万元
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Electricity Rates */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">电价信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">峰时电价</p>
              <p className="font-semibold text-red-600">{city.peak_price} 元/kWh</p>
            </div>
            <div>
              <p className="text-muted-foreground">谷时电价</p>
              <p className="font-semibold text-green-600">{city.valley_price} 元/kWh</p>
            </div>
            <div>
              <p className="text-muted-foreground">价差</p>
              <p className="font-semibold text-primary">
                {(city.peak_price - city.valley_price).toFixed(2)} 元/kWh
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Calculation Notice */}
      <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-md border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>点击"开始计算"后</strong>，系统将根据上述参数计算：
        </p>
        <ul className="text-xs text-blue-700 dark:text-blue-300 mt-2 space-y-1">
          <li>• 内部收益率 (IRR)</li>
          <li>• 净现值 (NPV)</li>
          <li>• 投资回收期</li>
          <li>• 年度现金流预测</li>
          <li>• 投资建议</li>
        </ul>
      </div>
    </div>
  );
}
