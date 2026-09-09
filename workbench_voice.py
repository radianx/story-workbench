"""Voz local: PCM español mediante Vosk y lectura con herramientas del sistema."""
import base64
import ctypes as C
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import wave
from workbench_store import check, text_value

RATE = 16000
MAX_SECONDS = 45


def decode_pcm(value):
    text_value(value, RATE * MAX_SECONDS * 2 * 4 // 3 + 4, False)
    try:
        pcm = base64.b64decode(value, validate=True)
    except ValueError:
        check(False, 'Audio inválido.')
    check(0 < len(pcm) <= RATE * MAX_SECONDS * 2 and len(pcm) % 2 == 0, 'Dictá hasta 45 segundos por mensaje.')
    return pcm


class Speech:
    def __init__(self):
        target = 'win' if os.name == 'nt' else 'linux'
        self.root = Path(os.environ.get('STORY_VOICE_DIR', Path(__file__).parent / 'dist' / 'voice' / target))
        self.library = self.root / ('libvosk.dll' if os.name == 'nt' else 'libvosk.so')
        self.model_path = self.root / 'model'
        self.tts = (shutil.which('powershell.exe') if os.name == 'nt' else
                    os.environ.get('STORY_TTS_BINARY') or shutil.which('espeak-ng'))
        self.lock = threading.Lock()
        self.lib = self.model = self.dll_directory = None

    def status(self):
        return dict(dictation=self.library.is_file() and self.model_path.is_dir(), reading=bool(self.tts),
                    language='es', max_seconds=MAX_SECONDS,
                    voice='Voz de Windows (según idiomas instalados)' if os.name == 'nt' else 'Español · eSpeak NG',
                    local=True)

    def load(self):
        if self.lib:
            return
        check(self.status()['dictation'], 'El motor de dictado no está incluido. Instalá la versión con voz.')
        if os.name == 'nt':
            self.dll_directory = os.add_dll_directory(str(self.root.resolve()))
        lib = C.CDLL(str(self.library))
        signatures = {
            'vosk_set_log_level': ([C.c_int], None),
            'vosk_model_new': ([C.c_char_p], C.c_void_p),
            'vosk_recognizer_new': ([C.c_void_p, C.c_float], C.c_void_p),
            'vosk_recognizer_accept_waveform': ([C.c_void_p, C.c_char_p, C.c_int], C.c_int),
            'vosk_recognizer_result': ([C.c_void_p], C.c_char_p),
            'vosk_recognizer_final_result': ([C.c_void_p], C.c_char_p),
            'vosk_recognizer_free': ([C.c_void_p], None),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(lib, name); fn.argtypes = args; fn.restype = result
        lib.vosk_set_log_level(-1)
        model = lib.vosk_model_new(str(self.model_path).encode('utf-8'))
        check(bool(model), 'No se pudo cargar el modelo español de dictado.')
        # ponytail: un modelo en memoria por proceso; se carga solo al primer dictado.
        self.lib, self.model = lib, model

    def transcribe(self, encoded):
        pcm = decode_pcm(encoded)
        check(self.lock.acquire(blocking=False), 'Ya se está procesando audio. Esperá un momento.', 409)
        try:
            self.load()
            recognizer = self.lib.vosk_recognizer_new(self.model, RATE)
            check(bool(recognizer), 'No se pudo iniciar el dictado.')
            try:
                parts = []
                for offset in range(0, len(pcm), 8000):
                    chunk = pcm[offset:offset+8000]
                    accepted = self.lib.vosk_recognizer_accept_waveform(recognizer, chunk, len(chunk))
                    check(accepted >= 0, 'No se pudo reconocer este audio.')
                    if accepted:
                        parts.append(json.loads(self.lib.vosk_recognizer_result(recognizer))['text'])
                parts.append(json.loads(self.lib.vosk_recognizer_final_result(recognizer))['text'])
                return {'text': ' '.join(p for p in parts if p), 'local': True}
            finally:
                self.lib.vosk_recognizer_free(recognizer)
        finally:
            self.lock.release()

    def synthesize(self, text):
        text_value(text, 6000, False)
        check(len(text) <= 2000, 'La lectura admite fragmentos de hasta 2.000 caracteres.')
        check(bool(self.tts), 'No hay una voz del sistema disponible en esta instalación.')
        if os.name == 'nt':
            # Texto por stdin, nunca interpolado en el código PowerShell.
            script = ("[Console]::InputEncoding = [System.Text.UTF8Encoding]::new(); Add-Type -AssemblyName System.Speech; "
                      "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                      "$v = $s.GetInstalledVoices() | Where-Object {$_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq 'es'} | Select-Object -First 1; "
                      "if ($v) {$s.SelectVoice($v.VoiceInfo.Name)}; "
                      "$m = New-Object System.IO.MemoryStream; $s.SetOutputToWaveStream($m); "
                      "$s.Speak([Console]::In.ReadToEnd()); $s.Dispose(); "
                      "$b = $m.ToArray(); [Console]::OpenStandardOutput().Write($b,0,$b.Length); $m.Dispose()")
            command = [self.tts, '-NoProfile', '-NonInteractive', '-Command', script]
        else:
            command = [self.tts, '--stdout', '--stdin', '-v', 'es', '-s', '155']
        result = subprocess.run(command, input=text.encode('utf-8'), capture_output=True, timeout=30,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        check(result.returncode == 0, 'No se pudo generar la lectura con la voz del sistema.')
        # Normalizar el tamaño WAV: eSpeak escribe una cabecera de flujo de longitud abierta.
        with wave.open(io.BytesIO(result.stdout), 'rb') as audio:
            params, frames = audio.getparams(), audio.readframes(audio.getnframes())
        output = io.BytesIO()
        with wave.open(output, 'wb') as audio:
            audio.setparams(params); audio.writeframes(frames)
        return output.getvalue()
