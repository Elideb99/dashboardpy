import os
import subprocess
import shutil
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

class AudioService: #classe per gestire la riproduzione audio 
    def __init__(self):
        self.wav_path = os.path.join(os.path.dirname(__file__), "..", "services", "alarm_dec.wav") # costruisce il percorso del file audio
        self._audio_process = None # inizializza il processo audio a none
        self.audio_available = False # flag per indicare se l'audio è disponibile
        

        self._is_wsl = ( #rileva wsl
            os.path.exists("/proc/version")
            and "microsoft" in open("/proc/version").read().lower()
        )
        
        if self._is_wsl: #se siamo in wsl converte da formato linux a windows
            self.win_wav_path = self.wav_path.replace("/mnt/c/", "C:\\").replace("/", "\\")
            self.audio_available = os.path.exists(self.wav_path)
            self._aplay_available = False
            self.alarm = None 
            # verifica se il file audio esiste e imposta i valori a false/none
        else:
            self._aplay_available = shutil.which("aplay") is not None # se non siamo in wsl verifica se il comando aplay è disponibile
            self.alarm = QSoundEffect()
            self.alarm.setVolume(0.9)
            self.alarm.setLoopCount(1)
    
    def set_source(self, url): # se esiste l'oggetto alarm imposta l'url
        if self.alarm:
            self.alarm.setSource(url)
    
    def on_status_changed(self, callback): # se esiste l'oggetto collega il segnale a una funzione callback
        if self.alarm:
            self.alarm.statusChanged.connect(callback)
    
    def is_ready(self): # verifica se l'audio è pronto
        return self.alarm and self.alarm.status() == QSoundEffect.Status.Ready
    
    def play(self): # riproduce l'audio, con fallback in cascata a seconda della piattaforma
        if self._is_wsl:
            self._play_wsl() # se in wsl usa _play_wsl
        elif self.alarm and self.audio_available and self.is_ready():
            self.alarm.play() # se l'audio è caricato e pronto riproduce il suono
        elif hasattr(self, '_aplay_available') and self._aplay_available and os.path.exists(self.wav_path):
            self._play_aplay() # se fallisce (QSoundEffect non pronto) prova con aplay
    
    def stop(self): # stoppa l'audio (sia il QSoundEffect sia un eventuale processo esterno powershell/aplay)
        if not self._is_wsl and self.alarm and self.is_ready():
            self.alarm.stop()
        if self._audio_process and self._audio_process.poll() is None:
            self._audio_process.terminate()
            self._audio_process = None
    
    def _play_wsl(self):
        # su WSL non c'è output audio diretto: delega a PowerShell.exe sull'host Windows
        if os.path.exists(self.wav_path):
            try: # se esiste già un audio in esecuzione allora lo termina
                if self._audio_process and self._audio_process.poll() is None:
                    self._audio_process.terminate()
                ps_cmd = f"(New-Object Media.SoundPlayer '{self.win_wav_path}').PlaySync()"
                self._audio_process = subprocess.Popen( # crea un oggetto per il percorso e riproduce il suono 
                    ["powershell.exe", "-c", ps_cmd], # avvia il processo powershell ed esegue il comando
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"⚠️ Errore PowerShell audio: {e}")
    
    def _play_aplay(self):
        # fallback Linux nativo (non-WSL) quando QSoundEffect non è disponibile/pronto
        try:
            if self._audio_process and self._audio_process.poll() is None:
                self._audio_process.terminate()
            self._audio_process = subprocess.Popen(
                ["aplay", self.wav_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"⚠️ Errore aplay: {e}")