import json
import csv
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.csgraph import connected_components
from scipy.stats import rankdata
from sklearn.utils.extmath import randomized_svd
from threadpoolctl import threadpool_limits

def main():
    ids = np.loadtxt("db-export/Author.csv", dtype=np.int64, delimiter=",", usecols=0)
    edges = np.loadtxt("db-export/COAUTHOR_Author_Author.csv", dtype=np.int64, delimiter=",")
    vertex_row = {author: i for i, author in enumerate(ids)}
    u, v = np.array([[vertex_row[a], vertex_row[b]] for a, b in edges]).T
    n = len(ids)
    original = {tuple(sorted((int(ids[a]), int(ids[b])))) for a,b in zip(u,v)}
    prepared = {tuple(map(int,line.split(","))) for line in Path("coauthors.csv").read_text().splitlines()}
    assert original == prepared and len(original) == len(edges)
    assert set(ids) == {int(x) for x in Path("authors.csv").read_text().splitlines()}
    adjacency = csr_matrix((np.ones(2 * len(u)), (np.r_[u,v], np.r_[v,u])), shape=(n,n))
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    inv = np.divide(1., degree, out=np.zeros(n), where=degree > 0)
    transition = diags(inv) @ adjacency
    dangling = degree == 0
    rank = np.full(n, 1/n)
    for iterations in range(1, 1001):
        updated = .85 * (transition.T @ rank + rank[dangling].sum()/n) + .15/n
        residual = np.abs(rank - updated).sum()
        rank = updated
        if residual < 1e-12:
            break
    assert residual < 1e-12 and np.isclose(rank.sum(), 1)
    # Factor a symmetric matrix that sums one- and two-step normalized walks.
    scale = diags(np.sqrt(inv))
    normalized = scale @ adjacency @ scale
    context = normalized + normalized @ normalized
    left, sigma, _ = randomized_svd(context, n_components=32, n_iter=10, random_state=42)
    embedding = left * np.sqrt(sigma)
    norms = np.linalg.norm(embedding, axis=1)
    assert np.isfinite(embedding).all()
    unit = np.divide(embedding, norms[:,None], out=np.zeros_like(embedding), where=norms[:,None]>0)
    positive = (unit[u] * unit[v]).sum(axis=1)
    rng = np.random.default_rng(42)
    negative_pairs = set()
    while len(negative_pairs) < len(u):
        for a,b in rng.integers(n, size=(len(u), 2)):
            a,b = sorted((int(a),int(b)))
            if a != b and adjacency[a,b] == 0:
                negative_pairs.add((a,b))
            if len(negative_pairs) == len(u):
                break
    a,b = np.array(sorted(negative_pairs)).T
    negative = (unit[a] * unit[b]).sum(axis=1)
    scores = rankdata(np.r_[positive,negative])
    auc = (scores[:len(u)].sum() - len(u)*(len(u)+1)/2) / len(u)**2
    top = np.lexsort((ids, -rank))[:10]
    candidate = top[0]
    sim = unit @ unit[candidate]
    sim[candidate] = -np.inf
    closest = np.lexsort((ids,-sim))[:5]
    components, labels = connected_components(adjacency, directed=False)
    stats = dict(n=n, edges=len(u), residual=residual, iterations=iterations,
                 rank_sum=rank.sum(), components=components, largest=int(np.bincount(labels).max()),
                 top=[[int(ids[i]),float(rank[i]),int(degree[i])] for i in top],
                 positive=float(positive.mean()), negative=float(negative.mean()), auc=float(auc),
                 neighbors=[[int(ids[i]),float(sim[i]),bool(adjacency[candidate,i])] for i in closest],
                 zero_vectors=int((norms==0).sum()), dims=list(embedding.shape))
    Path("results.json").write_text(json.dumps(stats, indent=2))
    with open("scores.tsv","w") as f:
        for author, score, vector in zip(ids,rank,embedding):
            f.write(f"{author}\t{score:.17g}\t{','.join(format(x,'.17g') for x in vector)}\n")
    with open("authors-enriched.csv", "w", newline="") as f:
        writer = csv.writer(f)
        for author, score, vector in zip(ids, rank, embedding):
            writer.writerow([author, format(score, ".17g"), ",".join(format(x, ".17g") for x in vector)])
    config = json.loads(Path("import.json").read_text())
    config["files"][0].update(path="authors-enriched.csv", columns=["id", "pagerank", "embedding"])
    Path("enriched.json").write_text(json.dumps(config, indent=2))
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
