# HouSmart Frontend

This is a [Next.js 15+](https://nextjs.org) App Router project styled with Tailwind CSS v4.

## Getting Started

First, install dependencies and run the development server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

---

## Project Structure & Routes

The application features a modular component architecture (`src/components/ui`, `src/components/auth`, `src/components/search`) with specific App Router paths.

### 1. Authentication (`/auth`)

The authentication flow utilizes a shared layout (`AuthLayout.tsx`) featuring a split-screen design (marketing hero on the left, forms perfectly centered on the right).

- **Login Screen:** [http://localhost:3000/auth/login](http://localhost:3000/auth/login)
- **Sign Up Screen:** [http://localhost:3000/auth/signup](http://localhost:3000/auth/signup)

*Note: The Login and Sign Up screens are connected. Users can navigate between them using the "Don't have an account?" and "Already have an account?" text links at the bottom of each form.*

### 2. Onboarding Flow (`/auth/setup/*`)

After authenticating, users are directed to a multi-step onboarding flow designed to gather their investment profile. State is preserved across steps using a React Context provider (`SetupProvider`).

The flow redirects sequentially:
1. **Redirect/Start:** [http://localhost:3000/auth/setup](http://localhost:3000/auth/setup) -> Auto-redirects to `/role`
2. **Step 1 (Role):** [http://localhost:3000/auth/setup/role](http://localhost:3000/auth/setup/role)
3. **Step 2 (Experience):** [http://localhost:3000/auth/setup/experience](http://localhost:3000/auth/setup/experience)
4. **Step 3 (Goal):** [http://localhost:3000/auth/setup/goal](http://localhost:3000/auth/setup/goal)
5. **Step 4 (Priorities):** [http://localhost:3000/auth/setup/priorities](http://localhost:3000/auth/setup/priorities) *(Features drag-and-drop `@dnd-kit` functionality)*
6. **Step 5 (Market):** [http://localhost:3000/auth/setup/market](http://localhost:3000/auth/setup/market)

### 3. Property Input (`/property-input`)

After setup, users access the Property Input dashboard to begin their property analysis.

- **URL:** [http://localhost:3000/property-input](http://localhost:3000/property-input)

**Key Features:**
- A central search component with recent search history functionality.
- A "Hot markets & hidden gems" grid divided into 3 responsive columns.
- The grid is powered by 3 simulated mock API endpoints inside `src/app/api/...`:
  1. `/api/investment-hotspots`
  2. `/api/trending-properties`
  3. `/api/new-listings`
- The mock endpoints utilize native Next.js `NextResponse` to simulate an 800ms network delay before rendering the data on the frontend.

---

## UI Documentation

### A. Reusable UI Components (`src/components/ui/`)
- **`Input.tsx`:** Flexible input component wrapping SVG icons natively.
- **`Button.tsx`:** Standardized buttons (`default`, `outline`) managing branding colors.
- **`Icons.tsx`:** A centralized hub exporting SVG-to-React components.

### B. Styling Engine
The project utilizes the new Tailwind CSS v4 engine (`@tailwindcss/postcss`). Accordingly, the `globals.css` file uses the modern `@import "tailwindcss";` directive. All pages enforce strict mobile-first flexibility, snapping easily from mobile to large desktop resolutions.