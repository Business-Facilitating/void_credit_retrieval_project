#!/usr/bin/env python3
"""Quick check of PeerDB extraction results"""

import duckdb

conn = duckdb.connect('peerdb_industry_index_logins.duckdb')

print("📊 Row count:", conn.execute('SELECT COUNT(*) FROM peerdb_data.industry_index_logins').fetchone()[0])

print("\n📋 Columns:")
for col in conn.execute('DESCRIBE peerdb_data.industry_index_logins').fetchall():
    print(f"   - {col[0]}: {col[1]}")

print("\n📝 Sample data (first 3 rows):")
result = conn.execute('''
    SELECT primary_key_for_updating, account_number, account_type, carrier_login, update_date
    FROM peerdb_data.industry_index_logins 
    LIMIT 3
''').fetchall()

for row in result:
    print(f"   {row}")

conn.close()

