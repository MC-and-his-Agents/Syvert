#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from syvert.resource_bootstrap import (
    bootstrap_resource_store,
    build_bootstrap_records,
    load_account_material,
    load_bootstrap_material,
)
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore, default_resource_lifecycle_store


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap managed account/proxy resources into the lifecycle store."
    )
    parser.add_argument("--adapter", required=True, choices=("xhs", "douyin"))
    parser.add_argument("--account-resource-id", required=True)
    account_source = parser.add_mutually_exclusive_group(required=True)
    account_source.add_argument("--account-material-file")
    account_source.add_argument("--account-session-file")
    parser.add_argument("--proxy-resource-id", required=True)
    parser.add_argument("--proxy-material-file", required=True)
    parser.add_argument("--store-file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        account_material = load_account_material(
            adapter_key=args.adapter,
            account_material_file=Path(args.account_material_file) if args.account_material_file else None,
            account_session_file=Path(args.account_session_file) if args.account_session_file else None,
        )
        proxy_material = load_bootstrap_material(Path(args.proxy_material_file))
        records = build_bootstrap_records(
            adapter_key=args.adapter,
            account_resource_id=args.account_resource_id,
            account_material=account_material,
            proxy_resource_id=args.proxy_resource_id,
            proxy_material=proxy_material,
        )
        store = LocalResourceLifecycleStore(Path(args.store_file)) if args.store_file else default_resource_lifecycle_store()
        seeded = bootstrap_resource_store(store=store, records=records)
    except ValueError as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "status": "failed",
                    "error": {
                        "code": "invalid_bootstrap_input",
                        "message": str(exc),
                    },
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        return 1

    print(
        json.dumps(
            {
                "status": "success",
                "adapter_key": args.adapter,
                "store_file": str(store.path),
                "seeded_resource_ids": sorted(record.resource_id for record in seeded),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
