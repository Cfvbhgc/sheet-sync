"""
processor.py - Data processing / aggregation module
Uses pandas to group, aggregate, and compute summary stats.
All functions take a DataFrame and return processed data (dicts, DataFrames, etc.)
"""

import pandas as pd
import numpy as np


def ensure_date_column(df):
    """Make sure we have a usable date column. Returns (df, date_col_name)."""
    # look for common date column names
    candidates = ['date', 'order_date', 'sale_date', 'created_at', 'timestamp']
    date_col = None
    for c in candidates:
        if c in df.columns:
            date_col = c
            break

    # fallback: just pick the first datetime column
    if date_col is None:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break

    if date_col is None:
        raise ValueError("No date column found in data! Need a date column for time-based reports.")

    # make sure it's actually datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    return df, date_col


def process_monthly(df):
    """
    Group sales data by month. Returns a dict with all the stats
    needed for the monthly report template.
    """
    print("[Processor] Running monthly aggregation...")

    df, date_col = ensure_date_column(df)

    # add helper columns for grouping
    df['_month'] = df[date_col].dt.to_period('M')
    df['_month_str'] = df[date_col].dt.strftime('%B %Y')

    # figure out the revenue column — look for total, revenue, amount, price
    rev_col = _find_numeric_col(df, ['total', 'revenue', 'amount', 'price', 'sales'])
    qty_col = _find_numeric_col(df, ['quantity', 'qty', 'units', 'count'])
    product_col = _find_text_col(df, ['product', 'item', 'name', 'sku', 'product_name'])

    print(f"  Using columns: revenue={rev_col}, quantity={qty_col}, product={product_col}")

    # --- monthly totals ---
    monthly_grp = df.groupby('_month_str', sort=False)
    monthly_summary = []
    for month_name, grp in monthly_grp:
        row = {
            'month': month_name,
            'total_revenue': round(grp[rev_col].sum(), 2) if rev_col else 0,
            'total_orders': len(grp),
            'avg_order_value': round(grp[rev_col].mean(), 2) if rev_col else 0,
        }
        if qty_col:
            row['total_units'] = int(grp[qty_col].sum())
        monthly_summary.append(row)

    # --- top products (overall) ---
    top_products = []
    if product_col and rev_col:
        prod_grp = df.groupby(product_col)[rev_col].agg(['sum', 'count', 'mean'])
        prod_grp = prod_grp.sort_values('sum', ascending=False).head(10)
        for prod, stats in prod_grp.iterrows():
            top_products.append({
                'product': prod,
                'total_revenue': round(stats['sum'], 2),
                'num_orders': int(stats['count']),
                'avg_price': round(stats['mean'], 2),
            })

    # --- overall summary stats ---
    total_rev = round(df[rev_col].sum(), 2) if rev_col else 0
    total_orders = len(df)
    avg_order = round(df[rev_col].mean(), 2) if rev_col else 0

    # growth calc — compare last month to previous month
    growth_pct = _calc_growth(df, date_col, rev_col)

    summary = {
        'total_revenue': total_rev,
        'total_orders': total_orders,
        'avg_order_value': avg_order,
        'growth_pct': growth_pct,
        'date_range': f"{df[date_col].min().strftime('%Y-%m-%d')} to {df[date_col].max().strftime('%Y-%m-%d')}",
    }

    # clean up temp columns
    df.drop(columns=['_month', '_month_str'], inplace=True, errors='ignore')

    print(f"  Monthly summary: {len(monthly_summary)} months, {len(top_products)} top products")
    return {
        'summary': summary,
        'monthly_data': monthly_summary,
        'top_products': top_products,
        'report_type': 'Monthly Report',
    }


def process_weekly(df):
    """
    Group sales data by week. Similar to monthly but with weekly granularity.
    """
    print("[Processor] Running weekly aggregation...")

    df, date_col = ensure_date_column(df)

    rev_col = _find_numeric_col(df, ['total', 'revenue', 'amount', 'price', 'sales'])
    qty_col = _find_numeric_col(df, ['quantity', 'qty', 'units', 'count'])
    product_col = _find_text_col(df, ['product', 'item', 'name', 'sku', 'product_name'])

    # group by ISO week
    df['_week'] = df[date_col].dt.isocalendar().week.astype(int)
    df['_year'] = df[date_col].dt.year
    df['_week_label'] = df.apply(lambda r: f"Week {r['_week']} ({r['_year']})", axis=1)

    weekly_summary = []
    wk_grp = df.groupby(['_year', '_week', '_week_label'], sort=True)
    for (yr, wk, label), grp in wk_grp:
        row = {
            'week': label,
            'total_revenue': round(grp[rev_col].sum(), 2) if rev_col else 0,
            'total_orders': len(grp),
            'avg_order_value': round(grp[rev_col].mean(), 2) if rev_col else 0,
        }
        if qty_col:
            row['total_units'] = int(grp[qty_col].sum())
        weekly_summary.append(row)

    # top products for the week (just use overall)
    top_products = []
    if product_col and rev_col:
        prod_grp = df.groupby(product_col)[rev_col].agg(['sum', 'count'])
        prod_grp = prod_grp.sort_values('sum', ascending=False).head(10)
        for prod, stats in prod_grp.iterrows():
            top_products.append({
                'product': prod,
                'total_revenue': round(stats['sum'], 2),
                'num_orders': int(stats['count']),
            })

    total_rev = round(df[rev_col].sum(), 2) if rev_col else 0

    summary = {
        'total_revenue': total_rev,
        'total_orders': len(df),
        'avg_order_value': round(df[rev_col].mean(), 2) if rev_col else 0,
        'growth_pct': _calc_growth(df, date_col, rev_col),
        'date_range': f"{df[date_col].min().strftime('%Y-%m-%d')} to {df[date_col].max().strftime('%Y-%m-%d')}",
    }

    df.drop(columns=['_week', '_year', '_week_label'], inplace=True, errors='ignore')

    print(f"  Weekly summary: {len(weekly_summary)} weeks, {len(top_products)} top products")
    return {
        'summary': summary,
        'weekly_data': weekly_summary,
        'top_products': top_products,
        'report_type': 'Weekly Report',
    }


# --- helper functions (internal) ---

def _find_numeric_col(df, hints):
    """Find the first numeric column whose name matches one of the hints."""
    for hint in hints:
        for col in df.columns:
            if hint in col.lower() and pd.api.types.is_numeric_dtype(df[col]):
                return col
    return None


def _find_text_col(df, hints):
    """Find the first text/object column matching hints."""
    for hint in hints:
        for col in df.columns:
            if hint in col.lower() and (df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col])):
                return col
    return None


def _calc_growth(df, date_col, rev_col):
    """Calculate month-over-month growth percentage for the last two months."""
    if rev_col is None:
        return 0.0

    df_temp = df.copy()
    df_temp['_m'] = df_temp[date_col].dt.to_period('M')
    monthly_totals = df_temp.groupby('_m')[rev_col].sum().sort_index()

    if len(monthly_totals) < 2:
        return 0.0

    last = monthly_totals.iloc[-1]
    prev = monthly_totals.iloc[-2]

    if prev == 0:
        return 0.0

    growth = ((last - prev) / prev) * 100
    return round(growth, 1)
