"use client";
import React from "react";
import Image from "next/image";
import { Bell, ChevronDown, Search } from "lucide-react";

interface DashboardHeaderProps {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    userName?: string;
    userRole?: string;
    userAvatar?: string;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
    searchValue = "1248 Highland Avenue, Seattle WA",
    onSearchChange,
    userName = "John Doe",
    userRole = "Pro Investor",
    userAvatar = "/assets/dashboard/images/user-avatar.png",
}) => {
    return (
        <header className="sticky top-0 z-50 bg-white border-b border-[#E5E7EB] h-14">
            <div className="max-w-[1340px] mx-auto px-5 h-full flex items-center justify-between gap-6">
                {/* Logo */}
                <div className="flex items-center gap-2 shrink-0">
                    <Image
                        src="/assets/dashboard/icons/logo-icon.svg"
                        alt="HouSmart Logo"
                        width={32}
                        height={32}
                    />
                    <Image
                        src="/assets/dashboard/icons/logo-text.svg"
                        alt="HouSmart"
                        width={80}
                        height={21}
                        className="hidden sm:block"
                    />
                </div>

                {/* Search bar */}
                <div className="flex-1 max-w-[420px] relative">
                    <Search
                        className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]"
                        size={14}
                    />
                    <input
                        type="text"
                        value={searchValue}
                        onChange={(e) => onSearchChange?.(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 text-sm border border-[#E5E7EB] rounded-lg bg-[#F9FAFB] text-[#101828] placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#101828]/20 transition"
                        placeholder="Search address..."
                        readOnly={!onSearchChange}
                    />
                </div>

                {/* Right: Bell + Profile */}
                <div className="flex items-center gap-3 shrink-0">
                    {/* Notification bell */}
                    <button className="relative w-8 h-8 flex items-center justify-center rounded-lg hover:bg-[#F3F4F6] transition border-0 outline-none">
                        <Bell size={16} className="text-[#6B7280]" />
                        <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 border-2 border-white" />
                    </button>

                    {/* Separator */}
                    <span className="h-6 w-px bg-[#E5E7EB]" />

                    {/* User profile */}
                    <button className="flex items-center gap-2 hover:bg-[#F3F4F6] rounded-lg px-2 py-1 transition border-0 outline-none">
                        <Image
                            src={userAvatar}
                            alt={userName}
                            width={30}
                            height={30}
                            className="rounded-full object-cover"
                        />
                        <div className="hidden md:flex flex-col text-left">
                            <span className="text-xs font-semibold text-[#101828] leading-tight">
                                {userName}
                            </span>
                            <span className="text-[10px] text-[#6B7280] leading-tight">
                                {userRole}
                            </span>
                        </div>
                        <ChevronDown size={12} className="text-[#6B7280] hidden md:block" />
                    </button>
                </div>
            </div>
        </header>
    );
};
