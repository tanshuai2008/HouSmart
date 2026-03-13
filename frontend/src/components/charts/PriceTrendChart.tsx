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
import type { DotProps } from "recharts";
import type { PriceTrendDataPoint } from "@/app/dashboard/dashboard-data";

interface PriceTrendChartProps {
    data: PriceTrendDataPoint[];
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
    const renderDot = ({ cx, cy }: DotProps) => {
        if (typeof cx !== "number" || typeof cy !== "number") return null;
        return <circle cx={cx} cy={cy} r={4} stroke="#3B82F6" strokeWidth={2} fill="white" />;
    };

    const horizontalCoordinatesGenerator = ({ yAxis }: { yAxis?: { ticks?: Array<{ coordinate: number }> } }) =>
        yAxis?.ticks?.map((tick) => tick.coordinate) ?? [];

    return (
        <ResponsiveContainer width="100%" height={213}>
            <LineChart data={data} margin={{ top: 2, right: 6, left: 0, bottom: 16 }}>
                <CartesianGrid
                    vertical={false}
                    stroke="#E5E7EB"
                    strokeDasharray="3 3"
                    horizontalCoordinatesGenerator={horizontalCoordinatesGenerator}
                />
                <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: "#667085", fontWeight: 400 }}
                    axisLine={false}
                    tickLine={false}
                    dy={8}
                    tickMargin={8}
                    height={28}
                    padding={{ left: 10, right: 10 }}
                />
                <YAxis
                    tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                    tick={{ fontSize: 11, fill: "#667085", fontWeight: 400 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[97.3, 102.7]}
                    ticks={[97.5, 100.0, 102.5]}
                    width={56}
                    tickMargin={6}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#D0D5DD", strokeWidth: 1 }} />
                <Line
                    type="monotone"
                    dataKey="property"
                    name="Sale-to-List"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={renderDot}
                    activeDot={{ r: 5, fill: "#FFFFFF", stroke: "#3B82F6", strokeWidth: 2 }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
