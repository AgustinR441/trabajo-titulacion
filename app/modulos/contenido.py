import ollama
import torch
import re
from pathlib import Path

# Activar/desactivar modismos y jerga
USAR_MODISMOS = False

# Importar archivo con las categorías predefinidas
ARCHIVO_CATEGORIAS = Path("categorias.csv")

# Parámetro para ajustar el máximo de palabras para una 'nueva' categoría
n = 2 

# CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def cargar_categorias():
    with ARCHIVO_CATEGORIAS.open("r", encoding="utf-8") as f:
        return [linea.strip() for linea in f if linea.strip()]

def agregar_categoria_si_nueva(etiqueta):
    existentes = set(cargar_categorias())
    if etiqueta not in existentes:
        with ARCHIVO_CATEGORIAS.open("a", encoding="utf-8") as f:
            f.write(etiqueta + "\n")

# DeepSeek
def get_contenido(texto, modismos=None):
    if USAR_MODISMOS:
        for modismo in (modismos or []):
            print()
            texto = texto.replace(modismo[1], modismo[2])

    categorias = cargar_categorias()
    lista_categorias = "\n".join(f"- {c}" for c in categorias)
    
    prompt = f"""
    Responde SOLO en español.

    Tarea: CLASIFICACIÓN. 
    Recibirás un texto y una lista FINITA de categorías permitidas.
    Devuelve EXACTAMENTE UNA etiqueta:
    1) Si alguna categoría de la lista calza con el contenido principal, responde solo esa categoría (idéntica).
    2) Si ninguna calza, propone una nueva etiqueta de máximo {n} palabra(s), en minúsculas y sin puntuación.
    No expliques nada. Responde solo la etiqueta final.

    Categorías permitidas:
    {lista_categorias}

    Transcripción:
    INICIO
    {texto}
    FIN
    """

    # DeepSeek en local. 7b, 8b, 14b
    respuesta = ollama.chat(model="deepseek-r1:14b", messages=[{"role": "user", "content": prompt}])
    contenido = respuesta.message.content
    resp_limpia = re.sub(r"<think>.*?</think>\s*", "", contenido, flags=re.DOTALL)

    agregar_categoria_si_nueva(resp_limpia)
    return resp_limpia