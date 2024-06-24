import socketio
import json
import base64
import os
import pygame
import threading
from collections import deque

# Инициализация pygame
pygame.mixer.init()

# Инициализация клиента SocketIO
sio = socketio.Client()

# Получение имени пользователя
name = input('Enter your name: ')
speaker = input('Enter speaker (baya, kseniya, aidar): ')

# Создание уникальной папки для аудиофайлов пользователя
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', f'audio_{name}')
os.makedirs(desktop_path, exist_ok=True)
audio_queue = deque()
current_audio_index = 0
max_audio_files = 10  # Максимальное количество сохраняемых аудиофайлов

@sio.event
def connect():
    print('Connected to server')

def play_audio():
    while True:
        if audio_queue:
            file_path = audio_queue.popleft()
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)  # Ждем завершения воспроизведения

                # Удаляем файл после воспроизведения, если файлов больше, чем max_audio_files
                if current_audio_index >= max_audio_files:
                    os.remove(file_path)
                    print(f"Файл {file_path} удален после воспроизведения")
            except Exception as e:
                print(f"Ошибка при воспроизведении файла {file_path}: {e}")

@sio.event
def receive_audio(data):
    global current_audio_index

    print("Вход в аудио")
    audio_data = data.get('audio')
    if audio_data:
        audio_bytes = base64.b64decode(audio_data)

        # Формируем уникальное имя файла
        audio_file_name = f'received_audio{current_audio_index:03d}.ogg'
        audio_file_path = os.path.join(desktop_path, audio_file_name)

        print(f"Начало перезаписи аудио в файл {audio_file_name}")

        # Перезаписываем аудиофайл
        with open(audio_file_path, 'wb') as f:
            f.write(audio_bytes)

        # Добавляем файл в очередь
        audio_queue.append(audio_file_path)

        # Увеличиваем индекс текущего аудио файла
        current_audio_index += 1

        # Проверяем, если файлов больше, чем max_audio_files, удаляем старые файлы
        if current_audio_index >= max_audio_files:
            old_file_index = current_audio_index - max_audio_files
            old_audio_file_name = f'received_audio{old_file_index:03d}.ogg'
            old_audio_file_path = os.path.join(desktop_path, old_audio_file_name)
            if os.path.exists(old_audio_file_path):
                try:
                    os.remove(old_audio_file_path)
                    print(f"Файл {old_audio_file_name} удален")
                except Exception as e:
                    print(f"Ошибка при удалении файла {old_audio_file_name}: {e}")

# Запуск потока воспроизведения аудио
play_thread = threading.Thread(target=play_audio, daemon=True)
play_thread.start()

# Подключение к серверу
sio.connect('http://localhost:5000')

while True:
    text = input(f'{name}: ')
    tts_request = {'speaker': speaker, 'text': text}
    json_request = json.dumps(tts_request)  # Преобразуем словарь в строку JSON
    sio.emit('send_message', json_request)
    print('Sent message to server')

# Завершение подключения при выходе из цикла
sio.disconnect()
