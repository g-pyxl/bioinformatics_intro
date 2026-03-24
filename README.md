# Bioinformatics Intro Exercise - Find the variant

> A hands-on introduction to clinical bioinformatics concepts for prospective applicants. No prior bioinformatics knowledge required.

---

## Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Background](#background)
- [Task 1 — Fix the SampleSheet](#task-1--fix-the-samplesheet)
- [Task 2 — Inspect the VCF](#task-2--inspect-the-vcf)

---

## Prerequisites

This exercise is hosted on **GitHub** and runs entirely in the browser — no local software installation required. You will need:

- A free **GitHub account** — [create one here](https://github.com/signup) if you don't already have one.

### What is GitHub?

GitHub is a web-based platform for hosting, sharing, and collaborating on code. It is built on top of **Git**, a version control system that tracks changes to files over time — letting you see who changed what, when, and why, and roll back to earlier versions if something goes wrong.

At its core, GitHub stores code in **repositories** (repos): collections of files, their full history, and any associated discussion or documentation.

### Why does GitHub matter in clinical bioinformatics?

In a clinical setting, the software used to analyse patient samples must be:

| Requirement | Why it matters |
|---|---|
| **Auditable** | Every change to the analysis pipeline must be traceable. Git commit history provides a complete record of what code was running at any given time. |
| **Version-controlled** | If a pipeline is updated, older results can be reproduced exactly by checking out the previous version of the code. |
| **Validated before deployment** | GitHub's pull request and code review workflow ensures changes are reviewed and approved before they affect patient results. |
| **Reproducible** | By pinning software versions and storing pipeline code in a repo, analyses can be rerun identically weeks or months later. |

Most clinical bioinformatics teams use GitHub (or a similar platform such as GitLab) as the central system of record for their pipelines, reference files, and validation evidence.

[↑ Back to top](#contents)

---

## Setup

1. **Fork this repository** — click the **Fork** button in the top-right corner of this page. This creates your own copy of the repo under your GitHub account.

2. **Open a Codespace** — on your forked repo, click the green **Code** button, select the **Codespaces** tab, and click **Create codespace on main**.
   Alternatively, navigate directly to: `https://codespaces.new/<your-username>/bioinformatics_intro`

3. **Open a terminal** — once the Codespace has loaded, open a terminal via `Terminal > New Terminal`.

[↑ Back to top](#contents)

---

## BACKGROUND 📖

<details>
<summary><strong>The Illumina Run Folder</strong></summary>

<br>

This repository contains a folder called `240315_M00123_0042_000000000-ABCDE`. This is a simulated **Illumina run folder** — the directory structure written to disk by an Illumina sequencing instrument (such as a MiSeq or NextSeq) when a sequencing run completes.

The folder name follows a standard Illumina convention:

```
240315_M00123_0042_000000000-ABCDE
│      │       │    └─ Flow cell ID
│      │       └─ Run number
│      └─ Instrument serial number
└─ Date (YYMMDD)
```

#### Files in the run folder

| File / Folder | Purpose |
|---|---|
| `RTAComplete.txt` | Written by the instrument's **Real-Time Analysis (RTA)** software when base-calling has finished. Its presence signals to downstream software that the run is ready to process. |
| `RunInfo.xml` | Machine-readable metadata about the run: instrument ID, flow cell ID, number of reads (cycles), and lane/tile layout. |
| `SampleSheet.csv` | Tells demultiplexing software which samples were on the run, which index sequences they used, and how output files should be named and organised. |
| `InterOp/` | Binary files written by the instrument containing real-time quality metrics (e.g. cluster density, error rate, % bases above Q30). Used by tools like Illumina Sequencing Analysis Viewer (SAV). |
| `Data/Intensities/BaseCalls/` | Where the instrument writes the raw FASTQ files — one pair of files (R1 and R2) per sample per lane. |

#### What is demultiplexing?

When multiple samples are sequenced together on a single flow cell (known as **multiplexing**), each sample's DNA fragments are tagged with a short, unique DNA sequence called an **index** (or barcode). After sequencing, the raw reads are sorted back into per-sample files based on these index sequences — this process is called **demultiplexing**.

Illumina's `bcl2fastq` or `BCL Convert` software reads the `SampleSheet.csv` to know which index belongs to which sample, then writes one FASTQ file per sample.

#### What is a SampleSheet?

The `SampleSheet.csv` is a plain-text file in CSV format with several sections:

| Section | Contents |
|---|---|
| `[Header]` | Run-level metadata: experiment name, date, instrument type, chemistry. |
| `[Reads]` | The number of cycles sequenced per read (e.g. `151` means 151 base pairs). |
| `[Settings]` | Software settings such as adapter trimming sequences. |
| `[Data]` | The sample table — one row per sample, with columns for ID, name, index sequences, and project. |

SampleSheet errors are a common cause of pipeline failures. A single typo in a sample ID or index sequence can cause an entire run's worth of data to fail demultiplexing.

</details>

[↑ Back to top](#contents)

---

## Task 1 — Fix the SampleSheet

The `SampleSheet.csv` in the run folder contains a deliberate error — the kind of mistake that is easy to make and quick to miss.

<details>
<summary><strong>Show instructions</strong></summary>

<br>

**Step 1** — Run the pipeline script from the terminal:

```bash
python pipeline.py
```

The script will ask you to confirm you have read the README, then ask for your name. It will then validate the SampleSheet and **fail with an error message** telling you exactly which line is wrong.

---

**Step 2** — Open the SampleSheet in the editor:

```
240315_M00123_0042_000000000-ABCDE/SampleSheet.csv
```

Navigate to the `[Data]` section at the bottom. Look carefully at the `Sample_ID` column.

> **Hint:** Illumina sample IDs must not contain spaces. Replace any space with an underscore (`_`).

---

**Step 3** — Save the file and re-run the script:

```bash
python pipeline.py
```

The validation should now pass and the script will list the samples found in the run.

</details>

[↑ Back to top](#contents)

---

## Task 2 — Inspect the VCF

The file `output/variants.vcf` contains pre-computed variant calls for the samples in this run. This is a [Variant Call Format (VCF)](https://samtools.github.io/hts-specs/VCFv4.2.pdf) file — the standard format for representing genetic variants identified from sequencing data.

**Open the file in the editor and answer the following:**

> Which sample carries the **BRCA1** variant that passed quality filters?

<details>
<summary><strong>Show hints</strong></summary>

<br>

Lines starting with `##` are metadata headers — skip these. The column structure of each data row is:

| Column | Description |
|---|---|
| `CHROM` | Chromosome |
| `POS` | Position on the chromosome |
| `ID` | Variant identifier (e.g. dbSNP rsID) |
| `REF` | Reference allele |
| `ALT` | Alternate allele |
| `QUAL` | Quality score |
| `FILTER` | `PASS` if the variant passed all filters, otherwise the reason it failed |
| `INFO` | Semicolon-separated annotations — look for `GENE=<name>` |
| `FORMAT` | Describes the format of the sample columns that follow |
| `Sample_1`, `Sample_2`, `Sample_3` | One column per sample, formatted as `GT:DP` (genotype : read depth) |

**Genotype key:**

| Genotype | Meaning |
|---|---|
| `0/0` | Homozygous reference — no variant |
| `0/1` | Heterozygous — one copy of the variant |
| `1/1` | Homozygous alternate — two copies of the variant |

</details>

[↑ Back to top](#contents)
