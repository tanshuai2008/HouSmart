import React from "react";
import Image from "next/image";

import logoContainer from "@/assets/auth/login/logo-container.svg";
import housmartText from "@/assets/auth/login/housmart-text.svg";
import checkIcon1 from "@/assets/auth/login/check-icon-1.svg";
import checkIcon2 from "@/assets/auth/login/check-icon-2.svg";
import checkIcon3 from "@/assets/auth/login/check-icon-3.svg";
import userPlaceholder from "@/assets/auth/login/user-placeholder.svg";

interface AuthLayoutProps {
    children: React.ReactNode;
}

const features = [
    {
        title: "Predictive Market Valuation",
        icon: checkIcon1,
    },
    {
        title: "Risk & Zoning Analysis",
        icon: checkIcon2,
    },
    {
        title: "Instant ROI Calculation",
        icon: checkIcon3,
    },
];

export const AuthLayout = ({ children }: AuthLayoutProps) => {
    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#FFFFFF]">
            {/* Left Panel */}
            <div className="relative w-full lg:w-1/2 lg:min-h-screen bg-[#101828] overflow-hidden flex flex-col px-8 py-12 lg:px-16 lg:py-14 lg:flex-shrink-0">
                {/* Aura Background Blur */}
                <div className="absolute w-[384px] h-[384px] left-[295px] top-[-80px] bg-[rgba(30,41,57,0.2)] blur-[64px] rounded-full pointer-events-none" />

                {/* Logo and Name */}
                <div className="flex items-center gap-2 z-10 mb-12 lg:mb-[180px]">
                    <Image src={logoContainer} alt="Logo" width={32} height={32} />
                    <Image src={housmartText} alt="Housmart" width={83} height={28} />
                </div>

                {/* Hero Content */}
                <div className="z-10 mt-4 lg:mt-0 max-w-[460px]">
                    <h1 className="font-semibold text-[36px] leading-[44px] tracking-[-0.02em] text-[#F9FAFB] mb-6">
                        The intelligent decision<br />engine for real estate.
                    </h1>
                    <p className="font-normal text-[15px] leading-[24px] text-[#A1A1AA] mb-12 max-w-[442px]">
                        Housmart empowers investors with institutional-grade data, AI-
                        driven valuation models, and comprehensive risk assessments—all
                        in one unified dashboard.
                    </p>

                    {/* Features List */}
                    <div className="flex flex-col gap-5">
                        {features.map((feature, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <Image src={feature.icon} alt={feature.title} width={18} height={18} />
                                <span className="font-medium text-[14px] leading-[20px] text-[#D4D4D8]">
                                    {feature.title}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Investors Section */}
                <div className="z-10 mt-16 lg:mt-auto pt-8 border-t border-[#1E293B] flex items-center gap-3">
                    <div className="flex -space-x-2">
                        <Image src={userPlaceholder} alt="Investor 1" width={32} height={32} className="w-8 h-8 rounded-full border-2 border-[#101828]" />
                        <Image src={userPlaceholder} alt="Investor 2" width={32} height={32} className="w-8 h-8 rounded-full border-2 border-[#101828]" />
                        <Image src={userPlaceholder} alt="Investor 3" width={32} height={32} className="w-8 h-8 rounded-full border-2 border-[#101828]" />
                    </div>
                    <span className="text-[14px] leading-[18px]">
                        <span className="font-semibold text-white">2,000+</span>{" "}
                        <span className="font-medium text-[#A1A1AA]">investors</span>
                    </span>
                </div>
            </div>

            {/* Right Panel (Form Container) */}
            <div className="flex-1 lg:w-1/2 flex flex-col items-center justify-center min-h-[500px] lg:min-h-screen relative p-6 w-full">
                <div className="w-full max-w-[400px]">
                    {children}
                </div>
            </div>
        </div>
    );
};
