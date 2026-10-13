"""properties.py — G-PBT falsification battery for django__django-13513 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct assembleReport`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec — here a declared
``witness_reference``, since gold's loop cannot decide anything; see WITNESS
MECHANICS below).

DEFENDED SURFACE (one contracted method over a chain of per-item entry
sequences, ``List (List Int)``):

  assembleReport (groups : List (List Int)) return (out : List Int)
    ensures out = flattenSeq groups                       -- THE load-bearing clause

The method assembles the complete report for a chain of related items: the
entries contributed by each item, in order, concatenated end to end — every item
contributes ALL of its entries, and an item that contributes NONE (an empty
element) is skipped over WITHOUT ending the assembly. ``flattenSeq`` is a total,
fully-unfolded pure ``def`` over the method's own input
(``flattenSeq (g :: gs) = g ++ flattenSeq gs``) in the ``pure`` region; the
``axioms`` region is empty. There is NO opaque answer-key oracle in the clause
(directive 8 — the post-image is grounded in the actual input carrier), so
pinning ``out = flattenSeq groups`` is grounded, not an echo.

The single clause decomposes into independently-attackable sub-behaviours of the
concatenation:

  * COMPLETENESS  — every item's entries appear IN FULL (no item dropped, no
                    per-item entry dropped);
  * SKIP-NOT-HALT — an empty item is skipped but does NOT truncate the report;
                    the entries of items AFTER an empty one still appear. This is
                    THE change: the pre-patch assembly halted on the first
                    empty item, dropping every later item's entries;
  * ORDER         — items are concatenated in their own order (this carrier is
                    ORDER-SENSITIVE, unlike the sibling's order-free SUM count).

ONE input binder, free (no ``require`` clause; the pre-conditions region is
empty): the post-image must hold for EVERY value of ``groups`` — its length, the
contents of each element, the ORDER of the elements, and how empty elements are
handled. Reject witnesses vary all of these facets (including WHERE an empty
element sits: leading in ``[[], [1]]``, trailing in ``[[4], []]``).

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The sibling's MANDATORY frame-mutation
    rival keeps the gold body verbatim then writes back into a read-only
    sequence input carrying only a fractional heap permission
    (``Acc(list_pred(trace_lens),1/2)``) and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: ``groups`` is an
    immutable value, the method declares no ``mut`` binder, there is no heap and
    no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated (per the
    porting map, this class is legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``flattenSeq groups`` — a concrete ``def`` over the method's own
    argument (empty ``axioms`` region; no opaque callee). The unique satisfier IS
    the grounded concatenation, so there is no wrong echo to build; the honest
    cheapest faithful reshapes are the ``pos-*`` controls.
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
  * PARTIAL-DOMAIN / VALUE — the reject surface. Each rival gets the coarse shape
    plausible (a ``List Int``) but diverges on one sub-behaviour: truncating at
    the first empty item (THE bug), keeping only one item, dropping every item,
    dropping the last entry of each item, reversing the item order, or padding
    every item with a phantom entry.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is a BACKWARD ``while`` fold:
its extracted program ``assembleReportExec`` elaborates through the loop's
``Classical.choice`` and the kernel does NOT reduce it under ``decide``. Every
reject rival, by contrast, is written LOOP-FREE (a single ``return <expr>`` over
``flattenSeq`` / ``List`` combinators), so its extracted ``assembleReportExec``
REDUCES fully under ``decide`` at a concrete input. Each witness states, at one
concrete input, that the rival's own extracted output DIFFERS from the transparent
post-image ``flattenSeq groups`` the clause demands — a direct clause violation
the elaborator decides.

The FROZEN solution therefore CANNOT serve as the witness's second subject, and
this manifest does not pretend otherwise (an earlier revision of this docstring
claimed gold "FAILS with a ``decide`` error", which read as a semantic refutation
and was wrong). Measured with ``scripts/lean_verify.sh`` on all five witnesses:
against gold the build fails (exit 1) with

    Tactic `decide` failed ... because its `Decidable` instance instDecidableNot
    did not reduce to `isTrue` or `isFalse`

— a STUCK REDUCTION, not a refutation. That is the ``_STUCK_REDUCTION`` class the
gate screens for: the same error appears for a TRUE claim about gold, so gold's
exit code discriminates nothing. Confirmed adversarially — a FORGED witness
asserting the rival AGREES with the post-image at an agreement point
(``… = flattenSeq [[]]``, the opposite of a refutation) also elaborates against
the rival (exit 0) and also fails on gold by stuck reduction (exit 1).

So every reject case names an explicit ``witness_reference``: the loop-free
``return flattenSeq groups`` impl, which shares the frozen spec byte-for-byte and
VERIFIES (it is ``pos-assemble-direct``'s module). The gate checks both of those
before using it, and an impl the verifier ACCEPTS cannot violate its own spec, so
a genuine refutation must still fail there. Measured per witness: rival exit 0,
reference exit 1 with ``Tactic `decide` proved that the proposition … is false``
— a SEMANTIC refutation of the concrete claim, which is what the gate needs and
what a stuck gold build never provided. The forged agreement-witness above is
killed by this subject (reference exit 0 => ``witness-vacuous``), where against a
stuck gold it would have been recorded as a refutation.

No witness binds a hypothesis (every input is a concrete literal that decides the
clause; ``flattenSeq`` over the literal reduces), so no consistency probe is
needed. No banned token (sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The sibling carries axiom-soundness /
containment probes; this bundle declares no consumed ``axiom`` and no deep-model
reference (``flattenSeq`` models the CHANGED assembly op itself, an R/I op checked
by ``conformance_check.py`` / G-CONF, not axiomatized). Nothing in the proof rests
on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13513"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the -- impl-start .. -- impl-end region
# (or the elided prove_correct body), so same_spec holds by construction and the
# prove_correct assembleReport obligation survives byte-identically. Every _swap
# asserts uniqueness at load, so drift in the frozen Solution.lean fails loudly.
# ---------------------------------------------------------------------------

# The WHOLE frozen assembleReport executable body (the backward `while` fold),
# between that method's -- impl-start / -- impl-end (the comment lines and the
# markers stay put, so the spec view is untouched).
_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := groups.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ groups.length\n"
    "      invariant result = flattenSeq (groups.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let g := groups[i - 1]!\n"
    "      result := g ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "assembleReport impl region drifted"

# The frozen proof (retuned only by the loop-free positive, whose residual goal
# no longer needs the backward-fold step lemma).
_PROOF = (
    "prove_correct assembleReport by\n"
    "  loom_solve\n"
    "  rw [flattenSeq_drop_step groups i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "assembleReport proof region drifted"

# The single in-loop prepend line (for the seg-local reshape; proof untouched).
_PREPEND = "      result := g ++ result"
assert _BASE.count(_PREPEND) == 1, "assembleReport prepend line drifted"


def _impl(new_body):
    """A loop-free assembleReport rival: swap the whole executable body for a
    single `return <expr>`. Being loop-free its extracted `…Exec` reduces under
    `decide`, so its witness discriminates; gold's `while` loop stays stuck. The
    frozen proof is LEFT in place — with no loop the `rw [flattenSeq_drop_step
    groups i …]` has no `i`/loop goal to hit and the rival module fails to build
    (which is what expect="reject" requires); the witness, not the build failure,
    attributes the rejection to the spec."""
    return _swap(_BASE, _IMPL, "    return (" + new_body + ")")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct loop-free reshapes)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness builder. The post-image is transparent, so refute the clause
# ---- directly against `flattenSeq` on the EXTRACTED program. Checked in a file
# ---- whose prove_correct block is stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT = "extract_program_for assembleReport\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match assembleReportExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ flattenSeq ({inp}) := by\n"
        "  decide\n"
    )


# ---- the witness SUBJECT for every reject case. The frozen impl's `while` loop
# ---- elaborates through `Classical.choice`, so `decide` against gold's extracted
# ---- program is STUCK for every claim, true or false ("did not reduce to
# ---- `isTrue` or `isFalse`") -- an exit code that discriminates nothing. This
# ---- loop-free impl of the SAME frozen spec does reduce, and it VERIFIES, so a
# ---- witness refuted against it is refuted against something known to satisfy
# ---- the spec. It is the module of `pos-assemble-direct`, independently required
# ---- to verify by this same battery, and the gate re-checks (shares the frozen
# ---- spec AND verifies) before using it.
_REF_DIRECT = _impl_reproved(
    "    return flattenSeq groups",
    "prove_correct assembleReport by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-assemble-direct",
        "kind": "soundness",
        "expect": "verify",
        # Report the whole concatenation DIRECTLY via the transparent fold, no
        # backward loop. The ensures IS `out = flattenSeq groups`, so this is the
        # cheapest HONEST correct impl — and, since `flattenSeq groups` is
        # GROUNDED in the argument (not an opaque answer key), it doubles as proof
        # the clause is not echo-vulnerable (any WRONG assembly fails `out =
        # flattenSeq groups`). The loop is gone, so the frozen proof's backward-
        # fold step is unneeded and the residual goal closes under `loom_solve`.
        "module": _REF_DIRECT,
        "rationale": "the post-image `flattenSeq groups` is GROUNDED in the input "
                     "(a total front-recursive fold, no opaque answer key), so "
                     "`return flattenSeq groups` is the honest cheapest CORRECT "
                     "assembly; the clause is literally `out = flattenSeq groups`, "
                     "so it MUST verify, else SPEC-TOO-STRONG. Ports the sibling's "
                     "structurally-different assemble positive (the sibling kept "
                     "the backward walk to dodge an f(a+b) lemma; on THIS carrier "
                     "the direct fold needs no lemma, so the cheapest reshape is "
                     "used) and doubles as the honest-echo control.",
    },
    {
        "id": "pos-assemble-seg-local",
        "kind": "soundness",
        "expect": "verify",
        # Keep the backward `while` fold but bind the per-item entry sequence to a
        # local `contribution` before prepending. Same value flow (`contribution =
        # g`), different control shape; the frozen proof still closes unchanged
        # (invariant and step lemma untouched). Mirrors the sibling's local-reshape
        # positive that keeps the gold backward walk and every framing step.
        "module": _swap(
            _BASE, _PREPEND,
            "      let contribution := g\n      result := contribution ++ result"),
        "rationale": "a correct assembly with a DIFFERENT control shape (bind the "
                     "per-item entry sequence to a local before prepending) must "
                     "verify; the value flow is unchanged (`contribution = g`) so "
                     "the clause still discharges and the frozen backward-fold "
                     "proof closes as-is. If it fails => SPEC-TOO-STRONG (over-fit "
                     "to the inline-prepend code form). Ports the sibling's "
                     "pos-assemble-reshape (local reshape keeping the gold walk).",
    },
    {
        "id": "pos-assemble-forward",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E). The two positives above are cheap: one is
        # loop-free, the other keeps the frozen backward fold and only binds a
        # local, so neither exercises a genuinely different CONTROL shape. This one
        # walks the chain FORWARD, appending each item's entries to the end, with a
        # take-prefix invariant instead of the frozen drop-suffix one. It is the
        # reshape the sibling explicitly DODGED (its note: a forward walk over a
        # front-recursive fold needs an f(a ++ b)-style step lemma the verifier will
        # not auto-discharge), so it is the strongest available soundness control:
        # the spec must admit a faithful assembly that accumulates in the opposite
        # direction and needs its OWN step lemma, proved in the elided tactic body.
        "module": _impl_reproved(
            "    let mut result : List Int := []\n"
            "    let mut i := 0\n"
            "    while i < groups.length\n"
            "      invariant i ≤ groups.length\n"
            "      invariant result = flattenSeq (groups.take i)\n"
            "      done_with i = groups.length\n"
            "      decreasing groups.length - i\n"
            "    do\n"
            "      result := result ++ groups[i]!\n"
            "      i := i + 1\n"
            "    return result",
            "prove_correct assembleReport by\n"
            "  have hstep : ∀ (gs : List (List Int)) (k : Nat), k < gs.length →\n"
            "      flattenSeq (gs.take (k + 1)) = flattenSeq (gs.take k) ++ gs[k]! := by\n"
            "    intro gs\n"
            "    induction gs with\n"
            "    | nil => intro k hk; simp at hk\n"
            "    | cons a bs ih =>\n"
            "      intro k hk\n"
            "      cases k with\n"
            "      | zero => simp [flattenSeq]\n"
            "      | succ n =>\n"
            "        have hn : n < bs.length := by simpa using hk\n"
            "        simp [flattenSeq, ih n hn, List.append_assoc]\n"
            "  loom_solve"),
        "rationale": "a correct assembly that walks the chain FORWARD (append each "
                     "item's entries to the end; take-prefix invariant instead of "
                     "the frozen drop-suffix one) must verify. This is a genuinely "
                     "different CONTROL shape, not a local rebinding: it needs its "
                     "own step lemma flattenSeq (take (k+1)) = flattenSeq (take k) "
                     "++ gs[k]!, proved in the elided tactic body, because "
                     "`flattenSeq` is FRONT-recursive and a forward accumulator "
                     "meets it at the back. The sibling recorded this reshape as one "
                     "it deliberately avoided for exactly that lemma gap; landing it "
                     "here shows the clause pins the assembled VALUE and not the "
                     "frozen fold's direction. If it failed => SPEC-TOO-STRONG "
                     "(over-fit to the backward-fold control shape). ADDED BY AUDIT "
                     "(attack E): the pre-audit battery's positives were a loop-free "
                     "impl and a local rebinding, so no case tested a reshape whose "
                     "proof needed a new lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the sibling's admiss-f2p-shaped-input. That
    # case re-established the read-only fractional-permission precondition on the
    # F2P chain [1, 0] under the function's own Requires. This method carries NO
    # `require` (the pre-conditions region is empty) and there is no heap
    # permission, so the classic "a normal input satisfies the precondition" probe
    # is vacuous (every input is in-domain). Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is jointly
    # SATISFIABLE by a gold-shaped computation on the F2P-shaped input. The frozen
    # impl discharging the obligation IS that witness. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": "the method carries no `require`, so the assembly is total "
                     "over every chain of per-item entry sequences — including the "
                     "F2P-shaped chain (an item contributing one entry alongside an "
                     "item contributing NONE); the gold impl discharging `out = "
                     "flattenSeq groups` is the admissibility witness that the "
                     "post-image is satisfiable there. Near-trivial precisely "
                     "because the precondition is empty. Re-aimed from the "
                     "sibling's admiss-f2p-shaped-input, whose read-only fractional-"
                     "permission half has no counterpart on this referentially-"
                     "transparent carrier. Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P/P2P tests. Each rival is a loop-free
    # expression so its extracted tester reduces under `decide`; the frozen spec
    # is untouched.
    # =====================================================================
    {
        "id": "uniq-prepatch-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG ITSELF. Assemble entries only up to the FIRST empty item, then
        # stop — dropping every later item's entries. This is the pre-patch coupled
        # walk: the single pointer advances to the next item only from inside the
        # per-entry loop, so an empty item ends the whole assembly. `takeWhile
        # (not empty)` is the faithful loop-free shape (it halts at the first empty
        # element, exactly as the coupled walk aborts).
        "module": _impl("flattenSeq (groups.takeWhile (fun g => ! g.isEmpty))"),
        "refinement": "this IS the pre-patch behaviour that Solution_prepatch "
                      "reproduces and G-DIFF flags: the assembly halts at the "
                      "first item whose own entry sequence is empty, dropping every "
                      "later item's entries. On the F2P chain (an empty-entry item "
                      "ahead of a one-entry item) it returns NO entries; the sole "
                      "FAIL_TO_PASS test asserts the report still contains the one "
                      "real entry (len == 1). Its faithful real counterpart is the "
                      "un-restructured coupled walk — exactly what does NOT resolve.",
        "rationale": "REJECT from `out = flattenSeq groups` via SKIP-NOT-HALT: "
                     "`flattenSeq` skips an empty item and keeps concatenating, but "
                     "the rival truncates at it, so their outputs differ on any "
                     "chain with a non-empty item AFTER an empty one. Refuted at "
                     "groups=[[], [1]] (the F2P shape): the rival's takeWhile "
                     "stops at the leading empty item and yields [], where "
                     "`flattenSeq` yields [1]. If it verified => SPEC-TOO-WEAK "
                     "(admits the very bug, mirrors G-DIFF).",
        "witness": _witness("([[], [1]] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "uniq-first-item-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Count only the FIRST item's entries (the innermost, consumed first) and
        # nothing else. Correct on a length-1 chain and on chains whose whole
        # report equals the first item's entries, but wrong whenever any later item
        # contributes entries. Ports the sibling's uniq-last-only onto this
        # carrier's item order (innermost-first).
        "module": _impl("match groups with | [] => [] | g :: _ => g"),
        "refinement": "counting only the first item's entries corresponds to a "
                      "patch that emitted the innermost item's entries and never "
                      "ran the loop over the remaining items — every later item's "
                      "entries are dropped. The nested-item P2P test observes "
                      "entries from multiple items in the chain; this drops all but "
                      "one and does NOT resolve.",
        "rationale": "REJECT from `out = flattenSeq groups` via COMPLETENESS: "
                     "`flattenSeq` concatenates EVERY item's entries, but the rival "
                     "returns only the first item's, so they differ whenever a "
                     "later item is non-empty. Refuted at groups=[[7], [8]]: the "
                     "rival yields [7], `flattenSeq` yields [7, 8]. Varies the "
                     "`groups` binder (two distinct singleton items) from the other "
                     "witnesses. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("([[7], [8]] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "uniq-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Return no entries at all. Correct only on the empty / all-empty chain;
        # wrong on every chain with a non-empty item. Cheap supporting near-miss.
        "module": _impl("[]"),
        "refinement": "returning no entries corresponds to a patch whose assembly "
                      "produced an empty report — every traceback test fails (the "
                      "F2P wants one entry, the nested-item tests want several). "
                      "Cheap supporting near-miss; does NOT resolve.",
        "rationale": "REJECT from `out = flattenSeq groups` via COMPLETENESS: "
                     "`flattenSeq` is non-empty on any chain with a non-empty item, "
                     "but the rival is always empty. Refuted at groups=[[5]]: the "
                     "rival yields [], `flattenSeq` yields [5]. Partial-domain "
                     "(correct only on the empty / all-empty chain). Distinct input "
                     "point from the other witnesses.",
        "witness": _witness("([[5]] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "uniq-drop-last-per-item",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the LAST entry of each item's contribution before concatenating.
        # The report is then short by one entry per non-empty item. Correct only
        # when every item is empty or contributes exactly one entry. Ports the
        # sibling's uniq-off-by-one-tail onto the assembly level (the sibling
        # attacked frames_from_traceback's per-item count, which is folded into the
        # carrier here; the assembly-level counterpart truncates each item's run).
        "module": _impl("flattenSeq (groups.map (fun g => g.dropLast))"),
        "refinement": "dropping the last entry of each item corresponds to an "
                      "assembly that truncated each item's entry run by one — every "
                      "non-empty item loses its final entry. The traceback-"
                      "rendering P2P tests observe the full per-item entry count; a "
                      "report short by one entry per item does NOT resolve.",
        "rationale": "REJECT from `out = flattenSeq groups` via COMPLETENESS "
                     "(per-item, not per-chain): `flattenSeq` carries EACH item's "
                     "entries in full, but the rival drops each item's last entry, "
                     "so they differ whenever an item has ≥ 2 entries. Refuted at "
                     "groups=[[1, 2]]: the rival yields [1], `flattenSeq` yields "
                     "[1, 2]. Varies `groups` (a single multi-entry item — a facet "
                     "no other witness exercises). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("([[1, 2]] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "uniq-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Concatenate the items in REVERSE order. Correct on a palindromic chain
        # of items; wrong otherwise. THIS carrier is order-sensitive (unlike the
        # sibling's order-free SUM count), so the ORDER sub-behaviour gets its own
        # rival — an observable the sibling could not express.
        "module": _impl("flattenSeq groups.reverse"),
        "refinement": "concatenating the items in reverse corresponds to an "
                      "assembly that emitted the chain's items back-to-front — the "
                      "report would list the outermost item's entries before the "
                      "innermost's, permuting the rendered traceback. The P2P "
                      "traceback tests observe the entries in chain order; a "
                      "reversed report does NOT resolve.",
        "rationale": "REJECT from `out = flattenSeq groups` via ORDER: `flattenSeq` "
                     "concatenates the items in their own order, the rival in "
                     "reverse, so for any non-palindromic chain (≥ 2 distinct "
                     "items) they differ. Refuted at groups=[[1], [2]]: the rival "
                     "yields [2, 1], `flattenSeq` yields [1, 2]. Attacks the ORDER "
                     "sub-behaviour the sibling's order-free SUM count could not "
                     "express (ADDED for this carrier). If it verified => "
                     "SPEC-TOO-WEAK (item order unpinned).",
        "witness": _witness("([[1], [2]] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "uniq-phantom-entry-per-item",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). Every pre-audit rival UNDER-produces: it drops
        # items, drops entries, truncates, or permutes. Nothing attacked the
        # OVER-production direction, so nothing showed the clause is an equality and
        # not a "contains at least" containment. This rival appends one phantom entry
        # to EVERY item's contribution, so the report is a strict SUPERSEQUENCE of
        # the correct one — longer than, and containing, `flattenSeq groups`.
        "module": _impl("flattenSeq (groups.map (fun g => g ++ [0]))"),
        "refinement": "appending a phantom entry per item corresponds to an assembly "
                      "that emitted one spurious trailing entry for every item in "
                      "the chain — including for an item that contributes NONE, "
                      "which would invent an entry out of nothing. The traceback-"
                      "rendering P2P tests observe the exact per-item entry count, "
                      "so a report padded by one entry per item does NOT resolve. "
                      "Ports the over-count direction of the sibling's "
                      "uniq-fft-extra onto the assembly level.",
        "rationale": "REJECT from `out = flattenSeq groups` via COMPLETENESS read as "
                     "an EQUALITY (the direction no other rival probes): `flattenSeq` "
                     "carries each item's entries and NOTHING ELSE, but the rival "
                     "adds one entry per item, so its output strictly CONTAINS the "
                     "correct report. Refuted at groups=[[4], []]: the rival yields "
                     "[4, 0, 0] (note the phantom entry even for the empty item), "
                     "`flattenSeq` yields [4]. Varies `groups` at a facet no other "
                     "witness uses — a non-empty item FOLLOWED by an empty one (the "
                     "F2P shape reversed). If it verified => SPEC-TOO-WEAK (the "
                     "clause would only bound the report from below).",
        "witness": _witness("([[4], []] : List (List Int))"),
        "witness_reference": _REF_DIRECT,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The sibling battery has 11 SPEC cases over TWO modeled functions
# (frames_from_traceback, assemble_frames) plus the pure `chain_total` SUM:
#   2 soundness positives (pos-frames-reshape, pos-assemble-reshape),
#   1 admissibility (admiss-f2p-shaped-input),
#   2 MANDATORY frame-mutation rivals (frame-mut-setitem, frame-mut-append),
#   6 uniqueness rivals (uniq-prepatch-coupled, uniq-last-only,
#     uniq-off-by-one-tail, uniq-empty, uniq-fft-extra, uniq-fft-short),
#   plus an AXIOM lane (2 probes).
#
# CARRIER NARROWING. This velvet bundle models ONLY the purely-functional core
# the patch changed: the cross-chain ASSEMBLY, `assembleReport`, with clause
# `out = flattenSeq groups`. The per-item traversal `frames_from_traceback` is
# UNCHANGED by the patch (mapping.md §3.1) and is folded into the input carrier
# `groups` — it is NOT modeled here — and `chain_total` (an order-free SUM count)
# is replaced by `flattenSeq` (the actual order-sensitive concatenation). So
# every sibling case attached to frames_from_traceback's per-item COUNT has no
# direct counterpart, and the assembly rivals port to the sub-behaviours of
# `flattenSeq`.
#
#   sibling case               -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-frames-reshape         -> (none)                        OMITTED (unmodeled fn)
#   pos-assemble-reshape       -> pos-assemble-direct           RE-EXPRESSED
#                              -> pos-assemble-seg-local        PORTED
#   (no sibling)               -> pos-assemble-forward          ADDED BY AUDIT (E)
#   uniq-fft-extra (direction) -> uniq-phantom-entry-per-item    ADDED BY AUDIT (D)
#   admiss-f2p-shaped-input    -> admiss-gold-total             RE-AIMED
#   frame-mut-setitem          -> (none)                        VACUOUS
#   frame-mut-append           -> (none)                        VACUOUS
#   uniq-prepatch-coupled      -> uniq-prepatch-truncate        PORTED (THE bug)
#   uniq-last-only             -> uniq-first-item-only          PORTED
#   uniq-off-by-one-tail       -> uniq-drop-last-per-item       PORTED (re-aimed)
#   uniq-empty                 -> uniq-empty                    PORTED
#   uniq-fft-extra             -> (none)                        OMITTED (unmodeled fn)
#   uniq-fft-short             -> (none)                        OMITTED (unmodeled fn)
#   (no sibling)               -> uniq-reverse-order            ADDED (ORDER clause)
#   AXIOM_TESTS (2)            -> (none)                        DROPPED (G-AX)
#
# 10 velvet SPEC cases: 3 soundness, 1 admissibility, 6 uniqueness. The single
# modeled obligation is DEFENDED (three positives + admissibility) and ATTACKED
# (six rivals across every sub-behaviour of the clause, in both the under- and
# over-production directions).
#
# OMITTED — frames_from_traceback cases (pos-frames-reshape, uniq-fft-extra,
#   uniq-fft-short): the per-item traversal is UNCHANGED by the patch and is not a
#   modeled function on this carrier — its output is the input `groups`. There is
#   no `len(Result()) == trace_len` clause here to defend or attack, so these
#   three cases have NO counterpart. This is carrier narrowing (the Lean-family
#   bundle models only the purely-functional core the patch changed), NOT a
#   dropped-because-hard omission: no rival for this behaviour could be authored
#   without modeling a function this bundle deliberately does not model.
# VACUOUS — frame-mut-setitem / frame-mut-append: the sibling's MANDATORY frame-
#   mutation rivals keep the gold body verbatim then WRITE into the read-only
#   input `trace_lens` (granted only half permission) and must be rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: `groups`
#   is an immutable value, the method declares no `mut` binder, there is no heap,
#   no aliasing, no permission system. There is no read-only input to overwrite,
#   so the class is vacuous. No substitute fabricated (porting map).
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# RE-AIMED (admissibility): the sibling asserts the half-permission admits the
#   F2P chain [1, 0]. This backend's method has NO precondition and no permission
#   surface, so that probe is degenerate (every input is in-domain). It is
#   re-aimed at the residual total-domain risk — that the post-image is
#   satisfiable by a gold-shaped computation on the F2P-shaped chain — witnessed
#   by the frozen impl discharging the obligation.
# RE-EXPRESSED / PORTED (positives): the sibling kept the gold BACKWARD walk in
#   both positive controls to avoid an f(a+b) lemma the front-recursive fold would
#   need on a FORWARD reshape. On THIS carrier the direct fold `return flattenSeq
#   groups` needs NO lemma (the clause IS `out = flattenSeq groups`), so it is the
#   cheapest honest positive (pos-assemble-direct); the local-reshape spirit of
#   pos-assemble-reshape — keep the gold backward walk, reshape only a local — is
#   carried by pos-assemble-seg-local (bind the per-item entries to a local before
#   prepending; frozen proof closes as-is). Both verified out-of-band.
# PORTED (rivals): uniq-prepatch-coupled -> uniq-prepatch-truncate (halt at the
#   first empty item — THE bug, F2P discriminator); uniq-last-only ->
#   uniq-first-item-only (keep only one item); uniq-empty -> uniq-empty (keep
#   nothing); uniq-off-by-one-tail -> uniq-drop-last-per-item (re-aimed: the
#   sibling attacked frames_from_traceback's per-item count, unmodeled here, so
#   the assembly-level counterpart truncates each item's run — attacking the
#   per-item COMPLETENESS half of the clause). Each carries a machine-checked
#   witness that ELABORATES against the rival and FAILS against gold.
# ADDED (uniq-reverse-order): the sibling's `chain_total` is an order-FREE SUM, so
#   it has no ORDER clause and no order rival. This carrier's `flattenSeq` is the
#   actual order-sensitive concatenation, so item order IS a top-level
#   sub-behaviour of the clause; a rival that reverses the items is a distinct
#   SPEC-TOO-WEAK probe (the ONLY witness that abuses element ORDER). Included so
#   no sub-behaviour of the clause is left unattacked.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   consumed axiom and no deep-model reference (`flattenSeq` models the CHANGED
#   assembly op itself — an R/I op checked by conformance_check.py / G-CONF, not
#   axiomatized), and the gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   * The single obligation `out = flattenSeq groups` is DEFENDED by three positives
#     (pos-assemble-direct, pos-assemble-seg-local, pos-assemble-forward) and the
#     admissibility case, and ATTACKED on every sub-behaviour in BOTH directions:
#     SKIP-NOT-HALT (uniq-prepatch-truncate — the bug), COMPLETENESS per-chain
#     (uniq-first-item-only, uniq-empty), COMPLETENESS per-item
#     (uniq-drop-last-per-item), ORDER (uniq-reverse-order), and OVER-PRODUCTION
#     (uniq-phantom-entry-per-item — the clause is an equality, not a containment).
#   * The single input binder `groups` is varied across all facets by the reject
#     witnesses (no facet held fixed): empty-leading two-item [[], [1]];
#     two distinct singleton items [[7], [8]]; a single singleton item [[5]];
#     a single MULTI-entry item [[1, 2]]; two distinct singleton items in an
#     order-sensitive pair [[1], [2]]; a non-empty item FOLLOWED by an empty one
#     [[4], []]. Element count (0-entry, 1-entry, 2-entry items; 1- and 2-item
#     chains), element contents, emptiness, emptiness POSITION (leading vs
#     trailing), and ORDER are all exercised.
#   * Reject witnesses probe 6 DISTINCT input points (pts = 6): [[], [1]],
#     [[7], [8]], [[5]], [[1, 2]], [[1], [2]], [[4], []] — no two rivals share an
#     input, so the battery demonstrates the clause's dependence on the several
#     facets of `groups` rather than refuting every rival at one point.
#
# WITNESS MECHANICS: the post-image is stated over the TRANSPARENT `flattenSeq`
#   (no opaque callee), so refutation is direct. Every witness extracts the
#   executable program (`assembleReportExec`) and refutes the clause at a concrete
#   input; each rival is loop-free so its `…Exec` reduces under `decide`. Gold's
#   `while`-loop `…Exec` does NOT reduce (its `Classical.choice` leaves `decide`
#   STUCK — "did not reduce to `isTrue` or `isFalse`" — for every claim, true or
#   false), so gold cannot be the discriminating subject and each reject case names
#   a `witness_reference` (_REF_DIRECT) instead. Measured with
#   scripts/lean_verify.sh, per witness: rival exit 0; reference exit 1 with
#   "`decide` proved that the proposition … is false" — a SEMANTIC refutation. No
#   witness binds a hypothesis, so no consistency probe is needed. See the module
#   docstring for the forged-witness experiment that establishes why the reference
#   subject, not gold, is what makes these witnesses discriminate.
#
# AUDIT RECORD (independent adversarial re-derivation of this port).
#   Attack A (statement integrity): every case diffs against the frozen file ONLY
#     inside -- impl-start/-- impl-end, plus a retuned tactic body in the two
#     reproved positives. No `method`/`ensures` byte differs. Clean.
#   Attack B (witness re-derivation): all five pre-audit witnesses rebuilt on
#     three subjects each. Rival exit 0 in all five; GOLD exit 1 by STUCK
#     REDUCTION in all five (not refutation); verifying-positive subject exit 1 by
#     semantic refutation in all five. The pre-audit manifest described gold's
#     failure as "a `decide` error" and claimed the witnesses discriminate against
#     gold — FALSE, and the gate was silently rescuing the battery through its
#     `_positive_sources` fallback. FIXED: each case now declares the reference
#     explicitly, and the docstring states the real mechanics.
#   Attack C (rival observably wrong?): each of the six rivals differs from
#     `flattenSeq groups` at its own witness point, machine-checked by that
#     witness's refutation against a VERIFYING impl. None is vacuous.
#   Attack D (SPEC-TOO-WEAK probe): 8 NEW wrong impls built against the frozen
#     spec — last-item-only, drop-first-item, duplicate-items, drop-first-entry-
#     per-item, one-extra-entry, dedup-entries, keep-only-empty-items, sorted
#     output. ALL 8 rejected (exit 1, each with an unsolved `ensures_1` goal). No
#     spec hole. The over-production family was the one direction the pre-audit
#     battery left unattacked, so it is now carried as
#     uniq-phantom-entry-per-item.
#   Attack E (SPEC-TOO-STRONG probe): 4 NEW correct reshapes built. `groups.flatten`
#     VERIFIES; `foldr (· ++ ·) []` VERIFIES; `filter (not ∘ isEmpty)` then
#     flatten VERIFIES (empty items are provably inert); the FORWARD loop with a
#     take-prefix invariant VERIFIES once its own step lemma is supplied. No
#     faithful correct impl is rejected. The forward reshape is now carried as
#     pos-assemble-forward.
#   Attack F (omissions): frame-mut-* re-derived independently and confirmed
#     INEXPRESSIBLE — an attempted write to the input carrier (`groups := ...`,
#     gold body otherwise verbatim) is refused by the carrier itself at parse
#     time: "`groups` cannot be mutated, only variables declared using `let mut`
#     can be mutated". A rejection the elaborator issues before any spec is
#     consulted attests to nothing about the spec, so no substitute is fabricated.
#     The frames_from_traceback cases (pos-frames-reshape, uniq-fft-extra,
#     uniq-fft-short) remain OMITTED as carrier narrowing, but the over-count
#     direction of uniq-fft-extra is now carried at the assembly level.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
AXIOM_TESTS = []
