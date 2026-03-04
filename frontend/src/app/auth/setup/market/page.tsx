"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSetup } from "@/context/SetupContext";
import { StepIndicator } from "@/components/layout/StepIndicator";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export default function MarketStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();
    const [localMarket, setLocalMarket] = useState(data.market || "");

    const handleNext = () => {
        // Save to global context
        updateData({ market: localMarket });

        // Simulating the final submission
        setTimeout(() => {
            alert(JSON.stringify({ ...data, market: localMarket }, null, 2));
            // router.push("/dashboard"); 
        }, 300);
    };

    return (
        <>
            <StepIndicator currentStep={5} title="REGION" />

            <div className="p-8 flex flex-col items-center">
                <div className="w-full mb-8">
                    <h1 className="font-semibold text-[28px] leading-[36px] text-[#111827] mb-3">
                        Target Market
                    </h1>
                    <p className="font-normal text-[16px] leading-[26px] text-[#6B7280]">
                        Enter your primary market of interest.
                    </p>
                </div>

                <div className="w-full mb-10 p-5 rounded-[12px] bg-[#F9FAFB] border border-[#E5E7EB]">
                    <Input
                        type="text"
                        placeholder="Seattle, WA"
                        value={localMarket}
                        onChange={(e) => setLocalMarket(e.target.value)}
                        icon={
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                <circle cx="12" cy="10" r="3"></circle>
                            </svg>
                        }
                        className="bg-white"
                    />

                    <div className="mt-6">
                        <span className="block font-semibold text-[11px] leading-[14px] tracking-[1px] text-[#9CA3AF] uppercase mb-3">
                            POPULAR MARKETS
                        </span>
                        <div className="flex flex-wrap gap-2">
                            {["Seattle", "Austin", "Nashville", "Denver"].map((city) => (
                                <button
                                    key={city}
                                    onClick={() => setLocalMarket(city)}
                                    className={`px-4 py-2 rounded-full border text-[13px] font-medium transition-colors ${localMarket === city
                                        ? "bg-[#111827] border-[#111827] text-white"
                                        : "bg-white border-[#E5E7EB] text-[#6B7280] hover:border-[#D1D5DC] hover:text-[#374151]"
                                        }`}
                                >
                                    {city}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="w-full flex items-center justify-between pt-4 border-t border-[#E5E7EB]">
                    <button
                        onClick={() => router.back()}
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
                        disabled={localMarket.trim().length === 0}
                        className={`w-auto px-6 h-12 text-[15px] font-medium rounded-[12px] bg-[#111827] text-white hover:bg-[#1f2937] ${localMarket.trim().length === 0 ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                        Complete Setup
                    </Button>
                </div>
            </div>
        </>
    );
}
