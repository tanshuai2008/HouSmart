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

export interface MarketTrendsResponse {
    priceTrend: PriceTrendDataPoint[];
    revenueExpenses: RevenueExpensesDataPoint[];
}
