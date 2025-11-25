# Job Search Automator

Automated job search and email generation system with multi-CV support, AI-powered email drafting, and comprehensive logging.

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys in config.json
# - Gemini API key (for email generation)
# - Groq API key (for AI quality control)
# - SerpAPI key (for job search)
```

### 2. Run the Workflow

```bash
# Step 1: Search for jobs
python3 scripts/04_search_jobs.py "Data Scientist NLP" "Machine Learning Engineer"

# Step 2: Generate cover letters (creates new CV run)
python3 scripts/07_generate_cover_letters.py <cv_name>

# Step 3: Export results to Excel
python3 scripts/08_export_to_excel.py
```

---

## 📖 How to Run the Scripts

This section provides detailed instructions for running each script in the job search automation workflow.

### **Step 1: Extract CV Text** 📄

Extract text from your CV PDF for processing by AI tools.

```bash
# Extract text from CV (saves to extracted_cvs/ folder)
python3 scripts/01_extract_cv.py
```

**What it does:**
- Extracts text from PDF files in `cvs/` folder
- Saves extracted text to `extracted_cvs/` as `.txt` files
- Automatically handles the CV specified in the script

**Output:**
- `extracted_cvs/CV_NAME.txt` - Plain text version of your CV

---

### **Step 2: Generate CV Configurations** ⚙️

Create AI-powered, CV-specific job search configurations.

```bash
# Generate configs for all CVs in cvs/ folder
python3 scripts/02_generate_cv_configs.py
```

**What it does:**
- Analyzes each CV using Llama 3.3 (via Groq)
- Extracts: name, skills, experience, target roles, locations
- Generates 15-20 strategic job search queries
- Creates individual config files in `configs/` folder

**Requirements:**
- Groq API key in `config.json`
- CV PDFs in `cvs/` folder
- PyMuPDF installed (`pip install PyMuPDF`)

**Output:**
- `configs/CV_NAME.json` - CV-specific configuration with:
  - User profile (name, skills, experience)
  - Job search queries (15-20 tailored queries)
  - Target roles and locations

**Example Output:**
```
======================================================================
🚀 CV CONFIG GENERATOR
======================================================================

🔍 Found 2 CV(s) in cvs/ folder

[1/2]
======================================================================
📄 Processing CV: CV_11_11_2025 (1) copy.pdf
======================================================================
   📝 Using extracted text file: extracted_cvs/CV_11_11_2025 (1) copy.txt
   ✅ Extracted 4860 characters
   🤖 Calling Groq API (llama-3.3-70b-versatile)...
   ✅ Received response from API

   📊 EXTRACTION SUMMARY:
      Name: Dr. Manu Dal Borgo
      Title: Lead/Senior Data Scientist & Technical Advisor
      Skills: 15 skills
      Target Roles: 7 roles
      Search Queries: 19 queries
   ✅ Saved config to: configs/CV_11_11_2025 (1) copy.json
```

---

### **Step 3: Search for Jobs** 🔍

Search for jobs using CV-specific configurations or custom queries.

#### **Option A: Use CV-Specific Config (Recommended)**

```bash
# Search using a specific CV's config
python3 scripts/search_jobs.py --cv "CV_11_11_2025 (1) copy"

# Limit results per query
python3 scripts/search_jobs.py --cv "CV_11_11_2025 (1) copy" --max-results 10

# Custom output file
python3 scripts/search_jobs.py --cv my_cv --output my_jobs.csv

# Skip summary display
python3 scripts/search_jobs.py --cv my_cv --no-summary
```

#### **Option B: Use Default Config**

```bash
# Use config.json in root directory
python3 scripts/search_jobs.py
```

#### **Option C: Use Custom Config Path**

```bash
# Specify exact config file path
python3 scripts/search_jobs.py --config path/to/config.json
```

**What it does:**
- Searches Google Jobs via SerpApi
- Uses queries from CV config (or default config)
- Searches both worldwide and primary location
- Deduplicates results
- Saves to CSV file

**Requirements:**
- SerpApi key in config file
- Free tier: 100 searches/month at https://serpapi.com/

**Command-Line Options:**
- `--cv CV_NAME` - Use specific CV config from `configs/` folder
- `--config PATH` - Use custom config file path
- `--max-results N` - Override max results per query
- `--output FILE` - Custom output filename (default: `jobs.csv`)
- `--no-summary` - Skip displaying job summary
- `--help` - Show all options

**Output:**
- `jobs.csv` (or custom filename) with columns:
  - title, company, location, description, salary
  - link, posted_date, job_id, source, query, region, search_date

**Example Output:**
```
======================================================================
🚀 JOB SEARCH
======================================================================
Config: CV_11_11_2025 (1) copy.json
Queries: 19
Max results per query: 20
Primary location: UK
======================================================================

[1/19] Query: 'Senior Data Scientist London'
   🔎 Searching: 'Senior Data Scientist London' (WORLDWIDE)
   ✅ Found 18 jobs
   🔎 Searching: 'Senior Data Scientist London' (UK)
   ✅ Found 15 jobs

[2/19] Query: 'Lead Data Scientist Remote'
   🔎 Searching: 'Lead Data Scientist Remote' (WORLDWIDE)
   ✅ Found 20 jobs

...

🔄 Deduplicating jobs...
   Removed 47 duplicate(s)

======================================================================
🎉 SEARCH COMPLETE
======================================================================
Total unique jobs found: 156
======================================================================

💾 Saved 156 jobs to jobs.csv
```

---

### **Step 4: Generate Cover Letters** ✉️

Generate AI-powered cover letters for job applications.

```bash
# Generate cover letters for a specific CV
python3 scripts/generate_cover_letters.py <cv_name>

# Example
python3 scripts/generate_cover_letters.py my_data_scientist_cv
```

**What it does:**
- Creates a new timestamped run folder
- Reads jobs from `jobs.csv`
- Generates personalized cover letters using **Gemini Flash 2.0**
- Validates quality using **Groq Llama 3.3** (AI Judge)
- Automatically refines if quality checks fail
- Saves cover letters to run folder

**Three-Step Pipeline:**
1. **Draft** (Gemini) → Initial cover letter
2. **Judge** (Llama 3.3) → Quality validation
3. **Refine** (Gemini) → Fix issues (if needed)

**Requirements:**
- Gemini API key in `config.json`
- Groq API key in `config.json`
- `jobs.csv` file with job listings

**Output:**
- `runs/cv_name_TIMESTAMP/generated_cover_letters/` - Cover letter drafts
- `runs/cv_name_TIMESTAMP/run_metadata.json` - Run statistics

**📖 [Detailed Documentation](docs/COVER_LETTER_GENERATION.md)**

---

### **Step 5: Export to Excel** 📊

Export all runs and results to Excel for analysis.

```bash
# Export all runs to Excel
python3 scripts/export_to_excel.py
```

**What it does:**
- Collects data from all runs
- Creates multi-sheet Excel workbook
- Includes jobs, emails, logs, statistics

**Output:**
- `runs_export.xlsx` with multiple sheets:
  - WORLD - All jobs worldwide
  - EUROPE - European jobs only
  - Run summaries and statistics

---

### **Complete Workflow Example** 🎯

Here's a complete example for a new CV:

```bash
# 1. Add your CV to cvs/ folder
cp ~/Desktop/my_cv.pdf cvs/

# 2. Extract text from CV
python3 scripts/01_extract_cv.py

# 3. Generate CV-specific configuration
python3 scripts/02_generate_cv_configs.py

# 4. Search for jobs using CV config
python3 scripts/search_jobs.py --cv "my_cv"

# 5. Generate personalized emails
python3 scripts/07_generate_cover_letters.py my_cv

# 6. Export everything to Excel
python3 scripts/08_export_to_excel.py

# 7. Review results
open runs_export.xlsx
ls runs/my_cv_*/generated_cover_letters/
```

---

### **Utility Scripts** 🛠️

#### List All Runs
```bash
# Show all CV runs with statistics
python3 scripts/10_list_runs.py
```

#### Migrate Old Data
```bash
# Migrate old data to new structure
python3 scripts/11_migrate_to_runs.py <cv_name>
```

---

### **Tips & Best Practices** 💡

1. **API Keys**: Make sure all API keys are configured in `config.json`
   - Gemini: https://aistudio.google.com/app/apikey
   - Groq: https://console.groq.com/keys
   - SerpApi: https://serpapi.com/

2. **Rate Limits**: 
   - Gemini free tier: 200 requests/day
   - Groq free tier: Available
   - SerpApi free tier: 100 searches/month

3. **CV Organization**: Keep CVs in `cvs/` folder with descriptive names

4. **Config Regeneration**: Re-run `generate_cv_configs.py` if you update your CV

5. **Job Search Frequency**: Run job searches regularly (daily/weekly) for fresh results

6. **Review Before Sending**: Always review generated emails before sending

---

## 📁 Folder Structure

```
job_search_automator/
├── setup_all_model_apis.sh           # Setup script for all API keys
├── GETTING_STARTED.md                # Step-by-step getting started guide
├── scripts/                          # All executable scripts
│   ├── 01_extract_cv.py                # Extract CV text
│   ├── 02_generate_cv_configs.py       # Generate CV-specific configs
│   ├── 03_add_job_from_url.py          # Add a job from URL
│   ├── 04_search_jobs.py               # Search for jobs using SerpAPI
│   ├── 05_rank_existing_jobs.py        # Rank jobs with AI
│   ├── 06_run_manager.py               # Run management module
│   ├── 07_generate_cover_letters.py    # Generate cover letters with AI
│   ├── 08_export_to_excel.py           # Export to Excel
│   ├── 09_create_final_excel.py        # Create final Excel report
│   ├── 10_list_runs.py                 # List all CV runs
│   ├── 11_migrate_to_runs.py           # Migrate old data
│   ├── generate_cover_letter_prompt.py # Cover letter prompt generator
│   └── extract_cv.py                   # CV text extraction (legacy)
│
├── runs/                            # All CV runs (organized by CV)
│   └── <cv_name_timestamp>/
│       ├── cv.pdf                   # CV copy
│       ├── run_metadata.json        # Run statistics
│       ├── jobs/
│       │   └── jobs.csv            # Job listings
│       ├── generated_cover_letters/ # Cover letter drafts
│       ├── ai_prompts/             # AI prompts used
│       └── logs/                   # Detailed logs
│
├── docs/                            # Documentation
│   ├── README.md                    # Main documentation
│   ├── EXCEL_EXPORT_GUIDE.md       # Excel export guide
│   ├── IMPLEMENTATION_SUMMARY.md    # Technical details
│   └── MANUAL_WORKFLOW.md          # Manual workflow guide
│
├── archive/                         # (excluded from public repo – contains old outputs and legacy scripts)
│
├── config.json                      # API keys & configuration
├── requirements.txt                 # Python dependencies
├── runs_export.xlsx                # Latest Excel export
└── venv/                           # Virtual environment
```

## 🎯 Workflow

### Complete Workflow for a New CV

```bash
# 1. Search for jobs (optional - or use existing jobs.csv)
python3 scripts/04_search_jobs.py "Your Job Title" "Another Job Title"

# 2. Create a new CV run and generate emails
python3 scripts/07_generate_cover_letters.py my_cv_name

# 3. Review generated emails
ls runs/my_cv_name_*/generated_cover_letters/

# 4. Export to Excel for analysis
python3 scripts/08_export_to_excel.py

# 5. Open Excel file
open runs_export.xlsx
```

## 📊 Features

### ✅ Multi-CV Support
- Organize job searches by different CVs
- Each CV gets its own timestamped folder
- No mixing of data between different CVs

### ✅ AI-Powered Cover Letter Generation
**Three-Step Quality Pipeline:**

```
Step 1: DRAFT      → Gemini Flash 2.0 generates initial cover letter
Step 2: JUDGE      → Groq Llama 3.3 validates against 25+ quality criteria
Step 3: REFINE     → Gemini refines based on feedback (if needed)
```

**Features:**
- **Dual-Model System**: Combines Gemini's creativity with Llama's strict validation
- **Automatic Quality Control**: 95% of drafts pass on first attempt
- **Personalized Content**: Tailored to each job description and your CV
- **Style Enforcement**: Maintains consistent professional tone
- **Free to Use**: Both models available on free tiers

**Quality Checks Include:**
- ✓ Professional writing style (no jargon, clichés, or banned words)
- ✓ Proper structure (bullet points, clear sections)
- ✓ Education mentions (PhD, MBA, MIT training)
- ✓ Company-specific insights
- ✓ 250-350 word limit
- ✓ Bold, humble, creative, corporate tone

**📖 [Read Full Documentation](docs/COVER_LETTER_GENERATION.md)**

### ✅ Comprehensive Logging
- Detailed logs for every operation
- Both file (DEBUG) and console (INFO) output
- Easy debugging and audit trail

### ✅ Excel Export
- Export all runs with metadata
- Multiple sheets for different views
- Logs, statistics, and summaries
- Ready for analysis and reporting

## 📝 Scripts Overview

### Core Workflow Scripts (Run in Order)

| Script | Purpose | Usage |
|--------|---------|-------|
| `04_search_jobs.py` | Search for jobs using SerpAPI | `python3 scripts/04_search_jobs.py "query1" "query2"` |
| `07_generate_cover_letters.py` | Generate AI cover letters for jobs | `python3 scripts/07_generate_cover_letters.py <cv_name>` |
| `08_export_to_excel.py` | Export results to Excel | `python3 scripts/08_export_to_excel.py` |

### Utility Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `10_list_runs.py` | List all CV runs with stats | `python3 scripts/10_list_runs.py` |
| `11_migrate_to_runs.py` | Migrate old data to new structure | `python3 scripts/11_migrate_to_runs.py <cv_name>` |

### Supporting Modules

| Module | Purpose |
|--------|---------|
| `06_run_manager.py` | Manages CV runs, folders, and logging |
| `generate_cover_letter_prompt.py` | Generates AI prompts for cover letters |
| `01_extract_cv.py` | Extracts text from PDF CVs |

## 🔧 Configuration

Edit `config.json`:

```json
{
  "api_keys": {
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "groq_api_key": "YOUR_GROQ_API_KEY",
    "serpapi_key": "YOUR_SERPAPI_KEY"
  },
  "cv_path": "path/to/your/cv.pdf",
  "writing_style": {
    "tone": "professional",
    "length": "concise"
  }
}
```

### Get API Keys

- **Gemini API**: https://aistudio.google.com/app/apikey (Free tier: 200 requests/day)
- **Groq API**: https://console.groq.com/keys (Free tier available)
- **SerpAPI**: https://serpapi.com/ (100 free searches/month)

## 📈 Current Status

Run `python3 scripts/list_runs.py` to see all your CV runs and statistics.

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No runs found" | Create new run: `python3 scripts/07_generate_cover_letters.py <cv_name>` |
| "API quota exceeded" | Wait 24 hours or use different Gemini model |
| "jobs.csv not found" | Run `scripts/04_search_jobs.py` first or copy jobs.csv to run folder |
| Import errors | Activate venv: `source venv/bin/activate` |

## 📚 Documentation

- **Main Guide**: `docs/README.md`
- **Cover Letter AI System**: `docs/COVER_LETTER_GENERATION.md` ⭐ **NEW**
- **Excel Export**: `docs/EXCEL_EXPORT_GUIDE.md`
- **Implementation**: `docs/IMPLEMENTATION_SUMMARY.md`
- **Manual Workflow**: `docs/MANUAL_WORKFLOW.md`

## 🎓 Example: Multiple CVs

```bash
# Data Scientist CV
# Data Scientist CV
python3 scripts/07_generate_cover_letters.py data_scientist_cv

# Software Engineer CV
python3 scripts/07_generate_cover_letters.py software_engineer_cv

# Product Manager CV
python3 scripts/07_generate_cover_letters.py product_manager_cv

# List all runs
python3 scripts/10_list_runs.py

# Export everything
python3 scripts/08_export_to_excel.py
```

## ⚠️ Important Notes

- **API Limits**: Gemini free tier = 200 requests/day
- **Rate Limiting**: 5 seconds between requests
- **Default Limit**: 100 jobs per run (configurable in script)
- **Virtual Environment**: Always activate venv before running scripts

## 🔄 Migration from Old Structure

If you have old data (jobs.csv, generated_emails, etc.):

```bash
python3 scripts/11_migrate_to_runs.py <cv_name>
```

This will move all old data into the new organized structure.

---

**Version**: 2.0  
**Last Updated**: 2025-11-21  
**Status**: ✅ Production Ready
