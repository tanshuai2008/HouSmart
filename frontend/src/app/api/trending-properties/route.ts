import { NextResponse } from "next/server";
import { TrendingProperty } from "@/types/search";

// Simulated database
const data: TrendingProperty[] = [
    {
        id: "1",
        address: "1425 Queen Anne Ave N",
        neighborhood: "Queen Anne",
        city: "Seattle",
        state: "WA",
        demandScore: 95,
        image: "1425-queen-anne-ave-n.png",
    },
    {
        id: "2",
        address: "2847 NE Pacific St",
        neighborhood: "University District",
        city: "Seattle",
        state: "WA",
        demandScore: 88,
        image: "2847-ne-pacific-st.png",
    },
    {
        id: "3",
        address: "5012 Ballard Ave NW",
        neighborhood: "Ballard",
        city: "Seattle",
        state: "WA",
        demandScore: 92,
        image: "5012-ballard-ave-nw.png",
    },
    {
        id: "4",
        address: "4021 Alaska St SW",
        neighborhood: "West Seattle",
        city: "Seattle",
        state: "WA",
        demandScore: 85,
        image: "4021-alaska-st-sw.png",
    },
    {
        id: "5",
        address: "3812 Rainier Ave S",
        neighborhood: "Columbia City",
        city: "Seattle",
        state: "WA",
        demandScore: 81,
        image: "3812-rainier-ave-s.png",
    }
];

export async function GET() {
    // Simulate 800ms delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    return NextResponse.json(data);
}
