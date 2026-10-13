"""properties.py — G-PBT falsification battery for sympy__sympy-19783 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and each ``prove_correct`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted product-dispatch methods over a finite carrier
``QExpr`` of symbolic quantum expressions — a plain operator ``op``, the identity
``ident``, a Hermitian-conjugate object ``dag e``, and an ordinary product
``mul a b``; all four carriers derive ``DecidableEq``, so every point below
``decide``s):

  daggerProduct (self other : QExpr) return (out : QExpr)
      require isDaggerClass self = true
      ensures out = daggerProd self other                              -- master
      -- daggerProd self other = if isIdentityClass other then self else mul self other
      --   D-COLLAPSE : a conjugate object times the identity collapses to the
      --                conjugate object itself (out = self);
      --   D-FALL     : times anything else it is the ordinary product mul self other.

  identityProduct (self other : QExpr) return (out : QExpr)
      require self = QExpr.ident
      ensures out = identityProd self other                            -- master
      -- identityProd self other =
      --   if isOperatorClass other || isDaggerClass other then other else mul self other
      --   I-COLLAPSE : the identity times an operator OR a conjugate object
      --                collapses to that operand (out = other) — the conjugate
      --                arm is the behaviour that must be covered as well as the
      --                operator arm;
      --   I-FALL     : times anything else it is the ordinary product mul self other.

Both ``daggerProd`` and ``identityProd`` are total, fully-unfolded pure ``def``s
over the methods' own arguments in the ``pure`` region; the ``axioms`` region is
EMPTY (there is no opaque answer key to echo — directive 8: the post-image is
grounded in the actual input carrier). The membership tests
``isOperatorClass`` / ``isDaggerClass`` / ``isIdentityClass`` are concrete
structural ``def``s, so ``decide`` reduces every witness fully.

BINDERS. ``daggerProduct`` carries TWO free binders — ``self`` (any conjugate
object, ``require isDaggerClass self``) and ``other`` (any shape). ``self`` is a
genuine variable here (the sibling carrier abstracted the receiver away into a
kind tag); the reject witnesses move it across three distinct conjugate objects,
and one rival (``uniq-dag-collapse-ignores-receiver``) can be refuted ONLY by
moving it, so the binder is genuinely probed and not merely varied.
``identityProduct``'s ``self`` is pinned to ``ident`` by its ``require``, so its
one free binder is ``other``, which the witnesses move across the operator, the
conjugate-object, and the product-node shapes.

ADVERSARIAL READ of the sibling classes on this carrier (case-by-case in the
footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The sibling records this class as
    already N/A there (the only parameter is a pass-by-value kind tag; each
    ``__mul__`` builds a fresh result and mutates no operand). Lean/Velvet are
    referentially transparent a fortiori: every input is an immutable value, no
    method declares a ``mut`` binder, there is no heap and no aliasing. No
    substitute probe is fabricated (porting map: dropped, not replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The
    post-images are pinned to ``daggerProd`` / ``identityProd`` — concrete
    ``def``s over the methods' own arguments (empty ``axioms`` region; no opaque
    callee). The only satisfier is the grounded dispatch itself.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``if`` over immutable
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
  * PARTIAL-DOMAIN / VALUE — the heart of this surface, ported in full. A rival
    gets the dispatch right on part of the shape domain but diverges on one
    sub-behaviour (drops a collapse arm, over-absorbs a fall-through shape,
    returns the wrong surviving operand, or mis-builds the ordinary product).

WITNESS MECHANICS. Every frozen impl is a loop-free ``if``/``return`` over a
finite ``DecidableEq`` carrier, so the extracted tester reduces under ``decide``.
Each reject rival is likewise loop-free, so its tester ``decide``s too. Each
reject case therefore carries a machine-checked refutation ``witness`` — a Velvet
tester statement ``<method>Tester self other = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` blocks are stripped so no tactic script
can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester ``decide``s to ``false``) and FAILS against the frozen solution (gold's
tester is ``true``, so ``= false`` is refuted), so each rejection is a genuine
spec refutation, not mechanical tactic breakage. Every witness input satisfies
its method's ``require`` clause (``daggerProduct``'s ``self`` is always a ``dag``
node; ``identityProduct``'s ``self`` is always ``ident``), so none is vacuously
excluded by a false precondition.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed axioms; the three
membership tests are deep-model A-references validated by G-AX, not obligations
this manifest probes. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19783"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The two frozen impl bodies, verbatim — everything strictly BETWEEN the
# ---- `-- impl-start` / `-- impl-end` markers (comments included) lives inside
# ---- the elided impl region. Every variant edits ONLY one of these blocks (and,
# ---- for reshapes/admissibility, the elided `prove_correct` tactic body), so
# ---- the spec view is untouched and same_spec holds by construction. Each anchor
# ---- is asserted unique in the file at load.
_IMPL_DAG = (
    "    -- When `other` is the identity operator the product collapses to `self`;\n"
    "    -- otherwise emit the ordinary product of the two operands.\n"
    "    if isIdentityClass other then\n"
    "      return self\n"
    "    else\n"
    "      return QExpr.mul self other"
)
_IMPL_ID = (
    "    -- When `other` is an operator or a Hermitian-conjugate object the product\n"
    "    -- collapses to `other`; otherwise emit the ordinary product.\n"
    "    if isOperatorClass other || isDaggerClass other then\n"
    "      return other\n"
    "    else\n"
    "      return QExpr.mul self other"
)
assert _BASE.count(_IMPL_DAG) == 1, "daggerProduct impl region drifted"
assert _BASE.count(_IMPL_ID) == 1, "identityProduct impl region drifted"

# ---- The two frozen proof bodies, verbatim. A correct reshape / admissibility
# ---- case may retune the relevant block (it is elided from the spec view);
# ---- rivals leave both as-is, so the wrong impl leaves the postcondition goal
# ---- unsolved and the rival MODULE fails to build — which is what
# ---- expect="reject" requires. The witness, not the module build, attributes
# ---- the rejection to the spec.
_PROOF_DAG = "prove_correct daggerProduct by\n  loom_solve <;> simp_all [daggerProd]"
_PROOF_ID = "prove_correct identityProduct by\n  loom_solve <;> simp_all [identityProd]"
assert _BASE.count(_PROOF_DAG) == 1, "daggerProduct proof region drifted"
assert _BASE.count(_PROOF_ID) == 1, "identityProduct proof region drifted"


def _variant_dag(body):
    """Swap ONLY daggerProduct's impl body (identityProduct stays gold)."""
    return _swap(_BASE, _IMPL_DAG, body)


def _variant_id(body):
    """Swap ONLY identityProduct's impl body (daggerProduct stays gold)."""
    return _swap(_BASE, _IMPL_ID, body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<method>Tester self other = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` blocks are stripped, so no tactic script can
# ---- mask the verdict; both the rival and the frozen impl are loop-free over a
# ---- DecidableEq carrier, so both testers reduce under `decide`.
def _witness_dag(call):
    return ("extract_program_for daggerProduct\n"
            "prove_precondition_decidable_for daggerProduct\n"
            "prove_postcondition_decidable_for daggerProduct\n"
            "derive_tester_for daggerProduct\n\n"
            f"example : {call} = false := by\n  decide\n")


def _witness_id(call):
    return ("extract_program_for identityProduct\n"
            "prove_precondition_decidable_for identityProduct\n"
            "prove_postcondition_decidable_for identityProduct\n"
            "derive_tester_for identityProduct\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. BOTH dispatches are rewritten
    # to handle the non-collapse (fall-through) case FIRST via the negated guard,
    # then collapse. Behaviourally identical on every shape; the frozen proofs
    # still close the byte-identical obligations. Verified out-of-band with a real
    # build.
    # =====================================================================
    {
        "id": "pos-negated-guard-both-sites",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_DAG,
                  "    -- Handle the non-collapse case first via the negated guard.\n"
                  "    if !(isIdentityClass other) then\n"
                  "      return QExpr.mul self other\n"
                  "    else\n"
                  "      return self"),
            _IMPL_ID,
            "    -- Handle the non-collapse case first via the negated guard.\n"
            "    if !(isOperatorClass other || isDaggerClass other) then\n"
            "      return QExpr.mul self other\n"
            "    else\n"
            "      return other"),
        "rationale": "both dispatches are rewritten to test the negated collapse "
                     "guard and emit the ordinary product first, collapsing "
                     "otherwise — behaviourally identical on every shape, so "
                     "`out = daggerProd self other` and `out = identityProd self "
                     "other` still hold on the whole domain. A correct reshape must "
                     "verify, else SPEC-TOO-STRONG on guard polarity.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — each impl returns its pure model directly
    # rather than inlining the branch. Observationally identical; the ensures IS
    # `out = <model> self other`, so the body is definitionally the RHS and the
    # frozen proofs close. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-direct-model-both-sites",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_DAG, "    return daggerProd self other"),
            _IMPL_ID, "    return identityProd self other"),
        "rationale": "each impl returns its pure dispatch model directly rather "
                     "than inlining the branch. Identical value on every input, so "
                     "the post-images hold on the whole domain. A faithful reshape "
                     "MUST verify, else the postcondition would reject its own "
                     "model's output.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe self-calls the two discriminating inputs
    # to force the precondition to discharge. On this backend the residual
    # admissibility risk is that the post-image is UNSATISFIABLE / DEGENERATE at
    # the interesting point (a spec no impl can meet reads like a spec every impl
    # meets). ONE in-region assert, at the two F2P-discriminating inputs
    # (I * Dagger(O) and Dagger(O) * I), asserts the dispatch is NON-DEGENERATE:
    # the identity times a conjugate object collapses to that conjugate object
    # (and is NOT left an ordinary product), and a conjugate object times the
    # identity collapses to the conjugate object — the two behaviours the failing
    # tests demand. The impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra assert goal by
    # `decide` (elided from the spec view). The assert is LIVE: a false claim about
    # the same points leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-discriminating-collapses",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_ID,
                  "    assert (with_name_prefix `admiss\n"
                  "      (isDaggerClass (QExpr.dag (QExpr.op \"A\")) = true\n"
                  "        ∧ identityProd QExpr.ident (QExpr.dag (QExpr.op \"A\")) = QExpr.dag (QExpr.op \"A\")\n"
                  "        ∧ daggerProd (QExpr.dag (QExpr.op \"A\")) QExpr.ident = QExpr.dag (QExpr.op \"A\")\n"
                  "        ∧ identityProd QExpr.ident (QExpr.dag (QExpr.op \"A\"))\n"
                  "            ≠ QExpr.mul QExpr.ident (QExpr.dag (QExpr.op \"A\"))))\n"
                  + _IMPL_ID),
            _PROOF_ID,
            "prove_correct identityProduct by\n"
            "  loom_solve <;> first\n"
            "    | decide\n"
            "    | simp_all [identityProd]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the two "
                     "F2P-discriminating inputs: the identity times a conjugate "
                     "object collapses to that conjugate object (and is NOT left an "
                     "ordinary product), and a conjugate object times the identity "
                     "collapses to the conjugate object — the behaviours the failing "
                     "tests demand. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable/degenerate at the interesting "
                     "point); the impl is kept verbatim so the method's own ensures "
                     "discharges too. Discharged by `decide` on the two constants.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "uniq-id-prepatch-dagger-not-absorbed",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH site 1: the identity absorbs only operator operands; a
        # conjugate object on the right is NOT absorbed, so it falls through to an
        # ordinary product. This is the identity dispatch reverted to test only the
        # operator class.
        "module": _variant_id(
            "    if isOperatorClass other then\n"
            "      return other\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "this IS the pre-patch identity dispatch (operator-only "
                      "collapse). A faithful counterpart leaves the identity times "
                      "a conjugate object as an unevaluated ordinary product instead "
                      "of the conjugate object, so the failing assertion "
                      "`I * Dagger(O) == Dagger(O)` stays false — the instance stays "
                      "unresolved.",
        "rationale": "REJECT from `out = identityProd self other` via I-COLLAPSE on "
                     "the conjugate-object sub-domain: the post-image collapses to "
                     "`other` when `isDaggerClass other`, the rival returns the "
                     "ordinary product. Refuted at other = a conjugate object — the "
                     "exact antecedent the fix adds.",
        "witness": _witness_id(
            'identityProductTester QExpr.ident (QExpr.dag (QExpr.op "A"))'),
    },
    {
        "id": "uniq-dag-prepatch-identity-not-absorbed",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH site 2: a conjugate object has no dedicated product rule, so
        # every product is the generic ordinary product, even against the identity.
        "module": _variant_dag("    return QExpr.mul self other"),
        "refinement": "this IS the absence of the conjugate-object product rule "
                      "(the generic fallback always builds an ordinary product). A "
                      "faithful counterpart leaves a conjugate object times the "
                      "identity as an ordinary product instead of the conjugate "
                      "object, so the failing assertions `Dagger(O) * I == Dagger(O)` "
                      "and `Dagger(O) * Dagger(I) == Dagger(O)` stay false — the "
                      "instance stays unresolved.",
        "rationale": "REJECT from `out = daggerProd self other` via D-COLLAPSE: the "
                     "post-image collapses to `self` when `isIdentityClass other`, "
                     "the rival returns the ordinary product. Refuted at "
                     "other = ident.",
        "witness": _witness_dag(
            'daggerProductTester (QExpr.dag (QExpr.op "A")) QExpr.ident'),
    },
    {
        "id": "uniq-id-overabsorb-product-node",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-absorb (site 1): collapse on EVERY shape, including a product-node
        # operand (the carrier's fall-through shape — a scalar/other factor). The
        # spec requires the identity times such a factor to stay an ordinary
        # product. A DISJOINT sub-domain from the prepatch rival (fall-through
        # shape, not the conjugate-object arm).
        "module": _variant_id("    return other"),
        "refinement": "over-absorbs: collapses on the fall-through shape too. A "
                      "faithful counterpart would make the identity times a "
                      "scalar/other factor return that factor instead of an ordinary "
                      "product, so the failing assertion `isinstance(I * x, Mul)` "
                      "stays false (I*x would be x) — the instance stays unresolved.",
        "rationale": "REJECT from `out = identityProd self other` via I-FALL on the "
                     "product-node sub-domain: the post-image is `mul self other` "
                     "there, the rival returns `other`. A DISJOINT sub-domain from "
                     "the prepatch rival (fall-through shape vs the conjugate arm).",
        "witness": _witness_id(
            'identityProductTester QExpr.ident (QExpr.mul (QExpr.op "A") (QExpr.op "B"))'),
    },
    {
        "id": "uniq-dag-overabsorb-operator",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-absorb (site 2): the conjugate object also collapses against a plain
        # operator, claiming the product simplifies to the conjugate object where
        # the spec requires an ordinary product. Distinct sub-domain from the site-2
        # prepatch rival (operator, not the identity).
        "module": _variant_dag(
            "    if isIdentityClass other || isOperatorClass other then\n"
            "      return self\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "over-absorbs: collapses against a plain operator too. A "
                      "faithful counterpart would make a conjugate object times an "
                      "operator return the conjugate object, dropping the operator "
                      "factor entirely, so the failing assertion that pins the "
                      "three-factor form `Dagger(O)*O*I` to the product of the two "
                      "operands times the identity no longer holds (the left side "
                      "would collapse to Dagger(O)*I while the right keeps both "
                      "factors), and the assertion pinning a conjugate times itself "
                      "to its square breaks the same way — the instance stays "
                      "unresolved.",
        "rationale": "REJECT from `out = daggerProd self other` via D-FALL on the "
                     "operator sub-domain: the post-image is `mul self other` there, "
                     "the rival returns `self`. Distinct sub-domain from the site-2 "
                     "prepatch rival (operator vs identity).",
        "witness": _witness_dag(
            'daggerProductTester (QExpr.dag (QExpr.op "B")) (QExpr.op "A")'),
    },
    {
        "id": "uniq-dag-overabsorb-dagger-shape",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-absorb (site 2), the conjugate-SHAPE sub-domain: the conjugate
        # object also collapses against another conjugate object, claiming the
        # product simplifies to the left operand where the spec requires an
        # ordinary product. Added by audit: every other daggerProduct rival moves
        # `other` only over {ident, op _}, so `other = dag _` was the one
        # daggerProd sub-domain no rival distinguished — and it is a shape the two
        # sites treat OPPOSITELY (identityProd collapses on it, daggerProd does
        # not), which is exactly where a dispatch is most likely to be
        # cross-contaminated.
        "module": _variant_dag(
            "    if isIdentityClass other || isDaggerClass other then\n"
            "      return self\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "over-absorbs the conjugate shape: it carries the OTHER "
                      "site's collapse condition across, absorbing a conjugate "
                      "right operand. A faithful counterpart would make a conjugate "
                      "object times another conjugate object return the left "
                      "conjugate alone, dropping the right factor, so the failing "
                      "assertion pinning a conjugate times itself to its square "
                      "breaks (the left side would be the bare conjugate, not its "
                      "square) — the instance stays unresolved.",
        "rationale": "REJECT from `out = daggerProd self other` via D-FALL on the "
                     "conjugate-shape sub-domain: `isIdentityClass (dag _)` is "
                     "false, so the post-image is `mul self other` there, while the "
                     "rival returns `self`. The only rival moving daggerProduct's "
                     "`other` binder onto the conjugate shape — the shape the two "
                     "dispatches treat oppositely.",
        "witness": _witness_dag(
            'daggerProductTester (QExpr.dag (QExpr.op "A")) (QExpr.dag (QExpr.op "B"))'),
    },
    {
        "id": "uniq-dag-collapse-ignores-receiver",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (site 2), the RECEIVER facet: the collapse decision is correct on
        # every shape AND the collapse branch returns a conjugate object (so it is
        # not the wrong-surviving-operand rival either) — but it returns a FIXED
        # conjugate object rather than the receiver `self`. Added by audit: the
        # mirror of uniq-id-wrong-fallthrough-left-operand on the site where the
        # receiver is a genuine free binder, and the only rival whose refutation
        # REQUIRES moving `self` (at self = dag (op "A") this rival is correct;
        # verified out-of-band that the witness there fails against the rival too,
        # so `self` carries the discrimination).
        "module": _variant_dag(
            "    if isIdentityClass other then\n"
            "      return QExpr.dag (QExpr.op \"A\")\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "the collapse decision is left correct on every shape and the "
                      "survivor is still a conjugate object, so neither a "
                      "collapse-bit fuzzer nor a survivor-shape check sees it; but "
                      "the surviving conjugate is a FIXED one instead of the "
                      "receiver. A faithful counterpart would return some other "
                      "conjugate object when a conjugate is multiplied by the "
                      "identity, so the failing assertions pinning that product to "
                      "the receiver itself stay false for every receiver but the "
                      "hard-coded one — the instance stays unresolved.",
        "rationale": "REJECT from `out = daggerProd self other` via D-COLLAPSE on "
                     "the RECEIVER facet: the post-image is `self`, the rival "
                     "returns a constant conjugate object, disagreeing for every "
                     "`self` but one. Targets the facet that the collapse decision "
                     "and the survivor's SHAPE both leave unconstrained; refuted "
                     "only by moving the `self` binder off the hard-coded value.",
        "witness": _witness_dag(
            'daggerProductTester (QExpr.dag (QExpr.op "B")) QExpr.ident'),
    },
    {
        "id": "uniq-id-wrong-surviving-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (site 1): the collapse DECISION is correct on every shape (a
        # collapse-bit fuzzer is blind to it), but on collapse it returns `self`
        # (the identity) as the survivor instead of `other`. Violates I-COLLAPSE
        # whenever other ≠ ident.
        "module": _variant_id(
            "    if isOperatorClass other || isDaggerClass other then\n"
            "      return self\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "the collapse decision is left correct on every shape, so a "
                      "fuzzer that only flips the collapse bit is blind to it; but "
                      "on collapse it returns `self` (the identity) instead of the "
                      "surviving operand. A faithful counterpart would make "
                      "I * Dagger(O) == I and I * O == I, so the failing assertions "
                      "`I * Dagger(O) == Dagger(O)` and `I * O == O` stay false — the "
                      "instance stays unresolved.",
        "rationale": "REJECT from `out = identityProd self other`: on the collapse "
                     "branch the post-image is `other` but the rival returns `self` "
                     "(= ident), disagreeing whenever other ≠ ident. Targets the "
                     "surviving-operand facet the collapse decision does not "
                     "constrain. Refuted at other = a conjugate object.",
        "witness": _witness_id(
            'identityProductTester QExpr.ident (QExpr.dag (QExpr.op "A"))'),
    },
    {
        "id": "uniq-dag-wrong-surviving-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (site 2): the collapse decision is correct, but on collapse it
        # returns `other` (the identity) instead of `self` (the conjugate object).
        # Violates D-COLLAPSE. The witness also moves the `self` binder to a THIRD
        # distinct conjugate object.
        "module": _variant_dag(
            "    if isIdentityClass other then\n"
            "      return other\n"
            "    else\n"
            "      return QExpr.mul self other"),
        "refinement": "the collapse decision is left correct, so a collapse-bit "
                      "fuzzer is blind to it; but on collapse it returns `other` "
                      "(the identity) instead of the surviving conjugate object. A "
                      "faithful counterpart would make Dagger(O) * I == I, so the "
                      "failing assertion `Dagger(O) * I == Dagger(O)` stays false — "
                      "the instance stays unresolved.",
        "rationale": "REJECT from `out = daggerProd self other`: on the collapse "
                     "branch the post-image is `self` but the rival returns `other` "
                     "(= ident). Targets the surviving-operand facet D-COLLAPSE's "
                     "decision does not constrain. Refuted with `self` = a third "
                     "distinct conjugate object, moving that binder.",
        "witness": _witness_dag(
            'daggerProductTester (QExpr.dag (QExpr.op "C")) QExpr.ident'),
    },
    {
        "id": "uniq-id-wrong-fallthrough-left-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (site 1): the collapse decision AND the collapse-branch survivor are
        # correct on every shape, but the FALL-THROUGH ordinary product is built
        # with the wrong left operand (a conjugate object instead of the identity
        # receiver `self`). The receiver is pinned to the identity (`require self =
        # QExpr.ident`); recording a conjugate left operand mis-builds the product,
        # a facet neither the collapse decision nor the surviving operand
        # constrains. The ONLY rival attacking the fall-through left operand.
        "module": _variant_id(
            "    if isOperatorClass other || isDaggerClass other then\n"
            "      return other\n"
            "    else\n"
            "      return QExpr.mul (QExpr.dag (QExpr.op \"L\")) other"),
        "refinement": "the collapse decision and the collapse survivor are left "
                      "correct on every shape; but the ordinary product built on "
                      "the fall-through uses a conjugate object as the left factor "
                      "instead of the identity receiver. A counterpart that emitted "
                      "the product against the wrong left operand no longer computes "
                      "IdentityOperator.__mul__ at all (the left factor of I * x "
                      "must be I), so the assembled product for I * x is the wrong "
                      "object and the F2P canonical forms do not match — it does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = identityProd self other` via I-FALL: the "
                     "post-image is `mul self other` (self = ident) but the rival "
                     "builds `mul (dag L) other`, disagreeing on the left factor. "
                     "Targets the fall-through left-operand facet neither the "
                     "collapse decision nor the survivor constrains. Refuted at "
                     "other = a product node (the fall-through shape).",
        "witness": _witness_id(
            'identityProductTester QExpr.ident (QExpr.mul (QExpr.op "A") (QExpr.op "B"))'),
    },
    {
        "id": "uniq-id-never-collapse-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        # SUPPORTING near-miss (site 1): never collapse — every product is the
        # ordinary product, even against an operator/identity/conjugate right
        # operand. Subsumes the site-1 prepatch rival on the whole collapse domain;
        # kept as a cheap supporting case. Refuted at a plain operator (a collapse
        # sub-domain none of the other identity rivals probe as `other`).
        "module": _variant_id("    return QExpr.mul self other"),
        "refinement": "cheap whole-domain near-miss: never collapse. A faithful "
                      "counterpart would leave I * O, I * I, and I * Dagger(O) all "
                      "unsimplified, so the failing assertions `I * O == O` and "
                      "`I * Dagger(O) == Dagger(O)` stay false — the instance stays "
                      "unresolved. Subsumes the site-1 prepatch rival on the whole "
                      "collapse domain; kept as a cheap supporting case, not a "
                      "substitute for the reasoned sub-domain rivals.",
        "rationale": "REJECT from `out = identityProd self other` via I-COLLAPSE on "
                     "the entire collapse domain: the post-image collapses to "
                     "`other` when isOperatorClass/isDaggerClass, the rival always "
                     "returns the ordinary product. Refuted at other = a plain "
                     "operator — a collapse sub-domain no other identity rival "
                     "moves `other` to.",
        "witness": _witness_id(
            'identityProductTester QExpr.ident (QExpr.op "A")'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (1 soundness
# positive, 1 admissibility, 8 uniqueness rivals) plus an EMPTY AXIOM lane, over a
# carrier where each operand is abstracted to an integer KIND TAG (0 operator,
# 1 identity, 2 conjugate, 3 other) and the receiver is elided. This bundle models
# the SAME two product dispatches as two `method`s over a finite `QExpr` carrier
# that keeps the receiver as a real input (`self`). Kind tags map to shapes:
#   kind 0 (operator)  -> QExpr.op _        kind 2 (conjugate) -> QExpr.dag _
#   kind 1 (identity)  -> QExpr.ident       kind 3 (other)     -> QExpr.mul _ _
# (the fall-through shape: not operator/identity/conjugate).
#
#   sibling case                              -> here                              disposition
#   ----------------------------------------------------------------------------------------
#   pos-control-enumerate-both-sites          -> pos-negated-guard-both-sites      PORTED
#   (no sibling)                              -> pos-direct-model-both-sites       ADDED
#   admiss-both-discriminating-kinds          -> admiss-f2p-discriminating-...     PORTED (re-aimed)
#   uniq-site1-prepatch-kind2-not-absorbed    -> uniq-id-prepatch-dagger-not-...   PORTED
#   uniq-site2-prepatch-kind1-not-absorbed    -> uniq-dag-prepatch-identity-not-.. PORTED
#   uniq-site1-overabsorb-scalar-kind3        -> uniq-id-overabsorb-product-node   PORTED
#   uniq-site2-overabsorb-operator-kind0      -> uniq-dag-overabsorb-operator      PORTED
#   uniq-site1-wrong-surviving-operand        -> uniq-id-wrong-surviving-operand   PORTED
#   uniq-site2-wrong-surviving-operand        -> uniq-dag-wrong-surviving-operand  PORTED
#   uniq-site1-wrong-left-operand-kind        -> uniq-id-wrong-fallthrough-left-.. PORTED (re-aimed)
#   uniq-site1-never-collapse-supporting      -> uniq-id-never-collapse-supporting PORTED
#   (no sibling)                              -> uniq-dag-overabsorb-dagger-shape  ADDED (audit)
#   (no sibling)                              -> uniq-dag-collapse-ignores-receiver ADDED (audit)
#   AXIOM_TESTS ([])                          -> (none)                            DROPPED (G-AX)
#   frame-mutation (N/A there)                -> (none)                            VACUOUS
#
# ALL 10 sibling SPEC cases PORTED; one positive added; two rivals ADDED by the
# independent audit (below); the empty axiom lane dropped. Case count HIGHER than
# the sibling because this carrier gives back a binder the sibling abstracted away
# (see below), not from chasing parity.
#
# ADDED BY AUDIT (two rivals closing sub-domains the port left unattacked, both
#   confirmed with real builds — rival module rejected, witness elaborating against
#   the rival and REFUTED against the frozen solution by a computed `decide`):
#   * uniq-dag-overabsorb-dagger-shape — daggerProduct's `other` binder was moved
#     only over {ident, op _} by the ported rivals, so `other = dag _` was an
#     undistinguished D-FALL sub-domain. It is also the shape the two dispatches
#     treat OPPOSITELY (identityProd collapses on it, daggerProd does not), i.e.
#     precisely where a cross-contaminated guard hides.
#   * uniq-dag-collapse-ignores-receiver — the RECEIVER facet of D-COLLAPSE. The
#     ported battery moved `self` across three conjugates but no rival's refutation
#     DEPENDED on that movement, so the extra binder was varied without being
#     probed: every ported dagger rival is refuted at a single `self`. This rival is
#     correct at self = dag (op "A") (its witness there fails against the rival
#     itself — checked), so only moving `self` refutes it.
#
# PORTED (positive): the sibling rewrites both dispatches as an explicit per-kind
#   enumeration handling the non-collapse kind first. Here the dispatches are
#   two-way `if`s, so the reshape is the negated collapse guard on both sites,
#   emitting the ordinary product first. Both keep the whole dispatch, so the
#   frozen `loom_solve <;> simp_all [...]` closes the byte-identical obligations
#   (verified out-of-band with a real build).
# ADDED (positive): pos-direct-model-both-sites returns each pure model
#   (`daggerProd`/`identityProd`) directly — a second cheapest-reshape control,
#   sharing the frozen proofs (the ensures IS `out = <model>`, so the body is
#   definitionally the RHS). Verified out-of-band.
# PORTED-RE-AIMED (admissibility): the sibling self-calls the two discriminating
#   kinds to force the precondition to discharge. Preconditions here are trivially
#   admissible for the F2P inputs (`isDaggerClass (dag O)` and `self = ident` both
#   hold), so the residual risk is post-image DEGENERACY on a total domain. The
#   re-aimed probe asserts, via a live in-region assert at the two F2P inputs, that
#   the dispatch is non-degenerate: I * Dagger(O) collapses to Dagger(O) (and is
#   NOT an ordinary product) and Dagger(O) * I collapses to Dagger(O). Kept the
#   impl verbatim; retuned only the elided proof body to clear the assert by
#   `decide` (a false claim leaves an unsolved goal — verified during authoring).
# PORTED-RE-AIMED (rival): uniq-site1-wrong-left-operand-kind attacked I1
#   (left_kind == 1) on the sibling's collapse branch, which recorded a separate
#   left-operand tag. Here the collapse branch returns `other` alone (no receiver
#   tag), so the receiver `self` is observable only on the fall-through ordinary
#   product `mul self other`. The port attacks that product's left factor: gold
#   builds `mul ident other`, the rival `mul (dag L) other`. Same facet (the
#   receiver identity is mis-recorded), re-aimed to the branch where the receiver
#   is observable on this carrier.
#
# EXTRA BINDER (why this is not parity-chasing): the sibling abstracts the receiver
#   into a fixed kind tag (identity_mul's left is always kind 1, dagger_mul's is
#   always kind 2), so `self` is not a variable there. Here `daggerProduct.self` is
#   a genuine free binder under `require isDaggerClass self`; the reject witnesses
#   move it across three distinct conjugate objects (dag(op A), dag(op B),
#   dag(op C)). This is carrier WIDENING, the mirror of the narrowing the porting
#   map warns about, and it is why the rival count matches the sibling rather than
#   shrinking.
#
# COVERAGE. Independent post-image sub-behaviours attacked:
#   daggerProduct — D-COLLAPSE decision (uniq-dag-prepatch), D-COLLAPSE survivor
#     (uniq-dag-wrong-surviving), D-COLLAPSE receiver (uniq-dag-collapse-ignores-
#     receiver), D-FALL on the operator shape (uniq-dag-overabsorb-operator) and on
#     the conjugate shape (uniq-dag-overabsorb-dagger-shape).
#   identityProduct — I-COLLAPSE (uniq-id-prepatch, uniq-id-wrong-surviving,
#     uniq-id-never-collapse), I-FALL (uniq-id-overabsorb, uniq-id-wrong-
#     fallthrough-left). Every top-level clause of both post-images is attacked and
#     both are defended by two positive controls + the admissibility probe.
#   Binders moved by the reject witnesses (8 distinct input tuples over 10 rivals;
#   the two sharing a tuple attack DIFFERENT facets at it — the collapse decision
#   vs the surviving operand, and the fall-through decision vs its left factor):
#     daggerProduct.self ∈ {dag(op A), dag(op B), dag(op C)} — three conjugates,
#       and uniq-dag-collapse-ignores-receiver is refuted ONLY off dag(op A), so the
#       binder is probed rather than merely varied;
#     daggerProduct.other ∈ {ident, op A, dag(op B)} — the collapse arm and BOTH
#       fall-through shapes that reach this site;
#     identityProduct.self = ident (pinned by require; not a free binder);
#     identityProduct.other ∈ {dag(op A), mul(op A)(op B), op A} — the
#       conjugate-object arm, the fall-through product-node shape, and the operator
#       arm.
#
# FRAME-MUTATION: VACUOUS. The sibling records this class as N/A (the only
#   parameter is a pass-by-value kind tag; each __mul__ builds a fresh result and
#   mutates no operand). This referentially-transparent backend declares no `mut`
#   binder — every input is an immutable value with no heap footprint — so there is
#   no read-only field to overwrite and no substitute probe. Not fabricated.
# DIVERGENCE: CLOSED BY THE SEMANTICS, not vacuous. The sibling carries no
#   `diverge-*` case, so there is nothing to port, and the frozen impl is loop-free,
#   so no divergence rival is SHIPPED here. But "a diverging body cannot be
#   written" is withdrawn: a rival owns the whole impl region and may splice a
#   loop. Under `total` a postcondition is claimed of ALL runs, so every loop owes
#   a decreasing measure AND its descent. Measured with the proofs reduced to
#   `loom_solve`: a spliced `decreasing z` loop whose body is `z := z + 1` is
#   refused on `case «decreasing_1: z»`, residual `z + 1 < z`; with the measure
#   omitted the refusal moves to the `method` declaration ("Decreasing annotations
#   are required in total correctness semantics"). No `partial`-mode spec hole to
#   record either: no velvet bundle sets `partial`.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the three membership tests
#   are deep-model A-references validated there, and this bundle consumes no
#   `axiom` (meta.json axioms == []). Nothing here for this gate to probe.
AXIOM_TESTS = []
