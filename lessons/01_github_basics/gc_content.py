#!/usr/bin/env python3
"""
GC Content Calculator
=====================
This script calculates the GC content of DNA sequences.

GC content is the percentage of nucleotide bases in a DNA sequence that are
either Guanine (G) or Cytosine (C). It is widely used in bioinformatics because:

  - It affects the melting temperature of DNA (higher GC = higher Tm)
  - It varies across genomic regions and between species
  - Some sequencing technologies are sensitive to GC bias

Formula:
    GC content (%) = (G + C) / total bases × 100
"""


def calculate_gc_content(sequence):
    """
    Calculate the GC content of a DNA sequence.

    Args:
        sequence: A string of DNA bases (A, T, G, C)

    Returns:
        GC content as a percentage (0–100), rounded to 2 decimal places
    """
    sequence = sequence.upper()

    g_count = sequence.count("G")
    c_count = sequence.count("C")
    a_count = sequence.count("A")
    t_count = sequence.count("T")

    # Calculate GC content as a percentage of total bases
    gc_content = (g_count + c_count) / (a_count + t_count) * 100

    return round(gc_content, 2)


def main():
    print("GC Content Calculator")
    print("=" * 60)
    print()

    # Test sequences with known expected GC content
    test_cases = [
        ("ATGCATGC",   50.0,  "Alternating AT and GC"),
        ("GGGGAAAA",   50.0,  "4× G + 4× A"),
        ("ATCGATCG",   50.0,  "Typical coding sequence"),
        ("GCGCGCGC",  100.0,  "All GC"),
        ("ATATATATAT",  0.0,  "All AT"),
    ]

    print(f"{'Sequence':<16} {'Expected':>10} {'Got':>10}  {'Result':<20}  Notes")
    print("-" * 75)

    all_passed = True
    for sequence, expected, notes in test_cases:
        try:
            result = calculate_gc_content(sequence)
            passed = abs(result - expected) < 0.01
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            print(f"{sequence:<16} {expected:>9.1f}% {result:>9.1f}%  {status:<20}  {notes}")
        except Exception as e:
            all_passed = False
            print(f"{sequence:<16} {expected:>9.1f}%      ERROR  {type(e).__name__:<18}  {notes}")

    print()
    if all_passed:
        print("All tests passed! The GC content calculator is working correctly.")
    else:
        print("Some tests failed. There is a bug in calculate_gc_content().")
        print("Can you find and fix it?")


if __name__ == "__main__":
    main()
