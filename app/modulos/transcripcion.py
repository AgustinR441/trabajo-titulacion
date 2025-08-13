import time
import json
import torch
import whisper
import ffmpeg

_MODEL = whisper.load_model("small", device="cuda")

# Obtener la duración del audio
def get_audio_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return round(float(probe['format']['duration']), 2)
    except Exception as e:
        print(f"❌ Error obteniendo duración del audio: {e}")
        return None
    
# Transcribir un audio
def transcribir_audio(file_path):
    try:
        torch.cuda.empty_cache()
        duracion = get_audio_duration(file_path)
        inicio = time.time()
        result = _MODEL.transcribe(file_path)
        tiempo_ejecucion = round(time.time() - inicio, 2)
        transcripcion = result["text"]
        n_tokens = len(transcripcion.split())
        velocidad = round(n_tokens / tiempo_ejecucion, 2) if tiempo_ejecucion > 0 else 0
        subido_por = "Agustín Riquelme"                 #
        segmentos = json.dumps(result["segments"], ensure_ascii=False, indent=2)  

        return (file_path, duracion, transcripcion, n_tokens, tiempo_ejecucion, velocidad, subido_por, segmentos)
    
    except Exception as e:
        print(f"❌ Error en la transcripción de {file_path}: {e}")
        return (file_path, None, None, None, None, None)
