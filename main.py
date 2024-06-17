import torch
import sounddevice as sd
import time

# Инициализация модели Silero TTS
language = 'ru'
model_id = 'v4_ru'
sample_rate = 24000
device = torch.device('cuda')

print("Загрузка модели...")
start_time = time.time()
model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language=language, speaker=model_id)
model.to(device)
print(f"Модель загружена за {time.time() - start_time:.2f} секунд")

# Доступные спикеры
speakers = ['baya', 'kseniya', 'aidar']
current_speaker = speakers[0]

def TTS(who, text_user):
    print(f"Генерация аудио для '{text_user}' спикером {who}...")
    start_time = time.time()
    audio = model.apply_tts(text=text_user, speaker=who, sample_rate=sample_rate)
    generation_time = time.time() - start_time
    print(f"Аудио сгенерировано за {generation_time:.2f} секунд")

    print("Воспроизведение аудио...")
    start_time = time.time()
    sd.play(audio, sample_rate)
    sd.wait()
    playback_time = time.time() - start_time
    print(f"Аудио воспроизведено за {playback_time:.2f} секунд")
    sd.stop()

def print_instructions():
    print("Добро пожаловать в локальный чат с TTS!")
    print("Введите сообщение для отправки.")
    print("Введите /speaker <имя> для смены спикера.")
    print("Доступные спикеры:", ', '.join(speakers))
    print("Введите /exit для выхода.")

def main():
    global current_speaker
    print_instructions()

    while True:
        user_input = input(f"{current_speaker}> ")

        if user_input.startswith('/speaker '):
            _, speaker = user_input.split(maxsplit=1)
            if speaker in speakers:
                current_speaker = speaker
                print(f"Спикер изменен на {current_speaker}")
            else:
                print(f"Спикер {speaker} не найден. Доступные спикеры: {', '.join(speakers)}")
        elif user_input == '/exit':
            print("Выход из чата.")
            break
        else:
            TTS(current_speaker, user_input)



if __name__ == "__main__":
    main()
