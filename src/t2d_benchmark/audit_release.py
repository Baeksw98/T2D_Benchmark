"""Audit the public release for accidental internal references.

This package is de-anonymized: real author names, affiliations, and contact
emails are part of the release and are NOT flagged. The audit instead enforces
the IP boundary -- it blocks internal infrastructure paths, deployment
configuration keys, private artifact roots, raw-output markers, and the private
patient-id scheme -- and verifies the released data assets are present and
aggregate-only.

Forbidden patterns are assembled from fragments via ``token``/``chars`` so this
audit file itself stays clean for the scan.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


def token(*parts: str) -> str:
    return "".join(parts)


def chars(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


FORBIDDEN_PATTERNS = (
    # --- Internal filesystem / infrastructure paths ---
    ("workspace absolute path", token("/", "NH", "N", "HOME", "/")),
    ("workspace root token", token("/", "WORK", "SPACE", "/")),
    ("internal home path", token("/", "home", "/")),
    ("internal os username", chars(115, 97, 109, 115, 117, 110, 103, 95, 107, 121, 46, 104)),
    # --- Private data roots / artifact directories ---
    ("private study root", token("data/", "t", "2", "d_", "stu", "dy")),
    ("private patients root", token("data/", "pat", "ients")),
    ("private ai-sources root", token("AI_", "Sources")),
    ("private rubric root", token("Gold_", "Rubric")),
    ("private rater artifact root", token("AI_", "Rater")),
    ("private cdss artifact root", token("CD", "SS", "/")),
    ("private campaign root", token("_", "campaigns")),
    ("private runs root", token("_", "runs", "/")),
    ("private source manifest", token("source_", "manifest")),
    ("internal content hash field", token("source_", "hash")),
    ("internal kst timestamp field", token("generated_at_", "kst")),
    ("private case workbook basename", token("synthetic_", "case_", "profiles")),
    # --- Serving / infrastructure ---
    ("private gateway port", token(":", "80", "00")),
    ("private upstream port", token(":", "81", "00")),
    ("model switch operation", token("switch_", "model")),
    ("private infra repo", token("N", "H", "N", "_GPU_Backend")),
    ("private remote slug", token(chars(66, 97, 101, 107, 115, 119, 57, 56), "/", "T2D_Research")),
    # --- Internal imports / module boundaries ---
    ("internal app import", token("from ", "app", "lications")),
    ("internal package import", token("from ", "pack", "ages")),
    ("internal app import", token("import ", "app", "lications")),
    ("internal package import", token("import ", "pack", "ages")),
    ("internal backend boundary", token("back", "end_", "cdss")),
    ("internal backend boundary", token("back", "end_", "shared")),
    # --- Private patient id scheme ---
    ("private patient id prefix", token("E", "11", "_", "P")),
    # --- Private model short aliases (the published names GLM-5 / QWEN3.5-397B
    #     do not contain these lowercase no-separator forms) ---
    ("private model alias", token(chars(113, 119, 101, 110), "35")),
    ("private model alias", token(chars(103, 108, 109), "5")),
    ("private model alias", token(chars(103, 101, 109, 109, 97), "4")),
    ("private model alias", chars(110, 101, 109, 111, 116, 114, 111, 110)),
    # --- Internal deployment config-key grammar (suffixes a published name
    #     never carries) ---
    ("deployment config suffix", token("_", "nvfp4_", "local")),
    ("deployment config suffix", token("_", "a17b_", "local")),
    ("deployment config suffix", token("_", "it_", "local")),
    ("deployment config suffix", token("_", "rh_", "local")),
    ("deployment active-params token", token("_", "a12b_")),
    # --- Leftover anonymization placeholders (must not survive de-anonymization) ---
    ("leftover anonymization placeholder", token("Anony", "mous Authors")),
    ("leftover anonymization placeholder", token("Anony", "mous AI")),
    ("leftover anonymization placeholder", token("Anony", "mous conference")),
)

TEXT_SUFFIXES = {".cff", ".csv", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    ".model_cache",
    "outputs",
}

REQUIRED_FILES = (
    "README.md",
    "REPRODUCIBILITY.md",
    "VALIDATION.md",
    "VARIANCE_COMPONENTS.md",
    "PUBLIC_DATA_CARD.md",
    "DATA_LICENSE.md",
    "LICENSE",
    "RELEASE_CHECKLIST.md",
    "CITATION.cff",
    "requirements.txt",
    "pyproject.toml",
    "data/vignettes/README.md",
    "data/vignettes/factorial_index.csv",
    "data/g_theory/README.md",
    "data/g_theory/variance_components.csv",
    "data/g_theory/coefficients.csv",
    "data/demo/synthetic_score_matrix.csv",
    "data/demo/synthetic_protocol_scores.csv",
    "src/t2d_benchmark/audit_release.py",
    "src/t2d_benchmark/build_factorial_index.py",
    "src/t2d_benchmark/build_public_vignettes.py",
    "src/t2d_benchmark/g_theory/run_g_theory.py",
    "src/t2d_benchmark/g_theory/variance_components.py",
    "src/t2d_benchmark/g_theory/coefficients.py",
    "src/t2d_benchmark/analysis/run_clinical_analysis.py",
    "src/t2d_benchmark/analysis/generate_synthetic_demo_data.py",
    "tests/test_audit_release.py",
    "tests/test_vignettes.py",
    "tests/test_g_theory.py",
    "tests/test_clinical_analysis.py",
    "tests/test_public_data.py",
)

# Filename fragments that must never appear as released files.
PROHIBITED_PATH_PARTS = (
    token("source_", "manifest"),
    token("gold_", "rubric"),
    token("user_prompt_", "ko"),
    token("synthetic_", "case_", "profiles"),
)
PROHIBITED_SUFFIXES = {".xlsx", ".xls"}

# Aggregate-only guard for the released variance CSVs.
RELEASED_VARIANCE_FILES = (
    "data/g_theory/variance_components.csv",
    "data/g_theory/coefficients.csv",
)
FORBIDDEN_VARIANCE_COLUMNS = {
    token("pat", "ient_id"),
    token("rat", "er_id"),
    token("rat", "er_model"),
    token("rat", "er_name"),
    "score",
    "rationale",
    token("ru", "bric"),
}
MAX_AGGREGATE_ROWS = 100  # an aggregate table cannot hold the ~388k raw observations

# Vignette set contract.
EXPECTED_VIGNETTE_COUNT = 480
VIGNETTE_REQUIRED_KEYS = {
    "vignette_id",
    "vignette_index",
    "language",
    "factorial_cell",
    "complexity_band",
    "trap_tag",
    "prompt_text",
}


@dataclass(slots=True)
class Finding:
    path: Path
    label: str
    pattern: str
    line_no: int

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        if self.line_no <= 0:
            return f"{rel}: {self.label}"
        return f"{rel}:{self.line_no}: {self.label}"


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings
    for line_no, line in enumerate(text.splitlines(), start=1):
        for label, pattern in FORBIDDEN_PATTERNS:
            if pattern in line:
                findings.append(Finding(path=path, label=label, pattern=pattern, line_no=line_no))
    return findings


def find_git_root(root: Path) -> Path | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    text = completed.stdout.strip()
    return Path(text).resolve() if text else None


def is_git_ignored(root: Path, path: Path) -> bool:
    git_root = find_git_root(root)
    if git_root is None:
        return False
    try:
        rel = path.resolve().relative_to(git_root)
    except ValueError:
        return False
    completed = subprocess.run(
        ["git", "-C", str(git_root), "check-ignore", "-q", "--", str(rel)],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def required_file_findings(root: Path, required_files: Sequence[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel_text in required_files:
        path = root / rel_text
        if not path.exists():
            findings.append(Finding(path=path, label="missing required file", pattern=rel_text, line_no=0))
            continue
        if is_git_ignored(root, path):
            findings.append(Finding(path=path, label="required file is ignored by git", pattern=rel_text, line_no=0))
    return findings


def prohibited_path_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel_text = path.relative_to(root).as_posix()
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            findings.append(Finding(path=path, label="prohibited spreadsheet file", pattern=path.suffix, line_no=0))
            continue
        for part in PROHIBITED_PATH_PARTS:
            if part in rel_text:
                findings.append(Finding(path=path, label="prohibited release file", pattern=part, line_no=0))
                break
    return findings


def vignette_set_findings(root: Path) -> list[Finding]:
    vdir = root / "data" / "vignettes"
    if not vdir.exists():
        return []
    import json

    findings: list[Finding] = []
    files = sorted(vdir.glob("T2D_V*.json"))
    if len(files) != EXPECTED_VIGNETTE_COUNT:
        findings.append(Finding(path=vdir, label="vignette count mismatch", pattern=str(len(files)), line_no=0))
    expected_ids = {f"T2D_V{idx:03d}" for idx in range(1, EXPECTED_VIGNETTE_COUNT + 1)}
    seen_ids: set[str] = set()
    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, ValueError):
            findings.append(Finding(path=path, label="vignette not valid json", pattern=path.name, line_no=0))
            continue
        if set(record) != VIGNETTE_REQUIRED_KEYS:
            findings.append(Finding(path=path, label="vignette schema mismatch", pattern=path.name, line_no=0))
            continue
        if record.get("language") != "en":
            findings.append(Finding(path=path, label="vignette not english", pattern=str(record.get("language")), line_no=0))
        seen_ids.add(record.get("vignette_id", ""))
    if files and seen_ids != expected_ids:
        findings.append(Finding(path=vdir, label="vignette id set mismatch", pattern="T2D_V001..T2D_V480", line_no=0))

    index_path = vdir / "factorial_index.csv"
    if index_path.exists():
        with index_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != EXPECTED_VIGNETTE_COUNT:
            findings.append(Finding(path=index_path, label="factorial index row count mismatch", pattern=str(len(rows)), line_no=0))
        cells = {(r["ckd_stage"], r["hf"], r["ascvd"], r["masld"], r["bmi_category"], r["hba1c_band"]) for r in rows}
        if rows and len(cells) != EXPECTED_VIGNETTE_COUNT:
            findings.append(Finding(path=index_path, label="factorial grid incomplete", pattern=str(len(cells)), line_no=0))
    return findings


def released_variance_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel_text in RELEASED_VARIANCE_FILES:
        path = root / rel_text
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                findings.append(Finding(path=path, label="released variance csv is empty", pattern=rel_text, line_no=1))
                continue
            row_count = sum(1 for _ in reader)
        lowered = {col.strip().lower() for col in header}
        leaked = lowered & FORBIDDEN_VARIANCE_COLUMNS
        if leaked:
            findings.append(Finding(path=path, label="released variance csv has non-aggregate column", pattern=",".join(sorted(leaked)), line_no=1))
        if row_count > MAX_AGGREGATE_ROWS:
            findings.append(Finding(path=path, label="released variance csv is not aggregate (too many rows)", pattern=str(row_count), line_no=0))
    return findings


def audit(
    root: Path,
    *,
    required_files: Sequence[str] = REQUIRED_FILES,
    check_required: bool = True,
    check_patterns: bool = True,
) -> list[Finding]:
    findings: list[Finding] = []
    if check_required:
        findings.extend(required_file_findings(root, required_files))
        findings.extend(prohibited_path_findings(root))
        findings.extend(vignette_set_findings(root))
        findings.extend(released_variance_findings(root))
    if check_patterns:
        findings.extend(finding for path in iter_text_files(root) for finding in scan_file(path))
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release-boundary audit for the public T2D benchmark.")
    parser.add_argument("--root", type=Path, default=Path("."))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    findings = audit(root)
    if findings:
        print("Release audit failed:")
        for finding in findings:
            print(f"- {finding.format(root)}")
        return 1
    print("Release audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
