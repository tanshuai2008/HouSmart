import React from "react";
import {
    LogoIcon,
    FeatureCheckIcon,
    TrendingUpIcon,
    ShieldCheckIcon,
} from "../ui/Icons";

interface AuthLayoutProps {
    children: React.ReactNode;
}

const features = [
    {
        title: "Predictive Market Valuation",
        icon: TrendingUpIcon,
    },
    {
        title: "Risk & Zoning Analysis",
        icon: ShieldCheckIcon,
    },
    {
        title: "Instant ROI Calculation",
        icon: FeatureCheckIcon,
    },
];

export const AuthLayout = ({ children }: AuthLayoutProps) => {
    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#F9FAFB]">
            {/* Left Panel */}
            <div className="relative w-full lg:w-1/2 lg:min-h-screen bg-[#101828] overflow-hidden flex flex-col px-8 py-12 lg:px-12 lg:flex-shrink-0">
                {/* Aura Background Blur */}
                <div className="absolute w-[384px] h-[384px] left-[295px] top-[-80px] bg-[rgba(30,41,57,0.3)] blur-[64px] rounded-full pointer-events-none" />

                {/* Logo and Name */}
                <div className="flex items-center gap-3 z-10 mb-12 lg:mb-[200px]">
                    <div className="w-10 h-10 bg-white rounded-[10px] flex items-center justify-center">
                        <LogoIcon className="w-6 h-6 text-[#101828]" />
                    </div>
                    <span className="font-semibold text-xl leading-[28px] tracking-[-0.45px] text-white/90">
                        Housmart
                    </span>
                </div>

                {/* Hero Content */}
                <div className="z-10 mt-4 lg:mt-0 max-w-[448px]">
                    <h1 className="font-semibold text-[32px] md:text-[36px] leading-[44px] tracking-[-0.75px] text-white mb-6">
                        The intelligent decision engine for real estate.
                    </h1>
                    <p className="font-normal text-[15px] md:text-[16px] leading-[26px] text-[#99A1AF] mb-10 max-w-[442px]">
                        Housmart empowers investors with institutional-grade data, AI-driven
                        valuation models, and comprehensive risk assessments—all in one
                        unified dashboard.
                    </p>

                    {/* Features List */}
                    <div className="flex flex-col gap-5">
                        {features.map((feature, i) => {
                            const Icon = feature.icon;
                            return (
                                <div key={i} className="flex items-center gap-3">
                                    <Icon className="w-5 h-5 text-[#00BC7D]" />
                                    <span className="font-normal text-[15px] leading-[20px] text-[#D1D5DC]">
                                        {feature.title}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Investors Section */}
                <div className="z-10 mt-16 lg:mt-auto pt-8 border-t border-white/10 flex items-center gap-3">
                    <div className="flex -space-x-2">
                        {[1, 2, 3].map((i) => (
                            <div
                                key={i}
                                className="w-8 h-8 rounded-full border-[1.7px] border-[#101828] bg-gray-600 flex items-center justify-center overflow-hidden"
                            >
                                {/* Fallback image style since actual user JPGs not provided */}
                                <svg
                                    className="w-full h-full text-gray-300"
                                    fill="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z" />
                                </svg>
                            </div>
                        ))}
                    </div>
                    <span className="font-medium text-[12px] leading-[16px] text-white">
                        2,000+ investors
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
