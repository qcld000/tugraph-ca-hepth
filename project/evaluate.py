import json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, diags
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.utils.extmath import randomized_svd
from threadpoolctl import threadpool_limits

def trial(ids, pairs, seed):
    n = len(ids)
    lookup = {author:i for i,author in enumerate(ids)}
    indexed = np.array([[lookup[u],lookup[v]] for u,v in pairs])
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(pairs))
    k = len(pairs)//5
    test, train = indexed[perm[:k]], indexed[perm[k:]]
    u,v = train.T
    A = csr_matrix((np.ones(2*len(train)), (np.r_[u,v],np.r_[v,u])), shape=(n,n))
    deg = np.asarray(A.sum(axis=1)).ravel()
    norm = np.divide(1,np.sqrt(deg),out=np.zeros(n),where=deg>0)
    S = diags(norm) @ A @ diags(norm)
    all_edges = {tuple(sorted(edge)) for edge in indexed}
    negatives = set()
    while len(negatives) < k:
        left,right = sorted(rng.integers(n,size=2))
        if left != right and (left,right) not in all_edges:
            negatives.add((left,right))
    a,b = np.vstack([test,np.array(sorted(negatives))]).T
    truth = np.r_[np.ones(k),np.zeros(k)]
    def metrics(score):
        return [float(roc_auc_score(truth,score)),float(average_precision_score(truth,score))]
    intersections = np.asarray(A[a].multiply(A[b]).sum(axis=1)).ravel()
    cn = metrics(intersections)
    jaccard = metrics(np.divide(intersections,deg[a]+deg[b]-intersections,
                               out=np.zeros_like(intersections),where=deg[a]+deg[b]-intersections>0))
    two_hop = S + S@S
    embeddings = {}
    for dim in (16,32,64):
        U, sig, _ = randomized_svd(two_hop,n_components=dim,n_iter=10,random_state=seed)
        z = U*np.sqrt(sig)
        length = np.linalg.norm(z,axis=1)
        z = np.divide(z,length[:,None],out=np.zeros_like(z),where=length[:,None]>0)
        embeddings[dim] = metrics(np.einsum('ij,ij->i',z[a],z[b]))
    return dict(seed=seed, train=len(train), test=k,
                cold_positive=int(((deg[a[:k]]==0)|(deg[b[:k]]==0)).sum()),
                cn=cn, jaccard=jaccard, emb=embeddings)

if __name__ == "__main__":
    ids=np.loadtxt("db-export/Author.csv",delimiter=",",dtype=int,usecols=0)
    pairs=np.loadtxt("db-export/COAUTHOR_Author_Author.csv",delimiter=",",dtype=int)
    with threadpool_limits(limits=4):
        results=[trial(ids,pairs,seed) for seed in (42,43,44)]
    Path("evaluation.json").write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
