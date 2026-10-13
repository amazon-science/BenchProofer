"""properties.py — G-PBT falsification battery for django__django-16819 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_reduceAddIndex``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the reduction decision as a tag-encoded integer ({0,1,2,3}) over the two
operations' facets, and — CRUCIALLY — models the generic shared fallback
(``super().reduce`` == ``Operation.reduce``) DEEPLY, as the ``@Pure``
``base_combine`` unfolded into a three-branch function of the two elidable flags.
This Lean bundle narrows the carrier: the fallback is an UNCHANGED callee the new
method delegates to, so it is modeled as an opaque A-reference
``baseReduce selfName op appLabel``, and the spec pins the result to
``ReduceResult.replace []`` on the same-name-removal branch and to ``baseReduce
…`` everywhere else. Consequently the nagini base-rule tag lattice's INTERNAL
structure (tags 2/3/0 and their oracle ``base_combine``) is not transparent here:
the three branches of the generic rule collapse into one opaque term, so a rival
that TRANSPOSES two of those branches has no expressible instance.

AUDIT CORRECTION. The port drew a wider conclusion than that — that "the whole
generic-rule outcome collapses into the one opaque term" — and dropped nagini's
only base-rule rival (``swap-base-tags``) on its strength. The narrow claim is
true; the wide one is not. What the opaque term collapses is the CHOICE AMONG the
generic rule's branches, not the requirement that the fallback DEFER to it at
all: an impl that ignores the shared reducer and hardcodes an outcome is still
refutable, because an opaque term needs no computable value to be refuted at,
only a hypothesis — the same technique the port's own ``drop-cancellation``
witness uses. ``fallback-not-deferred`` (added by audit; rival exit 0, gold exit
1, probe exit 1) restores that lane. Each nagini case is mapped to its Lean
counterpart (or its principled omission) in the module ``assessment`` below.

SECOND-AUDIT ADDITION. An independent re-audit rebuilt every case through the real
harness and confirmed the six then-shipped reject witnesses all discriminate
CLAIM-SENSITIVELY, not merely syntactically: each measured rival exit 0 / gold
exit 1 / probe exit 1, and the FORGERY pair settles the gold-side error in every
case — the flipped claim (the spec HOLDS at the witness input) builds exit 0 on
gold and exit 1 on the rival, so gold's exit code tracks what is CLAIMED rather
than how the impl is spelled. Type-revealing builds show the mechanism directly:
on gold the discharged hypothesis has type ``True`` (``simp`` PROVED the equation)
while on the rival it stays a concrete unproven equation. What the re-audit DID
find is one COVERAGE gap: the annihilation outcome's CONSTRUCTOR was unprobed on
the cancellation branch. ``cancel-wrong-payload`` varies the replacement list's
CONTENTS and so never leaves the ``.replace`` constructor, and
``fallback-not-deferred`` does return ``.cannot`` but on the FALLBACK branch, a
different clause over a different sub-domain. ``cancel-wrong-outcome-kind``
(added; rival exit 0, gold exit 1, no consistency probe — the witness binds
nothing) closes it. The same pass also WIDENED the divergence note below: the
earlier text reasoned only about the shape that is REJECTED and thereby
understated the hole, when the shapes that VERIFY are the ones that matter.

THIRD-AUDIT ADDITION. A third independent pass rebuilt all 29 gate inputs (10
variants, 7 witness pairs, 5 consistency probes) through the real harness and
reproduced every recorded exit code exactly: 3 positives exit 0, 7 rivals exit 1,
7 witnesses rival 0 / gold 1, 5 probes exit 1. The FORGERY pair was re-derived
independently for all 7 (not just read): the flipped claim — asserting the spec
HOLDS at each witness's own input — exits 0 on gold and 1 on the rival in all
seven, so gold's exit code tracks WHAT IS CLAIMED and no case is hollow. Both
positives were re-confirmed as genuine re-proofs rather than restatements: the
frozen proof script substituted byte-for-byte fails on each (exit 1) and bare
`rfl` fails on each (exit 1), while both close on the frozen impl (exit 0). Two
DEFECTS were found and are repaired here, both prose-versus-manifest mismatches
rather than hollow outcomes:

  1. ``pos-expr-form``'s rationale claimed "Proof re-authored to `rfl` after
     unfolding". That is FALSE of the shipped module, whose proof is
     `rw [Bool.and_comm]` — and measurably false: bare `rfl` exits 1 on it. The
     inline AUDIT NOTE above the module already said so correctly, so the
     rationale contradicted its own case. Corrected, with the measurements.
  2. The DEFENDED SURFACE note claims the faithful delegation is load-bearing in
     BOTH arguments ("same op, same label"), but only the LABEL half was ever
     demonstrated — ``fallback-wrong-arg`` moves ``appLabel`` and every other
     rival threads ``op`` verbatim, so the operand conjunct was asserted in prose
     and shown by nothing. ``fallback-wrong-operand`` (added; rival exit 0, gold
     exit 1, probe exit 1, flip gold 0 / flip rival 1) closes it.

Attack D (six NEW wrong impls the battery does not contain, aimed at the least
probed binders) found NO spec hole: the frozen spec rejected all six with genuine
unsolved obligations at the spec-pinned value — a guard narrowed by an extra
facet conjunct, a guard matching on name PREFIX rather than equality, a
label-sensitive cancellation, a fallback with selfName and appLabel transposed, a
fallback rebuilding the operand's name field, and the operand-flip that became
the shipped case above. Attack E (five NEW correct reshapes) found NO soundness
hole: `cond` in place of `if`, a dependent `if h :`, the commuted EQUALITY
`op.name == selfName`, a negated guard with the branches exchanged, and
one-conjunct-per-level nested `if`s all VERIFY (exit 0) once the `Id`-bind
residue `(do PUnit.unit; X) = X` is discharged by a trailing `rfl`. Those
first-attempt failures are a TACTIC gap in the attempt and are reported as one,
not as a spec defect.

FOURTH-AUDIT ADDITION. A fourth independent pass rebuilt all 33 gate inputs (11
variants, 8 witness pairs, 6 consistency probes) through the real harness and
reproduced every recorded exit code exactly: 3 positives exit 0, 8 rivals exit 1,
8 witnesses rival 0 / gold 1, 6 probes exit 1. The FORGERY pair (attack B′) was
re-derived independently for all 8: the flipped claim — asserting the spec HOLDS
at each witness's own input — exits 0 on gold and 1 on the rival in every one, so
gold's exit code tracks WHAT IS CLAIMED and no case is hollow. The
type-REVEALING build was run on the four cases whose gold-side error is an
application/type mismatch, and it exhibits the mechanism directly: on
``drop-cancellation`` gold prints ``heq has type True`` (``simp`` PROVED the
equation) while the rival prints the concrete unproven ``baseReduce … =
ReduceResult.replace []``; on the other three the two sides print DIFFERENT
concrete equations, gold's being the (true) ``Id``-bind residue and the rival's
the refutable claim. Both positives were re-confirmed as genuine re-proofs and
not restatements: the frozen proof script substituted byte-for-byte exits 1 on
each and bare ``rfl`` exits 1 on each, while both controls exit 0 on the frozen
impl. The admissibility positive was re-derived rather than read: its ground
instance discriminates (exit 1 against ``drop-cancellation``,
``cancel-wrong-payload`` and ``cancel-wrong-outcome-kind``) and is NOT vacuous
(the NEGATED ground claim on gold exits 1 with ``decide`` proving the negation
false, so ``decide`` is settling this equation rather than closing anything handed
to it). Two DEFECTS were found and are repaired here:

  1. The DEFENDED SURFACE note pins the fallback to the shared reducer's answer
     "for the SAME two operations and the SAME application label" — three
     delegated arguments, of which only two carried a rival.
     ``fallback-wrong-arg`` moves the label, ``fallback-wrong-operand`` moves the
     counterpart operation, and NO case moved the SELF-side argument: every rival
     threaded ``selfName`` verbatim into the shared reducer, so the "same two
     operations" half that describes the add-index operation ITSELF was asserted
     in prose and shown by nothing. The third audit measured this rival
     (``D7_fallback_selfname``) and declined to ship it as "a duplicate point",
     which does not hold: the operand clause it was called a duplicate of is
     about the COUNTERPART operation, a different argument position carrying a
     different modeled quantity. ``fallback-wrong-selfname`` (added; rival exit 0,
     gold exit 1, probe exit 1, flip gold 0 / rival 1) closes it, and all three
     delegated arguments now carry a rival that moves that one and threads the
     other two faithfully.
  2. The attack-E note above claimed ``cond`` "closes with the frozen script's
     own lemma set (exit 0)". That does not reproduce: with the frozen set plus
     ``cond`` it exits 1, both as ``return cond …`` inside the do-block and as a
     pure ``cond`` expression, leaving the residual ``baseReduce … = if false =
     true then … else baseReduce …``. It closes at exit 0 only with ``if_false``
     added and the ``Id``-bind residue discharged by a trailing ``rfl`` — i.e. it
     belongs with the other four reshapes, not apart from them. The CONCLUSION is
     unchanged (the reshape verifies, so there is no soundness hole); the
     measurement claim was wrong and is corrected.

DEFENDED SURFACE (one modeled behavior). The reduction result is fully
determined by a single guard over the two operations' observed attributes:

  * CANCELLATION clause — when the following operation removes an index of the
    SAME name, the pair annihilates: the result is exactly the empty replacement
    list;
  * FALLBACK clause — otherwise the result is exactly whatever the generic
    shared reducer yields for the SAME two operations and the SAME application
    label (pinned to the opaque reference, not left free — frame discipline).

The BEHAVIOURAL DISCRIMINATOR (the fix) is the guard itself: cancel exactly when
the counterpart is a removal AND its target name equals the added index's name;
otherwise defer, unchanged, to the shared reducer. Both conjuncts of the guard,
the annihilation PAYLOAD (the empty list, not some other list), the annihilation
OUTCOME KIND (the replacement constructor, not the sentinel), and the FAITHFUL
delegation in ALL THREE of its arguments (same added-index name, same counterpart
operation, same application label) are load-bearing. Each of those three
delegated arguments carries its own rival that moves exactly that one and threads
the other two verbatim, so no conjunct of the delegation claim rests on another's
rejection.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The two nagini frame-mutation rivals
    (``frame-mutate-is-remove`` an attribute store at 1/2; ``frame-mutate-name``
    a list_pred store at 1/2) have no expressible instance here — a Lean ``def``
    cannot write through its arguments — so no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class, and the
    hole is WIDER than the previous note recorded. (SECOND-AUDIT CORRECTION. The
    earlier note reasoned only about the self-referential ``partial def`` shape
    and concluded, correctly for that shape, that no witness discriminates: it
    has no equational lemma, ``unfold`` cannot reduce it, so the only available
    hypothesis is satisfiable by an opaque term and the witness elaborates against
    the frozen solution too — re-measured here, rival exit 0 AND gold exit 0,
    i.e. ``witness-vacuous``; a ``witness_reference`` to this battery's own
    verifying ``pos-match-guard`` does not rescue it, also exit 0. But that shape
    is the WEAK form of the attack, because it is REJECTED and so understates the
    hole. The strong form VERIFIES. This backend's obligation constrains only the
    VALUE the implementation denotes, and in ``Id`` a discarded iteration
    beta-reduces away, so an unbounded loop spliced ahead of the frozen body
    leaves the frozen proof script closing unchanged. Measured, four shapes, each
    passing ``variant_scope`` with the frozen proof untouched: ``while true do
    pure ()`` exit 0; ``repeat pure ()`` exit 0; ``for _ in Lean.Loop.mk do pure
    ()`` exit 0; and a ``partial`` auxiliary whose result is bound and dropped,
    exit 0. So the spec admits implementations that never produce a value, and no
    ``expect="reject"`` case can be shipped for them — an ``expect="reject"`` case
    requires the variant NOT to verify, and these verify. This is not a defect in
    this spec that a battery could repair: it is a property of the carrier, and it
    is the hole a ``set_option loom.semantics.termination "total"`` line would
    close. No bundle on this backend sets one (measured: 0 of 500), so the class
    is out of reach corpus-wide rather than skipped here. Recorded as a hole so the
    artifact does not overclaim; the nagini sibling closes it with
    ``MustTerminate`` and its ``diverging-self-call`` rival, which has no
    shippable analogue here. G-HYGIENE independently screens the frozen solution
    for every one of these tokens, so the FROZEN artifact cannot carry one — what
    is unattested is the spec's strength against a rival that does.)

  * UNGROUNDED-ORACLE ECHO — N/A as a reject class, exactly as in nagini. The
    postcondition is GROUNDED: ``result`` is pinned to a term built only from the
    inputs (``ReduceResult.replace []`` on the guard, the shared-reducer
    REFERENCE on the fallback). ``baseReduce`` is an A-reference to an UNCHANGED
    callee, not an answer-key for the modeled decision — the impl still must pick
    the branch and, on the fallback, pass the SAME arguments. In its place the
    battery carries honest cheapest-implementation POSITIVE CONTROLS that must
    verify (ports nagini ``pos-master-assert`` / ``pos-reshape``).

  * PARTIAL-DOMAIN / VALUE — APPLIES, the heaviest coverage (as in nagini).
    Rivals that are correct on part of the {cancel, defer} domain but wrong where
    the fix bites: dropping the guard, mis-scoping either conjunct, mangling the
    annihilation payload's CONTENTS, mangling the annihilation outcome's
    CONSTRUCTOR, mis-delegating the fallback LABEL, mis-delegating the fallback
    OPERAND, mis-delegating the fallback SELF-NAME, and skipping the fallback
    delegation altogether. The last four of those eight sit on the fallback clause
    and the first four on the cancellation clause, so both clauses of the modeled
    decision carry rivals rather than only the one the fix adds — and ALL THREE
    delegated arguments the DEFENDED SURFACE note calls load-bearing now carry
    one, rather than the label alone or the label and the operand.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``by_cases … simp`` script is tuned to
the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. Each was checked to
HOLD of its rival and to FAIL on the frozen solution (built both ways with
``scripts/lean_verify.sh``), so it discriminates rather than asserting a
tautology.

CONDITIONING ON THE CARRIER. The fallback result is the opaque ``baseReduce``, so
rivals that err on the CANCELLATION sub-domain (where the spec returns
``.replace []`` but the rival defers) cannot be refuted by evaluation — there is
no value to compute for ``baseReduce``. Their witnesses instead QUANTIFY over it:
they assume one weak hypothesis about the SINGLE opaque term at the witness input
(``baseReduce … ≠ .replace []`` for the drop/mis-scope rivals, or
``baseReduce … "" ≠ baseReduce … "app"`` for the mis-delegation rival — two
DISTINCT opaque terms, jointly satisfiable) and derive the contradiction from
it. That states the refutation over exactly the sub-domain where the rival is
wrong. Rivals whose divergence is entirely concrete (a wrong annihilation
payload) are refuted by plain ``decide`` with no hypothesis.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
predicate rather than fixing them at one convenient point:
  * ``op.isRemoveIndex`` takes both ``true`` (drop-cancellation, drop-nameeq,
    payload, outcome-kind, wrong-operand) and ``false`` (drop-isremove,
    wrong-arg);
  * ``selfName`` / ``op.name`` take the equal case (``"idx"``/``"idx"``,
    ``"col"``/``"col"``, ``"ix"``/``"ix"``) AND the unequal case
    (``"idx"``/``"other"``, ``"nm"``/``"zz"``, ``"kx"``/``"qz"``);
  * ``op.elidable`` takes both ``false`` and ``true`` (payload at ``"col"`` uses
    ``true``; wrong-arg uses ``true``; wrong-operand uses ``true`` and is the
    only rival for which this facet is what the delegation MANGLES);
  * ``selfName`` itself varies (``"idx"``, ``"col"``, ``"nm"``, ``"ix"``,
    ``"kx"``) so no rival holds it fixed;
  * ``appLabel`` is the binder ``fallback-wrong-arg`` demonstrates live
    (``"app"`` vs ``""``), and varies again in ``fallback-not-deferred``
    (``"lb"``), the payload rival (``"lbl"``), the outcome-kind rival
    (``"al"``) and the wrong-operand rival (``"ap"``).
  * the DELEGATED ARGUMENTS are separated three ways, each rival moving exactly
    one and threading the other two verbatim: ``fallback-wrong-arg`` moves the
    LABEL, ``fallback-wrong-operand`` moves the counterpart OPERATION, and
    ``fallback-wrong-selfname`` moves the added index's OWN NAME (``"ax"`` vs
    ``"bx"``, appLabel ``"cx"``). So no conjunct of the faithful-delegation claim
    rests on another's rejection.
No two rivals share a refutation point. The two positives additionally spread the
GUARD's syntactic shape: ``pos-expr-form`` commutes the two conjuncts (so it is
provably NOT definitionally equal to the frozen impl — see its note) and
``pos-match-guard`` replaces the ``if`` with a boolean ``match``.

AXIOM lane: EMPTY here, as in nagini. The bundle declares one ``opaque`` callee
(the unchanged generic shared reducer) validated executably by G-AX as an
A-reference, and consumes no ``axiom``. The axiom lane belongs to G-AX; this gate
ignores it, and the nagini ``AXIOM_TESTS`` (also empty) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16819"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for positives that
# re-prove, the proof region) so same_spec stays byte-identical.

# The whole impl body (the `Id.run do` block: guard + cancel return + fallback).
_I_BODY = (
    "  if op.isRemoveIndex && selfName == op.name then\n"
    "    return ReduceResult.replace []\n"
    "  return baseReduce selfName op appLabel\n"
)

# The guard line + its cancel return (the discriminating early return).
_I_GUARD = (
    "  if op.isRemoveIndex && selfName == op.name then\n"
    "    return ReduceResult.replace []\n"
)

# The cancellation PAYLOAD (the empty replacement list).
_I_PAYLOAD = "    return ReduceResult.replace []\n"

# The fallback delegation line (threading appLabel unchanged).
_I_FALLBACK = "  return baseReduce selfName op appLabel\n"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro selfName op appLabel\n"
    "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
    "  by_cases h : op.isRemoveIndex && selfName == op.name <;>\n"
    "    simp only [h, Id.run, bind, if_true, pure]\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (ports nagini pos-reshape) Structurally-different but CORRECT: the whole
# `Id.run do` procedure is rewritten as a pure `if/else` EXPRESSION returning the
# result directly (no do-block, no `return`), AND the two conjuncts of the guard
# are COMMUTED (`selfName == op.name && op.isRemoveIndex`). Same value on every
# input, so the obligation still holds.
#
# AUDIT NOTE — the commutation is load-bearing, not decoration. With the
# conjuncts in the frozen order this reshape is DEFINITIONALLY EQUAL to the
# frozen impl: `Id.run do if c then return a; return b` and `if c then a else b`
# have the same normal form, so the case's proof closed by bare `rfl` and — the
# measurement that matters — the FROZEN proof script, byte-for-byte unchanged,
# also closed the reshape (built: exit 0). A positive the frozen script already
# proves re-tests nothing; it is a syntactic restatement wearing a reshape's
# label. Commuting `&&` breaks defeq (`Bool.and` is defined by recursion on its
# FIRST argument, so the two guards have different normal forms): the frozen
# script now FAILS on this impl (built: exit 1, `unsolved goals` with the
# commuted guard visible in the residual), and closing it genuinely requires
# `rw [Bool.and_comm]`. So this case now exercises the spec's insensitivity to
# guard-conjunct ORDER, which no other case in the battery touches.
# If this failed to verify, the spec would be over-fit to the exact do-block
# shape and conjunct order => SPEC-TOO-STRONG.
_POS_EXPR = _swap(
    _swap(
        _BASE,
        "def implementation_reduceAddIndex\n"
        "    (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do\n"
        + _I_BODY,
        "def implementation_reduceAddIndex\n"
        "    (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult :=\n"
        "  if selfName == op.name && op.isRemoveIndex then\n"
        "    ReduceResult.replace []\n"
        "  else\n"
        "    baseReduce selfName op appLabel\n",
    ),
    _P_FROZEN,
    "  intro selfName op appLabel\n"
    "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
    "  rw [Bool.and_comm]\n",
)

# (ports nagini pos-master-assert idea: a second correct reshape on the guard)
# The guard is matched as a boolean via `match … with | true => … | false => …`
# instead of `if … then … return`. Semantically identical; a different source
# shape; needs no induction. Proof re-authored (`by_cases` + `simp`) to close it.
_POS_MATCH = _swap(
    _swap(
        _BASE,
        "  if op.isRemoveIndex && selfName == op.name then\n"
        "    return ReduceResult.replace []\n"
        "  return baseReduce selfName op appLabel\n",
        "  match op.isRemoveIndex && selfName == op.name with\n"
        "  | true => return ReduceResult.replace []\n"
        "  | false => return baseReduce selfName op appLabel\n",
    ),
    _P_FROZEN,
    "  intro selfName op appLabel\n"
    "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
    "  by_cases h : op.isRemoveIndex && selfName == op.name <;> simp [h, Id.run, pure]\n",
)

# ADMISSIBILITY (ports nagini admiss-fshape). The frozen theorem carries NO
# precondition hypothesis (the modeled behavior is total, so `∀` is unguarded),
# so the nagini precondition-admission probe has no binder to attack; the honest
# analogue is to discharge the spec predicate at the exact F2P-shaped input (a
# matching RemoveIndex: selfName and op.name both "idx", isRemoveIndex true,
# non-elidable) alongside the frozen obligation. Nothing is assumed: no new
# declaration; the theorem statement stays byte-identical; the ground instance is
# a `have` inside the existing tactic body.
_ADMISS = _swap(
    _BASE, _P_FROZEN,
    "  have _ground : problem_spec_reduceAddIndex \"idx\" "
    "{ isRemoveIndex := true, name := \"idx\", elidable := false } \"app\"\n"
    "      (implementation_reduceAddIndex \"idx\" "
    "{ isRemoveIndex := true, name := \"idx\", elidable := false } \"app\") := by\n"
    "    unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
    "    simp only [Id.run, pure]\n"
    "    decide\n"
    + _P_FROZEN,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (ports nagini drop-cancellation) Drop the cancellation guard entirely: always
# defer to the shared reducer. Correct on the whole non-cancelling sub-domain,
# WRONG on every matching removal (returns the fallback instead of the empty
# list). This IS the pre-gold state.
_RIVAL_DROP_CANCEL = _swap(_BASE, _I_GUARD, "")

# (ports nagini guard-drop-isremove) Mis-scope the guard: cancel on name-equality
# ALONE, dropping the removal conjunct. WRONG on a NON-removal counterpart whose
# name equals the added index name (cancels where it should defer).
_RIVAL_DROP_ISREMOVE = _swap(
    _BASE, _I_GUARD,
    "  if selfName == op.name then\n"
    "    return ReduceResult.replace []\n",
)

# (ports nagini guard-drop-nameeq) Mis-scope the guard the other way: cancel on
# `isRemoveIndex` ALONE, dropping the name-equality conjunct. WRONG on a removal
# of a DIFFERENT-named index (cancels where it should defer).
_RIVAL_DROP_NAMEEQ = _swap(
    _BASE, _I_GUARD,
    "  if op.isRemoveIndex then\n"
    "    return ReduceResult.replace []\n",
)

# (nagini has no exact counterpart — the empty-list payload is a Lean-carrier
# refinement of nagini's tag {1}: attacks the annihilation PAYLOAD.) Cancel on the
# correct guard but return a NON-empty replacement list. Correct branch selection,
# wrong result value on the cancellation sub-domain.
_RIVAL_PAYLOAD = _swap(
    _BASE, _I_PAYLOAD, "    return ReduceResult.replace [op]\n",
)

# (Lean-carrier analogue of nagini's frame/faithful-delegation concern: attacks
# the fallback ARGUMENT threading.) On the fallback path, delegate with a CONSTANT
# application label ("") instead of the actual `appLabel`. Correct branch
# selection, wrong delegation whenever the shared reducer's result depends on the
# label.
_RIVAL_FALLBACK_ARG = _swap(
    _BASE, _I_FALLBACK, "  return baseReduce selfName op \"\"\n",
)

# (ports nagini swap-base-tags — ADDED BY AUDIT.) The port recorded the whole
# generic-rule sub-domain as untestable on this carrier ("the nagini base-rule tag
# lattice is NOT transparent here — the whole generic-rule outcome collapses into
# the one opaque term"), and dropped nagini's only base-rule rival. That reason
# does not survive: an opaque term needs no VALUE to be refuted at, only a
# hypothesis, exactly as the port's own drop-cancellation witness does. This rival
# does not mis-thread an ARGUMENT into the shared reducer (that is
# fallback-wrong-arg's job) — it does not CALL it at all, returning a concrete
# "cannot optimize across" sentinel on the fallback path instead of DEFERRING.
# That is the clause nagini's swap-base-tags attacked: the fallback outcome must
# be whatever the shared reducer yields, not a hardcoded decision.
_RIVAL_FALLBACK_CONST = _swap(
    _BASE, _I_FALLBACK, "  return ReduceResult.cannot\n",
)

# (ADDED BY SECOND AUDIT — the annihilation OUTCOME KIND.) Cancel on the correct
# guard, but answer with the "cannot optimize across" SENTINEL instead of the
# empty replacement list. The frozen spec's own doc-comment calls this
# distinction load-bearing ("the empty list is a genuine outcome distinct from
# the sentinel — it means the pair annihilates"), and every other rival left it
# undemonstrated on the CANCELLATION branch: ``cancel-wrong-payload`` varies the
# LIST CONTENTS (`.replace [op]` vs `.replace []`), which keeps the outcome inside
# the same constructor, so nothing showed that the constructor CHOICE is pinned
# where the pair annihilates. ``fallback-not-deferred`` does return `.cannot`, but
# on the FALLBACK branch, where the spec pins the shared reducer rather than the
# empty list — a different clause and a different sub-domain. Fully concrete on
# both sides (no opaque term), so it is refuted by plain `decide`.
_RIVAL_CANCEL_SENTINEL = _swap(
    _BASE, _I_PAYLOAD, "    return ReduceResult.cannot\n",
)

# (ADDED BY THIRD AUDIT — the delegated OPERAND, as distinct from the delegated
# LABEL.) The DEFENDED SURFACE note claims the faithful delegation is load-bearing
# in BOTH of its arguments ("same op, same label"), but only the label half was
# demonstrated: ``fallback-wrong-arg`` moves the appLabel argument and every other
# rival leaves the `op` argument threaded verbatim. So the manifest asserted a
# conjunct it never showed. This rival delegates the OPERATION itself in mangled
# form — one observed attribute of the counterpart flipped — while threading the
# label faithfully, which is the mirror image of ``fallback-wrong-arg`` and lands
# on the one delegation argument no case had moved. Refuted the same way: the two
# delegations are two DISTINCT opaque terms, so assume only that they differ
# (jointly satisfiable — the consistency probe confirms no tactic derives `False`
# from an inequality between two opaque applications).
_RIVAL_FALLBACK_OPERAND = _swap(
    _BASE, _I_FALLBACK,
    "  return baseReduce selfName { op with elidable := !op.elidable } appLabel\n",
)

# (ADDED BY FOURTH AUDIT — the delegated SELF-NAME, the third and last of the
# three delegated arguments.) The DEFENDED SURFACE note pins the fallback to the
# shared reducer's answer for the SAME two operations and the SAME label, which is
# three delegated quantities; ``fallback-wrong-arg`` moved the label and
# ``fallback-wrong-operand`` moved the counterpart operation, but every rival
# threaded the added index's OWN name verbatim, so the half of "the same two
# operations" that describes the add-index operation itself was asserted in prose
# and demonstrated by nothing. This rival delegates the COUNTERPART's target name
# in that position instead of the added index's name — a plausible confusion
# between two same-typed arguments that agrees with the spec on exactly the
# sub-domain where those two names coincide (which is, notably, the sub-domain the
# cancellation guard already handles, so the error is invisible to every
# cancellation-side probe). Refuted the same way as its two siblings: the two
# delegations are two DISTINCT opaque terms, so assume only that they differ.
_RIVAL_FALLBACK_SELFNAME = _swap(
    _BASE, _I_FALLBACK, "  return baseReduce op.name op appLabel\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-expr-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EXPR,
        "rationale": "structurally-different but correct: the whole do-block is "
                     "rewritten as a pure if/else EXPRESSION (no `Id.run do`, no "
                     "`return`), returning `.replace []` on the guard and the "
                     "shared-reducer reference otherwise. Identical value on every "
                     "input, so `result = (if … then .replace [] else baseReduce …)` "
                     "still holds. The two guard conjuncts are also COMMUTED, "
                     "which breaks definitional equality with the frozen impl "
                     "(`Bool.and` recurses on its FIRST argument), so the proof "
                     "is re-authored as `rw [Bool.and_comm]` after unfolding — "
                     "NOT `rfl`, which fails here (measured: bare `rfl` exits 1, "
                     "`Tactic rfl failed`, and the frozen proof script "
                     "substituted verbatim also exits 1 with `unsolved goals`, "
                     "while both close on the frozen impl at exit 0). No helper "
                     "lemma / axiom / assumption token. Must verify, else "
                     "the spec is over-fit to the do-block shape => SPEC-TOO-STRONG. "
                     "Ports nagini's pos-reshape.",
    },
    {
        "id": "pos-match-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": "second correct reshape on a different region: the guard is "
                     "matched as a boolean (`match … with | true => … | false => …`) "
                     "instead of `if … then … return`. Semantically identical, "
                     "different source shape, no induction. Proof re-authored "
                     "(`by_cases` + `simp [h, Id.run, pure]`). Must verify. Defends "
                     "the guard/branch clause with a correct impl whose branch "
                     "syntax differs from gold. Ports nagini's cheapest-impl "
                     "positive control.",
    },
    {
        "id": "admiss-fshape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at the exact F2P-shaped input (a "
                     "matching RemoveIndex: selfName and op.name both 'idx', "
                     "isRemoveIndex true, non-elidable) by a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at exactly the input the F2P "
                     "exercises — the analogue of PRECOND-TOO-STRONG. Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, the ground instance is a `have` inside the "
                     "existing tactic body. Ports nagini's admiss-fshape.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "drop-cancellation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_CANCEL,
        "refinement": "drops the cancellation guard entirely — the exact pre-gold "
                      "state (the add-index reduction has no override and always "
                      "defers to the generic shared reducer). For the F2P scenario "
                      "(an add-index followed by a same-name remove-index) the pair "
                      "is NOT annihilated to the empty replacement, so the "
                      "optimizer test that asserts the annihilation FAILS; the "
                      "faithful real patch (removing the override) would NOT "
                      "resolve. This is exactly the bug the gold patch fixes.",
        "rationale": "partial-domain == the discriminating bug. Correct on the "
                     "whole non-cancelling sub-domain, WRONG on every matching "
                     "removal (defers to the shared reducer instead of returning "
                     "`.replace []`). Rejection source: the cancellation clause of "
                     "the postcondition. Binder spread: isRemoveIndex=true, "
                     "selfName==op.name (both 'idx'). If it verified => "
                     "SPEC-TOO-WEAK (admits the bug).",
        "witness": (
            "-- Refuted at a matching removal. The spec pins `.replace []` there;\n"
            "-- the rival defers to the opaque shared reducer. `baseReduce` has no\n"
            "-- computable value, so condition on the SINGLE opaque term at this\n"
            "-- input: whenever it differs from the empty-replacement outcome the\n"
            "-- rival's answer differs from the spec's — the sub-domain where the\n"
            "-- rival is wrong.\n"
            "example (h : baseReduce \"idx\" "
            "{ isRemoveIndex := true, name := \"idx\", elidable := false } \"app\" "
            "≠ ReduceResult.replace []) :\n"
            "    ¬ problem_spec_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := true, name := \"idx\", elidable := false } \"app\"\n"
            "      (implementation_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := true, name := \"idx\", elidable := false } \"app\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and, beq_self_eq_true, if_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },
    {
        "id": "guard-drop-isremove",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_ISREMOVE,
        "refinement": "cancels on name equality ALONE (drops the removal conjunct). "
                      "Its faithful real patch would annihilate an add-index "
                      "against ANY following operation that merely carries an equal "
                      "name — not only a removal — silently dropping a real index "
                      "addition and corrupting later migrations. That is not the "
                      "issue's behaviour and breaks the optimizer's cross-operation "
                      "invariants, so it would NOT resolve.",
        "rationale": "partial-domain. Correct unless the counterpart is a "
                     "NON-removal with an equal name, where it wrongly annihilates. "
                     "Rejection source: the fallback clause — on a non-removal the "
                     "guard premise is false so the spec demands the shared-reducer "
                     "result, but the rival returns `.replace []`. Binder spread: "
                     "isRemoveIndex=FALSE, names equal. If it verified => "
                     "SPEC-TOO-WEAK (cancellation under-guarded).",
        "witness": (
            "-- Refuted at a NON-removal (isRemoveIndex=false) whose name equals\n"
            "-- selfName: the spec defers (opaque), the rival annihilates. Condition\n"
            "-- on the single opaque term at this input.\n"
            "example (h : baseReduce \"idx\" "
            "{ isRemoveIndex := false, name := \"idx\", elidable := false } \"app\" "
            "≠ ReduceResult.replace []) :\n"
            "    ¬ problem_spec_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := false, name := \"idx\", elidable := false } \"app\"\n"
            "      (implementation_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := false, name := \"idx\", elidable := false } \"app\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.false_and, beq_self_eq_true, if_true]\n"
            "  intro heq\n"
            "  exact h heq.symm\n"
        ),
    },
    {
        "id": "guard-drop-nameeq",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_NAMEEQ,
        "refinement": "cancels on `isRemoveIndex` ALONE (drops the name-equality "
                      "conjunct). Its faithful real patch would annihilate an "
                      "add-index against a remove-index of an UNRELATED, "
                      "differently-named index, dropping an index addition the "
                      "migration genuinely needs — wrong behaviour that breaks the "
                      "optimizer tests combining independent index operations, so "
                      "it would NOT resolve.",
        "rationale": "partial-domain. Correct unless the counterpart is a removal "
                     "of a DIFFERENT-named index, where it wrongly annihilates. "
                     "Rejection source: the fallback clause — on a removal with a "
                     "different name the guard premise is false (names differ) so "
                     "the spec demands the shared-reducer result, but the rival "
                     "returns `.replace []`. Binder spread: isRemoveIndex=true, "
                     "names DIFFER ('idx' vs 'other'). If it verified => "
                     "SPEC-TOO-WEAK (cancellation over-broad).",
        "witness": (
            "-- Refuted at a removal whose name differs from selfName: the spec\n"
            "-- defers (opaque), the rival annihilates. Condition on the single\n"
            "-- opaque term at this input.\n"
            "example (h : baseReduce \"idx\" "
            "{ isRemoveIndex := true, name := \"other\", elidable := false } \"app\" "
            "≠ ReduceResult.replace []) :\n"
            "    ¬ problem_spec_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := true, name := \"other\", elidable := false } \"app\"\n"
            "      (implementation_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := true, name := \"other\", elidable := false } \"app\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and, if_true]\n"
            "  intro heq\n"
            "  exact h heq.symm\n"
        ),
    },
    {
        "id": "cancel-wrong-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PAYLOAD,
        "refinement": "selects the cancellation branch correctly but returns a "
                      "NON-empty replacement list (keeps the counterpart operation) "
                      "instead of annihilating the pair. A faithful real patch that "
                      "returned a non-empty replacement would leave a spurious "
                      "operation in the optimized plan rather than dropping the "
                      "add/remove pair, so the optimizer test asserting the pair "
                      "collapses to NO operations FAILS; it would NOT resolve. This "
                      "is the Lean-carrier refinement of nagini's cancellation tag "
                      "(the empty list is a genuine outcome distinct from any "
                      "non-empty replacement).",
        "rationale": "partial-domain on the cancellation PAYLOAD. Branch selection "
                     "is correct; the annihilation value is wrong. Rejection "
                     "source: the cancellation clause pins the result to "
                     "`.replace []`, but the rival returns `.replace [op]`. Fully "
                     "concrete (no opaque term), decidable. Binder spread: distinct "
                     "point from drop-cancellation — selfName/op.name='col', "
                     "elidable=TRUE — so the elidable binder and selfName are moved "
                     "off every other witness's value. If it verified => "
                     "SPEC-TOO-WEAK (payload unpinned).",
        "witness": (
            "-- Refuted at a matching removal — fully concrete, no opaque term.\n"
            "-- The spec pins `.replace []`; the rival returns `.replace [op]`.\n"
            "example :\n"
            "    ¬ problem_spec_reduceAddIndex \"col\" "
            "{ isRemoveIndex := true, name := \"col\", elidable := true } \"lbl\"\n"
            "      (implementation_reduceAddIndex \"col\" "
            "{ isRemoveIndex := true, name := \"col\", elidable := true } \"lbl\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and, beq_self_eq_true, if_true]\n"
            "  decide\n"
        ),
    },
    {
        "id": "fallback-wrong-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FALLBACK_ARG,
        "refinement": "selects the fallback branch correctly but delegates to the "
                      "shared reducer with a CONSTANT application label ('') rather "
                      "than the actual one threaded in. A faithful real patch that "
                      "dropped the real `app_label` argument in the `super()` "
                      "delegation would ask the generic reducer about the wrong "
                      "application context, yielding a different reduction wherever "
                      "the shared reducer's decision depends on the label, so it "
                      "would NOT resolve. Ports nagini's faithful-delegation / "
                      "frame concern onto the referentially-transparent carrier "
                      "(where 'don't disturb the inputs' becomes 'thread them "
                      "unchanged into the callee').",
        "rationale": "partial-domain on the fallback DELEGATION. Branch selection "
                     "is correct; the delegated argument is wrong. Rejection "
                     "source: the fallback clause pins `result = baseReduce "
                     "selfName op appLabel`, but the rival computes `baseReduce "
                     "selfName op \"\"`. Refuted by conditioning on the label "
                     "binder: two DISTINCT opaque terms (jointly satisfiable). "
                     "Binder spread: this is the ONLY rival that moves the appLabel "
                     "binder off its held value, demonstrating the spec's "
                     "dependence on it; isRemoveIndex=false, elidable=true. If it "
                     "verified => SPEC-TOO-WEAK (delegation argument unpinned).",
        "witness": (
            "-- Refuted on the fallback path: the spec delegates with appLabel;\n"
            "-- the rival delegates with the constant \"\". These are two DISTINCT\n"
            "-- opaque terms; assume only that they differ (jointly satisfiable —\n"
            "-- one hypothesis, two distinct terms, not two claims about one term).\n"
            "example (h : baseReduce \"idx\" "
            "{ isRemoveIndex := false, name := \"z\", elidable := true } \"\"\n"
            "           ≠ baseReduce \"idx\" "
            "{ isRemoveIndex := false, name := \"z\", elidable := true } \"app\") :\n"
            "    ¬ problem_spec_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := false, name := \"z\", elidable := true } \"app\"\n"
            "      (implementation_reduceAddIndex \"idx\" "
            "{ isRemoveIndex := false, name := \"z\", elidable := true } \"app\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.false_and, if_false]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "fallback-not-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FALLBACK_CONST,
        "refinement": "selects the fallback branch correctly but does not DEFER at "
                      "all: instead of asking the generic shared reducer, it "
                      "hardcodes the 'cannot optimize across' sentinel. A faithful "
                      "real patch that returned that sentinel directly rather than "
                      "consulting the shared reducer would suppress every "
                      "optimization the generic rule authorizes — an elidable "
                      "operation pair that the shared reducer would collapse is "
                      "instead reported as non-optimizable, so plans that must "
                      "shrink stop shrinking. It also silently overrides an "
                      "UNCHANGED shared behaviour the modeled decision is only "
                      "supposed to fall back to, so it would NOT resolve.",
        "rationale": "partial-domain on the fallback DELEGATION ITSELF (distinct "
                     "from fallback-wrong-arg, which delegates faithfully-shaped "
                     "but with a wrong argument; this one does not delegate). "
                     "Rejection source: the fallback clause pins `result = "
                     "baseReduce selfName op appLabel`, but the rival returns "
                     "`.cannot` — a concrete sentinel that equals the shared "
                     "reducer's answer only by coincidence. Binder spread: "
                     "isRemoveIndex=true with names DIFFERING ('nm' vs 'zz') and "
                     "appLabel='lb' — a fourth, distinct refutation point. If it "
                     "verified => SPEC-TOO-WEAK (the fallback OUTCOME is unpinned: "
                     "an impl could ignore the shared reducer entirely). ADDED BY "
                     "AUDIT: restores nagini's base-rule lane (swap-base-tags), "
                     "which the port had recorded as collapsed by this carrier.",
        "witness": (
            "-- Refuted on the fallback path at a differently-named removal: the\n"
            "-- spec pins the SHARED REDUCER's outcome there, the rival hardcodes\n"
            "-- `.cannot`. The shared reducer is opaque, so condition on the single\n"
            "-- opaque term at this input — whenever its answer is anything other\n"
            "-- than that sentinel, the rival's answer differs from the spec's.\n"
            "example (h : baseReduce \"nm\" "
            "{ isRemoveIndex := true, name := \"zz\", elidable := false } \"lb\" "
            "≠ ReduceResult.cannot) :\n"
            "    ¬ problem_spec_reduceAddIndex \"nm\" "
            "{ isRemoveIndex := true, name := \"zz\", elidable := false } \"lb\"\n"
            "      (implementation_reduceAddIndex \"nm\" "
            "{ isRemoveIndex := true, name := \"zz\", elidable := false } \"lb\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and, if_false]\n"
            "  intro heq\n"
            "  exact h heq.symm\n"
        ),
    },
    {
        "id": "cancel-wrong-outcome-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CANCEL_SENTINEL,
        "refinement": "selects the cancellation branch correctly but answers with "
                      "the 'cannot optimize across' sentinel instead of the empty "
                      "replacement list. A faithful real patch of this shape would "
                      "report the matching add/remove pair as NON-OPTIMIZABLE — the "
                      "optimizer would leave BOTH operations standing rather than "
                      "collapsing them, and would additionally stop considering that "
                      "pair for any further reduction. So the very scenario the issue "
                      "asks for (an add-index followed by a same-name remove-index "
                      "collapsing to no operations) still does not collapse, and the "
                      "optimizer test asserting the pair reduces to NO operations "
                      "FAILS; it would NOT resolve. Note this is a DIFFERENT failure "
                      "from cancel-wrong-payload: that one still replaces the pair "
                      "(with the wrong operations), while this one declines to "
                      "replace it at all.",
        "rationale": "partial-domain on the annihilation OUTCOME KIND, the one "
                     "distinction no other case demonstrates. Branch selection is "
                     "correct; the outcome's CONSTRUCTOR is wrong. Rejection source: "
                     "the cancellation clause pins the result to `.replace []`, but "
                     "the rival returns `.cannot`. Distinct from "
                     "`cancel-wrong-payload`, which varies the replacement list's "
                     "CONTENTS and so stays inside the `.replace` constructor, and "
                     "from `fallback-not-deferred`, which returns `.cannot` on the "
                     "FALLBACK branch (a different clause, where the spec pins the "
                     "shared reducer rather than the empty list). Fully concrete (no "
                     "opaque term), decidable. Binder spread: a fifth distinct "
                     "refutation point — selfName/op.name='ix', appLabel='al'. If it "
                     "verified => SPEC-TOO-WEAK (the annihilation outcome's "
                     "constructor is unpinned, so an impl could decline to "
                     "annihilate while still passing).",
        "witness": (
            "-- Refuted at a matching removal — fully concrete, no opaque term.\n"
            "-- The spec pins `.replace []` (the pair annihilates); the rival\n"
            "-- answers `.cannot` (the pair is not optimizable). Distinct outcome\n"
            "-- CONSTRUCTORS of a type with DecidableEq, so `decide` settles it.\n"
            "example :\n"
            "    ¬ problem_spec_reduceAddIndex \"ix\" "
            "{ isRemoveIndex := true, name := \"ix\", elidable := false } \"al\"\n"
            "      (implementation_reduceAddIndex \"ix\" "
            "{ isRemoveIndex := true, name := \"ix\", elidable := false } \"al\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and, beq_self_eq_true, if_true]\n"
            "  decide\n"
        ),
    },
    {
        "id": "fallback-wrong-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FALLBACK_OPERAND,
        "refinement": "selects the fallback branch correctly and threads the "
                      "application label faithfully, but hands the shared reducer "
                      "a MANGLED counterpart operation — one observed attribute of "
                      "it flipped — instead of the operation the optimizer "
                      "actually asked about. A faithful real patch of this shape "
                      "would consult the generic reducer about an operation that "
                      "is not the one standing next in the plan, so wherever the "
                      "shared rule's decision turns on that attribute the pair is "
                      "reduced under the wrong premise: pairs that must collapse "
                      "are reported non-optimizable and pairs that must be left "
                      "alone are collapsed. The optimizer's cross-operation "
                      "invariants break either way, so it would NOT resolve.",
        "rationale": "partial-domain on the fallback DELEGATION's OPERAND. This is "
                     "the mirror of `fallback-wrong-arg`: that rival moves the "
                     "LABEL argument and threads the operation verbatim, this one "
                     "threads the label verbatim and mangles the OPERATION. "
                     "Rejection source: the fallback clause pins `result = "
                     "baseReduce selfName op appLabel` — the SAME op — but the "
                     "rival computes `baseReduce selfName {op with elidable := "
                     "!op.elidable} appLabel`. ADDED BY AUDIT: the DEFENDED "
                     "SURFACE note claims faithful delegation is load-bearing in "
                     "'same op, same label', and the label half was demonstrated "
                     "while the op half was asserted only in prose — no case moved "
                     "the operand argument. Refuted by conditioning on two "
                     "DISTINCT opaque terms (jointly satisfiable; probe exit 1). "
                     "Binder spread: a sixth distinct refutation point — "
                     "selfName='kx' vs op.name='qz' (unequal) with "
                     "isRemoveIndex=TRUE and elidable=TRUE, a facet combination no "
                     "other rival occupies, appLabel='ap'. If it verified => "
                     "SPEC-TOO-WEAK (the delegated operand is unpinned, so an impl "
                     "could ask the shared reducer about a different operation).",
        "witness": (
            "-- Refuted on the fallback path: the spec delegates with the operation\n"
            "-- as given; the rival delegates with one of its observed attributes\n"
            "-- flipped. These are two DISTINCT opaque terms; assume only that they\n"
            "-- differ (one hypothesis, two distinct terms — jointly satisfiable,\n"
            "-- not two claims about one term).\n"
            "example (h : baseReduce \"kx\" "
            "{ isRemoveIndex := true, name := \"qz\", elidable := false } \"ap\"\n"
            "           ≠ baseReduce \"kx\" "
            "{ isRemoveIndex := true, name := \"qz\", elidable := true } \"ap\") :\n"
            "    ¬ problem_spec_reduceAddIndex \"kx\" "
            "{ isRemoveIndex := true, name := \"qz\", elidable := true } \"ap\"\n"
            "      (implementation_reduceAddIndex \"kx\" "
            "{ isRemoveIndex := true, name := \"qz\", elidable := true } \"ap\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.true_and]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "fallback-wrong-selfname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FALLBACK_SELFNAME,
        "refinement": "selects the fallback branch correctly and threads both the "
                      "counterpart operation and the application label faithfully, "
                      "but tells the shared reducer the WRONG added-index name: it "
                      "passes the counterpart's target name in the position where "
                      "the added index's own name belongs. A faithful real patch of "
                      "this shape would ask the generic reducer about an add-index "
                      "operation other than the one the optimizer is actually "
                      "holding, so wherever the shared rule's decision turns on "
                      "which operation is asking, the pair is reduced under the "
                      "wrong premise and the optimizer's cross-operation invariants "
                      "break. Note it agrees with the correct behaviour exactly "
                      "where the two names coincide — which is the sub-domain the "
                      "cancellation guard already answers — so the error is "
                      "invisible to every cancellation-side test and shows up only "
                      "on the deferral path; it would NOT resolve.",
        "rationale": "partial-domain on the fallback DELEGATION's SELF-NAME, the "
                     "third of the three delegated arguments and the one no case "
                     "moved. Rejection source: the fallback clause pins `result = "
                     "baseReduce selfName op appLabel` — the added index's OWN name "
                     "in the first position — but the rival computes `baseReduce "
                     "op.name op appLabel`. ADDED BY AUDIT: the DEFENDED SURFACE "
                     "note pins the delegation in three quantities and only two "
                     "carried a rival (`fallback-wrong-arg` the label, "
                     "`fallback-wrong-operand` the counterpart operation), so the "
                     "self-side conjunct was prose only. Distinct from "
                     "`fallback-wrong-operand`: that rival mangles the COUNTERPART "
                     "argument and threads this one verbatim; this one is its "
                     "mirror. Refuted by conditioning on two DISTINCT opaque terms "
                     "(jointly satisfiable; probe exit 1). Binder spread: a seventh "
                     "distinct refutation point — selfName='ax' vs op.name='bx' "
                     "(unequal) with isRemoveIndex=FALSE and elidable=false, "
                     "appLabel='cx'; it is the only rival whose two mis-delegated "
                     "terms differ in the FIRST argument rather than in a later "
                     "one. If it verified => SPEC-TOO-WEAK (the delegated "
                     "self-name is unpinned, so an impl could ask the shared "
                     "reducer on behalf of a different operation).",
        "witness": (
            "-- Refuted on the fallback path: the spec delegates with the added\n"
            "-- index's own name; the rival delegates with the counterpart's target\n"
            "-- name. These are two DISTINCT opaque terms (they differ in the FIRST\n"
            "-- argument); assume only that they differ — one hypothesis, two\n"
            "-- distinct terms, jointly satisfiable, not two claims about one term.\n"
            "example (h : baseReduce \"bx\" "
            "{ isRemoveIndex := false, name := \"bx\", elidable := false } \"cx\"\n"
            "           ≠ baseReduce \"ax\" "
            "{ isRemoveIndex := false, name := \"bx\", elidable := false } \"cx\") :\n"
            "    ¬ problem_spec_reduceAddIndex \"ax\" "
            "{ isRemoveIndex := false, name := \"bx\", elidable := false } \"cx\"\n"
            "      (implementation_reduceAddIndex \"ax\" "
            "{ isRemoveIndex := false, name := \"bx\", elidable := false } \"cx\") := by\n"
            "  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex\n"
            "  simp only [Id.run, pure, Bool.false_and, if_false]\n"
            "  exact h\n"
        ),
    },
]

# ===========================================================================
# AXIOM LANE — empty (no consumed `axiom`; one `opaque` A-reference callee).
# ===========================================================================
# The only callee (the generic shared reducer) is referenced opaquely and
# validated == the real `Operation.reduce` by G-AX; the proof consumes NO
# property of it (case split + reflexivity against the opaque term). There is no
# axiom-soundness or axiom-containment obligation. The nagini AXIOM_TESTS were
# also empty; dropped.
AXIOM_TESTS = []
