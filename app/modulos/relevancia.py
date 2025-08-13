import joblib
from pathlib import Path
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
MODELO_PATH = BASE_DIR / 'modulos/modelo_kmeans.joblib'
USAR_MODISMOS = False # Activar/desactivar modismos y jerga


kmeans = joblib.load(str(MODELO_PATH)) # modelo propio
modelo = SentenceTransformer('distiluse-base-multilingual-cased-v1') # modelo de embeddings

# Clasificar por relevancia
def get_relevancia(texto, modismos):
    if USAR_MODISMOS:
        for modismo in (modismos or []):
            texto.replace(modismo[1], modismo[2])

    embedding = modelo.encode([texto]) 
    prediccion = kmeans.predict(embedding)

    return int(prediccion[0]) # 0: Alta, 1: Media, 2: Baja
