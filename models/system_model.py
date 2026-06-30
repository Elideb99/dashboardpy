from datetime import datetime
from enum import Enum
import json

class SystemStatus(Enum): # evita gli errori usando un metodo più sicuro come "SystemStatus.ALLARME"
    NORMALE = "NORMALE"
    ATTENZIONE = "ATTENZIONE"
    ALLARME = "ALLARME"
    SCIAME = "SCIAME"


class SystemModel:
    """MODEL: Gestisce solo lo stato dell'applicazione"""
    
    def __init__(self): # costruttore
        self._status = SystemStatus.NORMALE #stato corrente con prefisso _ cioè attributo privato
        self._last_event_time = None #ultimo evento simulato
        self._tab_logs = { #memorizzazione dei log (4 tipi)
            "GENERALE": [],
            "CAMPI FLEGREI": [],
            "VESUVIO": [],
            "ISCHIA": []
        }
        self._observers = [] #lista vuota per tenere traccia degli observer che devono essere notificati
    
    def add_observer(self, observer): # registra una vista/observer
        self._observers.append(observer)
    
    def notify_observers(self):
        for observer in self._observers:
            observer.update_ui()  #notifica quando ci sta un aggiornamento
    
    @property # getter che permette di leggere self._status
    def status(self):
        return self._status
    
    @status.setter #setter per quando viene impostato un nuovo valore
    def status(self, value):
        self._status = value
        self.notify_observers()
    
    @property #getter per il tempo dell'ultimo evento
    def last_event_time(self):
        return self._last_event_time
    
    @last_event_time.setter #setter per il tempo dell'ultimo evento
    def last_event_time(self, value):
        self._last_event_time = value
        self.notify_observers()
    
    @property #getter per i log delle tab e non ha setter perchè sono di sola lettura
    def tab_logs(self):
        return self._tab_logs
    
    def add_log(self, zone, message): #aggiugne il messaggio
        if zone in self._tab_logs:
            self._tab_logs[zone].append(message)
            # Limita la lunghezza dei log (opzionale)
            if len(self._tab_logs[zone]) > 1000:
                self._tab_logs[zone] = self._tab_logs[zone][-500:]
        self.notify_observers() #notifica il cambiamento 
    
    def get_status_color(self): #definisce un dizionario che mappa ogni colore dello stato del sistema
        colors = {
            SystemStatus.NORMALE: "#2e7d32",
            SystemStatus.ATTENZIONE: "#ff9800",
            SystemStatus.ALLARME: "#d32f2f",
            SystemStatus.SCIAME: "#ef6c00"
        }
        return colors.get(self._status, "#2e7d32")
    
    @staticmethod

    def filtra_messaggio_kafka(msg_value: list) -> dict | None:

     """
     Estrae i dati essenziali da un messaggio Kafka INGV.
    
     msg.value è una lista di oggetti; quello con name='event'
     contiene le info principali dell'evento sismico.
    
     Ritorna un dict semplificato, oppure None se il messaggio
     non è un evento sismico riconoscibile.
     """

     # se arriva come stringa la deserializziamo 
     if isinstance(msg_value, (str, bytes)):
        try:
            msg_value = json.loads(msg_value)
        except (json.JSONDecodeError, ValueError):
            print(f"[KAFKA] msg.value non è JSON valido: {repr(msg_value[:100])}")
            return None
        
     if not isinstance(msg_value,list):
        print(f"[KAFKA] Formato inatteso: {type(msg_value)}")
        return None
         
    
     # Cerca il blocco 'event' nella lista
     event_block = None
     for item in msg_value:
        if item.get('name') == 'event':
            event_block = item.get('data', {})
            break

     if event_block is None:
        return None

     # Tipo evento: solo earthquake ci interessa (per ora)
     tipo = event_block.get('type', 'unknown')

     # Descrizione estesa, es. "Earthquake (T or VT)"
     tipo_desc = event_block.get('type_desc', '')

     # Area vulcanica: 'vesuvio', 'flegrei', 'ischia'
     area     = event_block.get('area', 'unknown')
     area_desc = event_block.get('adesc', '')

     # Timestamp dell'evento
     data_evento = event_block.get('date') or event_block.get('epoch')

     # Location principale (quella già selezionata da ovsvmlib come best)
     loc = event_block.get('location', {})

     latitudine  = loc.get('latitude')
     longitudine = loc.get('longitude')
     profondita  = loc.get('depth')          # km
     qualita     = loc.get('quality')        # 'A','B','C','D' oppure None
     metodo      = loc.get('method')         # 'BINDER', 'HYPO2000', 'WINPICK'
     n_picks     = loc.get('pick_number')

     # Magnitudine: è una lista, prendi il primo valore se esiste
     magnitudos = loc.get('magnitudos', [])
     if magnitudos:
        mag_val    = magnitudos[0].get('value')
        mag_tipo   = magnitudos[0].get('type')   # 'D', 'Ml', ecc.
        mag_errore = magnitudos[0].get('error')
     else:
        mag_val = mag_tipo = mag_errore = None

     # Errori di localizzazione (utili per valutare affidabilità)
     errori = loc.get('errors', {})
     rms    = errori.get('rms')    # residuo medio quadratico (s)
     gap    = errori.get('gap')    # gap azimutale (°)

     # ID evento
     event_id = event_block.get('id')

     return {
        'event_id':   event_id,
        'tipo':       tipo,
        'tipo_desc':  tipo_desc,
        'area':       area,
        'area_desc':  area_desc,
        'data':       data_evento,
        'latitudine': latitudine,
        'longitudine': longitudine,
        'profondita_km': profondita,
        'magnitudine': mag_val,
        'mag_tipo':   mag_tipo,
        'mag_errore': mag_errore,
        'qualita':    qualita,
        'metodo':     metodo,
        'n_picks':    n_picks,
        'rms':        rms,
        'gap_azimutale': gap,
    }


    # in system_model.py
    def add_log_batch(self, zona: str, messaggi: list[str]):
     """Aggiunge più righe in un colpo solo, senza aggiornare la UI ad ogni riga."""
     if zona not in self._tab_logs:
        zona = "GENERALE"
     self._tab_logs[zona].extend(messaggi)
     # tieni solo gli ultimi N messaggi per non riempire la RAM
     MAX = 500
     if len(self._tab_logs[zona]) > MAX:
        self._tab_logs[zona] = self._tab_logs[zona][-MAX:]
     self.notify_observers() #metodo per aggiornare e mostrare i log 
    

