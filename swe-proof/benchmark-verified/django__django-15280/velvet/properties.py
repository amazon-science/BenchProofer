"""properties.py — G-PBT falsification battery for django__django-15280 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct linkChildrenToParents`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and FAIL
against the witness's second subject, which on this bundle is the declared
``witness_reference`` rather than the frozen solution; see WITNESS MECHANICS for
why the frozen impl cannot decide anything here).

DEFENDED SURFACE (one contracted method over a batch of child objects,
parametric in the key→parent mapping). The single obligation is

    linkChildrenToParents (children : List Child) (lookup : Nat → Nat)
        return (out : List Nat)
      ensures out = resolvedSeq lookup children

``resolvedSeq lookup children`` is a total, fully-unfolded pure function: it maps
each child, IN BATCH ORDER, to the single parent it ends up associated with
(``resolveOne``): a child that ALREADY carries an association keeps it
(``existingParent = some p`` ↦ ``p``); a child that carries none is associated
with the parent its grouping key maps to (``existingParent = none`` ↦
``lookup key``). The load-bearing clause pins the WHOLE output sequence to this
per-child image, so it constrains three independent things at once: the
keep-existing branch, the look-up branch (including WHICH key is looked up), and
the batch order / length of the produced sequence.

``lookup : Nat → Nat`` is a FREE input the spec quantifies over: the ``ensures``
holds for EVERY value of it, so the spec makes no claim about how a key resolves
to a parent — only that the child carrying none is associated with the parent
ITS OWN key resolves to. Because the result is pinned for every ``lookup``, a
rival that consulted the wrong key (or ignored the mapping entirely) is refuted
uniformly, and can be caught by instantiating ``lookup`` at a NON-CONSTANT
function that separates the keys.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating backward loop collapsed to the
    closed form the post-image names; the per-child branch reordered) must still
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries NO ``require`` clause (the pre-conditions
    region is empty), so the sibling's "a normal input satisfies the
    precondition" probe is degenerate here (every input is in-domain). The
    residual risk on a total-domain spec is that the post-image is DEGENERATE at
    the interesting point — a spec no impl distinguishes reads exactly like one
    every impl meets. ``admiss-resolve-nondegenerate`` discharges an in-region
    assert pinning that the per-child image genuinely distinguishes its two
    branches (a child carrying an association keeps it; a child carrying none is
    looked up) and that the batch is assembled in order.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rivals write back into read-only sequence inputs that carry
    only a fractional heap permission (``Acc(...,1/2)``) and are rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent: every
    parameter is an immutable value, this bundle declares no ``mut`` binder, there
    is no heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated (per the porting map, this class is legitimately dropped here
    rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. The post-image is pinned
    to ``resolvedSeq lookup children`` — a concrete ``def`` computed entirely from
    the method's own inputs; the ``axioms`` region is empty (no opaque answer
    key). The unique satisfier IS the grounded decision, so there is no oracle to
    echo. The free ``lookup`` is quantified over, not an answer key: the output is
    pinned to the value of ``lookup`` at each child's OWN key, which a wrong impl
    cannot fake for every ``lookup``.
  * CONTROL-FLOW-EFFECT / PARTIAL-DOMAIN / VALUE — heavily exercised. The output
    surface has several sub-domains a rival can get right on most inputs yet
    diverge on one: the keep-existing branch (the F2P scenario — the pre-existing
    association clobbered), the look-up branch (ignored, or applied to the wrong
    key), and the batch order.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches it through Velvet's own tester
machinery: ``linkChildrenToParentsTester children lookup = false`` says the
extracted program's result violates the postcondition at that concrete input,
checked in a file whose ``prove_correct`` block has been stripped (no tactic
script can mask the verdict). Every reject rival is reshaped into a LOOP-FREE
closed form, so ITS tester kernel-reduces; the free mapping ``lookup`` is
instantiated at a concrete decidable function in each witness, so the tester
reduces to a ground boolean.

THE FROZEN IMPL CANNOT SERVE AS THE WITNESS'S SECOND SUBJECT, and every reject
case therefore names a ``witness_reference``. The frozen program keeps a ``while``
loop under ``loom.semantics.choice "demonic"``, whose fixpoint elaborates through
``Classical.choice``; the kernel cannot unfold it, so ``decide`` against the
frozen tester is stuck for EVERY claim regardless of truth. Measured here with
real builds, and it is not a subtlety to wave through — the refutation
``... = false`` and the exact OPPOSITE claim ``... = true`` (which asserts the
rival is CORRECT at that input) both fail against the frozen solution with the
identical

    ... did not reduce to `isTrue` or `isFalse`

so the frozen-side exit code carries NO information and a forged witness
asserting agreement would clear both halves of the discrimination check. A
computable projection (route 1, the preferred repair) does not exist on this
carrier either: the extracted program returns ``DivM (List Nat)``, so a length or
element projection does not typecheck (``The environment does not contain
DivM.length``) and equating the whole ``DivM`` to ``DivM.res [...]`` fails to
synthesize a ``Decidable`` instance — every route to the value goes through the
loop's fixpoint.

So each reject case is refuted against ``_REFERENCE`` instead: the LOOP-FREE
closed form that implements this same frozen spec, and that the gate independently
checks both shares the spec and VERIFIES before using it as a subject (an impl the
verifier accepts cannot violate its own spec, so a genuine witness must still fail
there). ``pos-closed-form`` ships that identical source as an ``expect="verify"``
case, so the battery itself records that loop-freeness is not what any rival is
being rejected for. Measured out of band with ``scripts/lean_verify.sh``: the
reference VERIFIES (exit 0), each witness builds GREEN against its rival (exit 0),
and each fails against the reference by genuine refutation — ``Tactic `decide`
proved that the proposition ... is false``, a decided verdict rather than a stuck
one.

Every reject witness states its refutation at LITERAL inputs (no head binder, no
hypothesis), so no witness conditions on an opaque term and the consistency probe
is vacuous by construction.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
plumbing (the child's carried association, its grouping key, the key→parent map)
enters as the free inputs ``children`` / ``lookup`` — A-references the R/I legs
differential-test (G-CONF / G-AX's job), not consumed contracts. The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15280"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or is the whole prove_correct tactic block, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the batch. Reject rivals replace this with a loop-free closed form (so their
# tester reduces under `decide`); the loop-free positive control does too.
_IMPL = """    -- impl-start
    let mut result : List Nat := []
    let mut i : Nat := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant result = resolvedSeq lookup (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      -- A child carrying no association yet is associated with the parent its
      -- key maps to; a child that already carries one keeps it untouched.
      let parent : Nat :=
        match c.existingParent with
        | some p => p
        | none   => lookup c.key
      result := parent :: result
      i := i - 1
    return result
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The per-child match block; a positive control may reorder its arms while
# keeping the loop and the invariant, so only the proof body needs retuning.
_MATCH = """      let parent : Nat :=
        match c.existingParent with
        | some p => p
        | none   => lookup c.key"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    -- impl-start\n    let mut result : List Nat := []"

# The FULL frozen proof body. A positive control that reshapes the impl retunes
# THIS block (elided from the spec view); reject rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = """prove_correct linkChildrenToParents by
  loom_solve <;>
    first
    | -- loop-entry: drop children.length = [], the fold is nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full variant with ONLY the impl region body replaced (frozen proof kept —
    used for reject rivals, which are expected NOT to verify)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(old, new, new_proof):
    """Reshape an in-region anchor AND retune the tactic body (correct
    reshapes whose new impl no longer matches the frozen loop-tuned script)."""
    return _swap(_swap(_BASE, old, new), _PROOF, new_proof)


# ---------------------------------------------------------------------------
# _REFERENCE — the witness subject for the WHOLE reject lane.
#
# The frozen impl cannot be one: its `while` loop elaborates through
# Classical.choice under `loom.semantics.choice "demonic"`, so `decide` against
# the frozen tester is stuck for EVERY claim (see the module docstring for the
# measured control: the refutation and its exact opposite fail identically), and
# no computable projection exists because the extracted program returns
# `DivM (List Nat)`. This is the loop-free closed form of the SAME frozen spec —
# it shares the spec (only the elided impl/proof regions differ, asserted by
# _swap) and it VERIFIES, both of which the gate re-checks itself before refuting
# any witness against it. Identical source to the `pos-closed-form` positive, so
# the battery independently records that loop-freeness is not the reason any rival
# is rejected.
# ---------------------------------------------------------------------------
_REFERENCE = _impl_reproved(
    _IMPL,
    "    -- impl-start\n"
    "    return resolvedSeq lookup children\n"
    "    -- impl-end",
    "prove_correct linkChildrenToParents by\n  loom_solve")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `linkChildrenToParentsTester children lookup = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped.
def _tester(body):
    return ("extract_program_for linkChildrenToParents\n"
            "prove_precondition_decidable_for linkChildrenToParents\n"
            "prove_postcondition_decidable_for linkChildrenToParents\n"
            "derive_tester_for linkChildrenToParents\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each keeps the `ensures out = resolvedSeq lookup
    # children` obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating backward loop into the closed form the
        # post-image names directly. A completely different control-flow shape (no
        # loop, no accumulator, no drop-step lemma) computing the same batch image;
        # the loop-specific proof collapses to `loom_solve`.
        #
        # This is the SAME source every reject case names as its
        # `witness_reference` (_REFERENCE), shipped here as a first-class positive
        # so the battery records on its own that this impl VERIFIES against the
        # frozen spec — i.e. that loop-freeness is not what any rival is being
        # rejected for, and the reject lane's subject is a genuinely correct impl.
        "module": _REFERENCE,
        "rationale": "a loop-free impl that returns the batch image directly must "
                     "satisfy `out = resolvedSeq lookup children`; a correct reshape "
                     "of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Exercises the obligation from a "
                     "maximally different (loop-free) control-flow shape.",
    },
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: swap the two arms of the per-child match (carrying-none arm
        # first). Same value flow; the loop and the front-recursive invariant are
        # unchanged, so only the final `simp_all [resolveOne]` needs the extra
        # Option case-split to match the reordered arms.
        "module": _impl_reproved(
            _MATCH,
            "      let parent : Nat :=\n"
            "        match c.existingParent with\n"
            "        | none   => lookup c.key\n"
            "        | some p => p",
            "prove_correct linkChildrenToParents by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | (rw [List.drop_length]; simp)\n"
            "    | (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)];\n"
            "       simp_all [resolveOne];\n"
            "       cases (children[i - 1]?.getD default).existingParent <;> rfl)"),
        "rationale": "reordering the per-child match arms computes the same parent "
                     "value-for-value with the loop and invariant unchanged, so "
                     "`out = resolvedSeq lookup children` still holds; a correct "
                     "reshape must verify (else SPEC-TOO-STRONG on the branch order). "
                     "The reproof adds only an Option case-split to align the "
                     "reordered arms with `resolveOne`.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries no `require` clause, so the "a normal
    # input satisfies the precondition" probe is degenerate (every input is
    # in-domain). The residual risk on a total-domain spec is that the post-image
    # is DEGENERATE at the interesting point (a spec no impl distinguishes reads
    # like one every impl meets). This case discharges an in-region assert at
    # concrete inputs establishing that the per-child image really does DISTINGUISH
    # its two branches — a child carrying an association keeps it, a child carrying
    # none is looked up — and assembles the batch IN ORDER. The surrounding impl is
    # kept verbatim so the method's own obligation still discharges; the assert is
    # live (a false claim leaves an unsolved goal), and the proof gains one
    # `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-resolve-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            _IMPL_TOP,
            "    -- impl-start\n"
            "    assert (with_name_prefix `assert\n"
            "      (resolveOne (fun _ => 9) { key := 0, existingParent := some 5 } = 5 ∧\n"
            "       resolveOne (fun _ => 9) { key := 0, existingParent := none } = 9 ∧\n"
            "       resolvedSeq (fun _ => 9) [{ key := 0, existingParent := some 5 }, "
            "{ key := 1, existingParent := none }] = [5, 9]))\n"
            "    let mut result : List Nat := []",
            "prove_correct linkChildrenToParents by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [List.drop_length]; simp)\n"
            "    | (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)];\n"
            "       simp_all [resolveOne])"),
        "rationale": "the post-image is satisfiable AND non-degenerate at F2P-shaped "
                     "points: a child carrying an association keeps it "
                     "(`some 5 ↦ 5`), a child carrying none is associated with the "
                     "parent its key maps to (`none ↦ lookup key = 9`), and a mixed "
                     "batch is assembled in order (`[5, 9]`). The in-region assert "
                     "must discharge (else the image would be constant / the "
                     "obligation degenerate); the impl is kept verbatim so "
                     "`out = resolvedSeq lookup children` still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a DISTINCT
    # concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-overwrite-existing",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating delta (the pre-image behaviour). Associate EVERY child
        # with the parent its key maps to, unconditionally — never honouring a
        # pre-existing association. Correct on every child that carries none;
        # diverges on the carrying-an-association sub-domain, where the post-image
        # demands the child KEEP its existing parent.
        "module": _impl("    return children.map (fun c => lookup c.key)"),
        "refinement": "this is the literal pre-image behaviour: every child is "
                      "associated with the parent implied by its grouping key, "
                      "unconditionally, so a pre-existing (more specific) "
                      "association is discarded. Its faithful real counterpart is "
                      "the UNCHANGED repo, which still overwrites the "
                      "nested-prefetched parent — exactly the failing scenario the "
                      "issue adds (accessing the doubly-prefetched parent then "
                      "fires a query where none is expected) — so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolvedSeq lookup children` via "
                     "`resolveOne`'s `some p ↦ p` (keep-existing) branch: at a child "
                     "carrying `some p` the image demands `p`, but the rival returns "
                     "`lookup key`. If it verified the spec would be SPEC-TOO-WEAK "
                     "(the keep-existing guarantee unenforced). Refuted at a single "
                     "child carrying an association whose looked-up parent differs "
                     "(`existingParent = some`), the load-bearing behavior of the "
                     "fix.",
        "witness": _tester(
            "example : linkChildrenToParentsTester "
            "[{ key := 1, existingParent := some 5 }] (fun _ => 9) = false := by\n"
            "  decide\n"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-lookup",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual omission: honour a pre-existing association, but for a child
        # carrying none associate it with a fixed sentinel parent instead of the
        # one its key maps to — the mapping is never consulted. Correct on every
        # child carrying an association; diverges on the carrying-none sub-domain.
        "module": _impl("    return children.map (fun c => c.existingParent.getD 0)"),
        "refinement": "a counterpart that added the keep-existing guard but never "
                      "looked the parent up for a child carrying none — associating "
                      "it with a null/sentinel parent instead — leaves every "
                      "uncached child mis-linked, so accessing its parent yields the "
                      "wrong object (or fires a query). It fails every test that "
                      "asserts a child carrying none is linked to the parent its key "
                      "resolves to. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedSeq lookup children` via "
                     "`resolveOne`'s `none ↦ lookup key` branch: at a child carrying "
                     "`none` the image demands `lookup key`, but the rival returns "
                     "the sentinel `0`. If it verified the spec would be "
                     "SPEC-TOO-WEAK (the look-up obligation unpinned). Refuted at a "
                     "single child carrying none whose key maps to a nonzero parent "
                     "(`existingParent = none`), a distinct sub-domain from the "
                     "overwrite rival.",
        "witness": _tester(
            "example : linkChildrenToParentsTester "
            "[{ key := 2, existingParent := none }] (fun _ => 7) = false := by\n"
            "  decide\n"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-lookup-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the look-up branch: DOES consult the mapping for a child
        # carrying none, but at a FIXED key (0) rather than the child's own key.
        # Correct whenever the mapping is constant or the child's key is 0;
        # diverges only where the mapping separates the keys — refutable ONLY by
        # instantiating `lookup` at a non-constant function.
        "module": _impl(
            "    return children.map (fun c => match c.existingParent with\n"
            "      | some p => p\n"
            "      | none   => lookup 0)"),
        "refinement": "a counterpart that looked the parent up under the wrong "
                      "grouping key (a fixed key rather than the child's own) "
                      "associates uncached children with the wrong parent whenever "
                      "the key distinguishes them — every test with more than one "
                      "distinct parent key would link a child to the wrong object. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedSeq lookup children` via the "
                     "ARGUMENT of the look-up: `resolveOne` looks up the child's OWN "
                     "`key`, so a rival that looks up a constant key contradicts the "
                     "image at any child carrying none whose key ≠ 0 under a mapping "
                     "that separates them. Refuted with a NON-CONSTANT `lookup` "
                     "(`fun k => k`) — the only reject witness that moves the "
                     "`lookup` binder off a constant — at a child carrying none with "
                     "key 3.",
        "witness": _tester(
            "example : linkChildrenToParentsTester "
            "[{ key := 3, existingParent := none }] (fun k => k) = false := by\n"
            "  decide\n"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-batch-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Structural rival: compute the correct per-child image but emit the batch
        # in REVERSED order. Correct on every batch of length ≤ 1 (and any batch
        # whose image is a palindrome); diverges on the batch-order clause.
        "module": _impl(
            "    return (children.map (fun c => match c.existingParent with\n"
            "      | some p => p\n"
            "      | none   => lookup c.key)).reverse"),
        "refinement": "a counterpart that linked the children in reversed batch "
                      "order associates each child with another child's parent "
                      "(shifted by the reversal) whenever the batch holds more than "
                      "one distinct parent — corrupting the reverse-relation "
                      "bookkeeping so children point at the wrong parents. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = resolvedSeq lookup children`, which pins the "
                     "output IN BATCH ORDER: on a length-2 batch whose two resolved "
                     "parents differ, the reversed output contradicts the image "
                     "element-wise. If it verified the spec would be SPEC-TOO-WEAK "
                     "(the batch order unpinned). Refuted at a two-child batch of "
                     "distinct pre-existing parents (varying the `children` binder "
                     "to length 2 — the only reject witness with a multi-element "
                     "batch).",
        "witness": _tester(
            "example : linkChildrenToParentsTester "
            "[{ key := 0, existingParent := some 1 }, { key := 0, existingParent := some 2 }] "
            "(fun _ => 0) = false := by\n"
            "  decide\n"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 2 mandatory frame-mutation rivals, 3
# uniqueness/partial-domain + control-flow rivals) and 0 AXIOM_TESTS. The sibling
# contracts a VOID mutator `link_children_to_parents(slot_full, slot_value,
# supplied)` over THREE parallel `List[int]` inputs carrying fractional heap
# permissions (`slot_value` full, `slot_full`/`supplied` at 1/2), pinning the
# per-child post-state `slot_value[k] == linked_parent(slot_full[k],
# Old(slot_value[k]), supplied[k])` under a 0/1-occupancy precondition. This
# backend models the same decision as a referentially-transparent FUNCTION
# `linkChildrenToParents (children) (lookup) return out`, with the per-child image
# the pure `resolveOne`/`resolvedSeq`: the occupancy flag + old value collapse to
# `Child.existingParent : Option Nat` (`some p` = populated, keep p; `none` =
# empty), the supplied-parent source to the free mapping `lookup`, and the whole
# post-state to a fresh output list. The value surface carries across intact; the
# permission surface, the mutation, and the 0/1-occupancy precondition do not
# exist here.
#
#   sibling case             kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------
#   pos-reverse-descending   soundness     -> pos-closed-form               PORTED (reshaped)
#                                          -> pos-arms-reordered            ADDED
#   admiss-mixed-collection  admissibility -> admiss-resolve-nondegenerate  RE-AIMED
#   frame-mutate-supplied    uniqueness    -> (none)                        VACUOUS
#   frame-mutate-slot_full   uniqueness    -> (none)                        VACUOUS
#   uncond-overwrite-prepatch uniqueness   -> weak-overwrite-existing       PORTED
#   partial-invert-guard     uniqueness    -> weak-overwrite-existing       SUBSUMED
#   partial-skip-last        uniqueness    -> weak-batch-order-reversed     RE-AIMED
#   (no sibling)             uniqueness    -> weak-drop-lookup              ADDED (binder cov.)
#   (no sibling)             uniqueness    -> weak-lookup-wrong-key         ADDED (binder cov.)
#
# PORTED-RESHAPED (pos-reverse-descending -> pos-closed-form + pos-arms-reordered):
#   the sibling's positive control walks the batch in DESCENDING index order,
#   mirroring every loop invariant/assert for the reverse walk. This backend's
#   frozen impl ALREADY walks backward (i = length .. 1), so the sibling's exact
#   descending-reshape is the frozen shape itself. The reshape SPIRIT —
#   "structurally different, behaviourally identical, must verify" — is carried by
#   pos-closed-form (collapse the loop to the closed form the post-image names) and
#   pos-arms-reordered (reorder the per-child match arms, keeping the loop). Both
#   verified (lean_verify EXIT 0).
# RE-AIMED (admiss-mixed-collection -> admiss-resolve-nondegenerate): the sibling
#   self-calls on an F2P-shaped mixed collection (one populated slot, one empty) to
#   show the 0/1-occupancy precondition ADMITS a normal input. This backend's
#   method has NO precondition and no occupancy constraint, so that probe is
#   degenerate (every input is in-domain). Re-aimed at the residual total-domain
#   risk — a degenerate post-image — via an in-region assert that the per-child
#   image genuinely distinguishes its two branches (keep-existing vs look-up) and
#   assembles the mixed batch (one carrying an association, one carrying none) in
#   order. Verified EXIT 0.
# VACUOUS (frame-mutate-supplied, frame-mutate-slot_full): the sibling's two
#   MANDATORY frame-mutation rivals keep the gold body verbatim then WRITE back
#   into a read-only sequence input granted only at half permission
#   (`supplied[i] = ...` / `slot_full[i] = 1`), each rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: every parameter is an
#   immutable value, the method declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system to
#   trip, so the whole class is vacuous. No substitute is fabricated (per the
#   porting map).
# PORTED (uncond-overwrite-prepatch -> weak-overwrite-existing): the sibling's
#   canonical uniqueness probe drops the occupancy guard and writes `supplied[i]`
#   unconditionally — the pre-patch bug that clobbers a populated slot. Ports
#   directly: `children.map (fun c => lookup c.key)` associates EVERY child by its
#   key, discarding a pre-existing association. Refuted at a child carrying `some`.
# SUBSUMED (partial-invert-guard): the sibling INVERTS the guard sense — write when
#   ALREADY populated, skip empty. Its "write the more-specific populated slot"
#   half IS the overwrite of a pre-existing association that weak-overwrite-existing
#   already refutes at a `some`-carrying child; its "skip empty" half (leave the
#   old value) has no analogue on a carrier with no `Old` pre-state — the functional
#   image of a `none` child is `lookup key`, attacked instead by weak-drop-lookup.
#   The two ADDED rivals below cover both halves at their own binder points.
# RE-AIMED (partial-skip-last -> weak-batch-order-reversed): the sibling's
#   partial-domain rival diverges only on the LAST index (skip the guarded write
#   when i == len-1), attacking the per-index Forall on a sub-domain that is correct
#   for shorter/other batches. This backend has no per-index side-effect to skip;
#   the analogous partial-domain, correct-on-short-batches / wrong-on-longer attack
#   on the SEQUENCE structure is a reversed batch order — correct on every batch of
#   length ≤ 1, wrong on a multi-element batch. It attacks the batch-order clause of
#   `resolvedSeq` (which no value rival touches), refuted at a length-2 batch.
# ADDED (2 binder-coverage rivals): the sibling's `linked_parent(was_full, old,
#   supplied)` folds keep-vs-lookup into scalar flags, so a single rival could not
#   independently abuse the look-up mechanism. This backend's `resolveOne` exposes
#   the look-up as `lookup c.key` — a mapping applied to the child's OWN key — so
#   two independent look-up defects get their own rival:
#     weak-drop-lookup      — never consults the mapping for a `none` child
#                             (attacks the `none ↦ lookup key` branch's EXISTENCE);
#     weak-lookup-wrong-key — consults the mapping at a FIXED key, not the child's
#                             own (attacks the branch's ARGUMENT — refutable ONLY by
#                             a NON-CONSTANT `lookup`, so it moves that binder).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (pts = 4 distinct input points):
#     children.existingParent — some (overwrite, batch-order-reversed), none
#                               (drop-lookup, wrong-key): BOTH branches attacked.
#     children.key            — 1 / 2 / 3 / 0: varied (never held fixed).
#     children (length/order) — 1 (overwrite, drop-lookup, wrong-key), 2
#                               (batch-order-reversed): the order clause exercised.
#     lookup                  — constant (overwrite `_↦9`, drop-lookup `_↦7`,
#                               batch-order `_↦0`) and NON-CONSTANT (`fun k => k`,
#                               wrong-key): the free mapping is moved off a constant,
#                               which is the only way the wrong-key argument defect
#                               is observable.
#   Every independent top-level behavior of the post-image is attacked: the
#   keep-existing branch (overwrite), the look-up branch's existence (drop-lookup)
#   and argument (wrong-key), and the batch order (batch-order-reversed).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (the unchanged plumbing enters as free inputs, an A-reference
# validated there), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
