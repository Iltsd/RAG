import os
from typing import AsyncIterator
from piper import PiperVoice


class TTSConfig:
    def __init__(self, config: dict):
        voice_path = config.get("voice_model", "")
        self.enabled = config.get("enabled", False)
        self.voice_path = voice_path
        self.config_path = voice_path + ".json" if voice_path and not voice_path.endswith(".json") else None


class AsyncPiperTTS:
    def __init__(self, voice_model: str):
        self.voice_model = voice_model
        self.config_path = voice_model + ".json"
        self._voice = None

    def _ensure_loaded(self):
        if self._voice is None:
            if not os.path.exists(self.voice_model):
                raise FileNotFoundError(f"Voice model not found: {self.voice_model}")
            self._voice = PiperVoice.load(self.voice_model)

    async def speak(self, text: str) -> AsyncIterator[bytes]:
        self._ensure_loaded()
        for chunk in self._voice.synthesize(text):
            if chunk.audio_int16_bytes:
                yield chunk.audio_int16_bytes

    async def stop(self):
        self._voice = None


def create_tts_engine(config: dict):
    tts_config = config.get("tts", {})
    if not tts_config.get("enabled", False):
        return None
    voice_model = tts_config.get("voice_model", "")
    if not os.path.exists(voice_model):
        print(f"[TTS] Voice model not found: {voice_model}")
        return None
    return AsyncPiperTTS(voice_model)
