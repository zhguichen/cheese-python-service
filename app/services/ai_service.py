"""
AI 服务模块 - 调用 OpenAI API 生成和验证练习题
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import List

from openai import AsyncOpenAI
from app.core.config import get_settings
from app.core.logging import SessionLogger, SessionLogContext
from app.schemas.practice import (
    GeneratePracticeRequest,
    VerifyPracticeRequest,
    AIGeneratedQuestions,
    AIVerifiedQuestions,
    GeneratedQuestion,
    VerifiedQuestion,
    QuestionWithAnswer,
)


class AIService:
    """AI 服务类"""

    def __init__(self):
        """初始化 OpenAI 客户端"""
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.OPENAI_MODEL
        self._project_root = Path(__file__).resolve().parent.parent.parent
        self.prompts_dir = self._project_root / "prompts"
        logs_dir = self._project_root / settings.LOGS_DIR
        self.session_logger = SessionLogger(logs_dir, settings.LOG_VERSION)

        # 加载 prompt 模板
        self.generate_prompt = self._load_prompt("generate.txt")
        self.verify_prompt = self._load_prompt("verify.txt")

    def _load_prompt(self, filename: str) -> str:
        """加载 prompt 文件"""
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def generate_practice(
        self, request: GeneratePracticeRequest
    ) -> List[GeneratedQuestion]:
        """
        生成练习题

        Args:
            request: 生成练习题请求

        Returns:
            生成的题目列表
        """
        context = self._session_context(request.userId, request.sessionId)
        self.session_logger.ensure_meta(context, self._build_generate_meta(request))
        # 构造用户消息
        user_message = f"""
书名：{request.bookName}
书籍简介：{request.bookIntroduction}

章节内容：
{request.sectionContent}

请根据以上内容生成3道练习题。
"""

        # 调用 OpenAI API
        start_time = perf_counter()
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.generate_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        latency_ms = int((perf_counter() - start_time) * 1000)

        # 解析结果 - 获取 JSON 字符串并解析
        json_string = completion.choices[0].message.content
        json_data = json.loads(json_string)

        # 使用 Pydantic 验证
        result = AIGeneratedQuestions.model_validate(json_data)
        self.session_logger.append_event(
            context,
            "generate",
            {
                "latency_ms": latency_ms,
                "questions": [
                    {
                        "question_id": q.questionId,
                        "type": q.type,
                        "content": q.content,
                    }
                    for q in result.questions
                ],
            },
            timestamp=self._now(),
        )
        return result.questions

    async def verify_practice(
        self, request: VerifyPracticeRequest
    ) -> List[VerifiedQuestion]:
        """
        验证练习题答案

        Args:
            request: 验证练习题请求

        Returns:
            验证结果列表
        """
        context = self._session_context(request.userId, request.sessionId)
        self.session_logger.ensure_meta(context, self._build_verify_meta(request))
        self.session_logger.append_event(
            context,
            "answer",
            {
                "answers": [
                    {"question_id": q.questionId, "answer": q.answer}
                    for q in request.questions
                ]
            },
            timestamp=self._now(),
        )
        # 构造题目和答案的描述
        questions_text = self._format_questions_for_verification(request.questions)

        user_message = f"""
请验证以下题目的答案：

{questions_text}

对每道题目进行评判，判断答案是否正确，并给出详细的解析。
"""

        # 调用 OpenAI API
        start_time = perf_counter()
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.verify_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        latency_ms = int((perf_counter() - start_time) * 1000)

        # 解析结果 - 获取 JSON 字符串并解析
        json_string = completion.choices[0].message.content
        json_data = json.loads(json_string)

        # 使用 Pydantic 验证
        result = AIVerifiedQuestions.model_validate(json_data)
        self.session_logger.append_event(
            context,
            "judge",
            {
                "latency_ms": latency_ms,
                "results": [
                    {
                        "question_id": r.questionId,
                        "is_correct": r.isCorrect,
                        "parsing": r.parsing,
                    }
                    for r in result.questions
                ],
            },
            timestamp=self._now(),
        )
        return result.questions

    def _format_questions_for_verification(
        self, questions: List[QuestionWithAnswer]
    ) -> str:
        """
        格式化题目和答案用于验证

        Args:
            questions: 题目列表

        Returns:
            格式化后的文本
        """
        formatted = []
        for q in questions:
            type_name = {
                "single_choice": "单选题",
                "short_answer": "简答题",
                "code": "代码题",
            }.get(q.type, q.type)

            formatted.append(f"""
题目 {q.questionId} ({type_name}):
{q.content}

用户答案:
{q.answer}
""")

        return "\n".join(formatted)

    def _session_context(self, user_id: str, session_id: str) -> SessionLogContext:
        """Create a session logging context object."""
        return SessionLogContext(user_id=user_id, session_id=session_id)

    def _build_generate_meta(self, request: GeneratePracticeRequest) -> dict:
        """Construct metadata payload for a generate session."""
        return {
            "session_id": request.sessionId,
            "user_id": request.userId,
            "book_name": request.bookName,
            "book_introduction": request.bookIntroduction,
            "section_id": request.sectionId,
            "section_content": request.sectionContent,
            "start_time": self._now(),
        }

    def _build_verify_meta(self, request: VerifyPracticeRequest) -> dict:
        """Construct fallback metadata when verify is the first interaction."""
        return {
            "session_id": request.sessionId,
            "user_id": request.userId,
            "book_name": "",
            "book_introduction": "",
            "section_id": request.sectionId,
            "section_content": "",
            "start_time": self._now(),
        }

    @staticmethod
    def _now() -> str:
        """Return the current timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


# 创建全局 AI 服务实例
ai_service = AIService()
