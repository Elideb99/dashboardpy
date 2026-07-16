# from datetime import datetime
# from models.system_model import SystemModel, SystemStatus
# from services.swarm_detector import SwarmDetector
# from PyQt6.QtCore import QObject,QTimer
# import json
# from datetime import datetime
# from services.kafka_recorder import KafkaRecorder
# from utils.helpers import seleziona_ultima_scossa
# from views.dialogs import AlarmDialog  # adatta il path al file reale, es. views/alarm_dialog.py


# class SystemController(QObject):
#     """CONTROLLER: Gestisce tutta la logica applicativa, rappresenta il controller di tutta l'architettura"""

#     _SWARM_SEVERITY = {
#         "SCIAME IN CORSO": 1,
#         "SCIAME INIZIATO": 2,
#         "SCIAME TERMINATO": 3,
#         "ATTIVITÀ ORDINARIA": 4,
#         "NESSUNO": 5,
#     }
    
#     def __init__(self, model, audio_service, map_service, view=None, data_worker=None ,data_thread=None, kafka_date_from=None): 
#         super().__init__()
#         #il costruttore riceve 4 componenti
#         self.model = model #modello dei dati
#         self.audio_service = audio_service #gestione audio
#         self.map_service = map_service #gestione mappa
#         self.view = view #interfaccia utente
#         self.data_worker = data_worker
#         self.data_thread=data_thread
#         self.kafka_date_from= kafka_date_from
#         self._elaborando = False
#         self._active_filter= "all"
#         self._alarmed_event_ids = set()
#         self._use_arrival_order_for_status = True   # TEST replay
#         self._latest_status_event_time = None       # modalità reale

#         self.swarm_detectors = {
#          "CAMPI FLEGREI": SwarmDetector(),
#          "VESUVIO": SwarmDetector(),
#          "ISCHIA": SwarmDetector(),
#         }
#         self.swarm_states = {}        # zona -> (state, color, tooltip) da SwarmDetector
#         self.official_swarms = {}     # zona -> ultimo comunicato ufficiale ricevuto da Kafka
#         self.kafka_recorder = KafkaRecorder()



#         #temporaneo
#         # self._kafka_date_from = None
#         # if kafka_date_from:
#         #     try:
#         #         self._kafka_date_from = datetime.fromisoformat(kafka_date_from)
#         #     except ValueError:
#         #         print(f"⚠️ [CONFIG] kafka.date_from non valido: {kafka_date_from!r}")

#         #


#         if self.data_worker is not None:
#             from servers.serenade.serenade import SerenadeWorker
#             from servers.serverkafka.kafka import KafkaWorker

#             if isinstance(self.data_worker, KafkaWorker):
#                 self.data_worker.message_received.connect(self.on_kafka_message)
#                 self.data_worker.swarm_message_received.connect(self.on_kafka_swarm_message)  # ← nuovo

#             elif isinstance(self.data_worker, SerenadeWorker):
#                 self.data_worker.message_received.connect(self.on_serenade_message)

    
#     # ─────────────────────────────────────────────────────────
#     #  LOGICA TEMPO
#     # ─────────────────────────────────────────────────────────
#     def get_time_since_last_event(self):
#         if self.model.last_event_time is None:
#             return None
#         # se non c'è stato alcun evento restituisce none 
        
#         diff = datetime.now() - self.model.last_event_time
#         seconds = int(diff.total_seconds())
#         # calcola la differenza tra ora attuale e ultimo evento
        
#         if seconds < 60:
#             return f"{seconds} secondi fa"
#         elif seconds < 3600:
#             return f"{seconds // 60} minuti e {seconds % 60} secondi fa"
#         else:
#             return f"{seconds // 3600} ore e {(seconds % 3600) // 60} minuti fa"
    
#     def get_current_date(self):
#         return datetime.now().strftime("%d/%m/%Y")
    
#     def get_current_date_utc(self):
#         """Restituisce la data UTC corrente"""
#         return datetime.utcnow().strftime("%d/%m/%Y")
    
#     def get_current_time(self):
#         return datetime.now().strftime("%H:%M:%S")

#     def get_utc_time(self):
#         """Restituisce l'ora UTC corrente"""
#         return datetime.utcnow().strftime("%H:%M:%S")

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA MAPPA
#     # ─────────────────────────────────────────────────────────

#     def on_map_loaded(self, ok):
#      print("Mappa caricata" if ok else "Errore mappa")
#      if ok:
#         self.map_service.set_ready(True)
#         self.map_service.apply_config()
#         if self.view and self.view.map_widget and self.view.map_widget.webview:
#             self.view.map_widget.webview.page().runJavaScript(
#                 f'if (window.setTimeFilter) {{ window.setTimeFilter("{self._active_filter}"); }}'
#             )
#         if self.data_thread is not None and not self.data_thread.isRunning():
#             self.data_thread.start()
    
#     def on_tab_changed(self, tab_name): # gestisce lo zoom delle zone sismiche
#         if not self.map_service.map_ready:
#             return
#         zone_map = {"CAMPI FLEGREI": "CAMPI FLEGREI", "VESUVIO": "VESUVIO", "ISCHIA": "ISCHIA"}
#         if tab_name in zone_map:
#             self.map_service.zoom_to_vulcano(zone_map[tab_name])
#         else:
#             self.map_service.zoom_to_all()
    
#     def refresh_map(self):
#         self.map_service.refresh_view() # aggiorna la visualizzazione della mappa
    
#     def process_pending_updates(self):
#         self.map_service.process_pending() # processa gli aggiornamenti in sospeso della mappa

#     def on_filter_changed(self, key):
#      """Cambia il filtro temporale attivo: aggiorna mappa e tabelle."""
#      self._active_filter = key

#     #  if self.view and self.view.map_widget and self.view.map_widget.webview:
#     #     self.view.map_widget.webview.page().runJavaScript(
#     #         f'window.setTimeFilter("{key}");'
#     #     )
#      if (self.map_service.map_ready
#             and self.view and self.view.map_widget and self.view.map_widget.webview):
#         self.view.map_widget.webview.page().runJavaScript(
#             f'if (window.setTimeFilter) {{ window.setTimeFilter("{key}"); }}'
#         )

#      self.render_logs_filtrati()

#     def _riferimento_temporale(self):
#      """Istante da cui misurare i filtri: l'ultima scossa presente nei dati,
#      così i filtri funzionano anche rigiocando registrazioni vecchie.
#      Se non ci sono eventi, usa l'ora reale."""
#      from datetime import datetime
#      date = []
#      for e in self.model.tab_logs.get("GENERALE", []):
#         if isinstance(e, dict) and e.get("data"):
#             try:
#                 date.append(datetime.strptime(
#                     str(e["data"]).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S"))
#             except Exception:
#                 pass
#      return max(date) if date else datetime.utcnow()

#     def _logs_filtrati(self, logs):
#      """Applica il filtro temporale attivo a una lista di log."""
#      from datetime import datetime, timedelta

#      def ordina(ls):
#         return sorted(ls, key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
#                       reverse=True)

#      key = self._active_filter
#      if key == "all":
#         return ordina(logs)

#      delta = {
#         "24h": timedelta(hours=24),
#         "48h": timedelta(hours=48),
#         "7gg": timedelta(days=7),
#         "14gg": timedelta(days=14),
#         "1mese": timedelta(days=30),
#      }.get(key)
#      if delta is None:
#         return ordina(logs)

#      cutoff = self._riferimento_temporale() - delta
#      risultato = []
#      for entry in logs:
#         if not isinstance(entry, dict):
#             continue
#         try:
#             data_str = str(entry.get("data", "")).replace("T", " ")[:19]
#             if datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S") >= cutoff:
#                 risultato.append(entry)
#         except Exception:
#             pass
#      return ordina(risultato)

#     def render_logs_filtrati(self):
#      """Ridisegna le tabelle applicando il filtro attivo (senza toccare la mappa)."""
#      if self.view is None:
#         return
#      for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
#         logs = self.model.tab_logs.get(zona, [])
#         self.view.tabs_view.update_logs(zona, self._logs_filtrati(logs))


#     def on_kafka_message(self, msg):
#      print(f"🔵 [KAFKA] Messaggio ricevuto")  # Debug

#       # Registra il messaggio Kafka
#      self.kafka_recorder.save(msg.value)



#     # -------------------------------------------------
#     # NORMALE ELABORAZIONE KAFKA
#     # -------------------------------------------------

#      if isinstance(msg.value, list):
#         nomi_blocchi = [
#             item.get("name")
#             for item in msg.value
#             if isinstance(item, dict)
#         ]

#         print(
#             f"[KAFKA] Blocchi presenti (lista): "
#             f"{nomi_blocchi}"
#         )

#      elif isinstance(msg.value, dict):
#         print(
#             f"[KAFKA] Messaggio DICT. "
#             f"Chiavi: {list(msg.value.keys())}"
#         )

#         print(
#             json.dumps(
#                 msg.value,
#                 indent=2,
#                 default=str
#             )
#         )

#      else:
#         print(
#             f"[KAFKA] Tipo inatteso: "
#             f"{type(msg.value)}"
#         )

    

#      # temporaneo per vedere il file json per intero 
#      #print(f"[RAW] {json.dumps(msg.value, indent=2, default=str)}")
    
#     #  filtrato = SystemModel.filtra_messaggio_kafka(msg.value)
#     #  print("TIPO EVENTO:", filtrato.get("tipo"))
#     #  print("DESCRIZIONE TIPO:", filtrato.get("tipo_desc"))
#     #  if filtrato is None:
#     #     print("⚠️ [KAFKA] Messaggio filtrato -> None")
#     #     return

#      filtrato = SystemModel.filtra_messaggio_kafka(msg.value)

#      if filtrato is None:
#       print("⚠️ [KAFKA] Messaggio filtrato -> None")
#       return
 
#      print("TIPO EVENTO:", filtrato.get("tipo"))
#      print("DESCRIZIONE TIPO:", filtrato.get("tipo_desc"))
     
#      # temporaneo 



#     # ── print di debug ──────────────────────────
#      print(
#         f"\n{'─'*50}"
#         f"\n[KAFKA] {filtrato['data']}"
#         f"\n  Tipo     : {filtrato['tipo_desc']}"
#         f"\n  Area     : {filtrato['area_desc']}"
#         f"\n  Lat/Lon  : {filtrato['latitudine']}, {filtrato['longitudine']}"
#         f"\n  Profond. : {filtrato['profondita_km']} km"
#         f"\n  Magn.    : {filtrato['magnitudine']} ({filtrato['mag_tipo']})"
#         f"\n  Qualità  : {filtrato['qualita']}  RMS: {filtrato['rms']}  GAP: {filtrato['gap_azimutale']}°"
#         f"\n{'─'*50}"
#      )

#      from services.alarm_service import should_alarm 
#      event_id = filtrato.get("event_id")
#      if (event_id
#              and event_id not in self._alarmed_event_ids
#              and not self.model.is_manuale(filtrato)
#              and should_alarm(filtrato)):
#       self._alarmed_event_ids.add(event_id)
#       self._trigger_alarm(filtrato)


#     # ── AGGIUNGI IL PUNTINO SULLA MAPPA (come fa Serenade) ──
#      lat = filtrato.get('latitudine')
#      lon = filtrato.get('longitudine')
#      mag = filtrato.get('magnitudine')
#      time_str = filtrato.get('data', '')
#      qualita = filtrato.get('qualita', 'n.d.')
    
#      if lat is not None and lon is not None and mag is not None:
#         # Crea una lista con un singolo evento (come fa Serenade ma con un solo elemento)
#         batch_event = [{
#             "lat": lat,
#             "lng": lon,
#             "mag": mag,
#             "data": time_str,
#             "qualita": qualita,
#             "area":filtrato.get('area_desc', 'n.d')
#         }]
#         # Aggiungi l'evento come puntino sulla mappa usando add_eventi_batch
#         self.map_service.add_eventi_batch(batch_event)

#     # ── log_entry come dict ──────────────────────
#      log_entry = {
#         "event_id":      filtrato.get("event_id"),
#         "data":          filtrato["data"],
#         "area":          filtrato.get("area"),
#         "area_desc":     filtrato["area_desc"],
#         "magnitudine":   filtrato["magnitudine"],
#         "profondita_km": filtrato["profondita_km"],
#         "latitudine":    filtrato["latitudine"],
#         "longitudine":   filtrato["longitudine"],
#         "qualita":       filtrato["qualita"],
#         "tipo":          filtrato["tipo"],
#         "tipo_desc":     filtrato["tipo_desc"],
#         "communicate":   filtrato.get("communicate"),
#         "author":        filtrato.get("author"),
        
#     }

#      zona = self._normalizza_zona_kafka(filtrato["area"])
#      self.model.add_log(zona, log_entry)
#      self.model.add_log("GENERALE", log_entry)
#      self._update_swarm_widget(zona)
#      if self.view:
#         self.view.tabs_view.update_zone_cards(self.model.tab_logs, source="kafka")
#         self._filtra_e_aggiorna_logs()


#     # # ── mappa - aggiorna lo stato del vulcano ─────────────────────

#     #  ultimo_generale = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)
#     #  if ultimo_generale:
#     #     self.map_service.update_vulcano(
#     #     zona,
#     #     self.model.status.value,
#     #     ultimo_generale.get("magnitudine")
#     #   )

#     # ── AGGIORNAMENTO STATO SISTEMA ────────────────────────────────

# #      if self._use_arrival_order_for_status:
# #      # MODALITÀ TEST REPLAY:
# #      # lo stato dipende dall'ultimo messaggio ricevuto da Kafka,
# #      # senza considerare la sua data.
# #       evento_stato = self.model.aggiorna_stato_da_evento_ricevuto(
# #         log_entry
# #       )

# #      if evento_stato:
# #         print(
# #             f"🧪 [STATO - ORDINE ARRIVO] "
# #             f"{evento_stato.get('data')} - "
# #             f"M{evento_stato.get('magnitudine')} - "
# #             f"{self.model.status.value}"
# #         )

# #      else:
# #     # MODALITÀ REALE:
# #     # lo stato dipende dall'evento automatico cronologicamente
# #     # più recente presente nei log.
# #       evento_stato = self.model.aggiorna_stato_da_logs(
# #         seleziona_ultima_scossa
# #       )

# #       if evento_stato:
# #         print(
# #             f"🕒 [STATO - ORDINE CRONOLOGICO] "
# #             f"{evento_stato.get('data')} - "
# #             f"M{evento_stato.get('magnitudine')} - "
# #             f"{self.model.status.value}"
# #         )


# # # Aggiorna la zona relativa all'evento che ha determinato lo stato
# #      if evento_stato:
# #        zona_stato = self._normalizza_zona_kafka(
# #        evento_stato.get("area")
# #        )

# #        self.map_service.update_vulcano(
# #         zona_stato,
# #         self.model.status.value,
# #         evento_stato.get("magnitudine")
# #      )

#     # ── AGGIORNAMENTO STATO SISTEMA ────────────────────────────────

#      evento_stato = None

#      if self._use_arrival_order_for_status:
#      # TEST REPLAY:
#     # usa esattamente il messaggio appena entrato da Kafka.
#       evento_stato = self.model.aggiorna_stato_da_evento_ricevuto(
#         log_entry
#       )

#       if evento_stato is not None:
#         print(
#             f"🧪 [STATO - ORDINE ARRIVO] "
#             f"data={evento_stato.get('data')} | "
#             f"M={evento_stato.get('magnitudine')} | "
#             f"author={evento_stato.get('author')} | "
#             f"stato={self.model.status.value}"
#         )
#       else:
#         print(
#             f"⏭️ [STATO - ORDINE ARRIVO] Evento ignorato: "
#             f"data={log_entry.get('data')} | "
#             f"M={log_entry.get('magnitudine')} | "
#             f"author={log_entry.get('author')}"
#         )

#      else:
#     # MODALITÀ REALE:
#     # cerca l'evento cronologicamente più recente nei log.
#       evento_stato = self.model.aggiorna_stato_da_logs(
#         seleziona_ultima_scossa
#       )

#       if evento_stato is not None:
#         print(
#             f"🕒 [STATO - ORDINE CRONOLOGICO] "
#             f"data={evento_stato.get('data')} | "
#             f"M={evento_stato.get('magnitudine')} | "
#             f"stato={self.model.status.value}"
#         )


# # Aggiorna la mappa soltanto se è stato selezionato un evento valido
#      if evento_stato is not None:
#       self.model.last_event_time = datetime.now()
#       zona_stato = self._normalizza_zona_kafka(
#         evento_stato.get("area")
#       )

#       self.map_service.update_vulcano(
#         zona_stato,
#         self.model.status.value,
#         evento_stato.get("magnitudine")
#        )
      
#     QUIETE_DOPO_SECONDI = 15 * 60 # quiete dopo 15 minuti 

#     def controlla_quiete(self):
#         t = self.model.last_event_time
#         if t is None:
#             return
#         if (datetime.now() - t).total_seconds() >= self.QUIETE_DOPO_SECONDI:
#             self.model.reset_a_quiete()


#     # Forza il refresh della mappa

#     def _normalizza_zona_kafka(self, area: str | None) -> str:
#         AREA_MAP = {
#             'vesuvio':  'VESUVIO',
#             'flegrei':  'CAMPI FLEGREI',
#             'ischia':   'ISCHIA',
#         }
#         if not area:
#             return 'GENERALE'
#         return AREA_MAP.get(area.lower().strip(), 'GENERALE')
    
#     DURATA_ALLARME_MS = 8000

#     def _trigger_alarm(self, filtrato: dict):
#         self.audio_service.play()
#         print(f"🚨 [ALLARME] Evento automatico M{filtrato['magnitudine']} — "
#               f"{filtrato['area_desc']} — {filtrato['data']}")

#         if not self.view:
#             return

#         # se ce n'è già uno a schermo lo chiudo: vince l'allarme più recente
#         if self._alarm_dialog is not None:
#             self._alarm_dialog.close()

#         dialog = AlarmDialog(
#             parent=self.view,
#             ui_scale=self.view.ui_scale,
#             magnitudo=filtrato.get("magnitudine"),
#             zona=filtrato.get("area_desc", "n.d.")
#         )
#         dialog.setModal(False)
#         self._alarm_dialog = dialog      # senza questo il popup sparisce all'istante
#         dialog.show()
#         dialog.raise_()
#         QTimer.singleShot(self.DURATA_ALLARME_MS, dialog.close)

    
    
#     # def _trigger_alarm(self, filtrato: dict):
#     #  self.audio_service.play()
#     #  print(f"🚨 [ALLARME] Evento automatico M{filtrato['magnitudine']} — {filtrato['area_desc']} — {filtrato['data']}")

#     #  if self.view:
#     #     dialog = AlarmDialog(
#     #         parent=self.view,
#     #         ui_scale=self.view.ui_scale,   # <-- adatta se lo scale factor si chiama/si trova diversamente
#     #         magnitudo=filtrato.get("magnitudine"),
#     #         zona=filtrato.get("area_desc", "n.d.")
#     #     )
#     #     dialog.exec()
    

#     def on_kafka_swarm_message(self, msg):
#      self.kafka_recorder.save(msg.value, topic=getattr(msg, "topic", None))
#      dati = msg.value
#      if not isinstance(dati, dict):
#         print(f"⚠️ [KAFKA SWARM] Formato inatteso: {type(dati)}")
#         return

#      zona = self._normalizza_zona_kafka(dati.get("area"))
#      tipo_comunicato = dati.get("type")
#      sciame_finito = tipo_comunicato == "end" or bool((dati.get("end_time") or "").strip())

#      print(f"📢 [KAFKA SWARM] {zona} - tipo: {tipo_comunicato} - Ev#{dati.get('event_number')} - Md{dati.get('max_md')}")

#      if sciame_finito:
#         tooltip = f"Sciame concluso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"
#         self.official_swarms.pop(zona, None)

#         # Mostra esplicitamente lo stato di chiusura ufficiale
#         self.swarm_states[zona] = ("SCIAME TERMINATO", "#2e7d32", tooltip)
#         if self.view and hasattr(self.view, "tabs_view"):
#             self.view.tabs_view.update_zone_swarm_state(zona, "SCIAME TERMINATO", "#2e7d32", tooltip)

#         # Allinea anche il detector euristico, così non riproponga subito INIZIATO/IN CORSO
#         if zona in self.swarm_detectors:
#             self.swarm_detectors[zona].previous_state = "SCIAME TERMINATO"

#         self._update_global_swarm_banner()
#         return

#      self.official_swarms[zona] = dati

#      if tipo_comunicato == "news":
#       etichetta = "SCIAME INIZIATO"
#       colore = "#EF6C00"
#       tooltip = f"Nuovo sciame rilevato — Md {dati.get('max_md', '?')}"
#      else:
#       etichetta = "SCIAME IN CORSO"
#       colore = "#c62828"
#       tooltip = f"Sciame in corso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"

#      self.swarm_states[zona] = (etichetta, colore , tooltip)

#      if self.view and hasattr(self.view, "tabs_view"):
#       self.view.tabs_view.update_zone_swarm_state(zona, etichetta, colore, tooltip)

#      self._update_global_swarm_banner()

    

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA SERENADE
#     # ─────────────────────────────────────────────────────────

#     def on_serenade_message(self, eventi):
#      if self._elaborando:
#         return
#      self._elaborando = True

#      try:
#         if isinstance(eventi, dict):
#             records = list(eventi.values())
#         else:
#             records = list(eventi)

#         # ── DEBUG: quali "type" distinti arrivano da Serenade? ──
#         tipi_trovati = set()
#         for evento in records:
#             if isinstance(evento, dict):
#                 tipi_trovati.add(evento.get("type", "MANCANTE"))
#         print(f"[SERENADE] Tipi di evento trovati in questo batch: {tipi_trovati}")
#         print(f"[SERENADE] Numero totale eventi nel batch: {len(records)}")

#         self.map_service.clear_eventi()

#         batch_map = []
#         log_generale = []
#         log_per_zona = {}

#         for evento in records:
#             try:
#                 loc      = evento.get("location", {})
#                 mags     = loc.get("magnitudos", [])
#                 mag      = mags[0]["value"] if mags else None
#                 lat      = loc.get("latitude")
#                 lon      = loc.get("longitude")
#                 dep      = loc.get("depth")
#                 time_str = evento.get("date", "")[:19]
#                 area     = evento.get("adesc", "Campi Flegrei")
#                 qualita  = loc.get("quality", "n.d.")
#                 tipo = evento.get("type", "unknown")
#                 tipo_desc = evento.get("type_desc", "")
#                 author = loc.get("author")

#                 if lat is None or lon is None:
#                     continue

#                 if mag is not None:
#                    batch_map.append({
#                     "lat": lat, "lng": lon, "mag": mag,
#                     "data": time_str, "qualita": qualita,
#                     "area": area
#                    })

#                 log_entry = {
#                    "event_id":     evento.get("id") or evento.get("event_id"),
#                     "data":         time_str,
#                     "area_desc":    area,
#                     "magnitudine":  mag,
#                     "profondita_km": dep,
#                     "latitudine":   lat,
#                     "longitudine":  lon,
#                     "qualita":      qualita,
#                     "tipo":         tipo,
#                     "tipo_desc":    tipo_desc,
#                     "communicate":  evento.get("communicate"),
#                     "author":       author,
#                 }

#                 log_generale.append(log_entry)

#                 zona_raw = evento.get("area", "").lower().strip()
#                 zona_tab = {
#                     "flegrei": "CAMPI FLEGREI",
#                     "vesuvio": "VESUVIO",
#                     "ischia":  "ISCHIA"
#                 }.get(zona_raw)

#                 if zona_tab:
#                     log_per_zona.setdefault(zona_tab, []).append(log_entry)

#             except Exception as e:
#                 print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")


#         # ── Inserisci nel model (che ora riordina l'INTERA lista per data) ──
#         if log_generale:
#             self.model.add_log_batch("GENERALE", log_generale)

#         zone_aggiornate = []

#         for zona, msgs in log_per_zona.items():
#          self.model.add_log_batch(zona, msgs)
#          zone_aggiornate.append(zona)

#         for zona in zone_aggiornate:
#          self._update_swarm_widget(zona)

            
#         if self.view:
#          self.view.tabs_view.update_zone_cards(self.model.tab_logs)

#          ultimo_evento = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)
#          if ultimo_evento:
#           mag_ultimo = ultimo_evento.get("magnitudine")
#           print(f"🔔 [SERENADE] Stato aggiornato dall'ultimo evento: {ultimo_evento.get('data')} - M{mag_ultimo} - Stato: {self.model.status.value}")


      
#         # ── Una sola chiamata JS per la mappa ─────────────────────────
#         self.map_service.add_eventi_batch(batch_map)

#      finally:
#         self._elaborando = False

#     def get_active_source(self):
#      """Ritorna 'kafka' o 'serenade' in base al worker configurato, per sapere come interpretare l'ordine dei log."""
#      from servers.serenade.serenade import SerenadeWorker
#      from servers.serverkafka.kafka import KafkaWorker

#      if isinstance(self.data_worker, KafkaWorker):
#         return "kafka"
#      elif isinstance(self.data_worker, SerenadeWorker):
#         return "serenade"
#      return None

  
        
#     def _filtra_e_aggiorna_logs(self):
#      """Riapplica il filtro attivo e aggiorna la vista. Da chiamare dopo ogni batch."""
#      if self.view is None:
#         return
#      self.on_filter_changed(self._active_filter)

   

#     def _detect_swarm_state_from_logs(self, zona):
#      detector = self.swarm_detectors.get(zona)
#      if detector is None:
#         return "NESSUNO", "#53565A", "Zona non monitorata"
#      eventi = self.model.tab_logs.get(zona, [])
#      return detector.detect(eventi)
    
#     def _update_swarm_widget(self, zona):
#      if zona not in self.swarm_detectors:
#         return

#     # Chiama SEMPRE detect(), anche se il comunicato ufficiale ha priorità sul badge:
#     # serve a tenere aggiornato previous_state, così la transizione a TERMINATO
#     # sarà corretta quando il comunicato ufficiale finirà.
#      detector_state, detector_color, detector_tooltip = self._detect_swarm_state_from_logs(zona)

#      if zona in self.official_swarms:
#         return  # il badge resta quello del comunicato ufficiale, già impostato altrove

#      self.swarm_states[zona] = (detector_state, detector_color, detector_tooltip)

#      if self.view and hasattr(self.view, "tabs_view"):
#         self.view.tabs_view.update_zone_swarm_state(zona, detector_state, detector_color, detector_tooltip)

#      self._update_global_swarm_banner()
    


#     def _update_global_swarm_banner(self):
#      if not self.view or not hasattr(self.view, "header") or not self.swarm_states:
#         return

#      peggiore_zona = min(
#         self.swarm_states,
#         key=lambda z: self._SWARM_SEVERITY.get(self.swarm_states[z][0], 99)
#      )

#      state, color, tooltip = self.swarm_states[peggiore_zona]

#      if state not in ("NESSUNO", "ATTIVITÀ ORDINARIA"):
#         tooltip = f"{peggiore_zona}: {tooltip}"
#         label = f"{state} - {peggiore_zona}"
#      else:
#         label = state

#      self.view.header.update_swarm_state(
#         label,
#         color,
#         tooltip
#      )

    


# from datetime import datetime
# from models.system_model import SystemModel, SystemStatus
# from services.swarm_detector import SwarmDetector
# from PyQt6.QtCore import QObject, QTimer
# import json
# from services.kafka_recorder import KafkaRecorder
# from utils.helpers import seleziona_ultima_scossa
# from views.dialogs import AlarmDialog


# class SystemController(QObject):
#     """CONTROLLER: Gestisce tutta la logica applicativa, rappresenta il controller di tutta l'architettura"""

#     _SWARM_SEVERITY = {
#         "SCIAME IN CORSO": 1,
#         "SCIAME INIZIATO": 2,
#         "SCIAME TERMINATO": 3,
#         "ATTIVITÀ ORDINARIA": 4,
#         "NESSUNO": 5,
#     }

#     # ── Tempi ─────────────────────────────────────────────────
#     QUIETE_DOPO_SECONDI   = 15 * 60   # silenzio necessario per tornare in QUIETE
#     ALLARME_CARD_DURATA_S = 15 * 60   # per quanto la card resta rossa dopo una scossa forte
#     TICK_QUIETE_MS        = 30_000    # ogni quanto controllo le due soglie qui sopra
#     DURATA_ALLARME_MS     = 8_000     # per quanto resta a schermo il popup

#     def __init__(self, model, audio_service, map_service, view=None, data_worker=None, data_thread=None, kafka_date_from=None):
#         super().__init__()
#         # il costruttore riceve 4 componenti
#         self.model = model                  # modello dei dati
#         self.audio_service = audio_service  # gestione audio
#         self.map_service = map_service      # gestione mappa
#         self.view = view                    # interfaccia utente
#         self.data_worker = data_worker
#         self.data_thread = data_thread
#         self.kafka_date_from = kafka_date_from
#         self._elaborando = False
#         self._active_filter = "all"
#         self._alarmed_event_ids = set()
#         self._use_arrival_order_for_status = True   # TEST replay
#         self._latest_status_event_time = None       # modalità reale

#         self._alarm_dialog = None   # SERVE: senza, il popup viene distrutto appena esco da _trigger_alarm
#         self._zone_alarms = {}      # zona -> (magnitudine, istante di ARRIVO della scossa forte)

#         self.swarm_detectors = {
#             "CAMPI FLEGREI": SwarmDetector(),
#             "VESUVIO": SwarmDetector(),
#             "ISCHIA": SwarmDetector(),
#         }
#         self.swarm_states = {}        # zona -> (state, color, tooltip) da SwarmDetector
#         self.official_swarms = {}     # zona -> ultimo comunicato ufficiale ricevuto da Kafka
#         self.kafka_recorder = KafkaRecorder()

#         # Timer che riporta in QUIETE e spegne le card rosse.
#         # Il tick è solo la frequenza del controllo, le soglie sono le costanti sopra.
#         self.quiete_timer = QTimer(self)
#         self.quiete_timer.timeout.connect(self.controlla_quiete)
#         self.quiete_timer.start(self.TICK_QUIETE_MS)

#         if self.data_worker is not None:
#             from servers.serenade.serenade import SerenadeWorker
#             from servers.serverkafka.kafka import KafkaWorker

#             if isinstance(self.data_worker, KafkaWorker):
#                 self.data_worker.message_received.connect(self.on_kafka_message)
#                 self.data_worker.swarm_message_received.connect(self.on_kafka_swarm_message)

#             elif isinstance(self.data_worker, SerenadeWorker):
#                 self.data_worker.message_received.connect(self.on_serenade_message)

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA TEMPO
#     # ─────────────────────────────────────────────────────────
#     def get_time_since_last_event(self):
#         if self.model.last_event_time is None:
#             return None
#         # se non c'è stato alcun evento restituisce none

#         diff = datetime.now() - self.model.last_event_time
#         seconds = int(diff.total_seconds())
#         # calcola la differenza tra ora attuale e ultimo evento

#         if seconds < 60:
#             return f"{seconds} secondi fa"
#         elif seconds < 3600:
#             return f"{seconds // 60} minuti e {seconds % 60} secondi fa"
#         else:
#             return f"{seconds // 3600} ore e {(seconds % 3600) // 60} minuti fa"

#     def get_current_date(self):
#         return datetime.now().strftime("%d/%m/%Y")

#     def get_current_date_utc(self):
#         """Restituisce la data UTC corrente"""
#         return datetime.utcnow().strftime("%d/%m/%Y")

#     def get_current_time(self):
#         return datetime.now().strftime("%H:%M:%S")

#     def get_utc_time(self):
#         """Restituisce l'ora UTC corrente"""
#         return datetime.utcnow().strftime("%H:%M:%S")

#     # ─────────────────────────────────────────────────────────
#     #  QUIETE E ALLERTA CARD
#     # ─────────────────────────────────────────────────────────
#     def controlla_quiete(self):
#         """Chiamato dal timer: spegne le card scadute e riporta il sistema in QUIETE.
#         Misura sempre sull'orologio di ARRIVO (last_event_time), mai sulla data
#         dell'evento: altrimenti col replay di dati vecchi saresti in quiete da subito."""
#         self._scadi_allarmi_card()

#         t = self.model.last_event_time
#         if t is None:
#             return
#         if (datetime.now() - t).total_seconds() >= self.QUIETE_DOPO_SECONDI:
#             self.model.reset_a_quiete()
#             self._spegni_tutti_allarmi_card()

#     def _accendi_allarme_card(self, zona, mag):
#         """Rende rossa la card della zona che ha avuto la scossa forte.
#         È la traccia persistente che resta dopo che il popup è sparito."""
#         if zona not in self.swarm_detectors:   # solo le 3 zone che hanno una card
#             return
#         try:
#             mag = float(mag)
#         except (TypeError, ValueError):
#             return

#         self._zone_alarms[zona] = (mag, datetime.now())
#         if self.view and hasattr(self.view, "tabs_view"):
#             self.view.tabs_view.update_zone_alarm(zona, mag)

#     def _spegni_allarme_card(self, zona):
#         self._zone_alarms.pop(zona, None)
#         if self.view and hasattr(self.view, "tabs_view"):
#             self.view.tabs_view.update_zone_alarm(zona, None)

#     def _spegni_tutti_allarmi_card(self):
#         for zona in list(self._zone_alarms):
#             self._spegni_allarme_card(zona)

#     def _scadi_allarmi_card(self):
#         ora = datetime.now()
#         scaduti = [
#             zona for zona, (_, t) in self._zone_alarms.items()
#             if (ora - t).total_seconds() >= self.ALLARME_CARD_DURATA_S
#         ]
#         for zona in scaduti:
#             self._spegni_allarme_card(zona)

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA MAPPA
#     # ─────────────────────────────────────────────────────────

#     def on_map_loaded(self, ok):
#         print("Mappa caricata" if ok else "Errore mappa")
#         if ok:
#             self.map_service.set_ready(True)
#             self.map_service.apply_config()
#             if self.view and self.view.map_widget and self.view.map_widget.webview:
#                 self.view.map_widget.webview.page().runJavaScript(
#                     f'if (window.setTimeFilter) {{ window.setTimeFilter("{self._active_filter}"); }}'
#                 )
#             if self.data_thread is not None and not self.data_thread.isRunning():
#                 self.data_thread.start()

#     def on_tab_changed(self, tab_name):  # gestisce lo zoom delle zone sismiche
#         if not self.map_service.map_ready:
#             return
#         zone_map = {"CAMPI FLEGREI": "CAMPI FLEGREI", "VESUVIO": "VESUVIO", "ISCHIA": "ISCHIA"}
#         if tab_name in zone_map:
#             self.map_service.zoom_to_vulcano(zone_map[tab_name])
#         else:
#             self.map_service.zoom_to_all()

#     def refresh_map(self):
#         self.map_service.refresh_view()  # aggiorna la visualizzazione della mappa

#     def process_pending_updates(self):
#         self.map_service.process_pending()  # processa gli aggiornamenti in sospeso della mappa

#     def on_filter_changed(self, key):
#         """Cambia il filtro temporale attivo: aggiorna mappa e tabelle."""
#         self._active_filter = key

#         if (self.map_service.map_ready
#                 and self.view and self.view.map_widget and self.view.map_widget.webview):
#             self.view.map_widget.webview.page().runJavaScript(
#                 f'if (window.setTimeFilter) {{ window.setTimeFilter("{key}"); }}'
#             )

#         self.render_logs_filtrati()

#     def _riferimento_temporale(self):
#         """Istante da cui misurare i filtri: l'ultima scossa presente nei dati,
#         così i filtri funzionano anche rigiocando registrazioni vecchie.
#         Se non ci sono eventi, usa l'ora reale."""
#         date = []
#         for e in self.model.tab_logs.get("GENERALE", []):
#             if isinstance(e, dict) and e.get("data"):
#                 try:
#                     date.append(datetime.strptime(
#                         str(e["data"]).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S"))
#                 except Exception:
#                     pass
#         return max(date) if date else datetime.utcnow()

#     def _logs_filtrati(self, logs):
#         """Applica il filtro temporale attivo a una lista di log."""
#         from datetime import timedelta

#         def ordina(ls):
#             return sorted(ls, key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
#                           reverse=True)

#         key = self._active_filter
#         if key == "all":
#             return ordina(logs)

#         delta = {
#             "24h": timedelta(hours=24),
#             "48h": timedelta(hours=48),
#             "7gg": timedelta(days=7),
#             "14gg": timedelta(days=14),
#             "1mese": timedelta(days=30),
#         }.get(key)
#         if delta is None:
#             return ordina(logs)

#         cutoff = self._riferimento_temporale() - delta
#         risultato = []
#         for entry in logs:
#             if not isinstance(entry, dict):
#                 continue
#             try:
#                 data_str = str(entry.get("data", "")).replace("T", " ")[:19]
#                 if datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S") >= cutoff:
#                     risultato.append(entry)
#             except Exception:
#                 pass
#         return ordina(risultato)

#     def render_logs_filtrati(self):
#         """Ridisegna le tabelle applicando il filtro attivo (senza toccare la mappa)."""
#         if self.view is None:
#             return
#         for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
#             logs = self.model.tab_logs.get(zona, [])
#             self.view.tabs_view.update_logs(zona, self._logs_filtrati(logs))

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA KAFKA
#     # ─────────────────────────────────────────────────────────

#     def on_kafka_message(self, msg):
#         print("🔵 [KAFKA] Messaggio ricevuto")

#         # Registra il messaggio Kafka
#         self.kafka_recorder.save(msg.value)

#         if isinstance(msg.value, list):
#             nomi_blocchi = [item.get("name") for item in msg.value if isinstance(item, dict)]
#             print(f"[KAFKA] Blocchi presenti (lista): {nomi_blocchi}")

#         elif isinstance(msg.value, dict):
#             print(f"[KAFKA] Messaggio DICT. Chiavi: {list(msg.value.keys())}")
#             print(json.dumps(msg.value, indent=2, default=str))

#         else:
#             print(f"[KAFKA] Tipo inatteso: {type(msg.value)}")

#         filtrato = SystemModel.filtra_messaggio_kafka(msg.value)

#         if filtrato is None:
#             print("⚠️ [KAFKA] Messaggio filtrato -> None")
#             return

#         print("TIPO EVENTO:", filtrato.get("tipo"))
#         print("DESCRIZIONE TIPO:", filtrato.get("tipo_desc"))

#         # ── print di debug ──────────────────────────
#         print(
#             f"\n{'─'*50}"
#             f"\n[KAFKA] {filtrato['data']}"
#             f"\n  Tipo     : {filtrato['tipo_desc']}"
#             f"\n  Area     : {filtrato['area_desc']}"
#             f"\n  Lat/Lon  : {filtrato['latitudine']}, {filtrato['longitudine']}"
#             f"\n  Profond. : {filtrato['profondita_km']} km"
#             f"\n  Magn.    : {filtrato['magnitudine']} ({filtrato['mag_tipo']})"
#             f"\n  Qualità  : {filtrato['qualita']}  RMS: {filtrato['rms']}  GAP: {filtrato['gap_azimutale']}°"
#             f"\n{'─'*50}"
#         )

#         # ── AGGIUNGI IL PUNTINO SULLA MAPPA (come fa Serenade) ──
#         lat = filtrato.get('latitudine')
#         lon = filtrato.get('longitudine')
#         mag = filtrato.get('magnitudine')
#         time_str = filtrato.get('data', '')
#         qualita = filtrato.get('qualita', 'n.d.')

#         if lat is not None and lon is not None and mag is not None:
#             batch_event = [{
#                 "lat": lat,
#                 "lng": lon,
#                 "mag": mag,
#                 "data": time_str,
#                 "qualita": qualita,
#                 "area": filtrato.get('area_desc', 'n.d')
#             }]
#             self.map_service.add_eventi_batch(batch_event)

#         # ── log_entry come dict ──────────────────────
#         log_entry = {
#             "event_id":      filtrato.get("event_id"),
#             "data":          filtrato["data"],
#             "area":          filtrato.get("area"),
#             "area_desc":     filtrato["area_desc"],
#             "magnitudine":   filtrato["magnitudine"],
#             "profondita_km": filtrato["profondita_km"],
#             "latitudine":    filtrato["latitudine"],
#             "longitudine":   filtrato["longitudine"],
#             "qualita":       filtrato["qualita"],
#             "tipo":          filtrato["tipo"],
#             "tipo_desc":     filtrato["tipo_desc"],
#             "communicate":   filtrato.get("communicate"),
#             "author":        filtrato.get("author"),
#         }

#         zona = self._normalizza_zona_kafka(filtrato["area"])
#         self.model.add_log(zona, log_entry)
#         if zona != "GENERALE":
#             self.model.add_log("GENERALE", log_entry)   # evita il doppio inserimento su GENERALE

#         self._update_swarm_widget(zona)
#         if self.view:
#             self.view.tabs_view.update_zone_cards(self.model.tab_logs, source="kafka")
#             self._filtra_e_aggiorna_logs()

#         # ── AGGIORNAMENTO STATO SISTEMA ────────────────────────────────
#         evento_stato = None

#         if self._use_arrival_order_for_status:
#             # TEST REPLAY: usa esattamente il messaggio appena entrato da Kafka.
#             evento_stato = self.model.aggiorna_stato_da_evento_ricevuto(log_entry)

#             if evento_stato is not None:
#                 print(
#                     f"🧪 [STATO - ORDINE ARRIVO] "
#                     f"data={evento_stato.get('data')} | "
#                     f"M={evento_stato.get('magnitudine')} | "
#                     f"author={evento_stato.get('author')} | "
#                     f"stato={self.model.status.value}"
#                 )
#             else:
#                 print(
#                     f"⏭️ [STATO - ORDINE ARRIVO] Evento ignorato: "
#                     f"data={log_entry.get('data')} | "
#                     f"M={log_entry.get('magnitudine')} | "
#                     f"author={log_entry.get('author')}"
#                 )

#         else:
#             # MODALITÀ REALE: cerca l'evento cronologicamente più recente nei log.
#             evento_stato = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)

#             if evento_stato is not None:
#                 print(
#                     f"🕒 [STATO - ORDINE CRONOLOGICO] "
#                     f"data={evento_stato.get('data')} | "
#                     f"M={evento_stato.get('magnitudine')} | "
#                     f"stato={self.model.status.value}"
#                 )

#         # Aggiorna la mappa soltanto se è stato selezionato un evento valido
#         if evento_stato is not None:
#             self.model.last_event_time = datetime.now()
#             zona_stato = self._normalizza_zona_kafka(evento_stato.get("area"))

#             self.map_service.update_vulcano(
#                 zona_stato,
#                 self.model.status.value,
#                 evento_stato.get("magnitudine")
#             )

#         # ── ALLARME IN FONDO ───────────────────────────────────────────
#         # Deve stare qui, dopo che mappa/log/stato sono già aggiornati:
#         # prima si elabora, poi si notifica.
#         from services.alarm_service import should_alarm
#         event_id = filtrato.get("event_id")
#         if (event_id
#                 and event_id not in self._alarmed_event_ids
#                 and not self.model.is_manuale(filtrato)
#                 and should_alarm(filtrato)):
#             self._alarmed_event_ids.add(event_id)
#             self._trigger_alarm(filtrato)

#     def _normalizza_zona_kafka(self, area: str | None) -> str:
#         AREA_MAP = {
#             'vesuvio':  'VESUVIO',
#             'flegrei':  'CAMPI FLEGREI',
#             'ischia':   'ISCHIA',
#         }
#         if not area:
#             return 'GENERALE'
#         return AREA_MAP.get(area.lower().strip(), 'GENERALE')

#     def _trigger_alarm(self, filtrato: dict):
#         self.audio_service.play()
#         zona = self._normalizza_zona_kafka(filtrato.get("area"))
#         print(f"🚨 [ALLARME] Evento automatico M{filtrato['magnitudine']} — "
#               f"{filtrato['area_desc']} — {filtrato['data']}")

#         # La card rossa resta anche dopo che il popup è sparito
#         self._accendi_allarme_card(zona, filtrato.get("magnitudine"))

#         if not self.view:
#             return

#         # se ce n'è già uno a schermo lo chiudo: vince l'allarme più recente
#         if self._alarm_dialog is not None:
#             self._alarm_dialog.close()

#         dialog = AlarmDialog(
#             parent=self.view,
#             ui_scale=self.view.ui_scale,
#             magnitudo=filtrato.get("magnitudine"),
#             zona=filtrato.get("area_desc", "n.d.")
#         )
#         dialog.setModal(False)          # non bloccante: la mappa continua ad aggiornarsi
#         self._alarm_dialog = dialog     # tiene vivo il riferimento, altrimenti Python lo distrugge
#         dialog.show()
#         dialog.raise_()
#         QTimer.singleShot(self.DURATA_ALLARME_MS, dialog.close)

#     def on_kafka_swarm_message(self, msg):
#         self.kafka_recorder.save(msg.value, topic=getattr(msg, "topic", None))
#         dati = msg.value
#         if not isinstance(dati, dict):
#             print(f"⚠️ [KAFKA SWARM] Formato inatteso: {type(dati)}")
#             return

#         zona = self._normalizza_zona_kafka(dati.get("area"))
#         tipo_comunicato = dati.get("type")
#         sciame_finito = tipo_comunicato == "end" or bool((dati.get("end_time") or "").strip())

#         print(f"📢 [KAFKA SWARM] {zona} - tipo: {tipo_comunicato} - "
#               f"Ev#{dati.get('event_number')} - Md{dati.get('max_md')}")

#         if sciame_finito:
#             tooltip = f"Sciame concluso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"
#             self.official_swarms.pop(zona, None)

#             # Mostra esplicitamente lo stato di chiusura ufficiale
#             self.swarm_states[zona] = ("SCIAME TERMINATO", "#2e7d32", tooltip)
#             if self.view and hasattr(self.view, "tabs_view"):
#                 self.view.tabs_view.update_zone_swarm_state(zona, "SCIAME TERMINATO", "#2e7d32", tooltip)

#             # Allinea anche il detector euristico, così non riproponga subito INIZIATO/IN CORSO
#             if zona in self.swarm_detectors:
#                 self.swarm_detectors[zona].previous_state = "SCIAME TERMINATO"

#             self._update_global_swarm_banner()
#             return

#         self.official_swarms[zona] = dati

#         if tipo_comunicato == "news":
#             etichetta = "SCIAME INIZIATO"
#             colore = "#EF6C00"
#             tooltip = f"Nuovo sciame rilevato — Md {dati.get('max_md', '?')}"
#         else:
#             etichetta = "SCIAME IN CORSO"
#             colore = "#c62828"
#             tooltip = f"Sciame in corso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"

#         self.swarm_states[zona] = (etichetta, colore, tooltip)

#         if self.view and hasattr(self.view, "tabs_view"):
#             self.view.tabs_view.update_zone_swarm_state(zona, etichetta, colore, tooltip)

#         self._update_global_swarm_banner()

#     # ─────────────────────────────────────────────────────────
#     #  LOGICA SERENADE
#     # ─────────────────────────────────────────────────────────

#     def on_serenade_message(self, eventi):
#         if self._elaborando:
#             return
#         self._elaborando = True

#         try:
#             if isinstance(eventi, dict):
#                 records = list(eventi.values())
#             else:
#                 records = list(eventi)

#             # ── DEBUG: quali "type" distinti arrivano da Serenade? ──
#             tipi_trovati = set()
#             for evento in records:
#                 if isinstance(evento, dict):
#                     tipi_trovati.add(evento.get("type", "MANCANTE"))
#             print(f"[SERENADE] Tipi di evento trovati in questo batch: {tipi_trovati}")
#             print(f"[SERENADE] Numero totale eventi nel batch: {len(records)}")

#             self.map_service.clear_eventi()

#             batch_map = []
#             log_generale = []
#             log_per_zona = {}

#             for evento in records:
#                 try:
#                     loc      = evento.get("location", {})
#                     mags     = loc.get("magnitudos", [])
#                     mag      = mags[0]["value"] if mags else None
#                     lat      = loc.get("latitude")
#                     lon      = loc.get("longitude")
#                     dep      = loc.get("depth")
#                     time_str = evento.get("date", "")[:19]
#                     area     = evento.get("adesc", "Campi Flegrei")
#                     qualita  = loc.get("quality", "n.d.")
#                     tipo = evento.get("type", "unknown")
#                     tipo_desc = evento.get("type_desc", "")
#                     author = loc.get("author")

#                     if lat is None or lon is None:
#                         continue

#                     if mag is not None:
#                         batch_map.append({
#                             "lat": lat, "lng": lon, "mag": mag,
#                             "data": time_str, "qualita": qualita,
#                             "area": area
#                         })

#                     log_entry = {
#                         "event_id":      evento.get("id") or evento.get("event_id"),
#                         "data":          time_str,
#                         "area":          evento.get("area"),
#                         "area_desc":     area,
#                         "magnitudine":   mag,
#                         "profondita_km": dep,
#                         "latitudine":    lat,
#                         "longitudine":   lon,
#                         "qualita":       qualita,
#                         "tipo":          tipo,
#                         "tipo_desc":     tipo_desc,
#                         "communicate":   evento.get("communicate"),
#                         "author":        author,
#                     }

#                     log_generale.append(log_entry)

#                     zona_raw = evento.get("area", "").lower().strip()
#                     zona_tab = {
#                         "flegrei": "CAMPI FLEGREI",
#                         "vesuvio": "VESUVIO",
#                         "ischia":  "ISCHIA"
#                     }.get(zona_raw)

#                     if zona_tab:
#                         log_per_zona.setdefault(zona_tab, []).append(log_entry)

#                 except Exception as e:
#                     print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")

#             # ── Inserisci nel model (che ora riordina l'INTERA lista per data) ──
#             if log_generale:
#                 self.model.add_log_batch("GENERALE", log_generale)

#             zone_aggiornate = []

#             for zona, msgs in log_per_zona.items():
#                 self.model.add_log_batch(zona, msgs)
#                 zone_aggiornate.append(zona)

#             for zona in zone_aggiornate:
#                 self._update_swarm_widget(zona)

#             if self.view:
#                 self.view.tabs_view.update_zone_cards(self.model.tab_logs)

#                 ultimo_evento = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)
#                 if ultimo_evento:
#                     self.model.last_event_time = datetime.now()
#                     mag_ultimo = ultimo_evento.get("magnitudine")
#                     print(f"🔔 [SERENADE] Stato aggiornato dall'ultimo evento: "
#                           f"{ultimo_evento.get('data')} - M{mag_ultimo} - Stato: {self.model.status.value}")

#             # ── Una sola chiamata JS per la mappa ─────────────────────────
#             self.map_service.add_eventi_batch(batch_map)

#         finally:
#             self._elaborando = False

#     def get_active_source(self):
#         """Ritorna 'kafka' o 'serenade' in base al worker configurato, per sapere come interpretare l'ordine dei log."""
#         from servers.serenade.serenade import SerenadeWorker
#         from servers.serverkafka.kafka import KafkaWorker

#         if isinstance(self.data_worker, KafkaWorker):
#             return "kafka"
#         elif isinstance(self.data_worker, SerenadeWorker):
#             return "serenade"
#         return None

#     def _filtra_e_aggiorna_logs(self):
#         """Riapplica il filtro attivo e aggiorna la vista. Da chiamare dopo ogni batch."""
#         if self.view is None:
#             return
#         self.on_filter_changed(self._active_filter)

#     # ─────────────────────────────────────────────────────────
#     #  SCIAMI
#     # ─────────────────────────────────────────────────────────

#     def _detect_swarm_state_from_logs(self, zona):
#         detector = self.swarm_detectors.get(zona)
#         if detector is None:
#             return "NESSUNO", "#53565A", "Zona non monitorata"
#         eventi = self.model.tab_logs.get(zona, [])
#         return detector.detect(eventi)

#     def _update_swarm_widget(self, zona):
#         if zona not in self.swarm_detectors:
#             return

#         # Chiama SEMPRE detect(), anche se il comunicato ufficiale ha priorità sul badge:
#         # serve a tenere aggiornato previous_state, così la transizione a TERMINATO
#         # sarà corretta quando il comunicato ufficiale finirà.
#         detector_state, detector_color, detector_tooltip = self._detect_swarm_state_from_logs(zona)

#         if zona in self.official_swarms:
#             return  # il badge resta quello del comunicato ufficiale, già impostato altrove

#         self.swarm_states[zona] = (detector_state, detector_color, detector_tooltip)

#         if self.view and hasattr(self.view, "tabs_view"):
#             self.view.tabs_view.update_zone_swarm_state(zona, detector_state, detector_color, detector_tooltip)

#         self._update_global_swarm_banner()

#     def _update_global_swarm_banner(self):
#         if not self.view or not hasattr(self.view, "header") or not self.swarm_states:
#             return

#         peggiore_zona = min(
#             self.swarm_states,
#             key=lambda z: self._SWARM_SEVERITY.get(self.swarm_states[z][0], 99)
#         )

#         state, color, tooltip = self.swarm_states[peggiore_zona]

#         if state not in ("NESSUNO", "ATTIVITÀ ORDINARIA"):
#             tooltip = f"{peggiore_zona}: {tooltip}"
#             label = f"{state} - {peggiore_zona}"
#         else:
#             label = state

#         self.view.header.update_swarm_state(label, color, tooltip)


from datetime import datetime
from models.system_model import SystemModel, SystemStatus
from services.swarm_detector import SwarmDetector
from PyQt6.QtCore import QObject, QTimer
import json
from services.kafka_recorder import KafkaRecorder
from utils.helpers import seleziona_ultima_scossa,parse_event_datetime
from views.dialogs import AlarmDialog


class SystemController(QObject):
    """CONTROLLER: Gestisce tutta la logica applicativa, rappresenta il controller di tutta l'architettura"""

    _SWARM_SEVERITY = {
        "SCIAME IN CORSO": 1,
        "SCIAME INIZIATO": 2,
        "SCIAME TERMINATO": 3,
        "ATTIVITÀ ORDINARIA": 4,
        "NESSUNO": 5,
    }

    # ── Tempi ─────────────────────────────────────────────────
    QUIETE_DOPO_SECONDI   = 15 * 60   # silenzio necessario per tornare in QUIETE
    ALLARME_CARD_DURATA_S = 1 * 60   # per quanto la card resta rossa dopo una scossa forte
    TICK_QUIETE_MS        = 30_000    # ogni quanto controllo le due soglie qui sopra
    DURATA_ALLARME_MS     = 30_000     # per quanto resta a schermo il popup
    TOLLERANZA_MAPPA_SECONDI = 2   # stessa tolleranza di seleziona_ultima_scossa

    def __init__(self, model, audio_service, map_service, view=None, data_worker=None, data_thread=None, kafka_date_from=None):
        super().__init__()
        # il costruttore riceve 4 componenti
        self.model = model                  # modello dei dati
        self.audio_service = audio_service  # gestione audio
        self.map_service = map_service      # gestione mappa
        self.view = view                    # interfaccia utente
        self.data_worker = data_worker
        self.data_thread = data_thread
        self.kafka_date_from = kafka_date_from
        self._elaborando = False
        self._active_filter = "all"
        self._alarmed_event_ids = set()
        self._use_arrival_order_for_status = True   # TEST replay
        self._latest_status_event_time = None       # modalità reale

        self._alarm_dialog = None   # SERVE: senza, il popup viene distrutto appena esco da _trigger_alarm
        self._zone_alarms = {}      # zona -> (magnitudine, istante di ARRIVO della scossa forte)
        self._eventi_mappa = {}   # chiave evento -> ultimo dict {lat,lng,mag,data,qualita,area} arrivato

        self.swarm_detectors = {
            "CAMPI FLEGREI": SwarmDetector(),
            "VESUVIO": SwarmDetector(),
            "ISCHIA": SwarmDetector(),
        }
        self.swarm_states = {}        # zona -> (state, color, tooltip) da SwarmDetector
        self.official_swarms = {}     # zona -> ultimo comunicato ufficiale ricevuto da Kafka
        self.kafka_recorder = KafkaRecorder()

        # Timer che riporta in QUIETE e spegne le card rosse.
        # Il tick è solo la frequenza del controllo, le soglie sono le costanti sopra.
        self.quiete_timer = QTimer(self)
        self.quiete_timer.timeout.connect(self.controlla_quiete)
        self.quiete_timer.start(self.TICK_QUIETE_MS)

        if self.data_worker is not None:
            from servers.serenade.serenade import SerenadeWorker
            from servers.serverkafka.kafka import KafkaWorker

            if isinstance(self.data_worker, KafkaWorker):
                self.data_worker.message_received.connect(self.on_kafka_message)
                self.data_worker.swarm_message_received.connect(self.on_kafka_swarm_message)

            elif isinstance(self.data_worker, SerenadeWorker):
                self.data_worker.message_received.connect(self.on_serenade_message)

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
    #  QUIETE E ALLERTA CARD
    # ─────────────────────────────────────────────────────────
    def controlla_quiete(self):
        """Chiamato dal timer: spegne le card scadute e riporta il sistema in QUIETE.
        Misura sempre sull'orologio di ARRIVO (last_event_time), mai sulla data
        dell'evento: altrimenti col replay di dati vecchi saresti in quiete da subito."""
        self._scadi_allarmi_card()

        t = self.model.last_event_time
        if t is None:
            return
        if (datetime.now() - t).total_seconds() >= self.QUIETE_DOPO_SECONDI:
            self.model.reset_a_quiete()
            self._spegni_tutti_allarmi_card()

    def _accendi_allarme_card(self, zona, mag):
        """Rende rossa la card della zona che ha avuto la scossa forte.
        È la traccia persistente che resta dopo che il popup è sparito."""
        if zona not in self.swarm_detectors:   # solo le 3 zone che hanno una card
            return
        try:
            mag = float(mag)
        except (TypeError, ValueError):
            return

        self._zone_alarms[zona] = (mag, datetime.now())
        if self.view and hasattr(self.view, "tabs_view"):
            self.view.tabs_view.update_zone_alarm(zona, mag)

    def _spegni_allarme_card(self, zona):
        self._zone_alarms.pop(zona, None)
        if self.view and hasattr(self.view, "tabs_view"):
            self.view.tabs_view.update_zone_alarm(zona, None)

    def _spegni_tutti_allarmi_card(self):
        for zona in list(self._zone_alarms):
            self._spegni_allarme_card(zona)

    def _scadi_allarmi_card(self):
        ora = datetime.now()
        scaduti = [
            zona for zona, (_, t) in self._zone_alarms.items()
            if (ora - t).total_seconds() >= self.ALLARME_CARD_DURATA_S
        ]
        for zona in scaduti:
            self._spegni_allarme_card(zona)

    # ─────────────────────────────────────────────────────────
    #  LOGICA MAPPA
    # ─────────────────────────────────────────────────────────

    def on_map_loaded(self, ok):
        print("Mappa caricata" if ok else "Errore mappa")
        if ok:
            self.map_service.set_ready(True)
            self.map_service.apply_config()
            if self.view and self.view.map_widget and self.view.map_widget.webview:
                self.view.map_widget.webview.page().runJavaScript(
                    f'if (window.setTimeFilter) {{ window.setTimeFilter("{self._active_filter}"); }}'
                )
            if self.data_thread is not None and not self.data_thread.isRunning():
                self.data_thread.start()

    def on_tab_changed(self, tab_name):  # gestisce lo zoom delle zone sismiche
        if not self.map_service.map_ready:
            return
        zone_map = {"CAMPI FLEGREI": "CAMPI FLEGREI", "VESUVIO": "VESUVIO", "ISCHIA": "ISCHIA"}
        if tab_name in zone_map:
            self.map_service.zoom_to_vulcano(zone_map[tab_name])
        else:
            self.map_service.zoom_to_all()

    def refresh_map(self):
        self.map_service.refresh_view()  # aggiorna la visualizzazione della mappa

    def process_pending_updates(self):
        self.map_service.process_pending()  # processa gli aggiornamenti in sospeso della mappa

    def on_filter_changed(self, key):
        """Cambia il filtro temporale attivo: aggiorna mappa e tabelle."""
        self._active_filter = key

        if (self.map_service.map_ready
                and self.view and self.view.map_widget and self.view.map_widget.webview):
            self.view.map_widget.webview.page().runJavaScript(
                f'if (window.setTimeFilter) {{ window.setTimeFilter("{key}"); }}'
            )

        self.render_logs_filtrati()

    def _riferimento_temporale(self):
        """Istante da cui misurare i filtri: l'ultima scossa presente nei dati,
        così i filtri funzionano anche rigiocando registrazioni vecchie.
        Se non ci sono eventi, usa l'ora reale."""
        date = []
        for e in self.model.tab_logs.get("GENERALE", []):
            if isinstance(e, dict) and e.get("data"):
                try:
                    date.append(datetime.strptime(
                        str(e["data"]).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S"))
                except Exception:
                    pass
        return max(date) if date else datetime.utcnow()

    def _logs_filtrati(self, logs):
        """Applica il filtro temporale attivo a una lista di log."""
        from datetime import timedelta

        def ordina(ls):
            return sorted(ls, key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
                          reverse=True)

        key = self._active_filter
        if key == "all":
            return ordina(logs)

        delta = {
            "24h": timedelta(hours=24),
            "48h": timedelta(hours=48),
            "7gg": timedelta(days=7),
            "14gg": timedelta(days=14),
            "1mese": timedelta(days=30),
        }.get(key)
        if delta is None:
            return ordina(logs)

        cutoff = self._riferimento_temporale() - delta
        risultato = []
        for entry in logs:
            if not isinstance(entry, dict):
                continue
            try:
                data_str = str(entry.get("data", "")).replace("T", " ")[:19]
                if datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S") >= cutoff:
                    risultato.append(entry)
            except Exception:
                pass
        return ordina(risultato)

    def render_logs_filtrati(self):
        """Ridisegna le tabelle applicando il filtro attivo (senza toccare la mappa)."""
        if self.view is None:
            return
        for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
            logs = self.model.tab_logs.get(zona, [])
            self.view.tabs_view.update_logs(zona, self._logs_filtrati(logs))

    # ─────────────────────────────────────────────────────────
    #  LOGICA KAFKA
    # ─────────────────────────────────────────────────────────

    def on_kafka_message(self, msg):
        print("🔵 [KAFKA] Messaggio ricevuto")

        # Registra il messaggio Kafka
        self.kafka_recorder.save(msg.value)

        if isinstance(msg.value, list):
            nomi_blocchi = [item.get("name") for item in msg.value if isinstance(item, dict)]
            print(f"[KAFKA] Blocchi presenti (lista): {nomi_blocchi}")

        elif isinstance(msg.value, dict):
            print(f"[KAFKA] Messaggio DICT. Chiavi: {list(msg.value.keys())}")
            print(json.dumps(msg.value, indent=2, default=str))

        else:
            print(f"[KAFKA] Tipo inatteso: {type(msg.value)}")

        filtrato = SystemModel.filtra_messaggio_kafka(msg.value)

        if filtrato is None:
            print("⚠️ [KAFKA] Messaggio filtrato -> None")
            return

        print("TIPO EVENTO:", filtrato.get("tipo"))
        print("DESCRIZIONE TIPO:", filtrato.get("tipo_desc"))

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

        self._aggiorna_evento_mappa(
            lat, lon, mag, time_str, qualita,
            filtrato.get('area_desc', 'n.d'),
            filtrato
        )

        # if lat is not None and lon is not None and mag is not None:
        #     batch_event = [{
        #         "lat": lat,
        #         "lng": lon,
        #         "mag": mag,
        #         "data": time_str,
        #         "qualita": qualita,
        #         "area": filtrato.get('area_desc', 'n.d')
        #     }]
        #     self.map_service.add_eventi_batch(batch_event)

        # ── log_entry come dict ──────────────────────
        log_entry = {
            "event_id":      filtrato.get("event_id"),
            "data":          filtrato["data"],
            "area":          filtrato.get("area"),
            "area_desc":     filtrato["area_desc"],
            "magnitudine":   filtrato["magnitudine"],
            "profondita_km": filtrato["profondita_km"],
            "latitudine":    filtrato["latitudine"],
            "longitudine":   filtrato["longitudine"],
            "qualita":       filtrato["qualita"],
            "tipo":          filtrato["tipo"],
            "tipo_desc":     filtrato["tipo_desc"],
            "communicate":   filtrato.get("communicate"),
            "author":        filtrato.get("author"),
        }

        zona = self._normalizza_zona_kafka(filtrato["area"])
        self.model.add_log(zona, log_entry)
        if zona != "GENERALE":
            self.model.add_log("GENERALE", log_entry)   # evita il doppio inserimento su GENERALE

        self._update_swarm_widget(zona)
        if self.view:
            self.view.tabs_view.update_zone_cards(self.model.tab_logs, source="kafka")
            self._filtra_e_aggiorna_logs()

        # ── AGGIORNAMENTO STATO SISTEMA ────────────────────────────────
        evento_stato = None

        if self._use_arrival_order_for_status:
            # TEST REPLAY: usa esattamente il messaggio appena entrato da Kafka.
            evento_stato = self.model.aggiorna_stato_da_evento_ricevuto(log_entry)

            if evento_stato is not None:
                print(
                    f"🧪 [STATO - ORDINE ARRIVO] "
                    f"data={evento_stato.get('data')} | "
                    f"M={evento_stato.get('magnitudine')} | "
                    f"author={evento_stato.get('author')} | "
                    f"stato={self.model.status.value}"
                )
            else:
                print(
                    f"⏭️ [STATO - ORDINE ARRIVO] Evento ignorato: "
                    f"data={log_entry.get('data')} | "
                    f"M={log_entry.get('magnitudine')} | "
                    f"author={log_entry.get('author')}"
                )

        else:
            # MODALITÀ REALE: cerca l'evento cronologicamente più recente nei log.
            evento_stato = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)

            if evento_stato is not None:
                print(
                    f"🕒 [STATO - ORDINE CRONOLOGICO] "
                    f"data={evento_stato.get('data')} | "
                    f"M={evento_stato.get('magnitudine')} | "
                    f"stato={self.model.status.value}"
                )

        # Aggiorna la mappa soltanto se è stato selezionato un evento valido
        if evento_stato is not None:
            self.model.last_event_time = datetime.now()
            zona_stato = self._normalizza_zona_kafka(evento_stato.get("area"))

            self.map_service.update_vulcano(
                zona_stato,
                self.model.status.value,
                evento_stato.get("magnitudine")
            )

        # ── ALLARME IN FONDO ───────────────────────────────────────────
        # Deve stare qui, dopo che mappa/log/stato sono già aggiornati:
        # prima si elabora, poi si notifica.
        from services.alarm_service import should_alarm
        event_id = filtrato.get("event_id")
        if (event_id
                and event_id not in self._alarmed_event_ids
                and not self.model.is_manuale(filtrato)
                and should_alarm(filtrato)):
            self._alarmed_event_ids.add(event_id)
            self._trigger_alarm(filtrato)

    def _normalizza_zona_kafka(self, area: str | None) -> str:
        AREA_MAP = {
            'vesuvio':  'VESUVIO',
            'flegrei':  'CAMPI FLEGREI',
            'ischia':   'ISCHIA',
        }
        if not area:
            return 'GENERALE'
        return AREA_MAP.get(area.lower().strip(), 'GENERALE')
    
    def _chiave_evento_mappa(self, entry: dict, gruppi: dict) -> str:
     """Chiave stabile per riconoscere la stessa scossa tra automatica e revisione.
     Preferisce event_id; se assente, raggruppa per area + prossimità temporale
     (stesso criterio usato da seleziona_ultima_scossa per lo stato di sistema)."""
     event_id = entry.get("event_id")
     if event_id:
        return str(event_id)

     area = entry.get("area") or entry.get("area_desc")
     dt = parse_event_datetime(entry.get("data"))
     if dt is None:
        return f"{area}|{entry.get('data')}"

     for chiave, esistente in gruppi.items():
        if esistente.get("area") != area:
            continue
        dt_esistente = parse_event_datetime(esistente.get("data"))
        if dt_esistente and abs((dt - dt_esistente).total_seconds()) <= self.TOLLERANZA_MAPPA_SECONDI:
            return chiave

     return f"{area}|{entry.get('data')}"
    

    # def _chiave_evento_mappa(self, entry: dict, gruppi: dict) -> str:
    #  """Chiave stabile per riconoscere la stessa scossa tra automatica e revisione.
    #  Preferisce event_id; se assente, raggruppa per area + prossimità temporale
    #  (stesso criterio usato da seleziona_ultima_scossa per lo stato di sistema)."""
    #  event_id = entry.get("event_id")
    #  if event_id:
    #     return str(event_id)

    #  area = entry.get("area") or entry.get("area_desc")
    #  dt = parse_event_datetime(entry.get("data"))
    #  if dt is None:
    #     return f"{area}|{entry.get('data')}"

    #  for chiave, esistente in self._eventi_mappa.items():
    #     if esistente.get("area") != area:
    #         continue
    #     dt_esistente = parse_event_datetime(esistente.get("data"))
    #     if dt_esistente and abs((dt - dt_esistente).total_seconds()) <= self.TOLLERANZA_MAPPA_SECONDI:
    #         return chiave

    #  return f"{area}|{entry.get('data')}"

    # def _aggiorna_evento_mappa(self, lat, lon, mag, time_str, qualita, area, filtrato_o_entry: dict):
    #  """Sostituisce (non aggiunge) il pallino della scossa sulla mappa con l'ultima revisione arrivata."""
    #  if lat is None or lon is None or mag is None:
    #     return
    #  chiave = self._chiave_evento_mappa(filtrato_o_entry)
    #  self._eventi_mappa[chiave] = {
    #     "lat": lat, "lng": lon, "mag": mag,
    #     "data": time_str, "qualita": qualita, "area": area
    #  }
    #  self.map_service.clear_eventi()
    #  self.map_service.add_eventi_batch(list(self._eventi_mappa.values()))
    
    def _aggiorna_evento_mappa(self, lat, lon, mag, time_str, qualita, area, filtrato_o_entry: dict):
     """Sostituisce (non aggiunge) il pallino della scossa sulla mappa con l'ultima revisione arrivata."""
     if lat is None or lon is None or mag is None:
        return
     chiave = self._chiave_evento_mappa(filtrato_o_entry, self._eventi_mappa)
     self._eventi_mappa[chiave] = {
        "lat": lat, "lng": lon, "mag": mag,
        "data": time_str, "qualita": qualita, "area": area
     }
    #  self.map_service.clear_eventi()
    #  self.map_service.add_eventi_batch(list(self._eventi_mappa.values()))
     self.map_service.upsert_evento(chiave, lat, lon, mag, time_str, qualita, area)

    def _trigger_alarm(self, filtrato: dict):
        self.audio_service.play()
        zona = self._normalizza_zona_kafka(filtrato.get("area"))
        print(f"🚨 [ALLARME] Evento automatico M{filtrato['magnitudine']} — "
              f"{filtrato['area_desc']} — {filtrato['data']}")

        # La card rossa resta anche dopo che il popup è sparito
        self._accendi_allarme_card(zona, filtrato.get("magnitudine"))

        if not self.view:
            return

        # se ce n'è già uno a schermo lo chiudo: vince l'allarme più recente
        if self._alarm_dialog is not None:
            self._alarm_dialog.close()

        dialog = AlarmDialog(
            parent=self.view,
            ui_scale=self.view.ui_scale,
            magnitudo=filtrato.get("magnitudine"),
            zona=filtrato.get("area_desc", "n.d.")
        )
        dialog.setModal(False)          # non bloccante: la mappa continua ad aggiornarsi
        self._alarm_dialog = dialog     # tiene vivo il riferimento, altrimenti Python lo distrugge
        dialog.show()
        dialog.raise_()
        QTimer.singleShot(self.DURATA_ALLARME_MS, dialog.close)

    def on_kafka_swarm_message(self, msg):
        self.kafka_recorder.save(msg.value, topic=getattr(msg, "topic", None))
        dati = msg.value
        if not isinstance(dati, dict):
            print(f"⚠️ [KAFKA SWARM] Formato inatteso: {type(dati)}")
            return

        zona = self._normalizza_zona_kafka(dati.get("area"))
        tipo_comunicato = dati.get("type")
        sciame_finito = tipo_comunicato == "end" or bool((dati.get("end_time") or "").strip())

        print(f"📢 [KAFKA SWARM] {zona} - tipo: {tipo_comunicato} - "
              f"Ev#{dati.get('event_number')} - Md{dati.get('max_md')}")

        if sciame_finito:
            tooltip = f"Sciame concluso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"
            self.official_swarms.pop(zona, None)

            # Mostra esplicitamente lo stato di chiusura ufficiale
            self.swarm_states[zona] = ("SCIAME TERMINATO", "#2e7d32", tooltip)
            if self.view and hasattr(self.view, "tabs_view"):
                self.view.tabs_view.update_zone_swarm_state(zona, "SCIAME TERMINATO", "#2e7d32", tooltip)

            # Allinea anche il detector euristico, così non riproponga subito INIZIATO/IN CORSO
            if zona in self.swarm_detectors:
                self.swarm_detectors[zona].previous_state = "SCIAME TERMINATO"

            self._update_global_swarm_banner()
            return

        self.official_swarms[zona] = dati

        if tipo_comunicato == "news":
            etichetta = "SCIAME INIZIATO"
            colore = "#EF6C00"
            tooltip = f"Nuovo sciame rilevato — Md {dati.get('max_md', '?')}"
        else:
            etichetta = "SCIAME IN CORSO"
            colore = "#c62828"
            tooltip = f"Sciame in corso — Ev#{dati.get('event_number', '?')} Md {dati.get('max_md', '?')}"

        self.swarm_states[zona] = (etichetta, colore, tooltip)

        if self.view and hasattr(self.view, "tabs_view"):
            self.view.tabs_view.update_zone_swarm_state(zona, etichetta, colore, tooltip)

        self._update_global_swarm_banner()

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

            # ── DEBUG: quali "type" distinti arrivano da Serenade? ──
            tipi_trovati = set()
            for evento in records:
                if isinstance(evento, dict):
                    tipi_trovati.add(evento.get("type", "MANCANTE"))
            print(f"[SERENADE] Tipi di evento trovati in questo batch: {tipi_trovati}")
            print(f"[SERENADE] Numero totale eventi nel batch: {len(records)}")

            self.map_service.clear_eventi()

            mappa_batch = {}
            log_generale = []
            log_per_zona = {}

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
                    tipo = evento.get("type", "unknown")
                    tipo_desc = evento.get("type_desc", "")
                    author = loc.get("author")
                    event_id = evento.get("id") or evento.get("event_id")

                    if lat is None or lon is None:
                        continue

                    if mag is not None:
                        chiave_evt = self._chiave_evento_mappa(
                            {"event_id": event_id, "area": area, "data": time_str},
                            mappa_batch
                        )
                        mappa_batch[chiave_evt] = {
                            "lat": lat, "lng": lon, "mag": mag,
                            "data": time_str, "qualita": qualita,
                            "area": area
                        }

                    # if mag is not None:
                    #     batch_map.append({
                    #         "lat": lat, "lng": lon, "mag": mag,
                    #         "data": time_str, "qualita": qualita,
                    #         "area": area
                    #     })

                    log_entry = {
                        "event_id":      event_id,
                        "data":          time_str,
                        "area":          evento.get("area"),
                        "area_desc":     area,
                        "magnitudine":   mag,
                        "profondita_km": dep,
                        "latitudine":    lat,
                        "longitudine":   lon,
                        "qualita":       qualita,
                        "tipo":          tipo,
                        "tipo_desc":     tipo_desc,
                        "communicate":   evento.get("communicate"),
                        "author":        author,
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

            # ── Inserisci nel model (che ora riordina l'INTERA lista per data) ──
            if log_generale:
                self.model.add_log_batch("GENERALE", log_generale)

            zone_aggiornate = []

            for zona, msgs in log_per_zona.items():
                self.model.add_log_batch(zona, msgs)
                zone_aggiornate.append(zona)

            for zona in zone_aggiornate:
                self._update_swarm_widget(zona)

            if self.view:
                self.view.tabs_view.update_zone_cards(self.model.tab_logs)

                ultimo_evento = self.model.aggiorna_stato_da_logs(seleziona_ultima_scossa)
                if ultimo_evento:
                    self.model.last_event_time = datetime.now()
                    mag_ultimo = ultimo_evento.get("magnitudine")
                    print(f"🔔 [SERENADE] Stato aggiornato dall'ultimo evento: "
                          f"{ultimo_evento.get('data')} - M{mag_ultimo} - Stato: {self.model.status.value}")

            # ── Una sola chiamata JS per la mappa ─────────────────────────
            # self.map_service.add_eventi_batch(batch_map)
            self.map_service.add_eventi_batch(list(mappa_batch.values()))

        finally:
            self._elaborando = False

    def get_active_source(self):
        """Ritorna 'kafka' o 'serenade' in base al worker configurato, per sapere come interpretare l'ordine dei log."""
        from servers.serenade.serenade import SerenadeWorker
        from servers.serverkafka.kafka import KafkaWorker

        if isinstance(self.data_worker, KafkaWorker):
            return "kafka"
        elif isinstance(self.data_worker, SerenadeWorker):
            return "serenade"
        return None

    # def _filtra_e_aggiorna_logs(self):
    #     """Riapplica il filtro attivo e aggiorna la vista. Da chiamare dopo ogni batch."""
    #     if self.view is None:
    #         return
    #     self.on_filter_changed(self._active_filter)
    def _filtra_e_aggiorna_logs(self):
     """Riapplica il filtro attivo alle SOLE tabelle di log. Da chiamare dopo ogni
     messaggio/batch. Non deve toccare la mappa: farlo forzerebbe applyFilter() a
     ridisegnare tutti i pallini ad ogni evento, chiudendo qualunque popup aperto."""
     if self.view is None:
        return
     self.render_logs_filtrati()

    # ─────────────────────────────────────────────────────────
    #  SCIAMI
    # ─────────────────────────────────────────────────────────

    def _detect_swarm_state_from_logs(self, zona):
        detector = self.swarm_detectors.get(zona)
        if detector is None:
            return "NESSUNO", "#53565A", "Zona non monitorata"
        eventi = self.model.tab_logs.get(zona, [])
        return detector.detect(eventi)

    def _update_swarm_widget(self, zona):
        if zona not in self.swarm_detectors:
            return

        # Chiama SEMPRE detect(), anche se il comunicato ufficiale ha priorità sul badge:
        # serve a tenere aggiornato previous_state, così la transizione a TERMINATO
        # sarà corretta quando il comunicato ufficiale finirà.
        detector_state, detector_color, detector_tooltip = self._detect_swarm_state_from_logs(zona)

        if zona in self.official_swarms:
            return  # il badge resta quello del comunicato ufficiale, già impostato altrove

        self.swarm_states[zona] = (detector_state, detector_color, detector_tooltip)

        if self.view and hasattr(self.view, "tabs_view"):
            self.view.tabs_view.update_zone_swarm_state(zona, detector_state, detector_color, detector_tooltip)

        self._update_global_swarm_banner()

    def _update_global_swarm_banner(self):
        if not self.view or not hasattr(self.view, "header") or not self.swarm_states:
            return

        peggiore_zona = min(
            self.swarm_states,
            key=lambda z: self._SWARM_SEVERITY.get(self.swarm_states[z][0], 99)
        )

        state, color, tooltip = self.swarm_states[peggiore_zona]

        if state not in ("NESSUNO", "ATTIVITÀ ORDINARIA"):
            tooltip = f"{peggiore_zona}: {tooltip}"
            label = f"{state} - {peggiore_zona}"
        else:
            label = state

        self.view.header.update_swarm_state(label, color, tooltip)