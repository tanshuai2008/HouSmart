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
            <div className="relative mx-3 mt-3 mb-3 rounded-xl overflow-hidden h-[200px]">
                {/* Base: street-map-style background */}
                <div
                    className="w-full h-full"
                    style={{
                        backgroundColor: "#e8e0d8",
                        backgroundImage: `
                            linear-gradient(rgba(200,194,186,0.8) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(200,194,186,0.8) 1px, transparent 1px),
                            linear-gradient(rgba(200,194,186,0.4) 0.5px, transparent 0.5px),
                            linear-gradient(90deg, rgba(200,194,186,0.4) 0.5px, transparent 0.5px)
                        `,
                        backgroundSize: "60px 60px, 60px 60px, 20px 20px, 20px 20px",
                    }}
                />

                {/* Streets */}
                <div className="absolute inset-0 pointer-events-none">
                    {/* Major horizontal road */}
                    <div className="absolute w-full" style={{ top: "42%", height: "8px", backgroundColor: "#fff", opacity: 0.95 }} />
                    {/* Major vertical road */}
                    <div className="absolute h-full" style={{ left: "40%", width: "8px", backgroundColor: "#fff", opacity: 0.95 }} />
                    {/* Secondary roads */}
                    <div className="absolute w-full" style={{ top: "65%", height: "4px", backgroundColor: "#f5f0ea", opacity: 0.9 }} />
                    <div className="absolute h-full" style={{ left: "65%", width: "4px", backgroundColor: "#f5f0ea", opacity: 0.9 }} />
                    <div className="absolute w-full" style={{ top: "22%", height: "3px", backgroundColor: "#f5f0ea", opacity: 0.7 }} />
                    <div className="absolute h-full" style={{ left: "20%", width: "3px", backgroundColor: "#f5f0ea", opacity: 0.7 }} />
                    {/* Block fills */}
                    <div className="absolute" style={{ top: "0%", left: "0%", width: "38%", height: "40%", backgroundColor: "#ddd9d2", opacity: 0.5 }} />
                    <div className="absolute" style={{ top: "44%", left: "42%", width: "21%", height: "19%", backgroundColor: "#d4edd8", opacity: 0.6 }} />
                    <div className="absolute" style={{ top: "0%", left: "42%", width: "20%", height: "40%", backgroundColor: "#ddd9d2", opacity: 0.4 }} />
                </div>

                {/* Satellite view button */}
                <div className="absolute top-2 right-2 z-10 flex items-center gap-1.5 bg-white/90 backdrop-blur-sm rounded-md px-2 py-1 shadow-sm border border-[#E5E7EB]/80">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" /><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                    </svg>
                    <span className="text-[10px] font-medium text-[#374151]">Satellite View</span>
                </div>

                {/* Zoom controls */}
                <div className="absolute top-2 left-2 z-10 flex flex-col bg-white rounded-md shadow-sm overflow-hidden border border-[#E5E7EB]">
                    <button className="w-6 h-6 flex items-center justify-center text-sm text-[#374151] hover:bg-[#F3F4F6] border-b border-[#E5E7EB] font-bold leading-none transition">+</button>
                    <button className="w-6 h-6 flex items-center justify-center text-sm text-[#374151] hover:bg-[#F3F4F6] font-bold leading-none transition">−</button>
                </div>

                {/* Subject property label */}
                <div
                    className="absolute z-10 flex items-center gap-1.5 bg-white text-[10px] font-semibold px-2 py-1 rounded-md shadow-md text-[#101828] border border-[#E5E7EB] whitespace-nowrap"
                    style={{ top: "40%", left: "12%" }}
                >
                    <span className="w-2 h-2 rounded-full bg-[#101828] shrink-0" />
                    1248 Highland Avenue
                </div>

                {/* Red location pin (target property) */}
                <div
                    className="absolute z-10"
                    style={{ top: "52%", left: "36%", transform: "translate(-50%, -100%)" }}
                >
                    <svg width="20" height="28" viewBox="0 0 20 28" fill="none">
                        <path d="M10 0C4.48 0 0 4.48 0 10c0 7.5 10 18 10 18S20 17.5 20 10C20 4.48 15.52 0 10 0z" fill="#EF4444" />
                        <circle cx="10" cy="10" r="4" fill="white" />
                    </svg>
                </div>

                {/* AI Chat bubble */}
                <div className="absolute bottom-2 right-2 z-10">
                    <div className="w-8 h-8 rounded-full bg-[#101828] flex items-center justify-center shadow-lg cursor-pointer hover:bg-[#1D2939] transition">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* Score rows — with dividers between each */}
            <div className="px-4 pb-3">
                {scores.map((score, idx) => (
                    <div key={score.label}>
                        <div className="flex items-center justify-between py-3">
                            <div className="flex items-center gap-2.5">
                                <Image src={score.icon} alt={score.label} width={14} height={14} className="shrink-0 opacity-70" />
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
