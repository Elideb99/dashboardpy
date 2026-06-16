import json
import os

class MapService:
    def __init__(self):
        self.webview = None
        self.map_ready = False # flage che indica se la mappa è caricata e pronta per ricevere i comandi 
        self.pending_updates = [] # lista per gli aggiornamenti in sospeso
        self.current_map_provider = None # memorizza il provider della mappa
    
    def set_webview(self, webview):
        self.webview = webview
    
    def set_ready(self, ready):
        self.map_ready = ready
    
    def load_configuration(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "map_config.json") # costruisce il percorso del file
        try:
            with open(config_path, "r", encoding="utf-8") as f: # apre il file json in modalità lettura
                return json.load(f)
        except Exception as e:
            print(f"Errore config mappa: {e}")
            return None
    
    def apply_config(self):  # carica la configurazione 
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