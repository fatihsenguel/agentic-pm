# 🏗️ PROJECT CONTEXT: FinBro / Agentic Finance (Production Build)

## 1. Executive Summary

**FinBro** ist ein institutionelles Multi-Agenten-System für Portfoliomanagement. Es verbindet **LLM-basierte Analyse** (Macro, Sentiment) mit **deterministischer Ausführung** (Rebalancing, Risk Checks).

**Aktueller Status:** Transition von "Demo MVP" (Phase 5) zu "Production Ready" (Phase 6).

---

## 2. Core Design Principles (Strict Adherence Required)

Jeder neue Code **muss** diesen Prinzipien folgen:

1. **Separation of Concerns (SoC):**
* `DataManager`: Nur CRUD/DB-Ops.
* `MetricsCalculator`: Nur Mathe.
* `Provider`: Nur API-Kommunikation.
* `Tools`: Nur das Interface für den Agenten.


2. **Hot Potato Principle:**
* **LLMs erhalten NIEMALS Rohdaten** (keine CSV-Dumps).
* Schichten aggregieren Daten. (DB -> Calculator -> Tool -> Agent).
* *Beispiel:* Agent erhält `{return: "13.6%", vol: "12%"}`, keine Liste von 1000 Preisen.


3. **Idempotent Operations:**
* Alle DB-Writes nutzen `ON CONFLICT UPDATE`.
* Safe to retry. Keine Duplikate.


4. **Provider Abstraction:**
* Interfaces (z.B. `DataProviderInterface`) entkoppeln die Logik von der Quelle (YFinance vs. Bloomberg).


5. **Agent-Ready Responses:**
* Tools geben strukturierte Dictionaries/DTOs zurück (Success bool, Data, Metadata, Error).


6. **Session Isolation:**
* `DataManager` und `QuotaManager` nutzen getrennte DB-Sessions, um SQLite Locking zu verhindern.



---

## 3. System Architecture & File Structure

### 📂 `src/portfolio_tool` (The Engine - Pure Python/SQL)

Hier liegt die Geschäftslogik. Keine LLMs, reine Funktion.

* **`data_manager.py`**: Zentraler Singleton für DB-Zugriffe. Handhabt Assets, Prices und Macro Data.
* **`database_setup.py`**: SQLAlchemy Models (`Asset`, `Price`, `MacroIndicator`).
* **`providers/yfinance_provider.py`**: Fetching Logic mit Rate Limiting & Quota Management.
* **`tools/rebalance_tools.py`**: **CRITICAL**. Reine Mathematik für Rebalancing. Deterministisch. Enthält Logik für Drift, Trade-Generierung und Steuerschätzung.
* **`tools/macro_tools.py`**: Logik für VIX und Yield Curve Analyse (SMA200 Trend Check implementiert).
* **`rag/`**: (In Dev) Gerüst für Embeddings und PDF-Scraper (Fed Minutes).

### 📂 `src/agents` (The Brain - LangChain/LangGraph)

Hier leben die Agenten, die die Tools nutzen.

* **`risk_manager_agent.py`**: Der Supervisor/Router. (Aktuell: Mocked/Regex. Ziel: LLM-Router).
* **`data_agent.py`**: Interface zum DataManager. Holt Kurse/Metriken.
* **`macro_agent.py`**: Nutzt Macro Tools. Entscheidet über Market Regime (Neutral/Bearish/Bullish).
* **`rebalance_agent.py`**: Wrapper um die Rebalance Tools. Führt keine Berechnungen selbst durch (Compliance!).
* **`multi_agent_cli.py`**: (Legacy Demo) Terminal UI mit `rich`. Nutzt noch Keyword-Routing.

### 📂 `data/` (Storage)

* **`portfolio.db`**: SQLite Datenbank. Verwaltet via Alembic.
* **Alembic Versions**: Schema-Änderungen sind versioniert (siehe `alembic/versions`).

---

## 4. Current State: Demo vs. Production Gaps

| Feature | Implementation im Demo-Code | Ziel für Production (To-Do) |
| --- | --- | --- |
| **Router** | `multi_agent_cli.py` nutzt Regex (`if "price" in input`). | **Smart Router:** `RiskManager` nutzt LLM (`bind_tools` oder JSON-Mode) für semantisches Routing. |
| **Orchestrierung** | Direkte Tool-Calls / If-Else. | **LangGraph:** State Machine mit Nodes/Edges und *Human-in-the-Loop* für Trade-Approvals. |
| **Portfolio** | Hardcoded Dicts (`current_weights = {...}`). | **Database:** Laden aus Tabelle `portfolios` & `positions`. |
| **Observability** | `print()` Statements in der Konsole. | **Tracing:** Nutzung von `Chainlit Steps` oder Custom Tracer, um Token-Verbrauch und Agent-Gedanken zu loggen. |
| **Interface** | CLI (Terminal). | **Web UI:** `app.py` mit Chainlit. |

---

## 5. Roadmap (Immediate Next Steps)

Wir befinden uns am Start von **Phase 6 (Production Hardening)**.

### Priority 1: Observability & Tracing (`src/observability`)

* Erstellen von `tracer.py` und `token_tracker.py`.
* Ziel: Wir müssen sehen, was die Agenten "denken" und was es kostet, bevor wir die Logik komplexer machen.

### Priority 2: Chainlit UI (`app.py`)

* Ersetzen der CLI durch ein Web-Interface.
* Integration des Tracers (Visualisierung der Steps).

### Priority 3: Smart Router (LLM Integration)

* Umbau des `RiskManager` von Regex auf echtes LLM-Entscheiden.
* Einsatz von Pydantic Guardrails, um validen Output sicherzustellen.

### Priority 4: Real Data Integration

* Erweitern des DB-Schemas um User-Portfolios.
* Aktivierung der RAG-Pipeline für echte Fed-Minutes-Analyse.

---

## 6. How to contribute / Code Rules

* **Datenbank-Änderungen:** Immer eine neue Alembic Revision erstellen (`alembic revision --autogenerate`).
* **Neue Tools:** Müssen in `src/portfolio_tool/tools` erstellt werden (Pure Python) und dann im Agenten registriert werden.
* **Testing:** Führe `pytest` aus, bevor Code gepusht wird. Achte besonders auf `test_rebalance.py` (Darf nicht fehlschlagen!).