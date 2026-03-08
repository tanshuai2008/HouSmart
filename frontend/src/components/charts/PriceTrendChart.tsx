"use client";
import React from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Dot,
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
    payload?: Array<{ value: number; name: string }>;
    label?: string;
}) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-[#E5E7EB] rounded-lg px-3 py-2.5 shadow-md pr-6">
                <p className="font-bold text-[#101828] text-[12px] mb-1.5">{label}</p>
                {payload.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-1.5 text-[12px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6]" />
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
    // Determine responsive rendering of the dot stroke
    const renderDot = (props: any) => {
        const { cx, cy, stroke, payload, value } = props;
        return (
            <svg x={cx - 4} y={cy - 4} width={8} height={8} fill="white" viewBox="0 0 8 8" className="overflow-visible">
                <circle cx={4} cy={4} r={4} stroke="#3B82F6" strokeWidth={2} fill="white" />
            </svg>
        );
    };

    return (
        <ResponsiveContainer width="100%" height={200}>
            <LineChart
                data={data}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
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
                    tickFormatter={(v) => `${v.toFixed(1)}%`}
                    tick={{ fontSize: 10, fill: "#9CA3AF" }}
                    axisLine={false}
                    tickLine={false}
                    domain={[97, 103]}
                    ticks={[97.5, 100.0, 102.5]}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#E5E7EB", strokeWidth: 1 }} />
                <ReferenceLine y={100} stroke="#E5E7EB" strokeWidth={1} strokeDasharray="3 3" />
                <Line
                    type="monotone"
                    dataKey="property"
                    name="Sale-to-List"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={renderDot}
                    activeDot={{ r: 5, fill: "#3B82F6" }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
