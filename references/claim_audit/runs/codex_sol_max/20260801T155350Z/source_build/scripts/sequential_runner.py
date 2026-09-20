#!/usr/bin/env python3
"""Run primary claim workers strictly one at a time without reading semantics."""

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
QUEUE_PATH = RUN_DIR / "queue.tsv"
CONTROLLER = RUN_DIR / "source_build/scripts/controller.py"
PYTHON_DEPS = RUN_DIR / "source_build/python_deps"
CODEX = Path("/Users/manebrasil/.nvm/versions/node/v22.22.1/bin/codex")
PROGRESS_LOG = RUN_DIR / "source_build/runner_progress.jsonl"
ABORTED_DIR = RUN_DIR / "source_build/aborted_attempts"
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
    log(
        "controller_command",
        command=list(args),
        exit_code=completed.returncode,
        output=completed.stdout.strip(),
    )
    return completed


def require_controller(*args: str) -> None:
    completed = run_controller(*args)
    if completed.returncode != 0:
        raise RuntimeError(f"controller {' '.join(args)} failed: {completed.stdout.strip()}")


def queue_rows() -> dict[str, dict[str, str]]:
    with QUEUE_PATH.open(encoding="utf-8", newline="") as handle:
        return {row["row_id"]: row for row in csv.DictReader(handle, delimiter="\t")}


def row_id(number: int) -> str:
    return f"ROW-{number:04d}"


def archive_attempt(rid: str, attempt: int, receipt: Path) -> None:
    ABORTED_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "candidate.json": RUN_DIR / f"source_build/candidates/{rid}.candidate.json",
        "pdf": RUN_DIR / f"evidence_pages/{rid}.pdf",
        "html": RUN_DIR / f"evidence_pages/{rid}.html",
        "receipt.txt": receipt,
    }
    archived: list[str] = []
    for suffix, source in artifacts.items():
        if source.exists():
            destination = ABORTED_DIR / f"{rid}.attempt{attempt}.{suffix}"
            if destination.exists():
                raise RuntimeError(f"archive destination already exists: {destination}")
            shutil.move(str(source), str(destination))
            archived.append(destination.relative_to(RUN_DIR).as_posix())
    log("attempt_archived", row_id=rid, attempt=attempt, artifacts=archived)


def launch_worker(rid: str, task_name: str, receipt: Path, timeout_seconds: int) -> tuple[int, bool, int]:
    prompt = RUN_DIR / f"source_build/prompts/{rid}.md"
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
        "worker_started",
        row_id=rid,
        worker_task_name=task_name,
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
    log(
        "worker_exited",
        row_id=rid,
        worker_task_name=task_name,
        pid=process.pid,
        exit_code=exit_code,
        timed_out=timed_out,
        candidate_exists=(RUN_DIR / f"source_build/candidates/{rid}.candidate.json").is_file(),
        evidence_exists=(RUN_DIR / f"evidence_pages/{rid}.pdf").is_file(),
        receipt_exists=receipt.is_file(),
    )
    return exit_code, timed_out, process.pid


def process_row(number: int, max_attempts: int, timeout_seconds: int) -> None:
    rid = row_id(number)
    result_path = RUN_DIR / f"results/{rid}.json"
    if result_path.is_file():
        log("row_skipped_already_committed", row_id=rid)
        return

    rows = queue_rows()
    if rid not in rows:
        raise RuntimeError(f"row is absent from queue: {rid}")
    citation_key = rows[rid]["citation_key"]
    source_type = rows[rid]["source_type"]
    require_controller("prepare-source", citation_key)

    task_name = f"claim_row_{number:04d}"
    require_controller("make-prompt", rid)

    for attempt in range(1, max_attempts + 1):
        retry_number = attempt - 1
        receipt_name = f"{rid}.txt" if retry_number == 0 else f"{rid}.retry{retry_number}.txt"
        receipt = RUN_DIR / "source_build/worker_receipts" / receipt_name
        exit_code, timed_out, pid = launch_worker(rid, task_name, receipt, timeout_seconds)

        candidate = RUN_DIR / f"source_build/candidates/{rid}.candidate.json"
        evidence_suffix = "html" if source_type == "LEGAL_HTML" else "pdf"
        evidence = RUN_DIR / f"evidence_pages/{rid}.{evidence_suffix}"
        artifacts_ready = candidate.is_file() and evidence.is_file()
        if artifacts_ready and (exit_code == 0 or timed_out):
            normalized = run_controller("normalize-source-version-date", rid)
            if normalized.returncode == 0:
                committed = run_controller("commit", rid)
                if committed.returncode == 0:
                    if timed_out:
                        require_controller(
                            "record-runner-termination",
                            rid,
                            "--pids",
                            str(pid),
                            "--elapsed",
                            f">={timeout_seconds}s",
                            "--signal",
                            "SIGTERM",
                            "--reason",
                            "Timeout reached after candidate and evidence were written; artifacts validated before advancing",
                        )
                    log("row_committed", row_id=rid, attempt=attempt)
                    return
                log(
                    "candidate_rejected",
                    row_id=rid,
                    attempt=attempt,
                    validation_error=committed.stdout.strip(),
                )
            else:
                log(
                    "candidate_rejected",
                    row_id=rid,
                    attempt=attempt,
                    validation_error=normalized.stdout.strip(),
                )
        else:
            log(
                "worker_attempt_incomplete",
                row_id=rid,
                attempt=attempt,
                exit_code=exit_code,
                timed_out=timed_out,
                candidate_exists=candidate.is_file(),
                evidence_exists=evidence.is_file(),
            )

        if attempt == max_attempts:
            raise RuntimeError(f"maximum attempts exhausted for {rid}")
        archive_attempt(rid, attempt, receipt)
        task_name = f"retry{attempt}_claim_row_{number:04d}"
        require_controller("retask-prompt", rid, task_name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start or args.end > 227:
        raise SystemExit("invalid inclusive row range")
    if args.max_attempts < 1:
        raise SystemExit("max attempts must be positive")
    log(
        "runner_started",
        start=args.start,
        end=args.end,
        max_attempts=args.max_attempts,
        timeout_seconds=args.timeout_seconds,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
    )
    try:
        for number in range(args.start, args.end + 1):
            process_row(number, args.max_attempts, args.timeout_seconds)
    except Exception as exc:
        log("runner_stopped_on_error", error=str(exc))
        raise
    log("runner_completed", start=args.start, end=args.end)


if __name__ == "__main__":
    main()
