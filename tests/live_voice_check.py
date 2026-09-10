"""Motores locales reales con frase sintética; no abre el micrófono ni llama a ChatGPT."""
import array
import base64
import io
from pathlib import Path
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.workbench_voice import Speech

speech=Speech()
audio=speech.synthesize('Hola. Quiero escribir una historia sobre una biblioteca en un barco.')
with wave.open(io.BytesIO(audio),'rb') as w:
    frames=w.readframes(w.getnframes());rate=w.getframerate()
    assert w.getsampwidth()==2 and w.getnchannels()==1
# Solo remuestreo del fixture sintético de esta prueba; la app usa AudioContext a 16 kHz.
samples=array.array('h',frames)
resampled=array.array('h')
for i in range(int(len(samples)*16000/rate)):
    position=i*rate/16000;left=int(position);fraction=position-left
    resampled.append(round(samples[left]*(1-fraction)+samples[min(left+1,len(samples)-1)]*fraction))
pcm=resampled.tobytes()
result=speech.transcribe(base64.b64encode(pcm).decode())
assert 'historia' in result['text'] and 'biblioteca' in result['text'],result
print('OK voz local real: síntesis WAV y reconocimiento español; frase ficticia, sin red ni micrófono.')
