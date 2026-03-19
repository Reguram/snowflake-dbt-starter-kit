"""dbt operations tools — run dbt, test data quality, review SQL.

Ported from snowflake-dbt-mcp/server.py.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ─── SQL Review Rules ─────────────────────────────────────────

_SQL_REVIEW_RULES = [
    {
        "id": "no_select_star",
        "pattern": r"\bSELECT\s+\*\b",
        "severity": "warning",
        "message": "Avoid SELECT * in marts/semantic models — list columns explicitly",
        "exclude_layers": ["staging"],
    },
    {
        "id": "no_hardcoded_db",
        "pattern": r"(?i)\bFROM\s+\w+\.\w+\.\w+\b",
        "severity": "error",
        "message": "Hard-coded database.schema.table reference — use {{ ref() }} or {{ source() }}",
    },
    {
        "id": "missing_ref",
        "pattern": r"(?i)\bFROM\s+(?!.*\{\{)\s*(stg_|int_|fct_|dim_)\w+",
        "severity": "error",
        "message": "Model name used without {{ ref() }} wrapper",
    },
    {
        "id": "no_limit",
        "pattern": r"(?i)\bLIMIT\s+\d+\b",
        "severity": "warning",
        "message": "LIMIT clause in model — remove for production",
    },
    {
        "id": "no_semicolon",
        "pattern": r";\s*$",
        "severity": "info",
        "message": "Trailing semicolon — dbt models shouldn't end with ;",
    },
]


@tool
def run_dbt(command: str = "build", select: str = "", full_refresh: bool = False) -> str:
    """Execute a dbt CLI command (build, run, test, compile, ls, debug, deps).

    Args:
        command: dbt command to run.
        select: Optional dbt selector (e.g. 'stg_my_model' or '+fct_orders').
        full_refresh: Whether to pass --full-refresh flag.
    """
    allowed = {"run", "test", "build", "compile", "ls", "debug", "deps"}
    if command not in allowed:
        return json.dumps({"error": f"Command '{command}' not allowed. Use: {', '.join(sorted(allowed))}"})

    cmd = ["dbt", command]
    if select:
        safe_select = re.sub(r"[^a-zA-Z0-9_+:.\-*/]", "", select)
        cmd.extend(["--select", safe_select])
    if full_refresh:
        cmd.append("--full-refresh")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return json.dumps({
            "success": result.returncode == 0,
            "output": output[:5000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt command timed out (300s limit)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found. Install with: pip install dbt-snowflake"})


@tool
def check_data_quality(select: str = "") -> str:
    """Run dbt tests and return a pass/fail summary.

    Args:
        select: Optional dbt selector to limit which tests to run.
    """
    cmd = ["dbt", "test"]
    if select:
        safe_select = re.sub(r"[^a-zA-Z0-9_+:.\-*/]", "", select)
        cmd.extend(["--select", safe_select])

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return json.dumps({
            "all_passed": result.returncode == 0,
            "output": output[:5000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt test timed out (300s limit)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found"})


@tool
def review_sql(sql_content: str, file_path: str = "") -> str:
    """Static analysis of SQL content against dbt best-practice rules.

    Args:
        sql_content: SQL text to review.
        file_path: Optional file path for context (used to detect layer).
    """
    issues = []
    lines = sql_content.split("\n")
    layer = ""
    if file_path:
        for lyr in ("staging", "intermediate", "marts", "semantic"):
            if lyr in file_path:
                layer = lyr
                break

    for rule in _SQL_REVIEW_RULES:
        if layer and layer in rule.get("exclude_layers", []):
            continue
        pattern = re.compile(rule["pattern"])
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                issue = {
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "line": i,
                    "message": rule["message"],
                    "content": line.strip(),
                }
                issues.append(issue)

    if not issues:
        return json.dumps({"status": "clean", "message": "No issues found"})

    return json.dumps({"status": "issues_found", "count": len(issues), "issues": issues}, indent=2)
