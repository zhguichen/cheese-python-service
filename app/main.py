"""
FastAPI 主应用
"""

from fastapi import FastAPI
from app.api.practice import router as practice_router
from app.core.config import get_settings

# 创建 FastAPI 应用
app = FastAPI(
    title="AI Practice Service",
    description="AI 练一练服务 - 生成和验证练习题",
    version="1.0.0",
)

# 注册路由
app.include_router(practice_router)


@app.get("/")
async def root():
    """根路径"""
    return {"service": "AI Practice Service", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
