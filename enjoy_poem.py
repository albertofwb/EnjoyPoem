from add_bgm import add_background_music, play_audio
from config import DATA_DIR
from utils import get_current_time
import os
from openai import AzureOpenAI
from private_config import AzureOpenAiConfig
from speech_assistant import get_speech_instance

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


if __name__ == '__main__':
    sound_manager = get_speech_instance()
    # 初始化消息历史
    user_input = "模仿冰心的口吻，描写一个满腹才华的少女思念她在外面打工的丈夫，写一篇诗,含蓄些，在第一行给它起一个恰当的名字"
    messages = [
        {"role": "system",
         "content": user_input}
    ]

    result_path = os.path.join(DATA_DIR, "text", "stories.txt")
    while True:
        # 添加用户输入到消息历史
        messages.append({"role": "user", "content": user_input})

        # 获取AI响应
        response = chat_with_gpt4(messages)
        # 去除开头的标记
        response = response.strip('#*').strip()
        print("AI:", response)

        # 添加AI响应到消息历史
        messages.append({"role": "assistant", "content": response})

        # 语音合成和播放
        original_audio = sound_manager.get_or_create_audio(response)
        bg_music = os.path.join(DATA_DIR, "bgm", "default.mp3")
        output_path = add_background_music(original_audio, bg_music, bg_volume=0.3)
        print(f"背景音乐已添加，输出文件路径: {output_path}")
        play_audio(output_path)
        user_input = "再来一个"

        # 将对话记录写入文件
        with open(result_path, "a", encoding="utf-8") as f:
            f.write(get_current_time() + "\n")
            f.write(response + "\n")
            f.write(output_path + "\n\n")
