---
name: dbt-one-stop-agent
description: >
  Master orchestrator skill for the dbt + Snowflake lifecycle. This skill does NOT execute
  work itself — it parses user intent, matches it to ONE specialized skill (or chain of skills),
  loads each target SKILL.md via read_file, and delegates execution. Covers source discovery,
  staging/intermediate/marts model generation, Snowflake Semantic Views, Cortex Agents,
  Snowflake Intelligence, code review, data quality, dbt CLI, Streamlit, Dynamic Tables,
  Iceberg, Snowpark, ML, governance, cost, security, and more.
  Use when: any dbt or Snowflake request — this skill picks the right specialist.
  Triggers: onboard, discover, build, generate, semantic view, cortex analyst, agent,
  intelligence, pipeline, end-to-end, rbac, audit, review, dashboard, streamlit, lineage,
  cost, governance, dynamic table, iceberg, snowpark, ml.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "6.0"
---

# dbt One-Stop Agent (Orchestrator)

> **Pure orchestrator.** This skill never handles work inline. It exists solely to route
> a user request to the correct specialized skill(s) and report which skills were used.
> All execution, templates, SQL, file writes, and dbt commands belong to the delegated
> skills — not to this one.

---

## CRITICAL: Delegation Protocol

This protocol is mandatory for every request. There is no inline-handling path.

1. **Parse user intent** — identify the primary task and any secondary tasks.
2. **Match to ONE row** in the Required Chains tables (Categories 1–8 below). If multiple rows match, pick the most specific. Chain extra skills only when the user's request explicitly spans them.
3. **Read each skill in the chain** — for every skill in the matched row, call `read_file` on its `SKILL.md` BEFORE producing any output. Try `.snowflake/cortex/skills/<skill>/SKILL.md` first; fall back to `.agents/skills/<skill>/SKILL.md`.
4. **Follow each skill's instructions completely** — the delegated skill is authoritative for its domain. Do not override, simplify, or paraphrase its steps.
5. **Execute chains in order** — complete each skill fully before moving to the next.
6. **Report skills used** — end every response with:
   ```
   Skills used: <skill-1>, <skill-2>, …
   ```

### What NOT to do

- ❌ Do not generate SQL, YAML, agent specs, RBAC scripts, or any other artifact from this file.
- ❌ Do not answer from general knowledge when a Required Chain row matches.
- ❌ Do not skip the `read_file` step.
- ❌ Do not maintain duplicate routing tables — Required Chains below is the single source of truth.

### No-match fallback

If no row in the Required Chains tables matches the request, respond with:

```
→ No specialized skill in the routing table matches this request.
→ Closest candidates: <skill-a>, <skill-b>
→ Please confirm which one to use, or rephrase the request.
```

Do not attempt to handle the request inline.

---

## Required Chains

Skill path resolution: `.snowflake/cortex/skills/<skill>/SKILL.md` → fallback `.agents/skills/<skill>/SKILL.md`.

### Category 1 — dbt Core Workflow

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Onboard a new source end-to-end (discover + EDA + stage + marts + semantic + agent) | `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent` |
| Profile / EDA a single Snowflake table (no model generation) | `data-profiling-eda` |
| Discover/profile a Snowflake DB or schema | `onboard-new-source` |
| Build only a staging / bronze model for a single table | `data-profiling-eda` → `onboard-bronze-layer` |
| Build only an intermediate / silver model (joins, dedup, business logic) | `onboard-silver-layer` |
| Build only a fact/dimension/mart (gold) model | `onboard-gold-layer` |
| Build any dbt model (general "create/modify a model" request, no layer specified) | `using-dbt-for-analytics-engineering` |
| Add unit tests / TDD for a model | `adding-dbt-unit-test` |
| Run `dbt build / run / test / compile / show / seed / snapshot / deps` | `running-dbt-commands` |
| Look up dbt feature / Cloud / Core docs | `fetching-dbt-docs` |
| Render dbt DAG / lineage as Mermaid | `creating-mermaid-dbt-dag` |
| Diagnose a dbt Cloud / dbt platform job failure | `troubleshooting-dbt-job-errors` |
| Audit project quality (missing tests, descriptions, SELECT *, semantic coverage) | `project-quality-audit` → `semantic-view-coverage-audit` |

### Category 2 — Semantic Layer & NL Querying

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Create a Snowflake Semantic View for ONE mart | `snowflake-semantic-view-creator` |
| Create Snowflake Semantic Views for ALL marts in a domain (batch) | `semantic-view-batch-sync` |
| Audit / find missing / orphaned / drifted semantic views | `semantic-view-coverage-audit` |
| Debug, fix, or optimize an existing semantic view; generate VQR / verified queries | `semantic-view` |
| Create a Cortex Agent (single-view or multi-view) and/or register with Snowflake Intelligence | `cortex-agent` |
| Create domain Cortex Agent + semantic views together | `semantic-view-batch-sync` → `cortex-agent` |
| Create dbt Semantic Layer / MetricFlow YAML (NOT Snowflake Semantic Views) | `building-dbt-semantic-layer` |
| Generate Cortex Analyst standalone YAML semantic model file | `cortex-analyst-semantic-model` |
| Answer a business / analytics question (KPIs, sales, "what was…", "show top…") | `answering-natural-language-questions-with-dbt` |
| Build an interactive multi-widget dashboard (DashboardSpec) | `dashboard` |

### Category 3 — Data Quality & Governance

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Snowflake DMFs / data quality monitors / quality score / SLA alerting | `data-quality` |
| Masking, row access, classification, PII, GDPR, grants, governance posture, RBAC | `data-governance` |
| Impact analysis / "what depends on" / column lineage / upstream tracing | `lineage` |

### Category 4 — Snowflake Platform

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Dynamic Tables — create, debug, target lag, UPSTREAM_FAILED, refresh issues | `dynamic-tables` |
| Iceberg tables, catalog integration, external volume, CLD, auto-refresh | `iceberg` |
| Create / edit a Snowflake workspace notebook (.ipynb) | `snowflake-notebooks` |
| Snowflake Postgres — instances, pg_lake, diagnostics | `snowflake-postgres` |
| Deploy Snowpark Python UDF / UDAF / UDTF / stored procedure | `snowpark` |
| Migrate PySpark to Snowpark Connect (SCOS) | `snowpark-connect` |
| Cortex AI functions (AI_CLASSIFY, AI_COMPLETE, AI_EXTRACT, sentiment, OCR, document parsing) | `cortex-ai-functions` |
| Snowflake integrations (API, catalog, storage, notification, security, external access) | `integrations` |
| Openflow / NiFi data integration / connector deployment | `openflow` |
| Data Clean Rooms (DCR) — collaborations, audience overlap, activation | `data-cleanrooms` |
| Internal Marketplace / organizational listings / data products | `data-products` |
| Declarative sharing / cross-account sharing / application packages (TYPE=DATA) | `declarative` |
| ML — train models, registry, feature store, HPO, distributed training, monitoring | `machine-learning` |
| Query performance — spilling, pruning, cache, clustering, SOS / QAS candidates | `workload-performance-analysis` |

### Category 5 — Infrastructure & DevOps

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Configure dbt MCP server (Claude Desktop / Cursor / VS Code / Copilot) | `configuring-dbt-mcp-server` |
| Deploy containerized app to Snowpark Container Services (SPCS) | `deploy-to-spcs` |
| `snow dbt deploy` / `EXECUTE DBT PROJECT` / dbt-as-Snowflake-object | `dbt-projects-on-snowflake` |
| DCM (Database Change Management) projects, `snow dcm`, manifest.yml DEFINE | `dcm` |
| Migrate dbt Core → dbt Fusion | `migrating-dbt-core-to-fusion` |
| Migrate dbt project across data platforms (e.g., Databricks ↔ Snowflake) | `migrating-dbt-project-across-platforms` |
| SnowConvert assessment / migration waves / SSIS / ETL workload analysis | `snowconvert-assessment` |

### Category 6 — Visualization & Apps

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Any Streamlit-in-Snowflake work (scaffold, style, theme, debug, custom components) | `developing-with-streamlit` |
| React / Next.js data app with Snowflake | `build-react-app` |

### Category 7 — Security & Cost

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Cost / credits / spending / budget / top spenders / query cost | `cost-intelligence` |
| Network policies / network rules / IP allowlists / SaaS rules | `network-security` |
| Tri-Secret Secure / CMK / BYOK / key rotation / periodic rekeying | `key-and-secret-management` |
| Trust Center scanners / security findings / CIS benchmarks | `trust-center` |
| Organization-level (org users, accounts, ORGANIZATION_USAGE, globalorgadmin) | `organization-management` |

### Category 8 — Meta / Tooling

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Create / audit / review a skill (skill authoring) | `skill_development` |
| Cortex Code CLI usage, commands, sessions, #table syntax, MCP integration | `cortex-code-guide` |

---

## Routing Flow

```
User Request
    │
    ▼
┌────────────────────────────────────┐
│  dbt-one-stop-agent (orchestrator) │
│  1. Parse intent                   │
│  2. Match to ONE row in Required   │
│     Chains (Categories 1–8)        │
│  3. read_file each skill in order  │
└──────────────┬─────────────────────┘
               │
               ▼
       ┌──────────────────┐
       │  DELEGATE        │
       │  (always)        │
       └──────┬───────────┘
              │
              ├── Read SKILL.md for skill #1 → execute its instructions
              ├── Read SKILL.md for skill #2 → execute its instructions  (if chained)
              └── …
              │
              ▼
   Report: "Skills used: skill-1, skill-2, …"
```

---

## Multi-Skill Chaining Examples

| User Request | Skills Chained (in order) |
|-------------|--------------------------|
| "Onboard MY_DB.MY_SCHEMA and create an agent" | `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent` |
| "Profile this Snowflake table / run EDA on ORDERS" | `data-profiling-eda` |
| "Create semantic views for all marts in japan_ecomm_data and an agent" | `semantic-view-batch-sync` → `cortex-agent` |
| "Add unit tests for fct_orders" | `adding-dbt-unit-test` |
| "What were total sales last quarter?" | `answering-natural-language-questions-with-dbt` |
| "Audit the project before deployment" | `project-quality-audit` → `semantic-view-coverage-audit` |
| "Create a Streamlit dashboard for sales data" | `developing-with-streamlit` |
| "Deploy fct_orders as a dynamic table" | `dynamic-tables` |
| "Classify PII columns in my marts" | `data-governance` |
| "Show me Snowflake costs by warehouse" | `cost-intelligence` |
| "Train an ML model on my mart data" | `machine-learning` |
| "Create a staging model for this table" | `data-profiling-eda` → `onboard-bronze-layer` |
| "Build an intermediate model joining orders and customers" | `onboard-silver-layer` |
| "Create a fact table for sales" | `onboard-gold-layer` |
| "Create an Iceberg table from my mart" | `iceberg` |
| "Debug why my semantic view returns wrong SQL" | `semantic-view` |
| "Migrate this project from Databricks to Snowflake" | `migrating-dbt-project-across-platforms` |
| "Set up a network policy for my Snowflake account" | `network-security` |
| "Create a Data Clean Room collaboration" | `data-cleanrooms` |
| "Visualize my dbt DAG as a Mermaid diagram" | `creating-mermaid-dbt-dag` |
| "Share my mart data with another Snowflake account" | `declarative` |
| "Create a DCM project for my database objects" | `dcm` |
| "Analyze query performance for slow queries" | `workload-performance-analysis` |
| "Set up Cortex Analyst RBAC role" | `data-governance` |

---

## Overlapping Skill Activations

This skill's `applyTo` pattern (`models/**/*.sql`, `models/**/*.yml`) overlaps with other
skills (e.g., `dbt-model-generation`, `code-review`, `data-quality`, `semantic-view-design`).
When multiple skills activate at once, this orchestrator is the entry point: pick the
correct row in Required Chains and delegate. Do not blend instructions from multiple
overlapping skills.

---

## Related Skills — Quick Reference

> All skills live in `.snowflake/cortex/skills/<skill-name>/SKILL.md` (fallback
> `.agents/skills/<skill-name>/SKILL.md`). Always `read_file` the target SKILL.md
> before delegating — see Delegation Protocol above.

| Category | Count | Skills |
|----------|-------|--------|
| dbt Core Workflow | 12 | `using-dbt-for-analytics-engineering`, `adding-dbt-unit-test`, `running-dbt-commands`, `fetching-dbt-docs`, `creating-mermaid-dbt-dag`, `data-profiling-eda`, `onboard-new-source`, `onboard-bronze-layer`, `onboard-silver-layer`, `onboard-gold-layer`, `troubleshooting-dbt-job-errors`, `project-quality-audit` |
| Semantic Layer & NL Querying | 9 | `building-dbt-semantic-layer`, `answering-natural-language-questions-with-dbt`, `snowflake-semantic-view-creator`, `semantic-view`, `semantic-view-batch-sync`, `semantic-view-coverage-audit`, `cortex-analyst-semantic-model`, `cortex-agent`, `dashboard` |
| Data Quality & Governance | 3 | `data-quality`, `data-governance`, `lineage` |
| Snowflake Platform | 14 | `dynamic-tables`, `iceberg`, `snowflake-notebooks`, `snowflake-postgres`, `snowpark`, `snowpark-connect`, `cortex-ai-functions`, `integrations`, `openflow`, `data-cleanrooms`, `data-products`, `declarative`, `machine-learning`, `workload-performance-analysis` |
| Infrastructure & DevOps | 7 | `configuring-dbt-mcp-server`, `deploy-to-spcs`, `dbt-projects-on-snowflake`, `dcm`, `migrating-dbt-core-to-fusion`, `migrating-dbt-project-across-platforms`, `snowconvert-assessment` |
| Visualization & Apps | 2 | `developing-with-streamlit`, `build-react-app` |
| Security & Cost | 5 | `cost-intelligence`, `network-security`, `key-and-secret-management`, `trust-center`, `organization-management` |
| Meta / Tooling | 2 | `skill_development`, `cortex-code-guide` |

**Total: 54 specialist skills routed by this orchestrator** (this skill is not counted, since it never routes to itself).
