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
} from "recharts";
import { RevenueExpensesDataPoint } from "@/types/marketTrends";

interface RevenueExpensesChartProps {
    data: RevenueExpensesDataPoint[];
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
                {payload.map((entry) => {
                    const num = typeof entry.value === "number" ? entry.value : Number(entry.value);
                    if (!Number.isFinite(num)) return null;
                    return (
                        <div key={entry.name} className="flex items-center gap-1.5 text-[12px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6]" />
                            <span className="text-[#6B7280]">Median Price:</span>
                            <span className="font-bold text-[#101828]">${num.toLocaleString()}</span>
                        </div>
                    );
                })}
            </div>
        );
    }
    return null;
};

function niceStep(rawStep: number): number {
    if (!Number.isFinite(rawStep) || rawStep <= 0) return 1;
    const exponent = Math.floor(Math.log10(rawStep));
    const base = Math.pow(10, exponent);
    const fraction = rawStep / base;
    if (fraction <= 1) return 1 * base;
    if (fraction <= 2) return 2 * base;
    if (fraction <= 5) return 5 * base;
    return 10 * base;
}

export const RevenueExpensesChart: React.FC<RevenueExpensesChartProps> = ({
    data,
}) => {
    const values = (data || [])
        .map((d) => (typeof d?.revenue === "number" ? d.revenue : Number(d?.revenue)))
        .filter((v) => Number.isFinite(v)) as number[];

    const hasData = values.length > 0;

    let domain: [number | "auto", number | "auto"] = ["auto", "auto"];
    let ticks: number[] | undefined = undefined;

    if (hasData) {
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = Math.max(1, maxVal - minVal);
        const pad = range * 0.08;

        const rawMin = minVal - pad;
        const rawMax = maxVal + pad;
        const step = niceStep((rawMax - rawMin) / 4);
        const domainMin = Math.floor(rawMin / step) * step;
        const domainMax = Math.ceil(rawMax / step) * step;

        const tickValues: number[] = [];
        for (let i = 0; i < 5; i++) {
            tickValues.push(domainMin + step * i);
        }
        if (tickValues[tickValues.length - 1] < domainMax) tickValues.push(domainMax);

        domain = [domainMin, domainMax];
        ticks = tickValues;
    }

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
                        return `$${(num / 1000).toFixed(0)}k`;
                    }}
                    tick={{ fontSize: 10, fill: "#9CA3AF" }}
                    axisLine={false}
                    tickLine={false}
                    domain={domain}
                    ticks={ticks}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#E5E7EB", strokeWidth: 1 }} />
                <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Median Price"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={renderDot}
                    activeDot={{ r: 5, fill: "#3B82F6" }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
};
