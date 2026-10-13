# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The scripts an agent session runs Benchproofer through, with the run's own settings.

A session that repairs or reviews a bundle runs the checker, the gates and the task's
environment from a shell of its own, which sees neither the run's command-line options nor
the `benchproofer.toml` it was started beside. So each script sets every setting the run
resolved and puts the copy of Benchproofer the run imported first on the module path, and
what the session runs judges as the run's gates do.

Every setting but the ones that reach a model (`NO_MODEL`): these scripts judge and never
draft or review, and a session that could reach a model through one could run the
model-backed review of its own bundle, as a command composed from the script's own line.

The settings and the module path are not in the script but in a file outside the
workspace that it reads (`script`), which a session may not read: they say where this
tool's source is and how the run is set, and a session's own environment has neither
(`private`).
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import ENV_PREFIX, Settings
from ..util.digest import digest_text, short
from ..util.fsio import write_text
from .bundle import Bundle
from .prompts import SHARED
from .task import Task

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = ["NO_MODEL", "SCRATCH", "lay_out", "private", "script", "tools_rules"]

#: The settings that reach a model, as a script sets them: the provider that refuses every
#: request, no model, and no agent session.
NO_MODEL: dict[str, str] = {
    "provider": "null",
    "model": "",
    "audit_model": "",
    "session": "",
    "session_model": "",
}

#: Where a session puts files of its own, inside its workspace rather than in the project
#: directory a backend's checker may run from, which every session on this machine shares.
SCRATCH = "scratch"


def lay_out(root: Path, task: Task, backend: str, settings: Settings) -> Bundle:
    """Lay out a session's workspace at ``root``, replacing what is there.

    A bundle root holding the task, with an empty bundle for ``backend`` in it; `scratch/`
    for the session's own files; and `./tools` over that bundle (`benchproofer.audit.tools`),
    which keeps its own files beside the bundle root, so the bundle has to sit where this
    puts it.

    Returns:
        The bundle in the workspace, at `bundles/<benchmark>/<task>/<backend>`.
    """
    shutil.rmtree(root, ignore_errors=True)
    copy = Bundle.create(root / "bundles", task, backend)
    (root / SCRATCH).mkdir()
    script(
        root / "tools", ["benchproofer.audit.tools", "--bundle", copy.root.as_posix()], settings
    )
    return copy


def script(
    path: Path, module: Sequence[str], settings: Settings, *, pinned: Sequence[str] = ()
) -> str:
    """Write an executable script running ``python -m <module...>`` with these settings.

    The arguments the script is run with follow ``module``, and ``pinned`` follows them, so
    an option given both ways takes the pinned value. What the script runs with is read
    from a file under the cache directory (`_environment`), outside every session's
    workspace: each setting, the module path, and the run's own value of each variable a
    session's environment empties or sets (`private`, `TMPDIR`), so Benchproofer runs as
    the run does whatever the session's shell holds.

    Returns:
        The script's path, quoted for a shell, for a prompt to name.
    """
    environment = _environment(settings)
    after = f" {shlex.join(pinned)}" if pinned else ""
    write_text(
        path,
        "#!/bin/sh\n"
        "set -a\n"
        f". {shlex.quote(environment.as_posix())}\n"
        "set +a\n"
        f'exec {shlex.join([sys.executable, "-m", *module])} "$@"{after}\n',
    )
    path.chmod(0o755)
    return shlex.quote(path.as_posix())


def tools_rules(
    settings: Settings, task: Task, backend: Backend, *, session_s: float, check: bool = False
) -> str:
    """What every session given `./tools` is told of them (`core/templates/tools-rules.md`).

    With the time limits the run sets: the checker's (`Backend.budget`), a program's in the
    task's environment (`Settings.oracle_timeout_s`, or the task's own where that is shorter,
    as the oracle takes it), a fuzzer's (`Settings.harness_timeout_s`, likewise) and one shell
    command's (`claude_code.environment`); with what `verify` prints of a proof's
    completeness under this backend (`Backend.closure_note`); and with the session's clock:
    the time it starts, which is now, and the time ``session_s`` later at which it is stopped.
    ``check`` is for a session whose workspace also has `./check`, a repair's, which is
    described to it as well (`check-rules.md`).
    """
    started = time.time()
    program_limit = f"{min(settings.harness_timeout_s, task.oracle.timeout_s):.0f}"
    checks = SHARED.render("check-rules", program_limit=program_limit).rstrip() if check else ""
    return SHARED.render(
        "tools-rules",
        check_rules=f"\n{checks}" if checks else "",
        checker_limit=f"{backend.budget(settings.verify_timeout_s):.0f}",
        closure=f" {backend.closure_note}" if backend.closure_note else "",
        run_limit=f"{min(settings.oracle_timeout_s, task.oracle.timeout_s):.0f}",
        program_limit=program_limit,
        command_limit=f"{min(session_s, settings.oracle_timeout_s):.0f}",
        started=_clock(started),
        stops=_clock(started + session_s),
        budget=f"{session_s / 60:.0f}",
    ).rstrip()


def _clock(seconds: float) -> str:
    """A moment as `date -u` reads it, to the second."""
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(seconds))


def private(environ: Mapping[str, str]) -> tuple[str, ...]:
    """The variables of ``environ`` a session's environment leaves empty.

    The module path and every Benchproofer setting: one says where Benchproofer's source
    is, and the settings say how the run is set, which nothing a session does needs.
    """
    return tuple(
        name for name in environ if name == "PYTHONPATH" or name.startswith(ENV_PREFIX)
    )


def _environment(settings: Settings) -> Path:
    """Write the file a script reads what it runs with from, and return its path.

    Named by its content, so the scripts of one run share it. Each line sets or unsets one
    variable, for a shell to read with every assignment exported.
    """
    # A path is made absolute, since the session's shell starts somewhere else.
    resolved = {
        name: getattr(settings, name).resolve()
        for name in type(settings).model_fields
        if isinstance(getattr(settings, name), Path)
    }
    judging = settings.model_copy(update={**resolved, **NO_MODEL})
    assigned = {
        f"{ENV_PREFIX}{name.upper()}": _setting(value)
        for name, value in judging.model_dump(mode="json").items()
        if name != "bundle_root"
    }
    # Other `BENCHPROOFER_*` variables, such as where a backend's workspace is, go too.
    assigned |= {
        name: value
        for name, value in sorted(os.environ.items())
        if name.startswith(ENV_PREFIX) and name not in assigned
    }
    found = [Path(__file__).resolve().parents[2].as_posix()]
    inherited = os.environ.get("PYTHONPATH", "")
    assigned["PYTHONPATH"] = os.pathsep.join([*found, *([inherited] if inherited else [])])
    if "TMPDIR" in os.environ:
        assigned["TMPDIR"] = os.environ["TMPDIR"]
    # What a session's environment has that the run's does not.
    cleared = sorted({*private(os.environ), "TMPDIR"} - set(assigned))
    lines = [f"{name}={shlex.quote(value)}" for name, value in assigned.items()]
    lines += [f"unset {name}" for name in cleared]
    text = "\n".join(lines) + "\n"
    path = settings.cache_dir.resolve() / "environments" / f"{short(digest_text(text), 16)}.sh"
    if not path.is_file():
        write_text(path, text)
    return path


def _setting(value: object) -> str:
    """One setting as the environment spells it: JSON for anything but a plain value."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, separators=(",", ":"))
