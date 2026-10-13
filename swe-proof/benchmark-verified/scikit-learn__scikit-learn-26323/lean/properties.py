"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-26323 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_setOutput``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models an in-place mutator over a heap of ``Child`` objects with fractional
permissions, contracting five postcondition clauses (P1..P5) plus a frame
condition, and drives them through a ``while`` loop with explicit invariants.
This Lean bundle models the SINGLE purely-functional core: one total function
``implementation_setOutput`` that, given the contained collection, the fall-back
transformer and the chosen container, returns the pair
``(contained-with-container-applied, fall-back-with-container-applied)``. The
carrier is a referentially-transparent value world: an estimator slot is
``Transformer.est id output`` and the two routing markers are
``Transformer.passthrough`` / ``Transformer.drop``; ``setOutput`` records the
container on an estimator and is a no-op on a marker. The mapping of each nagini
case to its Lean counterpart (or its principled omission) is the ADVERSARIAL READ
section below, case class by case class. (An earlier revision of this docstring
pointed at an ``assessment`` module "at the foot of this file"; no such module was
ever written, so the cross-reference is removed rather than left dangling.)

DEFENDED SURFACE (one modeled behavior). The postcondition
``problem_spec_setOutput`` pins ``result`` to a single grounded computation over
the inputs and has exactly TWO independent top-level clauses:

  * (C1) ``result.1 = transformers.map (setOutput transform)`` — every contained
    slot has the container applied element-wise, order-preserving, and each
    routing marker is left unchanged (the marker no-op is INSIDE ``setOutput``);
  * (C2) ``result.2 = setOutput transform remainder`` — the fall-back slot has
    the container applied too (unchanged if it is a marker). This is THE clause
    the fix adds: pre-fix the fall-back was left unconfigured.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — the PERMISSION half is vacuous, the FRAME half
    is NOT, and is now probed. Lean is referentially transparent: an input
    carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit, so the *insufficient-permission* error
    mode has no instance here. But the nagini frame obligation (P5: the
    classification field equals its input value across the call) is NOT a
    permission fact — it is the requirement that the parts of a slot the
    behavior does not touch come back unchanged, and on this carrier an
    estimator slot has exactly such an untouched part: its identity ``id``. Only
    ``output`` is mutated by the modeled behavior; ``id`` is the frame. An
    earlier revision of this port recorded the whole frame class as
    "inexpressible — a slot's identity is its constructor, so the spec equations
    pin the whole value". That reasoning was wrong twice over: the spec equations
    pinning the whole value is precisely WHY a frame violation is detectable, and
    the frame-bearing field is ``id``, not the constructor. Two rivals now carry
    it (``frame-contained-identity-clobbered``,
    ``frame-remainder-identity-clobbered``): each applies the requested container
    CORRECTLY — so the clause the fix adds is satisfied — while resetting the
    slot's identity to a constant, and each is rejected with a machine-checked
    witness at a slot whose identity is not that constant. This is nagini case 7
    (and the P5 frame note) landed on this carrier, not omitted from it.

  * STRUCTURAL (order / multiplicity) — APPLIES, and was previously unprobed.
    Clause C1 is an equation against ``transformers.map``, so it pins the output
    collection's LENGTH and ORDER as well as its elements. Neither was attacked
    by a rival that got the elements right, so the "order-preserving" and
    "element-wise" strength claimed for C1 rested on argument alone. Two rivals
    now carry it: ``weak-contained-order-reversed`` (correct elements, reversed
    order) and ``weak-contained-duplicated`` (correct elements and order, each
    emitted twice).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs via the fully-unfolded
    ``setOutput`` helper. There is no opaque answer key an implementation could
    echo. (nagini's is_configurable-echo note.)

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery: rivals
    correct on part of the domain but diverging where a clause bites — dropping
    the fall-back configuration (the pre-patch bug), configuring a fall-back
    marker that must stay untouched, applying the WRONG container to the
    fall-back, dropping the contained-collection configuration, and configuring a
    contained marker that must stay untouched.

  * ADMISSIBILITY / PRECOND-TOO-STRONG — APPLIES, in a reshaped form, and is now
    carried by ``admiss-behavior-shaped-input``. The nagini case reads the
    ``Requires``-granted domain facts back at the call site; this carrier grants
    nothing, because the obligation is a bare ``∀`` over three total input types
    with no precondition hypothesis at all. An earlier revision of this port
    concluded from that absence that the lane was inexpressible. That inference
    does not hold: "no premise can be too strong" says nothing about whether the
    CONCLUSION is reachable, and an over-pinned postcondition is unsatisfiable at
    a normal input without any precondition being involved. The on-carrier
    analogue is therefore to discharge the spec predicate at a concrete
    behavior-shaped input by evaluation, as a ``have``, before closing the frozen
    obligation verbatim — which is what the case does, and its ground point is
    shown by build to fail against a rival that leaves the fall-back
    unconfigured, so the ``have`` is a real obligation rather than a tautology.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. The whole carrier is
``DecidableEq`` and every witness input is a ground ``Transformer`` literal, so
each witness is a plain ``decide`` after unfolding: it evaluates to ``True``
(hence ``¬`` closes) against the rival and to ``False`` (``decide`` proves the
underlying equality) against the frozen solution. Each was built and run BOTH
ways — it elaborates against its rival and FAILS on the frozen solution — so it
discriminates rather than asserting a tautology. No conditioning on an opaque
term is needed here because ``setOutput`` is transparent.

BINDER / CLAUSE / POINT SPREAD. The spec's input binders are ``transformers``,
``remainder`` and ``transform``. The nine reject witnesses move all of them
rather than fixing them at one convenient point: ``transformers`` ranges over the
empty list, a one-estimator list (at identities 0, 3 and 7), a one-marker list
and a TWO-estimator list (the only point at which order is observable);
``remainder`` ranges over an estimator (at identities 0 and 9, with distinct
current containers ``"old"`` / ``"x"``), the ``passthrough`` marker and the
``drop`` marker; ``transform`` takes ``"new"`` and ``"pandas"``. Both top-level
clauses are attacked, and each along every dimension it constrains:

  * C2 by four rivals — the container dropped, applied to a marker that must stay
    untouched, applied with the wrong VALUE, and applied correctly but with the
    fall-back's untouched identity clobbered (the frame) — at four distinct
    fall-back inputs;
  * C1 by five rivals — the container dropped, applied to a contained marker,
    applied correctly but with a contained slot's identity clobbered (the frame),
    and the two STRUCTURAL rivals that get every element right but return them
    reversed / duplicated (order and length).

The nine witnesses probe nine distinct inputs. Every one of them was built twice
by hand against the real verifier (rival exit 0, frozen-solution exit 1) and the
frozen-side failure was read, not just counted: in all nine it is ``decide``
reporting that it PROVED the negated claim false — i.e. the kernel fully
evaluated the spec at that input and found the frozen solution satisfies it. That
is a semantic refutation, so none of these rejections rests on a stuck reduction,
an unknown identifier or a tactic gap.

FORGERY CONTROL (why those nine gold-side exit codes carry information). "The
gold-side build failed" is evidence only if the failure TRACKS THE CLAIM. For all
nine witnesses the flipped claim was built too — the same file with the ``¬``
dropped, so it asserts the frozen solution IS correct at that input, and nothing
else changed — and all nine flipped builds ELABORATE against the frozen solution
(exit 0) where the un-flipped ones fail (exit 1). The exit code therefore inverts
with the claim, which is exactly what a hollow case cannot do: on a stuck-kernel
carrier both spellings fail identically and the gate would record ``rejected``
for a witness asserting gold is right. Here the pair is 1/0 on every case, so the
nine rejections rest on evaluation and not on the shape of the file.

ADMISSIBILITY lane: PRESENT (``admiss-behavior-shaped-input``). See that case's
own comment for why the nagini ``Requires`` read-back does not transliterate onto
a total, precondition-free carrier while its PURPOSE still does, and for the
build evidence that its ground point discriminates.

DIVERGENCE / NON-TERMINATION lane: a known HOLE, not a vacuous class, and the
reason is a carrier fact rather than a proof difficulty. This is vanilla Lean 4
with no ``loom.semantics.termination`` setting: a plain ``def`` is total by
construction, so the only way to write a diverging contained-slot step is a
``partial def``, which is kernel-OPAQUE rather than non-terminating-but-checked.
Such a rival was built and it IS rejected (exit 1), and a hypothesis-conditioned
witness for it elaborates against the rival (exit 0) — but that witness must
mention the ``partial`` helper by name, which the frozen solution does not
declare, so on the frozen side it fails with ``Function expected at spin`` — an
UNKNOWN NAME, not a satisfied spec. That is precisely the defect
``witness_scope_problems`` screens for, and it is what makes the case
unshippable: there is no vocabulary shared by rival and frozen solution in which
the divergence can be stated, because the frozen carrier has no diverging term to
compare against. Recorded as a hole so it stays visible.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` — ``setOutput`` is a
deep model (an A-reference validated executably by G-AX), not a consumed
contract. The axiom lane belongs to G-AX; this gate ignores it, and the nagini
``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26323"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positive that
# re-proves, the proof region) so same_spec stays byte-identical.

# The contained-collection accumulation step (the loop body).
_I_LOOP = "    outTransformers := outTransformers ++ [setOutput transform trans]\n"

# The fall-back (remainder) configuration binding.
_I_REM = "  let outRemainder := setOutput transform remainder\n"

# The mutable accumulator declaration (used to hoist the fall-back binding up).
_I_MUT = "  let mut outTransformers : List Transformer := []\n"

# The frozen proof's `intro` line (proof region), unique in the file, so the
# admissibility positive can PREPEND a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro transformers remainder transform\n"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro transformers remainder transform\n"
    "  unfold implementation_setOutput problem_spec_setOutput\n"
    "  simp only [Id.run]\n"
    "  have h := loop_helper_setOutput transform transformers []\n"
    "  simp only [Id.run] at h\n"
    "  rw [h]\n"
    "  simp only [List.nil_append]\n"
    "  exact ⟨rfl, rfl⟩\n"
)

# sanity: each anchor present exactly once in the frozen solution
for _a in (_I_LOOP, _I_REM, _I_MUT, _P_INTRO, _P_FROZEN):
    assert _BASE.count(_a) == 1, f"anchor drifted from Solution.lean: {_a!r}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical, and none introduces a helper
    # lemma, an axiom or an assumption token.
    #
    # The first two are DEFINITIONAL reshapes: the impl's value is unchanged up
    # to zeta-reduction, so the frozen proof body still closes verbatim. That
    # makes them honest but weak — a positive whose proof is the frozen
    # reduction re-run tests the obligation only lightly. `pos-remainder-guarded`
    # is included precisely to cover that: its second component is extensionally
    # but NOT definitionally the frozen term, so the frozen `exact ⟨rfl, rfl⟩`
    # fails and it must genuinely re-prove.
    #
    # Ports nagini case 1 (pos-control-localvar-reshape): the nagini positive
    # hoisted the configurability test into a local and added an explicit
    # else-branch. Here the analogous structural reshapes act on the two
    # observable sites — the fall-back binding and the contained accumulation —
    # and `pos-remainder-guarded` additionally restores the explicit
    # marker/else split the nagini positive had.
    # =====================================================================
    {
        "id": "pos-remainder-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Inline the fall-back local directly into the returned pair. Same value
        # flow, so the result is identical on every input and the frozen proof
        # closes (the local zeta-reduces; `exact ⟨rfl, rfl⟩` still applies).
        "module": _swap(
            _swap(_BASE, _I_REM, ""),
            "  return (outTransformers, outRemainder)\n",
            "  return (outTransformers, setOutput transform remainder)\n",
        ),
        "rationale": (
            "the fall-back clause (C2) is reshaped by inlining the `outRemainder` "
            "local into the returned pair; the second component is identical on "
            "every input, so both spec equations still hold. Must verify, else "
            "the fall-back clause is SPEC-TOO-STRONG. Proof: the frozen tactic "
            "body is retained (the local zeta-reduces, `exact ⟨rfl, rfl⟩` "
            "closes). Ports nagini's local-reshape positive to the fall-back "
            "site."
        ),
    },
    {
        "id": "pos-remainder-hoisted",
        "kind": "soundness",
        "expect": "verify",
        # Bind the fall-back BEFORE the contained loop instead of after it. The
        # two bindings are independent, so reordering them changes nothing; the
        # frozen proof body closes unchanged.
        "module": _swap(
            _swap(_BASE, _I_REM, ""),
            _I_MUT,
            _I_MUT + "  let outRemainder := setOutput transform remainder\n",
        ),
        "rationale": (
            "the two observable computations (the contained-collection map and "
            "the fall-back application) are reordered — the fall-back binding is "
            "hoisted above the loop — with no data dependence between them, so "
            "`result` is identical on every input and both spec equations hold. "
            "Must verify. Proof: the frozen tactic body is retained (the loop "
            "still accumulates from `[]`, the fall-back local still zeta-reduces "
            "into the second component). Defends the obligation with a second "
            "correct reshape on a different site than the inline positive."
        ),
    },
    {
        "id": "pos-remainder-guarded",
        "kind": "soundness",
        "expect": "verify",
        # Re-add the explicit per-constructor marker guard on the fall-back
        # instead of relying on `setOutput` being a no-op on a marker. This is
        # the ONE positive whose second component is not DEFINITIONALLY the
        # frozen term: it is extensionally equal but reduces only after a case
        # split, so the frozen `exact ⟨rfl, rfl⟩` does NOT close it and the case
        # must genuinely re-prove (`refine ⟨rfl, ?_⟩; cases remainder <;> rfl`).
        # That makes it the positive that actually tests the obligation rather
        # than re-running the frozen reduction.
        "module": _swap(
            _swap(
                _BASE, _I_REM,
                "  let outRemainder := match remainder with\n"
                "    | .passthrough => Transformer.passthrough\n"
                "    | .drop => Transformer.drop\n"
                "    | .est id _ => Transformer.est id transform\n",
            ),
            _P_FROZEN,
            "  intro transformers remainder transform\n"
            "  unfold implementation_setOutput problem_spec_setOutput\n"
            "  simp only [Id.run]\n"
            "  have h := loop_helper_setOutput transform transformers []\n"
            "  simp only [Id.run] at h\n"
            "  rw [h]\n"
            "  simp only [List.nil_append]\n"
            "  refine ⟨rfl, ?_⟩\n"
            "  cases remainder <;> rfl\n",
        ),
        "rationale": (
            "the fall-back's marker no-op is spelled out as an explicit "
            "per-constructor guard rather than delegated to `setOutput`. This is "
            "the positive that MACHINE-CHECKS the subsumption refinement.md "
            "asserts on the fall-back op — that the guarded and guardless forms "
            "are extensionally equal — instead of taking it on argument. It is "
            "also the strongest of the three positives: unlike the inline and "
            "hoist reshapes, its second component is NOT definitionally the "
            "frozen term (it reduces only after a case split on `remainder`), so "
            "the frozen `exact ⟨rfl, rfl⟩` fails and the obligation is genuinely "
            "re-proven — `refine ⟨rfl, ?_⟩; cases remainder <;> rfl`, no helper "
            "lemma, no axiom, no assumption token, statement byte-identical. Must "
            "verify, else the fall-back clause is SPEC-TOO-STRONG against the "
            "real routine's own guarded shape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the frozen obligation is SATISFIABLE (non-vacuous)
    # at a normal, behavior-shaped concrete input. This carrier is TOTAL and the
    # obligation carries NO precondition hypothesis, so the nagini
    # precondition-admission self-call does not transliterate as a `Requires`
    # read-back. Its analogue on a total carrier is the one thing that CAN still
    # go wrong here: the obligation being unsatisfiable at exactly the input
    # shape the behavior is exercised on. An earlier revision of this port
    # recorded the whole lane as inexpressible because "the frozen obligation has
    # no precondition, so nothing can be too strong". That reason is
    # insufficient: it argues from the absence of a hypothesis, not from the
    # satisfiability of the conclusion, and the conclusion is exactly what an
    # over-pinned spec could make unreachable. The case below discharges the spec
    # predicate by KERNEL EVALUATION at the behavior-shaped input (one contained
    # estimator plus a fall-back estimator, both currently on the default
    # container, asked for a different one — the smallest input at which the
    # fall-back clause has anything to say) as a `have`, and only then closes the
    # frozen obligation verbatim. Nothing is assumed: no new declaration, no
    # axiom, no assumption token, statement byte-identical, and the ground
    # instance is a `have` prepended to the existing tactic body.
    #
    # The point is DEMONSTRATED to be discriminating, not merely asserted: the
    # same ground claim, stated positively, was built against a rival whose
    # fall-back is returned unconfigured and it FAILS there (`decide` proves the
    # conjunction false), while it elaborates against the frozen solution. So the
    # `have` is a real obligation at that input and not a tautology the kernel
    # would close for any impl.
    # =====================================================================
    {
        "id": "admiss-behavior-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _admissible : problem_spec_setOutput "
            "[Transformer.est 1 \"default\"]\n"
            "      (Transformer.est 2 \"default\") \"pandas\"\n"
            "      (implementation_setOutput [Transformer.est 1 \"default\"]\n"
            "        (Transformer.est 2 \"default\") \"pandas\") := by\n"
            "    unfold problem_spec_setOutput implementation_setOutput\n"
            "    decide\n"
            + _P_INTRO,
        ),
        "rationale": (
            "the obligation is discharged by evaluation at a concrete "
            "behavior-shaped input — one contained estimator and a fall-back "
            "estimator, both currently on the default container, asked for a "
            "different one, which is the smallest input at which BOTH clauses "
            "say something and the fall-back clause is non-trivial — as a "
            "`have`, and the frozen obligation is then closed verbatim. Must "
            "verify: if the spec predicate were unsatisfiable at exactly a "
            "normal input the modeled behavior is exercised on, that is this "
            "carrier's analogue of PRECOND-TOO-STRONG (the obligation carries no "
            "precondition hypothesis, so the failure mode is an unreachable "
            "conclusion rather than an unmeetable premise). Nothing is assumed: "
            "no new declaration, no axiom, no assumption token, statement "
            "byte-identical. Ports nagini's admiss-f2p-shaped-input, whose "
            "`Requires` read-back has no counterpart on a total, "
            "precondition-free carrier but whose PURPOSE — show the contract "
            "admits a normal input — does."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: fall-back left unconfigured (nagini case 3) ----
    {
        "id": "weak-drop-remainder",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behavior: the contained collection is configured but the
        # fall-back slot is returned unchanged (never gets the container).
        "module": _swap(_BASE, _I_REM, "  let outRemainder := remainder\n"),
        "refinement": (
            "this IS the pre-patch behavior: the contained collection receives "
            "the chosen container but the fall-back slot is left as-is. Its "
            "faithful real patch is the unpatched routine (the fall-back "
            "configuration hunk absent) — exactly what FAILS the F2P: a fall-back "
            "estimator does not record the requested container, so the composite "
            "returns the wrong output type and the frame-equality assertion "
            "fails. It does NOT resolve; a verifying rival would be a true "
            "verify-does-not-resolve break."
        ),
        "rationale": (
            "REJECT from clause C2 (`result.2 = setOutput transform remainder`): "
            "for a fall-back estimator the spec records the new container while "
            "the rival keeps the old one. Binder spread: transformers=[], "
            "remainder=est with current container \"old\", transform=\"new\"."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [] (Transformer.est 0 "old") "new"\n'
            '    (implementation_setOutput [] (Transformer.est 0 "old") "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # ---- configure a fall-back MARKER that must stay untouched ----
    {
        "id": "weak-remainder-marker-configured",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the marker no-op for the fall-back: turn ANY fall-back slot into a
        # configured estimator, even a routing marker.
        "module": _swap(
            _BASE, _I_REM, "  let outRemainder := Transformer.est 0 transform\n"
        ),
        "refinement": (
            "drops the marker guard on the fall-back: the container is applied to "
            "a fall-back that is a routing marker (\"passthrough\"/\"drop\"). Its "
            "faithful real patch calls the per-slot configuration on the marker "
            "string, which has no such capability and raises at fit time — "
            "breaking the F2P AND the marker-remainder P2P behaviors. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause C2: a marker fall-back must be returned unchanged "
            "(`setOutput` is a no-op on it) but the rival replaces it with a "
            "configured estimator. Binder spread: transformers=[], "
            "remainder=passthrough marker, transform=\"new\" — the only reject "
            "probing a marker fall-back."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [] Transformer.passthrough "new"\n'
            '    (implementation_setOutput [] Transformer.passthrough "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # ---- apply the WRONG container to the fall-back (value perturbation) ----
    {
        "id": "weak-remainder-wrong-container",
        "kind": "uniqueness",
        "expect": "reject",
        # Configure the fall-back estimator, but to a FIXED wrong container
        # ("default") instead of the requested one.
        "module": _swap(
            _BASE, _I_REM, '  let outRemainder := setOutput "default" remainder\n'
        ),
        "refinement": (
            "configures the fall-back but records a DIFFERENT container than the "
            "one requested. Its faithful real patch passes a fixed container to "
            "the fall-back's configuration instead of the requested one, so the "
            "fall-back round-trips the wrong output type — the F2P frame-equality "
            "assertion fails. It does NOT resolve. (Value-perturbation supporting "
            "case; carries a real refinement.)"
        ),
        "rationale": (
            "REJECT from clause C2: the second component must equal `setOutput "
            "transform remainder` EXACTLY, and \"default\" != the requested "
            "\"pandas\". Binder spread: transformers=[], remainder=est with "
            "current container \"x\", transform=\"pandas\" — moves the transform "
            "binder to a distinct value from the other rivals."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [] (Transformer.est 0 "x") "pandas"\n'
            '    (implementation_setOutput [] (Transformer.est 0 "x") "pandas") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # ---- the contained-collection clause: leave contained slots unconfigured ----
    {
        "id": "weak-drop-contained",
        "kind": "uniqueness",
        "expect": "reject",
        # Do not apply the container to the contained slots: accumulate each slot
        # unchanged.
        "module": _swap(
            _BASE, _I_LOOP, "    outTransformers := outTransformers ++ [trans]\n"
        ),
        "refinement": (
            "leaves every contained estimator unconfigured (the container is "
            "applied only to the fall-back). Its faithful real patch removes the "
            "per-contained configuration loop, so the contained estimators never "
            "record the requested container and the composite returns the wrong "
            "output type — the F2P assertion fails and the existing set_output "
            "P2P behaviors break. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (`result.1 = transformers.map (setOutput "
            "transform)`): a contained estimator must have the container applied "
            "but the rival returns it unchanged. Binder spread: "
            "transformers=[est with current container \"old\"], remainder=drop "
            "marker, transform=\"new\" — the first rival to move the transformers "
            "binder to a non-empty list."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [Transformer.est 0 "old"] Transformer.drop "new"\n'
            '    (implementation_setOutput [Transformer.est 0 "old"] Transformer.drop "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # ---- reclassify a contained MARKER as an estimator ----
    {
        "id": "weak-contained-marker-configured",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the marker no-op inside the loop: replace EVERY contained slot with
        # a configured estimator, even a routing marker.
        "module": _swap(
            _BASE, _I_LOOP,
            "    outTransformers := outTransformers ++ [Transformer.est 0 transform]\n",
        ),
        "refinement": (
            "configures every contained slot as an estimator, including routing "
            "markers that must be left untouched. Its faithful real patch drops "
            "the contained loop's marker filter and calls the per-slot "
            "configuration on the marker strings, which raises at set_output "
            "time — breaking the marker-in-contained P2P behaviors and the F2P. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1: a contained routing marker must map to itself "
            "under `setOutput` but the rival replaces it with a configured "
            "estimator. Binder spread: transformers=[passthrough marker], "
            "remainder=drop marker, transform=\"new\" — the only reject probing a "
            "marker INSIDE the contained collection."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [Transformer.passthrough] Transformer.drop "new"\n'
            '    (implementation_setOutput [Transformer.passthrough] Transformer.drop "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # FRAME rivals — the part of a slot the modeled behavior does NOT touch
    # must come back unchanged. Only `output` is mutated; a slot's identity
    # `id` is the frame. These two rivals apply the requested container
    # CORRECTLY (so the clause the fix adds is satisfied and the "did it
    # propagate?" question is answered yes) and are wrong ONLY in resetting the
    # identity — the on-carrier instance of the nagini frame obligation that an
    # earlier revision of this port recorded as inexpressible.
    # =====================================================================
    {
        "id": "frame-contained-identity-clobbered",
        "kind": "uniqueness",
        "expect": "reject",
        # Container applied correctly, but every contained estimator's identity
        # is reset to 0. Markers still pass through untouched.
        "module": _swap(
            _BASE, _I_LOOP,
            "    outTransformers := outTransformers ++ "
            "[match trans with | .est _ _ => Transformer.est 0 transform | other => other]\n",
        ),
        "refinement": (
            "propagates the container to every contained estimator correctly, but "
            "substitutes a different object for the one held in the collection: "
            "the returned slot is a fresh estimator rather than the caller's, so "
            "the identity the collection is keyed by is lost. Its faithful real "
            "patch would REPLACE each contained transformer with a newly "
            "constructed one instead of configuring the one in place; the "
            "composite would then hold objects that are not the fitted "
            "transformers it was built from, so its own bookkeeping no longer "
            "refers to them, the fitted state is discarded, and both the F2P and "
            "the existing propagation behaviors break. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (`result.1 = transformers.map (setOutput "
            "transform)`) on the FRAME dimension rather than the value: `setOutput` "
            "changes only the container and leaves the identity alone, so the "
            "element at index 0 must be `est 7 \"new\"`, not `est 0 \"new\"`. "
            "Binder spread: transformers=[est with identity 7], remainder=drop "
            "marker, transform=\"new\" — the only reject probing a non-zero "
            "contained identity."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [Transformer.est 7 "old"] Transformer.drop "new"\n'
            '    (implementation_setOutput [Transformer.est 7 "old"] Transformer.drop "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },
    {
        "id": "frame-remainder-identity-clobbered",
        "kind": "uniqueness",
        "expect": "reject",
        # Same frame violation on the fall-back: right container, wrong identity.
        "module": _swap(
            _BASE, _I_REM,
            "  let outRemainder := match remainder with\n"
            "    | .est _ _ => Transformer.est 0 transform\n"
            "    | other => other\n",
        ),
        "refinement": (
            "configures the fall-back with the requested container — so it does "
            "perform the propagation the fix is about — but returns a different "
            "object than the one it was given, discarding the fall-back's "
            "identity. Its faithful real patch replaces the fall-back with a "
            "freshly constructed transformer instead of configuring the existing "
            "one, so the fall-back the composite goes on to use is not the one it "
            "was configured with (and carries none of its fitted state); the F2P "
            "assertion fails. It does NOT resolve. This rival is the reason the "
            "fall-back clause must be an EQUATION against `setOutput transform "
            "remainder` and not merely \"the fall-back's container equals "
            "transform\": the weaker reading would admit it."
        ),
        "rationale": (
            "REJECT from clause C2 (`result.2 = setOutput transform remainder`) on "
            "the FRAME dimension: the container is right but the identity is not "
            "preserved, and `setOutput` preserves it. Binder spread: "
            "transformers=[], remainder=est with identity 9, transform=\"new\" — "
            "the only reject probing a non-zero fall-back identity."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [] (Transformer.est 9 "old") "new"\n'
            '    (implementation_setOutput [] (Transformer.est 9 "old") "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # STRUCTURAL rivals — C1 is an equation against `transformers.map`, so it
    # pins the output collection's ORDER and LENGTH too. Both rivals get every
    # ELEMENT right and are wrong only in the collection's shape.
    # =====================================================================
    {
        "id": "weak-contained-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Accumulate by prepending and never reverse: correct elements, reversed.
        "module": _swap(
            _BASE, _I_LOOP,
            "    outTransformers := [setOutput transform trans] ++ outTransformers\n",
        ),
        "refinement": (
            "applies the container to every contained slot correctly but returns "
            "the collection in the opposite order. Its faithful real patch "
            "iterates the contained transformers and rebuilds the composite's "
            "collection back-to-front, so each configured transformer is paired "
            "with a different column selection than the one it was fitted for; "
            "the composite then routes columns to the wrong sub-transformers and "
            "its assembled output does not match the expected frame — the F2P "
            "assertion fails and the column-routing behaviors break. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause C1 on the ORDER dimension: `List.map` is "
            "order-preserving, so the result must be positionally aligned with "
            "the input. Binder spread: transformers=[est 0 \"a\", est 1 \"b\"] — "
            "the only reject with a TWO-element collection, which is the shortest "
            "input at which order is observable at all; remainder=drop marker, "
            "transform=\"new\"."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [Transformer.est 0 "a", Transformer.est 1 "b"] Transformer.drop "new"\n'
            '    (implementation_setOutput [Transformer.est 0 "a", Transformer.est 1 "b"] Transformer.drop "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-contained-duplicated",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit each configured slot twice: correct elements, correct order,
        # wrong length.
        "module": _swap(
            _BASE, _I_LOOP,
            "    outTransformers := outTransformers ++ "
            "[setOutput transform trans, setOutput transform trans]\n",
        ),
        "refinement": (
            "applies the container correctly and in the right order, but emits "
            "every contained slot twice, doubling the collection. Its faithful "
            "real patch appends a second copy of each contained transformer to "
            "the composite's collection, so the composite holds twice the "
            "transformers it was constructed with and its assembled output has "
            "duplicated columns — the expected-frame comparison in the F2P fails, "
            "as do the existing shape/feature-name behaviors. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 on the LENGTH dimension: `transformers.map` "
            "preserves length, so no slot may be emitted more than once. Binder "
            "spread: transformers=[est with identity 3], remainder=passthrough "
            "marker, transform=\"new\" — a fall-back/identity point no other "
            "reject uses, so this witness is at a fresh input."
        ),
        "witness": (
            'example : ¬ problem_spec_setOutput [Transformer.est 3 "old"] Transformer.passthrough "new"\n'
            '    (implementation_setOutput [Transformer.est 3 "old"] Transformer.passthrough "new") := by\n'
            "  unfold problem_spec_setOutput implementation_setOutput\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (the `setOutput` deep model
# is an A-reference validated by G-AX, not a consumed contract). The nagini
# AXIOM_TESTS run the real callees in Docker and belong to the axiom lane; this
# gate ignores them and they are dropped.
AXIOM_TESTS = []
