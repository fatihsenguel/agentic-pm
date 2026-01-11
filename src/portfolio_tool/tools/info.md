
### Zusammenfassung der Mapping-Tabelle

| DataManager Methode (Die "Küche") | Tool (Die "Speisekarte") | Status |
| --- | --- | --- |
| `update_prices_for_asset` | `fetch_stock_prices` | ✅ Enthalten |
| `update_financial_statements...` | `fetch_financial_statements` | ✅ Enthalten |
| `update_quarterly_earnings...` | `fetch_earnings_history` | ✅ Enthalten |
| `force_update_asset_info` | `fetch_fundamentals` (Kombi) | ✅ Enthalten |
| `update_fundamental_data` | `fetch_fundamentals` (Kombi) | ✅ Enthalten |
| `update_dividends_for_asset` | *(Noch kein Tool)* | ⏳ Später / Optional |
| `update_splits_for_asset` | *(Noch kein Tool)* | ⏳ Später / Optional |
| `update_shares_history...` | *(Noch kein Tool)* | ⏳ Später / Optional |