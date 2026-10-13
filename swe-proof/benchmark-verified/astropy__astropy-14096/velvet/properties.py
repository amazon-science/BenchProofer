"""properties.py — G-PBT falsification battery for astropy__astropy-14096 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct lookupMissingAttribute`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  lookupMissingAttribute (requested, frameOutcome, genuineOutcome)
    ensures out = attrFallbackSpec requested frameOutcome genuineOutcome

The method resolves an attribute access the object's own directly held state did
not satisfy. An UNCHANGED resolution prefix runs first; its outcome is the free
input ``frameOutcome : Option Value`` (``some v`` = the prefix produced ``v``,
``none`` = it declined and the access is a genuine miss). On a genuine miss the
outcome of the UNCHANGED genuine attribute-resolution routine — the free input
``genuineOutcome : Except AttrErr Value`` — must be handed back VERBATIM (a value,
or the failure it reports, which may name an attribute OTHER than the requested
one). ``requested`` is read only to (mis)build a fabricated failure — the correct
behaviour never consults it on the miss path.

``attrFallbackSpec`` is a TRANSPARENT ``def`` in the ``pure`` region over the
method's own inputs — there is no opaque answer-key oracle in the load-bearing
clause, so pinning ``out = attrFallbackSpec …`` is grounded, not an echo. It has
TWO independent top-level legs, and every uniqueness rival targets one of them:

  (Lframe) frameOutcome = some v  -> out = Except.ok v        [prefix value returned]
  (Lmiss)  frameOutcome = none    -> out = genuineOutcome      [genuine outcome VERBATIM]

Lmiss is the discriminating behaviour the public issue reports: on a genuine
miss the failure the genuine routine reports (which may name a DIFFERENT
attribute than the one requested) must propagate unchanged, never be masked by a
freshly-minted failure renamed to the requested attribute. The F2P regression
asserts the surfaced failure blames the genuine inner attribute, not the
requested one — i.e. exactly ``out = genuineOutcome`` on the miss leg.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts a nine-input ``int/bool`` function with a four-way priority-ordered
resolution chain (alias > frame_attr > frame_passthrough > transform), a
normal-return guard, and a conditional-exception subject/capability clause. This
bundle models only the purely-functional CORE of the same fix: the two observable
outcomes of the whole prefix are collapsed into ONE opaque ``frameOutcome :
Option Value`` (some value produced, or a genuine miss), and the genuine routine's
result is the free input ``genuineOutcome``. So the nagini priority CHAIN and the
capability TOKEN have no counterpart on this carrier (see the footer accounting);
what remains is the two-leg dispatch, which is exactly what the F2P observable
turns on.

  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini class needs an input carrying
    a fractional heap permission an impl can overwrite. This backend is
    referentially transparent and this method declares NO ``mut`` binder: all
    three inputs are immutable values, there is no heap and no aliasing, so there
    is no read-only input to mutate and no substitute probe. Not fabricated.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, split across Lframe and
    Lmiss. ``frameOutcome`` is observed at both {some, none} and ``genuineOutcome``
    at both {ok, error} across the rivals, so neither free input is pinned. Both
    legs carry a WIDE rival (wrong on most inputs) and a NARROW one (wrong only on
    a sub-domain, or only in the payload), so neither leg is certified by a rival
    that any coarse spec would also reject.

WITNESS MECHANICS ON THIS BUNDLE. Unlike the opaque-carrier siblings, EVERY input
here is a fully decidable type (``Name``/``Value`` are ``Nat``; ``AttrErr`` is a
single ``Name`` field with ``DecidableEq``; the outcome is ``Except AttrErr
Value``). So a witness pins each free input to a CONCRETE literal and reaches the
contract through Velvet's own tester machinery: ``lookupMissingAttributeTester
requested frameOutcome genuineOutcome = false`` says the extracted program's
result violates the method's postcondition at that concrete input, closed by
``decide``. ``prove_postcondition_decidable_for`` needs equality of the report
carrier ``Except AttrErr Value`` decidable, so the preamble derives that instance
first — an instance, not an assumption (no ``axiom``/``sorry``/``native_decide``).
No witness binds a hypothesis (every input is a literal that decides the leg), so
no consistency probe is needed. Each witness is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict; each was checked out-of-band with ``scripts/lean_verify.sh`` — it
ELABORATES against its rival (exit 0) and FAILS against the frozen solution (a
``decide`` error), the discrimination the gate re-runs.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (both unchanged
sub-computations are carried as free inputs, owed no contract), so there is
nothing to probe, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14096"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the two-leg dispatch),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let out := match frameOutcome with\n"
    "      | some v => Except.ok v\n"
    "      | none   => genuineOutcome\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape whose residual goal the frozen script no
# longer closes may RETUNE this block (elided from the spec view) WITHOUT touching
# the spec or dropping the obligation — the `prove_correct lookupMissingAttribute
# by` header statement stays byte-identical. Rivals leave it as-is: the rejection
# is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct lookupMissingAttribute by\n"
    "  loom_solve <;> simp_all [attrFallbackSpec]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a reshape whose residual
    goal no longer closes under the frozen `simp_all`)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble + builder. The spec is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery.
# ---- `prove_postcondition_decidable_for` needs `Except AttrErr Value` equality
# ---- decidable, so the preamble derives that instance first (an instance, not an
# ---- assumption). Checked in a file whose `prove_correct` block is stripped, so
# ---- no tactic script can mask the verdict.
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for lookupMissingAttribute\n"
    "prove_precondition_decidable_for lookupMissingAttribute\n"
    "prove_postcondition_decidable_for lookupMissingAttribute\n"
    "derive_tester_for lookupMissingAttribute\n\n"
)


def _wit(requested, frame, genuine):
    return (
        _PREAMBLE +
        f"example : lookupMissingAttributeTester {requested} {frame} {genuine}"
        " = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures out = attrFallbackSpec …`
    # obligation and only reshapes the executable dispatch.
    # =====================================================================
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same two-way dispatch written with the miss arm before the
        # value arm. A `match` is order-insensitive on disjoint `Option`
        # constructors, so the computed outcome is identical on both legs. The
        # frozen script's `simp_all` no longer reconciles the reordered `match`
        # form, so the tactic body is retuned (elided from the spec view) with one
        # `cases` on `frameOutcome`; the obligation STATEMENT is byte-identical.
        "module": _impl_reproved(
            "    let out := match frameOutcome with\n"
            "      | none   => genuineOutcome\n"
            "      | some v => Except.ok v\n"
            "    return out",
            "prove_correct lookupMissingAttribute by\n"
            "  loom_solve <;> (cases frameOutcome <;> simp_all [attrFallbackSpec])"),
        "rationale": "reordering the disjoint `Option` arms computes the same "
                     "`Except AttrErr Value` on both legs, so `out = "
                     "attrFallbackSpec …` still holds; a correct reshape must "
                     "verify (else SPEC-TOO-STRONG on arm order). Ports the nagini "
                     "pos-elif-chain (a behaviour-preserving control reorder).",
    },
    {
        "id": "pos-direct-spec",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the outcome DIRECTLY via the transparent `pure` def, no
        # inline match. The post-image is literally `out = attrFallbackSpec …`, so
        # this is the cheapest HONEST correct impl — and, since attrFallbackSpec is
        # GROUNDED in the inputs (not an opaque answer key), it doubles as proof
        # the spec is not echo-vulnerable: any wrong leg fails the equality. The
        # inline match is gone, so the residual goal is `rfl`-shaped and the frozen
        # `simp_all [attrFallbackSpec]` closes it unchanged (no retune needed).
        "module": _impl(
            "    let out := attrFallbackSpec requested frameOutcome genuineOutcome\n"
            "    return out"),
        "rationale": "the post-image `attrFallbackSpec …` is GROUNDED in the "
                     "inputs (a total `def`, no opaque answer key), so reporting it "
                     "directly is the honest cheapest CORRECT impl; the obligation "
                     "is literally that equality, so it MUST verify, else "
                     "SPEC-TOO-STRONG. Re-expresses the nagini "
                     "pos-guard-negation-first / echo-attempt-honest control: the "
                     "cheapest impl satisfying the grounded pin, showing the spec "
                     "is not echo-vulnerable (any wrong leg fails the equality).",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-in-domain-call. That case
    # established that the (empty) Requires admits a representative F2P-shaped
    # input. This method carries NO `require` clause (the pre-conditions region is
    # empty), so nothing could exclude a normal input and the classic "a normal
    # input satisfies the precondition" probe is vacuous. Re-aimed at the residual
    # total-domain admissibility risk: that the post-image is jointly SATISFIABLE
    # by a gold-shaped computation (a spec no impl can meet reads exactly like a
    # spec every impl meets). The frozen impl discharging the obligation IS that
    # witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        # Admissibility must be witnessed by a computation that is NOT the frozen
        # impl: re-submitting `_BASE` verbatim re-runs the gold build and attests
        # nothing this manifest is responsible for. So the witness here is an
        # INDEPENDENT total computation that case-splits the report carrier on the
        # miss leg — it reconstructs `genuineOutcome` constructor-by-constructor
        # (`ok w -> ok w`, `error e -> error e`) instead of passing it through. That
        # exercises the post-image at BOTH `Except` constructors on the miss leg,
        # so joint satisfiability is demonstrated at every shape of every input
        # rather than asserted. The reconstruction makes the residual goal
        # two-level, so the tactic body is retuned (elided from the spec view) with
        # a `cases` on each scrutinee; the obligation STATEMENT is byte-identical.
        "module": _impl_reproved(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok v\n"
            "      | none   => match genuineOutcome with\n"
            "                  | Except.ok w    => Except.ok w\n"
            "                  | Except.error e => Except.error e\n"
            "    return out",
            "prove_correct lookupMissingAttribute by\n"
            "  loom_solve <;> (cases frameOutcome <;> cases genuineOutcome <;>\n"
            "    simp_all [attrFallbackSpec])"),
        "rationale": "the inputs carry no `require`, so the routine is total over "
                     "every (requested, frameOutcome, genuineOutcome); this case "
                     "witnesses that the post-image `out = attrFallbackSpec …` is "
                     "jointly SATISFIABLE at every input shape (a spec no impl can "
                     "meet reads exactly like a spec every impl meets). The witness "
                     "is deliberately NOT the frozen impl — it rebuilds the report "
                     "from its constructors on the miss leg, so the equality is "
                     "discharged with `frameOutcome` split at {some, none} AND "
                     "`genuineOutcome` split at {ok, error}, covering all four "
                     "combinations. Re-aimed from the nagini admiss-in-domain-call, "
                     "whose read-only-precondition half has no counterpart on this "
                     "referentially-transparent carrier. Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================

    # ---- Lmiss: the genuine-outcome-verbatim leg (the discriminating F2P) ----
    {
        "id": "weak-miss-renames-to-requested",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-patch behaviour: on a genuine miss, FABRICATE a fresh
        # failure naming the ORIGINALLY-REQUESTED attribute, discarding the genuine
        # routine's own outcome. Correct on the prefix-value leg; wrong exactly on
        # the miss leg whenever the genuine failure names a DIFFERENT attribute.
        "module": _impl(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok v\n"
            "      | none   => Except.error { subject := requested }\n"
            "    return out"),
        "refinement": "this is the pre-patch fallback: on a genuine miss it mints a "
                      "fresh failure blaming the requested attribute and discards "
                      "the genuine routine's outcome. Its faithful real patch is "
                      "the unpatched repo, whose fallback names the requested "
                      "attribute; the failing test asserts the surfaced failure "
                      "names the genuine INNER attribute (a different one), which "
                      "the requested-name failure does not, so it would NOT "
                      "resolve. This is the exact defect the fix corrects.",
        "rationale": "REJECT from Lmiss (`frameOutcome = none -> out = "
                     "genuineOutcome`): on a genuine miss the impl returns a "
                     "failure renamed to `requested` where the post-image demands "
                     "the genuine outcome verbatim. Refuted at `(requested=0, "
                     "frameOutcome=none, genuineOutcome=error {subject:=1})` — the "
                     "sub-domain where the genuine failure names a DIFFERENT "
                     "attribute (1 ≠ 0), so the rename diverges from gold. If it "
                     "verified => SPEC-TOO-WEAK (admits the bug).",
        "witness": _wit("0", "none", "(Except.error { subject := 1 })"),
    },
    {
        "id": "weak-miss-vacuous-value",
        "kind": "uniqueness",
        "expect": "reject",
        # On a genuine miss returns a fabricated SUCCESS value instead of the
        # genuine outcome — the "normal return where a failure is due" cheat. When
        # the genuine routine reports a failure, this swallows it and returns ok.
        "module": _impl(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok v\n"
            "      | none   => Except.ok 0\n"
            "    return out"),
        "refinement": "on a genuine miss this returns a fabricated success instead "
                      "of the failure the genuine routine reports. A real patch of "
                      "this shape would make a missing attribute appear to resolve "
                      "to a value, so the failing test — which requires an "
                      "AttributeError to surface on the miss path — reports DID NOT "
                      "RAISE and does NOT resolve.",
        "rationale": "REJECT from Lmiss (`frameOutcome = none -> out = "
                     "genuineOutcome`): on a genuine miss the impl returns a "
                     "vacuous success where the post-image demands the genuine "
                     "outcome. Refuted at `(requested=0, frameOutcome=none, "
                     "genuineOutcome=error {subject:=0})` — a DISTINCT point from "
                     "the rename rival (here the genuine failure names the "
                     "requested attribute, so the rename rival would COINCIDE with "
                     "gold; this rival still diverges by returning ok), so the "
                     "battery varies `genuineOutcome`. Re-sites the nagini "
                     "atk-return-name / atk-return-alias (a vacuous normal return "
                     "on the no-resolution path). If it verified => SPEC-TOO-WEAK.",
        "witness": _wit("0", "none", "(Except.error { subject := 0 })"),
    },
    {
        "id": "weak-miss-forged-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # On a genuine miss raises a fixed forged failure that ignores BOTH the
        # requested name and the genuine outcome. Correct on the prefix-value leg;
        # wrong on the miss leg whenever the genuine outcome is not that constant
        # (here, whenever the genuine routine SUCCEEDS).
        "module": _impl(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok v\n"
            "      | none   => Except.error { subject := 0 }\n"
            "    return out"),
        "refinement": "on a genuine miss this raises a fixed forged failure that "
                      "ignores what the genuine routine actually reported — in "
                      "particular it fails even when the genuine routine would "
                      "SUCCEED. A real patch of this shape neither delegates nor "
                      "propagates the genuine outcome, so the surfaced result never "
                      "matches what the genuine mechanism yields and the failing "
                      "tests do NOT resolve.",
        "rationale": "REJECT from Lmiss (`frameOutcome = none -> out = "
                     "genuineOutcome`): on a genuine miss the impl returns a "
                     "constant forged failure where the post-image demands the "
                     "genuine outcome. Refuted at `(requested=3, frameOutcome=none, "
                     "genuineOutcome=ok 7)` — the genuine routine SUCCEEDS, so the "
                     "forged failure diverges; also probes `genuineOutcome=ok` on "
                     "the miss leg (the third distinct genuine outcome the battery "
                     "exercises) and `requested=3` (subject 0 ≠ requested, "
                     "distinguishing it from the pre-patch rename). Re-sites the "
                     "nagini atk-raise-forged-token. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit("3", "none", "(Except.ok 7)"),
    },

    {
        "id": "weak-miss-masks-only-when-names-coincide",
        "kind": "uniqueness",
        "expect": "reject",
        # The SHARPEST near-miss on Lmiss, and the one the other three rivals leave
        # unattacked. It propagates the genuine outcome faithfully — values verbatim,
        # failures verbatim — EXCEPT on the single sub-domain where the genuine
        # failure happens to name the requested attribute, where it swallows the
        # failure and reports a success. Every other reject case in this battery
        # diverges from gold on a WIDE set of inputs; this one agrees with gold
        # everywhere the earlier witnesses look and diverges only at
        # `e.subject = requested`. If the spec admitted it, the spec would be blind
        # to a sub-domain-conditional masking defect.
        "module": _impl(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok v\n"
            "      | none   => match genuineOutcome with\n"
            "                  | Except.ok w    => Except.ok w\n"
            "                  | Except.error e =>\n"
            "                    if e.subject == requested then Except.ok 0\n"
            "                    else Except.error e\n"
            "    return out"),
        "refinement": "this consults `requested` on the miss path to decide whether "
                      "to suppress the genuine failure: when the genuine routine "
                      "reports a failure about the requested attribute itself, the "
                      "failure is swallowed and a value is reported instead. A real "
                      "patch of this shape makes a plainly-missing attribute appear "
                      "to resolve, so an access that must surface an AttributeError "
                      "returns normally and the unchanged tests pinning that failure "
                      "report DID NOT RAISE — it would NOT resolve.",
        "rationale": "REJECT from Lmiss (`frameOutcome = none -> out = "
                     "genuineOutcome`) on a NARROW sub-domain: the impl is correct on "
                     "the prefix-value leg, correct on the miss leg whenever the "
                     "genuine outcome is a value or names a DIFFERENT attribute, and "
                     "wrong only where the genuine failure's subject equals "
                     "`requested`. Refuted at `(requested=4, frameOutcome=none, "
                     "genuineOutcome=error {subject:=4})` — a point where all three "
                     "earlier miss rivals COINCIDE with gold or are already refuted "
                     "elsewhere, and a fourth distinct `requested` value. The post-"
                     "image demands the genuine outcome verbatim on the whole miss "
                     "leg, with no sub-domain the requested name may be consulted "
                     "on. If it verified => SPEC-TOO-WEAK (admits a "
                     "sub-domain-conditional masking defect).",
        "witness": _wit("4", "none", "(Except.error { subject := 4 })"),
    },

    # ---- Lframe: the prefix-value leg ----
    {
        "id": "weak-frame-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the unchanged prefix's own result and delegates to the genuine
        # routine on EVERY access — even when the prefix already produced a value.
        # Correct on the miss leg (frameOutcome = none); wrong exactly on the
        # prefix-value leg whenever the genuine outcome differs from that value.
        "module": _impl(
            "    let out := genuineOutcome\n"
            "    return out"),
        "refinement": "this discards the unchanged resolution prefix's own value "
                      "and re-runs the genuine routine even when the prefix already "
                      "resolved the access. A real patch of this shape would "
                      "override the frame-name / frame-attribute / transform "
                      "resolutions the unchanged prefix performs, changing "
                      "observable attribute resolution for those accesses, so the "
                      "unchanged tests that pin the prefix's result still fail — it "
                      "would NOT resolve.",
        "rationale": "REJECT from Lframe (`frameOutcome = some v -> out = "
                     "Except.ok v`): when the prefix produced a value the impl "
                     "returns the genuine routine's outcome instead. Refuted at "
                     "`(requested=0, frameOutcome=some 5, genuineOutcome=ok 7)` — "
                     "the only point probing `frameOutcome=some`, so the battery "
                     "varies that binder across both constructors. Re-sites the "
                     "nagini priority/drop-branch family (a value-producing prefix "
                     "ignored). If it verified => SPEC-TOO-WEAK.",
        "witness": _wit("0", "(some 5)", "(Except.ok 7)"),
    },
    {
        "id": "weak-frame-value-perturbed",
        "kind": "uniqueness",
        "expect": "reject",
        # Lframe was attacked by exactly ONE rival, and that rival discards the
        # prefix value WHOLESALE (returns genuineOutcome on every input), so it is
        # refuted by any point with `frameOutcome = some`. Nothing tested that the
        # value returned on the prefix-value leg is the prefix's OWN value: an impl
        # that takes the right branch, reports the right OUTCOME SHAPE (`Except.ok`),
        # and merely returns a DIFFERENT value passed the whole battery. This rival
        # closes that: it honours the branch and the constructor and corrupts only
        # the payload.
        "module": _impl(
            "    let out := match frameOutcome with\n"
            "      | some v => Except.ok (v + 1)\n"
            "      | none   => genuineOutcome\n"
            "    return out"),
        "refinement": "this returns a value DERIVED from, rather than equal to, the "
                      "value the unchanged resolution prefix produced. A real patch "
                      "of this shape hands back something other than what the prefix "
                      "resolved, so every unchanged test that reads a prefix-resolved "
                      "attribute observes the wrong object — it would NOT resolve.",
        "rationale": "REJECT from Lframe (`frameOutcome = some v -> out = "
                     "Except.ok v`) on the PAYLOAD rather than the branch: the impl "
                     "dispatches correctly and reports an `Except.ok`, but not of "
                     "`v`. Refuted at `(requested=0, frameOutcome=some 5, "
                     "genuineOutcome=error {subject:=9})` — where weak-frame-ignored "
                     "is ALSO wrong but for the other reason, and this point adds a "
                     "fourth distinct `genuineOutcome` (an error subject not equal to "
                     "any other case's) observed on the prefix-value leg, showing "
                     "`genuineOutcome` is irrelevant there. If it verified => "
                     "SPEC-TOO-WEAK (the prefix value would be unpinned, only its "
                     "outcome constructor pinned).",
        "witness": _wit("0", "(some 5)", "(Except.error { subject := 9 })"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling has 10 SPEC cases (2 soundness, 1 admissibility, 7
# uniqueness) plus 2 AXIOM_TESTS. It contracts a nine-input int/bool function
# `resolve_missing` with a FOUR-WAY priority-ordered resolution chain, a
# normal-return guard, and a conditional-exception clause carrying an unforgeable
# capability token. This velvet bundle models only the purely-functional CORE of
# the same fix: the whole prefix's two observable outcomes collapse into ONE
# opaque `frameOutcome : Option Value`, and the genuine routine's result is the
# free input `genuineOutcome`. So the priority CHAIN and the capability TOKEN have
# no counterpart on this carrier — carrier narrowing, not a fabricable gap.
#
#   nagini case                     -> here                         status
#   -----------------------------------------------------------------------
#   pos-elif-chain                  -> pos-arms-reordered            RE-SHAPED
#   pos-guard-negation-first        -> pos-direct-spec               RE-EXPRESSED
#   admiss-in-domain-call           -> admiss-total-domain            RE-AIMED
#   atk-raise-requested-name        -> weak-miss-renames-to-requested PORTED
#   atk-return-name                 -> weak-miss-vacuous-value        RE-SITED
#   atk-return-alias                -> (merged into weak-miss-vacuous-value)
#   atk-raise-forged-token          -> weak-miss-forged-constant      RE-SITED
#   atk-priority-swap-alias-frame   -> (none)                         OMITTED
#   atk-drop-transform-branch       -> weak-frame-ignored             RE-SITED
#   atk-echo-oracle                 -> (none)                         OMITTED
#   AXIOM_TESTS (2)                 -> (none)                         DROPPED (G-AX)
#   (no nagini source)              -> weak-miss-masks-only-when-      ADDED
#                                      names-coincide                  (audit)
#   (no nagini source)              -> weak-frame-value-perturbed      ADDED (audit)
#
# 9 velvet SPEC cases: 2 soundness, 1 admissibility, 6 uniqueness.
#
# ADDED (2, by the adversarial audit of this port — no nagini counterpart; they
#   close near-miss gaps the ported rivals left, each measured with the real
#   verifier):
#  * weak-miss-masks-only-when-names-coincide. All three ported Lmiss rivals
#    diverge from gold on a WIDE input set. None tested whether the spec forbids
#    consulting `requested` on a NARROW sub-domain, so a rival that propagates the
#    genuine outcome faithfully except where the genuine failure names the
#    requested attribute was unattacked. It is rejected, and its witness at
#    `(4, none, error {subject := 4})` discriminates.
#  * weak-frame-value-perturbed. Lframe carried exactly ONE rival, which discards
#    the prefix value wholesale; nothing pinned the prefix-leg PAYLOAD as opposed
#    to the branch and the outcome constructor. `some v -> ok (v+1)` honours both
#    and corrupts only the value; it is rejected, witness at
#    `(0, some 5, error {subject := 9})`.
#
# RE-AIMED, then REPAIRED by the audit (admiss-total-domain): the case originally
#   submitted `_BASE` — the frozen impl verbatim — as its own admissibility
#   witness. That verifies by re-running the gold build and attests nothing this
#   manifest is responsible for. Replaced with an INDEPENDENT total computation
#   that rebuilds the report from its constructors on the miss leg, so the
#   post-image is discharged with `frameOutcome` split at {some, none} AND
#   `genuineOutcome` split at {ok, error} — satisfiability demonstrated at all four
#   input shapes rather than inherited from gold.
#
# RE-SHAPED / RE-EXPRESSED (positives): pos-elif-chain -> pos-arms-reordered (a
#   behaviour-preserving reorder of the two disjoint dispatch arms, retuned
#   proof). pos-guard-negation-first -> pos-direct-spec: the nagini positive
#   handled the no-resolution path first via a negated disjunction; here the whole
#   dispatch IS the pure `attrFallbackSpec`, so the honest cheapest correct impl
#   reports it directly — the same "structurally different but correct" argument.
# RE-AIMED (admiss-in-domain-call -> admiss-total-domain): the nagini case
#   exercised the empty Requires on an F2P-shaped input. This method has no
#   `require`, so that probe is vacuous; re-aimed at the residual total-domain risk
#   (post-image joint satisfiability). See the audit repair note above for why the
#   witness is an independent computation and not the frozen impl.
# PORTED (atk-raise-requested-name -> weak-miss-renames-to-requested): the exact
#   pre-patch, the discriminating F2P behaviour — mint a failure blaming the
#   requested attribute instead of propagating the genuine one. Carries its nagini
#   refinement (unpatched repo blames the requested name; the F2P asserts the
#   inner name) with a machine-checked witness.
# RE-SITED (3):
#  * atk-return-name / atk-return-alias -> weak-miss-vacuous-value. Nagini's
#    normal-return guard (P2) forbade returning NORMALLY on the no-resolution
#    path. On this carrier the return type IS `Except`, so "return normally" =
#    return `Except.ok`; a miss-leg `Except.ok 0` is the faithful re-siting of
#    "fabricate a normal return where a failure is due". The two nagini rivals
#    (return `name` vs return `alias_value`) are the same wrongness at one point
#    on this carrier (a fabricated success on the miss leg), so they merge into a
#    single rival; splitting them would probe the same leg at the same reason.
#  * atk-raise-forged-token -> weak-miss-forged-constant. A raised-but-forged
#    subject that ignores both the requested name and the genuine outcome; refuted
#    where the genuine routine succeeds.
#  * atk-drop-transform-branch / atk-priority-swap family -> weak-frame-ignored.
#    Nagini's four resolution branches collapse into the single Lframe leg here;
#    a rival that ignores the prefix value and always delegates is the faithful
#    re-siting of "a value-producing resolution branch is dropped/overridden".
# OMITTED (2, carrier narrowing — NOT because hard):
#  * atk-priority-swap-alias-frame. Attacks the ORDER among the four resolution
#    sources (alias before frame_attr). This carrier does not model individual
#    resolution sources or their priority at all — the whole prefix is one opaque
#    `frameOutcome : Option Value` (a value was produced, or not). There is no
#    priority order in the model to invert, so no rival can express the inversion
#    and no witness could discriminate one. The residual "a value-producing prefix
#    is mishandled" attack IS expressible and is carried by weak-frame-ignored.
#  * atk-echo-oracle. Attacks the nagini capability clause: a rival that ECHOES
#    the pure subject-oracle without re-entering the ordinary mechanism, refuted
#    because it cannot present the unforgeable `reentered_ordinary_lookup` token.
#    This carrier has NO such oracle and NO capability token: the genuine routine's
#    result is the free input `genuineOutcome`, and the correct miss-leg behaviour
#    is precisely `out = genuineOutcome` — i.e. "echoing genuineOutcome" IS gold,
#    not a cheat. The distinction the capability clause guarded (echo the answer vs
#    actually delegate) collapses when the answer is a free input rather than an
#    opaque oracle, so the class is vacuous and no substitute is fabricated.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness/containment probes over
#   the real `__getattribute__` callee are G-AX's job (this bundle declares no
#   axiom — the genuine routine is a free input, owed no contract), and the G-PBT
#   gate ignores AXIOM_TESTS regardless.
#
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
#
# CLAUSE / BINDER / POINT COVERAGE. `attrFallbackSpec` has two impl-constraining
#   legs; BOTH are attacked at TWO grains each — Lmiss by three wide rivals plus one
#   sub-domain near-miss, Lframe by one wide rival plus one payload near-miss — and
#   both are defended by the two positives and the admissibility case. The three
#   free inputs are varied: `frameOutcome` at {none, some 5}; `genuineOutcome` at
#   {error {subject:=1}, error {subject:=0}, error {subject:=4},
#   error {subject:=9}, ok 7} (both constructors, error at four distinct subjects);
#   `requested` at {0, 3, 4}. The six reject witnesses probe six DISTINCT input
#   points, and each near-miss is refuted at a point where the others coincide with
#   gold — verified by build, not asserted: the vacuous-value witness's point
#   `(0, none, error {subject:=0})` does NOT hold of the rename rival (exit 1, the
#   `decide` reports the proposition false), so `genuineOutcome`'s subject is
#   genuinely varied and not pinned.
#
# WITNESS MECHANICS: every input type is decidable (Nat / single-field structure /
#   Except), so each witness pins the three inputs to concrete literals and closes
#   `lookupMissingAttributeTester … = false` by `decide`; the preamble derives
#   `DecidableEq` for `Except` (an instance, not an assumption) so
#   `prove_postcondition_decidable_for` succeeds. No witness binds a hypothesis, so
#   no consistency probe is needed. All six checked with scripts/lean_verify.sh:
#   each ELABORATES against its rival (exit 0) and FAILS against gold (exit 1) with
#   a SEMANTIC error — `Tactic 'decide' proved that the proposition
#   lookupMissingAttributeTester … = false is false`, i.e. gold's tester accepts the
#   point — never an unknown identifier, type error, unfolding failure or timeout.
#   No banned token (sorry/admit/native_decide/axiom/opaque).
AXIOM_TESTS = []
