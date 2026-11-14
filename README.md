# CA-HepTh 合作网络实验复现

可用浏览器打开 report.html 查看报告网页。用 A4、无页眉页脚、打印背景设置可另存 PDF。

## 环境与运行

实测 TuGraph 4.5.2、WSL 2（Ubuntu 24.04）、NumPy 2.1.3、SciPy 1.15.3、scikit-learn 1.6.1。在本目录操作，使用尚不存在的图库目录。Python 可在 Windows 或 Linux 运行。TuGraph 命令在 Linux 或 WSL 运行，按安装位置设置共享库路径。旧版二进制在 Ubuntu 24.04 上可能需要提供 libgfortran.so.4 的兼容运行库。

```bash
export LD_LIBRARY_PATH=/usr/local/lib64/lgraph:/opt/tugraph-homework/compat/usr/lib/x86_64-linux-gnu
python prepare.py
lgraph_import -c import.json -d hep-db
lgraph_export -d hep-db -e db-export -u admin -p 73@TuGraph > export-check.log
python analyze.py
lgraph_import -c enriched.json -d hep-results
lgraph_export -d hep-results -e db-results -u admin -p 73@TuGraph
python verify.py
python evaluate.py
python report.py
```

Python 依赖可用 pip install numpy scipy scikit-learn 安装。离线导出使用独立实验库的默认账号。

数据来自 https://snap.stanford.edu/data/ca-HepTh.html 。results.json 为报告统计，三个导入导出阶段及核验的日志保存在包内。scores.tsv 的各列为作者编号、PageRank 和逗号分隔的节点向量。

