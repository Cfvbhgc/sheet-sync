"""
report_generator.py - Generates HTML and PDF reports using Jinja2 and reportlab.
Loads templates from app/templates/, renders with data, optionally converts to PDF.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# reportlab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# where our jinja2 templates live
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')


def _get_jinja_env():
    """Set up Jinja2 environment with our template directory."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=True,
    )
    # custom filter for formatting numbers with commas
    env.filters['currency'] = lambda x: f"${x:,.2f}"
    env.filters['number'] = lambda x: f"{x:,}"
    return env


def render_html(report_data, report_type='monthly'):
    """
    Render an HTML report from template + data.
    Returns the HTML string.
    """
    print(f"[Report] Rendering HTML ({report_type})...")

    env = _get_jinja_env()

    if report_type == 'monthly':
        template = env.get_template('monthly_report.html')
    elif report_type == 'weekly':
        template = env.get_template('weekly_report.html')
    else:
        raise ValueError(f"Unknown report type: {report_type}")

    # inject some extra context
    ctx = {
        **report_data,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'generator': 'SheetSync v1.0',
    }

    html = template.render(**ctx)
    print(f"  HTML rendered, {len(html)} chars")
    return html


def save_html(html, output_path):
    """Save rendered HTML to a file."""
    with open(output_path, 'w') as f:
        f.write(html)
    print(f"  Saved HTML: {output_path}")
    return output_path


def generate_pdf(report_data, output_path, report_type='monthly'):
    """
    Generate a PDF report using reportlab.
    This builds the PDF programmatically — tables, headers, stats, etc.
    """
    print(f"[Report] Generating PDF ({report_type})...")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor('#1a1a2e'),
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#16213e'),
        spaceBefore=16,
        spaceAfter=8,
    )
    normal = styles['Normal']

    summary = report_data.get('summary', {})

    # --- Title ---
    elements.append(Paragraph(f"SheetSync {report_data.get('report_type', 'Report')}", title_style))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} | "
        f"Period: {summary.get('date_range', 'N/A')}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    elements.append(Spacer(1, 12))

    # --- Summary Stats ---
    elements.append(Paragraph("Summary", heading_style))

    stats_data = [
        ['Total Revenue', 'Total Orders', 'Avg Order Value', 'Growth'],
        [
            f"${summary.get('total_revenue', 0):,.2f}",
            f"{summary.get('total_orders', 0):,}",
            f"${summary.get('avg_order_value', 0):,.2f}",
            f"{summary.get('growth_pct', 0):+.1f}%",
        ],
    ]
    stats_table = Table(stats_data, colWidths=[130, 100, 120, 80])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f4ff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 16))

    # --- Time-based data table (monthly or weekly) ---
    if report_type == 'monthly':
        time_data = report_data.get('monthly_data', [])
        time_label = 'Month'
    else:
        time_data = report_data.get('weekly_data', [])
        time_label = 'Week'

    if time_data:
        elements.append(Paragraph(f"{time_label}ly Breakdown", heading_style))

        # build the table
        has_units = 'total_units' in time_data[0] if time_data else False
        header = [time_label, 'Revenue', 'Orders', 'Avg Value']
        if has_units:
            header.append('Units Sold')

        tbl_data = [header]
        for row in time_data:
            r = [
                row.get(time_label.lower(), row.get('month', row.get('week', ''))),
                f"${row.get('total_revenue', 0):,.2f}",
                str(row.get('total_orders', 0)),
                f"${row.get('avg_order_value', 0):,.2f}",
            ]
            if has_units:
                r.append(str(row.get('total_units', 0)))
            tbl_data.append(r)

        col_widths = [120, 100, 60, 90]
        if has_units:
            col_widths.append(70)

        tbl = Table(tbl_data, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 16))

    # --- Top Products ---
    top_products = report_data.get('top_products', [])
    if top_products:
        elements.append(Paragraph("Top Products", heading_style))

        prod_header = ['#', 'Product', 'Revenue', 'Orders']
        prod_data = [prod_header]
        for i, p in enumerate(top_products[:10], 1):
            prod_data.append([
                str(i),
                p['product'],
                f"${p['total_revenue']:,.2f}",
                str(p['num_orders']),
            ])

        prod_tbl = Table(prod_data, colWidths=[30, 200, 100, 60])
        prod_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(prod_tbl)

    # --- Footer ---
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    footer_style = ParagraphStyle('Footer', parent=normal, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph(
        f"Generated by SheetSync v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        footer_style
    ))

    # build the PDF
    doc.build(elements)
    print(f"  PDF saved: {output_path}")
    return output_path


def generate_report(report_data, output_dir, report_type='monthly', fmt='pdf'):
    """
    High-level function: generate a report in the requested format.
    Returns the path to the generated file.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{report_type}_report_{timestamp}"

    if fmt == 'html':
        html = render_html(report_data, report_type)
        out_path = os.path.join(output_dir, f"{base_name}.html")
        save_html(html, out_path)
        return out_path
    elif fmt == 'pdf':
        out_path = os.path.join(output_dir, f"{base_name}.pdf")
        generate_pdf(report_data, out_path, report_type)
        return out_path
    elif fmt == 'both':
        # generate both formats
        html = render_html(report_data, report_type)
        html_path = os.path.join(output_dir, f"{base_name}.html")
        save_html(html, html_path)

        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        generate_pdf(report_data, pdf_path, report_type)
        return pdf_path  # return pdf path as primary
    else:
        raise ValueError(f"Unknown format: {fmt}. Use 'pdf', 'html', or 'both'.")
