import socketio
import json
import base64
import os
import pygame
import threading

# Инициализация pygame
pygame.mixer.init()

# Инициализация клиента SocketIO
sio = socketio.Client()

# Путь к рабочему столу пользователя
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
current_audio_index = 0

@sio.event
def connect():
    print('Connected to server')

def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # Ждем завершения воспроизведения

@sio.event
def receive_audio(data):
    global current_audio_index

    print("Вход в аудио")
    audio_data = data.get('audio')
    if audio_data:
        audio_bytes = base64.b64decode(audio_data)

        # Останавливаем любое текущее воспроизведение
        pygame.mixer.music.stop()

        # Формируем имя файла с индексом
        audio_file_name = f'received_audio{current_audio_index:03d}.ogg'
        audio_file_path = os.path.join(desktop_path, audio_file_name)

        print(f"Начало перезаписи аудио в файл {audio_file_name}")

        # Перезаписываем аудиофайл
        with open(audio_file_path, 'wb') as f:
            f.write(audio_bytes)

        print("Воспроизведение")

        # Воспроизведение в отдельном потоке
        play_thread = threading.Thread(target=play_audio, args=(audio_file_path,))
        play_thread.start()

        # Увеличиваем индекс текущего аудио файла
        current_audio_index += 1

        # Удаляем предыдущий файл, если он существует
        if current_audio_index >= 2:
            prev_audio_index = current_audio_index - 2
            prev_audio_file_name = f'received_audio{prev_audio_index:03d}.ogg'
            prev_audio_file_path = os.path.join(desktop_path, prev_audio_file_name)
            try:
                os.remove(prev_audio_file_path)
                print(f"Файл {prev_audio_file_name} удален успешно")
            except Exception as e:
                print(f"Ошибка при удалении файла {prev_audio_file_name}: {e}")

        # Ждем завершения воспроизведения (не более 10 секунд)
        play_thread.join(timeout=10)

        print("Завершение воспроизведения")

# Подключение к серверу
sio.connect('http://localhost:5000')

name = input('Enter your name: ')
speaker = input('Enter speaker (baya, kseniya, aidar): ')

while True:
    text = input(f'{name}: ')
    tts_request = {'speaker': speaker, 'text': text}
    json_request = json.dumps(tts_request)  # Преобразуем словарь в строку JSON
    sio.emit('send_message', json_request)
    print('Sent message to server')

# Завершение подключения при выходе из цикла
sio.disconnect()
