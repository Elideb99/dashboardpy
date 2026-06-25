# 🌋 Osservatorio Vesuviano — Dashboard Simulatore

Applicazione desktop di simulazione per il monitoraggio sismico delle aree vulcaniche della Campania: **Vesuvio**, **Campi Flegrei** e **Ischia**.

---

## 📋 Descrizione

La Dashboard permette di simulare eventi sismici, sciami sismici e allarmi, visualizzando in tempo reale lo stato dei vulcani su una mappa interattiva. Include un sistema di log filtrabili per zona, pannelli flottanti e notifiche audio/visive.

---

## 🖥️ Requisiti di sistema

### Python
- Python **3.10** o superiore

### Librerie Python
```bash
pip install PyQt6 PyQt6-WebEngine PyQt6-Qt6-Multimedia
```

### Sistema operativo
| Ambiente | Supportato |
|---|---|
| Debian / Linux nativo | ✅ |
| WSL (Windows Subsystem for Linux) | ✅ |
| Windows (Python nativo) | ✅ |

### Dipendenze di sistema (Debian/Linux)
```bash
sudo apt install alsa-utils        # per aplay (fallback audio)
sudo apt install python3-pyqt6     # opzionale, se pip non basta
```

---

## 📁 Struttura del progetto (da modificare)

```

progetto/
├── main.py                 # Entry point
├── server.py              # Server HTTP (mappa)
├── map_config.json        # Configurazione tile layer
├── map.html               # Mappa Leaflet
├── alarm_dec.wav          # Suono allarme
├── icons/                 # Icone UI
│   ├── ingvlogo.png
│   ├── calendario.png
│   └── orario.png
├── models/
│   └── system_model.py    # Stato e dati (Model)
├── controllers/
│   └── system_controller.py # Logica applicativa (Presenter)
├── views/
│   ├── dashboard_view.py  # UI principale (View)
│   ├── dialogs.py         # Popup allarme
│   └── components/        # Componenti UI riutilizzabili
│       ├── header.py      # Header con logo e orologio
│       ├── tabs.py        # Tab dei log
│       ├── map_widget.py  # Widget mappa
│       └── controls.py    # Pulsanti di controllo
├── services/
│   ├── audio_service.py   # Servizio audio
│   └── map_service.py     # Servizio mappa
└── utils/
    └── helpers.py         # Utility varie
```

---

## Pattern utilizzato: MVP (Model-View-Presenter) ibrido

┌─────────────────────────────────────────────────────────────────┐
│                           MAIN.PY                               │
│                    (Composizione e bootstrap)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    MODEL     │    │   PRESENTER  │    │     VIEW     │
│ system_model │◄──►│   controller │◄──►│dashboard_view│
│              │    │              │    │              │
│ • Stato      │    │ • Logica     │    │ • Widget UI  │
│ • Dati       │    │ • Eventi     │    │ • Layout     │
│ • Observer   │    │ • Timer      │    │ • Popup      │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   SERVICES   │
                    │ audio/map    │
                    └──────────────┘

Questo è un MVP (Model-View-Presenter) con elementi di Layered Architecture.

Schema delle dipendenze:
View ──────┐
   │       │
   ▼       ▼
Presenter ◄──► Model
   │
   ▼
Services

Differenza chiave:

MVC: Controller → Model → View (View osservano Model)

MVP: View ↔ Presenter ↔ Model (Presenter media tutto)









<!--
## 🚀 Avvio

### 1. Avvia il server della mappa
La mappa richiede un server HTTP locale. Dalla cartella del progetto:
```bash
python3 -m http.server 8000
```

### 2. Avvia la dashboard (in un secondo terminale)
```bash
python3 dashboard.py
```
-->

La struttura più utile per la realizzazione del file Dashboard è l'utilizzo della logica ...




---

## 🔊 Audio — Compatibilità

Il sistema rileva automaticamente l'ambiente e sceglie il metodo audio più adatto:

| Ambiente | Metodo audio usato |
|---|---|
| Debian / Linux nativo | QSoundEffect → fallback aplay |
| WSL | PowerShell (Media.SoundPlayer) |

Non è necessaria nessuna configurazione manuale.

---

## 🗺️ Funzionalità principali

- **SIMULA EVENTO** — genera un evento sismico casuale (M1.0–M4.8) su una delle tre zone
- **ATTIVA SCIAME** — simula uno sciame sismico su una zona casuale
- **RESET SISTEMA** — riporta tutto allo stato normale e azzera i contatori

### Filtri log
- **GENERALE** — mostra tutti gli eventi
- **CAMPI FLEGREI / VESUVIO / ISCHIA** — apre un pannello flottante con il log della zona selezionata, trascinabile all'interno della finestra

### Stati del sistema
| Stato | Colore | Condizione |
|---|---|---|
| NORMALE | 🟢 Verde | Magnitudo < 2.0 |
| ATTENZIONE | 🟠 Arancione | Magnitudo 2.0–3.4 |
| ALLARME | 🔴 Rosso | Magnitudo ≥ 3.5 |
| SCIAME | 🟠 Arancione scuro | Sciame attivato manualmente |

---

## ⚠️ Note

- Il file `alarm_dec.wav` deve trovarsi nella stessa cartella di `dashboard.py`.
- Le icone nella cartella `icons/` sono opzionali: se assenti, vengono usate emoji di fallback.
- Su WSL il percorso del file `.wav` deve essere sotto `/mnt/c/` per essere accessibile a PowerShell.

---

## 👤 Autore

Progetto sviluppato come simulatore didattico ispirato all'attività dell'**INGV Osservatorio Vesuviano**.

---

## Mappa

Per la realizzazione della mappa è stato necessario creare due file differenti. 
**map.html** necessario per definire le caratteristiche grafiche e logiche della mappa stessa e **map_config** per la configurazione url. Nel progetto di default è stata inserita la modalità "provider: oms" che permette di utilizzare una mappa di openstreetmap, ma nel caso in cui si volesse cambiare è necessario cambiare in ->  "provider: ingv" e nell'apposito "url" dovrà essere inserito l'url desiderato.


## Architettura Mappa

La mappa è un'applicazione web che viene utilizzata all'interno dell'applicazione Pyton/PyQt6 tramite QWebEngineView. Python comunica con essa chiamando funzioni JavaScript tramite runJavaScript(). E' composta da tre layer principali: 
- HTML - Struttura della pagina
- CSS - Stili e responsive design
- JavaScript - Logica interattiva(basata su Leaflet.js)


1. LEAFLET.JS - La libreria cartografica

Leaflet è una libreria JS open-source per mappe interattive. Viene caricata tramite CDN:

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>

Funziona scaricando "tile" (mattonelle di immagine 256x256 px) da un server esterno e componendole in una griglia per formare la mappa. Il provider dei tile(OpenStreetMap,Stadia ecc) viene passato da Python tramite map_config.json.

2. STRUTTURA HTML

<body>
<div id="map"></div>  <!-- Container principale della mappa -->
<div class="legend">  <!-- Legenda dei colori -->
    <h4>Stato Attività</h4>
    <div>...</div>
</div>
</body>

- #map è il contenitore dove Leafket disegnerà la mappa
- La leggenda è posizionata fissa in basso a destra

3. CSS - STILI E RESPONSIVITA'

Tre funzioni gestiscono la scala su schermi diversi:

- markerRadius(stato) — raggio del punto colorato: innerWidth / 160, quindi ~12 px a 1920, ~24 px a 3840, ~40 px a 6400
- fitPadding() — margine quando Leaflet adatta la vista per mostrare tutti e tre i vulcani: innerWidth / 25
- initialZoom() — zoom di partenza: 10 su FullHD, scende a 8 su schermi ≥5000 px per mostrare più contesto geografico

Quando la finestra viene ridimensionata, handleResize() chiama map.invalidateSize() per forzare Leaflet a ricalcolare il layout, poi fitVultuni() per riadattare la vista, e infine aggiorna il raggio di tutti i marker già disegnati con setRadius().


## KAFKA
Apache Kafka è una piattaforma di messaggistica distribuita progettata per gestire grandi quantità di dati in tempo reale.
E' un sistema "publish/subscribe":

- Un'applicazione produce messaggi(Producer)
- Kafka li salva
- Una o più applicazioni consumano quei messaggi(Consumer)

Schema semplificato:

Producer
    |
    v
+---------+
|  Kafka  |
+---------+
    |
    +------> Consumer A
    |
    +------> Consumer B

Il producer pubblica un evento: "Nuovo dato sismico ricevuto" e Kafka lo salva e lo distribuisce a chi è interessato.

Nel nostro caso sarebbe: 

Sensore
   |
   v
 Kafka
   |
   +----> Dashboard
   |
   +----> Sistema allarmi
   |
   +----> Archivio dati

è una comunicazione asincrona.

Nel nostro caso la dashboard non "chiede" dati ma rimane in ascolto:
**wrk.process_messages(...)** 
e quando arriva un nuovo messaggio:
**kernel(msg)** viene eseguito automaticamente.

Kafka è più vicino a una radio che trasmette continuamente dati sismici.

## KAFKA-TOPIC
I messaggi vengono organizzati in topic. 
Nel nostro caso abbiamo: 

wrk.process_messages(
    'waves.flegrei.IV.CSTH',
    on_data=kernel
)

dove waves.flegrei.IV.CSTH è il topic ed è una cosa del tipo: 

Topic: waves.flegrei.IV.CSTH

Messaggio 1
Messaggio 2
Messaggio 3
...

Ogni volta che arriva un nuovo messaggio sul topic, Kafka lo rende disponibile ai consumer.

## KAFKA- BROKER
Kafka gira su uno o più server chiamati broker. 
Ad esempio nel codice abbiamo:

wrk.kafka_connect(
    ['kafkacluster.int.ov.ingv.it:9095']
)
significa che è una situazione del tipo: "Connettiti al broker Kafka che si trova all'indirizzo kafkacluster.int.ov.ingv.it sulla porta 9095.

Lo schema sarebbe:

Tua Applicazione
       |
       |
       v
kafkacluster.int.ov.ingv.it:9095
       |
       v
     Kafka

## PRODUCER-CONSUMER
- Producer: invia dati a Kafka ad esempio: 

producer.send(
    "waves.flegrei.IV.CSTH",
    valore
)

- Consumer: legge i dati da Kafka ad esempio:

wrk.process_messages(
    'waves.flegrei.IV.CSTH',
    on_data=kernel
) 
sto creando un consumer

**Cosa succede nella mia applicazione quando eseguo wrk.kafka_connect(...)?**
Avviene:
1. Apertura della connessione TCP al broker.
2. Negoziazione del protocollo Kafka.
3. Recupero dei metadati del cluster.
4. Preparazione del consumer.

Dopo: wrk.process_messages(...) fa qualcosa come:

Attendi messaggio
      |
      v
Ricevuto?
      |
     SI
      |
      v
Esegui callback kernel()
      |
      v
Attendi prossimo messaggio

Il callback kernel: 

def kernel(msg: Message):
    print(msg.value)

ogni messaggio ricevuto genera: 
Kafka --> process_messages()
             |
             v
         kernel(msg)

quindi: print(msg.value) stampa il contenuto ricevuto 

## OFFSET 

Kafka mantiene un indice chiamato offset.
Ad esempio:
Topic

Offset 0 -> msg A
Offset 1 -> msg B
Offset 2 -> msg C
Offset 3 -> msg D

Quando il consumer legge:
A
B
C

Kafka memorizza:
Ultimo offset letto = 2
Alla riconnessione riparte da lì.

## GRUPPI
Più consumer possono lavorare insieme se appartengono allo stesso gruppo.
Topic
   |
   +--> Consumer 1
   |
   +--> Consumer 2

ad esempio: group_id = "mygroup" e Kafka divide il lavoro.

Se appartengono a gruppi diversi: 
groupA
groupB

entrambi ricevono tutti i messaggi.

Nel mio caso la GUI deve continuare a rispondere mentre il consumer rimane in ascolto continuo. Per questo motivo normalmente si usa:

Thread GUI (Qt)
        +
Thread Kafka

dove:
Thread Kafka-> riceve i messaggi 
Thread Qt-> aggiorna l'interfaccia,mappe,grafici,audio
e i due comunicano tramite segnali Qt(pyqtSignal).

## Struttura con kafka
Kafka
 |
 |
Controller.on_kafka_message()
 |
 |
model.add_log()
model.status=
 |
 |
View aggiornata automaticamente


## Flusso attuale dei thread

MAIN THREAD (GUI)
├── start_background_server() → Thread separato (daemon)
├── kafka_thread.start() → Avvia thread Kafka
├── app.exec() → Loop eventi Qt
│   ├── Gestisce click bottoni (simulate_event, reset, etc.)
│   ├── Riceve segnali da Kafka via pyqtSignal
│   └── Aggiorna UI
│
KAFKA THREAD
├── run() → Eseguito nel thread separato
├── kafka_connect() → Connessione al broker
├── process_messages() → Loop bloccante di ricezione
│   ├── Riceve messaggio
│   ├── on_message() → Emette segnale
│   └── [continua a ricevere]
│
BACKGROUND THREAD (HTTP Server)
├── avvia_server() → Server HTTP in background
└── [sempre attivo]


Ci sta una struttura a due thread principali:
1. Thread principale Qt (GUI thread / Main Thread)
2. Thread Kafka dedicato (QThread)

L'idea è: la GUI non deve mai bloccarsi mentre Kafka aspetta messaggi. Quindi sposti il consumer Kafka in un thread separato e comunichi con la GUI tramite pyqtSignal.

1) Quando si avvia l'applicazione PyQt nasce automaticamente il main thread:

MAIN THREAD
│
├── QApplication
│
├── Window (View)
│
├── SystemController
│
└── Model

Questo thread gestisce:

-finestre
-pulsanti
-mappe
-aggiornamento grafico
-eventi utente

2) Creazione del thread Kafka -> gira in background e ascolta continuamente i messaggi Kafka senza bloccare la GUI


Kafka Thread
      |
      |
      | signal
      |
      v
GUI Thread

più nello specifico: 

KafkaWorker
     |
     |
emit(msg)
     |
     |
     v
SystemController.on_kafka_message()

*on_kafka_message()* viene eseguito nel thread del controller e non nel thread Kafka. Questo è il meccanismo thread-safe di Qt.


## SERVERS - Struttura

servers/
│
├── config.json              # scelta globale
│
├── serverkafka/
│   ├── kafka.py
│   └── thread.py
│
├── serenade/
│   ├── serenade.py
│   └── thread.py
│
└── servermap/
    ├── map_config.json
    ├── map.html
    └── server.py

    
Come funziona:
1. serenade.py - SerenadeWorker(QThread) che ogni n secondi fa un GET a Serenade, confronta gli event_id già visti e emette solo i nuovi eventi tramite signal (proprio come KafkaWorker)

2. parser.py - funzione parse_evento_serenade(event_id, event_data) traduce il json di Serenade nello stesso dict che già usa on_kafka_message nel controller, così non è necessario toccare il controller.

Le zone supportate dall'URL sono flegrei,vesuvio,ischia - il worker le interroga tutte e tre in sequenza 








 












