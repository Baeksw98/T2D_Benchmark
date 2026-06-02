"""Public statistical-analysis pipeline for the T2D benchmark.

- ``generate_synthetic_demo_data`` builds the deterministic synthetic demo
  tables that exercise the pipeline end-to-end without any private data.
- ``run_clinical_analysis`` reproduces the descriptive Baseline-vs-DRG
  comparison (per-question Kolmogorov-Smirnov tests and paired differences).
"""
