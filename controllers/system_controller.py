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
        self.data_worker =data_worker

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
           # self.view.update_ui() #aggiorna l'interfaccia
            self.view.flash_title() # il titolo lampeggia
        
        print(f"✅ Sciame attivato su {zone_name}")
        return datetime.now()
    
    def reset(self): #resetta il sistema
        self.audio_service.stop() #stoppa l'audio

        if self.kafka_worker is not None:
            self.kafka_worker.stop()

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
            #self.view.update_ui()
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
    
    # def get_current_time(self):
    #     return datetime.now().strftime("%H:%M:%S")
    
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

    # def on_kafka_message(self, msg):
    #     data = msg.value  # oppure msg.payload ecc.
    #     print( "MESSAGGIO KAFKA RICEVUTO", data)

    #     self.model.last_event_time = datetime.now()

        # metodo commentato al momento per evitare che il flusso di log da kafka 
        # si vedano anche nell'interfaccia 
        # self.model.add_log( "GENERALE",f"Kafka: {data}")

    def on_kafka_message(self, msg):
     filtrato = SystemModel.filtra_messaggio_kafka(msg.value)
     if filtrato is None:
        #print(f"[KAFKA] Messaggio non riconosciuto - topic:{msg.topic} class:{msg.message_class}")
        return
     
     mag_str = f"M{filtrato['magnitudine']}" if filtrato['magnitudine'] is not None else "M n.d."
     log_msg = (
        f"[KAFKA] {filtrato['data']} | "
        f"{filtrato['area_desc']} | "
        f"{mag_str} | "
        f"Prof. {filtrato['profondita_km']} km | "
        f"({filtrato['latitudine']}, {filtrato['longitudine']}) | "
        #f"Metodo: {filtrato['metodo']} | "
        f"Qualità: {filtrato['qualita']}"
     )


     print(
        f"\n{'─'*50}"
        f"\n[KAFKA] {filtrato['data']}"
        f"\n  Tipo     : {filtrato['tipo_desc']}"
        f"\n  Area     : {filtrato['area_desc']}"
        f"\n  Lat/Lon  : {filtrato['latitudine']}, {filtrato['longitudine']}"
        f"\n  Profond. : {filtrato['profondita_km']} km"
        f"\n  Magn.    : {filtrato['magnitudine'] if filtrato['magnitudine'] is not None else 'non disponibile'} ({filtrato['mag_tipo']})"
        f"\n  Qualità  : {filtrato['qualita']}  RMS: {filtrato['rms']}  GAP: {filtrato['gap_azimutale']}°"
        f"\n  Metodo   : {filtrato['metodo']}  Picks: {filtrato['n_picks']}"
        f"\n{'─'*50}"
     )
     #self.model.add_log( "GENERALE",f"Kafka: {filtrato}") 
     #zona = filtrato['area'].upper() if filtrato['area'] else 'GENERALE'
     zona = self._normalizza_zona_kafka(filtrato['area'])
     self.model.add_log(zona, log_msg)
     self.model.add_log("GENERALE", log_msg)

     stato = self._normalizza_stato_kafka(filtrato)

     self.map_service.update_vulcano(
     zona,
     stato,
     filtrato['magnitudine']
     )
 
    #  self.map_service.update_vulcano(
    #     zona,
    #     filtrato['tipo_desc'],
    #     filtrato['magnitudine']
    # )
    




    def _normalizza_zona_kafka(self, area: str | None) -> str:
     AREA_MAP = {
        'vesuvio':  'VESUVIO',
        'flegrei':  'CAMPI FLEGREI',
        'ischia':   'ISCHIA',
     }
     if not area:
        return 'GENERALE'
     return AREA_MAP.get(area.lower().strip(), 'GENERALE')

    # def _normalizza_stato_kafka(self, filtrato):
    #  mag = filtrato.get("magnitudine")

    #  if mag is None or mag >= 0.1:
    #     return "normale"
     
    #  if filtrato.get("n_eventi_ora", 0) > 10:
    #      return "sciame"

    #  if mag >= 3.0:
    #     return "sciame"
    #  elif mag > 5.0:
    #     return "allarme"
    #  else:
    #     return "critico"

    def _normalizza_stato_kafka(self, filtrato):
     mag = filtrato.get("magnitudine")

     # Prima controlla lo sciame (indipendente dalla magnitudo)
     if filtrato.get("n_eventi_ora", 0) > 10:
        return SystemStatus.SCIAME.value

     if mag is None:
        return SystemStatus.NORMALE.value

     # Soglie in ordine DECRESCENTE
     if mag > 5.0:
        return SystemStatus.ALLARME.value
     elif mag >= 3.5:
        return SystemStatus.ALLARME.value
     elif mag >= 2.0:
        return SystemStatus.ATTENZIONE.value
     else:
        return SystemStatus.NORMALE.value
     
    # def on_serenade_message(self, eventi: list):
    #  """Riceve la lista JSON da SerenadeWorker ad ogni polling."""
    #  for evento in eventi:
    #     try:
    #         mag  = evento.get("magnitude", {}).get("ml") or evento.get("magnitude", {}).get("mw")
    #         lat  = evento.get("latitude")
    #         lon  = evento.get("longitude")
    #         dep  = evento.get("depth")
    #         time_str = evento.get("time", "")[:19].replace("T", " ")

    #         mag_str = f"M{mag:.1f}" if mag is not None else "M n.d."
    #         log_msg = (
    #             f"[SERENADE] {time_str} | "
    #             f"{mag_str} | "
    #             f"Prof. {dep} km | "
    #             f"({lat}, {lon})"
    #         )

    #         print(log_msg)
    #         self.model.add_log("GENERALE", log_msg)
    #         self.model.add_log("CAMPI FLEGREI", log_msg)  # Serenade è su Flegrei

    #         stato = self._normalizza_stato_serenade(mag)
    #         self.map_service.update_vulcano("CAMPI FLEGREI", stato, mag)

    #     except Exception as e:
    #         print(f"[SERENADE] Errore parsing evento: {e}")

    # def on_serenade_message(self, eventi: list):
    #  print("TIPO:", type(eventi))
    #  print("LUNGHEZZA:", len(eventi))
    #  if eventi:
    #     print("PRIMO ELEMENTO TIPO:", type(eventi[0]))
    #     print("PRIMO ELEMENTO:", eventi[0])
    #  return  # blocca tutto il resto finché non vediamo la struttura

    # def on_serenade_message(self, eventi: list):
    # # eventi è in realtà un dict {id: {...}, id: {...}}
    # # il segnale emette r.json() che può essere dict o list
    
    #  if isinstance(eventi, dict):
    #     records = eventi.values()   # prendi i valori, non le chiavi
    #  else:
    #     records = eventi

    #  self.map_service.clear_eventi() 

    #  for evento in records:
    #     try:
    #         loc      = evento.get("location", {})
    #         mags     = loc.get("magnitudos", [])
    #         mag      = mags[0]["value"] if mags else None
    #         lat      = loc.get("latitude")
    #         lon      = loc.get("longitude")
    #         dep      = loc.get("depth")
    #         time_str = evento.get("date", "")[:19]
    #         area     = evento.get("adesc", "Campi Flegrei")
    #         qualita  = loc.get("quality", "n.d.")

    #         if lat is None or lon is None:
    #             continue

    #         self.map_service.add_evento(lat, lon, mag, time_str, qualita)


    #         mag_str = f"M{mag:.1f}" if mag is not None else "M n.d."
    #         log_msg = (
    #             f"[SERENADE] {time_str} | "
    #             f"{area} | "
    #             f"{mag_str} | "
    #             f"Prof. {dep} km | "
    #             f"({lat}, {lon}) | "
    #             f"Qualità: {qualita}"
    #         )

    #         print(log_msg)
    #         self.model.add_log("GENERALE", log_msg)
    #         self.model.add_log("CAMPI FLEGREI", log_msg)

    #         #stato = self._normalizza_stato_serenade(mag)
    #         #self.map_service.update_vulcano("CAMPI FLEGREI", stato, mag)

    #     except Exception as e:
    #         print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")

    def on_serenade_message(self, eventi):
     if isinstance(eventi, dict):
        records = list(eventi.values())
     else:
        records = list(eventi)

     self.map_service.clear_eventi()

     batch = []  # lista di tutti gli eventi da passare in una volta

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

            batch.append({
                "lat": lat,
                "lng": lon,
                "mag": mag,
                "data": time_str,
                "qualita": qualita
            })

            mag_str = f"M{mag:.1f}" if mag is not None else "M n.d."
            log_msg = (
                f"[SERENADE] {time_str} | {area} | {mag_str} | "
                f"Prof. {dep} km | ({lat}, {lon}) | Qualità: {qualita}"
            )
            print(log_msg)
            #self.model.add_log("GENERALE", log_msg)
            #self.model.add_log("CAMPI FLEGREI", log_msg)
            self.model.add_log("GENERALE", log_msg)

            area = evento.get("area", "").lower().strip()
            zona_tab = {
            "flegrei": "CAMPI FLEGREI",
            "vesuvio":  "VESUVIO",
            "ischia":   "ISCHIA"
            }.get(area)

            if zona_tab:
             self.model.add_log(zona_tab, log_msg)
        


        except Exception as e:
            print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")

     # una sola chiamata JS per tutti gli eventi
     self.map_service.add_eventi_batch(batch)

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

    def reset(self):
     self.audio_service.stop()

     if self.data_worker is not None:   # ← era self.kafka_worker, nome sbagliato
        self.data_worker.stop()

     self.model.status = SystemStatus.NORMALE
     self.model.last_event_time = None

     timestamp = datetime.now().strftime('%H:%M:%S')
     self.model.add_log("GENERALE", f"[{timestamp}] RESET SISTEMA")

     for zona in ["VESUVIO", "CAMPI FLEGREI", "ISCHIA"]:
        self.map_service.update_vulcano(zona, SystemStatus.NORMALE.value)

     if self.view:
        self.view.reset_window_title()

    



        