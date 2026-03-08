"use client";
import React from "react";
import Image, { StaticImageData } from "next/image";
import { PropertyDetails } from "@/lib/mockData";

import bedIcon from "@/assets/dashboard/icons/bed.svg";
import bathIcon from "@/assets/dashboard/icons/bath.svg";
import expandIcon from "@/assets/dashboard/icons/expand.svg";
import calendarIcon from "@/assets/dashboard/icons/calendar.svg";

interface PropertyContextProps {
    property: PropertyDetails;
}

const SpecItem: React.FC<{ icon: StaticImageData; label: string }> = ({ icon, label }) => (
    <span className="flex items-center gap-1.5 text-[12px] text-[#374151]">
        <Image src={icon} alt={label} width={14} height={14} className="shrink-0 opacity-60" />
        {label}
    </span>
);

export const PropertyContext: React.FC<PropertyContextProps> = ({ property }) => {
    return (
        <div className="pb-4">
            {/* Hero image — inset with padding and rounded corners */}
            <div className="px-4 pt-4">
                <div className="relative w-full h-[220px] rounded-xl overflow-hidden">
                    <Image
                        src={property.heroImage as any}
                        alt={property.address}
                        fill
                        className="object-cover"
                        sizes="320px"
                        priority
                    />
                </div>
            </div>

            {/* Details */}
            <div className="px-4 pt-4 flex flex-col gap-1.5">
                <h3 className="text-[15px] font-bold text-[#101828] leading-snug">{property.address}</h3>
                <p className="text-[12px] text-[#6B7280]">{property.neighborhood}</p>
                <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1.5">
                    <SpecItem icon={bedIcon} label={`${property.beds} bd`} />
                    <SpecItem icon={bathIcon} label={`${property.baths} ba`} />
                    <SpecItem icon={expandIcon} label={`${property.sqft} sqft`} />
                    <SpecItem icon={calendarIcon} label={`${property.yearBuilt}`} />
                </div>
            </div>
        </div>
    );
};
