"""Snowflake connection manager.

Supports two modes:
  - Local / CLI: uses snowflake-connector-python (env vars -> profiles.yml fallback)
  - Streamlit-in-Snowflake: uses snowpark get_active_session()
"""

import os
from pathlib import Path
from typing import Optional

_CONNECTION = None


def get_connection(
    account: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
):
    """Create or return a cached Snowflake connection.

    Resolution order per parameter:
      1. Explicit argument
      2. Environment variable (SNOWFLAKE_ACCOUNT, etc.)
      3. ~/.dbt/profiles.yml (first snowflake profile)
      4. Defaults (DBT_ROLE, DBT_AGENT_WH, DBT_DEV)
    """
    global _CONNECTION
    if _CONNECTION is not None:
        try:
            _CONNECTION.cursor().execute("SELECT 1")
            return _CONNECTION
        except Exception:
            _CONNECTION = None

    # Try Streamlit-in-Snowflake first
    try:
        from snowflake.snowpark.context import get_active_session

        session = get_active_session()
        _CONNECTION = session.connection
        return _CONNECTION
    except Exception:
        pass

    import snowflake.connector

    account = account or os.environ.get("SNOWFLAKE_ACCOUNT")
    user = user or os.environ.get("SNOWFLAKE_USER")
    password = password or os.environ.get("SNOWFLAKE_PASSWORD")
    role = role or os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE")
    warehouse = warehouse or os.environ.get("SNOWFLAKE_WAREHOUSE", "DBT_AGENT_WH")
    database = database or os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")

    if not all([account, user, password]):
        profiles_path = Path.home() / ".dbt" / "profiles.yml"
        if profiles_path.exists():
            import yaml

            with open(profiles_path) as f:
                profiles = yaml.safe_load(f)
            for _name, profile in profiles.items():
                if isinstance(profile, dict) and "outputs" in profile:
                    target = profile.get("target", "dev")
                    output = profile["outputs"].get(target, {})
                    if output.get("type") == "snowflake":
                        account = account or output.get("account")
                        user = user or output.get("user")
                        password = password or output.get("password")
                        role = role or output.get("role")
                        warehouse = warehouse or output.get("warehouse")
                        database = database or output.get("database")
                        break

    if not all([account, user, password]):
        raise RuntimeError(
            "Snowflake credentials not found. "
            "Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD env vars "
            "or configure ~/.dbt/profiles.yml"
        )

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
    )
    # Enable cross-region inference for Cortex
    try:
        conn.cursor().execute(
            "ALTER SESSION SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'"
        )
    except Exception:
        pass

    _CONNECTION = conn
    return _CONNECTION


def close_connection():
    """Close the cached connection if open."""
    global _CONNECTION
    if _CONNECTION is not None:
        try:
            _CONNECTION.close()
        except Exception:
            pass
        _CONNECTION = None
