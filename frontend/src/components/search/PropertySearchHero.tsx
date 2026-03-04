"use client";


import Image from "next/image";
import searchIcon from "@/assets/icons/search.svg";
import locationIcon from "@/assets/icons/location-pin.svg";

export const PropertySearchHero = () => {
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
                />
            </div>

            <div className="w-full mt-6">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    RECENT SEARCHES
                </h2>

                <div className="w-full flex items-center p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
                    <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center mr-3 border border-gray-100">
                        <Image src={locationIcon} alt="Location" width={16} height={16} />
                    </div>
                    <span className="text-sm text-gray-700 font-medium">
                        1248 Highland Avenue, Seattle WA
                    </span>
                </div>
            </div>
        </div>
    );
};
