"use client";

import Image from "next/image";
import { imageMap } from "@/utils/imageMapper";
import chevronRightIcon from "@/assets/search/icons/chevron-right.svg";

interface InsightListItemProps {
    title: string;
    subtitle: string;
    imageFilename: string;
    rightLabel?: string; // e.g. "2 days ago"
    showChevron?: boolean;
}

export const InsightListItem = ({
    title,
    subtitle,
    imageFilename,
    rightLabel,
    showChevron = false,
}: InsightListItemProps) => {
    const imgSrc = imageMap[imageFilename];

    return (
        <div className="flex items-center justify-between py-3 cursor-pointer hover:bg-gray-50 rounded-lg group transition-colors px-2 -mx-2">
            <div className="flex items-center space-x-4">
                {imgSrc && (
                    <div className="relative w-10 h-10 rounded-full overflow-hidden flex-shrink-0 bg-gray-100 border border-gray-100">
                        <Image
                            src={imgSrc}
                            alt={title}
                            fill
                            className="object-cover"
                            sizes="40px"
                        />
                    </div>
                )}
                <div className="flex flex-col">
                    <span className="text-sm font-semibold text-gray-900">{title}</span>
                    <span className="text-xs text-gray-500 mt-0.5">{subtitle}</span>
                </div>
            </div>

            {/* Right side component */}
            <div className="flex items-center text-xs text-gray-400">
                {rightLabel && <span>{rightLabel}</span>}
                {showChevron && (
                    <Image
                        src={chevronRightIcon}
                        alt="Go"
                        width={16}
                        height={16}
                        className="opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                    />
                )}
            </div>
        </div>
    );
};
