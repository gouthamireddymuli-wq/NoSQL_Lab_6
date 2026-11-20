"""
Lab 6.2 – Compare Index Strategies
====================================
1. Measures insert time for 10,000 docs with ZERO indexes.
2. Creates 5 indexes, inserts another 10,000 docs, measures time again.
   Calculates percentage slowdown.
3. Drops all but the most critical index.
   Re-runs the five representative queries and compares performance.
4. Prints a written analysis of the write-throughput vs query-performance
   trade-off.
"""

import random
import time
from pymongo import MongoClient, ASCENDING, DESCENDING

# ── connection ───────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
client    = MongoClient(MONGO_URI)
db        = client["lab6_db"]

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

def gen_batch(n: int, offset: int = 0):
    return [random_product(offset + i) for i in range(n)]

# ── timing helpers ───────────────────────────────────────────────────────────
def timed_insert(col, docs, label):
    t0 = time.perf_counter()
    col.insert_many(docs, ordered=False)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    rate    = len(docs) / elapsed
    print(f"  {label}: {len(docs):,} docs in {elapsed:.3f}s → {rate:,.0f} docs/sec")
    return elapsed

def timed_query(col, flt, srt, iters, label):
    t0 = time.perf_counter()
    for _ in range(iters):
        cur = col.find(flt).limit(50)
        if srt:
            cur = cur.sort(srt)
        list(cur)
    t1 = time.perf_counter()
    elapsed  = t1 - t0
    per_q_ms = (elapsed / iters) * 1000
    print(f"    {label}: {iters} runs → {per_q_ms:.3f} ms/query")
    return per_q_ms

# ── five representative queries ──────────────────────────────────────────────
QUERIES = [
    ("Q1 – Category + sort price",    {"category": "Electronics"}, [("price", 1)]),
    ("Q2 – Price range",              {"price": {"$gte": 50.0, "$lte": 200.0}}, None),
    ("Q3 – Tag lookup",               {"tags": "sale"}, None),
    ("Q4 – Category + rating range",  {"category": "Books", "rating": {"$gte": 4.0}}, None),
    ("Q5 – Low stock + sort price",   {"stock": {"$lt": 10}}, [("price", -1)]),
]
ITERS = 100

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  Lab 6.2 – Compare Index Strategies")
    print("=" * 65)

    # ── STEP 1: Insert 10,000 docs with ZERO indexes ──────────────────────
    print("\n[Step 1] Insert Performance – 0 Indexes (only _id)")
    col_a = db["products_no_idx"]
    col_a.drop()
    # _id index is always present; no additional indexes
    docs_a = gen_batch(10_000, offset=0)
    t_no_idx = timed_insert(col_a, docs_a, "0 indexes")

    # ── STEP 2: Create 5 indexes, insert 10,000 more docs ────────────────
    print("\n[Step 2] Insert Performance – 5 Indexes")
    col_b = db["products_5_idx"]
    col_b.drop()

    col_b.create_index([("category", 1), ("price", 1)],   name="idx_category_price")
    col_b.create_index([("price", 1)],                    name="idx_price")
    col_b.create_index([("tags", 1)],                     name="idx_tags")
    col_b.create_index([("category", 1), ("rating", -1)], name="idx_category_rating")
    col_b.create_index([("stock", 1), ("price", -1)],     name="idx_stock_price")
    print("  Created 5 indexes on products_5_idx")

    docs_b = gen_batch(10_000, offset=10_000)
    t_5_idx = timed_insert(col_b, docs_b, "5 indexes")

    overhead = ((t_5_idx - t_no_idx) / t_no_idx) * 100
    print(f"\n  Write overhead with 5 indexes: {overhead:+.1f}%")

    # ── STEP 3: Drop all but most critical index; compare query perf ──────
    print("\n[Step 3] Query Performance Comparison")

    # Need a shared dataset – use col_b (which has 10,000 docs + 5 indexes)
    # We'll also re-seed col_a with the same data for a fair COLLSCAN comparison
    col_a.drop()
    col_a.insert_many(docs_b, ordered=False)   # same 10,000 docs, 0 extra indexes

    print("\n  3a. Query times – NO indexes (COLLSCAN)")
    no_idx_times = []
    for label, flt, srt in QUERIES:
        ms = timed_query(col_a, flt, srt, ITERS, label)
        no_idx_times.append(ms)

    print("\n  3b. Query times – 5 Indexes")
    five_idx_times = []
    for label, flt, srt in QUERIES:
        ms = timed_query(col_b, flt, srt, ITERS, label)
        five_idx_times.append(ms)

    # Drop 4 of 5 indexes – keep only the most general one
    for idx in ["idx_price", "idx_tags", "idx_category_rating", "idx_stock_price"]:
        col_b.drop_index(idx)
    print("\n  Dropped 4 indexes. Kept: idx_category_price")

    print("\n  3c. Query times – 1 Index only (idx_category_price)")
    one_idx_times = []
    for label, flt, srt in QUERIES:
        ms = timed_query(col_b, flt, srt, ITERS, label)
        one_idx_times.append(ms)

    # ── Comparison table ──────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  Query Performance Comparison Table (ms/query)")
    print("=" * 65)
    print(f"  {'Query':<35} {'0 idx':>8} {'5 idx':>8} {'1 idx':>8}  {'5→1 Change'}")
    print(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*8}  {'-'*10}")
    for i, (label, _, _) in enumerate(QUERIES):
        chg = ((one_idx_times[i] - five_idx_times[i]) / five_idx_times[i]) * 100
        sign = "+" if chg >= 0 else ""
        print(f"  {label[:35]:<35} {no_idx_times[i]:>8.3f} {five_idx_times[i]:>8.3f} {one_idx_times[i]:>8.3f}  {sign}{chg:.1f}%")

    # ── STEP 4: Written analysis ──────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  [Step 4] Trade-off Analysis")
    print("=" * 65)
    analysis = """
  WRITE THROUGHPUT vs QUERY PERFORMANCE – Trade-off Analysis
  ───────────────────────────────────────────────────────────

  Every index MongoDB maintains is a separate B-tree data structure.
  When a document is inserted, updated, or deleted, MongoDB must
  update EVERY index that covers any of the modified fields.

  Observations from this experiment
  ──────────────────────────────────
  • 0 indexes: fastest writes (only _id B-tree is updated).
  • 5 indexes: writes are noticeably slower because each insert
    must write to 6 B-trees (_id + 5 custom).
  • Query time with 5 indexes is drastically lower than with 0
    indexes because the planner can use an IXSCAN instead of a
    full COLLSCAN, examining only the matching keys.
  • After dropping to 1 index, queries that used the dropped
    indexes fall back to COLLSCAN and slow down significantly,
    while queries that still use the surviving index remain fast.

  Practical guidelines
  ─────────────────────
  1. Index only fields that appear in frequent, expensive queries.
  2. Use compound indexes (ESR rule: Equality → Sort → Range) to
     cover multiple query patterns with fewer indexes.
  3. For write-heavy workloads (IoT, logging), minimise index count
     on the hot collection; move analytics to a secondary or replica.
  4. Monitor actual usage with $indexStats and drop indexes whose
     ops counter stays near zero – they impose write cost with no
     read benefit.
  5. Consider partial indexes (e.g., {stock: {$lt: 10}}) to index
     only the subset of documents actually queried, reducing both
     storage and write overhead.
"""
    print(analysis)

    print("=" * 65)
    print("  Lab 6.2 Complete")
    print("=" * 65)


if __name__ == "__main__":
    main()
