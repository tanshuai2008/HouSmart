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
    Legend,
    Dot,
} from "recharts";
import { RevenueExpensesDataPoint } from "@/lib/mockData";

interface RevenueExpensesChartProps {
    data: RevenueExpensesDataPoint[];
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
                        {entry.name}: ${(entry.value / 1000).toFixed(1)}k
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const CustomLegend = () => (
    <div className="flex items-center gap-4 text-xs text-[#6B7280]">
        <span className="flex items-center gap-1">
            <span className="inline-block w-5 h-0.5 bg-[#3B82F6]" />
            Revenue
        </span>
        <span className="flex items-center gap-1">
            <span className="inline-block w-5 h-0.5 bg-[#12B76A]" />
            Expenses
        </span>
    </div>
);

export const RevenueExpensesChart: React.FC<RevenueExpensesChartProps> = ({
    data,
}) => {
    return (
        <div>
            <div className="flex items-center justify-end mb-2">
                <CustomLegend />
            </div>
            <ResponsiveContainer width="100%" height={180}>
                <LineChart
                    data={data}
                    margin={{ top: 5, right: 0, left: -20, bottom: 0 }}
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
                        tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                        tick={{ fontSize: 10, fill: "#9CA3AF" }}
                        axisLine={false}
                        tickLine={false}
                        domain={[3400, 5700]}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#E5E7EB", strokeWidth: 1 }} />
                    <Line
                        type="monotone"
                        dataKey="revenue"
                        name="Revenue"
                        stroke="#3B82F6"
                        strokeWidth={2}
                        dot={<Dot r={3} fill="#3B82F6" strokeWidth={0} />}
                        activeDot={{ r: 5, fill: "#3B82F6" }}
                    />
                    <Line
                        type="monotone"
                        dataKey="expenses"
                        name="Expenses"
                        stroke="#12B76A"
                        strokeWidth={2}
                        dot={<Dot r={3} fill="#12B76A" strokeWidth={0} />}
                        activeDot={{ r: 5, fill: "#12B76A" }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
