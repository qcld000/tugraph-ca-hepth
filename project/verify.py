import csv
from pathlib import Path

def read_rows(path):
    with Path(path).open(newline="") as f:
        return list(csv.reader(f))

expected = {row[0]: (float(row[1]), row[2]) for row in read_rows("authors-enriched.csv")}
rows = read_rows("db-results/Author.csv")
actual = {row[0]: (float(row[1]), row[2]) for row in rows}
assert len(actual) == len(rows) == len(expected)
assert actual.keys() == expected.keys()
error = max(abs(actual[i][0] - expected[i][0]) for i in actual)
print(error)
assert error <= 5.01e-7
assert all(actual[i][1] == expected[i][1] and len(actual[i][1].split(",")) == 32 for i in actual)
initial_edges = read_rows("db-export/COAUTHOR_Author_Author.csv")
final_edges = read_rows("db-results/COAUTHOR_Author_Author.csv")
assert sorted(initial_edges) == sorted(final_edges)
summary = f"vertices={len(actual)} edges={len(final_edges)} scored={len(actual)}\n"
summary += f"max absolute PageRank export error={error:.3e}\n"
Path("db-check.log").write_text(summary)
print(summary, end="")

