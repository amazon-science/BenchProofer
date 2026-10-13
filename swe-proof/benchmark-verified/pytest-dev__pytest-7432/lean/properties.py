"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7432 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: every case changes only text inside the
``-- impl-start`` / ``-- impl-end`` region, EXCEPT ``admiss-ground-f2p``, which
instead prepends a ``have`` to the tactic body inside ``-- proof-start`` /
``-- proof-end`` and leaves the impl region frozen. Either way
``markers.same_spec`` holds and the ``theorem correct_skipLocationRewrite``
STATEMENT stays byte-identical: no case rewrites the obligation, and no case
needed a new tactic body to close it — the twelve impl-region variants re-use the
frozen script verbatim, and the admissibility case appends to it rather than
replacing it). ``expect:"verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total pure function of seven Boolean observations):

  skipLocationRewrite
      (unexpSuccess runxfail xfailRaised notSkippedXfail
       skippedByMark repSkipped longreprIsTuple : Bool) : Bool

The observable is the single location-rewrite decision. The spec is ONE
top-level clause, a complete equality:

  (C) result = skipLocationCondition skippedByMark repSkipped longreprIsTuple
        where skipLocationCondition a b c = a && b && c

Nothing is left free: the decision is pinned to a conjunction of exactly three
of the seven inputs. That single clause carries TWO independent obligations, and
both are attacked below:

  (C.fires)   all three of the mark-skipped / skipped / structured-triple
              observations hold  =>  the rewrite MUST happen. Notably the four
              expected-failure dispatch observations are ABSENT from the
              right-hand side, so this must hold for every combination of them —
              this is the independence property the issue is about.
  (C.silent)  any one of the three fails  =>  the rewrite must NOT happen; and
              no dispatch observation may make it happen either.

CARRIER NARROWING vs the nagini sibling. The nagini battery contracts a
procedure ``finalize_skip_location(rep, definition_line, ...) -> None`` that
MUTATES a two-field report carrier ``(loc_is_triple: bool, loc_line: int)``
under full write permission, with three postcondition clauses: a shape frame
(P1) pinning ``loc_is_triple`` unchanged, a value clause (P2) pinning the
rewritten line to ``definition_line + 1`` when the rewrite fires, and a frame
complement (P3) pinning the line unchanged otherwise. This Lean bundle models
only the purely functional CORE of that operation — the *gating decision* — and
drops both the carrier and the rewritten value:

  * nagini ``rep.loc_is_triple`` (a mutable carrier field, both READ by the
    guard and framed by (P1))  ->  the plain input ``longreprIsTuple``. It is an
    input observation here, not a mutable field, so it has no frame obligation.
  * nagini ``rep.loc_line`` / ``definition_line + 1`` (the rewritten VALUE)
    ->  not modeled at all. This bundle's result is the Boolean "was the
    location rewritten?", so the arithmetic of *what* it was rewritten to is
    outside the surface (that computation is unchanged by the modeled behavior,
    and mapping.md records it as out of scope).
  * nagini's (P2)/(P3) implication pair (fires => value pinned / does not fire
    => value framed)  ->  collapse into the single equality (C), because with no
    stored value the only observable left IS whether the rewrite fired. So the
    two nagini clauses become the two halves (C.fires)/(C.silent) of one clause.

ADVERSARIAL READ of the nagini classes on this carrier:

  * CONTROL-FLOW-EFFECT (nagini ``rej-prepatch-elif``) — APPLIES, and is the
    load-bearing rival. Chaining the rewrite onto the tail of the
    mutually-exclusive dispatch means an earlier dispatch arm firing suppresses
    it. Ported as dispatch-gated, refuted by (C.fires).

  * PARTIAL-DOMAIN on the option that governs expected failures (nagini
    ``rej-runxfail-guard``) — APPLIES. Ported as option-gated: the same
    suppression written as an explicit guard rather than as chain linkage.
    Refuted by (C.fires) on the sub-domain the chain rival cannot reach (see
    NEAR-MISS note below).

  * PARTIAL-DOMAIN over-firing (nagini ``rej-overfire``) — APPLIES, and SPLITS
    into THREE rivals here rather than one. Nagini drops the skip-mark conjunct;
    on this carrier each of the three conjuncts is a separate input binder, so
    dropping the skip-mark observation (no-mark-check), dropping the
    reported-outcome observation (no-skipped-check) and dropping the
    structured-triple observation (no-triple-check) are three distinct wrong
    impls, refuted at three different input points. All from (C.silent).
    Dropping ONE conjunct is the only way to attribute a rejection to that
    conjunct: at a point where several conjuncts fail at once, the rejection is
    explained by any of them, so a battery missing the drop-one rival for some
    conjunct never demonstrates that the spec reads that conjunct at all.

  * OFF-DOMAIN WRITE (nagini ``rej-touch-else``) — APPLIES. Ported as
    always-rewrite: decide the rewrite unconditionally. Refuted by (C.silent).

  * NO-OP (nagini ``rej-noop``) — APPLIES. Ported as never-rewrite. Refuted by
    (C.fires).

  * VALUE-FRAME MUTATION (nagini ``rej-frame-mutation``, which writes the
    carrier's shape field and violates (P1)) — DROPPED, not expressible. That
    rival's whole content is that a procedure MUTATES an input field it was
    supposed to leave alone. Lean is referentially transparent and
    ``longreprIsTuple`` is an immutable Bool argument, so there is no field to
    write and (P1) has no counterpart in this spec (see CARRIER NARROWING). Its
    nagini rationale already records that the permission-frame variant is N/A
    even there — full permission, no half-permission reference to abuse — so
    this is the value-frame analogue collapsing one level further. No
    substitute is fabricated.

  * OFF-BY-ONE / value-level (nagini ``rej-offbyone``, storing the line without
    the ``+ 1``) — DROPPED, not expressible. The rewritten line VALUE is not
    modeled here (see CARRIER NARROWING), so an impl that rewrites to the wrong
    line is indistinguishable from gold on this carrier: both decide "the
    rewrite happened". It is not that the rival is hard to refute — there is no
    term in the spec it could contradict, so it is not wrong on this carrier.
    Reported rather than faked.

  * ADMISSIBILITY (nagini ``admiss-f2p``, a self-call establishing ``Requires``
    on an F2P-shaped input) — PORTED, as ``admiss-ground-f2p``. An earlier
    revision of this battery dropped it as vacuous on the ground that "the
    frozen obligation has no precondition", which is NOT a sufficient reason:
    the analogue on a total carrier is not a precondition to satisfy but the
    obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
    positive that discharges the obligation at that concrete input — by
    evaluation, as a ``have``, before closing the frozen obligation verbatim —
    tests directly. That is what the shipped case does, and it is
    load-bearing rather than decorative: the same ``have`` block FAILS to
    elaborate against each of the three gating rivals (measured), because it
    pins the modeled decision to ``true`` at the F2P point rather than merely
    restating the spec there.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. The
    docstring previously recorded this as vacuous on the ground that "a
    diverging implementation cannot be written at all" on a total Lean carrier.
    That is false as stated, and it was measured: a ``partial def`` rival —
    either an auxiliary spinner or ``implementation_skipLocationRewrite`` made
    self-recursive on the rewrite branch — passes the variant scope check and
    is REJECTED by the frozen tactic (exit 1). What blocks the case is the
    WITNESS half, in both available forms:

      - a no-hypothesis witness over the shared vocabulary cannot refute it —
        ``decide`` reports ``instDecidableNot did not reduce``, because the
        diverging term has no value to compute, so the rival build fails and
        the case would record ``witness-unproven``;
      - a hypothesis-conditioned witness (the technique for opaque carriers)
        DOES elaborate against the rival, but it fails the discrimination
        half. Over an auxiliary spinner the hypothesis names a symbol the
        frozen solution does not declare, which ``witness_scope_problems``
        rejects (gold's failure would be an unknown name, not a satisfied
        spec). Made self-recursive so the hypothesis stays in shared
        vocabulary, the witness elaborates against the frozen solution TOO
        (exit 0, measured): the hypothesis ``implementation_… = false`` is
        simply false of gold, so gold's own decision contradicts it and the
        refutation goes through vacuously. Not a discriminator either way.

    So the class is shippable on neither witness form on this carrier. That is
    a hole in what this gate can attest, recorded here rather than dressed up
    as completeness. (The nagini sibling carries no divergence case either;
    this bundle sets no ``loom.semantics.termination``, so the velvet
    total/partial split in the corpus-wide termination-semantics finding does not apply.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS, as the nagini sibling also records. The
    spec unfolds the decision into a conjunction of actual input observations;
    there is no opaque callee or answer-key to echo. meta.json ``axioms == []``
    and ``deep_model_references == []``, so AXIOM_TESTS is EMPTY (the axiom lane
    is G-AX's job regardless).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen ``cases … <;> rfl`` script is tuned to
the frozen form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at one CONCRETE input over ``decide``-able Boolean literals. Each was
built and checked BOTH ways: it elaborates against its rival and FAILS on the
frozen solution (gold's failure is ``decide`` reporting the negation is FALSE at
that input — i.e. gold satisfies the spec there — not an elaboration accident).
No witness binds a hypothesis: every input is a literal, so no witness can have
inconsistent assumptions (the gate's consistency probe accordingly has nothing
to probe and is skipped for all of them).

That gold-side failure was additionally confirmed to CARRY INFORMATION ABOUT THE
CLAIM, rather than being a syntactic accident that would fire whatever the
witness asserted. For each of the eight reject cases, the witness was rebuilt
with its leading ``¬`` DROPPED — i.e. asserting the frozen solution is CORRECT
at that same point — and the exit codes invert exactly: the flipped claim
elaborates against the frozen solution (exit 0, no error) and FAILS against the
rival (exit 1), the mirror image of the real witness. So ``decide`` fully
reduces this carrier in both directions and gold's exit code tracks what is
being claimed. A tautology control (``example : 1 + 1 = 2``) elaborates against
gold, confirming the vacuity half of the contract is live here too.

NEAR-MISS SEPARATION. dispatch-gated and option-gated are both "an earlier
dispatch observation suppresses the rewrite", but they are NOT refuted at the
same point, because option-gated agrees with gold over strictly more of the
domain: it is suppressed only by the expected-failure option, whereas
dispatch-gated is suppressed by any of the four dispatch observations. So each
gets the point that isolates its own claim — dispatch-gated at
``xfailRaised = true`` with the option CLEAR (a point where option-gated is
correct, so this witness genuinely demonstrates the chain-linkage sub-domain),
and option-gated at ``runxfail = true`` with the other three dispatch
observations clear. Similarly no-mark-check, no-skipped-check and
no-triple-check drop the three different conjuncts and are refuted at the three
different points that isolate them.

BINDER + CLAUSE COVERAGE. The spec predicate has seven input binders and the
eight reject witnesses probe EIGHT DISTINCT input points, with every one of the
seven binders taking BOTH Boolean values across them:
  * ``unexpSuccess`` — true at always-rewrite, false elsewhere;
  * ``runxfail`` — true at option-gated, false elsewhere;
  * ``xfailRaised`` — true at dispatch-gated, false elsewhere;
  * ``notSkippedXfail`` — true at xfail-mark-overfire, false elsewhere;
  * ``skippedByMark`` — false at no-mark-check / always-rewrite /
    xfail-mark-overfire, true elsewhere;
  * ``repSkipped`` — false at no-skipped-check / always-rewrite /
    xfail-mark-overfire, true elsewhere;
  * ``longreprIsTuple`` — false at no-triple-check / always-rewrite /
    xfail-mark-overfire, true elsewhere.
Each of the three conjuncts additionally gets a point where it is the SOLE
failing conjunct (no-mark-check, no-skipped-check, no-triple-check
respectively), which is what makes each rejection attributable to that conjunct
rather than jointly to the others; a point where several conjuncts fail at once
attests only that the conjunction failed.
Varying the four dispatch binders is the point of this battery rather than a
formality: they are exactly the inputs the spec's right-hand side OMITS, so a
rival that let any one of them influence the decision is what must be caught —
and each of the four is separately made to influence a rival's decision
(dispatch-gated, option-gated, xfail-mark-overfire) or to fire it spuriously
(always-rewrite). ``pts`` = 8.

The admissibility case adds a NINTH input point, and it is the only point in the
battery that is exercised POSITIVELY rather than as a refutation: the F2P shape
(the expected-failure option enabled, all three rewrite observations holding).
It coincides with option-gated's refutation point deliberately — that is the
input the reported issue is about, and the battery now attests both directions
there: no rival may suppress the rewrite at it (option-gated), and the frozen
obligation is satisfiable at it (admiss-ground-f2p).
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7432"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor -------------------------------------------------------
# The FULL impl-region body, so every replacement lands entirely inside the
# impl region and never touches the spec view or the theorem statement.
_IMPL_GOLD = (
    "def implementation_skipLocationRewrite\n"
    "    (unexpSuccess runxfail xfailRaised notSkippedXfail\n"
    "     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do\n"
    "  let mut locationRewritten := false\n"
    "  -- Expected-failure dispatch: select among mutually exclusive cases (an\n"
    "  -- unexpected success on the call phase; the option that suppresses\n"
    "  -- expected-failure treatment; a raised expected-failure signal; a non-skipped\n"
    "  -- result carrying an expected-failure mark). None of these arms touch the skip\n"
    "  -- location.\n"
    "  if unexpSuccess then\n"
    "    pure ()\n"
    "  else if runxfail then\n"
    "    pure ()\n"
    "  else if xfailRaised then\n"
    "    pure ()\n"
    "  else if notSkippedXfail then\n"
    "    pure ()\n"
    "  -- Independent of the dispatch above: rewrite the reported location of a\n"
    "  -- mark-skipped, structured-triple result to point at the test item.\n"
    "  if skippedByMark && repSkipped && longreprIsTuple then\n"
    "    locationRewritten := true\n"
    "  return locationRewritten"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# Shared fragments, so each variant below differs from gold ONLY in the way its
# id names. `_HEAD` is the signature; `_DISPATCH` is the four-arm
# mutually-exclusive expected-failure dispatch, none of whose arms decides
# anything about the location.
_HEAD = (
    "def implementation_skipLocationRewrite\n"
    "    (unexpSuccess runxfail xfailRaised notSkippedXfail\n"
    "     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do\n"
)
_DISPATCH = (
    "  if unexpSuccess then\n"
    "    pure ()\n"
    "  else if runxfail then\n"
    "    pure ()\n"
    "  else if xfailRaised then\n"
    "    pure ()\n"
    "  else if notSkippedXfail then\n"
    "    pure ()\n"
)


_P_INTRO = (
    "  intro unexpSuccess runxfail xfailRaised notSkippedXfail\n"
    "        skippedByMark repSkipped longreprIsTuple\n"
)

assert _BASE.count(_P_INTRO) == 1, "proof intro drifted; update _P_INTRO"


def _ground(prefix):
    """Frozen file with `prefix` prepended to the frozen tactic body.

    The statement is untouched and the frozen script still runs verbatim after
    the prefix, so the obligation is closed the same way it always was; the
    prefix only adds a `have` that must ALSO be discharged.
    """
    return _swap(_BASE, _P_INTRO, prefix + _P_INTRO)


def _witness(args, note):
    """A refutation snippet: the spec predicate FAILS of the rival at `args`.

    Stated over Boolean literals so `decide` settles it outright; there are no
    binders, hence no assumptions that could be inconsistent.
    """
    a = " ".join(args)
    return (
        note
        + "example :\n"
        + f"    ¬ problem_spec_skipLocationRewrite {a}\n"
        + f"        (implementation_skipLocationRewrite {a}) := by\n"
        + "  unfold problem_spec_skipLocationRewrite implementation_skipLocationRewrite\n"
        + "    skipLocationCondition\n"
        + "  decide\n"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. Each keeps the theorem STATEMENT byte-identical; all four re-use
# the frozen tactic body unchanged (the frozen script splits on all seven Bools
# and closes each leaf by `rfl`, so it survives these reshapes definitionally).
# No helper lemma, axiom, or assumption token is introduced by any of them.
# ---------------------------------------------------------------------------

# (S.reorder) Decide the location rewrite FIRST, then run the dispatch. The
# dispatch arms are all no-ops on the decision, so ordering is unobservable.
_REORDER_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + "  if skippedByMark && repSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + _DISPATCH
    + "  return locationRewritten"
)

# (S.collapse) Drop the dispatch entirely — every arm is a no-op on the
# decision, so the cheapest honest impl keeps only the rewrite decision.
_COLLAPSE_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + "  if skippedByMark && repSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (S.direct) The imperative `Id.run do / let mut / if` collapsed into a direct
# functional definition returning the conjunction.
_DIRECT_IMPL = (
    "def implementation_skipLocationRewrite\n"
    "    (unexpSuccess runxfail xfailRaised notSkippedXfail\n"
    "     skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=\n"
    "  skippedByMark && repSkipped && longreprIsTuple"
)

# (S.commuted) The three observations tested in the reverse order. `&&` on Bool
# is commutative and all three are already-evaluated values, so the decision is
# unchanged on every input.
_COMMUTED_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if longreprIsTuple && repSkipped && skippedByMark then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (S.let) The mark-skipped part of the condition bound to a local first, then
# combined with the structured-triple observation.
_LET_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  let markSkipped := skippedByMark && repSkipped\n"
    + "  if markSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input, checked to hold of the rival and to fail on
# the frozen solution.
# ---------------------------------------------------------------------------

# (U.dispatch-gated) The rewrite decision hangs off the TAIL of the
# mutually-exclusive dispatch, so any earlier dispatch observation suppresses it.
_DISPATCH_GATED_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + "  if unexpSuccess then\n"
    + "    pure ()\n"
    + "  else if runxfail then\n"
    + "    pure ()\n"
    + "  else if xfailRaised then\n"
    + "    pure ()\n"
    + "  else if notSkippedXfail then\n"
    + "    pure ()\n"
    + "  else if skippedByMark && repSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.option-gated) The suppression written as an explicit guard on the option
# that governs expected failures, instead of as dispatch linkage.
_OPTION_GATED_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if (!runxfail) && skippedByMark && repSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.no-mark-check) Drop the skip-mark observation from the condition: rewrite
# for ANY skipped result whose location is a structured triple.
_NO_MARK_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if repSkipped && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.no-skipped-check) Drop the reported-outcome observation: rewrite for any
# result that carries a skip mark and a structured-triple location, whatever its
# reported outcome turned out to be.
_NO_SKIPPED_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if skippedByMark && longreprIsTuple then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.no-triple-check) Drop the structured-triple observation: rewrite for a
# mark-skipped result whatever form its reported location takes.
_NO_TRIPLE_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if skippedByMark && repSkipped then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.never) Never rewrite.
_NEVER_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  return locationRewritten"
)

# (U.always) Rewrite unconditionally, for every reported result.
_ALWAYS_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  locationRewritten := true\n"
    + "  return locationRewritten"
)

# (U.xfail-mark-overfire) Let one dispatch observation ADD a rewrite: a
# non-skipped result carrying an expected-failure mark also gets its location
# rewritten. The reverse polarity of the gating rivals — the dispatch inputs
# must not influence the decision in EITHER direction.
_XFAIL_OVERFIRE_IMPL = (
    _HEAD
    + "  let mut locationRewritten := false\n"
    + _DISPATCH
    + "  if (skippedByMark && repSkipped && longreprIsTuple) || notSkippedXfail then\n"
    + "    locationRewritten := true\n"
    + "  return locationRewritten"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation must be SATISFIABLE at a normal, F2P-shaped
# input, not only in the abstract. On this total carrier the nagini
# precondition-admission self-call has no precondition to establish, so the
# honest analogue is to discharge the spec predicate at the concrete F2P input
# by EVALUATION, as a `have`, and then close the frozen obligation verbatim.
#
# The first `have` is what makes this load-bearing rather than decorative: it
# evaluates the modeled decision at that input down to `true`, so it pins the
# admission to the branch the F2P actually exercises. Merely stating
# `problem_spec … (implementation … )` would be closable without ever showing
# WHICH decision that input produces — it would read the same if the input
# landed in a no-op branch. Measured: this block FAILS to elaborate against
# option-gated, dispatch-gated and never-rewrite alike.
# ---------------------------------------------------------------------------
_ADMISS_GROUND = (
    "  -- Admissibility at the F2P-shaped input: a result skipped by a skip\n"
    "  -- mark, reported as skipped, whose reported location is the structured\n"
    "  -- triple, WITH the expected-failure option enabled. Evaluate the\n"
    "  -- modeled decision there first, so the admission is pinned to the\n"
    "  -- rewrite firing rather than merely restating the spec at that point.\n"
    "  have _fires : implementation_skipLocationRewrite\n"
    "      false true false false true true true = true := by decide\n"
    "  have _ground : problem_spec_skipLocationRewrite\n"
    "      false true false false true true true\n"
    "      (implementation_skipLocationRewrite\n"
    "        false true false false true true true) := by\n"
    "    unfold problem_spec_skipLocationRewrite skipLocationCondition\n"
    "    rw [_fires]\n"
    "    decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — MUST verify.
    # =====================================================================
    {
        "id": "pos-decide-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_REORDER_IMPL),
        "rationale": (
            "a correct reshape that makes the location-rewrite decision BEFORE "
            "running the four-arm expected-failure dispatch instead of after it. "
            "Every dispatch arm is a no-op on the decision, so the order of the "
            "two blocks is unobservable and the result equals gold on all 2^7 "
            "inputs. This is the structural counterpart of the very independence "
            "clause (C) states: if the decision truly does not depend on the "
            "dispatch, it may be taken on either side of it. The frozen tactic "
            "body (split all seven Bools, `rfl` each leaf) closes unchanged — no "
            "helper lemma, axiom, or assumption token. If this failed to verify "
            "the spec would be over-fit to the frozen block order => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-drop-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_COLLAPSE_IMPL),
        "rationale": (
            "the cheapest honest impl: since no dispatch arm decides anything "
            "about the location, drop the dispatch and keep only the rewrite "
            "decision. Equal to gold on every input. The spec grounds the "
            "decision in the three observations directly (there is no opaque "
            "oracle to echo), so this minimal grounded impl is the legitimate "
            "positive control standing in for an echo case. Closes with the "
            "frozen tactic body. Must verify."
        ),
    },
    {
        "id": "pos-direct-conjunction",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_DIRECT_IMPL),
        "rationale": (
            "a correct reshape replacing the imperative `Id.run do / let mut / "
            "if` accumulation with a straight-line functional definition that "
            "returns the conjunction of the three observations. Same value on "
            "every input; a non-recursive definition needing no induction, and "
            "the frozen `cases … <;> rfl` script reduces it definitionally on "
            "each leaf, so it re-proves with the tactic body unchanged. If the "
            "obligation could only be met by the exact imperative shape the spec "
            "would be SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-commuted-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_COMMUTED_IMPL),
        "rationale": (
            "a correct reshape testing the three observations in reverse order. "
            "All three are already-evaluated Bool inputs and `&&` on Bool is "
            "commutative, so the decision is unchanged on all 2^7 inputs. This "
            "is precisely the reshape class that makes a bare `rfl`-based "
            "rejection uninformative on this backend (see WITNESSES in the module "
            "docstring), so it is shipped as a positive control: it MUST verify, "
            "and every reject case is separately backed by a witness rather than "
            "by tactic breakage."
        ),
    },
    {
        "id": "pos-let-bound-subcondition",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_LET_IMPL),
        "rationale": (
            "a correct reshape binding the mark-skipped half of the condition to "
            "a local and then combining it with the structured-triple "
            "observation. `let`-inlining is value-preserving on immutable Bool "
            "inputs, so the decision equals gold everywhere; the frozen tactic "
            "body closes unchanged. Must verify (else SPEC-TOO-STRONG on a "
            "purely syntactic factoring)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — MUST verify.
    # =====================================================================
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ground(_ADMISS_GROUND),
        "rationale": (
            "the obligation is discharged at the concrete F2P-shaped input — a "
            "mark-skipped result, reported skipped, with a structured-triple "
            "location, and the expected-failure option ENABLED — by evaluation "
            "as a `have`, and then the frozen obligation is closed verbatim by "
            "the frozen tactic body. This is the total-carrier analogue of "
            "nagini's precondition-admission self-call: there is no `Requires` "
            "to establish here, but the obligation could still be "
            "UNSATISFIABLE at exactly a normal F2P input, and that is what this "
            "case rules out. It is load-bearing, not decorative: the first "
            "`have` evaluates the modeled decision at that input down to "
            "`true`, so the admission is pinned to the rewrite actually firing "
            "on the sub-domain the reported behavior is about, rather than "
            "restating the spec there — measured, the same block fails to "
            "elaborate against option-gated, dispatch-gated and never-rewrite. "
            "Statement byte-identical, no new declaration, axiom or assumption "
            "token; the frozen script runs unchanged after the prefix. If this "
            "failed to verify, the modeled behavior would be unsatisfiable at "
            "the very input the reported issue is about => the analogue of "
            "PRECOND-TOO-STRONG."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — MUST be rejected.
    # =====================================================================
    {
        "id": "dispatch-gated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DISPATCH_GATED_IMPL),
        "refinement": (
            "chaining the rewrite decision onto the tail of the "
            "mutually-exclusive expected-failure dispatch is the regressed "
            "behavior the issue reports: whenever ANY earlier dispatch "
            "observation holds, the arm that would rewrite the location is never "
            "reached. Its faithful real patch is therefore the unfixed code, and "
            "the F2P observable defeats it directly — the F2P runs a "
            "mark-skipped test with the expected-failure option enabled and "
            "asserts the skip summary names the test's OWN location; with the "
            "decision chained, the option's arm is selected instead and the "
            "summary keeps the internal location where the skip was raised, so "
            "the assertion fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.fires): the spec's right-hand side mentions only "
            "`skippedByMark`, `repSkipped`, `longreprIsTuple`, so when all three "
            "hold the result must be `true` for EVERY combination of the four "
            "dispatch observations. This rival makes the decision depend on them. "
            "Refuted at `xfailRaised = true` with `unexpSuccess = false`, "
            "`runxfail = false`, `notSkippedXfail = false` and all three rewrite "
            "observations `true`: the spec demands `true`, the rival yields "
            "`false`. That point deliberately holds the expected-failure OPTION "
            "clear, so it isolates chain linkage as such rather than the option "
            "(which option-gated attacks separately) — the two near-miss rivals "
            "are refuted at different points. If it verified, the spec would "
            "admit the regressed decision => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "true", "false", "true", "true", "true"),
            "-- Refuted where the rewrite condition holds in full but an earlier\n"
            "-- dispatch observation (a raised expected-failure signal) is also\n"
            "-- present, with the expected-failure option CLEAR: the decision is\n"
            "-- specified independently of the dispatch, so it must still fire.\n",
        ),
    },
    {
        "id": "option-gated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OPTION_GATED_IMPL),
        "refinement": (
            "gating the rewrite on the option that governs expected failures "
            "reproduces the reported behavior semantically while leaving the "
            "dispatch chain alone: with that option enabled the rewrite never "
            "happens. This is exactly the scenario the F2P parametrization was "
            "added for — the same mark-skipped test is run twice, once plainly "
            "and once with the option enabled, and BOTH runs must report the "
            "test's own location. This rival is correct on the first and wrong on "
            "the second, so the added parametrization's assertion fails while its "
            "sibling passes. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.fires): `runxfail` does not appear in the spec's "
            "right-hand side at all, so it cannot suppress the decision. Refuted "
            "at `runxfail = true` with the other three dispatch observations "
            "false and all three rewrite observations true: the spec demands "
            "`true`, the rival yields `false`. This is the NEAR-MISS partner of "
            "dispatch-gated and agrees with gold over strictly more of the domain "
            "(only one dispatch observation suppresses it, not four), so it is "
            "refuted at its own distinguishing point — the one where "
            "dispatch-gated's chain is not even engaged. It also probes the "
            "`runxfail` binder, which no other witness sets. If it verified, the "
            "spec would let an expected-failure-only option govern a "
            "skip-location decision => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "true", "false", "false", "true", "true", "true"),
            "-- Refuted where the rewrite condition holds in full and the option\n"
            "-- that governs only expected-failure handling is enabled: that\n"
            "-- option is absent from the specified decision, so the rewrite must\n"
            "-- still fire.\n",
        ),
    },
    {
        "id": "no-mark-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_MARK_IMPL),
        "refinement": (
            "dropping the skip-mark observation rewrites the location of ANY "
            "skipped result whose reported location is a structured triple — "
            "including skips requested imperatively from inside a fixture or "
            "helper, which are not mark-skips. Those results are supposed to keep "
            "the location where the skip was actually requested; a faithful patch "
            "that widened the condition this way would move them to the test "
            "item's own line instead. Existing skip-reporting P2P tests assert "
            "exactly those helper/fixture locations in the skip summary (a "
            "shared helper's own line, reported for several tests at once), so "
            "they would break. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.silent): with `skippedByMark = false` the "
            "conjunction is `false`, so the spec demands no rewrite. Refuted at "
            "`skippedByMark = false`, `repSkipped = true`, `longreprIsTuple = "
            "true` (all four dispatch observations false): the spec demands "
            "`false`, the rival yields `true`. This probes the `skippedByMark` "
            "binder on its false side while the other two rewrite observations "
            "hold — the point that isolates the dropped conjunct, distinct from "
            "no-triple-check's point. If it verified, the spec would not require "
            "the skip to be a MARK skip => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "false", "false", "false", "true", "true"),
            "-- Refuted on a skipped result with a structured-triple location that\n"
            "-- was NOT skipped by a mark: the specified condition fails, so the\n"
            "-- location must be left alone.\n",
        ),
    },
    {
        "id": "no-skipped-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_SKIPPED_IMPL),
        "refinement": (
            "dropping the reported-outcome observation attempts the rewrite for "
            "any result carrying a skip mark whose reported location happens to "
            "be a structured triple, WITHOUT first checking that the reported "
            "outcome is actually 'skipped'. The mark-carrying observation and the "
            "reported outcome are set at different times and are genuinely "
            "independent: a test can carry a skip mark that did not fire (a "
            "conditional skip whose condition evaluated false), and it then runs "
            "normally and reports its real outcome. A faithful patch that "
            "omitted the outcome check would relocate the reported location of "
            "such a run, so the P2P tests that assert where a non-skipped "
            "outcome is reported for a mark-carrying test — including the "
            "multiple-condition reporting tests, which run a test whose first "
            "condition is false and assert the reported location — would break. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.silent): with `repSkipped = false` the conjunction is "
            "`false`, so the spec demands no rewrite. Refuted at `skippedByMark = "
            "true`, `repSkipped = false`, `longreprIsTuple = true` (all four "
            "dispatch observations false): the spec demands `false`, the rival "
            "yields `true`. This is the THIRD drop-one rival, and the only case "
            "that isolates `repSkipped`: it is the sole point in the battery "
            "where `repSkipped` is the ONLY failing conjunct, so it is the only "
            "case whose rejection is attributable to the spec reading the "
            "reported outcome at all. At every other `repSkipped = false` point "
            "(always-rewrite, xfail-mark-overfire) all three conjuncts fail "
            "together, so those rejections are equally explained by the other "
            "two. If it verified, the spec would not require the reported "
            "outcome to be 'skipped' => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "false", "false", "true", "false", "true"),
            "-- Refuted on a result carrying a skip mark and a structured-triple\n"
            "-- location whose reported outcome is NOT skipped: the specified\n"
            "-- condition fails, so no rewrite may be decided.\n",
        ),
    },
    {
        "id": "no-triple-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_TRIPLE_IMPL),
        "refinement": (
            "dropping the structured-triple observation attempts the rewrite for "
            "a mark-skipped result whose reported location is NOT in the "
            "structured (filename, line, reason) form. The rewrite is defined by "
            "taking that structure apart and putting it back with a new line, so "
            "a faithful patch without the form check would mis-handle results "
            "whose reported location is a plain message instead — either "
            "corrupting the reported text or failing outright while building the "
            "report. Either way the reporting P2P tests over such results break "
            "and the suite does not come clean. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.silent): with `longreprIsTuple = false` the "
            "conjunction is `false`, so the spec demands no rewrite. Refuted at "
            "`skippedByMark = true`, `repSkipped = true`, `longreprIsTuple = "
            "false` (all four dispatch observations false): the spec demands "
            "`false`, the rival yields `true`. This is the SEPARATE half of "
            "nagini's single over-fire rival — on this carrier each conjunct is "
            "its own binder, so it is refuted at the point that isolates the "
            "structured-triple observation, holding the other two true, which is "
            "a different input from no-mark-check's. If it verified, the spec "
            "would not require the reported location to be the structured form "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "false", "false", "true", "true", "false"),
            "-- Refuted on a mark-skipped result whose reported location is NOT\n"
            "-- the structured triple form: the specified condition fails, so no\n"
            "-- rewrite may be decided.\n",
        ),
    },
    {
        "id": "never-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEVER_IMPL),
        "refinement": (
            "deciding no rewrite ever means a mark-skipped result always reports "
            "the internal location where the skip was raised rather than the "
            "test's own definition. That fails the F2P assertion on both of its "
            "parametrizations, and also the pre-existing plain-run assertion "
            "over the same behavior, so the suite is strictly worse off than "
            "before. It does NOT resolve. (Cheap supporting case; the gating and "
            "over-fire rivals above are the primary battery.)"
        ),
        "rationale": (
            "REJECT from (C.fires): with all three rewrite observations true the "
            "spec demands `true`. Refuted at `skippedByMark = repSkipped = "
            "longreprIsTuple = true` and all four dispatch observations false — "
            "the CLEANEST point for the fires half, with no dispatch observation "
            "present to explain the omission: the spec demands `true`, the rival "
            "yields `false`. A verifying no-op would mean the spec never requires "
            "the rewrite at all => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "false", "false", "true", "true", "true"),
            "-- Refuted at the plain mark-skipped structured-triple result, with\n"
            "-- no dispatch observation present: the specified condition holds in\n"
            "-- full, so the rewrite is required.\n",
        ),
    },
    {
        "id": "always-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_IMPL),
        "refinement": (
            "deciding the rewrite unconditionally does report the test's own "
            "location for mark-skipped results, but it also rewrites the reported "
            "location of every OTHER result — passing, failing, and "
            "expected-failure ones alike. A faithful patch that dropped the "
            "condition entirely would relocate failure reports onto the test's "
            "definition line, so the many P2P tests that assert where a failure "
            "or an expected-failure is reported would break wholesale. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.silent): the spec pins the decision to the "
            "conjunction, so on any input where a conjunct fails the result must "
            "be `false`. Refuted at all three rewrite observations false with "
            "`unexpSuccess = true` — a point where nothing about the result is "
            "skip-like at all, and the only witness that probes the "
            "`unexpSuccess` binder on its true side: the spec demands `false`, "
            "the rival yields `true`. If it verified, the spec would leave the "
            "off-condition domain unconstrained => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("true", "false", "false", "false", "false", "false", "false"),
            "-- Refuted on a result that is not skipped at all (an unexpected\n"
            "-- success on the call phase): none of the three conditions holds, so\n"
            "-- the location must be left exactly as reported.\n",
        ),
    },
    {
        "id": "xfail-mark-overfire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_XFAIL_OVERFIRE_IMPL),
        "refinement": (
            "letting a dispatch observation ADD a rewrite means a non-skipped "
            "result carrying an expected-failure mark also has its reported "
            "location relocated to the test item. A faithful patch shaped this "
            "way would move the reported location of expected-failure and "
            "unexpected-pass results, whose reporting several P2P tests assert "
            "(including the strict unexpected-pass message and the "
            "expected-failure reason lines, which are built from the reported "
            "location structure). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C.silent), in the opposite POLARITY to the gating "
            "rivals: the dispatch observations must not influence the decision in "
            "EITHER direction, so a dispatch observation cannot cause a rewrite "
            "any more than it can suppress one. Refuted at `notSkippedXfail = "
            "true` with all three rewrite observations false: the spec demands "
            "`false`, the rival yields `true`. This is the only witness that "
            "probes the `notSkippedXfail` binder on its true side, closing the "
            "last of the four dispatch binders. If it verified, the spec would "
            "permit the expected-failure dispatch to drive a skip-location "
            "decision => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            ("false", "false", "false", "true", "false", "false", "false"),
            "-- Refuted on a non-skipped result carrying an expected-failure mark:\n"
            "-- none of the three conditions holds, so no rewrite may be decided\n"
            "-- however the expected-failure dispatch classified the result.\n",
        ),
    },
]


# No consumed axioms and no deep-model references (meta.json axioms == [],
# deep_model_references == []): the decision is modeled directly over the seven
# observations, so there is no in-model axiom obligation for the PBT axiom lane
# to exercise. The axiom lane is G-AX's job and this gate ignores it.
AXIOM_TESTS = []
