"""CLI entry point for the LangChain dbt agent.

Mirrors the interactive experience of scripts/medallion_agent.py.

Usage:
    # Interactive chat
    python -m langchain_agent.cli

    # Single question
    python -m langchain_agent.cli --ask "What sources do I have?"

    # Custom Cortex model
    python -m langchain_agent.cli --model llama3.1-70b
"""

import argparse
import sys

from langchain_agent.agent import build_agent
from langchain_agent.callbacks import AutoBuildCallback, LoggingCallback
from langchain_agent.skills.router import get_skill_instructions


def run_interactive(model_name: str = "mistral-large2", initial_question: str = ""):
    """Run the agent in interactive CLI mode."""
    print("\n" + "=" * 60)
    print("  dbt Agent — Powered by LangChain + Snowflake Cortex")
    print("=" * 60)
    print("\nI can help you build silver (intermediate) and gold (marts)")
    print("layer models from your existing bronze (staging) data.")
    print("\nExamples:")
    print('  "What sources do I have?"')
    print('  "Show me sample data from the free_company_data staging table"')
    print('  "Suggest silver layer models for japan_ecomm_data"')
    print('  "Create a dimension table for countries from free_company_data"')
    print('\nType "quit" or "exit" to end.\n')

    chat_history = []

    if initial_question:
        user_input = initial_question
        print(f"You: {user_input}\n")
    else:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

    while user_input.lower() not in ("quit", "exit", "q"):
        if not user_input:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            continue

        # Route skills based on user input
        skill_instructions = get_skill_instructions(user_input)

        agent = build_agent(
            model_name=model_name,
            skill_instructions=skill_instructions,
        )

        callbacks = [LoggingCallback(), AutoBuildCallback()]

        result = agent.invoke(
            {
                "input": user_input,
                "chat_history": chat_history,
            },
            config={"callbacks": callbacks},
        )

        output = result.get("output", str(result))
        print(f"\nAgent: {output}\n")

        # Track history (prune to last 20 turns)
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": output})
        if len(chat_history) > 40:
            chat_history = chat_history[-40:]

        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

    print("\nGoodbye!")


def main():
    parser = argparse.ArgumentParser(description="dbt LangChain Agent CLI")
    parser.add_argument(
        "--model",
        default="mistral-large2",
        help="Cortex LLM model (default: mistral-large2)",
    )
    parser.add_argument("--ask", help="Ask a single question (non-interactive mode)")
    args = parser.parse_args()

    run_interactive(model_name=args.model, initial_question=args.ask or "")


if __name__ == "__main__":
    main()
