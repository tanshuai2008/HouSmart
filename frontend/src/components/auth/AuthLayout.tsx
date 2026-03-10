import React from "react";
import Image from "next/image";

import logoMark from "@/assets/auth/logo-mark.svg";
import logoWordmark from "@/assets/auth/logo-wordmark.svg";
import valuationFeatureIcon from "@/assets/icons/trending-up.svg";
import riskFeatureIcon from "@/assets/icons/shield-check.svg";
import roiFeatureIcon from "@/assets/auth/feature-check-roi.svg";
import investorAvatar from "@/assets/auth/investor-avatar-placeholder.svg";

import styles from "./auth-layout.module.css";

interface AuthLayoutProps {
    children: React.ReactNode;
}

const authFeatures = [
    { title: "Predictive Market Valuation", icon: valuationFeatureIcon },
    { title: "Risk & Zoning Analysis", icon: riskFeatureIcon },
    { title: "Instant ROI Calculation", icon: roiFeatureIcon },
];

export const AuthLayout = ({ children }: AuthLayoutProps) => {
    return (
        <div className={styles.authShell}>
            <aside className={styles.leftPanel}>
                <div className={styles.panelAura} />

                <div className={styles.brandRow}>
                    <Image src={logoMark} alt="Housmart logo" width={32} height={32} />
                    <Image src={logoWordmark} alt="Housmart" width={83} height={28} />
                </div>

                <section className={styles.heroSection}>
                    <h1 className={styles.heroTitle}>The intelligent decision engine for real estate.</h1>
                    <p className={styles.heroDescription}>
                        Housmart empowers investors with institutional-grade data, AI-driven valuation
                        models, and comprehensive risk assessments, all in one unified dashboard.
                    </p>

                    <div className={styles.featureList}>
                        {authFeatures.map((feature) => (
                            <div key={feature.title} className={styles.featureItem}>
                                <Image src={feature.icon} alt="" width={18} height={18} aria-hidden="true" />
                                <span className={styles.featureText}>{feature.title}</span>
                            </div>
                        ))}
                    </div>
                </section>

                <div className={styles.investorsRow}>
                    <div className={styles.avatarGroup}>
                        <Image src={investorAvatar} alt="Investor" width={32} height={32} className={styles.avatar} />
                        <Image src={investorAvatar} alt="Investor" width={32} height={32} className={styles.avatar} />
                        <Image src={investorAvatar} alt="Investor" width={32} height={32} className={styles.avatar} />
                    </div>
                    <span className={styles.investorText}>
                        <span className={styles.investorCount}>2,000+</span>{" "}
                        <span className={styles.investorLabel}>investors</span>
                    </span>
                </div>
            </aside>

            <main className={styles.rightPanel}>
                <div className={styles.formSlot}>{children}</div>
            </main>
        </div>
    );
};
