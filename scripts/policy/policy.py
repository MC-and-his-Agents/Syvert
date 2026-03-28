from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from scripts.common import REPO_ROOT, load_json


POLICY_PATH = REPO_ROOT / "scripts" / "policy" / "policy.json"


@dataclass(frozen=True)
class ClassifiedPath:
    path: str
    category: str


def get_policy() -> dict:
    return load_json(POLICY_PATH)


def classify_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    policy = get_policy()
    for rule in policy["path_categories"]:
        for pattern in rule["patterns"]:
            if fnmatch(normalized, pattern):
                return rule["name"]
    return "implementation"


def classify_paths(paths: Iterable[str]) -> list[ClassifiedPath]:
    return [ClassifiedPath(path=path, category=classify_path(path)) for path in paths]


def allowed_categories(pr_class: str) -> set[str]:
    policy = get_policy()
    return set(policy["allowed_categories"][pr_class])


def risk_level(pr_class: str) -> str:
    return get_policy()["risk_levels"][pr_class]


def spec_suite_policy() -> dict:
    return get_policy()["spec_suite"]


def formal_spec_dirs(paths: Iterable[str]) -> set[Path]:
    output: set[Path] = set()
    for path in paths:
        normalized = Path(path)
        parts = normalized.parts
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "specs" and parts[2].startswith("FR-"):
            output.add(Path(*parts[:3]))
    return output
