import argparse
import os
import sys
from typing import List, Tuple


def list_files(dir_path: str) -> List[str]:
    if not os.path.isdir(dir_path):
        return []
    # Only list regular files (no subdirs), sorted for stable output
    return sorted([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])


def read_lines(path: str) -> List[str]:
    with open(path, "r") as f:
        return [line.rstrip("\n") for line in f.readlines()]


def diff_lines(a_lines: List[str], b_lines: List[str]) -> List[Tuple[int, str, str]]:
    """Return a compact list of (line_no, left, right) for differing lines.

    Line numbers are 1-based. Length differences are reported as additional
    lines with empty string on the missing side.
    """
    diffs: List[Tuple[int, str, str]] = []
    max_len = max(len(a_lines), len(b_lines))
    for i in range(max_len):
        left = a_lines[i] if i < len(a_lines) else ""
        right = b_lines[i] if i < len(b_lines) else ""
        if left != right:
            diffs.append((i + 1, left, right))
    return diffs


def compare_dirs(results_dir: str, sample_dir: str, max_diffs_per_file: int) -> int:
    exit_code = 0
    print(f"Comparing\n  results: {results_dir}\n  sample : {sample_dir}\n")

    res_files = set(list_files(results_dir))
    samp_files = set(list_files(sample_dir))

    only_in_results = sorted(res_files - samp_files)
    only_in_sample = sorted(samp_files - res_files)
    common = sorted(res_files & samp_files)

    if only_in_results:
        exit_code = 1
        print("Files only in results:")
        for f in only_in_results:
            print(f"  {f}")
        print()

    if only_in_sample:
        exit_code = 1
        print("Files only in sample_output:")
        for f in only_in_sample:
            print(f"  {f}")
        print()

    for fname in common:
        res_path = os.path.join(results_dir, fname)
        samp_path = os.path.join(sample_dir, fname)
        try:
            res_lines = read_lines(res_path)
            samp_lines = read_lines(samp_path)
        except Exception as e:
            exit_code = 1
            print(f"[ERROR] Failed reading {fname}: {e}")
            continue

        diffs = diff_lines(res_lines, samp_lines)
        if not diffs:
            print(f"[OK] {fname}")
            continue

        exit_code = 1
        print(f"[DIFF] {fname} — {len(diffs)} differing line(s)")
        for i, (ln, left, right) in enumerate(diffs[:max_diffs_per_file]):
            print(f"  L{ln}:")
            print(f"    results: {left}")
            print(f"    sample : {right}")
        if len(diffs) > max_diffs_per_file:
            print(f"  ... and {len(diffs) - max_diffs_per_file} more differing line(s)")
        print()

    if exit_code == 0:
        print("All files match.")
    return exit_code


def main():
    parser = argparse.ArgumentParser(description="Compare results against sample outputs.")
    parser.add_argument(
        "--results-dir",
        type=str,
        help="Path to results testcase directory (e.g., code/results/testcase0).",
    )
    parser.add_argument(
        "--sample-dir",
        type=str,
        help="Path to sample_output testcase directory (e.g., code/sample_output/testcase0).",
    )
    parser.add_argument(
        "--results-root",
        type=str,
        default=os.path.join("code", "results"),
        help="Root folder containing results per testcase (default: code/results)",
    )
    parser.add_argument(
        "--sample-root",
        type=str,
        default=os.path.join("code", "sample_output"),
        help="Root folder containing sample outputs per testcase (default: code/sample_output)",
    )
    parser.add_argument(
        "--testcase",
        type=str,
        default="testcase0",
        help="Testcase folder name under the roots (default: testcase0)",
    )
    parser.add_argument(
        "--max-diffs-per-file",
        type=int,
        default=10,
        help="Limit of differing lines to display per file",
    )

    args = parser.parse_args()

    # Resolve directories
    results_dir = args.results_dir or os.path.join(args.results_root, args.testcase)
    sample_dir = args.sample_dir or os.path.join(args.sample_root, args.testcase)

    results_dir = os.path.abspath(results_dir)
    sample_dir = os.path.abspath(sample_dir)

    if not os.path.isdir(results_dir):
        print(f"Results directory not found: {results_dir}")
        sys.exit(2)
    if not os.path.isdir(sample_dir):
        print(f"Sample directory not found: {sample_dir}")
        sys.exit(2)

    code = compare_dirs(results_dir, sample_dir, args.max_diffs_per_file)
    sys.exit(code)


if __name__ == "__main__":
    main()


