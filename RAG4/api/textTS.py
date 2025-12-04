import wave
import os
from piper import PiperVoice, SynthesisConfig

def synthesize_speech(text: str, voice_model_path: str = "/home/showee/RAG/RAG4/api/tts/voices/en_US-amy-medium.onnx", output_file: str = "/home/showee/RAG/RAG4/api/tts/output/response.wav") -> str:

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

    try:
        voice = PiperVoice.load(voice_model_path, use_cuda=False)
        print("INFO: Model loaded successfully with CPU fallback.")
    except Exception as fallback_e:
        print(f"ERROR: Failed to load model even with CPU fallback: {fallback_e}")
        return None
  
    if voice is None:
        print("ERROR: Piper model could not be loaded.")
        return None
    
    try:
        print("DEBUG: Configuring synthesis parameters.")
        syn_config = SynthesisConfig(
            volume=0.5, 
            length_scale=1.0,  
            noise_scale=1.0,  
            noise_w_scale=1.0,  
            normalize_audio=False 
        )
    except Exception as e:
        print(f"ERROR: Error configuring synthesis: {e}")
        return None
    
    try:
        print(f"DEBUG: Creating directory for output file: {os.path.dirname(output_file)}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    except OSError as e:
        print(f"ERROR: Failed to create output directory: {e}")
        return None
    
    try:
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
        if voice is not None:
            try:
                del voice  
                print("DEBUG: Model resources released.")
            except Exception as e:
                print(f"WARNING: Warning while releasing model resources: {e}")


if __name__ == "__main__":
    response_text = "This is a test should be saved as a WAV file without playing it."
    output_path = synthesize_speech(response_text)
    if output_path and os.path.exists(output_path):
        print(f" Файл с озвучкой успешно создан: {output_path}")
        print(f"Размер файла: {os.path.getsize(output_path)} байт")
    else:
        print(" Ошибка создания файла. Проверьте модель Piper TTS.")