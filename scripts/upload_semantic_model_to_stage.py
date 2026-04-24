#!/usr/bin/env python3
# ==============================================================================
# DEPRECATED — This script is archived. Use Snowflake Semantic Views instead.
# The project now uses the dbt_semantic_view package with publish_verified_queries()
# post-hook. No staging/PUT is needed.
# ==============================================================================
"""
Upload Cortex Analyst YAML Semantic Models to Snowflake Stage (DEPRECATED)
==========================================================================
Creates a Snowflake internal stage (if not exists) and uploads
generated YAML semantic model files for use with Cortex Analyst.

DEPRECATED: Use Snowflake Semantic Views (models/semantic/) instead.

Usage:
  # Upload all YAML files from cortex-analyst-models/
  python scripts/upload_semantic_model_to_stage.py --all

  # Upload a specific file
  python scripts/upload_semantic_model_to_stage.py --file semantic_sales.yaml

  # Custom stage name
  python scripts/upload_semantic_model_to_stage.py --all --stage MY_DB.MY_SCHEMA.MY_STAGE

  # Validate YAML spec before uploading (if supported)
  python scripts/upload_semantic_model_to_stage.py --all --validate

  # Generate SQL for Snowflake worksheet / Cortex Code (no local PUT needed)
  python scripts/upload_semantic_model_to_stage.py --file semantic_japan_ecomm_data.yaml --generate-sql

  # Generate SQL for all YAML files
  python scripts/upload_semantic_model_to_stage.py --all --generate-sql

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


def upload_file_via_stream(conn, stage_fqn, file_path):
    """Upload a YAML file using put_stream (works when PUT file:// doesn't).

    This is a fallback that reads the file into memory and uploads via
    the Snowpark file transfer API, avoiding local filesystem path issues.
    """
    try:
        import io
        content = file_path.read_bytes()
        cursor = conn.cursor()
        # Use the write_pandas / file_transfer approach
        cursor.execute(f"USE SCHEMA {stage_fqn.rsplit('.', 1)[0].rsplit('.', 1)[-1]}")

        # Try Snowpark session for put_stream
        from snowflake.snowpark import Session
        session = Session.builder.configs({
            "connection": conn
        }).create()
        input_stream = io.BytesIO(content)
        session.file.put_stream(
            input_stream,
            f"@{stage_fqn}/{file_path.name}",
            auto_compress=False,
            overwrite=True,
        )
        print(f"  [UPLOADED via stream] {file_path.name} → @{stage_fqn}/{file_path.name}")
        return True
    except ImportError:
        print(f"  [SKIPPED] snowflake-snowpark-python not installed for stream upload")
        return False
    except Exception as e:
        print(f"  [FAILED stream] {file_path.name}: {e}")
        return False


def generate_upload_sql(stage_fqn, file_path):
    """Generate SQL that can be run in Snowflake worksheet or Cortex Code
    to upload a YAML file to a stage using a Python stored procedure.

    Why this is needed:
    - PUT requires a LOCAL file system path — it does NOT work from Snowflake
      worksheets or Cortex Code (which run inside Snowflake, not on your machine)
    - COPY INTO @stage FROM (SELECT ...) writes CSV/Parquet format, not raw YAML
    - A Python stored procedure with put_stream() is the correct Snowflake-native approach
    """
    content = file_path.read_text(encoding="utf-8")
    # Escape single quotes for SQL string literal
    escaped_content = content.replace("\\", "\\\\").replace("'", "\\'")

    # Extract database and schema from stage_fqn (e.g. DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS)
    parts = stage_fqn.split(".")
    database = parts[0] if len(parts) >= 1 else "DBT_DEV"
    schema = parts[1] if len(parts) >= 2 else "SEMANTIC"

    sql = f"""-- =============================================================================
-- Upload {file_path.name} to @{stage_fqn}
-- Run this in a Snowflake Worksheet, Snowsight, or Cortex Code
-- =============================================================================

-- Step 1: Ensure the stage exists
CREATE STAGE IF NOT EXISTS {stage_fqn}
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Internal stage for Cortex Analyst YAML semantic models';

-- Step 2: Create the upload procedure (one-time setup, idempotent)
CREATE OR REPLACE PROCEDURE {database}.{schema}.UPLOAD_YAML_TO_STAGE(
    STAGE_PATH VARCHAR,
    FILE_NAME VARCHAR,
    YAML_CONTENT VARCHAR
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
AS
$$
import io

def main(session, stage_path, file_name, yaml_content):
    input_stream = io.BytesIO(yaml_content.encode('utf-8'))
    session.file.put_stream(
        input_stream,
        f'{{stage_path}}/{{file_name}}',
        auto_compress=False,
        overwrite=True
    )
    return f'Successfully uploaded {{file_name}} to {{stage_path}}'
$$;

-- Step 3: Upload the YAML file
CALL {database}.{schema}.UPLOAD_YAML_TO_STAGE(
    '@{stage_fqn}',
    '{file_path.name}',
    $YAML_CONTENT$
{content}
$YAML_CONTENT$
);

-- Step 4: Verify the upload
LIST @{stage_fqn};

-- Step 5: Validate the semantic model (optional)
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_VALIDATE(
    BUILD_SCOPED_FILE_URL('@{stage_fqn}', '{file_path.name}')
);

-- Step 6: Test with Cortex Analyst
-- SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
--     '@{stage_fqn}/{file_path.name}',
--     [{{'role': 'user', 'content': 'What are the total daily sales?'}}]
-- );
"""
    return sql


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
    parser.add_argument(
        "--generate-sql", action="store_true",
        help="Generate SQL for Snowflake worksheet/Cortex Code instead of uploading via PUT"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write generated SQL files (default: ddl/cortex-analyst/)"
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

    # Determine stage FQN
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")
    stage_fqn = args.stage or f"{database}.SEMANTIC.{DEFAULT_STAGE}"

    # ── Generate SQL mode ──
    if args.generate_sql:
        sql_output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "ddl" / "cortex-analyst"
        sql_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Generating upload SQL for {len(files)} file(s)...")
        for f in files:
            sql = generate_upload_sql(stage_fqn, f)
            sql_filename = f"upload_{f.stem}.sql"
            sql_path = sql_output_dir / sql_filename
            sql_path.write_text(sql, encoding="utf-8")
            print(f"  Wrote: {sql_path.relative_to(PROJECT_ROOT)}")

        print(f"\nGenerated {len(files)} SQL file(s) in {sql_output_dir.relative_to(PROJECT_ROOT)}/")
        print(f"\nTo upload, run the SQL in a Snowflake Worksheet or Snowsight.")
        print(f"The SQL creates a Python stored procedure and calls it — no PUT needed.")
        return

    # ── Direct upload mode (requires local Snowflake connector) ──
    print(f"Uploading {len(files)} file(s) to Snowflake stage...")

    # Connect
    conn = get_connection()

    # Ensure stage exists
    ensure_stage(conn, stage_fqn)

    # Upload each file
    uploaded = 0
    failed = 0
    for f in files:
        success = upload_file(conn, stage_fqn, f)
        if not success:
            # Fallback to stream upload if PUT file:// fails
            print(f"  Retrying with stream upload...")
            success = upload_file_via_stream(conn, stage_fqn, f)
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
