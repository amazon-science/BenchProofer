# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Flavor dispatch: an unknown flavor is an error, never a default.

docs/adding_a_backend.md tells a backend author that introducing a new `flavor`
means adding a branch to each lexing-sensitive module, and that "every one of
those branches raises on an unknown flavor rather than silently defaulting, so
you will be told exactly which ones you owe". Two dispatch points did not keep
that promise, and each failed in a worse way than a missing feature:

* `variant_scope.unsound_evasions` fell off the end of its dispatch and returned
  `[]`. An empty problem list MEANS admissible, so a new backend was told that
  every same-spec rival of its bundles evades nothing -- by a screen that had not
  run a single rule. That is the shape of unsoundness the module exists to
  refuse, arriving with no error anywhere.
* `gates.hygiene.run` fell through to the Lean linter, so a new flavor was
  checked against Lean's comment syntax, Lean's divergence tokens and Lean's
  axiom screen, and the first sign of trouble was a KeyError out of
  `_REQUIRED_REGIONS` several frames later.

Each test below therefore comes in a pair: the raise, and the inertness of the
raise on the flavors that ship today (python/nagini, lean/velvet+lean, ears).
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from swebench_unified import variant_scope
from swebench_unified.backends import get_backend
from swebench_unified.backends.base import LanguageTables
from swebench_unified.gates import hygiene as g_hygiene

NAGINI = get_backend("nagini").language
LEAN = get_backend("lean").language
VELVET = get_backend("velvet").language
EARS = get_backend("ears").language

#: a flavor no module has a rule for — the new backend's first build
UNKNOWN = dataclasses.replace(LEAN, flavor="coq")

LEAN_SRC = """\
-- post-conditions-start
def problem_spec_count (r : Nat) (x : Nat) : Prop := r = x + 1
-- post-conditions-end
-- impl-start
def implementation_count (x : Nat) : Nat := x + 1
-- impl-end
-- proof-start
theorem correct_count (x : Nat) : problem_spec_count (implementation_count x) x := by
  rfl
-- proof-end
"""

MODEL_SRC = """\
def count_items(xs):
    # pre-conditions-start
    Requires(len(xs) >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() >= 0)
    # post-conditions-end
    # impl-start
    return len(xs)
    # impl-end
"""


# ---------------------------------------------------------------------------
# variant_scope
# ---------------------------------------------------------------------------

def test_unsound_evasions_raises_on_an_unknown_flavor():
    """The finding itself: `[]` here means ADMISSIBLE, so silence is a verdict."""
    with pytest.raises(ValueError) as e:
        variant_scope.unsound_evasions(LEAN_SRC, LEAN_SRC, UNKNOWN)
    msg = str(e.value)
    assert "coq" in msg                      # names the flavor
    assert "lean" in msg and "python" in msg  # and the ones that do have rules
    assert "ADMISSIBLE" in msg               # and what defaulting would have said


def test_variant_problems_raises_on_an_unknown_flavor():
    with pytest.raises(ValueError):
        variant_scope.variant_problems(LEAN_SRC, LEAN_SRC, UNKNOWN)


def test_the_declaration_scans_raise_on_an_unknown_flavor():
    """A new axiom must not be reported as no new axiom because the scan for the
    flavor's declaration syntax does not exist yet."""
    for fn in (variant_scope._decl_names, variant_scope._axiom_names):
        with pytest.raises(ValueError) as e:
            fn(LEAN_SRC, UNKNOWN)
        assert "coq" in str(e.value)


def test_declaration_free_flavors_still_answer_the_empty_set():
    """python and ears have no `axiom`/`theorem`/`lemma` form at all, so an empty
    set is the ANSWER there, not a missing branch: they must not start raising."""
    for tables in (NAGINI, EARS):
        assert variant_scope._decl_names(MODEL_SRC, tables) == set()
        assert variant_scope._axiom_names(MODEL_SRC, tables) == set()


@pytest.mark.parametrize("tables", [LEAN, VELVET, NAGINI, EARS],
                         ids=["lean", "velvet", "nagini", "ears"])
def test_every_shipped_flavor_still_accepts_its_own_source(tables):
    """Inertness: the frozen source is admissible against itself for every flavor
    that exists today, exactly as before the raise was added."""
    src = MODEL_SRC if tables.flavor != "lean" else LEAN_SRC
    assert variant_scope.unsound_evasions(src, src, tables) == []


def test_lean_evasions_are_still_caught():
    """The lean branch is untouched: dropping the obligation, adding an axiom and
    reaching for `sorry` all still report."""
    dropped = LEAN_SRC.replace("theorem correct_count", "theorem other_count")
    assert any("missing" in p for p in
               variant_scope.unsound_evasions(LEAN_SRC, dropped, LEAN))
    with_axiom = LEAN_SRC.replace("-- proof-start",
                                  "-- proof-start\naxiom cheat : True")
    assert any("new axiom" in p for p in
               variant_scope.unsound_evasions(LEAN_SRC, with_axiom, LEAN))
    with_sorry = LEAN_SRC.replace("  rfl", "  sorry")
    assert any("sorry" in p for p in
               variant_scope.unsound_evasions(LEAN_SRC, with_sorry, LEAN))


def test_python_contractonly_screen_is_still_reached():
    """The python branch is untouched, and it is the one that matters for nagini:
    an injected @ContractOnly stub is an assumed postcondition."""
    stubbed = MODEL_SRC.replace("def count_items(xs):",
                                "@ContractOnly\ndef count_items(xs):")
    problems = variant_scope.unsound_evasions(MODEL_SRC, stubbed, NAGINI)
    assert any("ContractOnly" in p for p in problems)


# ---------------------------------------------------------------------------
# G-HYGIENE
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _StubBackend:
    name: str
    language: LanguageTables


class _StubBundle:
    """Just what `hygiene.run` reads before it dispatches: no dataset row, no
    tmp bundle dir, so the test is about the dispatch and nothing else."""

    def __init__(self, backend: _StubBackend, src: str) -> None:
        self.backend = backend
        self._src = src
        self.solution = Path(backend.language.solution_filename)

    def solution_src(self) -> str:
        return self._src


@pytest.mark.parametrize("tables,expected", [(NAGINI, "python"), (EARS, "ears"),
                                             (LEAN, "lean"), (VELVET, "lean")],
                         ids=["nagini", "ears", "lean", "velvet"])
def test_each_shipped_flavor_reaches_its_own_linter(monkeypatch, tables, expected):
    """Inertness, checked at the dispatch rather than through a whole gate run."""
    seen = []
    for flavor in ("python", "ears"):
        monkeypatch.setattr(g_hygiene, f"_run_{flavor}",
                            lambda b, s, f=flavor: seen.append(f))
    monkeypatch.setattr(g_hygiene, "_run_lean",
                        lambda b, s, m: seen.append("lean"))
    g_hygiene.run(_StubBundle(_StubBackend("x", tables), "irrelevant"))
    assert seen == [expected]


def test_hygiene_raises_on_an_unknown_flavor(monkeypatch):
    """And does NOT quietly hand the source to the Lean linter, whose rules were
    written for a different language."""
    called = []
    monkeypatch.setattr(g_hygiene, "_run_lean",
                        lambda b, s, m: called.append("lean"))
    bundle = _StubBundle(_StubBackend("coqbackend", UNKNOWN), LEAN_SRC)
    with pytest.raises(ValueError) as e:
        g_hygiene.run(bundle)
    msg = str(e.value)
    assert "coq" in msg and "coqbackend" in msg
    assert "_run_coq" in msg and "_REQUIRED_REGIONS" in msg   # actionable
    assert called == []


def test_a_backend_with_no_required_regions_entry_is_a_named_error():
    """The KeyError at a distance the fall-through used to produce. A new
    lean-flavored backend is a legitimate thing to add; being told which table
    it is missing is the difference between a five-second fix and a traceback."""
    bundle = _StubBundle(_StubBackend("loom2", LEAN), LEAN_SRC)
    with pytest.raises(ValueError) as e:
        g_hygiene._run_lean(bundle, LEAN_SRC, "strict")
    msg = str(e.value)
    assert "loom2" in msg and "_REQUIRED_REGIONS" in msg
    assert "velvet" in msg and "lean" in msg     # lists the entries that exist


def test_the_required_regions_table_covers_every_lean_flavored_backend():
    """The guard above is a backstop, not a licence: every backend that ships
    today must already have its entry."""
    for backend_name in ("nagini", "velvet", "lean"):
        assert backend_name in g_hygiene._REQUIRED_REGIONS
