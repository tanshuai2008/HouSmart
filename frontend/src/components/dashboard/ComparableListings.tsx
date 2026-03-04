"use client";
import React from "react";
import { Badge, getMatchVariant } from "@/components/ui/Badge";
import { ComparableListing } from "@/lib/mockData";

interface ComparableListingsProps {
    listings: ComparableListing[];
    radius?: string;
}

export const ComparableListings: React.FC<ComparableListingsProps> = ({
    listings,
    radius = "0.5 mi radius",
}) => {
    return (
        <div className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-[#F3F4F6]">
                <span className="text-[10px] font-semibold text-[#6B7280] tracking-[0.08em] uppercase">
                    Comparable Listings
                </span>
                <span className="text-[10px] text-[#9CA3AF]">{radius}</span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-[#F3F4F6]">
                            {[
                                "Property Address",
                                "Property Value",
                                "Listed Rent",
                                "Similarity",
                                "Details",
                                "Listed Date",
                            ].map((col) => (
                                <th
                                    key={col}
                                    className="text-left text-[10px] font-semibold text-[#9CA3AF] tracking-[0.06em] uppercase px-5 py-2.5 whitespace-nowrap bg-white"
                                >
                                    {col}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {listings.map((listing) => {
                            const matchVariant = getMatchVariant(listing.matchPercent);
                            return (
                                <tr
                                    key={listing.id}
                                    className="border-b border-[#F9FAFB] last:border-0 hover:bg-[#FAFAFA] transition"
                                >
                                    {/* Address */}
                                    <td className="px-5 py-3 min-w-[140px]">
                                        <p className="text-[12px] font-semibold text-[#101828]">{listing.address}</p>
                                        <p className="text-[11px] text-[#9CA3AF] truncate max-w-[140px] mt-0.5">
                                            {listing.neighborhood}
                                        </p>
                                    </td>

                                    {/* Property Value */}
                                    <td className="px-5 py-3 whitespace-nowrap">
                                        <p className="text-[12px] font-semibold text-[#101828]">{listing.propertyValue}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">Est. Payment {listing.estPayment}</p>
                                    </td>

                                    {/* Listed Rent */}
                                    <td className="px-5 py-3 whitespace-nowrap">
                                        <p className="text-[12px] font-semibold text-[#101828]">{listing.listedRent}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.rentPerSqft}</p>
                                    </td>

                                    {/* Similarity */}
                                    <td className="px-5 py-3">
                                        <Badge variant={matchVariant}>{listing.matchPercent}% Match</Badge>
                                    </td>

                                    {/* Details */}
                                    <td className="px-5 py-3 whitespace-nowrap">
                                        <p className="text-[12px] text-[#101828]">{listing.specs}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.sqft}</p>
                                    </td>

                                    {/* Listed Date */}
                                    <td className="px-5 py-3 whitespace-nowrap">
                                        <p className="text-[12px] text-[#101828]">{listing.listedDate}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.daysAgo} days ago</p>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
