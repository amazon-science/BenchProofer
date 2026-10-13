"""properties.py — G-PBT falsification battery for django__django-13344 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region — which the consumer spec view elides — is changed, so
``markers.same_spec`` holds and the ``prove_correct initMiddleware`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation, checked by the real verifier. One positive additionally reproves
(``pos-control-case-split``): the obligation STATEMENT is what must be
byte-identical, while the tactic body is the variant's own — a soundness positive
that kept a script tuned to the frozen impl's shape would score a tactic gap as
SPEC-TOO-STRONG. ``expect="verify"`` passes iff
(in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, one read-only input binder):

  initMiddleware (handlerIsAsync : Bool) return (out : Middleware)
    ensures out = construct handlerIsAsync            [clause A, whole result]
    ensures out.asyncCapable = handlerIsAsync         [clause A', the field]

  ``construct`` is a TRANSPARENT total function of the single input:
  ``construct b = { asyncCapable := b }``. The built middleware's
  async-capability observable is EXACTLY the async-classification of the handler
  it wraps. Both ensures clauses restate the one load-bearing fact — the result's
  ``asyncCapable`` field equals ``handlerIsAsync`` — the first pinning the whole
  record, the second projecting the field. The post-image is grounded entirely
  in the input (``construct`` is a plain ``def`` over ``Bool``; ``Middleware``
  derives ``DecidableEq``; the ``axioms`` region is empty), so a wrong impl
  cannot verify by echoing an opaque answer-key — it must reproduce the
  classification.

  THE BEHAVIOURAL DISCRIMINATOR: a middleware built around an asynchronous
  handler must advertise asynchronous operation, and one built around a
  synchronous handler must not. The pre-change constructors for the affected
  middleware types built the instance WITHOUT the async-capability registration
  step, so a middleware wrapping an asynchronous handler still reported itself
  synchronous. The failing test keys on exactly this observable (an asynchronous
  handler must yield a middleware that advertises async). Clause A senses it:
  ``out.asyncCapable = handlerIsAsync`` at every input.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a RICHER pair of functions and pins SIX facts: (P) the handler is
retained, (S) a deprecation signal fires exactly when the handler is absent,
(A) the async-capability advertisement equals the handler's async-ness, and
(N)/(R)/(Q) a store-selection/store-resolution invariant on a second function.
This bundle models ONLY the purely functional core the fix actually turns on —
fact (A): WHAT the constructed middleware advertises about its async-ness — as a
one-argument transparent classifier. The gold patch's behavioural delta is
exactly the restoration of the async-capability registration step (the F2P
``test_coroutine`` keys on it), and that is the entire modeled surface here.

Consequently the nagini rivals attached to the OTHER five facts have NO
counterpart on this carrier: there is no producer-retention field to drop (P),
no deprecation-signal flag to mis-fire (S), and no store-name/store/return-value
triple to abuse (N/R/Q). Those are downstream constructor behaviour the fix's
async-delta does not touch and this bundle does not model (mapping.md §2 folds
the deprecation path OUT of the modeled frame; the store fields are orthogonal).
Carrier narrowing, not a coverage gap in what IS modeled — the footer accounts
for every nagini case.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS here, and the nagini sibling ITSELF records the
    class as inapplicable (its read-only note: every handler field is held at
    FULL permission and the value params are immutable, so the Acc(.,1/2)
    frame-mutation class does not apply). Lean/Velvet are referentially
    transparent: ``handlerIsAsync`` is an immutable value (not a ``mut`` binder),
    there is no heap, no aliasing and no permission system. No read-only field to
    overwrite and no substitute probe to build.
  * ADMISSIBILITY — the method carries NO ``require`` clause (precondition ≡
    True), so the nagini admiss-self-call's "a normal F2P-shaped input satisfies
    the precondition" probe is vacuous. Re-aimed at the residual admissibility
    risk on a total domain: that the two-clause post-image is jointly SATISFIABLE
    by a gold-shaped computation (else SPEC-UNSATISFIABLE) — witnessed by the
    frozen impl discharging both ensures.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent total function
    of the input (``construct``), not an axiomatized oracle; the ``axioms``
    region is empty. The cheapest correct impl is carried as a positive control.

CARRIER NOTE — why this port refutes at CONCRETE literals (no conditioning).
The carrier is fully transparent: ``Bool`` for the input, ``Middleware`` a
single-``Bool``-field structure deriving ``DecidableEq``. So every reject witness
reaches the method's contract through Velvet's own tester machinery
(``initMiddlewareTester handlerIsAsync``) at a concrete literal and closes by
``decide`` — no hypothesis about an opaque term is needed, so no witness binds
anything and the gate's consistency probe has nothing to check. The frozen
solution is STRAIGHT-LINE and also reduces under ``decide``; the witness fails
against gold purely because gold SATISFIES the spec at that input (the tester
returns ``true``, so ``... = false`` is provably false), which is the required
discriminator. Checked in a file whose ``prove_correct`` block is stripped, so
no tactic script can mask the verdict. Every reject witness below was run against
both the rival (elaborates) and the frozen solution (fails) with two real builds.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries a combined
axiom-soundness/containment probe over the real ``asyncio.iscoroutinefunction``
classifier and the registry read; that is G-AX's job (axiom_check.py /
mapping.md §3) and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13344"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole frozen impl body (text strictly between
# ---- -- impl-start and -- impl-end, comments included). Lies wholly inside the
# ---- single impl region and is unique in Solution.lean (both facts asserted at
# ---- load by _swap), so every variant's edit is confined to the elided impl
# ---- region and same_spec holds by construction.
_GOLD_IMPL = (
    "    -- Build the middleware through the canonical construction routine, which\n"
    "    -- records the handler's async-capability on the result.\n"
    "    let out := construct handlerIsAsync\n"
    "    return out"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the frozen proof, verbatim. It is NOT generic over the impl shape, and the
# ---- audit measured exactly where it stops: `loom_solve; all_goals simp
# ---- [construct]` closes for any impl whose returned record is DEFINITIONALLY
# ---- `{ asyncCapable := handlerIsAsync }` (both defeq positives below), but a
# ---- reshape that CASE-SPLITS on the input leaves two residual goals
# ---- (`handlerIsAsync = true` under `if_pos : handlerIsAsync = true`, and the
# ---- `false` mirror) that `simp [construct]` cannot discharge because the branch
# ---- hypothesis is not in the simp set. Replacing `simp` with `simp_all` closes
# ---- both. A variant may reprove freely (variant_scope constrains the obligation
# ---- STATEMENT, not the tactic body), so the case-splitting positive below ships
# ---- that one-token adaptation — a soundness positive must isolate SPEC strength
# ---- from tactic brittleness, and keeping a proof that cannot close the reshape
# ---- would report SPEC-TOO-STRONG for a tactic gap. The reject rivals keep the
# ---- frozen proof (their rejection is carried by the witness, not by whether the
# ---- frozen tactic happens to break on the reshape).
_PROOF = (
    "prove_correct initMiddleware by\n"
    "  loom_solve\n"
    "  all_goals simp [construct]"
)

# The hypothesis-aware variant: identical except `simp_all`, which additionally
# consumes the branch hypothesis a case-splitting impl introduces.
_PROOF_SIMP_ALL = (
    "prove_correct initMiddleware by\n"
    "  loom_solve\n"
    "  all_goals simp_all [construct]"
)

assert _BASE.count(_PROOF) == 1, "frozen proof region drifted; update _PROOF"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (spec view and
    frozen proof untouched)."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body):
    """As `_impl`, but also swaps the tactic body for the hypothesis-aware one.

    The spec view is untouched (`prove_correct` bodies are elided from it and the
    header survives), so `same_spec` and the obligation-preserved check both hold;
    only the proof SCRIPT differs, which is exactly what a variant may reprove.
    """
    return _swap(_impl(body), _PROOF, _PROOF_SIMP_ALL)


# ---- witness builder. Reaches the method contract through Velvet's tester
# ---- machinery: `initMiddlewareTester b = false` says the extracted program's
# ---- result violates the postcondition at the concrete input b. Checked in a
# ---- file whose `prove_correct` block is stripped; closes by `decide` on the
# ---- transparent carrier. Binds nothing (literal input), so the gate's
# ---- consistency probe is a no-op.
def _witness(call):
    return (
        "extract_program_for initMiddleware\n"
        "prove_precondition_decidable_for initMiddleware\n"
        "prove_postcondition_decidable_for initMiddleware\n"
        "derive_tester_for initMiddleware\n\n"
        f"example : {call} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG. Every one keeps the
    # byte-identical obligation STATEMENT; the first two also keep the frozen
    # tactic body, the third reproves with a one-token adaptation (see `_PROOF`
    # / `_PROOF_SIMP_ALL`) because the frozen script was MEASURED not to close a
    # case-splitting impl. The first two are DEFINITIONALLY the frozen term
    # (`{ asyncCapable := handlerIsAsync }`), so on their own they only show the
    # spec is insensitive to SPELLING; pos-control-case-split is the one that
    # shows it is insensitive to control SHAPE. All three verified out-of-band
    # with real builds.
    # =====================================================================
    {
        "id": "pos-control-direct-record",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the result record DIRECTLY, recording the input on the
        # observable field, rather than going through the canonical classifier
        # `construct`. The value is definitionally `construct handlerIsAsync`
        # (both are `{ asyncCapable := handlerIsAsync }`), so both ensures still
        # discharge and the frozen proof closes unchanged. Since the post-image is
        # GROUNDED in the input (not an opaque answer-key), this is the honest
        # cheapest CORRECT impl — it doubles as proof the spec is not
        # echo-vulnerable (any impl recording the wrong bit fails
        # `out.asyncCapable = handlerIsAsync`).
        "module": _impl(
            "    return { asyncCapable := handlerIsAsync }"),
        "rationale": (
            "structurally different CORRECT reshape: build the result record "
            "directly with the input on the observable field, bypassing the "
            "classifier. Definitionally equal to `construct handlerIsAsync`, so "
            "both ensures discharge and the frozen `prove_correct` body closes "
            "unchanged. The post-image is grounded in the input, so this cheapest "
            "correct impl shows the spec is not echo-vulnerable. Must verify, else "
            "SPEC-TOO-STRONG. Ports the nagini pos-control-reorder + "
            "pos-cheapest-grounded (the grounded cheapest-correct control)."
        ),
    },
    {
        "id": "pos-control-local-stage",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the classification through a typed local before the
        # canonical construction. Same value flow, different control shape; the
        # frozen proof closes unchanged.
        "module": _impl(
            "    let b : Bool := handlerIsAsync\n"
            "    let out := construct b\n"
            "    return out"),
        "rationale": (
            "second correct shape: stage the async-classification through a typed "
            "local before the canonical construction. The value flow is unchanged "
            "(`b = handlerIsAsync`), so both ensures discharge and the frozen proof "
            "closes as-is. Proves the spec is not over-fitted to the inline "
            "construction spelling. Must verify, else SPEC-TOO-STRONG. Ports the "
            "nagini pos-control-reorder's local-staging half."
        ),
    },

    {
        "id": "pos-control-case-split",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: DECIDE on the handler's classification and build the matching
        # result in each branch, instead of threading the classification through
        # as a value. This is the first positive whose result is NOT
        # definitionally `construct handlerIsAsync` — the returned term is an
        # `if`/branch scrutinizing the input, so the two ensures become two
        # per-branch goals discharged from the branch hypothesis rather than by
        # reduction. That is what makes it a real SPEC-TOO-STRONG probe: the two
        # defeq positives above cannot distinguish "the spec accepts every
        # faithful shape" from "the spec accepts every spelling of gold's term".
        # Reproved with the hypothesis-aware tactic (see `_PROOF_SIMP_ALL`);
        # measured: the frozen `simp [construct]` leaves both branch goals open.
        "module": _impl_reproved(
            "    if handlerIsAsync then\n"
            "      return construct true\n"
            "    else\n"
            "      return construct false"),
        "rationale": (
            "third correct shape, and the only positive that is NOT "
            "definitionally the frozen term: branch on the handler's "
            "classification and build the matching result in each arm. The two "
            "ensures are discharged per-branch from the branch hypothesis "
            "(`handlerIsAsync = true` / `¬ handlerIsAsync = true`) instead of by "
            "reduction, so this probes whether the spec admits a faithful "
            "CONTROL shape rather than a re-spelling of the frozen value. Must "
            "verify, else SPEC-TOO-STRONG. Reproves with `simp_all [construct]` "
            "in place of `simp [construct]` — the obligation statement is "
            "byte-identical and only the tactic body differs, which is what a "
            "variant may legitimately do; the frozen script was MEASURED to "
            "leave both branch goals open, a tactic gap that must not be scored "
            "as spec strength. Ports the nagini pos-control-reorder's "
            "reordered-branch half, which the two defeq positives do not reach."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-self-call. That case
    # established that the precondition admits a normal F2P-shaped input. This
    # method carries NO `require` clause (precondition ≡ True), so nothing could
    # exclude a normal input and the classic probe is vacuous. Re-aimed at the
    # residual total-domain risk: that the two-clause post-image is jointly
    # SATISFIABLE by a gold-shaped computation. The frozen impl discharging both
    # ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the classifier is total over both "
            "handler classifications; the gold impl discharging both ensures is the "
            "admissibility witness that the post-image (clause A plus its field "
            "projection A') is jointly satisfiable. Near-trivial precisely because "
            "the precondition is empty. Re-aimed from the nagini admiss-self-call, "
            "whose precondition-admits-a-normal-input half has no counterpart on "
            "this referentially-transparent carrier with no require clause. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the sole
    # input binder handlerIsAsync ∈ {true, false} across the two distinct points
    # (pts=2); no point is pinned across the battery.
    # =====================================================================
    {
        "id": "weak-async-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: skip the async-capability registration, so the
        # built middleware NEVER advertises asynchronous operation regardless of
        # the handler it wraps. Correct on a synchronous handler; WRONG on an
        # asynchronous one.
        "module": _impl(
            "    let out := construct false\n"
            "    return out"),
        "refinement": (
            "this is the pre-change omission of the async-capability registration "
            "step: the async marker is never recorded, so the constructed "
            "middleware reports itself synchronous even when it wraps an "
            "asynchronous handler. The failing test asserts a middleware built "
            "around an asynchronous handler advertises asynchronous operation, "
            "which a middleware that never records the marker does not — so the "
            "faithful real patch FAILS the F2P and does NOT resolve. This is the "
            "exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from clause A (`out.asyncCapable = handlerIsAsync`): the impl "
            "hardcodes the synchronous classification, so for an asynchronous "
            "handler it advertises `false` while the spec forces `true`. Refuted "
            "at handlerIsAsync = true. If it verified => SPEC-TOO-WEAK (admits the "
            "bug — the async regression would go unnoticed)."
        ),
        "witness": _witness("initMiddlewareTester true"),
    },
    {
        "id": "weak-async-forced",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror miss: record the async marker UNCONDITIONALLY, so the built
        # middleware always advertises asynchronous operation regardless of the
        # handler. Correct on an asynchronous handler; WRONG on a synchronous one.
        "module": _impl(
            "    let out := construct true\n"
            "    return out"),
        "refinement": (
            "a faithful counterpart that recorded the async-capability marker "
            "unconditionally would make a middleware built around a SYNCHRONOUS "
            "handler advertise asynchronous operation; an asynchronous caller would "
            "then hand it awaitable values of the unintended kind. The failing test "
            "asserts a middleware built around a synchronous handler reports itself "
            "non-asynchronous, which the unconditional marker does not produce, so "
            "the faithful real patch FAILS the F2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause A (`out.asyncCapable = handlerIsAsync`): the impl "
            "hardcodes the asynchronous classification, so for a synchronous "
            "handler it advertises `true` while the spec forces `false`. Refuted "
            "at handlerIsAsync = false — a DISTINCT point from weak-async-dropped, "
            "so the sole binder is varied across both its values and no rival is "
            "refuted at the same input. If it verified => SPEC-TOO-WEAK (the "
            "async-advertisement would be pinned in only one direction)."
        ),
        "witness": _witness("initMiddlewareTester false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 1-entry AXIOM lane,
# over TWO modeled functions pinning SIX facts: (P) handler retained, (S)
# deprecation signal == (producer is None), (A) async-advertisement ==
# async-ness of the handler, and (N)/(R)/(Q) a store-name / store-resolution /
# return-value invariant on a second store-selecting function. THIS bundle models
# only the purely-functional core the fix's behavioural delta turns on — fact (A)
# — as a single one-argument transparent classifier `initMiddleware (Bool) ->
# Middleware` whose post-image is `asyncCapable = handlerIsAsync`. The other five
# facts (P, S, N, R, Q) are downstream constructor / store-selection behaviour the
# async-delta does not touch and this bundle does not model (mapping.md §2 folds
# the deprecation path out of frame and carries only the touched `asyncCapable`
# field). Every nagini case is accounted for below.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder         -> pos-control-case-split + pos-control-local-stage  RE-SHAPED
#   pos-cheapest-grounded       -> pos-control-direct-record  RE-EXPRESSED (merged)
#   admiss-self-call            -> admiss-gold-total          RE-AIMED
#   weak-async-dropped          -> weak-async-dropped         PORTED (central, THE bug-delta)
#   weak-signal-always          -> (none)                     NO COUNTERPART (fact S unmodeled)
#   weak-producer-not-retained  -> (none)                     NO COUNTERPART (fact P unmodeled)
#   weak-override-ignored       -> (none)                     NO COUNTERPART (fact N unmodeled)
#   weak-store-stale            -> (none)                     NO COUNTERPART (fact R unmodeled)
#   weak-result-stale           -> (none)                     NO COUNTERPART (fact Q unmodeled)
#   (new, no sibling)           -> weak-async-forced          ADDED (mirror, binder coverage)
#   AXIOM_TESTS (1 entry)       -> (none)                     DROPPED (G-AX lane)
#
# 6 velvet SPEC cases: 3 soundness, 1 admissibility, 2 uniqueness.
#
# PORTED (weak-async-dropped): THE central rival and the exact pre-change
#   behaviour — skip the async-capability registration, so the middleware never
#   advertises async. Carries its nagini refinement argument (the F2P test_coroutine
#   asserts an async handler yields an async-advertising middleware; the omission
#   fails it). Attacks clause A on the async sub-domain (handlerIsAsync=true).
# ADDED (weak-async-forced): the mirror rival — record the async marker
#   unconditionally, so a synchronous handler wrongly advertises async. Attacks
#   clause A on the synchronous sub-domain (handlerIsAsync=false), the distinct
#   binder value the dropped rival does not reach. A real divergence with a
#   machine-checked witness (a middleware around a sync handler must report itself
#   non-async), not fabricated wrongness — it exists to VARY the sole input binder
#   so the battery is not silent on the false-classification direction.
# RE-SHAPED / RE-EXPRESSED / MERGED (pos-control-reorder + pos-cheapest-grounded
#   -> pos-control-case-split + pos-control-local-stage + pos-control-direct-record):
#   the nagini file
#   carries two positives. pos-control-reorder reorders the signal/producer/async
#   assignments and stages the async flag via a local; on this carrier the only
#   modeled assignment is the async classification (the signal/producer facts are
#   unmodeled), so there is nothing to reorder in the ASSIGNMENT order — but the
#   reordered-branch half does carry over, as the case-splitting positive
#   (pos-control-case-split), and the local-staging half as
#   pos-control-local-stage. Keeping ONLY the two definitionally-equal positives
#   was the audit's finding: `{ asyncCapable := handlerIsAsync }` and
#   `let b := handlerIsAsync; construct b` both reduce to the frozen term, so
#   together they probe SPELLING insensitivity and never test whether the spec
#   admits a different control shape. pos-control-case-split closes that: its
#   result is an `if` on the input, discharged per-branch, and it verifies
#   (measured). pos-cheapest-grounded is the
#   cheapest correct impl assigning each field its grounded oracle value; on this
#   carrier the grounded value IS `construct handlerIsAsync`, so the cheapest
#   correct impl is the direct record build (pos-control-direct-record), which
#   also serves as the honest grounded control (no wrong echo, since the post-image
#   is grounded in the input).
# RE-AIMED (admiss-self-call -> admiss-gold-total): the nagini case established
#   that the precondition admits a normal F2P-shaped input (a fresh handler + a
#   supplied producer). This method has no `require` clause and no heap, so that
#   probe is vacuous; re-aimed at the residual total-domain risk (post-image joint
#   satisfiability), witnessed by the frozen impl discharging both ensures.
# NO COUNTERPART (5): weak-signal-always (fact S — the deprecation-signal flag),
#   weak-producer-not-retained (fact P — the retained handler), weak-override-ignored
#   (fact N — the store-name selection), weak-store-stale (fact R — the store
#   resolution) and weak-result-stale (fact Q — the returned store) each attack a
#   fact NOT modeled on this carrier. mapping.md §2 folds the deprecation path out
#   of the modeled frame and carries only the touched `asyncCapable` field of the
#   constructed middleware; there is no deprecation flag, no retained-handler field,
#   and no store-name/store/return triple here to violate. Omitted because the
#   modeled surface does not include those behaviours (carrier narrowing), NOT
#   because they were hard to prove.
# FRAME-MUTATION: VACUOUS, and the nagini sibling itself records the class as
#   inapplicable (its read-only note: every handler field is held at full
#   permission and the value params are immutable, so Acc(.,1/2) frame-mutation
#   does not apply). Referentially-transparent backend, no `mut` binder, no heap,
#   no aliasing, no permission system. No read-only input to overwrite; no
#   substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): the nagini bundle's combined axiom-soundness/containment
#   probe over the real async classifier and the registry read belongs to the G-AX
#   lane (axiom_check.py / mapping.md §3); this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE. One input binder (handlerIsAsync : Bool),
#   varied and abused across both its values: true (weak-async-dropped) and false
#   (weak-async-forced). The single load-bearing clause A
#   (`out.asyncCapable = handlerIsAsync`, restated by both ensures) is attacked on
#   BOTH sub-domains — a rival that mishandles only the async handler and a rival
#   that mishandles only the sync handler — so neither classification direction is
#   left unpinned. The clause is defended by the three soundness positives and
#   the admissibility case — and those positives are themselves stratified, which
#   is what makes them evidence rather than decoration: two are definitionally
#   the frozen term (spelling insensitivity) and one CASE-SPLITS on the input, so
#   the spec is shown to accept a faithful control shape and not merely a
#   re-spelling of gold's value. The two reject witnesses probe two DISTINCT
#   input points (pts=2); no point is pinned across the battery.
#
# CARRIER NOTE. The carrier is fully transparent (`Bool`, `Middleware` a
#   single-Bool-field structure deriving `DecidableEq`), so every witness refutes
#   at a concrete literal via the tester machinery and closes by `decide` — no
#   conditioning on an opaque term, hence no witness binds anything and the
#   consistency probe is a no-op. Each witness was SEEN to discriminate with two
#   real builds: it ELABORATES against the rival and FAILS against the frozen
#   (straight-line, `decide`-reducible) solution, whose tester returns `true`
#   because gold satisfies the spec at that input.
AXIOM_TESTS = []
