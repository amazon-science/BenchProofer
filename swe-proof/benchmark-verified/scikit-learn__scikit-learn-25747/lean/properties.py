"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25747 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each SPEC
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region —
or, for the case that legitimately re-proves, inside ``-- proof-start`` /
``-- proof-end`` — is changed, so ``markers.same_spec`` holds and the single
``theorem correct_buildOutputContainer`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed; ``expect:"reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts a single function too, but over a MUTABLE carrier: a heap-allocated
container lent at full permission plus two supplied label sets lent at HALF
permission, with the payload shape passed as two separate scalars. This Lean
bundle models the same wrapping decision as ONE total function over an immutable
input, so the nagini permission lane collapses (see the class read below) while
the VALUE lane ports across essentially intact and in fact widens: the shape
scalars become the payload itself, which makes both positional-default axes
attackable at once. The per-case correspondence to nagini (and every principled
omission) is in the module ``assessment`` of the submitted payload.

DEFENDED SURFACE (one modeled obligation). The produced container is exactly the
one the wrapping rule selects, for every input. The postcondition pins ``result``
to a single grounded computation over the inputs, so it decomposes into these
independent top-level clauses, selected by the input's runtime category:

  * the non-tabulable payload is REJECTED with the error outcome;
  * already-a-table, labels supplied — the supplied column labels are applied;
  * already-a-table, labels absent — the table's OWN column labels are kept;
  * already-a-table, ALWAYS — the table's OWN row index is kept and its payload
    carried through unchanged, regardless of any caller-supplied row index. BOTH
    directions of "regardless" carry their own rival: an index supplied and
    forced on (``riv-supplied-index-forced``), and no index supplied but the
    table re-indexed positionally anyway
    (``riv-table-index-positional-when-absent``, added by audit — the first rival
    is definitionally gold on the whole ``index = none`` sub-domain, so it could
    not speak for that half);
  * a fresh table, labels supplied / absent — the supplied column labels, else
    the positional labels sized to the payload's WIDTH;
  * a fresh table, index supplied / absent — the supplied row index, else the
    positional index sized to the payload's HEIGHT.

The BEHAVIOURAL DISCRIMINATOR (the fix): when the data already carries its own
row index, that index survives — a caller-supplied index does not apply to it.
The clause is load-bearing in exactly the direction the tests observe: a
transformer that re-labels its own rows must not be forced back onto the caller's
labels. ``riv-supplied-index-forced`` IS that pre-fix behavior, and mirrors
``Solution_prepatch.lean`` (G-DIFF).

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Nagini's two MANDATORY rivals write
    back through a supplied label set held at half permission, so the rejection
    comes from the permission system rather than the postcondition. Lean is
    referentially transparent: an input carries no heap permission, there is no
    read-only fraction to overwrite and no aliasing to exploit, so neither rival
    has an expressible instance here. No substitute is fabricated. (nagini cases
    2 and 2b.)

    AUDIT DEMONSTRATION (the class is asserted vacuous above, so it is now also
    measured rather than argued). The nearest expressible analogue of nagini's
    no-op write ``columns[0] = columns[0]`` is to rebind the supplied set locally
    before applying it — ``cols2 := some (c.set 0 (c.getD 0 ""))`` — since a
    local rebind is the only "write" an immutable value admits. Built: the variant
    passes the scope check (``variant_problems`` = ``[]``) and does NOT verify,
    but a witness at a table with a label set supplied does NOT hold of it
    (exit 1, residue ``unsolved goals``) — because ``c.set 0 (c.getD 0 "")`` is
    the identity on ``c``, so the variant is OBSERVABLY GOLD. That is the
    collapse, machine-checked: with no permissions to violate the rival reduces to
    a reshape, and shipping it would be a vacuous case attesting to a tactic
    mismatch. Dropped for that demonstrated reason, not for difficulty.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE, but NOT for the reason an
    earlier revision of this docstring gave. That revision claimed "a diverging
    implementation cannot be written at all" because the impl is a total Lean
    ``def``. AUDIT CORRECTION: that claim is FALSE and was measured false. The
    impl region may be replaced by

        partial def implementation_buildOutputContainer … :=
          implementation_buildOutputContainer input columns index

    which is a self-recursive non-terminating impl, introduces no new top-level
    name, and passes the scope check clean (``variant_problems`` = ``[]``). A
    second shape diverging only on the rejection arm and gold-correct elsewhere
    passes scope too. So the class is EXPRESSIBLE here; the docstring was wrong.

    What the measurements actually show is that the class is not a spec hole and
    is nonetheless not shippable as a reject case:

      - NOT A SPEC HOLE. Neither diverging variant VERIFIES (both exit 1). A
        ``partial def`` is opaque — Lean generates no equation lemmas for it — so
        the frozen obligation's ``unfold`` cannot even reduce it (``Tactic
        `unfold` failed to unfold `implementation_buildOutputContainer```). The
        spec does not admit the diverging behavior, which is the direction that
        would have made this a finding on the spec.
      - NOT ATTRIBUTABLE, so not shippable. No witness discriminates. An
        UNCONDITIONED refutation at the rejection arm cannot be closed against
        the rival at all — the opaque ``partial`` term does not reduce, so
        ``simp``, ``simp [implementation_buildOutputContainer]``, ``decide`` and
        ``decide +kernel`` all fail (measured: four tactic shapes, all exit 1,
        residue ``¬implementation_buildOutputContainer InputData.sparse none none
        = Except.error …`` or ``failed to synthesize Decidable``). Conditioning
        on that disequality by HYPOTHESIS does close it against the rival (exit
        0) — but the SAME conditioned witness also elaborates against the frozen
        solution (exit 0), because the hypothesis is exactly the refutation and
        gold's own reduction is not consulted. The gate reads that as
        ``witness-vacuous``, correctly: it asserts something true of any impl.
        (The consistency probe cannot rescue it either — it fails to derive
        ``False``, i.e. the hypothesis is satisfiable, so the forgery passes the
        one screen that exists.)

    So the honest disposition is a MEASURED LIMITATION of this carrier's
    attributability, not a vacuous class and not a spec hole: the rejection is
    real but is caused by term opacity rather than by a clause, which is exactly
    what the witness requirement exists to refuse to credit. Recorded rather than
    shipped. (Contrast the velvet backend under partial termination semantics,
    where the analogous class IS a known spec hole per
    ``the corpus-wide termination-semantics finding`` — there the diverging impl VERIFIES. That
    does not apply here.) The nagini sibling carries no such case either.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, as nagini also records. ``result`` is
    pinned equal to a term built only from the inputs; the bundle declares no
    ``opaque`` callee and consumes no ``axiom``, so there is no answer key an
    implementation could echo without doing the work. Every reject witness below
    is therefore stated at literal inputs and needs no conditioning: none of the
    nine binds a hypothesis, so no consistency probe arises.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Rivals
    correct on part of the domain but diverging where a clause bites: forcing the
    supplied index onto data that has its own, positionally re-indexing such data
    when no index is supplied, never applying supplied labels, clobbering the
    labels that should be kept, dropping the payload, ignoring a supplied axis
    when building fresh, sizing each positional default axis off the wrong
    dimension, and accepting the payload that must be rejected.

  * SUPPLIED-AXIS SWAP (nagini case 4's other half) — INEXPRESSIBLE, and this is
    a TYPE fact rather than a difficulty. Nagini carried both label axes as
    ``List[int]``, so stamping the supplied ``index`` onto the column axis and
    ``columns`` onto the row axis type-checked there. Here the axes have
    DIFFERENT types (``cols : List String``, ``idx : List Int``), so the swap does
    not elaborate at all: measured, it fails with ``Type mismatch: i has type
    List ℤ but is expected to have type List String`` — a variant that does not
    compile is not a rival the spec rejects, it is a non-variant. The DEFAULT-axis
    swap, which does type-check because both defaults are computed from the
    payload, is carried by ``riv-fresh-default-axes-swapped``; that is where
    nagini's axis-confusion class genuinely lands on this carrier.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was built BOTH ways before shipping and seen
to hold of its rival and to FAIL on the frozen solution, so it discriminates
rather than asserting a tautology.

Three carrier facts drive the witness tactics. First, ``decide`` cannot be
applied to the spec predicate DIRECTLY: ``Except String DataFrame`` has no
``DecidableEq`` instance (the error arm carries a ``String``), and a bare
``decide`` on an unreduced witness goal reports ``failed to synthesize
Decidable`` — measured. The imperative ``Id.run do`` skeleton is discharged
instead by ``simp only [Id.run, bind, pure, Id.instMonad]``. Second, the
positional-default helpers do not reduce under that alone; the witnesses touching
them add ``simp [ndColumns, ndIndex, List.range_succ]``.

Third — and this CORRECTS an earlier reading of this carrier — a divergence
landing on ``toString`` applied to a positional number IS closable. ``simp``
alone leaves the residue ``¬toString 0 = "feat1"``, but that residue is a
decidable ``String`` disequality, so a ``decide`` AFTER the two ``simp`` steps
closes it (``_T_DEC``); gold then fails with ``decide proved that the
proposition False is false``, a semantic refutation. The earlier port therefore
did not need its length-mismatch dodge, and two witnesses paid a real price for
it: they were stated at inputs whose label count CONTRADICTED the payload width
(one label for a two-wide payload; a table declaring two labels over a one-wide
payload). Such a container is not a coherent instance of the modeled carrier —
the wrapping rule's own arithmetic ties a label axis to a payload dimension — so
the divergence those witnesses exhibited was partly an artifact of the
incoherence rather than of the clause under attack. Both are now stated at
COHERENT inputs (label count == payload width) and closed with ``_T_DEC``, and
both were rebuilt against rival and gold to confirm they still discriminate.

BINDER / POINT SPREAD. The spec binds three inputs and the reject witnesses move
every one of them rather than fixing any at a convenient value. ``input`` ranges
over all three runtime categories, and within the already-a-table category over
tables differing in their own labels, own index and payload, and within the
fresh-table category over payloads of differing height AND width (1x3, 2x1, 3x1,
1x2) so that neither positional default can be confused with the other.
``columns`` takes ``none`` and ``some`` at lengths 1 and 2. ``index`` takes
``none`` and ``some`` at lengths 1, 2 and 3. The NINE reject witnesses probe nine
DISTINCT input points; no two rivals share one, so each rationale's claimed
sub-domain is demonstrated at its own input rather than inherited.

Every supplied label set now MATCHES its payload's width, which is a change from
the original port: two witnesses had been stated at label counts contradicting
the payload width purely so that `simp` could close a length difference. A
witness whose input is not a coherent container attributes part of its divergence
to the incoherence rather than to the clause under attack, and the tactic reason
for it turned out to be false (see the carrier facts above). Both are re-stated
at coherent inputs and re-measured.

AUDIT PROBES (independent, beyond the shipped cases; recorded because a battery
should say what was tried and failed to break it, not only what it ships).

  * FOUR further WRONG impls were built and none verified: the fresh-table branch
    returning an emptied payload; the rejection arm reporting a DIFFERENT error
    string; the table branch positionally re-indexing (this one is now shipped as
    ``riv-table-index-positional-when-absent``); and the fresh-table branch
    truncating its column labels to one entry. So the spec pins the payload on
    both branches, the error string's CONTENTS and not merely the outcome
    constructor, and the supplied label set's full length.

  * THREE further CORRECT reshapes were built and all three VERIFY, which is the
    evidence that the spec is not over-fit to the frozen syntactic form beyond the
    two shipped positives: ``Option.getD`` in place of the ``match`` on BOTH arms
    (proof cases the two ``Option``s in the fresh branch); the positional label
    width taken via ``values.head?.getD []`` instead of ``values.headD []`` (proof
    cases the payload); and the supplied-labels choice written as a dependent
    ``if h : columns.isSome then columns.get h``. Each keeps the theorem statement
    byte-identical and introduces no axiom or assumption. They are not shipped
    because the two shipped positives already defend both regions; they are
    recorded here as measurements, not as claims. (AUDIT REFINEMENT of one detail:
    "each needs a proof body a little longer than the frozen one" is true of the
    first two only. Re-measured: the ``Option.getD`` reshape and the
    ``head?.getD`` reshape each FAIL under the frozen tactic body — ``Tactic
    `rfl` failed``, because ``Option.getD`` and ``head?`` do not reduce without
    casing — and each VERIFIES once the proof cases the two ``Option``s (and, for
    the second, the payload list). The dependent-``if`` reshape verifies under the
    frozen tactic body UNCHANGED. All three are genuine correct reshapes the spec
    accepts, so no SPEC-TOO-STRONG hole; the third is simply cheaper than recorded.)

  * A SECOND, INDEPENDENT round of wrong impls was built by the audit — TWELVE
    beyond the shipped rivals — and none verified (all ``Tactic `rfl` failed``).
    Aimed at what the shipped rivals leave unattacked: the fresh payload reversed;
    a different rejection message; the table's supplied labels APPENDED to its own
    rather than replacing them; the fresh positional index off by one; the fresh
    supplied labels de-duplicated; the table's label application skipped when the
    payload is empty; an empty payload rejected as if non-tabulable; the table's
    own labels kept when the supplied set is EMPTY; the fresh supplied index
    ignored when empty; the table's supplied labels SORTED; the fresh positional
    labels 1-based rather than 0-based; and the table's index reset whenever
    labels are supplied. So the spec additionally pins each axis's ORDER and
    MULTIPLICITY (not merely its contents), the positional defaults' exact origin,
    and the empty-list corners of both optional inputs — no sub-domain among these
    is left free. A further probe confirmed the whole obligation is not decidable
    by ``decide`` directly (``failed to synthesize Decidable``), which is the
    carrier fact the witness tactics are built around.

AXIOM lane: EMPTY. The bundle consumes no ``axiom`` and declares no ``opaque``
callee (``meta.json`` records ``axioms: []`` and ``deep_model_references: []``);
the wrapping decision is modeled deeply and validated by G-CONF. The nagini
``AXIOM_TESTS`` was also empty; dropped either way, as the axiom lane is G-AX's
job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25747"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region (or, for the
# admissibility case, the proof region) and is unique in the file — asserted by
# _swap at load, so any drift in Solution.lean breaks the manifest loudly.
# ---------------------------------------------------------------------------

# The rejection arm for the non-tabulable payload.
_I_SPARSE = '      return Except.error "Pandas output does not support sparse data."'

# The whole already-a-table arm: optionally apply supplied labels, return.
_I_TABLE = ('      let mut out := df\n'
            '      if let some c := columns then\n'
            '        out := { out with cols := c }\n'
            '      return Except.ok out')

# The whole fresh-table arm: choose each axis, build the container.
_I_FRESH = ('      let cols := match columns with | some c => c | none => ndColumns values\n'
            '      let idx := match index with | some i => i | none => ndIndex values\n'
            '      return Except.ok { cols := cols, idx := idx, data := values }')

# The frozen proof body's opening (proof region).
_P_FROZEN = ('  intro input columns index\n'
             '  unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult')


# ---------------------------------------------------------------------------
# Witness scaffolding. The spec predicate is stated directly at one concrete
# input and refuted. See the module docstring for why `decide` is unavailable on
# this carrier and which tactic replaces it.
# ---------------------------------------------------------------------------

# Discharge the imperative skeleton, then the residual structural disequality.
_T_PLAIN = ("  simp only [Id.run, bind, pure, Id.instMonad]\n"
            "  simp\n")
# ...plus unfolding of the positional-default helpers, which do not reduce under
# `simp` alone.
_T_RANGE = ("  simp only [Id.run, bind, pure, Id.instMonad]\n"
            "  simp [ndColumns, ndIndex, List.range_succ]\n")
# ...and, when the residue is a `toString`-of-a-positional-number disequality,
# one more step: that residue is a decidable `String` claim even though the spec
# predicate as a whole is not, so `decide` closes it once `simp` has exposed it.
# This is what lets a witness be stated at a COHERENT input (label count equal to
# the payload width) instead of at a length-mismatched one.
_T_DEC = ("  simp only [Id.run, bind, pure, Id.instMonad]\n"
          "  simp [ndColumns, ndIndex, List.range_succ]\n"
          "  decide\n")


def _witness(inp, cols, idx, tac=_T_PLAIN, note=""):
    return (note
            + "example : ¬ problem_spec_buildOutputContainer\n"
              f"    {inp} {cols} {idx}\n"
              "    (implementation_buildOutputContainer\n"
              f"      {inp} {cols} {idx}) := by\n"
              "  unfold problem_spec_buildOutputContainer "
              "implementation_buildOutputContainer containerResult\n"
            + tac)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and retains the frozen tactic
    # body: the reshapes preserve the definitional form, so no helper lemma, no
    # axiom and no assumption token is introduced. Both were built and seen to
    # elaborate with the obligation closed.
    #
    # Ports nagini cases 5a and 5b, whose positives reordered the two
    # independent axis computations and flattened the nested guard of the
    # already-a-table branch. Both reshapes survive the narrowing intact.
    # =====================================================================
    {
        "id": "pos-fresh-axes-reordered",
        "kind": "soundness",
        "expect": "verify",
        # The two axis choices of the fresh-table arm are INDEPENDENT; compute
        # the row axis first and the column axis second. Same container on every
        # input.
        "module": _swap(
            _BASE, _I_FRESH,
            '      let idx := match index with | some i => i | none => ndIndex values\n'
            '      let cols := match columns with | some c => c | none => ndColumns values\n'
            '      return Except.ok { cols := cols, idx := idx, data := values }'),
        "rationale": "the fresh-table arm's two axis computations are reordered "
                     "(row axis first). They read disjoint inputs and neither "
                     "feeds the other, so the produced container is identical on "
                     "every input and `result = containerResult …` still holds. "
                     "Must verify, else the two fresh-table clauses are over-fit "
                     "to the column-first ordering => SPEC-TOO-STRONG. Proof: the "
                     "frozen tactic body is retained (the bindings zeta-reduce). "
                     "Ports nagini's axes-reordered positive (5a).",
    },
    {
        "id": "pos-table-branch-flattened",
        "kind": "soundness",
        "expect": "verify",
        # Replace the mutable-accumulator-plus-guard shape of the already-a-table
        # arm with a flat two-way match returning directly from each arm.
        # Identical decision: apply the supplied labels iff supplied, keep the
        # index and payload either way.
        "module": _swap(
            _BASE, _I_TABLE,
            '      match columns with\n'
            '      | some c => return Except.ok { df with cols := c }\n'
            '      | none => return Except.ok df'),
        "rationale": "the already-a-table arm is reshaped from an accumulator "
                     "updated under a guard into a flat two-way match returning "
                     "from each arm directly. The label decision, the kept row "
                     "index and the carried payload are unchanged on every input, "
                     "so `result = containerResult …` still holds. Must verify, "
                     "else the table-branch clauses are over-fit to the literal "
                     "accumulator shape => SPEC-TOO-STRONG. Proof: frozen tactic "
                     "body retained. Ports nagini's flattened-guard positive (5b), "
                     "and defends a DIFFERENT region than the fresh-table "
                     "positive above.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at the concrete input
    # the failing test exercises, not merely in the abstract. The frozen theorem
    # carries NO precondition hypothesis (the modeled behavior is total, so the
    # `∀` is unguarded), so nagini's self-call precondition probe has no binder
    # to attack here; the honest analogue is to discharge the spec predicate by
    # evaluation at that ground input alongside the frozen obligation. Ports
    # nagini case 6 (admiss-self-call-frame-input), which likewise probed the
    # already-a-table shape with both a supplied label set and a supplied index.
    # =====================================================================
    {
        "id": "admiss-ground-table-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the reported scenario's shape — data that
        # is already a table, carrying its own row index, with BOTH a supplied
        # label set and a supplied index present, AND the table's own index
        # DIFFERENT from the supplied one — then close the frozen obligation
        # verbatim. Nothing is assumed: no new declaration, the theorem statement
        # is byte-identical, and the ground instance is a `have` inside the
        # existing tactic body.
        #
        # AUDIT REPAIR. This instance previously used idx := [0, 1] with the
        # supplied index also [0, 1]. At such an input the two candidate
        # behaviors — keep the table's own index, or force the supplied one —
        # AGREE, so the instance was satisfied by both and demonstrated nothing
        # about the clause its rationale claimed. Measured: the old ground `have`
        # discharges against `Solution_prepatch.lean` too (exit 0), i.e. it holds
        # of the pre-fix behavior. The index is now [7, 9] against a supplied
        # [0, 1], where the two behaviors diverge; re-measured, the new `have`
        # FAILS on prepatch with the semantic residue
        #   Except.ok {…, idx := [0, 1], …} = Except.ok {…, idx := [7, 9], …}
        # and still discharges against the frozen impl (exit 0). The claim in the
        # rationale is now actually exercised.
        "module": _swap(
            _BASE, _P_FROZEN,
            '  have _ground : problem_spec_buildOutputContainer\n'
            '      (InputData.dataframe { cols := ["a", "b", "c"], idx := [7, 9], data := [[1, 2, 3], [4, 5, 6]] })\n'
            '      (some ["X0", "X1", "X2"]) (some [0, 1])\n'
            '      (implementation_buildOutputContainer\n'
            '        (InputData.dataframe { cols := ["a", "b", "c"], idx := [7, 9], data := [[1, 2, 3], [4, 5, 6]] })\n'
            '        (some ["X0", "X1", "X2"]) (some [0, 1])) := by\n'
            '    unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult\n'
            '    simp only [Id.run, bind, pure, Id.instMonad]\n'
            + _P_FROZEN),
        "rationale": "the obligation is discharged at the ground input the "
                     "failing scenario exercises — data that already carries its "
                     "own row index, wrapped with BOTH a supplied label set and a "
                     "supplied index present, and its own index DIFFERING from the "
                     "supplied one, which is precisely the configuration in which "
                     "the discriminating clause bites — and then the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at exactly the input the failing "
                     "test observes (the analogue of PRECOND-TOO-STRONG). The "
                     "divergence of the two axes is load-bearing and was measured: "
                     "this ground instance FAILS against the pre-fix behavior "
                     "(`Solution_prepatch.lean`) and holds against the frozen impl, "
                     "so it pins the post-fix decision rather than a point where "
                     "both behaviors agree. Nothing is assumed: no new "
                     "declaration, statement byte-identical, the ground instance "
                     "is a `have` inside the existing tactic body. Ports nagini's "
                     "self-call admissibility probe (6), whose in-domain input was "
                     "the same already-a-table-plus-both-axes shape.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival is a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness, built both ways and SEEN to hold of
    # the rival and fail on the frozen solution.
    # =====================================================================

    # ---- the discriminating clause itself (ports nagini case 1) ----
    {
        "id": "riv-supplied-index-forced",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: when a row index is supplied, force it onto data that
        # already carries its own, overwriting the index the data brought.
        "module": _swap(
            _BASE, _I_TABLE,
            '      let mut out := df\n'
            '      if let some c := columns then\n'
            '        out := { out with cols := c }\n'
            '      if let some i := index then\n'
            '        out := { out with idx := i }\n'
            '      return Except.ok out'),
        "refinement": "this is the pre-fix behavior, and mirrors "
                      "`Solution_prepatch.lean` (G-DIFF). The faithful real patch "
                      "is the base_commit routine left UNCHANGED — the wrapping "
                      "keeps forcing a supplied row index onto data that already "
                      "carries its own. The failing test fits a transformer whose "
                      "output re-labels its own rows and then asserts the wrapped "
                      "result still carries those re-labelled rows; the pre-fix "
                      "behavior replaces them with the caller's original labels "
                      "(and, in the reported aggregation scenario, errors on a "
                      "length mismatch instead). So the faithful patch would NOT "
                      "resolve — this rival verifying would mean the spec admits "
                      "the very behavior the change removes.",
        "rationale": "REJECT from the discriminating clause: when the data is "
                     "already a table its OWN row index is kept regardless of any "
                     "supplied index, so pinning `result` to `containerResult …` "
                     "forbids the overwrite. Refuted at a table carrying index "
                     "[0] with [7] supplied and no labels — the only rival that "
                     "moves the supplied index against a table's own differing "
                     "index. If it verified => SPEC-TOO-WEAK (the spec admits the "
                     "behavior the change removes).",
        "witness": _witness(
            '(InputData.dataframe { cols := ["a"], idx := [0], data := [[1]] })',
            "none", "(some [7])",
            note="-- The data already carries index [0]; [7] is supplied. Gold keeps\n"
                 "-- [0], the rival substitutes [7], so the produced containers differ.\n"),
    },

    # ---- supplied labels never applied on the table branch (nagini case 3) ----
    {
        "id": "riv-columns-never-applied",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain miss: on the already-a-table branch return the data
        # untouched, never applying the supplied column labels.
        "module": _swap(
            _BASE, _I_TABLE,
            '      let out := df\n'
            '      return Except.ok out'),
        "refinement": "a faithful real patch that dropped the application of the "
                      "supplied column labels on the already-a-table path would "
                      "leave such an output carrying its stale labels instead of "
                      "the estimator's feature names. The changed PASS_TO_PASS "
                      "test wraps a table with a fresh label set and asserts the "
                      "result carries THAT set (while asserting the row index is "
                      "the table's own — the two halves of the same assertion); "
                      "with the application dropped the labels stay the table's "
                      "original, so it would NOT resolve.",
        "rationale": "REJECT from the labels-supplied clause of the table branch. "
                     "Accidentally correct on the whole fresh-table branch, on the "
                     "rejection branch, and on the labels-absent sub-domain (where "
                     "the labels are kept anyway) — but wrong the moment a label "
                     "set is supplied for data that is already a table. Refuted at "
                     "a two-wide table with a two-label set supplied and no index. "
                     "If it verified => SPEC-TOO-WEAK (the label application "
                     "unpinned on the table branch).",
        "witness": _witness(
            '(InputData.dataframe { cols := ["a", "b"], idx := [5], data := [[1, 2]] })',
            '(some ["f0", "f1"])', "none",
            note="-- Labels [\"f0\",\"f1\"] are supplied for a table labelled [\"a\",\"b\"].\n"
                 "-- Gold applies them, the rival returns the table untouched.\n"),
    },

    # ---- the labels-ABSENT arm of the table branch (the other half of case 3) ----
    {
        "id": "riv-absent-columns-not-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror-image partial-domain miss: overwrite the table's own labels
        # with positional ones BEFORE the supplied set is (optionally) applied.
        # Correct whenever a label set IS supplied — the overwrite is then
        # itself overwritten — but wrong when none is, where the table's own
        # labels must survive.
        "module": _swap(
            _BASE, _I_TABLE,
            '      let mut out := df\n'
            '      out := { out with cols := ndColumns df.data }\n'
            '      if let some c := columns then\n'
            '        out := { out with cols := c }\n'
            '      return Except.ok out'),
        "refinement": "a faithful real patch that positionally re-labelled an "
                      "already-a-table output whenever no label set was supplied "
                      "would discard the caller's own column names on exactly the "
                      "no-labels path. A PASS_TO_PASS test drives that path (a "
                      "label source that fails is documented to have the same "
                      "meaning as supplying none) and asserts the wrapped table "
                      "still carries its ORIGINAL names; positional labels are not "
                      "those names, so it would NOT resolve. This is a NEAR-MISS "
                      "of the rival above — it agrees with gold on the whole "
                      "labels-supplied sub-domain where that one fails — hence its "
                      "own witness at a labels-absent input.",
        "rationale": "REJECT from the labels-ABSENT clause of the table branch: "
                     "the spec keeps the table's own labels when none are "
                     "supplied, and the rival substitutes positional ones. This "
                     "attacks the sub-domain COMPLEMENTARY to "
                     "riv-columns-never-applied, so the two arms of the label "
                     "decision are each demonstrated at their own input rather "
                     "than one standing in for both. Refuted at a COHERENT table "
                     "(one label over a one-wide payload) whose own label "
                     "\"feat1\" differs from the positional default \"0\", so the "
                     "divergence is in the label VALUE the clause is about. If it "
                     "verified => SPEC-TOO-WEAK (the labels-absent arm unpinned).",
        # AUDIT REPAIR. This witness previously gave its table TWO labels over a
        # ONE-wide payload, so that the divergence would be a length difference
        # closable by `simp` alone. That input is not a coherent container on this
        # carrier (the wrapping rule ties the label axis to the payload width), so
        # part of the exhibited divergence came from the incoherence rather than
        # from the labels-absent clause. Re-stated at a coherent one-label /
        # one-wide table and closed with `_T_DEC`; rebuilt both ways (rival exit 0,
        # gold exit 1 with `decide proved that the proposition False is false`),
        # and a FORGERY dropping the negation was confirmed to fail on the rival
        # (`decide proved that toString 0 = "feat1" is false`), so the gold-side
        # exit code carries information.
        "witness": _witness(
            '(InputData.dataframe { cols := ["feat1"], idx := [0, 1, 2], data := [[1], [2], [3]] })',
            "none", "(some [0, 1, 2])", _T_DEC,
            note="-- No labels supplied, so the table's own [\"feat1\"] must survive.\n"
                 "-- The rival substitutes the positional default [\"0\"] for its\n"
                 "-- one-wide payload, so the kept label differs in value.\n"),
    },

    # ---- the payload must be carried through unchanged (frame analogue) ----
    {
        "id": "riv-payload-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # The table branch returns the container with its payload emptied. The
        # label and index decisions are left exactly as gold makes them, so this
        # isolates the "everything else is carried through" half of the clause.
        "module": _swap(
            _BASE, _I_TABLE,
            '      let mut out := df\n'
            '      if let some c := columns then\n'
            '        out := { out with cols := c }\n'
            '      out := { out with data := [] }\n'
            '      return Except.ok out'),
        "refinement": "a faithful real patch that returned an already-a-table "
                      "output with its cell values discarded would hand back an "
                      "empty table from every such wrapping — the transformed "
                      "values the caller asked for would simply be gone. Every "
                      "test that inspects a wrapped table's contents, including "
                      "the failing one (which reads the result's row labels off a "
                      "two-row payload), observes a container built from the real "
                      "payload, so it would NOT resolve.",
        "rationale": "REJECT from the carry-through half of the table-branch "
                     "clause. This is the referentially-transparent ANALOGUE of "
                     "nagini's frame obligation: with no permissions to violate, "
                     "what remains of 'do not disturb what you were not asked to "
                     "change' is that the spec pins the untouched components "
                     "explicitly, and this rival disturbs one. Only the label "
                     "decision may change on this branch; the payload may not. "
                     "Refuted at a two-row table with neither labels nor index "
                     "supplied — the ONLY witness holding both optional inputs "
                     "absent, which also demonstrates that the spec still "
                     "constrains the result when both are `none`. If it verified "
                     "=> SPEC-TOO-WEAK (an output component left unconstrained).",
        "witness": _witness(
            '(InputData.dataframe { cols := ["u"], idx := [3, 4], data := [[7], [8]] })',
            "none", "none",
            note="-- Neither optional input is supplied, so gold returns the table\n"
                 "-- unchanged; the rival empties its payload.\n"),
    },

    # ---- the table's own index must survive even with NO index supplied -------
    # AUDIT ADDITION. `riv-supplied-index-forced` attacks the kept-index clause
    # only where an index IS supplied: it is literally the identity of gold on the
    # whole `index = none` sub-domain, so nothing in the shipped battery forbade an
    # impl that re-indexes an already-a-table result POSITIONALLY when no index is
    # supplied. That is a distinct wrong behavior in the same clause — the clause
    # says the table's own index is kept ALWAYS, "regardless of any
    # caller-supplied row index", which includes the absence of one — and it was
    # unattacked. Confirmed as a genuine gap by building this rival: it does not
    # verify (`Tactic 'rfl' failed`), and its witness discriminates.
    {
        "id": "riv-table-index-positional-when-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep gold's label decision exactly, then positionally re-index the
        # already-a-table result. Correct on the whole fresh-table branch, on the
        # rejection branch, and on any table whose own index already happens to be
        # positional — but wrong for a table carrying a non-positional index, with
        # or without a supplied one.
        "module": _swap(
            _BASE, _I_TABLE,
            '      let mut out := df\n'
            '      if let some c := columns then\n'
            '        out := { out with cols := c }\n'
            '      out := { out with idx := ndIndex df.data }\n'
            '      return Except.ok out'),
        "refinement": "a faithful real patch that positionally re-indexed an "
                      "already-a-table output would discard the row labels such an "
                      "output carries whenever they are not already 0,1,2,… — the "
                      "exact loss the failing scenario is about, and this variant "
                      "loses them even when the caller supplies no index at all, "
                      "so it is strictly worse than the pre-fix behavior on that "
                      "sub-domain. The failing test reads its result's row labels "
                      "off a re-labelled two-row payload and they are not "
                      "positional, so it would NOT resolve.",
        "rationale": "REJECT from the ALWAYS half of the kept-index clause, on the "
                     "sub-domain `riv-supplied-index-forced` cannot reach: that "
                     "rival agrees with gold everywhere `index` is `none`, so the "
                     "clause's claim that the table's own index survives "
                     "REGARDLESS of a supplied index was demonstrated only in the "
                     "supplied direction. Refuted at a table carrying index [5] "
                     "over a one-row payload with NEITHER axis supplied, where the "
                     "positional index would be [0]. If it verified => "
                     "SPEC-TOO-WEAK (the kept-index clause pinned only against a "
                     "supplied index, not against positional re-indexing).",
        "witness": _witness(
            '(InputData.dataframe { cols := ["a"], idx := [5], data := [[1]] })',
            "none", "none", _T_RANGE,
            note="-- The table carries index [5] and nothing is supplied. Gold keeps\n"
                 "-- [5]; the rival substitutes the positional [0].\n"),
    },

    # ---- fresh-table branch ignores the supplied index (nagini case 4, row axis) ----
    {
        "id": "riv-fresh-ignores-index",
        "kind": "uniqueness",
        "expect": "reject",
        # When building a fresh table, always use the positional row index,
        # ignoring a supplied one.
        "module": _swap(
            _BASE, _I_FRESH,
            '      let cols := match columns with | some c => c | none => ndColumns values\n'
            '      let idx := ndIndex values\n'
            '      return Except.ok { cols := cols, idx := idx, data := values }'),
        "refinement": "a faithful real patch that ignored the supplied row index "
                      "when building a fresh table would positionally re-index "
                      "every freshly-wrapped payload, discarding the row labels "
                      "the caller passed. A PASS_TO_PASS test wraps a plain dense "
                      "payload with an explicit row index and asserts the result "
                      "carries it, so it would NOT resolve. Note this is the "
                      "OPPOSITE error from riv-supplied-index-forced: that one "
                      "applies a supplied index where it must not, this one "
                      "declines it where it must — which is why the change is "
                      "confined to the already-a-table path and does not simply "
                      "drop the supplied index everywhere.",
        "rationale": "REJECT from the index-supplied clause of the fresh-table "
                     "branch. Accidentally correct on the whole table branch, the "
                     "rejection branch, and the index-absent sub-domain (where the "
                     "positional index is right anyway), but wrong whenever an "
                     "index is supplied for a fresh table. Refuted at a two-row "
                     "one-wide payload with a two-element index and a one-label "
                     "set supplied. If it verified => SPEC-TOO-WEAK (the supplied "
                     "row axis unpinned).",
        "witness": _witness(
            "(InputData.ndarray [[1], [2]])", '(some ["c"])', "(some [7, 9])",
            _T_RANGE,
            note="-- Index [7,9] is supplied for a fresh two-row table. Gold uses it,\n"
                 "-- the rival substitutes the positional [0,1].\n"),
    },

    # ---- fresh-table branch ignores the supplied labels (nagini case 4, col axis) ----
    {
        "id": "riv-fresh-ignores-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # When building a fresh table, always use positional column labels,
        # ignoring a supplied set.
        "module": _swap(
            _BASE, _I_FRESH,
            '      let cols := ndColumns values\n'
            '      let idx := match index with | some i => i | none => ndIndex values\n'
            '      return Except.ok { cols := cols, idx := idx, data := values }'),
        "refinement": "a faithful real patch that ignored the supplied column "
                      "labels when building a fresh table would label every "
                      "freshly-wrapped payload positionally, discarding the "
                      "estimator's feature names. A PASS_TO_PASS test wraps a "
                      "plain dense payload with an explicit label set and asserts "
                      "the result carries those labels, so it would NOT resolve.",
        "rationale": "REJECT from the labels-supplied clause of the fresh-table "
                     "branch — the axis complementary to the rival above, "
                     "attacked separately so neither fresh-table axis is left to "
                     "the other's witness. Accidentally correct on the table "
                     "branch, the rejection branch, and the labels-absent "
                     "sub-domain. Refuted at a one-row two-wide payload with a "
                     "matching TWO-label set supplied, whose labels differ in "
                     "VALUE from the positional default [\"0\",\"1\"]. If it "
                     "verified => SPEC-TOO-WEAK (the supplied column axis "
                     "unpinned).",
        # AUDIT REPAIR. This witness previously supplied ONE label for a TWO-wide
        # payload so the divergence would be a length difference closable by `simp`
        # alone. A one-label set for a two-wide payload is not a coherent input on
        # this carrier, so the divergence was partly an artifact of the mismatch
        # rather than of the labels-supplied clause. Re-stated with a coherent
        # two-label set and closed with `_T_DEC`; rebuilt both ways (rival exit 0,
        # gold exit 1 with `decide proved that the proposition False is false`),
        # and a FORGERY dropping the negation fails on the rival (`decide proved
        # that toString 0 = "p" ∧ toString 1 = "q" is false`).
        "witness": _witness(
            "(InputData.ndarray [[1, 2]])", '(some ["p", "q"])', "none", _T_DEC,
            note="-- Two labels are supplied for a two-wide payload. Gold uses the\n"
                 "-- supplied [\"p\",\"q\"]; the rival substitutes the positional\n"
                 "-- default [\"0\",\"1\"], so the labels differ in value.\n"),
    },

    # ---- each positional default sized off the other dimension (nagini 3b + 4) --
    {
        "id": "riv-fresh-default-axes-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Axis confusion on the DEFAULTS: size the positional row index by the
        # payload's width and the positional labels by its height. Correct
        # whenever both axes are supplied, and accidentally correct on a square
        # payload, but wrong on any non-square payload with a default axis.
        "module": _swap(
            _BASE, _I_FRESH,
            '      let cols := match columns with | some c => c | none => (ndIndex values).map (fun i => toString i)\n'
            '      let idx := match index with | some i => i | none => (List.range (values.headD []).length).map (fun i => (i : Int))\n'
            '      return Except.ok { cols := cols, idx := idx, data := values }'),
        "refinement": "a faithful real patch that sized each positional default "
                      "off the wrong dimension would give every freshly-wrapped "
                      "payload a transposed default labelling — as many row "
                      "labels as it has columns and vice versa — so any payload "
                      "that is not square would be mis-sized outright. The dense "
                      "PASS_TO_PASS paths build tables whose default row index "
                      "runs over the sample count and whose default labels run "
                      "over the feature count, so it would NOT resolve on a "
                      "non-square payload.",
        "rationale": "REJECT from BOTH default clauses of the fresh-table branch "
                     "at once (the positional row index sized to the payload's "
                     "height, the positional labels to its width). This is the "
                     "carrier's WIDENING of nagini's two separate shape rivals "
                     "(3b, wrong default row size, and 4, axis swap): there the "
                     "payload shape arrived as two independent scalars, here it is "
                     "the payload itself, so a single rival reading the wrong "
                     "dimension attacks both defaults together. Accidentally "
                     "correct on a square payload and whenever both axes are "
                     "supplied. Refuted at a ONE-row THREE-wide payload with "
                     "neither axis supplied — maximally non-square, so both "
                     "defaults are wrong at once. If it verified => SPEC-TOO-WEAK "
                     "(the default axis sizes unpinned).",
        "witness": _witness(
            "(InputData.ndarray [[1, 2, 3]])", "none", "none", _T_RANGE,
            note="-- A 1x3 payload with both axes defaulted. Gold's positional row\n"
                 "-- index has one entry (one row); the rival's has three.\n"),
    },

    # ---- the rejection branch (unchanged but load-bearing) ----
    {
        "id": "riv-sparse-accepted",
        "kind": "uniqueness",
        "expect": "reject",
        # Accept the non-tabulable payload, returning an empty container instead
        # of the error outcome.
        "module": _swap(
            _BASE, _I_SPARSE,
            '      return Except.ok { cols := [], idx := [], data := [] }'),
        "refinement": "a faithful real patch that accepted a payload which cannot "
                      "be densely tabulated — returning an empty container rather "
                      "than reporting the error — would silently hand back empty "
                      "output where callers are documented to get a diagnostic. A "
                      "PASS_TO_PASS test asserts that wrapping such a payload "
                      "raises with that message, so it would NOT resolve. The "
                      "branch is UNCHANGED by the fix, which is exactly why it "
                      "needs a rival: an unchanged branch is still part of the "
                      "obligation, and a spec that stopped constraining it would "
                      "admit a regression the change was never meant to permit.",
        "rationale": "REJECT from the rejection clause: the spec pins the "
                     "non-tabulable payload to the error outcome and the rival "
                     "returns a success outcome, so the two differ in the outcome "
                     "CONSTRUCTOR, not merely its contents. The only rival "
                     "reaching the third runtime category of `input`, so that "
                     "binder's full range is demonstrated across the reject lane "
                     "rather than two of three values. If it verified => "
                     "SPEC-TOO-WEAK (the rejection branch unpinned).",
        "witness": _witness(
            "InputData.sparse", "none", "none",
            note="-- The non-tabulable payload. Gold reports the error outcome; the\n"
                 "-- rival reports success, so the outcome constructors differ.\n"),
    },
]

# No AXIOM lane: this bundle consumes no `axiom` and declares no `opaque` callee
# (meta.json records axioms: [] and deep_model_references: []). The nagini
# AXIOM_TESTS was empty too; the axiom lane belongs to G-AX and this gate ignores
# it either way.
AXIOM_TESTS = []
