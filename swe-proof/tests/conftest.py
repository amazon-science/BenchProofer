# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Session-wide guards for the two ways a test can quietly stop testing anything.

Both of these were real. Neither announced itself: one cost a six-minute live
agent call inside what looked like a unit test, and the other is the reason that
call came back with the exact verdict its test exists to forbid.
"""
from __future__ import annotations

import sys

import pytest

# The `env` fixture the test_gates*.py families share. It is defined next to the
# synthetic bundle it builds (tests/gates_fixtures.py) and re-exported here so
# pytest resolves it by name in all four files: importing it into each of them
# instead would put a module-level `env` binding in front of the `env` parameter
# of every test in the file, which is a redefinition (ruff F811) ~60 times over.
from gates_fixtures import env  # noqa: F401

PKG = "swebench_unified"


def _submodule_identity_mismatches() -> list[str]:
    """Names where `sys.modules[...]` and the parent package attribute disagree.

    A module can be reached two ways, and they do not use the same lookup:

        import swebench_unified.agent as m   -> the parent package's attribute
        from ..agent import run_agent_step   -> sys.modules

    Normally both point at one object. A test that re-imports a module to pick
    up env-derived constants breaks that: `importlib.import_module` installs a
    new object in BOTH places, and `monkeypatch.delitem(sys.modules, ...)`
    restores only the first at teardown. The package attribute keeps the copy,
    for every test that runs afterwards.

    The result is not a copy winning, which would be survivable. It is a split:
    a later test patches the attribute's copy while the code under test calls
    the one in sys.modules. The patch lands on nothing, the real function runs,
    and the test reports on production behaviour it believes it stubbed out.
    """
    pkg = sys.modules.get(PKG)
    if pkg is None:
        return []
    bad = []
    for name, mod in list(sys.modules.items()):
        if not name.startswith(PKG + ".") or mod is None:
            continue
        leaf = name[len(PKG) + 1:]
        if "." in leaf:                      # only direct children have an attr
            continue
        attr = getattr(pkg, leaf, None)
        if attr is not None and attr is not mod:
            bad.append(name)
    return bad


@pytest.fixture(autouse=True)
def _no_leaked_module_copies():
    """Fail the test that leaks a module copy, not the unrelated one that trips.

    Autouse and conftest-level, so it is set up before the function-scoped
    fixtures a test asks for and therefore torn down AFTER them -- which is the
    whole point: `monkeypatch` has already run its undo stack by then, so
    anything still mismatched here is a leak monkeypatch was never told about
    rather than one it was about to clean up.
    """
    before = set(_submodule_identity_mismatches())
    yield
    leaked = sorted(set(_submodule_identity_mismatches()) - before)
    if leaked:
        raise AssertionError(
            "this test left a second copy of "
            + ", ".join(leaked)
            + " installed: sys.modules and the swebench_unified package"
            " attribute now point at different objects, so a later test's patch"
            " can land on one while the code under test calls the other."
            " If you re-imported the module, register the undo for the package"
            " attribute too:\n"
            "    monkeypatch.setattr(swebench_unified, '<name>',"
            " getattr(swebench_unified, '<name>', None), raising=False)\n"
            "before evicting it from sys.modules."
        )
