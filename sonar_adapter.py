"""
SonarQube and SonarCloud integration adapter.
Supports:
1. Ingestion of static SARIF reports (sonar-report.sarif).
2. Ingestion of SonarQube issues JSON exports (sonar-report.json).
3. Direct querying of SonarQube Web API via SONAR_HOST_URL and SONAR_TOKEN.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error
import base64

class SonarIssue:
    def __init__(self, rule: str, severity: str, file_path: str, line: int, message: str, issue_type: str = "CODE_SMELL"):
        self.rule = rule
        self.severity = severity.upper()
        self.file_path = file_path
        self.line = line
        self.message = message
        self.issue_type = issue_type.upper()

    def to_dict(self) -> Dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "file": self.file_path,
            "line": self.line,
            "message": self.message,
            "type": self.issue_type
        }

    def format_line(self) -> str:
        return f"- [{self.severity}] ({self.issue_type}) {self.file_path}:{self.line} - {self.rule}: {self.message}"

def parse_sonar_json(file_path: Path) -> List[SonarIssue]:
    """Parses SonarQube issues JSON report."""
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        issues = []
        for item in data.get("issues", []):
            component = item.get("component", "")
            if ":" in component:
                component = component.split(":", 1)[1]
            issues.append(SonarIssue(
                rule=item.get("rule", "unknown-rule"),
                severity=item.get("severity", "MAJOR"),
                file_path=component,
                line=item.get("line", 0),
                message=item.get("message", ""),
                issue_type=item.get("type", "CODE_SMELL")
            ))
        return issues
    except Exception as e:
        print(f"[WARN] Failed to parse Sonar JSON report {file_path}: {e}")
        return []

def parse_sarif_json(file_path: Path) -> List[SonarIssue]:
    """Parses SARIF format report (SARIF 2.1.0)."""
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        issues = []
        for run in data.get("runs", []):
            for result in run.get("results", []):
                rule_id = result.get("ruleId", "sarif-rule")
                level = result.get("level", "warning").lower()
                severity = "BLOCKER" if level == "error" else "MAJOR"
                message = result.get("message", {}).get("text", "")
                locations = result.get("locations", [])
                file_uri = ""
                line = 0
                if locations:
                    phys = locations[0].get("physicalLocation", {})
                    file_uri = phys.get("artifactLocation", {}).get("uri", "")
                    line = phys.get("region", {}).get("startLine", 0)
                issues.append(SonarIssue(
                    rule=rule_id,
                    severity=severity,
                    file_path=file_uri,
                    line=line,
                    message=message,
                    issue_type="VULNERABILITY" if severity == "BLOCKER" else "CODE_SMELL"
                ))
        return issues
    except Exception as e:
        print(f"[WARN] Failed to parse SARIF report {file_path}: {e}")
        return []

def fetch_sonar_api_issues() -> List[SonarIssue]:
    """Fetches unresolved pull request issues directly from SonarQube REST API if configured."""
    host = os.getenv("SONAR_HOST_URL")
    token = os.getenv("SONAR_TOKEN")
    project = os.getenv("SONAR_PROJECT_KEY")
    pr_number = os.getenv("PR_NUMBER")

    if not host or not token or not project:
        return []

    url = f"{host.rstrip('/')}/api/issues/search?componentKeys={project}&resolved=false"
    if pr_number:
        url += f"&pullRequest={pr_number}"

    try:
        req = urllib.request.Request(url)
        auth_bytes = base64.b64encode(f"{token}:".encode("utf-8")).decode("utf-8")
        req.add_header("Authorization", f"Basic {auth_bytes}")
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                issues = []
                for item in payload.get("issues", []):
                    comp = item.get("component", "")
                    if ":" in comp:
                        comp = comp.split(":", 1)[1]
                    issues.append(SonarIssue(
                        rule=item.get("rule", "api-rule"),
                        severity=item.get("severity", "MAJOR"),
                        file_path=comp,
                        line=item.get("line", 0),
                        message=item.get("message", ""),
                        issue_type=item.get("type", "CODE_SMELL")
                    ))
                return issues
    except Exception as e:
        print(f"[WARN] Failed to query SonarQube Web API: {e}")
    return []

def extract_modified_files(diff_text: str) -> set:
    """Extracts the set of normalized file paths modified in the git diff."""
    files = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git a/"):
            parts = line.split()
            if len(parts) >= 4:
                b_path = parts[3]
                if b_path.startswith("b/"):
                    files.add(b_path[2:].strip())
        elif line.startswith("+++ b/"):
            path = line[6:].strip()
            if path and path != "/dev/null":
                files.add(path)
    return files

def get_sonar_report(workspace_dir: Path = Path("."), diff_text: str = "") -> str:
    """
    Collects SonarQube issues from files or direct API and formats them for agent consumption.
    If diff_text is provided, filters issues so only files touched in the diff affect the quality gate.
    """
    issues: List[SonarIssue] = []

    # Priority 1: Check local JSON report (both hyphen and underscore variants)
    json_path = workspace_dir / "sonar-report.json"
    if not json_path.exists():
        json_path = workspace_dir / "sonar_report.json"
    if json_path.exists():
        issues.extend(parse_sonar_json(json_path))

    # Priority 2: Check SARIF report (both hyphen and underscore variants)
    sarif_path = workspace_dir / "sonar-report.sarif"
    if not sarif_path.exists():
        sarif_path = workspace_dir / "sonar_report.sarif"
    if sarif_path.exists():
        issues.extend(parse_sarif_json(sarif_path))

    # Priority 3: Query Web API if configured and no local file found
    if not issues:
        issues.extend(fetch_sonar_api_issues())

    if not issues:
        return ""

    # Filter against active diff files if diff is present
    if diff_text.strip():
        modified_files = extract_modified_files(diff_text)
        if modified_files:
            active_issues = []
            historical_count = 0
            for issue in issues:
                # Match normalized file path or suffix
                if any(issue.file_path.endswith(f) or f.endswith(issue.file_path) for f in modified_files):
                    active_issues.append(issue)
                else:
                    historical_count += 1

            if not active_issues:
                if historical_count > 0:
                    return f"[PASSED] No SonarQube issues detected in modified files ({historical_count} pre-existing baseline issues on untouched files ignored)."
                return ""

            lines = [
                f"SonarQube detected {len(active_issues)} issue(s) on modified files (ignored {historical_count} pre-existing issues on untouched files):"
            ]
            for issue in active_issues[:30]:
                lines.append(issue.format_line())
            return "\n".join(lines)

    lines = [
        f"SonarQube detected {len(issues)} issue(s):"
    ]
    for issue in issues[:30]:  # Cap to top 30 issues to preserve prompt budget
        lines.append(issue.format_line())

    return "\n".join(lines)
