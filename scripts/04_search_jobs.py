#!/usr/bin/env python3
"""
Job Search Module
Searches for relevant job listings using Google Jobs via SerpApi.

IMPROVEMENTS:
- Supports CV-specific configs from configs/ folder
- Command-line arguments for CV selection
- Better error handling and validation
- Integration with multi-CV workflow
- Progress tracking and detailed logging
"""

import json
import csv
import os
import sys
from datetime import datetime
import requests
import time
from typing import List, Dict, Optional
import argparse
from pathlib import Path
from groq import Groq


def get_project_root() -> Path:
    """
    Find the project root directory by looking for config.json or cvs/ folder.
    
    Returns:
        Path to the project root directory
    """
    # Start from the script's directory
    current = Path(__file__).resolve().parent
    
    # Go up directories looking for project markers
    for parent in [current] + list(current.parents):
        # Check for project markers
        if (parent / "config.json").exists() or (parent / "cvs").exists():
            return parent
    
    # If not found, return current working directory
    return Path.cwd()


# Change to project root directory
PROJECT_ROOT = get_project_root()
os.chdir(PROJECT_ROOT)



class JobSearcher:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the job searcher with a configuration file.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.config_path = config_path
        self.jobs = []
        self.serpapi_key = self.config['api_keys'].get('serpapi_key')
        self.groq_api_key = self.config['api_keys'].get('groq_api_key')
        
        # Initialize Groq client if key is available
        self.groq_client = None
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"⚠️  Failed to initialize Groq client: {e}")
        
        # Validate API key
        if not self.serpapi_key or self.serpapi_key == "YOUR_SERPAPI_KEY_HERE":
            print("⚠️  WARNING: SerpApi key not configured!")
            print("   Get a free key at: https://serpapi.com/")
            print("   Free tier: 100 searches/month\n")
    
    def search_with_serpapi(self, query: str, location: Optional[str] = None) -> List[Dict]:
        """
        Search using SerpApi (requires API key).
        
        Args:
            query: Job search query
            location: Optional location filter
            
        Returns:
            List of job dictionaries
        """
        if not self.serpapi_key or self.serpapi_key == "YOUR_SERPAPI_KEY_HERE":
            print(f"   ⚠️  Skipping '{query}' - No valid SerpApi key")
            return []
        
        url = "https://serpapi.com/search"
        all_jobs = []
        
        # Search for both World (default) and specified locations
        locations = [None]
        if location:
            locations.append(location)
        
        for loc in locations:
            params = {
                "engine": "google_jobs",
                "q": query,
                "api_key": self.serpapi_key,
                "num": 20  # Request more results
            }
            if loc:
                params["location"] = loc
            
            try:
                region_name = loc if loc else "WORLDWIDE"
                print(f"   🔎 Searching: '{query}' ({region_name})")
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    print(f"   ❌ API Error: {data['error']}")
                    continue
                
                jobs_results = data.get('jobs_results', [])
                
                for job in jobs_results:
                    # Extract salary if available
                    salary = job.get('detected_extensions', {}).get('salary', 'N/A')
                    
                    # Extract link from apply_options if share_url is missing
                    link = job.get('share_url')
                    if not link:
                        apply_options = job.get('apply_options', [])
                        if apply_options:
                            link = apply_options[0].get('link')
                    
                    # Get job highlights (requirements, responsibilities, etc.)
                    highlights = job.get('job_highlights', [])
                    description = job.get('description', 'No description available')
                    
                    # Add highlights to description if available
                    if highlights:
                        highlight_text = "\n\n".join([
                            f"{h.get('title', 'Details')}:\n" + "\n".join(h.get('items', []))
                            for h in highlights
                        ])
                        description = f"{description}\n\n{highlight_text}"
                    
                    all_jobs.append({
                        'title': job.get('title', 'N/A'),
                        'company': job.get('company_name', 'N/A'),
                        'location': job.get('location', 'N/A'),
                        'description': description,
                        'salary': salary,
                        'link': link if link else 'N/A',
                        'posted_date': job.get('detected_extensions', {}).get('posted_at', 'N/A'),
                        'job_id': job.get('job_id', 'N/A'),
                        'source': 'SerpApi',
                        'query': query,
                        'region': region_name,
                        'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                print(f"   ✅ Found {len(jobs_results)} jobs")
                
                # Rate limiting - be respectful to the API
                time.sleep(1)
                
            except requests.exceptions.Timeout:
                print(f"   ❌ Timeout error for '{query}' ({region_name})")
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request error for '{query}' ({region_name}): {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error for '{query}' ({region_name}): {e}")
                continue
        
        return all_jobs
    
    def search_all(self, max_results_per_query: Optional[int] = None) -> List[Dict]:
        """
        Run all configured job searches.
        
        Args:
            max_results_per_query: Maximum results per query (overrides config)
            
        Returns:
            List of all found jobs
        """
        queries = self.config['job_search']['queries']
        max_results = max_results_per_query or self.config['job_search'].get('max_results_per_query', 20)
        
        # Get location preferences from user profile
        locations = self.config.get('user_profile', {}).get('locations', [])
        primary_location = locations[0] if locations else None
        
        print(f"\n{'='*70}")
        print(f"🚀 JOB SEARCH")
        print(f"{'='*70}")
        print(f"Config: {os.path.basename(self.config_path)}")
        print(f"Queries: {len(queries)}")
        print(f"Max results per query: {max_results}")
        if primary_location:
            print(f"Primary location: {primary_location}")
        print(f"{'='*70}\n")
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Query: '{query}'")
            
            # Search with SerpApi
            jobs = self.search_with_serpapi(query, location=primary_location)
            
            # Limit results per query
            self.jobs.extend(jobs[:max_results])
            print()
        
        # Deduplicate jobs
        print("🔄 Deduplicating jobs...")
        unique_jobs = self._deduplicate_jobs(self.jobs)
        self.jobs = unique_jobs
        
        print(f"\n{'='*70}")
        print(f"🎉 SEARCH COMPLETE")
        print(f"{'='*70}")
        print(f"Total unique jobs found: {len(self.jobs)}")
        print(f"{'='*70}\n")
        
        return self.jobs
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Remove duplicate jobs based on link and (title, company) combination.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of unique jobs
        """
        unique_jobs = []
        seen_links = set()
        seen_keys = set()  # (title, company)
        
        for job in jobs:
            link = job.get('link')
            key = (job.get('title'), job.get('company'))
            
            # Skip if we've seen this link
            if link and link != 'N/A' and link in seen_links:
                continue
            
            # Skip if we've seen this title+company combo
            if key in seen_keys:
                continue
            
            # Add to unique jobs
            if link and link != 'N/A':
                seen_links.add(link)
            seen_keys.add(key)
            unique_jobs.append(job)
        
        removed = len(jobs) - len(unique_jobs)
        if removed > 0:
            print(f"   Removed {removed} duplicate(s)")
        
        return unique_jobs
    
    def _get_cv_text(self) -> str:
        """
        Retrieve the CV text for ranking.
        
        Returns:
            CV text string or empty string if not found
        """
        cv_name = self.config.get('cv', {}).get('name')
        if not cv_name:
            return ""
            
        # Try to find extracted text file
        txt_path = f"extracted_cvs/{cv_name}.txt"
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        
        return ""

    def rank_jobs(self) -> None:
        """
        Rank jobs based on suitability for the CV using AI.
        Updates self.jobs with 'suitability_score' and 'suitability_reason'.
        Sorts self.jobs by score descending.
        """
        if not self.groq_client:
            print("⚠️  Groq client not initialized. Skipping ranking.")
            return
            
        cv_text = self._get_cv_text()
        if not cv_text:
            print("⚠️  CV text not found. Skipping ranking.")
            return
            
        # Truncate CV text to avoid token limits (keep first 3000 chars)
        cv_summary = cv_text[:3000]
        
        print(f"\n🤖 Ranking {len(self.jobs)} jobs with AI (this may take a moment)...")
        
        ranked_jobs = []
        for i, job in enumerate(self.jobs, 1):
            # Add delay to avoid rate limits
            time.sleep(1.5) 
            
            retries = 3
            for attempt in range(retries):
                try:
                    # Prepare prompt
                    description = job.get('description', '')[:1000] # Truncate description
                    title = job.get('title', '')
                    company = job.get('company', '')
                    
                    prompt = f"""
                    Rate the suitability of this job for the candidate on a scale of 0 to 100.
                    
                    CANDIDATE CV SUMMARY:
                    {cv_summary}
                    
                    JOB DETAILS:
                    Title: {title}
                    Company: {company}
                    Description: {description}
                    
                    Return ONLY a JSON object with two keys:
                    1. "score": integer 0-100
                    2. "reason": short string (max 15 words) explaining why
                    """
                    
                    completion = self.groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a helpful career assistant. Output valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama-3.3-70b-versatile",
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    
                    result = json.loads(completion.choices[0].message.content)
                    score = result.get('score', 0)
                    reason = result.get('reason', 'No reason provided')
                    
                    job['suitability_score'] = score
                    job['suitability_reason'] = reason
                    ranked_jobs.append(job)
                    
                    # Progress indicator
                    print(f"   [{i}/{len(self.jobs)}] Scored {score}/100: {title[:30]}...")
                    break # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        wait_time = (attempt + 1) * 5 # Exponential backoff: 5s, 10s, 15s
                        print(f"   ⚠️  Rate limit hit for job {i}. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ⚠️  Error ranking job {i} (Attempt {attempt+1}): {e}")
                        if attempt == retries - 1:
                            job['suitability_score'] = 0
                            job['suitability_reason'] = f"Error: {error_msg[:50]}" # Save actual error
                            ranked_jobs.append(job)
        
        # Sort jobs by score descending
        self.jobs = sorted(ranked_jobs, key=lambda x: x.get('suitability_score', 0), reverse=True)
        print(f"✅ Ranked {len(self.jobs)} jobs by suitability\n")

    def save_to_csv(self, filename: str = "jobs.csv") -> None:
        """
        Save jobs to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        if not self.jobs:
            print("⚠️  No jobs to save.")
            return
        
        fieldnames = [
            'suitability_score', 'suitability_reason', # New fields first
            'title', 'company', 'location', 'description', 'salary', 
            'link', 'posted_date', 'job_id', 'source', 'query', 
            'region', 'search_date'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.jobs)
            
            print(f"💾 Saved {len(self.jobs)} jobs to {filename}")
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
            
    def save_to_excel(self, filename: str = "jobs.xlsx") -> None:
        """
        Save jobs to Excel file.
        
        Args:
            filename: Output Excel filename
        """
        if not self.jobs:
            return
            
        try:
            import pandas as pd
            df = pd.DataFrame(self.jobs)
            
            # Reorder columns if possible
            cols = [
                'suitability_score', 'suitability_reason', 
                'title', 'company', 'location', 'description', 'salary', 
                'link', 'posted_date', 'job_id', 'source', 'query', 
                'region', 'search_date'
            ]
            # Only keep columns that exist in the dataframe
            cols = [c for c in cols if c in df.columns]
            remaining = [c for c in df.columns if c not in cols]
            df = df[cols + remaining]
            
            df.to_excel(filename, index=False)
            print(f"💾 Saved {len(self.jobs)} jobs to {filename}")
        except ImportError:
            print("⚠️  pandas/openpyxl not installed. Skipping Excel export.")
        except Exception as e:
            print(f"❌ Error saving to Excel: {e}")
    
    def save_to_text_files(self, output_dir: str = "extracted_jobs", cv_name: Optional[str] = None) -> None:
        """
        Save each job as an individual text file for easy reading.
        Organizes by CV name if provided.
        
        Args:
            output_dir: Base directory for text files
            cv_name: Optional CV name to create subdirectory (e.g., "CV_11_11_2025 (1) copy")
        """
        if not self.jobs:
            print("⚠️  No jobs to save.")
            return
        
        # Determine the actual output directory
        if cv_name:
            # Create CV-specific subdirectory
            actual_output_dir = os.path.join(output_dir, cv_name)
        else:
            # Try to extract CV name from config
            cv_name_from_config = self.config.get('cv', {}).get('name')
            if cv_name_from_config:
                actual_output_dir = os.path.join(output_dir, cv_name_from_config)
            else:
                # Fallback to base directory with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                actual_output_dir = os.path.join(output_dir, f"jobs_{timestamp}")
        
        # Create output directory
        os.makedirs(actual_output_dir, exist_ok=True)
        
        print(f"\n📝 Saving jobs as text files to {actual_output_dir}/...")
        
        saved_count = 0
        for i, job in enumerate(self.jobs, 1):
            try:
                # Create a safe filename from job title and company
                title = job.get('title', 'Unknown')
                company = job.get('company', 'Unknown')
                
                # Clean filename (remove special characters)
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
                safe_company = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in company)
                
                # Truncate if too long
                safe_title = safe_title[:50].strip()
                safe_company = safe_company[:30].strip()
                
                # Create filename with index to ensure uniqueness
                filename = f"{i:03d}_{safe_title}_{safe_company}.txt"
                filepath = os.path.join(actual_output_dir, filename)
                
                # Format job details as text
                job_text = self._format_job_as_text(job, i)
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(job_text)
                
                saved_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error saving job {i}: {e}")
                continue
        
        print(f"✅ Saved {saved_count} job descriptions to {actual_output_dir}/")
        
        # Also save a summary file
        summary_path = os.path.join(actual_output_dir, "_SUMMARY.txt")
        self._save_summary_file(summary_path)
    
    def _save_summary_file(self, filepath: str) -> None:
        """
        Save a summary file with job titles and companies.
        
        Args:
            filepath: Path to save the summary file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("JOB SEARCH SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Total Jobs: {len(self.jobs)}\n")
                f.write(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # CV info if available
                cv_info = self.config.get('cv', {})
                if cv_info:
                    f.write(f"CV: {cv_info.get('name', 'N/A')}\n")
                
                f.write("\n" + "-" * 80 + "\n")
                f.write("JOB LIST:\n")
                f.write("-" * 80 + "\n\n")
                
                for i, job in enumerate(self.jobs, 1):
                    f.write(f"{i:03d}. {job.get('title', 'N/A')}\n")
                    f.write(f"     Company: {job.get('company', 'N/A')}\n")
                    f.write(f"     Location: {job.get('location', 'N/A')}\n")
                    f.write(f"     Query: {job.get('query', 'N/A')}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
            
            print(f"📄 Summary saved to {filepath}")
        except Exception as e:
            print(f"   ⚠️  Error saving summary: {e}")
    
    def _format_job_as_text(self, job: Dict, index: int) -> str:
        """
        Format a job dictionary as readable text.
        
        Args:
            job: Job dictionary
            index: Job index number
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"JOB #{index}")
        lines.append("=" * 80)
        lines.append("")
        
        # Basic info
        lines.append(f"TITLE: {job.get('title', 'N/A')}")
        lines.append(f"COMPANY: {job.get('company', 'N/A')}")
        lines.append(f"LOCATION: {job.get('location', 'N/A')}")
        lines.append(f"SALARY: {job.get('salary', 'N/A')}")
        lines.append(f"POSTED: {job.get('posted_date', 'N/A')}")
        
        # Suitability Score
        score = job.get('suitability_score')
        if score is not None:
            lines.append(f"MATCH SCORE: {score}/100")
            lines.append(f"MATCH REASON: {job.get('suitability_reason', 'N/A')}")
        
        lines.append("")
        
        # Link
        lines.append("APPLY LINK:")
        lines.append(job.get('link', 'N/A'))
        lines.append("")
        
        # Search metadata
        lines.append("SEARCH INFO:")
        lines.append(f"  Query: {job.get('query', 'N/A')}")
        lines.append(f"  Region: {job.get('region', 'N/A')}")
        lines.append(f"  Source: {job.get('source', 'N/A')}")
        lines.append(f"  Search Date: {job.get('search_date', 'N/A')}")
        lines.append(f"  Job ID: {job.get('job_id', 'N/A')}")
        lines.append("")
        
        # Description
        lines.append("-" * 80)
        lines.append("JOB DESCRIPTION:")
        lines.append("-" * 80)
        lines.append("")
        description = job.get('description', 'No description available')
        lines.append(description)
        lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

    
    def display_summary(self, limit: int = 10) -> None:
        """
        Display a summary of found jobs.
        
        Args:
            limit: Number of jobs to display
        """
        if not self.jobs:
            print("No jobs found.")
            return
        
        print("\n" + "="*80)
        print("JOB SEARCH SUMMARY")
        print("="*80)
        
        for i, job in enumerate(self.jobs[:limit], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job.get('salary', 'N/A')}")
            print(f"   Posted: {job.get('posted_date', 'N/A')}")
            link = job.get('link', 'N/A')
            if len(link) > 70:
                link = link[:70] + "..."
            print(f"   Link: {link}")
            print(f"   Source: {job['source']} | Query: '{job['query']}'")
        
        if len(self.jobs) > limit:
            print(f"\n... and {len(self.jobs) - limit} more jobs (see jobs.csv)")
        
        print("\n" + "="*80)


def find_cv_config(cv_name: Optional[str] = None) -> str:
    """
    Find the appropriate CV config file.
    
    Args:
        cv_name: Optional CV name to search for
        
    Returns:
        Path to the config file
    """
    # If CV name provided, look for it in configs/
    if cv_name:
        # Try exact match
        config_path = f"configs/{cv_name}.json"
        if os.path.exists(config_path):
            return config_path
        
        # Try with .json extension if not provided
        if not cv_name.endswith('.json'):
            config_path = f"configs/{cv_name}.json"
            if os.path.exists(config_path):
                return config_path
        
        print(f"⚠️  Config not found: configs/{cv_name}.json")
        print("   Available configs:")
        
        # List available configs
        if os.path.exists("configs"):
            configs = [f for f in os.listdir("configs") if f.endswith('.json')]
            for cfg in configs:
                print(f"   - {cfg}")
        
        sys.exit(1)
    
    # Default to config.json in root
    if os.path.exists("config.json"):
        return "config.json"
    
    print("❌ No config.json found in root directory")
    sys.exit(1)


def main():
    """Main function to run job search from command line."""
    parser = argparse.ArgumentParser(
        description="Search for jobs using CV-specific configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default config.json
  python3 scripts/search_jobs.py
  
  # Use specific CV config
  python3 scripts/search_jobs.py --cv "CV_11_11_2025 (1) copy"
  
  # Limit results per query
  python3 scripts/search_jobs.py --cv my_cv --max-results 10
  
  # Custom output file
  python3 scripts/search_jobs.py --output my_jobs.csv
        """
    )
    
    parser.add_argument(
        '--cv',
        type=str,
        help='CV name (looks for configs/CV_NAME.json)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to specific config file'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        help='Maximum results per query (overrides config)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='jobs.csv',
        help='Output CSV filename (default: jobs.csv)'
    )
    
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='Skip displaying job summary'
    )
    
    parser.add_argument(
        '--save-txt',
        action='store_true',
        help='Save jobs as individual text files in extracted_jobs/ folder'
    )
    
    parser.add_argument(
        '--txt-dir',
        type=str,
        default='extracted_jobs',
        help='Directory for text files (default: extracted_jobs)'
    )
    
    parser.add_argument(
        '--rank',
        action='store_true',
        help='Rank jobs using AI (requires Groq API key)'
    )
    
    args = parser.parse_args()
    
    # Determine config file to use
    if args.config:
        config_path = args.config
    elif args.cv:
        config_path = find_cv_config(args.cv)
    else:
        config_path = find_cv_config()
    
    print(f"📋 Using config: {config_path}\n")
    
    # Run job search
    try:
        searcher = JobSearcher(config_path)
        searcher.search_all(max_results_per_query=args.max_results)
        
        # Rank jobs if requested
        if args.rank:
            searcher.rank_jobs()
        
        searcher.save_to_csv(args.output)
        
        # Save as text files if requested
        if args.save_txt:
            searcher.save_to_text_files(args.txt_dir)
        
        if not args.no_summary:
            searcher.display_summary()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Search interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
