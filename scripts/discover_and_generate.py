#!/usr/bin/env python3
"""
Snowflake Source Discovery & dbt Model Generator
=================================================
Connects to Snowflake, discovers tables in a source database/schema,
and auto-generates:
  1. models/staging/_sources.yml       — dbt source definition
  2. models/staging/stg_<src>__<tbl>.sql — one staging model per table
  3. models/staging/schema.yml         — column descriptions + tests
  4. models/marts/overview.sql         — a starter mart (optional)

Usage:
  python scripts/discover_and_generate.py \\
    --source-database MY_DATABASE \\
    --source-schema RAW_DATA \\
    --source-name my_source

  # Or interactively (no args):
  python scripts/discover_and_generate.py
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import snowflake.connector
except ImportError:
    print("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    sys.exit(1)


# ─── Paths ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def get_snowflake_connection(cli_args=None):
    """Create a Snowflake connection from CLI args, env vars, or ~/.dbt/profiles.yml."""
    # Try CLI args first, then env vars
    account = getattr(cli_args, 'account', None) or os.environ.get("SNOWFLAKE_ACCOUNT")
    user = getattr(cli_args, 'user', None) or os.environ.get("SNOWFLAKE_USER")
    password = getattr(cli_args, 'password', None) or os.environ.get("SNOWFLAKE_PASSWORD")
    role = getattr(cli_args, 'role', None) or os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE")
    warehouse = getattr(cli_args, 'warehouse', None) or os.environ.get("SNOWFLAKE_WAREHOUSE", "DBT_AGENT_WH")
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")

    if not all([account, user, password]):
        # Try reading from profiles.yml
        profiles_path = Path.home() / ".dbt" / "profiles.yml"
        if profiles_path.exists():
            import yaml
            with open(profiles_path) as f:
                profiles = yaml.safe_load(f)
            # Find the first profile with type: snowflake
            for profile_name, profile in profiles.items():
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
        print("ERROR: Cannot find Snowflake credentials.")
        print("Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD env vars")
        print("or configure ~/.dbt/profiles.yml")
        sys.exit(1)

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
    )


def discover_tables(conn, source_database, source_schema):
    """Query INFORMATION_SCHEMA to discover all tables and their columns."""
    cursor = conn.cursor()

    # Get all tables
    cursor.execute(f"""
        SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT, COMMENT
        FROM {source_database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{source_schema.upper()}'
          AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_NAME
    """)
    tables = []
    for row in cursor:
        tables.append({
            "name": row[0],
            "type": row[1],
            "row_count": row[2],
            "comment": row[3] or "",
        })

    # Get columns for each table using DESCRIBE TABLE
    # (more reliable than INFORMATION_SCHEMA for Marketplace shared datasets)
    for table in tables:
        cursor.execute(
            f'DESCRIBE TABLE {source_database}.{source_schema}."{table["name"]}"'
        )
        table["columns"] = []
        for idx, col_row in enumerate(cursor, start=1):
            table["columns"].append({
                "name": col_row[0],          # column name
                "data_type": col_row[1],      # data type
                "nullable": col_row[3] == "Y", # null?
                "position": idx,
                "comment": col_row[8] if len(col_row) > 8 and col_row[8] else "",
            })

    cursor.close()
    return tables


def make_snake_case(name):
    """Convert UPPER_CASE column name to clean snake_case."""
    return name.lower()


def _yaml_safe_name(name):
    """Quote a YAML value if it contains special characters."""
    if any(ch in name for ch in ':{}[]&*?|>!%@`#,'):
        escaped = name.replace('"', '\\"')
        return f'"{escaped}"'
    return name


def _sql_identifier(name):
    """Quote a SQL identifier if needed for Snowflake.

    Snowflake uppercases unquoted identifiers. We must double-quote when:
      - the name contains non-alphanumeric chars (e.g. spaces, hyphens)
      - the name contains lowercase letters (mixed-case like B25001e1)
      - the name starts with a digit
    For purely uppercase alphanumeric names, return lowercase (Snowflake default).
    """
    # Pure uppercase alphanumeric (safe to use unquoted, return as lowercase)
    if re.match(r'^[A-Z_][A-Z0-9_]*$', name):
        return name.lower()
    # Contains lowercase or special chars — must quote to preserve exact name
    return f'"{name}"'


def strip_prefix(col_name, table_name):
    """
    Strip common single-letter prefixes from column names.
    E.g., O_ORDERKEY -> orderkey, C_CUSTKEY -> custkey
    Also handles table-initial prefixes (e.g., PS_ for PARTSUPP).
    """
    lower = col_name.lower()
    parts = lower.split("_", 1)
    # Single-letter prefix: O_, C_, L_, N_, R_, S_, P_
    if len(parts) > 1 and len(parts[0]) == 1:
        return parts[1]
    # Two-letter prefix matching table initials (e.g., PS_ for PARTSUPP)
    if len(parts) > 1 and len(parts[0]) == 2:
        table_initials = "".join(w[0] for w in table_name.lower().split("_") if w)
        if parts[0] == table_initials[:2]:
            return parts[1]
    return lower


def detect_primary_key(columns, table_name):
    """Heuristic: first column ending in KEY or ID, or first column."""
    for col in columns:
        lower = col["name"].lower()
        if lower.endswith("key") or lower.endswith("id") or lower.endswith("_pk"):
            return col["name"]
    return columns[0]["name"] if columns else None


def verify_uniqueness(conn, source_database, source_schema, table_name, column_name):
    """Query actual data to check if a column is truly unique and non-null."""
    try:
        cursor = conn.cursor()
        col_sql = _sql_identifier(column_name)
        cursor.execute(f"""
            SELECT COUNT(*) AS total,
                   COUNT(DISTINCT {col_sql}) AS distinct_count,
                   COUNT({col_sql}) AS non_null_count
            FROM {source_database}.{source_schema}."{table_name}"
        """)
        row = cursor.fetchone()
        cursor.close()
        if row:
            total, distinct, non_null = row[0], row[1], row[2]
            # Valid PK: no nulls AND all values distinct
            return total == distinct and total == non_null and total > 0
    except Exception:
        pass
    return False


def detect_foreign_keys(columns, table_name, all_table_names):
    """
    Heuristic: columns ending in KEY/ID that reference other tables.
    Returns list of (column, referenced_table_hint).
    """
    fks = []
    pk = detect_primary_key(columns, table_name)
    for col in columns:
        lower = col["name"].lower()
        if col["name"] == pk:
            continue
        if lower.endswith("key") or (lower.endswith("id") and lower != pk.lower()):
            # Try to match to another table
            clean = strip_prefix(col["name"], table_name)
            # Remove _key, _id suffix to get entity name
            entity = re.sub(r"_(key|id)$", "", clean)
            for other_table in all_table_names:
                if other_table.lower() == entity or other_table.lower().startswith(entity):
                    fks.append((col["name"], other_table))
                    break
    return fks


def detect_date_columns(columns):
    """Find columns that look like dates."""
    date_cols = []
    for col in columns:
        if col["data_type"] in ("DATE", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ"):
            date_cols.append(col["name"])
        elif any(kw in col["name"].lower() for kw in ("date", "time", "created", "updated", "at")):
            date_cols.append(col["name"])
    return date_cols


def detect_numeric_columns(columns):
    """Find numeric measure columns (excluding keys)."""
    numerics = []
    for col in columns:
        lower = col["name"].lower()
        if col["data_type"] in ("NUMBER", "FLOAT", "DECIMAL", "NUMERIC", "DOUBLE", "REAL"):
            if not (lower.endswith("key") or lower.endswith("id") or lower.endswith("_pk")):
                numerics.append(col["name"])
    return numerics


def detect_categorical_columns(columns):
    """Find string columns that are likely categorical (short varchar)."""
    categoricals = []
    for col in columns:
        if col["data_type"] in ("TEXT", "VARCHAR", "STRING", "CHAR"):
            lower = col["name"].lower()
            if any(kw in lower for kw in ("status", "type", "category", "segment",
                                           "priority", "flag", "code", "level", "tier")):
                categoricals.append(col["name"])
    return categoricals


# ─── Generators ──────────────────────────────────────────────

def generate_sources_yml(source_name, source_database, source_schema, tables, verified_pks=None):
    """Generate models/staging/_sources.yml. verified_pks maps table_name -> bool."""
    if verified_pks is None:
        verified_pks = {}
    lines = [
        "version: 2",
        "",
        "sources:",
        f"  - name: {source_name}",
        f'    description: "Auto-discovered source from {source_database}.{source_schema}"',
        f'    database: "{source_database}"',
        f'    schema: "{source_schema}"',
        "    quoting:",
        "      identifier: true",
        "    tables:",
    ]

    all_table_names = [t["name"] for t in tables]

    for table in tables:
        row_info = f" (~{table['row_count']:,} rows)" if table["row_count"] else ""
        lines.append(f"      - name: {_yaml_safe_name(table['name'])}")
        lines.append(f'        description: "Raw {table["name"].lower()} table{row_info}"')

        if table["columns"]:
            lines.append("        columns:")
            pk = detect_primary_key(table["columns"], table["name"])
            fks = detect_foreign_keys(table["columns"], table["name"], all_table_names)
            fk_cols = {fk[0] for fk in fks}

            for col in table["columns"]:
                desc = col["comment"] if col["comment"] else ""
                lines.append(f"          - name: {_yaml_safe_name(col['name'])}")
                lines.append(f'            description: "{desc}"')

                # Add tests for PK (only when verified against actual data)
                if col["name"] == pk:
                    pk_is_unique = verified_pks.get(table["name"], False)
                    if pk_is_unique:
                        lines.append("            tests:")
                        lines.append("              - unique")
                        lines.append("              - not_null")
                # Add FK relationship tests
                elif col["name"] in fk_cols:
                    ref_table = next(fk[1] for fk in fks if fk[0] == col["name"])
                    ref_pk = detect_primary_key(
                        next(t["columns"] for t in tables if t["name"] == ref_table),
                        ref_table,
                    )
                    lines.append("            tests:")
                    lines.append("              - not_null")
                    lines.append("              - relationships:")
                    lines.append(f"                  to: source('{source_name}', '{ref_table}')")
                    lines.append(f"                  field: {ref_pk}")
                # not_null for non-nullable columns
                elif not col["nullable"]:
                    lines.append("            tests:")
                    lines.append("              - not_null")

    return "\n".join(lines) + "\n"


def generate_staging_sql(source_name, table_name, columns):
    """Generate a staging model SQL file."""
    renames = []
    has_renames = False
    for col in columns:
        original = _sql_identifier(col["name"])
        clean = strip_prefix(col["name"], table_name)
        clean_sql = _sql_identifier(clean) if clean != col["name"].lower() else original
        if original != clean_sql:
            renames.append(f"        {original} as {clean_sql}")
            has_renames = True
        else:
            renames.append(f"        {original}")

    cols_str = ",\n".join(renames)

    cte_name = "renamed" if has_renames else "staged"

    return f"""with source as (
    select * from {{{{ source('{source_name}', '{table_name}') }}}}
),

{cte_name} as (
    select
{cols_str}
    from source
)

select * from {cte_name}
"""


def generate_staging_schema_yml(source_name, tables, verified_pks=None):
    """Generate models/staging/schema.yml with column descriptions and tests."""
    if verified_pks is None:
        verified_pks = {}
    lines = ["version: 2", "", "models:"]

    all_table_names = [t["name"] for t in tables]

    for table in tables:
        model_name = f"stg_{source_name}__{table['name'].lower()}"
        lines.append(f"  - name: {model_name}")
        lines.append(f'    description: "Staged {table["name"].lower()} from {source_name} — renamed columns, 1:1 with source"')
        lines.append("    columns:")

        pk = detect_primary_key(table["columns"], table["name"])
        fks = detect_foreign_keys(table["columns"], table["name"], all_table_names)
        fk_map = {fk[0]: fk[1] for fk in fks}
        categoricals = set(detect_categorical_columns(table["columns"]))

        for col in table["columns"]:
            clean_name = strip_prefix(col["name"], table["name"])
            desc = col["comment"] if col["comment"] else ""
            lines.append(f"      - name: {_yaml_safe_name(clean_name)}")
            lines.append(f'        description: "{desc}"')

            tests = []
            if col["name"] == pk:
                pk_is_unique = verified_pks.get(table["name"], False)
                if pk_is_unique:
                    tests.append("          - unique")
                    tests.append("          - not_null")
            elif col["name"] in fk_map:
                ref_table = fk_map[col["name"]]
                ref_pk_col = detect_primary_key(
                    next(t["columns"] for t in tables if t["name"] == ref_table),
                    ref_table,
                )
                ref_pk_clean = strip_prefix(ref_pk_col, ref_table)
                tests.append("          - not_null")
                tests.append("          - relationships:")
                tests.append(f"              to: ref('stg_{source_name}__{ref_table.lower()}')")
                tests.append(f"              field: {ref_pk_clean}")
            elif not col["nullable"]:
                tests.append("          - not_null")

            if tests:
                lines.append("        tests:")
                lines.extend(tests)

    return "\n".join(lines) + "\n"


def generate_overview_mart(source_name, tables):
    """
    Generate a basic 'overview' mart that picks the largest table
    and creates a simple fact model. Returns None if no suitable table found.
    """
    # Find the table with the most numeric columns (likely the "transactional" table)
    best_table = None
    best_score = 0
    for table in tables:
        numerics = detect_numeric_columns(table["columns"])
        dates = detect_date_columns(table["columns"])
        score = len(numerics) + len(dates) * 2
        if score > best_score:
            best_score = score
            best_table = table

    if not best_table or best_score == 0:
        return None, None

    stg_name = f"stg_{source_name}__{best_table['name'].lower()}"
    fct_name = f"fct_{best_table['name'].lower()}"

    pk = detect_primary_key(best_table["columns"], best_table["name"])
    pk_clean = strip_prefix(pk, best_table["name"])
    # Use the PK name as it appears in staging output
    pk_original_sql = _sql_identifier(pk)
    pk_clean_sql = _sql_identifier(pk_clean) if pk_clean != pk.lower() else pk_original_sql
    # For generate_surrogate_key, use the column name without outer quotes
    pk_for_sk = pk_clean_sql.strip('"')
    dates = detect_date_columns(best_table["columns"])
    numerics = detect_numeric_columns(best_table["columns"])

    # Determine surrogate key alias — quote if it starts with a digit
    sk_alias = _sql_identifier(f"{best_table['name'].lower()}_id")

    lines = [
        f"-- Fact table: auto-generated from {best_table['name']}",
        "with source as (",
        f"    select * from {{{{ ref('{stg_name}') }}}}",
        ")",
        "",
        "select",
        f"    {{{{ dbt_utils.generate_surrogate_key(['{pk_for_sk}']) }}}} as {sk_alias},",
    ]

    # Add all columns using the name as it appears in the staging output
    col_lines = []
    for col in best_table["columns"]:
        original = _sql_identifier(col["name"])
        clean = strip_prefix(col["name"], best_table["name"])
        # Use the clean (renamed) name if staging renamed it, otherwise the original
        clean_sql = _sql_identifier(clean) if clean != col["name"].lower() else original
        col_lines.append(f"    {clean_sql}")

    # Add date parts if we have date columns
    if dates:
        first_date = strip_prefix(dates[0], best_table["name"])
        first_date_original = _sql_identifier(dates[0])
        first_date_sql = _sql_identifier(first_date) if first_date != dates[0].lower() else first_date_original
        col_lines.append(f"    date_trunc('month', {first_date_sql}) as {first_date_sql}_month")
        col_lines.append(f"    year({first_date_sql}) as {first_date_sql}_year")

    lines.append(",\n".join(col_lines))

    lines.append("")
    lines.append("from source")
    lines.append("")

    sql = "\n".join(lines)
    return fct_name, sql


# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Discover Snowflake tables and generate dbt models")
    parser.add_argument("--source-database", help="Source database (e.g., MY_DATABASE)")
    parser.add_argument("--source-schema", help="Source schema (e.g., RAW_DATA)")
    parser.add_argument("--source-name", help="dbt source name (e.g., my_source). Used in model naming.")
    parser.add_argument("--account", help="Snowflake account identifier")
    parser.add_argument("--user", help="Snowflake username")
    parser.add_argument("--password", help="Snowflake password")
    parser.add_argument("--role", help="Snowflake role (default: DBT_ROLE)")
    parser.add_argument("--warehouse", help="Snowflake warehouse (default: DBT_AGENT_WH)")
    parser.add_argument("--skip-mart", action="store_true", help="Skip generating a starter mart model")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be generated without writing files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files without prompting")
    args = parser.parse_args()

    # Interactive prompts if args not provided
    source_database = args.source_database
    source_schema = args.source_schema
    source_name = args.source_name

    if not source_database:
        source_database = input("Source database (e.g., MY_DATABASE): ").strip()
    if not source_schema:
        source_schema = input("Source schema (e.g., RAW_DATA): ").strip()
    if not source_name:
        # Default: lowercase schema name
        default_name = source_schema.lower().replace("_", "")
        source_name = input(f"dbt source name [{default_name}]: ").strip() or default_name

    print(f"\n{'='*60}")
    print(f"Discovering: {source_database}.{source_schema}")
    print(f"Source name: {source_name}")
    print(f"{'='*60}\n")

    # Connect and discover
    print("Connecting to Snowflake...")
    conn = get_snowflake_connection(args)

    print("Discovering tables and columns...")
    tables = discover_tables(conn, source_database, source_schema)

    if not tables:
        conn.close()
        print(f"ERROR: No tables found in {source_database}.{source_schema}")
        print("Check that the database/schema exists and your role has access.")
        sys.exit(1)

    print(f"\nFound {len(tables)} table(s):")
    for t in tables:
        row_info = f" ({t['row_count']:,} rows)" if t["row_count"] else ""
        print(f"  - {t['name']}: {len(t['columns'])} columns{row_info}")

    # Verify primary key uniqueness by querying actual data
    print("\nVerifying primary keys against actual data...")
    verified_pks = {}
    for table in tables:
        pk = detect_primary_key(table["columns"], table["name"])
        if pk:
            is_unique = verify_uniqueness(conn, source_database, source_schema, table["name"], pk)
            verified_pks[table["name"]] = is_unique
            status = "unique ✓" if is_unique else "NOT unique ✗ (skipping unique test)"
            print(f"  {table['name']}.{pk}: {status}")

    conn.close()

    # Generate files
    # Compute source-specific output directories
    staging_dir = MODELS_DIR / "staging" / source_name
    marts_dir = MODELS_DIR / "marts" / source_name

    print(f"\n--- Generating dbt models ---\n")

    # 1. _sources.yml
    sources_yml = generate_sources_yml(source_name, source_database, source_schema, tables, verified_pks)
    sources_path = staging_dir / "_sources.yml"

    # 2. Staging SQL models
    staging_files = {}
    for table in tables:
        model_name = f"stg_{source_name}__{table['name'].lower()}"
        sql = generate_staging_sql(source_name, table["name"], table["columns"])
        staging_files[model_name] = sql

    # 3. schema.yml
    schema_yml = generate_staging_schema_yml(source_name, tables, verified_pks)
    schema_path = staging_dir / "schema.yml"

    # 4. Starter mart (optional)
    fct_name, fct_sql = None, None
    if not args.skip_mart:
        fct_name, fct_sql = generate_overview_mart(source_name, tables)

    if args.dry_run:
        print("DRY RUN — files would be generated:\n")
        print(f"  {sources_path.relative_to(PROJECT_ROOT)}")
        for name in staging_files:
            print(f"  models/staging/{source_name}/{name}.sql")
        print(f"  {schema_path.relative_to(PROJECT_ROOT)}")
        if fct_name:
            print(f"  models/marts/{source_name}/{fct_name}.sql")
        print(f"\nTotal: {2 + len(staging_files) + (1 if fct_name else 0)} files")
        return

    # Write files
    staging_dir.mkdir(parents=True, exist_ok=True)
    marts_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing files
    existing = []
    if sources_path.exists():
        existing.append(str(sources_path.relative_to(PROJECT_ROOT)))
    if schema_path.exists():
        existing.append(str(schema_path.relative_to(PROJECT_ROOT)))
    for name in staging_files:
        p = staging_dir / f"{name}.sql"
        if p.exists():
            existing.append(str(p.relative_to(PROJECT_ROOT)))

    if existing and not args.overwrite:
        print(f"WARNING: {len(existing)} file(s) already exist and will be overwritten:")
        for f in existing[:5]:
            print(f"  - {f}")
        if len(existing) > 5:
            print(f"  ... and {len(existing) - 5} more")
        confirm = input("\nOverwrite? (y/N): ").strip()
        if not confirm.lower().startswith("y"):
            print("Aborted.")
            sys.exit(0)

    with open(sources_path, "w") as f:
        f.write(sources_yml)
    print(f"  ✓ {sources_path.relative_to(PROJECT_ROOT)}")

    for name, sql in staging_files.items():
        path = staging_dir / f"{name}.sql"
        with open(path, "w") as f:
            f.write(sql)
        print(f"  ✓ models/staging/{source_name}/{name}.sql")

    with open(schema_path, "w") as f:
        f.write(schema_yml)
    print(f"  ✓ {schema_path.relative_to(PROJECT_ROOT)}")

    if fct_name and fct_sql:
        fct_path = marts_dir / f"{fct_name}.sql"
        with open(fct_path, "w") as f:
            f.write(fct_sql)
        print(f"  ✓ models/marts/{source_name}/{fct_name}.sql")

    # Update dbt_project.yml vars
    dbt_project_path = PROJECT_ROOT / "dbt_project.yml"
    if dbt_project_path.exists():
        content = dbt_project_path.read_text()
        # Update source_database and source_schema vars
        import re as re_mod
        content = re_mod.sub(
            r'source_database:\s*"[^"]*"',
            f'source_database: "{source_database}"',
            content,
        )
        content = re_mod.sub(
            r'source_schema:\s*"[^"]*"',
            f'source_schema: "{source_schema}"',
            content,
        )
        dbt_project_path.write_text(content)
        print(f"  ✓ Updated dbt_project.yml vars (source_database, source_schema)")

    total = 2 + len(staging_files) + (1 if fct_name else 0)
    print(f"\n{'='*60}")
    print(f"Generated {total} files from {len(tables)} tables!")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Review the generated models in models/staging/")
    print(f"  2. Run: dbt deps && dbt build")
    print(f"  3. Add intermediate/mart models as needed")
    if fct_name:
        print(f"  4. Review and customize models/marts/{fct_name}.sql")


if __name__ == "__main__":
    main()
