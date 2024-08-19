import os
from openai import AzureOpenAI
from private_config import AzureOpenAiConfig

# 设置环境变量
os.environ["AZURE_OPENAI_ENDPOINT"] = AzureOpenAiConfig.azure_endpoint
os.environ["AZURE_OPENAI_API_KEY"] = AzureOpenAiConfig.api_key

client = AzureOpenAI(
    api_version=AzureOpenAiConfig.api_version,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)


def chat_with_gpt4(messages):
    try:
        response = client.chat.completions.create(
            model=AzureOpenAiConfig.model_name,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_text_with_openai(user_input: str):
    messages = [
        {"role": "system",
         "content": user_input}
    ]

    while True:
        # 添加用户输入到消息历史
        messages.append({"role": "user", "content": user_input})
        # 获取AI响应
        response = chat_with_gpt4(messages)
        yield response
        messages.append({"role": "assistant", "content": messages})
