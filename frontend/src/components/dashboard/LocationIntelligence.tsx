"use client";
import React from "react";
import Image from "next/image";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { LocationScore } from "@/lib/mockData";

interface LocationIntelligenceProps {
    scores: LocationScore[];
    radius?: string;
}

const POI_LEGEND = [
    { label: "Target Property", color: "#101828" },
    { label: "Food/Drink", color: "#B45309" },
    { label: "Education", color: "#1D4ED8" },
    { label: "Commercial", color: "#374151" },
    { label: "Park/Leisure", color: "#15803D" },
    { label: "Grocery", color: "#7E22CE" },
    { label: "Health", color: "#B42318" },
];

const POI_PINS = [
    { top: "25%", left: "55%", color: "#B45309" },
    { top: "60%", left: "70%", color: "#15803D" },
    { top: "30%", left: "22%", color: "#1D4ED8" },
    { top: "72%", left: "28%", color: "#7E22CE" },
    { top: "18%", left: "72%", color: "#B42318" },
    { top: "52%", left: "18%", color: "#B45309" },
    { top: "78%", left: "62%", color: "#1D4ED8" },
    { top: "38%", left: "80%", color: "#15803D" },
    { top: "65%", left: "48%", color: "#374151" },
];

export const LocationIntelligence: React.FC<LocationIntelligenceProps> = ({
    scores,
    radius = "0.5 mi radius",
}) => {
    return (
        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3">
                <span className="text-[10px] font-semibold text-[#6B7280] tracking-[0.08em] uppercase">
                    Location Intelligence
                </span>
                <span className="text-[10px] text-[#9CA3AF]">{radius}</span>
            </div>

            {/* Map */}
            <div className="relative mx-3 mb-3 rounded-lg overflow-hidden h-[210px]">
                {/* Base map (satellite-style grid) */}
                <div
                    className="w-full h-full"
                    style={{
                        backgroundImage: `
              radial-gradient(circle at 30% 50%, rgba(255,200,100,0.25) 0%, transparent 60%),
              radial-gradient(circle at 70% 30%, rgba(100,180,255,0.2) 0%, transparent 60%),
              linear-gradient(rgba(160,180,165,0.35) 1px, transparent 1px),
              linear-gradient(90deg, rgba(160,180,165,0.35) 1px, transparent 1px)
            `,
                        backgroundSize: "100% 100%, 100% 100%, 22px 22px, 22px 22px",
                        backgroundColor: "#8B9E8A",
                    }}
                />

                {/* Road overlays */}
                <div className="absolute inset-0 pointer-events-none">
                    {/* Horizontal yellow road */}
                    <div className="absolute w-full" style={{ top: "46%", height: "5px", backgroundColor: "#F5C842", opacity: 0.85 }} />
                    {/* Vertical yellow road */}
                    <div className="absolute h-full" style={{ left: "38%", width: "5px", backgroundColor: "#F5C842", opacity: 0.85 }} />
                    {/* Secondary roads */}
                    <div className="absolute w-full" style={{ top: "62%", height: "2px", backgroundColor: "#E0CC8A", opacity: 0.7 }} />
                    <div className="absolute h-full" style={{ left: "63%", width: "2px", backgroundColor: "#E0CC8A", opacity: 0.7 }} />
                    <div className="absolute w-full" style={{ top: "28%", height: "2px", backgroundColor: "#C8BA6A", opacity: 0.5 }} />
                    <div className="absolute h-full" style={{ left: "80%", width: "2px", backgroundColor: "#C8BA6A", opacity: 0.5 }} />
                </div>

                {/* Satellite view button */}
                <div className="absolute top-2 right-2 z-10 flex items-center gap-1.5 bg-white/90 backdrop-blur-sm rounded-md px-2 py-1 shadow-sm border border-[#E5E7EB]">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" /><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                    </svg>
                    <span className="text-[10px] font-medium text-[#374151]">Satellite View</span>
                </div>

                {/* Zoom controls */}
                <div className="absolute top-2 left-2 z-10 flex flex-col bg-white rounded-md shadow overflow-hidden border border-[#E5E7EB]">
                    <button className="w-6 h-6 flex items-center justify-center text-sm text-[#374151] hover:bg-[#F3F4F6] border-b border-[#E5E7EB] font-bold leading-none transition">+</button>
                    <button className="w-6 h-6 flex items-center justify-center text-sm text-[#374151] hover:bg-[#F3F4F6] font-bold leading-none transition">−</button>
                </div>

                {/* POI dots */}
                {POI_PINS.map((pin, i) => (
                    <span
                        key={i}
                        className="absolute w-3 h-3 rounded-full border-2 border-white shadow-md"
                        style={{
                            top: pin.top,
                            left: pin.left,
                            backgroundColor: pin.color,
                            transform: "translate(-50%, -50%)",
                            zIndex: 5,
                        }}
                    />
                ))}

                {/* Subject property label */}
                <div
                    className="absolute z-10 flex items-center gap-1 bg-white/95 text-[9px] font-semibold px-1.5 py-0.5 rounded shadow-md text-[#101828] border border-[#E5E7EB] whitespace-nowrap"
                    style={{ top: "44%", left: "12%" }}
                >
                    <span className="w-2 h-2 rounded-full bg-[#101828] shrink-0" />
                    1248 Highland Avenue
                </div>

                {/* AI Chat bubble button – fixed within map context */}
                <div className="absolute bottom-2 right-2 z-10">
                    <div className="w-8 h-8 rounded-full bg-[#101828] flex items-center justify-center shadow-lg cursor-pointer hover:bg-[#1D2939] transition">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* POI Legend */}
            <div className="px-4 pb-2 grid grid-cols-3 gap-x-2 gap-y-1.5">
                {POI_LEGEND.map((cat) => (
                    <div key={cat.label} className="flex items-center gap-1.5">
                        <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: cat.color }}
                        />
                        <span className="text-[10px] text-[#6B7280] truncate">{cat.label}</span>
                    </div>
                ))}
            </div>

            {/* Divider */}
            <div className="h-px bg-[#F3F4F6] mx-4 my-2" />

            {/* Score bars */}
            <div className="px-4 pb-4 flex flex-col gap-2.5">
                {scores.map((score) => (
                    <div key={score.label} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Image src={score.icon} alt={score.label} width={12} height={12} className="shrink-0" />
                            <span className="text-[11px] text-[#344054]">{score.label}</span>
                        </div>
                        <ScoreBar score={score.score} />
                    </div>
                ))}
            </div>
        </div>
    );
};
