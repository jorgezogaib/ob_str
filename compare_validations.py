"""
Compare validation results from multiple exported JSON files

Usage:
    python compare_validations.py file1.json file2.json [file3.json ...]
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def load_validation_file(filepath: str) -> Dict[str, Any]:
    """Load validation export JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_validations(files: List[str]):
    """Compare validation results across multiple runs"""

    if len(files) < 2:
        print("Error: Need at least 2 validation files to compare")
        sys.exit(1)

    # Load all validation files
    validations = []
    for filepath in files:
        try:
            data = load_validation_file(filepath)
            validations.append({
                'file': Path(filepath).name,
                'data': data
            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            sys.exit(1)

    print("="*80)
    print("VALIDATION COMPARISON")
    print("="*80)

    # Summary comparison
    print("\n### SUMMARY COMPARISON ###\n")
    print(f"{'File':<40} {'Checks':<10} {'Warnings':<10} {'Passed':<10}")
    print("-" * 80)

    for val in validations:
        summary = val['data']['summary']
        print(f"{val['file']:<40} {summary['total_checks']:<10} "
              f"{summary['total_warnings']:<10} {summary['total_passed']:<10}")

    # Portfolio stats comparison
    print("\n### PORTFOLIO STATS COMPARISON ###\n")
    print(f"{'File':<40} {'Properties':<12} {'Total Value':<15} {'Equity':<15} {'LTV %':<10}")
    print("-" * 80)

    for val in validations:
        stats = val['data']['portfolio_stats']
        print(f"{val['file']:<40} {stats['properties_owned']:<12} "
              f"${stats['total_portfolio_value']/1e6:>6.2f}M{' '*6} "
              f"${stats['total_equity']/1e6:>6.2f}M{' '*6} "
              f"{stats['ltv_percent']:>6.1f}%")

    # Warning differences
    print("\n### WARNING CHANGES ###\n")

    base = validations[0]
    base_warnings = set()
    for category, checks in base['data']['results_by_category'].items():
        for check in checks:
            if check['status'] == 'warn':
                base_warnings.add(f"{category}: {check['message']}")

    for i, val in enumerate(validations[1:], 1):
        current_warnings = set()
        for category, checks in val['data']['results_by_category'].items():
            for check in checks:
                if check['status'] == 'warn':
                    current_warnings.add(f"{category}: {check['message']}")

        new_warnings = current_warnings - base_warnings
        resolved_warnings = base_warnings - current_warnings

        print(f"Comparing {base['file']} → {val['file']}:")

        if new_warnings:
            print(f"  ⚠ New Warnings ({len(new_warnings)}):")
            for warning in sorted(new_warnings):
                print(f"    + {warning}")

        if resolved_warnings:
            print(f"  ✓ Resolved Warnings ({len(resolved_warnings)}):")
            for warning in sorted(resolved_warnings):
                print(f"    - {warning}")

        if not new_warnings and not resolved_warnings:
            print("  → No warning changes")

        print()

    # Threshold comparison (if different)
    print("\n### THRESHOLD DIFFERENCES ###\n")

    base_thresholds = base['data']['validation_thresholds']
    threshold_changes = False

    for i, val in enumerate(validations[1:], 1):
        current_thresholds = val['data']['validation_thresholds']

        for category in base_thresholds:
            if category not in current_thresholds:
                continue

            for param, base_value in base_thresholds[category].items():
                current_value = current_thresholds[category].get(param)

                if current_value != base_value:
                    if not threshold_changes:
                        print(f"Comparing {base['file']} → {val['file']}:")
                        threshold_changes = True

                    print(f"  {category}.{param}: {base_value} → {current_value}")

        if threshold_changes:
            print()
            threshold_changes = False
        else:
            print(f"Comparing {base['file']} → {val['file']}: No threshold changes\n")

    print("="*80)
    print("COMPARISON COMPLETE")
    print("="*80)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nExample:")
        print("  python compare_validations.py validation_results_20251227_143045.json validation_results_20251227_150230.json")
        sys.exit(1)

    compare_validations(sys.argv[1:])
