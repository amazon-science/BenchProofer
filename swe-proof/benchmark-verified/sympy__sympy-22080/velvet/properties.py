"""properties.py — G-PBT falsification battery for sympy__sympy-22080 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct printNegatedFactor`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  printNegatedFactor (k : OperandKind) (inner : List Char) return (out : List Char)
    ensures out = renderNeg k inner                              -- (C1) master
    ensures k = .modOp     → out = '-' :: (('(' :: inner) ++ [')'])  -- (C2) wrap
    ensures k = .mulCluster → out = '-' :: (('(' :: inner) ++ [')']) -- (C3) wrap
    ensures k = .power     → out = '-' :: inner                   -- (C4) bare
    ensures k = .atomic    → out = '-' :: inner                   -- (C5) bare
    ensures k = .funcCall  → out = '-' :: inner                   -- (C6) bare

The method prints one sub-expression sitting directly under a leading unary
minus. The sub-expression is abstracted to its printed-form CLASS ``k`` (five
kinds); its own already-printed body is the free input ``inner : List Char``.
The pinned behaviour: a remainder operation and a product cluster are WRAPPED in
parentheses (so the minus governs the whole factor); an atom, a power, and a
self-delimited function call are left BARE. ``renderNeg`` / ``needsParen`` /
``opWeight`` are TRANSPARENT ``def``s in the ``pure`` region over the method's
own inputs — there is NO opaque answer-key oracle in the load-bearing clause, so
pinning ``out = renderNeg k inner`` is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``out = renderNeg k inner``) is the master
pin: it fixes the output at every ``(k, inner)``, so every wrap/bare decision and
the placement of the leading minus and the parentheses is pinned by it. C2–C6
are its per-kind CONSEQUENCES (the five modeled kinds), each pinning one arm of
the wrap table extensionally; a rival that mishandles exactly one kind violates
that kind's consequence clause (and C1). Every uniqueness rival targets one arm.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts THREE pure ``int/bool`` functions over the SAME fix split across two
repo sites: ``remainder_operand_level()`` (site A — the post-fix binding strength
of a remainder operand, an int), ``negated_single_operand_enclosed(lvl)`` (site B
— the wrap decision as a function of an operand's integer strength, with an
in-domain ``Requires`` 40..70 and two consequence clauses), and an illustrative
``negated_remainder_is_enclosed()`` composite. This velvet bundle FUSES both
sites into the single decision ``printNegatedFactor``: the operand is abstracted
to its strength CLASS ``k : OperandKind`` (five kinds) rather than a raw int
level, and the two edits (raise the unary-minus threshold; drop the remainder's
strength) become the single per-kind wrap table ``needsParen``. So the nagini
integer-band attacks re-express as per-KIND attacks, and the nagini site-A
value function has no separately-observable counterpart (see the footer).

  * FRAME/PERMISSION-MUTATION — VACUOUS. Nagini's ``has_readonly_input`` is
    already ``False`` here too: every modeled function takes an int-by-value or a
    kind and returns a pure value, so the nagini file itself ships NO
    frame-mutation rival. On this carrier the same holds structurally — Velvet is
    referentially transparent, this method declares NO ``mut`` binder, ``k`` and
    ``inner`` are immutable values, and there is no heap, aliasing, or permission
    system. No read-only input to overwrite, no substitute probe. Not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image ``renderNeg k
    inner`` is a transparent ``def`` over the method's own inputs; there is no
    answer key to echo. The honest cheapest CORRECT impl (``return renderNeg k
    inner``) is carried as a POSITIVE control instead (pos-direct) — it doubles as
    proof the spec is not echo-vulnerable, since any wrong wrap decision fails C1.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. Each nagini band attack
    re-expresses onto one per-kind consequence: revert the remainder to the
    function strength (modOp bare), revert the threshold below the multiplicative
    strength (mulCluster bare), push the threshold up to the power strength (power
    wrapped). Plus per-kind over-wrap rivals for the two remaining bare kinds
    (atomic, funcCall) and TWO genuine partial-domain rivals over ``inner`` (wrap
    only the first code point; suppress the wrap at the empty body), so both input
    binders are varied and ``inner`` is attacked at three distinct lengths.
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

WITNESS MECHANICS ON THIS BUNDLE. The carrier is FULLY TRANSPARENT: ``k`` is a
five-constructor ``inductive`` with ``DecidableEq``, ``inner`` is a ``List
Char``, and ``renderNeg`` / ``needsParen`` / ``opWeight`` compute on concrete
literals — there is NO opaque callee in the postcondition. So a witness pins both
inputs to concrete literals and reaches the contract through Velvet's own tester
machinery: ``extract_program_for`` → ``prove_precondition_decidable_for`` →
``prove_postcondition_decidable_for`` → ``derive_tester_for``, then
``printNegatedFactorTester k inner = false := by decide`` says the extracted
program's result violates the method's postcondition at that concrete input.

AUDIT NOTE — the gold-side exit code here carries real information, checked
rather than assumed. The standing failure mode for this witness shape is a gold
build that fails for a reason unrelated to truth (a stuck ``decide`` on an
irreducible term, a missing ``Decidable`` instance, an unknown name), in which
case a FORGED witness asserting the rival is CORRECT would clear both halves.
Measured on this bundle: asserting ``printNegatedFactorTester OperandKind.modOp
['a'] = true`` against the FROZEN solution ELABORATES (exit 0), while the same
claim against a rival is refuted (``decide`` proves it false, exit 1) — the exact
mirror image of the shipped witnesses. So the kernel really does evaluate this
tester on both subjects, both truth values are reachable, and a gold-side exit 1
means "gold satisfies its postcondition here", not "nothing was decided".
Because the FROZEN impl is ALSO loop-free (a single ``if``), its extracted
program reduces under ``decide`` too — so the discrimination is not "gold stays
stuck" but "gold SATISFIES the postcondition everywhere": the tester computes
``true`` on gold (so ``= false`` is provably FALSE and ``decide`` reports the
proposition is false → the gold build FAILS), and computes ``false`` on a rival
at a discriminating input (so ``= false`` closes by ``decide`` → the rival build
SUCCEEDS). Measured for every reject case with ``scripts/lean_verify.sh``: the
witness ELABORATES against its rival (exit 0), the full rival does NOT verify,
and the witness FAILS against the frozen solution (``decide`` proves the
proposition false). No witness binds a hypothesis (every input is a literal that
decides the clause), so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries an
axiom-soundness probe and a caller-domain-containment probe over the real sympy
``precedence`` / printer callees; that is G-AX's job (this bundle declares no
axiom — the changed op is modeled DEEPLY in the ``pure`` region and validated by
conformance_check.py / G-CONF against the patched renderer), and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22080"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the single wrap `if`),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`
# ---- (the two leading comment lines are inside that region too, but this anchor
# ---- is the executable tail only, which is unique in the file). Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- -- impl-start .. -- impl-end region and same_spec holds by construction
# ---- (both facts asserted at load by _swap).
_IMPL = (
    "    let wrapped : List Char :=\n"
    "      if needsParen k then ('(' :: inner) ++ [')'] else inner\n"
    "    return '-' :: wrapped"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. Two of the three positive controls keep it
# byte-identical — but that is a WEAKNESS of theirs, not a virtue: they leave the
# residual goal in the same shape because their impls are DEFINITIONALLY EQUAL to
# the frozen one (see pos-control-kindmatch, which is not). Rivals leave the proof
# as-is too — their rejection is carried by the witness, not the tactic script.
_PROOF = "prove_correct printNegatedFactor by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Variant with the impl body AND the elided tactic body replaced.

    Both regions the consumer spec view elides, so `markers.same_spec` still
    holds and the `prove_correct printNegatedFactor` header (hence the obligation
    with its byte-identical `method ... ensures` statement) survives — asserted
    at load by the two `_swap` uniqueness checks. Needed because a positive whose
    impl is NOT definitionally equal to the frozen one leaves a residual goal the
    frozen one-liner never had to close: re-proving it is the whole point of such
    a case, and refusing to re-prove would confuse "the spec rejects this correct
    impl" with "the frozen tactic script was tuned to the frozen syntax".
    """
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble + builder. The spec is a `method` CONTRACT over a fully
# ---- transparent carrier, so a witness reaches it through Velvet's own tester
# ---- machinery: `printNegatedFactorTester k inner = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped, so no
# ---- tactic script can mask the verdict. Because the FROZEN impl is loop-free,
# ---- its tester computes `true` (postcondition holds everywhere), so `= false`
# ---- is provably FALSE on gold and the gold build fails — while a rival's
# ---- tester computes `false` at a discriminating input, so `= false` closes.
_PREAMBLE = (
    "extract_program_for printNegatedFactor\n"
    "prove_precondition_decidable_for printNegatedFactor\n"
    "prove_postcondition_decidable_for printNegatedFactor\n"
    "derive_tester_for printNegatedFactor\n\n"
)


def _wit(k, inner):
    return (
        _PREAMBLE +
        f"example : printNegatedFactorTester {k} {inner} = false := by\n"
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
        # Reshape: report the printed form DIRECTLY via the transparent `pure`
        # def, no inline wrap `if`. C1 is literally `out = renderNeg k inner`, so
        # this is the cheapest HONEST correct impl — and, since `renderNeg k inner`
        # is GROUNDED in the inputs (not an opaque answer key), it doubles as proof
        # the spec is not echo-vulnerable (any wrong wrap decision fails C1). The
        # residual goal is `rfl`-shaped, so the frozen `loom_solve` closes it as-is.
        "module": _impl("    return renderNeg k inner"),
        "rationale": (
            "the post-image `renderNeg k inner` is GROUNDED in the inputs (a total "
            "`def`, no opaque answer key), so returning it directly is the honest "
            "cheapest CORRECT impl; C1 is literally `out = renderNeg k inner`, so "
            "it MUST verify, else C1 is SPEC-TOO-STRONG. Ports the nagini "
            "grounded-oracle honest control (pos-control-echo-grounded): the "
            "cheapest impl satisfying the grounded pin, showing the spec is not "
            "echo-vulnerable (any wrong wrap decision fails `out = renderNeg k "
            "inner`, and C2–C6's per-kind arms all discharge)."
        ),
    },
    {
        "id": "pos-control-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the wrap decision to a typed local Bool before the `if`.
        # Same value flow (`doWrap = needsParen k`), different executable shape;
        # the frozen proof closes unchanged. Ports the nagini pos-control-siteB-
        # local (site B reshaped through a local) onto this carrier's wrap `if`.
        "module": _impl(
            "    let doWrap : Bool := needsParen k\n"
            "    let wrapped : List Char :=\n"
            "      if doWrap then ('(' :: inner) ++ [')'] else inner\n"
            "    return '-' :: wrapped"),
        "rationale": (
            "a correct impl with a DIFFERENT executable shape (bind the wrap "
            "decision `needsParen k` to a typed local Bool before the `if`) must "
            "verify; the value flow is unchanged so C1 and all five per-kind arms "
            "still discharge and the frozen proof closes as-is. Ports the nagini "
            "pos-control-siteB-local / pos-control-siteA-local (reshape through a "
            "typed local); if it fails => SPEC-TOO-STRONG (over-fit to the inline "
            "`if needsParen k` code form)."
        ),
    },

    {
        "id": "pos-control-kindmatch",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The two positives above are honest but WEAK as
        # soundness probes: each is DEFINITIONALLY EQUAL to the frozen impl
        # (`renderNeg k inner` unfolds by `rfl` to the frozen `if`; a `let` for
        # `needsParen k` is a zeta-reduction), which is exactly why each closes
        # under the byte-identical frozen `loom_solve`. Neither can therefore
        # detect a spec over-fit to the frozen SHAPE: they never present a goal
        # the frozen script did not already face.
        #
        # This one does. It decides the wrap by MATCHING on the kind instead of
        # comparing ranks, so the spec's `needsParen k` (a `decide (opWeight k ≤
        # negLevel)`) never appears in the impl at all: the residual C1 goal is
        # `('-' :: match k with | .modOp => '(' :: inner ++ [')'] | ... ) =
        # renderNeg k inner`, which is NOT closed by `rfl` — `loom_solve` alone
        # leaves it (measured: exit 1, `unsolved goals` at `ensures_6`). It IS
        # closed once the kind is case-split and the rank arithmetic evaluated,
        # which is the honest re-proof for this shape. So this case tests that a
        # faithful correct impl reaching the SAME wrap table by a different route
        # is admitted on its semantics rather than on its syntax — the
        # SPEC-TOO-STRONG direction the other two positives cannot reach.
        "module": _impl_proof(
            "    let wrapped : List Char :=\n"
            "      match k with\n"
            "      | OperandKind.modOp => ('(' :: inner) ++ [')']\n"
            "      | OperandKind.mulCluster => ('(' :: inner) ++ [')']\n"
            "      | _ => inner\n"
            "    return '-' :: wrapped",
            "prove_correct printNegatedFactor by\n"
            "  loom_solve <;> cases k <;> "
            "simp [renderNeg, needsParen, opWeight, negLevel]"),
        "rationale": (
            "a correct impl that is NOT definitionally equal to the frozen one: "
            "it selects the wrap by a per-kind `match` rather than by comparing "
            "`opWeight k` to `negLevel`, so `needsParen` never occurs in it and "
            "the residual C1 goal is not `rfl`-shaped (the frozen one-line proof "
            "does NOT close it — measured). Re-proven by case-splitting `k` and "
            "evaluating the ranks, both inside the elided tactic body, so the "
            "`method ... ensures` statement stays byte-identical. It agrees with "
            "gold at every (k, inner), so it MUST verify; if it could not be "
            "proven, the spec would be SPEC-TOO-STRONG — over-fit to the frozen "
            "rank-comparison FORM rather than to the wrap table it denotes. This "
            "is the soundness probe pos-control-direct and pos-control-local "
            "cannot perform, since both reduce to the frozen impl by `rfl`."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-composite-indomain. That case
    # discharged an in-domain `Assert` establishing that the site-B precondition
    # (40 <= level <= 70) admits the real F2P operand (level 50). This method
    # carries NO `require` clause (the pre-conditions region is empty) — the
    # operand is already abstracted to one of the five in-domain OperandKinds, so
    # there is no numeric domain bound to satisfy and the classic "the real F2P
    # operand is in-domain" probe is vacuous. Re-aimed at the residual total-domain
    # admissibility risk: that the six-clause post-image is jointly SATISFIABLE by
    # a gold-shaped computation (a spec no impl can meet reads exactly like one
    # every impl meets). The frozen impl discharging all six ensures IS that
    # witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the inputs carry no `require`, so the printer is total over every "
            "(k, inner) — the operand is already abstracted to an in-domain "
            "OperandKind, so there is no numeric domain bound to establish; the "
            "gold impl discharging all six ensures is the admissibility witness "
            "that the post-image (C1 plus the five per-kind consequence clauses) is "
            "jointly satisfiable. Near-trivial precisely because the precondition "
            "is empty. Re-aimed from the nagini admiss-composite-indomain, whose "
            "in-domain-level Assert has no counterpart once the operand is a kind "
            "rather than a raw int level. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the F2P. The `k` binder is
    # varied across all five OperandKinds and the `inner` binder across a
    # single- and a two-code-point sequence.
    # =====================================================================

    # ---- C2: the remainder operation must WRAP. Revert the remainder's strength
    # ---- to the function-call strength (the pre-fix MRO fall-through), leaving a
    # ---- remainder factor bare. This is Solution_prepatch_2 (= nagini
    # ---- model_prepatch_2 / weak-siteA-remainder-to-func).
    {
        "id": "weak-modop-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let w : Int := if k = OperandKind.modOp then (140 : Int) "
            "else opWeight k\n"
            "    let wrapped : List Char :=\n"
            "      if w ≤ negLevel then ('(' :: inner) ++ [')'] else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this reverts the remainder operation's binding strength to the generic "
            "function-call strength (the pre-fix MRO fall-through), so a remainder "
            "factor is left BARE under a leading minus. Its faithful real patch is "
            "the unpatched precedence table, whose remainder operand keeps the "
            "inherited function strength; the failing test asserts a negated "
            "remainder is parenthesized (`-(x % y)`, not `-x % y`), which the bare "
            "rendering does not produce, so it would NOT resolve. This is the exact "
            "defect the fix corrects (Solution_prepatch_2)."
        ),
        "rationale": (
            "REJECT from C2 (`k = .modOp → out = '-' :: ('(' :: inner ++ [')'])`) "
            "and C1: on the remainder kind the rival leaves the factor bare where "
            "the post-image demands it wrapped. Refuted at `(k = modOp, inner = "
            "['a'])`. Varies `k` to the modOp arm. If it verified => SPEC-TOO-WEAK "
            "(admits the bug)."
        ),
        "witness": _wit("OperandKind.modOp", "['a']"),
    },

    # ---- C3: the product cluster must WRAP. Revert the unary-minus threshold to
    # ---- the negated-product strength (below the multiplicative strength), so a
    # ---- product-cluster factor is left bare. This is Solution_prepatch (= nagini
    # ---- model_prepatch / weak-siteB-cutoff-to-additive). Witnessed at the
    # ---- mulCluster kind (the modOp kind is bare here too, but C3 is the arm this
    # ---- rival is sited on and mulCluster keeps it distinct from weak-modop-bare).
    {
        "id": "weak-mulcluster-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if opWeight k ≤ (80 : Int) then ('(' :: inner) ++ [')'] "
            "else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this reverts the unary-minus threshold to the negated-product strength "
            "(below the multiplicative strength), so a product-cluster factor — and "
            "a remainder factor — is left BARE. Its faithful real patch is the "
            "pre-fix parenthesization level; the failing regression asserts a "
            "negated product cluster is wrapped (`-(x*x*x*x)`, not `-x*x*x*x`), "
            "which the bare rendering does not produce, so it would NOT resolve. "
            "This is Solution_prepatch."
        ),
        "rationale": (
            "REJECT from C3 (`k = .mulCluster → out = '-' :: ('(' :: inner ++ "
            "[')'])`) and C1: on the product-cluster kind the rival leaves the "
            "factor bare where the post-image demands it wrapped. Refuted at `(k = "
            "mulCluster, inner = ['a'])` — a DISTINCT kind arm from weak-modop-bare "
            "(both would be bare under this threshold, but this rival is sited on "
            "and witnessed at the mulCluster arm), so the battery varies `k`. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _wit("OperandKind.mulCluster", "['a']"),
    },

    # ---- C4: a power factor must stay BARE. Push the threshold UP to the power
    # ---- strength, so a power factor is now over-wrapped. This is nagini
    # ---- weak-siteB-cutoff-to-power (the threshold must be strictly below the
    # ---- power strength).
    {
        "id": "weak-power-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if opWeight k ≤ (120 : Int) then ('(' :: inner) ++ [')'] "
            "else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this pushes the unary-minus threshold up to the power strength, so a "
            "power factor under a leading minus is now WRAPPED where it must stay "
            "bare. Its faithful real patch would parenthesize a negated power "
            "operand (`-(x**3)` instead of `-x**3`), a different rendering than the "
            "gold's — the threshold must be strictly BELOW the power strength; the "
            "printer tests that pin power operands bare would fail, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C4 (`k = .power → out = '-' :: inner`) and C1: on the "
            "power kind the rival wraps the factor where the post-image demands it "
            "bare. Refuted at `(k = power, inner = ['a'])`. Varies `k` to the power "
            "arm. If it verified => SPEC-TOO-WEAK (over-wraps a power operand)."
        ),
        "witness": _wit("OperandKind.power", "['a']"),
    },

    # ---- C5: an atomic factor must stay BARE. Over-wrap the atomic kind only.
    # ---- ADDED (no direct nagini sibling — nagini's site-B domain top was the
    # ---- function level 70; the atomic kind carries an even higher strength here
    # ---- and must stay bare). Completes the bare-arm coverage.
    {
        "id": "weak-atomic-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if needsParen k || k == OperandKind.atomic then "
            "('(' :: inner) ++ [')'] else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this wraps a bare atom under a leading minus (`-(x)` instead of `-x`). "
            "A real patch of this shape would parenthesize a negated symbol or "
            "number, changing the rendering of the most common operand; the printer "
            "tests that pin atoms bare would fail, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C5 (`k = .atomic → out = '-' :: inner`) and C1: on the "
            "atomic kind the rival wraps the factor where the post-image demands it "
            "bare. Refuted at `(k = atomic, inner = ['a'])` — a distinct bare-kind "
            "arm from weak-power-wrapped, varying `k`. If it verified => "
            "SPEC-TOO-WEAK (over-wraps an atom)."
        ),
        "witness": _wit("OperandKind.atomic", "['a']"),
    },

    # ---- C6: a function-call factor must stay BARE. Over-wrap the funcCall kind
    # ---- only. ADDED — completes coverage of every bare arm of the wrap table so
    # ---- no per-kind consequence clause is left unattacked.
    {
        "id": "weak-funccall-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if needsParen k || k == OperandKind.funcCall then "
            "('(' :: inner) ++ [')'] else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this wraps a self-delimited function-call factor under a leading minus "
            "(`-(f(x))` instead of `-f(x)`). A real patch of this shape would "
            "parenthesize a negated function call, which is already self-delimited "
            "and must stay bare; the printer tests that pin function operands bare "
            "would fail, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C6 (`k = .funcCall → out = '-' :: inner`) and C1: on the "
            "function-call kind the rival wraps the factor where the post-image "
            "demands it bare. Refuted at `(k = funcCall, inner = ['a'])` — the "
            "fifth and last kind arm, so every arm of the wrap table (modOp, "
            "mulCluster, power, atomic, funcCall) is attacked by some rival. If it "
            "verified => SPEC-TOO-WEAK (over-wraps a function call)."
        ),
        "witness": _wit("OperandKind.funcCall", "['a']"),
    },

    # ---- C1 / C2, the `inner` binder — PARTIAL-DOMAIN over the factor body. Wrap
    # ---- only the FIRST code point of `inner`, leaving the rest outside the
    # ---- parentheses. Correct at a single-code-point factor (agrees with gold),
    # ---- wrong at any multi-code-point factor. This is the value-proxy /
    # ---- partial-domain attack a fuzzer that only varies `k` never constructs,
    # ---- and it is the ONLY rival that moves the `inner` binder off ['a'].
    {
        "id": "weak-partial-inner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if needsParen k then (('(' :: inner.take 1) ++ [')']) "
            "++ inner.drop 1 else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this parenthesizes only the first code point of the factor body, "
            "leaving the remainder outside the parentheses (`-(x % y` printed as "
            "`-(x) % y`-shaped). A real patch of this shape would enclose only the "
            "leading piece of a multi-token factor, so the leading minus still "
            "fails to govern the whole factor — exactly the mis-parenthesization "
            "the fix targets; the failing test asserts the WHOLE factor is enclosed "
            "(`-(x % y)`), which a single-token wrap does not produce, so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = renderNeg k inner`) / C2: for a wrapped kind, "
            "`renderNeg` encloses the WHOLE `inner`, so a rival wrapping only "
            "`inner.take 1` diverges on any factor body of length ≥ 2. Refuted at "
            "`(k = modOp, inner = ['a', 'b'])` — the ONLY witness that moves the "
            "`inner` binder off the single code point ['a'], and a genuine "
            "near-miss (it agrees with gold at every single-code-point factor, so "
            "it is refuted only on the length-≥2 sub-domain). If it verified => "
            "SPEC-TOO-WEAK (the `inner` binder unpinned beyond its first element)."
        ),
        "witness": _wit("OperandKind.modOp", "['a', 'b']"),
    },

    # ---- C1 / C2, the `inner` binder — the EMPTY factor body. ADDED BY AUDIT.
    # ---- Every rival above holds `inner` non-empty (['a'] or ['a','b']), so the
    # ---- length-0 point of the `inner` binder was unattacked: a rival free to do
    # ---- anything at `inner = []` was admitted by no case in the battery. This
    # ---- one suppresses the wrap exactly there, agreeing with gold at every
    # ---- non-empty factor body — so it is refutable ONLY at the empty one, the
    # ---- sharpest sub-domain near-miss the `inner` binder has.
    {
        "id": "weak-empty-inner-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let wrapped : List Char :=\n"
            "      if needsParen k && !inner.isEmpty then "
            "('(' :: inner) ++ [')'] else inner\n"
            "    return '-' :: wrapped"),
        "refinement": (
            "this suppresses the parentheses when the factor's printed form is "
            "empty, so an empty-bodied factor of a wrapped kind renders without "
            "the enclosing parentheses that the leading minus needs to govern it. "
            "A real patch of this shape carries a guard that skips the enclosing "
            "step on an empty rendering; the pinned behaviour encloses a wrapped "
            "kind unconditionally, so the two disagree wherever the factor's own "
            "rendering is empty and the patch would NOT reproduce the required "
            "output there. It is a strictly harder near-miss than "
            "weak-partial-inner: it agrees with gold on EVERY non-empty factor "
            "body, so nothing but the length-0 point refutes it."
        ),
        "rationale": (
            "REJECT from C2 (`k = .modOp → out = '-' :: ('(' :: inner ++ [')'])`) "
            "and C1: the post-image encloses a wrapped kind at EVERY `inner`, "
            "including the empty one, where this rival emits a bare `['-']`. "
            "Refuted at `(k = modOp, inner = [])` — the third distinct point of "
            "the `inner` binder (alongside ['a'] and ['a','b']) and the only case "
            "attacking length 0. Verified by build that the shipped `(modOp, "
            "['a'])` witness does NOT refute this rival (it agrees with gold "
            "there), so this case is not subsumed by weak-modop-bare. If it "
            "verified => SPEC-TOO-WEAK (the `inner` binder unpinned at length 0)."
        ),
        "witness": _wit("OperandKind.modOp", "([] : List Char)"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling has 9 SPEC cases (3 soundness, 1 admissibility, 5
# uniqueness) plus a 2-case AXIOM lane. It contracts THREE pure int/bool
# functions over the SAME two-site fix: `remainder_operand_level()` (site A — the
# post-fix remainder strength as an int, Ensures == 50), `negated_single_operand_
# enclosed(lvl)` (site B — the wrap decision as a function of an int level, with a
# 40..70 Requires and two consequence clauses), and an illustrative composite. This
# velvet bundle FUSES both sites into ONE decision `printNegatedFactor`: the
# operand is abstracted to its strength CLASS `k : OperandKind` (five kinds) and
# the two edits become the single per-kind wrap table `needsParen`. So the nagini
# integer-band attacks re-express as per-KIND attacks, and the site-A value
# function has no separately-observable counterpart.
#
#   nagini case                        -> here                     disposition
#   -----------------------------------------------------------------------
#   pos-control-siteB-local            -> pos-control-local          RE-EXPRESSED
#   pos-control-siteA-local            -> (merged into pos-control-local)
#   pos-control-echo-grounded          -> pos-control-direct         RE-EXPRESSED
#   admiss-composite-indomain          -> admiss-gold-total          RE-AIMED
#   weak-siteB-cutoff-to-additive      -> weak-mulcluster-bare       RE-EXPRESSED
#   weak-siteB-cutoff-to-power         -> weak-power-wrapped          PORTED
#   weak-siteB-strict-flip             -> (none)                      VACUOUS (carrier)
#   weak-siteA-remainder-to-func       -> weak-modop-bare             RE-EXPRESSED
#   weak-siteA-remainder-to-additive   -> (none)                      NOT WRONG here
#   weak-composite-bare                -> weak-modop-bare (subsumed)   RE-SITED
#   (no sibling)                       -> weak-atomic-wrapped          ADDED
#   (no sibling)                       -> weak-funccall-wrapped        ADDED
#   (no sibling)                       -> weak-partial-inner           ADDED
#   (no sibling)                       -> pos-control-kindmatch        ADDED (audit)
#   (no sibling)                       -> weak-empty-inner-bare        ADDED (audit)
#   AXIOM_TESTS (2)                    -> (none)                      DROPPED (G-AX)
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness.
#
# ADDED BY AUDIT (2). The port's SOUND was re-derived case by case with real
# builds; every shipped case behaved as declared and every witness discriminated
# semantically. Two GAPS were found and closed, neither of which the gate can see:
#  * pos-control-kindmatch. Both original positives are DEFINITIONALLY EQUAL to
#    the frozen impl (`renderNeg k inner` unfolds by `rfl`; a `let` for
#    `needsParen k` zeta-reduces), which is why both close under the byte-
#    identical frozen `loom_solve` — so neither could ever detect a spec over-fit
#    to the frozen rank-comparison SHAPE. The added positive decides the wrap by
#    matching on the kind, never mentions `needsParen`, and leaves a residual C1
#    goal the frozen one-liner does NOT close (measured: exit 1, `unsolved goals`
#    at `ensures_6`). Re-proven inside the elided tactic body; verifies (exit 0).
#    So the spec admits a faithful correct impl on its SEMANTICS, not its syntax.
#  * weak-empty-inner-bare. Every original rival held `inner` non-empty, leaving
#    the length-0 point of the `inner` binder attacked by nothing: a rival free to
#    do anything at `inner = []` was admitted by no case. Confirmed not subsumed —
#    the shipped `(modOp, ['a'])` witness does NOT refute the new rival (exit 1),
#    because it agrees with gold at every non-empty body.
#
# RE-EXPRESSED / MERGED (positives): pos-control-siteB-local + pos-control-siteA-
#   local both reshape their site through a typed local; on this fused carrier
#   there is one decision, so they merge into pos-control-local (bind `needsParen
#   k` to a local Bool). pos-control-echo-grounded -> pos-control-direct: the
#   nagini grounded-oracle honest control recomputed the cut-off inline; here the
#   whole decision IS the transparent `renderNeg`, so the honest cheapest impl
#   returns it directly. Both verified to build with the frozen proof unchanged.
# RE-AIMED (admiss-composite-indomain -> admiss-gold-total): the nagini case
#   asserted the real F2P operand level (50) lies in the site-B Requires [40,70].
#   Here the operand is abstracted to an in-domain kind, so there is no numeric
#   domain bound to establish and the method has no `require`; re-aimed at the
#   residual total-domain risk (post-image joint satisfiability), witnessed by the
#   frozen impl discharging all six ensures. Verified to build.
# RE-EXPRESSED / PORTED (band attacks -> per-kind attacks):
#  * weak-siteA-remainder-to-func -> weak-modop-bare. Revert the remainder's
#    strength to the function level; a remainder factor is left bare. = the
#    modeled Solution_prepatch_2, the exact defect the fix corrects.
#  * weak-siteB-cutoff-to-additive -> weak-mulcluster-bare. Revert the threshold
#    below the multiplicative strength; a product-cluster factor is left bare. =
#    Solution_prepatch. Sited/witnessed on the mulCluster arm to keep it distinct
#    from weak-modop-bare (both kinds go bare under this threshold).
#  * weak-siteB-cutoff-to-power -> weak-power-wrapped. Push the threshold up to the
#    power strength; a power factor is over-wrapped. The threshold must be strictly
#    below the power strength — carried intact.
#  All three refinement arguments carry over verbatim (unpatched precedence table
#  / pre-fix parenthesization level / power operand must stay bare), each backed by
#  a machine-checked witness (rival exit 0, full rival non-verify, gold build fail).
# RE-SITED (weak-composite-bare): the nagini composite returned the OPPOSITE
#   boolean (a negated remainder left bare). On this carrier there is no separate
#   composite function — the observable "a negated remainder is left bare" IS
#   weak-modop-bare, so the composite attack is subsumed by it rather than
#   duplicated.
# ADDED (3, NOT fabricated wrongness — real per-kind/per-binder divergences):
#  * weak-atomic-wrapped, weak-funccall-wrapped over-wrap the two remaining bare
#    kinds. The nagini file leans on its site-B integer domain (top = function
#    level 70) to catch these implicitly; here each per-kind consequence clause
#    (C5 atomic, C6 funcCall) is a distinct arm that needs a distinct rival, so
#    every arm of the five-kind wrap table is attacked by some rival.
#  * weak-partial-inner wraps only the first code point of `inner` — the ONLY
#    rival that moves the `inner` binder off ['a'], a genuine partial-domain
#    near-miss (correct at every single-code-point factor, wrong at length ≥ 2).
# VACUOUS on this carrier (weak-siteB-strict-flip): the nagini rival flips the
#   parenthesize mode to strict=True, differing from gold at the SINGLE integer
#   point level == cut-off (55). This carrier models operand strengths as five
#   DISCRETE kind ranks with NO rank at exactly the threshold negLevel=110
#   (modOp=100, power=120), so there is no band point / strict boundary to flip —
#   the abstraction to kinds collapses the single-integer-point distinction the
#   nagini case attacked. No rival can express it and no witness could
#   discriminate one; not fabricated.
#   AUDIT: re-derived independently and DEMONSTRATED rather than argued. The
#   faithful re-expression is the impl that compares with strict `<` instead of
#   `≤` (`if opWeight k < negLevel then ...`). Built: it VERIFIES against the
#   frozen spec (exit 0, `loom_solve` + case-split on `k`). Verifying means it is
#   a CORRECT impl here, so it could only ever be a positive, never a reject —
#   confirming the collapse. Since no rank equals 110, `<` and `≤` induce the same
#   wrap table, and the drop is right for the stated reason.
# NOT WRONG here (weak-siteA-remainder-to-additive): the nagini rival returns the
#   remainder LEVEL as 40 (additive) instead of 50, wrong because the site-A
#   Ensures pins the exact int value. On this carrier `opWeight .modOp` is not a
#   contracted value — only the WRAP decision is observable, and a remainder at
#   the additive strength (an even lower rank) is STILL ≤ the threshold, so it is
#   still wrapped == gold's observable. The rival is not wrong on this carrier's
#   modeled behaviour (the abstraction to the wrap decision collapses the exact
#   integer value the nagini case pinned). Dropped, said so.
#   AUDIT: re-derived independently and DEMONSTRATED. The faithful re-expression
#   drops the modOp rank to the additive strength (2*40 = 80) while leaving the
#   comparison intact. Built: it VERIFIES against the frozen spec (exit 0), so it
#   is a correct impl on this carrier and cannot be a reject case — an
#   expect="reject" entry for it would have been fabricated wrongness. Right call.
# DROPPED (AXIOM_TESTS x2): the nagini axiom-soundness / caller-domain-containment
#   probes over the real sympy `precedence` / printer callees are G-AX's job (this
#   bundle declares no axiom — the changed op is modeled DEEPLY in the `pure`
#   region and validated by conformance_check.py / G-CONF against the patched
#   renderer); the G-PBT gate ignores AXIOM_TESTS regardless.
#
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
# CLAUSE / BINDER / POINT COVERAGE. C1 (master) is attacked by all seven rivals;
#   its five per-kind consequence clauses are each attacked by a dedicated rival —
#   C2/modOp (weak-modop-bare), C3/mulCluster (weak-mulcluster-bare), C4/power
#   (weak-power-wrapped), C5/atomic (weak-atomic-wrapped), C6/funcCall
#   (weak-funccall-wrapped) — and the `inner` sub-domain by weak-partial-inner
#   (length ≥ 2) and weak-empty-inner-bare (length 0). The three positives and the
#   admissibility case defend all six clauses (all discharge on gold). Input
#   binders: `k` is varied across ALL FIVE OperandKinds (modOp, mulCluster, power,
#   atomic, funcCall); `inner` is varied across THREE lengths — [] (weak-empty-
#   inner-bare), ['a'], and ['a','b'] (weak-partial-inner). No binder is held fixed
#   by every witness. Seven reject witnesses probe SEVEN distinct input points.
#   The variation is MEANINGFUL, not two spellings of one point: each witness
#   point is one where its rival's output DIFFERS from gold's, and the two `inner`
#   rivals are mutually non-subsuming (measured: the (modOp, ['a']) witness does
#   not refute weak-empty-inner-bare, and weak-partial-inner is refutable only at
#   length ≥ 2).
# WITNESS DISCRIMINATION (re-derived by the audit with real builds, not carried
#   over from authoring): the carrier is fully transparent, so each witness pins
#   both inputs to concrete literals and closes `printNegatedFactorTester k inner
#   = false` by `decide`. Because the FROZEN impl is ALSO loop-free, its tester
#   computes `true` (postcondition holds everywhere), so `= false` is provably
#   FALSE on gold and the gold build FAILS; each rival's tester computes `false` at
#   its witness point, so `= false` closes and the rival build SUCCEEDS. Measured
#   for all seven: witness-vs-rival exit 0, full-rival verify exit 1 (does not
#   verify), witness-vs-gold exit 1 with the SEMANTIC message `Tactic `decide`
#   proved that the proposition ... is false` — a refutation the kernel actually
#   performed, not a missing identifier, type error, unfolding failure or timeout.
#   The gold side's exit code is load-bearing and was checked to carry
#   information: the OPPOSITE claim (`... = true`) ELABORATES against gold (exit 0)
#   and is refuted against a rival (exit 1), so both truth values are reachable and
#   a forged witness asserting a rival CORRECT could not pass. No witness binds a
#   hypothesis, so no consistency probe is needed (the gate agrees: probe=none for
#   every case). No sorry/admit/native_decide/axiom/opaque appears.
# SPEC STRENGTH PROBED INDEPENDENTLY BY THE AUDIT (attacks D and E), and no hole
#   was found. Wrong impls NOT in the battery, each built against the frozen spec:
#   drop the leading minus; parenthesize the minus along with the factor; always
#   bare; always wrapped; wrap only the LAST code point; suppress the wrap on an
#   empty body; a nondeterministically chosen wrap flag. All seven were REJECTED
#   (exit 1) — the last is now shipped as weak-empty-inner-bare. Correct reshapes:
#   the `!needsParen` complement and `['-'] ++ wrapped` verify under the frozen
#   proof; the per-kind `match` and the explicit-disjunction form verify once
#   re-proven (now shipped as pos-control-kindmatch). No faithful correct impl was
#   found that the spec rejects, and no wrong impl that it admits.
AXIOM_TESTS = []
