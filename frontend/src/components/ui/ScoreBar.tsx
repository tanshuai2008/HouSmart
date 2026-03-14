import React from "react";

interface ScoreBarProps {
    score: number; // 0 to 5
    maxScore?: number;
    activeColor?: string;
    inactiveColor?: string;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
    score,
    maxScore = 5,
    activeColor,
    inactiveColor = "#E5E7EB",
}) => {
    // Determine active color based on score if not provided
    const resolvedActiveColor =
        activeColor ??
        (score >= 4 ? "#12B76A" : score >= 3 ? "#F79009" : "#F04438");

    return (
        <div className="flex items-center gap-[3px]">
            {Array.from({ length: maxScore }).map((_, i) => (
                <span
                    key={i}
                    className="inline-block rounded-full"
                    style={{
                        width: 20,
                        height: 6,
                        backgroundColor: i < score ? resolvedActiveColor : inactiveColor,
                    }}
                />
            ))}
        </div>
    );
};
