"""The case table (eval/cases.csv) and a checker for it.

Each row is one eval case: an input (a Penn document and an RWTH document) plus the
expected answer. The checker catches mistakes in the table before any model is run.

Run the checker:  python -m src.cases
"""

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "eval" / "cases.csv"
DOCUMENTS_DIR = ROOT / "data" / "documents"

COLUMNS = [
    "case_id", "split", "penn_doc", "rwth_doc",
    "expected_recommendation", "label_type", "label_source", "notes",
]
SPLITS = {"dev", "test"}
LABELS = {"recognize", "partial", "reject", "not_enough_information"}
LABEL_TYPES = {"real", "constructed"}
MIN_TEST_CASES = 25  # handout, Section 4: at least 25 held-out test cases for a solo student


def load_cases(split: str | None = None, path: Path = CASES_FILE) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if split is None or r["split"] == split]


def load_case(case_id: str) -> dict:
    """One case by id, in the shape run_case.py expects."""
    for row in load_cases():
        if row["case_id"] == case_id:
            return {**row, "id": row["case_id"]}
    raise KeyError(f"No case '{case_id}' in {CASES_FILE}")


def validate(rows: list[dict], documents_dir: Path = DOCUMENTS_DIR) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors mean the table cannot be used as it is."""
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    seen_pairs: dict[tuple[str, str], str] = {}
    for r in rows:
        cid = r.get("case_id", "?")
        for col in COLUMNS:
            if col not in r or r[col] is None:
                errors.append(f"{cid}: column '{col}' is missing")
        if cid in seen_ids:
            errors.append(f"{cid}: duplicate case_id")
        seen_ids.add(cid)
        if r.get("split") not in SPLITS:
            errors.append(f"{cid}: split must be one of {sorted(SPLITS)}, got '{r.get('split')}'")
        if r.get("expected_recommendation") not in LABELS:
            errors.append(f"{cid}: expected_recommendation must be one of {sorted(LABELS)}")
        if r.get("label_type") not in LABEL_TYPES:
            errors.append(f"{cid}: label_type must be one of {sorted(LABEL_TYPES)}")
        if not (r.get("label_source") or "").strip():
            errors.append(f"{cid}: label_source is empty (say where the expected answer comes from)")
        for col in ("penn_doc", "rwth_doc"):
            if not (documents_dir / (r.get(col) or "")).is_file():
                errors.append(f"{cid}: {col} file not found: {r.get(col)}")
        pair = (r.get("penn_doc", ""), r.get("rwth_doc", ""))
        if pair in seen_pairs:
            errors.append(f"{cid}: same document pair as {seen_pairs[pair]} (a pair must not be in the table twice)")
        seen_pairs[pair] = cid

    tests = [r for r in rows if r.get("split") == "test"]
    if len(tests) < MIN_TEST_CASES:
        warnings.append(f"only {len(tests)} test cases, the handout requires at least {MIN_TEST_CASES}")
    if tests:
        counts = Counter(r["expected_recommendation"] for r in tests)
        label, n = counts.most_common(1)[0]
        share = n / len(tests)
        if share > 0.6:
            warnings.append(
                f"test set is unbalanced: always answering '{label}' would already be right on "
                f"{share:.0%} of cases ({n}/{len(tests)}); the agent must beat this, so add more "
                f"cases of the other kinds"
            )
        real = sum(r["label_type"] == "real" for r in tests)
        if real < len(tests) / 2:
            warnings.append(f"only {real} of {len(tests)} test cases are real decisions; report real and constructed results separately")
    return errors, warnings


def main() -> int:
    rows = load_cases()
    errors, warnings = validate(rows)
    for split in ("dev", "test"):
        part = [r for r in rows if r["split"] == split]
        by_label = Counter(r["expected_recommendation"] for r in part)
        by_type = Counter(r["label_type"] for r in part)
        print(f"{split}: {len(part)} cases | labels {dict(by_label)} | {dict(by_type)}")
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK: table is consistent" if not errors else f"{len(errors)} error(s) found")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
