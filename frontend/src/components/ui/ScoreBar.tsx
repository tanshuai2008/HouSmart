import React from "react";

interface ScoreBarProps {
    filledBars: number;
    tone: "positive" | "warning" | "negative";
    maxBars?: number;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
    filledBars,
    tone,
    maxBars = 3,
}) => {
    const activeColorClass =
        tone === "positive" ? "bg-[#12B76A]" : tone === "warning" ? "bg-[#F79009]" : "bg-[#F04438]";

    return (
        <div className="flex items-center gap-[3px]">
            {Array.from({ length: maxBars }).map((_, i) => (
                <span
                    key={i}
                    className={`inline-block rounded-full w-[20px] h-[6px] ${i < filledBars ? activeColorClass : "bg-[#E5E7EB]"}`}
                />
            ))}
        </div>
    );
};
