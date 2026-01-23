# tests/test_langgraph.py
# Purpose: Test the LangGraph state machine (Phase 6.2)
# Run with: pytest tests/test_langgraph.py -v

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.state import (
    AgentState,
    create_initial_state,
    set_router_decision,
    mark_agent_complete,
    add_shared_data,
    add_error,
    get_next_agent,
    is_execution_complete,
    has_errors,
    get_user_message,
)


# =============================================================================
# STATE TESTS
# =============================================================================

class TestAgentState:
    """Test AgentState creation and manipulation."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state("Hello, optimize my portfolio")
        
        assert state["request_id"] is not None
        assert len(state["messages"]) == 1
        assert state["execution_step"] == 0
        assert state["sub_results"] == {}
        assert state["errors"] == []
    
    def test_get_user_message(self):
        """Test extracting user message from state."""
        state = create_initial_state("Test message")
        
        msg = get_user_message(state)
        assert msg == "Test message"
    
    def test_set_router_decision(self):
        """Test setting router decision."""
        state = create_initial_state("Test")
        
        decision = {
            "intent": "optimization",
            "execution_order": ["DataAgent", "OptimizationAgent"],
            "parameters": {"tickers": ["SPY", "TLT"]},
        }
        
        updates = set_router_decision(state, decision)
        
        assert updates["router_decision"] == decision
        assert updates["agents_to_run"] == ["DataAgent", "OptimizationAgent"]
    
    def test_mark_agent_complete(self):
        """Test marking an agent as complete."""
        state = create_initial_state("Test")
        state["agents_to_run"] = ["DataAgent", "OptimizationAgent"]
        state["sub_results"] = {}
        state["execution_step"] = 0
        
        result = {"success": True, "data": {"prices": [1, 2, 3]}}
        updates = mark_agent_complete(state, "DataAgent", result)
        
        assert "DataAgent" in updates["sub_results"]
        assert updates["agents_to_run"] == ["OptimizationAgent"]
        assert updates["execution_step"] == 1
    
    def test_get_next_agent(self):
        """Test getting next agent to run."""
        state = create_initial_state("Test")
        state["agents_to_run"] = ["MacroAgent", "RebalanceAgent"]
        
        assert get_next_agent(state) == "MacroAgent"
        
        state["agents_to_run"] = []
        assert get_next_agent(state) is None
    
    def test_is_execution_complete(self):
        """Test checking if execution is complete."""
        state = create_initial_state("Test")
        
        state["agents_to_run"] = ["DataAgent"]
        assert not is_execution_complete(state)
        
        state["agents_to_run"] = []
        assert is_execution_complete(state)
    
    def test_add_shared_data(self):
        """Test adding shared data."""
        state = create_initial_state("Test")
        state["shared_data"] = {"existing": "data"}
        
        updates = add_shared_data(state, "new_key", {"value": 123})
        
        assert updates["shared_data"]["existing"] == "data"
        assert updates["shared_data"]["new_key"]["value"] == 123
    
    def test_add_error(self):
        """Test adding errors."""
        state = create_initial_state("Test")
        state["errors"] = ["First error"]
        
        updates = add_error(state, "Second error")
        
        assert len(updates["errors"]) == 2
        assert "Second error" in updates["errors"]
    
    def test_has_errors(self):
        """Test checking for errors."""
        state = create_initial_state("Test")
        
        state["errors"] = []
        assert not has_errors(state)
        
        state["errors"] = ["An error"]
        assert has_errors(state)


# =============================================================================
# GRAPH STRUCTURE TESTS
# =============================================================================

class TestGraphStructure:
    """Test the graph structure and routing logic."""
    
    def test_graph_builds(self):
        """Test that the graph builds without error."""
        from agents.graph import build_graph
        
        graph = build_graph()
        assert graph is not None
    
    def test_graph_compiles(self):
        """Test that the graph compiles."""
        from agents.graph import create_agent_graph
        
        compiled = create_agent_graph()
        assert compiled is not None
    
    def test_should_continue_or_end_with_response(self):
        """Test routing when final response is set."""
        from agents.graph import should_continue_or_end
        
        state = create_initial_state("Test")
        state["final_response"] = "Here is your answer"
        state["agents_to_run"] = []
        
        result = should_continue_or_end(state)
        assert result == "end"
    
    def test_should_continue_or_end_with_agents(self):
        """Test routing when agents remain."""
        from agents.graph import should_continue_or_end
        
        state = create_initial_state("Test")
        state["final_response"] = None
        state["agents_to_run"] = ["DataAgent"]
        
        result = should_continue_or_end(state)
        assert result == "dispatcher"
    
    def test_should_continue_or_end_complete(self):
        """Test routing when all agents done."""
        from agents.graph import should_continue_or_end
        
        state = create_initial_state("Test")
        state["final_response"] = None
        state["agents_to_run"] = []
        
        result = should_continue_or_end(state)
        assert result == "synthesizer"
    
    def test_route_to_agent(self):
        """Test routing to specific agents."""
        from agents.graph import route_to_agent
        
        state = create_initial_state("Test")
        
        state["current_agent"] = "DataAgent"
        assert route_to_agent(state) == "data_agent"
        
        state["current_agent"] = "MacroAgent"
        assert route_to_agent(state) == "macro_agent"
        
        state["current_agent"] = "OptimizationAgent"
        assert route_to_agent(state) == "optimization_agent"
        
        state["current_agent"] = None
        assert route_to_agent(state) == "synthesizer"


# =============================================================================
# NODE TESTS (Mock)
# =============================================================================

class TestNodes:
    """Test individual node functions."""
    
    @pytest.mark.asyncio
    async def test_dispatcher_node(self):
        """Test dispatcher node."""
        from agents.nodes import agent_dispatcher_node
        
        state = create_initial_state("Test")
        state["agents_to_run"] = ["MacroAgent", "RebalanceAgent"]
        
        updates = await agent_dispatcher_node(state)
        
        assert updates["current_agent"] == "MacroAgent"
    
    @pytest.mark.asyncio
    async def test_dispatcher_node_empty(self):
        """Test dispatcher with no agents."""
        from agents.nodes import agent_dispatcher_node
        
        state = create_initial_state("Test")
        state["agents_to_run"] = []
        
        updates = await agent_dispatcher_node(state)
        
        assert updates["current_agent"] is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full graph."""
    
    @pytest.mark.asyncio
    async def test_simple_macro_query(self):
        """Test a simple macro analysis query through the graph."""
        from agents.graph import run_agent_graph
        
        result = await run_agent_graph("Wie ist die aktuelle Marktlage?")
        
        # Should have completed
        assert result.get("final_response") is not None
        
        # Should have used MacroAgent
        sub_results = result.get("sub_results", {})
        assert "MacroAgent" in sub_results
    
    @pytest.mark.asyncio 
    async def test_multi_step_query(self):
        """Test a multi-step optimization query."""
        from agents.graph import run_agent_graph
        
        result = await run_agent_graph(
            "Optimiere mein Portfolio mit SPY und TLT"
        )
        
        assert result.get("final_response") is not None
        
        # Should have used DataAgent and OptimizationAgent
        sub_results = result.get("sub_results", {})
        assert "DataAgent" in sub_results or "OptimizationAgent" in sub_results
    
    @pytest.mark.asyncio
    async def test_clarification_query(self):
        """Test an ambiguous query that needs clarification."""
        from agents.graph import run_agent_graph
        
        result = await run_agent_graph("Portfolio")
        
        # Should ask for clarification
        assert result.get("final_response") is not None
        # Clarification messages typically contain a question
        response = result.get("final_response", "")
        assert "?" in response or "clarif" in response.lower() or "möchten" in response.lower()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
