import json
import os
from PyQt6.QtCore import QThread
from servers.serverkafka.kafka import KafkaWorker
from servers.serenade.serenade import SerenadeWorker

def load_config():
    # Ottieni la directory dove si trova questo file (servers/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.json")
    
    print(f"Caricamento config da: {config_path}")  # Debug
    
    with open(config_path) as f:
        return json.load(f)

# def start_data_server():
#     config = load_config()
#     thread = QThread()
    
#     if config["data_source"] == "kafka":
#         print("USO KAFKA")
#         worker = KafkaWorker()
#     elif config["data_source"] == "serenade":
#         print("USO SERENADE")
#         worker = SerenadeWorker(config["serenade"])
#     else:
#         raise Exception("Sorgente dati non valida")
    
#     worker.moveToThread(thread)
#     thread.started.connect(worker.run)
#     thread.start()
    
#     return thread, worker

def start_data_server():
    config = load_config()
    thread = QThread()
    
    if config["data_source"] == "kafka":
        print("USO KAFKA")
        worker = KafkaWorker()
    elif config["data_source"] == "serenade":
        print("USO SERENADE")
        worker = SerenadeWorker(config["serenade"])
    else:
        raise Exception("Sorgente dati non valida")
    
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    # ← NON fare thread.start() qui

    return thread, worker