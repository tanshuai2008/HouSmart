"use client";
import React from "react";
import Image from "next/image";
import { PropertyDetails } from "@/lib/mockData";

interface PropertyContextProps {
    property: PropertyDetails;
}

const SpecItem: React.FC<{ icon: string; label: string }> = ({ icon, label }) => (
    <span className="flex items-center gap-1 text-[11px] text-[#6B7280]">
        <Image src={icon} alt={label} width={12} height={12} className="shrink-0" />
        {label}
    </span>
);

export const PropertyContext: React.FC<PropertyContextProps> = ({ property }) => {
    return (
        <div>
            {/* Hero image */}
            <div className="relative w-full h-[190px]">
                <Image
                    src={property.heroImage}
                    alt={property.address}
                    fill
                    className="object-cover"
                    sizes="320px"
                    priority
                />
            </div>
            {/* Details */}
            <div className="px-4 pt-3 pb-4 flex flex-col gap-1.5">
                <h3 className="text-[13px] font-bold text-[#101828]">{property.address}</h3>
                <p className="text-[11px] text-[#6B7280]">{property.neighborhood}</p>
                <div className="flex items-center flex-wrap gap-x-2.5 gap-y-1 mt-1">
                    <SpecItem icon="/assets/dashboard/icons/bed.svg" label={`${property.beds} bd`} />
                    <SpecItem icon="/assets/dashboard/icons/bath.svg" label={`${property.baths} ba`} />
                    <SpecItem icon="/assets/dashboard/icons/expand.svg" label={`${property.sqft} sqft`} />
                    <SpecItem icon="/assets/dashboard/icons/calendar.svg" label={`${property.yearBuilt}`} />
                </div>
            </div>
        </div>
    );
};
