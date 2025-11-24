#!/usr/bin/env python3
"""
Export all run metadata and logs to Excel file
Creates a comprehensive Excel workbook with multiple sheets
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from run_manager import RunManager
import re


def parse_log_file(log_file_path):
    """Parse log file and extract structured data"""
    logs = []
    
    if not Path(log_file_path).exists():
        return logs
    
    with open(log_file_path, 'r') as f:
        for line in f:
            # Parse log line: timestamp - logger - level - message
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.+?) - (\w+) - (.+)', line.strip())
            if match:
                timestamp, logger, level, message = match.groups()
                logs.append({
                    'timestamp': timestamp,
                    'logger': logger,
                    'level': level,
                    'message': message
                })
    
    return logs


def export_runs_to_excel(output_file="runs_export.xlsx"):
    """
    Export all runs with metadata and logs to Excel
    
    Args:
        output_file: Output Excel file name
    """
    print("\n" + "="*80)
    print(" "*25 + "EXPORT RUNS TO EXCEL")
    print("="*80 + "\n")
    
    runs = RunManager.list_all_runs()
    
    if not runs:
        print("❌ No runs found to export.")
        return
    
    print(f"📊 Found {len(runs)} run(s) to export...\n")
    
    # Prepare data structures
    runs_summary = []
    all_logs = []
    run_details = []
    
    for run in runs:
        run_dir = Path("runs") / run['run_name']
        metadata_file = run_dir / "run_metadata.json"
        
        # Load full metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Summary data
        stats = metadata.get('stats', {})
        summary_row = {
            'Run Name': run['run_name'],
            'CV Name': run['cv_name'],
            'Created At': run['created_at'],
            'Status': run['status'],
            'Jobs Found': stats.get('jobs', 0),
            'Emails Generated': stats.get('emails_generated', 0),
            'Prompts Created': stats.get('prompts_created', 0),
            'Updated At': metadata.get('updated_at', ''),
            'Run Directory': str(run_dir)
        }
        runs_summary.append(summary_row)
        
        # Detailed metadata (flatten JSON)
        detail_row = {
            'Run Name': run['run_name'],
            'CV Name': run['cv_name'],
            'Created At': run['created_at'],
            'Updated At': metadata.get('updated_at', ''),
            'Status': run['status'],
            'Run Directory': metadata.get('run_dir', ''),
            'Jobs': stats.get('jobs', 0),
            'Emails': stats.get('emails_generated', 0),
            'Prompts': stats.get('prompts_created', 0),
        }
        
        # Add any additional stats
        for key, value in stats.items():
            if key not in ['jobs', 'emails_generated', 'prompts_created']:
                detail_row[f'Stats_{key}'] = value
        
        run_details.append(detail_row)
        
        # Parse logs
        logs_dir = run_dir / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                logs = parse_log_file(log_file)
                for log in logs:
                    log['run_name'] = run['run_name']
                    log['cv_name'] = run['cv_name']
                    log['log_file'] = log_file.name
                    all_logs.append(log)
        
        print(f"✅ Processed: {run['run_name']}")
    
    # Collect ALL jobs from all runs
    all_jobs_list = []
    for run in runs:
        run_dir = Path("runs") / run['run_name']
        jobs_csv = run_dir / "jobs" / "jobs.csv"
        if jobs_csv.exists():
            try:
                run_jobs_df = pd.read_csv(jobs_csv)
                run_jobs_df['run_name'] = run['run_name'] # Add run context
                run_jobs_df['cv_name'] = run['cv_name']
                all_jobs_list.append(run_jobs_df)
            except Exception as e:
                print(f"⚠️  Could not read jobs.csv for {run['run_name']}: {e}")

    # Create Excel writer
    print(f"\n📝 Creating Excel file: {output_file}")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Summary
        df_summary = pd.DataFrame(runs_summary)
        df_summary.to_excel(writer, sheet_name='Runs Summary', index=False)
        print("  ✅ Sheet 'Runs Summary' created")
        
        # Sheet 2: Detailed Metadata
        df_details = pd.DataFrame(run_details)
        df_details.to_excel(writer, sheet_name='Run Details', index=False)
        print("  ✅ Sheet 'Run Details' created")
        
        # Sheet 3 & 4: WORLD and EUROPE Jobs (Aggregated)
        if all_jobs_list:
            all_jobs_df = pd.concat(all_jobs_list, ignore_index=True)
            
            # Sort by suitability_score if available
            if 'suitability_score' in all_jobs_df.columns:
                all_jobs_df = all_jobs_df.sort_values(by='suitability_score', ascending=False)
                print("  ✅ Sorted jobs by suitability score")
            
            # WORLD Jobs (All jobs)
            all_jobs_df.to_excel(writer, sheet_name='All Jobs (World)', index=False)
            print(f"  ✅ Sheet 'All Jobs (World)' created ({len(all_jobs_df)} jobs)")
            
            # Dynamic Region Sheets
            # Find unique regions excluding WORLDWIDE/World
            if 'region' in all_jobs_df.columns:
                regions = all_jobs_df['region'].unique()
                for region in regions:
                    # Skip invalid regions
                    if pd.isna(region) or str(region).upper() in ['WORLDWIDE', 'WORLD', 'NAN', 'NONE']:
                        continue
                        
                    # Filter for this region
                    region_df = all_jobs_df[all_jobs_df['region'] == region]
                    
                    # Create safe sheet name (max 31 chars)
                    sheet_name = f"{str(region)[:20]} Jobs"
                    sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_'))
                    
                    region_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  ✅ Sheet '{sheet_name}' created ({len(region_df)} jobs)")
            
            # Fallback: If no region column, try to find UK/Europe jobs based on location text
            else:
                europe_keywords = ['London', 'UK', 'United Kingdom', 'Europe', 'Germany', 'France', 'Spain', 'Italy', 'Netherlands', 'Berlin', 'Paris', 'Madrid', 'Amsterdam']
                pattern = '|'.join(europe_keywords)
                
                europe_df = all_jobs_df[
                    all_jobs_df['location'].str.contains(pattern, case=False, na=False)
                ]
                
                if not europe_df.empty:
                    europe_df.to_excel(writer, sheet_name='Europe & UK Jobs', index=False)
                    print(f"  ✅ Sheet 'Europe & UK Jobs' created ({len(europe_df)} jobs)")

        # Sheet 5: All Logs
        if all_logs:
            df_logs = pd.DataFrame(all_logs)
            # Reorder columns
            cols = ['run_name', 'cv_name', 'timestamp', 'level', 'message', 'log_file', 'logger']
            df_logs = df_logs[cols]
            df_logs.to_excel(writer, sheet_name='All Logs', index=False)
            print(f"  ✅ Sheet 'All Logs' created ({len(all_logs)} log entries)")
        
        # Sheet 6: Logs by Level
        if all_logs:
            df_logs_grouped = df_logs.groupby(['run_name', 'level']).size().reset_index(name='count')
            df_logs_grouped.to_excel(writer, sheet_name='Logs by Level', index=False)
            print("  ✅ Sheet 'Logs by Level' created")
        
        # Sheet 7+: Individual run sheets (if not too many)
        if len(runs) <= 10:
            for run in runs:
                run_dir = Path("runs") / run['run_name']
                logs_dir = run_dir / "logs"
                
                run_logs = []
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        run_logs.extend(parse_log_file(log_file))
                
                if run_logs:
                    df_run_logs = pd.DataFrame(run_logs)
                    # Create unique sheet name (CV name + last 6 chars of run name)
                    # Excel sheet name limit is 31 chars
                    suffix = f"_{run['run_name'][-6:]}"
                    max_name_len = 31 - len(suffix)
                    safe_cv_name = run['cv_name'][:max_name_len]
                    sheet_name = f"{safe_cv_name}{suffix}"
                    
                    df_run_logs.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  ✅ Sheet '{sheet_name}' created")
    
    print("\n" + "="*80)
    print(f"✅ EXPORT COMPLETE!")
    print("="*80 + "\n")
    
    print(f"📁 File saved: {output_file}")
    print(f"📊 Sheets created:")
    print(f"   1. Runs Summary - Overview of all runs")
    print(f"   2. Run Details - Detailed metadata")
    print(f"   3. All Logs - Complete log history")
    print(f"   4. Logs by Level - Log statistics")
    if len(runs) <= 10:
        print(f"   5+. Individual run logs (one per CV)")
    
    print("\n💡 Open with:")
    print(f"   open {output_file}")
    print("\n" + "="*80 + "\n")
    
    return output_file


def export_single_run(run_name, output_file=None):
    """
    Export a single run to Excel
    
    Args:
        run_name: Name of the run to export
        output_file: Optional output file name
    """
    if not output_file:
        output_file = f"{run_name}_export.xlsx"
    
    run_dir = Path("runs") / run_name
    
    if not run_dir.exists():
        print(f"❌ Run not found: {run_name}")
        return
    
    print(f"\n📊 Exporting run: {run_name}\n")
    
    # Load metadata
    metadata_file = run_dir / "run_metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    # Parse logs
    all_logs = []
    logs_dir = run_dir / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            logs = parse_log_file(log_file)
            for log in logs:
                log['log_file'] = log_file.name
                all_logs.append(log)
    
    # Create Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Metadata
        metadata_flat = []
        for key, value in metadata.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    metadata_flat.append({'Key': f"{key}.{subkey}", 'Value': str(subvalue)})
            else:
                metadata_flat.append({'Key': key, 'Value': str(value)})
        
        df_metadata = pd.DataFrame(metadata_flat)
        df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        # Sheet 2: Logs
        if all_logs:
            df_logs = pd.DataFrame(all_logs)
            df_logs.to_excel(writer, sheet_name='Logs', index=False)
        
        # Sheet 3: Log Summary
        if all_logs:
            df_logs_summary = df_logs.groupby('level').size().reset_index(name='count')
            df_logs_summary.to_excel(writer, sheet_name='Log Summary', index=False)
    
    print(f"✅ Exported to: {output_file}\n")
    return output_file


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Export specific run
        run_name = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        export_single_run(run_name, output_file)
    else:
        # Export all runs
        output_file = sys.argv[1] if len(sys.argv) > 1 else "runs_export.xlsx"
        export_runs_to_excel(output_file)
