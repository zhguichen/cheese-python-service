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
    ) -> AIGeneratedQuestions:
        """生成练习题与章节总结"""
        context = self._session_context(request.userId, request.sessionId)
        self.session_logger.ensure_meta(context, self._build_generate_meta(request))
        # 构造用户消息
        user_message = f"""
书名：{request.bookName}
书籍简介：{request.bookIntroduction}

章节内容：
{request.sectionContent}

请根据以上内容生成章节总结与出题要点，并据此生成3道练习题。
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
                "summary": result.summary,
                "questions": [
                    {
                        "question_id": q.questionId,
                        "type": q.type,
                        "content": q.content,
                        **(
                            {
                                "options": [
                                    {"option_id": opt.optionId, "text": opt.text}
                                    for opt in q.options
                                ]
                            }
                            if q.options
                            else {}
                        ),
                    }
                    for q in result.questions
                ],
            },
            timestamp=self._now(),
        )
        return result

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
        try:
            generate_payload = self.session_logger.load_latest_generate_payload(context)
        except FileNotFoundError as exc:
            raise ValueError("未找到对应的会话日志，请先生成练习题。") from exc
        except ValueError as exc:
            raise ValueError("会话日志中缺少题目信息，请先生成练习题。") from exc

        summary = generate_payload.get("summary", "")
        generated_questions = generate_payload.get("questions")
        if not isinstance(generated_questions, list):
            raise ValueError("会话日志中缺少题目信息，请先生成练习题。")

        question_map = {item.get("question_id"): item for item in generated_questions}

        questions_with_content: List[QuestionWithAnswer] = []
        user_answers_list = []  # 用于存储用户答案
        for answer in request.questions:
            question_meta = question_map.get(answer.questionId)
            if not question_meta:
                raise ValueError(f"未在日志中找到题目 {answer.questionId}")
            content = question_meta.get("content")
            if not content:
                raise ValueError(
                    f"题目 {answer.questionId} 缺少题面内容，请重新生成练习题。"
                )
            question_type = question_meta.get("type") or answer.type
            options = question_meta.get("options")  # 获取选项信息（如果有）

            # 构建 QuestionWithAnswer 对象，包含选项信息
            question_with_answer = QuestionWithAnswer(
                questionId=answer.questionId,
                type=question_type,
                content=content,
                answer=answer.answer,
            )
            # 如果有选项，添加到对象中（用于后续格式化）
            if options:
                question_with_answer.options = [
                    {"optionId": opt.get("option_id"), "text": opt.get("text")}
                    for opt in options
                ]
            questions_with_content.append(question_with_answer)

            # 构建 userAnswer 字段
            if question_type == "single_choice":
                user_answers_list.append(
                    {
                        "questionId": answer.questionId,
                        "userAnswer": {"selectedOptionId": answer.answer},
                    }
                )
            elif question_type == "short_answer":
                user_answers_list.append(
                    {
                        "questionId": answer.questionId,
                        "userAnswer": {"answerText": answer.answer},
                    }
                )
            elif question_type == "code":
                user_answers_list.append(
                    {
                        "questionId": answer.questionId,
                        "userAnswer": {"codeText": answer.answer},
                    }
                )
            else:
                user_answers_list.append(
                    {
                        "questionId": answer.questionId,
                        "userAnswer": {"answerText": answer.answer},
                    }
                )

        self.session_logger.append_event(
            context,
            "answer",
            {
                "answers": [
                    {
                        "question_id": q.questionId,
                        "type": q.type,
                        "answer": q.answer,
                    }
                    for q in questions_with_content
                ]
            },
            timestamp=self._now(),
        )
        # 构造题目和答案的描述
        questions_text = self._format_questions_for_verification(questions_with_content)

        user_message = f"""
章节总结与出题要点：
{summary or "（无摘要信息）"}

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

        # 构建用户答案映射
        user_answer_map = {
            item["questionId"]: item["userAnswer"] for item in user_answers_list
        }

        # 将 userAnswer 添加到每个验证结果中
        enriched_questions = []
        for verified_q in result.questions:
            user_answer = user_answer_map.get(verified_q.questionId, {})
            enriched_questions.append(
                VerifiedQuestion(
                    questionId=verified_q.questionId,
                    type=verified_q.type,
                    isCorrect=verified_q.isCorrect,
                    userAnswer=user_answer,
                    correctAnswer=verified_q.correctAnswer,
                    parsing=verified_q.parsing,
                )
            )

        self.session_logger.append_event(
            context,
            "judge",
            {
                "latency_ms": latency_ms,
                "results": [
                    {
                        "question_id": r.questionId,
                        "is_correct": r.isCorrect,
                        "user_answer": user_answer_map.get(r.questionId, {}),
                        "correct_answer": r.correctAnswer,
                        "parsing": r.parsing,
                    }
                    for r in enriched_questions
                ],
            },
            timestamp=self._now(),
        )
        return enriched_questions

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

            question_text = f"题目 {q.questionId} ({type_name}):\n{q.content}"

            # 如果是单选题且有选项信息，添加选项
            if q.type == "single_choice" and hasattr(q, "options") and q.options:
                question_text += "\n选项："
                for opt in q.options:
                    question_text += f"\n  {opt['optionId']}. {opt['text']}"

            question_text += f"\n\n用户答案:\n{q.answer}"

            formatted.append(question_text)

        return "\n\n".join(formatted)

    def _session_context(self, user_id: str, session_id: str) -> SessionLogContext:
        """Create a session logging context object."""
        return SessionLogContext(user_id=user_id, session_id=session_id)

    def _build_generate_meta(self, request: GeneratePracticeRequest) -> dict:
        """Construct metadata payload for a generate session."""
        return {
            "session_id": request.sessionId,
            "user_id": request.userId,
            "summary": "",
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
            "summary": "",
            "book_name": "",
            "book_introduction": "",
            "section_id": "",
            "section_content": "",
            "start_time": self._now(),
        }

    @staticmethod
    def _now() -> str:
        """Return the current timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


# 创建全局 AI 服务实例
ai_service = AIService()
