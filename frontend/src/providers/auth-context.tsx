"use client";

import React, { createContext, ReactNode, useContext, useMemo, useState } from "react";
import type { AuthUser } from "@/lib/api/auth";

interface AuthContextType {
    user: AuthUser | null;
    isAuthenticated: boolean;
    isHydrated: boolean;
    setAuthenticatedUser: (nextUser: AuthUser) => void;
    logout: () => void;
}

const AUTH_USER_KEY = "housmart.auth.user";
const AUTH_COOKIE_KEY = "housmart_auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function setAuthCookie(value: "1" | "0") {
    document.cookie = `${AUTH_COOKIE_KEY}=${value}; Path=/; Max-Age=${value === "1" ? 86400 : 0}; SameSite=Lax`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(() => {
        if (typeof window === "undefined") {
            return null;
        }

        const serialized = window.localStorage.getItem(AUTH_USER_KEY);
        if (!serialized) {
            return null;
        }

        try {
            return JSON.parse(serialized) as AuthUser;
        } catch {
            window.localStorage.removeItem(AUTH_USER_KEY);
            return null;
        }
    });
    const isHydrated = true;

    const setAuthenticatedUser = (nextUser: AuthUser) => {
        setUser(nextUser);
        window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(nextUser));
        setAuthCookie("1");
    };

    const logout = () => {
        setUser(null);
        window.localStorage.removeItem(AUTH_USER_KEY);
        setAuthCookie("0");
    };

    const value = useMemo(
        () => ({
            user,
            isAuthenticated: user !== null,
            isHydrated,
            setAuthenticatedUser,
            logout,
        }),
        [user, isHydrated]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
