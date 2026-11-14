import gzip
import json
import hashlib
from pathlib import Path

source = Path("ca-HepTh.txt.gz")
with gzip.open(source, "rt") as f:
    raw = [tuple(map(int, line.split())) for line in f if not line.startswith("#") and line.strip()]
ids = sorted({v for edge in raw for v in edge})
pairs = sorted({tuple(sorted((u,v))) for u,v in raw if u != v})
Path("authors.csv").write_text("".join(f"{i}\n" for i in ids))
Path("coauthors.csv").write_text("".join(f"{u},{v}\n" for u,v in pairs))
Path("import.json").write_text(json.dumps({
 "schema": [
  {"label":"Author","type":"VERTEX","primary":"id","properties":[
   {"name":"id","type":"INT64"},
   {"name":"pagerank","type":"DOUBLE","optional":True},
   {"name":"embedding","type":"STRING","optional":True}]},
  {"label":"COAUTHOR","type":"EDGE","constraints":[["Author","Author"]]}],
 "files":[
  {"path":"authors.csv","format":"CSV","label":"Author","columns":["id"]},
  {"path":"coauthors.csv","format":"CSV","label":"COAUTHOR",
   "SRC_ID":"Author","DST_ID":"Author","columns":["SRC_ID","DST_ID"]}]
}, indent=2))
stats = dict(raw=len(raw), loops=sum(u==v for u,v in raw), nodes=len(ids),
             edges=len(pairs), sha256=hashlib.sha256(source.read_bytes()).hexdigest())
Path("data-summary.json").write_text(json.dumps(stats, indent=2))
print(stats)
