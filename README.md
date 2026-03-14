# SheetSync

Reporting automation tool that reads CSV/JSON data, processes it with pandas, generates PDF/HTML reports, and sends them via email.

Built with Python, pandas, Jinja2, and ReportLab.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a monthly PDF report
python main.py --source data/sales_2024.csv --report monthly

# Generate a weekly HTML report
python main.py --source data/sales_2024.csv --report weekly --format html

# Generate both PDF and HTML, then email it
python main.py --source data/sales_2024.csv --report monthly --format both --email manager@example.com
```

## CLI Reference

```
usage: sheetsync [-h] --source SOURCE [--report {monthly,weekly}]
                 [--format {pdf,html,both}] [--output OUTPUT]
                 [--email EMAIL] [--no-email]

Options:
  --source, -s    Path to data source file (CSV or JSON)
  --report, -r    Report type: monthly or weekly (default: monthly)
  --format, -f    Output format: pdf, html, or both (default: pdf)
  --output, -o    Output directory (default: ./output)
  --email, -e     Email address to send the report to (mock mode)
  --no-email      Skip sending email
```

## Usage Examples

### Monthly report from sales data

```bash
python main.py --source data/sales_2024.csv --report monthly --format pdf
```

Output:
```
============================================================
  SheetSync - Reporting Automation Tool
============================================================
  Source:  data/sales_2024.csv
  Report:  monthly
  Format:  pdf
  Output:  ./output
============================================================

[1/4] Loading data...
[Reader] Detected format: csv
  Reading CSV: data/sales_2024.csv
    Parsed 'order_date' as datetime
    Loaded 200 rows, 9 columns

[2/4] Processing data...
[Processor] Running monthly aggregation...
  Monthly summary: 12 months, 10 top products

[3/4] Generating report...
[Report] Generating PDF (monthly)...
  PDF saved: ./output/monthly_report_20240101_120000.pdf

[4/4] Email delivery...
  Skipped (no --email flag or --no-email set)

============================================================
  Done! Report saved to: ./output/monthly_report_20240101_120000.pdf
============================================================
```

### Weekly report with email

```bash
python main.py -s data/sales_2024.csv -r weekly -f pdf -e team@example.com
```

The email sender runs in mock mode by default -- it saves a `.eml` file to the output directory instead of actually sending. Configure real SMTP credentials in `.env` for production use.

### Using JSON data

```bash
python main.py --source data/customers.json --report monthly
```

The reader auto-detects CSV vs JSON based on file extension.

## Project Structure

```
sheet-sync/
├── app/
│   ├── reader.py             # CSV/JSON ingestion, auto-detection
│   ├── processor.py          # pandas aggregation (monthly/weekly)
│   ├── report_generator.py   # PDF (reportlab) and HTML (jinja2) output
│   ├── email_sender.py       # SMTP email with mock mode
│   └── templates/            # Jinja2 HTML templates
│       ├── base.html
│       ├── monthly_report.html
│       └── weekly_report.html
├── data/                     # Sample datasets
│   ├── sales_2024.csv        # 200 rows of sales data
│   ├── customers.json        # 50 customer records
│   └── inventory.csv         # 15 product inventory records
├── output/                   # Generated reports land here
├── main.py                   # CLI entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Docker

```bash
# Build and run
docker compose up --build

# Reports are saved to ./output/ on the host (volume mount)
```

## Configuration

Copy `.env.example` to `.env` and fill in SMTP credentials for live email sending:

```bash
cp .env.example .env
```

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DEFAULT_RECIPIENT=manager@example.com
OUTPUT_DIR=./output
```

## How It Works

1. **Reader** (`app/reader.py`) -- Loads CSV or JSON files into pandas DataFrames. Auto-detects format, parses date columns.

2. **Processor** (`app/processor.py`) -- Groups data by month or week. Calculates totals, averages, top products, and month-over-month growth. Auto-discovers revenue, quantity, and product columns by name.

3. **Report Generator** (`app/report_generator.py`) -- Renders Jinja2 HTML templates or builds PDFs with ReportLab. PDF reports include styled tables, summary stat cards, and a top products section.

4. **Email Sender** (`app/email_sender.py`) -- Builds MIME emails with report attachments. Mock mode saves `.eml` files locally; configure SMTP for real delivery.
