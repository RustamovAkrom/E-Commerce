import json
from pathlib import Path
from graphify.cache import check_semantic_cache

detect = json.loads(Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8"))
# only docs + images need semantic extraction (code handled by AST)
non_code = []
for k, v in detect["files"].items():
    if k == "code":
        continue
    non_code.extend(v)

cached_nodes, cached_edges, cached_hyperedges, uncached = check_semantic_cache(non_code)
if cached_nodes or cached_edges or cached_hyperedges:
    Path("graphify-out/.graphify_cached.json").write_text(
        json.dumps({"nodes": cached_nodes, "edges": cached_edges, "hyperedges": cached_hyperedges}, ensure_ascii=False),
        encoding="utf-8",
    )
Path("graphify-out/.graphify_uncached.txt").write_text("\n".join(uncached), encoding="utf-8")
print(f"non_code_total: {len(non_code)}  cache_hit: {len(non_code)-len(uncached)}  uncached: {len(uncached)}")
for u in uncached:
    print("UNCACHED:", u)
