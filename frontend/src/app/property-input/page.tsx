import { PropertySearchHero } from "@/components/search/PropertySearchHero";
import { DashboardHeader } from "@/components/layout/DashboardHeader";

export default function PropertyInputPage() {
    return (
        <div className="min-h-screen w-full bg-white font-sans text-gray-900">
            <DashboardHeader />

            <main className="min-h-[calc(100vh-56px)] w-full flex flex-col items-center justify-center relative px-4">
                <div className="w-full max-w-3xl transform -translate-y-12">
                    <PropertySearchHero />
                </div>

                <div className="absolute bottom-8 w-full flex justify-center pointer-events-none">
                    <p className="text-slate-400 text-[13px] font-medium flex items-center tracking-wide">
                        Press
                        <span className="mx-2 px-2 py-[2px] bg-slate-100 rounded-md text-slate-600 font-medium">
                            Enter
                        </span>
                        to search
                    </p>
                </div>
            </main>
        </div>
    );
}
