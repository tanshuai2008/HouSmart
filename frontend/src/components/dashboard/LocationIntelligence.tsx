"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import Image, { type StaticImageData } from "next/image";
import { ScoreBar } from "@/components/ui/ScoreBar";

declare global {
    interface Window {
        google?: unknown;
    }
}

interface LocationIntelligenceProps {
    scores: Array<{
        label: string;
        filledBars: number;
        tone: "positive" | "warning" | "negative";
        icon: StaticImageData | string;
        tooltipText?: string;
    }>;
    radius?: string;
    mapAddress?: string;
    latitude?: number | null;
    longitude?: number | null;
}

export const LocationIntelligence: React.FC<LocationIntelligenceProps> = ({
    scores,
    radius = "0.5 mi radius",
    mapAddress,
    latitude,
    longitude,
}) => {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const [mapsReady, setMapsReady] = useState(() => {
        if (typeof window === "undefined" || !window.google) {
            return false;
        }
        const candidate = window.google as { maps?: unknown };
        return Boolean(candidate.maps);
    });
    const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    const hasCoordinates = typeof latitude === "number" && typeof longitude === "number";
    const hasAddress = Boolean(mapAddress?.trim());
    const mapQuery = hasCoordinates ? `${latitude},${longitude}` : (mapAddress?.trim() ?? "");
    const canUseJsApi = Boolean(googleMapsApiKey);

    const embedSrc = mapQuery
        ? `https://www.google.com/maps?q=${encodeURIComponent(mapQuery)}&z=15&output=embed`
        : null;
    const openInMapsHref = mapQuery
        ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapQuery)}`
        : null;

    useEffect(() => {
        if (!canUseJsApi) {
            return;
        }

        const loadedGoogle = window.google as { maps?: unknown } | undefined;
        if (loadedGoogle?.maps) {
            return;
        }

        const scriptId = "google-maps-js-api";
        const existingScript = document.getElementById(scriptId) as HTMLScriptElement | null;
        if (existingScript) {
            existingScript.addEventListener("load", () => setMapsReady(true));
            return;
        }

        const script = document.createElement("script");
        script.id = scriptId;
        script.src = `https://maps.googleapis.com/maps/api/js?key=${googleMapsApiKey}`;
        script.async = true;
        script.defer = true;
        script.onload = () => setMapsReady(true);
        document.head.appendChild(script);
    }, [canUseJsApi, googleMapsApiKey]);

    const fallbackCenter = useMemo(() => ({ lat: 47.6205, lng: -122.3493 }), []);

    useEffect(() => {
        if (!canUseJsApi || !mapsReady || !mapContainerRef.current || !window.google?.maps) {
            return;
        }

        const loadedGoogle = window.google as { maps?: unknown } | undefined;
        if (!loadedGoogle?.maps) {
            return;
        }
        const gm = loadedGoogle.maps as {
            Map: new (element: HTMLDivElement, options: Record<string, unknown>) => {
                setCenter: (coords: { lat: number; lng: number }) => void;
            };
            Marker: new (options: { map: unknown; position: { lat: number; lng: number } }) => unknown;
            Geocoder: new () => {
                geocode: (
                    request: { address: string },
                    callback: (results: unknown, status: string) => void
                ) => void;
            };
            MapTypeControlStyle: { HORIZONTAL_BAR: unknown };
            ControlPosition: { LEFT_BOTTOM: unknown; RIGHT_BOTTOM: unknown };
        };
        const center = hasCoordinates
            ? { lat: Number(latitude), lng: Number(longitude) }
            : fallbackCenter;

        const mapOptions: Record<string, unknown> = {
            center,
            zoom: 15,
            mapTypeControl: true,
            mapTypeControlOptions: {
                style: gm.MapTypeControlStyle.HORIZONTAL_BAR,
                position: gm.ControlPosition.LEFT_BOTTOM,
            },
            zoomControl: true,
            zoomControlOptions: {
                position: gm.ControlPosition.RIGHT_BOTTOM,
            },
            streetViewControl: false,
            fullscreenControl: false,
            gestureHandling: "greedy",
        };

        mapOptions.cameraControl = true;
        mapOptions.cameraControlOptions = {
            position: gm.ControlPosition.RIGHT_BOTTOM,
        };

        const map = new gm.Map(mapContainerRef.current, mapOptions);
        const setMarker = (lat: number, lng: number) => {
            new gm.Marker({
                map,
                position: { lat, lng },
            });
            map.setCenter({ lat, lng });
        };

        if (hasCoordinates) {
            setMarker(Number(latitude), Number(longitude));
            return;
        }

        if (!hasAddress) {
            return;
        }

        const geocoder = new gm.Geocoder();
        geocoder.geocode({ address: mapAddress?.trim() ?? "" }, (results: unknown, status: string) => {
            if (!Array.isArray(results)) {
                return;
            }
            const first = results[0] as { geometry?: { location?: { lat: () => number; lng: () => number } } } | undefined;
            if (status !== "OK" || !first?.geometry?.location) {
                return;
            }
            const loc = first.geometry.location;
            setMarker(loc.lat(), loc.lng());
        });
    }, [canUseJsApi, fallbackCenter, hasAddress, hasCoordinates, latitude, longitude, mapAddress, mapsReady]);

    return (
        <div className="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-visible">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#F3F4F6]">
                <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
                    Location Intelligence
                </span>
                <span className="text-[10px] text-[#9CA3AF]">{radius}</span>
            </div>

            {/* Map */}
            <div className="location-map-surface relative mx-3 mt-3 mb-3 rounded-xl overflow-hidden aspect-square bg-[#F3F4F6] border border-[#E5E7EB]">
                {canUseJsApi ? (
                    <>
                        <div ref={mapContainerRef} className="w-full h-full" />
                        {openInMapsHref && (
                            <a
                                href={openInMapsHref}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="absolute left-3 top-3 inline-flex items-center rounded-md bg-white px-3 py-2 text-[10px] font-semibold text-[#175CD3] shadow-sm border border-[#E5E7EB] hover:bg-[#F8FAFC]"
                            >
                                Open in Maps
                            </a>
                        )}
                    </>
                ) : embedSrc ? (
                    <>
                        <iframe
                            title="Property location map"
                            src={embedSrc}
                            className="w-full h-full border-0"
                            loading="lazy"
                            referrerPolicy="no-referrer-when-downgrade"
                            allowFullScreen
                        />
                        {openInMapsHref && (
                            <a
                                href={openInMapsHref}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="absolute left-3 top-3 inline-flex items-center rounded-md bg-white px-3 py-2 text-[10px] font-semibold text-[#175CD3] shadow-sm border border-[#E5E7EB] hover:bg-[#F8FAFC]"
                            >
                                Open in Maps
                            </a>
                        )}
                    </>
                ) : (
                    <div className="h-full w-full" aria-label={hasAddress ? "Loading map" : "Map unavailable"} />
                )}
            </div>

            {/* Score rows — with dividers between each */}
            <div className="px-4 pb-3">
                {scores.map((score, idx) => (
                    <div key={score.label}>
                        <div className="flex items-center justify-between py-3">
                            <div className="flex items-center gap-2.5">
                                <div className="relative group">
                                    <Image
                                        src={score.icon}
                                        alt={score.label}
                                        width={14}
                                        height={14}
                                        className="shrink-0 opacity-70 cursor-help"
                                    />
                                    {score.tooltipText && (
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-[380px] max-w-[calc(100vw-2rem)] hidden group-hover:block whitespace-normal break-words text-left bg-white text-[#101828] font-medium text-[12px] leading-snug p-3 rounded-lg border border-[#E5E7EB] shadow-[0px_4px_16px_rgba(0,0,0,0.08)] z-[60]">
                                            {score.tooltipText}
                                        </div>
                                    )}
                                </div>
                                <span className="text-[12px] font-medium text-[#374151]">{score.label}</span>
                            </div>
                            <ScoreBar filledBars={score.filledBars} tone={score.tone} />
                        </div>
                        {idx < scores.length - 1 && (
                            <div className="h-px bg-[#F3F4F6]" />
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
