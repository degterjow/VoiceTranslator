import threading
from waitress import serve
from VoiceTranslator import app, start_streaming

# Запуск фонового потока для обработки аудио
def run_background_tasks():
    start_streaming()  # Здесь можно запустить ваш WebSocket или любой другой процесс

# Основная функция запуска
if __name__ == "__main__":
    # Фоновый поток
    background_thread = threading.Thread(target=run_background_tasks, daemon=True)
    background_thread.start()

    # Запуск WSGI-сервера Waitress
    serve(app, host="192.168.0.10", port=5000)
