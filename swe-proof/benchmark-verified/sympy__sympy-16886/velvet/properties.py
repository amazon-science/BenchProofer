"""properties.py — G-PBT falsification battery for sympy__sympy-16886 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct encodeWord``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against a subject known to satisfy the spec.

THE DISCRIMINATION SUBJECT IS NOT THE FROZEN SOLUTION HERE, and the manifest
says so rather than leaving it to a gate fallback. The frozen impl is a ``while``
loop, which under ``loom.semantics.choice "demonic"`` elaborates through
``Classical.choice``; the kernel cannot unfold that, so ``decide`` on the frozen
tester is STUCK for every claim regardless of truth. Measured, all three reject
witnesses built against the frozen solution: exit 1 with ``Tactic `decide`
failed ... did not reduce to `isTrue` or `isFalse` ... reduction got stuck at the
`Decidable` instance``. That exit code attests to nothing (a TRUE claim about the
frozen impl fails identically), so each reject case names an explicit
``witness_reference``: the loop-free ``word.map codeOf`` impl of this same frozen
spec, which the gate independently checks SHARES the spec and VERIFIES before
refuting the witness against it. An impl the verifier accepts cannot violate its
own spec, so a genuine witness must still fail there — and against that subject
each witness fails SEMANTICALLY (``Tactic `decide` proved that the proposition
... is false``), which is a real refutation of the concrete claim.

DEFENDED SURFACE (one contracted method):

  encodeWord (word : List Char) return (out : List (List Char))
    ensures out = codesOf word

``codesOf`` is a front-recursive spec fold: it renders a source-symbol sequence
into the per-symbol code sequences, in source order, one code sequence per
symbol (``codesOf (c :: cs) = codeOf c :: codesOf cs``). ``codeOf`` is the frozen
per-symbol code table (a ``pure`` ``def``, NOT the impl — it is elided from the
impl region and is part of the frozen spec view). The single load-bearing
``ensures`` pins ``out`` to ``codesOf word``: every symbol's code sequence must
be produced, in order, from the table — none dropped, none replaced by a wrong
code. The discriminating content of the fix lives in one table entry: the code
for the source symbol ``'1'`` is the canonical five-signal sequence, not the
four-signal sequence the base table carried; a rival that emits the four-signal
code for ``'1'`` produces a different ``out`` and cannot equal ``codesOf word``.

ONE INPUT BINDER, free: ``word : List Char`` (the source-symbol sequence). The
reject witnesses vary ``word`` across a single-symbol vector (probing the table
entry at one position) and a two-symbol vector (probing the ordered traversal),
and across the symbols the F2P behaviour exercises — the corrected symbol
``'1'``, the all-dash symbol ``'0'``, and a two-symbol prefix. A battery that
pinned ``word`` to one shape would let a rival that mishandled only another
symbol or only a longer sequence slip past.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``encodeWordTester word = false`` says the extracted
program's result violates the postcondition at that concrete input) and closes
by ``decide``, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. ``decide`` reduces the extracted
program by kernel computation; a program shaped as a ``while`` loop over the
symbol stream does NOT reduce to ``isTrue``/``isFalse`` (the loop's fixpoint is
opaque to the kernel). So each reject rival is expressed as a LOOP-FREE impl
that computes its (wrong) value directly (``word.map`` / a length-guarded drop)
— still a wrong implementation sharing the frozen spec, but one whose extracted
tester ``decide``s. This is a witnessing convenience, not a weakening: the
frozen spec is untouched and each rival's divergence from ``codesOf`` is real at
the witnessed input. (The table ``codeOf`` is a concrete ``def`` over ``Char``
literals, so ``decide`` reduces it — no conditioning on an opaque callee is
needed here.)

The SAME boundary applies to the OTHER side of the discrimination check, which
is why every reject case carries a ``witness_reference``: the frozen impl's loop
is exactly the term the kernel cannot reduce, so it cannot serve as the subject
a witness is refuted against. See the module preamble above for the measured
build outcomes. The reference is loop-free and reduces, so the refutation there
is a decided verdict rather than a stuck one.

ADVERSARIAL READ of the weakness classes (others justified-N/A below):
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's mandatory
    frame-mutation rival writes to a read-only container held at a fractional
    heap permission (``Acc(list_pred(msg), 1/2)``) and is rejected for
    INSUFFICIENT PERMISSION before any value reasoning. This backend is
    referentially transparent: ``word`` is an immutable ``List Char`` value, the
    method declares no ``mut`` binder among its inputs, and there is no heap and
    no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated (per the
    porting map, dropped rather than replaced).
  * TABLE-VALUE / PARTIAL-DOMAIN — APPLIES, and carries the reject lane: the
    single clause pins the per-symbol code on EVERY position, so a rival that
    emits a wrong code for one symbol — the corrected ``'1'`` (the exact
    discriminator the fix introduces), or the all-dash ``'0'`` (a wrong but
    same-length code) — diverges from ``codesOf`` at that symbol.
  * STRUCTURE / TRAVERSAL — APPLIES: a rival that skips the first symbol of a
    multi-symbol sequence returns ``codesOf`` of the tail, not of ``word``, so it
    disagrees on any sequence of length ≥ 2 while agreeing on a single symbol.
  * SEPARATOR / JOIN — NOT MODELED here, so its rival is DROPPED (not vacuous —
    genuinely outside the modeled surface). ``encodeWord`` produces only the
    per-symbol code sequences ``List (List Char)``; the single-signal join
    between codes is an UNCHANGED concrete op transliterated in the conformance
    shadow (mapping.md §2, the ``sep``-join row), not part of this spec. There is
    no separator binder to abuse, so the sibling's wrong-separator rival has no
    counterpart on this carrier.
  * UNGROUNDED-ORACLE ECHO — N/A. ``codesOf`` is a fully unfolded ``def`` over
    the method's own argument (front-recursion into the concrete ``codeOf``
    table; the ``axioms`` region is empty — no opaque answer key to echo). The
    only way to satisfy the postcondition is to build the correct per-symbol
    codes, which the positive controls do honestly.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS PLACEMENT / coverage. The five reject witnesses sit at five DISTINCT
input points and move the ``word`` binder across the empty, one-symbol and
two-symbol vectors and across five symbols (``'1'``, ``'0'``, the ``'2','3'``
prefix, and the asymmetric ``'1','0'`` pair). The digit-``'1'`` and digit-``'0'``
rivals do NOT share a witness: each is correct on the other's symbol, so each
carries the input at which it alone diverges. The skip-first rival is correct on
a single symbol and needs a length-2 input, which no value rival exercises.
pts=5.

The last two rivals were added by AUDIT, closing sub-domains the ported battery
asserted in prose but never demonstrated:
  * ORDER. The value rivals pin per-symbol codes and the skip-first rival pins
    length, but a rival that keeps every code exactly once and merely PERMUTES
    them was unattacked. ``reject-reversed-order`` refutes at ``['1','0']``.
  * THE EMPTY SEQUENCE. Every original witness sat at a non-empty ``word``, so
    the ``codesOf [] = []`` base case of the front-recursion was never probed.
    ``reject-nonempty-on-empty`` refutes at ``[]``.
Both were built and measured before being written down; neither is a spec hole
(the frozen clause rejects both, as it should).

SPEC-STRENGTH PROBES RUN BY AUDIT, and what they measured. Four NEW correct
reshapes of a different shape were built to look for a SPEC-TOO-STRONG hole, and
all four VERIFY against the frozen spec: ``word.foldr (fun c acc => codeOf c ::
acc) []``; ``word.attach.map (fun p => codeOf p.val)``; ``(List.range
word.length).map (fun k => codeOf word[k]!)``; and a forward accumulation
reversed at the end, ``(word.foldl (fun acc c => codeOf c :: acc) []).reverse``.
So the clause is not over-fit to the frozen fold's executable form — it admits
front-recursive, index-driven, and reverse-accumulating shapes alike. A fifth,
``return codesOf word``, also verifies, and that is correct rather than an echo
hole: ``codesOf`` is a fully unfolded ``def`` over the method's OWN argument, so
naming it IS performing the per-symbol expansion (there is no opaque oracle to
echo — the ``axioms`` region is empty).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16886"
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
# -- impl-end). Replaced wholesale by the structure/value rivals and by the
# map-based positive control, which abandon the loop entirely (so the extracted
# tester `decide`s — see CARRIER NOTE).
_IMPL = (
    "    let mut result : List (List Char) := []\n"
    "    let mut i := word.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ word.length\n"
    "      invariant result = codesOf (word.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := word[i - 1]!\n"
    "      result := codeOf c :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "impl-body anchor drift — re-sync _IMPL"

# The single loop-body prepend line, wholly inside the impl region and unique.
# The local-reshape positive control names the per-symbol code in a `let e`
# before prepending, leaving the loop, invariants and frozen proof script
# intact.
_PREPEND = "      result := codeOf c :: result\n"
assert _BASE.count(_PREPEND) == 1, "prepend-line anchor drift"

# The impl-start marker line (unique); the admissibility case inserts an
# in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only; elided from the spec view, so a
# rival that reshapes the impl into a single expression, or the admissibility
# case that adds an in-region assert, may retune it without touching the spec or
# dropping the `prove_correct encodeWord` obligation).
_PROOF_GOLD = (
    "prove_correct encodeWord by\n"
    "  loom_solve\n"
    "  rw [codesOf_drop_step word i (by omega) (by omega)]\n"
    "  simp_all\n"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A loop-free proof body: when the impl is a single expression there is no loop
# invariant to peel, so `loom_solve` alone discharges the goal (or leaves one —
# for the reject rivals it FAILS, which is the point). Reject rivals retune the
# proof to this shape so the rejection is attributable to the spec (the
# witness), not to a proof script tuned to a loop that no longer exists.
_PROOF_FLAT = "prove_correct encodeWord by\n  loom_solve\n"

# ---- the discrimination SUBJECT for every reject case ----------------------
# A loop-free, KERNEL-REDUCIBLE impl of the frozen spec, reproven by induction on
# `word`. Named here (rather than left to the gate's fallback search) because the
# frozen `while` impl cannot decide any claim: see the module preamble. The gate
# re-checks both required properties itself — it shares the frozen spec, and it
# VERIFIES — before refuting any witness against it, so nothing here is trusted
# on the manifest's word. It is the same source as the `pos-map-structural`
# positive control, which is independently required to verify for this battery to
# pass at all.
_REFERENCE = _swap(
    _swap(_BASE, _IMPL, "    return word.map codeOf\n"),
    _PROOF_GOLD,
    "prove_correct encodeWord by\n"
    "  loom_solve\n"
    "  induction word with\n"
    "  | nil => rfl\n"
    "  | cons c cs ih => simp [List.map, codesOf_cons, ih]\n")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `encodeWordTester word = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every argument is a
# ---- concrete `Char` literal list so `decide` reduces the (loop-free) extracted
# ---- program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for encodeWord\n"
            "prove_precondition_decidable_for encodeWord\n"
            "prove_postcondition_decidable_for encodeWord\n"
            "derive_tester_for encodeWord\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that MUST verify. Abandons the backward `while` fold entirely for a single
    # `word.map codeOf` expression, reproven from scratch by induction on `word`
    # (no reuse of the frozen drop-step lemma). Observationally identical to gold
    # on every input. If a faithful correct impl of a different SHAPE cannot
    # verify, the spec is SPEC-TOO-STRONG (over-fit to the fold form).
    # =====================================================================
    {
        "id": "pos-map-structural",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": (
            "structurally-different but CORRECT impl: emits the per-symbol codes "
            "via `word.map codeOf` instead of the backward `while` fold, reproven "
            "by induction on `word` (the frozen drop-step lemma is not used). "
            "`out = codesOf word` holds on the whole domain (`map codeOf = "
            "codesOf` by front-recursion). If this fails to verify, the "
            "postcondition is over-fit to the fold's executable form => "
            "SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a local data-flow reshape that keeps the
    # loop, the invariants and the frozen proof script. The per-symbol code is
    # named in a local `let e` before the prepend; the accumulated `result` is
    # definitionally identical, so `loom_solve` leaves the same single loop-body
    # goal and the frozen tactic script closes it unchanged. If it fails, the
    # spec is over-fit to the inlined-prepend form => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _PREPEND,
            "      let e := codeOf c\n"
            "      result := e :: result\n"),
        "rationale": (
            "naming the per-symbol code in a local `let e` before the prepend "
            "accumulates the same `result`, so `out = codesOf word` still holds; "
            "the loop, invariants and frozen proof script are untouched. A "
            "correct reshape that failed to verify would mean the spec is "
            "SPEC-TOO-STRONG on the impl's data-flow shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous (nothing could
    # exclude an F2P-shaped input; the sibling's default-separator admissibility
    # has no precondition to defend here, and the separator is not modeled). The
    # residual admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point. This case discharges an
    # in-region `assert` that the post-image for the corrected symbol is
    # non-degenerate: `codesOf ['1']` is the one-element list holding the
    # canonical five-signal code — i.e. the fix's datum is genuinely counted, not
    # collapsed. The impl is kept verbatim so the method's own obligation still
    # discharges; the proof is retuned only to clear the extra assert goal by
    # `decide` (allowed — the tactic body is elided from the spec view). A false
    # claim about that point would leave an unsolved goal.
    #
    # AUDIT: measured load-bearing rather than assumed. Flipping the asserted
    # value to the pre-fix four-signal code, with the proof script otherwise
    # unchanged, FAILS (exit 1) with `Tactic `decide` proved that the proposition
    # codesOf ['1'] = ["----".toList] is false` — so the assert genuinely
    # discharges a claim about the table's content and is not clearable by any
    # true-of-anything route.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (codesOf ['1'] = [\".----\".toList]))\n"),
            _PROOF_GOLD,
            "prove_correct encodeWord by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [codesOf_drop_step word i (by omega) (by omega)]; simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "symbol: `codesOf ['1']` is the singleton list carrying the canonical "
            "five-signal code, so the corrected table datum is genuinely produced "
            "rather than dropped or collapsed. The in-region assert must discharge "
            "(else the obligation is unsatisfiable / degenerate at the point the "
            "fix cares about); the impl is kept verbatim so the method's own "
            "`ensures` still discharges. If it could not, PRECOND/POST-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete input
    # and the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test. Each rival is LOOP-FREE (single expression) so its
    # extracted tester `decide`s (see CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "reject-symbol1-four-dash",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the four-signal (all-dash) code for the source symbol '1' — the
        # pre-fix table entry — and the correct code for every other symbol. This
        # is the EXACT discriminator the fix introduces. Attacks the value clause
        # at that one symbol.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return word.map (fun c => if c = '1' then \"----\".toList else codeOf c)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "returns the four-signal all-dash code for the source symbol '1' — the "
            "code the base table assigned before the fix — and is correct on every "
            "other symbol. Its faithful real counterpart is the unfixed table "
            "entry: under it a request containing '1' renders the four-signal code "
            "where the corrected output demands the canonical five-signal code, so "
            "the F2P assertion that pins the rendered string for a sequence "
            "beginning with '1' FAILS. This is precisely the bug the patch fixes — "
            "it would NOT resolve."),
        "rationale": (
            "REJECT from `out = codesOf word`: the frozen `codeOf '1'` is the "
            "five-signal code, so a four-signal result is the wrong length (4 ≠ 5) "
            "AND the wrong value at that symbol, and the two disagree wherever '1' "
            "appears. Verifying would be SPEC-TOO-WEAK (admits the pre-fix bug). "
            "Refuted at word=['1']."),
        "witness": _tester(
            "example : encodeWordTester (['1'] : List Char) = false := by\n"
            "  decide\n"),
        # Measured: rival exit 0; reference exit 1 with `Tactic `decide` proved
        # that the proposition encodeWordTester ['1'] = false is false` — a
        # SEMANTIC refutation. Discrimination is input-specific, not a blanket
        # breakage: the same witness moved to word=['5'] (where this rival is
        # correct) FAILS against the rival, and the OPPOSITE claim (`= true`,
        # i.e. the rival is right at '1') also fails against the rival while
        # succeeding against the reference.
        "witness_reference": _REFERENCE,
    },
    {
        "id": "reject-wrong-symbol0",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit a WRONG but same-length five-signal code for '0' (the code of '4')
        # instead of the all-dash code; correct on every other symbol. Targets the
        # value clause on a symbol where a LENGTH-only check would pass. Correct on
        # '1', so it does not share the symbol-1 rival's witness.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return word.map (fun c => if c = '0' then \"....-\".toList else codeOf c)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "returns a wrong but same-length five-signal code for the source "
            "symbol '0' (the code of '4') instead of the all-dash code; correct on "
            "every other symbol. Its faithful real counterpart is a table whose "
            "'0' entry is wrong; under it a request ending in '0' renders the wrong "
            "five-signal code, so the F2P assertion that pins the rendered string "
            "for a sequence ending in '0' FAILS. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = codesOf word`: `codeOf '0'` is the all-dash code, "
            "and the rival's '0' code differs in value (though not length, so a "
            "length-only check would miss it), disagreeing wherever '0' appears. "
            "Verifying would be SPEC-TOO-WEAK (a wrong same-length code slips "
            "through). Refuted at word=['0'] — the symbol where the symbol-1 rival "
            "is correct, so this near-miss carries its own discriminating input."),
        "witness": _tester(
            "example : encodeWordTester (['0'] : List Char) = false := by\n"
            "  decide\n"),
        # Measured: rival exit 0; reference exit 1 with `Tactic `decide` proved
        # that the proposition encodeWordTester ['0'] = false is false`.
        "witness_reference": _REFERENCE,
    },
    {
        "id": "reject-skip-first-symbol",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the FIRST symbol of a multi-symbol sequence (encode only the tail);
        # correct on a single-symbol sequence. Attacks the ordered-traversal
        # structure of the fold, not the table values. Needs a length-2 input.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return if word.length ≤ 1 then word.map codeOf else (word.drop 1).map codeOf\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "encodes only the tail of a multi-symbol sequence, dropping the first "
            "symbol's code (correct on a single symbol, diverges for length ≥ 2). "
            "Its faithful real counterpart is an encoder that skips the first input "
            "symbol; under it a multi-symbol request renders the codes missing the "
            "leading symbol, so the F2P exact-string assertion FAILS. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = codesOf word`: on a length-≥2 sequence the rival "
            "returns `codesOf (word.drop 1)`, which is a strictly shorter list than "
            "`codesOf word`, so the clause fails. Verifying would be SPEC-TOO-WEAK "
            "(drops the first symbol). Refuted at word=['2','3'] — a length-2 input "
            "the single-symbol value rivals do not exercise, exercising the ordered "
            "traversal rather than a table entry."),
        "witness": _tester(
            "example : encodeWordTester (['2', '3'] : List Char) = false := by\n"
            "  decide\n"),
        # Measured: rival exit 0; reference exit 1 with `Tactic `decide` proved
        # that the proposition encodeWordTester ['2', '3'] = false is false`.
        "witness_reference": _REFERENCE,
    },

    # =====================================================================
    # UNIQUENESS — SOURCE ORDER. Added by audit: the three rivals above pin the
    # per-symbol VALUES and the LENGTH of the output, but none of them pins the
    # ORDER. `reject-skip-first-symbol` shortens the list, so a rival that keeps
    # every code exactly once and merely PERMUTES them is unattacked — and an
    # encoder that assembles its output back-to-front is a realistic way to get
    # that wrong (the frozen impl accumulates by prepending while walking the
    # sequence backwards, so an inverted accumulation is the natural error). This
    # rival emits the multiset of correct codes in reversed source order.
    # =====================================================================
    {
        "id": "reject-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL, "    return (word.map codeOf).reverse\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "emits every symbol's code exactly once, each one CORRECT, but in "
            "reversed source order (correct on any sequence of length ≤ 1 and on "
            "any palindromic sequence, so it is a genuine near-miss rather than a "
            "broken encoder). Its faithful real counterpart is an encoder that "
            "accumulates the per-symbol codes back-to-front; under it a "
            "multi-symbol request renders the correct codes in the wrong order, so "
            "the F2P assertion that pins the rendered string exactly FAILS. It "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = codesOf word`: `codesOf` is front-recursive, so it "
            "pins the code sequences IN SOURCE ORDER, not merely as a multiset of "
            "the right size. The rival agrees with `codesOf word` on length and on "
            "every element's membership, and disagrees only in position — the one "
            "sub-domain the value and length rivals leave untested. Verifying "
            "would be SPEC-TOO-WEAK (the ordering of the clause would be "
            "unpinned). Refuted at word=['1','0'], an asymmetric length-2 input."),
        "witness": _tester(
            "example : encodeWordTester (['1', '0'] : List Char) = false := by\n"
            "  decide\n"),
        # Measured: rival exit 0; reference exit 1 with `Tactic `decide` proved
        # that the proposition encodeWordTester ['1', '0'] = false is false`.
        # (Against the frozen solution this same witness is STUCK, exit 1 with
        # `did not reduce to `isTrue` or `isFalse``, hence the reference.)
        "witness_reference": _REFERENCE,
    },

    # =====================================================================
    # UNIQUENESS — EMPTY SEQUENCE. Added by audit: every witness above sits at a
    # non-empty `word`, so the `codesOf [] = []` base case of the clause was
    # asserted in prose but never demonstrated. A rival that emits one spurious
    # empty code for the empty sequence is correct everywhere else, so this is
    # the boundary input at which it alone diverges.
    # =====================================================================
    {
        "id": "reject-nonempty-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return if word.isEmpty then [[]] else word.map codeOf\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "on the empty symbol sequence it emits a single empty code sequence "
            "instead of no code sequences at all; correct on every non-empty "
            "input. Its faithful real counterpart is an encoder that always emits "
            "at least one code group, so an empty request renders a spurious "
            "separator-joined empty group instead of the empty rendering, and an "
            "assertion pinning the rendering of an empty request FAILS. It would "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = codesOf word`: `codesOf [] = []`, so the clause "
            "pins the output to be EMPTY on the empty sequence, and a "
            "one-element list is a different value (length 1 ≠ 0). This is the "
            "base case of the front-recursion, which no other rival's witness "
            "reaches — all of them sit at a non-empty `word`. Verifying would be "
            "SPEC-TOO-WEAK (the clause would be unpinned at the boundary). "
            "Refuted at word=[]."),
        "witness": _tester(
            "example : encodeWordTester ([] : List Char) = false := by\n"
            "  decide\n"),
        # Measured: rival exit 0; reference exit 1 with `Tactic `decide` proved
        # that the proposition encodeWordTester [] = false is false`.
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) and 0 AXIOM_TESTS. This bundle
# models ONLY the purely-functional per-symbol expansion of ONE word — the single
# method `encodeWord` whose clause is `out = codesOf word`. The separator/join
# and the whitespace/filter I-ops of the sibling's `encode_morse` are NOT modeled
# here (unchanged concrete ops, transliterated in the conformance shadow —
# mapping.md §2), so the sibling cases attached to them have no counterpart. Every
# sibling case is accounted for below.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------------
#   pos-mlist-branch-reorder             -> pos-map-structural        PORTED
#                                           (structural, map-based reproof — the
#                                            on-carrier "reorder": a different
#                                            impl shape building the same table)
#   pos-encode-local-reshape             -> pos-local-reshape         PORTED
#   admiss-default-sep                   -> admiss-postimage-nondegenerate RE-AIMED
#   rival-frame-mutate-msg               -> (none)                    VACUOUS
#   rival-prepatch-digit1-four-dash      -> reject-symbol1-four-dash  PORTED (headline)
#   rival-wrong-digit0                   -> reject-wrong-symbol0       PORTED
#   rival-skip-first-symbol              -> reject-skip-first-symbol   PORTED
#   rival-wrong-separator-first-step     -> (none)                    DROPPED (unmodeled)
#   (no sibling counterpart)             -> reject-reversed-order      ADDED (audit)
#   (no sibling counterpart)             -> reject-nonempty-on-empty   ADDED (audit)
#
# 4 ported, 1 re-aimed, 1 vacuous, 1 dropped (separator not modeled), 2 ADDED by
# audit. No case was dropped because its proof was hard; each drop is a carrier
# limit stated below. The two added rivals are not sibling ports: they close
# sub-domains (source ORDER, and the empty-sequence base case) that this carrier
# expresses and the ported set left untested — the sibling's own reject lane did
# not cover them either, because its `encoded_seq` clause was attacked through the
# separator rival that has no counterpart here.
#
# VACUOUS (rival-frame-mutate-msg): the sibling writes to a read-only input
#   carrying a fractional heap permission (`Acc(list_pred(msg), 1/2)`) and is
#   rejected for INSUFFICIENT PERMISSION before any value reasoning. This backend
#   is referentially transparent: `word` is an immutable `List Char` value, the
#   method declares no `mut` input binder, and there is no heap or aliasing. No
#   read-only input to overwrite, no permission system to trip. No substitute
#   fabricated (per the porting map, dropped rather than replaced). AUDIT measured
#   this rather than accepting the prose: an in-region write to the input
#   (`word := '0' :: word.drop 1`) yields no value-level rejection to witness, it
#   fails to ELABORATE — "`word` cannot be mutated, only variables declared using
#   `let mut` can be mutated". The carrier has no such program to reject, which is
#   what vacuous means here.
# RE-AIMED (admiss-default-sep): the sibling re-derives that the default separator
#   is in-domain and a normal call is admissible. There is no `require` clause
#   here (precondition ≡ True) and the separator is not modeled, so that probe is
#   vacuous. It is re-aimed at the residual admissibility risk on a total domain —
#   an unsatisfiable/degenerate post-image — via an in-region assert pinning
#   `codesOf ['1']` (the fix's datum) to the singleton five-signal code, i.e.
#   counting it rather than collapsing it.
# DROPPED (rival-wrong-separator-first-step): the sibling attacks the join token
#   between adjacent symbols. `encodeWord` produces only the per-symbol code
#   sequences `List (List Char)`; the single-signal join is an UNCHANGED concrete
#   op transliterated in the conformance shadow (mapping.md §2), not part of this
#   spec. There is no separator binder to abuse and no clause pinning the join, so
#   the rival has no discriminable counterpart on this carrier. A genuine
#   carrier-narrowing drop, not an omission of convenience.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = codesOf word` is attacked by
#   all five rivals across distinct sub-domains — the corrected value at '1' (the
#   headline discriminator), a wrong same-length value at '0', the ordered
#   traversal (skip-first), source ORDER under a permutation that preserves length
#   and multiset (reversed-order), and the empty-sequence base case — refuted at
#   FIVE DISTINCT input points (pts=5). The sole input binder `word` is moved
#   across the empty vector ([]), one-symbol vectors (['1'], ['0']) and two-symbol
#   vectors (['2','3'], ['1','0']), and across five symbols, so the per-symbol
#   table dependence, the length dependence, the ORDER dependence and the base
#   case of the post-image are each demonstrated separately. No two rivals share a
#   witness, and each rival is CORRECT at every other rival's witnessed input, so
#   every rejection is attributable to the one sub-domain that rival attacks
#   rather than to a blanket breakage. Value, structure, order and boundary
#   coverage are defended on the positive side by the two positive controls (a
#   fold-shaped reshape and a map-shaped reproof) plus the four audit reshapes
#   recorded in the module docstring, all of which verify.
#
# AXIOM_TESTS: empty. The sibling has none; `codeOf`/`codesOf` are an A-reference
#   deep model validated by axiom_check.py (G-AX), and this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
