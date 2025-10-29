"""
练习题 API 路由
"""

from fastapi import APIRouter, HTTPException
from app.schemas.practice import (
    GeneratePracticeRequest,
    GeneratePracticeResponse,
    VerifyPracticeRequest,
    VerifyPracticeResponse,
)
from app.services.ai_service import ai_service

router = APIRouter(prefix="/internal/ai/practice", tags=["practice"])


@router.post("/generate", response_model=GeneratePracticeResponse)
async def generate_practice(request: GeneratePracticeRequest):
    """
    生成练习题

    根据章节内容生成3道不同类型的练习题
    """
    try:
        # 调用 AI 服务生成题目
        result = await ai_service.generate_practice(request)

        # 构造响应
        return GeneratePracticeResponse(
            code=200,
            message="success",
            data={
                "summary": result.summary,
                "questions": [q.model_dump() for q in result.questions],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成练习题失败: {str(e)}")


@router.post("/verify", response_model=VerifyPracticeResponse)
async def verify_practice(request: VerifyPracticeRequest):
    """
    验证练习题答案

    对用户提交的答案进行评判并给出解析
    """
    try:
        # 调用 AI 服务验证答案
        results = await ai_service.verify_practice(request)

        # 构造响应
        return VerifyPracticeResponse(
            code=200,
            message="success",
            data={"questions": [r.model_dump() for r in results]},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证答案失败: {str(e)}")
