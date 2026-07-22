from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("GOFIT_APP_NAME", "GoFit Business Center")
    database_url: str = os.getenv("GOFIT_DATABASE_URL", "sqlite:///./gofit.db")
    storage_dir: str = os.getenv("GOFIT_STORAGE_DIR", "../../storage")
    ai_center_url: str = os.getenv("GOFIT_AI_CENTER_URL", "http://127.0.0.1:8001")


settings = Settings()
