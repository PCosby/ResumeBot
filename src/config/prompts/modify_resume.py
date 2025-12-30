# config/prompts/modify_resume.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Dict, Any


# ---------- paths & loaders ----------

def _tpl_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def _compact(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _load_output_template_json() -> str:
    return _compact(_tpl_dir() / "modify_resume.json")


# ---------- SYSTEM PROMPT ----------

DEFAULT_SYSTEM = (
    "You tailor a single resume entry to a job. You are given structured job "
    "information, one base resume entry, and a JSON schema template. You rewrite "
    "only that entry so it aligns with the job while staying truthful.\n\n"

    "OUTPUT FORMAT (STRICT):\n"
    "- Output exactly ONE JSON object.\n"
    "- The object must match OUTPUT_TEMPLATE_JSON exactly.\n"
    "- Top level keys: section, name, title, dates, tools, bullets.\n"
    "- Do not add or remove top-level keys.\n\n"

    "SECTION AND METADATA RULES:\n"
    "- The 'section' field must match the provided section value.\n"
    "- 'name' must match BASE_ENTRY_JSON.name.\n"
    "- 'title' and 'dates' must stay consistent with BASE_ENTRY_JSON.\n"
    "- 'tools' may be lightly cleaned but not expanded with new tools.\n\n"

    "BULLET RULES:\n"
    "- All bullets must use an 'id' copied from one of BASE_ENTRY_JSON.bullets.\n"
    "- Never invent new bullet ids.\n"
    "- Maintain original relative ordering of ids.\n\n"

    "BULLET COUNT RULES (EXTREMELY STRICT):\n"
    "- For work experience entries (section == 'experience'):\n"
    "  - You MUST output NO MORE THAN 4 bullets.\n"
    "  - You MUST NOT output 5 or more bullets.\n"
    "- For project entries (section == 'projects'):\n"
    "  - You MUST output NO MORE THAN 3 bullets.\n"
    "  - You MUST NOT output 4 or more bullets.\n"
    "  - If at any point you produce 4 bullets for a project entry, you MUST "
    "merge or remove bullets until the final count is 3 or fewer.\n\n"

    "FAILURE MODE PREVENTION:\n"
    "- Before you respond, count the bullets you are about to output.\n"
    "- If section == 'experience' and you have more than 4 bullets, you MUST "
    "merge or remove bullets until there are at most 4.\n"
    "- If section == 'projects' and you have more than 3 bullets, you MUST "
    "merge or remove bullets until there are at most 3.\n"
    "- These bullet limits are non-negotiable and override any other instruction.\n\n"

    "BULLET SHORTENING RULES:\n"
    "- If the base entry has more bullets than allowed, COMBINE or MERGE bullets.\n"
    "- Keep only the strongest, most job-relevant content.\n"
    "- Merged bullets must stay truthful and must not invent new achievements.\n"
    "- When merging bullets, use the id of the earliest bullet involved.\n\n"

    "BULLET REWRITING RULES:\n"
    "- Rewrite bullet text to be ATS-optimized and job-aligned.\n"
    "- One sentence per bullet.\n"
    "- Aim for 23-29 words per bullet, max 32.\n"
    "- Use strong verbs and active voice.\n\n"

    "QUALITY CHECK BEFORE RESPONDING:\n"
    "- If section == 'experience': bullet count must be <= 4.\n"
    "- If section == 'projects': bullet count must be <= 3.\n"
    "- If the count is too high, you MUST fix it before responding.\n"
    "- Output EXACTLY one JSON object, nothing else.\n"
)


# ---------- public API ----------

def build_prompt(
    job_info_json: str,
    section: str,
    base_entry: Dict[str, Any],
) -> Tuple[str, str]:

    if section not in {"experience", "projects"}:
        raise ValueError(f"section must be 'experience' or 'projects', got {section!r}")

    base_entry_copy = dict(base_entry)
    base_entry_copy["section"] = section

    base_entry_str = json.dumps(
        base_entry_copy,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    output_template_str = _load_output_template_json()
    base_bullet_count = len(base_entry.get("bullets", []))

    user = (
        "JOB_INFORMATION_JSON:\n"
        f"{job_info_json.strip()}\n\n"
        "SECTION_FOR_ENTRY:\n"
        f"{section}\n\n"
        "BASE_ENTRY_BULLET_COUNT:\n"
        f"{base_bullet_count}\n\n"
        "BASE_ENTRY_JSON:\n"
        f"{base_entry_str}\n\n"
        "OUTPUT_TEMPLATE_JSON:\n"
        f"{output_template_str}\n\n"
        "TASK:\n"
        "- Rewrite only this entry.\n"
        "- Follow ALL SYSTEM RULES.\n"
        "- Respect the bullet max for this section.\n"
        "- Return ONE JSON object only."
    )

    return DEFAULT_SYSTEM, user