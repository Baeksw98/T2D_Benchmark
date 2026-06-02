from __future__ import annotations

from pathlib import Path

from t2d_benchmark.audit_release import audit, released_variance_findings


def test_detects_workspace_and_port(tmp_path: Path) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_text(
        "/" + "NH" + "N" + "HOME" + "/x\n" + "http://127.0.0.1:" + "80" + "00" + "/v1\n",
        encoding="utf-8",
    )
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "workspace absolute path" in labels
    assert "private gateway port" in labels


def test_detects_internal_import(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("from " + "app" + "lications.x import y\n", encoding="utf-8")
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "internal app import" in labels


def test_detects_deployment_config_key(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    key = "g" + "l" + "m" + "5" + "_" + "nvfp4_" + "local"
    bad.write_text("model_key=" + key + "\n", encoding="utf-8")
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "deployment config suffix" in labels


def test_detects_novel_deployment_suffix(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("key=foo_99b_a9b_" + "nvfp4_" + "local\n", encoding="utf-8")
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "deployment config suffix" in labels


def test_detects_private_artifact_roots(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(
        "a=" + "source_" + "manifest" + ".json\n"
        + "b=" + "Gold_" + "Rubric" + "/x\n"
        + "c=" + "AI_" + "Sources" + "/y\n"
        + "d=" + "source_" + "hash" + "\n",
        encoding="utf-8",
    )
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "private source manifest" in labels
    assert "private rubric root" in labels
    assert "private ai-sources root" in labels
    assert "internal content hash field" in labels


def test_detects_patient_prefix(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("id=" + "E" + "11_" + "P013\n", encoding="utf-8")
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "private patient id prefix" in labels


def test_detects_leftover_anonymization(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("Copyright Anony" + "mous Authors\n", encoding="utf-8")
    labels = {f.label for f in audit(tmp_path, check_required=False)}
    assert "leftover anonymization placeholder" in labels


def test_allows_published_model_names(tmp_path: Path) -> None:
    ok = tmp_path / "readme.md"
    # The published spellings must NOT be flagged.
    ok.write_text("We use GLM-5 and QWEN3.5-397B as backbones.\n", encoding="utf-8")
    assert audit(tmp_path, check_required=False) == []


def test_allows_deanonymized_identity(tmp_path: Path) -> None:
    ok = tmp_path / "cite.md"
    ok.write_text(
        "Sangwon Baek, Samsung Medical Center; contact ky.hur@skku.edu, kyunga.j.kim@gmail.com\n",
        encoding="utf-8",
    )
    assert audit(tmp_path, check_required=False) == []


def test_variance_aggregate_guard(tmp_path: Path) -> None:
    gdir = tmp_path / "data" / "g_theory"
    gdir.mkdir(parents=True)
    # A non-aggregate table with a per-patient column and too many rows.
    leak_col = "pat" + "ient_id"
    lines = ["%s,phi" % leak_col] + [f"P{i:04d},0.9" for i in range(150)]
    (gdir / "variance_components.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    labels = {f.label for f in released_variance_findings(tmp_path)}
    assert "released variance csv has non-aggregate column" in labels
    assert "released variance csv is not aggregate (too many rows)" in labels


def test_detects_missing_required_file(tmp_path: Path) -> None:
    findings = audit(tmp_path, required_files=("README.md",), check_patterns=False)
    assert findings
    assert findings[0].label == "missing required file"


def test_allows_public_tree() -> None:
    root = Path(__file__).resolve().parents[1]
    findings = audit(root)
    assert findings == [], "\n".join(f.format(root) for f in findings)
