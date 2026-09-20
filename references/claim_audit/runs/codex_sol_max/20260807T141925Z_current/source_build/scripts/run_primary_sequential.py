#!/usr/bin/env python3
"""Launch one fresh Codex Sol Max worker per primary row, strictly sequentially."""

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
PROJECT_DIR = RUN_DIR.parents[4]
QUEUE_PATH = RUN_DIR / "queue.tsv"
CONTROLLER = RUN_DIR / "source_build/scripts/current_controller.py"
PYTHON_DEPS = PROJECT_DIR / "references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps"
CODEX = Path("/Users/manebrasil/.nvm/versions/node/v22.22.1/bin/codex")
PROGRESS_LOG = RUN_DIR / "source_build/primary_runner_progress.jsonl"
RECEIPTS = RUN_DIR / "source_build/worker_receipts"
ATTEMPT_LOGS = RUN_DIR / "source_build/worker_logs"
ABORTED = RUN_DIR / "source_build/aborted_attempts"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "max"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(event: str, **fields: object) -> None:
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now(), "event": event, **fields}
    with PROGRESS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def environment() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(PYTHON_DEPS) + (os.pathsep + existing if existing else "")
    return env


def controller(*args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(CONTROLLER), *args],
        cwd=PROJECT_DIR,
        env=environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log("controller", args=list(args), exit_code=completed.returncode, output=completed.stdout.strip())
    return completed


def require_controller(*args: str) -> None:
    completed = controller(*args)
    if completed.returncode:
        raise RuntimeError(completed.stdout.strip())


def queue_rows() -> list[dict[str, str]]:
    with QUEUE_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def preflight(timeout: int) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    output = RUN_DIR / "source_build/runtime_preflight.txt"
    prompt = (
        "Runtime preflight only. You were explicitly launched as gpt-5.6-sol with "
        "model_reasoning_effort=max and no fallback. If and only if that is the effective "
        "runtime, reply exactly: RUNTIME_OK gpt-5.6-sol max. Otherwise reply RUNTIME_MISMATCH. "
        "Do not inspect or modify any files."
    )
    command = [
        str(CODEX), "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
        "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
        "--model", MODEL, "--config", f'model_reasoning_effort="{REASONING_EFFORT}"',
        "--cd", str(RUN_DIR), "--output-last-message", str(output), "-",
    ]
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        env=environment(),
    )
    receipt = output.read_text(encoding="utf-8").strip() if output.is_file() else ""
    if completed.returncode != 0 or receipt != "RUNTIME_OK gpt-5.6-sol max":
        raise RuntimeError(
            f"Runtime preflight failed: exit={completed.returncode}, receipt={receipt!r}, "
            f"stderr={completed.stderr[-2000:]!r}"
        )
    log(
        "runtime_preflight_passed",
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        codex_version=subprocess.run([str(CODEX), "--version"], capture_output=True, text=True).stdout.strip(),
        receipt=receipt,
    )


def archive_attempt(row_id: str, attempt: int) -> None:
    ABORTED.mkdir(parents=True, exist_ok=True)
    candidates = [
        RUN_DIR / f"source_build/candidates/{row_id}.candidate.json",
        RUN_DIR / f"evidence_pages/{row_id}.pdf",
        RUN_DIR / f"evidence_pages/{row_id}.html",
    ]
    archived = []
    for source in candidates:
        if source.exists():
            destination = ABORTED / f"{row_id}.attempt{attempt}{source.suffix}"
            if destination.exists():
                destination = ABORTED / f"{row_id}.attempt{attempt}.{int(datetime.now().timestamp())}{source.suffix}"
            shutil.move(str(source), str(destination))
            archived.append(destination.relative_to(RUN_DIR).as_posix())
    log("attempt_archived", row_id=row_id, attempt=attempt, artifacts=archived)


def launch(row: dict[str, str], attempt: int, timeout: int) -> tuple[int, bool]:
    row_id = row["row_id"]
    prompt_path = RUN_DIR / row["worker_prompt_path"]
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ATTEMPT_LOGS.mkdir(parents=True, exist_ok=True)
    receipt = RECEIPTS / f"{row_id}.attempt{attempt}.txt"
    worker_log = ATTEMPT_LOGS / f"{row_id}.attempt{attempt}.log"
    command = [
        str(CODEX), "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
        "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
        "--model", MODEL, "--config", f'model_reasoning_effort="{REASONING_EFFORT}"',
        "--cd", str(RUN_DIR), "--output-last-message", str(receipt), "-",
    ]
    log(
        "worker_started",
        row_id=row_id,
        attempt=attempt,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        task=row["worker_task_name"],
    )
    with prompt_path.open("rb") as stdin, worker_log.open("wb") as output:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_DIR,
            env=environment(),
            stdin=stdin,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        timed_out = False
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait(timeout=30)
    log(
        "worker_exited",
        row_id=row_id,
        attempt=attempt,
        exit_code=exit_code,
        timed_out=timed_out,
        candidate=(RUN_DIR / f"source_build/candidates/{row_id}.candidate.json").is_file(),
        pdf_evidence=(RUN_DIR / f"evidence_pages/{row_id}.pdf").is_file(),
        html_evidence=(RUN_DIR / f"evidence_pages/{row_id}.html").is_file(),
    )
    return exit_code, timed_out


def process(row_id: str, max_attempts: int, timeout: int) -> None:
    for attempt in range(1, max_attempts + 1):
        require_controller("make-prompt", row_id)
        row = next(row for row in queue_rows() if row["row_id"] == row_id)
        exit_code, timed_out = launch(row, attempt, timeout)
        candidate = RUN_DIR / f"source_build/candidates/{row_id}.candidate.json"
        evidence = RUN_DIR / f"evidence_pages/{row_id}.{'html' if row['source_type'] == 'LEGAL_HTML' else 'pdf'}"
        if candidate.is_file() and evidence.is_file() and (exit_code == 0 or timed_out):
            committed = controller("commit", row_id)
            if committed.returncode == 0:
                log("row_committed", row_id=row_id, attempt=attempt)
                return
            log("candidate_rejected", row_id=row_id, attempt=attempt, reason=committed.stdout[-6000:])
        else:
            log("worker_incomplete", row_id=row_id, attempt=attempt, exit_code=exit_code, timed_out=timed_out)
        if attempt == max_attempts:
            raise RuntimeError(f"Maximum attempts exhausted for {row_id}")
        archive_attempt(row_id, attempt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--preflight-timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0, help="Process at most this many pending rows; zero means all")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if args.max_attempts < 1 or args.timeout_seconds < 60 or args.limit < 0:
        raise SystemExit("Invalid runner arguments")
    if not args.skip_preflight:
        preflight(args.preflight_timeout)
    pending = [row["row_id"] for row in queue_rows() if row["queue_status"] != "COMPLETED"]
    if args.limit:
        pending = pending[: args.limit]
    log("primary_runner_started", pending=len(pending), limit=args.limit)
    try:
        for row_id in pending:
            process(row_id, args.max_attempts, args.timeout_seconds)
    except Exception as exc:
        log("primary_runner_stopped", error=str(exc))
        raise
    require_controller("verify")
    log("primary_runner_completed", processed=len(pending))


if __name__ == "__main__":
    main()
