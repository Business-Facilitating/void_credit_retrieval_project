#!/usr/bin/env python3
"""
Quick Setup for GSR Automation Pipeline
=======================================

This script provides a quick way to either:
1. Set up credentials for running fresh pipelines
2. Work with existing data files
3. Create a minimal .env for testing

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_minimal_env():
    """Create a minimal .env file for testing"""
    print("🔧 Creating minimal .env file for testing...")
    
    env_content = """# GSR Automation Environment Variables - Minimal Setup
# Copy this file to .env and fill in your actual credentials

# 17Track API Configuration (optional for carrier pipeline)
SEVENTEEN_TRACK_API_TOKEN=your_17track_api_token_here
SEVENTEEN_TRACK_API_URL=https://api.17track.net/track/v2.4/gettrackinfo
SEVENTEEN_TRACK_REGISTER_URL=https://api.17track.net/track/v2.2/register
SEVENTEEN_TRACK_DEFAULT_CARRIER_CODE=100002

# TrackingMore API Configuration (optional)
TRACKINGMORE_API_KEY=your_trackingmore_api_key_here

# ClickHouse Database Configuration (REQUIRED for carrier pipeline)
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=9440
CLICKHOUSE_USERNAME=your_clickhouse_username_here
CLICKHOUSE_PASSWORD=your_clickhouse_password_here
CLICKHOUSE_DATABASE=your_database_name_here
CLICKHOUSE_SECURE=true

# DLT Pipeline Configuration
DLT_WRITE_DISPOSITION=replace
DLT_CLICKHOUSE_BATCH_SIZE=50000
DLT_CLICKHOUSE_WINDOW_SECONDS=3600
DLT_INVOICE_CUTOFF_DAYS=30
DLT_FORCE_FULL_LOAD=false

# Application Configuration
BATCH_SIZE=40
API_DELAY=1.0
DUCKDB_PATH=carrier_invoice_extraction.duckdb
OUTPUT_DIR=data/output
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file with your actual credentials")
    return True

def check_existing_data():
    """Check and display existing data files"""
    print("📁 Checking existing data files...")
    
    output_dir = Path("data/output")
    if not output_dir.exists():
        print("❌ Output directory doesn't exist")
        return False
    
    # Get all CSV files
    csv_files = list(output_dir.glob("*.csv"))
    json_files = list(output_dir.glob("*.json"))
    
    if csv_files:
        print(f"\n📊 Found {len(csv_files)} CSV files:")
        for file in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            size = file.stat().st_size / 1024 / 1024  # MB
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"   📄 {file.name} ({size:.1f}MB, {mtime.strftime('%Y-%m-%d %H:%M')})")
    
    if json_files:
        print(f"\n📋 Found {len(json_files)} JSON files:")
        for file in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            size = file.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"   📄 {file.name} ({size:.1f}KB, {mtime.strftime('%Y-%m-%d %H:%M')})")
    
    return len(csv_files) > 0 or len(json_files) > 0

def show_menu():
    """Show the main menu"""
    print("\n🚀 GSR Automation Quick Setup")
    print("=" * 40)
    print("Choose an option:")
    print("1. 🔧 Create minimal .env file (for new setup)")
    print("2. 📁 View existing data files")
    print("3. 🏃 Try to run pipeline with current setup")
    print("4. 📖 Show setup instructions")
    print("5. ❌ Exit")
    
    return input("\nEnter your choice (1-5): ").strip()

def show_instructions():
    """Show detailed setup instructions"""
    print("\n📖 Setup Instructions")
    print("=" * 30)
    print("""
To run the pipeline today, you need:

🔑 ClickHouse Database Credentials:
   - Host (e.g., your-clickhouse-server.com)
   - Username and Password
   - Database name
   - Port (usually 9440 for secure connections)

🔑 API Keys (optional, for tracking):
   - 17Track API token
   - TrackingMore API key

📝 Steps:
   1. Choose option 1 to create .env file
   2. Edit .env file with your actual credentials
   3. Run: poetry run python run_pipeline_today.py

💡 If you don't have credentials:
   - You can still view existing data (option 2)
   - Contact your admin for ClickHouse access
   - Sign up for API keys at 17track.net or trackingmore.com
""")

def try_run_pipeline():
    """Try to run the pipeline with current setup"""
    print("\n🏃 Attempting to run pipeline...")
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ No .env file found. Please create one first (option 1)")
        return False
    
    # Try to run the pipeline
    import subprocess
    try:
        result = subprocess.run(
            ["poetry", "run", "python", "run_pipeline_today.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print("📤 Pipeline output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Errors/Warnings:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Pipeline timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return False

def main():
    """Main function"""
    print("🚀 GSR Automation - Quick Setup & Pipeline Runner")
    print("=" * 55)
    print(f"📅 Today: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            create_minimal_env()
        elif choice == "2":
            check_existing_data()
        elif choice == "3":
            try_run_pipeline()
        elif choice == "4":
            show_instructions()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
