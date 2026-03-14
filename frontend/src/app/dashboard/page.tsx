import { Suspense } from "react";
import type { Metadata } from "next";
import DashboardPageView from "@/components/dashboard/DashboardPageView";

export const metadata: Metadata = {
    title: "Dashboard | HouSmart",
    description: "Property investment dashboard.",
};

export default function DashboardPage() {
    return (
        <Suspense fallback={<div className="px-4 pt-10 text-sm text-gray-500">Loading dashboard...</div>}>
            <DashboardPageView />
        </Suspense>
    );
}
