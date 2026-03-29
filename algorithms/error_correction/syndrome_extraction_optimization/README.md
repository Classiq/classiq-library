## Release Branch (Paper Companion Code)

This branch is a cleaned, benchmark-focused snapshot of the research repository.
It is centered on `benchmark_circuits.py` and includes only the key files needed
for circuit generation, schedule handling, and benchmark/plot reproduction.

### Included core files

- `benchmark_circuits.py`
- `generate_zero_collision_schedules.py`
- `exhaustive_schedule_search.py`
- `ilp_circuit_distance.py`
- `cluster_benchmark/plot_aggregated_results.py`
- `cluster_benchmark/output/aggregated_results.csv`
- `gidney_circuits/src/` (required runtime dependency tree used by benchmark imports)
- `results/zero_collision_schedules.csv`
- `results/circuit_links.html`

### Important runtime note

`benchmark_circuits.py` now imports `ColorCode` from the in-repo fork:

- `color_code_stim_local/`

This avoids relying on modified package files inside a local venv and makes
the provenance explicit in the repository itself.

### Quick run

From repository root:

```bash
./venv_3_11_syndrome_extraction_opt/bin/python benchmark_circuits.py
```

### Plot aggregated cluster results

```bash
./venv_3_11_syndrome_extraction_opt/bin/python cluster_benchmark/plot_aggregated_results.py \
  cluster_benchmark/output/aggregated_results.csv \
  --output results/aggregated_plot.pdf
```

### Scope of this release branch

This branch intentionally excludes most exploratory scripts and large intermediate
research artifacts to make the paper companion code easier to navigate.
