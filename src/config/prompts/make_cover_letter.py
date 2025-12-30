from __future__ import annotations
from datetime import date
from typing import Tuple


def build_prompt(
    job_info_json: str,
    resume_info: str,
    today: date | None = None,
) -> Tuple[str, str]:
    """
    Build (system_msg, user_msg) to generate a tailored Markdown cover letter.

    - job_info_json: JSON string from extract_job step.
    - resume_info:   JSON string of RESUME_JSON (final resume).
    - today:         Optional date override; defaults to date.today().
    """
    if today is None:
        today = date.today()

    date_str = today.strftime("%B %d, %Y")

    # -------------------------
    # SYSTEM MESSAGE
    # -------------------------
    system_msg = (
        "You are an expert cover-letter writer that produces polished, truthful, "
        "ATS-aware Markdown cover letters.\n\n"

        "OUTPUT CONSTRAINTS (STRICT):\n"
        "- Return ONLY one valid JSON object with a single top-level key 'data'.\n"
        "- The value of 'data' must be a COMPLETE cover letter in Markdown.\n"
        "- Use real newline characters. No code fences.\n"
        "- Do NOT output placeholder text like '[Name]' or '[Date]'.\n\n"

        "HEADER FORMAT RULES:\n"
        "- Build a clean Markdown header using RESUME_JSON.basics.\n"
        "- First line: '# **<candidate name>**'\n"
        "- Then each contact field on its own line, with a blank line between each.\n\n"
        "- After the final contact line AND its trailing blank line, output exactly:\n"
        "      ---\n"
        "- Then add ONE blank line.\n"
        "- Then output the date line (CURRENT_DATE) on its own line.\n"
        "- IMPORTANT: Never place a horizontal rule after the date. Only one rule exists, above the date.\n\n"

        "EMPLOYER + GREETING:\n"
        "- After the date line, output employer information from JOB_INFORMATION_JSON.\n"
        "- Then ALWAYS use exactly:\n"
        "      Dear Hiring Team,\n"
        "- Never use recruiter names, manager names, or multiple greetings.\n\n"

        "CONTENT RULES:\n"
        "- Produce 3-4 concise paragraphs using active voice.\n"
        "- No lists, tables, or images.\n"
        "- Keep everything truthful to RESUME_JSON.\n"
        "- Mention Roblox work only as independent, self-published.\n\n"

        "STRUCTURE TO FOLLOW (EXACT ORDER):\n"
        "1. Header block.\n"
        "2. One horizontal rule ('---').\n"
        "3. One blank line.\n"
        "4. Date line using CURRENT_DATE.\n"
        "5. Employer block.\n"
        "6. 'Dear Hiring Team,' greeting.\n"
        "7. 3-4 short paragraphs.\n"
        "8. Signature with the candidate's name.\n\n"

        "QUALITY CHECK:\n"
        "- Ensure there is only ONE horizontal rule and it appears ONLY above the date.\n"
        "- Ensure the date is NOT surrounded by rules.\n"
        "- Ensure greeting is exactly 'Dear Hiring Team,'.\n"
        "- Ensure ONLY one JSON object is returned.\n"
    )

    # -------------------------
    # USER MESSAGE
    # -------------------------
    user_msg = (
        "CURRENT_DATE (use exactly for date line):\n"
        f"{date_str}\n\n"

        "JOB_INFORMATION_JSON (verbatim):\n"
        f"{job_info_json.strip()}\n\n"

        "RESUME_JSON (verbatim):\n"
        f"{resume_info}\n\n"

        "ADDITIONAL CONTEXT:\n"
        "- The candidate has already graduated college.\n"
        "- 'Jump' is independently developed and self-published on the Roblox platform.\n\n"

        "TASK:\n"
        "- Write a truthful Markdown cover letter following ALL SYSTEM RULES.\n"
        "- Use CURRENT_DATE exactly.\n"
        "- Always use the greeting 'Dear Hiring Team,'.\n"
        "- Ensure exactly ONE horizontal rule appears and NEVER after the date.\n"
        "- Return ONLY one JSON object with key 'data'.\n"
    )

    return system_msg, user_msg
