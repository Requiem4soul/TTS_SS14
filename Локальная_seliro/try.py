import silero
import os
import sounddevice as sd
import time
import torch
from IPython.display import Audio, display

device = torch.device('cuda:0')
model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language='ru',
                                     speaker='v4_ru')
model.to(device)  # gpu or cpu

sample_rate = 48000
speaker = 'xenia'
put_accent=True
put_yo=True
example_text = 'В недрах тундры выдры в г+етрах т+ырят в вёдра ядра к+едров.'

audio = model.apply_tts(text=example_text,
                        speaker=speaker,
                        sample_rate=sample_rate,
                        put_accent=put_accent,
                        put_yo=put_yo)
print(example_text)
display(Audio(audio, rate=sample_rate))

