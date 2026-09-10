"""
The router prompt renders its vocabularies from their registries: the agent
roster and its count from AGENTS, the intents and their descriptions from
INTENTS, the policy topics from ips.toml. A word that exists in one place
and not the other is the drift these tests refuse.
"""

from typing import get_args

from agents.router_prompts import ROUTER_SYSTEM_PROMPT, REPAIR_PROMPT, build_router_prompt
from agents import nodes
from agents.schemas import AGENTS, INTENTS, ExtractedParameters, IntentType
from portfolio_tool.ips import load_ips


def test_the_prompt_asks_for_no_plan_and_no_extracted_field():
    """After extraction and derivation the model decides intent, measure,
    group_by, the topic flag, confidence and a clarification. The prompt
    no longer shows a roster, asks for a plan, or asks for what extraction
    reads from the message."""
    for prompt in (ROUTER_SYSTEM_PROMPT, REPAIR_PROMPT):
        for absent in ("AVAILABLE AGENTS", "agents_needed", "execution_order", "is_multi_step",
                       "requires_confirmation", '"tickers"', '"period"', '"max_volatility"',
                       '"hypothetical_weight"', "policy_topic", "EXECUTION ORDER",
                       "EXTRACTION RULES"):
            assert absent not in prompt, absent
        for present in ('"measure"', '"group_by"', '"clarification_question"'):
            assert present in prompt, present


def test_the_out_of_scope_wording_is_the_registrys_verbatim():
    """The three failed prompt edits stay as they are (pending decision 6,
    decided keep): the description is rendered from INTENTS unchanged and
    the NEE example is kept. A change there is a fourth wording on a line
    with three failed predictions."""
    assert INTENTS["out_of_scope"] in ROUTER_SYSTEM_PROMPT
    assert 'User: "Is NEE up or down?" (active portfolio holding NEE)' in ROUTER_SYSTEM_PROMPT


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
    assert ", ".join(load_ips("ips.toml").topics) not in prompt


def test_the_output_format_carries_what_is_read():
    """measure and group_by are the model's; the topic is extraction's
    since 55dd80c and is not asked for."""
    assert '"measure": null' in ROUTER_SYSTEM_PROMPT
    assert '"group_by": null' in ROUTER_SYSTEM_PROMPT
    # status: the compliance report's breach selection, the model's too.
    assert '"status": null' in ROUTER_SYSTEM_PROMPT
    assert '"status": null' in REPAIR_PROMPT


def test_group_by_line_names_every_value_the_schema_allows():
    """The Group-by extraction rule and ExtractedParameters.group_by are two
    statements of one vocabulary; a value in the schema the prompt does not
    name is one the router is never told it may emit."""
    annotation = ExtractedParameters.model_fields["group_by"].annotation
    literal = [a for a in get_args(annotation) if get_args(a)][0]
    line = [l for l in ROUTER_SYSTEM_PROMPT.splitlines() if l.startswith("- Group by:")][0]
    for value in get_args(literal):
        assert f'"{value}"' in line, value


def test_status_line_names_every_value_the_schema_allows():
    """Same rule as group_by: the Status line and ExtractedParameters.status
    are two statements of one vocabulary."""
    annotation = ExtractedParameters.model_fields["status"].annotation
    literal = [a for a in get_args(annotation) if get_args(a)][0]
    line = [l for l in ROUTER_SYSTEM_PROMPT.splitlines() if l.startswith("- Status:")][0]
    for value in get_args(literal):
        assert f'"{value}"' in line, value


def test_intent_types_block_comes_from_intents():
    for value, description in INTENTS.items():
        assert f"- {value}: {description}" in ROUTER_SYSTEM_PROMPT, value


def test_intent_line_in_both_prompts_is_the_registry():
    joined = "|".join(INTENTS)
    for prompt in (ROUTER_SYSTEM_PROMPT, REPAIR_PROMPT):
        line = [l for l in prompt.splitlines() if l.lstrip().startswith('"intent": "')][0]
        assert f'"intent": "{joined}"' in line


def test_intent_type_is_built_from_intents():
    assert [m.value for m in IntentType] == list(INTENTS)
    assert IntentType.OUT_OF_SCOPE.value == "out_of_scope"
    assert IntentType["CLARIFICATION_NEEDED"] is IntentType.CLARIFICATION_NEEDED


def test_synthesizer_chain_is_held_to_the_registry():
    """The chain in synthesizer_node is a second statement of the vocabulary,
    checked rather than derived, as graph.AGENT_NODES is against AGENTS.
    clarification_needed exits the graph before the synthesizer and is the
    one value the chain does not format."""
    assert nodes.SYNTHESIZER_INTENTS | {"clarification_needed"} == set(INTENTS)
    nodes._check_synthesizer_intents(nodes.SYNTHESIZER_INTENTS)
    import pytest
    with pytest.raises(RuntimeError, match="planted"):
        nodes._check_synthesizer_intents(nodes.SYNTHESIZER_INTENTS | {"planted"})
    with pytest.raises(RuntimeError, match="compliance"):
        nodes._check_synthesizer_intents(nodes.SYNTHESIZER_INTENTS - {"compliance"})

