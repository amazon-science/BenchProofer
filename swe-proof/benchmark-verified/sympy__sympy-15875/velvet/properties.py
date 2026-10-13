"""properties.py — G-PBT falsification battery for sympy__sympy-15875 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct sumIsZero`` obligation survives with a byte-identical
statement) and swaps in a candidate impl; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: it elaborates against the rival and FAILS against the frozen
solution).

DEFENDED SURFACE (one contracted method over a mostly-transparent core):

  sumIsZero (isComm : Option Bool) (args : List Term) return (out : Option Bool)
    ensures out = sumIsZeroSpec isComm args

The three-valued zero-verdict for a commutative sum. Each ``Term`` reduces one
summand to four fuzzy facts. ``sumIsZeroSpec`` unfolds to a completed tally
(``tallyAll`` — a transparent fold classifying each term as real-and-zero,
real-and-nonzero, pure-imaginary, imaginary-or-zero, or unclassifiable) fed into
``verdict``, a transparent decision cascade. The SINGLE opaque term is
``residualIsZero : List Term → Option Bool`` — the deferred zero-test of the
real-nonzero residual sub-sum, left with no asserted contract.

CARRIER NOTE (decisive for the witnesses). ``tallyAll`` and ``verdict`` are
concrete ``def``s: at a concrete ``args`` literal the tally computes and every
guard of the cascade reduces. So a rival that reshapes a TRANSPARENT clause (the
commutativity guard, the all-zero / no-real-nonzero partition, the combination
of the imaginary flags) diverges at a point the elaborator can see. But the two
deepest arms of the cascade dispatch on ``residualIsZero acc.nz``, which never
reduces. A rival mishandling one of those arms is refutable only by CONDITIONING
on the carrier: the witness quantifies nothing away — it assumes ONE equality
about ``residualIsZero`` at the concrete residual the input produces (the
sub-domain where the rival is wrong) and shows the extracted program's output
differs from ``sumIsZeroSpec`` there. Every such hypothesis is a single equality
of one opaque application, so it is jointly satisfiable (the gate's
consistency-probe confirms no ``False`` follows from it).

THE GOLD DELTA is the ``nz.length = 0`` disjunct of the no/whole-real-nonzero
guard (``verdict`` clause 4). Pre-fix, a sum with NO real-nonzero summand but a
pure-imaginary term fell through to the residual arm and (with the empty
residual reading zero) returned a definite ``some false``; the fix routes that
case to ``none``. The ``weak-drop-nz-zero`` rival reproduces exactly the pre-fix
line and is refuted on the issue-shaped witness.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (the tally formed by a direct fold with no
    loop; the length hoisted into a ``let``) must still verify, else the spec is
    SPEC-TOO-STRONG on the assembly's shape.
  * ADMISSIBILITY — RE-AIMED. The method carries no ``require`` (the
    pre-conditions region is empty), so "a normal input meets the precondition"
    is vacuous. Re-aimed at the residual total-domain risk: that the post-image
    is degenerate at the interesting point. ``admiss-delta-grounded`` discharges
    a live in-region ``assert`` pinning ``sumIsZeroSpec``'s value on the
    gold-delta sub-domain (a two-pure-imaginary sum ↦ ``none``), the impl kept
    verbatim so the method's own obligation still discharges.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, and carry the port's
    discriminating content. SEVEN rivals attack seven independent clauses of
    ``verdict``: the commutativity guard, the ``bail`` guard, the gold-delta
    partition, and ALL FOUR residual-dispatch arms (``some true``/imOrZ, ``some
    true``/pure-imaginary, ``some false``, ``none``). Each carries a
    machine-checked, consistency-checked refutation witness AND the loop-free
    control described under GOLD-SIDE FAILURE MODE. (The last two —
    ``weak-drop-bail-guard`` and ``weak-residual-false-none`` — were added by
    audit: the ported five left the `bail` clause and the residual-`some false`
    arm unprobed, and no ported rival supplied a term of undetermined zero-ness.)
  * FRAME-MUTATION — VACUOUS. The sibling class exists because a permission-
    bearing read-only input may be overwritten. Velvet is referentially
    transparent, there is no heap and no aliasing, and this bundle declares no
    ``mut`` binder on an input (``args``/``isComm`` are immutable values), so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated. (See ACCOUNTING footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. The spec is NOT stated as an equality to an
    opaque answer key: ``verdict`` grounds the result in the input tally, and
    ``residualIsZero`` is consulted only inside two guarded arms. The cheapest
    correct impl computes the tally and the verdict, which the positive controls
    cover honestly.

WITNESS MECHANICS. Each reject witness reaches the frozen method through
Velvet's extractor (``extract_program_for sumIsZero`` ⟶ ``sumIsZeroExec``); for
a loop-free direct-fold rival ``sumIsZeroExec c a`` reduces (via ``NonDetT.run``
/ ``pure``) to ``DivM.res (sumIsZero c a)``, whose body then unfolds to the
inlined decision. The witness states ``sumIsZeroExec c a ≠ DivM.res
(sumIsZeroSpec c a)`` at one concrete input, discharged by ``simp`` on the
transparent ``verdict``/``tallyAll``/``classify`` defs plus the single opaque
hypothesis. No tester/``decide`` on the residual arms (the opaque term does
not compute); no ``sorry``/``admit``/``native_decide``/``axiom``.

GOLD-SIDE FAILURE MODE — MEASURED, and NOT what the gate's second leg suggests.
The frozen impl is a ``while`` loop, so its ``sumIsZeroExec`` elaborates through
``NonDetT.run``'s ``repeatCont`` arm into ``forIn Lean.Loop.mk`` decorated with
``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``. ``Loop.forIn`` is a
``partial def`` — no equation lemmas, no kernel delta — so NOTHING reduces it:
measured here, a claim that is TRUE of the frozen solution at the same input
(``sumIsZeroExec (some false) [zero] = DivM.res (sumIsZeroSpec …)``) fails
IDENTICALLY (exit 1, goal left as the un-normalised ``forIn`` term), and adding
``Lean.Loop.forIn``/``forIn``/the three gadgets to the ``simp`` set changes
nothing. So each gold-side build here distinguishes LOOP from LOOP-FREE, not
wrong from right, and the gate's "fails on gold" leg is weaker than it reads.
Re-measured by audit with the full forgery pair on all seven cases, which
confirmed it carries no information at all — see the next paragraph, and note
that the consequence is a ``witness_reference`` on every reject case, not prose.

WHAT ACTUALLY EARNS THE DISCRIMINATION, and it is now IN BAND (audit repair).
The paragraph above used to end by appealing to an out-of-band control the gate
does not run — every witness "was ALSO built" against a correct loop-free impl —
which is exactly the kind of claim an artifact cannot support: nothing in the
recorded verdict depended on it, so a reader had only the prose. Worse, the
gate's own second leg was measured HOLLOW here. The forgery pair (attack B'):
for all seven witnesses, the witness (``≠``) and the FLIPPED claim (``=``,
asserting the FROZEN impl is CORRECT at that input) both fail against the frozen
solution with exit 1 and the same un-normalised goal, differing only in the
``¬``. The frozen side's exit code therefore carried NO information about the
claim, and a witness asserting the opposite of a refutation would have been
recorded as ``rejected``. None of the gate's stuck-reduction screens match this
shape (the failure is ``unsolved goals``, not a stuck ``decide`` / dependent
elimination / missing ``Decidable`` / application type mismatch), so the
automatic positive-fallback never fired either.

So every reject case now carries an explicit ``witness_reference``: the
loop-free ``pos-direct-fold`` source, which the gate independently checks shares
the frozen spec and VERIFIES before refuting the witness against it. Against
that subject the exit code TRACKS THE CLAIM — witness exit 1 with a SEMANTIC
goal (``hres : residualIsZero … = …  ⊢ False``: ``simp`` fully reduced program
and spec, found them EQUAL, and was left with the impossible ``False``), flipped
claim exit 0. That pair is the discrimination, it is machine-checked by the
gate, and it is recorded per case in the ``control`` field below. A tautology, or
a witness that merely exploited the loop, fails that pair.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom
soundness/containment probes over the real deferred residual zero-test callee;
that is G-AX's job (axiom_check.py / mapping.md §3) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15875"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the executable lines
# ---- strictly inside sumIsZero's -- impl-start / -- impl-end). Lies wholly
# ---- inside the single impl region and is unique in the file (the prepatch
# ---- skeleton lives in a different file); both facts asserted at load by
# ---- _swap. Every reject rival and both positives replace exactly this block.
_IMPL = (
    "    -- impl-start\n"
    "    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }\n"
    "    let mut i := args.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ args.length\n"
    "      invariant acc = tallyAll (args.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := args[i - 1]!\n"
    "      acc := classify a acc\n"
    "      i := i - 1\n"
    "    return verdict isComm args.length acc\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "sumIsZero impl region drifted from expected text"

# ---- the frozen `prove_correct` tactic body (elided from the consumer spec
# ---- view). The admissibility case adds one alternative to close its extra
# ---- in-region `assert`; every other case leaves the proof untouched.
_PROOF = (
    "prove_correct sumIsZero by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (rw [tallyAll_drop_step args i (by omega) (by omega)]; simp_all)\n"
    "    | simp_all [sumIsZeroSpec]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- Term literals for the four fuzzy-fact carriers, at their canonical
# ---- classifications (mapping.md §3.1 branch table).
_ZERO = "⟨some true, some true, some false, some true⟩"      # real & zero        (z)
_NONZERO = "⟨some true, some false, some false, some false⟩"  # real & nonzero    (nz)
_IMAG = "⟨some false, some false, some true, some true⟩"      # pure imaginary    (im)
_IMORZ = "⟨none, none, none, some true⟩"                      # imaginary-or-zero (imOrZ)
_BAILR = "⟨some true, none, some false, none⟩"                # real, zero-ness undetermined (bail)


# ---- The frozen decision cascade, spelled out as a `let`-bound value so a
# ---- rival can reshape ONE clause while the rest stays gold-faithful. This is
# ---- semantically identical to `verdict isComm args.length (tallyAll args)`:
# ---- the positive `pos-direct-fold` uses this exact body and verifies.
def _gold_decision():
    return (
        "      if isComm = some false then none\n"
        "      else if acc.bail then none\n"
        "      else if acc.z = args.length then some true\n"
        "      else if acc.nz.length = 0 ∨ acc.nz.length = args.length then none\n"
        "      else match residualIsZero acc.nz with\n"
        "        | some true =>\n"
        "            if !acc.imOrZ && !acc.im then some true\n"
        "            else if acc.im && !acc.imOrZ then some false\n"
        "            else none\n"
        "        | some false => some false\n"
        "        | none => none\n"
    )


def _direct_fold(decision_body):
    """A loop-free direct-fold impl with an inlined (possibly reshaped) cascade.

    `sumIsZeroExec` on this shape reduces so a witness / the proof can unfold it.
    With `_gold_decision()` this is behaviourally identical to the frozen impl.
    """
    return (
        "    -- impl-start\n"
        "    let acc := tallyAll args\n"
        "    let r : Option Bool :=\n" + decision_body +
        "    return r\n"
        "    -- impl-end"
    )


def _module(decision_body):
    return _swap(_BASE, _IMPL, _direct_fold(decision_body))


# ---- THE WITNESS SUBJECT (audit repair). The frozen impl CANNOT serve as the
# ---- discrimination subject on this bundle: its `while` loop elaborates into
# ---- `forIn Lean.Loop.mk` decorated with invariant/onDone/decreasing gadgets,
# ---- and `Loom.Loop.forIn` is a `partial def` with no equation lemmas, so
# ---- nothing reduces it. MEASURED with the forgery pair (attack B'): for every
# ---- one of the seven witnesses below, the witness (`≠`) and the FLIPPED claim
# ---- (`=`, i.e. asserting the frozen impl is CORRECT at that input) BOTH fail
# ---- against the frozen solution with exit 1 and the same un-normalised goal:
# ----     ⊢ ¬(NonDetT.run do let r ← forIn Lean.Loop.mk …)     [witness]
# ----     ⊢  (NonDetT.run do let r ← forIn Lean.Loop.mk …)     [forgery]
# ---- So the frozen side's exit code carries NO information about the claim, and
# ---- a witness asserting the opposite of a refutation would have been recorded
# ---- as `rejected`. (The gate's own stuck-reduction screens do not match this
# ---- shape: the failure is `unsolved goals`, not a stuck `decide`, a dependent
# ---- elimination failure, a missing `Decidable`, or an application type
# ---- mismatch — so the automatic positive-fallback never fired.)
#
# ---- The repair is an explicit `witness_reference`: a LOOP-FREE impl of the
# ---- same frozen spec, which the gate independently checks shares the spec and
# ---- VERIFIES before refuting the witness against it. An impl the verifier
# ---- accepts cannot violate its own spec, so a genuine witness must still fail
# ---- there — and here the exit code TRACKS THE CLAIM, which is the property
# ---- gold lacked. Measured against this reference, per case:
# ----     witness (`≠`)   -> exit 1, goal `hres : residualIsZero … = … ⊢ False`
# ----                        (simp reduced BOTH program and spec, found them
# ----                         EQUAL, and was left with the impossible `False`)
# ----     forgery (`=`)   -> exit 0   <-- the claim's truth changes the verdict
# ----     consistency     -> exit 1   (no `False` from the hypothesis alone)
# ---- This is `pos-direct-fold`'s own source, so it is also an expect="verify"
# ---- case of this battery and is verified twice over.
_WITNESS_REF = _swap(
    _BASE, _IMPL,
    "    -- impl-start\n"
    "    let acc := tallyAll args\n"
    "    return verdict isComm args.length acc\n"
    "    -- impl-end")


# ---- witness builder. Reaches the frozen contract through the extractor and
# ---- CONDITIONS on the carrier: it assumes ONE equality about `residualIsZero`
# ---- at the concrete residual the input produces (the sub-domain the rival
# ---- mishandles) and shows the extracted program's output differs from the
# ---- spec there. Checked in a file whose `prove_correct` block is stripped, so
# ---- no tactic script can mask the verdict; the lone hypothesis is an ordinary
# ---- equality of one opaque application (jointly satisfiable — the gate's
# ---- consistency-probe confirms no False follows). `hyp=None` for the fully
# ---- transparent clause (commutativity guard), which needs no assumption.
def _wit(isComm, args_lit, hyp=None):
    head = f"(hres : {hyp}) " if hyp else ""
    hsimp = ", hres" if hyp else ""
    return (
        "extract_program_for sumIsZero\n\n"
        f"example {head}:\n"
        f"    sumIsZeroExec {isComm} {args_lit}\n"
        f"      ≠ DivM.res (sumIsZeroSpec {isComm} {args_lit}) := by\n"
        "  unfold sumIsZeroExec sumIsZero sumIsZeroSpec\n"
        f"  simp [NonDetT.run, pure, verdict, tallyAll, classify{hsimp}]\n"
    )


# ---- reject decision bodies: each a ONE-clause reshape of `_gold_decision()`.
# (1) GOLD DELTA — drop the `nz.length = 0` disjunct (the exact pre-fix line).
_DEC_DROP_NZ0 = _gold_decision().replace(
    "      else if acc.nz.length = 0 ∨ acc.nz.length = args.length then none\n",
    "      else if acc.nz.length = args.length then none\n")

# (2) residual-none arm: return a definite `some false` instead of `none`.
_DEC_NONE_FALSE = _gold_decision().replace(
    "        | none => none\n",
    "        | none => some false\n")

# (3) residual-true / imaginary-or-zero arm: drop the imOrZ guard so an
#     imaginary-or-zero summand wrongly yields `some true`.
_DEC_DROP_IMORZ = _gold_decision().replace(
    "            if !acc.imOrZ && !acc.im then some true\n"
    "            else if acc.im && !acc.imOrZ then some false\n"
    "            else none\n",
    "            if !acc.im then some true\n"
    "            else if acc.im && !acc.imOrZ then some false\n"
    "            else none\n")

# (4) residual-true / pure-imaginary arm: drop the `some false` conclusion so a
#     provably-nonzero pure-imaginary residual under-decides to `none`.
_DEC_DROP_IMFALSE = _gold_decision().replace(
    "            if !acc.imOrZ && !acc.im then some true\n"
    "            else if acc.im && !acc.imOrZ then some false\n"
    "            else none\n",
    "            if !acc.imOrZ && !acc.im then some true\n"
    "            else none\n")

# (5) commutativity guard: drop the `isComm = some false → none` short-circuit
#     (fully transparent clause; no residual involved).
_DEC_DROP_COMM = _gold_decision().replace(
    "      if isComm = some false then none\n"
    "      else if acc.bail then none\n",
    "      if acc.bail then none\n")

# (6) the BAIL clause: drop `acc.bail → none` entirely, so a term that defied
#     classification no longer forces an undetermined verdict and the cascade
#     reads a verdict off a tally it knows is incomplete. (Added by audit: no
#     other rival varies the `bail` flag, and no other rival supplies a term
#     whose zero-ness is undetermined.)
_DEC_DROP_BAIL = _gold_decision().replace(
    "      else if acc.bail then none\n", "")

# (7) residual-`some false` arm: under-decide it to `none`. (Added by audit:
#     this is the one residual arm no existing rival attacks — the three others
#     cover residual-true/imOrZ, residual-true/pure-imaginary and residual-none.)
_DEC_RESFALSE_NONE = _gold_decision().replace(
    "        | some false => some false\n",
    "        | some false => none\n")


# ---- admissibility: an in-region assert at the TOP of the impl pinning the
# ---- gold-delta post-image; the impl (loop + tail) is kept verbatim after it
# ---- so the method's own `ensures` still discharges. The frozen proof gets one
# ---- extra `decide` alternative to close the assert's decidable goal.
_ADMISS_IMPL = _IMPL.replace(
    "    -- impl-start\n"
    "    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }\n",
    "    -- impl-start\n"
    "    assert (with_name_prefix `assert\n"
    f"      (sumIsZeroSpec (some true) [{_IMAG}, {_IMAG}] = none))\n"
    "    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }\n")
_ADMISS_PROOF = (
    "prove_correct sumIsZero by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (rw [tallyAll_drop_step args i (by omega) (by omega)]; simp_all)\n"
    "    | decide\n"
    "    | simp_all [sumIsZeroSpec]"
)
_ADMISS = _swap(_swap(_BASE, _IMPL, _ADMISS_IMPL), _PROOF, _ADMISS_PROOF)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG on the assembly's shape.
    # =====================================================================
    {
        "id": "pos-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: form the tally with a single `tallyAll args` fold and return
        # the verdict directly — no mutable accumulator, no loop. Behaviourally
        # identical to the frozen loop by definition of `tallyAll`; the frozen
        # proof script closes it unchanged.
        "module": _WITNESS_REF,
        "rationale": "computing the tally by the front-recursive `tallyAll` fold "
                     "(no loop, no mutable accumulator) and returning the same "
                     "`verdict` yields the identical three-valued result on every "
                     "input; a correct reshape of the assembly must verify, else "
                     "the postcondition is over-fit to the loop spelling => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-hoist-length",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist `args.length` into a `let n` used for both the loop
        # bound and the verdict. Same computed values; frozen proof closes it.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    let n := args.length\n"
            "    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }\n"
            "    let mut i := n\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ args.length\n"
            "      invariant acc = tallyAll (args.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let a := args[i - 1]!\n"
            "      acc := classify a acc\n"
            "      i := i - 1\n"
            "    return verdict isComm n acc\n"
            "    -- impl-end"),
        "rationale": "binding `n := args.length` once and reusing it for the loop "
                     "bound and the verdict changes no computed value (`n` is "
                     "definitionally `args.length`), so every clause still "
                     "discharges under the frozen script; must verify, else "
                     "SPEC-TOO-STRONG against a correct hoisting reshape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` exists, so "a normal input is admitted" is
    # vacuous. Re-aimed at the total-domain risk: that the post-image is
    # degenerate at the interesting point (the gold-delta sub-domain). A live
    # in-region assert pins `sumIsZeroSpec` there; the impl is kept verbatim so
    # the method's own `ensures` still discharges. Replacing the assert with a
    # false claim leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-delta-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the post-image is satisfiable AND non-degenerate on the "
                     "gold-delta sub-domain: a two-pure-imaginary sum (no "
                     "real-nonzero summand) must map to the undetermined verdict "
                     "`none` — the very case the fix routes away from a definite "
                     "answer. The in-region assert must discharge (else the "
                     "obligation is degenerate / PRECOND-TOO-STRONG); the impl is "
                     "kept verbatim so the method's own `ensures` still holds.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a carrier-conditioned, consistency-
    # checked refutation witness and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-drop-nz-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE GOLD DELTA. Drop the `nz.length = 0` disjunct: a sum with NO
        # real-nonzero summand but a pure-imaginary term falls through to the
        # residual arm instead of `none`.
        "module": _module(_DEC_DROP_NZ0),
        "refinement": "this IS the pre-fix line — the no/whole-real-nonzero guard "
                      "WITHOUT the empty-residual disjunct. On the issue-shaped "
                      "input (two pure-imaginary summands, no real-nonzero term) "
                      "the empty residual sub-sum reads zero, so it enters the "
                      "residual-true arm and, with a pure-imaginary term present, "
                      "returns a definite `some false` where the true verdict is "
                      "`none`. That is exactly the misbehaviour the failing test "
                      "constructs (a complex integer wrongly reported zero-decided), "
                      "so a faithful counterpart would NOT resolve.",
        "rationale": "REJECT from `verdict` clause 4 (the gold-delta partition): "
                     "with `nz.length = 0` and not all-zero the spec pins `none`, "
                     "but this rival dispatches on the residual and returns a "
                     "definite verdict. Verifying would be SPEC-TOO-WEAK (it would "
                     "admit the pre-fix line). Refuted at the issue-shaped input "
                     "conditioned on the empty residual reading zero.",
        # residual over [] (no real-nonzero terms). some false ⟶ rival takes the
        # residual-true(im) arm ⟶ some false; spec = none. The `some false`
        # hypothesis is one of the sub-domain values on which the pre-fix errs.
        "witness": _wit("(some true)", f"[{_IMAG}, {_IMAG}]",
                        hyp="residualIsZero ([] : List Term) = some false"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [] = some false ⊢ False`; flipped "
                   "claim (`=`) exit 0 — the exit code tracks the claim. vs the "
                   "FROZEN impl both directions fail identically (exit 1, "
                   "un-normalised `forIn Lean.Loop.mk` goal), which is why this "
                   "case carries a `witness_reference`.",
    },
    {
        "id": "weak-residual-none-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Residual-none arm: return a definite `some false` when the residual
        # sub-decision is itself undetermined.
        "module": _module(_DEC_NONE_FALSE),
        "refinement": "a counterpart that treats an UNDETERMINED residual "
                      "sub-decision as a definite nonzero result fabricates a "
                      "verdict the sub-decision cannot justify: on a sum whose "
                      "real-nonzero part has undetermined zeroness the true "
                      "verdict is `none`, and reporting a definite answer corrupts "
                      "the three-valued contract downstream consumers rely on. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `verdict`'s residual-`none` arm: the spec maps "
                     "an undetermined residual to `none`, this returns `some "
                     "false`. Verifying would be SPEC-TOO-WEAK on that arm. "
                     "Refuted at a one-real-nonzero + one-imaginary input, "
                     "conditioned on the residual reading `none`.",
        # nz = [nonzero], residual over it = none ⟶ rival returns some false;
        # spec = none. Distinct residual value (none) from the other rivals.
        "witness": _wit("(some true)", f"[{_NONZERO}, {_IMAG}]",
                        hyp=f"residualIsZero [{_NONZERO}] = none"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [nonzero] = none ⊢ False`; flipped "
                   "claim (`=`) exit 0 — the exit code tracks the claim. vs the "
                   "FROZEN impl both directions fail identically, hence the "
                   "`witness_reference`.",
    },
    {
        "id": "weak-drop-imorz-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Residual-true / imaginary-or-zero arm: drop the imOrZ guard so an
        # imaginary-or-zero summand wrongly yields `some true`.
        "module": _module(_DEC_DROP_IMORZ),
        "refinement": "a counterpart that ignores an imaginary-or-zero summand and "
                      "declares the sum zero whenever the real part vanishes "
                      "reports a definite zero for an expression that is zero only "
                      "conditionally (the imaginary-or-zero term carries no "
                      "settling information), so it claims a possibly-nonzero sum "
                      "is zero — a soundness break in the zero-decision. Faithful "
                      "but non-resolving.",
        "rationale": "REJECT from `verdict`'s residual-true / imaginary-or-zero "
                     "arm: with the residual zero, an imaginary-or-zero summand "
                     "present and no pure-imaginary term the spec pins `none`, "
                     "this returns `some true`. Verifying would be SPEC-TOO-WEAK. "
                     "Refuted at a one-real-nonzero + one-imaginary-or-zero input, "
                     "conditioned on the residual reading zero.",
        # nz = [nonzero], residual = some true; args add an imOrZ term (no im).
        # rival: !im ⟶ some true; spec: imOrZ set ⟶ none.
        "witness": _wit("(some true)", f"[{_NONZERO}, {_IMORZ}]",
                        hyp=f"residualIsZero [{_NONZERO}] = some true"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [nonzero] = some true ⊢ False`; "
                   "flipped claim (`=`) exit 0 — the exit code tracks the claim. "
                   "vs the FROZEN impl both directions fail identically, hence "
                   "the `witness_reference`.",
    },
    {
        "id": "weak-drop-im-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Residual-true / pure-imaginary arm: drop the `some false` conclusion so
        # a provably-nonzero pure-imaginary residual under-decides to `none`.
        "module": _module(_DEC_DROP_IMFALSE),
        "refinement": "a counterpart that fails to conclude nonzero when the real "
                      "part is zero and a pure-imaginary summand remains "
                      "under-decides: the sum is provably NONZERO (a nonzero "
                      "imaginary quantity) yet it reports `none`, weakening the "
                      "zero-decision from a definite negative to undetermined and "
                      "failing the tests that expect the definite conclusion. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `verdict`'s residual-true / pure-imaginary arm: "
                     "with the residual zero, a pure-imaginary term present and no "
                     "imaginary-or-zero term the spec pins `some false`, this "
                     "returns `none`. Verifying would be SPEC-TOO-WEAK. Refuted at "
                     "a real-zero + real-nonzero + pure-imaginary input, "
                     "conditioned on the residual reading zero.",
        # z=1, nz=[nonzero], im set, imOrZ clear; residual = some true.
        # rival: not(!imOrZ&&!im) and drops the false-conclusion ⟶ none;
        # spec: im && !imOrZ ⟶ some false.
        "witness": _wit("(some true)", f"[{_ZERO}, {_NONZERO}, {_IMAG}]",
                        hyp=f"residualIsZero [{_NONZERO}] = some true"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [nonzero] = some true ⊢ False`; "
                   "flipped claim (`=`) exit 0 — the exit code tracks the claim. "
                   "vs the FROZEN impl both directions fail identically, hence "
                   "the `witness_reference`.",
    },
    {
        "id": "weak-drop-comm-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Commutativity guard (fully transparent clause; no residual). Drop the
        # `isComm = some false → none` short-circuit so a definitely-noncommutative
        # all-zero sum wrongly yields `some true`.
        "module": _module(_DEC_DROP_COMM),
        "refinement": "a counterpart that skips the commutativity short-circuit "
                      "reads the zero-verdict off a sum it has not established is "
                      "commutative; for a definitely-noncommutative sum the "
                      "verdict must stay undetermined (the ordering machinery no "
                      "longer applies), so returning a definite answer is a "
                      "soundness break independent of the imaginary handling. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `verdict` clause 1: `isComm = some false` pins "
                     "`none`, this falls through to the all-zero clause and "
                     "returns `some true` on a definitely-noncommutative all-zero "
                     "sum. Fully transparent — no residual — so the witness needs "
                     "no hypothesis. Verifying would be SPEC-TOO-WEAK, and this is "
                     "the ONLY rival that varies `isComm` (to `some false`), "
                     "demonstrating the post-image's dependence on that binder.",
        # isComm = some false, args = [zero]: gold clause 1 ⟶ none;
        # rival skips it, z==n ⟶ some true.
        "witness": _wit("(some false)", f"[{_ZERO}]"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`⊢ False` (semantic — simp reduced both program and spec and "
                   "found them EQUAL); flipped claim (`=`) exit 0 — the exit code "
                   "tracks the claim. vs the FROZEN impl both directions fail "
                   "identically (exit 1, un-normalised `forIn Lean.Loop.mk` "
                   "goal), hence the `witness_reference`.",
    },
    {
        "id": "weak-drop-bail-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The `bail` clause: a term that defied classification
        # must force `none`, because the tally that follows is incomplete —
        # its zero-count and residual list omit that term entirely. Dropping
        # the clause reads a definite verdict off that incomplete tally.
        "module": _module(_DEC_DROP_BAIL),
        "refinement": "a counterpart that omits the unclassifiable-term guard "
                      "decides zero-ness from a tally that silently DROPPED a "
                      "summand: the term contributed to neither the zero count "
                      "nor the real-nonzero residual, so the residual "
                      "sub-decision is consulted about a strictly smaller sum "
                      "than the one under decision. It then reports a definite "
                      "verdict for a sum containing a summand whose own "
                      "zero-ness is undetermined — unsound in the same "
                      "direction as the issue, and on a clause the fix does not "
                      "touch, so it neither resolves nor preserves correctness.",
        "rationale": "REJECT from `verdict` clause 2 (`acc.bail → none`): with a "
                     "real summand of undetermined zero-ness present the spec "
                     "pins `none`, but this rival skips the guard and, with the "
                     "residual reading zero and no imaginary flags set, returns "
                     "`some true`. Verifying would be SPEC-TOO-WEAK on the ONLY "
                     "clause no other rival attacks, and this is the only case "
                     "that exercises the `bail` flag at all.",
        # args = [real/undetermined-zero, real-nonzero]: bail set, nz=[nonzero],
        # n=2 so the no/whole-real-nonzero guard does not fire. residual = some
        # true, im/imOrZ clear ⟶ rival returns some true; spec pins none.
        "witness": _wit("(some true)", f"[{_BAILR}, {_NONZERO}]",
                        hyp=f"residualIsZero [{_NONZERO}] = some true"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [nonzero] = some true ⊢ False`; "
                   "flipped claim (`=`) exit 0 — the exit code tracks the claim. "
                   "vs the FROZEN impl both directions fail identically, hence "
                   "the `witness_reference`.",
    },
    {
        "id": "weak-residual-false-none",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The residual-`some false` arm — the one arm of the
        # residual dispatch left unattacked. When the residual sub-decision
        # reports the real-nonzero part is definitely NONZERO, the whole sum is
        # definitely nonzero; under-deciding to `none` discards that.
        "module": _module(_DEC_RESFALSE_NONE),
        "refinement": "a counterpart that under-decides the definitely-nonzero "
                      "residual throws away the one case the sub-decision "
                      "settles outright: the real-nonzero part is known nonzero, "
                      "so the sum is too, and returning `none` weakens a "
                      "definite negative to undetermined. It is wrong in the "
                      "opposite direction from the issue (which was a definite "
                      "answer where `none` was due), so it neither resolves nor "
                      "preserves the surrounding three-valued behaviour.",
        "rationale": "REJECT from `verdict`'s residual-`some false` arm: the spec "
                     "maps a definitely-nonzero residual to `some false`, this "
                     "returns `none`. Verifying would be SPEC-TOO-WEAK on the "
                     "one residual arm the ported rivals leave unprobed (the "
                     "others cover residual-true/imOrZ, residual-true/pure-"
                     "imaginary and residual-none).",
        # nz=[nonzero], residual = some false ⟶ spec: some false; rival: none.
        # Fourth DISTINCT residual value/arm across the reject lane.
        "witness": _wit("(some true)", f"[{_NONZERO}, {_IMAG}]",
                        hyp=f"residualIsZero [{_NONZERO}] = some false"),
        "witness_reference": _WITNESS_REF,
        "control": "MEASURED (audit). vs the reference: witness exit 1, goal "
                   "`hres : residualIsZero [nonzero] = some false ⊢ False`; "
                   "flipped claim (`=`) exit 0 — the exit code tracks the claim. "
                   "vs the FROZEN impl both directions fail identically, hence "
                   "the `witness_reference`.",
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The sibling nagini battery ships 7 SPEC cases (1 soundness positive, 1
# admissibility, 1 frame-mutation rival, 4 uniqueness rivals) plus 2
# AXIOM_TESTS. It contracts ONE function `add_is_zero(classes, sub_is_zero)`
# over a permission-bearing `List[int]` carrier of class tags 0..5, with the
# recursive `b.is_zero` entering as the three-valued PARAMETER `sub_is_zero`.
# This velvet bundle models the same purely-functional core as a single method
# `sumIsZero (isComm) (args)` over `List Term`, with the recursive residual
# zero-test as the OPAQUE callee `residualIsZero acc.nz` (not a caller-supplied
# parameter). The decision surface carries across intact; the difference is the
# carrier's opacity in the two residual-dispatch arms, handled by conditioning.
#
#   nagini case                     kind          -> here
#   -----------------------------------------------------------------------
#   pos-control-tail-reshape        soundness     -> pos-direct-fold        RE-EXPRESSED
#                                                    (+ pos-hoist-length ADDED)
#   admiss-self-call                admissibility -> admiss-delta-grounded  RE-AIMED
#   frame-mutate-classes            uniqueness    -> (none)                 VACUOUS
#   partial-domain-drop-nz0         uniqueness    -> weak-drop-nz-zero      PORTED
#   partial-domain-subnone-false    uniqueness    -> weak-residual-none-false PORTED
#   partial-domain-ioz-true         uniqueness    -> weak-drop-imorz-guard  PORTED
#   partial-domain-im3-none         uniqueness    -> weak-drop-im-false     PORTED
#   (no sibling)                    uniqueness    -> weak-drop-comm-guard   ADDED
#   (no sibling)                    uniqueness    -> weak-drop-bail-guard   ADDED (audit)
#   (no sibling)                    uniqueness    -> weak-residual-false-none ADDED (audit)
#   ax-deepmodel-sound              axiom         -> (none)                 G-AX
#   ax-deepmodel-containment        axiom         -> (none)                 G-AX
#
# PORTED (4 reject): each nagini PARTIAL-DOMAIN rival re-expresses as a
#   one-clause reshape of `verdict`, same clause attacked, same refinement
#   argument:
#     - partial-domain-drop-nz0  -> weak-drop-nz-zero. The gold delta; the exact
#       pre-fix line. Refuted on the issue-shaped two-pure-imaginary input.
#     - partial-domain-subnone-false -> weak-residual-none-false. The nagini
#       parameter `sub_is_zero is None` becomes the opaque `residualIsZero … =
#       none`; a definite `some false` there violates the residual-none arm.
#     - partial-domain-ioz-true  -> weak-drop-imorz-guard. The class-4 (imaginary-
#       or-zero) clause: dropping its guard wrongly declares the sum zero.
#     - partial-domain-im3-none  -> weak-drop-im-false. The class-3 (pure-
#       imaginary) discriminating clause: dropping the `some false` conclusion
#       under-decides to `none`.
# RE-EXPRESSED / ADDED (2 soundness): the nagini tail-reshape (a flattened
#   sub_is_zero cascade) re-expresses as pos-direct-fold (the tally by a direct
#   fold, verdict inlined clause-for-clause). A second positive, pos-hoist-length,
#   is ADDED so the reshape space is exercised by two distinct correct forms.
# RE-AIMED (1 admissibility): admiss-self-call establishes the sibling's
#   half-permission precondition admits a normal input. No method here has a
#   `require`, so that probe is vacuous; re-aimed at the total-domain risk that
#   the post-image is degenerate at the gold-delta point. admiss-delta-grounded
#   discharges a live in-region assert pinning `sumIsZeroSpec` = none there.
# ADDED (3 reject): weak-drop-comm-guard attacks `verdict` clause 1
#   (`isComm = some false → none`). The nagini carrier has no commutativity
#   binder (its `classes` list already excludes noncommutative summands), but
#   this backend surfaces `isComm` as a top-level input binder; a rival dropping
#   its guard is a real SPEC-TOO-WEAK on a binder no other rival varies, so it is
#   included to vary `isComm` (every other witness holds it at `some true`).
#   ADDED BY AUDIT: weak-drop-bail-guard attacks `verdict` clause 2
#   (`acc.bail → none`) and weak-residual-false-none attacks the residual-`some
#   false` arm. Both clauses were left unprobed by the ported five, and the
#   `bail` flag was not varied by ANY case (nor was a term of undetermined
#   zero-ness ever supplied): the nagini sibling folded the same content into its
#   class-2/class-5 `has2 or has5` guard, which the port dissolved into `bail`
#   without carrying a rival across. Both are one-clause reshapes, both reject,
#   both discriminate on the loop-free control.
# VACUOUS — frame/permission-mutation (1): frame-mutate-classes rejects a WRITE
#   into the read-only `classes` input for insufficient fractional permission.
#   Velvet is referentially transparent, has no heap and no aliasing, and this
#   bundle declares no `mut` input binder — there is no read-only input to
#   overwrite and no permission system to trip. The class does not exist on this
#   carrier; no substitute is fabricated (per the porting map).
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (axiom_check.py /
#   mapping.md §3 validates that `residualIsZero` ↔ the real deferred residual
#   zero-test is a patch-invariant unchanged callee); this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Both input binders are varied: `isComm` over
#   `some true` (six rivals) and `some false` (weak-drop-comm-guard), and `args`
#   over SIX distinct multiset shapes so the tally's counts/flags differ per
#   rival — including one shape carrying a term of undetermined zero-ness, the
#   only shape that sets `bail`. Seven independent `verdict` clauses are each
#   attacked by exactly one rival: the commutativity guard (1), the `bail` guard
#   (1), the gold-delta partition (1), and all four residual arms (`some true`
#   with imOrZ, `some true` pure-imaginary, `some false`, `none`). Six
#   residual-arm/partition witnesses condition on `residualIsZero` at the
#   concrete residual their input produces (a single opaque equality each,
#   consistency-checked) and that hypothesis takes FOUR distinct values across
#   the lane (`some true`, `some false`, `none`, and `some true` on a
#   bail-shaped tally); the commutativity witness is fully transparent (no
#   hypothesis). Refuted at SIX distinct input points (pts=6): the two
#   residual-arm rivals weak-residual-none-false and weak-residual-false-none
#   share one input shape and are separated by the residual value they condition
#   on (`none` vs `some false`), which is the discriminating coordinate for an
#   opaque callee — the coverage counter sees only the `args`/`isComm` literals.
#
# AUDIT RECORD (independent re-derivation; 78 verifier builds).
#   * Attack A (statement integrity): every case's diff against the frozen file
#     is confined to lines 115-127 (the sole impl region), plus the one extra
#     `| decide` proof alternative the admissibility case needs. No `method`
#     header, no `ensures` line, no `Term`/`Tally`/`classify`/`tallyAll`/
#     `verdict`/`sumIsZeroSpec` definition is touched by ANY case.
#   * Attack B/B' (witness discrimination): the defect this audit found and
#     fixed. All seven reject cases previously rested on the FROZEN impl as the
#     discrimination subject, whose `forIn Lean.Loop.mk` term does not reduce;
#     the forgery pair proved the frozen side's exit code independent of the
#     claim (identical failure for `≠` and `=`). Repaired with a checked
#     `witness_reference`; per-case exit codes in each `control` field.
#   * Attack C (is the rival wrong, or just different?): each of the seven
#     differs from gold OBSERVABLY, demonstrated by the reference-side goal
#     `⊢ False` — `simp` reduced BOTH the rival's program and the spec at the
#     concrete input and found them UNEQUAL where gold's reduce EQUAL. None is
#     definitionally equal to gold on this carrier; none is vacuous.
#   * Attack D (SPEC-TOO-WEAK): five NEW wrong impls the battery does not carry
#     — dropping the `nz.length = args.length` disjunct; under-deciding the
#     all-zero clause to `none`; turning the both-flags-set `else none` into
#     `some true`; widening the commutativity guard to `isComm ≠ some true`;
#     widening all-zero to `acc.z ≥ args.length`. ALL FIVE rejected. Re-run
#     under a PERMISSIVE proof script (one that demonstrably closes the correct
#     inlined cascade, so a tactic mismatch cannot be doing the work) — all five
#     still rejected, as were the battery's own seven. No spec hole.
#   * Attack E (SPEC-TOO-STRONG): a `let`-bound-output reshape verifies (exit 0).
#     The inlined-cascade reshape is NOT provable under the frozen script alone,
#     but IS provable once `verdict` is added to the `simp` set — a tactic-script
#     limit, not a spec hole, and the spec accepts the reshape.
#   * Attack F' (divergence, `termination = "total"`): the class is SHIPPABLE
#     here and is a known gap, not vacuous. Measured: dropping `decreasing`
#     yields "Decreasing annotations are required in total correctness
#     semantics"; a non-decrementing / incrementing body fails its measure or
#     invariant obligation. So a diverging rival IS rejected by this carrier. It
#     is not landed as a case because the rejection is attributable to the
#     termination obligation rather than to the `ensures` clause, and a witness
#     over such a rival inherits exactly the loop-irreducibility this audit just
#     removed (measured: the transparent witness against an incrementing-loop
#     rival fails with the un-normalised `forIn` goal, i.e. `witness-unproven`).
#     Landing it needs a loop-free diverging shape, which this carrier's
#     structural recursion does not offer. Recorded as a gap, not as vacuous.
#   * Admissibility liveness: the in-region assert is load-bearing, not a
#     decoration. Pinning it to a FALSE value (`= some false`) fails with the
#     assert goal unsolved, and REMOVING the `| decide` alternative also fails —
#     so `decide` really discharges a live obligation at the gold-delta point.
AXIOM_TESTS = []
