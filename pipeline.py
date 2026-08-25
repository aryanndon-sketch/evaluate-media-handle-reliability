from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from handle_reliability import (
    clean_cell,
    handle_key,
    normalize_domain,
    normalize_handle,
    normalize_platform,
    score_handle,
    utc_now_iso,
)


DEFAULT_CREDIBLE_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "nytimes.com",
}
DEFAULT_LOW_CREDIBILITY_DOMAINS = {
    "beforeitsnews.com",
    "infowars.com",
}
DEFAULT_FACTCHECK_FAILED_HANDLES = set()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handles (
            id INTEGER PRIMARY KEY,
            handle_key TEXT UNIQUE NOT NULL,
            handle TEXT,
            platform TEXT NOT NULL,
            url TEXT,
            source_name TEXT,
            linked_domain TEXT,
            first_seen_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY,
            handle_id INTEGER NOT NULL,
            scoring_version TEXT NOT NULL,
            label TEXT NOT NULL,
            score INTEGER NOT NULL,
            confidence REAL NOT NULL,
            needs_review INTEGER NOT NULL,
            reasons_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(handle_id) REFERENCES handles(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS enrichment_errors (
            id INTEGER PRIMARY KEY,
            handle_key TEXT NOT NULL,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def upsert_handle(conn: sqlite3.Connection, row: Dict[str, Any]) -> int:
    now = utc_now_iso()
    h_key = handle_key(row.get("platform"), row.get("handle"), row.get("linked_domain") or row.get("url"))
    if not h_key:
        raise ValueError("Unable to create handle_key due to missing platform/handle/domain")

    payload = (
        h_key,
        normalize_handle(row.get("handle")),
        normalize_platform(row.get("platform")),
        clean_cell(row.get("url")),
        clean_cell(row.get("source_name")),
        normalize_domain(row.get("linked_domain") or row.get("url")),
        now,
        now,
    )
    conn.execute(
        """
        INSERT INTO handles (handle_key, handle, platform, url, source_name, linked_domain, first_seen_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(handle_key) DO UPDATE SET
            handle=excluded.handle,
            url=excluded.url,
            source_name=excluded.source_name,
            linked_domain=excluded.linked_domain,
            updated_at=excluded.updated_at
        """,
        payload,
    )
    cursor = conn.execute("SELECT id FROM handles WHERE handle_key = ?", (h_key,))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError("Failed to retrieve handle id after upsert")
    return int(row[0])


def insert_label(conn: sqlite3.Connection, handle_id: int, result: Any) -> None:
    conn.execute(
        """
        INSERT INTO labels (handle_id, scoring_version, label, score, confidence, needs_review, reasons_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            handle_id,
            result.scoring_version,
            result.label,
            result.score,
            result.confidence,
            1 if result.needs_review else 0,
            json.dumps(result.reasons),
            utc_now_iso(),
        ),
    )


def _load_domains(path: Path) -> Iterable[str]:
    if not path.exists():
        return set()
    lines = [line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines()]
    return {line for line in lines if line and not line.startswith("#")}


def load_input_rows(input_path: Path) -> List[Dict[str, Any]]:
    import pandas as pd

    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)
    rows = df.to_dict(orient="records")
    return [{k: clean_cell(v) for k, v in row.items()} for row in rows]


def run_pipeline(
    input_path: Path,
    output_path: Path,
    sqlite_path: Path,
    credible_domains: Iterable[str],
    low_credibility_domains: Iterable[str],
    factcheck_failed_handles: Iterable[str],
) -> None:
    rows = load_input_rows(input_path)
    results: List[Dict[str, Any]] = []

    conn = sqlite3.connect(sqlite_path)
    init_db(conn)
    try:
        for row in rows:
            if not row.get("platform") or not (row.get("handle") or row.get("url") or row.get("linked_domain")):
                continue
            try:
                handle_id = upsert_handle(conn, row)
                result = score_handle(
                    row=row,
                    credible_domains=credible_domains,
                    low_credibility_domains=low_credibility_domains,
                    factcheck_failed_handles=factcheck_failed_handles,
                )
                insert_label(conn, handle_id, result)
                results.append(
                    {
                        **row,
                        "label": result.label,
                        "score": result.score,
                        "confidence": result.confidence,
                        "needs_review": result.needs_review,
                        "reasons": "; ".join(result.reasons),
                        "scoring_version": result.scoring_version,
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                h_key = handle_key(row.get("platform"), row.get("handle"), row.get("linked_domain") or row.get("url")) or "unknown"
                conn.execute(
                    """
                    INSERT INTO enrichment_errors (handle_key, error_type, message, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (h_key, exc.__class__.__name__, str(exc), utc_now_iso()),
                )
        conn.commit()
    finally:
        conn.close()

    if not results:
        raise RuntimeError("No valid rows processed. Ensure platform and handle/url are provided.")

    import pandas as pd

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_excel(output_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Handle reliability scoring pipeline.")
    parser.add_argument("--input", required=True, help="Input Excel/CSV file path")
    parser.add_argument("--output", required=True, help="Output Excel file path")
    parser.add_argument("--db", default="handle_reliability.db", help="SQLite db path")
    parser.add_argument("--credible-domains-file", default="", help="Optional newline-delimited credible domains")
    parser.add_argument("--low-cred-domains-file", default="", help="Optional newline-delimited low-credibility domains")
    parser.add_argument("--factcheck-failed-handles-file", default="", help="Optional newline-delimited fact-check-failed handles")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    credible = set(DEFAULT_CREDIBLE_DOMAINS)
    low_cred = set(DEFAULT_LOW_CREDIBILITY_DOMAINS)
    failed_handles = set(DEFAULT_FACTCHECK_FAILED_HANDLES)

    if args.credible_domains_file:
        credible |= set(_load_domains(Path(args.credible_domains_file)))
    if args.low_cred_domains_file:
        low_cred |= set(_load_domains(Path(args.low_cred_domains_file)))
    if args.factcheck_failed_handles_file:
        failed_handles |= set(_load_domains(Path(args.factcheck_failed_handles_file)))

    run_pipeline(
        input_path=Path(args.input),
        output_path=Path(args.output),
        sqlite_path=Path(args.db),
        credible_domains=credible,
        low_credibility_domains=low_cred,
        factcheck_failed_handles=failed_handles,
    )


if __name__ == "__main__":
    main()
