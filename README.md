# Trabajo de Titulación

Este repositorio explica la instalación y despliegue local del prototipo de software desarrollado como trabajo de titulación del Teniente Segundo Agustín Riquelme Duque, cuyo tema es:
**Transcripción y clasificación automática de audios según su contenido y relevancia.**

Contacto
- ariquelmed@asdjas.com
- +569 1234568789

## Tabla de contenidos

- [Requisitos técnicos](#requisitos-tecnicos)
  - [Instalar WSL2 en Windows](#instalar-wsl2-en-windows)
  - [Instalar CUDA Toolkit (Windows y Linux)](#instalar-cuda-toolkit-windows-y-linux)
  - [Instalar FFmpeg](#instalar-ffmpeg)
  - [Instalar PyTorch con CUDA](#instalar-pytorch-con-cuda)
- [Instalación del prototipo](#instalacion-local)
- [Configuración de la base de datos](#configuracion-de-la-base-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Uso](#uso)
  - [Interfaz web](#interfaz-web)
  - [API de subida y análisis](#api-de-subida-y-analisis)
- [Dockerización](#dockerizacion)
- [Licencia](#licencia)

---

<a id="requisitos-tecnicos"></a>
## Requisitos técnicos

- **Sistema operativo:** Linux o Windows 10/ Windows 11 (con **WSL2** en caso de usar Docker).
- **Python:** ≥ 3.9. 
- **FFmpeg:** Requerido para el manejo de audio.
- **GPU NVIDIA con soporte CUDA**. 
- **VRAM mínima recomendada:** 8 GB.
- **Drivers NVIDIA** + **CUDA Toolkit** compatibles con su versión de PyTorch.
- **Docker y Docker Compose** (opcional): Para despliegue en contenedores (recomendado).

> Se recomienda ejecutar el proyecto usando **Docker** para reproducibilidad (con **WSL2** si usa **Windows**) .

<a id="instalar-wsl2-en-windows"></a>
### Instalar WSL2 en Windows (obligatorio solo para ejecución usando **Docker**)

En **Windows 10/ Windows 11**, ejecutar PowerShell como Administrador:

```powershell
wsl --install -d Ubuntu
wsl --set-default-version 2
```

Si su Windows no soporta el comando anterior, debe habilitar manualmente y reiniciar:

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
```

Tras reiniciar, instale **Ubuntu** desde Microsoft Store o con:
```powershell
wsl --install -d Ubuntu
```

Luego, abrir Ubuntu (WSL) y continúe con las instrucciones para **Linux**.

<a id="instalar-cuda-toolkit-windows-y-linux"></a>
### Instalar CUDA Toolkit (Windows y Linux)

**Windows (controlador + toolkit):**
1. Instalar el **driver NVIDIA** más reciente para su GPU.
2. Descargar e instalar **CUDA Toolkit** desde el <a href="https://developer.nvidia.com/cuda-toolkit">sitio oficial de NVIDIA</a>.
3. Verifique la instalación:
   ```powershell
   nvcc --version
   ```

**Linux (Ubuntu/Debian):**
- Opción rápida:
  ```bash
  sudo apt-get update
  sudo apt-get install -y nvidia-cuda-toolkit
  nvcc --version
  ```
- O usar el <a href="https://developer.download.nvidia.com/compute/cuda/repos/">instalador oficial de NVIDIA</a> si necesita una versión específica del toolkit.

<a id="instalar-ffmpeg"></a>
### Instalar FFmpeg

**Windows**
  ```powershell
  winget install Gyan.FFmpeg
  ffmpeg -version
 ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
ffmpeg -version
```

<a id="instalar-pytorch-con-cuda"></a>
### Instalar PyTorch con CUDA

#### 1) Verificar la versión de CUDA que soporta su driver

```bash
nvidia-smi
```
#### 2) Instalar la versión de PyTorch con CUDA que corresponde
> Ajuste `cuXYZ` a la versión de CUDA soportada (por ejemplo, `cu121`).
```bash
pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cuXYZ
```

#### 3) Verificar la instalación

Para verificar que PyTorch detecte su GPU, cree un archivo `.py` con el siguiente código:
```python
import torch
print("CUDA disponible:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")
```
Si esta detectando la GPU, esto imprimirá en pantalla `CUDA disponible: True` y la GPU detectada.

---

<a id="instalacion-local"></a>
## Instalación del prototipo

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/AgustinR441/trabajo-titulacion
   cd trabajo-titulacion
   ```

2. **Crear y activar un entorno virtual**

   - Windows 
      ```powershell
      python3 -m venv venv
      venv\Scripts\activate
      ```

   - Linux (Ubuntu/Debian):
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

   
3. **Instalar dependencias**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Crear carpeta para audios**
   ```bash
   mkdir audios
   ```

5. **Instalar FFmpeg y PyTorch con CUDA si no usa Docker**
   - Ver secciones: [Instalar FFmpeg](#instalar-ffmpeg) y [Instalar PyTorch con CUDA](#instalar-pytorch-con-cuda)

El proyecto utiliza las siguientes dependencias (definidas en `requirements.txt`):
```txt
Flask>=2.0
ffmpeg-python
openai-whisper
ollama
sentence-transformers>=2.2.0
joblib
scikit-learn==1.6.1
```

---

<a id="configuracion-de-la-base-de-datos"></a>
## Configuración de la base de datos

1. Copiar el esquema SQL en un archivo `schema.sql`:
   ```sql
   CREATE TABLE users (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     user TEXT NOT NULL,
     password TEXT NOT NULL,
     correo TEXT NOT NULL,
     avatar TEXT NOT NULL
   );

   CREATE TABLE colecciones (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     nombre TEXT NOT NULL,
     imagen TEXT,
     categoria TEXT NOT NULL,
     audios INTEGER DEFAULT 0,
     prioridades TEXT NOT NULL,
     autor_creacion TEXT NOT NULL,
     fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     autor_actualizacion TEXT,
     fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   CREATE TABLE audios (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     archivo TEXT NOT NULL,
     estado TEXT NOT NULL DEFAULT 'pendiente',
     duracion REAL,
     transcripcion TEXT,
     n_tokens INTEGER,
     tiempo REAL,
     velocidad REAL,
     coleccion_id INTEGER NOT NULL DEFAULT 0,
     contenido TEXT,
     relevancia INT,
     fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     subido_por TEXT,
     transcripcion_segmentos TEXT,
     tiempo_transcripcion REAL,
     tiempo_contenido REAL,
     tiempo_relevancia REAL
   );

   CREATE TABLE modismos (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     expresion TEXT NOT NULL,
     significado TEXT NOT NULL,
     region TEXT
   );
   ```

2. Inicializar la base de datos:
   ```bash
   sqlite3 database.db < schema.sql
   ```

---

<a id="estructura-del-proyecto"></a>
## Estructura del proyecto

```
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── schema.sql
├── database.db
├── app.py
├── audios/
├── modulos/
│   ├── transcripcion.py
│   ├── contenido.py
│   └── relevancia.py
├── static/
│   ├── assets/
│   │        ├── ...    
│   ├── sass/
             ├── ...
└── templates/
    ├── index.html
    ├── login.html
    ├── colecciones.html
    ├── audios.html
    ├── detalles_audio.html
    └── modismos.html
```

---

<a id="uso"></a>
## Uso

<a id="interfaz-web"></a>
### Interfaz web

1. Iniciar la aplicación:
   ```bash
   python app.py
   ```
2. Abrir en el navegador:
   ```
   http://localhost:5000
   ```
3. Navegar por:
   - `/` – Página principal y subida de audios.
   - `/colecciones` – Visualización de colecciones.
   - `/modismos` – Administración de modismos y jerga.

<a id="api-de-subida-y-analisis"></a>
### API de subida y análisis

- **POST** `/upload`: Subir archivos de audio.
- **GET** `/analizar_stream/<coleccion_id>?files=file1.mp3,file2.wav`: Procesa y devuelve un stream SSE con el progreso.

---

<a id="dockerizacion"></a>
## Dockerización

> Para usar GPU con Docker, debe instalar **NVIDIA Container Toolkit**. El repositorio cuenta con los archivos `Dockerfile`, `Dockerfile.ollama` y `docker-compose.yaml`.
<a id="dockerfile"></a>

Para construir y ejecutar: 
```bash
docker-compose up --build
```

---

<a id="licencia"></a>
## Licencia

Este repositorio contiene el código desarrollado para el trabajo de titulación “Transcripción y clasificación automática de audios según su contenido y relevancia”, únicamente para fines académicos.

T2 Agustín Riquelme D., Academia Politécnica Naval © 2025.
