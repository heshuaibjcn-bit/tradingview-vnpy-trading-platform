"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { STRATEGY_CONFIGS } from "@/lib/strategies/config";
import type { strategy_type } from "@/types/database";

interface CreateStrategyFormProps {
  userId: string;
  onCreated: () => void;
}

export function CreateStrategyForm({ userId, onCreated }: CreateStrategyFormProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"type" | "params">("type");
  const [selectedType, setSelectedType] = useState<strategy_type | null>(null);
  const [name, setName] = useState("");
  const [parameters, setParameters] = useState<Record<string, string | number | boolean>>({});
  const [symbols, setSymbols] = useState("");

  const config = selectedType ? STRATEGY_CONFIGS[selectedType] : null;

  const handleTypeSelect = (type: strategy_type) => {
    setSelectedType(type);
    setName(STRATEGY_CONFIGS[type].name);
    setParameters(STRATEGY_CONFIGS[type].defaultParams);
    setStep("params");
  };

  const handleParamChange = (key: string, value: string | number) => {
    setParameters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (enabled: boolean) => {
    if (!selectedType || !name) return;

    try {
      setLoading(true);
      const symbolList = symbols
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const res = await fetch("/api/strategies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          name,
          type: selectedType,
          parameters: { ...parameters, symbols: symbolList },
          enabled,
        }),
      });

      if (res.ok) {
        onCreated();
        handleClose();
      }
    } catch (error) {
      console.error("Failed to create strategy:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setStep("type");
    setSelectedType(null);
    setName("");
    setParameters({});
    setSymbols("");
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full py-4 border-2 border-dashed border-zinc-700 rounded-lg text-zinc-400 hover:border-zinc-600 hover:text-zinc-300 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="h-5 w-5" />
        <span>创建新策略</span>
      </button>
    );
  }

  return (
    <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-900/50">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-zinc-100">
          {step === "type" ? "选择策略类型" : "配置策略参数"}
        </h2>
        <button
          onClick={handleClose}
          className="text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          ✕
        </button>
      </div>

      {step === "type" && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(Object.entries(STRATEGY_CONFIGS) as [strategy_type, typeof STRATEGY_CONFIGS[keyof typeof STRATEGY_CONFIGS]][]).map(([type, config]) => (
            <button
              key={type}
              onClick={() => handleTypeSelect(type)}
              className="p-4 border border-zinc-700 rounded-lg hover:border-zinc-600 hover:bg-zinc-800/50 transition-all text-left"
            >
              <h3 className="font-semibold text-zinc-200 mb-1">{config.name}</h3>
              <p className="text-sm text-zinc-500">{config.description}</p>
            </button>
          ))}
        </div>
      )}

      {step === "params" && config && (
        <div className="space-y-6">
          {/* Strategy Name */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              策略名称
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600"
              placeholder="输入策略名称"
            />
          </div>

          {/* Parameters */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-zinc-400">策略参数</h3>
            {config.paramSchema.map((param) => (
              <div key={param.key}>
                <div className="flex justify-between mb-1">
                  <label className="text-sm text-zinc-500">{param.label}</label>
                  {param.description && (
                    <span className="text-xs text-zinc-600">{param.description}</span>
                  )}
                </div>
                <input
                  type={param.type === "number" ? "number" : "text"}
                  value={String(parameters[param.key] ?? param.default)}
                  onChange={(e) =>
                    handleParamChange(
                      param.key,
                      param.type === "number"
                        ? parseFloat(e.target.value) || 0
                        : e.target.value
                    )
                  }
                  min={param.min}
                  max={param.max}
                  step={param.step}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
                />
              </div>
            ))}
          </div>

          {/* Trading Symbols */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              交易标的（可选，用逗号分隔）
            </label>
            <input
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
              placeholder="例如: 000001, 600000, 600519"
            />
            <p className="text-xs text-zinc-600 mt-1">
              留空则监控所有股票
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-4 border-t border-zinc-800">
            <button
              onClick={() => handleSubmit(false)}
              disabled={loading || !name}
              className="flex-1 py-2 px-4 bg-zinc-700 hover:bg-zinc-600 disabled:bg-zinc-800 disabled:text-zinc-600 text-zinc-200 rounded-lg transition-colors"
            >
              {loading ? "保存中..." : "保存为草稿"}
            </button>
            <button
              onClick={() => handleSubmit(true)}
              disabled={loading || !name}
              className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg transition-colors"
            >
              {loading ? "保存中..." : "保存并启用"}
            </button>
            <button
              onClick={() => setStep("type")}
              className="py-2 px-4 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              返回
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
