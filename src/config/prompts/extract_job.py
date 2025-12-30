from __future__ import annotations
import json
from pathlib import Path
from typing import Tuple


def _load_base_keys() -> str:
    """
    Load templates/extract_job.json and return a compact JSON string for embedding.
    """
    config = Path(__file__).resolve().parents[1]
    tpl_path = config / "templates" / "extract_job.json"
    obj = json.loads(tpl_path.read_text(encoding="utf-8"))

    # Compact representation for the model (no extra whitespace)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def build_prompt(selected_string: str) -> Tuple[str, str]:
    """
    Given raw selected job-posting text, produce (system_msg, user_msg).

    The model is instructed to:
    - Extract only resume-relevant information.
    - Fill ALL keys defined in templates/extract_job.json.
    - Return a single valid JSON object that matches that schema exactly.
    """
    raw_base_keys = _load_base_keys()  # compact JSON string

    # Also pretty-print for display in the prompt (helps the model see structure)
    try:
        base_keys_obj = json.loads(raw_base_keys)
    except Exception:
        base_keys_obj = {}
    base_keys_pretty = json.dumps(base_keys_obj, ensure_ascii=False, indent=2)

    system = (
        "You are a strict information extraction assistant. "
        "Your job is to read a job posting and extract ONLY resume-relevant details.\n\n"

        "You MUST return a single VALID JSON object that EXACTLY matches this base schema:\n"
        f"{base_keys_pretty}\n\n"

        "SCHEMA RULES:\n"
        "- Do NOT rename, remove, or add top-level keys.\n"
        "- Every key from the base schema must be present in the output.\n"
        "- For string fields, use a JSON string (not null). Use an empty string \"\" only if there is truly no information.\n"
        "- For list fields, always return a JSON array. Use an empty array [] only if there is truly no information.\n"
        "- Do NOT include comments, trailing commas, or any text outside the JSON object.\n\n"

        "FIELD-SPECIFIC GUIDANCE:\n"
        "- company_name: The hiring organization as written in the posting. "
        "If it is clearly a recruiting agency posting for a client, prefer the client company name.\n"
        "- target_title: The primary job title in the posting. Use the exact text if possible.\n"
        "- seniority_level: One of: \"intern\", \"new-grad\", \"junior\", \"mid\", \"senior\", \"staff\", \"principal\", "
        "or \"unspecified\" if the level is not clear.\n"
        "- location: The primary location descriptor (e.g., \"New York, NY\", \"Remote (US)\", \"Hybrid - SF Bay Area\").\n"
        "- work_style: One of: \"onsite\", \"hybrid\", \"remote\", or \"unspecified\".\n"
        "- role_summary: 1-2 sentences describing what this role does, in your own words, "
        "combining domain, responsibilities, and impact. This is natural language.\n\n"

        "- domain_keywords: 3-8 short tokens capturing the domain/industry or problem space "
        "(e.g., [\"fintech\", \"payments\", \"healthcare\", \"LLM infrastructure\"]).\n"
        "- skills_core: 5-15 REQUIRED skills or core technologies the role heavily emphasizes. "
        "Short tokens only (1-4 words each), no full sentences.\n"
        "- skills_secondary: 3-10 NICE-TO-HAVE or \"preferred\" skills. Same short-token format.\n"
        "- tools_technologies: 5-20 concrete named tools, frameworks, platforms, databases, clouds, or services "
        "(e.g., \"React\", \"PostgreSQL\", \"Docker\", \"Kubernetes\", \"PyTorch\").\n\n"

        "- responsibilities_core: 4-10 key responsibilities rewritten as short phrases or sentence fragments "
        "that describe what the engineer will actually do (e.g., \"Design and implement LLM-backed APIs\").\n"
        "- responsibilities_secondary: 2-8 additional or optional responsibilities, if present.\n\n"

        "- keywords_exact: 8-25 exact phrases copied VERBATIM from the posting that are important for ATS matching. "
        "Examples: specific frameworks, compliance terms, product names, or repeated phrases. "
        "These MUST be literal substrings from the job description.\n\n"

        "GENERAL POLICIES:\n"
        "- Prefer concise tokens (≈1-4 words) in array fields, not full sentences.\n"
        "- Preserve important domain terms and proper nouns as written (e.g., \"SOC 2\", \"HIPAA\", \"retrieval-augmented generation\").\n"
        "- Only leave a field empty (\"\" or []) if the posting provides no signal and it cannot be reasonably inferred.\n"
        "- Do NOT invent technologies, domains, or requirements that are not implied by the posting.\n"
        "- Your final answer MUST be only the JSON object, with double-quoted keys and strings, and no extra text."
    )

    user = (
        "JOB POSTING:\n"
        "------------\n"
        f"{selected_string.strip()}\n\n"
        "Task: Extract the job information according to the SCHEMA RULES and FIELD-SPECIFIC GUIDANCE above.\n"
        "Return ONLY the JSON object that matches the base schema."
    )

    return system, user
