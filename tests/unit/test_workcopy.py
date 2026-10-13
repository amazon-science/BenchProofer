# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The task's code, on this machine, for a stage that decides by looking.

What is pinned down: a caller is told whether it has the repository or only the files a
task ships, and an export is reconciled with the task so that it never holds the fix.
No container is involved; the oracles stand in for one.
"""

from __future__ import annotations

from pathlib import Path

from benchproofer.core import material
from benchproofer.core.differential import invented
from benchproofer.core.task import Reference, SourceFile, Task
from benchproofer.core.workcopy import PATCH, Touched, apply, materialize, touched
from benchproofer.util.fsio import read_text, write_text
from benchproofer.util.proc import run

ADDS = """\
diff --git a/pkg/added.py b/pkg/added.py
new file mode 100644
--- /dev/null
+++ b/pkg/added.py
@@ -0,0 +1,2 @@
+def added():
+    return 1
diff --git a/pkg/edited.py b/pkg/edited.py
--- a/pkg/edited.py
+++ b/pkg/edited.py
@@ -1,2 +1,2 @@
-def edited():
-    return 1
+def edited():
+    return 2
"""


class Exporting:
    """An oracle whose environment can be copied out, with whatever tree a case wants."""

    def __init__(self, tree: dict[str, str]) -> None:
        self.tree = tree

    def export(self, task: Task, *, into: Path) -> Path:
        for path, content in self.tree.items():
            write_text(into / path, content)
        return into


class Envious:
    """An oracle with no environment to export, which is most of them."""

    def export(self, task: Task, *, into: Path) -> None:
        return None


def edited(task: Task, **fields: object) -> Task:
    """The task with its context and reference set for one of these cases."""
    return task.model_copy(update=fields)  # type: ignore[arg-type]


def repo_task(task: Task) -> Task:
    """A task whose fix edits one file and creates another."""
    return edited(
        task,
        context=task.context.model_copy(
            update={
                "files": (
                    SourceFile(path="pkg/edited.py", content="def edited():\n    return 1\n"),
                )
            }
        ),
        reference=Reference(patch=ADDS),
    )


def test_a_whole_repository_and_a_handful_of_files_are_not_reported_the_same(
    coin_change: Task, tmp_path: Path
) -> None:
    """Because finding no candidate means something in one case and nothing in the other."""
    whole = materialize(
        repo_task(coin_change),
        into=tmp_path / "whole",
        oracle=Exporting({"pkg/other.py": "x = 1\n"}),
    )
    partial = materialize(repo_task(coin_change), into=tmp_path / "partial", oracle=Envious())

    assert whole.whole and "base state" in whole.detail
    assert not partial.whole and "not available here" in partial.detail


def test_a_task_with_no_container_still_gets_the_files_it_ships(
    coin_change: Task, tmp_path: Path
) -> None:
    copy = materialize(repo_task(coin_change), into=tmp_path / "copy", oracle=Envious())

    assert (copy.root / "pkg/edited.py").read_text() == "def edited():\n    return 1\n"
    assert (copy.root / PATCH).read_text() == ADDS


def test_a_file_the_fix_creates_is_removed_from_an_export(
    coin_change: Task, tmp_path: Path
) -> None:
    """A leftover would be the answer to the task sitting in the tree."""
    exporting = Exporting(
        {
            "pkg/edited.py": "def edited():\n    return 2\n",
            "pkg/added.py": "def added():\n    return 1\n",
            "pkg/untouched.py": "y = 2\n",
        }
    )

    copy = materialize(repo_task(coin_change), into=tmp_path / "copy", oracle=exporting)

    assert not (copy.root / "pkg/added.py").exists()
    # Edited, not created: the task's own content wins, and the file stays.
    assert (copy.root / "pkg/edited.py").read_text() == "def edited():\n    return 1\n"
    # Nothing the fix touches: the image's tree is what a stage reads.
    assert (copy.root / "pkg/untouched.py").read_text() == "y = 2\n"


def test_a_stale_copy_of_another_task_cannot_be_read_as_this_one(
    coin_change: Task, tmp_path: Path
) -> None:
    into = tmp_path / "copy"
    write_text(into / "pkg" / "somebody_elses.py", "z = 3\n")

    copy = materialize(repo_task(coin_change), into=into, oracle=Envious())

    assert not (copy.root / "pkg/somebody_elses.py").exists()


def test_the_files_a_fix_touches_are_read_as_they_are_before_and_after_it(
    coin_change: Task, tmp_path: Path
) -> None:
    """Applied to a scratch copy: the working copy stays at the task's starting point."""
    task = repo_task(coin_change)
    copy = materialize(task, into=tmp_path / "copy", oracle=Envious())

    found = touched(task, copy, ADDS)

    assert found.before == {"pkg/edited.py": "def edited():\n    return 1\n"}
    assert found.after == {
        "pkg/added.py": "def added():\n    return 1\n",
        "pkg/edited.py": "def edited():\n    return 2\n",
    }
    assert (copy.root / "pkg/edited.py").read_text() == "def edited():\n    return 1\n"


def test_a_fix_that_does_not_apply_to_the_copy_gives_no_files(
    coin_change: Task, tmp_path: Path
) -> None:
    """The prompts then carry the patch alone."""
    task = edited(coin_change, reference=Reference(patch=ADDS))
    copy = materialize(task, into=tmp_path / "copy", oracle=Envious())

    assert not (copy.root / "pkg/edited.py").exists()
    assert touched(task, copy, ADDS) == Touched()


def test_a_patch_is_applied_to_a_tree_inside_another_repository_as_to_its_own(
    tmp_path: Path,
) -> None:
    """A drafting session's copy of the repository sits wherever its cache is.

    Its paths are the copy's own, not those of a repository the copy happens to sit inside,
    and a patch that does not apply says why and leaves the tree as it was.
    """
    assert run(("git", "init", "-q"), cwd=tmp_path).ok
    tree = tmp_path / "cache" / "repository"
    write_text(tree / "pkg" / "edited.py", "def edited():\n    return 1\n")

    assert apply(tree, ADDS) == ""
    assert read_text(tree / "pkg" / "added.py") == "def added():\n    return 1\n"
    assert "return 2" in read_text(tree / "pkg" / "edited.py")
    assert not (tmp_path / "pkg").exists()
    assert apply(tree, ADDS)
    assert read_text(tree / "pkg" / "edited.py") == "def edited():\n    return 2\n"


def test_a_whole_copy_laid_out_for_the_same_task_is_reused(
    coin_change: Task, tmp_path: Path
) -> None:
    """An export is a repository copied out of an image, which a repair would repeat."""
    task = repo_task(coin_change)
    materialize(task, into=tmp_path / "copy", oracle=Exporting({"pkg/other.py": "x = 1\n"}))
    write_text(tmp_path / "copy" / "pkg/marker.py", "kept\n")

    again = materialize(task, into=tmp_path / "copy", oracle=Envious())

    assert again.whole and (again.root / "pkg/marker.py").is_file()
    other = edited(task, reference=Reference(patch=ADDS.replace("return 2", "return 3")))
    fresh = materialize(other, into=tmp_path / "copy", oracle=Envious())
    assert not fresh.whole and not (fresh.root / "pkg/marker.py").exists()


#: A module the fix edits, with a class the fix does not mention and a method it does.
CLIENT = """\
import os


class Helper:
    pass


class Client:
    def run(self, name="postgres"):
        if not name:
            return None
        return name.upper()

    def other(self):
        return 1
"""
EDITS_RUN = """\
diff --git a/pkg/client.py b/pkg/client.py
--- a/pkg/client.py
+++ b/pkg/client.py
@@ -10,3 +10,3 @@ class Client:
         if not name:
             return None
-        return name
+        return name.upper()
"""


def test_the_prompt_is_shown_each_function_the_fix_edits_in_full(coin_change: Task) -> None:
    """The default argument above the hunk is what a model of it gets wrong otherwise."""
    task = edited(coin_change, reference=Reference(patch=EDITS_RUN))
    before = CLIENT.replace("return name.upper()", "return name")

    block = material.code_block(
        task, Touched(before={"pkg/client.py": before}, after={"pkg/client.py": CLIENT})
    )

    assert "### `pkg/client.py`: `Client.run`, before the fix, lines 9-12" in block, block
    assert "### `pkg/client.py`: `Client.run`, after the fix, lines 9-12" in block
    assert block.count('def run(self, name="postgres"):') == 2
    assert "def other" not in block and "class Helper" not in block
    assert block.index("        return name\n") < block.index("return name.upper()")


def test_the_code_the_fix_edits_is_shown_before_a_document_it_touches(
    coin_change: Task,
) -> None:
    """A long document shown first would take the room the edited functions need."""
    document = (
        "diff --git a/doc/settings.adoc b/doc/settings.adoc\n"
        "--- a/doc/settings.adoc\n+++ b/doc/settings.adoc\n"
        "@@ -1 +1 @@\n-old\n+" + "x" * (material.REFERENCE_LIMIT * 2) + "\n"
    )
    task = edited(coin_change, reference=Reference(patch=document + EDITS_RUN))

    block = material.reference_block(task)

    assert "+        return name.upper()" in block
    assert block.index("pkg/client.py") < block.index("doc/settings.adoc")
    assert block.count("```") % 2 == 0


def test_an_import_is_judged_against_the_repository_where_there_is_one(tmp_path: Path) -> None:
    """A real class the task never mentions is not invented; a module that is not there is."""
    write_text(tmp_path / "pkg/__init__.py", "")
    write_text(tmp_path / "pkg/client.py", CLIENT)
    write_text(tmp_path / "pkg/sub/__init__.py", "")
    harness = (
        "from pkg.client import Client, Helper\n"
        "from pkg import sub\n"
        "from pkg.clients import Client\n"
        "from pkg.client import Missing\n"
        "from random import randint\n"
    )

    found = invented(harness, EDITS_RUN, tree=tmp_path)

    assert found == ("pkg.clients", "pkg.client.Missing")
    # Without the tree, the class the patch never names is what gets reported.
    assert "pkg.client.Helper" in invented(harness, EDITS_RUN)


def test_a_name_a_package_star_imports_is_defined_where_the_import_points(
    tmp_path: Path,
) -> None:
    """A package that re-exports with `import *` never writes the names it carries.

    They are looked for through its star imports, and theirs; one out of a module the tree
    has no file for could bring in anything, so a name it may carry is not reported.
    """
    write_text(tmp_path / "pkg/__init__.py", "from .core import *\nfrom .extra import *\n")
    write_text(tmp_path / "pkg/core/__init__.py", "from .numbers import *\n")
    write_text(tmp_path / "pkg/core/numbers.py", "class Rational:\n    pass\n")
    write_text(tmp_path / "pkg/extra.py", "def helper():\n    return 1\n")
    write_text(tmp_path / "loose/__init__.py", "from numpy import *\n")
    harness = (
        "from pkg import Rational\n"
        "from pkg import helper\n"
        "from pkg import Missing\n"
        "from loose import array\n"
    )

    assert invented(harness, EDITS_RUN, tree=tmp_path) == ("pkg.Missing",)
