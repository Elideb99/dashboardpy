"""
Script UNICO e autonomo per testare il rilevamento sciami sulla tua
registrazione. NON dipende da nessun altro file e NON devi toccare il tuo
codice. Salvalo dove vuoi e lancialo:

    python3 test_sciami.py test_data/kafka_recordings/kafka_20260708_114405.jsonl

Legge la registrazione, distingue scosse e sciami (dal contenuto, quindi
funziona anche senza il campo 'topic'), e stampa lo stato dello sciame
leggendolo dai messaggi 'swarms' di INGV.
"""

import json
import sys


def tipo_messaggio(value):
    """Sciame o scossa? Lo capisce guardando il contenuto del messaggio."""
    if isinstance(value, dict) and "swarm_id" in value:
        return "sciame"
    if isinstance(value, list):
        for blocco in value:
            if isinstance(blocco, dict) and blocco.get("name") == "event":
                return "evento"
    return "altro"


def stato_sciame(sciame):
    """Dai campi del messaggio-sciame ricava lo stato leggibile."""
    if (sciame.get("end_time") or "").strip():
        return "SCIAME TERMINATO"
    if (sciame.get("type") or "").lower() == "news":
        return "SCIAME INIZIATO"
    return "SCIAME IN CORSO"


def main(percorso):
    n_eventi = n_sciami = 0
    ultimo_stato = None

    print(f"\nLeggo {percorso}\n")
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            record = json.loads(riga)
            value = record.get("value", record)
            tipo = tipo_messaggio(value)

            if tipo == "evento":
                n_eventi += 1
            elif tipo == "sciame":
                n_sciami += 1
                stato = stato_sciame(value)
                if stato != ultimo_stato:      # stampo solo ai cambi di stato
                    ultimo_stato = stato
                    print(f"  {stato:17s} swarm_id={value.get('swarm_id')} "
                          f"eventi={value.get('event_number')} "
                          f"Md_max={value.get('max_md')} "
                          f"inizio={value.get('start_time')}")

    print(f"\nTotale nel file: {n_eventi} scosse, {n_sciami} messaggi-sciame\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 test_sciami.py <file_registrazione.jsonl>")
        raise SystemExit(1)
    main(sys.argv[1])
