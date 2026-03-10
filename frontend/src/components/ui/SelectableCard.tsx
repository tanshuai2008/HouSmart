import React from "react";
import { FeatureCheckIcon } from "./Icons";

interface SelectableCardProps {
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    selectedIcon?: React.ComponentType<{ className?: string }>;
    selected: boolean;
    onClick: () => void;
}

export const SelectableCard = ({
    title,
    description,
    icon: Icon,
    selectedIcon: SelectedIcon,
    selected,
    onClick,
}: SelectableCardProps) => {
    const ActiveIcon = selected && SelectedIcon ? SelectedIcon : Icon;

    return (
        <div
            onClick={onClick}
            className={`w-full flex items-center gap-4 p-5 rounded-[12px] border cursor-pointer transition-all ${selected
                ? "bg-[#ECFDF5] border-[#A7F3D0]"
                : "bg-white border-[#E5E7EB] hover:border-[#D1D5DC]"
                }`}
        >
            <div
                className={`w-10 h-10 flex-shrink-0 rounded-[8px] flex items-center justify-center ${selected ? "bg-[#A7F3D0]" : "bg-[#F3F4F6]"
                    }`}
            >
                <ActiveIcon className="w-5 h-5" />
            </div>

            <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                    <span
                        className={`font-semibold text-[17px] leading-[24px] ${selected ? "text-[#065F46]" : "text-[#111827]"
                            }`}
                    >
                        {title}
                    </span>
                    {selected && <FeatureCheckIcon className="w-[20px] h-[20px] text-[#10B981]" />}
                </div>
                <p className={`font-normal text-[15px] leading-[22px] ${selected ? "text-[#059669]" : "text-[#6B7280]"
                    }`}>
                    {description}
                </p>
            </div>
        </div>
    );
};
