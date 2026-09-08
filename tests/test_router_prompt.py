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


def test_the_router_is_never_shown_the_policy_vocabulary():
    """Shown a list, the model maps the user's words onto its nearest member
    ("currency risk" -> instruments -> IPS-2.1, runner 3.4, 8 September).
    The words stay the user's; the node matches them against ips.toml."""
    prompt = build_router_prompt("what does my policy say about cash?", include_examples=True)
    assert "POLICY TOPICS" not in prompt
    assert ", ".join(load_ips().topics) not in prompt
    assert "the user's own words" in ROUTER_SYSTEM_PROMPT


def test_mode_parameters_are_in_the_output_format():
    assert '"hypothetical_weight": null' in ROUTER_SYSTEM_PROMPT
    assert '"policy_topic": null' in ROUTER_SYSTEM_PROMPT
