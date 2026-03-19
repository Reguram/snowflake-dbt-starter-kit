"""Skill-specific tools — additional tools required by dbt-agent-skills.

These extend the core tools with capabilities needed by the skill modules:
- dbt_show, dbt_list, dbt_parse, dbt_compile
- generate_unit_test, query_semantic_layer
- analyze_run_results, generate_mermaid_dag
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from langchain_agent.snowflake_conn import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


@tool
def dbt_show(select: str = "", limit: int = 5, inline_sql: str = "") -> str:
    """Preview model output using dbt show, or run inline SQL.

    Args:
        select: Model selector (e.g. 'stg_my_model').
        limit: Number of rows to preview (default 5).
        inline_sql: Optional inline SQL to run instead of a model.
    """
    cmd = ["dbt", "show"]
    if inline_sql:
        cmd.extend(["--inline", inline_sql])
    elif select:
        safe = re.sub(r"[^a-zA-Z0-9_+:.\-*/]", "", select)
        cmd.extend(["--select", safe])
    else:
        return json.dumps({"error": "Provide either 'select' or 'inline_sql'"})

    cmd.extend(["--limit", str(min(max(1, limit), 100))])

    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return json.dumps({"success": result.returncode == 0, "output": output[:5000]})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt show timed out (120s)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found"})


@tool
def dbt_list(select: str = "", resource_type: str = "", output_format: str = "name") -> str:
    """List dbt resources matching a selector.

    Args:
        select: dbt selector (e.g. '+fct_orders', 'tag:nightly').
        resource_type: Filter by type (model, test, source, seed, snapshot).
        output_format: Output format — 'name', 'path', or 'json'.
    """
    cmd = ["dbt", "ls"]
    if select:
        safe = re.sub(r"[^a-zA-Z0-9_+:.\-*/]", "", select)
        cmd.extend(["--select", safe])
    if resource_type:
        safe_type = re.sub(r"[^a-zA-Z]", "", resource_type)
        cmd.extend(["--resource-type", safe_type])
    if output_format in ("name", "path", "json"):
        cmd.extend(["--output", output_format])

    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=60,
        )
        output = result.stdout.strip()
        items = output.split("\n") if output else []
        return json.dumps({"count": len(items), "items": items[:200]})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt ls timed out (60s)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found"})


@tool
def dbt_parse() -> str:
    """Parse the dbt project to validate syntax and configuration.

    Useful for validating semantic models, YAML changes, and project structure.
    """
    try:
        result = subprocess.run(
            ["dbt", "parse"], cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return json.dumps({
            "success": result.returncode == 0,
            "output": output[:5000],
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt parse timed out (120s)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found"})


@tool
def dbt_compile(select: str = "") -> str:
    """Compile a dbt model to see the rendered SQL without executing.

    Args:
        select: Model selector to compile (e.g. 'fct_orders').
    """
    cmd = ["dbt", "compile"]
    if select:
        safe = re.sub(r"[^a-zA-Z0-9_+:.\-*/]", "", select)
        cmd.extend(["--select", safe])

    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")

        # Try to read the compiled SQL file
        compiled_sql = ""
        if select and result.returncode == 0:
            model_name = re.sub(r"[^a-zA-Z0-9_]", "", select)
            compiled_dir = PROJECT_ROOT / "target" / "compiled"
            for sql_file in compiled_dir.rglob(f"{model_name}.sql"):
                compiled_sql = sql_file.read_text()
                break

        return json.dumps({
            "success": result.returncode == 0,
            "output": output[:3000],
            "compiled_sql": compiled_sql[:5000] if compiled_sql else "",
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "dbt compile timed out (120s)"})
    except FileNotFoundError:
        return json.dumps({"error": "dbt CLI not found"})


@tool
def generate_unit_test(
    model_name: str,
    test_name: str,
    given_inputs: list[dict],
    expected_output: list[dict],
) -> str:
    """Generate a dbt unit test YAML definition and write it to disk.

    Args:
        model_name: The model to test.
        test_name: Descriptive test name (e.g. 'test_fct_orders_calculates_total').
        given_inputs: List of dicts with 'input' (ref name) and 'rows' (list of row dicts).
        expected_output: List of expected output row dicts.
    """
    import yaml

    unit_test = {
        "name": test_name,
        "model": model_name,
        "given": [
            {
                "input": f"ref('{inp['input']}')",
                "rows": inp["rows"],
            }
            for inp in given_inputs
        ],
        "expect": {
            "rows": expected_output,
        },
    }

    # Find the schema.yml for this model
    from langchain_agent.tools.exploration import _find_model_path

    model_path = _find_model_path(model_name)
    if model_path is None:
        return json.dumps({"error": f"Model '{model_name}' not found on disk"})

    schema_path = model_path.parent / "schema.yml"
    if schema_path.exists():
        data = yaml.safe_load(schema_path.read_text()) or {}
    else:
        data = {"version": 2}

    if "unit_tests" not in data:
        data["unit_tests"] = []

    # Check for duplicate test name
    existing = next((t for t in data["unit_tests"] if t.get("name") == test_name), None)
    if existing:
        data["unit_tests"].remove(existing)

    data["unit_tests"].append(unit_test)
    schema_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    return json.dumps({
        "created": str(schema_path.relative_to(PROJECT_ROOT)),
        "test_name": test_name,
        "model": model_name,
    })


@tool
def query_semantic_layer(metric: str, dimensions: list[str], filters: str = "") -> str:
    """Query via MetricFlow semantic layer (if available).

    Falls back to direct SQL query against the mart model.

    Args:
        metric: Metric name to query (e.g. 'total_revenue').
        dimensions: List of dimension names to group by.
        filters: Optional WHERE clause filter.
    """
    # Try MetricFlow CLI first
    cmd = ["mf", "query", "--metrics", metric]
    for dim in dimensions:
        cmd.extend(["--group-by", dim])
    if filters:
        cmd.extend(["--where", filters])

    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return json.dumps({"source": "metricflow", "output": result.stdout[:5000]})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: construct a direct SQL query
    dim_cols = ", ".join(dimensions)
    sql = f"SELECT {dim_cols}, {metric} FROM DBT_MARTS.{metric.upper()}"
    if filters:
        sql += f" WHERE {filters}"
    sql += f" GROUP BY {dim_cols} LIMIT 100"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, r)) for r in cursor.fetchmany(100)]
        cursor.close()
        return json.dumps({
            "source": "direct_sql",
            "columns": columns,
            "rows": rows,
        }, indent=2, default=str)
    except Exception as e:
        cursor.close()
        return json.dumps({"error": f"Query failed: {e}", "attempted_sql": sql})


@tool
def analyze_run_results() -> str:
    """Parse target/run_results.json for recent dbt run status, timing, and errors."""
    results_path = PROJECT_ROOT / "target" / "run_results.json"
    if not results_path.exists():
        return json.dumps({"error": "No run_results.json found. Run 'dbt build' first."})

    data = json.loads(results_path.read_text())

    summary = {
        "generated_at": data.get("metadata", {}).get("generated_at", ""),
        "elapsed_time": data.get("elapsed_time", 0),
        "total": len(data.get("results", [])),
        "pass": 0,
        "error": 0,
        "skip": 0,
        "warn": 0,
        "failures": [],
    }

    for r in data.get("results", []):
        status = r.get("status", "")
        if status in ("pass", "success"):
            summary["pass"] += 1
        elif status in ("error", "fail"):
            summary["error"] += 1
            summary["failures"].append({
                "unique_id": r.get("unique_id", ""),
                "status": status,
                "message": r.get("message", "")[:500],
                "execution_time": r.get("execution_time", 0),
            })
        elif status == "skip":
            summary["skip"] += 1
        elif status == "warn":
            summary["warn"] += 1

    return json.dumps(summary, indent=2)


@tool
def generate_mermaid_dag(select: str = "", source_name: str = "") -> str:
    """Generate a Mermaid flowchart diagram showing dbt model dependencies.

    Args:
        select: Optional dbt selector to filter models.
        source_name: Optional source name to filter by.
    """
    edges = []
    nodes = set()

    # Scan model files for {{ ref('...') }} calls
    layers = ["staging", "intermediate", "marts", "semantic"]
    for layer in layers:
        layer_dir = MODELS_DIR / layer
        if not layer_dir.exists():
            continue
        for sql_file in layer_dir.rglob("*.sql"):
            model_name = sql_file.stem
            if source_name and source_name.lower() not in model_name.lower():
                if source_name.lower() not in sql_file.parent.name.lower():
                    continue
            if select and select.lower() not in model_name.lower():
                continue

            nodes.add(model_name)
            sql = sql_file.read_text()
            refs = re.findall(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", sql)
            for ref in refs:
                nodes.add(ref)
                edges.append((ref, model_name))

            sources = re.findall(
                r"\{\{\s*source\(['\"](\w+)['\"],\s*['\"](\w+)['\"]\)\s*\}\}", sql
            )
            for src_name, tbl_name in sources:
                src_node = f"src_{src_name}__{tbl_name.lower()}"
                nodes.add(src_node)
                edges.append((src_node, model_name))

    if not edges:
        return json.dumps({"error": "No dependencies found matching filters"})

    # Build Mermaid diagram
    lines = ["graph LR"]
    for node in sorted(nodes):
        if node.startswith("src_"):
            lines.append(f"    {node}[({node})]")
        elif node.startswith("stg_"):
            lines.append(f"    {node}[{node}]")
        elif node.startswith("int_"):
            lines.append(f"    {node}([{node}])")
        elif node.startswith("fct_") or node.startswith("dim_"):
            lines.append(f"    {node}{{{{{node}}}}}")
        else:
            lines.append(f"    {node}[{node}]")

    for src, tgt in edges:
        lines.append(f"    {src} --> {tgt}")

    mermaid = "\n".join(lines)
    return json.dumps({
        "node_count": len(nodes),
        "edge_count": len(edges),
        "mermaid": mermaid,
    })


# Exported list for agent.py to discover
SKILL_TOOLS = [
    dbt_show,
    dbt_list,
    dbt_parse,
    dbt_compile,
    generate_unit_test,
    query_semantic_layer,
    analyze_run_results,
    generate_mermaid_dag,
]
