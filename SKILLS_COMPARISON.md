# Skills Comparison: `.agents/skills/` vs `bundled_skills/`

> Generated: 2026-03-31
> Project: `snowflake-dbt-starter-kit`

---

## Summary

| Category | Count |
|---|---|
| Skills active in `.agents/skills/` | 17 |
| Skills available in `bundled_skills/` | 33 |
| Bundled skills already in `.agents/skills/` (by name) | 0 |
| Bundled skills with functional overlap to active skills | 3 |
| **New bundled skills (missing from `.agents/skills/`)** | **33** |

---

## Active Skills in `.agents/skills/`

### Custom / Project-Specific Skills (6)

| Skill Name | Purpose | User-Invocable |
|---|---|---|
| `dbt-one-stop-agent` | All-in-one dbt task orchestrator — runs, tests, builds, and documents dbt models | Yes |
| `project-quality-audit` | Audits the dbt project for code quality, documentation coverage, and best practices | Yes |
| `semantic-view-batch-sync` | Batch-syncs semantic views across multiple dbt models at once | Yes |
| `semantic-view-coverage-audit` | Audits which dbt models have / lack semantic view coverage | Yes |
| `snowflake-openflow-pipeline` | Creates NiFi-based Openflow data pipelines for Snowflake ingestion | Yes |
| `snowflake-semantic-view-creator` | Creates individual Snowflake Semantic Views from dbt model definitions | Yes |

### Upstream dbt Skills (11) — from `dbt-labs/dbt-agent-skills` (locked via `skills-lock.json`)

| Skill Name | Purpose | User-Invocable |
|---|---|---|
| `adding-dbt-unit-test` | Scaffolds and writes dbt unit tests | No |
| `answering-natural-language-questions-with-dbt` | Answers analytical questions by querying dbt semantic layer | No |
| `building-dbt-semantic-layer` | Guides building a complete dbt Semantic Layer | No |
| `configuring-dbt-mcp-server` | Configures the dbt MCP server for Claude integration | No |
| `creating-mermaid-dbt-dag` | Creates Mermaid diagrams of dbt DAGs | No |
| `fetching-dbt-docs` | Fetches and surfaces dbt documentation | No |
| `migrating-dbt-core-to-fusion` | Migrates dbt Core projects to dbt Fusion | No |
| `migrating-dbt-project-across-platforms` | Migrates dbt projects between data platforms | No |
| `running-dbt-commands` | Executes dbt CLI commands (run, test, build, compile) | No |
| `troubleshooting-dbt-job-errors` | Diagnoses and fixes failing dbt jobs | No |
| `using-dbt-for-analytics-engineering` | General analytics engineering guidance using dbt | No |

---

## All 33 Skills in `bundled_skills/` — Detailed Description

### Skills MISSING from `.agents/skills/` (all 33)

> None of the bundled skills currently exist in `.agents/skills/`. Three have functional overlap with custom project skills (noted below).

---

#### 1. `build-react-app` → `bundled_skills/build-react-app/`
**Purpose:** Builds full-stack React/Next.js applications connected to Snowflake data.
**Key capabilities:** TypeScript connection code for SSO (local dev) and OAuth token (SPCS production) auth. Routes to `build-with-nextjs` and `deploy-to-spcs` sub-skills.
**Overlap with active skills:** None.

---

#### 2. `cortex-agent` → `bundled_skills/cortex-agent/`
**Purpose:** Master router for all Snowflake Cortex Agent operations.
**Key capabilities:** 12 intent routes — CREATE, EDIT, ADHOC_TESTING, EVALUATE, DATASET, DEBUG_SINGLE_QUERY, DEBUG_EVAL, OPTIMIZE, DELETE, ACCESS, LIST, DOWNLOAD. Includes 15+ sub-skills: `create-cortex-agent`, `edit-cortex-agent`, `evaluate-cortex-agent`, `debug-single-query-for-cortex-agent`, `optimize-cortex-agent`, `optimize-cortex-search-service`, `agent-observability-report`, `agent-system-of-record`, `dataset-curation`, `investigate-cortex-agent-evals`, `delete-cortex-agent`, `list-cortex-agents`, `adhoc-testing-for-cortex-agent`, `best-practices`.
**Overlap with active skills:** None.

---

#### 3. `cortex-ai-functions` → `bundled_skills/cortex-ai-functions/`
**Purpose:** Routes to 12 Snowflake Cortex AI function sub-skills.
**Key capabilities:** AI_CLASSIFY, AI_FILTER, AI_EXTRACT, AI_AGG, AI_SENTIMENT, AI_TRANSLATE, AI_SUMMARIZE, AI_COMPLETE, PARSE_DOCUMENT, EMBED_TEXT, COMPLETE, document intelligence workflows.
**Overlap with active skills:** None.

---

#### 4. `cortex-code-guide` → `bundled_skills/cortex-code-guide/`
**Purpose:** Complete Cortex Code (CoCo) CLI reference and guidance.
**Key capabilities:** Routes to reference files for commands, shortcuts, configuration, skills, MCP, hooks, agents, Snowflake tools, and sessions.
**Overlap with active skills:** None.

---

#### 5. `cost-intelligence` → `bundled_skills/cost-intelligence/`
**Purpose:** Snowflake cost and billing query routing.
**Key capabilities:** Uses `SNOWFLAKE.ACCOUNT_USAGE` views. Routes to SQL query reference files per cost category. Includes budget management sub-skill.
**Overlap with active skills:** None.

---

#### 6. `dashboard` → `bundled_skills/dashboard/`
**Purpose:** Creates interactive dashboards using DashboardSpec JSON.
**Key capabilities:** Chart, table, markdown, and scorecard widgets on a 12-column grid layout using the DashboardSpec JSON format.
**Overlap with active skills:** None.

---

#### 7. `data-cleanrooms` → `bundled_skills/data-cleanrooms/`
**Purpose:** Snowflake Data Clean Rooms collaboration workflows.
**Key capabilities:** Routes browse/review-join/register/run/create operations using `SAMOOHA_BY_SNOWFLAKE_LOCAL_DB`. Supports multi-party data collaboration with privacy controls.
**Overlap with active skills:** None.

---

#### 8. `data-governance` → `bundled_skills/data-governance/`
**Purpose:** Complete Snowflake data governance suite.
**Key capabilities:** 5 sub-skills — `horizon-catalog`, `data-policy`, `sensitive-data-classification`, `governance-maturity-score`, `observability-maturity-score`.
**Overlap with active skills:** None.

---

#### 9. `internal-marketplace-org-listing` (`data-products`) → `bundled_skills/data-products/`
**Purpose:** Creates and manages internal marketplace organizational listings.
**Key capabilities:** Uses `CREATE ORGANIZATION LISTING` with YAML manifest; handles cross-region auto-fulfillment for data product sharing.
**Overlap with active skills:** None.

---

#### 10. `data-quality` → `bundled_skills/data-quality/`
**Purpose:** DMF-based data quality monitoring and management.
**Key capabilities:** 14 workflow routes. Uses `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()` UDTF (not ACCOUNT_USAGE view). Covers quality checks, anomaly detection, and alerting.
**Overlap with active skills:** None.

---

#### 11. `dbt-projects-on-snowflake` → `bundled_skills/dbt-projects-on-snowflake/`
**Purpose:** Manages dbt as native Snowflake objects via the `snow dbt` CLI.
**Key capabilities:** Routes to deploy/execute/manage/schedule/monitor/migrate sub-skills. **NOTE:** This is for the `snow dbt` workflow only — not standard local dbt commands (which are covered by `.agents/skills/running-dbt-commands`).
**Overlap with active skills:** Partial — `.agents/skills/` handles standard dbt CLI; this skill handles Snowflake-native `snow dbt` objects.

---

#### 12. `dcm` → `bundled_skills/dcm/`
**Purpose:** Database Change Management using the `snow dcm` CLI.
**Key capabilities:** Requires `snow` CLI v3.16+. Mandatory sequential initialization gates (version check → load syntax → gather info). Workflows: CREATE, MODIFY_LOCAL, DOWNLOAD_AND_MODIFY, ANALYZE, IMPORT_EXISTING, ROLE_GRANT_GUIDELINES, DEPLOY. Uses `DEFINE` keyword instead of `CREATE` in manifests. 4 sub-skills: `create-project`, `modify-project`, `deploy-project`, `roles-and-grants`.
**Overlap with active skills:** None.

---

#### 13. `declarative-sharing` (`declarative`) → `bundled_skills/declarative/`
**Purpose:** Cross-account data sharing with Application Packages TYPE=DATA.
**Key capabilities:** Versioned sharing via `manifest.yml`. Uses `CREATE APPLICATION PACKAGE`. Requires separate schemas for shared-by-copy objects (agents, UDFs) vs shared-by-reference objects (tables, views, semantic views).
**Overlap with active skills:** None.

---

#### 14. `deploy-to-spcs` → `bundled_skills/deploy-to-spcs/`
**Purpose:** Deploys containerized applications to Snowpark Container Services.
**Key capabilities:** 6-step workflow: Verify App → Prerequisites → `service-spec.yaml` → Build/Push → Deploy → Grant Access. Always uses `ALTER SERVICE` to update (never drop/recreate — would change the service URL).
**Overlap with active skills:** None.

---

#### 15. `developing-with-streamlit` → `bundled_skills/developing-with-streamlit/`
**Purpose:** Full Streamlit in Snowflake development lifecycle.
**Key capabilities:** Routes to 18 reference files: performance, dashboards, design, selection-widgets, theme, layouts, data-display, multipage-apps, session-state, markdown, chat-ui, snowflake-connection, snowflake-deployment, custom-components-v2, third-party-components, code-organization, environment-setup, CLI. Includes 8 dashboard templates and 8 themes with bundled fonts in `assets/`.
**Overlap with active skills:** None.

---

#### 16. `dynamic-tables` → `bundled_skills/dynamic-tables/`
**Purpose:** Snowflake Dynamic Table management with session diary tracking.
**Key capabilities:** Routes to create/monitor/troubleshoot/optimize/dt-alerting/permissions/task-to-dt sub-skills. Uses a session diary system to track diagnostic progress and avoid repeated steps.
**Overlap with active skills:** None.

---

#### 17. `iceberg` → `bundled_skills/iceberg/`
**Purpose:** All Snowflake Iceberg table operations.
**Key capabilities:** 5 routing paths: CATALOG_INTEGRATION (Glue, Unity Catalog, OpenCatalog), CATALOG_LINKED_DATABASE, EXTERNAL_VOLUME, AUTO_REFRESH, SNOWFLAKE_INTELLIGENCE. Typical journey: Catalog Integration → External Volume → Catalog Linked Database → Snowflake Intelligence.
**Overlap with active skills:** None.

---

#### 18. `integrations` → `bundled_skills/integrations/`
**Purpose:** All Snowflake integration CREATE/ALTER/DROP operations.
**Key capabilities:** 24 sub-skills organized by type — General (CREATE/ALTER/SHOW/DESCRIBE/DROP), API integrations, Catalog integrations, External Network Access, Notification integrations, Security integrations, Storage integrations.
**Overlap with active skills:** None.

---

#### 19. `key-and-secret-management` → `bundled_skills/key-and-secret-management/`
**Purpose:** Tri-Secret Secure (BYOK/CMK) and data rekeying operations.
**Key capabilities:** Routes TSS/CMK/BYOK operations to `tri-secret-secure/SKILL.md`. Handles periodic data rekeying via official Snowflake docs (separate account parameter).
**Overlap with active skills:** None.

---

#### 20. `lineage` → `bundled_skills/lineage/`
**Purpose:** Data lineage and impact analysis using `SNOWFLAKE.CORE.GET_LINEAGE()`.
**Key capabilities:** 4 workflows — Impact Analysis (downstream), Root Cause Analysis (upstream), Data Discovery (provenance), Column-Level Lineage. ACCOUNT_USAGE views as fallback. Configurable trust scoring via `config/schema-patterns.yaml`.
**Overlap with active skills:** None.

---

#### 21. `machine-learning` → `bundled_skills/machine-learning/`
**Purpose:** All Snowflake data science and ML workflows.
**Key capabilities:** 13 sub-skills — ml-development, model-registry, experiment-tracking, spcs-inference, batch-inference-jobs, ml-jobs, ml-pipeline-orchestration, model-monitor, distributed-training (XGBEstimator/LightGBMEstimator/PyTorchDistributor/MMT/DPF/Tuner), partitioned-inference, feature-store, inference-logs, debug-inference. Always loads environment guide (Snowsight vs CLI) before any sub-skill.
**Overlap with active skills:** None.

---

#### 22. `network-security` → `bundled_skills/network-security/`
**Purpose:** Snowflake network policies and security rules management.
**Key capabilities:** Manages network policies/rules with hybrid policy patterns using `SNOWFLAKE.NETWORK_SECURITY` SaaS rules. Routes to `network-policy-advisor/SKILL.md` for advisory workflows.
**Overlap with active skills:** None.

---

#### 23. `openflow` → `bundled_skills/openflow/`
**Purpose:** NiFi-based Openflow data integration pipelines.
**Key capabilities:** Primary/Secondary/Advanced routing tiers. Requires `nipyapi[cli]>=1.5.0`. **NOTE:** Distinct from Snowflake Tasks/Streams — this is the external NiFi-based Openflow integration.
**Overlap with active skills:** Partial — `.agents/skills/snowflake-openflow-pipeline` is a custom project-specific skill; this bundled skill is a broader, general-purpose Openflow skill.

---

#### 24. `organization-management` → `bundled_skills/organization-management/`
**Purpose:** Snowflake organization and account management.
**Key capabilities:** 7 intent routes — ACCOUNT_INSIGHTS, ORG_USERS_CREATE, ORG_USERS_IMPORT, ORG_USERS_TROUBLESHOOT, ORG_HUB_INSIGHTS, ORG_USAGE_VIEWS, GLOBAL_ORG_ADMIN. Uses ORGANIZATION_USAGE views. Sub-skills: `accounts`, `organization-users/create`, `organization-users/import`, `organization-users/troubleshoot`, `org-hub`, `org-usage-view`, `globalorgadmin`.
**Overlap with active skills:** None.

---

#### 25. `semantic-view` → `bundled_skills/semantic-view/`
**Purpose:** Full Snowflake Semantic View lifecycle management.
**Key capabilities:** Mandatory initialization (load concepts + setup), then routes to creation/VQR suggestions/audit/debug/optimization/upload sub-skills. Uses `semantic_view_get.py` and `semantic_view_set.py` scripts.
**Overlap with active skills:** Partial — three custom skills (`semantic-view-batch-sync`, `semantic-view-coverage-audit`, `snowflake-semantic-view-creator`) cover specific semantic view workflows; this bundled skill is a comprehensive all-in-one router.

---

#### 26. `skill-development` (`skill_development`) → `bundled_skills/skill_development/`
**Purpose:** Skill creation, auditing, and session summarization for Claude Code skills.
**Key capabilities:** 3 sub-skills — `create-from-scratch` (CREATE intent), `audit-skill` (AUDIT intent), `summarize-session` (SUMMARIZE intent). References `SKILL_BEST_PRACTICES.md` (1180-line guide).
**Overlap with active skills:** None.

---

#### 27. `snowconvert-assessment` → `bundled_skills/snowconvert-assessment/`
**Purpose:** Migration workload analysis using SnowConvert CSV reports.
**Key capabilities:** Analyzes SnowConvert output. Routes to: waves-generator, object_exclusion_detection, analyzing-sql-dynamic-patterns, etl-assessment. Always uses `generate_multi_report.py` for HTML reports. Mandatory welcome message + confirmation stopping points.
**Overlap with active skills:** None.

---

#### 28. `snowflake-notebooks` → `bundled_skills/snowflake-notebooks/`
**Purpose:** Creates Snowflake Workspace notebooks (`.ipynb` files).
**Key capabilities:** Generates `nbformat 4.5+` notebooks. Default: SQL cells with cell referencing (no connection code). Dual-mode only when explicitly requested. Forbidden libraries: `streamlit`, `ipywidgets`. Offers upload via `cortex artifact create notebook` and deep-link URL generation after creation.
**Overlap with active skills:** None.

---

#### 29. `snowflake-postgres` → `bundled_skills/snowflake-postgres/`
**Purpose:** Snowflake Postgres instance management.
**Key capabilities:** Routes to MANAGE (create/show/suspend/resume/reset), CONNECT (network policy/IP), DIAGNOSE (health via `pg_doctor.py`), PG_LAKE (Iceberg/S3 integration). Key scripts: `pg_connect.py`, `pg_doctor.py`, `pg_lake_setup.py`, `pg_lake_storage.py`. Never displays credentials; always uses 60s+ timeout.
**Overlap with active skills:** None.

---

#### 30. `snowpark-python` (`snowpark`) → `bundled_skills/snowpark/`
**Purpose:** Snowpark Python UDF, stored procedure, and deployment workflows.
**Key capabilities:** Writes, runs, and deploys Snowpark Python code. Uses `uv` for dependency management. Routes to `references/snowpark-deployment.md` for deployment details.
**Overlap with active skills:** None.

---

#### 31. `snowpark-connect` → `bundled_skills/snowpark-connect/`
**Purpose:** PySpark to Snowpark Connect migration and validation.
**Key capabilities:** 2 sub-skills — `migrate-pyspark-to-snowpark-connect` (convert/migrate intent) and `validate-pyspark-to-snowpark-connect` (validate/verify intent).
**Overlap with active skills:** None.

---

#### 32. `trust-center` → `bundled_skills/trust-center/`
**Purpose:** Snowflake Trust Center security findings and scanner management.
**Key capabilities:** 4 intent routes — ANALYZE_FINDINGS (`findings-analysis/SKILL.md`), ANALYZE_SCANNERS (`scanner-analysis/SKILL.md`), MANAGE_SCANNERS (`api-management/SKILL.md`), REMEDIATE_FINDING (`finding-remediation/SKILL.md`).
**Overlap with active skills:** None.

---

#### 33. `workload-performance-analysis` → `bundled_skills/workload-performance-analysis/`
**Purpose:** Snowflake SQL workload and performance analysis.
**Key capabilities:** Entity detection (QUERY/WAREHOUSE/TABLE/SPILLING/PRUNING/QAS/CACHE/ACCOUNT). 3-phase routing (summary/detection/recommendation). Uses ACCOUNT_USAGE views.
**Overlap with active skills:** None.

---

## Overlap Analysis

Three bundled skills have functional overlap with existing custom project skills:

| Bundled Skill | Overlapping Active Skill(s) | Nature of Overlap |
|---|---|---|
| `openflow` | `snowflake-openflow-pipeline` | Active skill is project-specific; bundled is a general-purpose Openflow router |
| `semantic-view` | `semantic-view-batch-sync`, `semantic-view-coverage-audit`, `snowflake-semantic-view-creator` | Active skills are task-specific; bundled is a comprehensive lifecycle router |
| `dbt-projects-on-snowflake` | `running-dbt-commands` (dbt-labs) | Active skill runs local dbt CLI; bundled handles Snowflake-native `snow dbt` objects |

---

## Installation Status

All 33 bundled skills have been copied into `.agents/skills/` and are now available alongside the 17 existing skills (total: **50 active skills**).

### Full Active Skills List (Post-Installation)

| # | Skill Name | Source |
|---|---|---|
| 1 | `adding-dbt-unit-test` | dbt-labs upstream |
| 2 | `answering-natural-language-questions-with-dbt` | dbt-labs upstream |
| 3 | `build-react-app` | bundled_skills ✨ |
| 4 | `building-dbt-semantic-layer` | dbt-labs upstream |
| 5 | `configuring-dbt-mcp-server` | dbt-labs upstream |
| 6 | `cortex-agent` | bundled_skills ✨ |
| 7 | `cortex-ai-functions` | bundled_skills ✨ |
| 8 | `cortex-code-guide` | bundled_skills ✨ |
| 9 | `cost-intelligence` | bundled_skills ✨ |
| 10 | `creating-mermaid-dbt-dag` | dbt-labs upstream |
| 11 | `dashboard` | bundled_skills ✨ |
| 12 | `data-cleanrooms` | bundled_skills ✨ |
| 13 | `data-governance` | bundled_skills ✨ |
| 14 | `data-products` (internal-marketplace-org-listing) | bundled_skills ✨ |
| 15 | `data-quality` | bundled_skills ✨ |
| 16 | `dbt-one-stop-agent` | project custom |
| 17 | `dbt-projects-on-snowflake` | bundled_skills ✨ |
| 18 | `dcm` | bundled_skills ✨ |
| 19 | `declarative` (declarative-sharing) | bundled_skills ✨ |
| 20 | `deploy-to-spcs` | bundled_skills ✨ |
| 21 | `developing-with-streamlit` | bundled_skills ✨ |
| 22 | `dynamic-tables` | bundled_skills ✨ |
| 23 | `fetching-dbt-docs` | dbt-labs upstream |
| 24 | `iceberg` | bundled_skills ✨ |
| 25 | `integrations` | bundled_skills ✨ |
| 26 | `key-and-secret-management` | bundled_skills ✨ |
| 27 | `lineage` | bundled_skills ✨ |
| 28 | `machine-learning` | bundled_skills ✨ |
| 29 | `migrating-dbt-core-to-fusion` | dbt-labs upstream |
| 30 | `migrating-dbt-project-across-platforms` | dbt-labs upstream |
| 31 | `network-security` | bundled_skills ✨ |
| 32 | `openflow` | bundled_skills ✨ |
| 33 | `organization-management` | bundled_skills ✨ |
| 34 | `project-quality-audit` | project custom |
| 35 | `running-dbt-commands` | dbt-labs upstream |
| 36 | `semantic-view` | bundled_skills ✨ |
| 37 | `semantic-view-batch-sync` | project custom |
| 38 | `semantic-view-coverage-audit` | project custom |
| 39 | `skill_development` | bundled_skills ✨ |
| 40 | `snowconvert-assessment` | bundled_skills ✨ |
| 41 | `snowflake-notebooks` | bundled_skills ✨ |
| 42 | `snowflake-openflow-pipeline` | project custom |
| 43 | `snowflake-postgres` | bundled_skills ✨ |
| 44 | `snowflake-semantic-view-creator` | project custom |
| 45 | `snowpark` (snowpark-python) | bundled_skills ✨ |
| 46 | `snowpark-connect` | bundled_skills ✨ |
| 47 | `troubleshooting-dbt-job-errors` | dbt-labs upstream |
| 48 | `trust-center` | bundled_skills ✨ |
| 49 | `using-dbt-for-analytics-engineering` | dbt-labs upstream |
| 50 | `workload-performance-analysis` | bundled_skills ✨ |
