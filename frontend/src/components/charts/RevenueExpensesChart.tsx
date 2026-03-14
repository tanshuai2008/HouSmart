"use client";
import React from "react";
import {
    CartesianGrid,
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import type { RevenueExpensesDataPoint } from "@/types/marketTrends";

interface RevenueExpensesChartProps {
    data: RevenueExpensesDataPoint[];
}

function formatMonthLabel(value: string): string {
    const match = /^(\d{4})-(\d{2})$/.exec(value);
    if (!match) {
        return value;
    }

    const year = Number(match[1]);
    const monthIndex = Number(match[2]) - 1;
    const date = new Date(year, monthIndex, 1);
    return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

const CustomTooltip = ({
    active,
    payload,
    label,
}: {
    active?: boolean;
    payload?: Array<{ value: number; name: string }>;
    label?: string;
}) => {
    if (active && payload && payload.length) {
        return (
            <div className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2.5 pr-6 shadow-md">
                <p className="mb-1.5 text-[12px] font-bold text-[#101828]">{label}</p>
                {payload.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-1.5 text-[12px]">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#3B82F6]" />
                        <span className="text-[#6B7280]">Median Price:</span>
                        <span className="font-bold text-[#101828]">${entry.value.toLocaleString()}</span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export const RevenueExpensesChart: React.FC<RevenueExpensesChartProps> = ({
    data,
}) => {
    const values = (data || [])
        .map((point) => (typeof point?.revenue === "number" ? point.revenue : Number(point?.revenue)))
        .filter((value) => Number.isFinite(value)) as number[];

    const defaultMin = 850_000;
    const defaultMax = 1_050_000;
    const minVal = values.length ? Math.min(...values) : defaultMin;
    const maxVal = values.length ? Math.max(...values) : defaultMax;
    const range = Math.max(1, maxVal - minVal);
    const pad = values.length ? range * 0.08 : 0;
    const rawMin = minVal - pad;
    const rawMax = maxVal + pad;

    const magnitude = Math.pow(10, Math.floor(Math.log10(Math.max(1, (rawMax - rawMin) / 4))));
    const normalized = ((rawMax - rawMin) / 4) / magnitude;
    const stepFactor = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
    const step = stepFactor * magnitude;
    const domainMin = Math.floor(rawMin / step) * step;
    const domainMax = Math.ceil(rawMax / step) * step;
    const ticks: number[] = [];
    for (let tick = domainMin; tick <= domainMax + 0.001; tick += step) {
        ticks.push(tick);
    }

    return (
        <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data} margin={{ top: 2, right: 6, left: 2, bottom: 10 }}>
                <CartesianGrid vertical={false} stroke="#E5E7EB" strokeDasharray="3 3" />
                <XAxis
                    dataKey="month"
                    tickFormatter={formatMonthLabel}
                    tick={{ fontSize: 8, fill: "#667085", fontWeight: 400 }}
                    axisLine={false}
                    tickLine={false}
                    angle={-90}
                    textAnchor="end"
                    dy={12}
                    tickMargin={2}
                    height={40}
                    padding={{ left: 10, right: 10 }}
                    interval={0}
                />
                <YAxis
                    tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 11, fill: "#667085", fontWeight: 400 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[domainMin, domainMax]}
                    ticks={ticks}
                    width={58}
                    tickMargin={6}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#D0D5DD", strokeWidth: 1 }} />
                <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Median Price"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ r: 4, stroke: "#3B82F6", strokeWidth: 2, fill: "white" }}
                    activeDot={{ r: 5, fill: "#FFFFFF", stroke: "#3B82F6", strokeWidth: 2 }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
