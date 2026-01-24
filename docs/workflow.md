Excellent question! This is **crucial** for long-term maintainability. Let me give you a comprehensive workflow guide based on your project's architecture.

---

## 🔄 **Typical Development Workflow**

### **Scenario-Based Guide: "Query doesn't work as expected"**

Let me walk through different scenarios and show you exactly which files to modify:

---

## 📋 **SCENARIO 1: Router Misunderstands User Intent**

**Example:** User says "How risky is my portfolio?" but router thinks it's a data request instead of optimization.

### **Diagnosis Steps:**

1. **Check router decision:**
```python
decision, validation = await router.route("How risky is my portfolio?")
print(f"Intent: {decision.intent}")
print(f"Agents: {decision.agents_needed}")
print(f"Confidence: {decision.confidence}")
```

2. **If intent is wrong, the issue is in the router prompt**

### **Files to Modify:**

**📄 `src/agents/router_prompts.py`** ← **PRIMARY FIX**

```python
# Add/improve examples in ROUTER_EXAMPLES

ROUTER_EXAMPLES = [
    # ... existing examples
    
    # ⭐ ADD THIS
    {
        "user_message": "How risky is my portfolio?",
        "correct_decision": {
            "intent": "risk_analysis",
            "agents_needed": ["DataAgent", "RiskManagerAgent"],
            "execution_order": ["DataAgent", "RiskManagerAgent"],
            "parameters": {"period": "1Y"}
        }
    }
]
```

**Why this file?**
- Router uses LLM + examples to learn patterns
- More/better examples → better routing
- No code changes needed, just prompt engineering

**📄 `src/agents/schemas.py`** ← **If new intent type needed**

```python
class IntentType(str, Enum):
    # ... existing intents
    RISK_ANALYSIS = "risk_analysis"  # ⭐ ADD if doesn't exist
```

**Testing:**
```bash
python -c "from agents.smart_router import SmartRouter; import asyncio; asyncio.run(SmartRouter().route('How risky is my portfolio?'))"
```

---

## 📋 **SCENARIO 2: Agent Produces Wrong Results**

**Example:** OptimizationAgent suggests 100% in one stock (violates constraints)

### **Diagnosis Steps:**

1. **Check agent output:**
```python
result = await optimization_agent.arun("Optimize SPY, TLT, GLD")
print(result["data"]["weights"])  # {"SPY": 1.0, "TLT": 0.0, "GLD": 0.0} ← WRONG!
```

2. **If constraints are violated, issue is in the tool or config**

### **Files to Modify:**

**📄 `src/config.py`** ← **FIRST CHECK** (most common fix)

```python
@dataclass
class OptimizationConfig:
    default_max_weight: float = 0.40  # ← Change this if constraint is wrong
    default_min_weight: float = 0.10  # ← Add minimum weights
```

**📄 `src/portfolio_tool/tools/optimization_tools.py`** ← **If config is correct but still wrong**

```python
def optimize_portfolio_max_sharpe(
    tickers: List[str],
    period: str = "3Y",
    max_weight: float = 0.40,  # ← This should use config.optimization.default_max_weight
):
    # Check if constraint is properly applied
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
        {'type': 'ineq', 'fun': lambda x: max_weight - x},  # ← Verify this
    ]
```

**📄 `src/agents/prompts.py`** ← **If agent doesn't call tool with right params**

```python
OPTIMIZATION_AGENT_PROMPT = """
You are an expert portfolio optimizer.

When calling optimize_portfolio_max_sharpe, you MUST:
1. Use max_weight parameter to enforce diversification  # ⭐ ADD THIS
2. Verify weights sum to 1.0
3. Check no weight exceeds max_weight
"""
```

**Testing:**
```bash
python -c "from portfolio_tool.tools.optimization_tools import optimize_portfolio_max_sharpe; print(optimize_portfolio_max_sharpe(['SPY','TLT','GLD']))"
```

---

## 📋 **SCENARIO 3: System Too Slow**

**Example:** Queries take 30+ seconds

### **Diagnosis Steps:**

1. **Check where time is spent:**
```python
from observability.tracer import get_tracer

tracer = get_tracer()
# Check tracer output to see which agent/tool is slow
```

2. **Common culprits:**
   - Data fetching (YFinance)
   - LLM calls (too many retries)
   - Database queries

### **Files to Modify:**

**📄 `src/config.py`** ← **Quick wins**

```python
@dataclass
class DataConfig:
    trading_days_per_year: int = 252
    min_observations: int = 60  # ← Reduce if you're fetching too much historical data
    default_period: str = "1Y"  # ← Change from "3Y" to "1Y" for faster queries
```

**📄 `src/agents/smart_router.py`** ← **If router is slow**

```python
class RouterConfig:
    use_stronger_model: bool = False  # ← Use GPT-3.5 instead of GPT-4 for routing
    max_retries: int = 1  # ← Reduce from 2
```

**📄 `src/portfolio_tool/providers/yfinance_provider.py`** ← **If data fetching is slow**

```python
def fetch_prices(self, tickers, start_date, end_date):
    # Add caching
    cache_key = f"{tickers}_{start_date}_{end_date}"
    if cache_key in self._cache:  # ⭐ ADD CACHING
        return self._cache[cache_key]
    
    data = yf.download(tickers, start=start_date, end=end_date, threads=True)  # ⭐ ADD threads=True
    self._cache[cache_key] = data
    return data
```

---

## 📋 **SCENARIO 4: Need to Add New Capability**

**Example:** You want to add "tax-loss harvesting" analysis

### **Step-by-Step Workflow:**

#### **Step 1: Define the Intent** ← `schemas.py`

```python
class IntentType(str, Enum):
    # ... existing
    TAX_LOSS_HARVESTING = "tax_loss_harvesting"  # ⭐ ADD
```

#### **Step 2: Create the Tool** ← `src/portfolio_tool/tools/tax_tools.py` (NEW FILE)

```python
# Create new file: src/portfolio_tool/tools/tax_tools.py

def identify_tax_loss_opportunities(
    tickers: List[str],
    cost_basis: Dict[str, float],
    current_prices: Dict[str, float],
    tax_rate: float = 0.25
) -> Dict[str, Any]:
    """
    Identify securities with unrealized losses for tax-loss harvesting.
    
    PURE MATH - No LLM!
    """
    opportunities = []
    
    for ticker in tickers:
        if ticker in cost_basis and ticker in current_prices:
            loss = cost_basis[ticker] - current_prices[ticker]
            if loss > 0:
                tax_benefit = loss * tax_rate
                opportunities.append({
                    "ticker": ticker,
                    "unrealized_loss": loss,
                    "tax_benefit": tax_benefit
                })
    
    return {
        "success": True,
        "data": {
            "opportunities": opportunities,
            "total_tax_benefit": sum(o["tax_benefit"] for o in opportunities)
        }
    }
```

#### **Step 3: Create the Agent** ← `src/agents/tax_agent.py` (NEW FILE)

```python
# Create new file: src/agents/tax_agent.py

from agents.base_agent import BaseAgent
from agents.protocols import AgentConfig, AgentRole
from portfolio_tool.tools.tax_tools import identify_tax_loss_opportunities

class TaxAgent(BaseAgent):
    """Agent for tax optimization analysis."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Register tool
        self.tools = [identify_tax_loss_opportunities]
    
    async def _generate_response(self, request: str) -> str:
        # LLM orchestrates calling the tool
        # Similar pattern to other agents
        pass
```

#### **Step 4: Register Agent** ← `schemas.py`

```python
class AgentName(str, Enum):
    # ... existing
    TaxAgent = "TaxAgent"  # ⭐ ADD
```

#### **Step 5: Add to Router Examples** ← `router_prompts.py`

```python
ROUTER_EXAMPLES = [
    # ... existing
    {
        "user_message": "Should I harvest any tax losses?",
        "correct_decision": {
            "intent": "tax_loss_harvesting",
            "agents_needed": ["DataAgent", "TaxAgent"],
            "execution_order": ["DataAgent", "TaxAgent"]
        }
    }
]
```

#### **Step 6: Add to Graph** ← `src/agents/nodes.py` & `src/agents/graph.py`

```python
# In nodes.py
async def tax_agent_node(state: AgentState) -> AgentState:
    """Tax optimization analysis"""
    # Similar to other agent nodes
    pass

# In graph.py
from agents.nodes import tax_agent_node

def create_agent_graph():
    builder = StateGraph(AgentState)
    # ... existing nodes
    builder.add_node("tax_agent", tax_agent_node)  # ⭐ ADD
```

#### **Step 7: Add Config** ← `src/config.py`

```python
@dataclass
class TaxConfig:
    """Tax optimization settings"""
    capital_gains_rate: float = 0.25
    short_term_rate: float = 0.37
    wash_sale_days: int = 30
    min_loss_threshold: float = 100.0  # Minimum loss worth harvesting

@dataclass
class AppConfig:
    # ... existing
    tax: TaxConfig = field(default_factory=TaxConfig)  # ⭐ ADD
```

---

## 🎯 **FILE MODIFICATION HIERARCHY**

Here's the **decision tree** for which files to modify:

```
❓ What's wrong?
│
├─ 🤔 Router picks wrong intent
│  └─→ 📄 router_prompts.py (add examples)
│     └─→ 📄 schemas.py (add intent type if new)
│
├─ 🔧 Tool produces wrong results
│  └─→ 📄 config.py (check parameters)
│     └─→ 📄 tools/xxx_tools.py (fix math/logic)
│        └─→ 📄 agents/prompts.py (improve agent instructions)
│
├─ 🐌 System too slow
│  └─→ 📄 config.py (reduce data/retries)
│     └─→ 📄 providers/xxx_provider.py (add caching)
│        └─→ 📄 smart_router.py (use cheaper model)
│
├─ ➕ Need new capability
│  └─→ 📄 tools/new_tool.py (create tool - PURE MATH)
│     └─→ 📄 agents/new_agent.py (create agent)
│        └─→ 📄 schemas.py (add intent/agent enum)
│           └─→ 📄 router_prompts.py (add examples)
│              └─→ 📄 nodes.py + graph.py (add to workflow)
│                 └─→ 📄 config.py (add config section)
│
└─ 🔒 Need better validation
   └─→ 📄 schemas.py (add validators)
      └─→ 📄 agents/protocols.py (add DTOs)
```

---

## ⚠️ **CRITICAL RULES TO FOLLOW**

### **1. Separation of Concerns (NEVER VIOLATE!)**

```python
# ❌ WRONG - LLM doing math
async def optimize_portfolio(self, tickers):
    result = await self.llm.ainvoke("Calculate optimal weights for " + str(tickers))
    return result  # DISASTER! Non-deterministic!

# ✅ CORRECT - LLM orchestrates, tool does math
async def optimize_portfolio(self, tickers):
    tool_result = optimize_portfolio_max_sharpe(tickers)  # Pure scipy
    summary = await self.llm.ainvoke(f"Explain these weights: {tool_result}")
    return summary
```

### **2. Configuration Changes (Always use config.py)**

```python
# ❌ WRONG - Hardcoded
def fetch_data(tickers):
    period = "3Y"  # BAD! What if you want to change this?

# ✅ CORRECT - Config
from config import config

def fetch_data(tickers):
    period = config.data.default_period  # Single source of truth
```

### **3. State Management (Hot Potato Principle)**

```python
# ❌ WRONG - Passing raw DataFrame
state["prices_data"] = prices_df  # 10,000 rows → context explosion!

# ✅ CORRECT - Pass summary
state["shared_data"]["latest_prices"] = {
    "SPY": 450.0,
    "TLT": 88.0,
    "mean_return": 0.12
}
```

### **4. Adding New Agents (Follow the Pattern)**

**Every new agent needs:**
1. ✅ Tool file in `tools/` (pure math)
2. ✅ Agent file in `agents/` (orchestration)
3. ✅ Node function in `nodes.py`
4. ✅ Registration in `graph.py`
5. ✅ Enum in `schemas.py`
6. ✅ Examples in `router_prompts.py`
7. ✅ Config section in `config.py`

**Missing ANY of these = broken system!**

---

## 🧪 **Testing Workflow**

### **After ANY modification:**

```bash
# 1. Unit test the component
python -c "from xxx import yyy; print(yyy())"

# 2. Test the agent
python tests/test_xxx_agent.py

# 3. Test routing
python -c "from agents.smart_router import SmartRouter; import asyncio; asyncio.run(SmartRouter().route('test query'))"

# 4. Test end-to-end
python demos/langgraph_demo.py

# 5. Check logs for errors
tail -f logs/app.log
```

---

## 📊 **Common Modification Patterns**

| Goal | Primary File | Secondary Files | Test File |
|------|-------------|-----------------|-----------|
| **Fix wrong intent** | `router_prompts.py` | `schemas.py` | Manual routing test |
| **Fix wrong results** | `tools/xxx_tools.py` | `config.py` | `tests/test_tools.py` |
| **Change parameters** | `config.py` | None | All tests |
| **Add new agent** | `agents/new_agent.py` | `nodes.py`, `graph.py`, `schemas.py` | `tests/test_new_agent.py` |
| **Improve speed** | `config.py` | `providers/`, `smart_router.py` | Performance benchmark |
| **Better validation** | `schemas.py` | `agents/protocols.py` | `tests/test_schemas.py` |

---

## 🎯 **Your Development Checklist**

Before making ANY change, ask yourself:

1. **What layer am I modifying?**
   - Config? → `config.py`
   - Math? → `tools/`
   - Orchestration? → `agents/`
   - Routing? → `router_prompts.py`
   - Workflow? → `nodes.py`, `graph.py`

2. **Am I following SoC (Separation of Concerns)?**
   - ✅ Math in tools (pure functions)
   - ✅ LLM in agents (orchestration only)
   - ✅ Config in config.py (single source)
   - ✅ Prompts in prompts.py (not in code)

3. **Am I breaking backward compatibility?**
   - Adding optional fields? ✅ OK
   - Changing function signature? ⚠️ Careful
   - Removing fields? ❌ Don't do it

4. **Did I test the change in isolation?**
   - Unit test the function
   - Test the agent
   - Test end-to-end

---

## 💡 **Pro Tips**

1. **Start with examples** - Fix 90% of routing issues without code changes
2. **Config first** - Many "bugs" are just wrong config values
3. **Never skip tools** - Always create deterministic tool before adding agent
4. **Test incrementally** - Don't change 5 files before testing
5. **Check logs** - Enable tracing to see exactly what's happening
6. **Use git** - Commit after each working change

---

Does this workflow make sense? Should I create a **quick reference card** you can keep on your desk?