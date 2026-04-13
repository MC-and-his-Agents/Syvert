from __future__ import annotations

import unittest

from syvert.registry import AdapterRegistry
from syvert.runtime import AdapterTaskRequest
from tests.runtime.contract_harness.fake_adapter import FakeContractAdapter
from tests.runtime.contract_harness.host import (
    DEFAULT_HARNESS_ADAPTER_KEY,
    HarnessExecutionInput,
    execute_harness_sample,
)


class ContractHarnessHostTests(unittest.TestCase):
    def test_executes_fake_adapter_via_standard_runtime_and_registry_path(self) -> None:
        adapter = FakeContractAdapter(scenario="success")
        sample = HarnessExecutionInput(sample_id="sample-success", url="https://example.com/fake/1")

        result = execute_harness_sample(
            sample,
            adapters={DEFAULT_HARNESS_ADAPTER_KEY: adapter},
            task_id="task-harness-success",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["task_id"], "task-harness-success")
        self.assertEqual(result["adapter_key"], DEFAULT_HARNESS_ADAPTER_KEY)
        self.assertEqual(result["capability"], "content_detail_by_url")
        self.assertIsInstance(adapter.last_request, AdapterTaskRequest)
        self.assertEqual(adapter.last_request.capability, "content_detail")
        self.assertEqual(adapter.last_request.target_type, "url")
        self.assertEqual(adapter.last_request.target_value, sample.url)
        self.assertEqual(adapter.last_request.collection_mode, "hybrid")

        registry = AdapterRegistry.from_mapping({DEFAULT_HARNESS_ADAPTER_KEY: adapter})
        self.assertEqual(
            registry.discover_capabilities(DEFAULT_HARNESS_ADAPTER_KEY),
            frozenset({"content_detail"}),
        )
        self.assertEqual(registry.discover_targets(DEFAULT_HARNESS_ADAPTER_KEY), frozenset({"url"}))
        self.assertEqual(
            registry.discover_collection_modes(DEFAULT_HARNESS_ADAPTER_KEY),
            frozenset({"hybrid"}),
        )

    def test_maps_illegal_fake_adapter_payload_to_existing_runtime_contract_failure(self) -> None:
        adapter = FakeContractAdapter(scenario="illegal_payload")
        sample = HarnessExecutionInput(sample_id="sample-illegal", url="https://example.com/fake/2")

        result = execute_harness_sample(
            sample,
            adapters={DEFAULT_HARNESS_ADAPTER_KEY: adapter},
            task_id="task-harness-illegal",
        )

        self.assertEqual(result["task_id"], "task-harness-illegal")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "invalid_adapter_success_payload")


if __name__ == "__main__":
    unittest.main()
