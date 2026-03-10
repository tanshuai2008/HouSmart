"use client";

import React, { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import {
    DndContext,
    closestCenter,
    DragEndEvent,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from "@dnd-kit/core";
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
} from "@dnd-kit/sortable";

import { StepIndicator } from "@/components/layout/StepIndicator";
import { Button } from "@/components/ui/Button";
import { DraggableItem } from "@/components/ui/DraggableItem";
import { useSetup } from "@/providers/setup-context";

import { PRIORITY_DATA } from "../setup-step-data";
import styles from "../setup-step.module.css";

export default function PrioritiesStep() {
    const router = useRouter();
    const { data, updateData, isStepValid } = useSetup();

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

    const canContinue = isStepValid(4);

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = items.indexOf(active.id as string);
            const newIndex = items.indexOf(over.id as string);
            const newOrder = arrayMove(items, oldIndex, newIndex);

            setItems(newOrder);
            updateData({ priorities: newOrder });
        }
    };

    const handleNext = () => {
        if (canContinue) {
            router.push("/property-input");
        }
    };

    return (
        <>
            <StepIndicator currentStep={4} title="PRIORITIES" />

            <div className={styles.setupStepContainer}>
                <div className={styles.stepHeader}>
                    <h1 className={styles.stepTitle}>Rank Your Priorities</h1>
                    <p className={styles.stepDescription}>
                        Drag and drop to rank these factors from most to least important.
                    </p>
                </div>

                <div className={styles.dragList}>
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                        <SortableContext items={items} strategy={verticalListSortingStrategy}>
                            <div className={styles.dragItems}>
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

                <div className={styles.footerRow}>
                    <button type="button" onClick={() => router.back()} className={styles.backButton}>
                        <ArrowLeft size={16} className={styles.backIcon} />
                        BACK
                    </button>

                    <div className={styles.footerActions}>
                        <button type="button" onClick={() => router.push("/property-input")} className={styles.skipButton}>
                            Skip now
                        </button>
                        <Button
                            variant="default"
                            onClick={handleNext}
                            disabled={!canContinue}
                            className={`${styles.nextButton} ${!canContinue ? styles.nextButtonDisabled : ""}`}
                        >
                            Complete Setup
                        </Button>
                    </div>
                </div>
            </div>
        </>
    );
}
