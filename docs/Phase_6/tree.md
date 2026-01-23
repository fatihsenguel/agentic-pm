E:.
|   .env
|   .env.example
|   .gitignore
|   alembic.ini
|   config.toml
|   pyproject.toml
|   README.md
|   
+---alembic
|   |   env.py
|   |   README
|   |   script.py.mako
|   |   
|   \---versions
|       |   0d1860d818e6_add_macro_data_fixed.py
|       |   21f92620c49c_created_news_tables_pipeline_runs_api_.py
|       |   67cc3e174858_financialstatement_tabelle_hinzugefügt_.py
|       |   a994ff3c87ed_created_news_tables_pipeline_runs_api_.py
|       |   b2663cf9d397_add_financial_statement_raw_data.py
|       |   c1e79ae31788_create_initial_schema_v2.py
|       |   d4db413ede26_add_operating_cash_flow_to_.py
|       |
|       \---__pycache__
|               0d1860d818e6_add_macro_data_fixed.cpython-310.pyc
|               21f92620c49c_created_news_tables_pipeline_runs_api_.cpython-310.pyc
|               67cc3e174858_financialstatement_tabelle_hinzugefügt_.cpython-310.pyc
|               a994ff3c87ed_created_news_tables_pipeline_runs_api_.cpython-310.pyc
|               b2663cf9d397_add_financial_statement_raw_data.cpython-310.pyc
|               c1e79ae31788_create_initial_schema_v2.cpython-310.pyc
|               d4db413ede26_add_operating_cash_flow_to_.cpython-310.pyc
|               e6265f92e25d_add_macro_data.cpython-310.pyc
|
+---data
|       portfolio.db
|
+---demos
|       multi_agent_cli.py
|
+---outputs
|       .gitkeep
|
+---src
|   +---agents
|   |   |   backtest_agent.py
|   |   |   base_agent.py
|   |   |   config.py
|   |   |   data_agent.py
|   |   |   macro_agent.py
|   |   |   optimization_agent.py
|   |   |   prompts.py
|   |   |   protocols.py
|   |   |   rebalance_agent.py
|   |   |   risk_manager_agent.py
|   |   |   state.py
|   |   |   __init__.py
|   |   |
|   |   \---nodes
|   |           __init__.py
|   |
|   +---api
|   |       main.py
|   |
|   +---observability
|   |   |   token_counter.py
|   |   |   tracer.py
|   |   |   __init__.py
|   |   |
|   |   \---__pycache__
|   |           token_counter.cpython-310.pyc
|   |           tracer.cpython-310.pyc
|   |           __init__.cpython-310.pyc
|   |
|   \---portfolio_tool
|       |   database_setup.py
|       |   data_manager.py
|       |   provider_models.py
|       |   __init__.py
|       |
|       +---analytics
|       |       metrics.py
|       |       __init__.py
|       |
|       +---backtest
|       |       engine.py
|       |       metrics.py
|       |       reports.py
|       |       strategies.py
|       |       __init__.py
|       |
|       +---models
|       |       LESEN!!!.md
|       |       responses.py
|       |       __init__.py
|       |
|       +---optimization
|       |       base.py
|       |       constraints.py
|       |       mean_variance.py
|       |       risk_parity.py
|       |       __init__.py
|       |
|       +---providers
|       |       base.py
|       |       utils.py
|       |       yfinance_provider.py
|       |       __init__.py
|       |
|       +---quant
|       |       covariance.py
|       |       returns.py
|       |       risk_metrics.py
|       |       __init__.py
|       |
|       +---rag
|       |       chunker.py
|       |       document_loader.py
|       |       embeddings.py
|       |       fed_scraper.py
|       |       sentiment.py
|       |       __init__.py
|       |
|       +---scripts
|       |       run_backfill.py
|       |       run_metrics_update.py
|       |       update_all_assets.py
|       |
|       +---services
|       |       quota_manager.py
|       |
|       \---tools
|               analytics_tools.py
|               data_tools.py
|               macro_tools.py
|               rebalance_tools.py
|               __init__.py
|
\---tests
        conftest.py
        test_observability.py
        test_phase5_4_integration.py
        test_rebalance.py