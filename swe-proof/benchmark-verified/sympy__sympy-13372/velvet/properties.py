"""properties.py — G-PBT falsification battery for sympy__sympy-13372 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct numericComplexResult`` obligation survives with a
byte-identical statement). It is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, ``numericComplexResult``):

  numericComplexResult (realPart imagPart : Part) (prec : Int)
      -> out : Option EvalResult
  ensures out = evalSpec realPart imagPart prec
  ensures (realPart.status = nonNumeric ∨ imagPart.status = nonNumeric)
            → out = none
  ensures realPart.status ≠ nonNumeric → imagPart.status ≠ nonNumeric
            → ∃ r, out = some r

A numeric-evaluation step splits a value into a real and an imaginary
component, each in exactly one of three situations — an exact zero, a concrete
numeric quantity, or neither (still-symbolic). It assembles a record pairing
each component with a reported value and a reported precision, OR — when EITHER
component is in the neither situation — reports the absent marker ``none`` so a
caller may fall back, rather than fabricating a partial record. Each ``Part``
carries a three-way ``status`` tag (``PartStatus.exactZero`` / ``.numeric`` /
``.nonNumeric``) and a converted-value handle ``value : Int`` (meaningful only
when ``status = numeric``). ``evalSpec`` is a fully-unfolded ``def`` over the
method's own arguments; there is no opaque answer-key to echo (the ``axioms``
region is empty).

THREE INPUT BINDERS, all free (no ``require`` clause, total domain):
``realPart``, ``imagPart`` (the two components, each a status tag + value
handle) and ``prec`` (the target precision). The reject witnesses move each
component's ``status`` across all three tags and drive ``prec`` and the value
handles across distinct values, so a rival mishandling only one situation, one
component, or the precision is caught.

The postcondition has THREE independent top-level clauses; the rivals attack
each:
  * clause 1  ``out = evalSpec realPart imagPart prec`` — the exact record
    (value + precision, per component)                     — wrong-precision,
                                                             numeric-as-absent,
                                                             swapped-components
  * clause 2  either component non-numeric ⇒ ``out = none`` — the DEFER decision
    (THE FIX): a non-numeric component must yield ``none``, never an assembled
    record. A DISJUNCTION, so each disjunct is attacked separately
                                                            — prepatch-fallthrough
                                                              (neither guard),
                                                              half-defer-real-only
                                                              (imaginary guard only)
  * clause 3  both components representable ⇒ a record exists (``∃ r, out =
    some r``): the step must not spuriously refuse a representable pairing
                                                            — over-defer

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite; the sibling itself records this class as N/A here (all inputs are
    integer VALUE types, ``has_readonly_input = False``). Lean and Velvet are
    referentially transparent: ``realPart`` / ``imagPart`` / ``prec`` are
    immutable values (the method declares NO ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe. Not fabricated — reported N/A in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. Every clause pins ``out`` to a fully-unfolded
    function of the method's own inputs (``evalSpec`` / ``none`` / ``∃ r``); the
    ``axioms`` region declares nothing, so there is no opaque answer-key to echo.
    The honest positive control does the assembly directly.
  * PARTIAL-DOMAIN / VALUE — the main class. Each rival is right on part of the
    domain and diverges on one sub-domain, refuted at a concrete point there.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``numericComplexResultTester
args = false`` says the extracted program's result violates the method
postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The result carrier ``EvalResult`` and the existential clause
``∃ r, out = some r`` are not decidable out of the box, so each witness first
brings a ``DecidableEq EvalResult`` instance and a ``Decidable (∃ r, o = some
r)`` instance into scope (appended to BOTH the rival and the gold build, so they
exist on both sides by construction and add no spec content); with those, the
frozen loop-free ``if`` ladder makes every witness ``decide``: it ELABORATES
against the reshaped/wrong rival (a genuine counterexample) and, because the
frozen solution satisfies the spec at every input, ``decide`` proves ``… =
false`` FALSE against gold — the discrimination half. Every witness is at
concrete literals, so no head binder and no consistency obligation.

WITNESS PLACEMENT. The six reject witnesses probe SIX DISTINCT input points,
moving each component's ``status`` across all three tags and ``prec`` across
distinct values:
  prepatch-fallthrough  (nonNumeric,0) (exactZero,0) 5   real non-numeric ⇒ defer
  half-defer-real-only  (numeric,7)    (nonNumeric,0) 3  IMAG non-numeric ⇒ defer
  over-defer            (numeric,7)    (numeric,3)   10  both representable ⇒ exists
  wrong-precision       (numeric,7)    (exactZero,0) 4   numeric real, wrong prec
  numeric-as-absent     (exactZero,0)  (numeric,9)   6   numeric imag mislabelled
  swapped-components    (exactZero,0)  (numeric,2)   5   asymmetric, crossed fields
BOTH components' ``status`` is driven across ALL THREE tags (realPart:
nonNumeric / numeric / exactZero; imagPart: exactZero / numeric / nonNumeric),
and ``prec`` takes 5 / 3 / 10 / 4 / 6; value handles vary. No binder is pinned
across the battery, and neither component is privileged: the defer clause is a
disjunction, so it is attacked on each of its two disjuncts separately
(prepatch-fallthrough drops both guards, half-defer-real-only drops only the
imaginary one).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
behaviour is modelled deeply). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13372"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each is a single contiguous block wholly inside the one
# `-- impl-start` / `-- impl-end` region (or the `prove_correct` body) and
# unique in Solution.lean; both facts are asserted at load, so the manifest
# breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "    if realPart.status = PartStatus.nonNumeric then\n"
    "      return none\n"
    "    else\n"
    "      if imagPart.status = PartStatus.nonNumeric then\n"
    "        return none\n"
    "      else\n"
    "        return some {\n"
    "          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,\n"
    "          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
    "          realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,\n"
    "          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }")
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1, "gold impl drift"

# The frozen `prove_correct` tactic body. Elided from the consumer spec view, so
# a variant whose impl reshapes the control flow may retune it, keeping the
# obligation STATEMENT and header untouched (same_spec preserved).
_GOLD_PROOF = (
    "prove_correct numericComplexResult by\n"
    "  loom_solve <;> simp_all [evalSpec]\n")
assert _GOLD_PROOF in _BASE and _BASE.count(_GOLD_PROOF) == 1, "gold proof drift"

# The impl-start marker line (unique); the admissibility case inserts an
# in-region `assert` immediately after it, keeping the whole gold body verbatim.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"


def _impl(body):
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The result carrier `EvalResult` and the existential
# ---- clause `∃ r, out = some r` are not decidable out of the box; the witness
# ---- brings the two needed instances into scope (appended to BOTH builds, so
# ---- they add no spec content and exist on gold and rival alike) and then
# ---- reaches the method contract through Velvet's tester machinery. The
# ---- extracted `if` ladder is loop-free, so each witness closes by `decide`.
def _tester():
    m = "numericComplexResult"
    return (
        "deriving instance DecidableEq for EvalResult\n\n"
        "instance (o : Option EvalResult) : Decidable (∃ r, o = some r) :=\n"
        "  decidable_of_iff (o.isSome = true) (by cases o <;> simp)\n\n"
        f"extract_program_for {m}\n"
        f"prove_precondition_decidable_for {m}\n"
        f"prove_postcondition_decidable_for {m}\n"
        f"derive_tester_for {m}\n\n")


def _witness(args):
    return _tester() + (
        f"example : numericComplexResultTester {args} = false := by\n  decide\n")


# A representable-part literal (numeric / exact-zero) and a non-numeric literal.
def _P(status, value):
    return f"{{ status := PartStatus.{status}, value := {value} }}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify; else the post-image is SPEC-TOO-STRONG. Collapses the
    # two nested per-component defer guards into ONE fused disjunctive guard
    # (either component non-numeric ⇒ none), then assembles the record. Same
    # observable value on every input; a distinct control shape. The reshaped
    # control flow needs the frozen tactic extended by `<;> tauto` to discharge
    # the fused-guard side goal (tactic body only; statement + header untouched,
    # verified during authoring).
    # =====================================================================
    {
        "id": "pos-control-fused-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    if realPart.status = PartStatus.nonNumeric ∨ imagPart.status = PartStatus.nonNumeric then\n"
            "      return none\n"
            "    else\n"
            "      return some {\n"
            "        realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,\n"
            "        imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
            "        realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,\n"
            "        imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }",
            "prove_correct numericComplexResult by\n"
            "  loom_solve <;> simp_all [evalSpec] <;> tauto\n"),
        "rationale": "a correct reshape — the two nested per-component defer "
                     "guards fused into one disjunctive guard, then the record "
                     "assembled — computes the identical `out = evalSpec realPart "
                     "imagPart prec` on every input; all three ensures clauses "
                     "still discharge. A faithful correct impl must verify, else "
                     "the postcondition is SPEC-TOO-STRONG over impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous (nothing could
    # exclude the F2P-shaped input). RE-AIMED at the residual risk on a total
    # domain: that the post-image is UNSATISFIABLE / DEGENERATE at the interesting
    # point. This case discharges a live in-region `assert` pinning `evalSpec` at
    # the F2P-shaped point — a numeric real component paired with an exact-zero
    # imaginary one — to the fully-populated record (the numeric part carries its
    # value AND the target precision, the exact-zero part carries neither). The
    # impl is kept verbatim so the method's own three clauses still discharge; the
    # assert is live (a false claim leaves an unsolved `False` goal — verified
    # during authoring), and the frozen `prove_correct` tactic clears it with no
    # retune.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `admiss\n"
            "      (evalSpec " + _P("numeric", "7") + " " + _P("exactZero", "0") + " 4\n"
            "        = some { realValue := some 7, imagValue := none, realPrec := some 4, imagPrec := none }))\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a numeric real component (value 7) paired "
                     "with an exact-zero imaginary component, at precision 4, must "
                     "assemble the fully-populated record (realValue = some 7, "
                     "realPrec = some 4; imagValue = imagPrec = none) — the numeric "
                     "part genuinely carries its value and the target precision "
                     "rather than collapsing to `none`. The in-region assert must "
                     "discharge (else the obligation is degenerate at the point the "
                     "fix cares about); the impl is verbatim so the three ensures "
                     "clauses discharge under the frozen `prove_correct`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "prepatch-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix shape: never branch on the non-numeric situation at all —
        # unconditionally assemble the record, treating a non-numeric component as
        # if it were representable (fabricating a value + precision for it). Never
        # yields `none`. Attacks clause 2 (the DEFER decision — the fix).
        "module": _impl(
            "    return some {\n"
            "      realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,\n"
            "      imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
            "      realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,\n"
            "      imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }"),
        "refinement": "this IS the pre-patch shape (no defer on the non-numeric "
                      "situation): a still-symbolic component is treated as "
                      "representable and a record is fabricated around a precision "
                      "that, in the real code, was never bound — the formal face of "
                      "the reported crash where the assembled tuple reads an unset "
                      "local. The faithful counterpart (dropping the defer) makes "
                      "the failing scenario assemble-and-crash instead of falling "
                      "back, so it still fails that test. It would NOT resolve.",
        "rationale": "REJECT from clause 2 (realPart.status = PartStatus.nonNumeric "
                     "∨ imagPart.status = PartStatus.nonNumeric → out = none): with "
                     "a non-numeric real component the post-image demands `none` "
                     "but the rival assembles a record, so `out = evalSpec …` also "
                     "fails. Verifying would be SPEC-TOO-WEAK on the defer clause. "
                     "Refuted at realPart non-numeric, imagPart exact-zero, prec 5.",
        "witness": _witness(f"{_P('nonNumeric','0')} {_P('exactZero','0')} 5"),
    },
    {
        "id": "over-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # Always report `none`, even when both components are representable. The
        # deferral is licensed only when some component is non-numeric; refusing a
        # fully-representable pairing leaves the assembled record unreachable.
        # Attacks clause 3 (both representable ⇒ a record exists) and clause 1.
        "module": _impl("    return none"),
        "refinement": "a counterpart that reports no numeric result for every "
                      "input makes the step fall back on EVERY expression — no "
                      "concrete number is ever assembled. Every scenario that pins "
                      "a numeric result (the F2P pair and all numeric companions) "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from clause 3 (realPart.status ≠ PartStatus.nonNumeric "
                     "→ imagPart.status ≠ PartStatus.nonNumeric → ∃ r, out = some "
                     "r): with both components representable the post-image demands "
                     "a record exists but the rival yields `none`, and `out = "
                     "evalSpec …` fails too. Verifying would leave the assemble path "
                     "unpinned (SPEC-TOO-WEAK). Refuted at both components numeric, "
                     "prec 10.",
        "witness": _witness(f"{_P('numeric','7')} {_P('numeric','3')} 10"),
    },
    {
        "id": "half-defer-real-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit. Guards the REAL component's situation but not the
        # imaginary one: a non-numeric IMAGINARY component still falls through
        # and gets a fabricated value + precision. The nearest miss to gold in
        # the battery — correct on the entire real-component sub-domain and on
        # every symmetric pairing, wrong only when the imaginary component alone
        # is non-numeric. Attacks clause 2 (the DEFER decision) on the component
        # the other rivals never place at `nonNumeric`: before this case, no
        # witness drove `imagPart.status` to `nonNumeric` at all, so a partial
        # fix covering only one of the two components was unattacked.
        "module": _impl(
            "    if realPart.status = PartStatus.nonNumeric then\n"
            "      return none\n"
            "    else\n"
            "      return some {\n"
            "        realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,\n"
            "        imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
            "        realPrec  := if realPart.status = PartStatus.exactZero then none else some prec,\n"
            "        imagPrec  := if imagPart.status = PartStatus.exactZero then none else some prec }"),
        "refinement": "a counterpart that guards only ONE of the two components "
                      "still fabricates a record around a precision that was "
                      "never bound whenever it is the OTHER component that is "
                      "still symbolic — the same assemble-and-crash the guarded "
                      "component was protected against, reachable through the "
                      "unguarded one. Any scenario whose still-symbolic part sits "
                      "on the unguarded component continues to fail. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause 2 (realPart.status = PartStatus.nonNumeric "
                     "∨ imagPart.status = PartStatus.nonNumeric → out = none): the "
                     "clause is a DISJUNCTION, so it demands `none` when EITHER "
                     "component is non-numeric; this rival honours it only for the "
                     "real component, and `out = evalSpec …` fails with it. "
                     "Verifying would leave the imaginary component's half of the "
                     "defer clause unpinned (partial-domain SPEC-TOO-WEAK). Refuted "
                     "at realPart numeric (value 7), imagPart NON-NUMERIC, prec 3 — "
                     "the one input shape no other rival's witness visits.",
        "witness": _witness(f"{_P('numeric','7')} {_P('nonNumeric','0')} 3"),
    },
    {
        "id": "wrong-precision",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the exact-zero and non-numeric situations, but on the numeric
        # situation reports `prec + 1` as the precision component instead of `prec`.
        # Diverges only on the numeric sub-domain. Attacks clause 1 (the exact
        # record — the precision component).
        "module": _impl(
            "    if realPart.status = PartStatus.nonNumeric then\n"
            "      return none\n"
            "    else\n"
            "      if imagPart.status = PartStatus.nonNumeric then\n"
            "        return none\n"
            "      else\n"
            "        return some {\n"
            "          realValue := if realPart.status = PartStatus.exactZero then none else some realPart.value,\n"
            "          imagValue := if imagPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
            "          realPrec  := if realPart.status = PartStatus.exactZero then none else some (prec + 1),\n"
            "          imagPrec  := if imagPart.status = PartStatus.exactZero then none else some (prec + 1) }"),
        "refinement": "a counterpart attaching `prec + 1` to a numeric component "
                      "reports the wrong working precision for every concrete "
                      "number, corrupting its downstream numeric evaluation. The "
                      "numeric scenarios that pin the reported precision still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from clause 1 (out = evalSpec realPart imagPart prec): "
                     "`evalSpec` reports exactly `prec` for a numeric component, but "
                     "the rival reports `prec + 1`, so the records differ whenever a "
                     "component is numeric. Verifying would leave the precision "
                     "component unpinned (partial-domain SPEC-TOO-WEAK). Refuted at "
                     "realPart numeric, imagPart exact-zero, prec 4.",
        "witness": _witness(f"{_P('numeric','7')} {_P('exactZero','0')} 4"),
    },
    {
        "id": "numeric-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Correctly defers on the non-numeric situation, but treats a NUMERIC
        # component like an exact-zero one: reports absent value + absent precision
        # for it. Attacks clause 1 (the exact record — the value AND precision
        # components on the numeric sub-domain).
        "module": _impl(
            "    if realPart.status = PartStatus.nonNumeric then\n"
            "      return none\n"
            "    else\n"
            "      if imagPart.status = PartStatus.nonNumeric then\n"
            "        return none\n"
            "      else\n"
            "        return some {\n"
            "          realValue := none,\n"
            "          imagValue := none,\n"
            "          realPrec  := none,\n"
            "          imagPrec  := none }"),
        "refinement": "a counterpart reporting an absent value + precision for a "
                      "numeric component marks every concrete number as an exact "
                      "zero, so downstream numeric evaluation treats real numbers as "
                      "0. Every numeric scenario still fails. It would NOT resolve.",
        "rationale": "REJECT from clause 1 (out = evalSpec realPart imagPart prec): "
                     "`evalSpec` reports `some value` and `some prec` for a numeric "
                     "component, but the rival reports `none` for both, so the "
                     "records differ whenever a component is numeric. Verifying "
                     "would leave the numeric value/precision unpinned. Refuted at "
                     "realPart exact-zero, imagPart numeric, prec 6 — an input where "
                     "wrong-precision agrees with gold on the (absent) real part, so "
                     "this rival carries its own separating witness on the imaginary "
                     "numeric part.",
        "witness": _witness(f"{_P('exactZero','0')} {_P('numeric','9')} 6"),
    },
    {
        "id": "swapped-components",
        "kind": "uniqueness",
        "expect": "reject",
        # Defers correctly, but keys the real component's value/precision emission
        # on imagPart's status and the imaginary component's on realPart's status.
        # Identical when the two situations coincide; diverges on any asymmetric
        # pairing. Attacks clause 1 (the exact record — cross-wired components).
        "module": _impl(
            "    if realPart.status = PartStatus.nonNumeric then\n"
            "      return none\n"
            "    else\n"
            "      if imagPart.status = PartStatus.nonNumeric then\n"
            "        return none\n"
            "      else\n"
            "        return some {\n"
            "          realValue := if imagPart.status = PartStatus.exactZero then none else some realPart.value,\n"
            "          imagValue := if realPart.status = PartStatus.exactZero then none else some imagPart.value,\n"
            "          realPrec  := if imagPart.status = PartStatus.exactZero then none else some prec,\n"
            "          imagPrec  := if realPart.status = PartStatus.exactZero then none else some prec }"),
        "refinement": "a counterpart crossing the two components' emission "
                      "conditions attaches the imaginary situation's presence "
                      "decision to the real component (and vice versa) — wrong on "
                      "every expression whose real and imaginary parts are "
                      "differently classified. The complex-valued scenarios that "
                      "pin each component's record still fail. It would NOT resolve.",
        "rationale": "REJECT from clause 1 (out = evalSpec realPart imagPart prec): "
                     "`evalSpec` keys the real component's value/precision on "
                     "realPart.status, but the rival keys it on imagPart.status, so "
                     "the records differ on any asymmetric pairing. Verifying would "
                     "leave the per-component wiring unpinned. Refuted at realPart "
                     "exact-zero, imagPart numeric, prec 5 — where the real part "
                     "must be absent but the rival (keyed on imagPart = numeric) "
                     "emits it, and the numeric imag part (keyed on realPart = "
                     "exact-zero) is dropped.",
        "witness": _witness(f"{_P('exactZero','0')} {_P('numeric','2')} 5"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 partial-domain/value uniqueness rivals) and 0
# AXIOM_TESTS; it already records FRAME-MUTATION as N/A (has_readonly_input =
# False — all inputs are integer value types). The sibling contracts
# `assemble_evalf_result(re_kind, im_kind, prec)` over integer case tags; this
# bundle contracts the SAME behaviour as `numericComplexResult(realPart,
# imagPart, prec)` over the richer `Part`/`EvalResult` carrier, with the nagini
# integer tags (0 exact-zero / 1 numeric / 2 OTHER) becoming the three-way
# `PartStatus`, and the deferral (nagini `raise EvalfDeferred`) becoming
# `out = none`. Every sibling case ports intact.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder          -> pos-control-fused-guard          PORTED
#   admiss-f2p-shaped            -> admiss-postimage-nondegenerate    RE-AIMED
#   prepatch-fallthrough         -> prepatch-fallthrough              PORTED (THE FIX)
#   wrong-precision              -> wrong-precision                   PORTED
#   numeric-as-absent            -> numeric-as-absent                 PORTED
#   over-defer                   -> over-defer                        PORTED
#   swapped-components           -> swapped-components                PORTED
#   (no sibling counterpart)     -> half-defer-real-only            AUDIT-ADDED
#   (FRAME-MUTATION: N/A already noted in the sibling)                VACUOUS
#
# 6 ported, 1 re-aimed, 1 audit-added, frame-mutation vacuous. All 7 sibling SPEC
# cases have a counterpart here — carrier narrowing does not drop any, because
# this bundle models the SAME single functional core the sibling defends.
#
# AUDIT-ADDED (half-defer-real-only): an independent audit found that although
#   clause 2's antecedent is a DISJUNCTION over the two components, no witness in
#   the ported battery placed `imagPart.status` at `nonNumeric` — every reject
#   point drove the imaginary component to exactZero or numeric only. A rival
#   honouring the defer decision for the real component but not the imaginary one
#   was therefore unattacked, even though it is the nearest miss to gold that
#   exists on this carrier. The audit built it against the real verifier (rival
#   build exit 1) with a discriminating witness (rival exit 0, gold exit 1, gold
#   failing by a semantic `decide` refutation), and it is included here.
#
# RE-AIMED (admissibility): the sibling self-calls on representative in-domain
#   inputs to show the precondition (0<=kind<=2) admits the normal F2P/P2P
#   domain. There is no `require` clause here, so that probe is vacuous; the case
#   is re-aimed at the residual admissibility risk on a total domain — that the
#   post-image is unsatisfiable/degenerate at the interesting point. It discharges
#   an in-region assert pinning `evalSpec` at the F2P-shaped point (numeric real /
#   exact-zero imag) to the fully-populated record, proving the numeric component
#   genuinely carries its value and the target precision.
# VACUOUS (frame-mutation): the sibling itself records this class N/A (no
#   read-only input; all params are integer value types). This backend is
#   referentially transparent, declares no `mut` binder, and has no heap or
#   aliasing, so there is no read-only input to overwrite and no substitute probe.
#   Not fabricated.
# DROPPED: none from the SPEC lane. AXIOM_TESTS is empty in the sibling (pure
#   control-flow / definedness fix; no @ContractOnly axiom), so there is nothing
#   in the axiom lane to mirror; the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The three top-level ensures clauses are each attacked:
#   clause 1 (out = evalSpec …) by wrong-precision, numeric-as-absent, and
#   swapped-components; clause 2 (non-numeric ⇒ none — THE FIX) by
#   prepatch-fallthrough AND half-defer-real-only, one per disjunct; clause 3
#   (both representable ⇒ ∃ record) by over-defer.
#   Defended by the fused-guard positive and the admissibility case. The six
#   reject witnesses probe SIX DISTINCT input points: realPart.status is moved
#   across nonNumeric / numeric / exactZero, imagPart.status across exactZero /
#   numeric / nonNumeric, and prec across 5 / 3 / 10 / 4 / 6, with the value
#   handles varied — no binder is pinned across the battery, and both components
#   reach all three tags. The near-miss pairs carry
#   their own separating inputs: wrong-precision and numeric-as-absent both
#   diverge on the numeric sub-domain but on different components (real vs imag),
#   and swapped-components diverges only on an asymmetric pairing, so each is
#   refuted at the input that distinguishes it.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
