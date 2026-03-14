"use client";
import React, { Suspense, useEffect, useState } from "react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { DashboardHeader } from "@/components/layout/DashboardHeader";
import { PropertyVerdict } from "@/components/dashboard/PropertyVerdict";
import { PropertyContext } from "@/components/dashboard/PropertyContext";
import { LocationIntelligence } from "@/components/dashboard/LocationIntelligence";
import { FinancialMetrics } from "@/components/dashboard/FinancialMetrics";
import { MarketTrends } from "@/components/dashboard/MarketTrends";
import { ComparableListings } from "@/components/dashboard/ComparableListings";

import mockDashboardData from "@/lib/mockData";
import type { PriceTrendDataPoint, RevenueExpensesDataPoint } from "@/types/marketTrends";
import { parseMarketTrendsResponse } from "@/lib/marketTrends";

import aiCustomizationIcon from "@/assets/dashboard/chat/ai-customization.svg";
import feedbackIcon from "@/assets/dashboard/chat/feedback.svg";
import closeIcon from "@/assets/dashboard/chat/close.svg";

/**
 * Dashboard Page – /dashboard
 *
 * Uses mock data from src/lib/mockData.ts.
 * To connect real backend data, replace `mockDashboardData` with
 * `await fetch('/api/property/[id]')` — the TypeScript types already
 * match the expected API shape.
 */
function DashboardPageContent() {
    const searchParams = useSearchParams();
    const propertyIdParam = searchParams?.get("property_id");
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'ai' | 'feedback'>('ai');

    const [priceTrend, setPriceTrend] = useState<PriceTrendDataPoint[]>([]);
    const [revenueExpenses, setRevenueExpenses] = useState<RevenueExpensesDataPoint[]>([]);

    const {
        property,
        insight,
        financialMetrics,
        locationScores,
        comparableListings,
    } = mockDashboardData;

    useEffect(() => {
        const controller = new AbortController();
        const propertyId = propertyIdParam || process.env.NEXT_PUBLIC_DEFAULT_PROPERTY_ID;

        if (!propertyId) {
            return () => controller.abort();
        }

        const propertyIdSafe = propertyId;

        async function loadTrends() {
            try {
                const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
                const res = await fetch(`${baseUrl}/api/market-trends?property_id=${encodeURIComponent(propertyIdSafe)}`, {
                    signal: controller.signal,
                    cache: "no-store",
                });
                if (!res.ok) return;

                const json: unknown = await res.json();
                const parsed = parseMarketTrendsResponse(json);
                setPriceTrend(parsed.priceTrend);
                setRevenueExpenses(parsed.revenueExpenses);
            } catch {
                // Keep empty series on error.
            }
        }

        loadTrends();
        return () => controller.abort();
    }, [propertyIdParam]);

    return (
        <div className="min-h-screen bg-[#F3F4F6] font-sans relative">
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
                            <div className="px-5 pt-4 pb-3 border-b border-[#F3F4F6]">
                                <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
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

            {/* Floating Chat Button and Dialog */}
            <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
                {isChatOpen && (
                    <div className="w-[380px] bg-white rounded-xl shadow-[0px_8px_32px_rgba(0,0,0,0.12)] border border-[#E5E7EB] overflow-hidden flex flex-col origin-bottom-right animate-in fade-in zoom-in-95 duration-200">
                        {/* Header Tabs */}
                        <div className="flex items-center justify-between px-2 pt-2 border-b border-[#F3F4F6] relative">
                            <div className="flex items-center gap-1">
                                <button
                                    onClick={() => setActiveTab('ai')}
                                    className={`flex items-center gap-1.5 px-3 py-2.5 transition text-[13px] ${activeTab === 'ai' ? 'border-b-2 border-[#101828] font-bold text-[#101828]' : 'font-semibold text-[#9CA3AF] hover:text-[#6B7280]'}`}
                                >
                                    <Image src={aiCustomizationIcon} alt="AI" width={14} height={14} className={activeTab === 'ai' ? '' : 'opacity-60'} />
                                    AI Customization
                                </button>
                                <button
                                    onClick={() => setActiveTab('feedback')}
                                    className={`flex items-center gap-1.5 px-3 py-2.5 transition text-[13px] mb-[2px] ${activeTab === 'feedback' ? 'border-b-2 border-[#101828] font-bold text-[#101828]' : 'font-semibold text-[#9CA3AF] hover:text-[#6B7280]'}`}
                                >
                                    <Image src={feedbackIcon} alt="Feedback" width={14} height={14} className={activeTab === 'feedback' ? 'brightness-0' : ''} />
                                    Feedback
                                </button>
                            </div>
                            <button onClick={() => setIsChatOpen(false)} className="p-1.5 hover:bg-[#F3F4F6] rounded-md transition absolute right-3 top-3">
                                <Image src={closeIcon} alt="Close" width={10} height={10} />
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-5 flex flex-col gap-4">
                            <p className="text-[13px] text-[#6B7280] leading-relaxed pr-2">
                                {activeTab === 'ai'
                                    ? "Tell the AI what you value most. We'll remember your preferences for future analyses."
                                    : "Found a bug or have a suggestion? Let us know how we can improve Housmart."}
                            </p>

                            <textarea
                                className="w-full h-[120px] resize-none bg-[#F9FAFB] border border-[#F3F4F6] rounded-xl p-3.5 text-[13px] text-[#101828] placeholder:text-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-[#E5E7EB]"
                                placeholder={activeTab === 'ai'
                                    ? "E.g., 'I prefer walkable neighborhoods', 'Avoid heavy traffic...'"
                                    : "Describe the issue or suggestion..."}
                            />

                            <div className="flex items-center justify-end gap-3 mt-1">
                                <button onClick={() => setIsChatOpen(false)} className="text-[13px] font-semibold text-[#6B7280] hover:text-[#374151] px-2 py-2 transition">
                                    Cancel
                                </button>
                                <button onClick={() => setIsChatOpen(false)} className="text-[13px] font-semibold bg-[#101828] text-white px-4 py-2 rounded-lg hover:bg-[#1D2939] transition">
                                    {activeTab === 'ai' ? 'Save' : 'Send'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <button
                    onClick={() => setIsChatOpen(!isChatOpen)}
                    className="w-[52px] h-[52px] rounded-full bg-[#101828] flex items-center justify-center shadow-2xl hover:bg-[#1D2939] transition"
                >
                    {isChatOpen ? (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    ) : (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                    )}
                </button>
            </div>
        </div>
    );
}

export default function DashboardPage() {
    return (
        <Suspense fallback={null}>
            <DashboardPageContent />
        </Suspense>
    );
}
