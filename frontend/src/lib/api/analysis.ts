const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface StartAnalysisResponse {
    run_id: string;
    property_id: string;
    status: string;
}

export interface AnalysisRunStatus {
    run_id: string;
    property_id: string;
    status: "running" | "completed" | "failed" | string;
    error_message?: string | null;
}

export interface DashboardPropertyPayload {
    property: Record<string, unknown> | null;
    latest_run: Record<string, unknown> | null;
    facts: Record<string, unknown> | null;
    scores: Record<string, unknown> | null;
    comparables: Record<string, unknown>[];
}

export interface RecentSearch {
    property_id: string;
    address: string;
}

export async function startPropertyAnalysis(userId: string, address: string): Promise<StartAnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/api/property/analyze`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-user-id": userId,
        },
        body: JSON.stringify({ user_id: userId, address }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Failed to start property analysis";
        throw new Error(detail);
    }

    return data as StartAnalysisResponse;
}

export async function getAnalysisRunStatus(runId: string, userId?: string): Promise<AnalysisRunStatus> {
    const response = await fetch(`${API_BASE_URL}/api/property/analyze/${runId}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            ...(userId ? { "x-user-id": userId } : {}),
        },
        cache: "no-store",
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Failed to fetch analysis status";
        throw new Error(detail);
    }

    return data as AnalysisRunStatus;
}

export async function getDashboardProperty(userId: string, propertyId: string): Promise<DashboardPropertyPayload> {
    const query = new URLSearchParams({ user_id: userId });
    const response = await fetch(`${API_BASE_URL}/api/dashboard/property/${propertyId}?${query.toString()}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "x-user-id": userId,
        },
        cache: "no-store",
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Failed to fetch dashboard property data";
        throw new Error(detail);
    }

    return data as DashboardPropertyPayload;
}

export async function getRecentSearches(userId: string, limit = 3): Promise<RecentSearch[]> {
    const query = new URLSearchParams({ user_id: userId, limit: String(limit) });
    const response = await fetch(`${API_BASE_URL}/api/property/recent-searches?${query.toString()}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "x-user-id": userId,
        },
        cache: "no-store",
    });

    const data = await response.json().catch(() => ([]));
    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Failed to fetch recent searches";
        throw new Error(detail);
    }

    return Array.isArray(data) ? (data as RecentSearch[]) : [];
}
