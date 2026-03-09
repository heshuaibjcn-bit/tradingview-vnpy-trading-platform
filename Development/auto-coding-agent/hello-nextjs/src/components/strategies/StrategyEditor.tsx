"use client";

import { useState } from "react";
import { ArrowLeft, Plus, X } from "lucide-react";
import type { Strategy, Json } from "@/types/database";

type StrategyType = "ma" | "macd" | "kdj" | "breakout" | "grid";

interface StrategyEditorProps {
  strategy: Strategy | null;
  onSave: (strategy: Omit<Strategy, "id" | "user_id" | "created_at" | "updated_at"> & { parameters: Json }) => void;
  onCancel: () => void;
  strategyTypes: Record<string, { name: string; description: string }>;
}

interface ParameterField {
  key: string;
  label: string;
  type: "number" | "text" | "array";
  default: unknown;
  placeholder?: string;
}

const PARAMETER_FIELDS: Record<StrategyType, ParameterField[]> = {
  ma: [
    { key: "shortPeriod", label: "短期均线周期", type: "number", default: 5, placeholder: "如: 5" },
    { key: "longPeriod", label: "长期均线周期", type: "number", default: 20, placeholder: "如: 20" },
    { key: "symbols", label: "监控股票", type: "array", default: [], placeholder: "输入股票代码" },
  ],
  macd: [
    { key: "fastPeriod", label: "快线周期", type: "number", default: 12, placeholder: "如: 12" },
    { key: "slowPeriod", label: "慢线周期", type: "number", default: 26, placeholder: "如: 26" },
    { key: "signalPeriod", label: "信号线周期", type: "number", default: 9, placeholder: "如: 9" },
    { key: "symbols", label: "监控股票", type: "array", default: [], placeholder: "输入股票代码" },
  ],
  kdj: [
    { key: "kPeriod", label: "K线周期", type: "number", default: 9, placeholder: "如: 9" },
    { key: "dPeriod", label: "D线周期", type: "number", default: 3, placeholder: "如: 3" },
    { key: "jPeriod", label: "J线周期", type: "number", default: 3, placeholder: "如: 3" },
    { key: "symbols", label: "监控股票", type: "array", default: [], placeholder: "输入股票代码" },
  ],
  breakout: [
    { key: "period", label: "突破周期", type: "number", default: 20, placeholder: "如: 20" },
    { key: "threshold", label: "突破阈值(%)", type: "number", default: 2, placeholder: "如: 2" },
    { key: "symbols", label: "监控股票", type: "array", default: [], placeholder: "输入股票代码" },
  ],
  grid: [
    { key: "upperPrice", label: "上限价格", type: "number", default: 0, placeholder: "如: 15.00" },
    { key: "lowerPrice", label: "下限价格", type: "number", default: 0, placeholder: "如: 10.00" },
    { key: "gridCount", label: "网格数量", type: "number", default: 10, placeholder: "如: 10" },
    { key: "symbols", label: "监控股票", type: "array", default: [], placeholder: "输入股票代码" },
  ],
};

export function StrategyEditor({ strategy, onSave, onCancel, strategyTypes }: StrategyEditorProps) {
  const [name, setName] = useState(strategy?.name || "");
  const [type, setType] = useState<StrategyType>((strategy?.type as StrategyType) || "ma");
  const [enabled, setEnabled] = useState(strategy?.enabled ?? true);
  const [parameters, setParameters] = useState<Record<string, unknown>>(
    (strategy?.parameters as Record<string, unknown>) || {}
  );
  const [symbolInput, setSymbolInput] = useState("");

  const isEdit = !!strategy;

  const handleSave = () => {
    if (!name.trim()) {
      alert("请输入策略名称");
      return;
    }

    const params = { ...parameters };

    // Ensure symbols array exists
    if (!params.symbols || !Array.isArray(params.symbols)) {
      params.symbols = [];
    }

    onSave({
      name: name.trim(),
      type,
      enabled,
      parameters: params as Json,
    });
  };

  const updateParameter = (key: string, value: unknown) => {
    setParameters((prev) => ({ ...prev, [key]: value }));
  };

  const addSymbol = () => {
    if (symbolInput.trim()) {
      const symbols = (parameters.symbols as string[]) || [];
      if (!symbols.includes(symbolInput.trim())) {
        updateParameter("symbols", [...symbols, symbolInput.trim()]);
      }
      setSymbolInput("");
    }
  };

  const removeSymbol = (symbol: string) => {
    const symbols = (parameters.symbols as string[]) || [];
    updateParameter("symbols", symbols.filter((s) => s !== symbol));
  };

  const currentFields = PARAMETER_FIELDS[type];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={onCancel}
          className="rounded p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {isEdit ? "编辑策略" : "新建策略"}
          </h2>
          <p className="text-sm text-zinc-500">
            {isEdit ? "修改策略参数和配置" : "创建一个新的交易策略"}
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="max-w-2xl rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        {/* Strategy Name */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            策略名称
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="给您的策略起个名字"
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>

        {/* Strategy Type */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            策略类型
          </label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as StrategyType)}
            disabled={isEdit}
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 disabled:opacity-50"
          >
            {Object.entries(strategyTypes).map(([key, { name, description }]) => (
              <option key={key} value={key}>
                {name} - {description}
              </option>
            ))}
          </select>
        </div>

        {/* Strategy Type Description */}
        <div className="mb-6 rounded-lg bg-zinc-50 p-4 dark:bg-zinc-800">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {strategyTypes[type].description}
          </p>
        </div>

        {/* Parameters */}
        <div className="mb-6 space-y-4">
          <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">策略参数</h3>

          {currentFields.map((field) => (
            <div key={field.key}>
              <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                {field.label}
              </label>

              {field.type === "array" ? (
                <div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={symbolInput}
                      onChange={(e) => setSymbolInput(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && addSymbol()}
                      placeholder={field.placeholder}
                      className="flex-1 rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                    <button
                      onClick={addSymbol}
                      className="flex items-center gap-1 rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
                    >
                      <Plus className="h-4 w-4" />
                      添加
                    </button>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {((parameters.symbols as string[]) || []).map((symbol) => (
                      <span
                        key={symbol}
                        className="flex items-center gap-1 rounded-full bg-zinc-100 px-3 py-1 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                      >
                        {symbol}
                        <button
                          onClick={() => removeSymbol(symbol)}
                          className="hover:text-red-500"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <input
                  type={field.type}
                  value={(parameters[field.key] as number | string) ?? field.default}
                  onChange={(e) => {
                    const value = field.type === "number" ? parseFloat(e.target.value) : e.target.value;
                    updateParameter(field.key, value);
                  }}
                  placeholder={field.placeholder}
                  className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
              )}
            </div>
          ))}
        </div>

        {/* Enabled Toggle */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">启用策略</p>
            <p className="text-xs text-zinc-500">创建后自动开始运行</p>
          </div>
          <button
            onClick={() => setEnabled(!enabled)}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              enabled ? "bg-zinc-900" : "bg-zinc-300 dark:bg-zinc-700"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${
                enabled ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg border border-zinc-300 px-6 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            className="rounded-lg bg-zinc-900 px-6 py-2.5 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            {isEdit ? "保存修改" : "创建策略"}
          </button>
        </div>
      </div>
    </div>
  );
}
