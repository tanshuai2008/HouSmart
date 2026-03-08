// mockData.ts
// This file mirrors the expected API response structure.
// Replacing this data source with real API calls should require minimal refactoring.

import { StaticImageData } from "next/image";

import propertyHeroImg from "@/assets/dashboard/images/property-hero.png";

import transitIcon from "@/assets/dashboard/icons/transit.svg";
import buildingIcon from "@/assets/dashboard/icons/building.svg";
import checkCircleIcon from "@/assets/dashboard/icons/check-circle.svg";
import noiseIcon from "@/assets/dashboard/icons/noise.svg";
import infrastructureIcon from "@/assets/dashboard/icons/infrastructure.svg";
import trendDownIcon from "@/assets/dashboard/icons/trend-down.svg";
import shieldIcon from "@/assets/dashboard/icons/shield.svg";
import schoolIcon from "@/assets/dashboard/icons/school.svg";
import parkIcon from "@/assets/dashboard/icons/park.svg";
import busIcon from "@/assets/dashboard/icons/bus.svg";

export interface UpsidesRiskItem {
    id: string;
    icon: StaticImageData | string; // path to asset icon
    title: string;
    description: string;
}

export interface FinancialMetric {
    label: string;
    value: string;
    subLabel: string;
    trend: "up" | "down" | "neutral";
    trendColor: "green" | "red" | "orange" | "neutral";
}

export interface PriceTrendDataPoint {
    month: string;
    property: number;
    market: number;
}

export interface RevenueExpensesDataPoint {
    month: string;
    revenue: number;
    expenses: number;
}

export interface LocationScore {
    label: string;
    score: number; // 0-5
    icon: StaticImageData | string; // path to asset icon
}

export interface ComparableListing {
    id: string;
    address: string;
    neighborhood: string;
    propertyValue: string;
    estPayment: string;
    listedRent: string;
    rentPerSqft: string;
    matchPercent: number;
    specs: string; // e.g. "4 bd • 3 ba"
    sqft: string;
    listedDate: string;
    daysAgo: number;
}

export interface PropertyDetails {
    address: string;
    neighborhood: string;
    beds: number;
    baths: number;
    sqft: string;
    yearBuilt: number;
    heroImage: StaticImageData | string;
}

export interface PropertyInsight {
    verdict: "Strong Buy" | "Buy" | "Hold" | "Sell";
    aiConfidence: number; // percentage
    headline: string;
    summary: string;
    dataPoints: number;
    comparableSales: number;
    lastUpdated: string; // e.g. "2h ago"
    upsideDrivers: UpsidesRiskItem[];
    riskFactors: UpsidesRiskItem[];
}

export interface DashboardData {
    property: PropertyDetails;
    insight: PropertyInsight;
    financialMetrics: FinancialMetric[];
    priceTrend: PriceTrendDataPoint[];
    revenueExpenses: RevenueExpensesDataPoint[];
    locationScores: LocationScore[];
    comparableListings: ComparableListing[];
}

const mockDashboardData: DashboardData = {
    property: {
        address: "1248 Highland Avenue",
        neighborhood: "Queen Anne, Seattle WA",
        beds: 4,
        baths: 2.5,
        sqft: "2,180",
        yearBuilt: 1948,
        heroImage: propertyHeroImg,
    },

    insight: {
        verdict: "Strong Buy",
        aiConfidence: 94,
        headline: "Transit expansion drives high appreciation potential.",
        summary:
            "Our model identifies this property as undervalued by 4.2% relative to the neighborhood average. Key value drivers include the 2027 light rail station and RSL zoning changes.",
        undervaluedBy: "4.2",
        dataPoints: 142,
        comparableSales: 12,
        lastUpdated: "2h ago",
        upsideDrivers: [
            {
                id: "transit",
                icon: transitIcon,
                title: "Transit Catalyst",
                description:
                    "New light rail station opening 2027 (0.3mi). Expected to drive 10–15% premium.",
            },
            {
                id: "zoning",
                icon: buildingIcon,
                title: "Zoning Bonus",
                description:
                    "RSL zoning allows for immediate ADU addition (+800 sqft allowable).",
            },
            {
                id: "turnkey",
                icon: checkCircleIcon,
                title: "Turnkey Asset",
                description:
                    "Recent renovation (2022) mitigates near-term CapEx risk.",
            },
        ],
        riskFactors: [
            {
                id: "noise",
                icon: noiseIcon,
                title: "Noise Pollution",
                description:
                    "Located under secondary flight path. Outdoor noise peaks at 65dB.",
            },
            {
                id: "infrastructure",
                icon: infrastructureIcon,
                title: "Infrastructure Age",
                description:
                    "Original sewer line (1948). Recommend scope inspection ($10k risk).",
            },
            {
                id: "market",
                icon: trendDownIcon,
                title: "Market Softening",
                description: "Inventory days-on-market up 15% month-over-month.",
            },
        ],
    } as PropertyInsight & { undervaluedBy: string },

    financialMetrics: [
        {
            label: "MONTHLY RENT",
            value: "$3,500 / mo",
            subLabel: "Estimated monthly rental income.",
            trend: "neutral",
            trendColor: "neutral",
        },
        {
            label: "RENT-TO-PRICE",
            value: "3.4%",
            subLabel: "Rental yield based on median house value.",
            trend: "neutral",
            trendColor: "neutral",
        },
        {
            label: "TENANT QUALITY INDEX",
            value: "High",
            subLabel: "Based on local education level vs national average.",
            trend: "neutral",
            trendColor: "neutral",
        },
        {
            label: "AFFORDABILITY INDEX",
            value: "28%",
            subLabel: "Highly affordable. Tenants can easily pay rent.",
            trend: "neutral",
            trendColor: "neutral",
        },
    ],

    priceTrend: [
        { month: "2021", property: 98.4, market: 0 },
        { month: "H2 21", property: 99.1, market: 0 },
        { month: "2022", property: 101.4, market: 0 },
        { month: "H2 22", property: 100.8, market: 0 },
        { month: "2023", property: 99.0, market: 0 },
        { month: "H2 23", property: 98.6, market: 0 },
        { month: "2024", property: 99.4, market: 0 },
    ],

    revenueExpenses: [
        { month: "2021", revenue: 850000, expenses: 0 },
        { month: "H2 21", revenue: 920000, expenses: 0 },
        { month: "2022", revenue: 1050000, expenses: 0 },
        { month: "H2 22", revenue: 1010000, expenses: 0 },
        { month: "2023", revenue: 980000, expenses: 0 },
        { month: "H2 23", revenue: 995000, expenses: 0 },
        { month: "2024", revenue: 1025000, expenses: 0 },
    ],

    locationScores: [
        { label: "Safety Score", score: 4, icon: shieldIcon },
        { label: "Schools", score: 4, icon: schoolIcon },
        { label: "Lifestyle Amenities", score: 4, icon: parkIcon },
        { label: "Transit Access", score: 3, icon: busIcon },
        { label: "Noise Levels", score: 2, icon: noiseIcon },
    ],

    comparableListings: [
        {
            id: "1",
            address: "1422 Highland Dr",
            neighborhood: "Queen Anne, Seattle W",
            propertyValue: "$1,350,000",
            estPayment: "$7,100/mo",
            listedRent: "$7,050",
            rentPerSqft: "$3.15 / sq ft",
            matchPercent: 94,
            specs: "4 bd • 3 ba",
            sqft: "2,240 sq ft",
            listedDate: "Oct 12, 2025",
            daysAgo: 8,
        },
        {
            id: "2",
            address: "1520 6th Ave W",
            neighborhood: "West Queen Anne, Sea",
            propertyValue: "$1,120,000",
            estPayment: "$5,900/mo",
            listedRent: "$5,150",
            rentPerSqft: "$2.95 / sq ft",
            matchPercent: 88,
            specs: "3 bd • 2 ba",
            sqft: "1,750 sq ft",
            listedDate: "Sep 28, 2025",
            daysAgo: 22,
        },
        {
            id: "3",
            address: "1308 Bigelow Ave N",
            neighborhood: "East Queen Anne, Sea",
            propertyValue: "$1,450,000",
            estPayment: "$7,600/mo",
            listedRent: "$8,900",
            rentPerSqft: "$3.42 / sq ft",
            matchPercent: 72,
            specs: "4 bd • 3.5 ba",
            sqft: "2,600 sq ft",
            listedDate: "Aug 15, 2025",
            daysAgo: 65,
        },
    ],
};

export default mockDashboardData;

