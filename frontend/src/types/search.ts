export interface InvestmentHotspot {
    id: string;
    city: string;
    state: string;
    tagline: string;
    appreciationRate: number;
    medianPrice: number;
    image: string; // Add image path to be uniform with other lists
}

export interface TrendingProperty {
    id: string;
    address: string;
    neighborhood: string;
    city: string;
    state: string;
    demandScore: number;
    image: string;
}

export interface NewListing {
    id: string;
    address: string;
    neighborhood: string;
    city: string;
    state: string;
    listedAt: string;
    image: string;
}
