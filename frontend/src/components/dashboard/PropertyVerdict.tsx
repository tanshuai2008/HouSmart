"use client";

import React from "react";
import Image, { type StaticImageData } from "next/image";
import {
    AlertTriangle,
    ArrowRight,
    Bookmark,
    Clock3,
    Download,
    Share2,
    TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import aiConfidenceScoreIcon from "@/assets/dashboard/icons/AIConfidenceScoreIcon.svg";

import styles from "./property-verdict.module.css";

interface PropertyVerdictProps {
    insight: {
        verdict: "Strong Buy" | "Buy" | "Hold" | "Sell";
        aiConfidence: number;
        headline: string;
        summary: string;
        undervaluedBy?: string;
        dataPoints: number;
        comparableSales: number;
        lastUpdated: string;
        upsideDrivers: Array<{
            id: string;
            icon: StaticImageData | string;
            title: string;
            description: string;
        }>;
        riskFactors: Array<{
            id: string;
            icon: StaticImageData | string;
            title: string;
            description: string;
        }>;
    };
}

export const PropertyVerdict: React.FC<PropertyVerdictProps> = ({ insight }) => {
    return (
        <div className={styles.root}>
            <div className={styles.topRow}>
                <div className={styles.verdictMeta}>
                    <Badge variant="strong-buy">{insight.verdict}</Badge>
                    <span className={styles.confidence}>
                        <Image src={aiConfidenceScoreIcon} alt="" width={12} height={12} className={styles.confidenceIcon} aria-hidden="true" />
                        AI CONFIDENCE: {insight.aiConfidence}%
                    </span>
                </div>

                <div className={styles.actionRow}>
                    <button type="button" className={styles.actionPrimary}>
                        View Listing
                        <ArrowRight size={13} />
                    </button>
                    <button type="button" className={styles.actionGhostBlue}>
                        <Bookmark size={13} /> Save Property
                    </button>
                    <button type="button" className={styles.actionGhost}>
                        <Share2 size={13} /> Share
                    </button>
                    <button type="button" className={styles.actionOutline}>
                        <Download size={13} /> Report
                    </button>
                </div>
            </div>

            <div className={styles.headlineWrap}>
                <h2 className={styles.headline}>{insight.headline}</h2>
                <p className={styles.summary}>
                    Our model identifies this property as{" "}
                    <span className={styles.summaryHighlight}>
                        undervalued by {insight.undervaluedBy ?? "4.2"}%
                    </span>{" "}
                    relative to the neighborhood average. Key value drivers include the
                    2027 light rail station and RSL zoning changes.
                </p>
            </div>

            <div className={styles.columns}>
                <div>
                    <div className={styles.columnHeader}>
                        <TrendingUp size={11} className={styles.columnIconPositive} />
                        <span className={styles.columnLabelPositive}>Upside Drivers</span>
                    </div>
                    <div className={styles.itemList}>
                        {insight.upsideDrivers.map((item) => (
                            <div key={item.id} className={styles.itemRow}>
                                <div className={styles.itemIconPositive}>
                                    <Image src={item.icon} alt={item.title} width={13} height={13} />
                                </div>
                                <div>
                                    <p className={styles.itemTitle}>{item.title}</p>
                                    <p className={styles.itemDescription}>{item.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div>
                    <div className={styles.columnHeader}>
                        <AlertTriangle size={11} className={styles.columnIconNegative} />
                        <span className={styles.columnLabelNegative}>Risk Factors</span>
                    </div>
                    <div className={styles.itemList}>
                        {insight.riskFactors.map((item) => (
                            <div key={item.id} className={styles.itemRow}>
                                <div className={styles.itemIconNegative}>
                                    <Image src={item.icon} alt={item.title} width={13} height={13} />
                                </div>
                                <div>
                                    <p className={styles.itemTitle}>{item.title}</p>
                                    <p className={styles.itemDescription}>{item.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className={styles.footer}>
                <div className={styles.footerStats}>
                    <span className={styles.footerStat}>
                        <span className={styles.footerDot} />
                        {insight.dataPoints} Data Points
                    </span>
                    <span className={styles.footerStat}>
                        <span className={styles.footerDot} />
                        {insight.comparableSales} Comparable Sales
                    </span>
                </div>
                <span className={styles.footerUpdated}>
                    <Clock3 size={14} className={styles.footerClock} />
                    Updated {insight.lastUpdated}
                </span>
            </div>
        </div>
    );
};
