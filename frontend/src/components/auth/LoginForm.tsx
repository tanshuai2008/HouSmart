"use client";

import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Divider } from "../ui/Divider";
import { GoogleIcon, EnvelopeIcon, LockIcon } from "../ui/Icons";
import Link from "next/link";

export const LoginForm = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log("Login submitted", { email, password });
    };

    return (
        <div className="w-full flex flex-col pt-12">
            {/* Header */}
            <div className="flex flex-col items-center gap-2 mb-8">
                <h2 className="font-semibold text-[24px] leading-[32px] tracking-[-0.6px] text-center text-[#101828]">
                    Welcome back
                </h2>
                <p className="font-normal text-[14px] leading-[20px] text-center text-[#6A7282]">
                    Enter your credentials to access your workspace.
                </p>
            </div>

            {/* Form Container */}
            <div className="w-full mt-4 flex flex-col gap-6">
                <Button
                    variant="outline"
                    type="button"
                    icon={<GoogleIcon />}
                    className="w-full h-[44px]"
                >
                    Continue with Gmail
                </Button>

                <Divider />

                <form onSubmit={handleSubmit} className="flex flex-col w-full">
                    {/* Email Field */}
                    <div className="flex flex-col gap-2 mb-4">
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.55px] uppercase text-[#6A7282] ml-1">
                            Email
                        </label>
                        <Input
                            type="email"
                            placeholder="name@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            icon={<EnvelopeIcon className="w-4 h-4" />}
                            required
                        />
                    </div>

                    {/* Password Field */}
                    <div className="flex flex-col gap-2 mb-6">
                        <div className="flex justify-between items-center w-full px-1">
                            <label className="font-bold text-[11px] leading-[16px] tracking-[0.55px] uppercase text-[#6A7282]">
                                Password
                            </label>
                            <Link
                                href="/forgot-password"
                                className="font-medium text-[11px] leading-[16px] text-center text-[#6A7282] hover:text-[#101828] transition-colors"
                            >
                                Forgot?
                            </Link>
                        </div>
                        <Input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            icon={<LockIcon className="w-4 h-4" />}
                            required
                        />
                    </div>

                    <Button type="submit" className="w-full h-[40px] mb-8">
                        Sign In
                    </Button>

                    {/* Sign Up Link */}
                    <div className="w-full flex justify-center items-center font-medium text-[11px] leading-[16px] text-[#6A7282]">
                        Don&apos;t have an account?{" "}
                        <Link
                            href="/signup"
                            className="font-semibold text-[#101828] ml-1 hover:underline"
                        >
                            Sign up
                        </Link>
                    </div>
                </form>

                {/* Footer Links */}
                <div className="flex justify-center items-center gap-6 mt-6 pb-8">
                    <span className="font-medium text-[10px] leading-[15px] tracking-[1px] text-[#99A1AF] uppercase">
                        Enterprise V2.4
                    </span>
                    <span className="font-medium text-[10px] leading-[15px] tracking-[1px] text-[#99A1AF] uppercase">
                        Secured
                    </span>
                    <Link
                        href="/help"
                        className="font-medium text-[10px] leading-[15px] tracking-[1px] text-[#99A1AF] uppercase hover:text-[#6A7282]"
                    >
                        Help
                    </Link>
                </div>
            </div>
        </div>
    );
};
