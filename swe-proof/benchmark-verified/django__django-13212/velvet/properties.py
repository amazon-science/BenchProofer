"""properties.py — G-PBT falsification battery for django__django-13212 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region — which the consumer spec view elides — and, for two of
the positives, the elided ``prove_correct checkValue`` tactic body, are changed,
so ``markers.same_spec`` holds and the ``prove_correct checkValue`` obligation
survives with a byte-identical ``method``/``require``/``ensures`` header) and
swaps in a candidate implementation, checked by the real verifier.
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method):

  checkValue (value code : List Char) (oldParams : List (String × List Char))
             (isValid : Bool)  return (out : Except Report Unit)
    require lookupKey "value" oldParams = none
    ensures out = checkOutcome isValid code oldParams value              [C1]
    ensures isValid = true  → out = Except.ok ()                         [C2]
    ensures isValid = false → out = Except.error (buildReport …)          [C3]
    ensures isValid = false → lookupKey "value" (buildReport …).params
                                = some value                            [C4]
    ensures (buildReport …).code = code                                  [C5]
    ensures ∀ k v, k ≠ "value" → lookupKey k oldParams = some v →
              lookupKey k (buildReport …).params = some v                [C6]

The operation screens one input and, when the screen does not pass, constructs
the rejection report the message layer will consult. ``isValid`` is the free
Boolean carrying the (unchanged) per-input screen; ``code`` is the report's
machine tag; ``oldParams`` are the named substitution bindings the report
already carries; ``value`` is the offending input as a message template would
stringify it. The desired behaviour: a passing input is accepted carrying no
report, and a failing input is rejected with a report that keeps its tag and
every pre-existing binding AND additionally binds the input itself under the
``"value"`` key, so a custom message can interpolate it.

WHICH CLAUSES ACTUALLY CONSTRAIN THE IMPL — and this is the load-bearing
observation for aiming the battery. Only C1/C2/C3 mention ``out``. C4/C5/C6 are
stated purely over ``buildReport code oldParams value``, a total ``def`` in the
frozen ``pure`` region, so they are properties of the SPEC's own report
constructor and hold identically for every candidate impl; no rival can violate
them and no rival is aimed at them. C1 is therefore the whole impl-constraining
surface, and it subsumes C2/C3: it pins ``out`` to ``checkOutcome isValid code
oldParams value`` at every input, i.e. it pins BOTH legs of the screen and, on
the failing leg, the report's tag, the preservation of every pre-existing
binding, the presence of the ``"value"`` key, its bound content, AND the absence
of anything else. Every uniqueness rival below diverges from ``checkOutcome`` at
a concrete input, and its witness refutes it there directly.

C1 IS GROUNDED, NOT AN ORACLE ECHO. ``checkOutcome`` / ``buildReport`` /
``lookupKey`` are transparent ``def``s over the method's own four inputs and the
``axioms`` region is EMPTY (mapping.md §3 — the unchanged per-input screen is
carried as the free Boolean ``isValid``, owed no contract, and there is no
module-level ``axiom`` and no opaque callee anywhere in the file). So pinning
``out = checkOutcome …`` is grounded in the arguments; there is no answer key a
wrong impl could echo to verify vacuously. Per the nagini sibling's own
UNGROUNDED-ORACLE note the echo probe is replaced by honest positive controls,
and the binding pins are attacked by wrong-content / dropped-key / spurious-key /
dropped-preservation rivals.

WITNESS MECHANICS ON THIS BUNDLE. The tester route is DEAD here: C6 quantifies
over ``∀ k : String`` (and ``∀ v : List Char``), so
``prove_postcondition_decidable_for checkValue`` cannot build a ``Decidable``
instance — measured, it leaves ``Decidable (∀ (k : String) (v : List Char), …)``
as an unsolved goal and the derived tester is noncomputable. But the carrier is
otherwise FULLY TRANSPARENT and finite-shaped at any concrete input: ``List
Char`` literals, an assoc-list literal, a ``Bool``. So each witness extracts the
executable program (``extract_program_for checkValue`` → ``checkValueExec``) and
refutes C1 directly at one concrete four-tuple:

    (match checkValueExec <value> <code> <oldParams> <isValid> with
     | DivM.res r => r | _ => Except.ok ())
        ≠ checkOutcome <isValid> <code> <oldParams> <value>

i.e. the rival's own output DIFFERS from what C1 demands. ``Report`` derives
``DecidableEq`` in the frozen file but the outcome carrier is ``Except Report
Unit``, so each witness first derives that instance (``deriving instance
DecidableEq for Except``) — an INSTANCE, not an assumption — and closes the
residual literal by ``decide``. Against the FROZEN solution the same statement is
provably FALSE (gold's ``checkValueExec`` reduces to exactly ``checkOutcome`` at
that input), so ``decide`` proves the ``≠`` false and the witness FAILS on gold —
the required discrimination. No witness binds a hypothesis (the carrier computes,
so no conditioning is needed and the gate's consistency probe is a no-op). No
banned token (sorry/admit/native_decide/axiom/opaque). Every witness below was
run out-of-band against BOTH its rival (ELABORATES, exit 0) and the frozen
solution (FAILS, exit 1) with two real ``scripts/lean_verify.sh`` builds, and
every gold-side failure is the SEMANTIC ``Tactic 'decide' proved that the
proposition … is false`` — never an unknown identifier, unfolding failure, type
error or timeout.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as
    MANDATORY and ships THREE such rivals (one per contracted function), because
    all of its list inputs are held at fractional permission and a rival that
    writes into one must be refused for insufficient permission. Lean and Velvet
    are referentially transparent: this method declares NO ``mut`` binder, every
    input is an immutable value, and there is no heap, no aliasing and no
    permission system — so there is no read-only input to overwrite and no
    substitute probe. Not fabricated, per the porting map.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface. Each
    nagini binding rival re-expresses onto one sub-behaviour C1 pins; see the
    footer map.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack (see above); replaced by the
    honest positive controls.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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

INDEPENDENT AUDIT OF THIS PORT (all figures below are real
``scripts/lean_verify.sh`` exit codes, re-run out-of-band, not the port's
self-report):

  * All 12 reject witnesses were rebuilt TWICE — against the rival (all exit 0)
    and against the frozen solution (all exit 1, every one carrying the SEMANTIC
    ``Tactic `decide` proved that the proposition … is false``; none stuck, none
    an unknown identifier, none a timeout). No witness binds a hypothesis, so the
    gate's consistency probe is a no-op on all of them.
  * Every obligation header and every byte outside the two elided regions is
    IDENTICAL to the frozen file across all cases (checked by hashing the
    ``method … do`` header and the whole file minus the impl body and the
    ``prove_correct`` body). No case reformats a statement.
  * No rival is vacuous: each differs observably from ``checkOutcome`` on a
    96-point input sweep, and each one's OWN witness point is a divergence point.
  * The dead-tester claim was re-measured: ``prove_postcondition_decidable_for
    checkValue`` leaves FOUR unsolved ``Decidable`` goals, and the C6 one is over
    ``∀ (k : String) (v : List Char)`` as documented. The route really is dead.
  * SPEC-TOO-WEAK probe (six new wrong impls the battery does not contain, none
    of which verified): accept-when-the-input-is-empty; the new binding PREPENDED
    instead of appended; the binding appended TWICE; the binding dropped only
    when the tag is empty; the binding dropped only on two-entry binding lists;
    ``code`` and ``value`` swapped in the post-image. All exit 1. Two more
    repaired defects are recorded below.
  * SPEC-TOO-STRONG probe (four new correct reshapes, all of which verified,
    exit 0): the report built through the structure's own constructor applied to
    a let-bound binding list; the report let-bound before the dispatch; the
    screen dispatched by ``match`` on the Bool instead of ``if``; and a variant
    that additionally dispatches on the precondition's own lookup. C1 is not
    over-fit to the frozen impl's shape.
  * ORDER is genuinely pinned, and that is CORRECT, not too strong. C1 fixes the
    binding list up to order, so the PREPENDING rival above is rejected even
    though — given the ``require`` — prepending is indistinguishable from
    appending to every ``lookupKey`` query. Both halves of that were machine-
    checked here (``lookupKey k (old ++ [(k',v)]) = lookupKey k old`` for
    ``k ≠ k'``, and ``lookupKey k' (old ++ [(k',v)]) = lookupKey k' ((k',v)::old)``
    under the require). It is still right to reject: the modeled carrier is an
    ORDERED binding list standing for an insertion-ordered mapping, mapping.md §2
    pins the order (``'value'`` appended last), and closure — which a real
    near-miss violates — is only statable against a fixed shape. Recorded because
    a future reader will hit this and should not weaken C1 over it.

TWO DEFECTS THIS AUDIT FOUND AND REPAIRED, both in the port's PROSE/coverage
rather than in the frozen spec:

  1. The admissibility case's rationale claimed it would sense "a vacuously-False
     precondition". Measured false: with ``require False`` substituted, that case
     verifies (exit 0) and so does a bare ``return Except.ok ()`` (exit 0) — on
     this carrier a false require discharges every clause vacuously, so NO
     expect="verify" case can attest to it. The claim is retracted at the case and
     replaced with what the case does demonstrate, which was also measured in both
     directions: narrowing the require FAILS it (exit 1) and widening it to
     ``require True`` FAILS it (exit 1).
  2. The nagini ``weak-decimal-finite-spurious-key`` rival was recorded as
     "merged" into the unconditional ``weak-spurious-extra-binding``. That merge
     discarded the sibling case's actual content — closure violated on ONE branch
     only, which is exactly what a sub-domain-guarded closure clause admits — and
     left the closure sub-behaviour probed at ``oldParams = []`` and nowhere else.
     The missing rival was written, and it does NOT verify (exit 1); its witness
     elaborates against it (exit 0) and is refuted on gold semantically (exit 1).
     It ships as ``weak-spurious-extra-binding-when-parameterised``.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini sibling's own note is that
it has no ``@ContractOnly`` axioms either (its ``meta.axioms == []``); this
bundle likewise declares no ``axiom`` (mapping.md §3), and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13212"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the consumer spec view elides (the
# `let result … return result` expression strictly between the method's
# `-- impl-start` / `-- impl-end`, or the `prove_correct` tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the `prove_correct checkValue`
# obligation header byte-identical.
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    let result : Except Report Unit :=\n"
    "      if isValid then Except.ok ()\n"
    "      else Except.error (buildReport code oldParams value)\n"
    "    return result"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# The frozen proof, verbatim. Reject rivals KEEP it unchanged — their rejection is
# carried by the witness, not by whether the frozen tactic happens to break on the
# reshape. Two positives retune only THIS elided tactic body (the
# `method`/`require`/`ensures` obligation header is untouched, so same_spec holds
# and the obligation survives byte-identically), because their reshaped impl no
# longer presents `simp_all` with a `buildReport`-shaped residual goal.
_GOLD_PROOF = (
    "prove_correct checkValue by\n"
    "  loom_solve <;>\n"
    "    simp_all [buildReport, lookupKey_append_fresh, lookupKey_append_pres]"
)

assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof region drifted; update _GOLD_PROOF"

# The retune actually needed by the two reshapes that spell the report out
# field-by-field instead of naming `buildReport`: add `checkOutcome` to the same
# simp set, so the residual goal is reconciled at the outcome level too. No new
# lemma, no new axiom, no `sorry` — the same tactic with one more frozen `def`
# unfolded. Verified to close for each reshape with a real build.
_PROOF_RETUNED = (
    "prove_correct checkValue by\n"
    "  loom_solve <;>\n"
    "    simp_all [buildReport, checkOutcome, lookupKey_append_fresh,\n"
    "      lookupKey_append_pres]"
)


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body):
    """Impl body replaced AND the (elided) prove_correct tactic body retuned."""
    return _swap(_impl(body), _GOLD_PROOF, _PROOF_RETUNED)


def _outcome(expr):
    """Impl body that computes the outcome from `expr` (a full if/match ladder)."""
    return ("    let result : Except Report Unit :=\n" + expr + "\n    return result")


def _report(params, code="code"):
    """The frozen two-leg dispatch with the FAILING leg's report reshaped: accept a
    passing input, and on a failing one build a report with `code` and `params`."""
    return _outcome(
        "      if isValid then Except.ok ()\n"
        f"      else Except.error {{ code := {code}, params := {params} }}")


# ---- witness builder. The tester route is dead (C6 quantifies over
# ---- `∀ k : String`, so `prove_postcondition_decidable_for` cannot build a
# ---- Decidable instance). Instead extract the executable program and refute C1
# ---- directly against the TRANSPARENT `checkOutcome` at one concrete four-tuple.
# ---- `deriving instance DecidableEq for Except` supplies the outcome carrier's
# ---- equality — an instance the elaborator constructs, not an assumption; the
# ---- frozen file already derives `DecidableEq` for `Report`. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. Binds nothing (every input is a literal), so the gate's
# ---- consistency probe is a no-op.
def _witness(value, code, old_params, is_valid):
    args = f"{value} {code} {old_params} {is_valid}"
    return (
        "deriving instance DecidableEq for Except\n\n"
        "extract_program_for checkValue\n\n"
        "example :\n"
        f"    (match checkValueExec {args} with\n"
        "     | DivM.res r => r | _ => Except.ok ())\n"
        f"    ≠ checkOutcome {is_valid} {code} {old_params} {value} := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else C1 is SPEC-TOO-STRONG (the postcondition would be
    # rejecting an equivalent correct construction). Each keeps the obligation
    # header byte-identical; only the elided impl (and, for the third, the elided
    # tactic body) is reshaped. All three verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-direct-outcome",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST impl: report the transparent post-image directly,
        # with no inline dispatch of its own. Ports the nagini pos-decimal-inline /
        # direct-control shape (an equivalent correct construction that does not
        # spell the branch out) and, because `checkOutcome` is GROUNDED in the four
        # arguments rather than an opaque answer key, it doubles as evidence that
        # C1 is not echo-vulnerable: any wrong leg, tag, key or binding fails the
        # equality. The inline `if` is gone, so the residual goal is `rfl`-shaped
        # and the FROZEN tactic body closes it unchanged.
        "module": _impl(_outcome(
            "      checkOutcome isValid code oldParams value")),
        "rationale": "the post-image `checkOutcome isValid code oldParams value` "
                     "is GROUNDED in the method's own four inputs (transparent "
                     "`def`s, empty axioms region, no opaque callee), so reporting "
                     "it directly is the honest cheapest CORRECT impl. C1 is "
                     "literally that equality, so it MUST verify — else C1 is "
                     "SPEC-TOO-STRONG. Also shows C1 is not echo-vulnerable: there "
                     "is no answer key here to echo, and any wrong leg/tag/binding "
                     "would fail the equality. Frozen proof unchanged.",
    },
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the screen NEGATED and put the rejection leg first. The two
        # legs are exhaustive and disjoint on a `Bool`, so the computed outcome is
        # identical at every input; C1/C2/C3 all still discharge under the frozen
        # tactic body with no retune. Ports the nagini pos-invalid-local-reshape /
        # pos-limit-reorder argument (a statement/branch reorder, not a
        # fold-direction flip, so no new lemma is needed).
        "module": _impl(_outcome(
            "      if !isValid then Except.error (buildReport code oldParams value)\n"
            "      else Except.ok ()")),
        "rationale": "structurally different CORRECT reshape: the screen is tested "
                     "negated and the rejection leg is emitted first. The two legs "
                     "are exhaustive and disjoint on a `Bool`, so the outcome is "
                     "identical at every input and C1/C2/C3 still hold. A faithful "
                     "correct reshape MUST verify, else C1 is over-fit to the guard "
                     "POLARITY / leg order => SPEC-TOO-STRONG. Frozen proof "
                     "unchanged.",
    },
    {
        "id": "pos-inline-report",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the failing leg's report INLINE, field by field, instead of
        # naming the spec's report constructor — the same tag and the same binding
        # list appended in the same place, spelled out. This is the velvet analogue
        # of the nagini pos-decimal-inline case (construct the map inline instead of
        # delegating). Naming `buildReport` is gone from the impl, so the frozen
        # `simp_all` no longer sees a `buildReport`-shaped residual goal; the elided
        # tactic body is retuned by adding the frozen `checkOutcome` def to the SAME
        # simp set (no new lemma, no new axiom, no `sorry`), and the obligation
        # header is byte-identical.
        "module": _impl_reproved(_report('oldParams ++ [("value", value)]')),
        "rationale": "structurally different CORRECT impl: the failing leg's report "
                     "is constructed INLINE field-by-field (same tag, same binding "
                     "appended in the same position) rather than by naming the "
                     "spec's constructor. Identical outcome at every input, so C1 "
                     "still holds; MUST verify, else C1 is over-fit to the SYNTACTIC "
                     "use of the constructor => SPEC-TOO-STRONG. Ports the nagini "
                     "pos-decimal-inline (build the map inline instead of "
                     "delegating). The elided tactic body is retuned with one more "
                     "FROZEN def in the same simp set; the obligation statement is "
                     "untouched.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-invalid-input case. That case
    # asserted the read-only input is still readable under the retained half
    # permission AND that the postcondition is non-vacuously establishable on an
    # in-domain input. The permission half has no counterpart here (referential
    # transparency), but this method DOES carry a real `require`, so the other half
    # ports directly and sharpens: the impl READS the precondition and dispatches
    # on it, so the case verifies only if `require lookupKey "value" oldParams =
    # none` genuinely admits the in-domain inputs (a vacuously-False precondition,
    # or one excluding the ordinary bare-report shape, would show up here).
    # =====================================================================
    {
        "id": "admiss-precondition-admits",
        "kind": "admissibility",
        "expect": "verify",
        # Deliberately NOT the frozen impl (resubmitting `_BASE` would re-run the
        # gold build and attest nothing this manifest is responsible for). It
        # CONSUMES the precondition — matching on `lookupKey "value" oldParams` and
        # taking the accept leg in the `some` case, which the `require` excludes —
        # and independently RECONSTRUCTS the report from its own fields on the
        # rejection leg, so the post-image is discharged with `isValid` split at
        # {true, false} under a precondition the impl has actually inspected.
        #
        # WHAT THIS CASE DOES AND DOES NOT ATTEST — measured, not argued. It is a
        # genuine NON-VACUITY probe of the require in the direction that the
        # require is not too NARROW: its `some` leg is observably wrong at
        # `oldParams = [(\"value\", ['q'])]` (checked: `decide` closes the `≠`
        # against `checkOutcome` there), so the case can only verify because the
        # require excludes that shape and admits the ordinary bare/parameterised
        # ones. Narrowing the require to `… ∧ oldParams = []` makes this case FAIL
        # (measured, exit 1 on clauses C4/C6), and widening it to `require True`
        # also makes it FAIL (measured, exit 1 on C1/C3/C4) — so the case is
        # genuinely sensitive to the precondition's content in both directions.
        #
        # It is NOT a probe for a vacuously-FALSE precondition: `require False`
        # verifies for this impl AND for `Except.ok ()` alike (both measured, exit
        # 0), because on this carrier a false require discharges every clause
        # vacuously and no expect="verify" case can sense that. Sensing a false
        # require needs a reject case, and no witness exists for a rival the spec
        # SATISFIES — the same structural reason the divergence hole ships nothing.
        # G-HYGIENE/G-DIFF hold that line instead (the frozen require is a literal
        # `lookupKey … = none`, and Solution_prepatch must FAIL, which a vacuous
        # require would prevent). Recorded so this case is not read as covering it.
        "module": _impl_reproved(_outcome(
            "      match lookupKey \"value\" oldParams with\n"
            "      | some _ => Except.ok ()\n"
            "      | none   =>\n"
            "        match isValid with\n"
            "        | true  => Except.ok ()\n"
            "        | false => Except.error { code := (buildReport code oldParams value).code,\n"
            "                                  params := (buildReport code oldParams value).params }")),
        "rationale": "admissibility: the impl CONSUMES `require lookupKey \"value\" "
                     "oldParams = none` (it dispatches on that very lookup and takes "
                     "the accept leg in the `some` case the precondition excludes) "
                     "and independently rebuilds the report from its fields on the "
                     "rejection leg. It therefore verifies only if the precondition "
                     "genuinely ADMITS the in-domain inputs — the ordinary "
                     "no-pre-existing-`value`-binding reports, which every modeled "
                     "site has — and the post-image is jointly SATISFIABLE there "
                     "with `isValid` split at both values. Its `some` leg is "
                     "observably WRONG (refuted by `decide` at `oldParams = "
                     "[(\"value\", ['q'])]`), so verification is attributable to the "
                     "require's content, not to a leg that happens to be right "
                     "anyway: measured, NARROWING the require (`… ∧ oldParams = []`) "
                     "fails it and WIDENING it (`require True`) fails it too. "
                     "Re-aimed from the nagini admiss-invalid-input (whose "
                     "half-permission-readability half has no counterpart on this "
                     "referentially-transparent carrier). Else PRECOND-TOO-STRONG. "
                     "It does NOT sense a vacuously-FALSE precondition — see the "
                     "comment above: `require False` verifies for ANY impl on this "
                     "carrier, so no expect=\"verify\" case can attest to that, and "
                     "the claim is not made here.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests. Every rival is aimed at C1,
    # the only impl-constraining clause; each names the sub-behaviour of C1 it
    # breaks. Witness points vary all four binders — see the footer.
    # =====================================================================

    # ---- the value binding is absent entirely (the pre-change behaviour) ----
    {
        "id": "weak-omits-value-binding",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact PRE-CHANGE behaviour, and the discriminating one: the rejection
        # report carries its tag and whatever bindings it already had, but the
        # offending input is never bound under the templating key. This is the dual
        # of Solution_prepatch.lean at the PBT layer.
        "module": _impl(_report("oldParams")),
        "refinement": "this is the unchanged pre-change construction: the rejection "
                      "report never binds the offending input under the templating "
                      "key. Its faithful real counterpart is the unpatched "
                      "behaviour, where a custom message written against that "
                      "placeholder has nothing to interpolate — the failing tests "
                      "assert the rendered message is exactly the submitted input, "
                      "which an unbound placeholder cannot produce (the render "
                      "raises on the missing key rather than yielding the input), so "
                      "it does NOT resolve. This is precisely the behaviour the fix "
                      "introduces.",
        "rationale": "REJECT from C1 (`out = checkOutcome isValid code oldParams "
                     "value`), the value-PRESENCE sub-behaviour: on a failing screen "
                     "the impl's report omits the `\"value\"` binding the post-image "
                     "requires. Refuted at `(value=['a'], code=['i','n','v'], "
                     "oldParams=[], isValid=false)` — a bare report with no "
                     "pre-existing binding, the shape twelve of the modeled sites "
                     "have. If it verified => SPEC-TOO-WEAK (the spec would admit "
                     "the pre-change behaviour).",
        "witness": _witness("['a']", "['i', 'n', 'v']", "[]", "false"),
    },
    {
        "id": "weak-omits-value-only-when-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # The NEAR-MISS of the rival above: it binds the offending input correctly
        # whenever the report already carries bindings, and omits it ONLY on the bare
        # reports. So it agrees with gold across the whole non-empty-oldParams
        # sub-domain that the preservation rivals probe, and is wrong exactly where
        # most of the modeled sites live.
        "module": _impl(_report(
            "(match oldParams with\n"
            "                                   | [] => oldParams\n"
            "                                   | _  => oldParams ++ [(\"value\", value)])")),
        "refinement": "binds the offending input only on reports that ALREADY carry "
                      "bindings, and omits it on the bare ones. A faithful real "
                      "counterpart would add the placeholder binding at the handful "
                      "of sites that already publish parameters and skip the bare "
                      "sites — the majority of them — so a custom message written "
                      "against the placeholder still has nothing to interpolate at "
                      "those sites. The failing tests drive precisely those bare "
                      "screens (a malformed address, a malformed network address, a "
                      "pattern mismatch, a forbidden control character), so it does "
                      "NOT resolve.",
        "rationale": "REJECT from C1, the value-PRESENCE sub-behaviour, on a NARROW "
                     "sub-domain: the impl agrees with the post-image at every input "
                     "whose report already carries bindings and diverges only on the "
                     "bare ones. Refuted at `(value=['e','f','g'], code=['x'], "
                     "oldParams=[], isValid=false)` — the only sub-domain where it is "
                     "wrong, at a third distinct `value` (length 3) and a distinct "
                     "`code`. Its distinctness from weak-omits-value-binding is the "
                     "point: that rival is wrong everywhere, this one only here, so "
                     "C1 is shown to pin the binding at the bare sites specifically. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['e', 'f', 'g']", "['x']", "[]", "false"),
    },
    {
        "id": "weak-omits-value-unless-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual sub-domain: binds the input on the bare reports and DROPS it on
        # the ones that already carry bindings — the shape a patch would have if it
        # only touched the simple raise sites and left the parameterised ones alone.
        "module": _impl(_report(
            "(match oldParams with\n"
            "                                   | [] => oldParams ++ [(\"value\", value)]\n"
            "                                   | _  => oldParams)")),
        "refinement": "the dual: binds the offending input on the bare reports and "
                      "drops it on the ones that already publish parameters. A "
                      "faithful real counterpart would leave the parameterised sites "
                      "untouched — the magnitude screens and the file-suffix screen — "
                      "so a custom message written against the placeholder has "
                      "nothing to interpolate there. The failing tests exercise "
                      "exactly those sites (the fixed-precision magnitude cases and "
                      "the uploaded-file suffix case), so it does NOT resolve.",
        "rationale": "REJECT from C1, the value-PRESENCE sub-behaviour, on the "
                     "COMPLEMENTARY sub-domain to weak-omits-value-only-when-bare: "
                     "wrong exactly where the report already carries bindings. "
                     "Refuted at `(value=['d'], code=['m','d'], "
                     "oldParams=[(\"max\",['9']),(\"ext\",['t'])], isValid=false)` — a "
                     "TWO-entry pre-existing binding list, the widest `oldParams` any "
                     "witness probes, and a point where the previous rival coincides "
                     "with gold. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['d']", "['m', 'd']",
                            "[(\"max\", ['9']), (\"ext\", ['t'])]", "false"),
    },

    # ---- the pre-existing bindings are not preserved ----
    {
        "id": "weak-drops-existing-bindings",
        "kind": "uniqueness",
        "expect": "reject",
        # REPLACES the report's bindings with just the value binding instead of
        # APPENDING to them — the dual of the desired change. Ports the nagini
        # weak-limit-drop-max rival.
        "module": _impl(_report('[("value", value)]')),
        "refinement": "replaces the report's bindings with the new one instead of "
                      "appending to them, so every parameter the report already "
                      "published is lost. A faithful real counterpart would drop the "
                      "bound-magnitude parameter from the fixed-precision screens and "
                      "the suffix parameters from the file screen, which the "
                      "UNCHANGED default messages for those screens interpolate — "
                      "rendering them then raises on the missing key, so the "
                      "previously-passing behaviour those messages back regresses and "
                      "the patch does NOT resolve. The desired change ADDS a binding; "
                      "it does not replace the set.",
        "rationale": "REJECT from C1, the PRESERVATION sub-behaviour: the post-image "
                     "keeps `oldParams` as a prefix, and the impl discards it. "
                     "Refuted at `(value=['b','c'], code=['m','d'], "
                     "oldParams=[(\"max\",['2'])], isValid=false)` — a report that "
                     "already carries a binding, so the loss is observable. Ports the "
                     "nagini weak-limit-drop-max (the pre-existing binding dropped "
                     "rather than preserved). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['b', 'c']", "['m', 'd']", "[(\"max\", ['2'])]", "false"),
    },

    # ---- the value key is bound to the WRONG content ----
    {
        "id": "weak-binds-empty-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Binds the templating key to the EMPTY string instead of the offending
        # input. Presence and preservation both hold; only the CONTENT is wrong.
        # Ports the nagini weak-invalid-empty-binding / weak-decimal-empty-binding.
        "module": _impl(_report('oldParams ++ [("value", [])]')),
        "refinement": "binds the templating key to the EMPTY string instead of the "
                      "offending input. A faithful real counterpart would render a "
                      "custom message written against that placeholder as the empty "
                      "string; the failing tests assert the rendered message equals "
                      "the ACTUAL submitted input (every one of their inputs is "
                      "non-empty), so it does NOT resolve.",
        "rationale": "REJECT from C1, the value-CONTENT sub-behaviour: the key is "
                     "present and the pre-existing bindings are preserved, but the "
                     "bound content is the empty sequence rather than `value`. "
                     "Refuted at `(value=['h','i'], code=['n'], "
                     "oldParams=[(\"max\",['1'])], isValid=false)` — a non-empty input, "
                     "which is where empty and correct diverge. Ports the nagini "
                     "weak-invalid-empty-binding / weak-decimal-empty-binding. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness("['h', 'i']", "['n']", "[(\"max\", ['1'])]", "false"),
    },
    {
        "id": "weak-binds-existing-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Binds the templating key to a PRE-EXISTING binding's rendered text instead
        # of the offending input — the velvet re-expression of the nagini
        # weak-limit-value-renders-limit rival. A NEAR-MISS: on a bare report there
        # is no other text to reach for, so it falls back to the input and coincides
        # with gold; it is wrong exactly where the report already carries a binding.
        "module": _impl(_report(
            "oldParams ++ [(\"value\",\n"
            "                                   (match oldParams with\n"
            "                                    | []          => value\n"
            "                                    | (_, w) :: _ => w))]")),
        "refinement": "binds the templating key to a parameter the report ALREADY "
                      "published rather than to the offending input. A faithful real "
                      "counterpart would make a custom message written against the "
                      "placeholder render the bound magnitude (e.g. the configured "
                      "digit limit) instead of the rejected input; the failing test "
                      "for the fixed-precision field asserts the rendered message is "
                      "the submitted input, so it does NOT resolve.",
        "rationale": "REJECT from C1, the value-CONTENT sub-behaviour, on a NARROW "
                     "sub-domain: the key is present, the pre-existing bindings are "
                     "preserved, and on a BARE report it falls back to the input and "
                     "COINCIDES with gold — it is wrong only where the report already "
                     "carries a binding whose text differs from the input. Refuted at "
                     "`(value=['s','t'], code=['m','d'], oldParams=[(\"max\",['7'])], "
                     "isValid=false)`, a fifth distinct pre-existing binding. "
                     "Re-expresses the nagini weak-limit-value-renders-limit (the "
                     "value placeholder rendering the bound limit). If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness("['s', 't']", "['m', 'd']", "[(\"max\", ['7'])]", "false"),
    },
    {
        "id": "weak-binds-perturbed-content",
        "kind": "uniqueness",
        "expect": "reject",
        # The SHARPEST content rival: binds a value DERIVED from the input (reversed)
        # rather than the input itself. Presence, preservation, tag and key are all
        # correct, and it even coincides with gold on every palindromic input — so it
        # tests that C1 pins the bound content EXACTLY, not merely that something
        # input-shaped was bound.
        "module": _impl(_report('oldParams ++ [("value", value.reverse)]')),
        "refinement": "binds a value DERIVED from the offending input rather than the "
                      "input itself. A faithful real counterpart would render a "
                      "custom message written against the placeholder as a mangled "
                      "form of the submitted input; the failing tests compare the "
                      "rendered message to the input verbatim, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from C1, the value-CONTENT sub-behaviour, at the "
                     "SHARPEST grain: presence, preservation, tag and key are all "
                     "correct and only the bound content is perturbed — and it "
                     "coincides with gold on every single-character and palindromic "
                     "input, so no coarser probe would sense it. Refuted at "
                     "`(value=['t','u'], code=['v'], oldParams=[], isValid=false)` — a "
                     "non-palindromic input, the sub-domain where a derived binding "
                     "diverges from the input. If it verified => SPEC-TOO-WEAK (the "
                     "bound content would be unpinned, only its presence pinned).",
        "witness": _witness("['t', 'u']", "['v']", "[]", "false"),
    },

    # ---- the binding is published under the WRONG key ----
    {
        "id": "weak-binds-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Publishes the offending input under a near-miss key, so the templating
        # lookup for the intended placeholder still finds nothing. Presence of A
        # binding is not presence of THE binding.
        "module": _impl(_report('oldParams ++ [("valu", value)]')),
        "refinement": "publishes the offending input under a different (near-miss) "
                      "name. A faithful real counterpart would add a parameter the "
                      "message layer never consults for the documented placeholder, "
                      "so a custom message written against that placeholder still has "
                      "nothing to interpolate and the render raises on the missing "
                      "key — the failing tests assert the rendered message equals the "
                      "submitted input, so it does NOT resolve. The placeholder name "
                      "is part of the published interface, not an internal detail.",
        "rationale": "REJECT from C1, the KEY-IDENTITY sub-behaviour: the impl "
                     "appends a binding carrying the right content under the wrong "
                     "name, so the post-image's report differs and the intended "
                     "lookup would still miss. Refuted at `(value=['m'], code=['q'], "
                     "oldParams=[(\"max\",['3'])], isValid=false)`. If it verified => "
                     "SPEC-TOO-WEAK (the spec would pin only that SOME binding was "
                     "added, not which).",
        "witness": _witness("['m']", "['q']", "[(\"max\", ['3'])]", "false"),
    },

    # ---- a SPURIOUS extra binding (the closure sub-behaviour) ----
    {
        "id": "weak-spurious-extra-binding",
        "kind": "uniqueness",
        "expect": "reject",
        # Adds the correct binding AND a spurious extra one. Presence, content,
        # preservation, key and tag are all correct; only the CLOSURE ("nothing
        # else is added") is violated. Ports the nagini weak-invalid-spurious-key /
        # weak-decimal-finite-spurious-key rivals.
        "module": _impl(_report(
            'oldParams ++ [("value", value), ("max", value)]')),
        "refinement": "adds the correct binding AND a spurious extra parameter on "
                      "top of it. A faithful real counterpart would inject a stray "
                      "parameter into EVERY rejection report — including the many "
                      "screens whose messages never mention it — so the reports the "
                      "patch produces differ from the intended ones at every site. "
                      "The artifact is then not the intended change and is not "
                      "guaranteed to resolve: any consumer or default message that "
                      "does not expect the stray key now carries it, and the "
                      "published parameter set at each site no longer matches.",
        "rationale": "REJECT from C1, the CLOSURE sub-behaviour: the post-image is "
                     "`oldParams` followed by EXACTLY the one new binding, and the "
                     "impl appends a second. Every other sub-behaviour (presence, "
                     "content, key, preservation, tag, leg) is correct, isolating the "
                     "rejection to closure. Refuted at `(value=['w'], code=['y'], "
                     "oldParams=[], isValid=false)`. Ports the nagini "
                     "weak-invalid-spurious-key / weak-decimal-finite-spurious-key. "
                     "If it verified => SPEC-TOO-WEAK (a report could smuggle in "
                     "arbitrary extra parameters).",
        "witness": _witness("['w']", "['y']", "[]", "false"),
    },
    {
        "id": "weak-spurious-extra-binding-when-parameterised",
        "kind": "uniqueness",
        "expect": "reject",
        # The NEAR-MISS of the rival above, and the case the nagini merge dropped.
        # weak-spurious-extra-binding smuggles the stray parameter in at EVERY
        # input, so it is refuted by the bare-report point and says nothing about
        # whether C1's closure holds SEPARATELY on the two `oldParams`
        # sub-domains. This one is correct on the bare reports and smuggles the
        # stray binding in ONLY where the report already carries parameters —
        # exactly the shape the nagini weak-decimal-finite-spurious-key had
        # (closure violated on one branch only), whose whole point in the sibling
        # was that a GUARDED closure clause admitted it. The merge into the
        # unconditional rival lost that; the two now sit side by side, and
        # `oldParams` becomes a binder the CLOSURE sub-behaviour is probed at on
        # both sides rather than only at `[]`.
        "module": _impl(_report(
            "(match oldParams with\n"
            "                                   | [] => oldParams ++ [(\"value\", value)]\n"
            "                                   | _  => oldParams ++ [(\"value\", value),\n"
            "                                                         (\"max\", value)])")),
        "refinement": "adds the stray extra parameter ONLY to the rejection "
                      "reports that already publish parameters, and is exactly "
                      "right on the bare ones. A faithful real counterpart would "
                      "leave the many bare screens untouched and inject a stray "
                      "binding at the handful of parameterised ones — the "
                      "magnitude screens and the file-suffix screen — silently "
                      "overwriting the parameter those screens' UNCHANGED default "
                      "messages interpolate, since the stray name collides with "
                      "one already published there and the appended entry changes "
                      "what a front-to-back template scan finds. The rendered "
                      "default text for those screens then reports the rejected "
                      "input where it should report the configured bound, so the "
                      "previously-passing behaviour those messages back regresses "
                      "and it does NOT resolve.",
        "rationale": "REJECT from C1, the CLOSURE sub-behaviour, on the NARROW "
                     "sub-domain the unconditional closure rival cannot reach: it "
                     "coincides with the post-image at every bare report (where "
                     "weak-spurious-extra-binding is refuted) and violates closure "
                     "only where `oldParams` is non-empty. Refuted at "
                     "`(value=['p'], code=['r'], oldParams=[(\"max\",['5'])], "
                     "isValid=false)`. This is the genuine port of the nagini "
                     "weak-decimal-finite-spurious-key's actual content — a "
                     "closure violated on ONE branch, which is precisely what a "
                     "sub-domain-guarded closure clause would have admitted — "
                     "rather than a merge into the unconditional rival, which "
                     "leaves the guarded shape unattacked. If it verified => "
                     "SPEC-TOO-WEAK (closure would be pinned only at the bare "
                     "reports).",
        "witness": _witness("['p']", "['r']", "[(\"max\", ['5'])]", "false"),
    },

    # ---- the report's machine tag ----
    {
        "id": "weak-drops-report-tag",
        "kind": "uniqueness",
        "expect": "reject",
        # Builds the binding list correctly but blanks the report's machine tag. The
        # tag is what selects which custom message applies, so losing it is not
        # cosmetic. This attacks the one sub-behaviour of C1 that C5 states only
        # over the spec's own constructor and therefore cannot police in the impl.
        "module": _impl(_report('oldParams ++ [("value", value)]', code="[]")),
        "refinement": "publishes the bindings correctly but blanks the rejection "
                      "report's machine tag. A faithful real counterpart would "
                      "produce rejections that no longer carry the tag the message "
                      "layer keys custom overrides on, so a message registered "
                      "against that tag is never selected and the default text "
                      "surfaces instead — the failing tests register their override "
                      "under the tag and assert the overridden text renders, so it "
                      "does NOT resolve. (The desired change also SETS this tag at "
                      "one screen that previously published none, so the tag is part "
                      "of the behaviour, not incidental.)",
        "rationale": "REJECT from C1, the TAG sub-behaviour: the post-image's report "
                     "carries `code`, and the impl emits a blank tag. Note C5 states "
                     "the tag property over the spec's own constructor only, so C1 is "
                     "the sole clause that can sense this in the IMPL — which is "
                     "exactly why the rival is here. Refuted at `(value=['n'], "
                     "code=['p','q'], oldParams=[], isValid=false)` — the only witness "
                     "with a two-character `code`, so that binder is genuinely varied "
                     "rather than held fixed. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['n']", "['p', 'q']", "[]", "false"),
    },

    # ---- the passing leg ----
    {
        "id": "weak-rejects-passing-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the failing leg — the report it builds is exactly right — but it
        # rejects unconditionally, ignoring the screen. This is the ONLY rival aimed
        # at the passing leg, and the only witness at `isValid = true`; without it
        # every probe would hold that binder fixed at `false` and a rival that
        # mishandled acceptance would go unnoticed.
        "module": _impl(_outcome(
            "      Except.error (buildReport code oldParams value)")),
        "refinement": "builds exactly the right report but emits it unconditionally, "
                      "ignoring the screen. A faithful real counterpart would reject "
                      "every input the screen accepts, so inputs that must validate "
                      "cleanly now surface an error — the previously-passing "
                      "behaviour across the whole validation surface regresses and it "
                      "does NOT resolve.",
        "rationale": "REJECT from C1 via C2's leg (`isValid = true → out = "
                     "Except.ok ()`): the post-image accepts when the screen passes "
                     "and the impl rejects. Refuted at `(value=['z'], "
                     "code=['a','b'], oldParams=[(\"max\",['4'])], isValid=TRUE)` — the "
                     "only witness in the battery at `isValid = true`, so this is what "
                     "keeps that binder from being pinned at one value across every "
                     "probe. If it verified => SPEC-TOO-WEAK (the spec would say "
                     "nothing about the accepting leg).",
        "witness": _witness("['z']", "['a', 'b']", "[(\"max\", ['4'])]", "true"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling ships 13 SPEC cases (3 soundness/admissibility positives,
# 3 MANDATORY frame-mutation rivals, 7 binding rivals) plus an empty AXIOM lane.
# It contracts THREE functions — build_invalid_params, build_limit_params,
# decimal_reject_params — over an integer-code-point carrier with fractional
# permissions. This velvet bundle contracts ONE method, `checkValue`, whose four
# inputs subsume all three nagini surfaces: the bare-report case is
# `oldParams = []`, the preserved-binding case is `oldParams ≠ []`, and the
# control-flow case (a candidate that used to be short-circuited by a duplicate
# screen and now reaches the value-binding rejection) is `isValid = false`, since
# the removal of that duplicate is precisely "this input reaches the modeled
# rejection branch". So the three nagini functions collapse into ONE obligation
# with `oldParams` and `isValid` as the discriminating binders — carrier
# narrowing, and the reason 13 nagini cases land as 15 here without any
# fabrication: each nagini rival re-expresses onto a sub-behaviour of C1, and the
# sub-domain structure `oldParams ∈ {[], non-empty}` splits two of them in two.
#
#   nagini case                        -> here                            status
#   ------------------------------------------------------------------------------
#   pos-invalid-local-reshape          -> pos-negated-guard               RE-SHAPED
#   pos-limit-reorder                  -> pos-negated-guard (merged)      RE-SHAPED
#   pos-decimal-inline                 -> pos-inline-report               PORTED
#   (cheapest-honest control)          -> pos-direct-outcome              PORTED
#   admiss-invalid-input               -> admiss-precondition-admits      RE-AIMED
#   frame-mutate-value                 -> (none)                         VACUOUS
#   frame-mutate-limit                 -> (none)                         VACUOUS
#   frame-mutate-decimal-value         -> (none)                         VACUOUS
#   decimal-keeps-notfinite-screen     -> weak-omits-value-binding        RE-SITED
#   weak-invalid-empty-binding         -> weak-binds-empty-content        PORTED
#   weak-decimal-empty-binding         -> weak-binds-empty-content (merged)
#   weak-invalid-spurious-key          -> weak-spurious-extra-binding     PORTED
#   weak-decimal-finite-spurious-key   -> weak-spurious-extra-binding-
#                                           when-parameterised            PORTED
#   weak-limit-drop-max                -> weak-drops-existing-bindings    PORTED
#   weak-limit-value-renders-limit     -> weak-binds-existing-content     RE-EXPRESSED
#   AXIOM_TESTS (0)                    -> (none)                          N/A
#   (no nagini source)                 -> weak-omits-value-only-when-bare ADDED
#   (no nagini source)                 -> weak-omits-value-unless-bare    ADDED
#   (no nagini source)                 -> weak-binds-perturbed-content    ADDED
#   (no nagini source)                 -> weak-binds-wrong-key            ADDED
#   (no nagini source)                 -> weak-drops-report-tag           ADDED
#   (no nagini source)                 -> weak-rejects-passing-input      ADDED
#
# 16 velvet SPEC cases: 3 soundness, 1 admissibility, 12 uniqueness.
#
# PORTED / RE-EXPRESSED (5 rivals + 2 positives). Each nagini binding rival names
#   a postcondition pin (I1/I2/I3, L1..L5, D1/D2/D3) that is a sub-behaviour of the
#   single clause C1 here, so it re-expresses directly:
#     * decimal-keeps-notfinite-screen (D1 fails: a short-circuited candidate
#       yields a paramless report) -> weak-omits-value-binding. On this carrier the
#       duplicate screen's removal IS "the candidate reaches the modeled rejection
#       branch", i.e. `isValid = false`; the surviving wrongness the nagini rival
#       demonstrates is that the report then carries no value binding. Same
#       refinement argument, same discriminating failing test.
#     * weak-invalid-empty-binding / weak-decimal-empty-binding (I2 / D2) ->
#       weak-binds-empty-content. The two nagini rivals are the same wrongness at
#       one point on this carrier (the templating key bound to the empty string on
#       a failing screen), so they merge; splitting them would probe one clause
#       twice at the same reason.
#     * weak-invalid-spurious-key (I3) -> weak-spurious-extra-binding, the
#       unconditional closure violation.
#     * weak-decimal-finite-spurious-key (D3) ->
#       weak-spurious-extra-binding-when-parameterised, NOT merged into the
#       unconditional rival. The port originally merged the pair on the grounds
#       that they "differ only in which function's finite-branch was decorated";
#       the audit of this port measured that this discards the sibling case's
#       actual content. The nagini D3 rival violates closure on ONE BRANCH only,
#       and its stated purpose there is that a sub-domain-GUARDED closure clause
#       admitted exactly that shape (the sibling's own G-PANEL-1 weakness
#       witness). An unconditional spurious rival is refuted at the bare-report
#       point and therefore never asks whether closure is pinned on the
#       non-empty-`oldParams` sub-domain too. Both now ship.
#     * weak-limit-drop-max (L1/L2) -> weak-drops-existing-bindings, at
#       `oldParams ≠ []`.
#     * weak-limit-value-renders-limit (L4) -> weak-binds-existing-content, and
#       sharpened: on a bare report there is no other text to reach for, so the
#       velvet rival falls back to the input and COINCIDES with gold there, making
#       it a genuine near-miss rather than a wide rival.
#     * pos-invalid-local-reshape and pos-limit-reorder are both
#       "behaviour-preserving statement reshape, no new lemma needed"; with one
#       method they merge into pos-negated-guard (guard polarity + leg order).
#       pos-decimal-inline -> pos-inline-report (construct the report inline
#       instead of naming the spec's constructor).
# RE-AIMED (admiss-invalid-input -> admiss-precondition-admits): the nagini case
#   had two halves — the half-permission input is still readable, and the
#   postcondition is non-vacuously establishable on an in-domain input. The first
#   half is vacuous here (referential transparency, no permissions). The second
#   ports and SHARPENS, because unlike most bundles this method carries a real
#   `require`: the admissibility impl consumes it, so the case verifies only if
#   the precondition genuinely admits the ordinary bare-report inputs. The witness
#   is deliberately NOT the frozen impl (resubmitting gold attests nothing).
# ADDED (6, by the adversarial audit of this port — no nagini counterpart; each
#   closes a gap the ported rivals left, and each was measured with real builds):
#   * weak-omits-value-only-when-bare / weak-omits-value-unless-bare. The ported
#     presence rival is wrong at EVERY input. Nothing tested whether C1 pins the
#     binding SEPARATELY on the two `oldParams` sub-domains, so a patch that
#     covered only the parameterised sites (or only the bare ones) was unattacked.
#     These are the two complementary near-misses, and they are what make
#     `oldParams` a genuinely exercised binder rather than incidental scenery.
#   * weak-binds-perturbed-content. The two content rivals bind the empty string
#     or another parameter's text; nothing pinned the content EXACTLY. A binding
#     derived from the input (reversed) honours presence, key, preservation and tag
#     and coincides with gold on every palindromic input, so it is the sharpest
#     content probe.
#   * weak-binds-wrong-key. Presence of A binding is not presence of THE binding;
#     no ported rival varied the key while keeping the content right.
#   * weak-drops-report-tag. C5 states the tag property over the spec's own
#     constructor and so cannot police the impl; C1 is the only clause that can,
#     and nothing was aimed at it. Also the only witness with a multi-character
#     `code`.
#   * weak-rejects-passing-input. Every other rival probes `isValid = false`. With
#     no rival on the accepting leg, `isValid` would be a binder held at one value
#     by every witness — exactly the measured failure mode this port is warned
#     about — and a rival mishandling acceptance would verify unnoticed.
# VACUOUS (3, the whole nagini frame lane — NOT dropped for difficulty): the
#   sibling marks frame mutation MANDATORY and ships one rival per function,
#   because each list input is held at fractional permission and a write needs
#   full permission. This backend is referentially transparent: `checkValue`
#   declares NO `mut` binder, all four inputs are immutable values, and there is
#   no heap, no aliasing and no permission system — so there is no read-only input
#   to overwrite and no substitute probe exists. Not fabricated, per the porting
#   map.
# AXIOM lane: N/A both sides. The nagini file ships `AXIOM_TESTS = []` (its
#   meta.axioms == []) and this bundle declares no `axiom` either (mapping.md §3:
#   the unchanged per-input screen is a free Boolean, owed no contract). The gate
#   ignores AXIOM_TESTS regardless.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# CLAUSE / BINDER / POINT COVERAGE.
#   CLAUSES. C1 is the only impl-constraining clause (C4/C5/C6 are stated purely
#     over the spec's own `buildReport` and mention no output, so they hold for
#     every candidate and no rival can attack them — stated plainly rather than
#     papered over with a rival that would merely re-prove a frozen def). C1 is
#     attacked along SEVEN independent sub-behaviours: value presence (3 rivals: one
#     wide, two complementary sub-domain near-misses), preservation of the
#     pre-existing bindings (1), bound content (3: empty, another parameter's text,
#     a perturbation of the input), key identity (1), closure/no-extra-binding (2:
#     one unconditional, one confined to the parameterised sub-domain),
#     the report tag (1), and the accepting leg (1). C2's and C3's legs are covered
#     by weak-rejects-passing-input and by every failing-leg rival respectively. All
#     four are defended by the three positives plus the admissibility case.
#   BINDERS. All four INPUT BINDERS are varied by the reject witnesses — this is
#     the check the two known real failures would have needed:
#       value     : ['a'], ['b','c'], ['d'], ['e','f','g'], ['h','i'], ['m'],
#                   ['n'], ['p'], ['s','t'], ['t','u'], ['w'], ['z']  (lengths
#                   1/2/3, palindromic and not)
#       code      : ['i','n','v'], ['m','d'], ['x'], ['n'], ['q'], ['p','q'],
#                   ['r'], ['v'], ['y'], ['a','b'], []-in-rival  (lengths 1 and 2)
#       oldParams : [] (5 witnesses), [("max",['1'])], [("max",['2'])],
#                   [("max",['3'])], [("max",['4'])], [("max",['5'])],
#                   [("max",['7'])], [("max",['9']),("ext",['t'])]  (empty, one
#                   entry at six distinct contents, and a two-entry list)
#       isValid   : false (11 witnesses) AND true (weak-rejects-passing-input) —
#                   the binder the battery would otherwise have pinned.
#   POINTS. The 12 reject witnesses probe 12 DISTINCT input four-tuples; no two
#     rivals share a witness. pts = 12.
#   NEAR-MISS SITING. Each of the five near-miss rivals is refuted at a point where
#     the corresponding wide rival's own point would NOT have discriminated it:
#     weak-omits-value-only-when-bare at `oldParams = []` versus
#     weak-omits-value-unless-bare at a two-entry `oldParams` (each coincides with
#     gold at the other's point); weak-binds-existing-content at a non-empty
#     `oldParams` (it coincides with gold at every bare witness);
#     weak-binds-perturbed-content at a non-palindromic `value` (it coincides with
#     gold at every single-character witness, which is most of them);
#     weak-spurious-extra-binding-when-parameterised at a non-empty `oldParams`
#     (it coincides with gold at the unconditional closure rival's own bare point).
# WITNESS DISCRIMINATION — verified during authoring, not asserted. Every reject
#   case was built twice with scripts/lean_verify.sh: the witness ELABORATES against
#   its rival (exit 0) and FAILS against the frozen solution (exit 1) with the
#   SEMANTIC error `Tactic 'decide' proved that the proposition (match
#   checkValueExec … ) ≠ checkOutcome … is false` — i.e. gold's extracted program
#   equals the post-image at that point — never an unknown identifier, unfolding
#   failure, type error or timeout. No witness binds a hypothesis (the carrier
#   computes at literal inputs, so no conditioning is needed), hence the gate's
#   joint-satisfiability probe is a no-op and no witness can be
#   witness-inconsistent. No banned token (sorry/admit/native_decide/axiom/opaque)
#   appears in any witness or variant, no variant adds a theorem/lemma/axiom, and
#   the two retuned proofs add only frozen `def`s to the existing simp set.
AXIOM_TESTS = []
