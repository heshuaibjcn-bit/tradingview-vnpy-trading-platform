/**
 * Step 4: Scenario Selection
 */

'use client';

import { ScenarioType, scenarios } from '@/lib/investment/cities';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ScenarioStepProps {
  scenario: ScenarioType;
  onScenarioSelect: (scenario: ScenarioType) => void;
}

export function ScenarioStep({ scenario, onScenarioSelect }: ScenarioStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium mb-2">选择分析情景</h3>
        <p className="text-sm text-muted-foreground">
          不同情景假设会影响电价和补贴，从而影响投资回报
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((s) => {
          const isSelected = scenario === s.value;

          return (
            <Card
              key={s.value}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md',
                isSelected && 'ring-2 ring-primary'
              )}
              onClick={() => onScenarioSelect(s.value)}
            >
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{s.name}</h4>
                    {isSelected && <Badge>已选择</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {s.description}
                  </p>
                  <div className="flex items-center space-x-2">
                    <div
                      className={cn(
                        'w-3 h-3 rounded-full',
                        s.color
                      )}
                    />
                    <span className="text-xs text-muted-foreground">
                      {s.value === 'optimistic' && '高回报预期'}
                      {s.value === 'base' && '基准预期'}
                      {s.value === 'conservative' && '保守预期'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="p-4 bg-muted rounded-md">
        <p className="text-sm font-medium mb-2">情景说明:</p>
        <ul className="text-xs text-muted-foreground space-y-1">
          <li>• <strong>乐观情景:</strong> 峰谷价差扩大，补贴增加</li>
          <li>• <strong>基准情景:</strong> 基于当前政策</li>
          <li>• <strong>保守情景:</strong> 峰谷价差缩小，补贴减少</li>
        </ul>
      </div>
    </div>
  );
}
