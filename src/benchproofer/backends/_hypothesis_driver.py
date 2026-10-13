# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run a solution module's property functions in a child process.

Usage: ``python -m benchproofer.backends._hypothesis_driver <file> <examples>``.

The search is derandomized, so two runs of the same file try the same inputs and a
recorded result is reproducible. Exit codes: 0 when no property was falsified, 1
when one was, 2 when the module could not be imported, 65 when it declares no
properties.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from types import ModuleType

PROPERTY_PREFIX = "property_"


def load(path: Path) -> ModuleType:
    """Import a module from an explicit path under a private name."""
    spec = importlib.util.spec_from_file_location("benchproofer_solution", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    """Import one solution module and run every property it declares."""
    if len(argv) != 2:
        print("usage: _hypothesis_driver <file> <examples>", file=sys.stderr)
        return 64
    path, examples = Path(argv[0]), int(argv[1])

    from hypothesis import settings

    settings.register_profile(
        "benchproofer", derandomize=True, deadline=None, max_examples=examples
    )
    settings.load_profile("benchproofer")

    try:
        module = load(path)
    except Exception:  # noqa: BLE001 - importing a drafted file: any failure means 2
        traceback.print_exc()
        return 2

    properties = sorted(name for name in dir(module) if name.startswith(PROPERTY_PREFIX))
    if not properties:
        print(f"no {PROPERTY_PREFIX}* function found", file=sys.stderr)
        return 65

    for name in properties:
        try:
            getattr(module, name)()
        except Exception as exc:  # noqa: BLE001 - a falsified property raises anything
            print(f"{name}: {type(exc).__name__}: {exc}".strip(), file=sys.stderr)
            return 1
    print(f"{len(properties)} property/properties held over {examples} examples")
    return 0


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main(sys.argv[1:]))
