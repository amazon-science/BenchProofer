"""properties.py — G-PBT falsification battery for sympy__sympy-13877 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both elided from the consumer spec view, so ``markers.same_spec`` holds and the
``prove_correct selectPivot`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it ELABORATES against the rival and FAILS against the
discrimination subject). Here that subject is the declared ``witness_reference``,
NOT the frozen solution — the frozen loop's extracted program does not reduce in
the kernel, so a ``decide`` against it is stuck rather than refuting. See WITNESS
MECHANICS below; this is the audit's central correction to this file.

DEFENDED SURFACE (one contracted method over the single binder ``col``):

  selectPivot (col : Array Entry) return (res : PivotResult)
    require consistent col
    ensures res.found = true →                                         -- C-found
      res.idx < col.size ∧ (col[res.idx]!).mathNonzero = true ∧
        (∀ j, j < res.idx → (col[j]!).mathNonzero = false)
    ensures res.found = false →                                        -- C-none
      (∀ j, j < col.size → (col[j]!).mathNonzero = false)

Each ``Entry`` carries two boolean observations of a scalar: ``litNonzero`` (the
cheap structural recogniser) and ``mathNonzero`` (the decisive recogniser). The
selection MUST rest on ``mathNonzero`` alone: report the FIRST index whose
decisive recogniser is set (``found=true``, ``idx`` that index, and every earlier
entry decisively zero), or ``found=false`` when the whole column is decisively
zero. The discriminating content the port defends:

  * C-found pins THREE things at once — the reported index is in range
    (``idx < col.size``), the chosen entry is decisively non-zero
    (``mathNonzero=true``, NOT merely structurally non-zero ``litNonzero``), and
    the reported index is the LOWEST such (every earlier entry decisively zero).
  * C-none pins that a ``found=false`` verdict is only legitimate when the ENTIRE
    column is decisively zero.

``consistent col`` (the ``require``) is the standing relationship
``mathNonzero → litNonzero`` on every entry — a value decisively non-zero cannot
be a literal zero. It is TRANSPARENT (a fully-unfolded ``def``, empty ``axioms``
region — no opaque answer key to echo, spec-guide directive 8), so the witnesses
below decide it directly.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its column is held at a fractional heap permission (``Acc(list_pred(col),
    1/2)``) an impl can illegally overwrite, so a rival that writes ``col[i]=0``
    is rejected for INSUFFICIENT PERMISSION regardless of value. Lean and Velvet
    are referentially transparent: ``col`` is an immutable ``Array Entry`` value,
    no parameter is declared ``mut``, there is no heap and no aliasing — so there
    is no read-only input to mutate and no substitute probe to build. Reported
    N/A in the footer; NOT fabricated.
  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. The nagini sibling
    ships NO ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, and this
    bundle runs under ``loom.semantics.termination "total"`` (a total-correctness
    bundle: the frozen loop carries a ``decreasing col.size - i`` measure). A
    Under ``total`` a postcondition is claimed of ALL runs, not only terminating ones,
    and the verifier demands a decreasing measure on every loop, so the class is
    CLOSED BY THE SEMANTICS - NOT a spec hole. A diverging impl CAN be written (a
    rival owns the whole impl region); it is REJECTED when it is, and the earlier
    wording "cannot even be written past the termination checker" is corrected on that
    point. Measured on this bundle with the proof reduced to a bare ``loom_solve``: an
    unmeasured spun loop is refused at elaboration (``Decreasing annotations are
    required in total correctness semantics``), and the sharper shape that CARRIES a
    measure which does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the measure's own
    goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. (The bullet used to cite
    an internal findings doc for a known-hole disposition scoped to "the 401
    ``partial`` bundles" against "the 99 ``total``" ones. That census is withdrawn:
    all 500 velvet bundles set ``"total"``.)
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is stated over the method's own
    ``col`` via the transparent ``mathNonzero`` field (empty ``axioms`` region),
    so the cheapest correct impl just scans for the first ``mathNonzero`` — done
    honestly by the positive controls; no wrong echo verifies.
  * PARTIAL-DOMAIN / VALUE / REGIME — the main class, ported below.

WITNESS MECHANICS. The frozen impl of ``selectPivot`` is a ``while`` loop whose
extracted program does NOT reduce under kernel ``decide`` (it compiles to
well-founded recursion through ``Classical.choice``). Every reject rival below is
therefore written LOOP-FREE (``Array.findIdx`` / ``List.foldl`` / a direct
return), so its extracted program reduces and ``selectPivotTester … = false``
decides.

The frozen solution therefore CANNOT serve as the discrimination subject, and
this is the one thing a reader must not take on trust. Re-measured with real
builds: every witness below, built against the frozen solution, fails with
``Tactic `decide` failed … did not reduce to `isTrue` or `isFalse` … reduction
got stuck at the `Decidable` instance``. That is a STUCK REDUCTION, not a
refutation — the kernel never evaluated the claim, so the same error appears for
a TRUE claim about the frozen impl and the gold-side exit code carries no
information whatsoever. An earlier revision of this file argued that "half 2
holds by construction" because gold fails to reduce; that argument is WRONG and
is retracted here, because it would equally bless a forged witness asserting the
rival is CORRECT at an agreement point.

Each reject case therefore names an explicit ``witness_reference``: ``_POS_FIRST``
(the ``pos-first-index`` positive), a LOOP-FREE impl of the same frozen spec
which is independently required to VERIFY and whose extracted program does
reduce. Against that subject each witness fails with ``Tactic `decide` proved
that the proposition … is false`` — a SEMANTIC refutation of the concrete claim,
which is the attestation this lane needs. This is sound for the reason the gate
records: an impl the verifier accepts cannot violate its own spec, so a genuine
"the spec is violated at this input" statement must fail there. Naming the
reference explicitly (rather than leaning on the gate's fallback-positive rescue)
is what makes the attribution a designed property of this battery instead of an
accident of manifest ordering. Each witness reaches the method contract through
Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``); it is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``consistent`` is not auto-synthesised Decidable, so
``prove_precondition_decidable_for`` is given an explicit
``by unfold consistent; infer_instance``; every ``Entry`` literal is fully
concrete (``Entry`` derives nothing extra but its two ``Bool`` fields are
``DecidableEq``), so ``decide`` settles the whole tester equality — no opaque
term, no conditioning, no head binders (hence no consistency obligation). Every
witness input satisfies ``consistent`` (each entry has ``mathNonzero → litNonzero``
by construction: no entry is ``⟨false,true⟩``), so none is vacuously excluded by
a false precondition. All witness builds (each witness against its own rival, and
against BOTH the frozen solution and the ``witness_reference``, plus all three
positives and the admissibility case) were re-run with ``scripts/lean_verify.sh``
during the audit; the exit codes are recorded in that audit's payload.

BINDER / CLAUSE COVERAGE. The single binder ``col`` is driven across SIX distinct
input points (pts=6). Both ``ensures`` clauses are attacked and defended:
  C-found → weak-structtruthy (middle conjunct: chosen entry decisively zero),
            weak-lastlive (third conjunct: an earlier entry live),
            weak-idx-offbyone (index shifted off the live entry),
            weak-len-sentinel (first conjunct: idx out of range);
  C-none  → weak-skipfirst (a live entry exists yet found=false),
            weak-allfalse (a live entry exists yet found=false).
The near-miss rivals do NOT share a witness with the whole-domain rivals: each is
refuted at a point that exercises exactly the sub-domain it abuses (structtruthy
at a lone structurally-nonzero-but-decisively-zero entry; skipfirst at a lone
index-0 live entry; lastlive at two live entries; idx-offbyone at a live-then-dead
pair; len-sentinel and allfalse at their own shapes).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the decisive
recogniser is modelled DEEPLY (the ``mathNonzero`` field) and its soundness
against the real (patched) callee is a G-AX/G-CONF concern (mapping.md §3). This
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13877"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL` is the COMPLETE impl body (both `-- impl-*` markers
# retained inside it), lies wholly inside the single impl region, and is unique
# in Solution.lean (both facts asserted at load by _swap). `_PROOF` is the frozen
# tactic body (elided from the consumer spec view, so a case may retune it
# without touching the spec or dropping the obligation). Anchoring on whole
# regions keeps every surgery inside the elided text — the `method` header, the
# `require`/`ensures` clauses, and the `pure`/`structure` regions are never
# touched, so `same_spec` holds for every case.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- impl-start\n"
    "    let mut i := 0\n"
    "    let mut found := false\n"
    "    let mut idx := 0\n"
    "    while i < col.size ∧ found = false\n"
    "      invariant 0 ≤ i ∧ i ≤ col.size\n"
    "      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)\n"
    "      invariant found = true →\n"
    "        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧\n"
    "          (∀ j, j < idx → (col[j]!).mathNonzero = false))\n"
    "      done_with (i = col.size ∨ found = true)\n"
    "      decreasing col.size - i\n"
    "    do\n"
    "      if (col[i]!).mathNonzero = true then\n"
    "        idx := i\n"
    "        found := true\n"
    "      i := i + 1\n"
    "    return ⟨found, idx⟩\n"
    "    -- impl-end"
)
_IMPL_START = "    -- impl-start\n"
_PROOF = "prove_correct selectPivot by\n  loom_solve"

for _s in (_IMPL, _IMPL_START, _PROOF):
    assert _BASE.count(_s) == 1, f"anchor drift / not unique: {_s[:40]!r}"


def _with_impl(body):
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _tester(call):
    """A refutation witness reaching the contract through Velvet's tester. The
    `require consistent col` is not auto-synthesised Decidable, so its
    decidability command is given an explicit unfold+infer_instance body."""
    return ("extract_program_for selectPivot\n"
            "prove_precondition_decidable_for selectPivot by\n"
            "  unfold consistent\n"
            "  infer_instance\n"
            "prove_postcondition_decidable_for selectPivot\n"
            "derive_tester_for selectPivot\n\n"
            f"example : {call} = false := by\n  decide\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Two are LOOP-FREE (a direct first-index scan, the
# maximally-different shape: no loop, no invariant) and one is a RESHAPED LOOP,
# so the spec is shown not to be over-fit either to the loop spelling or to the
# loop's presence. All verified with real builds.
#
# CORRECTION (audit): an earlier revision of this file asserted that the frozen
# `loom_solve` is "tightly coupled to the loop's exact spelling — even swapping
# the two assignments inside the `if`, or reordering the guard conjuncts, drops
# `loom_solve` to `sorry`", and used that measurement to justify carrying NO
# loop-shaped positive at all. That measurement is FALSE. Re-run with real
# builds, each of the following verifies (exit 0) with the frozen `loom_solve`
# retained verbatim and the frozen invariants kept:
#   * the two assignments inside the `if` swapped              -> exit 0
#   * the guard conjuncts reordered (`found = false ∧ i < …`)  -> exit 0
#   * the entry test hoisted into a `let live := …` local      -> exit 0
#   * all three of the above at once                           -> exit 0
# So the reject lane's loop-free requirement is a KERNEL-REDUCIBILITY need (see
# WITNESS MECHANICS), not a proof-fragility one, and there was never a reason to
# drop the loop-shaped structural control. `pos-loop-reshape` below restores it.
# ===========================================================================

# pos-first-index: the cheapest correct impl — the first index whose decisive
# recogniser is set, reported found iff such an index exists. Maps nagini
# `pos-cheapest` (materialise the grounded first-usable answer directly).
_POS_FIRST = _with_impl(
    "    let k := col.findIdx (fun e => e.mathNonzero)\n"
    "    return ⟨k < col.size, k⟩")

# pos-ifexpr: same first-index scan, but the found/idx result is assembled
# through an explicit `if … then ⟨true,k⟩ else ⟨false,0⟩` ladder (a different
# executable shape for the same value on every input). Maps nagini `pos-reorder`
# (structurally-different control flow, same forward scan).
_POS_IFEXPR = _with_impl(
    "    let k := col.findIdx (fun e => e.mathNonzero = true)\n"
    "    if k < col.size then\n"
    "      return ⟨true, k⟩\n"
    "    else\n"
    "      return ⟨false, 0⟩")

# pos-loop-reshape: the structural LOOP control the nagini `pos-reorder` actually
# calls for, restored after the audit disproved the "loop reshapes break
# loom_solve" claim above. Same forward scan and the frozen invariants verbatim,
# but three independent shape changes at once: the guard conjuncts are reordered,
# the entry test is hoisted into a local, and the two assignments inside the `if`
# are swapped. Verified with a real build (exit 0) under the frozen `loom_solve`.
# This is the control that pins the spec is not over-fit to the frozen loop's
# spelling — the loop-free positives cannot show that, since they discharge the
# clauses by a different route entirely.
_POS_LOOP = _with_impl(
    "    let mut i := 0\n"
    "    let mut found := false\n"
    "    let mut idx := 0\n"
    "    while found = false ∧ i < col.size\n"
    "      invariant 0 ≤ i ∧ i ≤ col.size\n"
    "      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)\n"
    "      invariant found = true →\n"
    "        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧\n"
    "          (∀ j, j < idx → (col[j]!).mathNonzero = false))\n"
    "      done_with (i = col.size ∨ found = true)\n"
    "      decreasing col.size - i\n"
    "    do\n"
    "      let live := (col[i]!).mathNonzero\n"
    "      if live = true then\n"
    "        found := true\n"
    "        idx := i\n"
    "      i := i + 1\n"
    "    return ⟨found, idx⟩")


# ===========================================================================
# ADMISSIBILITY (verify) — re-aimed from the nagini precondition-admission probe.
# The nagini sibling reads the half-permission column to show its `Requires` is
# satisfiable by an F2P-shaped input. Here the residual admissibility risk on a
# total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
# interesting point (a spec no impl can meet reads exactly like one every impl
# meets), AND that the `require consistent col` is jointly satisfiable with a
# genuine "structurally-nonzero-but-decisively-zero" entry — the exact
# discriminating shape the whole fix hinges on. An in-region `assert` at a
# concrete F2P-shaped column pins: (a) `consistent` holds of a column containing a
# pseudo-zero entry ⟨litNonzero:=true, mathNonzero:=false⟩ (so the interesting
# input IS in-domain), and (b) that entry's decisive recogniser really is false
# (so the post-image demands it be SKIPPED, not degenerate). The frozen impl and
# proof are kept verbatim so the method's own two obligations still discharge; the
# assert is live (a false variant — claiming that entry's mathNonzero=true —
# leaves an unsolved goal, verified during authoring).
# ===========================================================================
_ADMISS = _swap(
    _BASE, _IMPL_START,
    _IMPL_START +
    "    assert (with_name_prefix `admiss\n"
    "      (consistent (#[⟨true,true⟩,⟨true,false⟩] : Array Entry) ∧\n"
    "       (#[⟨true,true⟩,⟨true,false⟩] : Array Entry)[1]!.mathNonzero = false))\n")


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the frozen
# spec that MUST be rejected, each with a machine-checked refutation witness at a
# concrete input and the argument that its faithful real counterpart would NOT
# resolve the failing F2P test (test_determinant: M(5)/M(6)/M(7).det() == 0).
# ===========================================================================

# weak-structtruthy: THE reported bug class — decide on the cheap STRUCTURAL
# recogniser `litNonzero` instead of the decisive `mathNonzero`. On a
# structurally-nonzero-but-decisively-zero entry it selects that index where the
# spec demands skipping it.
_RIVAL_STRUCT = _with_impl(
    "    let k := col.findIdx (fun e => e.litNonzero)\n"
    "    return ⟨k < col.size, k⟩")

# weak-skipfirst: correct everywhere EXCEPT it never selects index 0 (the first
# entry is masked before the scan). On a column whose only live entry is at index
# 0 it reports found=false.
_RIVAL_SKIP = _with_impl(
    "    let masked := col.set! 0 ⟨false, false⟩\n"
    "    let k := masked.findIdx (fun e => e.mathNonzero)\n"
    "    return ⟨k < col.size, k⟩")

# weak-lastlive: reports the HIGHEST live index (scan for the last mathNonzero)
# rather than the lowest. On a multi-live column an earlier entry is live, so the
# "every earlier entry decisively zero" conjunct fails.
_RIVAL_LAST = _with_impl(
    "    let n := col.size\n"
    "    let r := (List.range n).foldl\n"
    "      (fun acc j => if (col[j]!).mathNonzero then j else acc) n\n"
    "    return ⟨r < n, r⟩")

# weak-allfalse: the degenerate "no pivot ever" rival — always reports
# found=false. Trivially correct on all-decisively-zero columns but wrong as soon
# as any entry is live.
_RIVAL_ALLFALSE = _with_impl(
    "    return ⟨false, 0⟩")

# weak-idx-offbyone: correct found flag and the correct SCAN, but reports the
# index one past the true first-live entry.
_RIVAL_OFFBYONE = _with_impl(
    "    let k := col.findIdx (fun e => e.mathNonzero)\n"
    "    return ⟨k < col.size, k + 1⟩")

# weak-len-sentinel: when a pivot exists, reports found=true but idx = col.size —
# an out-of-range sentinel. Violates the `idx < col.size` conjunct of C-found.
_RIVAL_LEN = _with_impl(
    "    let k := col.findIdx (fun e => e.mathNonzero)\n"
    "    if k < col.size then\n"
    "      return ⟨true, col.size⟩\n"
    "    else\n"
    "      return ⟨false, 0⟩")

# weak-halffix: ADDED by the audit (attack D — a tuned wrong impl the battery did
# not contain). The subtlest near-miss in this family and the one the existing
# rivals leave unattacked: locate the candidate with the CHEAP structural
# recogniser, then gate it on the decisive one, reporting no pivot when the gate
# fails. It agrees with the frozen behaviour on every column whose first
# structurally-nonzero entry is also decisively nonzero — so every other rival's
# witness point except structtruthy's is an AGREEMENT point for it — yet it is
# wrong exactly on the shape the whole fix is about: a leading
# structurally-nonzero-but-decisively-zero entry followed by a genuinely live one.
# It stops at the pseudo-zero, fails its own gate, and reports found=false while a
# live entry exists further down. This probes whether C-none pins the WHOLE-column
# obligation rather than merely "the first structural candidate failed".
_RIVAL_HALFFIX = _with_impl(
    "    let k := col.findIdx (fun e => e.litNonzero)\n"
    "    if k < col.size ∧ (col[k]!).mathNonzero = true then\n"
    "      return ⟨true, k⟩\n"
    "    else\n"
    "      return ⟨false, 0⟩")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-first-index",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FIRST,
        "rationale": "the cheapest correct impl — report the first index whose "
                     "decisive recogniser is set, found iff such an index exists. "
                     "A maximally-different shape (no loop, no invariant) that is "
                     "observationally identical on every input, so both `ensures` "
                     "clauses discharge; a correct reshape MUST verify (else the "
                     "postcondition is over-fit to the loop spelling => "
                     "SPEC-TOO-STRONG). Maps nagini pos-cheapest. Proof: frozen "
                     "`loom_solve` retained. This module is also the "
                     "`witness_reference` every reject case is refuted against: "
                     "it is loop-free, so its extracted program REDUCES in the "
                     "kernel, which the frozen loop-based impl does not.",
    },
    {
        "id": "pos-ifexpr",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_IFEXPR,
        "rationale": "same forward first-index scan, but the found/idx result is "
                     "assembled through an explicit if-ladder — a different "
                     "executable control-flow shape for the same value on every "
                     "input, so both clauses still hold. Transliterates nagini "
                     "pos-reorder (structurally-different control flow, forward "
                     "scan). Loop reshapes were measured to break the frozen "
                     "`loom_solve`, so the structural difference is carried by a "
                     "loop-free shape instead. Must verify.",
    },
    {
        "id": "pos-loop-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOOP,
        "rationale": "the structural LOOP control: same forward scan and the "
                     "frozen invariants verbatim, but three independent shape "
                     "changes at once — guard conjuncts reordered, the entry test "
                     "hoisted into a local, and the two assignments inside the "
                     "`if` swapped. This is what nagini pos-reorder actually asks "
                     "for (a structurally-different LOOP), and it is the only "
                     "control that can show the spec is not over-fit to the frozen "
                     "loop's SPELLING — the loop-free positives discharge the "
                     "clauses by a different route and so cannot speak to that. "
                     "Restored by the audit: the claim that such reshapes drop "
                     "`loom_solve` to `sorry` was re-measured and is false (this "
                     "module verifies, exit 0, with `loom_solve` unchanged). Must "
                     "verify, else SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must VERIFY; else PRECOND-TOO-STRONG / degenerate) ----
    {
        "id": "admiss-pseudozero-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the `require consistent col` is jointly satisfiable with the "
                     "exact discriminating shape the fix hinges on — a column "
                     "containing a structurally-nonzero-but-decisively-zero entry "
                     "⟨litNonzero:=true, mathNonzero:=false⟩ — and the post-image "
                     "is non-degenerate there: it demands that entry be SKIPPED "
                     "(its mathNonzero really is false). The in-region assert pins "
                     "both facts and must discharge (else the modeled behaviour is "
                     "degenerate / the precondition excludes the interesting input "
                     "=> PRECOND-TOO-STRONG); the frozen impl and proof are kept "
                     "verbatim so the method's own two obligations discharge too. "
                     "Nothing is assumed: no new declaration, the obligation "
                     "statement is unchanged, and the assert is a live goal (a "
                     "false variant claiming that entry's mathNonzero=true leaves "
                     "it unsolved).",
    },

    # ---- uniqueness rivals (must be REJECTED, each with a discriminating witness) ----
    {
        "id": "weak-structtruthy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_STRUCT,
        "refinement": "THE pre-fix bug: the selection decides on the cheap "
                      "structural recogniser (`litNonzero`) instead of the "
                      "decisive one. A faithful real patch that kept the structural "
                      "test would accept a value that only LOOKS non-zero but "
                      "normalises to zero as a pivot, then divide by it on the "
                      "singular M(5)/M(6)/M(7) columns — the 'Invalid NaN "
                      "comparison' / nan the issue reports — so det() does NOT "
                      "equal 0 and test_determinant still FAILS. A verifying rival "
                      "here would be a true verify-without-resolve break.",
        "rationale": "REJECT from C-found's middle conjunct "
                     "((col[res.idx]!).mathNonzero = true): on a lone entry that is "
                     "structurally non-zero yet decisively zero this returns "
                     "idx=0 with found=true, but that entry's mathNonzero is false, "
                     "so the clause cannot discharge. Verifying would be "
                     "SPEC-TOO-WEAK (admits the structural-recogniser regression). "
                     "Refuted at col = #[⟨true,false⟩] — the pseudo-zero shape, "
                     "which no other rival's witness uses.",
        "witness": _tester(
            "selectPivotTester (#[⟨true,false⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-skipfirst",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SKIP,
        "refinement": "correct on every column whose first live entry is at index "
                      ">= 1, but it never selects index 0. A faithful patch that "
                      "started the pivot search at row 1 would report no usable "
                      "pivot (or the wrong one) whenever the top entry is the "
                      "genuine non-zero one — a different Bareiss pivot row, a "
                      "different elimination, the wrong determinant on the failing "
                      "matrices, so it would NOT resolve.",
        "rationale": "REJECT from C-none (res.found = false → every entry decisively "
                     "zero): on col = #[⟨true,true⟩] the sole entry is decisively "
                     "non-zero, yet this rival masks index 0 and reports "
                     "found=false, contradicting C-none. Verifying would leave the "
                     "index-0 sub-domain unpinned (partial-domain SPEC-TOO-WEAK). "
                     "Refuted at a lone index-0 live entry — the regime where the "
                     "whole-domain rivals agree with gold.",
        "witness": _tester(
            "selectPivotTester (#[⟨true,true⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-lastlive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LAST,
        "refinement": "reports the HIGHEST live index instead of the lowest. A "
                      "faithful patch picking the last non-zero row as the Bareiss "
                      "pivot changes the elimination order and yields a different / "
                      "wrong determinant on the multi-live matrices (the algorithm "
                      "is specified for the lowest valid pivot), so it would NOT "
                      "resolve.",
        "rationale": "REJECT from C-found's third conjunct "
                     "(∀ j < res.idx, (col[j]!).mathNonzero = false): on "
                     "col = #[⟨true,true⟩,⟨true,true⟩] this returns idx=1, but "
                     "index 0 is decisively non-zero, so an earlier entry is live "
                     "and the clause fails. Verifying would be SPEC-TOO-WEAK (the "
                     "lowest-index requirement unenforced). Refuted at two live "
                     "entries — a point no near-miss rival probes.",
        "witness": _tester(
            "selectPivotTester (#[⟨true,true⟩,⟨true,true⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-allfalse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALLFALSE,
        "refinement": "always reports 'no pivot'. A faithful patch returning "
                      "S.Zero for every minor would make EVERY determinant 0, "
                      "including the non-singular matrices test_determinant also "
                      "asserts, so it fails the test suite — does not resolve.",
        "rationale": "REJECT from C-none (res.found = false → every entry decisively "
                     "zero): on col = #[⟨false,false⟩,⟨false,false⟩,⟨true,true⟩] a "
                     "live entry exists at index 2, yet this reports found=false, "
                     "contradicting C-none. Supporting degenerate case with a real "
                     "refinement. Refuted at a 3-entry column with the live entry "
                     "LAST — a distinct point from weak-skipfirst's lone index-0 "
                     "live entry.",
        "witness": _tester(
            "selectPivotTester (#[⟨false,false⟩,⟨false,false⟩,⟨true,true⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-idx-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OFFBYONE,
        "refinement": "the found flag and the scan are correct, but the reported "
                      "index is shifted one past the true first-live entry. A "
                      "faithful patch reporting pivot_offset+1 would eliminate on "
                      "the wrong row, changing the determinant on the failing "
                      "matrices — it would NOT resolve.",
        "rationale": "REJECT from C-found (res.idx = pivot must satisfy "
                     "(col[res.idx]!).mathNonzero = true AND every earlier entry "
                     "decisively zero): on col = #[⟨true,true⟩,⟨false,false⟩] the "
                     "true pivot is index 0, but this returns idx=1, whose "
                     "mathNonzero is false, and index 0 (< 1) is live. Verifying "
                     "would leave the exact index unpinned (SPEC-TOO-WEAK). Refuted "
                     "at a live-then-dead pair — its own discriminating point.",
        "witness": _tester(
            "selectPivotTester (#[⟨true,true⟩,⟨false,false⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-len-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEN,
        "refinement": "reports found=true with idx = col.size — an out-of-range "
                      "sentinel — when a pivot exists. A faithful patch comparing "
                      "pivot_offset against the wrong out-of-range sentinel would "
                      "mis-handle the pivot branch, so the singular minors would "
                      "not contribute correctly — not resolving.",
        "rationale": "REJECT from C-found's first conjunct (res.idx < col.size): on "
                     "col = #[⟨true,true⟩,⟨false,false⟩,⟨false,false⟩] this returns "
                     "found=true with idx=3 = col.size, which is out of range, so "
                     "the range conjunct fails (and col[3]! is off the end). "
                     "Verifying would leave the range clause unenforced "
                     "(SPEC-TOO-WEAK). Refuted at a 3-entry column with a single "
                     "leading live entry — its own point.",
        "witness": _tester(
            "selectPivotTester (#[⟨true,true⟩,⟨false,false⟩,⟨false,false⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
    {
        "id": "weak-halffix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_HALFFIX,
        "refinement": "the half-done fix: locate the candidate with the cheap "
                      "structural recogniser, then gate it on the decisive one and "
                      "report no pivot if the gate fails. A faithful patch of this "
                      "shape stops at the first structurally-nonzero entry and, "
                      "when that entry normalises to zero, declares the minor "
                      "singular WITHOUT looking further down the column — so a "
                      "genuinely usable pivot below it is never found, the "
                      "elimination is skipped, and the singular matrices get the "
                      "wrong determinant. It does not resolve, and unlike "
                      "weak-structtruthy it does not even divide by a pseudo-zero, "
                      "so the crash-shaped symptom is absent while the answer is "
                      "still wrong.",
        "rationale": "REJECT from C-none (res.found = false → every entry decisively "
                     "zero): on col = #[⟨true,false⟩,⟨true,true⟩] the structural "
                     "scan stops at index 0, whose decisive recogniser is false, so "
                     "the gate fails and this reports found=false — yet index 1 is "
                     "decisively non-zero, contradicting C-none. ADDED by the audit "
                     "(attack D): this is the near-miss the other rivals leave "
                     "unattacked, because it AGREES with the frozen behaviour at "
                     "every one of their witness points except structtruthy's. It "
                     "probes that C-none pins the whole-column obligation rather "
                     "than merely 'the first structural candidate failed its gate'. "
                     "Refuted at a pseudo-zero FOLLOWED BY a live entry — a "
                     "two-entry shape no other case uses (structtruthy's point is "
                     "the lone pseudo-zero; idx-offbyone's is live-then-dead, the "
                     "mirror image of this one).",
        "witness": _tester(
            "selectPivotTester (#[⟨true,false⟩,⟨true,true⟩] : Array Entry)"),
        "witness_reference": _POS_FIRST,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation, 5 uniqueness rivals)
# plus 2 AXIOM_TESTS. The Lean-family bundle models the purely functional
# pivot-selection core as a SINGLE method (`selectPivot`, one `prove_correct`),
# so the carrier narrows and the permission machinery falls away.
#
#   sibling case               -> here
#   ---------------------------------------------------------------------
#   pos-cheapest               -> pos-first-index                 PORTED
#   pos-reorder                -> pos-ifexpr                      PORTED (loop-free)
#                                 + pos-loop-reshape              RESTORED (audit)
#   admiss-1                   -> admiss-pseudozero-in-domain     RE-AIMED
#   frame-mutate               -> (none)                          VACUOUS
#   weak-structtruthy          -> weak-structtruthy              PORTED
#   weak-skipfirst             -> weak-skipfirst                 PORTED
#   weak-lastlive              -> weak-lastlive                  PORTED
#   weak-alwaysminusone        -> weak-allfalse                  PORTED
#   weak-offbyone-sentinel     -> weak-len-sentinel              PORTED
#                                 (+ weak-idx-offbyone            ADDED)
#                                 (+ weak-halffix                 ADDED, audit)
#   ax-* (AXIOM_TESTS)         -> (none)                          DROPPED (G-AX lane)
#
# 3 positives (2 ported + 1 restored), 1 admissibility re-aimed, 5 rivals ported,
# 2 rivals added, 1 frame-mutation vacuous, 2 axiom-lane dropped = 11 SPEC cases.
#
# PORTED + RESTORED (pos-reorder -> pos-ifexpr AND pos-loop-reshape). The nagini
#   pos-reorder is a structurally-different LOOP variant. An earlier revision
#   carried only the loop-free pos-ifexpr, on the stated measurement that the
#   frozen `loom_solve` is "tightly coupled to the loop's exact spelling: swapping
#   the two assignments inside the `if`, reordering the guard conjuncts, or binding
#   the entry into a local all drop `loom_solve` to `sorry`". The audit re-ran
#   exactly those three reshapes as real builds: each verifies (exit 0) with
#   `loom_solve` unchanged, as does all three applied at once. The measurement was
#   wrong, so the loop-shaped control is restored as `pos-loop-reshape` and the
#   claim is retracted. Both shapes are now carried: the loop-free positives probe
#   a maximally-different route to the clauses, and the loop positive probes that
#   the spec is not over-fit to the frozen loop's spelling. Note the reject lane's
#   loop-freeness is a separate and still-valid requirement — it is about KERNEL
#   REDUCIBILITY for the witness `decide`, not about proof fragility.
# RE-AIMED (admissibility): the nagini probe re-reads the half-permission column
#   to show its Requires admits an F2P-shaped input. `selectPivot`'s only
#   precondition is `consistent col`; the re-aimed case pins that `consistent` is
#   jointly satisfiable with the discriminating pseudo-zero entry AND that the
#   post-image is non-degenerate there (that entry must be skipped) — the residual
#   admissibility risk on a total domain.
# ADDED (weak-idx-offbyone): the velvet C-found clause pins the EXACT index (a
#   three-way conjunction), where nagini's P1/P3 split range and value across
#   separate clauses. weak-len-sentinel attacks the range conjunct; weak-idx-
#   offbyone attacks the value/lowest conjunct with an in-range but wrong index,
#   so both independent facets of C-found are exercised.
# ADDED (weak-halffix, audit attack D): a tuned wrong impl aimed at what the
#   ported rivals leave unattacked — gate the cheap structural candidate on the
#   decisive recogniser and give up if it fails, instead of continuing the scan.
#   It agrees with the frozen behaviour at every other rival's witness point but
#   one, and is wrong exactly on a pseudo-zero followed by a live entry. Confirmed
#   rejected with a discriminating witness (see witnesses list). Three further
#   tuned rivals were probed and all rejected: always-found (found=true even on an
#   all-dead column), always-idx-0 (correct flag, index pinned to 0), and
#   structural-flag-with-decisive-index (the two recognisers crossed). None
#   verified, so no spec hole was found on the C-found/C-none surface.
# VACUOUS (frame-mutate): the nagini sibling writes col[i]=0 to a column held at a
#   fractional heap permission (Acc(list_pred(col),1/2)) and is rejected for
#   INSUFFICIENT PERMISSION before any value reasoning. Lean/Velvet are
#   referentially transparent: `col` is an immutable Array Entry value, no
#   parameter is `mut`, there is no heap and no aliasing — no read-only input to
#   overwrite and no permission system to trip. No expressible instance; no
#   substitute fabricated (per the porting map, this class is genuinely vacuous
#   here). DEMONSTRATED by the audit rather than asserted: an impl that assigns to
#   the input binder (`col := col.set! i ⟨false,false⟩`) does not merely fail the
#   contract, it fails to ELABORATE — "`col` cannot be mutated, only variables
#   declared using `let mut` can be mutated" — so there is no rival to build; and
#   adding `mut` to the binder is not available either, since it changes the method
#   header and so the spec view (mechanically: same_spec fails), which puts it out
#   of variant scope by construction.
# DIVERGENCE / NON-TERMINATION lane: the nagini sibling ships NONE, and this bundle
#   runs under termination "total" (the frozen loop carries a `decreasing`
#   measure), so a diverging rival is REJECTED rather than vacuously admitted -- the
#   class is CLOSED BY THE SEMANTICS, not a spec hole. (The earlier version of this
#   note cited an internal findings doc whose known-hole disposition it scoped to "the
#   `partial` bundles"; that cohort is withdrawn, since all 500 velvet bundles now
#   read "total". It also said a diverging impl "cannot be written past the
#   termination checker": it can be written, and a loop CARRYING a non-decreasing
#   measure (`while q > 0 ... decreasing q`, body `q := q`) is rejected on the
#   measure's own goal -- `case «decreasing_1: q»`, residual `q < q`.) CONFIRMED with
#   a real build: an unmeasured `while found = false do i := i + 1` rival is
#   refused at elaboration — "Decreasing annotations are required in total
#   correctness semantics" — and its obligation collapses to `sorry`, which the
#   variant-scope screen bans outright. So the diverging impl cannot verify here,
#   vacuously or otherwise.
# DROPPED (ax-*): the sibling's two AXIOM_TESTS probe the deep-model recogniser's
#   soundness/containment against the real callee. This bundle has NO consumed
#   axiom (mapping.md §3: the decisive recogniser is modelled deeply via the
#   `mathNonzero` field); the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single binder `col` is driven across SEVEN distinct
#   input points. C-found is attacked by weak-structtruthy (middle conjunct),
#   weak-lastlive (third conjunct), weak-idx-offbyone (value/lowest),
#   weak-len-sentinel (range conjunct); C-none by weak-skipfirst, weak-allfalse and
#   weak-halffix. Both clauses are defended by the three positives and the
#   admissibility case. No two rivals share a witness: each near-miss is refuted at
#   the input that exercises exactly its sub-domain (structtruthy at a lone
#   pseudo-zero; skipfirst at a lone index-0 live entry; lastlive at two live
#   entries; allfalse at a 3-entry column with the live entry last; idx-offbyone at
#   a live-then-dead pair; len-sentinel at a single leading live entry in a 3-entry
#   column; halffix at a pseudo-zero followed by a live entry). The variation is
#   MEANINGFUL and not two spellings of one point: each of the seven columns changes
#   the spec's own verdict about what must be returned (found/idx differ, or the
#   same answer is reached only by honouring a different clause).
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
