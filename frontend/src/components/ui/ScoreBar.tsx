import React from "react";

interface ScoreBarProps {
    score: number; // 0 to 5
    maxScore?: number;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
    score,
    maxScore = 5,
}) => {
    const activeColorClass =
        score >= 4 ? "bg-[#12B76A]" : score >= 3 ? "bg-[#F79009]" : "bg-[#F04438]";

    return (
        <div className="flex items-center gap-[3px]">
            {Array.from({ length: maxScore }).map((_, i) => (
                <span
                    key={i}
                    className={`inline-block rounded-full w-[20px] h-[6px] ${i < score ? activeColorClass : "bg-[#E5E7EB]"}`}
                />
            ))}
        </div>
    );
};
