#!/usr/bin/env python3
"""
Bioinformatics Intro Exercise
A simulated sequencing pipeline introducing key concepts.
"""

import sys
import os

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


def print_banner():
    print(c("""
╔══════════════════════════════════════════════════╗
║        Bioinformatics Intro Exercise             ║
║        Clinical Bioinformatics Training          ║
╚══════════════════════════════════════════════════╝
""", CYAN, BOLD))


def prompt_readme():
    print(c("Before continuing, please read the ", DIM) +
          c("README.md", BOLD) +
          c(" file in this repository.", DIM))
    print(c("It contains background information and instructions for this exercise.\n", DIM))
    response = input(c("Have you read the README? Press Y to continue: ", YELLOW)).strip().lower()
    if response != "y":
        print(c("\nPlease read the README.md file before continuing. See you soon!\n", DIM))
        sys.exit(0)
    print()


def get_name():
    name = input(c("Please enter your name: ", YELLOW)).strip()
    if not name:
        print(c("Name cannot be empty.", RED))
        sys.exit(1)
    return name


def validate_samplesheet():
    print(c("\n[ Step 1 ]", CYAN, BOLD) + c(" Validating SampleSheet.csv...", BOLD))

    errors = []
    in_data_section = False

    with open(SAMPLESHEET_PATH) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if line == "[Data]":
                in_data_section = True
                continue
            if in_data_section and line.startswith("Sample_ID"):
                continue  # skip header row
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

    # Collect sample IDs for display
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


if __name__ == "__main__":
    print_banner()
    prompt_readme()
    name = get_name()
    print(c(f"\n  Hello, {name}! Let's get started.\n", GREEN))

    samples = validate_samplesheet()
    if samples is None:
        sys.exit(1)

    print_challenge()
