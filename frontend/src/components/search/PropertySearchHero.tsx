"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import searchIcon from "@/assets/search/icons/search.svg";
import locationIcon from "@/assets/search/icons/location-pin.svg";
import { useAuth } from "@/providers/auth-context";
import { startPropertyAnalysis } from "@/lib/api/analysis";

export const PropertySearchHero = () => {
    const router = useRouter();
    const { user } = useAuth();
    const [address, setAddress] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const submit = async (nextAddress?: string) => {
        const finalAddress = (nextAddress ?? address).trim();
        if (!finalAddress || isSubmitting) {
            return;
        }
        if (!user?.id) {
            setError("Please log in to analyze a property.");
            return;
        }

        setIsSubmitting(true);
        setError(null);
        try {
            const result = await startPropertyAnalysis(user.id, finalAddress);
            const query = new URLSearchParams({
                run_id: result.run_id,
                property_id: result.property_id,
                address: finalAddress,
            });
            router.push(`/analyze?${query.toString()}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to start analysis");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex flex-col items-center pt-10 pb-6 w-full max-w-3xl mx-auto px-4">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6 text-center">
                Which property are we analyzing?
            </h1>

            <div className="w-full relative group shadow-[0_4px_16px_rgba(0,0,0,0.04)] rounded-xl transition-shadow hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Image src={searchIcon} alt="Search" width={20} height={20} className="text-gray-400" />
                </div>
                <input
                    type="text"
                    placeholder="Enter full property address..."
                    className="block w-full pl-12 pr-4 py-4 border border-gray-100 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            void submit();
                        }
                    }}
                />
            </div>
            {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

            <div className="w-full mt-6">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    RECENT SEARCHES
                </h2>

                <div
                    className="w-full flex items-center p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer shadow-[0_2px_8px_rgba(0,0,0,0.02)]"
                    onClick={() => void submit("1248 Highland Avenue, Seattle WA")}
                >
                    <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center mr-3 border border-gray-100">
                        <Image src={locationIcon} alt="Location" width={16} height={16} />
                    </div>
                    <span className="text-sm text-gray-700 font-medium">
                        1248 Highland Avenue, Seattle WA
                    </span>
                </div>
                <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => void submit()}
                    className="mt-4 inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isSubmitting ? "Starting..." : "Search"}
                </button>
            </div>
        </div>
    );
};
