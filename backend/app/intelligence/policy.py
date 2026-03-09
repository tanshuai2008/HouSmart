import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Model config
# LLM 2: more powerful model for legal/policy reasoning
POLICY_MODEL     = os.getenv("GEMINI_POLICY_MODEL", "gemini-3-flash-preview")
MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_POLICY_MAX_TOKENS", "2000"))
TEMPERATURE       = float(os.getenv("GEMINI_POLICY_TEMPERATURE", "0.1"))  # very low = precise

# Supported states for policy analysis
SUPPORTED_POLICY_STATES = ["TX", "WA", "NC"]

# Top-k chunks to retrieve per query category
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Policy query categories — used for pgVector similarity search
POLICY_QUERY_CATEGORIES = [
    "eviction process and timelines",
    "rent control and rent increase limits",
    "landlord notice requirements",
    "security deposit rules",
    "landlord licensing and registration",
    "ADU allowance rules",
    "short-term rental restrictions",
]

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_POLICY_PROMPT_PATH = _PROMPTS_DIR / "policy_v1.txt"


def run_policy(
    evaluation_id: str,
    state_code: str,
    db_session=None,
) -> dict:
    """
    Run the policy analysis stage for a supported state.

    Args:
        evaluation_id: The evaluation ID (used for cache key lookup).
        state_code:    Two-letter state code (e.g. "TX").
        db_session:    Optional SQLAlchemy/asyncpg session for RAG retrieval.
                       If None, falls back to mock chunks for local dev.

    Returns:
        Structured policy analysis dict, or empty dict if state not supported.
    """
    if state_code not in SUPPORTED_POLICY_STATES:
        logger.info("Policy stage skipped — state %s not supported.", state_code)
        return {}

    logger.info("Running policy analysis for evaluation_id=%s state=%s", evaluation_id, state_code)

    #1. Retrieve RAG chunks
    chunks = _retrieve_policy_chunks(state_code, db_session)
    if not chunks:
        logger.warning("No policy chunks found for state %s — skipping policy stage.", state_code)
        return {}

    #2. Build prompt
    system_prompt = _load_system_prompt()
    user_prompt   = _build_policy_prompt(state_code, chunks)

    #3. Call Gemini Pro
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=POLICY_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
            ),
        )
        raw_text  = response.text

        usage = getattr(response, "usage_metadata", None)
        input_tokens  = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

    except Exception as exc:
        logger.error("Policy LLM call failed: %s", exc)
        return {}  # Non-fatal — policy is optional; recommendation proceeds without it

    #4. Parse
    try:
        parsed = _parse_json_response(raw_text)
    except ValueError as exc:
        logger.error("Failed to parse policy LLM response: %s", exc)
        return {}

    parsed["_meta"] = {
        "model":         POLICY_MODEL,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "chunks_used":   len(chunks),
    }

    return parsed


def _retrieve_policy_chunks(state_code: str, db_session=None) -> list[dict]:
    """
    Retrieve relevant policy document chunks from pgVector.

    In production: runs cosine similarity search over policy_embeddings table
    for each POLICY_QUERY_CATEGORIES query, deduplicates, and returns top-k chunks.

    In dev (no db_session): returns empty list (policy stage skipped gracefully).
    """
    if db_session is None:
        logger.warning("No DB session provided — RAG retrieval unavailable in dev mode.")
        return []

    # ── Production pgVector retrieval ─────────────────────────────────────
    # NOTE: Replace this block with your actual pgVector query helper once
    # the policy_embeddings table is populated and the embedding model is set up.
    #
    # Example query (using asyncpg + pgvector):
    #
    #   embedding = embed_text(query_text)   # your embedding function
    #   rows = await db_session.fetch("""
    #       SELECT pe.chunk_text, pd.title, pd.category
    #       FROM policy_embeddings pe
    #       JOIN policy_documents pd ON pe.policy_document_id = pd.id
    #       WHERE pd.state_code = $1
    #       ORDER BY pe.embedding <=> $2
    #       LIMIT $3
    #   """, state_code, embedding, RAG_TOP_K)
    #   return [{"text": r["chunk_text"], "source": r["title"], "category": r["category"]} for r in rows]

    all_chunks: list[dict] = []

    for category in POLICY_QUERY_CATEGORIES:
        try:
            # Placeholder — swap in real pgVector query here
            chunks = _pgvector_similarity_search(
                db_session=db_session,
                state_code=state_code,
                query_text=category,
                top_k=RAG_TOP_K,
            )
            all_chunks.extend(chunks)
        except Exception as exc:
            logger.warning("RAG retrieval failed for category '%s': %s", category, exc)

    # Deduplicate by chunk text
    seen: set[str] = set()
    unique_chunks: list[dict] = []
    for chunk in all_chunks:
        key = chunk.get("text", "")[:100]
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)

    return unique_chunks


def _pgvector_similarity_search(
    db_session,
    state_code: str,
    query_text: str,
    top_k: int,
) -> list[dict]:
    """
    Stub for pgVector similarity search.
    Replace with real implementation once embedding model + table are ready.
    """
    # TODO: implement with actual pgvector + embedding model
    return []


def _build_policy_prompt(state_code: str, chunks: list[dict]) -> str:
    """Format the retrieved chunks into a structured user prompt for the policy LLM."""
    chunks_text = "\n\n".join(
        f"[Document: {c.get('source', 'Unknown')} | Category: {c.get('category', 'General')}]\n{c.get('text', '')}"
        for i, c in enumerate(chunks)
    )

    return f"""State: {state_code}

## Retrieved Policy Documents
{chunks_text}

Analyze these documents and return the structured policy JSON as instructed."""


def _load_system_prompt() -> str:
    try:
        return _POLICY_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("policy_v1.txt not found at %s", _POLICY_PROMPT_PATH)
        raise


def _parse_json_response(raw_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Policy LLM returned invalid JSON: {exc}") from exc