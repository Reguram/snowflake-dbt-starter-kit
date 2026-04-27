#!/usr/bin/env python3
"""
Create a Cortex Agent for a Domain — Bundles All Semantic Views
================================================================
Scans models/semantic/ for all semantic views belonging to a domain,
generates a single Cortex Agent SQL that bundles them all as
cortex_analyst_text_to_sql tools, and optionally registers the agent
in Snowflake Intelligence.

The agent uses semantic views (not YAML files on stage) — this means
the verified queries attached via publish_verified_queries() post-hook
are automatically available to the agent.

Usage:
  # Generate agent SQL for a domain
  python scripts/create_domain_agent.py --domain japan_ecomm_data

  # Generate agent SQL for all domains
  python scripts/create_domain_agent.py --all

  # Specify database/schema/warehouse
  python scripts/create_domain_agent.py --domain covid19_data \
    --database DBT_DEV --schema SEMANTIC --warehouse DBT_AGENT_WH

  # Include Snowflake Intelligence registration
  python scripts/create_domain_agent.py --domain japan_ecomm_data --register-si
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

# ─── Paths ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
SEMANTIC_DIR = MODELS_DIR / "semantic"
MARTS_DIR = MODELS_DIR / "marts"
DDL_DIR = PROJECT_ROOT / "ddl" / "cortex-analyst"


def find_semantic_views_for_domain(domain: str) -> list:
    """
    Find all semantic views that reference mart models in a given domain.
    Parses each sem_*.sql to find {{ ref('model_name') }} and checks
    if that model exists under models/marts/<domain>/.
    """
    domain_marts_dir = MARTS_DIR / domain
    if not domain_marts_dir.exists():
        return []

    # Get all mart model names in this domain
    domain_models = {
        f.stem for f in domain_marts_dir.glob("*.sql")
    }

    semantic_views = []

    # Scan all semantic view directories and standalone .sql files
    for item in sorted(SEMANTIC_DIR.iterdir()):
        sql_path = None
        yml_path = None

        if item.is_dir() and item.name.startswith("sem_"):
            # Subfolder pattern: sem_<name>/sem_<name>.sql
            sql_path = item / f"{item.name}.sql"
            yml_path = item / f"{item.name}.yml"
            if not sql_path.exists():
                continue
        elif item.is_file() and item.name.startswith("sem_") and item.suffix == ".sql":
            sql_path = item
            # Check for adjacent yml
            yml_path = item.with_suffix(".yml")
        else:
            continue

        # Read SQL to find ref() targets
        with open(sql_path) as f:
            sql_content = f.read()

        # Extract all {{ ref('model_name') }} references
        refs = re.findall(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", sql_content)

        # Check if any ref points to a model in this domain
        matching_refs = [r for r in refs if r in domain_models]
        if not matching_refs:
            continue

        # Get description from yml if available
        description = ""
        if yml_path and yml_path.exists():
            with open(yml_path) as f:
                yml_data = yaml.safe_load(f)
            if yml_data and "models" in yml_data:
                for m in yml_data["models"]:
                    description = m.get("description", "")
                    break

        # Fallback: extract COMMENT from SQL
        if not description:
            comment_match = re.search(r"COMMENT\s*=\s*'([^']*)'", sql_content)
            if comment_match:
                description = comment_match.group(1)

        sem_name = sql_path.stem
        semantic_views.append({
            "name": sem_name,
            "sql_path": str(sql_path.relative_to(PROJECT_ROOT)),
            "refs": matching_refs,
            "description": description or f"Semantic view for {', '.join(matching_refs)}",
        })

    return semantic_views


def generate_agent_sql(
    domain: str,
    semantic_views: list,
    database: str = "DBT_DEV",
    schema: str = "SEMANTIC",
    warehouse: str = "DBT_AGENT_WH",
    role: str = "CORTEX_ANALYST_ROLE",
    register_si: bool = False,
) -> str:
    """Generate CREATE AGENT SQL for a domain with all semantic views as tools."""

    agent_name = f"AGENT_{domain.upper()}"
    domain_label = domain.replace("_", " ").title()

    # Build tools array — one tool per semantic view
    tools = []
    tool_resources = {}

    for sv in semantic_views:
        # Tool name: short, unique identifier (max ~30 chars)
        tool_name = sv["name"].replace("sem_", "")[:30]
        tool_name = re.sub(r"[^a-z0-9_]", "_", tool_name)

        # Tool description: what questions this semantic view can answer
        tool_desc = sv["description"][:500]

        tools.append({
            "tool_spec": {
                "type": "cortex_analyst_text_to_sql",
                "name": tool_name,
                "description": tool_desc,
            }
        })

        # Semantic view reference (fully qualified)
        sv_fqn = f"{database}.{schema}.{sv['name'].upper()}"
        tool_resources[tool_name] = {
            "semantic_view": sv_fqn,
            "execution_environment": {
                "type": "warehouse",
                "warehouse": warehouse,
            },
        }

    # Build the spec JSON
    spec = {
        "models": {"orchestration": "auto"},
        "tools": tools,
        "tool_resources": tool_resources,
    }

    spec_json = json.dumps(spec, indent=2)

    # Build SQL
    lines = []
    lines.append(f"-- =============================================================================")
    lines.append(f"-- Cortex Agent for Domain: {domain_label}")
    lines.append(f"-- Bundles {len(semantic_views)} semantic view(s) into a single agent")
    lines.append(f"-- Auto-generated by scripts/create_domain_agent.py")
    lines.append(f"-- =============================================================================")
    lines.append(f"")
    lines.append(f"-- ─── Prerequisites ──────────────────────────────────────────────────────────")
    lines.append(f"-- 1. All semantic views must be built: dbt build --select tag:semantic")
    lines.append(f"-- 2. CORTEX_ANALYST_ROLE must exist: run scripts/snowflake_cortex_rbac_setup.sql")
    lines.append(f"-- 3. Use a role with CREATE AGENT privilege (DBT_ROLE or SYSADMIN)")
    lines.append(f"")
    lines.append(f"USE ROLE DBT_ROLE;")
    lines.append(f"USE WAREHOUSE {warehouse};")
    lines.append(f"USE DATABASE {database};")
    lines.append(f"USE SCHEMA {schema};")
    lines.append(f"")

    # List semantic views included
    lines.append(f"-- ─── Semantic Views Included ────────────────────────────────────────────────")
    for sv in semantic_views:
        lines.append(f"-- • {sv['name'].upper()} → refs: {', '.join(sv['refs'])}")
    lines.append(f"")

    # Verify semantic views exist
    lines.append(f"-- ─── Step 1: Verify Semantic Views Exist ────────────────────────────────────")
    lines.append(f"SHOW SEMANTIC VIEWS IN SCHEMA {database}.{schema};")
    lines.append(f"-- Confirm all {len(semantic_views)} views appear in the output")
    lines.append(f"")

    # Create agent
    lines.append(f"-- ─── Step 2: Create Cortex Agent ────────────────────────────────────────────")
    lines.append(f"CREATE OR REPLACE AGENT {database}.{schema}.{agent_name}")
    lines.append(f"  COMMENT = 'Cortex Agent for {domain_label} — {len(semantic_views)} semantic views, created for Snowflake Intelligence NL querying'")
    lines.append(f"  FROM SPECIFICATION $$")
    lines.append(spec_json)
    lines.append(f"  $$;")
    lines.append(f"")

    # Verify agent
    lines.append(f"-- ─── Step 3: Verify Agent ───────────────────────────────────────────────────")
    lines.append(f"SHOW AGENTS IN SCHEMA {database}.{schema};")
    lines.append(f"DESCRIBE AGENT {database}.{schema}.{agent_name};")
    lines.append(f"")

    # Grant permissions to CORTEX_ANALYST_ROLE
    lines.append(f"-- ─── Step 4: Grant Access to CORTEX_ANALYST_ROLE ────────────────────────────")
    lines.append(f"-- (Run as ACCOUNTADMIN or SECURITYADMIN)")
    lines.append(f"-- GRANT USAGE ON AGENT {database}.{schema}.{agent_name} TO ROLE {role};")
    lines.append(f"")

    # Register in Snowflake Intelligence
    if register_si:
        lines.append(f"-- ─── Step 5: Register in Snowflake Intelligence ────────────────────────────")
        lines.append(f"-- Ensure SI object exists:")
        lines.append(f"-- SHOW SNOWFLAKE INTELLIGENCES;")
        lines.append(f"-- If no rows: CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;")
        lines.append(f"")
        lines.append(f"ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT")
        lines.append(f"  ADD AGENT {database}.{schema}.{agent_name};")
        lines.append(f"")
        lines.append(f"-- Grant SI access to CORTEX_ANALYST_ROLE")
        lines.append(f"-- GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT")
        lines.append(f"--   TO ROLE {role};")
        lines.append(f"")

    # Test section
    lines.append(f"-- ─── Test the Agent ─────────────────────────────────────────────────────────")
    lines.append(f"-- In Snowsight: AI & ML → Snowflake Intelligence → select {agent_name}")
    lines.append(f"-- Or programmatically:")
    lines.append(f"-- SELECT {database}.{schema}.{agent_name}!PREDICT(")
    lines.append(f"--   'What are the key metrics?'")
    lines.append(f"-- );")
    lines.append(f"")
    lines.append(f"-- ─── Done ───────────────────────────────────────────────────────────────────")
    lines.append(f"SELECT '{agent_name} created with {len(semantic_views)} semantic views' AS status;")

    return "\n".join(lines) + "\n"


def process_domain(
    domain: str,
    database: str,
    schema: str,
    warehouse: str,
    role: str,
    register_si: bool,
    dry_run: bool,
) -> dict:
    """Process a single domain and generate agent SQL."""
    semantic_views = find_semantic_views_for_domain(domain)

    if not semantic_views:
        print(f"  ⚠ No semantic views found for domain '{domain}'")
        return {"domain": domain, "status": "skipped", "reason": "no semantic views"}

    print(f"\n  Domain: {domain}")
    print(f"  Semantic views found: {len(semantic_views)}")
    for sv in semantic_views:
        print(f"    • {sv['name']} → {', '.join(sv['refs'])}")

    if dry_run:
        return {"domain": domain, "status": "dry_run", "views": len(semantic_views)}

    # Generate SQL
    agent_sql = generate_agent_sql(
        domain=domain,
        semantic_views=semantic_views,
        database=database,
        schema=schema,
        warehouse=warehouse,
        role=role,
        register_si=register_si,
    )

    # Write to ddl/cortex-analyst/
    DDL_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DDL_DIR / f"deploy_agent_{domain}.sql"

    with open(output_path, "w") as f:
        f.write(agent_sql)

    print(f"  ✓ Agent SQL written to: {output_path.relative_to(PROJECT_ROOT)}")
    return {
        "domain": domain,
        "status": "created",
        "views": len(semantic_views),
        "output": str(output_path.relative_to(PROJECT_ROOT)),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create Cortex Agent for a domain with all semantic views"
    )
    parser.add_argument("--domain", help="Domain name (subdirectory under models/marts/)")
    parser.add_argument("--all", action="store_true", help="Create agents for all domains")
    parser.add_argument("--database", default="DBT_DEV", help="Snowflake database (default: DBT_DEV)")
    parser.add_argument("--schema", default="SEMANTIC", help="Schema for agents (default: SEMANTIC)")
    parser.add_argument("--warehouse", default="DBT_AGENT_WH", help="Warehouse (default: DBT_AGENT_WH)")
    parser.add_argument("--role", default="CORTEX_ANALYST_ROLE", help="Role for grants (default: CORTEX_ANALYST_ROLE)")
    parser.add_argument("--register-si", action="store_true", help="Include Snowflake Intelligence registration")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    args = parser.parse_args()

    if not args.domain and not args.all:
        # List available domains
        domains = sorted(
            d.name for d in MARTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        print("Available domains:")
        for i, d in enumerate(domains, 1):
            sv_count = len(find_semantic_views_for_domain(d))
            print(f"  {i}. {d} ({sv_count} semantic views)")

        try:
            choice = input("\nSelect domain number (or 'all'): ").strip()
            if choice.lower() == "all":
                args.all = True
            else:
                idx = int(choice) - 1
                args.domain = domains[idx]
        except (ValueError, IndexError):
            print("Invalid selection")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Cortex Agent Generator")
    print(f"{'='*60}")

    all_results = []
    if args.all:
        domains = sorted(
            d.name for d in MARTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        for domain in domains:
            result = process_domain(
                domain, args.database, args.schema, args.warehouse,
                args.role, args.register_si, args.dry_run,
            )
            all_results.append(result)
    else:
        result = process_domain(
            args.domain, args.database, args.schema, args.warehouse,
            args.role, args.register_si, args.dry_run,
        )
        all_results.append(result)

    # Summary
    created = [r for r in all_results if r["status"] == "created"]
    skipped = [r for r in all_results if r["status"] == "skipped"]

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    if created:
        print(f"  Created: {len(created)} agent SQL files")
        for r in created:
            print(f"    ✓ AGENT_{r['domain'].upper()} ({r['views']} semantic views)")
            print(f"      → {r['output']}")
    if skipped:
        print(f"  Skipped: {len(skipped)} domains")
        for r in skipped:
            print(f"    - {r['domain']}: {r['reason']}")

    if created:
        print(f"\n  Next steps:")
        print(f"    1. Review generated SQL in ddl/cortex-analyst/")
        print(f"    2. Execute in Snowflake (Snowsight worksheet or CLI)")
        print(f"    3. Test via Snowflake Intelligence or agent API")
        print(f"    4. Grant access: GRANT USAGE ON AGENT ... TO ROLE CORTEX_ANALYST_ROLE;")


if __name__ == "__main__":
    main()
