"""
Run Manager - Organizes job search runs by CV
Creates unique folders for each CV run with proper logging
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path


class RunManager:
    """Manages job search runs with unique folders per CV"""
    
    def __init__(self, cv_name=None, base_dir="runs"):
        """
        Initialize a new run or load existing one
        
        Args:
            cv_name: Name identifier for the CV (e.g., "john_doe", "data_scientist_cv")
            base_dir: Base directory for all runs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        if cv_name:
            # Create new run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_name = f"{cv_name}_{timestamp}"
            self.run_dir = self.base_dir / self.run_name
            self.run_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            self.jobs_dir = self.run_dir / "jobs"
            self.cover_letters_dir = self.run_dir / "generated_cover_letters"
            self.prompts_dir = self.run_dir / "ai_prompts"
            self.logs_dir = self.run_dir / "logs"
            
            for dir_path in [self.jobs_dir, self.cover_letters_dir, self.prompts_dir, self.logs_dir]:
                dir_path.mkdir(exist_ok=True)
            
            # Setup logging
            self._setup_logging()
            
            # Save run metadata
            self._save_metadata(cv_name)
            
            self.logger.info(f"Created new run: {self.run_name}")
        else:
            # Load most recent run
            runs = sorted([d for d in self.base_dir.iterdir() if d.is_dir()], 
                         key=lambda x: x.stat().st_mtime, reverse=True)
            if runs:
                self.run_dir = runs[0]
                self.run_name = self.run_dir.name
                self._load_directories()
                self._setup_logging()
                self.logger.info(f"Loaded existing run: {self.run_name}")
            else:
                raise ValueError("No existing runs found. Please specify a cv_name to create a new run.")
    
    def _setup_logging(self):
        """Setup logging for this run"""
        log_file = self.logs_dir / f"run_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create logger
        self.logger = logging.getLogger(f"JobSearch_{self.run_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler (detailed)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler (less verbose)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _load_directories(self):
        """Load directory paths for existing run"""
        self.jobs_dir = self.run_dir / "jobs"
        self.cover_letters_dir = self.run_dir / "generated_cover_letters"
        self.prompts_dir = self.run_dir / "ai_prompts"
        self.logs_dir = self.run_dir / "logs"
    
    def _save_metadata(self, cv_name):
        """Save run metadata"""
        metadata = {
            "cv_name": cv_name,
            "run_name": self.run_name,
            "created_at": datetime.now().isoformat(),
            "run_dir": str(self.run_dir),
            "status": "active"
        }
        
        metadata_file = self.run_dir / "run_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_jobs_csv_path(self):
        """Get path for jobs CSV file"""
        return self.jobs_dir / "jobs.csv"
    
    def get_cover_letters_dir(self):
        """Get path for generated cover letters directory"""
        return str(self.cover_letters_dir)
    
    def get_prompts_dir(self):
        """Get path for AI prompts directory"""
        return str(self.prompts_dir)
    
    def get_cv_path(self):
        """Get path where CV should be stored"""
        return self.run_dir / "cv.pdf"
    
    def copy_cv(self, cv_source_path):
        """Copy CV to run directory"""
        import shutil
        cv_dest = self.get_cv_path()
        shutil.copy2(cv_source_path, cv_dest)
        self.logger.info(f"Copied CV from {cv_source_path} to {cv_dest}")
        return cv_dest
    
    def update_status(self, status, stats=None):
        """Update run status and statistics"""
        metadata_file = self.run_dir / "run_metadata.json"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metadata["status"] = status
        metadata["updated_at"] = datetime.now().isoformat()
        
        if stats:
            metadata["stats"] = stats
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Updated run status to: {status}")
    
    def get_summary(self):
        """Get summary of this run"""
        metadata_file = self.run_dir / "run_metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Count files
        jobs_csv = self.get_jobs_csv_path()
        num_jobs = 0
        if jobs_csv.exists():
            try:
                # Use pandas to properly parse CSV (handles newlines in descriptions)
                import pandas as pd
                df = pd.read_csv(jobs_csv)
                num_jobs = len(df)
            except Exception as e:
                # Fallback to line counting if pandas fails
                self.logger.warning(f"Could not parse CSV with pandas: {e}. Using line count.")
                with open(jobs_csv, 'r') as f:
                    num_jobs = sum(1 for line in f) - 1  # Subtract header
        
        num_cover_letters = len(list(self.cover_letters_dir.glob("*.txt")))
        num_prompts = len(list(self.prompts_dir.glob("*.txt")))
        
        summary = {
            "run_name": self.run_name,
            "run_dir": str(self.run_dir),
            "metadata": metadata,
            "counts": {
                "jobs": num_jobs,
                "cover_letters_generated": num_cover_letters,
                "prompts_created": num_prompts
            }
        }
        
        return summary
    
    @staticmethod
    def list_all_runs(base_dir="runs"):
        """List all available runs"""
        base_path = Path(base_dir)
        if not base_path.exists():
            return []
        
        runs = []
        for run_dir in sorted(base_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if run_dir.is_dir():
                metadata_file = run_dir / "run_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    runs.append({
                        "run_name": run_dir.name,
                        "cv_name": metadata.get("cv_name", "unknown"),
                        "created_at": metadata.get("created_at", "unknown"),
                        "status": metadata.get("status", "unknown")
                    })
        
        return runs


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*80)
    print("RUN MANAGER - Example Usage")
    print("="*80 + "\n")
    
    # List existing runs
    print("Existing runs:")
    runs = RunManager.list_all_runs()
    if runs:
        for run in runs:
            print(f"  - {run['run_name']} (CV: {run['cv_name']}, Status: {run['status']})")
    else:
        print("  No runs found")
    
    print("\n" + "="*80 + "\n")
