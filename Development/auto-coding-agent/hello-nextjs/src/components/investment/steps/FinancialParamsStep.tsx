/**
 * Step 3: Financial Parameters
 */

'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FinancialParamsStepProps {
  params: {
    equipment_cost_per_mwh: number;
    installation_cost_per_mwh: number;
    grid_connection_cost: number;
    annual_maintenance_cost_percent: number;
    insurance_cost_percent: number;
    project_lifetime_years: number;
    discount_rate: number;
    inflation_rate: number;
  };
  onChange: (params: any) => void;
}

export function FinancialParamsStep({ params, onChange }: FinancialParamsStepProps) {
  const updateParam = (field: string, value: number) => {
    onChange({ ...params, [field]: value });
  };

  const calculateTotalCAPEX = () => {
    // Example: assuming 10 MWh system
    const exampleCapacity = 10;
    return (
      params.equipment_cost_per_mwh * exampleCapacity +
      params.installation_cost_per_mwh * exampleCapacity +
      params.grid_connection_cost
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">设置财务参数</h3>
        <p className="text-sm text-muted-foreground">
          输入设备成本、安装成本等财务参数
        </p>
      </div>

      {/* Capital Expenditure */}
      <div className="space-y-4">
        <h4 className="font-medium">资本支出 (CAPEX)</h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">设备成本</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>元/MWh</Label>
                <Input
                  type="number"
                  value={params.equipment_cost_per_mwh}
                  onChange={(e) =>
                    updateParam('equipment_cost_per_mwh', parseFloat(e.target.value) || 0)
                  }
                  min={100000}
                  max={10000000}
                  step={50000}
                />
                <p className="text-xs text-muted-foreground">
                  {(params.equipment_cost_per_mwh / 10000).toFixed(0)} 万元/MWh
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">安装成本</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>元/MWh</Label>
                <Input
                  type="number"
                  value={params.installation_cost_per_mwh}
                  onChange={(e) =>
                    updateParam('installation_cost_per_mwh', parseFloat(e.target.value) || 0)
                  }
                  min={50000}
                  max={5000000}
                  step={10000}
                />
                <p className="text-xs text-muted-foreground">
                  {(params.installation_cost_per_mwh / 10000).toFixed(0)} 万元/MWh
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">电网接入</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>元 (总成本)</Label>
                <Input
                  type="number"
                  value={params.grid_connection_cost}
                  onChange={(e) =>
                    updateParam('grid_connection_cost', parseFloat(e.target.value) || 0)
                  }
                  min={0}
                  max={5000000}
                  step={50000}
                />
                <p className="text-xs text-muted-foreground">
                  {(params.grid_connection_cost / 10000).toFixed(0)} 万元
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="p-4 bg-muted rounded-md">
          <p className="text-sm">
            <span className="font-medium">示例总投资 (10MWh系统): </span>
            <span className="text-primary font-semibold">
              {(calculateTotalCAPEX() / 10000).toFixed(0)} 万元
            </span>
          </p>
        </div>
      </div>

      {/* Operating Costs */}
      <div className="space-y-4">
        <h4 className="font-medium">运营成本 (OPEX)</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">年维护费</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>占CAPEX比例</Label>
                  <span className="text-sm font-medium">{params.annual_maintenance_cost_percent}%</span>
                </div>
                <Slider
                  value={[params.annual_maintenance_cost_percent]}
                  onValueChange={(value) => updateParam('annual_maintenance_cost_percent', value[0])}
                  min={0}
                  max={10}
                  step={0.1}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">保险费</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>占CAPEX比例</Label>
                  <span className="text-sm font-medium">{params.insurance_cost_percent}%</span>
                </div>
                <Slider
                  value={[params.insurance_cost_percent]}
                  onValueChange={(value) => updateParam('insurance_cost_percent', value[0])}
                  min={0}
                  max={5}
                  step={0.1}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Financial Parameters */}
      <div className="space-y-4">
        <h4 className="font-medium">财务参数</h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">项目寿命</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>年</Label>
                <Input
                  type="number"
                  value={params.project_lifetime_years}
                  onChange={(e) =>
                    updateParam('project_lifetime_years', parseInt(e.target.value) || 0)
                  }
                  min={5}
                  max={30}
                  step={1}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">折现率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between mb-2">
                  <Label>利率</Label>
                  <span className="text-sm font-medium">{(params.discount_rate * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[params.discount_rate * 100]}
                  onValueChange={(value) => updateParam('discount_rate', value[0] / 100)}
                  min={0}
                  max={30}
                  step={1}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">通胀率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between mb-2">
                  <Label>利率</Label>
                  <span className="text-sm font-medium">{(params.inflation_rate * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[params.inflation_rate * 100]}
                  onValueChange={(value) => updateParam('inflation_rate', value[0] / 100)}
                  min={0}
                  max={10}
                  step={0.5}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
