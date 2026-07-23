import httpx
import asyncio
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class SerenadeWorker(QObject):

    message_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    # Inizializza il worker e carica la configurazione del servizio Serenade.
    def __init__(self, config):
        super().__init__()
        self.url = config["base_url"] + config["endpoint"]
        self.params = config["params"]
        self.refresh = config["refresh"]
        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None

    # Avvia il worker creando un event loop dedicato al thread.
    def run(self):
        print("SERENADE THREAD START:", threading.current_thread().name)
        self._running = True
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._task = self._loop.create_task(self._poll_loop())
            self._loop.run_until_complete(self._poll_loop())
        except asyncio.CancelledError:
            pass
        finally:
            self._loop.close()
            print("SERENADE THREAD STOPPED")

    # Esegue il polling periodico del servizio Serenade.
    async def _poll_loop(self):
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=2.0),
            limits=limits,
        ) as client:
            while self._running:
                await self._fetch(client)
                for _ in range(self.refresh):
                    if not self._running:
                        return
                    await asyncio.sleep(1)

    # Invia una richiesta HTTP e pubblica gli eventi ricevuti.
    async def _fetch(self, client: httpx.AsyncClient):
        try:
            r = await client.get(self.url, params=self.params)
            r.raise_for_status()
            eventi = r.json()
            self.message_received.emit(eventi)
        except httpx.TimeoutException as e:
            msg = f"Timeout Serenade: {e}"
            print(msg)
            self.error_occurred.emit(msg)
        except httpx.HTTPStatusError as e:
            msg = f"HTTP {e.response.status_code}: {e.request.url}"
            print(msg)
            self.error_occurred.emit(msg)
        except Exception as e:
            msg = f"Errore Serenade: {e}"
            print(msg)
            self.error_occurred.emit(msg)

    # Arresta il worker in modo sicuro.
    def stop(self):
        self._running = False
        print("STOP SERENADE WORKER")
        if self._loop and self._task:
            self._loop.call_soon_threadsafe(self._task.cancel)