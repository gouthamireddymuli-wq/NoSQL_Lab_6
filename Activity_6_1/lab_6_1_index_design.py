"""
Lab 6.1 – Index Design for a Query Workload
============================================
1. Creates a 'products' collection with 50,000 generated documents.
   Fields: name, category, price, rating, stock, tags (array).
2. Runs explain() on five representative queries BEFORE indexes.
3. Creates a covering set of indexes.
4. Runs explain() on the same five queries AFTER indexes.
5. Compares before-vs-after (stage, totalDocsExamined, totalKeysExamined).
"""

import random
import time
from pymongo import MongoClient

# ── connection ───────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
client    = MongoClient(MONGO_URI)
db        = client["lab6_db"]
col       = db["products"]

# ── data generation helpers ──────────────────────────────────────────────────
CATEGORIES = ["Electronics", "Clothing", "Books", "Home", "Sports",
               "Toys", "Beauty", "Automotive", "Garden", "Food"]
TAG_POOL   = ["sale", "new", "top-rated", "clearance", "limited",
               "eco-friendly", "bestseller", "imported", "organic", "premium"]

def random_product(i: int) -> dict:
    return {
        "name":     f"Product_{i:05d} {random.choice(['Pro','Lite','Max','Ultra','Basic'])}",
        "category": random.choice(CATEGORIES),
        "price":    round(random.uniform(1.99, 999.99), 2),
        "rating":   round(random.uniform(1.0, 5.0), 1),
        "stock":    random.randint(0, 500),
        "tags":     random.sample(TAG_POOL, k=random.randint(1, 4)),
    }

# ── explain helper ───────────────────────────────────────────────────────────
def run_explain(query, sort=None, label="Query"):
    cursor = col.find(query)
    if sort:
        cursor = cursor.sort(sort)
    plan  = cursor.explain()
    qp    = plan["queryPlanner"]
    es    = plan.get("executionStats", {})
    stage = qp["winningPlan"].get("stage", "?")

    # Walk the plan tree looking for IXSCAN
    def walk(node):
        if node is None:
            return []
        names = []
        if node.get("stage") == "IXSCAN":
            names.append(node.get("indexName", "?"))
        for key in ("inputStage", "innerStage", "outerStage"):
            names += walk(node.get(key))
        for child in node.get("inputStages", []):
            names += walk(child)
        return names

    index_names = walk(qp["winningPlan"])

    print(f"\n  [{label}]")
    print(f"    Query         : {query}  sort={sort}")
    print(f"    Stage         : {stage}")
    print(f"    Index(es) used: {index_names if index_names else 'none (COLLSCAN)'}")
    print(f"    docsExamined  : {es.get('totalDocsExamined', 'N/A')}")
    print(f"    keysExamined  : {es.get('totalKeysExamined', 'N/A')}")
    print(f"    nReturned     : {es.get('nReturned', 'N/A')}")

    return {
        "label":          label,
        "stage":          stage,
        "indexes":        index_names,
        "docsExamined":   es.get("totalDocsExamined", -1),
        "keysExamined":   es.get("totalKeysExamined", -1),
        "nReturned":      es.get("nReturned", -1),
    }

# ── five representative queries ──────────────────────────────────────────────
QUERIES = [
    # (label, filter_dict, sort_list_or_None)
    ("Q1 – Category filter + sort by price",
        {"category": "Electronics"},
        [("price", 1)]),

    ("Q2 – Price range filter",
        {"price": {"$gte": 50.0, "$lte": 200.0}},
        None),

    ("Q3 – Find by tag (array field)",
        {"tags": "sale"},
        None),

    ("Q4 – Category + rating range",
        {"category": "Books", "rating": {"$gte": 4.0}},
        None),

    ("Q5 – Low stock items",
        {"stock": {"$lt": 10}},
        [("price", -1)]),
]

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  Lab 6.1 – Index Design for a Query Workload")
    print("=" * 65)

    # 1. Reset & insert 50,000 products
    col.drop()
    print("\n[1] Generating and inserting 50,000 product documents ...")
    t0   = time.perf_counter()
    batch = [random_product(i) for i in range(50_000)]
    col.insert_many(batch, ordered=False)
    t1   = time.perf_counter()
    print(f"    Inserted {col.count_documents({}):,} docs in {t1-t0:.2f}s")

    # 2. BEFORE – run explain on all five queries
    print("\n" + "=" * 65)
    print("  EXPLAIN – BEFORE Creating Indexes (COLLSCAN expected)")
    print("=" * 65)
    before = []
    for label, flt, srt in QUERIES:
        before.append(run_explain(flt, srt, label))

    # 3. Create indexes covering all five queries
    print("\n" + "=" * 65)
    print("  Creating Indexes")
    print("=" * 65)
    # Q1 – compound: category + price
    col.create_index([("category", 1), ("price", 1)],  name="idx_category_price")
    print("  [+] idx_category_price     on (category, price)")
    # Q2 – single: price
    col.create_index([("price", 1)],                   name="idx_price")
    print("  [+] idx_price              on (price)")
    # Q3 – multikey: tags
    col.create_index([("tags", 1)],                    name="idx_tags")
    print("  [+] idx_tags               on (tags)")
    # Q4 – compound: category + rating
    col.create_index([("category", 1), ("rating", -1)],name="idx_category_rating")
    print("  [+] idx_category_rating    on (category, rating)")
    # Q5 – compound: stock + price
    col.create_index([("stock", 1), ("price", -1)],    name="idx_stock_price")
    print("  [+] idx_stock_price        on (stock, price)")

    # 4. AFTER – run explain again
    print("\n" + "=" * 65)
    print("  EXPLAIN – AFTER Creating Indexes (IXSCAN expected)")
    print("=" * 65)
    after = []
    for label, flt, srt in QUERIES:
        after.append(run_explain(flt, srt, label))

    # 5. Comparison table
    print("\n" + "=" * 65)
    print("  Before vs After Comparison")
    print("=" * 65)
    print(f"  {'Query':<40} {'Before Stage':<12} {'Before Docs':<13} {'After Stage':<12} {'After Docs'}")
    print(f"  {'-'*40} {'-'*12} {'-'*13} {'-'*12} {'-'*10}")
    for b, a in zip(before, after):
        print(f"  {b['label'][:40]:<40} {b['stage']:<12} {b['docsExamined']:<13} {a['stage']:<12} {a['docsExamined']}")

    # 6. List all indexes
    print("\n" + "=" * 65)
    print("  Final Index List")
    print("=" * 65)
    for idx in col.list_indexes():
        print(f"  {idx['name']:<30} keys={dict(idx['key'])}")

    print("\n" + "=" * 65)
    print("  Lab 6.1 Complete")
    print("=" * 65)

if __name__ == "__main__":
    main()
