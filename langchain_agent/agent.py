"""LangChain agent construction — ReAct agent with Snowflake Cortex.

Uses ``create_react_agent`` + ``AgentExecutor`` since Cortex doesn't support
structured function calling (no OpenAI-style tool_calls).
"""

import json
from typing import Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_agent.cortex_llm import SnowflakeCortexChat
from langchain_agent.prompts import REACT_PROMPT
from langchain_agent.tools.exploration import (
    describe_table,
    list_models,
    list_sources,
    profile_data,
    read_model,
    run_query,
    sample_data,
)
from langchain_agent.tools.generation import (
    generate_gold_model,
    generate_silver_model,
    generate_staging_model,
    modify_model,
)
from langchain_agent.tools.dbt_ops import (
    check_data_quality,
    review_sql,
    run_dbt,
)
from langchain_agent.tools.advanced import (
    generate_semantic_view,
    generate_streamlit_app,
)
from langchain_agent.tools.discovery import (
    auto_generate_staging,
    classify_columns,
    discover_tables,
)

# Lazy-loaded skill tools (Phase 6)
_SKILL_TOOLS = None


def _get_skill_tools():
    """Load skill-specific tools lazily to avoid circular imports."""
    global _SKILL_TOOLS
    if _SKILL_TOOLS is None:
        try:
            from langchain_agent.tools.skill_tools import SKILL_TOOLS

            _SKILL_TOOLS = SKILL_TOOLS
        except ImportError:
            _SKILL_TOOLS = []
    return _SKILL_TOOLS


# Core tools available to the agent
CORE_TOOLS = [
    # Exploration
    list_sources,
    list_models,
    read_model,
    sample_data,
    describe_table,
    profile_data,
    run_query,
    # Generation
    generate_silver_model,
    generate_gold_model,
    modify_model,
    generate_staging_model,
    # dbt ops
    run_dbt,
    check_data_quality,
    review_sql,
    # Advanced
    generate_semantic_view,
    generate_streamlit_app,
    # Discovery
    discover_tables,
    classify_columns,
    auto_generate_staging,
]

# Session-level message history store keyed by session_id
_message_stores: dict[str, InMemoryChatMessageHistory] = {}


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _message_stores:
        _message_stores[session_id] = InMemoryChatMessageHistory()
    history = _message_stores[session_id]
    # Prune to last 20 messages to keep context manageable
    if len(history.messages) > 20:
        history.messages = history.messages[-20:]
    return history


def build_agent(
    model_name: str = "mistral-large2",
    temperature: float = 0.1,
    max_iterations: int = 10,
    skill_instructions: str = "",
) -> AgentExecutor:
    """Build and return a LangChain ReAct AgentExecutor.

    Args:
        model_name: Cortex model to use.
        temperature: LLM temperature.
        max_iterations: Max tool-calling rounds.
        skill_instructions: Extra skill-specific instructions to inject.

    Returns:
        Configured AgentExecutor ready for ``.invoke()``.
    """
    llm = SnowflakeCortexChat(
        model_name=model_name,
        temperature=temperature,
    )

    all_tools = CORE_TOOLS + _get_skill_tools()

    prompt = REACT_PROMPT.partial(
        skill_instructions=skill_instructions,
    )

    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=all_tools,
        max_iterations=max_iterations,
        handle_parsing_errors=True,
        verbose=True,
    )


def build_agent_with_history(
    model_name: str = "mistral-large2",
    temperature: float = 0.1,
    max_iterations: int = 10,
    skill_instructions: str = "",
) -> RunnableWithMessageHistory:
    """Build an agent wrapped with conversation history management.

    Returns a ``RunnableWithMessageHistory`` that tracks chat per session_id.
    """
    executor = build_agent(
        model_name=model_name,
        temperature=temperature,
        max_iterations=max_iterations,
        skill_instructions=skill_instructions,
    )

    return RunnableWithMessageHistory(
        executor,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
