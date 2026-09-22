import json
import os
import shutil
import subprocess
from copy import deepcopy
from zipfile import ZipFile

import pytest

from scripts import project


@pytest.fixture
def source_tree(tmp_path):
    for filename in project.RUNTIME_FILES:
        (tmp_path / filename).write_text("", encoding="utf-8")
    (tmp_path / "VERSION").write_text("2026-09-21\n", encoding="utf-8")
    (tmp_path / "server.py").write_text('print("service")\n', encoding="utf-8")
    return tmp_path


@pytest.fixture
def coverage_data():
    summary = {
        "covered_lines": 9,
        "num_statements": 10,
        "covered_branches": 9,
        "num_branches": 10,
    }
    return {
        "meta": {"branch_coverage": True},
        "totals": deepcopy(summary),
        "files": {
            "server.py": {
                "summary": deepcopy(summary),
                "functions": {
                    "score": {"summary": deepcopy(summary)},
                    "": {"summary": deepcopy(summary)},
                },
            }
        },
    }


def test_build_contains_only_runtime_files(source_tree):
    (source_tree / ".env").write_text("SECRET=private", encoding="utf-8")
    (source_tree / "unrelated.py").write_text("", encoding="utf-8")
    archive_path = project.build_archive(source_tree)

    assert archive_path.name == "similarstring-2026-09-21.zip"
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(project.RUNTIME_FILES)
        assert archive.read("VERSION") == b"2026-09-21\n"
        assert archive.testzip() is None


def test_build_rejects_missing_runtime_file(source_tree):
    (source_tree / "config.yaml").unlink()

    with pytest.raises(FileNotFoundError, match="config.yaml"):
        project.build_archive(source_tree)


def test_build_rejects_invalid_version(source_tree):
    (source_tree / "VERSION").write_text("../../unsafe", encoding="utf-8")

    with pytest.raises(ValueError):
        project.build_archive(source_tree)


def test_build_checks_python_syntax(source_tree):
    (source_tree / "server.py").write_text("def invalid(", encoding="utf-8")

    with pytest.raises(SyntaxError):
        project.build_archive(source_tree)


def test_coverage_passes_at_threshold(coverage_data):
    report, passed = project.coverage_report(coverage_data, 90)

    assert passed
    assert "90.00% (target 90%)" in report
    assert "| PASS | Functions | 100.00% (target 90%) | 1 / 1 |" in report
    assert "File Coverage" in report
    assert "`server.py`" in report


@pytest.mark.parametrize("field", ["covered_lines", "covered_branches"])
def test_each_coverage_metric_has_a_minimum(coverage_data, field):
    coverage_data["totals"][field] = 8

    report, passed = project.coverage_report(coverage_data, 90)

    assert not passed
    assert "FAIL" in report


def test_uncovered_functions_fail_the_gate(coverage_data):
    coverage_data["files"]["server.py"]["functions"]["untested"] = {
        "summary": {"covered_lines": 0, "num_statements": 5}
    }

    report, passed = project.coverage_report(coverage_data, 90)

    assert not passed
    assert "| FAIL | Functions | 50.00%" in report


def test_zero_branches_does_not_divide_by_zero(coverage_data):
    for summary in [
        coverage_data["totals"],
        coverage_data["files"]["server.py"]["summary"],
    ]:
        summary.update(covered_branches=0, num_branches=0)

    report, passed = project.coverage_report(coverage_data, 90)

    assert passed
    assert "| PASS | Branches | 100.00% (target 90%) | 0 / 0 |" in report


def test_report_requires_branch_measurement(coverage_data):
    coverage_data["meta"]["branch_coverage"] = False

    with pytest.raises(ValueError, match="Branch coverage"):
        project.coverage_report(coverage_data, 90)


def test_empty_report_is_rejected(coverage_data):
    coverage_data["files"] = {}

    with pytest.raises(ValueError, match="No executable statements"):
        project.coverage_report(coverage_data, 90)


def test_build_command(source_tree, capsys):
    assert project.main(["build"], root=source_tree) == 0
    assert "similarstring-2026-09-21.zip" in capsys.readouterr().out


@pytest.mark.parametrize("covered, expected_exit", [(9, 0), (8, 1)])
def test_report_command_writes_report_and_enforces_gate(
    tmp_path, coverage_data, monkeypatch, covered, expected_exit
):
    coverage_data["totals"]["covered_branches"] = covered
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.report]\nfail_under = 90\n", encoding="utf-8"
    )
    output = tmp_path / "coverage"
    output.mkdir()
    (output / "coverage.json").write_text(json.dumps(coverage_data), encoding="utf-8")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "9")
    monkeypatch.setenv("COVERAGE_COMMIT", "c75b15312345")

    assert project.main(["coverage-report"], root=tmp_path) == expected_exit
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "workflow #9 for commit `c75b153`" in report


@pytest.fixture
def smoke_runner(tmp_path):
    if not shutil.which("bash") or not shutil.which("jq"):
        pytest.skip("Smoke script checks require Bash and jq")
    curl = tmp_path / "curl"
    curl.write_text(
        """#!/bin/sh
printf '%s\\n' "$*" >> "$CURL_CALLS"
case "$*" in
  *"/health"*)
    echo 'curl: (56) Recv failure: Connection reset by peer' >&2
    case "$HEALTH_RESULT" in
      ready) echo '{"status":"ok","version":"2026-09-21"}' ;;
      failed) exit 28 ;;
      invalid) echo '{"status":"error"}' ;;
    esac
    ;;
  *) echo '{"status":"success","s1":"A laptop","s2":"A laptop","score":1.0}' ;;
esac
""",
        encoding="utf-8",
    )
    curl.chmod(0o755)
    calls_path = tmp_path / "curl-calls.txt"

    def run(health_result="ready", startup_timeout="1"):
        environment = {
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            "SS_URL": "http://127.0.0.1:5000",
            "SS_STARTUP_TIMEOUT": startup_timeout,
            "HEALTH_RESULT": health_result,
            "CURL_CALLS": str(calls_path),
        }
        result = subprocess.run(
            ["bash", str(project.ROOT / "test_ml_server.sh")],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        calls = calls_path.read_text().splitlines() if calls_path.exists() else []
        return result, calls

    return run


def test_smoke_startup_retries_are_quiet_on_success(smoke_runner):
    result, calls = smoke_runner()

    assert result.returncode == 0
    assert "Waiting for" in result.stdout
    assert "Server is ready" in result.stdout
    assert "connection resets during this wait are expected" in result.stdout
    assert result.stderr == ""
    assert len(calls) == 4
    assert "--retry-max-time 1" in calls[0]


def test_smoke_startup_failure_keeps_diagnostics(smoke_runner):
    result, calls = smoke_runner("failed")

    assert result.returncode != 0
    assert "Server did not become ready" in result.stderr
    assert "Connection reset by peer" in result.stderr
    assert "Server is ready" not in result.stdout
    assert len(calls) == 1


def test_smoke_rejects_invalid_health_response(smoke_runner):
    result, calls = smoke_runner("invalid")

    assert result.returncode != 0
    assert "Unexpected health response" in result.stderr
    assert "Server is ready" not in result.stdout
    assert len(calls) == 1


@pytest.mark.parametrize("timeout", ["0", "-1", "invalid"])
def test_smoke_rejects_invalid_startup_timeout(smoke_runner, timeout):
    result, calls = smoke_runner(startup_timeout=timeout)

    assert result.returncode != 0
    assert "SS_STARTUP_TIMEOUT must be a positive number" in result.stderr
    assert not calls
