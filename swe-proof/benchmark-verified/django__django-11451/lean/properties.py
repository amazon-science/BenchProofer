"""properties.py — G-PBT falsification battery for django__django-11451 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a positive control that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is replaced, so ``markers.same_spec``
holds and the ``theorem correct_credentialAuth`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one total function; three inputs; a three-component result)

  implementation_credentialAuth
      (name fallback secret : Option (List Char)) : AuthOutcome

  ``AuthOutcome`` carries the decision plus the TWO observable resource costs:
  ``user : Option User``, ``queries : Nat``, ``hasherCalls : Nat``.

  ``problem_spec_credentialAuth name fallback secret result`` splits on the pair
  ``(resolveName name fallback, secret)``:

    ABSENT ARM — either the resolved login name or the secret is absent:
        result.user = none  ∧  result.queries = 0  ∧  result.hasherCalls = 0
      i.e. the check is abandoned before ANY cost is incurred. Three independent
      top-level conjuncts, each separately attackable — and each separately
      ATTACKED (the third by weak-principal-without-credentials, since a rival
      that leaks a cost leaves the decision conjunct satisfied).

    PRESENT ARM — both present (``some login``, ``some pw``):
        result.queries = 1                                    (C1)
      and, split on the store lookup ``lookupUser login``:
        MISS arm:  result.user = none  ∧  result.hasherCalls = 1     (C2, C3)
        HIT  arm:  result.hasherCalls = checkHashCount u pw          (C4)
                 ∧ result.user =
                     (if passwordMatches u pw && userAllowed u
                      then some u else none)                        (C5)

  So the postcondition has SIX independently attackable top-level components
  across its arms, and every one of them is pinned to the inputs — there is no
  unconstrained result field in any branch. That total pinning is this carrier's
  analogue of nagini's frame obligation (see below).

  ``lookupUser`` / ``passwordMatches`` / ``userAllowed`` / ``checkHashCount``
  are declared signature-only (UNCHANGED callee observables, referenced
  identically in the specification and the implementation). They are GROUNDED in
  the function's own arguments — a rival that wants a principal returned must
  make the store lookup and the two decisions come out that way; there is no
  separate answer key to echo.

HOW THE NAGINI CLASSES LAND ON THIS CARRIER

  * THE CHANGE (nagini ``uniq-no-guard-leak``, its F2P discriminator) — PORTS
    DIRECTLY and is the load-bearing rival here too: drop the
    abandon-before-any-cost behavior, so an absent credential still incurs a
    store query (and, when a secret was supplied, a hash). Refuted on the ABSENT
    arm, where the spec pins all three cost/decision components to zero.

  * PARTIAL-DOMAIN (nagini ``uniq-guard-identifier-only`` /
    ``uniq-guard-secret-only``) — PORT DIRECTLY as the two half-abandon rivals.
    Each is correct on one absent sub-domain and wrong on the OTHER, so each is
    refuted at an input the full-leak rival is ALSO wrong at — which is why each
    gets its own witness at its own distinguishing point rather than sharing
    one: the full-leak rival is refuted where NEITHER credential is present (a
    point at which both half-abandon rivals are correct), and each half-abandon
    rival is refuted on precisely the absent sub-domain it fails to cover.

  * CONTROL-FLOW / COST (nagini ``uniq-verify-only-on-recognised``, the
    uniform-timing rival) — PORTS as the miss-arm hash rival: skip the
    uniform-timing hash on the store-miss path (C3). Nagini's ``uniq-double-
    lookup`` cost over-count ports as the double-query rival (C1), and this
    carrier admits one MORE cost rival nagini's did not model: nagini folded the
    hit-path cost into a constant, while this carrier models it as the check's
    own inherent cost, so an extra hit-path hash is separately attackable (C4).

  * VALUE-LEVEL (nagini ``uniq-wrong-identity`` / ``uniq-skip-secret-check``) —
    PORT DIRECTLY, attacking C5. ``uniq-skip-secret-check`` SPLITS on this
    carrier: nagini folded the secret match and the permission decision into one
    opaque predicate, whereas here they are two separate conjuncts, so dropping
    each is a distinct rival refuted on a distinct sub-domain (a wrong secret vs.
    a principal not permitted to authenticate).

  * FRAME / PERMISSION MUTATION (nagini's #1 class, mandatory there because the
    inputs are held at fractional read-only permission) — VACUOUS as a
    PERMISSION attack. Lean is referentially transparent: the three inputs are
    immutable values, there is no fractional permission to violate and no
    aliasing to overwrite, so no substitute is fabricated. The SEMANTIC content
    of nagini's frame obligation — "no result component is left free for a wrong
    impl to fill in" — survives as the spec's total pinning of all three
    ``AuthOutcome`` components in every arm, and that IS attacked: the rivals
    below hit ``queries``, ``hasherCalls`` and ``user`` separately, ON EACH ARM.
    The last part is load-bearing and was audited by machine rather than by
    argument: a cost rival that leaves ``user = none`` intact demonstrates the
    arm's cost conjuncts only, so the absent arm's and the store-miss arm's
    ``user`` pins get their own rivals
    (``weak-principal-without-credentials`` / ``weak-principal-on-store-miss``),
    each refuted at a point where the COST conjuncts of its arm still hold.

  * DIVERGENCE / NON-TERMINATION — genuinely VACUOUS on lean, and for the
    carrier's reason rather than a spec hole: ``implementation_credentialAuth``
    is a total Lean ``def``, so a diverging implementation cannot be written at
    all and there is nothing for the spec to admit. (Contrast the velvet lane,
    where ``the corpus-wide termination-semantics finding`` records this as a real spec hole under
    partial-correctness semantics; that finding does not apply to this backend.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the
    function's own arguments and the UNCHANGED callee observables applied to
    them; there is no answer-key term an impl could echo instead of doing the
    work. Covered instead by the cheapest-honest positive controls.

  * ADMISSIBILITY / PRECOND-TOO-STRONG — SHIPPED, as
    ``admiss-obligation-at-abandoned-inputs``. It is true that
    ``correct_credentialAuth`` quantifies over ALL ``(name, fallback, secret)``
    with NO precondition hypothesis, but that does not make the lane vacuous: the
    analogue on a total carrier is the obligation being UNSATISFIABLE at exactly
    an input the demanded behavior is asserted at, which a positive that
    discharges the obligation AT that concrete input — by evaluation, as a
    ``have``, before closing the frozen obligation verbatim — tests directly.
    Nagini's ``admiss-fresh-checker`` asserted the counters'
    permission/non-negativity precondition for a freshly built checker; the
    faithful counterpart here is the abandoning arm's three cost/decision
    conjuncts being jointly satisfiable at the four abandoned-check inputs, and
    that is what the case checks.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation, so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet that states the
spec predicate at a concrete input and shows the rival's own result violates it.
Two techniques are used, per the carrier:

  * WHERE THE CARRIER IS TRANSPARENT — the absent-arm and the ``queries``
    component are decided by literals alone, because the spec's demand there is
    a constant. For the ``queries`` component the store lookup still appears in
    the rival's term, but BOTH of its arms report the same query count, so the
    witness case-splits on the lookup (``cases hl : lookupUser …``) and refutes
    both arms — no assumption about the lookup's value is needed.

  * WHERE IT IS NOT — the miss-arm and hit-arm clauses hold only at a point the
    callee observables select, so those witnesses CONDITION on the carrier
    instead of computing it: one hypothesis per observable term, no more than
    the refutation needs, e.g. ``(u : User) (h : lookupUser ['a'] = some u)
    (hp : passwordMatches u ['p'] = false)``. Each such hypothesis constrains a
    DIFFERENT term (or a different argument), so the assumptions are jointly
    satisfiable — deliberately never two hypotheses about the same term, which
    is the shape that would make the refutation follow from a contradiction.
    Two of the witnesses need no assumption about a callee's VALUE at all: the
    identity rival is refuted by ``u.uid + 1 ≠ u.uid`` and the extra-hash rival
    by ``checkHashCount u pw + 1 ≠ checkHashCount u pw``, both pure arithmetic
    over an unconstrained term.

BINDER COVERAGE. Every input binder of the spec predicate is varied across the
reject witnesses, so no rival could mishandle one input and go unnoticed:

  * ``name`` — absent in the full-leak / secret-only / hit-via-fallback
    witnesses, present in the others.
  * ``fallback`` — absent in most; PRESENT and load-bearing in four witnesses
    (``weak-cost-when-secret-absent`` resolves the login name THROUGH the
    fallback on the absent arm, ``weak-return-without-secret-check`` resolves it
    through the fallback on the present arm, and the two AUDIT-ADDITION rivals
    attack the resolution step's CONTENT — ``weak-ignore-fallback-name`` where
    the fallback is the only name supplied, ``weak-prefer-fallback-name`` where
    BOTH are supplied and only the preference order distinguishes them, the one
    input shape no other witness in the battery uses).
  * ``secret`` — absent in the full-leak, name-resolved-only and
    absent-arm-principal witnesses, present in every present-arm witness, and
    its VALUE is varied (``['p']`` / ``['q']``) so the hit-arm clauses are not
    pinned to one secret.
  * the login-name value is varied across ``['a'] … ``['j']`` so no clause is
    demonstrated at a single store key.

Each rival is also refuted at a point where the conjuncts it does NOT attack
still HOLD, so no witness passes by riding a sibling clause's failure. That is
what separates the two ``user``-pin rivals from the cost rivals on the same arms.

``pts`` = 13 distinct input points, one per rival; no two rivals share a witness.

A NOTE ON THE SIMP SET, and why every witness carries ``bind, pure``. The
implementation is written in ``Id.run do`` notation, so its result appears in a
goal as ``pure { user := …, queries := …, hasherCalls := … }`` — an application
whose FIELD PROJECTIONS do not reduce under ``simp [Id.run]`` alone. A witness
that unfolds only ``Id.run`` therefore leaves goals of the form
``(pure {…}).queries = 0 → …`` in which no projection has been computed, and such
a goal is unprovable for BOTH sides for a reason that has nothing to do with the
claim: it was measured that the witness and a FORGERY asserting the exact
opposite (the frozen solution is CORRECT at that point) failed against the frozen
solution with the same unreduced goal, so the gold-side exit code carried no
information about the claim. Adding ``bind, pure`` to each simp set makes the
projections reduce; the same forgery pair then separates cleanly (the flipped
claim ELABORATES against the frozen solution, exit 0, while the witness fails
with ``unsolved goals ⊢ False`` — a decided refutation). Do not drop those two
lemmas from a witness's simp set.

AXIOM LANE: EMPTY. meta.json records ``axioms == []`` and
``deep_model_references == []`` (G-AX is a skip stub: the four callee observables
are signature-only and referenced identically in the specification and the
implementation, and the changed behavior is modeled deeply as control flow, not
axiomatized). Nagini's AXIOM_TESTS are therefore dropped: that lane is G-AX's
job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "django__django-11451"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of the region it names, verbatim from
# the frozen Solution.lean and unique in the file, so every replacement lands
# entirely inside the region it means to edit.
# ---------------------------------------------------------------------------
_IMPL_GOLD = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          -- No principal carries this name: perform one secret-hashing operation
          -- to keep the timing uniform, and return no principal.
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          -- Checking the supplied secret performs whatever hashing the check
          -- itself requires (once in the ordinary case, none when the stored
          -- secret is unusable).
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- A credential is absent: abandon the check before touching the store or
      -- the secret hasher.
      return { user := none, queries := 0, hasherCalls := 0 }"""

_PROOF_GOLD = """  intro name fallback secret
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  by_cases hn : name.isNone
  · simp only [hn, if_true]
    cases fallback with
    | none => cases secret <;> simp
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]
  · simp only [hn]
    cases hnm : name with
    | none => simp [hnm] at hn
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]"""

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _rival(impl):
    """A reject variant: only the impl region changes (the frozen tactic script
    is left exactly as it is — a rival does not get to reshape the proof)."""
    return _swap(_BASE, _IMPL_GOLD, impl)


def _positive(impl, proof):
    """A verify variant: a structurally different CORRECT impl plus a proof that
    closes for THAT shape. The theorem statement is untouched."""
    return _swap(_swap(_BASE, _IMPL_GOLD, impl), _PROOF_GOLD, proof)


# ===========================================================================
# POSITIVE CONTROLS (soundness; must verify, else SPEC-TOO-STRONG)
# ===========================================================================

# pos-resolve-and-reorder: two independent reshapes at once. (a) The login name
# is resolved by the shared resolution helper applied directly, instead of the
# frozen impl's mutable-local rebinding; (b) the two-credential case split is
# taken in the OPPOSITE order — the secret first, the resolved name second. All
# six outcome components are unchanged, so every clause holds; the tactic script
# is rewritten to follow the new split (the theorem statement is byte-identical).
_POS_REORDER = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let login := resolveName name fallback
  match secret, login with
  | some pw, some loginName =>
      match lookupUser loginName with
      | none =>
          -- No principal carries this name: one secret-hashing operation keeps
          -- the timing uniform, and no principal is returned.
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- A credential is absent: abandon before touching the store or the hasher.
      return { user := none, queries := 0, hasherCalls := 0 }"""

_POS_REORDER_PROOF = """  intro name fallback secret
  unfold problem_spec_credentialAuth implementation_credentialAuth
  simp only [Id.run, bind, pure]
  cases hs : secret with
  | none => cases hr : resolveName name fallback <;> simp [hr, hs]
  | some pw =>
    cases hr : resolveName name fallback with
    | none => simp [hr, hs]
    | some login =>
      cases hl : lookupUser login with
      | none => simp [hr, hs, hl]
      | some u =>
        by_cases hp : passwordMatches u pw && userAllowed u <;>
          simp [hr, hs, hl, hp]"""

# pos-merge-decision: collapse the frozen impl's two store-hit returns (one per
# side of the secret-and-permission decision) into a SINGLE return whose
# principal field carries the decision as a conditional expression. The cost
# fields are shared between the two former branches, which is exactly why the
# merge is behavior-preserving. Same guard, same costs, same decision.
_POS_MERGE = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          -- No principal carries this name: one secret-hashing operation keeps
          -- the timing uniform, and no principal is returned.
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          -- One return: the hashing cost of the check is the same either way,
          -- and the principal is returned exactly on the accepting decision.
          return { user := if passwordMatches u pw && userAllowed u then some u
                           else none,
                   queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- A credential is absent: abandon before touching the store or the hasher.
      return { user := none, queries := 0, hasherCalls := 0 }"""

_POS_MERGE_PROOF = """  intro name fallback secret
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  by_cases hn : name.isNone
  · simp only [hn, if_true]
    cases fallback with
    | none => cases secret <;> simp
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u => simp [hl]
  · simp only [hn]
    cases hnm : name with
    | none => simp [hnm] at hn
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u => simp [hl]"""


# ===========================================================================
# UNIQUENESS rivals (must reject, else SPEC-TOO-WEAK)
# ===========================================================================

# weak-cost-on-absent-credential — THE load-bearing rival (nagini's
# uniq-no-guard-leak; identical in content to Solution_prepatch.lean's impl).
# The check is never abandoned: the store is queried on every input, and the
# uniform-timing hash runs whenever a secret was supplied. Wrong on the WHOLE
# absent arm.
_WEAK_NO_ABANDON = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login with
  | some loginName =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1,
                   hasherCalls := if secret.isSome then 1 else 0 }
      | some u =>
          match secret with
          | none =>
              return { user := none, queries := 1, hasherCalls := 0 }
          | some pw =>
              if passwordMatches u pw && userAllowed u then
                return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
              else
                return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | none =>
      return { user := none, queries := 1,
               hasherCalls := if secret.isSome then 1 else 0 }"""

_W_NO_ABANDON_WITNESS = """example : ¬ problem_spec_credentialAuth none none none
    (implementation_credentialAuth none none none) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure]"""

# weak-cost-when-secret-absent (partial domain): the check is abandoned when the
# resolved login name is absent, but NOT when the secret is absent. Correct
# everywhere the full-leak rival is, EXCEPT it still spends a store query on the
# name-present / secret-absent sub-domain.
_WEAK_SECRET_ABSENT = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login with
  | none =>
      return { user := none, queries := 0, hasherCalls := 0 }
  | some loginName =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1,
                   hasherCalls := if secret.isSome then 1 else 0 }
      | some u =>
          match secret with
          | none =>
              return { user := none, queries := 1, hasherCalls := 0 }
          | some pw =>
              if passwordMatches u pw && userAllowed u then
                return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
              else
                return { user := none, queries := 1, hasherCalls := checkHashCount u pw }"""

# The login name is resolved THROUGH the fallback here, so the witness also
# exercises the resolution step. Both store-lookup arms report the same query
# count, so no assumption about the lookup is needed — the split is enough.
_W_SECRET_ABSENT_WITNESS = """example : ¬ problem_spec_credentialAuth none (some ['a']) none
    (implementation_credentialAuth none (some ['a']) none) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  cases hl : lookupUser ['a'] with
  | none => simp [Id.run, bind, pure, hl]
  | some u => simp [Id.run, bind, pure, hl]"""

# weak-cost-when-name-absent (partial domain, mirror): the check is abandoned
# when the secret is absent, but NOT when the resolved login name is absent — a
# null name still reaches the store and the uniform-timing hash.
_WEAK_NAME_ABSENT = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match secret with
  | none =>
      return { user := none, queries := 0, hasherCalls := 0 }
  | some pw =>
      match login with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some loginName =>
          match lookupUser loginName with
          | none =>
              return { user := none, queries := 1, hasherCalls := 1 }
          | some u =>
              if passwordMatches u pw && userAllowed u then
                return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
              else
                return { user := none, queries := 1, hasherCalls := checkHashCount u pw }"""

_W_NAME_ABSENT_WITNESS = """example : ¬ problem_spec_credentialAuth none none (some ['p'])
    (implementation_credentialAuth none none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure]"""

# weak-no-uniform-timing-hash (control-flow / cost): on the store-MISS path the
# uniform-timing hash is skipped, so a name no principal carries costs zero
# hashes while a name that is found costs the check's own. Attacks C3.
_WEAK_NO_TIMING_HASH = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 0 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# The miss arm is selected by the store lookup, which no literal input decides,
# so the refutation is stated at a point described by ONE hypothesis about ONE
# term: the store carries no principal under this name. Satisfiable by
# construction (nothing else constrains that term).
_W_NO_TIMING_HASH_WITNESS = """example (h : lookupUser ['b'] = none) :
    ¬ problem_spec_credentialAuth (some ['b']) none (some ['p'])
        (implementation_credentialAuth (some ['b']) none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure, h]"""

# weak-double-query (cost over-count; nagini's uniq-double-lookup): the store is
# queried twice on the both-present path. Attacks C1.
_WEAK_DOUBLE_QUERY = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 2, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 2, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 2, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# C1 holds in BOTH lookup arms, so splitting on the lookup refutes the rival
# without assuming anything about it.
_W_DOUBLE_QUERY_WITNESS = """example : ¬ problem_spec_credentialAuth (some ['c']) none (some ['p'])
    (implementation_credentialAuth (some ['c']) none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  cases hl : lookupUser ['c'] with
  | none => simp [hl]
  | some u => by_cases hp : passwordMatches u ['p'] && userAllowed u <;> simp [hl, hp]"""

# weak-extra-hash-on-hit (cost over-count on the OTHER cost clause): when a
# principal IS found, one hash more than the check itself requires is performed.
# Attacks C4 — a clause nagini's carrier folded into a constant and so never
# separately modeled.
_WEAK_EXTRA_HASH = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1,
                     hasherCalls := checkHashCount u pw + 1 }
          else
            return { user := none, queries := 1,
                     hasherCalls := checkHashCount u pw + 1 }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# ONE hypothesis, about the store lookup only — the refutation needs no
# assumption about the hashing cost's VALUE, since `n + 1 ≠ n` for every `n`.
_W_EXTRA_HASH_WITNESS = """example (u : User) (h : lookupUser ['d'] = some u) :
    ¬ problem_spec_credentialAuth (some ['d']) none (some ['p'])
        (implementation_credentialAuth (some ['d']) none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  by_cases hp : passwordMatches u ['p'] && userAllowed u <;> simp [h, hp]"""

# weak-return-without-secret-check (value level; nagini's
# uniq-skip-secret-check): when a principal is found it is returned WITHOUT
# consulting the supplied secret at all. Attacks C5 on the wrong-secret
# sub-domain.
_WEAK_SKIP_SECRET = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# Two hypotheses about two DIFFERENT terms (the store lookup, and the
# secret-match decision at the found principal), so they are jointly
# satisfiable. The login name is resolved through the FALLBACK, exercising the
# resolution step on the present arm.
_W_SKIP_SECRET_WITNESS = """example (u : User) (h : lookupUser ['e'] = some u)
    (hp : passwordMatches u ['q'] = false) :
    ¬ problem_spec_credentialAuth none (some ['e']) (some ['q'])
        (implementation_credentialAuth none (some ['e']) (some ['q'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure, h, hp]"""

# weak-ignore-permission (value level, the OTHER half of C5's decision): the
# secret is checked, but whether the found principal is permitted to
# authenticate is ignored. A near-miss for weak-return-without-secret-check —
# it agrees with the specified behavior wherever the secret does not match, so
# it is refuted at the input that distinguishes them: a MATCHING secret on a
# principal that is not permitted.
_WEAK_IGNORE_PERMISSION = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# Three hypotheses, each about a DIFFERENT term (the lookup, the secret-match
# decision, the permission decision), so they are jointly satisfiable.
_W_IGNORE_PERMISSION_WITNESS = """example (u : User) (h : lookupUser ['a'] = some u)
    (hp : passwordMatches u ['p'] = true) (ha : userAllowed u = false) :
    ¬ problem_spec_credentialAuth (some ['a']) none (some ['p'])
        (implementation_credentialAuth (some ['a']) none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure, h, hp, ha]"""

# weak-principal-without-credentials (the ABSENT arm's `user` conjunct, which no
# other rival perturbs): the check IS abandoned before any cost — both cost
# conjuncts hold — but a principal is handed back anyway. Machine-checked that
# every other absent-arm rival returns `none` on that arm, so this conjunct of
# the specification was demonstrated by no case before this one.
_WEAK_ABSENT_PRINCIPAL = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- Abandoned before any cost, but a principal is returned regardless.
      return { user := some { uid := 0 }, queries := 0, hasherCalls := 0 }"""

# A FRESH absent-arm point: the login name is PRESENT and the secret absent — the
# sub-domain no other absent-arm witness states its refutation at (the full-leak
# witness uses both-absent, the mirror uses secret-present). Decidable at
# literals: the store is never consulted on this path.
_W_ABSENT_PRINCIPAL_WITNESS = """example : ¬ problem_spec_credentialAuth (some ['g']) none none
    (implementation_credentialAuth (some ['g']) none none) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure]"""

# weak-principal-on-store-miss (C2, the miss arm's `user = none` conjunct — the
# other component no rival perturbed): the uniform-timing hash still runs and the
# query count is right, but a principal is returned for a name the store does not
# carry. C3 holds, so this isolates C2.
_WEAK_MISS_PRINCIPAL = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          -- The uniform-timing hash still runs, but a principal is invented for
          -- a name the store does not carry.
          return { user := some { uid := 0 }, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# ONE hypothesis about ONE term (this name is not carried), at a login-name value
# no other witness uses, selecting the miss arm the refutation lives on.
_W_MISS_PRINCIPAL_WITNESS = """example (h : lookupUser ['f'] = none) :
    ¬ problem_spec_credentialAuth (some ['f']) none (some ['p'])
        (implementation_credentialAuth (some ['f']) none (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure, h]"""

# weak-wrong-principal (value level; nagini's uniq-wrong-identity): on the
# accepting decision a principal OTHER than the one the store returned is
# handed back. Attacks C5's identity pin.
_WEAK_WRONG_PRINCIPAL = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some { uid := u.uid + 1 }, queries := 1,
                     hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# Three hypotheses, each about a DIFFERENT term, only SELECT the accepting
# decision; the refutation itself is arithmetic on the returned identity and
# assumes nothing about any callee's value. The principal is destructured first
# so the identity disequality is decided structurally on its one field.
_W_WRONG_PRINCIPAL_WITNESS = """example (u : User) (h : lookupUser ['b'] = some u)
    (hp : passwordMatches u ['q'] = true) (ha : userAllowed u = true) :
    ¬ problem_spec_credentialAuth (some ['b']) none (some ['q'])
        (implementation_credentialAuth (some ['b']) none (some ['q'])) := by
  obtain ⟨n⟩ := u
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  simp [h, hp, ha]"""

# weak-ignore-fallback-name (AUDIT ADDITION): the resolution step is dropped
# altogether — the fallback name is never read, so a check that supplies only the
# keyword name is treated as having no login name at all and is abandoned. Wrong
# on the whole name-absent / fallback-present sub-domain, which every rival above
# leaves unattacked: the eleven original rivals all reproduce the resolution step
# verbatim, so `resolveName`'s own content was demonstrated by no case.
_WEAK_IGNORE_FALLBACK = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  match name, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# C1 (`result.queries = 1`) is demanded in BOTH lookup arms once the name
# resolves, so the witness splits on the store lookup and refutes each arm
# without assuming anything about the store. No hypothesis at all, hence no
# consistency question.
_W_IGNORE_FALLBACK_WITNESS = """example : ¬ problem_spec_credentialAuth none (some ['h']) (some ['p'])
    (implementation_credentialAuth none (some ['h']) (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  cases hl : lookupUser ['h'] with
  | none => simp [hl]
  | some u => by_cases hp : passwordMatches u ['p'] && userAllowed u <;> simp [hl, hp]"""

# weak-prefer-fallback-name (AUDIT ADDITION, and a genuine NEAR-MISS of the case
# above): the resolution step is present but its PREFERENCE is inverted — the
# fallback wins whenever it is supplied, instead of only when the positional name
# is absent. Agrees with the specified behavior on every input where at most one
# of the two names is supplied, so it is refuted at the one input that
# distinguishes them: BOTH names present, resolving to different principals.
_WEAK_PREFER_FALLBACK = """def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let login := if fallback.isNone then name else fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      return { user := none, queries := 0, hasherCalls := 0 }"""

# Four hypotheses, each about a DIFFERENT term — the store at TWO different keys
# (so the two equations constrain different applications, never the same one),
# plus the two decisions at the principal the second key carries. Jointly
# satisfiable by construction. The refutation then needs no assumption about any
# cost: the specification pins the outcome to what the POSITIONAL name resolves
# to, and the rival reports what the fallback resolves to instead.
_W_PREFER_FALLBACK_WITNESS = """example (u : User) (h1 : lookupUser ['i'] = none)
    (h2 : lookupUser ['j'] = some u)
    (hp : passwordMatches u ['p'] = true) (ha : userAllowed u = true) :
    ¬ problem_spec_credentialAuth (some ['i']) (some ['j']) (some ['p'])
        (implementation_credentialAuth (some ['i']) (some ['j']) (some ['p'])) := by
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp [Id.run, bind, pure, h1, h2, hp, ha]"""

# admiss-obligation-at-abandoned-inputs (AUDIT ADDITION). The impl region stays
# BYTE-IDENTICAL to the frozen one; only the proof region changes, by discharging
# the frozen obligation's own body BY EVALUATION at four concrete abandoned-check
# inputs before closing the general obligation verbatim.
_ADM_PROOF = """  -- ADMISSIBILITY. `correct_credentialAuth` binds every input with no
  -- precondition hypothesis, so the analogue of a too-strong precondition on
  -- this total carrier is the obligation being UNSATISFIABLE at exactly the
  -- inputs the demanded behavior is asserted at. Each `have` below is the frozen
  -- obligation's own body instantiated at one such point and closed by
  -- evaluation: if the absent arm's three conjuncts could not jointly hold there
  -- — if, say, the arm demanded both zero cost and a returned principal — no
  -- implementation whatsoever could satisfy the obligation on that sub-domain,
  -- and the uniqueness lane's rejections there would attest to an unsatisfiable
  -- clause rather than to a wrong rival. All four combinations of the two
  -- credentials' absence that reach the abandoning arm are covered, including
  -- the one that reaches it THROUGH the resolution step (fallback present,
  -- secret absent).
  have _adm_no_credentials :
      problem_spec_credentialAuth none none none
        (implementation_credentialAuth none none none) := by
    unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
    simp [Id.run, bind, pure]
  have _adm_name_only :
      problem_spec_credentialAuth (some ['a']) none none
        (implementation_credentialAuth (some ['a']) none none) := by
    unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
    simp [Id.run, bind, pure]
  have _adm_secret_only :
      problem_spec_credentialAuth none none (some ['p'])
        (implementation_credentialAuth none none (some ['p'])) := by
    unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
    simp [Id.run, bind, pure]
  have _adm_fallback_only :
      problem_spec_credentialAuth none (some ['a']) none
        (implementation_credentialAuth none (some ['a']) none) := by
    unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
    simp [Id.run, bind, pure]
""" + _PROOF_GOLD


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) --------------
    {
        "id": "pos-resolve-and-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_REORDER, _POS_REORDER_PROOF),
        "rationale":
            "structurally DIFFERENT but behaviorally identical: the login name is "
            "resolved by applying the shared resolution helper directly instead of "
            "rebinding a mutable local, and the two-credential case split is taken "
            "in the opposite order (secret first, resolved name second). All six "
            "outcome components are produced unchanged in every arm, so the absent "
            "arm still reports zero/zero/none and the present arm still reports one "
            "query, the uniform-timing hash on a store miss, and the check's own "
            "hashing cost plus the accepting decision on a store hit. The proof is "
            "rewritten to follow the new split (the theorem STATEMENT is "
            "byte-identical and no lemma is added). If this cannot verify the spec "
            "over-constrains the shape rather than the behavior => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-merge-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_MERGE, _POS_MERGE_PROOF),
        "rationale":
            "a second, independent reshape: the two store-hit returns are collapsed "
            "into ONE return whose principal field carries the accept/reject "
            "decision as a conditional expression. This is behavior-preserving "
            "precisely because both former branches reported the same two costs, so "
            "C1/C4 are untouched and C5 is produced in exactly the conditional form "
            "the specification states. Chosen to keep the proof close to the frozen "
            "one (the hit arm's case split simply disappears); must verify, else "
            "SPEC-TOO-STRONG.",
    },

    # ---- uniqueness rivals (must reject; else SPEC-TOO-WEAK) ---------------
    {
        "id": "weak-cost-on-absent-credential",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NO_ABANDON),
        "witness": _W_NO_ABANDON_WITNESS,
        "rationale":
            "attacks the ABSENT arm's QUERY conjunct. The rival never abandons the "
            "check: the store is queried on every input, so at name absent / "
            "fallback absent / secret absent it reports one query where the "
            "specification pins `result.queries = 0`. Machine-checked at that "
            "point, the rival's whole outcome is "
            "`{user := none, queries := 1, hasherCalls := 0}` (confirmed by an "
            "`rfl` build against the rival), so `result.queries = 0` is the ONE "
            "conjunct violated there: with no secret supplied the rival performs "
            "no hash either, and it returns no principal on any absent-arm input "
            "(also machine-checked, for every fallback and secret). The "
            "hasherCalls conjunct on the absent arm is attacked by "
            "weak-cost-when-name-absent instead, and the absent arm's `user` pin "
            "by weak-principal-without-credentials. Refuted at the point where "
            "NEITHER credential is present — an input at which both half-abandon "
            "rivals below are correct, so this witness is this rival's alone. "
            "Fully decidable at literals: nothing about the store is consulted on "
            "the absent-name path.",
        "refinement":
            "this is the pre-change behavior itself. Its faithful real patch is the "
            "unguarded credential check: with no credentials supplied it still "
            "issues one store query (a lookup on a null name) and, when a secret "
            "was supplied, still runs the hasher once. The F2P test asserts, for "
            "each of the no-credentials / name-only / secret-only cases, that ZERO "
            "queries are issued and the hasher counter stays at zero; the "
            "unguarded code issues a query in all three and FAILS the zero-query "
            "assertion (the zero-hasher assertion additionally fails only in the "
            "secret-supplied case), so it does NOT resolve — a verifying rival "
            "here would be a true verify-does-not-imply-resolve break.",
    },
    {
        "id": "weak-cost-when-secret-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_SECRET_ABSENT),
        "witness": _W_SECRET_ABSENT_WITNESS,
        "rationale":
            "partial-domain attack on the ABSENT arm: the rival abandons only when "
            "the resolved login name is absent, so it is correct on that "
            "sub-domain but still spends a store query when the name is present and "
            "the SECRET is absent — one query against the specified "
            "`result.queries = 0`. Refuted "
            "exactly there, at a point where the full-leak rival is also wrong but "
            "the mirror rival is correct, so the sub-domain this case claims is the "
            "one the witness demonstrates. The witness resolves the login name "
            "THROUGH the fallback (name absent, fallback present), exercising the "
            "resolution step on the absent arm; it splits on the store lookup "
            "because both of its arms report the same query count, so no assumption "
            "about the store is needed.",
        "refinement":
            "its faithful real patch is the half-guard: abandon on a missing login "
            "name only, leaving a missing secret to fall through. The F2P test's "
            "name-only case (a name supplied, no secret) then still reaches the "
            "store and issues a query, failing that subtest's zero-query "
            "assertion, so it does NOT resolve.",
    },
    {
        "id": "weak-cost-when-name-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NAME_ABSENT),
        "witness": _W_NAME_ABSENT_WITNESS,
        "rationale":
            "the mirror partial-domain attack on the ABSENT arm: the rival abandons "
            "only when the secret is absent, so a resolved login name that is "
            "absent still reaches the store and the uniform-timing hash — one "
            "query and one hash against the specified `result.queries = 0` and "
            "`result.hasherCalls = 0`. Refuted at secret "
            "present / name and fallback both absent, the complementary sub-domain "
            "to the case above, so the two near-misses are demonstrated at "
            "different points rather than sharing one. Decidable at literals.",
        "refinement":
            "its faithful real patch is the opposite half-guard: abandon on a "
            "missing secret only. The F2P test's secret-only case (a secret "
            "supplied, no name) then still issues the null-name store query and "
            "runs the uniform-timing hasher, failing both that subtest's zero-query "
            "assertion and its zero-hasher-call assertion, so it does NOT resolve.",
    },
    {
        "id": "weak-no-uniform-timing-hash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NO_TIMING_HASH),
        "witness": _W_NO_TIMING_HASH_WITNESS,
        "rationale":
            "attacks C3 (the miss arm's hasherCalls = 1) on the both-present "
            "sub-domain where the store carries no principal under the resolved "
            "name: the rival reports hasherCalls = 0 there, so the cost of a check "
            "reveals whether the name was found. The miss arm is selected by the "
            "store lookup, which no literal decides, so the witness CONDITIONS on "
            "the carrier with a single hypothesis about a single term (this name is "
            "not carried) — weak enough to be jointly satisfiable and exactly the "
            "sub-domain the rival is wrong on.",
        "refinement":
            "its faithful real patch drops the uniform-timing hash the "
            "not-found branch performs. A PASS_TO_PASS test pins the hasher "
            "counter at exactly one for BOTH an existing and a non-existent name; "
            "with the not-found branch performing zero hashes that assertion fails, "
            "so it does NOT resolve (and it re-introduces the very timing leak that "
            "branch exists to close).",
    },
    {
        "id": "weak-double-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_DOUBLE_QUERY),
        "witness": _W_DOUBLE_QUERY_WITNESS,
        "rationale":
            "attacks C1 (the present arm's `result.queries = 1`) directly: the "
            "rival reports "
            "two store queries on the both-present path. C1 holds in BOTH arms of "
            "the store lookup, so the witness splits on the lookup and refutes each "
            "arm without assuming anything about the store — this is the component "
            "of the outcome that stays transparent even though the callee is not.",
        "refinement":
            "its faithful real patch issues two store queries per credential check. "
            "The query counts the auth tests pin (the F2P zero-query assertions on "
            "the abandoned paths, and the surrounding assertNumQueries-style "
            "expectations on the ordinary paths) would double on every "
            "both-present check, so it does NOT resolve.",
    },
    {
        "id": "weak-extra-hash-on-hit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_EXTRA_HASH),
        "witness": _W_EXTRA_HASH_WITNESS,
        "rationale":
            "attacks C4 (the hit arm's hasherCalls = the check's own inherent cost) "
            "— the second, independent cost clause, which nagini's carrier folded "
            "into a constant and therefore never modeled separately. The rival "
            "performs one hash MORE than the check requires. The witness needs only "
            "ONE hypothesis, about the store lookup, because the refutation is pure "
            "arithmetic on the cost term (one more than a quantity is never that "
            "quantity) and so assumes nothing about the cost's value.",
        "refinement":
            "its faithful real patch performs an extra hashing operation on the "
            "found-principal path. A PASS_TO_PASS test pins the hasher counter at "
            "exactly one for an existing name; two hashes fail that equality, so it "
            "does NOT resolve.",
    },
    {
        "id": "weak-return-without-secret-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_SKIP_SECRET),
        "witness": _W_SKIP_SECRET_WITNESS,
        "rationale":
            "attacks C5 (the hit arm's decision) by returning the found principal "
            "unconditionally — anyone whose name is carried by the store is "
            "authenticated. Refuted on the sub-domain where the supplied secret does "
            "NOT match: the specification pins the result to none there, the rival "
            "hands back the principal. Two hypotheses, each about a DIFFERENT term "
            "(the lookup; the secret-match decision at the found principal), so they "
            "are jointly satisfiable. The login name is resolved through the "
            "fallback, so this witness also exercises the resolution step on the "
            "PRESENT arm.",
        "refinement":
            "its faithful real patch returns the found principal without consulting "
            "the secret match or the permission decision, so a stored principal "
            "authenticates under ANY secret. The PASS_TO_PASS authentication tests "
            "that require a wrong secret to be refused (and an unpermitted "
            "principal to be refused) would then see a successful authentication "
            "where they assert failure, so it does NOT resolve.",
    },
    {
        "id": "weak-ignore-permission",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_IGNORE_PERMISSION),
        "witness": _W_IGNORE_PERMISSION_WITNESS,
        "rationale":
            "the OTHER half of C5's decision, and a genuine NEAR-MISS of the case "
            "above: this rival does consult the secret and is therefore correct "
            "wherever the secret does not match, so it must be refuted at the input "
            "that distinguishes the two — a MATCHING secret on a principal that is "
            "not permitted to authenticate, where the specification pins the result "
            "to none and the rival returns the principal. Three hypotheses, each "
            "about a DIFFERENT term (lookup, secret-match, permission), jointly "
            "satisfiable. Nagini's carrier folded these two decisions into one "
            "opaque predicate, so this split is a refinement the lean carrier makes "
            "attackable.",
        "refinement":
            "its faithful real patch checks the secret but drops the "
            "may-this-principal-authenticate half of the condition, so a principal "
            "that is not permitted to authenticate is returned on a correct secret. "
            "A PASS_TO_PASS test asserts that such a principal is NOT authenticated "
            "by this backend (that behavior is the province of the "
            "permit-everyone variant, which a separate PASS_TO_PASS test pins), so "
            "the patch fails it and does NOT resolve.",
    },
    {
        "id": "weak-principal-without-credentials",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_ABSENT_PRINCIPAL),
        "witness": _W_ABSENT_PRINCIPAL_WITNESS,
        "rationale":
            "attacks the ABSENT arm's `result.user = none` conjunct, which NO other "
            "rival in this battery perturbs — machine-checked: every other "
            "absent-arm rival returns `none` on that arm (the full-leak rival "
            "provably so for every fallback and secret), so the two cost rivals "
            "above demonstrate only the arm's `queries`/`hasherCalls` conjuncts. "
            "This rival abandons the check correctly — both costs are zero, so C-"
            "cost holds — and yet hands back a principal, which is the strictly "
            "stronger failure the arm's third conjunct exists to forbid: a "
            "successful authentication with no credentials supplied. Refuted at a "
            "FRESH absent-arm point (login name present, secret absent) that no "
            "other witness in the battery uses, so the arm's `user` pin is "
            "demonstrated on its own sub-domain rather than inherited from a cost "
            "refutation. Decidable at literals.",
        "refinement":
            "its faithful real patch abandons the check without cost but returns a "
            "principal instead of nothing on that path. The F2P test's zero-query "
            "and zero-hasher assertions would both still PASS (no cost is "
            "incurred), which is exactly why this rival needs its own case; it is "
            "caught instead by the surrounding P2P authentication tests, which "
            "assert the credential check returns the stored principal only for "
            "supplied matching credentials (`test_authenticate`, "
            "`test_authenticates`, `test_skips_backends_without_arguments`) and "
            "which drive the session login flow — a principal returned for absent "
            "credentials would authenticate a caller who supplied none and break "
            "those equalities, so it does NOT resolve.",
    },
    {
        "id": "weak-principal-on-store-miss",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_MISS_PRINCIPAL),
        "witness": _W_MISS_PRINCIPAL_WITNESS,
        "rationale":
            "attacks C2 (the miss arm's `result.user = none`), the other outcome "
            "component no rival perturbed: weak-no-uniform-timing-hash attacks the "
            "SAME arm's cost conjunct C3 and leaves C2 satisfied, so before this "
            "case the miss arm's decision was demonstrated by nothing. Here the "
            "cost conjuncts both hold — one query, the uniform-timing hash still "
            "runs — and a principal is invented for a name the store does not "
            "carry, so the refutation isolates C2 exactly. ONE hypothesis about ONE "
            "term (this name is not carried) selects the arm; the login-name value "
            "is one no other witness uses, so the clause is not demonstrated at an "
            "already-probed store key.",
        "refinement":
            "its faithful real patch returns a principal on the store-miss branch "
            "rather than falling through to no principal. The timing P2P test "
            "(`Hasher is run once regardless of whether the user exists`) still "
            "passes — the hash count is untouched — so this rival is caught by the "
            "authentication tests instead: a name no principal carries would "
            "authenticate, and the P2P tests that pin the returned principal to the "
            "one created and stored (`test_authenticate`, `test_authenticates`, and "
            "the UUID login flow that re-reads the session's principal) would see a "
            "principal that was never stored, so it does NOT resolve.",
    },
    {
        "id": "weak-wrong-principal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_WRONG_PRINCIPAL),
        "witness": _W_WRONG_PRINCIPAL_WITNESS,
        "rationale":
            "attacks C5's IDENTITY pin: on the accepting decision the rival returns "
            "a principal other than the one the store returned. The two hypotheses "
            "(about two different terms) only select the accepting decision; the "
            "refutation itself is arithmetic on the returned identity and assumes "
            "nothing about any callee's value, which is why this witness probes an "
            "identity the spec pins rather than a cost.",
        "refinement":
            "its faithful real patch returns a principal other than the one the "
            "store matched. The PASS_TO_PASS authentication tests compare the "
            "returned principal against the one that was created and stored (and "
            "the login flow re-reads the session's principal), so the wrong "
            "identity fails those equalities and it does NOT resolve.",
    },
    {
        "id": "weak-ignore-fallback-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_IGNORE_FALLBACK),
        "witness": _W_IGNORE_FALLBACK_WITNESS,
        "rationale":
            "AUDIT ADDITION, closing a gap every rival above shares: all eleven "
            "reproduce the login-name resolution step verbatim, so its CONTENT was "
            "demonstrated by no case — a rival could mishandle the fallback name "
            "and go unnoticed. This rival drops the resolution step entirely: the "
            "fallback name is never read, so a check supplying only the keyword "
            "name is treated as carrying no login name and is abandoned. Refuted at "
            "name absent / fallback present / secret present, where the "
            "specification resolves the login name THROUGH the fallback and "
            "therefore demands `result.queries = 1` while the rival reports zero. "
            "C1 is demanded in both arms of the store lookup, so the witness splits "
            "on the lookup and refutes each arm with no assumption about the store "
            "and no hypothesis at all.",
        "refinement":
            "its faithful real patch reads only the positional login name and never "
            "consults the keyword one. Every PASS_TO_PASS authentication test that "
            "supplies the login name by keyword would then abandon the check and "
            "return no principal where it asserts the stored principal is returned, "
            "so it does NOT resolve.",
    },
    {
        "id": "weak-prefer-fallback-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_PREFER_FALLBACK),
        "witness": _W_PREFER_FALLBACK_WITNESS,
        "rationale":
            "AUDIT ADDITION, and a genuine NEAR-MISS of the case above: the "
            "resolution step is present but its PREFERENCE is inverted — the "
            "fallback wins whenever supplied, rather than only when the positional "
            "name is absent. It therefore agrees with the specified behavior on "
            "every input where at most one of the two names is supplied (including "
            "the point the case above is refuted at), and must be refuted at the "
            "only input that distinguishes them: BOTH names present, resolving to "
            "different principals. Four hypotheses, each about a DIFFERENT term — "
            "the store at TWO different keys, so no two equations constrain the "
            "same application, plus the two decisions at the principal the second "
            "key carries — hence jointly satisfiable. The refutation itself assumes "
            "nothing about any cost: the specification pins the outcome to what the "
            "POSITIONAL name resolves to, and the rival reports what the fallback "
            "resolves to instead.",
        "refinement":
            "its faithful real patch lets the keyword login name override the "
            "positional one. The PASS_TO_PASS authentication tests that pass both "
            "and expect the positional name to win would authenticate the wrong "
            "principal (or none), so it does NOT resolve.",
    },
    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ---------------
    {
        "id": "admiss-obligation-at-abandoned-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADM_PROOF),
        "rationale":
            "AUDIT ADDITION: the battery shipped with no admissibility lane, and "
            "the recorded reason — that the obligation carries no precondition "
            "hypothesis — is not sufficient, because the analogue of "
            "PRECOND-TOO-STRONG on a total carrier is the obligation being "
            "UNSATISFIABLE at an input the demanded behavior is asserted at. This "
            "case tests that directly: the impl region is byte-identical to the "
            "frozen one and only the proof region changes, discharging the frozen "
            "obligation's own body BY EVALUATION at four concrete abandoned-check "
            "inputs (no credentials; login name only; secret only; and fallback "
            "only, which reaches the arm THROUGH the resolution step) as `have`s, "
            "before closing the general obligation verbatim. If the absent arm's "
            "three conjuncts could not jointly hold at those points — if the arm "
            "demanded both zero cost and a returned principal, say — no "
            "implementation could satisfy the obligation on that sub-domain and the "
            "uniqueness lane's rejections there would attest to an unsatisfiable "
            "clause rather than to a wrong rival. Non-vacuity was machine-checked: "
            "the same `have` shape asserting the arm's clauses of a WRONG outcome at "
            "the no-credentials point fails (`unsolved goals ⊢ False`), so these "
            "`have`s are refutable claims and not tautologies. No new declaration, "
            "no new assumption token, theorem STATEMENT byte-identical.",
    },
]
