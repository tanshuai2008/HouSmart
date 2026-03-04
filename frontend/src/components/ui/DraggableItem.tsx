import React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

interface DraggableItemProps {
    id: string;
    title: string;
    description: string;
    index: number;
}

export const DraggableItem = ({ id, title, description, index }: DraggableItemProps) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`w-full flex items-center gap-4 p-5 rounded-[12px] border bg-white transition-shadow ${isDragging ? "opacity-50 shadow-lg border-[#00BC7D] z-50 relative" : "border-[#E5E7EB]"
                }`}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="cursor-grab hover:cursor-grabbing flex-shrink-0 text-[#9CA3AF] p-1 -ml-2"
            >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="5" cy="4" r="1.5" />
                    <circle cx="5" cy="8" r="1.5" />
                    <circle cx="5" cy="12" r="1.5" />
                    <circle cx="11" cy="4" r="1.5" />
                    <circle cx="11" cy="8" r="1.5" />
                    <circle cx="11" cy="12" r="1.5" />
                </svg>
            </div>

            <div className="w-6 h-6 rounded-full bg-[#F3F4F6] flex-shrink-0 flex items-center justify-center font-medium text-[11px] text-[#6B7280]">
                {index + 1}
            </div>

            <div className="flex-1">
                <span className="block font-semibold text-[17px] leading-[24px] text-[#111827] mb-1">
                    {title}
                </span>
                <p className="font-normal text-[15px] leading-[22px] text-[#6B7280]">
                    {description}
                </p>
            </div>
        </div>
    );
};
