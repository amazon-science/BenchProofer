# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The task's working copy, on this machine, in the state the task starts from.

A stage that decides what to write by reading the repository needs it on disk; for a
benchmark whose environment is a container, it is exported from the image first.

The state it arrives in matters, since a stage reasoning about a task must not be handed
the fixed code. An image's tree is expected to be the **base** commit, but nothing guarantees
it, so an export is reconciled with what the tool already holds, without running
anything the dataset supplied:

* a file the task ships as **context** whose content differs is written back from the
  task;
* a file the reference patch **creates** is deleted, since a leftover would be the fix.

Either rule firing is logged. Nothing in a working copy is executed.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..log import logger
from ..util.digest import digest_text
from ..util.fsio import write_text
from ..util.patch import touched_paths
from ..util.proc import run
from .task import Task

__all__ = ["Touched", "WorkCopy", "apply", "materialize", "touched"]

log = logger(__name__)

#: The patch is written beside the working copy under this name, so a stage that reads
#: the tree can also read what the task asks for without it being in the tree.
PATCH = "reference.patch"
#: Written into a whole working copy once it is complete, naming the task it is of.
STAMP = ".benchproofer-workcopy"


@dataclass(frozen=True, slots=True)
class WorkCopy:
    """A directory holding the task's code, and how complete it is.

    `whole` is True for the repository, where finding nothing means something, and False
    for only the files the task ships, where it does not.
    """

    root: Path
    whole: bool
    detail: str = ""

    def __bool__(self) -> bool:
        return self.root.is_dir()


def materialize(task: Task, *, into: Path, oracle: object | None = None) -> WorkCopy:
    """Put the task's code at ``into``, as close to its starting state as can be had.

    A whole working copy already at ``into`` laid out for this task is kept rather than
    exported again.

    Args:
        task: The task to lay out.
        into: Where to put it, replacing what is there, so a stale copy of another task
            cannot be read as this one.
        oracle: The task's oracle, asked to `export` its environment's checkout; one
            without that method gets the files the task ships.

    Returns:
        A `WorkCopy`, always a directory; `whole` says whether it is the repository.
    """
    stamp = into / STAMP
    if stamp.is_file() and stamp.read_text(encoding="utf-8") == _stamp(task):
        return WorkCopy(root=into, whole=True, detail="the repository at the task's base state")
    shutil.rmtree(into, ignore_errors=True)
    into.mkdir(parents=True, exist_ok=True)

    exported = None
    export = getattr(oracle, "export", None)
    if callable(export):
        exported = export(task, into=into)

    if exported is None:
        _lay_out(task, into)
        return WorkCopy(
            root=into,
            whole=False,
            detail="only the files the task itself ships; the repository is not available here",
        )

    _rewind(task, into)
    # Written last, so that an export interrupted part way is never reused.
    write_text(stamp, _stamp(task))
    return WorkCopy(root=into, whole=True, detail="the repository at the task's base state")


def _stamp(task: Task) -> str:
    """What identifies the task a working copy was laid out for."""
    return f"{task.key}\n{digest_text(task.reference.patch or '')}\n"


@dataclass(frozen=True, slots=True)
class Touched:
    """The source files a patch touches, by path, as they read before it and after it.

    Empty where the working copy lacks them or the patch does not apply to them.
    """

    before: dict[str, str] = field(default_factory=dict)
    #: Every one the patch leaves in place, those it creates among them.
    after: dict[str, str] = field(default_factory=dict)


def touched(task: Task, copy: WorkCopy, patch: str) -> Touched:
    """The source files ``patch`` touches, as ``copy`` has them and once it is applied.

    ``patch`` is the golden patch or the test patch. It is applied to a scratch copy of
    those files, never to the working copy.
    """
    wanted = touched_paths(patch, source_only=True)
    if not wanted or not copy:
        return Touched()
    with tempfile.TemporaryDirectory(prefix="benchproofer-fixed-") as scratch:
        root = Path(scratch)
        for path in touched_paths(patch):
            source = copy.root / path
            if source.is_file():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, root / path)
        before = _read(root, wanted)
        refused = apply(root, patch)
        if refused:
            log.info("%s: a patch does not apply to the working copy: %s", task.key, refused)
            return Touched()
        return Touched(before, _read(root, wanted))


def apply(root: Path, patch: str) -> str:
    """Apply ``patch`` to the tree at ``root``, as the benchmark applies its test patch.

    Returns:
        An empty string once it applied, or the tail of what `git apply` printed when it did
        not, which leaves the tree as it was.
    """
    with tempfile.TemporaryDirectory(prefix="benchproofer-patch-") as scratch:
        file = Path(scratch) / PATCH
        write_text(file, patch if patch.endswith("\n") else patch + "\n")
        # No further up than ``root``: a tree with no repository of its own must not have
        # the patch's paths resolved against a repository it happens to sit inside.
        applied = run(
            ("git", "apply", "--whitespace=nowarn", str(file)),
            cwd=root,
            env={"GIT_CEILING_DIRECTORIES": str(root.resolve().parent)},
            timeout_s=120,
        )
    return "" if applied.ok else applied.tail()


def _read(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    """The text of each of ``paths`` under ``root`` that is a file there."""
    return {
        path: (root / path).read_text(encoding="utf-8", errors="replace")
        for path in paths
        if (root / path).is_file()
    }


def _lay_out(task: Task, into: Path) -> None:
    """Write the files the task ships, and the patch beside them."""
    for source in task.context.files:
        write_text(into / source.path, source.content or "")
    write_text(into / PATCH, task.reference.patch or "")


def _rewind(task: Task, into: Path) -> None:
    """Reconcile an exported tree with what the task says a solver starts from."""
    restored: list[str] = []
    for source in task.context.files:
        target = into / source.path
        if source.content is None:
            continue
        if target.is_file() and target.read_text(encoding="utf-8", errors="replace") == (
            source.content
        ):
            continue
        write_text(target, source.content)
        restored.append(source.path)
    if restored:
        log.warning(
            "%s: the image's tree differs from the files the task ships, so %s "
            "%s restored from the task",
            task.key,
            len(restored),
            "was" if len(restored) == 1 else "were",
        )

    shipped = {source.path for source in task.context.files}
    created = [
        path
        for path in touched_paths(task.reference.patch or "")
        if path not in shipped and (into / path).is_file() and _adds(task, path)
    ]
    for path in created:
        (into / path).unlink()
    if created:
        log.warning(
            "%s: the image's tree holds %d file(s) the fix creates, so the image is not "
            "at the base commit; removed them",
            task.key,
            len(created),
        )
    write_text(into / PATCH, task.reference.patch or "")


def _adds(task: Task, path: str) -> bool:
    """Whether the reference patch creates ``path`` rather than editing it.

    Read off the patch's headers: a created file's `a/` side is `--- /dev/null`.
    """
    patch = task.reference.patch or ""
    marker = f"+++ b/{path}"
    at = patch.find(marker)
    if at < 0:
        return False
    head = patch[:at]
    return head.rstrip().endswith("--- /dev/null")
