const DEFAULT_BACKEND_URLS = ["http://localhost:8000", "https://housmart.onrender.com"];

function normalizeUrl(url: string): string {
    return url.trim().replace(/\/+$/, "");
}

function getConfiguredBackendUrls(): string[] {
    const configured = process.env.NEXT_PUBLIC_BACKEND_URL
        ?.split(",")
        .map(normalizeUrl)
        .filter(Boolean);

    if (configured && configured.length > 0) {
        return configured;
    }

    return DEFAULT_BACKEND_URLS;
}

export function buildBackendUrl(path: string): string {
    const [primaryUrl] = getConfiguredBackendUrls();
    return `${primaryUrl}${path}`;
}

export async function fetchWithBackendFallback(path: string, init?: RequestInit): Promise<Response> {
    const backendUrls = getConfiguredBackendUrls();
    let lastError: unknown;

    for (const baseUrl of backendUrls) {
        try {
            return await fetch(`${baseUrl}${path}`, init);
        } catch (error) {
            if (init?.signal?.aborted) {
                throw error;
            }

            lastError = error;
        }
    }

    throw lastError instanceof Error
        ? lastError
        : new Error("Unable to reach any configured backend URL");
}
