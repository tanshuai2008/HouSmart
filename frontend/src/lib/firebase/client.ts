import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

function getFirebaseConfig() {
    const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
    const authDomain = process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN;
    const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
    const appId = process.env.NEXT_PUBLIC_FIREBASE_APP_ID;

    if (!apiKey) {
        throw new Error("Missing NEXT_PUBLIC_FIREBASE_API_KEY in frontend/.env.local");
    }
    if (!authDomain || !projectId || !appId) {
        throw new Error("Missing Firebase web config in frontend/.env.local");
    }

    return { apiKey, authDomain, projectId, appId };
}

export function getFirebaseAuth() {
    const config = getFirebaseConfig();
    const app = getApps().length > 0 ? getApps()[0] : initializeApp(config);
    return getAuth(app);
}

export const googleProvider = new GoogleAuthProvider();
