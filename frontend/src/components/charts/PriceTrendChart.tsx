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
} from "recharts";
import { PriceTrendDataPoint } from "@/types/marketTrends";

interface PriceTrendChartProps {
    data: PriceTrendDataPoint[];
}

const CustomTooltip = ({
    active,
    payload,
    label,
}: {
    active?: boolean;
    payload?: Array<{ value: unknown; name: string }>;
    label?: string;
}) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-[#E5E7EB] rounded-lg px-3 py-2.5 shadow-md pr-6">
                <p className="font-bold text-[#101828] text-[12px] mb-1.5">{label}</p>
                {payload.map((entry) => (
                    (() => {
                        const num = typeof entry.value === "number" ? entry.value : Number(entry.value);
                        if (!Number.isFinite(num)) return null;
                        return (
                    <div key={entry.name} className="flex items-center gap-1.5 text-[12px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6]" />
                        <span className="text-[#6B7280]">Ratio:</span>
                        <span className="font-bold text-[#101828]">{num.toFixed(1)}%</span>
                    </div>
                        );
                    })()
                ))}
            </div>
        );
    }
    return null;
};

export const PriceTrendChart: React.FC<PriceTrendChartProps> = ({ data }) => {
    const values = (data || [])
        .map((d) => (typeof d?.property === "number" ? d.property : Number(d?.property)))
        .filter((v) => Number.isFinite(v)) as number[];

    const defaultMin = 97;
    const defaultMax = 103;
    const minVal = values.length ? Math.min(...values) : defaultMin;
    const maxVal = values.length ? Math.max(...values) : defaultMax;
    const pad = values.length ? Math.max(0.2, (maxVal - minVal) * 0.1) : 0;
    const domainMin = Math.floor((minVal - pad) * 10) / 10;
    const domainMax = Math.ceil((maxVal + pad) * 10) / 10;
    const mid = Math.round(((domainMin + domainMax) / 2) * 10) / 10;
    const ticks = [domainMin, mid, domainMax];

    const renderDot = (props: { cx?: number; cy?: number }) => {
        const { cx, cy } = props;
        if (typeof cx !== "number" || typeof cy !== "number") return null;
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
                    tickFormatter={(v) => {
                        const num = typeof v === "number" ? v : Number(v);
                        if (!Number.isFinite(num)) return "";
                        return `${num.toFixed(1)}%`;
                    }}
                    tick={{ fontSize: 10, fill: "#9CA3AF" }}
                    axisLine={false}
                    tickLine={false}
                    domain={[domainMin, domainMax]}
                    ticks={ticks}
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
