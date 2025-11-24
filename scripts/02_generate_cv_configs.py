#!/usr/bin/env python3
"""
Generate unique JSON configuration files for every CV in the cvs/ folder.
Uses Llama 3.3 (via Groq) to extract profile info and generate tailored job search queries.

IMPROVEMENTS:
- Uses extracted .txt files for faster processing
- Better prompt engineering with examples
- Validation of extracted data
- Enhanced error handling
- More diverse query generation (15-20 queries)
- Summary report of extraction
"""

import json
import os
import glob
from pathlib import Path
from groq import Groq
import sys
from typing import Dict, Optional, List

# Add current directory to path to import extract_cv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from extract_cv import extract_text_from_pdf
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.getcwd(), 'scripts'))
    from extract_cv import extract_text_from_pdf


def load_base_config(config_path="config.json") -> Dict:
    """Load the base configuration file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_cv_text(cv_path: str) -> Optional[str]:
    """
    Get CV text, preferring extracted .txt files over PDF extraction.
    
    Args:
        cv_path: Path to the CV PDF file
        
    Returns:
        Extracted text or None if extraction fails
    """
    cv_filename = os.path.basename(cv_path)
    cv_name = os.path.splitext(cv_filename)[0]
    
    # First, try to use extracted .txt file
    txt_path = f"extracted_cvs/{cv_name}.txt"
    if os.path.exists(txt_path):
        print(f"   📝 Using extracted text file: {txt_path}")
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"   ⚠️  Error reading extracted text: {e}")
    
    # Fallback: Extract from PDF
    print(f"   🔄 Extracting text from PDF...")
    try:
        cv_text = extract_text_from_pdf(cv_path)
        
        # Save extracted text for future use
        os.makedirs("extracted_cvs", exist_ok=True)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(cv_text)
        print(f"   💾 Saved extracted text to: {txt_path}")
        
        return cv_text
    except Exception as e:
        print(f"   ❌ Error extracting from PDF: {e}")
        return None


def validate_config_data(data: Dict, cv_filename: str) -> bool:
    """
    Validate that the generated config has all required fields and reasonable data.
    
    Args:
        data: Generated configuration data
        cv_filename: Name of the CV file for error reporting
        
    Returns:
        True if valid, False otherwise
    """
    issues = []
    
    # Check required top-level keys
    if 'user_profile' not in data:
        issues.append("Missing 'user_profile' section")
    if 'job_search' not in data:
        issues.append("Missing 'job_search' section")
    
    # Validate user_profile
    if 'user_profile' in data:
        profile = data['user_profile']
        required_fields = ['name', 'current_title', 'core_skills', 'target_roles', 'locations']
        
        for field in required_fields:
            if field not in profile or not profile[field]:
                issues.append(f"Missing or empty user_profile.{field}")
        
        # Check for placeholder/generic data
        if 'name' in profile:
            if len(profile['name']) < 3 or profile['name'].lower() in ['n/a', 'name', 'full name']:
                issues.append(f"Invalid name: '{profile['name']}'")
        
        if 'core_skills' in profile:
            if not isinstance(profile['core_skills'], list) or len(profile['core_skills']) < 3:
                issues.append(f"Insufficient core_skills (need at least 3)")
    
    # Validate job_search
    if 'job_search' in data:
        search = data['job_search']
        
        if 'queries' not in search or not isinstance(search['queries'], list):
            issues.append("Missing or invalid job_search.queries")
        elif len(search['queries']) < 10:
            issues.append(f"Too few search queries ({len(search['queries'])}, expected 15-20)")
    
    # Report issues
    if issues:
        print(f"\n   ⚠️  Validation issues for {cv_filename}:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    
    return True


def generate_config_for_cv(cv_path: str, base_config: Dict, groq_client: Groq) -> Optional[Dict]:
    """
    Generate a configuration file for a single CV.
    
    Args:
        cv_path: Path to the CV PDF file
        base_config: Base configuration to extend
        groq_client: Groq API client
        
    Returns:
        Generated configuration dict or None if generation fails
    """
    cv_filename = os.path.basename(cv_path)
    cv_name = os.path.splitext(cv_filename)[0]
    
    print(f"\n{'='*70}")
    print(f"📄 Processing CV: {cv_filename}")
    print(f"{'='*70}")
    
    # 1. Get CV text (from .txt file or extract from PDF)
    cv_text = get_cv_text(cv_path)
    if not cv_text or len(cv_text) < 100:
        print(f"❌ Could not extract sufficient text from {cv_filename}. Skipping.")
        return None
    
    print(f"   ✅ Extracted {len(cv_text)} characters")

    # 2. Create enhanced prompt for Llama
    prompt = f"""You are an expert CV analyzer and career advisor. Your task is to extract structured information from a CV and generate strategic job search queries.

IMPORTANT INSTRUCTIONS:
1. Extract EXACT information from the CV - do not use placeholders or generic terms
2. Be specific and detailed in all fields
3. Generate 15-20 diverse, strategic job search queries
4. Output ONLY valid JSON, no additional text

REQUIRED JSON STRUCTURE:
{{
    "user_profile": {{
        "name": "Extract the FULL NAME exactly as shown (including titles like Dr., PhD, etc.)",
        "current_title": "Most recent job title or 'Seeking Opportunities' if between jobs",
        "current_company": "Current/most recent company name or 'N/A'",
        "experience_years": "Total years or level (e.g., '8', 'Senior', 'Lead')",
        "education": [
            "List ALL degrees with institution names, e.g., 'PhD Economics - University College London'",
            "MBA - London Business School",
            "Include executive education if relevant"
        ],
        "core_skills": [
            "List 8-15 specific technical and professional skills",
            "Include programming languages, tools, methodologies",
            "Include domain expertise"
        ],
        "key_achievements": [
            "3-5 specific, quantifiable achievements from the CV",
            "Include project names, impact, technologies used"
        ],
        "target_roles": [
            "5-8 specific job titles this person would be qualified for",
            "Based on their experience and skills"
        ],
        "locations": [
            "List specific cities/countries mentioned",
            "Include 'Remote' if applicable",
            "Include regions (e.g., 'Europe', 'UK')"
        ],
        "industries": [
            "List 4-6 relevant industries based on experience",
            "Be specific (e.g., 'Legal Tech', 'Energy Regulation', not just 'Technology')"
        ],
        "experience_level": "Junior/Mid/Senior/Lead/Executive"
    }},
    "job_search": {{
        "queries": [
            "Generate 15-20 strategic search queries",
            "Mix these patterns:",
            "- 'Role Title + Location' (e.g., 'Senior Data Scientist London')",
            "- 'Role + Key Skill' (e.g., 'Data Scientist NLP')",
            "- 'Role + Industry' (e.g., 'Data Scientist Legal Tech')",
            "- 'Senior/Lead + Role + Remote' (e.g., 'Lead ML Engineer Remote')",
            "- 'Specific specialization' (e.g., 'LLMOps Engineer')",
            "- 'Role + Technology' (e.g., 'Data Scientist Azure')",
            "Use actual skills, locations, and roles from the CV"
        ],
        "max_results_per_query": 20
    }}
}}

EXAMPLE OUTPUT (for reference - adapt to the actual CV):
{{
    "user_profile": {{
        "name": "Dr. Jane Smith",
        "current_title": "Lead Data Scientist",
        "current_company": "Tech Corp",
        "experience_years": "10",
        "education": [
            "PhD Computer Science - Stanford University",
            "MSc Machine Learning - MIT"
        ],
        "core_skills": ["Python", "TensorFlow", "NLP", "Deep Learning", "Azure", "MLOps"],
        "key_achievements": [
            "Led ML pipeline serving 10M+ users",
            "Published 5 papers in top-tier conferences"
        ],
        "target_roles": ["Senior Data Scientist", "ML Engineering Manager", "AI Research Scientist"],
        "locations": ["San Francisco", "Remote", "USA"],
        "industries": ["Technology", "AI/ML", "Healthcare AI"],
        "experience_level": "Senior"
    }},
    "job_search": {{
        "queries": [
            "Senior Data Scientist San Francisco",
            "Lead Data Scientist Remote",
            "ML Engineer NLP",
            "Data Scientist Healthcare AI"
        ],
        "max_results_per_query": 20
    }}
}}

Now analyze this CV and output the JSON:

CV TEXT:
{cv_text}
"""

    try:
        print(f"   🤖 Calling Groq API (llama-3.3-70b-versatile)...")
        
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional CV analyzer. Output only valid JSON with accurate, specific information extracted from the CV. Never use placeholders or generic terms."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",  # Using the most capable model
            temperature=0.3,  # Slightly higher for more creative query generation
            max_tokens=4000,  # Ensure we get complete responses
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        generated_data = json.loads(response_content)
        
        print(f"   ✅ Received response from API")
        
        # 3. Validate the generated data
        if not validate_config_data(generated_data, cv_filename):
            print(f"   ⚠️  Generated config has validation issues, but continuing...")
        
        # 4. Construct full config
        new_config = base_config.copy()
        
        # Update CV info with proper path handling
        new_config['cv'] = {
            "name": cv_name,
            "file_path": cv_path
        }
        
        # Update Profile & Search (keep API keys from base)
        new_config['user_profile'] = generated_data.get('user_profile', {})
        new_config['job_search'] = generated_data.get('job_search', {})
        
        # Ensure max_results is set
        if 'max_results_per_query' not in new_config['job_search']:
            new_config['job_search']['max_results_per_query'] = 20
        
        # 5. Print summary
        print(f"\n   📊 EXTRACTION SUMMARY:")
        print(f"      Name: {new_config['user_profile'].get('name', 'N/A')}")
        print(f"      Title: {new_config['user_profile'].get('current_title', 'N/A')}")
        print(f"      Skills: {len(new_config['user_profile'].get('core_skills', []))} skills")
        print(f"      Target Roles: {len(new_config['user_profile'].get('target_roles', []))} roles")
        print(f"      Search Queries: {len(new_config['job_search'].get('queries', []))} queries")
        
        return new_config

    except json.JSONDecodeError as e:
        print(f"   ❌ Error parsing JSON response: {e}")
        print(f"   Response was: {response_content[:500]}...")
        return None
    except Exception as e:
        print(f"   ❌ Error generating config: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to process all CVs and generate configs."""
    print("\n" + "="*70)
    print("🚀 CV CONFIG GENERATOR")
    print("="*70)
    
    # Load base config
    try:
        base_config = load_base_config()
    except Exception as e:
        print(f"❌ Error loading config.json: {e}")
        return
    
    groq_api_key = base_config['api_keys'].get('groq_api_key')
    
    if not groq_api_key:
        print("❌ Groq API key not found in config.json")
        return

    client = Groq(api_key=groq_api_key)
    
    # Create necessary directories
    os.makedirs("configs", exist_ok=True)
    os.makedirs("extracted_cvs", exist_ok=True)
    
    # Find all PDFs
    cv_files = glob.glob("cvs/*.pdf")
    
    if not cv_files:
        print("❌ No PDF files found in cvs/ folder")
        return
    
    print(f"\n🔍 Found {len(cv_files)} CV(s) in cvs/ folder")
    
    # Process each CV
    successful = 0
    failed = 0
    
    for i, cv_path in enumerate(cv_files, 1):
        print(f"\n[{i}/{len(cv_files)}]")
        
        config_data = generate_config_for_cv(cv_path, base_config, client)
        
        if config_data:
            cv_name = config_data['cv']['name']
            output_path = f"configs/{cv_name}.json"
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                
                print(f"   ✅ Saved config to: {output_path}")
                successful += 1
            except Exception as e:
                print(f"   ❌ Error saving config: {e}")
                failed += 1
        else:
            failed += 1
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"📈 FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Configs saved to: configs/")
    print(f"📝 Extracted texts in: extracted_cvs/")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
