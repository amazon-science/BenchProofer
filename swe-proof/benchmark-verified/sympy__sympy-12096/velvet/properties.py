"""properties.py — G-PBT falsification battery for sympy__sympy-12096 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct evaluateArgs`` obligation survives with a byte-identical
``method`` header) and swaps in a candidate implementation; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against an impl KNOWN to satisfy the spec — here the declared
``witness_reference``, since the frozen solution cannot decide anything on this
bundle; see THE WITNESS ON THIS CARRIER below).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  evaluateArgs (prec : Nat) (args : List Term)  return (out : List Term)
    ensures out = numEvalSeq prec args
    ensures out.length = args.length

TWO INPUT binders. ``prec : Nat`` is the read-only target working precision;
``args : List Term`` is the read-only argument sequence, whose elements are
OPAQUE handles (the ``Term`` axiom carries no equational content — only that the
SAME per-argument evaluator ``numEval`` is applied to each). The outcome is
pinned as a total function of the two binders by ``numEvalSeq`` (the
front-recursive map of ``numEval _ prec`` over the list), with TWO independent
top-level clauses:

  (C-value)  out = numEvalSeq prec args   — each element is the precision-``prec``
             numeric evaluation of the corresponding argument, in the SAME order.
  (C-length) out.length = args.length     — one evaluated element per input
             argument; the result neither drops nor invents positions.

C-value is the discriminating behaviour the public issue reports: each argument
must itself be numerically evaluated (not carried through verbatim) before the
function's numerical implementation is invoked. A wrong rival must violate one
of the two clauses.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
models the same change over a NUMERIC carrier: a depth-``n`` chain of unary
implemented-function applications over an integer leaf abstracted to
``eval_implemented(leaf, layers) -> Optional[int]``, with a fully-grounded
``@Pure`` fold ``eval_seq`` (``imp(x)=x*x``) as its oracle, a ``leaf>=0`` /
``eval_seq<1e14`` precondition, and ``layers`` held at a fractional
``Acc(list_pred, 1/2)``. This bundle models the change one level UP — the
argument-sequence pre-evaluation ``[i.evalf(prec) for i in self.args]`` — as a
list-to-list map over an OPAQUE per-argument evaluator. The two carriers are not
the same partition; the nagini rivals re-site onto the two clauses of this spec.

  * FRAME-MUTATION (nagini ``frame-mutate-append`` / ``frame-mutate-index``) —
    VACUOUS here. Those rivals exist because ``layers`` carries a fractional heap
    permission a write can consume, so a value-no-op mutation the value
    abstraction cannot see is still rejected by the permission system. This
    backend is referentially transparent and the method declares NO ``mut`` input
    binder — ``prec`` and ``args`` are immutable values with no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe. Not fabricated (per the porting map's frame/permission row); accounted
    for in the block below.

  * PARTIAL-DOMAIN / VALUE-PIN (nagini ``partial-none-on-composition``,
    ``partial-offbyone-on-composition``, ``partial-wrong-bare-leaf``) — APPLY,
    re-sited onto C-value and C-length. The nagini rivals split the numeric
    domain by nesting depth (0/1 layers vs >=2, and the bare-leaf base case).
    This carrier has no ``Optional``/``None`` channel and no numeric depth: the
    "left unevaluated" abstraction (``None`` for >=2 layers — the pre-patch bug)
    becomes "the argument is carried through un-evaluated" (``args`` verbatim —
    the pre-patch skeleton in ``Solution_prepatch.lean``), which is
    ``uniq-identity`` below. The off-by-one / base-case value rivals become the
    length rivals ``uniq-drop-last`` (a position dropped) and ``uniq-concat-raw``
    (a position invented), which attack C-length while also carrying a raw
    (un-evaluated) element so they violate C-value too.

  * DIVERGENCE — this bundle is ``total`` (``set_option
    loom.semantics.termination "total"``, line 4 of the frozen file), so the
    verifier DISCHARGES a termination obligation and a diverging rival is
    genuinely REJECTED. This class is therefore NOT a spec hole here — the
    earlier revision of this manifest asserted ``partial`` and recorded a known
    hole, which was simply false about this bundle's own semantics option.
    Re-measured with real builds rather than argued: the frozen body prefixed
    with an unbounded ``while spin ≥ 0 ... do spin := spin + 1`` (no
    ``decreasing`` clause), everything else verbatim, is REJECTED (exit 1) with

        error: Decreasing annotations are required in total correctness semantics
        error: Failed to prove assertion without names: WPGen

    It is nevertheless NOT shippable as an ``expect="reject"`` case, and the
    reason is mechanical rather than a matter of effort: a reject case on this
    backend needs a witness that ELABORATES against the rival, and the rival's
    own file is what fails to elaborate — the missing decreasing annotation is a
    hard ``loom.linter.errors`` diagnostic, so EVERY file containing that impl
    fails no matter what is appended. Measured: the witness file built against
    the diverging rival exits 1 on the rival half (the same decreasing-annotation
    error plus an unsolved goal over an unreduced ``forIn Lean.Loop.mk`` term),
    which the gate reads as ``witness-unproven`` — an INCONCLUSIVE outcome that
    FAILS the battery rather than passing it. So the class is closed by the
    frozen semantics option and unshippable as a case: no hole, no vacuity, a
    tooling limit on the reject lane. Sibling measurement of the same shape:
    scikit-learn__scikit-learn-10908/velvet.

  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense (mirrors the nagini
    reasoning). ``numEvalSeq`` is a total ``def`` in the ``pure`` region written
    directly as the front-recursive map of the per-argument evaluator; it is
    FULLY GROUNDED in the inputs, not an opaque answer-key the impl could echo
    without doing the work. Because it is grounded, ``return numEvalSeq prec
    args`` is the CORRECT cheapest impl (``pos-cheapest-map`` below), exactly as
    the nagini ``pos-cheapest-fold`` positive control. The ``axioms`` region
    declares ``numEval``/``Term``/``termDefault`` as A-consumed/reference callees
    with no equational ``ensures`` to attack.

  * ADMISSIBILITY (nagini ``admiss-self-call``) — PORTED, as
    ``admiss-postimage-nondegenerate``. The sibling discharges a domain
    precondition (``leaf>=0`` and ``eval_seq<1e14``) plus two
    ``Acc(list_pred,1/2)`` halves at a representative in-domain call site, and an
    earlier revision of this manifest concluded from "no ``require`` clause, no
    fractional permissions" that the whole lane was vacuous here. That is the
    WRONG analogue on a total carrier and the omission was a real gap: what
    PRECOND-TOO-STRONG becomes when the admitted domain is total is the
    OBLIGATION being unsatisfiable — or satisfiable only degenerately — at
    exactly an F2P-shaped input. A positive that discharges BOTH ``ensures``
    clauses at that concrete input, by evaluation, as a ``have`` that is then
    ``clear``ed before the frozen obligation closes verbatim, tests that
    directly. Landed and measured non-vacuous by three negative controls (see
    the case).

WHY ORDER / PRECISION RIVALS ARE NOT SHIPPED (deliberate, not an omission). The
spec pins C-value strongly — element-wise AND in order AND at ``prec`` — so a
rival that evaluates every argument correctly but REVERSES the result, or
evaluates at a fixed WRONG precision, is refutable against the spec (its witness
discriminates; verified during authoring). But its faithful real patch would
RESOLVE the failing test: the F2P discriminator ``test_issue_12092`` is
``f(f(2)).evalf() == Float(16)`` — a SINGLE argument (``self.args`` is a
one-tuple), so reordering the evaluated argument list is the identity, and the
values are exact integers, so any working precision computes the same
``Float(16)``. A verifying reversal/precision rival would therefore be a spec
artifact (the spec is stronger than the test), NOT a verify-does-not-resolve
break. Directive: a reject case ships only when a VERIFYING rival would be a true
break, i.e. its faithful patch would NOT resolve. Order/precision fail that test
on this single-argument, exact-value F2P, so they are excluded, and every shipped
rival is one whose faithful patch leaves F2P red (see each ``refinement``).

THE WITNESS ON THIS CARRIER. Each element of the result flows through the opaque
``numEval``, so a ``decide`` on a literal cannot compute it (``Term`` has no
constructors). Every witness reaches the extracted program through Velvet's
extractor (``extract_program_for evaluateArgs`` gives ``evaluateArgsExec = fun
prec args => NonDetT.run (evaluateArgs prec args)``), wrapped in a
``noncomputable section`` because the method is ``noncomputable`` (it calls the
``numEval`` axiom). Two shapes:

  * When the rival differs from the spec in a per-element VALUE (a raw,
    un-evaluated element where the spec demands ``numEval a prec``), the witness
    HYPOTHESISES that the evaluator changes that argument (``numEval a p ≠ a`` —
    the load-bearing "evalf genuinely changes a composite argument" fact G-AX
    validates against the real callee; it holds e.g. of ``f(2)`` inside
    ``f(f(2))``, whose ``evalf`` is ``4.0 ≠ f(2)``). ONE hypothesis about a single
    opaque ``numEval`` application — never two about the same term, which would be
    a contradictory forgery the gate's ``consistency_probe`` rejects; each is left
    consistent (verified: the derive-``False``-from-binders probe cannot close).
  * When the rival differs in LENGTH (a position dropped or invented), the result
    list and the spec list differ by a constructor/``nil`` clash the kernel
    decides directly, so that witness binds NOTHING at all.

A straight-line rival impl reduces cleanly under ``NonDetT.run`` (``return e``
becomes ``pure e``), so each witness ELABORATES against its (straight-line)
rival. The SECOND half — the witness must FAIL against an impl that satisfies
the spec — cannot use the FROZEN solution as its subject on this bundle, and
this was measured, not assumed. The frozen impl's ``mut``/``while`` body
desugars to ``forIn Lean.Loop.mk ...`` under ``loom.semantics.choice
"demonic"``; that term does not reduce in the kernel, so the goal against the
frozen solution is left with the whole unreduced ``forIn`` block for EVERY
claim, true or false. Measured with real builds: each of the three witnesses
fails against the frozen solution (exit 1), and so does the exact OPPOSITE
claim at the same input — ``evaluateArgsExec p as = DivM.res (numEvalSeq p
as)``, i.e. that the frozen impl is CORRECT there, which is TRUE — with the
byte-identical ``unsolved goals`` residue carrying the unreduced ``forIn``. A
trivial ``1 + 1 = 2`` claim in the same file builds (exit 0), so the cell is
not simply broken; it is this claim's reduction that is unavailable. A
frozen-side exit code therefore carries NO information here, and reading it as
a refutation would attest to a discrimination that was never performed.

So every reject case names a ``witness_reference``: ``_REF_LOOPFREE``, the
loop-free ``return numEvalSeq prec args`` impl of the same frozen spec (the
``pos-cheapest-map`` positive, which the battery independently requires to
VERIFY and which the gate re-checks for same_spec + verification before using
it). That is sound for the reason gold was: an impl the verifier ACCEPTS
cannot violate its own spec, so a genuine "the spec is violated at this input"
must fail against it too. And unlike the frozen impl it REDUCES, so its exit
codes discriminate — measured: the TRUE claim above builds against the
reference (exit 0), while each witness fails against it with a genuine
SEMANTIC residue (``⊢ False`` for the two length rivals; ``hc : True``, i.e.
the hypothesis is unusable because the values agree, for the value rivals).
Witnesses are stated positionally (``evaluateArgsExec <prec> <args>``) so the
coverage tool reads which input point each probes. No
``sorry``/``admit``/``native_decide``/``axiom``.

WITNESS PLACEMENT / BINDER COVERAGE. Four reject witnesses probe four distinct
input points and move BOTH input binders: ``prec`` at {0, 7, 15, 53} (never
pinned); ``args`` at {[a] (singleton), [a,b] (pair)}. Both top-level clauses are
attacked: C-value by ``uniq-identity`` (a raw element) and by
``uniq-subst-default`` (an evaluated element replaced by a DIFFERENT opaque
term, on a length-restricted sub-domain), and secondarily by the length rivals,
which also carry raw elements; C-length by ``uniq-drop-last`` (short) and
``uniq-concat-raw`` (long). Three positive controls defend the whole obligation
from three different proof arguments (gold's own invariant, reflexivity on the
grounded oracle, and a fresh induction), and the admissibility positive pins
BOTH clauses as jointly satisfiable and non-degenerate at the F2P-shaped
one-argument input at 53-bit precision.

AXIOM lane: dropped. The axiom lane is G-AX's job; this gate ignores
``AXIOM_TESTS``. ``numEval``/``numEvalSeq`` are validated == the real
``Expr.evalf`` comprehension by axiom_check.py (mapping.md §3), not here.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12096"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole gold backward-fold body, wholly inside the
# ---- one `-- impl-start` / `-- impl-end` region and unique in the file (both
# ---- facts asserted at load by _swap). Every variant reshapes exactly this
# ---- block; the frozen `method` header (the obligation) and the spec are
# ---- untouched, so same_spec holds and `prove_correct evaluateArgs` survives.
_GOLD_IMPL = (
    "    let mut result : List Term := []\n"
    "    let mut i := args.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ args.length\n"
    "      invariant result = numEvalSeq prec (args.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := args[i - 1]!\n"
    "      result := numEval a prec :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# ---- the frozen proof body (the backward-fold tactic script). The cheapest-map
# ---- positive reshapes the impl into a loop-free form the frozen tactic script
# ---- no longer fits (its `rw [numEvalSeq_drop_step ...]` addresses a loop goal
# ---- that no longer exists), so that ONE positive also swaps the proof body for
# ---- a bare `loom_solve` — a legal edit (the `prove_correct evaluateArgs`
# ---- header and the `ensures` statements are byte-identical; only the tactic
# ---- body, which the spec view elides, changes). The loop-rename positive keeps
# ---- the frozen tactic script verbatim.
_GOLD_PROOF = (
    "prove_correct evaluateArgs by\n"
    "  loom_solve\n"
    "  rw [numEvalSeq_drop_step prec args i (by omega) (by omega)]\n"
    "  simp_all"
)


def _with_impl(new_body):
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _with_impl_and_proof(new_body, new_proof):
    return _swap(_with_impl(new_body), _GOLD_PROOF, new_proof)


# ---- witness preamble. The result flows through the opaque `numEval`, so a
# ---- witness reaches the impl through Velvet's extractor. The method is
# ---- `noncomputable` (it calls the `numEval` axiom), so the extractor must run
# ---- inside a `noncomputable section`. Checked in a file whose `prove_correct`
# ---- block is stripped, so no tactic script can interfere.
_EXTRACT = (
    "noncomputable section\n"
    "extract_program_for evaluateArgs\n"
    "end\n\n"
)


# ---- the witness_reference subject for every reject case. The frozen impl's
# ---- `mut`/`while` body desugars to `forIn Lean.Loop.mk ...`, which the kernel
# ---- cannot reduce under loom.semantics.choice "demonic", so a witness build
# ---- against the frozen solution fails for EVERY claim regardless of truth
# ---- (measured: the witness AND the opposite, true, claim both leave the whole
# ---- unreduced `forIn` block as `unsolved goals`, while `1 + 1 = 2` builds).
# ---- Its exit code therefore discriminates nothing. This loop-free impl of the
# ---- SAME frozen spec does reduce, and it is the `pos-cheapest-map` positive —
# ---- an impl this battery independently asserts VERIFIES, which the gate
# ---- re-checks (same_spec + verifies) before refuting a witness against it. An
# ---- impl the verifier accepts cannot violate its own spec, so a genuine
# ---- witness must still fail here — and each does, with a SEMANTIC residue.
_REF_LOOPFREE = _with_impl_and_proof(
    "    return numEvalSeq prec args",
    "prove_correct evaluateArgs by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the two `ensures` clauses and the
    # `prove_correct evaluateArgs` header; only the impl (and, for the loop-free
    # one, the elided tactic body) changes.
    # =====================================================================
    {
        "id": "pos-cheapest-map",
        "kind": "soundness",
        "expect": "verify",
        # The postcondition oracle `numEvalSeq` is FULLY GROUNDED in the inputs
        # (a total front-recursive map in the `pure` region), so the cheapest
        # CORRECT impl returns it directly. Structurally different from the gold
        # backward loop (no loop, no invariants) yet behaviourally identical at
        # every argument count. The frozen loop tactic no longer fits a loop-free
        # goal, so the elided proof body becomes a bare `loom_solve`.
        "module": _REF_LOOPFREE,
        "rationale": "C-value (out = numEvalSeq prec args) and C-length "
                     "(out.length = args.length, immediate from numEvalSeq_length) "
                     "are both discharged directly when the impl returns the "
                     "grounded map; a correct impl with a structurally different "
                     "(loop-free) shape must verify, else the postcondition rejects "
                     "a correct output (SPEC-TOO-STRONG). The grounded oracle also "
                     "stands in for the ungrounded-echo probe: echoing numEvalSeq "
                     "is CORRECT, not a wrong echo.",
    },
    {
        "id": "pos-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        # Same backward fold with the accumulator renamed (result -> acc) and
        # args.length hoisted into a local `n` used only for the initial `i`. The
        # two invariant lines and the loop body are byte-identical to gold up to
        # the rename, so the frozen tactic script (numEvalSeq_drop_step) still
        # closes with NO proof-body change.
        "module": _with_impl(
            "    let n := args.length\n"
            "    let mut acc : List Term := []\n"
            "    let mut i := n\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ args.length\n"
            "      invariant acc = numEvalSeq prec (args.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let a := args[i - 1]!\n"
            "      acc := numEval a prec :: acc\n"
            "      i := i - 1\n"
            "    return acc"),
        "rationale": "behaviourally identical backward fold with the accumulator "
                     "renamed and args.length hoisted into a local; the invariants "
                     "and loop body are kept up to the rename, so the loop-invariant "
                     "proof (the frozen numEvalSeq_drop_step tactic) is unchanged. A "
                     "reshape that keeps the gold proof must verify (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-elementwise-map",
        "kind": "soundness",
        "expect": "verify",
        # A THIRD shape, and the one furthest from both of the above: the
        # per-element rule applied by `List.map` rather than by a loop or by the
        # oracle's own name. Behaviourally identical at every argument count, but
        # neither the frozen loop tactic nor a bare `loom_solve` closes it — the
        # goal `args.map (fun a => numEval a prec) = numEvalSeq prec args` needs
        # its own induction, supplied in the elided tactic body. Added by audit:
        # the two shipped positives were the gold loop RENAMED and the oracle
        # ECHOED, so neither exercised an impl whose correctness ARGUMENT differs
        # from gold's, and "a correct reshape verifies" had only been tested where
        # the proof was already in hand.
        "module": _with_impl_and_proof(
            "    return args.map (fun a => numEval a prec)",
            "prove_correct evaluateArgs by\n"
            "  loom_solve\n"
            "  induction args with\n"
            "  | nil => rfl\n"
            "  | cons a rest ih => simp [numEvalSeq, ih]"),
        "rationale": "C-value and C-length both hold of the element-wise map, and "
                     "the spec must ADMIT it: mapping the per-argument evaluator "
                     "is the same per-element rule as numEvalSeq reached by a "
                     "different recursion, so a spec that rejected it would reject "
                     "a faithful correct impl (SPEC-TOO-STRONG). Distinct from "
                     "pos-cheapest-map (which names the oracle, so the clause "
                     "closes by reflexivity) and from pos-loop-rename (which "
                     "reuses gold's own invariant proof): here the obligation is "
                     "discharged by an induction gold's script does not contain, "
                     "so it establishes the spec is provable from more than one "
                     "argument rather than only from gold's.",
    },
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # PRECOND-TOO-STRONG probe, re-aimed at what that direction becomes on a
        # TOTAL carrier. The method has no `require`, so there is no precondition
        # an input can be shown to be inside — and an earlier revision read the
        # whole lane as vacuous for that reason. The right analogue is that the
        # OBLIGATION must be satisfiable, and non-degenerately, at exactly an
        # F2P-shaped input: the failing scenario evaluates a nested application
        # whose argument sequence is a ONE-element list, at a working precision of
        # 53 bits. So the `have` exhibits, at that shape, a value that satisfies
        # BOTH `ensures` clauses jointly and pins it to the non-degenerate
        # post-image (the singleton whose element is the argument's evaluation,
        # not an empty or collapsed list); then the pair shape, which pins ORDER;
        # then the empty boundary. All three by evaluation over an arbitrary
        # opaque `a`/`b`, so nothing is assumed about a particular term.
        #
        # The impl region is the frozen body VERBATIM and the `have` is `clear`ed
        # before the frozen tactic tail runs, so the frozen obligation still
        # discharges entirely on its own terms — the case cannot pass by having
        # been helped.
        #
        # NON-VACUITY, measured with three negative controls rather than argued.
        # Each perturbs exactly one conjunct of the `have` and each FAILS:
        #   * singleton length claimed 2  -> exit 1, `unsolved goals ... ⊢ False`
        #   * singleton value pinned to the raw argument (`o = [a]`)
        #                                 -> exit 1, `Application type mismatch:
        #                                    rfl ... numEvalSeq 53 [a] = [a]`
        #   * pair value pinned in reversed order
        #                                 -> exit 1, `Application type mismatch:
        #                                    rfl ... = [numEval b 53, numEval a 53]`
        # So each conjunct is genuinely computed: if the post-image at the
        # F2P-shaped singleton were unsatisfiable, or satisfiable only by
        # dropping the argument's evaluation, or order-blind, this case would
        # fail. Shipped script exit 0.
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "prove_correct evaluateArgs by\n"
            "  have hAdm : ∀ a b : Term,\n"
            "      (∃ o : List Term, o = numEvalSeq 53 [a]\n"
            "         ∧ o.length = ([a] : List Term).length ∧ o = [numEval a 53])\n"
            "      ∧ (∃ o : List Term, o = numEvalSeq 53 [a, b]\n"
            "         ∧ o.length = ([a, b] : List Term).length\n"
            "         ∧ o = [numEval a 53, numEval b 53])\n"
            "      ∧ (∃ o : List Term, o = numEvalSeq 0 ([] : List Term)\n"
            "         ∧ o.length = ([] : List Term).length) := by\n"
            "    intro a b\n"
            "    exact ⟨⟨numEvalSeq 53 [a], rfl, by simp [numEvalSeq], rfl⟩,\n"
            "           ⟨numEvalSeq 53 [a, b], rfl, by simp [numEvalSeq], rfl⟩,\n"
            "           ⟨numEvalSeq 0 ([] : List Term), rfl, rfl⟩⟩\n"
            "  clear hAdm\n" + _GOLD_PROOF.split("\n", 1)[1]),
        "rationale": "PRECOND-TOO-STRONG in the form a total domain admits: the "
                     "conjunction of C-value and C-length must be JOINTLY "
                     "SATISFIABLE, and non-degenerate, at an F2P-shaped input — a "
                     "one-element argument sequence at a 53-bit working precision. "
                     "The `have` exhibits a witness value there and pins it to the "
                     "singleton carrying the argument's evaluation (not an empty or "
                     "constant list), then does the same at the pair shape (which "
                     "additionally pins ORDER) and at the empty boundary, all by "
                     "evaluation over arbitrary opaque arguments. The impl is "
                     "byte-identical to gold and the `have` is cleared, so the "
                     "frozen obligation closes on its own terms. If the post-image "
                     "were unsatisfiable at the shape the change is about, or "
                     "satisfiable only by collapsing the result, this fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input point and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Each rival is straight-line
    # so its witness reduces under NonDetT.run (the gold loop does not).
    # =====================================================================

    # ---- C-value: each argument must be numerically evaluated, not carried raw
    {
        "id": "uniq-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-patch behaviour (Solution_prepatch.lean): the arguments
        # are passed on VERBATIM, with no per-argument numeric evaluation. Correct
        # on C-length (same length) but wrong on C-value wherever an argument's
        # evaluation differs from the argument itself.
        "module": _with_impl("    return args"),
        "refinement": "this is exactly the reported defect: the argument sequence "
                      "is spliced into the function's numerical implementation "
                      "un-evaluated, so a composite argument reaches it as a "
                      "symbolic term rather than a number and the outer numeric "
                      "evaluation cannot reduce it. The failing test evaluates a "
                      "TWO-deep composition of an implemented function and asserts "
                      "the result equals the reduced number; with the arguments "
                      "carried through un-evaluated the inner application stays "
                      "symbolic and the assertion stays RED. It is the pre-patch "
                      "skeleton (G-DIFF), so it does NOT resolve.",
        "rationale": "REJECT from C-value (out = numEvalSeq prec args): the impl "
                     "returns `args` where the post-image demands each element "
                     "numerically evaluated. Probes prec=0, args=[a]; the witness "
                     "hypothesises the evaluator changes `a` (numEval a 0 ≠ a — the "
                     "evalf-changes-a-composite-argument fact G-AX validates). If it "
                     "verified, the per-argument-evaluation guarantee is unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": _EXTRACT +
                   "example (a : Term) (h : numEval a 0 ≠ a) :\n"
                   "    evaluateArgsExec 0 [a] ≠ DivM.res (numEvalSeq 0 [a]) := by\n"
                   "  unfold evaluateArgsExec evaluateArgs\n"
                   "  simp only [numEvalSeq, NonDetT.run, pure]\n"
                   "  simp only [ne_eq, DivM.res.injEq, List.cons.injEq]\n"
                   "  exact fun hc => h hc.left.symm\n",
        # The frozen impl cannot decide this (or any) claim — its `forIn` does
        # not reduce — so the refutation is checked against the loop-free
        # verifying impl of the same spec. Measured: rival 0, reference 1 with
        # `hc : True` (the values agree there, so the hypothesis is unusable),
        # consistency probe 1.
        "witness_reference": _REF_LOOPFREE,
    },

    # ---- C-length: one evaluated element per input argument (no drop) ----
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Evaluates every argument correctly but drops the LAST evaluated element,
        # so the result is one position too SHORT. Correct on the HEAD values but
        # wrong on C-length whenever args is non-empty — the tail-of-sequence
        # sub-domain a head-only value check would miss.
        "module": _with_impl("    return (numEvalSeq prec args).dropLast"),
        "refinement": "forwarding one fewer evaluated argument than the function's "
                      "numerical implementation expects supplies the wrong ARITY: "
                      "the call raises (a TypeError on the missing positional), the "
                      "except-branch leaves the expression symbolic, and the failing "
                      "test's composition is never reduced — the assertion stays "
                      "RED. It would NOT resolve.",
        "rationale": "REJECT from C-length (out.length = args.length): on a "
                     "non-empty args the impl returns a list one shorter than "
                     "args. Probes prec=15, args=[a,b] (both length 2 -> result "
                     "length 1); a `_ :: _` vs `[_]` constructor clash the kernel "
                     "decides with NO hypothesis. If it verified, the "
                     "one-element-per-argument guarantee is unpinned "
                     "(SPEC-TOO-WEAK on C-length).",
        "witness": _EXTRACT +
                   "example (a b : Term) :\n"
                   "    evaluateArgsExec 15 [a, b] ≠ "
                   "DivM.res (numEvalSeq 15 [a, b]) := by\n"
                   "  unfold evaluateArgsExec evaluateArgs\n"
                   "  simp only [numEvalSeq, NonDetT.run, pure, "
                   "List.dropLast_cons₂, List.dropLast_single]\n"
                   "  simp\n",
        # As uniq-identity: the frozen impl decides nothing, so the discriminating
        # build is against the loop-free verifying impl. Measured: rival 0,
        # reference 1 with the semantic residue `⊢ False` (the length claim
        # genuinely does not hold of a correct impl).
        "witness_reference": _REF_LOOPFREE,
    },

    # ---- C-length: the result neither drops nor INVENTS positions ----
    {
        "id": "uniq-concat-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # Evaluates every argument correctly but then appends the ORIGINAL
        # (un-evaluated) arguments, so the result is too LONG (and carries raw
        # elements). Attacks the OTHER end of C-length (over-length) that the
        # drop-last rival does not touch; moves args to a singleton.
        "module": _with_impl("    return numEvalSeq prec args ++ args"),
        "refinement": "appending the arguments a second time forwards MORE "
                      "positionals than the function's numerical implementation "
                      "expects: the call raises (a TypeError on the extra "
                      "positional), the except-branch leaves the expression "
                      "symbolic, and the composition in the failing test is never "
                      "reduced — the assertion stays RED. It would NOT resolve.",
        "rationale": "REJECT from C-length (out.length = args.length): the impl "
                     "returns args.length * 2 elements. Probes prec=53, args=[a] "
                     "(length 1 -> result length 2); a `[_]` vs `_ :: _ :: _` "
                     "constructor clash the kernel decides with NO hypothesis. If "
                     "it verified, the no-invented-position guarantee is unpinned "
                     "(SPEC-TOO-WEAK on C-length). Complements uniq-drop-last "
                     "(short) by attacking the over-length side, and moves prec to "
                     "53 and args to the singleton [a].",
        "witness": _EXTRACT +
                   "example (a : Term) :\n"
                   "    evaluateArgsExec 53 [a] ≠ "
                   "DivM.res (numEvalSeq 53 [a]) := by\n"
                   "  unfold evaluateArgsExec evaluateArgs\n"
                   "  simp only [numEvalSeq, NonDetT.run, pure, List.nil_append, "
                   "List.cons_append, List.singleton_append]\n"
                   "  simp\n",
        # As uniq-identity: the frozen impl decides nothing, so the discriminating
        # build is against the loop-free verifying impl. Measured: rival 0,
        # reference 1 with the semantic residue `⊢ False`, consistency probe n/a
        # (binds only `a : Term`, no hypotheses).
        "witness_reference": _REF_LOOPFREE,
    },

    # ---- C-value on a LENGTH-RESTRICTED sub-domain: an evaluated element
    # ---- replaced by a DIFFERENT opaque term (not a raw carry-through) ----
    {
        "id": "uniq-subst-default",
        "kind": "uniqueness",
        "expect": "reject",
        # The per-element VALUE perturbation on a proper SUB-DOMAIN: correct at
        # every argument count EXCEPT length 1, where it substitutes the opaque
        # `termDefault` for the argument's numeric evaluation. This is the direct
        # analogue of the nagini value-pin rivals (right on part of the domain,
        # wrong elsewhere) and it needs a SECOND opaque term to substitute —
        # which this carrier does have, in the frozen `termDefault` axiom. So it
        # is expressible here, and it attacks C-value in a way `uniq-identity`
        # (which is wrong EVERYWHERE, and wrong by carrying the argument itself)
        # does not: a spec that only forbade the raw carry-through would admit
        # this one. Probes the third distinct prec (7) and the singleton sub-
        # domain that the length rivals leave alone on the value clause.
        "module": _with_impl_and_proof(
            "    let out := if args.length == 1 then [termDefault]\n"
            "               else numEvalSeq prec args\n"
            "    return out",
            "prove_correct evaluateArgs by\n  loom_solve"),
        "refinement": "substituting a fixed default term for one argument's "
                      "numeric evaluation forwards the WRONG VALUE into the "
                      "function's numerical implementation on exactly the "
                      "one-argument shape. The failing test's composition is a "
                      "single-argument application, so the value the numerical "
                      "implementation receives is the default rather than the "
                      "argument's evaluation, the result is not the reduced number "
                      "the assertion demands, and it stays RED. It would NOT "
                      "resolve. (Nor is it rescued by the multi-argument branch "
                      "being correct: the discriminating shape is the restricted "
                      "one.)",
        "rationale": "REJECT from C-value (out = numEvalSeq prec args): at "
                     "args.length = 1 the impl returns [termDefault] where the "
                     "post-image demands [numEval a prec]. Probes prec=7, "
                     "args=[a]; the witness hypothesises the evaluation of `a` "
                     "differs from the default (numEval a 7 ≠ termDefault) — one "
                     "hypothesis about one opaque application, left consistent "
                     "(the derive-False probe cannot close it: exit 1, measured). "
                     "The other-length branch returns the grounded map and is "
                     "correct, so the rejection attributes precisely to the "
                     "singleton sub-domain. If it verified, C-value would be "
                     "unpinned against a wrong-VALUE substitution as opposed to a "
                     "raw carry-through (SPEC-TOO-WEAK on C-value).",
        "witness": _EXTRACT +
                   "example (a : Term) (h : numEval a 7 ≠ termDefault) :\n"
                   "    evaluateArgsExec 7 [a] ≠ "
                   "DivM.res (numEvalSeq 7 [a]) := by\n"
                   "  unfold evaluateArgsExec evaluateArgs\n"
                   "  simp only [numEvalSeq, NonDetT.run, pure, List.length_cons,\n"
                   "    List.length_nil, beq_self_eq_true, if_pos]\n"
                   "  simp only [ne_eq, DivM.res.injEq, List.cons.injEq]\n"
                   "  exact fun hc => h hc.left.symm\n",
        # Measured: rival 0, reference 1 with `hc : True` (a correct impl agrees
        # there, so the hypothesis cannot close the goal), probe 1.
        "witness_reference": _REF_LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals, 2 of them frame-mutation);
# every one is accounted for below. The two carriers are NOT the same partition:
# the sibling models the numeric core `eval_implemented(leaf, layers) ->
# Optional[int]` with a fully-grounded `@Pure` fold `eval_seq` (imp(x)=x*x), a
# `leaf>=0 / eval_seq<1e14` precondition, and `layers` at `Acc(list_pred, 1/2)`;
# this bundle models one level up, the argument-sequence pre-evaluation
# `evaluateArgs prec args -> List Term`, a list-to-list map over the OPAQUE
# per-argument evaluator `numEval`, with no precondition and no permissions. The
# nagini rivals over the numeric-depth carrier re-site onto the two clauses of
# `numEvalSeq`.
#
#   sibling case                        -> here                         status
#   ---------------------------------------------------------------------------
#   pos-cheapest-fold                   -> pos-cheapest-map             PORTED
#   pos-loop-rename                     -> pos-loop-rename              PORTED
#   admiss-self-call                    -> admiss-postimage-
#                                            nondegenerate           RE-AIMED
#   frame-mutate-append                 -> (none, VACUOUS)              OMITTED
#   frame-mutate-index                  -> (none, VACUOUS)              OMITTED
#   partial-none-on-composition         -> uniq-identity               RE-SITED
#   partial-offbyone-on-composition     -> uniq-subst-default           RE-SITED
#   partial-wrong-bare-leaf             -> uniq-drop-last +
#                                          uniq-concat-raw              RE-SITED
#
# 2 ported, 1 re-aimed, 3 re-sited (onto 4 rivals), 2 omitted (both vacuous
# frame-mutation). Plus one positive with no sibling counterpart,
# pos-elementwise-map, added because both ported positives reuse gold's own proof
# argument (renamed loop; oracle echo) and neither tested that the spec is
# provable from a DIFFERENT argument.
#
# RE-SITED (the argument is unchanged; only the carrier is):
#  * partial-none-on-composition attacks the nagini "always a present number"
#    clause on the composition sub-domain: for >=2 layers the pre-patch returns
#    None (left unevaluated). This carrier has no Optional/None channel and no
#    numeric depth; "left unevaluated" here IS "the argument is carried through
#    un-evaluated" (`return args`), which is the pre-patch skeleton in
#    Solution_prepatch.lean and the discriminating F2P behaviour the public issue
#    reports. That is uniq-identity, attacking C-value.
#  * partial-offbyone-on-composition and partial-wrong-bare-leaf are the nagini
#    VALUE-pin rivals (right on part of the numeric domain, off by one elsewhere).
#    The sub-domain value perturbation re-sites DIRECTLY, as uniq-subst-default:
#    a rival that returns the grounded map everywhere except one length class,
#    where an element's evaluation is replaced by a DIFFERENT opaque term. An
#    earlier revision of this manifest recorded that shape as "not expressible
#    without a second opaque term to substitute" and re-sited both value rivals
#    onto C-LENGTH instead. That reason was WRONG, and an audit landed the case:
#    the carrier already HAS a second opaque term — the frozen `termDefault`
#    axiom — and no equational fact about either term is needed, because the
#    witness states the disagreement by HYPOTHESIS (numEval a 7 ≠ termDefault)
#    and the gate's consistency probe confirms that hypothesis is satisfiable
#    (an opaque pair makes it easy: no tactic derives False from it). Built and
#    measured: rival 0, reference 1, probe 1. It is a genuinely distinct attack
#    on C-value — a spec forbidding only the raw carry-through of uniq-identity
#    would admit a wrong-VALUE substitution — so it ships rather than being
#    accounted for as carrier collapse.
#    partial-wrong-bare-leaf additionally re-sites onto the C-LENGTH clause, as
#    uniq-drop-last (a position dropped -> wrong arity into the numerical
#    implementation) and uniq-concat-raw (a position invented -> wrong arity),
#    which attack the OTHER top-level clause the nagini battery had no direct
#    counterpart for on this carrier (the nagini spec's length was implicit in the
#    Optional result). Both also carry a raw element, so they secondarily violate
#    C-value. This is carrier narrowing (mapping.md §2): the modeled operation is
#    the sequence pre-evaluation, whose two observable clauses are per-element
#    value and length/order, and both are attacked.
#
# NOT SHIPPED, ON PURPOSE (order / precision rivals). The spec pins C-value
# element-wise AND in order AND at prec. A rival that evaluates every argument
# but reverses the list, or evaluates at a fixed wrong precision, is refutable
# against the spec (verified during authoring) BUT its faithful real patch would
# RESOLVE the failing test: test_issue_12092 is `f(f(2)).evalf() == Float(16)` —
# a SINGLE argument (self.args is a one-tuple), so reordering is the identity, and
# the values are exact integers, so any precision computes Float(16). A verifying
# reversal/precision rival is therefore a spec artifact (the spec is stronger than
# the test), NOT a verify-does-not-resolve break, so it is excluded. Every shipped
# rival is one whose faithful patch leaves F2P red.
#
# RE-AIMED:
#  * admiss-self-call -> admiss-postimage-nondegenerate. The sibling discharges a
#    domain precondition (leaf>=0 and eval_seq<1e14) plus two Acc(list_pred,1/2)
#    halves at a representative call site. This bundle has NO `require` clause and
#    no fractional permissions, and an earlier revision of this manifest concluded
#    from that alone that the lane was vacuous — "the machinery it exercises does
#    not exist here". That reason was WRONG, in the same way the earlier
#    uniq-subst-default omission was: it identifies the mechanism rather than the
#    DIRECTION the lane tests. PRECOND-TOO-STRONG on a total carrier is the
#    obligation being unsatisfiable, or degenerate, at exactly an F2P-shaped
#    input, and that is testable — by a positive that exhibits a joint witness for
#    both ensures clauses at the concrete one-argument shape, by evaluation, as a
#    `have` that is `clear`ed before the frozen obligation closes verbatim. Landed
#    and measured: shipped script exit 0, and three negative controls that
#    perturb one conjunct each all fail (see the case for the exact errors), so
#    the case is not passing on a tautology.
# OMITTED (2):
#  * frame-mutate-append, frame-mutate-index. Nagini-specific fractional heap
#    permissions: a value-no-op write to `layers` the value abstraction cannot
#    see but the permission system rejects. This backend is referentially
#    transparent and the method declares no `mut` binder — `prec` and `args` are
#    immutable values with no heap and no aliasing — so there is no read-only
#    input to overwrite and no substitute probe. VACUOUS; not fabricated (per the
#    porting map's frame/permission row).
#
# DIVERGENCE lane: this bundle is `total` (frozen line 4), NOT `partial` — an
# earlier revision of this manifest asserted `partial` and recorded the class as a
# known spec hole, which was false about this bundle's own semantics option. Under
# `total` the verifier discharges a termination obligation, so there IS no hole:
# re-measured with real builds, the frozen body prefixed with an unbounded
# `while spin ≥ 0 ... do spin := spin + 1` (no `decreasing`) is REJECTED, exit 1,
# `error: Decreasing annotations are required in total correctness semantics` plus
# `Failed to prove assertion without names: WPGen`. It is still not shippable as a
# reject case, for a mechanical reason: the missing decreasing annotation is a hard
# `loom.linter.errors` diagnostic, so the rival's file fails to elaborate whatever
# is appended, and the witness build against the rival exits 1 (measured) — which
# the gate reads as `witness-unproven`, an inconclusive outcome that FAILS the
# battery. So: class closed by the frozen semantics, case blocked by the reject
# lane's own requirement. Neither a hole nor vacuous. Same shape measured on
# scikit-learn__scikit-learn-10908/velvet.
#
# BINDER / CLAUSE COVERAGE. Two input binders `prec`, `args`. The four reject
# witnesses probe four DISTINCT input points and move both binders: `prec` at
# {0, 7, 15, 53} (never pinned); `args` at {[a] (singleton), [a,b] (pair)}. Both
# top-level clauses are attacked: C-value by uniq-identity (a raw carry-through,
# wrong everywhere) and uniq-subst-default (a wrong VALUE on a length-restricted
# sub-domain), and secondarily by the two length rivals, which carry raw
# elements; C-length by uniq-drop-last (short) and uniq-concat-raw (long). Three
# positive controls defend the whole obligation, each by a DIFFERENT proof
# argument: pos-loop-rename reuses gold's invariant, pos-cheapest-map closes by
# reflexivity on the grounded oracle, pos-elementwise-map needs a fresh induction.
# The admissibility positive adds the third gate direction, pinning both clauses
# as jointly satisfiable and non-degenerate at the F2P-shaped input.
#
# WITNESS DISCRIMINATION. Each witness ELABORATES against its straight-line rival
# (the rival's output provably differs from numEvalSeq at the probed point) and
# FAILS against `_REF_LOOPFREE`, the loop-free VERIFYING impl of the same frozen
# spec, which the gate re-checks (same_spec + verifies) before using it. The
# frozen solution is NOT the subject, and that is measured rather than assumed:
# its `mut`/while body desugars to `forIn Lean.Loop.mk ...`, which the kernel
# cannot reduce under loom.semantics.choice "demonic", so the goal against it is
# left with the whole unreduced `forIn` for every claim — the witness AND the
# opposite, TRUE, claim at the same input both fail there with the byte-identical
# `unsolved goals` residue, while `1 + 1 = 2` in the same file builds. Against
# the reference the claims genuinely reduce: the two length witnesses leave
# `⊢ False` and the two value witnesses leave `hc : True` (a correct impl agrees
# at that element, so the hypothesis cannot close the goal), and the TRUE claim
# BUILDS (exit 0) — which is what makes the reference's exit codes informative.
# uniq-identity and uniq-subst-default each carry ONE hypothesis about a single
# opaque application (the evalf-changes-a-composite-argument fact G-AX validates,
# resp. its disagreement with the default) — the gate's consistency_probe cannot
# derive `False` from either (checked: exit 1). The two length witnesses bind
# NOTHING (bare constructor/nil clashes). No sorry/admit/native_decide/axiom
# appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and is validated by
# axiom_check.py (numEval/numEvalSeq == the real Expr.evalf comprehension,
# mapping.md §3); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
