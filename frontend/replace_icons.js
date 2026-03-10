const fs = require('fs');

const iconsPath = '/media/adi/New Volume/Internships/PM Accelerator/HouSmart/HouSmart/frontend/src/components/ui/Icons.tsx';
let content = fs.readFileSync(iconsPath, 'utf8');

// The replacement mapping
const replacements = {
  'LogoIcon': 'logo-icon-v2.svg',
  'FeatureCheckIcon': 'feature-check.svg',
  'TrendingUpIcon': 'trending-up.svg',
  'ShieldCheckIcon': 'shield-check.svg',
  'EnvelopeIcon': 'envelope.svg',
  'LockIcon': 'lock.svg',
  'IndividualInvestorIcon': 'individual-investor.svg',
  'RealEstateAgentIcon': 'real-estate-agent.svg',
  'InstitutionalBuyerIcon': 'institutional-buyer.svg',
  'ExperiencedInvestorIcon': 'experienced-investor.svg',
  'CashFlowIcon': 'cash-flow.svg',
  'LongTermAppreciationIcon': 'long-term-appreciation.svg',
  'BalancedMixIcon': 'balanced-mix.svg'
};

const imports = [
  'import Image from "next/image";',
  'import logoIconV2 from "@/assets/icons/logo-icon-v2.svg";',
  'import featureCheck from "@/assets/icons/feature-check.svg";',
  'import trendingUp from "@/assets/icons/trending-up.svg";',
  'import shieldCheck from "@/assets/icons/shield-check.svg";',
  'import envelope from "@/assets/icons/envelope.svg";',
  'import lock from "@/assets/icons/lock.svg";',
  'import individualInvestor from "@/assets/icons/individual-investor.svg";',
  'import realEstateAgent from "@/assets/icons/real-estate-agent.svg";',
  'import institutionalBuyer from "@/assets/icons/institutional-buyer.svg";',
  'import experiencedInvestor from "@/assets/icons/experienced-investor.svg";',
  'import cashFlow from "@/assets/icons/cash-flow.svg";',
  'import longTermAppreciation from "@/assets/icons/long-term-appreciation.svg";',
  'import balancedMix from "@/assets/icons/balanced-mix.svg";'
].join('\n');

content = content.replace('import React from "react";', `import React from "react";\n${imports}`);

const camelCaseMap = {
  'LogoIcon': 'logoIconV2',
  'FeatureCheckIcon': 'featureCheck',
  'TrendingUpIcon': 'trendingUp',
  'ShieldCheckIcon': 'shieldCheck',
  'EnvelopeIcon': 'envelope',
  'LockIcon': 'lock',
  'IndividualInvestorIcon': 'individualInvestor',
  'RealEstateAgentIcon': 'realEstateAgent',
  'InstitutionalBuyerIcon': 'institutionalBuyer',
  'ExperiencedInvestorIcon': 'experiencedInvestor',
  'CashFlowIcon': 'cashFlow',
  'LongTermAppreciationIcon': 'longTermAppreciation',
  'BalancedMixIcon': 'balancedMix'
};

for (const [componentName, varName] of Object.entries(camelCaseMap)) {
    const regex = new RegExp(`export const ${componentName} = \\(props: React\\.SVGProps<SVGSVGElement>\\) => \\([\\s\\S]*?<svg[^>]*>([\\s\\S]*?)<\\/svg>\\n\\);`);
    content = content.replace(regex, `export const ${componentName} = (props: any) => (\n    <Image src={${varName}} alt="${componentName}" {...props} />\n);`);
}

fs.writeFileSync(iconsPath, content);
console.log("Replaced icons in Icons.tsx");
