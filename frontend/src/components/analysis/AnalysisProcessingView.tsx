"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

// Assumed asset paths
import propertyImage from "@/assets/analyze/property-image.png";
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
    const [progress, setProgress] = useState(0);
    const [processingMessageIdx, setProcessingMessageIdx] = useState(0);

    useEffect(() => {
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
    }, []);

    useEffect(() => {
        if (progress === 100) {
            setTimeout(() => {
                router.push("/dashboard");
            }, 500); // slight delay at 100% before redirect
        }
    }, [progress, router]);

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
        <div className="min-h-screen bg-white flex flex-col items-center pt-16 px-4 font-sans text-gray-900">
            <div className="w-full max-w-2xl flex flex-col gap-8">

                {/* Property Card */}
                <div className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl shadow-sm bg-white">
                    <Image
                        src={propertyImage}
                        alt="Property"
                        className="w-20 h-20 rounded-lg object-cover"
                        priority
                    />
                    <div className="flex flex-col">
                        <h2 className="text-lg font-bold text-gray-900">1248 Highland Avenue, Seattle WA</h2>
                        <p className="text-sm text-gray-500">Queen Anne, Seattle WA</p>
                        <p className="text-sm text-gray-400 mt-1">Asking Price: $1,195,000</p>
                    </div>
                </div>

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
                    <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-slate-900 transition-all duration-75 ease-linear rounded-full"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
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
