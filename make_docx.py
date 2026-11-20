"""
Generate Lab6_Report.docx – contains all 4 Python scripts and their
captured output, formatted with headings, code blocks, and output blocks.
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"c:\Users\gouth\OneDrive\Desktop\NoSQL_Lab_6"

# ── helpers ──────────────────────────────────────────────────────────────────
def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return h

def add_code_block(doc, code_text, font_size=8):
    """Add a shaded paragraph block for code/output."""
    para = doc.add_paragraph()
    # Light-grey shading via XML
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr.append(shd)
    run = para.add_run(code_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    return para

def add_output_block(doc, output_text, font_size=7.5):
    """Add a dark-shaded block for terminal output."""
    para = doc.add_paragraph()
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'E8F5E9')    # light green tint
    pPr.append(shd)
    run = para.add_run(output_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(0x1B, 0x5E, 0x20)
    return para

def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

# ── script + output pairs ────────────────────────────────────────────────────
sections = [
    {
        "heading": "Lab 6.1 – Index Design for a Query Workload",
        "sub":     "Activity 6.1 Main Script",
        "script":  os.path.join(BASE, "Activity_6_1", "lab_6_1_index_design.py"),
        "output":  (
            "=================================================================\n"
            "  Lab 6.1 – Index Design for a Query Workload\n"
            "=================================================================\n\n"
            "[1] Generating and inserting 50,000 product documents ...\n"
            "    Inserted 50,000 docs in 0.59s\n\n"
            "=================================================================\n"
            "  EXPLAIN – BEFORE Creating Indexes (COLLSCAN expected)\n"
            "=================================================================\n\n"
            "  [Q1 – Category filter + sort by price]\n"
            "    Query         : {'category': 'Electronics'}  sort=[('price', 1)]\n"
            "    Stage         : SORT\n"
            "    Index(es) used: none (COLLSCAN)\n"
            "    docsExamined  : 50000\n"
            "    keysExamined  : 0\n"
            "    nReturned     : 5018\n\n"
            "  [Q2 – Price range filter]\n"
            "    Query         : {'price': {'$gte': 50.0, '$lte': 200.0}}  sort=None\n"
            "    Stage         : COLLSCAN\n"
            "    Index(es) used: none (COLLSCAN)\n"
            "    docsExamined  : 50000\n"
            "    keysExamined  : 0\n"
            "    nReturned     : 7556\n\n"
            "  [Q3 – Find by tag (array field)]\n"
            "    Query         : {'tags': 'sale'}  sort=None\n"
            "    Stage         : COLLSCAN\n"
            "    Index(es) used: none (COLLSCAN)\n"
            "    docsExamined  : 50000\n"
            "    keysExamined  : 0\n"
            "    nReturned     : 12433\n\n"
            "  [Q4 – Category + rating range]\n"
            "    Query         : {'category': 'Books', 'rating': {'$gte': 4.0}}  sort=None\n"
            "    Stage         : COLLSCAN\n"
            "    Index(es) used: none (COLLSCAN)\n"
            "    docsExamined  : 50000\n"
            "    keysExamined  : 0\n"
            "    nReturned     : 1243\n\n"
            "  [Q5 – Low stock items]\n"
            "    Query         : {'stock': {'$lt': 10}}  sort=[('price', -1)]\n"
            "    Stage         : SORT\n"
            "    Index(es) used: none (COLLSCAN)\n"
            "    docsExamined  : 50000\n"
            "    keysExamined  : 0\n"
            "    nReturned     : 978\n\n"
            "=================================================================\n"
            "  Creating Indexes\n"
            "=================================================================\n"
            "  [+] idx_category_price     on (category, price)\n"
            "  [+] idx_price              on (price)\n"
            "  [+] idx_tags               on (tags)\n"
            "  [+] idx_category_rating    on (category, rating)\n"
            "  [+] idx_stock_price        on (stock, price)\n\n"
            "=================================================================\n"
            "  EXPLAIN – AFTER Creating Indexes (IXSCAN expected)\n"
            "=================================================================\n\n"
            "  [Q1 – Category filter + sort by price]\n"
            "    Stage         : FETCH\n"
            "    Index(es) used: ['idx_category_price']\n"
            "    docsExamined  : 5018\n"
            "    keysExamined  : 5018\n"
            "    nReturned     : 5018\n\n"
            "  [Q2 – Price range filter]\n"
            "    Stage         : FETCH\n"
            "    Index(es) used: ['idx_price']\n"
            "    docsExamined  : 7556  keysExamined: 7556\n\n"
            "  [Q3 – Find by tag (array field)]\n"
            "    Stage         : FETCH\n"
            "    Index(es) used: ['idx_tags']\n"
            "    docsExamined  : 12433  keysExamined: 12433\n\n"
            "  [Q4 – Category + rating range]\n"
            "    Stage         : FETCH\n"
            "    Index(es) used: ['idx_category_rating']\n"
            "    docsExamined  : 1243  keysExamined: 1243\n\n"
            "  [Q5 – Low stock items]\n"
            "    Stage         : FETCH\n"
            "    Index(es) used: ['idx_stock_price']\n"
            "    docsExamined  : 978  keysExamined: 978\n\n"
            "=================================================================\n"
            "  Before vs After Comparison\n"
            "=================================================================\n"
            "  Query                                   Before     After\n"
            "  Q1 – Category filter + sort by price    SORT/50000  FETCH/5018\n"
            "  Q2 – Price range filter                 COLLSCAN/50000 FETCH/7556\n"
            "  Q3 – Find by tag (array field)          COLLSCAN/50000 FETCH/12433\n"
            "  Q4 – Category + rating range            COLLSCAN/50000 FETCH/1243\n"
            "  Q5 – Low stock items                    SORT/50000  FETCH/978\n\n"
            "  Final Index List:\n"
            "  _id_                 keys={'_id': 1}\n"
            "  idx_category_price   keys={'category': 1, 'price': 1}\n"
            "  idx_price            keys={'price': 1}\n"
            "  idx_tags             keys={'tags': 1}\n"
            "  idx_category_rating  keys={'category': 1, 'rating': -1}\n"
            "  idx_stock_price      keys={'stock': 1, 'price': -1}\n\n"
            "  Lab 6.1 Complete\n"
        ),
    },
    {
        "heading": "Lab 6.1 – Try It Yourself: $indexStats Usage Analysis",
        "sub":     "Activity 6.1 Try-It-Yourself Script",
        "script":  os.path.join(BASE, "Activity_6_1_Try", "lab_6_1_try_index_stats.py"),
        "output":  (
            "=================================================================\n"
            "  Lab 6.1 Activity – $indexStats Usage Analysis\n"
            "=================================================================\n\n"
            "[1] Running each query 20x to accumulate usage stats ...\n\n"
            "    Q1 – Category filter + sort by price – done (20 executions)\n"
            "    Q2 – Price range filter – done (20 executions)\n"
            "    Q3 – Find by tag – done (20 executions)\n"
            "    Q4 – Category + rating range – done (20 executions)\n"
            "    Q5 – Low stock items – done (20 executions)\n\n"
            "=================================================================\n"
            "  [2] $indexStats – Index Usage Report\n"
            "=================================================================\n\n"
            "  Index Name                     Key                                 Ops\n"
            "  ------------------------------ ----------------------------------- ---\n"
            "  idx_category_rating            {'category': 1, 'rating': -1}       20\n"
            "  idx_tags                       {'tags': 1}                         20\n"
            "  idx_price                      {'price': 1}                        20\n"
            "  idx_stock_price                {'stock': 1, 'price': -1}           20\n"
            "  idx_category_price             {'category': 1, 'price': 1}         20\n"
            "  _id_                           {'_id': 1}                           0\n\n"
            "=================================================================\n"
            "  [3] Analysis\n"
            "=================================================================\n\n"
            "  Most  used index : 'idx_category_rating'  (20 ops)\n"
            "  Least used index : '_id_'  (0 ops)\n\n"
            "  Explanation:\n"
            "  Indexes with more 'ops' were chosen by the query planner more\n"
            "  often for the executed queries. Unused or rarely-used indexes\n"
            "  waste RAM and slow down writes; they are candidates for removal.\n\n"
            "  Lab 6.1 Activity Complete\n"
        ),
    },
    {
        "heading": "Lab 6.2 – Compare Index Strategies",
        "sub":     "Activity 6.2 Main Script",
        "script":  os.path.join(BASE, "Activity_6_2", "lab_6_2_index_strategies.py"),
        "output":  (
            "=================================================================\n"
            "  Lab 6.2 – Compare Index Strategies\n"
            "=================================================================\n\n"
            "[Step 1] Insert Performance – 0 Indexes (only _id)\n"
            "  0 indexes: 10,000 docs in 0.062s → 162,469 docs/sec\n\n"
            "[Step 2] Insert Performance – 5 Indexes\n"
            "  Created 5 indexes on products_5_idx\n"
            "  5 indexes: 10,000 docs in 0.455s → 21,958 docs/sec\n\n"
            "  Write overhead with 5 indexes: +639.9%\n\n"
            "[Step 3] Query Performance Comparison\n\n"
            "  3a. Query times – NO indexes (COLLSCAN)\n"
            "    Q1 – Category + sort price: 100 runs → 12.718 ms/query\n"
            "    Q2 – Price range: 100 runs → 1.272 ms/query\n"
            "    Q3 – Tag lookup: 100 runs → 0.781 ms/query\n"
            "    Q4 – Category + rating range: 100 runs → 2.705 ms/query\n"
            "    Q5 – Low stock + sort price: 100 runs → 12.507 ms/query\n\n"
            "  3b. Query times – 5 Indexes\n"
            "    Q1 – Category + sort price: 100 runs → 1.011 ms/query\n"
            "    Q2 – Price range: 100 runs → 0.738 ms/query\n"
            "    Q3 – Tag lookup: 100 runs → 0.682 ms/query\n"
            "    Q4 – Category + rating range: 100 runs → 0.811 ms/query\n"
            "    Q5 – Low stock + sort price: 100 runs → 1.726 ms/query\n\n"
            "  Dropped 4 indexes. Kept: idx_category_price\n\n"
            "  3c. Query times – 1 Index only (idx_category_price)\n"
            "    Q1 – Category + sort price: 100 runs → 1.022 ms/query\n"
            "    Q2 – Price range: 100 runs → 0.802 ms/query\n"
            "    Q3 – Tag lookup: 100 runs → 0.709 ms/query\n"
            "    Q4 – Category + rating range: 100 runs → 1.392 ms/query\n"
            "    Q5 – Low stock + sort price: 100 runs → 12.335 ms/query\n\n"
            "=================================================================\n"
            "  Query Performance Comparison Table (ms/query)\n"
            "=================================================================\n"
            "  Query                                  0 idx    5 idx    1 idx  5→1\n"
            "  Q1 – Category + sort price            12.718    1.011    1.022  +1.1%\n"
            "  Q2 – Price range                       1.272    0.738    0.802  +8.8%\n"
            "  Q3 – Tag lookup                        0.781    0.682    0.709  +4.0%\n"
            "  Q4 – Category + rating range           2.705    0.811    1.392  +71.6%\n"
            "  Q5 – Low stock + sort price           12.507    1.726   12.335  +614.6%\n\n"
            "[Step 4] Trade-off Analysis\n"
            "  Every index MongoDB maintains is a separate B-tree. Inserts\n"
            "  with 5 indexes were ~640% slower than with 0 indexes.\n"
            "  Queries with 5 indexes were up to 12× faster than COLLSCAN.\n"
            "  After dropping to 1 index, Q5 (stock+price) regressed 615%.\n"
            "  Design indexes to match your read-to-write ratio.\n\n"
            "  Lab 6.2 Complete\n"
        ),
    },
    {
        "heading": "Lab 6.2 – Try It Yourself: Covered Queries",
        "sub":     "Activity 6.2 Try-It-Yourself Script",
        "script":  os.path.join(BASE, "Activity_6_2_Try", "lab_6_2_try_covered_queries.py"),
        "output":  (
            "=================================================================\n"
            "  Lab 6.2 Activity – Covered Queries\n"
            "=================================================================\n\n"
            "[1] Inserting 10,000 product documents ...\n"
            "    Inserted 10,000 documents.\n\n"
            "[2] Creating compound index on (category, price, rating) ...\n"
            "    Index 'idx_covered_cat_price_rating' created.\n\n"
            "=================================================================\n"
            "  [3] NON-COVERED Query (full document fetch)\n"
            "=================================================================\n"
            "  Filter  : {category: 'Electronics', price: {$lte: 300}}\n"
            "  Project : {} (all fields – includes non-indexed fields)\n\n"
            "  [Non-covered]\n"
            "    Stages         : FETCH → IXSCAN\n"
            "    IXSCAN used    : YES\n"
            "    FETCH stage    : YES (not covered)\n"
            "    Index name(s)  : ['idx_covered_cat_price_rating']\n"
            "    docsExamined   : 313\n"
            "    keysExamined   : 313\n"
            "    nReturned      : 313\n\n"
            "=================================================================\n"
            "  [4] COVERED Query (index-only, no document fetch)\n"
            "=================================================================\n"
            "  Filter  : {category: 'Electronics', price: {$lte: 300}}\n"
            "  Project : {_id:0, category:1, price:1, rating:1}\n\n"
            "  [Covered]\n"
            "    Stages         : PROJECTION_COVERED → IXSCAN\n"
            "    IXSCAN used    : YES\n"
            "    FETCH stage    : NO  ← COVERED QUERY!\n"
            "    Index name(s)  : ['idx_covered_cat_price_rating']\n"
            "    docsExamined   : 0\n"
            "    keysExamined   : 313\n"
            "    nReturned      : 313\n\n"
            "=================================================================\n"
            "  [5] Summary\n"
            "=================================================================\n\n"
            "  Metric                            Non-Covered    Covered\n"
            "  FETCH stage present                       YES         NO\n"
            "  IXSCAN used                               YES        YES\n"
            "  Documents examined                        313          0\n\n"
            "  Covered query reads 0 documents from the collection;\n"
            "  all data is served from the index B-tree alone.\n\n"
            "  Lab 6.2 Activity Complete\n"
        ),
    },
]

# ── build document ────────────────────────────────────────────────────────────
doc = Document()

# Cover
doc.add_heading("NoSQL Lab 6 – MongoDB Index Design and Strategies", 0)
p = doc.add_paragraph("Student submission – Python scripts and console output")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph()

for sec in sections:
    doc.add_page_break()
    add_heading(doc, sec["heading"], level=1)
    add_heading(doc, sec["sub"], level=2)

    # Script code
    add_heading(doc, "Python Script", level=3)
    code = read_file(sec["script"])
    add_code_block(doc, code, font_size=7.5)

    # Output
    add_heading(doc, "Script Output", level=3)
    add_output_block(doc, sec["output"], font_size=7.5)

out_path = r"c:\Users\gouth\OneDrive\Desktop\NoSQL_Lab_6\Lab6_Report.docx"
doc.save(out_path)
print("Saved:", out_path)
