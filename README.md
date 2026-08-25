# post_handle_reliabilty_checker

Handle-level source reliability pipeline (not post-level yet).

## What this does

Given a handle/page/source row from Excel/CSV, the pipeline labels the source as:

- `reliable`
- `unreliable`
- `neutral`

It also stores:

- numeric `score`
- `confidence`
- `needs_review` flag
- rule `scoring_version`
- reason text for auditability

Missing signals are treated as neutral evidence (not negative), and low-evidence rows are flagged for manual review.

## Input columns

Minimum:

- `platform`
- one of `handle` / `url` / `linked_domain`

Manual review columns (optional but recommended):

- `manual_identity_clear` (`yes|no|unknown`)
- `manual_verified` (`yes|no|unknown`)
- `manual_impersonation_flag` (`yes|no|unknown`)
- `manual_parody_labeled` (`yes|no|unknown|not_applicable`)
- `manual_account_age_bucket` (`under_3_months|3mo_2yr|2yr_plus|unknown`)

## Setup

```bash
python -m pip install -r requirements.txt
```

## Build Excel template

```bash
python build_template.py
```

This creates `handles_template.xlsx` with dropdown validation.

## Run pipeline

```bash
python pipeline.py --input handles.xlsx --output handles_labeled.xlsx --db handle_reliability.db
```

Optional domain/handle lists:

```bash
python pipeline.py \
  --input handles.xlsx \
  --output handles_labeled.xlsx \
  --credible-domains-file credible_domains.txt \
  --low-cred-domains-file low_cred_domains.txt \
  --factcheck-failed-handles-file failed_handles.txt
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```