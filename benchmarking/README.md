# Benchmarking

This directory contains a lightweight framework for benchmarking quantum programs across multiple backends and collecting the results into CSV files and a PDF report.

The framework is designed around a simple workflow: define a benchmarked quantum task, define one or more backend runners, execute them through a result collector, store results incrementally, and optionally update a LaTeX report after each completed run.
This makes it suitable for comparative benchmarking across different providers through Classiq.

## What this directory does

The benchmarking framework supports the following tasks:

- Defining benchmark examples in a backend-independent way
- Running the same benchmark across multiple hardware or simulator backends, including hardware-aware-compilation
- Collecting and storing results incrementally in CSV format
- Resuming partially completed benchmark campaigns without restarting from scratch
- Updating a report directory with generated tables and LaTeX sections
- Optionally rebuilding a PDF report after each completed result

The framework is intended for notebook-based benchmarking workflows, where a user prepares a benchmark, launches runs across several backends, and reviews the collected results in both raw and report-ready forms.

## Main classes

### BenchmarkExample

`BenchmarkExample` represents the quantum task being benchmarked. It stores the benchmark name, the number of qubits, the logic used to build the quantum program, the logic used to execute it, the logic used to score the result, and optionally any synthesis constraints that should be applied.

This class is the benchmark-specific part of the framework. It describes what should be run and how its output should be evaluated, while remaining independent of the specific backend on which the benchmark will execute.

### HardwareRunner

A `HardwareRunner` represents one backend configuration. It stores:

- the backend provider
- the backend name
- the number of shots
- timeout and concurrency parameters
- optional backend-specific keyword arguments (e.g., credentials)

The same `BenchmarkExample` can be run on many different `HardwareRunner`s.

### ResultCollector

`ResultCollector` manages the execution process and persistent result storage.

Its responsibilities include:

- checking whether a benchmark/backend pair was already completed
- submitting jobs only when needed
- resuming from partially completed CSV files
- updating results safely
- optionally rebuilding the report after every completed run

This makes it possible to stop and resume long benchmark runs without losing progress.

## Result files

Benchmark results are written incrementally into a CSV file.

Each row corresponds to a benchmark/backend combination and may include fields such as:

- benchmark name
- number of qubits
- backend provider
- backend name
- number of shots
- status
- job id
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

## Summary

This directory provides a small but reusable infrastructure for running quantum benchmarks in a structured way. It separates benchmark definition from backend configuration, supports resumable result collection, and can automatically maintain a report as data is gathered. The intended use case is repeated comparative benchmarking across multiple providers with minimal duplication of orchestration code.
