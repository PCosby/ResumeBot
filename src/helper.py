from __future__ import annotations

import os
from pathlib import Path
import webbrowser
import json
import yaml

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

import ollama_client
import config.prompts.extract_job as extract_job
import config.prompts.modify_resume as modify_resume
import config.prompts.make_cover_letter as make_cover_letter
import config.prompts.modify_skills as modify_skills

import config.writer.finalize_resume as finalize_resume
import config.writer.write_final as write_final


def write_to_file(content: str, file_name: str) -> None:
    out_path = Path(f"../out/{file_name}").resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def extract_job_info(selected_text: str) -> str:
    system_msg, user_msg = extract_job.build_prompt(selected_text)
    response = ollama_client.run(system=system_msg, user=user_msg)

    write_to_file(response, "job_info.json")
    return response


BASE_RESUME_PATH = (
    Path(__file__).resolve().parent / "config" / "templates" / "base_resume.yml"
)


def _load_base_resume_yaml() -> dict:
    text = BASE_RESUME_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _modify_skills_info(job_info: str) -> str:
    """
    Update ONLY the Programming Languages and Technologies lists using LLM-based
    alignment with the target job posting.

    - Loads the canonical base resume YAML.
    - Extracts the base skills section.
    - Builds a skills-only modification prompt using modify_skills.build_modify_skills_prompt().
    - Calls the LLM once.
    - Returns a JSON object with { "skills": { ... } }.

    Output is also saved to ../out/modified_skills.json.
    """
    base_resume = _load_base_resume_yaml()
    base_skills = base_resume.get("skills", {})

    # Build system + user messages
    system_msg, user_msg = modify_skills.build_modify_skills_prompt(
        base_skills=base_skills, job_extract=json.loads(job_info)
    )

    # Call LLM
    response = ollama_client.run(system=system_msg, user=user_msg)

    # Should return {"skills": {...}}
    skills_obj = json.loads(response)

    # Persist result
    write_to_file(
        json.dumps(skills_obj, ensure_ascii=False, indent=2), "modified_skills.json"
    )

    return json.dumps(skills_obj, ensure_ascii=False)


def modify_resume_info(job_info: str) -> str:
    """
    Generate a modified resume JSON by tailoring EACH entry separately.

    - Reads the canonical base resume from base_resume.yml.
    - For each entry in 'experience' and 'projects', calls the LLM once using
      config.prompts.modify_resume.build_prompt(job_info, section, base_entry).
    - Aggregates the per-entry outputs into a single JSON object representing
      the modified resume.

    For now:
      - No verification/repair is done.
      - 'basics', 'education', 'skills' are copied through unchanged from YAML.
    """
    base_resume = _load_base_resume_yaml()

    modified_resume: dict[str, object] = {}

    for section in ("basics", "education"):
        modified_resume[section] = base_resume.get(section, {})

    # Sections we will tailor entry-by-entry
    modified_resume["experience"] = []
    modified_resume["projects"] = []

    for section in ("experience", "projects"):
        entries = base_resume.get(section, []) or []
        for entry in entries:
            system_msg, user_msg = modify_resume.build_prompt(
                job_info_json=job_info,
                section=section,
                base_entry=entry,
            )
            entry_response = ollama_client.run(system=system_msg, user=user_msg)

            # Assume the model returns a single JSON object for this entry.
            # No verification / repair here on purpose.
            entry_obj = json.loads(entry_response)
            entry_obj["tools"] = entry.get("tools", [])

            modified_resume[section].append(entry_obj)
            print(
                f"[INFO] Tailored {section} entry {len(modified_resume[section])}/{len(entries)} added.",
                flush=True,
            )

    modified_skills = json.loads(_modify_skills_info(job_info))
    modified_resume["skills"] = modified_skills.get("skills", {})

    result_str = json.dumps(modified_resume, ensure_ascii=False, indent=2)

    write_to_file(result_str, "modified_resume.json")
    return result_str


def generate_cover_letter(job_info_json: str, resume_info: str) -> str:
    system_msg, user_msg = make_cover_letter.build_prompt(job_info_json, resume_info)
    response = ollama_client.run(system=system_msg, user=user_msg)
    response_str = json.loads(response)["data"]

    write_to_file(response_str, "cover_letter.md")
    return response_str


def finalize_resume_info(modified_resume_info: str) -> str:
    response = finalize_resume.to_json_resume(modified_resume_info)

    write_to_file(response, "final_resume.json")
    return response


def compile_resume_pdf(json_resume_text: str) -> Path:
    return write_final.json_resume_to_pdf(
        json_resume_text,
        Path("../out/resume.pdf").resolve(),
        theme=os.getenv("RESUME_THEME"),  # or None, or another installed theme name
    )


def compile_cover_letter_pdf(letter_text: str) -> Path:
    return write_final.markdown_to_pdf(
        letter_text, Path("../out/cover_letter.pdf").resolve()
    )


def open_pdf(path: Path) -> None:
    webbrowser.open_new_tab(path.as_uri())
