"""properties.py — G-PBT falsification battery for sympy__sympy-13372 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a three-input domain):

  reduceComponentsToFloat (rePart imPart : EvalfPart) (prec : Nat)
      : Except Unit EvalfTuple
    result = reduceComponentsToFloat rePart imPart prec

  Each of the two input components (real / imaginary) is classified into one of
  three kinds — exactly-zero, concrete-number, or neither — and additionally
  carries a flag for a still-unevaluated marker. The single top-level clause
  ``result = reduceComponentsToFloat rePart imPart prec`` pins the WHOLE
  supported/unsupported decision and the fully-pinned four-tuple:

    * WHETHER the reduction is supported at all: unsupported (``.error ()``)
      exactly when either component carries an unevaluated marker OR either
      component is of the neither-zero-nor-number kind; supported (``.ok``)
      otherwise. This is the load-bearing behavior (the fix): a component of the
      neither kind must make the whole reduction defer, NOT fall through to a
      malformed tuple.
    * The reduced VALUE contributed by each component (``null`` for zero, the
      carried machine-float value for a number).
    * The PRECISION component contributed by each component (``none`` for zero,
      the working precision for a number) — position by position, real from the
      real component and imaginary from the imaginary component.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack meaningful because its modeled inputs are held at
    fractional (read-only) permission. Lean is referentially transparent: the
    three inputs are plain immutable values, there is no half-permission to
    violate and no aliasing to exploit, so this class has NO expressible instance
    here. No substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — EXPRESSIBLE, and measured rather than argued. The
    bundle declares NO ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []) and the machine-float value a number reduces to
    is carried as an ordinary input field, so there is no AXIOMATIZED answer key.
    But the spec IS stated as an equation against a transparent `pure`-region
    reduction, so the cheapest "echo" — an impl whose body is literally
    ``reduceComponentsToFloat rePart imPart prec`` — does exist and DOES verify
    (measured on audit: it fails the frozen tactic, which is tuned to the
    `Id.run do` form, but closes under `unfold problem_spec_…; rfl`). That is not
    a spec hole: the spec's job is to pin the input-output relation, and an impl
    that computes exactly that relation IS correct — the guarantee the gate
    protects is verify ⟹ correct, and the echo is correct. It is recorded here
    because the class is real and the honest analogue is the POSITIVE CONTROLS
    below, whose value is that they are NOT the frozen impl and NOT the spec
    function (both re-measured on audit — see the DEFEQ note there).

  * DEFINEDNESS / FALL-THROUGH (the pre-fix bug), WRONG-PRECISION,
    VALUE-MISLABEL, OVER-DEFER, SWAPPED-COMPONENTS — ALL APPLY. Each attacks the
    one clause on a distinct sub-domain and is refuted with a witness at a
    concrete input.

  * MARKER-GUARD and CARRIED-VALUE — ALL APPLY, and are attacked directly
    (added on audit; see AUDIT below). The unevaluated-marker leg of the support
    decision and the reduced VALUE positions are separately-falsifiable parts of
    the one clause, so each gets its own rival rather than riding on the
    precision rivals.

AUDIT (independent re-derivation, machine-checked). Every reject witness was
rebuilt against its rival (must ELABORATE) and against the frozen solution (must
FAIL), and every gold-side failure was read: all are `unsolved goals ⊢ False` —
`simp` fully reduced both sides, found the spec SATISFIED on gold, and could not
close the negation. That is a semantic refutation, not a missing identifier, a
type error, an unfolding failure, or a timeout. Both positives were rebuilt and
elaborate. The audit also found, and this file now closes, two clauses the
battery ASSERTED it defended while never demonstrating them:

  * the unevaluated-marker leg of the support decision — no original rival
    perturbed that guard and no original witness set the marker at all, so the
    `hasUneval` field never varied at a discriminating point. Closed by
    `weak-ignores-marker` (guard dropped entirely) and `weak-half-marker-guard`
    (the near-miss: guard consults only the real component).
  * the reduced VALUE positions — every original rival altered only a PRECISION
    component or the whole result, so "the carried machine-float value is
    threaded through unchanged, position by position" was never falsified.
    Closed by `weak-constant-value` (a constant replaces the carried value) and
    `weak-swapped-values` (the two value positions crossed).

Also closed: the defer decision was only ever demonstrated on the REAL
component (no original witness put the imaginary component at the neither
kind), so `weak-half-fallthrough` refutes an asymmetric near-miss that keeps the
real chain's final else-branch and drops only the imaginary one.

SECOND AUDIT (independent, machine-checked; the a5 audit's own claims re-derived
rather than accepted). Every case above was rebuilt and every reject witness was
re-derived on BOTH sides, and additionally put through the FORGERY test the a5
record does not contain: for each of the ten reject witnesses, the claim was
FLIPPED (the leading ``¬`` dropped) and the flipped claim built against BOTH the
frozen solution and the rival. All ten flip cleanly — flipped-on-gold ELABORATES
(exit 0) where the unflipped witness failed, and flipped-on-rival FAILS (exit 1,
`unsolved goals ⊢ False`) where the unflipped witness succeeded. So each gold-side
exit code TRACKS THE CLAIM rather than being a constant property of the file, which
is the only thing that makes `unsolved goals ⊢ False` admissible evidence. None of
the ten is hollow.

This audit found and closes ONE real coverage gap, measured by crossing every
existing witness against fresh rivals rather than by reading the prose. The ten
witness points visit only five of the nine kind-pair corners: every one holds at
least one component at exact-zero, so the entire DIAGONAL — both components at the
same non-zero classification — was never visited. Two rivals wrong ONLY there were
therefore refuted by NO witness in the battery (all ten cross-builds exit 1 against
each), i.e. the battery would have recorded them as passing-by-tactic-mismatch:
  * ``weak-both-number-defers`` — correct on every asymmetric input, but defers when
    BOTH components are concrete numbers. The both-number corner is exactly the
    ordinary complex-number case, so this is the narrowest possible over-defer.
  * ``weak-both-symbolic-ok`` — correct whenever exactly one component is the
    neither kind, but reports the both-neither corner as SUPPORTED with a malformed
    tuple. The load-bearing defer decision had only ever been demonstrated with the
    OTHER component reducible, so the corner where both are non-reducible — the
    strongest form of the bug — was undefended.
Both were built as attack-D probes first (each REJECTED by the frozen spec: no spec
hole), then promoted with witnesses that pass both halves AND the forgery test.

Two prose claims above were also corrected against measurement, not argument: the
UNGROUNDED-ORACLE class is EXPRESSIBLE here (see that entry), and the divergence
lane is a known SPEC hole rather than a vacuous class (see DIVERGENCE below).

DIVERGENCE (attack F′). The frozen solution sets NO
``set_option loom.semantics.termination`` — it is vanilla Lean 4 + Mathlib, where a
plain ``def`` must already be seen to terminate by the elaborator and the only way
to write a non-terminating impl is ``partial def``. Measured on audit: a ``partial
def`` self-call passes the mechanical scope check (``variant_problems`` == []) and
does NOT verify, but its rejection is NOT attributable to the spec — ``partial``
makes the impl an OPAQUE constant, so the frozen tactic fails with `Tactic 'unfold'
failed to unfold implementation_reduceComponentsToFloat`, a definitional-opacity
error, not a semantic one. Nor can a witness rescue it: a refutation stated by
HYPOTHESIS at a concrete input (the technique for an opaque carrier) ELABORATES
against the frozen solution too (both sides exit 0), because nothing can derive the
impl's value on either side — so it is a tautology, not a discriminator, and the
gate would record it `witness-vacuous`. Disposition: a KNOWN HOLE in the spec, not
a vacuous class — the spec does not pin termination, and on this carrier no
shippable case can refute a diverging rival. Recorded, not fabricated; no builds
should be spent re-measuring it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival, must ELABORATE) and rebuilt
(against the frozen solution, must FAIL) to confirm it discriminates rather than
asserting a tautology. The spec is fully transparent (no opaque callee), so each
witness unfolds spec + impl and closes with ``simp`` on concrete literals; no
witness binds a hypothesis, so there is no conditioning and nothing for the
consistency probe to reject.

BINDER COVERAGE. All three input binders are varied across the reject witnesses,
and — after the audit — every FIELD of the two component binders varies at a
discriminating point, which is the part a binder count does not show:
  * ``rePart.kind`` — refuted at the neither-kind, at a concrete number, and at
    exact-zero, exercising every classification of the real component.
  * ``imPart.kind`` — refuted at exact-zero, at a concrete number, AND (added on
    audit) at the neither-kind, so the defer decision is demonstrated on BOTH
    components rather than only the real one.
  * the kind PAIR — measured on the second audit, because varying each binder
    separately is not the same as visiting the joint domain: the original ten
    points covered only 5 of the 9 kind-pair corners, all four DIAGONAL corners
    (both components at the same non-zero classification) being unvisited. The
    two both-number and both-neither corners are now refuted by
    ``weak-both-number-defers`` and ``weak-both-symbolic-ok``, so the joint
    domain is defended at 7 of 9 corners. The remaining two (number/neither and
    neither/number) are the MIXED corners: an impl wrong only there is refuted
    by ``weak-half-fallthrough`` / ``weak-fallthrough`` already, since the defer
    decision short-circuits on whichever component is the neither kind
    regardless of the other's classification.
  * ``hasUneval`` — refuted with the marker SET on the real component and,
    separately, on the imaginary component (added on audit; previously this field
    was `false` at every single witness point, so the marker leg of the support
    decision was asserted but never exercised).
  * ``floatVal`` — refuted at a point where the carried value must appear
    unchanged in its own output position (added on audit).
  * ``prec`` — varied across the witnesses (10, 5, 3, 7, 8, 9, 4, 6, 2, 12, 19)
    so the precision component is not pinned to one value.
  ``pts`` = 12 distinct input points.

OMITTED nagini cases (re-derived per case on audit; the nagini sibling has 7
SPEC_TESTS, and all 7 have a counterpart here):
  * ``pos-control-reorder`` -> ``pos-early-defer-flat``. Kept.
  * ``admiss-f2p-shaped`` -> ``admiss-f2p-shaped-ground``. Kept, with the
    technique necessarily changed: nagini's version is a SELF-CALL that must
    discharge the callee's ``Requires`` at a concrete argument, which probes a
    precondition. The frozen theorem here carries no precondition hypothesis (the
    modeled behavior is total over its three inputs), so there is no binder to
    admit and no ``Requires`` to establish; the honest analogue is that the
    obligation be SATISFIABLE at the F2P-shaped inputs, discharged as ground
    ``have``s. The nagini case's own purpose (PRECOND-TOO-STRONG) is
    inexpressible for the reason that it cannot arise, not because it is hard.
  * ``prepatch-fallthrough`` -> ``weak-fallthrough``. Kept.
  * ``wrong-precision`` -> ``weak-wrong-precision``. Kept.
  * ``numeric-as-absent`` -> ``weak-numeric-as-absent``. Kept.
  * ``over-defer`` -> ``weak-over-defer``. Kept. Note the nagini rival is
    discriminated by an ``Exsures`` clause (deferral is an exceptional
    control-flow effect there); here it is the same distinction reified as the
    ``.error ()`` vs ``.ok`` branch of the result type, so no clause is lost.
  * ``swapped-components`` -> ``weak-swapped-precisions``. Kept.
Two nagini COVERAGE DECISIONS, not cases, are also carried over and both hold on
this carrier for the reasons given above: FRAME-MUTATION (nagini records it N/A
for itself — its three params are value types with no read-only ``Acc``, so there
is nothing to omit) and the empty AXIOM lane (no axiom / deep-model reference;
G-AX skips, and the axiom lane is not this gate's job). Re-derived on the second
audit against the nagini artifact rather than its prose: ``model.py`` declares
``Requires(0 <= re_kind and re_kind <= 2)`` on both kind params — an integer-range
guard — which is what makes nagini's ``admiss-f2p-shaped`` a genuine precondition
probe. The frozen Lean statement is a bare ``∀`` over three inputs with NO
hypothesis, because the trichotomy is carried by the inductive ``EvalfPartKind``
(total by construction) instead of by a range predicate. So PRECOND-TOO-STRONG is
unreachable here because the carrier makes the domain total, not because a proof
was hard — and the admissibility lane is kept, in the only form it can take, as
``admiss-f2p-shaped-ground``. Its two ground ``have``s were checked to have TEETH
rather than being decoration: grafting that same proof region onto the pre-fix impl
makes the defer ``have`` itself fail (`unsolved goals ⊢ False` at the ``have``,
before the frozen obligation is reached), and grafting it onto the unconditional-
defer impl makes the supported-shape ``have`` fail the same way. Neither ground
instance is provable of a wrong impl, so both are real instances of the F2P shapes.

Nagini carries no divergence/non-termination case either, so nothing was dropped
there; the class is nonetheless assessed independently under DIVERGENCE above,
where it is recorded as a known SPEC hole with the measurement that supports it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13372"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

_PROOF_BODY = (
    "  intro rePart imPart prec\n"
    "  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat\n"
    "    reduceComponentsToFloat\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases huneval : rePart.hasUneval || imPart.hasUneval\n"
    "  · simp only [huneval, if_true]\n"
    "  · simp only [huneval]\n"
    "    rcases hre : rePart.kind with _ | _ | _ <;>\n"
    "      rcases him : imPart.kind with _ | _ | _ <;>\n"
    "      simp [evalfPartOut, evalfPartPrec, hre, him]"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PREPATCH (the pre-fix bug): the two classification chains have NO final
# else-branch, so a component of the neither-zero-nor-number kind falls through
# with its output value / precision left at their unassigned defaults, and the
# four-tuple is still assembled and reported as supported.
_PREPATCH_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# WRONG PRECISION: correct on the zero and neither cases, but on the concrete-
# number case attaches the wrong precision component (prec + 1 instead of prec).
_WRONGPREC_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some (prec + 1)\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some (prec + 1)\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# VALUE-MISLABEL (numeric-as-absent): treats a concrete number like an exact
# zero — no precision component for the number case (none instead of some prec).
_NUMABSENT_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := none\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := none\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# OVER-DEFER: always reports unsupported, even when both components are
# reducible. Deferring is a control-flow effect the spec licenses ONLY when some
# component is the neither kind (or carries an unevaluated marker).
_OVERDEFER_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  return .error ()"
)

# SWAPPED COMPONENTS: assigns the real precision from the imaginary computation
# and vice versa (the last tuple field order is crossed). Identical when the two
# components share a kind; diverges whenever they are classified differently.
_SWAP_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, imprec, reprec)"
)

# ---- rivals added on audit (each built, and each witness re-derived) --------

# IGNORES THE MARKER: drops the unevaluated-marker guard entirely, so a
# component carrying an unevaluated marker is reduced as if it were an ordinary
# zero/number instead of making the whole reduction unsupported. Attacks the leg
# of the support decision that no other rival perturbs.
_NOUNEVAL_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# HALF MARKER-GUARD (near-miss): the marker guard consults only the REAL
# component, so an unevaluated marker on the imaginary component alone is
# missed. Identical to gold except on that one sub-domain.
_HALFUNEVAL_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# CONSTANT VALUE: the precision components are right and the support decision is
# right, but a concrete number's reduced VALUE is a constant instead of the
# machine-float value carried on the input. Attacks the value positions, which
# the precision rivals leave untouched.
_CONSTVAL_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num 0\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num 0\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# SWAPPED VALUES: crosses the two reduced VALUE positions (the mirror of the
# swapped-precision rival, on the other pair of tuple fields).
_SWAPVAL_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (imOut, reOut, reprec, imprec)"
)

# HALF FALL-THROUGH (asymmetric near-miss): keeps the real chain's final
# else-branch and drops ONLY the imaginary one, so the reduction defers on a
# neither-kind real component but falls through on a neither-kind imaginary one.
# Strictly closer to gold than the full pre-fix shape, and demonstrates the defer
# decision on the imaginary side.
_HALFFALL_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# ---- rivals added on the SECOND audit (the unvisited DIAGONAL corners) -----
# Each of these is wrong ONLY where both components share a non-zero
# classification. Every pre-existing witness holds at least one component at
# exact-zero, so each of the ten was cross-built against these two rivals and
# ALL TWENTY builds failed: neither rival was refuted by anything the battery
# already carried.

# BOTH-NUMBER OVER-DEFER (narrowest over-defer): every component is classified
# and reduced exactly as gold does, and the support decision is right on every
# ASYMMETRIC input — but when both components are concrete numbers the reduction
# is reported unsupported anyway. The both-number corner is the ordinary case of
# a value with a real AND an imaginary part, so this defers precisely where the
# reduction is most obviously licensed.
_BOTHNUM_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  if rePart.kind = .number && imPart.kind = .number then\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# BOTH-NEITHER FALL-THROUGH (the strongest form of the defer bug, and the last
# undefended corner of the support decision): both classification chains keep
# their final else-branch, so a SINGLE non-reducible component still makes the
# reduction unsupported — but the corner where BOTH components are of the
# neither kind is short-circuited to a supported, malformed tuple before either
# chain runs. Every earlier defer witness holds the other component reducible,
# so this corner was asserted and never demonstrated.
_BOTHSYM_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  if rePart.kind = .symbolic && imPart.kind = .symbolic then\n"
    "    return .ok (.sym, .sym, none, none)\n"
    "  let mut reOut : EvalfPartOut := .sym\n"
    "  let mut reprec : Option Nat := none\n"
    "  if rePart.kind = .zero then\n"
    "    reOut := .null\n"
    "    reprec := none\n"
    "  else if rePart.kind = .number then\n"
    "    reOut := .num rePart.floatVal\n"
    "    reprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  let mut imOut : EvalfPartOut := .sym\n"
    "  let mut imprec : Option Nat := none\n"
    "  if imPart.kind = .zero then\n"
    "    imOut := .null\n"
    "    imprec := none\n"
    "  else if imPart.kind = .number then\n"
    "    imOut := .num imPart.floatVal\n"
    "    imprec := some prec\n"
    "  else\n"
    "    return .error ()\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)


# SECOND POSITIVE CONTROL (soundness, added on audit): a correct reshape that
# abandons the two sequential `let mut` chains for a single simultaneous `match`
# on the PAIR of kinds, returning each fully-assembled tuple as a literal. The
# support decision and all four positions are the same function of the inputs;
# only the shape differs. The frozen tactic closes it verbatim.
_POS2_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  match rePart.kind, imPart.kind with\n"
    "  | .zero, .zero => return .ok (.null, .null, none, none)\n"
    "  | .zero, .number => return .ok (.null, .num imPart.floatVal, none, some prec)\n"
    "  | .number, .zero => return .ok (.num rePart.floatVal, .null, some prec, none)\n"
    "  | .number, .number =>\n"
    "    return .ok (.num rePart.floatVal, .num imPart.floatVal, some prec, some prec)\n"
    "  | _, _ => return .error ()"
)


# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl —
# defer FIRST on the neither kind, then a flat `let`-based two-way assignment for
# the reducible cases. Same observable behavior as gold; only the executable
# shape differs. The frozen tactic (case analysis on the kinds, not on syntactic
# form) closes it verbatim, so the theorem STATEMENT and proof body are unchanged
# — no new declaration, axiom, or assumption token.
_POS_IMPL = (
    "def implementation_reduceComponentsToFloat\n"
    "    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do\n"
    "  if rePart.hasUneval || imPart.hasUneval then\n"
    "    return .error ()\n"
    "  if rePart.kind = .symbolic then\n"
    "    return .error ()\n"
    "  if imPart.kind = .symbolic then\n"
    "    return .error ()\n"
    "  let reOut : EvalfPartOut := if rePart.kind = .zero then .null else .num rePart.floatVal\n"
    "  let reprec : Option Nat := if rePart.kind = .zero then none else some prec\n"
    "  let imOut : EvalfPartOut := if imPart.kind = .zero then .null else .num imPart.floatVal\n"
    "  let imprec : Option Nat := if imPart.kind = .zero then none else some prec\n"
    "  return .ok (reOut, imOut, reprec, imprec)"
)

# ADMISSIBILITY: the frozen impl + proof, with two ground instances discharged
# BEFORE the frozen obligation — one at the F2P-shaped defer input (a neither-
# kind component must make the reduction unsupported) and one at a representable
# input (a concrete-number real part with an exact-zero imaginary part yields the
# well-formed supported tuple) — proving the modeled behavior is satisfiable at
# exactly the shapes the F2P exercises. Nothing is assumed: the theorem STATEMENT
# is byte-identical, the ground instances are `have`s inside the existing tactic
# body, and no new declaration/axiom/`sorry` is introduced.
_ADM_PROOF = (
    "  have _ground_defer : problem_spec_reduceComponentsToFloat\n"
    "      { kind := .symbolic, floatVal := 0, hasUneval := false }\n"
    "      { kind := .zero, floatVal := 0, hasUneval := false } 53\n"
    "      (implementation_reduceComponentsToFloat\n"
    "        { kind := .symbolic, floatVal := 0, hasUneval := false }\n"
    "        { kind := .zero, floatVal := 0, hasUneval := false } 53) := by\n"
    "    unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat\n"
    "      reduceComponentsToFloat\n"
    "    simp [Id.run, bind, pure]\n"
    "  have _ground_ok : problem_spec_reduceComponentsToFloat\n"
    "      { kind := .number, floatVal := 42, hasUneval := false }\n"
    "      { kind := .zero, floatVal := 0, hasUneval := false } 53\n"
    "      (implementation_reduceComponentsToFloat\n"
    "        { kind := .number, floatVal := 42, hasUneval := false }\n"
    "        { kind := .zero, floatVal := 0, hasUneval := false } 53) := by\n"
    "    unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat\n"
    "      reduceComponentsToFloat\n"
    "    simp [Id.run, bind, pure, evalfPartOut, evalfPartPrec]\n"
    + _PROOF_BODY
)


# ---- witnesses ------------------------------------------------------------
# The spec is fully transparent, so each witness unfolds spec + impl and closes
# on concrete literals. No head binder, so no conditioning and no consistency
# probe. `_part` builds a component literal; `_witness` the full example.
def _part(kind, fv, un):
    return (f"{{ kind := .{kind}, floatVal := {fv}, hasUneval := {un} }}")


def _witness(re_part, im_part, prec):
    return (
        f"example : ¬ problem_spec_reduceComponentsToFloat\n"
        f"    {re_part}\n"
        f"    {im_part} {prec}\n"
        f"    (implementation_reduceComponentsToFloat\n"
        f"      {re_part}\n"
        f"      {im_part} {prec}) := by\n"
        f"  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat\n"
        f"    reduceComponentsToFloat\n"
        f"  simp [Id.run, bind, pure, evalfPartOut, evalfPartPrec]"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify; else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-early-defer-flat",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_IMPL),
        "rationale": (
            "a correct reshape — defer FIRST on the neither-kind component, then "
            "a flat `let`-based assignment for the reducible cases — must satisfy "
            "`result = reduceComponentsToFloat rePart imPart prec`; if it cannot, "
            "the spec is SPEC-TOO-STRONG. The frozen tactic does case analysis on "
            "the component kinds (not on the impl's syntactic form), so it closes "
            "the reshaped impl verbatim — the theorem STATEMENT and proof body are "
            "unchanged and no new declaration/axiom/assumption token is added. "
            "NOT trivially the frozen impl and not definitionally equal to it: "
            "measured on the second audit by appending a renamed copy of the "
            "frozen impl and asking `rfl` whether the two agree — it FAILS "
            "(`is not definitionally equal to`), while the same probe run on the "
            "frozen impl against its own copy succeeds, so the frozen tactic's "
            "case analysis is doing real work here rather than closing a defeq."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the
    # F2P-shaped inputs. The frozen theorem carries NO precondition hypothesis
    # (the behavior is total), so nagini's precondition-admission probe has no
    # binder to attack; the honest analogue discharges the spec predicate at the
    # F2P ground inputs (a defer shape AND a supported shape) inside the proof
    # region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADM_PROOF),
        "rationale": (
            "the obligation is discharged at two F2P ground inputs — a neither-"
            "kind real component (the reduction must be reported unsupported, the "
            "F2P observable) and a concrete-number real part with an exact-zero "
            "imaginary part (the well-formed supported tuple) — by `simp` over the "
            "reduced `Id.run`, then the frozen obligation is closed verbatim. "
            "Verifies (else the spec is unsatisfiable at the normal input, the "
            "analogue of PRECOND-TOO-STRONG). Nothing is assumed: the theorem "
            "STATEMENT is byte-identical, the ground instances are `have`s inside "
            "the existing tactic body, and no new declaration/axiom/`sorry` is "
            "introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_IMPL),
        "refinement": (
            "this is the pre-fix behavior: the classification chains have no final "
            "else-branch, so a component that is neither exactly zero nor a "
            "concrete number falls through with its output value / precision at "
            "the unassigned defaults and the four-tuple is still assembled and "
            "reported as supported. On the issue's own reproducer — a real part of "
            "the neither kind — it produces a malformed result instead of "
            "reporting the reduction unsupported so the caller can fall back, "
            "which is precisely the crash the F2P test guards. It does NOT resolve "
            "— this is the literal pre-patch."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: at a neither-kind real component the spec demands the "
            "unsupported `.error ()`, but the rival assembles a `.ok` tuple with a "
            "malformed real value. Refuted on the neither-kind sub-domain — the "
            "direct attack on the support decision (the fix). If it verifies, the "
            "spec does not force deferral on a non-reducible component "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("symbolic", 0, "false"),
                            _part("zero", 0, "false"), 10),
    },
    {
        "id": "weak-wrong-precision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONGPREC_IMPL),
        "refinement": (
            "a real patch attaching the wrong precision (`prec + 1`) to every "
            "concrete-number component would corrupt the working precision fed to "
            "the downstream numeric evaluation of every concrete number, so the "
            "numeric evaluation tests would fail — it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: on a concrete-number component the spec pins the "
            "precision component to exactly the working precision (`some prec`), "
            "but the rival yields `some (prec + 1)`. Refuted at a concrete-number "
            "real part (`prec = 10`). If it verifies, the precision component is "
            "left unpinned on the number sub-domain (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("number", 7, "false"),
                            _part("zero", 0, "false"), 10),
    },
    {
        "id": "weak-numeric-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NUMABSENT_IMPL),
        "refinement": (
            "a real patch leaving no precision component for a concrete number "
            "(the absent/`none` marker that denotes an exact zero) would mark "
            "every concrete number as an exact zero downstream, so the numeric "
            "evaluation of real numbers would collapse to zero — every numeric "
            "evaluation test would fail; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: on a concrete-number component the spec pins the "
            "precision component to `some prec`, but the rival yields `none`. "
            "Refuted at a concrete-number IMAGINARY part (varying the `imPart` "
            "binder to the number kind, `prec = 5`). If it verifies, the number "
            "case is not distinguished from the exact-zero case (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("zero", 0, "false"),
                            _part("number", 4, "false"), 5),
    },
    {
        "id": "weak-over-defer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVERDEFER_IMPL),
        "refinement": (
            "a real patch reporting the reduction unsupported for EVERY input "
            "would make the numeric evaluation defer on every expression — no "
            "number is ever evaluated; essentially every numeric evaluation test "
            "(and the F2P) would fail; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: when both components are reducible (here both exactly "
            "zero) the spec demands the supported `.ok` tuple, but the rival "
            "returns `.error ()`. Refuted where both components are reducible "
            "(`prec = 3`) — the sub-domain the support decision must accept. If it "
            "verifies, the spec does not force a supported result on reducible "
            "inputs (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("zero", 0, "false"),
                            _part("zero", 0, "false"), 3),
    },
    {
        "id": "weak-swapped-precisions",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP_IMPL),
        "refinement": (
            "a real patch crossing the real and imaginary precision components in "
            "the assembled tuple would attach the imaginary component's precision "
            "to the real position (and vice versa) — wrong on every expression "
            "whose real and imaginary parts are classified differently; it would "
            "not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec pins the real precision from the real "
            "component (`some prec` for a number) and the imaginary precision from "
            "the imaginary component (`none` for zero), but the rival crosses "
            "them. Refuted at an asymmetric input — concrete-number real part, "
            "exact-zero imaginary part (`prec = 7`) — where the two positions "
            "differ. If it verifies, the spec does not tie each precision "
            "component to its own side (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("number", 9, "false"),
                            _part("zero", 0, "false"), 7),
    },

    # =====================================================================
    # ADDED ON AUDIT — the clauses the battery above asserted it defended but
    # never demonstrated: the unevaluated-marker leg of the support decision,
    # the reduced VALUE positions, and the defer decision on the IMAGINARY
    # component. Each witness was built against its rival (elaborates) and
    # against the frozen solution (fails with `unsolved goals ⊢ False`, i.e. a
    # semantic refutation).
    # =====================================================================
    {
        "id": "weak-ignores-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOUNEVAL_IMPL),
        "refinement": (
            "a real patch dropping the unevaluated-marker check would reduce a "
            "component that still carries an unevaluated symbolic marker as "
            "though it were an ordinary zero or concrete number, feeding a "
            "not-yet-evaluated quantity into the downstream numeric evaluation "
            "instead of reporting the reduction unsupported so the caller can "
            "fall back — it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec makes the reduction unsupported whenever "
            "EITHER component carries an unevaluated marker, but the rival "
            "reduces it anyway. Refuted at an exact-zero real component whose "
            "marker is SET (`prec = 8`) — a point where the kinds alone would "
            "license a supported result, so only the marker leg can reject it. "
            "If it verifies, the marker leg of the support decision is unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("zero", 0, "true"),
                            _part("zero", 0, "false"), 8),
    },
    {
        "id": "weak-half-marker-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HALFUNEVAL_IMPL),
        "refinement": (
            "a real patch testing the marker on only the real component would "
            "miss an unevaluated marker carried by the imaginary component "
            "alone, so that quantity would flow into the downstream numeric "
            "evaluation unevaluated — wrong on exactly the expressions whose "
            "imaginary part is the unevaluated one; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the marker test is over BOTH components, but the "
            "rival consults only the real one. Refuted at the asymmetric point "
            "the near-miss survives — marker CLEAR on the real component, SET on "
            "the imaginary one (`prec = 4`), varying the `imPart` marker field. "
            "If it verifies, the spec does not require the marker test to cover "
            "the imaginary component (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("zero", 0, "false"),
                            _part("zero", 0, "true"), 4),
    },
    {
        "id": "weak-constant-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CONSTVAL_IMPL),
        "refinement": (
            "a real patch emitting a fixed value for every concrete number "
            "instead of the machine-float value that number reduces to would "
            "replace every evaluated number by that constant, so every numeric "
            "evaluation test would fail; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: on a concrete-number component the spec pins the "
            "reduced value to the machine-float value carried on THAT input "
            "(`.num p.floatVal`), but the rival emits a constant. Refuted at a "
            "concrete-number real component whose carried value is non-zero "
            "(`floatVal = 5`, `prec = 9`), which is what makes the constant "
            "observably different. If it verifies, the value positions are "
            "unpinned and the carried payload need not be threaded through "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("number", 5, "false"),
                            _part("zero", 0, "false"), 9),
    },
    {
        "id": "weak-swapped-values",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAPVAL_IMPL),
        "refinement": (
            "a real patch crossing the two reduced VALUE positions would report "
            "each component's value in the other's slot, so the real and "
            "imaginary results of every expression whose two components reduce "
            "differently would be exchanged; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec pins the real VALUE position from the real "
            "component and the imaginary one from the imaginary component, but "
            "the rival crosses them. Refuted at an asymmetric input — "
            "concrete-number real part, exact-zero imaginary part (`prec = 6`) — "
            "where the two value positions differ. The mirror of the "
            "swapped-precision case on the other pair of fields: if it verifies, "
            "the spec ties the precisions to their own side but not the values "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("number", 9, "false"),
                            _part("zero", 0, "false"), 6),
    },
    {
        "id": "weak-half-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HALFFALL_IMPL),
        "refinement": (
            "a real patch that guarded only the real component's classification "
            "chain and left the imaginary one falling through is a partial fix: "
            "the issue's own reproducer defers, but an expression whose "
            "IMAGINARY component is the non-reducible one still assembles a "
            "malformed result around a value that was never computed, so the "
            "same failure remains reachable — it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec makes the reduction unsupported when EITHER "
            "component is of the neither kind, but the rival defers only on the "
            "real one. Refuted at the point the partial fix misses — exact-zero "
            "real component, neither-kind IMAGINARY component (`prec = 2`) — "
            "which is the only sub-domain separating this rival from gold. If it "
            "verifies, the spec forces deferral on the real component only "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("zero", 0, "false"),
                            _part("symbolic", 0, "false"), 2),
    },

    # =====================================================================
    # ADDED ON THE SECOND AUDIT — the unvisited DIAGONAL corners of the kind
    # pair. Every witness above holds at least one component at exact-zero, so
    # an impl wrong only where both components share a non-zero classification
    # was refuted by NOTHING in the battery: each of these two rivals was
    # cross-built against all ten witnesses above and all twenty builds failed.
    # Both were first run as attack-D probes (each REJECTED by the frozen spec,
    # so neither is a spec hole), then promoted with witnesses that pass both
    # halves of the discrimination check AND the flipped-claim forgery test.
    # =====================================================================
    {
        "id": "weak-both-number-defers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOTHNUM_IMPL),
        "refinement": (
            "a real patch that reported the reduction unsupported whenever BOTH "
            "components are concrete numbers would make the caller fall back on "
            "every value that has a real AND an imaginary part, even though both "
            "are perfectly reducible — every numeric evaluation of such a value "
            "would stop being evaluated; it would not resolve. It is a strictly "
            "narrower over-defer than the unconditional one: correct on every "
            "asymmetric input, so only the both-number corner exposes it."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec licenses the unsupported `.error ()` ONLY "
            "when some component carries an unevaluated marker or is of the "
            "neither kind, and two concrete numbers are neither, so the spec "
            "demands the `.ok` tuple with both value positions and both "
            "precision positions filled. Refuted at the both-number corner "
            "(`floatVal` 3 and 4, `prec = 12`) — the corner NO other witness "
            "visits, since every one of them holds a component at exact-zero. "
            "If it verifies, the spec does not force a supported result once "
            "both components are non-zero and reducible (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("number", 3, "false"),
                            _part("number", 4, "false"), 12),
    },
    {
        "id": "weak-both-symbolic-ok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOTHSYM_IMPL),
        "refinement": (
            "a real patch that guarded each component's classification chain but "
            "short-circuited the case where BOTH components are non-reducible "
            "into a supported result is the deepest form of the original defect: "
            "the reduction hands back a tuple assembled around two values that "
            "were never computed, instead of reporting unsupported so the caller "
            "can fall back. The issue's own reproducer defers correctly, yet a "
            "value whose real AND imaginary parts are both non-reducible still "
            "yields the malformed result — the same failure remains reachable, so "
            "it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = reduceComponentsToFloat rePart "
            "imPart prec`: the spec makes the reduction unsupported when EITHER "
            "component is of the neither kind, which includes the case where "
            "both are, but the rival reports that corner as supported. Refuted "
            "at exactly that corner — both components the neither kind (`prec = "
            "19`) — which every earlier defer witness misses, because each holds "
            "the OTHER component reducible. If it verifies, the spec forces "
            "deferral only when exactly one component is non-reducible "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(_part("symbolic", 0, "false"),
                            _part("symbolic", 0, "false"), 19),
    },

    # =====================================================================
    # SECOND POSITIVE CONTROL (soundness, added on audit) — a correct reshape
    # far from the frozen form: one simultaneous `match` on the PAIR of kinds
    # returning assembled tuple literals, instead of two sequential mutable
    # chains. Guards against the repaired reject lane above having been closed by
    # a spec that merely pins the frozen SHAPE.
    # =====================================================================
    {
        "id": "pos-paired-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS2_IMPL),
        "rationale": (
            "a correct impl that decides all four output positions in ONE match "
            "on the pair of kinds — returning each tuple as a literal, with no "
            "mutable accumulation and no per-component sequencing — must satisfy "
            "`result = reduceComponentsToFloat rePart imPart prec`; if it cannot, "
            "the spec pins the frozen impl's shape rather than its behavior "
            "(SPEC-TOO-STRONG). Distinct from the other positive, which keeps the "
            "per-component structure: this one removes it entirely, so together "
            "they show the spec constrains the input-output relation only. The "
            "frozen tactic's case analysis on the kinds closes it verbatim — the "
            "theorem STATEMENT and proof body are unchanged and no new "
            "declaration/axiom/assumption token is added. Also measured NOT "
            "definitionally equal to the frozen impl (the renamed-copy `rfl` "
            "probe fails on it and succeeds on gold-vs-gold), so this positive "
            "is not a reshape the kernel silently identifies with gold."
        ),
    },
]


# No consumed axioms and no deep-model references: the support decision and the
# four-tuple are modeled directly over the inputs, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
