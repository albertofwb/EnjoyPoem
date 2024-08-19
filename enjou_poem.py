from azure_openai_wrapper import create_text_with_openai
from config import SPEECH_CACHE_DIR
from music_object import MusicMeta
from utils import open_in_file_explorer


def main():
    prompt = '''写一首描写程序员工作成长过程的歌,以json格式返回，标准如下：
{
    "title": "文章标题",
    "content": "文章内容",
    "photo_desc": "面向 della3 编写一套用于生成对应封面的prompt"：
}
'''
    # 将对话记录写入文件
    for content in create_text_with_openai(prompt):
        music = MusicMeta(content, SPEECH_CACHE_DIR)
        music.save_content_to_text_file()
        wav_file = music.generate_audio()
        np3 = music.attach_bgm(wav_file)
        open_in_file_explorer(np3)
        input("按回车键继续")


if __name__ == '__main__':
    main()
