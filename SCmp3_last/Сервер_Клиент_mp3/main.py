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
import subprocess
import sounddevice as sd
import time

# Устанавливаем путь к ffmpeg.exe
ffmpeg_path = r'C:\Users\Ilya\Desktop\ffmpeg-7.0.1-essentials_build\bin\ffmpeg.exe'
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
    print("Начало ТТС")
    audio = model.apply_tts(text=text_user, speaker=who, sample_rate=sample_rate)
    wav_io = io.BytesIO()
    sf.write(wav_io, audio, sample_rate, format='WAV')
    wav_io.seek(0)
    print("Середина ТТС")
    audio_segment = AudioSegment.from_wav(wav_io)
    mp3_io = io.BytesIO()
    audio_segment.export(mp3_io, format='mp3')
    mp3_io.seek(0)
    print("Конец ТТС")
    return mp3_io

@socketio.on('send_message')
def handle_send_message(message):
    print("Начало хэндла")
    try:
        data = json.loads(message)  # Преобразуем строку JSON в объект Pythonы
        speaker = data.get('speaker', 'baya')
        text = data.get('text', '')
        mp3_io = TTS(speaker, text)
        audio_data = base64.b64encode(mp3_io.read()).decode('utf-8')
        emit('receive_audio', {'audio': audio_data}, broadcast=True)
    except json.JSONDecodeError:
        print("Received message is not valid JSON")
    print("Конец хэндла")

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
