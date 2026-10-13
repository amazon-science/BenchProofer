"""properties.py — G-PBT falsification battery for pydata__xarray-6938 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a heap-of-objects carrier):

  problem_spec_toIndexVariable
      (heap : Array VarRec) (src : Nat)
      (result : Array VarRec × Nat) : Prop :=
    result.2 = heap.size                              -- (C1) independence
    ∧ result.1.size = heap.size + 1                   -- (C2) exactly one new object
    ∧ result.1[result.2]! = heap[src]!                -- (C3) carries source's fields
    ∧ (∀ i, i < heap.size → result.1[i]! = heap[i]!)  -- (C4) frame: originals intact

  The live-object universe is a heap (``Array VarRec``); an object's identity is
  its slot index (a handle : Nat), and ``src`` is the source handle
  (precondition ``src < heap.size``). Converting the object at ``src`` to its
  indexed form must yield an INDEPENDENT object: the produced handle
  (``result.2``) is a brand-new slot (``= heap.size``), so it is distinct from
  every pre-existing handle — in particular from ``src`` — and a later in-place
  edit of the produced object cannot reach back to the source. The four
  independent top-level conjuncts each pin a distinct facet:

    * C1 — the produced handle is FRESH (``= heap.size``): the discriminating
      independence clause. An aliasing re-presentation hands back the source
      handle and violates exactly this.
    * C2 — the heap grows by exactly one slot: one and only one object is
      allocated. Pinned by the relationship between ``result.1.size`` and
      ``heap.size``.
    * C3 — the produced object carries the SOURCE object's fields
      (``heap[src]!``): pinned by both ``src`` (which object is duplicated) and
      the produced record.
    * C4 — every pre-existing object is left untouched (the frame): the
      referentially-transparent analogue of "the input is read-only". Pinned by
      the pre-existing slots ``heap[i]!``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — NOT vacuous here, and this is the key
    difference from a value-only port. The nagini sibling makes an input-write
    attack MANDATORY because the receiver is held at a fractional (read-only)
    permission and a rival that writes it is rejected for insufficient
    permission. Lean is referentially transparent — there is no half-permission
    to violate — BUT the read-only obligation is re-expressed as the explicit
    FRAME conjunct C4 (``∀ i < heap.size, result.1[i]! = heap[i]!``). A rival
    that "mutates the receiver" is representable as one that overwrites a
    pre-existing heap slot, and C4 refutes it. So the nagini frame-mutation
    rivals port to a genuine, expressible attack on C4 (see
    ``weak-mutate-existing-slot``), rather than collapsing to a vacuous class.

  * DIVERGENCE / NON-TERMINATION — nothing to ship, but NOT for the reason
    originally recorded here. The original text said a diverging
    re-presentation "cannot be written at all"; it can — ``partial def
    implementation_toIndexVariable heap src := implementation_toIndexVariable
    heap src`` clears ``variant_problems`` with no complaint. It is not a
    usable rival because ``partial`` makes the constant opaque to the kernel,
    so the frozen obligation fails at ``unfold`` and the rejection attributes
    to irreducibility rather than to the spec (measured: the build errors with
    ``Tactic `unfold` failed to unfold `implementation_toIndexVariable```). The
    vacuous-verification lane for ``partial`` impls is a KNOWN, already-recorded
    spec hole measured corpus-wide on the velvet backend — see
    ``the corpus-wide termination-semantics finding``; it is not re-derived or re-reported here.
    Disposition unchanged: no substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: every
    conjunct relates ``result`` to the actual input carrier (``heap``, ``src``,
    ``heap.size``) via structural equalities. The bundle declares no
    ``opaque``/``axiom`` (meta.json: the copy semantics ARE modeled deeply, not
    axiomatized), so there is no answer key to echo. The honest analogue is the
    cheapest-correct POSITIVE CONTROL below.

  * VALUE / PARTIAL-DOMAIN / FABRICATE rivals — APPLY. The nagini drop-first and
    fabricate-names rivals become rivals whose produced object carries the wrong
    fields (C3) or reads the wrong source slot (C3 via ``src``); each violates
    one conjunct on a distinct sub-domain and is refuted with a witness at a
    distinct input. Both are carried EXPLICITLY:
    ``weak-fabricate-contents`` (fabricate-names: wrong on every input) and
    ``weak-drop-first-label`` (drop-first: a genuine partial-domain rival,
    agreeing with gold on label-free sources).

  * SHARED-STORAGE (the nagini ``weak-shared-storage-ctor`` rival) — VACUOUS on
    this carrier, and DROPPED for that reason. Nagini distinguishes "a distinct
    object whose ``dims`` is the SAME list object" from a true copy, because its
    carrier has a storage identity for the field. Here a ``VarRec`` field is a
    VALUE: rebuilding the record from the source's own fields,
    ``heap.push ⟨(heap[src]!).dims, (heap[src]!).data⟩``, is DEFINITIONALLY the
    frozen impl — the audit closed the equation by ``fun _ _ => rfl`` (build
    exit 0). A rival observably identical to gold cannot be refuted by any
    witness, so the case would be vacuous rather than merely hard. This is a
    genuine carrier collapse, demonstrated rather than asserted.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``refine ⟨…⟩`` script is tuned to the
frozen ``Id.run do`` form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at a CONCRETE input, applied to the rival's own
``implementation_toIndexVariable``. The whole-spec ``decide`` is blocked by the
``∀`` frame conjunct, so each witness ``rintro``s the conjunction and refutes the
single violated conjunct. Each was checked to HOLD of its rival and to FAIL on
the frozen solution (so it discriminates rather than asserting a tautology). All
witness hypotheses are literal inputs (no conditioning, so no satisfiability
obligation).

BINDER COVERAGE. Both input binders are varied across the reject witnesses:
  * ``src`` — refuted at ``src = 1`` (alias independence; wrong-source-index;
    mutate-source-slot), at ``src = 0`` (no-growth; fabricate-contents;
    drop-first-label) and at ``src = 2`` (mutate-existing). The
    ``wrong-source-index`` rival exists specifically to exercise the spec's
    dependence on ``src``: it is indistinguishable from gold at ``src = 0`` and
    refuted only at ``src = 1``.
  * ``heap`` — varied in size and contents across the witnesses (1-, 2- and
    3-element heaps with distinct records, and a TWO-label source record
    ``⟨[7, 9], 3⟩`` that only ``weak-drop-first-label`` uses; every other
    witness holds a single-label source, so without it no witness could see a
    rival that is wrong only in the tail of the label list).
The two frame rivals are refuted so that C4 is shown to protect BOTH facets,
which is the pairing that makes carrying two frame rivals worth its builds:
``weak-mutate-source-slot`` corrupts slot 1 while ``src = 1``, so the corrupted
object is the SOURCE ITSELF, and ``weak-mutate-existing-slot`` corrupts slot 0
while ``src = 2``, so the corrupted object is a genuine BYSTANDER the operation
was never asked about. (Audit repair: the second witness previously stood at
``src = 0``, where the slot it corrupts IS the source, so the bystander facet
was claimed in this docstring and demonstrated by neither case.)
Distinct input points across the reject lane: ``pts`` = 6 across 7 witnesses —
``weak-alias-return-src`` and ``weak-mutate-source-slot`` deliberately share the
input ``(#[⟨[7],0⟩, ⟨[8],1⟩], src = 1)``, refuting DIFFERENT conjuncts (C1 and
C4) at the same point, so the count is 6 and not 7. Stated exactly because the
coverage reporter reports 6 and a claim of 7 here would be prose the manifest
does not demonstrate.

SPEC STRENGTH (PROVED, not argued). The independent audit closed the
SPEC-TOO-WEAK direction by proving determinacy inside the verifier rather than
by sampling rivals — the theorem

    ∀ heap src, src < heap.size → ∀ r, problem_spec_toIndexVariable heap src r →
      r.2 = heap.size
      ∧ r.1.size = (heap.push (heap[src]!)).size
      ∧ ∀ i < r.1.size, r.1[i]! = (heap.push (heap[src]!))[i]!

elaborates against the frozen spec (build exit 0). So ANY ``r`` satisfying C1-C4
agrees with the frozen result in its handle, its size and every slot: the four
conjuncts pin the observable result uniquely on the precondition's domain, and
no wrong impl can satisfy all four. That is a proof over all inputs, which no
finite set of rivals could give. C1 fixes ``result.2``, C2 and C4 fix the size
and every slot below ``heap.size``, and C3 fixes the one remaining slot.
Consistently, every SPEC-TOO-WEAK probe is rejected on the spec's OWN unsolved
goal rather than on a tactic mismatch — the rivals below plus the extra ones the
audits ran: grow-the-heap-by-two; zero the ``data`` field; drop a label;
prepend instead of append; push-then-truncate (a dangling handle);
copy-the-last-slot (residual goal
``heap[heap.size - 1]?.getD default = heap[src]?.getD default``, i.e. C3);
reverse the pre-existing slots (a frame break C4 catches); and an off-by-one on
the copied ``data`` field.

In the other direction five independently-authored CORRECT reshapes were proven
against the frozen obligation: append-a-singleton via ``heap.toList.length``;
handle as ``r.size - 1``; a ``dif``-guarded impl branching on the precondition;
``heap ++ #[heap[src]!]``; a whole-route-through-``List`` impl
(``(heap.toList ++ [heap[src]!]).toArray``); and a field-by-field record
rebuild combined with a result-derived handle. So the spec is not too strong
either. No spec hole was found in either direction.

AXIOM lane: EMPTY. The copy behavior is modeled deeply as a fresh heap
allocation (mapping.md: no ``opaque``/``axiom``, no deep_model_reference to
validate in isolation), so there is no in-model axiom obligation for the PBT
axiom lane to re-discharge. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6938"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let fresh := h[src]!        -- the contents of the source object\n"
    "  let handle := h.size        -- identity of the produced object: a new slot\n"
    "  h := h.push fresh           -- allocate the produced object as an independent slot\n"
    "  return (h, handle)\n"
)

_PROOF_BODY = (
    "  intro heap src hsrc\n"
    "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
    "  simp only [Id.run, pure]\n"
    "  refine ⟨trivial, ?_, ?_, ?_⟩\n"
    "  · simp [Array.size_push]\n"
    "  · simp [Array.getElem!_eq_getD]\n"
    "  · intro i hi\n"
    "    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,\n"
    "        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,\n"
    "        Array.getElem?_push]\n"
    "    simp [Nat.ne_of_lt hi, hi]\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# ALIAS (= the actual bug): hand back the SOURCE handle itself, aliasing it. The
# heap is unchanged and the produced handle is `src`, not the fresh `heap.size`.
_ALIAS = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  return (heap, src)\n"
)

# NO-GROWTH: compute the fresh handle number correctly but never allocate the
# object — return the unchanged heap with the would-be handle. The handle points
# one past the end; no new slot exists.
_NO_GROWTH = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  return (heap, heap.size)\n"
)

# FABRICATE-CONTENTS: allocate a fresh distinct slot with a full-perm record, but
# the record's fields are a CONSTANT, not copied from the source object.
_FABRICATE = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let handle := h.size\n"
    "  h := h.push ⟨[424242], 0⟩\n"
    "  return (h, handle)\n"
)

# WRONG-SOURCE-INDEX: allocate a fresh distinct slot, but duplicate the object at
# a FIXED slot 0 instead of the source `src`. Coincides with gold at src=0;
# diverges for any other source.
_WRONG_SOURCE = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let fresh := h[0]!\n"
    "  let handle := h.size\n"
    "  h := h.push fresh\n"
    "  return (h, handle)\n"
)

# DROP-FIRST-LABEL (partial domain, ported from the nagini drop-first rival that
# this battery originally recorded as absent). Allocate a fresh distinct slot
# carrying the source's `data` and the TAIL of its label list. Agrees with gold on
# the sub-domain where the source's label list is empty or a singleton-insensitive
# read, and diverges as soon as the source carries labels — the partial-domain
# shape the value rivals above do not have (they are wrong everywhere).
_DROP_FIRST = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let fresh := h[src]!\n"
    "  let handle := h.size\n"
    "  h := h.push ⟨fresh.dims.tail, fresh.data⟩\n"
    "  return (h, handle)\n"
)

# MUTATE-SOURCE-SLOT (frame attack aimed at the SOURCE, not a bystander): extend
# the source object's own label list in place, then allocate the copy. The
# produced object is fresh, distinct and value-correct against the PRE-state
# record, so C1/C2/C3 all pass; only the frame conjunct sees it. This is the
# nagini receiver-mutation rival's direct image: the corrupted slot is `src`
# itself, which `weak-mutate-existing-slot` (which always writes slot 0, a
# bystander when `src ≠ 0`) never exercises.
_MUTATE_SOURCE = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let fresh := h[src]!\n"
    "  h := h.set! src ⟨fresh.dims ++ [999], fresh.data⟩\n"
    "  let handle := h.size\n"
    "  h := h.push fresh\n"
    "  return (h, handle)\n"
)

# MUTATE-EXISTING-SLOT (frame attack): overwrite a PRE-EXISTING slot before
# allocating the copy. The produced object is fresh, distinct, and value-correct,
# but a source-adjacent original object has been corrupted — the frame is broken.
_MUTATE_EXISTING = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do\n"
    "  let mut h := heap\n"
    "  let fresh := h[src]!\n"
    "  h := h.set! 0 ⟨[999], 0⟩\n"
    "  let handle := h.size\n"
    "  h := h.push fresh\n"
    "  return (h, handle)\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl. The
# handle is DERIVED FROM THE RESULT (`r.size - 1`) instead of being read off the
# input (`heap.size`), which is what makes this a real reshape rather than a
# re-spelling: the two are NOT definitionally equal, so C1 cannot be closed by
# `rfl` on the frozen term and the proof has to carry an arithmetic step
# (`Array.size_push` then `n + 1 - 1 = n`) that the frozen script never needs.
#
# AUDIT NOTE. The predecessor positive here was `(heap.push (heap[src]!),
# heap.size)`, which is DEFINITIONALLY the frozen impl: the audit closed
# `∀ heap src, implementation_toIndexVariable heap src
#   = (heap.push (heap[src]!), heap.size)` by `fun _ _ => rfl` (build exit 0).
# A defeq impl cannot make the spec's verdict differ, so as a SPEC-TOO-STRONG
# probe it was vacuous — it passed honestly while testing nothing about shape.
# The replacement was checked NOT defeq: the same `rfl` probe against
# `(heap.push (heap[src]!), (heap.push (heap[src]!)).size - 1)` FAILS (exit 1),
# and the variant itself verifies (exit 0).
_POS_CONTROL = (
    "def implementation_toIndexVariable\n"
    "    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat :=\n"
    "  let r := heap.push (heap[src]!)\n"
    "  (r, r.size - 1)\n"
)
_POS_PROOF = (
    "  intro heap src hsrc\n"
    "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
    "  simp only []\n"
    "  have hs : (heap.push (heap[src]!)).size - 1 = heap.size := by\n"
    "    simp [Array.size_push]\n"
    "  rw [hs]\n"
    "  refine ⟨rfl, ?_, ?_, ?_⟩\n"
    "  · simp [Array.size_push]\n"
    "  · simp [Array.getElem!_eq_getD]\n"
    "  · intro i hi\n"
    "    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,\n"
    "        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,\n"
    "        Array.getElem?_push]\n"
    "    simp [Nat.ne_of_lt hi, hi]\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation, the spec is SPEC-TOO-STRONG. The `theorem correct_toIndexVariable`
    # STATEMENT is byte-identical; the tactic body re-proves the new (functional)
    # shape (the frozen `simp only [Id.run, pure]` step no longer applies). No
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-pair",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_CONTROL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` AND "
            "derives the produced handle from the RESULT (`r.size - 1`) rather than "
            "from the input (`heap.size`) must still satisfy all four conjuncts: C1 "
            "only after rewriting `(heap.push _).size - 1` to `heap.size`, C2 by "
            "`Array.size_push`, C3 by the push read-back, C4 by the "
            "`getElem?_push` frame argument. The reshape is NOT definitionally "
            "equal to the frozen impl — `fun _ _ => rfl` between the two does not "
            "elaborate — so C1 genuinely has to be re-earned for the new shape "
            "rather than inherited. If a faithful correct impl cannot verify, the "
            "spec is SPEC-TOO-STRONG. Only the impl and the tactic body differ; the "
            "obligation statement is byte-identical and no new "
            "declaration/axiom/assumption token is introduced."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only in the
    # abstract. The F2P builds a single-element index variable and converts it;
    # the ground input here is a one-slot heap with `src = 0`. Discharging the
    # spec predicate there, inside the proof region alongside the frozen
    # obligation, shows the modeled behavior is realizable at exactly the input
    # the F2P exercises (the analogue of PRECOND-TOO-STRONG if it could not be).
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_toIndexVariable #[(⟨[3], 0⟩ : VarRec)] 0\n"
            "      (implementation_toIndexVariable #[(⟨[3], 0⟩ : VarRec)] 0) := by\n"
            "    unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "    simp only [Id.run, pure]\n"
            "    refine ⟨trivial, ?_, ?_, ?_⟩\n"
            "    · decide\n"
            "    · decide\n"
            "    · intro i hi\n"
            "      have hi0 : i = 0 := by\n"
            "        have : i < 1 := by simpa using hi\n"
            "        omega\n"
            "      subst hi0\n"
            "      decide\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a one-slot heap "
            "holding a single index-variable record, converting the object at `src "
            "= 0`), where the spec demands a fresh handle `= 1`, a heap of size 2, "
            "the produced object equal to the source, and the original slot intact "
            "— shown by `decide` on each concrete conjunct; then the frozen "
            "obligation is closed verbatim. Verifies (else the spec is unsatisfiable "
            "at the normal input). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break rather than an artifact, and (b)
    # a refutation witness pinning the violation at one concrete input.
    # =====================================================================

    # C1 (independence) — the actual pre-patch bug: hand back the source handle.
    {
        "id": "weak-alias-return-src",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS),
        "refinement": (
            "this is the pre-patch behavior: the conversion hands back the SOURCE "
            "object itself rather than an independent one. Its faithful real patch "
            "is exactly the pre-fix code (the produced value IS the source), which "
            "the F2P observable rejects: it asserts the produced object is a "
            "DISTINCT object and that a later in-place edit of it leaves the source "
            "unchanged. An alias fails both. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 `result.2 = heap.size`: the rival returns the handle "
            "`src`, but the precondition `src < heap.size` makes `src ≠ heap.size`, "
            "so the produced handle is not fresh (it coincides with the source). "
            "Refuted at `src = 1` in a two-slot heap, exercising `src` at a "
            "non-zero value."
        ),
        # The refutation is routed through the CONCRETE Nat claim `1 = 2` so that
        # the gold-side failure text names the arithmetic, not a tactic. The
        # predecessor closed with a bare `simp at h1`, which held of the rival
        # and failed on gold (so the gate passed it) — but gold's failure read
        # ``simp` made no progress`, a tactic-shaped message indistinguishable
        # from a witness that never asked the spec anything. The cause was
        # semantic (on gold `h1` reduces to `True`, i.e. gold SATISFIES C1;
        # confirmed by `trace_state`), but the recorded evidence did not show
        # that. This form fails on gold as ``h.left` has type True but is
        # expected to have type False` — a statement about the spec's verdict.
        "witness": (
            "-- Alias: the produced handle is the source handle `1`, not the fresh\n"
            "-- slot `heap.size = 2`, so the independence conjunct C1 fails. Stated\n"
            "-- as the concrete arithmetic claim `1 = 2` so the refutation is about\n"
            "-- the spec's verdict at this input and not about a tactic.\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩] 1\n"
            "    (implementation_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩] 1) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  intro h\n"
            "  have h1 : (1 : Nat) = 2 := by simpa using h.1\n"
            "  omega\n"
        ),
    },

    # C2 (exactly one new object) — right handle number, no allocation.
    {
        "id": "weak-no-growth",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_GROWTH),
        "refinement": (
            "computing the fresh handle number but never allocating the object "
            "leaves the produced handle pointing one past the end of the live-object "
            "universe: the F2P's produced variable would not actually exist, so "
            "reading or editing it is undefined and the copy-independence assertions "
            "cannot hold. A real patch that returns a dangling handle does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C2 `result.1.size = heap.size + 1`: the rival returns the "
            "unchanged heap, so its size is `heap.size`, not `heap.size + 1` — no "
            "object was allocated. Refuted at `src = 0` in a one-slot heap."
        ),
        "witness": (
            "-- No allocation: the heap size stays `1`, but C2 demands `heap.size +\n"
            "-- 1 = 2`, so exactly-one-new-object fails.\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[5], 2⟩ : VarRec)] 0\n"
            "    (implementation_toIndexVariable #[(⟨[5], 2⟩ : VarRec)] 0) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  rintro ⟨_, h2, _⟩\n"
            "  simp at h2\n"
        ),
    },

    # C3 (carries source's fields) — fresh distinct object, fabricated fields.
    {
        "id": "weak-fabricate-contents",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FABRICATE),
        "refinement": (
            "allocating a fresh, distinct, fully-owned object whose fields are a "
            "CONSTANT rather than copied from the source is not a re-presentation of "
            "the source at all; the F2P asserts the produced object carries the "
            "source's fields (its dimension labels), and every caller depends on "
            "that. A constant-field result fails the F2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from C3 `result.1[result.2]! = heap[src]!`: the produced object "
            "carries the constant record `⟨[424242], 0⟩` regardless of the source, "
            "so it differs from `heap[src]!`. C1/C2/C4 all pass (fresh distinct slot, "
            "originals intact), isolating the value conjunct. Refuted at `src = 0`."
        ),
        "witness": (
            "-- Fabricated fields: the produced object is `⟨[424242], 0⟩`, not the\n"
            "-- source's `⟨[7], 0⟩`, so the contents conjunct C3 fails.\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[7], 0⟩ : VarRec)] 0\n"
            "    (implementation_toIndexVariable #[(⟨[7], 0⟩ : VarRec)] 0) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  rintro ⟨_, _, h3, _⟩\n"
            "  simp [Array.getElem!_eq_getD] at h3\n"
        ),
    },

    # C3 via the `src` binder — duplicate a fixed slot instead of the source.
    {
        "id": "weak-wrong-source-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_SOURCE),
        "refinement": (
            "duplicating the object at a FIXED slot instead of the requested source "
            "produces the wrong object whenever the source is not that slot; the F2P "
            "converts a specific variable and asserts the copy carries THAT "
            "variable's fields. A patch that ignores the source argument returns "
            "someone else's fields and does NOT resolve."
        ),
        "rationale": (
            "REJECT from C3 `result.1[result.2]! = heap[src]!`: the rival duplicates "
            "`heap[0]!`, so at `src = 1` (with distinct records) the produced object "
            "is `heap[0]! ≠ heap[1]!`. Coincides with gold at `src = 0`, so this "
            "rival exists to exercise the spec's dependence on the `src` binder — "
            "refuted only at `src = 1`."
        ),
        "witness": (
            "-- Wrong source: the rival copies slot `0` `⟨[8], 1⟩`, but `src = 1`\n"
            "-- selects `⟨[7], 0⟩`, so the produced object's fields are wrong (C3).\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[8], 1⟩ : VarRec), ⟨[7], 0⟩] 1\n"
            "    (implementation_toIndexVariable #[(⟨[8], 1⟩ : VarRec), ⟨[7], 0⟩] 1) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  rintro ⟨_, _, h3, _⟩\n"
            "  simp [Array.getElem!_eq_getD] at h3\n"
        ),
    },

    # C3 on a PARTIAL sub-domain — the nagini drop-first rival, landed here.
    {
        "id": "weak-drop-first-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_FIRST),
        "refinement": (
            "a re-presentation that drops the first axis label produces an object "
            "with the wrong labels. The F2P starts from a single-label index "
            "variable and asserts the produced object carries THAT label; a "
            "drop-first variant hands back an empty label list and fails it, as "
            "does every PASS_TO_PASS that round-trips labels through the "
            "conversion. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from C3 `result.1[result.2]! = heap[src]!`: the produced record "
            "keeps the source's `data` but only the TAIL of its label list, so the "
            "records differ whenever the source carries at least one label. "
            "C1/C2/C4 pass (fresh distinct slot, size grows by one, originals "
            "intact), isolating the value conjunct. Unlike "
            "`weak-fabricate-contents` (wrong on every input) this rival is a "
            "PARTIAL-domain attack: it coincides with gold on label-free sources "
            "and is refuted only once a label exists. Refuted at `src = 0` with a "
            "TWO-label source `⟨[7, 9], 3⟩`, a heap shape and record no other "
            "witness in this battery uses."
        ),
        "witness": (
            "-- Drop-first: the produced object is `⟨[9], 3⟩` (tail of the labels),\n"
            "-- not the source's `⟨[7, 9], 3⟩`, so the contents conjunct C3 fails.\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[7, 9], 3⟩ : VarRec)] 0\n"
            "    (implementation_toIndexVariable #[(⟨[7, 9], 3⟩ : VarRec)] 0) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  rintro ⟨_, _, h3, _⟩\n"
            "  simp [Array.getElem!_eq_getD] at h3\n"
        ),
    },

    # C4 (frame) aimed at the SOURCE slot itself — the nagini receiver-mutation
    # rival, landed here rather than recorded as absent.
    {
        "id": "weak-mutate-source-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MUTATE_SOURCE),
        "refinement": (
            "extending the SOURCE object's own label list in place while producing "
            "the conversion is the referentially-transparent image of mutating the "
            "receiver — the exact corruption the fix exists to prevent, and the "
            "reason the conversion may not hand back something tied to the source. "
            "The F2P asserts the source's labels are unchanged after the operation; "
            "a patch that writes the source object breaks that directly. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C4 `∀ i < heap.size, result.1[i]! = heap[i]!`: the rival "
            "writes `heap[src]` itself, appending a label to it, so at `i = src` "
            "the pre-existing object differs from `heap[src]!`. The produced object "
            "is copied from the PRE-state record, so C1/C2/C3 all pass — the frame "
            "conjunct is the only one that sees this. Distinct from "
            "`weak-mutate-existing-slot`, which always corrupts slot 0 (a "
            "BYSTANDER whenever `src ≠ 0`) and so never shows that the frame "
            "protects the source itself. Refuted at `src = 1`, where the corrupted "
            "slot is the source and slot 0 is untouched."
        ),
        "witness": (
            "-- Frame break at the SOURCE: slot `1` (the source) is rewritten to\n"
            "-- `⟨[8, 999], 1⟩`, so the pre-existing object at `i = 1` no longer\n"
            "-- equals `heap[1]!` (C4), even though the produced copy is correct.\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩] 1\n"
            "    (implementation_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩] 1) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  intro h\n"
            "  have h4 := h.2.2.2 1 (by decide)\n"
            "  simp [Array.getElem!_eq_getD] at h4\n"
        ),
    },

    # C4 (frame) — the nagini frame-mutation attack, re-expressed as a heap write.
    {
        "id": "weak-mutate-existing-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MUTATE_EXISTING),
        "refinement": (
            "overwriting a pre-existing object while producing the conversion is the "
            "referentially-transparent image of mutating the read-only source (or a "
            "sibling) in place — precisely the corruption the fix exists to prevent. "
            "The F2P asserts the SOURCE object is unchanged after the operation; a "
            "patch that writes an existing object breaks that (and the PASS_TO_PASS "
            "that rely on the conversion being non-mutating). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from C4 `∀ i < heap.size, result.1[i]! = heap[i]!`: the rival "
            "overwrites slot `0` with `⟨[999], 0⟩` before pushing the copy, so at `i "
            "= 0` the pre-existing object differs from `heap[0]!`. C1/C2 pass (fresh "
            "handle, size grows by one) and the produced object is value-correct, "
            "isolating the frame conjunct. Refuted at `src = 2` in a THREE-slot heap, "
            "so the corrupted slot 0 is a genuine BYSTANDER — an object the operation "
            "was never asked about — which is the facet `weak-mutate-source-slot` "
            "(corrupting the source itself) does not cover."
        ),
        # AUDIT REPAIR. The predecessor witness refuted this rival at `src = 0`,
        # where the slot the rival corrupts (always 0) IS the source. The
        # docstring claimed this case shows the frame protecting "some
        # bystander" as opposed to the source, and paired with
        # `weak-mutate-source-slot` to cover both facets — but at `src = 0`
        # BOTH cases were refuting a corruption of the source, so the
        # bystander facet was claimed and never demonstrated, and the two
        # frame witnesses were not the complementary pair the prose described.
        # Re-pointed at `src = 2` in a three-slot heap, where slot 0 is
        # genuinely a bystander. Re-measured: rival exit 0, gold exit 1
        # (gold's `h` reduces so that the C4 instance at `i = 0` becomes
        # `True`, i.e. gold SATISFIES the frame there); the flipped-claim
        # forgery probe at the same input gives gold exit 0 / rival exit 1
        # with `trivial ... has type True but is expected to have type ...`,
        # so the gold-side exit code does track the claim.
        "witness": (
            "-- Frame break at a BYSTANDER: the source is slot `2`, but the rival\n"
            "-- overwrites slot `0` with `⟨[999], 0⟩`, so the pre-existing object at\n"
            "-- `i = 0` — an object the operation was never asked about — no longer\n"
            "-- equals `heap[0]!` (C4).\n"
            "example : ¬ problem_spec_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩, ⟨[6], 4⟩] 2\n"
            "    (implementation_toIndexVariable #[(⟨[7], 0⟩ : VarRec), ⟨[8], 1⟩, ⟨[6], 4⟩] 2) := by\n"
            "  unfold problem_spec_toIndexVariable implementation_toIndexVariable\n"
            "  simp only [Id.run, pure]\n"
            "  intro h\n"
            "  have h4 := h.2.2.2 0 (by decide)\n"
            "  simp [Array.getElem!_eq_getD] at h4\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the copy behavior is modeled
# deeply as a fresh heap allocation, so there is no in-model axiom obligation for
# the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
