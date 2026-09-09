#!/usr/bin/env python
"""Run from backend/ with the venv active: python eval/run_eval.py"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clauseguard.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

from reviews.models import Contract, PlaybookRule  # noqa: E402
from reviews.services.engines.base import RISK_ORDER  # noqa: E402
from reviews.services.brain import ContractBrain  # noqa: E402
from reviews.services.parsing import UnreadableFile, UnsupportedFileType, extract_text  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
CONTRACTS_DIR = EVAL_DIR / "contracts"
RESULTS_DIR = EVAL_DIR / "results"
MANUAL_WORDS_PER_MINUTE = 200  # assumption, stated in docs/EVALUATION.md


def estimate_manual_minutes(text: str) -> float:
    words = len(text.split())
    return round(words / (MANUAL_WORDS_PER_MINUTE * 0.5), 1)


# Rough keyword used to check whether the naive baseline's free-text answer
# even mentioned the risk area a test case requires ClauseGuard to catch.
# This is a coarse text-overlap heuristic, not semantic grading -- good
# enough to tell "didn't mention it at all" from "did", not to score quality.
RISK_KEYWORD = {
    "auto-renewal": r"renew",
    "confidentiality": r"confidential",
    "data-privacy": r"privacy|data protection|breach",
    "indemnification": r"indemnif",
    "ip-ownership": r"intellectual property|\bip\b|ownership",
    "liability-cap": r"liabilit",
    "non-compete": r"non-?compete",
    "payment-terms": r"payment|net[\s-]?90|invoice",
}


def naive_llm_baseline(text: str) -> dict:
    if not settings.GEMINI_API_KEY:
        return {"ran": False, "note": "Skipped -- no GEMINI_API_KEY configured for this run."}

    from google import genai

    prompt = "Review this contract and list any risks you notice.\n\n" + text[:6000]
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        resp = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        return {"ran": True, "provider": "gemini", "output": resp.text or ""}
    except Exception as exc:
        return {"ran": False, "note": f"Baseline call failed: {exc}"}


def load_test_cases():
    return json.loads((EVAL_DIR / "test_cases.json").read_text())


def run_case(case: dict) -> dict:
    path = CONTRACTS_DIR / case["file"]
    raw_bytes = path.read_bytes()

    result = {"id": case["id"], "category": case["category"], "pass": True, "notes": []}

    if case.get("expect_http_error"):
        try:
            extract_text(case["file"], raw_bytes)
            result["pass"] = False
            result["notes"].append("Expected a parsing error but extraction succeeded.")
        except (UnreadableFile, UnsupportedFileType) as exc:
            result["notes"].append(f"Correctly raised: {exc}")
        return result

    text = extract_text(case["file"], raw_bytes)
    contract = Contract.objects.create(filename=case["file"], source_text=text)
    started = time.monotonic()
    review = ContractBrain(contract).review()
    elapsed_ms = int((time.monotonic() - started) * 1000)

    result["overall_risk"] = review.overall_risk
    result["next_action"] = review.next_action
    result["processing_time_ms"] = elapsed_ms
    result["manual_baseline_minutes"] = estimate_manual_minutes(text)
    result["naive_baseline"] = naive_llm_baseline(text)

    if review.overall_risk != case["expected_overall_risk"]:
        result["pass"] = False
        result["notes"].append(
            f"overall_risk: expected {case['expected_overall_risk']}, got {review.overall_risk}"
        )
    if review.next_action != case["expected_next_action"]:
        result["pass"] = False
        result["notes"].append(
            f"next_action: expected {case['expected_next_action']}, got {review.next_action}"
        )

    naive_output = result["naive_baseline"].get("output", "") if result["naive_baseline"]["ran"] else None

    findings_by_key = {f.rule_key: f for f in review.findings.all()}
    result["required_checks"] = []
    for req in case.get("must_flag", []):
        finding = findings_by_key.get(req["rule_key"])
        is_recall_check = "max_risk" not in req
        check = {"rule_key": req["rule_key"], "is_recall_check": is_recall_check, "ok": True}

        if is_recall_check and naive_output is not None:
            keyword = RISK_KEYWORD.get(req["rule_key"])
            check["naive_mentioned"] = bool(keyword and re.search(keyword, naive_output, re.IGNORECASE))

        if not finding:
            result["pass"] = False
            check["ok"] = False
            result["notes"].append(f"missing required finding for rule '{req['rule_key']}'")
            result["required_checks"].append(check)
            continue

        actual_rank = RISK_ORDER.get(finding.risk_level, -1)
        min_rank = RISK_ORDER.get(req["min_risk"], 0)
        if actual_rank < min_rank:
            result["pass"] = False
            check["ok"] = False
            result["notes"].append(
                f"{req['rule_key']}: expected risk >= {req['min_risk']}, got {finding.risk_level}"
            )
        max_risk = req.get("max_risk")
        if max_risk is not None and actual_rank > RISK_ORDER.get(max_risk, 999):
            result["pass"] = False
            check["ok"] = False
            result["notes"].append(
                f"{req['rule_key']}: expected risk <= {max_risk} (false positive check), got {finding.risk_level}"
            )
        result["required_checks"].append(check)

    return result


def main():
    PlaybookRule.objects.all().delete()
    from django.core.management import call_command

    call_command("load_playbook")

    cases = load_test_cases()
    results = [run_case(c) for c in cases]

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    recall_checks = [
        c for r in results for c in r.get("required_checks", []) if c["is_recall_check"]
    ]
    caught_flags = sum(1 for c in recall_checks if c["ok"])
    required_flags = len(recall_checks)
    recall = round(caught_flags / required_flags, 2) if required_flags else None

    naive_ran_count = sum(1 for r in results if r.get("naive_baseline", {}).get("ran"))
    naive_scoreable = [c for c in recall_checks if "naive_mentioned" in c]
    naive_recall = (
        round(sum(1 for c in naive_scoreable if c["naive_mentioned"]) / len(naive_scoreable), 2)
        if naive_scoreable
        else None
    )

    timed = [r for r in results if "processing_time_ms" in r]
    avg_processing_ms = round(sum(r["processing_time_ms"] for r in timed) / len(timed), 1) if timed else None
    total_manual_minutes = round(sum(r.get("manual_baseline_minutes", 0) for r in timed), 1)
    total_clauseguard_seconds = round(sum(r["processing_time_ms"] for r in timed) / 1000, 2)

    summary = {
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "critical_high_recall": recall,
        "avg_processing_ms": avg_processing_ms,
        "estimated_total_manual_minutes": total_manual_minutes,
        "total_clauseguard_seconds": total_clauseguard_seconds,
        "naive_llm_baseline_ran_for_cases": naive_ran_count,
        "naive_llm_baseline_keyword_recall": naive_recall,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "results.json").write_text(
        json.dumps({"summary": summary, "cases": results}, indent=2)
    )

    print(f"\n{'ID':35} {'STATUS':6} {'RISK':10} {'ACTION':25} NOTES")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(
            f"{r['id']:35} {status:6} {r.get('overall_risk', '-'):10} "
            f"{r.get('next_action', '-'):25} {'; '.join(r['notes']) if r['notes'] else ''}"
        )

    print(f"\n{passed}/{total} cases passed.")
    print(f"ClauseGuard recall on required Critical/High findings: {recall}")
    if naive_ran_count:
        print(
            f"Naive single-prompt LLM baseline ran for {naive_ran_count}/{total} cases; "
            f"keyword-mentioned the required risk in {naive_recall} of them "
            "(coarse text-overlap check, not semantic grading -- see docs/EVALUATION.md)"
        )
    else:
        print("Naive single-prompt LLM baseline: skipped -- no GEMINI_API_KEY configured.")
    print(f"Avg ClauseGuard processing time: {avg_processing_ms} ms/contract")
    print(
        f"Estimated manual reading time for this set: {total_manual_minutes} min "
        f"vs {total_clauseguard_seconds} sec for ClauseGuard "
        f"(assumption: {MANUAL_WORDS_PER_MINUTE * 0.5:.0f} careful-reading wpm, see docs/EVALUATION.md)"
    )
    print(f"Full results written to {RESULTS_DIR / 'results.json'}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
