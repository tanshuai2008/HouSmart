"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { getAnalysisRunStatus } from "@/lib/api/analysis";
import { useAuth } from "@/providers/auth-context";

// Assumed asset paths
import clockIcon from "@/assets/analyze/clock.svg";
import checkCircleIcon from "@/assets/analyze/check-circle.svg";
import spinnerIcon from "@/assets/analyze/spinner.svg";
import emptyCircleIcon from "@/assets/analyze/empty-circle.svg";

const ANALYSIS_STEPS = [
    "Retrieving structured property data",
    "Evaluating surrounding market signals",
    "Computing financial performance metrics",
    "Modeling risk exposure and volatility",
    "Generating AI investment summary",
];

const PROCESSING_MESSAGES = [
    "Initializing data streams...",
    "Querying MLS databases...",
    "Running comparative market analysis...",
    "Parsing historical tax records...",
    "Aggregating neighborhood statistics...",
    "Calculating expected cap rate...",
    "Estimating cash on cash return...",
    "Reviewing zoning regulations...",
    "Analyzing regional economic trends...",
    "Stress-testing downside scenarios...",
    "Finalizing investment report...",
];

export default function AnalysisProcessingView() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { user } = useAuth();
    const runId = searchParams.get("run_id");
    const propertyId = searchParams.get("property_id");
    const address = searchParams.get("address") ?? "1248 Highland Avenue, Seattle WA";
    const [progress, setProgress] = useState(0);
    const [processingMessageIdx, setProcessingMessageIdx] = useState(0);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (runId) {
            return;
        }
        // Total duration: let's say 8 seconds to 100%
        // 8000ms / 100 = 80ms per 1%
        const interval = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 100) {
                    clearInterval(interval);
                    return 100;
                }
                return prev + 1; /* increment by 1% */
            });
        }, 80);

        return () => clearInterval(interval);
    }, [runId]);

    useEffect(() => {
        if (runId) {
            return;
        }
        if (progress === 100) {
            setTimeout(() => {
                router.push("/dashboard");
            }, 500); // slight delay at 100% before redirect
        }
    }, [progress, router, runId]);

    useEffect(() => {
        if (!runId) {
            return;
        }

        let cancelled = false;
        const poll = async () => {
            try {
                const status = await getAnalysisRunStatus(runId, user?.id);
                if (cancelled) {
                    return;
                }

                if (status.status === "completed") {
                    setProgress(100);
                    const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : "";
                    router.push(`/dashboard${query}`);
                    return;
                }

                if (status.status === "failed") {
                    setError(status.error_message || "Analysis failed. Please try again.");
                    return;
                }

                setProgress((prev) => Math.min(prev + 5, 95));
                setTimeout(poll, 1500);
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : "Failed to check analysis status");
                }
            }
        };

        void poll();
        return () => {
            cancelled = true;
        };
    }, [runId, propertyId, router, user?.id]);

    useEffect(() => {
        // Change sub-message occasionally
        const messageInterval = setInterval(() => {
            setProcessingMessageIdx((prev) => {
                return (prev + 1) % PROCESSING_MESSAGES.length;
            });
        }, 700);

        return () => clearInterval(messageInterval);
    }, []);

    // Determine which step is currently active (1 to 5)
    // 0-19% (0), 20-39% (1), 40-59% (2), 60-79% (3), 80-100% (4)
    const currentStepIndex = Math.min(Math.floor(progress / 20), 4);
    const estimatedTimeRemaining = Math.max(0, Math.ceil((100 - progress) * 80 / 1000));

    return (
        <div className="min-h-[calc(100vh-56px)] bg-white flex flex-col items-center pt-10 px-4 font-sans text-gray-900">
            <div className="w-full max-w-2xl flex flex-col gap-8">

                {/* Property Card */}
                <div className="flex items-center p-4 border border-gray-200 rounded-xl shadow-sm bg-white">
                    <div className="flex flex-col">
                        <h2 className="text-lg font-bold text-gray-900">{address}</h2>
                        <p className="text-sm text-gray-500">Queen Anne, Seattle WA</p>
                    </div>
                </div>
                {error ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        {error}
                    </div>
                ) : null}

                {/* Title and Subtitle */}
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold">Analyzing Investment Potential</h1>
                    <p className="text-gray-500">Our AI is evaluating financial, market, and risk signals.</p>
                </div>

                {/* Progress Bar Section */}
                <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-end">
                        <span className="text-xs font-bold text-gray-600 tracking-wider">RESEARCH PROGRESS</span>
                        <span className="text-lg font-bold">{progress}%</span>
                    </div>
                    <progress
                        className="analysis-progress w-full"
                        value={progress}
                        max={100}
                        aria-label="Analysis progress"
                    />
                    <div className="flex justify-end items-center gap-1 mt-1 text-xs text-gray-400">
                        <Image src={clockIcon} alt="Clock" width={12} height={12} className="opacity-50" />
                        <span>Estimated time remaining: 00:0{estimatedTimeRemaining}</span>
                    </div>
                </div>

                {/* Steps Card */}
                <div className="border border-gray-100 bg-gray-50/50 rounded-xl overflow-hidden flex flex-col shadow-sm mt-4">
                    <div className="bg-gray-50 px-6 py-4 border-b border-gray-100">
                        <span className="text-xs font-bold text-gray-500 tracking-wider">ANALYSIS STEPS</span>
                    </div>
                    <div className="flex flex-col bg-white">
                        {ANALYSIS_STEPS.map((step, idx) => {
                            const isActive = idx === currentStepIndex;
                            const isCompleted = idx < currentStepIndex;
                            const isPending = idx > currentStepIndex;

                            let IconToUse = emptyCircleIcon;
                            if (isCompleted) IconToUse = checkCircleIcon;
                            if (isActive) IconToUse = spinnerIcon;

                            return (
                                <div
                                    key={step}
                                    className={`flex items-center gap-4 px-6 py-4 border-b border-gray-50 last:border-none transition-colors duration-300 ${isActive ? 'bg-gray-50/50' : ''}`}
                                >
                                    <Image
                                        src={IconToUse}
                                        alt={isActive ? "Loading" : isCompleted ? "Done" : "Pending"}
                                        width={20}
                                        height={20}
                                        className={`${isActive ? 'animate-spin' : ''} ${isPending ? 'opacity-30' : ''}`}
                                    />
                                    <span className={`text-sm ${isCompleted || isActive ? 'text-slate-700' : 'text-slate-400'} ${isActive ? 'font-medium' : ''}`}>
                                        {step}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                    {/* Sub message footer */}
                    <div className="px-6 py-3 bg-gray-50 text-xs text-gray-400 flex items-center gap-2 italic">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                        <span>{PROCESSING_MESSAGES[processingMessageIdx]}</span>
                    </div>
                </div>

            </div>
        </div>
    );
}
