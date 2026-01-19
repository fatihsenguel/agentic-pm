# AGENTIC QUANT PORTFOLIO MANAGER
## Multi-Agent System Roadmap v5.0 - Quant PM Focus

---

# 📋 EXECUTIVE SUMMARY

**Pivot:** Von "Equity Research Assistant" zu "Agentic Quant Portfolio Manager"

**Ziel:** Multi-Agent System das selbstständig Portfolios optimiert, Marktregime erkennt, und taktische Adjustments vorschlägt.

**Zielgruppe:** Portfolio Manager, Quant PM, Asset Allocation Teams bei Großbanken und Asset Managern

**Timeline:** 5-6 Wochen

**Ziel-Prompts:**

| # | Prompt | Fokus | Quant-Relevanz |
|---|--------|-------|----------------|
| **#1** | Portfolio Optimization (SAA) | Markowitz, Risk Parity, Constraints | ⭐⭐⭐⭐⭐ |
| **#2** | Macro Regime Detection (TAA) | RAG auf Fed Minutes, Sentiment Signals | ⭐⭐⭐⭐⭐ |
| **#3** | Strategy Backtesting | Point-in-Time Simulation, Performance Attribution | ⭐⭐⭐⭐⭐ |
| **#4** | Rebalancing Recommendation | Drift Detection, Tax-Aware Rebalancing | ⭐⭐⭐⭐ |

**Outcome:** Interview-ready MVP das zeigt: "Ich verstehe Modern Tech UND Quant Finance"

---

# 🧭 PROJEKTPHILOSOPHIE

## Unsere Architektur-Prinzipien (unverändert)

Diese Prinzipien aus Phase 1-3 bleiben gültig:

| Prinzip | Phase 1-3 Anwendung | Phase 5 (Quant) Anwendung |
|---------|---------------------|---------------------------|
| **Separation of Concerns** | DataManager, MetricsCalculator, Provider | OptimizationEngine, RiskEngine, BacktestEngine |
| **Hot Potato Principle** | 10k Preise → Return Summary | Covariance Matrix → Optimal Weights |
| **DRY** | UpdateResult DTO | PortfolioResult, BacktestResult DTOs |
| **Interface Abstraction** | DataProviderInterface | OptimizerInterface (Markowitz, Risk Parity, etc.) |
| **Idempotenz** | Upserts | Deterministic Backtests |
| **Agent-Ready Responses** | Tool Results | Optimization Results mit Reasoning |
| **Testability First** | Mock Providers | Mock Optimizers, Deterministic Seeds |

## NEUES Prinzip: No Look-Ahead Bias

```
PRINZIP: LLMs treffen KEINE Entscheidungen die historische Daten betreffen.

ANWENDUNG:
├── LLM übersetzt User-Intent → Deterministische Regeln/Parameter
├── Backtest Engine führt Regeln aus → Reines Python, kein LLM
├── LLM interpretiert Ergebnisse → Nur auf fertige Resultate
└── NIEMALS: LLM entscheidet "Soll ich 2020 kaufen?"

WARUM:
├── LLM wurde auf Post-Facto Daten trainiert
├── LLM "weiß" dass Tech 2020-2024 geboomt hat
└── Trade-Entscheidungen durch LLM = Look-Ahead Bias = Wertloser Backtest
```

---

# 🎯 ZIEL-PROMPTS

## Prompt #1: Strategic Asset Allocation (SAA)

### User Input:
```
"Ich habe €500,000 mit einem 10-Jahres-Horizont.
Risikotoleranz: Moderat (max. Volatilität 12%)
Universum: Global Equities, Bonds, Gold, REITs

Erstelle eine optimale Asset Allocation mit:
1. Efficient Frontier Visualisierung
2. Empfohlene Gewichte für mein Risikoprofil
3. Expected Return und Risiko-Kennzahlen
4. Vergleich: Mean-Variance vs. Risk Parity Ansatz"
```

### Erwarteter Output:
```
📊 STRATEGIC ASSET ALLOCATION

👤 Investor Profile:
   • Capital: €500,000
   • Horizon: 10 years
   • Risk Tolerance: Moderate (σ ≤ 12%)

📈 Efficient Frontier Analysis:
   [Visualization: Return vs. Volatility mit markiertem optimal point]

💼 MEAN-VARIANCE OPTIMIZATION (Max Sharpe):
┌──────────────┬──────────┬─────────────┬──────────────┐
│ Asset        │ Weight   │ Contribution│ Exp. Return  │
├──────────────┼──────────┼─────────────┼──────────────┤
│ Global Eq.   │ 45.2%    │ 7.8% risk   │ 8.5%         │
│ Bonds        │ 32.1%    │ 2.1% risk   │ 3.2%         │
│ Gold         │ 12.4%    │ 1.5% risk   │ 4.1%         │
│ REITs        │ 10.3%    │ 0.6% risk   │ 6.2%         │
└──────────────┴──────────┴─────────────┴──────────────┘

Portfolio Metrics:
• Expected Return: 6.8% p.a.
• Expected Volatility: 11.4% (within 12% limit ✓)
• Sharpe Ratio: 0.52
• Max Drawdown (historical): -18.3%

⚖️ RISK PARITY COMPARISON:
┌──────────────┬──────────┬─────────────┐
│ Asset        │ Weight   │ Risk Contrib│
├──────────────┼──────────┼─────────────┤
│ Global Eq.   │ 22.5%    │ 25.0%       │  ← Equal risk
│ Bonds        │ 48.3%    │ 25.0%       │
│ Gold         │ 18.7%    │ 25.0%       │
│ REITs        │ 10.5%    │ 25.0%       │
└──────────────┴──────────┴─────────────┘

Risk Parity Metrics:
• Expected Return: 5.2% p.a.
• Expected Volatility: 8.1%
• Sharpe Ratio: 0.46

💡 RECOMMENDATION:
Für Ihr moderates Risikoprofil empfehle ich die Mean-Variance Lösung:
• Höhere Expected Return (6.8% vs 5.2%)
• Volatilität bleibt unter 12% Limit
• Bessere Sharpe Ratio (0.52 vs 0.46)

Risk Parity wäre besser bei: Sehr langen Horizonten, Fokus auf Drawdown-Minimierung

📅 Berechnung: 2026-01-17 | Daten: 5Y historisch | Optimierer: scipy.minimize (SLSQP)
```

### Warum wertvoll für PM-Interview:
- Zeigt Markowitz-Verständnis (nicht nur "ich kenne den Namen")
- Zeigt praktische Constraints (Volatilitätslimit)
- Vergleicht Methoden (Mean-Variance vs Risk Parity)
- Audit Trail für alle Parameter

---

## Prompt #2: Tactical Asset Allocation (TAA) via Macro Regime Detection

### User Input:
```
"Analysiere die aktuellen Marktbedingungen basierend auf:
1. Letzte Fed Minutes (Dokument hochgeladen)
2. Aktuelle Volatilität (VIX)
3. Yield Curve Status

Soll ich mein Portfolio taktisch anpassen?
Aktuelles Portfolio: 60% Equities, 30% Bonds, 10% Gold"
```

### Erwarteter Output:
```
📊 TACTICAL ASSET ALLOCATION ANALYSIS

📄 MACRO REGIME DETECTION:

1️⃣ Fed Minutes Analysis (RAG):
   Document: fed_minutes_january_2026.pdf
   
   Key Extractions:
   • "Committee remains concerned about persistent inflation" (Page 3)
   • "Labor market showing signs of cooling" (Page 7)
   • "Data-dependent approach to future rate decisions" (Page 12)
   
   Sentiment Score: -0.3 (leicht hawkish)
   Regime Signal: CAUTIOUS

2️⃣ Volatility Regime:
   • Current VIX: 22.4
   • 30-day Average: 18.2
   • Percentile (1Y): 72nd
   
   Signal: ELEVATED RISK

3️⃣ Yield Curve:
   • 10Y-2Y Spread: +0.15%
   • Status: Leicht positiv (nach Inversion)
   • Historical Pattern: Post-inversion = Recession Risk +6-18 months
   
   Signal: LATE CYCLE WARNING

📈 COMBINED REGIME ASSESSMENT:
┌─────────────────┬───────────┬──────────┐
│ Indicator       │ Signal    │ Weight   │
├─────────────────┼───────────┼──────────┤
│ Fed Sentiment   │ Cautious  │ 40%      │
│ VIX Level       │ Elevated  │ 30%      │
│ Yield Curve     │ Warning   │ 30%      │
└─────────────────┴───────────┴──────────┘

Overall Regime: ⚠️ RISK-OFF

💼 TAA RECOMMENDATION:

Current vs. Recommended Allocation:
┌──────────────┬─────────┬─────────────┬────────────┐
│ Asset        │ Current │ Recommended │ Change     │
├──────────────┼─────────┼─────────────┼────────────┤
│ Equities     │ 60%     │ 50%         │ -10%       │
│ Bonds        │ 30%     │ 35%         │ +5%        │
│ Gold         │ 10%     │ 12%         │ +2%        │
│ Cash         │ 0%      │ 3%          │ +3%        │
└──────────────┴─────────┴─────────────┴────────────┘

Rationale:
1. Reduce equity exposure given elevated VIX + hawkish Fed
2. Increase bonds as defensive position
3. Add gold as inflation/uncertainty hedge
4. Small cash buffer for opportunistic reentry

⚠️ IMPORTANT: TAA deviations should be temporary (3-6 months).
   Return to SAA when regime normalizes.

📅 Analysis: 2026-01-17 | Fed Doc: 127 chunks indexed | VIX source: Live
```

### Warum wertvoll für PM-Interview:
- Kombiniert RAG (unstrukturierte Daten) mit quantitativen Signalen
- Zeigt systematischen Ansatz zu TAA (nicht Bauchgefühl)
- Multi-Source Regime Detection
- Klare Handlungsempfehlung mit Begründung

---

## Prompt #3: Strategy Backtesting

### User Input:
```
"Backteste folgende Strategie über die letzten 5 Jahre:
- SAA: 60% SPY, 30% TLT, 10% GLD
- Rebalancing: Quarterly
- TAA Rule: Wenn VIX > 25, reduziere Equities auf 40%

Vergleiche mit reinem Buy-and-Hold der SAA."
```

### Erwarteter Output:
```
📊 BACKTEST RESULTS

⚙️ STRATEGY CONFIGURATION:
   • Period: 2021-01-01 to 2026-01-01 (5 years)
   • Initial Capital: €100,000 (normalized)
   • SAA: SPY 60%, TLT 30%, GLD 10%
   • Rebalancing: Quarterly
   • TAA Rule: VIX > 25 → Equities 40%, Cash 20%

📈 PERFORMANCE COMPARISON:
┌────────────────────┬──────────────┬──────────────┐
│ Metric             │ SAA + TAA    │ Buy & Hold   │
├────────────────────┼──────────────┼──────────────┤
│ Total Return       │ +47.2%       │ +38.5%       │
│ CAGR               │ 8.0%         │ 6.7%         │
│ Volatility (ann.)  │ 10.8%        │ 12.4%        │
│ Sharpe Ratio       │ 0.74         │ 0.54         │
│ Max Drawdown       │ -14.2%       │ -22.1%       │
│ Calmar Ratio       │ 0.56         │ 0.30         │
│ Win Rate (monthly) │ 62%          │ 58%          │
└────────────────────┴──────────────┴──────────────┘

📉 EQUITY CURVES:
   [Chart: Beide Strategien über Zeit, mit Drawdown-Perioden markiert]

🔄 TAA TRIGGERS:
   The VIX > 25 rule triggered 4 times:
   • 2022-01-24: VIX 31.2 → Risk-Off (6 weeks)
   • 2022-06-13: VIX 28.4 → Risk-Off (4 weeks)
   • 2022-09-26: VIX 32.5 → Risk-Off (8 weeks)
   • 2023-03-13: VIX 26.1 → Risk-Off (3 weeks)

   Impact: TAA avoided avg. 4.2% drawdown per trigger

📊 DRAWDOWN ANALYSIS:
   
   Worst Period: Feb-Oct 2022 (Inflation shock)
   • Buy & Hold: -22.1%
   • SAA + TAA: -14.2% (protected by Risk-Off triggers)
   
   Recovery Time:
   • Buy & Hold: 14 months
   • SAA + TAA: 8 months

💡 INTERPRETATION:

Die TAA-Regel verbesserte risikoadjustierte Returns signifikant:
• +8.7% mehr Total Return
• -7.9% weniger Max Drawdown
• Sharpe verbessert von 0.54 auf 0.74

Der Mehrwert kam primär aus der 2022 Drawdown-Vermeidung.

⚠️ CAVEATS:
• Backtest nutzt point-in-time VIX (kein Look-Ahead)
• Transaction costs: ~0.1% pro Rebalance (inkludiert)
• Keine Steuern berücksichtigt

📅 Backtest: 2026-01-17 | Engine: Deterministic (no LLM in simulation)
   Data Points: 1,260 trading days | Rebalance Events: 24
```

### Warum wertvoll für PM-Interview:
- Zeigt du verstehst Backtesting-Pitfalls (Look-Ahead Bias explizit erwähnt)
- Vergleicht Strategien fair
- Performance Attribution (wo kam der Mehrwert her?)
- Professional Caveats (Transaction Costs, Steuern)

---

## Prompt #4: Rebalancing Recommendation

### User Input:
```
"Mein Portfolio ist gedriftet:
- Target: 60% Equities, 30% Bonds, 10% Gold
- Actual: 68% Equities, 25% Bonds, 7% Gold

Soll ich rebalancen? Berücksichtige:
1. Transaction Costs
2. Steuerliche Auswirkungen (Deutschland)
3. Rebalancing Threshold Best Practices"
```

### Erwarteter Output:
```
📊 REBALANCING ANALYSIS

📈 CURRENT DRIFT:
┌──────────────┬────────┬────────┬─────────┬───────────┐
│ Asset        │ Target │ Actual │ Drift   │ Status    │
├──────────────┼────────┼────────┼─────────┼───────────┤
│ Equities     │ 60%    │ 68%    │ +8%     │ ⚠️ OVER   │
│ Bonds        │ 30%    │ 25%    │ -5%     │ ⚠️ UNDER  │
│ Gold         │ 10%    │ 7%     │ -3%     │ ⚠️ UNDER  │
└──────────────┴────────┴────────┴─────────┴───────────┘

Maximum Drift: 8% (Equities)

📏 THRESHOLD ANALYSIS:

Common Rebalancing Thresholds:
• Conservative: 5% → TRIGGERED ✓
• Moderate: 10% → Not triggered
• Aggressive: 15% → Not triggered

Academic Research (Vanguard, 2019):
• 5% threshold optimal for risk control
• Marginal benefit diminishes beyond monthly checks

💰 COST-BENEFIT ANALYSIS:

Portfolio Value: €500,000
Rebalance Amount: ~€40,000 (8% of portfolio)

Costs:
├── Transaction Costs (0.1%): €40
├── Spread Costs (0.05%): €20
└── Total Costs: ~€60

Expected Benefit:
├── Risk Reduction: Portfolio σ drops from 13.2% to 11.8%
├── Estimated Value-at-Risk improvement: €2,400/year
└── Benefit >> Cost ✓

🇩🇪 STEUERLICHE BETRACHTUNG (Deutschland):

Equity Position hat unrealisierte Gewinne: +€25,000

Bei Verkauf:
├── Kapitalertragsteuer: 25%
├── Soli: 5.5% auf KESt
├── Effektiver Steuersatz: 26.375%
├── Steuerlast bei vollem Rebalance: ~€2,109
└── 
Alternative: "Tax-Aware Rebalancing"
├── Nur Dividenden/Zinsen zum Rebalancen nutzen
├── Neue Einzahlungen in untergewichtete Assets
├── Nur teilweise Rebalancen (Drift auf 5% reduzieren statt 0%)

💼 EMPFEHLUNG:

Option A: Volles Rebalancing
• Pro: Portfolio zurück auf Target-Risiko
• Con: Steuerlast ~€2,100

Option B: Partial Rebalancing (EMPFOHLEN)
• Verkaufe nur €20,000 Equities (statt €40,000)
• Reduziert Drift auf ~4% (unter Threshold)
• Steuerlast: ~€1,050 (50% gespart)
• Risiko bleibt akzeptabel: σ = 12.3%

Option C: Cash Flow Rebalancing
• Nächste Einzahlungen 100% in Bonds/Gold
• Keine Steuerlast
• Dauert länger bis Target erreicht

📅 Analyse: 2026-01-17 | Steuer-Sätze: Deutschland 2026
```

---

# 🏗️ SYSTEM-ARCHITEKTUR

## High-Level Architecture (Quant PM Focus)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      AGENTIC QUANT PORTFOLIO MANAGER v5                         │
│                           Multi-Agent System                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                         ┌─────────────────────────┐                             │
│                         │      USER INTERFACE     │                             │
│                         │    (CLI / Future: API)  │                             │
│                         └───────────┬─────────────┘                             │
│                                     │                                           │
│                                     ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                      RISK MANAGER AGENT (Supervisor)                      │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Responsibilities:                                                   │  │  │
│  │  │ • Parse investment mandate & constraints                            │  │  │
│  │  │ • Validate risk limits before execution                             │  │  │
│  │  │ • Coordinate specialized agents                                     │  │  │
│  │  │ • Final approval of allocations                                     │  │  │
│  │  │ • Synthesize recommendations with risk context                      │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────┬───────────────────────────────────────┘  │
│                                     │                                           │
│         ┌───────────────────────────┼───────────────────────────┐              │
│         │                           │                           │              │
│         ▼                           ▼                           ▼              │
│  ┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    │
│  │   DATA AGENT    │    │ OPTIMIZATION AGENT  │    │  MACRO/RAG AGENT    │    │
│  │                 │    │                     │    │                     │    │
│  │ Skills:         │    │ Skills:             │    │ Skills:             │    │
│  │ • Fetch prices  │    │ • Mean-Variance Opt │    │ • Load Fed Minutes  │    │
│  │ • Calc returns  │    │ • Risk Parity       │    │ • Sentiment Extract │    │
│  │ • Covariance    │    │ • Black-Litterman   │    │ • Regime Detection  │    │
│  │ • Factor calc   │    │ • Constraint handling│   │ • Signal Generation │    │
│  │ • VIX/Macro data│    │ • Efficient Frontier│    │                     │    │
│  │                 │    │                     │    │                     │    │
│  └────────┬────────┘    └──────────┬──────────┘    └──────────┬──────────┘    │
│           │                        │                          │               │
│           ▼                        ▼                          ▼               │
│  ┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    │
│  │  DATA LAYER     │    │ OPTIMIZATION ENGINE │    │    RAG PIPELINE     │    │
│  │                 │    │                     │    │                     │    │
│  │ • DataManager   │    │ • PyPortfolioOpt    │    │ • DocumentLoader    │    │
│  │ • YFinance      │    │ • scipy.optimize    │    │ • ChromaDB          │    │
│  │ • Factor Store  │    │ • cvxpy (optional)  │    │ • Hybrid Retrieval  │    │
│  └─────────────────┘    └─────────────────────┘    └─────────────────────┘    │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         BACKTEST AGENT                                    │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Skills:                                                             │  │  │
│  │  │ • Strategy Simulation (DETERMINISTIC - No LLM in loop)             │  │  │
│  │  │ • Performance Attribution                                           │  │  │
│  │  │ • Risk Analytics (Drawdown, VaR, etc.)                             │  │  │
│  │  │ • Comparison Reports                                                │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                      │  │
│  │                                    ▼                                      │  │
│  │                        ┌─────────────────────┐                           │  │
│  │                        │  BACKTEST ENGINE    │                           │  │
│  │                        │  (Pure Python)      │                           │  │
│  │                        │  • No LLM           │                           │  │
│  │                        │  • Point-in-time    │                           │  │
│  │                        │  • Deterministic    │                           │  │
│  │                        └─────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  CROSS-CUTTING CONCERNS                                                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ PortfolioResult │ │ RiskMetrics     │ │ AuditLogger     │ │ Constraints  │  │
│  │ DTO             │ │ Calculator      │ │ (Compliance)    │ │ Validator    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Communication Protocol (Quant Version)

```python
@dataclass
class PortfolioTask:
    """Task specification for portfolio agents."""
    task_id: str
    task_type: Literal["optimize", "backtest", "analyze_regime", "rebalance"]
    
    # Investment Mandate
    universe: List[str]           # ["SPY", "TLT", "GLD"]
    constraints: Dict[str, Any]   # {"max_volatility": 0.12, "max_weight": 0.4}
    
    # Optional inputs
    current_weights: Optional[Dict[str, float]]
    historical_period: Optional[str]  # "5Y", "10Y"
    taa_rules: Optional[Dict]
    
    metadata: Dict[str, Any]


@dataclass  
class PortfolioResult:
    """Standardized result from portfolio agents."""
    agent_name: str
    task_id: str
    success: bool
    
    # Core outputs
    weights: Dict[str, float]              # {"SPY": 0.6, "TLT": 0.3, "GLD": 0.1}
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    
    # Risk decomposition
    risk_contributions: Dict[str, float]   # {"SPY": 0.65, "TLT": 0.20, "GLD": 0.15}
    
    # Backtest specific (optional)
    backtest_metrics: Optional[BacktestMetrics]
    
    # Audit trail
    optimization_method: str               # "mean_variance", "risk_parity"
    constraints_applied: List[str]
    data_period: str
    calculation_timestamp: datetime
    
    # For LLM
    reasoning: str
    confidence: float
```

---

## Execution Flow: Prompt #1 (SAA Optimization)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER: "Optimiere Portfolio mit max 12% Volatilität"                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RISK MANAGER (Supervisor):                                                 │
│  → Parse constraints: σ_max = 12%                                          │
│  → Identify universe from context or ask                                    │
│  → Create execution plan                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│  STEP 1: DATA AGENT               │ │  (Parallel if macro requested)    │
│                                   │ │                                   │
│  • Fetch 5Y prices for universe   │ │  MACRO AGENT (optional):         │
│  • Calculate returns              │ │  • Current regime assessment      │
│  • Build covariance matrix        │ │  • Any TAA adjustments needed?   │
│                                   │ │                                   │
│  Returns:                         │ │                                   │
│  • returns_df                     │ │                                   │
│  • cov_matrix                     │ │                                   │
│  • risk_free_rate                 │ │                                   │
└───────────────────┬───────────────┘ └───────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: OPTIMIZATION AGENT                                                 │
│                                                                             │
│  Input: Covariance matrix, returns, constraints                            │
│                                                                             │
│  Task 2.1: Mean-Variance Optimization                                      │
│  • Objective: Maximize Sharpe Ratio                                        │
│  • Constraint: σ ≤ 12%                                                     │
│  • Method: scipy.optimize.minimize (SLSQP)                                 │
│                                                                             │
│  Task 2.2: Risk Parity (for comparison)                                    │
│  • Objective: Equal risk contribution                                      │
│  • Method: Iterative risk budgeting                                        │
│                                                                             │
│  Task 2.3: Generate Efficient Frontier                                     │
│  • 50 points from min-var to max-return                                    │
│                                                                             │
│  Returns: PortfolioResult with both solutions                              │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RISK MANAGER: Validate & Synthesize                                        │
│                                                                             │
│  • Check: Are all constraints satisfied? ✓                                 │
│  • Check: Any concentration risk? (max weight check)                       │
│  • Compare: Mean-Variance vs Risk Parity                                   │
│  • Synthesize: Final recommendation with reasoning                         │
│  • Add: Audit trail (data dates, methods used)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Execution Flow: Prompt #3 (Backtesting) - CRITICAL: No LLM in Simulation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER: "Backteste 60/40 mit TAA (VIX > 25 → Risk-Off)"                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RISK MANAGER: Parse & Translate                                            │
│                                                                             │
│  LLM's ONLY JOB HERE:                                                      │
│  • Understand user intent                                                   │
│  • Translate to DETERMINISTIC rules:                                       │
│                                                                             │
│    strategy_config = {                                                      │
│        "weights": {"SPY": 0.6, "TLT": 0.4},                                │
│        "rebalance": "quarterly",                                            │
│        "taa_rules": [                                                       │
│            {"condition": "VIX > 25",                                       │
│             "action": {"SPY": 0.4, "TLT": 0.4, "CASH": 0.2}}              │
│        ],                                                                   │
│        "period": "2021-01-01 to 2026-01-01"                                │
│    }                                                                        │
│                                                                             │
│  LLM DOES NOT: Make any trade decisions                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATA AGENT: Prepare Historical Data                                        │
│                                                                             │
│  • Fetch: SPY, TLT prices (2021-2026)                                      │
│  • Fetch: VIX levels (for TAA trigger evaluation)                          │
│  • Ensure: Point-in-time data (no future data leakage)                    │
│                                                                             │
│  Returns: DataFrame with all required time series                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKTEST AGENT: Execute Simulation                                         │
│                                                                             │
│  ⚠️  CRITICAL: This is PURE PYTHON. NO LLM IN THIS LOOP.                   │
│                                                                             │
│  class BacktestEngine:                                                      │
│      def run(self, config, historical_data) -> BacktestResult:             │
│          portfolio_value = initial_capital                                  │
│          weights = config.weights                                           │
│                                                                             │
│          for date in trading_days:                                          │
│              # 1. Check TAA rules (DETERMINISTIC)                          │
│              if self._taa_triggered(date, historical_data):                │
│                  weights = config.taa_rules.action_weights                 │
│                                                                             │
│              # 2. Check rebalance schedule (DETERMINISTIC)                 │
│              if self._should_rebalance(date, config):                      │
│                  self._rebalance(portfolio, weights)                       │
│                                                                             │
│              # 3. Update portfolio value with historical prices            │
│              portfolio_value = self._mark_to_market(portfolio, prices)     │
│                                                                             │
│          return BacktestResult(...)                                        │
│                                                                             │
│  NO DECISIONS BY LLM. ONLY RULE EXECUTION.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RISK MANAGER: Interpret Results                                            │
│                                                                             │
│  NOW LLM can work again:                                                   │
│  • Interpret backtest metrics                                               │
│  • Compare strategies                                                       │
│  • Explain where value was added/lost                                      │
│  • Generate human-readable report                                           │
│  • Add appropriate caveats                                                  │
│                                                                             │
│  LLM sees: Completed BacktestResult (past tense, already computed)        │
│  LLM does NOT see: Real-time decision points                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 📅 IMPLEMENTATION ROADMAP

## Phase 5.1: Foundation + Data Agent (Woche 1)

### Ziele:
- [ ] Multi-Agent Grundstruktur
- [ ] Data Agent mit Quant-fokussierten Tools
- [ ] Covariance Matrix Berechnung
- [ ] Risk Metrics (Volatility, Correlation)

### Deliverables:

```
src/
├── agents/
│   ├── base_agent.py           # BaseAgent
│   ├── risk_manager_agent.py   # Supervisor mit Risk Focus
│   ├── data_agent.py           # Quant Data Agent
│   └── protocols.py            # PortfolioTask, PortfolioResult
├── portfolio_tool/
│   ├── quant/                  # NEU
│   │   ├── __init__.py
│   │   ├── returns.py          # Return calculations
│   │   ├── covariance.py       # Covariance estimation
│   │   └── risk_metrics.py     # Vol, VaR, etc.
```

### Key Tools (Data Agent):

```python
@tool
def calculate_covariance_matrix(
    tickers: str,  # Comma-separated
    period: str = "5Y",
    method: str = "sample"  # "sample", "shrinkage", "exponential"
) -> Dict:
    """
    Calculate covariance matrix for portfolio optimization.
    
    Returns:
    - covariance_matrix: nested dict
    - correlation_matrix: for interpretation
    - annualized_volatilities: per asset
    - estimation_period: actual dates used
    """
    pass

@tool
def get_risk_free_rate() -> Dict:
    """Get current risk-free rate (10Y Treasury or similar)."""
    pass

@tool
def calculate_rolling_volatility(
    ticker: str,
    window: int = 30
) -> Dict:
    """Calculate rolling volatility for regime detection."""
    pass
```

---

## Phase 5.2: Optimization Agent + Prompt #1 (Woche 2)

### Ziele:
- [ ] Optimization Engine (PyPortfolioOpt oder scipy)
- [ ] Mean-Variance Optimization
- [ ] Risk Parity Implementation
- [ ] Efficient Frontier Generation
- [ ] End-to-End: Prompt #1 funktioniert

### Deliverables:

```
src/
├── agents/
│   └── optimization_agent.py   # NEU
├── portfolio_tool/
│   └── optimization/           # NEU
│       ├── __init__.py
│       ├── base.py             # OptimizerInterface
│       ├── mean_variance.py    # Markowitz
│       ├── risk_parity.py      # Risk Parity
│       └── constraints.py      # Constraint handling
```

### Optimization Engine Interface:

```python
class OptimizerInterface(ABC):
    """Interface for portfolio optimizers."""
    
    @abstractmethod
    def optimize(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        pass


class MeanVarianceOptimizer(OptimizerInterface):
    """Classic Markowitz mean-variance optimization."""
    
    def optimize(self, ...) -> OptimizationResult:
        # Using scipy.optimize or PyPortfolioOpt
        pass
    
    def max_sharpe(self, ...) -> OptimizationResult:
        """Find maximum Sharpe ratio portfolio."""
        pass
    
    def min_volatility(self, ...) -> OptimizationResult:
        """Find minimum volatility portfolio."""
        pass
    
    def efficient_frontier(self, n_points: int = 50) -> List[OptimizationResult]:
        """Generate efficient frontier."""
        pass


class RiskParityOptimizer(OptimizerInterface):
    """Risk parity / equal risk contribution."""
    
    def optimize(self, ...) -> OptimizationResult:
        # Iterative risk budgeting
        pass
```

### Constraints System:

```python
@dataclass
class PortfolioConstraints:
    """Investment mandate constraints."""
    
    # Return/Risk targets
    min_return: Optional[float] = None
    max_volatility: Optional[float] = None
    target_volatility: Optional[float] = None
    
    # Weight constraints
    min_weight: float = 0.0            # No shorting by default
    max_weight: float = 1.0            # No single asset > 100%
    asset_bounds: Dict[str, Tuple[float, float]] = None  # Per-asset limits
    
    # Sector constraints (future)
    max_sector_weight: Optional[float] = None
    
    def to_scipy_constraints(self) -> List[Dict]:
        """Convert to scipy.optimize format."""
        pass
```

---

## Phase 5.3: Backtest Agent + Prompt #3 (Woche 3)

### Ziele:
- [ ] Backtest Engine (DETERMINISTIC, no LLM)
- [ ] Performance Attribution
- [ ] Strategy Comparison
- [ ] End-to-End: Prompt #3 funktioniert

### Deliverables:

```
src/
├── agents/
│   └── backtest_agent.py       # NEU
├── portfolio_tool/
│   └── backtest/               # NEU
│       ├── __init__.py
│       ├── engine.py           # BacktestEngine (NO LLM!)
│       ├── strategies.py       # Strategy definitions
│       ├── metrics.py          # Performance metrics
│       └── reports.py          # Report generation
```

### Backtest Engine (Critical: No LLM):

```python
class BacktestEngine:
    """
    DETERMINISTIC backtest engine.
    
    ⚠️  CRITICAL: This class MUST NOT use any LLM.
    All decisions are based on pre-defined rules.
    Same inputs = Same outputs. Always.
    """
    
    def __init__(self, transaction_cost: float = 0.001):
        self.transaction_cost = transaction_cost
        # NO LLM initialization here
    
    def run(
        self,
        strategy: Strategy,
        historical_data: pd.DataFrame,
        initial_capital: float = 100_000
    ) -> BacktestResult:
        """
        Run backtest simulation.
        
        Args:
            strategy: Deterministic strategy definition
            historical_data: OHLCV + signals (e.g., VIX)
            initial_capital: Starting capital
        
        Returns:
            BacktestResult with full performance metrics
        """
        portfolio = Portfolio(initial_capital, strategy.initial_weights)
        daily_values = []
        
        for date, row in historical_data.iterrows():
            # 1. Evaluate TAA rules (DETERMINISTIC)
            if strategy.taa_rules:
                for rule in strategy.taa_rules:
                    if rule.evaluate(date, row):  # Pure boolean logic
                        portfolio.adjust_weights(rule.target_weights)
            
            # 2. Rebalancing check (DETERMINISTIC)
            if strategy.should_rebalance(date, portfolio):
                costs = portfolio.rebalance(row['prices'])
            
            # 3. Mark to market
            portfolio.update_values(row['prices'])
            daily_values.append(portfolio.total_value)
        
        return self._calculate_metrics(daily_values, historical_data.index)
    
    def _calculate_metrics(self, values, dates) -> BacktestResult:
        """Calculate all performance metrics."""
        returns = pd.Series(values).pct_change().dropna()
        
        return BacktestResult(
            total_return=(values[-1] / values[0]) - 1,
            cagr=self._cagr(values, len(dates)),
            volatility=returns.std() * np.sqrt(252),
            sharpe_ratio=self._sharpe(returns),
            max_drawdown=self._max_drawdown(values),
            calmar_ratio=self._calmar(values),
            # ... more metrics
        )
```

### Strategy Definition (Rule-Based, No LLM):

```python
@dataclass
class TAARule:
    """Tactical allocation rule - purely deterministic."""
    
    name: str
    condition: str              # "VIX > 25" - parsed to function
    target_weights: Dict[str, float]
    
    def evaluate(self, date: datetime, market_data: pd.Series) -> bool:
        """
        Evaluate if rule triggers.
        MUST be deterministic. No LLM.
        """
        # Parse condition and evaluate against market_data
        # e.g., market_data['VIX'] > 25
        return self._evaluate_condition(market_data)


@dataclass
class Strategy:
    """Complete strategy definition."""
    
    name: str
    initial_weights: Dict[str, float]
    rebalance_frequency: str          # "monthly", "quarterly"
    rebalance_threshold: float = 0.05  # Drift threshold
    taa_rules: List[TAARule] = None
    
    def should_rebalance(self, date: datetime, portfolio: Portfolio) -> bool:
        """Check if rebalancing needed. Deterministic."""
        # Check calendar
        if self.rebalance_frequency == "quarterly":
            if date.month not in [3, 6, 9, 12]:
                return False
        
        # Check drift
        max_drift = portfolio.calculate_drift(self.initial_weights)
        return max_drift > self.rebalance_threshold
```

---

## Phase 5.4: Macro/RAG Agent + Prompt #2 (Woche 4)

### Ziele:
- [ ] RAG Pipeline für Fed Minutes
- [ ] Sentiment Extraction
- [ ] Regime Signal Generation
- [ ] TAA Integration
- [ ] End-to-End: Prompt #2 funktioniert

### Deliverables:

```
src/
├── agents/
│   └── macro_agent.py          # NEU (evolved from RAG Agent)
├── portfolio_tool/
│   └── rag/
│       ├── __init__.py
│       ├── document_loader.py  
│       ├── chunker.py          # Optimized for Fed Minutes structure
│       ├── embeddings.py       
│       └── sentiment.py        # NEU: Sentiment scoring
```

### Macro Agent Specifics:

```python
class MacroAgent(BaseAgent):
    """
    Analyzes macro environment for TAA decisions.
    
    NOT for trade decisions - only for regime assessment
    that informs parameter settings.
    """
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "analyze_fed_minutes",
            "assess_market_regime", 
            "generate_taa_signal"
        ]
    
    async def analyze_fed_minutes(self, document_path: str) -> MacroSignal:
        """
        Extract sentiment and key themes from Fed Minutes.
        
        Returns:
        - sentiment_score: -1 (dovish) to +1 (hawkish)
        - key_themes: List of extracted topics
        - risk_assessment: "risk_on" | "risk_off" | "neutral"
        """
        pass
    
    async def generate_regime_signal(
        self,
        fed_sentiment: float,
        vix_level: float,
        yield_curve: float
    ) -> RegimeSignal:
        """
        Combine multiple inputs into regime assessment.
        
        This informs TAA parameters, NOT direct trades.
        """
        pass
```

---

## Phase 5.5: Integration + Prompt #4 + Polish (Woche 5-6)

### Ziele:
- [ ] Prompt #4 (Rebalancing) implementieren
- [ ] Alle Prompts End-to-End funktionierend
- [ ] Error Handling & Edge Cases
- [ ] Documentation & Demo
- [ ] Performance Optimization

### Final Demo Flow:

```
DEMO SCRIPT (5 minutes):

1. [1 min] SAA Optimization
   "Optimiere ein Portfolio mit max 12% Volatilität"
   → Zeigt: Efficient Frontier, Weights, Comparison

2. [1.5 min] TAA with Macro
   "Analysiere Fed Minutes und aktuelles VIX für TAA"
   → Zeigt: RAG extraction, Regime signal, Adjustment

3. [1.5 min] Backtesting  
   "Backteste diese Strategie über 5 Jahre"
   → Zeigt: Performance vs Benchmark, Drawdowns, Metrics
   → Betone: "No LLM in simulation - deterministic"

4. [1 min] Rebalancing
   "Portfolio ist gedriftet - soll ich rebalancen?"
   → Zeigt: Drift analysis, Tax-aware recommendation
```

---

# ⚠️ RISIKEN & TESTING-FOKUS (Quant-Spezifisch)

## 1. Look-Ahead Bias im Backtest

**Das wichtigste Risiko für Quant-Credibility.**

```
PROBLEM:
LLM wird 2024 trainiert, "weiß" dass 2022 ein schlechtes Jahr war.
Wenn LLM Trade-Entscheidungen im Backtest trifft → Bias.

LÖSUNG (bereits im Design):
• BacktestEngine ist reines Python, KEIN LLM
• LLM nur: (1) Parse user intent → rules, (2) Interpret results
• Alle Entscheidungen durch deterministische Regeln

TESTS:
• [ ] Same config + same data = IDENTICAL results (100 runs)
• [ ] LLM temperature=0 für rule parsing
• [ ] Audit log zeigt keine LLM calls während simulation
```

## 2. Covariance Estimation Instabilität

```
PROBLEM:
Sample covariance mit kurzen Perioden → instabile Optimierung.
Extreme Weights (99% in einem Asset) möglich.

LÖSUNG:
• Shrinkage Estimators (Ledoit-Wolf)
• Minimum weight constraints (z.B. 5%)
• Maximum weight constraints (z.B. 40%)
• Warnung wenn Condition Number hoch

TESTS:
• [ ] Optimization mit synthetischen edge cases
• [ ] Extreme correlation scenarios (0.99, -0.99)
• [ ] Short history (< 60 data points) handling
```

## 3. Overfitting in TAA Rules

```
PROBLEM:
User definiert "VIX > 25 → Risk Off" - was wenn das nur in-sample gut war?

LÖSUNG:
• Backtest zeigt Out-of-Sample period separat
• Warnung bei zu vielen/komplexen TAA Rules
• Monte Carlo für Rule Robustness (optional)

TESTS:
• [ ] Same strategy, different time periods
• [ ] Random rule (baseline) comparison
```

## 4. RAG Hallucination bei Macro Signals

```
PROBLEM:
LLM "erfindet" Fed-Aussagen die nicht im Dokument sind.

LÖSUNG:
• Strict citation requirement (page numbers)
• Confidence scores für extractions
• Human-readable audit trail

TESTS:
• [ ] Golden dataset: Known Fed Minutes with verified extractions
• [ ] Adversarial: Ask about topics NOT in document
```

---

# 📊 SUCCESS CRITERIA

## Minimum Viable Product (MVP)

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Prompt #1 (SAA) Success | >95% | Optimization converges, constraints satisfied |
| Prompt #2 (TAA) Success | >85% | Regime correctly identified |
| Prompt #3 (Backtest) Success | 100% | Deterministic, reproducible |
| Prompt #4 (Rebalance) Success | >90% | Correct drift calculation |
| Look-Ahead Bias | 0 instances | Audit log verification |
| Backtest Reproducibility | 100% | Same input = same output |

## Interview Readiness

| Requirement | Status |
|-------------|--------|
| SAA Demo: Efficient Frontier + Weights | ⬜ |
| TAA Demo: Fed Minutes → Signal | ⬜ |
| Backtest Demo: Strategy vs Benchmark | ⬜ |
| Explain "No Look-Ahead Bias" | ⬜ |
| Explain Covariance Estimation | ⬜ |
| README with Architecture Diagram | ⬜ |
| Sample Fed Minutes PDF | ⬜ |

---

# 🚀 NEXT STEPS

**Immediate Action:** Start Phase 5.1 - Foundation + Data Agent

Week 1, Day 1:
1. Create `src/portfolio_tool/quant/` module
2. Implement `covariance.py` with shrinkage estimators
3. Create `PortfolioTask` and `PortfolioResult` DTOs
4. Write tests for covariance estimation

Soll ich mit der Implementierung beginnen?

