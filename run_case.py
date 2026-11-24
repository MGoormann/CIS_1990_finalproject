"""Run the agent on one dev case:  python run_case.py <case-id>"""

import argparse
import sys

from src.documents import load_case, load_document
from src.pipeline import format_report, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the credit-transfer agent on one case.")
    parser.add_argument("case_id", help="a case_id from eval/cases.csv, for example case01")
    args = parser.parse_args()

    case = load_case(args.case_id)
    report = run_pipeline(load_document(case["penn_doc"]), load_document(case["rwth_doc"]))

    print(format_report(report))
    print()
    print(f"Expected: {case['expected_recommendation']}   Got: {report.recommendation}")
    recommendation_ok = report.recommendation == case["expected_recommendation"]
    quotes_ok = not report.any_invalid_quote
    print(f"Recommendation matches: {recommendation_ok}   All quotes real: {quotes_ok}")
    return 0 if recommendation_ok and quotes_ok else 1


if __name__ == "__main__":
    sys.exit(main())
