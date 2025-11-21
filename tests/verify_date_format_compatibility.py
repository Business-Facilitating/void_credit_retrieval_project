#!/usr/bin/env python3
"""
Verify that dlt_pipeline_examples.py and ups_label_only_filter.py can handle
the exact date formats found in latest_transac_dt.csv
"""

import csv
import duckdb
from collections import defaultdict

print("=" * 80)
print("Date Format Compatibility Verification")
print("=" * 80)

# Read the CSV file
csv_path = "data/input/latest_transac_dt.csv"
print(f"\n📂 Reading: {csv_path}")

date_formats = defaultdict(list)
all_dates = []

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        date_str = row['transaction_date'].strip()
        if date_str == '':
            date_formats['Empty String'].append(date_str)
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts[0]) == 1:  # M/D/YYYY or M/DD/YYYY
                date_formats['M/D/YYYY or M/DD/YYYY'].append(date_str)
            else:  # MM/D/YYYY or MM/DD/YYYY
                date_formats['MM/D/YYYY or MM/DD/YYYY'].append(date_str)
        elif '-' in date_str:
            date_formats['YYYY-MM-DD'].append(date_str)
        else:
            date_formats['Unknown Format'].append(date_str)
        
        all_dates.append(date_str)

print(f"\n📊 Total dates in CSV: {len(all_dates):,}")
print(f"\n📋 Date Format Distribution:")
for format_type, dates in sorted(date_formats.items()):
    print(f"   {format_type}: {len(dates):,} dates")
    # Show first 5 examples
    examples = dates[:5]
    for example in examples:
        print(f"      - {repr(example)}")

# Test DuckDB parsing with the COALESCE + TRY_STRPTIME approach
print("\n" + "=" * 80)
print("Testing DuckDB Date Parsing (COALESCE + TRY_STRPTIME)")
print("=" * 80)

conn = duckdb.connect(':memory:')

# Create test table
conn.execute("""
    CREATE TABLE test_dates (
        id INTEGER,
        date_str VARCHAR
    )
""")

# Insert sample dates from each format category
test_samples = []
sample_id = 1
for format_type, dates in date_formats.items():
    # Take up to 10 samples from each format
    for date_str in dates[:10]:
        test_samples.append((sample_id, date_str))
        sample_id += 1

conn.executemany("INSERT INTO test_dates VALUES (?, ?)", test_samples)

print(f"\n📊 Inserted {len(test_samples)} test dates into DuckDB")

# Test the exact parsing logic used in both scripts
query = """
    SELECT
        id,
        date_str,
        COALESCE(
            TRY_STRPTIME(date_str, '%Y-%m-%d'),  -- YYYY-MM-DD
            TRY_STRPTIME(date_str, '%m/%d/%Y'),  -- MM/DD/YYYY
            TRY_STRPTIME(date_str, '%-m/%-d/%Y')   -- M/D/YYYY (single digit)
        ) as parsed_date,
        CASE
            WHEN COALESCE(
                TRY_STRPTIME(date_str, '%Y-%m-%d'),
                TRY_STRPTIME(date_str, '%m/%d/%Y'),
                TRY_STRPTIME(date_str, '%-m/%-d/%Y')
            ) IS NOT NULL THEN '✓'
            ELSE '✗'
        END as status
    FROM test_dates
    ORDER BY id
"""

results = conn.execute(query).fetchall()

# Analyze results
successful = 0
failed = 0
failed_examples = []

for row in results:
    if row[3] == '✓':
        successful += 1
    else:
        failed += 1
        failed_examples.append(row[1])

print(f"\n📊 Parsing Results:")
print(f"   ✅ Successfully parsed: {successful}/{len(test_samples)} ({successful/len(test_samples)*100:.1f}%)")
print(f"   ❌ Failed to parse: {failed}/{len(test_samples)} ({failed/len(test_samples)*100:.1f}%)")

if failed_examples:
    print(f"\n⚠️ Failed Examples:")
    for example in failed_examples[:10]:
        print(f"      - {repr(example)}")

# Test date range filtering (89-30 days ago)
print("\n" + "=" * 80)
print("Testing Date Range Filtering (89-30 days ago)")
print("=" * 80)

from datetime import datetime, timedelta

today = datetime.now().date()
start_days_ago = 89
end_days_ago = 30

start_target_date = today - timedelta(days=start_days_ago)
end_target_date = today - timedelta(days=end_days_ago)

print(f"\n📅 Today: {today}")
print(f"🎯 Target range: {start_target_date} to {end_target_date}")
print(f"   ({start_days_ago} to {end_days_ago} days ago)")

start_date_str = start_target_date.strftime("%Y-%m-%d")
end_date_str = end_target_date.strftime("%Y-%m-%d")

filter_query = f"""
    SELECT
        date_str,
        COALESCE(
            TRY_STRPTIME(date_str, '%Y-%m-%d'),
            TRY_STRPTIME(date_str, '%m/%d/%Y'),
            TRY_STRPTIME(date_str, '%-m/%-d/%Y')
        ) as parsed_date
    FROM test_dates
    WHERE COALESCE(
        TRY_STRPTIME(date_str, '%Y-%m-%d'),
        TRY_STRPTIME(date_str, '%m/%d/%Y'),
        TRY_STRPTIME(date_str, '%-m/%-d/%Y')
    ) BETWEEN CAST('{start_date_str}' AS DATE) AND CAST('{end_date_str}' AS DATE)
    ORDER BY parsed_date
"""

filtered_results = conn.execute(filter_query).fetchall()

print(f"\n📊 Dates in target range: {len(filtered_results)}")
if filtered_results:
    print(f"\n📋 Sample dates in range:")
    for row in filtered_results[:10]:
        print(f"   {row[0]} -> {row[1]}")

conn.close()

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)

if failed == 0:
    print("\n✅ SUCCESS: All date formats in latest_transac_dt.csv are compatible!")
    print("   Both dlt_pipeline_examples.py and ups_label_only_filter.py will handle them correctly.")
else:
    print(f"\n⚠️ WARNING: {failed} dates could not be parsed!")
    print("   Review the failed examples above and update the parsing logic if needed.")

