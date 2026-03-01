This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


# HouSmart-Frontend

## Implementation: Login Page (Desktop)

This section documents the architectural decisions, component structure, and styling approach used to build the desktop version of the HouSmart Login Page. The primary goal was to create a highly modular, pixel-perfect replication of the provided Figma design that can be easily repurposed for future authentication pages (e.g., Sign Up).

### 1. Technology Stack & Environment
- **Framework:** Next.js 15+ (App Router)
- **Styling:** Tailwind CSS v4
- **Fonts:** Inter (Loaded via `next/font/google` in `layout.tsx`)

*Note on Tailwind v4:* The project utilizes the new Tailwind CSS v4 engine (`@tailwindcss/postcss`). Accordingly, the `globals.css` file uses the modern `@import "tailwindcss";` directive rather than the legacy `@tailwind base;` directives to ensure utility classes compile correctly.

### 2. Component Architecture

To guarantee reusability, the UI was broken down into atomic components located in `src/components/ui/` and assembled in a specific layout wrapper.

#### A. Reusable UI Components
- **`Input.tsx`:** A flexible, controlled `<input>` component wrapped in a styled `div`. It accepts an optional `icon` prop to render SVG icons (like an envelope or lock) on the left side of the input field. It enforces a standard `#E5E7EB` border, rounded corners (`10px`), and consistent padding.
- **`Button.tsx`:** A foundational button component supporting two design variants:
  - `variant="default"`: The primary dark `#101828` button used for "Sign In".
  - `variant="outline"`: The secondary white button with a border, used for the "Continue with Gmail" action. It also supports passing an `icon` prop.
- **`Divider.tsx`:** A simple visual separator used to render the "OR CONTINUE WITH EMAIL" line.
- **`Icons.tsx`:** A centralized file exporting all necessary pure SVG React components (HouSmart Logo, Feature checkmarks, Google logo, etc.) to keep component files clean.

#### B. Layout & Assembly
- **`AuthLayout.tsx`:** The core structural component handling the split-screen design.
  - **Left Panel (Hero/Marketing):** A strictly sized container (`lg:w-1/2`) featuring the dark `#101828` background, a blurred aura element (`blur-[64px]`), the company logo, heading, and a dynamic list of features. 
  - **Right Panel (Form Container):** A flexible container taking up the remaining 50% of the screen (`lg:w-1/2`) with a light `#F9FAFB` background, designed to perfectly center whatever form children are passed to it.
- **`LoginForm.tsx`:** The specific module housed in `src/components/auth/` that handles the state and layout of the Email and Password fields, the "Forgot Password" link, and the bottom footer links ("Enterprise V2.4", etc.).

### 3. Styling & Desktop Responsiveness
The layout achieves its side-by-side desktop view through Tailwind's Flexbox utilities. 
- The parent wrapper uses `flex flex-col lg:flex-row`. 
- By applying `lg:w-1/2` to both the Left Panel and Right Panel, the layout guarantees a strict 50/50 split on large desktop monitors.
- Fonts and spacing precisely map to the provided CSS dimensions, ensuring a 1:1 match with the design specifications.