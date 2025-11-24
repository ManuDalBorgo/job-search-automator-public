import json
import csv
import os
import time
import pandas as pd
from pathlib import Path
from groq import Groq
from typing import List, Dict

# Configuration
CONFIG_PATH = "configs/CV_11_11_2025 (1) copy.json"
JOBS_CSV = "jobs.csv"
CV_TXT = "extracted_cvs/CV_11_11_2025 (1) copy.txt"

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def load_jobs(path):
    jobs = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)
    return jobs

def load_cv_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_jobs(jobs, filename):
    if not jobs:
        return
    
    fieldnames = [
        'suitability_score', 'suitability_reason',
        'title', 'company', 'location', 'description', 'salary', 
        'link', 'posted_date', 'job_id', 'source', 'query', 
        'region', 'search_date'
    ]
    
    # Ensure all fields exist
    for job in jobs:
        for field in fieldnames:
            if field not in job:
                job[field] = ""
                
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(jobs)
    print(f"💾 Saved {len(jobs)} jobs to {filename}")

def rank_jobs_standalone():
    print(f"🚀 Starting standalone ranking fix...")
    
    # Load config and init Groq
    config = load_config(CONFIG_PATH)
    groq_api_key = config['api_keys'].get('groq_api_key')
    
    if not groq_api_key:
        print("❌ No Groq API key found")
        return

    client = Groq(api_key=groq_api_key)
    
    # Load data
    jobs = load_jobs(JOBS_CSV)
    cv_text = load_cv_text(CV_TXT)
    cv_summary = cv_text[:3000]
    
    print(f"📊 Loaded {len(jobs)} jobs")
    
    ranked_jobs = []
    
    for i, job in enumerate(jobs, 1):
        # Skip if already ranked successfully (score > 0 and no error in reason)
        current_score = job.get('suitability_score', '0')
        current_reason = job.get('suitability_reason', '')
        
        try:
            score_val = int(float(current_score))
        except:
            score_val = 0
            
        if score_val > 0 and "Error" not in current_reason:
            # Keep existing ranking
            ranked_jobs.append(job)
            continue
            
        # Needs ranking
        time.sleep(5.0) # Increased base delay to 5 seconds
        
        retries = 3
        for attempt in range(retries):
            try:
                description = job.get('description', '')[:1000]
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
                
                completion = client.chat.completions.create(
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
                
                print(f"   [{i}/{len(jobs)}] Scored {score}/100: {title[:30]}...")
                break
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    wait_time = (attempt + 1) * 20 # Aggressive backoff: 20s, 40s, 60s
                    print(f"   ⚠️  Rate limit hit for job {i}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   ⚠️  Error ranking job {i} (Attempt {attempt+1}): {e}")
                    if attempt == retries - 1:
                        job['suitability_score'] = 0
                        job['suitability_reason'] = f"Error: {error_msg[:50]}"
                        ranked_jobs.append(job)

    # Sort
    ranked_jobs = sorted(ranked_jobs, key=lambda x: int(float(x.get('suitability_score', 0))), reverse=True)
    
    # Save
    save_jobs(ranked_jobs, JOBS_CSV)
    
    # Create Excel
    print("\n📊 Creating final Excel...")
    from create_final_excel import create_final_excel
    create_final_excel(JOBS_CSV, "final_ranked_jobs_fixed.xlsx")

if __name__ == "__main__":
    rank_jobs_standalone()
