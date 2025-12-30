# ResumeBot ⚙️📄

A local workflow for automating the process of tailoring resumes and cover letters to specific job postings by running ResumeBot on selected text 🎯🤖

---

## How to use (Windows) 🪟

### AutoHotkey workflow (recommended) ⌨️

1. Install AutoHotkey v2
2. Open `ahk/resumeBot.ahk`
3. Double-click the file to run it
4. Anywhere on your system:
   - highlight text (for example, a job posting)
   - press Ctrl + Shift + P

This will:

- copy the selected text 📋
- save it to `out/selected.txt`
- run the ResumeBot pipeline automatically ▶️

---

## What to customize 🛠️

### Resume data 🧾

Your real resume data lives locally at:

`src/config/templates/base_resume.yml`

An example structure is provided at:

`src/config/templates/base_resume.yml.example`

Your real resume file is ignored by Git 🔒

---

### Prompts (important) ✨

All LLM behavior is defined in:

`src/config/prompts/`

These prompt files are intentionally generic and can be customized freely:

- rewrite instructions ✏️
- change constraints 🔧
- adjust tone or verbosity 🎛️
- repurpose them for non-resume tasks 🔄

Nothing in the prompt files is fixed or canonical.

---

### Environment variables 🌱

Optional runtime configuration lives in:

`.env`

An example is provided in:

`.env.example`

---

### Resume theme 🎨

PDF styling is controlled via resume-cli themes under:

`resume_theme/`

You may switch themes or modify CSS as desired.

---

## Output 📂

Generated artifacts are written to:

`out/`

This directory is ignored by Git.

---

## Notes 🧭

- Everything runs locally 🖥️
- No personal data is committed 🔐
- The project is meant to be customized, not used as-is
