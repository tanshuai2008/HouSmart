"use client";

import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Divider } from "../ui/Divider";
import Image from "next/image";
import Link from "next/link";

import googleIcon from "@/assets/auth/login/google-icon.svg";
import microsoftIcon from "@/assets/auth/login/microsoft-icon.svg";
import appleIcon from "@/assets/auth/login/apple-icon.svg";
import mailIcon from "@/assets/auth/login/mail-icon.svg";
import lockIcon from "@/assets/auth/login/lock-icon.svg";

export const LoginForm = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log("Login submitted", { email, password });
    };

    return (
        <div className="w-full flex flex-col pt-8 lg:pt-12">
            {/* Header */}
            <div className="flex flex-col items-center gap-2 mb-8">
                <h2 className="font-bold text-[28px] leading-[36px] tracking-tight text-center text-[#10151C]">
                    Welcome back
                </h2>
                <p className="font-normal text-[14px] leading-[20px] text-center text-[#71717A]">
                    Enter your credentials to access your workspace.
                </p>
            </div>

            {/* Form Container */}
            <div className="w-full mt-2 flex flex-col gap-5">
                {/* SSO Buttons */}
                <div className="flex flex-col gap-3">
                    <Button
                        variant="outline"
                        type="button"
                        className="w-full h-[46px] rounded-xl border border-[#E4E4E7] flex justify-center items-center gap-3 text-[#3F3F46] font-semibold text-[15px] hover:bg-[#F4F4F5]"
                    >
                        <Image src={googleIcon} alt="Google" width={20} height={20} />
                        Continue with Google
                    </Button>
                    <Button
                        variant="outline"
                        type="button"
                        className="w-full h-[46px] rounded-xl border border-[#E4E4E7] flex justify-center items-center gap-3 text-[#3F3F46] font-semibold text-[15px] hover:bg-[#F4F4F5]"
                    >
                        <Image src={microsoftIcon} alt="Microsoft" width={20} height={20} />
                        Continue with Microsoft
                    </Button>
                    <Button
                        variant="outline"
                        type="button"
                        className="w-full h-[46px] rounded-xl border border-[#E4E4E7] flex justify-center items-center gap-3 text-[#3F3F46] font-semibold text-[15px] hover:bg-[#F4F4F5]"
                    >
                        <Image src={appleIcon} alt="Apple" width={18} height={20} />
                        Continue with Apple
                    </Button>
                </div>

                <Divider className="my-1" />

                <form onSubmit={handleSubmit} className="flex flex-col w-full gap-5">
                    {/* Email Field */}
                    <div className="flex flex-col gap-2">
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.05em] uppercase text-[#71717A] ml-1">
                            EMAIL
                        </label>
                        <Input
                            type="email"
                            placeholder="name@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            icon={<Image src={mailIcon} alt="Email" width={18} height={18} className="opacity-60" />}
                            className="h-[46px] rounded-xl border-[#E4E4E7]"
                            required
                        />
                    </div>

                    {/* Password Field */}
                    <div className="flex flex-col gap-2 mb-1">
                        <div className="flex justify-between items-center w-full px-1">
                            <label className="font-bold text-[11px] leading-[16px] tracking-[0.05em] uppercase text-[#71717A]">
                                PASSWORD
                            </label>
                            <Link
                                href="/forgot-password"
                                className="font-medium text-[12px] leading-[16px] text-center text-[#71717A] hover:text-[#10151C] transition-colors"
                            >
                                Forgot?
                            </Link>
                        </div>
                        <Input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            icon={<Image src={lockIcon} alt="Password" width={18} height={18} className="opacity-60" />}
                            className="h-[46px] rounded-xl border-[#E4E4E7]"
                            required
                        />
                    </div>

                    <Button type="submit" className="w-full h-[46px] rounded-xl bg-[#10151C] hover:bg-[#18212e] text-white font-semibold text-[15px] mt-1 mb-6">
                        Sign In
                    </Button>

                    {/* Sign Up Link */}
                    <div className="w-full flex justify-center items-center font-medium text-[12px] leading-[16px] text-[#71717A]">
                        Don&apos;t have an account?{" "}
                        <Link
                            href="/auth/signup"
                            className="font-bold text-[#10151C] ml-1 hover:underline"
                        >
                            Sign up
                        </Link>
                    </div>
                </form>

                {/* Footer Links */}
                <div className="flex justify-center items-center gap-6 mt-8 pb-8">
                    <span className="font-bold text-[9px] leading-[16px] tracking-[0.1em] text-[#A1A1AA] uppercase">
                        ENTERPRISE V2.4
                    </span>
                    <span className="font-bold text-[9px] leading-[16px] tracking-[0.1em] text-[#A1A1AA] uppercase">
                        SECURED
                    </span>
                    <Link
                        href="/help"
                        className="font-bold text-[9px] leading-[16px] tracking-[0.1em] text-[#A1A1AA] uppercase hover:text-[#71717A] transition-colors"
                    >
                        HELP
                    </Link>
                    <Link
                        href="/"
                        className="font-bold text-[9px] leading-[16px] tracking-[0.1em] text-[#A1A1AA] uppercase hover:text-[#71717A] transition-colors"
                    >
                        WEBSITE
                    </Link>
                </div>
            </div>
        </div>
    );
};
