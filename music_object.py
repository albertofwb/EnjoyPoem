import json
import os
from types import SimpleNamespace
from add_bgm import add_background_music
from azure_dalle3 import generate_img_with_dalle3
from config import SPEECH_CACHE_DIR, BGM_DIR, DATA_DIR
from speech_assistant import get_speech_instance
from utils import get_logger

logger = get_logger("music_object")


def p():
    j = '''
{
    "title": "晨曦中的花瓣",
    "content": "晨曦露珠微，羞涩花瓣垂。\\n天光渐映晚，\\n柔情绕心扉。\\n\\n未笺孤影寂，\\n思绪何人随？\\n愿君回首处，\\n有我盈盈泪。",
    "photo_desc": "Create a soft, pastel-hued sunrise scene with delicate dew-covered petals of a flower just about to bloom. Capture the gentle light filtering through, casting a tender glow on the flower and background. The atmosphere should feel serene and imbued with a quiet, reflective emotion."
}'''
    d = json.loads(j, object_hook=lambda d: SimpleNamespace(**d))
    print(d.title)
    print(d.content)
    print(d.photo_desc)


class MusicMeta:
    def __init__(self, response: str, cache_dir: str):
        self.response = response
        self.cache_dir = cache_dir
        self.parse_response(response)
        response_file = os.path.join(self.cache_dir, self.title + ".json")
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(response)
        self.bg_music_edition_path = None
        self.wav_path = None

    def parse_response(self, content: str):
        print(content)
        obj = json.loads(content, object_hook=lambda d: SimpleNamespace(**d))
        self.title = obj.title
        self.content = obj.content
        self.photo_desc = obj.photo_desc
        self.full_text = f"{self.title}\n{self.content}"
        with open(os.path.join(self.cache_dir, self.title + ".txt"), "w", encoding="utf-8") as f:
            f.write(self.full_text)

    def save_content_to_text_file(self):
        self.text_path = os.path.join(self.cache_dir, self.title + ".txt")
        with open(self.text_path, "a", encoding="utf-8") as f:
            f.write(self.full_text)

    def generate_audio(self) -> str:
        sound_manager = get_speech_instance()
        wav_path = os.path.join(SPEECH_CACHE_DIR, self.title + "_ori.wav")
        sound_manager.get_or_create_audio(self.full_text, save_path=wav_path)
        return wav_path

    def attach_bgm(self, original_wav_path: str) -> str:
        bg_music = os.path.join(BGM_DIR, "default.mp3")
        cover_png = os.path.join(DATA_DIR, f"{self.title}.png")
        if not os.path.exists(cover_png):
            generate_img_with_dalle3(self.photo_desc, cover_png)
        output_path = add_background_music(original_wav_path,
                                           bg_music,
                                           bg_volume=0.3,
                                           cover_img=cover_png,
                                           lyrics_file=self.text_path,
                                           artist="azure"
                                           )
        logger.info(f"背景音乐已添加，输出文件路径: {output_path}")
        self.bg_music_edition_path = output_path
        return output_path


if __name__ == '__main__':
    p()
