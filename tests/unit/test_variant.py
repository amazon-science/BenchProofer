# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Whether a variant of a solution is admissible evidence about its specification.

A variant that reaches for an escape hatch is accepted or refused for reasons unrelated
to the specification, so the screen is tested both ways: the honest variant is admissible
and one differing only by the hatch is not. The rest covers what a variant may write --
the regions it owns, the claim it restates, what is carried from a reply -- and when two
files compute the same thing.
"""

from __future__ import annotations

import ast

import pytest

from benchproofer.backends.base import Backend
from benchproofer.core import markers, variant
from benchproofer.core.variant import assemble, owned, probe_rule, rule, scope
from benchproofer.errors import BenchproofError
from benchproofer.registries import BACKENDS

COMMENT = "#"

#: A Lean file, for a backend whose escape hatch is a proof term rather than a statement.
LEAN = """\
-- benchproofer:begin spec
theorem spec (n : Nat) : impl n = n := by
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) : Nat := n
-- benchproofer:end impl

-- benchproofer:begin proof
  rfl
-- benchproofer:end proof
"""


@pytest.fixture
def falsifier() -> Backend:
    return BACKENDS.get("falsifier")


@pytest.fixture
def lean() -> Backend:
    return BACKENDS.get("lean4")


def swapped(source: str, body: str, region: str = "impl") -> str:
    """One region of a solution file replaced, as every variant is produced."""
    return markers.replace_region(source, COMMENT, region, body)


def test_a_differently_written_implementation_is_admissible(
    solution: str, falsifier: Backend
) -> None:
    """A rival computing the answer another way, under a checker with no claim to restate."""
    rival = swapped(solution, "def impl(cents):\n    return (0, 0, 0, cents)")

    verdict = scope(solution, rival, falsifier)

    assert verdict
    assert verdict.admissible
    assert verdict.reason == ""


def test_an_implementation_that_stops_the_search_is_not_admissible(
    solution: str, falsifier: Backend
) -> None:
    """`assume(False` makes every property hold, which is not the spec's doing."""
    rigged = swapped(
        solution,
        "def impl(cents):\n    assume(False)\n    return (0, 0, 0, 0)",
    )

    verdict = scope(solution, rigged, falsifier)

    assert not verdict
    assert "'assume(False'" in verdict.reason


def test_a_directive_that_turns_the_checker_off_is_not_admissible() -> None:
    """The escape hatch that a comment mask would have hidden."""
    backend = BACKENDS.get("crosshair")
    source = (
        "# benchproofer:begin spec\n"
        "def spec(x: int) -> None:\n"
        "    assert impl(x) == x\n"
        "# benchproofer:end spec\n"
        "\n"
        "# benchproofer:begin impl\n"
        "def impl(x: int) -> int:\n"
        "    return x\n"
        "# benchproofer:end impl\n"
    )
    rigged = swapped(source, "def impl(x: int) -> int:\n    # crosshair: off\n    return 0")

    assert scope(source, source, backend)
    assert not scope(source, rigged, backend)
    assert "'# crosshair: off'" in scope(source, rigged, backend).reason


def test_a_hatch_named_in_a_docstring_is_not_reached_for_where_strings_are_inert(
    solution: str, falsifier: Backend
) -> None:
    """A docstring naming a hatch is prose, except under CrossHair, whose contracts it is."""
    documented = (
        "def impl(cents):\n"
        '    """post: sys.exit(0) is never called, nor assume(False."""\n'
        "    return (0, 0, 0, cents)"
    )

    assert scope(solution, swapped(solution, documented), falsifier)
    verdict = scope(solution, swapped(solution, documented), BACKENDS.get("crosshair"))
    assert not verdict
    assert "'sys.exit'" in verdict.reason


def test_the_proof_region_is_screened_as_well_as_the_implementation(lean: Backend) -> None:
    """A proof that says `sorry` establishes nothing, whatever the impl says."""
    rigged = LEAN.replace("  rfl", "  sorry")

    assert scope(LEAN, LEAN, lean)
    verdict = scope(LEAN, rigged, lean)
    assert not verdict
    assert "'sorry'" in verdict.reason


def test_the_specification_region_is_not_screened_here(
    solution: str, falsifier: Backend
) -> None:
    """Drift in the spec is the spec view's finding, which the caller reports."""
    drifted = swapped(solution, "assume(False)", "spec")

    assert scope(solution, drifted, falsifier)
    assert not falsifier.same_spec(solution, drifted)


def test_a_hatch_the_accepted_file_already_has_is_not_introduced(falsifier: Backend) -> None:
    """The scope is the solution file's own; `spec.hygiene` judges the file itself."""
    accepted = (
        "# benchproofer:begin spec\n"
        "def property_trivial():\n"
        "    assert True\n"
        "# benchproofer:end spec\n"
        "\n"
        "# benchproofer:begin impl\n"
        "def impl(x):\n"
        "    sys.exit(0)\n"
        "# benchproofer:end impl\n"
    )
    variant = swapped(accepted, "def impl(x):\n    sys.exit(1)")

    assert scope(accepted, variant, falsifier)


def test_a_variant_with_no_readable_regions_is_not_admissible(
    solution: str, falsifier: Backend
) -> None:
    """An unreadable variant decides nothing, so it must not read as one about the spec."""
    verdict = scope(solution, "def impl(cents):\n    return ()\n", falsifier)

    assert not verdict
    assert "marker regions cannot be read" in verdict.reason


def test_a_backend_that_bans_nothing_admits_everything(solution: str) -> None:
    """The screen is defined by the backend's own list, not by a hardcoded one."""

    class Permissive(Backend):
        name = "permissive"
        language = "Python"
        extension = ".py"
        comment = "#"

        def check(self, source, *, workdir, timeout_s=120.0):  # type: ignore[no-untyped-def]
            raise NotImplementedError

    rigged = swapped(solution, "def impl(cents):\n    assume(False)\n    return ()")

    assert scope(solution, rigged, Permissive())


# ---- the regions a variant owns -----------------------------------------


def test_a_variant_of_a_proof_carrying_file_owns_the_proof_too(lean: Backend) -> None:
    """The shipped proof was written for the shipped implementation, not for a variant."""
    assert owned(lean.template(), lean) == ("impl", "proof")


def test_a_variant_of_a_file_with_no_proof_region_owns_the_implementation(
    solution: str, falsifier: Backend
) -> None:
    assert owned(solution, falsifier) == ("impl",)


def test_the_rule_a_variant_is_given_names_the_regions_it_owns() -> None:
    """Every prompt that asks for a variant renders this one wording."""
    one = rule(("impl",))
    both = rule(("impl", "proof"))

    assert "`impl` region" in one
    assert "proof" not in one.replace("Benchproofer", "")
    assert "`impl` and `proof` regions" in both
    assert "The proof is yours" in both
    assert "word for word" in both


# ---- assembling one out of a reply --------------------------------------


#: The two regions of a Lean reply, doubling by addition.
DOUBLED_IMPL = (
    "-- benchproofer:begin impl\ndef impl (n : Nat) : Nat :=\n  n + n\n-- benchproofer:end impl"
)
DOUBLED_PROOF = (
    "-- benchproofer:begin proof\ntheorem impl_meets_spec (n : Nat) : Spec n (impl n) := by\n"
    "  unfold Spec impl\n  rfl\n-- benchproofer:end proof"
)


@pytest.mark.parametrize(
    "reply",
    [
        f"CLAIM: doubled by addition.\n\n```lean\n{DOUBLED_IMPL}\n\n{DOUBLED_PROOF}\n```\n",
        f"```lean\n{DOUBLED_IMPL}\n```\n\nand its proof:\n\n```lean\n{DOUBLED_PROOF}\n```\n",
    ],
    ids=["one block", "a block per region"],
)
def test_a_reply_that_marks_the_regions_it_wrote_is_spliced_into_the_accepted_file(
    reply: str, lean: Backend
) -> None:
    """Every block that carries sentinels is part of the answer, not only the last."""
    accepted = lean.template()

    source = assemble(accepted, reply, lean, allowed=owned(accepted, lean))
    regions = markers.parse(source, lean.comment)

    assert regions["impl"].text == "def impl (n : Nat) : Nat :=\n  n + n"
    assert regions["proof"].text.endswith("rfl")
    assert lean.same_spec(accepted, source)


def test_a_block_that_writes_a_region_again_replaces_the_earlier_one(lean: Backend) -> None:
    """A reply that corrects itself is read by what it wrote last."""
    accepted = lean.template()
    first = (
        "-- benchproofer:begin impl\ndef impl (n : Nat) : Nat :=\n  n\n-- benchproofer:end impl"
    )
    again = first.replace("  n\n", "  n + n\n")
    reply = f"```lean\n{first}\n```\n\nCorrected:\n\n```lean\n{again}\n```\n"

    source = assemble(accepted, reply, lean, allowed=("impl",))

    assert markers.parse(source, lean.comment)["impl"].text.endswith("n + n")


def test_a_region_it_was_not_offered_quoted_unchanged_is_left_alone(lean: Backend) -> None:
    """Writing the specification out as it stands is a quotation, not a rewrite of it."""
    accepted = lean.template()
    spec = markers.parse(accepted, lean.comment)["spec"].text
    reply = (
        f"```lean\n-- benchproofer:begin spec\n{spec}\n-- benchproofer:end spec\n```\n\n"
        "```lean\n-- benchproofer:begin impl\ndef impl (n : Nat) : Nat :=\n  n + n\n"
        "-- benchproofer:end impl\n```\n"
    )

    source = assemble(accepted, reply, lean, allowed=("impl", "proof"))

    assert markers.parse(source, lean.comment)["impl"].text.endswith("n + n")
    assert lean.same_spec(accepted, source)


def test_a_reply_that_owns_one_region_need_not_mark_it(
    solution: str, falsifier: Backend
) -> None:
    """There is nothing a single region could be confused with."""
    reply = (
        "CLAIM: pennies only.\n\n```python\ndef impl(cents):\n    return (0, 0, 0, cents)\n```"
    )

    source = assemble(solution, reply, falsifier, allowed=("impl",))

    assert (
        markers.parse(source, COMMENT)["impl"].text
        == "def impl(cents):\n    return (0, 0, 0, cents)"
    )


def test_a_reply_that_wrote_only_the_closing_sentinel_has_the_other_added(
    lean: Backend,
) -> None:
    """The body is the lines above the close that no other region claims."""
    reply = "```lean\ndef impl (n : Nat) : Nat :=\n  n + n\n-- benchproofer:end impl\n```"

    source = assemble(lean.template(), reply, lean, allowed=("impl", "proof"))

    assert (
        markers.parse(source, lean.comment)["impl"].text
        == "def impl (n : Nat) : Nat :=\n  n + n"
    )


def test_only_the_missing_half_of_a_pair_is_added(lean: Backend) -> None:
    """Markers unbalanced some other way are the parse's to report, not this to guess at."""
    reply = (
        "```lean\n-- benchproofer:begin impl\ndef impl (n : Nat) : Nat :=\n  n + n\n"
        "-- benchproofer:end proof\n```"
    )

    with pytest.raises(BenchproofError, match="closes at line"):
        assemble(lean.template(), reply, lean, allowed=("impl", "proof"))


def test_a_reply_that_owns_two_regions_and_marks_neither_is_refused(lean: Backend) -> None:
    """Which of the two it wrote would otherwise be a guess, so the round is retried."""
    reply = "```lean\ndef impl (n : Nat) : Nat := n + n\n```"

    with pytest.raises(BenchproofError, match="region sentinels"):
        assemble(lean.template(), reply, lean, allowed=("impl", "proof"))


def test_a_reply_that_rewrites_a_region_it_was_not_offered_is_refused(lean: Backend) -> None:
    """A variant that writes the specification is not a variant of it."""
    reply = """```lean
-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  True
-- benchproofer:end spec
```
"""

    with pytest.raises(BenchproofError, match="was not offered: 'spec'"):
        assemble(lean.template(), reply, lean, allowed=("impl", "proof"))


def test_a_reply_that_marks_its_regions_in_another_language_is_refused(lean: Backend) -> None:
    """Sentinels the backend's comment token does not open are text, not markers."""
    reply = """```lean
# benchproofer:begin impl
def impl (n : Nat) : Nat := n + n
# benchproofer:end impl
```
"""

    with pytest.raises(BenchproofError, match="contains none of the region"):
        assemble(lean.template(), reply, lean, allowed=("impl", "proof"))


# ---- the claim a variant has to restate ---------------------------------


@pytest.mark.parametrize(
    "regions",
    [
        {
            "impl": "def larger (a : Nat) (b : Nat) : Nat :=\n  a + b",
            "proof": "theorem larger_meets_spec (a : Nat) (b : Nat)\n"
            "    : Spec a b (larger a b) := by\n  unfold Spec larger",
        },
        # A pre-fix implementation, whose accepted proof cannot go through, still restates the
        # claim.
        {"impl": "def impl (n : Nat) : Nat :=\n  n"},
    ],
    ids=["its own proof", "the solution file's proof"],
)
def test_a_variant_that_restates_the_accepted_claim_is_admissible(
    regions: dict[str, str], lean: Backend
) -> None:
    accepted = rival = lean.template()
    for name, body in regions.items():
        rival = markers.replace_region(rival, lean.comment, name, body)

    assert scope(accepted, rival, lean)


def test_a_variant_that_proves_a_claim_of_its_own_is_not_admissible(lean: Backend) -> None:
    """`theorem nothing : True := by trivial` elaborates, and says nothing about the spec."""
    accepted = lean.template()
    rigged = markers.replace_region(
        accepted, lean.comment, "proof", "theorem nothing : True := by trivial"
    )

    verdict = scope(accepted, rigged, lean)

    assert not verdict
    assert "a claim of its own" in verdict.reason
    assert "larger_meets_spec" in verdict.reason


def test_a_probe_is_told_where_it_goes_by_the_checker_that_reads_it() -> None:
    """Inside a Nagini method body a probe is a recursive call; Lean's are top-level."""
    nagini, lean = BACKENDS.get("nagini"), BACKENDS.get("lean4")

    under_nagini = probe_rule(("impl",), nagini.probe_placement)
    under_lean = probe_rule(("impl", "proof"), lean.probe_placement)

    assert "**after** the reference implementation's body" in under_nagini
    assert "after the `end impl`\n  line, in the same fenced block" in under_nagini
    assert "**first**" not in under_nagini
    assert "top-level `example`" in under_lean


def test_every_checker_that_needs_a_witness_says_what_shape_one_takes() -> None:
    """Lean's witness negates the predicate; Velvet's goes through the tester it derives."""
    for name in BACKENDS.names():
        backend = BACKENDS.get(name)
        if backend.witness_required:
            assert backend.witness_placement, name

    lean, velvet = BACKENDS.get("lean4"), BACKENDS.get("velvet")

    assert "negate it" in lean.witness_placement
    assert "derive_tester_for" in velvet.witness_placement
    assert "= false := by decide" in velvet.witness_placement


# ---- a probe written after the region it belongs in ------------------------

#: A model of an HTTP request's body-size header, in `verified-swebench`'s layout: the
#: implementation region is the method's body, so its sentinels are indented and end the file.
ANNOUNCE = """\
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# benchproofer:begin helpers
@Pure
def size_header() -> int:
    return 0


@Pure
def method_get() -> int:
    return 1
# benchproofer:end helpers


# benchproofer:begin spec
def announce_body_size(headers: Dict[int, int], method: int,
                       body_present: bool, body_len: int) -> None:
    Requires(MustTerminate(2))
    Requires(dict_pred(headers))
    Requires(size_header() not in headers)
    Ensures(dict_pred(headers))
    Ensures(Implies(body_present,
                    size_header() in headers and headers[size_header()] == body_len))
    Ensures(Implies(not body_present,
                    (size_header() in headers) == (method != method_get())))
    # benchproofer:end spec
    # benchproofer:begin impl
    if body_present:
        headers[size_header()] = body_len
    elif method != method_get():
        headers[size_header()] = 0
    # benchproofer:end impl
"""
#: An admissibility reply: one bare fenced block holding the region as accepted, then the
#: probe after the closing sentinel, at the top level, its locals typed by comment.
ANNOUNCED = """\
RATIONALE: A bodyless GET on a fresh header map must leave the size header absent.

```
    # benchproofer:begin impl
    if body_present:
        headers[size_header()] = body_len
    elif method != method_get():
        headers[size_header()] = 0
    # benchproofer:end impl


def admissibility_probe() -> None:
    # A bodyless GET: no size header is announced.
    h1 = {}  # type: Dict[int, int]
    announce_body_size(h1, method_get(), False, 0)
    Assert(size_header() not in h1)

    # A body present: its length is announced.
    h2 = {}  # type: Dict[int, int]
    announce_body_size(h2, 7, True, 42)
    Assert(h2[size_header()] == 42)
```
"""


def test_a_probe_written_after_the_region_is_carried_into_it() -> None:
    """Carried to the end of the owned region, the probe leaves the spec view untouched.

    Every screen then reads it, and it is still a module-level function, since the region
    closes the definition it sits in.
    """
    nagini = BACKENDS.get("nagini")
    accepted = markers.parse(ANNOUNCE, COMMENT)["impl"].text

    source = assemble(ANNOUNCE, ANNOUNCED, nagini, allowed=owned(ANNOUNCE, nagini), probe=True)

    impl = markers.parse(source, COMMENT)["impl"].text
    assert impl.startswith(f"{accepted}\n\n\ndef admissibility_probe() -> None:\n")
    assert impl.endswith("    Assert(h2[size_header()] == 42)")
    defined = {
        node.name for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
    }
    assert "admissibility_probe" in defined
    assert nagini.same_spec(ANNOUNCE, source)
    assert scope(ANNOUNCE, source, nagini)
    assert variant.probe_problem(ANNOUNCE, source, nagini) == ""
    assert variant.probe_holds(ANNOUNCE, source, nagini)


def test_a_rival_that_writes_code_after_its_region_does_not_bring_it_into_the_file() -> None:
    """Only a probe's function is carried: every other variant owns its regions and no more."""
    nagini = BACKENDS.get("nagini")

    source = assemble(ANNOUNCE, ANNOUNCED, nagini, allowed=owned(ANNOUNCE, nagini))

    assert source == ANNOUNCE


def test_a_statement_a_probe_writes_after_the_region_is_not_carried() -> None:
    """Only a function of its own is carried from there."""
    nagini = BACKENDS.get("nagini")
    loose = ANNOUNCED.split("def admissibility_probe() -> None:\n")[0] + (
        "h = {}  # type: Dict[int, int]\nannounce_body_size(h, 7, True, 42)\n```\n"
    )

    source = assemble(ANNOUNCE, loose, nagini, allowed=owned(ANNOUNCE, nagini), probe=True)

    assert source == ANNOUNCE


#: Two functions: the first's body is a method's, in a class that goes on past it; the
#: second's body ends the file.
METERED = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Meter:
    # benchproofer:begin spec
    def bump(self, by: int) -> int:
        Requires(MustTerminate(2))
        Requires(by >= 0)
        Ensures(Result() == by + 1)
        # benchproofer:end spec
        # benchproofer:begin impl
        return by + 1
        # benchproofer:end impl

    def reset(self) -> int:
        Ensures(Result() == 0)
        return 0


# benchproofer:begin spec.2
def double(n: int) -> int:
    Requires(MustTerminate(2))
    Requires(n >= 0)
    Ensures(Result() == n + n)
    # benchproofer:end spec.2
    # benchproofer:begin impl.2
    return n + n
    # benchproofer:end impl.2
"""
PROBE = "def admissibility_probe() -> None:\n    Assert(double(2) == 4)\n"


def after_bump(probe: str) -> str:
    """A reply writing ``probe`` after the first function's body, at the top level."""
    region = (
        "        # benchproofer:begin impl\n"
        "        return by + 1\n"
        "        # benchproofer:end impl\n"
    )
    return f"RATIONALE: doubling two.\n\n```python\n{region}\n\n{probe}```\n"


def test_a_probe_after_a_body_its_class_goes_on_past_goes_to_one_that_ends_the_file() -> None:
    """Appended where it was written, the probe would end the class and swallow `reset`."""
    nagini = BACKENDS.get("nagini")
    in_place = markers.replace_region(
        METERED, COMMENT, "impl", f"        return by + 1\n\n\n{PROBE}"
    )
    swallowed = next(
        node for node in ast.parse(in_place).body if isinstance(node, ast.ClassDef)
    )
    assert [node.name for node in swallowed.body] == ["bump"]

    source = assemble(
        METERED, after_bump(PROBE), nagini, allowed=owned(METERED, nagini), probe=True
    )

    regions = markers.parse(source, COMMENT)
    assert regions["impl"].text == "        return by + 1"
    assert regions["impl.2"].text == f"    return n + n\n\n\n{PROBE.rstrip()}"
    tree = ast.parse(source)
    meter = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    assert [node.name for node in meter.body] == ["bump", "reset"]
    assert "admissibility_probe" in {getattr(node, "name", "") for node in tree.body}
    assert nagini.same_spec(METERED, source)
    assert variant.probe_problem(METERED, source, nagini) == ""


def test_a_reply_that_writes_out_the_whole_file_is_read_for_its_probe_alone() -> None:
    """The solution file's own lines between regions are a quotation, not something lost."""
    nagini = BACKENDS.get("nagini")
    whole = f"RATIONALE: doubling two.\n\n```python\n{METERED}\n\n{PROBE}```\n"

    source = assemble(METERED, whole, nagini, allowed=owned(METERED, nagini), probe=True)

    assert markers.parse(source, COMMENT)["impl.2"].text.endswith(PROBE.rstrip())
    assert source.count("def reset(self) -> int:") == 1


def test_a_probe_no_region_can_hold_at_the_top_level_is_not_carried() -> None:
    """With every body inside a definition that goes on, there is nowhere to put a function."""
    nagini = BACKENDS.get("nagini")
    metered = METERED.split("# benchproofer:begin spec.2")[0].rstrip("\n") + "\n"

    source = assemble(
        metered, after_bump(PROBE), nagini, allowed=owned(metered, nagini), probe=True
    )

    assert source == metered


def test_a_lean_example_written_after_the_region_is_carried_into_it(lean: Backend) -> None:
    """A Lean command keyword opens a command of its own wherever it stands."""
    accepted = lean.template()
    body = markers.parse(accepted, lean.comment)["impl"].text
    reply = (
        f"```lean\n-- benchproofer:begin impl\n{body}\n"
        "-- benchproofer:end impl\n\n-- the task's input\n"
        "example : Spec 1 2 (larger 1 2) := by\n  unfold Spec larger; decide\n```\n"
    )

    source = assemble(accepted, reply, lean, allowed=owned(accepted, lean), probe=True)

    impl = markers.parse(source, lean.comment)["impl"].text
    assert "if a ≤ b then b else a" in impl
    assert "example : Spec 1 2 (larger 1 2) := by\n  unfold Spec larger; decide" in impl
    assert variant.probe_problem(accepted, source, lean) == ""


def test_a_lean_theorem_the_file_already_binds_is_not_carried(lean: Backend) -> None:
    """A second `larger_meets_spec` would not elaborate: it is a quotation, or it is stray."""
    accepted = lean.template()
    body = markers.parse(accepted, lean.comment)["impl"].text
    reply = (
        f"```lean\n-- benchproofer:begin impl\n{body}\n"
        "-- benchproofer:end impl\n\ntheorem larger_meets_spec : Spec 1 2 2 := by decide\n```\n"
    )

    source = assemble(accepted, reply, lean, allowed=owned(accepted, lean), probe=True)

    assert source == accepted


def test_a_probe_after_a_method_body_is_not_carried() -> None:
    """Under Velvet a line after the `impl` region may still belong to the method around it."""
    velvet = BACKENDS.get("velvet")
    accepted = LEAN.replace("theorem spec", "def spec")
    reply = (
        "```lean\n-- benchproofer:begin impl\ndef impl (n : Nat) : Nat := n\n"
        "-- benchproofer:end impl\n\nexample : impl 2 = 2 := rfl\n```\n"
    )

    source = assemble(accepted, reply, velvet, allowed=("impl",), probe=True)

    assert "example" not in source


#: A Velvet file whose postcondition names a model function, for probes written as `have`s.
VELVET = """\
-- benchproofer:begin helpers
def pick (a : Option Nat) (d : Nat) : Nat := a.getD d
-- benchproofer:end helpers

-- benchproofer:begin spec
method choose (a : Option Nat) (d : Nat) return (out : Nat)
  ensures out = pick a d
-- benchproofer:end spec
-- benchproofer:begin impl
  do
    let r := a.getD d
    return r
-- benchproofer:end impl

-- benchproofer:begin proof
prove_correct choose by
  loom_solve
-- benchproofer:end proof
"""


@pytest.mark.parametrize(
    ("body", "why"),
    [
        (
            "  do\n    have w : pick (some 3) 7 = 3 := by\n      rfl\n"
            "    let r := a.getD d\n    return r",
            "",
        ),
        (
            "  do\n    have w : pick none 7 = 7 := rfl\n    let r := a.getD 0\n    return r",
            "rewrites the reference implementation",
        ),
        ("  do\n    let r := a.getD d\n    return r", "solution file unchanged"),
    ],
    ids=["adds a statement", "rewrites", "adds none"],
)
def test_a_velvet_probe_is_a_have_beside_the_accepted_lines(body: str, why: str) -> None:
    """Velvet's probe cannot call the method, so it is a statement inside it."""
    found = variant.probe_problem(
        VELVET, markers.replace_region(VELVET, "--", "impl", body), BACKENDS.get("velvet")
    )

    assert why in found if why else found == ""


def test_statements_set_apart_take_the_lines_that_continue_them() -> None:
    code = "  do\n    have w : p\n        = q := by\n      simp\n    let r := 1\n    return r"

    rest, blocks = variant.set_apart(code, ("have",))

    assert rest == "  do\n    let r := 1\n    return r"
    assert blocks == ["    have w : p\n        = q := by\n      simp"]


def test_a_variant_of_a_file_modelling_two_functions_owns_both_bodies() -> None:
    """And writes them by name, so the second body lands in the second function."""
    backend = BACKENDS.get("nagini")
    solution = (
        markers.wrap(COMMENT, "spec", "def first(x: int) -> int:\n    Ensures(Result() == x)")
        + "\n"
        + markers.wrap(COMMENT, "impl", "    return x")
        + "\n"
        + markers.wrap(
            COMMENT, "spec.2", "def second(x: int) -> int:\n    Ensures(Result() > x)"
        )
        + "\n"
        + markers.wrap(COMMENT, "impl.2", "    return x + 1")
        + "\n"
    )
    reply = "```python\n" + markers.wrap(COMMENT, "impl.2", "    return x + 2") + "\n```"

    allowed = owned(solution, backend)
    variant = markers.parse(assemble(solution, reply, backend, allowed=allowed), COMMENT)

    assert allowed == ("impl", "impl.2")
    assert "`impl` and `impl.2` regions" in rule(allowed)
    assert (variant["impl"].text, variant["impl.2"].text) == (
        "    return x",
        "    return x + 2",
    )


#: An accepted Nagini file over a sequence, with a pure helper stated by a quantifier.
PROBED = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin helpers
@Pure
def all_below(xs: PSeq[int], bound: int) -> bool:
    return Forall(int, lambda k: (Implies(0 <= k and k < len(xs), xs[k] < bound), [[xs[k]]]))
# benchproofer:end helpers

# benchproofer:begin spec
def first_below(xs: PSeq[int], bound: int) -> bool:
    Requires(MustTerminate(2))
    Requires(len(xs) > 0)
    Ensures(Result() == (xs[0] < bound))
# benchproofer:end spec
# benchproofer:begin impl
    return xs[0] < bound
# benchproofer:end impl
"""


def probed(asserted: str) -> str:
    """The solution file with a probe after the body that asserts ``asserted``."""
    probe = (
        "    return xs[0] < bound\n\n\n"
        "def admissibility_probe() -> None:\n"
        "    xs = PSeq(1, 5)  # type: PSeq[int]\n"
        f"    Assert({asserted})\n"
    )
    return PROBED.replace("    return xs[0] < bound\n", probe)


@pytest.mark.parametrize(
    ("asserted", "wrong"),
    [
        ("first_below(xs, 2)", False),
        ("all_below(xs, 6) and not all_below(xs, 5)", False),
        ("first_below(xs, 1)", True),
    ],
)
def test_a_probe_holds_only_where_it_asserts_what_the_accepted_implementation_returns(
    asserted: str, wrong: bool
) -> None:
    assert variant.probe_holds(PROBED, probed(asserted), BACKENDS.get("nagini")) is not wrong


#: An accepted Nagini file whose implementation answers outside its precondition too.
HALVING = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def halve(n: int) -> int:
    Requires(MustTerminate(2))
    Requires(n > 0)
    Ensures(Result() == n // 2)
# benchproofer:end spec
# benchproofer:begin impl
    return n // 2
# benchproofer:end impl
"""


def test_a_probe_holds_only_where_the_precondition_admits_every_call_it_makes() -> None:
    """`halve(-4)` is outside the precondition, so its refusal is the precondition's."""
    nagini = BACKENDS.get("nagini")

    def probing(argument: int) -> str:
        return HALVING.replace(
            "    return n // 2\n",
            "    return n // 2\n\n\ndef admissibility_probe() -> None:\n"
            f"    Assert(halve({argument}) == {argument} // 2)\n",
        )

    assert variant.probe_holds(HALVING, probing(4), nagini)
    assert not variant.probe_holds(HALVING, probing(-4), nagini)


@pytest.mark.parametrize(
    ("body", "echo"),
    [
        ("    return not (xs[0] >= bound)\n", True),
        ("    first = xs[0]  # type: int\n    return first < bound\n", True),
        ("    return xs[0] <= bound\n", False),
        # A change no draw reaches is a difference nobody looked at.
        ("    if len(xs) > 100:\n        return False\n    return xs[0] < bound\n", False),
    ],
    ids=["negated", "through a local", "different", "unreached"],
)
def test_a_variant_that_computes_what_the_accepted_one_computes_is_recognized(
    body: str, echo: bool
) -> None:
    variant_file = markers.replace_region(PROBED, "#", "impl", body)

    found = variant.coincides(PROBED, variant_file, BACKENDS.get("nagini"))

    assert bool(found) is echo
    if echo:
        assert "`first_below`" in found


def test_a_quoted_annotation_is_drawn_as_the_type_it_names() -> None:
    """`'PSeq[int]'` is how a file names a type it cannot import at run time."""
    quoted = PROBED.replace("def first_below(xs: PSeq[int]", "def first_below(xs: 'PSeq[int]'")
    variant_file = markers.replace_region(
        quoted, "#", "impl", "    return not (xs[0] >= bound)\n"
    )

    assert "`first_below`" in variant.coincides(quoted, variant_file, BACKENDS.get("nagini"))


#: An accepted Nagini file over an optional string and a pair.
LABELLED = """\
from typing import Optional, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def label(name: Optional[str], pair: Tuple[int, str]) -> str:
    Requires(MustTerminate(2))
    Ensures(True)
# benchproofer:end spec
# benchproofer:begin impl
    if name is None:
        return pair[1]
    return name
# benchproofer:end impl
"""


@pytest.mark.parametrize(
    ("body", "echo"),
    [
        ("    if name is not None:\n        return name\n    return pair[1]\n", True),
        ("    if name is None:\n        return 'none'\n    return name\n", False),
    ],
    ids=["reordered", "different"],
)
def test_optional_strings_and_tuples_are_drawn_to_compare(body: str, echo: bool) -> None:
    variant_file = markers.replace_region(LABELLED, "#", "impl", body)

    found = variant.coincides(LABELLED, variant_file, BACKENDS.get("nagini"))

    assert bool(found) is echo


def test_a_file_that_reaches_outside_a_closed_module_is_not_run_here() -> None:
    """It is a model's code, and would run on the machine the tool runs on."""
    nagini = BACKENDS.get("nagini")
    reaching = markers.replace_region(
        PROBED, "#", "impl", "    __import__('os').system('true')\n    return xs[0] < bound\n"
    )
    probe = probed("first_below(xs, 2)").replace(
        "    Assert(", "    __import__('os').system('true')\n    Assert("
    )

    assert variant.coincides(PROBED, reaching, nagini) == ""
    assert not variant.probe_holds(PROBED, probe, nagini)


#: An accepted Nagini file over objects of a class it defines: its constructor has a
#: precondition, an object holds another of its class, a special method compares two, and
#: the specified function returns a new object.
BOXED = """\
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin helpers
class Box:
    def __init__(self, size: int, inner: Optional['Box']) -> None:
        Requires(MustTerminate(1))
        Requires(size >= 0)
        Ensures(Acc(self.size) and self.size == size)
        Ensures(Acc(self.inner) and self.inner is inner)
        self.size = size  # type: int
        self.inner = inner  # type: Optional[Box]

    def __lt__(self, other: 'Box') -> bool:
        return self.size < other.size
# benchproofer:end helpers

# benchproofer:begin spec
def grown(box: Box, by: int) -> Box:
    Requires(MustTerminate(2))
    Requires(Acc(box.size) and Acc(box.inner) and by >= 0)
    Ensures(Acc(Result().size) and Result().size == box.size + by)
# benchproofer:end spec
# benchproofer:begin impl
    if box.size < 0:
        return Box(0, None)
    return Box(box.size + by, box.inner)
# benchproofer:end impl
"""


#: `BOXED` with a precondition that admits no negative size.
SIZED = BOXED.replace("and by >= 0)", "and by >= 0 and box.size >= 0)")
#: What `BOXED` returns, with the size's sign dropped: the same wherever it is not negative.
UNSIGNED = "    return Box(abs(box.size) + by, box.inner)\n"


@pytest.mark.parametrize(
    ("accepted", "body", "answer", "said"),
    [
        # A size its constructor never sets is one the precondition admits.
        (BOXED, UNSIGNED, "differs", "{size=-"),
        (SIZED, UNSIGNED, "agreed", "`grown`"),
        (
            BOXED,
            "    if box.size < 0:\n        return Box(0, None)\n"
            "    return box.__class__(by + box.size, box.inner)\n",
            "agreed",
            "`grown`",
        ),
        (
            BOXED,
            "    if Box(0, None) < box:\n        return Box(box.size + by, None)\n"
            "    return Box(by, box.inner)\n",
            "differs",
            "something else on `grown(Box(",
        ),
    ],
    ids=[
        "a state its constructor never builds",
        "kept where the precondition admits it",
        "built by its class",
        "a field changed",
    ],
)
def test_an_argument_of_a_class_the_file_defines_is_drawn_over_what_its_precondition_admits(
    accepted: str, body: str, answer: str, said: str
) -> None:
    """Built by its constructor, its fields set to drawn values, compared by its fields.

    The precondition is the domain, so any state it admits is a fair input, whether or not the
    constructor builds it. Two objects built apart are never the same object, so the solution
    file executed alongside itself agrees only because they are compared by what they hold.
    """
    backend = BACKENDS.get("nagini")
    variant_file = markers.replace_region(accepted, "#", "impl", body)

    ran = variant.run_beside(accepted, variant_file, backend)

    assert ran.answer == answer, ran.why
    assert said in ran.why
    assert variant.run_beside(BOXED, BOXED, backend).answer == "agreed"


#: `Box` built by a constructor it inherits, which `run_beside` calls with no arguments.
INHERITED = (
    "class Base:\n"
    "    def __init__(self, size: int) -> None:\n"
    "        self.size = size  # type: int\n\n\n"
    "class Box(Base):\n"
    "    pass\n\n\n"
    "class Unused:"
)


@pytest.mark.parametrize(
    ("change", "said"),
    [
        # Only an `Optional` one is drawn as absent past the bound.
        (("inner: Optional['Box']", "inner: 'Box'"), "of type `Box` for `grown`"),
        (("inner: Optional['Box']", "inner: float"), "of type `Box` for `grown`"),
        (("class Box:", INHERITED), "raised TypeError"),
    ],
    ids=["nested without end", "a parameter nothing draws", "a constructor it cannot call"],
)
def test_an_object_the_run_cannot_build_leaves_the_question_open(
    change: tuple[str, str], said: str
) -> None:
    """A `TypeError` building one means the run did not happen, as calling the function."""
    accepted = BOXED.replace(*change)

    ran = variant.run_beside(accepted, accepted, BACKENDS.get("nagini"))

    assert said in ran.why, ran.why


@pytest.mark.parametrize(
    "reach",
    [
        "grown.__globals__",
        "().__class__.__base__.__subclasses__()",
        "len.__self__",
        "type(box).__mro__",
        "__builtins__",
        "(x for x in ()).gi_frame",
        "getattr(box, 'size')",
        "__import__",
    ],
)
def test_a_name_that_leads_out_of_the_module_stops_the_run(reach: str) -> None:
    """A special method and `__class__` are the module's own; these lead outside it."""
    reaching = markers.replace_region(
        BOXED, "#", "impl", f"    found = {reach}\n    return Box(box.size + by, box.inner)\n"
    )

    ran = variant.run_beside(BOXED, reaching, BACKENDS.get("nagini"))

    assert ran.answer == "not run"
    assert "reaches for something a closed module has no use for" in ran.why


@pytest.mark.parametrize(
    ("axioms", "run"),
    [
        ("# nothing to assume: the operation calls no library function\n", True),
        (
            "@ContractOnly\ndef lookup(key: int) -> int:\n    Ensures(Result() >= 0)\n",
            False,
        ),
    ],
    ids=["a comment", "an assumption"],
)
def test_only_an_axioms_region_that_assumes_something_stops_a_comparison(
    axioms: str, run: bool
) -> None:
    """A region saying there is nothing to assume leaves the file runnable as it is."""
    region = f"# benchproofer:begin axioms\n{axioms}# benchproofer:end axioms\n\n"
    accepted = PROBED.replace(
        "# benchproofer:begin helpers", region + "# benchproofer:begin helpers"
    )
    local = "    first = xs[0]  # type: int\n    return first < bound\n"

    found = variant.coincides(
        accepted, markers.replace_region(accepted, "#", "impl", local), BACKENDS.get("nagini")
    )

    assert bool(found) is run


#: A Nagini file choosing a tier from four integers, one branch taken at a single
#: combination; a comment and a docstring say, in prose, it has no `@ContractOnly` function.
TIERED = '''\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin axioms
# No @ContractOnly axiom: the selection is modeled deeply.
# benchproofer:end axioms

# benchproofer:begin spec
def tier(a: int, b: int, c: int, d: int) -> int:
    """Chosen without any @ContractOnly callee."""
    Requires(MustTerminate(2))
    Requires(a >= 0)
    Ensures(Result() >= 1)
# benchproofer:end spec
# benchproofer:begin impl
    if a >= 6:
        return 3
    elif a == 5 and b == 15 and c == 2 and d == 87:
        return 2
    else:
        return 1
# benchproofer:end impl


# benchproofer:begin spec.2
def key(t: int) -> int:
    Requires(MustTerminate(2))
    Requires(t == 1 or t == 2 or t == 3)
    Ensures(Result() >= 0)
# benchproofer:end spec.2
# benchproofer:begin impl.2
    if t == 3:
        return 1
    return 0
# benchproofer:end impl.2
'''
#: The same choices with the branch chain reordered, which computes the same tiers.
REORDERED = (
    "    if a == 5 and b == 15 and c == 2 and d == 87:\n        return 2\n"
    "    elif a < 6:\n        return 1\n"
    "    else:\n        return 3\n"
)


def test_a_contract_only_decorator_named_in_prose_does_not_stop_a_comparison() -> None:
    """Only a decorator on a function assumes a callee; a comment or a docstring does not."""
    reordered = markers.replace_region(TIERED, "#", "impl", REORDERED)
    decorated = TIERED.replace(
        "# benchproofer:begin spec\n",
        "@ContractOnly\ndef other() -> int:\n    Ensures(Result() >= 0)\n\n\n"
        "# benchproofer:begin spec\n",
        1,
    )

    assert variant.coincides(TIERED, reordered, BACKENDS.get("nagini"))
    assert variant.coincides(decorated, reordered, BACKENDS.get("nagini")) == ""


def test_a_branch_taken_at_one_combination_is_reached_by_running_every_combination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uniform draws seldom reach the branch, so the reordered line would go unlooked at."""
    reordered = markers.replace_region(TIERED, "#", "impl", REORDERED)
    backend = BACKENDS.get("nagini")

    assert "`tier` and `key`" in variant.coincides(TIERED, reordered, backend)
    different = markers.replace_region(
        TIERED, "#", "impl", REORDERED.replace("return 2", "return 3")
    )
    assert variant.coincides(TIERED, different, backend) == ""
    monkeypatch.setattr(variant, "_EXHAUSTIVE", 0)
    assert variant.coincides(TIERED, reordered, backend) == ""


#: A specification whose precondition few of the inputs drawn for it meet.
NARROW = """\
# benchproofer:begin spec
def total(a: int, b: int, c: int) -> int:
    Requires(MustTerminate(2))
    Requires(a == b and b == c and a >= 0)
    Ensures(Result() >= 0)
# benchproofer:end spec
# benchproofer:begin impl
    return a + b + c
# benchproofer:end impl
"""


#: A specification whose function takes a mapping, a type nothing draws for it.
HELD = """\
from typing import Dict

# benchproofer:begin spec
def grow(sizes: Dict[int, int], by: int) -> int:
    Requires(MustTerminate(2))
    Requires(by >= 0)
    Ensures(Result() >= by)
# benchproofer:end spec
# benchproofer:begin impl
    return by
# benchproofer:end impl
"""


@pytest.mark.parametrize(
    ("accepted", "body", "answer", "said"),
    [
        (NARROW, "    return 2 * a\n", "differs", "something else on `total(1, 1, 1)`"),
        (TIERED, REORDERED, "agreed", "every one of"),
        (NARROW, "    return 3 * a\n", "not run", "only 11 of them were admissible"),
        (HELD, "    return by + 1\n", "not run", "of type `Dict[int,int]` for `grow`"),
        (PROBED, "    return Unknown(xs)\n", "not run", "raised NameError"),
    ],
    ids=["an input tells them apart", "agreed", "too few admissible", "undrawn", "undefined"],
)
def test_a_run_on_the_reference_implementation_s_inputs_gives_one_of_three_results(
    accepted: str, body: str, answer: str, said: str
) -> None:
    """Told apart, agreed on enough inputs, or neither, each with what was found.

    Agreement on too few admissible inputs, an argument nothing draws, and a name the run
    does not provide decide nothing, so `coincides` says nothing of them either.
    """
    backend = BACKENDS.get("nagini")
    variant_file = markers.replace_region(accepted, "#", "impl", body)

    ran = variant.run_beside(accepted, variant_file, backend)

    assert ran.answer == answer, ran.why
    assert said in ran.why
    assert bool(variant.coincides(accepted, variant_file, backend)) is (answer == "agreed")


#: A specification over a boolean and an object of five boolean fields, whose precondition
#: admits two of the 64 combinations: a share no number of draws would reach.
FLAGGED = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin helpers
class Flags:
    def __init__(self) -> None:
        self.a = False  # type: bool
        self.b = False  # type: bool
        self.c = False  # type: bool
        self.d = False  # type: bool
        self.e = False  # type: bool
# benchproofer:end helpers

# benchproofer:begin spec
def pick(left: bool, flags: Flags) -> bool:
    Requires(MustTerminate(2))
    Requires(not flags.a and not flags.b and not flags.c and not flags.d and not flags.e)
    Ensures(Result() == left)
# benchproofer:end spec
# benchproofer:begin impl
    return left
# benchproofer:end impl
"""


@pytest.mark.parametrize(
    ("accepted", "answer", "said"),
    [
        (FLAGGED, "agreed", "on all 2 admissible inputs of a finite domain for `pick`"),
        # An integer's pool is a sample of its type, so the share rule holds.
        (
            FLAGGED.replace("self.e = False  # type: bool", "self.e = 0  # type: int").replace(
                "not flags.e", "flags.e == 0"
            ),
            "not run",
            "only 2 of them were admissible",
        ),
    ],
    ids=["every pool its type's whole range", "a pool that samples its type"],
)
def test_a_run_over_a_whole_finite_domain_is_decided_whatever_share_of_it_is_admissible(
    accepted: str, answer: str, said: str
) -> None:
    """Every admissible input of the domain was run, so the enumeration is not a sample."""
    reworded = markers.replace_region(accepted, "#", "impl", "    return not (not left)\n")

    ran = variant.run_beside(accepted, reworded, BACKENDS.get("nagini"))

    assert ran.answer == answer, ran.why
    assert said in ran.why


def test_a_line_a_variant_deletes_at_the_end_of_a_function_is_looked_for_where_code_is() -> (
    None
):
    """The line standing where it stood is the blank one after the function, never run."""
    accepted = (
        "def f(x):\n    if x:\n        return 1\n    return 0\n\ndef g():\n    return 2\n"
    )
    trimmed = "def f(x):\n    if x:\n        return 1\n\ndef g():\n    return 2\n"

    assert variant._changed(accepted, trimmed) == [3]


# ---- which variants are one variant ----------------------------------------

PENNIES = "def impl(cents):\n    return (0, 0, 0, cents)\n"


@pytest.mark.parametrize(
    "written",
    [
        "def impl(cents):\n    # every coin a penny\n    return (0, 0, 0, cents)\n",
        "def impl(cents):\n    return (0, 0, 0, cents)  # the bug the task reports\n",
        "def impl(cents):\n\n        return (0, 0, 0, cents)\n",
    ],
    ids=["comment line", "trailing comment", "spacing"],
)
def test_what_the_code_does_not_compute_does_not_make_a_variant_new(
    written: str, falsifier: Backend
) -> None:
    assert variant.fingerprint(written, falsifier) == variant.fingerprint(PENNIES, falsifier)


def test_a_hash_inside_a_python_string_is_code_and_not_a_comment(falsifier: Backend) -> None:
    """Masking from the first ``#`` would make these one variant, and they are two."""
    tagged = 'def impl(text):\n    return text.startswith("{}")\n'

    first = variant.fingerprint(tagged.format("#"), falsifier)
    second = variant.fingerprint(tagged.format("# "), falsifier)

    assert first != second


def test_a_comment_the_python_tokenizer_cannot_find_is_masked_by_its_token(
    lean: Backend, falsifier: Backend
) -> None:
    """Another language's comments, and those in Python the tokenizer refuses."""
    bare = "def impl (n : Nat) : Nat := n"
    unfinished = '    x = """never closed'
    noted = variant.fingerprint(f"{bare} -- the identity", lean)

    assert noted == variant.fingerprint(bare, lean)
    assert noted != variant.fingerprint(f"{bare} + 1", lean)
    assert variant.fingerprint(f"{unfinished}  # a note", falsifier) == variant.fingerprint(
        unfinished, falsifier
    )
