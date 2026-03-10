import React from "react";

interface StepIndicatorProps {
    currentStep: number;
    totalSteps?: number;
    title: string;
}

export const StepIndicator = ({ currentStep, totalSteps = 4, title }: StepIndicatorProps) => {
    return (
        <div className="w-full flex items-center justify-between border-b border-[#E5E7EB] px-8 py-5 mt-2">
            <span className="font-semibold text-[13px] leading-[18px] tracking-[1px] text-[#9CA3AF] uppercase">
                STEP {currentStep} OF {totalSteps}
            </span>

            <div className="flex items-center gap-3">
                <span className="font-semibold text-[13px] leading-[18px] tracking-[1px] text-[#9CA3AF] uppercase">
                    {title}
                </span>
                <progress
                    className="step-indicator-progress w-[60px]"
                    value={currentStep}
                    max={totalSteps}
                    aria-label="Onboarding progress"
                />
            </div>
        </div>
    );
};
