"""
AI Cover Letter Prompt Generator
Generates detailed AI prompts that can be used with ChatGPT, Claude, or other LLMs
to create personalized job application cover letters in your exact writing style.
"""

import json
import csv
import os
from datetime import datetime


class CoverLetterPromptGenerator:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Your professional profile (extracted from config)
        user_profile = self.config.get('user_profile', {})
        
        self.profile = {
            "name": user_profile.get('name', 'Candidate'),
            "current_title": user_profile.get('current_role', 'Professional'),
            "current_company": user_profile.get('current_company', ''),
            "experience_years": user_profile.get('experience_years', 'several'),
            "education": user_profile.get('education', []),
            "core_skills": user_profile.get('skills', []),
            "key_achievements": user_profile.get('achievements', []),
            "target_roles": user_profile.get('target_roles', []),
            "preferred_locations": user_profile.get('locations', [])
        }
    
    def generate_job_application_prompt(self, job, include_judge=True):
        """Generate a detailed AI prompt for creating a job application cover letter"""
        
        prompt = f"""You are helping me write a professional, compelling job application cover letter. Here's the context:

## MY PROFESSIONAL PROFILE:
**Name:** {self.profile['name']}
**Current Role:** {self.profile['current_title']} at {self.profile['current_company']}
**Experience:** {self.profile['experience_years']} years in data science, NLP, and AI/ML

**Education:**
{self._format_list(self.profile['education'])}

**Core Technical Skills:**
{self._format_list(self.profile['core_skills'])}

**Key Achievements:**
{self._format_list(self.profile['key_achievements'])}

**Target Roles:** {', '.join(self.profile['target_roles'])}
**Preferred Locations:** {', '.join(self.profile['preferred_locations'])}

## JOB DETAILS:
**Position:** {job.get('title', 'N/A')}
**Company:** {job.get('company', 'N/A')}
**Location:** {job.get('location', 'N/A')}
**Job Description:** {job.get('description', 'N/A')[:1000]}
**Job Link:** {job.get('link', 'N/A')}
**Source:** {job.get('source', 'N/A')}

## WRITING STYLE GUIDELINES:
1. **Tone:** Bold, humble, creative, corporate - confident without arrogance
2. **Length:** Concise (250-350 words max) - hiring managers are busy
3. **Structure:**
   - **Opening Sentence:** Choose ONE of these styles (convey the job, my background, and tone):
     * High-impact & confident: "I'm reaching out because your team is working on exactly the kind of challenges I've spent the last few years mastering—and I'm ready to contribute from day one."
     * Curiosity-driven: "Your role stood out to me for one reason: it aligns remarkably well with the problems I'm already passionate about solving."
     * Value-forward: "Before sharing my background, I'll start with what matters most: I can help your team achieve [specific outcome] by [specific approach]—and I'd like to demonstrate how."
     * Story-driven: "When I read your job posting, I immediately recognised a familiar challenge—one I've tackled successfully before and would be keen to approach again."
     * Bold and concise: "I know how to deliver tangible results in this role, and I'd welcome the chance to prove it."
     * Human, warm, genuine: "This role feels like a rare instance where my strengths and your team's needs align with unusual precision."
     * Problem-solution framing: "You're looking for someone who can take ownership of [specific responsibility]—and that's exactly where I've delivered my strongest results."
     * Outcome-focused: "I'm reaching out because I specialise in turning challenges like yours into clear, measurable wins."
     * Strategic positioning: "What drew me to this position is how closely it aligns with the kind of impact I've been delivering—and hope to expand—in my next role."
     * Vivid & memorable: "Opportunities like this are uncommon, especially ones that match both my experience and long-term direction so precisely."
   - Body Paragraph 1: Highlight current role and 3-4 specific achievements using **bullet points**
   - Body Paragraph 2: Mention technical expertise and education (PhD, MBA, MIT)
   - Closing: Express enthusiasm for the specific company and suggest next steps
4. **Avoid:**
   - Generic phrases like "I am writing to apply" or "I am excited to apply"
   - Overly formal or stiff language
   - Buzzwords without substance
   - Starting with "Dear Hiring Manager" (use a more direct opening)
5. **Include:**
   - **Bullet points** for achievements (CRITICAL)
   - Specific examples of relevant work
   - Quantifiable achievements where possible
   - Genuine interest in the company/role
   - Clear connection between my experience and their needs

## FOLLOW THIS WRITING STYLE:
**SHOULD:**
- Use clear, simple language
- Be spartan and informative
- Use short, impactful sentences
- Use active voice (avoid passive voice)
- Focus on practical, actionable insights
- **Use a bulleted list for key achievements**
- Use data and examples to support claims when possible
- Use "you" and "your" to directly address the reader

**AVOID:**
- Em dashes (—) anywhere in your response. Use only commas, periods, or other standard punctuation
- Constructions like "...not just this, but also this"
- Metaphors and clichés
- Generalizations
- Common setup language in any sentence (in conclusion, in closing, etc.)
- Output warnings or notes, just the output requested
- Unnecessary adjectives and adverbs
- Hashtags
- Semicolons
- Markdown formatting (except for the bullet list)
- Asterisks
- These words: "can, may, just, that, very, really, literally, actually, certainly, probably, basically, could, maybe, delve, embark, enlightening, esteemed, shed light, craft, crafting, imagine, realm, game-changer, unlock, discover, skyrocket, abyss, not alone, in a world where, revolutionize, disruptive, utilize, utilizing, dive deep, tapestry, illuminate, unveil, pivotal, intricate, elucidate, hence, furthermore, realm, however, harness, exciting, excited, groundbreaking, cutting-edge, remarkable, it, remains to be seen, glimpse into, navigating, landscape, stark, testament, in summary, in conclusion, moreover, boost, skyrocketing, opened up, powerful, inquiries, ever-evolving"

**IMPORTANT:** Review your response and ensure no em dashes are used!

## TASK:
Write a compelling job application cover letter that:
1. Has a strong, specific subject line
2. **Opens with ONE of the provided opening sentence styles** - must convey: the job, my background, and a bold/humble/creative/corporate tone
3. **Must include a bulleted list** of 3-4 relevant achievements from my profile
4. **Must mention** my PhD, MBA, and MIT training
5. Shows I understand what the company does and why I want to work there
6. Ends with a clear call to action
7. Maintains a warm, professional tone throughout
8. **Tone must be: bold, humble, creative, corporate**

## ADDITIONAL CONTEXT:
- Research the company ({job.get('company', 'N/A')}) and mention something specific about them if possible
- Match my skills to the job requirements intelligently
- If the job mentions specific technologies I have (NLP, LLMs, Azure, Python, etc.), emphasize those
- Keep it authentic - this should sound like a real person, not a template

"""
        
        if include_judge:
            prompt += f"\n\n{self.get_job_judge_instructions()}"
            prompt += "\n\nPlease write the cover letter now, then review it against all checks above before submitting."
        else:
            prompt += "\n\nPlease write the cover letter now."

        return prompt

    def get_job_judge_instructions(self):
        """Get the AI Judge instructions for job applications"""
        return """## AI JUDGE - QUALITY CONTROL:
Before submitting your final cover letter, act as a strict quality judge and verify:

**CRITICAL CHECKS (Must Pass All):**
1. ✓ No em dashes (—) anywhere in the cover letter
2. ✓ No semicolons anywhere in the cover letter
3. ✓ No markdown formatting (no **, __, ##, etc.) EXCEPT for the bullet list
4. ✓ No asterisks for emphasis
5. ✓ No hashtags
6. ✓ All sentences use active voice (not passive)
7. ✓ No banned words from the list above (including "excited")
8. ✓ **Does NOT start with "I am excited to apply"**
9. ✓ No metaphors or clichés
10. ✓ Cover letter is 250-350 words maximum

**STYLE CHECKS (Must Pass All):**
1. ✓ Uses short, impactful sentences
2. ✓ Uses clear, simple language
3. ✓ Addresses reader with "you" and "your"
4. ✓ Includes specific examples and data
5. ✓ Sounds like a real person, not a template
6. ✓ **Includes a bulleted list** for achievements

**CONTENT CHECKS (Must Pass All):**
1. ✓ Subject line is specific and compelling
2. ✓ **Opening sentence follows ONE of the provided styles** (bold, humble, creative, corporate tone)
3. ✓ Opening conveys: the job, my background, and appropriate tone
4. ✓ Highlights 3-4 relevant achievements in bullets
5. ✓ **Mentions PhD, MBA, and MIT training**
6. ✓ Shows understanding of the company
7. ✓ Ends with clear call to action
8. ✓ Mentions specific technologies from job description
9. ✓ Overall tone is: bold, humble, creative, corporate

**IF ANY CHECK FAILS:** Revise the cover letter and check again. Do not output until ALL checks pass."""


    
    def _format_list(self, items):
        """Format a list with bullet points"""
        return '\n'.join([f"- {item}" for item in items])
    
    def save_prompts_for_jobs(self, jobs_csv="jobs.csv", output_dir="ai_prompts"):
        """Generate AI prompts for all jobs and save them"""
        os.makedirs(output_dir, exist_ok=True)
        
        with open(jobs_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
        
        print(f"🤖 Generating AI prompts for {len(jobs)} jobs...\n")
        
        for i, job in enumerate(jobs, 1):
            prompt = self.generate_job_application_prompt(job)
            
            # Create safe filename
            safe_company = "".join(c for c in job['company'] if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = f"{output_dir}/job_{i:03d}_{safe_company}_PROMPT.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
        
        print(f"✅ Created {len(jobs)} AI prompts in {output_dir}/")
        print(f"\n💡 Usage: Copy any prompt file and paste it into ChatGPT, Claude, or your preferred AI assistant")
    
    def generate_single_prompt(self, job_title, company_name):
        """Generate a prompt for a specific job by searching the CSV"""
        with open("jobs.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for job in reader:
                if job_title.lower() in job['title'].lower() and company_name.lower() in job['company'].lower():
                    return self.generate_job_application_prompt(job)
        
        return "Job not found in jobs.csv"


def main():
    """Main function to generate all AI prompts"""
    print("\n" + "="*80)
    print(" "*20 + "AI COVER LETTER PROMPT GENERATOR")
    print(" "*20 + "Generate prompts for AI assistants")
    print("="*80 + "\n")
    
    generator = CoverLetterPromptGenerator()
    
    # Generate prompts for jobs
    if os.path.exists("jobs.csv"):
        generator.save_prompts_for_jobs()
    else:
        print("⚠️  jobs.csv not found. Run main.py first to search for jobs.")
    
    print("\n" + "="*80)
    print("DONE! Check the 'ai_prompts/' folder for your AI prompts.")
    print("="*80 + "\n")
    
    print("📋 HOW TO USE:")
    print("1. Open any prompt file from the ai_prompts/ folder")
    print("2. Copy the entire prompt")
    print("3. Paste it into ChatGPT, Claude, or your preferred AI assistant")
    print("4. The AI will generate a personalized cover letter in your style")
    print("5. Review and customize the output before sending")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
