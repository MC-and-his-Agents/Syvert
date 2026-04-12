from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from scripts.common import REPO_ROOT, load_json


@dataclass
class Policy:
    commit_regex: re.Pattern[str]
    path_categories: Dict[str, List[str]]
    class_matrix: Dict[str, Set[str]]
    spec_guard: dict

    def category_for_path(self, path: str) -> str:
        normalized = path.strip().replace("\\", "/").lstrip("./")
        if not normalized:
            return "implementation"
        # Priority order matters.
        for key in ("governance", "spec_todo", "spec", "docs", "implementation"):
            for pattern in self.path_categories.get(key, []):
                from fnmatch import fnmatch

                if fnmatch(normalized, pattern):
                    return key
        return "implementation"


def _normalize_path_categories(raw: dict) -> Dict[str, List[str]]:
    if "paths" in raw and isinstance(raw["paths"], dict):
        return {k: list(v) for k, v in raw["paths"].items()}
    if "path_categories" in raw and isinstance(raw["path_categories"], list):
        categories: Dict[str, List[str]] = {}
        for item in raw["path_categories"]:
            if isinstance(item, dict) and "name" in item:
                categories[item["name"]] = list(item.get("patterns", []))
        return categories
    raise KeyError("path_categories")


def _normalize_class_matrix(raw: dict) -> Dict[str, Set[str]]:
    matrix_raw = {}
    if "pr_scope" in raw and isinstance(raw["pr_scope"], dict):
        matrix_raw = raw["pr_scope"].get("classes", {})
    if not matrix_raw:
        matrix_raw = raw.get("allowed_categories", {})
    matrix = {
        pr_class: set(categories)
        for pr_class, categories in matrix_raw.items()
        if isinstance(categories, list)
    }
    if not matrix:
        raise KeyError("class_matrix")
    return matrix


def _normalize_spec_guard(raw: dict) -> dict:
    spec_guard = raw.get("spec_guard") or raw.get("spec_suite")
    if not isinstance(spec_guard, dict):
        raise KeyError("spec_guard")
    if "required_suite_files" not in spec_guard and "required_files" in spec_guard:
        spec_guard["required_suite_files"] = list(spec_guard["required_files"])
    if "spec_required_headers" not in spec_guard and "spec_required_headings" in spec_guard:
        spec_guard["spec_required_headers"] = list(spec_guard["spec_required_headings"])
    if "plan_required_headers" not in spec_guard and "plan_required_headings" in spec_guard:
        spec_guard["plan_required_headers"] = list(spec_guard["plan_required_headings"])
    return spec_guard


def load_policy() -> Policy:
    raw = load_json(REPO_ROOT / "scripts" / "policy" / "policy.json")
    commit_regex_raw = (
        raw.get("commit", {}).get("regex")
        or raw.get("commit_regex")
        or r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?: .+$"
    )
    return Policy(
        commit_regex=re.compile(commit_regex_raw),
        path_categories=_normalize_path_categories(raw),
        class_matrix=_normalize_class_matrix(raw),
        spec_guard=_normalize_spec_guard(raw),
    )


def load_review_schema_path() -> Path:
    candidates = [
        REPO_ROOT / "scripts" / "policy" / "review_result.schema.json",
        REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("missing review result schema json")

