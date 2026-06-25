import threading
import http.server
import os

def avvia_server(porta=8000):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # silenzia i log
    with http.server.HTTPServer(("127.0.0.1", porta), handler) as httpd:
        httpd.serve_forever()

def start_background_server(porta=8000):
    try:
        thread = threading.Thread(target=avvia_server, args=(porta,), daemon=True)
        thread.start()
        print("SERVER IN ASCOLTO SU 8000")

    except Exception as e:
        print("ERRORE SERVER:", e)