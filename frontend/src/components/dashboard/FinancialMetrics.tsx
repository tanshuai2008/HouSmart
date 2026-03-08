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
                        <div className="relative group self-start flex flex-col justify-end">
                            <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase cursor-help">
                                {metric.label}
                            </span>
                            {/* Tooltip */}
                            {metric.tooltipText && (
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-max max-w-[240px] hidden group-hover:block bg-white text-[#101828] font-medium text-[12px] leading-snug p-3 rounded-lg border border-[#E5E7EB] shadow-[0px_4px_16px_rgba(0,0,0,0.08)] z-[60]">
                                    {metric.tooltipText}
                                </div>
                            )}
                        </div>
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
