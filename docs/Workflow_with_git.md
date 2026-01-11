# See what changed
git status

# See detailed changes
git diff

# Stage your changes
git add src/portfolio_tool/models/responses.py

# Or stage everything
git add .

# Commit with a message
git commit -m "Add UpdateResult and QueryResult response models"

# View commit history
git log --oneline


# Example: After creating responses.py
git add src/portfolio_tool/models/
git commit -m "Add response models for agent communication"

# Example: After refactoring data_manager
git add src/portfolio_tool/data_manager.py
git add tests/test_data_manager_refactor.py
git commit -m "Refactor update_daily_prices to return UpdateResult"
```

---

## **💡 Recommended Commit Strategy**

Make commits after each logical step:
```
✅ "Add response models (UpdateResult, QueryResult)"
✅ "Refactor update_daily_prices to return structured data"
✅ "Add tests for response models"
✅ "Create first LangChain tool wrapper"
✅ "Add web search capability"