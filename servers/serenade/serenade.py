
import httpx
import asyncio
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class SerenadeWorker(QObject):

    message_received = pyqtSignal(object)
    error_occurred   = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.url     = config["base_url"] + config["endpoint"]
        self.params  = config["params"]
        self.refresh = config["refresh"]
        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    #  Slot chiamato da QThread.started                                    #
    # ------------------------------------------------------------------ #
    def run(self):
        print("SERENADE THREAD START:", threading.current_thread().name)
        self._running = True

        # Crea un event loop dedicato per questo thread
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

    # ------------------------------------------------------------------ #
    #  Loop asincrono principale                                           #
    # ------------------------------------------------------------------ #
    async def _poll_loop(self):
        # Limita le connessioni simultanee (1 è sufficiente per il polling)
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=2.0),
            limits=limits,
        ) as client:

            while self._running:
                await self._fetch(client)

                # Sleep interrompibile: controlla _running ogni secondo
                for _ in range(self.refresh):
                    if not self._running:
                        return
                    await asyncio.sleep(1)   # <-- NON blocca il thread

    # ------------------------------------------------------------------ #
    #  Singola richiesta                                                   #
    # ------------------------------------------------------------------ #
    async def _fetch(self, client: httpx.AsyncClient):
        try:
            r = await client.get(self.url, params=self.params)
            r.raise_for_status()

            # .json() di httpx è sincrono ma veloce; per payload enormi
            # si può spostare in un executor:
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

    # ------------------------------------------------------------------ #
    #  Stop thread-safe                                                    #
    # ------------------------------------------------------------------ #
    def stop(self):

        self._running = False
        print("STOP SERENADE WORKER")
        if self._loop and self._task:
         self._loop.call_soon_threadsafe(self._task.cancel)
    