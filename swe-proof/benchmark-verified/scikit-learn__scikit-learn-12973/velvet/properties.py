"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12973 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region
and, where a case legitimately re-proves, the ``prove_correct`` tactic body is
changed — both elided from the consumer spec view, so ``markers.same_spec`` holds
and the ``prove_correct applyWithCopyChoice`` obligation survives).
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one modeled method over an optional per-call copy choice, a
caller data buffer, the target vector that travels with it, and the buffer the
second consumer is handed):

  applyWithCopyChoice (mut data) (target) (configuredCopy) (requestedCopy)
      return (work : Array Int)
    ensures effectiveCopy configuredCopy requestedCopy = true  → data = dataOld
    ensures bothRoutinesDeliver dataOld target →
              effectiveCopy configuredCopy requestedCopy = true  →
              work = prepareInPlace dataOld target
    ensures bothRoutinesDeliver dataOld target →
              effectiveCopy configuredCopy requestedCopy = false →
              data = searchInPlace (prepareInPlace dataOld target) target
    ensures bothRoutinesDeliver dataOld target →
              effectiveCopy configuredCopy requestedCopy = false →
              work = searchInPlace (prepareInPlace dataOld target) target

where ``effectiveCopy configured requested = requested.getD configured`` (an
explicit per-call choice takes precedence; the configured default is used when
none is supplied).

``bothRoutinesDeliver`` is the DOMAIN of the two-routine sequence: neither
routine is total, and on a pair where a reduction produces an entry the next
check refuses the routine SIGNALS instead of returning a buffer, so the three
clauses that name a routine's output are stated where an output exists. It is a
function of ``(buffer, target)`` only -- NOT of the copy choice -- so it cannot
be used to make a delivered buffer vary with the choice, and on every delivering
pair all four clauses bind exactly as they did. The frame clause carries NO such
hypothesis: the first routine copies before it reduces, so the caller's buffer is
preserved on the preserve leg whether the sequence delivers or signals.

THE CARRIER IS TWO-STAGE AND TWO-BUFFERED, and that is what shapes this battery.
The modeled routine hands the caller's buffer to TWO opaque in-place consumers in
sequence (mapping.md §0), each of which the effective choice must govern:

  * ``prepareInPlace : Array Int → Array Int → Array Int`` — the FIRST consumer's
    transform, of the buffer AND the companion target (the target fixes how the
    routine groups the buffer's entries; see Solution.lean's axioms region).
    Unary: measured independent of the target vector, and measured independent of
    its own gate, so ONE symbol denotes its output on both legs (axiom_check.py).
  * ``searchInPlace : Array Int → Array Int → Array Int`` — the SECOND
    consumer's in-place effect, on whatever buffer it is HANDED, under the target
    vector. Binary because the target is genuinely read (measured).

and TWO buffers survive a run, which are NOT the same buffer:

  * ``data`` — the CALLER's buffer;
  * ``work`` — the buffer the second consumer was handed, as that consumer left
    it. On the preserve leg the first consumer works on a buffer of its OWN, so
    ``work`` is that private buffer and the caller's buffer is decoupled from the
    second consumer entirely; on the overwrite leg the two are one array
    (refinement.md op #5), which is why the ``false`` clauses share a right-hand
    side. The run's consumer READS ``work`` after both consumers return
    (mapping.md §3.4), so it is observable.

Both symbols are ``axiom`` declarations and are deep-model REFERENCES: neither is
ever equated to anything, so the ``false`` clauses assert only
``… = searchInPlace (prepareInPlace dataOld target) target`` and deliberately NOT
``… ≠ dataOld`` (the real consumers may legitimately leave a degenerate buffer
unchanged). That is what keeps the spec non-overclaiming, and it is also why the
overwrite-clause rivals below cannot be refuted by ``decide``.

THE OBLIGATION THE ``work`` CLAUSE BUYS, and the hole it closes. A
caller's-buffer-only carrier — the two ``data`` clauses alone — states nothing
whatever about the second consumer ON THE PRESERVE LEG, and not because the
clause is weakly phrased: on that leg the first consumer hands the second one a
private buffer, so ``data = dataOld`` holds for an implementation that gates the
second consumer correctly and EQUALLY for one that gates it by the raw per-call
request, by a constant, or not at all. Such an implementation preserves the
caller's buffer and still reports numbers built from a buffer the second consumer
reworked, which is a real and measured defect shape (it regresses the
preserved-behaviour leg that refits one shared matrix and compares the reported
coefficients). ``work = prepareInPlace dataOld target`` is the clause that rejects it:
the rival's ``work`` is ``searchInPlace (prepareInPlace dataOld target) target``, and
equating the two is unprovable for an opaque ``searchInPlace``. THREE rivals
attack that clause — ``weak-second-routine-ungated`` (the recorded attack's own
shape, sharpened), ``weak-second-stage-raw-per-call`` (the raw-gate variant), and
``weak-work-is-caller-buffer`` (the first consumer's output discarded).
``weak-drops-second-stage`` is the single-stage impl, now rejected on the
``work`` half of the overwrite leg, and ``weak-second-stage-drops-target`` keeps
both consumers and feeds the second the wrong second argument, which is what
makes ``target`` load-bearing rather than decorative.

ALL FOUR clauses are attacked, and each by the technique its own reducibility
admits:

  1. A PRESERVE-``data`` violation is decidable at a literal input WHEN the
     rival's overwrite is CONCRETE. On an ``effectiveCopy … = true`` input the
     ``false`` clauses are vacuous and the ``data`` clause reduces to
     ``data = dataOld`` — no opaque term on the spec side — so a rival that
     concretely overwrites the buffer yields a ``decide``-able violation.
  2. A violation where EITHER side of the equation names an opaque consumer
     (every ``work`` case, and every overwrite-clause case) is NOT decidable at a
     literal input: ``decide`` reduces a ``Decidable`` instance and that reduction
     gets stuck on the opaque application (measured — see WITNESS MECHANICS). It
     is still refutable, by CONDITIONING on the carrier and discharging the
     refutation through DEFINITIONAL UNIFICATION rather than ``decide``: under the
     hypothesis that the modeled buffer value differs from what the rival
     concretely delivers, ``exact h (hc rfl)`` (or ``.symm``, per clause)
     typechecks against the rival — whose extracted output IS that value — and
     raises an ``Application type mismatch`` against the frozen solution. Each
     such witness binds ONE hypothesis about opaque terms, so the gate's
     consistency probe confirms it is satisfiable.

WHY THE OVERWRITE-``work`` CLAUSE IS ATTACKED ONLY JOINTLY, stated plainly
because the alternative would be a fabricated rival. On the overwrite leg the two
modeled buffers are the SAME array, so every rival that gets the exit contents
wrong there violates both ``false`` clauses at once — which is why
``weak-drops-second-stage``'s witness is aimed at the ``work`` component and the
other three overwrite rivals' at ``data``, giving each clause its own
machine-checked refutation. A rival violating ONLY the ``work`` half would have
to report a STALE snapshot of the buffer taken before the second consumer ran
while still letting that consumer write the caller's array. That is a coherent
implementation and the spec does reject it — but no shipped test leg pins the
reported numbers of a non-preserving run, so its faithful patch would RESOLVE the
instance, and shipping it with a "would not resolve" refinement argument would be
a fabrication. It is recorded here instead of invented.

ADVERSARIAL READ of the nagini classes on this carrier:

  * POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl must
    still satisfy all four clauses. THREE are carried: a negated-guard branch
    swap reproven with the frozen tactic body; an inlined
    ``requestedCopy.getD configuredCopy`` resolution; and a one-assignment form
    that resolves the choice by an explicit ``match`` on the option and writes the
    composite ``searchInPlace (prepareInPlace data target) target`` in a single step
    rather than staging it. The third is the direct control on the two-buffer
    strengthening: if adding the ``work`` clauses had made the spec demand a
    particular STAGING rather than a particular RESULT, that case would fail and
    the verdict would be SPEC-TOO-STRONG. Measured directly outside the gate as
    well: that impl verifies (exit 0) against the frozen spec.

  * ADMISSIBILITY — the method carries NO ``require`` clause, so the nagini
    precondition-admission probe (establish the precondition for an F2P-shaped
    input) has no binder to attack; it is vacuous. The residual admissibility
    risk on a total domain is that the frame is UNSATISFIABLE / DEGENERATE at the
    interesting point. The honest analogue discharges an in-region ``assert``
    that the resolution really demands overwrite at the F2P-discriminating input
    (configured True, explicit per-call False) and preserve at the absent-choice
    input (configured True, none) — the latter being exactly the point the
    preserved-behaviour test exercises — a live, non-degenerate obligation (a
    false variant of it leaves an unsolved goal), with the frozen impl kept
    verbatim so all four clauses still discharge.

  * PARTIAL-DOMAIN / VALUE + ABSENT-CHOICE FALLTHROUGH + EXPLICIT-CHOICE POLARITY
    + PER-CONSUMER DECOUPLING + PER-BUFFER DECOUPLING (uniqueness) — APPLY. Eleven
    rivals attack the frame, spanning ALL FOUR clauses, BOTH consumers, BOTH
    observable buffers, and all three ``requestedCopy`` shapes:
      - weak-ignores-per-call: the frame is decided by ``configuredCopy`` alone;
        refuted where a present per-call choice should have preserved but the
        configured value overwrote (configured False, requested some True).
      - weak-delivers-complement: the choice is resolved correctly then inverted;
        refuted where an explicit preserve request is honored as an overwrite
        (configured True, requested some True).
      - weak-absent-choice-hardcodes-overwrite: an explicit choice is honored but
        an ABSENT one is hardcoded to overwrite (``requestedCopy.getD false``);
        refuted only on the ``requested = none`` arm (configured True, none).
      - weak-overwrite-wrong-value: the choice is resolved correctly but the
        non-preserving branch delivers a buffer that is not what the consumers
        produce; refuted on the OVERWRITE arm (configured True, some False).
      - weak-absent-choice-hardcodes-preserve: the mirror fallthrough defect — an
        absent choice is hardcoded to PRESERVE (``requestedCopy.getD true``);
        refuted at (configured False, none), the one corner no other rival
        reaches, and on the overwrite clause.
      - weak-resolves-then-ignores: the resolution is computed and then discarded
        by a guard true on every input, so no buffer is ever touched; refuted on
        the overwrite arm (configured True, some False).
      - weak-second-routine-ungated: THE RECORDED ATTACK, sharpened. The caller's
        buffer frame is exactly right on both legs; the second consumer is simply
        never gated, so on the preserve leg it reworks the first consumer's own
        buffer. Refuted on the PRESERVE-``work`` clause at (configured True,
        requested some True) — a point at which the ``data`` clause is satisfied.
      - weak-second-stage-raw-per-call: the resolution governs the FIRST consumer
        only; the second is gated by the raw per-call request. Refuted on the
        PRESERVE-``work`` clause at (configured True, none) — the absent-choice
        arm, where the raw request is falsy and the second consumer reworks a
        buffer the effective choice said to leave alone.
      - weak-work-is-caller-buffer: both consumers are gated correctly, but on the
        preserve leg the run reports the CALLER's buffer as the one handed on, so
        the first consumer's output is discarded. Refuted on the
        PRESERVE-``work`` clause at (configured False, some True).
      - weak-drops-second-stage: the second consumer is not applied at all (the
        single-stage impl); refuted on the OVERWRITE-``work`` clause, where the
        buffer is left holding only the first consumer's output.
      - weak-second-stage-drops-target: both consumers run, but the second is fed
        the buffer in place of the target; refuted on the OVERWRITE-``data``
        clause, which is what shows ``target`` is constrained by the spec rather
        than carried decoratively.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini frame-mutation rival wrote
    a read-only input granted only a half permission and was rejected by the
    permission system. Velvet is referentially transparent; the only ``mut``
    binder here is ``data`` (legitimately mutated on the overwrite branch), the
    three read-only inputs carry no heap permission, and there is no aliasing to
    exploit. No expressible instance; no substitute fabricated.

  * VALUE DOUBLE-MASK / ARRAY-EFFECT DECOUPLING — PORTED, and now instantiated
    THREE ways. The nagini double-mask rival decouples a SECOND observable (the
    returned preference value) from the array fate. The generic form is "the
    resolution is computed correctly and then never allowed to govern the
    buffer", expressible here as a live ``copy`` binding whose value is discarded
    by a guard that is true on every input (``weak-resolves-then-ignores``). On
    this carrier the class gains its sharpest instances, because there really are
    TWO observables to decouple: the resolution governs one consumer and is
    decoupled from the other (``weak-second-stage-raw-per-call``), or it governs
    the caller's buffer and is decoupled from the buffer handed on
    (``weak-second-routine-ungated``). Those are the shapes a
    caller's-buffer-only spec admitted.

  * DIVERGENCE / NON-TERMINATION — the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
    and the ``open`` is the line that actually selects the semantics: both
    namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins,
    and the ``PartialCorrectness`` version takes a loop measure and DISCARDS it,
    so the two lines have to move together and they do here. Under the total
    scope a postcondition is claimed of ALL runs and not only of terminating
    ones, so a spliced loop owes a descent obligation ``measure b' < measure b``.
    Measured on this bundle with a real build: a ``while spin > 0 do spin :=
    spin`` prefix carrying ``decreasing spin`` is REJECTED on the measure's own
    goal (``case «decreasing_1: spin» … ⊢ spin < spin``), and an increasing
    measure is likewise rejected (``⊢ k + 1 < k``). Dropping the clause rather
    than faking it is refused even earlier, by the elaborator's own check
    (``Decreasing annotations are required in total correctness semantics``). So
    divergence neither applies to this impl nor discharges the ``ensures``
    clauses vacuously if a rival introduces it. There is NO loop-measure vacuity
    on this carrier: the strict-decrease side condition IS emitted and IS left
    unsolved.

    It is still not shipped as a reject case, and the reason is the WITNESS
    CONTRACT rather than any spec weakness. A reject case must carry a witness
    that ELABORATES against the rival, and a diverging rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself, ahead
    of any appended tester. Measured through the gate's own ``_check_witness``,
    even ``example : True := trivial`` comes back ``witness-unproven`` on such a
    rival, an INCONCLUSIVE outcome that would fail the whole battery rather than
    pass a case. Recorded as REJECTED-BY-SPEC and not expressible as a witnessed
    case, which is neither a spec hole nor a battery gap.

WITNESS MECHANICS (the part with no nagini counterpart).

Witnesses reach the modeled behaviour through the extracted EXECUTABLE, whose
type was MEASURED rather than assumed — the method now returns a value as well as
mutating ``data``, so the ``DivM`` payload is a PAIR of buffers:

    applyWithCopyChoiceExec : Array ℤ → Array ℤ → Bool → Option Bool →
                              DivM (Array ℤ × Array ℤ)

with the FIRST component the returned ``work`` and the SECOND the final ``data``.
Both projections were checked against the frozen solution by ``rfl`` on both
legs (``(w, _)`` is ``prepareInPlace buf target`` / the composite; ``(_, d)`` is ``buf``
/ the composite), so a witness that aims at the wrong component cannot pass
unnoticed. Witnesses project the component whose clause they attack and state the
negation of that clause.

``derive_tester_for applyWithCopyChoice`` DOES elaborate here provided it follows
``extract_program_for``, but the tester is unusable for any claim whose terms
reach an opaque consumer: because the postcondition names ``prepareInPlace`` /
``searchInPlace``, ``decide`` on the tester gets STUCK (``did not reduce to
isTrue or isFalse``) against BOTH the rival and the frozen solution at such an
input, so its exit code discriminates nothing there. The witnesses are therefore
stated over the executable, and ``decide`` is used only where BOTH sides of the
claim are concrete.

The extraction must be wrapped in ``noncomputable section … end``. This is
LOAD-BEARING, not cosmetic. ``extract_program_for`` emits a ``def``, so Lean
tries to compile it to executable IR; the frozen impl names opaque axioms, which
have no executable code, so that compilation FAILS against gold with

  failed to compile definition, compiler IR check failed at
  `applyWithCopyChoiceExec` … depends on declaration 'applyWithCopyChoice',
  which has no executable code

— a build failure in the PREAMBLE, before the witness's own claim is ever
elaborated. Unwrapped, the gold-side build then fails for EVERY witness
regardless of truth, so its exit code discriminates nothing and a tautology
clears both halves. Measured: ``example : (1:Nat) = 1 := by decide`` under a bare
``extract_program_for`` preamble gives rival exit 0, gold exit 1 — a forgery that
would have been recorded as a refutation. Wrapping the extraction in
``noncomputable section`` skips IR compilation while leaving KERNEL reduction
(what ``decide`` and definitional unification actually use) untouched; the same
tautology then passes on gold (exit 0), which is the check that the gold-side
exit code carries information again. No ``sorry``/``admit``/``native_decide``/
``axiom``/``opaque`` is used by any witness.

BINDER COVERAGE. The eleven reject witnesses probe SIX distinct input points
across ALL FOUR clauses and BOTH observable buffers; every input binder moves,
and each of the two modeled consumers is attacked on its own:

  (configured=false, requested=some true)  preserve/data  present choice ignored
  (configured=true,  requested=some true)  preserve/data  resolved choice inverted
  (configured=true,  requested=none)       preserve/data  absent choice → overwrite
  (configured=true,  requested=some true)  preserve/work  second consumer never gated
  (configured=true,  requested=none)       preserve/work  second consumer gated by the raw request
  (configured=false, requested=some true)  preserve/work  first consumer's output discarded
  (configured=true,  requested=some false) overwrite/data wrong buffer delivered
  (configured=true,  requested=some false) overwrite/data resolution never consumed
  (configured=true,  requested=some false) overwrite/work second consumer omitted
  (configured=true,  requested=some false) overwrite/data second consumer fed the wrong target
  (configured=false, requested=none)       overwrite/data absent choice → preserve

so ``configuredCopy`` moves over {true, false}, ``requestedCopy`` over
{some true, some false, none}, and the ``data`` and ``target`` buffers over
distinct arrays (each case gets its own pair, so no two witnesses share a
refutation point even where they share an input arm). Where two rivals do share
an arm they differ in WHICH clause they violate, in which observable buffer they
violate it on, and in which opaque term the hypothesis is about, and every one of
them is separately machine-checked against gold.

AXIOM lane: DROPPED. The ``axioms`` region declares ``prepareInPlace`` and
``searchInPlace``, but those are G-AX-validated deep-model references (their
frame, determinacy, gate-independence and composite two-buffer laws are checked
against the real unchanged callees in ``axiom_check.py``), not this gate's
concern; and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12973"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region and the FULL frozen proof body, so every
# replacement lands entirely inside the region it means to edit.
_GOLD_IMPL = (
    "    let copy := effectiveCopy configuredCopy requestedCopy\n"
    "    if copy then\n"
    "      return prepareInPlace data target\n"
    "    else\n"
    "      data := prepareInPlace data target\n"
    "      data := searchInPlace data target\n"
    "      return data"
)
_GOLD_PROOF = "  loom_solve"


def _swap2(impl_new, proof_new):
    """Reshape the impl region AND retune the prove_correct tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, impl_new), _GOLD_PROOF, proof_new)


# ---- witness preamble -------------------------------------------------------
# `extract_program_for` yields the executable `applyWithCopyChoiceExec`, through
# which a witness reaches the modeled behaviour. The `noncomputable section`
# wrapper is LOAD-BEARING — see WITNESS MECHANICS in the module docstring.
_EXTRACT = ("noncomputable section\n"
            "extract_program_for applyWithCopyChoice\n"
            "end\n\n")


def _exec(buf, target, configured, requested):
    return ("applyWithCopyChoiceExec " + buf + " " + target + " "
            + configured + " " + requested)


def _out_data(buf, target, configured, requested):
    """The CALLER's buffer the extracted executable delivers (2nd component)."""
    return ("(match " + _exec(buf, target, configured, requested)
            + " with | DivM.res (_, d) => d | _ => #[99])")


def _out_work(buf, target, configured, requested):
    """The buffer handed to the second consumer, as the executable reports it
    (1st component — the returned `work`)."""
    return ("(match " + _exec(buf, target, configured, requested)
            + " with | DivM.res (w, _) => w | _ => #[99])")


def _modeled(buf, target):
    """The buffer value BOTH overwrite clauses pin: the two modeled consumers
    composed in call order."""
    return "searchInPlace (prepareInPlace " + buf + " " + target + ") " + target


def _preserve_data_witness(configured, requested, buf, target):
    """Negate the PRESERVE clause on the CALLER's buffer at a concrete
    `effectiveCopy … = true` input, for a rival whose overwrite is CONCRETE.

    On such an input the overwrite clauses are vacuous and this clause reduces to
    `data = buf` — no opaque term on either side — so a literal `decide` settles
    it. It holds of a rival that concretely overwrites `buf` and FAILS on the
    frozen solution, which preserves it (gold-side error: "`decide` proved that
    the proposition … is false" — a semantic refutation, not a stuck reduction).
    Binds nothing, so no consistency probe is needed.
    """
    return (
        _EXTRACT +
        "example :\n"
        "  ¬ ( (effectiveCopy " + configured + " " + requested + " = true →\n"
        "        " + _out_data(buf, target, configured, requested)
        + " = " + buf + ")\n"
        "    ) := by decide\n"
    )


def _preserve_work_witness(configured, requested, buf, target, delivered):
    """Negate the PRESERVE clause on the buffer HANDED ON — the clause that
    closes the recorded hole — at an `effectiveCopy … = true` input.

    Both sides can name an opaque consumer here (the spec side always does:
    `work = prepareInPlace dataOld target`), so `decide` is unusable — the `Decidable`
    reduction gets stuck, including against the rival, which is the half that
    must SUCCEED. The refutation is discharged by DEFINITIONAL UNIFICATION:

      * `hc rfl` instantiates the clause at this input (`rfl` closes the
        `effectiveCopy … = true` guard by defeq), giving
        `work = prepareInPlace buf target`;
      * `exact h (hc rfl)` then typechecks exactly when the extracted `work` is
        definitionally `delivered` — which is what the rival reports, and is NOT
        what the frozen solution reports (its `work` on this leg is literally
        `prepareInPlace buf target`, so gold fails with `Application type mismatch`).

    The single free hypothesis says two distinct applications of opaque symbols
    differ, so the gate's consistency probe confirms it is satisfiable.
    """
    return (
        _EXTRACT +
        "example (hd : bothRoutinesDeliver " + buf + " " + target + ")\n"
        "        (h : " + delivered + " ≠ prepareInPlace " + buf + " " + target + ") :\n"
        "  ¬ ( (bothRoutinesDeliver " + buf + " " + target + " →\n"
        "        effectiveCopy " + configured + " " + requested + " = true →\n"
        "        " + _out_work(buf, target, configured, requested)
        + " = prepareInPlace " + buf + " " + target + ")\n"
        "    ) := by\n"
        "  intro hc\n"
        "  exact h (hc hd rfl)\n"
    )


def _overwrite_witness(configured, requested, buf, target, delivered,
                       component="data"):
    """Negate an OVERWRITE clause at a concrete `effectiveCopy … = false` input,
    on the CALLER's buffer (`component="data"`) or on the buffer handed on
    (`component="work"`).

    The overwrite clauses name the opaque consumers, so no literal input DECIDES
    them — `decide` reduces a `Decidable` instance and that reduction gets stuck
    on the opaque application. The refutation is therefore discharged by
    DEFINITIONAL UNIFICATION instead, at a point described by hypothesis:

      * `hc rfl` instantiates the clause at this input (`rfl` closes the
        `effectiveCopy … = false` guard by defeq);
      * `exact h (hc rfl).symm` then typechecks exactly when the extracted
        component is definitionally `delivered` — which is what the rival
        delivers, and is NOT what the frozen solution delivers (both of its
        components on this leg are literally
        `searchInPlace (prepareInPlace dataOld target) target`, so gold fails with
        `Application type mismatch`).

    `delivered` must match the rival's concrete output on the false branch. The
    single free hypothesis relates opaque applications, so the gate's consistency
    probe confirms it is satisfiable (the probe's unsolved-goal failure is exactly
    that confirmation).
    """
    out = (_out_work if component == "work" else _out_data)(
        buf, target, configured, requested)
    return (
        _EXTRACT +
        "example (hd : bothRoutinesDeliver " + buf + " " + target + ")\n"
        "        (h : " + _modeled(buf, target) + " ≠ " + delivered + ") :\n"
        "  ¬ ( (bothRoutinesDeliver " + buf + " " + target + " →\n"
        "        effectiveCopy " + configured + " " + requested + " = false →\n"
        "        " + out + " = " + _modeled(buf, target) + ")\n"
        "    ) := by\n"
        "  intro hc\n"
        "  exact h (hc hd rfl).symm\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen clauses the spec is SPEC-TOO-STRONG. Each keeps
    # the `prove_correct applyWithCopyChoice` obligation and only reshapes the
    # executable surface (+ retunes the tactic body where needed); none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-control-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Negate the copy guard and swap the branches: test the overwrite case
        # first, preserve in the else. Same preserve-iff-effective-copy decision,
        # the same two consumers in the same order, and the same buffer reported
        # as handed on, so all four clauses still hold. Frozen tactic body kept.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy = false then\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data\n"
            "    else\n"
            "      return prepareInPlace data target",
        ),
        "rationale": "a structurally-different but CORRECT impl (guard negated, "
                     "branches swapped, same preserve-iff-effective-copy frame "
                     "across both consumers and both observable buffers) must "
                     "satisfy all four clauses; if it cannot, SPEC-TOO-STRONG. "
                     "Proof: frozen `loom_solve` retained — it still closes for "
                     "the reshaped branch order.",
    },
    {
        "id": "pos-control-inline-getd",
        "kind": "soundness",
        "expect": "verify",
        # Inline the effective-choice resolution as `requestedCopy.getD
        # configuredCopy` (definitionally `effectiveCopy configuredCopy
        # requestedCopy`) rather than the named helper. Same value on every
        # input; the tactic body is retuned with `simp_all [effectiveCopy]` so
        # the two forms are reconciled (no new lemma/axiom).
        "module": _swap2(
            "    let copy : Bool := requestedCopy.getD configuredCopy\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
            "  loom_solve <;> simp_all [effectiveCopy]",
        ),
        "rationale": "resolving the choice inline as `requestedCopy.getD "
                     "configuredCopy` equals `effectiveCopy configuredCopy "
                     "requestedCopy` definitionally, so all four clauses hold "
                     "pointwise; a correct reshape must verify. Proof: tactic "
                     "body retuned with `simp_all [effectiveCopy]` to reconcile "
                     "the inlined form — no helper lemma or assumption added.",
    },
    {
        "id": "pos-control-composite-one-assignment",
        "kind": "soundness",
        "expect": "verify",
        # THE CONTROL ON THE TWO-BUFFER STRENGTHENING. Resolve the choice by an
        # explicit `match` on the option (rather than the helper or `getD`) and
        # write the composite `searchInPlace (prepareInPlace data target) target` in ONE
        # assignment rather than staging it through two. Same exit buffers on
        # every input. If the spec had accidentally demanded a particular STAGING
        # rather than particular RESULTS — a real risk when clauses are
        # strengthened to name two composed consumers over two buffers — this case
        # would fail and the verdict would be SPEC-TOO-STRONG. Measured outside
        # the gate too: exit 0.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let choice := match requestedCopy with\n"
            "      | some b => b\n"
            "      | none => configuredCopy\n"
            "    if choice then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := searchInPlace (prepareInPlace data target) target\n"
            "      return data",
        ),
        "rationale": "a correct impl that resolves the choice by an explicit "
                     "`match` and writes the composite of the two consumers in a "
                     "SINGLE assignment must verify: the strengthened clauses pin "
                     "the exit VALUES of the two observable buffers, not the "
                     "number of assignment steps used to reach them. If this were "
                     "rejected the two-buffer clauses would be over-specifying "
                     "the implementation and the verdict would be "
                     "SPEC-TOO-STRONG. Proof: frozen `loom_solve` retained — "
                     "measured to close the `match` form as well, so not even a "
                     "tactic retune is needed.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the frame is SATISFIABLE
    # and NON-DEGENERATE at the discriminating inputs rather than only provable
    # in the abstract. No `require` clause exists, so the nagini
    # precondition-admission probe has no binder to attack; the honest analogue
    # discharges an in-region `assert` that the effective-choice resolution
    # demands OVERWRITE at (configured True, explicit per-call False) and
    # PRESERVE at (configured True, none) — the two arms the tests exercise —
    # then closes the frozen obligation verbatim. The assert is live: a false
    # variant leaves an unsolved goal (verified).
    # =====================================================================
    {
        "id": "admiss-f2p-frame-non-degenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    assert (with_name_prefix `assert\n"
            "      (effectiveCopy true (some false) = false ∧ "
            "effectiveCopy true none = true))\n"
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
        ),
        "rationale": "the frame is non-degenerate at the discriminating inputs: "
                     "the resolution demands OVERWRITE at (configured True, "
                     "explicit per-call False) — where the frozen obligation would "
                     "otherwise be vacuous had the choice been ignored — and "
                     "PRESERVE at (configured True, none), the absent-choice arm "
                     "the preserved-behaviour test exercises. The in-region assert "
                     "must discharge (else the modeled frame is unsatisfiable at "
                     "exactly the inputs the tests exercise, the analogue of "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so all four "
                     "clauses still discharge too. Nothing is assumed: no new "
                     "declaration, the obligation is unchanged, and the assert is "
                     "a live goal (a false variant fails).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the instance and
    # (b) a refutation witness, seen to hold of the rival and to FAIL
    # semantically on the frozen solution, pinning the violated clause at one
    # concrete input.
    # =====================================================================
    {
        "id": "weak-ignores-per-call",
        "kind": "uniqueness",
        "expect": "reject",
        # The baseline defect on the first consumer: the frame is decided by
        # `configuredCopy` alone; the per-call choice never reaches the buffer.
        # Refuted where an explicit PRESERVE request (some true) should have
        # preserved but the configured False overwrote.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if configuredCopy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := data.push 0\n"
            "      return data",
        ),
        "refinement": "ignoring the per-call choice and deciding the buffer frame "
                      "by the configured value alone is exactly the pre-existing "
                      "behavior: the explicit per-call choice never reaches the "
                      "data-preparation step. On the newly-tested case — a default "
                      "consumer with an explicit per-call choice — the buffer "
                      "frame is governed by the configured value, so the caller's "
                      "per-call intent is silently overridden and the new test "
                      "asserting the per-call choice governs the buffer FAILS. It "
                      "would NOT resolve — this is the leg's baseline.",
        "rationale": "REJECT from the PRESERVE clause on the caller's buffer, "
                     "`effectiveCopy … = true → data = dataOld`: at configured "
                     "False, requested some True the effective choice is True "
                     "(preserve), but this rival reads configured False and "
                     "overwrites the buffer. The violation is at a literal input "
                     "with a concrete overwrite, so `decide` settles it; gold "
                     "fails semantically there (`decide` proves the negation "
                     "false).",
        "witness": _preserve_data_witness("false", "(some true)", "#[(1:Int)]",
                                         "#[(11:Int)]"),
    },
    {
        "id": "weak-delivers-complement",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves the choice exactly as gold, then INVERTS the frame decision:
        # every preserve becomes an overwrite and vice versa. Refuted where an
        # explicit preserve request (some true) is honored as an overwrite.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      data := data.push 0\n"
            "      return data\n"
            "    else\n"
            "      return prepareInPlace data target",
        ),
        "refinement": "its faithful real patch resolves the per-call/configured "
                      "precedence correctly and then hands the consumers the "
                      "OPPOSITE frame, so every request to preserve overwrites and "
                      "every request to overwrite preserves. The discriminating "
                      "input would have its buffer touched exactly opposite to what "
                      "the caller asked, which is what the new test forbids, and "
                      "both pre-existing legs invert as well. It would NOT resolve.",
        "rationale": "REJECT from the PRESERVE clause on the caller's buffer: at "
                     "configured True, requested some True the effective choice is "
                     "True (preserve), but this rival inverts and overwrites. "
                     "Refuted at a DIFFERENT `configuredCopy` value than "
                     "weak-ignores-per-call (True vs False): the two fail for "
                     "different reasons — one ignores the per-call choice, this "
                     "one inverts the resolved choice — so they do not share a "
                     "refutation point.",
        "witness": _preserve_data_witness("true", "(some true)", "#[(2:Int)]",
                                         "#[(12:Int)]"),
    },
    {
        "id": "weak-absent-choice-hardcodes-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        # Honors an explicit per-call choice, but resolves an ABSENT one to a
        # hardcoded overwrite (`requestedCopy.getD false`) instead of reading the
        # configured value. Invisible on the whole `requested = some _`
        # sub-domain; refuted only on the `requested = none` arm.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := requestedCopy.getD false\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := data.push 0\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves an absent per-call choice "
                      "to a hardcoded overwrite rather than reading the "
                      "consumer's configured value, so the configured value "
                      "never governs the buffer at all. It happens to agree with "
                      "the newly-tested input (which supplies an explicit "
                      "per-call choice), but it regresses the PRE-EXISTING "
                      "behavior on the absent-choice path: a consumer configured "
                      "to preserve, run with no per-call choice, would have its "
                      "buffer overwritten. The pre-existing test leg asserting the "
                      "configured preserve choice still governs a no-per-call run "
                      "therefore FAILS. Resolution requires the pre-existing legs "
                      "to keep passing alongside the new one, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the `requested = none` arm of the PRESERVE "
                     "clause on the caller's buffer: at configured True, requested "
                     "none the effective choice is the configured True (preserve), "
                     "but this rival hardcodes the absent choice to overwrite. "
                     "Refuted only where the per-call choice is ABSENT — this is "
                     "one of the cases that make `configuredCopy` load-bearing on "
                     "the fallthrough, since the rivals refuted at inputs carrying "
                     "an explicit choice mask it entirely.",
        "witness": _preserve_data_witness("true", "none", "#[(3:Int)]",
                                         "#[(13:Int)]"),
    },
    {
        "id": "weak-overwrite-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves the choice exactly as gold, but on the OVERWRITE branch delivers
        # a CONCRETE wrong buffer (`data.push 0`) instead of what the consumers
        # produce. Wrong across the whole `effective copy = false` direction;
        # refuted here on the `requested = some false` arm — the
        # explicit-overwrite point no preserve-direction rival can touch.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := data.push 0\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves the per-call/configured "
                      "precedence correctly but, on the branch where the caller "
                      "asked NOT to preserve, leaves the buffer holding something "
                      "other than what the two numeric routines actually produce. "
                      "On any input whose effective choice is overwrite the buffer "
                      "ends with the wrong contents, so the assertion that the "
                      "non-preserving path yields the processed buffer FAILS — the "
                      "test leg reads the buffer, not just whether it changed. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the OVERWRITE clause on the caller's buffer, "
                     "`effectiveCopy … = false → data = searchInPlace "
                     "(prepareInPlace dataOld target) target`: at configured True, "
                     "requested some False the effective choice is False "
                     "(overwrite), and the spec pins the buffer to the composite "
                     "of the two consumers, but this rival delivers a concrete "
                     "`dataOld.push 0`. The clause names opaque consumers, so the "
                     "witness conditions on them by hypothesis and discharges by "
                     "definitional unification rather than `decide` (which would "
                     "get stuck); the consistency probe confirms the hypothesis is "
                     "satisfiable, and gold fails with an `Application type "
                     "mismatch` because its false branch delivers exactly the "
                     "composite.",
        "witness": _overwrite_witness("true", "(some false)", "#[(4:Int)]",
                                      "#[(14:Int)]", "(#[(4:Int)]).push 0"),
    },
    {
        "id": "weak-absent-choice-hardcodes-preserve",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR fallthrough defect: an explicit per-call choice is honored,
        # but an ABSENT one is hardcoded to PRESERVE (`requestedCopy.getD true`)
        # instead of reading the configured value. Invisible on the whole
        # `requested = some _` sub-domain AND at configured True; refuted only at
        # (configured False, none) — the one corner of the input space no other
        # rival in this battery reaches — and on the OVERWRITE clause.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := requestedCopy.getD true\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves an absent per-call choice "
                      "to a hardcoded PRESERVE rather than reading the consumer's "
                      "configured value. It agrees with the newly-tested input "
                      "(which supplies an explicit per-call choice) and it agrees "
                      "wherever the configured value is preserve, which is the "
                      "configured default — so it looks correct on most of the "
                      "domain. But it regresses the PRE-EXISTING behavior for a "
                      "consumer configured NOT to preserve and run with no "
                      "per-call choice: the buffer would be left untouched where "
                      "the configured choice demands it be overwritten, and the "
                      "pre-existing test leg asserting the configured "
                      "non-preserving choice governs a no-per-call run FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the `requested = none` arm of the OVERWRITE "
                     "clause on the caller's buffer: at configured False, "
                     "requested none the effective choice is the configured False "
                     "(overwrite), but this rival hardcodes the absent choice to "
                     "preserve and leaves the buffer at `dataOld`. This is a "
                     "NEAR-MISS of weak-absent-choice-hardcodes-overwrite — the "
                     "same fallthrough binder, the opposite polarity — so it gets "
                     "its own refutation point at the opposite `configuredCopy` "
                     "value and on the opposite clause, rather than sharing a "
                     "witness. The clause names the opaque consumers, so the "
                     "witness conditions on the composite (`searchInPlace "
                     "(prepareInPlace buf target) target ≠ buf` — satisfiable, and NOT "
                     "something the spec asserts, which is why gold is not refuted "
                     "by it) and discharges by definitional unification.",
        "witness": _overwrite_witness("false", "none", "#[(5:Int)]", "#[(15:Int)]",
                                      "#[(5:Int)]"),
    },
    {
        "id": "weak-resolves-then-ignores",
        "kind": "uniqueness",
        "expect": "reject",
        # The DOUBLE-MASK analogue. The effective choice IS resolved correctly into
        # a live `copy` binding — every other rival's resolution can be blamed —
        # but the guard that consumes it is true on EVERY input, so the resolved
        # value never reaches the buffer at all and the caller's buffer is left
        # intact unconditionally. Distinct from the fallthrough/polarity rivals:
        # those get the frame wrong somewhere while still letting the resolution
        # govern it; this severs the connection entirely.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy || !copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves the per-call/configured "
                      "precedence correctly — it computes the right choice — and "
                      "then never routes that choice into either numeric routine, "
                      "so the caller's buffer is left intact on every run whatever "
                      "was asked. On the newly-tested input, which supplies an "
                      "explicit per-call choice NOT to preserve, the buffer comes "
                      "back unchanged, so the assertion that the non-preserving "
                      "path leaves the buffer overwritten FAILS; the pre-existing "
                      "non-preserving leg fails for the same reason. It would NOT "
                      "resolve. This is the cheapest 'looks right' defect: the "
                      "resolution is visibly correct in the source and is simply "
                      "never used.",
        "rationale": "REJECT from the OVERWRITE clause on the caller's buffer: at "
                     "configured True, requested some False the effective choice "
                     "is False (overwrite), and the spec pins the buffer to the "
                     "composite of the two consumers, but this rival returns "
                     "`dataOld` untouched. The resolution itself is correct, so no "
                     "PRESERVE-clause input refutes it on the caller's buffer — "
                     "the violation is visible on the overwrite clause, which "
                     "names the opaque consumers; the witness therefore conditions "
                     "on them by hypothesis and discharges by definitional "
                     "unification, and the consistency probe confirms the "
                     "hypothesis is satisfiable. Refuted at its own buffer/target "
                     "pair, not shared with any other witness.",
        "witness": _overwrite_witness("true", "(some false)", "#[(6:Int)]",
                                      "#[(16:Int)]", "#[(6:Int)]"),
    },
    {
        "id": "weak-second-routine-ungated",
        "kind": "uniqueness",
        "expect": "reject",
        # THE RECORDED ATTACK, SHARPENED — the most faithful model of the
        # behaviour that verified against a caller's-buffer-only carrier and then
        # failed the preserved-behaviour test. The caller's buffer frame is
        # EXACTLY right on both legs: preserve when the effective choice says
        # preserve, the full composite when it says overwrite. The only thing
        # wrong is that the second consumer is never GATED, so on the preserve
        # leg it reworks the buffer the first consumer produced for itself. A
        # caller's-buffer-only spec admits this, because on that leg the caller's
        # buffer is decoupled from the second consumer no matter what it does.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      let w := prepareInPlace data target\n"
            "      return searchInPlace w target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
        ),
        "refinement": "its faithful real patch threads the resolved choice into "
                      "the first numeric routine and hands the second routine a "
                      "hardcoded 'do not preserve', so the second routine always "
                      "rewrites the buffer it is given. The caller's buffer is "
                      "still preserved exactly when asked — the first routine took "
                      "a buffer of its own on that path — so the newly-tested leg, "
                      "which only reads the caller's buffer, PASSES. But the run "
                      "then computes its reported numbers from a buffer the second "
                      "routine has permuted in place, so the pre-existing leg that "
                      "refits one shared matrix under several configurations and "
                      "compares the reported coefficients gets different answers "
                      "and FAILS. Measured on the real repository: the reported "
                      "coefficients differ between a preserving and a "
                      "non-preserving second routine on 39 of 40 fuzzed matrices. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the PRESERVE clause on the buffer HANDED ON, "
                     "`effectiveCopy … = true → work = prepareInPlace dataOld target`: at "
                     "configured True, requested some True the effective choice is "
                     "True, this rival duly preserves the caller's buffer (so the "
                     "`data` clause is SATISFIED — that is the whole point), and "
                     "it reports `searchInPlace (prepareInPlace dataOld target) target` "
                     "as the buffer handed on, which the clause forbids. This is "
                     "the case a caller's-buffer-only carrier cannot reject, and "
                     "the rejection is on a FEASIBLE branch (the hypothesis "
                     "`effectiveCopy true (some true) = true` is closed by `rfl`), "
                     "so it is not a vacuous guard. Both sides name an opaque "
                     "consumer, so the witness conditions on their difference by "
                     "hypothesis and discharges by definitional unification; gold "
                     "fails with an `Application type mismatch` because gold's "
                     "reported buffer at this input is literally `prepareInPlace "
                     "dataOld target`.",
        "witness": _preserve_work_witness(
            "true", "(some true)", "#[(10:Int)]", "#[(20:Int)]",
            "searchInPlace (prepareInPlace #[(10:Int)] #[(20:Int)]) #[(20:Int)]"),
    },
    {
        "id": "weak-second-stage-raw-per-call",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PER-CONSUMER DECOUPLING DEFECT. The resolved choice governs the
        # FIRST consumer, exactly as the change intends; the SECOND consumer is
        # gated by the RAW per-call request, which is falsy whenever no per-call
        # choice was supplied. Agrees with gold on every input that carries an
        # explicit per-call choice — including the newly-tested one — and diverges
        # precisely on the absent-choice arm. Note that on the preserve leg the
        # CALLER's buffer is preserved either way, so only the buffer handed on
        # records the divergence.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    let raw := requestedCopy.getD false\n"
            "    if copy then\n"
            "      let w := prepareInPlace data target\n"
            "      if raw then\n"
            "        return w\n"
            "      else\n"
            "        return searchInPlace w target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      if raw then\n"
            "        return data\n"
            "      else\n"
            "        data := searchInPlace data target\n"
            "        return data",
        ),
        "refinement": "its faithful real patch resolves the per-call/configured "
                      "precedence and threads the resolved value into the FIRST "
                      "numeric routine only; the second routine keeps receiving "
                      "the raw per-call argument, which stands for 'do not "
                      "preserve' when the caller supplied nothing. The newly-tested "
                      "case passes, because it supplies an explicit per-call choice "
                      "that both routines then receive; and the caller's buffer is "
                      "never harmed, because on a preserving run the first routine "
                      "already took a buffer of its own. But the PRE-EXISTING leg "
                      "that refits one shared matrix with no per-call argument "
                      "under several configurations reads its numbers from a buffer "
                      "the second routine permuted in place, so the coefficients it "
                      "compares differ and it FAILS. It would NOT resolve.",
        "rationale": "REJECT from the PRESERVE clause on the buffer HANDED ON: at "
                     "configured True, requested none the effective choice is True "
                     "(preserve), the caller's buffer is duly preserved (`data` "
                     "clause SATISFIED), and the second consumer — gated by the "
                     "raw absent request — reworks the first consumer's buffer, so "
                     "the reported `work` is `searchInPlace (prepareInPlace "
                     "dataOld target) target` rather than `prepareInPlace dataOld target`. "
                     "Distinct from weak-second-routine-ungated in BOTH the module "
                     "(the per-call value is read, and honored when present) and "
                     "the refutation arm (the absent-choice arm rather than an "
                     "explicit request). The witness conditions on the opaque "
                     "difference by hypothesis and discharges by definitional "
                     "unification; gold fails with an `Application type mismatch`.",
        "witness": _preserve_work_witness(
            "true", "none", "#[(7:Int)]", "#[(17:Int)]",
            "searchInPlace (prepareInPlace #[(7:Int)] #[(17:Int)]) #[(17:Int)]"),
    },
    {
        "id": "weak-work-is-caller-buffer",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PER-BUFFER DECOUPLING DEFECT in its other direction: both consumers
        # are gated correctly and the caller's buffer frame is exactly right, but
        # on the preserve leg the run reports the CALLER's buffer as the one
        # handed on, discarding the first consumer's output. This is the case that
        # makes `prepareInPlace` load-bearing inside the `work` clause rather than
        # merely mentioned by it.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      return data\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data target\n"
            "      return data",
        ),
        "refinement": "its faithful real patch keeps the copy decision entirely "
                      "correct — the caller's buffer is preserved exactly when "
                      "asked, so the newly-tested leg PASSES — but on the "
                      "preserving path it hands the second numeric routine, and "
                      "the tail that reads the buffer afterwards, the caller's "
                      "ORIGINAL matrix rather than the one the first routine "
                      "produced. The first routine's centering and scaling are "
                      "therefore thrown away, and every pre-existing leg that "
                      "checks the reported coefficients or the reported intercept "
                      "of a default-configured run reads the fit of a different "
                      "problem and FAILS. It would NOT resolve.",
        "rationale": "REJECT from the PRESERVE clause on the buffer HANDED ON: at "
                     "configured False, requested some True the effective choice "
                     "is True (preserve), the caller's buffer is duly preserved "
                     "(`data` clause SATISFIED), and this rival reports `dataOld` "
                     "where the clause pins `prepareInPlace dataOld target`. A third "
                     "distinct refutation arm for the `work` clause (configured "
                     "False, an explicit request) and a distinct hypothesis shape: "
                     "the free hypothesis is that the first consumer is not the "
                     "identity on this literal buffer — satisfiable, and NOT "
                     "something the spec asserts, which is why gold is not refuted "
                     "by it. Discharged by definitional unification; gold fails "
                     "with an `Application type mismatch`.",
        "witness": _preserve_work_witness(
            "false", "(some true)", "#[(12:Int)]", "#[(22:Int)]", "#[(12:Int)]"),
    },
    {
        "id": "weak-drops-second-stage",
        "kind": "uniqueness",
        "expect": "reject",
        # The SINGLE-STAGE impl itself: the choice is resolved correctly and
        # governs the first consumer, and the second consumer is never applied.
        # Under a one-consumer spec this IS the gold impl; under this spec it is a
        # rival, which is exactly what the strengthening bought. Its witness is
        # aimed at the OVERWRITE-`work` clause, so that clause has a refutation of
        # its own (on the overwrite leg the two modeled buffers are one array, so
        # this rival violates the `data` half too).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves the choice correctly for "
                      "the first numeric routine and then does not let the second "
                      "routine touch the buffer at all — it hands that routine a "
                      "defensive copy unconditionally. On the non-preserving path "
                      "the buffer the run reports, and the caller's buffer with it, "
                      "therefore end holding only the first routine's output rather "
                      "than the result of the whole run, so a leg that reads the "
                      "buffer after a non-preserving run sees the wrong contents "
                      "and FAILS. It would NOT resolve.",
        "rationale": "REJECT from the OVERWRITE clause on the buffer HANDED ON, "
                     "`effectiveCopy … = false → work = searchInPlace "
                     "(prepareInPlace dataOld target) target`: at configured True, "
                     "requested some False this rival reports `prepareInPlace "
                     "dataOld`. The witness conditions on the two opaque consumers "
                     "differing at this point (satisfiable — nothing in the spec "
                     "says a second pass is a fixpoint of the first's output) and "
                     "discharges by definitional unification; gold fails with an "
                     "`Application type mismatch`. This case is the direct "
                     "measurement that the second consumer is load-bearing in the "
                     "spec rather than decoration — it is the impl a one-consumer "
                     "spec accepts — and it is the battery's refutation of the "
                     "fourth clause, which no rival can violate in isolation "
                     "(see the module docstring).",
        "witness": _overwrite_witness("true", "(some false)", "#[(8:Int)]",
                                      "#[(18:Int)]", "prepareInPlace #[(8:Int)] #[(18:Int)]",
                                      component="work"),
    },
    {
        "id": "weak-second-stage-drops-target",
        "kind": "uniqueness",
        "expect": "reject",
        # Both consumers run under the correctly resolved choice, but the second
        # is fed the BUFFER in place of the target vector. The only thing wrong is
        # the second argument, so this is the case that measures whether `target`
        # is genuinely constrained by the spec.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let copy := effectiveCopy configuredCopy requestedCopy\n"
            "    if copy then\n"
            "      return prepareInPlace data target\n"
            "    else\n"
            "      data := prepareInPlace data target\n"
            "      data := searchInPlace data data\n"
            "      return data",
        ),
        "refinement": "its faithful real patch resolves the choice correctly and "
                      "runs both numeric routines in place, but passes the feature "
                      "buffer where the second routine expects the target vector. "
                      "The second routine's decisions depend on that vector, so "
                      "the caller's buffer ends holding the result of a different "
                      "computation than the one the run is supposed to perform; a "
                      "leg that reads the buffer after a non-preserving run sees "
                      "the wrong contents and FAILS. It would NOT resolve.",
        "rationale": "REJECT from the OVERWRITE clause on the caller's buffer: at "
                     "configured True, requested some False the spec pins the "
                     "buffer to `searchInPlace (prepareInPlace dataOld target) target`, "
                     "and this rival delivers `searchInPlace (prepareInPlace "
                     "dataOld target) (prepareInPlace dataOld target)`. The hypothesis relates "
                     "two applications of one opaque consumer at different second "
                     "arguments — satisfiable, since the spec says nothing about "
                     "the consumer's values — so the consistency probe passes and "
                     "the refutation discharges by definitional unification. This "
                     "is the measurement that `target` is a CONSTRAINED input of "
                     "the modeled behaviour and not a carried-along field: with "
                     "the second argument unconstrained, this rival would verify.",
        "witness": _overwrite_witness(
            "true", "(some false)", "#[(9:Int)]", "#[(19:Int)]",
            "searchInPlace (prepareInPlace #[(9:Int)] #[(19:Int)]) (prepareInPlace #[(9:Int)] #[(19:Int)])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 5 cases (1 soundness
# positive, 1 admissibility, 3 uniqueness rivals; its AXIOM_TESTS lane is a
# separate G-AX concern). Every one is accounted for below. The carrier change
# (nagini defends a returned preference VALUE plus a second array-fate boolean;
# this bundle defends the frames of TWO observable buffers across TWO opaque
# in-place consumers as four implications) is what drives the re-siting and the
# one omission.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder          -> pos-control-negated-guard        PORTED
#   admissibility-f2p-shaped-self-call  -> admiss-f2p-frame-non-degenerate  RE-AIMED
#   partial-domain-false-routes-default -> weak-ignores-per-call            RE-SITED
#   frame-mutation-write-readonly-config-> (none)                           OMITTED (vacuous)
#   value-double-mask-array-always-intact-> weak-resolves-then-ignores      PORTED
#
# 2 ported, 1 re-aimed, 1 re-sited, 1 omitted = 5, accounting for 4 of the 15
# cases shipped here. The one omission is not for difficulty; the class is
# inexpressible on this carrier, per below.
#
# RE-AIMED (admissibility): the sibling establishes a precondition for a fresh
#   F2P-shaped input via a self-call. No method here has a `require` clause, so
#   that probe is vacuous — nothing could exclude a normal input. It is re-aimed
#   at the residual admissibility risk on a total domain: that the frame is
#   UNSATISFIABLE / degenerate at the interesting point. The case discharges an
#   in-region assert that the resolution demands overwrite at the newly-tested
#   input and preserve at the absent-choice input.
# RE-SITED (partial-domain): the sibling's "explicit False routes the
#   construction-time default" rival attacks the returned VALUE via its
#   value postcondition. Here that behaviour IS the buffer frame, so the argument
#   lands on the PRESERVE clause as weak-ignores-per-call (the frame decided by
#   the configured value alone). The ARGUMENT is unchanged; only the carrier is.
# OMITTED (1), because the class is VACUOUS on this carrier, not because it was
#   hard:
#   * frame-mutation-write-readonly-config — the sibling writes a read-only input
#     granted a half permission and is rejected by the permission system. Velvet
#     is referentially transparent; the only `mut` binder is `data` (legitimately
#     mutated on overwrite), the three read-only inputs carry no heap permission,
#     and there is no aliasing. No expressible instance; no substitute fabricated.
#     DEMONSTRATED rather than asserted: assigning any read-only binder in the
#     impl region does not produce a spec violation the gate could read, it
#     produces a FRONT-END error — "`configuredCopy` cannot be mutated, only
#     variables declared using `let mut` can be mutated" — which breaks the
#     variant AND the witness build against the rival, i.e. the half that must
#     succeed. There is no permission lattice here for a rival to violate; the
#     distinction is enforced by the binder syntax, so nothing is left to test.
# AXIOM_TESTS: dropped. The sibling's AXIOM lane (the A-reference deep model of
#   the real callee) belongs to G-AX; `prepareInPlace` and `searchInPlace` here
#   are those same G-AX-validated deep-model references, and this gate ignores
#   AXIOM_TESTS.
#
# ADDED (11, no sibling counterpart) — none for parity; each is demanded by the
#   coverage requirement. The frame is FOUR implications over TWO opaque consumers,
#   TWO observable buffers and three input binders, and a battery that attacked
#   one clause at one corner would attest nothing about the rest:
#     pos-control-inline-getd — a second soundness control: the resolution written
#         inline rather than through the named helper must still verify.
#     pos-control-composite-one-assignment — the soundness control on the
#         two-buffer clauses: a correct impl that writes the composite in ONE
#         assignment must still verify, else the clauses over-specify the
#         staging (SPEC-TOO-STRONG). Measured outside the gate: exit 0.
#     weak-delivers-complement    — resolution correct, frame inverted; refuted at
#         configured True (weak-ignores-per-call is refuted at False).
#     weak-absent-choice-hardcodes-overwrite — the fallthrough defect on the
#         absent-choice arm, the corner every explicit-request rival masks.
#     weak-overwrite-wrong-value  — the OVERWRITE clause's own attack: resolution
#         correct, but the non-preserving branch delivers the wrong buffer.
#     weak-absent-choice-hardcodes-preserve — the mirror of the fallthrough
#         defect, refuted at (configured False, none): the one input corner no
#         other rival reaches, and a second attack on the OVERWRITE clause.
#     weak-second-routine-ungated — THE RECORDED ATTACK, sharpened, and the
#         reason the `work` clauses exist. Refuted on the PRESERVE-`work` clause
#         at an input where the caller's-buffer clause is SATISFIED.
#     weak-second-stage-raw-per-call — the PER-CONSUMER DECOUPLING defect, on the
#         absent-choice arm of the PRESERVE-`work` clause.
#     weak-work-is-caller-buffer — the PER-BUFFER DECOUPLING defect: the first
#         consumer's output discarded on the preserve leg. Makes `prepareInPlace`
#         load-bearing inside the `work` clause.
#     weak-drops-second-stage — the single-consumer impl, i.e. the impl a
#         one-consumer spec accepts; refuted on the OVERWRITE-`work` clause,
#         which is that clause's only available refutation (see the docstring).
#     weak-second-stage-drops-target — the second consumer fed the buffer instead
#         of the target; refuted on the OVERWRITE-`data` clause. This is the case
#         that measures whether `target` is CONSTRAINED rather than carried.
#   Each is a real divergence from the frozen spec with a machine-checked witness.
#   None is fabricated wrongness. 4 accounted + 11 added = 15 cases.
#
# WITNESSABILITY (the load-bearing tooling fact — see WITNESS MECHANICS in the
#   module docstring). A witness preamble that runs `extract_program_for` OUTSIDE
#   a `noncomputable section` makes Lean attempt IR compilation of the emitted
#   `def`; against the frozen solution — whose impl names opaque axioms — that
#   compilation fails ("has no executable code"), in the PREAMBLE, before the
#   witness's claim is elaborated. Measured directly: the tautology
#   `example : (1:Nat) = 1 := by decide` under that preamble gives rival exit 0
#   and gold exit 1, so it would have been recorded as a refutation, and the
#   gold-side exit code would carry no information at all. Wrapping the extraction
#   in `noncomputable section … end` suppresses IR compilation while leaving
#   kernel reduction — what `decide` and definitional unification use —
#   untouched; under the wrapper the tautology probe PASSES on gold (exit 0),
#   which is the check that the gold-side exit code discriminates again, and a
#   forged "the rival is correct here" claim FAILS on the rival, the half that
#   must succeed.
#   The witness shapes are chosen by which side of the claim is concrete, not by
#   preference, and by WHICH COMPONENT of the extracted pair the attacked clause
#   is about. `decide` is used only where BOTH sides are concrete (the three
#   preserve-`data` rivals with a literal `data.push 0` overwrite). Every `work`
#   clause names `prepareInPlace` on the spec side, and every overwrite clause
#   names the composite, so `decide` would be stuck there — against the rival
#   itself in the `work` cases, against both sides in the overwrite cases; those
#   cases condition on one hypothesis about opaque terms and discharge by
#   definitional unification, which is what avoids a `witness-undecided` outcome.
#   Every such hypothesis is checked satisfiable by the gate's consistency probe.
#   The pair projections were verified against gold by `rfl` on both legs before
#   any witness was written, so no witness can be silently aimed at the wrong
#   component.
AXIOM_TESTS = []
