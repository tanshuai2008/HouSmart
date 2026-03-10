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
            <AnalysisProcessingView />
        </div>
    );
}
