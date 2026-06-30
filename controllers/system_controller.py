import random
from datetime import datetime
from models.system_model import SystemModel, SystemStatus
from utils.helpers import get_random_event
from servers.serverkafka.kafka import KafkaWorker
from PyQt6.QtCore import QObject

class SystemController(QObject):
    """CONTROLLER: Gestisce tutta la logica applicativa, rappresenta il controller di tutta l'architettura"""
    
    def __init__(self, model, audio_service, map_service, view=None, data_worker=None): 
        super().__init__()
        #il costruttore riceve 4 componenti
        self.model = model #modello dei dati
        self.audio_service = audio_service #gestione audio
        self.map_service = map_service #gestione mappa
        self.view = view #interfaccia utente
        self.data_worker = data_worker
        self._elaborando = False
        self._active_filter= "all"

        if self.data_worker is not None:
            from servers.serenade.serenade import SerenadeWorker
            from servers.serverkafka.kafka import KafkaWorker

            if isinstance(self.data_worker, KafkaWorker):
                self.data_worker.message_received.connect(self.on_kafka_message)
            elif isinstance(self.data_worker, SerenadeWorker):
                self.data_worker.message_received.connect(self.on_serenade_message)
    
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
            self.view.flash_title() # il titolo lampeggia
        
        print(f"✅ Sciame attivato su {zone_name}")
        return datetime.now()
    
    def reset(self): #resetta il sistema
        self.audio_service.stop() #stoppa l'audio

        # CORREZIONE: usa self.data_worker invece di self.kafka_worker
        if self.data_worker is not None:
            self.data_worker.stop()

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

    # ─────────────────────────────────────────────────────────
    #  LOGICA MAPPA
    # ─────────────────────────────────────────────────────────
    # def on_map_loaded(self, ok): # stampa un messaggio in console con ...
    #     print("Mappa caricata" if ok else "Errore mappa")
    #     if ok:
    #         self.map_service.set_ready(True)
    #         self.map_service.apply_config()
    def on_map_loaded(self, ok):
     print("Mappa caricata" if ok else "Errore mappa")
     if ok:
        self.map_service.set_ready(True)
        self.map_service.apply_config()
        # Sincronizza il filtro iniziale con quello attivo (default da config)
        if self.view and self.view.map_widget and self.view.map_widget.webview:
            self.view.map_widget.webview.page().runJavaScript(
                f'window.setTimeFilter("{self._active_filter}");'
            )
    
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

    # ─────────────────────────────────────────────────────────
#  LOGICA FILTRO TEMPORALE
# ─────────────────────────────────────────────────────────
    # def on_filter_changed(self, key):
    #  """Filtra gli eventi visualizzati in base all'intervallo temporale."""
    #  from datetime import timedelta
    
    #  ora = datetime.utcnow()
    #  delta = {
    #     "24h":   timedelta(hours=24),
    #     "48h":   timedelta(hours=48),
    #     "7gg":  timedelta(days=7),
    #     "14gg":  timedelta(days=14),
    #     "1 mese": timedelta(days=30),
    #  }.get(key)

    #  if delta is None:
    #     return

    #  cutoff = ora - delta

    #  def filtra(logs):
    #     risultato = []
    #     for entry in logs:
    #         if not isinstance(entry, dict):
    #             continue
    #         try:
    #             data_str = entry.get("data", "")[:19]
    #             data_evento = datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S")
    #             if data_evento >= cutoff:
    #                 risultato.append(entry)
    #         except Exception:
    #             risultato.append(entry)  # se non parsabile lo teniamo
    #     return risultato
 
    #  if self.view is None:
    #     return

    #  for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
    #     logs_filtrati = filtra(self.model.tab_logs.get(zona, []))
    #     self.view.tabs_view.update_logs(zona, logs_filtrati)  


    # ─────────────────────────────────────────────────────────
    #  LOGICA KAFKA
    # ─────────────────────────────────────────────────────────
    # def on_kafka_message(self, msg):
    #     print(f"🔵 [KAFKA] Messaggio ricevuto")  # Debug
        
    #     filtrato = SystemModel.filtra_messaggio_kafka(msg.value)
    #     if filtrato is None:
    #         print("⚠️ [KAFKA] Messaggio filtrato -> None")
    #         return
        
    #     print(f"✅ [KAFKA] Messaggio filtrato: {filtrato.get('area_desc')} - M{filtrato.get('magnitudine')}")  # Debug

    #     # ── print di debug ──────────────────────────
    #     print(
    #         f"\n{'─'*50}"
    #         f"\n[KAFKA] {filtrato['data']}"
    #         f"\n  Tipo     : {filtrato['tipo_desc']}"
    #         f"\n  Area     : {filtrato['area_desc']}"
    #         f"\n  Lat/Lon  : {filtrato['latitudine']}, {filtrato['longitudine']}"
    #         f"\n  Profond. : {filtrato['profondita_km']} km"
    #         f"\n  Magn.    : {filtrato['magnitudine']} ({filtrato['mag_tipo']})"
    #         f"\n  Qualità  : {filtrato['qualita']}  RMS: {filtrato['rms']}  GAP: {filtrato['gap_azimutale']}°"
    #         f"\n{'─'*50}"
    #     )

    #     # ── log_entry come dict ──────────────────────
    #     log_entry = {
    #         "data":          filtrato["data"],
    #         "area_desc":     filtrato["area_desc"],
    #         "magnitudine":   filtrato["magnitudine"],
    #         "profondita_km": filtrato["profondita_km"],
    #         "latitudine":    filtrato["latitudine"],
    #         "longitudine":   filtrato["longitudine"],
    #         "qualita":       filtrato["qualita"],
    #     }

    #     zona = self._normalizza_zona_kafka(filtrato["area"])
    #     self.model.add_log(zona, log_entry)
    #     self.model.add_log("GENERALE", log_entry)

    #     # ── mappa ─────────────────────────────────────
    #     stato = self._normalizza_stato_kafka(filtrato)
    #     print(f"🗺️ [MAP] Aggiornamento mappa: zona={zona}, stato={stato}, mag={filtrato['magnitudine']}")  # Debug
    #     self.map_service.update_vulcano(zona, stato, filtrato["magnitudine"])
        
    #     # Forza il refresh della mappa
    #     self.map_service.refresh_view()

    # def on_filter_changed(self, key):
    #  from datetime import timedelta
    #  self._active_filter = key

    #  ora = datetime.utcnow()
    #  delta = {
    #     "24h":   timedelta(hours=24),
    #     "48h":   timedelta(hours=48),
    #     "7gg":   timedelta(days=7),
    #     "14gg":  timedelta(days=14),
    #     "1mese": timedelta(days=30),   # ← era "1 mese", corretto in "1mese"
    # }.get(key)

    #  if delta is None:
    #     return

    #  cutoff = ora - delta
    # def on_filter_changed(self, key):
    #  """Filtra i puntini sulla mappa e i log in base al periodo."""
    #  # 1. Aggiorna la mappa via JS
    #  if self.view and self.view.map_widget and self.view.map_widget.webview:
    #     self.view.map_widget.webview.page().runJavaScript(
    #         f'window.setTimeFilter("{key}");'
    #     )

    #  def filtra(logs):
    #     risultato = []
    #     for entry in logs:
    #         if not isinstance(entry, dict):
    #             continue
    #         try:
    #             data_str = entry.get("data", "")[:19]
    #             data_evento = datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S")
    #             if data_evento >= cutoff:
    #                 risultato.append(entry)
    #         except Exception:
    #             risultato.append(entry)
    #     return risultato

    #  if self.view is None:
    #     return

    #  for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
    #     logs_filtrati = filtra(self.model.tab_logs.get(zona, []))
    #     self.view.tabs_view.update_logs(zona, logs_filtrati)

    def on_filter_changed(self, key):
     """Filtra i puntini sulla mappa e i log in base al periodo."""
     from datetime import timedelta
     self._active_filter = key

     # 1. Aggiorna la mappa via JS (la mappa gestisce "all" lato JS)
     if self.view and self.view.map_widget and self.view.map_widget.webview:
        self.view.map_widget.webview.page().runJavaScript(
            f'window.setTimeFilter("{key}");'
        )

     if self.view is None:
        return

    # 2. "all" → nessun filtro, mostra tutto
     if key == "all":
        for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
            self.view.tabs_view.update_logs(zona, self.model.tab_logs.get(zona, []))
        return

     delta = {
        "24h":   timedelta(hours=24),
        "48h":   timedelta(hours=48),
        "7gg":   timedelta(days=7),
        "14gg":  timedelta(days=14),
        "1mese": timedelta(days=30),
     }.get(key)

     if delta is None:
        return

     cutoff = datetime.utcnow() - delta

     def filtra(logs):
        risultato = []
        for entry in logs:
            if not isinstance(entry, dict):
                continue
            try:
                data_str = entry.get("data", "")[:19]
                data_evento = datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S")
                if data_evento >= cutoff:
                    risultato.append(entry)
            except Exception:
                risultato.append(entry)
        return risultato

     for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
        logs_filtrati = filtra(self.model.tab_logs.get(zona, []))
        self.view.tabs_view.update_logs(zona, logs_filtrati)

    def on_kafka_message(self, msg):
     print(f"🔵 [KAFKA] Messaggio ricevuto")  # Debug
    
     filtrato = SystemModel.filtra_messaggio_kafka(msg.value)
     if filtrato is None:
        print("⚠️ [KAFKA] Messaggio filtrato -> None")
        return
    
     print(f"✅ [KAFKA] Messaggio filtrato: {filtrato.get('area_desc')} - M{filtrato.get('magnitudine')}")  # Debug

    # ── print di debug ──────────────────────────
     print(
        f"\n{'─'*50}"
        f"\n[KAFKA] {filtrato['data']}"
        f"\n  Tipo     : {filtrato['tipo_desc']}"
        f"\n  Area     : {filtrato['area_desc']}"
        f"\n  Lat/Lon  : {filtrato['latitudine']}, {filtrato['longitudine']}"
        f"\n  Profond. : {filtrato['profondita_km']} km"
        f"\n  Magn.    : {filtrato['magnitudine']} ({filtrato['mag_tipo']})"
        f"\n  Qualità  : {filtrato['qualita']}  RMS: {filtrato['rms']}  GAP: {filtrato['gap_azimutale']}°"
        f"\n{'─'*50}"
     )

    # ── AGGIUNGI IL PUNTINO SULLA MAPPA (come fa Serenade) ──
     lat = filtrato.get('latitudine')
     lon = filtrato.get('longitudine')
     mag = filtrato.get('magnitudine')
     time_str = filtrato.get('data', '')
     qualita = filtrato.get('qualita', 'n.d.')
    
     if lat is not None and lon is not None:
        # Crea una lista con un singolo evento (come fa Serenade ma con un solo elemento)
        batch_event = [{
            "lat": lat,
            "lng": lon,
            "mag": mag,
            "data": time_str,
            "qualita": qualita
        }]
        # Aggiungi l'evento come puntino sulla mappa usando add_eventi_batch
        self.map_service.add_eventi_batch(batch_event)
        print(f"📍 [MAP] Aggiunto puntino: lat={lat}, lon={lon}, mag={mag}")

    # ── log_entry come dict ──────────────────────
     log_entry = {
        "data":          filtrato["data"],
        "area_desc":     filtrato["area_desc"],
        "magnitudine":   filtrato["magnitudine"],
        "profondita_km": filtrato["profondita_km"],
        "latitudine":    filtrato["latitudine"],
        "longitudine":   filtrato["longitudine"],
        "qualita":       filtrato["qualita"],
    }

     zona = self._normalizza_zona_kafka(filtrato["area"])
     self.model.add_log(zona, log_entry)
     self.model.add_log("GENERALE", log_entry)

    # ── mappa - aggiorna lo stato del vulcano ─────────────────────
     stato = self._normalizza_stato_kafka(filtrato)
     print(f"🗺️ [MAP] Aggiornamento vulcano: zona={zona}, stato={stato}, mag={filtrato['magnitudine']}")  # Debug
     self.map_service.update_vulcano(zona, stato, filtrato["magnitudine"])
    
    # Forza il refresh della mappa
     self.map_service.refresh_view()

    def _normalizza_zona_kafka(self, area: str | None) -> str:
        AREA_MAP = {
            'vesuvio':  'VESUVIO',
            'flegrei':  'CAMPI FLEGREI',
            'ischia':   'ISCHIA',
        }
        if not area:
            return 'GENERALE'
        return AREA_MAP.get(area.lower().strip(), 'GENERALE')

    def _normalizza_stato_kafka(self, filtrato):
        mag = filtrato.get("magnitudine")
        
        # Gestione dei valori None
        if mag is None:
            # Se non c'è magnitudo, controlla se ci sono dati di qualità
            if filtrato.get("qualita") and filtrato.get("qualita") != "n.d.":
                return SystemStatus.NORMALE.value
            return SystemStatus.NORMALE.value
        
        # Soglie in ordine DECRESCENTE
        if mag >= 3.5:  # Allarme per magnitudo >= 3.5
            return SystemStatus.ALLARME.value
        elif mag >= 2.0:  # Attenzione per magnitudo >= 2.0
            return SystemStatus.ATTENZIONE.value
        else:  # Normale per magnitudo < 2.0
            return SystemStatus.NORMALE.value

    # ─────────────────────────────────────────────────────────
    #  LOGICA SERENADE
    # ─────────────────────────────────────────────────────────
    def on_serenade_message(self, eventi):
        if self._elaborando:
            return
        self._elaborando = True

        try:
            if isinstance(eventi, dict):
                records = list(eventi.values())
            else:
                records = list(eventi)

            self.map_service.clear_eventi()

            batch_map = []
            log_generale = []
            log_per_zona = {}   # {"CAMPI FLEGREI": [...], "VESUVIO": [...], ...}

            for evento in records:
                try:
                    loc      = evento.get("location", {})
                    mags     = loc.get("magnitudos", [])
                    mag      = mags[0]["value"] if mags else None
                    lat      = loc.get("latitude")
                    lon      = loc.get("longitude")
                    dep      = loc.get("depth")
                    time_str = evento.get("date", "")[:19]
                    area     = evento.get("adesc", "Campi Flegrei")
                    qualita  = loc.get("quality", "n.d.")

                    if lat is None or lon is None:
                        continue

                    batch_map.append({
                        "lat": lat, "lng": lon, "mag": mag,
                        "data": time_str, "qualita": qualita
                    })

                    log_entry = {
                        "data":         time_str,
                        "area_desc":    area,
                        "magnitudine":  mag,
                        "profondita_km": dep,
                        "latitudine":   lat,
                        "longitudine":  lon,
                        "qualita":      qualita,
                    }

                    log_generale.append(log_entry)

                    zona_raw = evento.get("area", "").lower().strip()
                    zona_tab = {
                        "flegrei": "CAMPI FLEGREI",
                        "vesuvio": "VESUVIO",
                        "ischia":  "ISCHIA"
                    }.get(zona_raw)

                    if zona_tab:
                        log_per_zona.setdefault(zona_tab, []).append(log_entry)

                except Exception as e:
                    print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")

            # ── Un solo aggiornamento UI per tutti i log ──────────────────
            if log_generale:
                self.model.add_log_batch("GENERALE", log_generale)

            for zona, msgs in log_per_zona.items():
                self.model.add_log_batch(zona, msgs)

            # ── Una sola chiamata JS per la mappa ─────────────────────────
            self.map_service.add_eventi_batch(batch_map)

        finally:
            self._elaborando = False

    def _normalizza_stato_serenade(self, mag):
        if mag is None:
            return SystemStatus.NORMALE.value
        if mag > 5.0:
            return SystemStatus.ALLARME.value
        elif mag >= 3.5:
            return SystemStatus.ALLARME.value
        elif mag >= 2.0:
            return SystemStatus.ATTENZIONE.value
        else:
            return SystemStatus.NORMALE.value
        
    def _filtra_e_aggiorna_logs(self):
     """Riapplica il filtro attivo e aggiorna la vista. Da chiamare dopo ogni batch."""
     if self.view is None:
        return
     self.on_filter_changed(self._active_filter)