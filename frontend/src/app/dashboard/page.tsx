"use client";

import React, { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { MessageSquare, X } from "lucide-react";

import { DashboardHeader } from "@/components/layout/DashboardHeader";
import { ComparableListings } from "@/components/dashboard/ComparableListings";
import { FinancialMetrics } from "@/components/dashboard/FinancialMetrics";
import { LocationIntelligence } from "@/components/dashboard/LocationIntelligence";
import { MarketTrends } from "@/components/dashboard/MarketTrends";
import { PropertyContext } from "@/components/dashboard/PropertyContext";
import { PropertyVerdict } from "@/components/dashboard/PropertyVerdict";

import aiCustomizationIcon from "@/assets/dashboard/chat/ai-customization.svg";
import closeIcon from "@/assets/dashboard/chat/close.svg";
import feedbackIcon from "@/assets/dashboard/chat/feedback.svg";
import { useAuth } from "@/providers/auth-context";
import { getDashboardProperty, type DashboardPropertyPayload } from "@/lib/api/analysis";
import { fetchWithBackendFallback } from "@/lib/api/client";
import { parseMarketTrendsResponse } from "@/lib/marketTrends";
import type { PriceTrendDataPoint, RevenueExpensesDataPoint } from "@/types/marketTrends";

import { dashboardData } from "./dashboard-data";
import styles from "./dashboard-page.module.css";

type DashboardLoadStatus = "idle" | "loading" | "ready" | "error";

function DashboardSkeleton() {
    const metricLabels = dashboardData.financialMetrics.map((metric) => metric.label);

    return (
        <div className={styles.layoutGrid}>
            <div className={styles.leftColumn}>
                <section className={styles.sectionCard}>
                    <div className={styles.sectionHeader}>
                        <span className={styles.sectionLabel}>Property Verdict</span>
                    </div>
                    <div className="animate-pulse p-6">
                        <div className="h-6 w-28 rounded-full bg-slate-200" />
                        <div className="mt-5 h-8 w-3/4 rounded bg-slate-200" />
                        <div className="mt-3 h-4 w-full rounded bg-slate-100" />
                        <div className="mt-2 h-4 w-5/6 rounded bg-slate-100" />
                        <div className="mt-6 grid gap-4 md:grid-cols-2">
                            <div className="space-y-3">
                                <div className="h-4 w-28 rounded bg-slate-200" />
                                <div className="h-16 rounded-xl bg-slate-100" />
                                <div className="h-16 rounded-xl bg-slate-100" />
                            </div>
                            <div className="space-y-3">
                                <div className="h-4 w-28 rounded bg-slate-200" />
                                <div className="h-16 rounded-xl bg-slate-100" />
                                <div className="h-16 rounded-xl bg-slate-100" />
                            </div>
                        </div>
                    </div>
                </section>

                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    {metricLabels.map((label) => (
                        <div key={label} className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
                            <div className="animate-pulse">
                                <div className="h-3 w-24 rounded bg-slate-200" />
                                <div className="mt-3 h-8 w-20 rounded bg-slate-100" />
                                <div className="mt-2 h-3 w-full rounded bg-slate-100" />
                            </div>
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                    {[0, 1].map((index) => (
                        <div key={index} className="rounded-[12px] border border-[#E5E7EB] bg-white px-6 py-6">
                            <div className="animate-pulse">
                                <div className="h-3 w-28 rounded bg-slate-200" />
                                <div className="mt-2 h-3 w-36 rounded bg-slate-100" />
                                <div className="mt-8 h-[220px] rounded-xl bg-slate-100" />
                            </div>
                        </div>
                    ))}
                </div>

                <div className="overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <div className="flex items-center justify-between border-b border-[#F3F4F6] px-5 py-3.5">
                        <div className="h-3 w-32 animate-pulse rounded bg-slate-200" />
                        <div className="h-3 w-20 animate-pulse rounded bg-slate-100" />
                    </div>
                    <div className="animate-pulse px-5 py-4">
                        {[0, 1, 2].map((row) => (
                            <div key={row} className="grid grid-cols-6 gap-4 border-b border-[#F3F4F6] py-4 last:border-0">
                                {[0, 1, 2, 3, 4, 5].map((cell) => (
                                    <div key={cell} className="h-8 rounded bg-slate-100" />
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <aside className={styles.rightColumn}>
                <section className={styles.sectionCard}>
                    <div className={styles.sectionHeader}>
                        <span className={styles.sectionLabel}>Property Context</span>
                    </div>
                    <div className="animate-pulse px-5 py-5">
                        <div className="h-7 w-3/4 rounded bg-slate-200" />
                        <div className="mt-2 h-4 w-1/2 rounded bg-slate-100" />
                        <div className="mt-6 h-px w-full bg-slate-100" />
                        <div className="mt-4 grid grid-cols-2 gap-3">
                            {[0, 1, 2, 3].map((item) => (
                                <div key={item} className="h-5 rounded bg-slate-100" />
                            ))}
                        </div>
                    </div>
                </section>

                <section className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <div className="animate-pulse p-5">
                        <div className="h-3 w-32 rounded bg-slate-200" />
                        <div className="mt-5 space-y-4">
                            {[0, 1, 2, 3, 4].map((item) => (
                                <div key={item} className="flex items-center justify-between">
                                    <div className="h-5 w-32 rounded bg-slate-100" />
                                    <div className="h-4 w-16 rounded bg-slate-100" />
                                </div>
                            ))}
                        </div>
                        <div className="mt-6 h-52 rounded-xl bg-slate-100" />
                    </div>
                </section>
            </aside>
        </div>
    );
}

export default function DashboardPage() {
    const searchParams = useSearchParams();
    const { user } = useAuth();
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<"ai" | "feedback">("ai");
    const [status, setStatus] = useState<DashboardLoadStatus>("idle");
    const [dashboardError, setDashboardError] = useState<string | null>(null);
    const [dashboardPayload, setDashboardPayload] = useState<DashboardPropertyPayload | null>(null);

    const {
        comparableListings,
        financialMetrics,
        insight,
        locationScores,
        property,
    } = dashboardData;
    const [marketPriceTrend, setMarketPriceTrend] = useState<PriceTrendDataPoint[] | null>(null);
    const [marketRevenueExpenses, setMarketRevenueExpenses] = useState<RevenueExpensesDataPoint[] | null>(null);
    const propertyId = searchParams.get("property_id");

    useEffect(() => {
        const controller = new AbortController();
        let cancelled = false;

        const loadDashboard = async () => {
            if (!user?.id || !propertyId) {
                setStatus("idle");
                setDashboardError(null);
                setDashboardPayload(null);
                setMarketPriceTrend(null);
                setMarketRevenueExpenses(null);
                return;
            }

            setStatus("loading");
            setDashboardError(null);
            setDashboardPayload(null);
            setMarketPriceTrend(null);
            setMarketRevenueExpenses(null);

            try {
                const query = new URLSearchParams({ property_id: propertyId });
                const [payload, response] = await Promise.all([
                    getDashboardProperty(user.id, propertyId),
                    fetchWithBackendFallback(`/api/market-trends?${query.toString()}`, {
                        signal: controller.signal,
                    }),
                ]);

                if (cancelled) {
                    return;
                }

                if (!response.ok) {
                    throw new Error("Failed to fetch market trends");
                }

                const marketTrends = parseMarketTrendsResponse(await response.json());

                setDashboardPayload(payload);
                setMarketPriceTrend(marketTrends.priceTrend);
                setMarketRevenueExpenses(marketTrends.revenueExpenses);
                setStatus("ready");
            } catch (error) {
                if (cancelled || (error instanceof DOMException && error.name === "AbortError")) {
                    return;
                }

                setDashboardPayload(null);
                setMarketPriceTrend(null);
                setMarketRevenueExpenses(null);
                setDashboardError(error instanceof Error ? error.message : "Failed to load dashboard");
                setStatus("error");
            }
        };

        void loadDashboard();

        return () => {
            cancelled = true;
            controller.abort();
        };
    }, [propertyId, user?.id]);

    const mapData = useMemo(() => {
        const prop = dashboardPayload?.property ?? null;
        const toNumber = (value: unknown): number | null => {
            if (typeof value === "number" && Number.isFinite(value)) {
                return value;
            }
            if (typeof value === "string" && value.trim()) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : null;
            }
            return null;
        };

        return {
            address: typeof prop?.address === "string" ? prop.address : property.address,
            latitude: toNumber(prop?.latitude),
            longitude: toNumber(prop?.longitude),
        };
    }, [dashboardPayload?.property, property.address]);

    const contextProperty = useMemo(() => {
        const prop = dashboardPayload?.property ?? null;
        const toNumber = (value: unknown): number | null => {
            if (typeof value === "number" && Number.isFinite(value)) {
                return value;
            }
            if (typeof value === "string" && value.trim()) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : null;
            }
            return null;
        };

        const fullAddress =
            typeof prop?.address === "string" && prop.address.trim()
                ? prop.address.trim()
                : property.address;

        const firstCommaIndex = fullAddress.indexOf(",");
        const addressLineOne = firstCommaIndex === -1 ? fullAddress : fullAddress.slice(0, firstCommaIndex).trim();
        const addressLineTwo =
            firstCommaIndex === -1 ? property.neighborhood : fullAddress.slice(firstCommaIndex + 1).trim();

        const bedrooms = toNumber(prop?.bedrooms);
        const bathrooms = toNumber(prop?.bathrooms);
        const squareFootage = toNumber(prop?.square_footage);
        const yearBuilt = toNumber(prop?.year_built);

        return {
            address: addressLineOne,
            neighborhood: addressLineTwo,
            beds: bedrooms,
            baths: bathrooms,
            sqft: squareFootage !== null ? Math.round(squareFootage).toLocaleString() : null,
            yearBuilt: yearBuilt !== null ? Math.round(yearBuilt) : null,
        };
    }, [dashboardPayload?.property, property.address, property.neighborhood]);

    const dynamicLocationScores = useMemo(() => {
        const toNumber = (value: unknown): number | null => {
            if (typeof value === "number" && Number.isFinite(value)) {
                return value;
            }
            if (typeof value === "string" && value.trim()) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : null;
            }
            return null;
        };

        const scoresPayload = dashboardPayload?.scores ?? null;
        const factsPayload = dashboardPayload?.facts ?? null;

        const scoreToBars = (score: number): { tone: "positive" | "warning" | "negative"; filledBars: number } => {
            if (score > 75) {
                return { tone: "positive", filledBars: 3 };
            }
            if (score >= 40) {
                return { tone: "warning", filledBars: 2 };
            }
            return { tone: "negative", filledBars: 1 };
        };

        const noiseDbToBars = (noiseDb: number): { tone: "positive" | "warning" | "negative"; filledBars: number } => {
            if (noiseDb < 55) {
                return { tone: "positive", filledBars: 3 };
            }
            if (noiseDb <= 65) {
                return { tone: "warning", filledBars: 2 };
            }
            return { tone: "negative", filledBars: 1 };
        };

        const noiseScoreToBars = (noiseScore: number): { tone: "positive" | "warning" | "negative"; filledBars: number } => {
            if (noiseScore < 40) {
                return { tone: "positive", filledBars: 3 };
            }
            if (noiseScore <= 65) {
                return { tone: "warning", filledBars: 2 };
            }
            return { tone: "negative", filledBars: 1 };
        };

        const scoreValueMap: Record<string, number | null> = {
            "Safety Score": toNumber(scoresPayload?.safety_score),
            "Schools": toNumber(scoresPayload?.school_score),
            "Lifestyle Amenities": toNumber(scoresPayload?.amenity_score),
            "Transit Access": toNumber(scoresPayload?.transit_score),
        };

        const estimatedNoiseDb = toNumber(factsPayload?.estimated_noise_db);
        const noiseScoreFallback = toNumber(scoresPayload?.noise_score);

        return locationScores.map((item) => {
            if (item.label === "Noise Levels") {
                if (estimatedNoiseDb !== null) {
                    return {
                        ...item,
                        ...noiseDbToBars(estimatedNoiseDb),
                    };
                }
                if (noiseScoreFallback !== null) {
                    return {
                        ...item,
                        ...noiseScoreToBars(noiseScoreFallback),
                    };
                }
                return item;
            }

            const numericScore = scoreValueMap[item.label];
            if (numericScore === null) {
                return item;
            }

            return {
                ...item,
                ...scoreToBars(numericScore),
            };
        });
    }, [dashboardPayload?.facts, dashboardPayload?.scores, locationScores]);

    const dynamicFinancialMetrics = useMemo(() => {
        const toNumber = (value: unknown): number | null => {
            if (typeof value === "number" && Number.isFinite(value)) {
                return value;
            }
            if (typeof value === "string" && value.trim()) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : null;
            }
            return null;
        };

        const propertyPayload = dashboardPayload?.property ?? null;
        const factsPayload = dashboardPayload?.facts ?? null;

        const monthlyRent = toNumber(propertyPayload?.rent);
        const rentToPrice = toNumber(factsPayload?.rent_to_price);
        const affordabilityIndex = toNumber(factsPayload?.affordability_index);
        const tenantQualityIndex =
            typeof factsPayload?.tenant_quality_index === "string" && factsPayload.tenant_quality_index.trim()
                ? factsPayload.tenant_quality_index.trim()
                : null;

        return financialMetrics.map((metric) => {
            if (metric.label === "MONTHLY RENT") {
                return {
                    ...metric,
                    value: monthlyRent !== null ? `$${Math.round(monthlyRent).toLocaleString()} / mo` : "-",
                };
            }

            if (metric.label === "RENT-TO-PRICE") {
                return {
                    ...metric,
                    value: rentToPrice !== null ? `${rentToPrice.toFixed(1)}%` : "-",
                };
            }

            if (metric.label === "TENANT QUALITY INDEX") {
                return {
                    ...metric,
                    value: tenantQualityIndex ?? "-",
                };
            }

            if (metric.label === "AFFORDABILITY INDEX") {
                return {
                    ...metric,
                    value: affordabilityIndex !== null ? `${Math.round(affordabilityIndex)}%` : "-",
                };
            }

            return metric;
        });
    }, [dashboardPayload?.facts, dashboardPayload?.property, financialMetrics]);

    const dynamicComparableListings = useMemo(() => {
        const toNumber = (value: unknown): number | null => {
            if (typeof value === "number" && Number.isFinite(value)) {
                return value;
            }
            if (typeof value === "string" && value.trim()) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : null;
            }
            return null;
        };

        const parseIsoDate = (value: unknown): Date | null => {
            if (typeof value !== "string" || !value.trim()) {
                return null;
            }
            const date = new Date(value);
            return Number.isNaN(date.getTime()) ? null : date;
        };

        const rawComparables = Array.isArray(dashboardPayload?.comparables)
            ? dashboardPayload.comparables
            : [];
        const now = new Date();

        const mapped = rawComparables.slice(0, 5).map((row, index) => {
            const fullAddress =
                typeof row?.address === "string" && row.address.trim()
                    ? row.address.trim()
                    : "-";
            const firstCommaIndex = fullAddress.indexOf(",");
            const addressLineOne = firstCommaIndex === -1 ? fullAddress : fullAddress.slice(0, firstCommaIndex).trim();
            const addressLineTwo = firstCommaIndex === -1 ? "-" : fullAddress.slice(firstCommaIndex + 1).trim();

            const rentalPrice = toNumber(row?.rental_price);
            const squareFootage = toNumber(row?.square_footage);
            const matchPercentRaw = toNumber(row?.correlation_score);
            const matchPercent = Math.max(0, Math.min(100, Math.round(matchPercentRaw ?? 0)));
            const bedrooms = toNumber(row?.bedrooms);
            const bathrooms = toNumber(row?.bathrooms);
            const listedDateObj = parseIsoDate(row?.listed_date);
            const listedDate = listedDateObj
                ? listedDateObj.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                })
                : "-";
            const daysAgo = listedDateObj
                ? Math.max(0, Math.floor((now.getTime() - listedDateObj.getTime()) / (1000 * 60 * 60 * 24)))
                : 0;

            const rawStatus = typeof row?.status === "string" ? row.status.trim().toLowerCase() : "";
            const status = rawStatus === "active" || rawStatus === "for_rent" || rawStatus === "for rent"
                ? "Active"
                : "Inactive";

            const rentPerSqft = rentalPrice !== null && squareFootage && squareFootage > 0
                ? `$${(rentalPrice / squareFootage).toFixed(2)} / sq ft`
                : "-";

            const idSource = typeof row?.id === "string" && row.id.trim()
                ? row.id.trim()
                : `${fullAddress}-${String(row?.listed_date ?? "")}-${index}`;

            return {
                id: idSource,
                address: addressLineOne,
                neighborhood: addressLineTwo || "-",
                listedRent: rentalPrice !== null ? `$${Math.round(rentalPrice).toLocaleString()}` : "-",
                rentPerSqft,
                matchPercent,
                specs: `${bedrooms ?? "-"} bd / ${bathrooms ?? "-"} ba`,
                sqft: squareFootage !== null ? `${Math.round(squareFootage).toLocaleString()} sq ft` : "-",
                listedDate,
                daysAgo,
                status: status as "Active" | "Inactive",
            };
        });

        return mapped.length > 0 ? mapped : comparableListings;
    }, [dashboardPayload, comparableListings]);

    const isLoading = status === "loading";
    const showDashboard = status === "ready" && dashboardPayload && marketPriceTrend && marketRevenueExpenses;

    return (
        <div className={styles.pageRoot}>
            <DashboardHeader showPropertySearch />

            <main className={styles.main}>
                {isLoading ? <DashboardSkeleton /> : null}

                {status === "error" ? (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
                        {dashboardError ?? "Failed to load dashboard data."}
                    </div>
                ) : null}

                {status === "idle" ? (
                    <div className="rounded-xl border border-[#E5E7EB] bg-white px-5 py-4 text-sm text-[#475467] shadow-sm">
                        Select a property to view its dashboard.
                    </div>
                ) : null}

                {showDashboard ? (
                    <div className={styles.layoutGrid}>
                        <div className={styles.leftColumn}>
                            <section className={styles.sectionCard}>
                                <div className={styles.sectionHeader}>
                                    <span className={styles.sectionLabel}>Property Verdict</span>
                                </div>
                                <PropertyVerdict insight={insight} />
                            </section>

                            <FinancialMetrics metrics={dynamicFinancialMetrics} />
                            <MarketTrends priceTrend={marketPriceTrend} revenueExpenses={marketRevenueExpenses} />
                            <ComparableListings listings={dynamicComparableListings} />
                        </div>

                        <aside className={styles.rightColumn}>
                            <section className={styles.sectionCard}>
                                <div className={styles.sectionHeader}>
                                    <span className={styles.sectionLabel}>Property Context</span>
                                </div>
                                <PropertyContext property={contextProperty} />
                            </section>

                            <LocationIntelligence
                                scores={dynamicLocationScores}
                                mapAddress={mapData.address}
                                latitude={mapData.latitude}
                                longitude={mapData.longitude}
                            />
                        </aside>
                    </div>
                ) : null}
            </main>

            <div className={styles.chatDock}>
                {isChatOpen && (
                    <div className={styles.chatPanel}>
                        <div className={styles.chatHeader}>
                            <div className={styles.tabRow}>
                                <button
                                    type="button"
                                    onClick={() => setActiveTab("ai")}
                                    className={`${styles.tabButton} ${activeTab === "ai" ? styles.tabButtonActive : ""}`}
                                >
                                    <Image
                                        src={aiCustomizationIcon}
                                        alt="AI"
                                        width={14}
                                        height={14}
                                        className={activeTab === "ai" ? "" : styles.tabIconMuted}
                                    />
                                    AI Customization
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setActiveTab("feedback")}
                                    className={`${styles.tabButton} ${activeTab === "feedback" ? styles.tabButtonActive : ""}`}
                                >
                                    <Image
                                        src={feedbackIcon}
                                        alt="Feedback"
                                        width={14}
                                        height={14}
                                        className={activeTab === "feedback" ? styles.tabIconActiveFeedback : ""}
                                    />
                                    Feedback
                                </button>
                            </div>
                            <button
                                type="button"
                                onClick={() => setIsChatOpen(false)}
                                className={styles.closeButton}
                            >
                                <Image src={closeIcon} alt="Close" width={10} height={10} />
                            </button>
                        </div>

                        <div className={styles.chatBody}>
                            <p className={styles.chatText}>
                                {activeTab === "ai"
                                    ? "Tell the AI what you value most. We'll remember your preferences for future analyses."
                                    : "Found a bug or have a suggestion? Let us know how we can improve Housmart."}
                            </p>

                            <textarea
                                className={styles.chatTextarea}
                                placeholder={
                                    activeTab === "ai"
                                        ? "E.g., 'I prefer walkable neighborhoods', 'Avoid heavy traffic...'"
                                        : "Describe the issue or suggestion..."
                                }
                            />

                            <div className={styles.chatActions}>
                                <button
                                    type="button"
                                    onClick={() => setIsChatOpen(false)}
                                    className={styles.cancelButton}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsChatOpen(false)}
                                    className={styles.primaryButton}
                                >
                                    {activeTab === "ai" ? "Save" : "Send"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <button
                    type="button"
                    onClick={() => setIsChatOpen(!isChatOpen)}
                    className={styles.chatFab}
                >
                    {isChatOpen ? <X size={24} /> : <MessageSquare size={24} />}
                </button>
            </div>
        </div>
    );
}
