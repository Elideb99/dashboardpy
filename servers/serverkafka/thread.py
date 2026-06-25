from PyQt6.QtCore import QThread
from servers.serverkafka.kafka import KafkaWorker

kafka_thread = QThread()
kafka_worker = KafkaWorker()

kafka_worker.moveToThread(kafka_thread)

kafka_thread.started.connect(kafka_worker.run)
kafka_thread.start()
