#!/usr/bin/env python3
"""
List all job search runs and their statistics
"""

from run_manager import RunManager
from datetime import datetime
import json


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


def main():
    print("\n" + "="*100)
    print(" "*40 + "JOB SEARCH RUNS")
    print("="*100 + "\n")
    
    runs = RunManager.list_all_runs()
    
    if not runs:
        print("No runs found. Create a new run with:")
        print("  python3 generate_emails_auto.py <cv_name>\n")
        return
    
    print(f"Found {len(runs)} run(s):\n")
    
    for i, run in enumerate(runs, 1):
        print(f"{i}. {run['run_name']}")
        print(f"   CV: {run['cv_name']}")
        print(f"   Created: {format_timestamp(run['created_at'])}")
        print(f"   Status: {run['status']}")
        
        # Load full metadata for stats
        run_dir = f"runs/{run['run_name']}"
        metadata_file = f"{run_dir}/run_metadata.json"
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                if 'stats' in metadata:
                    stats = metadata['stats']
                    print(f"   Stats:")
                    print(f"     - Jobs: {stats.get('jobs', 0)}")
                    print(f"     - Emails: {stats.get('emails_generated', 0)}")
                    print(f"     - Prompts: {stats.get('prompts_created', 0)}")
        except:
            pass
        
        print()
    
    print("="*100)
    print("\n💡 To use a specific run:")
    print("   1. Copy jobs.csv to the run's jobs/ directory")
    print("   2. Run: python3 generate_emails_auto.py\n")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
