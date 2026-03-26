/**
 * Investment Calculator Page
 */

import { InvestmentCalculatorForm } from '@/components/investment/InvestmentCalculatorForm';
import { Suspense } from 'react';

export const metadata = {
  title: '储能投资计算器',
  description: '专业的工商业储能项目投资回报分析工具',
};

export default function InvestmentPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">储能投资计算器</h1>
        <p className="text-muted-foreground">
          基于真实电价数据，计算工商业储能项目的投资回报
        </p>
      </div>

      <Suspense fallback={<div>加载中...</div>}>
        <InvestmentCalculatorForm />
      </Suspense>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-muted-foreground">
        <div>
          <h3 className="font-semibold mb-2">数据来源</h3>
          <ul className="space-y-1">
            <li>• 城市峰谷电价 (公开数据)</li>
            <li>• 补贴政策 (各地政府)</li>
            <li>• 设备成本 (市场调研)</li>
          </ul>
        </div>
        <div>
          <h3 className="font-semibold mb-2">计算方法</h3>
          <ul className="space-y-1">
            <li>• IRR: numpy-financial 库</li>
            <li>• NPV: 折现现金流分析</li>
            <li>• 回收期: 累计现金流法</li>
          </ul>
        </div>
        <div>
          <h3 className="font-semibold mb-2">免责声明</h3>
          <p>
            本工具仅供投资参考，不构成投资建议。
            实际投资需结合更多市场调研和风险评估。
          </p>
        </div>
      </div>
    </div>
  );
}
