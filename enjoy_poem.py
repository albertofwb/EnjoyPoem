from add_bgm import add_background_music, play_audio
from config import DATA_DIR, SPEECH_CACHE_DIR
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
    user_input = "模仿冰心的口吻写一篇诗,含蓄些，在第一行给它起一个恰当的名字"
    messages = [
        {"role": "system",
         "content": user_input}
    ]

    while True:
        # 添加用户输入到消息历史
        messages.append({"role": "user", "content": user_input})

        # 获取AI响应
        response = chat_with_gpt4(messages)
        # remove any # * from the whole response
        pure_text = response.replace("#", "").replace("*", "")
        # 去除开头的标记
        title = pure_text.split("\n")[0].strip()
        # 将对话记录写入文件
        result_path = os.path.join(SPEECH_CACHE_DIR, title+".md")
        with open(result_path, "a", encoding="utf-8") as f:
            f.write(get_current_time() + "\n")
            f.write(response + "\n\n")
        print("AI:", pure_text)

        # 添加AI响应到消息历史
        messages.append({"role": "assistant", "content": pure_text})

        # 语音合成和播放
        original_wav_path = os.path.join(SPEECH_CACHE_DIR, title + ".wav")
        original_audio = sound_manager.get_or_create_audio(pure_text, save_path=original_wav_path)
        bg_music = os.path.join(DATA_DIR, "bgm", "default.mp3")
        music_path = os.path.join(SPEECH_CACHE_DIR, title + ".mp3")
        output_path = add_background_music(original_audio, bg_music, output_audio=music_path, bg_volume=0.3)
        print(f"背景音乐已添加，输出文件路径: {output_path}")
        play_audio(output_path)
        user_input = "再来一个"
