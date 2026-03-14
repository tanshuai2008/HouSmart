"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSetup, UserRole } from "@/context/SetupContext";
import { StepIndicator } from "@/components/layout/StepIndicator";
import { SelectableCard } from "@/components/ui/SelectableCard";
import { Button } from "@/components/ui/Button";
import { IndividualInvestorIcon, RealEstateAgentIcon, InstitutionalBuyerIcon } from "@/components/ui/Icons";

export default function RoleStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    const handleSelect = (role: UserRole) => {
        updateData({ role });
    };

    const handleNext = () => {
        if (isStepValid(1)) {
            router.push("/auth/setup/experience");
        }
    };

    // Optional: Prefetch the next route for speed
    useEffect(() => {
        router.prefetch("/auth/setup/experience");
    }, [router]);

    return (
        <>
            <StepIndicator currentStep={1} title="ROLE" />

            <div className="p-8 flex flex-col items-center">
                <div className="w-full mb-8">
                    <h1 className="font-semibold text-[28px] leading-[36px] text-[#111827] mb-3">
                        User Profile
                    </h1>
                    <p className="font-normal text-[16px] leading-[26px] text-[#6B7280]">
                        Select your primary role to calibrate risk models.
                    </p>
                </div>

                <div className="w-full flex flex-col gap-4 mb-10">
                    <SelectableCard
                        title="Individual Investor"
                        description="Building personal portfolio. Focus on 1-4 unit properties."
                        icon={IndividualInvestorIcon}
                        selected={data.role === "Individual Investor"}
                        onClick={() => handleSelect("Individual Investor")}
                    />
                    <SelectableCard
                        title="Real Estate Agent"
                        description="Sourcing deals for clients. Deep market analysis required."
                        icon={RealEstateAgentIcon}
                        selected={data.role === "Real Estate Agent"}
                        onClick={() => handleSelect("Real Estate Agent")}
                    />
                    <SelectableCard
                        title="Institutional Buyer"
                        description="High volume acquisition. Cap rate and IRR driven."
                        icon={InstitutionalBuyerIcon}
                        selected={data.role === "Institutional Buyer"}
                        onClick={() => handleSelect("Institutional Buyer")}
                    />
                </div>

                <div className="w-full flex justify-end pt-4 border-t border-[#E5E7EB]">
                    <Button
                        variant="default"
                        onClick={handleNext}
                        disabled={!isStepValid(1)}
                        className={`w-auto px-6 h-12 text-[15px] rounded-[12px] bg-[#111827] text-white hover:bg-[#1f2937] ${!isStepValid(1) ? "opacity-50 cursor-not-allowed" : ""}`}
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
