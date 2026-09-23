# post_handle_reliabilty_checker

A compliance-first local job assistant that combines:
- multi-source job discovery,
- match scoring/ranking,
- resume variant selection,
- screening-question planning,
- and guarded application execution with explicit human checkpoints.

## Safety boundaries

This project intentionally does **not** bypass CAPTCHA, does **not** evade bot detection, and does **not** automate unauthorized login.

When login or CAPTCHA is encountered, it pauses and requires user action.

## What this unified build now supports

- Resume PDF ingestion and profile extraction (`pypdf`)
- Editable profile overrides
- Job source allow-list + per-source rate limiting
- Normalized job schema with ATS type tagging (LinkedIn/Indeed/Greenhouse/Lever/Workday/Ashby/Other)
- Requirement parsing and explainable scoring with standout detection
- Filtering by work mode, salary, sponsorship, and domain
- Resume variant library and best-fit resume selection per job
- Screening question answer planner with QA bank + profile-derived answers
- Application pipeline covering:
  - login checkpoint
  - captcha checkpoint
  - field-by-field autofill
  - screening answer attachment
  - retry/fail handling for missing required data
  - explicit pre-submit confirmation gate
- Application state tracking (`drafted`, `pending_user_action`, `ready_to_submit`, `submitted`, `failed`)
- Audit logging for key actions

## Project structure

- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/engine.py` — orchestration
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/job_sources.py` — source collection + normalization
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/matching.py` — scoring and ranking
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/resume.py` — PDF parsing
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/resume_library.py` — resume variant selection
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/question_planner.py` — screening answer planning
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/application.py` — workflow state transitions
- `/home/runner/work/evaluate-media-handle-reliability/evaluate-media-handle-reliability/job_bot/pipeline.py` — end-to-end apply pipeline

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

The demo intentionally pauses submission by default so you can review the generated application record.

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
