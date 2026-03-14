import React from "react";
import { SetupProvider } from "@/context/SetupContext";
import { LogoIcon } from "@/components/ui/Icons";

export default function SetupLayout({ children }: { children: React.ReactNode }) {
    return (
        <SetupProvider>
            <div className="min-h-screen bg-[#F9FAFB] flex flex-col items-center py-10 px-4 md:py-20 font-inter">
                {/* Top Logo */}
                <div className="flex items-center gap-3 mb-12">
                    <LogoIcon className="w-10 h-10" />
                    <span className="font-semibold text-lg text-[#101828]">
                        Housmart Setup
                    </span>
                </div>

                {/* Main Card Container */}
                <div className="w-full max-w-[640px] bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm overflow-hidden flex flex-col">
                    {children}
                </div>
            </div>
        </SetupProvider>
    );
}
