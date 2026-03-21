/*
=============================================================================
Step 4: PAT Security Integration for MCP Server
=============================================================================
Snowflake Managed MCP Servers authenticate via Programmatic Access Tokens
(PATs). This script creates the security integration and generates a PAT
for connecting from clients (VS Code, Claude Desktop, etc.).

PATs are simpler than OAuth — no redirect URIs, no token refresh logic.
Each user generates a token tied to a security integration and uses it
as a Bearer token in Authorization headers.
=============================================================================
*/

USE ROLE ACCOUNTADMIN;

-- ==========================================
-- 1. Create PAT Security Integration
-- ==========================================
CREATE OR REPLACE SECURITY INTEGRATION DBT_MCP_PAT
    TYPE = API_AUTHENTICATION
    AUTH_TYPE = PROGRAMMATIC_ACCESS_TOKEN
    ENABLED = TRUE
    COMMENT = 'PAT integration for dbt MCP Server — VS Code, Claude Desktop, etc.';


-- ==========================================
-- 2. Grant the integration to the MCP role
-- ==========================================
GRANT USAGE ON INTEGRATION DBT_MCP_PAT TO ROLE DBT_MCP_ROLE;


-- ==========================================
-- 3. Generate a PAT for your user
-- Replace <YOUR_USERNAME> with your Snowflake username.
-- The token is returned ONCE — store it securely.
-- ==========================================
-- Switch to the user's role to generate the PAT
-- USE ROLE DBT_MCP_ROLE;

-- ALTER USER <YOUR_USERNAME> ADD PROGRAMMATIC_ACCESS_TOKEN
--     PURPOSE = 'dbt_mcp_access'
--     SECURITY_INTEGRATION = 'DBT_MCP_PAT'
--     COMMENT = 'PAT for dbt MCP Server access';

-- ⚠️ IMPORTANT:
-- The above command returns the PAT token in the result.
-- Copy and save it immediately — it cannot be retrieved again.
-- Use the token as: Authorization: Bearer <YOUR_PAT_TOKEN>


-- ==========================================
-- 4. (Optional) List / Revoke PATs for a user
-- ==========================================
-- List all PATs:
-- ALTER USER <YOUR_USERNAME> LIST PROGRAMMATIC_ACCESS_TOKENS;

-- Revoke a specific PAT:
-- ALTER USER <YOUR_USERNAME> REMOVE PROGRAMMATIC_ACCESS_TOKEN
--     PURPOSE = 'dbt_mcp_access'
--     SECURITY_INTEGRATION = 'DBT_MCP_PAT';


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


-- ==========================================
-- Verify
-- ==========================================
DESCRIBE SECURITY INTEGRATION DBT_MCP_PAT;
