"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect, useRef } from "react";
import { getOnboardingAnswers, upsertOnboardingAnswers } from "@/lib/api/onboarding";
import { useAuth } from "@/providers/auth-context";

// Types for the onboarding data
export type UserRole = "Individual Investor" | "Real Estate Agent" | "Institutional Buyer" | null;
export type ExperienceLevel = "Newbie (1st Deal)" | "Experienced Investor" | null;
export type InvestmentGoal = "Cash Flow" | "Long-term Appreciation" | "Balanced Mix" | null;

// Initial state shape
interface SetupState {
    role: UserRole;
    experience: ExperienceLevel;
    goal: InvestmentGoal;
    priorities: string[]; // Ordered list of IDs
    market: string | null;
}

const defaultState: SetupState = {
    role: null,
    experience: null,
    goal: null,
    priorities: [
        "safety",
        "schools",
        "proximity",
        "demographics"
    ],
    market: null,
};

interface SetupContextType {
    data: SetupState;
    updateData: (updates: Partial<SetupState>) => void;
    isStepValid: (step: number) => boolean;
}

const SetupContext = createContext<SetupContextType | undefined>(undefined);

export const SetupProvider = ({ children }: { children: ReactNode }) => {
    const { user } = useAuth();
    const [data, setData] = useState<SetupState>(defaultState);
    const [isLoadingSavedData, setIsLoadingSavedData] = useState(true);
    const lastSavedPayloadRef = useRef<string>("");

    const updateData = (updates: Partial<SetupState>) => {
        setData((prev) => ({ ...prev, ...updates }));
    };

    // Helper to check if a specific step has required data before allowing "Next"
    const isStepValid = (step: number): boolean => {
        switch (step) {
            case 1:
                return data.role !== null;
            case 2:
                return data.experience !== null;
            case 3:
                return data.goal !== null;
            case 4:
                return data.priorities.length === 4; // Assuming 4 items to rank
            case 5:
                return data.market !== null;
            default:
                return false;
        }
    };

    useEffect(() => {
        let isMounted = true;

        const hydrateFromBackend = async () => {
            if (!user?.id) {
                if (isMounted) {
                    setIsLoadingSavedData(false);
                }
                return;
            }

            try {
                const saved = await getOnboardingAnswers(user.id);
                if (!saved || !isMounted) {
                    return;
                }

                setData((prev) => ({
                    ...prev,
                    role: (saved.primary_role_ques as UserRole) ?? prev.role,
                    experience: (saved.investment_experience_level_ques as ExperienceLevel) ?? prev.experience,
                    goal: (saved.investment_goal_ques as InvestmentGoal) ?? prev.goal,
                    priorities: saved.priorities_ranking_ques?.length ? saved.priorities_ranking_ques : prev.priorities,
                }));
            } catch (error) {
                console.error("Failed to load onboarding answers:", error);
            } finally {
                if (isMounted) {
                    setIsLoadingSavedData(false);
                }
            }
        };

        hydrateFromBackend();

        return () => {
            isMounted = false;
        };
    }, [user?.id]);

    useEffect(() => {
        if (isLoadingSavedData || !user?.id) {
            return;
        }

        const payload = {
            user_id: user.id,
            primary_role_ques: data.role,
            investment_experience_level_ques: data.experience,
            investment_goal_ques: data.goal,
            priorities_ranking_ques: data.priorities,
        };

        const serializedPayload = JSON.stringify(payload);
        if (serializedPayload === lastSavedPayloadRef.current) {
            return;
        }

        const timeoutId = window.setTimeout(async () => {
            try {
                await upsertOnboardingAnswers(payload);
                lastSavedPayloadRef.current = serializedPayload;
            } catch (error) {
                console.error("Failed to autosave onboarding answers:", error);
            }
        }, 500);

        return () => {
            window.clearTimeout(timeoutId);
        };
    }, [data, isLoadingSavedData, user?.id]);

    return (
        <SetupContext.Provider value={{ data, updateData, isStepValid }}>
            {children}
        </SetupContext.Provider>
    );
};

export const useSetup = () => {
    const context = useContext(SetupContext);
    if (context === undefined) {
        throw new Error("useSetup must be used within a SetupProvider");
    }
    return context;
};
