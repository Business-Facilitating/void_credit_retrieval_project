#!/usr/bin/env python3
"""
DuckDB Query Examples for Carrier Invoice Data
==============================================

This file contains ready-to-use query examples for analyzing the carrier invoice data.
Use these in your Jupyter notebook or Python scripts.

Database: Main carrier invoice extraction database (all dates)
Records: ~935,481 records with 263 columns
"""

import os
from datetime import datetime

import duckdb
import pandas as pd

# Database path - use the main carrier invoice extraction database
MAIN_DB = "carrier_invoice_extraction.duckdb"


def connect_to_db():
    """Connect to the DuckDB database."""
    if not os.path.exists(MAIN_DB):
        print(f"❌ Database not found: {MAIN_DB}")
        return None
    return duckdb.connect(MAIN_DB)


def basic_data_overview():
    """Get basic overview of the data."""
    conn = connect_to_db()
    if not conn:
        return

    print("📊 BASIC DATA OVERVIEW")
    print("=" * 50)

    # Total records
    total = conn.execute(
        "SELECT COUNT(*) FROM carrier_invoice_extraction.carrier_invoice_data"
    ).fetchone()[0]
    print(f"Total Records: {total:,}")

    # Date range
    date_info = conn.execute(
        """
        SELECT
            MIN(invoice_date) as min_date,
            MAX(invoice_date) as max_date,
            COUNT(DISTINCT invoice_date) as unique_dates
        FROM carrier_invoice_extraction.carrier_invoice_data
    """
    ).fetchone()
    print(f"Date Range: {date_info[0]} to {date_info[1]} ({date_info[2]} unique dates)")

    # Tracking numbers
    tracking_info = conn.execute(
        """
        SELECT
            COUNT(tracking_number) as total_tracking,
            COUNT(DISTINCT tracking_number) as unique_tracking
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE tracking_number IS NOT NULL AND tracking_number != ''
    """
    ).fetchone()
    print(f"Tracking Numbers: {tracking_info[0]:,} total, {tracking_info[1]:,} unique")

    conn.close()


def top_senders_analysis():
    """Analyze top senders by shipment volume."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n📦 TOP SENDERS BY VOLUME")
    print("=" * 50)

    result = conn.execute(
        """
        SELECT
            sender_company_name,
            COUNT(*) as shipments,
            COUNT(DISTINCT tracking_number) as unique_packages,
            ROUND(SUM(CAST(net_amount AS DECIMAL)), 2) as total_amount
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE sender_company_name IS NOT NULL AND sender_company_name != ''
        GROUP BY sender_company_name
        ORDER BY shipments DESC
        LIMIT 15
    """
    ).fetchall()

    print("Company Name                    | Shipments | Packages | Total Amount")
    print("-" * 70)
    for row in result:
        company = (row[0] or "")[:30]
        print(f"{company:<30} | {row[1]:>9,} | {row[2]:>8,} | ${row[3]:>10,.2f}")

    conn.close()


def top_receivers_analysis():
    """Analyze top receivers by shipment volume."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n📬 TOP RECEIVERS BY VOLUME")
    print("=" * 50)

    result = conn.execute(
        """
        SELECT
            receiver_company_name,
            COUNT(*) as shipments,
            COUNT(DISTINCT tracking_number) as unique_packages,
            ROUND(SUM(CAST(net_amount AS DECIMAL)), 2) as total_amount
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE receiver_company_name IS NOT NULL AND receiver_company_name != ''
        GROUP BY receiver_company_name
        ORDER BY shipments DESC
        LIMIT 15
    """
    ).fetchall()

    print("Company Name                    | Shipments | Packages | Total Amount")
    print("-" * 70)
    for row in result:
        company = (row[0] or "")[:30]
        print(f"{company:<30} | {row[1]:>9,} | {row[2]:>8,} | ${row[3]:>10,.2f}")

    conn.close()


def geographic_analysis():
    """Analyze shipments by state/geography."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n🗺️ GEOGRAPHIC ANALYSIS")
    print("=" * 50)

    # Top sender states
    print("Top Sender States:")
    sender_states = conn.execute(
        """
        SELECT
            sender_state,
            COUNT(*) as shipments,
            COUNT(DISTINCT sender_company_name) as companies
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE sender_state IS NOT NULL AND sender_state != ''
        GROUP BY sender_state
        ORDER BY shipments DESC
        LIMIT 10
    """
    ).fetchall()

    for row in sender_states:
        print(f"  {row[0]}: {row[1]:,} shipments from {row[2]:,} companies")

    print("\nTop Receiver States:")
    receiver_states = conn.execute(
        """
        SELECT
            receiver_state,
            COUNT(*) as shipments,
            COUNT(DISTINCT receiver_company_name) as companies
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE receiver_state IS NOT NULL AND receiver_state != ''
        GROUP BY receiver_state
        ORDER BY shipments DESC
        LIMIT 10
    """
    ).fetchall()

    for row in receiver_states:
        print(f"  {row[0]}: {row[1]:,} shipments to {row[2]:,} companies")

    conn.close()


def service_type_analysis():
    """Analyze different service types and charges."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n🚚 SERVICE TYPE ANALYSIS")
    print("=" * 50)

    result = conn.execute(
        """
        SELECT
            charge_description,
            COUNT(*) as frequency,
            ROUND(AVG(CAST(net_amount AS DECIMAL)), 2) as avg_amount,
            ROUND(SUM(CAST(net_amount AS DECIMAL)), 2) as total_amount
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE charge_description IS NOT NULL AND charge_description != ''
        GROUP BY charge_description
        ORDER BY frequency DESC
        LIMIT 15
    """
    ).fetchall()

    print("Service Type                    | Frequency | Avg Amount | Total Amount")
    print("-" * 75)
    for row in result:
        service = (row[0] or "")[:30]
        print(f"{service:<30} | {row[1]:>9,} | ${row[2]:>9,.2f} | ${row[3]:>11,.2f}")

    conn.close()


def tracking_number_patterns():
    """Analyze tracking number patterns."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n📋 TRACKING NUMBER PATTERNS")
    print("=" * 50)

    # Tracking number prefixes
    result = conn.execute(
        """
        SELECT
            SUBSTR(tracking_number, 1, 2) as prefix,
            COUNT(*) as count,
            COUNT(DISTINCT tracking_number) as unique_numbers
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE tracking_number IS NOT NULL
        AND tracking_number != ''
        AND LENGTH(tracking_number) > 2
        GROUP BY SUBSTR(tracking_number, 1, 2)
        ORDER BY count DESC
        LIMIT 10
    """
    ).fetchall()

    print("Prefix | Count     | Unique Numbers")
    print("-" * 35)
    for row in result:
        print(f"{row[0]:<6} | {row[1]:>8,} | {row[2]:>13,}")

    conn.close()


def financial_summary():
    """Financial summary of the data."""
    conn = connect_to_db()
    if not conn:
        return

    print("\n💰 FINANCIAL SUMMARY")
    print("=" * 50)

    result = conn.execute(
        """
        SELECT
            COUNT(*) as total_records,
            ROUND(SUM(CAST(net_amount AS DECIMAL)), 2) as total_net_amount,
            ROUND(AVG(CAST(net_amount AS DECIMAL)), 2) as avg_net_amount,
            ROUND(SUM(CAST(invoice_amount AS DECIMAL)), 2) as total_invoice_amount,
            COUNT(DISTINCT invoice_number) as unique_invoices
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE net_amount IS NOT NULL AND net_amount != ''
    """
    ).fetchone()

    print(f"Total Records: {result[0]:,}")
    print(f"Total Net Amount: ${result[1]:,.2f}")
    print(f"Average Net Amount: ${result[2]:,.2f}")
    print(f"Total Invoice Amount: ${result[3]:,.2f}")
    print(f"Unique Invoices: {result[4]:,}")

    conn.close()


def search_tracking_number(tracking_num):
    """Search for a specific tracking number."""
    conn = connect_to_db()
    if not conn:
        return

    print(f"\n🔍 TRACKING NUMBER SEARCH: {tracking_num}")
    print("=" * 60)

    result = conn.execute(
        """
        SELECT
            tracking_number,
            invoice_date,
            invoice_number,
            sender_company_name,
            receiver_company_name,
            sender_city,
            sender_state,
            receiver_city,
            receiver_state,
            net_amount,
            charge_description
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE tracking_number = ?
    """,
        [tracking_num],
    ).fetchall()

    if result:
        for row in result:
            print(f"Tracking: {row[0]}")
            print(f"Invoice Date: {row[1]}")
            print(f"Invoice #: {row[2]}")
            print(f"From: {row[3]} ({row[5]}, {row[6]})")
            print(f"To: {row[4]} ({row[7]}, {row[8]})")
            print(f"Amount: ${row[9]}")
            print(f"Service: {row[10]}")
            print("-" * 40)
    else:
        print("No records found for this tracking number.")

    conn.close()


def export_to_pandas():
    """Example of how to export data to pandas DataFrame."""
    conn = connect_to_db()
    if not conn:
        return None

    print("\n📊 EXPORTING TO PANDAS")
    print("=" * 50)

    # Example query - top 1000 records
    df = conn.execute(
        """
        SELECT
            tracking_number,
            invoice_date,
            sender_company_name,
            receiver_company_name,
            sender_state,
            receiver_state,
            net_amount,
            charge_description
        FROM carrier_invoice_extraction.carrier_invoice_data
        WHERE tracking_number IS NOT NULL AND tracking_number != ''
        LIMIT 1000
    """
    ).df()

    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 5 rows:")
    print(df.head())

    conn.close()
    return df


if __name__ == "__main__":
    """Run all analysis functions."""
    basic_data_overview()
    top_senders_analysis()
    top_receivers_analysis()
    geographic_analysis()
    service_type_analysis()
    tracking_number_patterns()
    financial_summary()

    # Example tracking number search
    # search_tracking_number("1Z3X66Y00316040373")

    # Export to pandas
    # df = export_to_pandas()
