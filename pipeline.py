#!/usr/bin/env python3
"""
Bioinformatics Intro Exercise
A simulated sequencing pipeline introducing key concepts.
"""

import sys
import os
import json
import gzip
import select
import shlex
import shutil
import subprocess
import tty
import termios
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen

# ANSI colour helpers
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"

def c(text, *codes):
    return "".join(codes) + text + RESET


def normalise_shell_command(cmd):
    return " ".join(cmd.strip().split())

RUN_FOLDER = "240315_M00123_0042_000000000-ABCDE"
SAMPLESHEET_PATH = os.path.join(RUN_FOLDER, "SampleSheet.csv")
VCF_PATH = os.path.join("output", "variants.vcf")
FASTQ_OUTPUT_DIR = os.path.join("output", "fastq")
DETAILS_PATH = "details.json"
DEFAULT_CHECKPOINT_WEBHOOK = "https://eo50e4i80bv4hnb.m.pipedream.net"
CHECKPOINT_WEBHOOK = os.getenv("PIPELINE_CHECKPOINT_WEBHOOK", DEFAULT_CHECKPOINT_WEBHOOK).strip()
CHECKPOINT_TOKEN = os.getenv("PIPELINE_CHECKPOINT_TOKEN", "").strip()
RUN_SESSION_ID = os.getenv("PIPELINE_SESSION_ID", str(uuid.uuid4()))
CHECKPOINT_TIMEOUT_SECONDS = 3


def notify_checkpoint(event, details, status="ok", extra=None):
    """Best-effort checkpoint notifier for external assessment tracking."""
    if not CHECKPOINT_WEBHOOK:
        return

    progress = {
        "ngs_mcq_complete": bool(details.get("ngs_mcq_complete")),
        "mcq_complete": bool(details.get("mcq_complete")),
        "task1_complete": bool(details.get("task1_complete")),
        "task2_complete": bool(details.get("task2_complete")),
        "fastq_mcq_complete": bool(details.get("fastq_mcq_complete")),
    }

    payload = {
        "event": event,
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": RUN_SESSION_ID,
        "candidate_name": details.get("name"),
        "progress": progress,
        "extra": extra or {},
    }

    headers = {"Content-Type": "application/json"}
    if CHECKPOINT_TOKEN:
        headers["Authorization"] = f"Bearer {CHECKPOINT_TOKEN}"

    request = Request(
        CHECKPOINT_WEBHOOK,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=CHECKPOINT_TIMEOUT_SECONDS) as response:
            response.read(1)
    except Exception:
        # Never block the exercise if the endpoint is unavailable.
        pass


# ---------------------------------------------------------------------------
# Save / load progress
# ---------------------------------------------------------------------------

def load_details():
    if os.path.exists(DETAILS_PATH):
        with open(DETAILS_PATH) as f:
            return json.load(f)
    return {}


def save_details(details):
    with open(DETAILS_PATH, "w") as f:
        json.dump(details, f, indent=2)

# ---------------------------------------------------------------------------
# MCQ definitions — based on README background sections
# ---------------------------------------------------------------------------

NGS_INTRO_QUESTIONS = [
    {
        "question": "In NGS, what does coverage (depth) refer to?",
        "options": [
            "The number of unique genes included in a panel",
            "How many times a genomic position is sequenced",
            "The percentage of samples that pass QC in a batch",
            "The number of cycles used for index reads",
        ],
        "correct": 1,
    },
    {
        "question": "What is paired-end sequencing?",
        "options": [
            "Sequencing both ends of the same DNA fragment",
            "Sequencing two samples on the same flow cell lane",
            "Running the same sample on two instruments",
            "Using two index reads instead of one",
        ],
        "correct": 0,
    },
    {
        "question": "What does a Q30 base quality score indicate?",
        "options": [
            "About 1 error in 10 bases",
            "About 1 error in 100 bases",
            "About 1 error in 1000 bases",
            "No base-calling errors",
        ],
        "correct": 2,
    },
]

QUESTIONS = [
    {
        "question": "What does the presence of RTAComplete.txt in a run folder indicate?",
        "options": [
            "The SampleSheet has been validated successfully",
            "Base-calling has finished and the run is ready to process",
            "Demultiplexing has completed and FASTQ files are available",
            "The flow cell has been loaded into the instrument",
        ],
        "correct": 1,
    },
    {
        "question": "What is demultiplexing?",
        "options": [
            "Compressing FASTQ files to save disk space",
            "Converting raw base intensities into quality scores",
            "Sorting sequencing reads into per-sample files using index sequences",
            "Aligning reads to a reference genome",
        ],
        "correct": 2,
    },
    {
        "question": "Which section of the SampleSheet contains the per-sample data table?",
        "options": [
            "[Header]",
            "[Reads]",
            "[Settings]",
            "[Data]",
        ],
        "correct": 3,
    },
    {
        "question": "What could cause an entire sequencing run to fail demultiplexing?",
        "options": [
            "Running bcl2fastq on a machine with insufficient RAM",
            "A typo in a sample ID or index sequence in the SampleSheet",
            "Sequencing more than 10 samples on a single flow cell",
            "Using paired-end reads instead of single-end reads",
        ],
        "correct": 1,
    },
]

FASTQ_QUESTIONS = [
    {
        "question": "Which 4-line structure correctly describes one FASTQ record?",
        "options": [
            "@header, sequence, +separator, quality string",
            ">header, sequence, quality string, +separator",
            "@header, +separator, sequence, quality string",
            "header, sequence, sequence length, quality string",
        ],
        "correct": 0,
    },
]


# ---------------------------------------------------------------------------
# Terminal key reading
# ---------------------------------------------------------------------------

def read_key():
    """Read a single keypress, returning a string token."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b'\x1b':
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                ch += os.read(fd, 2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------------------------------------------------------------------------
# MCQ runner
# ---------------------------------------------------------------------------

def ask_question(number, total, question, options, correct_index):
    """Display one MCQ with arrow-key selection. Returns True if correct."""
    selected = 0
    n = len(options)

    print(c(f"\n  Question {number} of {total}\n", DIM))
    print(c(f"  {question}\n", BOLD))

    def render(final=False):
        sys.stdout.write("\033[u")  # restore saved cursor position
        sys.stdout.write("\033[J")  # clear from cursor to end of screen
        for i, opt in enumerate(options):
            if final:
                if i == selected == correct_index:
                    sys.stdout.write(c(f"   ✓  {opt}", GREEN, BOLD) + "\n")
                elif i == selected:
                    sys.stdout.write(c(f"   ✗  {opt}", RED, BOLD) + "\n")
                elif i == correct_index:
                    sys.stdout.write(c(f"   ✓  {opt}", GREEN) + "\n")
                else:
                    sys.stdout.write(c(f"      {opt}", DIM) + "\n")
            else:
                if i == selected:
                    sys.stdout.write(c(f"   ▶  {opt}", CYAN, BOLD) + "\n")
                else:
                    sys.stdout.write(c(f"      {opt}", DIM) + "\n")
        if not final:
            sys.stdout.write(c("\n  ↑ ↓ to move   Enter to confirm\n\n", DIM))
        sys.stdout.flush()

    sys.stdout.write("\033[s")  # save cursor position (start of options block)
    render()

    while True:
        key = read_key()
        if key in (b'\r', b'\n'):
            break
        elif key == b'\x03':
            print()
            sys.exit(0)
        elif key == b'\x1b[A':
            selected = (selected - 1) % n
        elif key == b'\x1b[B':
            selected = (selected + 1) % n
        else:
            continue
        render()

    render(final=True)

    correct = selected == correct_index
    if correct:
        print(c("\n  Correct!\n", GREEN, BOLD))
    else:
        print(c(f"\n  Not quite — the answer was: ", RED) +
              c(options[correct_index], BOLD) + "\n")

    return correct


def run_quiz(details):
    if details.get("mcq_complete"):
        score = details.get("mcq_score", "?")
        total = len(QUESTIONS)
        print(c("─" * 52, DIM))
        print(c(f"\n  Quiz already completed ", DIM) +
              c(f"({score}/{total})", GREEN) +
              c(" — skipping.\n", DIM))
        print(c("─" * 52, DIM))
        notify_checkpoint(
            "illumina_quiz_skipped",
            details,
            extra={"reason": "already_completed", "score": score, "total": total},
        )
        return

    print(c("─" * 52, DIM))
    print(c("\n  Before continuing, open the README and read the", DIM))
    print(c("  'The Illumina Run Folder' section.\n", BOLD))
    print(c("  Then answer a few quick questions to confirm\n  you've taken it in.\n", DIM))

    response = input(c("  Ready? Press Y to start: ", YELLOW)).strip().lower()
    if response != "y":
        print(c("\n  Come back when you're ready. Good luck!\n", DIM))
        notify_checkpoint("illumina_quiz_declined", details, status="stopped")
        sys.exit(0)

    total = len(QUESTIONS)
    score = 0
    for i, q in enumerate(QUESTIONS, 1):
        correct = ask_question(i, total, q["question"], q["options"], q["correct"])
        if correct:
            score += 1

    print(c("─" * 52, DIM))
    if score == total:
        print(c(f"\n  {score}/{total} — Perfect score! Great work.\n", GREEN, BOLD))
    elif score >= total // 2:
        print(c(f"\n  {score}/{total} — Good effort. ", YELLOW, BOLD) +
              c("It's worth re-reading any sections you missed.\n", DIM))
    else:
        print(c(f"\n  {score}/{total} — ", RED, BOLD) +
              c("Have another read through the README before continuing.\n", DIM))

    print(c("─" * 52, DIM))

    details["mcq_complete"] = True
    details["mcq_score"] = score
    save_details(details)
    notify_checkpoint(
        "illumina_quiz_completed",
        details,
        extra={"score": score, "total": total},
    )


def run_ngs_intro_quiz(details):
    total = len(NGS_INTRO_QUESTIONS)
    if details.get("ngs_mcq_complete") and details.get("ngs_mcq_total") == total:
        score = details.get("ngs_mcq_score", "?")
        print(c("─" * 52, DIM))
        print(c(f"\n  NGS intro quiz already completed ", DIM) +
              c(f"({score}/{total})", GREEN) +
              c(" — skipping.\n", DIM))
        print(c("─" * 52, DIM))
        notify_checkpoint(
            "ngs_quiz_skipped",
            details,
            extra={"reason": "already_completed", "score": score, "total": total},
        )
        return

    print(c("─" * 52, DIM))
    print(c("\n  First, open the README and read the", DIM))
    print(c("  'Next Generation Sequencing (NGS)' section.\n", BOLD))
    if details.get("ngs_mcq_complete"):
        print(c("  The NGS quiz has been updated — you'll run the latest version.\n", DIM))
    else:
        print(c("  Then answer a few quick warm-up questions.\n", DIM))

    response = input(c("  Ready? Press Y to start: ", YELLOW)).strip().lower()
    if response != "y":
        print(c("\n  Come back when you're ready. Good luck!\n", DIM))
        notify_checkpoint("ngs_quiz_declined", details, status="stopped")
        sys.exit(0)

    score = 0
    for i, q in enumerate(NGS_INTRO_QUESTIONS, 1):
        correct = ask_question(i, total, q["question"], q["options"], q["correct"])
        if correct:
            score += 1

    details["ngs_mcq_complete"] = True
    details["ngs_mcq_score"] = score
    details["ngs_mcq_total"] = total
    details.pop("ngs_mcq_correct", None)
    save_details(details)
    notify_checkpoint(
        "ngs_quiz_completed",
        details,
        extra={"score": score, "total": total},
    )


def run_fastq_quiz(details):
    total = len(FASTQ_QUESTIONS)
    if details.get("fastq_mcq_complete") and details.get("fastq_mcq_total") == total:
        score = details.get("fastq_mcq_score", "?")
        print(c("─" * 52, DIM))
        print(c(f"\n  FASTQ check already completed ", DIM) +
              c(f"({score}/{total})", GREEN) +
              c(" — skipping.\n", DIM))
        print(c("─" * 52, DIM))
        notify_checkpoint(
            "fastq_quiz_skipped",
            details,
            extra={"reason": "already_completed", "score": score, "total": total},
        )
        return

    print(c("─" * 52, DIM))
    print(c("\n  Before Task 3, open the README and read the", DIM))
    print(c("  'FASTQ Files' section.\n", BOLD))
    print(c("  Then answer a quick FASTQ check.\n", DIM))

    response = input(c("  Ready? Press Y to start: ", YELLOW)).strip().lower()
    if response != "y":
        print(c("\n  Come back when you're ready. Good luck!\n", DIM))
        notify_checkpoint("fastq_quiz_declined", details, status="stopped")
        sys.exit(0)

    score = 0
    for i, q in enumerate(FASTQ_QUESTIONS, 1):
        correct = ask_question(i, total, q["question"], q["options"], q["correct"])
        if correct:
            score += 1

    details["fastq_mcq_complete"] = True
    details["fastq_mcq_score"] = score
    details["fastq_mcq_total"] = total
    save_details(details)
    notify_checkpoint(
        "fastq_quiz_completed",
        details,
        extra={"score": score, "total": total},
    )


# ---------------------------------------------------------------------------
# Banner, name, task runners
# ---------------------------------------------------------------------------

def print_banner():
    print(c("""
╔══════════════════════════════════════════════════╗
║        Bioinformatics Intro Exercise             ║
║        Clinical Bioinformatics Training          ║
╚══════════════════════════════════════════════════╝
""", CYAN, BOLD))


def get_name(details):
    if details.get("name"):
        print(c(f"\n  Welcome back, {details['name']}!\n", GREEN))
        return details["name"]

    name = input(c("\n  Please enter your name: ", YELLOW)).strip()
    if not name:
        print(c("  Name cannot be empty.", RED))
        sys.exit(1)
    details["name"] = name
    save_details(details)
    return name


def print_task_header(task_number, task_title):
    print(c("\n" + "═" * 52, CYAN, DIM))
    print(c(f"  TASK {task_number}: {task_title}", CYAN, BOLD))
    print(c("═" * 52, CYAN, DIM))


def load_samples_from_samplesheet():
    samples = []
    in_data_section = False
    with open(SAMPLESHEET_PATH) as f:
        for line in f:
            line = line.strip()
            if line == "[Data]":
                in_data_section = True
                continue
            if in_data_section and line.startswith("Sample_ID"):
                continue
            if in_data_section and line:
                parts = line.split(",")
                if len(parts) >= 2:
                    samples.append((parts[0], parts[1]))
    return samples


def create_simulated_fastqs(samples, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    r1_seq = "ACGTGCTAGCTAGCTAACGTGCTAGCTAGCTAACGTGCTAGCTAGCTA"
    r2_seq = "TAGCTAGCTAGCACGTTAGCTAGCTAGCACGTTAGCTAGCTAGCACGT"
    r1_qual = "I" * len(r1_seq)
    r2_qual = "I" * len(r2_seq)

    created = []
    for idx, (sample_id, _) in enumerate(samples, 1):
        safe_sample_id = sample_id.replace(" ", "_")
        for read_label, seq, qual in (("R1", r1_seq, r1_qual), ("R2", r2_seq, r2_qual)):
            fastq_name = f"{safe_sample_id}_S{idx}_L001_{read_label}_001.fastq.gz"
            fastq_path = os.path.join(output_dir, fastq_name)
            with gzip.open(fastq_path, "wt") as f:
                f.write(f"@SIM:{safe_sample_id}:L001:{read_label}:0001\n")
                f.write(seq + "\n")
                f.write("+\n")
                f.write(qual + "\n")
            created.append(fastq_name)
    return created


def run_demultiplex(samples, details):
    print_task_header(2, "Run Demultiplexing")

    existing_fastqs = []
    if os.path.isdir(FASTQ_OUTPUT_DIR):
        existing_fastqs = sorted(
            f for f in os.listdir(FASTQ_OUTPUT_DIR) if f.endswith(".fastq.gz")
        )

    if details.get("task2_complete") and existing_fastqs:
        print(c("  Already complete — skipping.\n", DIM))
        notify_checkpoint(
            "task2_demultiplex_skipped",
            details,
            extra={"reason": "already_completed", "fastq_count": len(existing_fastqs)},
        )
        return
    if details.get("task2_complete") and not existing_fastqs:
        print(c("  Task marked complete but no FASTQ files were found. Re-running demultiplexing.\n", DIM))

    os.makedirs(FASTQ_OUTPUT_DIR, exist_ok=True)

    expected_cmd = (
        f"bcl2fastq --runfolder-dir {RUN_FOLDER} "
        f"--sample-sheet {SAMPLESHEET_PATH} "
        f"--output-dir {FASTQ_OUTPUT_DIR} "
        "--no-lane-splitting"
    )

    print(c("  Open README.md > '🟩 Task 2 — Run Demultiplexing'.", DIM))
    print(c("  Build the command from the placeholders shown there, then paste it below.\n", DIM))

    while True:
        pasted_cmd = input(c("  Paste command: ", YELLOW)).strip()
        if not pasted_cmd:
            print(c("  Please paste your completed command from the README template.\n", RED))
            continue
        if normalise_shell_command(pasted_cmd) != normalise_shell_command(expected_cmd):
            print(c("  That command is not correct for this run folder. Check the placeholder values and try again.\n", RED))
            continue
        break

    cmd = shlex.split(pasted_cmd)
    print(c("\n  Running demultiplex command...\n", BOLD))

    used_simulation = False
    bcl2fastq_bin = shutil.which("bcl2fastq")

    if bcl2fastq_bin:
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(c("  bcl2fastq2 completed successfully.\n", GREEN, BOLD))
            else:
                used_simulation = True
                print(c("  bcl2fastq2 could not process this simulated run folder.\n", YELLOW, BOLD))
                if result.stderr.strip():
                    last_line = result.stderr.strip().splitlines()[-1]
                    print(c(f"  {last_line}\n", DIM))
        except OSError as exc:
            used_simulation = True
            print(c(f"  bcl2fastq2 failed to start: {exc}\n", YELLOW))
    else:
        used_simulation = True
        print(c("  bcl2fastq2 not found in this environment.\n", YELLOW))

    if used_simulation:
        created_fastqs = create_simulated_fastqs(samples, FASTQ_OUTPUT_DIR)
        print(c("  Created simulated FASTQ files in ", DIM) +
              c(FASTQ_OUTPUT_DIR, BOLD) + c(".\n", DIM))
    else:
        created_fastqs = sorted(
            f for f in os.listdir(FASTQ_OUTPUT_DIR) if f.endswith(".fastq.gz")
        )
        if created_fastqs:
            print(c("  FASTQ files written to ", DIM) +
                  c(FASTQ_OUTPUT_DIR, BOLD) + c(".\n", DIM))
        else:
            used_simulation = True
            created_fastqs = create_simulated_fastqs(samples, FASTQ_OUTPUT_DIR)
            print(c("  bcl2fastq2 completed but no FASTQs were produced from this simulated run.\n", YELLOW))
            print(c("  Created simulated FASTQ files in ", DIM) +
                  c(FASTQ_OUTPUT_DIR, BOLD) + c(".\n", DIM))

    if created_fastqs:
        for name in created_fastqs:
            print(c(f"    ✓  {name}", GREEN))
        print()

    details["task2_complete"] = True
    details["task2_mode"] = "simulated" if used_simulation else "bcl2fastq2"
    details["task2_output_dir"] = FASTQ_OUTPUT_DIR
    save_details(details)
    notify_checkpoint(
        "task2_demultiplex_completed",
        details,
        extra={
            "mode": details["task2_mode"],
            "fastq_count": len(created_fastqs),
            "output_dir": FASTQ_OUTPUT_DIR,
        },
    )


def validate_samplesheet(details):
    print_task_header(1, "Fix the SampleSheet")

    if details.get("task1_complete"):
        print(c("  Already complete — skipping.\n", DIM))
        notify_checkpoint(
            "task1_samplesheet_skipped",
            details,
            extra={"reason": "already_completed"},
        )
        return load_samples_from_samplesheet()

    print(c("  Validating SampleSheet.csv...\n", BOLD))

    errors = []
    in_data_section = False

    with open(SAMPLESHEET_PATH) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if line == "[Data]":
                in_data_section = True
                continue
            if in_data_section and line.startswith("Sample_ID"):
                continue
            if in_data_section and line:
                sample_id = line.split(",")[0]
                if " " in sample_id:
                    errors.append((lineno, sample_id))

    if errors:
        notify_checkpoint(
            "task1_samplesheet_validation_failed",
            details,
            status="error",
            extra={
                "invalid_sample_id_count": len(errors),
                "line_numbers": [lineno for lineno, _ in errors],
            },
        )
        print(c("\n  VALIDATION FAILED\n", RED, BOLD))
        for lineno, sample_id in errors:
            print(c(f"  Line {lineno}: ", RED) +
                  f"Sample_ID {c(repr(sample_id), YELLOW)} contains a space.")
            print(c(f"           Use underscores instead — e.g. '{sample_id.replace(' ', '_')}'\n", DIM))
        print(c(f"  Task 1: Fix the error in ", DIM) +
              c(SAMPLESHEET_PATH, BOLD) + c(".\n", DIM))
        print(c("          See README.md > '🟩 Task 1 — Fix the SampleSheet' for instructions.\n", DIM))
        return None

    samples = load_samples_from_samplesheet()

    print(c(f"\n  VALIDATION PASSED", GREEN, BOLD) +
          c(f" — {len(samples)} sample(s) found:\n", GREEN))
    for sample_id, sample_name in samples:
        print(c(f"    ✓  {sample_id}", GREEN) + c(f"  ({sample_name})", DIM))

    details["task1_complete"] = True
    save_details(details)
    notify_checkpoint(
        "task1_samplesheet_completed",
        details,
        extra={"sample_count": len(samples)},
    )
    return samples


def print_challenge(details):
    print_task_header(3, "Inspect the VCF")
    print(c("  Variant calling complete.\n", BOLD))
    print(c("  The file ", DIM) + c(VCF_PATH, BOLD) +
          c(" contains variant calls for all samples.\n", DIM))

    print(c("┌─ CHALLENGE ──────────────────────────────────────────┐", YELLOW, BOLD))
    print(c("│                                                      │", YELLOW))
    print(c("│  Open the VCF in the editor and answer:             │", YELLOW))
    print(c("│                                                      │", YELLOW))
    print(c("│  Which sample carries the BRCA1 variant that        │", YELLOW))
    print(c("│  passed quality filters?                            │", YELLOW))
    print(c("│                                                      │", YELLOW))
    print(c("└──────────────────────────────────────────────────────┘\n", YELLOW, BOLD))

    print(c("  Genotype key:\n", DIM))
    print(c("    0/0", BOLD) + c("  homozygous reference  ", DIM) + c("(no variant)", DIM))
    print(c("    0/1", BOLD) + c("  heterozygous          ", DIM) + c("(one copy of the variant)", DIM))
    print(c("    1/1", BOLD) + c("  homozygous alternate  ", DIM) + c("(two copies of the variant)\n", DIM))

    print(c("  Hints:\n", DIM))
    print(c("    - Lines starting with '##' are metadata headers — skip these.", DIM))
    print(c("    - The FILTER column tells you whether a variant passed quality checks.", DIM))
    print(c("    - The INFO column contains GENE=<name> to identify the gene.\n", DIM))
    notify_checkpoint("task3_challenge_displayed", details)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_banner()

    details = load_details()
    notify_checkpoint(
        "pipeline_started",
        details,
        extra={"run_folder": RUN_FOLDER, "script": os.path.basename(__file__)},
    )

    name = get_name(details)
    notify_checkpoint("candidate_identified", details, extra={"candidate_name": name})
    if not details.get("mcq_complete"):
        print(c(f"\n  Hello, {name}! Let's get started.\n", GREEN))

    run_ngs_intro_quiz(details)
    run_quiz(details)

    samples = validate_samplesheet(details)
    if samples is None:
        notify_checkpoint("pipeline_stopped_after_task1", details, status="stopped")
        sys.exit(1)

    run_demultiplex(samples, details)
    run_fastq_quiz(details)
    print_challenge(details)
    notify_checkpoint("pipeline_finished", details)
