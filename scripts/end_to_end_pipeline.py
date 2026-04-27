#!/usr/bin/env python3
"""
End-to-End Pipeline: Discover → Profile → Stage → Mart → Validate → Semantic → Agent
=======================================================================================
Orchestrates the complete workflow from source discovery to a queryable
Cortex Agent registered in Snowflake Intelligence.

Pipeline Steps:
  1. Discover & Profile   — Connect to Snowflake, discover tables, profile columns
  2. Generate Staging     — Create staging models + source YAML + schema tests
  3. Generate Marts       — Create mart models (fct_, dim_, summary_)
  4. dbt Build & Validate — Run dbt build to compile, materialize, and test
  5. Generate Semantic     — Auto-create semantic views with verified queries
  6. dbt Build Semantic   — Build semantic views + attach verified queries
  7. Create Agent          — Generate Cortex Agent SQL bundling all semantic views
  8. Deploy (optional)    — Execute agent SQL in Snowflake + register in SI

Usage:
  # Full pipeline for a new source (interactive)
  python scripts/end_to_end_pipeline.py

  # Full pipeline (CLI mode)
  python scripts/end_to_end_pipeline.py \
    --source-database MY_DB \
    --source-schema MY_SCHEMA \
    --source-name my_source

  # Skip discovery (if staging/marts already exist)
  python scripts/end_to_end_pipeline.py --domain japan_ecomm_data --skip-discover

  # Dry run (preview all steps without executing)
  python scripts/end_to_end_pipeline.py --domain japan_ecomm_data --dry-run

  # With Snowflake Intelligence registration
  python scripts/end_to_end_pipeline.py --domain japan_ecomm_data --register-si
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_command(cmd: list, description: str, dry_run: bool = False) -> bool:
    """Run a shell command with logging."""
    cmd_str = " ".join(str(c) for c in cmd)
    print(f"\n  ▶ {description}")
    print(f"    $ {cmd_str}")

    if dry_run:
        print(f"    [DRY RUN] Would execute above command")
        return True

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"    ✗ Failed (exit code {result.returncode})")
            if result.stderr:
                # Show last 20 lines of stderr
                stderr_lines = result.stderr.strip().split("\n")[-20:]
                for line in stderr_lines:
                    print(f"      {line}")
            return False
        else:
            print(f"    ✓ Success")
            if result.stdout:
                # Show last 5 lines of stdout
                stdout_lines = result.stdout.strip().split("\n")[-5:]
                for line in stdout_lines:
                    print(f"      {line}")
            return True
    except subprocess.TimeoutExpired:
        print(f"    ✗ Timed out (300s)")
        return False
    except FileNotFoundError:
        print(f"    ✗ Command not found: {cmd[0]}")
        return False


def step_discover(args) -> str:
    """Step 1-3: Discover, profile, and generate staging + mart models."""
    print(f"\n{'='*60}")
    print(f"  STEP 1-3: Discover → Profile → Generate Models")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "discover_and_generate.py"),
        "--source-database", args.source_database,
        "--source-schema", args.source_schema,
    ]
    if args.source_name:
        cmd.extend(["--source-name", args.source_name])
    if args.overwrite:
        cmd.append("--overwrite")

    success = run_command(
        cmd,
        f"Discovering tables in {args.source_database}.{args.source_schema}",
        dry_run=args.dry_run,
    )

    if not success and not args.dry_run:
        print("\n  ✗ Discovery failed. Check Snowflake connection and credentials.")
        return None

    # Infer domain name from source_name
    domain = args.source_name or args.source_database.lower()
    return domain


def step_dbt_build(domain: str, selector: str, description: str, dry_run: bool = False) -> bool:
    """Step 4/6: Run dbt build with a selector."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")

    cmd = ["dbt", "build", "--select", selector]
    return run_command(cmd, f"dbt build --select {selector}", dry_run=dry_run)


def step_generate_semantic(domain: str, dry_run: bool = False, overwrite: bool = False) -> bool:
    """Step 5: Generate semantic views for the domain."""
    print(f"\n{'='*60}")
    print(f"  STEP 5: Generate Semantic Views")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "generate_semantic_views_for_domain.py"),
        "--domain", domain,
    ]
    if overwrite:
        cmd.append("--overwrite")
    if dry_run:
        cmd.append("--dry-run")

    return run_command(cmd, f"Generating semantic views for {domain}", dry_run=False)


def step_create_agent(
    domain: str,
    database: str,
    register_si: bool,
    dry_run: bool = False,
) -> bool:
    """Step 7: Generate Cortex Agent SQL."""
    print(f"\n{'='*60}")
    print(f"  STEP 7: Create Cortex Agent")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "create_domain_agent.py"),
        "--domain", domain,
        "--database", database,
    ]
    if register_si:
        cmd.append("--register-si")
    if dry_run:
        cmd.append("--dry-run")

    return run_command(cmd, f"Creating agent for {domain}", dry_run=False)


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end pipeline: Discover → Semantic Views → Agent"
    )

    # Source discovery args
    parser.add_argument("--source-database", help="Snowflake source database")
    parser.add_argument("--source-schema", help="Snowflake source schema")
    parser.add_argument("--source-name", help="dbt source name (default: derived from database)")

    # Skip/domain args
    parser.add_argument("--domain", help="Domain name (skip discovery, use existing marts)")
    parser.add_argument("--skip-discover", action="store_true", help="Skip steps 1-3 (use existing models)")

    # Config
    parser.add_argument("--database", default="DBT_DEV", help="Target Snowflake database")
    parser.add_argument("--register-si", action="store_true", help="Register agent in Snowflake Intelligence")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Preview all steps without executing")

    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  End-to-End Pipeline")
    print(f"  Discover → Stage → Mart → Validate → Semantic → Agent")
    print(f"{'='*60}")

    if args.dry_run:
        print(f"  MODE: DRY RUN (no files will be written or commands executed)")

    domain = args.domain

    # ─── Steps 1-3: Discover & Generate ─────────────────────────
    if not args.skip_discover and not domain:
        if not args.source_database or not args.source_schema:
            # Interactive mode
            print("\n  Source Discovery (interactive mode)")
            args.source_database = input("    Source database: ").strip()
            args.source_schema = input("    Source schema: ").strip()
            args.source_name = input("    Source name (optional, press Enter to derive): ").strip() or None

        domain = step_discover(args)
        if domain is None and not args.dry_run:
            sys.exit(1)
        if args.dry_run and not domain:
            domain = (args.source_name or args.source_database).lower()

    if not domain:
        # List available domains
        marts_dir = PROJECT_ROOT / "models" / "marts"
        domains = sorted(
            d.name for d in marts_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        if not domains:
            print("No domains found. Run without --skip-discover to create models first.")
            sys.exit(1)
        print("\nAvailable domains:")
        for i, d in enumerate(domains, 1):
            print(f"  {i}. {d}")
        try:
            choice = int(input("\nSelect domain: ").strip()) - 1
            domain = domains[choice]
        except (ValueError, IndexError):
            sys.exit(1)

    print(f"\n  Domain: {domain}")

    # ─── Step 4: dbt Build (staging + marts) ────────────────────
    if not args.skip_discover:
        step_dbt_build(
            domain,
            f"source:{domain}+",
            "STEP 4: dbt Build & Validate (staging + marts)",
            dry_run=args.dry_run,
        )

    # ─── Step 5: Generate Semantic Views ────────────────────────
    step_generate_semantic(domain, dry_run=args.dry_run, overwrite=args.overwrite)

    # ─── Step 6: dbt Build Semantic Views ───────────────────────
    step_dbt_build(
        domain,
        "tag:semantic",
        "STEP 6: dbt Build Semantic Views (+ verified queries post-hook)",
        dry_run=args.dry_run,
    )

    # ─── Step 7: Create Cortex Agent ────────────────────────────
    step_create_agent(domain, args.database, args.register_si, dry_run=args.dry_run)

    # ─── Summary ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Pipeline Complete!")
    print(f"{'='*60}")
    print(f"""
  What was done:
    1. {'[SKIPPED]' if args.skip_discover else '[DONE]'} Discover & profile source tables
    2. {'[SKIPPED]' if args.skip_discover else '[DONE]'} Generate staging + mart models
    3. {'[SKIPPED]' if args.skip_discover else '[DONE]'} dbt build & validate
    4. [DONE] Generate semantic views with verified queries
    5. [DONE] dbt build semantic views (post-hook attaches verified queries)
    6. [DONE] Create Cortex Agent SQL

  Next steps:
    1. Review agent SQL:  ddl/cortex-analyst/deploy_agent_{domain}.sql
    2. Execute in Snowflake (as DBT_ROLE, NOT ACCOUNTADMIN)
    3. Grant access:
       USE ROLE ACCOUNTADMIN;
       GRANT USAGE ON AGENT {args.database}.SEMANTIC.AGENT_{domain.upper()} TO ROLE CORTEX_ANALYST_ROLE;
    4. Test in Snowflake Intelligence:
       USE ROLE CORTEX_ANALYST_ROLE;
       SELECT {args.database}.SEMANTIC.AGENT_{domain.upper()}!PREDICT('What are the key metrics?');
    5. For Copilot users, set session role:
       USE ROLE CORTEX_ANALYST_ROLE;
""")


if __name__ == "__main__":
    main()
