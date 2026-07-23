import json
import hashlib
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _impronta(value, topic):
    """Chiave stabile del messaggio, SENZA received_at (che cambia a ogni run),
    così lo stesso evento registrato prima viene riconosciuto e saltato."""
    testo = json.dumps({"topic": topic, "value": value},
                       ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(testo.encode("utf-8")).hexdigest()


class KafkaRecorder:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else BASE_DIR / "test_data" / "kafka_recordings"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # carica le impronte di TUTTO ciò che è già in kafka_recordings, scandendo tutti i .jsonl esistenti
        self._gia_visti = self._carica_impronte()

        # ogni avvio crea un nuovo file di registrazione (timestampato), ma la deduplica
        # controlla anche i file precedenti tramite _gia_visti
        filename = datetime.now().strftime("kafka_%Y%m%d_%H%M%S.jsonl")
        self.file_path = self.output_dir / filename

        self.enabled = False   # opt-in: si registra solo se lo decidi tu nel config
        self.blocked = False   # vince su tutto: durante il replay non si scrive mai
        

    def _carica_impronte(self):
        visti = set()
        for percorso in self.output_dir.glob("*.jsonl"):
            try:
                with open(percorso, encoding="utf-8") as f:
                    for riga in f:
                        riga = riga.strip()
                        if not riga:
                            continue
                        rec = json.loads(riga)
                        visti.add(_impronta(rec.get("value"), rec.get("topic")))
            except (OSError, json.JSONDecodeError):
                continue   # file corrotto o illeggibile: ignoralo e prosegui con gli altri
        print(f"[RECORDER] {len(visti)} messaggi già registrati: verranno saltati")
        return visti

    def save(self, msg_value, topic=None):

        if not self.enabled or not self.enabled:
            return 
        
        chiave = _impronta(msg_value, topic)
        if chiave in self._gia_visti:
            return  # già presente in una registrazione precedente: non riscrivo

        self._gia_visti.add(chiave)
        record = {
            "received_at": datetime.now().isoformat(),   # solo metadato, escluso dal calcolo dell'impronta
            "topic": topic,
            "value": msg_value,
        }
        # append su file: ogni chiamata apre/chiude il file (nessun handle tenuto aperto tra le save)
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")