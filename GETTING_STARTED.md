# 🚀 Getting Started with **Job Search Automator** (public repo)

Below is a step‑by‑step markdown guide that walks you through setting up the project from a fresh clone, fixing the dependency issue you hit, and running the full pipeline.

---

## 1️⃣  Clone the repository (if you haven’t already)

```bash
git clone https://github.com/ManuDalBorgo/job-search-automator.git
cd job-search-automator/public   # the folder we prepared for public use
```

---

## 2️⃣  Create & activate a Python virtual environment  

```bash
# Create the venv (run **once**)
python3 -m venv venv

# Activate it (run **every** new terminal session)
source venv/bin/activate
```

You should see the prompt change to `(venv)`.

---

## 3️⃣  Upgrade `pip` (this fixes the *jiter* install error)

The failure you saw was caused by an old `pip` (19.2.3). Upgrade it **inside** the virtual environment:

```bash
pip install --upgrade pip
```

You should now have a recent version (e.g., `pip 24.x`).

---

## 4️⃣  Install all project dependencies  

Now run the setup script again – it will install the core requirements **and** the fallback‑API libraries.

```bash
bash setup_all_model_apis.sh
```

If you prefer to do it manually, you can run the two `pip` commands directly:

```bash
pip install -r requirements.txt
pip install openai together huggingface_hub
```

> **Why this works:**
> * The upgraded `pip` can resolve the `jiter` package that `openai` depends on.
> * The script also checks (or creates) the virtual environment for you.

---

## 5️⃣  Create a `config.json` with your API keys  

The repository contains a `config.example.json`. Copy it and fill in your real keys:

```bash
cp config.example.json config.json
```

Edit `config.json` (any editor) and replace the placeholder values:

```json
{
  "api_keys": {
    "gemini_api_key":   "YOUR_GEMINI_KEY",
    "groq_api_key":     "YOUR_GROQ_KEY",
    "serpapi_key":      "YOUR_SERPAPI_KEY",
    "openrouter_api_key":"YOUR_OPENROUTER_KEY",
    "together_api_key": "YOUR_TOGETHER_KEY",
    "huggingface_api_key":"YOUR_HUGGINGFACE_TOKEN"
  },

  "fallback_models": {
    "gemini_fallback": {
      "enabled": true,
      "model": "meta-llama/llama-3.1-8b-instruct:free"
    },
    "groq_fallback": {
      "enabled": true,
      "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    }
  },

  // (optional extra settings you may already have)
  "cv_path": "cvs/",
  "writing_style": {
    "tone": "professional",
    "length": "concise"
  }
}
```

> **Never commit `config.json`** – it contains secrets. The repo already has a `.gitignore` entry for it.

---

## 6️⃣  Add your CV(s)

Create a `cvs/` folder (if it doesn’t exist) and drop one or more PDF CV files inside:

```bash
mkdir -p cvs
cp ~/Desktop/my_cv.pdf cvs/
```

The filename (without `.pdf`) will be used as the CV identifier (e.g., `my_cv`).

---

## 7️⃣  Extract text from the CV(s)

```bash
python3 scripts/01_extract_cv.py
```

Plain‑text versions appear in `extracted_cvs/`.

---

## 8️⃣  Generate per‑CV configuration files  

```bash
python3 scripts/02_generate_cv_configs.py
```

This creates JSON files under `configs/` (e.g., `configs/my_cv.json`).  **These files do NOT contain API keys** – they only hold CV‑specific data (name, skills, search queries, etc.).

---

## 9️⃣  Search for jobs (SerpAPI)

You can either use the CV‑specific queries (recommended) or run an ad‑hoc search.

*Using the CV config*:

```bash
python3 scripts/04_search_jobs.py --cv "my_cv"
```

*Ad‑hoc example*:

```bash
python3 scripts/04_search_jobs.py "Data Scientist" "Machine Learning Engineer"
```

The results are saved as `jobs.csv` (or a custom file you specify).

---

## 🔟  Rank the jobs (Groq / fallback)

```bash
python3 scripts/05_rank_existing_jobs.py
```

A `suitability_score` column is added to `jobs.csv`.

---

## 1️⃣1️⃣  Generate cover letters  

```bash
python3 scripts/07_generate_cover_letters.py my_cv
```

A timestamped run folder appears under `runs/` (e.g., `runs/my_cv_20251124_173500`).  All generated letters are stored in `runs/.../generated_cover_letters/`.

---

## 1️⃣2️⃣  Export everything to Excel (nice summary)

```bash
python3 scripts/08_export_to_excel.py
```

Creates `runs_export.xlsx` with multiple sheets (jobs, letters, logs, stats).

---

## 1️⃣3️⃣  One‑command pipeline (optional)

If you prefer a single command that runs the whole flow:

```bash
python3 run_all.py
```

Make sure you have a CV in `cvs/` before invoking it.

---

## 1️⃣4️⃣  Utility scripts you might find handy

| Script | What it does |
|--------|--------------|
| `10_list_runs.py` | Lists all existing run folders with basic statistics. |
| `11_migrate_to_runs.py` | Moves legacy data (old `jobs.csv`, `generated_emails`) into the new `runs/` layout. |
| `scripts/add_job_from_url.py` | Manually add a single job posting by URL. |
| `scripts/create_final_excel.py` | Generates a polished final Excel report (if you need extra formatting). |

Run any script with `-h` / `--help` for its options, e.g.:

```bash
python3 scripts/10_list_runs.py --help
```

---

## 1️⃣5️⃣  Push the repo to GitHub (optional)

```bash
git add .
git commit -m "Initial public commit – scripts renamed, setup script added"
git remote add origin https://github.com/ManuDalBorgo/job-search-automator.git
git push -u origin main
```

> **Important:** `config.json` is ignored by `.gitignore`; only `config.example.json` is stored in the repo.

---

## ✅  Quick checklist (run after each step)

- [ ] Virtual environment activated (`source venv/bin/activate`).
- [ ] `pip` upgraded (`pip install --upgrade pip`).
- [ ] Dependencies installed (`bash setup_all_model_apis.sh`).
- [ ] `config.json` filled with real API keys.
- [ ] At least one CV PDF in `cvs/`.
- [ ] Text extracted (`01_extract_cv.py`).
- [ ] CV config generated (`02_generate_cv_configs.py`).
- [ ] Jobs searched (`04_search_jobs.py`).
- [ ] Jobs ranked (`05_rank_existing_jobs.py`).
- [ ] Cover letters generated (`07_generate_cover_letters.py`).
- [ ] Excel exported (`08_export_to_excel.py`).

You’re now ready to hunt for jobs and let the AI draft personalized cover letters for you! 🎉

If anything still fails or you need clarification on a particular step, just let me know. Happy job hunting!
