# Das Konsolidierte Projekt-Manifest ("Die Bibel")

**Status:** Aktuell (inkl. implementierter Quota- & Idempotenz-Infrastruktur)
**An das Team & LLM:** Dies ist die **einzige "Source of Truth"** für unsere Projekt-Architektur, technische Implementierung und Entwicklungsprinzipien.

## 1. Kernphilosophie (Unser "Warum")

Das oberste Ziel ist ein **zukunftssicheres, modulares und wartbares** System. Wir erreichen dies durch zwei Kernprinzipien:
1.  **Separation of Concerns (SoC):** Jede Komponente hat *eine* klar definierte Aufgabe und Verantwortung.
2.  **DRY (Don't Repeat Yourself):** Logik wird zentralisiert und nicht dupliziert.

---

## 2. Die 5-Schichten-Architektur (Unser "Was")

Unser Projekt ist in 5 logische Schichten unterteilt. Eine Schicht kommuniziert idealerweise *nur* mit der Schicht direkt unter ihr.

### Schicht 5: Präsentation & Orchestrierung (Das "Gesicht" & "Dirigent")
* **Zweck:** Dem Benutzer Daten anzeigen (UI), APIs bereitstellen oder automatisierte Jobs starten.
* **Komponenten:**
    * `scripts/update_all_assets.py`: Startet den Rohdaten-Import. Initialisiert `PipelineRun` und injiziert Services (z.B. `QuotaManager`).
    * `scripts/run_metrics_update.py`: Startet die Metrik-Berechnung.
    * `api/main.py`: FastAPI-Endpunkte, inkl. `/freshness`-Endpoint für Stale-Data-Alerting.
* **Regeln:**
    * Spricht *nur* mit Schicht 3 (Business-Logik) oder Schicht 4 (Analyse).
    * Spricht **niemals** direkt mit der Datenbank (L2) oder den Providern (L1).
    * Verantwortlich für das **Error Boundary** auf oberster Ebene (fängt Exceptions, schließt Pipeline-Runs ab).

### Schicht 4: Analyse & API (Die "Experten")
* **Zweck:** Komplexe, abgeleitete Berechnungen durchführen (Metriken, Analysen).
* **Komponenten:**
    * `portfolio_tool/analytics/calculator.py`
    * `class MetricsCalculator`
* **Regeln:**
    * Liest Rohdaten *nur* aus der Datenbank (L2).
    * Berechnet abgeleitete Metriken (z.B. `market_cap` aus `price.close * shares`).
    * Schreibt die berechneten Metriken zurück in die Datenbank (L2).
    * Ruft **niemals** Provider (L1) auf.

### Schicht 3: Business-Logik (Das "Gehirn")
* **Zweck:** Den Datenfluss orchestrieren. Entscheiden, *was* wann von *wem* geholt und *wie* es in die DB geladen wird.
* **Komponenten:**
    * `portfolio_tool/data_manager.py` (`class DataManager`)
* **Regeln:**
    * **Einzige** Schicht, die sowohl mit Providern (L1) als auch mit der Datenbank (L2) sprechen darf.
    * **Selbstheilung:** Enthält die "Delta-Logik" (z.B. `start_date = last_entry` statt `last_entry + 1`), um Lücken zu schließen.
    * **Idempotenz:** Führt Upserts (`INSERT ... ON CONFLICT DO UPDATE`) via `_perform_upsert` aus, um Duplikate zu verhindern.
    * Ist "agnostisch" gegenüber den Providern.

### Schicht 2: Datenbank (Das "Fundament")
* **Zweck:** Die "Source of Truth" sein; die Datenstruktur definieren.
* **Komponenten:**
    * `portfolio_tool/database_setup.py` (SQLAlchemy-Modelle, `Base`)
    * `alembic/` (Migrationen)
* **Schlüsselmodelle (Business Daten):**
    * `Asset`: `ticker`, `name`, `sector`, `industry`.
    * `DailyPrice`: Rohdaten (OHLCV) + Abgeleitet (`market_cap`). Constraint: `UNIQUE(asset_id, date)`.
    * `SharesHistory`, `Fundamentals`, `QuarterlyEarnings`.
    * `FinancialStatement`: Rohdaten (Income/Balance/Cash Flow).
* **Schlüsselmodelle (Metadaten & Observability):**
    * `AssetFetchMetadata`: Speichert `last_earnings_fetch_time` etc. für Snapshot-Guards.
    * `PipelineRun`: Protokolliert jeden Skript-Lauf (`id`, `status`, `start_time`, `git_commit`).
    * `ApiCallLog`: Protokolliert *jeden* API-Aufruf (`pipeline_run_id`, `endpoint`, `success`).
    * `ApiQuota`: Verfolgt atomar den Quota-Verbrauch (`bucket_key`, `calls_consumed`).

### Schicht 1: Daten-Akquise (Die "Lieferanten")
* **Zweck:** Daten von externen APIs holen und in interne DTOs übersetzen.
* **Komponenten:**
    * `portfolio_tool/provider_models.py` (DTOs).
    * `portfolio_tool/providers/base.py` (Interface `DataProviderInterface`).
    * `portfolio_tool/providers/yfinance_provider.py` (Implementierung).
    * `portfolio_tool/providers/utils.py` (Enthält `SimpleRateLimiter`).
* **Regeln:**
    * Provider sind "dumm": Sie wissen *nichts* über L2 oder L3.
    * Nutzen injizierte Services (`DatabaseQuotaManager`) zur Protokollierung, ohne deren Interna zu kennen.

---

## 3. Goldene Regeln (Unser "Wie")

### Regel I: Provider-Abstraktion (Adapter Pattern)
Sicherstellung der Austauschbarkeit von Datenquellen.
1.  **Vertrag (L1):** `DataProviderInterface` definiert Methoden (`get_daily_prices`).
2.  **Sprache (L1):** DTOs (`ProviderPriceData`) standardisieren den Rückgabewert.
3.  **Agnostik (L3):** Der `DataManager` nutzt nur das Interface, injiziert per Dependency Injection.

### Regel II: Rohdaten vs. Abgeleitete Daten
Strikte Trennung von Herkunft und Verarbeitung.
1.  **Rohdaten-Workflow:** `update_all_assets.py` → `DataManager` → `Provider` → DB (Speichert z.B. `close`).
2.  **Metriken-Workflow:** `run_metrics_update.py` → `MetricsCalculator` → DB (Liest `close`, schreibt `market_cap`).

---

## 4. API-Management & Observability (Implementiert)

Wir nutzen ein robustes System aus lokaler Begrenzung und zentraler Quota-Verwaltung.

### 4.1. Rate Limiting (Frequenz & Volumen)
* **Frequenz (Lokal):** Der `SimpleRateLimiter` (in `utils.py`) sorgt dafür, dass wir technische API-Limits (z.B. "max 5 requests/sec") einhalten (`wait_for_slot()`).
* **Volumen (Zentral - DB-gestützt):**
    * Der `DatabaseQuotaManager` (Service) prüft vor jedem Call die `ApiQuota`-Tabelle.
    * Erlaubt atomares Zählen (`bucket_key` z.B. "yfinance_daily").
    * Blockiert Aufrufe systemweit, wenn das Tageslimit erreicht ist.

### 4.2. Abruf-Strategien
1.  **Delta-Abrufe (Zeitreihen):**
    * Prüfung: `func.max(DailyPrice.date)` in der DB.
    * Self-Healing: Startdatum = Letztes DB-Datum (Überschreiben zur Korrektur).
    * Sicherheit: `ON CONFLICT DO UPDATE` in der DB verhindert Duplikate.
2.  **Snapshot-Abrufe (Stammdaten):**
    * Guard: Prüfung der `AssetFetchMetadata` gegen konfigurierte Intervalle (z.B. 30 Tage).

### 4.3. Observability
* Jeder Lauf hat eine `pipeline_run_id`.
* Jeder externe Call erzeugt einen `ApiCallLog`-Eintrag.
* Ein `/freshness`-Endpoint (FastAPI) erlaubt Monitoring des Datenalters.

---

## 5. Entwicklungs-Workflow (7/9-Schritte-Muster)

Bei neuen Datenpunkten:
1.  **DB-Modell (L2):** SQLAlchemy-Klasse definieren/erweitern.
2.  **Migration (L2):** `alembic revision --autogenerate` && `upgrade head`.
3.  **DTO (L1):** `@dataclass` in `provider_models.py` anpassen.
4.  **Interface (L1):** Methode in `base.py` hinzufügen.
5.  **Provider (L1):** Implementierung in `yfinance_provider.py` (inkl. Quota-Checks).
6.  **Manager (L3):** `update_...`-Methode mit Delta/Guard-Logik und `_perform_upsert`.
7.  **Orchestrator (L5):** Aufruf in `update_all_assets.py`.
8.  *(Optional)* **Calculator (L4):** Berechnungslogik für Metriken.
9.  *(Optional)* **Metrik-Job (L5):** Aufruf in `run_metrics_update.py`.

---

## 6. Erweiterbarkeit (Polyglot Persistence Strategie)

**Ziel:** Start mit PostgreSQL, spätere Erweiterung ohne Rewrites.

1.  **DB-Agnostik:** Nutzung von `DATABASE_URL` und SQLAlchemy. Keine SQLite-Spezifika.
2.  **Separation:** Raw (Postgres) → Compute (Python) → Serve (Postgres/API).
3.  **Zukunftspfad:**
    * *Zeitreihen-Scale:* TimescaleDB (via Docker/Extension).
    * *Analytics:* ClickHouse oder Cloud Warehouse.
    * *ML:* Feature Store (Feast) auf Basis von Parquet/S3.
4.  **Prinzip:** Wir binden neue Stores nur an, wenn der Workload es erfordert. Die Architektur (L3 Manager) kapselt den Speicherort weg.

---

## 7. Roadmap (Offene Nächste Schritte)

Nachdem die Infrastruktur (Quota, Idempotenz, Observability) steht, folgt nun:

**Kurzfristig:**
* **Metadaten-Anreicherung:** `pipeline_run` um Git Commit Hash und Config Hash erweitern (für volle Reproduzierbarkeit).
* **Testing:** Contract Tests / Recorded Fixtures (z.B. mit `vcrpy`) für die Provider erstellen.
* **Resilience:** Basic Retry/Backoff + Circuit-Breaker Muster für Provider-Fehler integrieren.

**Mittelfristig:**
* **Performance:** Partitioning (Postgres/Timescale) für große Zeitreihen-Tabellen.
* **Data Quality:** Integration von "Great Expectations" für Checks nach dem Import.
* **Scheduling:** Umbau der Skripte auf einen echten Orchestrator (Prefect/Dagster) oder erweitertes Cron-Scheduling (Daily/Weekly Rotation).