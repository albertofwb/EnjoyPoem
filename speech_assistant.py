import os
import hashlib
import azure.cognitiveservices.speech as speechsdk
import pygame

from add_bgm import add_background_music, play_audio
from config import SPEECH_CACHE_DIR, LANGUAGE, AzureVoice, DATA_DIR
from private_config import AzureOpenAiConfig
from utils import get_logger
logger = get_logger("speech_assistant")


class SpeechAssistant:
    def __init__(self, speech_key, speech_region, output_dir, human):
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.speech_human = human
        self.output_dir = output_dir
        self.speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region)
        self.speech_config.speech_synthesis_voice_name = self.speech_human

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_hash(self, text):
        return hashlib.md5(text.encode()).hexdigest()

    def _get_file_path(self, text):
        hash_value = self._get_hash(text.strip())
        return os.path.join(self.output_dir, f"{hash_value}_{self.speech_human}.wav")

    def get_or_create_audio(self, text, save_path=None):
        if save_path is None:
            file_path = self._get_file_path(text)
            if os.path.exists(file_path):
                logger.info(f"Using existing audio file: {file_path}")
                return file_path
        else:
            file_path = save_path
        logger.info(f"Generating new audio file: {file_path}")
        self._generate_audio(text, file_path)
        return file_path

    def _generate_audio(self, text, file_path):
        audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info(f"Speech synthesized and saved to file '{file_path}'")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.warning("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logger.error("Error details: {}".format(cancellation_details.error_details))

    def play_sound(self, text):
        pygame.mixer.init()
        file_path = self.get_or_create_audio(text)
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except pygame.error as e:
            logger.info(f"Error playing sound: {e}")

    def get_hear_text(self):
        # Creates a recognizer with the given settings
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, language=LANGUAGE)
        logger.info("Say something: ")
        result = speech_recognizer.recognize_once()
        # Checks result.
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info("Recognized: {}".format(result.text))
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.warning("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error("Error details: {}".format(cancellation_details.error_details))


def get_speech_instance() -> SpeechAssistant:
    return SpeechAssistant(
            AzureOpenAiConfig.SPEECH_KEY,
            AzureOpenAiConfig.AzureLocation,
            SPEECH_CACHE_DIR,
            AzureVoice.Xiaoqiu)


# Example usage:
if __name__ == '__main__':
    sound_manager = get_speech_instance()
    poem = '床前明月光，疑是地上霜。'
    original_audio = sound_manager.get_or_create_audio(poem)
    bg_music = os.path.join(DATA_DIR, "bgm", "default.mp3")
    output_path = add_background_music(original_audio, bg_music, bg_volume=0.3)
    print(f"背景音乐已添加，输出文件路径: {output_path}")
    play_audio(output_path)