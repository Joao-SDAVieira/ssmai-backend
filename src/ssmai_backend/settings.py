from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    DATABASE_URL: str

    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_PASSWORD: str

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET: str
    REGION: str

    BEDROCK_AWS_ACCESS_KEY_ID: str
    BEDROCK_AWS_SECRET_ACCESS_KEY: str
    CLOUDE_INFERENCE_PROFILE: str
