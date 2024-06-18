import eventlet
eventlet.monkey_patch()

from flask import Flask, request
from flask_socketio import SocketIO, emit
import torch
import soundfile as sf
from pydub import AudioSegment
import io
import base64
import json
import os

# Устанавливаем путь к ffmpeg.exe
ffmpeg_path = "C:/Users/Ilya/AppData/Local/Programs/Microsoft VS Code/MyCode/Flask/bin/ffmpeg.exe"
AudioSegment.converter = ffmpeg_path

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Инициализация модели Silero TTS
language = 'ru'
model_id = 'v4_ru'
sample_rate = 24000
device = torch.device('cuda:0')

model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language=language, speaker=model_id)
model.to(device)

def TTS(who, text_user):
    audio = model.apply_tts(text=text_user, speaker=who, sample_rate=sample_rate)
    wav_io = io.BytesIO()
    sf.write(wav_io, audio, sample_rate, format='WAV')
    wav_io.seek(0)
    audio_segment = AudioSegment.from_wav(wav_io)
    ogg_io = io.BytesIO()
    audio_segment.export(ogg_io, format='ogg')
    ogg_io.seek(0)
    print("Конец ТТС")
    return ogg_io

@socketio.on('send_message')
def handle_send_message(message):
    try:
        data = json.loads(message)  # Преобразуем строку JSON в объект Python
        speaker = data.get('speaker', 'baya')
        text = data.get('text', '')
        socketio.start_background_task(target=process_tts, speaker=speaker, text=text)
    except json.JSONDecodeError:
        print("Received message is not valid JSON")

def process_tts(speaker, text):
    ogg_io = TTS(speaker, text)
    audio_data = base64.b64encode(ogg_io.read()).decode('utf-8')
    socketio.emit('receive_audio', {'audio': audio_data}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
