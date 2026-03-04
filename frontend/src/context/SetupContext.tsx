"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

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
    const [data, setData] = useState<SetupState>(defaultState);

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
