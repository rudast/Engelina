from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    MODEL_ID: str = "Qwen/Qwen2.5-7B-Instruct"

    DEVICE: str = "cuda:0"

    LOAD_IN_4BIT: bool

    MAX_NEW_TOKENS_REPLY: int = 256

    MAX_NEW_TOKENS_FEEDBACK: int = 256

    TEMPERATURE_REPLY: float = 0.6

    TEMPERATURE_FEEDBACK: float = 0.6

    TOP_P: float = 0.9

    MAX_HISTORY_TURNS: int = 12

    REQUEST_TIMEOUT_S: int = 5

    LOG_LEVEL: str

    # HF_CACHE_DIR: str | None (опционально)