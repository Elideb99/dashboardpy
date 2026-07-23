# Crea il thread Qt e il worker Kafka.
from PyQt6.QtCore import QThread
from servers.serverkafka.kafka import KafkaWorker

kafka_thread = QThread()
kafka_worker = KafkaWorker()

# Sposta il worker nel thread dedicato.
kafka_worker.moveToThread(kafka_thread)

# Avvia il worker quando il thread parte.
kafka_thread.started.connect(kafka_worker.run)
kafka_thread.start()