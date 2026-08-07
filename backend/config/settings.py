"""全局配置模块

使用 pydantic-settings 从 .env 文件和环境变量加载配置。
所有配置项在应用启动时一次性加载，后续通过 `get_settings()` 获取单例。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 backend/.env 文件和环境变量加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── 阿里云百炼 API（OpenAI 兼容接口） ──
    openai_api_key: str = ""
    openai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ── 模型选择 ──
    model_name: str = "qwen3.8-max"
    model_name_lite: str = "qwen3.7-flash"

    # ── 服务配置 ──
    backend_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """将逗号分隔的 CORS_ORIGINS 转换为 FastAPI/Socket.IO 配置。"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（缓存，只加载一次）"""
    return Settings()
