import pyaudio
import requests
import threading
import websockets
import asyncio
from flask import Flask, render_template, jsonify
import json
import os

MAX_TRANSLATION_ROWS = 10
SAMPLE_RATE = 16000

app = Flask(__name__)

# Storage for text
german_texts = []
russian_texts = []
german_partial = ""  # Global variable for partial transcription

# Gladia.io parameters
API_KEY_FILE = 'gladia_api_key.txt'
LIVE_TRANSCRIPTION_URL = 'https://api.gladia.io/v2/live'  # Gladia live transcription URL
TRANSLATION_URL = 'https://api.gladia.io/v2/text/text-translation'
SESSION_FILE = 'gladia_session.txt'  # File to store session information

# Line-In Device ID (replace with your actual line-in device ID)
LINE_IN_DEVICE_ID = 2

# Function to load the API key from file
def load_api_key():
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError(f"API key file '{API_KEY_FILE}' not found. Please create it and add your Gladia API key.")

    with open(API_KEY_FILE, 'r') as f:
        api_key = f.read().strip()  # Read and strip whitespace/newlines
        if not api_key:
            raise ValueError(f"API key file '{API_KEY_FILE}' is empty. Please add your Gladia API key.")
        return api_key
# Load the API key
try:
    API_KEY = load_api_key()
except (FileNotFoundError, ValueError) as e:
    print(e)
    exit(1)

# Function to request a new WebSocket URL for live transcription
def get_websocket_url():
    headers = {
        'Content-Type': 'application/json',
        'X-Gladia-Key': API_KEY
    }
    payload = {
        "encoding": "wav/pcm",
        "sample_rate": SAMPLE_RATE,
        "bit_depth": 16,
        "channels": 1
    }
    response = requests.post(LIVE_TRANSCRIPTION_URL, headers=headers, json=payload)

    if response.ok:
        stream_data = response.json()
        websocket_url = stream_data.get("url")
        print(f"URL: {websocket_url}")

        # Save session data to file
        with open(SESSION_FILE, 'w') as f:
            f.write(websocket_url)

        return websocket_url
    else:
        print(f"Error initializing live transcription: {response.status_code} {response.text}")
        return None


# Function to load WebSocket URL from file if it exists
def load_websocket_url_from_file():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            websocket_url = f.read().strip()
            return websocket_url
    return None


# Function to stream audio over WebSocket
async def stream_audio(websocket_url):
    global german_partial  # Declare the global variable

    if not websocket_url:
        print("Нет WebSocket URL. Завершаем поток.")
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
            async with websockets.connect(websocket_url) as websocket:
                while True:
                    # Read audio data and send it over WebSocket
                    audio_data = stream.read(chunk)
                    bytes_read = len(audio_data)
                    # print(f"Bytes read from audio stream: {bytes_read}")
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
                                print(f"german: {german_text}")
                                german_texts.append(german_text)
                                german_partial = ""

                                if len(german_texts) > MAX_TRANSLATION_ROWS:
                                    german_texts.pop(0)
                                # Translate German text to Russian
                                translation_payload = {'text': german_text, 'source_lang': 'de', 'target_lang': 'ru'}
                                translation_response = requests.post(TRANSLATION_URL, headers={'X-Gladia-Key': API_KEY},
                                                                     json=translation_payload)
                                if translation_response.ok:
                                    russian_text = translation_response.json().get('translation', '')
                                    if russian_text:
                                        print(f"russian: {russian_text}")
                                        russian_texts.append(russian_text)
                                        if len(russian_text) > MAX_TRANSLATION_ROWS:
                                            russian_text.pop(0)
                            else:
                                german_partial = german_text

                        # Delay to control rate
                        await asyncio.sleep(0.1)

        except websockets.exceptions.InvalidStatus as e:
            if e.response.status_code == 403:
                print(f"Запрашиваем новый URL: {e.response.body}")
                websocket_url = get_websocket_url()  # Запрашиваем новый WebSocket URL
                if not websocket_url:
                    print("Не удалось получить новый WebSocket URL. Повтор через 5 секунд...")
                    await asyncio.sleep(5)
            else:
                print(f"Ошибка подключения WebSocket: {e}")
                await asyncio.sleep(5)

        except (websockets.ConnectionClosed, ConnectionError) as e:
            print(f"WebSocket connection failed: {e}. Requesting new WebSocket URL...")
            # Request a new WebSocket URL and update `websocket_url`
            websocket_url = get_websocket_url()
            if not websocket_url:
                print("Failed to obtain new WebSocket URL. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying to avoid rapid requests


#        finally:
#            stream.stop_stream()
#            stream.close()
#            audio.terminate()
# Flask routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_texts')
def get_texts():
    return jsonify({'german': german_texts, 'russian': russian_texts, 'partial': german_partial})


# Start WebSocket streaming in a background thread
def start_streaming():
    # Load WebSocket URL from file or request a new one
    websocket_url = load_websocket_url_from_file() or get_websocket_url()
    if websocket_url:
        # Run WebSocket audio streaming in a new asyncio event loop
        asyncio.run(stream_audio(websocket_url))
    else:
        print("Failed to start live transcription session.")


if __name__ == '__main__':
    # Start audio streaming in a background thread
    threading.Thread(target=start_streaming, daemon=True).start()
    app.run(debug=True)
