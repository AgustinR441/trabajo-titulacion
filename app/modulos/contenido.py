import ollama
import torch
import re

# Activar/desactivar modismos y jerga
USAR_MODISMOS = False

# CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# DeepSeek
def get_contenido(texto, modismos):
    if USAR_MODISMOS:
        for modismo in (modismos or []):
            print()
            texto = texto.replace(modismo[1], modismo[2])

    prompt = f"""
    Responde solamente en idioma español.
    Analiza el siguiente texto (entre INICIO TEXTO y FIN TEXTO) y clasificalo según su contenido. Da lo mismo el largo del texto, solo describe su contenido de forma muy específica en un máximo de 10 palabras. 
    Devuelve solamente el contenido, sin explicaciones ni ningún texto adicional. 
    INICIO TEXTO
    {texto}
    FIN TEXTO
    Recuerda contestar en español y darme su contenido de forma muy específica en MÁXIMO 10 palabras.
    """
    # DeepSeek en local. 7b, 8b, 14b
    respuesta = ollama.chat(model="deepseek-r1:14b", messages=[{"role": "user", "content": prompt}])
    contenido = respuesta.message.content
    resp_limpia = re.sub(r"<think>.*?</think>\s*", "", contenido, flags=re.DOTALL)

    return resp_limpia



