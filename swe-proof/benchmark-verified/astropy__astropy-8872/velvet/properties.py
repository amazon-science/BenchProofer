"""properties.py — G-PBT falsification battery for astropy__astropy-8872 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches ONLY text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside an elided ``prove_correct`` tactic body, both of
which the consumer spec view elides, so ``markers.same_spec`` holds by
construction and both ``prove_correct`` headers survive. It is then checked by the
real verifier: ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. Two contracted methods over ONE modeled carrier, the
categorical element-type ``ElemType`` of an array offered for construction:

  resolveElemGeneral (input : ElemType) return (out : ElemType)
    ensures out = resultElemGeneral input                    -- the value clause
    ensures input = .integral → out = .floatDouble           -- 9 per-category arms
    ...                                                      --   (one per ctor)
    ensures isFloating out = true ↔                          -- the family clause
      (isFloating input = true ∨ input = .integral ∨ input = .object)

  resolveElemFast (input : ElemType) return (out : ElemType)
    ensures out = resultElemFast input                       -- the value clause
    ensures input = .integral → out = .floatDouble           -- 9 per-category arms
    ...
    ensures isFloating out = true ↔                          -- the family clause
      (isFloating input = true ∨ input = .integral)

Each method decides, from the input element-type ALONE, the element-type the
resulting array is materialized under. Both are total, side-effect-free, and
declare no ``require`` clause, so every one of the nine ``ElemType`` constructors
is an admissible input and no witness can be vacuously excluded by a false
precondition. There is exactly ONE input binder per obligation (``input``), and it
is FREE — the two methods differ only in which categories convert.

THE DISCRIMINATOR the modeled behavior turns on: the decision is a function of the
element-type's CATEGORY, never of its storage WIDTH. Every real floating category
— narrowest, single, double, and wider-than-double — is preserved at its own
width; only the whole-number category (and, on the general path, the
individually-boxed-object category) is re-materialized under the default
double-width floating element-type. A narrow floating input keeping its own width
is exactly the behavior the failing test asserts, and the categorical dispatch is
what makes width irrelevant.

Because ``resultElemGeneral`` / ``resultElemFast`` are fully-unfolded ``def``s over
the method's own argument (empty ``axioms`` region, no opaque callee, no A-tagged
reference), the carrier is entirely TRANSPARENT: every witness below states its
refutation at a concrete ``ElemType`` literal and closes under ``decide``. No
witness needs to condition on the carrier by hypothesis, so no witness binds
anything and the consistency probe is not reached — there are no assumptions that
could be jointly unsatisfiable.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting in
the footer):

  * PARTIAL-DOMAIN / VALUE — heavily exercised, and the whole battery. The
    sibling's width-keyed rival, its convert-too-much rivals, and its
    convert-too-little rivals all port, but the sibling's three-field
    ``(kind, width-flag, composite-flag)`` carrier collapses here into one
    categorical binder whose nine values the spec names INDIVIDUALLY. So the port
    is not a translation of seven rivals: it is one rival per ``ensures`` arm per
    obligation, each retargeting exactly ONE match arm and correct on the other
    eight categories.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to a concrete ``def`` over the method's own argument; there is no
    opaque answer key to echo. The honest cheapest impl (return the model
    directly) is therefore a positive control, included below.
  * FRAME / PERMISSION-MUTATION — VACUOUS, and the sibling already records it as
    vacuous on its own side (all its parameters are plain value-type ints/bools
    passed by value, touching no heap, so there is no read-only cell to
    overwrite). This backend is referentially transparent a fortiori: ``input`` is
    an immutable value, neither method declares a ``mut`` binder, and there is no
    heap and no aliasing. No substitute probe is fabricated.
  * CONTROL-FLOW-EFFECT — N/A, as the sibling records. Both methods are total,
    raise nothing, and the returned element-type is the whole observable.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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

WITNESS MECHANICS. The spec is a ``method`` contract, not a bare predicate, so
each witness reaches the post-image through Velvet's own tester machinery:
``<base>Tester <input> = false`` says the extracted program's result violates the
postcondition at that concrete element-type. It is checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can mask the
verdict. Both halves of every witness below were checked out-of-band with real
``scripts/lean_verify.sh`` builds: each ELABORATES against its own rival (the
tester ``decide``s to ``false``) and FAILS against the frozen solution (gold's
tester ``decide``s to ``true``, so ``= false`` is refuted with ``Tactic `decide`
proved that the proposition ... is false``). Neither method declares a ``require``
clause, so no witness input is short-circuited to ``true``.

Note why the witness is load-bearing here and the module build alone is not: each
rival leaves the frozen tactic script in place, so the rival module fails with
``unsolved goals`` — which a merely RESHAPED-but-correct impl would also produce.
The witness, not the module build, is what attributes each rejection to the spec.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(the decision is computed solely from the input element-type), so there is nothing
to probe; this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-8872"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two dispatch tables, verbatim. Both lie ENTIRELY inside their method's
# `-- impl-start` / `-- impl-end` region and each is unique in the file, so every
# `_swap` below edits only the elided impl region. The manifest breaks loudly if
# the frozen solution ever changes.
# ---------------------------------------------------------------------------
_GENERAL_ARMS = """      | .integral     => .floatDouble
      | .object       => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .structured   => .structured"""

_FAST_ARMS = """      | .integral     => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .object       => .object
      | .structured   => .structured"""

if _BASE.count(_GENERAL_ARMS) != 1:
    raise AssertionError("general-path dispatch table drifted")
if _BASE.count(_FAST_ARMS) != 1:
    raise AssertionError("fast-path dispatch table drifted")

# The whole `let`-bound dispatch plus its `return`, for the reshape positives.
_GENERAL_BODY = ("    let result : ElemType :=\n      match input with\n"
                 + _GENERAL_ARMS + "\n    return result")
_FAST_BODY = ("    let result : ElemType :=\n      match input with\n"
              + _FAST_ARMS + "\n    return result")

if _BASE.count(_GENERAL_BODY) != 1 or _BASE.count(_FAST_BODY) != 1:
    raise AssertionError("dispatch body shape drifted")

# The frozen proofs, verbatim. Rivals leave these untouched (so the wrong impl
# leaves the postcondition goal unsolved and the rival module fails to build,
# which is what expect="reject" requires); the admissibility case retunes the
# general-path one ONLY to clear its extra in-region `assert` goal. Both bodies
# are elided from the spec view, and both `prove_correct` headers survive.
_PROOF_GENERAL = ("prove_correct resolveElemGeneral by\n  loom_solve <;>\n"
                  "    cases input <;>\n      simp_all [resultElemGeneral, "
                  "castsToFloatGeneral, defaultFloat, isFloating]")

if _BASE.count(_PROOF_GENERAL) != 1:
    raise AssertionError("general-path proof region drifted")


def _one_arm(table, ctor, rhs):
    """`table` with EXACTLY ONE match arm retargeted to `rhs`."""
    out, hits = [], 0
    for line in table.split("\n"):
        if line.strip().startswith(f"| .{ctor} "):
            out.append(line.split("=>")[0] + "=> " + rhs)
            hits += 1
        else:
            out.append(line)
    if hits != 1:
        raise AssertionError(f"arm {ctor!r} matched {hits} times")
    return "\n".join(out)


def _general(ctor, rhs):
    """Rival: the general-path table with one arm retargeted."""
    return _swap(_BASE, _GENERAL_ARMS, _one_arm(_GENERAL_ARMS, ctor, rhs))


def _fast(ctor, rhs):
    """Rival: the fast-path table with one arm retargeted."""
    return _swap(_BASE, _FAST_ARMS, _one_arm(_FAST_ARMS, ctor, rhs))


def _witness(base, point):
    """A refutation at ONE concrete element-type, via the derived tester.

    The spec is a `method` contract, so the post-image is reached through
    Velvet's tester machinery rather than as a bare predicate. Checked in a file
    whose `prove_correct` blocks are stripped; the frozen impl and every rival
    are loop-free categorical dispatches, so both testers reduce under `decide`.
    """
    return (f"extract_program_for {base}\n"
            f"prove_precondition_decidable_for {base}\n"
            f"prove_postcondition_decidable_for {base}\n"
            f"derive_tester_for {base}\n\n"
            f"example : {base}Tester {point} = false := by\n  decide\n")


# The admissibility probe's claim: every modeled category is in-domain AND the
# post-image is NON-DEGENERATE there — three distinct floating widths each
# preserved as themselves (not collapsed onto one width), both converting
# categories landing on the default, and the fast path preserving two categories
# the general path converts or preserves differently. A constant or
# width-collapsing post-image would falsify it.
_ADMISS_CLAIM = (
    "    assert (with_name_prefix `admiss\n"
    "      (resultElemGeneral .floatHalf = .floatHalf ∧\n"
    "       resultElemGeneral .floatSingle = .floatSingle ∧\n"
    "       resultElemGeneral .floatExtended = .floatExtended ∧\n"
    "       resultElemGeneral .integral = .floatDouble ∧\n"
    "       resultElemGeneral .object = .floatDouble ∧\n"
    "       resultElemFast .floatHalf = .floatHalf ∧\n"
    "       resultElemFast .boolean = .boolean ∧\n"
    "       resultElemFast .object = .object ∧\n"
    "       resultElemFast .integral = .floatDouble))\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVES — structurally different but CORRECT impls that MUST
    # verify, else the spec is SPEC-TOO-STRONG. All four keep the frozen proof
    # script unchanged and were confirmed to verify with real builds.
    # =====================================================================
    {
        "id": "pos-model-general",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GENERAL_BODY,
                        "    return resultElemGeneral input"),
        "rationale": "the honest cheapest CORRECT impl on the general path: it "
                     "returns the pure post-image model directly instead of "
                     "spelling out the categorical dispatch. Observationally "
                     "identical on all nine categories, so the value clause "
                     "`out = resultElemGeneral input`, every per-category arm, "
                     "and the isFloating family clause all hold on the whole "
                     "domain. This is the ungrounded-oracle case's positive "
                     "counterpart: because the post-image is a fully-unfolded "
                     "def over the method's own argument (not an opaque answer "
                     "key), returning it IS doing the work. Must verify, else "
                     "the postcondition rejects its own model's output.",
    },
    {
        "id": "pos-model-fast",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FAST_BODY, "    return resultElemFast input"),
        "rationale": "the same reshape on the FAST-path obligation, so that "
                     "obligation is independently DEFENDED rather than covered "
                     "only by the general-path positive. Returns the fast-path "
                     "post-image model directly; identical on all nine "
                     "categories, so `out = resultElemFast input`, every "
                     "per-category arm, and the fast family clause hold "
                     "everywhere. Must verify.",
    },
    {
        "id": "pos-arm-reorder-general",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GENERAL_ARMS,
            "      | .structured   => .structured\n"
            "      | .complexFloat => .complexFloat\n"
            "      | .boolean      => .boolean\n"
            "      | .floatExtended => .floatExtended\n"
            "      | .floatDouble   => .floatDouble\n"
            "      | .floatSingle   => .floatSingle\n"
            "      | .floatHalf     => .floatHalf\n"
            "      | .object       => .floatDouble\n"
            "      | .integral     => .floatDouble"),
        "rationale": "branch-REORDER positive control: the nine dispatch arms "
                     "are listed in fully reversed order, converting categories "
                     "last instead of first. The arms are disjoint so the "
                     "mapping is unchanged — identical values, different "
                     "control-flow shape. Must verify; a rejection here would "
                     "mean the spec pins the dispatch ORDER rather than the "
                     "decision, which is not behavior any test can observe.",
    },
    {
        "id": "pos-predicate-ladder-both",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GENERAL_BODY,
                  "    let converts : Bool := castsToFloatGeneral input\n"
                  "    if converts then\n      return defaultFloat\n"
                  "    else\n      return input"),
            _FAST_BODY,
            "    let converts : Bool := castsToFloatFast input\n"
            "    if converts then\n      return defaultFloat\n"
            "    else\n      return input"),
        "rationale": "BOTH obligations reshaped at once, and to a different "
                     "shape than the dispatch table: each computes the "
                     "per-path conversion test into a local Bool, then branches "
                     "on it — two early `return`s instead of one `let`-bound "
                     "result, so the control flow really differs rather than "
                     "just the arm order. Semantically identical on all nine "
                     "categories per path. The frozen spec must admit a "
                     "faithful full-module rewrite; must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe asserts the precondition admits the
    # failing-test-shaped witness inputs. Neither method here declares a
    # `require` clause, so admissibility of the INPUT is trivial and probing it
    # would assert nothing. The residual risk this backend actually carries is
    # POST-IMAGE DEGENERACY: a post-image that collapsed the floating widths onto
    # one representative, or was constant, would satisfy every arm read
    # individually while making the width-preservation the failing test asserts
    # unobservable. So the probe is re-aimed at non-degeneracy, pinned by ONE
    # in-region assert. Confirmed LIVE during authoring: substituting a FALSE
    # claim leaves `decide` refusing the goal (`decide proved that the
    # proposition False is false`), so the assert is not trivially discharged.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-postimage",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GENERAL_BODY, _ADMISS_CLAIM + _GENERAL_BODY),
            _PROOF_GENERAL, _PROOF_GENERAL + "\n  all_goals decide"),
        "rationale": "both obligations are satisfiable at real inputs AND their "
                     "post-images are NON-DEGENERATE: three distinct floating "
                     "widths are each preserved as THEMSELVES (narrowest, "
                     "single, and wider-than-double all map to themselves, not "
                     "collapsed onto one width), both converting categories land "
                     "on the default double width, and the fast path preserves "
                     "two categories the general path treats differently — so "
                     "the two obligations are genuinely distinct and neither is "
                     "a constant or width-collapsing map. A degenerate "
                     "post-image would satisfy each per-category arm read alone "
                     "while making width preservation unobservable. The impl is "
                     "kept verbatim so each method's own `ensures` still "
                     "discharges; the general-path proof is retuned ONLY to "
                     "clear the extra assert goal (an elided tactic body — both "
                     "`prove_correct` headers survive).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each retargets EXACTLY ONE arm of one
    # dispatch table and is correct on the other eight categories — a
    # single-category partial-domain miss, the strictest near-miss this carrier
    # admits. Every rival carries a machine-checked witness at the one category
    # where it diverges, and every one of the nine categories appears as some
    # witness's input point on BOTH obligations, so the single input binder is
    # varied across its whole modeled domain rather than probed at one value.
    # =====================================================================

    # ---- general path -------------------------------------------------
    {
        "id": "weak-general-half-widened",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("floatHalf", ".floatDouble"),
        "refinement": "THE headline defect, reborn as a same-spec rival: the "
                      "narrowest real floating category is re-materialized under "
                      "the default double width instead of being preserved. Its "
                      "faithful real counterpart is precisely the behavior the "
                      "issue reports — a narrow-width float input silently "
                      "coming back at double width. The failing test constructs "
                      "an array of exactly that element-type and asserts the "
                      "result carries the SAME element-type, so this counterpart "
                      "fails that assertion outright and does NOT resolve.",
        "rationale": "REJECT from the value clause `out = resultElemGeneral "
                     "input`, from the per-category arm `input = .floatHalf → "
                     "out = .floatHalf`, and from the family clause (which pins "
                     "floating-ness but not width, so the arm is what catches "
                     "this): at input = .floatHalf the rival returns "
                     ".floatDouble while the post-image returns .floatHalf. "
                     "Verifying would be SPEC-TOO-WEAK — the width-preservation "
                     "the fix establishes would be unpinned. Refuted at the "
                     ".floatHalf input point.",
        "witness": _witness("resolveElemGeneral", ".floatHalf"),
    },
    {
        "id": "weak-general-bool-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("boolean", ".floatDouble"),
        "refinement": "the second half of the same pre-fix predicate: a "
                      "truth-valued input is also converted to the default "
                      "floating width, because it too fails a "
                      "'can this type hold the reference width' test. Note this "
                      "rival reproduces the PRE-fix treatment of the boolean "
                      "category exactly, so — unlike the wider/narrower float "
                      "rivals — it does not regress anything that passes "
                      "beforehand; boolean preservation is new behavior the fix "
                      "establishes alongside narrow-float preservation. It is "
                      "shipped because the frozen spec pins that new arm "
                      "(`input = .boolean → out = .boolean`), so a counterpart "
                      "that kept converting booleans leaves a category the fix "
                      "settles unpinned and does NOT resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .boolean → out = .boolean`: at input = .boolean "
                     "the rival returns .floatDouble, the post-image .boolean. "
                     "A distinct single-category miss from the narrow-float "
                     "rival — it agrees with gold on every floating width — so "
                     "it needs and gets its own input point, .boolean.",
        "witness": _witness("resolveElemGeneral", ".boolean"),
    },
    {
        "id": "weak-general-single-widened",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("floatSingle", ".floatDouble"),
        "refinement": "a counterpart that widened the SINGLE-width floating "
                      "category to the default would regress behavior that "
                      "holds before the fix: the pre-fix predicate already "
                      "preserves a single-width input (it is not narrower than "
                      "the single-width reference), so converting it is a "
                      "regression the fix never asks for, on top of failing to "
                      "establish the new narrow-width behavior. No existing "
                      "element-type test exercises this width directly — the "
                      "argument is from the pre-fix predicate and the frozen "
                      "arm, not from test appeal. It does NOT resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .floatSingle → out = .floatSingle`: at "
                     "input = .floatSingle the rival returns .floatDouble. This "
                     "is the NEAR-MISS the narrow-float rival does not subsume "
                     "— it agrees with gold on the narrowest width and diverges "
                     "only one width up — so it is refuted at its own input "
                     "point, .floatSingle, demonstrating the spec pins EVERY "
                     "floating width and not just the narrowest one.",
        "witness": _witness("resolveElemGeneral", ".floatSingle"),
    },
    {
        "id": "weak-general-extended-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("floatExtended", ".floatDouble"),
        "refinement": "the mirror direction: a counterpart that re-materialized "
                      "a WIDER-than-default floating input under the default "
                      "would silently lose precision. The pre-fix predicate "
                      "already preserves a wider-than-double input, so this is "
                      "a regression of behavior that holds beforehand rather "
                      "than a failure to establish the new behavior; no "
                      "existing element-type test exercises a wider-than-double "
                      "input, so the argument rests on the pre-fix predicate and "
                      "the frozen arm, not on test appeal. It would not "
                      "resolve. Included because a width-keyed predicate could "
                      "plausibly be mis-fixed in the widening direction too.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .floatExtended → out = .floatExtended`: at "
                     "input = .floatExtended the rival returns .floatDouble. "
                     "Attacks the arm on the OTHER side of the default width "
                     "from the narrow-float rivals, at its own input point.",
        "witness": _witness("resolveElemGeneral", ".floatExtended"),
    },
    {
        "id": "weak-general-double-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("floatDouble", ".floatSingle"),
        "refinement": "a counterpart that handed a double-width floating input "
                      "back at single width would narrow it — losing precision "
                      "on the most common floating input of all, which the "
                      "pre-fix predicate already preserves. Existing "
                      "precision-sensitive display assertions would observe the "
                      "narrowing (a double-width value printed at full "
                      "precision differs from its single-width rounding), so "
                      "this regresses behavior that holds beforehand. It would "
                      "not resolve. This is the one rival whose result is NOT the "
                      "default width, so it probes that the arm pins the "
                      "identity rather than merely 'some floating width'.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .floatDouble → out = .floatDouble`: at "
                     "input = .floatDouble the rival returns .floatSingle. Note "
                     "the family clause `isFloating out = true ↔ ...` is "
                     "SATISFIED by this rival (both sides are floating), so the "
                     "rejection is attributable to the per-category arm and the "
                     "value clause specifically — which is exactly what makes "
                     "this rival worth shipping: it demonstrates the family "
                     "clause alone would be too weak.",
        "witness": _witness("resolveElemGeneral", ".floatDouble"),
    },
    {
        "id": "weak-general-complex-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("complexFloat", ".floatDouble"),
        "refinement": "a counterpart that also converted the complex floating "
                      "category to the default real floating width would be "
                      "lossy — it discards the imaginary component — and the "
                      "element-type tests assert a complex input is preserved. "
                      "Never the intended behavior, so it would not resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .complexFloat → out = .complexFloat`: at "
                     "input = .complexFloat the rival returns .floatDouble. A "
                     "convert-too-much miss on a category no other rival "
                     "touches, refuted at the .complexFloat input point.",
        "witness": _witness("resolveElemGeneral", ".complexFloat"),
    },
    {
        "id": "weak-general-record-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("structured", ".floatDouble"),
        "refinement": "a counterpart that converted a composite record "
                      "element-type to the default floating width would flatten "
                      "away its named fields — the record-carrying escape the "
                      "pre-fix predicate explicitly protected and the fix keeps "
                      "protecting. Record inputs would stop round-tripping, so "
                      "it would not resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input` and the arm "
                     "`input = .structured → out = .structured`: at "
                     "input = .structured the rival returns .floatDouble. This "
                     "attacks the composite-record arm, the one modeled "
                     "category that is neither floating nor a scalar number, at "
                     "its own input point.",
        "witness": _witness("resolveElemGeneral", ".structured"),
    },
    {
        "id": "weak-general-object-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("object", ".object"),
        "refinement": "the convert-too-LITTLE direction, and the arm that "
                      "distinguishes the two modeled paths: a counterpart that "
                      "left an individually-boxed-object input unconverted on "
                      "the general path would hand back an object-element array "
                      "where the failing test asserts a floating one (the test "
                      "constructs a boxed arbitrary-precision decimal and "
                      "asserts the result is floating). That assertion is in the "
                      "SAME failing test as the narrow-width one, so this "
                      "counterpart does NOT resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input`, the arm "
                     "`input = .object → out = .floatDouble`, and the family "
                     "clause `isFloating out = true ↔ (isFloating input = true "
                     "∨ input = .integral ∨ input = .object)` — this is the "
                     "rival that attacks the family clause's `input = .object` "
                     "disjunct directly: at input = .object the rival returns a "
                     "NON-floating result where the clause demands a floating "
                     "one. Refuted at the .object input point, which is also "
                     "the point that separates the two obligations (the fast "
                     "path PRESERVES this category).",
        "witness": _witness("resolveElemGeneral", ".object"),
    },
    {
        "id": "weak-general-integral-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _general("integral", ".integral"),
        "refinement": "the other convert-too-little direction: a counterpart "
                      "that left whole-number inputs unconverted would keep them "
                      "at their integer element-type, directly contradicting the "
                      "documented default that whole-number inputs come back "
                      "floating — asserted both by the failing test and by "
                      "several currently-passing element-type tests. It would "
                      "not resolve.",
        "rationale": "REJECT from `out = resultElemGeneral input`, the arm "
                     "`input = .integral → out = .floatDouble`, and the family "
                     "clause's `input = .integral` disjunct: at "
                     "input = .integral the rival returns a non-floating result "
                     "where both the arm and the clause demand .floatDouble. "
                     "The complement of the width-keyed rivals — they convert "
                     "too much, this converts too little — refuted at the "
                     ".integral input point.",
        "witness": _witness("resolveElemGeneral", ".integral"),
    },

    # ---- fast path ----------------------------------------------------
    # The fast-path obligation is a SEPARATE `prove_correct` with its own nine
    # arms and its own family clause, and it differs from the general path on the
    # boxed-object category. Attacking it only through the general-path rivals
    # would leave it unattacked, so it gets its own full set. Every fast-path
    # rival is refuted at a fast-path input point.
    {
        "id": "weak-fast-half-widened",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("floatHalf", ".floatDouble"),
        "refinement": "the headline defect on the OTHER modeled path: the "
                      "narrowest floating category widened to the default when "
                      "the input is already an array of the target kind. A "
                      "faithful counterpart leaves the reported defect in place "
                      "for exactly those inputs — a narrow-width float array "
                      "still coming back at double width — so it does NOT "
                      "resolve. The general-path fix alone does not cover this "
                      "path; both sites carry the same width-keyed test.",
        "rationale": "REJECT from `out = resultElemFast input` and the fast-path "
                     "arm `input = .floatHalf → out = .floatHalf`: at "
                     "input = .floatHalf the rival returns .floatDouble. This "
                     "case is what ATTACKS the fast-path obligation — the "
                     "general-path rivals cannot, since they leave the "
                     "fast-path impl untouched.",
        "witness": _witness("resolveElemFast", ".floatHalf"),
    },
    {
        "id": "weak-fast-bool-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("boolean", ".floatDouble"),
        "refinement": "the truth-valued half of the pre-fix predicate on the "
                      "fast path. As on the general path, this rival reproduces "
                      "the PRE-fix treatment of the boolean category, so it "
                      "regresses nothing that passes beforehand: boolean "
                      "preservation on this path is new behavior the fix "
                      "establishes. It is shipped because the frozen spec pins "
                      "that arm (`input = .boolean → out = .boolean`) on this "
                      "obligation, so a counterpart that kept converting "
                      "booleans here does NOT resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .boolean → out = .boolean`: at input = .boolean "
                     "the rival returns .floatDouble, the post-image .boolean. "
                     "Distinct from the fast narrow-float rival (it agrees with "
                     "gold on every floating width), so it is refuted at its "
                     "own .boolean input point on this obligation.",
        "witness": _witness("resolveElemFast", ".boolean"),
    },
    {
        "id": "weak-fast-single-widened",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("floatSingle", ".floatDouble"),
        "refinement": "widening the single-width floating category on the fast "
                      "path regresses behavior that holds before the fix — the "
                      "pre-fix predicate already preserves a single-width input "
                      "— so a faithful counterpart both breaks prior behavior "
                      "and fails to establish the narrow-width behavior. The "
                      "argument is from the pre-fix predicate and the frozen "
                      "arm; no existing element-type test exercises this width "
                      "on this path. It does NOT resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .floatSingle → out = .floatSingle`: at "
                     "input = .floatSingle the rival returns .floatDouble. The "
                     "fast-path NEAR-MISS the fast narrow-float rival does not "
                     "subsume — it is correct on the narrowest width — refuted "
                     "at its own input point.",
        "witness": _witness("resolveElemFast", ".floatSingle"),
    },
    {
        "id": "weak-fast-extended-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("floatExtended", ".floatDouble"),
        "refinement": "re-materializing a wider-than-default floating input "
                      "under the default on the fast path loses precision and "
                      "contradicts the frozen arm pinning that a "
                      "wider-than-double input keeps its own width. The pre-fix "
                      "predicate already preserves that input, so this "
                      "regresses behavior that holds beforehand; no existing "
                      "element-type test exercises a wider-than-double input, "
                      "so the argument is from the predicate and the arm rather "
                      "than test appeal. It would not resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .floatExtended → out = .floatExtended`: at "
                     "input = .floatExtended the rival returns .floatDouble. "
                     "Attacks the fast-path arm above the default width, at its "
                     "own input point.",
        "witness": _witness("resolveElemFast", ".floatExtended"),
    },
    {
        "id": "weak-fast-double-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("floatDouble", ".floatSingle"),
        "refinement": "handing a double-width floating input back at single "
                      "width on the fast path narrows the most common floating "
                      "input, which the pre-fix predicate already preserves; "
                      "existing precision-sensitive display assertions would "
                      "observe the narrowing. It would not resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .floatDouble → out = .floatDouble`: at "
                     "input = .floatDouble the rival returns .floatSingle. As "
                     "on the general path, the fast family clause `isFloating "
                     "out = true ↔ (isFloating input = true ∨ input = "
                     ".integral)` is SATISFIED here (both sides floating), so "
                     "the rejection is attributable to the per-category arm and "
                     "value clause — demonstrating the fast family clause alone "
                     "would be too weak.",
        "witness": _witness("resolveElemFast", ".floatDouble"),
    },
    {
        "id": "weak-fast-complex-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("complexFloat", ".floatDouble"),
        "refinement": "converting the complex floating category to the default "
                      "real floating width on the fast path discards the "
                      "imaginary component; the element-type tests assert a "
                      "complex input is preserved. It would not resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .complexFloat → out = .complexFloat`: at "
                     "input = .complexFloat the rival returns .floatDouble. A "
                     "convert-too-much miss on the fast path's complex arm, "
                     "refuted at its own input point.",
        "witness": _witness("resolveElemFast", ".complexFloat"),
    },
    {
        "id": "weak-fast-record-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("structured", ".floatDouble"),
        "refinement": "flattening a composite record element-type to the "
                      "default floating width on the fast path destroys its "
                      "named fields — the record-carrying escape the pre-fix "
                      "predicate protected and the fix keeps protecting. Record "
                      "inputs would stop round-tripping; it would not resolve.",
        "rationale": "REJECT from `out = resultElemFast input` and the arm "
                     "`input = .structured → out = .structured`: at "
                     "input = .structured the rival returns .floatDouble. "
                     "Attacks the fast path's composite-record arm at its own "
                     "input point.",
        "witness": _witness("resolveElemFast", ".structured"),
    },
    {
        "id": "weak-fast-object-converted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("object", ".floatDouble"),
        "refinement": "THE rival that distinguishes the two modeled paths, in "
                      "the direction opposite to its general-path sibling: the "
                      "boxed-object category converts on the general path but is "
                      "PRESERVED on the fast path, because a boxed-object "
                      "element-type cannot arise for an input already of the "
                      "target kind. A counterpart that converted it here would "
                      "apply the general path's category set to the fast path — "
                      "a real mis-fix, since both sites were edited by the same "
                      "change and it is easy to give them the same category set. "
                      "It converts an element-type the fast path must leave "
                      "alone, so it does NOT resolve.",
        "rationale": "REJECT from `out = resultElemFast input`, the arm "
                     "`input = .object → out = .object`, and the fast family "
                     "clause `isFloating out = true ↔ (isFloating input = true "
                     "∨ input = .integral)` — whose right side is FALSE at "
                     "input = .object while the rival makes the left side true. "
                     "So this rival attacks the fast family clause directly, and "
                     "it is the ONLY rival whose input point demonstrates that "
                     "the two obligations genuinely differ: at .object the "
                     "general path must convert and the fast path must preserve, "
                     "so a single shared decision cannot satisfy both.",
        "witness": _witness("resolveElemFast", ".object"),
    },
    {
        "id": "weak-fast-integral-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fast("integral", ".integral"),
        "refinement": "the convert-too-little direction on the fast path: whole "
                      "numbers left at their integer element-type, contradicting "
                      "the documented default that whole-number inputs come back "
                      "floating (asserted by both the failing test and "
                      "currently-passing element-type tests). It would not "
                      "resolve.",
        "rationale": "REJECT from `out = resultElemFast input`, the arm "
                     "`input = .integral → out = .floatDouble`, and the fast "
                     "family clause's `input = .integral` disjunct: at "
                     "input = .integral the rival returns a non-floating result "
                     "where all three demand .floatDouble. The complement of "
                     "the fast width-keyed rivals, refuted at the .integral "
                     "input point.",
        "witness": _witness("resolveElemFast", ".integral"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery has 11 SPEC cases (3 soundness positives, 1 admissibility,
# 7 uniqueness rivals) plus an EMPTY axiom lane. This bundle ships 23 (4
# positives, 1 admissibility, 18 rivals). The count went UP, not down, and the
# reason is a carrier change rather than a decision to add cases for their own
# sake:
#
#   * the sibling models ONE decision surface as two boolean predicates over a
#     three-field input (a category code point plus a storage-width flag plus a
#     composite flag), with the result a single Bool "does it convert";
#   * this bundle models the SAME decision as two methods over ONE categorical
#     input whose nine values the spec enumerates INDIVIDUALLY, with the result
#     the resulting element-type rather than a Bool.
#
# So the sibling's width-flag and composite-flag binders are absorbed into the
# category constructors, and each of the sibling's rivals — which had to be
# expressed as a formula over three binders — becomes a single retargeted arm.
# Because the spec names all nine categories per path as separate `ensures` arms,
# "every independent top-level clause is attacked by some rival" requires one
# rival per arm per obligation: 9 + 9. The 18 rivals are not parity-chasing;
# they are the arms the frozen spec actually declares.
#
#   sibling case                    -> here                            disposition
#   ------------------------------------------------------------------------------
#   pos-control-homog               -> pos-model-fast                  PORTED
#   pos-control-generic             -> pos-arm-reorder-general         PORTED
#   pos-control-both                -> pos-predicate-ladder-both       PORTED
#   (no sibling)                    -> pos-model-general               ADDED
#   admiss-witnesses                -> admiss-nondegenerate-postimage  PORTED (re-aimed)
#   weak-width-homog                -> weak-fast-half-widened
#                                      + weak-fast-bool-converted      PORTED (split)
#   weak-width-generic              -> weak-general-half-widened
#                                      + weak-general-bool-converted   PORTED (split)
#   weak-coerce-bool-homog          -> weak-fast-bool-converted        PORTED (merged)
#   weak-coerce-complex-generic     -> weak-general-complex-converted  PORTED
#   weak-drop-object-generic        -> weak-general-object-preserved   PORTED
#   weak-drop-uint-homog            -> weak-fast-integral-preserved    PORTED (widened)
#   weak-const-false-homog          -> weak-fast-integral-preserved    PORTED (subsumed)
#   (no sibling)                    -> 10 further per-arm rivals       ADDED
#   AXIOM_TESTS ([])                -> (none)                          DROPPED (G-AX)
#   frame-mutation (already vacuous) -> (none)                         VACUOUS
#   control-flow-effect (already N/A) -> (none)                        VACUOUS
#   (no sibling)                    -> divergence               SPEC-CLOSED (witness)
#
# All 11 sibling SPEC cases are accounted for; NONE was omitted for being hard to
# prove, and no soundness positive was dropped (all four close under the frozen
# proof script, confirmed with real builds).
#
# PORTED (positives): pos-control-homog / -generic spelled the predicate out and
#   reordered its branches — here the two shapes are the reversed dispatch table
#   (pos-arm-reorder-general) and the direct post-image call (pos-model-fast).
#   pos-control-both rewrote both sites at once with a local-variable reshape;
#   pos-predicate-ladder-both does the same but reaches a genuinely different
#   control flow (a Bool local plus two early returns rather than one let-bound
#   result). ADDED pos-model-general so BOTH obligations are independently
#   defended by a direct-model positive, not just one.
# PORTED-SPLIT (the width rivals): the sibling's single width-keyed rival keys on
#   a storage-width FLAG, so one impl gets both the narrow-float and the boolean
#   category wrong at once. Here those are two separate `ensures` arms, and a
#   rival that missed both would let a rival that missed only ONE of them slip
#   through. Split into per-arm rivals per path, so each is a single-category
#   near-miss refuted at its own input point.
# PORTED-MERGED / -SUBSUMED: the sibling's coerce-bool rival is the same behavior
#   as half of its width rival, and lands on the same arm here; its
#   drop-uint rival and its const-false near-miss both collapse onto the single
#   `integral` category (the carrier does not split signed from unsigned, since
#   the decision treats them identically — noted as a carrier narrowing, not a
#   dropped case).
# PORTED-RE-AIMED (admissibility): the sibling asserts its precondition admits
#   four failing-test-shaped witnesses. Neither method here declares a `require`
#   clause, so input admissibility is trivially true and asserting it would test
#   nothing. Re-aimed at the risk this backend does carry — POST-IMAGE
#   DEGENERACY — and confirmed live by checking a false claim leaves the goal
#   unsolved.
# ADDED (10 per-arm rivals): the sibling has no rival for the single-width,
#   wider-than-double, double-width, or composite-record categories, because its
#   Bool-valued predicate cannot express "returns the wrong floating WIDTH" at
#   all — its result is one bit. On this carrier the result is the element-type
#   itself, so each of those arms is independently violable and gets a rival.
#   weak-{general,fast}-double-narrowed matter most: both SATISFY the isFloating
#   family clause and are caught only by the per-category arm, which demonstrates
#   the family clause alone would be SPEC-TOO-WEAK.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references, so there is nothing to probe.
# VACUOUS (frame-mutation, control-flow-effect): the sibling already records both
#   as vacuous on its own side. Referential transparency makes the first vacuous
#   a fortiori here (`input` is an immutable value, no `mut` binder, no heap, no
#   aliasing) and both methods are total and side-effect-free, so the returned
#   element-type is the whole observable. Neither is replaced by a fabricated
#   substitute.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
# BINDER / CLAUSE COVERAGE of the reject witnesses.
#   Each obligation has exactly ONE input binder, `input`, and it is FREE (no
#   `require` clause pins it). Across the 18 reject witnesses that binder takes
#   all NINE of its modeled values — .floatHalf, .floatSingle, .floatDouble,
#   .floatExtended, .boolean, .complexFloat, .structured, .object, .integral —
#   on EACH of the two obligations. That is the binder's entire modeled domain,
#   so pts = 9 distinct input points per obligation and no category is left at a
#   value every rival holds fixed.
#   Every top-level `ensures` clause is attacked. Per obligation: the value
#   clause (`out = resultElem* input`) by all nine of its rivals; each of the
#   nine per-category arms by the rival that retargets exactly that arm; and the
#   isFloating family clause by the rivals that cross the floating boundary
#   (general: object-preserved and integral-preserved make a demanded-floating
#   result non-floating, complex/record/bool-converted make a
#   demanded-non-floating result floating; fast: the same plus object-converted,
#   the rival that shows the two obligations' family clauses genuinely differ).
#   Both obligations are DEFENDED (pos-model-general, pos-model-fast, and
#   pos-predicate-ladder-both reshape both; pos-arm-reorder-general the general
#   one) and ATTACKED (nine rivals each).
AXIOM_TESTS = []
