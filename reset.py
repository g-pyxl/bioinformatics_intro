#!/usr/bin/env python3
"""
Reset local exercise state.

Removes learner-generated files while preserving repository-tracked files.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SAMPLESHEET_PATH = ROOT / "240315_M00123_0042_000000000-ABCDE" / "SampleSheet.csv"
DEFAULT_SAMPLESHEET = """[Header]
IEMFileVersion,5
Experiment Name,Training Exercise
Date,15/03/2024
Workflow,GenerateFASTQ
Application,FASTQ Only
Instrument Type,MiSeq
Description,Intro bioinformatics exercise
Chemistry,Amplicon

[Reads]
151
151

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample 1,PatientA,,,N701,TAAGGCGA,S502,ATAGAGAG,training,
Sample_2,PatientB,,,N702,CGTACTAG,S502,ATAGAGAG,training,
Sample_3,PatientC,,,N703,AGGCAGAA,S503,TATCCTCT,training,
"""


def get_tracked_paths(repo_root: Path) -> set[str]:
    """Return git-tracked repo-relative paths as POSIX strings."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return set()

    tracked = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            tracked.add(line)
    return tracked


def repo_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def remove_path(path: Path, dry_run: bool) -> str | None:
    if not path.exists():
        return None
    rel = repo_relative(path)
    if dry_run:
        return f"would remove {rel}"
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return f"removed {rel}"


def remove_untracked_output(repo_root: Path, tracked: set[str], dry_run: bool) -> list[str]:
    logs: list[str] = []
    output_dir = repo_root / "output"
    if not output_dir.exists():
        return logs

    # Remove untracked files first.
    for file_path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        rel = repo_relative(file_path)
        if tracked and rel in tracked:
            continue
        action = remove_path(file_path, dry_run)
        if action:
            logs.append(action)

    # Remove empty directories bottom-up.
    for dir_path in sorted((p for p in output_dir.rglob("*") if p.is_dir()), reverse=True):
        try:
            next(dir_path.iterdir())
            continue
        except StopIteration:
            action = remove_path(dir_path, dry_run)
            if action:
                logs.append(action)

    # Remove top-level output directory if now empty.
    try:
        next(output_dir.iterdir())
    except StopIteration:
        action = remove_path(output_dir, dry_run)
        if action:
            logs.append(action)

    return logs


def restore_default_samplesheet(dry_run: bool) -> str:
    rel = repo_relative(SAMPLESHEET_PATH)
    if dry_run:
        return f"would restore {rel} to default exercise state"
    SAMPLESHEET_PATH.write_text(DEFAULT_SAMPLESHEET, encoding="utf-8")
    return f"restored {rel} to default exercise state"


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset generated exercise files.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting files.",
    )
    args = parser.parse_args()

    tracked = get_tracked_paths(ROOT)
    actions: list[str] = []

    # Exercise progress.
    action = remove_path(ROOT / "details.json", args.dry_run)
    if action:
        actions.append(action)

    # Python cache artifacts.
    for cache_dir in sorted(ROOT.rglob("__pycache__")):
        action = remove_path(cache_dir, args.dry_run)
        if action:
            actions.append(action)

    for pyc_file in sorted(ROOT.rglob("*.pyc")):
        action = remove_path(pyc_file, args.dry_run)
        if action:
            actions.append(action)

    # Generated output files from pipeline tasks/demultiplexing.
    actions.extend(remove_untracked_output(ROOT, tracked, args.dry_run))

    # Task 1 training reset: restore the intentional SampleSheet error.
    actions.append(restore_default_samplesheet(args.dry_run))

    mode = "dry run" if args.dry_run else "reset"
    print(f"{mode} complete.")
    if actions:
        for line in actions:
            print(f" - {line}")
    else:
        print(" - nothing to clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
