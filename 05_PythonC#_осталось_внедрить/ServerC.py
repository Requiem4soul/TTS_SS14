import asyncio
import json
import io
import torch
import soundfile as sf
from pydub import AudioSegment
import threading
import websockets
from websockets import WebSocketServerProtocol

# Устанавливаем путь к ffmpeg.exe
ffmpeg_path = "C:/Users/Ilya/AppData/Local/Programs/Microsoft VS Code/MyCode/Flask/bin/ffmpeg.exe"
AudioSegment.converter = ffmpeg_path

# Инициализация модели Silero TTS
language = 'ru'
model_id = 'v4_ru'
sample_rate = 24000
device = torch.device('cuda:0')

model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language=language, speaker=model_id)
model.to(device)

# Список всех подключенных клиентов
connected_clients = set()

def TTS(who, text_user):
    print(f"Generating audio for '{text_user}' with speaker '{who}'")

    audio = model.apply_tts(text=text_user, speaker=who, sample_rate=sample_rate)
    wav_io = io.BytesIO()
    sf.write(wav_io, audio, sample_rate, format='WAV')
    wav_io.seek(0)
    audio_segment = AudioSegment.from_wav(wav_io)
    ogg_io = io.BytesIO()
    audio_segment.export(ogg_io, format='ogg')
    ogg_io.seek(0)
    
    print(f"Audio generated for '{text_user}' with speaker '{who}'")
    
    return ogg_io

async def handle_client(websocket: WebSocketServerProtocol, path: str):
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                print(f"Received message from client: {message}")

                data = json.loads(message)
                speaker = data.get('speaker', 'baya')
                text = data.get('text', '')

                # Генерация аудио
                ogg_io = TTS(speaker, text)

                # Отправка аудиофайла всем подключенным клиентам
                audio_data = ogg_io.read()
                for client in connected_clients.copy():
                    if client.open:
                        try:
                            await client.send(audio_data)
                            print(f"Sent audio data to client {client.remote_address} for '{text}' with speaker '{speaker}'")
                        except Exception as e:
                            print(f"Error sending data to client {client.remote_address}: {e}")
                            connected_clients.remove(client)
                    else:
                        connected_clients.remove(client)

            except json.JSONDecodeError:
                print("Invalid JSON received")

    except Exception as e:
        print(f"Client disconnected: {e}")
    finally:
        connected_clients.remove(websocket)

async def start_server():
    async with websockets.serve(handle_client, 'localhost', 5000, max_size=10**7, ping_interval=None):
        print("Server started...")
        await asyncio.Future()  # Ожидание для работы сервера

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(start_server()), daemon=True).start()
    threading.Event().wait()  # Ожидание завершения работы сервера
