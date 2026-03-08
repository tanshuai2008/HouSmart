"use client";
import React from "react";
import { FinancialMetric } from "@/lib/mockData";

interface FinancialMetricsProps {
    metrics: FinancialMetric[];
}

export const FinancialMetrics: React.FC<FinancialMetricsProps> = ({ metrics }) => {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {metrics.map((metric) => {
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
                        <div className="flex items-center gap-1 text-[#6B7280] mt-0.5">
                            <span className="text-[11px] font-medium leading-tight">{metric.subLabel}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
