# 📚 DataManager Guide

**Last Updated:** 2026-01-11  
**Status:** Phase 1B Complete - All update methods return `UpdateResult`

---

## 🎯 **Was Ist Der DataManager?**

Der `DataManager` ist die **zentrale Orchestrierungsschicht** (Layer 3) deines Systems.

**Seine Aufgaben:**
- 🔄 Koordiniert Datenfluss zwischen Provider (YFinance) und Datenbank
- 💾 Speichert Daten idempotent (keine Duplikate)
- 📊 Tracked Metadaten (wann wurde zuletzt geholt?)
- 🤖 Liefert strukturierte Responses für Agents (`UpdateResult`)

**Er ist NICHT zuständig für:**
- ❌ Analytics/Berechnungen → Das macht `MetricsCalculator` (Layer 4)
- ❌ Direkte API-Calls → Das macht `YFinanceProvider` (Layer 1)
- ❌ Agent-Logik → Das machen Tools & Agents (Layer 5)

---

## 📂 **Aktuelle Struktur (Stand: Phase 1B)**
```
src/portfolio_tool/
├── data_manager.py          ← Hauptklasse
├── database_setup.py        ← Schema-Definitionen
├── providers/
│   ├── base.py             ← Provider-Interface
│   └── yfinance_provider.py ← YFinance-Implementierung
└── models/
    └── responses.py         ← UpdateResult, QueryResult
```

---

## ✅ **Was Ist Aktuell Vorhanden?**

### **Unterstützte Datentypen:**

| Datentyp | Tabelle | Update-Methode | Status |
|----------|---------|----------------|--------|
| **Daily Prices** | `daily_prices` | `update_prices_for_asset()` | ✅ Fertig |
| **Dividends** | `dividends` | `update_dividends_for_asset()` | ✅ Fertig |
| **Stock Splits** | `corporate_actions` | `update_splits_for_asset()` | ✅ Fertig |
| **Shares History** | `shares_history` | `update_shares_history_for_asset()` | ✅ Fertig |
| **Quarterly Earnings** | `quarterly_earnings` | `update_quarterly_earnings_for_asset()` | ✅ Fertig |
| **Fundamentals** | `fundamentals` | `update_fundamental_data()` | ✅ Fertig |
| **Financial Statements** | `financial_statements` | `update_financial_statements_for_asset()` | ✅ Fertig |
| **Asset Info** | `assets` | `force_update_asset_info()` | ✅ Fertig |

---

### **Helper-Methoden:**

| Methode | Rückgabe | Zweck |
|---------|----------|-------|
| `_get_or_create_asset(ticker, name, class)` | `Asset \| None` | Holt/erstellt Asset mit erweiterten Stammdaten |
| `_get_or_create_metadata(asset_id)` | `AssetFetchMetadata` | Holt/erstellt Metadaten für Fetch-Tracking |
| `_perform_upsert(model, values, index)` | `int` | Führt idempotenten Batch-Upsert aus |
| `_should_fetch(last_fetch, interval)` | `bool` | Prüft ob Re-Fetch nötig ist |

---

### **Alle Update-Methoden Geben `UpdateResult` Zurück:**
```python
result = dm.update_prices_for_asset(asset)

# result ist ein UpdateResult mit:
result.success          # bool: True/False
result.operation        # str: "update_prices"
result.affected_count   # int: Anzahl aktualisierter Zeilen
result.entities         # list: ["AAPL"]
result.entity_type      # str: "asset"
result.date_range       # tuple: (start_date, end_date) oder None
result.metadata         # dict: Zusätzliche Infos
result.error_message    # str: Fehlermeldung oder None
```

**Das ermöglicht Agents zu verstehen was passiert ist!** 🤖

---

## 🔄 **Typischer Workflow**

### **Beispiel: Preise Für AAPL Aktualisieren**
```python
from portfolio_tool.database_setup import get_session
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider

# 1. Initialisierung
session = get_session()
provider = YFinanceProvider()
dm = DataManager(session, provider)

# 2. Asset holen/erstellen
asset = dm.get_or_create_asset("AAPL", "Apple Inc.", "stock")
# → Sucht AAPL in DB
# → Wenn nicht vorhanden: erstellt es + holt Stammdaten vom Provider
# → Gibt Asset-Objekt zurück

# 3. Daten aktualisieren
result = dm.update_prices_for_asset(asset, start_date=None)
# → Findet letztes Datum in DB
# → Holt nur fehlende Daten vom Provider (Delta-Fetch)
# → Upsert in DB (keine Duplikate)
# → Gibt UpdateResult zurück

# 4. Ergebnis prüfen
if result.success:
    print(f"✅ {result.affected_count} Preise für {result.entities[0]} aktualisiert")
else:
    print(f"❌ Fehler: {result.error_message}")
```

---

## 🚀 **In Tools Nutzen (Phase 1C)**

### **So Werden Deine Tools Aussehen:**
```python
# src/tools/data_tools.py

from langchain.tools import tool
from portfolio_tool.database_setup import get_session
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider

@tool
def fetch_stock_prices(ticker: str, start_date: str = None) -> dict:
    """Fetch and update stock price data for a ticker."""
    
    session = get_session()
    provider = YFinanceProvider()
    dm = DataManager(session, provider)
    
    # Asset holen/erstellen (intern)
    asset = dm.get_or_create_asset(ticker, ticker, "stock")
    
    if not asset:
        return {"success": False, "error": f"Could not find/create {ticker}"}
    
    # Daten aktualisieren
    from datetime import datetime
    start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    result = dm.update_prices_for_asset(asset, start_date=start)
    
    # UpdateResult als dict für Agent
    return result.to_dict()


@tool
def fetch_financial_statements(ticker: str, report_type: str = "balance_sheet") -> dict:
    """Fetch financial statements for a stock."""
    
    session = get_session()
    provider = YFinanceProvider()
    dm = DataManager(session, provider)
    
    asset = dm.get_or_create_asset(ticker, ticker, "stock")
    
    result = dm.update_financial_statements_for_asset(
        asset=asset,
        report_type=report_type,
        period_type="annual"
    )
    
    return result.to_dict()
```

**Agents können diese Tools dann direkt nutzen!**

---

## 📊 **Idempotenz & Delta-Fetching**

### **Wie Verhindert Der DataManager Duplikate?**

**1. Delta-Fetching (Nur Neue Daten Holen):**
```python
# In update_prices_for_asset():
if not start_date:
    # Finde letztes Datum in DB
    last_entry = self.session.query(func.max(DailyPrice.date)).filter(
        DailyPrice.asset_id == asset.id
    ).scalar()
    
    # Nur ab diesem Datum holen
    start_date = last_entry if last_entry else date(2000, 1, 1)

# Hole nur fehlende Daten
provider_data = self.provider.get_daily_prices(
    ticker=asset.ticker,
    start=start_date,  # ← Nur ab letztem Datum!
    end=date.today()
)
```

**Ergebnis:** Wenn AAPL schon Daten bis 2024-12-31 hat, holt es nur ab 2025-01-01.

---

**2. Upsert (ON CONFLICT DO UPDATE):**
```python
# In _perform_upsert():
stmt = sqlite_insert(DailyPrice).values(values)

upsert_stmt = stmt.on_conflict_do_update(
    index_elements=['asset_id', 'date'],  # ← Unique constraint
    set_=update_set  # ← Bei Konflikt: UPDATE statt INSERT
)

self.session.execute(upsert_stmt)
```

**Ergebnis:** Wenn ein Datum schon existiert, wird es geupdatet statt dupliziert.

---

**3. Batch-Processing (Verhindert SQLite-Limits):**
```python
# SQLite hat Limit von ~32.000 SQL-Variablen
# _perform_upsert() teilt in Batches auf:

BATCH_SIZE = 500  # 500 Zeilen pro Batch

for i in range(0, total_rows, BATCH_SIZE):
    chunk = values[i:i + BATCH_SIZE]
    # Upsert diesen Chunk
    self.session.execute(upsert_stmt)

self.session.commit()  # Alle Batches in EINER Transaktion
```

**Ergebnis:** Kann 10.000+ Zeilen auf einmal importieren ohne Fehler.

---

## ⏳ **Fetch-Interval Management**

### **Wie Verhindert Der DataManager Zu Viele API-Calls?**

**Manche Daten ändern sich selten (z.B. Fundamentals, Shares).**

**Lösung: Interval-Based Fetching**
```python
# In config.toml:
[data_fetch]
earnings_fetch_interval_days = 7   # Earnings nur alle 7 Tage
profile_fetch_interval_days = 30   # Fundamentals nur alle 30 Tage
shares_fetch_interval_days = 30    # Shares nur alle 30 Tage

# Im DataManager:
def update_quarterly_earnings_for_asset(self, asset, force_update=False):
    meta = self._get_or_create_metadata(asset.id)
    interval = self.config.get('earnings_fetch_interval_days', 7)
    
    # Prüfe ob Interval abgelaufen ist
    if not force_update and not self._should_fetch(meta.last_earnings_fetch_time, interval):
        # Zu früh! Skip.
        return UpdateResult(
            success=True, 
            operation="update_earnings", 
            affected_count=0,
            metadata={"reason": "skipped_interval"}
        )
    
    # Interval abgelaufen → Fetch neue Daten
    # ...
    
    # Speichere Fetch-Zeit
    meta.last_earnings_fetch_time = datetime.utcnow()
    self.session.commit()
```

**Ergebnis:** Verhindert unnötige API-Calls und respektiert Rate-Limits.

---

## 🔮 **Was Fehlt Noch? (Zukünftige Erweiterungen)**

### **Aktuell: NUR Stock-Daten**

Dein DataManager unterstützt aktuell:
- ✅ Stocks (AAPL, MSFT, GOOGL)
- ✅ Stock-bezogene Daten (Preise, Earnings, Statements)

**Was NICHT unterstützt wird:**
- ❌ Economic Indicators (GDP, Inflation, Unemployment)
- ❌ News Articles
- ❌ PDF Documents / Earnings Call Transcripts
- ❌ Bonds, Commodities, Crypto
- ❌ Alternative Data (Social Media Sentiment, etc.)

---

## 📋 **Roadmap: Erweiterungen Für Neue Datentypen**

### **Phase 2: Economic Indicators (GDP, Inflation, etc.)**

**Was Brauchst Du:**

#### **1. Neues Schema (database_setup.py):**
```python
class EconomicIndicator(Base):
    """Represents an economic indicator (GDP, Inflation, etc.)"""
    __tablename__ = 'economic_indicators'
    
    id = Column(Integer, primary_key=True)
    indicator_code = Column(String, unique=True, nullable=False)  # "US_GDP", "US_CPI"
    name = Column(String, nullable=False)  # "United States GDP"
    source = Column(String)  # "FRED", "World Bank", "OECD"
    frequency = Column(String)  # "quarterly", "monthly", "annual"
    unit = Column(String)  # "Billions USD", "Percent"

class EconomicIndicatorValue(Base):
    """Time series values for economic indicators"""
    __tablename__ = 'economic_indicator_values'
    
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey('economic_indicators.id'))
    date = Column(Date, nullable=False)
    value = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('indicator_id', 'date', name='uix_indicator_date'),
    )
```

---

#### **2. Neuer Provider (providers/fred_provider.py):**
```python
from .base import DataProviderInterface
from typing import List
from datetime import date

class FREDProvider(DataProviderInterface):
    """Provider for economic data from FRED API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # ... FRED API client setup
    
    def get_indicator_data(
        self, 
        indicator_code: str, 
        start_date: date = None
    ) -> List[IndicatorValueDTO]:
        """Fetch indicator values from FRED."""
        # Call FRED API
        # Return list of IndicatorValueDTO
        pass
    
    def get_indicator_info(self, indicator_code: str) -> IndicatorInfoDTO:
        """Get metadata about an indicator."""
        pass
```

---

#### **3. Helper-Methode (data_manager.py):**
```python
def get_or_create_indicator(
    self,
    indicator_code: str,
    name: str,
    source: str = "FRED",
    frequency: str = "quarterly"
) -> Optional[EconomicIndicator]:
    """
    Get or create an economic indicator.
    Similar to get_or_create_asset() but for indicators.
    """
    # Versuche zu finden
    indicator = self.session.query(EconomicIndicator).filter_by(
        indicator_code=indicator_code
    ).first()
    
    if indicator:
        print(f"Indicator gefunden: {indicator.name}")
        return indicator
    
    print(f"Indicator {indicator_code} nicht gefunden, erstelle ihn...")
    
    try:
        new_indicator = EconomicIndicator(
            indicator_code=indicator_code,
            name=name,
            source=source,
            frequency=frequency
        )
        self.session.add(new_indicator)
        self.session.commit()
        print(f"Indicator erstellt: {new_indicator}")
        return new_indicator
    except Exception as e:
        print(f"Fehler beim Erstellen von Indicator {indicator_code}: {e}")
        self.session.rollback()
        return None
```

---

#### **4. Update-Methode (data_manager.py):**
```python
def update_indicator_values(
    self, 
    indicator: EconomicIndicator,
    start_date: date = None
) -> UpdateResult:
    """
    Updates economic indicator values from FRED.
    
    Args:
        indicator: EconomicIndicator object
        start_date: Optional start date for delta-fetch
    
    Returns:
        UpdateResult with operation status
    """
    try:
        print(f"... prüfe Werte für {indicator.name}")
        
        # Delta-Fetch: Finde letztes Datum
        if not start_date:
            last_date = self.session.query(
                func.max(EconomicIndicatorValue.date)
            ).filter(
                EconomicIndicatorValue.indicator_id == indicator.id
            ).scalar()
            start_date = last_date if last_date else date(2000, 1, 1)
        
        # Hole Daten vom Provider
        provider_data = self.fred_provider.get_indicator_data(
            indicator.indicator_code, 
            start_date
        )
        
        if not provider_data:
            return UpdateResult(
                success=True,
                operation="update_indicator_values",
                affected_count=0,
                entities=[indicator.indicator_code],
                entity_type="indicator",  # ← NEUER entity_type!
                metadata={"status": "no_new_data"}
            )
        
        # Konvertiere zu Upsert-Format
        values_to_upsert = []
        for value_dto in provider_data:
            if start_date and value_dto.date < start_date:
                continue
            values_to_upsert.append({
                'indicator_id': indicator.id,
                'date': value_dto.date,
                'value': float(value_dto.value)
            })
        
        if not values_to_upsert:
            return UpdateResult(
                success=True,
                operation="update_indicator_values",
                affected_count=0,
                entities=[indicator.indicator_code],
                entity_type="indicator"
            )
        
        # Upsert
        affected_count = self._perform_upsert(
            model=EconomicIndicatorValue,
            values=values_to_upsert,
            index_elements=['indicator_id', 'date']
        )
        
        return UpdateResult(
            success=True,
            operation="update_indicator_values",
            affected_count=affected_count,
            entities=[indicator.indicator_code],
            entity_type="indicator",
            date_range=(start_date, date.today()),
            metadata={"source": "FRED"}
        )
        
    except Exception as e:
        return UpdateResult(
            success=False,
            operation="update_indicator_values",
            affected_count=0,
            entities=[indicator.indicator_code],
            entity_type="indicator",
            error_message=str(e)
        )
```

---

#### **5. Nutzung:**
```python
# In deinem Script/Tool:
from portfolio_tool.providers.fred_provider import FREDProvider

# DataManager mit FRED Provider initialisieren
fred_provider = FREDProvider(api_key="YOUR_FRED_API_KEY")
dm = DataManager(session, yfinance_provider)
dm.fred_provider = fred_provider  # Zusätzlicher Provider

# Indicator holen/erstellen
gdp = dm.get_or_create_indicator(
    indicator_code="GDPC1",
    name="Real Gross Domestic Product",
    source="FRED",
    frequency="quarterly"
)

# Werte aktualisieren
result = dm.update_indicator_values(gdp)

if result.success:
    print(f"✅ {result.affected_count} GDP-Werte aktualisiert")
```

---

### **Phase 3: PDF Documents / News**

**Was Brauchst Du:**

#### **1. Schema:**
```python
class Document(Base):
    """Represents a document (PDF, news article, etc.)"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)
    file_path = Column(String)
    document_type = Column(String)  # "earnings_call", "10K", "news", "analyst_report"
    related_asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
class DocumentChunk(Base):
    """Vector embeddings for semantic search (RAG)"""
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    chunk_index = Column(Integer)
    text = Column(Text)
    embedding_id = Column(String)  # ChromaDB ID
```

---

#### **2. Helper-Methode:**
```python
def get_or_create_document(
    self,
    filename: str,
    document_type: str,
    file_path: str = None,
    related_ticker: str = None
) -> Optional[Document]:
    """Get or create a document."""
    
    doc = self.session.query(Document).filter_by(filename=filename).first()
    
    if doc:
        return doc
    
    # Find related asset if ticker provided
    related_asset_id = None
    if related_ticker:
        asset = self.get_or_create_asset(related_ticker, related_ticker, "stock")
        if asset:
            related_asset_id = asset.id
    
    try:
        new_doc = Document(
            filename=filename,
            file_path=file_path or f"/data/{filename}",
            document_type=document_type,
            related_asset_id=related_asset_id
        )
        self.session.add(new_doc)
        self.session.commit()
        return new_doc
    except Exception as e:
        self.session.rollback()
        return None
```

---

#### **3. Update-Methode:**
```python
def ingest_document(
    self,
    document: Document,
    content: str = None
) -> UpdateResult:
    """
    Ingests a document and creates vector embeddings for RAG.
    
    Args:
        document: Document object
        content: Text content (if not reading from file)
    
    Returns:
        UpdateResult with number of chunks created
    """
    try:
        # Read content if not provided
        if not content:
            # Read from file_path
            with open(document.file_path, 'r') as f:
                content = f.read()
        
        # Split into chunks
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_text(content)
        
        # Create embeddings and store in ChromaDB
        from langchain.embeddings import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings()
        
        chunk_records = []
        for idx, chunk_text in enumerate(chunks):
            # Store in vector DB
            embedding_id = f"{document.id}_{idx}"
            # ... ChromaDB logic ...
            
            # Track in SQL
            chunk_records.append({
                'document_id': document.id,
                'chunk_index': idx,
                'text': chunk_text,
                'embedding_id': embedding_id
            })
        
        # Upsert chunks
        affected_count = self._perform_upsert(
            model=DocumentChunk,
            values=chunk_records,
            index_elements=['document_id', 'chunk_index']
        )
        
        return UpdateResult(
            success=True,
            operation="ingest_document",
            affected_count=affected_count,
            entities=[document.filename],
            entity_type="document",  # ← NEUER entity_type!
            metadata={
                "chunks_created": len(chunks),
                "document_type": document.document_type
            }
        )
        
    except Exception as e:
        return UpdateResult(
            success=False,
            operation="ingest_document",
            affected_count=0,
            entities=[document.filename],
            entity_type="document",
            error_message=str(e)
        )
```

---

## 🎯 **Pattern Für Neue Datentypen**

### **Checkliste: Neuen Datentyp Hinzufügen**

Wenn du einen neuen Datentyp hinzufügen willst (Bonds, News, Social Media, etc.):

#### **1. Schema Definieren (database_setup.py)**
```python
class NewEntityType(Base):
    __tablename__ = 'new_entities'
    id = Column(Integer, primary_key=True)
    # ... deine Felder ...

class NewEntityData(Base):
    __tablename__ = 'new_entity_data'
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey('new_entities.id'))
    # ... deine Datenfelder ...
```

#### **2. Provider Erstellen (providers/new_provider.py)**
```python
class NewDataProvider(DataProviderInterface):
    def get_new_data(self, ...):
        # API-Calls, Web-Scraping, etc.
        pass
```

#### **3. Helper-Methode (data_manager.py)**
```python
def get_or_create_new_entity(self, identifier, ...):
    # Finde oder erstelle Entität
    pass
```

#### **4. Update-Methode (data_manager.py)**
```python
def update_new_entity_data(self, entity, ...) -> UpdateResult:
    try:
        # Delta-Fetch
        # Provider-Call
        # Upsert
        return UpdateResult(
            success=True,
            operation="update_new_entity",
            affected_count=...,
            entities=[...],
            entity_type="new_entity_type",  # ← WICHTIG!
            metadata={...}
        )
    except Exception as e:
        return UpdateResult(
            success=False,
            operation="update_new_entity",
            affected_count=0,
            entities=[...],
            entity_type="new_entity_type",
            error_message=str(e)
        )
```

#### **5. Tool Erstellen (tools/data_tools.py)**
```python
@tool
def fetch_new_data(identifier: str) -> dict:
    dm = DataManager(...)
    entity = dm.get_or_create_new_entity(identifier)
    result = dm.update_new_entity_data(entity)
    return result.to_dict()
```

---

## 📊 **Entity Types Übersicht**

### **Aktuell Unterstützt:**

| entity_type | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `"asset"` | Stocks, ETFs | `["AAPL", "MSFT"]` |

### **Zukünftig:**

| entity_type | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `"indicator"` | Economic indicators | `["US_GDP", "US_CPI"]` |
| `"document"` | PDFs, transcripts | `["AAPL_Q4_2024.pdf"]` |
| `"news"` | News articles | `["article_12345"]` |
| `"bond"` | Bonds | `["US10Y"]` |
| `"commodity"` | Commodities | `["GOLD", "OIL"]` |
| `"crypto"` | Cryptocurrencies | `["BTC", "ETH"]` |

**Der `entity_type` im `UpdateResult` hilft Agents zu verstehen WAS aktualisiert wurde!**

---

## 🔧 **Best Practices**

### **DO:**
- ✅ Nutze Delta-Fetching (nur fehlende Daten holen)
- ✅ Nutze `_perform_upsert()` für idempotente Inserts
- ✅ Gib IMMER `UpdateResult` zurück (nie `None`)
- ✅ Logge Metadaten (last_fetch_time) für Interval-Management
- ✅ Wrappe in `try-except` für robustes Error-Handling
- ✅ Nutze `get_or_create_*` Methoden für Asset/Indicator/etc.

### **DON'T:**
- ❌ Hole ALLE Daten jedes Mal neu (waste of API calls)
- ❌ Erstelle Duplikate (nutze Upsert mit Unique Constraints)
- ❌ Gib `None` zurück (Agents können damit nichts anfangen)
- ❌ Ignoriere Fehler (fange sie und gib Error-Result zurück)
- ❌ Schreibe Analytics-Logik in DataManager (gehört in Calculator)

---

## 🎓 **Zusammenfassung**

**Der DataManager ist:**
- ✅ Zentrale Orchestrierungsschicht für Datenfluss
- ✅ Idempotent (keine Duplikate, kann mehrfach aufgerufen werden)
- ✅ Delta-basiert (holt nur fehlende Daten)
- ✅ Agent-ready (strukturierte `UpdateResult` Responses)
- ✅ Erweiterbar (neuer Datentyp = neues Schema + Provider + Methoden)

**Aktueller Status:**
- ✅ Vollständig für Stock-Daten
- ⏳ Bereit für Economic Data, News, PDFs (Schema + Methoden hinzufügen)

**Nächste Schritte:**
1. Phase 1C: Tools bauen (wrappe existierende Methoden)
2. Phase 2: Economic Data hinzufügen (optional)
3. Phase 3: RAG für Dokumente (optional)
4. Phase 4: Multi-Agent System

---

**Du hast ein solides Foundation!** Der DataManager kann einfach erweitert werden wenn du neue Datentypen brauchst. 🚀