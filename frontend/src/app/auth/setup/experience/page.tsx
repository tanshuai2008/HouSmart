"use client";

import React, { useEffect } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { ExperienceLevel, useSetup } from "@/providers/setup-context";

import { EXPERIENCE_OPTIONS } from "../setup-step-data";
import styles from "../setup-step.module.css";

export default function ExperienceStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (experience: ExperienceLevel) => {
        updateData({ experience });
    };

    const canContinue = isStepValid(2);

    const handleNext = () => {
        if (canContinue) {
            router.push("/auth/setup/goal");
        }
    };

    useEffect(() => {
        router.prefetch("/auth/setup/goal");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={2} title="EXPERIENCE" />

            <div className={styles.setupStepContainer}>
                <div className={styles.stepHeader}>
                    <h1 className={styles.stepTitle}>Invest Experience Level</h1>
                    <p className={styles.stepDescription}>
                        We&apos;ll adjust the complexity of insights based on your experience.
                    </p>
                </div>

                <div className={styles.cardsList}>
                    {EXPERIENCE_OPTIONS.map((option) => (
                        <SelectableCard
                            key={option.value}
                            title={option.title}
                            description={option.description}
                            icon={option.icon}
                            selectedIcon={option.selectedIcon}
                            selected={data.experience === option.value}
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
