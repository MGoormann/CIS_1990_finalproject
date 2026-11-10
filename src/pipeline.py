"""The simple first version of the agent (no advocate/critic, no retrieval yet).

Steps: extract RWTH learning outcomes -> judge each outcome against the Penn text with
quotes -> verify every quote in code -> compute the recommendation with a fixed rule.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from .llm import LLMResult, call_llm
from .quotes import check_quotes

SYSTEM = (
    "You compare a course from the University of Pennsylvania (Penn) with a module from "
    "RWTH Aachen to help decide whether the course can be credited. The documents may be "
    "in English or German. Be strict and honest: do not assume a match exists. "
    "Only quote text that appears word for word in the documents, in its original language."
)


class OutcomeList(BaseModel):
    outcomes: list[str]


class Judgment(BaseModel):
    verdict: Literal["full", "partial", "none"]
    rwth_quotes: list[str]
    penn_quotes: list[str]
    reasoning: str


@dataclass
class OutcomeResult:
    outcome: str
    claimed_verdict: str  # what the model said
    verdict: str  # full | partial | none | unverified (claimed coverage without valid quote)
    rwth_quotes: list[str]
    penn_quotes: list[str]
    rwth_quotes_valid: list[bool]
    penn_quotes_valid: list[bool]
    reasoning: str


@dataclass
class Report:
    recommendation: str
    outcomes: list[OutcomeResult]
    any_invalid_quote: bool
    notes: list[str] = field(default_factory=list)
    model: str = ""
    llm_calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    llm_latency_s: float = 0.0


def extract_outcomes(rwth_text: str) -> tuple[list[str], LLMResult]:
    prompt = (
        "List the learning outcomes (competences, objectives) of the module below, one "
        "short statement each, close to the original wording. If the document has no "
        "learning outcomes, return an empty list.\n\n=== RWTH MODULE ===\n" + rwth_text
    )
    result = call_llm(prompt, system=SYSTEM, schema=OutcomeList)
    return [o.strip() for o in result.parsed.outcomes if o.strip()], result


def judge_outcome(outcome: str, rwth_text: str, penn_text: str) -> tuple[Judgment, LLMResult]:
    prompt = (
        "Does the Penn course cover this RWTH learning outcome?\n\n"
        f"OUTCOME: {outcome}\n\n"
        "Answer 'full' only if the Penn text clearly shows the same content at a "
        "comparable level, 'partial' if it is only touched on or the level differs, "
        "'none' if there is no evidence. Support 'full' or 'partial' with at least one "
        "quote from the Penn text, and quote the RWTH sentence the outcome comes from. "
        "Quotes must be copied word for word from the documents. If there is no "
        "evidence, give an empty penn_quotes list.\n\n"
        "=== RWTH MODULE ===\n" + rwth_text + "\n\n=== PENN COURSE ===\n" + penn_text
    )
    result = call_llm(prompt, system=SYSTEM, schema=Judgment)
    return result.parsed, result


def decide_recommendation(verdicts: list[str]) -> str:
    """Fixed rule (not the model): turn per-outcome verdicts into one recommendation.

    - no outcomes, or more than half unverified -> not_enough_information
    - every outcome full -> recognize
    - no outcome full or partial -> reject
    - otherwise -> partial
    """
    if not verdicts:
        return "not_enough_information"
    if sum(v == "unverified" for v in verdicts) * 2 > len(verdicts):
        return "not_enough_information"
    if all(v == "full" for v in verdicts):
        return "recognize"
    if not any(v in ("full", "partial") for v in verdicts):
        return "reject"
    return "partial"


def run_pipeline(penn_text: str, rwth_text: str) -> Report:
    calls: list[LLMResult] = []
    notes: list[str] = []

    if not penn_text.strip() or not rwth_text.strip():
        return Report("not_enough_information", [], False, ["A document was empty."])

    outcomes, call = extract_outcomes(rwth_text)
    calls.append(call)
    if not outcomes:
        notes.append("No learning outcomes found in the RWTH document.")

    results: list[OutcomeResult] = []
    for outcome in outcomes:
        judgment, call = judge_outcome(outcome, rwth_text, penn_text)
        calls.append(call)
        rwth_ok = check_quotes(judgment.rwth_quotes, rwth_text)
        penn_ok = check_quotes(judgment.penn_quotes, penn_text)
        verdict = judgment.verdict
        # Claiming coverage without at least one valid Penn quote is not accepted.
        if verdict in ("full", "partial") and not any(penn_ok):
            verdict = "unverified"
        results.append(
            OutcomeResult(
                outcome=outcome,
                claimed_verdict=judgment.verdict,
                verdict=verdict,
                rwth_quotes=judgment.rwth_quotes,
                penn_quotes=judgment.penn_quotes,
                rwth_quotes_valid=rwth_ok,
                penn_quotes_valid=penn_ok,
                reasoning=judgment.reasoning,
            )
        )

    return Report(
        recommendation=decide_recommendation([r.verdict for r in results]),
        outcomes=results,
        any_invalid_quote=any(not ok for r in results for ok in r.rwth_quotes_valid + r.penn_quotes_valid),
        notes=notes,
        model=calls[0].model if calls else "",
        llm_calls=len(calls),
        prompt_tokens=sum(c.prompt_tokens for c in calls),
        output_tokens=sum(c.output_tokens for c in calls),
        llm_latency_s=sum(c.latency_s for c in calls),
    )


def format_report(report: Report) -> str:
    lines = [f"RECOMMENDATION: {report.recommendation}", ""]
    for i, r in enumerate(report.outcomes, 1):
        lines.append(f"{i}. {r.outcome}")
        lines.append(f"   verdict: {r.verdict}" + (f" (model claimed: {r.claimed_verdict})" if r.verdict != r.claimed_verdict else ""))
        for q, ok in zip(r.rwth_quotes, r.rwth_quotes_valid):
            lines.append(f"   RWTH quote [{'ok' if ok else 'NOT IN SOURCE'}]: {q}")
        for q, ok in zip(r.penn_quotes, r.penn_quotes_valid):
            lines.append(f"   Penn quote [{'ok' if ok else 'NOT IN SOURCE'}]: {q}")
        lines.append(f"   reasoning: {r.reasoning}")
    for note in report.notes:
        lines.append(f"NOTE: {note}")
    lines.append("")
    lines.append(
        f"{report.llm_calls} model calls, {report.prompt_tokens} prompt + {report.output_tokens} "
        f"output tokens, {report.llm_latency_s:.1f}s model time ({report.model})"
    )
    return "\n".join(lines)
