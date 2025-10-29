project-structure:

├── app/
│   ├── api/
│   │   ├── dependencies.py       # 依赖注入函数（例如：选择 LLM Provider 实例）
│   │   ├── endpoints/
│   │   │   └── chat.py           # 聊天 API 路由定义 (e.g., /v1/chat/completion)
│   │   └── router.py             # 汇集所有路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # 应用程序配置，加载 API Keys 等
│   │   └── logging.py            # 日志配置工具
│   ├── services/                 # 核心业务逻辑和 AI 集成
│   │   ├── __init__.py
│   │   ├── prompts/              # 存放所有 Prompt 模板文件
│   │   │   ├── system_persona.txt
│   │   │   └── summarization_template.txt
│   │   ├── llm_providers/        # AI 厂商抽象接口层 (可插拔)
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # LLM 抽象基类 (Interface)
│   │   │   ├── gemini_provider.py# Gemini 接口具体实现
│   │   │   └── openai_provider.py# OpenAI 接口具体实现
│   │   └── chat_service.py       # 对话业务逻辑：选择模型、管理 Prompt、处理响应
│   ├── schemas/                  # Pydantic 数据模型 (用于请求和响应)
│   │   ├── __init__.py
│   │   └── chat.py               # RequestBody 和 Response 模型
│   └── main.py                   # 应用启动入口 (FastAPI 实例创建)
├── tests/                        # 单元测试和集成测试
│   └── test_chat_service.py
├── .env.example                  # 环境变量配置模板
└── requirements.txt              # Python 依赖列表



If you need to comment the code, comment in Chinese.