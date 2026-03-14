"use client";

import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Divider } from "../ui/Divider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Image from "next/image";

import mailIcon from "@/assets/auth/login/mail-icon.svg";
import lockIcon from "@/assets/auth/login/lock-icon.svg";
import googleIcon from "@/assets/auth/login/google-icon.svg";
import microsoftIcon from "@/assets/auth/login/microsoft-icon.svg";
import appleIcon from "@/assets/auth/login/apple-icon.svg";

export const SignUpForm = () => {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        console.log("Sign Up submitted", { email, password });
    };

    return (
        <div className="w-full flex flex-col pt-12">
            {/* Header */}
            <div className="flex flex-col items-center gap-2 mb-8">
                <h2 className="font-semibold text-[24px] leading-[32px] tracking-[-0.6px] text-center text-[#101828]">
                    Create an account
                </h2>
                <p className="font-normal text-[14px] leading-[20px] text-center text-[#6A7282]">
                    Enter your details to get started with Housmart.
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
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.05em] uppercase text-[#71717A] ml-1">
                            PASSWORD
                        </label>
                        <Input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            icon={<Image src={lockIcon} alt="Password" width={18} height={18} className="opacity-60" />}
                            className="h-[46px] rounded-xl border-[#E4E4E7]"
                            required
                        />
                        <p className="font-normal text-[11px] leading-[16px] text-[#A1A1AA] mt-1 ml-1">Must be at least 8 characters long.</p>
                        {error && (
                            <p className="text-red-500 text-[11px] leading-[16px] mt-1 ml-1 font-medium">{error}</p>
                        )}
                    </div>

                    <Button type="submit" className="w-full h-[46px] rounded-xl bg-[#10151C] hover:bg-[#18212e] text-white font-semibold text-[15px] mb-8 mt-1">
                        Sign Up
                    </Button>

                    {/* Sign In Link */}
                    <div className="w-full flex justify-center items-center font-medium text-[11px] leading-[16px] text-[#6A7282]">
                        Already have an account?{" "}
                        <Link
                            href="/auth/login"
                            className="font-semibold text-[#101828] ml-1 hover:underline"
                        >
                            Log in
                        </Link>
                    </div>
                </form>

                {/* Footer Links */}
                <div className="flex justify-center items-center gap-6 mt-6 pb-8">
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
