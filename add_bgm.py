import os
import time
import pygame
from pydub import AudioSegment
from tqdm import tqdm

from config import DATA_DIR, BGM_DIR
from utils import extended_seconds_to_hms

# 定义支持的音频格式常量
AUDIO_FORMATS = {
    '.wav': 'wav',
    '.mp3': 'mp3',
    '.ogg': 'ogg',
    '.flac': 'flac',
    '.aac': 'aac',
    '.m4a': 'm4a',
    '.wma': 'wma'
}


def load_audio(file_path):
    """加载音频文件"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {ext}")
    return AudioSegment.from_file(file_path, format=AUDIO_FORMATS[ext])


def add_background_music(original_audio, bg_music, output_audio=None, bg_volume=0.5):
    """
    为音频文件添加背景音乐

    :param original_audio: 原始音频文件路径
    :param bg_music: 背景音乐文件路径
    :param output_audio: 输出音频文件路径（可选）
    :param bg_volume: 背景音乐音量，范围0-1（默认0.5）
    :return: 输出音频文件路径
    """
    # 加载原始音频和背景音乐
    original = load_audio(original_audio)
    background = load_audio(bg_music)

    # 调整背景音乐音量
    background = background - (10 * (1 - bg_volume))

    # 如果背景音乐比原始音频短，则循环播放直到长度匹配
    if len(background) < len(original):
        background = background * (len(original) // len(background) + 1)

    # 裁剪背景音乐以匹配原始音频长度
    background = background[:len(original)]

    # 混合音频
    output = original.overlay(background)

    # 如果没有指定输出文件路径，则在原始文件的目录中创建一个新文件
    if output_audio is None:
        original_dir = os.path.dirname(original_audio)
        original_name = os.path.splitext(os.path.basename(original_audio))[0]
        output_audio = os.path.join(original_dir, f"{original_name}_with_bgm.mp3")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)

    # 获取输出文件格式
    output_ext = os.path.splitext(output_audio)[1].lower()
    if output_ext not in AUDIO_FORMATS:
        raise ValueError(f"Unsupported output format: {output_ext}")

    # 导出结果
    output.export(output_audio, format=AUDIO_FORMATS[output_ext])

    return output_audio


def play_audio(file_path):
    """
    播放给定路径的音频文件，并显示进度条

    :param file_path: 音频文件的路径
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在。")
        return

    # 初始化 pygame mixer
    pygame.mixer.init()

    try:
        # 加载音频文件
        pygame.mixer.music.load(file_path)

        # 获取音频长度（以秒为单位）
        audio = pygame.mixer.Sound(file_path)
        duration = int(audio.get_length())

        print(f"正在播放: {os.path.basename(file_path)}")
        print(f"音频长度: {extended_seconds_to_hms(duration)}")

        # 播放音频
        pygame.mixer.music.play()
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}",

        # 创建进度条，使用自定义格式化函数确保显示整数
        with tqdm(total=duration, unit="sec", bar_format=bar_format,
                  ncols=100,  # 设置进度条的总宽度
                  # 使用 lambda 函数确保 n 和 total 都显示为整数
                  unit_scale=False, unit_divisor=0.2) as pbar:
            start_time = time.time()
            while pygame.mixer.music.get_busy():
                elapsed_time = round(time.time() - start_time)
                pbar.n = elapsed_time
                pbar.refresh()
                time.sleep(0.1)
    except pygame.error as e:
        print(f"播放音频时发生错误: {e}")
    finally:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
