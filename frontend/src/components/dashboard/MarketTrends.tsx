"use client";
import React from "react";
import { PriceTrendChart } from "@/components/charts/PriceTrendChart";
import { RevenueExpensesChart } from "@/components/charts/RevenueExpensesChart";
import { PriceTrendDataPoint, RevenueExpensesDataPoint } from "@/lib/mockData";

interface MarketTrendsProps {
    priceTrend: PriceTrendDataPoint[];
    revenueExpenses: RevenueExpensesDataPoint[];
}

export const MarketTrends: React.FC<MarketTrendsProps> = ({
    priceTrend,
    revenueExpenses,
}) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Price vs Market Trend */}
            <div className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm p-4">
                <h3 className="text-[13px] font-semibold text-[#101828] mb-3">
                    Price vs Market Trend
                </h3>
                <PriceTrendChart data={priceTrend} />
            </div>

            {/* Revenue vs Expenses */}
            <div className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm p-4">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h3 className="text-[13px] font-semibold text-[#101828]">Revenue vs Expenses</h3>
                        <p className="text-[10px] text-[#9CA3AF] mt-0.5">12-month overview</p>
                    </div>
                    {/* Legend */}
                    <div className="flex items-center gap-3 text-[11px] text-[#6B7280]">
                        <span className="flex items-center gap-1">
                            <span className="inline-block w-5 h-0.5 bg-[#3B82F6]" />
                            Revenue
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="inline-block w-5 h-0.5 bg-[#12B76A]" />
                            Expenses
                        </span>
                    </div>
                </div>
                <RevenueExpensesChart data={revenueExpenses} />
            </div>
        </div>
    );
};
