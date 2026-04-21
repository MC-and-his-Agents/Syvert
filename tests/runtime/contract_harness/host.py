from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from syvert.runtime import TaskInput, TaskRequest, execute_task

DEFAULT_HARNESS_ADAPTER_KEY = "fake"
DEFAULT_HARNESS_CAPABILITY = "content_detail_by_url"


@dataclass(frozen=True)
class HarnessExecutionInput:
    sample_id: str
    url: str
    adapter_key: str = DEFAULT_HARNESS_ADAPTER_KEY
    capability: str = DEFAULT_HARNESS_CAPABILITY


def execute_harness_sample(
    sample: HarnessExecutionInput,
    *,
    adapters: Mapping[str, Any],
    task_id: str | None = None,
    resource_lifecycle_store: Any | None = None,
) -> dict[str, Any]:
    request = TaskRequest(
        adapter_key=sample.adapter_key,
        capability=sample.capability,
        input=TaskInput(url=sample.url),
    )
    if task_id is None:
        return execute_task(request, adapters=adapters, resource_lifecycle_store=resource_lifecycle_store)
    return execute_task(
        request,
        adapters=adapters,
        task_id_factory=lambda: task_id,
        resource_lifecycle_store=resource_lifecycle_store,
    )
