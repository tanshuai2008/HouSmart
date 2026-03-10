const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface OnboardingAnswers {
    id?: number;
    user_id: string;
    primary_role_ques: string | null;
    investment_experience_level_ques: string | null;
    investment_goal_ques: string | null;
    priorities_ranking_ques: string[];
    created_on?: string;
    updated_on?: string;
}

interface OnboardingResponse {
    answers: OnboardingAnswers | null;
}

interface OnboardingUpsertResponse {
    message: string;
    answers: OnboardingAnswers;
}

export function hasCompleteOnboardingAnswers(answers: OnboardingAnswers | null): boolean {
    if (!answers) {
        return false;
    }

    const hasRole = Boolean(answers.primary_role_ques?.trim());
    const hasExperience = Boolean(answers.investment_experience_level_ques?.trim());
    const hasGoal = Boolean(answers.investment_goal_ques?.trim());
    const hasPriorities = Array.isArray(answers.priorities_ranking_ques) && answers.priorities_ranking_ques.length === 4;

    return hasRole && hasExperience && hasGoal && hasPriorities;
}

export async function getOnboardingAnswers(userId: string): Promise<OnboardingAnswers | null> {
    const response = await fetch(`${API_BASE_URL}/onboarding/${userId}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    });

    const data = (await response.json().catch(() => ({}))) as Partial<OnboardingResponse & { detail?: string }>;
    if (!response.ok) {
        throw new Error(typeof data?.detail === "string" ? data.detail : "Failed to fetch onboarding answers");
    }

    return data.answers ?? null;
}

export async function upsertOnboardingAnswers(payload: OnboardingAnswers): Promise<OnboardingAnswers> {
    const response = await fetch(`${API_BASE_URL}/onboarding`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = (await response.json().catch(() => ({}))) as Partial<OnboardingUpsertResponse & { detail?: string }>;
    if (!response.ok) {
        throw new Error(typeof data?.detail === "string" ? data.detail : "Failed to save onboarding answers");
    }

    if (!data.answers) {
        throw new Error("Backend did not return onboarding answers");
    }

    return data.answers;
}
