import json
import os
import sqlite3
import time
import re
from flask import Flask, jsonify, render_template, request, Response, stream_with_context, redirect, url_for
from multiprocessing import Pool, cpu_count
from urllib.parse import unquote
# Funciones modulares
from modulos import transcribir_audio, get_contenido, get_relevancia


app = Flask(__name__)
app.config['SECRET_KEY'] = 'key_de_prototipado'

# BD
def connect_db():
    return sqlite3.connect('database.db')

# BD c/ acceso diccionarios
def connect_db_rows():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------  SUBIDA DE ARCHIVOS ------------------------------------
UPLOAD_FOLDER = "audios"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
EXTENSIONES_PERMITIDAS = {
    'flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm'
}

def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in EXTENSIONES_PERMITIDAS

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify(success=False, error='Agregar archivos'), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, error='No hay un archivo seleccionado'), 400
    if not allowed_file(file.filename):
        return jsonify(success=False, error='Tipo de archivo no permitido'), 400

    # Guardar
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return jsonify(success=True, filename=file.filename), 200

# Obtener colecciones para mostrar en /colecciones/
def get_colecciones():
    conn   = connect_db_rows()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
          c.id,
          c.nombre,
          c.imagen,
          c.categoria,
          COUNT(a.id) AS num_audios,
          -- Todo lo que NO sea 1 ni 2 lo consideramos "alta"
          SUM(CASE WHEN a.relevancia NOT IN (1,2) THEN 1 ELSE 0 END) AS alta,
          SUM(CASE WHEN a.relevancia = 1         THEN 1 ELSE 0 END) AS media,
          SUM(CASE WHEN a.relevancia = 2         THEN 1 ELSE 0 END) AS baja,
          c.autor_creacion,
          c.fecha_creacion,
          c.autor_actualizacion,
          c.fecha_actualizacion
        FROM colecciones c
        LEFT JOIN audios a
          ON a.coleccion_id = c.id
        GROUP BY c.id
        ORDER BY c.fecha_creacion DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    colecciones = []
    for row in rows:
        d = dict(row)
        # conteo dict prioridades
        d["prioridades"] = {
            "alta":  d.pop("alta",  0),
            "media": d.pop("media", 0),
            "baja":  d.pop("baja",  0),
        }
        colecciones.append(d)

    return colecciones


@app.route('/analizar_stream/<int:coleccion_id>')
def analizar_stream(coleccion_id):
    # Leer lista de archivos
    files_param = request.args.get('files', '')
    
    # Decodificar percent-encoding
    filenames = [unquote(f) for f in files_param.split(',') if f.strip()]
    total = len(filenames)
    if total == 0:
        return jsonify(error="No hay audios para procesar"), 400

    def gen():
        conn = connect_db()
        cursor = conn.cursor()

        # Obtener modismos y jergas de la bd
        cursor.execute("SELECT * FROM modismos")
        modismos = cursor.fetchall()
        
        init_process_completo = time.time()
        for i, filename in enumerate(filenames, start=1):
            init_process  = time.time()

             # 1. enviar SSE
            payload = {
            'current': i,
            'total':   total,
            'step':    'Transcribiendo',
            'elapsed': round(time.time() - init_process, 1)
            }
            yield f"data: {json.dumps(payload)}\n\n"
          
            # 2. Transcripcion  y clasificación
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            fp, duracion, transcripcion, n_tokens, tiempo_transcripcion, velocidad, subido_por, segmentos = transcribir_audio(file_path)
            
            comex_contenido = time.time()
            payload['step']   = 'Clasificando contenido'
            payload['elapsed']= round(time.time() - init_process, 1)
            yield f"data: {json.dumps(payload)}\n\n"
            contenido  = get_contenido(transcripcion, modismos)
            tiempo_contenido = round(time.time() - comex_contenido, 1)

            comex_relevancia = time.time() 
            payload['step']   = 'Clasificando relevancia'
            payload['elapsed']= round(time.time() - init_process, 1)
            yield f"data: {json.dumps(payload)}\n\n"
            relevancia = get_relevancia(transcripcion, modismos)
            tiempo_relevancia = round(time.time() - comex_relevancia)

            tiempo_analisis_audio = round(time.time() - init_process, 1)
            # 3. Guardar en BD
            if transcripcion is not None:
                archivo = os.path.basename(fp)
                cursor.execute("""
                    INSERT INTO audios(
                        archivo, estado, duracion, transcripcion,
                        n_tokens, tiempo, velocidad, coleccion_id, fecha_creacion, subido_por, transcripcion_segmentos, contenido, relevancia,
                        tiempo_transcripcion, tiempo_contenido, tiempo_relevancia       
                    ) VALUES (?, 'procesado', ?, ?, ?, ?, ?, ?, current_timestamp, ?, ?, ?, ?, ?, ?, ?)
                """, (archivo, duracion, transcripcion, n_tokens, tiempo_analisis_audio, 
                      velocidad, coleccion_id, subido_por, segmentos, contenido, relevancia,
                      tiempo_transcripcion, tiempo_contenido, tiempo_relevancia))
                conn.commit()

        # 4. Aviso proceso completado (uso SSE)
        total_elapsed = time.time() - init_process_completo
        minutos, segundos = divmod(total_elapsed, 60)
        minutos = int(minutos)
        segundos = int(segundos)

        payload = {
        'done': True,
        'elapsed': f"{minutos}m {segundos}s"
        }
        yield f"data: {json.dumps(payload)}\n\n"

        conn.close()

    return Response(
        stream_with_context(gen()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache'}
    )

# Agregar nueva colección 
@app.route('/guardar_coleccion', methods=['POST'])
def guardar_coleccion():
    data = request.json  
    prioridades_dict = {"urgente": 0, "alta": 0, "media": 0, "baja": 0}

    nombre = data.get("nombre")
    imagen = data.get("imagen")
    categoria = data.get("categoria")
    prioridades = json.dumps(prioridades_dict)  
    autor_creacion = data.get("autor_creacion", "Desconocido")

    if not nombre or not categoria:
        return jsonify({"success": False, "message": "Nombre y categoría son obligatorios"}), 400

    conn = connect_db_rows()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO colecciones (nombre, imagen, categoria, audios, prioridades, autor_creacion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, imagen, categoria, 0, prioridades, autor_creacion))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Colección agregada exitosamente"}), 200

# Obtener audios de una coleccion
def get_audios(coleccion_id):
    conn   = connect_db_rows()
    cursor = conn.cursor()
    cursor.execute("""
      SELECT a.id, a.archivo, a.duracion, a.transcripcion, a.contenido, a.relevancia, a.n_tokens, a.fecha_creacion, a.velocidad, a.tiempo,
             c.nombre AS coleccion, c.categoria
      FROM audios a
      JOIN colecciones c ON a.coleccion_id = c.id
      WHERE c.id = ?
      ORDER BY a.id DESC
    """, (coleccion_id,))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

# Obtener un audio específico
def get_audio(audio_id):
    conn   = connect_db_rows()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.id,
            a.archivo,
            a.estado,
            a.duracion,
            a.transcripcion,
            a.n_tokens,
            a.tiempo,
            a.velocidad,
            a.contenido,
            a.relevancia,
            a.fecha_creacion,
            a.coleccion_id,
            a.transcripcion_segmentos,
            a.subido_por,
            a.tiempo_transcripcion,
            a.tiempo_contenido,
            a.tiempo_relevancia,
            c.nombre   AS coleccion_nombre,
            c.categoria AS coleccion_categoria
        FROM audios a
        JOIN colecciones c
          ON a.coleccion_id = c.id
        WHERE a.id = ?
    """, (audio_id,))
    audio = cursor.fetchone()
    conn.close()
    return audio

def get_modismos():
    conn   = connect_db_rows()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM modismos")
    modismos = cursor.fetchall()
    conn.close()

    return modismos

@app.route('/add_modismo', methods=['POST'])
def add_modismo():
    data = request.form.to_dict()
    expresion, significado, region = data.get('expresion'), data.get('significado'), data.get('region')
    conn = connect_db_rows()
    conn.execute("INSERT INTO modismos (expresion, significado, region) VALUES (?, ?, ?)", (expresion, significado, region))
    conn.commit()
    conn.close()
    return redirect(url_for('modismos'))

@app.route('/delete_modismo', methods=['POST'])
def delete_modismo():
    data = request.form.getlist('ids')
    if not data:
        return redirect(url_for('modismos'))
    
    placeholders = ','.join('?' for _ in data)
    conn = connect_db_rows()
    conn.execute(
    f"DELETE FROM modismos WHERE id IN ({placeholders})", tuple(data))
    conn.commit()
    conn.close()
    return redirect(url_for('modismos'))


# Rutas 
@app.route('/')
def index():
    colecciones = get_colecciones()
    return render_template('index.html', colecciones=colecciones)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/colecciones')
def colecciones():
    colecciones = get_colecciones()
    return render_template('colecciones.html', colecciones=colecciones)

@app.route('/colecciones/<int:coleccion_id>')
def audios(coleccion_id):
    audios = get_audios(int(coleccion_id))
    n_audios = len(audios)
    return render_template('audios.html', audios=audios, n_audios=n_audios)

@app.route('/colecciones/audios/<int:audio_id>')
def detalles_audio(audio_id):
    audio = get_audio(audio_id)
    text = audio['transcripcion']
    # dividir tras cada punto/pregunta/exclamación + espacio
    oraciones = re.split(r'(?<=[\.!?])\s+', text)
    return render_template(
        'detalles_audio.html',
        audio=audio,
        oraciones=oraciones
    )

@app.route('/modismos')
def modismos():
    modismos = get_modismos()
    return render_template('modismos.html', modismos=modismos)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
