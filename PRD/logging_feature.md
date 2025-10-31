#  AI 练一练日志记录需求文档（JSONL 格式）

## 一、日志目标

AI 练一练模块的日志用于追踪 **出题 → 答题 → 判题** 的完整流程，
以便于后期进行：

* LLM 题目生成效果评估
* 用户答题行为分析
* 模型判题准确率与响应延迟分析
* 结果可重现与溯源

---

## 二、文件结构

每位用户独立目录，每个练习 session 对应一个日志文件。session来自API请求中的sessionId。

```
logs/
  user_{user_id}/
    session_{session_id}.jsonl
```

* **user_id**：用户唯一标识
* **session_id**：一次练习的唯一标识
* 文件后缀固定为 `.jsonl`
* 每行一个 JSON 对象

---

## 三、文件内容结构

日志文件分为两部分：

1. **Meta 信息行**（第 1 行，仅出现一次）
2. **事件记录行**（第 2 行起，若干条）

---

### （1）Meta 信息行

> 用于描述当前练习的上下文信息，仅写一次。

```json
{
  "meta": {
    "session_id": "session_20251029_001",
    "user_id": "user_123",
    "book_name": "Python入门",
    "book_introduction": "为零基础学习者设计的Python入门课程。",
    "section_id": "sec_abc123",
    "section_content": "在Python中，变量用于存储数据。变量名可以由字母、数字和下划线组成……",
    "start_time": "2025-10-29T18:00:00+08:00",
    "version": "v1.0.0"
  }
}
```

#### 字段说明

| 字段名               | 类型     | 说明                 |
| ----------------- | ------ | ------------------ |
| session_id        | string | 当前练习唯一标识           |
| user_id           | string | 用户标识               |
| book_name         | string | 书名                 |
| book_introduction | string | 书籍简介               |
| section_id        | string | 小节 ID              |
| section_content   | string | 小节正文（作为 LLM 出题上下文） |
| start_time        | string | Session 开始时间       |
| version           | string | 日志格式版本号            |

---

### （2）事件记录行

每个事件为一行 JSON，包含以下基本字段：

```json
{
  "event_type": "generate",
  "timestamp": "2025-10-29T18:03:00+08:00",
  "data": { ... }
}
```

#### 通用字段说明

| 字段名        | 类型     | 说明                      |
| ---------- | ------ | ----------------------- |
| event_type | string | 事件类型（见下表）               |
| timestamp  | string | 事件时间戳                   |
| data       | object | 事件数据体，结构依 event_type 而定 |

---

## 四、事件类型定义

### 1️⃣ 出题事件（`event_type = "generate"`）

记录 LLM 生成的题目信息及模型元数据。

```json
{
  "event_type": "generate",
  "timestamp": "2025-10-29T18:03:00+08:00",
  "data": {
    "latency_ms": 3150,
    "summary": "在Python中，变量用于存储数据。变量名可以由字母、数字和下划线组成……",
    "questions": [
      {
        "question_id": "1",
        "type": "single_choice",
        "content": "在python中，哪个关键字用于定义函数？",
        "options": [
          { "optionId": "A", "text": "def" },
          { "optionId": "B", "text": "function" },
          { "optionId": "C", "text": "func" },
          { "optionId": "D", "text": "define" }
        ]
      },
      {
        "question_id": "2",
        "type": "short_answer",
        "content": "解释Python的缩进规则。"
      }
    ]
  }
}
```

---

### 2️⃣ 用户答题事件（`event_type = "answer"`）

记录用户提交的答案。

```json
{
  "event_type": "answer",
  "timestamp": "2025-10-29T18:07:11+08:00",
  "data": {
    "answers": [
      {"question_id": "1", "type": "single_choice", "answer": ""},
      {"question_id": "2", "type": "short_answer", "answer": "通过缩进区分代码块"}
    ]
  }
}
```

---

### 3️⃣ 判题事件（`event_type = "judge"`）

记录 LLM 对用户答案的判定结果与解析。

```json
{
  "event_type": "judge",
  "timestamp": "2025-10-29T18:08:55+08:00",
  "data": {
    "latency_ms": 2500,
    "results": [
      {
        "question_id": "1",
        "is_correct": true,
        "parsing": "正确答案是def，用于定义函数。"
      },
      {
        "question_id": "2",
        "is_correct": true,
        "parsing": "缩进用于表示代码块层级。"
      }
    ]
  }
}
```

