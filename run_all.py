#!/usr/bin/env python3
"""
Pipeline runner for the job search automator.

Usage:
    python3 run_all.py

The CV to use is defined in config.json under the "cv" section.
"""

import json
import sys
import os
from pathlib import Path

# Add scripts directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from run_manager import RunManager
from extract_cv import extract_text_from_pdf
from search_jobs import JobSearcher
from generate_cover_letters import main as generate_cover_letters_main
from export_to_excel import export_runs_to_excel


def load_config(config_path: str = "config.json") -> dict:
    """Load JSON config and return as dict."""
    with open(config_path, "r") as f:
        return json.load(f)


def main():
    # 1. Load config
    config = load_config()

    # 2. Read CV info from config
    cv_cfg = config.get("cv", {})
    cv_name = cv_cfg.get("name")
    cv_file_path = cv_cfg.get("file_path")

    if not cv_name:
        raise ValueError("config.json is missing cv.name")
    if not cv_file_path:
        raise ValueError("config.json is missing cv.file_path")

    cv_path = Path(cv_file_path)
    if not cv_path.exists():
        # Try relative to project root if not absolute
        if not cv_path.is_absolute():
            cv_path = Path.cwd() / cv_file_path
            
        if not cv_path.exists():
             raise FileNotFoundError(f"CV file not found: {cv_path}")

    print("=" * 80)
    print(f"Running pipeline for CV: {cv_name}")
    print(f"CV file: {cv_path}")
    print("=" * 80 + "\n")

    # 3. Create a RunManager for this CV
    run_mgr = RunManager(cv_name=cv_name)
    print(f"Run directory: {run_mgr.run_dir}\n")

    # 4. (Optional) Extract CV text — currently not used in job search,
    # but available if you want to tailor queries later.
    try:
        cv_text = extract_text_from_pdf(str(cv_path))
        # You can log or inspect this if needed:
        run_mgr.logger.info("Extracted CV text length: %d", len(cv_text))
    except Exception as e:
        print(f"⚠️  Warning: Could not extract text from CV: {e}")
        run_mgr.logger.warning(f"Could not extract text from CV: {e}")

    # 5. Run job search (using global queries from config.json)
    searcher = JobSearcher()
    searcher.search_all()                 # uses config['job_search']['queries']
    
    jobs_csv_path = run_mgr.get_jobs_csv_path()
    jobs_xlsx_path = jobs_csv_path.parent / "jobs.xlsx"
    jobs_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Save jobs to THIS run's directory
    searcher.save_to_csv(filename=str(jobs_csv_path))
    searcher.save_to_excel(filename=str(jobs_xlsx_path))
    
    # Also save to root jobs.csv/xlsx for convenience/legacy support
    searcher.save_to_csv(filename="jobs.csv")
    searcher.save_to_excel(filename="jobs.xlsx")
    
    searcher.display_summary()

    # 6. Generate cover letters for this specific run (uses RunManager inside)
    #    We call it WITHOUT arguments so it picks up the most recent run (the one we just created).
    #    If we passed cv_name, it would force creating a NEW run, which we don't want.
    print(f"\n📧 Generating cover letters for run: {run_mgr.run_name}")
    generate_cover_letters_main()

    # 7. Export all runs to Excel (or just this one if you prefer)
    export_runs_to_excel("runs_export.xlsx")

    print("=" * 80)
    print("✅ All steps completed successfully!")
    print(f"   - Run directory: {run_mgr.run_dir}")
    print("   - Excel export: runs_export.xlsx")
    print("=" * 80)


if __name__ == "__main__":
    main()
