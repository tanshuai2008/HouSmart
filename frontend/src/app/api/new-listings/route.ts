import { NextResponse } from "next/server";
import { NewListing } from "@/types/search";

// Simulated database
const data: NewListing[] = [
    {
        id: "1",
        address: "1890 Capitol Hill Blvd",
        neighborhood: "Capitol Hill",
        city: "Seattle",
        state: "WA",
        listedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
        image: "1890-capitol-hill-blvd.png",
    },
    {
        id: "2",
        address: "3421 Fremont Ave N",
        neighborhood: "Fremont",
        city: "Seattle",
        state: "WA",
        listedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
        image: "3421-fremont-ave-n.png",
    },
    {
        id: "3",
        address: "6140 Greenwood Ave N",
        neighborhood: "Greenwood",
        city: "Seattle",
        state: "WA",
        listedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago
        image: "6140-greenwood-ave-n.png",
    },
    {
        id: "4",
        address: "2301 Beacon Ave S",
        neighborhood: "Beacon Hill",
        city: "Seattle",
        state: "WA",
        listedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(), // 6 days ago
        image: "2301-beacon-ave-s.png",
    },
    {
        id: "5",
        address: "5512 20th Ave NE",
        neighborhood: "Ravenna",
        city: "Seattle",
        state: "WA",
        listedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
        image: "5512-20th-ave-ne.png",
    }
];

export async function GET() {
    // Simulate 800ms delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    return NextResponse.json(data);
}
