"""properties.py — G-PBT falsification battery for pydata__xarray-4629 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct combineFirst`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE. One contracted method that combines a non-empty sequence of
mapping objects under the "take the first object's contents" policy, returning
an object of its OWN — distinct from every input, carrying exactly the first
input's contents, and leaving every input object untouched:

  combineFirst (mut store : Handle → Entries) (mut fresh : Handle)
      (sources : List Handle)  return (result : Handle)
    require sources ≠ []                                          (R1)
    require ∀ h, h ∈ sources → h < fresh                          (R2)
    ensures store result = storeOld (sources.head!)               (E1)
    ensures result ∉ sources                                      (E2)
    ensures ∀ h, h ∈ sources → store h = storeOld h               (E3)
    ensures result = freshOld                                     (E4)
    ensures fresh = freshOld + 1                                  (E5)

CARRIER — object identity as a heap. A mapping object is a ``Handle`` (an
``Int``) into a ``store : Handle → Entries`` giving each live object's current
contents; ``fresh : Handle`` is the next never-allocated handle, and R2 pins the
bump-allocator invariant (every live source sits below ``fresh``). Allocating a
fresh object is ``result := fresh`` + a ``Function.update store fresh …`` binding
its contents + ``fresh := fresh + 1``. Returning an existing handle SHARES
(aliases) that object; a later update through the returned handle is then seen
through the source — which is the reported defect. Both ``store`` and ``fresh``
are ``mut``, so E3 is a genuine value-level FRAME clause on the mutable heap
(directive 5): it is FALSE of an impl that writes through a source handle.

FIVE independent, load-bearing top-level ``ensures`` clauses over THREE input
binders (``store``, ``fresh``, ``sources``):
  * E1 the CONTENTS — the result object carries the first source's contents.
  * E2 the FRESHNESS — the result is not any input object (the identity the
    fix establishes; false for the aliasing pre-patch).
  * E3 the FRAME — every input object's contents are preserved (no write through
    a source handle). A value-level frame on the mutable ``store``.
  * E4 the ALLOCATION — the returned handle IS the pre-state ``fresh``.
  * E5 the BUMP — the allocator advances by exactly one.
Everything is grounded in the method's own inputs (``store``, ``fresh``,
``sources.head!``); the ``axioms`` region is empty, so there is no opaque answer
key to echo (directive 8).

CARRIER NOTE — the frame clause E3 quantifies ``∀ h : Handle`` over a total
function ``store : Handle → Entries``, so the frame conjunct is not decidable by
evaluation at an arbitrary point. Two consequences shape every witness:

  * The ``…Tester args = false`` route is nonetheless AVAILABLE here, and the
    earlier claim in this file that it was not has been corrected after being
    measured: ``extract_program_for combineFirst`` followed by
    ``derive_tester_for combineFirst`` elaborates (exit 0) and yields
    ``combineFirstTester : (Handle → Entries) → Handle → List Handle → Bool``,
    which ``decide`` reduces — ``combineFirstTester (fun _ => [("x","0")]) 5 [0]
    = false`` builds against the aliasing rival and fails on the frozen solution
    with ``decide proved that the proposition … is false``. The witnesses below
    keep the projection route by CHOICE, not by necessity: a tester refutation
    reports only "some clause fails here", whereas a projection names the
    clause, so each rival's witness pins the specific ``ensures`` it breaks.
  * The post-state is concrete: the returned triple ``(result, store,
    fresh)`` READ at one probe point is a decidable value. Each witness
    ``extract_program_for``s the rival (extraction needs no decidability — it
    just names ``combineFirstExec``) and states, at ONE concrete input, that a
    projection of the rival's post-state differs from what E1–E5 demand:

        ((combineFirstExec store fresh sources).run).1              -- result (E2/E4)
        ((combineFirstExec store fresh sources).run).2.1 <handle>   -- store  (E1/E3)
        ((combineFirstExec store fresh sources).run).2.2            -- fresh  (E5)

    discharged by ``simp [NonDetT.run, DivM.run, Function.update]``. The frozen
    impl allocates a fresh handle and copies contents in place, so the SAME probe
    reads the correct/preserved value there and the witness FAILS on gold — a
    genuine discriminator, not a tautology. Every witness binds NO hypotheses
    (all inputs are concrete literals / ``fun _ => …`` stores), so the
    consistency probe is trivially satisfiable; no opaque-term conditioning is
    needed.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS positives — APPLY. Structurally different but CORRECT impls (name
    the copied contents in a local; derive the next-fresh from the allocated
    handle) that MUST verify, else SPEC-TOO-STRONG. Each keeps the fresh-alloc /
    in-place-copy shape so the frozen tactic script still closes.
  * ADMISSIBILITY — APPLIES (unlike the matplotlib sibling, this method HAS a
    precondition). ``admiss-f2p`` discharges an in-region ``assert`` that the F2P
    -shaped input (a one-element ``sources`` below ``fresh``) satisfies R1/R2 and
    that the allocated handle is distinct from that source — so a normal
    merge(['override']) call is admitted (else PRECOND-TOO-STRONG). The impl is
    kept verbatim so E1–E5 still discharge; the proof gains a ``decide`` arm.
  * FRAME / PERMISSION-MUTATION (the nagini MANDATORY rivals) — the permission
    MECHANISM is vacuous (Velvet is referentially transparent: no fractional
    ``Acc(list_pred(…),1/2)`` to trip), BUT the BEHAVIOUR those rivals guarded —
    a write through a read-only source object must be refused — is NOT lost. It
    is captured directly by the value-level frame clause E3 on the mutable
    ``store`` and is attacked by ``frame-write-source`` below. So the mechanism
    is vacuous; the behaviour is fully expressible and exercised (see footer).
  * DIVERGENCE / NON-TERMINATION — no nagini divergence case exists here to port,
    and the frozen impl is loop-free; nothing to record on this cell.
  * PARTIAL-DOMAIN / IDENTITY — carry the reject lane: the aliasing pre-patch
    (E2/E4), a write through the source (E3), an empty copy (E1 on a non-empty
    source), a copy short one entry (E1), and a missing allocator bump (E5).

WITNESS PLACEMENT. The five reject witnesses sit at FIVE DISTINCT input points,
varying every binder: ``sources`` over one-element lists at handles {0,1,2,3},
``fresh`` over {4,5,6,7,9}, and ``store`` over {three different one-entry maps,
a two-entry map}. Each of the five clauses is attacked by some rival. No binder
is pinned at a single value across the reject set (pts=5 — and this is now
literally true: ``empty-copy`` previously shared ``alias-return``'s
``(store,fresh,sources)`` tuple, which made the honest count pts=4, so its
witness was moved to ``(one-entry [("k","9")], 6, [2])``, a point no other case
occupies).

MEASURED SPEC LIMIT (documented, not patched — a spec change is out of this
lane). E3 frames only handles ``h ∈ sources``, and E1/E2/E4 constrain only the
returned handle, so NOTHING in E1–E5 constrains ``store`` at a handle that is
neither a source nor the result. An impl that does the gold allocate-and-copy
and ALSO scribbles on a never-allocated handle therefore satisfies the whole
obligation. Measured, not argued: adding
``store := Function.update store (fresh + 100) []`` to the frozen body VERIFIES
(exit 0) once the frozen script's ``simp`` arms are given the two disequalities
(``h ≠ freshOld + 100`` from ``h < freshOld``; ``freshOld ≠ freshOld + 100``);
the same rival under the frozen script alone fails only with ``simp made no
progress``, i.e. for a TACTIC reason, which is why the outcome has to be
re-measured with a retuned proof before it means anything.

This is a real gap in the spec's expressive reach, but it is NOT a defect that
this battery can or should close: writing to a handle at or above ``fresh``
corresponds to touching an object the allocator has not handed out, which has no
counterpart in the modeled operation (there is no such live object to corrupt),
and G-CONF's shadow only ever reads the three observable consequences. The
bounded frame ("every live object other than the result is preserved") would
need an extra ``ensures`` over a liveness predicate the carrier does not carry —
a FROZEN-SPEC change, which must re-clear the equivalence and leakage gates. So
it is recorded here as a limit of the model rather than smuggled in as a rival
whose rejection this spec cannot actually deliver. The neighbouring case that
DOES bite is checked and does bite: writing to ``fresh - 1`` (a handle that may
be a live source) is REJECTED, so the frame is enforced exactly where the
carrier can see liveness.

AXIOM lane: EMPTY. This bundle declares no ``axiom`` (the object-copy operation
is modeled DEEPLY by the allocate-fresh + copy-contents sequence, an A-reference
validated by G-AX, not a consumed axiom — mapping.md §3.2), so there is nothing
here for this gate to probe and it ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4629"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (marker lines included);
# ---- lies wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    let result := fresh\n"
    "    store := Function.update store fresh (store sources.head!)\n"
    "    fresh := fresh + 1\n"
    "    return result\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- the `-- impl-start` marker line (unique); the admissibility case inserts
# ---- an in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- proof-body anchor. The frozen tactic script is elided from the consumer
# ---- spec view (only the obligation header is kept), so a positive control or
# ---- the admissibility case may retune it without touching the spec or dropping
# ---- the obligation. Unique in the file.
_GOLD_PROOF = (
    "prove_correct combineFirst by\n"
    "  loom_solve\n"
    "  all_goals (\n"
    "    try (intro h hmem)\n"
    "    -- a handle differs from the freshly-allocated one iff it is an input handle\n"
    "    first\n"
    "    | (simp [Function.update_self])\n"
    "    | (have hlt : h < freshOld := require_1 h hmem\n"
    "       simp [Function.update_of_ne (ne_of_lt hlt)]))"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"

# A proof that ALSO clears an in-region `assert` VC (decidable), keeping the
# frozen arm for the five method obligations. Used by the admissibility case.
_PROOF_WITH_DECIDE = (
    "prove_correct combineFirst by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | decide\n"
    "    | (try (intro h hmem)\n"
    "       first\n"
    "       | (simp [Function.update_self])\n"
    "       | (have hlt : h < freshOld := require_1 h hmem\n"
    "          simp [Function.update_of_ne (ne_of_lt hlt)]))"
)


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced (frozen proof
    kept — used by rivals, whose rejection is carried by the witness)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the proof retuned (correct reshapes keep the frozen
    proof via _impl; this is for the admissibility assert's extra `decide` arm)."""
    return _swap(_impl(body), _GOLD_PROOF, new_proof)


# ---- witness preamble. Reaches the rival's extracted program (extraction needs
# ---- no decidability — it just names `combineFirstExec`) and states, at one
# ---- concrete input, that a projection of the rival's returned post-state
# ---- differs from what the postcondition demands. Discriminated by a decidable
# ---- read of the returned `(result, store, fresh)` triple; checked in a file
# ---- whose `prove_correct` block is stripped. No `axiom`/`sorry`/`native_decide`.
def _witness(claim):
    return (
        "extract_program_for combineFirst\n\n"
        f"example : {claim} := by\n"
        "  unfold combineFirstExec combineFirst\n"
        "  simp [NonDetT.run, DivM.run, Function.update]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify; else the spec is SPEC-TOO-STRONG. Each keeps the
    # fresh-allocate + in-place-copy shape (so E1–E5 still discharge) and only
    # reshapes the executable surface, so the frozen tactic script still closes.
    # =====================================================================
    {
        "id": "pos-name-contents-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the first source's contents in a local BEFORE allocating.
        # Same value flow (the copied contents are read from the pre-state store
        # exactly once, as in gold), so all five clauses hold on every input and
        # the frozen proof still closes.
        "module": _impl(
            "    let contents := store sources.head!\n"
            "    let result := fresh\n"
            "    store := Function.update store fresh contents\n"
            "    fresh := fresh + 1\n"
            "    return result"),
        "rationale": "naming the first source's contents in a local before the "
        "in-place copy leaves the written contents and the frame identical, so "
        "E1–E5 are unchanged and the frozen proof closes. A correct reshape must "
        "verify, else SPEC-TOO-STRONG on the shape of the copy. (Sibling: "
        "pos-reorder — a structurally-different correct impl.)",
    },
    {
        "id": "pos-derive-fresh-from-result",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: derive the bumped allocator from the allocated handle
        # (`fresh := result + 1`) and copy into `result` rather than `fresh`,
        # reordering the bump before the copy. `result = freshOld` still holds,
        # `fresh = freshOld + 1` still holds, and the copy targets the same
        # handle, so all five clauses and the frozen proof are unaffected.
        "module": _impl(
            "    let result := fresh\n"
            "    fresh := result + 1\n"
            "    store := Function.update store result (store sources.head!)\n"
            "    return result"),
        "rationale": "deriving the next allocator value from the allocated handle "
        "(`fresh := result + 1`) and reordering the bump before the in-place copy "
        "leaves every post-state identical (the copy still targets the allocated "
        "handle, `fresh` still advances by one), so E1–E5 discharge under the "
        "frozen script. If it failed to verify the spec would be SPEC-TOO-STRONG "
        "on statement order. (Sibling: pos-reorder, a second control-flow "
        "reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY — this method HAS a precondition (R1 `sources ≠ []`, R2 the
    # bump-allocator invariant), so the sibling's "a normal F2P-shaped input
    # satisfies the precondition" probe ports directly. This case discharges an
    # in-region assert, at the F2P-shaped input (a one-element `sources` at a
    # handle below `fresh` — the merge(['override']) shape with one leading
    # source object), that R1 AND R2 hold there AND that the allocated handle is
    # distinct from that source (the freshness the fix turns on). The assert is
    # LIVE (a false conjunct leaves an unsolved goal — verified). The impl is
    # kept verbatim so E1–E5 still discharge; the proof gains a `decide` arm.
    # =====================================================================
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `adm (\n"
            "      ([(0 : Handle)] ≠ []) ∧\n"
            "      (∀ h, h ∈ ([(0 : Handle)]) → h < (1 : Handle)) ∧\n"
            "      ((1 : Handle) ∉ ([(0 : Handle)]))))\n"
            "    let result := fresh\n"
            "    store := Function.update store fresh (store sources.head!)\n"
            "    fresh := fresh + 1\n"
            "    return result",
            _PROOF_WITH_DECIDE),
        "rationale": "the precondition admits the F2P-shaped input: a one-element "
        "`sources` [0] with the leading source object below `fresh` (1) satisfies "
        "R1 (`sources ≠ []`) AND R2 (`∀ h ∈ sources → h < fresh`), and the handle "
        "the allocator hands out (1) is distinct from that source (`1 ∉ [0]`) — "
        "the freshness the modeled branch establishes. The in-region assert must "
        "discharge (else the precondition would be unsatisfiable for a normal "
        "input — PRECOND-TOO-STRONG); the impl is kept verbatim so E1–E5 still "
        "discharge too. (Sibling: admiss-f2p.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a reshaped impl carrying a machine-checked
    # refutation witness at a DISTINCT concrete input (discriminated by a
    # decidable read of the returned triple) and the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "alias-return",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch: return the leading source object itself instead of a
        # fresh copy. Contents (E1) hold trivially, but E2 (result ∉ sources) and
        # E4 (result = freshOld) are false — the returned handle IS an input
        # handle, not the freshly-allocated one. Also E5 (no allocation happened).
        "module": _impl(
            "    let result := sources.head!\n"
            "    return result"),
        "refinement": "this is the pre-patch behaviour: the leading source object "
        "is handed back directly, so the returned object IS a source object. The "
        "failing scenario mutates the combined object's contents and asserts the "
        "leading source is untouched, but the alias makes the source's contents "
        "change too — exactly the bug the change fixes, so it does NOT resolve.",
        "rationale": "REJECT from E2 (`result ∉ sources`) and E4 (`result = "
        "freshOld`): the returned handle is `sources.head!`, an input handle, not "
        "the freshly-allocated one. Verifying would be SPEC-TOO-WEAK (the "
        "freshness/allocation of the result unpinned). Refuted at sources=[0], "
        "fresh=5, where the result must be the fresh handle 5 but the rival "
        "returns 0. (Sibling: alias-return.)",
        "witness": _witness(
            '((combineFirstExec (fun _ => [("x","0")]) 5 [0]).run).1 = 0'),
    },
    {
        "id": "frame-write-source",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME-MUTATION (the nagini MANDATORY rival, on the value-level carrier):
        # allocate a fresh handle correctly, but ALSO overwrite the leading source
        # object's contents (blank it). E1/E2/E4/E5 all hold; E3 — the frame on
        # the mutable store — is violated at the source handle.
        "module": _impl(
            "    let result := fresh\n"
            "    store := Function.update store fresh (store sources.head!)\n"
            "    store := Function.update store sources.head! []\n"
            "    fresh := fresh + 1\n"
            "    return result"),
        "refinement": "a real patch that produced the copy by clearing then "
        "refilling the leading source object in place would corrupt that source's "
        "contents (and, if it returned the source, still alias it). The failing "
        "scenario asserts the leading source is untouched after the merge; a "
        "patch that writes through the source fails it — it would NOT resolve. "
        "(This is the on-carrier analogue of the nagini permission-mutation "
        "rival: the fractional-permission MECHANISM is vacuous under referential "
        "transparency, but the behaviour it guarded is pinned by the frame clause "
        "E3 and attacked here.)",
        "rationale": "REJECT from E3 (`∀ h ∈ sources → store h = storeOld h`): the "
        "rival writes through the leading source handle, so that input object's "
        "contents change. Verifying would be SPEC-TOO-WEAK (the read-only frame "
        "on the source objects unenforced). Refuted at sources=[3], fresh=9, "
        "where the preserved source 3 must keep its contents but the rival blanks "
        "it to []. (Sibling: frame-write-source — the MANDATORY frame rival.)",
        "witness": _witness(
            '((combineFirstExec (fun _ => [("x","0")]) 9 [3]).run).2.1 3 = []'),
    },
    {
        "id": "empty-copy",
        "kind": "uniqueness",
        "expect": "reject",
        # The result is a FRESH distinct object (E2/E4/E5 hold) but its contents
        # are EMPTY rather than the source's. Correct on an empty leading source;
        # diverges on every non-empty one (the F2P's {"x":0}). Attacks E1
        # (contents) independently of the identity clauses.
        "module": _impl(
            "    let result := fresh\n"
            "    store := Function.update store fresh []\n"
            "    fresh := fresh + 1\n"
            "    return result"),
        "refinement": "a real patch whose override branch returned a fresh EMPTY "
        "mapping would make the merged product carry none of the leading source's "
        "attributes; the scenario that reads the merged object's attribute and "
        "the P2P override-attrs tests that assert the leading source's attrs are "
        "present would fail — it would NOT resolve. Correct only on an empty "
        "leading source.",
        "rationale": "REJECT from E1 (`store result = storeOld (sources.head!)`): "
        "the fresh object is bound to `[]` rather than the source's contents. "
        "Verifying would be SPEC-TOO-WEAK (the copied CONTENTS unpinned — it "
        "would say only that the result is fresh, not that it carries the right "
        "data). Refuted at sources=[2], fresh=6 with a one-entry source, where "
        "the result's contents must equal that entry but the rival gives []. "
        "(Sibling: empty-copy.)",
        # Stated at (store,fresh,sources) = (one-entry [("k","9")], 6, [2]) —
        # a point NO other reject case uses, so the five reject witnesses sit at
        # five genuinely distinct input tuples rather than four. Rebuilt: holds
        # of the rival (exit 0), fails on the frozen solution (exit 1,
        # `unsolved goals ⊢ False`), and the flipped claim inverts both exit
        # codes, so gold's code tracks the claim.
        "witness": _witness(
            '((combineFirstExec (fun _ => [("k","9")]) 6 [2]).run).2.1 6 '
            '= ([] : Entries)'),
    },
    {
        "id": "skip-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the contents: the fresh object carries the source's
        # contents MINUS the last entry (`dropLast`). Fresh/distinct (E2/E4/E5)
        # and content-equal on a 0/1-entry source, but a proper prefix on any
        # source of length ≥ 2 — a faithful copy on a strict sub-domain only.
        "module": _impl(
            "    let result := fresh\n"
            "    store := Function.update store fresh ((store sources.head!).dropLast)\n"
            "    fresh := fresh + 1\n"
            "    return result"),
        "refinement": "a real patch that copied all but the last attribute of the "
        "leading source (e.g. `dict(list(d.items())[:-1])`) would drop the final "
        "attribute from the merged product; the P2P override-attrs tests that "
        "compare the merged attrs to a multi-entry source would find it missing "
        "— it would NOT resolve. Correct on a 0/1-entry source only.",
        "rationale": "REJECT from E1 (`store result = storeOld (sources.head!)`): "
        "the copy must reproduce the WHOLE contents, but `dropLast` is a proper "
        "prefix on any source of length ≥ 2. This is the sub-domain no other "
        "rival probes — it exercises a TWO-entry source (a near-miss of "
        "empty-copy that agrees with gold on more of the domain, so it gets its "
        "own discriminating witness). Refuted at sources=[2], fresh=7 with a "
        "two-entry source, where the result must carry both entries but the rival "
        "keeps only the first. (Sibling: skip-last.)",
        "witness": _witness(
            '((combineFirstExec (fun _ => [("a","1"),("b","2")]) 7 [2]).run).2.1 7 '
            '= ([("a","1")] : Entries)'),
    },
    {
        "id": "no-bump",
        "kind": "uniqueness",
        "expect": "reject",
        # The allocator does NOT advance: everything else is correct (fresh copy,
        # right contents, right result handle) but `fresh` is left unchanged.
        # E1/E2/E3/E4 all hold; only E5 (fresh = freshOld + 1) is violated. Isolates
        # the allocator-bump clause — a rival that forgot to bump would leak the
        # same handle to the next allocation, aliasing two "fresh" objects.
        "module": _impl(
            "    let result := fresh\n"
            "    store := Function.update store fresh (store sources.head!)\n"
            "    return result"),
        "refinement": "a real patch whose allocator did not advance would hand the "
        "SAME identity to the next constructed object, so two objects that must be "
        "distinct would alias; the next merge would then see its result "
        "overwritten by a later allocation and the identity-preservation "
        "scenarios would fail — it would NOT resolve. Correct on the single-"
        "allocation observation of one call, but the allocator invariant is "
        "broken for the next.",
        "rationale": "REJECT from E5 (`fresh = freshOld + 1`): the allocator is "
        "left unchanged. Verifying would be SPEC-TOO-WEAK (the bump — the "
        "invariant that keeps future allocations fresh — unpinned; it is the sole "
        "clause this rival violates). Refuted at sources=[1], fresh=4, where "
        "`fresh` must become 5 but the rival leaves it 4. (No direct sibling: the "
        "nagini carrier tracks freshness through fractional permission rather "
        "than an explicit allocator, so this clause is new to the deep model — "
        "ADDED to attack E5.)",
        "witness": _witness(
            '((combineFirstExec (fun _ => [("m","1")]) 4 [1]).run).2.2 = 4'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 8 SPEC cases (1
# soundness positive `pos-reorder`, 1 admissibility `admiss-f2p`, 6 uniqueness
# rivals — two of them MANDATORY frame-mutation rivals `frame-write-source` /
# `frame-write-outer`) plus an EMPTY axiom lane (AXIOM_TESTS = []). The nagini
# sibling contracts `combine_attrs(variable_attrs: List[List[int]], mode) ->
# List[int]` over a full-permission returned list with fractional (1/2)
# permissions on BOTH inputs, and observes object identity through Nagini
# reference identity + the permission discipline. This backend models the SAME
# "take the first object's contents" branch DEEPLY as a heap: `store : Handle →
# Entries` + a bump allocator `fresh`, so object identity/freshness is a
# value-level property (E2/E4/E5) and the read-only-input frame is a value-level
# frame clause (E3) rather than a permission fact. The DROP policy branch is NOT
# modeled here (mapping.md §1: the modeled method is restricted to the override
# branch the issue is about), which narrows two nagini cases away.
#
#   nagini case            kind          -> here                         disposition
#   ------------------------------------------------------------------------------------
#   pos-reorder            soundness     -> pos-name-contents-local       RE-SHAPED
#                                            (+ pos-derive-fresh-from-result ADDED)
#   admiss-f2p             admissibility -> admiss-f2p                    PORTED
#   frame-write-source     uniqueness    -> frame-write-source           PORTED (value-frame)
#   frame-write-outer      uniqueness    -> (none)                       VACUOUS-CARRIER
#   alias-return           uniqueness    -> alias-return                 PORTED
#   drop-nonempty          uniqueness    -> (none)                       VACUOUS (DROP unmodeled)
#   skip-last              uniqueness    -> skip-last-entry              PORTED
#   empty-copy             uniqueness    -> empty-copy                   PORTED
#   (no nagini counterpart)-> no-bump                                    ADDED (attacks E5)
#   AXIOM_TESTS (none)     axiom         -> (none)                       N/A (G-AX)
#
# 4 uniqueness ported, 1 admissibility ported, 1 soundness re-shaped + 1 added,
# 1 uniqueness added (no-bump); 2 uniqueness omitted (frame-write-outer vacuous,
# drop-nonempty out of the modeled branch). Axiom lane empty (nothing to port).
#
# RE-SHAPED / ADDED (positives): the nagini positive is a branch reorder over the
#   mode tag. This backend does not model the DROP branch, so there is no branch
#   to reorder; the on-carrier analogues are two fresh-allocate + in-place-copy
#   reshapes — naming the copied contents in a local (pos-name-contents-local)
#   and deriving the next allocator value from the allocated handle
#   (pos-derive-fresh-from-result). Both keep the fresh-alloc/copy shape so the
#   frozen tactic script closes; verified with scripts/lean_verify.sh.
# PORTED (frame-write-source): the nagini MANDATORY rival writes to the read-only
#   leading source held at Acc(list_pred(variable_attrs[0]),1/2), rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent — no
#   fractional permission to trip — but the BEHAVIOUR (a write through the source
#   object must be refused) is pinned by the value-level frame clause E3 on the
#   mutable `store`, and the rival that overwrites the source's contents is
#   refuted at that clause. The permission MECHANISM is vacuous; the behaviour is
#   fully exercised. This is the matplotlib__matplotlib-20826 pattern
#   (permission-mutation -> value-frame drop rival), NOT the django-10554 pattern
#   (frame genuinely vacuous because the input is a read-only immutable value).
# VACUOUS-CARRIER (frame-write-outer): the nagini rival WRITES to the outer
#   read-only collection `variable_attrs` (appends a mapping), rejected for
#   INSUFFICIENT PERMISSION on the collection. On this carrier the outer
#   collection is the `sources : List Handle` input, declared READ-ONLY (not
#   `mut`): it is an immutable Lean value with no heap identity and no permission,
#   so there is no outer collection to overwrite and no frame clause on it to
#   violate. The class has no carrier analogue (the abstraction models the source
#   collection as an immutable value, not a mutable object), so it is DROPPED
#   rather than faked — a genuine carrier fact, per the porting map. The source
#   OBJECTS' contents (the observable half of the read-only-input behaviour) are
#   instead framed by E3 and attacked by frame-write-source.
# VACUOUS (drop-nonempty): the nagini rival ignores the mode tag and returns a
#   content-equal copy for the DROP mode, rejected by the DROP postcondition
#   `Implies(mode==DROP, len(Result())==0)`. This backend models ONLY the
#   "take the first" (override) branch (mapping.md §1: the DROP branch already
#   returned `{}` before the patch and is outside the changed behaviour), so
#   there is no `mode` binder and no DROP postcondition in the spec to attack.
#   The class has no counterpart on the narrowed surface, so it is DROPPED and
#   reported rather than fabricated.
# ADDED (no-bump): the deep model makes freshness explicit through a bump
#   allocator (`fresh := fresh + 1`), a clause (E5) with no nagini counterpart
#   (nagini tracks the fresh identity through fractional permission, not an
#   explicit counter). Without a rival attacking E5, an impl that forgot to
#   advance the allocator — leaking the same identity to the next allocation —
#   would verify, so no-bump is added to defend that clause.
#
# CLAUSE / BINDER COVERAGE. All FIVE independent top-level `ensures` clauses are
#   attacked: E1 by empty-copy AND skip-last-entry (the empty and short-by-one
#   directions of the contents violation); E2 by alias-return; E3 by
#   frame-write-source; E4 by alias-return; E5 by no-bump. All five are defended
#   by the two positive controls and the admissibility case (the impl is kept
#   verbatim there, so E1–E5 discharge). The five reject witnesses probe FIVE
#   DISTINCT input points (pts=5):
#     store                       fresh  sources   case
#     one-entry [("x","0")]       5      [0]       alias-return        (E2/E4)
#     one-entry [("x","0")]       9      [3]       frame-write-source  (E3)
#     one-entry [("k","9")]       6      [2]       empty-copy          (E1)
#     two-entry [("a","1"),..]    7      [2]       skip-last-entry     (E1)
#     one-entry [("m","1")]       4      [1]       no-bump             (E5)
#   Five distinct (store,fresh,sources) tuples. `sources` ranges over handles
#   {0,1,2,3}, `fresh` over {4,5,6,7,9}, and `store` over {one-entry, two-entry}
#   maps — no binder is pinned to a single value across the reject set. The
#   two-entry source in skip-last-entry is the one that separates it from
#   empty-copy (both attack E1, but skip-last-entry agrees with gold on more of
#   the domain and needs a length-≥2 source to bite).
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3.2: the object
#   copy is modeled deeply and concretely as allocate-fresh + copy-contents, an
#   A-reference validated by G-AX, not a consumed axiom); the nagini sibling's
#   AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
