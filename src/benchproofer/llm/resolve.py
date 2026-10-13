# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Turning settings into a configured provider."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ..config import Settings
from ..errors import PluginError, ProviderError
from ..log import logger
from .agentic import AgentSession
from .base import Provider, ProviderConfig

__all__ = [
    "NO_SESSION",
    "require_session",
    "resolve",
    "reviewer",
    "session_for",
    "toolchains",
]

log = logger(__name__)

#: What a stage that cannot run without an agent session says when the run has none.
NO_SESSION = (
    "{stage} needs an agent session, and this run has none: install `benchproofer[agent]` "
    "and the `claude` command-line tool, and run with `session` naming one (`claude-code`, "
    "the default) and without `--offline`"
)

#: The variables naming the Lake workspace a Lean or a Velvet checker reads its packages
#: from (`backends.lean4`, `backends.velvet`), which a session's proof search reads too.
_LAKE = ("BENCHPROOFER_LEAN_WORKSPACE", "BENCHPROOFER_VELVET")
#: Where the Lean toolchain manager keeps its toolchains, unless `ELAN_HOME` says otherwise.
_ELAN = "~/.elan"


def resolve(settings: Settings) -> Provider:
    """Look up the provider named in ``settings`` and configure it for drafting.

    Raises:
        PluginError: The settings name a provider that is not registered.
    """
    from ..registries import PROVIDERS

    return _configured(PROVIDERS.get(settings.provider), settings, settings.model)


def session_for(settings: Settings, model: str = "") -> AgentSession | None:
    """The agent session this run may use, or None when it has none it can use.

    None when the settings name no session, the one they name is not registered or cannot
    run on this machine, or it reaches a model (`AgentSession.remote`) and the run is
    offline, since it does so over the network; the stage that asks reports each the same
    way.

    ``model`` is the model the session runs on; empty means `session_model`, or the
    drafting model when that is unset. Each call builds its own instance, because the
    tasks of a run go through their stages side by side and one instance pointed at
    the reviewing model for one of them would move another's repair onto it.
    """
    from ..registries import SESSIONS

    if not settings.session:
        return None
    try:
        found = SESSIONS.build(settings.session)
    except PluginError:
        log.warning("no session named %r is registered", settings.session)
        return None
    if found.remote and settings.offline:
        return None
    found.model = model or settings.session_model or settings.model
    found.record_dir = settings.cassette_dir / "sessions" if settings.record else None
    found.readable = toolchains(settings)
    # As long as `./tools run` gives a program, the longest anything a session runs takes.
    found.command_timeout_s = float(settings.oracle_timeout_s)
    available = found.availability()
    if not available:
        log.info("session %r cannot run here: %s", settings.session, available.detail)
        return None
    return found


def toolchains(settings: Settings) -> tuple[Path, ...]:
    """What every session may read besides its own workspace: the toolchains it may need.

    The Python environment this run runs in, with the verifiers installed in it, and the
    interpreter installation it was made from; the directory `scripts/install/*.sh` puts
    verifier toolchains in (`Settings.toolchain_dir`); the Lean toolchains; and the Lake
    workspace a Lean or a Velvet checker reads its packages from. Each that this machine
    has, resolved, once.
    """
    lake = [os.environ[name] for name in _LAKE if os.environ.get(name)]
    spelled: list[str | Path] = [
        sys.prefix,
        sys.base_prefix,
        settings.toolchain_dir,
        os.environ.get("ELAN_HOME") or _ELAN,
        *lake,
    ]
    found: list[Path] = []
    for place in spelled:
        path = Path(place).expanduser().resolve()
        if path.exists() and path not in found:
            found.append(path)
    return tuple(found)


def require_session(settings: Settings, stage: str, model: str = "") -> AgentSession:
    """The agent session `session_for` gives, for a stage that cannot run without one.

    ``stage`` names the stage in the error, as a sentence opens with it.

    Raises:
        ProviderError: The run has no session it can use (`NO_SESSION`).
    """
    found = session_for(settings, model)
    if found is None:
        raise ProviderError(NO_SESSION.format(stage=stage))
    return found


def reviewer(settings: Settings) -> Provider:
    """The provider the review stage uses, configured with ``audit_model``.

    A separate instance, not the drafting one reconfigured: the two stages run over the
    same bundle in one command, and a single object cannot be pointed at two models at
    once. When ``audit_model`` is unset this returns the drafting model, which the
    `audit.independence` gate then reports as a self-review rather than counting.

    Raises:
        PluginError: The settings name a provider that is not registered.
    """
    from ..registries import PROVIDERS

    return _configured(
        PROVIDERS.build(settings.provider), settings, settings.audit_model or settings.model
    )


def _configured(provider: Provider, settings: Settings, model: str) -> Provider:
    """Apply the run's settings to one provider instance."""
    provider.configure(
        ProviderConfig(
            model=model,
            cassette_dir=settings.cassette_dir,
            offline=settings.offline,
        )
    )
    return provider
