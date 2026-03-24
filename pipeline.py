#!/usr/bin/env python3
"""
Bioinformatics Intro Exercise
A simulated sequencing pipeline introducing key concepts.
"""

import sys
import os
import select
import tty
import termios

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

RUN_FOLDER = "240315_M00123_0042_000000000-ABCDE"
SAMPLESHEET_PATH = os.path.join(RUN_FOLDER, "SampleSheet.csv")
VCF_PATH = os.path.join("output", "variants.vcf")

# ---------------------------------------------------------------------------
# MCQ definitions — based on "The Illumina Run Folder" section of README.md
# ---------------------------------------------------------------------------

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


def run_quiz():
    print(c("─" * 52, DIM))
    print(c("\n  Before continuing, open the README and read the", DIM))
    print(c("  'The Illumina Run Folder' section.\n", BOLD))
    print(c("  Then answer a few quick questions to confirm\n  you've taken it in.\n", DIM))

    response = input(c("  Ready? Press Y to start: ", YELLOW)).strip().lower()
    if response != "y":
        print(c("\n  Come back when you're ready. Good luck!\n", DIM))
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


# ---------------------------------------------------------------------------
# Banner, name, samplesheet, challenge
# ---------------------------------------------------------------------------

def print_banner():
    print(c("""
╔══════════════════════════════════════════════════╗
║        Bioinformatics Intro Exercise             ║
║        Clinical Bioinformatics Training          ║
╚══════════════════════════════════════════════════╝
""", CYAN, BOLD))


def get_name():
    name = input(c("\n  Please enter your name: ", YELLOW)).strip()
    if not name:
        print(c("  Name cannot be empty.", RED))
        sys.exit(1)
    return name


def validate_samplesheet():
    print(c("\n[ TASK 1 ]", CYAN, BOLD) + c(" Validating SampleSheet.csv...", BOLD))

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
        print(c("\n  VALIDATION FAILED\n", RED, BOLD))
        for lineno, sample_id in errors:
            print(c(f"  Line {lineno}: ", RED) +
                  f"Sample_ID {c(repr(sample_id), YELLOW)} contains a space.")
            print(c(f"           Use underscores instead — e.g. '{sample_id.replace(' ', '_')}'\n", DIM))
        print(c(f"  Task 1: Fix the error in ", DIM) +
              c(SAMPLESHEET_PATH, BOLD) +
              c(" and re-run the script.\n", DIM))
        return None

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
                samples.append((parts[0], parts[1]))

    print(c(f"\n  VALIDATION PASSED", GREEN, BOLD) +
          c(f" — {len(samples)} sample(s) found:\n", GREEN))
    for sample_id, sample_name in samples:
        print(c(f"    ✓  {sample_id}", GREEN) + c(f"  ({sample_name})", DIM))
    return samples


def print_challenge():
    print(c("\n[ Step 2 ]", CYAN, BOLD) + c(" Variant calling complete.\n", BOLD))
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_banner()
    run_quiz()
    name = get_name()
    print(c(f"\n  Hello, {name}! Let's get started.\n", GREEN))

    samples = validate_samplesheet()
    if samples is None:
        sys.exit(1)

    print_challenge()
