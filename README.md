# Bioinformatics Intro Exercise

Welcome! This exercise introduces a few basic concepts used in clinical bioinformatics pipelines. No prior bioinformatics knowledge is required — just follow the steps.

---

## Before You Start: You Need a GitHub Account

This exercise is hosted on **GitHub**. You will need a free GitHub account to complete it.

[Create a GitHub account here](https://github.com/signup) if you don't already have one.

### What is GitHub?

GitHub is a web-based platform for hosting, sharing, and collaborating on code. It is built on top of **Git**, a version control system that tracks changes to files over time — letting you see who changed what, when, and why, and roll back to earlier versions if something goes wrong.

At its core, GitHub stores code in **repositories** (repos): collections of files, their full history, and any associated discussion or documentation.

### Why does GitHub matter in clinical bioinformatics?

In a clinical setting, the software used to analyse patient samples must be:

- **Auditable** — every change to the analysis pipeline must be traceable. Git commit history provides a complete record of what code was running at any given time.
- **Version-controlled** — if a pipeline is updated, older results can be reproduced exactly by checking out the previous version of the code.
- **Validated before deployment** — GitHub's pull request and code review workflow is used to ensure changes are reviewed and approved before they affect patient results.
- **Reproducible** — by pinning software versions and storing pipeline code in a repo, analyses can be rerun identically weeks or months later.

Most clinical bioinformatics teams use GitHub (or a similar platform such as GitLab) as the central system of record for their pipelines, reference files, and validation evidence.

---

## Setup

1. **Fork this repository** — click the "Fork" button in the top-right corner of the GitHub page. This creates your own copy of the repo under your account.
2. **Open your fork in a Codespace** by navigating to `https://codespaces.new/<your-username>/bioinformatics_intro`
   (or click the green "Code" button on your fork and select "Create codespace on main").
3. **Open a terminal** in the Codespace (`Terminal > New Terminal`).

---

## Starting the exercise

<details>
<summary><strong>The Run Folder</strong></summary>

This repository contains a folder called `240315_M00123_0042_000000000-ABCDE`. This is a simulated **Illumina run folder** — the directory structure written to disk by an Illumina sequencing instrument (such as a MiSeq or NextSeq) when a sequencing run completes.

The name follows a standard Illumina convention:

```
240315_M00123_0042_000000000-ABCDE
│      │       │    └─ Flow cell ID
│      │       └─ Run number
│      └─ Instrument serial number
└─ Date (YYMMDD)
```

### Files in the run folder

| File / Folder | Purpose |
|---|---|
| `RTAComplete.txt` | Written by the instrument's **Real-Time Analysis (RTA)** software when base-calling has finished. Its presence signals to downstream software that the run is ready to process. |
| `RunInfo.xml` | Machine-readable metadata about the run: instrument ID, flow cell ID, number of reads (cycles), and lane/tile layout. |
| `SampleSheet.csv` | Tells demultiplexing software which samples were on the run, which index sequences they used, and how the output files should be named and organised. |
| `InterOp/` | Binary files written by the instrument containing real-time quality metrics (e.g. cluster density, error rate, % bases above Q30). Used by tools like Illumina Sequencing Analysis Viewer (SAV). |
| `Data/Intensities/BaseCalls/` | Where the instrument writes the raw FASTQ files — one pair of files (R1 and R2) per sample per lane. |

### What is demultiplexing?

When multiple samples are sequenced together on a single flow cell (known as **multiplexing**), each sample's DNA fragments are tagged with a short, unique DNA sequence called an **index** (or barcode). After sequencing, the raw reads are sorted back into per-sample files based on these index sequences — this process is called **demultiplexing**.

Illumina's `bcl2fastq` or `BCL Convert` software reads the `SampleSheet.csv` to know which index belongs to which sample, then writes one FASTQ file per sample.

### What is a SampleSheet?

The `SampleSheet.csv` is a plain-text file in CSV format. It has several sections:

- **`[Header]`** — run-level metadata: experiment name, date, instrument type, chemistry.
- **`[Reads]`** — the number of cycles sequenced for each read (e.g. 151 means 151 base pairs per read).
- **`[Settings]`** — software settings such as adapter trimming sequences.
- **`[Data]`** — the sample table. Each row is one sample, with columns for the sample ID, name, index sequences, and project assignment.

SampleSheet errors are a common source of pipeline failures in the lab. A single typo in a sample ID or index sequence can cause an entire run's worth of data to fail demultiplexing.

</details>

<details>
<summary><strong>TASK 1: Fix the SampleSheet error</strong></summary>

### Background

The `SampleSheet.csv` in this run folder contains a deliberate error — the kind of mistake that is easy to make and quick to miss.

### Steps

1. **Run the pipeline script** from the terminal:

   ```bash
   python pipeline.py
   ```

   The script will ask you to confirm you have read the README, then ask for your name. It will then attempt to validate the SampleSheet and **fail with an error message** telling you exactly which line is wrong.

2. **Open the SampleSheet** in the editor:

   ```
   240315_M00123_0042_000000000-ABCDE/SampleSheet.csv
   ```

3. **Find and fix the error.** Navigate to the `[Data]` section at the bottom of the file. Look at the `Sample_ID` column.

   > **Hint:** Illumina sample IDs must not contain spaces. Replace any space with an underscore (`_`).

4. **Save the file** and re-run the script:

   ```bash
   python pipeline.py
   ```

   The validation should now pass and the script will list the samples found in the run.

</details>

---

## Part 2 — Inspect the VCF

The repository contains a pre-computed variant call file at `output/variants.vcf`. This is a [Variant Call Format (VCF)](https://samtools.github.io/hts-specs/VCFv4.2.pdf) file — the standard format for representing genetic variants identified from sequencing data.

Open the file in the editor and answer the following:

> **Which sample carries the BRCA1 variant that passed quality filters?**

**Hints:**
- Lines starting with `##` are metadata headers — skip these.
- The `FILTER` column tells you whether a variant passed quality checks (`PASS` or a reason for failure).
- The `INFO` column contains `GENE=<name>` to identify the gene.
- The final columns are one per sample. Their genotypes use:
  - `0/0` = homozygous reference (no variant)
  - `0/1` = heterozygous (one copy of the variant)
  - `1/1` = homozygous alternate (two copies of the variant)
