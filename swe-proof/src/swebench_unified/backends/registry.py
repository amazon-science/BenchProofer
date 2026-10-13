# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Backend registry: the single place that maps backend names to instances."""
from __future__ import annotations

from .base import Backend
from .ears import EarsBackend
from .lean import LeanBackend
from .nagini import NaginiBackend
from .velvet import VelvetBackend

BACKENDS: dict[str, type[Backend]] = {
    "nagini": NaginiBackend,
    "velvet": VelvetBackend,
    "lean": LeanBackend,
    "ears": EarsBackend,
}

# The backends the RELEASE GATE covers, which is not the set that ships: `ears`
# ships too, but it has no verifier (backends/ears.py), so the gates whose
# records the release checks read -- G-VERIFY, G-PBT, G-MUT -- deliberately leave
# it out of `applies_to` and record explicit skips. A tool that walked all four
# would report every ears bundle as unjudged forever.
#
# THE one definition, kept here because this module already owns the backend
# vocabulary: a release check that hand-writes its own copy goes stale against
# the registry the moment a proof backend is added.
GATED_BACKENDS: tuple[str, ...] = ("nagini", "velvet", "lean")

_instances: dict[str, Backend] = {}


def get_backend(name: str) -> Backend:
    if name not in BACKENDS:
        raise ValueError(f"unknown backend {name!r}; expected one of {sorted(BACKENDS)}")
    if name not in _instances:
        _instances[name] = BACKENDS[name]()
    return _instances[name]
