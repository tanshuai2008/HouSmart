export interface AuthUser {
    id?: string;
    firebase_uid?: string;
    email: string;
    auth_provider?: string;
    onboarding_complete?: boolean;
    created_on?: string;
    last_login?: string;
}

interface AuthResponse {
    message: string;
    user: AuthUser;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function postJson<T>(path: string, body: Record<string, unknown>): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Request failed";
        throw new Error(detail);
    }

    return data as T;
}

export async function registerWithEmail(email: string, password: string): Promise<AuthResponse> {
    return postJson<AuthResponse>("/auth/register", { email, password });
}

export async function loginWithEmail(email: string, password: string): Promise<AuthResponse> {
    return postJson<AuthResponse>("/auth/login", { email, password });
}

export async function logout(): Promise<{ message: string }> {
    return postJson<{ message: string }>("/auth/logout", {});
}

export async function loginWithGoogleIdToken(idToken: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${idToken}`,
        },
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Google login failed";
        throw new Error(detail);
    }

    return data as AuthResponse;
}
