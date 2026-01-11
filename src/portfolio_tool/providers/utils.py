import time
from collections import deque

class SimpleRateLimiter:
    """
    Ein einfacher Rate-Limiter, der sicherstellt, dass nicht mehr als
    'per_minute'-Aufrufe in einem 60-Sekunden-Fenster erfolgen.
    (Basierend auf FIN_API_Runbook.md, Abschnitt 5.1)
    """
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.window_seconds = 60
        # deque speichert die Zeitstempel der Aufrufe im Fenster
        self.timestamps = deque()

    def wait_for_slot(self):
        """
        Blockiert, bis ein Slot für einen Aufruf verfügbar ist.
        """
        now = time.time()

        # 1. Entferne alte Zeitstempel (älter als 'window_seconds')
        while self.timestamps and (now - self.timestamps[0] > self.window_seconds):
            self.timestamps.popleft()

        # 2. Prüfen, ob das Fenster voll ist
        if len(self.timestamps) < self.per_minute:
            # Slot ist frei
            self.timestamps.append(now)
            return

        # 3. Fenster ist voll. Wir müssen warten.
        # Warte, bis der älteste Aufruf aus dem Fenster fällt.
        oldest_call_time = self.timestamps[0]
        time_to_wait = (oldest_call_time + self.window_seconds) - now
        
        if time_to_wait > 0:
            # (+ 0.02s Puffer, um Rundungsfehler zu vermeiden)
            time.sleep(time_to_wait + 0.02)
        
        # Rekursiver Aufruf, um den Slot erneut zu prüfen (falls mehrere Threads warten)
        # In unserem Single-Thread-Skript könnten wir auch einfach 
        # self.timestamps.popleft() und self.timestamps.append(time.time()) machen.
        # Aber die rekursive Variante ist sicherer.
        self.wait_for_slot()