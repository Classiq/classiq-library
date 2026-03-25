# Benchmarking

This directory contains a framework for benchmarking quantum programs across multiple backends, collecting the results into CSV files, and optionally generating a single summary PDF report.

The framework is designed around a simple workflow: define a benchmarked quantum task, define one or more backend runners, execute them through a result collector, store results incrementally, and optionally update a LaTeX report after each completed run. This makes it suitable for comparative benchmarking across different providers through Classiq.

### Requirements

PDF generation uses `latexmk`. The benchmarking notebooks assume that `latexmk` is installed and available in `$PATH`.

## What this directory does

The benchmarking framework supports the following tasks:

- Defining benchmark examples in a backend-independent way
- Running the same benchmark across multiple hardware or simulator backends, including hardware-aware compilation
- Collecting and storing results incrementally in CSV format
- Resuming partially completed benchmark campaigns without restarting from scratch
- Defining a Quantum Volume protocol based on a benchmark example with varying width
- Updating a report directory with generated tables and LaTeX sections
- Optionally rebuilding a PDF report after each completed result

The framework is intended for notebook-based benchmarking workflows, where a user prepares a benchmark, launches runs across several backends, and reviews the collected results in both raw and report-ready forms.

## How to run benchmark experiments

Benchmark notebooks are located in the `benchmarks` directory, and the Quantum Volume notebook is located in the `protocols` directory.

The repository already contains data and report outputs from a previous benchmark run. To start a new benchmarking project from scratch, call the following in any of the notebooks (only once):

```python
from project_reset import reset_benchmark_project
reset_benchmark_project()
```

After that, you can run any benchmark notebook to generate a new report from fresh data.

### Benchmarks

In each benchmark notebook, an example is defined, and its size can be set, for example:

```python
example = AdderExample(num_qubits=4)
```

The backends to benchmark are then specified, for example:

```python
benchmark_hardware = [
    {"provider": "Classiq", "backend": "simulator"},
    {"provider": "Classiq", "backend": "simulator_statevector"},
    {"provider": "IonQ", "backend": "qpu.forte-1"},
    {"provider": "Amazon Braket", "backend": "Ankaa-3"},
]
```

When a notebook is run, benchmarking jobs are submitted and their results are collected asynchronously. The `report/report.pdf` file is updated whenever a new result is obtained.

### Quantum Volume protocol

A notebook for running the Quantum Volume protocol is located in the `protocols` directory. The range of widths and the number of trials can be configured, for example:

```python
protocol = QuantumVolumeProtocol(
    min_num_qubits=2,
    max_num_qubits=4,
    num_trials=10,
    ...
)
```

The backends to benchmark are defined in the same way as for the benchmark notebooks. The `report/report.pdf` file is updated whenever a new result is obtained for a given width.

## Main classes

### BenchmarkExample

`BenchmarkExample` represents the quantum task being benchmarked. It stores the benchmark name, the number of qubits, the logic used to build the quantum program, the logic used to execute it, the logic used to score the result, and optionally any synthesis constraints that should be applied.

This class is the benchmark-specific part of the framework. It describes what should be run and how its output should be evaluated, while remaining independent of the specific backend on which the benchmark will execute.

### HardwareRunner

A `HardwareRunner` represents one backend configuration. It stores:

- the backend provider
- the backend name
- the number of shots
- backend execution timeout parameters
- optional backend-specific keyword arguments (for example, credentials)

The same `BenchmarkExample` can be run on many different `HardwareRunner`s.

### ResultCollector

`ResultCollector` manages the execution process and persistent result storage.

Its responsibilities include:

- checking whether a benchmark/backend pair has already been completed
- submitting jobs only when needed
- resuming from partially completed CSV files
- updating results safely
- enforcing local submission and execution limits
- optionally rebuilding the report after every completed run

The result file path is the single source of truth for a `ResultCollector` object. This makes it possible to stop and resume long benchmark runs without losing progress, as well as to add new `HardwareRunner`s to an existing experiment.

When running on Classiq backends, there is currently a limit of three parallel submitted jobs. Accordingly, `ResultCollector` ensures that no more than three jobs are submitted at the same time by default. This behavior is controlled by the `max_submitted_jobs_in_dir` property, which can be adjusted if a higher submission limit is available. If a notebook run is interrupted, rerunning it will both check whether previously submitted jobs have completed and submit new jobs when submission capacity becomes available.

## Result files

Benchmark results are written incrementally into a CSV file.

Each row corresponds to a benchmark/backend combination and may include fields such as:

- benchmark name
- number of qubits
- backend provider
- backend name
- number of shots
- status
- job ID
- timestamps
- score
- runtime metrics

Because results are written incrementally, interrupted runs can be resumed later by reusing the same CSV file.

## Report generation

The framework can also maintain a LaTeX report directory containing:

- raw section CSV files
- generated section `.tex` files
- an include file for the report
- a built PDF report

When `build_each_time=True`, the report is updated every time a benchmark finishes.

## Quantum Volume protocol

The framework also includes classes for defining a Quantum Volume `BenchmarkExample`, as well as a `QuantumVolumeProtocol` class to run and manage result collectors for this benchmark across varying widths.

## Summary

This directory provides a small but reusable infrastructure for running quantum benchmarks in a structured way. It separates benchmark definition from backend configuration, supports resumable result collection, and can automatically maintain a report as data is gathered. The intended use case is repeated comparative benchmarking across multiple providers with minimal duplication of orchestration code.
