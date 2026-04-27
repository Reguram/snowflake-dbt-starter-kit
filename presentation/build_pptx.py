#!/usr/bin/env python3
"""
Generate the Novo Nordisk stakeholder presentation:
  "From Raw Data to Natural Language Answers — Intelligent Analytics on Snowflake"

Run: python presentation/build_pptx.py
Output: presentation/Novo_Nordisk_Snowflake_Intelligence.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ─── Brand Colors ───────────────────────────────────────────────────────────
SNOWFLAKE_BLUE   = RGBColor(0x29, 0xB5, 0xE8)   # #29B5E8
DARK_BLUE        = RGBColor(0x11, 0x27, 0x3F)    # #11273F
MED_BLUE         = RGBColor(0x1B, 0x3A, 0x5C)    # #1B3A5C
ACCENT_CYAN      = RGBColor(0x00, 0xD4, 0xFF)    # #00D4FF
ACCENT_GREEN     = RGBColor(0x2E, 0xCC, 0x71)    # #2ECC71
ACCENT_ORANGE    = RGBColor(0xF3, 0x9C, 0x12)    # #F39C12
ACCENT_RED       = RGBColor(0xE7, 0x4C, 0x3C)    # #E74C3C
WHITE            = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY       = RGBColor(0xEC, 0xF0, 0xF1)    # #ECF0F1
DARK_GRAY        = RGBColor(0x2C, 0x3E, 0x50)    # #2C3E50
NOVO_BLUE        = RGBColor(0x00, 0x1E, 0x62)    # Novo Nordisk brand blue
SLIDE_BG         = RGBColor(0xF8, 0xFA, 0xFC)    # Off-white background

SLIDE_WIDTH  = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def set_slide_bg(slide, color):
    """Set solid background color for a slide."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape(slide, left, top, width, height, fill_color, border_color=None, border_width=Pt(0)):
    """Add a rectangle shape with optional border."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = border_width
    else:
        shape.line.fill.background()
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color):
    """Add a rounded rectangle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=DARK_BLUE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    """Add a text box with styled text."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_bullet_list(slide, left, top, width, height, items, font_size=14,
                    color=DARK_GRAY, bold_first=False, spacing=Pt(6)):
    """Add a bulleted list."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.text = f"• {item}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = spacing

        if bold_first and ":" in item:
            # We can't easily bold part of the text, so just make the whole thing normal
            pass

    return txBox


def add_card(slide, left, top, width, height, title, body_lines, title_color=WHITE,
             body_color=WHITE, bg_color=MED_BLUE, title_size=16, body_size=12):
    """Add a card with title and bullet points."""
    card = add_rounded_rect(slide, left, top, width, height, bg_color)

    # Title
    add_text_box(slide, left + Inches(0.2), top + Inches(0.15),
                 width - Inches(0.4), Inches(0.4),
                 title, font_size=title_size, color=title_color, bold=True)

    # Body
    body_top = top + Inches(0.6)
    add_bullet_list(slide, left + Inches(0.2), body_top,
                    width - Inches(0.4), height - Inches(0.8),
                    body_lines, font_size=body_size, color=body_color)

    return card


def add_table(slide, left, top, width, rows_data, col_widths=None, header_color=DARK_BLUE):
    """Add a styled table."""
    rows = len(rows_data)
    cols = len(rows_data[0])
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, Inches(0.4 * rows))
    table = table_shape.table

    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w

    for r, row in enumerate(rows_data):
        for c, cell_text in enumerate(row):
            cell = table.cell(r, c)
            cell.text = cell_text
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)
                p.font.name = "Calibri"
                if r == 0:
                    p.font.bold = True
                    p.font.color.rgb = WHITE
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = header_color
                else:
                    p.font.color.rgb = DARK_GRAY
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = WHITE if r % 2 == 1 else LIGHT_GRAY

    return table_shape


# ═══════════════════════════════════════════════════════════════════════════
# SLIDES
# ═══════════════════════════════════════════════════════════════════════════

def slide_01_title(prs):
    """Title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    set_slide_bg(slide, DARK_BLUE)

    # Top accent bar
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), SNOWFLAKE_BLUE)

    # Title
    add_text_box(slide, Inches(1), Inches(1.5), Inches(11), Inches(1.2),
                 "From Raw Data to Natural Language Answers",
                 font_size=40, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Subtitle
    add_text_box(slide, Inches(1), Inches(2.8), Inches(11), Inches(0.8),
                 "Intelligent Analytics on Snowflake with Semantic Views, Cortex Agents & Snowflake Intelligence",
                 font_size=20, color=SNOWFLAKE_BLUE, bold=False, alignment=PP_ALIGN.CENTER)

    # Divider
    add_shape(slide, Inches(4.5), Inches(4.0), Inches(4), Inches(0.03), SNOWFLAKE_BLUE)

    # Presented to
    add_text_box(slide, Inches(1), Inches(4.4), Inches(11), Inches(0.5),
                 "Presented to Novo Nordisk",
                 font_size=22, color=LIGHT_GRAY, bold=False, alignment=PP_ALIGN.CENTER)

    # Date
    add_text_box(slide, Inches(1), Inches(5.0), Inches(11), Inches(0.5),
                 "April 2026",
                 font_size=16, color=LIGHT_GRAY, bold=False, alignment=PP_ALIGN.CENTER)

    # Bottom accent
    add_shape(slide, Inches(0), Inches(7.42), SLIDE_WIDTH, Inches(0.08), ACCENT_CYAN)


def slide_02_problem(prs):
    """The Analytics Bottleneck."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "The Analytics Bottleneck", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(1.1), Inches(11), Inches(0.5),
                 "Today's path from question to answer is too slow", font_size=16, color=DARK_GRAY)

    # The painful cycle - cards
    steps = [
        ("1. Question", "Business user has\na data question", ACCENT_RED),
        ("2. Request", "Files ticket to the\nanalytics team", ACCENT_ORANGE),
        ("3. Build", "Analyst writes SQL,\nbuilds dashboard", ACCENT_ORANGE),
        ("4. Review", '"Actually, I meant\nthis instead..."', ACCENT_RED),
        ("5. Iterate", "Rinse and repeat.\nDays → Weeks.", ACCENT_RED),
    ]

    for i, (title, body, color) in enumerate(steps):
        x = Inches(0.6 + i * 2.45)
        card = add_rounded_rect(slide, x, Inches(2.0), Inches(2.2), Inches(1.8), color)
        add_text_box(slide, x + Inches(0.15), Inches(2.1), Inches(1.9), Inches(0.4),
                     title, font_size=16, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.15), Inches(2.6), Inches(1.9), Inches(1.0),
                     body, font_size=13, color=WHITE, alignment=PP_ALIGN.CENTER)

    # Two problems
    add_card(slide, Inches(0.8), Inches(4.3), Inches(5.5), Inches(2.5),
             "The Cost of Waiting",
             [
                 "Analytics team becomes a bottleneck",
                 "Every question — no matter how simple — needs their time",
                 "By the time you get the answer, the moment has passed",
                 "In pharma, timely data = better decisions",
             ],
             bg_color=DARK_BLUE, body_size=13)

    add_card(slide, Inches(6.8), Inches(4.3), Inches(5.5), Inches(2.5),
             "The Vision",
             [
                 "Every authorized user asks data questions in English",
                 "Immediate, accurate, governed answers",
                 "No SQL knowledge required",
                 "Self-service analytics that actually works",
             ],
             bg_color=MED_BLUE, title_color=ACCENT_CYAN, body_size=13)


def slide_03_solution_overview(prs):
    """Three Layers of Intelligence."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Our Approach: Three Layers of Intelligence", font_size=32, color=DARK_BLUE, bold=True)

    layers = [
        {
            "title": "Layer 1: Medallion Data Architecture",
            "subtitle": "dbt-powered data engineering",
            "color": MED_BLUE,
            "items": [
                "Bronze (Staging) — Raw data, cleaned & renamed",
                "Silver (Intermediate) — Business logic, joins, enrichments",
                "Gold (Marts) — Consumption-ready facts & dimensions",
                "Automated tests at every layer: PK, FK, accepted values",
            ]
        },
        {
            "title": "Layer 2: Semantic Views",
            "subtitle": "Teaching Snowflake what the data means",
            "color": RGBColor(0x16, 0x50, 0x8C),
            "items": [
                "Native Snowflake objects on top of mart tables",
                "Dimensions — things you filter/group by (date, category, region)",
                "Metrics — things you aggregate (revenue, count, average)",
                "Verified Queries — known-good SQL examples for AI accuracy",
            ]
        },
        {
            "title": "Layer 3: Cortex Agents + Intelligence",
            "subtitle": "Making data conversational",
            "color": DARK_BLUE,
            "items": [
                "Cortex Agents convert natural language → SQL",
                "Read semantic views for dimension/metric understanding",
                "Snowflake Intelligence — org-wide NL querying in Snowsight",
                "Any authorized user types English, gets accurate answers",
            ]
        },
    ]

    for i, layer in enumerate(layers):
        y = Inches(1.3 + i * 2.0)
        add_card(slide, Inches(0.8), y, Inches(11.7), Inches(1.8),
                 layer["title"], layer["items"],
                 bg_color=layer["color"], title_size=18, body_size=13,
                 title_color=ACCENT_CYAN)

        # Subtitle badge
        add_text_box(slide, Inches(7), y + Inches(0.05), Inches(5), Inches(0.35),
                     layer["subtitle"], font_size=12, color=LIGHT_GRAY,
                     alignment=PP_ALIGN.RIGHT)


def slide_04_pipeline(prs):
    """End-to-End Pipeline."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.6),
                 "End-to-End Pipeline", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(0.9), Inches(11), Inches(0.4),
                 "Source → Models → Semantic Views → Agent → Intelligence → User Question → Answer",
                 font_size=14, color=DARK_GRAY)

    pipeline_steps = [
        ("Raw Data\nin Snowflake", "Any database\nany schema", RGBColor(0x95, 0xA5, 0xA6)),
        ("Auto-Discovery\n& Staging", "Profile tables\ngenerate models", MED_BLUE),
        ("dbt Build\n& Test", "Medallion layers\nquality gates", MED_BLUE),
        ("Semantic View\nGeneration", "Classify dims\n& metrics", RGBColor(0x16, 0x50, 0x8C)),
        ("Verified\nQueries", "Embed known-good\nSQL examples", RGBColor(0x16, 0x50, 0x8C)),
        ("Cortex Agent\nCreation", "Wire agent to\nsemantic view", DARK_BLUE),
        ("Snowflake\nIntelligence", "Org-wide NL\nquerying", DARK_BLUE),
    ]

    for i, (title, detail, color) in enumerate(pipeline_steps):
        x = Inches(0.3 + i * 1.82)
        y = Inches(1.6)

        # Step box
        add_rounded_rect(slide, x, y, Inches(1.65), Inches(1.4), color)
        add_text_box(slide, x + Inches(0.08), y + Inches(0.1), Inches(1.5), Inches(0.7),
                     title, font_size=13, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.08), y + Inches(0.75), Inches(1.5), Inches(0.55),
                     detail, font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

        # Arrow between steps
        if i < len(pipeline_steps) - 1:
            add_text_box(slide, x + Inches(1.6), y + Inches(0.45), Inches(0.25), Inches(0.4),
                         "→", font_size=20, color=SNOWFLAKE_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

        # Step number
        add_text_box(slide, x + Inches(0.6), y - Inches(0.35), Inches(0.5), Inches(0.35),
                     str(i + 1), font_size=14, color=SNOWFLAKE_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

    # Key metrics row
    metrics = [
        ("< 5 min", "Source Onboarding", ACCENT_GREEN),
        ("85-95%", "Query Accuracy", ACCENT_CYAN),
        ("100%", "Semantic Coverage", SNOWFLAKE_BLUE),
        ("0 SQL Required", "For Business Users", ACCENT_GREEN),
    ]

    for i, (value, label, color) in enumerate(metrics):
        x = Inches(0.8 + i * 3.1)
        y = Inches(3.5)
        add_rounded_rect(slide, x, y, Inches(2.7), Inches(1.1), DARK_BLUE)
        add_text_box(slide, x, y + Inches(0.1), Inches(2.7), Inches(0.5),
                     value, font_size=28, color=color, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x, y + Inches(0.65), Inches(2.7), Inches(0.35),
                     label, font_size=12, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Bottom details
    add_text_box(slide, Inches(0.8), Inches(5.0), Inches(12), Inches(0.4),
                 "Key Automation Capabilities", font_size=20, color=DARK_BLUE, bold=True)

    details = [
        ["Feature", "What It Does", "Impact"],
        ["Auto-Discovery Script", "Profiles any Snowflake table, generates staging + marts + tests", "Days → Minutes"],
        ["Semantic View Batch Sync", "Scans all marts, auto-classifies dims/metrics, generates DDL", "100% coverage"],
        ["Verified Query Post-Hook", "Embeds known-good SQL in semantic views via dbt build", "Improves AI accuracy"],
        ["One-Stop Agent", "Orchestrates entire pipeline: discover → build → semantic → deploy", "Single interface"],
    ]
    add_table(slide, Inches(0.8), Inches(5.5), Inches(11.7), details)


def slide_05_semantic_views(prs):
    """Semantic Views Deep Dive."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Semantic Views: The Key Innovation", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(1.0), Inches(11), Inches(0.5),
                 "Native Snowflake objects that describe your data in business terms",
                 font_size=16, color=DARK_GRAY)

    # Left: What a semantic view looks like
    add_card(slide, Inches(0.8), Inches(1.7), Inches(5.8), Inches(5.2),
             "Semantic View Structure (sem_revenue_analysis)",
             [
                 "TABLE: fct_sales",
                 "",
                 "DIMENSIONS (filter / group by):",
                 "  sales_date   → 'Date of transaction'",
                 "  maker        → 'Brand / manufacturer'",
                 "  item_category → 'Product category'",
                 "",
                 "METRICS (aggregate):",
                 "  total_revenue  = SUM(total_sales)",
                 "  avg_price      = AVG(average_price)",
                 "  order_count    = SUM(transaction_count)",
                 "",
                 "VERIFIED QUERIES:",
                 "  Q: 'Revenue by category?'",
                 "  SQL: SELECT item_category, SUM(total_sales)...",
             ],
             bg_color=DARK_BLUE, body_size=12, title_size=15)

    # Right: How Cortex reads it
    add_text_box(slide, Inches(7.2), Inches(1.7), Inches(5.5), Inches(0.4),
                 "How Cortex Analyst Uses It", font_size=18, color=DARK_BLUE, bold=True)

    qa_pairs = [
        ("User asks:", '"Show me Apple\'s revenue trend by month"', ACCENT_CYAN),
        ("AI maps:", '"Apple" → maker dimension\n"revenue" → total_revenue metric (SUM)\n"by month" → DATE_TRUNC(\'month\', sales_date)', SNOWFLAKE_BLUE),
        ("AI generates:", 'SELECT DATE_TRUNC(\'month\', sales_date),\n       SUM(total_sales)\nFROM fct_sales\nWHERE maker = \'Apple\'\nGROUP BY 1 ORDER BY 1', ACCENT_GREEN),
    ]

    for i, (label, text, color) in enumerate(qa_pairs):
        y = Inches(2.3 + i * 1.55)
        add_rounded_rect(slide, Inches(7.2), y, Inches(5.5), Inches(1.4), MED_BLUE)
        add_text_box(slide, Inches(7.4), y + Inches(0.08), Inches(2), Inches(0.3),
                     label, font_size=12, color=color, bold=True)
        add_text_box(slide, Inches(7.4), y + Inches(0.35), Inches(5.1), Inches(1.0),
                     text, font_size=11, color=WHITE)


def slide_06_verified_queries(prs):
    """Verified Queries."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Verified Queries: The Accuracy Feedback Loop", font_size=32, color=DARK_BLUE, bold=True)

    # Three pillars
    pillars = [
        ("Accuracy", "Known-good SQL examples\nguide the AI — like giving\na new analyst starter queries", ACCENT_GREEN),
        ("Governance", "Analytics team vets each\nquery — business logic\nis guaranteed correct", SNOWFLAKE_BLUE),
        ("Iterative Learning", "More questions → more verified\nqueries → smarter AI.\nThe system improves over time", ACCENT_CYAN),
    ]

    for i, (title, body, color) in enumerate(pillars):
        x = Inches(0.8 + i * 4.1)
        add_rounded_rect(slide, x, Inches(1.3), Inches(3.7), Inches(2.0), DARK_BLUE)
        add_text_box(slide, x + Inches(0.2), Inches(1.4), Inches(3.3), Inches(0.4),
                     title, font_size=20, color=color, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.2), Inches(1.9), Inches(3.3), Inches(1.2),
                     body, font_size=13, color=WHITE, alignment=PP_ALIGN.CENTER)

    # How it works
    add_text_box(slide, Inches(0.8), Inches(3.7), Inches(11), Inches(0.4),
                 "How Verified Queries Work", font_size=20, color=DARK_BLUE, bold=True)

    flow_data = [
        ["Step", "What Happens", "Who Does It"],
        ["1. Define", "Write verified query in schema.yml (question + SQL)", "Data Engineer"],
        ["2. Build", "dbt build runs post-hook macro → publishes to semantic view", "Automated (CI/CD)"],
        ["3. Query", "User asks similar question → AI references verified SQL as pattern", "Cortex Analyst"],
        ["4. Refine", "Monitor question patterns → add new verified queries for gaps", "Analytics Team"],
    ]
    add_table(slide, Inches(0.8), Inches(4.2), Inches(11.7), flow_data)

    # Example verified query
    add_card(slide, Inches(0.8), Inches(5.9), Inches(11.7), Inches(1.4),
             "Example Verified Query (in schema.yml)",
             [
                 'name: revenue_by_category',
                 'question: "What was total revenue by product category?"',
                 'sql: "SELECT item_category, SUM(total_sales) FROM t GROUP BY item_category ORDER BY 2 DESC"',
                 'verified_by: analytics_team  |  verified_at: 2026-04-24',
             ],
             bg_color=MED_BLUE, body_size=12, title_size=14)


def slide_07_agent_intelligence(prs):
    """From Semantic View to Agent to Intelligence."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "The Last Mile: Agent → Snowflake Intelligence", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(1.0), Inches(11), Inches(0.5),
                 "Making data conversational for every user in the organization",
                 font_size=16, color=DARK_GRAY)

    # Step 1: Create Agent
    add_card(slide, Inches(0.8), Inches(1.7), Inches(5.8), Inches(2.2),
             "Step 1: Create a Cortex Agent",
             [
                 "CREATE AGENT sales_analyst",
                 "  USING (",
                 "    cortex_analyst_text_to_sql(",
                 "      semantic_view => 'SEM_REVENUE_ANALYSIS'",
                 "    )",
                 "  );",
                 "",
                 "One SQL statement. Agent is live.",
             ],
             bg_color=DARK_BLUE, body_size=12)

    # Step 2: Register with Intelligence
    add_card(slide, Inches(7.0), Inches(1.7), Inches(5.8), Inches(2.2),
             "Step 2: Register with Snowflake Intelligence",
             [
                 "Agent appears in Snowsight sidebar",
                 "Available org-wide to authorized roles",
                 "Users click 'Ask a question' and type English",
                 "No BI tool, no SQL, no analytics ticket",
                 "",
                 "Copenhagen, Tokyo, New Jersey — same experience",
             ],
             bg_color=MED_BLUE, body_size=12)

    # User experience flow
    add_text_box(slide, Inches(0.8), Inches(4.3), Inches(11), Inches(0.4),
                 "The End-User Experience", font_size=20, color=DARK_BLUE, bold=True)

    ux_steps = [
        ("User Types", '"Top 5 products\nby revenue\nlast quarter?"', ACCENT_CYAN),
        ("Agent Reads", "Semantic view:\ndims, metrics,\nverified queries", SNOWFLAKE_BLUE),
        ("Agent Generates", "SELECT product,\nSUM(revenue)\n...GROUP BY 1\nLIMIT 5", ACCENT_GREEN),
        ("User Sees", "Instant table\nwith results +\nfollow-up chat", ACCENT_GREEN),
    ]

    for i, (title, detail, color) in enumerate(ux_steps):
        x = Inches(0.8 + i * 3.1)
        add_rounded_rect(slide, x, Inches(4.9), Inches(2.8), Inches(2.2), DARK_BLUE)
        add_text_box(slide, x + Inches(0.1), Inches(4.95), Inches(2.6), Inches(0.35),
                     title, font_size=15, color=color, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(5.4), Inches(2.6), Inches(1.5),
                     detail, font_size=12, color=WHITE, alignment=PP_ALIGN.CENTER)

        if i < len(ux_steps) - 1:
            add_text_box(slide, x + Inches(2.75), Inches(5.7), Inches(0.4), Inches(0.4),
                         "→", font_size=22, color=SNOWFLAKE_BLUE, bold=True)


def slide_08_ai_skills(prs):
    """50 AI Skills & MCP Server."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "AI-Powered Development: 50 Skills + MCP Server", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(1.0), Inches(11), Inches(0.4),
                 "How we build and maintain the platform 10x faster",
                 font_size=16, color=DARK_GRAY)

    # Left: Skills
    add_card(slide, Inches(0.8), Inches(1.6), Inches(6), Inches(3.0),
             "50 AI Agent Skills (Auto-Activating)",
             [
                 "17 dbt/custom skills: model gen, semantic views, code review",
                 "33 bundled Snowflake skills: Cortex AI, ML, governance, Iceberg",
                 "Auto-activate based on file being edited",
                 "Work across Claude Code, GitHub Copilot, Cortex Code",
                 "",
                 "Key skills for this pipeline:",
                 "  • snowflake-semantic-view-creator",
                 "  • cortex-analyst-semantic-model",
                 "  • semantic-view-batch-sync",
                 "  • dbt-one-stop-agent",
             ],
             bg_color=DARK_BLUE, body_size=12)

    # Right: MCP Server
    add_card(slide, Inches(7.2), Inches(1.6), Inches(5.5), Inches(3.0),
             "MCP Server (Model Context Protocol)",
             [
                 "Gives AI assistants direct Snowflake access",
                 "",
                 "Tools available:",
                 "  • generate_dbt_model — scaffold staging models",
                 "  • generate_semantic_view — create semantic DDL",
                 "  • run_dbt_command — build, test, compile",
                 "  • review_sql — static analysis for best practices",
                 "  • check_data_quality — run tests + pass/fail",
                 "  • deploy_agent — create & register agents",
             ],
             bg_color=MED_BLUE, body_size=12)

    # Bottom: What this means
    add_text_box(slide, Inches(0.8), Inches(5.0), Inches(11), Inches(0.4),
                 "Development Acceleration", font_size=20, color=DARK_BLUE, bold=True)

    accel_data = [
        ["Task", "Traditional", "With AI Skills + MCP", "Speedup"],
        ["Onboard new source", "2-3 days", "< 30 minutes", "50x"],
        ["Create semantic view", "4-6 hours", "< 10 minutes", "30x"],
        ["Full code review", "1-2 hours", "< 5 minutes", "20x"],
        ["Deploy Cortex Agent", "1-2 hours", "< 5 minutes", "20x"],
        ["End-to-end pipeline", "1-2 weeks", "1-2 hours", "40x"],
    ]
    add_table(slide, Inches(0.8), Inches(5.5), Inches(11.7), accel_data)


def slide_09_governance(prs):
    """Governance & Quality Gates."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Enterprise Governance & Quality Gates", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(1.0), Inches(11), Inches(0.4),
                 "Every pipeline is tested, documented, and access-controlled",
                 font_size=16, color=DARK_GRAY)

    pillars = [
        {
            "title": "Automated Testing",
            "items": [
                "Primary key: unique + not_null",
                "Foreign keys: relationships tests",
                "Data quality: accepted_values, ranges",
                "Source freshness monitoring",
            ],
            "color": ACCENT_GREEN,
        },
        {
            "title": "Documentation",
            "items": [
                "Every model described in schema.yml",
                "Every column documented",
                "Semantic views = living data dictionary",
                "Verified queries = institutional knowledge",
            ],
            "color": SNOWFLAKE_BLUE,
        },
        {
            "title": "Quality Audits",
            "items": [
                "Project-wide quality scan skill",
                "Semantic view coverage audit",
                "Missing tests detection",
                "SELECT * and hard-coded schema alerts",
            ],
            "color": ACCENT_ORANGE,
        },
        {
            "title": "Access Control",
            "items": [
                "Snowflake native RBAC enforced",
                "Agents inherit caller's role",
                "Row-level & column-level security",
                "Full audit trail: source → answer",
            ],
            "color": ACCENT_CYAN,
        },
    ]

    for i, pillar in enumerate(pillars):
        x = Inches(0.5 + i * 3.15)
        add_rounded_rect(slide, x, Inches(1.7), Inches(2.9), Inches(3.2), DARK_BLUE)
        add_text_box(slide, x + Inches(0.15), Inches(1.8), Inches(2.6), Inches(0.4),
                     pillar["title"], font_size=17, color=pillar["color"],
                     bold=True, alignment=PP_ALIGN.CENTER)
        add_bullet_list(slide, x + Inches(0.15), Inches(2.3), Inches(2.6), Inches(2.4),
                        pillar["items"], font_size=11, color=WHITE, spacing=Pt(4))

    # Bottom: pharma relevance
    add_card(slide, Inches(0.8), Inches(5.3), Inches(11.7), Inches(1.6),
             "Why This Matters for Pharma",
             [
                 "Regulatory compliance requires data lineage and auditability — every query traceable to source",
                 "Column masking and row-level security ensure sensitive data is protected, even through NL queries",
                 "Verified queries encode approved business logic — no ad-hoc misinterpretation of metrics",
                 "Semantic views provide a governed vocabulary — 'revenue' means the same thing across the organization",
             ],
             bg_color=MED_BLUE, body_size=12, title_size=15)


def slide_10_multi_source(prs):
    """Multi-Source Architecture."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Source-Agnostic: Any Data, Same Pipeline", font_size=32, color=DARK_BLUE, bold=True)

    # Reference implementation sources
    sources_data = [
        ["Data Domain", "Tables", "Models", "Semantic Views", "Use Case"],
        ["COVID-19 Epidemiological", "10+", "30+", "8", "Public health analytics"],
        ["Japan E-Commerce Sales", "3", "7", "2", "Revenue & product performance"],
        ["US Census Data", "5", "10", "2", "Demographic & geographic analysis"],
        ["Company Registry", "2", "3", "1", "Company & country analytics"],
    ]
    add_table(slide, Inches(0.8), Inches(1.3), Inches(11.7), sources_data)

    # Onboarding steps
    add_text_box(slide, Inches(0.8), Inches(3.5), Inches(11), Inches(0.4),
                 "New Source Onboarding — 5 Steps, One Session", font_size=20, color=DARK_BLUE, bold=True)

    steps = [
        ("1", "Discover", "Run auto-discovery\nscript on any\nSnowflake schema"),
        ("2", "Build", "dbt build materializes\nstaging → intermediate\n→ marts"),
        ("3", "Semantic", "Batch sync creates\nsemantic views for\nall new marts"),
        ("4", "Agent", "Deploy Cortex Agent\nlinked to semantic\nview"),
        ("5", "Intelligence", "Register agent for\norg-wide NL\nquerying"),
    ]

    for i, (num, title, detail) in enumerate(steps):
        x = Inches(0.5 + i * 2.5)
        add_rounded_rect(slide, x, Inches(4.1), Inches(2.2), Inches(2.0), DARK_BLUE)
        # Number circle
        add_text_box(slide, x + Inches(0.8), Inches(4.15), Inches(0.6), Inches(0.4),
                     num, font_size=22, color=ACCENT_CYAN, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(4.55), Inches(2.0), Inches(0.35),
                     title, font_size=16, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(4.95), Inches(2.0), Inches(1.0),
                     detail, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Novo Nordisk callout
    add_card(slide, Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.9),
             "For Novo Nordisk",
             ["Same pipeline applies to clinical trial data, supply chain, financials, manufacturing — any Snowflake-hosted data"],
             bg_color=NOVO_BLUE, body_size=13, title_size=15, title_color=ACCENT_CYAN)


def slide_11_demo(prs):
    """Real-World Example."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Live Example: Japan E-Commerce → Natural Language", font_size=32, color=DARK_BLUE, bold=True)

    # Mart table
    add_text_box(slide, Inches(0.8), Inches(1.2), Inches(5), Inches(0.4),
                 "Gold Mart: fct_sales", font_size=18, color=DARK_BLUE, bold=True)

    mart_data = [
        ["Column", "Type", "Classification"],
        ["sales_date", "DATE", "Time Dimension"],
        ["maker", "VARCHAR", "Categorical Dimension"],
        ["item_category", "VARCHAR", "Categorical Dimension"],
        ["total_sales", "NUMBER", "Metric (SUM)"],
        ["average_price", "NUMBER", "Metric (AVG)"],
        ["transaction_count", "NUMBER", "Metric (SUM)"],
    ]
    add_table(slide, Inches(0.8), Inches(1.7), Inches(5.5), mart_data)

    # Questions & Answers
    add_text_box(slide, Inches(7), Inches(1.2), Inches(5.5), Inches(0.4),
                 "Natural Language → SQL → Answer", font_size=18, color=DARK_BLUE, bold=True)

    qa = [
        ('"Total revenue last month"', "¥42.3M"),
        ('"Top 3 brands by sales"', "Apple, Samsung, Sony"),
        ('"Monthly trend for Smartphones"', "Time series: Jan→Dec"),
        ('"Compare Q1 vs Q2 by category"', "Pivot table with delta"),
    ]

    for i, (question, answer) in enumerate(qa):
        y = Inches(1.8 + i * 1.0)
        add_rounded_rect(slide, Inches(7), y, Inches(5.5), Inches(0.85), DARK_BLUE)
        add_text_box(slide, Inches(7.15), y + Inches(0.05), Inches(3.5), Inches(0.35),
                     question, font_size=12, color=ACCENT_CYAN, bold=True)
        add_text_box(slide, Inches(7.15), y + Inches(0.42), Inches(3.5), Inches(0.35),
                     f"→ {answer}", font_size=12, color=ACCENT_GREEN)

    # Key points
    add_card(slide, Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.5),
             "What Makes This Work",
             [
                 "Accurate — grounded in semantic view metadata, not AI guessing at column names",
                 "Governed — runs through Snowflake RBAC, users only see data they're authorized for",
                 "Instantaneous — no SQL writing, no dashboard building, no analytics ticket",
                 "Conversational — user can ask follow-up questions in the same session",
             ],
             bg_color=MED_BLUE, body_size=13, title_size=15)


def slide_12_three_approaches(prs):
    """Three Semantic Approaches."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Three Semantic Approaches — Choose What Fits", font_size=32, color=DARK_BLUE, bold=True)

    approaches = [
        ["Feature", "Snowflake Semantic Views", "Cortex Analyst YAML", "dbt Semantic Layer"],
        ["Best For", "Single-mart analytics", "Complex multi-table", "Cross-platform metrics"],
        ["Richness", "Dimensions + Metrics", "Synonyms, sample values,\nverified queries", "Governed metric definitions"],
        ["Integration", "Native Snowflake object", "YAML file on stage", "dbt Cloud, Tableau, Looker"],
        ["AI Accuracy", "Good (with verified queries)", "Excellent (rich metadata)", "N/A (not NL-focused)"],
        ["Setup Effort", "Low (auto-classified)", "Medium (agentic profiling)", "High (MetricFlow config)"],
        ["Recommended", "✅ PRIMARY approach", "For terminology-rich domains", "For BI tool consistency"],
    ]
    add_table(slide, Inches(0.8), Inches(1.3), Inches(11.7), approaches)

    # Recommendation
    add_card(slide, Inches(0.8), Inches(4.5), Inches(11.7), Inches(2.5),
             "Recommendation for Novo Nordisk",
             [
                 "Start with Snowflake Semantic Views — fastest path, native integration, auto-classified columns",
                 "Layer in Cortex Analyst YAML for clinical/scientific data where terminology matters",
                 "  → Synonyms map business jargon: 'adverse event' = 'AE' = 'side effect'",
                 "  → Sample values help AI understand valid inputs for categorical filters",
                 "  → Custom instructions encode domain-specific query rules",
                 "Use dbt Semantic Layer if you need the same metric definitions in Tableau/Looker/Power BI",
                 "",
                 "All three approaches coexist in this platform — mix and match per data domain",
             ],
             bg_color=DARK_BLUE, body_size=13, title_size=16, title_color=ACCENT_CYAN)


def slide_13_value(prs):
    """Value Proposition for Novo Nordisk."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Value for Novo Nordisk", font_size=32, color=DARK_BLUE, bold=True)

    stakeholders = [
        {
            "title": "Business Users",
            "items": [
                "Ask questions in English",
                "Get answers in seconds",
                "No SQL training needed",
                "Follow-up in same session",
            ],
            "color": ACCENT_GREEN,
        },
        {
            "title": "Analytics Teams",
            "items": [
                "Eliminate ad-hoc bottleneck",
                "Focus on high-value analysis",
                "Encode knowledge in verified queries",
                "Semantic views = living docs",
            ],
            "color": SNOWFLAKE_BLUE,
        },
        {
            "title": "Data Engineering",
            "items": [
                "Automated source onboarding",
                "50 AI skills for 10x velocity",
                "Quality gates ensure reliability",
                "Clear medallion architecture",
            ],
            "color": ACCENT_CYAN,
        },
        {
            "title": "IT / Governance",
            "items": [
                "Native RBAC — no shadow analytics",
                "Auditable Snowflake objects",
                "Agent inherits caller's role",
                "Full lineage: source → answer",
            ],
            "color": ACCENT_ORANGE,
        },
    ]

    for i, s in enumerate(stakeholders):
        x = Inches(0.5 + i * 3.15)
        add_rounded_rect(slide, x, Inches(1.3), Inches(2.9), Inches(3.0), DARK_BLUE)
        add_text_box(slide, x + Inches(0.15), Inches(1.4), Inches(2.6), Inches(0.4),
                     s["title"], font_size=17, color=s["color"],
                     bold=True, alignment=PP_ALIGN.CENTER)
        add_bullet_list(slide, x + Inches(0.15), Inches(1.9), Inches(2.6), Inches(2.2),
                        s["items"], font_size=12, color=WHITE, spacing=Pt(5))

    # Leadership summary
    add_card(slide, Inches(0.8), Inches(4.7), Inches(11.7), Inches(2.3),
             "For Leadership",
             [
                 "Democratized data access — every authorized user can query any data source in English",
                 "Faster time-to-decision — answers in seconds, not days",
                 "Reduced dependency on specialized SQL resources",
                 "Foundation for advanced AI: predictive analytics, anomaly detection, clinical trial insights",
                 "Scalable model — each new data source follows the same automated pipeline",
             ],
             bg_color=NOVO_BLUE, body_size=14, title_size=18, title_color=WHITE)


def slide_14_roadmap(prs):
    """Implementation Roadmap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, SLIDE_BG)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.6),
                 "Implementation Roadmap", font_size=32, color=DARK_BLUE, bold=True)

    phases = [
        ("Phase 1\nWeeks 1-2", "Foundation", [
            "Deploy starter kit in your environment",
            "Connect to first priority data source",
            "Run auto-discovery & generate models",
            "dbt build + test all pipelines",
        ], ACCENT_GREEN),
        ("Phase 2\nWeeks 2-3", "Semantic Layer", [
            "Create semantic views for all marts",
            "Define verified queries with SMEs",
            "Run coverage audit — ensure no gaps",
        ], SNOWFLAKE_BLUE),
        ("Phase 3\nWeeks 3-4", "Agent Deploy", [
            "Create Cortex Agents per domain",
            "Test with real business questions",
            "Refine verified queries from feedback",
            "Register with Snowflake Intelligence",
        ], ACCENT_CYAN),
        ("Phase 4\nWeeks 4-6", "Pilot Rollout", [
            "Enable for pilot user group",
            "Monitor question patterns & accuracy",
            "Add verified queries for common Qs",
            "Onboard additional data sources",
        ], ACCENT_ORANGE),
        ("Phase 5\nOngoing", "Scale", [
            "Self-service source onboarding",
            "Clinical, supply chain, financial data",
            "Domain-specific agent instructions",
            "YAML models for terminology-rich domains",
        ], ACCENT_GREEN),
    ]

    for i, (period, title, items, color) in enumerate(phases):
        x = Inches(0.3 + i * 2.55)
        # Phase header
        add_rounded_rect(slide, x, Inches(1.3), Inches(2.3), Inches(0.9), color)
        add_text_box(slide, x + Inches(0.1), Inches(1.35), Inches(2.1), Inches(0.4),
                     title, font_size=16, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(1.75), Inches(2.1), Inches(0.35),
                     period, font_size=10, color=WHITE, alignment=PP_ALIGN.CENTER)

        # Items
        add_rounded_rect(slide, x, Inches(2.35), Inches(2.3), Inches(2.5), DARK_BLUE)
        add_bullet_list(slide, x + Inches(0.1), Inches(2.45), Inches(2.1), Inches(2.3),
                        items, font_size=10, color=WHITE, spacing=Pt(3))

        # Connector
        if i < len(phases) - 1:
            add_text_box(slide, x + Inches(2.25), Inches(1.6), Inches(0.35), Inches(0.4),
                         "→", font_size=18, color=DARK_GRAY, bold=True)

    # Key message
    add_card(slide, Inches(0.8), Inches(5.3), Inches(11.7), Inches(1.8),
             "Why This Timeline Works",
             [
                 "Infrastructure is pre-built — the Snowflake dbt Starter Kit is production-ready",
                 "Auto-discovery eliminates manual data modeling — new sources onboard in minutes, not days",
                 "Each phase delivers incremental value — you don't wait 6 weeks for the first result",
                 "The platform is self-reinforcing — more verified queries = better AI accuracy over time",
             ],
             bg_color=MED_BLUE, body_size=13, title_size=15)


def slide_15_closing(prs):
    """Closing slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, DARK_BLUE)

    # Top accent
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), SNOWFLAKE_BLUE)

    add_text_box(slide, Inches(1), Inches(1.2), Inches(11), Inches(1.0),
                 "The Future of Analytics Is Conversational",
                 font_size=38, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Divider
    add_shape(slide, Inches(4.5), Inches(2.5), Inches(4), Inches(0.03), SNOWFLAKE_BLUE)

    # Key takeaways
    takeaways = [
        "Data learns to speak your language — ask in English, get accurate answers",
        "Semantic views + verified queries = governed, accurate text-to-SQL",
        "Snowflake Intelligence makes it organization-wide with one registration",
        "Automated pipeline: raw table → NL-queryable in a single session",
        "Production-grade: tested, documented, access-controlled, auditable",
    ]
    add_bullet_list(slide, Inches(2), Inches(3.0), Inches(9), Inches(2.5),
                    takeaways, font_size=16, color=LIGHT_GRAY, spacing=Pt(12))

    # CTA
    add_text_box(slide, Inches(1), Inches(5.8), Inches(11), Inches(0.5),
                 "Let's discuss how to apply this to your priority data domains",
                 font_size=18, color=ACCENT_CYAN, bold=False, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(1), Inches(6.5), Inches(11), Inches(0.5),
                 "Thank You",
                 font_size=28, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Bottom accent
    add_shape(slide, Inches(0), Inches(7.42), SLIDE_WIDTH, Inches(0.08), ACCENT_CYAN)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    slide_01_title(prs)
    slide_02_problem(prs)
    slide_03_solution_overview(prs)
    slide_04_pipeline(prs)
    slide_05_semantic_views(prs)
    slide_06_verified_queries(prs)
    slide_07_agent_intelligence(prs)
    slide_08_ai_skills(prs)
    slide_09_governance(prs)
    slide_10_multi_source(prs)
    slide_11_demo(prs)
    slide_12_three_approaches(prs)
    slide_13_value(prs)
    slide_14_roadmap(prs)
    slide_15_closing(prs)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "Novo_Nordisk_Snowflake_Intelligence.pptx")
    prs.save(out_path)
    print(f"✅ Presentation saved to: {out_path}")
    print(f"   {len(prs.slides)} slides generated")


if __name__ == "__main__":
    main()
