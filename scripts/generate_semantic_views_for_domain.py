#!/usr/bin/env python3
"""
Auto-Generate Semantic Views for All Marts in a Domain
=======================================================
Scans models/marts/<domain>/ for all mart models (fct_*, dim_*, summary_*),
reads their schema.yml columns, auto-classifies dimensions vs metrics,
and generates:
  1. models/semantic/sem_<model>/sem_<model>.sql   — DDL-like semantic view
  2. models/semantic/sem_<model>/sem_<model>.yml   — verified queries + description

Designed to plug into the existing dbt_semantic_view materialization with
publish_verified_queries() post-hook.

Usage:
  # Generate semantic views for all marts in a domain
  python scripts/generate_semantic_views_for_domain.py --domain japan_ecomm_data

  # Dry run (preview without writing files)
  python scripts/generate_semantic_views_for_domain.py --domain covid19_data --dry-run

  # Overwrite existing semantic views
  python scripts/generate_semantic_views_for_domain.py --domain japan_ecomm_data --overwrite

  # Generate for ALL domains
  python scripts/generate_semantic_views_for_domain.py --all
"""

import argparse
import math
import os
import re
import sys
import time
from pathlib import Path

import yaml

# ─── Paths ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
MARTS_DIR = MODELS_DIR / "marts"
SEMANTIC_DIR = MODELS_DIR / "semantic"


# ─── Column Classification Rules ────────────────────────────

# Patterns that indicate a DIMENSION
DIMENSION_PATTERNS = [
    # Date/time dimensions
    (r".*_date$", "time"),
    (r".*_at$", "time"),
    (r".*_timestamp$", "time"),
    (r".*_month$", "time"),
    (r".*_quarter$", "time"),
    (r".*_year$", "time"),
    (r"^date$", "time"),
    (r"^month$", "time"),
    (r"^year$", "time"),
    (r".*_period$", "time"),
    # Categorical dimensions
    (r".*_status$", "categorical"),
    (r".*_type$", "categorical"),
    (r".*_category$", "categorical"),
    (r".*_segment$", "categorical"),
    (r".*_class$", "categorical"),
    (r".*_tier$", "categorical"),
    (r".*_level$", "categorical"),
    (r".*_group$", "categorical"),
    (r".*_flag$", "categorical"),
    (r"^is_.*", "categorical"),
    (r"^has_.*", "categorical"),
    # Entity dimensions
    (r".*_name$", "entity"),
    (r".*_region$", "entity"),
    (r".*_country$", "entity"),
    (r".*_city$", "entity"),
    (r".*_state$", "entity"),
    (r".*_province$", "entity"),
    (r".*_county$", "entity"),
    (r".*_code$", "entity"),
    (r"^maker$", "entity"),
    (r"^brand$", "entity"),
    (r"^vendor$", "entity"),
    (r"^manufacturer$", "entity"),
    (r"^iso.*", "entity"),
]

# Patterns that indicate a METRIC
METRIC_PATTERNS = [
    # Sum metrics (amounts/quantities)
    (r".*_amount$", "SUM"),
    (r".*_revenue$", "SUM"),
    (r".*_sales$", "SUM"),
    (r".*_cost$", "SUM"),
    (r".*_price$", "SUM"),
    (r".*_total$", "SUM"),
    (r".*_quantity$", "SUM"),
    (r".*_qty$", "SUM"),
    (r".*_count$", "SUM"),
    (r"^total_.*", "SUM"),
    (r"^sum_.*", "SUM"),
    (r"^transaction_count$", "SUM"),
    # Average metrics
    (r".*_rate$", "AVG"),
    (r".*_percentage$", "AVG"),
    (r".*_pct$", "AVG"),
    (r".*_ratio$", "AVG"),
    (r".*_utilization$", "AVG"),
    (r"^average_.*", "AVG"),
    (r"^avg_.*", "AVG"),
    (r"^mean_.*", "AVG"),
    # Min/Max metrics
    (r"^min_.*", "MIN"),
    (r"^max_.*", "MAX"),
    (r"^first_.*", "MIN"),
    (r"^last_.*", "MAX"),
]

# Keys to skip (not dimensions or metrics)
KEY_PATTERNS = [
    r".*_key$",
    r".*_id$",
    r".*_sk$",
    r".*_surrogate$",
]


def classify_column(col_name: str) -> tuple:
    """
    Classify a column as dimension, metric, or key.
    Returns: (classification, subtype)
      - ("dimension", "time"|"categorical"|"entity")
      - ("metric", "SUM"|"AVG"|"MIN"|"MAX"|"COUNT")
      - ("key", "skip")
      - ("unknown", "")
    """
    name = col_name.lower()

    # Check keys first (skip these)
    for pattern in KEY_PATTERNS:
        if re.match(pattern, name):
            return ("key", "skip")

    # Check dimensions
    for pattern, subtype in DIMENSION_PATTERNS:
        if re.match(pattern, name):
            return ("dimension", subtype)

    # Check metrics
    for pattern, agg in METRIC_PATTERNS:
        if re.match(pattern, name):
            return ("metric", agg)

    return ("unknown", "")


def read_schema_yml(domain_dir: Path) -> dict:
    """Read schema.yml from a domain's marts directory."""
    schema_path = domain_dir / "schema.yml"
    if not schema_path.exists():
        return {}

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    if not schema or "models" not in schema:
        return {}

    # Build a dict: model_name -> {description, columns: [{name, description, tests}]}
    models = {}
    for model in schema["models"]:
        name = model.get("name", "")
        models[name] = {
            "description": model.get("description", ""),
            "columns": model.get("columns", []),
        }
    return models


def get_sql_columns_from_file(sql_path: Path) -> list:
    """
    Extract column names from a dbt SQL model file by parsing the final SELECT.
    Falls back to regex-based extraction.
    """
    with open(sql_path) as f:
        content = f.read()

    # Try to find columns in the final select statement
    # Look for 'select ... from final' or the last select block
    columns = []

    # Match column names in select statements (handles aliases)
    # Pattern: column_name or expression AS column_name
    select_pattern = re.findall(
        r"(?:select|,)\s+(?:.*?\s+as\s+)?(\w+)\s*(?:,|$|\bfrom\b)",
        content,
        re.IGNORECASE | re.DOTALL,
    )

    for col in select_pattern:
        col = col.strip().lower()
        if col and col not in ("select", "from", "final", "base", "*"):
            columns.append(col)

    return list(dict.fromkeys(columns))  # deduplicate preserving order


def generate_semantic_view_sql(
    model_name: str,
    ref_model: str,
    dimensions: list,
    metrics: list,
    description: str,
) -> str:
    """Generate the semantic view .sql file content."""
    # Create alias from model name
    alias = ref_model.split("_")[0]  # fct -> fct, dim -> dim, summary -> summary
    if alias in ("fct", "dim", "summary"):
        alias = ref_model.replace(f"{alias}_", "")[:10]  # use entity name, truncated
    alias = re.sub(r"[^a-z0-9]", "", alias)[:8] or "t"

    lines = []
    lines.append("{{")
    lines.append("  config(")
    lines.append("    materialized = 'semantic_view',")
    lines.append("    schema = 'SEMANTIC',")
    lines.append(f"    tags = ['semantic', '{model_name}'],")
    lines.append("    post_hook = [")
    lines.append('      "{{ publish_verified_queries() }}"')
    lines.append("    ]")
    lines.append("  )")
    lines.append("}}")
    lines.append("")
    lines.append("TABLES (")
    lines.append(f"  {alias} AS {{{{ ref('{ref_model}') }}}}")
    lines.append(")")
    lines.append("DIMENSIONS (")

    dim_lines = []
    for d in dimensions:
        col_name = d["name"]
        comment = d.get("description", col_name.replace("_", " ").title())
        comment = comment.replace("'", "''")
        dim_lines.append(
            f"  {alias}.{col_name} AS {col_name}\n    COMMENT = '{comment}'"
        )
    lines.append(",\n".join(dim_lines))

    lines.append(")")
    lines.append("METRICS (")

    metric_lines = []
    for m in metrics:
        col_name = m["name"]
        agg = m["aggregation"]
        metric_alias = f"{agg.lower()}_{col_name}" if not col_name.startswith(f"{agg.lower()}_") and not col_name.startswith("total_") else col_name
        comment = m.get("description", col_name.replace("_", " ").title())
        comment = comment.replace("'", "''")
        metric_lines.append(
            f"  {alias}.{metric_alias} AS {agg}({col_name})\n    COMMENT = '{comment}'"
        )
    lines.append(",\n".join(metric_lines))

    lines.append(")")
    lines.append(f"COMMENT = '{description.replace(chr(39), chr(39)+chr(39))}'")
    lines.append("")

    # AI_SQL_GENERATION instructions (single-dash + $$ delimiters)
    lines.append("- AI_SQL_GENERATION $$")
    dim_names = ", ".join(d["name"] for d in dimensions)
    metric_names = ", ".join(m["name"] for m in metrics)
    lines.append(f"- Dimensions available for filtering/grouping: {dim_names}")
    lines.append(f"- Metrics available for aggregation: {metric_names}")
    time_dims = [d["name"] for d in dimensions if d.get("subtype") == "time"]
    if time_dims:
        lines.append(
            f"- For time-based analysis, group by: {', '.join(time_dims)}"
        )
    lines.append(f"- Base model: {ref_model}")
    lines.append("$$")

    return "\n".join(lines) + "\n"


def generate_verified_queries(
    model_name: str,
    alias: str,
    dimensions: list,
    metrics: list,
    description: str,
) -> list:
    """Auto-generate 3-5 verified queries based on dimensions and metrics."""
    queries = []
    now_ts = int(time.time())

    # Query 1: Top-level aggregation by first categorical/entity dimension
    cat_dims = [d for d in dimensions if d.get("subtype") in ("categorical", "entity")]
    time_dims = [d for d in dimensions if d.get("subtype") == "time"]

    if metrics:
        primary_metric = metrics[0]
        metric_col = primary_metric["name"]
        metric_agg = primary_metric["aggregation"]

        if cat_dims:
            dim = cat_dims[0]
            queries.append({
                "name": f"{metric_agg.lower()}_{metric_col}_by_{dim['name']}",
                "question": f"What is the {metric_agg.lower()} of {metric_col.replace('_', ' ')} by {dim['name'].replace('_', ' ')}?",
                "verified_at": now_ts,
                "verified_by": "auto_generator",
                "sql": (
                    f"SELECT {dim['name']}, {metric_agg}({metric_col}) AS {metric_agg.lower()}_{metric_col}\n"
                    f"FROM {alias}\n"
                    f"GROUP BY {dim['name']}\n"
                    f"ORDER BY {metric_agg.lower()}_{metric_col} DESC"
                ),
            })

        # Query 2: Time trend
        if time_dims:
            time_dim = time_dims[0]
            queries.append({
                "name": f"{metric_col}_over_time",
                "question": f"Show the trend of {metric_col.replace('_', ' ')} over time",
                "verified_at": now_ts,
                "verified_by": "auto_generator",
                "sql": (
                    f"SELECT {time_dim['name']}, {metric_agg}({metric_col}) AS {metric_agg.lower()}_{metric_col}\n"
                    f"FROM {alias}\n"
                    f"GROUP BY {time_dim['name']}\n"
                    f"ORDER BY {time_dim['name']} DESC\n"
                    f"LIMIT 30"
                ),
            })

        # Query 3: Multi-metric summary
        if len(metrics) > 1:
            metric_selects = ", ".join(
                f"{m['aggregation']}({m['name']}) AS {m['aggregation'].lower()}_{m['name']}"
                for m in metrics[:3]
            )
            if cat_dims:
                dim = cat_dims[0]
                queries.append({
                    "name": f"summary_by_{dim['name']}",
                    "question": f"Give me a summary of all metrics by {dim['name'].replace('_', ' ')}",
                    "verified_at": now_ts,
                    "verified_by": "auto_generator",
                    "sql": (
                        f"SELECT {dim['name']}, {metric_selects}\n"
                        f"FROM {alias}\n"
                        f"GROUP BY {dim['name']}\n"
                        f"ORDER BY {metrics[0]['aggregation'].lower()}_{metrics[0]['name']} DESC"
                    ),
                })

        # Query 4: Top N query
        if cat_dims:
            dim = cat_dims[0]
            queries.append({
                "name": f"top_10_{dim['name']}_by_{metric_col}",
                "question": f"What are the top 10 {dim['name'].replace('_', ' ')}s by {metric_col.replace('_', ' ')}?",
                "verified_at": now_ts,
                "verified_by": "auto_generator",
                "sql": (
                    f"SELECT {dim['name']}, {metric_agg}({metric_col}) AS {metric_agg.lower()}_{metric_col}\n"
                    f"FROM {alias}\n"
                    f"GROUP BY {dim['name']}\n"
                    f"ORDER BY {metric_agg.lower()}_{metric_col} DESC\n"
                    f"LIMIT 10"
                ),
            })

        # Query 5: Cross-dimension analysis
        if len(cat_dims) >= 2:
            dim1 = cat_dims[0]
            dim2 = cat_dims[1]
            queries.append({
                "name": f"{metric_col}_by_{dim1['name']}_and_{dim2['name']}",
                "question": f"Break down {metric_col.replace('_', ' ')} by {dim1['name'].replace('_', ' ')} and {dim2['name'].replace('_', ' ')}",
                "verified_at": now_ts,
                "verified_by": "auto_generator",
                "sql": (
                    f"SELECT {dim1['name']}, {dim2['name']}, {metric_agg}({metric_col}) AS {metric_agg.lower()}_{metric_col}\n"
                    f"FROM {alias}\n"
                    f"GROUP BY {dim1['name']}, {dim2['name']}\n"
                    f"ORDER BY {metric_agg.lower()}_{metric_col} DESC"
                ),
            })

    return queries


def generate_semantic_view_yml(
    model_name: str,
    description: str,
    verified_queries: list,
) -> str:
    """Generate the semantic view .yml file content."""
    yml_data = {
        "version": 2,
        "models": [
            {
                "name": model_name,
                "description": description,
                "config": {
                    "meta": {
                        "verified_queries": verified_queries,
                    }
                },
            }
        ],
    }

    return yaml.dump(yml_data, default_flow_style=False, sort_keys=False, width=120)


def process_mart_model(
    model_name: str,
    sql_path: Path,
    schema_info: dict,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict:
    """Process a single mart model and generate semantic view files."""
    sem_name = f"sem_{model_name.replace('fct_', '').replace('dim_', '').replace('summary_', '')}"
    sem_dir = SEMANTIC_DIR / sem_name

    # Check if already exists
    if sem_dir.exists() and not overwrite:
        return {"model": model_name, "status": "skipped", "reason": "already exists"}

    # Get columns from schema.yml
    columns = schema_info.get("columns", [])
    if not columns:
        # Try extracting from SQL
        sql_cols = get_sql_columns_from_file(sql_path)
        columns = [{"name": c, "description": ""} for c in sql_cols]

    if not columns:
        return {"model": model_name, "status": "skipped", "reason": "no columns found"}

    # Classify columns
    dimensions = []
    metrics = []
    for col in columns:
        col_name = col.get("name", "").lower()
        if not col_name:
            continue

        classification, subtype = classify_column(col_name)

        if classification == "dimension":
            dimensions.append({
                "name": col_name,
                "description": col.get("description", col_name.replace("_", " ").title()),
                "subtype": subtype,
            })
        elif classification == "metric":
            metrics.append({
                "name": col_name,
                "description": col.get("description", col_name.replace("_", " ").title()),
                "aggregation": subtype,
            })
        elif classification == "unknown":
            # Default: treat VARCHAR-like names as dimensions, NUMBER-like as metrics
            # Use naming heuristics as fallback
            dimensions.append({
                "name": col_name,
                "description": col.get("description", col_name.replace("_", " ").title()),
                "subtype": "entity",
            })

    if not dimensions and not metrics:
        return {"model": model_name, "status": "skipped", "reason": "no dims/metrics classified"}

    # Generate alias
    alias_base = model_name.replace("fct_", "").replace("dim_", "").replace("summary_", "")
    alias = re.sub(r"[^a-z0-9]", "", alias_base)[:8] or "t"

    # Model description
    description = schema_info.get("description", "").strip()
    if not description:
        description = f"Semantic view for {model_name} — auto-generated"

    sem_description = f"Semantic view for {model_name}. {description}"

    # Generate SQL
    sql_content = generate_semantic_view_sql(
        model_name=sem_name,
        ref_model=model_name,
        dimensions=dimensions,
        metrics=metrics,
        description=sem_description[:200],
    )

    # Generate verified queries
    verified_queries = generate_verified_queries(
        model_name=sem_name,
        alias=alias,
        dimensions=dimensions,
        metrics=metrics,
        description=description,
    )

    # Generate YML
    yml_content = generate_semantic_view_yml(
        model_name=sem_name,
        description=sem_description,
        verified_queries=verified_queries,
    )

    if dry_run:
        print(f"\n{'='*60}")
        print(f"  DRY RUN: {sem_name}")
        print(f"{'='*60}")
        print(f"  Dimensions: {len(dimensions)}")
        for d in dimensions:
            print(f"    - {d['name']} ({d['subtype']})")
        print(f"  Metrics: {len(metrics)}")
        for m in metrics:
            print(f"    - {m['name']} ({m['aggregation']})")
        print(f"  Verified Queries: {len(verified_queries)}")
        for vq in verified_queries:
            print(f"    - {vq['name']}: {vq['question']}")
        print(f"  Would write:")
        print(f"    {sem_dir / f'{sem_name}.sql'}")
        print(f"    {sem_dir / f'{sem_name}.yml'}")
        return {"model": model_name, "status": "dry_run", "sem_name": sem_name}

    # Write files
    sem_dir.mkdir(parents=True, exist_ok=True)

    sql_path_out = sem_dir / f"{sem_name}.sql"
    yml_path_out = sem_dir / f"{sem_name}.yml"

    with open(sql_path_out, "w") as f:
        f.write(sql_content)

    with open(yml_path_out, "w") as f:
        f.write(yml_content)

    print(f"  ✓ Created {sem_name}/")
    print(f"    - {sql_path_out.relative_to(PROJECT_ROOT)}")
    print(f"    - {yml_path_out.relative_to(PROJECT_ROOT)}")

    return {
        "model": model_name,
        "status": "created",
        "sem_name": sem_name,
        "dimensions": len(dimensions),
        "metrics": len(metrics),
        "verified_queries": len(verified_queries),
    }


def process_domain(domain: str, dry_run: bool = False, overwrite: bool = False) -> list:
    """Process all mart models in a domain."""
    domain_dir = MARTS_DIR / domain
    if not domain_dir.exists():
        print(f"ERROR: Domain directory not found: {domain_dir}")
        return []

    print(f"\n{'='*60}")
    print(f"  Processing domain: {domain}")
    print(f"{'='*60}")

    # Read schema.yml
    schema_models = read_schema_yml(domain_dir)

    # Find all SQL model files
    sql_files = sorted(domain_dir.glob("*.sql"))
    results = []

    for sql_path in sql_files:
        model_name = sql_path.stem
        schema_info = schema_models.get(model_name, {"description": "", "columns": []})

        result = process_mart_model(
            model_name=model_name,
            sql_path=sql_path,
            schema_info=schema_info,
            dry_run=dry_run,
            overwrite=overwrite,
        )
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate Snowflake Semantic Views for mart models"
    )
    parser.add_argument(
        "--domain",
        help="Domain name (subdirectory under models/marts/)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all domains under models/marts/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be generated without writing files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing semantic view files",
    )

    args = parser.parse_args()

    if not args.domain and not args.all:
        # List available domains
        domains = [d.name for d in MARTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if not domains:
            print("No domains found under models/marts/")
            sys.exit(1)

        print("Available domains:")
        for i, d in enumerate(sorted(domains), 1):
            mart_count = len(list((MARTS_DIR / d).glob("*.sql")))
            print(f"  {i}. {d} ({mart_count} models)")

        try:
            choice = input("\nSelect domain number (or 'all'): ").strip()
            if choice.lower() == "all":
                args.all = True
            else:
                idx = int(choice) - 1
                args.domain = sorted(domains)[idx]
        except (ValueError, IndexError):
            print("Invalid selection")
            sys.exit(1)

    # Process domains
    all_results = []
    if args.all:
        domains = sorted(
            d.name for d in MARTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        for domain in domains:
            results = process_domain(domain, dry_run=args.dry_run, overwrite=args.overwrite)
            all_results.extend(results)
    else:
        results = process_domain(args.domain, dry_run=args.dry_run, overwrite=args.overwrite)
        all_results.extend(results)

    # Summary
    created = [r for r in all_results if r["status"] == "created"]
    skipped = [r for r in all_results if r["status"] == "skipped"]
    dry_runs = [r for r in all_results if r["status"] == "dry_run"]

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    if created:
        print(f"  Created: {len(created)} semantic views")
        for r in created:
            print(f"    ✓ {r['sem_name']} ({r['dimensions']}D / {r['metrics']}M / {r['verified_queries']}VQ)")
    if dry_runs:
        print(f"  Would create: {len(dry_runs)} semantic views")
    if skipped:
        print(f"  Skipped: {len(skipped)}")
        for r in skipped:
            print(f"    - {r['model']}: {r['reason']}")

    if created:
        print(f"\n  Next steps:")
        print(f"    1. Review generated files in models/semantic/")
        print(f"    2. Run: dbt build --select tag:semantic")
        print(f"    3. Verify in Snowflake: SHOW SEMANTIC VIEWS IN SCHEMA DBT_DEV.SEMANTIC;")


if __name__ == "__main__":
    main()
