"""
Lab 6.2 – Try It Yourself: Covered Queries
===========================================
A COVERED QUERY is one where:
  • all query predicate fields are in an index, AND
  • all projected (returned) fields are also in the same index.

MongoDB can then satisfy the query entirely from the index B-tree,
skipping the FETCH stage (no document reads from the collection).

This script:
  1. Creates a compound index on (category, price, rating).
  2. Runs a NON-covered query  → FETCH stage present.
  3. Runs a COVERED query       → FETCH stage absent, only IXSCAN.
  4. Verifies via explain() and prints side-by-side comparison.
"""

import random
from pymongo import MongoClient

# ── connection ───────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
client    = MongoClient(MONGO_URI)
db        = client["lab6_db"]
col       = db["products_covered"]

# ── data generation ──────────────────────────────────────────────────────────
CATEGORIES = ["Electronics", "Clothing", "Books", "Home", "Sports",
               "Toys", "Beauty", "Automotive", "Garden", "Food"]
TAG_POOL   = ["sale", "new", "top-rated", "clearance", "limited",
               "eco-friendly", "bestseller", "imported", "organic", "premium"]

def random_product(i: int) -> dict:
    return {
        "name":     f"Product_{i:05d}",
        "category": random.choice(CATEGORIES),
        "price":    round(random.uniform(1.99, 999.99), 2),
        "rating":   round(random.uniform(1.0, 5.0), 1),
        "stock":    random.randint(0, 500),
        "tags":     random.sample(TAG_POOL, k=random.randint(1, 4)),
    }

# ── explain helper ───────────────────────────────────────────────────────────
def collect_stages(node, stages=None):
    """Recursively collect all stage names from a query plan tree."""
    if stages is None:
        stages = []
    if node is None:
        return stages
    stages.append(node.get("stage", ""))
    for key in ("inputStage", "innerStage", "outerStage"):
        collect_stages(node.get(key), stages)
    for child in node.get("inputStages", []):
        collect_stages(child, stages)
    return stages

def run_explain(cursor, label):
    plan   = cursor.explain()
    qp     = plan["queryPlanner"]
    es     = plan.get("executionStats", {})
    stages = collect_stages(qp["winningPlan"])

    has_fetch  = "FETCH"  in stages
    has_ixscan = "IXSCAN" in stages

    # Find index name(s)
    def find_index(node):
        if node is None:
            return []
        names = []
        if node.get("stage") == "IXSCAN":
            names.append(node.get("indexName", "?"))
        for key in ("inputStage", "innerStage", "outerStage"):
            names += find_index(node.get(key))
        for child in node.get("inputStages", []):
            names += find_index(child)
        return names

    index_names = find_index(qp["winningPlan"])

    print(f"\n  [{label}]")
    print(f"    Stages         : {' → '.join(s for s in stages if s)}")
    print(f"    IXSCAN used    : {'YES' if has_ixscan else 'NO'}")
    print(f"    FETCH stage    : {'YES (not covered)' if has_fetch else 'NO  ← COVERED QUERY!'}")
    print(f"    Index name(s)  : {index_names}")
    print(f"    docsExamined   : {es.get('totalDocsExamined', 'N/A')}")
    print(f"    keysExamined   : {es.get('totalKeysExamined', 'N/A')}")
    print(f"    nReturned      : {es.get('nReturned', 'N/A')}")

    return has_fetch, has_ixscan, es.get("totalDocsExamined", -1)

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  Lab 6.2 Activity – Covered Queries")
    print("=" * 65)

    # 1. Prepare collection
    col.drop()
    print("\n[1] Inserting 10,000 product documents ...")
    docs = [random_product(i) for i in range(10_000)]
    col.insert_many(docs, ordered=False)
    print(f"    Inserted {col.count_documents({}):,} documents.")

    # 2. Create compound index on (category, price, rating)
    #    _id is excluded from projection to allow full coverage
    print("\n[2] Creating compound index on (category, price, rating) ...")
    col.create_index(
        [("category", 1), ("price", 1), ("rating", -1)],
        name="idx_covered_cat_price_rating"
    )
    print("    Index 'idx_covered_cat_price_rating' created.")

    # ── Common query predicate ────────────────────────────────────────────
    query_filter = {"category": "Electronics", "price": {"$lte": 300.0}}

    # 3. NON-COVERED query (returns all fields including _id, name, stock, tags)
    print("\n" + "=" * 65)
    print("  [3] NON-COVERED Query (full document fetch)")
    print("=" * 65)
    print("  Filter  : {category: 'Electronics', price: {$lte: 300}}")
    print("  Project : {} (all fields – includes non-indexed fields)")

    nc_cursor = col.find(query_filter).limit(0)
    nc_fetch, nc_ixscan, nc_docs = run_explain(nc_cursor, "Non-covered")

    # 4. COVERED query (project only indexed fields; exclude _id)
    print("\n" + "=" * 65)
    print("  [4] COVERED Query (index-only, no document fetch)")
    print("=" * 65)
    print("  Filter  : {category: 'Electronics', price: {$lte: 300}}")
    print("  Project : {_id:0, category:1, price:1, rating:1}  ← only indexed fields")

    cov_cursor = col.find(
        query_filter,
        {"_id": 0, "category": 1, "price": 1, "rating": 1}
    ).limit(0)
    cov_fetch, cov_ixscan, cov_docs = run_explain(cov_cursor, "Covered")

    # 5. Summary
    print("\n" + "=" * 65)
    print("  [5] Summary")
    print("=" * 65)
    print(f"\n  {'Metric':<30} {'Non-Covered':>14} {'Covered':>14}")
    print(f"  {'-'*30} {'-'*14} {'-'*14}")
    print(f"  {'FETCH stage present':<30} {'YES':>14} {'NO':>14}")
    print(f"  {'IXSCAN used':<30} {'YES' if nc_ixscan else 'NO':>14} {'YES' if cov_ixscan else 'NO':>14}")
    print(f"  {'Documents examined':<30} {nc_docs:>14} {cov_docs:>14}")

    print("""
  Explanation
  ───────────────────────────────────────────────────────────
  • Non-covered query: even though an index is used (IXSCAN),
    MongoDB still performs a FETCH stage to read the full
    document from the collection (to return unindexed fields
    like 'name', 'stock', 'tags').

  • Covered query: the projection requests ONLY fields that are
    present in the index (category, price, rating) and excludes
    _id.  MongoDB satisfies the entire query from the B-tree
    alone — no FETCH, zero documents read from the collection.

  • Covered queries are ideal for high-frequency, latency-
    sensitive read patterns where you only need a subset of
    fields that can all be placed inside a single compound index.
""")

    print("=" * 65)
    print("  Lab 6.2 Activity Complete")
    print("=" * 65)

if __name__ == "__main__":
    main()
