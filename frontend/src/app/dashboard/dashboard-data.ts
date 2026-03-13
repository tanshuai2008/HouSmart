import transitIcon from "@/assets/dashboard/icons/transit.svg";
import buildingIcon from "@/assets/dashboard/icons/building.svg";
import checkCircleIcon from "@/assets/dashboard/icons/check-circle.svg";
import infrastructureIcon from "@/assets/dashboard/icons/infrastructure.svg";
import trendDownIcon from "@/assets/dashboard/icons/trend-down.svg";
import safetyScoreIcon from "@/assets/dashboard/icons/SafetyScoreIcon.svg";
import schoolScoreIcon from "@/assets/dashboard/icons/SchoolScoreIcon.svg";
import amenityScoreIcon from "@/assets/dashboard/icons/AmenityScoreIcon.svg";
import transitScoreIcon from "@/assets/dashboard/icons/TransitScoreIcon.svg";
import noiseScoreIcon from "@/assets/dashboard/icons/NoiseScoreIcon.svg";
import redNoiseIcon from "@/assets/dashboard/icons/RedNoiseIcon.svg";

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

export const dashboardData = {
    property: {
        address: "1248 Highland Avenue",
        neighborhood: "Queen Anne, Seattle WA",
        beds: 4,
        baths: 2.5,
        sqft: "2,180",
        yearBuilt: 1948,
    },
    insight: {
        verdict: "Strong Buy" as const,
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
                description: "New light rail station opening 2027 (0.3mi). Expected to drive 10-15% premium.",
            },
            {
                id: "zoning",
                icon: buildingIcon,
                title: "Zoning Bonus",
                description: "RSL zoning allows for immediate ADU addition (+800 sqft allowable).",
            },
            {
                id: "turnkey",
                icon: checkCircleIcon,
                title: "Turnkey Asset",
                description: "Recent renovation (2022) mitigates near-term CapEx risk.",
            },
        ],
        riskFactors: [
            {
                id: "noise",
                icon: redNoiseIcon,
                title: "Noise Pollution",
                description: "Located under secondary flight path. Outdoor noise peaks at 65dB.",
            },
            {
                id: "infrastructure",
                icon: infrastructureIcon,
                title: "Infrastructure Age",
                description: "Original sewer line (1948). Recommend scope inspection ($10k risk).",
            },
            {
                id: "market",
                icon: trendDownIcon,
                title: "Market Softening",
                description: "Inventory days-on-market up 15% month-over-month.",
            },
        ],
    },
    financialMetrics: [
        {
            label: "MONTHLY RENT",
            value: "$3,500 / mo",
            subLabel: "Estimated monthly rental income.",
            trend: "neutral" as const,
            trendColor: "neutral" as const,
            tooltipText: "Estimated monthly rental income based on our rental data models.",
        },
        {
            label: "RENT-TO-PRICE",
            value: "3.4%",
            subLabel: "Rental yield based on median house value.",
            trend: "neutral" as const,
            trendColor: "neutral" as const,
            tooltipText: "Rental yield based on median house value.",
        },
        {
            label: "TENANT QUALITY INDEX",
            value: "High",
            subLabel: "Based on local education level vs national average.",
            trend: "neutral" as const,
            trendColor: "neutral" as const,
            tooltipText: "Calculated from local education attainment versus the national average.",
        },
        {
            label: "AFFORDABILITY INDEX",
            value: "28%",
            subLabel: "Highly affordable. Tenants can easily pay rent.",
            trend: "neutral" as const,
            trendColor: "neutral" as const,
            tooltipText: "Based on estimated rent vs local median income.",
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
    ] satisfies PriceTrendDataPoint[],
    revenueExpenses: [
        { month: "2021", revenue: 850000, expenses: 0 },
        { month: "H2 21", revenue: 920000, expenses: 0 },
        { month: "2022", revenue: 1050000, expenses: 0 },
        { month: "H2 22", revenue: 1010000, expenses: 0 },
        { month: "2023", revenue: 980000, expenses: 0 },
        { month: "H2 23", revenue: 995000, expenses: 0 },
        { month: "2024", revenue: 1025000, expenses: 0 },
    ] satisfies RevenueExpensesDataPoint[],
    locationScores: [
        {
            label: "Safety Score",
            filledBars: 3,
            tone: "positive" as const,
            icon: safetyScoreIcon,
            tooltipText: "Composite index based on local crime rates, street lighting coverage, and pedestrian safety metrics.",
        },
        {
            label: "Schools",
            filledBars: 3,
            tone: "positive" as const,
            icon: schoolScoreIcon,
            tooltipText: "Aggregated rating based on test scores, student-teacher ratios, and funding of nearby public schools.",
        },
        {
            label: "Lifestyle Amenities",
            filledBars: 3,
            tone: "positive" as const,
            icon: amenityScoreIcon,
            tooltipText: "Density and quality of cafes, restaurants, gyms, parks, and shopping centers within walking distance.",
        },
        {
            label: "Transit Access",
            filledBars: 2,
            tone: "warning" as const,
            icon: transitScoreIcon,
            tooltipText: "Availability, frequency, and proximity of public transportation options like bus stops and train stations.",
        },
        {
            label: "Noise Levels",
            filledBars: 3,
            tone: "negative" as const,
            icon: noiseScoreIcon,
            tooltipText: "Decibel measurements derived from traffic patterns, flight paths, and nearby construction activity.",
        },
    ],
    comparableListings: [
        {
            id: "1",
            address: "1422 Highland Dr",
            neighborhood: "Queen Anne, Seattle W",
            listedRent: "$7,050",
            rentPerSqft: "$3.15 / sq ft",
            matchPercent: 94,
            specs: "4 bd / 3 ba",
            sqft: "2,240 sq ft",
            listedDate: "Oct 12, 2025",
            daysAgo: 8,
            status: "Active" as const,
        },
        {
            id: "2",
            address: "1520 6th Ave W",
            neighborhood: "West Queen Anne, Sea",
            listedRent: "$5,150",
            rentPerSqft: "$2.95 / sq ft",
            matchPercent: 88,
            specs: "3 bd / 2 ba",
            sqft: "1,750 sq ft",
            listedDate: "Sep 28, 2025",
            daysAgo: 22,
            status: "Active" as const,
        },
        {
            id: "3",
            address: "1308 Bigelow Ave N",
            neighborhood: "East Queen Anne, Sea",
            listedRent: "$8,900",
            rentPerSqft: "$3.42 / sq ft",
            matchPercent: 72,
            specs: "4 bd / 3.5 ba",
            sqft: "2,600 sq ft",
            listedDate: "Aug 15, 2025",
            daysAgo: 65,
            status: "Inactive" as const,
        },
    ],
};
