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
     "questions": [
        {
            "questionId": "1",
            "type": "single_choice",
            "content": "",
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
    "sectionId":"",
    "questions": [
        {
            "questionId": "1",
            "type": "single_choice",
            "content": "",
            "answer": "",
        },
        {
            "questionId": "2",
            "type": "short_answer",
            "content": "",
            "answer": "",   
        },
        {
            "questionId": "3",
            "type": "code",
            "content": "",
            "answer": "",
        }
    ]
}
```

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
                "parsing": "", //LLM生成的解析
            },
            {
                "questionId": "2",
                "type": "short_answer",
                "isCorrect": true,
                "parsing": "",
            },
            {
                "questionId": "3",
                "type": "code",
                "isCorrect": true,
                "parsing": "", 
            }
        ]
    }
}
```

