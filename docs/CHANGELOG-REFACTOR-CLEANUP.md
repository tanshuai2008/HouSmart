# Frontend Change Log

Date: 2026-03-09
Scope: End-to-end refactor and cleanup from initial state to final sweep.

## 1. Route and Page Refactor

- Updated core routes and page implementations:
  - `src/app/page.tsx`
  - `src/app/property-input/page.tsx`
  - `src/app/analyze/page.tsx`
  - `src/app/dashboard/page.tsx`
  - `src/app/layout.tsx`
  - `src/app/globals.css`
- Refactored auth routes:
  - `src/app/auth/login/page.tsx`
  - `src/app/auth/signup/page.tsx`
- Refactored setup flow routes:
  - `src/app/auth/setup/layout.tsx`
  - `src/app/auth/setup/role/page.tsx`
  - `src/app/auth/setup/experience/page.tsx`
  - `src/app/auth/setup/goal/page.tsx`
  - `src/app/auth/setup/priorities/page.tsx`

## 2. Setup Flow Consolidation

- Added centralized setup data and styling:
  - `src/app/auth/setup/setup-step-data.ts`
  - `src/app/auth/setup/setup-step.module.css`
- Added/standardized provider location:
  - `src/providers/setup-context.tsx`
- Removed legacy context location:
  - `src/context/SetupContext.tsx`

## 3. Dashboard Data and Styling Reorganization

- Added route-local dashboard data and styles:
  - `src/app/dashboard/dashboard-data.ts`
  - `src/app/dashboard/dashboard-page.module.css`
- Updated dashboard components:
  - `src/components/dashboard/PropertyContext.tsx`
  - `src/components/dashboard/PropertyVerdict.tsx`
  - `src/components/dashboard/FinancialMetrics.tsx`
  - `src/components/dashboard/MarketTrends.tsx`
  - `src/components/dashboard/ComparableListings.tsx`
  - `src/components/layout/DashboardHeader.tsx`
  - `src/components/layout/StepIndicator.tsx`
  - `src/components/charts/PriceTrendChart.tsx`
  - `src/components/charts/RevenueExpensesChart.tsx`
  - `src/components/analysis/AnalysisProcessingView.tsx`

## 4. Auth Component Modernization

- Added/renamed auth components and styles:
  - `src/components/auth/AuthLayout.tsx`
  - `src/components/auth/LoginForm.tsx`
  - `src/components/auth/RegistrationForm.tsx`
  - `src/components/auth/auth-layout.module.css`
  - `src/components/auth/auth-form.module.css`
- Removed legacy auth component naming:
  - `src/components/auth/SignUpForm.tsx`
  - `src/components/layout/AuthLayout.tsx`

## 5. UI Layer Cleanup

- Updated shared UI components:
  - `src/components/ui/SelectableCard.tsx`
  - `src/components/ui/ScoreBar.tsx`
  - `src/components/ui/DraggableItem.tsx`
  - `src/components/ui/Divider.tsx`
  - `src/components/ui/Input.tsx`
  - `src/components/ui/Icons.tsx`
- Removed unused UI/search/dashboard components:
  - `src/components/ui/Card.tsx`
  - `src/components/search/InsightColumn.tsx`
  - `src/components/search/InsightListItem.tsx`
  - `src/components/search/MarketInsightsGrid.tsx`
  - `src/components/dashboard/AIChatWidget.tsx`

## 6. Asset Rationalization

- Added normalized SVG/icon set under active paths:
  - `src/assets/auth/*`
  - `src/assets/icons/*`
  - `src/assets/dashboard/icons/*`
- Removed legacy/unused assets from prior structure:
  - `src/assets/auth/login/*`
  - `src/assets/search/images/*` (legacy static set)
  - multiple deprecated `src/assets/dashboard/icons/*` entries
  - deprecated analyze and dashboard image assets

## 7. Removed Obsolete Helpers and Scripts

- Removed deprecated local scripts:
  - `match_svgs.js`
  - `replace_icons.js`
- Removed outdated utility files:
  - `src/lib/mockData.ts`
  - `src/utils/imageMapper.ts`

## 8. Final Sweep Outcomes

- Enforced no-inline-SVG in TSX component layer:
  - Replaced raw `<svg>` blocks in `src/components/ui/Icons.tsx` with `lucide-react` icons or asset-backed `next/image` icons.
- Enforced no-inline-style usage in app/components/providers (none remaining).
- Refreshed stale unused report:
  - `tmp-unused-report.txt` now records final sweep status and no actionable entries.
- Validation checks passed:
  - `npm run lint`
  - `npx tsc --noEmit`

## 9. Notes

- This log reflects the working tree transition from initial implementation to the current refactored state.
- If needed, this can be split into commit-level changelogs once commits are organized by feature area.
