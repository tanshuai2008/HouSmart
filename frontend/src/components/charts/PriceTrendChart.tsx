"use client";
import React from "react";
import {
    CartesianGrid,
    LineChart,
    Line,
    ReferenceLine,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import type { PriceTrendDataPoint } from "@/types/marketTrends";

interface PriceTrendChartProps {
    data: PriceTrendDataPoint[];
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
                        <span className="text-[#6B7280]">Ratio:</span>
                        <span className="font-bold text-[#101828]">{entry.value.toFixed(1)}%</span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export const PriceTrendChart: React.FC<PriceTrendChartProps> = ({ data }) => {
    const values = (data || [])
        .map((point) => (typeof point?.property === "number" ? point.property : Number(point?.property)))
        .filter((value) => Number.isFinite(value)) as number[];

    const defaultMin = 97.5;
    const defaultMax = 102.5;
    const minVal = values.length ? Math.min(...values) : defaultMin;
    const maxVal = values.length ? Math.max(...values) : defaultMax;
    const range = Math.max(0.5, maxVal - minVal);
    const pad = values.length ? Math.max(0.4, range * 0.15) : 0;
    const domainMin = Math.floor((minVal - pad) * 2) / 2;
    const domainMax = Math.ceil((maxVal + pad) * 2) / 2;
    const step = Math.max(0.5, Math.round(((domainMax - domainMin) / 4) * 2) / 2);
    const ticks: number[] = [];
    for (let tick = domainMin; tick <= domainMax + 0.001; tick += step) {
        ticks.push(Number(tick.toFixed(1)));
    }

    return (
        <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data} margin={{ top: 2, right: 6, left: 0, bottom: 10 }}>
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
                    tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                    tick={{ fontSize: 11, fill: "#667085", fontWeight: 400 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[domainMin, domainMax]}
                    ticks={ticks}
                    width={56}
                    tickMargin={6}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#D0D5DD", strokeWidth: 1 }} />
                <ReferenceLine y={100} stroke="#E5E7EB" strokeWidth={1} strokeDasharray="3 3" />
                <Line
                    type="monotone"
                    dataKey="property"
                    name="Sale-to-List"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ r: 4, stroke: "#3B82F6", strokeWidth: 2, fill: "white" }}
                    activeDot={{ r: 5, fill: "#FFFFFF", stroke: "#3B82F6", strokeWidth: 2 }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
