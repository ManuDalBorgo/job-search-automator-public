#!/usr/bin/env bash

# ------------------------------------------------------------
#  Setup Script for All API Providers & Models
# ------------------------------------------------------------
# This script prepares the development environment, installs the
# required Python packages and guides you through adding the API keys
# for every service used by the Job Search Automator:
#   • Gemini (primary)
#   • Groq   (primary)
#   • SerpAPI (job search)
#   • OpenRouter (Gemini fallback)
#   • Together AI (Groq fallback)
#   • Hugging Face (optional fallback for both)
# ------------------------------------------------------------

set -e

# 1️⃣  Ensure we are inside a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "⚠️  No virtual environment detected."
  echo "Attempting to activate one..."
  if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
  else
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    exit 1
  fi
fi

# 2️⃣  Install all required Python dependencies
echo "\n📦 Installing required Python packages..."
# Core dependencies are listed in requirements.txt; we also need the fallback libs
pip install -r requirements.txt
pip install openai together huggingface_hub
echo "✅ Dependencies installed"

# 3️⃣  Collect API keys from the user (or instruct where to add them)
echo "\n🔑 API Keys Setup"
cat <<'EOF'
Please add the following keys to your config.json (or config.example.json if you prefer to copy it first):

  "api_keys": {
    "gemini_api_key": "YOUR_GEMINI_KEY",
    "groq_api_key":   "YOUR_GROQ_KEY",
    "serpapi_key":    "YOUR_SERPAPI_KEY",
    "openrouter_api_key": "YOUR_OPENROUTER_KEY",
    "together_api_key":   "YOUR_TOGETHER_KEY",
    "huggingface_api_key": "YOUR_HUGGINGFACE_TOKEN"
  }

If you already have a config.json, simply edit the fields above.  If not, copy the example:
  cp config.example.json config.json
  # then edit config.json with your keys.
EOF

# 4️⃣  Model configuration (fallback models)
cat <<'EOF'
Fallback model configuration (add under "fallback_models" in config.json):

  "fallback_models": {
    "gemini_fallback": {
      "enabled": true,
      "model": "meta-llama/llama-3.1-8b-instruct:free"
    },
    "groq_fallback": {
      "enabled": true,
      "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    }
  }
EOF

# 5️⃣  Quick verification (optional)
if command -v python3 >/dev/null 2>&1; then
  echo "\n🔍 Verifying installation..."
  python3 -c "import openai, together, huggingface_hub; print('✅ All Python packages import correctly')"
fi

# 6️⃣  Final instructions
cat <<'EOF'
------------------------------------------------------------
Setup complete! You can now:
  1. Edit config.json with your real API keys (see step 3).
  2. Run the workflow, e.g.:
       python3 scripts/04_search_jobs.py "Data Scientist" "Machine Learning Engineer"
       python3 scripts/07_generate_cover_letters.py <cv_name>
       python3 scripts/08_export_to_excel.py
  3. Push the repository to GitHub.
------------------------------------------------------------
EOF
