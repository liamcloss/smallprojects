from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), extra="ignore")

    openai_api_key: str | None = None
    text_model: str = "gpt-5.6-luna"
    image_model: str = "gpt-image-2"
    image_quality: str = "low"
    image_generation_size: str = "1024x1536"

    concept_count: int = 12
    output_post_count: int = 3
    use_web_context: bool = True
    mock_openai: bool = False
    uk_region: str = "United Kingdom"
    account_handle: str = "@yourhandle"

    app_auth_username: str | None = None
    app_auth_password: str | None = None

    auto_prepare_enabled: bool = False
    auto_prepare_time: str = "07:00"
    auto_prepare_timezone: str = "Europe/London"
    auto_prepare_web_context: bool = True
    auto_prepare_mock: bool = False

    output_dir: Path = Path("./output")
    database_path: Path = Path("./data/content_factory.sqlite3")

    canvas_width: int = 1080
    canvas_height: int = 1920
    text_margin: int = 110
    watermark_margin: int = 60


settings = Settings()
