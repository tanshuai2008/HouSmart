import json
import logging
import os
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SUPPORTED_POLICY_STATES = ["TX", "WA", "NC"]

POLICY_MODEL    = os.getenv("GEMINI_POLICY_MODEL", "gemini-3-flash-preview")
RAG_TOP_K       = int(os.getenv("RAG_TOP_K", "5"))
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")

POLICY_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "policy_v1.txt")


def run_policy(evaluation_id: str, state_code: str, db_session=None) -> dict:
    state = state_code
    """
    Fetch relevant policy documents and generate a policy summary for the given state.

    Returns:
        dict with 'policy_summary' (str) and '_meta' (usage info)
        or empty dict if no documents found or policy stage skipped
    """
    if not db_session:
        logger.info("No DB session provided — RAG retrieval unavailable in dev mode.")
        return {}

    # ── 1. Try pgVector RAG (Phase 13) ────────────────────────────────────
    chunks = _pgvector_similarity_search(db_session, state)

    # ── 2. Fallback: simple text fetch ────────────────────────────────────
    if not chunks:
        chunks = _simple_text_fetch(db_session, state)

    if not chunks:
        logger.info("No policy chunks found for state %s — skipping policy stage.", state)
        return {}

    logger.info("Found %d policy chunk(s) for state %s — running policy LLM.", len(chunks), state)

    # ── 3. Build context string ────────────────────────────────────────────
    context = "\n\n---\n\n".join(
        f"[{c.get('title', 'Policy Document')}]\n{c.get('content', '')}"
        for c in chunks
    )

    # ── 4. Call Gemini policy model ────────────────────────────────────────
    return _call_policy_llm(evaluation_id, state, context)


def _simple_text_fetch(db_session, state: str) -> list:
    """
    Fallback: fetch policy documents directly by state from policy_documents table.
    Used when pgVector embeddings are not yet populated.
    """
    try:
        resp = db_session.table("policy_documents") \
            .select("title, content, source, effective_date") \
            .eq("state", state) \
            .limit(RAG_TOP_K) \
            .execute()
        return resp.data or []
    except Exception as exc:
        logger.warning("Simple policy fetch failed for state %s: %s", state, exc)
        return []


def _pgvector_similarity_search(db_session, state: str) -> list:
    """
    Phase 13 — pgVector RAG similarity search.
    Requires policy_embeddings table to be populated.
    Returns empty list until embeddings are ready.
    """
    # TODO (Phase 13): Replace with real pgVector query:
    # SELECT content, title FROM policy_embeddings
    # WHERE state = $state
    # ORDER BY embedding <=> $query_vector
    # LIMIT RAG_TOP_K
    return []


def _call_policy_llm(evaluation_id: str, state: str, context: str) -> dict:
    """Call Gemini to summarize policy implications for the investor."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — skipping policy LLM call.")
        return {}

    try:
        system_prompt = _load_prompt()
        user_message  = (
            f"State: {state}\n\n"
            f"Policy Documents:\n{context}\n\n"
            f"Summarize the key policy implications for a real estate investor "
            f"purchasing a property in {state}. Focus on tax implications, "
            f"rental regulations, and any recent legislative changes that affect ROI."
        )

        client   = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=POLICY_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                max_output_tokens=2000,
                response_mime_type="application/json",
            ),
        )

        summary = response.text.strip() if response.text else ""
        usage   = response.usage_metadata

        logger.info("Policy LLM call complete — evaluation_id=%s tokens=%s",
                    evaluation_id, getattr(usage, "total_token_count", "?"))

        return {
            "policy_summary": summary,
            "_meta": {
                "model":         POLICY_MODEL,
                "input_tokens":  getattr(usage, "prompt_token_count", 0),
                "output_tokens": getattr(usage, "candidates_token_count", 0),
                "state":         state,
                "chunks_used":   1,
            }
        }

    except Exception as exc:
        logger.error("Policy LLM call failed for evaluation_id=%s: %s", evaluation_id, exc)
        return {}


def _load_prompt() -> str:
    try:
        with open(POLICY_PROMPT_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "You are a real estate policy expert. "
            "Summarize the key policy implications for investors based on the provided documents. "
            "Be concise, factual, and focused on investment impact."
        )