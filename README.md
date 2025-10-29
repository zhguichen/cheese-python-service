# AI Practice Service

AI 练一练服务 - 使用 OpenAI API 生成和验证练习题的 Python 微服务

## 功能特性

- 🎯 根据章节内容自动生成练习题（单选题、简答题、代码题）
- ✅ 智能验证学生答案并给出详细解析
- 🔒 使用 Pydantic 进行数据验证
- 📝 结构化 JSON 输出
- 🚀 基于 FastAPI 的高性能异步服务

## 技术栈

- **FastAPI**: Web 框架
- **OpenAI API**: LLM 服务（支持结构化输出）
- **Pydantic**: 数据验证和设置管理
- **Uvicorn**: ASGI 服务器

## 项目结构

```
python-service/
├── app/                           # 核心应用代码包
│   ├── api/                       # API 接口定义和路由管理
│   │   ├── endpoints/             # 子路由模块
│   │   │   └── practice.py        # 练习题相关路由
│   │   └── router.py              # 路由聚合入口
│   ├── core/                      # 基础配置、安全、工具和通用模块
│   │   └── config.py              # 配置管理
│   ├── services/                  # 核心业务逻辑和 AI 厂商接口
│   │   └── ai_service.py          # OpenAI 服务封装
│   ├── schemas/                   # Pydantic 数据模型
│   │   └── practice.py            # 练习题相关模型
│   └── main.py                    # FastAPI 主应用
├── prompts/                       # LLM Prompt 模板
│   ├── generate.txt               # 生成题目的 prompt
│   └── verify.txt                 # 验证答案的 prompt
├── tests/                         # 测试代码
│   └── practice_test.http         # HTTP 接口测试
├── requirements.txt               # Python 依赖列表
└── README.md                      # 项目文档
```

## 快速开始

### 0. 先决条件

- 已安装 `uv`
- 可用的 Python 3.11 解释器（`uv` 会自动下载/管理）

### 1. 安装依赖（使用 uv 管理环境）

项目推荐使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境和依赖，请先确保已安装 `uv`（macOS 或 Linux 可通过 `curl -LsSf https://astral.sh/uv/install.sh | sh` 安装，Windows 可使用 `powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"`）。

```bash
cd python-service
uv venv --python 3.11
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

> 后续需要安装新依赖时，优先使用 `uv pip install 包名`，并同步更新 `requirements.txt`。

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Server Configuration
HOST=0.0.0.0
PORT=8001

# Environment
ENVIRONMENT=development
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
python -m app.main

# 或使用 uvicorn 直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. 测试接口

使用 `tests/practice_test.http` 文件进行测试（需要 REST Client 插件）

或使用 curl：

```bash
# 健康检查
curl http://localhost:8001/health

# 生成练习题
curl -X POST http://localhost:8001/internal/ai/practice/generate \
  -H "Content-Type: application/json" \
  -d @tests/generate_example.json

# 验证答案
curl -X POST http://localhost:8001/internal/ai/practice/verify \
  -H "Content-Type: application/json" \
  -d @tests/verify_example.json
```

## API 文档

### 1. 生成练习题

**接口**: `POST /internal/ai/practice/generate`

**请求体**:
```json
{
  "sessionId": "session_001",
  "userId": "user_001",
  "sectionId": "section_001",
  "bookName": "Python编程入门",
  "bookIntroduction": "本书介绍Python基础知识",
  "sectionContent": "章节的完整内容..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "summary": "章节总结与出题要点...",
    "questions": [
      {
        "questionId": "1",
        "type": "single_choice",
        "content": "题目内容..."
      },
      {
        "questionId": "2",
        "type": "short_answer",
        "content": "题目内容..."
      },
      {
        "questionId": "3",
        "type": "code",
        "content": "题目内容..."
      }
    ]
  }
}
```

### 2. 验证练习题答案

**接口**: `POST /internal/ai/practice/verify`

**请求体**（题目内容将由服务通过 `sessionId` 从日志中拉取）:
```json
{
  "sessionId": "session_001",
  "userId": "user_001",
  "questions": [
    {
      "questionId": "1",
      "type": "single_choice",
      "answer": "用户的答案"
    }
  ]
}
```

> 提交答案时无需传递题目内容，服务会基于 `sessionId` 与 `userId` 在会话日志中定位最近一次生成的题面。
> 服务在生成题目时会自动写入章节总结 `summary`，验证阶段会将该摘要加入提示词以提升判题准确性。

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "questions": [
      {
        "questionId": "1",
        "type": "single_choice",
        "isCorrect": true,
        "parsing": "详细的解析说明..."
      }
    ]
  }
}
```

## 与 Go 后端集成

Go 后端调用 Python 服务的示例代码：

```go
// 生成练习题
resp, err := http.Post(
    "http://localhost:8001/internal/ai/practice/generate",
    "application/json",
    bytes.NewBuffer(jsonData),
)

// 验证答案
resp, err := http.Post(
    "http://localhost:8001/internal/ai/practice/verify",
    "application/json",
    bytes.NewBuffer(jsonData),
)
```

## 开发说明

### Prompt 模板

- `prompts/generate.txt`: 生成练习题的系统提示词
- `prompts/verify.txt`: 验证答案的系统提示词

如需调整题目生成策略或评判标准，修改对应的 prompt 文件即可。

### 数据模型

所有数据模型定义在 `app/schemas/practice.py`，使用 Pydantic 进行验证。

### AI 服务

`app/services/ai_service.py` 封装了 OpenAI API 调用，使用结构化输出确保返回格式正确。
