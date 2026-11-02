import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
APP_PORT = int(os.getenv("APP_PORT", "8501"))
