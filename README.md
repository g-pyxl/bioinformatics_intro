<p align="center">
  <img src="assets/header.svg" alt="Bioinformatics Intro Exercise — Clinical Bioinformatics Training"/>
</p>

<p align="center">
  A hands-on introduction to clinical bioinformatics concepts for prospective applicants.<br/>
  No prior bioinformatics knowledge required.
</p>

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [📚 Background Reading](#background-reading)
- [🟩 Task 1 — Fix the SampleSheet](#task-1--fix-the-samplesheet)
- [🟩 Task 2 — Run Demultiplexing](#task-2--run-demultiplexing)
- [🟩 Task 3 — Inspect the VCF](#task-3--inspect-the-vcf)

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## Prerequisites

This exercise is hosted on **GitHub** and runs entirely in the browser — no local software installation required. You will need:

- A free **GitHub account** — [create one here](https://github.com/signup) if you don't already have one.

[↑ Back to top](#contents)

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## Setup

1. **Fork this repository** — click the **Fork** button in the top-right corner of this page, then click **Create Fork** on the following page. This creates your own copy of this repository under your GitHub account.

| Fork Screenshot |
|---|
| ![GitHub fork button screenshot](assets/fork.png) |

2. **Open a Codespace** — on your forked repo, click the green **Code** button, select the **Codespaces** tab, and click **Create codespace on main**.
   Alternatively, navigate directly to: `https://codespaces.new/<your-username>/bioinformatics_intro`

3. **Start the exercise** — Once your Codespace loads, in the terminal, run [`pipeline.py`](pipeline.py):

| Codespace Screenshot |
|---|
| ![GitHub Codespace terminal screenshot](assets/codespace.png) |

```bash
python pipeline.py
```

Then follow the on-screen prompts and complete each exercise in this README.

Optional (assessment admins): send checkpoint events to an external webhook.

```bash
export PIPELINE_CHECKPOINT_WEBHOOK="https://your-service.example/webhook"
export PIPELINE_CHECKPOINT_TOKEN="your-shared-token"
python pipeline.py
```

If `PIPELINE_CHECKPOINT_WEBHOOK` is not set, no external notifications are sent.  
Events include milestones such as pipeline start, quiz completion, SampleSheet validation pass/fail, demultiplex completion, and challenge display.

If you want to restart from scratch at any point, run:

```bash
python reset.py
```

This clears progress/output files and restores `SampleSheet.csv` to the original training state (including the intentional Task 1 error).

[↑ Back to top](#contents)

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## 📚 BACKGROUND READING

<details>
<summary><strong>What is GitHub?</strong></summary>

<br>

GitHub is a web-based platform for hosting, sharing, and collaborating on code. It is built on top of **Git**, a version control system that tracks changes to files over time — letting you see who changed what, when, and why, and roll back to earlier versions if something goes wrong.

At its core, GitHub stores code in **repositories** (repos): collections of files, their full history, and any associated discussion or documentation.

#### Why does GitHub matter in clinical bioinformatics?

In a clinical setting, the software used to analyse patient samples must be:

| Requirement | Why it matters |
|---|---|
| **Auditable** | Every change to the analysis pipeline must be traceable. Git commit history provides a complete record of what code was running at any given time. |
| **Version-controlled** | If a pipeline is updated, older results can be reproduced exactly by checking out the previous version of the code. |
| **Validated before deployment** | GitHub's pull request and code review workflow ensures changes are reviewed and approved before they affect patient results. |
| **Reproducible** | By pinning software versions and storing pipeline code in a repo, analyses can be rerun identically weeks or months later. |

Most clinical bioinformatics teams use GitHub (or a similar platform such as GitLab) as the central system of record for their pipelines, reference files, and validation evidence.

</details>

<details>
<summary><strong>Next Generation Sequencing (NGS)</strong></summary>

<br>

**Next Generation Sequencing (NGS)** is a group of high-throughput methods that can sequence millions of DNA fragments in parallel. Compared with older single-fragment methods (such as Sanger sequencing), NGS produces much more data per run and enables broad tests such as gene panels, exomes, genomes, and targeted amplicon assays.

#### Typical NGS workflow

| Stage | What happens |
|---|---|
| Sample preparation | DNA (or RNA converted to cDNA) is extracted from the specimen and converted into a sequencing library by adding adapters and, where needed, sample indexes (barcodes). |
| Sequencing run | Library fragments bind to a flow cell and are sequenced cycle-by-cycle. The instrument captures signals and converts them into base calls with quality scores. |
| Primary analysis | Raw instrument output is converted into FASTQ files, then demultiplexed into one file pair per sample if multiple samples were pooled. |
| Secondary analysis | Reads are aligned to a reference genome and analysed for variants (SNVs, indels, CNVs, etc.), depending on the test design. |
| Interpretation & reporting | Detected variants are filtered, annotated, and interpreted in a clinical context before a report is issued. |

#### Core terms

| Term | Meaning |
|---|---|
| Read | One sequenced DNA fragment (or one end of a fragment in paired-end sequencing). |
| Paired-end sequencing | Sequencing both ends of the same DNA fragment, improving alignment and structural resolution. |
| Coverage (depth) | How many times a base is sequenced; higher coverage usually increases confidence in variant calls. |
| Q score | A Phred quality score representing confidence in each base call (e.g. Q30 means 1 in 1000 error probability). |

NGS underpins modern clinical genomics because it can process many samples and many genomic targets efficiently, while still supporting traceability and quality control throughout the pipeline.

</details>

<details>
<summary><strong>FASTQ Files</strong></summary>

<br>

A **FASTQ** file stores sequencing reads along with per-base quality scores. It is the standard output format after demultiplexing.

Each read is represented by **4 lines**:

| Line | Contents |
|---|---|
| 1 | Read header (starts with `@`) |
| 2 | Nucleotide sequence (`A/C/G/T/N`) |
| 3 | Separator line (starts with `+`) |
| 4 | Quality string (ASCII-encoded Phred quality scores) |

In **paired-end** sequencing, each sample usually has two FASTQ files:

| File | Meaning |
|---|---|
| `R1` | Forward read (read 1) |
| `R2` | Reverse read (read 2) |

FASTQ files are often compressed as `.fastq.gz` because they are large.

Common naming components include:

- sample identifier
- lane identifier (for example `L001`)
- read identifier (`R1` or `R2`)

</details>

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

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## 🟩 Task 1 — Fix the SampleSheet

The `SampleSheet.csv` in the run folder contains a deliberate error — the kind of mistake that is easy to make and quick to miss.

<details>
<summary><strong>Show instructions</strong></summary>

<br>

**Step 1** — Open the SampleSheet in the editor:

```
240315_M00123_0042_000000000-ABCDE/SampleSheet.csv
```

Navigate to the `[Data]` section at the bottom. Look carefully at the `Sample_ID` column.

---

**Step 2** — Fix the invalid sample ID:

> **Hint:** Illumina sample IDs must not contain spaces. Replace any space with an underscore (`_`).

---

**Step 3** — Save the file.

The next run will validate the SampleSheet, list the samples found in the run, and continue to demultiplexing.

</details>

[↑ Back to top](#contents)

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## 🟩 Task 2 — Run Demultiplexing

Once Task 1 passes, the next stage is demultiplexing the run folder with **bcl2fastq2**.

<details>
<summary><strong>Show instructions</strong></summary>

<br>

Construct the full command from this template:

```bash
bcl2fastq --runfolder-dir {run_folder} --sample-sheet {sample_sheet} --output-dir {output_dir} --no-lane-splitting
```

Replace placeholders with the correct values for this exercise:

- `{run_folder}` = `240315_M00123_0042_000000000-ABCDE`
- `{sample_sheet}` = `240315_M00123_0042_000000000-ABCDE/SampleSheet.csv`
- `{output_dir}` = `output/fastq`

Because this repository uses a simulated run folder, the script will create **simulated FASTQ files** in `output/fastq/` if `bcl2fastq2` is unavailable or cannot process the run folder directly.

The script will prompt you to paste your completed command before Task 2 runs.

After demultiplexing, the script will ask a short MCQ about FASTQ files before continuing to Task 3.

</details>

[↑ Back to top](#contents)

<p align="center">
  <img src="assets/divider.svg" width="100%" alt=""/>
</p>

## 🟩 Task 3 — Inspect the VCF

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
