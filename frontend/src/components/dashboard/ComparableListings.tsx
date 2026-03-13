"use client";
import React from "react";
import { Badge, getMatchVariant } from "@/components/ui/Badge";

interface ComparableListingsProps {
    listings: Array<{
        id: string;
        address: string;
        neighborhood: string;
        listedRent: string;
        rentPerSqft: string;
        matchPercent: number;
        specs: string;
        sqft: string;
        listedDate: string;
        daysAgo: number;
        status: "Active" | "Inactive";
    }>;
    radius?: string;
}

export const ComparableListings: React.FC<ComparableListingsProps> = ({
    listings,
    radius = "0.5 mi radius",
}) => {
    return (
        <div className="bg-white border border-[#E5E7EB] rounded-xl shadow-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#F3F4F6]">
                <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
                    Comparable Listings
                </span>
                <span className="text-[10px] text-[#9CA3AF]">{radius}</span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full table-fixed">
                    <colgroup>
                        <col className="w-[24%]" />
                        <col className="w-[14%]" />
                        <col className="w-[15%]" />
                        <col className="w-[17%]" />
                        <col className="w-[18%]" />
                        <col className="w-[12%]" />
                    </colgroup>
                    <thead>
                        <tr className="border-b border-[#F3F4F6]">
                            <th className="text-left text-[10px] font-semibold text-[#9CA3AF] tracking-[0.06em] uppercase px-5 py-3 min-w-[190px]">
                                Property<br />Address
                            </th>
                            {[
                                "Listed Rent",
                                "Similarity",
                                "Details",
                                "Listed Date",
                                "Status",
                            ].map((col) => (
                                <th
                                    key={col}
                                    className="text-left text-[10px] font-semibold text-[#9CA3AF] tracking-[0.06em] uppercase px-5 py-3 whitespace-nowrap"
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
                                    className="border-b border-[#F3F4F6] last:border-0 hover:bg-[#FAFAFA] transition"
                                >
                                    {/* Address */}
                                    <td className="px-5 py-4 min-w-[190px]">
                                        <p className="text-[12px] font-bold text-[#101828]">{listing.address}</p>
                                        <p className="text-[11px] text-[#9CA3AF] truncate max-w-[220px] mt-0.5">
                                            {listing.neighborhood}
                                        </p>
                                    </td>

                                    {/* Listed Rent */}
                                    <td className="px-5 py-4 whitespace-nowrap">
                                        <p className="text-[12px] font-bold text-[#101828]">{listing.listedRent}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.rentPerSqft}</p>
                                    </td>

                                    {/* Similarity */}
                                    <td className="px-5 py-4">
                                        <Badge variant={matchVariant}>{listing.matchPercent}% Match</Badge>
                                    </td>

                                    {/* Details */}
                                    <td className="px-5 py-4 whitespace-nowrap">
                                        <p className="text-[12px] font-semibold text-[#101828]">{listing.specs}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.sqft}</p>
                                    </td>

                                    {/* Listed Date */}
                                    <td className="px-5 py-4 whitespace-nowrap">
                                        <p className="text-[12px] font-bold text-[#101828]">{listing.listedDate}</p>
                                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{listing.daysAgo} days ago</p>
                                    </td>

                                    {/* Status */}
                                    <td className="px-5 py-4 whitespace-nowrap">
                                        <span
                                            className={`inline-flex items-center rounded-full px-3 py-1 text-[12px] font-semibold ${
                                                listing.status === "Active"
                                                    ? "bg-[#ECFDF3] text-[#027A48]"
                                                    : "bg-[#F2F4F7] text-[#475467]"
                                            }`}
                                        >
                                            {listing.status}
                                        </span>
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
