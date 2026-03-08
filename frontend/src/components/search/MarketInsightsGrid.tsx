"use client";

import { useEffect, useState } from "react";
import { InvestmentHotspot, TrendingProperty, NewListing } from "@/types/search";
import { InsightColumn } from "./InsightColumn";
import { InsightListItem } from "./InsightListItem";

import trendingUpIcon from "@/assets/search/icons/trending-up.svg";
import thumbUpIcon from "@/assets/search/icons/thumb-up.svg";
import clockIcon from "@/assets/search/icons/clock.svg";

export const MarketInsightsGrid = () => {
    const [hotspots, setHotspots] = useState<InvestmentHotspot[]>([]);
    const [trending, setTrending] = useState<TrendingProperty[]>([]);
    const [newListings, setNewListings] = useState<NewListing[]>([]);

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAllData = async () => {
            try {
                setIsLoading(true);
                setError(null);

                const [hotspotsRes, trendingRes, listingsRes] = await Promise.all([
                    fetch("/api/investment-hotspots"),
                    fetch("/api/trending-properties"),
                    fetch("/api/new-listings"),
                ]);

                if (!hotspotsRes.ok || !trendingRes.ok || !listingsRes.ok) {
                    throw new Error("Failed to fetch insight data.");
                }

                const hotspotsData = await hotspotsRes.json();
                const trendingData = await trendingRes.json();
                const listingsData = await listingsRes.json();

                setHotspots(hotspotsData);
                setTrending(trendingData);
                setNewListings(listingsData);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Unknown error occurred");
            } finally {
                setIsLoading(false);
            }
        };

        fetchAllData();
    }, []);

    if (error) {
        return (
            <div className="w-full p-4 rounded-xl bg-red-50 text-red-600 text-center border border-red-100">
                {error}
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="w-full flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-7xl mx-auto px-4 pb-16 flex-1 overflow-y-auto custom-scrollbar">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Hot markets & hidden gems</h2>

            <div className="flex flex-col lg:flex-row gap-6">
                <InsightColumn
                    title="INVESTMENT HOTSPOTS"
                    subtitle="Best Places to Invest in 2026"
                    iconSrc={trendingUpIcon}
                >
                    {hotspots.map((item) => (
                        <InsightListItem
                            key={item.id}
                            title={`${item.city}, ${item.state}`}
                            subtitle={item.tagline}
                            imageFilename={item.image}
                            showChevron={true}
                        />
                    ))}
                </InsightColumn>

                <InsightColumn
                    title="TRENDING PROPERTIES"
                    subtitle="High demand right now"
                    iconSrc={thumbUpIcon}
                >
                    {trending.map((item) => (
                        <InsightListItem
                            key={item.id}
                            title={item.address}
                            subtitle={`${item.neighborhood}, ${item.city} ${item.state}`}
                            imageFilename={item.image}
                            showChevron={true}
                        />
                    ))}
                </InsightColumn>

                <InsightColumn
                    title="NEW LISTINGS"
                    subtitle="Recently added properties"
                    iconSrc={clockIcon}
                >
                    {newListings.map((item) => {
                        // Very simple relative time formatter for "N days ago"
                        const daysDiff = Math.floor(
                            (new Date().getTime() - new Date(item.listedAt).getTime()) / (1000 * 3600 * 24)
                        );
                        const timeStr = daysDiff === 0 ? "today" : daysDiff === 7 ? "1 week ago" : `${daysDiff} days ago`;

                        return (
                            <InsightListItem
                                key={item.id}
                                title={item.address}
                                subtitle={`${item.neighborhood}, ${item.city} ${item.state}`}
                                imageFilename={item.image}
                                rightLabel={timeStr}
                            />
                        );
                    })}
                </InsightColumn>
            </div>
        </div>
    );
};
