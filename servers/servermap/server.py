import threading
import http.server
import os

def avvia_server(porta=8000):
    # serve i file dalla cartella dove si trova questo script (es. l'HTML della mappa)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # silenzia i log
    with http.server.HTTPServer(("127.0.0.1", porta), handler) as httpd:
        httpd.serve_forever()   # bloccante: per questo va lanciato in un thread separato

def start_background_server(porta=8000):
    # avvia il server in un thread daemon: non blocca l'app e si chiude da solo alla chiusura del programma
    try:
        thread = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
        thread.start()
        print("SERVER IN ASCOLTO SU 8000")  

    except Exception as e:
        print("ERRORE SERVER:", e)