from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LinkedIn Automated Apply App"
    app_api_key: str = "change-me"
    database_url: str = "sqlite:///./linkedin_apply.db"
    key_vault_url: str = ""
    linkedin_email: str = ""
    linkedin_password: str = ""
    linkedin_email_secret_name: str = "linkedin-email"
    linkedin_password_secret_name: str = "linkedin-password"
    linkedin_default_keywords: str = "software engineer,backend engineer"
    linkedin_default_location: str = "Germany"
    linkedin_easy_apply_only: bool = True
    linkedin_headless: bool = True
    linkedin_max_jobs_per_run: int = 20
    linkedin_schedule_cron: str = "0 8 * * *"
    linkedin_daily_limit: int = 20
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def linkedin_keyword_list(self) -> list[str]:
        return [keyword.strip() for keyword in self.linkedin_default_keywords.split(",") if keyword.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
