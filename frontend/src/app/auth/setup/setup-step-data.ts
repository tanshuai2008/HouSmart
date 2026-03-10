import type { ComponentType } from "react";
import {
    BalancedMixIcon,
    BalancedMixSelectedIcon,
    CashFlowIcon,
    CashFlowSelectedIcon,
    ExperiencedInvestorIcon,
    ExperiencedInvestorSelectedIcon,
    GraduationCapIcon,
    GraduationCapSelectedIcon,
    IndividualInvestorIcon,
    IndividualInvestorSelectedIcon,
    InstitutionalBuyerIcon,
    InstitutionalBuyerSelectedIcon,
    LongTermAppreciationIcon,
    LongTermAppreciationSelectedIcon,
    RealEstateAgentIcon,
    RealEstateAgentSelectedIcon,
} from "@/components/ui/Icons";
import { ExperienceLevel, InvestmentGoal, UserRole } from "@/providers/setup-context";

type SetupOption<T extends string> = {
    value: T;
    title: string;
    description: string;
    icon: ComponentType<{ className?: string }>;
    selectedIcon: ComponentType<{ className?: string }>;
};

export const ROLE_OPTIONS: Array<SetupOption<Exclude<UserRole, null>>> = [
    {
        value: "Individual Investor",
        title: "Individual Investor",
        description: "Building personal portfolio. Focus on 1-4 unit properties.",
        icon: IndividualInvestorIcon,
        selectedIcon: IndividualInvestorSelectedIcon,
    },
    {
        value: "Real Estate Agent",
        title: "Real Estate Agent",
        description: "Sourcing deals for clients. Deep market analysis required.",
        icon: RealEstateAgentIcon,
        selectedIcon: RealEstateAgentSelectedIcon,
    },
    {
        value: "Institutional Buyer",
        title: "Institutional Buyer",
        description: "High volume acquisition. Cap rate and IRR driven.",
        icon: InstitutionalBuyerIcon,
        selectedIcon: InstitutionalBuyerSelectedIcon,
    },
];

export const EXPERIENCE_OPTIONS: Array<SetupOption<Exclude<ExperienceLevel, null>>> = [
    {
        value: "Newbie (1st Deal)",
        title: "Newbie (1st Deal)",
        description: "AI explains basic concepts. Focus on education and clear risk indicators.",
        icon: GraduationCapIcon,
        selectedIcon: GraduationCapSelectedIcon,
    },
    {
        value: "Experienced Investor",
        title: "Experienced Investor",
        description: "AI generates deep financial KPIs, advanced sensitivity analysis, and tax implications.",
        icon: ExperiencedInvestorIcon,
        selectedIcon: ExperiencedInvestorSelectedIcon,
    },
];

export const GOAL_OPTIONS: Array<SetupOption<Exclude<InvestmentGoal, null>>> = [
    {
        value: "Cash Flow",
        title: "Cash Flow",
        description: "Prioritize immediate monthly income. Lower risk tolerance.",
        icon: CashFlowIcon,
        selectedIcon: CashFlowSelectedIcon,
    },
    {
        value: "Long-term Appreciation",
        title: "Long-term Appreciation",
        description: "Focus on growth markets with transit/zoning upside.",
        icon: LongTermAppreciationIcon,
        selectedIcon: LongTermAppreciationSelectedIcon,
    },
    {
        value: "Balanced Mix",
        title: "Balanced Mix",
        description: "Blend of steady income and moderate growth potential.",
        icon: BalancedMixIcon,
        selectedIcon: BalancedMixSelectedIcon,
    },
];

export const PRIORITY_DATA = {
    safety: {
        title: "Safety & Low Crime",
        description: "Peace of mind is my number one priority.",
    },
    schools: {
        title: "School District Quality",
        description: "I want properties in areas with top-rated public schools.",
    },
    proximity: {
        title: "Proximity & Convenience",
        description: "Focus on areas near major job hubs, transit, and amenities.",
    },
    demographics: {
        title: "Demographic Stability",
        description: "I prefer neighborhoods with high homeownership rates and established residents.",
    },
} as const;
