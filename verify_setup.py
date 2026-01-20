import sys
import os

# WICHTIG: Füge den 'src' Ordner zum Python-Pfad hinzu
# Damit Python 'agents' und 'portfolio_tool' findet
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

print(f"🔧 Testing environment with path: {src_path}")
print("-" * 50)

# --- Test Start ---

try:
    # Test 1: Imports & Protocols
    print("1️⃣  Testing Imports & Protocols...")
    from agents.macro_agent import create_macro_agent, MacroAgent
    from agents.data_agent import create_data_agent, DataAgent
    from agents.protocols import TaskType, RegimeType
    
    # Verify TaskType update
    if hasattr(TaskType, 'MACRO_ANALYSIS'):
        print("   ✅ TaskType.MACRO_ANALYSIS found")
    else:
        print("   ❌ TaskType.MACRO_ANALYSIS MISSING (Update protocols.py!)")

    # Verify RegimeType update (Critical for MacroAgent)
    if hasattr(RegimeType, 'CRISIS') and hasattr(RegimeType, 'RECOVERY'):
        print("   ✅ RegimeType.CRISIS/RECOVERY found")
    else:
        print("   ❌ RegimeType.CRISIS MISSING (Update protocols.py!)")

    # Test 2: Agent Creation
    print("\n2️⃣  Testing Agent Creation...")
    macro_agent = create_macro_agent()
    data_agent = create_data_agent()
    
    print(f"   ✅ MacroAgent created with {len(macro_agent.get_tools())} tools")
    # Optional: Tools auflisten
    # print(f"      Tools: {[t.__name__ for t in macro_agent.get_tools()]}")
    
    print(f"   ✅ DataAgent created with {len(data_agent.get_tools())} tools")

    # Test 3: DataManager Macro Methods
    print("\n3️⃣  Testing DataManager Capabilities...")
    from portfolio_tool.data_manager import get_data_manager
    
    dm = get_data_manager()
    
    # Check for the new methods needed by MacroAgent
    missing_methods = []
    for method in ['update_vix', 'get_vix_with_regime', 'get_yield_curve_status', 'update_macro_data']:
        if hasattr(dm, method):
            print(f"   ✅ DataManager.{method} exists")
        else:
            print(f"   ❌ DataManager.{method} MISSING")
            missing_methods.append(method)
            
    if missing_methods:
        print(f"   ⚠️ ACHTUNG: Du musst data_manager.py aktualisieren! Es fehlen: {missing_methods}")

    # Test 4: Database Models
    print("\n4️⃣  Testing Database Models...")
    try:
        from portfolio_tool.database_setup import MacroData
        print("   ✅ MacroData table class found")
    except ImportError:
        print("   ❌ MacroData table class MISSING in database_setup.py")

    print("-" * 50)
    print("🎉 DIAGNOSTIC COMPLETE")

except Exception as e:
    print(f"\n❌ FATAL ERROR: {str(e)}")
    import traceback
    traceback.print_exc()