"""Callback handlers for the dbt LangChain agent.

- StreamlitCallbackHandler: streams tokens to Streamlit UI
- AutoBuildCallback: auto-runs dbt build after model generation tools
- LoggingCallback: console debug logging
"""

import json
from typing import Any, Optional

from langchain_core.callbacks import BaseCallbackHandler


class StreamlitCallbackHandler(BaseCallbackHandler):
    """Streams LLM tokens and tool events to a Streamlit container."""

    def __init__(self, container):
        self.container = container
        self._text = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self._text += token
        self.container.markdown(self._text + "▌")

    def on_llm_end(self, response, **kwargs) -> None:
        self.container.markdown(self._text)

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        tool_name = serialized.get("name", "tool")
        self.container.status(f"Calling {tool_name}...")

    def on_tool_end(self, output: str, **kwargs) -> None:
        try:
            parsed = json.loads(output)
            if "error" in parsed:
                self.container.error(f"Tool error: {parsed['error']}")
            elif "created" in parsed:
                self.container.success(f"Created: {parsed['created']}")
            elif "modified" in parsed:
                self.container.success(f"Modified: {parsed['modified']}")
        except (json.JSONDecodeError, TypeError):
            pass


class AutoBuildCallback(BaseCallbackHandler):
    """Automatically runs dbt build after model generation tools complete."""

    def __init__(self):
        self.generated_models: list[str] = []

    def on_tool_end(self, output: str, name: Optional[str] = None, **kwargs) -> None:
        if name not in ("generate_silver_model", "generate_gold_model"):
            return
        try:
            parsed = json.loads(output)
            if "model_name" in parsed:
                self.generated_models.append(parsed["model_name"])
        except (json.JSONDecodeError, TypeError):
            pass

    def on_agent_finish(self, finish, **kwargs) -> None:
        """After agent finishes, trigger dbt build for generated models."""
        if not self.generated_models:
            return
        from langchain_agent.tools.dbt_ops import run_dbt

        selector = " ".join(self.generated_models)
        print(f"\n  [Auto-building {len(self.generated_models)} model(s): {selector}...]")
        result_str = run_dbt.invoke({"command": "build", "select": selector})
        try:
            result = json.loads(result_str)
            if result.get("success"):
                print("  [Build PASSED ✔]")
            else:
                print("  [Build FAILED ✘]")
                output_lines = result.get("output", "").strip().splitlines()
                for line in output_lines[-15:]:
                    print(f"    {line}")
        except (json.JSONDecodeError, TypeError):
            pass

        self.generated_models.clear()


class LoggingCallback(BaseCallbackHandler):
    """Simple console logging for debugging."""

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs) -> None:
        print(f"[LLM] Starting with {len(prompts)} prompt(s)")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        tool_name = serialized.get("name", "tool")
        print(f"  [Calling {tool_name}...]")

    def on_tool_end(self, output: str, **kwargs) -> None:
        try:
            parsed = json.loads(output)
            if "error" in parsed:
                print(f"  [Error: {parsed['error']}]")
            elif "created" in parsed:
                print(f"  [Created: {parsed['created']}]")
            elif "modified" in parsed:
                print(f"  [Modified: {parsed['modified']}]")
            else:
                print("  [Done]")
        except (json.JSONDecodeError, TypeError):
            print("  [Done]")
