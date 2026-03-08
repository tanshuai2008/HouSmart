"use client";
import React from "react";
import Image from "next/image";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { LocationScore } from "@/lib/mockData";

interface LocationIntelligenceProps {
    scores: LocationScore[];
    radius?: string;
}

export const LocationIntelligence: React.FC<LocationIntelligenceProps> = ({
    scores,
    radius = "0.5 mi radius",
}) => {
    return (
        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden">
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
                                <Image src={score.icon as any} alt={score.label} width={14} height={14} className="shrink-0 opacity-70" />
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
