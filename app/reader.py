"""
reader.py - Data ingestion module for SheetSync
Handles CSV and JSON files, auto-detects format based on extension.
Returns pandas DataFrames ready for processing.
"""

import os
import json
import pandas as pd


def detect_format(filepath):
    """Figure out if we're dealing with CSV or JSON based on extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        return 'csv'
    elif ext == '.json':
        return 'json'
    else:
        # try to sniff it — read first few bytes
        with open(filepath, 'r') as f:
            first_char = f.read(1).strip()
        if first_char in ('{', '['):
            return 'json'
        return 'csv'  # default fallback


def read_csv_file(filepath):
    """Read a CSV file into a DataFrame. Tries to parse dates automatically."""
    print(f"  Reading CSV: {filepath}")
    df = pd.read_csv(filepath)

    # try to parse any column that looks like a date
    for col in df.columns:
        if any(hint in col.lower() for hint in ['date', 'time', 'created', 'updated']):
            try:
                df[col] = pd.to_datetime(df[col])
                print(f"    Parsed '{col}' as datetime")
            except (ValueError, TypeError):
                pass  # not a date, whatever

    print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def read_json_file(filepath):
    """Read a JSON file into a DataFrame. Handles both array and object formats."""
    print(f"  Reading JSON: {filepath}")

    with open(filepath, 'r') as f:
        raw = json.load(f)

    # if it's a dict with a single key containing a list, unwrap it
    if isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(val, list):
                print(f"    Found nested array under key '{key}'")
                raw = val
                break

    df = pd.DataFrame(raw)
    print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def load_data(filepath):
    """
    Main entry point — give it a file path, get back a DataFrame.
    Auto-detects CSV vs JSON.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    fmt = detect_format(filepath)
    print(f"[Reader] Detected format: {fmt}")

    if fmt == 'csv':
        return read_csv_file(filepath)
    elif fmt == 'json':
        return read_json_file(filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def load_multiple(filepaths):
    """Load multiple files and return a dict of DataFrames keyed by filename."""
    results = {}
    for fp in filepaths:
        name = os.path.basename(fp)
        results[name] = load_data(fp)
    return results
