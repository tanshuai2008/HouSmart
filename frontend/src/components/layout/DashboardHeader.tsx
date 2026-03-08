"use client";
import React, { useState } from "react";
import Image from "next/image";
import { Bell, ChevronDown, Search } from "lucide-react";

import logoIcon from "@/assets/dashboard/icons/logo-icon.svg";
import logoText from "@/assets/dashboard/icons/logo-text.svg";
import userAvatarImg from "@/assets/dashboard/images/user-avatar.png";

interface DashboardHeaderProps {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    userName?: string;
    userRole?: string;
    userAvatar?: any;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
    searchValue = "1248 Highland Avenue, Seattle WA",
    onSearchChange,
    userName = "John Doe",
    userRole = "Pro Investor",
    userAvatar = userAvatarImg,
}) => {
    const [isProfileOpen, setIsProfileOpen] = useState(false);

    return (
        <header className="sticky top-0 z-50 bg-white border-b border-[#E5E7EB] h-14">
            <div className="max-w-[1340px] mx-auto px-5 h-full flex items-center justify-between gap-6">
                {/* Logo */}
                <div className="flex items-center gap-2 shrink-0">
                    <Image
                        src={logoIcon}
                        alt="HouSmart Logo"
                        width={32}
                        height={32}
                    />
                    <Image
                        src={logoText}
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
                    <div className="relative">
                        <button
                            onClick={() => setIsProfileOpen(!isProfileOpen)}
                            className="flex items-center gap-2 hover:bg-[#F3F4F6] rounded-lg px-2 py-1 transition border-0 outline-none focus:outline-none"
                        >
                            <Image
                                src={userAvatar}
                                alt={userName}
                                width={30}
                                height={30}
                                className="rounded-full object-cover"
                            />
                            <div className="hidden md:flex flex-col text-left">
                                <span className="text-[13px] font-semibold text-[#101828] leading-tight">
                                    {userName}
                                </span>
                                <span className="text-[11px] text-[#6B7280] leading-tight">
                                    {userRole}
                                </span>
                            </div>
                            <ChevronDown size={12} className="text-[#6B7280] hidden md:block" />
                        </button>

                        {/* Dropdown Menu */}
                        {isProfileOpen && (
                            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-[0px_8px_32px_rgba(0,0,0,0.12)] border border-[#E5E7EB] z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                {/* Header */}
                                <div className="p-4 border-b border-[#E5E7EB] flex flex-col gap-0.5 pointer-events-none">
                                    <span className="text-[15px] font-bold text-[#101828] leading-snug">{userName}</span>
                                    <span className="text-[14px] text-[#6B7280] leading-none">{userRole}</span>
                                </div>

                                {/* Primary Nav */}
                                <div className="py-2 border-b border-[#E5E7EB] flex flex-col">
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        User Profile
                                    </button>
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        Saved Properties
                                    </button>
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        AI Preferences
                                    </button>
                                </div>

                                {/* Secondary Nav */}
                                <div className="py-2 flex flex-col">
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        Account Settings
                                    </button>
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        Billing & Plan
                                    </button>
                                    <button onClick={() => setIsProfileOpen(false)} className="w-full text-left px-4 py-2.5 text-[15px] text-[#344054] hover:bg-[#F9FAFB] hover:text-[#101828] transition font-medium">
                                        Sign Out
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};
