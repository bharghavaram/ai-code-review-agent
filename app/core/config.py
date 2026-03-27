import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    MAX_FILE_SIZE_KB: int = int(os.getenv("MAX_FILE_SIZE_KB", "100"))
    MAX_FILES_PER_PR: int = int(os.getenv("MAX_FILES_PER_PR", "20"))
    COMPLEXITY_THRESHOLD: int = int(os.getenv("COMPLEXITY_THRESHOLD", "10"))
    SECURITY_SCAN_ENABLED: bool = os.getenv("SECURITY_SCAN_ENABLED", "true").lower() == "true"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

settings = Settings()
