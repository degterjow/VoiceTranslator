import pyaudio
import requests
import threading
import websockets
import asyncio
from flask import Flask, render_template, jsonify, Response, request
from elevenlabs.client import ElevenLabs
import json
import os
import deepl
import queue
import io
import time
import atexit
import logging

# Line-In Device ID (replace with your actual line-in device ID - see device_enumerator.py output)
LINE_IN_DEVICE_ID = 2
MAX_TRANSLATION_ROWS = 3
SAMPLE_RATE = 16000
endpointing_duration=0.3

app = Flask(__name__)

# Storage for text
german_texts = ["Erste Zeile", "Zweite Zeile", "Dritte Zeile"]
russian_texts = ["Первая строка", "Вторая строка", "Третья строка"]
german_partial = "Aktuelle Übersetzung in Progress..."
new_german = ""
new_russian = ""

# Queue for TTS
tts_queue = queue.Queue()
audio_queue = queue.Queue(maxsize=10)  # Очередь для передачи аудиоданных клиентам


# Gladia.io parameters
GLADIA_API_KEY_FILE = 'gladia_api_key.txt'
GLADIA_SESSION_FILE = 'gladia_session.txt'
LIVE_TRANSCRIPTION_URL = 'https://api.gladia.io/v2/live'

# Deepl parameters
DEEPL_API_KEY_FILE = 'deepl_api_key.txt'

# Eleven labs parameters
ELEVEN_LABS_API_KEY_FILE = 'eleven_labs_api_key.txt'

# Настройка логгера
logging.basicConfig(
    level=logging.DEBUG,  # Установите уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Логи в консоль
        logging.FileHandler("voice_translator.log")  # Логи в файл
    ]
)

logger = logging.getLogger(__name__)

# Function to load the API key from file
def load_api_key(api_file_name):
    if not os.path.exists(api_file_name):
        raise FileNotFoundError(
            f"API key file '{api_file_name}' not found. Please create it and add your API key.")

    with open(api_file_name, 'r') as f:
        api_key = f.read().strip()  # Read and strip whitespace/newlines
        if not api_key:
            raise ValueError(f"API key file '{api_file_name}' is empty. Please add your API key.")
        return api_key

# Load the API keys
try:
    GLADIA_API_KEY = load_api_key(GLADIA_API_KEY_FILE)
    DEEPL_API_KEY = load_api_key(DEEPL_API_KEY_FILE)
    ELEVEN_LABS_API_KEY = load_api_key(ELEVEN_LABS_API_KEY_FILE)
    translator = deepl.Translator(DEEPL_API_KEY)
    elevenLabsClient = ElevenLabs( api_key=ELEVEN_LABS_API_KEY,)
except (FileNotFoundError, ValueError) as e:
    logger.error(e)
    exit(1)


# Function to request a new WebSocket URL for live transcription
def get_websocket_url(duration):
    headers = {
        'Content-Type': 'application/json',
        'X-Gladia-Key': GLADIA_API_KEY
    }
    payload = {
        "encoding": "wav/pcm",
        "sample_rate": SAMPLE_RATE,
        "bit_depth": 16,
        "channels": 1,
        "endpointing": duration
    }
    response = requests.post(LIVE_TRANSCRIPTION_URL, headers=headers, json=payload)

    if response.ok:
        stream_data = response.json()
        websocket_url = stream_data.get("url")
        logger.info(f"URL: {websocket_url}")

        # Save session data to file
        with open(GLADIA_SESSION_FILE, 'w') as f:
            f.write(websocket_url)

        return websocket_url
    else:
        logger.error(f"Error initializing live transcription: {response.status_code} {response.text}")
        return None


# Function to load WebSocket URL from file if it exists
def load_websocket_url_from_file():
    if os.path.exists(GLADIA_SESSION_FILE):
        with open(GLADIA_SESSION_FILE, 'r') as f:
            gladia_websocket_url = f.read().strip()
            return gladia_websocket_url
    return None


# Function to stream audio over WebSocket
async def stream_audio(gladia_websocket_url):
    global german_partial
    global new_german
    global new_russian

    if not gladia_websocket_url:
        logger.error("No WebSocket URL. closing...")
        return

    audio_format = pyaudio.paInt16
    channels = 1
    rate = SAMPLE_RATE
    chunk = 1024
    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio_format, channels=channels, rate=rate, input=True,
                        frames_per_buffer=chunk, input_device_index=LINE_IN_DEVICE_ID)

    while True:
        try:
            # Connect to WebSocket and start streaming audio
            async with websockets.connect(gladia_websocket_url) as websocket:
                while True:
                    # Read audio data and send it over WebSocket
                    audio_data = stream.read(chunk)
                    await websocket.send(audio_data)

                    # Receive transcription data
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    if response_data.get("type") == "transcript":
                        transcript_data = response_data.get("data", {}).get("utterance", {})
                        german_text = transcript_data.get("text", "").strip()
                        is_final = response_data.get("data", {}).get("is_final", False)

                        if german_text:
                            if is_final:
                                logger.debug(f"german: {german_text}")
                                german_texts.append(german_text)
                                german_partial = ""

                                if len(german_texts) > MAX_TRANSLATION_ROWS:
                                    german_texts.pop(0)

                                # Translate German text to Russian
                                russian_text_result = translator.translate_text(german_text,
                                                                         source_lang="DE",
                                                                         target_lang="RU")
                                if russian_text_result:
                                    logger.debug(f"russian: {russian_text_result.text}")
                                    russian_texts.append(russian_text_result.text)
                                    new_german = german_text
                                    new_russian = russian_text_result.text
                                    tts_queue.put(new_russian)
                                    if len(russian_texts) > MAX_TRANSLATION_ROWS:
                                        russian_texts.pop(0)
                            else:
                                german_partial = german_text

                        # Delay to control rate
                        await asyncio.sleep(0.1)

        except websockets.exceptions.InvalidStatus as e:
            if e.response.status_code == 403:
                logger.info(f"Запрашиваем новый URL: {e.response.body}")
                gladia_websocket_url = get_websocket_url(endpointing_duration)  # Запрашиваем новый WebSocket URL
                if not gladia_websocket_url:
                    logger.error("Не удалось получить новый WebSocket URL. Повтор через 5 секунд...")
                    await asyncio.sleep(5)
            else:
                logger.error(f"Ошибка подключения WebSocket: {e}")
                await asyncio.sleep(5)

        except (websockets.ConnectionClosed, ConnectionError) as e:
            logger.error(f"WebSocket connection failed: {e}. Requesting new WebSocket URL...")
            # Request a new WebSocket URL and update `websocket_url`
            gladia_websocket_url = get_websocket_url(endpointing_duration)
            if not gladia_websocket_url:
                logger.error("Failed to obtain new WebSocket URL. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying to avoid rapid requests


# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_initial_texts', methods=['GET'])
def get_initial_texts():
    return jsonify({
        "german": german_texts,
        "russian": russian_texts
    })

@app.route('/update_endpointing', methods=['POST'])
def update_endpointing():
    global websocket_url, endpointing_duration

    # Parse the new endpointing duration
    data = request.json
    endpointing_duration = data.get('endpointing', 0.5)  # Default to 0.5 if not provided

    # Reinitialize WebSocket connection with new parameters
    websocket_url = get_websocket_url(endpointing_duration)  # Optionally request a new WebSocket URL
    logger.info(f"Updated endpointing duration to {endpointing_duration}. WebSocket URL refreshed.")

    return jsonify({"status": "success", "endpointing": endpointing_duration})

# SSE Route
@app.route('/stream')
def stream():
    def event_stream():
        previous_german = ""
        previous_partial = ""

        while True:

            if german_partial != previous_partial:
                yield f"event: partial\ndata: {json.dumps({'german_partial': german_partial})}\n\n"

            if new_german != previous_german:
                yield f"event: update\ndata: {json.dumps({'new_german': new_german, 'new_russian': new_russian})}\n\n"

            # Update the previous state
            previous_german = new_german
            previous_partial = german_partial

            # Control the update frequency
            time.sleep(0.1)

    return Response(event_stream(), content_type='text/event-stream')

@app.route('/audio_stream')
def audio_stream():
    """
    HTTP-эндпоинт для передачи аудиопотока клиентам.
    """
    def audio_generator():
        try:
            logger.debug("Starting audio stream to clients...")
            while True:
                # Получение аудиоданных из очереди
                chunk = audio_queue.get()
                if chunk is None:
                    break  # Сигнал остановки
                yield chunk
        except GeneratorExit:
            logger.debug("Client disconnected from audio stream.")
        except Exception as e:
            logger.error(f"Error in audio generator: {e}")

    return Response(audio_generator(), content_type='audio/wav')


def eleven_labs_worker():
    """
    Фоновый процесс для обработки очереди текста TTS и передачи аудиопотока в audio_queue.
    """
    while True:
        try:
            # Получение текста из очереди
            tts_text = tts_queue.get()
            if tts_text is None:
                break  # Сигнал остановки

            logger.debug(f"Processing TTS for text: {tts_text}")
            audio_stream = elevenLabsClient.text_to_speech.convert_as_stream(
                text=tts_text,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2"
            )

            # Чтение аудиопотока по частям и добавление в очередь аудиоданных
            for chunk in iter(lambda: audio_stream.read(1024), b''):
                audio_queue.put(chunk)

        except Exception as e:
            logger.error(f"Error in TTS worker: {e}")
        finally:
            tts_queue.task_done()

def send_stream_flask(audio_stream):
    """
    Отправляет аудиопоток в Flask.

    Args:
        audio_stream: Поток аудиоданных, возвращаемый Eleven Labs.
    """
    try:
        logger.debug("Streaming audio to Flask server...")

        # Преобразуем поток в байтовый буфер
        audio_buffer = io.BytesIO(audio_stream.read())

    except Exception as e:
        logger.error(f"Error while streaming audio to Flask: {e}")

# Start WebSocket streaming in a background thread
def start_streaming():
    # Load WebSocket URL from file or request a new one
    gladia_websocket_url = load_websocket_url_from_file() or get_websocket_url(endpointing_duration)
    if gladia_websocket_url:
        # Run WebSocket audio streaming in a new asyncio event loop
        asyncio.run(stream_audio(gladia_websocket_url))
    else:
        logger.error("Failed to start live transcription session.")

def cleanup_on_exit():
    """
    Обеспечивает корректное завершение фоновых потоков при завершении приложения.
    """
    tts_queue.put(None)  # Сигнал остановки для TTS-потока
    tts_thread.join()    # Ожидание завершения потока

    audio_queue.put(None)  # Сигнал остановки для аудиопотока
    logger.info("Cleaned up resources on exit.")

atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    # Start audio streaming in a background thread
    threading.Thread(target=start_streaming, daemon=True).start()
    # Initialize and start the TTS worker thread
    # Добавление текста в очередь
    tts_queue.put("Небольщой пример текста для проверки работы синтеза речи движка Eleven Labs.")

    tts_thread = threading.Thread(target=eleven_labs_worker, daemon=True)
    tts_thread.start()
    app.run(debug=True)
