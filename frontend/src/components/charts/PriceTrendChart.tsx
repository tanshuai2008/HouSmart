"use client";
import React from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Cell,
} from "recharts";
import { PriceTrendDataPoint } from "@/lib/mockData";

interface PriceTrendChartProps {
    data: PriceTrendDataPoint[];
}

const CustomTooltip = ({
    active,
    payload,
    label,
}: {
    active?: boolean;
    payload?: Array<{ value: number; name: string; color: string }>;
    label?: string;
}) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-[#E5E7EB] rounded-lg p-2 shadow-lg text-xs">
                <p className="font-semibold text-[#101828] mb-1">{label}</p>
                {payload.map((entry) => (
                    <p key={entry.name} style={{ color: entry.color }}>
                        {entry.name}: {entry.value > 0 ? "+" : ""}
                        {entry.value}%
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

export const PriceTrendChart: React.FC<PriceTrendChartProps> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={200}>
            <BarChart
                data={data}
                margin={{ top: 10, right: 0, left: -20, bottom: 0 }}
                barCategoryGap="35%"
            >
                <CartesianGrid
                    vertical={false}
                    strokeDasharray="3 3"
                    stroke="#F3F4F6"
                />
                <XAxis
                    dataKey="month"
                    tick={{ fontSize: 10, fill: "#9CA3AF" }}
                    axisLine={false}
                    tickLine={false}
                />
                <YAxis
                    tickFormatter={(v) => `${v}%`}
                    tick={{ fontSize: 10, fill: "#9CA3AF" }}
                    axisLine={false}
                    tickLine={false}
                    domain={[-1.2, 3.2]}
                    ticks={[-0.95, 0, 0.95, 1.9, 2.85]}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.04)" }} />
                <ReferenceLine y={0} stroke="#E5E7EB" strokeWidth={1} />
                <Bar dataKey="property" name="Property" radius={[3, 3, 0, 0]}>
                    {data.map((entry, index) => (
                        <Cell
                            key={`cell-${index}`}
                            fill={entry.property < 0 ? "#12B76A" : "#3B82F6"}
                        />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};
