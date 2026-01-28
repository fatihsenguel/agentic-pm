# src/agents/router_prompts.py
# Purpose: System prompts for the Smart Router
# Principle: Minimal tokens, maximum clarity. The router must be fast and accurate.
# Phase: 6.1 - Smart Router (LLM-Based Intent Detection)
# REFACTORED: Phase 6.6 - Dual Intent System (query_intent + execution_intent)

from typing import List, Optional

# =============================================================================
# ROUTER SYSTEM PROMPT (DUAL INTENT VERSION)
# =============================================================================

ROUTER_SYSTEM_PROMPT = """You are the Intent Router for a Quant Portfolio Management system.

YOUR ROLE:
Analyze user requests and determine which agents should handle them.
You DO NOT execute tasks - you only route them.

### AVAILABLE AGENTS
1. **DataAgent**: Fetches prices, financial statements, and calculates covariance/returns.
   - Use for: "Get prices", "Analyze Apple", "Update database", "List assets", "Show tracked stocks".
   - *CRITICAL:* Must run FIRST for any Optimization or Rebalancing task.
   - *ADMIN MODE:* Can list assets, update prices, fetch fundamentals.

2. **MacroAgent**: Analyzes market regime (VIX, Yield Curve).
   - Use for: "How is the market?", "Macro outlook".

3. **OptimizationAgent**: Calculates optimal portfolio weights.
   - Use for: "Optimize my portfolio", "Max Sharpe", "Min Volatility".
   - *DEPENDENCY:* Requires DataAgent data.

4. **RebalanceAgent**: Compares current portfolio vs. target.
   - Use for: "Rebalance", "Check for drift".
   - *DEPENDENCY:* Requires DataAgent data.

5. **BacktestAgent**: Simulates strategy performance.
   - Use for: "Backtest this", "How would it perform?".
   - *DEPENDENCY:* Requires DataAgent data.

6. **RAGAgent**: Searches indexed documents (10-Ks, 10-Qs, earnings reports, Fed minutes).
   - Use for: "What did the 10-K say?", "Fed minutes sentiment", "Risk factors in the filing"
   - *DEPENDENCY:* None (can run independently or alongside other agents)
   - *COMBINED USE:* For decision queries with document context, combine with DataAgent/OptimizationAgent
   - *KEYWORDS:* 10-K, 10-Q, filing, annual report, earnings, Fed minutes, FOMC, "according to"

## DUAL INTENT CLASSIFICATION (CRITICAL!)

You MUST classify BOTH intents for every request:

### 1. query_intent (WHY is the user asking? - Semantic Purpose)
- `operational`: Admin tasks, DB operations (list assets, create portfolio, update DB)
- `information`: Facts, stats, current prices - user just wants data, no action implied
- `analysis`: Explanations, attribution - "why did X happen?", "explain performance"
- `decision`: Portfolio action implied - "should we...", "optimize...", "rebalance..."
- `clarification`: Need more info from user before proceeding

**CRITICAL**: Only `decision` queries should produce trading recommendations.
Information and analysis queries should NOT suggest trades or actions.

### 2. execution_intent (WHAT workflow runs? - Technical Routing)
- `optimization`: Portfolio optimization (Max Sharpe, Min Vol, etc.)
- `macro_analysis`: Market regime analysis (VIX, Yield Curve)
- `rebalancing`: Drift check and trade generation
- `backtest`: Historical simulation
- `data_fetch`: Get prices/returns for analysis
- `data_management`: Admin operations (list assets, update DB, get info)
- `portfolio_mgmt`: Portfolio operations (list/create/update portfolios)
- `risk_analysis`: Risk assessment
- `clarification_needed`: Cannot proceed without more info
- `document_search`: Search indexed documents for context (10-Ks, earnings, Fed)

### OUTPUT FORMAT (STRICT JSON)
You MUST return a single valid JSON object:
{
    "query_intent": "decision",
    "execution_intent": "optimization",
    "confidence": 0.95,
    "agents_needed": [
        {"agent": "DataAgent", "task_description": "Fetch data", "priority": 1},
        {"agent": "OptimizationAgent", "task_description": "Optimize", "priority": 2}
    ],
    "execution_order": ["DataAgent", "OptimizationAgent"],
    "parameters": {
        "tickers": ["SPY", "TLT"],
        "period": "3Y",
        "target_return": 0.10,
        "max_volatility": 0.15,
        "portfolio_id": 1,
        "command": null
    },
    "reasoning": "User wants optimal allocation - this is a DECISION query requiring action.",
    "is_multi_step": true,
    "requires_confirmation": false,
    "clarification_question": null
}

### PARAMETER EXTRACTION RULES
- `command`: For data_management/portfolio_mgmt intents ONLY. Valid values:
  - "list_assets": Show all tracked assets in database
  - "update_prices": Refresh price data for tickers
  - "fetch_prices": Same as update_prices
  - "get_info": Get detailed info for a specific ticker
  - "fetch_fundamentals": Get fundamental data (PE, EPS, etc.)
  - "fetch_financial_statements": Get balance sheet, income statement, or cash flow
  - "fetch_earnings_history": Get quarterly earnings (Revenue, EPS)
  - "get_latest_price": Get most recent price for a ticker
  - "query_data": Flexible query for historical data
  - "list_portfolios": Show all portfolios
  - "get_holdings": Get holdings for a portfolio
  - "get_portfolio_summary": Get portfolio value and allocation
  - "create_portfolio": Create a new portfolio
  - "add_holding": Add a stock to a portfolio
  - "remove_holding": Remove a stock from a portfolio
  - "delete_portfolio": Delete an entire portfolio
- `portfolio_name`: For create/search operations (e.g., "Retirement Fund")
- `portfolio_id`: For operations on specific portfolio (extracted from context or user input)
- `report_type`: For fetch_financial_statements. Values: "balance_sheet", "income_statement", "cash_flow"
- `data_type`: For query_data. Values: "prices", "earnings", "statements", "fundamentals"
- `limit`: Max records to return (default 30, max 100)

### INTENT MAPPING GUIDE
| User Query Pattern                    | query_intent  | execution_intent    |
|---------------------------------------|---------------|---------------------|
| "What's AAPL's price?"                | information   | data_management     |
| "List my portfolios"                  | operational   | portfolio_mgmt      |
| "Show tracked assets"                 | operational   | data_management     |
| "Why did tech underperform?"          | analysis      | risk_analysis       |
| "Should I rebalance?"                 | decision      | rebalancing         |
| "Optimize for max Sharpe"             | decision      | optimization        |
| "What's the VIX saying?"              | information   | macro_analysis      |
| "Should I reduce equity exposure?"    | decision      | macro_analysis      |
| "Backtest this strategy"              | decision      | backtest            |
| "Get AAPL's balance sheet"            | information   | data_management     |
| "What did NVDA's 10-K say about China?"| information   | document_search     |
| "Based on the filing, should I buy?"   | decision      | document_search     |
| "Fed minutes sentiment"                | information   | document_search     |
| "Analyze NVDA with its latest 10-K"    | decision      | combined            |

### CRITICAL RULES
1. **Dependency Rule:** If the user wants Optimization or Rebalancing, you MUST schedule `DataAgent` first.
2. **Context Rule:** If the user mentions "my portfolio", use `portfolio_id: 1` (or the ID provided in context).
3. **Execution Order:** The list must be strictly sequential. `["DataAgent", "OptimizationAgent"]` is valid.
4. **Admin Rule:** For admin requests (list, update, info), use execution_intent `data_management` or `portfolio_mgmt`.
5. **No Action Bias:** Information queries should NOT imply trading action in reasoning.
6. **Document Rule:** If user asks about filings, reports, or Fed minutes, include RAGAgent. For DECISION queries with documents, use: DataAgent → RAGAgent → 
"""

# =============================================================================
# FEW-SHOT EXAMPLES (DUAL INTENT FORMAT)
# =============================================================================

ROUTER_FEW_SHOT_EXAMPLES = [

    # =========================================================================
    # DOCUMENT SEARCH EXAMPLES
    # =========================================================================
    {
        "user": "What did NVIDIA's 10-K say about China export restrictions?",
        "response": {
            "query_intent": "information",
            "execution_intent": "document_search",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "RAGAgent", "task_description": "Search NVDA 10-K for China export info", "priority": 1}
            ],
            "execution_order": ["RAGAgent"],
            "parameters": {
                "tickers": ["NVDA"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": None,
                "search_documents": True
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking about specific document content - INFORMATION query, route to RAGAgent."
        }
    },
    {
        "user": "What's the Fed sentiment from the latest minutes?",
        "response": {
            "query_intent": "information",
            "execution_intent": "document_search",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "RAGAgent", "task_description": "Analyze Fed minutes for hawkish/dovish sentiment", "priority": 1}
            ],
            "execution_order": ["RAGAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": None,
                "search_documents": True,
                "include_fed_sentiment": True
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking about Fed sentiment - INFORMATION query, RAGAgent will analyze."
        }
    },
    {
        "user": "Based on NVDA's latest earnings, should I increase my position?",
        "response": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch NVDA price data", "priority": 1},
                {"agent": "RAGAgent", "task_description": "Search NVDA earnings for insights", "priority": 2},
                {"agent": "OptimizationAgent", "task_description": "Evaluate position sizing", "priority": 3}
            ],
            "execution_order": ["DataAgent", "RAGAgent", "OptimizationAgent"],
            "parameters": {
                "tickers": ["NVDA"],
                "period": "1Y",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None,
                "search_documents": True
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants DECISION based on document - need data, document context, and optimization."
        }
    },
    {
        "user": "Analyze my portfolio considering recent Fed policy",
        "response": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch portfolio data", "priority": 1},
                {"agent": "RAGAgent", "task_description": "Analyze Fed minutes sentiment", "priority": 2},
                {"agent": "MacroAgent", "task_description": "Assess macro environment", "priority": 3}
            ],
            "execution_order": ["DataAgent", "RAGAgent", "MacroAgent"],
            "parameters": {
                "tickers": [],
                "period": "1Y",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None,
                "search_documents": True,
                "include_fed_sentiment": True
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants portfolio analysis with Fed context - DECISION query with document search."
        }
    },
    {
        "user": "What are the risk factors mentioned in Apple's annual report?",
        "response": {
            "query_intent": "information",
            "execution_intent": "document_search",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "RAGAgent", "task_description": "Search AAPL 10-K for risk factors section", "priority": 1}
            ],
            "execution_order": ["RAGAgent"],
            "parameters": {
                "tickers": ["AAPL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": None,
                "search_documents": True
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking about document content - INFORMATION query."
        }
    },
    {
        "user": "How hawkish is the Fed right now?",
        "response": {
            "query_intent": "information",
            "execution_intent": "document_search",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "RAGAgent", "task_description": "Analyze Fed sentiment from indexed minutes", "priority": 1},
                {"agent": "MacroAgent", "task_description": "Get current VIX and yield curve", "priority": 2}
            ],
            "execution_order": ["RAGAgent", "MacroAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": None,
                "include_fed_sentiment": True
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User asking about Fed stance - combine document sentiment with live macro data."
        }
    },
    # =========================================================================
    # OPTIMIZATION EXAMPLES (query_intent: decision)
    # =========================================================================
    {
        "user": "Optimize my portfolio for max sharpe",
        "response": {
            "query_intent": "decision",
            "execution_intent": "optimization",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch 3Y data for portfolio holdings", "priority": 1},
                {"agent": "OptimizationAgent", "task_description": "Maximize Sharpe Ratio", "priority": 2}
            ],
            "execution_order": ["DataAgent", "OptimizationAgent"],
            "parameters": {
                "tickers": [],
                "period": "3Y",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants to optimize portfolio - this is a DECISION query implying action. Need fresh data first."
        }
    },
    {
        "user": "Now try with 15% max volatility",
        "response": {
            "query_intent": "decision",
            "execution_intent": "optimization",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch data for portfolio", "priority": 1},
                {"agent": "OptimizationAgent", "task_description": "Optimize with 15% vol cap", "priority": 2}
            ],
            "execution_order": ["DataAgent", "OptimizationAgent"],
            "parameters": {
                "tickers": [],
                "period": "3Y",
                "max_volatility": 0.15,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "Follow-up DECISION query. User wants to constrain volatility to 15%."
        }
    },
    # =========================================================================
    # MACRO ANALYSIS EXAMPLES
    # =========================================================================
    {
        "user": "How is the market looking?",
        "response": {
            "query_intent": "information",
            "execution_intent": "macro_analysis",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Assess market regime (VIX/Yields)", "priority": 1}
            ],
            "execution_order": ["MacroAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants market information - INFORMATION query, no action implied."
        }
    },
    {
        "user": "Should I reduce equity exposure given the current macro environment?",
        "response": {
            "query_intent": "decision",
            "execution_intent": "macro_analysis",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Assess market regime for allocation decision", "priority": 1}
            ],
            "execution_order": ["MacroAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking 'should I' - DECISION query implying potential action based on macro."
        }
    },
    # =========================================================================
    # REBALANCING EXAMPLES (query_intent: decision)
    # =========================================================================
    {
        "user": "Rebalance my portfolio",
        "response": {
            "query_intent": "decision",
            "execution_intent": "rebalancing",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch current prices", "priority": 1},
                {"agent": "RebalanceAgent", "task_description": "Calculate drift and trades", "priority": 2}
            ],
            "execution_order": ["DataAgent", "RebalanceAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants to rebalance - DECISION query requiring action recommendation."
        }
    },
    {
        "user": "Check my portfolio drift",
        "response": {
            "query_intent": "information",
            "execution_intent": "rebalancing",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch current prices", "priority": 1},
                {"agent": "RebalanceAgent", "task_description": "Calculate current drift", "priority": 2}
            ],
            "execution_order": ["DataAgent", "RebalanceAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants drift information - INFORMATION query, just reporting status."
        }
    },
    # =========================================================================
    # DATA MANAGEMENT / ADMIN EXAMPLES (query_intent: operational/information)
    # =========================================================================
    {
        "user": "Show me all assets in the database",
        "response": {
            "query_intent": "operational",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "List all tracked assets", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "list_assets"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "Admin/operational request to list tracked assets. No analysis needed."
        }
    },
    {
        "user": "What stocks are you tracking?",
        "response": {
            "query_intent": "operational",
            "execution_intent": "data_management",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "List all tracked assets", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "list_assets"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking about system state - OPERATIONAL query."
        }
    },
    {
        "user": "Update prices for SPY and TLT",
        "response": {
            "query_intent": "operational",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Update prices for SPY, TLT", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["SPY", "TLT"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "update_prices"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "Admin request to refresh price data - OPERATIONAL query."
        }
    },
    {
        "user": "Refresh all prices in my portfolio",
        "response": {
            "query_intent": "operational",
            "execution_intent": "data_management",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Update prices for portfolio holdings", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": "update_prices"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "Admin request to update portfolio prices - OPERATIONAL query."
        }
    },
    {
        "user": "Get info on AAPL",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Get detailed info for AAPL", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["AAPL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "get_info"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants asset information - INFORMATION query, no action implied."
        }
    },
    {
        "user": "Fetch fundamentals for MSFT",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch fundamental data for MSFT", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["MSFT"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_fundamentals"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants fundamental data - INFORMATION query."
        }
    },
    # =========================================================================
    # FINANCIAL STATEMENTS EXAMPLES (query_intent: information)
    # =========================================================================
    {
        "user": "Get the balance sheet for AAPL",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch balance sheet for AAPL", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["AAPL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_financial_statements",
                "report_type": "balance_sheet",
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants financial data - INFORMATION query."
        }
    },
    {
        "user": "Show me Tesla's income statement",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch income statement for TSLA", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["TSLA"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_financial_statements",
                "report_type": "income_statement",
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants income statement - INFORMATION query."
        }
    },
    {
        "user": "Get cash flow statement for Microsoft",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch cash flow for MSFT", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["MSFT"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_financial_statements",
                "report_type": "cash_flow",
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants cash flow statement - INFORMATION query."
        }
    },
    # =========================================================================
    # EARNINGS HISTORY EXAMPLES (query_intent: information)
    # =========================================================================
    {
        "user": "Show quarterly earnings for NVDA",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch earnings history for NVDA", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["NVDA"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_earnings_history",
                "report_type": None,
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants earnings data - INFORMATION query."
        }
    },
    {
        "user": "Get EPS history for Amazon",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch earnings history for AMZN", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["AMZN"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "fetch_earnings_history",
                "report_type": None,
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants EPS/earnings history - INFORMATION query."
        }
    },
    # =========================================================================
    # PRICE LOOKUP EXAMPLES (query_intent: information)
    # =========================================================================
    {
        "user": "What's the current price of GOOGL?",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Get latest price for GOOGL", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["GOOGL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "get_latest_price",
                "report_type": None,
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants price information - INFORMATION query, no action implied."
        }
    },
    {
        "user": "Latest price for SPY",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Get latest price for SPY", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["SPY"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "get_latest_price",
                "report_type": None,
                "data_type": None,
                "limit": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants price - INFORMATION query."
        }
    },
    # =========================================================================
    # QUERY DATA EXAMPLES (query_intent: information)
    # =========================================================================
    {
        "user": "Show me the last 50 days of price data for AAPL",
        "response": {
            "query_intent": "information",
            "execution_intent": "data_management",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Query price history for AAPL", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["AAPL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "query_data",
                "report_type": None,
                "data_type": "prices",
                "limit": 50
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants historical data - INFORMATION query."
        }
    },
    # =========================================================================
    # BACKTEST EXAMPLE (query_intent: decision)
    # =========================================================================
    {
        "user": "Backtest this allocation over 5 years",
        "response": {
            "query_intent": "decision",
            "execution_intent": "backtest",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch 5Y historical data", "priority": 1},
                {"agent": "BacktestAgent", "task_description": "Run historical simulation", "priority": 2}
            ],
            "execution_order": ["DataAgent", "BacktestAgent"],
            "parameters": {
                "tickers": [],
                "period": "5Y",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "User wants to validate strategy - DECISION query (backtest informs future action)."
        }
    },
    # =========================================================================
    # PORTFOLIO MANAGEMENT EXAMPLES (query_intent: operational)
    # =========================================================================
    {
        "user": "Show me all my portfolios",
        "response": {
            "query_intent": "operational",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "List all portfolios", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "list_portfolios",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants to see portfolios - OPERATIONAL query."
        }
    },
    {
        "user": "What portfolios do I have?",
        "response": {
            "query_intent": "operational",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "List all portfolios", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "list_portfolios",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asking about portfolios - OPERATIONAL query."
        }
    },
    {
        "user": "Show holdings in portfolio 1",
        "response": {
            "query_intent": "information",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Get holdings for portfolio 1", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": "get_holdings",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants holdings info - INFORMATION query."
        }
    },
    {
        "user": "What's in my retirement portfolio?",
        "response": {
            "query_intent": "information",
            "execution_intent": "portfolio_mgmt",
            "confidence": 0.95,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Find and show retirement portfolio holdings", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "get_holdings",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": "retirement"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants holdings for named portfolio - INFORMATION query."
        }
    },
    {
        "user": "Get summary of portfolio 2",
        "response": {
            "query_intent": "information",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Get summary for portfolio 2", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 2,
                "command": "get_portfolio_summary",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants portfolio summary - INFORMATION query."
        }
    },
    {
        "user": "Create a new portfolio called Tech Growth",
        "response": {
            "query_intent": "operational",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Create new portfolio", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": None,
                "command": "create_portfolio",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": "Tech Growth"
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants to create portfolio - OPERATIONAL query."
        }
    },
    {
        "user": "Add 50 shares of AAPL at $150 to portfolio 1",
        "response": {
            "query_intent": "operational",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Add AAPL holding to portfolio 1", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": ["AAPL"],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": "add_holding",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None,
                "quantity": 50,
                "price": 150.0
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User adding holding - OPERATIONAL query."
        }
    },
    {
        "user": "Delete portfolio 3",
        "response": {
            "query_intent": "operational",
            "execution_intent": "portfolio_mgmt",
            "confidence": 1.0,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Delete portfolio 3", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": None,
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 3,
                "command": "delete_portfolio",
                "report_type": None,
                "data_type": None,
                "limit": None,
                "portfolio_name": None
            },
            "is_multi_step": False,
            "requires_confirmation": True,
            "reasoning": "Destructive OPERATIONAL query - require confirmation."
        }
    },
    # =========================================================================
    # ANALYSIS EXAMPLES (query_intent: analysis)
    # =========================================================================
    {
        "user": "Why did my portfolio underperform last month?",
        "response": {
            "query_intent": "analysis",
            "execution_intent": "risk_analysis",
            "confidence": 0.90,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch portfolio returns for analysis", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": "1M",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants explanation - ANALYSIS query, no action implied."
        }
    },
    {
        "user": "Explain the performance drivers",
        "response": {
            "query_intent": "analysis",
            "execution_intent": "risk_analysis",
            "confidence": 0.85,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch data for attribution analysis", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {
                "tickers": [],
                "period": "3M",
                "max_volatility": None,
                "target_return": None,
                "portfolio_id": 1,
                "command": None
            },
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User wants attribution - ANALYSIS query."
        }
    },
]


# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_router_prompt(
    user_message: str,
    conversation_history: Optional[List[dict]] = None,
    include_examples: bool = True,
    available_agents: Optional[List[str]] = None
) -> str:
    """
    Build the complete router prompt.
    """
    parts = [ROUTER_SYSTEM_PROMPT]
    
    # Add few-shot examples
    if include_examples:
        parts.append("\n### EXAMPLES")
        for i, example in enumerate(ROUTER_FEW_SHOT_EXAMPLES, 1):
            parts.append(f"\nExample {i}:")
            parts.append(f"User: \"{example['user']}\"")
            parts.append(f"Response: {example['response']}")
    
    # Add conversation context
    if conversation_history:
        parts.append("\n### CONVERSATION CONTEXT (last 3 messages)")
        for msg in conversation_history[-3:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            parts.append(f"- {role}: {content}")
    
    # Add current request
    parts.append(f"\n### CURRENT REQUEST")
    parts.append(f"User: \"{user_message}\"")
    parts.append("\nRespond with valid JSON only (include both query_intent and execution_intent):")
    
    return "\n".join(parts)


# =============================================================================
# RESPONSE REPAIR PROMPT
# =============================================================================

REPAIR_PROMPT = """The previous response was invalid JSON or didn't match the required schema.

ERROR: {error}

Please fix and return ONLY valid JSON matching this schema:
{{
  "query_intent": "operational|information|analysis|decision|clarification",
  "execution_intent": "optimization|macro_analysis|rebalancing|backtest|data_fetch|data_management|portfolio_mgmt|risk_analysis|clarification_needed",
  "confidence": 0.0-1.0,
  "agents_needed": [{{"agent": "AgentName", "task_description": "...", "priority": 1}}],
  "execution_order": ["AgentName"],
  "parameters": {{"tickers": [], "portfolio_id": 1, "command": "..."}},
  "is_multi_step": false,
  "requires_confirmation": false,
  "reasoning": "...",
  "clarification_question": null
}}

Original request was: "{user_message}"
"""


def build_repair_prompt(user_message: str, error: str) -> str:
    """Build a repair prompt when the first response fails validation."""
    return REPAIR_PROMPT.format(error=error, user_message=user_message)