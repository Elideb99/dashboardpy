import json
import os

class MapService:
    def __init__(self):
        self.webview = None
        self.map_ready = False # flag che indica se la mappa è caricata e pronta per ricevere i comandi 
        self.pending_updates = [] # lista per gli aggiornamenti in sospeso
        self.current_map_provider = None # memorizza il provider della mappa
    
    def set_webview(self, webview):
        self.webview = webview
    
    def set_ready(self, ready):
        self.map_ready = ready


    def load_configuration(self):
     # Percorso relativo dalla posizione del file corrente
     current_file = os.path.abspath(__file__)
     current_dir = os.path.dirname(current_file)
    
     # Vai a servers/servermap/ (risali di un livello)
     config_path = os.path.join(current_dir, "..", "servers", "servermap", "map_config.json")
     config_path = os.path.normpath(config_path)  # Normalizza il percorso
        
     try:
        with open(config_path, "r", encoding="utf-8") as f:
            print("✅ Config caricata con successo!")
            return json.load(f)
     except Exception as e:
        print(f"Errore config mappa: {e}")
        return None
    
    def apply_config(self):  # carica la configurazione e imposta il tile layer via JS
        config = self.load_configuration()
        if not config:
            return
        provider = config.get("provider", "osm") # ottiene il provider
        self.current_map_provider = provider
        layer = config["tile_layers"][provider] # memorizza il provider scelto 
        min_zoom = layer.get("minZoom", 0) #ottiene i dettagli 
        max_zoom = layer.get("maxZoom", 20)
        js = (f'setBaseMap("{layer["url"]}", "{layer["attribution"]}", ' # costruisce una stringa di codice JS che chiama setBaseMap()
              f'{min_zoom}, {max_zoom});')
        self.webview.page().runJavaScript(js)
    
    def update_vulcano(self, zona, stato, magnitudo=None):
        # via "diretta": usata solo quando la mappa è già pronta (nessun controllo typeof lato JS, a differenza di _update_safe)
        if self.map_ready:
            if magnitudo is not None:
                self.webview.page().runJavaScript( # se la mappa è pronta per ricevere i comandi chiama la funzion JS
                    f'aggiornaStatoVulcano("{zona}", "{stato}", {magnitudo})'
                )
            else:
                self.webview.page().runJavaScript(
                    f'aggiornaStatoVulcano("{zona}", "{stato}")'
                )
        else:
            self.pending_updates.append((zona, stato, magnitudo)) # se non pronta accoda l'aggionramento per essere processato
    
    def queue_update(self, zona, stato, magnitudo=None): # aggiunge un aggiornamento in coda
        self.pending_updates.append((zona, stato, magnitudo))
    
    def process_pending(self):
        if not self.map_ready or not self.pending_updates:
            return # se la mappa non è pronta esce la lista che già ci stava
        latest_updates = {} # crea un dizionario per memorizzare solo l'ultimo aggiornamento
        for zona, stato, magnitudo in self.pending_updates:
            latest_updates[zona] = (stato, magnitudo) # se ci sono più aggiornamenti viene mantenuto solo l'ultimo
        self.pending_updates.clear() # evita aggiornamenti ridondanti e svuota la coda
        for zona, (stato, magnitudo) in latest_updates.items():
            self._update_safe(zona, stato, magnitudo)
    
    def _update_safe(self, zona, stato, magnitudo=None):
        # versione difensiva di update_vulcano: controlla lato JS che la funzione esista prima di chiamarla
        if not self.webview:
            return
        try: # controlla se la funzione aggiornaStatoVulcano esiste e la chiama con 3 parametri
            if magnitudo is not None:
                js_code = (f'if(typeof aggiornaStatoVulcano !== "undefined") '
                           f'aggiornaStatoVulcano("{zona}", "{stato}", {magnitudo});')
            else:
                js_code = (f'if(typeof aggiornaStatoVulcano !== "undefined") '
                           f'aggiornaStatoVulcano("{zona}", "{stato}");')
            self.webview.page().runJavaScript(js_code) # esegue il codice JS nella webview
        except Exception as e:
            print(f"Errore aggiornamento mappa: {e}")
    
    

    def zoom_to_vulcano(self, zona): # deve essere definita nella pagina HTML
        self.webview.page().runJavaScript(f'zoomToVulcano("{zona}");')
    
    def zoom_to_all(self): # esegue JS per zoomare su tutti i vulcani
        self.webview.page().runJavaScript('zoomToAll();')
    
    def refresh_view(self): # se la mappa esegue JS per aggiornare la visualizzazione
        if self.map_ready:
            self.webview.page().runJavaScript("""
                if (typeof refreshMapView !== 'undefined') {
                    refreshMapView();
                } else if (typeof map !== 'undefined' && map) {
                    setTimeout(function() { map.invalidateSize(); }, 100);
                }
            """)


    def add_eventi_batch(self, eventi: list):
     """Passa tutti gli eventi in una sola chiamata JS."""
     if not self.map_ready or not self.webview:
        return
     js = f'aggiungiEventiBatch({json.dumps(eventi)});'
     self.webview.page().runJavaScript(js)

    def clear_eventi(self):
     if self.map_ready and self.webview:
        self.webview.page().runJavaScript('clearEventi();')
    
    def upsert_evento(self, chiave: str, lat, lng, mag, data, qualita, area):
     """Aggiorna o aggiunge un solo pallino sulla mappa, senza ridisegnare tutto.
     Fondamentale con flussi Kafka ad alta frequenza."""
     if not self.map_ready or not self.webview:
        return
     args = json.dumps([chiave, lat, lng, mag, data, qualita, area])
     # "...{args}" spacchetta l'array JSON come lista di argomenti posizionali per upsertEvento(...)
     js = f'if (typeof upsertEvento !== "undefined") upsertEvento(...{args});'
     self.webview.page().runJavaScript(js)

    def replay_sciame(self, eventi: list, intervallo_ms=400):
     if not self.map_ready or not self.webview:
        return
     
     js = f'replaySciame({json.dumps(eventi)}, {intervallo_ms});'
     self.webview.page().runJavaScript(js)