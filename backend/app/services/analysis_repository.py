from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.supabase_client import supabase


class AnalysisRepository:
    @staticmethod
    def _to_date_only(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text[:10]

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_correlation_percentage(value: Any) -> Optional[float]:
        score = AnalysisRepository._to_float(value)
        if score is None:
            return None
        # RentCast commonly returns correlations in [0, 1]; persist as percentage.
        if 0.0 <= score <= 1.0:
            score *= 100.0
        return round(score, 1)

    @staticmethod
    def _is_active_status(value: Any) -> bool:
        if value is None:
            return False
        status = str(value).strip().lower()
        return status in {"active", "for_rent", "for rent"}

    @staticmethod
    def _normalized_listing_status(value: Any) -> str:
        return "active" if AnalysisRepository._is_active_status(value) else "inactive"

    @staticmethod
    def _days_on_market(*, listed_date: Any, explicit_days: Any) -> Optional[int]:
        try:
            if explicit_days is not None:
                return max(int(explicit_days), 0)
        except (TypeError, ValueError):
            pass

        date_text = AnalysisRepository._to_date_only(listed_date)
        if not date_text:
            return None

        try:
            listed = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            return None

        return max((datetime.now(timezone.utc).date() - listed).days, 0)

    @staticmethod
    def upsert_user_property(
        *,
        user_id: str,
        address: str,
        normalized_address: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        rent: Optional[float],
        rent_currency: Optional[str],
        property_type: Optional[str],
        bedrooms: Optional[int],
        bathrooms: Optional[float],
        square_footage: Optional[int],
        year_built: Optional[int],
        last_sale_date: Optional[str],
        last_sale_price: Optional[float],
        state_fips: Optional[str],
        county_fips: Optional[str],
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
            "address": address,
            "normalized_address": normalized_address,
            "latitude": latitude,
            "longitude": longitude,
            "rent": rent,
            "rent_currency": rent_currency or "USD",
            "property_type": property_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "square_footage": square_footage,
            "year_built": year_built,
            "last_sale_date": last_sale_date,
            "last_sale_price": last_sale_price,
            "state_fips": state_fips,
            "county_fips": county_fips,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        existing = (
            supabase.table("user_properties")
            .select("property_id")
            .eq("user_id", user_id)
            .ilike("address", address)
            .limit(1)
            .execute()
        )
        rows = existing.data or []
        if rows:
            response = (
                supabase.table("user_properties")
                .update(payload)
                .eq("property_id", rows[0]["property_id"])
                .execute()
            )
            return response.data[0]

        response = supabase.table("user_properties").insert(payload).execute()
        return response.data[0]

    @staticmethod
    def get_user_property(*, user_id: str, address: str) -> Optional[dict[str, Any]]:
        response = (
            supabase.table("user_properties")
            .select("*")
            .eq("user_id", user_id)
            .ilike("address", address)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    @staticmethod
    def get_user_property_by_id(*, user_id: str, property_id: str) -> Optional[dict[str, Any]]:
        response = (
            supabase.table("user_properties")
            .select("*")
            .eq("user_id", user_id)
            .eq("property_id", property_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    @staticmethod
    def list_recent_user_properties(*, user_id: str, limit: int = 3) -> list[dict[str, Any]]:
        response = (
            supabase.table("user_properties")
            .select("property_id,address")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    @staticmethod
    def create_run(*, property_id: str) -> dict[str, Any]:
        response = (
            supabase.table("property_analysis_runs")
            .insert({"property_id": property_id, "status": "running"})
            .execute()
        )
        return response.data[0]

    @staticmethod
    def set_run_status(
        *,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if error_message:
            payload["error_message"] = error_message

        (
            supabase.table("property_analysis_runs")
            .update(payload)
            .eq("run_id", run_id)
            .execute()
        )

    @staticmethod
    def upsert_property_facts(*, property_id: str, run_id: str, payload: dict[str, Any]) -> None:
        row = {
            "property_id": property_id,
            "run_id": run_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        (
            supabase.table("property_facts")
            .upsert(row, on_conflict="run_id")
            .execute()
        )

    @staticmethod
    def replace_comparables(*, property_id: str, run_id: str, comparables: list[dict[str, Any]]) -> None:
        (
            supabase.table("comparable_properties")
            .delete()
            .eq("property_id", property_id)
            .eq("run_id", run_id)
            .execute()
        )

        if not comparables:
            return

        ranked = sorted(
            comparables,
            key=lambda comp: (
                AnalysisRepository._normalize_correlation_percentage(
                    comp.get("correlation_score")
                    or comp.get("correlationScore")
                    or comp.get("correlation")
                )
                or 0.0
            ),
            reverse=True,
        )
        ranked = sorted(
            ranked,
            key=lambda comp: not AnalysisRepository._is_active_status(comp.get("status")),
        )
        top_five = ranked[:5]

        rows = []
        for comp in top_five:
            correlation_score = AnalysisRepository._normalize_correlation_percentage(
                comp.get("correlation_score") or comp.get("correlationScore") or comp.get("correlation")
            )
            listed_date = AnalysisRepository._to_date_only(comp.get("listed_date") or comp.get("listedDate"))
            rows.append({
                "property_id": property_id,
                "run_id": run_id,
                "address": comp.get("address") or comp.get("formattedAddress") or comp.get("formatted_address"),
                "property_type": comp.get("property_type") or comp.get("propertyType"),
                "bedrooms": comp.get("bedrooms"),
                "bathrooms": comp.get("bathrooms"),
                "square_footage": comp.get("square_footage") or comp.get("squareFootage"),
                "year_built": comp.get("year_built") or comp.get("yearBuilt"),
                "status": AnalysisRepository._normalized_listing_status(comp.get("status")),
                "rental_price": comp.get("price") or comp.get("rent") or comp.get("rental_price"),
                "listed_type": comp.get("listed_type") or comp.get("listingType"),
                "listed_date": listed_date,
                "days_on_market": AnalysisRepository._days_on_market(
                    listed_date=listed_date,
                    explicit_days=comp.get("days_on_market") or comp.get("daysOnMarket"),
                ),
                "distance": comp.get("distance"),
                "correlation_score": correlation_score,
            })

        supabase.table("comparable_properties").insert(rows).execute()

    @staticmethod
    def upsert_user_scores(
        *,
        user_id: str,
        property_id: str,
        run_id: str,
        payload: dict[str, Any],
    ) -> None:
        row = {
            "user_id": user_id,
            "property_id": property_id,
            "run_id": run_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        (
            supabase.table("property_user_scores")
            .upsert(row, on_conflict="user_id,property_id,run_id")
            .execute()
        )

    @staticmethod
    def get_run(*, run_id: str) -> Optional[dict[str, Any]]:
        response = (
            supabase.table("property_analysis_runs")
            .select("*")
            .eq("run_id", run_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    @staticmethod
    def get_dashboard_payload(*, user_id: str, property_id: str) -> dict[str, Any]:
        run_resp = (
            supabase.table("property_analysis_runs")
            .select("*")
            .eq("property_id", property_id)
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        run_rows = run_resp.data or []
        latest_run = run_rows[0] if run_rows else None

        facts = None
        scores = None
        comparables: list[dict[str, Any]] = []

        if latest_run:
            run_id = latest_run["run_id"]
            facts_resp = (
                supabase.table("property_facts")
                .select("*")
                .eq("run_id", run_id)
                .limit(1)
                .execute()
            )
            facts_rows = facts_resp.data or []
            facts = facts_rows[0] if facts_rows else None

            score_resp = (
                supabase.table("property_user_scores")
                .select("*")
                .eq("run_id", run_id)
                .eq("property_id", property_id)
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            score_rows = score_resp.data or []
            scores = score_rows[0] if score_rows else None

            comps_resp = (
                supabase.table("comparable_properties")
                .select("*")
                .eq("run_id", run_id)
                .eq("property_id", property_id)
                .execute()
            )
            comparables = comps_resp.data or []

        prop_resp = (
            supabase.table("user_properties")
            .select("*")
            .eq("property_id", property_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        prop_rows = prop_resp.data or []
        prop = prop_rows[0] if prop_rows else None

        return {
            "property": prop,
            "latest_run": latest_run,
            "facts": facts,
            "scores": scores,
            "comparables": comparables,
        }
