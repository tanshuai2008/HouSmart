# Changes Record (14 March 2026)

Date: 14 March 2026

## Summary

Today's work focused on two frontend areas:
- improving dashboard loading behavior while property data and market trends are fetched
- refining the market trend chart presentation for sale-to-list ratio and median sale price

## Frontend changes

### Dashboard loading flow update
- Added explicit dashboard load states in `frontend/src/app/dashboard/page.tsx`:
  - `idle`
  - `loading`
  - `ready`
  - `error`
- Added a dedicated `DashboardSkeleton()` view so the dashboard shows structured placeholder content while data is loading.
- Updated the dashboard load effect to fetch:
  - property dashboard payload from `getDashboardProperty(...)`
  - market trends from `/api/market-trends`
- Coordinated those requests with `Promise.all(...)` so the page waits for both data sources before rendering the main dashboard content.
- Reset dashboard payload and chart state when the selected property changes or when the user/property context is missing.
- Added guarded rendering so the main dashboard layout only appears when:
  - the page status is `ready`
  - property payload data is available
  - price trend data is available
  - revenue/median sale price trend data is available
- Added clearer fallback states for:
  - no selected property (`idle`)
  - failed dashboard load (`error`)

### Market trends graph update
- Updated `frontend/src/components/dashboard/MarketTrends.tsx` to use backend-provided trend series instead of static dashboard mock data.
- Kept the market trends section split into two charts:
  - sale-to-list ratio
  - median sale price

### Sale-to-list ratio chart refinement
- Updated `frontend/src/components/charts/PriceTrendChart.tsx` to calculate Y-axis bounds dynamically from the incoming data.
- Added padded chart domains and generated tick marks from the live series instead of relying on a fixed range.
- Kept the 100% reference line so ratio movement remains easy to read against the sale-to-list baseline.
- Formatted X-axis labels from `YYYY-MM` to compact month/year labels for better readability in the narrow chart width.
- Updated the tooltip to show the ratio as a percentage with a cleaner chart-specific label.

### Median sale price chart refinement
- Updated `frontend/src/components/charts/RevenueExpensesChart.tsx` to derive chart min/max values from the fetched revenue series.
- Added auto-scaled Y-axis step calculation so larger or smaller price ranges remain readable without hand-tuned constants.
- Formatted Y-axis ticks in thousands (`$xxxk`) while keeping full dollar values inside the tooltip.
- Formatted X-axis month labels to match the sale-to-list chart for visual consistency across the market trends section.
- Updated the tooltip copy so the chart clearly reports median sale price values.

## Outcome

At the end of today's changes:
- the dashboard loads more cleanly with a dedicated skeleton and clearer state handling
- users no longer see partially rendered dashboard content before both API responses are ready
- both market trend charts scale to the returned backend data more reliably
- chart labels and tooltips are more consistent and easier to read
