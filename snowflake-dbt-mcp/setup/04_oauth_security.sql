/*
=============================================================================
Step 4: OAuth Security Integration for MCP Server
=============================================================================
Snowflake Managed MCP Servers require OAuth authentication.
This script creates the security integration needed for clients
(VS Code, Claude Desktop, etc.) to authenticate via OAuth.
=============================================================================
*/

USE ROLE ACCOUNTADMIN;

-- ==========================================
-- Option A: Snowflake OAuth (for Snowflake-native clients)
-- ==========================================
CREATE OR REPLACE SECURITY INTEGRATION DBT_MCP_OAUTH_SNOWFLAKE
    TYPE = OAUTH
    OAUTH_CLIENT = CUSTOM
    OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
    OAUTH_REDIRECT_URI = 'http://localhost:8001/callback'
    OAUTH_ISSUE_REFRESH_TOKENS = TRUE
    OAUTH_REFRESH_TOKEN_VALIDITY = 86400
    ENABLED = TRUE
    COMMENT = 'OAuth integration for dbt MCP Server — Snowflake-native clients';


-- ==========================================
-- Option B: External OAuth (for VS Code / Claude Desktop / external clients)
-- Use this if you have an external identity provider (Okta, Azure AD, etc.)
-- Uncomment and configure as needed.
-- ==========================================

-- Example for Azure AD:
-- CREATE OR REPLACE SECURITY INTEGRATION DBT_MCP_OAUTH_EXTERNAL
--     TYPE = EXTERNAL_OAUTH
--     EXTERNAL_OAUTH_TYPE = AZURE
--     EXTERNAL_OAUTH_ISSUER = 'https://sts.windows.net/<tenant-id>/'
--     EXTERNAL_OAUTH_JWS_KEYS_URL = 'https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys'
--     EXTERNAL_OAUTH_AUDIENCE_LIST = ('https://<account>.snowflakecomputing.com')
--     EXTERNAL_OAUTH_TOKEN_USER_MAPPING_CLAIM = 'upn'
--     EXTERNAL_OAUTH_SNOWFLAKE_USER_MAPPING_ATTRIBUTE = 'login_name'
--     ENABLED = TRUE;

-- Example for Okta:
-- CREATE OR REPLACE SECURITY INTEGRATION DBT_MCP_OAUTH_OKTA
--     TYPE = EXTERNAL_OAUTH
--     EXTERNAL_OAUTH_TYPE = OKTA
--     EXTERNAL_OAUTH_ISSUER = 'https://<org>.okta.com/oauth2/<auth-server-id>'
--     EXTERNAL_OAUTH_JWS_KEYS_URL = 'https://<org>.okta.com/oauth2/<auth-server-id>/v1/keys'
--     EXTERNAL_OAUTH_AUDIENCE_LIST = ('https://<account>.snowflakecomputing.com')
--     EXTERNAL_OAUTH_TOKEN_USER_MAPPING_CLAIM = 'sub'
--     EXTERNAL_OAUTH_SNOWFLAKE_USER_MAPPING_ATTRIBUTE = 'login_name'
--     ENABLED = TRUE;


-- ==========================================
-- Retrieve OAuth client credentials
-- Run this AFTER creating the integration to get client ID and secret
-- ==========================================
-- CALL SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('DBT_MCP_OAUTH_SNOWFLAKE');

-- ==========================================
-- Verify
-- ==========================================
DESCRIBE SECURITY INTEGRATION DBT_MCP_OAUTH_SNOWFLAKE;
