import argparse
import json
import os
import tomllib
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    "server.py",
    "config.yaml",
    "requirements.txt",
    "VERSION",
    "Dockerfile",
    ".dockerignore",
    "docker-compose.yml",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "SECURITY.md",
    "SUPPORT.md",
    "PRIVACY.md",
)


def build_archive(root=ROOT):
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if date.fromisoformat(version).isoformat() != version:
        raise ValueError("VERSION must use YYYY-MM-DD format")
    for filename in RUNTIME_FILES:
        if not (root / filename).is_file():
            raise FileNotFoundError(filename)
    compile((root / "server.py").read_text(encoding="utf-8"), "server.py", "exec")
    output = root / "dist" / f"similarstring-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for filename in RUNTIME_FILES:
            archive.write(root / filename, arcname=filename)
    return output


def percentage(covered, total):
    return 100 * covered / total if total else 100.0


def coverage_report(data, threshold):
    if not data["meta"]["branch_coverage"]:
        raise ValueError("Branch coverage must be enabled")
    totals = data["totals"]
    if not data["files"] or not totals["num_statements"]:
        raise ValueError("No executable statements were measured")
    functions = [
        function
        for file_data in data["files"].values()
        for name, function in file_data["functions"].items()
        if name and function["summary"]["num_statements"]
    ]
    metrics = (
        ("Lines", totals["covered_lines"], totals["num_statements"]),
        ("Statements", totals["covered_lines"], totals["num_statements"]),
        (
            "Functions",
            sum(function["summary"]["covered_lines"] > 0 for function in functions),
            len(functions),
        ),
        ("Branches", totals["covered_branches"], totals["num_branches"]),
    )
    lines = [
        "<!-- similarstring-coverage -->",
        "## Coverage Report",
        "",
        "| Status | Category | Percentage | Covered / Total |",
        "| :--- | :--- | ---: | ---: |",
    ]
    passed = True
    for category, covered, total in metrics:
        value = percentage(covered, total)
        status = "PASS" if value >= threshold else "FAIL"
        passed = passed and value >= threshold
        lines.append(
            f"| {status} | {category} | {value:.2f}% (target {threshold:g}%) "
            f"| {covered} / {total} |"
        )
    lines.extend(
        [
            "",
            "### File Coverage",
            "",
            "| File | Lines / statements | Branches |",
            "| :--- | ---: | ---: |",
        ]
    )
    for filename, file_data in sorted(data["files"].items()):
        summary = file_data["summary"]
        line_percent = percentage(summary["covered_lines"], summary["num_statements"])
        branch_percent = percentage(
            summary["covered_branches"], summary["num_branches"]
        )
        lines.append(f"| `{filename}` | {line_percent:.2f}% | {branch_percent:.2f}% |")
    lines.extend(
        [
            "",
            "coverage.py measures executable statements as lines. "
            "A function is covered when at least one of its executable lines runs.",
            "",
        ]
    )
    return "\n".join(lines), passed


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description="SimilarString development tools")
    parser.add_argument("command", choices=("build", "coverage-report"))
    args = parser.parse_args(argv)
    if args.command == "build":
        print(build_archive(root))
        return 0
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    threshold = config["tool"]["coverage"]["report"]["fail_under"]
    report_path = root / "coverage" / "coverage.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    report, passed = coverage_report(data, threshold)
    if os.environ.get("GITHUB_RUN_NUMBER"):
        run = os.environ["GITHUB_RUN_NUMBER"]
        commit = os.environ.get("COVERAGE_COMMIT", "unknown")[:7]
        report += (
            f"\nGenerated in workflow #{run} for commit `{commit}` with pytest-cov.\n"
        )
    (report_path.parent / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
