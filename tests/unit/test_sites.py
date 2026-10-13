# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Which of the repository's functions the task's fix changes.

The drafting prompts list them. Each changed line is placed in the definition around it in
the file's own source, the file before the fix for a line the fix removes and the file
after it for a line it adds, whatever definition `git` writes beside the hunk. That reading
is made once, at drafting, and recorded; a bundle without the record reads the diff alone.
"""

from __future__ import annotations

from benchproofer.core.differential import ungrounded
from benchproofer.core.sites import (
    LISTED,
    changed,
    listed,
    others,
    readers,
    record,
    sites,
)
from benchproofer.core.task import Reference, Task
from benchproofer.core.workcopy import Touched
from benchproofer.util.patch import (
    Edited,
    edited_definitions,
    edited_symbols,
    header_definitions,
)
from doubles import revised


def names(task: Task, edited: Edited) -> tuple[str, ...]:
    """Every name `sites` gives, whichever file it is in, sorted."""
    return tuple(sorted({name for found in sites(task, edited).values() for name in found}))


def patched(task: Task, patch: str, symbols: tuple[str, ...] = ()) -> Task:
    return task.model_copy(update={"reference": Reference(patch=patch, symbols=symbols)})


def test_the_sites_are_what_the_fix_defines_and_what_the_benchmark_lists(
    coin_change: Task,
) -> None:
    patch, fix = revised(
        "bandit/core/cache_manager.py",
        "import os\n",
        "import os\n\n\nclass CacheManager:\n\n"
        "    def get_cached_results(self, file_path, cache_key):\n        return None\n",
    )

    found = sites(patched(coin_change, patch, ("listed_by_the_benchmark",)), fix)

    # A method is named under its class, so two of one name in a file are told apart.
    assert found == {
        "bandit/core/cache_manager.py": ("CacheManager", "CacheManager.get_cached_results"),
        "": ("listed_by_the_benchmark",),
    }
    assert listed(found) == (
        "* in `bandit/core/cache_manager.py`: `CacheManager`, "
        "`CacheManager.get_cached_results`\n"
        "* named by the benchmark: `listed_by_the_benchmark`"
    )


def test_a_task_whose_fix_names_nothing_asks_nothing(coin_change: Task) -> None:
    """There is no list to point into."""
    bare = coin_change.model_copy(update={"reference": Reference(answer="42")})

    assert names(bare, {}) == ()


def test_a_file_the_fix_writes_that_is_not_python_is_named_beside_the_python_names(
    coin_change: Task,
) -> None:
    """A behavior a test checks can be in a script the test runs in a browser engine.

    The test is a FAIL_TO_PASS test or a PASS_TO_PASS test the test patch adds or edits.
    """
    script, _ = revised("browser/quirks/array_at.user.js", "", "Array.prototype.at = f;\n")
    notes, _ = revised("doc/changelog.md", "", "* at()\n")
    code, fix = revised("browser/quirks.py", "QUIRKS = []\n", "QUIRKS = ['array_at']\n")
    task = patched(coin_change, script + notes + code)

    assert others(task) == ("browser/quirks/array_at.user.js",)
    assert names(task, fix) == ("QUIRKS",)


def test_a_long_list_is_clipped_and_says_so() -> None:
    many = {
        "a.py": tuple(f"f{index}" for index in range(LISTED - 2)),
        "b.py": tuple(f"g{index}" for index in range(7)),
    }

    shown = listed(many)

    assert shown.count("`f") + shown.count("`g") == LISTED
    assert "5 more; the golden patch names them all" in shown


def test_a_method_reported_by_its_class_path_is_grounded_in_the_module_it_came_from() -> None:
    """`conformance.py` imports the class out of the module, never writing the class's path."""
    harness = "from bandit.core.cache_manager import CacheManager\n"
    report = (
        "benchproofer:compared bandit.core.cache_manager.CacheManager.get_cached_results 10 x\n"
    )

    assert ungrounded(report, harness) == ()
    assert ungrounded(report, "from bandit.core.cache_manager import CacheKey\n") == (
        "bandit.core.cache_manager.CacheManager.get_cached_results",
    )


#: A function with a helper nested near its top, and the line the fix changes further
#: down, past the helper's end. `git` writes the helper beside the hunk, as the nearest
#: definition above it.
SYMBOLS = """\
def symbols(names, *, cls=None, **args):
    result = []

    def literal(s):
        if s.startswith('!'):
            return s[1:]
        return s

    for name in names.split(','):
        name = literal(name.strip())
        if name:
            result.append(symbols(name, **args))
    return result
"""


def test_a_change_below_a_nested_helper_is_in_the_function_around_it(
    coin_change: Task,
) -> None:
    """The helper ends above the changed line, so what the fix edits is the outer function."""
    patch, fix = revised(
        "pkg/symbol.py",
        SYMBOLS,
        SYMBOLS.replace("symbols(name, **args)", "symbols(name, cls=cls, **args)"),
        header="def literal(s):",
    )

    assert names(patched(coin_change, patch), fix) == ("symbols",)


#: A class whose method the fix edits below the method's own `def`.
AUTODETECTOR = """\
class MigrationAutodetector:
    def generate_renamed_fields(self):
        for app_label, model_name in self.models:
            old_model_name = self.renamed.get(model_name, model_name)
            old_state = self.from_state[app_label, old_model_name]
            new_state = self.to_state[app_label, old_model_name]
            yield old_state, new_state

    def generate_added_fields(self):
        return []
"""


def test_a_change_under_a_hunk_header_naming_its_class_is_in_the_method() -> None:
    """Qualified, the method is named under the class the file defines it in."""
    _, fix = revised(
        "pkg/autodetector.py",
        AUTODETECTOR,
        AUTODETECTOR.replace(
            "to_state[app_label, old_model_name]", "to_state[app_label, model_name]"
        ),
        header="class MigrationAutodetector:",
    )

    assert edited_symbols(fix) == ("generate_renamed_fields",)
    assert edited_symbols(fix, qualified=True) == (
        "MigrationAutodetector.generate_renamed_fields",
    )


def test_a_function_the_fix_adds_is_a_site_and_the_one_above_it_is_not(
    coin_change: Task,
) -> None:
    """`git` names the definition nearest above the hunk; this fix only calls it."""
    before = "def infer_chromium_version(raw):\n    return TABLE.get(raw)\n"
    patch, fix = revised(
        "pkg/versions.py",
        before,
        before
        + "\n\ndef from_importlib(raw):\n    return Versions(infer_chromium_version(raw))\n",
        header="def infer_chromium_version(raw):",
    )

    assert names(patched(coin_change, patch), fix) == ("from_importlib",)


def test_a_function_the_fix_deletes_is_not_a_site(coin_change: Task) -> None:
    """The fixed code has no such function for a `conformance.py` to reach."""
    patch, fix = revised(
        "pkg/paths.py",
        "def resolve(path):\n    return path\n\n\n"
        "def unique_path(path):\n    return normcase(path)\n\n\n"
        "def import_module(path):\n    key = unique_path(path)\n    return key\n",
        "def resolve(path):\n    return path\n\n\n"
        "def import_module(path):\n    key = path\n    return key\n",
        header="def resolve(path):",
    )

    assert names(patched(coin_change, patch), fix) == ("import_module",)


def test_a_method_the_fix_renames_is_named_as_the_fix_leaves_it(coin_change: Task) -> None:
    """The method above it is untouched, and a decorator is part of what it decorates."""
    patch, fix = revised(
        "pkg/versions.py",
        "class Versions:\n"
        "    @classmethod\n    def infer(cls, raw):\n        return cls._TABLE.get(raw)\n\n"
        "    @classmethod\n    def from_raw(\n            cls,\n            raw,\n"
        '    ) -> "Versions":\n        return cls(raw)\n',
        "class Versions:\n"
        "    @classmethod\n    def infer(cls, raw):\n        return cls._TABLE.get(raw)\n\n"
        '    @classmethod\n    def from_text(cls, raw) -> "Versions":\n'
        "        return cls(raw)\n\n"
        "    @staticmethod\n    def suffixes():\n        return set()\n",
        header="def infer(cls, raw):",
    )

    assert names(patched(coin_change, patch), fix) == (
        "Versions.from_text",
        "Versions.suffixes",
    )


def test_a_decorator_the_fix_adds_edits_the_function_it_decorates(coin_change: Task) -> None:
    """It opens above the `def`, and it still wraps what the function does."""
    patch, fix = revised(
        "pkg/filters.py",
        "def to_yaml(data):\n    return dump(data)\n",
        "@accept_lazy_markers\ndef to_yaml(data):\n    return dump(data)\n",
    )

    assert names(patched(coin_change, patch), fix) == ("to_yaml",)


#: A table at module level: one entry renamed inside the literal, and one added by a
#: statement at the left margin. The hunk header names a method above the table.
EDITS_A_TABLE = """\
--- a/pkg/darkmode.py
+++ b/pkg/darkmode.py
@@ -240,8 +240,8 @@ def copy_add_setting(self, setting):
 _DEFINITIONS = {
     Variant.old: _Definition(
         _Setting('grayscale.all', 'Grayscale'),
-        _Setting('threshold.text', 'TextBrightnessThreshold'),
+        _Setting('threshold.foreground', 'TextBrightnessThreshold'),
     ),
 }
@@ -300,3 +300,6 @@ def copy_add_setting(self, setting):
 _SETTINGS = ['a']
+_DEFINITIONS[Variant.new] = _DEFINITIONS[Variant.old].copy_replace_setting(
+    'threshold.foreground', 'ForegroundBrightnessThreshold',
+)
"""


def test_a_table_the_fix_edits_or_adds_an_entry_to_is_a_site(coin_change: Task) -> None:
    """Whether the entry is edited inside the literal or added by a statement of its own."""
    found = names(patched(coin_change, EDITS_A_TABLE), {})

    assert "_DEFINITIONS" in found
    assert "_SETTINGS" not in found


def test_a_binding_the_fix_removes_is_not_a_site(coin_change: Task) -> None:
    removed = """\
--- a/pkg/cfg.py
+++ b/pkg/cfg.py
@@ -1,4 +1,2 @@
-LEGACY = {
-    'a': 1,
-}
 CURRENT = 2
"""
    assert names(patched(coin_change, removed), {}) == ()


def test_a_comparison_or_a_call_at_the_left_margin_binds_nothing(coin_change: Task) -> None:
    calls = """\
--- a/pkg/cli.py
+++ b/pkg/cli.py
@@ -1,2 +1,4 @@
 import sys
+register(name='x')
+assert LIMIT == 3
+if LIMIT >= 2: pass
"""
    assert names(patched(coin_change, calls), {}) == ()


#: A class attribute the fix adds, in a hunk whose header names the class, and a local
#: variable it adds inside a method.
ADDS_AN_ATTRIBUTE = """\
--- a/pkg/validators.py
+++ b/pkg/validators.py
@@ -92,6 +92,7 @@ class URLValidator(RegexValidator):
     message = 'Enter a valid URL.'
     schemes = ['http', 'https']
+    unsafe_chars = frozenset('\\t\\r\\n')

     def __init__(self, schemes=None, **kwargs):
         super().__init__(**kwargs)
+        local = 1
"""


def test_a_class_attribute_the_fix_adds_is_a_site_and_a_local_is_not(
    coin_change: Task,
) -> None:
    found = names(patched(coin_change, ADDS_AN_ATTRIBUTE), {})

    assert "unsafe_chars" in found
    assert "local" not in found and "schemes" not in found


#: A class whose `__call__` the fix edits, in a hunk whose header names `__init__`.
VALIDATOR = """\
class UrlCheck(PatternCheck):
    message = 'bad'

    def __init__(self, schemes=None):
        super().__init__()

    def __call__(self, value):
        if not isinstance(value, str):
            raise TypeError(value)
        scheme = value.split(':')[0]
        return scheme
"""


def test_a_method_is_qualified_by_its_class_and_the_class_is_not_named_for_it() -> None:
    """The method is how the class's code is reached, and constructing it runs other code."""
    _, fix = revised(
        "pkg/validators.py",
        VALIDATOR,
        VALIDATOR.replace(
            "        scheme =",
            "        if self.unsafe.intersection(value):\n            raise ValueError(value)\n"
            "        scheme =",
        ),
        header="def __init__(self, schemes=None):",
    )

    assert edited_symbols(fix) == ("__call__",)
    assert edited_symbols(fix, qualified=True) == ("UrlCheck.__call__",)
    assert edited_symbols(fix, enclosing=True) == ("__call__",)


#: A function with a helper nested in it, whose body the fix edits.
NUMERIC = """\
def ensure_numeric(data):
    from .dataset import Dataset

    def to_floatable(x):
        if x.kind in "mM":
            return x.copy()
        return x

    return to_floatable(data)
"""


def test_a_function_around_a_nested_one_the_fix_edits_is_a_site(coin_change: Task) -> None:
    """The nested one is reached only through it, so `conformance.py` compares nothing else."""
    patch, fix = revised(
        "pkg/computation.py",
        NUMERIC,
        NUMERIC.replace('x.kind in "mM"', 'x.kind == "M"'),
        header="def ensure_numeric(data):",
    )

    assert names(patched(coin_change, patch), fix) == ("ensure_numeric", "to_floatable")
    # Asked for what it edits alone, the patch names the nested function only.
    assert edited_symbols(fix) == ("to_floatable",)


def test_a_file_that_is_not_python_is_missing_or_does_not_parse_names_nothing() -> None:
    """There is no source to place a changed line in."""
    _, unparsed = revised("pkg/broken.py", "def f(:\n    return 1\n", "def f(:\n    return 2\n")
    _, prose = revised("docs/notes.txt", "def f():\n    return 1\n", "def f():\n    return 2\n")
    numeric, _ = revised("pkg/computation.py", NUMERIC, NUMERIC.replace("mM", "M"))

    assert edited_symbols(unparsed) == ()
    assert edited_symbols(prose) == ()
    assert edited_definitions(numeric, {}, {}) == {}


#: A fix that edits only a module-level pattern, which a function further down reads.
EDITS_A_PATTERN = """\
diff --git a/pkg/trans.py b/pkg/trans.py
--- a/pkg/trans.py
+++ b/pkg/trans.py
@@ -3,3 +3,3 @@ import re

-prefix_re = re.compile(r'^/(\\w+([@-]\\w+)?)(/|$)')
+prefix_re = re.compile(r'^/(\\w+([@-]\\w+){0,2})(/|$)')

"""
#: The file that fix leaves: one reader of the pattern, one reader through a nested
#: function, one function that only binds a local of that name, and a class attribute
#: spelled the same.
TRANS_FIXED = """\
import re

prefix_re = re.compile(r'^/(\\w+([@-]\\w+){0,2})(/|$)')


def language_from_path(path):
    found = prefix_re.match(path)
    return found[1] if found else None


def variants(path):
    def first(text):
        return prefix_re.match(text)
    return first(path)


def unrelated(path):
    prefix_re = 3
    return 'en'


class Settings:
    prefix_re = None

    def default(self):
        return self.prefix_re
"""


def test_a_function_that_reads_a_module_level_name_the_fix_edits_is_one_of_its_readers(
    coin_change: Task,
) -> None:
    """A load counts, even from a nested function; a same-named local or attribute does not."""
    assert names(patched(coin_change, EDITS_A_PATTERN), {}) == ("prefix_re",)
    assert readers(EDITS_A_PATTERN, {"pkg/trans.py": TRANS_FIXED}) == {
        "pkg/trans.py": ("first", "language_from_path", "variants")
    }


def test_a_fixed_file_that_is_missing_or_does_not_parse_names_no_reader() -> None:
    assert readers(EDITS_A_PATTERN, {}) == {}
    assert readers(EDITS_A_PATTERN, {"pkg/trans.py": "def broken(:\n"}) == {}
    assert readers(EDITS_A_PATTERN, {"pkg/other.py": TRANS_FIXED}) == {}


def test_a_function_the_fix_touches_only_in_its_layout_comments_or_docstring_is_no_site(
    coin_change: Task,
) -> None:
    """Nothing it computes changed, so it is not a function the fix changes."""
    patch, fix = revised(
        "m.py",
        "def changed(x):\n    return x\n\n\n"
        "def touched(x):\n    '''\n    Old words.\n    '''\n"
        "    y = x   \n    return y  # old\n\n\n"
        "def described(x):\n    'Old.'\n    return x\n",
        "def changed(x):\n    return x + 1\n\n\n"
        "def touched(x):\n    '''\n    New words.\n    '''\n    # why\n    y = x\n"
        "    return y  # new\n\n\n"
        "def described(x):\n    'New.'\n    return x\n",
    )

    assert edited_symbols(fix) == ("changed",)
    assert names(patched(coin_change, patch), fix) == ("changed",)


def test_a_line_moved_into_or_out_of_a_block_changes_code() -> None:
    """Indentation is code in Python, and so is the spacing inside a string."""
    _, out_of_block = revised(
        "m.py",
        "def f(x):\n    if x:\n        y = 1\n        return y\n",
        "def f(x):\n    if x:\n        y = 1\n    return y\n",
    )
    _, respaced = revised(
        "m.py", "def f(x):\n    return 'a  b'\n", "def f(x):\n    return 'a b'\n"
    )

    assert edited_symbols(out_of_block) == ("f",)
    assert edited_symbols(respaced) == ("f",)


def test_drafting_records_what_the_patches_edit_and_every_later_stage_reads_it_back(
    coin_change: Task,
) -> None:
    """The record is the reading of the files, kept in `manifest.json` as JSON and read back."""
    fixed = SYMBOLS.replace("symbols(name, **args)", "symbols(name, cls=cls, **args)")
    patch, fix = revised("pkg/symbol.py", SYMBOLS, fixed, header="def literal(s):")
    test = "def test_cls():\n    assert symbols('x', cls=int)\n"
    tests, _ = revised("tests/test_symbol.py", "", test)
    task = patched(coin_change, patch).model_copy(update={"metadata": {"test_patch": tests}})
    files = Touched(before={"pkg/symbol.py": SYMBOLS}, after={"pkg/symbol.py": fixed})

    kept = record(task, files, Touched(after={"tests/test_symbol.py": test}))

    assert kept["golden_patch"] == {"pkg/symbol.py": [["def symbols"]]}
    assert changed(task, kept).golden == fix
    assert changed(task, kept).tests == {"tests/test_symbol.py": ((("test_cls", False),),)}


def test_without_a_record_the_names_are_read_off_the_diff(coin_change: Task) -> None:
    """The hunk header's name is `git`'s guess, here the helper above the changed line."""
    fixed = SYMBOLS.replace("symbols(name, **args)", "symbols(name, cls=cls, **args)")
    patch, _ = revised("pkg/symbol.py", SYMBOLS, fixed, header="def literal(s):")
    task = patched(coin_change, patch)

    assert changed(task, None).golden == header_definitions(patch)
    assert names(task, changed(task, None).golden) == ("literal",)
    # A patch whose files drafting could not read is recorded as None, and read the same way.
    unread = record(task, Touched(), Touched())
    assert unread["golden_patch"] is None
    assert changed(task, unread).golden == header_definitions(patch)


def test_off_the_diff_a_name_on_a_changed_line_counts_and_a_header_names_no_class() -> None:
    """Deleted and added definitions alike, in Python files only."""
    patch = (
        "diff --git a/pkg/a.py b/pkg/a.py\n--- a/pkg/a.py\n+++ b/pkg/a.py\n"
        "@@ -1,4 +1,4 @@ class Versions:\n"
        "-    def from_raw(cls, raw):\n+    def from_text(cls, raw):\n"
        "         return cls(raw)\n"
        "diff --git a/docs/notes.txt b/docs/notes.txt\n--- a/docs/notes.txt\n"
        "+++ b/docs/notes.txt\n@@ -1 +1 @@ def documented():\n-old\n+def new(): words\n"
    )

    read = header_definitions(patch)

    assert read == {
        "pkg/a.py": (
            (("Versions", True),),
            (("from_raw", False),),
            (("from_text", False),),
        )
    }
    assert edited_symbols(read, qualified=True, enclosing=True) == (
        "Versions",
        "from_raw",
        "from_text",
    )
