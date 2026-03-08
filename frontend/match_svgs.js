const fs = require('fs');
const path = require('path');

const svgDir = '/media/adi/New Volume/Internships/PM Accelerator/HouSmart/HouSmart/frontend/assets_svgs';
const svgFiles = fs.readdirSync(svgDir).filter(f => f.endsWith('.svg'));

const svgs = {};
for (const file of svgFiles) {
    const content = fs.readFileSync(path.join(svgDir, file), 'utf8');
    // Extract all d="..."
    const ds = [];
    const regex = /d="([^"]+)"/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
        ds.push(match[1]);
    }
    svgs[file] = ds.sort().join('|||'); // sorted joined paths
}

const iconsFile = '/media/adi/New Volume/Internships/PM Accelerator/HouSmart/HouSmart/frontend/src/components/ui/Icons.tsx';
const iconsContent = fs.readFileSync(iconsFile, 'utf8');
const iconRegex = /export const ([A-Za-z0-9_]+) = [\s\S]*?<svg[^>]*>([\s\S]*?)<\/svg>/g;

let match2;
const matches = {};
while ((match2 = iconRegex.exec(iconsContent)) !== null) {
    const name = match2[1];
    const inner = match2[2];
    const ds = [];
    const dRegex = /d="([^"]+)"/g;
    let dMatch;
    while ((dMatch = dRegex.exec(inner)) !== null) {
        ds.push(dMatch[1]);
    }
    const signature = ds.sort().join('|||');
    
    // Find match
    const matchedFile = Object.keys(svgs).find(file => svgs[file] === signature);
    if (matchedFile && signature) {
        matches[name] = matchedFile;
    } else {
        // Try substring match if exact match fails
        const matchedSubstring = Object.keys(svgs).find(file => svgs[file].includes(ds[0]) || (ds[0] && svgs[file].includes(ds[0])));
        if (matchedSubstring) {
             matches[name] = matchedSubstring + " (partial)";
        }
    }
}

console.log("MATCHES:", JSON.stringify(matches, null, 2));

// also check app/auth setup pages
const authPages = [
    'src/app/auth/setup/role/page.tsx',
    'src/app/auth/setup/priorities/page.tsx',
    'src/app/auth/setup/goal/page.tsx',
    'src/app/auth/setup/experience/page.tsx'
];
for (const page of authPages) {
     const pagePath = path.join('/media/adi/New Volume/Internships/PM Accelerator/HouSmart/HouSmart/frontend', page);
     const content = fs.readFileSync(pagePath, 'utf8');
     const dRegex = /<svg[^>]*>.*?d="([^"]+)".*?<\/svg>/gs;
     let m;
     while ((m = dRegex.exec(content)) !== null) {
         const d = m[1];
         const matchedFile = Object.keys(svgs).find(file => svgs[file].includes(d));
         if (matchedFile) {
             console.log(`Matched in ${page}: ${matchedFile}`);
         }
     }
}
