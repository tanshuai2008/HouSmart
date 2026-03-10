"use client";
import React from "react";
import Image, { StaticImageData } from "next/image";

import bedIcon from "@/assets/dashboard/icons/bed.svg";
import bathIcon from "@/assets/dashboard/icons/bath.svg";
import expandIcon from "@/assets/dashboard/icons/expand.svg";
import calendarIcon from "@/assets/dashboard/icons/calendar.svg";

interface PropertyContextProps {
    property: {
        address: string;
        neighborhood: string;
        beds: number;
        baths: number;
        sqft: string;
        yearBuilt: number;
    };
}

const SpecItem: React.FC<{ icon: StaticImageData; label: string }> = ({ icon, label }) => (
    <span className="flex items-center gap-1.5 text-[12px] text-[#6B7280] font-medium">
        <Image src={icon} alt={label} width={14} height={14} className="shrink-0 opacity-60" />
        {label}
    </span>
);

export const PropertyContext: React.FC<PropertyContextProps> = ({ property }) => {
    return (
        <div className="pb-5">
            {/* Details */}
            <div className="px-5 pt-5 pb-4 flex flex-col gap-0.5">
                <h3 className="text-[17px] font-bold text-[#101828] leading-tight">{property.address}</h3>
                <p className="text-[13px] text-[#6B7280]">{property.neighborhood}</p>
            </div>

            <hr className="border-t border-[#F3F4F6] mx-5" />

            <div className="px-5 pt-4 flex items-center flex-wrap gap-x-4 gap-y-2">
                <SpecItem icon={bedIcon} label={`${property.beds} bd`} />
                <SpecItem icon={bathIcon} label={`${property.baths} ba`} />
                <SpecItem icon={expandIcon} label={`${property.sqft} sqft`} />
                <SpecItem icon={calendarIcon} label={`${property.yearBuilt}`} />
            </div>
        </div>
    );
};
