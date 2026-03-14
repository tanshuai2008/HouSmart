import React from "react";

interface CardProps {
    children: React.ReactNode;
    className?: string;
    padding?: "sm" | "md" | "lg" | "none";
}

const paddingMap = {
    none: "",
    sm: "p-3",
    md: "p-4",
    lg: "p-5",
};

export const Card: React.FC<CardProps> = ({
    children,
    className = "",
    padding = "md",
}) => {
    return (
        <div
            className={`bg-white border border-[#E5E7EB] rounded-xl shadow-sm ${paddingMap[padding]} ${className}`}
        >
            {children}
        </div>
    );
};
