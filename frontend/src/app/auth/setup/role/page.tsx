"use client";

import React, { useEffect } from "react";
import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { UserRole, useSetup } from "@/providers/setup-context";

import { ROLE_OPTIONS } from "../setup-step-data";
import styles from "../setup-step.module.css";

export default function RoleStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (role: UserRole) => {
        updateData({ role });
    };

    const canContinue = isStepValid(1);

    const handleNext = () => {
        if (canContinue) {
            router.push("/auth/setup/experience");
        }
    };

    useEffect(() => {
        router.prefetch("/auth/setup/experience");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={1} title="ROLE" />

            <div className={styles.setupStepContainer}>
                <div className={styles.stepHeader}>
                    <h1 className={styles.stepTitle}>User Profile</h1>
                    <p className={styles.stepDescription}>Select your primary role to calibrate risk models.</p>
                </div>

                <div className={styles.cardsList}>
                    {ROLE_OPTIONS.map((option) => (
                        <SelectableCard
                            key={option.value}
                            title={option.title}
                            description={option.description}
                            icon={option.icon}
                            selectedIcon={option.selectedIcon}
                            selected={data.role === option.value}
                            onClick={() => handleSelect(option.value)}
                        />
                    ))}
                </div>

                <div className={styles.footerRow}>
                    <div />
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
