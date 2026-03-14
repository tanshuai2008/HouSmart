"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signInWithPopup } from "firebase/auth";
import type { AuthError } from "firebase/auth";

import { Button } from "../ui/Button";
import { Divider } from "../ui/Divider";
import { Input } from "../ui/Input";
import { loginWithGoogleIdToken, registerWithEmail } from "@/lib/api/auth";
import { getFirebaseAuth, googleProvider } from "@/lib/firebase/client";
import { useAuth } from "@/providers/auth-context";

import googleIcon from "@/assets/auth/social-google.svg";
import microsoftIcon from "@/assets/auth/social-microsoft.svg";
import appleIcon from "@/assets/auth/social-apple.svg";
import emailIcon from "@/assets/icons/envelope.svg";
import passwordIcon from "@/assets/icons/lock.svg";

import styles from "./auth-form.module.css";

export const RegistrationForm = () => {
    const router = useRouter();
    const { setAuthenticatedUser } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);

    const isFirebaseAuthError = (err: unknown): err is AuthError => {
        return typeof err === "object" && err !== null && "code" in err;
    };

    const getGoogleSignInError = (err: unknown) => {
        if (isFirebaseAuthError(err)) {
            if (err.code === "auth/unauthorized-domain") {
                return "Google sign-in is not enabled for this deployment domain yet. Add this site to Firebase Authentication -> Settings -> Authorized domains.";
            }

            if (err.code === "auth/popup-blocked") {
                return "The sign-in popup was blocked by the browser. Allow popups and try again.";
            }
        }

        return err instanceof Error ? err.message : "Google sign in failed";
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError("");
        setIsSubmitting(true);

        try {
            const response = await registerWithEmail(email, password);
            setAuthenticatedUser(response.user);
            router.push("/auth/setup/role");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to sign up");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setError("");
        setIsGoogleSubmitting(true);
        try {
            const firebaseAuth = getFirebaseAuth();
            const credential = await signInWithPopup(firebaseAuth, googleProvider);
            const idToken = await credential.user.getIdToken();
            const response = await loginWithGoogleIdToken(idToken);
            setAuthenticatedUser(response.user);
            router.push("/auth/setup/role");
        } catch (err) {
            setError(getGoogleSignInError(err));
        } finally {
            setIsGoogleSubmitting(false);
        }
    };

    return (
        <section className={`${styles.formRoot} ${styles.formRootSignup}`}>
            <header className={styles.header}>
                <h2 className={`${styles.title} ${styles.titleSignup}`}>Create an account</h2>
                <p className={`${styles.subtitle} ${styles.subtitleSignup}`}>
                    Enter your details to get started with Housmart.
                </p>
            </header>

            <div className={styles.stack}>
                <div className={styles.socialStack}>
                    <Button variant="outline" type="button" className={styles.socialButton} onClick={handleGoogleSignIn} disabled={isGoogleSubmitting}>
                        <Image src={googleIcon} alt="Google" width={20} height={20} />
                        {isGoogleSubmitting ? "Connecting..." : "Continue with Google"}
                    </Button>
                    <Button variant="outline" type="button" className={styles.socialButton}>
                        <Image src={microsoftIcon} alt="Microsoft" width={20} height={20} />
                        Continue with Microsoft
                    </Button>
                    <Button variant="outline" type="button" className={styles.socialButton}>
                        <Image src={appleIcon} alt="Apple" width={18} height={20} />
                        Continue with Apple
                    </Button>
                </div>

                <Divider className="my-1" />

                <form onSubmit={handleSubmit} className={styles.form}>
                    <div className={styles.fieldGroup}>
                        <label className={styles.label} htmlFor="signup-email">
                            EMAIL
                        </label>
                        <Input
                            id="signup-email"
                            type="email"
                            autoComplete="email"
                            placeholder="name@company.com"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            icon={<Image src={emailIcon} alt="" width={18} height={18} className={styles.icon} aria-hidden="true" />}
                            className={styles.input}
                            required
                        />
                    </div>

                    <div className={styles.fieldGroup}>
                        <label className={styles.label} htmlFor="signup-password">
                            PASSWORD
                        </label>
                        <Input
                            id="signup-password"
                            type="password"
                            autoComplete="new-password"
                            placeholder="********"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            icon={<Image src={passwordIcon} alt="" width={18} height={18} className={styles.icon} aria-hidden="true" />}
                            className={styles.input}
                            required
                        />
                        <p className={styles.passwordHint}>Must be at least 8 characters long.</p>
                        {error && <p className={styles.errorText}>{error}</p>}
                    </div>

                    <Button type="submit" className={`${styles.submitButton} ${styles.submitSignup}`}>
                        {isSubmitting ? "Signing Up..." : "Sign Up"}
                    </Button>

                    <div className={`${styles.switchAuthRow} ${styles.switchAuthRowSignup}`}>
                        Already have an account?
                        <Link href="/auth/login" className={`${styles.switchAuthLink} ${styles.switchAuthLinkSignup}`}>
                            Log in
                        </Link>
                    </div>
                </form>

                <footer className={`${styles.footerLinks} ${styles.footerLinksSignup}`}>
                    <span className={styles.footerText}>ENTERPRISE V2.4</span>
                    <span className={styles.footerText}>SECURED</span>
                    <a
                        href="#"
                        className={styles.footerLink}
                        onClick={(event) => event.preventDefault()}
                    >
                        HELP
                    </a>
                </footer>
            </div>
        </section>
    );
};
