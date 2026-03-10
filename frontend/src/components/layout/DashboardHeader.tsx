"use client";

import React, { useState } from "react";
import Image, { type StaticImageData } from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, ChevronDown, Search } from "lucide-react";

import logoIcon from "@/assets/dashboard/icons/logo-icon.svg";
import logoText from "@/assets/dashboard/icons/logo-text.svg";
import userAvatarImg from "@/assets/dashboard/images/user-avatar.png";
import { logout as logoutApi } from "@/lib/api/auth";
import { useAuth } from "@/providers/auth-context";

import styles from "./dashboard-header.module.css";

interface DashboardHeaderProps {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    userName?: string;
    userRole?: string;
    userAvatar?: StaticImageData | string;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
    searchValue = "1248 Highland Avenue, Seattle WA",
    onSearchChange,
    userName = "John Doe",
    userRole = "Pro Investor",
    userAvatar = userAvatarImg,
}) => {
    const router = useRouter();
    const { logout } = useAuth();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isSigningOut, setIsSigningOut] = useState(false);

    const handleSignOut = async () => {
        setIsSigningOut(true);
        try {
            await logoutApi();
        } catch {
            // Clear client auth state even if backend logout fails.
        } finally {
            logout();
            setIsProfileOpen(false);
            setIsSigningOut(false);
            router.push("/auth/login");
        }
    };

    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <Link href="/property-input" className={styles.brand} aria-label="Go to property search">
                    <Image src={logoIcon} alt="HouSmart Logo" width={32} height={32} />
                    <Image src={logoText} alt="HouSmart" width={80} height={21} className={styles.logoText} />
                </Link>

                <div className={styles.searchWrap}>
                    <Search className={styles.searchIcon} size={14} />
                    <input
                        type="text"
                        value={searchValue}
                        onChange={(event) => onSearchChange?.(event.target.value)}
                        className={styles.searchInput}
                        placeholder="Search address..."
                        readOnly={!onSearchChange}
                    />
                </div>

                <div className={styles.actions}>
                    <button type="button" className={styles.iconButton}>
                        <Bell size={16} className={styles.bellIcon} />
                        <span className={styles.notificationDot} />
                    </button>

                    <span className={styles.separator} />

                    <div className={styles.profileWrap}>
                        <button
                            type="button"
                            onClick={() => setIsProfileOpen((open) => !open)}
                            className={styles.profileButton}
                        >
                            <Image
                                src={userAvatar}
                                alt={userName}
                                width={30}
                                height={30}
                                className={styles.avatar}
                            />
                            <div className={styles.profileMeta}>
                                <span className={styles.profileName}>{userName}</span>
                                <span className={styles.profileRole}>{userRole}</span>
                            </div>
                            <ChevronDown size={12} className={styles.chevron} />
                        </button>

                        {isProfileOpen && (
                            <div className={styles.menu}>
                                <div className={styles.menuHeader}>
                                    <span className={styles.menuHeaderName}>{userName}</span>
                                    <span className={styles.menuHeaderRole}>{userRole}</span>
                                </div>

                                <div className={`${styles.menuGroup} ${styles.menuGroupBorder}`}>
                                    <button type="button" onClick={() => setIsProfileOpen(false)} className={styles.menuItem}>
                                        User Profile
                                    </button>
                                    <button type="button" onClick={() => setIsProfileOpen(false)} className={styles.menuItem}>
                                        Saved Properties
                                    </button>
                                    <button type="button" onClick={() => setIsProfileOpen(false)} className={styles.menuItem}>
                                        AI Preferences
                                    </button>
                                </div>

                                <div className={styles.menuGroup}>
                                    <button type="button" onClick={() => setIsProfileOpen(false)} className={styles.menuItem}>
                                        Account Settings
                                    </button>
                                    <button type="button" onClick={() => setIsProfileOpen(false)} className={styles.menuItem}>
                                        Billing & Plan
                                    </button>
                                    <button type="button" onClick={handleSignOut} className={styles.menuItem} disabled={isSigningOut}>
                                        {isSigningOut ? "Signing Out..." : "Sign Out"}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};
