# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What to run: the case catalog, and the named selections over it.

Cases live in `benchproofer.smoke.cases`, one module per group. This module is the
only place that knows the whole list, so adding a group is a new module plus one
entry in `_MODULES`.

Three ways to name work, in the order `select` tries them:

============================  =================================================
a suite, such as ``offline``  a predicate over every case, listed in `SUITES`
a group, such as ``gates``    every case in one module
a case id, ``gates.waiver``   exactly one case
============================  =================================================

``offline`` is defined by what a case declares rather than by a hand-kept list: a
case is hermetic when it needs neither the network nor a container runtime. A new
case that only touches the packaged fixtures therefore joins the hermetic suite by
itself, and one that reaches for a dataset cannot join it by accident. The suite leaves
out the cases that take minutes unless ``--slow`` asks for them, so a slow case that is
otherwise hermetic stays reachable through it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import ModuleType

from ..errors import BenchproofError
from .cases import backends, benchmarks, gates, oracles, pipeline, registry, review
from .model import Case

__all__ = ["GROUPS", "SUITES", "Suite", "cases", "select"]

#: Case modules, in the order a full run visits them: cheap and diagnostic first,
#: so an installation problem is reported before a case spends a minute on it.
_MODULES: tuple[ModuleType, ...] = (
    registry,
    backends,
    benchmarks,
    oracles,
    gates,
    pipeline,
    review,
)

#: Requirements that take a case outside a hermetic run.
_EXTERNAL = frozenset({"network", "docker"})


@dataclass(frozen=True, slots=True)
class Suite:
    """A named selection of cases."""

    name: str
    summary: str
    includes: Callable[[Case], bool]
    #: True for a suite that is meant to finish quickly, so it leaves out the cases
    #: that take minutes until a run asks for them.
    quick: bool = False

    def cases(self, *, include_slow: bool = False) -> tuple[Case, ...]:
        """The cases this suite selects, in catalog order."""
        omit_slow = self.quick and not include_slow
        return tuple(
            item for item in cases() if self.includes(item) and not (omit_slow and item.slow)
        )


def _hermetic(item: Case) -> bool:
    """True when a case needs nothing but this machine and the packaged fixtures."""
    return not (_EXTERNAL & set(item.requires))


def _grouped(modules: Iterable[ModuleType]) -> dict[str, tuple[Case, ...]]:
    """Collect every module's cases, keyed by the group their ids declare.

    Raises:
        BenchproofError: Two cases share an id. Ids identify results in a report and
            on the command line, so a duplicate would make one case invisible.
    """
    groups: dict[str, list[Case]] = {}
    seen: dict[str, str] = {}
    for module in modules:
        for item in module.CASES:
            if item.id in seen:
                raise BenchproofError(
                    f"two smoke cases are called {item.id!r}: one in {seen[item.id]} and "
                    f"one in {module.__name__}"
                )
            seen[item.id] = module.__name__
            groups.setdefault(item.group, []).append(item)
    return {name: tuple(items) for name, items in groups.items()}


#: Every case, by group, in the order a full run visits them.
GROUPS: dict[str, tuple[Case, ...]] = _grouped(_MODULES)

#: The named suites.
SUITES: dict[str, Suite] = {
    "offline": Suite(
        name="offline",
        summary="everything that runs with no network, no container, and no API key",
        includes=_hermetic,
        quick=True,
    ),
    "all": Suite(
        name="all",
        summary="every case; those this machine cannot run are reported as skipped",
        includes=lambda _: True,
    ),
}


def cases() -> tuple[Case, ...]:
    """Every registered case, in catalog order."""
    return tuple(item for group in GROUPS.values() for item in group)


def select(name: str, *, include_slow: bool = False) -> tuple[Case, ...]:
    """Resolve a suite name, a group name, or a case id to the cases it names.

    Args:
        name: What to run.
        include_slow: Whether the run asked for the cases that take minutes. A group
            or a case named directly is selected either way, and the runner is what
            skips a slow one; only a suite leaves them out of the selection.

    Raises:
        BenchproofError: The name matches nothing. The message lists what does.
    """
    wanted = name.strip()
    if wanted in SUITES:
        return SUITES[wanted].cases(include_slow=include_slow)
    if wanted in GROUPS:
        return GROUPS[wanted]
    found = tuple(item for item in cases() if item.id == wanted)
    if found:
        return found
    raise BenchproofError(
        f"nothing to run for {name!r}. Suites: {', '.join(SUITES)}. "
        f"Groups: {', '.join(GROUPS)}. "
        f"Cases: {', '.join(item.id for item in cases())}"
    )
