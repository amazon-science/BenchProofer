"""properties.py — G-PBT falsification battery for django__django-13516 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct propagateFlush`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable minimal carrier for a
thin output-stream wrapper's flush request:

  propagateFlush (mut sink : OutputSink) return (u : Unit)
    ensures sink.flushable = sinkOld.flushable                       -- (1)
    ensures sinkOld.flushable = true  → sink.flushes = sinkOld.flushes + 1   -- (2)
    ensures sinkOld.flushable = false → sink.flushes = sinkOld.flushes        -- (3)

``OutputSink`` carries only the two aspects a flush request can touch: whether
the underlying stream the wrapper forwards to supports flushing (``flushable``,
a read-only property of the wrapper) and how many flushes have actually been
driven through to it (``flushes``, the outward observable the failing test
asserts on). There is no ``require`` clause, so the admitted domain is total:
the post-image must hold for EVERY starting state.

THREE independent top-level clauses, each load-bearing:
  (1) ``sink.flushable = sinkOld.flushable`` — the flushable property is
      read-only across a flush request; a flush must not rewrite it. This is the
      directive-5 frame clause: ``sink`` is ``mut`` but the ``flushable`` aspect
      is conceptually unchanged, so it is pinned exactly. A body that overwrites
      it fails here.
  (2) ``flushable = true → flushes + 1`` — when the underlying stream supports
      flushing, the request is carried through to it EXACTLY ONCE (the count
      advances by one). This is the discriminating clause the failing test
      observes: pre-change the request was silently dropped and the count stayed
      put. A body that never forwards fails here.
  (3) ``flushable = false → flushes unchanged`` — when the underlying stream has
      no flush, the request is a no-op. A body that forwards unconditionally
      advances the count on this sub-domain and fails here.

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME-MUTATION — APPLIES, and PORTS to a real value attack (not vacuous). On
    the sibling the read-only capability is held at a fractional heap permission
    an impl can illegally overwrite, and the rejection comes from the permission
    system. Lean/Velvet are referentially transparent and have no such
    permission, BUT the flushable property IS a ``mut`` field here and clause (1)
    pins it as unchanged, so a body that rewrites it violates a genuine
    postcondition clause. The sibling's capability-bit frame rival therefore
    re-expresses as ``weak-frame-write-flushable`` — the rejection source is
    postcondition clause (1) rather than a permission system, but the attack (an
    impl that mutates the read-only aspect) is the same.
  * WRITE-THE-WRAPPED-STREAM-REFERENCE — VACUOUS. The sibling also probes a write
    to the OTHER read-only field, the wrapped-stream reference. That reference is
    NOT part of this carrier (mapping.md §2 restricts ``OutputSink`` to the two
    flush-relevant aspects; the wrapped-stream object, its content, styling and
    line ending are invariant under a flush and omitted). There is no term
    denoting it here, so there is no read-only field to overwrite and no
    discriminating witness. Dropped, not fabricated (see footer).
  * ECHO / FABRICATE-THE-COUNT — APPLIES as a value attack. The sibling's echo
    rival tries to discharge the count clause by WRITING the raw invocation count
    without running the drain primitive. On this carrier there is no
    predicate/permission wall to separate "fabricate" from "forward", but the
    attack's actual content — the observable is WRITTEN as an absolute value
    rather than DERIVED from the pre-state — re-expresses directly: a body that
    assigns the literal ``1`` on the flushable arm agrees with the required
    behaviour exactly at the F2P corner (starting count 0) and is wrong at every
    other starting count. Shipped as ``weak-fabricate-absolute-count``, refuted
    at a flushable state whose count is already 3.
  * PARTIAL-DOMAIN — APPLIES: a body right on one sub-domain but diverging on the
    other (never forward — the pre-change no-op; forward unconditionally). Each
    is refuted at a concrete point on the sub-domain where it goes wrong.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``propagateFlushTester sink = false`` says the extracted program's observable
(the mutated ``sink``'s ``flushable``/``flushes``) violates the method's
postcondition at that concrete starting state. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``OutputSink`` derives ``Inhabited`` and its fields are ``Bool``/``Nat``
with decidable equality, so every witness closes by ``decide``. Each witness
binds nothing (literal starting state), so there are no hypotheses to be
inconsistent.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the operation is
modeled directly over the carrier — the only callee the gold body invokes, the
underlying stream's own flush, is precisely the operation whose forwarding is
the change, and its single observable contribution is modeled directly as the
``flushes`` increment guarded by ``flushable``; mapping.md §3.1). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13516"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_GOLD_IMPL = (
    "    if sink.flushable then\n"
    "      sink := { sink with flushes := sink.flushes + 1 }\n"
    "    else\n"
    "      return\n"
    "    return"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# The same gold branch WITHOUT its trailing `return`, for the one case that has to
# append a live statement after the branch: appending past the method's final
# `return` would make the addition dead code, so the obligation it is supposed to
# generate would never be emitted (and the surgery would not elaborate).
_GOLD_IMPL_NO_TAIL = _GOLD_IMPL[: -len("\n    return")]
assert _GOLD_IMPL_NO_TAIL + "\n    return" == _GOLD_IMPL

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec statement or dropping
# ---- the obligation. Unique in the file.
_GOLD_PROOF = "prove_correct propagateFlush by\n  loom_solve"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- method returns `Unit` and mutates `sink`, so the tester takes the single
# ---- (mutable) starting state and reports whether the resulting observable
# ---- satisfies the postcondition. No `deriving instance` is needed: OutputSink's
# ---- fields are `Bool`/`Nat`, whose equalities `decide` settles directly.
def _tester(body):
    return ("extract_program_for propagateFlush\n"
            "prove_precondition_decidable_for propagateFlush\n"
            "prove_postcondition_decidable_for propagateFlush\n"
            "derive_tester_for propagateFlush\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — guard inversion + early return. A
    # structurally different but CORRECT impl that MUST verify, else the
    # post-image is SPEC-TOO-STRONG. On the not-flushable state it returns
    # early (count untouched => clause (3), clause (2) vacuous); on the
    # flushable state it advances the count once (=> clause (2)); the flushable
    # aspect is never written (=> clause (1)). A branch-reorder/early-return
    # reshape whose decision collapses to the same final state, so the frozen
    # tactic script (`loom_solve`) still discharges the byte-identical
    # obligation with no retune (verified out-of-band with two real builds).
    # =====================================================================
    {
        "id": "pos-guard-invert-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if !sink.flushable then\n"
            "      return\n"
            "    sink := { sink with flushes := sink.flushes + 1 }\n"
            "    return"),
        "rationale": "structurally different CORRECT impl (guard inverted + early "
                     "return, then an unconditional single increment) — "
                     "observationally identical to the frozen if/increment: "
                     "not-flushable returns early (count untouched => clause (3)), "
                     "flushable advances the count once (=> clause (2)); no write "
                     "to the flushable aspect so clause (1) holds. Branch reshape "
                     "only; must verify, else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the count advanced by a COMMUTED sum.
    # The sibling's honest-inline positive showed the count clause is
    # dischargeable by performing the increment directly rather than by
    # invoking a callee by name. This carrier has no named callee (the forward
    # is modeled directly as the increment), so the argument re-expresses as:
    # the count clause is not over-fit to one SYNTACTIC form of the increment.
    # `1 + flushes` is a term shape the frozen impl does not contain, and it is
    # NOT definitionally equal to `flushes + 1` (`Nat.add` recurses on its second
    # argument, so `rfl` does not close `1 + n = n + 1` — measured: exit 1; it
    # needs commutativity/`omega`). So this reshape genuinely forces the proof off
    # the frozen syntactic form and `loom_solve` still closes the obligation via
    # arithmetic normalization rather than by matching the gold term.
    # =====================================================================
    {
        "id": "pos-increment-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if sink.flushable then\n"
            "      sink := { sink with flushes := 1 + sink.flushes }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "rationale": "correct reshape: the flushable arm advances the count by the "
                     "COMMUTED sum `1 + flushes` (a term the frozen impl does not "
                     "contain) rather than `flushes + 1`. The two are equal but NOT "
                     "definitionally so on `Nat` (`rfl` fails on `1 + n = n + 1`), so "
                     "this really does move the proof off the frozen term shape; "
                     "clauses (1)/(2)/(3) still hold and the frozen script discharges "
                     "it by arithmetic normalization. Demonstrates the count clause is "
                     "not over-fit to one syntactic form of the increment (else "
                     "SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point.
    #
    # AUDIT REPAIR. The ported form of this case asserted a conjunction over
    # freshly-written record LITERALS
    #   ({ flushable := true, flushes := 0 } : OutputSink).flushable = true ∧
    #   ({ flushable := true, flushes := 0 + 1 } : OutputSink).flushes = 1
    # whose two projections reduce by `rfl` with NO reference to `sink` at all.
    # It therefore discharged independently of the program: measured, the same
    # assert also discharges when the entire body is replaced by the no-op
    # `return` (exit 0), exactly as a pure `true = true ∧ (1:Nat) = 1` does. It
    # passed honestly and tested nothing about the post-image.
    #
    # The repair states the SAME F2P claim about the actual pre/post states:
    # capture the starting state in `sinkPre`, run the gold body verbatim, then
    # assert that IF the run started at the F2P corner (a flushable stream at
    # count 0) THEN the observable post-state is exactly count 1 with the
    # flushable aspect preserved. The assert now mentions both `sinkPre` and the
    # post-`sink`, so it is discharged only by the program's own final state —
    # `loom_solve` closes it with no retune. Falsifiability re-derived with real
    # builds: perturbing the claimed count to 2, or the claimed frame to
    # `flushable = false`, each leaves an `unsolved goals` obligation
    # (`⊢ sinkOld = {flushable := true, flushes := 0} → sinkOld.flushes + 1 = 2 ∧ …`),
    # so this assert can fail. The two-clause conjunction pins clause (2) at the
    # F2P corner and clause (1) simultaneously.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-forward-once",
        "kind": "admissibility",
        "expect": "verify",
        # The gold branch verbatim, minus its trailing `return` (the assert has to
        # sit BEFORE the method's final return, or it is dead code after an early
        # exit and the obligation is never generated), with the pre-state capture
        # prepended and the assert appended.
        "module": _impl(
            "    let sinkPre := sink\n"
            + _GOLD_IMPL_NO_TAIL + "\n"
            "    assert (with_name_prefix `assert\n"
            "      (sinkPre = { flushable := true, flushes := 0 } →\n"
            "       (sink.flushes = 1 ∧ sink.flushable = true)))\n"
            "    return"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the F2P "
                     "corner: a flushable stream starting at count 0, after one "
                     "driven flush, reports a count of exactly 1 and preserves the "
                     "flushable aspect. The assert is stated over the CAPTURED "
                     "starting state `sinkPre` and the resulting `sink`, so it is "
                     "dischargeable only from the program's own final state — a "
                     "claim about literals alone would reduce by `rfl` and prove "
                     "nothing. It must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the gold body and frozen "
                     "proof are kept verbatim so the method's own `ensures` still "
                     "discharges too. Falsifiable: perturbing the claimed count or "
                     "the claimed frame leaves an unsolved goal.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete starting state and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test. Witnesses vary BOTH
    # aspects of `sink`: `flushable` over {true, false} and the starting
    # `flushes` over {0, 2, 5}, so neither is pinned across the battery.
    # =====================================================================
    {
        "id": "weak-noop-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # Never forward: a no-op regardless of the starting state. This IS the
        # pre-change behaviour — a flush request that is silently dropped.
        # Isolates clause (2): clauses (1) and (3) hold, only the forward-once
        # count is missing.
        "module": _impl("    return"),
        "refinement": "a faithful counterpart that never carries the flush request "
                      "through to the underlying stream is exactly the pre-change "
                      "behaviour the issue reports: a long-running command's output "
                      "is buffered and nothing reaches the stream until the very "
                      "end. The failing test drives the public entry point on a "
                      "flushable stream and asserts the underlying flush WAS "
                      "invoked; a no-op leaves it uninvoked, so the test still "
                      "fails. It would NOT resolve (it is the exact bug the fix "
                      "removes).",
        "rationale": "REJECT from clause (2) `flushable = true → flushes + 1`: on a "
                     "flushable starting state the body leaves the count unchanged "
                     "where the post-image demands a single advance. Clauses (1) "
                     "and (3) are kept correct (nothing is written), so the ONLY "
                     "failing clause is the forward-once count. Refuted at a "
                     "flushable state, count 0. If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : propagateFlushTester { flushable := true, flushes := 0 } "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-unconditional-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward UNCONDITIONALLY: advance the count whether or not the stream
        # supports flushing. Correct on the flushable sub-domain, wrong on the
        # not-flushable one. Isolates clause (3): clauses (1) and (2) hold.
        "module": _impl(
            "    sink := { sink with flushes := sink.flushes + 1 }\n"
            "    return"),
        "refinement": "dropping the capability guard and forwarding on every stream "
                      "drives a flush through to a stream that has no flush "
                      "operation — on the non-flushable sub-domain the faithful "
                      "counterpart raises (an attribute error) rather than doing a "
                      "harmless no-op, breaking management-command output on such a "
                      "stream. That is not a faithful resolving patch: the guard "
                      "exists precisely for the non-flushable case, and a body that "
                      "crashes there would not resolve.",
        "rationale": "REJECT from clause (3) `flushable = false → flushes "
                     "unchanged`: on a not-flushable starting state the body still "
                     "advances the count, where the post-image demands it stay put. "
                     "Clauses (1) and (2) are kept correct, so the ONLY failing "
                     "clause is the no-op-on-non-flushable one. Refuted at a "
                     "not-flushable state, count 2. If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : propagateFlushTester { flushable := false, flushes := 2 } "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-frame-write-flushable",
        "kind": "uniqueness",
        "expect": "reject",
        # Rewrite the READ-ONLY flushable aspect. The count is handled correctly
        # on both arms (advanced iff flushable, unchanged otherwise), but on the
        # not-flushable arm the body flips the flushable aspect to true.
        # Isolates clause (1): clauses (2) and (3) hold.
        "module": _impl(
            "    if sink.flushable then\n"
            "      sink := { sink with flushes := sink.flushes + 1 }\n"
            "      return\n"
            "    else\n"
            "      sink := { sink with flushable := true }\n"
            "      return"),
        "refinement": "the flushable property is a fixed characteristic of the "
                      "wrapped stream (whether it exposes a flush operation), read "
                      "but never rewritten by a flush request. No faithful patch "
                      "reassigns it: a flush that mutated whether its own wrapped "
                      "stream is flushable would corrupt every subsequent flush "
                      "decision and diverge from the surrounding command-output "
                      "behaviour. A verifying rival that overwrites it is a "
                      "verify-not-resolve artifact — the frame clause held only "
                      "vacuously.",
        "rationale": "REJECT from clause (1) `sink.flushable = sinkOld.flushable`: "
                     "on a not-flushable starting state the body sets the flushable "
                     "aspect to true, so the post-state disagrees with the "
                     "pre-state. The count clauses (2)/(3) are kept correct "
                     "(advanced iff originally flushable), so the ONLY failing "
                     "clause is the frame. This is the sibling's mandatory "
                     "capability-frame probe re-expressed as a value attack on the "
                     "`mut` frame clause. Refuted at a not-flushable state, count "
                     "5. If it verified => SPEC-TOO-WEAK (the frame protection "
                     "would be hollow).",
        "witness": _tester(
            "example : propagateFlushTester { flushable := false, flushes := 5 } "
            "= false := by\n  decide\n"),
    },

    # =====================================================================
    # AUDIT ADDITION — the sibling's ECHO rival, re-expressed and LANDED. The
    # port recorded it as VACUOUS on the ground that "advancing the count by one
    # IS the modeled work, so there is no wall separating fabricating the count
    # from doing the forward". That reasoning is wrong on this carrier: the echo
    # attack's content is that the observable is WRITTEN as an absolute value
    # rather than DERIVED from the pre-state, and that distinction survives here
    # as a plain value attack. This body sets the count to the literal 1 on the
    # flushable arm instead of advancing the pre-state count. It is right at the
    # F2P corner (starting count 0 => 1, which is exactly what the failing test's
    # boolean observable can see) and WRONG at every other starting count, so it
    # is precisely a rival that fabricates the observable the test checks without
    # tracking the work actually done. Distinct from weak-noop-prepatch (which
    # never writes) and from weak-unconditional-forward (which drops the guard):
    # it keeps the guard and does write, but ignores the incoming count.
    # Refuted at a flushable state with starting count 3 — a fourth distinct
    # probe point, and the first that varies `flushes` on the FLUSHABLE arm
    # (the battery previously pinned that arm to count 0).
    # =====================================================================
    {
        "id": "weak-fabricate-absolute-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if sink.flushable then\n"
            "      sink := { sink with flushes := 1 }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": "a faithful counterpart that reports the underlying stream as "
                      "having been flushed exactly once no matter how many requests "
                      "have already been driven through it is not a resolving patch: "
                      "it agrees with the required behaviour only on a stream that has "
                      "never been flushed. On the second and later requests the "
                      "underlying stream's flush would be recorded as still having "
                      "happened just once, so output driven by a long-running command "
                      "would stop reaching the stream after the first flush — the very "
                      "symptom the issue reports, reintroduced past the first request. "
                      "It would not resolve.",
        "rationale": "REJECT from clause (2) `flushable = true → flushes = flushes + "
                     "1`: on a flushable starting state whose count is already 3 the "
                     "body sets the count to 1, where the post-image demands 4. Clause "
                     "(1) holds (the flushable aspect is untouched) and clause (3) "
                     "holds (the non-flushable arm is a no-op), so the ONLY failing "
                     "clause is the forward-once count — and it fails for a reason the "
                     "other rivals do not reach: the count is FABRICATED as an "
                     "absolute value rather than derived from the pre-state. Note this "
                     "rival is indistinguishable from gold at the F2P corner (count "
                     "0), which is why it must be refuted at a nonzero starting count. "
                     "If it verified => SPEC-TOO-WEAK (the observable could be written "
                     "without accounting for work already done).",
        "witness": _tester(
            "example : propagateFlushTester { flushable := true, flushes := 3 } "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 2 partial-domain rivals)
# plus a 2-case AXIOM lane, contracting one function (`drain_buffer`, the flush
# forward) over a permission-bearing heap object where the invocation count lives
# behind an abstraction predicate. This bundle models the same operation over the
# purely-functional carrier `OutputSink` (the flushable property + the forward
# count) and pins THREE clauses: the frame (flushable unchanged), forward-once on
# the flushable arm, and no-op on the non-flushable arm. Every sibling case is
# accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-early-return                -> pos-guard-invert-early-return   PORTED
#   pos-inline-drain                -> pos-increment-commuted          RE-EXPRESSED
#   admiss-fresh-wrapper            -> admiss-nondegenerate-forward-once RE-AIMED
#   frame-mutate-capability-bit     -> weak-frame-write-flushable      PORTED
#   frame-mutate-out-ref            -> (none)                          VACUOUS
#   weak-echo-fieldwrite            -> weak-fabricate-absolute-count   RE-EXPRESSED
#   weak-drop-guard-unconditional   -> weak-unconditional-forward      PORTED
#   weak-noop-prepatch              -> weak-noop-prepatch              PORTED
#   AXIOM_TESTS (2)                 -> (none)                          DROPPED (G-AX)
#
# PORTED (pos-early-return): the guard-inversion + early-return reshape ports
#   directly; the frozen `loom_solve` closes the collapsed conditional.
# RE-EXPRESSED (pos-inline-drain): the sibling's inline drain showed the count
#   clause is dischargeable by doing the increment work directly, not by calling
#   the drain primitive BY NAME. This carrier models the forward directly as the
#   increment (no named callee), so the "not over-fit to a callee name" argument
#   has no counterpart; it re-expresses as "not over-fit to one SYNTACTIC form of
#   the increment" — the commuted sum `1 + flushes`. Verified to build under the
#   frozen script.
# RE-AIMED (admiss-fresh-wrapper): the sibling constructs a fresh F2P-shaped
#   wrapper and asserts the FULL precondition is establishable on it. There is no
#   `require` clause here (pre-conditions region empty), so the "a normal input
#   satisfies the precondition" reading is vacuous. Re-aimed at proving the
#   post-image is satisfiable AND non-degenerate at the F2P corner (a flushable
#   stream driven once reports count 1 and preserves the flushable aspect), via a
#   live in-region assert against concrete literals.
# PORTED (frame-mutate-capability-bit): the sibling writes the read-only
#   capability bit (held at Acc(.,1/2)) and is rejected by the PERMISSION SYSTEM.
#   This backend has no permission system, BUT the flushable property is a `mut`
#   field pinned unchanged by clause (1) (directive-5 frame discipline), so a body
#   that rewrites it violates a genuine postcondition clause. The attack ports;
#   only the rejection SOURCE changes (postcondition clause (1), not permissions).
# VACUOUS (frame-mutate-out-ref): the sibling's supporting frame rival writes the
#   OTHER read-only field, the wrapped-stream REFERENCE. That reference is not part
#   of this carrier — mapping.md §2 restricts OutputSink to the two flush-relevant
#   aspects, and the wrapped-stream object (content, styling, line ending) is
#   invariant under a flush and omitted. There is no term denoting it, no read-only
#   field to overwrite, and no discriminating witness. Dropped, not fabricated.
#   AUDIT CONFIRMED with a real build: a body attempting to write such a field is
#   not a same-spec rival at all, it fails to elaborate with "`wrapped` is not a
#   field of structure `OutputSink`" — a carrier-vocabulary error, not a spec
#   verdict. Genuinely inexpressible here; the port's disposition is correct.
# RE-EXPRESSED (weak-echo-fieldwrite) — AUDIT CORRECTION. The port recorded this
#   as VACUOUS, reasoning that on a plain `Nat` field "advancing the count by one
#   IS the modeled work", so no wall separates echoing the count from doing the
#   forward. That reasoning does not survive audit. The sibling's echo attack is
#   about the observable being WRITTEN rather than DERIVED from the pre-state, and
#   that distinction is fully expressible here: a body that assigns the ABSOLUTE
#   literal 1 on the flushable arm neither advances the pre-state count nor is
#   caught at the F2P corner (where the starting count is 0 and the rival agrees
#   with gold exactly). It is a genuine wrong impl, rejected by clause (2), and it
#   lands with a discriminating witness at a nonzero starting count. Shipped as
#   weak-fabricate-absolute-count. The original "any other value is caught by
#   clauses (2)/(3) directly" was true but is not an argument for dropping the
#   case — being caught by a clause is what a reject case DEMONSTRATES.
# PORTED (partial-domain): weak-drop-guard-unconditional ports as
#   weak-unconditional-forward (advance the count on every stream => violates
#   clause (3) on the non-flushable arm). weak-noop-prepatch ports directly (never
#   forward => violates clause (2) on the flushable arm; this is the pre-change
#   behaviour).
#
# DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
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
#
# BINDER / CLAUSE COVERAGE. All three independent top-level clauses are attacked:
#   (1) frame by weak-frame-write-flushable, (2) forward-once by weak-noop-prepatch
#   AND weak-fabricate-absolute-count (never-write vs. write-the-wrong-value — two
#   distinct ways to miss the same clause), (3) no-op-on-non-flushable by
#   weak-unconditional-forward; and all three are defended by the two positive
#   controls and the admissibility case. The four reject witnesses probe four
#   DISTINCT starting states:
#     { flushable := true,  flushes := 0 }   weak-noop-prepatch
#     { flushable := false, flushes := 2 }   weak-unconditional-forward
#     { flushable := false, flushes := 5 }   weak-frame-write-flushable
#     { flushable := true,  flushes := 3 }   weak-fabricate-absolute-count
#   so `flushable` is varied over {true, false} (the sole branch determinant) and
#   the starting `flushes` over {0, 2, 3, 5} — and crucially the FLUSHABLE arm is
#   now probed at both a zero and a nonzero starting count, which is what separates
#   "the count advances" from "the count ends up at 1". Neither aspect of `sink` is
#   pinned across the battery. Each witness binds nothing (literal starting state),
#   so no consistency probe applies.
#
# WHY THE VALUE-LEVEL RIVAL LANE IS EXHAUSTED (audit note). The three `ensures`
#   clauses UNIQUELY DETERMINE the post-state from the pre-state: given `sinkOld`,
#   any two post-states satisfying all three clauses are equal (machine-checked
#   out-of-band: the `s1 = s2` derivation from the six hypotheses closes by
#   `cases`/`simp_all` on the two-constructor carrier). So no value-level wrong
#   impl over this carrier can satisfy the spec — the post-image admits exactly
#   one behaviour, which is the gold one. That is why the spec-too-weak lane
#   bottoms out at the four rivals above rather than at some untested residue;
#   the only remaining hole on this bundle is the corpus-wide `partial`-semantics
#   divergence one recorded below.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom (the operation is modeled directly over the carrier; there is no
#   unchanged callee to contract — mapping.md §3.1), so there is nothing to probe.
AXIOM_TESTS = []
