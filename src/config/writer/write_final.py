from __future__ import annotations
import subprocess
import tempfile
import shutil
from pathlib import Path


def markdown_to_pdf(md_text: str, output_path: Path) -> Path:
    """
    Convert a Markdown string to a PDF file using Pandoc.

    Keep this for cover letters or simple docs.
    The resume uses json_resume_to_pdf instead.
    """
    output_path = Path(output_path).resolve()

    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as md_file:
        md_file.write(md_text)
        md_path = Path(md_file.name)

    cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(output_path),
        "--from",
        "markdown",
        "--pdf-engine",
        "xelatex",
        "--quiet",
    ]

    subprocess.run(cmd, check=True)
    return output_path


def json_resume_to_pdf(
    json_resume_text: str,
    output_path: Path,
    theme: str | None = "elegant",
) -> Path:
    import subprocess, shutil
    from pathlib import Path

    output_path = Path(output_path).resolve()

    # Path to your local theme folder
    THEME_DIR = Path(__file__).resolve().parents[3] / "resume_theme"

    if not THEME_DIR.exists():
        raise RuntimeError(
            f"Theme directory does not exist: {THEME_DIR}\n"
            f"You must create it and run:\n"
            f"   npm install resume-cli\n"
            f"   npm install jsonresume-theme-{theme}\n"
        )

    resume_json_path = THEME_DIR / "resume.json"
    resume_json_path.write_text(json_resume_text, encoding="utf-8")

    tmp_pdf_path = THEME_DIR / "resume.pdf"

    # path to local resume-cli binary
    RESUME_CMD = THEME_DIR / "node_modules" / ".bin" / "resume.cmd"

    cmd = [
        str(RESUME_CMD),
        "export",
        str(tmp_pdf_path),
        "--format",
        "pdf",
        "--theme",
        theme,
    ]

    proc = subprocess.run(
        cmd,
        cwd=THEME_DIR,
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"resume-cli failed.\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )

    if not tmp_pdf_path.exists():
        raise FileNotFoundError(
            f"resume.pdf was not created.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmp_pdf_path, output_path)

    return output_path
