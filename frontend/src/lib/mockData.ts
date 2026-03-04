// mockData.ts
// This file mirrors the expected API response structure.
// Replacing this data source with real API calls should require minimal refactoring.

export interface UpsidesRiskItem {
    id: string;
    icon: string; // path to asset icon
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
    icon: string; // path to asset icon
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
    heroImage: string;
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
        heroImage: "/assets/dashboard/images/property-hero.png",
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
                icon: "/assets/dashboard/icons/transit.svg",
                title: "Transit Catalyst",
                description:
                    "New light rail station opening 2027 (0.3mi). Expected to drive 10–15% premium.",
            },
            {
                id: "zoning",
                icon: "/assets/dashboard/icons/building.svg",
                title: "Zoning Bonus",
                description:
                    "RSL zoning allows for immediate ADU addition (+800 sqft allowable).",
            },
            {
                id: "turnkey",
                icon: "/assets/dashboard/icons/check-circle.svg",
                title: "Turnkey Asset",
                description:
                    "Recent renovation (2022) mitigates near-term CapEx risk.",
            },
        ],
        riskFactors: [
            {
                id: "noise",
                icon: "/assets/dashboard/icons/noise.svg",
                title: "Noise Pollution",
                description:
                    "Located under secondary flight path. Outdoor noise peaks at 65dB.",
            },
            {
                id: "infrastructure",
                icon: "/assets/dashboard/icons/infrastructure.svg",
                title: "Infrastructure Age",
                description:
                    "Original sewer line (1948). Recommend scope inspection ($10k risk).",
            },
            {
                id: "market",
                icon: "/assets/dashboard/icons/trend-down.svg",
                title: "Market Softening",
                description: "Inventory days-on-market up 15% month-over-month.",
            },
        ],
    } as PropertyInsight & { undervaluedBy: string },

    financialMetrics: [
        {
            label: "EST. VALUE",
            value: "$1.24M",
            subLabel: "↑ 4% vs Mrkt",
            trend: "up",
            trendColor: "green",
        },
        {
            label: "PROJ. 5YR ROI",
            value: "42.5%",
            subLabel: "High Growth",
            trend: "up",
            trendColor: "green",
        },
        {
            label: "CAP RATE",
            value: "5.2%",
            subLabel: "Market Avg",
            trend: "neutral",
            trendColor: "neutral",
        },
        {
            label: "CASH FLOW",
            value: "$240/mo",
            subLabel: "↓ Thin Margin",
            trend: "down",
            trendColor: "orange",
        },
    ],

    priceTrend: [
        { month: "Jan", property: 0.5, market: -0.3 },
        { month: "Feb", property: 0.8, market: 0.2 },
        { month: "Mar", property: -0.5, market: 0.1 },
        { month: "Apr", property: 1.9, market: 0.6 },
        { month: "May", property: 1.5, market: 0.4 },
        { month: "Jun", property: 2.1, market: 0.8 },
        { month: "Jul", property: 2.85, market: 0.9 },
        { month: "Aug", property: 2.4, market: 0.7 },
        { month: "Sep", property: 2.6, market: 0.5 },
        { month: "Oct", property: 1.8, market: 0.3 },
        { month: "Nov", property: -0.95, market: -0.2 },
        { month: "Dec", property: 0.3, market: 0.1 },
    ],

    revenueExpenses: [
        { month: "Jan", revenue: 3900, expenses: 4100 },
        { month: "Feb", revenue: 4100, expenses: 4000 },
        { month: "Mar", revenue: 4200, expenses: 3950 },
        { month: "Apr", revenue: 4350, expenses: 4050 },
        { month: "May", revenue: 4500, expenses: 4000 },
        { month: "Jun", revenue: 4600, expenses: 4150 },
        { month: "Jul", revenue: 4750, expenses: 4300 },
        { month: "Aug", revenue: 4900, expenses: 4250 },
        { month: "Sep", revenue: 5050, expenses: 4100 },
        { month: "Oct", revenue: 5200, expenses: 4200 },
        { month: "Nov", revenue: 5350, expenses: 4150 },
        { month: "Dec", revenue: 5500, expenses: 4300 },
    ],

    locationScores: [
        { label: "Safety Score", score: 4, icon: "/assets/dashboard/icons/shield.svg" },
        { label: "Schools", score: 4, icon: "/assets/dashboard/icons/school.svg" },
        { label: "Lifestyle Amenities", score: 4, icon: "/assets/dashboard/icons/park.svg" },
        { label: "Transit Access", score: 3, icon: "/assets/dashboard/icons/bus.svg" },
        { label: "Noise Levels", score: 2, icon: "/assets/dashboard/icons/noise.svg" },
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
