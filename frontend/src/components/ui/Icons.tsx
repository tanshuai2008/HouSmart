import React from "react";
import Image, { type ImageProps } from "next/image";
import { ChartLine, CircleDollarSign, UserRound, UsersRound } from "lucide-react";
import logoIconV2 from "@/assets/icons/logo-icon-v2.svg";
import featureCheck from "@/assets/icons/feature-check.svg";
import trendingUp from "@/assets/icons/trending-up.svg";
import shieldCheck from "@/assets/icons/shield-check.svg";
import socialGoogle from "@/assets/auth/social-google.svg";
import envelope from "@/assets/icons/envelope.svg";
import lock from "@/assets/icons/lock.svg";
import individualInvestor from "@/assets/icons/individual-investor.svg";
import individualInvestorSelected from "@/assets/icons/individual-investor-selected.svg";
import realEstateAgent from "@/assets/icons/real-estate-agent.svg";
import realEstateAgentSelected from "@/assets/icons/real-estate-agent-selected.svg";
import institutionalBuyer from "@/assets/icons/institutional-buyer.svg";
import institutionalBuyerSelected from "@/assets/icons/institutional-buyer-selected.svg";
import experiencedInvestor from "@/assets/icons/experienced-investor.svg";
import experiencedInvestorSelected from "@/assets/icons/experienced-investor-selected.svg";
import graduationCap from "@/assets/icons/graduation-cap.svg";
import graduationCapSelected from "@/assets/icons/graduation-cap-selected.svg";
import cashFlow from "@/assets/icons/cash-flow.svg";
import cashFlowSelected from "@/assets/icons/cash-flow-selected.svg";
import longTermAppreciation from "@/assets/icons/long-term-appreciation.svg";
import longTermAppreciationSelected from "@/assets/icons/long-term-appreciation-selected.svg";
import balancedMix from "@/assets/icons/balanced-mix.svg";
import balancedMixSelected from "@/assets/icons/balanced-mix-selected.svg";

type ImageIconProps = Omit<ImageProps, "src" | "alt">;

export const LogoIcon = (props: ImageIconProps) => (
    <Image src={logoIconV2} alt="LogoIcon" {...props} />
);

export const FeatureCheckIcon = (props: ImageIconProps) => (
    <Image src={featureCheck} alt="FeatureCheckIcon" {...props} />
);

export const TrendingUpIcon = (props: ImageIconProps) => (
    <Image src={trendingUp} alt="TrendingUpIcon" {...props} />
);

export const ShieldCheckIcon = (props: ImageIconProps) => (
    <Image src={shieldCheck} alt="ShieldCheckIcon" {...props} />
);

export const GoogleIcon = (props: ImageIconProps) => (
    <Image src={socialGoogle} alt="GoogleIcon" {...props} />
);

export const EnvelopeIcon = (props: ImageIconProps) => (
    <Image src={envelope} alt="EnvelopeIcon" {...props} />
);

export const LockIcon = (props: ImageIconProps) => (
    <Image src={lock} alt="LockIcon" {...props} />
);

export const IndividualInvestorIcon = (props: ImageIconProps) => (
    <Image src={individualInvestor} alt="IndividualInvestorIcon" {...props} />
);

export const IndividualInvestorSelectedIcon = (props: ImageIconProps) => (
    <Image src={individualInvestorSelected} alt="IndividualInvestorSelectedIcon" {...props} />
);

export const RealEstateAgentIcon = (props: ImageIconProps) => (
    <Image src={realEstateAgent} alt="RealEstateAgentIcon" {...props} />
);

export const RealEstateAgentSelectedIcon = (props: ImageIconProps) => (
    <Image src={realEstateAgentSelected} alt="RealEstateAgentSelectedIcon" {...props} />
);

export const InstitutionalBuyerIcon = (props: ImageIconProps) => (
    <Image src={institutionalBuyer} alt="InstitutionalBuyerIcon" {...props} />
);

export const InstitutionalBuyerSelectedIcon = (props: ImageIconProps) => (
    <Image src={institutionalBuyerSelected} alt="InstitutionalBuyerSelectedIcon" {...props} />
);

export const GraduationCapIcon = (props: ImageIconProps) => (
    <Image src={graduationCap} alt="GraduationCapIcon" {...props} />
);

export const GraduationCapSelectedIcon = (props: ImageIconProps) => (
    <Image src={graduationCapSelected} alt="GraduationCapSelectedIcon" {...props} />
);

export const ExperiencedInvestorIcon = (props: ImageIconProps) => (
    <Image src={experiencedInvestor} alt="ExperiencedInvestorIcon" {...props} />
);

export const ExperiencedInvestorSelectedIcon = (props: ImageIconProps) => (
    <Image src={experiencedInvestorSelected} alt="ExperiencedInvestorSelectedIcon" {...props} />
);

export const CoinsIcon = (props: React.SVGProps<SVGSVGElement>) => <CircleDollarSign {...props} />;

export const LineChartIcon = (props: React.SVGProps<SVGSVGElement>) => <ChartLine {...props} />;

export const UsersGroupIcon = (props: React.SVGProps<SVGSVGElement>) => <UsersRound {...props} />;

export const CashFlowIcon = (props: ImageIconProps) => (
    <Image src={cashFlow} alt="CashFlowIcon" {...props} />
);

export const CashFlowSelectedIcon = (props: ImageIconProps) => (
    <Image src={cashFlowSelected} alt="CashFlowSelectedIcon" {...props} />
);

export const LongTermAppreciationIcon = (props: ImageIconProps) => (
    <Image src={longTermAppreciation} alt="LongTermAppreciationIcon" {...props} />
);

export const LongTermAppreciationSelectedIcon = (props: ImageIconProps) => (
    <Image src={longTermAppreciationSelected} alt="LongTermAppreciationSelectedIcon" {...props} />
);

export const BalancedMixIcon = (props: ImageIconProps) => (
    <Image src={balancedMix} alt="BalancedMixIcon" {...props} />
);

export const BalancedMixSelectedIcon = (props: ImageIconProps) => (
    <Image src={balancedMixSelected} alt="BalancedMixSelectedIcon" {...props} />
);

export const UserIcon = (props: React.SVGProps<SVGSVGElement>) => <UserRound {...props} />;
