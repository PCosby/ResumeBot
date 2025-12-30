# config/prompts/modify_skills.py

from __future__ import annotations

import json
from typing import Dict, Any, Tuple


def _compact(obj: Any) -> str:
    """
    Compact an object into a single-line JSON string for embedding in prompts.
    """
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# ---------------- SYSTEM PROMPT ----------------

DEFAULT_SYSTEM = """
You update the SKILLS section of a software engineer's resume.

You must ONLY modify two lists:
  - skills.programming_languages
  - skills.technologies

Your goal:
  - Add relevant skills from the job posting.
  - Remove irrelevant, outdated, generic, or domain-mismatched items.
  - STRICTLY allow ONLY single-word technologies. NO multi-word items.

----------------
ABSOLUTE HARD RULES
----------------

1) **ONLY SINGLE-WORD TECHNOLOGIES ALLOWED**
   - A valid technology must contain NO SPACES.
   - If a technology contains one or more spaces, you MUST remove it.
   - You MUST NOT add any multi-word technologies under any circumstance.
   - Even real tools like “Spring Boot”, “Visual Studio Code”, “Google BigQuery”
     MUST NOT appear because they contain spaces.

2) **NO GENERIC CATEGORIES**
   These must NEVER appear:
     - vector databases
     - graph databases
     - cloud platforms
     - data pipelines
     - search indexes
     - ranking pipeline
     - embeddings and retrieval
     - AI infrastructure
     - merchant integration
     - commerce layer
     - workflow orchestration
     - CRMs
     - ATS platforms
     - analytics providers
     - ANY multi-word phrase of any type

3) **PROGRAMMING LANGUAGES**
   - Must be real languages: Python, Java, C++, SQL, Rust, Go, Lua, etc.
   - These are allowed even if stylized (“C++”) because they contain no spaces.

4) **TECHNOLOGIES (STRICT DEFINITION)**
   - Must be a single token with no whitespace.
   - Examples of VALID items:
       Docker, Kubernetes, Snowflake, MySQL, PostgreSQL, Nginx, Redis, Kafka
   - Examples of INVALID items:
       Spring Boot, Google BigQuery, GitHub Actions, AWS Glue,
       Visual Studio Code, Pinecone DB, FAISS Search, LangChain Agents
     → All invalid because they contain whitespace.

5) **MATCH THE CANDIDATE'S FIELD**
   - Remove irrelevant domains (e.g., RobloxStudio if job is enterprise data).
   - Keep core SWE / backend / data / infra stack items when single-word.

6) **DEDUPLICATION AND CANONICAL NAMES**
   - Use canonical forms:
       PostgreSQL (not Postgres)
       Node.js (without variants)
   - A canonical form must still be a **single word** to be allowed.

----------------
OUTPUT FORMAT (STRICT)
----------------

You MUST output exactly ONE JSON object:

{
  "skills": {
    "programming_languages": [...],
    "technologies": [...]
  }
}

Rules for output:
- programming_languages must be present.
- technologies must be present.
- EVERY technology must be a single word.
- REMOVE any item that contains spaces.
- REMOVE any item that resembles a concept instead of a tool.
- No commentary or explanations.
"""




# ---------------- PROMPT BUILDER ----------------

def build_modify_skills_prompt(
    base_skills: Dict[str, Any],
    job_extract: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Build the (system, user) messages for updating the Programming Languages /
    Technologies section using a structured job extract.

    Parameters
    ----------
    base_skills:
        A dict that at least contains:
        {
          "skills": {
            "programming_languages": [...],
            "technologies": [...]
          }
        }

    job_extract:
        The JSON produced by the extract_job step, matching extract_job.json:
        {
          "company_name": "",
          "target_title": "",
          "seniority_level": "",
          "location": "",
          "work_style": "",
          "role_summary": "",
          "domain_keywords": [],
          "skills_core": [],
          "skills_secondary": [],
          "tools_technologies": [],
          "responsibilities_core": [],
          "responsibilities_secondary": [],
          "keywords_exact": []
        }

    Returns
    -------
    (system, user): Tuple[str, str]
        system: DEFAULT_SYSTEM instructions.
        user:   Concrete task with embedded base skills + job extract.
    """
    base_skills_str = _compact(base_skills)
    job_extract_str = _compact(job_extract)

    user = (
      "You are updating ONLY the Programming Languages and Technologies section of the "
      "candidate's resume. Your job is to strictly enforce ALL SYSTEM RULES.\n\n"
      "BASE_SKILLS_JSON:\n"
      "-----------------\n"
      f"{base_skills_str}\n\n"
      "JOB_EXTRACT_JSON:\n"
      "-----------------\n"
      f"{job_extract_str}\n\n"
      "TASK:\n"
      "- Start from the existing skills in BASE_SKILLS_JSON.\n"
      "- Update skills.programming_languages and skills.technologies based on the job posting.\n"
      "- You MUST remove any technology containing one or more spaces.\n"
      "- You MUST NOT add any multi-word technologies under any circumstance.\n"
      "- You MUST only keep single-word, concrete tools (e.g., Docker, MySQL, Snowflake, Kafka).\n"
      "- Remove all conceptual, generic, domain, or multi-word phrases.\n"
      "- Normalize and deduplicate all items.\n"
      "- Output EXACTLY one JSON object in the required schema."
  )

    return DEFAULT_SYSTEM, user
