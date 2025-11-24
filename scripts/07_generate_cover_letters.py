"""
Automated Cover Letter Generator using Google Gemini API and Groq
Generates cover letters using Gemini, Judges with Groq (Llama 3), and Refines with Gemini.
Now with automatic fallback to OpenRouter, Together AI, and Hugging Face when rate limits are hit.
"""

import json
import csv
import os
import requests
import time
from pathlib import Path
from groq import Groq
from generate_cover_letter_prompt import CoverLetterPromptGenerator


class GeminiCoverLetterGenerator:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Get primary API keys
        self.gemini_api_key = self.config['api_keys'].get('gemini_api_key')
        if not self.gemini_api_key or self.gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
            raise ValueError("Gemini API key not configured in config.json")
            
        self.groq_api_key = self.config['api_keys'].get('groq_api_key')
        if not self.groq_api_key or self.groq_api_key == "YOUR_GROQ_API_KEY_HERE":
            print("⚠️  Groq API key not found. AI Judge will use fallback providers.", flush=True)
            self.groq_client = None
        else:
            self.groq_client = Groq(api_key=self.groq_api_key)
        
        # Get fallback API keys
        self.openrouter_api_key = self.config['api_keys'].get('openrouter_api_key')
        self.together_api_key = self.config['api_keys'].get('together_api_key')
        self.huggingface_api_key = self.config['api_keys'].get('huggingface_api_key')
        
        # Fallback configuration
        self.fallback_config = self.config.get('fallback_models', {})
        
        # API endpoints
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.together_url = "https://api.together.xyz/v1/chat/completions"
        self.huggingface_url = "https://router.huggingface.co/models/{model}"
        
        # Track which providers are working
        self.gemini_available = True
        self.groq_available = True
        
        # Initialize prompt generator
        self.prompt_generator = CoverLetterPromptGenerator(config_path)
    
    
    def _call_openrouter_api(self, prompt, model="meta-llama/llama-3.1-8b-instruct:free", temperature=0.7):
        """Fallback method to call OpenRouter API"""
        if not self.openrouter_api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/job-search-automator",  # Optional
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(self.openrouter_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"⚠️  OpenRouter API Error: {response.status_code}", flush=True)
                return None
        except Exception as e:
            print(f"⚠️  OpenRouter API Exception: {e}", flush=True)
            return None
    
    def _call_together_api(self, prompt, model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", temperature=0.7):
        """Fallback method to call Together AI API"""
        if not self.together_api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.together_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(self.together_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"⚠️  Together AI API Error: {response.status_code}", flush=True)
                return None
        except Exception as e:
            print(f"⚠️  Together AI API Exception: {e}", flush=True)
            return None
    
    def _call_huggingface_api(self, prompt, model="meta-llama/Meta-Llama-3-8B-Instruct", temperature=0.7):
        """Fallback method to call Hugging Face Inference API"""
        if not self.huggingface_api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": 1000,
                    "return_full_text": False
                }
            }
            
            url = self.huggingface_url.format(model=model)
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                return str(result)
            else:
                print(f"⚠️  Hugging Face API Error: {response.status_code}", flush=True)
                return None
        except Exception as e:
            print(f"⚠️  Hugging Face API Exception: {e}", flush=True)
            return None
    
    def _call_gemini_api(self, prompt, model="gemini-2.0-flash", temperature=0.7):
        """Helper method to call Gemini API with automatic fallback to alternative providers"""
        # Try Gemini first if available
        if self.gemini_available:
            url = self.api_url.format(model=model)
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 1000,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            try:
                response = requests.post(
                    f"{url}?key={self.gemini_api_key}",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                elif response.status_code == 429:
                    print(f"⚠️  Gemini API Quota Exceeded (429). Trying fallback providers...", flush=True)
                    self.gemini_available = False  # Mark as unavailable for this session
                else:
                    print(f"⚠️  Gemini API Error: {response.status_code}. Trying fallback...", flush=True)
                    self.gemini_available = False
            except Exception as e:
                print(f"⚠️  Gemini API Exception: {e}. Trying fallback...", flush=True)
                self.gemini_available = False
        
        # Try fallbacks in order
        fallback_gemini = self.fallback_config.get('gemini_fallback', {})
        if fallback_gemini.get('enabled', True):
            # Try OpenRouter
            if self.openrouter_api_key:
                print("    🔄 Using OpenRouter fallback...", flush=True)
                result = self._call_openrouter_api(
                    prompt, 
                    model=fallback_gemini.get('model', 'meta-llama/llama-3.1-8b-instruct:free'),
                    temperature=temperature
                )
                if result:
                    return result
            
            # Try Hugging Face
            if self.huggingface_api_key:
                print("    🔄 Using Hugging Face fallback...", flush=True)
                result = self._call_huggingface_api(prompt, temperature=temperature)
                if result:
                    return result
        
        print(f"❌ All Gemini fallback providers failed.", flush=True)
        return None


    def _call_groq_api(self, prompt, model="llama-3.3-70b-instruct", temperature=0.1):
        """Helper method to call Groq API with automatic fallback to alternative providers"""
        # Try Groq first if available
        if self.groq_client and self.groq_available:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model,
                    temperature=temperature,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"⚠️  Groq API Rate Limit. Trying fallback providers...", flush=True)
                else:
                    print(f"⚠️  Groq API Error: {e}. Trying fallback...", flush=True)
                self.groq_available = False
        
        # Try fallbacks in order
        fallback_groq = self.fallback_config.get('groq_fallback', {})
        if fallback_groq.get('enabled', True):
            # Try Together AI
            if self.together_api_key:
                print("    🔄 Using Together AI fallback for Judge...", flush=True)
                result = self._call_together_api(
                    prompt,
                    model=fallback_groq.get('model', 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo'),
                    temperature=temperature
                )
                if result:
                    return result
            
            # Try Hugging Face
            if self.huggingface_api_key:
                print("    🔄 Using Hugging Face fallback for Judge...", flush=True)
                result = self._call_huggingface_api(prompt, temperature=temperature)
                if result:
                    return result
        
        print(f"⚠️  All Groq fallback providers failed. Skipping judge step.", flush=True)
        return None


    def _judge_content(self, content, criteria):
        """Ask Groq (Llama 3) to judge the content against criteria"""
        judge_prompt = f"""You are a strict AI Quality Assurance Judge.
Your task is to review the following cover letter draft against a set of strict criteria.

## CRITERIA TO CHECK:
{criteria}

## COVER LETTER DRAFT:
{content}

## TASK:
Evaluate if the cover letter meets ALL the criteria.
If it fails ANY check, it is a FAIL.

Respond with this exact JSON format:
{{
  "status": "PASS" or "FAIL",
  "feedback": "If FAIL, list specific violations. If PASS, write 'All checks passed'."
}}
"""
        # Use Groq if available, otherwise fallback to Gemini (or skip)
        if self.groq_client:
            response = self._call_groq_api(judge_prompt, model="llama-3.3-70b-versatile")
        else:
            print("⚠️  Groq not configured, skipping AI Judge.", flush=True)
            return {"status": "PASS", "feedback": "Judge skipped (Groq not configured)."}

        if not response:
            return {"status": "PASS", "feedback": "Judge failed to respond, skipping check."}
            
        try:
            # Clean markdown formatting if present
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            # Sometimes models add extra text, try to find the JSON object
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                cleaned_response = cleaned_response[start_idx:end_idx]
                
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            print(f"⚠️  Could not parse Judge response: {response}", flush=True)
            return {"status": "PASS", "feedback": "Judge response parse error, skipping check."}

    def generate_cover_letter_with_gemini(self, job, model="gemini-2.0-flash"):
        """Generate cover letter using Gemini API with separate AI Judge step (Groq)"""
        # 1. Generate Draft (Gemini Flash 2.0)
        prompt = self.prompt_generator.generate_job_application_prompt(job, include_judge=False)
        draft = self._call_gemini_api(prompt, model)
        
        if not draft:
            return None
            
        # 2. Judge (Groq Llama 3.1-70B)
        criteria = self.prompt_generator.get_job_judge_instructions()
        judgment = self._judge_content(draft, criteria)
        
        if judgment.get('status') == 'PASS':
            return draft
            
        # 3. Refine (Gemini Flash 2.0 / 2.5)
        print(f"    ⚠️  AI Judge (Groq) flagged issues: {judgment.get('feedback')}", flush=True)
        print(f"    🔄 Refining cover letter...", flush=True)
        
        refine_prompt = f"""You are a professional cover letter writer.
Here is a draft cover letter you wrote:
{draft}

The Quality Assurance team found these issues:
{judgment.get('feedback')}

Please rewrite the cover letter to fix these issues while maintaining the original tone and content.
Ensure you strictly follow the original style guidelines.
"""
        refined_cover_letter = self._call_gemini_api(refine_prompt, model)
        return refined_cover_letter if refined_cover_letter else draft
    
    def generate_all_job_cover_letters(self, jobs_csv="jobs.csv", output_dir="generated_cover_letters", model="gemini-2.0-flash", max_jobs=None):
        """
        Generate cover letters for all jobs using Gemini API
        
        Args:
            jobs_csv: Path to jobs CSV file
            output_dir: Directory to save generated cover letters
            model: Gemini model to use
            max_jobs: Maximum number of jobs to process (None = all jobs)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        with open(jobs_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
        
        # Limit number of jobs if specified
        if max_jobs:
            jobs = jobs[:max_jobs]
            print(f"\n🤖 Generating {len(jobs)} cover letters (limited to first {max_jobs}) using Gemini API ({model}) + Groq Judge...")
        else:
            print(f"\n🤖 Generating {len(jobs)} cover letters using Gemini API ({model}) + Groq Judge...")
        
        print(f"⏳ This will take approximately {len(jobs) * 5 / 60:.1f} minutes...\n")
        
        successful = 0
        failed = 0
        
        for i, job in enumerate(jobs, 1):
            print(f"📧 [{i}/{len(jobs)}] Generating cover letter for {job['company']}...", end=" ", flush=True)
            
            cover_letter = self.generate_cover_letter_with_gemini(job, model=model)
            
            if cover_letter == "QUOTA_EXCEEDED":
                print("\n🛑 Stopping due to API quota limit. Resume later.", flush=True)
                break
                
            if cover_letter:
                # Create safe filename
                safe_company = "".join(c for c in job['company'] if c.isalnum() or c in (' ', '-', '_'))[:50]
                filename = f"{output_dir}/job_{i:03d}_{safe_company}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(cover_letter)
                
                print("✅", flush=True)
                successful += 1
            else:
                print("❌", flush=True)
                failed += 1
            
            # Rate limiting: Free tier allows 15 requests/minute
            # Wait 5 seconds between requests to stay under limit
            if i < len(jobs):
                time.sleep(5)
        
        print(f"\n✅ Successfully generated {successful} cover letters")
        if failed > 0:
            print(f"❌ Failed to generate {failed} cover letters")
        print(f"📁 Cover letters saved in {output_dir}/\n")


def main(cv_name=None):
    """Main function to generate all cover letters automatically
    
    Args:
        cv_name: Optional CV identifier for organizing runs
    """
    import sys
    from run_manager import RunManager
    
    print("\n" + "="*80)
    print(" "*17 + "AUTOMATED COVER LETTER GENERATOR")
    print(" "*15 + "Gemini Flash 2.0 (Draft) -> Groq Llama 3 (Judge) -> Gemini (Refine)")
    print("="*80 + "\n")
    
    # Parse command line arguments
    if len(sys.argv) > 1 and not cv_name:
        cv_name = sys.argv[1]
    
    try:
        # Initialize or load run
        if cv_name:
            print(f"📁 Creating new run for CV: {cv_name}")
            run_mgr = RunManager(cv_name=cv_name)
        else:
            print("📁 Loading most recent run...")
            try:
                run_mgr = RunManager()
            except ValueError:
                print("\n⚠️  No existing runs found.")
                print("Please specify a CV name: python3 generate_emails_auto.py <cv_name>")
                print("Example: python3 generate_emails_auto.py john_doe\n")
                return
        
        logger = run_mgr.logger
        logger.info("="*80)
        logger.info("Starting cover letter generation process")
        logger.info("="*80)
        
        print(f"📂 Run directory: {run_mgr.run_dir}")
        print(f"📧 Cover letters will be saved to: {run_mgr.cover_letters_dir}\n")
        
        generator = GeminiCoverLetterGenerator()
        
        # Choose model
        model = "gemini-2.0-flash"
        
        logger.info(f"Using model: {model}")
        print(f"🔧 Using model: {model}")
        print(f"💰 Estimated cost: FREE (Gemini Free Tier + Groq Free Tier)\n")
        
        # Generate cover letters for jobs
        # Check root jobs.csv first (master file)
        root_jobs_csv = Path("jobs.csv")
        run_jobs_csv = run_mgr.get_jobs_csv_path()
        
        target_csv = None
        if root_jobs_csv.exists():
            target_csv = str(root_jobs_csv)
            logger.info(f"Using root jobs CSV: {target_csv}")
        elif run_jobs_csv.exists():
            target_csv = str(run_jobs_csv)
            logger.info(f"Using run jobs CSV: {target_csv}")
            
        if target_csv:
            # Process only first 100 jobs (change this number as needed)
            generator.generate_all_job_cover_letters(
                jobs_csv=target_csv,
                output_dir=run_mgr.get_cover_letters_dir(),
                model=model,
                max_jobs=100
            )
            
            # Update run status
            summary = run_mgr.get_summary()
            run_mgr.update_status("completed", stats=summary["counts"])
            
        else:
            logger.warning(f"jobs.csv not found")
            print(f"⚠️  jobs.csv not found in root or run directory")
            print("Run main.py first to search for jobs.")
        
        print("\n" + "="*80)
        print(f"DONE! Check '{run_mgr.cover_letters_dir}' for your cover letters.")
        print("="*80 + "\n")
        
        print("📋 NEXT STEPS:")
        print(f"1. Review cover letters in {run_mgr.cover_letters_dir}")
        print("2. Each cover letter has been reviewed by the AI Judge")
        print("3. Add company-specific research if needed")
        print("4. Copy and send!")
        print(f"\n📊 Run summary:")
        summary = run_mgr.get_summary()
        print(f"   - Jobs found: {summary['counts']['jobs']}")
        print(f"   - Cover letters generated: {summary['counts']['cover_letters_generated']}")
        print(f"   - Prompts created: {summary['counts']['prompts_created']}")
        print("\n" + "="*80 + "\n")
        
        logger.info("Cover letter generation completed successfully")
        logger.info(f"Summary: {summary['counts']}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To fix this:")
        print("1. Get your Gemini API key from https://aistudio.google.com/app/apikey")
        print("2. Get your Groq API key from https://console.groq.com/keys")
        print("3. Open config.json")
        print("4. Add your API keys")
        print("\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if 'logger' in locals():
            logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
