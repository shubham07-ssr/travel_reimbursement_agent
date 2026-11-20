from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
HF_PROVIDER = os.getenv("HF_PROVIDER", "auto")
HF_TEMPERATURE = float(os.getenv("HF_TEMPERATURE", "0.1"))
HF_MAX_TOKENS = int(os.getenv("HF_MAX_TOKENS", "1200"))
