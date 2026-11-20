from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017")
db = client["lab6_db"]

# 1. products sample (Lab 6.1)
docs = list(db["products"].find({}, {"_id": 0}).limit(20))
with open("Activity_6_1/products_sample.json", "w") as f:
    json.dump(docs, f, indent=2, default=str)
print("Activity_6_1/products_sample.json:", len(docs), "docs")

# 2. indexStats (Lab 6.1 Try)
stats = list(db["products"].aggregate([{"$indexStats": {}}]))
clean = []
for s in stats:
    entry = {}
    for k, v in s.items():
        if k == "_id":
            continue
        if hasattr(v, "items"):
            entry[k] = dict(v)
        else:
            entry[k] = v
    clean.append(entry)
with open("Activity_6_1_Try/index_stats_output.json", "w") as f:
    json.dump(clean, f, indent=2, default=str)
print("Activity_6_1_Try/index_stats_output.json written")

# 3. products_5_idx sample (Lab 6.2)
docs2 = list(db["products_5_idx"].find({}, {"_id": 0}).limit(20))
with open("Activity_6_2/products_5idx_sample.json", "w") as f:
    json.dump(docs2, f, indent=2, default=str)
print("Activity_6_2/products_5idx_sample.json:", len(docs2), "docs")

# 4. covered query result (Lab 6.2 Try)
result = list(
    db["products_covered"].find(
        {"category": "Electronics", "price": {"$lte": 300}},
        {"_id": 0, "category": 1, "price": 1, "rating": 1}
    ).limit(20)
)
with open("Activity_6_2_Try/covered_query_result.json", "w") as f:
    json.dump(result, f, indent=2, default=str)
print("Activity_6_2_Try/covered_query_result.json:", len(result), "docs")
