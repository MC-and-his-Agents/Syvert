from __future__ import annotations

import os
from pathlib import Path


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def syvert_state_dir() -> Path:
    return codex_home() / "state" / "syvert"


def guardian_state_path() -> Path:
    return syvert_state_dir() / "guardian.json"


def guardian_legacy_state_path() -> Path:
    return codex_home() / "state" / "syvert-pr-guardian-results.json"


def review_poller_state_path() -> Path:
    return syvert_state_dir() / "review-poller.json"


def review_poller_legacy_state_path() -> Path:
    return codex_home() / "state" / "syvert-pr-review.json"


def worktrees_state_path() -> Path:
    return syvert_state_dir() / "worktrees.json"
