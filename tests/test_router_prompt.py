"""
The router prompt renders its vocabularies from their registries: the agent
roster and its count from AGENTS, the policy topics from ips.toml. A word
that exists in one place and not the other is the drift these tests refuse.
"""

from agents.router_prompts import ROUTER_SYSTEM_PROMPT, REPAIR_PROMPT, build_router_prompt
from agents.schemas import AGENTS, IntentType
from portfolio_tool.ips import load_ips


def test_roster_and_count_come_from_agents():
    for i, (name, description) in enumerate(AGENTS.items(), 1):
        assert f"{i}. {name} - {description}" in ROUTER_SYSTEM_PROMPT
    assert f"only use the {len(AGENTS)} listed above" in ROUTER_SYSTEM_PROMPT


def test_compliance_intent_is_in_both_prompts():
    line = [l for l in ROUTER_SYSTEM_PROMPT.splitlines() if l.startswith('  "intent": "')][0]
    assert "|compliance|" in line
    assert "|compliance|" in REPAIR_PROMPT
    assert "- compliance:" in ROUTER_SYSTEM_PROMPT
    assert IntentType.COMPLIANCE.value == "compliance"


def test_policy_topics_are_rendered_from_the_ips():
    prompt = build_router_prompt("what does my policy say about cash?", include_examples=False)
    assert "POLICY TOPICS" in prompt
    topics_line = prompt.split("\nPOLICY TOPICS (", 1)[1].splitlines()[1]
    assert topics_line == ", ".join(load_ips().topics)
    assert "currency" not in topics_line


def test_mode_parameters_are_in_the_output_format():
    assert '"hypothetical_weight": null' in ROUTER_SYSTEM_PROMPT
    assert '"policy_topic": null' in ROUTER_SYSTEM_PROMPT
