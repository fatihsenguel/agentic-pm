# 🚀 Agentic Finance - Development TODO List

**Last Updated:** 2026-01-11  
**Current Phase:** Phase 1B - Refactoring `data_manager.py`

---

## 📖 **Why Are We Doing This?**

### **The Problem:**
Your current `data_manager.py` methods return `None`. Agents can't work with `None` - they need **structured data** to understand:
- ✅ Did the operation succeed?
- ✅ How many records were affected?
- ✅ What was updated (tickers, indicators, documents)?
- ✅ If it failed, what was the error?

### **The Solution:**
Refactor all update methods to return `UpdateResult` objects. This makes your system **agent-ready**.

### **Example:**
```python
# BEFORE (Agent-hostile):
dm.update_prices_for_asset(asset)  
# Returns: None
# Agent thinks: "WTF happened? Did it work? How many records?"

# AFTER (Agent-friendly):
result = dm.update_prices_for_asset(asset)
# Returns: UpdateResult(success=True, affected_count=21, entities=["AAPL"])
# Agent thinks: "Great! 21 records updated for AAPL. Moving on..."
```

---

## 🎯 **Current Status**

### ✅ **Completed:**
- [x] Project structure cleaned and organized
- [x] Git initialized with proper `.gitignore`
- [x] Created `UpdateResult` and `QueryResult` classes
- [x] Comprehensive tests for response models
- [x] All tests passing
- [x] 2 commits made to git

### 🔄 **In Progress:**
- [ ] Refactor `update_prices_for_asset()` to return `UpdateResult`

### ⏳ **Not Started:**
- [x] Refactor remaining 4 update methods
- [ ] Create LangChain tool wrappers
- [ ] Build single-agent MVP

---

## 📅 **Phase 1B: Refactor Data Manager (THIS WEEK)**

### **Goal:** 
Make all data update methods return structured `UpdateResult` objects.

---

### **Task 1: Refactor `update_prices_for_asset()` [Priority: 🔥 CRITICAL]**

**Why:** This is your most important method - it's the foundation for everything else.

**Time Estimate:** 30-45 minutes

**Steps:**

1. **Add import at top of `data_manager.py`:**
```python
   from portfolio_tool.models import UpdateResult
```

2. **Change method signature:**
```python
   # FROM:
   def update_prices_for_asset(self, asset: Asset, start_date: date | None = None) -> None:
   
   # TO:
   def update_prices_for_asset(self, asset: Asset, start_date: date | None = None) -> UpdateResult:
```

3. **Wrap entire method logic in `try-except`:**
   - Keep ALL existing logic unchanged
   - Replace all `return` statements with `return UpdateResult(...)`
   - Add `except Exception as e:` block at the end

4. **Update `_perform_upsert` to return count:**
```python
   # FROM:
   def _perform_upsert(...):
       # ...
       self.session.commit()
       print(f"... {total_rows} Zeilen...")
   
   # TO:
   def _perform_upsert(...) -> int:
       # ...
       self.session.commit()
       print(f"... {total_rows} Zeilen...")
       return total_rows  # ← ADD THIS
```

5. **Use the returned count:**
```python
   affected_count = self._perform_upsert(
       model=DailyPrice,
       values=values_to_upsert,
       index_elements=['asset_id', 'date']
   )
```

6. **Return UpdateResult on success:**
```python
   return UpdateResult(
       success=True,
       operation="update_prices_for_asset",
       affected_count=affected_count,
       entities=[asset.ticker],
       entity_type="asset",
       date_range=(start_date, date.today()),
       metadata={"provider": "yfinance"}
   )
```

7. **Return UpdateResult on error:**
```python
   except Exception as e:
       return UpdateResult(
           success=False,
           operation="update_prices_for_asset",
           affected_count=0,
           entities=[asset.ticker],
           entity_type="asset",
           error_message=str(e)
       )
```

**Testing:**
```powershell
# Create test file: tests/test_data_manager_refactor.py
# (Code provided in previous conversation)

# Run test:
python tests\test_data_manager_refactor.py

# Should see:
# ✅ Returns UpdateResult (not None!)
# 🎉 SUCCESS! data_manager is agent-ready!
```

**Commit:**
```powershell
git add .
git commit -m "Refactor update_prices_for_asset to return UpdateResult"
```

---

### **Task 2: Refactor `update_fundamentals()` [Priority: 🟡 HIGH]**

**Why:** Fundamentals are needed for financial analysis agents.

**Time Estimate:** 15 minutes (you'll copy the pattern from Task 1)

**Steps:**

1. Find the `update_fundamentals()` method
2. Apply the SAME pattern as `update_prices_for_asset()`:
   - Change signature: `-> None` to `-> UpdateResult`
   - Wrap in `try-except`
   - Return `UpdateResult` on success
   - Return `UpdateResult` on error

**Template:**
```python
def update_fundamentals(self, asset: Asset) -> UpdateResult:
    """Updates fundamental data for an asset."""
    try:
        # === YOUR EXISTING LOGIC (don't change) ===
        
        affected = self._perform_upsert(...)
        
        return UpdateResult(
            success=True,
            operation="update_fundamentals",
            affected_count=affected,
            entities=[asset.ticker],
            entity_type="asset",
            metadata={"provider": "yfinance"}
        )
    except Exception as e:
        return UpdateResult(
            success=False,
            operation="update_fundamentals",
            affected_count=0,
            entities=[asset.ticker],
            entity_type="asset",
            error_message=str(e)
        )
```

**Testing:**
```python
# Add to tests/test_data_manager_refactor.py
def test_update_fundamentals():
    dm = DataManager()
    asset = session.query(Asset).filter_by(ticker="AAPL").first()
    result = dm.update_fundamentals(asset)
    assert isinstance(result, UpdateResult)
    print(f"✅ update_fundamentals returns {result.affected_count} records")
```

**Commit:**
```powershell
git add .
git commit -m "Refactor update_fundamentals to return UpdateResult"
```

---

### **Task 3: Refactor `update_earnings()` [Priority: 🟢 MEDIUM]**

**Why:** Earnings data is useful for comprehensive analysis.

**Time Estimate:** 15 minutes

**Steps:** Same pattern as Task 2

**Commit:**
```powershell
git commit -m "Refactor update_earnings to return UpdateResult"
```

---

### **Task 4: Refactor `update_shares_history()` [Priority: 🟢 MEDIUM]**

**Why:** Share changes affect market cap calculations.

**Time Estimate:** 15 minutes

**Steps:** Same pattern as Task 2

**Commit:**
```powershell
git commit -m "Refactor update_shares_history to return UpdateResult"
```

---

### **Task 5: Refactor `update_financial_statements()` [Priority: 🟢 MEDIUM]**

**Why:** Financial statements are needed for deep analysis.

**Time Estimate:** 15 minutes

**Steps:** Same pattern as Task 2

**Commit:**
```powershell
git commit -m "Refactor update_financial_statements to return UpdateResult"
```

---

### **✅ Phase 1B Complete Checklist:**

After completing all 5 tasks, verify:

- [ ] All 5 methods return `UpdateResult`
- [ ] `_perform_upsert()` returns `int` (count)
- [ ] All tests pass
- [ ] 5+ commits made to git
- [ ] No methods still return `None`

**Run comprehensive test:**
```powershell
# Test all refactored methods
python tests\test_data_manager_refactor.py
```

**Final commit:**
```powershell
git add .
git commit -m "Phase 1B complete: All data_manager methods return UpdateResult"
```

---

## 📅 **Phase 1C: Create LangChain Tools (NEXT WEEK)**

### **Goal:**
Wrap your refactored methods in LangChain `@tool` decorators so agents can use them.

**Time Estimate:** 2-3 hours

---

### **Task 6: Create First Tool - `fetch_stock_prices`**

**Why:** This proves the concept - one working tool validates the entire pattern.

**File:** `src/tools/data_tools.py`

**Steps:**

1. **Create the tool:**
```python
   from langchain.tools import tool
   from portfolio_tool.data_manager import DataManager
   from portfolio_tool.database_setup import Asset, get_session
   
   @tool
   def fetch_stock_prices(ticker: str, start_date: str = None) -> dict:
       """
       Fetch and update stock price data for a given ticker.
       
       Args:
           ticker: Stock ticker symbol (e.g., 'AAPL')
           start_date: Optional start date in YYYY-MM-DD format
       
       Returns:
           Dictionary with operation status and metadata
       """
       dm = DataManager()
       session = get_session()
       
       # Get or create asset
       asset = session.query(Asset).filter_by(ticker=ticker).first()
       if not asset:
           asset = Asset(ticker=ticker, name=ticker)
           session.add(asset)
           session.commit()
       
       # Call refactored method
       from datetime import datetime
       start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
       result = dm.update_prices_for_asset(asset, start_date=start)
       
       # Return as dict for agent
       return result.to_dict()
```

2. **Test the tool manually:**
```python
   # tests/test_tools.py
   from tools.data_tools import fetch_stock_prices
   
   def test_fetch_stock_prices_tool():
       result = fetch_stock_prices.invoke({"ticker": "AAPL"})
       print(f"Tool returned: {result}")
       assert result["success"] == True
       assert "AAPL" in result["entities"]
```

3. **Run:**
```powershell
   python tests\test_tools.py
```

**Expected Output:**
```
Tool returned: {
    'success': True, 
    'operation': 'update_prices_for_asset',
    'affected_count': 21,
    'entities': ['AAPL'],
    'entity_type': 'asset',
    ...
}
✅ Tool works!
```

**Commit:**
```powershell
git add .
git commit -m "Create first LangChain tool: fetch_stock_prices"
```

---

### **Task 7: Create Additional Tools**

**Why:** More tools = more capabilities for agents.

**Time Estimate:** 10 minutes per tool

**Tools to create:**

1. **`fetch_fundamentals`** - Wraps `update_fundamentals()`
2. **`fetch_earnings`** - Wraps `update_earnings()`
3. **`fetch_financial_statements`** - Wraps `update_financial_statements()`

**Pattern (copy for each tool):**
```python
@tool
def fetch_fundamentals(ticker: str) -> dict:
    """Fetch fundamental data for a stock."""
    dm = DataManager()
    session = get_session()
    asset = session.query(Asset).filter_by(ticker=ticker).first()
    result = dm.update_fundamentals(asset)
    return result.to_dict()
```

**Commit after each:**
```powershell
git commit -m "Add tool: fetch_fundamentals"
git commit -m "Add tool: fetch_earnings"
git commit -m "Add tool: fetch_financial_statements"
```

---

### **✅ Phase 1C Complete Checklist:**

- [ ] Created `src/tools/data_tools.py`
- [ ] Implemented 4+ tools
- [ ] All tools tested manually
- [ ] All tools return proper dictionaries
- [ ] 4+ commits made

---

## 📅 **Phase 2: RAG Infrastructure (LATER - OPTIONAL)**

### **Goal:**
Add semantic search capability for earnings calls, news, PDFs.

**Time Estimate:** 1 week

**Tasks:**
- [ ] Add `DocumentChunk` table to database
- [ ] Setup ChromaDB vector store
- [ ] Create document ingestion pipeline
- [ ] Create `search_documents` tool

**Skip this phase if you want to build agents first!**

---

## 📅 **Phase 3: Single-Agent MVP (AFTER TOOLS)**

### **Goal:**
Create one simple agent that can use your tools.

**Time Estimate:** 1-2 hours

**Tasks:**

1. **Install dependencies:**
```powershell
   pip install langchain langchain-anthropic langgraph
```

2. **Create simple agent:**
```python
   # src/agents/simple_agent.py
   from langchain_anthropic import ChatAnthropic
   from langgraph.prebuilt import create_react_agent
   from tools.data_tools import fetch_stock_prices
   
   llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
   tools = [fetch_stock_prices]
   agent = create_react_agent(llm, tools)
   
   # Test it
   response = agent.invoke({
       "messages": [("user", "Get latest prices for AAPL")]
   })
   print(response["messages"][-1].content)
```

3. **Test the agent:**
```powershell
   python src\agents\simple_agent.py
```

**Expected:** Agent uses your tool, fetches data, reports back!

---

## 📅 **Phase 4: Multi-Agent System (FINAL GOAL)**

### **Goal:**
Build the full Supervisor → Scout → Analyst → Reporter system.

**Time Estimate:** 2-3 weeks

**This is your end vision from `Agentic_Architecture.md`**

---

## 🎯 **Important Guidelines**

### **DO:**
- ✅ Test after EVERY change
- ✅ Commit after EVERY working feature
- ✅ Keep commits small and focused
- ✅ Run tests before committing
- ✅ Use descriptive commit messages

### **DON'T:**
- ❌ Change multiple methods without testing
- ❌ Commit broken code
- ❌ Skip tests to save time
- ❌ Refactor everything at once

### **When You Get Stuck:**
1. Check the test output - it tells you what's wrong
2. Review the working example (`update_prices_for_asset`)
3. Check git log to see what worked before
4. Take a break and come back with fresh eyes

---

## 📊 **Progress Tracking**

### **Week 1 (Current Week):**
- [x] Day 1: Setup + Response Models
- [ ] Day 2: Refactor update_prices_for_asset
- [ ] Day 3: Refactor update_fundamentals + update_earnings
- [ ] Day 4: Refactor remaining methods
- [ ] Day 5: Review and polish

### **Week 2:**
- [ ] Create tools
- [ ] Test tools manually
- [ ] Build simple agent
- [ ] Celebrate! 🎉

---

## 🆘 **Quick Reference**

### **Common Commands:**
```powershell
# Run response model tests
python tests\test_responses.py

# Run data_manager tests
python tests\test_data_manager_refactor.py

# Run tool tests
python tests\test_tools.py

# Check git status
git status

# Commit changes
git add .
git commit -m "Description of what you did"

# View commit history
git log --oneline
```

### **File Locations:**
```
src/portfolio_tool/models/responses.py    # UpdateResult, QueryResult
src/portfolio_tool/data_manager.py        # Methods to refactor
src/tools/data_tools.py                   # Tools for agents
tests/test_responses.py                   # Response model tests
tests/test_data_manager_refactor.py       # Data manager tests
```

---

## 🎯 **Your Next Session Checklist**

When you sit down to code next:

1. [ ] Open this TODO file
2. [ ] Check what's next (probably Task 1)
3. [ ] Open the relevant files
4. [ ] Make the changes
5. [ ] Test it
6. [ ] Commit if it works
7. [ ] Check off the task in this file
8. [ ] Move to next task

---

## 🎉 **Milestones to Celebrate**

- 🎊 First method returns UpdateResult
- 🎊 All 5 methods refactored
- 🎊 First tool created
- 🎊 First agent runs successfully
- 🎊 Multi-agent system working

---

**Remember:** You're building something powerful. Take it one step at a time. Each small commit is progress! 🚀

**Good luck! You've got this!** 💪