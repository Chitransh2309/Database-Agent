from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM provider selection ─────────────────────────────────────────────
    LLM_PROVIDER: str = "bedrock"            # "bedrock" | "gemini"

    # ── AWS Bedrock (via the Bedrock Mantle OpenAI-compatible endpoint) ────
    BEDROCK_MODEL_ID: str = "openai.gpt-oss-120b"
    BEDROCK_MANTLE_BASE_URL: str = "https://bedrock-mantle.ap-south-1.api.aws/v1"
    BEDROCK_MANTLE_API_KEY: str | None = None

    # ── Gemini (optional — only needed when LLM_PROVIDER=gemini) ──────────
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # ── Databases ──────────────────────────────────────────────────────────
    POSTGRES_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/copilot_db"
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "copilot_db"

    # ── Server ─────────────────────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    MAX_REPAIR_ATTEMPTS: int = 3

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
