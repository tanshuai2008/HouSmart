import type {
    MarketTrendsResponse,
    PriceTrendDataPoint,
    RevenueExpensesDataPoint,
} from "@/types/marketTrends";

function toFiniteNumber(value: unknown): number | null {
    if (typeof value === "number") {
        return Number.isFinite(value) ? value : null;
    }
    if (typeof value === "string") {
        const trimmed = value.trim();
        if (!trimmed) {
            return null;
        }
        const parsed = Number(trimmed.replace(/,/g, ""));
        return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
}

function toNonEmptyString(value: unknown): string | null {
    if (typeof value !== "string") {
        return null;
    }
    const trimmed = value.trim();
    return trimmed || null;
}

export function parsePriceTrendSeries(raw: unknown): PriceTrendDataPoint[] {
    if (!Array.isArray(raw)) {
        return [];
    }

    const points: PriceTrendDataPoint[] = [];
    for (const item of raw) {
        if (!item || typeof item !== "object") {
            continue;
        }
        const record = item as Record<string, unknown>;
        const month = toNonEmptyString(record.month);
        const property = toFiniteNumber(record.property);
        const market = toFiniteNumber(record.market) ?? 0;

        if (!month || property === null) {
            continue;
        }
        points.push({ month, property, market });
    }
    return points;
}

export function parseRevenueExpensesSeries(raw: unknown): RevenueExpensesDataPoint[] {
    if (!Array.isArray(raw)) {
        return [];
    }

    const points: RevenueExpensesDataPoint[] = [];
    for (const item of raw) {
        if (!item || typeof item !== "object") {
            continue;
        }
        const record = item as Record<string, unknown>;
        const month = toNonEmptyString(record.month);
        const revenue = toFiniteNumber(record.revenue);
        const expenses = toFiniteNumber(record.expenses) ?? 0;

        if (!month || revenue === null) {
            continue;
        }
        points.push({ month, revenue, expenses });
    }
    return points;
}

export function parseMarketTrendsResponse(raw: unknown): MarketTrendsResponse {
    if (!raw || typeof raw !== "object") {
        return { priceTrend: [], revenueExpenses: [] };
    }

    const record = raw as Record<string, unknown>;
    return {
        priceTrend: parsePriceTrendSeries(record.priceTrend),
        revenueExpenses: parseRevenueExpensesSeries(record.revenueExpenses),
    };
}
