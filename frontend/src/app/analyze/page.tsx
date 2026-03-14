import AnalysisProcessingView from "@/components/analysis/AnalysisProcessingView";
import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Analyzing Property | HouSmart",
    description: "Analyzing investment potential for the selected property.",
};

export default function AnalyzePage() {
    return <AnalysisProcessingView />;
}
