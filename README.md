# post_handle_reliabilty_checker

A compliance-first assistant that:
- ingests a resume PDF,
- extracts an editable profile,
- collects jobs from approved sources,
- matches and ranks jobs with explainable scoring,
- and supports assisted application workflows with user checkpoints.

## Safety boundaries

This project intentionally does **not** bypass CAPTCHA, does **not** evade bot detection, and does **not** automate unauthorized login.  
When login or CAPTCHA is encountered, it pauses and requires user action.

## Features

- Source compliance controls (allow-list + per-source rate limiting)
- Explicit user consent requirement before collecting jobs
- Audit logging for key actions
- Resume parsing from PDF (`pypdf`) with profile overrides
- Job normalization to one schema
- Requirement parsing (skills + experience) and match scoring
- Standout detection and confidence labels
- Filter support: work mode, minimum salary, sponsorship, domain
- Application workflow states: drafted, pending user action, ready to submit, submitted
- Final submission requires explicit user confirmation

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run demo

```bash
python -m job_bot.cli /absolute/path/to/resume.pdf --query "backend engineer" --min-salary 100000
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
