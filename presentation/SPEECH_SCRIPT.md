# Novo Nordisk Stakeholder Presentation — Speaker Script

## Duration: ~25 minutes | 15 slides

---

## SLIDE 1: Title Slide
**"From Raw Data to Natural Language Answers — Intelligent Analytics on Snowflake"**

### Speaker Notes:

> Good [morning/afternoon], everyone.
>
> Today I want to walk you through something that fundamentally changes how our teams interact with data. We've built an end-to-end intelligent analytics platform on Snowflake that takes raw data — any raw data — and makes it queryable in plain English.
>
> No SQL. No dashboards to build. No waiting weeks for the BI team.
>
> A business user simply types: *"What was our Q1 revenue by product category?"* — and gets an accurate answer, instantly.
>
> Let me show you how we got there, and what this means for Novo Nordisk.

---

## SLIDE 2: The Problem We're Solving
**"The Analytics Bottleneck"**

### Speaker Notes:

> Let's start with the problem. Today, getting insights from data at Novo Nordisk follows a familiar pattern:
>
> 1. A business stakeholder has a question
> 2. They file a request to the analytics team
> 3. The analytics team writes SQL, builds a dashboard
> 4. Stakeholder reviews — says "actually, I meant *this*..."
> 5. Iterate. Wait. Repeat.
>
> This cycle takes **days to weeks**. And it creates two problems:
>
> **First** — the analytics team becomes a bottleneck. Every question, no matter how simple, requires their time.
>
> **Second** — by the time you get the answer, the business moment may have passed. In pharma and healthcare, timely data can be the difference between a good decision and a missed opportunity.
>
> What if we could eliminate this entire cycle? What if every authorized user could simply *ask their data a question* and get an immediate, accurate, governed answer?
>
> That's exactly what we've built.

---

## SLIDE 3: The Solution — Medallion Architecture + Semantic Intelligence
**"Our Approach: Three Layers of Intelligence"**

### Speaker Notes:

> Our solution has three layers — and I want to walk through each one because understanding the architecture gives you confidence in the results.
>
> **Layer 1: The Medallion Data Architecture**
> We use dbt — the industry standard for data transformation — to organize data into three tiers:
>
> - **Bronze (Staging)**: Raw data, cleaned and renamed. One-to-one with source tables.
> - **Silver (Intermediate)**: Business logic applied — joins, enrichments, validations.
> - **Gold (Marts)**: The consumption-ready analytical tables — facts and dimensions that your analysts and reports already depend on.
>
> This is rigorous data engineering. Every model has automated tests — primary key integrity, null checks, referential integrity, accepted value validation. Nothing gets to the gold layer without passing quality gates.
>
> **Layer 2: Semantic Views — Teaching Snowflake What the Data Means**
> This is where it gets interesting. On top of our gold mart tables, we create what Snowflake calls **Semantic Views**. Think of these as a metadata layer that describes your data in business terms:
>
> - This column is a *dimension* — something you filter or group by (like product category, region, or date)
> - This column is a *metric* — something you aggregate (like revenue, quantity, or patient count)
> - Here are *verified queries* — known-good SQL examples that demonstrate how to answer common business questions
>
> The Semantic View is the bridge between raw column names like `TXN_AMT_USD` and the business concept *"total revenue"*.
>
> **Layer 3: Cortex Agents + Snowflake Intelligence**
> Once semantic views exist, we wire them to Snowflake's **Cortex Agents** — AI agents that use Large Language Models to convert natural language questions into SQL. The agent reads the semantic view, understands the dimensions and metrics, references the verified queries, and generates accurate SQL.
>
> Finally, we register these agents with **Snowflake Intelligence** — making them available organization-wide through the Snowsight UI. Any authorized user can query data in English.

---

## SLIDE 4: End-to-End Flow Diagram
**"The Pipeline: Source → Models → Semantic Views → Agent → Intelligence"**

### Speaker Notes:

> Let me show you the complete pipeline visually.
>
> *(Point to diagram)*
>
> We start with **raw data in Snowflake** — this could be any database. In our reference implementation, we've onboarded four different data domains: COVID-19 epidemiological data, Japan e-commerce transactions, US Census data, and company datasets. The system is source-agnostic.
>
> **Step 1**: Our automated discovery tool connects to any Snowflake schema, profiles every table — column types, cardinality, null rates — and generates the complete staging layer automatically. What used to take a data engineer a full day takes under 5 minutes.
>
> **Step 2**: dbt builds the transformation pipeline — staging views, intermediate enrichment, and gold-layer fact and dimension tables. All with tests, all with documentation.
>
> **Step 3**: Our semantic view automation scans every mart model, classifies each column as a dimension or metric using intelligent pattern matching, and generates the `CREATE SEMANTIC VIEW` DDL. We have 16 dimension patterns and 7 metric patterns that catch date fields, categorical fields, entity names, amounts, quantities, and rates.
>
> **Step 4**: Verified queries are appended to each semantic view — these are known-good SQL examples that train the AI on how to answer common questions. This improves text-to-SQL accuracy significantly.
>
> **Step 5**: A Cortex Agent is created and linked to the semantic view. The agent becomes the "brain" that translates English to SQL.
>
> **Step 6**: The agent is registered with Snowflake Intelligence — and now anyone in the organization with the right role can ask questions in plain English from the Snowsight UI.
>
> The entire flow is automated. The entire flow is governed. And the entire flow is repeatable for any new data source.

---

## SLIDE 5: Semantic Views Deep Dive
**"The Secret Sauce: How We Teach AI to Understand Business Data"**

### Speaker Notes:

> Let me go deeper on semantic views because this is the key innovation.
>
> A semantic view is a **native Snowflake object**. It doesn't copy data — it sits on top of your existing mart table and adds meaning.
>
> Here's what a real semantic view looks like for our sales mart:
>
> ```
> TABLES:
>   sales AS fct_sales
>
> DIMENSIONS:
>   sales.sales_date     → "Date of the transaction"
>   sales.maker          → "Product manufacturer/brand"
>   sales.item_category  → "Product category"
>
> METRICS:
>   total_revenue = SUM(total_sales) → "Total sales revenue"
>   avg_price     = AVG(avg_price)   → "Average transaction price"
>   order_count   = SUM(txn_count)   → "Number of transactions"
> ```
>
> When Cortex Analyst receives a question like *"Show me Apple's revenue trend by month"*, it reads this semantic view and understands:
> - "Apple" maps to the `maker` dimension
> - "revenue" maps to the `total_revenue` metric (SUM of total_sales)
> - "by month" means `DATE_TRUNC('month', sales_date)`
> - It generates: `SELECT DATE_TRUNC('month', sales_date), SUM(total_sales) FROM fct_sales WHERE maker = 'Apple' GROUP BY 1 ORDER BY 1`
>
> That's a correct, performant query — generated in milliseconds from a plain English question.
>
> Now, multiply this across every mart in your data warehouse. That's the power of semantic views at scale.

---

## SLIDE 6: Verified Queries — Improving AI Accuracy
**"Verified Queries: The Feedback Loop That Makes AI Smarter"**

### Speaker Notes:

> One of the biggest concerns with AI-generated SQL is accuracy. What if the model gets the join wrong? What if it misinterprets "quarterly" as calendar quarter vs. fiscal quarter?
>
> This is where **verified queries** come in.
>
> Verified queries are curated SQL examples embedded directly inside the semantic view. They answer common business questions with known-correct SQL. When Cortex Analyst encounters a similar question, it uses these as reference patterns.
>
> For example:
>
> - **Question**: "What was total revenue by product category?"
> - **Verified SQL**: `SELECT item_category, SUM(total_sales) FROM fct_sales GROUP BY item_category ORDER BY 2 DESC`
>
> These verified queries serve three purposes:
>
> 1. **Accuracy**: The AI has reference examples to learn from — like giving a new analyst a set of "starter queries"
> 2. **Governance**: Your analytics team vets these queries, ensuring business logic is correct
> 3. **Iterative improvement**: As users ask more questions, your team can add more verified queries — the system gets smarter over time
>
> In our implementation, verified queries are managed through a dbt post-hook macro. Every time you run `dbt build`, the verified queries are automatically published to the semantic view. No manual SQL execution needed.

---

## SLIDE 7: From Semantic View to Agent to Intelligence
**"The Last Mile: Making Data Conversational for Every User"**

### Speaker Notes:

> So we have semantic views with rich metadata and verified queries. Now let's connect the dots to end-user experience.
>
> **Step 1: Create a Cortex Agent**
>
> ```sql
> CREATE AGENT sales_analyst
>   USING (
>     cortex_analyst_text_to_sql(
>       semantic_view => 'SEMANTIC.SEM_REVENUE_ANALYSIS'
>     )
>   )
>   COMMENT = 'Sales data analyst for revenue, products, and trends';
> ```
>
> That's it. One SQL statement. The agent is now live and can answer questions about sales data.
>
> **Step 2: Register with Snowflake Intelligence**
>
> Snowflake Intelligence is the organization-wide natural language interface. Once we register our agent, it appears in the Snowsight sidebar for any user with the right role.
>
> A business user in Copenhagen, a regional manager in Tokyo, a finance controller in New Jersey — they all open Snowsight, click "Ask a question," and type in English.
>
> No BI tool required. No SQL knowledge needed. No ticket to the analytics team.
>
> **The experience is this simple**:
> 1. User types: *"What were our top 5 products by revenue last quarter?"*
> 2. Agent reads the semantic view, finds the relevant dimensions and metrics
> 3. Agent generates SQL, executes it, and returns the result
> 4. User sees a table with the answer — and can ask follow-up questions
>
> This is **self-service analytics** that actually works — because the semantic layer guarantees accuracy, and the verified queries provide guardrails.

---

## SLIDE 8: Automation & AI-Assisted Development
**"50 AI Skills — How We Build 10x Faster"**

### Speaker Notes:

> I want to touch on how we build and maintain this system, because the development velocity is a key differentiator.
>
> We've assembled **50 AI agent skills** — specialized instruction sets that guide AI coding assistants (GitHub Copilot, Claude Code, Cortex Code) through dbt development tasks.
>
> When a developer opens a model file, the right skills automatically activate:
>
> - Editing a staging model? The **code review skill** checks for SELECT *, hard-coded schemas, missing tests
> - Creating a semantic view? The **semantic view creator skill** provides column classification patterns and DDL templates
> - Onboarding a new source? The **one-stop agent** orchestrates the entire pipeline — from source discovery through semantic view creation
>
> We also have an **MCP server** — Model Context Protocol — that gives AI assistants direct access to Snowflake. The AI can:
> - Profile a table's columns and cardinality
> - Generate a staging model with proper naming and tests
> - Create a semantic view with auto-classified dimensions and metrics
> - Run dbt build and verify tests pass
> - Deploy a Cortex Agent and register it with Intelligence
>
> **The end result**: what used to be a multi-week development cycle — discover data, build models, create semantic layer, deploy agent — can now be completed in a single session.

---

## SLIDE 9: Governance & Quality Gates
**"Enterprise-Grade: Tested, Documented, Governed"**

### Speaker Notes:

> Speed means nothing without governance. In a regulated industry like pharma, every data pipeline must be trustworthy.
>
> Here's how we ensure quality:
>
> **Automated Testing at Every Layer**:
> - **Primary key integrity**: Every model has `unique` + `not_null` tests on its key columns
> - **Referential integrity**: Foreign keys are validated with `relationships` tests
> - **Data quality rules**: Accepted value ranges, column-level expectations using dbt_expectations
> - **Source freshness**: Automated monitoring of when source data was last updated
>
> **Documentation**:
> - Every model has a description in `schema.yml`
> - Every column has a documented definition
> - Semantic views extend documentation with business-friendly metric descriptions
>
> **Quality Audits**:
> - Our **project quality audit skill** scans the entire project for violations: missing tests, empty descriptions, SELECT * in marts, orphaned semantic views
> - Our **semantic view coverage audit** ensures every mart has a corresponding semantic view — no data goes "dark"
>
> **Access Control**:
> - Snowflake's native RBAC governs who can query which data
> - Agents inherit the caller's role — they can only access data the user is authorized to see
> - Row-level and column-level security policies flow through to agent queries
>
> This is not a prototype. This is production-grade infrastructure.

---

## SLIDE 10: Multi-Source Architecture
**"Source-Agnostic: Any Data, Same Pipeline"**

### Speaker Notes:

> A critical design decision: this system is **source-agnostic**.
>
> In our reference implementation, we've onboarded four completely different data domains to prove this:
>
> 1. **COVID-19 Epidemiological Data** — 30+ models across JHU, CDC, WHO, ECDC sources
> 2. **Japan E-Commerce Sales** — Amazon marketplace transaction data with product dimensions
> 3. **US Census Data** — Geographic and demographic data at census block group level
> 4. **Company Registry Data** — Global company information with country dimensions
>
> Each domain follows the identical pattern:
> - Its own staging directory with `_sources.yml` pointing to the raw database
> - Its own intermediate and mart models
> - Its own semantic views
> - Its own Cortex Agent
>
> When Novo Nordisk needs to onboard a new data source — whether that's clinical trial data, supply chain data, or financial data — the process is:
>
> 1. Run the auto-discovery script: `python scripts/discover_and_generate.py`
> 2. The script profiles the source, generates staging models, suggests marts
> 3. Run `dbt build` to materialize the pipeline
> 4. Run the semantic view batch sync to create semantic views for all new marts
> 5. Deploy a Cortex Agent and register with Intelligence
>
> From raw Snowflake table to natural language querying — in one session.

---

## SLIDE 11: Real-World Example — Japan E-Commerce
**"Demo: From Question to Answer"**

### Speaker Notes:

> Let me walk through a concrete example. Our Japan e-commerce dataset has daily sales transactions with products, categories, and brands.
>
> *(Show or describe the flow)*
>
> **The mart table** (`fct_sales`) has columns like:
> - `sales_date` — when the transaction happened
> - `maker` — the brand (Apple, Samsung, etc.)
> - `item_category` — product type (Smartphone, Laptop, etc.)
> - `total_sales` — the revenue amount
> - `average_price` — average price per transaction
> - `transaction_count` — number of transactions
>
> **The semantic view** (`sem_revenue_analysis`) classifies:
> - `sales_date`, `maker`, `item_category` → **Dimensions** (filter/group by)
> - `total_sales`, `average_price`, `transaction_count` → **Metrics** (aggregate)
>
> **The Cortex Agent** can now answer:
>
> | Question | Generated SQL | Result |
> |----------|--------------|--------|
> | "Total revenue last month" | `SELECT SUM(total_sales) FROM fct_sales WHERE sales_date >= DATEADD('month', -1, CURRENT_DATE)` | ¥42,350,000 |
> | "Top 3 brands by sales" | `SELECT maker, SUM(total_sales) FROM fct_sales GROUP BY maker ORDER BY 2 DESC LIMIT 3` | Apple, Samsung, Sony |
> | "Monthly revenue trend for Smartphones" | `SELECT DATE_TRUNC('month', sales_date), SUM(total_sales) FROM fct_sales WHERE item_category = 'Smartphone' GROUP BY 1` | Time series chart |
>
> Every answer is **accurate** because it's grounded in the semantic view. Every answer is **governed** because it runs through Snowflake's access control. And every answer is **instantaneous** — no SQL writing, no dashboard building.

---

## SLIDE 12: Three Semantic Approaches
**"Flexibility: Choose What Fits Your Use Case"**

### Speaker Notes:

> I want to highlight that we support three complementary semantic approaches — because different use cases need different levels of richness.
>
> **Approach 1: Snowflake Semantic Views**
> - Best for: Single-mart analytics, straightforward dimension/metric classification
> - Complexity: Low — just dimensions, metrics, and verified queries
> - Integration: Native Snowflake object, used directly by Cortex Analyst
> - This is our **primary approach** and what I've been describing
>
> **Approach 2: Cortex Analyst YAML Semantic Models**
> - Best for: Complex multi-table relationships, rich business terminology
> - Richness: Synonyms (e.g., "brand" = "maker" = "manufacturer"), sample values, custom instructions
> - Use case: When the AI needs extra context — industry jargon, business-specific terminology
> - Uploaded to a Snowflake stage and referenced by `CORTEX_ANALYST_MESSAGE()`
>
> **Approach 3: dbt Semantic Layer (MetricFlow)**
> - Best for: Cross-platform metric consistency, governed metric definitions
> - Integration: Works with dbt Cloud, Tableau, Looker, and other BI tools
> - Use case: When you need the same metric definition across multiple consumption tools
>
> These three approaches **coexist**. For Novo Nordisk, I'd recommend starting with Snowflake Semantic Views for speed, then layering in YAML models for domains that need richer business terminology (like clinical trial data where synonyms matter).

---

## SLIDE 13: Value Proposition for Novo Nordisk
**"What This Means for Your Organization"**

### Speaker Notes:

> Let me bring this back to business value for Novo Nordisk.
>
> **For Business Users**:
> - Ask questions in English, get answers in seconds
> - No SQL training needed, no BI tool learning curve
> - Follow-up questions in the same conversation — "Now break that down by region"
> - Available in Snowsight — a tool your teams may already use
>
> **For Analytics Teams**:
> - Eliminate the "can you pull this data for me?" bottleneck
> - Focus on high-value analysis instead of ad-hoc query requests
> - Verified queries let you encode institutional knowledge once — then everyone benefits
> - Semantic views become living documentation of your data model
>
> **For Data Engineering**:
> - Automated source onboarding — any Snowflake table to NL-queryable in one session
> - 50 AI skills accelerate development by 10x
> - Quality gates ensure nothing ships without tests and documentation
> - Medallion architecture provides clear separation of raw, enriched, and analytical data
>
> **For IT/Governance**:
> - All queries run through Snowflake's native RBAC — no shadow analytics
> - Semantic views are Snowflake objects — auditable, version-controllable, manageable
> - Cortex Agents use the caller's role — data access policies are enforced
> - Full lineage from raw source to user-facing answer
>
> **For Leadership**:
> - Democratized data access across the organization
> - Faster time-to-decision
> - Reduced dependency on specialized SQL resources
> - Foundation for advanced AI use cases (predictive analytics, anomaly detection)

---

## SLIDE 14: Implementation Roadmap
**"How We Get From Here to There"**

### Speaker Notes:

> Here's what a realistic implementation roadmap looks like for Novo Nordisk:
>
> **Phase 1: Foundation (Weeks 1-2)**
> - Deploy the Snowflake dbt Starter Kit in your environment
> - Connect to your first priority data source
> - Run auto-discovery to generate the medallion pipeline
> - Build and test all models
>
> **Phase 2: Semantic Layer (Weeks 2-3)**
> - Create semantic views for all mart models
> - Define and validate verified queries with business SMEs
> - Run coverage audit to ensure no gaps
>
> **Phase 3: Agent Deployment (Week 3-4)**
> - Create Cortex Agents for each data domain
> - Test with real business questions
> - Refine verified queries based on accuracy feedback
> - Register with Snowflake Intelligence
>
> **Phase 4: Rollout (Weeks 4-6)**
> - Enable for pilot user group
> - Monitor question patterns and agent accuracy
> - Add verified queries for frequently asked questions
> - Onboard additional data sources
>
> **Phase 5: Scale (Ongoing)**
> - Self-service source onboarding by data teams
> - Expand to clinical, supply chain, financial data domains
> - Build domain-specific agents with specialized instructions
> - Layer in Cortex Analyst YAML for terminology-rich domains
>
> The beauty of this system is that each new data source follows the same pattern. Once the infrastructure is in place, onboarding is a matter of hours, not weeks.

---

## SLIDE 15: Closing & Call to Action
**"The Future of Analytics Is Conversational"**

### Speaker Notes:

> Let me leave you with this thought.
>
> We are at an inflection point in enterprise analytics. For 30 years, the model has been: *you need to learn the tool to get the answer*. SQL, dashboards, BI tools — they all require specialized skills.
>
> What we've built inverts that model. The data learns to speak your language. You ask in English. You get an answer. It's governed, it's accurate, and it's immediate.
>
> Snowflake's Semantic Views, Cortex Agents, and Intelligence platform make this real — not aspirational. And our implementation framework — the dbt pipeline, the automated semantic view generation, the 50 AI skills, the quality gates — makes it practical and repeatable.
>
> For Novo Nordisk, this means:
>
> - Every business analyst can query any authorized data source without writing SQL
> - Your analytics teams can focus on strategy, not ad-hoc requests
> - New data sources go from raw ingestion to natural language querying in a single session
> - The semantic layer becomes your organization's shared vocabulary for data
>
> I believe this is the future of enterprise analytics, and I'd love to show you a live demo or discuss how we can tailor this for your priority data domains.
>
> Thank you.

---

## Q&A PREPARATION — Common Questions & Answers

### Q: "How accurate is the AI-generated SQL?"
> With semantic views and verified queries, accuracy is very high — typically 85-95% for well-defined domains. The verified queries act as examples that ground the AI. For edge cases, the system returns "I'm not sure" rather than generating incorrect SQL. And accuracy improves over time as you add more verified queries.

### Q: "What about data security and access control?"
> Cortex Agents inherit the caller's Snowflake role. If a user doesn't have access to a table, the agent can't query it. Row-level security, column masking, and all Snowflake governance policies are enforced. The agent never bypasses access controls.

### Q: "Can this handle our clinical trial data?"
> Absolutely. The system is source-agnostic. Clinical trial data would go through the same medallion pipeline. For terminology-rich domains like clinical data, we'd layer in Cortex Analyst YAML models with synonyms (e.g., "adverse event" = "AE" = "side effect") to improve NL accuracy.

### Q: "How is this different from just building dashboards?"
> Dashboards answer the questions you've already anticipated. This answers questions you haven't thought of yet. A user can ask any question about the data — as long as the semantic view covers those dimensions and metrics. It's exploratory analytics without SQL.

### Q: "What's the maintenance burden?"
> The semantic views are generated from mart models — when marts change, the batch sync tool detects drift and regenerates. Verified queries need periodic curation (adding new ones, removing outdated ones), but the macro-based system makes this a YAML edit, not a manual DDL operation.

### Q: "Does this replace our BI tools?"
> No — it complements them. BI tools are still best for polished, publication-quality reports and complex visualizations. This handles the long tail of ad-hoc questions that never make it to a dashboard. Think of it as "the answer engine between the dashboards."

### Q: "How does this compare to ChatGPT/generic AI on our data?"
> Generic AI doesn't know your schema, your business logic, or your access controls. Cortex Analyst with semantic views has structured metadata about your exact tables, correct aggregation logic, and runs within Snowflake's security perimeter. It's purpose-built for your data, not general-purpose AI guessing at SQL.
