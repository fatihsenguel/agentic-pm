"""
🎬 AGENTIC FINANCE - INTERVIEW DEMO (Simulated)
================================================

This demo SIMULATES a perfectly polished multi-agent system.
Use this for interviews to show the VISION of what the system does.

The real system is 80-90% there, this fills the gaps for presentation.

Usage:
    python demos/interview_demo.py

Author: Agentic Finance Team
Version: Interview Ready
"""

import sys
import os
import time
import random

# Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║      🦊 AGENTIC FINANCE - PORTFOLIO MANAGER AI v3.0              ║
║           RAG + Decision Engine + Full Capabilities               ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")


def typing_effect(text, delay=0.02):
    """Print text with typing effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def simulate_delay(min_sec=0.3, max_sec=0.8):
    """Simulate processing delay."""
    time.sleep(random.uniform(min_sec, max_sec))


def print_agent_step(agent_name, icon, message, duration_ms, success=True):
    """Print a simulated agent step."""
    status = "✓" if success else "✗"
    color = GREEN if success else RED
    print(f"  {DIM}[{duration_ms/1000:.1f}s]{RESET} {icon} {BOLD}{agent_name}:{RESET} {color}{status}{RESET} {message}")
    simulate_delay(0.2, 0.5)


def print_thinking(message):
    """Print thinking indicator."""
    print(f"  {DIM}└─ {message}{RESET}")
    simulate_delay(0.1, 0.3)


# =============================================================================
# SIMULATED RESPONSES
# =============================================================================

SIMULATED_RESPONSES = {
    # =========================================================================
    # WOW #1: THE SMART HOLD
    # =========================================================================
    "markets dropped": {
        "router": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "agents": ["DataAgent", "MacroAgent", "RAGAgent", "RebalanceAgent"],
            "duration": 2100,
        },
        "agents": [
            ("DataAgent", "📊", "Fetched portfolio: 5 holdings, €127,450 value", 850),
            ("MacroAgent", "🌍", "VIX: 28.3 (elevated), Yield curve: normal", 920),
            ("RAGAgent", "📄", "No panic-related news for holdings", 680),
            ("RebalanceAgent", "⚖️", "Drift: 2.1% (within threshold)", 340),
        ],
        "response": f"""
{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         DECISION SUMMARY{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{GREEN}{BOLD}Decision:        HOLD{RESET}
{BOLD}Confidence:      92%{RESET}
{BOLD}Trade Required:  No{RESET}

{BOLD}Rationale:{RESET}
  Your portfolio declined 2.1% versus the market's 4.0% drop.
  {GREEN}This is EXACTLY what diversification should do.{RESET}
  Selling now would lock in losses and miss potential recovery.
  VIX is elevated (28.3) but not at crisis levels.

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         RISK ASSESSMENT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{GREEN}Status: ACCEPTABLE{RESET}

{BOLD}Key Metrics:{RESET}
  • Portfolio Beta: 0.52 (defensive positioning working)
  • Max Drawdown Today: -2.1% vs SPY -4.0%
  • Diversification Score: 0.73 (healthy)

{BOLD}Why HOLD is correct:{RESET}
  ✓ No constraint breaches
  ✓ Drift within tolerance (2.1% < 5% threshold)
  ✓ Macro regime: Elevated but not crisis
  ✓ No material news on holdings

{YELLOW}💡 Note: This is what diversification looks like during drawdowns.
   Your portfolio is performing as designed.{RESET}
"""
    },
    
    # =========================================================================
    # WOW #2: DOCUMENT-INFORMED DECISION
    # =========================================================================
    "based on nvidia": {
        "router": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "agents": ["DataAgent", "RAGAgent", "OptimizationAgent"],
            "duration": 2800,
        },
        "agents": [
            ("DataAgent", "📊", "Fetched NVDA data: +279% YTD, current weight 15%", 920),
            ("RAGAgent", "📄", "Searched earnings report: 5 key findings, 3 risks", 1240),
            ("OptimizationAgent", "🧮", "Evaluated position sizing: max 20% recommended", 680),
        ],
        "response": f"""
{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         DECISION SUMMARY{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}{BOLD}Decision:        TILT{RESET}
{BOLD}Confidence:      78%{RESET}
{BOLD}Trade Required:  Optional{RESET}

{BOLD}Rationale:{RESET}
  Strong earnings (279% revenue growth) support the position, BUT
  China export restrictions present material risk (~$5B revenue impact).
  Current 15% weight is appropriate. Increasing to 20% acceptable
  only with hedging consideration.

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         RISK ASSESSMENT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}Status: ELEVATED{RESET}

{BOLD}Key Risks:{RESET}
  • {RED}[DOC]{RESET} China export restrictions may impact ~$5B annual revenue
  • {RED}[DOC]{RESET} Customer concentration: Top 4 = 46% of revenue
  • {RED}[DOC]{RESET} Supply constraints: H100 lead times 6-9 months
  • Current NVDA weight (15%) approaching concentration limit

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                       DOCUMENT EVIDENCE{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  📎 {CYAN}"Revenue: $18.1 billion, up 279% year-over-year..."{RESET}
     Source: NVDA_Q3_2024_Earnings.txt, §Financial Highlights

  📎 {CYAN}"New U.S. export controls may impact approximately $5 billion..."{RESET}
     Source: NVDA_Q3_2024_Earnings.txt, §Risk Factors

  📎 {CYAN}"Top four customers represent approximately 46% of revenue..."{RESET}
     Source: NVDA_Q3_2024_Earnings.txt, §Risk Factors

{BOLD}Recommendation:{RESET}
  {YELLOW}→ Maintain current 15% position
  → Consider protective put if increasing exposure
  → Monitor Q4 guidance for China impact clarity{RESET}
"""
    },
    
    # =========================================================================
    # WOW #3: FED POLICY IMPACT
    # =========================================================================
    "fed": {
        "router": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "agents": ["DataAgent", "RAGAgent", "MacroAgent", "RebalanceAgent"],
            "duration": 3200,
        },
        "agents": [
            ("DataAgent", "📊", "Loaded dividend portfolio: 8 holdings, 3.2yr duration", 780),
            ("RAGAgent", "📄", "Analyzed Fed minutes: Hawkish sentiment +0.45", 1450),
            ("MacroAgent", "🌍", "10Y yield: 4.52%, curve steepening", 890),
            ("RebalanceAgent", "⚖️", "Duration risk identified, rotation suggested", 560),
        ],
        "response": f"""
{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         DECISION SUMMARY{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}{BOLD}Decision:        TILT{RESET}
{BOLD}Confidence:      75%{RESET}
{BOLD}Trade Required:  Yes (2 trades){RESET}

{BOLD}Rationale:{RESET}
  Fed minutes indicate hawkish stance (sentiment: +0.45).
  Your dividend portfolio has duration risk in rising rate environment.
  Recommend reducing long-duration bonds in favor of shorter duration.

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                        FED SENTIMENT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  🦅 {RED}{BOLD}HAWKISH{RESET} (Score: +0.45)
  
  {BOLD}Key Signals from Minutes:{RESET}
  • "Inflation remains elevated above target"
  • "Further tightening may be appropriate"
  • "Labor market remains tight"
  • "Balance sheet reduction continuing"
  
  {BOLD}Method:{RESET} Hybrid (rule-based + LLM verification)
  {BOLD}Confidence:{RESET} 82%

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         RISK ASSESSMENT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}Status: ELEVATED{RESET}

{BOLD}Key Risks:{RESET}
  • Portfolio duration: 3.2 years (sensitive to rate moves)
  • TLT position: -8.2% YTD (long duration pain)
  • Hawkish Fed = potential for more rate pressure

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                      RECOMMENDED TRADES{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  {RED}SELL{RESET}  TLT    5% of portfolio  (~€6,400)
  {GREEN}BUY{RESET}   SHY    5% of portfolio  (~€6,400)
  
  {BOLD}Impact:{RESET}
  • Duration: 3.2yr → 2.1yr (-34%)
  • Rate sensitivity reduced significantly
  • Dividend yield maintained (~3.8%)

{BOLD}Est. Transaction Cost:{RESET} €12.80 (0.02%)
"""
    },
    
    # =========================================================================
    # WOW #4: FULL PORTFOLIO REVIEW
    # =========================================================================
    "quarterly review": {
        "router": {
            "query_intent": "decision",
            "execution_intent": "combined",
            "agents": ["DataAgent", "RAGAgent", "MacroAgent", "OptimizationAgent", "RebalanceAgent"],
            "duration": 4100,
        },
        "agents": [
            ("DataAgent", "📊", "Full portfolio analysis: 5 holdings, €127,450", 1200),
            ("RAGAgent", "📄", "Scanned 3 documents for holdings", 1850),
            ("MacroAgent", "🌍", "Regime: Risk-On, VIX: 16.2", 920),
            ("OptimizationAgent", "🧮", "Optimal weights calculated, Sharpe: 1.52", 780),
            ("RebalanceAgent", "⚖️", "Drift: 8.3%, rebalance recommended", 650),
        ],
        "response": f"""
{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                    QUARTERLY PORTFOLIO REVIEW{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{BOLD}Portfolio:{RESET} Growth Tech Portfolio
{BOLD}Value:{RESET} €127,450.00
{BOLD}Period:{RESET} Q3 2024

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         DECISION SUMMARY{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}{BOLD}Decision:        REBALANCE{RESET}
{BOLD}Confidence:      88%{RESET}
{BOLD}Trade Required:  Yes (3 trades){RESET}

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                      1. DRIFT ANALYSIS{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{BOLD}Max Drift:{RESET} 8.3% {YELLOW}(exceeds 5% threshold){RESET}

  Ticker   Current    Target     Drift
  ──────────────────────────────────────
  NVDA     23.5%      15.0%     {RED}+8.5%{RESET}
  AAPL     18.2%      20.0%     -1.8%
  MSFT     21.0%      20.0%     +1.0%
  GOOGL    17.3%      20.0%     -2.7%
  SPY      20.0%      25.0%     -5.0%

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                    2. MACRO ENVIRONMENT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  {GREEN}Regime: RISK-ON{RESET}
  
  • VIX: 16.2 (low volatility)
  • Yield Curve: Normal (slope: +0.65%)
  • Fed Stance: Neutral to slightly hawkish
  
  {BOLD}Implication:{RESET} Environment supports equity exposure

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                    3. DOCUMENT INSIGHTS{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  📎 {BOLD}NVDA:{RESET} Strong earnings (+279%), but China risk material
  📎 {BOLD}AAPL:{RESET} Services growth solid, China exposure noted
  
  {BOLD}Aggregate Risk Factors:{RESET}
  • Geopolitical (China exposure across holdings)
  • Concentration in tech sector

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                    4. RECOMMENDED ACTIONS{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  {RED}SELL{RESET}  NVDA   €10,840  (reduce from 23.5% → 15%)
  {GREEN}BUY{RESET}   SPY    €6,380   (increase to target 25%)
  {GREEN}BUY{RESET}   GOOGL  €3,440   (increase to target 20%)

  {BOLD}Est. Transaction Cost:{RESET} €20.66
  {BOLD}Est. Tax Impact:{RESET} €1,240 (NVDA gains)

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                    5. EXPECTED IMPACT{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  Metric              Before      After       Change
  ──────────────────────────────────────────────────
  Expected Return     18.2%       16.8%       -1.4%
  Volatility          22.1%       18.3%       {GREEN}-3.8%{RESET}
  Sharpe Ratio        0.82        1.02        {GREEN}+0.20{RESET}
  Max Concentration   23.5%       20.0%       {GREEN}-3.5%{RESET}

{CYAN}{BOLD}
Summary: Rebalancing will reduce concentration risk and improve
risk-adjusted returns, with minimal tax impact.
{RESET}"""
    },
    
    # =========================================================================
    # SIMPLE QUERIES
    # =========================================================================
    "optimize": {
        "router": {
            "query_intent": "decision",
            "execution_intent": "optimization",
            "agents": ["DataAgent", "OptimizationAgent"],
            "duration": 1800,
        },
        "agents": [
            ("DataAgent", "📊", "Fetched 3Y data for 5 tickers", 1200),
            ("OptimizationAgent", "🧮", "Max Sharpe optimization complete", 580),
        ],
        "response": f"""
{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                         DECISION SUMMARY{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

{YELLOW}{BOLD}Decision:        REBALANCE{RESET}
{BOLD}Confidence:      95%{RESET}
{BOLD}Trade Required:  Yes{RESET}

{BOLD}Rationale:{RESET}
  Current allocation significantly deviates from optimal.
  Concentration risk in SPY (83.6%) exceeds limits.

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                     OPTIMAL ALLOCATION{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  {BOLD}Current → Optimal{RESET}
  
  SPY:  83.6% → 40.0%  {RED}(-43.6%){RESET}
  GLD:  11.1% → 35.0%  {GREEN}(+23.9%){RESET}
  TLT:   5.3% → 25.0%  {GREEN}(+19.7%){RESET}

{BOLD}════════════════════════════════════════════════════════════════════{RESET}
{BOLD}                     EXPECTED METRICS{RESET}
{BOLD}════════════════════════════════════════════════════════════════════{RESET}

  • Expected Return:  14.2%
  • Volatility:       9.8%
  • Sharpe Ratio:     {GREEN}1.45{RESET}
"""
    },
    
    "risk factors": {
        "router": {
            "query_intent": "information",
            "execution_intent": "document_search",
            "agents": ["RAGAgent"],
            "duration": 1200,
        },
        "agents": [
            ("RAGAgent", "📄", "Searched earnings report: 5 risk factors found", 980),
        ],
        "response": f"""
{BOLD}📄 DOCUMENT INSIGHTS{RESET}

{BOLD}Sources:{RESET}
  • NVDA_Q3_2024_Earnings.txt

{BOLD}Risk Factors Identified:{RESET}

  {RED}1. CHINA EXPORT RESTRICTIONS (HIGH IMPACT){RESET}
     New U.S. government export controls significantly restrict 
     ability to sell advanced AI chips to China. 
     Estimated impact: ~$5 billion annual revenue.

  {YELLOW}2. SUPPLY CHAIN CONSTRAINTS (MEDIUM IMPACT){RESET}
     Demand for H100/H200 GPUs exceeds supply.
     Lead times: 6-9 months.
     Capacity expansion ongoing with TSMC.

  {YELLOW}3. CUSTOMER CONCENTRATION (MEDIUM IMPACT){RESET}
     Top 4 customers = 46% of total revenue.
     Loss of major customer could materially impact results.

  {YELLOW}4. COMPETITIVE LANDSCAPE (EMERGING){RESET}
     AMD MI300 and Intel Gaudi gaining traction.
     Market share pressure expected in 2025.

  {YELLOW}5. GEOPOLITICAL (ONGOING){RESET}
     Taiwan tensions present supply chain risk.
     TSMC is sole supplier of advanced chips.

{BOLD}Citations:{RESET}
  📎 NVDA_Q3_2024_Earnings.txt, §Risk Factors (p.3-4)
"""
    },
}


def find_response(user_input: str) -> dict:
    """Find matching simulated response."""
    user_lower = user_input.lower()
    
    # Check for keyword matches
    if any(kw in user_lower for kw in ["market", "dropped", "crash", "sell everything", "nervous", "panic"]):
        return SIMULATED_RESPONSES["markets dropped"]
    
    if any(kw in user_lower for kw in ["based on nvidia", "based on nvda", "earnings", "should i increase", "nvda position"]):
        return SIMULATED_RESPONSES["based on nvidia"]
    
    if any(kw in user_lower for kw in ["fed", "hawkish", "dovish", "interest rate", "monetary", "dividend portfolio"]):
        return SIMULATED_RESPONSES["fed"]
    
    if any(kw in user_lower for kw in ["quarterly review", "full review", "portfolio review", "analyze everything"]):
        return SIMULATED_RESPONSES["quarterly review"]
    
    if any(kw in user_lower for kw in ["optimize", "optimal", "max sharpe"]):
        return SIMULATED_RESPONSES["optimize"]
    
    if any(kw in user_lower for kw in ["risk factor", "what does", "10-k", "10k", "say about"]):
        return SIMULATED_RESPONSES["risk factors"]
    
    return None


def run_simulation(user_input: str):
    """Run the simulated agent response."""
    response_data = find_response(user_input)
    
    if not response_data:
        print(f"\n{YELLOW}[Demo] No simulation configured for this prompt.{RESET}")
        print(f"{DIM}Try one of these WOW prompts:{RESET}")
        print(f'{DIM}  • "Markets dropped 4% today. Should I sell everything?"{RESET}')
        print(f'{DIM}  • "Based on NVIDIA\'s earnings, should I increase my position?"{RESET}')
        print(f'{DIM}  • "The Fed just released hawkish minutes. How does this affect my dividend portfolio?"{RESET}')
        print(f'{DIM}  • "Run a full quarterly review of my portfolio"{RESET}')
        print()
        return
    
    router = response_data["router"]
    agents = response_data["agents"]
    final_response = response_data["response"]
    
    print(f"\n{CYAN}🤖 Processing...{RESET}")
    print(f"{'─' * 60}")
    
    # Simulate router
    simulate_delay(0.5, 1.0)
    print(f"\n{DIM}🧠 Router analyzing request...{RESET}")
    simulate_delay(0.8, 1.5)
    
    print(f"  {DIM}[{router['duration']/1000:.1f}s]{RESET} 🧠 {BOLD}Router:{RESET} {router['query_intent']}/{router['execution_intent']} → {router['agents']}")
    print()
    
    # Simulate each agent
    total_time = router['duration']
    for agent_name, icon, message, duration in agents:
        total_time += duration
        simulate_delay(0.3, 0.8)
        print_agent_step(agent_name, icon, message, total_time)
    
    # Synthesizer
    simulate_delay(0.2, 0.4)
    print(f"  {DIM}[{(total_time + 200)/1000:.1f}s]{RESET} ✍️ {BOLD}Synthesizer:{RESET} formatting response...")
    
    print(f"{'─' * 60}")
    
    # Print response with slight delay for effect
    simulate_delay(0.3, 0.5)
    print(f"\n{GREEN}{BOLD}AI:{RESET}")
    print(final_response)


def print_help():
    """Print available demo prompts."""
    print(f"""
{BOLD}{YELLOW}🎬 INTERVIEW DEMO - Simulated Prompts{RESET}
{DIM}{'─' * 60}{RESET}

{BOLD}{CYAN}WOW Prompts (try these!):{RESET}

{GREEN}1. The "Smart HOLD" (Anti-Action-Bias):{RESET}
   "Markets dropped 4% today. My portfolio is down 2.1%. 
    I'm nervous - should I sell everything?"

{GREEN}2. Document-Informed Decision:{RESET}
   "Based on NVIDIA's Q3 earnings showing 279% growth but 
    China restrictions, should I increase my position?"

{GREEN}3. Fed Policy Impact:{RESET}
   "The Fed just released hawkish minutes. How does this 
    affect my dividend portfolio? Should I rotate?"

{GREEN}4. Full Quarterly Review:{RESET}
   "Run a full quarterly review of my portfolio"

{GREEN}5. Simple Optimization:{RESET}
   "Optimize my portfolio"

{GREEN}6. Document Search:{RESET}
   "What are NVIDIA's risk factors from the earnings report?"

{DIM}Type 'exit' to quit, '/help' for this menu{RESET}
""")


def main():
    """Main demo loop."""
    clear_screen()
    print_banner()
    
    print(f"{GREEN}✓ Database:{RESET} 12 assets tracked")
    print(f"{GREEN}✓ RAG System:{RESET} 3 documents, 23 chunks indexed")
    print(f"{GREEN}✓ Active Portfolio:{RESET} Growth Tech (ID: 1)")
    print()
    
    print(f"{YELLOW}🎬 INTERVIEW MODE - Simulated responses for demo{RESET}")
    print(f"{DIM}Type /help for suggested prompts{RESET}")
    print(f"{'─' * 60}\n")
    
    while True:
        try:
            user_input = input(f"{BOLD}You:{RESET} ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{YELLOW}Demo ended. Good luck with the interview! 🚀{RESET}")
                break
            
            if user_input.lower() == "/help":
                print_help()
                continue
            
            run_simulation(user_input)
            
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted. Type 'exit' to quit.{RESET}")
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}")


if __name__ == "__main__":
    main()
