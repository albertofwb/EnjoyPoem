import os
LANGUAGE = "zh-CN"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SPEECH_CACHE_DIR = os.path.join(DATA_DIR, "speech_cache")
BGM_DIR = os.path.join(DATA_DIR, "bgm")
WITH_BGM_DIR = os.path.join(DATA_DIR, "with_bgm")


class AzureVoice:
    XiaoNiWoman = 'zh-CN-shaanxi-XiaoniNeural'
    YunYeMan = "zh-CN-YunyeNeural"  # 云野 男声
    XiaoYouGirl = "zh-CN-XiaoxuanNeural"  # 小幽 女声 小孩
    Xiaomo = "zh-CN-XiaomoNeural"  # 晓墨 清晰、放松的声音，具有丰富的角色扮演和情感，适合音频书籍
    Xiaoqiu = "zh-CN-XiaoqiuNeural"
    YunzeNeuralMatualMan = "zh-CN-YunzeNeural"
