"use client";
import React from "react";
import Image from "next/image";
import { ArrowRight, Upload, Download, TrendingUp, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { PropertyInsight } from "@/lib/mockData";

interface PropertyVerdictProps {
    insight: PropertyInsight & { undervaluedBy?: string };
}

export const PropertyVerdict: React.FC<PropertyVerdictProps> = ({ insight }) => {
    return (
        <div className="flex flex-col gap-4 px-5 pt-4 pb-5">
            {/* Badge row + action buttons */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                    <Badge variant="strong-buy">{insight.verdict}</Badge>
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-[#027A48]">
                        <Image
                            src="/assets/dashboard/icons/ai-star.svg"
                            alt="AI"
                            width={10}
                            height={10}
                        />
                        AI CONFIDENCE: {insight.aiConfidence}%
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    <button className="flex items-center gap-1.5 bg-[#101828] text-white text-xs font-semibold px-3.5 py-2 rounded-lg hover:bg-[#1D2939] transition">
                        View Listing
                        <ArrowRight size={11} />
                    </button>
                    <button className="flex items-center gap-1.5 border border-[#D0D5DD] text-[#344054] text-xs font-medium px-3 py-2 rounded-lg hover:bg-[#F9FAFB] transition">
                        <Upload size={11} /> Share
                    </button>
                    <button className="flex items-center gap-1.5 border border-[#D0D5DD] text-[#344054] text-xs font-medium px-3 py-2 rounded-lg hover:bg-[#F9FAFB] transition">
                        <Download size={11} /> Report
                    </button>
                </div>
            </div>

            {/* Headline + summary */}
            <div>
                <h2 className="text-[15px] font-bold text-[#101828] leading-snug">
                    {insight.headline}
                </h2>
                <p className="text-xs text-[#6B7280] mt-1.5 leading-relaxed max-w-[580px]">
                    Our model identifies this property as{" "}
                    <span className="text-[#027A48] font-semibold underline">
                        undervalued by {insight.undervaluedBy ?? "4.2"}%
                    </span>{" "}
                    relative to the neighborhood average. Key value drivers include the
                    2027 light rail station and RSL zoning changes.
                </p>
            </div>

            {/* Two-column: Upside Drivers | Risk Factors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Upside Drivers */}
                <div>
                    <div className="flex items-center gap-1.5 mb-3">
                        <TrendingUp size={11} className="text-[#027A48]" />
                        <span className="text-[10px] font-bold text-[#027A48] tracking-[0.1em] uppercase">
                            Upside Drivers
                        </span>
                    </div>
                    <div className="flex flex-col gap-3">
                        {insight.upsideDrivers.map((item) => (
                            <div key={item.id} className="flex gap-2.5 items-start">
                                <div className="mt-0.5 w-[26px] h-[26px] flex items-center justify-center rounded-full bg-[#ECFDF3] shrink-0">
                                    <Image src={item.icon} alt={item.title} width={13} height={13} />
                                </div>
                                <div>
                                    <p className="text-[11px] font-semibold text-[#101828] leading-tight">{item.title}</p>
                                    <p className="text-[11px] text-[#6B7280] leading-relaxed mt-0.5">
                                        {item.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Factors */}
                <div>
                    <div className="flex items-center gap-1.5 mb-3">
                        <AlertTriangle size={11} className="text-[#B42318]" />
                        <span className="text-[10px] font-bold text-[#B42318] tracking-[0.1em] uppercase">
                            Risk Factors
                        </span>
                    </div>
                    <div className="flex flex-col gap-3">
                        {insight.riskFactors.map((item, idx) => (
                            <div key={item.id} className="flex gap-2.5 items-start">
                                <div className="mt-0.5 w-[26px] h-[26px] flex items-center justify-center rounded-full bg-[#FFF1F0] shrink-0">
                                    <Image src={item.icon} alt={item.title} width={13} height={13} />
                                </div>
                                <div>
                                    <p className="text-[11px] font-semibold text-[#101828] leading-tight">{item.title}</p>
                                    <p className="text-[11px] text-[#6B7280] leading-relaxed mt-0.5">
                                        {item.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-3 border-t border-[#F3F4F6]">
                <div className="flex items-center gap-4 text-[11px] text-[#6B7280]">
                    <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#D0D5DD] inline-block" />
                        {insight.dataPoints} Data Points
                    </span>
                    <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#D0D5DD] inline-block" />
                        {insight.comparableSales} Comparable Sales
                    </span>
                </div>
                <span className="text-[11px] text-[#9CA3AF] flex items-center gap-1">
                    <svg className="w-3 h-3 text-[#9CA3AF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" strokeWidth="2" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6l4 2" />
                    </svg>
                    Updated {insight.lastUpdated}
                </span>
            </div>
        </div>
    );
};
