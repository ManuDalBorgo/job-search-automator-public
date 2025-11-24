import sys
import os
import json
import csv
import time
import requests
from bs4 import BeautifulSoup
from groq import Groq
from datetime import datetime

# Configuration
CONFIG_PATH = "configs/CV_11_11_2025 (1) copy.json"
JOBS_CSV = "jobs.csv"
CV_TXT = "extracted_cvs/CV_11_11_2025 (1) copy.txt"

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def load_cv_text(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def extract_text_from_url(url):
    """Extract main text content from a URL"""
    print(f"🌐 Fetching URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return None

def parse_job_with_ai(client, text, url):
    """Use AI to extract structured job data from raw text"""
    print("🤖 Parsing job details with AI...")
    
    prompt = f"""
    Extract the following job details from the text below.
    Return a JSON object with these exact keys:
    - title
    - company
    - location
    - description (summarize the key parts, max 300 words)
    - salary (if found, else "N/A")
    - posted_date (if found, else "N/A")
    
    TEXT CONTENT:
    {text[:10000]}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful data extraction assistant. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        
        # Add metadata
        data['link'] = url
        data['source'] = "Manual URL"
        data['search_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['job_id'] = f"manual_{int(time.time())}"
        data['query'] = "Manual Addition"
        
        # Determine region
        loc = data.get('location', '').lower()
        if any(x in loc for x in ['uk', 'united kingdom', 'london', 'england', 'scotland', 'wales']):
            data['region'] = "United Kingdom"
        else:
            data['region'] = "WORLDWIDE"
            
        return data
    except Exception as e:
        print(f"❌ Error parsing job: {e}")
        return None

def rank_job(client, job, cv_text):
    """Rank the job against the CV"""
    print("⚖️  Ranking job suitability...")
    
    cv_summary = cv_text[:3000]
    
    prompt = f"""
    Rate the suitability of this job for the candidate on a scale of 0 to 100.
    
    CANDIDATE CV SUMMARY:
    {cv_summary}
    
    JOB DETAILS:
    Title: {job['title']}
    Company: {job['company']}
    Description: {job['description']}
    
    Return ONLY a JSON object with two keys:
    1. "score": integer 0-100
    2. "reason": short string (max 15 words) explaining why
    """
    
    try:
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
        job['suitability_score'] = result.get('score', 0)
        job['suitability_reason'] = result.get('reason', 'No reason provided')
        
        print(f"✅ Scored: {job['suitability_score']}/100 ({job['suitability_reason']})")
        return job
    except Exception as e:
        print(f"❌ Error ranking job: {e}")
        job['suitability_score'] = 0
        job['suitability_reason'] = "Error during ranking"
        return job

def append_to_csv(job, filename):
    """Append the new job to the CSV file"""
    file_exists = os.path.isfile(filename)
    
    fieldnames = [
        'suitability_score', 'suitability_reason',
        'title', 'company', 'location', 'description', 'salary', 
        'link', 'posted_date', 'job_id', 'source', 'query', 
        'region', 'search_date'
    ]
    
    # Ensure all fields exist
    for field in fieldnames:
        if field not in job:
            job[field] = ""
            
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        writer.writerow(job)
    
    print(f"💾 Added job to {filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_job_from_url.py <URL>")
        return
        
    url = sys.argv[1]
    
    # Load config and init Groq
    config = load_config(CONFIG_PATH)
    groq_api_key = config['api_keys'].get('groq_api_key')
    
    if not groq_api_key:
        print("❌ No Groq API key found")
        return

    client = Groq(api_key=groq_api_key)
    
    # 1. Extract Text
    text = extract_text_from_url(url)
    if not text:
        return
        
    # 2. Parse Job
    job = parse_job_with_ai(client, text, url)
    if not job:
        return
        
    print(f"\n📄 Extracted: {job['title']} at {job['company']}")
    print(f"📍 Location: {job['location']}")
    
    # 3. Rank Job
    cv_text = load_cv_text(CV_TXT)
    job = rank_job(client, job, cv_text)
    
    # 4. Save
    append_to_csv(job, JOBS_CSV)
    
    # 5. Update Excel
    print("\n📊 Updating Excel report...")
    from create_final_excel import create_final_excel
    create_final_excel(JOBS_CSV, "final_ranked_jobs.xlsx")

if __name__ == "__main__":
    main()
