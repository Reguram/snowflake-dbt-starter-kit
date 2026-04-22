/*
=============================================================================
Step 4: PAT (Programmatic Access Token) for MCP Server
=============================================================================
Snowflake Managed MCP Servers authenticate via Programmatic Access Tokens
(PATs). PATs are generated directly on the user — no security integration
is required.

PATs are simpler than OAuth — no redirect URIs, no token refresh logic.
Generate a token, paste it as a Bearer token in Authorization headers.
=============================================================================
*/

USE ROLE ACCOUNTADMIN;

-- ==========================================
-- 1. Generate a PAT for your user
-- Replace <YOUR_USERNAME> with your Snowflake username (e.g. REGURAM).
-- ⚠️ The token is returned ONCE — copy and store it immediately.
-- ==========================================
ALTER USER <YOUR_USERNAME> ADD PROGRAMMATIC ACCESS TOKEN dbt_mcp_access
    DAYS_TO_EXPIRY = 365
    COMMENT = 'PAT for dbt MCP Server access — VS Code, Claude Desktop, etc.';

-- Use the returned token as: Authorization: Bearer <TOKEN>


-- ==========================================
-- 2. (Optional) List PATs for a user
-- ==========================================
-- SHOW PROGRAMMATIC ACCESS TOKENS FOR USER <YOUR_USERNAME>;


-- ==========================================
-- 3. (Optional) Revoke a PAT
-- ==========================================
-- ALTER USER <YOUR_USERNAME> REMOVE PROGRAMMATIC ACCESS TOKEN dbt_mcp_access;


-- ==========================================
-- Legacy: OAuth security integration (preserved for reference)
-- Uncomment if you need OAuth instead of PAT.
-- ==========================================
-- CREATE OR REPLACE SECURITY INTEGRATION DBT_MCP_OAUTH_SNOWFLAKE
--     TYPE = OAUTH
--     OAUTH_CLIENT = CUSTOM
--     OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
--     OAUTH_REDIRECT_URI = 'http://localhost:8001/callback'
--     OAUTH_ISSUE_REFRESH_TOKENS = TRUE
--     OAUTH_REFRESH_TOKEN_VALIDITY = 86400
--     ENABLED = TRUE
--     COMMENT = 'OAuth integration for dbt MCP Server — Snowflake-native clients';
