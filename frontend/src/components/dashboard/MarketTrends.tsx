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
                <h3 className="text-[10px] font-semibold text-[#6B7280] tracking-[0.08em] uppercase">
                    SALE-TO-LIST RATIO
                </h3>
                <p className="text-[10px] text-[#9CA3AF] mt-1 mb-3">3-year trend • Data from Redfin</p>
                <PriceTrendChart data={priceTrend} />
            </div>

            {/* Revenue vs Expenses */}
            <div className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm p-4">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h3 className="text-[10px] font-semibold text-[#6B7280] tracking-[0.08em] uppercase">MEDIAN SALE PRICE</h3>
                        <p className="text-[10px] text-[#9CA3AF] mt-1">3-year trend • Data from Redfin</p>
                    </div>
                </div>
                <RevenueExpensesChart data={revenueExpenses} />
            </div>
        </div>
    );
};
