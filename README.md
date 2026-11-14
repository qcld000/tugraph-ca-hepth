# 基于 TuGraph 的 CA-HepTh 合作网络分析

[在线报告](https://qcld000.github.io/tugraph-ca-hepth/) · [提交用 PDF](report.pdf) · [离线复现包](reproduction.zip)

使用 Stanford SNAP 的 [CA-HepTh 数据集](https://snap.stanford.edu/data/ca-HepTh.html)，将 51,971 条原始边表记录清洗为 9,877 个作者节点和 25,973 条无向合作边。TuGraph 负责图库导入、导出与结果持久化。Python 在导出的实库图数据上执行 PageRank 和 32 维谱嵌入，并进行三轮留出边评估。

## 项目文件

| 文件 | 用途 |
| --- | --- |
| [prepare.py](project/prepare.py) | 清洗原始边表、生成 CSV 和导入配置 |
| [analyze.py](project/analyze.py) | 构造无向邻接矩阵、计算 PageRank 与谱嵌入 |
| [evaluate.py](project/evaluate.py) | 验证 16、32、64 维嵌入，对照共同邻居与 Jaccard |
| [verify.py](project/verify.py) | 校验结果库中的作者、合作边、分数与向量 |
| [report.py](project/report.py) | 从运行结果生成实验报告网页 |
| [config/](project/config/) | 实测所用的两阶段 TuGraph 导入配置 |
| [data/](project/data/) | 原始 SNAP 压缩边表 |
| [results/](project/results/) | 实测指标、全量节点结果和导入导出日志 |

## 复现完整流程

在 Linux 或 WSL 中准备 TuGraph 4.5.2 与 Python。确保 `lgraph_import`、`lgraph_export` 在 PATH 中。按 TuGraph 安装位置配置动态库搜索路径，旧版二进制在 Ubuntu 24.04 上可能还需要 `libgfortran.so.4` 兼容库。

```bash
git clone https://github.com/qcld000/tugraph-ca-hepth.git
cd tugraph-ca-hepth
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r project/requirements.txt
bash project/run.sh
```

也可传入一个尚不存在的目录，例如 `bash project/run.sh ./experiment-01`。脚本在该目录生成源图库 `hep-db`、结果图库 `hep-results`、全量 `scores.tsv`、评估指标及报告网页。复现脚本会自动重新生成两份导入配置，以匹配本轮生成的数据文件。

GitHub Pages 托管报告、PDF 和复现包。TuGraph 实验由仓库中的复现脚本在 Linux 或 WSL 中运行。
