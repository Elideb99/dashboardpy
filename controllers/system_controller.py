
from datetime import datetime,timedelta
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
    QUIETE_DOPO_SECONDI   = 15 * 60   # 15 minuti - silenzio necessario per tornare in QUIETE
    ALLARME_CARD_DURATA_S = 1 * 60   # 1 minuto - per quanto la card resta rossa dopo una scossa forte
    TICK_QUIETE_MS        = 30_000    # ogni 30 secondi il timer controlla se deve fare qualcosa
    DURATA_ALLARME_MS     = 30_000     # 30 secondi - per quanto resta a schermo il popup
    TOLLERANZA_MAPPA_SECONDI = 2   # stessa tolleranza di seleziona_ultima_scossa
    # se kafka invia lo stesso messaggio relativo alla stessa scossa più volte in meno di 2 secondi allora capisce che è la stessa scossa quindi aggiorna il pallino esistente

    

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
        self._ultimo_sciame_ufficiale = {}   # zona -> ultimo comunicato sciame, mantenuto anche a sciame concluso
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
     """Ridisegna le tabelle con TUTTI i log (ordinati per data). I filtri
     temporali (24h/48h/...) riguardano solo i pallini sulla mappa, mai
     il contenuto delle tabelle — per nessuna delle due fonti."""
     if self.view is None:
        return
     for zona in ["GENERALE", "CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
        logs = self.model.tab_logs.get(zona, [])
        ordinati = sorted(
            logs,
            key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
            reverse=True
        )
        self.view.tabs_view.update_logs(zona, ordinati)


    def _filtra_e_aggiorna_logs(self):
     if self.view is None:
        return
     self.render_logs_filtrati()


    def on_filter_changed(self, key):
     self._active_filter = key

     if (self.map_service.map_ready
            and self.view and self.view.map_widget and self.view.map_widget.webview):
        self.view.map_widget.webview.page().runJavaScript(
            f'if (window.setTimeFilter) {{ window.setTimeFilter("{key}"); }}'
        )

     self.render_logs_filtrati()

    # ─────────────────────────────────────────────────────────
    #  LOGICA KAFKA
    # ─────────────────────────────────────────────────────────

    def on_kafka_message(self, msg):
        # print("🔵 [KAFKA] Messaggio ricevuto")

        # Registra il messaggio Kafka
        self.kafka_recorder.save(msg.value)

        if isinstance(msg.value, list):
            nomi_blocchi = [item.get("name") for item in msg.value if isinstance(item, dict)]
            # print(f"[KAFKA] Blocchi presenti (lista): {nomi_blocchi}")

        elif isinstance(msg.value, dict):
            # print(f"[KAFKA] Messaggio DICT. Chiavi: {list(msg.value.keys())}")
            print(json.dumps(msg.value, indent=2, default=str))

        else:
             print(f"[KAFKA] Tipo inatteso: {type(msg.value)}")

        filtrato = SystemModel.filtra_messaggio_kafka(msg.value)

        if filtrato is None:
            print("⚠️ [KAFKA] Messaggio filtrato -> None")
            return

        print("TIPO EVENTO:", filtrato.get("tipo"))

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
    


    def _aggiorna_evento_mappa(self, lat, lon, mag, time_str, qualita, area, filtrato_o_entry: dict):
     """Sostituisce il pallino della scossa sulla mappa con la STESSA regola
     usata dalla tabella (seleziona_rappresentante): tra tutte le revisioni note
     di un evento, vince quella con la data DELL'EVENTO (non di arrivo) più
     recente che ha magnitudo. Una revisione senza magnitudo non sovrascrive
     mai; una revisione più vecchia per data-evento, anche se arrivata dopo,
     non sovrascrive una revisione già più recente."""
     if lat is None or lon is None or mag is None:
        return

     chiave = self._chiave_evento_mappa(filtrato_o_entry, self._eventi_mappa)
     esistente = self._eventi_mappa.get(chiave)

     if esistente is not None:
        dt_nuovo = parse_event_datetime(time_str)
        dt_esistente = parse_event_datetime(esistente.get("data"))
        if dt_nuovo is not None and dt_esistente is not None and dt_nuovo < dt_esistente:
            return  # revisione più vecchia per data-evento arrivata in ritardo: ignorata

     self._eventi_mappa[chiave] = {
        "lat": lat, "lng": lon, "mag": mag,
        "data": time_str, "qualita": qualita, "area": area
     }
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

        # ricorda sempre l'ultimo sciame della zona (anche l'"end"), così il replay
        # funziona a sciame concluso. Fondo i campi non-None per non perdere lo start_time.
        prec = self._ultimo_sciame_ufficiale.get(zona, {})
        self._ultimo_sciame_ufficiale[zona] = {**prec, **{k: v for k, v in dati.items() if v is not None}}



        tipo_comunicato = dati.get("type")
        sciame_finito = tipo_comunicato == "end" or bool((dati.get("end_time") or "").strip())

        # Memorizza il picco dello sciame nella card.
        if self.view and hasattr(self.view, "tabs_view"):
          self.view.tabs_view.update_zone_swarm_peak(
          zona,
          dati.get("max_md"),
          dati.get("start_time")
          or dati.get("time_iso")
          or dati.get("end_time")
         )

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

        print(f"[SERENADE] Numero totale eventi nel batch: {len(records)}")

        # ── Chiavi già presenti in GENERALE, per scartare i duplicati ──
        chiavi_esistenti = {
            (e.get("event_id") or f"{e.get('area')}|{e.get('data')}")
            for e in self.model.tab_logs.get("GENERALE", [])
            if isinstance(e, dict)
        }

        log_generale = []
        log_per_zona = {}
        nuovi = 0
        scartati = 0

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

                area_raw = evento.get("area")
                chiave_dedup = event_id or f"{area_raw}|{time_str}"

                if chiave_dedup in chiavi_esistenti:
                    scartati += 1
                    continue
                chiavi_esistenti.add(chiave_dedup)
                nuovi += 1

                self._aggiorna_evento_mappa(
                    lat, lon, mag, time_str, qualita, area,
                    {"event_id": event_id, "area": area, "data": time_str}
                )

                log_entry = {
                    "event_id":      event_id,
                    "data":          time_str,
                    "area":          area_raw,
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

                zona_tab_full = self._normalizza_zona_kafka(area_raw)
                zona_tab = zona_tab_full if zona_tab_full != "GENERALE" else None
                if zona_tab:
                    log_per_zona.setdefault(zona_tab, []).append(log_entry)

            except Exception as e:
                print(f"[SERENADE] Errore parsing evento {evento.get('id', '?')}: {e}")

        print(f"[SERENADE] Nuovi: {nuovi} | Scartati (duplicati): {scartati}")

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
            self._filtra_e_aggiorna_logs(applica_filtro_tempo=False)
            ultimo_evento = self.model.aggiorna_stato_da_logs(
                seleziona_ultima_scossa, richiedi_automatico=False
            )
            if ultimo_evento:
                self.model.last_event_time = datetime.now()
                zona_stato = self._normalizza_zona_kafka(ultimo_evento.get("area"))
                self.map_service.update_vulcano(
                    zona_stato, self.model.status.value, ultimo_evento.get("magnitudine")
                )
                print(f"🔔 [SERENADE] Stato aggiornato: {ultimo_evento.get('data')} "
                      f"- M{ultimo_evento.get('magnitudine')} - Stato: {self.model.status.value}")

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


        from datetime import datetime, timedelta

    def ottieni_magnitudo_da_mostrare(zona, eventi_vulcano, stato_vulcano):
     """
     Calcola la magnitudo da inviare alla mappa per una determinata zona:
     - Se c'è uno sciame sismico, prende la magnitudo massima dello sciame.
     - Altrimenti, prende la magnitudo più alta delle ultime 24 ore.
     """
    # 1. Caso SCIAME SISMICO
     if stato_vulcano == 'SCIAME':
        eventi_sciame = [e for e in eventi_vulcano if e.get("in_sciame") == True]
        if eventi_sciame:
            # Trova la magnitudo massima dello sciame
            magnitudini = [float(e.get("magnitudine", 0)) for e in eventi_sciame if e.get("magnitudine") is not None]
            if magnitudini:
                return max(magnitudini)

    # 2. Caso Standard / Mancanza di sciame attivo: cerca nelle ultime 24 ore
     ora_limite = datetime.now() - timedelta(hours=24)
     eventi_recenti = []

     for e in eventi_vulcano:
        data_str = e.get("data")
        if not data_str:
            continue
        try:
            # Adatta il formato data a quello del tuo model (es. "YYYY-MM-DD HH:MM:SS")
            data_evento = datetime.strptime(data_str.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
            if data_evento >= ora_limite:
                eventi_recenti.append(e)
        except ValueError:
            continue

     if eventi_recenti:
        # Estrae la magnitudo più significativa (massima) delle ultime 24 ore
        magnitudini_recenti = []
        for e in eventi_recenti:
            mag = e.get("magnitudine")
            if mag is not None:
                try:
                    magnitudini_recenti.append(float(mag))
                except ValueError:
                    pass
        if magnitudini_recenti:
            return max(magnitudini_recenti)

    # 3. Default: se non c'è nulla nelle ultime 24 ore, restituisce None (o 0)
     return None
    

    def on_replay_sciame_richiesto(self, azione):
     if azione != "sciame":
        return
     self._avvia_replay_ultimo_sciame()

    def _zona_ultimo_sciame(self):
     fonte = self.official_swarms or self._ultimo_sciame_ufficiale
     if fonte:
        zona, _ = max(fonte.items(),
                      key=lambda it: it[1].get("start_time") or it[1].get("time_iso") or "")
        return zona
     zone_attive = [
        z for z, (stato, _, _) in self.swarm_states.items()
        if stato not in ("NESSUNO", "ATTIVITÀ ORDINARIA")
     ]
     return zone_attive[0] if zone_attive else None

    def _avvia_replay_ultimo_sciame(self):
     zona = self._zona_ultimo_sciame()
     if zona is None:
        print("[REPLAY SCIAME] Nessuno sciame in memoria")
        return

     dati = self.official_swarms.get(zona) or self._ultimo_sciame_ufficiale.get(zona) or {}
     inizio = parse_event_datetime(dati.get("start_time") or dati.get("time_iso"))
     fine   = parse_event_datetime(dati.get("end_time")) or datetime.max

     def _mag(v):
        try:
            return float(str(v).lstrip("Mm").strip())
        except (TypeError, ValueError):
            return None

     payload = []
     for e in sorted(self.model.tab_logs.get(zona, []),
                    key=lambda e: e.get("data", "")):
        if not isinstance(e, dict):
            continue
        dt = parse_event_datetime(e.get("data"))
        if dt is None or (inizio and dt < inizio) or dt > fine:
            continue
        if e.get("latitudine") is None or e.get("longitudine") is None:
            continue
        mag = _mag(e.get("magnitudine"))
        if mag is None:
            continue   # niente n.d. nel replay
        payload.append({
            "lat": e.get("latitudine"), "lng": e.get("longitudine"),
            "mag": mag, "data": e.get("data"),
            "qualita": e.get("qualita"), "area": e.get("area_desc"),
        })

     if not payload:
        print(f"[REPLAY SCIAME] Nessun evento trovato per {zona}")
        return

     print(f"[REPLAY SCIAME] {zona}: {len(payload)} eventi")
     js = f"window.replaySciame({json.dumps(payload)}, 400)"
     self.view.map_widget.webview.page().runJavaScript(js)