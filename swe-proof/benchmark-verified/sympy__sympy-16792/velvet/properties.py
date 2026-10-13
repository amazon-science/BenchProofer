"""properties.py — G-PBT falsification battery for sympy__sympy-16792 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct buildArgList``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  buildArgList (requests : List ArgSpec) return (out : List Arg)
    ensures out = argList requests

``argList`` is a front-recursive spec fold mapping each request through
``argFor``, in order. ``argFor`` decides one request's produced argument by three
observables of that request: whether an argument for it was ALREADY built (reuse
its prior form verbatim), and otherwise whether the request is ARRAY-LIKE (carry
its extent-derived dimension metadata) or a plain scalar (carry none). The single
load-bearing ``ensures`` pins ``out`` element-wise to ``argList requests``: the
count and order of the request sequence are preserved and each request yields
exactly its ``argFor`` argument. The content the issue turns on lives in the
fresh-array-like sub-case — a freshly-built array-like request must receive its
dimension metadata, not be flattened to a scalar.

FOUR MODELED BINDERS of the per-request decision (the fields of each ``ArgSpec``
the clause reads): ``alreadyResolved`` (reuse-prior vs build-fresh),
``prior`` (the reused argument), ``arrayLike`` (owns a shape vs scalar), and
``extents`` (the per-axis shape). Plus the list-level shape (length and order of
``requests``). The reject witnesses must move each of these, since a rival that
mishandled only one sub-case — only fresh-array-like, only fresh-scalar, only the
reuse leg, or only the list shape — would slip past a battery that pinned it.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``buildArgListTester requests = false`` says the
extracted program's result violates the postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. ``decide`` reduces the
extracted program by kernel computation; a program shaped as a ``while`` loop
does NOT reduce to ``isTrue``/``isFalse`` (the loop's fixpoint is opaque to the
kernel). So each reject rival is expressed as a LOOP-FREE impl that computes its
(wrong) argument list directly from the pure helpers (``argFor`` / ``extentBounds``
/ ``List.map``), still a wrong implementation sharing the frozen spec but one
whose extracted tester ``decide``s. The carrier is fully transparent here (no
opaque callee; the ``axioms`` region is empty and every observable is computed
from the inputs), so witnesses use concrete literals and never condition on a
hypothesis. This is a witnessing convenience, not a weakening: the frozen spec is
untouched and each rival's divergence from ``argList`` is real at the witnessed
input.

ASYMMETRY OF THE TWO WITNESS BUILDS (measured during the audit — read this before
trusting a gold-side exit code). The same loop-opacity that forces the rivals to
be loop-free also means the FROZEN file's tester never ``decide``s at all: gold's
impl IS the ``while`` loop, so against gold every witness fails with ``Tactic
`decide` failed ... did not reduce to `isTrue` or `isFalse` `` — a STUCK
REDUCTION, not "``decide`` proved the proposition is false". Confirmed by building
the *true* claim ``buildArgListTester [<a fresh array-like request>] = true``
against the frozen file: it also fails, identically stuck (exit 1). So the gate's
gold-side half is satisfied here for a SYNTACTIC reason, and on its own it does
not establish that a witness discriminates by content.

What does establish it, and what the audit therefore ran per reject case, is a
third build the gate does not do: the same witness statement against a LOOP-FREE
but CORRECT impl (``return requests.map argFor``, the shape of
``pos-control-forward-map``). That file reduces, so the verdict is semantic, and
for all five reject witnesses it fails with ``Tactic `decide` proved that the
proposition ... is false`` (exit 1) — i.e. at each witnessed input the correct
argument list SATISFIES the postcondition and only the rival violates it. Each
rival's witness therefore separates wrong-from-correct on content, not
loop-from-no-loop. Anyone re-auditing this battery should re-run that control
rather than reading the gold-side exit code as a refutation.

ADVERSARIAL READ of the weakness classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's mandatory
    frame-mutation rivals write to a read-only input carrying a fractional heap
    permission. This backend is referentially transparent: ``requests`` is an
    immutable ``List ArgSpec`` value, this bundle declares no ``mut`` binder on an
    input, and there is no heap and no aliasing. There is no read-only input to
    overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated (per the porting map, dropped rather than replaced).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane. The single
    clause pins the produced argument on EVERY request, so a rival that flattens a
    fresh array-like request to a scalar (drops its metadata), or over-promotes a
    fresh scalar to array metadata, or discards the prior form on the reuse leg,
    diverges from ``argList`` at a concrete request.
  * LENGTH / ORDER — APPLIES. A rival that emits one fewer element (drops the
    head) violates the element-wise/count pinning of the clause.
  * UNGROUNDED-ORACLE ECHO — N/A. ``argList`` is a fully unfolded ``def`` over the
    method's own argument (the ``axioms`` region is empty — no opaque answer key
    to echo); the only way to satisfy the postcondition is to build the per-request
    argument map correctly, which the positive control does honestly.

WITNESS PLACEMENT. The five reject witnesses sit at FIVE DISTINCT input points and
between them move every modeled binder: ``alreadyResolved`` across false (the
three fresh-arm rivals) and true (the reuse-leg and head-drop rivals);
``arrayLike`` across true (fresh-array-like) and false (fresh-scalar); ``extents``
across ``[2]``, ``[3]``, ``[]``, ``[5]`` and ``[2,1]`` — the last being the only
MULTI-AXIS point, which is what pins the metadata's per-axis content rather than
merely its presence; ``prior`` across ``[]``, ``[(5,7)]`` and ``[(1,4)]``; and the
list shape across length 1 and length 2. Rivals do not share a witness: each is
refuted at the request-kind it specifically mishandles. pts=5.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16792"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the value/structure-attacking rivals, which
# abandon the loop entirely so their extracted tester `decide`s.
_IMPL = (
    "    let mut result : List Arg := []\n"
    "    let mut i := requests.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ requests.length\n"
    "      invariant result = argList (requests.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := requests[i - 1]!\n"
    "      result := argFor e :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "impl-body anchor drift — re-sync _IMPL"

# The two loop-body lines that bind `e` then prepend its argument. The positive
# control names the produced argument in a local `let` before prepending — a
# data-flow reshape that keeps `result` definitionally identical, so `loom_solve`
# leaves the same single loop-body goal and the frozen tactic script closes it.
_INNER = (
    "      let e := requests[i - 1]!\n"
    "      result := argFor e :: result\n"
)
assert _BASE.count(_INNER) == 1, "inner-line anchor drift"

# The impl-start marker line (unique); the admissibility case inserts an in-region
# `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). Reject
# rivals reshape the impl into a single expression with no loop invariant to peel,
# so `loom_solve` alone is retuned in — for them it FAILS, which is the point; the
# rejection is attributed to the spec (the witness), not to a proof script tuned to
# a loop that no longer exists.
_PROOF = (
    "prove_correct buildArgList by\n"
    "  loom_solve\n"
    "  rw [argList_drop_step requests i (by omega) (by omega)]\n"
    "  simp_all\n"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

_PROOF_FLAT = "prove_correct buildArgList by\n  loom_solve\n"

# Admissibility proof: clears the extra in-region assert goal by `decide` while
# still discharging the method's own loop-body goal by the frozen fold step.
_PROOF_ADMISS = (
    "prove_correct buildArgList by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | decide\n"
    "    | (rw [argList_drop_step requests i (by omega) (by omega)]; simp_all)\n"
)


def _rival(expr):
    """A loop-free reject rival: swap the whole loop body for `expr` and retune
    the proof to the flat shape (which fails — the witness carries the rejection)."""
    return _swap(_swap(_BASE, _IMPL, expr), _PROOF, _PROOF_FLAT)


# ---- witness helper. The spec is a `method` contract, so a witness reaches the
# ---- post-image through Velvet's own tester machinery:
# ---- `buildArgListTester requests = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every request is a
# ---- concrete `ArgSpec` literal so `decide` reduces the loop-free program.
def _tester(body):
    return (
        "\n"
        "extract_program_for buildArgList\n"
        "prove_precondition_decidable_for buildArgList\n"
        "prove_postcondition_decidable_for buildArgList\n"
        "derive_tester_for buildArgList\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The per-request argument
    # is named in a local `let a := argFor e` before the prepend: the accumulated
    # `result` is DEFINITIONALLY identical, so `loom_solve` leaves the same single
    # loop-body goal and the frozen tactic script discharges it unchanged. No new
    # lemma; the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-control-named-argument",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      let e := requests[i - 1]!\n"
            "      let a : Arg := argFor e\n"
            "      result := a :: result\n"),
        "rationale": (
            "naming the per-request produced argument in a local `let a := argFor "
            "e` before prepending leaves the accumulated `result` definitionally "
            "identical, so `out = argList requests` still holds on the whole "
            "domain; the loop, invariants and frozen proof script are untouched. A "
            "correct reshape must verify, else the postcondition is SPEC-TOO-STRONG "
            "over the shape of the accumulation step. NOTE (audit): this reshape is "
            "DEFINITIONALLY equal to the frozen impl, so it is a weak soundness "
            "probe on its own — `pos-control-forward-map` below carries the real "
            "SPEC-TOO-STRONG load."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness, the load-bearing one) — a correct impl whose
    # shape is genuinely DIFFERENT, not definitionally equal: the loop, the two
    # invariants and the backward accumulation are abandoned entirely for a single
    # FORWARD `List.map` over the requests. `List.map argFor requests` is NOT
    # definitionally `argList requests` (the frozen `rfl`-shaped lemmas do not
    # close it — measured: the frozen tactic script leaves
    # `⊢ List.map argFor requests = argList requests` unsolved), so this case has
    # to reprove the obligation from scratch by induction on `requests`. It still
    # verifies, which is real evidence the postcondition constrains the FUNCTION
    # computed and not the loop shape that computes it. A faithful correct impl the
    # spec rejected here would be a soundness hole in the frozen spec.
    # =====================================================================
    {
        "id": "pos-control-forward-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL, "    return requests.map argFor\n"),
            _PROOF,
            "prove_correct buildArgList by\n"
            "  loom_solve\n"
            "  induction requests <;> simp_all [argList]\n"),
        "rationale": (
            "a loop-free FORWARD map is a faithful correct implementation of the "
            "same function: `List.map argFor requests = argList requests` for every "
            "`requests` (by induction, peeling `argList_cons`), so `out = argList "
            "requests` holds on the whole domain. It is NOT definitionally equal to "
            "the frozen backward accumulation — the frozen proof script does not "
            "close it — so it must be reproven, and the obligation statement is "
            "byte-identical. If the spec rejected this it would be SPEC-TOO-STRONG: "
            "pinning the accumulation order rather than the argument list computed."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like one every impl meets. This case discharges an
    # in-region `assert`, at the F2P-shaped input (a single freshly-built
    # array-like request whose shape is [2,1], mirroring the absent 2×1 matrix
    # argument of the issue), that the post-image is NON-DEGENERATE: the produced
    # argument carries the extent-derived metadata [(0,1),(0,0)] rather than empty
    # (scalar) metadata. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned only to clear the extra
    # assert goal by `decide` (allowed — the tactic body is elided). The assert is
    # live: re-checked during the audit by building the asserted proposition
    # standalone in both polarities against the frozen file — the true form
    # (`argList [<the 2x1 fresh array-like request>] = [{ bounds := [(0,1),(0,0)] }]`)
    # elaborates (exit 0) and the false twin (`= [{ bounds := [] }]`) fails with
    # "`decide` proved that the proposition ... is false" (exit 1), so the claim is
    # decided on content and could not have passed vacuously.
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `admiss\n"
                "      (argList [({ alreadyResolved := false, prior := { bounds := [] }, arrayLike := true, extents := ([2,1] : List Int) } : ArgSpec)]\n"
                "        = [({ bounds := [((0:Int),(1:Int)), ((0:Int),(0:Int))] } : Arg)]))\n"),
            _PROOF, _PROOF_ADMISS),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: for a single freshly-built array-like request of shape [2,1] "
            "(the absent 2×1 matrix argument of the issue) it demands the produced "
            "argument carry the extent-derived dimension metadata "
            "[(0,1),(0,0)] rather than empty scalar metadata. The in-region assert "
            "must discharge (else the obligation is unsatisfiable / degenerate at "
            "the point the fix cares about); the impl is kept verbatim so the "
            "method's own `ensures` still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete input
    # and the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test. Each is a LOOP-FREE impl so its extracted tester
    # `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-fresh-arraylike-flattened",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch behaviour: a request that must be built fresh is ALWAYS
        # given empty dimension metadata, regardless of array-likeness. An
        # array-like request absent from the resolved set comes back as a plain
        # scalar (empty bounds) instead of carrying its extent-derived dimensions.
        "module": _rival(
            "    return requests.map (fun e => if e.alreadyResolved then e.prior else ({ bounds := [] } : Arg))\n"),
        "refinement": (
            "this reproduces the prepatch behaviour: a freshly-built array-like "
            "request is flattened to empty dimension metadata, so it is emitted as "
            "a by-value scalar argument instead of a by-reference array argument. "
            "Its faithful real counterpart attaches no metadata in the fresh arm "
            "for an array-like symbol, which is exactly the pre-fix code path that "
            "FAILS the failing scenario (an absent array argument rendered "
            "by-value). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = argList requests`: `argFor` gives a fresh "
            "array-like request its extent-derived metadata, and this impl gives "
            "empty metadata, so the two disagree whenever a request is fresh AND "
            "array-like. Verifying would be SPEC-TOO-WEAK on the fresh-array-like "
            "sub-domain (the whole content of the fix). Refuted at a single fresh "
            "array-like request of shape [2] (alreadyResolved=false, arrayLike=true, "
            "extents=[2]), whose correct metadata is [(0,1)]."
        ),
        "witness": _tester(
            "example : buildArgListTester "
            "[({ alreadyResolved := false, prior := { bounds := [] }, arrayLike := true, extents := ([2] : List Int) } : ArgSpec)] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-fresh-scalar-overpromoted",
        "kind": "uniqueness",
        "expect": "reject",
        # The other fresh-arm sub-domain: a freshly-built PLAIN SCALAR request is
        # wrongly given extent-derived metadata (promoted to array-like) instead
        # of empty metadata. Correct on array-like and reuse legs; wrong on fresh
        # scalars.
        "module": _rival(
            "    return requests.map (fun e => if e.alreadyResolved then e.prior else ({ bounds := extentBounds e.extents } : Arg))\n"),
        "refinement": (
            "a freshly-built plain scalar request is over-promoted to carry "
            "extent-derived metadata, so a scalar argument would be emitted "
            "by-reference. Its faithful real counterpart attaches array metadata in "
            "the fresh arm unconditionally, which mis-renders every scalar argument "
            "as a pointer — breaking the scalar-argument scenarios the passing "
            "tests pin. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = argList requests`: `argFor` gives a fresh scalar "
            "request empty metadata, and this impl gives extent-derived metadata, "
            "so the two disagree whenever a request is fresh AND a scalar with "
            "non-empty extents. Verifying would leave the fresh-scalar sub-domain "
            "unpinned (partial-domain SPEC-TOO-WEAK), the complement of the "
            "flattening rival, so this near-miss carries its own discriminating "
            "input. Refuted at a single fresh scalar request with extents=[3] "
            "(alreadyResolved=false, arrayLike=false), whose correct metadata is []."
        ),
        "witness": _tester(
            "example : buildArgListTester "
            "[({ alreadyResolved := false, prior := { bounds := [] }, arrayLike := false, extents := ([3] : List Int) } : ArgSpec)] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-reuse-leg-recomputed",
        "kind": "uniqueness",
        "expect": "reject",
        # The reuse leg: an ALREADY-RESOLVED request must be reused VERBATIM
        # (its prior argument, whose metadata was fixed at scan time). This rival
        # ignores `alreadyResolved`/`prior` entirely and recomputes every request
        # from its arrayLike/extents fields, so a resolved request whose prior
        # form differs from a fresh recomputation diverges.
        "module": _rival(
            "    return requests.map (fun e => ({ bounds := if e.arrayLike then extentBounds e.extents else [] } : Arg))\n"),
        "refinement": (
            "an already-resolved request is recomputed from scratch instead of "
            "reusing its prior argument, discarding the metadata determined when it "
            "was first built. Its faithful real counterpart drops the reuse branch "
            "and rebuilds every requested symbol, so a symbol already turned into "
            "an argument while scanning the expression is re-derived with possibly "
            "different metadata — changing the generated prototype for the "
            "resolved-argument scenarios the passing tests pin. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from `out = argList requests`: `argFor` reuses the prior "
            "argument on the resolved leg, and this impl recomputes from "
            "arrayLike/extents, so the two disagree whenever a resolved request's "
            "prior form is not what a fresh recomputation would produce. Verifying "
            "would leave the reuse leg (the `alreadyResolved`/`prior` binders) "
            "unpinned. Refuted at a single resolved request with prior bounds "
            "[(5,7)] but arrayLike=false, extents=[] (alreadyResolved=true): gold "
            "reuses [(5,7)] while the rival recomputes []."
        ),
        "witness": _tester(
            "example : buildArgListTester "
            "[({ alreadyResolved := true, prior := { bounds := [((5:Int),(7:Int))] }, arrayLike := false, extents := ([] : List Int) } : ArgSpec)] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-drop-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Length/order class: build every argument correctly then drop the head,
        # so the output has one fewer element and every request after the first is
        # shifted. Correct per-element values; wrong count and order.
        "module": _rival(
            "    return (requests.map argFor).tail\n"),
        "refinement": (
            "every per-request argument is built correctly but the first is "
            "dropped, so the produced argument list is one element short. Its "
            "faithful real counterpart omits the leading requested symbol from the "
            "argument list, dropping the first parameter from the generated "
            "prototype and breaking the requested argument order/count the passing "
            "tests pin. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = argList requests`: the clause pins the count and "
            "order element-wise, and this impl returns `(requests.map argFor).tail` "
            "— length `len - 1` and shifted — so it disagrees on any non-empty "
            "request sequence. Verifying would leave the list-level shape (length "
            "and order) unpinned. Refuted at a two-request sequence "
            "(a resolved array-like request with prior [(1,4)], then a fresh "
            "scalar): gold keeps both in order, the rival drops the first."
        ),
        "witness": _tester(
            "example : buildArgListTester "
            "[({ alreadyResolved := true, prior := { bounds := [((1:Int),(4:Int))] }, arrayLike := true, extents := ([5] : List Int) } : ArgSpec), "
            "({ alreadyResolved := false, prior := { bounds := [] }, arrayLike := false, extents := ([] : List Int) } : ArgSpec)] = false := by\n"
            "  decide\n"),
    },
    {
        # ADDED BY AUDIT. The four rivals above all attack WHETHER metadata is
        # attached (present/absent/reused) and all four are refuted at SINGLE-axis
        # extents ([2], [3], [], [5]). None of them attacks the metadata's own
        # per-axis CONTENT, so an impl that attaches metadata on exactly the right
        # leg but records only the FIRST axis was unattacked: measured during the
        # audit, this rival survives all four shipped witnesses (each of their
        # `decide` builds against it exits 1 — they agree with gold at their
        # single-axis points), which is precisely a rival that is wrong where no
        # witness looks. It matters here because the issue's own argument is a
        # 2x1 (two-axis) array-like quantity, so the axis count is load-bearing
        # content, not a cosmetic detail.
        "id": "weak-first-axis-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    return requests.map (fun e => if e.alreadyResolved then e.prior else "
            "({ bounds := if e.arrayLike then extentBounds (e.extents.take 1) else [] } : Arg))\n"),
        "refinement": (
            "a freshly-built array-like request receives dimension metadata for its "
            "FIRST axis only, so a multi-axis quantity is described as if it were "
            "one-dimensional. Its faithful real counterpart derives the bound pairs "
            "from a truncated shape instead of the whole shape, so a multi-axis "
            "array argument is emitted with the wrong extent list — the declared "
            "argument disagrees with the caller's actual layout for exactly the "
            "multi-axis shape the failing scenario uses. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = argList requests`: `argFor` maps EVERY axis of a "
            "fresh array-like request through `extentBounds`, and this impl maps "
            "only the first, so the two disagree on any fresh array-like request "
            "with two or more axes. Verifying would leave the per-axis CONTENT of "
            "the metadata unpinned (SPEC-TOO-WEAK on the `extents` binder beyond "
            "its first element) — the sub-domain the four other rivals leave "
            "untouched, since each of those is refuted at a single-axis extent. "
            "Refuted at a single fresh array-like request of shape [2,1], whose "
            "correct metadata is [(0,1),(0,0)] and whose rival metadata is [(0,1)]."
        ),
        "witness": _tester(
            "example : buildArgListTester "
            "[({ alreadyResolved := false, prior := { bounds := [] }, arrayLike := true, extents := ([2,1] : List Int) } : ArgSpec)] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 2 partial-domain uniqueness
# rivals, 1 length-class uniqueness rival) plus 1 AXIOM_TESTS probe. This bundle
# models the changed operation DEEPLY (the per-request argument map `argList` via
# `argFor`/`extentBounds`, spelled-out), so there is no axiom and no permission
# surface; the value/length surface carries across intact.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder           -> pos-control-named-argument      PORTED
#   admiss-f2p-shape                     -> admiss-f2p-shape-nondegenerate  RE-AIMED
#   partial-absent-matrix-prepatch       -> weak-fresh-arraylike-flattened  PORTED
#   partial-absent-indexed-overpromote   -> weak-fresh-scalar-overpromoted  RE-EXPRESSED
#   frame-mutation-kinds                 -> (none)                          VACUOUS
#   frame-mutation-present               -> (none)                          VACUOUS
#   length-short-drop-last               -> weak-drop-head                  PORTED (re-aimed at head)
#   ax-sound-deep-model-vs-real-proto    -> (none)                          DROPPED (G-AX lane)
#
#   plus NET-NEW cases with no direct sibling:
#   (n/a)                                -> weak-reuse-leg-recomputed        ADDED
#   (n/a)                                -> weak-first-axis-only             ADDED (audit)
#   (n/a)                                -> pos-control-forward-map          ADDED (audit)
#
# 4 ported/re-expressed, 1 re-aimed admissibility, 3 net-new, 2 vacuous, 1
# axiom-lane dropped. No case was dropped because its proof was hard.
#
# RE-EXPRESSED (weak-fresh-scalar-overpromoted): the sibling attacks a distinct
#   non-array requested quantity wrongly promoted to carry a shape. On this
#   carrier the modeled decision sees only array-like or plain-scalar requests, so
#   the discriminable analogue is "a fresh scalar over-promoted to array
#   metadata", the exact complement of the flattening rival: it refutes the same
#   clause on the fresh-scalar sub-domain.
# RE-AIMED (admissibility): the sibling establishes the F2P-shaped precondition is
#   satisfiable. There is no precondition here, so that probe is vacuous. It is
#   re-aimed at the residual admissibility risk on a total domain — that the
#   post-image is unsatisfiable/degenerate at the interesting point — via an
#   in-region assert pinning the produced argument for the absent 2×1 matrix
#   request to its extent metadata [(0,1),(0,0)], counting the shape rather than
#   flattening it.
# ADDED (weak-reuse-leg-recomputed): the sibling never attacks the reuse leg (its
#   carrier has no `alreadyResolved`/`prior` distinction in the modeled function).
#   Here `argFor` reuses the prior argument verbatim on the resolved leg, so the
#   `alreadyResolved`/`prior` binders would go unattacked without this rival — a
#   binder no witness moves is a binder no rival was built to abuse. Added to
#   defend the reuse leg.
# VACUOUS (frame-mutation-kinds, frame-mutation-present): the sibling writes to a
#   read-only input carrying a fractional heap permission and is rejected for
#   INSUFFICIENT PERMISSION before any value reasoning. This backend is
#   referentially transparent: `requests` is an immutable `List ArgSpec` value,
#   this bundle declares no `mut` binder on an input, and there is no heap or
#   aliasing. There is no read-only input to overwrite and no permission system to
#   trip. No substitute is fabricated (per the porting map, dropped rather than
#   replaced). Re-derived independently during the audit rather than taken on
#   trust: the class needs a read-only input to write, i.e. a `mut` binder on
#   `requests`. Adding one was tried and is not expressible as a same-spec
#   variant — the `method` header lives in the CONSUMER SPEC VIEW, so
#   `mut requests` changes it and `variant_scope` rejects the case with
#   "spec view differs (same_spec failed)" before any build. So the class is
#   genuinely inexpressible on this carrier, not merely hard: expressing it
#   would require editing the frozen spec, which is out of this lane.
# DROPPED (ax-sound-*): the sibling's AXIOM_TESTS probe validates the deep
#   array-ness/pointer-rendering model against the real sympy callee. This bundle
#   has NO axiom (meta.json axioms=[]; the per-request map is modeled deeply, no
#   opaque oracle), so there is no axiom lane to mirror. The axiom lane is G-AX's
#   job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = argList requests` is attacked
#   by all five rivals across distinct sub-domains — fresh-array-like flattening,
#   fresh-scalar over-promotion, reuse-leg recomputation, head-drop
#   (length/order), and first-axis-only metadata — refuted at FIVE DISTINCT input
#   points (pts=5). Every modeled binder is moved: `alreadyResolved` across false
#   (the three fresh-arm rivals) and true (the reuse-leg and head-drop rivals);
#   `arrayLike` across true and false; `extents` across [2], [3], [], [5] and the
#   multi-axis [2,1]; `prior` across [], [(5,7)] and [(1,4)]; the list shape across
#   length 1 and length 2 (order probed by the head-drop rival). No two rivals share
#   a witness — each is refuted at the request-kind it specifically mishandles.
#
#   The `extents` binder is the one where "the binder varies" was NOT the same as
#   "the variation is meaningful", and it is why `weak-first-axis-only` exists.
#   Before the audit the four witnesses moved `extents` across [2], [3], [] and
#   [5] — four spellings, but every non-empty one a SINGLE-axis shape, so all four
#   agree with gold about how many bound pairs to emit. Measured: an impl that
#   emits only the first axis's bound pair survives all four shipped witnesses
#   (each of their `decide` builds against it exits 1). The added multi-axis point
#   [2,1] is what makes the variation discriminating, and it is the shape the
#   issue's own array argument has.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
