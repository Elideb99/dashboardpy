from datetime import datetime, timedelta


class SwarmDetector:
    def __init__(self):
        self.previous_state = "NESSUNO"

    def _parse_time(self, date_str):
        if not date_str:
            return None

        date_str = str(date_str).replace("T", " ")[:19]

        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def detect(self, eventi):
        now = datetime.now()

        eventi_1h = []
        eventi_6h = []
        eventi_24h = []

        for event in eventi:
            if not isinstance(event, dict):
                continue

            event_time = self._parse_time(event.get("data") or event.get("date"))
            if not event_time:
                continue

            if event_time > now:
                continue

            if event_time >= now - timedelta(hours=1):
                eventi_1h.append(event)

            if event_time >= now - timedelta(hours=6):
                eventi_6h.append(event)

            if event_time >= now - timedelta(hours=24):
                eventi_24h.append(event)

        eventi_confermati_1h = [
            e for e in eventi_1h
            if str(e.get("tipo", "")).lower() != "trigger"
        ]

        eventi_confermati_6h = [
            e for e in eventi_6h
            if str(e.get("tipo", "")).lower() != "trigger"
        ]

        trigger_1h = [
            e for e in eventi_1h
            if str(e.get("tipo", "")).lower() == "trigger"
        ]

        # Logica stati - solo quelli effettivamente usati
        if len(eventi_confermati_1h) >= 3:
            state = "SCIAME INIZIATO"
            color = "#FF9800"  # arancione
            tooltip = f"{len(eventi_confermati_1h)} eventi confermati nell'ultima ora"

        elif len(eventi_confermati_6h) >= 5:
            state = "SCIAME IN CORSO"
            color = "#E53935"  # rosso
            tooltip = f"{len(eventi_confermati_6h)} eventi confermati nelle ultime 6 ore"

        elif self.previous_state in [
            "SCIAME INIZIATO",
            "SCIAME IN CORSO",
        ] and len(eventi_confermati_6h) < 2 and len(trigger_1h) < 2:
            state = "SCIAME TERMINATO"
            color = "#3DDC84"  # verde
            tooltip = "Attività sismica rientrata"

        else:
            state = "NESSUNO"
            color = "#53565A"  # grigio
            tooltip = "Nessun evento o attività insufficiente per uno sciame"

        self.previous_state = state
        return state, color, tooltip