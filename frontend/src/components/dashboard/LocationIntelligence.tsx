"use client";
import React from "react";
import Image, { type StaticImageData } from "next/image";
import { ScoreBar } from "@/components/ui/ScoreBar";

interface LocationIntelligenceProps {
    scores: Array<{
        label: string;
        score: number;
        icon: StaticImageData | string;
        tooltipText?: string;
    }>;
    radius?: string;
}

export const LocationIntelligence: React.FC<LocationIntelligenceProps> = ({
    scores,
    radius = "0.5 mi radius",
}) => {
    return (
        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-visible">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#F3F4F6]">
                <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
                    Location Intelligence
                </span>
                <span className="text-[10px] text-[#9CA3AF]">{radius}</span>
            </div>

            {/* Map placeholder */}
            <div className="relative mx-3 mt-3 mb-3 rounded-xl overflow-hidden h-[200px] bg-[#F3F4F6] border border-[#E5E7EB]">
            </div>

            {/* Score rows — with dividers between each */}
            <div className="px-4 pb-3">
                {scores.map((score, idx) => (
                    <div key={score.label}>
                        <div className="flex items-center justify-between py-3">
                            <div className="flex items-center gap-2.5">
                                <div className="relative group">
                                    <Image
                                        src={score.icon}
                                        alt={score.label}
                                        width={14}
                                        height={14}
                                        className="shrink-0 opacity-70 cursor-help"
                                    />
                                    {score.tooltipText && (
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-[380px] max-w-[calc(100vw-2rem)] hidden group-hover:block whitespace-normal break-words text-left bg-white text-[#101828] font-medium text-[12px] leading-snug p-3 rounded-lg border border-[#E5E7EB] shadow-[0px_4px_16px_rgba(0,0,0,0.08)] z-[60]">
                                            {score.tooltipText}
                                        </div>
                                    )}
                                </div>
                                <span className="text-[12px] font-medium text-[#374151]">{score.label}</span>
                            </div>
                            <ScoreBar score={score.score} />
                        </div>
                        {idx < scores.length - 1 && (
                            <div className="h-px bg-[#F3F4F6]" />
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
