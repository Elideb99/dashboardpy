import random
from datetime import datetime
from models.system_model import SystemModel, SystemStatus
from utils.helpers import get_random_event

class SystemController:
    """CONTROLLER: Gestisce tutta la logica applicativa, rappresenta il controller di tutta l'architettura"""
    
    def __init__(self, model, audio_service, map_service, view): 
        #il costruttore riceve 4 componenti
        self.model = model #modello dei dati
        self.audio_service = audio_service #gestione audio
        self.map_service = map_service #gestione mappa
        self.view = view #interfaccia utente
    
    # ─────────────────────────────────────────────────────────
    #  LOGICA EVENTI
    # ─────────────────────────────────────────────────────────
    def simulate_event(self):
        mag, zone, zone_filter = get_random_event()  #genera eventi casuali e ritorna mag,zone e zone_filter
        self.model.last_event_time = datetime.now() #imposta l'ora dell'ultimo evento al momento attuale
        
        # Log
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] EVENTO M{mag} - {zone}"
        #costruisce il messaggio di log con orario,magnitudo e zona
        
        # Determina zona corretta per il log
        if "Vesuvio" in zone:
            log_zone = "VESUVIO"
        elif "Campi Flegrei" in zone:
            log_zone = "CAMPI FLEGREI"
        elif "Ischia" in zone:
            log_zone = "ISCHIA"
        else:
            log_zone = zone_filter
        
        self.model.add_log(log_zone, log_msg)
        self.model.add_log("GENERALE", log_msg)
        
        # Determina stato
        if mag >= 3.5: #se la magnitudo è >= 3.5 scatta l'allarme
            self.model.status = SystemStatus.ALLARME
            self.audio_service.play() # attiva l'audio 
            if self.view: # se la vista esiste
                self.view.flash_title()  # mostra il pop-up
                self.view.show_alarm_popup(mag, zone)
        elif mag >= 2.0:
            self.model.status = SystemStatus.ATTENZIONE
        else:
            self.model.status = SystemStatus.NORMALE
        
        # Aggiorna mappa
        self.map_service.update_vulcano(zone_filter, self.model.status.value, mag)
        
        # Aggiorna UI
        if self.view:
            self.view.update_ui()
        
        print(f"✅ Evento simulato: M{mag} - {zone} - Stato: {self.model.status.value}")
        return self.model.last_event_time
    
    def activate_swarm(self): #attiva sciame 
        zone = random.choice(["VESUVIO", "CAMPI FLEGREI", "ISCHIA"])
        zone_name = {"VESUVIO": "Vesuvio", "CAMPI FLEGREI": "Campi Flegrei", "ISCHIA": "Ischia"}[zone]
        # sceglie randomicamente una zona tra quelle disponibili e attiva lo sciame
        self.model.status = SystemStatus.SCIAME
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] SCIAME SISMICO ATTIVATO - {zone_name}"
        self.model.add_log(zone, log_msg)
        self.model.add_log("GENERALE", log_msg)
        #lo aggiunge sia per la zona specifica che in generale
        
        self.audio_service.play()
        self.map_service.update_vulcano(zone, SystemStatus.SCIAME.value)
        #attiva l'audio e aggiorna la mappa
        
        # Aggiorna UI
        if self.view:
            self.view.update_ui() #aggiorna l'interfaccia
            self.view.flash_title() # il titolo lampeggia
        
        print(f"✅ Sciame attivato su {zone_name}")
        return datetime.now()
    
    def reset(self): #resetta il sistema
        self.audio_service.stop() #stoppa l'audio
        self.model.status = SystemStatus.NORMALE #setta a normale
        self.model.last_event_time = None #resetta il tempo dell'ultimo evento a none
        
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.model.add_log("GENERALE", f"[{timestamp}] RESET SISTEMA")
        #aggiunge un log di reset
        
        for zona in ["VESUVIO", "CAMPI FLEGREI", "ISCHIA"]:
            self.map_service.update_vulcano(zona, SystemStatus.NORMALE.value)
            # per ogni zona aggiorna il vulcano sulla mappa a stato normale
        
        # Aggiorna UI
        if self.view:
            self.view.update_ui()
            self.view.reset_window_title() # resetta il titolo
        
       
    
    # ─────────────────────────────────────────────────────────
    #  LOGICA TEMPO
    # ─────────────────────────────────────────────────────────
    def get_time_since_last_event(self):
        if self.model.last_event_time is None:
            return None
        # se non c'è stato alcun evento restituisce none 
        
        diff = datetime.now() - self.model.last_event_time
        seconds = int(diff.total_seconds())
        # calcola la differenza tra ora attuale e ultimo evento
        
        if seconds < 60:
            return f"{seconds} secondi fa"
        elif seconds < 3600:
            return f"{seconds // 60} minuti e {seconds % 60} secondi fa"
        else:
            return f"{seconds // 3600} ore e {(seconds % 3600) // 60} minuti fa"
    
    def get_current_time(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def get_current_date(self):
        return datetime.now().strftime("%d/%m/%Y")
    
    def get_current_date_utc(self):
     """Restituisce la data UTC corrente"""
     return datetime.utcnow().strftime("%d/%m/%Y")
    
    def get_current_time(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_utc_time(self):
     """Restituisce l'ora UTC corrente"""
     return datetime.utcnow().strftime("%H:%M:%S")

    def get_current_date(self):
     return datetime.now().strftime("%d/%m/%Y")
    

    # ─────────────────────────────────────────────────────────
    #  LOGICA MAPPA
    # ─────────────────────────────────────────────────────────
    def on_map_loaded(self, ok): # stampa un messaggio in console con ...
        print("Mappa caricata" if ok else "Errore mappa")
        if ok:
            self.map_service.set_ready(True)
            self.map_service.apply_config()
    
    def on_tab_changed(self, tab_name): # gestisce lo zoom delle zone sismiche
        if not self.map_service.map_ready:
            return
        zone_map = {"CAMPI FLEGREI": "CAMPI FLEGREI", "VESUVIO": "VESUVIO", "ISCHIA": "ISCHIA"}
        if tab_name in zone_map:
            self.map_service.zoom_to_vulcano(zone_map[tab_name])
        else:
            self.map_service.zoom_to_all()
    
    def refresh_map(self):
        self.map_service.refresh_view() # aggiorna la visualizzazione della mappa
    
    def process_pending_updates(self):
        self.map_service.process_pending() # processa gli aggiornamenti in sospeso della mappa