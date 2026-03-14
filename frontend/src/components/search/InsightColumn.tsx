"use client";

import Image from "next/image";

interface InsightColumnProps {
    title: string;
    subtitle: string;
    iconSrc: string;
    children: React.ReactNode;
}

export const InsightColumn = ({
    title,
    subtitle,
    iconSrc,
    children,
}: InsightColumnProps) => {
    return (
        <div className="flex flex-col flex-1 p-5 bg-white border border-gray-100 rounded-xl shadow-sm">
            <div className="flex flex-col mb-4">
                <div className="flex items-center space-x-2 text-blue-600 font-semibold text-xs tracking-wider uppercase">
                    <Image src={iconSrc} alt="Icon" width={16} height={16} />
                    <span>{title}</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            </div>

            <div className="flex flex-col divide-y divide-gray-50 flex-1">
                {children}
            </div>
        </div>
    );
};
