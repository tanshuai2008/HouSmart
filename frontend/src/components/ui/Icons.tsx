import React from "react";
import Image from "next/image";
import logoIconV2 from "@/assets/icons/logo-icon-v2.svg";
import featureCheck from "@/assets/icons/feature-check.svg";
import trendingUp from "@/assets/icons/trending-up.svg";
import shieldCheck from "@/assets/icons/shield-check.svg";
import envelope from "@/assets/icons/envelope.svg";
import lock from "@/assets/icons/lock.svg";
import individualInvestor from "@/assets/icons/individual-investor.svg";
import realEstateAgent from "@/assets/icons/real-estate-agent.svg";
import institutionalBuyer from "@/assets/icons/institutional-buyer.svg";
import experiencedInvestor from "@/assets/icons/experienced-investor.svg";
import cashFlow from "@/assets/icons/cash-flow.svg";
import longTermAppreciation from "@/assets/icons/long-term-appreciation.svg";
import balancedMix from "@/assets/icons/balanced-mix.svg";

export const LogoIcon = (props: any) => (
    <Image src={logoIconV2} alt="LogoIcon" {...props} />
);

export const FeatureCheckIcon = (props: any) => (
    <Image src={featureCheck} alt="FeatureCheckIcon" {...props} />
);

export const TrendingUpIcon = (props: any) => (
    <Image src={trendingUp} alt="TrendingUpIcon" {...props} />
);

export const ShieldCheckIcon = (props: any) => (
    <Image src={shieldCheck} alt="ShieldCheckIcon" {...props} />
);

export const GoogleIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        {...props}
    >
        <path
            d="M15.037 8.16501C15.037 7.64512 14.9903 7.14522 14.9037 6.66531H7.99841V9.50474H11.9443C11.771 10.4179 11.2511 11.1911 10.4712 11.711V13.5573H12.8508C14.2372 12.2775 15.037 10.3979 15.037 8.16501Z"
            fill="#4285F4"
        />
        <path
            d="M7.99841 15.3302C9.97801 15.3302 11.6377 14.677 12.8508 13.5573L10.4712 11.711C9.81804 12.1509 8.98488 12.4175 7.99841 12.4175C6.09213 12.4175 4.47245 11.1311 3.89257 9.3981H1.45306V11.2911C2.65949 13.6839 5.13232 15.3302 7.99841 15.3302Z"
            fill="#34A853"
        />
        <path
            d="M3.89252 9.39143C3.74588 8.95152 3.65923 8.48494 3.65923 7.99837C3.65923 7.51181 3.74588 7.04523 3.89252 6.60532V4.71237H1.45301C0.953113 5.69884 0.666504 6.81195 0.666504 7.99837C0.666504 9.1848 0.953113 10.2979 1.45301 11.2844L3.35263 9.80468L3.89252 9.39143Z"
            fill="#FBBC05"
        />
        <path
            d="M7.99841 3.58595C9.07819 3.58595 10.038 3.9592 10.8045 4.67906L12.9041 2.57948C11.631 1.39305 9.97801 0.666534 7.99841 0.666534C5.13232 0.666534 2.65949 2.31287 1.45306 4.71238L3.89257 6.60534C4.47245 4.87235 6.09213 3.58595 7.99841 3.58595Z"
            fill="#EA4335"
        />
    </svg>
);

export const EnvelopeIcon = (props: any) => (
    <Image src={envelope} alt="EnvelopeIcon" {...props} />
);

export const LockIcon = (props: any) => (
    <Image src={lock} alt="LockIcon" {...props} />
);

export const IndividualInvestorIcon = (props: any) => (
    <Image src={individualInvestor} alt="IndividualInvestorIcon" {...props} />
);

export const RealEstateAgentIcon = (props: any) => (
    <Image src={realEstateAgent} alt="RealEstateAgentIcon" {...props} />
);

export const InstitutionalBuyerIcon = (props: any) => (
    <Image src={institutionalBuyer} alt="InstitutionalBuyerIcon" {...props} />
);

export const GraduationCapIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="M22 10L12 5L2 10L12 15L22 10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M6 12V16C6 17 8 19 12 19C16 19 18 17 18 16V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M22 10V16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const ExperiencedInvestorIcon = (props: any) => (
    <Image src={experiencedInvestor} alt="ExperiencedInvestorIcon" {...props} />
);

export const CoinsIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
        <circle cx="9" cy="15" r="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M11 5H21V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 5L15 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 15H9.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const LineChartIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="M3 3V21H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 16L9 10L13 14L21 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const UsersGroupIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
        <path d="M17 21V19C17 17.8954 16.1046 17 15 17H9C7.89543 17 7 17.8954 7 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 13C14.2091 13 16 11.2091 16 9C16 6.79086 14.2091 5 12 5C9.79086 5 8 6.79086 8 9C8 11.2091 9.79086 13 12 13Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M22 21V19C22 17.8954 21.1046 17 20 17H19M16 3.13C17.5 3.5 18.5 4.8 18.5 6.5C18.5 8.2 17.5 9.5 16 9.87M2 21V19C2 17.8954 2.89543 17 4 17H5M8 9.87C6.5 9.5 5.5 8.2 5.5 6.5C5.5 4.8 6.5 3.5 8 3.13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const CashFlowIcon = (props: any) => (
    <Image src={cashFlow} alt="CashFlowIcon" {...props} />
);

export const LongTermAppreciationIcon = (props: any) => (
    <Image src={longTermAppreciation} alt="LongTermAppreciationIcon" {...props} />
);

export const BalancedMixIcon = (props: any) => (
    <Image src={balancedMix} alt="BalancedMixIcon" {...props} />
);

export const UserIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        {...props}
    >
        <path
            d="M8 8C9.84095 8 11.3333 6.50761 11.3333 4.66667C11.3333 2.82572 9.84095 1.33333 8 1.33333C6.15905 1.33333 4.66667 2.82572 4.66667 4.66667C4.66667 6.50761 6.15905 8 8 8Z"
            stroke="currentColor"
            strokeWidth="1.33306"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <path
            d="M3.33333 14.6667C3.33333 12.0893 5.38556 10 8 10C10.6144 10 12.6667 12.0893 12.6667 14.6667"
            stroke="currentColor"
            strokeWidth="1.33306"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
    </svg>
);
