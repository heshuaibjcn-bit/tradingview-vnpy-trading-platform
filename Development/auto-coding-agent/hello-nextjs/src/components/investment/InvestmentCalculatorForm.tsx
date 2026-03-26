/**
 * Investment Calculator Form Component
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScenarioType, CityData } from '@/lib/investment/cities';
import type { InvestmentRequest } from '@/types/investment';
import { SelectCityStep } from './steps/SelectCityStep';
import { SystemSpecsStep } from './steps/SystemSpecsStep';
import { FinancialParamsStep } from './steps/FinancialParamsStep';
import { ScenarioStep } from './steps/ScenarioStep';
import { ReviewStep } from './steps/ReviewStep';
import { CalculationResultsStep } from './steps/CalculationResultsStep';
import { InvestmentAnalysis } from '@/types/investment';
import { Loader2 } from 'lucide-react';

type Step = 'city' | 'system' | 'financial' | 'scenario' | 'review' | 'results';

interface InvestmentCalculatorFormProps {
  onAnalysisComplete?: (analysis: InvestmentAnalysis) => void;
}

const steps: { id: Step; title: string; description: string }[] = [
  { id: 'city', title: '选择城市', description: '选择投资地点' },
  { id: 'system', title: '系统规格', description: '配置储能系统' },
  { id: 'financial', title: '财务参数', description: '设置投资参数' },
  { id: 'scenario', title: '分析情景', description: '选择分析情景' },
  { id: 'review', title: '确认信息', description: '确认并计算' },
  { id: 'results', title: '分析结果', description: '查看投资回报' },
];

export function InvestmentCalculatorForm({ onAnalysisComplete }: InvestmentCalculatorFormProps) {
  const [currentStep, setCurrentStep] = useState<Step>('city');
  const [isCalculating, setIsCalculating] = useState(false);
  const [calculationError, setCalculationError] = useState<string | null>(null);

  // Form state
  const [selectedCity, setSelectedCity] = useState<CityData | null>(null);
  const [systemSpecs, setSystemSpecs] = useState({
    capacity_mwh: 10,
    power_mw: 5,
    discharge_efficiency: 0.92,
    cycle_life: 6000,
    daily_cycles: 1.5,
  });
  const [financialParams, setFinancialParams] = useState({
    equipment_cost_per_mwh: 1500000,
    installation_cost_per_mwh: 300000,
    grid_connection_cost: 500000,
    annual_maintenance_cost_percent: 2.0,
    insurance_cost_percent: 0.5,
    project_lifetime_years: 15,
    discount_rate: 0.08,
    inflation_rate: 0.03,
  });
  const [scenario, setScenario] = useState<ScenarioType>('base');
  const [analysis, setAnalysis] = useState<InvestmentAnalysis | null>(null);

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);

  const canGoNext = () => {
    switch (currentStep) {
      case 'city':
        return selectedCity !== null;
      case 'system':
        return systemSpecs.capacity_mwh > 0 && systemSpecs.power_mw > 0;
      case 'financial':
        return (
          financialParams.equipment_cost_per_mwh > 0 &&
          financialParams.installation_cost_per_mwh > 0
        );
      case 'scenario':
        return true;
      case 'review':
        return true;
      default:
        return false;
    }
  };

  const handleNext = async () => {
    if (currentStep === 'review' && canGoNext()) {
      await performCalculation();
    } else if (canGoNext()) {
      const nextIndex = Math.min(currentStepIndex + 1, steps.length - 1);
      setCurrentStep(steps[nextIndex].id);
    }
  };

  const handleBack = () => {
    const prevIndex = Math.max(currentStepIndex - 1, 0);
    setCurrentStep(steps[prevIndex].id);
    setCalculationError(null);
  };

  const performCalculation = async () => {
    setIsCalculating(true);
    setCalculationError(null);

    try {
      const request: InvestmentRequest = {
        city_name: selectedCity!.name,
        province_code: selectedCity!.province_code,
        storage_system: systemSpecs,
        investment_params: financialParams,
        scenario,
      };

      const response = await fetch('/api/investment/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '计算失败');
      }

      const result: InvestmentAnalysis = await response.json();
      setAnalysis(result);
      setCurrentStep('results');
      onAnalysisComplete?.(result);
    } catch (error) {
      console.error('Calculation error:', error);
      setCalculationError(error instanceof Error ? error.message : '计算失败，请重试');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleReset = () => {
    setCurrentStep('city');
    setSelectedCity(null);
    setSystemSpecs({
      capacity_mwh: 10,
      power_mw: 5,
      discharge_efficiency: 0.92,
      cycle_life: 6000,
      daily_cycles: 1.5,
    });
    setFinancialParams({
      equipment_cost_per_mwh: 1500000,
      installation_cost_per_mwh: 300000,
      grid_connection_cost: 500000,
      annual_maintenance_cost_percent: 2.0,
      insurance_cost_percent: 0.5,
      project_lifetime_years: 15,
      discount_rate: 0.08,
      inflation_rate: 0.03,
    });
    setScenario('base');
    setAnalysis(null);
    setCalculationError(null);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'city':
        return (
          <SelectCityStep
            selectedCity={selectedCity}
            onCitySelect={setSelectedCity}
          />
        );
      case 'system':
        return (
          <SystemSpecsStep
            specs={systemSpecs}
            onChange={setSystemSpecs}
          />
        );
      case 'financial':
        return (
          <FinancialParamsStep
            params={financialParams}
            onChange={setFinancialParams}
          />
        );
      case 'scenario':
        return (
          <ScenarioStep
            scenario={scenario}
            onScenarioSelect={setScenario}
          />
        );
      case 'review':
        return (
          <ReviewStep
            city={selectedCity!}
            systemSpecs={systemSpecs}
            financialParams={financialParams}
            scenario={scenario}
          />
        );
      case 'results':
        return analysis ? (
          <CalculationResultsStep analysis={analysis} />
        ) : null;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <Card>
        <CardHeader>
          <CardTitle>储能项目投资计算器</CardTitle>
          <CardDescription>
            分步填写项目信息，系统将自动计算投资回报
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Progress Steps */}
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const isCompleted = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;

              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                        isCompleted
                          ? 'bg-primary text-primary-foreground'
                          : isCurrent
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {isCompleted ? '✓' : index + 1}
                    </div>
                    <div className="mt-2 text-xs text-center">
                      <div className="font-medium">{step.title}</div>
                      <div className="text-muted-foreground hidden sm:block">
                        {step.description}
                      </div>
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`h-0.5 flex-1 mx-2 transition-colors ${
                        index < currentStepIndex
                          ? 'bg-primary'
                          : 'bg-muted'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Current Step Content */}
      <Card>
        <CardContent className="pt-6">
          {calculationError && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-md">
              <p className="font-medium">计算失败</p>
              <p className="text-sm">{calculationError}</p>
            </div>
          )}
          {renderStep()}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      {currentStep !== 'results' && (
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 'city' || isCalculating}
          >
            上一步
          </Button>

          {currentStep === 'review' ? (
            <Button
              onClick={handleNext}
              disabled={!canGoNext() || isCalculating}
            >
              {isCalculating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  计算中...
                </>
              ) : (
                '开始计算'
              )}
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={!canGoNext()}
            >
              下一步
            </Button>
          )}
        </div>
      )}

      {currentStep === 'results' && (
        <div className="flex justify-between">
          <Button variant="outline" onClick={handleReset}>
            重新计算
          </Button>
          {analysis && (
            <Button
              onClick={async () => {
                try {
                  const response = await fetch('/api/investment/report/generate', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                      analysis,
                      include_charts: true,
                      language: 'zh',
                    }),
                  });

                  if (response.ok) {
                    const reportData = await response.json();
                    window.open(reportData.report_url, '_blank');
                  }
                } catch (error) {
                  console.error('Report generation error:', error);
                }
              }}
            >
              生成PDF报告
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
