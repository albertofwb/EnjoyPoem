import os
import time
import pygame
from PIL import Image
import io
from mutagen.mp3 import MP3
from pydub import AudioSegment
from tqdm import tqdm
from mutagen.id3 import ID3, USLT, TALB, TPE1, SYLT, APIC
from utils import extended_seconds_to_hms
import math
from utils import get_logger
logger = get_logger("add_bgm")


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


def set_mp3_metadata(mp3_file, album=None, artist=None, cover_img=None, lyrics_file=None, create_lrc=True):
    """
    Set metadata (album, artist, cover image, lyrics) for an MP3 file

    :param mp3_file: Path to the MP3 file
    :param album: Album name (optional)
    :param artist: Artist name (optional)
    :param cover_img: Path to the cover image file (optional)
    :param lyrics_file: Path to the LRC lyrics file (optional)
    :param create_lrc: Whether to create an external LRC file (default: True)
    """
    try:
        audio = ID3(mp3_file)

        if album:
            audio['TALB'] = TALB(encoding=3, text=album)
            logger.info(f"Album set: {album}")

        if artist:
            audio['TPE1'] = TPE1(encoding=3, text=artist)
            logger.info(f"Artist set: {artist}")

        if cover_img and os.path.exists(cover_img):
            try:
                img = Image.open(cover_img)
                print(f"Image format: {img.format}, Mode: {img.mode}, Size: {img.size}")

                # Convert to RGB mode (remove alpha channel if RGBA)
                if img.mode in ('RGBA', 'LA'):
                    print("Converting RGBA image to RGB")
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    print(f"Converting {img.mode} image to RGB")
                    img = img.convert('RGB')

                # Resize image to 500x500 pixels
                img = img.resize((500, 500), Image.LANCZOS)
                print(f"Image resized to 500x500 pixels")

                # Convert image to bytes
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                img_data = buffer.getvalue()
                print(f"Image converted to JPEG, size: {len(img_data)} bytes")

                audio['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # 3 is for the cover image
                    desc='Cover',
                    data=img_data
                )
                print(f"Cover image successfully added to {mp3_file}")
            except Exception as img_error:
                print(f"Error processing cover image: {str(img_error)}")
        else:
            print(f"Cover image file not found: {cover_img}")

        if lyrics_file and os.path.exists(lyrics_file):
            logger.info(f"Adding lyrics from {lyrics_file} to {mp3_file}")
            try:
                with open(lyrics_file, 'r', encoding='utf-8') as f:
                    lrc_content = f.read()
                logger.info(f"LRC content:\n{lrc_content[:300]}...")  # logger.info first 300 characters
                logger.info(f"Total LRC length: {len(lrc_content)} characters")

                # Add unsynchronized lyrics (USLT)
                audio.add(USLT(encoding=3, lang="zho", desc="", text=lrc_content))

                # Add synchronized lyrics (SYLT)
                sylt_data = []
                for line in lrc_content.split('\n'):
                    if line.strip() and '[' in line:
                        time_str, _, content = line.partition(']')
                        time_str = time_str[1:]  # Remove leading '['
                        minutes, seconds = map(float, time_str.split(':'))
                        timestamp = int((minutes * 60 + seconds) * 1000)
                        sylt_data.append((content.strip(), timestamp))

                audio.add(SYLT(encoding=3, lang="zho", format=2, type=1, text=sylt_data))

                logger.info(f"Lyrics (USLT and SYLT) saved to MP3 file.")

                # Create external LRC file if requested
                if create_lrc:
                    lrc_output = os.path.splitext(mp3_file)[0] + '.lrc'
                    with open(lrc_output, 'w', encoding='utf-8') as f:
                        f.write(lrc_content)
                    logger.info(f"External LRC file created: {lrc_output}")

            except Exception as lyrics_error:
                logger.info(f"Error adding lyrics to MP3: {str(lyrics_error)}")
                import traceback
                logger.info(traceback.format_exc())
        else:
            logger.info(f"Lyrics file not found: {lyrics_file}")

        audio.save()
        logger.info(f"Metadata successfully saved to {mp3_file}")

        # Verify metadata
        verify_mp3_metadata(mp3_file)

    except Exception as e:
        logger.info(f"Error setting MP3 metadata: {str(e)}")
        import traceback
        logger.info(traceback.format_exc())


def verify_mp3_metadata(mp3_file):
    """
    Verify the metadata of an MP3 file

    :param mp3_file: Path to the MP3 file
    """
    try:
        audio = ID3(mp3_file)
        logger.info(f"\nVerifying metadata for {mp3_file}:")

        if 'TALB' in audio:
            logger.info(f"Album: {audio['TALB']}")
        else:
            logger.info("Album: Not set")

        if 'TPE1' in audio:
            logger.info(f"Artist: {audio['TPE1']}")
        else:
            logger.info("Artist: Not set")

        if 'APIC:' in audio:
            cover = audio['APIC:'].data
            logger.info(f"Cover image: Present (size: {len(cover)} bytes)")
        else:
            logger.info("Cover image: Not present")

        if 'USLT::zho' in audio:
            lyrics = audio['USLT::zho'].text
            logger.info(f"Lyrics: Present (length: {len(lyrics)} characters)")
            logger.info(f"Lyrics preview: {lyrics[:100]}...")  # logger.info first 100 characters
        else:
            logger.info("Lyrics: Not present")

    except Exception as e:
        logger.info(f"Error verifying MP3 metadata: {str(e)}")


def generate_timestamped_lyrics(mp3_file, lyrics_file, bgm_intro_duration=2, crossfade_duration=1):
    """
    根据 MP3 文件的时长生成带时间戳的歌词，考虑 BGM 介绍和交叉淡入

    :param mp3_file: MP3 文件路径
    :param lyrics_file: 歌词文件路径
    :param bgm_intro_duration: BGM 介绍时长（秒）
    :param crossfade_duration: 交叉淡入时长（秒）
    :return: 带时间戳的歌词列表
    """
    # 获取 MP3 文件时长
    audio = MP3(mp3_file)
    duration = audio.info.length

    # 读取歌词文件
    with open(lyrics_file, 'r', encoding='utf-8') as f:
        lyrics = f.read().splitlines()

    # 移除空行
    lyrics = [line for line in lyrics if line.strip()]

    # 计算实际歌词开始时间和持续时间
    lyrics_start_time = bgm_intro_duration + crossfade_duration
    lyrics_duration = duration - lyrics_start_time

    # 计算每行歌词的持续时间
    line_duration = lyrics_duration / len(lyrics)

    # 生成带时间戳的歌词
    timestamped_lyrics = []
    current_time = lyrics_start_time
    for line in lyrics:
        minutes = math.floor(current_time / 60)
        seconds = current_time % 60
        timestamp = f"[{minutes:02d}:{seconds:05.2f}]"
        timestamped_lyrics.append(f"{timestamp}{line}")
        current_time += line_duration

    return timestamped_lyrics

def create_lrc_file(timestamped_lyrics, output_lrc):
    """
    创建 LRC 格式的歌词文件

    :param timestamped_lyrics: 带时间戳的歌词列表
    :param output_lrc: 输出的 LRC 文件路径
    """
    with open(output_lrc, 'w', encoding='utf-8') as f:
        for line in timestamped_lyrics:
            f.write(f"{line}\n")


def add_lyrics_to_mp3(mp3_file, lrc_file):
    """
    为MP3文件添加LRC格式的歌词

    :param mp3_file: MP3文件路径
    :param lrc_file: LRC歌词文件路径
    """
    try:
        logger.info(f"Attempting to add lyrics from {lrc_file} to {mp3_file}")

        # 检查文件是否存在
        if not os.path.exists(mp3_file):
            raise FileNotFoundError(f"MP3 file not found: {mp3_file}")
        if not os.path.exists(lrc_file):
            raise FileNotFoundError(f"LRC file not found: {lrc_file}")

        # 读取LRC文件
        with open(lrc_file, 'r', encoding='utf-8') as f:
            lrc_content = f.read()
        logger.info(f"LRC content:\n{lrc_content[:300]}...")  # 打印前300个字符
        logger.info(f"Total LRC length: {len(lrc_content)} characters")

        # 添加歌词到MP3文件
        audio = ID3(mp3_file)
        audio.add(USLT(encoding=3, lang="zho", desc="", text=lrc_content))
        audio.save()
        logger.info(f"Lyrics saved to MP3 file.")

        # 验证歌词是否成功添加
        audio = ID3(mp3_file)
        if "USLT::'zho'" in audio:
            logger.info("Lyrics successfully added to the MP3 file.")
        else:
            logger.info("Warning: Lyrics were not found in the MP3 file after addition.")

    except Exception as e:
        logger.info(f"Error adding lyrics to MP3: {str(e)}")
        raise


def add_background_music(original_audio, bg_music, lyrics_file=None, output_audio=None, bg_volume=0.5, album=None,
                         artist=None, cover_img=None):
    """
    For audio file add background music and lyrics

    :param original_audio: Path to the original audio file
    :param bg_music: Path to the background music file
    :param lyrics_file: Path to the lyrics file (optional)
    :param output_audio: Path to the output audio file (optional)
    :param bg_volume: Background music volume, range 0-1 (default 0.5)
    :param album: Album name (optional)
    :param artist: Artist name (optional)
    :param cover_img: Path to the cover image file (optional)
    :return: Path to the output audio file
    """
    # Load original audio and background music
    original = load_audio(original_audio)
    background = load_audio(bg_music)

    # Adjust background music volume
    background = background - (10 * (1 - bg_volume))

    # Create a 3-second segment of background music
    bg_intro = background[:3000]  # 3000 milliseconds = 3 seconds

    # Create a crossfade effect for the transition
    crossfade_duration = 1000  # 1 second crossfade

    # Prepare the main part of the background music
    bg_main = background
    if len(bg_main) < len(original):
        bg_main = bg_main * (len(original) // len(bg_main) + 1)
    bg_main = bg_main[:len(original)]

    # Combine the intro, crossfade, and main audio
    output = bg_intro.append(original, crossfade=crossfade_duration)
    output = output.overlay(bg_main[crossfade_duration:])

    # If no output file path is specified, create a new file in the original directory
    if output_audio is None:
        original_dir = os.path.dirname(original_audio)
        original_name = os.path.splitext(os.path.basename(original_audio))[0]
        output_audio = os.path.join(original_dir, f"{original_name}_with_bgm.mp3")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)

    # Get the output file format
    output_ext = os.path.splitext(output_audio)[1].lower()
    if output_ext not in AUDIO_FORMATS:
        raise ValueError(f"Unsupported output format: {output_ext}")

    # Export the result
    output.export(output_audio, format=AUDIO_FORMATS[output_ext])

    # If lyrics file is provided, generate timestamped lyrics
    if lyrics_file:
        logger.info(f"Generating timestamped lyrics from {lyrics_file}")
        timestamped_lyrics = generate_timestamped_lyrics(output_audio, lyrics_file)
        lrc_file = os.path.splitext(output_audio)[0] + '.lrc'
        create_lrc_file(timestamped_lyrics, lrc_file)
        logger.info(f"Created LRC file: {lrc_file}")
    else:
        lrc_file = None

    # Set metadata (album, artist, cover image, lyrics)
    set_mp3_metadata(output_audio, album, artist, cover_img, lrc_file)

    return output_audio


def play_audio(file_path):
    """
    播放给定路径的音频文件，并显示进度条

    :param file_path: 音频文件的路径
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.info(f"错误：文件 '{file_path}' 不存在。")
        return

    # 初始化 pygame mixer
    pygame.mixer.init()

    try:
        # 加载音频文件
        pygame.mixer.music.load(file_path)

        # 获取音频长度（以秒为单位）
        audio = pygame.mixer.Sound(file_path)
        duration = int(audio.get_length())

        logger.info(f"正在播放: {os.path.basename(file_path)}")
        logger.info(f"音频长度: {extended_seconds_to_hms(duration)}")

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
        logger.info(f"播放音频时发生错误: {e}")
    finally:
        pygame.mixer.music.stop()
        pygame.mixer.quit()


if __name__ == '__main__':
    from config import SPEECH_CACHE_DIR, BGM_DIR
    title = "秋夜的絮语"
    original = os.path.join(SPEECH_CACHE_DIR, f"{title}_ori.wav")
    lyric = os.path.join(SPEECH_CACHE_DIR, f"{title}.txt")
    bgm = os.path.join(BGM_DIR, "default.mp3")
    output = os.path.join(SPEECH_CACHE_DIR, f"{title}_with_bgm.mp3")
    cover_img = os.path.join(SPEECH_CACHE_DIR, f"{title}.png")
    album = title
    artist = "Albert with azure"
    add_background_music(original,
                         bgm,
                         output_audio=output,
                         bg_volume=0.5,
                         album=album,
                         artist=artist,
                         cover_img=cover_img)
    play_audio(output)