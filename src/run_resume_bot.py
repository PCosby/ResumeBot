import os
from pathlib import Path
import helper
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

selection_file = Path(__file__).parent.parent / "out" / "selected.txt"
MAKE_COVER_LETTER = os.getenv("MAKE_COVER_LETTER", "False").lower() in [
    "t",
    "true",
    "1",
]

try:
    if not selection_file.exists():
        print(f"ERROR: File not found: {selection_file}")
    else:
        text = selection_file.read_text(encoding="utf-8")
        if text.strip():
            print("Starting job info extraction...")
            job_info = helper.extract_job_info(text)
            print("[DONE] Job info extracted")

            print("Starting resume modification...")
            modified_resume_info = helper.modify_resume_info(job_info)
            print("[DONE] Resume info modified")

            print("Finalizing resume...")
            finalized_resume_info = helper.finalize_resume_info(modified_resume_info)
            print("[DONE] Resume finalized")

            print("Compiling Resume MD -> PDF...")
            resume_path = helper.compile_resume_pdf(finalized_resume_info)
            print("[DONE] Resume PDF written")

            if MAKE_COVER_LETTER:
                print("Starting cover letter generation...")
                cover_letter = helper.generate_cover_letter(
                    job_info, finalized_resume_info
                )
                print("[DONE] Cover letter generated")

                print("Compiling Cover Letter MD -> PDF...")
                cover_letter_path = helper.compile_cover_letter_pdf(cover_letter)
                print("[DONE] Cover letter PDF written")

                print("Opening cover letter PDF...")
                helper.open_pdf(cover_letter_path)
                print("[DONE] Cover letter PDF opened")
            else:
                print("[INFO] Skipping Cover letter...")

            print(f"Opening resume PDF...")
            helper.open_pdf(resume_path)
            print("[DONE] PDF opened")

            print("Completed.")
        else:
            print("ERROR: selected.txt is empty.")
except Exception as e:
    print(f"ERROR: {e}")
