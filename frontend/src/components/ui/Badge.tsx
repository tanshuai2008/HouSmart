import React from "react";

type BadgeVariant =
    | "strong-buy"
    | "ai-confidence"
    | "match-high"
    | "match-medium"
    | "match-low"
    | "outline";

interface BadgeProps {
    variant?: BadgeVariant;
    children: React.ReactNode;
    className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
    "strong-buy":
        "bg-[#ECFDF3] text-[#027A48] border border-[#6CE9A6] font-semibold text-xs px-2.5 py-1 rounded-md",
    "ai-confidence":
        "text-[#027A48] font-semibold text-xs flex items-center gap-1",
    "match-high":
        "bg-[#ECFDF3] text-[#027A48] border border-[#6CE9A6] text-xs font-semibold px-2.5 py-1 rounded-md",
    "match-medium":
        "bg-[#EFF8FF] text-[#1D4ED8] border border-[#93C5FD] text-xs font-semibold px-2.5 py-1 rounded-md",
    "match-low":
        "bg-[#F9FAFB] text-[#344054] border border-[#D0D5DD] text-xs font-semibold px-2.5 py-1 rounded-md",
    outline:
        "bg-white text-[#344054] border border-[#D0D5DD] text-xs font-semibold px-2.5 py-1 rounded-md",
};

export const Badge: React.FC<BadgeProps> = ({
    variant = "outline",
    children,
    className = "",
}) => {
    return (
        <span className={`inline-flex items-center ${variantStyles[variant]} ${className}`}>
            {children}
        </span>
    );
};

export function getMatchVariant(
    percent: number
): "match-high" | "match-medium" | "match-low" {
    if (percent >= 90) return "match-high";
    if (percent >= 80) return "match-medium";
    return "match-low";
}
