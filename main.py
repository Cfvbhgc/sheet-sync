#!/usr/bin/env python3
"""
main.py - SheetSync CLI entry point
Reporting automation tool: reads data, processes it, generates reports, sends emails.

Usage:
    python main.py --source data/sales_2024.csv --report monthly --format pdf
    python main.py --source data/sales_2024.csv --report weekly --email test@example.com
    python main.py --source data/sales_2024.csv --report monthly --format both --output output/
"""

import argparse
import os
import sys
from datetime import datetime

# our modules
from app.reader import load_data
from app.processor import process_monthly, process_weekly
from app.report_generator import generate_report
from app.email_sender import send_report


def parse_args():
    """Set up CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='sheetsync',
        description='SheetSync - Automated reporting from CSV/JSON data',
        epilog='Example: python main.py --source data/sales_2024.csv --report monthly --format pdf',
    )

    parser.add_argument(
        '--source', '-s',
        required=True,
        help='Path to data source file (CSV or JSON)',
    )
    parser.add_argument(
        '--report', '-r',
        choices=['monthly', 'weekly'],
        default='monthly',
        help='Report type: monthly or weekly (default: monthly)',
    )
    parser.add_argument(
        '--format', '-f',
        choices=['pdf', 'html', 'both'],
        default='pdf',
        help='Output format: pdf, html, or both (default: pdf)',
    )
    parser.add_argument(
        '--output', '-o',
        default='./output',
        help='Output directory (default: ./output)',
    )
    parser.add_argument(
        '--email', '-e',
        default=None,
        help='Email address to send the report to (mock mode)',
    )
    parser.add_argument(
        '--no-email',
        action='store_true',
        help='Skip sending email even if --email is set',
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("  SheetSync - Reporting Automation Tool")
    print("=" * 60)
    print(f"  Source:  {args.source}")
    print(f"  Report:  {args.report}")
    print(f"  Format:  {args.format}")
    print(f"  Output:  {args.output}")
    if args.email:
        print(f"  Email:   {args.email}")
    print("=" * 60)
    print()

    # Step 1: Load data
    print("[1/4] Loading data...")
    try:
        df = load_data(args.source)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading data: {e}")
        sys.exit(1)

    print(f"  Data shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"  Columns: {', '.join(df.columns)}")
    print()

    # Step 2: Process data
    print("[2/4] Processing data...")
    if args.report == 'monthly':
        report_data = process_monthly(df)
    elif args.report == 'weekly':
        report_data = process_weekly(df)
    else:
        print(f"ERROR: Unknown report type '{args.report}'")
        sys.exit(1)
    print()

    # Step 3: Generate report
    print("[3/4] Generating report...")
    output_dir = os.environ.get('OUTPUT_DIR', args.output)
    report_path = generate_report(
        report_data,
        output_dir=output_dir,
        report_type=args.report,
        fmt=args.format,
    )
    print()

    # Step 4: Send email (if requested)
    print("[4/4] Email delivery...")
    if args.email and not args.no_email:
        send_report(report_path, recipient=args.email, report_type=args.report)
    else:
        print("  Skipped (no --email flag or --no-email set)")
    print()

    # Done!
    print("=" * 60)
    print(f"  Done! Report saved to: {report_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
