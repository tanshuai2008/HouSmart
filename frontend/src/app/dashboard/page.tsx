"use client";

import React, { useState } from "react";
import Image from "next/image";
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

import { dashboardData } from "./dashboard-data";
import styles from "./dashboard-page.module.css";

export default function DashboardPage() {
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<"ai" | "feedback">("ai");

    const {
        comparableListings,
        financialMetrics,
        insight,
        locationScores,
        priceTrend,
        property,
        revenueExpenses,
    } = dashboardData;

    return (
        <div className={styles.pageRoot}>
            <DashboardHeader />

            <main className={styles.main}>
                <div className={styles.layoutGrid}>
                    <div className={styles.leftColumn}>
                        <section className={styles.sectionCard}>
                            <div className={styles.sectionHeader}>
                                <span className={styles.sectionLabel}>Property Verdict</span>
                            </div>
                            <PropertyVerdict insight={insight} />
                        </section>

                        <FinancialMetrics metrics={financialMetrics} />
                        <MarketTrends priceTrend={priceTrend} revenueExpenses={revenueExpenses} />
                        <ComparableListings listings={comparableListings} />
                    </div>

                    <aside className={styles.rightColumn}>
                        <section className={styles.sectionCard}>
                            <div className={styles.sectionHeader}>
                                <span className={styles.sectionLabel}>Property Context</span>
                            </div>
                            <PropertyContext property={property} />
                        </section>

                        <LocationIntelligence scores={locationScores} />
                    </aside>
                </div>
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
