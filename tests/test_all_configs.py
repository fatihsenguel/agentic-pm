# tests/test_all_configs.py
"""
Test that all config values are accessible and agents can be created.
"""

import sys
sys.path.insert(0, 'src')

def test_config_structure():
    """Test that config.py loads correctly."""
    from config import config
    
    print("Testing config structure...")
    
    # Test all config sections exist
    assert hasattr(config, 'data'), "Missing config.data"
    assert hasattr(config, 'macro'), "Missing config.macro"
    assert hasattr(config, 'optimization'), "Missing config.optimization"
    assert hasattr(config, 'rebalance'), "Missing config.rebalance"
    assert hasattr(config, 'backtest'), "Missing config.backtest"
    assert hasattr(config, 'risk'), "Missing config.risk"
    assert hasattr(config, 'features'), "Missing config.features"
    
    print("✅ All config sections exist")


def test_data_config():
    """Test DataConfig values."""
    from config import config
    
    print("\nTesting DataConfig...")
    print(f"  default_period: {config.data.default_period}")
    print(f"  default_covariance_method: {config.data.default_covariance_method}")
    print(f"  trading_days_per_year: {config.data.trading_days_per_year}")
    assert config.data.default_period == "3Y"
    assert config.data.trading_days_per_year == 252
    print("✅ DataConfig OK")


def test_macro_config():
    """Test MacroConfig values."""
    from config import config
    
    print("\nTesting MacroConfig...")
    print(f"  vix_low: {config.macro.vix_low}")
    print(f"  vix_elevated: {config.macro.vix_elevated}")
    print(f"  vix_crisis: {config.macro.vix_crisis}")
    assert config.macro.vix_low == 15.0
    assert config.macro.vix_elevated == 25.0
    print("✅ MacroConfig OK")


def test_optimization_config():
    """Test OptimizationConfig values."""
    from config import config
    
    print("\nTesting OptimizationConfig...")
    print(f"  default_method: {config.optimization.default_method}")
    print(f"  risk_free_rate: {config.optimization.risk_free_rate}")
    print(f"  default_max_weight: {config.optimization.default_max_weight}")
    assert config.optimization.default_method == "max_sharpe"
    assert config.optimization.risk_free_rate == 0.05
    print("✅ OptimizationConfig OK")


def test_rebalance_config():
    """Test RebalanceConfig values."""
    from config import config
    
    print("\nTesting RebalanceConfig...")
    print(f"  default_drift_threshold: {config.rebalance.default_drift_threshold}")
    print(f"  capital_gains_rate: {config.rebalance.capital_gains_rate}")
    assert config.rebalance.default_drift_threshold == 5.0
    assert config.rebalance.capital_gains_rate == 0.25
    print("✅ RebalanceConfig OK")


def test_backtest_config():
    """Test BacktestConfig values."""
    from config import config
    
    print("\nTesting BacktestConfig...")
    print(f"  default_initial_capital: {config.backtest.default_initial_capital}")
    print(f"  risk_free_rate: {config.backtest.risk_free_rate}")
    assert config.backtest.default_initial_capital == 100_000
    print("✅ BacktestConfig OK")


def test_risk_config():
    """Test RiskManagerConfig values."""
    from config import config
    
    print("\nTesting RiskManagerConfig...")
    print(f"  default_max_volatility: {config.risk.default_max_volatility}")
    print(f"  max_concentration: {config.risk.max_concentration}")
    assert config.risk.default_max_volatility == 0.15
    print("✅ RiskManagerConfig OK")


def test_agent_creation():
    """Test that all agents can be created without XxxAgentConfig."""
    print("\nTesting agent creation...")
    
    # Data Agent
    from agents.data_agent import create_data_agent
    agent = create_data_agent()
    assert agent.name == "DataAgent"
    print("✅ DataAgent created")
    
    # Macro Agent
    from agents.macro_agent import create_macro_agent
    agent = create_macro_agent()
    assert agent.name == "MacroAgent"
    print("✅ MacroAgent created")
    
    # Optimization Agent
    from agents.optimization_agent import create_optimization_agent
    agent = create_optimization_agent()
    assert agent.name == "OptimizationAgent"
    print("✅ OptimizationAgent created")
    
    # Rebalance Agent
    from agents.rebalance_agent import create_rebalance_agent
    agent = create_rebalance_agent()
    assert agent.name == "RebalanceAgent"
    print("✅ RebalanceAgent created")
    
    print("\n✅ All agents created successfully!")


def test_no_self_config_references():
    """Test that agents use config, not self.config."""
    print("\nTesting for self.config violations...")
    
    from pathlib import Path

    violations = []
    agents_dir = Path(__file__).parent.parent / "src" / "agents"

    agent_files = [
        agents_dir / "data_agent.py",
        agents_dir / "macro_agent.py",
        agents_dir / "optimization_agent.py",
        agents_dir / "rebalance_agent.py",
    ]

    for filepath in agent_files:
        assert filepath.exists(), f"Expected agent file missing: {filepath}"
        if "self.config." in filepath.read_text():
            violations.append(filepath.name)

    assert not violations, (
        f"Found self.config in {violations}. "
        "Agents must read the global config, not carry their own."
    )
    print("✅ No self.config violations found")


def test_sonnet_config_is_not_haiku():
    """ANTHROPIC_SONNET pointed at the Haiku id (KNOWN_GAPS): flipping the
    router's use_stronger_model would silently give Haiku. The id is the
    one the token counter accepted on 9 September."""
    from agents.config import ANTHROPIC_HAIKU, ANTHROPIC_SONNET
    assert ANTHROPIC_SONNET.model != ANTHROPIC_HAIKU.model
    assert ANTHROPIC_SONNET.model == "claude-sonnet-5"


if __name__ == "__main__":
    print("="*60)
    print("COMPREHENSIVE CONFIG TEST")
    print("="*60)
    
    try:
        test_config_structure()
        test_data_config()
        test_macro_config()
        test_optimization_config()
        test_rebalance_config()
        test_backtest_config()
        test_risk_config()
        test_agent_creation()
        test_no_self_config_references()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nYour config refactoring is complete and working!")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
