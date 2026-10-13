# properties.py — G-PBT falsification battery for django__django-16082 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (region
# surgery: only text inside `-- impl-start`/`-- impl-end`, or inside the
# `-- proof-start`/`-- proof-end` tactic body, is edited — both are elided from the
# consumer spec view, so `markers.same_spec` holds and the `theorem
# correct_resolveCombinedType` obligation survives with a byte-identical statement).
# Every expect="reject" case carries a refutation `witness`: a self-contained
# snippet that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the spec and not to a tactic script that merely
# stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   implementation_resolveCombinedType : ArithOp → FieldKind → FieldKind
#                                          → Option FieldKind
#   Given an arithmetic operator and the two operand kinds, resolve the result
#   kind. The single postcondition `problem_spec_resolveCombinedType` pins the
#   result to `resolveSpec op lhs rhs` — the first registered combination for the
#   operator whose two operand slots both ACCEPT the operand kinds, or `none`. The
#   predicate is NOT parameterised in a way that lets one connector behave
#   differently from the spec: it must hold for EVERY operator uniformly. The
#   load-bearing clauses (over the operator × kind grid) are:
#     (S) like-with-like -> that kind, for every operator that supports operands
#         (integer/integer -> integer, decimal/decimal -> decimal, ...);
#     (M) MIXED numeric kinds promote to the WIDER kind — integer/decimal ->
#         decimal, decimal/integer -> decimal, integer/float -> float,
#         float/integer -> float — for EVERY promoting operator INCLUDING the
#         remainder operator (`modOp`). This is the modeled content of the fix:
#         the remainder operator joins the other arithmetic operators in
#         promoting a mixed numeric combination to the wider kind, rather than
#         failing to resolve;
#     (A) the auto-increment integer kind is a specialization of the plain integer
#         kind (`kindMatches .autoKind .integerKind = true`), so an auto operand
#         resolves through the integer rows (auto/integer -> integer, auto/decimal
#         -> decimal, auto/float -> float, ...);
#     (N) a mixed combination the registry does not record (decimal/float,
#         float/decimal), and any mixed combination under a NON-promoting operator
#         (exponentiation), resolves to `none`.
#   `resolveSpec` / `combosFor` / `firstMatch` / `kindMatches` are total,
#   transparent `def`s over the two inputs (no opaque callee, no answer-key), so
#   witnesses need no conditioning on the carrier — `decide` reduces them at any
#   literal (operator, kind, kind) point.
#
# CARRIER NOTE / relation to the nagini sibling. This backend's carrier is RICH:
# it models BOTH the arithmetic operator binder (`op : ArithOp`, six operators)
# AND a distinct auto-increment integer kind (`FieldKind.autoKind`). So the two
# nagini classes that the velvet sibling had to drop as vacuous BOTH port here:
#   * the connector-gated pre-patch rival (`weak-mod-gated-prepatch`) IS
#     expressible — this carrier has an `op` binder, so a rival can promote mixed
#     kinds for every operator EXCEPT the remainder operator, which is exactly the
#     pre-patch registry;
#   * the AUTO rival (`weak-auto-unresolved`) IS expressible — this carrier has a
#     distinct auto kind whose subtype relation to the integer kind a rival can
#     drop.
# The nagini rivals are expressed over nagini's int-code carrier; here they become
# `ArithOp`/`FieldKind` constructors. Every reject witness probes a distinct
# (op, lhs, rhs) point so all three spec binders — the operator, the left kind,
# and the right kind — are varied, and the operator binder in particular is
# probed at BOTH the remainder operator and a non-remainder operator (the exact
# axis the fix turns on).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini declares it STRUCTURALLY INAPPLICABLE: all three
#     params are immutable `int` scalars, nothing to alias/write-through). Lean is
#     referentially transparent regardless — no aliasing, no fractional
#     permission, the three inputs are immutable values — so a "store into a
#     read-only input" rival is not expressible. VACUOUS here. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries none. NOTHING TO
#     SHIP here, but AUDIT-CORRECTED reason: the port claimed a non-terminating
#     impl "cannot be written at all", which is false — `partial def
#     implementation_resolveCombinedType op lhs rhs := implementation_… op lhs rhs`
#     is writable, clears `variant_scope` (measured: no scope problems), and does
#     not need the `partial` keyword banned anywhere in the impl region. What
#     actually makes the class unshippable is that it is UNWITNESSABLE and
#     therefore inconclusive, not inexpressible: measured with two real builds,
#     the diverging rival is REJECTED (exit 1, the frozen `rfl` case split cannot
#     close on an unreducible body), but a witness against it fails by STUCK
#     REDUCTION, not refutation — `Tactic decide failed … instDecidableNot did not
#     reduce to isTrue or isFalse` (exit 1 on the RIVAL side, the half that must
#     succeed). So the case could only ever land as `witness-undecided`, which this
#     gate counts as MALFORMED-TESTS rather than a finding. This is the lean lane's
#     own (semantics-free) situation, NOT the velvet `loom.semantics.termination
#     "partial"` vacuous-verification spec hole recorded in
#     the corpus-wide termination-semantics finding — here the diverging impl does not verify.
#     RE-MEASURED INDEPENDENTLY (second audit pass), and the "unwitnessable"
#     finding is upheld on BOTH available witness shapes, which is stronger than
#     the single measurement above:
#       - the frozen file sets NO `loom.semantics.termination` option at all (the
#         lean lane has no such option), so the "partial => vacuous verification"
#         disposition does not apply; the diverging rival is genuinely REJECTED
#         (measured exit 1, `Tactic rfl failed … not definitionally equal to
#         implementation_resolveCombinedType …`);
#       - a `decide` witness is STUCK on the RIVAL side, the half that must
#         succeed (exit 1, `Tactic decide failed for proposition …`) — the
#         self-call has no normal form for the kernel to evaluate;
#       - a HYPOTHESIS-CONDITIONED witness (`(h : implementation_… = none)` then
#         `rw [h]; decide`), i.e. the technique that makes an opaque carrier
#         attackable, DOES elaborate against the rival (exit 0) but ALSO
#         elaborates against the FROZEN solution (exit 0) — because the
#         hypothesis is false of gold, so the rewrite proves anything. That is
#         `witness-vacuous`, not a refutation.
#     So both shapes land as MALFORMED-TESTS rather than as a finding, and the
#     class is a KNOWN HOLE in what this gate can attest, not a vacuous class.
#     See 'assessment'.
#   * (ADMISSIBILITY DOES PORT — see `admiss-ground-mod-mixed` below. An earlier
#     revision of this manifest recorded the lane as N/A on the ground that the
#     lean obligation `∀ (op) (lhs rhs), problem_spec … (implementation …)` carries
#     no precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. That
#     reason is REJECTED: on a total carrier the analogue of PRECOND-TOO-STRONG is
#     the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#     positive that discharges it AT that concrete input — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly. That
#     is precisely what nagini's `admiss-self-call-mod-mixed` asserts with its
#     three `Assert`s, and it transplants here unchanged. Landed as a case.)
#   * AXIOM_TESTS (nagini's `ax-issubclass-and-registry-cascade`). The axiom lane
#     is G-AX's job; this gate ignores them. `kindMatches` and the row cascade are
#     modeled DEEPLY over transparent carriers (no consumed axiom), so there is
#     nothing to echo here anyway.
from pathlib import Path

INSTANCE = "django__django-16082"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_resolveCombinedType\n"
    "    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do\n"
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Kept intact for
# BOTH positives: each reshaped-but-correct impl is closed by the frozen exhaustive
# case split `cases op <;> cases lhs <;> cases rhs <;> rfl` (confirmed by real build),
# so no reproof, no new lemma/axiom/sorry is needed.
_PROOF = (
    "  intro op lhs rhs\n"
    "  cases op <;> cases lhs <;> cases rhs <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

_HDR = (
    "def implementation_resolveCombinedType\n"
    "    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind := Id.run do\n"
)


def _impl(new_body: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof untouched)."""
    return _swap(_BASE, _IMPL, new_body)


def _proof(new_body: str) -> str:
    """Solution.lean with ONLY the tactic body replaced (spec + impl untouched).

    Used by the admissibility case, which keeps the FROZEN impl and prepends
    ground `have`s to the FROZEN tactic script. The theorem statement is never
    touched, so `same_spec` and the byte-identical obligation both hold.
    """
    return _swap(_BASE, _PROOF, new_body)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Both confirmed out-of-band with a real build;
# each closes under the FROZEN proof body (the exhaustive case split is shape-
# agnostic), so no reproof/new lemma/sorry is introduced.
# ===========================================================================

# pos-reorder-mixed-first: the mixed rows are SCANNED BEFORE the same-kind rows, so
# the assembled row list is `mixedKindRows ++ sameKindRows` — the reverse of the
# frozen `sameKindRows ++ mixedKindRows`. The row guards are mutually exclusive on
# the in-domain grid (a same-kind row never matches a mixed query and vice-versa),
# so the first-match scan returns the same result on every input while the list it
# scans is genuinely a different list.
#
# AUDIT NOTE (repair). The ported form of this case appended in the OTHER direction:
# it seeded `combinators := mixedKindRows` and then rebuilt it as
# `sameKindRows ++ combinators`, which evaluates to `sameKindRows ++ mixedKindRows`
# — byte-for-byte the frozen assembly order. So the "reorder" was definitionally the
# frozen impl's row list, and the case verified while testing nothing about
# order-independence (the property its rationale claims). Rewritten to actually put
# the mixed rows first; re-confirmed to verify under the frozen proof body with a
# real build (exit 0).
_POS_REORDER = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := mixedKindRows\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# pos-explicit-dispatch: a genuinely different SHAPE — a pure `if`-expression (no
# `Id.run do`, no `mut`, no `for` scan) that folds the auto kind to the integer kind
# up front and dispatches on the two resulting operand kinds directly. Behaviourally
# equal to the gold scan over the entire operator × kind grid, including the
# unrecorded decimal/float mix and the non-promoting operator (both -> none). If it
# FAILS => SPEC-TOO-STRONG (the postcondition is over-fit to the scan shape).
_POS_DISPATCH = _impl(
    "def implementation_resolveCombinedType\n"
    "    (op : ArithOp) (lhs rhs : FieldKind) : Option FieldKind :=\n"
    "  let a := match lhs with | .autoKind => FieldKind.integerKind | k => k\n"
    "  let b := match rhs with | .autoKind => FieldKind.integerKind | k => k\n"
    "  let mixedOk := ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op\n"
    "  if a = b then some a\n"
    "  else if mixedOk then\n"
    "    match a, b with\n"
    "    | .integerKind, .decimalKind => some .decimalKind\n"
    "    | .decimalKind, .integerKind => some .decimalKind\n"
    "    | .integerKind, .floatKind => some .floatKind\n"
    "    | .floatKind, .integerKind => some .floatKind\n"
    "    | _, _ => none\n"
    "  else none"
)


# ===========================================================================
# ADMISSIBILITY (AUDIT-ADDED). The frozen obligation is an unconditional
# `∀ (op) (lhs rhs)`, so there is no precondition binder to attack directly. On a
# total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input, and THAT is what this case tests:
# it keeps the FROZEN impl and prepends `have`s that discharge the master clause
# BY EVALUATION at the concrete F2P-shaped points, then closes the frozen
# obligation verbatim. Two `have`s first pin the computed VALUE at those points
# (so the admission is attributed to the promoting branch and not to an
# unspecified one), then three more discharge `problem_spec_resolveCombinedType`
# itself there. If any of them fails, the modeled behavior is unsatisfiable at
# precisely the input the failing test observes.
# ===========================================================================
_ADM = _proof(
    "  -- Ground the master clause at the F2P-shaped inputs BEFORE closing the\n"
    "  -- frozen obligation verbatim: the remainder operator over MIXED numeric\n"
    "  -- operands, in both orientations, plus a same-kind control.\n"
    "  have _val_mod_int_dec :\n"
    "      implementation_resolveCombinedType ArithOp.modOp FieldKind.integerKind\n"
    "        FieldKind.decimalKind = some FieldKind.decimalKind := by decide\n"
    "  have _val_mod_flt_int :\n"
    "      implementation_resolveCombinedType ArithOp.modOp FieldKind.floatKind\n"
    "        FieldKind.integerKind = some FieldKind.floatKind := by decide\n"
    "  have _ground_mod_int_dec : problem_spec_resolveCombinedType\n"
    "      ArithOp.modOp FieldKind.integerKind FieldKind.decimalKind\n"
    "      (implementation_resolveCombinedType ArithOp.modOp FieldKind.integerKind\n"
    "        FieldKind.decimalKind) := by\n"
    "    unfold problem_spec_resolveCombinedType\n"
    "    decide\n"
    "  have _ground_mod_flt_int : problem_spec_resolveCombinedType\n"
    "      ArithOp.modOp FieldKind.floatKind FieldKind.integerKind\n"
    "      (implementation_resolveCombinedType ArithOp.modOp FieldKind.floatKind\n"
    "        FieldKind.integerKind) := by\n"
    "    unfold problem_spec_resolveCombinedType\n"
    "    decide\n"
    "  have _ground_add_int_int : problem_spec_resolveCombinedType\n"
    "      ArithOp.add FieldKind.integerKind FieldKind.integerKind\n"
    "      (implementation_resolveCombinedType ArithOp.add FieldKind.integerKind\n"
    "        FieldKind.integerKind) := by\n"
    "    unfold problem_spec_resolveCombinedType\n"
    "    decide\n"
    + _PROOF
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in
# place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-mod-gated-prepatch (THE bug-delta == pre-patch registry). Promote mixed
# numeric kinds for every operator EXCEPT the remainder operator: the mixed rows are
# added only for add/sub/mul/div, with `modOp` dropped from the guard. Correct on
# every non-remainder operator and every same-kind query; WRONG for the remainder
# operator over mixed operands (returns none instead of the wider kind).
_RIV_GATED = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-mixed-dropped-all: the mixed rows are dropped for EVERY operator; only the
# three same-kind rows remain. Correct on same-kind queries; WRONG on every mixed
# operand pair even for the already-working operators.
_RIV_DROPALL = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-mixed-decimal-narrower (the exact defect the issue names — "doesn't resolve
# to a Decimal"): the integer/decimal mix resolves to the NARROWER integer kind
# instead of the wider decimal kind. Float mixes still correct.
_RIV_NARROW = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++\n"
    "      [(.integerKind, .decimalKind, .integerKind),\n"
    "       (.decimalKind, .integerKind, .integerKind),\n"
    "       (.integerKind, .floatKind,   .floatKind),\n"
    "       (.floatKind,   .integerKind, .floatKind)]\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-only-float-mixed: partial fix WITHIN the mixed sub-domain — only the
# integer/float widenings are recorded; the integer/decimal widenings are dropped.
# Correct on same-kind and on float mixes; WRONG on decimal mixes (-> none). Exactly
# the half-fix a value-proxy that only spot-checks the float sub-domain would miss.
_RIV_FLOATONLY = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++\n"
    "      [(.integerKind, .floatKind, .floatKind),\n"
    "       (.floatKind,   .integerKind, .floatKind)]\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-pow-overpromoted (AUDIT-ADDED; clause (N), operator axis). The OVER-fix in
# the promoting direction: the mixed rows are registered for EVERY same-kind
# operator, i.e. exponentiation is dragged into the promoting set too. Correct on
# all five promoting operators and on every same-kind query; WRONG at the
# non-promoting operator over mixed operands (resolves to the wider kind where the
# registry records nothing). The five ported rivals all attack by REMOVING or
# NARROWING a promotion, so none of them would notice a spec that failed to pin the
# non-promoting operator's `none`; this is the missing direction.
_RIV_POWWIDE = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-decimalfloat-resolved (AUDIT-ADDED; clause (N), kind axis). Registers two
# rows the registry does NOT record — the decimal/float mix in both orientations —
# resolving them to the float kind. Correct on every recorded combination; WRONG on
# the decimal/float mix, which must stay unresolved. Again the direction none of the
# ported rivals take: they all under-resolve, so a spec that left the UNRECORDED
# mixes free would pass the whole ported battery.
_RIV_DECFLT = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows ++\n"
    "      [(.decimalKind, .floatKind, .floatKind),\n"
    "       (.floatKind,   .decimalKind, .floatKind)]\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-auto-unresolved: drop the auto<:integer specialization — any auto operand
# short-circuits to the unresolved sentinel. Correct on the integer/decimal/float
# grid; WRONG on every auto query.
_RIV_AUTO = _impl(
    _HDR +
    "  if lhs == FieldKind.autoKind || rhs == FieldKind.autoKind then\n"
    "    return none\n"
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)


# weak-samekind-decimal-dropped (AUDIT-ADDED; clause (S), the LIKE-WITH-LIKE lane).
# Every other rival in this battery attacks a MIXED row or the auto relation, so
# clause (S) — like-with-like resolves to that kind — was attacked by nothing: a
# spec that pinned only the mixed grid and left the same-kind rows free would have
# been rejected by all seven and the hole would be invisible. This drops the
# same-kind DECIMAL row while keeping the integer and float ones and the whole
# mixed grid. Correct on every mixed query and on integer/integer and float/float;
# WRONG at decimal/decimal, which must resolve to the decimal kind and instead
# falls through to the unresolved sentinel.
_RIV_SAMEKIND_DEC = _impl(
    _HDR +
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++\n"
    "      [(.integerKind, .integerKind, .integerKind),\n"
    "       (.floatKind,   .floatKind,   .floatKind)]\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)

# weak-auto-rhs-rejected (AUDIT-ADDED; clause (A) in the ORIENTATION direction).
# weak-auto-unresolved drops the auto specialization in BOTH slots at once, so it
# cannot tell a spec that pins the auto relation SYMMETRICALLY from one that only
# pins it in the left slot. This rival is the asymmetric near-miss: an auto operand
# is accepted in the LHS slot (via the integer rows, as gold does) but rejected in
# the RHS slot. Correct on every query whose right operand is not auto — including
# all of weak-auto-unresolved's left-auto points; WRONG whenever the auto kind
# appears on the right.
_RIV_AUTO_RHS = _impl(
    _HDR +
    "  if rhs == FieldKind.autoKind then\n"
    "    return none\n"
    "  let mut combinators : List ComboRow := []\n"
    "  if sameKindOps.contains op then\n"
    "    combinators := combinators ++ sameKindRows\n"
    "  if ([ArithOp.add, .sub, .mul, .div, .modOp] : List ArithOp).contains op then\n"
    "    combinators := combinators ++ mixedKindRows\n"
    "  for (clhs, crhs, combined) in combinators do\n"
    "    if kindMatches lhs clhs && kindMatches rhs crhs then\n"
    "      return some combined\n"
    "  return none"
)


def _wit(op: str, lhs: str, rhs: str, note: str) -> str:
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (op, lhs, rhs). `decide` reduces resolveSpec/combosFor/firstMatch/
    kindMatches (all total transparent defs) and settles the disequality. Binds
    NOTHING in its head (literal inputs), so there is no consistency obligation.
    Elaborates against a rival that diverges from the spec there, and FAILS on gold
    (which satisfies the spec at every input) — SEEN to discriminate both ways."""
    args = f"ArithOp.{op} FieldKind.{lhs} FieldKind.{rhs}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_resolveCombinedType {args}\n"
        f"    (implementation_resolveCombinedType {args}) := by\n"
        f"  unfold problem_spec_resolveCombinedType\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-mixed-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "a correct scan whose assembled row list is `mixedKindRows ++ "
            "sameKindRows` — the REVERSE of the frozen `sameKindRows ++ "
            "mixedKindRows`, so the scan visits the mixed rows first. The row "
            "guards are mutually exclusive on the in-domain grid, so the "
            "first-match scan returns the same result on every (op, lhs, rhs) — a "
            "structurally different but behaviourally identical impl. The theorem "
            "statement is byte-identical and the FROZEN exhaustive case-split proof "
            "still closes (confirmed by a real build); no reproof, no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to one syntactic scan order)."
        ),
    },
    {
        "id": "pos-explicit-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DISPATCH,
        "rationale": (
            "a genuinely different SHAPE: a pure `if`-expression (no `Id.run do`, no "
            "`mut`, no `for` scan) that folds the auto kind to the integer kind up "
            "front and dispatches on the two operand kinds directly. Behaviourally "
            "equal to the gold scan over the entire operator × kind grid (incl. the "
            "unrecorded decimal/float mix and the non-promoting operator, both -> "
            "none). Theorem statement byte-identical; the FROZEN exhaustive "
            "case-split proof closes it (confirmed by a real build) — no reproof, no "
            "new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to the scan shape rather than the behaviour)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-mod-mixed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "the frozen obligation is an unconditional `∀ (op) (lhs rhs)`, so there "
            "is no precondition binder to attack directly; on this total carrier the "
            "analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at "
            "exactly an F2P-shaped input. This case tests that directly: keeping the "
            "FROZEN impl, it discharges `problem_spec_resolveCombinedType` BY "
            "EVALUATION (`decide`) at the F2P-shaped points — the REMAINDER operator "
            "over mixed numeric operands in both orientations (integer with decimal, "
            "float with integer), plus a same-kind control — as `have`s, and only "
            "then closes the frozen obligation verbatim. Two further `have`s pin the "
            "computed VALUE at those points (`some decimalKind` / `some floatKind`), "
            "so the admission is attributed to the promoting branch rather than to an "
            "unspecified one; a plain discharge alone would also hold of a spec that "
            "resolved those points to anything at all. Nothing is assumed: no new "
            "declaration, no lemma/axiom/sorry, the theorem statement is "
            "byte-identical, and every addition is a `have` inside the existing "
            "tactic body. If it FAILS => the modeled behavior is unsatisfiable at "
            "precisely the input the failing tests observe. Ports nagini's "
            "`admiss-self-call-mod-mixed`, whose three `Assert`s are these points."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-mod-gated-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GATED,
        "refinement": (
            "this IS the pre-patch registry: the mixed numeric promotion rows are "
            "recorded for every arithmetic operator EXCEPT the remainder operator "
            "(the gold patch's added remainder entry reverted). The F2P "
            "test_resolve_output_field_number iterates the remainder operator over "
            "mixed numeric operands (e.g. integer with decimal) and asserts the "
            "combined output field resolves to the wider (decimal) type; a faithful "
            "real counterpart returns no type -> 'Cannot infer type of %% expression' "
            "FieldError, so the test still errors. The faithful real patch FAILS the "
            "F2P; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: under the remainder "
            "operator a mixed operand pair promotes to the wider kind, but the rival "
            "returns none. Witness probes the REMAINDER operator specifically "
            "(op = modOp with integer/float operands), the exact operator-binder "
            "point the fix turns on — the near-miss agrees with gold on every "
            "non-remainder operator, so only a remainder-operator witness "
            "discriminates it. If it VERIFIES => SPEC-TOO-WEAK (the remainder-operator "
            "mixed promotion is unpinned)."
        ),
        # (modOp, integer, float): gold -> some float; gated rival -> none.
        "witness": _wit("modOp", "integerKind", "floatKind",
                        "remainder operator, mixed integer/float: gold promotes to "
                        "float, pre-patch rival leaves unresolved"),
    },
    {
        "id": "weak-mixed-dropped-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPALL,
        "refinement": (
            "this drops the mixed numeric promotion rows for EVERY promoting "
            "operator (both the remainder line and the pre-existing add/sub/mul/div "
            "mixed rows). test_resolve_output_field_number iterates its mixed "
            "numeric rows over every promoting operator and asserts each resolves "
            "to the wider type; a faithful real counterpart returns no type for "
            "every mixed pair -> 'Cannot infer type' FieldError, so the test errors "
            "on the non-remainder operators too. The faithful real patch FAILS the "
            "F2P (worse than pre-patch); it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: on a mixed operand pair "
            "the spec promotes to the wider kind; the rival returns none. Witness "
            "probes a NON-remainder operator (op = add with float/integer operands), "
            "where the gated near-miss would still be correct — so this point "
            "distinguishes 'dropped for all operators' from 'dropped for the "
            "remainder operator only'. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (add, float, integer): gold -> some float; drop-all rival -> none.
        "witness": _wit("add", "floatKind", "integerKind",
                        "non-remainder operator, mixed float/integer: gold promotes "
                        "to float, all-dropped rival leaves unresolved"),
    },
    {
        "id": "weak-mixed-decimal-narrower",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NARROW,
        "refinement": (
            "this records the integer/decimal mixed rows but with the WRONG result "
            "kind (the narrower integer kind instead of the wider decimal kind) — the "
            "precise defect the issue describes ('doesn't resolve to a Decimal'). "
            "test_resolve_output_field_number asserts the integer/decimal combination "
            "resolves to the decimal type; a faithful real counterpart resolves it to "
            "the integer type, so the assertion fails. The faithful real patch FAILS "
            "the F2P; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: the decimal/integer mix "
            "promotes to the decimal kind; the rival returns the integer kind. "
            "Witness at (modOp, decimal, integer) — the decimal-widening clause in "
            "the reversed orientation, under the remainder operator, where gold -> "
            "some decimal and the rival -> some integer. If it VERIFIES => "
            "SPEC-TOO-WEAK (the mix resolves to the wrong kind, not merely to none)."
        ),
        # (modOp, decimal, integer): gold -> some decimal; narrower rival -> some integer.
        "witness": _wit("modOp", "decimalKind", "integerKind",
                        "remainder operator, mixed decimal/integer: gold promotes to "
                        "decimal, narrower rival resolves to integer"),
    },
    {
        "id": "weak-only-float-mixed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLOATONLY,
        "refinement": (
            "this registers only the integer/float mixed widenings and omits the "
            "integer/decimal ones. test_resolve_output_field_number's integer/decimal "
            "and decimal/integer rows fail (a faithful real counterpart returns no "
            "type for a decimal mix -> 'Cannot infer type' FieldError), so the test "
            "still errors. The faithful real patch FAILS the F2P; it does NOT resolve "
            "— and this is a NEAR-MISS that passes the float half of the mixed grid."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: the integer/decimal mix "
            "promotes to the decimal kind but the rival returns none (only the float "
            "mixes are recorded). Witness at (mul, integer, decimal) — puts the "
            "decimal kind in the rhs position under yet another operator, exercising "
            "the decimal-widening clause the float-only fix drops. If it VERIFIES => "
            "SPEC-TOO-WEAK on the decimal sub-domain."
        ),
        # (mul, integer, decimal): gold -> some decimal; float-only rival -> none.
        "witness": _wit("mul", "integerKind", "decimalKind",
                        "non-remainder operator, mixed integer/decimal: gold promotes "
                        "to decimal, float-only rival leaves the decimal mix unresolved"),
    },
    {
        "id": "weak-pow-overpromoted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_POWWIDE,
        "refinement": (
            "this widens the mixed numeric promotion to EVERY operator that accepts "
            "same-kind operands, i.e. exponentiation is added to the promoting set "
            "alongside the remainder operator. The registry records no mixed "
            "combination for exponentiation, so a faithful real counterpart would "
            "report a combined output type where the real resolver reports none — "
            "changing behaviour on an operator the fix does not touch and that no "
            "F2P row asserts. It over-resolves rather than under-resolves, so it is "
            "not a pre-patch state and does NOT resolve the issue faithfully: it "
            "silently infers a type for an operand pair the registry leaves "
            "unregistered, which the caller is entitled to reject."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: `mixedKindOps` excludes "
            "the exponentiation operator, so a mixed operand pair under it resolves "
            "to none; the rival returns the wider kind. Witness at (powOp, integer, "
            "decimal) — the ONLY witness in the battery at the non-promoting "
            "operator, and the only one probing clause (N) on the operator axis. "
            "Every other rival attacks by removing a promotion, so if the spec "
            "failed to pin the non-promoting operator's none, all five would still "
            "reject and the hole would be invisible. If it VERIFIES => "
            "SPEC-TOO-WEAK (mixed promotion is not confined to the promoting "
            "operators)."
        ),
        # (powOp, integer, decimal): gold -> none; over-promoting rival -> some decimal.
        "witness": _wit("powOp", "integerKind", "decimalKind",
                        "NON-promoting operator, mixed integer/decimal: gold leaves "
                        "it unresolved, over-promoting rival widens to decimal"),
    },
    {
        "id": "weak-decimalfloat-resolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DECFLT,
        "refinement": (
            "this registers the decimal/float mix (both orientations) as resolving "
            "to the float kind. The registry records no such combination — only "
            "mixes involving the integer kind are recorded — so a faithful real "
            "counterpart would infer a combined type for a pair the real resolver "
            "leaves unresolved, and would silently pick a lossy result kind for a "
            "decimal operand. No F2P row asserts this pair; the change is outside "
            "the fix and it does NOT resolve the issue faithfully."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: no registered row "
            "accepts a decimal/float pair, so the spec pins none; the rival returns "
            "some float. Witness at (add, decimal, float) — clause (N) on the KIND "
            "axis, the unrecorded mix, at a point no other witness touches. The five "
            "ported rivals all under-resolve, so this is the only case that would "
            "catch a spec leaving the unrecorded mixes free. If it VERIFIES => "
            "SPEC-TOO-WEAK (the unrecorded mixed combinations are not pinned to "
            "none)."
        ),
        # (add, decimal, float): gold -> none; rival -> some float.
        "witness": _wit("add", "decimalKind", "floatKind",
                        "UNRECORDED decimal/float mix: gold leaves it unresolved, "
                        "over-registering rival resolves it to float"),
    },
    {
        "id": "weak-auto-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_AUTO,
        "refinement": (
            "this drops the specialization of the auto-increment integer kind to the "
            "plain integer kind — any auto operand short-circuits to the unresolved "
            "sentinel. The real subclass relation makes the auto-increment field a "
            "kind of integer, so the real resolver treats an auto operand via the "
            "integer rows; the number F2P exercises auto/integer combinations and "
            "asserts they resolve. A faithful real counterpart that failed to treat "
            "the auto field as an integer would diverge from the real callee (which "
            "G-CONF/G-AX validate against the real subclass test over the full grid) "
            "and would break the auto-combination behaviour the registry guarantees. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: the auto kind matches the "
            "integer slot (`kindMatches .autoKind .integerKind = true`), so an "
            "auto/decimal mix promotes to the decimal kind, but the rival returns "
            "none for any auto operand. Witness at (add, auto, decimal) — varies the "
            "LEFT kind to the auto kind (a kind no other witness probes) and pins the "
            "auto specialization clause. If it VERIFIES => SPEC-TOO-WEAK (the auto "
            "kind's subtype behaviour is unpinned)."
        ),
        # (add, auto, decimal): gold -> some decimal (auto matches integer slot);
        # auto rival -> none.
        "witness": _wit("add", "autoKind", "decimalKind",
                        "auto operand with decimal: gold resolves it through the "
                        "integer rows to decimal, auto-dropping rival leaves it unresolved"),
    },
    {
        "id": "weak-samekind-decimal-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SAMEKIND_DEC,
        "refinement": (
            "this keeps the whole mixed promotion grid (so the modeled content of the "
            "fix is present and correct) but drops the like-with-like row for the "
            "decimal kind. A faithful real counterpart would fail to infer a type for "
            "two decimal operands — a combination that has always resolved and that "
            "the issue does not touch — so it breaks long-standing behaviour outside "
            "the fix while leaving the fix itself intact. That is a regression, not a "
            "pre-patch state, and it does NOT resolve the issue faithfully."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: `sameKindRows` records "
            "the decimal/decimal row, so two decimal operands resolve to the decimal "
            "kind; the rival leaves them unresolved. Witness at (mul, decimal, "
            "decimal) — clause (S), the LIKE-WITH-LIKE lane, which NO other case in "
            "this battery attacks: every other rival edits a mixed row or the auto "
            "relation, so a spec that pinned only the mixed grid and left the "
            "same-kind rows free would be rejected by all of them and the hole would "
            "never surface. If it VERIFIES => SPEC-TOO-WEAK (the same-kind rows are "
            "unpinned)."
        ),
        # (mul, decimal, decimal): gold -> some decimal; rival -> none.
        "witness": _wit("mul", "decimalKind", "decimalKind",
                        "LIKE-WITH-LIKE decimal pair: gold resolves to decimal, the "
                        "same-kind-dropping rival leaves it unresolved"),
    },
    {
        "id": "weak-auto-rhs-rejected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_AUTO_RHS,
        "refinement": (
            "this accepts the auto-increment integer kind in the LEFT operand slot "
            "(through the integer rows, as the registry does) but rejects it in the "
            "RIGHT slot. The real subclass relation is a property of the field kind, "
            "not of which operand position it occupies, so a faithful real "
            "counterpart would resolve an auto operand on the left and fail on the "
            "right — an orientation-dependent asymmetry the real resolver does not "
            "have, and one that would diverge from the real subclass callee that "
            "G-CONF/G-AX validate over the full grid. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = resolveSpec op lhs rhs`: `kindMatches` is applied "
            "to both slots alike, so an auto operand resolves through the integer "
            "rows in EITHER position; the rival returns none whenever the auto kind "
            "is on the right. Witness at (modOp, integer, auto) — the auto kind in "
            "the RHS slot, which no other witness probes (weak-auto-unresolved sits "
            "at (add, auto, decimal), a LEFT-auto point where this rival is still "
            "CORRECT). So this is the strict near-miss that separates 'the auto "
            "relation is pinned symmetrically' from 'pinned in the left slot only'. "
            "If it VERIFIES => SPEC-TOO-WEAK (the auto relation is unpinned in the "
            "right operand position)."
        ),
        # (modOp, integer, auto): gold -> some integer; rhs-rejecting rival -> none.
        "witness": _wit("modOp", "integerKind", "autoKind",
                        "auto operand in the RIGHT slot: gold resolves it through the "
                        "integer rows, the rhs-rejecting rival leaves it unresolved"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling SPEC lane has 8 cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 1-case AXIOM lane.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-reorder-mixed-first      -> pos-reorder-mixed-first     PORTED
#   pos-explicit-dispatch        -> pos-explicit-dispatch       PORTED
#   admiss-self-call-mod-mixed   -> admiss-ground-mod-mixed     PORTED (audit-landed)
#   weak-mod-gated-prepatch      -> weak-mod-gated-prepatch     PORTED (op binder exists)
#   weak-mixed-dropped-all       -> weak-mixed-dropped-all      PORTED
#   weak-mixed-decimal-narrower  -> weak-mixed-decimal-narrower PORTED
#   weak-only-float-mixed        -> weak-only-float-mixed       PORTED
#   weak-auto-unresolved         -> weak-auto-unresolved        PORTED (auto kind exists)
#   AXIOM_TESTS (1)              -> (none)                      DROPPED (G-AX lane)
#   (no sibling)                 -> weak-pow-overpromoted       AUDIT-ADDED
#   (no sibling)                 -> weak-decimalfloat-resolved  AUDIT-ADDED
#   (no sibling)                 -> weak-samekind-decimal-dropped  AUDIT-ADDED (2nd pass)
#   (no sibling)                 -> weak-auto-rhs-rejected         AUDIT-ADDED (2nd pass)
#
# UNLIKE the velvet sibling, this lean carrier models BOTH the operator binder AND
# the distinct auto kind, so weak-mod-gated-prepatch and weak-auto-unresolved — both
# vacuous on velvet — port here as full reject rivals with discriminating witnesses.
# The connector-gated rival is kept SEPARATE from weak-mixed-dropped-all (it is a
# strict near-miss: correct on every non-remainder operator), and the two are
# probed at distinct operator points so the distinction is demonstrated.
#
# PORTED (admissibility): landed as `admiss-ground-mod-mixed` by the second audit
#   pass. The earlier "N/A because the obligation has no precondition hypothesis"
#   is an INADMISSIBLE reason: on a total carrier the lane's content is the
#   obligation's SATISFIABILITY at an F2P-shaped input, which is testable and is
#   now tested. Measured: verifies (exit 0), variant_problems=[], theorem statement
#   byte-identical, and the ground `have`s are load-bearing (a negative control
#   asserting the narrower kind at the same point fails, exit 1).
# VACUOUS (frame-mutation): referentially transparent carrier, immutable value
#   inputs, no `mut` binder, no heap — no read-only input to overwrite. (Nagini
#   declared this structurally inapplicable too.)
# KNOWN HOLE, not vacuous (divergence/non-termination): a diverging impl IS
#   writable here (`partial def implementation_… := implementation_… op lhs rhs`)
#   and clears variant_scope; it is REJECTED (exit 1). What blocks the case is that
#   it is unwitnessable on both available shapes — a `decide` witness is stuck on
#   the RIVAL side (exit 1) and a hypothesis-conditioned witness elaborates against
#   GOLD too (exit 0, `witness-vacuous`) — so it can only ever record
#   MALFORMED-TESTS. Re-measured independently; see the header note.
# DROPPED (AXIOM_TESTS): this gate ignores the axiom lane (G-AX's job); the
#   subclass test and the row cascade are modeled deeply, no consumed axiom.
#
# AUDIT-ADDED rivals (not in the nagini sibling; found by an independent
# SPEC-TOO-WEAK probe over the clauses the ported set left unattacked):
#   weak-pow-overpromoted      -> clause (N) on the OPERATOR axis
#   weak-decimalfloat-resolved -> clause (N) on the KIND axis
# Both attack in the OVER-resolving direction. Every ported rival under-resolves
# (removes or narrows a promotion), so a spec that pinned only "the promotions are
# present" and left the UNRECORDED combinations free would have been rejected by all
# five ported rivals and the hole would never have surfaced. Confirmed by real
# builds: each rival is rejected with the frozen proof retained (exit 1) and its
# witness elaborates against the rival (exit 0) while failing on the frozen solution
# by a SEMANTIC refutation (`decide` proved the negation false), not a name/type
# error. The frozen spec pinned both — no spec hole.
#
# SECOND-PASS AUDIT-ADDED rivals, aimed at the two clauses the nine-case battery
# left with NO attacker at all:
#   weak-samekind-decimal-dropped -> clause (S), like-with-like. Every prior rival
#     edits a MIXED row or the auto relation, so a spec pinning only the mixed grid
#     and leaving the same-kind rows free would have been rejected by all seven.
#   weak-auto-rhs-rejected        -> clause (A) in the ORIENTATION direction. The
#     existing auto rival drops the relation in BOTH slots at once, so it cannot
#     separate a symmetric pinning from a left-slot-only one; this one is correct at
#     the existing rival's own witness point and wrong only with auto on the right.
# Both measured: rival module rejected with the frozen proof retained (exit 1),
# witness elaborates against the rival (exit 0), fails on the frozen solution
# (exit 1) by `decide proved … is false`, and a FORGERY dropping the `¬` inverts
# both exits (gold 0 / rival 1), so the gold-side code tracks the CLAIM.
#
#   The nine reject witnesses probe nine DISTINCT (op, lhs, rhs) points:
#     (modOp,int,float) (add,float,int) (modOp,dec,int) (mul,int,dec) (add,auto,dec)
#     (powOp,int,dec) (add,dec,float) (mul,dec,dec) (modOp,int,auto)
#   [nine uniqueness rivals; each one point]. op takes {modOp, add, mul, powOp} —
#   the remainder operator, other promoting operators, AND the non-promoting
#   operator, so the operator binder is probed on both sides of the promoting/
#   non-promoting split as well as the axis the fix turns on; lhs takes {integer,
#   float, decimal, auto}; rhs takes {float, integer, decimal, auto}. No binder is
#   pinned. Both mixed widenings are attacked in both orientations, the
#   remainder-vs-other-operator distinction is demonstrated (gated near-miss refuted
#   only at modOp; drop-all refuted at add), the auto specialization is pinned in
#   BOTH operand slots, clause (N) is pinned on both axes in the over-resolving
#   direction, and clause (S) is pinned in the under-resolving direction.
#   Every witness was confirmed with two real builds to ELABORATE against the rival
#   and FAIL against the frozen solution; every rival module was confirmed to fail
#   verification with the frozen proof retained; both positives and the
#   admissibility case were confirmed to verify.
#
# INDEPENDENT WHOLE-GRID CHECK (second pass). Rather than trust per-point reasoning,
# every case's impl was compiled side-by-side with `resolveSpec` and evaluated over
# the ENTIRE 6x4x4 operator x kind grid (96 points). Result: the frozen impl and
# both positives disagree with the spec at 0 points; each of the nine rivals
# disagrees at 8-40 points, and every witness point is one of its own disagreement
# points. So no rival is merely RESHAPED — each is observably wrong on this carrier.
AXIOM_TESTS = []
