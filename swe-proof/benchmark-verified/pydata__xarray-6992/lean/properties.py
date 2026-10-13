"""properties.py — G-PBT falsification battery for pydata__xarray-6992 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant produced by region surgery on the
FROZEN solution: only text inside the ``-- impl-start`` / ``-- impl-end`` region
— and, for a case that legitimately re-proves or adds a ground instance, inside
the ``-- proof-start`` / ``-- proof-end`` region — is changed. So
``markers.same_spec`` holds by construction and the ``theorem
correct_resetIndexCoords`` STATEMENT stays byte-identical; a rejection is
attributable to the postcondition, never to a tampered spec. No case adds an
``axiom``, a helper lemma, a ``sorry``/``admit``, or ``native_decide``.

``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation genuinely closed). ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (ONE obligation; three inputs)

  resetIndexCoords (c : ContainerNames) (resetNames : List String) (drop : Bool)
      -> ContainerNames

  A labelled container is observed through three name collections: the stored
  variable names, the coordinate names (a sub-collection of the stored names),
  and the names carrying a lookup index. Releasing the plain dimension indexes
  named in ``resetNames`` always removes their lookup index; the boolean
  ``drop`` then decides the fate of the underlying coordinates.

  The postcondition is FULLY PINNED (directive-5 frame, directive-8 grounded):
  it fixes all THREE output collections to exact ``removeAll`` expressions over
  the input collections, with a single derived quantity
  ``dropVariables = if drop then resetNames else []``:

    C1  result.indexNames   = removeAll c.indexNames   resetNames
    C2  result.varNames     = removeAll c.varNames     dropVariables
    C3  result.coordNames   = removeAll c.coordNames   dropVariables

  The three clauses are INDEPENDENT top-level conjuncts, so each is attacked by
  its own rival below. Note in particular that C2 and C3 share ``dropVariables``
  — that shared subtraction is exactly what keeps the coordinate/variable
  invariant (``coordNames ⊆ varNames``) intact, and it is the load-bearing
  content of the fix: the discriminating pre-patch shape leaves C3 unsubtracted
  while C2 subtracts, which is the invariant break the reported symptom comes
  from (an observed name count going negative when the two collections drift).

  The carrier is FULLY TRANSPARENT: ``removeAll = List.filter``, ``String`` has
  ``DecidableEq``, and ``ContainerNames`` derives ``DecidableEq``, so every
  witness below is stated at CONCRETE list literals and closed by ``decide``
  after unfolding. No ``opaque`` term, no hypothesis binder — hence no
  ``witness-inconsistent`` exposure at all (``consistency_probe`` returns None
  for a head that binds nothing).

PORTING THE NAGINI ARGUMENT ONTO THIS CARRIER

The nagini sibling contracts TWO functions over an immutable set carrier —
``promote_to_index`` and ``teardown_index`` — each pinning FOUR output
collections (stored variables, coordinate names, live indexes, and a fourth
collection recording which names are held in the index-backed representation),
plus a ``well_formed`` conjunct chaining the inclusions between them, and each
threading THREE removal channels (discarded / retained-but-converted /
displaced).

This bundle models a strictly NARROWER surface, and the narrowing is declared in
mapping.md / meta.json ``modeled_domain``: ONE obligation, THREE collections,
ONE removal channel governed by a boolean, restricted to plain single dimension
indexes. Case-count parity with nagini would therefore require fabricating
rivals for collections and channels that do not exist here, so it is not the
target. What IS carried over is the adversarial ARGUMENT of each nagini case,
re-expressed against this carrier where a counterpart exists:

  * nagini ``reject-convert-as-drop`` (treat a RETAINED coordinate as if
    discarded) -> ``reject-retain-as-discard`` below. This is the same attack:
    the nagini rival subtracts the retained channel from the variable/coordinate
    collections although a retained coordinate keeps its stored array; here the
    boolean ``drop`` IS the channel selector, so the rival unconditionally fills
    ``dropVariables``, which is the identical mistake on this carrier.
  * nagini ``reject-prepatch-coordnames`` (the base-commit shape: the coordinate
    collection is rebuilt from the ORIGINAL, unsubtracted) ->
    ``reject-coords-unsubtracted`` below, verbatim in argument and in effect.
    This is the discriminating clause (``Solution_prepatch.lean`` is exactly
    this rival).
  * nagini ``reject-identity-teardown`` (partial-domain: remove nothing) ->
    ``reject-identity`` below.
  * nagini ``reject-teardown-overkeep-indexes`` (a released name keeps its live
    index) -> ``reject-index-kept-unless-discarded`` below, sharpened: on this
    carrier the index release is UNCONDITIONAL while the coordinate fate is
    conditional, so the rival that couples them attacks C1's independence from
    ``drop`` — a stronger statement than the nagini original made.
  * nagini ``pos-teardown-combined`` / ``pos-promote-reorder`` (structurally
    different but CORRECT restructurings) -> the two soundness positives below,
    whose proofs actually close (the real work on a tactic-proof backend).
  * nagini ``admiss-teardown`` (the precondition admits a normal input) ->
    ``admiss-ground-instance`` below, adapted: the frozen obligation carries NO
    precondition (it is ``∀ c resetNames drop``, unconditional), so there is no
    ``Requires`` to establish. The admissibility question that remains is
    whether the postcondition is SATISFIABLE — not vacuous — at a realistic
    input, which the case discharges as a ground instance.

  * ``reject-var-kept`` below has no nagini counterpart: it is the C2 attack
    this narrower carrier makes available (a discarded coordinate leaves the
    coordinate collection but keeps its stored variable — the MIRROR of the
    pre-patch drift, the same invariant broken in the other direction).

NAGINI CASES DELIBERATELY NOT PORTED (see 'assessment' in the submitted payload)

  * The whole ``promote_to_index`` half — ``pos-promote-reorder`` and
    ``reject-promote-no-readd``. That behavior is a SECOND modeled function in
    nagini and is NOT modeled in this bundle at all (one obligation only), so
    those rivals have no carrier here. Fabricating a substitute would attack a
    behavior the frozen spec does not state.
  * ``reject-no-convert-repr``. It attacks the fourth collection (which names are
    held in the index-backed representation) and the ``well_formed`` inclusion
    that ties it to the live-index collection. This bundle models THREE
    collections; there is no fourth to leave a name in, and no ``well_formed``
    conjunct. The rival is not wrong on this carrier — it is inexpressible.
  * FRAME / PERMISSION-MUTATION class — VACUOUS, exactly as the nagini docstring
    already concludes for its own carrier. Lean is referentially transparent:
    ``c`` is an immutable value, there is no aliasing and no read-only-input
    obligation to violate. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION — REAL BUT UNWITNESSABLE on this carrier, so
    not shippable as a reject case. (An earlier revision of this docstring
    recorded the class as VACUOUS on the ground that "a diverging implementation
    cannot be written at all". That reason is FALSE and was corrected here after
    being measured; the disposition below is what the builds actually show.)

    A diverging rival IS expressible, in at least two forms, and both pass
    ``variant_scope`` (no new axiom/theorem, statement byte-identical):

      (i)  a ``partial def`` helper that recurses without a measure, whose result
           is returned in all three output collections;
      (ii) an unbounded ``while true do`` accumulator inside the same
           ``Id.run do`` block (desugaring to ``forIn Lean.Loop.mk``).

    Both are genuinely REJECTED by the verifier — exit 1, the obligation does not
    close — which is the ``"total"``-semantics disposition: a vanilla Lean ``def``
    is total, and ``partial``/``Lean.Loop`` buy non-termination only by making
    the term IRREDUCIBLE, not by making the postcondition vacuously true. So this
    is NOT the velvet ``set_option loom.semantics.termination "partial"``
    situation, where a non-terminating impl satisfies every ``ensures`` vacuously
    and the spec genuinely ADMITS the rival (the corpus-wide termination-semantics finding). There
    is no spec hole here: the rejection is real.

    What blocks SHIPPING the case is the witness half, and it blocks it on the
    side that must succeed. A witness must first ELABORATE against the rival, and
    the refutation is closed by ``decide`` over the impl's computed value — but
    the rival's whole point is that this value does not reduce. Measured: against
    both rivals ``decide`` reports ``failed for proposition`` (a STUCK reduction,
    with ``forIn Lean.Loop.mk`` visible in the (ii) goal), not ``is false``. That
    is the ``witness-undecided`` class, and it fails the RIVAL build, so the case
    would be recorded ``witness-unproven`` => inconclusive => MALFORMED-TESTS,
    turning the whole battery into a gate ERROR. Neither escape hatch applies:
    ``witness_reference`` substitutes only the SECOND (gold-side) subject and so
    cannot fix a rival-side stuck reduction, and a hypothesis-style witness must
    name the rival's own recursive helper — a variant-only name that
    ``witness_scope_problems`` correctly rejects, since its failure on gold would
    be an unknown identifier rather than a satisfied spec.

    Recorded therefore as a real class this BACKEND cannot witness, not as a
    vacuous class and not as a spec hole.
  * UNGROUNDED-ORACLE ECHO — VACUOUS, same reasoning as nagini's: the
    postcondition is spelled out as ``removeAll`` over the input collections,
    with no axiomatized answer key an impl could echo. ``meta.json`` declares
    ``axioms: []`` and ``opaque_callees: []``.
  * ``AXIOM_TESTS`` — DROPPED. The axiom lane is G-AX's job and this gate ignores
    it; the bundle's single deep-model reference is validated there.

BINDER COVERAGE. The spec binds ``c``, ``resetNames``, ``drop`` (``result`` is
the output). The five reject witnesses probe FIVE DISTINCT input points and
every input binder is moved:

  * ``drop`` — ``false`` (reject-retain-as-discard, reject-index-kept-unless-
    discarded) AND ``true`` (the other three). Not pinned: the two rivals that
    attack the conditional channel are refuted precisely on the ``drop=false``
    side, which is where they diverge from gold.
  * ``resetNames`` — a one-name list, and a TWO-name list
    (``reject-identity``), so the traversal is exercised at more than one length.
  * ``c`` — varied in shape across the five: a container whose stored names
    exceed its coordinate names (so a C2/C3 drift is observable), one whose
    collections coincide, one carrying an extra non-coordinate stored name, and
    one where the released name is NOT the only coordinate.

CLAUSE COVERAGE. C1 is attacked by ``reject-index-kept-unless-discarded`` and
``reject-identity``; C2 by ``reject-retain-as-discard`` and ``reject-var-kept``;
C3 by ``reject-coords-unsubtracted`` and ``reject-retain-as-discard``. No clause
is left unattacked. Re-derived mechanically over a shadow of the three clauses at
each case's own witness point: every rival violates exactly the clause(s) its
``rationale`` names, gold satisfies all three at all five points, and the five
points are pairwise DISTINCT.

WHY THE REJECT LANE IS EXHAUSTIVE (not merely broad). The postcondition pins all
three output collections to closed expressions over the inputs, so it determines
the result UNIQUELY — machine-checked, both closing at exit 0 over the frozen
spec region with the impl and proof regions removed:

    theorem spec_determines_result (c rn d) (r1 r2)
        (h1 : problem_spec_resetIndexCoords c rn d r1)
        (h2 : problem_spec_resetIndexCoords c rn d r2) : r1 = r2
    theorem spec_total (c rn d) : ∃ r, problem_spec_resetIndexCoords c rn d r

Determinacy plus totality is what makes SPEC-TOO-WEAK structurally unreachable
here: any impl that differs from the frozen one at even one input is refutable at
that input, and any impl that agrees everywhere is correct. So the reject lane's
job is not to enumerate wrong impls (there is no residue for one to hide in) but
to demonstrate that each clause is pinned SEPARATELY — which is exactly what the
five cases do, each leaving the other clauses intact.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6992"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors.
#
# _IMPL_GOLD is the ENTIRE text between `-- impl-start` and `-- impl-end`, and
# _PROOF_GOLD the entire text between `-- proof-start` and `-- proof-end`. Both
# are unique in _BASE, so every _swap below lands wholly inside the region it
# means to edit and the manifest breaks loudly (AssertionError at import) if the
# frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    "def implementation_resetIndexCoords\n"
    "    (c : ContainerNames) (resetNames : List String) (drop : Bool) :\n"
    "    ContainerNames := Id.run do\n"
    "  let mut dropIndexes : List String := []\n"
    "  let mut dropVariables : List String := []\n"
    "  for name in resetNames do\n"
    "    -- the coordinate names sharing this plain dimension index: just `name`\n"
    "    dropIndexes := dropIndexes ++ [name]\n"
    "    -- discard-or-convert the underlying coordinate\n"
    "    if drop then\n"
    "      dropVariables := dropVariables ++ [name]\n"
    "  let indexNames := removeAll c.indexNames dropIndexes\n"
    "  let varNames := removeAll c.varNames dropVariables\n"
    "  let coordNames := removeAll c.coordNames dropVariables\n"
    "  return { varNames := varNames, coordNames := coordNames, "
    "indexNames := indexNames }\n"
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drift"

_PROOF_START = "-- proof-start\n"
_PROOF_END = "-- proof-end"
_P0 = _BASE.index(_PROOF_START) + len(_PROOF_START)
_P1 = _BASE.index(_PROOF_END)
_PROOF_GOLD = _BASE[_P0:_P1]
assert "theorem correct_resetIndexCoords" in _PROOF_GOLD, "proof region drift"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region not unique"

# The obligation STATEMENT — byte-identical in every variant (variant_scope
# rule 2). Only the tactic body after `:= by` may differ.
_OBLIGATION = (
    "theorem correct_resetIndexCoords :\n"
    "    ∀ (c : ContainerNames) (resetNames : List String) (drop : Bool),\n"
    "    problem_spec_resetIndexCoords c resetNames drop\n"
    "      (implementation_resetIndexCoords c resetNames drop) := by\n"
)
assert _BASE.count(_OBLIGATION) == 1, "obligation statement drift"


def _impl(body):
    """Swap ONLY the impl region; the frozen proof body is carried over."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body, proof):
    """Swap the impl region AND reprove — for a soundness positive whose new
    impl shape the frozen tactic script no longer matches."""
    return _swap(_swap(_BASE, _IMPL_GOLD, body), _PROOF_GOLD, proof)


def _proof_extra(extra):
    """Keep the gold impl and the gold proof, appending `extra` inside the
    proof region — for the admissibility ground instance."""
    return _swap(_BASE, _PROOF_GOLD, _PROOF_GOLD.rstrip("\n") + "\n" + extra)


# --- rival impl shapes -------------------------------------------------------
_HEAD = (
    "def implementation_resetIndexCoords\n"
    "    (c : ContainerNames) (resetNames : List String) (drop : Bool) :\n"
    "    ContainerNames := Id.run do\n"
)

# the gold traversal, comments dropped (the loop is not what these rivals edit)
_GOLD_LOOP = (
    "  let mut dropIndexes : List String := []\n"
    "  let mut dropVariables : List String := []\n"
    "  for name in resetNames do\n"
    "    dropIndexes := dropIndexes ++ [name]\n"
    "    if drop then\n"
    "      dropVariables := dropVariables ++ [name]\n"
)

_GOLD_TAIL = (
    "  let indexNames := removeAll c.indexNames dropIndexes\n"
    "  let varNames := removeAll c.varNames dropVariables\n"
    "  let coordNames := removeAll c.coordNames dropVariables\n"
    "  return { varNames := varNames, coordNames := coordNames, "
    "indexNames := indexNames }\n"
)


def _witness(varNames, coordNames, indexNames, resetNames, drop):
    """A refutation witness at CONCRETE literals.

    States the spec predicate directly at one input and asserts its negation of
    the value the variant computes there. The carrier is fully transparent, so
    `decide` settles it after unfolding — no hypothesis binder, hence nothing
    for the gate's consistency probe to find inconsistent.

    Every witness below was built against BOTH files with scripts/lean_verify.sh:
    it ELABORATES against its rival (exit 0) and FAILS on the frozen solution
    (`decide` reports the goal `is false`), so it is a seen discriminator.

    The gold-side failure is a PLAIN EVALUATION, not a syntactic accident, and
    each of the five was additionally forgery-tested by flipping only the claim
    (dropping the leading `¬`, changing nothing else) and rebuilding both sides:

      * flipped claim vs the FROZEN solution -> exit 0 (gold satisfies the spec
        at that input, as it must);
      * flipped claim vs the RIVAL           -> exit 1, `decide proved that the
        proposition ... is false`.

    That is the exact inverse of the witness's own pair, so `decide`'s exit code
    here carries information about the CLAIM rather than about the impl's shape:
    a witness asserting gold is CORRECT at these points would NOT have been
    recorded as a refutation. No case rests on an unfolding failure, a missing
    identifier, a type error, or a timeout.
    """
    c = ("{ varNames := %s, coordNames := %s, indexNames := %s }"
         % (varNames, coordNames, indexNames))
    return (
        "example : ¬ problem_spec_resetIndexCoords\n"
        "    %s %s %s\n"
        "    (implementation_resetIndexCoords\n"
        "      %s %s %s) := by\n"
        "  unfold problem_spec_resetIndexCoords implementation_resetIndexCoords\n"
        "  decide\n" % (c, resetNames, drop, c, resetNames, drop))


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ================= POSITIVE CONTROLS (soundness) ========================

    # -- pos-direct: the same relation, computed WITHOUT the traversal ---------
    # The gold impl accumulates the released names in a `for` loop and then
    # applies the three removals. This variant skips the accumulator entirely
    # and applies `removeAll` directly to the input list, deriving the
    # conditional channel with a `let`. Identical extensional behaviour (folding
    # `++ [name]` over a list from `[]` yields the list itself), a completely
    # different executable shape — and the frozen tactic script, which is a
    # closed-form loop induction, does NOT apply, so the case reproves.
    # The new proof is `unfold; exact ⟨rfl, rfl, rfl⟩`: all three conjuncts are
    # definitional once the loop is gone. Must VERIFY (else SPEC-TOO-STRONG).
    # BUILT: exit 0 (obligation genuinely closed, no sorry).
    # The "frozen script does not apply" claim is MEASURED, not asserted: this
    # impl carrying the frozen proof body verbatim fails to build (exit 1, `No
    # goals to be solved` — `rw [reduce_impl]` already discharges the goal for
    # the loop-free shape). So the case does real proof work; it is not the
    # frozen impl wearing a different spelling, and its `verify` is not inherited
    # from a script tuned to a shape it no longer has.
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "def implementation_resetIndexCoords\n"
            "    (c : ContainerNames) (resetNames : List String) (drop : Bool) :\n"
            "    ContainerNames :=\n"
            "  let dropVariables : List String := if drop then resetNames else []\n"
            "  { varNames := removeAll c.varNames dropVariables,\n"
            "    coordNames := removeAll c.coordNames dropVariables,\n"
            "    indexNames := removeAll c.indexNames resetNames }\n",
            _OBLIGATION
            + "  intro c resetNames drop\n"
              "  unfold problem_spec_resetIndexCoords "
              "implementation_resetIndexCoords\n"
              "  exact ⟨rfl, rfl, rfl⟩\n",
        ),
        "rationale": "a structurally DIFFERENT but CORRECT implementation: the "
                     "released-name accumulator is eliminated and the three "
                     "removals are applied directly to the input list, with the "
                     "conditional channel derived in a `let`. Extensionally "
                     "identical (accumulating `++ [name]` from `[]` reproduces "
                     "the list), so all three postcondition conjuncts C1/C2/C3 "
                     "hold definitionally and the obligation closes with "
                     "`exact ⟨rfl, rfl, rfl⟩`. The frozen script does not apply "
                     "to this shape, so the case reproves rather than reusing "
                     "it — the obligation statement is byte-identical. If this "
                     "is rejected the postcondition over-constrains the "
                     "COMPUTATION rather than the relation => SPEC-TOO-STRONG.",
    },

    # -- pos-single-accumulator: one accumulator instead of two ----------------
    # Gold threads a PAIR through the loop (released names, and the conditional
    # discard channel). This variant threads ONE accumulator and derives the
    # conditional channel once, AFTER the traversal — which is where the real
    # decision belongs, since the flag does not vary per iteration. Same three
    # collections out. Needs its own closed-form lemma for the single-accumulator
    # loop, proved INLINE as a `have` inside the tactic body (no new top-level
    # theorem/lemma, per variant_scope rule 3). Must VERIFY.
    # BUILT: exit 0.
    # Also measured: this impl with the frozen proof body verbatim FAILS (exit 1,
    # `rewrite failed: Did not find an occurrence of the pattern` — the frozen
    # `reduce_impl` is stated over the PAIR accumulator and no longer unifies with
    # a single-accumulator `forIn`). The inline `have` is therefore load-bearing.
    {
        "id": "pos-single-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            _HEAD
            + "  -- one accumulator: collect the released names, then decide the\n"
              "  -- underlying coordinates' fate once, after the traversal.\n"
              "  let mut released : List String := []\n"
              "  for name in resetNames do\n"
              "    released := released ++ [name]\n"
              "  let dropVariables : List String := if drop then released else []\n"
              "  let coordNames := removeAll c.coordNames dropVariables\n"
              "  let varNames := removeAll c.varNames dropVariables\n"
              "  let indexNames := removeAll c.indexNames released\n"
              "  return { varNames := varNames, coordNames := coordNames, "
              "indexNames := indexNames }\n",
            _OBLIGATION
            + "  intro c resetNames drop\n"
              "  unfold problem_spec_resetIndexCoords "
              "implementation_resetIndexCoords\n"
              "  simp only [Id.run, bind, pure]\n"
              "  have key : ∀ (l acc : List String),\n"
              "      (forIn l acc (fun name r => ForInStep.yield (r ++ [name])) :"
              " Id (List String))\n"
              "        = acc ++ l := by\n"
              "    intro l\n"
              "    induction l with\n"
              "    | nil => intro acc; simp [pure]\n"
              "    | cons a t ih =>\n"
              "      intro acc\n"
              "      rw [List.forIn_cons]\n"
              "      show (forIn t (acc ++ [a]) _ : Id _) = _\n"
              "      rw [ih]\n"
              "      simp\n"
              "  rw [key]\n"
              "  cases drop <;> simp\n",
        ),
        "rationale": "a CORRECT restructuring that threads ONE accumulator "
                     "through the traversal and derives the conditional channel "
                     "once afterwards, plus a reordered assembly of the three "
                     "output collections. The relation is unchanged, so C1/C2/C3 "
                     "all still hold and the obligation closes: an inline "
                     "closed-form `have` for the single-accumulator loop, then "
                     "`cases drop <;> simp`. No new top-level lemma, no axiom, "
                     "no sorry; the obligation statement is byte-identical. If "
                     "this is rejected the spec is pinned to the gold loop's "
                     "particular accumulator SHAPE rather than to the "
                     "input->output relation => SPEC-TOO-STRONG.",
    },

    # ================= ADMISSIBILITY ========================================

    # -- admiss-ground-instance: the postcondition is satisfiable, not vacuous -
    # The nagini sibling's `admiss-teardown` Asserts its `Requires` inside the
    # body to show the PRECONDITION admits a normal input. The frozen obligation
    # here carries NO precondition (`∀ c resetNames drop`, unconditional), so
    # there is no Requires to establish and that mechanic has no counterpart.
    # The admissibility question that survives is whether the pinned relation is
    # SATISFIABLE at a realistic input — a postcondition that were contradictory
    # at every input would make the obligation unprovable, which is the same
    # PRECOND-TOO-STRONG failure one level up. So: keep the gold impl and gold
    # proof VERBATIM and add a ground instance at an F2P-shaped input (one plain
    # dimension index released with the coordinate discarded, alongside an
    # unrelated stored name that must survive), discharged by `decide`.
    # BUILT: exit 0.
    # The `decide` here genuinely EVALUATES rather than closing for a syntactic
    # reason — checked by the same forgery experiment the reject witnesses get.
    # Holding the input fixed and asserting the relation of a deliberately WRONG
    # result (the container returned UNCHANGED, i.e. no removal performed) flips
    # the build to exit 1 with `decide proved that the proposition ... is false`.
    # So the ground instance's exit code tracks the CLAIM, and it is real
    # evidence that the relation is satisfiable at this input rather than a
    # tautology about a term that failed to reduce.
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof_extra(
            "\n"
            "-- The specification is INSTANTIABLE at a normal release input:\n"
            "-- releasing one plain dimension index with the flag set takes its\n"
            "-- name out of BOTH the stored variables and the coordinate set\n"
            "-- while an unrelated stored name survives, and the pinned relation\n"
            "-- holds of the computed result. A postcondition that were "
            "unsatisfiable\n"
            "-- here could not be discharged at all.\n"
            "example : problem_spec_resetIndexCoords\n"
            '    { varNames := ["x", "d"], coordNames := ["x"], '
            'indexNames := ["x"] } ["x"] true\n'
            "    (implementation_resetIndexCoords\n"
            '      { varNames := ["x", "d"], coordNames := ["x"], '
            'indexNames := ["x"] } ["x"] true) := by\n'
            "  unfold problem_spec_resetIndexCoords "
            "implementation_resetIndexCoords\n"
            "  decide\n"
        ),
        "rationale": "the pinned relation must be SATISFIABLE at a realistic "
                     "release input, not vacuous: the gold impl and gold proof "
                     "are carried over verbatim and a ground instance is added "
                     "at a container whose released name is one of two stored "
                     "names, with the flag set. All three conjuncts C1/C2/C3 "
                     "reduce and `decide` closes them. The frozen obligation has "
                     "no precondition binder, so nagini's `Assert(Requires)` "
                     "mechanic has no counterpart; this is the surviving "
                     "admissibility content. If the instance could not be "
                     "discharged the relation would be unsatisfiable in the "
                     "modeled domain => PRECOND-TOO-STRONG.",
    },

    # ================= UNIQUENESS / REJECT ==================================

    # -- reject-coords-unsubtracted: THE discriminating clause (C3) ------------
    # Rebuild the coordinate collection from the ORIGINAL, unsubtracted, while
    # the stored-variable collection IS subtracted. This is the pre-patch shape
    # the bundle's own Solution_prepatch.lean carries, and the nagini sibling's
    # `reject-prepatch-coordnames` verbatim in argument. A discarded coordinate
    # then leaves the stored variables but LINGERS in the coordinate set, so the
    # two collections drift apart and the invariant breaks.
    # WITNESS at (c={vars:[a,b], coords:[a], idx:[a]}, reset=[a], drop=true):
    # C3 demands the coordinate set become [] but the rival returns [a].
    # BUILT: rival exit 0, gold exit 1 ("is false").
    {
        "id": "reject-coords-unsubtracted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD + _GOLD_LOOP
            + "  let indexNames := removeAll c.indexNames dropIndexes\n"
              "  let varNames := removeAll c.varNames dropVariables\n"
              "  let coordNames := c.coordNames\n"
              "  return { varNames := varNames, coordNames := coordNames, "
              "indexNames := indexNames }\n"
        ),
        "witness": _witness('["a", "b"]', '["a"]', '["a"]', '["a"]', "true"),
        "refinement": "the faithful real patch of this rival is the BASE-COMMIT "
                      "assembly: the coordinate collection is rebuilt from the "
                      "original one unioned with the (empty, for a plain "
                      "dimension index) set of re-added names, so a discarded "
                      "coordinate is never taken out of it. That is precisely "
                      "the reported defect: the coordinate collection then "
                      "exceeds the stored-variable collection and the derived "
                      "count of non-coordinate variables goes NEGATIVE, raising "
                      "the ValueError quoted in the issue on repr and on the "
                      "length of the data-variable view. The F2P suite asserts "
                      "the released name is gone from the container's "
                      "coordinates after a discarding release, and "
                      "test_reset_index / test_reset_index_drop_dims / the "
                      "drop=True arms of test_reset_index_drop_convert all fail "
                      "on it (G-DIFF: Solution_prepatch.lean is this rival and "
                      "fails to verify). So a verifying rival here would be a "
                      "genuine verify-does-not-imply-resolve break.",
        "rationale": "refuted by clause C3, `result.coordNames = removeAll "
                     "c.coordNames dropVariables`, at the binder point "
                     "drop=true / resetNames=[\"a\"]: with the flag set "
                     "dropVariables is [\"a\"], so C3 demands the coordinate "
                     "collection [\"a\"] become [], while the rival returns it "
                     "unchanged. The witness states ¬ problem_spec at exactly "
                     "that input and `decide` closes it; on the frozen solution "
                     "the same statement is reported false, so it is a seen "
                     "discriminator. Note this rival leaves C1 and C2 intact — "
                     "it is refutable ONLY because C3 is pinned independently.",
    },

    # -- reject-retain-as-discard: the retained coordinate treated as discarded
    # Fill the discard channel UNCONDITIONALLY, ignoring the flag. A retained
    # coordinate then vanishes from both the stored variables and the coordinate
    # set although it was supposed to survive as an ordinary stored variable.
    # This is nagini's `reject-convert-as-drop` on this carrier: there the
    # retained channel is a separate input subtracted where it must not be, here
    # the flag IS the channel selector.
    # NEAR-MISS NOTE: this rival agrees with gold on the whole drop=true half of
    # the domain, so its witness must sit on the drop=false side — which is why
    # it does not share a witness with any other case.
    # WITNESS at (c={vars:[x,d], coords:[x], idx:[x]}, reset=[x], drop=false):
    # C2 demands the stored names stay [x,d] but the rival returns [d].
    # BUILT: rival exit 0, gold exit 1.
    {
        "id": "reject-retain-as-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD
            + "  let mut dropIndexes : List String := []\n"
              "  let mut dropVariables : List String := []\n"
              "  for name in resetNames do\n"
              "    dropIndexes := dropIndexes ++ [name]\n"
              "    dropVariables := dropVariables ++ [name]\n"
            + _GOLD_TAIL
        ),
        "witness": _witness('["x", "d"]', '["x"]', '["x"]', '["x"]', "false"),
        "refinement": "the faithful real patch routes the RETAINED (non-"
                      "discarding) names through the discard channel instead of "
                      "re-storing them as ordinary variables, which DELETES the "
                      "retained coordinate's array. The F2P suite's non-"
                      "discarding arms assert the released name's variable "
                      "SURVIVES in its plain (non-index-backed) form — the "
                      "drop=False arms of test_reset_index_drop_convert read "
                      "that variable back and compare it. Deleting it makes the "
                      "name missing entirely, so those arms fail with a lookup "
                      "error. The faithful patch does NOT resolve.",
        "rationale": "refuted by clauses C2 and C3 at the binder point "
                     "drop=false: with the flag clear dropVariables is [], so "
                     "C2 demands the stored names stay [\"x\", \"d\"] and C3 "
                     "the coordinate names stay [\"x\"], while the rival "
                     "subtracts the released name from both and returns [\"d\"] "
                     "/ []. This is a NEAR-MISS that agrees with gold across "
                     "the whole drop=true half of the domain, so the witness is "
                     "placed on the drop=false side where it actually diverges — "
                     "it shares no input point with any other case. `decide` "
                     "closes it against the rival; the frozen solution reports "
                     "it false.",
    },

    # -- reject-index-kept-unless-discarded: C1 must not depend on the flag ----
    # Couple the index release to the flag: release the lookup index only when
    # the coordinate is discarded. A retained coordinate then keeps a live
    # lookup index that was supposed to be released. nagini's
    # `reject-teardown-overkeep-indexes` sharpened for this carrier: the point
    # here is that C1's removal is UNCONDITIONAL, so the rival attacks C1's
    # independence from `drop`, which no single nagini case stated.
    # WITNESS at (c={vars:[m], coords:[m], idx:[m]}, reset=[m], drop=false):
    # C1 demands the index collection become [] but the rival returns [m].
    # BUILT: rival exit 0, gold exit 1.
    {
        "id": "reject-index-kept-unless-discarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD
            + "  let mut dropIndexes : List String := []\n"
              "  let mut dropVariables : List String := []\n"
              "  for name in resetNames do\n"
              "    if drop then\n"
              "      dropIndexes := dropIndexes ++ [name]\n"
              "      dropVariables := dropVariables ++ [name]\n"
            + _GOLD_TAIL
        ),
        "witness": _witness('["m"]', '["m"]', '["m"]', '["m"]', "false"),
        "refinement": "the faithful real patch only removes the released name "
                      "from the lookup-index mapping when its coordinate is also "
                      "being discarded, leaving a stale index entry behind "
                      "otherwise. The F2P suite asserts that after a non-"
                      "discarding release the name is NO LONGER among the "
                      "container's indexes (it has become a plain coordinate) — "
                      "test_reset_index and the drop=False arms of "
                      "test_reset_index_drop_convert both check the index "
                      "mapping directly. A stale entry fails those assertions, "
                      "and it is also the dangling index-backed state behind the "
                      "issue's broken-repr symptom class. The faithful patch "
                      "does NOT resolve.",
        "rationale": "refuted by clause C1, `result.indexNames = removeAll "
                     "c.indexNames resetNames`, at the binder point drop=false: "
                     "C1's removal is UNCONDITIONAL — the flag governs only "
                     "dropVariables in C2/C3 — so C1 demands the index "
                     "collection [\"m\"] become [], while the rival, having "
                     "gated the index channel on the flag, returns it unchanged. "
                     "This is the case that pins C1's INDEPENDENCE from `drop`; "
                     "without it a rival conflating the two channels would "
                     "verify. `decide` closes the witness against the rival and "
                     "the frozen solution reports it false.",
    },

    # -- reject-var-kept: the C2 mirror of the pre-patch drift ----------------
    # Subtract the discard channel from the coordinate set but NOT from the
    # stored variables. A discarded coordinate keeps its stored array while
    # ceasing to be a coordinate — the same two-collection drift as the pre-patch
    # bug, in the opposite direction. No nagini counterpart: the attack is
    # available here because C2 and C3 share `dropVariables` and are pinned
    # SEPARATELY, so each is refutable while the other holds.
    # WITNESS at (c={vars:[s,t], coords:[t], idx:[t]}, reset=[t], drop=true):
    # C2 demands the stored names become [s] but the rival returns [s,t].
    # BUILT: rival exit 0, gold exit 1.
    {
        "id": "reject-var-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD + _GOLD_LOOP
            + "  let indexNames := removeAll c.indexNames dropIndexes\n"
              "  let varNames := c.varNames\n"
              "  let coordNames := removeAll c.coordNames dropVariables\n"
              "  return { varNames := varNames, coordNames := coordNames, "
              "indexNames := indexNames }\n"
        ),
        "witness": _witness('["s", "t"]', '["t"]', '["t"]', '["t"]', "true"),
        "refinement": "the faithful real patch takes the discarded name out of "
                      "the coordinate collection but never deletes its stored "
                      "array. The array then lingers as an ordinary "
                      "(non-coordinate) stored variable, so a discarding release "
                      "silently PROMOTES the released coordinate into a data "
                      "variable instead of removing it. The F2P suite asserts "
                      "the discarded name is absent from the container "
                      "altogether after a drop=True release — "
                      "test_reset_index_drop_dims checks the resulting variable "
                      "set, and the drop=True arms of "
                      "test_reset_index_drop_convert assert the name is gone — "
                      "and it would also inflate the count of data variables the "
                      "issue is about. The faithful patch does NOT resolve.",
        "rationale": "refuted by clause C2, `result.varNames = removeAll "
                     "c.varNames dropVariables`, at the binder point drop=true "
                     "with the released name NOT the only stored name: C2 "
                     "demands the stored names [\"s\", \"t\"] become [\"s\"], "
                     "while the rival returns them unchanged. C3 still holds for "
                     "this rival, so it is refutable ONLY because C2 is pinned "
                     "separately from C3 even though the two share the derived "
                     "dropVariables — the mirror of reject-coords-unsubtracted, "
                     "and the reason both clauses need their own case. `decide` "
                     "closes the witness against the rival; the frozen solution "
                     "reports it false.",
    },

    # -- reject-identity: PARTIAL-DOMAIN — release nothing --------------------
    # Return the three input collections untouched. Correct ONLY when
    # resetNames is empty; wrong on every input that actually releases a name.
    # nagini's `reject-identity-teardown`. The witness uses a TWO-name
    # resetNames so the battery's traversal length is not pinned at one.
    # WITNESS at (c={vars:[p,q,r], coords:[p,q], idx:[p,q]}, reset=[p,q],
    # drop=true): all three clauses demand removals; the rival makes none.
    # BUILT: rival exit 0, gold exit 1.
    {
        "id": "reject-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD
            + "  let mut dropIndexes : List String := []\n"
              "  let mut dropVariables : List String := []\n"
              "  for name in resetNames do\n"
              "    dropIndexes := dropIndexes\n"
              "    dropVariables := dropVariables\n"
              "  let indexNames := c.indexNames\n"
              "  let varNames := c.varNames\n"
              "  let coordNames := c.coordNames\n"
              "  return { varNames := varNames, coordNames := coordNames, "
              "indexNames := indexNames }\n"
        ),
        "witness": _witness('["p", "q", "r"]', '["p", "q"]', '["p", "q"]',
                            '["p", "q"]', "true"),
        "refinement": "the faithful real patch is a no-op release: it computes "
                      "the released names and then rebuilds the container from "
                      "the ORIGINAL three collections, so nothing is ever "
                      "removed. Releasing a dimension index would leave that "
                      "index live, which is the very thing the operation exists "
                      "to undo: test_reset_index asserts the index is gone "
                      "afterwards, test_reset_index_drop_dims asserts the "
                      "discarded variables are gone, and every arm of "
                      "test_reset_index_drop_convert checks at least one removal. "
                      "All fail. The faithful patch does NOT resolve.",
        "rationale": "refuted by all three clauses simultaneously — C1 (the "
                     "index collection must lose resetNames), C2 and C3 (both "
                     "must lose dropVariables, which is resetNames here since "
                     "drop=true) — at a point where resetNames has TWO names, "
                     "so the battery does not pin the traversal to length one. "
                     "The rival is correct only on the empty-resetNames "
                     "sub-domain, which is the partial-domain shape nagini's "
                     "identity rival attacks. `decide` closes the witness "
                     "against the rival; the frozen solution reports it false.",
    },
]
