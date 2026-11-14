import html
import json
from statistics import mean, stdev
from pathlib import Path
from urllib.parse import quote

def read(name):
    return Path(name).read_text(encoding="utf-8")

def code(source):
    return "<pre>" + html.escape(source.strip()) + "</pre>"

def table(headers, rows):
    return "<table><thead><tr>" + "".join(f"<th>{x}</th>" for x in headers) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{x}</td>" for x in row) + "</tr>" for row in rows
    ) + "</tbody></table>"

def page(n, heading, content):
    return f'<section id="part-{n}"><header><span>图数据分析实验</span><span>TuGraph 4.5.2 · SNAP CA-HepTh</span></header><h1>{heading}</h1>{content}<footer><span>CA-HepTh / 实验报告</span><span>{n:02d} / 06</span></footer></section>'

d = json.loads(read("data-summary.json"))
r = json.loads(read("results.json"))
db = read("db-check.log")
assert f'vertices={d["nodes"]} edges={d["edges"]} scored={d["nodes"]}' in db
raw = d["raw"]
nodes = d["nodes"]
edges = d["edges"]
pg1 = page(1, "高能物理理论合作网络分析", f"""
<p class="lede">基于 TuGraph 的作者中心性计算与 32 维节点嵌入</p>
<div class="cards"><div><b>{raw:,}</b><span>原始边表记录</span></div><div><b>{nodes:,}</b><span>作者节点</span></div><div><b>{edges:,}</b><span>去重合作关系</span></div></div>
<h2>1　数据来源与任务</h2>
<p>选用 Stanford Network Analysis Project（SNAP）发布的 <a href="https://snap.stanford.edu/data/ca-HepTh.html">CA-HepTh 合作网络</a>。数据来自 arXiv 高能物理理论类别，覆盖 1993 年 1 月至 2003 年 4 月。作者为节点，两位作者共同署名至少一篇论文就形成合作关系。边表为制表符分隔的两列整数 FromNodeId、ToNodeId，仅含匿名作者编号。</p>
<p>实验用 PageRank 排序合作网络中的作者，再用节点向量检索结构相近的作者。合作关系按无权边处理，因为所用边表没有提供共同署名次数。</p>
<h2>2　清洗与图模型</h2>
<p>跳过注释，保留原始端点中的所有作者。删除 {d['loops']} 条自环，将每对作者映射为 (min(u,v), max(u,v)) 后去重。数据库只存一条 COAUTHOR 边，算法构造邻接矩阵时为每条边补上反向项。</p>
{table(['图元素','类型与字段','含义'],[['Author','顶点 / id INT64 主键','源数据作者编号'],['Author','pagerank DOUBLE','中心性分数'],['Author','embedding STRING','逗号分隔的 32 维向量'],['COAUTHOR','边 / Author → Author','一对作者的合作关系']])}
<p class="hash"><b>原始压缩文件 SHA-256</b><br>{d['sha256']}</p>
""")
pg2 = page(2, "TuGraph 数据导入与结果校验", f"""
<p class="lede">WSL 2 · Ubuntu 24.04 · TuGraph 4.5.2 · Python 稀疏矩阵计算</p>
<h2>3　数据库操作</h2>
<p>运行 prepare.py 生成两个无表头 CSV 和导入配置。lgraph_import 创建图库 default，lgraph_export 从实际图库读出作者和边。Python 将导出内容与清洗结果逐项比对，再运行两个算法。将带有 PageRank 和向量的作者表与原有边表批量导入第二个 TuGraph 库。</p>
{code("python prepare.py\nlgraph_import -c import.json -d hep-db\nlgraph_export -d hep-db -e db-export -u admin -p 73@TuGraph\npython analyze.py\nlgraph_import -c enriched.json -d hep-results\nlgraph_export -d hep-results -e db-results -u admin -p 73@TuGraph\npython verify.py")}
<h2>结果核验</h2>
<p>再次从结果库导出数据。按作者编号逐项核对 32 维向量字符串，并比较结果库与源图库的全部合作边。PageRank 导出 CSV 显示到小数点后 6 位，按 0.000000501 的绝对误差上限校验。</p>
<h2>实测日志</h2>
{code(next(line for line in read('export-check.log').splitlines() if 'Dumped' in line))}
{code(db)}
<p class="note">两个算法由 Python 在 TuGraph 进程外运行，输入来自 TuGraph 实库。运行所需的库路径见复现包。</p>
""")
top = [[i, a, f"{b:.9f}", c] for i,(a,b,c) in enumerate(r["top"],1)]
pg3 = page(3, "PageRank 作者中心性", f"""
<h2>4　算法原理与参数</h2>
<p>将作者视为均匀选择合作者进行跳转的随机游走者。对有合作者的作者 i，转移概率 P(i,j)=A(i,j)/d(i)。孤立节点的概率质量均匀分给所有节点。阻尼系数为 0.85，从均匀分布开始迭代。</p>
<div class="formula">r′ = 0.85 × (Pᵀr + 孤立节点概率质量 / n) + 0.15 / n</div>
{code('transition = diags(inv) @ adjacency\nfor iterations in range(1, 1001):\n    updated = .85 * (transition.T @ rank + rank[dangling].sum()/n) + .15/n\n    residual = np.abs(rank - updated).sum()\n    rank = updated\n    if residual < 1e-12:\n        break')}
<h2>实测结果</h2>
<p>第 {r['iterations']} 轮达到停止阈值，末次 L1 变化量为 {r['residual']:.3e}，分数之和为 {r['rank_sum']:.12f}。图中有 {r['components']} 个连通分量，最大分量有 {r['largest']:,} 个节点。</p>
{table(['排名','作者 ID','PageRank','合作作者数'],top)}
<p>首位作者 {top[0][1]} 有 {top[0][3]} 位合作者。第 3 位作者的合作者数低于第 4 位，说明该排名还受合作者分数及其对外分配比例影响。</p>
""")
near = [[a, f"{b:.6f}", "是" if c else "否"] for a,b,c in r["neighbors"]]
pg4 = page(4, "谱矩阵分解节点嵌入", f"""
<h2>5　算法原理与参数</h2>
<p>对称归一化邻接矩阵 S=D⁻¹ᐟ²AD⁻¹ᐟ²，孤立点的归一化系数置零。构造 C=S+S²，将直接合作和两步共同邻居纳入结构表示。用随机化截断 SVD 计算 32 个奇异分量，以左奇异向量各列乘相应奇异值的平方根，取得节点向量。</p>
{code('scale = diags(np.sqrt(inv))\nnormalized = scale @ adjacency @ scale\ncontext = normalized + normalized @ normalized\nleft, sigma, _ = randomized_svd(context, n_components=32,\n                                n_iter=10, random_state=42)\nembedding = left * np.sqrt(sigma)')}
<h2>实测结果</h2>
<p>向量矩阵尺寸 {r['dims'][0]:,} × {r['dims'][1]}，其中 {r['zero_vectors']:,} 个节点的向量范数为零。零向量参与统计时相似度按 0 处理。比较全部 {edges:,} 个合作对与等量均匀抽样的唯一非合作对（种子 42）。两类平均余弦相似度分别为 {r['positive']:.4f} 和 {r['negative']:.4f}，排序 AUC 为 {r['auc']:.4f}。正例参与了嵌入构造，该指标衡量原图内区分度。</p>
<p>以 PageRank 第一的作者 {top[0][1]} 为查询节点，按余弦相似度取前五名。</p>
{table(['相近作者 ID','余弦相似度','有直接合作边'],near)}
<h2>来源与实现文档</h2>
<p><a href="https://snap.stanford.edu/data/ca-HepTh.html">Stanford SNAP · CA-HepTh 数据集</a><br>
<a href="https://tugraph-db.readthedocs.io/en/latest/6.utility-tools/1.data-import.html">TuGraph · 数据导入</a><br>
<a href="https://tugraph-db.readthedocs.io/en/v4.3.0/9.olap%26procedure/2.olap/1.tutorial.html">TuGraph · 图分析接口与嵌入模式</a></p>
""")
trials = json.loads(read("evaluation.json"))
methods = [
    ("共同邻居", [t["cn"] for t in trials]),
    ("Jaccard", [t["jaccard"] for t in trials]),
    *[(str(dim) + " 维谱嵌入", [t["emb"][str(dim)] for t in trials]) for dim in (16,32,64)],
]
metrics = [[name, *(f"{mean(v):.4f} ± {stdev(v):.4f}" for v in zip(*values))] for name, values in methods]
seed_rows = [[t["seed"], t["train"], t["test"], t["cold_positive"],
              f'{t["emb"]["32"][0]:.4f}',f'{t["emb"]["32"][1]:.4f}'] for t in trials]
pg5 = page(5, "留出边验证与基线对比", f"""
<h2>6　验证方法</h2>
<p>对数据库导出的无向边使用种子 42、43、44 独立划分。每次将 5,194 条真实合作边从图中移除，保留 20,779 条训练边。所有作者均保留。测试负例从完整图的非边中均匀抽取，排除自环并去重，共 5,194 对。每轮所有方法共用同一批测试样本。</p>
<p>归一化矩阵、共同邻居及 Jaccard 都只基于训练图。Jaccard 是两个邻居集合的交集大小除以并集大小，并集为空时记为 0。节点嵌入用余弦相似度评分，含零向量的样本记为 0。</p>
<h2>基线和维度对比</h2>
<p>ROC AUC 衡量正例排在负例之前的能力，同分计半。AP（平均精确率）侧重排序靠前的预测。表中报告三次实验的均值与样本标准差。</p>
{table(['方法','ROC AUC','AP'],metrics)}
<h2>32 维嵌入各轮结果</h2>
{table(['种子','训练边','留出正例','含孤立点正例','ROC AUC','AP'],seed_rows)}
<p>共同邻居的平均 AUC 最高，64 维嵌入的平均 AP 最高。三个维度之间的差距较小，增加维度没有带来稳定增益。留出边使部分作者在训练图中变为孤立点，这些正例无法从训练邻接矩阵取得邻居信息。</p>
""")
pg6 = page(6, "结果解释与复现", f"""
<h2>7　结果解释</h2>
<p>作者 1441 的 PageRank 最高。排名与合作作者数存在差异，因为每位作者向各合作者传递的贡献被自身度数平分。报告只用匿名 ID 描述图中的位置。</p>
<p>原图内 AUC 为 {r['auc']:.4f}，该分数包含用于构造嵌入的已知合作边。32 维嵌入在留出实验中的平均 AUC 为 {mean(t['emb']['32'][0] for t in trials):.4f}。两者衡量不同问题，留出实验更适合评价未参与训练的合作关系。</p>
<p>原始边表没有合作时间、论文数或研究主题。随机留出验证衡量同一图上的边恢复，不能推断未来合作。评估用等量正负例，AP 以该抽样比例为条件。更换负样本比例或使用更难区分的负例会改变评估结果。</p>
<h2>8　复现入口与核验项</h2>
{table(['文件','作用'],[['prepare.py','记录原始数据哈希并生成导入文件'],['analyze.py','计算全图 PageRank、32 维嵌入和相近作者'],['evaluate.py','运行三次留出实验及基线对比'],['verify.py','逐项核对结果库的边、分数与向量'],['results.json / evaluation.json','保存报告数值和每轮指标'],['scores.tsv','按作者 ID 保存全量分数与向量']])}
<p>复现包包含原始数据、TuGraph 导入配置和运行日志。报告中的数据规模来自实际导入和导出记录，留出实验复用同一份实库边表。</p>
""")
css = """
@page{size:A4;margin:0} *{box-sizing:border-box}
body{margin:0;color:#18293a;font:10.5pt/1.58 "Microsoft YaHei",sans-serif}
section{height:296.8mm;width:210mm;position:relative;padding:15mm 17mm 17mm;break-after:page}
section:last-child{break-after:auto}
header,footer{display:flex;justify-content:space-between;font-size:9pt;color:#496677}
header{border-bottom:1.5pt solid #158377;padding-bottom:3mm}
footer{border-top:1px solid #c9dade;padding-top:2.8mm;position:absolute;bottom:11mm;left:17mm;right:17mm}
h1{font-size:24pt;margin:8mm 0 2mm;line-height:1.3;color:#102b43}
h2{font-size:13pt;margin:5mm 0 1.5mm;color:#135e58}
p{margin:1.6mm 0 2.5mm} .lede{color:#466176;margin:2mm 0 4mm}
.cards{display:flex;gap:3mm;margin:7mm 0}.cards div{flex:1;background:#eaf4f2;padding:3mm 4mm}
.cards b,.cards span{display:block}.cards b{font-size:21pt;color:#145e57}.cards span{font-size:9pt}
table{border-collapse:collapse;width:100%;margin:3mm 0;font-size:9.5pt}
th,td{text-align:left;padding:1.2mm 2.8mm;border-bottom:1px solid #dae5e9}
th{background:#e6f0f1;color:#1d4e58}
pre{white-space:pre-wrap;background:#f0f4f7;border-left:2pt solid #158377;padding:2.8mm 3.6mm;font:8.7pt/1.43 Consolas,monospace;margin:2mm 0}
.formula{background:#eaf4f2;padding:2.5mm 4mm;color:#145e57;margin:3mm 0}
a{color:#076758}.hash,.note{font-size:9pt;color:#496677}
.web-nav{display:none}
@media screen{
body{background:#edf4f5}
section{height:auto;width:min(100%,210mm);min-height:0;margin:1rem auto;background:white;padding:clamp(1rem,5vw,17mm)}
footer{position:static;margin-top:2rem}
.web-nav{display:flex;flex-wrap:wrap;gap:1rem;max-width:210mm;margin:1rem auto;padding:1rem;background:#e0eeec}
table{display:block;overflow-x:auto}
}
"""
nav = """<nav class="web-nav" aria-label="报告目录"><a href="#part-1">数据来源</a><a href="#part-2">TuGraph</a><a href="#part-3">PageRank</a><a href="#part-4">节点嵌入</a><a href="#part-5">实验验证</a><a href="#part-6">复现</a><a href="report.pdf">PDF</a><a href="reproduction.zip">复现包</a></nav>"""
Path("report.html").write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CA-HepTh 合作网络分析</title><style>"+css+"</style>"+nav+pg1+pg2+pg3+pg4+pg5+pg6+"</html>", encoding="utf-8")

