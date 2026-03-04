"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSetup, ExperienceLevel } from "@/context/SetupContext";
import { StepIndicator } from "@/components/layout/StepIndicator";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { Button } from "@/components/ui/Button";
import { GraduationCapIcon, ExperiencedInvestorIcon } from "@/components/ui/Icons";

export default function ExperienceStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (experience: ExperienceLevel) => {
        updateData({ experience });
    };

    const handleNext = () => {
        if (isStepValid(2)) {
            router.push("/auth/setup/goal");
        }
    };

    const handleBack = () => {
        router.back();
    };

    useEffect(() => {
        router.prefetch("/auth/setup/goal");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={2} title="EXPERIENCE" />

            <div className="p-8 flex flex-col items-center">
                <div className="w-full mb-8">
                    <h1 className="font-semibold text-[28px] leading-[36px] text-[#111827] mb-3">
                        Invest Experience Level
                    </h1>
                    <p className="font-normal text-[16px] leading-[26px] text-[#6B7280]">
                        We'll adjust the complexity of insights based on your experience.
                    </p>
                </div>

                <div className="w-full flex flex-col gap-4 mb-10">
                    <SelectableCard
                        title="Newbie (1st Deal)"
                        description="AI explains basic concepts. Focus on education and clear risk indicators."
                        icon={GraduationCapIcon}
                        selected={data.experience === "Newbie (1st Deal)"}
                        onClick={() => handleSelect("Newbie (1st Deal)")}
                    />
                    <SelectableCard
                        title="Experienced Investor"
                        description="AI generates deep financial KPIs, advanced sensitivity analysis, and tax implications."
                        icon={ExperiencedInvestorIcon}
                        selected={data.experience === "Experienced Investor"}
                        onClick={() => handleSelect("Experienced Investor")}
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
                        disabled={!isStepValid(2)}
                        className={`w-auto px-6 h-12 text-[15px] rounded-[12px] bg-[#111827] text-white hover:bg-[#1f2937] ${!isStepValid(2) ? "opacity-50 cursor-not-allowed" : ""}`}
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
