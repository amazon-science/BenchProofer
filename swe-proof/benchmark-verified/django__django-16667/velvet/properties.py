"""properties.py — G-PBT falsification battery for django__django-16667 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct dateComponentsText`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  dateComponentsText (y m d : List Char) (outcome : ConstructOutcome)
      return (out : Except DateErr (List Char))
    ensures out = dateText y m d outcome                                   -- C1
    ensures ∀ s, outcome = .rendered s → out = Except.ok s                 -- C2
    ensures outcome = .notCalendar → out = Except.ok (pseudoTriple y m d)  -- C3
    ensures outcome = .unrepresentable → out = Except.ok fallbackNoComponents  -- C4
    ensures ∃ r, out = Except.ok r                                         -- C5

The method models the all-three-components-present inner branch that turns three
textual date components and the outcome of handing them to the calendar
machinery into the text this widget reports. ``ConstructOutcome`` is a FREE INPUT
(no consumed axiom): its three mutually-exclusive shapes are

  * ``rendered s``       — a representable value was obtained and rendered to
                           the opaque payload ``s`` (echoed back verbatim, C2);
  * ``notCalendar``      — the components name no representable calendar value,
                           so the result is the pseudo-ISO fallback built from
                           the very components, ``pseudoTriple y m d`` (C3);
  * ``unrepresentable``  — a component's magnitude is too large to be accepted
                           at all, so the branch returns the component-
                           independent instance of that same fallback,
                           ``fallbackNoComponents`` = ``pseudoTriple [] [] []``,
                           as a value (``Except.ok``) (C4 + C5).

WHICH CLAUSE CONSTRAINS THE IMPL. ``dateText``, ``pseudoTriple``, ``orZero`` and
``fallbackNoComponents`` are all TRANSPARENT ``def``s over the method's own
inputs —
there is NO opaque answer-key oracle in any clause. C1 (``out = dateText y m d
outcome``) is the whole pin: it is a function of the four inputs and pins the
returned value at every outcome. C2–C4 are the three per-outcome projections of
C1 (each attackable independently by a rival that mishandles exactly one
outcome), and C5 is the load-bearing NO-ESCAPE contract the fix defends (a
correct result is always ``Except.ok``; the pre-patch crash is exactly an
``Except.error`` on the ``unrepresentable`` leg). Every uniqueness rival targets
one of these; being TRANSPARENT they are all refutable by a concrete witness.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * The nagini sibling contracts the WHOLE ``value_from_components(all_blank,
    all_present, kind)`` including the all-blank fast path and the
    not-all-present raw-retrieval fallback. This velvet bundle models ONLY the
    all-three-present inner routing (mapping.md §1: the patch hunk lives entirely
    inside the all-present try/except, which is exactly what this method models).
    The outer branches are UNMODELED here — carrier narrowing, not a gap — so the
    three nagini rivals attached to them have no counterpart (see accounting).
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini three params are primitive
    value types passed by value with no ``Acc(.,1/2)`` read-only input, and the
    sibling itself records the class structurally N/A. Lean/Velvet are
    referentially transparent besides: ``y``, ``m``, ``d`` and ``outcome`` are
    immutable values declared read-only (no ``mut``), there is no heap, aliasing,
    or permission system. No read-only input to overwrite; no substitute
    fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. Every clause is pinned to a
    transparent ``def`` of the method's own inputs; there is no answer key to
    echo. The cheapest honest correct impl (``return dateText y m d outcome``) is
    carried as a POSITIVE control, doubling as proof the spec is not
    echo-vulnerable (any wrong routing fails C1). The nagini file's UNGROUNDED-
    ORACLE note (the success/out-of-range/raw oracles are abstract @ContractOnly)
    manifests here as CROSS-BRANCH substitution rivals (echo-pseudo-unrep,
    swap-notcal, ignore-rendered) — return a different transparent branch's text.
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

WITNESS MECHANICS ON THIS BUNDLE. The tester+``decide`` path is DEAD: the
postcondition mixes a ``∀ s`` (C2) and a ``∃ r`` (C5), so no ``Decidable``
instance exists for the conjoined postcondition and ``derive_tester_for
dateComponentsText`` cannot emit a tester at all. Re-measured during audit, with
``extract_program_for`` supplied first so the failure is not merely a missing
executable: BOTH a wrong rival and gold fail identically with ``failed to
synthesize Decidable ((∃ r, out = Except.ok r) ∧ ... ∧ (∀ (s : List Char), ...))``
— the same error text on both sides, so that path discriminates nothing.

But C1's carrier IS transparent. Each rival is written LOOP-FREE (a ``match`` on
``outcome`` returning a closed expression), so its extracted program
``dateComponentsTextExec`` — the ``NonDetT``-run of the impl — REDUCES fully
under ``decide`` at a concrete input. ``Except DateErr (List Char)`` has no
``DecidableEq`` instance, so each witness first PROJECTS both sides to
``Option (List Char)`` (``Except.ok r ↦ some r``, ``Except.error _ ↦ none`` — a
projection that preserves BOTH the ok/error distinction C5 turns on AND the
value C1/C2/C3/C4 pin) and states, at one concrete input,

    (proj (dateComponentsTextExec <input>)) ≠ proj (dateText <input>)

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator can see. Against the FROZEN solution the
SAME statement is ``proj gold ≠ proj gold`` which is decidably FALSE, so
``decide`` cannot close the ``≠`` and the witness FAILS on gold — exactly the
discrimination the gate requires. No witness binds any hypothesis (every input is
a concrete literal that decides C1), so no consistency probe is needed and no
banned token (sorry/admit/native_decide/axiom/opaque) appears. Each witness was
checked out-of-band with ``scripts/lean_verify.sh``: every one ELABORATES against
its rival (exit 0, no errors) and FAILS against gold (a ``decide`` error).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real ``datetime.date`` callee; that is
G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless. (This bundle also declares no consumed axiom —
``ConstructOutcome`` is a free input, mapping.md §3.)
"""
from pathlib import Path

INSTANCE = "django__django-16667"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE frozen impl body, everything strictly BETWEEN the method's
# ---- `-- impl-start` / `-- impl-end`. Every variant replaces exactly this text
# ---- (or a slice of it), so each edit lies wholly inside the one impl region
# ---- and same_spec holds by construction (both facts asserted at load).
_IMPL = (
    "    let result : Except DateErr (List Char) :=\n"
    "      match outcome with\n"
    "      | .rendered s      => Except.ok s\n"
    "      | .notCalendar     => Except.ok (pseudoTriple y m d)\n"
    "      | .unrepresentable => Except.ok fallbackNoComponents\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- reshape that removes the `let`/`match` staging retunes THIS block; the
# ---- arm-reorder positive and every reject rival leave it as-is (the rejection
# ---- is carried by the witness, not the tactic script).
_PROOF = (
    "prove_correct dateComponentsText by\n"
    "  loom_solve\n"
    "  cases outcome <;> simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes whose residual
    goal no longer matches the frozen `let`/`match` staging)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- a loop-free reject rival: dispatch on `outcome` with three closed arms.
# ---- Being loop-free its extracted `…Exec` reduces under `decide`, so its
# ---- witness discriminates; the proof is left frozen (the rejection is the
# ---- witness's job, not the tactic script's).
def _arms(rendered_arm, notcal_arm, unrep_arm):
    return _impl(
        "    let result : Except DateErr (List Char) :=\n"
        "      match outcome with\n"
        f"      | .rendered s      => {rendered_arm}\n"
        f"      | .notCalendar     => {notcal_arm}\n"
        f"      | .unrepresentable => {unrep_arm}\n"
        "    return result\n"
    )


# ---- witness preamble + builder. The postcondition is NOT decidable (C2's
# ---- `∀ s` and C5's `∃ r`), so the tester+`decide` path is dead; instead
# ---- extract the executable program and refute C1 directly on the TRANSPARENT
# ---- `dateText`, projecting `Except` to `Option (List Char)` (no `DecidableEq`
# ---- for `Except`) so `decide` can settle the `≠`. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT = "extract_program_for dateComponentsText\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match dateComponentsTextExec {inp} with\n"
        "     | DivM.res (Except.ok r) => some r"
        " | DivM.res (Except.error _) => none | _ => none)\n"
        f"    ≠ (match (dateText {inp}) with"
        " | Except.ok r => some r | Except.error _ => none) := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no `let`/`match` staging. `out` IS `dateText y m d outcome`, so C1
        # holds definitionally and the per-outcome projections follow by
        # `cases outcome`. Since `dateText` is GROUNDED in the inputs (not an
        # opaque answer key), this doubles as proof the spec is not
        # echo-vulnerable: any WRONG routing fails `out = dateText …`. The
        # `let` is gone, so the residual goal closes under `cases outcome <;>
        # simp [dateText]`.
        "module": _impl_reproved(
            "    return (dateText y m d outcome)\n",
            "prove_correct dateComponentsText by\n"
            "  loom_solve\n"
            "  cases outcome <;> simp [dateText]"),
        "rationale": (
            "the post-image `dateText y m d outcome` is GROUNDED in the inputs "
            "(a transparent total `def`, no opaque answer key), so `return "
            "dateText y m d outcome` is the honest cheapest CORRECT impl; C1 is "
            "literally `out = dateText y m d outcome`, so it MUST verify, else C1 "
            "is SPEC-TOO-STRONG. Ports the nagini pos-reorder soundness intent "
            "(a structurally-different correct impl) and shows the spec is not "
            "echo-vulnerable (any wrong per-outcome routing fails C1)."),
    },
    {
        "id": "pos-control-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the `let`/`match` staging but REORDER the three arms
        # (unrepresentable, then notCalendar, then rendered). The three
        # constructors are mutually exclusive, so arm order is irrelevant to the
        # value; the frozen proof closes unchanged.
        "module": _impl(
            "    let result : Except DateErr (List Char) :=\n"
            "      match outcome with\n"
            "      | .unrepresentable => Except.ok fallbackNoComponents\n"
            "      | .notCalendar     => Except.ok (pseudoTriple y m d)\n"
            "      | .rendered s      => Except.ok s\n"
            "    return result\n"),
        "rationale": (
            "a correct impl with the three mutually-exclusive match arms in a "
            "DIFFERENT order must verify; the value flow is unchanged so C1–C5 "
            "still discharge and the frozen `cases outcome <;> simp_all` proof "
            "closes as-is. Ports the nagini pos-reorder (which reorders the "
            "branch cascade and flips the except order — independent outcomes, so "
            "order is irrelevant to correctness). If it fails => SPEC-TOO-STRONG "
            "(over-fit to the frozen arm order)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p. That case established the
    # precondition admits the F2P overflow input (all present, none blank, kind
    # 2) by self-calling. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude any input and the
    # classic "the precondition admits the F2P input" probe is vacuous. Re-aimed
    # at the residual admissibility risk on a total domain: that the five-clause
    # post-image is jointly SATISFIABLE by a gold-shaped computation. The frozen
    # impl discharging all five ensures IS that witness — including the F2P-shaped
    # `unrepresentable` outcome, where C4 pins the "0-0-0" sentinel and C5 pins
    # the no-escape. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the routing is total over every "
            "component triple and outcome; the gold impl discharging all five "
            "ensures is the admissibility witness that the post-image (C1 plus "
            "the four per-outcome projections, incl. the F2P-shaped "
            "`unrepresentable` leg pinning the constant sentinel and the "
            "no-escape) is jointly satisfiable. Near-trivial precisely because "
            "the precondition is empty. Re-aimed from the nagini admiss-f2p, "
            "whose precondition-admits-F2P half has no counterpart on this "
            "require-free carrier. Else SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is LOOP-FREE so its
    # extracted `…Exec` `decide`s (see WITNESS MECHANICS); the frozen spec is
    # untouched. The four input binders (y, m, d, outcome) are varied across the
    # witnesses; `outcome` ranges over all three constructors.
    # =====================================================================
    {
        "id": "reject-let-value-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-patch behaviour: on the `unrepresentable` outcome let the
        # magnitude ESCAPE (return `Except.error`) instead of returning the
        # constant all-zero triple. This is the single behavioural change the F2P
        # observes. Violates BOTH C4 (the sentinel pin) and C5 (the no-escape).
        "module": _arms(
            "Except.ok s",
            "Except.ok (pseudoTriple y m d)",
            "Except.error DateErr.valueEscaped"),
        "refinement": (
            "this is the literal pre-patch body: the too-large-magnitude outcome "
            "is left to escape the method uncaught rather than being turned into "
            "the constant all-zero triple. Its faithful real patch is the "
            "unpatched repo, on which the F2P overflow input (a component beyond "
            "the accepted magnitude range) escapes and the request crashes "
            "instead of producing the '0-0-0' text that the form then rejects "
            "with 'Enter a valid date.'. Both F2P tests (the widget's "
            "value-from-data mapping asserting '0-0-0', and the field test "
            "asserting the invalid-date message) FAIL. verify⇏resolve."),
        "rationale": (
            "REJECT from C5 (`∃ r, out = Except.ok r`) AND C4 (`outcome = "
            ".unrepresentable → out = Except.ok fallbackNoComponents`): an escape on the "
            "unrepresentable leg is `Except.error`, so no `r` makes `out = "
            "Except.ok r` and the sentinel pin is missed. This is the G-DIFF "
            "discriminator (the prepatch skeleton fails exactly here — mapping.md "
            "§2). Refuted at `['1'] ['2'] ['3'] unrepresentable`. If it verified "
            "=> SPEC-TOO-WEAK (admits the crash bug)."),
        "witness": _witness("['1'] ['2'] ['3'] ConstructOutcome.unrepresentable"),
    },
    {
        "id": "reject-wrong-sentinel-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Return a NEAR-MISS sentinel "0-0-1" on the unrepresentable outcome:
        # non-empty, no escape, but != fallbackNoComponents. Supporting case for the
        # exact-content pin C4.
        "module": _arms(
            "Except.ok s",
            "Except.ok (pseudoTriple y m d)",
            "Except.ok \"0-0-1\".toList"),
        "refinement": (
            "its faithful real patch returns a non-'0-0-0' constant (e.g. "
            "'0-0-1') on the too-large-magnitude outcome. The F2P widget test "
            "asserts the overflow input maps to exactly '0-0-0' verbatim, so it "
            "FAILS. verify⇏resolve."),
        "rationale": (
            "REJECT from the exact-content pin C4 (`outcome = .unrepresentable → "
            "out = Except.ok fallbackNoComponents`), fallbackNoComponents = \"0-0-0\".toList: "
            "\"0-0-1\".toList differs in the last code point, so it also violates "
            "C1. Supporting near-miss for the load-bearing sentinel clause. "
            "Refuted at `['9'] ['8'] ['7'] unrepresentable` — a distinct point "
            "from reject-let-value-escape (different components, same outcome). "
            "Ports nagini reject-wrong-sentinel-content. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness("['9'] ['8'] ['7'] ConstructOutcome.unrepresentable"),
    },
    {
        "id": "reject-empty-on-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the empty text on the unrepresentable outcome. Non-escaping (so
        # C5 holds) but empty != fallbackNoComponents, so it collapses the sentinel text
        # into an absent-looking value. Violates C4.
        "module": _arms(
            "Except.ok s",
            "Except.ok (pseudoTriple y m d)",
            "Except.ok []"),
        "refinement": (
            "its faithful real patch returns an empty string on the "
            "too-large-magnitude outcome. The F2P widget test asserts the "
            "overflow input maps to '0-0-0', not the empty string; the field "
            "would then report the value as absent (a 'required' error or a skip) "
            "instead of the invalid-date message the field test asserts. Resolves "
            "NEITHER F2P. verify⇏resolve."),
        "rationale": (
            "REJECT from C4 (`outcome = .unrepresentable → out = Except.ok "
            "fallbackNoComponents`): the empty text is Except.ok but != fallbackNoComponents, "
            "so it violates the sentinel pin (and C1). Ports nagini "
            "reject-empty-on-kind2. Refuted at `['a'] ['b'] ['c'] "
            "unrepresentable` — a third distinct point. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness("['a'] ['b'] ['c'] ConstructOutcome.unrepresentable"),
    },
    {
        "id": "reject-echo-fallback-on-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        # CROSS-BRANCH echo: on the unrepresentable outcome return the OTHER
        # branch's grounded text (the pseudo-ISO fallback built from the
        # components) instead of the constant all-zero triple. Non-empty, no
        # escape — passes C5 and every clause EXCEPT C4. The velvet analogue of
        # the nagini reject-echo-success-on-kind2 (wrong-but-non-empty, echoing
        # the wrong grounded branch).
        "module": _arms(
            "Except.ok s",
            "Except.ok (pseudoTriple y m d)",
            "Except.ok (pseudoTriple y m d)"),
        "refinement": (
            "its faithful real patch returns the pseudo-ISO fallback (the "
            "components joined by hyphens) on the too-large-magnitude outcome "
            "instead of the constant '0-0-0'. For an overflow input like a "
            "far-too-large component, the F2P widget test asserts exactly "
            "'0-0-0'; the fallback built from the actual components (e.g. "
            "'2-0-1') is a different, non-'0-0-0' string, so it FAILS. "
            "verify⇏resolve."),
        "rationale": (
            "REJECT from C4 (`outcome = .unrepresentable → out = Except.ok "
            "fallbackNoComponents`): pseudoTriple y m d is a grounded but DIFFERENT text "
            "from fallbackNoComponents whenever the components are not all the "
            "empty/zero shape, so it violates the sentinel pin (and C1). The true "
            "cross-branch-echo attack: it echoes the notCalendar branch's "
            "grounded text on the unrepresentable leg. Refuted at `['2'] ['0'] "
            "['1'] unrepresentable`, where pseudoTriple = \"2-0-1\" != \"0-0-0\". "
            "Ports nagini reject-echo-success-on-kind2. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness("['2'] ['0'] ['1'] ConstructOutcome.unrepresentable"),
    },
    {
        "id": "reject-swap-notcalendar-to-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # CROSS-BRANCH swap on the OTHER failure leg: on the notCalendar outcome
        # return the constant all-zero triple instead of the pseudo-ISO fallback.
        # Non-empty, no escape — passes C5, C2, C4, but violates C3. Guards the
        # unchanged ValueError-fallback branch (the branch the patch does NOT
        # change), so a rival collapsing it into the overflow sentinel is caught.
        "module": _arms(
            "Except.ok s",
            "Except.ok fallbackNoComponents",
            "Except.ok fallbackNoComponents"),
        "refinement": (
            "its faithful real patch returns the constant '0-0-0' on the "
            "not-a-calendar-date outcome (e.g. an out-of-range month/day) instead "
            "of the pseudo-ISO fallback the unchanged code produces. The P2P "
            "widget rows that submit such components assert the pseudo-ISO "
            "fallback ('%s-%s-%s'), not '0-0-0', so they FAIL — this branch is "
            "context the patch leaves untouched, so pinning it to the overflow "
            "sentinel is a behaviour change that does NOT resolve. verify⇏resolve."),
        "rationale": (
            "REJECT from C3 (`outcome = .notCalendar → out = Except.ok "
            "(pseudoTriple y m d)`): fallbackNoComponents != pseudoTriple y m d whenever "
            "the components are not the empty/zero shape, so it violates the "
            "fallback pin (and C1). Attacks the notCalendar leg — a DISTINCT "
            "top-level clause from the unrepresentable rivals, varying `outcome` "
            "to .notCalendar. Refuted at `['1'] ['2'] ['3'] notCalendar`, where "
            "pseudoTriple = \"1-2-3\" != \"0-0-0\". No direct nagini sibling (the "
            "nagini kind-1 oracle is abstract @ContractOnly); ADDED to attack the "
            "transparent fallback clause. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness("['1'] ['2'] ['3'] ConstructOutcome.notCalendar"),
    },
    {
        "id": "reject-fallback-drops-day",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the notCalendar fallback: build the pseudo-ISO triple
        # but DROP the day component (use `[]` in its place). Correct on every
        # input whose day component is already empty; diverges on any non-empty
        # day. Demonstrates the `d` binder is LOAD-BEARING in C3.
        "module": _arms(
            "Except.ok s",
            "Except.ok (pseudoTriple y m [])",
            "Except.ok fallbackNoComponents"),
        "refinement": (
            "its faithful real patch builds the pseudo-ISO fallback from only the "
            "first two components, dropping the day (rendering it as the empty "
            "component's zero). The P2P widget rows that submit a non-empty day "
            "assert the fallback carrying that day's own text, not a zero, so "
            "they FAIL. verify⇏resolve. A genuine partial-domain break — correct "
            "on every empty-day input."),
        "rationale": (
            "REJECT from C3 (`outcome = .notCalendar → out = Except.ok "
            "(pseudoTriple y m d)`): pseudoTriple y m [] differs from pseudoTriple "
            "y m d at every non-empty day component, so it violates the fallback "
            "pin (and C1). This is the sub-domain that proves the `d` binder is "
            "LOAD-BEARING in the fallback text — a rival mishandling only the day "
            "is caught by no other witness. Refuted at `['5'] ['6'] ['4'] "
            "notCalendar`, where pseudoTriple y m d = \"5-6-4\" but pseudoTriple y "
            "m [] = \"5-6-0\". ADDED (nagini's abstract kind-1 oracle cannot "
            "express this per-component break). If it verified => SPEC-TOO-WEAK "
            "(the fallback's day component unpinned)."),
        "witness": _witness("['5'] ['6'] ['4'] ConstructOutcome.notCalendar"),
    },
    {
        "id": "reject-fallback-drops-empty-normalization",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the fallback by joining the three components RAW, without the
        # per-component empty->'0' normalization. Correct on every triple whose
        # three components are all non-empty; wrong exactly when a component is
        # EMPTY. Added by audit: every other reject witness probes only NON-empty
        # components, so `orZero`'s empty branch — a clause the transparent
        # fallback genuinely carries — was pinned by no concrete point.
        "module": _arms(
            "Except.ok s",
            "Except.ok (y ++ ['-'] ++ m ++ ['-'] ++ d)",
            "Except.ok fallbackNoComponents"),
        "refinement": (
            "its faithful real patch joins the three components directly, "
            "dropping the per-component empty-shows-as-zero coercion. The P2P "
            "widget rows that leave exactly one of the three components blank "
            "assert a fallback carrying a zero in that position, not a collapsed "
            "double separator, so they FAIL. verify⇏resolve. A genuine "
            "partial-domain break — correct on every all-non-empty triple."),
        "rationale": (
            "REJECT from C3 (`outcome = .notCalendar → out = Except.ok "
            "(pseudoTriple y m d)`): pseudoTriple normalizes each component via "
            "`orZero` (empty ↦ ['0']), so the raw join differs from it at every "
            "triple with an empty component (and thus violates C1). This is the "
            "sub-domain that proves `orZero`'s EMPTY branch is load-bearing — no "
            "other witness in this battery supplies an empty component. Refuted "
            "at `[] ['1'] ['2'] notCalendar`, where pseudoTriple = \"0-1-2\" but "
            "the raw join is \"-1-2\". ADDED by audit. If it verified => "
            "SPEC-TOO-WEAK (the empty-component normalization unpinned)."),
        "witness": _witness("[] ['1'] ['2'] ConstructOutcome.notCalendar"),
    },
    {
        "id": "reject-escape-on-notcalendar",
        "kind": "uniqueness",
        "expect": "reject",
        # Let a value ESCAPE on the notCalendar leg instead of returning the
        # pseudo-ISO fallback. Added by audit: C5 (the no-escape contract) was
        # attacked on the `unrepresentable` leg ONLY, so an impl that returns a
        # value there but escapes on the OTHER failure leg was unprobed. C5 is
        # quantified over every outcome, and this rival shows it.
        "module": _arms(
            "Except.ok s",
            "Except.error DateErr.valueEscaped",
            "Except.ok fallbackNoComponents"),
        "refinement": (
            "its faithful real patch guards the too-large-magnitude outcome but "
            "leaves the components-name-no-representable-value outcome to escape "
            "uncaught. The P2P widget rows that submit such components assert the "
            "pseudo-ISO fallback text; instead the request crashes, so they FAIL "
            "— and the branch that escapes is context this change leaves "
            "untouched. verify⇏resolve."),
        "rationale": (
            "REJECT from C5 (`∃ r, out = Except.ok r`) AND C3 (`outcome = "
            ".notCalendar → out = Except.ok (pseudoTriple y m d)`): an escape is "
            "`Except.error`, so no `r` makes `out = Except.ok r` on this leg and "
            "the fallback pin is missed. Shows C5 is load-bearing on EVERY "
            "outcome, not just the one reject-let-value-escape attacks. Refuted "
            "at `['4'] [] ['7'] notCalendar` — a point that also carries an empty "
            "component. ADDED by audit. If it verified => SPEC-TOO-WEAK (the "
            "no-escape contract pinned on one leg only)."),
        "witness": _witness("['4'] [] ['7'] ConstructOutcome.notCalendar"),
    },
    {
        "id": "reject-ignore-rendered-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # On the `rendered s` outcome IGNORE the rendered payload and return the
        # constant all-zero triple. Non-empty, no escape — passes C5, C3, C4, but
        # violates C2 (the rendered text must be echoed back verbatim). The velvet
        # analogue of the nagini reject-swap-text-on-kind0 (cross-branch echo on
        # the success path).
        "module": _arms(
            "Except.ok fallbackNoComponents",
            "Except.ok (pseudoTriple y m d)",
            "Except.ok fallbackNoComponents"),
        "refinement": (
            "its faithful real patch returns the constant '0-0-0' on the "
            "successful-render outcome instead of the rendered date text. For a "
            "valid date the P2P widget/round-trip rows assert the canonical "
            "rendered date, not '0-0-0', so they FAIL. verify⇏resolve."),
        "rationale": (
            "REJECT from C2 (`∀ s, outcome = .rendered s → out = Except.ok s`): "
            "the rendered payload `s` must be echoed back, but this returns the "
            "constant fallbackNoComponents, which is not `s` for a rendered payload "
            "other than the all-zero triple, so it violates C2 (and C1). Attacks "
            "the rendered leg — the third top-level clause, varying `outcome` to "
            ".rendered. Refuted at `['7'] ['8'] ['9'] (rendered ['x'])`, where "
            "the payload ['x'] != fallbackNoComponents. Ports nagini "
            "reject-swap-text-on-kind0. If it verified => SPEC-TOO-WEAK (the "
            "rendered echo unpinned)."),
        "witness": _witness("['7'] ['8'] ['9'] (ConstructOutcome.rendered ['x'])"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts the WHOLE `value_from_components(all_blank,
# all_present, kind)` — the all-blank fast path, the not-all-present raw-retrieval
# fallback, AND the all-present kind 0/1/2 sub-branches. This velvet bundle models
# ONLY the all-three-present inner routing of `ConstructOutcome` (mapping.md §1:
# the patch hunk lives entirely inside the all-present try/except). That is
# carrier narrowing: the three nagini rivals attached to the UNMODELED outer
# branches have no counterpart here. `rendered`/`notCalendar`/`unrepresentable`
# correspond to the nagini kind 0 / kind 1 / kind 2 all-present outcomes.
#
#   nagini case                        -> here                              disposition
#   -----------------------------------------------------------------------------------
#   pos-reorder                        -> pos-control-reorder-arms          PORTED
#                                         (+ pos-control-direct              ADDED)
#   admiss-f2p                         -> admiss-gold-total                  RE-AIMED
#   reject-drop-overflow-handler       -> reject-let-value-escape           PORTED
#   reject-echo-success-on-kind2       -> reject-echo-fallback-on-unrep     RE-EXPRESSED
#   reject-wrong-sentinel-content      -> reject-wrong-sentinel-content     PORTED
#   reject-empty-on-kind2              -> reject-empty-on-unrep             PORTED
#   reject-swap-text-on-kind0          -> reject-ignore-rendered-payload    RE-EXPRESSED
#   reject-nonempty-not-all-present    -> (none)                            UNMODELED (carrier)
#   reject-empty-literal-not-all-present -> (none)                          UNMODELED (carrier)
#   reject-nonempty-all-blank          -> (none)                            UNMODELED (carrier)
#   (no sibling)                       -> reject-swap-notcalendar-to-sentinel ADDED
#   (no sibling)                       -> reject-fallback-drops-day         ADDED
#   (no sibling)  -> reject-fallback-drops-empty-normalization  ADDED (audit)
#   (no sibling)  -> reject-escape-on-notcalendar               ADDED (audit)
#   AXIOM_TESTS (2)                    -> (none)                            DROPPED (G-AX lane)
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness. Every nagini
# case that attacks a clause THIS bundle models is ported or re-expressed; three
# are legitimately UNMODELED (their branch is outside this method); two are ADDED
# to attack the transparent notCalendar-fallback clause the nagini abstract oracle
# could not reach concretely.
#
# PORTED / RE-EXPRESSED:
#   reject-drop-overflow-handler -> reject-let-value-escape: the exact pre-patch
#     shape — the too-large-magnitude outcome escapes uncaught instead of
#     returning the constant sentinel. On this carrier the escape is
#     `Except.error .valueEscaped` (mapping.md §2), so the no-Exsures contract is
#     modeled as C5 (`∃ r, out = Except.ok r`) plus C4; the rival violates both.
#     THE core G-DIFF case.
#   reject-echo-success-on-kind2 -> reject-echo-fallback-on-unrep: the nagini
#     rival echoes the SUCCESS branch's grounded text on kind 2. On this carrier
#     the `rendered s` payload is not available inside the unrepresentable arm, so
#     the faithful cross-branch echo is the notCalendar branch's grounded
#     `pseudoTriple y m d` — a non-empty, non-escaping wrong value on the overflow
#     leg, the same "wrong-but-non-empty on the sentinel domain" attack.
#   reject-swap-text-on-kind0 -> reject-ignore-rendered-payload: the nagini rival
#     returns the wrong grounded branch's text on the SUCCESS path. Here the
#     success path echoes the opaque payload `s` (C2); the rival ignores `s` and
#     returns the constant sentinel — the same "echo the wrong grounded oracle on
#     the success branch" attack, now against C2.
#   reject-wrong-sentinel-content, reject-empty-on-kind2: carry across intact
#     (near-miss "0-0-1" and empty text on the sentinel domain), only the carrier
#     changes from a nagini `List[int]` to a Velvet `List Char`.
#
# RE-AIMED (admiss-f2p -> admiss-gold-total): the nagini case self-calls to show
#   the precondition admits the F2P overflow input. This method has NO `require`,
#   so nothing can exclude any input and that probe is vacuous; re-aimed at the
#   residual total-domain risk (post-image joint satisfiability), witnessed by the
#   frozen impl discharging all five ensures — including the F2P-shaped
#   unrepresentable leg pinning the sentinel and the no-escape.
#
# ADDED (2): reject-swap-notcalendar-to-sentinel and reject-fallback-drops-day
#   attack C3, the notCalendar (ValueError-fallback) clause. The nagini file pins
#   kind 1 to the ABSTRACT @ContractOnly out_of_range_text() oracle (len>0 only),
#   so it can only catch a cross-branch swap implicitly. Here the fallback is the
#   TRANSPARENT `pseudoTriple y m d`, so it is attackable concretely: swap it to
#   the overflow sentinel (which also demonstrates the notCalendar leg is pinned
#   independently of the unrepresentable leg), and drop the day component (which
#   demonstrates the `d` binder is load-bearing in the fallback text). Real
#   divergences with machine-checked witnesses, not fabricated wrongness.
#
# UNMODELED (3, carrier narrowing — NOT dropped for difficulty):
#   reject-nonempty-not-all-present, reject-empty-literal-not-all-present, and
#   reject-nonempty-all-blank all attack the OUTER framing of value_from_datadict
#   (the not-all-present `return data.get(name)` fallback and the all-blank
#   short-circuit). mapping.md §1 records that framing as unchanged context the
#   patch does NOT touch and this bundle does NOT model — `dateComponentsText`
#   models only the all-present inner try/except. There is no spec clause here for
#   those branches, so there is no rival to write; fabricating one would attack a
#   behaviour this bundle does not model. Legitimately omitted per the porting map
#   (most nagini cases attached to an unmodeled behaviour have no counterpart).
#
# FRAME-MUTATION: VACUOUS. The nagini three params (bool, bool, int) are primitive
#   value types passed by value with no Acc(.,1/2) read-only input, and the nagini
#   sibling itself records the class structurally N/A. Velvet is referentially
#   transparent besides: y/m/d/outcome are immutable values, no `mut`, no heap, no
#   aliasing, no permission system. No read-only input to overwrite; no substitute
#   fabricated.
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
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness/containment probes
#   over the real datetime.date callee are G-AX's job (axiom_check.py /
#   mapping.md); the G-PBT gate ignores AXIOM_TESTS regardless. This bundle also
#   declares no consumed axiom (ConstructOutcome is a free input, mapping.md §3).
#
# CLAUSE / BINDER / POINT COVERAGE. C1 (`out = dateText y m d outcome`) is the
#   whole pin; C2/C3/C4 are its three per-outcome projections and C5 the no-escape
#   contract. Every independent clause is attacked: C2 rendered
#   (reject-ignore-rendered-payload), C3 notCalendar
#   (reject-swap-notcalendar-to-sentinel, reject-fallback-drops-day,
#   reject-fallback-drops-empty-normalization), C4 unrepresentable-content
#   (reject-wrong-sentinel-content, reject-empty-on-unrep,
#   reject-echo-fallback-on-unrep), and C5 no-escape + C4
#   (reject-let-value-escape) / C5 + C3 (reject-escape-on-notcalendar). C5 is thus
#   attacked on BOTH failure legs, not just the unrepresentable one.
#   The four input binders are all varied by the reject
#   witnesses: `outcome` ranges over all three constructors (.rendered, .notCalendar,
#   .unrepresentable); `y`/`m`/`d` each range over several NON-empty texts AND the
#   EMPTY component (`[]`), so `orZero`'s two branches are both pinned: the `d`
#   binder is demonstrated LOAD-BEARING by reject-fallback-drops-day, and the
#   empty-component normalization by reject-fallback-drops-empty-normalization
#   (refuted at `[] ['1'] ['2']`, where the raw join drops a zero the fallback
#   requires). The nine reject witnesses probe nine DISTINCT input points; no
#   binder is held at a single value or a single shape across the reject set. Both
#   positives and the admissibility case defend all five clauses (all discharge on
#   gold).
#
# AUDIT ADDENDA (independent re-derivation, all builds re-run):
#   * Attack A (statement integrity): every case's module diffed against the
#     frozen file. Each diff is confined to the impl region (pos-control-direct
#     additionally retunes the prove_correct tactic body, which the spec view
#     elides); admiss-gold-total is byte-identical. No statement reformatted.
#   * Attack B (witness discrimination): all seven original witnesses rebuilt on
#     both sides. Rival exit 0, gold exit 1 in every case, and every gold-side
#     failure is a KERNEL-EVALUATED refutation — "Tactic `decide` proved that the
#     proposition ... is false" — never a stuck reduction, unknown identifier,
#     type error, or timeout. No witness binds a hypothesis, so no consistency
#     probe applies.
#   * Attack D (SPEC-TOO-WEAK probe): six NEW wrong impls the battery did not
#     contain — raw fallback join (no empty normalization), fallback with the
#     components reversed, rendered leg swapped to the fallback, escape on the
#     notCalendar leg, sentinel truncated to a "0-0" prefix, and the two failure
#     legs swapped wholesale. ALL SIX were rejected, each with a witness that
#     elaborates against the rival and is semantically refuted on gold. No spec
#     hole. The two that probed genuinely unattacked sub-domains were promoted
#     into this battery as the two ADDED (audit) cases above.
#   * Attack E (SPEC-TOO-STRONG probe): four NEW correct reshapes — an if-ladder
#     over DecidableEq collapsing the two failure arms, both pure defs
#     inline-expanded to raw char-list literals, the sentinel computed as
#     `pseudoTriple [] [] []` instead of named, and a two-stage staging that
#     binds both texts to locals first. ALL FOUR VERIFY. Three needed a retuned
#     tactic body (the frozen `cases outcome <;> simp_all` leaves residual goals
#     on a reshaped `match`); that is a tactic gap, not a spec rejection, and the
#     retune closes it with `all_goals (cases outcome <;> simp_all [dateText,
#     pseudoTriple, orZero, fallbackNoComponents])`. The spec admits every faithful
#     correct reshape tried.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (C2's `∀ s` and C5's `∃ r`
#   make the postcondition's Decidable instance noncomputable, so
#   `derive_tester_for` yields a stuck `dateComponentsTextTester`). Every witness
#   instead extracts the executable program and refutes C1 directly against the
#   TRANSPARENT `dateText`, projecting `Except` to `Option (List Char)` (no
#   `DecidableEq` for `Except`) so `decide` settles the `≠`. Each rival is
#   loop-free so its `…Exec` reduces under `decide`; against gold the projected
#   sides are identical so the `≠` is decidably false and `decide` fails — the
#   required FAIL-on-gold half. No witness binds a hypothesis, so no consistency
#   probe is needed. All NINE checked with scripts/lean_verify.sh: rival exit 0
#   (no errors), gold exit 1 with `Tactic `decide` proved that the proposition …
#   is false` — a semantic refutation the kernel actually evaluated, not a stuck
#   reduction or a missing name.
AXIOM_TESTS = []
