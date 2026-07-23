import json
from pathlib import Path

# script una tantum: aggiunge il campo "topic" mancante a una registrazione Kafka vecchia,
# deducendolo dalla forma del payload (vedi elif sotto)
INPUT = Path("test_data/kafka_recordings/kafka_20260708_114405.jsonl")
OUTPUT = INPUT.with_name(INPUT.stem + "_fixed.jsonl")

n_swarms = 0
n_eventi = 0
n_altro = 0

with open(INPUT, encoding="utf-8") as fin, open(OUTPUT, "w", encoding="utf-8") as fout:
    for i, line in enumerate(fin, start=1):
        line = line.strip()
        if not line:
            continue

        record = json.loads(line)
        value = record.get("value", {})

        if record.get("topic"):
            # già presente (es. se in futuro rilanci lo script su un file già fixato)
            pass
        elif isinstance(value, dict) and "swarm_id" in value:
            record["topic"] = "replay.swarms"
            n_swarms += 1
        elif isinstance(value, dict) and "channels" in value and "modId" in value:
            record["topic"] = "eew_events"   # i trigger che avevi visto prima
            n_altro += 1
        elif isinstance(value, dict):
            record["topic"] = "replay.events"
            n_eventi += 1
        else:
            record["topic"] = None
            n_altro += 1

        fout.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

print(f"Fatto: {OUTPUT}")
print(f"  replay.swarms : {n_swarms}")
print(f"  replay.events : {n_eventi}")
print(f"  altro/trigger : {n_altro}")