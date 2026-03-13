"use client";
import React from "react";
import { PriceTrendChart } from "@/components/charts/PriceTrendChart";
import { RevenueExpensesChart } from "@/components/charts/RevenueExpensesChart";
import type { PriceTrendDataPoint, RevenueExpensesDataPoint } from "@/app/dashboard/dashboard-data";

interface MarketTrendsProps {
    priceTrend: PriceTrendDataPoint[];
    revenueExpenses: RevenueExpensesDataPoint[];
}

export const MarketTrends: React.FC<MarketTrendsProps> = ({
    priceTrend,
    revenueExpenses,
}) => {
    return (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            <div className="rounded-[12px] border border-[#E5E7EB] bg-white px-6 py-6">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[#6A7282]">
                    SALE-TO-LIST RATIO
                </h3>
                <p className="mt-0.5 mb-6 text-[10px] font-medium text-[#99A1AF]">3-year trend • Data from Redfin</p>
                <PriceTrendChart data={priceTrend} />
            </div>

            <div className="rounded-[12px] border border-[#E5E7EB] bg-white px-6 py-6">
                <div className="mb-6">
                    <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[#6A7282]">
                        MEDIAN SALE PRICE
                    </h3>
                    <p className="mt-0.5 text-[10px] font-medium text-[#99A1AF]">3-year trend • Data from Redfin</p>
                </div>
                <RevenueExpensesChart data={revenueExpenses} />
            </div>
        </div>
    );
};
