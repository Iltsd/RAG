import wave
import os
from piper import PiperVoice, SynthesisConfig

def synthesize_speech(text: str, voice_model_path: str = "/home/showee/RAG/RAG4/api/tts/voices/en_US-amy-medium.onnx", output_file: str = "/home/showee/RAG/RAG4/api/tts/output/response.wav") -> str:
    """
    Синтезирует речь из текста с помощью Piper TTS и сохраняет в WAV-файл.
    
    Args:
        text (str): Текст для озвучивания (ответ от ИИ).
        voice_model_path (str): Путь к модели Piper TTS.
        output_file (str): Путь к выходному WAV-файлу.
    
    Returns:
        str: Путь к сгенерированному WAV-файлу или None при ошибке.
    """
    # Проверка входных параметров
    if not isinstance(text, str) or not text.strip():
        print("ERROR: Invalid input text: must be non-empty string.")
        return None
    if not isinstance(voice_model_path, str) or not voice_model_path.strip():
        print("ERROR: Invalid voice_model_path: must be non-empty string.")
        return None
    if not isinstance(output_file, str) or not output_file.strip():
        print("ERROR: Invalid output_file: must be non-empty string.")
        return None
    
    voice = None
    '''
    try:
        print(f"INFO: Loading Piper model from: {voice_model_path}")
        # Загрузка модели Piper TTS с использованием GPU (если доступно)
        voice = PiperVoice.load(voice_model_path, use_cuda=True)
        print("INFO: Model loaded successfully with CUDA.")
    except FileNotFoundError as e:
        print(f"ERROR: The voice model file was not found: {e}")
        return None
    except RuntimeError as e:
        print(f"WARNING: Failed to load model with CUDA: {e}. Falling back to CPU.")
    '''
    try:
        voice = PiperVoice.load(voice_model_path, use_cuda=False)
        print("INFO: Model loaded successfully with CPU fallback.")
    except Exception as fallback_e:
        print(f"ERROR: Failed to load model even with CPU fallback: {fallback_e}")
        return None
    '''
    except Exception as e:
        print(f"ERROR: Unexpected error while loading Piper model: {e}")
        return None
    '''
    
    if voice is None:
        print("ERROR: Piper model could not be loaded.")
        return None
    
    try:
        # Настройка параметров синтеза
        print("DEBUG: Configuring synthesis parameters.")
        syn_config = SynthesisConfig(
            volume=0.5,  # Уровень громкости (0.5 - половина от максимума)
            length_scale=1.0,  # Скорость речи (стандартная)
            noise_scale=1.0,  # Вариация аудио
            noise_w_scale=1.0,  # Вариация речи
            normalize_audio=False  # Использовать сырое аудио
        )
    except Exception as e:
        print(f"ERROR: Error configuring synthesis: {e}")
        return None
    
    try:
        # Создание директории, если её нет
        print(f"DEBUG: Creating directory for output file: {os.path.dirname(output_file)}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    except OSError as e:
        print(f"ERROR: Failed to create output directory: {e}")
        return None
    
    try:
        # Синтез и сохранение в WAV-файл
        print(f"INFO: Synthesizing speech for text: {text[:100]}...")
        with wave.open(output_file, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)
        print(f"INFO: Speech synthesis completed. File saved: {output_file}")
        return output_file
    except ValueError as e:
        print(f"ERROR: ValueError during synthesis: {e}")
        return None
    except OSError as e:
        print(f"ERROR: OSError while writing WAV file: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error during synthesis: {e}")
        return None
    finally:
        # Закрытие модели, если она загружена
        if voice is not None:
            try:
                del voice  # Освобождение ресурсов
                print("DEBUG: Model resources released.")
            except Exception as e:
                print(f"WARNING: Warning while releasing model resources: {e}")

# Тест: Только создание файла с озвучкой (без воспроизведения)
if __name__ == "__main__":
    response_text = "This is a test should be saved as a WAV file without playing it."
    output_path = synthesize_speech(response_text)
    if output_path and os.path.exists(output_path):
        print(f"✅ Файл с озвучкой успешно создан: {output_path}")
        print(f"Размер файла: {os.path.getsize(output_path)} байт")
    else:
        print("❌ Ошибка создания файла. Проверьте модель Piper TTS.")