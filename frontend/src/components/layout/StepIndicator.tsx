import React from "react";

interface StepIndicatorProps {
    currentStep: number;
    totalSteps?: number;
    title: string;
}

export const StepIndicator = ({ currentStep, totalSteps = 5, title }: StepIndicatorProps) => {
    // Calculate progress percentage
    const progress = (currentStep / totalSteps) * 100;

    return (
        <div className="w-full flex items-center justify-between border-b border-[#E5E7EB] px-8 py-5 mt-2">
            <span className="font-semibold text-[13px] leading-[18px] tracking-[1px] text-[#9CA3AF] uppercase">
                STEP {currentStep} OF {totalSteps}
            </span>

            <div className="flex items-center gap-3">
                <span className="font-semibold text-[13px] leading-[18px] tracking-[1px] text-[#9CA3AF] uppercase">
                    {title}
                </span>
                {/* Progress Bar Track */}
                <div className="w-[60px] h-[3px] bg-[#E5E7EB] rounded-full overflow-hidden">
                    {/* Active Progress */}
                    <div
                        className="h-full bg-[#00BC7D] rounded-full transition-all duration-300 ease-in-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>
        </div>
    );
};
