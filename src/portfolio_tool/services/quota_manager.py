# portfolio_tool/services/quota_manager.py
import sys
database_setup_path = r"E:\\Programming\\Finance_Phase_3\\portfolio_tool\\database_setup.py"

if database_setup_path not in sys.path:
        sys.path.append(database_setup_path)

from portfolio_tool.database_setup import ApiQuota, ApiCallLog, PipelineRun

import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

class DatabaseQuotaManager:
    """
    Verwaltet zentral API-Quotas und loggt Aufrufe in der Datenbank.
    Diese Klasse ist zustandsbehaftet und an einen einzelnen PipelineRun gebunden.
    """
    
    def __init__(self, 
                 session: Session, 
                 pipeline_run_id: int, 
                 provider_name: str, 
                 daily_limit: int):
        
        if not pipeline_run_id:
            raise ValueError("DatabaseQuotaManager erfordert eine gültige pipeline_run_id.")
            
        self.session = session
        self.pipeline_run_id = pipeline_run_id
        self.provider_name = provider_name
        self.daily_limit = daily_limit
        print(f"DEBUG [QuotaManager]: Initialisiert für '{provider_name}', Run ID {pipeline_run_id}, Limit {daily_limit}")

    def _get_current_bucket_key(self) -> str:
        """Erzeugt den eindeutigen Schlüssel für das heutige tägliche Quota-Fenster."""
        today = datetime.date.today()
        return f"daily_{self.provider_name}_{today.strftime('%Y-%m-%d')}"

    def _get_window_start(self) -> datetime.datetime:
        """Gibt den UTC-Startzeitpunkt des aktuellen Tages zurück."""
        return datetime.datetime.now(datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def can_consume_credit(self) -> bool:
        """
        Prüft atomar, ob ein Aufruf getätigt werden darf und verbraucht ein Credit.
        Dies ist der "atomisch prüfen + konsumieren"-Schritt.
        
        Führt einen 'SELECT ... FOR UPDATE' aus, um die Zeile zu sperren,
        den Zähler zu prüfen, ihn zu erhöhen und zu committen - alles in
        einer Transaktion.
        """
        bucket_key = self._get_current_bucket_key()
        
        try:
            # Wir starten eine "nested" Transaktion. Wenn der aufrufende Code
            # (z.B. der DataManager) bereits in einer Transaktion ist, wird
            # ein Savepoint erstellt.
            with self.session.begin_nested():
                # 1. Atomar die Quota-Zeile holen und sperren
                stmt = (
                    select(ApiQuota)
                    .where(ApiQuota.bucket_key == bucket_key)
                    .with_for_update() # WICHTIG: Sperrt die Zeile bis zum Transaktionsende
                )
                quota = self.session.scalars(stmt).first()
                
                # 2. Quota-Eintrag erstellen, falls er nicht existiert
                if not quota:
                    print(f"DEBUG [QuotaManager]: Erstelle neuen Quota-Bucket: {bucket_key}")
                    quota = ApiQuota(
                        provider_name=self.provider_name,
                        bucket_key=bucket_key,
                        calls_consumed=0,
                        window_start_time=self._get_window_start()
                    )
                    self.session.add(quota)

                # 3. Prüfen, ob das Limit erreicht ist
                if quota.calls_consumed < self.daily_limit:
                    # 4. Limit nicht erreicht: Zähler erhöhen und 'True' zurückgeben
                    quota.calls_consumed += 1
                    print(f"DEBUG [QuotaManager]: Credit verbraucht. Neuer Stand für {bucket_key}: {quota.calls_consumed}/{self.daily_limit}")
                    # Die Transaktion wird am Ende des 'with'-Blocks committed
                    return True
                else:
                    # 5. Limit erreicht: Nichts tun, 'False' zurückgeben
                    print(f"WARN [QuotaManager]: Tägliches Limit erreicht für {bucket_key} ({self.daily_limit})")
                    # Die Transaktion wird am Ende des 'with'-Blocks committed (ohne Änderung)
                    # oder zurückgerollt, falls ein Fehler auftritt.
                    return False

        except Exception as e:
            print(f"ERROR [QuotaManager]: Fehler bei der Quota-Prüfung: {e}")
            # Bei einem DB-Fehler (z.B. Deadlock) den Aufruf sicherheitshalber ablehnen
            return False

    def log_api_call(self, 
                     endpoint_name: str, 
                     asset_ticker: str = None, 
                     success: bool = True, 
                     http_status_code: int = None, 
                     error_message: str = None,
                     credits_consumed: int = 1):
        """
        Protokolliert den *Ausgang* eines API-Aufrufs in der ApiCallLog-Tabelle.
        """
        if not success:
            # Wenn der Aufruf fehlschlug, zählen wir ihn nicht gegen das Quota,
            # (das wir bereits in can_consume_credit gebucht haben).
            # ABER: Wir loggen ihn als '0 credits' verbraucht.
            # Dies ist eine Design-Entscheidung: Zählen wir Versuche oder Erfolge?
            # Aktuell zählt can_consume_credit() den *Versuch*.
            # Wir loggen hier das Ergebnis.
            
            # Wenn der Aufruf selbst fehlschlug (z.B. 404, 500),
            # wurde der Credit in can_consume_credit() trotzdem verbraucht.
            # Wir setzen credits_consumed auf 0 nur, wenn die *Quota-Prüfung* fehlschlug.
            pass # Logik siehe unten

        if error_message and len(error_message) > 950: # Kürzen für die DB
            error_message = error_message[:950] + "..."

        log_entry = ApiCallLog(
            pipeline_run_id=self.pipeline_run_id,
            provider_name=self.provider_name,
            endpoint_name=endpoint_name,
            asset_ticker=asset_ticker,
            call_timestamp=func.now(), # Serverseitige Zeit
            http_status_code=http_status_code,
            success=success,
            # Wenn 'success' Falsch ist, setzen wir die verbrauchten Credits auf 0,
            # da der Aufruf (vermutlich) nicht durchging.
            credits_consumed=credits_consumed if success else 0,
            error_message=error_message
        )
        
        try:
            with self.session.begin_nested():
                self.session.add(log_entry)
        except Exception as e:
            print(f"FATAL [QuotaManager]: Logging des API-Aufrufs fehlgeschlagen: {e}")
            # Dies ist ein ernstes Problem, da unser Logging versagt,
            # aber wir sollten den Hauptprozess nicht deswegen abbrechen.