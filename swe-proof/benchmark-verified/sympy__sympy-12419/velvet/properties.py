"""properties.py — G-PBT falsification manifest for sympy__sympy-12419 (velvet).

NOT a Velvet module: a record of adversarial cases the spec-lane gate executes.
A `kind="soundness"`/`"admissibility"` case passes iff it is in scope AND
verifies; a `kind="uniqueness"` case passes iff it is in scope AND does NOT
verify AND its refutation `witness` discriminates (elaborates against the rival,
FAILS against the frozen solution).

This is a PORT of the nagini sibling's battery onto this bundle's carrier. The
adversarial reasoning is carried over; the mechanics are re-expressed, and the
refutation witnesses are new work with no nagini counterpart.

DEFENDED SURFACE (one contracted method, four read-only inputs).

  identityEntry (i j : Idx) (eq : Option Bool) (kd : Option Bool)
      return (out : MatEntry)
      ensures out = entryFor i j eq kd                              -- (C0)
      ensures eq = some true  → out = MatEntry.unit                 -- (C1)
      ensures eq = some false → out = MatEntry.null                 -- (C2)
      ensures eq = none → out = coincideValue i j kd                -- (C3)
      ensures eq = none → kd = some true  → out = MatEntry.unit     -- (C4)
      ensures eq = none → kd = some false → out = MatEntry.null     -- (C5)
      ensures eq = none → kd = none → out = MatEntry.coincide i j   -- (C6)
      ensures eq = none → kd = none → out ≠ MatEntry.null           -- (C7)

There is ONE obligation (`prove_correct identityEntry`) and NO `require` clause:
the admitted domain is total, so every input tuple is legal and the post-image
must hold at each of them. `entryFor` and `coincideValue` are concrete, fully
unfolded `def`s over the method's own arguments — a two-STAGE selection, the
comparison verdict first and the indicator's own verdict second — so (C0) already
implies (C1)-(C7); the seven implications are pinned separately because each
names a sub-domain a rival can get wrong on its own.

TWO VERDICTS, AND WHY THE SECOND IS NOT DECORATION. The element value is selected
in two stages, and the stages have DIFFERENT decision power. The comparison
primitive settles some pairs; the coincidence indicator settles those AND MORE,
because its own rules see facts about the positions that the comparison does not.
So `kd` is an independent input, and the sub-domain `eq = none ∧ kd = some false`
— the comparison declines, the indicator nonetheless settles the pair as distinct
— is REAL, not hypothetical: it is populated in the modeled library, and the
operator there reports the zero. Any spec that answered the whole `eq = none`
sub-domain with an always-unevaluated indicator would predict a value the modeled
operator does not produce there. `weak-ignores-indicator-verdict` below is
exactly that rival, and it is rejected.

The four inputs are FREE. `eq` and `kd` each range over the whole three-valued
verdict (`some true` / `some false` / `none`); `i` and `j` are independent atoms
that the post-image on the doubly-unsettled case must REFER TO, in that order.
Each of those is a distinct thing a rival can abuse, so each is attacked on its
own and the witnesses below move all four off any fixed value.

CARRIER NOTE — FULLY TRANSPARENT, SO EVERY RIVAL IS DECIDABLY REFUTABLE. The
`axioms` region declares nothing at all: `Idx` and `MatEntry` are finite/atomic
inductives with `DecidableEq`, and `entryFor`/`coincideValue` are concrete `def`s.
So there is no `opaque` leaf to get stuck on, no need to condition a witness on
the carrier, and every witness below is stated at fully CONCRETE literal inputs
and closes by `decide`. (Contrast the ports whose spec is stated over an opaque
callee; that constraint simply does not arise here.) A witness reaches the
post-image through Velvet's tester machinery — `identityEntryTester i j eq kd =
false` says the extracted program's result violates the method's contract at that
tuple — checked in a file whose `prove_correct` block has been stripped, so no
tactic script can mask the verdict.

REACHABILITY DISCIPLINE (measured against the modeled library, not assumed).
Of the nine verdict combinations, four carry the modeled operator's behaviour and
one is not populated:

  * `eq = some true`              — settled coincident → the unit;
  * `eq = some false`             — settled distinct   → the zero;
  * `eq = none, kd = none`        — doubly unsettled   → the indicator;
  * `eq = none, kd = some false`  — POPULATED: comparison declines, indicator
                                    settles distinct → the zero;
  * `eq = none, kd = some true`   — NOT populated in the modeled library: nothing
                                    the indicator settles as coincident is left
                                    unsettled by the comparison.

Every reject case below is refuted on a POPULATED combination, so each rejection
rests on a sub-domain whose faithful counterpart is observably wrong against the
real operator. No rival is shipped whose only disagreement with the frozen spec
sits at the unpopulated combination — a rejection there would attest to carrier
strictness rather than to the spec, which is the same audit rule that dropped the
vacuous rivals recorded below.

ADVERSARIAL READ of the nagini classes, and what each becomes here:

  * PREPATCH COLLAPSE (nagini `prepatch-unknown-to-zero`) — PORTED as
    `weak-undetermined-to-null`. The headline rival, and the substance of the
    report: on an unsettled comparison return the zero cell instead of deferring
    to the coincidence indicator. Refuted by (C3)/(C6)/(C7).

  * INDICATOR-VERDICT ERASURE — NEW on this carrier, and the case that makes the
    two-stage selection load-bearing. `weak-ignores-indicator-verdict` answers
    the whole unsettled-comparison sub-domain with the unevaluated indicator,
    never consulting `kd`. That is wrong exactly on the populated
    `eq = none, kd = some false` combination, where the modeled operator reports
    the zero. Refuted by (C3)/(C5).

  * STRUCTURAL-IDENTITY DECISION (nagini `prepatch-via-struct-eq`) — PORTED as
    `weak-decides-on-atoms`, and it ports with MORE bite than on the sibling.
    Nagini expressed it through a one-directional axiom link about a structural
    equality callee; here there is no axiom at all, so the rival simply reads the
    two position atoms directly (`if i = j`) instead of the supplied verdicts.
    That is refutable in BOTH directions — at distinct atoms whose verdict is
    nonetheless definitely-equal, and at equal atoms whose verdict is
    definitely-distinct — and the witness sits at the latter.

  * PARTIAL-DOMAIN / VALUE — APPLIES, three ways: the doubly-unsettled
    sub-domain answered with the unit (`weak-undetermined-to-unit`), the
    definitely-EQUAL sub-domain answered with the zero (`weak-equal-to-null`),
    and the definitely-DISTINCT sub-domain answered with the unit
    (`weak-false-to-unit`). Each names a sub-domain on which the rival's
    faithful counterpart is observably wrong ELEMENT-WISE against the intended
    operator — see the AUDIT note below on why the two decided sub-domains must
    be attacked by a wrong VALUE and not by an unevaluated indicator.

  * MASK SWAP (nagini `mask-swap-equal-unequal`) — PORTED as
    `weak-decided-transposed`: the two decided cells exchanged.

  * FREE-INPUT PRESERVATION / GROUNDING — APPLIES, but ONLY on the second
    operand, and only in the drop direction. Nagini's result was a flat integer
    cell tag, so once the branch was right there was nothing left to get wrong.
    Here the value on the doubly-unsettled case is PARAMETERISED by the two
    position atoms, so a rival can pick the right constructor and still wire the
    operands wrongly — but the two wirings are NOT equally observable. Dropping
    the second operand (`weak-second-operand-dropped`) is observable, because the
    coincidence indicator of a position with ITSELF collapses to the unit, so
    every unsettled cell reads as the unit. EXCHANGING the two operands is
    NOT: the coincidence indicator is symmetric in its two positions and
    canonicalises their order, so the exchanged wiring denotes the SAME library
    value. That is why only the drop rival ships; the exchange rival was dropped
    by audit (see AUDIT below).

  * AUDIT — THREE RIVALS DROPPED AS VACUOUS (this port's own correction). The
    carrier distinguishes `coincide i j` from `coincide j i`, and distinguishes
    `coincide i j` from the unit and the zero at ALL verdicts. The modeled
    library value does NOT make those distinctions everywhere:

      - the coincidence indicator is SYMMETRIC in its two positions (it
        canonicalises their order), so a rival that exchanges the operands
        denotes the same value as the frozen impl at every input;
      - the coincidence indicator SELF-COLLAPSES to the unit on a
        definitely-coincident pair and to the zero on a definitely-distinct
        pair, so a rival that emits the indicator on a DECIDED verdict — either
        on the definitely-equal one, or on both decided ones — also denotes the
        same value as the frozen impl at every input.

    All three were therefore rejected by the frozen spec for a distinction the
    carrier draws and the modeled operator does not: their faithful counterparts
    agree with the intended operator element-wise and RESOLVE the failing test.
    A rejection of a CORRECT rival attests to the carrier's strictness, not to
    the spec, so shipping them would have inflated the battery. Dropped:
    `weak-operands-transposed`, `weak-equal-to-coincide`,
    `weak-constant-coincide`. Replaced by `weak-equal-to-null` and
    `weak-false-to-unit`, which attack the SAME two decided sub-domains with a
    wrong VALUE rather than with an unevaluated indicator, and whose faithful
    counterparts do NOT resolve. This is a carrier-strictness gap, not a spec
    hole: the frozen spec still rejects every rival whose counterpart fails.

  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason as on the sibling but by a
    different mechanism. There is no axiomatised answer key in this bundle: the
    post-image is a concrete function of the method's OWN arguments, so
    `return entryFor i j eq kd` is not an echo of an oracle but the cheapest
    HONEST implementation. It is shipped as a positive control
    (`pos-direct-post-image`) precisely to record that no WRONG echo exists —
    the only way to satisfy the post-image is to perform the two-stage
    selection over the actual operands.

  * FRAME / PERMISSION MUTATION (nagini's read-only-input class) — VACUOUS on
    this backend. That class exists on the sibling because an input may carry a
    fractional heap permission an implementation can write through. This backend
    is referentially transparent: there is no heap, no aliasing, and this method
    declares no `mut` binder, so there is no read-only input to overwrite and no
    substitute probe to fabricate. No case is invented for it.

  * DIVERGENCE / NON-TERMINATION (nagini `nonterm-loop-before-return`,
    `nonterm-self-recursion`) - NOT PORTED, and CLOSED BY THE SEMANTICS rather
    than a spec hole. Line 4 of `Solution.lean` reads
    `set_option loom.semantics.termination "total"` and line 7 reads
    `open TotalCorrectness DemonicChoice`, so the verifier discharges a real
    termination obligation. Re-measured on this carrier with real builds:

      - a self-recursive measure-free pure helper (`partial def`) is REJECTED
        (exit 1, five `unsolved goals` on the `ensures` clauses);
      - an in-`do` `while` prefix with NO `decreasing` clause is REJECTED
        (exit 1, `Decreasing annotations are required in total correctness
        semantics`);
      - and the SHARPER rival, the one that cannot be dismissed as merely
        missing the annotation, CARRIES a measure that does not decrease:
        `while 0 < 1` with `done_with 1 < 0` and `decreasing (0 : Nat)`. It is
        REJECTED TOO, at exit 1, on the MEASURE's own descent goal:
        `unsolved goals case «decreasing_1: (0 : Nat)» ... |- 0 < 0`.

    RETRACTION. An earlier revision of this header recorded that third shape as
    VERIFYING at exit 0 (an unreachable loop exit discharging every `ensures`
    vacuously while the impl returned a flatly wrong `MatEntry.null` /
    `MatEntry.unit`), attributed it to
    `decreasingGadget (measure : Option ℕ) : m PUnit := pure .unit` emitting no
    measure-decrease VC, and escalated it as a spec hole. The build above
    withdraws that: the strict-decrease side condition IS a goal here and the
    constant measure fails it. The mechanism is that BOTH header lines select the
    total scope: `set_option loom.semantics.termination "total"` itself opens
    `TotalCorrectness` (Loom, `MonadAlgebras/WP/Options.lean`, the
    `openScope `TotalCorrectness` arm), line 7 opens it again, and
    `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
    `measure b' < measure b`; only the `PartialCorrectness` twin takes a measure
    and discards it. No spec hole is escalated from this class.

    The class still does not ship as a reject case, now for a WITNESS reason
    rather than a semantic one: a reject case needs a witness that ELABORATES
    against the rival, but a rejected rival's own module does not compile (the
    verdict lands on the `method`, which survives the `prove_correct` strip), and
    for loop-bearing impls the tester additionally does not reduce (measured,
    exit 1 with `did not reduce to isTrue or isFalse`). Either way half 1 is
    unmeetable and the gate would record `witness-unproven`. Reported, not faked.

  * AXIOM LANE (nagini `AXIOM_TESTS`) — dropped; that is G-AX's job and this
    gate ignores it. Note this bundle consumes no axiom at all, so there is no
    axiom-soundness obligation for this gate to probe in the first place.

WITNESS PLACEMENT. The eight reject witnesses sit at EIGHT DISTINCT input
tuples, and between them move every binder of the spec predicate:

  * `eq` takes all three verdicts — `none` (4 witnesses), `some false` (2),
    `some true` (2). No sub-domain of the comparison verdict is left unprobed,
    which is what makes (C1)-(C7) each demonstrated rather than assumed.
  * `kd` is moved off a fixed value too, and critically it takes `some false`
    ALONGSIDE `eq = none` (`weak-ignores-indicator-verdict`), which is the
    populated combination the whole two-stage selection turns on; every other
    witness holds `kd = none`, the doubly-unsettled case.
  * `i` takes 0, 1, 2, 3, 4, 5 and `j` takes 1, 2, 3, 4, 6, 7 — and the pair is
    taken both DISTINCT (six witnesses) and EQUAL (two), so a rival that
    conflated the two atoms cannot slip through on a witness set that only ever
    probed one relation between them.
  * Rivals share no refutation point. `weak-second-operand-dropped` is a
    NEAR-MISS that agrees with the post-image on both decided verdicts and, on
    the doubly-unsettled case, wherever the two atoms coincide — so it is
    refuted at its own distinct-atom tuple (1/6), never at an equal-atom one
    where it would coincide with the frozen behaviour.
  * The two decided sub-domains are each attacked TWICE: once in isolation
    (`weak-equal-to-null` on the definitely-equal side, `weak-false-to-unit` on
    the definitely-distinct side) and once jointly
    (`weak-decided-transposed`), so a clause that carried its sub-domain only in
    combination with the other would be visible.
"""

from pathlib import Path

INSTANCE = "sympy__sympy-12419"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body: one anchor lying wholly inside the impl region and
# ---- unique in the file (both asserted at load by _swap). Every variant
# ---- replaces exactly this block, so the spec view is untouched by
# ---- construction and a rejection is attributable to the contract.
_IMPL_GOLD = """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else
          if kd = some true then MatEntry.unit
          else if kd = some false then MatEntry.null
          else MatEntry.coincide i j
      return e"""

# ---- the frozen proof body. Elided from the spec view, so a positive control
# ---- that reshapes the impl may retune the tactic script; the
# ---- `prove_correct identityEntry` HEADER is preserved in every variant.
_PROOF_GOLD = """prove_correct identityEntry by
  loom_solve
  all_goals simp_all [entryFor, coincideValue]"""

assert _IMPL_GOLD in _BASE, "impl anchor drift"
assert _PROOF_GOLD in _BASE, "proof anchor drift"

# ---- retuned proof for the variants whose branch structure no longer matches
# ---- the frozen script's shape: split BOTH verdicts into their three cases,
# ---- then discharge each against the post-image. Same obligation, same
# ---- strength — nothing is assumed and no lemma is added.
_PROOF_CASES = """prove_correct identityEntry by
  loom_solve
  all_goals rcases eq with _ | b
  all_goals try cases b
  all_goals rcases kd with _ | c
  all_goals try cases c
  all_goals simp_all [entryFor, coincideValue]"""


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so the witness reaches the post-image through Velvet's tester machinery.
# ---- `identityEntryTester i j eq kd = false` states that the extracted
# ---- program's result VIOLATES the contract at that concrete tuple. Both `Idx`
# ---- and `MatEntry` are decidable and both selectors are concrete, so `decide`
# ---- closes without touching anything abstract.
_TESTER = ("extract_program_for identityEntry\n"
           "prove_precondition_decidable_for identityEntry\n"
           "prove_postcondition_decidable_for identityEntry\n"
           "derive_tester_for identityEntry\n\n")


def _witness(i, j, eq, kd):
    """A refutation at one concrete input tuple."""
    return _TESTER + (f"example : identityEntryTester (Idx.mk {i}) (Idx.mk {j})"
                      f" {eq} {kd} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify. A correct reshape that cannot verify
    # means the contract is over-fit to the frozen spelling => SPEC-TOO-STRONG.
    # Each keeps the `prove_correct identityEntry` header; where the reshape
    # moves the branch structure the tactic BODY is retuned to case-split the
    # verdicts (allowed — the body is elided from the spec view — and it neither
    # weakens the obligation nor adds a lemma).
    # =====================================================================
    {
        "id": "pos-undetermined-branch-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the UNSETTLED comparison first (deferring to the
        # indicator's own three-way collapse), the definitely-distinct verdict
        # next, and fall through to the unit on the one remaining outcome.
        "module": _swap(_swap(_BASE, _IMPL_GOLD,
            """    if eq = none then
      let d : MatEntry :=
        if kd = some true then MatEntry.unit
        else if kd = some false then MatEntry.null
        else MatEntry.coincide i j
      return d
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else MatEntry.unit
      return e"""), _PROOF_GOLD, _PROOF_CASES),
        "rationale": "the three comparison cases are answered with the same "
                     "values as the frozen body, in the reverse order, and the "
                     "unsettled one still defers to the indicator's own three-way "
                     "collapse, so `out = entryFor i j eq kd` still holds "
                     "pointwise and (C1)-(C7) with it. Must verify; if it cannot, "
                     "the contract is over-fit to the frozen branch order => "
                     "SPEC-TOO-STRONG. Ports the sibling's branch-reorder control.",
    },
    {
        "id": "pos-single-exit-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: one exhaustive `match` on BOTH verdicts bound to a single
        # local and returned once, instead of nested conditionals.
        "module": _swap(_swap(_BASE, _IMPL_GOLD,
            """    let e : MatEntry :=
      match eq, kd with
      | some true,  _          => MatEntry.unit
      | some false, _          => MatEntry.null
      | none,       some true  => MatEntry.unit
      | none,       some false => MatEntry.null
      | none,       none       => MatEntry.coincide i j
    return e"""), _PROOF_GOLD, _PROOF_CASES),
        "rationale": "same two-stage selection, expressed as one exhaustive match "
                     "over both verdicts with a single exit rather than nested "
                     "conditionals. The returned value is unchanged at every "
                     "input, so the post-image holds. If it fails the contract is "
                     "over-fit to the conditional spelling => SPEC-TOO-STRONG. "
                     "Ports the sibling's single-exit control.",
    },
    {
        "id": "pos-indicator-hoisted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the indicator's value over the two operands BEFORE the
        # comparison branch and name it, rather than inline on the fall-through.
        "module": _swap(_swap(_BASE, _IMPL_GOLD,
            """    let d : MatEntry := coincideValue i j kd
    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else d
      return e"""), _PROOF_GOLD, _PROOF_CASES),
        "rationale": "hoisting the indicator's value into a named local computed "
                     "before the comparison branch leaves the returned value "
                     "unchanged on all verdict combinations, so the post-image is "
                     "unchanged. A correct reshape must verify, else the contract "
                     "is sensitive to where the operands are consumed.",
    },
    {
        "id": "pos-inverted-leading-test",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the leading test and exchange the two arms.
        "module": _swap(_swap(_BASE, _IMPL_GOLD,
            """    if eq ≠ some true then
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else coincideValue i j kd
      return e
    else
      return MatEntry.unit"""), _PROOF_GOLD, _PROOF_CASES),
        "rationale": "negating the leading test and exchanging the arms is "
                     "value-preserving on every verdict combination, so the "
                     "post-image holds. Must verify; a failure would mean the "
                     "contract is over-fit to the polarity of the leading test => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-direct-post-image",
        "kind": "soundness",
        "expect": "verify",
        # The CHEAPEST HONEST implementation, and the no-wrong-echo control.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    let e : MatEntry := entryFor i j eq kd
    return e"""),
        "rationale": "the cheapest honest implementation: the post-image is a "
                     "concrete selection over the method's OWN arguments, so "
                     "returning it directly performs the work rather than echoing "
                     "an oracle (this bundle consumes no axiom, so there is no "
                     "answer key to echo and no wrong echo to build). Must verify; "
                     "this is the port of the sibling's no-wrong-echo control.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is DEGENERATE
    # at the interesting point. This case discharges in-region asserts, at
    # concrete inputs, that the post-image genuinely SEPARATES the
    # doubly-unsettled case from the definitely-distinct one at the same pair of
    # operands, AND separates the two POPULATED sub-cases of an unsettled
    # comparison from each other — the separation the two-stage selection exists
    # to make. The impl is kept verbatim so the method's own obligation still
    # discharges; the asserts are live, not decoration.
    # =====================================================================
    {
        "id": "admiss-undetermined-separates-from-null",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD,
            """    assert (with_name_prefix `admiss
      (entryFor (Idx.mk 0) (Idx.mk 1) none none
        ≠ entryFor (Idx.mk 0) (Idx.mk 1) (some false) none))
    assert (with_name_prefix `admiss2
      (entryFor (Idx.mk 0) (Idx.mk 1) none none
        ≠ entryFor (Idx.mk 0) (Idx.mk 1) none (some false)))
""" + _IMPL_GOLD), _PROOF_GOLD,
            """prove_correct identityEntry by
  loom_solve
  all_goals first
    | decide
    | simp_all [entryFor, coincideValue]"""),
        "rationale": "the domain is total (no `require`), so admissibility reduces "
                     "to the post-image being non-degenerate where it matters. Two "
                     "separations are asserted at one concrete pair of operands: "
                     "the value demanded on the doubly-unsettled case differs from "
                     "the value demanded on a definitely-distinct comparison, AND "
                     "it differs from the value demanded when the comparison is "
                     "unsettled but the indicator settles the pair as distinct. "
                     "The second is the populated sub-domain the two-stage "
                     "selection exists to distinguish, so if it collapsed the "
                     "contract would be degenerate at exactly that point. Both "
                     "asserts must discharge and the impl is verbatim so the "
                     "ensures clauses discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries a machine-checked
    # refutation witness at its OWN concrete input tuple, plus the refinement
    # argument that its faithful counterpart would NOT resolve the failing test
    # or is observably wrong against the modeled operator.
    # =====================================================================
    {
        "id": "weak-undetermined-to-null",
        "kind": "uniqueness",
        "expect": "reject",
        # THE HEADLINE RIVAL — the reported behaviour.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else MatEntry.null
      return e"""),
        "refinement": "this IS the reported defect. A faithful counterpart yields "
                      "the additive zero whenever the comparison of the two "
                      "positions is unsettled, so a symbolic element of the "
                      "operator is the zero: the failing test's assertion that "
                      "such an element is non-zero is FALSE, and the summation "
                      "over the square range adds zeros to zero instead of "
                      "recovering the count of coincident positions. Definitively "
                      "non-resolving.",
        "rationale": "REJECT from (C6) `eq = none → kd = none → out = "
                     "MatEntry.coincide i j` and, redundantly, from (C7) "
                     "`... → out ≠ MatEntry.null`: on the doubly-unsettled case "
                     "the impl returns exactly the value (C7) forbids. Refuted at "
                     "distinct atoms 0/1 with both verdicts unsettled — the "
                     "sub-domain the whole contract is built around.",
        "witness": _witness(0, 1, "none", "none"),
    },
    {
        "id": "weak-ignores-indicator-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SECOND-STAGE RIVAL. On an unsettled comparison return the
        # UNEVALUATED indicator unconditionally, never consulting `kd`. Right on
        # both decided comparisons and right on the doubly-unsettled case; wrong
        # exactly on the populated `eq = none, kd = some false` combination,
        # where the indicator's own rules settle the pair as distinct and the
        # operator reports the zero.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else MatEntry.coincide i j
      return e"""),
        "refinement": "a faithful counterpart hands back an UNEVALUATED "
                      "coincidence indicator on every unsettled comparison, "
                      "including the pairs whose coincidence the indicator's own "
                      "rules DO settle. On such a pair the modeled operator's "
                      "element is the additive zero, and the counterpart instead "
                      "reports a live symbolic object that is not equal to the "
                      "zero — an element-wise disagreement with the intended "
                      "operator on a populated sub-domain, which leaks downstream "
                      "into any summation over that sub-domain. Faithful to the "
                      "comparison verdict alone, but wrong.",
        "rationale": "REJECT from (C3) `eq = none → out = coincideValue i j kd` "
                     "and (C5) `eq = none → kd = some false → out = "
                     "MatEntry.null`: the impl returns the unevaluated indicator "
                     "where the indicator itself collapses to the zero. This is "
                     "the ONLY rival that reads the comparison verdict correctly "
                     "on all three of its cases and still gets the element value "
                     "wrong, so it is what makes the SECOND verdict binder "
                     "load-bearing: without (C3)/(C5) an impl that ignored `kd` "
                     "entirely would satisfy every clause the other witnesses "
                     "probe. Refuted at distinct atoms 0/1 with the comparison "
                     "unsettled and the indicator settling DISTINCT — the one "
                     "witness at that populated combination.",
        "witness": _witness(0, 1, "none", "(some false)"),
    },
    {
        "id": "weak-decides-on-atoms",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the supplied verdicts entirely and decide on the two position
        # atoms, two-valued: equal atoms -> unit, otherwise -> zero.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if i = j then
      return MatEntry.unit
    else
      return MatEntry.null"""),
        "refinement": "a faithful counterpart decides coincidence by structural "
                      "identity of the two positions rather than by the supplied "
                      "verdicts, and so never produces the coincidence indicator "
                      "at all: two structurally distinct symbolic positions fall "
                      "to the additive zero. That is the pre-change behaviour, so "
                      "the failing test's non-zero assertion and its square-range "
                      "summation both still fail. It would NOT resolve.",
        "rationale": "REJECT from the post-image (C0) `out = entryFor i j eq kd`: "
                     "the value must be a function of the two verdicts, and this "
                     "impl ignores both entirely — the ONLY rival that violates "
                     "the whole post-image by never reading a verdict binder at "
                     "all, rather than mis-answering one of its cases. So it is "
                     "wrong wherever the structural relation of the atoms and the "
                     "verdicts disagree — in BOTH directions. Refuted at EQUAL "
                     "atoms 3/3 with a definitely-distinct comparison, where (C2) "
                     "demands the zero and the impl returns the unit; it is "
                     "equally wrong at distinct atoms with an unsettled "
                     "comparison. The only witness holding the two atoms EQUAL "
                     "while the comparison is definitely-distinct.",
        "witness": _witness(3, 3, "(some false)", "none"),
    },
    {
        "id": "weak-undetermined-to-unit",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: right on both decided comparisons, but the unsettled
        # comparison is answered with the UNIT rather than by deferring.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else MatEntry.unit
      return e"""),
        "refinement": "a faithful counterpart treats every unsettled pair as "
                      "coincident, yielding the multiplicative unit. Every "
                      "symbolic element of the operator then reads as the unit, so "
                      "the summation over the square range totals the number of "
                      "CELLS rather than the number of coincident positions "
                      "(nine rather than three at the tested size) — the failing "
                      "test's expected total is not produced. Faithful but "
                      "non-resolving.",
        "rationale": "REJECT from (C6): the doubly-unsettled case demands the "
                     "coincidence indicator over the operands and the impl returns "
                     "the unit. Note (C7) alone does NOT catch this rival — the "
                     "unit is not the zero — so this case is what demonstrates "
                     "(C6) is load-bearing beyond the away-from-zero clause. "
                     "Refuted at distinct atoms 2/7, both verdicts unsettled.",
        "witness": _witness(2, 7, "none", "none"),
    },
    {
        "id": "weak-equal-to-null",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, the definitely-EQUAL side answered with the ZERO.
        #
        # AUDIT NOTE — this case REPLACES a dropped rival that answered the
        # definitely-equal verdict with the coincidence INDICATOR. That rival was
        # vacuous: the indicator self-collapses to the unit on a coincident pair,
        # so its faithful counterpart denoted the frozen value at every input and
        # RESOLVED the failing test.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some false then
      return MatEntry.null
    else
      let e : MatEntry :=
        if eq = some true then MatEntry.null
        else coincideValue i j kd
      return e"""),
        "refinement": "a faithful counterpart yields the additive zero on a "
                      "DEFINITELY-coincident pair of positions, so the coincident "
                      "diagonal of the operator is zero rather than the "
                      "multiplicative unit. The failing test's summation over the "
                      "square range then totals zero instead of the count of "
                      "coincident positions, and the operator disagrees "
                      "element-wise with the intended one on every settled "
                      "coincident cell. Faithful but non-resolving.",
        "rationale": "REJECT from (C1) `eq = some true → out = MatEntry.unit`: on "
                     "the definitely-equal comparison the impl returns the zero. "
                     "Refuted at EQUAL atoms 4/4 with a definitely-equal "
                     "comparison — the only witness at that combination. Unlike "
                     "the indicator-valued rival it replaces, this one is wrong on "
                     "the modeled operator too, so its rejection attests to (C1) "
                     "rather than to a distinction the carrier draws and the "
                     "operator does not.",
        "witness": _witness(4, 4, "(some true)", "none"),
    },
    {
        "id": "weak-false-to-unit",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, the definitely-DISTINCT side answered with the UNIT.
        #
        # AUDIT NOTE — this case REPLACES a dropped rival that returned the
        # coincidence indicator unconditionally (dropping BOTH decided branches).
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.unit
        else coincideValue i j kd
      return e"""),
        "refinement": "a faithful counterpart yields the multiplicative unit on a "
                      "DEFINITELY-distinct pair of positions, so every settled "
                      "off-diagonal cell of the operator is one rather than zero. "
                      "The operator disagrees element-wise with the intended one on "
                      "every such cell and the summation over the square range "
                      "over-counts, so the failing test's expected total is not "
                      "produced. Faithful but non-resolving.",
        "rationale": "REJECT from (C2) `eq = some false → out = MatEntry.null`: on "
                     "the definitely-distinct comparison the impl returns the "
                     "unit. Refuted at distinct atoms 5/6 with a "
                     "definitely-distinct comparison. Together with "
                     "`weak-equal-to-null` this makes BOTH decided sub-domains "
                     "attacked by an observably wrong value; "
                     "`weak-decided-transposed` gets both wrong at once, so these "
                     "two isolate which clause is load-bearing on its own.",
        "witness": _witness(5, 6, "(some false)", "none"),
    },
    {
        "id": "weak-decided-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        # MASK SWAP: the two decided cells exchanged.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.null
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.unit
        else coincideValue i j kd
      return e"""),
        "refinement": "a faithful counterpart exchanges the two settled answers: "
                      "definitely-coincident positions yield the additive zero and "
                      "definitely-distinct ones the multiplicative unit, so the "
                      "operator disagrees element-wise with the intended one on "
                      "EVERY settled cell — the coincident diagonal reads as the "
                      "zero and every decided off-diagonal cell as the unit. "
                      "HONEST SCOPE NOTE, measured rather than asserted: unlike "
                      "the other rivals here, this one is NOT witnessed as "
                      "non-resolving by the failing test. The test only ever "
                      "indexes at two free symbolic positions, whose comparison is "
                      "UNSETTLED, and this rival answers that case correctly — so "
                      "the failing test passes on its counterpart, as do the "
                      "pre-existing assertions. The case still earns its "
                      "rejection from the two decided clauses the frozen contract "
                      "pins independently of the test, and it is kept for that "
                      "reason; what it does not do is argue from the test. This is "
                      "a property of the test, not of this rival: the two decided "
                      "sub-domains are underdetermined BY the failing test, so any "
                      "battery for this cell argues from the intended operator "
                      "there.",
        "rationale": "REJECT from BOTH decided clauses: (C1) demands the unit on "
                     "the definitely-equal comparison and the impl gives the zero; "
                     "(C2) demands the zero on the definitely-distinct comparison "
                     "and the impl gives the unit. Refuted at distinct atoms 0/2 "
                     "with a definitely-equal comparison, where (C1) is violated.",
        "witness": _witness(0, 2, "(some true)", "none"),
    },
    # ---------------------------------------------------------------------
    # DROPPED BY AUDIT — `weak-constant-coincide` (both decided branches
    # dropped, always return the coincidence indicator) and
    # `weak-operands-transposed` (the indicator built over the two operands in
    # the opposite order).
    #
    # Both were VACUOUS: each was rejected by the frozen spec for a distinction
    # the CARRIER draws that the modeled library operator does not.
    #
    #   * the coincidence indicator canonicalises the order of its two
    #     positions, so an exchanged wiring denotes the SAME value;
    #   * the coincidence indicator self-collapses to the unit on a
    #     definitely-coincident pair and to the zero on a definitely-distinct
    #     pair, so emitting it unconditionally denotes the SAME value on both
    #     decided sub-domains as collapsing it by hand does.
    #
    # Verified by executing both counterparts against the real operator: each
    # agrees with the frozen behaviour element-wise on every index-pair shape
    # probed, and each RESOLVES the failing test. Their rejection therefore
    # attested to carrier strictness, not to the spec.
    #
    # NOTE the boundary against `weak-ignores-indicator-verdict`, which DOES
    # ship: that rival is not the "emit the indicator unconditionally" rival. It
    # emits the indicator only on an unsettled COMPARISON, which is precisely
    # where the carrier's `coincide` node and the library's value come apart —
    # the library indicator collapses to the zero on part of that sub-domain
    # (measured), so the rival's counterpart IS observably wrong there. The
    # dropped rivals differed from the frozen behaviour only where the library
    # value coincides with it; this one differs where it does not.
    #
    # The sub-domains the dropped rivals nominally covered are still covered, by
    # rivals whose counterparts are observably wrong: `weak-equal-to-null` and
    # `weak-false-to-unit` (the two decided sub-domains, attacked with a wrong
    # VALUE), and `weak-second-operand-dropped` (the second-operand binder).
    # ---------------------------------------------------------------------
    {
        "id": "weak-second-operand-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # GROUNDING / NEAR-MISS: right constructor and right first operand, but
        # the SECOND operand is never consulted — the first is used twice.
        "module": _swap(_BASE, _IMPL_GOLD,
            """    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else
          if kd = some true then MatEntry.unit
          else if kd = some false then MatEntry.null
          else MatEntry.coincide i i
      return e"""),
        "refinement": "a faithful counterpart builds the coincidence indicator "
                      "from the first position twice, never consulting the second. "
                      "The indicator then always reports a coincidence of a "
                      "position with itself, which collapses to the multiplicative "
                      "unit rather than remaining an unevaluated symbolic object: "
                      "every symbolic element reads as the unit, so the "
                      "square-range summation totals the number of cells (nine at "
                      "the tested size) instead of the count of coincident "
                      "positions (three), and the failing test's expected total is "
                      "not produced. Faithful but non-resolving.",
        "rationale": "REJECT from (C6): the indicator must be built over `i` AND "
                     "`j`, and this impl drops `j` entirely. This is the rival "
                     "that makes the SECOND operand binder load-bearing — without "
                     "it, an impl ignoring `j` would satisfy every clause the "
                     "other witnesses probe. It is the ONE operand-wiring rival "
                     "that survives audit: dropping the operand is observable "
                     "because the indicator of a position with itself collapses to "
                     "the unit, whereas merely EXCHANGING the two operands is not "
                     "(the indicator canonicalises their order), which is why the "
                     "exchange rival was dropped as vacuous. Witness at distinct "
                     "atoms 1/6, both verdicts unsettled — the sub-domain where "
                     "dropping `j` is visible.",
        "witness": _witness(1, 6, "none", "none"),
    },
]
