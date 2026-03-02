"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragEndEvent,
} from "@dnd-kit/core";
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useSetup } from "@/context/SetupContext";
import { StepIndicator } from "@/components/layout/StepIndicator";
import { DraggableItem } from "@/components/ui/DraggableItem";
import { Button } from "@/components/ui/Button";

// Static data mapping for the IDs
const PRIORITY_DATA = {
    safety: { title: "Safety & Low Crime", description: "Peace of mind is my number one priority." },
    schools: { title: "School District Quality", description: "I want properties in areas with top-rated public schools." },
    proximity: { title: "Proximity & Convenience", description: "Focus on areas near major job hubs, transit, and amenities." },
    demographics: { title: "Demographic Stability", description: "I prefer neighborhoods with high homeownership rates and established residents." }
};

export default function PrioritiesStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

    // Local state for smooth drag animations before committing to global context
    const [items, setItems] = useState(data.priorities);

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 5,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = items.indexOf(active.id as string);
            const newIndex = items.indexOf(over.id as string);
            const newOrder = arrayMove(items, oldIndex, newIndex);

            setItems(newOrder);
            // Immediately save the new order to the global setup context
            updateData({ priorities: newOrder });
        }
    };

    const handleNext = () => {
        if (isStepValid(4)) {
            router.push("/auth/setup/market");
        }
    };

    return (
        <>
            <StepIndicator currentStep={4} title="MUST-HAVES" />

            <div className="p-8 flex flex-col items-center">
                <div className="w-full mb-8">
                    <h1 className="font-semibold text-[28px] leading-[36px] text-[#111827] mb-3">
                        Rank Your Priorities
                    </h1>
                    <p className="font-normal text-[16px] leading-[26px] text-[#6B7280]">
                        Drag and drop to rank these factors from most to least important.
                    </p>
                </div>

                <div className="w-full mb-10">
                    <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleDragEnd}
                    >
                        <SortableContext
                            items={items}
                            strategy={verticalListSortingStrategy}
                        >
                            <div className="flex flex-col gap-3">
                                {items.map((id, index) => {
                                    const meta = PRIORITY_DATA[id as keyof typeof PRIORITY_DATA];
                                    return (
                                        <DraggableItem
                                            key={id}
                                            id={id}
                                            index={index}
                                            title={meta.title}
                                            description={meta.description}
                                        />
                                    );
                                })}
                            </div>
                        </SortableContext>
                    </DndContext>
                </div>

                <div className="w-full flex items-center justify-between pt-4 border-t border-[#E5E7EB]">
                    <button
                        onClick={() => router.back()}
                        className="font-semibold text-[13px] leading-[18px] text-[#6B7280] flex items-center hover:text-[#374151] transition-colors"
                    >
                        <svg className="w-4 h-4 mr-2" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12.6665 8H3.33317M3.33317 8L7.33317 12M3.33317 8L7.33317 4" stroke="currentColor" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        BACK
                    </button>

                    <Button
                        variant="default"
                        onClick={handleNext}
                        disabled={!isStepValid(4)}
                        className={`w-auto px-6 h-12 text-[15px] rounded-[12px] bg-[#111827] text-white hover:bg-[#1f2937] ${!isStepValid(4) ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                        Next Step
                        <svg className="w-5 h-5 ml-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M12 5L19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </Button>
                </div>
            </div>
        </>
    );
}
