# HouSmart Rent Estimation API: Technical Integration Plan (v2.0)

## 1. Overview
This document defines the transition to the **Zyla Rent Estimation API** as the primary data source and the implementation of the **HouSmart Proprietary Refinement Layer**. By ingesting specific property nuances from the user, the API provides a "Value-Add" estimate that outperforms standard market data.

## 2. Updated API Specification

### 2.1 Endpoint: `POST /api/v1/rent-estimate/enhanced`
To provide a better estimation, the API now accepts specific "Condition" and "Feature" parameters.

**Query Parameters / Request Body:**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `address` | String | Yes | Full property address or ZIP |
| `beds` / `baths` | Float | Yes | Room counts |
| `condition` | Enum | No | `Excellent`, `Good`, `Average`, `Poor` |
| `is_renovated` | Boolean | No | Specifically for Kitchen/Bath updates |
| `amenities` | List | No | e.g., `["pool", "central_ac", "in_unit_laundry"]` |
| `parking_spots`| Int | No | Number of dedicated off-street spots |

---

## 3. The "Better Estimation" Logic (Post-Processing)

Zyla provides the *market baseline*. HouSmart applies the *investor reality*.

### Layer 1: The Condition & Feature Modifier (Modifier Table)
Upon receiving the Zyla baseline, the engine applies the following weighted adjustments:
1.  **Condition Adjustment:**
    - `Excellent`: +10% to baseline.
    - `Average`: +0% (Baseline).
    - `Poor`: -15% (Reflects "as-is" rental risk).
2.  **Renovation Premium:** If `is_renovated` is `True`, add a flat **$150 - $300** "Modernization Lift" based on the local ZIP code's luxury tier.
3.  **Amenity Stacking:** - `In-unit Laundry`: +$50/mo.
    - `Central AC`: +3% to total.
    - `Parking`: +$75 per spot (Urban) or +$25 (Suburban).



### Layer 2: Proprietary Confidence Score (0-100)
This score tells the user how much they can trust the Zyla data based on the quality of the comparables (comps) found:
- **Comp Density (40%):** 10+ comps = Full points.
- **Geographic Tightness (30%):** Points deducted if the average comp distance is >1.2 miles.
- **Recency (30%):** Points deducted if the average comp listing is >6 months old.

---

## 4. Implementation Workflow (FastAPI)

```python
async def get_enhanced_rent_flow(user_input):
    # 1. Fetch Baseline from Zyla API
    zyla_data = await zyla_client.get_rent_stats(
        address=user_input.address, 
        beds=user_input.beds
    )
    
    # 2. Extract Zyla's Comps for Confidence Calculation
    comps = zyla_data.get("comparables", [])
    confidence_score = calculate_housmart_confidence(comps, user_input)
    
    # 3. Apply Modifier Table Logic
    base_rent = zyla_data["estimated_rent"]
    refined_rent = apply_user_modifiers(base_rent, user_input)
    
    # 4. Generate Range & Metrics
    return {
        "property": user_input.address,
        "housmart_estimate": round(refined_rent, 2),
        "confidence_value": f"{confidence_score}%",
        "low_high_range": [refined_rent * 0.94, refined_rent * 1.06],
        "zyla_raw_baseline": base_rent,
        "adjustments_applied": {
            "condition_mod": user_input.condition,
            "renovation_premium": user_input.is_renovated
        }
    }
5. Document Changes Checklist
[ ] Section 4 (Dev Plan): Replace RentCast API endpoints with Zyla Labs endpoints.

[ ] Section 5.2 (Waterfall): Remove Zyla as "Fallback" and set as "Primary."

[ ] Section 9 (Database): Add confidence_score and user_parameters_json columns to the rent_estimates table.

[ ] Validation Set: Add a test case for "Renovated vs. Non-Renovated" to ensure the +5-10% uplift logic triggers correctly.


Getty Images
6. Summary of Value-Add
By wrapping Zyla with this custom API, HouSmart moves from Data Retrieval to Data Intelligence. We are no longer just reporting what the web says; we are adjusting that data based on the specific condition of the property provided by the user, leading to a much higher conversion rate for serious real estate investors.