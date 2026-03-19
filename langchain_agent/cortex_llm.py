"""Custom LangChain ChatModel wrapping Snowflake Cortex COMPLETE."""

import json
from typing import Any, Iterator, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from langchain_agent.snowflake_conn import get_connection

DEFAULT_MODEL = "mistral-large2"


def _message_to_dict(msg: BaseMessage) -> dict:
    """Convert a LangChain message to Cortex-compatible dict."""
    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": msg.content}
    elif isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}
    return {"role": "user", "content": str(msg.content)}


class SnowflakeCortexChat(BaseChatModel):
    """LangChain ChatModel backed by Snowflake Cortex COMPLETE.

    Uses ``SELECT SNOWFLAKE.CORTEX.COMPLETE(model, messages_json)``
    to call Cortex LLMs (mistral-large2, llama3.1-70b, etc.).
    """

    model_name: str = DEFAULT_MODEL
    temperature: float = 0.1
    max_tokens: int = 4096

    @property
    def _llm_type(self) -> str:
        return "snowflake-cortex"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model_name}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        cortex_messages = [_message_to_dict(m) for m in messages]

        conn = get_connection()
        cursor = conn.cursor()

        request_body = {
            "messages": cortex_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if stop:
            request_body["stop"] = stop

        try:
            cursor.execute(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)",
                (self.model_name, json.dumps(request_body)),
            )
            raw = cursor.fetchone()[0]
        finally:
            cursor.close()

        content = self._parse_cortex_response(raw)

        if run_manager:
            run_manager.on_llm_new_token(content)

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )

    @staticmethod
    def _parse_cortex_response(raw: str) -> str:
        """Extract text content from Cortex response.

        Cortex may return:
          - Plain text string
          - JSON with ``choices[0].messages`` or ``choices[0].message.content``
          - JSON with ``message`` or ``content`` keys
        """
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                if "choices" in parsed:
                    choice = parsed["choices"][0]
                    if "messages" in choice:
                        return choice["messages"]
                    if "message" in choice and isinstance(choice["message"], dict):
                        return choice["message"].get("content", raw)
                if "message" in parsed:
                    return parsed["message"]
                if "content" in parsed:
                    return parsed["content"]
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return raw
