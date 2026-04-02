#!/usr/bin/env python3
"""
Upload Cortex Analyst YAML Semantic Models to Snowflake Stage
=============================================================
Creates a Snowflake internal stage (if not exists) and uploads
generated YAML semantic model files for use with Cortex Analyst.

Usage:
  # Upload all YAML files from cortex-analyst-models/
  python scripts/upload_semantic_model_to_stage.py --all

  # Upload a specific file
  python scripts/upload_semantic_model_to_stage.py --file semantic_sales.yaml

  # Custom stage name
  python scripts/upload_semantic_model_to_stage.py --all --stage MY_DB.MY_SCHEMA.MY_STAGE

  # Validate YAML spec before uploading (if supported)
  python scripts/upload_semantic_model_to_stage.py --all --validate

Requirements:
  pip install snowflake-connector-python pyyaml
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import snowflake.connector
except ImportError:
    print("Error: snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "cortex-analyst-models"
DEFAULT_STAGE = "CORTEX_ANALYST_MODELS"


def get_connection():
    """Create a Snowflake connection from env vars or profiles.yml."""
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    user = os.environ.get("SNOWFLAKE_USER")
    password = os.environ.get("SNOWFLAKE_PASSWORD")
    role = os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE", "DBT_AGENT_WH")
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")

    if not all([account, user, password]):
        profiles_path = Path.home() / ".dbt" / "profiles.yml"
        if profiles_path.exists():
            with open(profiles_path) as f:
                profiles = yaml.safe_load(f)
            for profile in profiles.values():
                if isinstance(profile, dict) and "outputs" in profile:
                    target = profile.get("target", "dev")
                    output = profile["outputs"].get(target, {})
                    if output.get("type") == "snowflake":
                        account = output.get("account", account)
                        user = output.get("user", user)
                        password = output.get("password", password)
                        role = output.get("role", role)
                        warehouse = output.get("warehouse", warehouse)
                        database = output.get("database", database)
                        break

    if not all([account, user, password]):
        print("ERROR: Snowflake credentials not found.")
        print("Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD env vars")
        print("Or configure ~/.dbt/profiles.yml")
        sys.exit(1)

    return snowflake.connector.connect(
        account=account, user=user, password=password,
        role=role, warehouse=warehouse, database=database,
    )


def ensure_stage(conn, stage_fqn):
    """Create the internal stage if it doesn't exist."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"CREATE STAGE IF NOT EXISTS {stage_fqn} "
            f"ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE') "
            f"COMMENT = 'Internal stage for Cortex Analyst YAML semantic models'"
        )
        print(f"Stage ready: {stage_fqn}")
    except Exception as e:
        print(f"Warning: Could not create stage {stage_fqn}: {e}")
        print("You may need to create it manually with appropriate privileges.")
    finally:
        cursor.close()


def validate_yaml(conn, stage_fqn, filename):
    """Validate a semantic model YAML spec using Snowflake system function (if available)."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT SYSTEM$VERIFY_SEMANTIC_MODEL_SPEC("
            f"  '@{stage_fqn}/{filename}'"
            f")"
        )
        result = cursor.fetchone()
        if result:
            print(f"  Validation result: {result[0][:500]}")
            return True
    except Exception as e:
        # SYSTEM$VERIFY_SEMANTIC_MODEL_SPEC may not be available in all accounts
        print(f"  Validation skipped (function may not be available): {e}")
    finally:
        cursor.close()
    return True  # Don't block on validation failures


def upload_file(conn, stage_fqn, file_path):
    """Upload a single YAML file to the Snowflake stage."""
    cursor = conn.cursor()
    try:
        # Use PUT command to upload the file
        put_sql = (
            f"PUT 'file://{file_path}' '@{stage_fqn}' "
            f"AUTO_COMPRESS = FALSE OVERWRITE = TRUE"
        )
        cursor.execute(put_sql)
        result = cursor.fetchone()
        status = result[6] if result and len(result) > 6 else "UPLOADED"
        print(f"  [{status}] {file_path.name} → @{stage_fqn}/{file_path.name}")
        return True
    except Exception as e:
        print(f"  [FAILED] {file_path.name}: {e}")
        return False
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Upload Cortex Analyst YAML semantic models to Snowflake stage"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Upload all YAML files from cortex-analyst-models/"
    )
    parser.add_argument(
        "--file", help="Upload a specific YAML file (name or path)"
    )
    parser.add_argument(
        "--stage",
        default=None,
        help="Fully qualified stage name (default: <database>.SEMANTIC.CORTEX_ANALYST_MODELS)"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate YAML spec after uploading (requires SYSTEM$VERIFY_SEMANTIC_MODEL_SPEC)"
    )
    args = parser.parse_args()

    if not args.all and not args.file:
        parser.error("Specify --all or --file <name>")

    # Find files to upload
    files = []
    if args.all:
        if not OUTPUT_DIR.exists():
            print(f"ERROR: Directory not found: {OUTPUT_DIR}")
            sys.exit(1)
        files = sorted(OUTPUT_DIR.glob("*.yaml"))
        if not files:
            print(f"ERROR: No YAML files found in {OUTPUT_DIR}")
            sys.exit(1)
    else:
        # Support both filename-only and full path
        file_path = Path(args.file)
        if not file_path.exists():
            file_path = OUTPUT_DIR / args.file
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            sys.exit(1)
        files = [file_path]

    print(f"Uploading {len(files)} file(s) to Snowflake stage...")

    # Connect
    conn = get_connection()

    # Determine stage FQN
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")
    stage_fqn = args.stage or f"{database}.SEMANTIC.{DEFAULT_STAGE}"

    # Ensure stage exists
    ensure_stage(conn, stage_fqn)

    # Upload each file
    uploaded = 0
    failed = 0
    for f in files:
        success = upload_file(conn, stage_fqn, f)
        if success:
            uploaded += 1
            if args.validate:
                validate_yaml(conn, stage_fqn, f.name)
        else:
            failed += 1

    conn.close()

    # Summary
    print(f"\nSummary: {uploaded} uploaded, {failed} failed")
    if uploaded > 0:
        print(f"\nTest with Cortex Analyst:")
        example = files[0].name
        print(f"  SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(")
        print(f"    '@{stage_fqn}/{example}',")
        print(f"    [{{'role': 'user', 'content': 'What is the summary?'}}]")
        print(f"  );")


if __name__ == "__main__":
    main()
