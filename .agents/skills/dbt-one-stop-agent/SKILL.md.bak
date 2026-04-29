---
name: dbt-one-stop-agent
description: >
  Unified, context-aware dbt orchestrator that routes to 53 specialized skills across the entire
  Snowflake + dbt lifecycle: source discovery, staging/intermediate/marts model generation,
  Snowflake Semantic View creation, Snowflake Agent deployment, Snowflake Intelligence
  registration, code review, data quality checks, medallion architecture advising, dbt CLI
  operations, Streamlit app scaffolding, Dynamic Tables, Iceberg, Snowpark, ML, data governance,
  cost analysis, security, and more.
  Always reads existing project state before generating code — produces models that fit the
  existing project rather than generic boilerplate. Delegates to specialized skills when deeper
  expertise is needed.
  Use when: building any dbt model, discovering new data sources, creating semantic views,
  deploying agents, enabling Snowflake Intelligence, reviewing code, checking data quality,
  or asking questions about the project — or ANY Snowflake platform task.
  Triggers: onboard, discover, build, generate, semantic view, cortex analyst, agent, intelligence,
  pipeline, end-to-end, rbac, cortex role, semantic views for domain.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "5.2"
---

# dbt One-Stop Agent

> **Unified orchestrator** that combines 53 specialized skills for the entire dbt + Snowflake
> lifecycle. Handles tasks directly when it can, delegates to specialized skills when deeper
> expertise is needed. One entry point for everything.

---

## CRITICAL: Delegation Protocol

> **This section is mandatory.** Follow it exactly whenever routing to another skill.

When delegating to another skill, you **MUST**:

1. **Read the skill file first** — Call `read_file` on `.snowflake/cortex/skills/<skill-name>/SKILL.md` BEFORE generating any output for that task. Never guess what a skill does from the routing table alone.
2. **Follow that skill's instructions completely** — The delegated skill is authoritative for its domain. Do not override or simplify its steps.
3. **Return here only for chaining** — If the delegated skill completes and another skill is needed for the next step (e.g., after `onboard-bronze-layer`, chain to `onboard-gold-layer`), return to this routing table to identify the next skill.
4. **Never skip delegation** — If the routing table says "Delegate", you MUST load the skill. Do not attempt to handle it inline using general knowledge.
5. **Report which skill was used** — In your response, briefly note which skill(s) you delegated to so the user has traceability.

### Delegation command pattern
```
→ Matched skill: <skill-name>
→ Action: read_file(".snowflake/cortex/skills/<skill-name>/SKILL.md")
→ Follow its instructions, then return here if chaining is needed
```

---

## Required Chains (MUST delegate — never inline)

> **This section overrides any "Handle directly" hint in the routing table.** When a user
> request matches one of the intent patterns below, you MUST `read_file` every listed skill
> in order BEFORE producing any output, then execute the chain. This is enforced for ALL
> triggers — there is no implicit "handle directly" path.
>
> **Skill path resolution:** Try `.snowflake/cortex/skills/<skill>/SKILL.md` first. If not
> found, fall back to `.agents/skills/<skill>/SKILL.md`.
>
> **Reporting:** At the end of every response, include a `Skills used:` line listing each
> skill that was actually loaded (via `read_file`) for traceability.

### How to use this table

1. Match the user's request to ONE row using the **Intent / Trigger** column. If multiple match, pick the most specific row; chain extra skills only when the user's request explicitly spans them.
2. Execute the chain in order. For each skill, call `read_file` first, then apply its instructions.
3. If the chain has multiple skills, complete each fully before moving to the next.
4. Report every skill loaded.

### Category 1 — dbt Core Workflow

| Intent / Trigger | Required Chain (in order) |
|---|---|
| Onboard a new source end-to-end (discover + stage + marts + semantic + agent) | `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent` |
| Discover/profile a Snowflake DB or schema | `onboard-new-source` |
| Build only a staging / bronze model for a single table | `onboard-bronze-layer` |
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
| Masking, row access, classification, PII, GDPR, grants, governance posture | `data-governance` |
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
| Scaffold a basic Streamlit-in-Snowflake app from a mart | `developing-with-streamlit` |
| Style / theme / beautify / debug / build custom components for Streamlit | `developing-with-streamlit` |
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

### Cross-cutting fallback rule

If a request matches **none** of the rows above, then — and only then — the orchestrator may handle it inline using the inline templates in this file (semantic view templates in Step 5, agent templates in Phase 2, etc.). In that case, prefix the response with:

```
→ No specialized skill matched. Handling inline using dbt-one-stop-agent templates.
```

### Skill loading checklist (run before producing output)

1. Parse user intent and pick ONE row from the Required Chains tables.
2. For each skill in the chain: `read_file(".snowflake/cortex/skills/<skill>/SKILL.md")` (fallback to `.agents/skills/<skill>/SKILL.md`).
3. Execute that skill's instructions completely before moving to the next.
4. After the final skill, return here only to chain or summarize.
5. End the response with `Skills used: <skill-1>, <skill-2>, …`.

---

## Execution Modes: MCP Server vs Copilot Agent

> **Important:** This skill operates in two distinct modes. Know which mode you are in.

| Mode | How to detect | Tool availability | File creation |
|------|--------------|-------------------|---------------|
| **MCP Server mode** | Running via `dbt_agent.py --mcp` or MCP tools are available (e.g., `generate_model`, `discover_source`, `run_dbt`) | All tools in the "Available Tools" table below work | Use MCP tools directly |
| **Copilot Agent mode** | Running in VS Code Copilot Chat — NO MCP tools available | Only `read_file`, `create_file`, `replace_string_in_file`, terminal commands | Create files manually using templates in this skill. Run dbt via terminal commands |

**Rule:** When you reference a tool like `generate_domain_semantic_views()` or `run_dbt()`, verify the tool is actually available. If not, fall back to the inline step-by-step instructions (e.g., Step 5 for semantic views) and terminal commands (e.g., `dbt build --select tag:semantic`).

---

## What This Skill Does

| Capability | Description |
|-----------|-------------|
| **Source Discovery** | Connects to any Snowflake database/schema, discovers tables, auto-generates staging models with proper naming, tests, and documentation |
| **Model Generation** | Creates intermediate (silver) and marts (gold) models with context-aware SQL — reads existing models before generating |
| **Snowflake Semantic Views** | Creates Snowflake-native Semantic Views via `dbt_semantic_view` package with auto-classified dimensions/metrics, verified queries, and AI_SQL_GENERATION instructions for Cortex Analyst NL querying |
| **Domain Semantic Views** | Batch-generate semantic views for ALL marts in a domain with auto-classified dims/metrics and verified queries |
| **Cortex Agent Creation** | Generate Cortex Agent SQL bundling all semantic views for a domain as `cortex_analyst_text_to_sql` tools |
| **End-to-End Pipeline** | Full pipeline: Discover → Stage → Marts → Validate → Semantic Views → Agent — one command |
| **Snowflake Agent Deployment** | Creates Cortex Agents (`CREATE AGENT`) wired to Snowflake Semantic Views for text-to-SQL |
| **Snowflake Intelligence** | Registers agents with Snowflake Intelligence for org-wide natural language querying in the Snowsight UI |
| **RBAC / Security** | Least-privilege `CORTEX_ANALYST_ROLE` for Copilot/Analyst — never ACCOUNTADMIN |
| **Code Review** | Static analysis against project conventions: naming, `ref()` usage, hard-coded schemas, missing tests |
| **Data Quality** | Runs dbt tests, profiles columns for null rates and cardinality, validates data pipelines |
| **Medallion Advising** | Suggests silver/gold models based on existing bronze data using Cortex LLM |
| **dbt Operations** | Run, build, test, compile, seed via dbt CLI |
| **Streamlit Apps** | Generate Streamlit-in-Snowflake dashboards from mart models |
| **Skill Routing** | Delegates to 53 specialized skills when tasks require deeper Snowflake platform expertise |

---

## Skill Routing Table (53 Skills)

> This agent acts as the **orchestrator**. For tasks it handles directly (model generation,
> source discovery, semantic views, code review), it executes inline. For everything else,
> it delegates to the appropriate specialized skill below.

### Delegation Rules

1. **Always delegate first** — every user request must be matched to a row in the **Required Chains** section above. Read the listed skill(s) via `read_file` BEFORE producing output.
2. **Inline handling is the exception** — only allowed when no Required Chain row matches (see *Cross-cutting fallback rule*). The orchestrator must announce this explicitly in the response.
3. **Chain when intent spans domains** — e.g., onboard a source AND create an agent → `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent`.
4. **Always report** — end every response with `Skills used: …` listing each skill loaded.

> **Note on overlapping activations:** This skill's `applyTo` pattern (`models/**/*.sql`, `models/**/*.yml`) overlaps with other skills like `dbt-model-generation`, `code-review`, `data-quality`, and `semantic-view-design`. When multiple skills activate simultaneously, use **this skill as the router** — it will delegate to the specialized skill when needed. Do not follow conflicting instructions from multiple skills; let this orchestrator decide which skill applies.

### Category 1: dbt Core Workflow

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `using-dbt-for-analytics-engineering` | model, SQL, ref, source, transform, pipeline | **Delegate** — see Required Chains. Read this skill before generating any dbt model |
| `adding-dbt-unit-test` | unit test, TDD, mock, test model logic | **Delegate** — specialized YAML format and mocking patterns |
| `running-dbt-commands` | dbt build, dbt run, dbt test, dbt compile, dbt show | **Delegate** — read this skill before invoking `run_dbt` or shelling out to dbt CLI |
| `fetching-dbt-docs` | dbt docs, documentation, dbt features, dbt Cloud | **Delegate** — retrieves docs.getdbt.com pages in LLM-friendly format |
| `creating-mermaid-dbt-dag` | DAG, lineage diagram, mermaid, visualize dependencies | **Delegate** — generates Mermaid flowcharts from manifest or code |
| `onboard-new-source` | onboard, new source, discover, add source, build pipeline | **Delegate** — always read this skill for any source onboarding (chains to bronze/silver/gold) |
| `onboard-bronze-layer` | bronze, staging model, new source table, profile table, stg_ model | **Delegate** — single-layer staging onboarding with column profiling and pattern inference |
| `onboard-silver-layer` | silver, intermediate model, int_ model, join tables, business logic, enrich | **Delegate** — intermediate model generation with joins, dedup, and business logic. Advises skipping if not needed |
| `onboard-gold-layer` | gold, marts, fact table, dimension table, fct_, dim_, surrogate key | **Delegate** — mart model generation with surrogate keys, clustering, and comprehensive tests |
| `troubleshooting-dbt-job-errors` | job failed, dbt Cloud error, intermittent failure, logs | **Delegate** — specialized in dbt Cloud log analysis and Admin API |
| `project-quality-audit` | audit, quality check, validate, pre-deploy, missing tests | **Delegate** — read this skill, then chain `semantic-view-coverage-audit` |

### Category 2: Semantic Layer & NL Querying

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `building-dbt-semantic-layer` | semantic model, metric, MetricFlow, measure, dimension, `dbt sl` | **Delegate** — MetricFlow YAML is distinct from Snowflake Semantic Views |
| `answering-natural-language-questions-with-dbt` | "What were total sales?", KPI, analytics question, NL query | **Delegate** — translates business questions to SQL via Semantic Layer |
| `snowflake-semantic-view-creator` | semantic view, CREATE SEMANTIC VIEW, `dbt_semantic_view` package | **Delegate** — read this skill before creating any `sem_*.sql` / `sem_*.yml` |
| `semantic-view` | create/debug/fix/optimize semantic view, VQR, verified queries | **Delegate** — entry point for ALL semantic view operations including debugging |
| `semantic-view-batch-sync` | batch semantic views, sync, enable Cortex Analyst for all marts | **Delegate** — read this skill for any multi-mart / domain-level semantic view work |
| `semantic-view-coverage-audit` | audit semantic views, coverage, missing views, orphaned, drift | **Delegate** — read this skill for any coverage/drift audit |
| `cortex-analyst-semantic-model` | Cortex Analyst YAML, semantic model YAML, `CORTEX_ANALYST_MESSAGE` | **Delegate** — only if user explicitly requests standalone YAML files. Default path is Snowflake Semantic Views |
| `cortex-agent` | create agent, debug agent, list agents, Snowflake Intelligence, SI | **Delegate** — read this skill for ALL agent operations (create, register, debug, evaluate) |
| `dashboard` | dashboard, KPI report, executive summary, widgets, charts | **Delegate** — specialized DashboardSpec JSON format |

### Category 3: Data Quality & Governance

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `data-quality` | data quality, DMF, quality score, schema health, SLA alerting | **Delegate** — Snowflake DMFs, table comparison, quality monitoring are beyond dbt tests |
| `data-governance` | governance, masking, PII, GDPR, classify, grants, row access policy | **Delegate** — routes to 5 sub-skills (catalog, masking, classification, maturity, observability) |
| `lineage` | what depends on, impact analysis, upstream, where does this come from | **Delegate** — Snowflake ACCOUNT_USAGE lineage, column-level tracing |

### Category 4: Snowflake Platform

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `dynamic-tables` | dynamic table, DT, target lag, incremental refresh, UPSTREAM_FAILED | **Delegate** — specialized in DT creation, optimization, troubleshooting |
| `iceberg` | iceberg, catalog integration, external volume, Glue, CLD, auto-refresh | **Delegate** — catalog integrations, external volumes, auto-refresh |
| `snowflake-notebooks` | notebook, .ipynb, workspace notebook, SQL cell, Snowpark session | **Delegate** — creates/edits Snowflake Workspace notebooks |
| `snowflake-postgres` | postgres, pg, create instance, health check, pg_lake, diagnostics | **Delegate** — Snowflake Postgres instance management |
| `snowpark` | Snowpark, UDF, stored procedure, deploy Python, `snow snowpark` | **Delegate** — Python UDF/SP deployment via CLI |
| `snowpark-connect` | snowpark connect, SCOS, PySpark migration, Spark Connect | **Delegate** — PySpark → Snowpark Connect migration |
| `cortex-ai-functions` | classify, extract, sentiment, summarize, parse PDF, OCR, AI_COMPLETE | **Delegate** — routes to correct Cortex AI function |
| `integrations` | integration, API integration, catalog integration, notification | **Delegate** — all Snowflake integration types |
| `openflow` | Openflow, NiFi, data replication, connector deployment | **Delegate** — NiFi-based data integration |
| `data-cleanrooms` | clean room, DCR, collaboration, audience overlap, activation | **Delegate** — Snowflake Data Clean Room workflows |
| `data-products` | data product, internal marketplace, org listing, share across accounts | **Delegate** — organizational listings and Internal Marketplace |
| `declarative` | declarative, share data, cross account, application package, TYPE=DATA | **Delegate** — declarative sharing with versioned app packages |
| `machine-learning` | train model, ML, model registry, feature store, HPO, distributed | **Delegate** — routes to ML sub-skills (training, registry, inference, etc.) |
| `workload-performance-analysis` | spilling, pruning, cache hit, clustering, slow query, SOS, QAS | **Delegate** — SQL execution analysis via ACCOUNT_USAGE |

### Category 5: Infrastructure & DevOps

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `configuring-dbt-mcp-server` | MCP server, dbt MCP, configure MCP, Claude Desktop, Cursor | **Delegate** — MCP config JSON and connectivity validation |
| `deploy-to-spcs` | SPCS, Docker, container, deploy to Snowflake, Snowpark Container | **Delegate** — containerized app deployment |
| `dbt-projects-on-snowflake` | `snow dbt`, EXECUTE DBT PROJECT, deployed dbt project object | **Delegate** — dbt-as-Snowflake-object (NOT normal dbt dev) |
| `dcm` | DCM, Database Change Management, `snow dcm`, manifest.yml, DEFINE | **Delegate** — infrastructure-as-code for Snowflake objects |
| `migrating-dbt-core-to-fusion` | Fusion migration, migration errors, dbt Fusion, auto-fixable | **Delegate** — migration error triage |
| `migrating-dbt-project-across-platforms` | migrate platform, Snowflake to Databricks, cross-platform dbt | **Delegate** — cross-platform SQL dialect differences |
| `snowconvert-assessment` | SnowConvert, assessment, migration waves, SSIS, ETL analysis | **Delegate** — workload migration assessment |

### Category 6: Visualization & Apps

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `developing-with-streamlit` | streamlit, st., app.py, beautify, CSS, theme, custom component | **Delegate** — read this skill for any Streamlit work (scaffolding, styling, components, deployment) |
| `build-react-app` | React, Next.js, dashboard app, data app, analytics tool | **Delegate** — React/Next.js data apps with Snowflake |

### Category 7: Security & Cost

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `cost-intelligence` | cost, credits, spending, budget, warehouse cost, top spenders | **Delegate** — all Snowflake cost/billing analysis |
| `network-security` | network policy, network rule, IP allowlist, SaaS rules | **Delegate** — network policies and rules |
| `key-and-secret-management` | TSS, CMK, BYOK, encryption key, key rotation, rekeying | **Delegate** — Tri-Secret Secure and key management |
| `trust-center` | Trust Center, security findings, CIS benchmark, scanner | **Delegate** — security finding analysis and remediation |
| `organization-management` | org, accounts, org users, org spending, globalorgadmin | **Delegate** — org-level management and ORGANIZATION_USAGE |

### Category 8: Meta / Tooling

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `skill_development` | create skill, new skill, audit skill, capture session as skill | **Delegate** — skill authoring and review |
| `cortex-code-guide` | cortex guide, cortex help, cortex commands, #table, sessions | **Delegate** — Cortex Code CLI reference |

---

### How Routing Works

```
User Request
    │
    ▼
┌──────────────────────────────┐
│  dbt One-Stop Agent (this)   │
│  1. Parse intent              │
│  2. Check skill routing table │
│  3. Read project context      │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 HANDLE        DELEGATE
 DIRECTLY      TO SKILL
    │             │
    │             ├── Read SKILL.md for the matched skill
    │             ├── Follow its instructions
    │             └── Return to one-stop agent for next step
    │
    ├── Source discovery
    ├── Model generation (stg/int/fct/dim)
    ├── Snowflake Semantic View creation
    ├── Agent deployment + SI registration
    ├── Code review (static analysis)
    ├── dbt CLI commands
    └── End-to-end pipeline orchestration
```

### Multi-Skill Chaining Examples

| User Request | Skills Chained (in order) |
|-------------|--------------------------|
| "Onboard MY_DB.MY_SCHEMA and create an agent" | `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent` |
| "Add unit tests for fct_orders" | `adding-dbt-unit-test` |
| "What were total sales last quarter?" | `answering-natural-language-questions-with-dbt` |
| "Audit the project before deployment" | `project-quality-audit` → `semantic-view-coverage-audit` |
| "Create a Streamlit dashboard for sales data" | `developing-with-streamlit` (handle basic via `generate_streamlit_app`, delegate for styling) |
| "Deploy fct_orders as a dynamic table" | `dynamic-tables` |
| "Classify PII columns in my marts" | `data-governance` (→ sensitive-data-classification sub-skill) |
| "Show me Snowflake costs by warehouse" | `cost-intelligence` |
| "Train an ML model on my mart data" | `machine-learning` |
| "Create a staging model for this table" | `onboard-bronze-layer` |
| "Build an intermediate model joining orders and customers" | `onboard-silver-layer` |
| "Create a fact table for sales" | `onboard-gold-layer` |
| "Create an Iceberg table from my mart" | `iceberg` |
| "Debug why my semantic view returns wrong SQL" | `semantic-view` |
| "Migrate this project from Databricks to Snowflake" | `migrating-dbt-project-across-platforms` |
| "Set up network policy for my Snowflake account" | `network-security` |
| "Create a Data Clean Room collaboration" | `data-cleanrooms` |
| "Visualize my dbt DAG as a Mermaid diagram" | `creating-mermaid-dbt-dag` |
| "Share my mart data with another Snowflake account" | `declarative` or `data-products` |
| "Create a DCM project for my database objects" | `dcm` |
| "Analyze query performance for slow queries" | `workload-performance-analysis` |

## When to Invoke This Skill

This orchestrator is invoked for **any** dbt or Snowflake request. It does not handle work itself — it routes to the specialized skills listed in the **Required Chains** tables above.

### Routing decision (every request)

1. Match the request to ONE row in the Required Chains tables (Categories 1–8).
2. `read_file` each skill in the chain, in order.
3. Execute the chain.
4. Report `Skills used: …`.

If and only if no row matches, fall back to inline templates in this file and announce it (see *Cross-cutting fallback rule*).

### Delegation summary

The legacy bullet list of "delegate to X" mappings has been consolidated into the **Required Chains** tables above (Categories 1–8). That is now the single source of truth — do not maintain a parallel list here.

## Context-Awareness (CRITICAL)

This agent is **NOT deterministic/generic**. Before generating ANY code, it:

1. **Reads existing models** — understands what staging, intermediate, marts models already exist
2. **Profiles actual data** — queries Snowflake for column types, cardinality, null rates
3. **Inspects schema.yml** — knows which tests and descriptions are already defined
4. **Understands the DAG** — resolves model references and avoids generating duplicates
5. **Checks naming conventions** — ensures output matches `stg_<source>__<table>`, `int_<desc>`, `fct_<entity>`, `dim_<entity>`

## How to Run

### Interactive CLI (Cortex-powered chat)
```bash
python scripts/dbt_agent.py
```

### Single Question
```bash
python scripts/dbt_agent.py --ask "What sources do I have?"
```

### MCP Server (VS Code / Cortex Code)
```bash
python scripts/dbt_agent.py --mcp
```

## Available Tools

| Tool | Parameters | What It Does |
|------|-----------|-------------|
| `project_context` | *(none)* | Get project summary: sources, model counts, layer breakdown |
| `discover_source` | `source_database`, `source_schema`, `source_name?`, `dry_run?` | Discover tables and generate staging + mart models |
| `list_sources` | `source_name?` | List dbt source definitions |
| `list_models` | `layer?`, `source_name?` | List models by layer |
| `read_model` | `model_name` | Read a model's SQL source code |
| `sample_data` | `table_or_model`, `limit?` | Query sample rows from Snowflake |
| `describe_table` | `table_or_model` | Get column metadata + row count |
| `profile_data` | `table_or_model`, `max_columns?` | Profile: distinct counts, null rates, cardinality |
| `run_query` | `sql` | Execute read-only SQL query |
| `generate_model` | `layer`, `source_name`, `model_name`, `sql`, `description?` | Create/update any dbt model + schema.yml |
| `deploy_agent` | `model_name`, `agent_name?`, `warehouse?` | Create Snowflake Agent wired to Snowflake Semantic Views |
| `register_intelligence` | `agent_name` | Register agent with Snowflake Intelligence UI |
| `review_sql` | `model_name?`, `sql_content?` | Static analysis for best practices |
| `check_data_quality` | `select?` | Run dbt tests |
| `run_dbt` | `command`, `select?`, `full_refresh?` | Execute dbt CLI commands |
| `generate_streamlit_app` | `model_name`, `app_title?` | Scaffold Streamlit dashboard |
| `generate_domain_semantic_views` | `domain`, `overwrite?`, `dry_run?` | Auto-generate semantic views for ALL marts in a domain |
| `create_domain_agent` | `domain`, `database?`, `register_si?`, `dry_run?` | Create Cortex Agent SQL bundling all semantic views for a domain |
| `run_end_to_end_pipeline` | `domain`, `skip_discover?`, `register_si?`, `source_database?`, `source_schema?`, `source_name?`, `overwrite?`, `dry_run?` | Full pipeline: Discover → Stage → Marts → Build → Semantic → Agent |

## Workflow Examples

### Discover a New Data Source
```
User: "Discover tables in COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC"
Agent:
  1. Calls project_context() to see current state
  2. Calls discover_source(source_database="COVID19_EPIDEMIOLOGICAL_DATA", source_schema="PUBLIC", source_name="covid19_data")
  3. Reports: tables found, staging models created, mart models created
  4. Auto-runs dbt build for the new models
```

### Build a Silver Model
```
User: "Create an intermediate model that enriches orders with customer data"
Agent:
  1. Calls list_models(layer="staging") to find source models
  2. Calls read_model("stg_tpch__orders") to understand columns
  3. Calls read_model("stg_tpch__customers") to understand join keys
  4. Calls profile_data("stg_tpch__orders") to check cardinality
  5. Generates int_orders_enriched with proper joins and naming
  6. Auto-builds and reports results
```

### Create a Snowflake Semantic View
```
User: "Create a semantic view for fct_orders"
Agent:
  1. Reads fct_orders model and schema.yml
  2. Classifies columns into dimensions vs metrics using naming patterns and types
  3. Creates models/semantic/sem_orders/sem_orders.sql (TABLES/DIMENSIONS/METRICS DDL-like syntax)
  4. Creates models/semantic/sem_orders/sem_orders.yml (verified queries + description)
  5. Runs: dbt build --select sem_orders
     → Creates Snowflake Semantic View + attaches verified queries via post-hook
  6. Verifies: SHOW SEMANTIC VIEWS IN SCHEMA <DATABASE>.SEMANTIC
```

### Deploy a Snowflake Agent + Snowflake Intelligence
```
User: "Deploy an agent for fct_orders and register with Snowflake Intelligence"
Agent:
  1. Verifies Snowflake Semantic View exists (or creates it first via snowflake-semantic-view-creator)
  2. Derives variables: DATABASE, SCHEMA, WAREHOUSE from profiles.yml/dbt_project.yml
  3. Generates CREATE AGENT SQL with cortex_analyst_text_to_sql tool spec referencing the semantic view
  4. Executes CREATE AGENT via run_query()
  5. Registers with: ALTER SNOWFLAKE INTELLIGENCE ... ADD AGENT
  6. Grants permissions: USAGE on agent, warehouse, semantic views, schema
  7. Verifies: DESCRIBE AGENT, test question via Snowflake Intelligence UI
```

## Review Enforcement

All model writes are **automatically reviewed** before being written to disk. This is a code-level gate — it cannot be skipped by the LLM.

### How it works
- `generate_model` and `write_medallion_model` run static analysis before writing
- `discover_source` reviews generated mart models before writing (staging models are template-trusted)
- After auto-build, each generated model is reviewed and results are returned to the LLM

### Severity levels

| Severity | Effect | Example |
|----------|--------|---------|
| **error** | **Blocks write** — returns `REVIEW_BLOCKED` | Hard-coded `database.schema.table` (use `ref()`/`source()`) |
| **warning** | Write succeeds, reported in response | `SELECT *` in marts, missing `ref()`, naming violations |
| **info** | Write succeeds, reported in response | `LIMIT` clause in production model |

### Review rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| `HARDCODED_SCHEMA` | `FROM/JOIN db.schema.table` | error |
| `NO_SELECT_STAR_MARTS` | `SELECT *` in marts/semantic | warning |
| `MISSING_REF` | Direct table reference without `ref()`/`source()` | warning |
| `NO_LIMIT` | `LIMIT N` in model SQL | info |
| `NAMING_STG` | Staging model not prefixed `stg_` | warning |

### Force bypass
Pass `force=True` (agent) or `force=true` (MCP) to write despite error-severity issues. The errors are still reported in the response `review` field.

## Project Conventions

- **Staging**: `stg_<source>__<table>` — 1:1 with source, rename columns to snake_case
- **Intermediate**: `int_<description>` — joins, dedup, business logic
- **Marts**: `fct_<entity>` (facts) or `dim_<entity>` (dimensions) — consumption-ready
- **Semantic Views**: `models/semantic/sem_<name>/sem_<name>.sql` — Snowflake Semantic Views via `dbt_semantic_view` package
- Always use `{{ ref() }}` and `{{ source() }}`
- Use CTEs, not subqueries
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys
- Every model must have a schema.yml entry with description and tests

---

## Snowflake Semantic View → Agent Workflow

> This is the workflow for creating Snowflake Semantic Views, deploying Cortex Agents
> wired to those semantic views, and registering with Snowflake Intelligence.
> Reference: `snowflake-semantic-view-creator` skill for detailed semantic view creation.

### Phase 1: Create Snowflake Semantic Views

For a given mart model (e.g., `fct_orders`):

#### 1.1 — Read the mart model and its schema.yml

```
1. Read models/marts/<domain>/schema.yml → get column names, descriptions, tests
2. Read models/marts/<domain>/fct_<entity>.sql → understand the SQL, grain, joins
3. Identify: table alias to use in TABLES(), all columns for classification
```

#### 1.2 — Classify columns into dimensions and metrics

Apply the **Column Classification Rules** (defined once in Step 5.2 below) to classify each column.

#### 1.3 — Create the semantic view SQL + YAML files

Follow the **templates and rules** in Steps 5.3 and 5.4 below.

#### 1.4 — Build and verify

```bash
dbt compile --select tag:semantic
dbt build --select tag:semantic
```

```sql
SHOW SEMANTIC VIEWS IN SCHEMA <DATABASE>.SEMANTIC;
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('<DATABASE>.SEMANTIC.SEM_<NAME>');
```

### Phase 2: Deploy Snowflake Agent (using Semantic Views)

#### 2.1 — Derive variables from project context (do NOT ask user)

| Variable | Source |
|----------|--------|
| `DATABASE` | `profiles.yml` → target `database` |
| `SCHEMA` | `SEMANTIC` (where agents + semantic views live) |
| `WAREHOUSE` | `profiles.yml` or `dbt_project.yml` |
| `AGENT_NAME` | `AGENT_` + uppercase entity (e.g., `AGENT_SALES_ANALYSIS`) |
| `SEMANTIC_VIEW` | `SEM_<NAME>` from Phase 1 |

#### 2.2 — Check for existing agent

```sql
SHOW AGENTS IN SCHEMA <DATABASE>.SEMANTIC;
```

#### 2.3 — Create the agent (referencing semantic views, NOT YAML files)

```sql
CREATE OR REPLACE AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>
  COMMENT = '<description of what data and questions it handles>'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "auto"},
    "tools": [{
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "analyst",
        "description": "<what tables, data, and question types this covers>"
      }
    }],
    "tool_resources": {
      "analyst": {
        "semantic_model": "<DATABASE>.SEMANTIC.SEM_<NAME>",
        "execution_environment": {
          "type": "warehouse",
          "warehouse": "<WAREHOUSE>"
        }
      }
    }
  }
  $$;
```

**Multi-view agents:** If the domain has multiple semantic views, add one tool per view:
```json
"tools": [
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales", "description": "..."}},
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "products", "description": "..."}}
],
"tool_resources": {
  "sales": {"semantic_model": "<DATABASE>.SEMANTIC.SEM_SALES", ...},
  "products": {"semantic_model": "<DATABASE>.SEMANTIC.SEM_PRODUCTS", ...}
}
```
Best practice: 5–10 tools per agent max.

#### 2.4 — Verify agent

```sql
DESCRIBE AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>;
```

### Phase 3: Register with Snowflake Intelligence

#### 3.1 — Ensure SI object exists

```sql
SHOW SNOWFLAKE INTELLIGENCES;
-- If empty:
CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;
```

#### 3.2 — Register the agent

```sql
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>;
```

#### 3.3 — Grant permissions

```sql
-- For the consuming role (e.g., DBT_ROLE or ANALYST_ROLE)
GRANT USAGE ON DATABASE <DATABASE> TO ROLE <ROLE>;
GRANT USAGE ON SCHEMA <DATABASE>.SEMANTIC TO ROLE <ROLE>;
GRANT USAGE ON AGENT <DATABASE>.SEMANTIC.<AGENT_NAME> TO ROLE <ROLE>;
GRANT USAGE ON WAREHOUSE <WAREHOUSE> TO ROLE <ROLE>;
GRANT SELECT ON ALL SEMANTIC VIEWS IN SCHEMA <DATABASE>.SEMANTIC TO ROLE <ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE>.DBT_MARTS TO ROLE <ROLE>;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE <ROLE>;
```

#### 3.4 — Verify end-to-end

```sql
SHOW AGENTS IN SCHEMA <DATABASE>.SEMANTIC;
SHOW SNOWFLAKE INTELLIGENCES;
-- Then in Snowsight: AI & ML → Snowflake Intelligence → select agent → ask a question
```

### Phase Summary

| Phase | What Happens | Output |
|-------|-------------|--------|
| 1. Create Semantic Views | Classify columns, create `sem_*.sql` + `sem_*.yml`, `dbt build` | Snowflake Semantic View objects in `SEMANTIC` schema |
| 2. Deploy Agent | `CREATE AGENT` referencing semantic views | Agent object in `SEMANTIC` schema |
| 3. Register SI | `ALTER SNOWFLAKE INTELLIGENCE ADD AGENT` | Agent visible in Snowsight Intelligence UI |

---

## RBAC / Security for Cortex Copilot

> **NEVER use ACCOUNTADMIN** for Cortex Copilot, Cortex Analyst, or Snowflake Intelligence.

### Role Hierarchy

```
ACCOUNTADMIN  (one-time setup only)
  └── DBT_ROLE  (dbt build, model deployment)
        └── CORTEX_ANALYST_ROLE  (Cortex Copilot / Analyst / Intelligence)
```

### CORTEX_ANALYST_ROLE Permissions

| Can | Cannot |
|-----|--------|
| SELECT from mart tables | Create/alter/drop ANY objects |
| Read semantic views | Access staging or intermediate schemas |
| Use Snowflake Semantic Views | Modify source data |
| Use the warehouse | Manage roles, users, or warehouses |
| Invoke Cortex Agents | Access ACCOUNT_USAGE or ORGANIZATION_USAGE |
| Query via Snowflake Intelligence | — |

### Setup SQL

Run `scripts/snowflake_cortex_rbac_setup.sql` as ACCOUNTADMIN (one-time):

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS CORTEX_ANALYST_ROLE;

-- Read-only access to marts and semantic views
GRANT USAGE ON DATABASE DBT_DEV TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL SEMANTIC VIEWS IN SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE CORTEX_ANALYST_ROLE;

-- Hierarchy: DBT_ROLE inherits CORTEX_ANALYST_ROLE
GRANT ROLE CORTEX_ANALYST_ROLE TO ROLE DBT_ROLE;
```

For Copilot users, set the session role:
```sql
USE ROLE CORTEX_ANALYST_ROLE;
-- Or set as default: ALTER USER <user> SET DEFAULT_ROLE = 'CORTEX_ANALYST_ROLE';
```

---

## End-to-End Pipeline

> Full pipeline: **Discover → Stage → Marts → Validate → Snowflake Semantic Views → Agent**
>
> **IMPORTANT**: When operating as a GitHub Copilot agent (not via MCP/CLI tools), you MUST
> follow the inline step-by-step instructions below to create semantic views by reading/writing
> files directly. Do NOT just reference tool names like `generate_domain_semantic_views()` — those
> only work via the MCP server (`dbt_agent.py`). Instead, follow the manual file creation steps below.

---

### Pipeline Overview

| Step | What Happens | Output |
|------|-------------|--------|
| 1. Discover & Profile | Connect to Snowflake, discover tables, profile columns | Source metadata |
| 2. Generate Staging | Create `stg_<source>__<table>.sql` + `_sources.yml` + `schema.yml` | `models/staging/<source>/` |
| 3. Generate Marts | Create `fct_<entity>.sql` / `dim_<entity>.sql` + `schema.yml` | `models/marts/<source>/` |
| 4. dbt Build & Validate | `dbt build --select "source:<source>+"` | Materialized models + test results |
| 5. Create Snowflake Semantic Views | Create `sem_<name>.sql` + `sem_<name>.yml` for each mart | `models/semantic/sem_<name>/` |
| 6. Build Semantic Views | `dbt build --select tag:semantic` | Semantic views in Snowflake + verified queries attached |
| 7. (Optional) Deploy Agent | CREATE AGENT SQL bundling semantic views | `ddl/cortex-analyst/deploy_agent_<domain>.sql` |

---

### Step 5 — Create Snowflake Semantic Views (DETAILED — follow these steps exactly)

> **This is the step that was previously missing inline instructions.** When working as a
> Copilot agent, you MUST create these files manually by reading/writing files directly.
> Snowflake Semantic Views are the primary mechanism for Cortex Analyst NL querying.

For EACH mart model (`fct_*`, `dim_*`, `summary_*`) in `models/marts/<domain>/`:

#### 5.1 — Read the mart model and its schema.yml

```
1. Read models/marts/<domain>/schema.yml → get column names, descriptions, tests
2. Read models/marts/<domain>/fct_<entity>.sql → understand the SQL, grain, joins
3. Identify: table alias to use in TABLES(), all columns for classification
```

#### 5.2 — Classify columns into dimensions and metrics

Apply these rules to EACH column:

| Column Pattern | Classification | Semantic View Section |
|---------------|---------------|----------------------|
| `*_date`, `*_at`, `*_timestamp`, `date`, `month`, `year` | Time dimension | `DIMENSIONS` |
| `*_status`, `*_type`, `*_category`, `*_segment`, `*_flag`, `is_*`, `has_*` | Categorical dimension | `DIMENSIONS` |
| `*_name`, `*_region`, `*_country`, `*_city`, `*_code`, `maker`, `brand` | Entity dimension | `DIMENSIONS` |
| `*_amount`, `*_revenue`, `*_sales`, `*_cost`, `*_total`, `*_quantity`, `*_count` | Metric (SUM) | `METRICS` with `SUM()` |
| `*_rate`, `*_pct`, `*_ratio`, `*_avg`, `average_*` | Metric (AVG) | `METRICS` with `AVG()` |
| `*_key`, `*_id`, `*_sk` | Key — **SKIP** | Do not include |
| `*_loaded_at`, `*_etl_*` | ETL — **SKIP** | Do not include |

**Use the column descriptions from schema.yml + actual SQL context to resolve ambiguous cases.**

#### 5.3 — Create the semantic view SQL file

Create directory and file: `models/semantic/sem_<name>/sem_<name>.sql`

**Template** (copy and adapt — do NOT deviate from this structure):

```sql
{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_<name>'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  t AS {{ ref('fct_<entity>') }}
)
DIMENSIONS (
  t.<dim_col_1> AS <dim_col_1>
    COMMENT = '<description from schema.yml or inferred>',
  t.<dim_col_2> AS <dim_col_2>
    COMMENT = '<description>'
)
METRICS (
  t.<metric_alias> AS SUM(<metric_col>)
    COMMENT = '<description>',
  t.<metric_alias_2> AS AVG(<metric_col_2>)
    COMMENT = '<description>'
)
COMMENT = '<One-line description of what this semantic view enables for Cortex Analyst>'

- AI_SQL_GENERATION $$
- <Instruction 1: map business terms to columns>
- <Instruction 2: how to handle time queries>
- <Instruction 3: default aggregations and orderings>
$$
```

**Rules:**
- The `config()` block uses `materialized = 'semantic_view'` — this is provided by `dbt_packages/dbt_semantic_view`
- `schema = 'SEMANTIC'` is already set in `dbt_project.yml` for the semantic folder but include it explicitly
- The `post_hook` calls `publish_verified_queries()` which reads verified queries from the `.yml` and attaches them
- Use `{{ ref('fct_<entity>') }}` in `TABLES()` — NEVER hard-code database/schema names
- The table alias (e.g., `t` or `sales`) is used in `DIMENSIONS()` and `METRICS()`
- Every dimension and metric MUST have a `COMMENT`
- `AI_SQL_GENERATION` block guides Cortex Analyst text-to-SQL behavior

#### 5.4 — Create the semantic view YAML file

Create: `models/semantic/sem_<name>/sem_<name>.yml`

**Template:**

```yaml
version: 2

models:
  - name: sem_<name>
    description: >
      Semantic view for <domain> analytics built from <mart_model>.
      Grain: one row per (<grain columns>).
      Enables Cortex Analyst natural language querying over <domain> data.
    config:
      meta:
        verified_queries:
          - name: <descriptive_query_name_1>
            question: "<Natural language business question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <dimension>, SUM(<metric>) AS total
              FROM t
              GROUP BY <dimension>
              ORDER BY total DESC
          - name: <descriptive_query_name_2>
            question: "<Time-trend question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <date_dim>, SUM(<metric>) AS total
              FROM t
              GROUP BY <date_dim>
              ORDER BY <date_dim> DESC
              LIMIT 30
          - name: <descriptive_query_name_3>
            question: "<Dimensional breakdown question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <dim1>, <dim2>, SUM(<metric>) AS total
              FROM t
              GROUP BY <dim1>, <dim2>
              ORDER BY total DESC
```

**Verified query rules:**
- `sql` uses the **table alias** from `TABLES()` (e.g., `t` or `sales`), NOT the physical table name
- `verified_at` is a Unix timestamp in seconds (use current epoch, e.g., `1745452800`)
- Write 3–5 queries covering: summary, time trend, top-N, dimensional breakdown, filtered
- If you have MCP access, test each query via `run_query()` first — only include passing queries

#### 5.5 — Example: Complete semantic view for `fct_sales`

**File: `models/semantic/sem_revenue_analysis/sem_revenue_analysis.sql`**
```sql
{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_revenue_analysis'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  sales AS {{ ref('fct_sales') }}
)
DIMENSIONS (
  sales.sales_date AS sales_date
    COMMENT = 'Date of sales activity',
  sales.maker AS maker
    COMMENT = 'Manufacturer or brand of the item sold',
  sales.item_category AS item_category
    COMMENT = 'Product category (Smartphone or Other)'
)
METRICS (
  sales.total_revenue AS SUM(total_sales)
    COMMENT = 'Total sales revenue',
  sales.total_transactions AS SUM(transaction_count)
    COMMENT = 'Total number of transactions',
  sales.avg_price AS AVG(average_price)
    COMMENT = 'Average item price'
)
COMMENT = 'Revenue analysis by maker, category, and time for Cortex Analyst'

- AI_SQL_GENERATION $$
- When users ask about "revenue", "sales", or "transactions", query this semantic view.
- total_sales is the primary revenue metric — always use SUM aggregation.
- For time-based queries, group by sales_date.
- maker represents the manufacturer or brand.
- item_category is either "Smartphone" or "Other".
$$
```

**File: `models/semantic/sem_revenue_analysis/sem_revenue_analysis.yml`**
```yaml
version: 2

models:
  - name: sem_revenue_analysis
    description: >
      Semantic view for sales analytics built from fct_sales.
      Grain: one row per (sales_date, maker, item_category).
      Enables Cortex Analyst natural language querying over revenue data.
    config:
      meta:
        verified_queries:
          - name: total_revenue_by_maker
            question: "What is the total revenue by maker?"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT maker, SUM(total_sales) AS total_revenue
              FROM sales
              GROUP BY maker
              ORDER BY total_revenue DESC
          - name: daily_sales_trend
            question: "Show the daily sales trend"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT sales_date, SUM(total_sales) AS total_revenue
              FROM sales
              GROUP BY sales_date
              ORDER BY sales_date DESC
              LIMIT 30
          - name: revenue_by_category
            question: "What is the revenue breakdown by item category?"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT item_category,
                     SUM(total_sales) AS total_revenue,
                     SUM(transaction_count) AS total_transactions
              FROM sales
              GROUP BY item_category
              ORDER BY total_revenue DESC
```

#### 5.6 — Build the semantic views

```bash
# Compile first to catch Jinja errors
dbt compile --select tag:semantic

# Build — creates semantic views in Snowflake + attaches verified queries via post-hook
dbt build --select tag:semantic
```

#### 5.7 — Verify in Snowflake (if MCP access available)

```sql
-- Check semantic views exist
SHOW SEMANTIC VIEWS IN SCHEMA <DATABASE>.SEMANTIC;

-- Read the full definition including verified queries
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('<DATABASE>.SEMANTIC.SEM_<NAME>');
```

---

### For an existing domain (marts already built):

```
User: "Create semantic views and an agent for japan_ecomm_data"
Agent:
  1. Read models/marts/japan_ecomm_data/schema.yml → list all mart models and columns
  2. For EACH mart model (fct_*, dim_*, summary_*):
     a. Classify columns into dimensions vs metrics (Step 5.2 rules)
     b. Create models/semantic/sem_<name>/sem_<name>.sql (Step 5.3 template)
     c. Create models/semantic/sem_<name>/sem_<name>.yml (Step 5.4 template)
  3. Run: dbt build --select tag:semantic
     → Materializes semantic views in Snowflake
     → publish_verified_queries() post-hook attaches verified queries
  4. (Optional) Generate Cortex Agent SQL with all semantic views as tools
     → Output: ddl/cortex-analyst/deploy_agent_japan_ecomm_data.sql
  5. Report: semantic views created, build results, next steps
```

### For a brand-new source:

```
User: "Onboard MY_DATABASE.MY_SCHEMA and create an agent"
Agent:
  1. Profile source table (Step 1 from onboard-new-source)
  2. Generate staging models: stg_<source>__<table>.sql + _sources.yml + schema.yml
  3. Generate mart models: fct_<entity>.sql + schema.yml
  4. Run: dbt build --select "source:<source>+"
  5. For EACH mart model created in step 3:
     a. Classify columns into dimensions vs metrics (Step 5.2 rules)
     b. Create models/semantic/sem_<name>/sem_<name>.sql (Step 5.3 template)
     c. Create models/semantic/sem_<name>/sem_<name>.yml (Step 5.4 template)
  6. Run: dbt build --select tag:semantic
  7. (Optional) Generate Cortex Agent SQL referencing the semantic views
  8. Report: full pipeline output, agent SQL location, RBAC instructions
```

### CLI Shortcuts (when using scripts directly)

```bash
# Existing domain — via scripts
python scripts/generate_semantic_views_for_domain.py --domain japan_ecomm_data
dbt build --select tag:semantic
python scripts/create_domain_agent.py --domain japan_ecomm_data --register-si

# New source — one command
python scripts/end_to_end_pipeline.py \
  --source-database MY_DB --source-schema MY_SCHEMA --register-si

# Existing domain — one command
python scripts/end_to_end_pipeline.py --domain japan_ecomm_data --skip-discover --register-si
```

### Pipeline Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/generate_semantic_views_for_domain.py` | Batch-generate semantic views for all marts in a domain |
| `scripts/create_domain_agent.py` | Create Cortex Agent SQL bundling all semantic views |
| `scripts/end_to_end_pipeline.py` | Full orchestrator: discover → semantic → agent |
| `scripts/snowflake_cortex_rbac_setup.sql` | CORTEX_ANALYST_ROLE setup (least-privilege) |

---

## Related Skills — Quick Reference (53 Skills)

> **All 53 skills live in `.snowflake/cortex/skills/<skill-name>/SKILL.md`.**
> The full routing table with triggers and delegation rules is in the **Skill Routing Table** section above.
> Always `read_file` the target SKILL.md before delegating — see **Delegation Protocol** at the top.

| Category | Count | Skills |
|----------|-------|--------|
| dbt Core Workflow | 12 | `using-dbt-for-analytics-engineering`, `adding-dbt-unit-test`, `running-dbt-commands`, `fetching-dbt-docs`, `creating-mermaid-dbt-dag`, `onboard-new-source`, `onboard-bronze-layer`, `onboard-silver-layer`, `onboard-gold-layer`, `troubleshooting-dbt-job-errors`, `project-quality-audit`, `dbt-one-stop-agent` |
| Semantic Layer & NL Querying | 9 | `building-dbt-semantic-layer`, `answering-natural-language-questions-with-dbt`, `snowflake-semantic-view-creator`, `semantic-view`, `semantic-view-batch-sync`, `semantic-view-coverage-audit`, `cortex-analyst-semantic-model`, `cortex-agent`, `dashboard` |
| Data Quality & Governance | 3 | `data-quality`, `data-governance`, `lineage` |
| Snowflake Platform | 14 | `dynamic-tables`, `iceberg`, `snowflake-notebooks`, `snowflake-postgres`, `snowpark`, `snowpark-connect`, `cortex-ai-functions`, `integrations`, `openflow`, `data-cleanrooms`, `data-products`, `declarative`, `machine-learning`, `workload-performance-analysis` |
| Infrastructure & DevOps | 7 | `configuring-dbt-mcp-server`, `deploy-to-spcs`, `dbt-projects-on-snowflake`, `dcm`, `migrating-dbt-core-to-fusion`, `migrating-dbt-project-across-platforms`, `snowconvert-assessment` |
| Visualization & Apps | 2 | `developing-with-streamlit`, `build-react-app` |
| Security & Cost | 5 | `cost-intelligence`, `network-security`, `key-and-secret-management`, `trust-center`, `organization-management` |
| Meta / Tooling | 2 | `skill_development`, `cortex-code-guide` |
