from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Tuple, Optional


# ---------- helpers ----------

MONTH_MAP = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}


def _parse_city_region(location: str) -> Tuple[str, str]:
    """
    Convert 'North Brunswick, NJ' -> ('North Brunswick', 'NJ').
    If parsing fails, put everything in city and leave region empty.
    """
    if not isinstance(location, str):
        return "", ""
    parts = [p.strip() for p in location.split(",") if p.strip()]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    # Only keep first two parts; ignore country for JSON Resume's "region"
    return parts[0], parts[1]


def _parse_link_profile(url: str) -> Optional[Dict[str, str]]:
    """
    Best-effort detect LinkedIn / GitHub etc and turn into a JSON Resume profile.

    Example:
      'https://github.com/PCosby/' ->
        {"network": "GitHub", "username": "PCosby", "url": "..."}
    """
    if not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()

    lowered = url.lower()
    if "linkedin.com" in lowered:
        network = "LinkedIn"
    elif "github.com" in lowered:
        network = "GitHub"
    else:
        # Other networks are fine, keep generic
        network = "Profile"

    # Extract username as last non-empty segment
    username = ""
    try:
        path = url.split("://", 1)[-1]
        segments = [s for s in path.split("/") if s]
        if segments:
            username = segments[-1]
    except Exception:
        username = ""

    return {
        "network": network,
        "username": username,
        "url": url,
    }


_DATE_SPLIT_RE = re.compile(r"\s*[--—]\s*")  # split on -, - or —


def _parse_month_year(text: str) -> Tuple[str, str]:
    """
    Parse something like 'Jun 2023', 'June 2023', 'Jan. 2025' into (YYYY, MM).

    Returns ("", "") on failure.
    """
    if not isinstance(text, str):
        return "", ""
    text = text.strip()
    if not text:
        return "", ""

    # Remove trailing punctuation on month
    tokens = text.replace(",", " ").split()
    if len(tokens) < 2:
        return "", ""
    month_raw = re.sub(r"[^\w]", "", tokens[0]).lower()
    year_match = re.search(r"\d{4}", text)
    if not year_match:
        return "", ""

    year = year_match.group(0)
    month = MONTH_MAP.get(month_raw)
    if not month:
        return "", ""
    return year, month


def _parse_date_range(dates: str) -> Tuple[str, str]:
    """
    Best-effort parse your 'dates' strings into JSON Resume startDate / endDate.

    Accepts formats like:
      'Jun 2023 - Aug 2023'
      'Jan. 2025 - May. 2025'
      'Jan 2024 - Present'   (endDate will be "")

    Returns (startDate, endDate) as 'YYYY-MM' or '' if parsing fails.
    """
    if not isinstance(dates, str):
        return "", ""
    dates = dates.strip()
    if not dates:
        return "", ""

    parts = _DATE_SPLIT_RE.split(dates)
    if not parts:
        return "", ""

    start_raw = parts[0].strip()
    end_raw = parts[1].strip() if len(parts) > 1 else ""

    start_y, start_m = _parse_month_year(start_raw)
    start_iso = f"{start_y}-{start_m}" if start_y and start_m else ""

    end_iso = ""
    if end_raw and not re.search(r"present", end_raw, re.IGNORECASE):
        end_y, end_m = _parse_month_year(end_raw)
        if end_y and end_m:
            end_iso = f"{end_y}-{end_m}"

    return start_iso, end_iso


def _bullet_texts(entry: Dict[str, Any]) -> List[str]:
    bullets = entry.get("bullets") or []
    out: List[str] = []
    for b in bullets:
        if not isinstance(b, dict):
            continue
        txt = b.get("text")
        if isinstance(txt, str):
            txt = txt.strip()
            if txt:
                out.append(txt)
    return out


# ---------- converters to JSON Resume ----------


def _convert_basics(basics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map your 'basics' block to JSON Resume 'basics'.
    Expected input keys (from your pipeline):
      - name, email, phone, location, website, linkedin, github
    """
    if not isinstance(basics, dict):
        basics = {}

    name = str(basics.get("name") or "").strip()
    email = str(basics.get("email") or "").strip()
    phone = str(basics.get("phone") or "").strip()
    location_str = str(basics.get("location") or "").strip()
    website = str(basics.get("website") or "").strip()
    linkedin = str(basics.get("linkedin") or "").strip()
    github = str(basics.get("github") or "").strip()

    city, region = _parse_city_region(location_str)

    profiles: List[Dict[str, str]] = []
    for url in (linkedin, github):
        p = _parse_link_profile(url)
        if p:
            profiles.append(p)

    basics_out: Dict[str, Any] = {
        "name": name,
    }

    if email:
        basics_out["email"] = email
    if phone:
        basics_out["phone"] = phone
    if website:
        basics_out["url"] = website  # JSON Resume uses 'url' for main site

    # Location is nested object in JSON Resume
    if city or region:
        basics_out["location"] = {
            "city": city,
            "region": region,
        }

    if profiles:
        basics_out["profiles"] = profiles

    return basics_out


def _split_degree_title(title: str) -> Tuple[str, str]:
    """
    Heuristic: split 'Masters of Engineering in Computer Science'
    into (studyType='Masters of Engineering', area='Computer Science').

    If ' in ' not found, put everything into studyType.
    """
    if not isinstance(title, str):
        return "", ""
    title = title.strip()
    if not title:
        return "", ""

    parts = re.split(r"\s+in\s+", title, flags=re.IGNORECASE)
    if len(parts) == 1:
        return title, ""
    study_type = parts[0].strip()
    area = parts[1].strip()
    return study_type, area


def _convert_education(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue

        name = str(entry.get("name") or "").strip()
        title = str(entry.get("title") or "").strip()
        dates = str(entry.get("dates") or "").strip()
        location_str = str(entry.get("location") or "").strip()
        gpa = str(entry.get("gpa") or "").strip()  # <-- NEW

        study_type, area = _split_degree_title(title)
        start_date, end_date = _parse_date_range(dates)

        edu: Dict[str, Any] = {}
        if name:
            edu["institution"] = name
        if area:
            edu["area"] = area
        if study_type:
            edu["studyType"] = study_type
        if start_date:
            edu["startDate"] = start_date
        if end_date:
            edu["endDate"] = end_date

        # Non-standard but useful: keep location if present
        if location_str:
            edu["location"] = location_str

        # Use JSON Resume's "score" field for GPA so themes can render it
        # if gpa:
        # edu["score"] = gpa
        # edu["gpa"] = gpa

        if edu:
            out.append(edu)
    return out


def _convert_experience(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Map your 'experience' array to JSON Resume 'work'.
    Input entry shape (approx):
      {
        "name": "Fiserv",
        "title": "Software Engineer Intern",
        "location": "Berkeley Heights, NJ",
        "dates": "Jun 2023 - Aug 2023",
        "tools": [...],
        "bullets": [{ "id": "...", "text": "..." }, ...]
      }
    """
    out: List[Dict[str, Any]] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue

        company = str(entry.get("name") or "").strip()
        position = str(entry.get("title") or "").strip()
        location_str = str(entry.get("location") or "").strip()
        dates = str(entry.get("dates") or "").strip()
        tools = entry.get("tools") or []

        start_date, end_date = _parse_date_range(dates)
        highlights = _bullet_texts(entry)

        work: Dict[str, Any] = {}
        if company:
            work["name"] = company
        if position:
            work["position"] = position
        if location_str:
            work["location"] = location_str
        if start_date:
            work["startDate"] = start_date
        if end_date:
            work["endDate"] = end_date
        if highlights:
            work["highlights"] = highlights

        # Optional: tuck tools into 'keywords' list (non-standard but many themes support)
        tool_keywords = [str(t).strip() for t in tools if str(t).strip()]
        if tool_keywords:
            work["keywords"] = tool_keywords

        if work:
            out.append(work)

    return out


def _convert_projects(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Map your 'projects' array to JSON Resume 'projects'.

    Input entry shape (approx):
      {
        "name": "AI-Driven Security Risk Assessment System",
        "title": "...",        # often unused here
        "dates": "Jan 2025 - May 2025",
        "location": "...",     # often unused
        "tools": [...],
        "bullets": [{ "id": "...", "text": "..." }, ...]
      }
    """
    out: List[Dict[str, Any]] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue

        name = str(entry.get("name") or "").strip()
        dates = str(entry.get("dates") or "").strip()
        tools = entry.get("tools") or []

        start_date, end_date = _parse_date_range(dates)
        highlights = _bullet_texts(entry)

        proj: Dict[str, Any] = {}
        if name:
            proj["name"] = name
        if highlights:
            proj["highlights"] = highlights
        if start_date:
            proj["startDate"] = start_date
        if end_date:
            proj["endDate"] = end_date

        tool_keywords = [str(t).strip() for t in tools if str(t).strip()]
        if tool_keywords:
            proj["keywords"] = tool_keywords

        if proj:
            out.append(proj)

    return out


def _convert_skills(skills: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Map your 'skills' dict into JSON Resume 'skills' array.

    Input example:
      {
        "programming": ["Python", "TypeScript", "Java"],
        "technologies": ["Kubernetes", "Docker", "React"]
      }

    Output example:
      [
        {"name": "Programming", "level": "", "keywords": ["Python", "TypeScript", "Java"]},
        {"name": "Technologies", "level": "", "keywords": ["Kubernetes", "Docker", "React"]}
      ]
    """
    if not isinstance(skills, dict):
        return []

    out: List[Dict[str, Any]] = []
    for key, value in skills.items():
        if value is None:
            continue
        if isinstance(value, list):
            keywords = [str(v).strip() for v in value if str(v).strip()]
        else:
            # Single string or something else; split on commas as a fallback
            keywords = [s.strip() for s in str(value).split(",") if s.strip()]

        if not keywords:
            continue

        name = str(key).replace("_", " ").title()
        out.append(
            {
                "name": name,
                "level": "",
                "keywords": keywords,
            }
        )

    return out


# ---------- PUBLIC API ----------


def to_json_resume(modified_resume_json_str: str) -> str:
    """
    Convert your existing modified_resume.json (LLM-tailored entries) into
    a JSON Resume v1.0.0 compatible JSON string.

    This is the final step before feeding the result to `resume-cli`:

        resume export --theme <theme-name> resume.pdf

    Returns:
        A pretty-printed JSON string following the JSON Resume schema.
    """
    data = json.loads(modified_resume_json_str)

    basics_in = data.get("basics") or {}
    education_in = data.get("education") or []
    experience_in = data.get("experience") or []
    projects_in = data.get("projects") or []
    skills_in = data.get("skills") or {}

    basics_out = _convert_basics(basics_in)
    education_out = _convert_education(education_in)
    work_out = _convert_experience(experience_in)
    projects_out = _convert_projects(projects_in)
    skills_out = _convert_skills(skills_in)

    resume: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": basics_out,
        "work": work_out,
        "education": education_out,
        "skills": skills_out,
        "projects": projects_out,
    }

    # JSON Resume also supports: languages, interests, references, awards, etc.
    # You can wire those later if/when you add them to your base YAML/JSON.

    return json.dumps(resume, ensure_ascii=False, indent=2)
