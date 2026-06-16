from datetime import datetime
from enum import Enum

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