import { PropertySearchHero } from "@/components/search/PropertySearchHero";
import { MarketInsightsGrid } from "@/components/search/MarketInsightsGrid";

export default function PropertyInputPage() {
    return (
        <main className="h-screen overflow-hidden bg-white font-sans text-gray-900 flex flex-col">
            <PropertySearchHero />
            <MarketInsightsGrid />

            <div className="fixed bottom-8 w-full flex justify-center pointer-events-none">
                <p className="text-slate-400 text-[13px] font-medium flex items-center tracking-wide">
                    Press
                    <span className="mx-2 px-2 py-[2px] bg-slate-100 rounded-md text-slate-600 font-medium">
                        Enter
                    </span>
                    to search
                </p>
            </div>
        </main>
    );
}
