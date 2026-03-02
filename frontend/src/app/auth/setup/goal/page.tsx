"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSetup, InvestmentGoal } from "@/context/SetupContext";
import { StepIndicator } from "@/components/layout/StepIndicator";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { Button } from "@/components/ui/Button";
import { CashFlowIcon, LongTermAppreciationIcon, BalancedMixIcon } from "@/components/ui/Icons";

export default function GoalStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (goal: InvestmentGoal) => {
        updateData({ goal });
    };

    const handleNext = () => {
        if (isStepValid(3)) {
            router.push("/auth/setup/priorities");
        }
    };

    const handleBack = () => {
        router.back();
    };

    useEffect(() => {
        router.prefetch("/auth/setup/priorities");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={3} title="STRATEGY" />

            <div className="p-8 flex flex-col items-center">
                <div className="w-full mb-8">
                    <h1 className="font-semibold text-[28px] leading-[36px] text-[#111827] mb-3">
                        Investment Goal
                    </h1>
                    <p className="font-normal text-[16px] leading-[26px] text-[#6B7280]">
                        We'll prioritize metrics that align with this strategy.
                    </p>
                </div>

                <div className="w-full flex flex-col gap-4 mb-10">
                    <SelectableCard
                        title="Cash Flow"
                        description="Prioritize immediate monthly income. Lower risk tolerance."
                        icon={CashFlowIcon}
                        selected={data.goal === "Cash Flow"}
                        onClick={() => handleSelect("Cash Flow")}
                    />
                    <SelectableCard
                        title="Long-term Appreciation"
                        description="Focus on growth markets with transit/zoning upside."
                        icon={LongTermAppreciationIcon}
                        selected={data.goal === "Long-term Appreciation"}
                        onClick={() => handleSelect("Long-term Appreciation")}
                    />
                    <SelectableCard
                        title="Balanced Mix"
                        description="Blend of steady income and moderate growth potential."
                        icon={BalancedMixIcon}
                        selected={data.goal === "Balanced Mix"}
                        onClick={() => handleSelect("Balanced Mix")}
                    />
                </div>

                <div className="w-full flex items-center justify-between pt-4 border-t border-[#E5E7EB]">
                    <button
                        onClick={handleBack}
                        className="font-semibold text-[13px] leading-[18px] text-[#6B7280] flex items-center hover:text-[#374151] transition-colors"
                    >
                        <svg className="w-4 h-4 mr-2" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12.6665 8H3.33317M3.33317 8L7.33317 12M3.33317 8L7.33317 4" stroke="currentColor" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        BACK
                    </button>

                    <Button
                        variant="default"
                        onClick={handleNext}
                        disabled={!isStepValid(3)}
                        className={`w-auto px-6 h-12 text-[15px] rounded-[12px] bg-[#111827] text-white hover:bg-[#1f2937] ${!isStepValid(3) ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                        Next Step
                        <svg className="w-5 h-5 ml-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M12 5L19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </Button>
                </div>
            </div>
        </>
    );
}
