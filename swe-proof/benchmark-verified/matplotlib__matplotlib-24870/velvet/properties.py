"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24870 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct chooseLevelArg`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method that selects a level specification for a
2-D field plot when no explicit level keyword was passed; the carrier is the
pre-dispatch specification ``LevelArg``, either an automatic ``count n`` or an
``explicit`` list of ``Rat`` level positions):

  chooseLevelArg (levelsKwSet : Bool) (levelsKw : LevelArg)
                 (posGiven : Bool)    (posArg : LevelArg)
                 (boolField : Bool)   (filled : Bool)  return (out : LevelArg)

with FIVE independent top-level ``ensures`` clauses forming a priority cascade:

  C1  levelsKwSet                                         → out = levelsKw
  C2  ¬levelsKwSet ∧ posGiven                             → out = posArg
  C3  ¬levelsKwSet ∧ ¬posGiven ∧ boolField ∧ filled       → out = explicit [0, 1/2, 1]
  C4  ¬levelsKwSet ∧ ¬posGiven ∧ boolField ∧ ¬filled      → out = explicit [1/2]
  C5  ¬levelsKwSet ∧ ¬posGiven ∧ ¬boolField               → out = count 7

The DISCRIMINATING content of the change is C3/C4 (and the fact that C5 no longer
fires for a boolean field): a boolean field, absent explicit levels, gets a
constant boundary specification — three bracketing positions when regions are
filled, a single interior position otherwise — instead of the ordinary automatic
count. The two boolean facets are pinned ELEMENT-BY-ELEMENT with exact ``Rat``
positions (``0``, ``1/2``, ``1`` are dyadic, so ``Rat`` is order- and
value-faithful and equality is decidable). There is NO opaque answer key in any
branch (the ``axioms`` region is empty — the whole selection is grounded in the
method's own flag/value inputs), so every uniqueness rival attacks a concrete
clause: which branch fires, the element positions it emits, and their order.

CARRIER WIDTH vs. the nagini sibling. The nagini model FIXED ``has_explicit ==
False`` and modeled only the two-valued/continuous split (its ``two_valued`` ⇔
``boolField`` here, ``filled`` ⇔ ``filled``, and its ``not two_valued`` branch ⇔
C5). This velvet carrier is WIDER: it also models the explicit-keyword (C1) and
positional-argument (C2) legs of the same selection cascade that surround the
changed branch. So the sibling's five two-valued rivals port onto C3/C4/C5, and
TWO ADDITIONAL rivals (C1, C2) are authored to attack the wider surface — a
faithful port covers the clauses THIS bundle models, not merely the ones nagini
did. The sibling's ``not two_valued`` pin was to a ``@Pure`` ``auto_levels``
axiom (an oracle); here the continuous default is the concrete ``count 7`` with
no oracle, so there is no echo-vulnerability class and the sibling's honest-echo
control is replaced by two grounded positive controls.

ADVERSARIAL READ of the nagini classes on this carrier (see footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling itself records
    ``has_readonly_input == False``: every parameter is a by-value scalar and the
    only ``Acc`` is on the freshly-built result the impl owns fully, so even on
    nagini there is no read-only input to overwrite. Lean/Velvet are
    referentially transparent a fortiori: every input is an immutable value, the
    method declares no ``mut`` binder, there is no heap and no aliasing. No
    substitute probe is fabricated (per the porting map, this class is dropped,
    not replaced).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is empty; every clause
    pins ``out`` to a concrete literal or to an input value (``levelsKw`` /
    ``posArg``). There is no answer key to echo. Replaced by grounded positive
    controls.
  * ADMISSIBILITY — RE-AIMED, not vacuous. There is no ``require`` clause, so the
    sibling's "a normal input satisfies the precondition" probe has no referent;
    but on a total domain the residual risk is a DEGENERATE post-image, and that
    IS expressible here. See ``admiss-postimage-nondegenerate``: an in-region
    ``assert`` that the three values C3/C4/C5 pin are pairwise DISTINCT on this
    carrier. Without it, a carrier that collapsed those values would let every
    uniqueness rival attack nothing while the battery still reported SOUND.
  * PARTIAL-DOMAIN / VALUE — the heart of the port. Each rival gets the carrier
    type right (returns a ``LevelArg``) and is correct on part of the cascade,
    but diverges on one clause. Nine rivals: the five ported two-valued ones, the
    three the wider carrier adds (C1/C2/C5), and one that breaks C4 ALONE while
    leaving all four other clauses intact.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT over a TRANSPARENT carrier
(``LevelArg`` derives ``DecidableEq``; every input is ``Bool`` or a concrete
``LevelArg`` literal). A witness reaches the impl through Velvet's extractor
(``extract_program_for chooseLevelArg`` gives ``chooseLevelArgExec … =
NonDetT.run (chooseLevelArg …)``) and states, at ONE concrete input,
``chooseLevelArgExec … ≠ DivM.res <gold's output>`` — i.e. the impl's output
contradicts the postcondition there. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The residual (in)equality is over ``Rat`` list literals, on which plain
``decide`` STALLS (the ``Rat`` ``Decidable`` instance does not reduce — measured);
the witness therefore closes it with ``unfold …; simp [NonDetT.run, pure] <;>
decide +kernel`` (the ``+kernel`` reducer computes the ``Rat`` comparison the
elaborator's ``decide`` leaves stuck). Every reject witness was checked
out-of-band with two real builds: it ELABORATES against its rival (the wrong
constant/branch makes ``≠`` provably true) and FAILS against the frozen solution
(gold's output equals the RHS, so ``decide`` refutes ``≠`` — the required
discrimination). No witness binds a hypothesis (the carrier is transparent), so
there is no joint-satisfiability obligation; no ``sorry``/``admit``/
``native_decide``/``axiom`` appears (``decide +kernel`` is the trusted kernel
reducer, not ``native_decide``).

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the whole selection is concrete over the inputs. Nothing in the proof
rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24870"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct chooseLevelArg
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the nested keyword→positional→
# boolField→count cascade). Every rival/reshape replaces this single block.
_IMPL = (
    "    if levelsKwSet then\n"
    "      return levelsKw\n"
    "    else\n"
    "      if posGiven then\n"
    "        return posArg\n"
    "      else\n"
    "        if boolField then\n"
    "          if filled then\n"
    "            return (LevelArg.explicit [0, 1/2, 1])\n"
    "          else\n"
    "            return (LevelArg.explicit [1/2])\n"
    "        else\n"
    "          return (LevelArg.count 7)"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as-is, so the wrong impl leaves the
# postcondition goal unsolved and the rival MODULE fails to build — which is what
# expect="reject" requires. The witness, not the module build, is what attributes
# the rejection to the spec.
_PROOF = "prove_correct chooseLevelArg by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (proof frozen).

    Both positive controls are observationally identical reshapes whose residual
    obligation the frozen `loom_solve` still closes, so the proof block is never
    retuned — every variant edits ONLY the impl body via this one helper.
    """
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. Reaches the impl's extracted program (extraction needs
# ---- no re-authoring — it just names `chooseLevelArgExec`) and states, at one
# ---- concrete input, that the impl's output contradicts the postcondition:
# ---- `chooseLevelArgExec <args> ≠ DivM.res <gold output>`. The residual is a
# ---- `Rat`-list (in)equality on which plain `decide` stalls, so it is closed by
# ---- `simp [NonDetT.run, pure] <;> decide +kernel` (the kernel reducer computes
# ---- the Rat comparison). Checked in a `prove_correct`-stripped file, so no
# ---- tactic script can interfere; both halves seen out-of-band (rival exit 0,
# ---- gold nonzero).
def _witness(args, gold_out):
    return ("extract_program_for chooseLevelArg\n\n"
            f"example : chooseLevelArgExec {args}\n"
            f"    ≠ DivM.res ({gold_out}) := by\n"
            "  unfold chooseLevelArgExec chooseLevelArg\n"
            "  simp [NonDetT.run, pure] <;> decide +kernel\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally DIFFERENT but CORRECT
    # impl: the outer conditions are INVERTED (test `¬levelsKwSet` first, and
    # inside the boolean facet test the line case `¬filled` first). Same literals,
    # same input-value returns, different control-flow shape. Observationally
    # identical on every input (the five cascade clauses partition the same input
    # cube), so all of C1–C5 still hold and the frozen `loom_solve` closes the
    # byte-identical obligation. If it FAILED to verify, the postcondition would be
    # over-fit to one branch nesting => SPEC-TOO-STRONG. Verified out-of-band with
    # a real build.
    # =====================================================================
    {
        "id": "pos-control-inverted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if !levelsKwSet then\n"
            "      if !posGiven then\n"
            "        if boolField then\n"
            "          if !filled then\n"
            "            return (LevelArg.explicit [1/2])\n"
            "          else\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "        else\n"
            "          return (LevelArg.count 7)\n"
            "      else\n"
            "        return posArg\n"
            "    else\n"
            "      return levelsKw"),
        "rationale": "structurally different CORRECT impl: the outer guards are "
                     "inverted (¬levelsKwSet first; the line facet ¬filled first) "
                     "with the SAME literals and input returns. The five clauses "
                     "partition the same input cube, so C1–C5 all still hold on the "
                     "whole domain and the frozen loom_solve closes it. A faithful "
                     "reshape MUST verify, else the postcondition is over-fit to one "
                     "branch nesting => SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — the boolean facet is built through a
    # local `let`-bound if-expression naming the chosen specification, rather than
    # returning the two literals from two branches. A different code shape for the
    # most-pinned (C3/C4) facet; identical values. Keeps the cascade, so the frozen
    # loom_solve closes it. If it FAILED, the spec would be over-fit to the inline
    # two-branch literal form => SPEC-TOO-STRONG. Verified out-of-band with a real
    # build.
    # =====================================================================
    {
        "id": "pos-control-let",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          let lv := if filled then LevelArg.explicit [0, 1/2, 1] "
            "else LevelArg.explicit [1/2]\n"
            "          return lv\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "rationale": "structurally different CORRECT impl: the boolean facet is a "
                     "local let-bound if-expression rather than two literal-return "
                     "branches — a different code shape for the most-pinned C3/C4 "
                     "facet, identical values. C1–C5 still hold, frozen loom_solve "
                     "closes it. Must verify, else the spec is over-fit to the "
                     "inline two-branch literal form => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed from the sibling's precondition-admits probe).
    # This bundle declares NO `require` clause, so "a normal input satisfies the
    # precondition" has no referent — nothing could exclude an F2P-shaped input.
    # The residual admissibility risk on a TOTAL domain is that the post-image is
    # DEGENERATE at the interesting point: three clauses that all pinned the SAME
    # carrier value would read as a spec that discriminates the boolean facets
    # when it does not, and every uniqueness rival above would then be attacking
    # a distinction the carrier collapses. This case discharges an in-region
    # `assert`, at fully concrete inputs, that the three post-images C3/C4/C5 pin
    # are PAIRWISE DISTINCT on this carrier (`LevelArg` derives DecidableEq, and
    # 0/1/2 are dyadic so Rat equality decides). The impl is kept VERBATIM (the
    # frozen body follows the assert), so the method's own obligation still
    # discharges, and the proof block is NOT retuned — the frozen `loom_solve`
    # closes the extra goal too. Checked with real builds: it verifies (exit 0),
    # and the same assert with its FIRST conjunct falsified leaves an unsolved
    # `adm_1` goal (exit 1) under the frozen proof — so the assert is LIVE, not
    # decoration. If it FAILED, the three pinned post-images would not be
    # separable and the uniqueness lane would be attacking nothing.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      ((LevelArg.explicit [0, 1/2, 1] ≠ LevelArg.explicit [1/2]) ∧\n"
            "       (LevelArg.explicit [1/2] ≠ LevelArg.count 7) ∧\n"
            "       (LevelArg.explicit [0, 1/2, 1] ≠ LevelArg.count 7)))\n"
            + _IMPL),
        "rationale": "ADMISSIBILITY on a total domain with no `require` clause: the "
                     "risk is not that the precondition excludes a normal input "
                     "(there is none to exclude) but that the post-image is "
                     "DEGENERATE — that the three values C3/C4/C5 pin coincide on "
                     "this carrier, which would make every uniqueness rival above "
                     "attack a collapsed distinction. The in-region assert "
                     "establishes they are pairwise DISTINCT (explicit [0,1/2,1] ≠ "
                     "explicit [1/2] ≠ count 7), at concrete literals, under the "
                     "FROZEN proof. It is live: falsifying its first conjunct leaves "
                     "an unsolved `adm_1` goal. If it failed => the pinned "
                     "post-images are not separable (PRECOND/POST-DEGENERATE).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec,
    # each attacking one cascade clause, each with a machine-checked refutation
    # witness at a concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve. Each rival keeps the frozen proof (which
    # cannot close the wrong body — the intended rejection); the witness is what
    # attributes the rejection to the spec, not the tactic failure.
    # =====================================================================

    # ---- C1 (explicit-keyword leg): keyword ignored, falls through to the count ----
    {
        "id": "rival-keyword-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # The explicit-keyword branch returns the hard-wired count instead of the
        # supplied keyword value — a plausible reshape bug that drops the keyword
        # leg while adding the boolean leg.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return (LevelArg.count 7)\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "          else\n"
            "            return (LevelArg.explicit [1/2])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "a faithful counterpart of this shape ignores a supplied "
                      "explicit level specification and substitutes the automatic "
                      "count. The failing boolean test never supplies an explicit "
                      "specification, so it would still pass — but the many "
                      "regression tests that DO pass an explicit specification "
                      "(and expect it honored) would break, so this counterpart "
                      "would NOT resolve (a resolved patch keeps those passing).",
        "rationale": "REJECT from C1 (levelsKwSet → out = levelsKw): the rival "
                     "returns count 7 when a keyword spec was supplied, so on any "
                     "supplied value other than count 7 the clause is violated. "
                     "Refuted at levelsKwSet=true, levelsKw=explicit [1/2]: gold "
                     "returns explicit [1/2], the rival count 7. Uniquely varies "
                     "levelsKwSet=true (every other witness holds it false) and "
                     "levelsKw to a non-default value. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(
            "true (LevelArg.explicit [1/2]) false (LevelArg.count 0) false false",
            "LevelArg.explicit [1/2]"),
    },

    # ---- C2 (positional leg): positional argument ignored ----
    {
        "id": "rival-positional-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # The positional branch returns the hard-wired count instead of the
        # supplied positional value.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return (LevelArg.count 7)\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "          else\n"
            "            return (LevelArg.explicit [1/2])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "a faithful counterpart that drops the positional-argument "
                      "leg (substituting the automatic count) would still pass the "
                      "failing boolean test (which passes no positional argument), "
                      "but would break the regression tests that pass a positional "
                      "level argument and expect it honored, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from C2 (¬levelsKwSet ∧ posGiven → out = posArg): the "
                     "rival returns count 7 when a positional spec was supplied, "
                     "violating the clause on any supplied value ≠ count 7. Refuted "
                     "at posGiven=true, posArg=explicit [2, 3]: gold returns "
                     "explicit [2, 3], the rival count 7. Uniquely varies "
                     "posGiven=true and posArg to a non-default value. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.count 0) true (LevelArg.explicit [2, 3]) false false",
            "LevelArg.explicit [2, 3]"),
    },

    # ---- C3/C4 CONFUSION — filled/line swap (ported nagini U1) ----
    {
        "id": "rival-filled-line-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        # Reads `filled` inverted: a filled boolean field gets the single interior
        # position and a line boolean field gets the three bracketing positions.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [1/2])\n"
            "          else\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "its faithful counterpart reads the fill flag inverted: it "
                      "emits the single interior position for a FILLED boolean "
                      "field and the three bracketing positions for a LINE boolean "
                      "field. The failing test asserts the OPPOSITE for both, so "
                      "this counterpart would NOT resolve.",
        "rationale": "REJECT from C3 AND C4 (the two boolean facets): the filled "
                     "facet now emits explicit [1/2] (violates C3, which pins "
                     "explicit [0, 1/2, 1]) and the line facet emits "
                     "explicit [0, 1/2, 1] (violates C4, which pins explicit [1/2]). "
                     "Refuted at boolField=true, filled=true: gold returns "
                     "explicit [0, 1/2, 1], the rival explicit [1/2]. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.count 0) false (LevelArg.count 0) true true",
            "LevelArg.explicit [0, 1/2, 1]"),
    },

    # ---- C3 element pin — filled drops the midpoint (ported nagini U2) ----
    {
        "id": "rival-filled-drop-midpoint",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits only the two extremes [0, 1] for a filled boolean field — a
        # misreading that a filled specification needs only the two bracketing
        # extremes. Correct length family but the interior position is gone.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [0, 1])\n"
            "          else\n"
            "            return (LevelArg.explicit [1/2])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "its faithful counterpart emits only the two bracketing "
                      "extremes (no interior position) for a filled boolean field. "
                      "The failing test asserts the three-position specification "
                      "WITH the interior boundary, so the missing midpoint means it "
                      "would NOT resolve.",
        "rationale": "REJECT from C3 (filled → explicit [0, 1/2, 1]): the rival "
                     "emits explicit [0, 1], dropping the interior 1/2, so the "
                     "element sequence disagrees. Refuted at boolField=true, "
                     "filled=true (filler binders levelsKw=explicit [9], "
                     "posArg=count 3, distinct from the confusion rival's input): "
                     "gold returns explicit [0, 1/2, 1], the rival explicit [0, 1]. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.explicit [9]) false (LevelArg.count 3) true true",
            "LevelArg.explicit [0, 1/2, 1]"),
    },

    # ---- C4 value pin — line uses a boundary value (ported nagini U3) ----
    {
        "id": "rival-line-boundary-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits [0] (a boundary position) for a line boolean field instead of the
        # interior [1/2]. Correct length, wrong value.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "          else\n"
            "            return (LevelArg.explicit [0])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "its faithful counterpart emits a boundary position rather "
                      "than the interior one for a line boolean field. A boundary "
                      "position lies on the edge of the value range, not strictly "
                      "inside it, so the downstream interior filter would drop it "
                      "and leave no boundary line drawn — the failing test asserts "
                      "the single interior position, so it would NOT resolve.",
        "rationale": "REJECT from C4 (line → explicit [1/2]): the rival emits "
                     "explicit [0], the correct length but the wrong (boundary) "
                     "position. Refuted at boolField=true, filled=false: gold "
                     "returns explicit [1/2], the rival explicit [0]. Discriminates "
                     "on the element VALUE (both length 1). If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.count 0) false (LevelArg.count 0) true false",
            "LevelArg.explicit [1/2]"),
    },

    # ---- C3 order pin — filled wrong order (ported nagini U4) ----
    {
        "id": "rival-filled-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits [1, 1/2, 0] — the extremes swapped, a decreasing sequence.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [1, 1/2, 0])\n"
            "          else\n"
            "            return (LevelArg.explicit [1/2])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "its faithful counterpart emits the three positions in "
                      "DECREASING order for a filled boolean field. Downstream "
                      "processing requires increasing positions and would raise or "
                      "reorder/clip, so the resulting specification would not equal "
                      "the ascending three-position one the failing test asserts — "
                      "it would NOT resolve.",
        "rationale": "REJECT from C3 (filled → explicit [0, 1/2, 1]): the rival "
                     "emits explicit [1, 1/2, 0] — correct length and correct "
                     "middle element, but the extremes are swapped (wrong order and "
                     "wrong endpoints). Refuted at boolField=true, filled=true "
                     "(filler binders levelsKw=count 1, posArg=count 2, a distinct "
                     "input point): gold returns explicit [0, 1/2, 1]. Discriminates "
                     "on element ORDER/position. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.count 1) false (LevelArg.count 2) true true",
            "LevelArg.explicit [0, 1/2, 1]"),
    },

    # ---- C4 near-miss — the fill test is dropped inside the boolean facet ----
    {
        "id": "rival-boolfield-ignores-filled",
        "kind": "uniqueness",
        "expect": "reject",
        # A boolean field always gets the three bracketing positions; the fill
        # flag is never consulted. The subtlest near-miss in the C3/C4 family:
        # unlike every rival above it emits the OTHER facet's CORRECT value (not
        # a wrong element, wrong order, or a count), so C3 still holds in full
        # and only C4 is violated. A rival that reads the flag but forgets to
        # branch on it.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          return (LevelArg.explicit [0, 1/2, 1])\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "its faithful counterpart emits the three-position filled "
                      "specification for EVERY boolean field, never consulting "
                      "whether regions are filled. The failing test asserts the "
                      "single interior position for the unfilled boolean case (and "
                      "the three positions for the filled one), so half of its "
                      "assertions still fail and this counterpart would NOT resolve.",
        "rationale": "REJECT from C4 ALONE (¬levelsKwSet ∧ ¬posGiven ∧ boolField ∧ "
                     "¬filled → explicit [1/2]): the rival emits explicit "
                     "[0, 1/2, 1] there. C1, C2, C3 and C5 all still hold, so this "
                     "isolates C4 as an INDEPENDENT clause — no other rival leaves "
                     "the other four intact while breaking it (the confusion rival "
                     "breaks C3 too, the boundary-value rival emits a wrong element, "
                     "prepatch emits the wrong constructor). Refuted at "
                     "boolField=true, filled=false with filler binders "
                     "levelsKw=count 4, posArg=explicit [8] — a ninth input tuple "
                     "distinct from every other witness. Gold returns explicit "
                     "[1/2], the rival explicit [0, 1/2, 1]. If it verified => "
                     "SPEC-TOO-WEAK (C4 would be implied by C3 rather than "
                     "independent).",
        "witness": _witness(
            "false (LevelArg.count 4) false (LevelArg.explicit [8]) true false",
            "LevelArg.explicit [1/2]"),
    },

    # ---- C5 pin — continuous field uses the wrong count ----
    {
        "id": "rival-continuous-wrong-count",
        "kind": "uniqueness",
        "expect": "reject",
        # A non-boolean field returns count 8 instead of the hard-wired count 7.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          if filled then\n"
            "            return (LevelArg.explicit [0, 1/2, 1])\n"
            "          else\n"
            "            return (LevelArg.explicit [1/2])\n"
            "        else\n"
            "          return (LevelArg.count 8)"),
        "refinement": "its faithful counterpart uses a different automatic count "
                      "for a non-boolean field. The many regression tests that "
                      "exercise the ordinary automatic default expect the "
                      "hard-wired count, so a changed count would break them and "
                      "the counterpart would NOT resolve (the change must leave the "
                      "non-boolean default untouched).",
        "rationale": "REJECT from C5 (¬boolField → out = count 7): the rival "
                     "returns count 8. Refuted at boolField=false: gold returns "
                     "count 7, the rival count 8. Uniquely varies boolField=false "
                     "(every C3/C4 rival holds it true), attacking the continuous "
                     "default clause the boolean rivals never reach. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _witness(
            "false (LevelArg.count 0) false (LevelArg.count 0) false false",
            "LevelArg.count 7"),
    },

    # ---- prepatch twin — no boolean special-casing (ported nagini U5) ----
    {
        "id": "rival-prepatch-no-boolfield",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: no special-casing of a boolean field, so a
        # boolean field (absent explicit/positional) always falls to the hard-wired
        # automatic count — exactly the bug the change removes.
        "module": _impl(
            "    if levelsKwSet then\n"
            "      return levelsKw\n"
            "    else\n"
            "      if posGiven then\n"
            "        return posArg\n"
            "      else\n"
            "        if boolField then\n"
            "          return (LevelArg.count 7)\n"
            "        else\n"
            "          return (LevelArg.count 7)"),
        "refinement": "this is the pre-patch behaviour verbatim: a boolean field is "
                      "not special-cased, so it falls through to the hard-wired "
                      "automatic count and gets the ordinary multi-position default "
                      "instead of the single interior position. This is exactly the "
                      "state the failing test observes and the change removes, so "
                      "the unpatched code does NOT resolve (the G-DIFF prepatch "
                      "witness).",
        "rationale": "REJECT from C4 (boolField ∧ ¬filled → explicit [1/2]): the "
                     "rival returns count 7 for a line boolean field, so the "
                     "carrier constructor itself disagrees (count vs explicit). "
                     "Refuted at boolField=true, filled=false (filler binder "
                     "levelsKw=explicit [5], a distinct input point from the "
                     "boundary-value rival): gold returns explicit [1/2], the rival "
                     "count 7. If it verified => SPEC-TOO-WEAK (admits the bug).",
        "witness": _witness(
            "false (LevelArg.explicit [5]) false (LevelArg.count 0) true false",
            "LevelArg.explicit [1/2]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (3 soundness
# positives incl. an honest-echo control, 1 admissibility, 5 uniqueness rivals)
# plus a 2-case AXIOM lane. This velvet bundle models the SAME functional core —
# the level-specification selection — but over a WIDER carrier: the sibling FIXED
# `has_explicit == False` and modeled only the two-valued/continuous split,
# whereas this bundle models the full keyword→positional→boolField→count cascade
# (clauses C1–C5). So the sibling's two-valued rivals port onto C3/C4/C5, and TWO
# NEW rivals (C1, C2) attack the wider surface this bundle models.
#
#   sibling case                  -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-reordered         -> pos-control-inverted          PORTED (re-expressed)
#   pos-control-local             -> pos-control-let               PORTED (re-expressed)
#   echo-honest                   -> (none)                        VACUOUS (no oracle here)
#   admiss-f2p-bool-line          -> admiss-postimage-nondegenerate RE-AIMED (no `require`;
#                                                                   post-image separability instead)
#   rival-filled-line-confusion   -> rival-filled-line-confusion   PORTED
#   rival-filled-drop-midpoint    -> rival-filled-drop-midpoint    PORTED
#   rival-line-boundary-value     -> rival-line-boundary-value     PORTED
#   rival-filled-wrong-order      -> rival-filled-wrong-order      PORTED
#   rival-prepatch-multilevel     -> rival-prepatch-no-boolfield   PORTED
#   (no sibling counterpart)      -> rival-keyword-ignored         NEW (C1, wider carrier)
#   (no sibling counterpart)      -> rival-positional-ignored      NEW (C2, wider carrier)
#   (no sibling counterpart)      -> rival-continuous-wrong-count  NEW (C5 value pin)
#   (no sibling counterpart)      -> rival-boolfield-ignores-filled NEW (C4 in isolation;
#                                                                   added by audit)
#   AXIOM_TESTS ([A1,A2])         -> (none)                        DROPPED (G-AX/G-CONF)
#   frame-mutation                -> (none)                        VACUOUS
#   divergence lane               -> (none)                        VACUOUS (no sibling case; total semantics)
#
# 5 rivals PORTED + 4 NEW rivals (C1/C2/C5 for the wider carrier, plus C4-in-
# isolation added by the audit) + 2 positives ported + 1 re-aimed admissibility
# case = 12 SPEC cases (2 soundness, 1 admissibility, 9 uniqueness).
#
# PORTED (2 positive controls). The sibling's pos-control-reordered reorganises
#   the branch nesting; here the analogue INVERTS the outer guards (¬levelsKwSet
#   first, ¬filled first) with identical literals — a different control shape whose
#   clauses still partition the same input cube, so the frozen loom_solve closes
#   it. The sibling's pos-control-local builds the filled list via local
#   intermediates; here the analogue is a local let-bound if-expression for the
#   C3/C4 facet. Both verified to build.
# PORTED (5 partial-domain rivals). The four two-valued sibling rivals port
#   directly onto the boolean-facet clauses C3/C4 (filled/line confusion, drop the
#   midpoint, line boundary value, filled wrong order); the prepatch rival ports as
#   "no boolean special-casing, fall through to the count". Each carries a
#   machine-checked witness that ELABORATES against its rival and FAILS against the
#   frozen solution (two real builds per case).
# NEW (3 rivals for the wider carrier). rival-keyword-ignored (C1) and
#   rival-positional-ignored (C2) attack the keyword/positional legs of the
#   cascade that the nagini model FIXED away (it set has_explicit=False and never
#   modeled positional args); a rival that broke either leg would still pass the
#   boolean F2P test but regress the P2P tests that supply explicit/positional
#   levels, so a verifying such rival would be a genuine verify-does-not-resolve
#   break — hence these clauses MUST be defended here even though nagini could not.
#   rival-continuous-wrong-count (C5) pins the exact automatic count for a
#   non-boolean field (the sibling pinned this branch to a @Pure oracle, which is
#   not modeled here; the concrete count is directly attackable). These are carrier
#   WIDENING, not fabrication: each attacks a real independent clause of the frozen
#   spec, grounded in a real F2P/P2P behaviour.
# VACUOUS (echo-honest): the sibling's not-two_valued branch was pinned to a @Pure
#   auto_levels ORACLE, and its echo-honest control demonstrated the pin was not
#   echo-vulnerable. Here that branch is the CONCRETE `count 7` (no oracle, empty
#   axioms region), so there is no answer key to echo and no echo-vulnerability
#   class to defend. Its defensive role is covered by the two grounded positive
#   controls and rival-continuous-wrong-count (which pins the count directly).
#   Omitted as a genuine carrier fact, not an effort gap.
# RE-AIMED (admiss-f2p-bool-line -> admiss-postimage-nondegenerate): the sibling
#   self-establishes that its numeric precondition (well-resolved span, linear
#   midpoint pin) admits the F2P-shaped input. This bundle declares NO `require`
#   clause (pre-conditions region empty — every flag combination is admissible), so
#   the sibling's exact probe has no referent. But the CLASS is not vacuous here,
#   and calling it vacuous was wrong: on a total domain the residual admissibility
#   risk is a DEGENERATE post-image — if the three values C3/C4/C5 pin coincided on
#   this carrier, every uniqueness rival would be attacking a collapsed distinction
#   while the battery still reported SOUND. So the case is re-aimed rather than
#   dropped: an in-region `assert`, at concrete literals under the FROZEN proof,
#   that the three pinned post-images are PAIRWISE DISTINCT. Live (falsifying one
#   conjunct leaves an unsolved `adm_1` goal), so it is a real obligation.
# VACUOUS (frame-mutation): the sibling records has_readonly_input == False (every
#   parameter is a by-value scalar; the only Acc is on the owned result). This
#   backend is referentially transparent and declares no `mut` binder, so there is
#   no read-only input to overwrite and no substitute probe. Not fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
# AXIOM_TESTS ([A1,A2]): dropped. The sibling's axiom lane validates the @Pure
#   auto_levels oracle (soundness + containment). This bundle consumes no axiom and
#   declares no deep-model reference (the whole selection is concrete over the
#   inputs; there is no oracle at all — the continuous default is `count 7`), so
#   there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Six input binders (levelsKwSet, levelsKw, posGiven,
#   posArg, boolField, filled) and five independent top-level clauses (C1–C5).
#   Every clause is DEFENDED (both positives establish all five) and ATTACKED:
#     C1 -> rival-keyword-ignored
#     C2 -> rival-positional-ignored
#     C3 -> rival-filled-line-confusion, rival-filled-drop-midpoint,
#           rival-filled-wrong-order
#     C4 -> rival-filled-line-confusion, rival-line-boundary-value,
#           rival-prepatch-no-boolfield, rival-boolfield-ignores-filled
#           (the last breaks C4 ALONE, leaving C1/C2/C3/C5 intact — the only
#            rival that isolates C4 as an independent clause)
#     C5 -> rival-continuous-wrong-count
#   Every binder is VARIED by the reject witnesses:
#     levelsKwSet: true (keyword-ignored) vs false (all others).
#     levelsKw:    explicit [1/2] where it is load-bearing (keyword-ignored,
#                  levelsKwSet=true); also varied as filler (explicit [9],
#                  count 1, explicit [5]) to keep input points distinct.
#     posGiven:    true (positional-ignored) vs false (all others).
#     posArg:      explicit [2, 3] where it is load-bearing (positional-ignored);
#                  also varied as filler (count 3, count 2).
#     boolField:   true (C3/C4 rivals + prepatch) vs false (keyword-ignored,
#                  positional-ignored, continuous-wrong-count).
#     filled:      true (confusion, drop-midpoint, wrong-order) vs false
#                  (boundary-value, prepatch, boolfield-ignores-filled) within
#                  the boolean facet.
#   The nine reject witnesses probe NINE DISTINCT input tuples: no two
#   rivals share an input point (the C3/C4 rivals at the same (boolField,filled)
#   are separated by distinct levelsKw/posArg fillers). Each rival is refuted at
#   the input where its specific wrong behaviour (wrong branch / wrong element /
#   wrong order / wrong count) diverges from gold.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per reject
#   case): each witness ELABORATES against its rival (the extracted program reduces
#   and `simp [NonDetT.run, pure] <;> decide +kernel` proves the ≠ at the probed
#   input) and FAILS against the frozen solution (gold's output equals the RHS, so
#   decide refutes the ≠). Plain `decide` STALLS on the Rat DecidableEq instance
#   (measured — spec_guide's Rat caveat); `decide +kernel` (the trusted kernel
#   reducer, NOT native_decide) computes the Rat comparison. No witness binds a
#   hypothesis (the carrier is transparent), so there is no joint-satisfiability
#   obligation. No sorry/admit/native_decide/axiom appears in any case.
AXIOM_TESTS = []
