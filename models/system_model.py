from enum import Enum
import json


class SystemStatus(Enum):
    QUIETE = "QUIETE"                 # nessun evento da abbastanza tempo
    NON_DETERMINATO = "N.D."          # c'è un evento ma senza magnitudo
    NORMALE = "NORMALE"
    ATTENZIONE = "ATTENZIONE"
    ALLARME = "ALLARME"


class SystemModel:
    """MODEL: Gestisce solo lo stato dell'applicazione.

    UNICO punto in cui si decide lo stato del sistema: né la View né il
    Controller devono ricalcolarlo dai log."""

    # Soglie: cambiare QUI e in nessun altro posto.
    SOGLIA_ALLARME    = 3.0
    SOGLIA_ATTENZIONE = 2.0

    # Inizializza lo stato del sistema, i log e la lista degli observer.
    def __init__(self):
        self._status = SystemStatus.QUIETE
        self._evento_stato = None      # evento che ha determinato lo stato corrente
        self._last_event_time = None
        self._tab_logs = {
            "GENERALE": [],
            "CAMPI FLEGREI": [],
            "VESUVIO": [],
            "ISCHIA": []
        }
        self._observers = []

    # ------------------------------------------------------------------
    # Distinzione automatico / manuale
    # ------------------------------------------------------------------
    @staticmethod
    # Stabilisce se un evento è stato revisionato manualmente.
    def is_manuale(log_entry: dict) -> bool:
        """
        Restituisce True soltanto quando l'autore è presente
        ed è diverso da Earthworm.

        Se author manca, l'evento viene trattato come automatico,
        utile soprattutto durante il replay.
        """
        author = log_entry.get("author")

        if author is None or str(author).strip() == "":
            return False

        return "earthworm" not in str(author).lower()

    # ------------------------------------------------------------------
    # Stato di sistema
    # ------------------------------------------------------------------
    @classmethod
    # Determina lo stato del sistema in base alla magnitudo.
    def _status_da_magnitudo(cls, mag) -> SystemStatus:
        """mag=None è un esito valido (N.D.), non un errore."""
        if mag is None:
            return SystemStatus.NON_DETERMINATO
        if mag >= cls.SOGLIA_ALLARME:
            return SystemStatus.ALLARME
        if mag >= cls.SOGLIA_ATTENZIONE:
            return SystemStatus.ATTENZIONE
        return SystemStatus.NORMALE

    @staticmethod
    # Converte la magnitudo in float, restituendo None se non valida.
    def _to_float(mag):
        """Converte a float, oppure None se assente o non valida."""
        if mag is None:
            return None
        try:
            return float(mag)
        except (TypeError, ValueError):
            return None

    # Aggiorna lo stato usando l'evento cronologicamente più recente.
    def aggiorna_stato_da_logs(self, seleziona_ultima_scossa_fn, richiedi_automatico: bool = True):
     """
     MODALITÀ REALE: lo stato segue l'evento cronologicamente più recente.

     richiedi_automatico: se True (default, comportamento Kafka) esclude i log
     manuali dalla ricerca. Se False (Serenade) considera tutti i log, perché
     per Serenade la distinzione automatico/manuale non è affidabile/rilevante.
     """
     logs = self._tab_logs.get("GENERALE", [])
     if richiedi_automatico:
        logs = [e for e in logs if isinstance(e, dict) and not self.is_manuale(e)]
     else:
        logs = [e for e in logs if isinstance(e, dict)]

     ultimo = seleziona_ultima_scossa_fn(logs)
     if ultimo is None:
        return

     mag = self._to_float(ultimo.get("magnitudine"))
     self._evento_stato = ultimo
     self.status = self._status_da_magnitudo(mag)
     return ultimo

    # Aggiorna lo stato usando l'ultimo evento ricevuto.
    def aggiorna_stato_da_evento_ricevuto(self, evento: dict):
        """
        MODALITÀ TEST/REPLAY: lo stato segue l'ultimo messaggio ARRIVATO,
        indipendentemente dalla data che contiene.

        Le revisioni manuali non modificano lo stato. Gli eventi senza
        magnitudo invece sì: portano lo stato a N.D.
        """
        if not isinstance(evento, dict):
            return None

        if self.is_manuale(evento):
            return None

        mag = self._to_float(evento.get("magnitudine"))

        self._evento_stato = evento          # PRIMA di self.status: il setter notifica subito
        self.status = self._status_da_magnitudo(mag)
        return evento

    # Riporta il sistema nello stato di quiete.
    def reset_a_quiete(self):
        """Chiamato dal timer del Controller dopo abbastanza silenzio."""
        if self._status is SystemStatus.QUIETE:
            return                            # evita di ridisegnare la UI a ogni tick
        self._evento_stato = None
        self.status = SystemStatus.QUIETE

    # ------------------------------------------------------------------
    # Observer pattern esistente
    # ------------------------------------------------------------------
    # Registra un observer da notificare quando il modello cambia.
    def add_observer(self, observer):
        self._observers.append(observer)

    # Notifica agli observer che i dati del modello sono cambiati.
    def notify_observers(self):
        for observer in self._observers:
            observer.update_ui()

    @property
    # Restituisce o aggiorna lo stato corrente del sistema.
    def status(self):
        return self._status

    @status.setter
    # Restituisce o aggiorna lo stato corrente del sistema.
    def status(self, value):
        self._status = value
        self.notify_observers()

    @property
    # Restituisce l'evento che ha determinato lo stato corrente.
    def evento_stato(self):
        """L'evento che ha determinato lo stato corrente. None se in QUIETE."""
        return self._evento_stato

    @property
    # Restituisce o aggiorna l'istante di arrivo dell'ultimo evento.
    def last_event_time(self):
        return self._last_event_time

    @last_event_time.setter
    # Restituisce o aggiorna l'istante di arrivo dell'ultimo evento.
    def last_event_time(self, value):
        self._last_event_time = value
        self.notify_observers()

    @property
    # Restituisce i log suddivisi per zona.
    def tab_logs(self):
        return self._tab_logs

    # Aggiunge un singolo evento ai log della zona indicata.
    def add_log(self, zone, message):
        if zone not in self._tab_logs:
            zone = "GENERALE"

        self._tab_logs[zone].append(message)

        self._tab_logs[zone].sort(
            key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
            reverse=True
        )

        if len(self._tab_logs[zone]) > 500:
            self._tab_logs[zone] = self._tab_logs[zone][:500]

        self.notify_observers()

    # Aggiunge più eventi ai log della zona indicata.
    def add_log_batch(self, zona: str, messaggi: list):
        if zona not in self._tab_logs:
            zona = "GENERALE"

        self._tab_logs[zona].extend(messaggi)

        self._tab_logs[zona].sort(
            key=lambda e: e.get("data", "") if isinstance(e, dict) else "",
            reverse=True
        )

        if len(self._tab_logs[zona]) > 500:
            self._tab_logs[zona] = self._tab_logs[zona][:500]

        self.notify_observers()

    # Restituisce il colore associato allo stato corrente.
    def get_status_color(self):
        colors = {
            SystemStatus.QUIETE:          "#53565A",   # grigio "a riposo"
            SystemStatus.NON_DETERMINATO: "#6b7280",   # stesso grigio di _colore_magnitudo(None)
            SystemStatus.NORMALE:         "#2e7d32",
            SystemStatus.ATTENZIONE:      "#ff9800",
            SystemStatus.ALLARME:         "#d32f2f",
        }
        return colors.get(self._status, "#53565A")

    @staticmethod
    # Estrae e normalizza i dati utili da un messaggio Kafka.
    def filtra_messaggio_kafka(msg_value) -> dict | None:
        """
        Estrae i dati essenziali da un messaggio Kafka INGV.

        Gestisce due formati:
        1. lista con blocco name='event' -> evento sismico confermato
        2. dict con channels -> trigger sismico
        """

        if isinstance(msg_value, (str, bytes)):
            try:
                msg_value = json.loads(msg_value)
            except (json.JSONDecodeError, ValueError):
                print(f"[KAFKA] msg.value non è JSON valido")
                return None

        # FORMATO TRIGGER
        if isinstance(msg_value, dict) and "channels" in msg_value:
            area_raw = msg_value.get("area", "unknown")

            area_map = {
                "Vesuvio": "vesuvio",
                "Campi Flegrei": "flegrei",
                "Ischia": "ischia",
            }

            return {
                "event_id": None,
                "tipo": "trigger",
                "tipo_desc": "Trigger sismico",
                "area": area_map.get(area_raw, str(area_raw).lower()),
                "area_desc": area_raw,
                "data": msg_value.get("time_iso"),
                "latitudine": None,
                "longitudine": None,
                "profondita_km": None,
                "magnitudine": None,
                "mag_tipo": None,
                "mag_errore": None,
                "qualita": "trigger",
                "metodo": msg_value.get("modId"),
                "n_picks": len(msg_value.get("channels", {})),
                "rms": None,
                "gap_azimutale": None,
                "communicate": None,
                "author": None,
            }

        if not isinstance(msg_value, list):
            print(f"[KAFKA] Formato inatteso: {type(msg_value)}")
            return None

        event_block = None

        for item in msg_value:
            if isinstance(item, dict) and item.get("name") == "event":
                event_block = item.get("data", {})
                break

        if event_block is None:
            return None

        tipo = event_block.get("type", "unknown")
        tipo_desc = event_block.get("type_desc", "")

        area = event_block.get("area", "unknown")
        area_desc = event_block.get("adesc", "")

        data_evento = event_block.get("date") or event_block.get("epoch")

        loc = event_block.get("location", {}) or {}

        latitudine = loc.get("latitude")
        longitudine = loc.get("longitude")
        profondita = loc.get("depth")
        qualita = loc.get("quality")
        metodo = loc.get("method")
        n_picks = loc.get("pick_number")
        author = loc.get("author")

        magnitudos = loc.get("magnitudos", []) or []
        mag_scelta = None

        for m in magnitudos:
            if str(m.get("type", "")).upper() == "D":
                mag_scelta = m
                break

        if mag_scelta is None and magnitudos:
            mag_scelta = magnitudos[0]

        if mag_scelta:
            mag_val = mag_scelta.get("value")
            mag_tipo = mag_scelta.get("type")
            mag_errore = mag_scelta.get("error")
        else:
            mag_val = None
            mag_tipo = None
            mag_errore = None

        errori = loc.get("errors", {}) or {}
        rms = errori.get("rms")
        gap = errori.get("gap")

        event_id = event_block.get("id")

        return {
            "event_id": event_id,
            "tipo": tipo,
            "tipo_desc": tipo_desc,
            "area": area,
            "area_desc": area_desc,
            "data": data_evento,
            "latitudine": latitudine,
            "longitudine": longitudine,
            "profondita_km": profondita,
            "magnitudine": mag_val,
            "mag_tipo": mag_tipo,
            "mag_errore": mag_errore,
            "qualita": qualita,
            "metodo": metodo,
            "author": author,
            "n_picks": n_picks,
            "rms": rms,
            "gap_azimutale": gap,
            "communicate": event_block.get("communicate"),
        }