import React from "react";
import { FeatureCheckIcon } from "./Icons";

interface SelectableCardProps {
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    selected: boolean;
    onClick: () => void;
}

export const SelectableCard = ({ title, description, icon: Icon, selected, onClick }: SelectableCardProps) => {
    return (
        <div
            onClick={onClick}
            className={`w-full flex items-center gap-4 p-5 rounded-[12px] border cursor-pointer transition-all ${selected
                ? "bg-[#F0FDF4] border-[#86EFAC]"
                : "bg-white border-[#E5E7EB] hover:border-[#D1D5DC]"
                }`}
        >
            <div
                className={`w-10 h-10 flex-shrink-0 rounded-[8px] flex items-center justify-center ${selected ? "bg-[#DCFCE7]" : "bg-[#F3F4F6]"
                    }`}
            >
                <Icon
                    className={`w-5 h-5 ${selected ? "text-[#00BC7D]" : "text-[#9CA3AF]"
                        }`}
                />
            </div>

            <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-[17px] leading-[24px] text-[#111827]">
                        {title}
                    </span>
                    {selected && <FeatureCheckIcon className="w-[20px] h-[20px] text-[#00BC7D]" />}
                </div>
                <p className={`font-normal text-[15px] leading-[22px] ${selected ? "text-[#00BC7D]" : "text-[#6B7280]"
                    }`}>
                    {description}
                </p>
            </div>
        </div>
    );
};
