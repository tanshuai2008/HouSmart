"use client";
import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { FinancialMetric } from "@/lib/mockData";

interface FinancialMetricsProps {
    metrics: FinancialMetric[];
}

const trendIconMap = {
    up: TrendingUp,
    down: TrendingDown,
    neutral: Minus,
};

const trendColorClasses: Record<FinancialMetric["trendColor"], string> = {
    green: "text-[#027A48]",
    red: "text-[#B42318]",
    orange: "text-[#B54708]",
    neutral: "text-[#6B7280]",
};

export const FinancialMetrics: React.FC<FinancialMetricsProps> = ({ metrics }) => {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {metrics.map((metric) => {
                const TrendIcon = trendIconMap[metric.trend];
                const colorClass = trendColorClasses[metric.trendColor];
                return (
                    <div
                        key={metric.label}
                        className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm p-4 flex flex-col gap-1"
                    >
                        <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
                            {metric.label}
                        </span>
                        <span className="text-[22px] font-bold text-[#101828] leading-tight mt-0.5">
                            {metric.value}
                        </span>
                        <div className={`flex items-center gap-1 ${colorClass} mt-0.5`}>
                            <TrendIcon size={11} />
                            <span className="text-[11px] font-medium">{metric.subLabel}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
