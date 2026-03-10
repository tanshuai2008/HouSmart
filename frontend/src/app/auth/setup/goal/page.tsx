"use client";

import React, { useEffect } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { InvestmentGoal, useSetup } from "@/providers/setup-context";

import { GOAL_OPTIONS } from "../setup-step-data";
import styles from "../setup-step.module.css";

export default function GoalStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (goal: InvestmentGoal) => {
        updateData({ goal });
    };

    const canContinue = isStepValid(3);

    const handleNext = () => {
        if (canContinue) {
            router.push("/auth/setup/priorities");
        }
    };

    useEffect(() => {
        router.prefetch("/auth/setup/priorities");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={3} title="STRATEGY" />

            <div className={styles.setupStepContainer}>
                <div className={styles.stepHeader}>
                    <h1 className={styles.stepTitle}>Investment Goal</h1>
                    <p className={styles.stepDescription}>We&apos;ll prioritize metrics that align with this strategy.</p>
                </div>

                <div className={styles.cardsList}>
                    {GOAL_OPTIONS.map((option) => (
                        <SelectableCard
                            key={option.value}
                            title={option.title}
                            description={option.description}
                            icon={option.icon}
                            selectedIcon={option.selectedIcon}
                            selected={data.goal === option.value}
                            onClick={() => handleSelect(option.value)}
                        />
                    ))}
                </div>

                <div className={styles.footerRow}>
                    <button type="button" onClick={() => router.back()} className={styles.backButton}>
                        <ArrowLeft size={16} className={styles.backIcon} />
                        BACK
                    </button>

                    <Button
                        variant="default"
                        onClick={handleNext}
                        disabled={!canContinue}
                        className={`${styles.nextButton} ${!canContinue ? styles.nextButtonDisabled : ""}`}
                    >
                        Next Step
                        <ArrowRight size={20} className={styles.nextIcon} />
                    </Button>
                </div>
            </div>
        </>
    );
}
