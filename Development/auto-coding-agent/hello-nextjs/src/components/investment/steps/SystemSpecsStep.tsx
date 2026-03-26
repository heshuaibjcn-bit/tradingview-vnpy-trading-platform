/**
 * Step 2: System Specifications
 */

'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface SystemSpecsStepProps {
  specs: {
    capacity_mwh: number;
    power_mw: number;
    discharge_efficiency: number;
    cycle_life: number;
    daily_cycles: number;
  };
  onChange: (specs: any) => void;
}

export function SystemSpecsStep({ specs, onChange }: SystemSpecsStepProps) {
  const updateSpec = (field: string, value: number) => {
    onChange({ ...specs, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">配置储能系统</h3>
        <p className="text-sm text-muted-foreground">
          设置储能系统的技术参数，这些参数将影响投资回报计算
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Capacity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">装机容量</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>容量 (MWh)</Label>
              <Input
                type="number"
                value={specs.capacity_mwh}
                onChange={(e) => updateSpec('capacity_mwh', parseFloat(e.target.value) || 0)}
                min={0.1}
                max={1000}
                step={0.5}
              />
              <p className="text-xs text-muted-foreground mt-1">
                当前: {specs.capacity_mwh} MWh
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Power */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">额定功率</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>功率 (MW)</Label>
              <Input
                type="number"
                value={specs.power_mw}
                onChange={(e) => updateSpec('power_mw', parseFloat(e.target.value) || 0)}
                min={0.1}
                max={1000}
                step={0.1}
              />
              <p className="text-xs text-muted-foreground mt-1">
                当前: {specs.power_mw} MW
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Efficiency */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">充放电效率</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>效率</Label>
              <span className="text-sm font-medium">{(specs.discharge_efficiency * 100).toFixed(0)}%</span>
            </div>
            <Slider
              value={[specs.discharge_efficiency * 100]}
              onValueChange={(value) => updateSpec('discharge_efficiency', value[0] / 100)}
              min={50}
              max={100}
              step={1}
            />
            <p className="text-xs text-muted-foreground mt-2">
              锂离子电池典型效率: 85-95%
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Cycle Life */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">循环寿命</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>循环次数</Label>
            <Input
              type="number"
              value={specs.cycle_life}
              onChange={(e) => updateSpec('cycle_life', parseInt(e.target.value) || 0)}
              min={1000}
              max={10000}
              step={500}
            />
            <p className="text-xs text-muted-foreground mt-1">
              当前: {specs.cycle_life.toLocaleString()} 次
            </p>
            <p className="text-xs text-muted-foreground">
              锂离子电池典型值: 5000-8000次
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Daily Cycles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">每日充放电次数</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>次数/天</Label>
              <span className="text-sm font-medium">{specs.daily_cycles}</span>
            </div>
            <Slider
              value={[specs.daily_cycles]}
              onValueChange={(value) => updateSpec('daily_cycles', value[0])}
              min={0.5}
              max={3}
              step={0.1}
            />
            <p className="text-xs text-muted-foreground mt-2">
              每天{specs.daily_cycles}次完整充放电循环
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
