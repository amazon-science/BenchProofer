"""properties.py — G-PBT falsification battery for django__django-15554 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
full ``Solution.lean`` variant built by REGION SURGERY: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for cases that legitimately
re-prove, inside the ``-- proof-start`` / ``-- proof-end`` region — is changed,
so ``markers.same_spec`` holds by construction and the single
``theorem correct_addJoin`` STATEMENT stays byte-identical. ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` HOLDS of the rival while FAILING on the frozen solution).

PORT NOTE. This ports the nagini falsification battery (``../nagini/properties.py``)
onto this backend's carrier. The nagini bundle models ONE function ``install_join``
with fractional-permission contracts over parallel registry arrays
(``base``/``frel``/``reuse_mask``) held at ``Acc(.,1/2)``, returning a bool
("a fresh alias must be created"). This Lean bundle models the SAME
alias-allocation slice more richly as a single total function
``implementation_addJoin`` over the DATA — an ordered registry
``List (Alias × JoinKey)``, the new join's key, its own alias, the fresh alias,
the permitted-reuse set ``permittedAliases``, and the two flags — returning the full
``(chosen alias, updated registry)`` pair.

The obligation is UNCONDITIONAL: ``theorem correct_addJoin`` quantifies over both
values of ``restrictedTraversal`` with no precondition, so BOTH routes the
modeled slice spans are defended — the filtered-relation route (reuse confined to
the supplied set, reusability judged on the base part alone) and the ordinary one
(reusability judged on the WHOLE key, filter tag included). A prior revision
guarded the theorem with ``restrictedTraversal = true``, which left every
ordinary-route behavior unconstrained; the reject lane below now carries cases at
exactly those points.

Because the Lean carrier returns the WHOLE outcome (chosen alias AND the possibly
grown registry) rather than nagini's single bool, it exposes strictly more
observable clauses to attack than nagini's ``no_eligible_match`` bool — the
selection among candidates and the registry-growth frame are visible here and
have no nagini counterpart. The mapping of each nagini case to its Lean
counterpart (or its principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). The postcondition pins ``result`` to a
single grounded computation over ALL the inputs:
``result = registrationOutcome registry newJoin newJoinAlias freshAlias permittedAliases
multiValued restrictedTraversal``. That is spelled out over the actual data (a
``filterMap`` over the registry gated by permitted-AND-compatible, then a
fresh-vs-reuse branch), so there is NO opaque oracle to echo — returning it
directly IS the real work (the cheapest honest positive control). Its
independent, input-selected clauses:

  * reuse is CONFINED to the supplied set exactly when a filtered relation is
    being resolved AND that set is non-empty; confinement is also what selects
    the compatibility test;
  * under confinement an alias is COMPATIBLE iff its base part agrees — the
    filter tag is ignored (base-only);
  * OUTSIDE confinement compatibility requires the WHOLE key to agree, filter
    tag included, so joins carrying different filter tags are never compatible;
  * the permitted-reuse set is the supplied set when the relation is
    many-to-many or is being resolved under a filtered relation, and is "every
    alias permitted" otherwise;
  * a registered alias is ELIGIBLE iff it is permitted AND compatible;
  * with no eligible alias a FRESH alias is allocated and the new join is
    APPENDED to the registry (growth-by-one frame);
  * with an eligible alias the registry is UNCHANGED and the SELECTED alias is
    the new join's own alias when itself eligible, else the MOST RECENT eligible.

THE BEHAVIOURAL DISCRIMINATOR (two joins on the same base relation carrying
DIFFERENT filter tags must each receive their own alias, never one shared one).
The obligation forces that on both routes, by two different mechanisms, and a
rival has to get BOTH right:

  * where reuse is confined to the supplied set, the earlier alias reached along
    the first relation's own path is not in the second relation's supplied set,
    so reuse is refused and a fresh alias is allocated. The pre-fix decision
    used "every alias permitted" on the non-many-to-many route and wrongly
    collapsed the two onto the first alias (F2P ``test_multiple``);
  * on the ORDINARY route the two are held apart instead by the compatibility
    test itself: differing filter tags make the keys unequal, so the earlier
    entry is not a candidate at all. Relaxing that test to base-only is exactly
    the mistake measured below in the AUDIT RECORD — it leaves the F2P test
    failing — and it is what the ``weak-ordinary-route-*`` rivals do.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. Nagini's ``frame-mut-base-write`` rival
    (writing into a read-only ``Acc(.,1/2)`` registry array) has no expressible
    instance here; no substitute is fabricated. The frame CONTENT obligation
    (registry read-only on reuse, grown-by-one on fresh) is not vacuous, though —
    it is a value-level clause of ``chooseAlias`` and IS attacked (see
    ``weak-fresh-no-append``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to ``registrationOutcome`` built only from the inputs. There
    is no opaque answer key to echo; the cheapest correct impl returns that
    computation, which is the real work. Positive controls stand in for this
    class.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where MOST of the nagini
    ``uniqueness`` family lands. Each nagini partial-domain rival attacked "which
    slots count" / "how a match is decided"; here the corresponding rivals attack
    the reuse-set decision, the confinement condition, BOTH compatibility tests
    and the choice between them, the eligibility gate, the candidate selection,
    the fresh-vs-reuse branch polarity, and the registry-growth frame. The nagini
    rival ``weak-default-mask-only-eligibility`` (which attacks the "every alias
    permitted" arm) LANDS here now that the obligation is unconditional: that arm
    is reachable, and ``weak-prepatch-reuse-set`` plus the
    ``weak-ordinary-route-*`` family cover it.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean: ``implementation_addJoin`` is
    a total Lean ``def`` (a bounded ``for`` over the registry), so a diverging
    implementation cannot be written at all. (Nagini carries no divergence case
    for this instance either.)

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. The carrier is fully concrete and DecidableEq
(``Nat``/``List``/``Option``/``Bool``), so each witness ``unfold``s the spec
predicate and closes by ``decide``. Each was checked to HOLD of its rival and to
FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The reject witnesses probe DISTINCT inputs and move EVERY
binder the modeled behavior depends on, with no binder pinned: ``registry``
ranges over the empty, a one-slot, a two-slot, and a non-matching-base registry
(slot base 5, 9, and 4); ``newJoin`` varies base (5 vs 4) and filter tag
(``none`` vs ``some``); ``newJoinAlias`` takes 0/6/8/9 (in and out of the
candidate set); ``freshAlias`` takes 1, 7 and 9; ``permittedAliases`` ranges over ``[]``,
``[0]``, ``[2]``, ``[7]``, ``[0,3]`` (present, absent, empty); ``multiValued`` takes
both values; and ``restrictedTraversal`` takes BOTH values — the
``weak-ordinary-route-*`` witnesses sit at ``false``, which is what makes the
ordinary route's whole-key compatibility test an observable clause rather than
dead weight.

AXIOM lane: EMPTY. The reuse decision and registry update are modeled DEEPLY
(``keysEqual`` / ``matchCandidates`` / ``chooseAlias`` over the data), so there
is no ``opaque``/``axiom`` callee here. Nagini's ``AXIOM_TESTS`` belong to G-AX;
this gate ignores them and they are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-15554"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl body and proof tactic body, extracted from _BASE by marker split
# so a drift in the frozen solution breaks this manifest loudly. Every variant
# is a _swap of a substring lying ENTIRELY inside the impl region (or, for the
# re-proving positives/admissibility, the proof region).
# ---------------------------------------------------------------------------
_IMPL_BODY = _BASE.split(":= Id.run do\n", 1)[1].split("-- impl-end", 1)[0]
_PROOF_TAC = _BASE.split("(implementation_addJoin registry newJoin newJoinAlias "
                         "freshAlias\n          permittedAliases multiValued "
                         "restrictedTraversal) := by\n",
                         1)[1].split("-- proof-end", 1)[0]

assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync with Solution.lean"
assert _BASE.count(_PROOF_TAC) == 1, "proof-body anchor drift — re-sync with Solution.lean"


# ---- impl-region anchors (each unique inside Solution.lean; verified above) ----

# The permitted-set decision (part of the CHANGED slice): a traversal carrying a
# restriction of its own is governed by the supplied set, a multi-valued
# traversal likewise, and failing both every registered alias is permitted.
_A_REUSESET = (
    "    if restrictedTraversal then some permittedAliases\n"
    "    else if multiValued then some permittedAliases\n"
    "    else none"
)

# The candidate-collect block: the three-condition reusability gate (permission,
# same base relation, same filter tag unless waived) + append.
_A_COLLECT = (
    "    if permitted && p.2.base == newJoin.base\n"
    "                 && (restrictedTraversal || p.2.filt == newJoin.filt) then\n"
    "      cands := cands ++ [p.1]"
)

# The filter-tag condition alone, with its waiver (part of the CHANGED slice).
_A_FILTCOND = "                 && (restrictedTraversal || p.2.filt == newJoin.filt) then"

# The permitted-computation + collect block (membership confinement lives here).
_A_PERMITTED = (
    "    let permitted : Bool := match reuse with\n"
    "      | none   => true\n"
    "      | some s => s.contains p.1\n"
    "    if permitted && p.2.base == newJoin.base\n"
    "                 && (restrictedTraversal || p.2.filt == newJoin.filt) then\n"
    "      cands := cands ++ [p.1]"
)

# The own-alias-preference + most-recent selection block.
_A_PREFER = (
    "  if cands.contains newJoinAlias then\n"
    "    return (newJoinAlias, registry)\n"
    "  return (cands.getLastD freshAlias, registry)"
)

# The most-recent selection line of the impl (unique against the pure helper).
_A_GETLAST = "  return (cands.getLastD freshAlias, registry)"

# The fresh-alias allocation + registry-STORE block. The registry is name-keyed,
# so the store is a two-case operation: replace in place under a name already
# held, else add a last entry.
_A_APPEND = (
    "    return (freshAlias,\n"
    "      if registry.any (fun p => p.1 == freshAlias) then\n"
    "        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)\n"
    "      else\n"
    "        registry ++ [(freshAlias, newJoin)])"
)

# The add-a-last-entry leg of the store, on its own (the leg taken when the
# allocated name is not already held).
_A_STORE_ADD = "        registry ++ [(freshAlias, newJoin)])"

# The replace-in-place leg of the store, on its own.
_A_STORE_REPLACE = (
    "        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)"
)

# The store's case discrimination — whether the allocated name is already held.
_A_STORE_GUARD = "      if registry.any (fun p => p.1 == freshAlias) then"

# The proof's first tactic line (proof-region anchor for admissibility).
_A_INTRO = ("  intro registry newJoin newJoinAlias freshAlias permittedAliases "
            "multiValued\n    restrictedTraversal\n")


def _impl_swap(old, new):
    """Swap a substring inside the impl body only (keeps the frozen proof)."""
    return _swap(_BASE, old, new)


# A frozen witness harness: the spec is stated directly at a concrete input and
# closed by `unfold problem_spec_addJoin; decide` (the carrier is fully
# DecidableEq). `ex(...)` builds the reject witness for one input point.
def _ex(reg, nj, nja, fresh, canreuse, m2m, rwfr="true"):
    call = (f"{reg} {nj} {nja} {fresh} {canreuse} {m2m} {rwfr}")
    return (
        f"example : ¬ problem_spec_addJoin {call}\n"
        f"    (implementation_addJoin {call}) := by\n"
        f"  unfold problem_spec_addJoin\n"
        f"  decide\n"
    )


# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ================================================= soundness / positive ===
    # POSITIVE CONTROL 1 (local reshape). Hoist the per-slot eligibility into a
    # local `elig` before the guard — structurally different but fully CORRECT:
    # the loop scans the registry front-to-back exactly like gold and the value
    # flow is identical, so the frozen proof (the `key` fold lemma over the
    # `forIn` body, then `rfl`) still closes. If this cannot verify =>
    # SPEC-TOO-STRONG. Ports nagini's pos-control-reorder (eligibility/match
    # hoisted into locals) to the single modeled site.
    {
        "id": "pos-eligibility-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_swap(
            _A_COLLECT,
            "    let elig : Bool := permitted && p.2.base == newJoin.base\n"
            "                 && (restrictedTraversal || p.2.filt == newJoin.filt)\n"
            "    if elig then\n"
            "      cands := cands ++ [p.1]",
        ),
        "rationale": "a correct, structurally-reshaped impl (per-slot eligibility "
                     "hoisted into a local `elig` before the guard) must verify; it "
                     "keeps the front-to-back scan and identical value flow, so the "
                     "frozen fold lemma + `rfl` still close (no new lemma/axiom "
                     "introduced). Else SPEC-TOO-STRONG. Ports nagini's "
                     "pos-control-reorder.",
    },

    # POSITIVE CONTROL 2 (cheapest honest impl == grounded computation). Since
    # `registrationOutcome` is grounded in the args (not a @ContractOnly
    # answer-key), the cheapest correct impl simply RETURNS it — which IS the work
    # the loop computes, on BOTH routes. No loop, so the proof reduces to `rfl`
    # (the spec is definitionally this value). Ports nagini's
    # pos-cheapest-grounded.
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE,
                _IMPL_BODY,
                "  return chooseAlias registry newJoin newJoinAlias freshAlias\n"
                "    (if restrictedTraversal then some permittedAliases\n"
                "     else if multiValued then some permittedAliases\n"
                "     else none)\n"
                "    restrictedTraversal\n",
            ),
            _PROOF_TAC,
            "  intro registry newJoin newJoinAlias freshAlias permittedAliases "
            "multiValued\n    restrictedTraversal\n"
            "  rfl\n",
        ),
        "rationale": "the postcondition is result = registrationOutcome(...) and the "
                     "computation is grounded in the inputs, so the cheapest correct "
                     "impl returns it directly — doing the real work. Must verify "
                     "(proof `rfl`); else SPEC-TOO-STRONG. Stands in for "
                     "ungrounded-oracle (no wrong echo exists for a grounded "
                     "computation). Ports nagini's pos-cheapest-grounded.",
    },

    # POSITIVE CONTROL 3 (anti-over-fit on the filter-tag clause and its waiver).
    # The obligation says the filter tags must agree, except where the waiver
    # applies. A correct impl is free to phrase that as a CASE SPLIT on the
    # waiver — comparing the base alone on one side and the whole key on the
    # other — instead of as a base test conjoined with a waived filter test. The
    # behavior is identical on every input, only the phrasing differs. If this
    # could not verify, the clause would be pinning the frozen solution's
    # factoring rather than its behavior, i.e. SPEC-TOO-STRONG in the
    # over-fitting direction, which is the specific failure mode this clause
    # risks.
    {
        "id": "pos-route-tests-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _impl_swap(
                _A_COLLECT,
                "    if permitted && (if restrictedTraversal then "
                "p.2.base == newJoin.base\n"
                "                     else p.2 == newJoin) then\n"
                "      cands := cands ++ [p.1]",
            ),
            _PROOF_TAC,
            # The reshape is not definitional, so it needs its own bridging
            # lemma (`pointwise`) proving the two phrasings of the gate agree
            # pointwise, plus `full` decomposing whole-key equality into the two
            # component tests. Nothing is assumed; the theorem STATEMENT is
            # byte-identical and only this tactic body differs.
            "  intro registry newJoin newJoinAlias freshAlias permittedAliases "
            "multiValued\n    restrictedTraversal\n"
            "  have key : ∀ (pred : (Alias × JoinKey) → Bool) "
            "(l : List (Alias × JoinKey))\n"
            "      (acc : List Alias),\n"
            "      (forIn l acc (fun p r =>\n"
            "        (if pred p = true\n"
            "         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))\n"
            "         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))\n"
            "      = pure (acc ++ l.filterMap (fun p =>\n"
            "          if pred p = true then some p.1 else none)) := by\n"
            "    intro pred l\n"
            "    induction l with\n"
            "    | nil => intro acc; simp\n"
            "    | cons hd tl ih =>\n"
            "      intro acc\n"
            "      simp only [List.forIn_cons, List.filterMap_cons]\n"
            "      split <;> simp_all\n"
            "  have pointwise : ∀ (permitted : Bool) (p : Alias × JoinKey),\n"
            "      (permitted && (if restrictedTraversal then "
            "p.2.base == newJoin.base\n"
            "                     else p.2 == newJoin))\n"
            "    = (permitted && p.2.base == newJoin.base\n"
            "                 && (restrictedTraversal || p.2.filt == newJoin.filt)) "
            ":= by\n"
            "    intro permitted p\n"
            "    have full : ∀ (a b : JoinKey), (a == b) = "
            "(a.base == b.base && a.filt == b.filt) := by\n"
            "      intro a b\n"
            "      rcases a with ⟨ab, af⟩; rcases b with ⟨bb, bf⟩\n"
            "      by_cases hb : ab = bb\n"
            "      · by_cases hf : af = bf\n"
            "        · subst hb; subst hf; simp\n"
            "        · subst hb; simp [hf, beq_iff_eq]\n"
            "      · have : ¬ ({ base := ab, filt := af } : JoinKey) = "
            "{ base := bb, filt := bf } := by\n"
            "          intro h; exact hb (congrArg JoinKey.base h)\n"
            "        simp [beq_eq_false_iff_ne.mpr this, hb]\n"
            "    cases restrictedTraversal <;> cases permitted <;> simp [full]\n"
            "  simp only [problem_spec_addJoin, implementation_addJoin, "
            "registrationOutcome,\n"
            "    chooseAlias, matchCandidates, permittedReuse, eligible, "
            "pointwise]\n"
            "  rw [key _ registry []]\n"
            "  rfl\n",
        ),
        "rationale": "a correct impl that phrases the reusability gate as a case "
                     "split on the waiver (base alone on one side, whole key on the "
                     "other) instead of a base test conjoined with a waived filter "
                     "test must verify: same behavior on every input, different "
                     "phrasing. Guards the filter-tag clause against over-fitting "
                     "the frozen factoring; else SPEC-TOO-STRONG.",
    },

    # ===================================================== admissibility ======
    # A positive control confirming the obligation is SATISFIABLE (non-vacuous) at
    # the normal, F2P-shaped input rather than only in the abstract. The frozen
    # theorem carries NO precondition (it is quantified over both routes); the
    # honest analogue of nagini's self-call admissibility probe is to discharge
    # the spec predicate by evaluation at a ground F2P-shaped input (a one-slot
    # registry base 5 filt none, an incoming same-base distinct-filter join, empty
    # permittedAliases => a fresh alias must be allocated) as a `have`, then close the
    # frozen obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical. Ports nagini's admiss-self-call.
    {
        "id": "admiss-ground-fresh-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _A_INTRO,
            _A_INTRO +
            "  have _ground : problem_spec_addJoin [(0, ⟨5, none⟩)] ⟨5, some 1⟩ 9 1 "
            "[] false true\n"
            "      (implementation_addJoin [(0, ⟨5, none⟩)] ⟨5, some 1⟩ 9 1 [] false "
            "true) := by\n"
            "    unfold problem_spec_addJoin; decide\n",
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input (a "
                     "one-slot registry, a same-base distinct-filter incoming join, "
                     "empty permittedAliases => fresh alias allocated) by `decide`, then the "
                     "frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior is unsatisfiable at exactly the F2P input — "
                     "the analogue of PRECOND-TOO-STRONG). Nothing assumed: no new "
                     "declaration, statement byte-identical, ground instance is a "
                     "`have` inside the existing tactic body. Ports nagini's "
                     "admiss-self-call.",
    },

    # ================================================= uniqueness / reject =====
    # Each carries (a) the refinement argument that its faithful real patch would
    # NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input, checked to
    # HOLD of the rival and FAIL on the frozen solution.

    # ---- THE bug-delta: pre-patch reuse-set decision (nagini weak-default-base-only) ----
    {
        "id": "weak-prepatch-reuse-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the restricted-traversal case: on the modeled (not
        # multi-valued) route this yields "all permitted" (reuse = none) — the
        # original behavior the corrected spec must exclude.
        "module": _impl_swap(
            _A_REUSESET,
            "    if multiValued then some permittedAliases else none",
        ),
        "refinement": "this IS the pre-patch reuse-set decision: on the "
                      "filtered-relation path (not m2m) it makes every registered "
                      "alias permitted instead of confining reuse to the supplied "
                      "set. With two filtered relations on the same base relation "
                      "(F2P test_multiple), the second relation's join is then "
                      "judged compatible with the first's already-registered alias "
                      "(base parts agree, filter ignored) and reuses it — collapsing "
                      "two distinct filtered joins onto ONE alias. test_multiple "
                      "asserts they stay distinct, so the faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from the reuse-set clause: with reuse CONFINED to "
                     "permittedAliases=[3], the spec permits no existing alias (0 ∉ [3]), so a "
                     "fresh alias is allocated and appended; the rival treats every "
                     "alias as permitted, judges the base-5 slot compatible, and "
                     "reuses alias 0 with the registry unchanged — `result` differs in "
                     "BOTH components. The supplied set is deliberately NON-EMPTY here "
                     "(the F2P shape: aliases reachable along the second relation's own "
                     "path, not the first relation's join), which is what makes "
                     "confinement active and the clause observable. Binders: one-slot "
                     "registry base 5 filt none, incoming ⟨5, some 1⟩, permittedAliases=[3], "
                     "not m2m.",
        "witness": _ex("[(0, ⟨5, none⟩)]", "⟨5, some 1⟩", "9", "1", "[3]", "false"),
    },

    # ---- compatibility uses FULL identity incl. filter tag (nagini weak-constrained-full-identity) ----
    {
        "id": "weak-full-identity-match",
        "kind": "uniqueness",
        "expect": "reject",
        # Compatibility test uses base AND filter tag instead of base-only; a
        # same-base distinct-filter permitted alias is wrongly judged incompatible.
        "module": _impl_swap(
            _A_COLLECT,
            "    if permitted && (p.2.base == newJoin.base && p.2.filt == newJoin.filt) then\n"
            "      cands := cands ++ [p.1]",
        ),
        "refinement": "the reuse-compatibility test deliberately ignores the filter "
                      "tag (two joins on the same base relation are compatible "
                      "regardless of their filter). A faithful patch that required "
                      "the filter tag to match too would refuse to reuse a permitted "
                      "same-base alias whose filter differs, spuriously allocating "
                      "extra aliases and changing the generated SQL of the "
                      "filtered-relation P2P suite (the aggregation tests), so it "
                      "does NOT resolve.",
        "rationale": "REJECT from the compatibility clause: with a permitted "
                     "(permittedAliases=[0]) same-base distinct-filter slot, the spec finds "
                     "it compatible and reuses alias 0 (registry unchanged), while "
                     "the rival finds no candidate and allocates+appends a fresh "
                     "alias — `result` differs. Binders: incoming filt `some 1` vs "
                     "slot filt `none`, permittedAliases=[0], m2m true.",
        "witness": _ex("[(0, ⟨5, none⟩)]", "⟨5, some 1⟩", "9", "1", "[0]", "true"),
    },

    # ---- reusability ignores the permission gate (nagini weak-default-ignore-eligibility) ----
    {
        "id": "weak-ignore-reuse-confinement",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the permission (∈ permittedAliases) gate: decide on the shape
        # conditions alone, reusing an alias the caller did not permit.
        "module": _impl_swap(
            _A_PERMITTED,
            "    if p.2.base == newJoin.base\n"
            "                 && (restrictedTraversal || p.2.filt == newJoin.filt) then\n"
            "      cands := cands ++ [p.1]",
        ),
        "refinement": "this drops the confinement of permission to the supplied "
                      "set. When an alias on the same base relation exists but is "
                      "NOT in permittedAliases (reached only along a different "
                      "relation's path), the spec must allocate a fresh alias; this "
                      "rival reuses the forbidden alias, leaking a join the caller "
                      "had confined away — exactly the collapse the required "
                      "behavior forbids. The faithful real patch does NOT resolve.",
        "rationale": "REJECT from the permission clause: with permittedAliases=[7] "
                     "the base-5 slot alias 0 stands on the same base relation but "
                     "is NOT permitted, so the spec allocates+appends a fresh alias, "
                     "while the rival reuses alias 0 (registry unchanged) — `result` "
                     "differs. Binders: permittedAliases=[7] (present but "
                     "non-matching), incoming ⟨5, none⟩, not m2m.",
        "witness": _ex("[(0, ⟨5, none⟩)]", "⟨5, none⟩", "9", "1", "[7]", "false"),
    },

    # ---- selection drops the own-alias preference (no nagini counterpart: richer carrier) ----
    {
        "id": "weak-drop-own-alias-preference",
        "kind": "uniqueness",
        "expect": "reject",
        # Always reuse the most-recent candidate, dropping the "own alias
        # preferred if itself eligible" rule.
        "module": _impl_swap(
            _A_PREFER,
            "  return (cands.getLastD freshAlias, registry)",
        ),
        "refinement": "when the freshly-built connection already carries an alias "
                      "(a filtered relation's own alias) that is itself among the "
                      "eligible candidates, that alias must be preferred so the "
                      "relation lands on its own name; a patch that always took the "
                      "most-recent candidate would rename the connection onto a "
                      "different eligible alias, breaking the alias identity the "
                      "downstream SQL assembly relies on — it does NOT resolve. "
                      "(This clause is observable only on the Lean carrier, which "
                      "returns the chosen alias; nagini's bool result cannot see it.)",
        "rationale": "REJECT from the selection clause: with two eligible slots "
                     "[0,3] and newJoinAlias=0 itself eligible, the spec returns 0 "
                     "(own-alias preference) while the rival returns the most-recent "
                     "3 — `result` differs. Binders: two-slot registry, "
                     "newJoinAlias=0 in candidates, permittedAliases=[0,3], m2m true.",
        "witness": _ex("[(0, ⟨5, none⟩), (3, ⟨5, none⟩)]", "⟨5, none⟩", "0", "9",
                       "[0, 3]", "true"),
    },

    # ---- selection reuses the FIRST candidate, not the most recent (no nagini counterpart) ----
    {
        "id": "weak-reuse-first-not-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Reuse the earliest eligible candidate instead of the most recent.
        "module": _impl_swap(
            _A_GETLAST,
            "  return (cands.headD freshAlias, registry)",
        ),
        "refinement": "when several aliases are eligible and none is the "
                      "connection's own, the most-recently-registered one is reused "
                      "(matching the ORM's last-writer reuse order); a patch reusing "
                      "the earliest instead would attach the join to a stale alias, "
                      "changing which JOIN the filter binds to and the emitted SQL "
                      "across the reuse-order-sensitive P2P tests — it does NOT "
                      "resolve. (Observable only on the alias-returning Lean "
                      "carrier.)",
        "rationale": "REJECT from the selection clause: with eligible [0,3] and "
                     "newJoinAlias=9 (not among them), the spec returns the "
                     "most-recent 3 while the rival returns the first 0 — `result` "
                     "differs. Binders: newJoinAlias=9 (out of candidates, distinct "
                     "from the own-alias case), freshAlias=1, not m2m.",
        "witness": _ex("[(0, ⟨5, none⟩), (3, ⟨5, none⟩)]", "⟨5, none⟩", "9", "1",
                       "[0, 3]", "false"),
    },

    # ---- AUDIT REPAIR: the registry is NAME-KEYED, so the store has two legs ----
    # The obligation had asserted an unconditional append, which claims a
    # registry holding one name twice — a shape a name-keyed store can never
    # hold — and claims the join previously held under that name survives. The
    # store's two legs are now separately defended: the three cases below attack
    # (i) collapsing the store to an unconditional add, (ii) collapsing it to an
    # unconditional replace, and (iii) getting the replacement's POSITION wrong.
    {
        "id": "weak-store-always-add",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the "already held" leg: always add a last entry, so a name ends up
        # held twice and the join formerly under it is retained.
        "module": _impl_swap(
            _A_APPEND,
            "    return (freshAlias, registry ++ [(freshAlias, newJoin)])",
        ),
        "refinement": "the registry keys joins BY NAME, so a name holds at most "
                      "one join: storing under a name already held replaces the "
                      "join there rather than adding a second entry beside it. A "
                      "patch that always added would model a registry holding one "
                      "name twice — a state the store cannot reach — and would keep "
                      "a join the store discards. The retained stale entry is then "
                      "read back by the reuse scan, so a later registration reuses "
                      "an alias whose join no longer exists and the emitted SQL "
                      "binds the filter to the wrong JOIN: it does NOT resolve.",
        "rationale": "REJECT from the store's add-vs-replace leg: with the "
                     "allocated name A1 already held (registry [(0,⟨4,none⟩) under "
                     "name 1]) and no eligible alias (base 6 vs 4), the spec "
                     "replaces the join under name 1 in place, giving a 2-entry "
                     "registry, while the rival appends a third entry and keeps the "
                     "stale ⟨4,none⟩ — the registry component differs. Binders: "
                     "freshAlias=1 coinciding with a held name (the shape no other "
                     "witness uses), incoming base 6, permittedAliases=[], not m2m.",
        "witness": _ex("[(0, ⟨9, none⟩), (1, ⟨4, none⟩)]", "⟨6, none⟩", "8", "1",
                       "[]", "false", "false"),
    },

    {
        "id": "weak-store-always-replace",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the "not yet held" leg: only ever map over the existing entries,
        # so a store under a name not already held silently registers nothing.
        "module": _impl_swap(
            _A_APPEND,
            "    return (freshAlias, registry.map (fun p =>\n"
            "      if p.1 == freshAlias then (freshAlias, newJoin) else p))",
        ),
        "refinement": "storing under a name the registry does not yet hold ADDS "
                      "that name as a last entry; it is not a no-op. A patch that "
                      "only ever overwrote existing entries would fail to register "
                      "the overwhelmingly common genuinely-new join at all, so the "
                      "registry would never grow and every join would be emitted "
                      "under a name the registry does not record — the P2P suite "
                      "breaks wholesale and it does NOT resolve.",
        "rationale": "REJECT from the store's add leg: with the allocated name 7 "
                     "NOT held by the registry and no eligible alias (base 6 vs 4), "
                     "the spec adds (7, ⟨6,none⟩) as a last entry while the rival "
                     "maps over a registry containing no such name and returns it "
                     "unchanged — the registry component differs. Binders: "
                     "freshAlias=7 absent from the registry, incoming base 6, "
                     "restrictedTraversal=false.",
        "witness": _ex("[(1, ⟨4, none⟩)]", "⟨6, none⟩", "8", "7", "[]", "false",
                       "false"),
    },

    {
        "id": "weak-store-replace-moves-to-end",
        "kind": "uniqueness",
        "expect": "reject",
        # Replace under a held name, but re-register it at the END rather than in
        # place — the order of names is not preserved.
        "module": _impl_swap(
            _A_STORE_REPLACE,
            "        (registry.filter (fun p => p.1 != freshAlias)) "
            "++ [(freshAlias, newJoin)]",
        ),
        "refinement": "replacing the join held under a name leaves the ORDER of "
                      "names untouched — the name keeps the position it already "
                      "had. A patch that moved the replaced name to the end would "
                      "reorder the registry, and the order is exactly what the "
                      "most-recently-registered reuse rule reads: a later "
                      "registration would then reuse a different alias than the "
                      "real one, changing which JOIN a filter binds to across the "
                      "reuse-order-sensitive P2P tests — it does NOT resolve.",
        "rationale": "REJECT from the store's in-place positioning: with the "
                     "allocated name 1 held at the MIDDLE of a 3-entry registry and "
                     "no eligible alias (base 6), the spec keeps name 1 in position "
                     "1 while the rival drops it and re-adds it last — the registry "
                     "component differs in ORDER while holding the same names and "
                     "joins, so only the positioning clause separates them. "
                     "Binders: a 3-entry registry with the collided name in the "
                     "middle (a shape no other witness uses), freshAlias=1.",
        "witness": _ex("[(0, ⟨9, none⟩), (1, ⟨4, none⟩), (2, ⟨5, none⟩)]",
                       "⟨6, none⟩", "8", "1", "[]", "false", "false"),
    },

    # ---- registry frame: fresh alias but no store at all (nagini frame class, value-level here) ----
    {
        "id": "weak-fresh-no-append",
        "kind": "uniqueness",
        "expect": "reject",
        # Allocate the fresh alias but leave the registry UNCHANGED (fail to
        # append the new join).
        "module": _impl_swap(
            _A_APPEND,
            "    return (freshAlias, registry)",
        ),
        "refinement": "when no eligible alias exists a fresh one is allocated AND "
                      "the new join is appended to the registry under it, so later "
                      "joins in the same query build see it. A patch that returned "
                      "the fresh alias without registering the join would drop it "
                      "from the live registry: subsequent setup_joins/build_filter "
                      "reads would miss the join and rebuild wrong SQL — it does NOT "
                      "resolve. (Nagini expressed this class only as a "
                      "half-permission WRITE fault; on the referentially-transparent "
                      "Lean carrier it is a value-level frame clause of the returned "
                      "registry.)",
        "rationale": "REJECT from the registry-growth frame clause: with an "
                     "incompatible slot (base 9 vs incoming base 5) no alias is "
                     "eligible, so the spec appends `(1, ⟨5,none⟩)` to the registry "
                     "while the rival leaves it unchanged — the returned registry "
                     "component differs. Binders: registry base 9 (no match), "
                     "incoming ⟨5, none⟩, freshAlias=1, permittedAliases=[], not m2m.",
        "witness": _ex("[(0, ⟨9, none⟩)]", "⟨5, none⟩", "8", "1", "[]", "false"),
    },

    # ---- fresh-vs-reuse branch polarity inverted (ports nagini weak-result-polarity) ----
    # AUDIT ADDITION. The port dropped nagini's polarity case as having no
    # counterpart, but the branch it inverts IS observable on this carrier: the
    # emptiness test that chooses between "allocate fresh + append" and "reuse an
    # existing alias". Inverting it is the value-level analogue of nagini's
    # `return found` vs `return not found`, and it lands (rival exit 0 / gold
    # exit 1) at a point no other witness uses.
    {
        "id": "weak-branch-polarity-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the fresh-allocation branch exactly when an eligible alias EXISTS
        # (and the reuse branch when none does) — the polarity flip.
        "module": _impl_swap(
            "  if cands.isEmpty then\n" + _A_APPEND,
            "  if !cands.isEmpty then\n" + _A_APPEND,
        ),
        "refinement": "this allocates a fresh alias exactly when a permitted "
                      "compatible one was available and reuses when none was: every "
                      "legitimate reuse becomes a spurious duplicate JOIN and every "
                      "genuinely-new join is folded onto an alias that does not "
                      "describe it. Both the F2P assertion (the two filtered "
                      "relations get their own aliases, not a fresh-then-collapsed "
                      "pair) and the reuse-order-sensitive P2P suite break, so the "
                      "faithful real patch does NOT resolve.",
        "rationale": "REJECT from the fresh-vs-reuse branch clause: with a permitted "
                     "compatible slot (alias 2, permittedAliases=[2]) the spec reuses alias 2 "
                     "and leaves the registry unchanged, while the rival allocates "
                     "freshAlias=7 and appends — `result` differs in both components. "
                     "Binders: registry base 4 (a base no other witness uses), "
                     "newJoinAlias=6, freshAlias=7, permittedAliases=[2], not m2m.",
        "witness": _ex("[(2, ⟨4, none⟩)]", "⟨4, none⟩", "6", "7", "[2]", "false"),
    },
    # ---- AUDIT REPAIR: the ordinary route's reusability test (filter-SENSITIVE) ----
    # The escalated spec hole was that the obligation constrained only the
    # filtered-relation route, leaving everything the slice does on the ordinary
    # route unconstrained; every recorded counterexample lived there. The
    # obligation now spans both routes, so the ordinary route's own clauses are
    # defended here.
    {
        "id": "weak-ordinary-route-base-only-match",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the filter-tag condition altogether, so the base parts alone
        # decide reusability everywhere and a registered join whose filter tag
        # differs is wrongly judged reusable where no waiver applies.
        "module": _impl_swap(
            _A_COLLECT,
            "    if permitted && p.2.base == newJoin.base then\n"
            "      cands := cands ++ [p.1]",
        ),
        "refinement": "where no waiver applies a registered join is reusable only "
                      "when its filter tag agrees too; consulting the base part "
                      "alone there makes a join carrying a different filter tag "
                      "reusable, so an ordinary lookup traversing a relation that a "
                      "restricted one has already joined collapses onto that alias "
                      "and silently inherits its restriction. That is the same "
                      "collapse the reported behavior complains about, reached by "
                      "the other circumstance, and it changes the SQL of the "
                      "restricted-relation suite — the faithful patch does NOT "
                      "resolve (this is the class the recorded counterexamples "
                      "exploited).",
        "rationale": "REJECT from the filter-tag clause: with no waiver in force, a "
                     "permitted slot agreeing on base 5 but carrying filter tag "
                     "`none` against an incoming `some 1` is NOT reusable, so the "
                     "spec allocates+appends a fresh alias, while the rival reuses "
                     "alias 0 and leaves the registry unchanged — `result` differs in "
                     "both components. Binders: restrictedTraversal=false (the "
                     "circumstance no prior witness could reach), "
                     "permittedAliases=[0], m2m true.",
        "witness": _ex("[(0, ⟨5, none⟩)]", "⟨5, some 1⟩", "9", "1", "[0]", "true",
                       "false"),
    },

    # ---- AUDIT REPAIR: the circumstance that WAIVES the filter-tag condition ----
    {
        "id": "weak-route-test-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert which circumstance waives the filter-tag condition: require the
        # tags to agree exactly where the waiver belongs, and waive them exactly
        # where they are required.
        "module": _impl_swap(
            _A_FILTCOND,
            "                 && (!restrictedTraversal || p.2.filt == newJoin.filt) then",
        ),
        "refinement": "the waiver is not symmetric: it belongs to a traversal "
                      "carrying a restriction of its own — whose reuse is confined "
                      "by the supplied permitted set instead — and nowhere else. A "
                      "patch that inverted it would refuse legitimate reuse of a "
                      "permitted same-base alias on a restricted traversal AND "
                      "collapse differently-filtered joins everywhere else — both "
                      "directions of the defect at once, so it does NOT resolve.",
        "rationale": "REJECT from the waiver clause: with no waiver in force, a "
                     "permitted same-base distinct-filter slot is not reusable, so "
                     "the spec allocates fresh alias 1, while the rival waives the "
                     "filter-tag condition here, judges it reusable and returns alias "
                     "0 with the registry unchanged. Binders: "
                     "restrictedTraversal=false, incoming filt `some 1` vs "
                     "slot `none`, permittedAliases=[0].",
        "witness": _ex("[(0, ⟨5, none⟩)]", "⟨5, some 1⟩", "9", "1", "[0]", "true",
                       "false"),
    },

    # ---- AUDIT REPAIR: the ordinary route is still the whole allocation ----
    {
        "id": "weak-ordinary-route-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the join's own alias immediately off the filtered-relation
        # route, doing no allocation at all — the exact shape of the recorded
        # counterexamples.
        "module": _impl_swap(
            "  let reuse : Option (List Alias) :=",
            "  if !restrictedTraversal then\n"
            "    return (newJoinAlias, registry)\n"
            "  let reuse : Option (List Alias) :=",
        ),
        "refinement": "the allocation is the same procedure on both routes — the "
                      "route selects the permitted set and the reusability test, "
                      "not whether allocation happens at all. An impl that answered "
                      "with the incoming join's own alias off the filtered-relation "
                      "route would never register the join and never reuse a "
                      "genuinely matching one, so ordinary queries would emit joins "
                      "under an alias the registry never records: the P2P suite "
                      "breaks wholesale. This is the literal shape of the recorded "
                      "verify-does-not-resolve counterexamples, which is why it is "
                      "pinned as a case.",
        "rationale": "REJECT from the both-routes coverage of the allocation "
                     "clauses: on the ordinary route with an empty registry the "
                     "spec allocates freshAlias=1 and appends the new join, while "
                     "the rival returns newJoinAlias=9 and leaves the registry "
                     "empty — `result` differs in both components. Binders: empty "
                     "registry (a shape no other reject witness uses), "
                     "restrictedTraversal=false.",
        "witness": _ex("[]", "⟨5, none⟩", "9", "1", "[]", "false", "false"),
    },

    # ---- AUDIT REPAIR: WHICH circumstance waives the filter-tag condition ----
    # The cases above attack the filter-tag condition and the polarity of its
    # waiver; none pins WHICH circumstance the waiver keys on. Re-keying it to
    # "a permitted set was supplied at all" waives the filter-tag condition
    # wherever any set is supplied, restoring the collapse under a different
    # guard while agreeing with the spec everywhere the two guards coincide.
    {
        "id": "weak-confinement-condition-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_swap(
            _A_FILTCOND,
            "                 && (!permittedAliases.isEmpty || p.2.filt == newJoin.filt) then",
        ),
        "refinement": "the waiver keys on the CIRCUMSTANCE of the traversal, not on "
                      "whether a set of permitted aliases happens to have been "
                      "supplied. A patch keyed on the latter would stop consulting "
                      "the filter tag on every ordinary multi-valued traversal that "
                      "supplies a set, so two joins on one base relation carrying "
                      "different filter tags are judged reusable for each other "
                      "there and the second collapses onto the first's alias again. "
                      "Measured against the real harness: relaxing that one "
                      "comparison back to the base-part-only test while leaving the "
                      "permitted-set confinement in place leaves F2P test_multiple "
                      "FAILING (0/1, P2P 41/41), so the faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from the waiver-condition clause: with no waiver in "
                     "force the spec consults the filter tag, so a same-base "
                     "distinct-filter slot is NOT reusable and a fresh alias is "
                     "allocated + appended; the rival, seeing a non-empty supplied "
                     "set, waives the filter tag and reuses alias 2 with the registry "
                     "unchanged — `result` differs in both components. Binders: "
                     "restrictedTraversal=false with permittedAliases=[2] non-empty "
                     "(so only the circumstance, not the emptiness, may decide), "
                     "registry base 4, incoming ⟨4, some 3⟩ vs slot ⟨4, none⟩, "
                     "freshAlias=7, not m2m.",
        "witness": _ex("[(2, ⟨4, none⟩)]", "⟨4, some 3⟩", "6", "7", "[2]", "false",
                       "false"),
    },
]


# ---------------------------------------------------------------------------
# AUDIT RECORD (independent adversarial audit of the ported battery).
#
# ATTACK A (statement integrity). Every case's `theorem correct_addJoin`
# statement, and the whole `pure` / `post-conditions` / `axioms` regions, were
# extracted and compared byte-for-byte against Solution.lean: identical for all
# cases. No case reformats or weakens a hypothesis.
#
# ATTACK B (witness discrimination, re-derived). All witness pairs were rebuilt
# independently with the gate's own harness (`pbt_witness.witness_file`) and
# built with the real verifier: every rival build exits 0, every gold build
# exits 1, and each gold-side failure is the SEMANTIC message
# "`decide` proved that the proposition ¬… = … is false" — the kernel EVALUATED
# the claim and found the frozen solution satisfies the spec at that point. No
# gold-side failure is an unknown identifier, a type error, an unfolding
# failure, a stuck reduction, or a timeout. No witness binds anything, so no
# consistency probe is required (`consistency_probe` returns None for all).
#
# ATTACK C (is the rival wrong, or just different?). Each rival's outcome was
# computed independently at its own witness point: all differ from
# `registrationOutcome`'s value observably, in the chosen alias, the returned
# registry, or both. None is a mere reshape and none is definitionally equal to
# gold on this carrier, so no case is vacuous.
#
# ATTACK E (correct reshapes; SPEC-TOO-STRONG probe). Two NEW correct impls the
# battery did not contain were written and proven: (E1) the eligibility guard's
# `&&` commuted, and (E2) candidates accumulated in REVERSE via `foldl` and
# reversed at the end — a genuinely non-definitional reshape needing its own
# fold lemma. Both verify (exit 0), so the spec is not too strong. A correct impl
# spelling BOTH route comparisons out inline instead of via the shared
# compatibility helper also verifies (exit 0), so the widened clause does not
# over-fit the frozen factoring; that probe was kept as the in-battery control
# `pos-route-tests-inline`. A third probe (E2's first attempt) failed on an unsolved
# `reverse_reverse` goal, i.e. on the proof, not the spec; it was closed on
# retry, so no SPEC-TOO-STRONG claim rests on a proof I could not land.
#
# ATTACK D (tuned wrong impls; SPEC-TOO-WEAK probe). Five NEW wrong impls were
# written and built. Three aimed at the defended path are correctly REJECTED
# (exit 1, `rfl` failing on the value): dropping the filter tag when appending
# the freshly-registered join, growing the registry on the REUSE branch (frame
# violation), and returning the join's own alias instead of the fresh one on the
# fresh branch. Two aimed at the then-undefended route VERIFIED (exit 0) — see
# the SPEC HOLE record below, which those probes opened and which is now closed.
# A sixth probe inverted the "reuse = none means all permitted" arm and also
# verified then, for the same structural reason.
#
# SPEC HOLE (recorded above by an earlier revision of this manifest) — NOW
# CLOSED, and the closure is the reason this manifest was extended. The hole was
# that the obligation carried a precondition pinning
# `restrictedTraversal = true`, so it constrained ONE route of a function
# whose signature, docstring and modeled slice span both. Anything the impl did on
# the other route was unconstrained: impls returning `(0, [])` there VERIFIED
# (exit 0), and the `reuse = none` arm of the permitted test was dead, which is
# why G-MUT recorded that exact line as its lone survivor. G-EQ and G-PANEL-1
# recorded that as `fail` for this cell.
#
# The route was measured to be LOAD-BEARING before the obligation was widened,
# rather than assumed to be. The gold patch was rebuilt with ONE change — the
# ordinary route's comparison relaxed from whole-key back to base-only, leaving
# the filtered-relation route exactly as gold has it — and run against the real
# harness: `"resolved": false`, with FAIL_TO_PASS `test_multiple` in `failure`
# (0/1) and all 41 P2P still passing, reproduced over two attempts. So a rival
# that corrupts only that route is genuinely WRONG, not merely different, and an
# obligation blind to it cannot enforce verify => correct.
#
# The obligation is therefore now quantified over BOTH values of
# `restrictedTraversal` with no precondition — the domain GREW, it was not
# narrowed — and the postcondition states which compatibility test governs on
# each route (base-only under confinement, whole-key otherwise). Rivals at the
# formerly-dead points are now rejected and carry witnesses at
# `restrictedTraversal = false`: `weak-ordinary-route-base-only-match`,
# `weak-route-test-swapped`, `weak-ordinary-route-short-circuit`, and
# `weak-confinement-condition-always`. No reject case was weakened or removed to
# achieve this, and no precondition was added anywhere.
#
# COVERAGE (advisory). The earlier finding — binder `restrictedTraversal`
# pinned to `true` across all reject witnesses — no longer holds: four reject
# witnesses now sit at `false`. Every binder varies at values that change the
# spec's verdict, verified by computing gold's outcome at each witness point: they
# cover the fresh branch, the own-alias-preferred branch, and the
# most-recent-eligible branch, on both routes, with `permittedAliases` empty, hit, and
# missed.
#
# OMISSIONS re-derived (attack F), one verdict per dropped nagini case:
#   * frame-mut-base-write — INEXPRESSIBLE. Nagini's fault is a WRITE to an
#     `Acc(.,1/2)` array; a Lean input is a value with no permission to violate.
#     The frame CONTENT obligation it stood for is not dropped: it is attacked
#     value-level by `weak-fresh-no-append`, and this audit additionally
#     confirmed the reuse-side frame is defended (probe D4, registry grown on
#     the reuse branch, exit 1).
#   * weak-default-base-only — MAPPED to `weak-prepatch-reuse-set`.
#   * weak-default-ignore-eligibility — MAPPED to `weak-ignore-reuse-confinement`.
#   * weak-constrained-full-identity — MAPPED to `weak-full-identity-match`.
#   * weak-default-mask-only-eligibility — now EXPRESSIBLE and LANDED. Under the
#     earlier guarded obligation the DEFAULT ("every alias permitted") arm was
#     unreachable and mutating it to `false` VERIFIED (exit 0); with the
#     obligation widened to both routes that arm is live, and the clause is
#     attacked by `weak-prepatch-reuse-set` (reuse-set decision) together with
#     the `weak-ordinary-route-*` family (what the default arm then compares).
#   * weak-result-polarity — EXPRESSIBLE, and it was a real gap. The port
#     recorded no counterpart, but the fresh-vs-reuse branch is observable on
#     this carrier. Landed by this audit as `weak-branch-polarity-inverted`
#     (rival exit 0 / gold exit 1).
#   * AXIOM_TESTS (ax-join-eq-equals-areference) — out of lane; G-AX's, and
#     recorded pass there.
# ---------------------------------------------------------------------------


# No AXIOM lane: the reuse decision and registry update are modeled DEEPLY
# (keysEqual / matchCandidates / chooseAlias over the data), so the bundle
# consumes no `axiom` and declares no `opaque` callee. Nagini's AXIOM_TESTS
# belong to G-AX; dropped here.
AXIOM_TESTS = []
