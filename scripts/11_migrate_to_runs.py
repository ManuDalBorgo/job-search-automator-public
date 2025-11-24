"""
Migrate existing job search data to new run-based structure
"""

import os
import shutil
from pathlib import Path
from run_manager import RunManager


def migrate_existing_data(cv_name="existing_cv"):
    """
    Migrate existing jobs.csv, generated_emails, and ai_prompts to new structure
    
    Args:
        cv_name: Name to use for the migrated run
    """
    print("\n" + "="*80)
    print("MIGRATING EXISTING DATA TO NEW STRUCTURE")
    print("="*80 + "\n")
    
    # Create new run
    print(f"📁 Creating run for: {cv_name}")
    run_mgr = RunManager(cv_name=cv_name)
    
    migrated_files = []
    
    # Migrate jobs.csv
    if os.path.exists("jobs.csv"):
        dest = run_mgr.get_jobs_csv_path()
        shutil.copy2("jobs.csv", dest)
        migrated_files.append(f"jobs.csv -> {dest}")
        print(f"✅ Migrated jobs.csv")
    
    # Migrate generated_emails
    if os.path.exists("generated_emails"):
        emails_dir = Path("generated_emails")
        for email_file in emails_dir.glob("*.txt"):
            dest = run_mgr.emails_dir / email_file.name
            shutil.copy2(email_file, dest)
        
        count = len(list(run_mgr.emails_dir.glob("*.txt")))
        migrated_files.append(f"generated_emails/*.txt -> {run_mgr.emails_dir} ({count} files)")
        print(f"✅ Migrated {count} email files")
    
    # Migrate ai_prompts
    if os.path.exists("ai_prompts"):
        prompts_dir = Path("ai_prompts")
        for prompt_file in prompts_dir.glob("*.txt"):
            dest = run_mgr.prompts_dir / prompt_file.name
            shutil.copy2(prompt_file, dest)
        
        count = len(list(run_mgr.prompts_dir.glob("*.txt")))
        migrated_files.append(f"ai_prompts/*.txt -> {run_mgr.prompts_dir} ({count} files)")
        print(f"✅ Migrated {count} prompt files")
    
    # Copy CV if it exists
    cv_files = list(Path(".").glob("*.pdf"))
    if cv_files:
        cv_source = cv_files[0]  # Take first PDF found
        run_mgr.copy_cv(cv_source)
        migrated_files.append(f"{cv_source} -> {run_mgr.get_cv_path()}")
        print(f"✅ Copied CV: {cv_source.name}")
    
    # Update run status
    summary = run_mgr.get_summary()
    run_mgr.update_status("migrated", stats=summary["counts"])
    
    print("\n" + "="*80)
    print("MIGRATION COMPLETE!")
    print("="*80 + "\n")
    
    print(f"📂 New run directory: {run_mgr.run_dir}\n")
    print("📊 Summary:")
    print(f"   - Jobs: {summary['counts']['jobs']}")
    print(f"   - Emails: {summary['counts']['emails_generated']}")
    print(f"   - Prompts: {summary['counts']['prompts_created']}")
    
    print("\n📋 Migrated files:")
    for item in migrated_files:
        print(f"   - {item}")
    
    print("\n💡 Next steps:")
    print(f"   1. Your data is now in: {run_mgr.run_dir}")
    print(f"   2. Logs are in: {run_mgr.logs_dir}")
    print(f"   3. Run with: python3 generate_emails_auto.py {cv_name}")
    print("\n" + "="*80 + "\n")
    
    return run_mgr


if __name__ == "__main__":
    import sys
    
    cv_name = "existing_cv"
    if len(sys.argv) > 1:
        cv_name = sys.argv[1]
    
    migrate_existing_data(cv_name)
