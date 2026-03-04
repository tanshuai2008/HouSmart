import { NextResponse } from "next/server";
import { InvestmentHotspot } from "@/types/search";

// Simulated database
const data: InvestmentHotspot[] = [
    {
        id: "1",
        city: "Seattle",
        state: "WA",
        tagline: "Tech Hub Growth",
        appreciationRate: 8.5,
        medianPrice: 850000,
        image: "seattle-wa.png",
    },
    {
        id: "2",
        city: "Portland",
        state: "OR",
        tagline: "Emerging Market",
        appreciationRate: 6.2,
        medianPrice: 550000,
        image: "portland-or.png",
    },
    {
        id: "3",
        city: "Austin",
        state: "TX",
        tagline: "High Appreciation",
        appreciationRate: 12.1,
        medianPrice: 620000,
        image: "austin-tx.png",
    },
    {
        id: "4",
        city: "Denver",
        state: "CO",
        tagline: "Migration Hotspot",
        appreciationRate: 7.8,
        medianPrice: 605000,
        image: "denver-co.png",
    },
    {
        id: "5",
        city: "Nashville",
        state: "TN",
        tagline: "Music City Boom",
        appreciationRate: 10.5,
        medianPrice: 480000,
        image: "nashville-tn.png",
    }
];

export async function GET() {
    // Simulate 800ms delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    return NextResponse.json(data);
}
