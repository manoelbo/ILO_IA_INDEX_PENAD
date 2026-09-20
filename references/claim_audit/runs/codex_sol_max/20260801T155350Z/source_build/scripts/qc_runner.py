#!/usr/bin/env python3
"""Run blind QC reviewers strictly one at a time in fresh Codex contexts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parents[2]
WORKSPACE = RUN_DIR.parents[4]
QC_DIR = RUN_DIR / "quality_control"
QUEUE_PATH = QC_DIR / "queue.tsv"
CONTROLLER = RUN_DIR / "source_build/scripts/qc_controller.py"
PYTHON_DEPS = RUN_DIR / "source_build/python_deps"
CODEX = Path("/Users/manebrasil/.nvm/versions/node/v22.22.1/bin/codex")
PROGRESS_LOG = QC_DIR / "runner_progress.jsonl"
ABORTED_DIR = QC_DIR / "aborted_attempts"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "max"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log(event: str, **fields: object) -> None:
    payload = {"timestamp": now(), "event": event, **fields}
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def controller_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(PYTHON_DEPS) + (os.pathsep + existing if existing else "")
    return env


def run_controller(*args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(CONTROLLER), *args],
        cwd=WORKSPACE,
        env=controller_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log("controller_command", command=list(args), exit_code=completed.returncode, output=completed.stdout.strip())
    return completed


def require_controller(*args: str) -> None:
    completed = run_controller(*args)
    if completed.returncode != 0:
        raise RuntimeError(f"QC controller {' '.join(args)} failed: {completed.stdout.strip()}")


def queue_rows() -> list[dict[str, str]]:
    with QUEUE_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def archive_attempt(row: dict[str, str], attempt: int, receipt: Path) -> None:
    row_id = row["row_id"]
    suffix = "html" if row["source_type"] == "LEGAL_HTML" else "pdf"
    artifacts = {
        "candidate.json": QC_DIR / f"candidates/{row_id}.candidate.json",
        suffix: QC_DIR / f"evidence_pages/{row_id}.{suffix}",
        "receipt.txt": receipt,
    }
    ABORTED_DIR.mkdir(parents=True, exist_ok=True)
    archived: list[str] = []
    for label, source in artifacts.items():
        if source.exists():
            destination = ABORTED_DIR / f"{row_id}.attempt{attempt}.{label}"
            if destination.exists():
                raise RuntimeError(f"QC archive destination already exists: {destination}")
            shutil.move(str(source), str(destination))
            archived.append(destination.relative_to(RUN_DIR).as_posix())
    log("qc_attempt_archived", row_id=row_id, attempt=attempt, artifacts=archived)


def launch_worker(row: dict[str, str], task_name: str, receipt: Path, timeout_seconds: int) -> tuple[int, bool, int]:
    row_id = row["row_id"]
    prompt = QC_DIR / f"prompts/{row_id}.md"
    env = controller_env()
    env["CLAIM_AUDIT_WORKER_TASK"] = task_name
    command = [
        str(CODEX),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "--model",
        MODEL,
        "--config",
        f'model_reasoning_effort="{REASONING_EFFORT}"',
        "--cd",
        str(WORKSPACE),
        "--output-last-message",
        str(receipt),
        "-",
    ]
    log(
        "qc_worker_started",
        qc_sequence=int(row["qc_sequence"]),
        row_id=row_id,
        task_name=task_name,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        prompt_path=prompt.relative_to(RUN_DIR).as_posix(),
    )
    with prompt.open("rb") as prompt_handle:
        process = subprocess.Popen(
            command,
            cwd=WORKSPACE,
            env=env,
            stdin=prompt_handle,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        timed_out = False
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait(timeout=30)
    suffix = "html" if row["source_type"] == "LEGAL_HTML" else "pdf"
    log(
        "qc_worker_exited",
        qc_sequence=int(row["qc_sequence"]),
        row_id=row_id,
        task_name=task_name,
        pid=process.pid,
        exit_code=exit_code,
        timed_out=timed_out,
        candidate_exists=(QC_DIR / f"candidates/{row_id}.candidate.json").is_file(),
        evidence_exists=(QC_DIR / f"evidence_pages/{row_id}.{suffix}").is_file(),
        receipt_exists=receipt.is_file(),
    )
    return exit_code, timed_out, process.pid


def process_row(row: dict[str, str], max_attempts: int, timeout_seconds: int) -> None:
    row_id = row["row_id"]
    if (QC_DIR / f"results/{row_id}.json").is_file():
        log("qc_row_skipped_already_committed", qc_sequence=int(row["qc_sequence"]), row_id=row_id)
        return

    require_controller("make-prompt", row_id)
    task_name = f"qc_row_{int(row_id.split('-')[1]):04d}"

    for attempt in range(1, max_attempts + 1):
        retry_number = attempt - 1
        receipt_name = f"{row_id}.txt" if retry_number == 0 else f"{row_id}.retry{retry_number}.txt"
        receipt = QC_DIR / "worker_receipts" / receipt_name
        exit_code, timed_out, pid = launch_worker(row, task_name, receipt, timeout_seconds)

        suffix = "html" if row["source_type"] == "LEGAL_HTML" else "pdf"
        candidate = QC_DIR / f"candidates/{row_id}.candidate.json"
        evidence = QC_DIR / f"evidence_pages/{row_id}.{suffix}"
        artifacts_ready = candidate.is_file() and evidence.is_file()
        if artifacts_ready and (exit_code == 0 or timed_out):
            committed = run_controller("commit", row_id)
            if committed.returncode == 0:
                log(
                    "qc_row_committed",
                    qc_sequence=int(row["qc_sequence"]),
                    row_id=row_id,
                    attempt=attempt,
                    timed_out=timed_out,
                    pid=pid,
                )
                return
            log(
                "qc_candidate_rejected",
                qc_sequence=int(row["qc_sequence"]),
                row_id=row_id,
                attempt=attempt,
                validation_error=committed.stdout.strip(),
            )
        else:
            log(
                "qc_worker_attempt_incomplete",
                qc_sequence=int(row["qc_sequence"]),
                row_id=row_id,
                attempt=attempt,
                exit_code=exit_code,
                timed_out=timed_out,
                candidate_exists=candidate.is_file(),
                evidence_exists=evidence.is_file(),
            )

        if attempt == max_attempts:
            raise RuntimeError(f"Maximum QC attempts exhausted for {row_id}")
        archive_attempt(row, attempt, receipt)
        task_name = f"retry{attempt}_qc_row_{int(row_id.split('-')[1]):04d}"
        require_controller("retask-prompt", row_id, task_name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-sequence", type=int, required=True)
    parser.add_argument("--end-sequence", type=int, required=True)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    args = parser.parse_args()
    rows = queue_rows()
    if args.start_sequence < 1 or args.end_sequence < args.start_sequence or args.end_sequence > len(rows):
        raise SystemExit("Invalid inclusive QC sequence range")
    selected = [row for row in rows if args.start_sequence <= int(row["qc_sequence"]) <= args.end_sequence]
    if [int(row["qc_sequence"]) for row in selected] != list(range(args.start_sequence, args.end_sequence + 1)):
        raise SystemExit("QC queue sequence is not contiguous")
    log(
        "qc_runner_started",
        start_sequence=args.start_sequence,
        end_sequence=args.end_sequence,
        max_attempts=args.max_attempts,
        timeout_seconds=args.timeout_seconds,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
    )
    try:
        for row in selected:
            process_row(row, args.max_attempts, args.timeout_seconds)
    except Exception as exc:
        log("qc_runner_stopped_on_error", error=str(exc))
        raise
    log("qc_runner_completed", start_sequence=args.start_sequence, end_sequence=args.end_sequence)


if __name__ == "__main__":
    main()
