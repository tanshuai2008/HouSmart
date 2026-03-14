import { Suspense } from "react";
import AnalysisProcessingView from "@/components/analysis/AnalysisProcessingView";
import { DashboardHeader } from "@/components/layout/DashboardHeader";
import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Analyzing Property | HouSmart",
    description: "Analyzing investment potential for the selected property.",
};

export default function AnalyzePage() {
    return (
        <div className="min-h-screen bg-white">
            <DashboardHeader />
            <Suspense fallback={<div className="px-4 pt-10 text-sm text-gray-500">Loading analysis...</div>}>
                <AnalysisProcessingView />
            </Suspense>
        </div>
    );
}
