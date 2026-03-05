import React from "react";
import { DashboardHeader } from "@/components/layout/DashboardHeader";
import { PropertyVerdict } from "@/components/dashboard/PropertyVerdict";
import { PropertyContext } from "@/components/dashboard/PropertyContext";
import { LocationIntelligence } from "@/components/dashboard/LocationIntelligence";
import { FinancialMetrics } from "@/components/dashboard/FinancialMetrics";
import { MarketTrends } from "@/components/dashboard/MarketTrends";
import { ComparableListings } from "@/components/dashboard/ComparableListings";

import mockDashboardData from "@/lib/mockData";

/**
 * Dashboard Page – /dashboard
 *
 * Uses mock data from src/lib/mockData.ts.
 * To connect real backend data, replace `mockDashboardData` with
 * `await fetch('/api/property/[id]')` — the TypeScript types already
 * match the expected API shape.
 */
export default function DashboardPage() {
    const {
        property,
        insight,
        financialMetrics,
        priceTrend,
        revenueExpenses,
        locationScores,
        comparableListings,
    } = mockDashboardData;

    return (
        <div className="min-h-screen bg-[#F3F4F6] font-sans">
            <DashboardHeader />

            <main className="px-5 py-5 max-w-[1340px] mx-auto">
                {/* Two-column grid: left main content | right sidebar */}
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4 items-start">

                    {/* ── LEFT COLUMN ── */}
                    <div className="flex flex-col gap-4 min-w-0">

                        {/* Property Verdict Card (with label inside) */}
                        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden">
                            {/* Section label */}
                            <div className="px-5 pt-4 pb-3 border-b border-[#F3F4F6]">
                                <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
                                    Property Verdict
                                </span>
                            </div>
                            <PropertyVerdict insight={insight as Parameters<typeof PropertyVerdict>[0]["insight"]} />
                        </div>

                        {/* Financial Metrics */}
                        <FinancialMetrics metrics={financialMetrics} />

                        {/* Market Trends */}
                        <MarketTrends priceTrend={priceTrend} revenueExpenses={revenueExpenses} />

                        {/* Comparable Listings */}
                        <ComparableListings listings={comparableListings} />
                    </div>

                    {/* ── RIGHT COLUMN ── */}
                    <div className="flex flex-col gap-4">
                        {/* Property Context */}
                        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden">
                            <div className="px-4 pt-4 pb-2">
                                <span className="text-[10px] font-semibold text-[#6B7280] tracking-[0.08em] uppercase">
                                    Property Context
                                </span>
                            </div>
                            <PropertyContext property={property} />
                        </div>

                        {/* Location Intelligence */}
                        <LocationIntelligence scores={locationScores} />
                    </div>
                </div>
            </main>

        </div>
    );
}
