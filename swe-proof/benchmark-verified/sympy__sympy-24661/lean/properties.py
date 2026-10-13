"""properties.py — G-PBT falsification battery for sympy__sympy-24661 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and every ``theorem correct_*`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function):

  implementation_transformRelational (left : AstNode) (op : RelOp) (right : AstNode)
      : AstNode

  A single comparison ``left op right`` is rewritten in a non-evaluating mode.
  The postcondition ``problem_spec_transformRelational`` splits on whether the
  operator is one of the six recognised relational operators
  (``relClassName op = some cls``):

    * RECOGNISED — the result is fully pinned to the call
      ``AstNode.app cls [transform left, transform right] true``. FIVE things are
      pinned at once and each is an independent, load-bearing clause:
        (C1) the OUTER shape is an ``app`` (a produced call), not the unchanged
             ``cmp`` — the observable the fix restores;
        (C2) the CONSTRUCTOR NAME is exactly ``cls`` = the operator's own name
             (the bijection ``lt→Lt … ne→Ne``), never a fixed/other name;
        (C3) the OPERANDS appear in source order ``[transform left, transform
             right]`` — left first, right second;
        (C4) the "do-not-evaluate" FLAG is ``true``, never ``false`` — the exact
             reported bug (a relational built evaluating collapses to a value).
        (C5) each operand is the REBUILT ``transform`` of the source operand, not
             the source operand itself — so a comparison nested inside another is
             itself rewritten. Independent of C1-C4 and observable ONLY at a
             COMPOUND operand: ``transform`` is the identity on literals and
             identifiers, so a rival that skips the recursion agrees with gold at
             every atomic input. ``rival-no-recurse`` attacks it at a nested
             comparison; the F2P's own bare-numeral inputs cannot see it. C5 is
             moreover TWO obligations, one per operand POSITION, and each is
             separately load-bearing: a rival may rebuild one operand and pass the
             other through raw. ``rival-right-no-recurse`` isolates the RIGHT
             position, which every other witness in the battery leaves unprobed
             because each states its compound operand on the LEFT. And C5 is
             RECURSIVE, not one-step: ``transform`` on a ``cmp`` rebuilds that
             comparison's own operands too, which is strictly stronger than "the
             operand is rebuilt at all". A rival that rebuilds an operand's outer
             relational — right name, right order, right flag — but stops before
             ITS operands agrees with gold at every DEPTH-1 nested operand, i.e.
             at the input both C5 position cases state, and is observable only at
             a DEPTH-2 nest: ``rival-cmp-one-level``.
        (C6) rebuilding a CALL operand is itself two obligations, and ``transform``
             discharges both: its ARGUMENTS are each rebuilt, and the
             do-not-evaluate flag is attached when the callee is one of the names
             built in non-evaluating form (an ADD, so a flag already present
             survives). Observable only at a call-shaped operand, which no other
             clause's witness uses: ``rival-identity-on-call`` leaves a call
             operand alone and agrees with gold at every atomic and every
             nested-comparison input. Splitting C6's two halves is what
             ``rival-call-no-flag`` and ``rival-call-no-argrecurse`` probe
             separately. The flag half is itself a DISJUNCTION (``evalFalse ||
             isNonEvaluatingFunc func``), and the left disjunct is separately
             load-bearing: a flag ALREADY carried by the operand survives even
             when the callee is NOT in the table, because the modeled rebuild only
             ever adds. A rival that ASSIGNS the table lookup instead of or-ing it
             therefore agrees with gold on every input the other rivals use — the
             two differ only at an ordinary callee that arrives already flagged —
             and ``rival-call-flag-assign`` is stated at exactly that input.
             C6's argument half is finally ELEMENTWISE over the whole list, not
             just its head: ``transformArgs`` maps ``transform`` over every
             argument. Every call-shaped operand the four cases above use has
             exactly ONE argument, so a rival that rebuilds only the first
             argument agrees with gold on all of them and is observable only at a
             call of arity ≥ 2 whose LATER argument is compound:
             ``rival-call-first-arg-only``.
    * UNRECOGNISED (``relClassName op = none``, i.e. ``RelOp.other``) — the node
      is returned UNCHANGED (``result = AstNode.cmp left op right``); a rival that
      converts it anyway is refuted by this clause. "Unchanged" is pinned over the
      SOURCE operands, not merely as "a ``cmp`` under the same operator", so a
      rival that keeps the outer ``cmp`` but rewrites INSIDE it also violates the
      clause. ``rival-over-convert`` attacks the outer constructor at atomic
      operands, on which such a rival is the identity, so the ``none`` branch's
      OPERAND FIELDS need their own case: ``rival-none-branch-transforms``.

  Input binders of the spec predicate: ``left``, ``op``, ``right``, ``result``.
  The reject witnesses below vary ``op`` across ALL SEVEN values (``lt``, ``le``,
  ``gt``, ``ge``, ``eq``, ``ne``, ``other``) and vary ``left`` / ``right`` across
  constants, identifiers, a NESTED COMPARISON (at depth 1 and at depth 2), and a
  CALL (arity 1 and arity 2), in both the left and the right position, so no
  clause is probed at a single fixed input point and neither operand binder is
  held constant. The compound operand matters on its own account: it is the only
  input shape at which clause C5 is observable at all (see C5).

  Binder VARIATION is not binder COVERAGE, so the variations that are actually
  load-bearing are named here, each established the same way — by rebuilding
  every other witness in the battery against the rival and showing that NONE of
  them refutes it (all exit 1). Five were added by audit:

    * ``rival-right-no-recurse`` — the ``ge`` operator and the RIGHT-hand
      compound operand. Every other witness states its compound operand on the
      LEFT.
    * ``rival-call-flag-assign`` — an already-flagged ORDINARY callee, the only
      input at which C6's disjunction differs from an assignment.
    * ``rival-cmp-one-level`` — a DEPTH-2 nest. Both C5 position cases state
      depth 1, at which a one-step rebuild is indistinguishable from the
      recursive one.
    * ``rival-call-first-arg-only`` — a call of ARITY 2 whose later argument is
      compound. Every other call-shaped operand in the battery is arity 1, at
      which rebuilding only the head is indistinguishable from mapping the list.
    * ``rival-none-branch-transforms`` — a COMPOUND operand under ``other``. The
      battery's other ``op=other`` witness states atomic operands, so the
      ``none`` clause's operand fields were unprobed.

  The last three of those closed gaps the previous revision's own prose asserted
  it had covered: it described C5 as observable "at a COMPOUND operand" and C6's
  argument half as "its ARGUMENTS are each rebuilt" without any case that
  distinguished one-step from recursive, or head-only from elementwise.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION (nagini ``frame-mut-op`` / ``frame-mut-tag``) —
    VACUOUS. The nagini bundle held the comparison node's operator and operand
    tags at a fractional (read-only) permission and its MANDATORY frame probes
    wrote them back (``node.op = node.op``) to be rejected for insufficient
    permission. Lean is referentially transparent: the inputs carry no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. These two rivals have NO expressible instance here and
    no substitute is fabricated. See 'assessment'.

  * WRONG CONSTRUCTOR (nagini ``wrong-constructor``) — PORTED as
    ``rival-wrong-constructor``: emit a fixed ``"Lt"`` for every recognised
    operator, attacking clause C2 (the bijection). Correct only on ``lt``.

  * OPERAND ORDER SWAP (nagini ``operand-order-swap``) — PORTED as
    ``rival-operand-order-swap``: build the call with operands reversed,
    attacking clause C3.

  * EVALUATE=TRUE (nagini ``evaluate-true``, THE reported bug) — PORTED as
    ``rival-evaluate-flag``: attach the flag as ``false`` (evaluating) instead of
    ``true``, attacking clause C4.

  * PARTIAL-DOMAIN / DROP EQUALITY (nagini ``partial-domain-drop-eq``) — PORTED
    as ``rival-drop-eq``: treat ``RelOp.eq`` as unrecognised (leave it a ``cmp``),
    attacking clause C1 at the equality operator. Correct on the other five.

  * OVER-CONVERT NON-RELATIONAL (nagini ``over-convert-nonrelational``) — PORTED
    as ``rival-over-convert``: convert EVERY comparison to a call, including the
    unrecognised operator, attacking the ``none`` branch (C1 in the other
    direction — a call where the node must stay a ``cmp``).

  * NO NAGINI ANALOGUE (added by audit from the carrier's own clause structure,
    not from the design document) — ``rival-cmp-one-level``,
    ``rival-call-first-arg-only`` and ``rival-none-branch-transforms``. The
    nagini sibling's rivals are all stated over the ``ast`` node the transformer
    is handed, at the depth and arity its own tests use; these three attack
    obligations that exist because THIS carrier models the dispatch DEEPLY
    (``transform``/``transformArgs`` recurse, and the ``none`` branch pins the
    operand fields). Each was landed only after its rival was shown unreachable
    by all eleven pre-existing witnesses.

  * POSITIVE CONTROL (nagini ``pos-control-branch-reorder``) — PORTED as
    ``pos-branch-reorder``: a structurally-different but CORRECT impl (the
    unrecognised case is handled first and the operand locals are bound in the
    opposite order). Must verify (else SPEC-TOO-STRONG).

  * ADMISSIBILITY (nagini ``admiss-readonly-input``) — PORTED as
    ``admiss-ground-instance``: the obligation is discharged at a ground,
    F2P-shaped input (``1 < 2``) as a ``have`` prepended to the frozen tactic
    body, which then closes verbatim. Must verify (else PRECOND-TOO-STRONG).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, and the reject case that used to
    stand here (``rival-nonterminating``) was DROPPED by audit as hollow. The
    reasoning it rested on — "``partial`` makes the function opaque, so the
    obligation can never close, so the rejection is attributable to divergence" —
    is false in the direction that matters. Three builds settle it:

      - a ``partial def`` carrying the GOLD body verbatim (not self-recursive at
        all) VERIFIES, so ``partial`` alone does not block the obligation;
      - a ``partial def`` that IS self-recursive but whose recursive arm is
        unreachable — so its VALUE equals gold's at every input, i.e. a CORRECT
        impl — is REJECTED, with the error byte-identical to the diverging
        rival's (``Tactic `unfold` failed to unfold
        implementation_transformRelational``);
      - the dropped case's own witness ELABORATES against that correct impl.

    So the rejection tracked OPACITY (``unfold`` cannot see through a ``partial``
    definition), not wrongness, and the witness could not tell a diverging impl
    from a correct one. It was hollow for a second, independent reason as well:
    it conditioned the opaque call's value by HYPOTHESIS, and a forged hypothesis
    naming a value the rival never produces (``= AstNode.const 42``) passes both
    halves of the discrimination check identically — the hypothesis does all the
    work, so gold's exit code carries no information about the rival.

    On this carrier there is no ``set_option loom.semantics.termination`` line at
    all: the obligation is a plain Lean ``theorem`` over a total ``def``, and
    reduction — not a discharged termination measure — is what closes it. A plain
    ``def`` that re-enters itself is refused outright ('fail to show
    termination'), so no diverging impl can be stated that the spec then judges
    on its VALUE. The class is therefore recorded as a KNOWN HOLE (the spec does
    not constrain termination) rather than as a vacuous class or a carried case,
    and no substitute is fabricated. (The nagini sibling carries no ``diverge-*``
    case either, so nothing is dropped from the design document here.)

  * AXIOM lane (nagini ``AXIOM_TESTS`` / ``aref-visit-compare``) — DROPPED. The
    axiom lane is G-AX's job; this gate ignores it. This carrier declares NO
    ``opaque`` callee and consumes NO ``axiom … _prop`` (``correct_*`` closes by
    a case split on ``relClassName op``), so there is no axiom-soundness
    obligation for this gate.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input: it reduces the rival's ``implementation_transformRelational`` at
that input via a fixed ``simp only`` set, then inverts the produced
``AstNode`` constructor (``injection`` / ``AstNode.noConfusion``) to derive the
contradiction. Each was machine-checked to ELABORATE against its rival and to
FAIL against the frozen solution (whose result carries the right constructor,
order, flag and outer shape), so it is a real discriminator, not a tautology.

Every witness here is UNCONDITIONAL — it binds no hypothesis and states its
refutation at literal inputs, so the claim is settled by reduction and nothing
rests on the hypotheses being satisfiable. That is a deliberate property of this
battery, established by audit after the one hypothesis-conditioned witness it
carried was found hollow (see the divergence note above): a conditioned witness
lets the HYPOTHESIS rather than the impl close the goal, and a forged hypothesis
naming a value the rival never produces then passes both halves of the gate's
discrimination check. The gold-side failure of each witness here was additionally
confirmed to TRACK THE CLAIM rather than to be a fixed tactic mismatch: flipping a
witness's claim (dropping the ``¬``) makes the frozen solution ACCEPT it, and
revealing the reduced hypothesis's type prints ``True`` on gold — ``simp`` proved
the spec equation there — against a concrete false equation on the rival.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24661"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl or proof region and is
# unique in the file, so every replacement preserves same_spec by construction.
# ---------------------------------------------------------------------------

# The complete gold impl body (the match over `relClassName op`), unique in the
# file and wholly inside the impl region.
_IMPL_GOLD = """  match relClassName op with
  | some cls =>
    let right' := transform right
    let left' := transform left
    return AstNode.app cls [left', right'] true
  | none =>
    return AstNode.cmp left op right"""

# The complete gold proof body, unique and wholly inside the proof region.
_PROOF_GOLD = """  intro left op right
  unfold problem_spec_transformRelational implementation_transformRelational
  cases h : relClassName op with
  | none => rfl
  | some cls => rfl"""

assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each ships the FROZEN proof body verbatim (a `sorry` would
# violate variant scope), so its rejection is the frozen script failing against
# the reshaped impl — which is exactly why the WITNESS, not the rejection,
# attributes the failure to the spec.
# ---------------------------------------------------------------------------

# rival-wrong-constructor: emit a fixed "Lt" for every recognised operator.
# Correct only for `lt`; violates C2 (the constructor bijection) for the others.
_RIVAL_WRONGCTOR = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some _ =>
    let right' := transform right
    let left' := transform left
    return AstNode.app "Lt" [left', right'] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-operand-order-swap: build the call with operands reversed. Violates C3.
_RIVAL_SWAP = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let right' := transform right
    let left' := transform left
    return AstNode.app cls [right', left'] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-evaluate-flag: attach the "do-not-evaluate" flag as `false`. Violates C4
# — the exact reported bug (a relational built evaluating collapses to a value).
_RIVAL_EVAL = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let right' := transform right
    let left' := transform left
    return AstNode.app cls [left', right'] false
  | none =>
    return AstNode.cmp left op right""",
)

# rival-drop-eq: treat `RelOp.eq` as unrecognised (leave it a `cmp`). Correct on
# the other five; violates C1 (outer shape) at the equality operator.
_RIVAL_DROPEQ = _swap(
    _BASE, _IMPL_GOLD,
    """  match op with
  | RelOp.eq => return AstNode.cmp left op right
  | _ =>
    match relClassName op with
    | some cls =>
      let right' := transform right
      let left' := transform left
      return AstNode.app cls [left', right'] true
    | none =>
      return AstNode.cmp left op right""",
)

# rival-over-convert: convert EVERY comparison to a call, including the
# unrecognised operator (a fixed name is used where there is no constructor).
# Violates C1 on the `none` branch — a call where the node must stay a `cmp`.
_RIVAL_OVERCONV = _swap(
    _BASE, _IMPL_GOLD,
    """  let cls := (relClassName op).getD "Rel"
  let right' := transform right
  let left' := transform left
  return AstNode.app cls [left', right'] true""",
)

# rival-no-recurse: build the call from the operands AS GIVEN, skipping the
# recursive rebuild. Attacks clause C5 — the operands are pinned to `transform
# left` / `transform right`, NOT to `left` / `right`. Agrees with gold on every
# ATOMIC operand (`transform` is the identity on literals and identifiers), so
# the five rivals above — all stated at atomic operands — leave this clause
# completely unprobed; it is observable only at a COMPOUND operand.
_RIVAL_NORECURSE = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    return AstNode.app cls [left, right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-identity-on-call: leave a CALL operand exactly as it came in (the shape a
# model that treats the dispatch as identity-on-call predicts). Attacks clause C6
# as a whole. Agrees with gold on every atom and every nested comparison, so all
# six rivals above leave it unprobed.
_RIVAL_IDCALL = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let shallow : AstNode → AstNode := fun n =>
      match n with
      | .app f a e => .app f a e
      | n => transform n
    return AstNode.app cls [shallow left, shallow right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-call-no-flag: rebuild a call's ARGUMENTS but never attach the
# do-not-evaluate flag to a non-evaluating callee. Attacks the second half of C6
# only; correct on ordinary callees, wrong on the non-evaluating ones.
_RIVAL_CALLNOFLAG = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let noFlag : AstNode → AstNode := fun n =>
      match transform n with
      | .app f a _ => .app f a false
      | m => m
    return AstNode.app cls [noFlag left, noFlag right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-call-no-argrecurse: attach the flag by the table but do NOT rebuild the
# call's arguments. Attacks the first half of C6 only; correct whenever the
# arguments are already atoms.
_RIVAL_CALLNOARGS = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let left' := match left with
      | .app f a e => AstNode.app f a (e || isNonEvaluatingFunc f)
      | n => transform n
    let right' := match right with
      | .app f a e => AstNode.app f a (e || isNonEvaluatingFunc f)
      | n => transform n
    return AstNode.app cls [left', right'] true
  | none =>
    return AstNode.cmp left op right""",
)


# rival-right-no-recurse: rebuild the LEFT operand but pass the RIGHT one through
# raw. Attacks clause C5 at the RIGHT operand POSITION specifically. Every other
# rival in this battery that touches C5 or C6 states its compound operand on the
# LEFT, so all ten of their witnesses elaborate against this rival unchanged (all
# measured: exit 1, i.e. none refutes it) — the position is a separate obligation
# and this is the only case that probes it.
_RIVAL_RIGHTNORECURSE = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    return AstNode.app cls [transform left, right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-call-flag-assign: ASSIGN the table lookup to a call operand's flag instead
# of OR-ing it with the flag the operand already carries. Attacks the left disjunct
# of C6's flag half: the modeled rebuild only ever ADDS the flag, so one already
# present must survive even for a callee outside the table. Differs from gold ONLY
# at an already-flagged ORDINARY callee, which no other witness in the battery
# uses; it rebuilds the arguments correctly and is right on every non-evaluating
# callee, so `rival-call-no-flag` and `rival-identity-on-call` do not reach it.
_RIVAL_CALLFLAGASSIGN = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let fix : AstNode → AstNode := fun n =>
      match n with
      | .app f a _ => .app f (transformArgs a) (isNonEvaluatingFunc f)
      | n => transform n
    return AstNode.app cls [fix left, fix right] true
  | none =>
    return AstNode.cmp left op right""",
)


# rival-cmp-one-level: rebuild a nested-comparison operand ONE LEVEL only — emit
# the relational call for the operand itself but pass ITS OWN operands through
# raw. Attacks the RECURSIVENESS of C5 (`transform` on a `cmp` rebuilds the
# sub-operands too, via `transform left`/`transform right` inside `transform`),
# which is a strictly stronger obligation than "the operand is rebuilt at all":
# this rival DOES rebuild each operand's outer shape, name, order and flag, so it
# agrees with gold at every DEPTH-1 nested operand — which is the only nesting
# depth `rival-no-recurse` and `rival-right-no-recurse` state. Observable only at
# a DEPTH-2 nest, and measured: all eleven other witnesses in this battery
# elaborate against it unchanged (each exits 1, i.e. none refutes it).
_RIVAL_CMPONELEVEL = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let one : AstNode → AstNode := fun n =>
      match n with
      | .cmp l o r =>
        match relClassName o with
        | some c => .app c [l, r] true
        | none => .cmp l o r
      | m => transform m
    return AstNode.app cls [one left, one right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-call-first-arg-only: rebuild only the FIRST argument of a call operand,
# leaving the remaining arguments raw. Attacks the ELEMENTWISE-ness of C6's
# argument half (`transformArgs` maps over the WHOLE list, not just its head).
# Every call-shaped operand used by `rival-identity-on-call`,
# `rival-call-no-flag`, `rival-call-no-argrecurse` and `rival-call-flag-assign`
# has exactly ONE argument, so this rival agrees with gold on all of them and is
# observable only at a call of arity ≥ 2 whose LATER argument is compound.
# Measured: all eleven other witnesses elaborate against it unchanged (exit 1).
_RIVAL_CALLFIRSTARG = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let one : AstNode → AstNode := fun n =>
      match n with
      | .app f (a :: rest) e => .app f (transform a :: rest) (e || isNonEvaluatingFunc f)
      | m => transform m
    return AstNode.app cls [one left, one right] true
  | none =>
    return AstNode.cmp left op right""",
)

# rival-none-branch-transforms: on the UNRECOGNISED branch, rebuild the operands
# instead of returning the node UNCHANGED. Attacks the `none` clause's strength:
# the clause pins `result = AstNode.cmp left op right` with the SOURCE operands,
# not merely "the result is a `cmp` under the same operator", so rewriting inside
# a node that must be returned untouched violates it. `rival-over-convert` — the
# battery's only other `op=other` case — changes the OUTER constructor and states
# its witness at atomic operands, on which this rival is the identity, so it
# agrees with gold there; the two differ only at an unrecognised comparison whose
# operand is itself compound. Measured: all eleven other witnesses elaborate
# against it unchanged (exit 1).
_RIVAL_NONETRANSFORMS = _swap(
    _BASE, _IMPL_GOLD,
    """  match relClassName op with
  | some cls =>
    let right' := transform right
    let left' := transform left
    return AstNode.app cls [left', right'] true
  | none =>
    return AstNode.cmp (transform left) op (transform right)""",
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — structurally different but CORRECT. Handle the
# unrecognised case first via an early return, and bind the operand locals in the
# opposite order in the recognised branch. Same value on every branch, so the
# postcondition is unchanged. The proof reshapes minimally: the case split is the
# same, both arms still close by `rfl`.
# ---------------------------------------------------------------------------
_POS_REORDER = _swap(
    _swap(
        _BASE, _IMPL_GOLD,
        """  match relClassName op with
  | none =>
    return AstNode.cmp left op right
  | some cls =>
    let left' := transform left
    let right' := transform right
    return AstNode.app cls [left', right'] true""",
    ),
    _PROOF_GOLD,
    """  intro left op right
  unfold problem_spec_transformRelational implementation_transformRelational
  cases h : relClassName op with
  | none => rfl
  | some cls => rfl""",
)

# A SECOND positive that is NOT definitionally equal to the frozen impl. The one
# above only reorders match arms and `let` bindings, both of which are defeq — its
# arms still close by the frozen `rfl`, so it is honest but weak. This one drops
# the table lookup from the impl entirely and enumerates all SEVEN operators with
# literal constructor names, so the impl no longer mentions `relClassName` at all
# and the spec's `match relClassName op` must be reconciled operator-by-operator:
# the frozen `cases h : relClassName op ... rfl` no longer closes it, and the proof
# genuinely reshapes to `cases op <;> rfl`. Faithful to the spec on every operator
# (it is the table, written out), so it MUST verify — else SPEC-TOO-STRONG.
_POS_ENUMERATE = _swap(
    _swap(
        _BASE, _IMPL_GOLD,
        """  match op with
  | RelOp.lt => return AstNode.app "Lt" [transform left, transform right] true
  | RelOp.le => return AstNode.app "Le" [transform left, transform right] true
  | RelOp.gt => return AstNode.app "Gt" [transform left, transform right] true
  | RelOp.ge => return AstNode.app "Ge" [transform left, transform right] true
  | RelOp.eq => return AstNode.app "Eq" [transform left, transform right] true
  | RelOp.ne => return AstNode.app "Ne" [transform left, transform right] true
  | RelOp.other => return AstNode.cmp left op right""",
    ),
    _PROOF_GOLD,
    """  intro left op right
  unfold problem_spec_transformRelational implementation_transformRelational
  cases op <;> rfl""",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is discharged at a ground F2P-shaped input
# (`1 < 2`) as a `have` prepended to the frozen tactic body; the frozen
# obligation is then closed verbatim. Nothing is assumed: no new declaration, the
# `correct_transformRelational` statement is byte-identical, and the ground
# instance is proved by reducing the impl to the spec's call.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _PROOF_GOLD,
    """  have _ground : problem_spec_transformRelational
      (AstNode.const 1) RelOp.lt (AstNode.const 2)
      (implementation_transformRelational (AstNode.const 1) RelOp.lt (AstNode.const 2)) := by
    simp only [problem_spec_transformRelational, implementation_transformRelational,
      relClassName, transform, Id.run, pure]
  intro left op right
  unfold problem_spec_transformRelational implementation_transformRelational
  cases h : relClassName op with
  | none => rfl
  | some cls => rfl""",
)


# ---- witnesses (each machine-checked: elaborates vs rival, fails vs frozen) --
def _wit(op, left, right, closer):
    return (
        "example : ¬ problem_spec_transformRelational\n"
        f"    ({left}) RelOp.{op} ({right})\n"
        f"    (implementation_transformRelational ({left}) RelOp.{op} ({right})) := by\n"
        "  simp only [problem_spec_transformRelational, implementation_transformRelational,\n"
        "    relClassName, transform, Id.run, pure]\n"
        "  intro h\n"
        f"{closer}"
    )


# C2: rival's outer call names "Lt" but the spec pins "Le"; `injection` on the
# `app` exposes the name clash, closed by `decide`. op=le, operands are constants.
_WIT_WRONGCTOR = _wit(
    "le", "AstNode.const 1", "AstNode.const 2",
    "  injection h with hf _\n  exact absurd hf (by decide)\n",
)

# C3: rival's first argument is `name \"b\"`, spec's is `name \"a\"`; peel the
# outer `app`, then the first list cons, then the `name`. op=lt, identifiers.
_WIT_SWAP = _wit(
    "lt", "AstNode.name \"a\"", "AstNode.name \"b\"",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with hn\n"
    "  exact absurd hn (by decide)\n",
)

# C4: rival's flag is `false`, spec's is `true`; the third `app` field clashes.
# op=gt, distinct constants (5,7).
_WIT_EVAL = _wit(
    "gt", "AstNode.const 5", "AstNode.const 7",
    "  injection h with _ _ hev\n  exact absurd hev (by decide)\n",
)

# C1 (equality dropped): rival returns a `cmp`, spec pins an `app`; the two
# constructors do not unify. op=eq, mixed operands (identifier, constant).
_WIT_DROPEQ = _wit(
    "eq", "AstNode.name \"p\"", "AstNode.const 9",
    "  exact AstNode.noConfusion h\n",
)

# C1 (over-convert): rival returns an `app`, spec pins the unchanged `cmp`; the
# two constructors do not unify. op=other, mixed operands (constant, identifier).
_WIT_OVERCONV = _wit(
    "other", "AstNode.const 3", "AstNode.name \"q\"",
    "  exact AstNode.noConfusion h\n",
)

# C5 (recursive rebuild): stated at a COMPOUND left operand — a nested comparison
# `1 < 2` under `!=` — which is the only place this clause is observable. The
# rival's first argument is the RAW `cmp` sub-node; the spec pins `transform left`,
# i.e. the rebuilt `app "Lt" ...`. Peel the outer `app`, then the first cons, then
# the two constructors do not unify. op=ne, the sixth operator value.
_WIT_NORECURSE = _wit(
    "ne", "AstNode.cmp (AstNode.const 1) RelOp.lt (AstNode.const 2)",
    "AstNode.const 3",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  exact AstNode.noConfusion hargs.1\n",
)

# C6 (whole clause): stated at a NON-EVALUATING call operand `sin(x)` under `<`.
# The rival returns the call untouched (flag `false`); the spec pins the rebuilt
# call whose flag is `true`. Peel the outer `app`, then the first cons, then the
# inner `app`'s flag field.
_WIT_IDCALL = _wit(
    "lt", "AstNode.app \"sin\" [AstNode.name \"x\"] false", "AstNode.const 3",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ _ hev\n"
    "  exact absurd hev (by decide)\n",
)

# C6 (flag half): same operand shape, but the rival DOES rebuild the arguments —
# it only drops the flag. Refuted on the same field, which is what makes the two
# halves of C6 separately load-bearing.
_WIT_CALLNOFLAG = _wit(
    "le", "AstNode.app \"exp\" [AstNode.const 1] false", "AstNode.const 2",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ _ hev\n"
    "  exact absurd hev (by decide)\n",
)

# C6 (argument-recursion half): an ORDINARY callee (not in the table, so the flag
# is irrelevant) wrapping a nested comparison. The rival leaves the inner `cmp`
# raw; the spec pins the rebuilt `app "Lt" ...`. Peel outer `app`, first cons,
# inner `app`, its first cons, then the constructors do not unify.
_WIT_CALLNOARGS = _wit(
    "gt",
    "AstNode.app \"f\" [AstNode.cmp (AstNode.const 1) RelOp.lt (AstNode.const 2)] false",
    "AstNode.const 3",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ hinner _\n"
    "  simp only [transformArgs, transform, relClassName] at hinner\n"
    "  rw [List.cons_eq_cons] at hinner\n"
    "  exact AstNode.noConfusion hinner.1\n",
)


# C5 (RIGHT operand position): stated at a compound operand on the RIGHT — a
# nested `2 < 3` under `>=` — the mirror of `rival-no-recurse`'s input. The rival's
# SECOND argument is the raw `cmp` sub-node; the spec pins `transform right`, i.e.
# the rebuilt `app "Lt" ...`. Peel the outer `app`, then TWO conses to reach the
# second element, then the constructors do not unify. op=ge, the seventh operator
# value and the one no other witness binds. Unconditional (no hypothesis): the
# claim is decided by reduction, so nothing rests on a satisfiability probe.
_WIT_RIGHTNORECURSE = _wit(
    "ge", "AstNode.const 1",
    "AstNode.cmp (AstNode.const 2) RelOp.lt (AstNode.const 3)",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons, List.cons_eq_cons] at hargs\n"
    "  exact AstNode.noConfusion hargs.2.1\n",
)

# C6 (flag DISJUNCTION, left disjunct): stated at an ORDINARY callee `g(1)` that
# ALREADY carries the flag, under `==`. Gold's rebuild or-s the existing flag with
# the table lookup, so the flag survives as `true`; the rival assigns the lookup,
# which is `false` for `g`, so the flag is LOST. The arguments are rebuilt
# identically on both sides and the callee is outside the table, so the flag field
# is the ONLY difference — which is what isolates this disjunct. Peel the outer
# `app`, the first cons, then the inner `app`'s flag field. op=eq.
_WIT_CALLFLAGASSIGN = _wit(
    "eq", "AstNode.app \"g\" [AstNode.const 1] true", "AstNode.const 4",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ _ hev\n"
    "  exact absurd hev (by decide)\n",
)


# C5 (RECURSIVENESS, depth 2): stated at a DOUBLY-nested left operand —
# `(1 < 2) <= 3` under `<`. The rival rebuilds that operand's outer relational
# correctly but leaves ITS first operand the raw inner `cmp`; the spec pins
# `transform left`, which rebuilds all the way down. Peel the outer `app`, the
# first cons, the inner `app`'s own argument list, then its first cons: the two
# constructors do not unify. Depth 1 is where every other C5 witness stops, so
# this is the only input at which the recursion's own recursion is observable.
_WIT_CMPONELEVEL = _wit(
    "lt",
    "AstNode.cmp (AstNode.cmp (AstNode.const 1) RelOp.lt (AstNode.const 2)) "
    "RelOp.le (AstNode.const 3)",
    "AstNode.const 4",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ hinner _\n"
    "  rw [List.cons_eq_cons] at hinner\n"
    "  exact AstNode.noConfusion hinner.1\n",
)

# C6 (argument half, ELEMENTWISE): stated at an ORDINARY callee of arity TWO
# whose SECOND argument is a nested comparison — `f(1, 2 < 3)` under `>`. The
# callee is outside the table so the flag is identical on both sides and only the
# argument WALK can be responsible; the rival rebuilds the head and leaves the
# tail raw, while the spec pins `transformArgs`, which maps the whole list. Peel
# the outer `app`, the first cons, the inner `app`'s arguments, then TWO conses to
# reach the second element.
_WIT_CALLFIRSTARG = _wit(
    "gt",
    "AstNode.app \"f\" [AstNode.const 1, "
    "AstNode.cmp (AstNode.const 2) RelOp.lt (AstNode.const 3)] false",
    "AstNode.const 4",
    "  injection h with _ hargs\n"
    "  rw [List.cons_eq_cons] at hargs\n"
    "  injection hargs.1 with _ hinner _\n"
    "  simp only [transformArgs, transform, relClassName] at hinner\n"
    "  rw [List.cons_eq_cons, List.cons_eq_cons] at hinner\n"
    "  exact AstNode.noConfusion hinner.2.1\n",
)

# `none` clause (operands UNCHANGED): stated at op=other over a COMPOUND left
# operand — a nested `1 < 2`. The clause pins the result to `AstNode.cmp left op
# right` with the SOURCE operands; the rival returns a `cmp` whose left field is
# the rebuilt `app "Lt" ...`. Injecting the `cmp` exposes the left field, whose
# two constructors do not unify. The battery's other `op=other` witness states
# atomic operands, on which this rival is the identity.
_WIT_NONETRANSFORMS = _wit(
    "other", "AstNode.cmp (AstNode.const 1) RelOp.lt (AstNode.const 2)",
    "AstNode.const 3",
    "  injection h with hl _ _\n"
    "  exact AstNode.noConfusion hl\n",
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness)
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "Structurally-different CORRECT impl: the unrecognised case is handled "
            "first via an early return and the operand locals are bound in the "
            "opposite order in the recognised branch. The value returned on every "
            "branch is unchanged, so all four recognised clauses (outer shape, "
            "constructor, operand order, flag) and the unchanged-node clause still "
            "hold; must verify (else SPEC-TOO-STRONG — a faithful correct impl "
            "rejected). The case split is the same, so both arms still close by "
            "`rfl`; no new lemma, axiom, or assumption is introduced. NOTE: this "
            "reshape is definitionally equal to the frozen impl (reordered match "
            "arms and `let` bindings both are), which is why it is not the "
            "battery's only positive — see `pos-enumerate-ops`, whose impl is not "
            "defeq and whose proof genuinely reshapes."
        ),
    },
    {
        "id": "pos-enumerate-ops",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ENUMERATE,
        "rationale": (
            "A CORRECT impl that is NOT definitionally equal to the frozen one: the "
            "table lookup is dropped from the implementation entirely and all seven "
            "operators are enumerated with literal constructor names, so the impl "
            "never mentions `relClassName` while the spec still branches on it. The "
            "frozen tactic body does NOT close this (`cases h : relClassName op` "
            "leaves the operator abstract, so neither arm is `rfl`-true); the proof "
            "genuinely reshapes to `cases op <;> rfl`, reconciling the two forms "
            "operator-by-operator. This is what makes it a real soundness probe "
            "rather than a restatement: it writes the bijection out longhand and is "
            "faithful on every operator, so the spec must ACCEPT it. If it were "
            "rejected the spec would be SPEC-TOO-STRONG — pinning the impl's "
            "SYNTACTIC form (that it consult the table) rather than its VALUE. No "
            "new lemma, axiom, or assumption is introduced."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The obligation is discharged at a ground F2P-shaped input (`1 < 2`, a "
            "recognised operator over two numeric literals) as a `have` prepended "
            "to the frozen tactic body; the frozen obligation is then closed "
            "verbatim. Verifies (else the modeled behavior would be unsatisfiable "
            "at exactly the shape the F2P exercises — the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, the "
            "`correct_transformRelational` statement is byte-identical, and the "
            "ground instance is proved by reducing the impl to the spec's call."
        ),
    },
    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "rival-wrong-constructor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WRONGCTOR,
        "refinement": (
            "Hard-coding the strict-less constructor for every recognised operator "
            "is correct only for `<`. The faithful real patch looks the operator up "
            "in its constructor table, producing the matching name for `<=`, `>`, "
            "`>=`, `==`, `!=`; emitting the strict-less name for `1 <= 2` yields a "
            "call to the wrong relational constructor, which is NOT equal to the "
            "expected unevaluated object. The added F2P assertion for `1 <= 2` (and "
            "four other operators) FAILS — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (constructor bijection): the result must be the "
            "call named `cls` = the operator's own constructor, but this rival "
            "always names the strict-less one. Witness at op=le / (const 1, const "
            "2) reduces the rival's impl to a call named `\"Lt\"` and inverts the "
            "`app` to expose the clash with the pinned `\"Le\"`; it fails on gold, "
            "whose call is named `\"Le\"`."
        ),
        "witness": _WIT_WRONGCTOR,
    },
    {
        "id": "rival-operand-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SWAP,
        "refinement": (
            "Building the call with operands reversed produces a call whose first "
            "argument is the right operand. The faithful real patch places the "
            "operands in source order (left first); for `1 < 2` the swapped form is "
            "the object for `2 < 1`, which is NOT equal to the expected `1 < 2` "
            "object, so the F2P assertion for `1 < 2` (and every asymmetric "
            "operator) FAILS — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C3 (operand order): the result's arguments must be "
            "`[transform left, transform right]`, but this rival emits them "
            "reversed. Witness at op=lt / (name \"a\", name \"b\") reduces the "
            "rival's impl to a call whose first argument is `name \"b\"` and peels "
            "the `app`/cons/`name` to expose the clash with the pinned first "
            "argument `name \"a\"`; it fails on gold, whose first argument is `name "
            "\"a\"`. Varies both operand binders (identifiers, distinct from the "
            "other rivals' constants)."
        ),
        "witness": _WIT_SWAP,
    },
    {
        "id": "rival-evaluate-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EVAL,
        "refinement": (
            "Attaching the flag as evaluating reproduces the EXACT reported bug: a "
            "relational built without the do-not-evaluate flag collapses to a "
            "concrete truth value. The faithful real patch sets the flag so the "
            "parse stays unevaluated; with it cleared, parsing `1 < 2` in "
            "non-evaluating mode returns the boolean value instead of the "
            "unevaluated relational object — precisely what the F2P was written to "
            "catch — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C4 (do-not-evaluate flag): the produced call must "
            "carry the flag `true`, but this rival carries `false`. Witness at "
            "op=gt / (const 5, const 7) reduces the rival's impl to a call with the "
            "flag `false` and inverts the `app`'s third field to expose the clash "
            "with the pinned `true`; it fails on gold, whose flag is `true`."
        ),
        "witness": _WIT_EVAL,
    },
    {
        "id": "rival-drop-eq",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROPEQ,
        "refinement": (
            "Treating equality as unrecognised is correct on five operators but "
            "drops `==`. The faithful real patch would omit equality from the "
            "operator table, leaving `1 == 2` an unchanged comparison node that "
            "collapses to a boolean; parsing `1 == 2` in non-evaluating mode then "
            "returns the truth value instead of the unevaluated equality object — "
            "the `1 == 2` entry of the F2P FAILS — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (outer shape) at the equality operator: for a "
            "recognised operator the result must be an `app`, but this rival leaves "
            "it the unchanged `cmp`. Witness at op=eq / (name \"p\", const 9) "
            "reduces the rival's impl to a `cmp` and refutes it against the pinned "
            "`app` via `AstNode.noConfusion`; it fails on gold, whose result is an "
            "`app`. Varies both operand binders (identifier, constant)."
        ),
        "witness": _WIT_DROPEQ,
    },
    {
        "id": "rival-over-convert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OVERCONV,
        "refinement": (
            "Converting every comparison to a call also rewrites the unrecognised "
            "operators (identity / membership tests). The faithful real patch only "
            "rewrites operators IN the table and returns the rest unchanged; "
            "wrapping such a comparison into a relational call with a fabricated "
            "constructor changes parser output for those comparisons (the gold "
            "returns them unchanged so they behave as before). The pre-existing "
            "parser tests covering non-relational comparison parsing would break — "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (outer shape) on the `none` branch: for an "
            "unrecognised operator the result must be the unchanged `cmp`, but this "
            "rival forces an `app`. Witness at op=other / (const 3, name \"q\") "
            "reduces the rival's impl to an `app` and refutes it against the pinned "
            "`cmp` via `AstNode.noConfusion`; it fails on gold, whose result is the "
            "unchanged `cmp`. Exercises the `other` operator, the only value the "
            "other rivals never probe."
        ),
        "witness": _WIT_OVERCONV,
    },
    {
        "id": "rival-no-recurse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NORECURSE,
        "refinement": (
            "Building the call from the operands AS GIVEN skips the recursive "
            "rebuild of each operand. The faithful real patch rebuilds each operand "
            "through the same dispatch before assembling the call, so a comparison "
            "nested inside another comparison is itself rewritten into an "
            "unevaluated relational; without the recursion the inner comparison "
            "stays a raw comparison node and collapses to a truth value when the "
            "rewritten tree is finally evaluated. Indistinguishable from the "
            "faithful patch on the F2P's own literals (both operands there are bare "
            "numerals, on which the rebuild is the identity), so this is the clause "
            "a shallow patch passes the F2P while still breaking: the surrounding "
            "parser tests that nest a comparison inside a relational FAIL — does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C5 (recursive rebuild): the result's arguments must "
            "be `[transform left, transform right]`, but this rival emits `[left, "
            "right]`. Because `transform` is the IDENTITY on literals and "
            "identifiers, this rival agrees with gold at every input the other five "
            "witnesses use — so the clause is observable only at a COMPOUND "
            "operand, and the witness is stated at one: a nested `1 < 2` as the left "
            "operand of `!=`. It reduces the rival's impl to a call whose first "
            "argument is the raw `cmp` sub-node and refutes it against the pinned "
            "rebuilt `app` via `AstNode.noConfusion`; it fails on gold, whose first "
            "argument is that rebuilt `app`. Adds the sixth operator value (`ne`) "
            "and the only compound operand in the battery."
        ),
        "witness": _WIT_NORECURSE,
    },
    {
        "id": "rival-identity-on-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_IDCALL,
        "refinement": (
            "Leaving a CALL operand exactly as it came in skips the rebuild that "
            "a call receives: its arguments are not rewritten and the "
            "do-not-evaluate flag is not attached to a callee built in "
            "non-evaluating form. The faithful real patch rebuilds each operand "
            "through the same dispatch, and that dispatch handles a call by "
            "rewriting its arguments and then adding the flag for such a callee. "
            "So parsing a comparison one side of which is such a call yields a "
            "call still marked as evaluating, and the sub-expression evaluates "
            "when the rewritten tree is finally evaluated — the same class of bug "
            "the report is about, one level in. Indistinguishable from the "
            "faithful patch on the F2P's own bare-numeral literals, so it passes "
            "the F2P while breaking every parser test whose comparison has a "
            "named-function operand — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C6: an operand that is a call must be the REBUILT "
            "call, but this rival returns it verbatim. Because `transform` is the "
            "identity on literals and identifiers and this rival only differs on "
            "the call arm, it agrees with gold at every input the other six "
            "witnesses use — including `rival-no-recurse`'s nested comparison — so "
            "the clause is observable only at a CALL operand, and the witness is "
            "stated at one (`sin(x)` under `<`). It reduces the rival's impl to a "
            "first argument whose flag is `false` and inverts the inner `app` to "
            "expose the clash with the pinned `true`; it fails on gold, whose "
            "first argument carries `true`. Adds the only call-shaped operand in "
            "the battery."
        ),
        "witness": _WIT_IDCALL,
    },
    {
        "id": "rival-call-no-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CALLNOFLAG,
        "refinement": (
            "Rebuilding a call's arguments but never attaching the "
            "do-not-evaluate flag drops half of the treatment a call receives. "
            "The faithful real patch consults the table of names that are built "
            "in non-evaluating form and attaches the flag when the callee is one "
            "of them; without it the sub-call evaluates eagerly, so a comparison "
            "over such a call parses to a partially-evaluated object rather than "
            "the fully unevaluated one. Correct on ordinary callees, so it passes "
            "the F2P and every test whose operands are plain — does NOT resolve."
        ),
        "rationale": (
            "REJECT from the FLAG half of clause C6, isolated: this rival differs "
            "from `rival-identity-on-call` in that it DOES rewrite the arguments, "
            "so a witness that only probed argument recursion would accept it. "
            "Witness at op=le / (`exp(1)`, const 2) reduces the rival's first "
            "argument to a call with flag `false` and exposes the clash with the "
            "pinned `true`; it fails on gold. Uses a different non-evaluating "
            "callee and a different operator from the sibling case."
        ),
        "witness": _WIT_CALLNOFLAG,
    },
    {
        "id": "rival-call-no-argrecurse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CALLNOARGS,
        "refinement": (
            "Attaching the flag by the table but NOT rebuilding a call's "
            "arguments drops the other half of the treatment a call receives. The "
            "faithful real patch rewrites every child of a call before applying "
            "the flag, so a comparison nested inside a call argument is itself "
            "rebuilt; without the recursion that inner comparison stays a raw "
            "comparison node and collapses to a truth value. Correct whenever the "
            "arguments are already atoms, which is every F2P input — does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the ARGUMENT-RECURSION half of clause C6, isolated. The "
            "witness deliberately uses an ORDINARY callee (`f`, not in the table) "
            "so the flag is identical under rival and gold and ONLY the argument "
            "walk can be responsible: op=gt / (`f(1 < 2)`, const 3) reduces the "
            "rival's first argument to a call whose own first argument is the raw "
            "`cmp`, and refutes it against the pinned rebuilt `app` via "
            "`AstNode.noConfusion`; it fails on gold. Together with "
            "`rival-call-no-flag` this shows both halves of C6 are load-bearing "
            "independently, not just their conjunction."
        ),
        "witness": _WIT_CALLNOARGS,
    },
    {
        "id": "rival-right-no-recurse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_RIGHTNORECURSE,
        "refinement": (
            "Rebuilding one operand but passing the other through raw skips the "
            "recursive rebuild on ONE SIDE only. The faithful real patch rebuilds "
            "both operands through the same dispatch before assembling the call, "
            "so a comparison nested on either side is itself rewritten; with the "
            "right-hand rebuild missing, a comparison appearing as the right "
            "operand stays a raw comparison node and collapses to a truth value "
            "when the rewritten tree is finally evaluated. Indistinguishable from "
            "the faithful patch on the F2P's own literals — both operands there "
            "are bare numerals, on which the rebuild is the identity — and also "
            "indistinguishable from it on every input whose only compound operand "
            "is on the LEFT, so a battery that probes recursion only on the left "
            "accepts it: the parser tests that nest a comparison on the right FAIL "
            "— does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C5 at the RIGHT operand POSITION. C5 is two "
            "obligations, one per position, and this rival discharges only the "
            "left one: it emits `[transform left, right]`. Every other witness in "
            "this battery states its compound operand on the LEFT, so all ten of "
            "them elaborate against this rival unchanged (measured: each exits 1, "
            "i.e. none refutes it) — the position is genuinely unprobed without "
            "this case. Witness at op=ge / (const 1, nested `2 < 3`) reduces the "
            "rival's impl to a call whose SECOND argument is the raw `cmp` "
            "sub-node and refutes it against the pinned rebuilt `app` via "
            "`AstNode.noConfusion`; it fails on gold, whose second argument is "
            "that rebuilt `app`. Adds the seventh operator value (`ge`) and the "
            "only right-hand compound operand in the battery."
        ),
        "witness": _WIT_RIGHTNORECURSE,
    },
    {
        "id": "rival-call-flag-assign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CALLFLAGASSIGN,
        "refinement": (
            "Assigning the table lookup to a rebuilt call's flag, rather than "
            "combining it with the flag the call already carried, DISCARDS a flag "
            "that was already there. The faithful real patch only ever adds the "
            "flag, never clears one, so a sub-call that arrived already marked as "
            "non-evaluating stays marked even though its callee is not one of the "
            "names that receive the treatment. With the assignment, such a "
            "sub-expression is silently re-enabled for evaluation and the parsed "
            "object evaluates a part of itself — the same class of bug the report "
            "is about, reached from the other side. Correct on every callee IN the "
            "table and on every operand that arrives unflagged, which is every "
            "F2P input and every ordinary parser test — does NOT resolve."
        ),
        "rationale": (
            "REJECT from the DISJUNCTION in clause C6's flag half: the rebuild is "
            "`evalFalse || isNonEvaluatingFunc func`, and this rival computes "
            "`isNonEvaluatingFunc func`, losing the left disjunct. It rebuilds the "
            "arguments correctly and is right on every non-evaluating callee, so "
            "`rival-call-no-flag` and `rival-identity-on-call` do not reach it, and "
            "all ten other witnesses elaborate against it unchanged (measured: "
            "each exits 1). The witness is stated at the only input shape where "
            "the disjunction and the assignment differ: an ORDINARY callee "
            "(`g`, outside the table) that ALREADY carries the flag, under `==`. "
            "It reduces the rival's first argument to a call whose flag is `false` "
            "and exposes the clash with the pinned `true`; it fails on gold, where "
            "the pre-existing flag survives."
        ),
        "witness": _WIT_CALLFLAGASSIGN,
    },
    {
        "id": "rival-cmp-one-level",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CMPONELEVEL,
        "refinement": (
            "Rebuilding a nested comparison one level deep but not rebuilding "
            "that comparison's OWN operands stops the walk after a single step. "
            "The faithful real patch rebuilds each operand through the same "
            "dispatch, and that dispatch recurses on the comparison it finds, so "
            "the rewrite reaches every comparison at every depth; stopping after "
            "one level leaves the innermost comparison a raw comparison node, "
            "which collapses to a truth value when the rewritten tree is finally "
            "evaluated. Indistinguishable from the faithful patch on the F2P's "
            "own literals AND on every singly-nested comparison, so a battery "
            "that probes the recursion only one level deep accepts it: the "
            "parser tests that chain comparisons two deep FAIL — does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause C5's RECURSIVENESS. C5 pins the operands to "
            "`transform left` / `transform right`, and `transform` on a `cmp` "
            "rebuilds ITS operands too — a strictly stronger obligation than "
            "'the operand is rebuilt at all'. This rival discharges the weaker "
            "one: it emits the operand's relational call with the right name, "
            "order and flag, so it agrees with gold at every DEPTH-1 nested "
            "operand, which is the only depth `rival-no-recurse` and "
            "`rival-right-no-recurse` state. Measured: all eleven other "
            "witnesses in this battery elaborate against this rival unchanged "
            "(each exits 1, i.e. none refutes it). Witness at op=lt / "
            "(`(1 < 2) <= 3`, const 4) reduces the rival's impl to a first "
            "argument whose own first argument is the raw inner `cmp` and "
            "refutes it against the pinned fully-rebuilt `app` via "
            "`AstNode.noConfusion`; it fails on gold, which rebuilds all the way "
            "down. Adds the only depth-2 operand in the battery."
        ),
        "witness": _WIT_CMPONELEVEL,
    },
    {
        "id": "rival-call-first-arg-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CALLFIRSTARG,
        "refinement": (
            "Rebuilding only a call's FIRST argument leaves every later argument "
            "raw. The faithful real patch's walk over a call visits every child "
            "in every field, so a multi-argument call has all of its arguments "
            "rewritten; with only the head rebuilt, a comparison sitting in a "
            "second or later argument stays a raw comparison node and collapses "
            "to a truth value. Correct on every single-argument call, which is "
            "every F2P input and every ordinary parser test whose functions are "
            "unary — does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C6's argument half, at its ELEMENTWISE-ness: "
            "`transformArgs` maps `transform` over the WHOLE argument list, not "
            "just its head. Every call-shaped operand the battery's other C6 "
            "cases use (`rival-identity-on-call`, `rival-call-no-flag`, "
            "`rival-call-no-argrecurse`, `rival-call-flag-assign`) has exactly "
            "ONE argument, so this rival agrees with gold on all of them; it is "
            "observable only at a call of arity ≥ 2 whose LATER argument is "
            "compound. Measured: all eleven other witnesses elaborate against it "
            "unchanged (each exits 1). The witness uses an ORDINARY callee (`f`, "
            "outside the table) so the flag is identical on both sides and only "
            "the argument walk can be responsible: op=gt / (`f(1, 2 < 3)`, const "
            "4) reduces the rival's first argument to a call whose SECOND "
            "argument is the raw `cmp` and refutes it against the pinned rebuilt "
            "`app`; it fails on gold. Adds the only arity-2 operand in the "
            "battery."
        ),
        "witness": _WIT_CALLFIRSTARG,
    },
    {
        "id": "rival-none-branch-transforms",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NONETRANSFORMS,
        "refinement": (
            "Rewriting the operands of a comparison whose operator is NOT in the "
            "table changes a node the faithful real patch returns untouched. The "
            "faithful patch returns such a comparison unchanged — the whole "
            "node, operands included — so those comparisons behave exactly as "
            "they did before; rewriting inside them alters parser output for "
            "identity and membership tests whose operands happen to contain a "
            "comparison. Correct whenever such an operand is a bare literal or "
            "identifier, which is every F2P input, so it passes the F2P while "
            "breaking the pre-existing tests over non-relational comparisons — "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the UNRECOGNISED clause, at its full strength: the "
            "clause pins `result = AstNode.cmp left op right` over the SOURCE "
            "operands, not merely 'a `cmp` under the same operator'. "
            "`rival-over-convert`, the battery's only other `op=other` case, "
            "changes the OUTER constructor and states its witness at atomic "
            "operands — on which this rival is the identity — so it agrees with "
            "gold there and the operand fields of the `none` branch are "
            "otherwise unprobed. Measured: all eleven other witnesses elaborate "
            "against it unchanged (each exits 1). Witness at op=other / (nested "
            "`1 < 2`, const 3) reduces the rival's impl to a `cmp` whose LEFT "
            "field is the rebuilt `app \"Lt\" ...` and refutes it against the "
            "pinned raw sub-node via `AstNode.noConfusion`; it fails on gold, "
            "which returns the node untouched. Pairs a compound operand with the "
            "`other` operator, a combination no other case states."
        ),
        "witness": _WIT_NONETRANSFORMS,
    },
]
