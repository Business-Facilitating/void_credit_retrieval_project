"""Check the current database statistics"""
import duckdb
from datetime import datetime, timedelta

# Connect to the database
db_path = "data/output/carrier_invoice_extraction.duckdb"
conn = duckdb.connect(db_path, read_only=True)

print(f"📊 Database Statistics for: {db_path}")
print("=" * 80)

# Check total records
total_query = "SELECT COUNT(*) as total FROM carrier_invoice_data"
total_result = conn.execute(total_query).fetchone()
print(f"\n📦 Total records: {total_result[0]:,}")

# Check date range
date_range_query = """
SELECT 
    MIN(COALESCE(
        TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
        TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
        TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
    )) as min_date,
    MAX(COALESCE(
        TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
        TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
        TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
    )) as max_date
FROM carrier_invoice_data
WHERE transaction_date IS NOT NULL AND transaction_date != ''
"""
date_result = conn.execute(date_range_query).fetchone()
print(f"📅 Transaction date range: {date_result[0]} to {date_result[1]}")

# Check unique tracking numbers
tracking_query = "SELECT COUNT(DISTINCT tracking_number) as unique_tracking FROM carrier_invoice_data WHERE tracking_number IS NOT NULL"
tracking_result = conn.execute(tracking_query).fetchone()
print(f"🔢 Unique tracking numbers: {tracking_result[0]:,}")

# Check records in target date range (89-50 days ago)
start_days_ago = 89
end_days_ago = 50
start_date = (datetime.utcnow() - timedelta(days=start_days_ago)).date()
end_date = (datetime.utcnow() - timedelta(days=end_days_ago)).date()

target_range_query = f"""
SELECT COUNT(*) as count_in_range
FROM carrier_invoice_data
WHERE (
    COALESCE(
        TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
        TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
        TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
    ) BETWEEN CAST('{start_date}' AS DATE) AND CAST('{end_date}' AS DATE)
)
"""
target_result = conn.execute(target_range_query).fetchone()
print(f"\n🎯 Records in target range ({start_date} to {end_date}): {target_result[0]:,}")

# Check unique tracking numbers in target range
target_tracking_query = f"""
SELECT COUNT(DISTINCT tracking_number) as unique_tracking
FROM carrier_invoice_data
WHERE tracking_number IS NOT NULL
AND tracking_number != ''
AND LENGTH(TRIM(tracking_number)) > 0
AND tracking_number LIKE '1Z%'
AND (
    COALESCE(
        TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
        TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
        TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
    ) BETWEEN CAST('{start_date}' AS DATE) AND CAST('{end_date}' AS DATE)
)
"""
target_tracking_result = conn.execute(target_tracking_query).fetchone()
print(f"🔢 Unique UPS tracking numbers in target range: {target_tracking_result[0]:,}")

conn.close()
print("\n✅ Analysis complete!")

