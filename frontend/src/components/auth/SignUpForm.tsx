"use client";

import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Divider } from "../ui/Divider";
import { GoogleIcon, EnvelopeIcon, LockIcon, UserIcon } from "../ui/Icons";
import Link from "next/link";
import { useRouter } from "next/navigation";

export const SignUpForm = () => {
    const router = useRouter();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        console.log("Sign Up submitted", { name, email, password });
    };

    return (
        <div className="w-full flex flex-col pt-12">
            {/* Header */}
            <div className="flex flex-col items-center gap-2 mb-8">
                <h2 className="font-semibold text-[24px] leading-[32px] tracking-[-0.6px] text-center text-[#101828]">
                    Register
                </h2>
                <p className="font-normal text-[14px] leading-[20px] text-center text-[#6A7282]">
                    Create an account to get started.
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
                    {/* Name Field */}
                    <div className="flex flex-col gap-2 mb-4">
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.55px] uppercase text-[#6A7282] ml-1">
                            Name
                        </label>
                        <Input
                            type="text"
                            placeholder="Your Name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            icon={<UserIcon className="w-4 h-4" />}
                            required
                        />
                    </div>

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
                    <div className="flex flex-col gap-2 mb-4">
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.55px] uppercase text-[#6A7282] ml-1">
                            Password
                        </label>
                        <Input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            icon={<LockIcon className="w-4 h-4" />}
                            required
                        />
                    </div>

                    {/* Confirm Password Field */}
                    <div className="flex flex-col gap-2 mb-6">
                        <label className="font-bold text-[11px] leading-[16px] tracking-[0.55px] uppercase text-[#6A7282] ml-1">
                            Confirm Password
                        </label>
                        <Input
                            type="password"
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            icon={<LockIcon className="w-4 h-4" />}
                            required
                        />
                        {error && (
                            <p className="text-red-500 text-[11px] leading-[16px] mt-1 ml-1 font-medium">{error}</p>
                        )}
                    </div>

                    <Button type="submit" className="w-full h-[40px] mb-8">
                        Sign Up
                    </Button>

                    {/* Sign In Link */}
                    <div className="w-full flex justify-center items-center font-medium text-[11px] leading-[16px] text-[#6A7282]">
                        Already have an account?{" "}
                        <Link
                            href="/login"
                            className="font-semibold text-[#101828] ml-1 hover:underline"
                        >
                            Sign in
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
