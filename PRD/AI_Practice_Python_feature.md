AI 练一练 内部接口 API 设计文档

Go 服务调用 Python 服务

## API 设计

### 创建练习题

POST:  internal/ai/practice/generate

```json
{
    "sessionId":"",  
    "userId":"",
    "sectionId":"",
    "bookName":"",
    "bookIntroduction":"",
    "sectionContent":"",
}
```

Response:
```json
{
    "code":200,
    "message":"success",
    "data":{
     "summary": "",
     "questions": [
        {
            "questionId": "1",
            "type": "single_choice",
            "content": "",
            "options": [
                { "optionId": "a", "text": "选项A内容" },
                { "optionId": "b", "text": "选项B内容" },
                { "optionId": "c", "text": "选项C内容" },
                { "optionId": "d", "text": "选项D内容" }
            ]
        },
        {
            "questionId": "2",
            "type": "short_answer",
            "content": "",
        },
        {
            "questionId": "3",
            "type": "code",
            "content": "",
        }
    ]
}
}

```

### 提交答案

POST internal/ai/practice/verify

请求体:

```json
{
    "sessionId":"",
    "userId":"",
    "questions": [
        {
            "questionId": "1",
            "type": "single_choice",
            "answer": "",
        },
        {
            "questionId": "2",
            "type": "short_answer",
            "answer": "",   
        },
        {
            "questionId": "3",
            "type": "code",
            "answer": "",
        }
    ]
}
```

> 题目内容不再由调用方提交，Python 服务会使用 `sessionId` 和 `userId` 在会话日志中查询最近一次生成的题面，并将题面与用户答案进行比对。
> Python 服务会在生成题目时自动产出 `summary`，判题阶段会将该摘要注入提示词，以提高判题准确性。

Response:
```json
{
    "code":200,
    "message":"success",
    "data":{
        "questions": [
            {
                "questionId": "1",
                "type": "single_choice",
                "isCorrect": true,
                "userAnswer": { "selectedOptionId": "b" },
                "correctAnswer": { "optionId": "b" },
                "parsing": "LLM生成的解析"
            },
            {
                "questionId": "2",
                "type": "short_answer",
                "isCorrect": true,
                "userAnswer": { "answerText": "用户提交的答案文本" },
                "correctAnswer": { "answerText": "参考答案文本" },
                "parsing": "LLM生成的解析"
            },
            {
                "questionId": "3",
                "type": "code",
                "isCorrect": true,
                "userAnswer": { "codeText": "用户提交的代码" },
                "correctAnswer": { "codeText": "参考代码或空字符串" },
                "parsing": "LLM生成的解析"
            }
        ]
    }
}
```
