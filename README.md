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




 












