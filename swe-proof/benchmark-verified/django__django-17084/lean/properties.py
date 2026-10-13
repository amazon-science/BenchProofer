"""properties.py — G-PBT falsification battery for django__django-17084 (lean lane).

PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
mechanics re-expressed against this backend's carrier. NOT a Lean module — a
manifest the G-PBT runner parses. Each SPEC case is a FULL ``Solution.lean``
variant produced by region surgery, so it shares the FROZEN spec byte-for-byte
(only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a positive that
legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — differs).
``markers.same_spec`` therefore holds by construction, the ``theorem
correct_requiresSubqueryWrap`` STATEMENT stays byte-identical, and every
rejection is attributable to the postcondition rather than to a tampered spec.

DEFENDED SURFACE
----------------
One total function over a fully transparent carrier::

    implementation_requiresSubqueryWrap
        (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool

pinned by the single load-bearing clause

    result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)

`AggregateExpr.refs : List RefAnnotation`, and each `RefAnnotation` carries two
independent booleans (`isSubqueryExpr`, `isWindowExpr`). Both `anyRef*` helpers
are transparent existential folds — `aggs.any (fun a => a.refs.any ...)` — over
the actual input, with NO opaque callee and no answer key. So `decide` computes
the whole clause at any literal input and every witness below is stated at a
concrete input; no conditioning on the carrier is needed anywhere.

The one clause is a THREE-TERM disjunction, and the three terms are separately
attackable because each is grounded in a different part of the input:

  * `otherConditions` — the scalar binder. A rival that drops it is refuted at
    `aggregates = []`, `otherConditions = true`.
  * `anyRefSubquery aggregates` — the pre-existing reference term. A rival that
    drops it is refuted at a reference whose subquery flag alone is set.
  * `anyRefWindow aggregates` — the NEW term, and the discriminating one. A
    rival that drops it, neutralizes it, or mis-quantifies it is refuted at a
    reference whose window flag alone is set.

The clause additionally pins HOW the two reference terms quantify over the
nested list structure: existentially at BOTH levels (some aggregate, some
reference), and ACCUMULATED across the whole outer list rather than only the
last element. Both are independently attacked (`weak-window-all-refs`,
`weak-window-last-aggregate-only`), and both need a MULTI-element input to
expose — which is what moves the list-shaped binder off a single point.

Nagini's oracle-grounding note ports directly: `anyRefWindow` / `anyRefSubquery`
are grounded in the input, not opaque, so there is no wrong value for a rival to
ECHO and the ungrounded-oracle-echo class is N/A. Its place is taken by the
honest cheapest-impl positive (`pos-direct`), exactly as in the sibling.

LANES THAT DO NOT PORT
----------------------
  * FRAME / PERMISSION MUTATION — nagini's mandatory class and its two cases
    (`frame-mut`, `frame-mut-sub`) wrote into inputs held at half permission.
    Lean is referentially transparent: `aggregates` is an immutable value, there
    is no fractional permission to violate and no aliasing to overwrite, so a
    "store into a read-only input" rival is not expressible. The class is
    genuinely VACUOUS here — no substitute is fabricated. Unlike some bundles,
    the frame content does not resurface structurally either: the result is a
    bare `Bool`, so no input component is an observable part of the output.
  * DIVERGENCE / NON-TERMINATION — nagini's `nonterm-diverge` (the hole its
    clause T was added to close). The class is VACUOUS here, and an audit pass
    MEASURED the two ways it could have been mis-disposed rather than asserting
    the structural argument:
      - Splicing nagini's exact shape (`let mut k := 0; while k >= 0 do
        k := k + 1` ahead of the verbatim gold body) VERIFIES, exit 0. That
        looks like the velvet `partial` hole and is NOT: the loop's result is
        unused, and in the `Id` monad the bind is definitional, so the loop is
        ERASED. Measured two ways — `#eval` on that impl returns `false`
        immediately rather than hanging, and `example : ∀ a o, rivalImpl a o =
        implementation_requiresSubqueryWrap a o := fun a o => rfl` closes by
        `rfl` (exit 0). The impl is gold plus dead code, so its verification
        attests nothing about termination in either direction.
      - Making the loop's result LOAD-BEARING (`… && (k == 0)`) is rejected
        (exit 1), and a `partial def` that recurses on itself unconditionally is
        also rejected (exit 1, `rewrite` finds no fold to unfold because the
        `partial` def has no equation).
    So on this carrier a diverging impl either erases to gold or fails to
    verify; there is no rival that both diverges and passes, hence nothing to
    ship and no spec hole. (The velvet sibling of THIS instance is
    `loom.semantics.termination "total"`, not `"partial"`, so
    `the corpus-wide termination-semantics finding` does not apply to it either.)
  * ADMISSIBILITY — see `adm-f2p-window-input` below. The lane is NOT N/A: an
    earlier revision of this file dropped it on the ground that the frozen
    obligation carries no precondition hypothesis, which is precisely the
    reason that does not survive. On a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at an F2P-shaped
    input, and a positive that discharges it at that concrete input by
    evaluation — before closing the frozen obligation verbatim — tests that
    directly. The case is landed and its `have`s are measured load-bearing.
  * AXIOM_TESTS — dropped; the axiom lane is G-AX's job and this gate ignores
    it. (The axioms region is empty here regardless: both flag lookups are
    modeled deeply as boolean fields, so no axiom is consumed.)

WHY SPEC-TOO-WEAK IS UNREACHABLE HERE (and the reject lane still earns its keep)
-------------------------------------------------------------------------------
The postcondition is `result = <total function of the two inputs>`, which pins
`result` UNIQUELY. An audit pass proved that on the frozen file:

    example : ∀ (f g : List AggregateExpr → Bool → Bool),
        (∀ a o, problem_spec_requiresSubqueryWrap a o (f a o)) →
        (∀ a o, problem_spec_requiresSubqueryWrap a o (g a o)) →
        ∀ a o, f a o = g a o            -- elaborates, exit 0

So any two impls satisfying the spec agree everywhere: no wrong impl can verify,
and a spec hole in the too-weak direction is impossible by construction rather
than merely unobserved. Five FURTHER wrong impls beyond the seven below were
built against the frozen spec by that pass and all five were rejected (exit 1):
both accumulators reading the subquery field so the window field is never read;
the window term quantified universally over the OUTER `aggregates` list (the
inner-list analogue of `weak-window-all-refs`, at the one list level no shipped
rival attacks); the window term gated on `aggregates.length == 1`; the two
reference terms combined by XOR rather than OR; and the window flag read only
from each aggregate's HEAD reference. The reject lane's value here is therefore
regression pressure on the impl, not the discovery of a hole.

In the other direction three further CORRECT reshapes were built and all three
verify (exit 0): a `foldl` over `aggregates` with one merged accumulator, a
`flatMap` that flattens both list levels before a single `.any`, and a de Morgan
spelling (`!(… .all (fun r => !r.isWindowExpr))`). Together with the four shipped
positives that is seven independently-shaped correct impls the spec admits, so it
is not over-fit to the frozen form. None of the four shipped positives is a mere
re-spelling: for each, `example : ∀ a o, rivalImpl a o =
implementation_requiresSubqueryWrap a o := fun a o => rfl` FAILS (exit 1), i.e.
every one is a genuinely non-definitional reshape that had to be re-proven.
"""
from pathlib import Path

INSTANCE = "django__django-17084"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region (or, for the two
# proof anchors, entirely inside the proof region) and is unique in the file, so
# every _swap edits only text the spec view elides.
# ---------------------------------------------------------------------------

# impl region ---------------------------------------------------------------
_DECL_DO = ("    (aggregates : List AggregateExpr) (otherConditions : Bool)"
            " : Bool := Id.run do\n")
_DECL_PURE = ("    (aggregates : List AggregateExpr) (otherConditions : Bool)"
              " : Bool :=\n")
_ACC_WINDOW = "    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)\n"
_ACC_SUBQ = "    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)\n"
_RETURN = "  return otherConditions || refsSubquery || refsWindow\n"
_IMPL_BODY = (
    "  let mut refsSubquery := false\n"
    "  let mut refsWindow := false\n"
    "  for agg in aggregates do\n"
    + _ACC_SUBQ
    + _ACC_WINDOW
    + _RETURN
)

# proof region --------------------------------------------------------------
_PROOF_TAIL = (
    "  rw [(key aggregates false false).1, (key aggregates false false).2]\n"
    "  simp [Bool.or_assoc]\n"
)
# The frozen `have key : … := by …` block, verbatim: everything from its opening
# to the closing rewrite. Reused (once field-renamed) by the two positives whose
# loop shape changes, so no NEW lemma is introduced — the same in-proof `have`
# is restated over the reshaped fold.
_KEY_LEMMA = _BASE[_BASE.index("  have key :"):_BASE.index(_PROOF_TAIL)]
for _a in (_DECL_DO, _ACC_WINDOW, _ACC_SUBQ, _RETURN, _IMPL_BODY,
           _PROOF_TAIL, _KEY_LEMMA):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted (count={_BASE.count(_a)}): {_a!r}")


def _swap_flags(text):
    """Exchange the two per-reference flag names throughout `text`.

    Used to restate the frozen in-proof `have key` over a loop whose two
    accumulators were exchanged. Purely a renaming of which fold component is
    which — it introduces no new lemma and no new assumption."""
    return (text.replace("isSubqueryExpr", "\x00")
                .replace("isWindowExpr", "isSubqueryExpr")
                .replace("\x00", "isWindowExpr"))


# The window-only referenced annotation, as a Lean structure literal. Declared
# here because the admissibility positive below needs it; the witness section
# further down re-exports it as `_WIN` alongside its two siblings.
_WIN_F = "{ isSubqueryExpr := false, isWindowExpr := true }"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — a CORRECT impl in a structurally different
# shape must still verify, else the spec is SPEC-TOO-STRONG. Each re-closes the
# obligation honestly: the `theorem correct_requiresSubqueryWrap` statement is
# byte-identical and no axiom / helper lemma / sorry is introduced.
# ===========================================================================

# pos-direct: the honest cheapest impl — return the three-term disjunction
# DIRECTLY, as a pure functional `def` with no do-block, no accumulator and no
# loop. Ports nagini's `pos-direct` including its oracle-grounding argument: the
# two `anyRef*` folds are grounded in the input, so this expression is literally
# the clause's RHS and MUST verify. Proof collapses to `rfl` after unfolding.
_POS_DIRECT = _swap(
    _swap(
        _swap(_BASE, _DECL_DO, _DECL_PURE),
        _IMPL_BODY,
        "  otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates\n",
    ),
    _KEY_LEMMA + _PROOF_TAIL,
    "  unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n"
    "  rfl\n",
)
# The frozen proof opens with `simp only [...]`; the direct impl needs only
# `unfold` + `rfl`, so drop the now-redundant opener too.
_POS_DIRECT = _swap(
    _POS_DIRECT,
    "  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,\n"
    "    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]\n"
    "  unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n",
    "  unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n",
)

# pos-reorder: ports nagini's `pos-reorder`. Both accumulators are DECLARED in
# the opposite order, UPDATED in the opposite order inside the loop, and the
# final disjunction ORs them in the opposite textual order (window before
# subquery). Behaviourally identical on every input — the two accumulations are
# independent and `||` is commutative/associative. The frozen in-proof `have key`
# is reused VERBATIM (the reshaped loop still elaborates to a fold over the same
# two components); only the closing step changes, from the frozen
# `simp [Bool.or_assoc]` to `grind`, because the two accumulators now reach the
# disjunction in the opposite order.
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL_BODY,
        "  let mut refsWindow := false\n"
        "  let mut refsSubquery := false\n"
        "  for agg in aggregates do\n"
        + _ACC_WINDOW
        + _ACC_SUBQ
        + "  return otherConditions || refsWindow || refsSubquery\n",
    ),
    _PROOF_TAIL,
    "  rw [(key aggregates false false).1, (key aggregates false false).2]\n"
    "  grind\n",
)

# pos-merged: a genuinely different ALGORITHM shape for the same decision — one
# single traversal that tests the two per-reference flags TOGETHER
# (`r.isSubqueryExpr || r.isWindowExpr`) instead of maintaining two separate
# accumulators, written as a pure functional `def`. Correct because an
# existential over a disjunction equals the disjunction of the existentials, at
# both list levels. This is the shape most likely to be rejected by a
# postcondition over-fit to the two-accumulator form, so it is the sharpest
# available SPEC-TOO-STRONG probe. Closed with `grind` over the unfolded folds.
_POS_MERGED = _swap(
    _swap(
        _swap(_BASE, _DECL_DO, _DECL_PURE),
        _IMPL_BODY,
        "  otherConditions || aggregates.any (fun a =>\n"
        "    a.refs.any (fun r => r.isSubqueryExpr || r.isWindowExpr))\n",
    ),
    "  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,\n"
    "    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]\n"
    + _KEY_LEMMA + _PROOF_TAIL,
    "  unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n"
    "    anyRefSubquery anyRefWindow\n"
    "  grind [anyRefSubquery, anyRefWindow]\n",
)

# pos-swap-names: ports nagini's `swap-names` (which that sibling also carries
# as expect=verify, after correcting an earlier mislabel). The accumulator NAMED
# `refsSubquery` carries the WINDOW flag and the one named `refsWindow` carries
# the SUBQUERY flag; the returned expression is textually IDENTICAL to gold's.
# The returned VALUE is unchanged — the final `||` is symmetric in the two
# accumulators — so both reference terms still reach the result, just through
# locally-misnamed carriers. Its faithful real correlate is the same
# accumulation with two LOCAL variable names exchanged: identical emitted SQL,
# resolves. A correct impl in this shape MUST verify.
# adm-f2p-window-input: the ADMISSIBILITY positive. The frozen obligation is
# unguarded (`∀ aggregates otherConditions, problem_spec …`), so there is no
# precondition hypothesis to attack directly; the analogue on a total carrier is
# whether the obligation is SATISFIABLE at an F2P-shaped input rather than only
# in the abstract. Three `have`s discharge exactly that, IN-REGION and by
# EVALUATION, at the input the discriminating scenario has the shape of — one
# requested aggregate whose single referenced annotation carries the
# window/over-clause flag and nothing else forcing the wrap:
#   _ground      the spec predicate HOLDS at that concrete input;
#   _forced      the modeled decision EVALUATES to `true` there — this is what
#                stops _ground from being satisfiable-but-vacuous, since the
#                spec pins `result` to a term over the same inputs and would
#                close by evaluation even if the input landed in a no-wrap case;
#   _not_vacuous the clause's RHS is `true` at that input, i.e. the disjunction
#                is genuinely triggered by the window term alone.
# Then the frozen proof closes the obligation VERBATIM, so nothing is assumed
# and the theorem statement stays byte-identical. Measured load-bearing: grafting
# these same `have`s onto the pre-patch rival FAILS (exit 1, `decide` proves both
# _ground and _forced false), so they are not tautologies over the input.
_ADMISS = _swap(
    _BASE,
    "  intro aggregates otherConditions\n",
    "  intro aggregates otherConditions\n"
    "  have _ground : problem_spec_requiresSubqueryWrap\n"
    "      [{ refs := [" + _WIN_F + "] }] false\n"
    "      (implementation_requiresSubqueryWrap\n"
    "        [{ refs := [" + _WIN_F + "] }] false) := by\n"
    "    unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n"
    "    decide\n"
    "  have _forced : implementation_requiresSubqueryWrap\n"
    "      [{ refs := [" + _WIN_F + "] }] false = true := by\n"
    "    unfold implementation_requiresSubqueryWrap\n"
    "    decide\n"
    "  have _not_vacuous : (false || anyRefSubquery\n"
    "      [{ refs := [" + _WIN_F + "] }]\n"
    "      || anyRefWindow\n"
    "      [{ refs := [" + _WIN_F + "] }]) = true := by\n"
    "    decide\n",
)


_POS_SWAP_NAMES = _swap(
    _swap(
        _BASE,
        _IMPL_BODY,
        "  let mut refsSubquery := false\n"
        "  let mut refsWindow := false\n"
        "  for agg in aggregates do\n"
        "    refsSubquery := refsSubquery || agg.refs.any (·.isWindowExpr)\n"
        "    refsWindow   := refsWindow   || agg.refs.any (·.isSubqueryExpr)\n"
        + _RETURN,
    ),
    _KEY_LEMMA + _PROOF_TAIL,
    _swap_flags(_KEY_LEMMA)
    + "  rw [(key aggregates false false).1, (key aggregates false false).2]\n"
    "  grind\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (expect reject) — each shares the frozen spec and edits only
# the impl region. If any VERIFIES the spec admits a wrong impl (SPEC-TOO-WEAK).
# The frozen proof body is left in place: it will not close against a reshaped
# impl, which is exactly why each case must carry a WITNESS. The witness is
# checked in a file with the obligation removed, so no tactic script can
# interfere; it must elaborate against the rival and FAIL on the frozen
# solution.
# ===========================================================================

# weak-drop-window: the PRE-PATCH decision verbatim (Solution_prepatch.lean) —
# the window-reference accumulator is never declared, never updated, and never
# reaches the result.
_RIV_DROP_WINDOW = _swap(
    _BASE, _IMPL_BODY,
    "  let mut refsSubquery := false\n"
    "  for agg in aggregates do\n"
    + _ACC_SUBQ
    + "  return otherConditions || refsSubquery\n",
)

# weak-window-and: the window term is PRESENT in the source text but
# neutralized by an AND against the subquery term — `otherConditions ||
# refsSubquery || (refsSubquery && refsWindow)` is algebraically just
# `otherConditions || refsSubquery`. Ports nagini's `wrong-and`.
_RIV_WINDOW_AND = _swap(
    _BASE, _RETURN,
    "  return otherConditions || refsSubquery || (refsSubquery && refsWindow)\n",
)

# weak-window-all-refs: the window term quantifies UNIVERSALLY over one
# aggregate's references (`.all`) instead of existentially (`.any`), so an
# aggregate that references a window annotation ALONGSIDE a non-window one no
# longer forces the wrap.
_RIV_WINDOW_ALL = _swap(
    _BASE, _ACC_WINDOW,
    "    refsWindow   := refsWindow   || agg.refs.all (·.isWindowExpr)\n",
)

# weak-window-last-aggregate-only: the window flag is ASSIGNED rather than
# OR-accumulated across the outer loop, so only the LAST requested aggregate's
# window references survive. Attacks the accumulation across `aggregates`.
_RIV_WINDOW_LAST = _swap(
    _BASE, _ACC_WINDOW,
    "    refsWindow   := agg.refs.any (·.isWindowExpr)\n",
)

# weak-drop-subquery: the pre-existing subquery-reference term is dropped from
# the decision (the accumulator is still computed, but never ORed in). Attacks
# the term the patch did NOT change, which the frozen spec nevertheless pins.
_RIV_DROP_SUBQ = _swap(
    _BASE, _RETURN, "  return otherConditions || refsWindow\n",
)

# weak-drop-other: the collapsed pre-existing structural conditions are dropped
# from the decision. Attacks the SCALAR binder, which no other rival moves.
_RIV_DROP_OTHER = _swap(
    _BASE, _RETURN, "  return refsSubquery || refsWindow\n",
)

# weak-always-wrap: the constant `true` — always wrap, regardless of every
# input. The maximally coarse over-approximation, and the one a "just be
# conservative" patch would take.
_RIV_ALWAYS = _swap(_BASE, _IMPL_BODY, "  return true\n")


# ---------------------------------------------------------------------------
# Witnesses. Every one states `¬ problem_spec_requiresSubqueryWrap <input>
# (implementation_requiresSubqueryWrap <input>)` at a CONCRETE literal input and
# closes by `decide`: the carrier is fully transparent, so no conditioning on an
# opaque term is needed and there are no hypotheses that could be inconsistent.
# Each was built against the rival (elaborates) and against the frozen solution
# (fails, with `decide` reporting the proposition is false) before shipping.
# ---------------------------------------------------------------------------

_WIN = _WIN_F
_PLAIN = "{ isSubqueryExpr := false, isWindowExpr := false }"
_SUBQ = "{ isSubqueryExpr := true, isWindowExpr := false }"


def _wit(aggregates, other, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_requiresSubqueryWrap\n"
        f"    {aggregates} {other}\n"
        f"    (implementation_requiresSubqueryWrap\n"
        f"      {aggregates} {other}) := by\n"
        f"  unfold problem_spec_requiresSubqueryWrap implementation_requiresSubqueryWrap\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "The honest cheapest CORRECT impl: return the three-term disjunction "
            "directly as a pure functional `def` — no do-block, no accumulator, no "
            "loop. Both reference folds are GROUNDED in the input (transparent "
            "existential folds over `aggregates`), so this expression is literally "
            "the postcondition clause's RHS and MUST verify; the proof collapses to "
            "`unfold` + `rfl`, with the theorem statement byte-identical and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG. Also records why the "
            "ungrounded-oracle-echo class is N/A here: there is no opaque answer key "
            "to echo, so the only echo of the grounded fold is the correct answer, "
            "and any WRONG constant fails the clause (see weak-always-wrap)."
        ),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "A correct impl that declares, updates and returns the two reference "
            "accumulators in the OPPOSITE order (window before subquery throughout). "
            "The two accumulations are independent and the final disjunction is "
            "commutative/associative, so the result is identical on every input; only "
            "the loop's fold shape changes. The frozen in-proof `have key` is restated "
            "over the exchanged fold components (a renaming of which component is "
            "which — NOT a new lemma) and the closing step becomes `grind`; the "
            "obligation statement is byte-identical. If it FAILS => SPEC-TOO-STRONG "
            "(the clause would be over-fit to one accumulation order)."
        ),
    },
    {
        "id": "pos-merged",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MERGED,
        "rationale": (
            "A correct impl in a genuinely different ALGORITHM shape: ONE traversal "
            "testing the two per-reference flags together (`isSubqueryExpr || "
            "isWindowExpr`) instead of two separate accumulators, as a pure functional "
            "`def`. Correct because an existential over a disjunction equals the "
            "disjunction of the existentials at both list levels. This is the shape a "
            "clause over-fit to the two-accumulator form would reject, so it is the "
            "sharpest SPEC-TOO-STRONG probe available on this carrier; closed with "
            "`grind` over the unfolded folds, statement byte-identical, nothing "
            "assumed."
        ),
    },
    {
        "id": "pos-swap-names",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SWAP_NAMES,
        "rationale": (
            "Ports the nagini sibling's `swap-names` (which that battery also carries "
            "as expect=verify): the accumulator NAMED for the subquery term carries the "
            "WINDOW flag and vice versa, while the returned expression is textually "
            "identical to the frozen one. The returned VALUE is unchanged — the final "
            "disjunction is symmetric in the two accumulators — so both reference terms "
            "still reach the result through locally-misnamed carriers. The clause "
            "constrains the RESULT, not variable provenance, so it MUST verify; its "
            "faithful real correlate is the same accumulation with two LOCAL variable "
            "names exchanged, which emits identical SQL and resolves. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---------------- admissibility (must VERIFY) ----------------
    {
        "id": "adm-f2p-window-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The frozen obligation is UNGUARDED — `∀ aggregates otherConditions, "
            "problem_spec …`, no precondition hypothesis — so the nagini sibling's "
            "half-permission `Requires` / `MustTerminate(2)` probe has no binder to "
            "attack. The analogue on a total carrier is whether the obligation is "
            "SATISFIABLE at an F2P-shaped input rather than only in the abstract, and "
            "that is what this case discharges in-region by EVALUATION at the concrete "
            "input the discriminating scenario has the shape of (one requested "
            "aggregate, its single referenced annotation carrying the window/over-clause "
            "flag, nothing else forcing the wrap): `_ground` shows the spec predicate "
            "holds there, `_forced` shows the modeled decision evaluates to `true` there "
            "(without which `_ground` would be satisfiable-but-vacuous, since the clause "
            "pins `result` to a term over the same inputs and closes by evaluation even "
            "on a no-wrap input), and `_not_vacuous` shows the clause's RHS is triggered "
            "by the window term ALONE. The frozen proof then closes the obligation "
            "verbatim: statement byte-identical, no axiom/lemma/sorry. Measured "
            "load-bearing — grafting these `have`s onto the pre-patch rival FAILS, with "
            "`decide` proving both `_ground` and `_forced` false. If it FAILS => "
            "PRECOND-TOO-STRONG (the obligation would be unsatisfiable at exactly the "
            "input that matters)."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "weak-drop-window",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_WINDOW,
        "refinement": (
            "This is the PRE-PATCH decision verbatim: the window-reference term is "
            "never computed and never contributes. Its faithful real counterpart is "
            "the unpatched wrapping decision, which the F2P case rejects: an aggregate "
            "over an annotation built from a window/over-clause expression is left "
            "UNWRAPPED, so the emitted SQL nests the aggregate directly over the "
            "over-clause expression (one SELECT where the test asserts two) and the "
            "backend raises a grouping error rather than returning the expected "
            "aggregate values. It does NOT resolve, so a verifying rival here would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition clause, whose third disjunct "
            "`anyRefWindow aggregates` demands `result = true` on an input where a "
            "referenced annotation carries the window flag while nothing else forces "
            "the wrap; this impl returns false there. Attacks the NEW window term over "
            "the `aggregates` binder. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # one aggregate, one window-only reference, otherConditions false:
        # gold => true, rival => false.
        "witness": _wit(
            "[{ refs := [" + _WIN + "] }]", "false",
            "a window-only reference forces the wrap; the rival never sees it",
        ),
    },
    {
        "id": "weak-window-and",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WINDOW_AND,
        "refinement": (
            "Ports nagini's `wrong-and`. The window term is PRESENT in the source text "
            "but ANDed against the subquery term, making it algebraically a no-op: the "
            "decision reduces to the pre-patch one. Its faithful real counterpart "
            "forces the wrap for a window-referencing aggregate only when that "
            "aggregate ALSO references a subquery annotation. The F2P case references a "
            "window-derived annotation and no subquery annotation, so the aggregation "
            "is left unwrapped and the illegal nesting is emitted exactly as pre-patch. "
            "It does NOT resolve. NOT a distinct sub-domain from weak-drop-window, and "
            "an earlier revision of this file wrongly claimed one: `other || subq || "
            "(subq && win)` is absorption-equal to `other || subq`, so this rival "
            "denotes the SAME FUNCTION as that one on every input. Machine-checked, not "
            "argued — `example : ∀ a o, implA a o = (o || anyRefSubquery a)` was proven "
            "for BOTH rivals (exit 0), so they are extensionally identical. The case is "
            "kept anyway because what it varies is not the input domain but the SOURCE "
            "SHAPE: the window flag is read and accumulated exactly as gold does it and "
            "is textually present in the returned expression, so it survives any review "
            "or mutation check keyed on `isWindowExpr` appearing in the decision. Its "
            "witness is stated at a different input from weak-drop-window's (two "
            "aggregates rather than one, moving the outer list off length 1) so the two "
            "cases are not literally the same build."
        ),
        "rationale": (
            "REJECTED by the same third disjunct, but on the sub-domain the AND leaves "
            "exposed: with the subquery flag FALSE everywhere and the scalar false, "
            "`anyRefWindow aggregates` demands true and the conjunction yields false. "
            "Attacks the window term's INDEPENDENCE from the subquery term. If it "
            "VERIFIES => SPEC-TOO-WEAK (the new disjunct would be hollow)."
        ),
        # two aggregates (the first referencing nothing), the window flag on the
        # SECOND — a different input point from weak-drop-window, and one that
        # also moves the outer list off length 1. gold => true, rival => false.
        "witness": _wit(
            "[{ refs := [] }, { refs := [" + _WIN + "] }]", "false",
            "window term neutralized by the AND: no subquery reference to enable it",
        ),
    },
    {
        "id": "weak-window-all-refs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WINDOW_ALL,
        "refinement": (
            "Quantifies the window test UNIVERSALLY over one aggregate's references "
            "instead of existentially. Its faithful real counterpart replaces the "
            "any-over-references read with an all-over-references read, so an aggregate "
            "that references a window-derived annotation ALONGSIDE any ordinary one is "
            "left unwrapped. That is the shape of the F2P scenario and of realistic "
            "usage generally (an aggregate is routinely requested next to plain "
            "annotations), so the illegal nesting still reaches the backend and it does "
            "NOT resolve. It is also silently correct on every single-reference input, "
            "which is why it needs a multi-reference witness of its own."
        ),
        "rationale": (
            "REJECTED by the third disjunct's EXISTENTIAL quantification over the inner "
            "`refs` list: with one plain and one window reference under a single "
            "aggregate, `anyRefWindow` is true and demands `result = true`, while an "
            "all-quantified test yields false. Attacks the inner-list quantifier of the "
            "`aggregates` binder. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # ONE aggregate with TWO references, plain then window: gold => true,
        # rival (all-quantified) => false.
        "witness": _wit(
            "[{ refs := [" + _PLAIN + ", " + _WIN + "] }]", "false",
            "window reference beside a plain one: existential holds, universal does not",
        ),
    },
    {
        "id": "weak-window-last-aggregate-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WINDOW_LAST,
        "refinement": (
            "ASSIGNS the window flag instead of OR-accumulating it across the outer "
            "loop, so only the LAST requested aggregate's window references survive. "
            "Its faithful real counterpart writes `=` where the accumulation needs "
            "`|=`, a plausible real slip. Whenever more than one aggregate is requested "
            "and the window-derived reference is not under the last of them, the wrap is "
            "skipped and the illegal nesting is emitted. The F2P case requests TWO "
            "aggregates, only one of which references the window-derived annotation, so "
            "it does NOT resolve. Correct on every single-aggregate input, hence its own "
            "multi-aggregate witness."
        ),
        "rationale": (
            "REJECTED by the third disjunct's ACCUMULATION over the outer `aggregates` "
            "list: with a window reference under the FIRST of two aggregates, "
            "`anyRefWindow` is true and demands `result = true`, while a "
            "last-wins assignment yields false. Attacks the outer-list quantifier of "
            "the `aggregates` binder — the one dimension no other rival moves. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # window reference under the FIRST of two aggregates, the second empty:
        # gold => true, rival (last-wins) => false.
        "witness": _wit(
            "[{ refs := [" + _WIN + "] }, { refs := [] }]", "false",
            "window reference under a non-final aggregate: accumulation vs last-wins",
        ),
    },
    {
        "id": "weak-drop-subquery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_SUBQ,
        "refinement": (
            "Drops the PRE-EXISTING subquery-reference term from the decision (it is "
            "still accumulated, but never reaches the result). Its faithful real "
            "counterpart adds the new window disjunct while deleting the subquery one — "
            "a regression a patch author reshaping that condition could plausibly "
            "introduce. It breaks the already-passing case that asserts an aggregate "
            "referencing a subquery-derived annotation is wrapped (a strict SELECT "
            "count), so it does NOT resolve: it fails a PASS_TO_PASS case rather than "
            "the F2P one, which is equally a verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the SECOND disjunct `anyRefSubquery aggregates`, which the "
            "frozen clause pins even though the change did not touch it: on an input "
            "whose only set flag is a reference's subquery flag, the clause demands "
            "`result = true` and this impl returns false. Attacks the subquery term — "
            "the frame the spec deliberately pins rather than leaving unconstrained. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # one aggregate, one subquery-only reference (window flag FALSE — the
        # only witness that sets isSubqueryExpr): gold => true, rival => false.
        "witness": _wit(
            "[{ refs := [" + _SUBQ + "] }]", "false",
            "subquery-only reference: the unchanged term is pinned too",
        ),
    },
    {
        "id": "weak-drop-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_OTHER,
        "refinement": (
            "Drops the collapsed pre-existing structural conditions from the decision, "
            "keeping only the two reference terms. Its faithful real counterpart "
            "rewrites the condition around the new disjunct and loses the structural "
            "ones, so aggregations that must be wrapped for a reason unrelated to "
            "references — a sliced or distinct or combined query, or one that already "
            "aggregates — are no longer wrapped. Several already-passing cases assert "
            "exactly those wraps by SELECT count, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the FIRST disjunct `otherConditions`: with no aggregates at "
            "all and the scalar TRUE, the clause demands `result = true` and this impl "
            "returns false. This is the only rival that moves the SCALAR binder — every "
            "other witness holds it false — so without it a rival mishandling only that "
            "input would verify unnoticed. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # the scalar alone forces the wrap; empty aggregate list.
        # gold => true, rival => false.
        "witness": _wit(
            "[]", "true",
            "the structural conditions alone force the wrap",
        ),
    },
    {
        "id": "weak-always-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS,
        "refinement": (
            "The constant `true`: always wrap. Its faithful real counterpart makes the "
            "wrapping condition unconditional — the maximally conservative "
            "over-approximation, and a tempting one since wrapping is never WRONG for "
            "the returned values. It resolves the F2P case but breaks the "
            "already-passing cases that assert an aggregation needing NO wrap emits a "
            "single SELECT (one asserts exactly `select` count 1), so it does NOT "
            "resolve. This is the direction the other rivals cannot cover: they all "
            "under-wrap, and a spec that pinned only the wrap-forcing direction (an "
            "implication rather than an equality) would admit it."
        ),
        "rationale": (
            "REJECTED by the clause being an EQUALITY rather than a one-sided "
            "implication: on the all-false input (no aggregates, scalar false) the RHS "
            "is false and the clause demands `result = false`, while this impl returns "
            "true. Attacks the completeness direction of the decision over both "
            "binders at once. If it VERIFIES => SPEC-TOO-WEAK (the clause would only "
            "forbid under-wrapping)."
        ),
        # the all-false input: nothing forces a wrap. gold => false, rival => true.
        "witness": _wit(
            "[]", "false",
            "nothing forces the wrap: the clause is an equality, not an implication",
        ),
    },
]


# The axiom lane belongs to G-AX and this gate ignores it. Empty here regardless:
# the axioms region of the frozen solution declares nothing, because both
# per-reference flag lookups are modeled DEEPLY as boolean fields rather than
# axiomatized, so there is no consumed callee property to cross-check.
AXIOM_TESTS = []
