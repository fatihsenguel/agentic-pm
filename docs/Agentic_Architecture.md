
# Das Konsolidierte AI-Architektur-Manifest ("Die Agentic Bible")

**Status:** Transformation zu Distributed Agentic AI (Multi-Agent & MCP Ready)
**Basierend auf:** *Projektbibel v1 (Legacy)*
**An das Team & AI-Agenten:** Dies ist die **erweiterte "Source of Truth"**. Sie definiert eine Plattform, auf der spezialisierte KI-Agenten kollaborieren.

---

## 1. Kernphilosophie (Unser "Warum")

Wir bauen eine **Agentic Platform**, keine monolithische Applikation.

1. **Separation of Concerns (SoC):** Tools (Fähigkeiten) sind strikt von Agenten (Entscheidungen) getrennt.
2. **Orchestration over Monolith:** Komplexe Aufgaben werden in spezialisierte Sub-Agenten zerlegt (Supervisor Pattern).
3. **Universal Interface:** Unsere Business-Logik ist über Python-Objekte, API und **MCP (Model Context Protocol)** verfügbar.
4. **Idempotenz & Sicherheit:** Agenten dürfen Daten anfordern, aber die Integrität der DB wird durch die Layer 3 Logik (Quota, Upserts) garantiert.

---

## 2. Die 7-Schichten-Architektur (The "Agent Stack")

### Schicht 7: The Agent Swarm (Orchestrierung & Kognition) **[NEU]**

* **Zweck:** Koordination spezialisierter Agenten zur Lösung komplexer Aufgaben.
* **Architektur-Pattern:** Hierarchical Supervisor (z.B. via LangGraph).
* **Die Akteure:**
* **Supervisor Agent:** Der "Router". Nimmt User-Input, plant, delegiert an Sub-Agenten. Hat keine eigenen Tools.
* **Data Scout Agent:** Spezialist für Beschaffung. Nutzt `DataManager` Tools.
* **Analyst Agent:** Spezialist für Bewertung. Nutzt RAG (Texte) und Metrics (Zahlen).
* **Reporter Agent:** Spezialist für Output. Erstellt Excel, PDF oder Charts (Visualisierung).



### Schicht 6: Semantic Layer (Das "Gedächtnis") **[NEU]**

* **Zweck:** Verknüpfung von Hard Facts (SQL) mit Soft Facts (Text).
* **Komponenten:**
* **Vector Store:** ChromaDB (Lokal) / Qdrant.
* **Linker:** Tabelle `DocumentChunk` in SQLite.


* **Funktion:** Ermöglicht RAG (Retrieval Augmented Generation) für Geschäftsberichte und News.

### Schicht 5: Tool Interface & Protocols (Die "Hände") **[TRANSFORMIERT]**

* **Zweck:** Exponiert die Business-Logik (Schicht 3 & 4) standardisiert nach außen.
* **Protokolle:**
1. **Internal Tools:** Pydantic-basierte Funktionen für LangChain/LangGraph.
2. **MCP Server:** Model Context Protocol Server für externe Integration (z.B. Claude Desktop).
3. **Rest API:** FastAPI für Monitoring & Legacy-Integration.



### Schicht 4: Analyse & Reporting (Die "Verarbeitung")

* **Komponenten:**
* `MetricsCalculator`: Berechnet Finanzkennzahlen.
* **[Neu]** `VizGenerator`: Erstellt Plots (Matplotlib/Plotly).
* **[Neu]** `ReportBuilder`: Generiert Excel/PDF Dateien.


* **Regel:** Outputs werden als Dateien oder Daten-Objekte zurückgegeben, nicht nur angezeigt.

### Schicht 3: Business-Logik (Der "Maschinenraum")

* **Status:** Bestehendes Kernstück.
* **Aufgabe:** Orchestriert Datenfluss, Idempotenz (`_perform_upsert`), und Transaktionen.
* **Anpassung:** Methoden liefern strukturierte `UpdateResult`-Objekte statt `None`.

### Schicht 2: Datenbank (Das "Fundament")

* **Status:** SQLite (MVP).
* **Modelle:** `Asset`, `DailyPrice`, `ApiQuota`, `ApiCallLog`.
* **Erweiterung:** `DocumentChunk` für Vektor-Referenzen.

### Schicht 1: Daten-Akquise (Die "Lieferanten")

* **Status:** `YFinanceProvider` mit `DatabaseQuotaManager`.
* **Regel:** "Hard Limits" für API-Calls schützen vor Agenten-Loops.

---

## 3. Goldene Regeln für Multi-Agent-Systeme

### Regel I: Standardisierte Kommunikation (Tool-Output)

Wenn Agent A (Data Scout) ein Tool aufruft, muss der Output so strukturiert sein, dass Agent B (Analyst) ihn versteht.

* **Format:** JSON / Pydantic Objects.
* **Inhalt:** Status, betroffene IDs, Zusammenfassung der Daten (nicht *alle* Rohdaten, um Context Window zu sparen).

### Regel II: State Management (Das "Gedächtnis" des Teams)

Der Supervisor hält den **Global State**.

* `messages`: Chat Historie.
* `data_context`: Welche Ticker wurden bereits geladen?
* `artifacts`: Pfade zu erstellten Excel-Dateien oder Charts.

### Regel III: Human-in-the-Loop

Bevor der **Reporter Agent** eine E-Mail sendet oder eine Datei finalisiert, kann der Supervisor eine Bestätigung vom User einfordern. Dies wird im Graphen als "Interrupt" modelliert.

---

## 4. Implementierungs-Roadmap

### Phase 1: Tool-ification (Basis schaffen)

* **Refactoring:** `DataManager` Methoden auf Rückgabewerte umstellen.
* **MCP-Vorbereitung:** Tools so kapseln, dass sie sowohl von LangChain als auch einem MCP-Server genutzt werden können.

### Phase 2: Semantic & Data Layer

* **DB-Upgrade:** `DocumentChunk` Tabelle anlegen.
* **Ingestion:** Skript für RAG-Loading (PDF/Text -> ChromaDB).

### Phase 3: Single-Agent MVP

* Ein "Generalist Agent", der Tools nutzen kann (um zu testen, ob die Tools funktionieren).

### Phase 4: Multi-Agent Orchestration

* Aufbau des Supervisors mit LangGraph.
* Aufteilung in spezialisierte Sub-Agenten (Scout, Analyst, Reporter).
* Integration der "Excel/Viz"-Fähigkeiten in Schicht 4.

---

## 5. Vision: Der "AI Architect Showcase"

Das Ziel ist ein System, bei dem der User sagt:

> *"Analysiere mir das Portfolio von SAP und Siemens, vergleiche die KGV-Historie und erstelle mir eine Excel-Datei mit den Charts."*

Und das System:

1. **Supervisor:** Versteht den Plan -> Ruft Scout.
2. **Scout:** Lädt Kurse & Kennzahlen (via `DataManager`). Meldet "Done".
3. **Analyst:** Berechnet KGV-Verläufe. Meldet "Done".
4. **Reporter:** Erstellt Excel mit Charts.
5. **Supervisor:** Antwortet dem User: "Hier ist deine Datei."

---


# Schritt für Schritt Liste 

Wir arbeiten uns von unten (Daten-Fundament) nach oben (Agenten-Schwarm) vor.

### **Phase 1: Tool-ification (Die Schnittstellen härten)**

*Ziel: Deine bestehende Python-Logik "maschinenlesbar" machen.*

* **1.1. Return-Types Definieren**
* [ ] `portfolio_tool/models.py` (oder `types.py`) erstellen.
* [ ] Dataclass `UpdateResult` definieren (Felder: `ticker`, `status`, `rows_updated`, `message`).


* **1.2. DataManager Refactoring (Schicht 3)**
* [ ] `update_prices_for_asset` in `data_manager.py` anpassen: `print()` durch Return `UpdateResult` ersetzen.
* [ ] `update_dividends_for_asset` anpassen.
* [ ] `update_splits_for_asset` anpassen.
* [ ] `update_shares_history_for_asset` anpassen.
* [ ] `update_quarterly_earnings_for_asset` anpassen.
* [ ] `update_financial_statements_for_asset` anpassen.


* **1.3. Tool Wrapper erstellen (Schicht 5)**
* [ ] Verzeichnis `portfolio_tool/tools/` erstellen.
* [ ] Datei `market_data_tools.py` erstellen.
* [ ] Pydantic Models für die Input-Parameter definieren (für LLM Schema).
* [ ] Funktionen mit `@tool` (LangChain) oder als reine Python-Funktionen wrappen, die den `DataManager` aufrufen und JSON zurückgeben.

---

### **Phase 2: Semantic Layer (Das Gedächtnis aufbauen)**

*Ziel: Unstrukturierte Daten (Texte) speicherbar und suchbar machen.*

* **2.1. Datenbank-Erweiterung (SQL)**
* [ ] In `database_setup.py`: Tabelle `DocumentChunk` hinzufügen (Spalten: `id`, `asset_id`, `content`, `embedding_id`, `metadata`).
* [ ] DB-Migration durchführen (oder DB neu initialisieren, da SQLite).


* **2.2. Vektor-Datenbank Setup (ChromaDB)**
* [ ] `chromadb` und `sentence-transformers` installieren.
* [ ] `portfolio_tool/services/vector_store.py` erstellen (Initialisierung des Chroma Clients).


* **2.3. RAG Ingestion Pipeline**
* [ ] Skript `scripts/ingest_documents.py` erstellen.
* [ ] Funktion schreiben, die einen Beispiel-Text (z.B. PDF oder String) in Chunks teilt.
* [ ] Chunks embedden (Vektor erzeugen).
* [ ] Dual-Write implementieren: Text-Metadaten in SQLite (`DocumentChunk`), Vektor in ChromaDB.


* **2.4. RAG Retrieval Tool**
* [ ] Tool `search_documents(query, ticker)` in `portfolio_tool/tools/rag_tools.py` erstellen.

---

### **Phase 3: The Agent Swarm (Die Orchestrierung)**

*Ziel: Aufbau des Multi-Agenten-Systems mit LangGraph.*

* **3.1. Environment Setup**
* [ ] API Keys setzen (OpenAI / Anthropic) in `.env`.
* [ ] `langgraph` und `langchain_openai` installieren.


* **3.2. State Definition**
* [ ] `agent/state.py` erstellen.
* [ ] `AgentState` definieren (TypedDict mit `messages`, `data_context`, `next_step`).


* **3.3. Die Sub-Agenten (Nodes)**
* [ ] `agent/nodes/scout.py` (Nutzt Tools aus Phase 1).
* [ ] `agent/nodes/analyst.py` (Nutzt Tools aus Phase 2 + Metrics).
* [ ] `agent/nodes/reporter.py` (Erstellt Zusammenfassungen).


* **3.4. Der Supervisor (Der Graph)**
* [ ] `agent/graph.py` erstellen.
* [ ] Router-Logik implementieren (LLM entscheidet: "Wen frage ich als nächstes?").
* [ ] Graphen kompilieren (Entry Point -> Supervisor -> Node -> Supervisor).

---

### **Phase 4: Output & Visualization (Das "Wow")**

*Ziel: Ergebnisse sichtbar machen (Excel/Plots).*

* **4.1. Visualization Tool**
* [ ] `portfolio_tool/analytics/viz.py` erstellen (Matplotlib/Plotly).
* [ ] Tool `generate_price_chart(ticker)` erstellen, das ein Bild speichert.


* **4.2. Reporting Tool**
* [ ] Tool `create_excel_report(data)` erstellen (pandas `to_excel`).


* **4.3. Demo Skript**
* [ ] `main_agent_demo.py` erstellen, das den Graphen mit einer User-Query startet ("Analysiere SAP").