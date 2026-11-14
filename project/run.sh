#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python_bin=${PYTHON:-python3}
run_dir=${1:-"$project_dir/runs/$(date +%Y%m%d-%H%M%S)"}

for command in "$python_bin" lgraph_import lgraph_export; do
    command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done

mkdir -p -- "$(dirname -- "$run_dir")"
mkdir -- "$run_dir"
cd -- "$run_dir"
cp -- "$project_dir/data/ca-HepTh.txt.gz" .
password=${TUGRAPH_PASSWORD:-73@TuGraph}

"$python_bin" "$project_dir/prepare.py"
lgraph_import -c import.json -d hep-db 2>&1 | tee import.log
lgraph_export -d hep-db -e db-export -u admin -p "$password" | tee export-check.log
"$python_bin" "$project_dir/analyze.py"
lgraph_import -c enriched.json -d hep-results 2>&1 | tee enriched-import.log
lgraph_export -d hep-results -e db-results -u admin -p "$password" | tee enriched-export.log
"$python_bin" "$project_dir/verify.py"
"$python_bin" "$project_dir/evaluate.py"
"$python_bin" "$project_dir/report.py"
printf 'Results: %s\n' "$PWD"
