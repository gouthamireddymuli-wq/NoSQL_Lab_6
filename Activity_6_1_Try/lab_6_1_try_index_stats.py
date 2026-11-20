"""
Lab 6.1 – Try It Yourself: $indexStats Usage Analysis
======================================================
1. Runs each of the five representative queries multiple times so that
   MongoDB accumulates index-usage counters.
2. Uses the $indexStats aggregation stage to retrieve usage statistics
   for every index on the 'products' collection.
3. Identifies which indexes are used most frequently.

Prerequisites: Run lab_6_1_index_design.py first (creates the collection
               and indexes).
"""

import random
import time
from pymongo import MongoClient

# ── connection ───────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
client    = MongoClient(MONGO_URI)
db        = client["lab6_db"]
col       = db["products"]

# ── five representative queries (same as Lab 6.1) ───────────────────────────
QUERIES = [
    ("Q1 – Category filter + sort by price",
        {"category": "Electronics"},
        [("price", 1)]),

    ("Q2 – Price range filter",
        {"price": {"$gte": 50.0, "$lte": 200.0}},
        None),

    ("Q3 – Find by tag",
        {"tags": "sale"},
        None),

    ("Q4 – Category + rating range",
        {"category": "Books", "rating": {"$gte": 4.0}},
        None),

    ("Q5 – Low stock items",
        {"stock": {"$lt": 10}},
        [("price", -1)]),
]

RUNS_PER_QUERY = 20   # each query is executed this many times

def main():
    print("=" * 65)
    print("  Lab 6.1 Activity – $indexStats Usage Analysis")
    print("=" * 65)

    # Verify that the collection exists
    if col.count_documents({}) == 0:
        print("\n[ERROR] 'products' collection is empty.")
        print("        Please run lab_6_1_index_design.py first.\n")
        return

    print(f"\n[1] Running each query {RUNS_PER_QUERY}× to accumulate usage stats ...\n")
    for label, flt, srt in QUERIES:
        for _ in range(RUNS_PER_QUERY):
            cur = col.find(flt).limit(50)
            if srt:
                cur = cur.sort(srt)
            list(cur)          # fully consume the cursor
        print(f"    {label} – done ({RUNS_PER_QUERY} executions)")

    # ── $indexStats aggregation ───────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  [2] $indexStats – Index Usage Report")
    print("=" * 65)

    pipeline = [{"$indexStats": {}}]
    stats    = list(col.aggregate(pipeline))

    # Sort by ops descending
    stats.sort(key=lambda s: s.get("accesses", {}).get("ops", 0), reverse=True)

    print(f"\n  {'Index Name':<30} {'Key':<35} {'Ops (accesses)'}")
    print(f"  {'-'*30} {'-'*35} {'-'*14}")

    for s in stats:
        name = s.get("name", "?")
        key  = str(dict(s.get("key", {})))
        ops  = s.get("accesses", {}).get("ops", 0)
        print(f"  {name:<30} {key:<35} {ops}")

    # ── identify most / least used ────────────────────────────────────────
    if stats:
        most_used  = stats[0]
        least_used = stats[-1]
        print("\n" + "=" * 65)
        print("  [3] Analysis")
        print("=" * 65)
        print(f"\n  Most  used index : '{most_used['name']}'  "
              f"({most_used['accesses']['ops']} ops)")
        print(f"  Least used index : '{least_used['name']}'  "
              f"({least_used['accesses']['ops']} ops)")
        print()
        print("  Explanation:")
        print("  ─────────────────────────────────────────────────────")
        print("  Indexes with more 'ops' were chosen by the query")
        print("  planner more often for the executed queries.  Unused")
        print("  or rarely-used indexes waste RAM and slow down writes;")
        print("  they are candidates for removal.")

    print("\n" + "=" * 65)
    print("  Lab 6.1 Activity Complete")
    print("=" * 65)

if __name__ == "__main__":
    main()
