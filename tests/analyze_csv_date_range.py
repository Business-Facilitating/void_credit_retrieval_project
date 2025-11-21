#!/usr/bin/env python3
"""
Analyze the actual date range in latest_transac_dt.csv
"""

import csv
from datetime import datetime, timedelta

print("=" * 80)
print("Analyzing Date Range in latest_transac_dt.csv")
print("=" * 80)

csv_path = "data/input/latest_transac_dt.csv"

# Parse all dates
parsed_dates = []
unparseable = []

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        date_str = row['transaction_date'].strip()
        if date_str == '':
            unparseable.append(date_str)
            continue
        
        # Try multiple formats
        parsed = None
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%-m/%-d/%Y']:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        
        if parsed:
            parsed_dates.append((date_str, parsed))
        else:
            unparseable.append(date_str)

print(f"\n📊 Total dates: {len(parsed_dates) + len(unparseable):,}")
print(f"   ✅ Parseable: {len(parsed_dates):,}")
print(f"   ❌ Unparseable: {len(unparseable):,}")

if parsed_dates:
    # Sort by date
    parsed_dates.sort(key=lambda x: x[1])
    
    min_date = parsed_dates[0][1]
    max_date = parsed_dates[-1][1]
    
    print(f"\n📅 Date Range in CSV:")
    print(f"   Earliest: {min_date} ({parsed_dates[0][0]})")
    print(f"   Latest: {max_date} ({parsed_dates[-1][0]})")
    
    # Calculate days from today
    today = datetime.now().date()
    days_from_today_min = (today - min_date).days
    days_from_today_max = (today - max_date).days
    
    print(f"\n📊 Days from today ({today}):")
    print(f"   Earliest date is {days_from_today_min} days ago")
    print(f"   Latest date is {days_from_today_max} days ago")
    
    # Check if there are dates in the 89-30 day window
    start_days_ago = 89
    end_days_ago = 30
    
    start_target_date = today - timedelta(days=start_days_ago)
    end_target_date = today - timedelta(days=end_days_ago)
    
    print(f"\n🎯 Target range (89-30 days ago):")
    print(f"   {start_target_date} to {end_target_date}")
    
    dates_in_range = [d for d in parsed_dates if start_target_date <= d[1] <= end_target_date]
    
    print(f"\n📊 Dates in target range: {len(dates_in_range)}")
    
    if dates_in_range:
        print(f"\n📋 Sample dates in range:")
        for date_str, date_obj in dates_in_range[:20]:
            days_ago = (today - date_obj).days
            print(f"   {date_str} ({date_obj}) - {days_ago} days ago")
    else:
        print(f"\n⚠️ NO DATES IN TARGET RANGE!")
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Your data ranges from {days_from_today_min} to {days_from_today_max} days ago")
        print(f"   But you're looking for dates {start_days_ago} to {end_days_ago} days ago")
        print(f"\n   To extract data from this CSV, adjust the configuration:")
        print(f"   TRANSACTION_DATE_START_DAYS_AGO = {days_from_today_min}")
        print(f"   TRANSACTION_DATE_END_DAYS_AGO = {days_from_today_max}")
        
        # Show most recent dates
        print(f"\n📋 Most recent 20 dates in CSV:")
        for date_str, date_obj in parsed_dates[-20:]:
            days_ago = (today - date_obj).days
            print(f"   {date_str} ({date_obj}) - {days_ago} days ago")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

