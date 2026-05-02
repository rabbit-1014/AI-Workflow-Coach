from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
VECTOR_STORE_DIR = BASE_DIR / "vector_store" / "chroma_db"
LOG_DIR = BASE_DIR / "logs"

COLLECTION_NAME = "ai_workflow_coach"

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v3").strip()

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n", "\n", "。", "；", "，", " ", ""]
TOP_K = 5

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()

CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "dashscope").strip().lower()
CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "qwen3.6-max-preview").strip()
MODEL_NAME = CHAT_MODEL_NAME

CHAT_API_KEY = os.getenv("CHAT_API_KEY", "").strip()
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "").strip()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()

EFFECTIVE_CHAT_PROVIDER = (
    "openai_compatible" if CHAT_PROVIDER == "deepseek" else CHAT_PROVIDER
)
EFFECTIVE_CHAT_API_KEY = CHAT_API_KEY or DEEPSEEK_API_KEY
EFFECTIVE_CHAT_BASE_URL = CHAT_BASE_URL or (
    DEEPSEEK_BASE_URL
    if CHAT_PROVIDER in {"deepseek", "openai_compatible"}
    else ""
)

LLM_TEMPERATURE = 0.3
LLM_MAX_RETRIES = 2
MAX_LLM_API_RETRIES = int(os.getenv("MAX_LLM_API_RETRIES", "1"))
MAX_PARSE_CORRECTION_RETRIES = int(os.getenv("MAX_PARSE_CORRECTION_RETRIES", "1"))

def ensure_dirs():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def validate_api_key():
    if not DASHSCOPE_API_KEY:
        raise ValueError("缺少 DASHSCOPE_API_KEY，请先配置环境变量。")
