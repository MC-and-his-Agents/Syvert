#!/usr/bin/env python3
"""Minimal Loom repository mechanical self-check."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from fact_chain_support import inspect_fact_chain
from governance_surface import build_governance_surface
from loom_flow import repo_specific_requirements_payload
from runtime_paths import repo_local_root

TOP_LEVEL_DIRS = (
    ".codex",
    ".codex-plugin",
    "docs",
    "examples",
    "packages",
    "skills",
    "tools",
)

TOP_LEVEL_FILES = (
    "AGENTS.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "VISION.md",
)

AREA_READMES = (
    "docs/adoption/README.md",
    "docs/methodology/governance/README.md",
    "docs/methodology/harness/README.md",
    "skills/README.md",
    "docs/methodology/templates/README.md",
)

CORE_DOCS = (
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/loom-check.yml",
    ".github/workflows/node-installer-pr.yml",
    ".github/workflows/node-installer-release.yml",
    ".codex/INSTALL.md",
    ".codex-plugin/plugin.json",
    "docs/architecture/governance-design.md",
    "docs/architecture/harness-design.md",
    "docs/architecture/system-design.md",
    "docs/methodology/governance/principles.md",
    "docs/methodology/governance/review-model.md",
    "docs/methodology/governance/github-delivery-funnel.md",
    "docs/methodology/governance/spec-implementation-separation.md",
    "docs/methodology/governance/maturity-and-closing.md",
    "docs/methodology/governance/governance-maturity-model.md",
    "docs/methodology/governance/state-machine.md",
    "docs/methodology/governance/truth-and-sync-boundary.md",
    "docs/methodology/governance/host-object-taxonomy.md",
    "docs/methodology/harness/work-item-contract.md",
    "docs/methodology/harness/item-context-contract.md",
    "docs/methodology/harness/fact-chain-contract.md",
    "docs/methodology/harness/execution-context.md",
    "docs/methodology/harness/execution-chain.md",
    "docs/methodology/harness/checkpoint-model.md",
    "docs/methodology/harness/workspace-model.md",
    "docs/methodology/harness/workspace-lifecycle.md",
    "docs/methodology/harness/host-action-contract.md",
    "docs/methodology/harness/host-lifecycle-boundary.md",
    "docs/methodology/harness/reconciliation-audit.md",
    "docs/methodology/harness/recovery-model.md",
    "docs/methodology/harness/review-execution.md",
    "docs/methodology/harness/status-surface.md",
    "docs/methodology/harness/automation-frontload.md",
    "docs/methodology/harness/merge-checkpoint.md",
    "docs/methodology/harness/closeout-gate.md",
    "docs/methodology/harness/gate-chain.md",
    "docs/methodology/harness/controlled-merge.md",
    "docs/methodology/harness/governance-failure-taxonomy.md",
    "docs/methodology/harness/workspace-and-purity.md",
    "docs/methodology/templates/spec-suite.md",
    "docs/methodology/templates/spec-template.md",
    "docs/methodology/templates/implementation-contract-template.md",
    "docs/methodology/templates/pull-request.md",
    "docs/evidence/extraction-ledger.md",
    "docs/evidence/landing-map.md",
    "docs/evidence/validations/validation-closeout-reconciliation-blocking-gate.md",
    "docs/evidence/validations/validation-adoption-maturity-upgrade-automation.md",
    "docs/evidence/validations/validation-adoption-maturity-required-fields.md",
    "docs/evidence/validations/validation-skills-consume-maturity-upgrade-path.md",
    "docs/evidence/validations/validation-github-profile-binding-orchestration.md",
    "docs/evidence/validations/validation-github-profile-drift-reconciliation.md",
    "docs/evidence/validations/validation-github-profile-graphql-budget-guard.md",
    "docs/evidence/validations/validation-loom-core-runtime-parity.md",
    "docs/evidence/validations/validation-shadow-parity-blocking-gate.md",
    "docs/evidence/validations/validation-syvert-strong-governance-parity.md",
    "docs/evidence/validations/validation-syvert-reverse-consumption-smoke.md",
    "docs/evidence/syvert-residue-closeout.md",
    "docs/evidence/validations/validation-syvert-runtime-parity-release-judgment.md",
    "docs/adoption/rationale.md",
    "docs/adoption/routing-and-checkpoints.md",
    "docs/adoption/github-profile.md",
    "docs/adoption/github-profile-upgrade.md",
    "docs/adoption/lightweight-retrofit-default.md",
    "docs/adoption/repo-companion-contract.md",
    "docs/adoption/repo-interop-contract.md",
    "skills/distribution-and-adapter-contract.md",
    "skills/registry.json",
    "skills/install-layout.json",
    "skills/upgrade-contract.json",
    "skills/route-matrix.md",
    "skills/loom-init/SKILL.md",
    "skills/loom-init/contract.json",
    "skills/loom-init/references/input-signals.md",
    "skills/loom-init/references/intake-signals.md",
    "skills/loom-init/references/output-contract.md",
    "skills/loom-review/SKILL.md",
    "skills/loom-review/contract.json",
    "skills/loom-review/references/input-signals.md",
    "skills/loom-review/references/output-contract.md",
    "skills/loom-spec-review/SKILL.md",
    "skills/loom-spec-review/contract.json",
    "skills/loom-spec-review/references/input-signals.md",
    "skills/loom-spec-review/references/output-contract.md",
    "docs/methodology/templates/review-record.md",
    "docs/methodology/templates/scaffold/spec.md",
    "docs/methodology/templates/scaffold/plan.md",
    "tools/loom_status.py",
    "packages/loom-installer/README.md",
    "packages/loom-installer/package.json",
    "packages/loom-installer/package-lock.json",
    "packages/loom-installer/tsconfig.json",
    "packages/loom-installer/scripts/build-payload.mjs",
    "packages/loom-installer/scripts/check-doc-sync.mjs",
    "packages/loom-installer/scripts/check-payload-drift.mjs",
    "packages/loom-installer/scripts/check-version-bump.mjs",
    "packages/loom-installer/src/cli.ts",
    "packages/loom-installer/src/index.ts",
    "packages/loom-installer/test/installer.test.ts",
    "tools/loom_init.py",
    "tools/loom_flow.py",
)

AUTOMATION_FRONTLOAD_TEMPLATES = (
    "docs/methodology/templates/spec-suite.md",
    "docs/methodology/templates/spec-template.md",
    "docs/methodology/templates/implementation-contract-template.md",
    "docs/methodology/templates/pull-request.md",
)

AUTOMATION_FRONTLOAD_SKILLS = (
    "skills/README.md",
    "skills/distribution-and-adapter-contract.md",
    "skills/install-layout.json",
    "skills/route-matrix.md",
    "skills/loom-init/SKILL.md",
    "skills/loom-init/references/input-signals.md",
    "skills/loom-init/references/intake-signals.md",
    "skills/loom-init/references/output-contract.md",
    "skills/loom-spec-review/SKILL.md",
    "skills/loom-spec-review/references/input-signals.md",
    "skills/loom-spec-review/references/output-contract.md",
)

AUTOMATION_FRONTLOAD_EXECUTION_SUPPORT = (
    "docs/methodology/harness/work-item-contract.md",
    "docs/methodology/harness/execution-context.md",
    "docs/methodology/harness/execution-chain.md",
    "docs/methodology/harness/checkpoint-model.md",
    "docs/methodology/harness/workspace-model.md",
    "docs/methodology/harness/workspace-lifecycle.md",
    "docs/methodology/harness/recovery-model.md",
    "docs/methodology/harness/status-surface.md",
    "docs/methodology/harness/automation-frontload.md",
    "docs/methodology/harness/merge-checkpoint.md",
    "docs/methodology/harness/workspace-and-purity.md",
)

GENERATED_TRACKED_PATHS = (
    "plugins/loom",
    "packages/skills",
    "packages/loom-installer/payload",
)

DEMO_ASSETS = (
    "examples/new-project/.gitkeep",
    "examples/new-project/AGENTS.md",
    "examples/new-project/.github/PULL_REQUEST_TEMPLATE.md",
    "examples/new-project/.loom/bootstrap/init-result.json",
    "examples/new-project/.loom/bootstrap/manifest.json",
    "examples/new-project/.loom/work-items/INIT-0001.md",
    "examples/new-project/.loom/progress/INIT-0001.md",
    "examples/new-project/.loom/reviews/INIT-0001.json",
    "examples/new-project/.loom/reviews/INIT-0001.spec.json",
    "examples/new-project/.loom/status/current.md",
    "examples/new-project/.loom/bin/loom_init.py",
    "examples/new-project/.loom/bin/fact_chain_support.py",
    "examples/new-project/.loom/bin/runtime_paths.py",
    "examples/new-project/.loom/bin/runtime_state.py",
    "examples/new-project/.loom/bin/loom_flow.py",
    "examples/new-project/.loom/bin/loom_status.py",
    "examples/new-project/.loom/bin/loom_check.py",
    "examples/new-project/.loom/specs/INIT-0001/spec.md",
    "examples/new-project/.loom/specs/INIT-0001/plan.md",
    "examples/new-project/.loom/specs/INIT-0001/implementation-contract.md",
)

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+\s*)?$")
CODE_FENCE_RE = re.compile(r"^(```|~~~)")
EXTERNAL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


@dataclass(frozen=True)
class Failure:
    category: str
    detail: str


GOVERNANCE_SURFACE_ROUTE_SKILLS = {
    "loom-adopt",
    "loom-resume",
}

GOVERNANCE_SURFACE_CONTRACT_SKILLS = {
    "loom-adopt",
    "loom-resume",
}

REVIEW_FINDING_SEVERITIES = {"warn", "block"}
REVIEW_FINDING_DISPOSITION_STATUSES = {"accepted", "rejected", "deferred"}
REPO_INTERFACE_AVAILABILITY = {"absent", "companion_docs_only", "incomplete", "present"}
REPO_INTERFACE_ENFORCEMENT = {"blocking", "advisory"}
REPO_INTEROP_AVAILABILITY = {"absent", "incomplete", "present"}


def repo_root_from_argv(argv: list[str]) -> Path:
    if len(argv) > 2:
        raise SystemExit("usage: loom_check.py [repo-root]")
    if len(argv) == 2:
        return Path(argv[1]).expanduser().resolve()
    hinted_root = repo_local_root(__file__)
    if hinted_root is not None:
        return hinted_root
    current = Path.cwd().resolve()
    if (current / "skills").exists() and (current / "README.md").exists():
        return current
    return Path(__file__).resolve().parent.parent


def check_required_paths(root: Path, category: str, paths: tuple[str, ...]) -> list[Failure]:
    failures: list[Failure] = []
    for relative_path in paths:
        if not (root / relative_path).exists():
            failures.append(Failure(category, f"missing `{relative_path}`"))
    return failures


def iter_markdown_files(root: Path) -> list[Path]:
    skipped_parts = {
        ".git",
        "node_modules",
        "dist",
        "payload",
        "packages/skills",
        "plugins/loom",
    }
    results: list[Path] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(relative == part or relative.startswith(f"{part}/") for part in skipped_parts):
            continue
        if any(part.startswith(".payload-build-") for part in path.relative_to(root).parts):
            continue
        if relative.startswith("packages/loom-installer/payload/"):
            continue
        results.append(path)
    return sorted(results)


def split_link_target(raw_target: str) -> tuple[str, str]:
    target = raw_target.strip()
    if not target:
        return "", ""
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    if "#" in target:
        path_part, fragment = target.split("#", 1)
        return path_part, fragment
    return target, ""


def markdown_links(path: Path) -> list[tuple[int, str]]:
    results: list[tuple[int, str]] = []
    in_code_fence = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if CODE_FENCE_RE.match(line.strip()):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        for match in LINK_RE.finditer(line):
            results.append((line_no, match.group(1)))
    return results


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    return text


def github_anchor_map(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    cached = cache.get(path)
    if cached is not None:
        return cached

    anchors: set[str] = set()
    duplicates: Counter[str] = Counter()
    in_code_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if CODE_FENCE_RE.match(stripped):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = github_slug(strip_inline_markdown(match.group(2)))
        if not base:
            continue
        duplicates[base] += 1
        anchor = base if duplicates[base] == 1 else f"{base}-{duplicates[base] - 1}"
        anchors.add(anchor)

    cache[path] = anchors
    return anchors


def github_slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).lower().strip()
    slug_chars: list[str] = []
    last_was_dash = False
    for char in text:
        if char.isspace() or char == "-":
            if slug_chars and not last_was_dash:
                slug_chars.append("-")
                last_was_dash = True
            continue

        category = unicodedata.category(char)
        if category[0] in {"L", "N"} or category == "Mn":
            slug_chars.append(char)
            last_was_dash = False

    return "".join(slug_chars).strip("-")


def resolve_link_target(root: Path, source_path: Path, raw_target: str) -> tuple[Path | None, str]:
    target, fragment = split_link_target(raw_target)
    if not target:
        return source_path, fragment
    if EXTERNAL_SCHEME_RE.match(target) or target.startswith("//"):
        return None, ""
    if target.startswith("/"):
        return None, ""

    resolved = (source_path.parent / target).resolve()
    if resolved.exists():
        return resolved, fragment
    if resolved.is_dir():
        readme = resolved / "README.md"
        if readme.exists():
            return readme, fragment
    try:
        resolved.relative_to(root)
    except ValueError:
        return resolved, fragment
    return resolved, fragment


def check_markdown_links(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    anchor_cache: dict[Path, set[str]] = {}
    for markdown_path in iter_markdown_files(root):
        for line_no, raw_target in markdown_links(markdown_path):
            resolved, fragment = resolve_link_target(root, markdown_path, raw_target)
            if resolved is None:
                continue
            if not resolved.exists():
                detail = (
                    f"`{markdown_path.relative_to(root)}:{line_no}` -> `{raw_target}` "
                    f"(missing `{resolved.relative_to(root) if resolved.is_absolute() and is_within(resolved, root) else resolved}`)"
                )
                failures.append(Failure("markdown-links", detail))
                continue
            if fragment and resolved.suffix.lower() == ".md":
                anchors = github_anchor_map(resolved, anchor_cache)
                if fragment not in anchors:
                    detail = (
                        f"`{markdown_path.relative_to(root)}:{line_no}` -> `{raw_target}` "
                        f"(missing anchor `#{fragment}` in `{resolved.relative_to(root)}`)"
                    )
                    failures.append(Failure("markdown-links", detail))
    return failures


def load_json_file(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_command(
    root: Path,
    args: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    for key in ("LOOM_SOURCE_REPO_ROOT", "LOOM_INSTALLED_SKILLS_ROOT", "LOOM_RUNTIME_SCENE"):
        command_env.pop(key, None)
    if env:
        command_env.update(env)
    return subprocess.run(
        args,
        cwd=cwd or root,
        check=False,
        capture_output=True,
        text=True,
        env=command_env,
        timeout=timeout_seconds,
    )


def load_command_json(
    root: Path,
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> tuple[dict[str, object] | None, str | None]:
    try:
        result = run_command(root, args, cwd=cwd, env=env, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired:
        return None, f"command timed out after {int(timeout_seconds or 0)}s"
    if not result.stdout.strip():
        detail = "command produced no JSON output"
        if result.stderr.strip():
            detail += f": {result.stderr.strip()}"
        return None, detail
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON output: {exc.msg}"
    if not isinstance(payload, dict):
        return None, "command output must be a JSON object"
    return payload, None


def load_command_json_with_retry(
    root: Path,
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
    retries: int = 2,
) -> tuple[dict[str, object] | None, str | None]:
    transient_needles = (
        "EOF",
        "unknown owner type",
        "command timed out",
        "connection reset",
        "TLS handshake timeout",
    )
    last_payload: dict[str, object] | None = None
    last_error: str | None = None
    for _ in range(retries):
        payload, error = load_command_json(
            root,
            args,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
        )
        if error is None:
            return payload, None
        last_payload = payload
        last_error = error
        if not any(needle in error for needle in transient_needles):
            return payload, error
    return last_payload, last_error


def payload_has_github_rate_limit(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    missing_inputs = payload.get("missing_inputs")
    if not isinstance(missing_inputs, list):
        return False
    return any(isinstance(item, str) and "API rate limit exceeded" in item for item in missing_inputs)


def prepend_path_env(bin_dir: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(extra or {})
    current_path = os.environ.get("PATH", "")
    env["PATH"] = str(bin_dir) if not current_path else f"{bin_dir}:{current_path}"
    return env


def write_fake_codex(
    path: Path,
    *,
    mode: str,
    tracked_edit_target: str | None = None,
) -> None:
    if mode == "success":
        body = """#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
output_path = pathlib.Path(args[args.index("-o") + 1])
payload = {
    "decision": "allow",
    "summary": "Default Codex reviewer found the item ready for merge checkpoint consumption.",
    "findings": [
        {
            "id": "warn-1",
            "summary": "Keep the follow-up validation note visible in the review record.",
            "severity": "warn",
            "rebuttal": None,
            "disposition": {
                "status": "accepted",
                "summary": "The reviewer accepts the current validation coverage."
            },
            "details": "This finding is advisory and should not block merge-ready."
        }
    ]
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
sys.exit(0)
"""
    elif mode == "schema_drift":
        body = """#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
output_path = pathlib.Path(args[args.index("-o") + 1])
payload = {
    "decision": "allow",
    "findings": []
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
sys.exit(0)
"""
    elif mode == "tracked_edit":
        target = tracked_edit_target or ""
        body = f"""#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
cwd = pathlib.Path(args[args.index("-C") + 1])
output_path = pathlib.Path(args[args.index("-o") + 1])
target = cwd / {target!r}
target.write_text(target.read_text(encoding="utf-8") + "\\ntracked edit from fake codex\\n", encoding="utf-8")
payload = {{
    "decision": "block",
    "summary": "Tracked repository content was modified during review.",
    "findings": [
        {{
            "id": "block-1",
            "summary": "Tracked repo content changed during review execution.",
            "severity": "block",
            "rebuttal": None,
            "disposition": {{
                "status": "rejected",
                "summary": "The run must fail closed."
            }}
        }}
    ]
}}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
sys.exit(0)
"""
    else:
        raise ValueError(f"unknown fake codex mode: {mode}")
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def require_governance_surface(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: dict[str, object],
) -> None:
    governance_surface = payload.get("governance_surface")
    if not isinstance(governance_surface, dict):
        failures.append(Failure(category, f"{context} must include `governance_surface` as an object"))
        return

    required_keys = (
        "repository_mode",
        "loom_state",
        "carrier_summary",
        "execution_entry",
        "validation_entry",
        "review_merge_surface",
        "github_control_plane",
        "repo_interface",
        "repo_interop",
        "summary",
        "missing_inputs",
    )
    for key in required_keys:
        if key not in governance_surface:
            failures.append(Failure(category, f"{context} governance_surface must include `{key}`"))

    for key in ("repository_mode", "loom_state", "execution_entry", "validation_entry", "summary"):
        if key in governance_surface and (not isinstance(governance_surface.get(key), str) or not governance_surface.get(key)):
            failures.append(Failure(category, f"{context} governance_surface `{key}` must be a non-empty string"))
    if governance_surface.get("repository_mode") not in {"new", "small-existing", "complex-existing"}:
        failures.append(Failure(category, f"{context} governance_surface `repository_mode` must stay within the stable contract"))
    if governance_surface.get("loom_state") not in {"active", "partial", "absent"}:
        failures.append(Failure(category, f"{context} governance_surface `loom_state` must stay within the stable contract"))

    missing_inputs = governance_surface.get("missing_inputs")
    if missing_inputs is not None and not isinstance(missing_inputs, list):
        failures.append(Failure(category, f"{context} governance_surface `missing_inputs` must be a list"))

    carrier_summary = governance_surface.get("carrier_summary")
    if not isinstance(carrier_summary, dict):
        failures.append(Failure(category, f"{context} governance_surface must include `carrier_summary`"))
    else:
        required_carriers = ("work_item", "recovery", "review", "status_surface", "spec_path", "plan_path")
        if set(carrier_summary.keys()) != set(required_carriers):
            failures.append(Failure(category, f"{context} governance_surface carrier keys must stay within the stable contract"))
        for carrier in required_carriers:
            entry = carrier_summary.get(carrier)
            if not isinstance(entry, dict):
                failures.append(Failure(category, f"{context} governance_surface carrier `{carrier}` must be an object"))
                continue
            if entry.get("status") not in {"present", "missing", "planned"}:
                failures.append(
                    Failure(category, f"{context} governance_surface carrier `{carrier}` status must stay within the stable contract")
                )
            for field in ("locator", "source"):
                value = entry.get(field)
                if not isinstance(value, str) or not value:
                    failures.append(
                        Failure(category, f"{context} governance_surface carrier `{carrier}` must include non-empty `{field}`")
                    )

    review_merge_surface = governance_surface.get("review_merge_surface")
    if review_merge_surface is not None and not isinstance(review_merge_surface, dict):
        failures.append(Failure(category, f"{context} governance_surface `review_merge_surface` must be an object"))
    elif isinstance(review_merge_surface, dict):
        for key in ("pr_template", "validation_surface", "merge_surface"):
            value = review_merge_surface.get(key)
            if not isinstance(value, str) or not value:
                failures.append(Failure(category, f"{context} governance_surface `review_merge_surface.{key}` must be a non-empty string"))

    github_control_plane = governance_surface.get("github_control_plane")
    if github_control_plane is not None and not isinstance(github_control_plane, dict):
        failures.append(Failure(category, f"{context} governance_surface `github_control_plane` must be an object"))
    elif isinstance(github_control_plane, dict):
        for key in ("repository", "default_branch", "branch_protection", "required_checks", "pr_reviews"):
            if key not in github_control_plane:
                failures.append(Failure(category, f"{context} governance_surface `github_control_plane.{key}` must exist"))
        for key in ("repository", "default_branch"):
            value = github_control_plane.get(key)
            if not isinstance(value, str) or not value:
                failures.append(Failure(category, f"{context} governance_surface `github_control_plane.{key}` must be a non-empty string"))
        if github_control_plane.get("branch_protection") not in {"enabled", "disabled", "unknown"}:
            failures.append(Failure(category, f"{context} governance_surface `github_control_plane.branch_protection` must stay within the stable contract"))
        if github_control_plane.get("pr_reviews") not in {"required", "not_required", "unknown"}:
            failures.append(Failure(category, f"{context} governance_surface `github_control_plane.pr_reviews` must stay within the stable contract"))
        required_checks = github_control_plane.get("required_checks")
        if not (
            required_checks == "unknown"
            or (isinstance(required_checks, list) and all(isinstance(item, str) and item for item in required_checks))
        ):
            failures.append(Failure(category, f"{context} governance_surface `github_control_plane.required_checks` must be `unknown` or a string list"))

    require_repo_interface_payload(
        failures,
        category=category,
        context=f"{context} governance_surface.repo_interface",
        payload=governance_surface.get("repo_interface"),
    )
    require_repo_interop_payload(
        failures,
        category=category,
        context=f"{context} governance_surface.repo_interop",
        payload=governance_surface.get("repo_interop"),
    )
    require_governance_control_plane(
        failures,
        category=category,
        context=f"{context} governance_surface.governance_control_plane",
        payload=governance_surface.get("governance_control_plane"),
    )


def require_governance_control_plane(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("schema_version") != "loom-governance-control/v1":
        failures.append(Failure(category, f"{context} schema_version must be `loom-governance-control/v1`"))
    execution_entry = payload.get("execution_entry")
    if not isinstance(execution_entry, dict):
        failures.append(Failure(category, f"{context}.execution_entry must be an object"))
    else:
        if execution_entry.get("only_default_entry") != "work_item":
            failures.append(Failure(category, f"{context}.execution_entry must keep `work_item` as the only default entry"))
        if execution_entry.get("result") not in {"pass", "block"}:
            failures.append(Failure(category, f"{context}.execution_entry.result must be `pass` or `block`"))
        fallbacks = execution_entry.get("illegal_entry_fallbacks")
        if not isinstance(fallbacks, dict) or fallbacks.get("fr") != "work_item" or fallbacks.get("implementation_pr") != "work_item":
            failures.append(Failure(category, f"{context}.execution_entry must fail closed from FR/PR back to Work Item"))

    host_binding = payload.get("host_binding")
    if not isinstance(host_binding, dict):
        failures.append(Failure(category, f"{context}.host_binding must be an object"))
    else:
        if host_binding.get("schema_version") != "loom-host-binding/v1":
            failures.append(Failure(category, f"{context}.host_binding schema_version must be `loom-host-binding/v1`"))
        if host_binding.get("result") not in {"pass", "block"}:
            failures.append(Failure(category, f"{context}.host_binding.result must be `pass` or `block`"))
        required_objects = host_binding.get("required_objects")
        expected_objects = {"phase", "fr", "work_item", "branch", "worktree", "implementation_pr", "merge_commit", "closeout"}
        if not isinstance(required_objects, dict) or set(required_objects) != expected_objects:
            failures.append(Failure(category, f"{context}.host_binding.required_objects must expose the stable host binding object set"))
        elif required_objects.get("work_item", {}).get("authority") != "loom fact chain":
            failures.append(Failure(category, f"{context}.host_binding work_item authority must remain Loom fact chain"))

    taxonomy = payload.get("taxonomy")
    expected_taxonomy = {
        "spec_stale",
        "review_stale",
        "head_drift",
        "host_signal_drift",
        "gate_failure",
        "closeout_reconciliation_drift",
    }
    if not isinstance(taxonomy, dict) or not expected_taxonomy.issubset(set(taxonomy)):
        failures.append(Failure(category, f"{context}.taxonomy must expose the stable stale/drift/gate-failure keys"))

    gate_chain = payload.get("gate_chain")
    expected_gate_order = [
        "work_item_admission",
        "spec_gate",
        "build_gate",
        "review_gate",
        "merge_gate",
        "github_controlled_merge",
        "closeout",
    ]
    if not isinstance(gate_chain, list):
        failures.append(Failure(category, f"{context}.gate_chain must be a list"))
    else:
        gate_order = [entry.get("id") for entry in gate_chain if isinstance(entry, dict)]
        if gate_order != expected_gate_order:
            failures.append(Failure(category, f"{context}.gate_chain must preserve the strong governance gate order"))
        for entry in gate_chain:
            if not isinstance(entry, dict):
                failures.append(Failure(category, f"{context}.gate_chain entries must be objects"))
                continue
            if not isinstance(entry.get("requires"), list):
                failures.append(Failure(category, f"{context}.gate_chain `{entry.get('id')}` must declare `requires`"))
            if entry.get("fallback_to") not in {"admission", "build", "review", "merge", "reconciliation-sync"}:
                failures.append(Failure(category, f"{context}.gate_chain `{entry.get('id')}` fallback_to is outside the stable set"))

    maturity = payload.get("maturity")
    if not isinstance(maturity, dict):
        failures.append(Failure(category, f"{context}.maturity must be an object"))
    else:
        if maturity.get("schema_version") != "loom-governance-maturity/v1":
            failures.append(Failure(category, f"{context}.maturity schema_version must be `loom-governance-maturity/v1`"))
        if maturity.get("current") not in {"unadopted", "light", "standard", "strong"}:
            failures.append(Failure(category, f"{context}.maturity current must stay within the stable levels"))
        levels = maturity.get("levels")
        if not isinstance(levels, dict) or set(levels) != {"light", "standard", "strong"}:
            failures.append(Failure(category, f"{context}.maturity levels must define light, standard, and strong"))
        standard_requires = levels.get("standard", {}).get("requires") if isinstance(levels, dict) and isinstance(levels.get("standard"), dict) else None
        expected_standard_requires = {
            "light",
            "fr_work_item_layer",
            "spec_path",
            "plan_path",
            "spec_gate",
            "status_control_plane",
            "basic_host_binding",
            "closeout_reconciliation_read",
        }
        if not isinstance(standard_requires, list) or set(standard_requires) != expected_standard_requires:
            failures.append(Failure(category, f"{context}.maturity standard level must require the full governance control plane"))
        strong_requires = levels.get("strong", {}).get("requires") if isinstance(levels, dict) and isinstance(levels.get("strong"), dict) else None
        if not isinstance(strong_requires, list) or "github_controlled_merge" not in strong_requires:
            failures.append(Failure(category, f"{context}.maturity strong level must require GitHub controlled merge"))
        required_fields = maturity.get("required_fields")
        if not isinstance(required_fields, dict) or set(required_fields) != {"light", "standard", "strong"}:
            failures.append(Failure(category, f"{context}.maturity required_fields must define light, standard, and strong"))
        else:
            for level, rows in required_fields.items():
                if not isinstance(rows, list) or not rows:
                    failures.append(Failure(category, f"{context}.maturity required_fields.{level} must be a non-empty list"))
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        failures.append(Failure(category, f"{context}.maturity required_fields.{level} entries must be objects"))
                        continue
                    if row.get("layer") not in {"core", "github-profile", "repo-owned-residue"}:
                        failures.append(Failure(category, f"{context}.maturity required_fields.{level} layer must be stable"))
                    if not isinstance(row.get("recommended_action"), str) or not row.get("recommended_action"):
                        failures.append(Failure(category, f"{context}.maturity required_fields.{level} entries must include recommended_action"))
        missing_details = maturity.get("missing_details_by_level")
        if not isinstance(missing_details, dict) or set(missing_details) != {"light", "standard", "strong"}:
            failures.append(Failure(category, f"{context}.maturity missing_details_by_level must define light, standard, and strong"))


def require_locator_entry(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    allowed_statuses: set[str],
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("status") not in allowed_statuses:
        failures.append(Failure(category, f"{context} status must stay within the stable contract"))
    for field in ("locator", "source"):
        value = payload.get(field)
        if not isinstance(value, str) or not value:
            failures.append(Failure(category, f"{context} must include non-empty `{field}`"))


def require_repo_interface_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("availability") not in REPO_INTERFACE_AVAILABILITY:
        failures.append(Failure(category, f"{context} availability must stay within the stable contract"))
    require_locator_entry(
        failures,
        category=category,
        context=f"{context}.manifest",
        payload=payload.get("manifest"),
        allowed_statuses={"present", "missing"},
    )
    for key in ("companion_entry", "repo_specific_requirements", "specialized_gates"):
        require_locator_entry(
            failures,
            category=category,
            context=f"{context}.{key}",
            payload=payload.get(key),
            allowed_statuses={"present", "missing"},
        )
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs` as a list"))


def require_repo_interop_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("availability") not in REPO_INTEROP_AVAILABILITY:
        failures.append(Failure(category, f"{context} availability must stay within the stable contract"))
    require_locator_entry(
        failures,
        category=category,
        context=f"{context}.contract",
        payload=payload.get("contract"),
        allowed_statuses={"present", "missing"},
    )
    for key in ("host_adapters", "repo_native_carriers", "shadow_surfaces"):
        require_locator_entry(
            failures,
            category=category,
            context=f"{context}.{key}",
            payload=payload.get(key),
            allowed_statuses={"present", "missing"},
        )
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs` as a list"))


def require_repo_specific_requirements_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    expected_surface: str,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("surface") != expected_surface:
        failures.append(Failure(category, f"{context} must report `surface: {expected_surface}`"))
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} result must be `pass` or `block`"))
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs`"))
    if payload.get("fallback_to") not in {None, "build", "merge"}:
        failures.append(Failure(category, f"{context} fallback must stay within the stable contract"))
    for key in ("declared_requirements", "blocking_requirements", "advisory_requirements"):
        entries = payload.get(key)
        if not isinstance(entries, list):
            failures.append(Failure(category, f"{context} must include `{key}` as a list"))
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                failures.append(Failure(category, f"{context} {key}[{index}] must be an object"))
                continue
            for field in ("id", "summary", "locator", "enforcement"):
                value = entry.get(field)
                if not isinstance(value, str) or not value:
                    failures.append(Failure(category, f"{context} {key}[{index}] missing `{field}`"))
            if entry.get("enforcement") not in REPO_INTERFACE_ENFORCEMENT:
                failures.append(Failure(category, f"{context} {key}[{index}] enforcement must stay within the stable contract"))
    declared = payload.get("declared_requirements")
    blocking = payload.get("blocking_requirements")
    advisory = payload.get("advisory_requirements")
    if isinstance(declared, list) and isinstance(blocking, list) and isinstance(advisory, list):
        if len(declared) != len(blocking) + len(advisory):
            failures.append(Failure(category, f"{context} declared requirements must split cleanly into blocking and advisory"))


def require_shadow_parity_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    expected_reports: int,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("command") != "shadow-parity":
        failures.append(Failure(category, f"{context} must report `command: shadow-parity`"))
    mode = payload.get("mode", "validation-only")
    if mode not in {"validation-only", "blocking"}:
        failures.append(Failure(category, f"{context} mode must be `validation-only` or `blocking`"))
    if payload.get("blocking") != (mode == "blocking"):
        failures.append(Failure(category, f"{context} blocking flag must match mode"))
    allowed_results = {"pass", "block"} if mode == "blocking" else {"pass", "warn"}
    if payload.get("result") not in allowed_results:
        failures.append(Failure(category, f"{context} result must stay within the stable mode-specific contract"))
    expected_fallbacks = {"manual-reconciliation"} if payload.get("result") == "block" else {None}
    if payload.get("fallback_to") not in expected_fallbacks:
        failures.append(Failure(category, f"{context} fallback_to must match the shadow parity enforcement mode"))
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs`"))
    require_runtime_state_payload(
        failures,
        category=category,
        context=context,
        payload=payload.get("runtime_state"),
        expected_scene="repo-local-demo",
        expected_carrier="repo-local-wrapper",
        allowed_results={"pass"},
    )
    governance_surface = {"governance_surface": payload.get("governance_surface")}
    if isinstance(payload.get("governance_surface"), dict):
        require_governance_surface(
            failures,
            category=category,
            context=context,
            payload=governance_surface,
        )
    reports = payload.get("reports")
    if not isinstance(reports, list):
        failures.append(Failure(category, f"{context} must include `reports` as a list"))
        return
    if len(reports) != expected_reports:
        failures.append(Failure(category, f"{context} must include {expected_reports} parity reports"))
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            failures.append(Failure(category, f"{context} reports[{index}] must be an object"))
            continue
        if report.get("surface") not in {"admission", "review", "merge_ready", "closeout"}:
            failures.append(Failure(category, f"{context} reports[{index}] must declare a known surface"))
        if report.get("result") not in {"match", "mismatch", "unreadable"}:
            failures.append(Failure(category, f"{context} reports[{index}] result must stay within the stable contract"))
        if report.get("classification") not in {None, "drift", "gate_failure"}:
            failures.append(Failure(category, f"{context} reports[{index}] classification must stay within the stable contract"))
        if not isinstance(report.get("blocking"), bool):
            failures.append(Failure(category, f"{context} reports[{index}] must include boolean `blocking`"))
        if not isinstance(report.get("recommended_action"), str) or not report.get("recommended_action"):
            failures.append(Failure(category, f"{context} reports[{index}] must include non-empty `recommended_action`"))
        if mode == "blocking" and report.get("result") != "match" and report.get("blocking") is not True:
            failures.append(Failure(category, f"{context} reports[{index}] must block non-matching reports in blocking mode"))
        if not isinstance(report.get("summary"), str) or not report.get("summary"):
            failures.append(Failure(category, f"{context} reports[{index}] must include non-empty `summary`"))
        if not isinstance(report.get("missing_inputs"), list):
            failures.append(Failure(category, f"{context} reports[{index}] must include `missing_inputs`"))
        for key in ("host_adapters", "repo_native_carriers"):
            if not isinstance(report.get(key), list):
                failures.append(Failure(category, f"{context} reports[{index}] must include `{key}` as a list"))
        for surface_key in ("loom_surface", "repo_surface"):
            surface_payload = report.get(surface_key)
            if not isinstance(surface_payload, dict):
                failures.append(Failure(category, f"{context} reports[{index}] must include `{surface_key}`"))
                continue
            if surface_payload.get("status") not in {"readable", "missing"}:
                failures.append(Failure(category, f"{context} reports[{index}] `{surface_key}.status` must stay within the stable contract"))
            locator = surface_payload.get("locator")
            if not isinstance(locator, str) or not locator:
                failures.append(Failure(category, f"{context} reports[{index}] `{surface_key}.locator` must be non-empty"))


def require_host_lifecycle_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: dict[str, object],
) -> None:
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} must return `pass` or `block`"))
    if payload.get("fallback_to") not in {None, "admission"}:
        failures.append(Failure(category, f"{context} fallback must be `null` or `admission`"))
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include a non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs`"))

    objects = payload.get("objects")
    if not isinstance(objects, dict):
        failures.append(Failure(category, f"{context} must include `objects`"))
        return

    workspace = objects.get("workspace")
    branch = objects.get("branch")
    pr = objects.get("pr")
    worktree = objects.get("worktree")
    for key, value in (("workspace", workspace), ("branch", branch), ("pr", pr), ("worktree", worktree)):
        if not isinstance(value, dict):
            failures.append(Failure(category, f"{context} must include `{key}`"))
    if not isinstance(workspace, dict) or not isinstance(branch, dict) or not isinstance(pr, dict) or not isinstance(worktree, dict):
        return

    if workspace.get("ownership") != "loom":
        failures.append(Failure(category, f"{context} workspace ownership must stay `loom`"))
    for field in ("entry", "path", "lifecycle_entry"):
        value = workspace.get(field)
        if not isinstance(value, str) or not value:
            failures.append(Failure(category, f"{context} workspace must include non-empty `{field}`"))

    if branch.get("ownership") != "host":
        failures.append(Failure(category, f"{context} branch ownership must stay `host`"))
    if branch.get("purity_status") not in {"report_only", "host_managed_without_local_branch"}:
        failures.append(Failure(category, f"{context} branch purity_status must stay within the stable contract"))
    if not isinstance(branch.get("next_action"), str) or not branch.get("next_action"):
        failures.append(Failure(category, f"{context} branch must include non-empty `next_action`"))

    if pr.get("ownership") != "host":
        failures.append(Failure(category, f"{context} PR ownership must stay `host`"))
    if pr.get("purity_status") != "report_only":
        failures.append(Failure(category, f"{context} PR purity_status must stay `report_only`"))
    if not isinstance(pr.get("next_action"), str) or not pr.get("next_action"):
        failures.append(Failure(category, f"{context} PR must include non-empty `next_action`"))

    if worktree.get("ownership") != "host":
        failures.append(Failure(category, f"{context} worktree ownership must stay `host`"))
    if worktree.get("status") != "host_managed":
        failures.append(Failure(category, f"{context} worktree status must stay `host_managed`"))
    for field in ("cwd_within_repo", "next_action"):
        value = worktree.get(field)
        if not isinstance(value, str) or not value:
            failures.append(Failure(category, f"{context} worktree must include non-empty `{field}`"))


def require_reconciliation_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must include `reconciliation` as an object"))
        return
    if payload.get("command") != "reconciliation":
        failures.append(Failure(category, f"{context} must report `command: reconciliation`"))
    if payload.get("operation") != "audit":
        failures.append(Failure(category, f"{context} must report `operation: audit`"))
    if payload.get("result") not in {"pass", "warn", "fix-needed", "block"}:
        failures.append(Failure(category, f"{context} returned an unknown reconciliation result"))
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include a non-empty reconciliation `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include reconciliation `missing_inputs`"))
    if payload.get("fallback_to") not in {None, "manual-reconciliation"}:
        failures.append(Failure(category, f"{context} reconciliation fallback must be `null` or `manual-reconciliation`"))
    findings = payload.get("findings")
    if not isinstance(findings, list):
        failures.append(Failure(category, f"{context} must include reconciliation `findings` as a list"))
        return
    for finding in findings:
        if not isinstance(finding, dict):
            failures.append(Failure(category, f"{context} reconciliation findings must be JSON objects"))
            continue
        if finding.get("category") not in {"drift", "gate_failure"}:
            failures.append(Failure(category, f"{context} reconciliation finding category must stay within the stable taxonomy"))
        if finding.get("kind") not in {"merged_but_open", "absorbed_but_open", "parent_drift", "project_drift", "host_signal_drift", "binding_failure", "merge_signal_drift"}:
            failures.append(Failure(category, f"{context} reconciliation finding kind must stay within the stable contract"))
        if finding.get("severity") not in {"warn", "fix-needed", "block"}:
            failures.append(Failure(category, f"{context} reconciliation finding severity must stay within the stable contract"))
        if finding.get("fallback_to") not in {"reconciliation-sync", "manual-reconciliation", None}:
            failures.append(Failure(category, f"{context} reconciliation finding fallback_to must stay within the stable contract"))
        if not isinstance(finding.get("subject"), str) or not finding.get("subject"):
            failures.append(Failure(category, f"{context} reconciliation findings must include non-empty `subject`"))
        if not isinstance(finding.get("evidence"), dict):
            failures.append(Failure(category, f"{context} reconciliation findings must include `evidence`"))
        if not isinstance(finding.get("recommended_action"), str) or not finding.get("recommended_action"):
            failures.append(Failure(category, f"{context} reconciliation findings must include non-empty `recommended_action`"))
    binding = payload.get("binding")
    if binding is not None:
        if not isinstance(binding, dict):
            failures.append(Failure(category, f"{context} binding must be an object when present"))
        elif binding.get("schema_version") != "loom-github-binding/v1":
            failures.append(Failure(category, f"{context} binding must use `loom-github-binding/v1`"))


def require_closeout_reconciliation_contract(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: dict[str, object],
) -> None:
    reconciliation = payload.get("reconciliation")
    if reconciliation is None:
        return
    require_reconciliation_payload(
        failures,
        category=category,
        context=f"{context} reconciliation",
        payload=reconciliation,
    )
    if not isinstance(reconciliation, dict):
        return
    reconciliation_result = reconciliation.get("result")
    closeout_result = payload.get("result")
    fallback_to = payload.get("fallback_to")
    if reconciliation_result == "fix-needed":
        if closeout_result != "block":
            failures.append(Failure(category, f"{context} must block when reconciliation returns `fix-needed`"))
        if fallback_to != "reconciliation-sync":
            failures.append(Failure(category, f"{context} must point `fix-needed` reconciliation drift to `reconciliation-sync`"))
    if reconciliation_result == "block":
        if closeout_result != "block":
            failures.append(Failure(category, f"{context} must block when reconciliation returns `block`"))
        if fallback_to != "manual-reconciliation":
            failures.append(Failure(category, f"{context} must point blocked reconciliation drift to `manual-reconciliation`"))


def require_runtime_parity_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("command") != "runtime-parity":
        failures.append(Failure(category, f"{context} must report `command: runtime-parity`"))
    if payload.get("operation") != "validate":
        failures.append(Failure(category, f"{context} must report `operation: validate`"))
    if payload.get("schema_version") != "loom-runtime-parity/v1":
        failures.append(Failure(category, f"{context} schema_version must be `loom-runtime-parity/v1`"))
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} result must be `pass` or `block`"))
    if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
        failures.append(Failure(category, f"{context} must include a non-empty `summary`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs`"))
    if payload.get("fallback_to") not in {None, "admission", "merge", "reconciliation-sync", "manual-runtime-reconciliation", "rebootstrap-runtime", "refresh-install", "loom-init"}:
        failures.append(Failure(category, f"{context} fallback_to must stay within the stable runtime parity contract"))
    require_runtime_state_payload(
        failures,
        category=category,
        context=context,
        payload=payload.get("runtime_state"),
        expected_scene="repo-local-demo",
        expected_carrier="repo-local-wrapper",
        allowed_results={"pass"},
    )
    checks = payload.get("checks")
    if not isinstance(checks, list):
        failures.append(Failure(category, f"{context} must include `checks` as a list"))
        return
    required_checks = {
        "work_item",
        "status_control_plane",
        "gate_chain",
        "controlled_merge_contract",
        "closeout_reconciliation",
        "shadow_parity_boundary",
    }
    check_names = {check.get("name") for check in checks if isinstance(check, dict)}
    if not required_checks.issubset(check_names):
        failures.append(Failure(category, f"{context} must cover the stable runtime parity check set"))
    for check in checks:
        if not isinstance(check, dict):
            failures.append(Failure(category, f"{context} checks must be JSON objects"))
            continue
        if check.get("result") not in {"pass", "block"}:
            failures.append(Failure(category, f"{context} check `{check.get('name')}` result must be `pass` or `block`"))
        if not isinstance(check.get("summary"), str) or not check.get("summary"):
            failures.append(Failure(category, f"{context} check `{check.get('name')}` must include non-empty `summary`"))
        if not isinstance(check.get("missing_inputs"), list):
            failures.append(Failure(category, f"{context} check `{check.get('name')}` must include `missing_inputs`"))
        if not isinstance(check.get("evidence"), dict):
            failures.append(Failure(category, f"{context} check `{check.get('name')}` must include `evidence`"))


def require_github_binding_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("command") != "governance-profile":
        failures.append(Failure(category, f"{context} must report `command: governance-profile`"))
    if payload.get("operation") != "binding":
        failures.append(Failure(category, f"{context} must report `operation: binding`"))
    if payload.get("schema_version") != "loom-github-binding/v1":
        failures.append(Failure(category, f"{context} schema_version must be `loom-github-binding/v1`"))
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} result must be pass/block"))
    if payload.get("fallback_to") not in {None, "github-profile-binding"}:
        failures.append(Failure(category, f"{context} fallback_to must be null or `github-profile-binding`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} missing_inputs must be a list"))
    binding = payload.get("binding")
    if not isinstance(binding, dict):
        failures.append(Failure(category, f"{context} must include `binding` as an object"))
        return
    if binding.get("schema_version") != "loom-github-binding/v1":
        failures.append(Failure(category, f"{context}.binding schema_version must be `loom-github-binding/v1`"))
    objects = binding.get("objects")
    expected_objects = {"phase", "fr", "work_item", "branch", "implementation_pr", "merge_commit", "target_branch"}
    if not isinstance(objects, dict) or set(objects) != expected_objects:
        failures.append(Failure(category, f"{context}.binding.objects must expose the stable GitHub binding object set"))
    chain = binding.get("chain")
    expected_chain = [
        ("phase", "fr"),
        ("fr", "work_item"),
        ("work_item", "implementation_pr"),
        ("implementation_pr", "merge_commit"),
        ("merge_commit", "target_branch"),
    ]
    if not isinstance(chain, list):
        failures.append(Failure(category, f"{context}.binding.chain must be a list"))
    else:
        actual_chain = [
            (entry.get("from"), entry.get("to"))
            for entry in chain
            if isinstance(entry, dict)
        ]
        if actual_chain != expected_chain:
            failures.append(Failure(category, f"{context}.binding.chain must preserve Phase -> FR -> Work Item -> PR -> merge commit -> target branch order"))
        for entry in chain:
            if not isinstance(entry, dict):
                failures.append(Failure(category, f"{context}.binding.chain entries must be objects"))
                continue
            if entry.get("status") not in {"present", "missing"}:
                failures.append(Failure(category, f"{context}.binding.chain statuses must be present/missing"))
    findings = binding.get("findings")
    if not isinstance(findings, list):
        failures.append(Failure(category, f"{context}.binding.findings must be a list"))
        return
    for finding in findings:
        if not isinstance(finding, dict):
            failures.append(Failure(category, f"{context}.binding.findings entries must be objects"))
            continue
        if finding.get("category") not in {"stale", "drift", "gate_failure"}:
            failures.append(Failure(category, f"{context}.binding findings must use stable taxonomy categories"))
        if finding.get("kind") != "binding_failure":
            failures.append(Failure(category, f"{context}.binding findings must use `binding_failure` for orchestration gaps"))
        if finding.get("fallback_to") != "github-profile-binding":
            failures.append(Failure(category, f"{context}.binding findings must fallback to `github-profile-binding`"))


def require_governance_upgrade_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must be an object"))
        return
    if payload.get("command") != "governance-profile":
        failures.append(Failure(category, f"{context} must report `command: governance-profile`"))
    if payload.get("operation") != "upgrade":
        failures.append(Failure(category, f"{context} must report `operation: upgrade`"))
    if payload.get("schema_version") != "loom-governance-upgrade/v1":
        failures.append(Failure(category, f"{context} schema_version must be `loom-governance-upgrade/v1`"))
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} result must be pass/block"))
    if payload.get("target_maturity") not in {"standard", "strong"}:
        failures.append(Failure(category, f"{context} target_maturity must be standard/strong"))
    if not isinstance(payload.get("dry_run"), bool):
        failures.append(Failure(category, f"{context} dry_run must be boolean"))
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        failures.append(Failure(category, f"{context} must include non-empty actions"))
        return
    for action in actions:
        if not isinstance(action, dict):
            failures.append(Failure(category, f"{context} actions must be objects"))
            continue
        if action.get("owner") not in {"loom-owned", "repo-owned", "profile"}:
            failures.append(Failure(category, f"{context} action owner must stay within the stable set"))
        if action.get("status") not in {"planned", "present"}:
            failures.append(Failure(category, f"{context} action status must be planned/present"))
        if action.get("action") == "satisfy_missing_input" and not isinstance(action.get("recommended_action"), str):
            failures.append(Failure(category, f"{context} missing-input actions must include recommended_action"))


def require_maturity_upgrade_path(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must include maturity_upgrade_path"))
        return
    if payload.get("result") not in {"pass", "block"}:
        failures.append(Failure(category, f"{context} result must be pass/block"))
    if payload.get("current") not in {"unadopted", "light", "standard", "strong", "unknown"}:
        failures.append(Failure(category, f"{context} current maturity must stay within the stable set"))
    if payload.get("next") not in {None, "light", "standard", "strong"}:
        failures.append(Failure(category, f"{context} next maturity must stay within the stable set"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} missing_inputs must be a list"))
    if not isinstance(payload.get("missing_details"), list):
        failures.append(Failure(category, f"{context} missing_details must be a list"))
    if payload.get("fallback_to") not in {None, "adoption", "admission"}:
        failures.append(Failure(category, f"{context} fallback_to must be stable"))
    if payload.get("next") is not None and not isinstance(payload.get("upgrade_entry"), str):
        failures.append(Failure(category, f"{context} upgrade_entry must be present when next maturity exists"))
    validation_entries = payload.get("validation_entries")
    if not isinstance(validation_entries, list) or not validation_entries:
        failures.append(Failure(category, f"{context} validation_entries must be non-empty"))


def require_review_record_contract(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must include a review record object"))
        return
    findings = payload.get("findings")
    if not isinstance(findings, list):
        failures.append(Failure(category, f"{context} must include review `findings` as a list"))
        return
    for list_field in ("blocking_issues", "follow_ups"):
        if not isinstance(payload.get(list_field), list):
            failures.append(Failure(category, f"{context} must include review `{list_field}` as a list"))
    consumed_inputs = payload.get("consumed_inputs")
    if consumed_inputs is not None:
        if not isinstance(consumed_inputs, dict):
            failures.append(Failure(category, f"{context} review `consumed_inputs` must be an object when present"))
        else:
            for key in ("engine_adapter", "engine_evidence", "normalized_findings"):
                value = consumed_inputs.get(key)
                if value is not None and (not isinstance(value, str) or not value):
                    failures.append(Failure(category, f"{context} review consumed input `{key}` must be null or a non-empty string"))
    for finding in findings:
        if not isinstance(finding, dict):
            failures.append(Failure(category, f"{context} review findings must be JSON objects"))
            continue
        if not isinstance(finding.get("id"), str) or not finding.get("id"):
            failures.append(Failure(category, f"{context} review findings must include non-empty `id`"))
        if not isinstance(finding.get("summary"), str) or not finding.get("summary"):
            failures.append(Failure(category, f"{context} review findings must include non-empty `summary`"))
        if finding.get("severity") not in REVIEW_FINDING_SEVERITIES:
            failures.append(Failure(category, f"{context} review finding severity must stay within the stable contract"))
        rebuttal = finding.get("rebuttal")
        if rebuttal is not None and (not isinstance(rebuttal, str) or not rebuttal):
            failures.append(
                Failure(category, f"{context} review finding `rebuttal` must be `null` or a non-empty string")
            )
        disposition = finding.get("disposition")
        if disposition is not None:
            if not isinstance(disposition, dict):
                failures.append(Failure(category, f"{context} review finding disposition must be `null` or an object"))
                continue
            if disposition.get("status") not in REVIEW_FINDING_DISPOSITION_STATUSES:
                failures.append(Failure(category, f"{context} review finding disposition status must stay within the stable contract"))
            if not isinstance(disposition.get("summary"), str) or not disposition.get("summary"):
                failures.append(Failure(category, f"{context} review finding disposition must include non-empty `summary`"))


def require_review_run_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    expected_result: set[str],
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must return a JSON object"))
        return
    if payload.get("command") != "review":
        failures.append(Failure(category, f"{context} must report `command: review`"))
    if payload.get("operation") != "run":
        failures.append(Failure(category, f"{context} must report `operation: run`"))
    if payload.get("result") not in expected_result:
        failures.append(Failure(category, f"{context} returned an unexpected result"))
    for key in ("item", "state_check", "runtime_evidence", "build_checkpoint", "review", "current_checkpoint", "engine", "manual_review"):
        if not isinstance(payload.get(key), dict):
            failures.append(Failure(category, f"{context} must include `{key}`"))
    require_runtime_state_payload(
        failures,
        category=category,
        context=context,
        payload=payload.get("runtime_state"),
        allowed_results={"pass", "block"},
    )
    engine = payload.get("engine")
    if not isinstance(engine, dict):
        return
    if engine.get("engine") != "codex":
        failures.append(Failure(category, f"{context} engine must stay `codex` for the default path"))
    if engine.get("adapter") != "loom/default-codex":
        failures.append(Failure(category, f"{context} adapter must stay `loom/default-codex`"))
    if engine.get("result") not in {"pass", "block", "not_run"}:
        failures.append(Failure(category, f"{context} engine result must stay within the stable contract"))
    if engine.get("failure_reason") not in {None, "engine_unavailable", "schema_drift", "runtime_conflict", "repo_diff_detected"}:
        failures.append(Failure(category, f"{context} engine failure reason must stay within the stable contract"))
    evidence = engine.get("evidence")
    if engine.get("result") == "not_run":
        if evidence is not None:
            failures.append(Failure(category, f"{context} engine evidence must be null when the engine is not run"))
    else:
        if not isinstance(evidence, dict):
            failures.append(Failure(category, f"{context} engine must include `evidence` when it runs"))
        else:
            for key in ("runtime_root", "prompt", "raw_result", "normalized_findings", "metadata"):
                value = evidence.get(key)
                if not isinstance(value, str) or not value:
                    failures.append(Failure(category, f"{context} engine evidence must include non-empty `{key}`"))
    manual_review = payload.get("manual_review")
    if isinstance(manual_review, dict):
        if not isinstance(manual_review.get("summary"), str) or not manual_review.get("summary"):
            failures.append(Failure(category, f"{context} manual_review must include non-empty `summary`"))
        if not isinstance(manual_review.get("review_record_path"), str) or not manual_review.get("review_record_path"):
            failures.append(Failure(category, f"{context} manual_review must include `review_record_path`"))
        if manual_review.get("recommended_kind") not in {"general_review", "code_review", "spec_review"}:
            failures.append(Failure(category, f"{context} manual_review recommended kind must stay within the stable contract"))
        if not isinstance(manual_review.get("command"), list):
            failures.append(Failure(category, f"{context} manual_review must include `command` as a list"))
    review_record_input = payload.get("review_record_input")
    if payload.get("result") == "pass":
        if not isinstance(review_record_input, dict):
            failures.append(Failure(category, f"{context} must include `review_record_input` when engine review passes"))
        else:
            for key in ("decision", "summary", "reviewer", "kind", "findings_file", "engine_adapter", "engine_evidence", "normalized_findings"):
                value = review_record_input.get(key)
                if not isinstance(value, str) or not value:
                    failures.append(Failure(category, f"{context} review_record_input must include non-empty `{key}`"))
            if review_record_input.get("decision") not in {"allow", "block", "fallback"}:
                failures.append(Failure(category, f"{context} review_record_input decision must stay within the stable contract"))
            if review_record_input.get("reviewer") != "loom/default-codex":
                failures.append(Failure(category, f"{context} review_record_input reviewer must stay `loom/default-codex`"))


def require_runtime_state_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    expected_scene: str | None = None,
    expected_carrier: str | None = None,
    allowed_results: set[str] | None = None,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must include `runtime_state` as an object"))
        return
    if payload.get("result") not in (allowed_results or {"pass", "block"}):
        failures.append(Failure(category, f"{context} runtime_state.result must stay within the stable contract"))
    if expected_scene is not None and payload.get("scene") != expected_scene:
        failures.append(Failure(category, f"{context} runtime_state.scene must be `{expected_scene}`"))
    if expected_carrier is not None and payload.get("carrier") != expected_carrier:
        failures.append(Failure(category, f"{context} runtime_state.carrier must be `{expected_carrier}`"))
    if payload.get("entry_family") not in {"loom-init", "loom-flow"}:
        failures.append(Failure(category, f"{context} runtime_state.entry_family must stay within the stable contract"))
    if not isinstance(payload.get("runtime_root"), str) or not payload.get("runtime_root"):
        failures.append(Failure(category, f"{context} runtime_state must include non-empty `runtime_root`"))
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        failures.append(Failure(category, f"{context} runtime_state must include `checks`"))
        return
    for key in ("scene_marker", "carrier_layout", "registry_contract", "shared_runtime", "referenced_resources"):
        check = checks.get(key)
        if not isinstance(check, dict):
            failures.append(Failure(category, f"{context} runtime_state must include check `{key}`"))
            continue
        if check.get("status") not in {"pass", "block", "not_applicable"}:
            failures.append(Failure(category, f"{context} runtime_state check `{key}` returned an unknown status"))
        if not isinstance(check.get("summary"), str) or not check.get("summary"):
            failures.append(Failure(category, f"{context} runtime_state check `{key}` must include non-empty `summary`"))


def require_route_payload(
    failures: list[Failure],
    *,
    category: str,
    context: str,
    payload: object,
    expected_skill: str,
    expected_mode: str,
    expected_runtime_scene: str | None = None,
    expected_runtime_carrier: str | None = None,
    allowed_results: set[str] | None = None,
) -> None:
    if not isinstance(payload, dict):
        failures.append(Failure(category, f"{context} must return a JSON object"))
        return
    if payload.get("command") != "route":
        failures.append(Failure(category, f"{context} must report `command: route`"))
    if payload.get("result") not in (allowed_results or {"pass"}):
        failures.append(Failure(category, f"{context} result must stay within the stable contract"))
    if payload.get("selected_skill") != expected_skill:
        failures.append(Failure(category, f"{context} must select `{expected_skill}`"))
    if payload.get("mode") != expected_mode:
        failures.append(Failure(category, f"{context} must report `mode: {expected_mode}`"))
    if not isinstance(payload.get("matched_signals"), list):
        failures.append(Failure(category, f"{context} must include `matched_signals`"))
    if not isinstance(payload.get("missing_inputs"), list):
        failures.append(Failure(category, f"{context} must include `missing_inputs`"))
    if payload.get("fallback_to") not in {"loom-init", "refresh-install", "rebootstrap-runtime", "manual-runtime-reconciliation", None}:
        failures.append(Failure(category, f"{context} fallback must stay within the stable contract"))
    if expected_runtime_scene is not None or expected_runtime_carrier is not None:
        require_runtime_state_payload(
            failures,
            category=category,
            context=context,
            payload=payload.get("runtime_state"),
            expected_scene=expected_runtime_scene,
            expected_carrier=expected_runtime_carrier,
            allowed_results={"pass", "block"},
        )


def check_root_route_contracts(root: Path) -> list[Failure]:
    category = "skill-routing-contract"
    failures: list[Failure] = []
    readme_path = root / "README.md"
    readme_zh_path = root / "README.zh-CN.md"
    skills_readme_path = root / "skills/README.md"
    skills_readme_zh_path = root / "skills/README.zh-CN.md"
    route_matrix_path = root / "skills/route-matrix.md"
    contract_path = root / "skills/loom-init/contract.json"

    try:
        readme = load_text_file(readme_path)
        readme_zh = load_text_file(readme_zh_path)
        skills_readme = load_text_file(skills_readme_path)
        skills_readme_zh = load_text_file(skills_readme_zh_path)
        route_matrix = load_text_file(route_matrix_path)
        contract = load_json_file(contract_path)
    except FileNotFoundError:
        return failures
    except json.JSONDecodeError as exc:
        return [Failure(category, f"`skills/loom-init/contract.json` is invalid JSON: {exc.msg}")]

    if not isinstance(contract, dict):
        return [Failure(category, "`skills/loom-init/contract.json` must be a JSON object")]

    if "skills-first methodology repository" not in readme:
        failures.append(Failure(category, "`README.md` must present Loom as a skills-first methodology repository"))
    if "Advanced / Compatibility" not in readme:
        failures.append(Failure(category, "`README.md` must keep single-skill installation as an advanced compatibility path"))
    if "[中文版本](./README.zh-CN.md)" not in readme or "[English version](./README.md)" not in readme_zh:
        failures.append(Failure(category, "root README language switch links must stay in sync"))
    if "以 skills 为先的方法论仓库" not in readme_zh:
        failures.append(Failure(category, "`README.zh-CN.md` must preserve the Chinese repository positioning"))
    if "unique root entry" not in skills_readme:
        failures.append(Failure(category, "`skills/README.md` must keep `loom-init` as the unique root entry"))
    if "[中文版本](./README.zh-CN.md)" not in skills_readme or "[English version](./README.md)" not in skills_readme_zh:
        failures.append(Failure(category, "skills README language switch links must stay in sync"))
    if "唯一的 root entry" not in skills_readme_zh:
        failures.append(Failure(category, "`skills/README.zh-CN.md` must preserve the Chinese root-entry explanation"))
    if "显式 skill 名称调用优先" not in route_matrix:
        failures.append(Failure(category, "`skills/route-matrix.md` must keep explicit routing as the first priority"))
    if "若无法稳定判断，回退到 `loom-init`" not in route_matrix:
        failures.append(Failure(category, "`skills/route-matrix.md` must keep fallback-to-loom-init semantics"))
    if "`plugin` 与 `single-skill` 两类安装结果边界" not in route_matrix and "fallback_to: \"loom-init\"" not in route_matrix:
        failures.append(Failure(category, "`skills/route-matrix.md` must keep the stable fallback payload contract"))

    if contract.get("id") != "loom-init":
        failures.append(Failure(category, "`skills/loom-init/contract.json` id must remain `loom-init`"))
    if contract.get("root_entry") is not True:
        failures.append(Failure(category, "`skills/loom-init/contract.json` must keep `root_entry: true`"))

    routing = contract.get("routing")
    if not isinstance(routing, dict):
        failures.append(Failure(category, "`skills/loom-init/contract.json` must declare `routing`"))
    else:
        if routing.get("reference") != "../route-matrix.md":
            failures.append(Failure(category, "`skills/loom-init/contract.json` must reference `../route-matrix.md`"))
        if routing.get("fallback_entry") != "loom-init":
            failures.append(Failure(category, "`skills/loom-init/contract.json` fallback entry must remain `loom-init`"))
        if routing.get("priority_order") != [
            "explicit skill name",
            "task signal routing",
            "fallback to loom-init with missing inputs",
        ]:
            failures.append(Failure(category, "`skills/loom-init/contract.json` routing priority order drifted from the stable contract"))

    installation_commands = (
        "npx @mc-and-his-agents/loom-installer add plugin",
        "npx @mc-and-his-agents/loom-installer add skill <skill-id>",
    )
    for command in installation_commands:
        if command not in skills_readme:
            failures.append(Failure(category, f"`skills/README.md` must document `{command}`"))
        if command not in skills_readme_zh:
            failures.append(Failure(category, f"`skills/README.zh-CN.md` must document `{command}`"))
    if "git clone https://github.com/MC-and-his-Agents/Loom.git ~/.codex/loom" not in readme:
        failures.append(Failure(category, "`README.md` must document native skills-library installation"))
    if "git clone https://github.com/MC-and-his-Agents/Loom.git ~/.codex/loom" not in readme_zh:
        failures.append(Failure(category, "`README.zh-CN.md` must document native skills-library installation"))

    return failures


def check_skill_manifests(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    expected_entries = {
        "loom-init": "bootstrap/root",
        "loom-adopt": "scenario/adopt",
        "loom-resume": "scenario/resume",
        "loom-pre-review": "scenario/pre-review",
        "loom-review": "scenario/review",
        "loom-spec-review": "scenario/spec-review",
        "loom-handoff": "scenario/handoff",
        "loom-retire": "scenario/retire",
        "loom-merge-ready": "scenario/merge-ready",
    }
    registry_path = root / "skills/registry.json"
    upgrade_contract_path = root / "skills/upgrade-contract.json"

    for candidate in (registry_path, upgrade_contract_path):
        if not candidate.exists():
            return failures

    try:
        registry = load_json_file(registry_path)
    except json.JSONDecodeError as exc:
        return [Failure("skill-manifests", f"`skills/registry.json` is invalid JSON: {exc.msg}")]

    try:
        upgrade_contract = load_json_file(upgrade_contract_path)
    except json.JSONDecodeError as exc:
        return [Failure("skill-manifests", f"`skills/upgrade-contract.json` is invalid JSON: {exc.msg}")]

    if not isinstance(registry, dict):
        failures.append(Failure("skill-manifests", "`skills/registry.json` must be a JSON object"))
        return failures
    if not isinstance(upgrade_contract, dict):
        failures.append(Failure("skill-manifests", "`skills/upgrade-contract.json` must be a JSON object"))
        return failures

    registry_version = registry.get("registry_version")
    root_entry = registry.get("root_entry")
    entries = registry.get("entries")
    upgrade_reference = registry.get("upgrade_contract")
    install_layout_reference = registry.get("install_layout")
    layout_manifest: dict[str, object] | None = None
    if registry_version != upgrade_contract.get("registry_version"):
        failures.append(Failure("skill-manifests", "`skills/upgrade-contract.json` registry version must match `skills/registry.json`"))
    if install_layout_reference != "install-layout.json":
        failures.append(Failure("skill-manifests", "`skills/registry.json` must point `install_layout` to `install-layout.json`"))
    else:
        install_layout_path = registry_path.parent / install_layout_reference
        if not install_layout_path.exists():
            failures.append(Failure("skill-manifests", "`skills/install-layout.json` must exist"))
        else:
            try:
                candidate_layout = load_json_file(install_layout_path)
            except json.JSONDecodeError as exc:
                failures.append(Failure("skill-manifests", f"`skills/install-layout.json` is invalid JSON: {exc.msg}"))
            else:
                layout_manifest = candidate_layout
                required_paths = candidate_layout.get("required_paths")
                if not isinstance(required_paths, list) or not required_paths:
                    failures.append(Failure("skill-manifests", "`skills/install-layout.json` must declare a non-empty `required_paths`"))
                else:
                    for relative in required_paths:
                        if not isinstance(relative, str) or not relative:
                            failures.append(Failure("skill-manifests", "`skills/install-layout.json` required paths must be non-empty strings"))
                            continue
                        if not (registry_path.parent / relative).exists():
                            failures.append(Failure("skill-manifests", f"`skills/install-layout.json` points to missing path `{relative}`"))
                runtime_state = candidate_layout.get("runtime_state")
                if not isinstance(runtime_state, dict):
                    failures.append(Failure("skill-manifests", "`skills/install-layout.json` must declare `runtime_state`"))
                else:
                    recognized_states = runtime_state.get("recognized_states")
                    if recognized_states != ["installed-runtime", "repo-local-demo", "upgrade-rehearsal"]:
                        failures.append(
                            Failure(
                                "skill-manifests",
                                "`skills/install-layout.json` runtime_state recognized_states must stay in the stable order",
                            )
                        )
    if not isinstance(root_entry, str) or not root_entry:
        failures.append(Failure("skill-manifests", "`skills/registry.json` must declare a non-empty `root_entry`"))
        return failures
    if not isinstance(entries, list) or not entries:
        failures.append(Failure("skill-manifests", "`skills/registry.json` must declare at least one entry"))
        return failures
    if root_entry != "loom-init":
        failures.append(Failure("skill-manifests", "`skills/registry.json` root entry must remain `loom-init`"))

    root_registry_entry: dict[str, object] | None = None
    seen_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append(Failure("skill-manifests", "every registry entry must be an object"))
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append(Failure("skill-manifests", "every registry entry must declare a non-empty `id`"))
            continue
        if entry_id in seen_ids:
            failures.append(Failure("skill-manifests", f"registry declares duplicate entry `{entry_id}`"))
            continue
        seen_ids.add(entry_id)
        if entry_id == root_entry:
            root_registry_entry = entry
        expected_role = expected_entries.get(entry_id)
        if expected_role is None:
            failures.append(Failure("skill-manifests", f"registry declares unexpected entry `{entry_id}`"))
        elif entry.get("role") != expected_role:
            failures.append(Failure("skill-manifests", f"registry entry `{entry_id}` must declare role `{expected_role}`"))

        for field in ("role", "contract_version", "manifest", "executable"):
            value = entry.get(field)
            if not isinstance(value, str) or not value:
                failures.append(Failure("skill-manifests", f"registry entry `{entry_id}` must declare `{field}`"))

        manifest_path = entry.get("manifest")
        if not isinstance(manifest_path, str) or not manifest_path:
            continue
        manifest_file = registry_path.parent / manifest_path
        if not manifest_file.exists():
            failures.append(Failure("skill-manifests", f"registry entry `{entry_id}` points to missing manifest `{manifest_path}`"))
            continue
        executable_path = entry.get("executable")
        if isinstance(executable_path, str) and executable_path:
            if not (registry_path.parent / executable_path).resolve().exists():
                failures.append(
                    Failure("skill-manifests", f"registry entry `{entry_id}` points to missing executable `{executable_path}`")
                )

        try:
            contract = load_json_file(manifest_file)
        except json.JSONDecodeError as exc:
            failures.append(Failure("skill-manifests", f"`{manifest_path}` is invalid JSON: {exc.msg}"))
            continue
        if not isinstance(contract, dict):
            failures.append(Failure("skill-manifests", f"`{manifest_path}` must be a JSON object"))
            continue

        if contract.get("id") != entry_id:
            failures.append(Failure("skill-manifests", f"`{manifest_path}` id must match registry entry `{entry_id}`"))
        if contract.get("role") != entry.get("role"):
            failures.append(Failure("skill-manifests", f"`{manifest_path}` role must match registry entry `{entry_id}`"))
        if contract.get("contract_version") != entry.get("contract_version"):
            failures.append(Failure("skill-manifests", f"`{manifest_path}` contract version must match registry entry `{entry_id}`"))

        contract_root = contract.get("root_entry")
        if entry_id == root_entry:
            if contract_root is not True:
                failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `root_entry: true`"))
        elif contract_root is not False:
            failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `root_entry: false`"))

        entrypoint = contract.get("entrypoint")
        if not isinstance(entrypoint, dict):
            failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `entrypoint`"))
        else:
            required_entrypoint_keys = {"skill_markdown", "adapter_metadata"}
            if entry_id == "loom-init":
                required_entrypoint_keys.add("bootstrap_cli")
                required_entrypoint_keys.add("route_cli")
            else:
                required_entrypoint_keys.add("orchestration_cli")
            for key in required_entrypoint_keys:
                value = entrypoint.get(key)
                if not isinstance(value, str) or not value:
                    failures.append(Failure("skill-manifests", f"`{manifest_path}` missing `entrypoint.{key}`"))
                    continue
                if not (manifest_file.parent / value).exists():
                    failures.append(Failure("skill-manifests", f"`{manifest_path}` points `entrypoint.{key}` to missing `{value}`"))

        for section in ("input_contract", "output_contract", "routing"):
            value = contract.get(section)
            if not isinstance(value, dict):
                failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `{section}`"))
                continue
            reference = value.get("reference")
            if not isinstance(reference, str) or not reference:
                failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `{section}.reference`"))
                continue
            if not (manifest_file.parent / reference).exists():
                failures.append(Failure("skill-manifests", f"`{manifest_path}` points `{section}.reference` to missing `{reference}`"))

        output_contract = contract.get("output_contract")
        if isinstance(output_contract, dict) and entry_id in GOVERNANCE_SURFACE_CONTRACT_SKILLS:
            required_sections = output_contract.get("required_sections")
            if not isinstance(required_sections, list):
                failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `output_contract.required_sections`"))
            elif "governance_surface" not in required_sections:
                failures.append(
                    Failure(
                        "skill-manifests",
                        f"`{manifest_path}` must require `governance_surface` in `output_contract.required_sections`",
                    )
                )

        installation = contract.get("installation")
        if not isinstance(installation, dict):
            failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `installation`"))
        else:
            for field in ("registry", "upgrade_contract", "layout_manifest"):
                value = installation.get(field)
                if not isinstance(value, str) or not value:
                    failures.append(Failure("skill-manifests", f"`{manifest_path}` must declare `installation.{field}`"))
                    continue
                if not (manifest_file.parent / value).exists():
                    failures.append(Failure("skill-manifests", f"`{manifest_path}` points `installation.{field}` to missing `{value}`"))

    if root_registry_entry is None:
        failures.append(Failure("skill-manifests", f"`skills/registry.json` root entry `{root_entry}` does not match any declared entry"))
        return failures
    if seen_ids != set(expected_entries):
        missing = sorted(set(expected_entries) - seen_ids)
        extra = sorted(seen_ids - set(expected_entries))
        if missing:
            failures.append(Failure("skill-manifests", f"registry is missing first-wave entries: {', '.join(missing)}"))
        if extra:
            failures.append(Failure("skill-manifests", f"registry contains unexpected first-wave entries: {', '.join(extra)}"))
    if upgrade_reference != "upgrade-contract.json":
        failures.append(Failure("skill-manifests", "`skills/registry.json` must point to `upgrade-contract.json`"))

    upgrade_root = upgrade_contract.get("root_entry")
    current_contract_version = upgrade_contract.get("current_contract_version")
    upgrade_policy = upgrade_contract.get("upgrade_policy")
    if upgrade_root != root_entry:
        failures.append(
            Failure(
                "skill-manifests",
                f"`skills/upgrade-contract.json` root entry `{upgrade_root}` does not match registry root `{root_entry}`",
            )
        )
    if current_contract_version != root_registry_entry.get("contract_version"):
        failures.append(
            Failure(
                "skill-manifests",
                "`skills/upgrade-contract.json` current contract version must match the registry entry version",
            )
        )
        if not isinstance(upgrade_policy, dict):
            failures.append(Failure("skill-manifests", "`skills/upgrade-contract.json` must declare `upgrade_policy`"))
    else:
        if upgrade_policy.get("mode") != "explicit":
            failures.append(Failure("skill-manifests", "`upgrade_policy.mode` must be `explicit`"))
        refresh_required = upgrade_policy.get("refresh_required")
        if not isinstance(refresh_required, list) or not refresh_required:
            failures.append(Failure("skill-manifests", "`upgrade_policy.refresh_required` must be a non-empty list"))
        else:
            required = {"registry", "manifest", "executable", "referenced_resources", "layout_manifest"}
            if not required.issubset(set(refresh_required)):
                failures.append(
                    Failure(
                        "skill-manifests",
                        "`upgrade_policy.refresh_required` must cover registry, manifest, executable, referenced_resources, and layout_manifest",
                    )
                )

    return failures


def check_skill_routing(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    target = root / "examples/new-project"
    tool_path = root / "tools/loom_init.py"
    if not tool_path.exists() or not target.exists():
        return failures

    registry = load_json_file(root / "skills/registry.json")
    if not isinstance(registry, dict):
        return failures
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return failures
    explicit_skills = [
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry.get("id")
    ]
    for skill_id in explicit_skills:
        payload, error = load_command_json(
            root,
            ["python3", "tools/loom_init.py", "route", "--target", "examples/new-project", "--skill", skill_id],
        )
        if error:
            failures.append(Failure("skill-routing", f"explicit route for `{skill_id}` failed: {error}"))
            continue
        require_route_payload(
            failures,
            category="skill-routing",
            context=f"explicit route for `{skill_id}`",
            payload=payload,
            expected_skill=skill_id,
            expected_mode="explicit",
            expected_runtime_scene="repo-local-demo",
            expected_runtime_carrier="repo-local-wrapper",
        )
        if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
            failures.append(Failure("skill-routing", f"explicit route for `{skill_id}` must include `summary`"))
        if skill_id in GOVERNANCE_SURFACE_ROUTE_SKILLS and payload.get("result") == "pass":
            require_governance_surface(
                failures,
                category="skill-routing",
                context=f"explicit route for `{skill_id}`",
                payload=payload,
            )

    implicit_cases = (
        ("请初始化这个新项目并接入 Loom", "loom-adopt"),
        ("请接手当前事项并恢复上下文后继续推进", "loom-resume"),
        ("请在进入 review 前做统一检查", "loom-pre-review"),
        ("请先对 formal spec 做 spec review", "loom-spec-review"),
        ("请对当前事项做正式 review 并给出审查结论", "loom-review"),
        ("请准备交接并回写停点", "loom-handoff"),
        ("请清理并 retire 当前事项现场", "loom-retire"),
        ("请确认这个事项是否 merge-ready", "loom-merge-ready"),
    )
    for task, skill_id in implicit_cases:
        payload, error = load_command_json(
            root,
            ["python3", "tools/loom_init.py", "route", "--target", "examples/new-project", "--task", task],
        )
        if error:
            failures.append(Failure("skill-routing", f"implicit route for `{skill_id}` failed: {error}"))
            continue
        require_route_payload(
            failures,
            category="skill-routing",
            context=f"implicit route for `{skill_id}`",
            payload=payload,
            expected_skill=skill_id,
            expected_mode="implicit",
            expected_runtime_scene="repo-local-demo",
            expected_runtime_carrier="repo-local-wrapper",
        )
        if not isinstance(payload.get("matched_signals"), list) or not payload.get("matched_signals"):
            failures.append(Failure("skill-routing", f"implicit route for `{skill_id}` must include matched signals"))
        if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
            failures.append(Failure("skill-routing", f"implicit route for `{skill_id}` must include `summary`"))
        if skill_id in GOVERNANCE_SURFACE_ROUTE_SKILLS and payload.get("result") == "pass":
            require_governance_surface(
                failures,
                category="skill-routing",
                context=f"implicit route for `{skill_id}`",
                payload=payload,
            )

    fallback_payload, error = load_command_json(
        root,
        ["python3", "tools/loom_init.py", "route", "--target", "examples/new-project", "--task", "请帮我看看这个仓库"],
    )
    if error:
        failures.append(Failure("skill-routing", f"fallback route failed: {error}"))
    else:
        require_route_payload(
            failures,
            category="skill-routing",
            context="fallback route",
            payload=fallback_payload,
            expected_skill="loom-init",
            expected_mode="fallback",
            expected_runtime_scene="repo-local-demo",
            expected_runtime_carrier="repo-local-wrapper",
            allowed_results={"fallback"},
        )
        if not isinstance(fallback_payload.get("missing_inputs"), list) or not fallback_payload.get("missing_inputs"):
            failures.append(Failure("skill-routing", "fallback route must include `missing_inputs`"))

    ambiguous_payload, error = load_command_json(
        root,
        [
            "python3",
            "tools/loom_init.py",
            "route",
            "--target",
            "examples/new-project",
            "--task",
            "请接手当前事项并在 review 前检查",
        ],
    )
    if error:
        failures.append(Failure("skill-routing", f"ambiguous route failed: {error}"))
    else:
        require_route_payload(
            failures,
            category="skill-routing",
            context="multi-match route",
            payload=ambiguous_payload,
            expected_skill="loom-init",
            expected_mode="fallback",
            expected_runtime_scene="repo-local-demo",
            expected_runtime_carrier="repo-local-wrapper",
            allowed_results={"fallback"},
        )
        if not isinstance(ambiguous_payload.get("matched_signals"), list) or len(ambiguous_payload.get("matched_signals", [])) < 2:
            failures.append(Failure("skill-routing", "multi-match route must expose matched signals"))

    unknown_payload, error = load_command_json(
        root,
        ["python3", "tools/loom_init.py", "route", "--target", "examples/new-project", "--skill", "not-a-skill"],
    )
    if error:
        failures.append(Failure("skill-routing", f"unknown explicit route failed: {error}"))
    else:
        require_route_payload(
            failures,
            category="skill-routing",
            context="unknown explicit route",
            payload=unknown_payload,
            expected_skill="loom-init",
            expected_mode="explicit",
            expected_runtime_scene="repo-local-demo",
            expected_runtime_carrier="repo-local-wrapper",
            allowed_results={"block"},
        )
        if "unknown skill" not in str(unknown_payload.get("summary", "")):
            failures.append(Failure("skill-routing", "unknown explicit skill must expose an `unknown skill` summary"))

    with tempfile.TemporaryDirectory(prefix="loom-check-route-registry-") as tmp:
        broken_skills = Path(tmp) / "skills"
        shutil.copytree(root / "skills", broken_skills)
        registry_path = broken_skills / "registry.json"
        registry = load_json_file(registry_path)
        if isinstance(registry, dict):
            entries = registry.get("entries")
            if isinstance(entries, list):
                registry["entries"] = [
                    entry
                    for entry in entries
                    if not (isinstance(entry, dict) and entry.get("id") == "loom-review")
                ]
                registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        drift_payload, error = load_command_json(
            root,
            [
                "python3",
                str(broken_skills / "loom-init" / "scripts" / "loom-init.py"),
                "route",
                "--target",
                str(target),
                "--task",
                "请对当前事项做正式 review 并给出审查结论",
            ],
        )
        if error:
            failures.append(Failure("skill-routing", f"registry drift route failed: {error}"))
        else:
            require_route_payload(
                failures,
                category="skill-routing",
                context="registry drift route",
                payload=drift_payload,
                expected_skill="loom-init",
                expected_mode="implicit",
                expected_runtime_scene="installed-runtime",
                expected_runtime_carrier="installed-skills-root",
                allowed_results={"block"},
            )
            if "route table resolved to unknown registry skill" not in str(drift_payload.get("summary", "")):
                failures.append(Failure("skill-routing", "registry drift route must expose an unknown registry skill summary"))

    return failures


def check_demo_assets(root: Path) -> list[Failure]:
    failures = check_required_paths(root, "demo-assets", DEMO_ASSETS)

    init_result_path = root / "examples/new-project/.loom/bootstrap/init-result.json"
    if init_result_path.exists():
        try:
            init_result = load_json_file(init_result_path)
        except json.JSONDecodeError as exc:
            failures.append(Failure("demo-assets", f"demo init-result is invalid JSON: {exc.msg}"))
            return failures
        if not isinstance(init_result, dict):
            failures.append(Failure("demo-assets", "demo init-result must be a JSON object"))
            return failures
        run = init_result.get("run")
        if not isinstance(run, dict) or run.get("scenario_key") != "new":
            failures.append(Failure("demo-assets", "demo init-result must keep `scenario_key` as `new`"))
    return failures


def check_demo_fact_chain(root: Path) -> list[Failure]:
    target = root / "examples/new-project"
    if not target.exists():
        return []

    report, errors = inspect_fact_chain(target)
    failures: list[Failure] = []
    for detail in errors:
        failures.append(Failure("demo-fact-chain", detail))
    if report and report.get("fact_chain", {}).get("entry_points", {}).get("status_surface") != ".loom/status/current.md":
        failures.append(Failure("demo-fact-chain", "demo fact chain must point status_surface to `.loom/status/current.md`"))
    return failures


def check_demo_repo_local_cli(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    target = root / "examples/new-project"
    if not target.exists():
        return failures

    repo_local_commands = [
        (
            "repo-local-verify",
            ["python3", ".loom/bin/loom_init.py", "verify", "--target", "."],
            "ok",
        ),
        (
            "repo-local-fact-chain",
            ["python3", ".loom/bin/loom_init.py", "fact-chain", "--target", "."],
            "ok",
        ),
    ]
    for label, args, expected_key in repo_local_commands:
        payload, error = load_command_json(root, args, cwd=target)
        if error:
            failures.append(Failure("demo-repo-local-cli", f"`{label}` failed: {error}"))
            continue
        if payload.get(expected_key) is not True:
            failures.append(Failure("demo-repo-local-cli", f"`{label}` must report `{expected_key}: true`"))
    return failures


def check_deep_existing_repo_bootstrap(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    with tempfile.TemporaryDirectory(prefix="loom-check-deep-existing-") as tmp:
        tmp_root = Path(tmp)

        def write_repo(target: Path, *, validation_entry: bool, pr_template: bool, workflow_doc: bool) -> None:
            (target / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
            (target / "scripts").mkdir(parents=True, exist_ok=True)
            (target / "src").mkdir(parents=True, exist_ok=True)
            (target / "README.md").write_text("# Sample Repo\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("# Root Rules\n", encoding="utf-8")
            (target / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (target / "scripts" / "governance_status.py").write_text("print('ok')\n", encoding="utf-8")
            (target / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
            if workflow_doc:
                (target / "WORKFLOW.md").write_text("# Workflow\n", encoding="utf-8")
            if validation_entry:
                (target / "Makefile").write_text("check:\n\t@echo ok\n", encoding="utf-8")
            if pr_template:
                (target / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("## Summary\n", encoding="utf-8")

        deep_target = tmp_root / "deep-existing"
        write_repo(deep_target, validation_entry=True, pr_template=True, workflow_doc=True)
        deep_payload, deep_error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_init.py",
                "bootstrap",
                "--target",
                str(deep_target),
                "--write",
                "--force",
                "--verify",
                "--install-pr-template",
            ],
        )
        if deep_error:
            failures.append(Failure("deep-existing-bootstrap", f"`deep-existing bootstrap` failed: {deep_error}"))
        else:
            recommended = deep_payload.get("recommended_adoption")
            verification = deep_payload.get("verification")
            governance_surface = deep_payload.get("governance_surface")
            if not isinstance(recommended, dict) or recommended.get("path") != "deep-existing-repo":
                failures.append(Failure("deep-existing-bootstrap", "`deep-existing bootstrap` must select `recommended_adoption.path = deep-existing-repo`"))
            run = deep_payload.get("run")
            if not isinstance(run, dict) or run.get("scenario_key") != "complex-existing":
                failures.append(Failure("deep-existing-bootstrap", "`deep-existing bootstrap` must keep `scenario_key = complex-existing`"))
            if not isinstance(verification, dict) or verification.get("ok") is not True:
                failures.append(Failure("deep-existing-bootstrap", "`deep-existing bootstrap` must verify successfully"))
            if not isinstance(governance_surface, dict) or governance_surface.get("repository_mode") != "complex-existing":
                failures.append(Failure("deep-existing-bootstrap", "`deep-existing bootstrap` must keep `governance_surface.repository_mode = complex-existing`"))
            for required in (
                ".loom/companion/README.md",
                ".loom/companion/checkpoints.md",
                ".loom/companion/review.md",
                ".loom/companion/merge-ready.md",
                ".loom/companion/closeout.md",
            ):
                if not (deep_target / required).exists():
                    failures.append(Failure("deep-existing-bootstrap", f"`deep-existing bootstrap` is missing `{required}`"))
            for forbidden in (
                ".loom/work-items/INIT-0001.md",
                ".loom/progress/INIT-0001.md",
                ".loom/status/current.md",
            ):
                if (deep_target / forbidden).exists():
                    failures.append(Failure("deep-existing-bootstrap", f"`deep-existing bootstrap` must not generate `{forbidden}`"))
            fact_chain = deep_payload.get("fact_chain")
            if not isinstance(fact_chain, dict) or fact_chain.get("mode") != "repo-native attach-only":
                failures.append(Failure("deep-existing-bootstrap", "`deep-existing bootstrap` must keep `fact_chain.mode = repo-native attach-only`"))

        full_target = tmp_root / "full-bootstrap"
        write_repo(full_target, validation_entry=False, pr_template=False, workflow_doc=False)
        full_payload, full_error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_init.py",
                "bootstrap",
                "--target",
                str(full_target),
                "--write",
                "--force",
                "--verify",
                "--install-pr-template",
            ],
        )
        if full_error:
            failures.append(Failure("deep-existing-bootstrap", f"`full-bootstrap fallback sample` failed: {full_error}"))
        else:
            recommended = full_payload.get("recommended_adoption")
            if not isinstance(recommended, dict) or recommended.get("path") != "full-bootstrap":
                failures.append(Failure("deep-existing-bootstrap", "complex existing sample without overload must keep `recommended_adoption.path = full-bootstrap`"))
            for required in (
                ".loom/work-items/INIT-0001.md",
                ".loom/progress/INIT-0001.md",
                ".loom/status/current.md",
            ):
                if not (full_target / required).exists():
                    failures.append(Failure("deep-existing-bootstrap", f"`full-bootstrap fallback sample` must generate `{required}`"))
    return failures


def check_daily_execution_cli(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    example_target = root / "examples/new-project"
    tool_path = root / "tools/loom_flow.py"
    if not tool_path.exists() or not example_target.exists():
        return failures

    demo_commands = [
        (
            "runtime-state-init",
            ["python3", "tools/loom_init.py", "runtime-state", "--target", "."],
            {"pass"},
        ),
        (
            "runtime-state-flow",
            ["python3", "tools/loom_flow.py", "runtime-state", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "fact-chain",
            ["python3", "tools/loom_flow.py", "fact-chain", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "runtime-evidence",
            [
                "python3",
                "tools/loom_flow.py",
                "runtime-evidence",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass"},
        ),
        (
            "state-check",
            ["python3", "tools/loom_flow.py", "state-check", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "status-control",
            ["python3", "tools/loom_status.py", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass", "block"},
        ),
        (
            "runtime-parity",
            [
                "python3",
                "tools/loom_flow.py",
                "runtime-parity",
                "validate",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass"},
        ),
        (
            "governance-profile-status",
            ["python3", "tools/loom_flow.py", "governance-profile", "status", "--target", "examples/new-project"],
            {"pass"},
        ),
        (
            "governance-profile-upgrade-plan",
            ["python3", "tools/loom_flow.py", "governance-profile", "upgrade-plan", "--target", "examples/new-project"],
            {"pass", "block"},
        ),
        (
            "governance-profile-upgrade",
            [
                "python3",
                "tools/loom_flow.py",
                "governance-profile",
                "upgrade",
                "--target",
                "examples/new-project",
                "--to",
                "standard",
                "--dry-run",
            ],
            {"pass"},
        ),
        (
            "governance-profile-binding",
            ["python3", "tools/loom_flow.py", "governance-profile", "binding", "--target", "."],
            {"block"},
        ),
        (
            "flow-pre-review",
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "pre-review",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass", "block", "fallback"},
        ),
        (
            "flow-review",
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "review",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass", "block", "fallback"},
        ),
        (
            "flow-resume",
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "resume",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass"},
        ),
        (
            "flow-handoff",
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "handoff",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass", "block"},
        ),
        (
            "flow-merge-ready",
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "merge-ready",
                "--target",
                "examples/new-project",
                "--item",
                "INIT-0001",
            ],
            {"pass", "block", "fallback"},
        ),
        (
            "admission",
            ["python3", "tools/loom_flow.py", "checkpoint", "admission", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "build",
            ["python3", "tools/loom_flow.py", "checkpoint", "build", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass", "block", "fallback"},
        ),
        (
            "merge",
            ["python3", "tools/loom_flow.py", "checkpoint", "merge", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass", "block", "fallback"},
        ),
        (
            "locate",
            ["python3", "tools/loom_flow.py", "workspace", "locate", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "review-read",
            ["python3", "tools/loom_flow.py", "review", "read", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "host-lifecycle",
            ["python3", "tools/loom_flow.py", "host-lifecycle", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
        (
            "closeout-check",
            ["python3", "tools/loom_flow.py", "closeout", "check", "--target", ".", "--skip-gate"],
            {"pass"},
        ),
        (
            "closeout-sync",
            ["python3", "tools/loom_flow.py", "closeout", "sync", "--target", ".", "--skip-gate"],
            {"pass"},
        ),
        (
            "reconciliation-audit",
            ["python3", "tools/loom_flow.py", "reconciliation", "audit", "--target", "."],
            {"block"},
        ),
        (
            "purity",
            ["python3", "tools/loom_flow.py", "purity-check", "--target", "examples/new-project", "--item", "INIT-0001"],
            {"pass"},
        ),
    ]
    for label, args, allowed_results in demo_commands:
        payload, error = load_command_json(root, args)
        if error:
            failures.append(Failure("daily-execution-cli", f"`{label}` command failed: {error}"))
            continue
        result = payload.get("result")
        if result not in allowed_results:
            failures.append(
                Failure(
                    "daily-execution-cli",
                    f"`{label}` returned unexpected result `{result}`",
                )
            )
        if label == "runtime-state-init":
            if payload.get("command") != "runtime-state":
                failures.append(Failure("daily-execution-cli", "`loom-init runtime-state` must report `command: runtime-state`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`loom-init runtime-state`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
        if label == "runtime-state-flow":
            if payload.get("command") != "runtime-state":
                failures.append(Failure("daily-execution-cli", "`loom-flow runtime-state` must report `command: runtime-state`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`loom-flow runtime-state`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
        if label == "runtime-evidence":
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`runtime-evidence`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
        if label == "state-check":
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`state-check`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
        if label == "status-control":
            if payload.get("command") != "status":
                failures.append(Failure("daily-execution-cli", "`loom_status` must report `command: status`"))
            governance_status = payload.get("governance_status")
            if not isinstance(governance_status, dict):
                failures.append(Failure("daily-execution-cli", "`loom_status` must include `governance_status`"))
            else:
                if governance_status.get("schema_version") != "loom-governance-status/v2":
                    failures.append(Failure("daily-execution-cli", "`loom_status` governance_status must report schema v2"))
                if governance_status.get("result") not in {"pass", "block"}:
                    failures.append(Failure("daily-execution-cli", "`loom_status` governance_status result must be `pass` or `block`"))
                if not isinstance(governance_status.get("gate_chain"), list):
                    failures.append(Failure("daily-execution-cli", "`loom_status` governance_status must include gate_chain"))
                else:
                    gate_names = [
                        gate.get("name")
                        for gate in governance_status["gate_chain"]
                        if isinstance(gate, dict)
                    ]
                    expected_names = [
                        "work_item_admission",
                        "spec_gate",
                        "build_gate",
                        "review_gate",
                        "merge_gate",
                        "github_controlled_merge",
                    ]
                    if gate_names != expected_names:
                        failures.append(Failure("daily-execution-cli", "`loom_status` governance_status gate_chain must use the stable gate vocabulary"))
                classifications = governance_status.get("classifications")
                if not isinstance(classifications, list):
                    failures.append(Failure("daily-execution-cli", "`loom_status` governance_status must include classifications"))
            closeout = payload.get("closeout")
            if not isinstance(closeout, dict):
                failures.append(Failure("daily-execution-cli", "`loom_status` must include `closeout`"))
            else:
                if closeout.get("result") not in {"pass", "block", "not_applicable"}:
                    failures.append(Failure("daily-execution-cli", "`loom_status` closeout result must stay within the stable set"))
                reconciliation = closeout.get("reconciliation")
                if not isinstance(reconciliation, dict):
                    failures.append(Failure("daily-execution-cli", "`loom_status` closeout must include reconciliation"))
                elif reconciliation.get("result") not in {"pass", "warn", "fix-needed", "block", "not_applicable"}:
                    failures.append(Failure("daily-execution-cli", "`loom_status` closeout reconciliation result must stay within the stable set"))
            require_governance_surface(
                failures,
                category="daily-execution-cli",
                context="`loom_status`",
                payload=payload,
            )
        if label == "runtime-parity":
            require_runtime_parity_payload(
                failures,
                category="daily-execution-cli",
                context="`runtime-parity validate`",
                payload=payload,
            )
        if label in {"governance-profile-status", "governance-profile-upgrade-plan"}:
            if payload.get("command") != "governance-profile":
                failures.append(Failure("daily-execution-cli", f"`{label}` must report `command: governance-profile`"))
            expected_operation = "status" if label == "governance-profile-status" else "upgrade-plan"
            if payload.get("operation") != expected_operation:
                failures.append(Failure("daily-execution-cli", f"`{label}` must report `operation: {expected_operation}`"))
            control_plane = payload.get("governance_control_plane")
            require_governance_control_plane(
                failures,
                category="daily-execution-cli",
                context=f"`{label}` governance_control_plane",
                payload=control_plane,
            )
        if label == "governance-profile-binding":
            require_github_binding_payload(
                failures,
                category="daily-execution-cli",
                context="`governance-profile binding`",
                payload=payload,
            )
        if label == "governance-profile-upgrade":
            require_governance_upgrade_payload(
                failures,
                category="daily-execution-cli",
                context="`governance-profile upgrade`",
                payload=payload,
            )
        if label == "flow-pre-review":
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`flow pre-review`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            steps = payload.get("steps")
            if isinstance(steps, list):
                step_names = [step.get("name") for step in steps if isinstance(step, dict)]
                if step_names != [
                    "runtime-state",
                    "fact-chain",
                    "state-check",
                    "runtime-evidence",
                    "checkpoint-admission",
                    "workspace-locate",
                ]:
                    failures.append(
                        Failure(
                            "daily-execution-cli",
                            "`flow pre-review` must run runtime-state, fact-chain, state-check, runtime-evidence, checkpoint-admission, and workspace-locate in order",
                        )
                    )
        if label == "purity":
            purity = payload.get("purity")
            if not isinstance(purity, dict):
                failures.append(Failure("daily-execution-cli", "`purity` output must include a `purity` object"))
                continue
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`purity`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            scope_assessment = purity.get("scope_assessment")
            if not isinstance(scope_assessment, dict):
                failures.append(Failure("daily-execution-cli", "`purity` output must include `scope_assessment`"))
                continue
            mode = scope_assessment.get("mode")
            if mode not in {"constrained", "unconstrained"}:
                failures.append(
                    Failure("daily-execution-cli", "`scope_assessment.mode` must be `constrained` or `unconstrained`")
                )
        if label == "flow-resume":
            if payload.get("command") != "flow":
                failures.append(Failure("daily-execution-cli", "`flow resume` must report `command: flow`"))
            if payload.get("operation") != "resume":
                failures.append(Failure("daily-execution-cli", "`flow resume` must report `operation: resume`"))
            if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
                failures.append(Failure("daily-execution-cli", "`flow resume` must include a non-empty `summary`"))
            if not isinstance(payload.get("missing_inputs"), list):
                failures.append(Failure("daily-execution-cli", "`flow resume` must include `missing_inputs`"))
            if payload.get("fallback_to") not in {None, "admission"}:
                failures.append(Failure("daily-execution-cli", "`flow resume` fallback must be `null` or `admission`"))
            for key in ("item", "workspace", "recovery", "checkpoint", "state_check"):
                if not isinstance(payload.get(key), dict):
                    failures.append(Failure("daily-execution-cli", f"`flow resume` must include `{key}`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`flow resume`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            require_governance_surface(
                failures,
                category="daily-execution-cli",
                context="`flow resume`",
                payload=payload,
            )
            require_maturity_upgrade_path(
                failures,
                category="daily-execution-cli",
                context="`flow resume`",
                payload=payload.get("maturity_upgrade_path"),
            )
            steps = payload.get("steps")
            if not isinstance(steps, list):
                failures.append(Failure("daily-execution-cli", "`flow resume` must include `steps`"))
                continue
            step_names = [step.get("name") for step in steps if isinstance(step, dict)]
            if step_names != ["runtime-state", "fact-chain", "state-check", "workspace-locate"]:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow resume` must run runtime-state, fact-chain, state-check, and workspace-locate in order",
                    )
                )
            recovery = payload.get("recovery")
            if isinstance(recovery, dict):
                for field in ("current_stop", "next_step", "blockers", "latest_validation_summary"):
                    value = recovery.get(field)
                    if not isinstance(value, str) or not value:
                        failures.append(
                            Failure("daily-execution-cli", f"`flow resume` recovery must include non-empty `{field}`")
                        )
            checkpoint = payload.get("checkpoint")
            if isinstance(checkpoint, dict):
                if checkpoint.get("normalized") not in {"admission", "build", "merge", "retired"}:
                    failures.append(
                        Failure("daily-execution-cli", "`flow resume` checkpoint must include a known normalized value")
                    )
            state_check = payload.get("state_check")
            if isinstance(state_check, dict):
                if state_check.get("result") not in {"pass", "block"}:
                    failures.append(
                        Failure("daily-execution-cli", "`flow resume` state_check.result must be `pass` or `block`")
                    )
                if not isinstance(state_check.get("checks"), dict):
                    failures.append(Failure("daily-execution-cli", "`flow resume` must include `state_check.checks`"))
        if label == "flow-handoff":
            if payload.get("command") != "flow":
                failures.append(Failure("daily-execution-cli", "`flow handoff` must report `command: flow`"))
            if payload.get("operation") != "handoff":
                failures.append(Failure("daily-execution-cli", "`flow handoff` must report `operation: handoff`"))
            if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
                failures.append(Failure("daily-execution-cli", "`flow handoff` must include a non-empty `summary`"))
            if not isinstance(payload.get("missing_inputs"), list):
                failures.append(Failure("daily-execution-cli", "`flow handoff` must include `missing_inputs`"))
            if payload.get("fallback_to") not in {None, "admission"}:
                failures.append(Failure("daily-execution-cli", "`flow handoff` fallback must be `null` or `admission`"))
            for key in ("item", "workspace", "checkpoint", "state_check"):
                if not isinstance(payload.get(key), dict):
                    failures.append(Failure("daily-execution-cli", f"`flow handoff` must include `{key}`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`flow handoff`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            for key in (
                "recovery_entry",
                "status_surface",
                "current_stop",
                "next_step",
                "blockers",
                "latest_validation_summary",
            ):
                value = payload.get(key)
                if not isinstance(value, str) or not value:
                    failures.append(Failure("daily-execution-cli", f"`flow handoff` must include non-empty `{key}`"))
            if payload.get("fallback_target") not in {None, "admission"}:
                failures.append(Failure("daily-execution-cli", "`flow handoff` fallback_target must be `null` or `admission`"))
            writeback_fields = payload.get("writeback_fields")
            if writeback_fields != [
                "current_stop",
                "next_step",
                "blockers",
                "latest_validation_summary",
            ]:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow handoff` must report the stable writeback field list in order",
                    )
                )
            steps = payload.get("steps")
            if not isinstance(steps, list):
                failures.append(Failure("daily-execution-cli", "`flow handoff` must include `steps`"))
                continue
            step_names = [step.get("name") for step in steps if isinstance(step, dict)]
            if step_names != ["runtime-state", "fact-chain", "state-check", "workspace-locate"]:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow handoff` must run runtime-state, fact-chain, state-check, and workspace-locate in order",
                    )
                )
            state_check = payload.get("state_check")
            if isinstance(state_check, dict):
                if state_check.get("result") not in {"pass", "block"}:
                    failures.append(
                        Failure("daily-execution-cli", "`flow handoff` state_check.result must be `pass` or `block`")
                    )
                if not isinstance(state_check.get("checks"), dict):
                    failures.append(Failure("daily-execution-cli", "`flow handoff` must include `state_check.checks`"))
        if label == "flow-review":
            if payload.get("command") != "flow":
                failures.append(Failure("daily-execution-cli", "`flow review` must report `command: flow`"))
            if payload.get("operation") != "review":
                failures.append(Failure("daily-execution-cli", "`flow review` must report `operation: review`"))
            for key in ("item", "state_check", "runtime_evidence", "build_checkpoint", "review", "current_checkpoint", "repo_specific_requirements"):
                if not isinstance(payload.get(key), dict):
                    failures.append(Failure("daily-execution-cli", f"`flow review` must include `{key}`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`flow review`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            steps = payload.get("steps")
            if not isinstance(steps, list):
                failures.append(Failure("daily-execution-cli", "`flow review` must include `steps`"))
                continue
            step_names = [step.get("name") for step in steps if isinstance(step, dict)]
            if step_names != [
                "runtime-state",
                "fact-chain",
                "state-check",
                "runtime-evidence",
                "checkpoint-build",
                "spec-review-gate",
                "review-entry",
            ]:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow review` must run runtime-state, fact-chain, state-check, runtime-evidence, checkpoint-build, spec-review-gate, and review-entry in order",
                    )
                )
            review = payload.get("review")
            if isinstance(review, dict):
                require_review_record_contract(
                    failures,
                    category="daily-execution-cli",
                    context="`flow review` review.record",
                    payload=review.get("record"),
                )
            require_repo_specific_requirements_payload(
                failures,
                category="daily-execution-cli",
                context="`flow review` repo_specific_requirements",
                payload=payload.get("repo_specific_requirements"),
                expected_surface="review",
            )
        if label == "review-read":
            if payload.get("command") != "review":
                failures.append(Failure("daily-execution-cli", "`review read` must report `command: review`"))
            if payload.get("operation") != "read":
                failures.append(Failure("daily-execution-cli", "`review read` must report `operation: read`"))
            review = payload.get("review")
            if not isinstance(review, dict):
                failures.append(Failure("daily-execution-cli", "`review read` must include a `review` object"))
            elif not isinstance(review.get("record"), dict):
                failures.append(Failure("daily-execution-cli", "`review read` must include `review.record`"))
            else:
                require_review_record_contract(
                    failures,
                    category="daily-execution-cli",
                    context="`review read` review.record",
                    payload=review.get("record"),
                )
        if label == "host-lifecycle":
            if payload.get("command") != "host-lifecycle":
                failures.append(Failure("daily-execution-cli", "`host-lifecycle` must report `command: host-lifecycle`"))
            require_host_lifecycle_payload(
                failures,
                category="daily-execution-cli",
                context="`host-lifecycle`",
                payload=payload,
            )
        if label in {"closeout-check", "closeout-sync"}:
            if payload.get("command") != "closeout":
                failures.append(Failure("daily-execution-cli", f"`{label}` must report `command: closeout`"))
            expected_operation = "check" if label == "closeout-check" else "sync"
            if payload.get("operation") != expected_operation:
                failures.append(
                    Failure("daily-execution-cli", f"`{label}` must report `operation: {expected_operation}`")
                )
            repo = payload.get("repo")
            if not isinstance(repo, dict):
                failures.append(Failure("daily-execution-cli", f"`{label}` must include `repo`"))
            else:
                if not isinstance(repo.get("owner"), str) or not repo.get("owner"):
                    failures.append(Failure("daily-execution-cli", f"`{label}` must include `repo.owner`"))
                if not isinstance(repo.get("name"), str) or not repo.get("name"):
                    failures.append(Failure("daily-execution-cli", f"`{label}` must include `repo.name`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context=f"`{label}`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            require_closeout_reconciliation_contract(
                failures,
                category="daily-execution-cli",
                context=f"`{label}`",
                payload=payload,
            )
            require_repo_specific_requirements_payload(
                failures,
                category="daily-execution-cli",
                context=f"`{label}` repo_specific_requirements",
                payload=payload.get("repo_specific_requirements"),
                expected_surface="closeout",
            )
        if label == "reconciliation-audit":
            if payload.get("command") != "reconciliation":
                failures.append(Failure("daily-execution-cli", "`reconciliation audit` must report `command: reconciliation`"))
            if payload.get("operation") != "audit":
                failures.append(Failure("daily-execution-cli", "`reconciliation audit` must report `operation: audit`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`reconciliation audit`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            require_reconciliation_payload(
                failures,
                category="daily-execution-cli",
                context="`reconciliation audit`",
                payload=payload,
            )
        if label == "flow-merge-ready":
            if payload.get("command") != "flow":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must report `command: flow`"))
            if payload.get("operation") != "merge-ready":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must report `operation: merge-ready`"))
            if not isinstance(payload.get("summary"), str) or not payload.get("summary"):
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include a non-empty `summary`"))
            if not isinstance(payload.get("missing_inputs"), list):
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include `missing_inputs`"))
            if payload.get("fallback_to") not in {None, "admission", "build", "merge", "retired"}:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow merge-ready` fallback must be `null` or a known checkpoint",
                    )
                )
            for key in ("item", "runtime_state", "state_check", "runtime_evidence", "build_checkpoint", "merge_checkpoint", "current_checkpoint", "repo_specific_requirements"):
                if not isinstance(payload.get(key), dict):
                    failures.append(Failure("daily-execution-cli", f"`flow merge-ready` must include `{key}`"))
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`flow merge-ready`",
                payload=payload.get("runtime_state"),
                expected_scene="repo-local-demo",
                expected_carrier="repo-local-wrapper",
                allowed_results={"pass"},
            )
            if not isinstance(payload.get("current_lane"), str) or not payload.get("current_lane"):
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include `current_lane`"))
            if not isinstance(payload.get("latest_validation_summary"), str) or not payload.get("latest_validation_summary"):
                failures.append(
                    Failure("daily-execution-cli", "`flow merge-ready` must include `latest_validation_summary`")
                )
            steps = payload.get("steps")
            if not isinstance(steps, list):
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include `steps`"))
                continue
            step_names = [step.get("name") for step in steps if isinstance(step, dict)]
            if step_names != [
                "runtime-state",
                "fact-chain",
                "state-check",
                "runtime-evidence",
                "checkpoint-build",
                "checkpoint-merge",
            ]:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        "`flow merge-ready` must run runtime-state, fact-chain, state-check, runtime-evidence, checkpoint-build, and checkpoint-merge in order",
                    )
                )
            state_check = payload.get("state_check")
            if isinstance(state_check, dict):
                if state_check.get("result") not in {"pass", "block"}:
                    failures.append(
                        Failure("daily-execution-cli", "`flow merge-ready` state_check.result must be `pass` or `block`")
                    )
                if not isinstance(state_check.get("checks"), dict):
                    failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include `state_check.checks`"))
            runtime_evidence = payload.get("runtime_evidence")
            if isinstance(runtime_evidence, dict):
                for field in ("run_entry", "logs_entry", "diagnostics_entry", "verification_entry", "lane_entry"):
                    if not isinstance(runtime_evidence.get(field), dict):
                        failures.append(
                            Failure("daily-execution-cli", f"`flow merge-ready` must include runtime evidence field `{field}`")
                        )
            for key in ("build_checkpoint", "merge_checkpoint"):
                checkpoint = payload.get(key)
                if isinstance(checkpoint, dict):
                    if checkpoint.get("result") not in {"pass", "block", "fallback"}:
                        failures.append(
                            Failure(
                                "daily-execution-cli",
                                f"`flow merge-ready` {key}.result must be `pass`, `block`, or `fallback`",
                            )
                        )
                    if not isinstance(checkpoint.get("missing_inputs"), list):
                        failures.append(
                            Failure("daily-execution-cli", f"`flow merge-ready` {key} must include `missing_inputs`")
                        )
            merge_checkpoint = payload.get("merge_checkpoint")
            if isinstance(merge_checkpoint, dict) and not isinstance(merge_checkpoint.get("pr_template"), dict):
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must include `merge_checkpoint.pr_template`"))
            require_repo_specific_requirements_payload(
                failures,
                category="daily-execution-cli",
                context="`flow merge-ready` repo_specific_requirements",
                payload=payload.get("repo_specific_requirements"),
                expected_surface="merge_ready",
            )
            if payload.get("result") != "fallback":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must return `fallback` for the bootstrap demo"))
            if payload.get("fallback_to") != "admission":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` must fall back to `admission` for the bootstrap demo"))
            if isinstance(payload.get("build_checkpoint"), dict) and payload["build_checkpoint"].get("fallback_to") != "admission":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` build checkpoint must fall back to `admission` for the bootstrap demo"))
            if isinstance(payload.get("merge_checkpoint"), dict) and payload["merge_checkpoint"].get("fallback_to") != "admission":
                failures.append(Failure("daily-execution-cli", "`flow merge-ready` merge checkpoint must fall back to `admission` for the bootstrap demo"))

    with tempfile.TemporaryDirectory(prefix="loom-check-review-run-") as tmp:
        source_snapshot = Path(tmp) / "source-snapshot"
        review_target = Path(tmp) / "new-project"
        fake_bin = Path(tmp) / "bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, source_snapshot, ignore=shutil.ignore_patterns(".git", ".DS_Store", "__pycache__"))

        def prepare_review_target(target: Path, label: str) -> bool:
            shutil.copytree(source_snapshot, target)
            for args in (
                ["git", "init"],
                ["git", "config", "user.email", "loom-check@example.com"],
                ["git", "config", "user.name", "loom-check"],
            ):
                result = run_command(root, args, cwd=target)
                if result.returncode != 0:
                    detail = result.stderr.strip() or result.stdout.strip() or "git setup failed"
                    failures.append(Failure("daily-execution-cli", f"`{label}` setup failed: {detail}"))
                    return False
            payload, error = load_command_json(
                root,
                [
                    "python3",
                    "tools/loom_init.py",
                    "bootstrap",
                    "--target",
                    ".",
                    "--write",
                    "--force",
                    "--verify",
                    "--install-pr-template",
                ],
                cwd=target,
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`{label}` bootstrap failed: {error}"))
                return False
            verification = payload.get("verification")
            if not isinstance(verification, dict) or verification.get("ok") is not True:
                failures.append(Failure("daily-execution-cli", f"`{label}` bootstrap must verify successfully"))
                return False
            for args in (
                ["git", "add", "."],
                ["git", "add", "-f", ".loom"],
                ["git", "commit", "-m", "review-run baseline"],
            ):
                result = run_command(root, args, cwd=target)
                if result.returncode != 0:
                    detail = result.stderr.strip() or result.stdout.strip() or "git baseline commit failed"
                    failures.append(Failure("daily-execution-cli", f"`{label}` setup failed: {detail}"))
                    return False
            head = run_command(root, ["git", "rev-parse", "HEAD"], cwd=target)
            if head.returncode != 0:
                detail = head.stderr.strip() or head.stdout.strip() or "git rev-parse failed"
                failures.append(Failure("daily-execution-cli", f"`{label}` setup failed: {detail}"))
                return False
            reviewed_head = head.stdout.strip() or "unknown-head"
            spec_review_path = target / ".loom/reviews/INIT-0001.spec.json"
            spec_review_path.write_text(
                json.dumps(
                    {
                        "schema_version": "loom-review/v1",
                        "item_id": "INIT-0001",
                        "decision": "allow",
                        "kind": "spec_review",
                        "summary": "Formal spec is approved for downstream review-run tests.",
                        "reviewer": "loom-check",
                        "reviewed_head": reviewed_head,
                        "reviewed_validation_summary": "Bootstrap manifest exists; init-result JSON can be read mechanically; the first work item, status surface, and spec/plan artifacts exist.",
                        "fallback_to": None,
                        "findings": [],
                        "blocking_issues": [],
                        "follow_ups": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            for args in (
                ["git", "add", "-f", ".loom/reviews/INIT-0001.spec.json"],
                ["git", "commit", "-m", "record spec review baseline"],
            ):
                result = run_command(root, args, cwd=target)
                if result.returncode != 0:
                    detail = result.stderr.strip() or result.stdout.strip() or "git spec review baseline failed"
                    failures.append(Failure("daily-execution-cli", f"`{label}` setup failed: {detail}"))
                    return False
            return True

        prepare_review_target(review_target, "review run positive chain")
        write_fake_codex(fake_bin / "codex", mode="success")
        success_env = prepend_path_env(fake_bin)

        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "review",
                "run",
                "--target",
                str(review_target),
                "--item",
                "INIT-0001",
            ],
            env=success_env,
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`review run` positive chain failed: {error}"))
        else:
            require_review_run_payload(
                failures,
                category="daily-execution-cli",
                context="`review run` positive chain",
                payload=payload,
                expected_result={"pass"},
            )

        engine_missing_target = Path(tmp) / "engine-missing"
        prepare_review_target(engine_missing_target, "review run engine unavailable")
        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "review",
                "run",
                "--target",
                str(engine_missing_target),
                "--item",
                "INIT-0001",
            ],
            env={"PATH": "/usr/bin:/bin"},
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`review run` engine unavailable failed: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`review run` must block when the default engine is unavailable"))
        else:
            require_review_run_payload(
                failures,
                category="daily-execution-cli",
                context="`review run` engine unavailable",
                payload=payload,
                expected_result={"block"},
            )
            engine = payload.get("engine")
            if isinstance(engine, dict) and engine.get("failure_reason") != "engine_unavailable":
                failures.append(Failure("daily-execution-cli", "`review run` must report `engine_unavailable` when Codex is missing"))
            if payload.get("fallback_to") is not None:
                failures.append(Failure("daily-execution-cli", "`review run` must not convert engine failure into checkpoint fallback"))

        schema_target = Path(tmp) / "schema-drift"
        prepare_review_target(schema_target, "review run schema drift")
        write_fake_codex(fake_bin / "codex", mode="schema_drift")
        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "review",
                "run",
                "--target",
                str(schema_target),
                "--item",
                "INIT-0001",
            ],
            env=success_env,
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`review run` schema drift failed: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`review run` must block on schema drift"))
        else:
            require_review_run_payload(
                failures,
                category="daily-execution-cli",
                context="`review run` schema drift",
                payload=payload,
                expected_result={"block"},
            )
            engine = payload.get("engine")
            if isinstance(engine, dict) and engine.get("failure_reason") != "schema_drift":
                failures.append(Failure("daily-execution-cli", "`review run` must report `schema_drift` for invalid engine output"))

        dirty_target = Path(tmp) / "tracked-edit"
        prepare_review_target(dirty_target, "review run tracked edit")
        write_fake_codex(fake_bin / "codex", mode="tracked_edit", tracked_edit_target=".loom/status/current.md")
        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "review",
                "run",
                "--target",
                str(dirty_target),
                "--item",
                "INIT-0001",
            ],
            env=success_env,
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`review run` tracked edit failed: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`review run` must block when engine modifies tracked repo content"))
        else:
            require_review_run_payload(
                failures,
                category="daily-execution-cli",
                context="`review run` tracked edit",
                payload=payload,
                expected_result={"block"},
            )
            engine = payload.get("engine")
            if isinstance(engine, dict) and engine.get("failure_reason") != "repo_diff_detected":
                failures.append(Failure("daily-execution-cli", "`review run` must report `repo_diff_detected` when tracked files change"))

    with tempfile.TemporaryDirectory(prefix="loom-check-flow-") as tmp:
        lifecycle_target = Path(tmp) / "new-project"
        shutil.copytree(example_target, lifecycle_target)
        temp_root = lifecycle_target / ".loom/flow/tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        (temp_root / "sentinel.txt").write_text("temp\n", encoding="utf-8")

        for operation in ("create", "cleanup", "retire"):
            payload, error = load_command_json(
                root,
                [
                    "python3",
                    "tools/loom_flow.py",
                    "workspace",
                    operation,
                    "--target",
                    str(lifecycle_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`workspace {operation}` failed: {error}"))
                continue
            if payload.get("result") != "pass":
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        f"`workspace {operation}` must pass on a clean temp copy, got `{payload.get('result')}`",
                    )
                )

        locate_payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "workspace",
                "locate",
                "--target",
                str(lifecycle_target),
                "--item",
                "INIT-0001",
            ],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`workspace locate` after retire failed: {error}"))
        elif (
            not isinstance(locate_payload.get("checkpoint"), dict)
            or locate_payload["checkpoint"].get("normalized") != "retired"
        ):
            failures.append(Failure("daily-execution-cli", "`workspace retire` must leave the copied sample in `retired` state"))

    with tempfile.TemporaryDirectory(prefix="loom-check-authoring-") as tmp:
        authoring_target = Path(tmp) / "new-project"
        shutil.copytree(example_target, authoring_target)

        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "recovery",
                "writeback",
                "--target",
                str(authoring_target),
                "--item",
                "INIT-0001",
                "--current-stop",
                "Bootstrap review has started.",
                "--next-step",
                "Record the first formal review conclusion.",
                "--latest-validation-summary",
                "Bootstrap artifacts verified and ready for semantic review.",
            ],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`recovery writeback` failed: {error}"))
        elif payload.get("result") != "pass":
            failures.append(Failure("daily-execution-cli", "`recovery writeback` must pass on a clean temp copy"))

        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "work-item",
                "create",
                "--target",
                str(authoring_target),
                "--item",
                "NEXT-0001",
                "--goal",
                "Validate work item authoring",
                "--scope",
                "Limit changes to `.loom/` artifacts for this temp check",
                "--execution-path",
                "execution/support",
                "--workspace-entry",
                ".",
                "--validation-entry",
                "python3 .loom/bin/loom_init.py verify --target .",
                "--closing-condition",
                "The authored work item can be activated and read mechanically.",
                "--init-recovery",
                "--activate",
            ],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`work-item create` failed: {error}"))
        elif payload.get("result") != "pass":
            failures.append(Failure("daily-execution-cli", "`work-item create --activate` must pass on a clean temp copy"))

        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "work-item",
                "update",
                "--target",
                str(authoring_target),
                "--item",
                "NEXT-0001",
                "--scope",
                "Keep the temp authoring check constrained to `.loom/` files",
                "--add-artifact",
                ".loom/reviews/NEXT-0001.json",
            ],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`work-item update` failed: {error}"))
        elif payload.get("result") != "pass":
            failures.append(Failure("daily-execution-cli", "`work-item update` must pass on a clean temp copy"))

        findings_path = authoring_target / ".loom" / "review-findings.json"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_text(
            json.dumps(
                [
                    {
                        "id": "compat-block-1",
                        "summary": "Formal review has not approved the item yet.",
                        "severity": "block",
                        "rebuttal": None,
                        "disposition": {
                            "status": "rejected",
                            "summary": "The finding remains open until the missing approval signal is resolved."
                        },
                    },
                    {
                        "id": "compat-warn-1",
                        "summary": "Re-run formal review after the missing approval signal is resolved.",
                        "severity": "warn",
                        "rebuttal": "A follow-up review will be recorded after the blocking issue is resolved.",
                        "disposition": {
                            "status": "deferred",
                            "summary": "This follow-up stays open until the next formal review."
                        },
                    },
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "review",
                "record",
                "--target",
                str(authoring_target),
                "--item",
                "NEXT-0001",
                "--decision",
                "fallback",
                "--kind",
                "code_review",
                "--summary",
                "Formal review has not approved the item yet.",
                "--reviewer",
                "loom-check",
                "--fallback-to",
                "admission",
                "--findings-file",
                ".loom/review-findings.json",
            ],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`review record` failed: {error}"))
        elif payload.get("result") != "pass":
            failures.append(Failure("daily-execution-cli", "`review record` must pass for an authored fallback decision"))
        else:
            review = payload.get("review")
            if isinstance(review, dict):
                require_review_record_contract(
                    failures,
                    category="daily-execution-cli",
                    context="`review record` review.record",
                    payload=review.get("record"),
                )

    if shutil.which("git") is not None:
        with tempfile.TemporaryDirectory(prefix="loom-check-purity-") as tmp:
            dirty_target = Path(tmp) / "new-project"
            shutil.copytree(example_target, dirty_target)
            run_command(root, ["git", "init"], cwd=dirty_target)
            run_command(root, ["git", "config", "user.email", "loom-check@example.com"], cwd=dirty_target)
            run_command(root, ["git", "config", "user.name", "loom-check"], cwd=dirty_target)
            run_command(root, ["git", "add", "."], cwd=dirty_target)
            run_command(root, ["git", "commit", "-m", "baseline"], cwd=dirty_target)
            (dirty_target / "untriaged.txt").write_text("pending\n", encoding="utf-8")
            payload, error = load_command_json(
                root,
                [
                    "python3",
                    "tools/loom_flow.py",
                    "purity-check",
                    "--target",
                    str(dirty_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`purity-check` negative sample failed: {error}"))
            elif payload.get("result") != "block":
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        f"`purity-check` negative sample must block, got `{payload.get('result')}`",
                    )
                )
            state_payload, error = load_command_json(
                root,
                [
                    "python3",
                    "tools/loom_flow.py",
                    "state-check",
                    "--target",
                    str(dirty_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`state-check` negative sample failed: {error}"))
            elif state_payload.get("result") != "block":
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        f"`state-check` negative sample must block, got `{state_payload.get('result')}`",
                    )
                )

    with tempfile.TemporaryDirectory(prefix="loom-check-runtime-state-") as tmp:
        tmp_root = Path(tmp)
        install_root = tmp_root / "installed" / "skills"
        target_root = tmp_root / "target"
        bootstrap_target = tmp_root / "bootstrapped-target"
        shutil.copytree(root / "skills", install_root)
        target_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(example_target, bootstrap_target)

        payload, error = load_command_json(
            root,
            ["python3", str(install_root / "loom-init" / "scripts" / "loom-init.py"), "runtime-state", "--target", str(target_root)],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`installed loom-init runtime-state` failed: {error}"))
        else:
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`installed loom-init runtime-state`",
                payload=payload.get("runtime_state"),
                expected_scene="installed-runtime",
                expected_carrier="installed-skills-root",
                allowed_results={"pass"},
            )

        payload, error = load_command_json(
            root,
            ["python3", str(install_root / "shared" / "scripts" / "loom_flow.py"), "runtime-state", "--target", str(target_root)],
            env={"LOOM_RUNTIME_SCENE": "upgrade-rehearsal"},
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`installed loom-flow runtime-state -- rehearsal` failed: {error}"))
        else:
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`installed loom-flow runtime-state -- rehearsal`",
                payload=payload.get("runtime_state"),
                expected_scene="upgrade-rehearsal",
                expected_carrier="installed-skills-root",
                allowed_results={"pass"},
            )

        broken_install = tmp_root / "broken-install" / "skills"
        shutil.copytree(root / "skills", broken_install)
        (broken_install / "shared" / "scripts" / "loom_flow.py").unlink()
        payload, error = load_command_json(
            root,
            ["python3", str(broken_install / "loom-init" / "scripts" / "loom-init.py"), "runtime-state", "--target", str(target_root)],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`installed runtime-state` missing shared runtime failed unexpectedly: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`installed runtime-state` must block when shared runtime is missing"))

        drift_install = tmp_root / "drift-install" / "skills"
        shutil.copytree(root / "skills", drift_install)
        (drift_install / "install-layout.json").unlink()
        payload, error = load_command_json(
            root,
            ["python3", str(drift_install / "loom-init" / "scripts" / "loom-init.py"), "runtime-state", "--target", str(target_root)],
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`installed runtime-state` missing install-layout failed unexpectedly: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`installed runtime-state` must block when install-layout is missing"))

        payload, error = load_command_json(
            root,
            ["python3", str(install_root / "shared" / "scripts" / "loom_flow.py"), "runtime-state", "--target", str(target_root)],
            env={"LOOM_RUNTIME_SCENE": "repo-local-demo"},
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`installed runtime-state` scene conflict failed unexpectedly: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`installed runtime-state` must block on scene/carrier conflict"))

        payload, error = load_command_json(
            root,
            ["python3", ".loom/bin/loom_init.py", "runtime-state", "--target", "."],
            cwd=bootstrap_target,
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`bootstrapped loom-init runtime-state` failed: {error}"))
        else:
            require_runtime_state_payload(
                failures,
                category="daily-execution-cli",
                context="`bootstrapped loom-init runtime-state`",
                payload=payload.get("runtime_state"),
                expected_scene="installed-runtime",
                expected_carrier="bootstrapped-target-runtime",
                allowed_results={"pass"},
            )

        broken_bootstrap = tmp_root / "broken-bootstrapped-target"
        shutil.copytree(example_target, broken_bootstrap)
        manifest_path = broken_bootstrap / ".loom" / "bootstrap" / "manifest.json"
        manifest = load_json_file(manifest_path)
        if isinstance(manifest, dict):
            artifacts = manifest.get("artifacts")
            if isinstance(artifacts, list):
                for artifact in artifacts:
                    if isinstance(artifact, dict) and artifact.get("path") == ".loom/bin/runtime_state.py":
                        artifact["source"] = "broken/source.py"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload, error = load_command_json(
            root,
            ["python3", ".loom/bin/loom_init.py", "runtime-state", "--target", "."],
            cwd=broken_bootstrap,
        )
        if error:
            failures.append(Failure("daily-execution-cli", f"`bootstrapped runtime-state` manifest drift failed unexpectedly: {error}"))
        elif payload.get("result") != "block":
            failures.append(Failure("daily-execution-cli", "`bootstrapped runtime-state` must block when the bootstrap manifest drifts"))

    if shutil.which("git") is not None:
        with tempfile.TemporaryDirectory(prefix="loom-check-installed-pre-merge-") as tmp:
            tmp_root = Path(tmp)
            install_root = tmp_root / "installed" / "skills"
            source_snapshot = tmp_root / "source-snapshot"
            positive_target = tmp_root / "positive-target"
            review_fallback_target = tmp_root / "review-fallback-target"
            fake_bin = tmp_root / "bin"
            fake_bin.mkdir(parents=True, exist_ok=True)
            write_fake_codex(fake_bin / "codex", mode="success")
            installed_review_env = prepend_path_env(fake_bin)
            shutil.copytree(root / "skills", install_root)
            shutil.copytree(root, source_snapshot, ignore=shutil.ignore_patterns(".git", ".DS_Store", "__pycache__"))

            def prepare_target(target: Path) -> tuple[str | None, list[str]]:
                errors: list[str] = []
                shutil.copytree(source_snapshot, target)
                for args in (
                    ["git", "init"],
                    ["git", "config", "user.email", "loom-check@example.com"],
                    ["git", "config", "user.name", "loom-check"],
                ):
                    result = run_command(root, args, cwd=target)
                    if result.returncode != 0:
                        detail = result.stderr.strip() or result.stdout.strip() or "git setup failed"
                        errors.append(detail)
                        return None, errors

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "bootstrap",
                        "--target",
                        str(target),
                        "--write",
                        "--force",
                        "--verify",
                        "--install-pr-template",
                    ],
                )
                if error:
                    errors.append(error)
                    return None, errors
                verification = payload.get("verification")
                if not isinstance(verification, dict) or verification.get("ok") is not True:
                    errors.append("installed bootstrap must verify successfully before the pre-merge chain starts")
                    return None, errors

                git_add = run_command(root, ["git", "add", "."], cwd=target)
                if git_add.returncode != 0:
                    detail = git_add.stderr.strip() or git_add.stdout.strip() or "git add failed"
                    errors.append(detail)
                    return None, errors
                git_commit = run_command(root, ["git", "commit", "-m", "bootstrap baseline for #209"], cwd=target)
                if git_commit.returncode != 0:
                    detail = git_commit.stderr.strip() or git_commit.stdout.strip() or "git commit failed"
                    errors.append(detail)
                    return None, errors

                resume_payload, resume_error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-resume" / "scripts" / "loom-resume.py"),
                        "flow",
                        "resume",
                        "--target",
                        str(target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if resume_error:
                    errors.append(resume_error)
                    return None, errors
                recovery = resume_payload.get("recovery")
                if not isinstance(recovery, dict):
                    errors.append("resume payload must include `recovery`")
                    return None, errors
                summary = recovery.get("latest_validation_summary")
                if not isinstance(summary, str) or not summary:
                    errors.append("resume payload must expose a non-empty `latest_validation_summary`")
                    return None, errors
                return summary, errors

            positive_summary, positive_setup_errors = prepare_target(positive_target)
            if positive_setup_errors:
                failures.append(
                    Failure(
                        "daily-execution-cli",
                        f"`installed pre-merge chain` setup failed: {'; '.join(positive_setup_errors)}",
                    )
                )
            else:
                task_signals = {
                    "resume": "请接手当前事项并恢复上下文后继续推进",
                    "pre-review": "请在进入 review 前做统一检查",
                    "spec-review": "请先对 formal spec 做 spec review",
                    "review": "请对当前事项做正式 review 并给出审查结论",
                    "merge-ready": "请做 merge-ready 最终放行前预检并确认是否可以合并",
                }

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["resume"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route resume` failed: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route resume`",
                        payload=payload,
                        expected_skill="loom-resume",
                        expected_mode="implicit",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                    )

                resume_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-resume" / "scripts" / "loom-resume.py"),
                        "flow",
                        "resume",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow resume` failed: {error}"))
                elif resume_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed flow resume` must pass for the positive chain"))
                else:
                    require_runtime_state_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed flow resume`",
                        payload=resume_payload.get("runtime_state"),
                        expected_scene="installed-runtime",
                        expected_carrier="installed-skills-root",
                        allowed_results={"pass"},
                    )

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["pre-review"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route pre-review` failed: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route pre-review`",
                        payload=payload,
                        expected_skill="loom-pre-review",
                        expected_mode="implicit",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                    )

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-pre-review" / "scripts" / "loom-pre-review.py"),
                        "flow",
                        "pre-review",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow pre-review` failed: {error}"))
                elif payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed flow pre-review` must pass for the positive chain"))

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["spec-review"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route spec-review` failed: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route spec-review`",
                        payload=payload,
                        expected_skill="loom-spec-review",
                        expected_mode="implicit",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                    )

                spec_review_flow_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-spec-review" / "scripts" / "loom-spec-review.py"),
                        "flow",
                        "spec-review",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow spec-review` failed: {error}"))
                elif spec_review_flow_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed flow spec-review` must pass for the positive chain"))

                spec_review_run_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "review",
                        "run",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                        "--review-file",
                        ".loom/reviews/INIT-0001.spec.json",
                    ],
                    env=installed_review_env,
                    timeout_seconds=150,
                )
                spec_review_record_input: dict[str, object] | None = None
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed spec review run` failed: {error}"))
                elif spec_review_run_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed spec review run` must pass for the positive chain"))
                else:
                    require_review_run_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed spec review run`",
                        payload=spec_review_run_payload,
                        expected_result={"pass"},
                    )
                    spec_review_record_input = (
                        spec_review_run_payload.get("review_record_input")
                        if isinstance(spec_review_run_payload, dict)
                        else None
                    )

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-spec-review" / "scripts" / "loom-spec-review.py"),
                        "review",
                        "record",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                        "--review-file",
                        ".loom/reviews/INIT-0001.spec.json",
                        "--decision",
                        str(spec_review_record_input.get("decision", "allow")) if isinstance(spec_review_record_input, dict) else "allow",
                        "--kind",
                        "spec_review",
                        "--summary",
                        str(spec_review_record_input.get("summary", "Installed formal spec is approved for downstream review."))
                        if isinstance(spec_review_record_input, dict)
                        else "Installed formal spec is approved for downstream review.",
                        "--reviewer",
                        str(spec_review_record_input.get("reviewer", "loom-check")) if isinstance(spec_review_record_input, dict) else "loom-check",
                        "--findings-file",
                        str(spec_review_record_input.get("findings_file", ".loom/review-findings.json"))
                        if isinstance(spec_review_record_input, dict)
                        else ".loom/review-findings.json",
                        "--engine-adapter",
                        str(spec_review_record_input.get("engine_adapter", "loom/default-codex"))
                        if isinstance(spec_review_record_input, dict)
                        else "loom/default-codex",
                        "--engine-evidence",
                        str(spec_review_record_input.get("engine_evidence", ".loom/runtime/review/INIT-0001/unknown-head/engine-result.json"))
                        if isinstance(spec_review_record_input, dict)
                        else ".loom/runtime/review/INIT-0001/unknown-head/engine-result.json",
                        "--normalized-findings",
                        str(spec_review_record_input.get("normalized_findings", ".loom/review-findings.json"))
                        if isinstance(spec_review_record_input, dict)
                        else ".loom/review-findings.json",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed spec review record allow` failed: {error}"))
                elif payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed spec review record allow` must pass"))

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["review"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route review` failed: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route review`",
                        payload=payload,
                        expected_skill="loom-review",
                        expected_mode="implicit",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                    )

                review_flow_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-review" / "scripts" / "loom-review.py"),
                        "flow",
                        "review",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow review` failed: {error}"))
                elif review_flow_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed flow review` must pass for the positive chain"))
                else:
                    review = review_flow_payload.get("review")
                    if isinstance(review, dict):
                        require_review_record_contract(
                            failures,
                            category="daily-execution-cli",
                            context="`installed flow review` review.record",
                            payload=review.get("record"),
                        )

                review_run_payload: dict[str, object] | None = None
                review_record_input: dict[str, object] | None = None
                review_run_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "review",
                        "run",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                    env=installed_review_env,
                    timeout_seconds=150,
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed review run` failed: {error}"))
                elif review_run_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed review run` must pass for the positive chain"))
                else:
                    require_review_run_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed review run`",
                        payload=review_run_payload,
                        expected_result={"pass"},
                    )
                    review_record_input = review_run_payload.get("review_record_input") if isinstance(review_run_payload, dict) else None
                review_record_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-review" / "scripts" / "loom-review.py"),
                        "review",
                        "record",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                        "--decision",
                        str(review_record_input.get("decision", "allow")) if isinstance(review_record_input, dict) else "allow",
                        "--kind",
                        str(review_record_input.get("kind", "code_review")) if isinstance(review_record_input, dict) else "code_review",
                        "--summary",
                        str(review_record_input.get("summary", "Installed pre-merge chain is ready for merge checkpoint consumption."))
                        if isinstance(review_record_input, dict)
                        else "Installed pre-merge chain is ready for merge checkpoint consumption.",
                        "--reviewer",
                        str(review_record_input.get("reviewer", "loom-check")) if isinstance(review_record_input, dict) else "loom-check",
                        "--findings-file",
                        str(review_record_input.get("findings_file", ".loom/review-findings.json")) if isinstance(review_record_input, dict) else ".loom/review-findings.json",
                        "--engine-adapter",
                        str(review_record_input.get("engine_adapter", "loom/default-codex")) if isinstance(review_record_input, dict) else "loom/default-codex",
                        "--engine-evidence",
                        str(review_record_input.get("engine_evidence", ".loom/runtime/review/INIT-0001/unknown-head/engine-result.json"))
                        if isinstance(review_record_input, dict)
                        else ".loom/runtime/review/INIT-0001/unknown-head/engine-result.json",
                        "--normalized-findings",
                        str(review_record_input.get("normalized_findings", ".loom/review-findings.json"))
                        if isinstance(review_record_input, dict)
                        else ".loom/review-findings.json",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed review record allow` failed: {error}"))
                elif review_record_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed review record allow` must pass"))
                else:
                    review = review_record_payload.get("review")
                    if isinstance(review, dict):
                        require_review_record_contract(
                            failures,
                            category="daily-execution-cli",
                            context="`installed review record allow` review.record",
                            payload=review.get("record"),
                        )

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "recovery",
                        "writeback",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                        "--current-checkpoint",
                        "merge checkpoint",
                        "--current-stop",
                        "Installed review completed and merge-ready validation is next.",
                        "--next-step",
                        "Run merge-ready and checkpoint merge from installed skills.",
                        "--latest-validation-summary",
                        positive_summary,
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed recovery writeback for merge` failed: {error}"))
                elif payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed recovery writeback for merge` must pass"))

                git_add = run_command(
                    root,
                    [
                        "git",
                        "add",
                        "-f",
                        ".loom/progress/INIT-0001.md",
                        ".loom/status/current.md",
                        ".loom/reviews/INIT-0001.json",
                    ],
                    cwd=positive_target,
                )
                if git_add.returncode != 0:
                    detail = git_add.stderr.strip() or git_add.stdout.strip() or "git add failed"
                    failures.append(Failure("daily-execution-cli", f"`installed pre-merge carrier commit` add failed: {detail}"))
                else:
                    git_commit = run_command(
                        root,
                        ["git", "commit", "-m", "author installed pre-merge carriers for #209"],
                        cwd=positive_target,
                    )
                    if git_commit.returncode != 0:
                        detail = git_commit.stderr.strip() or git_commit.stdout.strip() or "git commit failed"
                        failures.append(Failure("daily-execution-cli", f"`installed pre-merge carrier commit` failed: {detail}"))

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["merge-ready"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route merge-ready` failed: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route merge-ready`",
                        payload=payload,
                        expected_skill="loom-merge-ready",
                        expected_mode="implicit",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                    )

                merge_ready_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "loom-merge-ready" / "scripts" / "loom-merge-ready.py"),
                        "flow",
                        "merge-ready",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow merge-ready` failed: {error}"))
                elif merge_ready_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed flow merge-ready` must pass for the positive chain"))
                else:
                    merge_checkpoint = merge_ready_payload.get("merge_checkpoint")
                    if not isinstance(merge_checkpoint, dict) or merge_checkpoint.get("result") != "pass":
                        failures.append(Failure("daily-execution-cli", "`installed flow merge-ready` must expose `merge_checkpoint.result = pass`"))

                checkpoint_merge_payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "checkpoint",
                        "merge",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed checkpoint merge` failed: {error}"))
                elif checkpoint_merge_payload.get("result") != "pass":
                    failures.append(Failure("daily-execution-cli", "`installed checkpoint merge` must pass for the positive chain"))

                broken_install = tmp_root / "broken-install" / "skills"
                shutil.copytree(root / "skills", broken_install)
                (broken_install / "install-layout.json").unlink()
                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(broken_install / "loom-init" / "scripts" / "loom-init.py"),
                        "route",
                        "--target",
                        str(positive_target),
                        "--task",
                        task_signals["resume"],
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed route` missing install-layout failed unexpectedly: {error}"))
                else:
                    require_route_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed route` missing install-layout",
                        payload=payload,
                        expected_skill="loom-init",
                        expected_mode="fallback",
                        expected_runtime_scene="installed-runtime",
                        expected_runtime_carrier="installed-skills-root",
                        allowed_results={"block"},
                    )

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(broken_install / "loom-pre-review" / "scripts" / "loom-pre-review.py"),
                        "flow",
                        "pre-review",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed flow pre-review` missing install-layout failed unexpectedly: {error}"))
                elif payload.get("result") != "block":
                    failures.append(Failure("daily-execution-cli", "`installed flow pre-review` must block when install-layout is missing"))
                else:
                    require_runtime_state_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed flow pre-review` missing install-layout",
                        payload=payload.get("runtime_state"),
                        expected_scene="installed-runtime",
                        expected_carrier="installed-skills-root",
                        allowed_results={"block"},
                    )

                review_fallback_summary, review_fallback_errors = prepare_target(review_fallback_target)
                if review_fallback_errors:
                    failures.append(
                        Failure(
                            "daily-execution-cli",
                            f"`installed review baseline fallback` setup failed: {'; '.join(review_fallback_errors)}",
                        )
                    )
                else:
                    payload, error = load_command_json(
                        root,
                        [
                            "python3",
                            str(install_root / "shared" / "scripts" / "loom_flow.py"),
                            "recovery",
                            "writeback",
                            "--target",
                            str(review_fallback_target),
                            "--item",
                            "INIT-0001",
                            "--current-checkpoint",
                            "admission checkpoint",
                            "--current-stop",
                            "Installed review baseline is still at admission.",
                            "--next-step",
                            "Promote the target repo to build checkpoint before review.",
                            "--latest-validation-summary",
                            review_fallback_summary,
                        ],
                    )
                    if error:
                        failures.append(Failure("daily-execution-cli", f"`installed recovery writeback for admission fallback` failed: {error}"))
                    elif payload.get("result") != "pass":
                        failures.append(Failure("daily-execution-cli", "`installed recovery writeback for admission fallback` must pass"))

                    git_add = run_command(
                        root,
                        ["git", "add", "-f", ".loom/progress/INIT-0001.md", ".loom/status/current.md"],
                        cwd=review_fallback_target,
                    )
                    if git_add.returncode != 0:
                        detail = git_add.stderr.strip() or git_add.stdout.strip() or "git add failed"
                        failures.append(Failure("daily-execution-cli", f"`installed review baseline fallback` add failed: {detail}"))
                    else:
                        git_commit = run_command(
                            root,
                            ["git", "commit", "-m", "lower checkpoint to admission for #209 fallback"],
                            cwd=review_fallback_target,
                        )
                        if git_commit.returncode != 0:
                            detail = git_commit.stderr.strip() or git_commit.stdout.strip() or "git commit failed"
                            failures.append(Failure("daily-execution-cli", f"`installed review baseline fallback` commit failed: {detail}"))

                    payload, error = load_command_json(
                        root,
                        [
                            "python3",
                            str(install_root / "loom-review" / "scripts" / "loom-review.py"),
                            "flow",
                            "review",
                            "--target",
                            str(review_fallback_target),
                            "--item",
                            "INIT-0001",
                        ],
                    )
                    if error:
                        failures.append(Failure("daily-execution-cli", f"`installed flow review` admission fallback failed: {error}"))
                    elif payload.get("result") != "fallback" or payload.get("fallback_to") != "admission":
                        failures.append(Failure("daily-execution-cli", "`installed flow review` must fall back to `admission` when build checkpoint is missing"))

                    payload, error = load_command_json(
                        root,
                        [
                            "python3",
                            str(install_root / "loom-merge-ready" / "scripts" / "loom-merge-ready.py"),
                            "flow",
                            "merge-ready",
                            "--target",
                            str(review_fallback_target),
                            "--item",
                            "INIT-0001",
                        ],
                    )
                    if error:
                        failures.append(Failure("daily-execution-cli", f"`installed flow merge-ready` review-baseline fallback failed: {error}"))
                    elif payload.get("result") not in {"fallback", "block"}:
                        failures.append(Failure("daily-execution-cli", "`installed flow merge-ready` must fail closed when review baseline is missing"))

                readme_path = positive_target / "README.md"
                readme_path.write_text(readme_path.read_text(encoding="utf-8") + "\n# review-head-drift\n", encoding="utf-8")
                git_add = run_command(root, ["git", "add", "README.md"], cwd=positive_target)
                if git_add.returncode != 0:
                    detail = git_add.stderr.strip() or git_add.stdout.strip() or "git add failed"
                    failures.append(Failure("daily-execution-cli", f"`installed merge-ready drift` add failed: {detail}"))
                else:
                    git_commit = run_command(
                        root,
                        ["git", "commit", "-m", "introduce non-carrier drift after review for #209"],
                        cwd=positive_target,
                    )
                    if git_commit.returncode != 0:
                        detail = git_commit.stderr.strip() or git_commit.stdout.strip() or "git commit failed"
                        failures.append(Failure("daily-execution-cli", f"`installed merge-ready drift` commit failed: {detail}"))

                payload, error = load_command_json(
                    root,
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "checkpoint",
                        "merge",
                        "--target",
                        str(positive_target),
                        "--item",
                        "INIT-0001",
                    ],
                )
                if error:
                    failures.append(Failure("daily-execution-cli", f"`installed checkpoint merge` drift negative failed: {error}"))
                elif payload.get("result") != "block":
                    failures.append(Failure("daily-execution-cli", "`installed checkpoint merge` must block when HEAD drifts beyond Loom carriers"))

    gh_auth_probe = None
    if shutil.which("gh") is not None:
        try:
            gh_auth_probe = run_command(root, ["gh", "auth", "status"], timeout_seconds=5)
        except subprocess.TimeoutExpired:
            gh_auth_probe = None
    gh_auth_ready = gh_auth_probe is not None and gh_auth_probe.returncode == 0
    if gh_auth_ready:
        with tempfile.TemporaryDirectory(prefix="loom-check-installed-post-merge-") as tmp:
            tmp_root = Path(tmp)
            install_root = tmp_root / "installed" / "skills"
            retire_target = tmp_root / "retire-target"
            dirty_target = tmp_root / "dirty-target"
            broken_install = tmp_root / "broken-install" / "skills"
            shutil.copytree(root / "skills", install_root)

            for label, args in (
                (
                    "installed reconciliation audit",
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "reconciliation",
                        "audit",
                        "--target",
                        str(root),
                        "--issue",
                        "131",
                        "--pr",
                        "138",
                        "--project",
                        "5",
                    ],
                ),
                (
                    "installed reconciliation sync dry-run",
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "reconciliation",
                        "sync",
                        "--target",
                        str(root),
                        "--issue",
                        "131",
                        "--pr",
                        "138",
                        "--project",
                        "5",
                        "--dry-run",
                    ],
                ),
                (
                    "installed closeout check",
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "closeout",
                        "check",
                        "--target",
                        str(root),
                        "--issue",
                        "131",
                        "--pr",
                        "138",
                        "--project",
                        "5",
                        "--skip-gate",
                    ],
                ),
                (
                    "installed closeout sync",
                    [
                        "python3",
                        str(install_root / "shared" / "scripts" / "loom_flow.py"),
                        "closeout",
                        "sync",
                        "--target",
                        str(root),
                        "--issue",
                        "131",
                        "--pr",
                        "138",
                        "--project",
                        "5",
                        "--skip-gate",
                    ],
                ),
            ):
                payload, error = load_command_json_with_retry(
                    root,
                    args,
                    timeout_seconds=30,
                    retries=3,
                )
                if error:
                    if label in {"installed closeout check", "installed closeout sync"} and "command timed out" in error:
                        continue
                    failures.append(Failure("daily-execution-cli", f"`{label}` failed: {error}"))
                    continue
                rate_limited = payload_has_github_rate_limit(payload)
                if label == "installed reconciliation audit":
                    if payload.get("result") != "pass" and not rate_limited:
                        failures.append(Failure("daily-execution-cli", "`installed reconciliation audit` must pass on the historical closeout sample"))
                    require_runtime_state_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed reconciliation audit`",
                        payload=payload.get("runtime_state"),
                        expected_scene="installed-runtime",
                        expected_carrier="installed-skills-root",
                        allowed_results={"pass"},
                    )
                    require_reconciliation_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed reconciliation audit`",
                        payload=payload,
                    )
                elif label == "installed reconciliation sync dry-run":
                    if payload.get("result") != "pass" and not rate_limited:
                        failures.append(Failure("daily-execution-cli", "`installed reconciliation sync --dry-run` must pass on an already aligned sample"))
                    require_runtime_state_payload(
                        failures,
                        category="daily-execution-cli",
                        context="`installed reconciliation sync --dry-run`",
                        payload=payload.get("runtime_state"),
                        expected_scene="installed-runtime",
                        expected_carrier="installed-skills-root",
                        allowed_results={"pass"},
                    )
                else:
                    if payload.get("result") != "pass" and not rate_limited:
                        failures.append(Failure("daily-execution-cli", f"`{label}` must pass on the historical closeout sample"))
                    require_runtime_state_payload(
                        failures,
                        category="daily-execution-cli",
                        context=f"`{label}`",
                        payload=payload.get("runtime_state"),
                        expected_scene="installed-runtime",
                        expected_carrier="installed-skills-root",
                        allowed_results={"pass"},
                    )
                    require_closeout_reconciliation_contract(
                        failures,
                        category="daily-execution-cli",
                        context=f"`{label}`",
                        payload=payload,
                    )

            for target in (retire_target, dirty_target):
                shutil.copytree(example_target, target)
                for args in (
                    ["git", "init"],
                    ["git", "config", "user.email", "loom-check@example.com"],
                    ["git", "config", "user.name", "loom-check"],
                    ["git", "add", "."],
                    ["git", "commit", "-m", "baseline"],
                ):
                    result = run_command(root, args, cwd=target)
                    if result.returncode != 0:
                        detail = result.stderr.strip() or result.stdout.strip() or "git setup failed"
                        failures.append(Failure("daily-execution-cli", f"`installed retire` setup failed: {detail}"))
                        break

            purity_payload, error = load_command_json(
                root,
                [
                    "python3",
                    str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                    "purity-check",
                    "--target",
                    str(retire_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`installed purity-check` failed: {error}"))
            elif purity_payload.get("result") != "pass":
                failures.append(Failure("daily-execution-cli", "`installed purity-check` must pass on a clean retire target"))
            else:
                require_runtime_state_payload(
                    failures,
                    category="daily-execution-cli",
                    context="`installed purity-check`",
                    payload=purity_payload.get("runtime_state"),
                    expected_scene="installed-runtime",
                    expected_carrier="installed-skills-root",
                    allowed_results={"pass"},
                )

            temp_root = retire_target / ".loom" / ".tmp"
            temp_root.mkdir(parents=True, exist_ok=True)
            (temp_root / "sentinel.txt").write_text("temp\n", encoding="utf-8")

            cleanup_payload, error = load_command_json(
                root,
                [
                    "python3",
                    str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                    "workspace",
                    "cleanup",
                    "--target",
                    str(retire_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`installed workspace cleanup` failed: {error}"))
            elif cleanup_payload.get("result") != "pass":
                failures.append(Failure("daily-execution-cli", "`installed workspace cleanup` must pass for Loom-owned residue"))
            else:
                require_runtime_state_payload(
                    failures,
                    category="daily-execution-cli",
                    context="`installed workspace cleanup`",
                    payload=cleanup_payload.get("runtime_state"),
                    expected_scene="installed-runtime",
                    expected_carrier="installed-skills-root",
                    allowed_results={"pass"},
                )

            retire_payload, error = load_command_json(
                root,
                [
                    "python3",
                    str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                    "workspace",
                    "retire",
                    "--target",
                    str(retire_target),
                    "--item",
                    "INIT-0001",
                ],
            )
            if error:
                failures.append(Failure("daily-execution-cli", f"`installed workspace retire` failed: {error}"))
            elif retire_payload.get("result") != "pass":
                failures.append(Failure("daily-execution-cli", "`installed workspace retire` must pass after cleanup"))
            else:
                require_runtime_state_payload(
                    failures,
                    category="daily-execution-cli",
                    context="`installed workspace retire`",
                    payload=retire_payload.get("runtime_state"),
                    expected_scene="installed-runtime",
                    expected_carrier="installed-skills-root",
                    allowed_results={"pass"},
                )
                checkpoint = retire_payload.get("checkpoint")
                if not isinstance(checkpoint, dict) or checkpoint.get("normalized") != "retired":
                    failures.append(Failure("daily-execution-cli", "`installed workspace retire` must leave the target in `retired` state"))

            (dirty_target / "foreign-residue.txt").write_text("pending\n", encoding="utf-8")
            dirty_add = run_command(root, ["git", "add", "foreign-residue.txt"], cwd=dirty_target)
            if dirty_add.returncode != 0:
                detail = dirty_add.stderr.strip() or dirty_add.stdout.strip() or "git add failed"
                failures.append(Failure("daily-execution-cli", f"`installed retire` dirty sample setup failed: {detail}"))

            for label, args in (
                (
                    "installed purity-check dirty sample",
                    [
                        "python3",
                        str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                        "purity-check",
                        "--target",
                        str(dirty_target),
                        "--item",
                        "INIT-0001",
                    ],
                ),
                (
                    "installed workspace cleanup dirty sample",
                    [
                        "python3",
                        str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                        "workspace",
                        "cleanup",
                        "--target",
                        str(dirty_target),
                        "--item",
                        "INIT-0001",
                    ],
                ),
                (
                    "installed workspace retire dirty sample",
                    [
                        "python3",
                        str(install_root / "loom-retire" / "scripts" / "loom-retire.py"),
                        "workspace",
                        "retire",
                        "--target",
                        str(dirty_target),
                        "--item",
                        "INIT-0001",
                    ],
                ),
            ):
                payload, error = load_command_json(root, args)
                if error:
                    failures.append(Failure("daily-execution-cli", f"`{label}` failed: {error}"))
                    continue
                if payload.get("result") != "block":
                    failures.append(Failure("daily-execution-cli", f"`{label}` must block when non-Loom residue is present"))
                require_runtime_state_payload(
                    failures,
                    category="daily-execution-cli",
                    context=f"`{label}`",
                    payload=payload.get("runtime_state"),
                    expected_scene="installed-runtime",
                    expected_carrier="installed-skills-root",
                    allowed_results={"pass"},
                )

            shutil.copytree(root / "skills", broken_install)
            (broken_install / "install-layout.json").unlink()
            for label, args in (
                (
                    "installed closeout check missing install-layout",
                    [
                        "python3",
                        str(broken_install / "shared" / "scripts" / "loom_flow.py"),
                        "closeout",
                        "check",
                        "--target",
                        str(root),
                        "--issue",
                        "131",
                        "--pr",
                        "138",
                        "--skip-gate",
                    ],
                ),
                (
                    "installed purity-check missing install-layout",
                    [
                        "python3",
                        str(broken_install / "loom-retire" / "scripts" / "loom-retire.py"),
                        "purity-check",
                        "--target",
                        str(retire_target),
                        "--item",
                        "INIT-0001",
                    ],
                ),
            ):
                payload, error = load_command_json(root, args)
                if error:
                    failures.append(Failure("daily-execution-cli", f"`{label}` failed unexpectedly: {error}"))
                    continue
                if payload.get("result") != "block":
                    failures.append(Failure("daily-execution-cli", f"`{label}` must block when install-layout is missing"))
                require_runtime_state_payload(
                    failures,
                    category="daily-execution-cli",
                    context=f"`{label}`",
                    payload=payload.get("runtime_state"),
                    expected_scene="installed-runtime",
                    expected_carrier="installed-skills-root",
                    allowed_results={"block"},
                )

    fail_closed_payloads = [
        (
            "closeout-fix-needed-fail-open",
            {
                "result": "pass",
                "fallback_to": None,
                "reconciliation": {
                    "command": "reconciliation",
                    "operation": "audit",
                    "result": "fix-needed",
                    "summary": "fix-needed",
                    "missing_inputs": [],
                    "fallback_to": "manual-reconciliation",
                    "findings": [
                        {
                            "kind": "absorbed_but_open",
                            "severity": "fix-needed",
                            "subject": "issue #177",
                            "evidence": {},
                            "recommended_action": "run reconciliation sync",
                        }
                    ],
                },
            },
        ),
        (
            "closeout-block-fallback-drift",
            {
                "result": "block",
                "fallback_to": "merge",
                "reconciliation": {
                    "command": "reconciliation",
                    "operation": "audit",
                    "result": "block",
                    "summary": "block",
                    "missing_inputs": ["issue/pr/project"],
                    "fallback_to": "manual-reconciliation",
                    "findings": [
                        {
                            "kind": "parent_drift",
                            "severity": "block",
                            "subject": "parent issue #148",
                            "evidence": {},
                            "recommended_action": "manual reconciliation",
                        }
                    ],
                },
            },
        ),
        (
            "closeout-malformed-reconciliation",
            {
                "result": "pass",
                "fallback_to": None,
                "reconciliation": {
                    "command": "reconciliation",
                    "operation": "audit",
                    "summary": "broken",
                    "missing_inputs": "bad",
                    "findings": "bad",
                },
            },
        ),
    ]
    for label, payload in fail_closed_payloads:
        sample_failures: list[Failure] = []
        require_closeout_reconciliation_contract(
            sample_failures,
            category="daily-execution-cli",
            context=f"`{label}`",
            payload=payload,
        )
        if not sample_failures:
            failures.append(
                Failure(
                    "daily-execution-cli",
                    f"`{label}` synthetic payload must fail closeout reconciliation validation",
                )
            )

    warn_payload_failures: list[Failure] = []
    require_closeout_reconciliation_contract(
        warn_payload_failures,
        category="daily-execution-cli",
        context="`closeout-warn-does-not-block`",
        payload={
            "result": "pass",
            "fallback_to": None,
            "reconciliation": {
                "command": "reconciliation",
                "operation": "audit",
                "result": "warn",
                "summary": "warn",
                "missing_inputs": [],
                "fallback_to": "manual-reconciliation",
                    "findings": [
                        {
                            "category": "drift",
                            "kind": "project_drift",
                            "severity": "warn",
                            "subject": "project 5",
                            "evidence": {},
                            "recommended_action": "review warning",
                            "fallback_to": "reconciliation-sync",
                        }
                    ],
                },
            },
        )
    if warn_payload_failures:
        failures.append(
            Failure(
                "daily-execution-cli",
                "`closeout-warn-does-not-block` synthetic payload must allow non-blocking reconciliation warnings",
            )
        )

    valid_reconciliation_samples = [
        ("merged_but_open", "fix-needed", "reconciliation-sync"),
        ("absorbed_but_open", "fix-needed", "reconciliation-sync"),
        ("parent_drift", "block", "manual-reconciliation"),
        ("binding_failure", "block", "manual-reconciliation"),
        ("merge_signal_drift", "block", "manual-reconciliation"),
        ("host_signal_drift", "block", "manual-reconciliation"),
    ]
    for kind, reconciliation_result_value, fallback_to in valid_reconciliation_samples:
        sample_failures = []
        require_closeout_reconciliation_contract(
            sample_failures,
            category="daily-execution-cli",
            context=f"`closeout-{kind}`",
            payload={
                "result": "block",
                "fallback_to": fallback_to,
                "reconciliation": {
                    "command": "reconciliation",
                    "operation": "audit",
                    "result": reconciliation_result_value,
                    "summary": kind,
                    "missing_inputs": [] if kind != "host_signal_drift" else ["github control plane"],
                    "fallback_to": "manual-reconciliation",
                    "findings": [
                        {
                            "category": "drift",
                            "kind": kind,
                            "severity": reconciliation_result_value,
                            "subject": "closeout sample",
                            "evidence": {},
                            "recommended_action": "reconcile closeout sample",
                            "fallback_to": fallback_to,
                        }
                    ],
                },
            },
        )
        if sample_failures:
            failures.append(
                Failure(
                    "daily-execution-cli",
                    f"`closeout-{kind}` synthetic payload must satisfy closeout reconciliation validation",
                )
            )

    return failures


def check_repo_companion_interface_contracts(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    example_target = root / "examples/new-project"
    if not example_target.exists():
        return failures

    def write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def install_companion(
        target: Path,
        *,
        manifest: dict[str, object] | None = None,
        repo_interface: dict[str, object] | None = None,
        legacy_docs_only: bool = False,
    ) -> None:
        companion_dir = target / ".loom" / "companion"
        companion_dir.mkdir(parents=True, exist_ok=True)
        if legacy_docs_only:
            (companion_dir / "README.md").write_text("# Legacy Companion Docs\n", encoding="utf-8")
            return
        (companion_dir / "README.md").write_text("# Repo Companion\n", encoding="utf-8")
        for doc in (
            "review.md",
            "merge-ready.md",
            "closeout.md",
            "specialized-gates.md",
            "checkpoints.md",
            "metadata-contract.md",
            "context-schema.md",
        ):
            (companion_dir / doc).write_text(f"# {doc}\n", encoding="utf-8")
        if manifest is not None:
            write_json(companion_dir / "manifest.json", manifest)
        if repo_interface is not None:
            write_json(companion_dir / "repo-interface.json", repo_interface)

    valid_manifest = {
        "schema_version": "loom-repo-companion-manifest/v1",
        "companion_entry": ".loom/companion/README.md",
        "repo_interface": ".loom/companion/repo-interface.json",
    }
    valid_interface_v1 = {
        "schema_version": "loom-repo-interface/v1",
        "companion_entry": ".loom/companion/README.md",
        "repo_specific_requirements": {
            "review": [
                {
                    "id": "review-specialized-gate",
                    "summary": "Run the repo-specific semantic review checklist.",
                    "locator": ".loom/companion/review.md",
                    "enforcement": "blocking",
                }
            ],
            "merge_ready": [
                {
                    "id": "merge-ready-advisory-note",
                    "summary": "Review the repo-specific merge advisory note.",
                    "locator": ".loom/companion/merge-ready.md",
                    "enforcement": "advisory",
                }
            ],
            "closeout": [
                {
                    "id": "closeout-specialized-gate",
                    "summary": "Confirm the repo-specific closeout checklist.",
                    "locator": ".loom/companion/closeout.md",
                    "enforcement": "blocking",
                }
            ],
        },
        "specialized_gates": [
            {
                "id": "specialized-release-gate",
                "summary": "Companion-owned release judgment.",
                "locator": ".loom/companion/specialized-gates.md",
            }
        ],
    }
    valid_interface_v2 = {
        "schema_version": "loom-repo-interface/v2",
        "companion_entry": ".loom/companion/README.md",
        "repo_specific_requirements": valid_interface_v1["repo_specific_requirements"],
        "specialized_gates": [
            {
                "id": "specialized-review-gate",
                "summary": "Companion-owned review specialization.",
                "locator": ".loom/companion/specialized-gates.md",
                "gate_type": "review",
            }
        ],
        "metadata_contract": {
            "fields": [
                {
                    "id": "integration_check",
                    "summary": "Declare repo-specific integration metadata.",
                    "applicability_locator": ".loom/companion/metadata-contract.md",
                    "authority_locator": ".loom/companion/review.md",
                    "enforcement": "blocking",
                }
            ]
        },
        "context_schema": {
            "fields": [
                {
                    "id": "item_key",
                    "summary": "Repo-native item key.",
                    "type": "string",
                    "required": True,
                    "mapping_rule_locator": ".loom/companion/context-schema.md",
                }
            ]
        },
    }

    with tempfile.TemporaryDirectory(prefix="loom-check-repo-companion-") as tmp:
        base = Path(tmp)

        absent_target = base / "absent"
        shutil.copytree(example_target, absent_target)
        absent_surface = build_governance_surface(absent_target)
        repo_interface = absent_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="absent repo companion",
            payload=repo_interface,
        )
        if not isinstance(repo_interface, dict) or repo_interface.get("availability") != "absent":
            failures.append(Failure("repo-companion", "absent repo companion sample must report `availability: absent`"))

        docs_only_target = base / "docs-only"
        shutil.copytree(example_target, docs_only_target)
        install_companion(docs_only_target, legacy_docs_only=True)
        docs_only_surface = build_governance_surface(docs_only_target)
        docs_only_interface = docs_only_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="docs-only repo companion",
            payload=docs_only_interface,
        )
        if not isinstance(docs_only_interface, dict) or docs_only_interface.get("availability") != "companion_docs_only":
            failures.append(Failure("repo-companion", "docs-only repo companion sample must report `availability: companion_docs_only`"))

        incomplete_target = base / "incomplete"
        shutil.copytree(example_target, incomplete_target)
        install_companion(
            incomplete_target,
            manifest={
                **valid_manifest,
                "current_stop": "forbidden authored state",
                "repo_interface": ".loom/companion/missing-interface.json",
            },
        )
        incomplete_surface = build_governance_surface(incomplete_target)
        incomplete_interface = incomplete_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="incomplete repo companion",
            payload=incomplete_interface,
        )
        if not isinstance(incomplete_interface, dict) or incomplete_interface.get("availability") != "incomplete":
            failures.append(Failure("repo-companion", "incomplete repo companion sample must report `availability: incomplete`"))

        invalid_interface_target = base / "invalid-interface"
        shutil.copytree(example_target, invalid_interface_target)
        install_companion(
            invalid_interface_target,
            manifest=valid_manifest,
            repo_interface={
                "schema_version": "loom-repo-interface/v1",
                "companion_entry": ".loom/companion/README.md",
                "repo_specific_requirements": {
                    "review": [
                        {
                            "id": "bad-enforcement",
                            "summary": "Broken requirement",
                            "locator": ".loom/companion/review.md",
                            "enforcement": "required",
                        }
                    ],
                    "merge_ready": [],
                },
                "specialized_gates": [],
            },
        )
        invalid_interface_surface = build_governance_surface(invalid_interface_target)
        invalid_interface = invalid_interface_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="invalid repo companion interface",
            payload=invalid_interface,
        )
        if not isinstance(invalid_interface, dict) or invalid_interface.get("availability") != "incomplete":
            failures.append(Failure("repo-companion", "invalid repo companion interface sample must report `availability: incomplete`"))

        invalid_v2_target = base / "invalid-v2-interface"
        shutil.copytree(example_target, invalid_v2_target)
        install_companion(
            invalid_v2_target,
            manifest=valid_manifest,
            repo_interface={
                "schema_version": "loom-repo-interface/v2",
                "companion_entry": ".loom/companion/README.md",
                "repo_specific_requirements": valid_interface_v1["repo_specific_requirements"],
                "specialized_gates": [
                    {
                        "id": "bad-gate-type",
                        "summary": "Broken gate type",
                        "locator": ".loom/companion/specialized-gates.md",
                        "gate_type": "guardian",
                    }
                ],
                "metadata_contract": {
                    "fields": [
                        {
                            "id": "bad-metadata",
                            "summary": "Broken metadata field",
                            "applicability_locator": ".loom/companion/metadata-contract.md",
                            "authority_locator": ".loom/companion/review.md",
                            "enforcement": "required",
                        }
                    ]
                },
                "context_schema": {
                    "fields": [
                        {
                            "id": "bad-context",
                            "summary": "Broken context field",
                            "type": "object",
                            "required": "yes",
                            "mapping_rule_locator": ".loom/companion/context-schema.md",
                        }
                    ]
                },
            },
        )
        invalid_v2_surface = build_governance_surface(invalid_v2_target)
        invalid_v2_interface = invalid_v2_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="invalid v2 repo companion interface",
            payload=invalid_v2_interface,
        )
        if not isinstance(invalid_v2_interface, dict) or invalid_v2_interface.get("availability") != "incomplete":
            failures.append(Failure("repo-companion", "invalid v2 repo companion interface sample must report `availability: incomplete`"))

        present_v1_target = base / "present-v1"
        shutil.copytree(example_target, present_v1_target)
        install_companion(
            present_v1_target,
            manifest=valid_manifest,
            repo_interface=valid_interface_v1,
        )
        present_v1_surface = build_governance_surface(present_v1_target)
        present_v1_interface = present_v1_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="present v1 repo companion",
            payload=present_v1_interface,
        )
        if not isinstance(present_v1_interface, dict) or present_v1_interface.get("availability") != "present":
            failures.append(Failure("repo-companion", "present v1 repo companion sample must report `availability: present`"))

        present_target = base / "present-v2"
        shutil.copytree(example_target, present_target)
        install_companion(
            present_target,
            manifest=valid_manifest,
            repo_interface=valid_interface_v2,
        )
        present_surface = build_governance_surface(present_target)
        present_interface = present_surface.get("repo_interface")
        require_repo_interface_payload(
            failures,
            category="repo-companion",
            context="present v2 repo companion",
            payload=present_interface,
        )
        if not isinstance(present_interface, dict) or present_interface.get("availability") != "present":
            failures.append(Failure("repo-companion", "present v2 repo companion sample must report `availability: present`"))

        review_requirements = repo_specific_requirements_payload(
            present_interface,
            target_root=present_target,
            surface="review",
        )
        require_repo_specific_requirements_payload(
            failures,
            category="repo-companion",
            context="present repo companion review requirements",
            payload=review_requirements,
            expected_surface="review",
        )
        if review_requirements.get("result") != "block":
            failures.append(Failure("repo-companion", "blocking review requirements must fail closed"))

        merge_requirements = repo_specific_requirements_payload(
            present_interface,
            target_root=present_target,
            surface="merge_ready",
        )
        require_repo_specific_requirements_payload(
            failures,
            category="repo-companion",
            context="present repo companion merge-ready requirements",
            payload=merge_requirements,
            expected_surface="merge_ready",
        )
        if merge_requirements.get("result") != "pass":
            failures.append(Failure("repo-companion", "advisory merge-ready requirements must remain non-blocking"))

        closeout_requirements = repo_specific_requirements_payload(
            present_interface,
            target_root=present_target,
            surface="closeout",
        )
        require_repo_specific_requirements_payload(
            failures,
            category="repo-companion",
            context="present repo companion closeout requirements",
            payload=closeout_requirements,
            expected_surface="closeout",
        )
        if closeout_requirements.get("result") != "block":
            failures.append(Failure("repo-companion", "blocking closeout requirements must fail closed"))

        flow_review_payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "review",
                "--target",
                str(present_target),
                "--item",
                "INIT-0001",
            ],
        )
        if error:
            failures.append(Failure("repo-companion", f"`flow review` companion sample failed: {error}"))
        elif flow_review_payload.get("result") != "block":
            failures.append(Failure("repo-companion", "`flow review` must block when repo companion declares blocking review requirements"))

        flow_merge_ready_payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "flow",
                "merge-ready",
                "--target",
                str(present_target),
                "--item",
                "INIT-0001",
            ],
        )
        if error:
            failures.append(Failure("repo-companion", f"`flow merge-ready` companion sample failed: {error}"))
        elif not isinstance(flow_merge_ready_payload.get("repo_specific_requirements"), dict):
            failures.append(Failure("repo-companion", "`flow merge-ready` companion sample must include `repo_specific_requirements`"))
        elif flow_merge_ready_payload["repo_specific_requirements"].get("result") != "pass":
            failures.append(Failure("repo-companion", "`flow merge-ready` advisory companion requirements must stay non-blocking"))

    return failures


def check_repo_interop_contracts(root: Path) -> list[Failure]:
    example_target = root / "examples/new-project"
    if not example_target.exists():
        return []

    failures: list[Failure] = []

    def write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def install_interop(
        target: Path,
        *,
        interop: dict[str, object] | None = None,
    ) -> None:
        companion_dir = target / ".loom" / "companion"
        companion_dir.mkdir(parents=True, exist_ok=True)
        (target / "host").mkdir(parents=True, exist_ok=True)
        (target / "native").mkdir(parents=True, exist_ok=True)
        (target / ".loom" / "shadow").mkdir(parents=True, exist_ok=True)
        (target / "native" / "status").mkdir(parents=True, exist_ok=True)
        for relative, payload in {
            ".loom/shadow/admission-loom.json": {"result": "pass"},
            ".loom/shadow/admission-repo.json": {"result": "pass"},
            ".loom/shadow/review-loom.json": {"decision": "allow"},
            ".loom/shadow/review-repo.json": {"decision": "allow"},
            ".loom/shadow/merge-ready-loom.json": {"status": "pass"},
            ".loom/shadow/merge-ready-repo.json": {"status": "pass"},
            ".loom/shadow/closeout-loom.json": {"status": "done"},
            ".loom/shadow/closeout-repo.json": {"status": "done"},
            "host/guardian-review.json": {"verdict": "allow"},
        }.items():
            write_json(target / relative, payload)
        if interop is not None:
            write_json(companion_dir / "interop.json", interop)

    valid_interop = {
        "schema_version": "loom-repo-interop/v1",
        "host_adapters": [
            {
                "id": "guardian-review",
                "summary": "Read guardian review verdicts without reimplementing the host action.",
                "surfaces": ["review", "merge_ready"],
                "locator": "host/guardian-review.json",
            }
        ],
        "repo_native_carriers": [
            {
                "id": "governance-status",
                "summary": "Read repo-native governance status output without migrating carriers.",
                "surfaces": ["admission", "review", "merge_ready", "closeout"],
                "locator": "native/status",
            }
        ],
        "shadow_surfaces": {
            "admission": {
                "summary": "Compare admission parity.",
                "loom_locator": ".loom/shadow/admission-loom.json",
                "repo_locator": ".loom/shadow/admission-repo.json",
            },
            "review": {
                "summary": "Compare review parity.",
                "loom_locator": ".loom/shadow/review-loom.json",
                "repo_locator": ".loom/shadow/review-repo.json",
            },
            "merge_ready": {
                "summary": "Compare merge-ready parity.",
                "loom_locator": ".loom/shadow/merge-ready-loom.json",
                "repo_locator": ".loom/shadow/merge-ready-repo.json",
            },
            "closeout": {
                "summary": "Compare closeout parity.",
                "loom_locator": ".loom/shadow/closeout-loom.json",
                "repo_locator": ".loom/shadow/closeout-repo.json",
            },
        },
    }

    with tempfile.TemporaryDirectory(prefix="loom-check-repo-interop-") as tmp:
        base = Path(tmp)

        absent_target = base / "absent"
        shutil.copytree(example_target, absent_target)
        absent_surface = build_governance_surface(absent_target)
        repo_interop = absent_surface.get("repo_interop")
        require_repo_interop_payload(
            failures,
            category="repo-interop",
            context="absent repo interop",
            payload=repo_interop,
        )
        if not isinstance(repo_interop, dict) or repo_interop.get("availability") != "absent":
            failures.append(Failure("repo-interop", "absent repo interop sample must report `availability: absent`"))

        invalid_target = base / "invalid"
        shutil.copytree(example_target, invalid_target)
        install_interop(
            invalid_target,
            interop={
                "schema_version": "loom-repo-interop/v1",
                "host_adapters": [
                    {
                        "id": "bad-adapter",
                        "summary": "Broken adapter",
                        "surfaces": ["guardian"],
                        "locator": "host/missing.json",
                    }
                ],
                "repo_native_carriers": [],
                "shadow_surfaces": {
                    "admission": {
                        "summary": "Compare admission parity.",
                        "loom_locator": ".loom/shadow/admission-loom.json",
                        "repo_locator": ".loom/shadow/admission-repo.json",
                    }
                },
            },
        )
        invalid_surface = build_governance_surface(invalid_target)
        invalid_interop = invalid_surface.get("repo_interop")
        require_repo_interop_payload(
            failures,
            category="repo-interop",
            context="invalid repo interop",
            payload=invalid_interop,
        )
        if not isinstance(invalid_interop, dict) or invalid_interop.get("availability") != "incomplete":
            failures.append(Failure("repo-interop", "invalid repo interop sample must report `availability: incomplete`"))

        present_target = base / "present"
        shutil.copytree(example_target, present_target)
        install_interop(present_target, interop=valid_interop)
        present_surface = build_governance_surface(present_target)
        present_interop = present_surface.get("repo_interop")
        require_repo_interop_payload(
            failures,
            category="repo-interop",
            context="present repo interop",
            payload=present_interop,
        )
        if not isinstance(present_interop, dict) or present_interop.get("availability") != "present":
            failures.append(Failure("repo-interop", "present repo interop sample must report `availability: present`"))

        parity_payload, error = load_command_json(
            root,
            ["python3", "tools/loom_flow.py", "shadow-parity", "--target", str(present_target)],
        )
        if error:
            failures.append(Failure("repo-interop", f"`shadow-parity` sample failed: {error}"))
        else:
            require_shadow_parity_payload(
                failures,
                category="repo-interop",
                context="`shadow-parity` present sample",
                payload=parity_payload,
                expected_reports=4,
            )
            if parity_payload.get("result") != "pass":
                failures.append(Failure("repo-interop", "`shadow-parity` must pass when all declared surfaces match"))

        blocking_match_payload, error = load_command_json(
            root,
            ["python3", "tools/loom_flow.py", "shadow-parity", "--target", str(present_target), "--blocking"],
        )
        if error:
            failures.append(Failure("repo-interop", f"`shadow-parity --blocking` match sample failed: {error}"))
        else:
            require_shadow_parity_payload(
                failures,
                category="repo-interop",
                context="`shadow-parity --blocking` match sample",
                payload=blocking_match_payload,
                expected_reports=4,
            )
            if blocking_match_payload.get("result") != "pass":
                failures.append(Failure("repo-interop", "`shadow-parity --blocking` must pass when all declared surfaces match"))

        mismatch_target = base / "mismatch"
        shutil.copytree(present_target, mismatch_target)
        write_json(mismatch_target / ".loom/shadow/review-repo.json", {"decision": "block"})
        mismatch_payload, error = load_command_json(
            root,
            ["python3", "tools/loom_flow.py", "shadow-parity", "--target", str(mismatch_target), "--surface", "review"],
        )
        if error:
            failures.append(Failure("repo-interop", f"`shadow-parity` mismatch sample failed: {error}"))
        else:
            require_shadow_parity_payload(
                failures,
                category="repo-interop",
                context="`shadow-parity` mismatch sample",
                payload=mismatch_payload,
                expected_reports=1,
            )
            reports = mismatch_payload.get("reports")
            if not isinstance(reports, list) or not reports or reports[0].get("result") != "mismatch":
                failures.append(Failure("repo-interop", "`shadow-parity` mismatch sample must report `mismatch`"))

        blocking_mismatch_payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "shadow-parity",
                "--target",
                str(mismatch_target),
                "--surface",
                "review",
                "--mode",
                "blocking",
            ],
        )
        if error:
            failures.append(Failure("repo-interop", f"`shadow-parity --mode blocking` mismatch sample failed: {error}"))
        else:
            require_shadow_parity_payload(
                failures,
                category="repo-interop",
                context="`shadow-parity --mode blocking` mismatch sample",
                payload=blocking_mismatch_payload,
                expected_reports=1,
            )
            if blocking_mismatch_payload.get("result") != "block":
                failures.append(Failure("repo-interop", "`shadow-parity --mode blocking` must block mismatches"))

        unreadable_target = base / "unreadable"
        shutil.copytree(present_target, unreadable_target)
        (unreadable_target / ".loom/shadow/closeout-repo.json").unlink()
        blocking_unreadable_payload, error = load_command_json(
            root,
            [
                "python3",
                "tools/loom_flow.py",
                "shadow-parity",
                "--target",
                str(unreadable_target),
                "--surface",
                "closeout",
                "--blocking",
            ],
        )
        if error:
            failures.append(Failure("repo-interop", f"`shadow-parity --blocking` unreadable sample failed: {error}"))
        else:
            require_shadow_parity_payload(
                failures,
                category="repo-interop",
                context="`shadow-parity --blocking` unreadable sample",
                payload=blocking_unreadable_payload,
                expected_reports=1,
            )
            if blocking_unreadable_payload.get("result") != "block":
                failures.append(Failure("repo-interop", "`shadow-parity --blocking` must block unreadable surfaces"))

    return failures


def check_node_installer(root: Path) -> list[Failure]:
    category = "node-installer"
    failures: list[Failure] = []
    package_root = root / "packages/loom-installer"
    if not package_root.exists():
        return [Failure(category, "missing `packages/loom-installer`")]
    npm_bin = shutil.which("npm")
    if not npm_bin:
        return [Failure(category, "`npm` is required to validate the Node installer")]

    commands = (
        ["npm", "ci"],
        ["npm", "test"],
        ["npm", "pack", "--dry-run"],
    )
    for args in commands:
        try:
            result = run_command(root, args, cwd=package_root, timeout_seconds=300)
        except subprocess.TimeoutExpired:
            failures.append(Failure(category, f"`{' '.join(args)}` timed out"))
            continue
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "command failed without output"
            failures.append(Failure(category, f"`{' '.join(args)}` failed: {detail}"))
    return failures


def check_generated_artifacts_untracked(root: Path) -> list[Failure]:
    if not (root / ".git").exists():
        return []
    result = run_command(
        root,
        ["git", "ls-files", *GENERATED_TRACKED_PATHS],
        timeout_seconds=30,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git ls-files failed"
        return [Failure("generated-artifacts", detail)]
    tracked = [line for line in result.stdout.splitlines() if line.strip()]
    if not tracked:
        return []
    preview = ", ".join(tracked[:8])
    suffix = "" if len(tracked) <= 8 else f", ... (+{len(tracked) - 8} more)"
    return [
        Failure(
            "generated-artifacts",
            f"generated payload paths must not be tracked: {preview}{suffix}",
        )
    ]


def check_github_cli_budget(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    forbidden = tuple(f"gh {kind} view" for kind in ("repo", "issue", "pr"))
    search_roots = [root / "skills/shared/scripts", root / "tools"]
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in search_root.rglob("*.py"):
            if path.name == "loom_check.py":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for needle in forbidden:
                if needle in text:
                    failures.append(
                        Failure(
                            "github-api-budget",
                            f"`{needle}` must not be used in high-frequency implementation path `{path.relative_to(root)}`",
                        )
                    )
    return failures


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def collect_failures(root: Path) -> list[Failure]:
    failures: list[Failure] = []
    failures.extend(check_required_paths(root, "top-level-dirs", TOP_LEVEL_DIRS))
    failures.extend(check_required_paths(root, "top-level-files", TOP_LEVEL_FILES))
    failures.extend(check_required_paths(root, "area-readmes", AREA_READMES))
    failures.extend(check_required_paths(root, "core-docs", CORE_DOCS))
    failures.extend(
        check_required_paths(root, "automation-frontload-templates", AUTOMATION_FRONTLOAD_TEMPLATES)
    )
    failures.extend(check_required_paths(root, "automation-frontload-skills", AUTOMATION_FRONTLOAD_SKILLS))
    failures.extend(
        check_required_paths(
            root,
            "automation-frontload-execution-support",
            AUTOMATION_FRONTLOAD_EXECUTION_SUPPORT,
        )
    )
    failures.extend(check_root_route_contracts(root))
    failures.extend(check_skill_manifests(root))
    failures.extend(check_skill_routing(root))
    failures.extend(check_demo_assets(root))
    failures.extend(check_demo_fact_chain(root))
    failures.extend(check_demo_repo_local_cli(root))
    failures.extend(check_deep_existing_repo_bootstrap(root))
    failures.extend(check_daily_execution_cli(root))
    failures.extend(check_repo_companion_interface_contracts(root))
    failures.extend(check_repo_interop_contracts(root))
    failures.extend(check_node_installer(root))
    failures.extend(check_generated_artifacts_untracked(root))
    failures.extend(check_github_cli_budget(root))
    failures.extend(check_markdown_links(root))
    return failures


def print_report(root: Path, failures: list[Failure]) -> None:
    categories_checked = 17
    if not failures:
        print(f"loom_check: OK ({root})")
        print(f"checked {categories_checked} surfaces")
        return

    grouped: dict[str, list[str]] = defaultdict(list)
    for failure in failures:
        grouped[failure.category].append(failure.detail)

    print(f"loom_check: FAILED ({root})")
    for category in sorted(grouped):
        print(f"- {category}")
        for detail in grouped[category]:
            print(f"  - {detail}")
    print(f"failures: {len(failures)} across {len(grouped)} categories")


def main(argv: list[str]) -> int:
    root = repo_root_from_argv(argv)
    if not root.exists():
        print(f"loom_check: repo root does not exist: {root}", file=sys.stderr)
        return 2
    failures = collect_failures(root)
    print_report(root, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
