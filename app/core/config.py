"""
应用配置管理模块
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

    # OpenAI 配置
    OPENAI_API_KEY: str = "sk-fd03056d6baf438280b9d63479c55677"
    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    OPENAI_MODEL: str = "qwen-flash"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # 环境配置
    ENVIRONMENT: str = "development"

    # 日志配置
    LOGS_DIR: str = "logs"
    LOG_VERSION: str = "v1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
