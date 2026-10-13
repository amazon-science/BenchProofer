# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_coverage: measuring what a passing battery actually defends.

The checker exists because G-PBT is silent about coverage — a two-case manifest
passes exactly as loudly as a twelve-case one. It is advisory, but it decides
which cells go back for repair, so its two judgments have to be trustworthy in
both directions:

  * a battery that DOES vary a binder must not be reported as pinned (the first
    cut searched for binder NAMES in the witness text and false-positived
    everywhere, because witnesses apply the spec POSITIONALLY);
  * a battery that never moves a binder must not pass (the same cut passed a
    battery whose witnesses all held one binder at `true`).

Both regressions are pinned below with the shapes that produced them.
"""
from __future__ import annotations

import pytest

from pbt_coverage import (
    _align,
    _binders,
    _drop_result,
    _spec_args,
    _split_args,
    spec_surface,
)

# ---------------------------------------------------------------------------
# argument splitting: application atoms, not tokens
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text,want", [
    # the shape that broke the name-based heuristic: nested parens per argument
    ("(some (-1)) (some 100000) (some 2) := by",
     ["(some (-1))", "(some 100000)", "(some 2)"]),
    ("false true := by", ["false", "true"]),
    # a record literal is ONE argument even though it contains spaces + commas
    ('{rest := "r", code := some "c1"} {rest := "r"} := by',
     ['{rest := "r", code := some "c1"}', '{rest := "r"}']),
    ("[0,1,2] 3 true := by", ["[0,1,2]", "3", "true"]),
    ("(f (g 3)) none := by", ["(f (g 3))", "none"]),
])
def test_split_args_respects_brackets(text, want):
    assert _split_args(" " + text) == want


def test_split_args_stops_at_a_top_level_relation():
    """The velvet witness form is `<name>Tester <args> = false`. Reading `=` and
    `false` as arguments would inflate the arity and defeat alignment."""
    assert _split_args(' (some "a".toList) = false := by') == ['(some "a".toList)']


def test_split_args_stops_at_by_with_no_assign():
    assert _split_args(" true false by decide") == ["true", "false"]


def test_split_args_does_not_escape_an_enclosing_group():
    """Called on the tail after a head match, a closing paren at depth 0 belongs
    to a group that started BEFORE the head, so it ends the argument list."""
    assert _split_args(" 3) := by") == ["3"]


# ---------------------------------------------------------------------------
# head forms: lean `problem_spec_*`, velvet `*Tester`
# ---------------------------------------------------------------------------

LEAN_WITNESS = """\
example : ¬ problem_spec_availableCpus (some (-1)) (some 100000) (some 2)
    (implementation_availableCpus (some (-1)) (some 100000) (some 2)) := by
  unfold problem_spec_availableCpus implementation_availableCpus rawCpu
  decide
"""

VELVET_WITNESS = """\
extract_program_for recordErrorCode
prove_precondition_decidable_for recordErrorCode
prove_postcondition_decidable_for recordErrorCode
derive_tester_for recordErrorCode

example : recordErrorCodeTester (some "a".toList) = false := by
  decide
"""


def test_reads_the_lean_spec_application():
    assert _spec_args(LEAN_WITNESS, "availableCpus") == [
        "(some (-1))", "(some 100000)", "(some 2)",
        "(implementation_availableCpus (some (-1)) (some 100000) (some 2))"]


def test_reads_the_velvet_tester_application():
    """`derive_tester_for recordErrorCode` names the bare method BEFORE the
    example, so a bare-name head must be tried last or the directive's own
    argument gets parsed as the witness's."""
    assert _spec_args(VELVET_WITNESS, "recordErrorCode") == ['(some "a".toList)']


def test_quantified_witness_is_unreadable_not_uncovered():
    """A `∀`-witness applies the spec to BOUND VARIABLES. Reading `n` as a value
    would report the binder as pinned to the string 'n' — a false finding."""
    assert _spec_args(
        "example : ∀ n, ¬ problem_spec_f n (implementation_f n) := by decide",
        "f") == []


def test_unknown_predicate_yields_nothing():
    assert _spec_args("example : True := trivial", "f") == []


# The `<base>Exec` head form. It got both of the reader's failure modes at once:
# the `extract_program_for <base>` preamble was matched as the application
# (yielding ['example', ':', '¬', ...]) and the `match ... with | ...` arms were
# read as further arguments.
EXEC_WITNESS = """\
extract_program_for applyWithCopyChoice
prove_precondition_decidable_for applyWithCopyChoice

example :
  ¬ ( (effectiveCopy false (some true) = true →
        (match applyWithCopyChoiceExec #[(1:Int)] false (some true) with
         | DivM.res (_, d) => d | _ => #[99]) = #[(1:Int)])
    ) := by decide
"""


def test_a_directive_naming_the_method_is_not_an_application():
    """A velvet witness may open with `extract_program_for <base>`. Parsing there
    produces argument atoms that then align against a same-length binder list by
    coincidence, reporting binders as "pinned to '¬'"."""
    assert _spec_args(EXEC_WITNESS, "applyWithCopyChoice") == [
        "#[(1:Int)]", "false", "(some true)"]


def test_a_match_arm_is_not_an_argument():
    """`match <base>Exec a b c with | ...` — without a keyword terminator the
    arms were read as arguments, so the shape either failed to align (a false
    never-named finding) or aligned wrongly and reported a garbage held value."""
    args = _spec_args(EXEC_WITNESS, "applyWithCopyChoice")
    assert not any(a in ("with", "|", "DivM.res") for a in args)


# ---------------------------------------------------------------------------
# alignment: which position is the RESULT
# ---------------------------------------------------------------------------


def test_align_drops_a_trailing_result():
    """`_align` takes the def's FULL binder list, result included."""
    args = _spec_args(LEAN_WITNESS, "availableCpus")
    binders = ["cpuQuotaFile", "cpuPeriodFile", "cpuSharesFile", "result"]
    assert _align(args, binders) == [
        "(some (-1))", "(some 100000)", "(some 2)"]
    assert _drop_result(binders, args) == [
        "cpuQuotaFile", "cpuPeriodFile", "cpuSharesFile"]


def test_align_drops_a_leading_result():
    """Result position is per-bundle, so it is located by finding the
    `implementation_*` application rather than assumed to be last. A spec may
    name its result for its domain (`objs`, `toks`), so a name-based guess would
    shift every later position onto the wrong binder."""
    args = _spec_args(
        "example : ¬ problem_spec_count (implementation_count 3) 3 := by decide",
        "count")
    assert _align(args, ["r", "x"]) == ["3"]
    assert _drop_result(["r", "x"], args) == ["x"]


def test_align_keeps_a_result_free_application():
    """The velvet tester runs the program itself, so there is no result arg."""
    assert _align(['(some "a")'], ["supplied"]) == ['(some "a")']


def test_align_refuses_a_shape_it_cannot_map():
    """Unreadable must stay distinguishable from uncovered: a shape that maps to
    neither arity returns None so the caller falls back rather than reporting a
    gap it did not measure."""
    assert _align(["a", "b", "c"], ["x", "y"]) is None
    assert _align([], ["x", "y"]) is None


def test_align_reads_no_arguments_as_unreadable_not_as_a_shape():
    """On a ONE-binder spec the empty list matched the "result already dropped
    upstream" arm and aligned as the empty tuple, so a cell whose every witness
    was unreadable reported `binders=0 pts=1 ok` — a clean line saying "nothing to
    cover" about a real input, with the by-name fallback never running."""
    assert _align([], ["x"]) is None
    assert _align([], []) is None


# The witness quantifies over its input and pins the probed point in a
# HYPOTHESIS, because the input is an opaque handle no literal inhabits. Every
# such witness then reads as the same argument, `call`.
QUANTIFIED_WITNESS = """\
extract_program_for dispatchUfunc

example (call : Int)
    (h1 : coreUfunc call = Except.ok 0) :
    dispatchUfuncExec call ≠ DivM.res (ufuncSpec call) := by
  unfold dispatchUfuncExec dispatchUfunc ufuncSpec
  rw [h1]
  simp [NonDetT.run, pure]
"""


def test_a_head_bound_variable_is_not_a_probed_value():
    """The point lives in `h1`, not in the argument list. Comparing the VARIABLE
    across witnesses reported pts=1 on a battery that discriminates four distinct
    outcomes of the wrapped computation. Unreadable, exactly as `∀` is."""
    assert _spec_args(QUANTIFIED_WITNESS, "dispatchUfunc") == []


def test_a_literal_argument_is_still_read_when_the_head_binds_something_else():
    """The exclusion is per-NAME, not per-witness: a witness may bind a type or a
    hypothesis in its head and still apply the spec to concrete values."""
    w = ("example (h : cfg = none) :\n"
         "    fTester (some 3) false = false := by\n  decide\n")
    assert _spec_args(w, "f") == ["(some 3)", "false"]


# ---------------------------------------------------------------------------
# end to end on the two shapes that produced the original false verdicts
#
# Built as synthetic bundles rather than read from a released corpus. The first
# cut pointed at live cells, and repairing one of them (3 witnesses at one point
# -> 6 distinct points) then failed the test that existed to pin the finding. A
# regression test whose fixture is a live artifact stops testing the checker the
# moment the artifact is fixed, which is exactly when the check still needs to
# hold. The shapes below are copies of the two it was built from.
# ---------------------------------------------------------------------------

# Three binders sharing one type annotation, every witness passing them
# POSITIONALLY. This is what the name-search heuristic
# flagged as three pinned binders while all three genuinely vary.
CPUS_SRC = """\
def problem_spec_availableCpus
    (cpuQuotaFile cpuPeriodFile cpuSharesFile : Option Int) (result : Option Int) : Prop :=
  result = rawCpu cpuQuotaFile cpuPeriodFile cpuSharesFile

def implementation_availableCpus
    (cpuQuotaFile cpuPeriodFile cpuSharesFile : Option Int) : Option Int :=
  rawCpu cpuQuotaFile cpuPeriodFile cpuSharesFile

theorem correct_availableCpus (a b c : Option Int) :
    problem_spec_availableCpus a b c (implementation_availableCpus a b c) := by
  rfl
"""


def _wit(base: str, args: str) -> str:
    return (f"example : ¬ problem_spec_{base} {args}\n"
            f"    (implementation_{base} {args}) := by\n  decide\n")


def _cell(tmp_path, src: str, tests: list[dict], backend="lean") -> list[str]:
    """A minimal bundle: a frozen Solution.lean plus a SPEC_TESTS manifest."""
    from pbt_coverage import audit_cell
    (tmp_path / "Solution.lean").write_text(src)
    (tmp_path / "properties.py").write_text(
        "SPEC_TESTS = " + repr(tests) + "\n")
    return audit_cell(tmp_path, backend)["findings"]


def test_positional_variation_is_not_a_gap(tmp_path):
    """Five witnesses move all three binders, but pass them positionally:
    `(some (-1)) (some 100000) (some 2)`, `(some 50000) ... none`,
    `none none none`. The name-search heuristic flagged all three as pinned."""
    args = ["(some (-1)) (some 100000) (some 2)",
            "(some 50000) (some 100000) none",
            "(some 200000) (some 100000) none",
            "none none none"]
    tests = [{"id": f"r{i}", "kind": "uniqueness", "expect": "reject",
              "module": CPUS_SRC, "rationale": "attacks the quota adjustment",
              "refinement": "...", "witness": _wit("availableCpus", a)}
             for i, a in enumerate(args)]
    tests.append({"id": "pos", "kind": "soundness", "expect": "verify",
                  "module": CPUS_SRC, "rationale": "restructured, same values"})
    assert _cell(tmp_path, CPUS_SRC, tests) == []


# A battery as SHIPPED before repair: three witnesses, all at the same input
# point.
WINDOWS_SRC = """\
def problem_spec_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool)
    (result : List (List Int)) : Prop :=
  result = (List.range xs.length).map (windowAt xs window center)

def implementation_rollingWindows
    (xs : List Int) (window : Nat) (center : Bool) : List (List Int) :=
  (List.range xs.length).map (windowAt xs window center)

theorem correct_rollingWindows :
    ∀ (xs : List Int) (window : Nat) (center : Bool),
      problem_spec_rollingWindows xs window center
        (implementation_rollingWindows xs window center) := by
  rfl
"""


def _windows(args: list[str]) -> list[dict]:
    tests = [{"id": f"r{i}", "kind": "uniqueness", "expect": "reject",
              "module": WINDOWS_SRC, "rationale": "attacks the windowAt slice",
              "refinement": "...", "witness": _wit("rollingWindows", a)}
             for i, a in enumerate(args)]
    tests.append({"id": "pos", "kind": "soundness", "expect": "verify",
                  "module": WINDOWS_SRC, "rationale": "same map, unfolded"})
    return tests


def test_a_single_probe_point_is_reported_once_for_the_obligation(tmp_path):
    """Every witness at `[0,1,2] 3 true` pins all three binders trivially.
    Naming each one repeats the same fact three times; the SHAPE is the
    finding, so it must be reported exactly once for the obligation."""
    f = _cell(tmp_path, WINDOWS_SRC, _windows(["[0,1,2] 3 true"] * 3))
    assert len(f) == 1 and "SAME input point" in f[0]


def test_one_pinned_binder_among_varying_ones_is_named(tmp_path):
    """The other direction, and the finding that sends a battery back for
    repair: it DOES move `xs` and `window`, so it is not degenerate, but
    `center` never leaves `true`. A rival that mishandled only
    the non-centered alignment would verify against every witness here."""
    f = _cell(tmp_path, WINDOWS_SRC, _windows(
        ["[0,1,2] 3 true", "[0,1,2,3,4] 7 true", "[5,6,7] 2 true"]))
    assert len(f) == 1 and "'center'" in f[0] and "pinned to true" in f[0]


def test_varying_every_binder_clears_the_finding(tmp_path):
    """The repair the finding asks for: witnesses moved onto 6 distinct points,
    `center` among them. Pinning this keeps the checker honest in the direction
    that matters — a cleared finding must mean the coverage arrived, not that
    the checker stopped looking."""
    assert _cell(tmp_path, WINDOWS_SRC, _windows(
        ["[0,1,2] 3 true", "[0,1,2,3,4] 7 true", "[0,1,2] 2 false",
         "[0,1,2] 3 false", "[3,4] 2 false", "[5,6,7] 2 true"])) == []


# The shape that produces a false coverage finding an audit has to rule out.
# `operandPresent` is held at `true` by every witness because
# `require operandPresent = true` is the spec —
# no admissible input moves it, so there is no repair to make.
MASK_SRC = """\
method resolveMask
    (selfMask : Option (List Int))
    (operandMask : Option (List Int))
    ({third})
    return (out : Option (List Int))
{require}  ensures out = selfMask.orElse (fun _ => operandMask)
  do
    -- impl-start
    return (selfMask.orElse (fun _ => operandMask))
    -- impl-end
"""


def _mask_src(require: str, third: str = "operandPresent : Bool") -> str:
    return MASK_SRC.format(require=require, third=third)


def _mask(src: str, args: list[str]) -> list[dict]:
    tests = [{"id": f"r{i}", "kind": "uniqueness", "expect": "reject",
              "module": src, "rationale": "attacks the carry-over branch",
              "refinement": "...",
              "witness": ("extract_program_for resolveMask\n"
                          "derive_tester_for resolveMask\n\n"
                          f"example : resolveMaskTester {a} = false := by\n"
                          "  decide\n")}
             for i, a in enumerate(args)]
    tests.append({"id": "pos", "kind": "soundness", "expect": "verify",
                  "module": src, "rationale": "same value, case-split shape"})
    return tests


# Both directions of the exemption run over the SAME witnesses, so the only
# variable is whether the precondition pins the binder.
_MASK_ARGS = ["(some [1]) none true", "none (some [2]) true",
              "(some [1]) (some [2]) true"]


def test_a_binder_the_precondition_pins_raises_no_finding(tmp_path):
    """End to end: the exemption has to SUPPRESS the finding, not merely park the
    name in `pinned_by_spec`. Every witness holds `operandPresent` at `true`
    while moving the other two."""
    src = _mask_src("  require operandPresent = true\n")
    assert _cell(tmp_path, src, _mask(src, _MASK_ARGS), "velvet") == []


def test_the_same_battery_without_the_require_is_a_finding(tmp_path):
    """The control. Drop the precondition and the identical witnesses become a
    real gap — a rival that mishandled `operandPresent = false` would verify
    against all three. Without this the test above could pass because the
    checker stopped looking rather than because the spec forbids the input."""
    src = _mask_src("")
    f = _cell(tmp_path, src, _mask(src, _MASK_ARGS), "velvet")
    assert len(f) == 1 and "'operandPresent'" in f[0]
    assert "pinned to true" in f[0]


def test_a_relational_precondition_does_not_exempt_its_binder(tmp_path):
    """The exemption covers only a binder the precondition pins to ONE value.
    `require year ≤ 9999` mentions the binder and constrains it, but leaves 10000
    admissible values a rival can abuse, so witnesses stuck at one of them are
    still a gap. Pinning the narrow reading keeps the exemption from growing into
    "any binder the precondition mentions"."""
    src = _mask_src("  require year ≤ 9999\n", "year : Nat")
    f = _cell(tmp_path, src, _mask(src, ["(some [1]) none 2024",
                                         "none (some [2]) 2024",
                                         "(some [1]) (some [2]) 2024"]),
              "velvet")
    assert len(f) == 1 and "'year'" in f[0] and "pinned to 2024" in f[0]


def test_every_witness_unreadable_falls_back_instead_of_reading_clean(tmp_path):
    """The two fixes composed. Every witness quantifies over its input, so nothing
    is measurable positionally; the cell must fall through to the by-name signal
    and report the binder no reject case names. Reading the empty argument list as
    a SHAPE instead printed `binders=0 pts=1 ok` — the worst possible line,
    because it says the question was asked and answered."""
    src = _mask_src("")
    tests = [{"id": "r0", "kind": "uniqueness", "expect": "reject",
              "module": src, "rationale": "attacks the carry-over",
              "refinement": "...",
              "witness": ("example (m : Option (List Int)) (h : m = none) :\n"
                          "    resolveMaskTester m none true = false := by\n"
                          "  simp [h]\n")}]
    tests.append({"id": "pos", "kind": "soundness", "expect": "verify",
                  "module": src, "rationale": "same value"})
    f = _cell(tmp_path, src, tests, "velvet")
    assert any("'operandPresent'" in x and "never named" in x for x in f)
    assert any("witnesses unreadable" in x for x in f)


def test_a_double_negated_literal_pin_is_still_a_pin(tmp_path):
    """`require ¬ (operandPresent = false)` fixes the binder exactly as hard as
    `= true` does, so the exemption reads through the negation. Missing this
    would send a cell back for a repair its own precondition forbids."""
    src = _mask_src("  require ¬ (operandPresent = false)\n")
    assert _cell(tmp_path, src, _mask(src, _MASK_ARGS), "velvet") == []


# ---------------------------------------------------------------------------
# spec surface
# ---------------------------------------------------------------------------

LEAN_SRC = """\
def problem_spec_f (a : Bool) (b : Nat) (result : Bool) : Prop :=
  result = (a && b > 0)

def implementation_f (a : Bool) (b : Nat) : Bool := a && b > 0

theorem correct_f (a : Bool) (b : Nat) : problem_spec_f a b (implementation_f a b) := by
  rfl
"""


def test_spec_surface_reads_every_binder():
    surf = spec_surface(LEAN_SRC, "lean")
    assert surf["correct_f"]["binders"] == ["a", "b", "result"]


def test_spec_surface_finds_obligations_that_bind_before_the_colon():
    """An obligation can be written `theorem correct_f (a : T) :`, and a pattern
    anchored on `correct_\\w+\\s*:` skips it, and an obligation the
    surface never lists is an obligation whose coverage is never checked."""
    src = LEAN_SRC.replace(
        "theorem correct_f (a : Bool) (b : Nat) : problem_spec_f",
        "theorem correct_f (a : Bool) (b : Nat) :\n    problem_spec_f")
    assert "correct_f" in spec_surface(src, "lean")


def test_a_lean_corollary_with_no_problem_spec_still_has_a_surface():
    """An obligation can be a SPECIALIZED corollary stated alongside the general
    one (`correct_getGroupBy_isNone` next to `correct_getGroupBy`), with no
    `problem_spec_getGroupBy_isNone` to read the binders from. Reading nothing
    reports it as having no binders, so a real coverage gap on it could never be
    raised — the binders are on the theorem."""
    src = LEAN_SRC + """
theorem correct_f_true (b : Nat) :
    implementation_f true b = (b > 0) := by
  rfl
"""
    surf = spec_surface(src, "lean")
    assert surf["correct_f_true"]["binders"] == ["b"]
    assert surf["correct_f"]["binders"] == ["a", "b", "result"]


# ---------------------------------------------------------------------------
# velvet spec surface
#
# The velvet carrier declares inputs in the method signature and the result
# separately in `return (...)`, so it needs its own parse. Every shape below is
# one the first cut got wrong, and each failed the SAME way: it reported the
# bundle as having no obligation or no clause at all, which reads as "nothing to
# cover" rather than as a finding.
# ---------------------------------------------------------------------------

VELVET_SRC = """\
method wrapped
    (definingModule : List Char)
    (publicPath : Option (List Char))
    (exactType : Bool)
    return (out : List Char)
  ensures (publicPath ≠ none ∧ exactType = true) → out = publicPath.getD []
  -- a comment line explaining the fallback
  ensures ¬(publicPath ≠ none ∧ exactType = true) →
    out = definingModule ++ ['.']
  do
    -- impl-start
    ensures_is_not_a_keyword_here
    -- impl-end
"""


def test_a_wrapped_velvet_signature_is_not_an_empty_surface():
    """A method may wrap its signature across several lines. Without DOTALL the
    pattern matched nothing, so those bundles reported obl=0 and every coverage
    question about them went unasked."""
    surf = spec_surface(VELVET_SRC, "velvet")
    assert surf["wrapped"]["binders"] == ["definingModule", "publicPath",
                                          "exactType"]


def test_a_wrapped_ensures_keeps_its_continuation():
    """An `ensures` may wrap too, and truncating at the newline drops exactly
    the half of the clause a rival would be built to violate — here the whole
    right-hand side of the fallback."""
    clauses = spec_surface(VELVET_SRC, "velvet")["wrapped"]["clauses"]
    assert len(clauses) == 2
    assert clauses[1].endswith("out = definingModule ++ ['.']")


def test_comments_do_not_leak_into_a_clause():
    """A comment absorbed into the preceding wrapped clause would be scanned for
    identifiers, making an unattacked clause look referenced by a rationale that
    happens to share a word with the prose."""
    clauses = spec_surface(VELVET_SRC, "velvet")["wrapped"]["clauses"]
    assert not any("comment" in c for c in clauses)


def test_mut_is_a_modifier_not_a_binder_name():
    """`(mut data : Array Int)` — reading `mut` as a name shifts every later
    position onto the wrong binder, so a pinned-binder finding is attributed to
    the wrong input and reports a nonsense held value. 34 methods declare one."""
    surf = spec_surface(
        "method m (mut data : Array Int) (configuredCopy : Bool)\n"
        "    return (u : Unit)\n"
        "  ensures data = dataOld\n"
        "  do\n", "velvet")
    assert surf["m"]["binders"] == ["data", "configuredCopy"]


def test_a_binder_legitimately_named_ref_survives():
    """The strip is leading-position only: `ref` and friends are real names."""
    surf = spec_surface("method m (ref : List Char) return (out : List Char)\n"
                        "  ensures out = ref\n  do\n", "velvet")
    assert surf["m"]["binders"] == ["ref"]


def test_a_binder_the_precondition_fixes_is_not_a_coverage_gap():
    """`require operandPresent = true` — no admissible input moves that binder,
    so "pinned across all rivals" is the spec, not a gap, and there is no repair
    to make. Narrow on purpose: a relational precondition (`year <= 9999`) still
    leaves values a rival can abuse and is NOT exempted."""
    surf = spec_surface(
        "method m (mask : Option Nat) (present : Bool) (year : Nat)\n"
        "    return (out : Option Nat)\n"
        "  require present = true\n"
        "  require year ≤ 9999\n"
        "  ensures out = mask\n"
        "  do\n", "velvet")
    assert surf["m"]["pinned_by_spec"] == {"present"}


def test_the_impl_region_contributes_no_clauses():
    """`do` ends the spec region; anything below it is implementation."""
    clauses = spec_surface(VELVET_SRC, "velvet")["wrapped"]["clauses"]
    assert not any("not_a_keyword" in c for c in clauses)


@pytest.mark.parametrize("sig,want", [
    # the shape that silently emptied 16 specs' binder lists: a PARENTHESIZED
    # type. `\\([^():]+\\)` cannot match `(result : List (List Int))`, so the
    # group is skipped and the spec reads as having fewer inputs than it has.
    ("(xs : List Int) (window : Nat) (center : Bool) (result : List (List Int))",
     ["xs", "window", "center", "result"]),
    ("(r : Option (Option String))", ["r"]),
    ("(f : Nat → (Nat → Nat)) (result : Nat)", ["f", "result"]),
    # several names share one type annotation
    ("(a b : Bool) (result : Bool)", ["a", "b", "result"]),
    # implicit/instance binders take no positional argument
    ("{α : Type} [Inhabited α] (x : α) (result : α)", ["x", "result"]),
    ("", []),
])
def test_binders_scans_balanced_groups(sig, want):
    assert _binders(sig) == want
