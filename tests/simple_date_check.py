#!/usr/bin/env python3

import sys
sys.path.append('src/src')

try:
    from dlt_pipeline_examples import export_to_csv
    import dlt
    
    print("🔍 Attempting to export data from DuckDB...")
    
    # Create a pipeline object to use for export
    pipeline = dlt.pipeline(
        pipeline_name="carrier_invoice_extraction",
        destination="duckdb",
        dataset_name="carrier_invoice_data",
    )
    
    # Try to export
    export_to_csv(pipeline)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
