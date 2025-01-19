import sys
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Add the virtual environment site-packages to Python path
VENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv')
if os.path.exists(VENV_PATH):
    SITE_PACKAGES = os.path.join(VENV_PATH, 'Lib', 'site-packages')
    sys.path.append(SITE_PACKAGES)

# Replace OpenAI with Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Add this for debugging
print(f"API Key loaded: {'Yes' if GEMINI_API_KEY else 'No'}")  # Debug line

# Optional: Add to prevent API key exposure in error pages
DEBUG = False  # Set to False in production 