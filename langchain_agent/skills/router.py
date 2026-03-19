"""Skill router — dynamically selects and injects skill instructions based on user intent.

Uses keyword matching with optional LLM fallback. Selects 1-2 skills per query
and returns their combined instructions for injection into the agent prompt.
"""

from typing import Optional

from langchain_agent.skills import analytics_engineering
from langchain_agent.skills import unit_testing
from langchain_agent.skills import semantic_layer
from langchain_agent.skills import nl_questions
from langchain_agent.skills import troubleshooting
from langchain_agent.skills import dbt_commands
from langchain_agent.skills import dbt_docs
from langchain_agent.skills import mermaid_dag

# Registry of all available skills
SKILL_REGISTRY = [
    analytics_engineering,
    unit_testing,
    semantic_layer,
    nl_questions,
    troubleshooting,
    dbt_commands,
    dbt_docs,
    mermaid_dag,
]

# Maximum number of skills to inject per query (to keep prompt size manageable)
MAX_SKILLS = 2

# Maximum total character length for skill instructions
MAX_INSTRUCTION_LENGTH = 4000


def _score_skill(user_input: str, skill_module) -> int:
    """Score a skill based on keyword matches in the user input."""
    input_lower = user_input.lower()
    score = 0
    for keyword in skill_module.KEYWORDS:
        keyword_lower = keyword.lower()
        if keyword_lower in input_lower:
            # Longer keywords get higher scores (more specific)
            score += len(keyword_lower)
    return score


def get_skill_instructions(user_input: str, max_skills: int = MAX_SKILLS) -> str:
    """Route user input to the most relevant skill(s) and return their instructions.

    Args:
        user_input: The user's message/question.
        max_skills: Maximum number of skills to include.

    Returns:
        Combined skill instructions string to inject into the prompt.
        Empty string if no skills match.
    """
    scored = [
        (skill, _score_skill(user_input, skill))
        for skill in SKILL_REGISTRY
    ]
    # Filter out zero-score skills and sort by score descending
    matched = [(s, score) for s, score in scored if score > 0]
    matched.sort(key=lambda x: x[1], reverse=True)

    if not matched:
        return ""

    # Take top N skills
    selected = matched[:max_skills]
    instructions_parts = []
    total_len = 0

    for skill, _score in selected:
        text = skill.INSTRUCTIONS
        # Truncate individual skill if it would exceed budget
        remaining = MAX_INSTRUCTION_LENGTH - total_len
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining] + "\n... (truncated)"
        instructions_parts.append(text)
        total_len += len(text)

    return "\n\n".join(instructions_parts)


def list_available_skills() -> list[dict]:
    """Return metadata about all available skills."""
    return [
        {
            "name": s.SKILL_NAME,
            "keywords": s.KEYWORDS[:5],  # First 5 keywords as preview
        }
        for s in SKILL_REGISTRY
    ]
