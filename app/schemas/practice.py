"""
练习题相关的 Pydantic 数据模型
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ============= 生成练习题相关模型 =============


class GeneratePracticeRequest(BaseModel):
    """生成练习题请求"""

    sessionId: str = Field(..., description="学习会话ID")
    userId: str = Field(..., description="用户ID")
    sectionId: str = Field(..., description="章节ID")
    bookName: str = Field(..., description="书名")
    bookIntroduction: str = Field(..., description="书籍简介")
    sectionContent: str = Field(..., description="章节内容")


class Option(BaseModel):
    """选择题选项模型"""

    optionId: str = Field(..., description="选项ID (a, b, c, d)")
    text: str = Field(..., description="选项文本内容")


class QuestionBase(BaseModel):
    """题目基础模型"""

    questionId: str = Field(..., description="题目ID")
    type: Literal["single_choice", "short_answer", "code"] = Field(
        ..., description="题目类型"
    )
    content: str = Field(..., description="题目内容")
    options: Optional[List[Option]] = Field(
        None, description="选项列表（仅单选题需要）"
    )


class GeneratedQuestion(QuestionBase):
    """生成的题目"""

    pass


class GeneratePracticeResponse(BaseModel):
    """生成练习题响应"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict = Field(..., description="响应数据")


class GeneratePracticeData(BaseModel):
    """生成练习题的数据部分"""

    summary: str = Field(..., description="章节总结与出题要点")
    questions: List[GeneratedQuestion] = Field(..., description="生成的题目列表")


# ============= 验证答案相关模型 =============


class QuestionAnswer(BaseModel):
    """用户提交的答案"""

    questionId: str = Field(..., description="题目ID")
    type: Literal["single_choice", "short_answer", "code"] = Field(
        ..., description="题目类型"
    )
    answer: str = Field(..., description="用户提交的答案")


class VerifyPracticeRequest(BaseModel):
    """验证练习题请求"""

    sessionId: str = Field(..., description="学习会话ID")
    userId: str = Field(..., description="用户ID")
    questions: List[QuestionAnswer] = Field(..., description="待验证的题目列表")


class QuestionWithAnswer(QuestionBase):
    """带题面内容的答案，用于内部验证流程"""

    answer: str = Field(..., description="用户提交的答案")


class VerifiedQuestion(BaseModel):
    """验证后的题目结果"""

    questionId: str = Field(..., description="题目ID")
    type: Literal["single_choice", "short_answer", "code"] = Field(
        ..., description="题目类型"
    )
    isCorrect: bool = Field(..., description="答案是否正确")
    parsing: str = Field(..., description="LLM生成的解析")


class VerifyPracticeResponse(BaseModel):
    """验证练习题响应"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict = Field(..., description="响应数据")


class VerifyPracticeData(BaseModel):
    """验证练习题的数据部分"""

    questions: List[VerifiedQuestion] = Field(..., description="验证结果列表")


# ============= OpenAI 输出格式模型 =============


class AIGeneratedQuestions(BaseModel):
    """AI生成的题目列表（用于结构化输出）"""

    summary: str = Field(..., description="章节总结与出题要点")
    questions: List[GeneratedQuestion] = Field(..., description="生成的题目列表")


class AIVerifiedQuestionResult(BaseModel):
    """AI验证的单个题目结果（不含userAnswer，由LLM生成）"""

    questionId: str = Field(..., description="题目ID")
    type: Literal["single_choice", "short_answer", "code"] = Field(
        ..., description="题目类型"
    )
    isCorrect: bool = Field(..., description="答案是否正确")
    parsing: str = Field(..., description="LLM生成的解析")


class AIVerifiedQuestions(BaseModel):
    """AI验证的题目结果列表（用于结构化输出）"""

    questions: List[AIVerifiedQuestionResult] = Field(..., description="验证结果列表")
