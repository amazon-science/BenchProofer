"""properties.py — PBT falsification manifest for matplotlib__matplotlib-25311 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
Two independent obligations are modeled:

  (1) implementation_initHandlerState (useBlit blitSupported : Bool) : List Attr
      pinned by
        problem_spec_initHandlerState :
          stateSerializable result
          ∧ result = [Attr.serial, Attr.flag false,
                      Attr.flag (useBlit && blitSupported), Attr.serial]
      i.e. the persisted state is (a) fully serializable — it retains no live
      display handle — AND (b) exactly the ordered four-component list: the
      dragged-object reference, the "drag in progress" flag (off), the effective
      fast-redraw flag (on iff both requested AND supported), and the connected
      callback identifiers, IN THAT ORDER.

  (2) implementation_accessDisplayHandle (owner : Container) : Nat
      pinned by
        problem_spec_accessDisplayHandle : result = owner.displayHandle
      i.e. the display-handle accessor recomputes the owner's CURRENT handle.

The carrier is FULLY TRANSPARENT (`Attr` is an inductive with `DecidableEq`,
`Container` is a one-field structure, the flag is Boolean `&&`); there is no
opaque callee, so every rival is refuted by `decide` at concrete literal inputs
and no witness needs to condition on a hypothesis.

WHY THIS SPEC IS STRONGER THAN THE NAGINI SIBLING
-------------------------------------------------
The nagini model abstracted the serializable state to a `List[int]` of held
identities and pinned only MEMBERSHIP: the surface identity is ABSENT and each
genuine identity is PRESENT, order-free. The lean carrier pins the EXACT ORDERED
LIST plus the serializability property, so several distinctions the nagini model
could not see (position, the flag COMBINATION, the display accessor) are pinned
here. Two consequences for the port:

  * nagini's `pos-genuine-reorder` (a correct impl emitting the genuine values in
    a DIFFERENT order) is NOT a soundness positive here — the lean spec pins the
    order, so a reordered impl is genuinely wrong. It is not ported as a verify
    case; it is instead INVERTED into the reject case `weak-permute-order` below.
    NOTE (audit): the drop rivals do NOT demonstrate the ordering clause. Each of
    them changes the list's LENGTH/multiset, so an order-blind spec (one pinning
    only the multiset of components) would reject every one of them too. Only a
    pure PERMUTATION — same length, same multiset, wrong order — isolates the
    ordering, which is why `weak-permute-order` is required.
  * a whole clause absent from nagini — the effective fast-redraw flag
    `useBlit && blitSupported` — is modeled here and gets its own rival
    (`weak-flag-or`), the ONLY case that varies both boolean binders.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
  * `pos-local-reshape` (nagini) -> `pos-init-functional`: a structurally
    different CORRECT impl of obligation (1) — a pure functional expression (no
    `Id.run do` / `let mut`) whose value is the same ordered list. Verifies or
    the spec is over-fit to the imperative construction shape (SPEC-TOO-STRONG).
  * added `pos-init-flag-comm`: a second correct impl whose fast-redraw flag is
    written in the commuted form; the proof re-closes via Boolean commutativity.
    Defends the flag clause against being over-fit to one syntactic form.
  * added `pos-access-functional`: obligation (2) in pure functional form; a
    soundness positive so that obligation is DEFENDED, not only attacked.
  * `weak-leak-surface` (nagini pre-patch bug) -> `weak-leak-handle`: retain the
    non-serializable live display handle in the persisted state. This is exactly
    the pre-patch skeleton; refuted by BOTH the serializability conjunct AND the
    exact-list conjunct.
  * `weak-drop-cid-release` (nagini) -> `weak-drop-cids`: omit the trailing
    connected-callback component; refuted by the exact-list conjunct (wrong
    length/shape).
  * `weak-drop-element` (nagini) -> `weak-drop-refartist`: omit the leading
    dragged-object reference; refuted by the exact-list conjunct.
  * `weak-empty-state` (nagini) -> `weak-empty`: return the empty state (the
    vacuous "drop everything" cheat); refuted by the exact-list conjunct.
  * added `weak-dragflag-on` (audit): initialize the "drag in progress" status
    flag ON instead of OFF. The second component was the one clause of the
    four-component list that NO shipped rival perturbed — every other rival
    changed the length, the third (fast-redraw) component, or the serializability
    of the list, so a spec that left the second component free would have passed
    the whole battery.
  * added `weak-permute-order` (audit): emit exactly the four required components
    (same multiset, same length) in a PERMUTED order. This is the only case that
    isolates the exact-list clause's ORDERING content; see the note above.
  * added `weak-flag-or`: compute the effective fast-redraw flag with the WRONG
    boolean combination (disjunction instead of conjunction). The ONLY rival that
    varies useBlit AND blitSupported; without it a rival mishandling only the
    flag combination would slip by. Refuted by the exact-list conjunct at an
    input where the two flags differ.
  * added `weak-access-const` / `weak-access-offby1`: obligation (2) rivals — a
    handle accessor that ignores the owner (returns a constant) and one that is
    off by one; they attack obligation (2) at two distinct owner values so the
    `owner` binder is discriminated.
  * nagini `admiss-fts-input` -> `admiss-ground-scenario-input`. An earlier pass
    recorded this class as VACUOUS on the ground that the lean obligations are
    `∀ useBlit blitSupported, problem_spec …` and `∀ owner, problem_spec …` with
    no precondition hypothesis, so there is nothing to over/under-constrain.
    A later audit rejected that reasoning and LANDED the case: "the frozen
    obligation has no precondition" is not a demonstration of vacuity, because
    the analogue on a TOTAL carrier is the obligation being unsatisfiable at
    exactly a scenario-shaped input, which a positive that discharges the
    obligation at that concrete input — by evaluation, as a `have`, before
    closing the frozen obligation verbatim — tests directly. See the case's
    rationale for the load-bearing measurement.
  * nagini `weak-return-fresh-empty` (the permission/ownership negative control)
    is VACUOUS on lean: the language is referentially transparent — there is no
    aliased input to overwrite and no result-ownership permission to drop; the
    returned list IS the result. Demonstrated rather than asserted (audit): an
    impl that builds the correct state into a local and then returns a fresh `[]`
    is definitionally equal to the `weak-empty` rival — the two are proved equal
    by `rfl`, so nagini's ownership case collapses onto a rival the port DID
    ship and is not a separate discriminator here. No substitute is fabricated.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it
    (this bundle's axioms region is empty anyway).

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligations
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1).
The carrier is transparent, so no witness binds a hypothesis (nothing to be
inconsistent).

AUDIT RECORD (independent re-derivation, all 9 reject cases rebuilt both ways)
-----------------------------------------------------------------------------
Every witness was rebuilt from scratch by the audit: rival exit 0, gold exit 1
for all nine, and each gold-side failure was read and confirmed to be a SEMANTIC
refutation — `decide` proved the negation false, i.e. gold genuinely satisfies
the spec at that input — never an unknown identifier, type error, unfolding
failure, or timeout. Each spec region and each `theorem correct_*` statement was
diffed byte-for-byte against the frozen file across all cases: identical.

Attack D (spec-too-weak): 7 NEW wrong impls not in this battery were built and
all 7 are REJECTED by the frozen spec — status flag on, pure permutation, flag
ignoring the support flag, flag negated, an extra serializable component, a live
handle at the trailing position, and a doubling accessor. Two of them exposed
genuine coverage gaps and were promoted into this battery as `weak-dragflag-on`
and `weak-permute-order`. No spec hole found.

Attack E (spec-too-strong): 5 NEW correct reshapes were built and all 5 VERIFY —
append-chain construction, the flag as `if useBlit then blitSupported else false`,
a four-branch `match` on both booleans, the accessor by pattern match, and the
accessor via the explicit projection. The spec rejects no faithful correct impl
that was tried.

SECOND-PASS AUDIT (independent adversarial re-derivation; every exit code below
is from a real scripts/lean_verify.sh build, 71 builds total)
-----------------------------------------------------------------------------
The first-pass claims above were RE-DERIVED rather than trusted. What held, what
was corrected, and what was added:

  * STATEMENT INTEGRITY (attack A) — the whole `spec_view` and both
    `theorem correct_*` statements were extracted from all 13 case modules and
    compared to the frozen file programmatically: byte-identical in every case.
    No obligation is weakened, restated or narrowed.

  * WITNESS DISCRIMINATION (attack B) — all 9 shipped reject witnesses were
    rebuilt from scratch, both ways: rival EXIT 0 and frozen-solution EXIT 1 in
    every case, reproducing each recorded `gold_signature`. Each of the 9 rival
    variant builds was also confirmed to fail (EXIT 1) on its own.

  * FORGERY TEST (attack B′) — run on all 9 even though every `gold_signature`
    is a plain evaluation (the admissible class), because "it looks semantic" is
    not evidence. For each case a second file was built differing from the
    witness ONLY in what it claims — the exact-list equation asserted POSITIVELY
    instead of negated. The exit codes INVERT cleanly on all 9: forgery-vs-gold
    EXIT 0 (the frozen impl PROVES the equation the rival violates) and
    forgery-vs-rival EXIT 1, versus witness-vs-gold EXIT 1 and
    witness-vs-rival EXIT 0. The gold-side error text tracks the claim rather
    than the tactic shape: `¬… is false` for the witness against
    `… is false` for the flip, same input, same tactic. No case is hollow.

  * IS THE RIVAL WRONG, OR MERELY DIFFERENT? (attack C) — every rival differs
    from the frozen impl OBSERVABLY on this carrier, and the forgery pair proves
    it per case: the frozen impl satisfies the exact-list equation at the
    witness input (forgery builds, EXIT 0) while the rival refutes it (witness
    builds, EXIT 0 on the negation). No rival is a definitionally-equal reshape,
    so no rejection here attests only to a tactic mismatch. `Attr` carries
    `DecidableEq` and `Container` is a one-field structure, so none of the usual
    collapse traps (Nat truncation, Option collapsing, list coercion, clamps)
    applies.

  * SPEC-TOO-WEAK PROBE (attack D) — 9 FURTHER wrong impls beyond the first
    pass's 7, aimed at what the shipped rivals leave unattacked, were built
    against the frozen spec. ALL 9 REJECTED (EXIT 1): the flag reading only the
    request flag, the flag reading only the support flag, the flag negated, an
    extra trailing serializable component, a live handle APPENDED at the tail, a
    live handle SUBSTITUTED for the trailing component (same length, so neither
    the length nor the leading prefix distinguishes it), the third and fourth
    components transposed, a doubling accessor, and a saturating-predecessor
    accessor (the last two chosen because they AGREE with the frozen accessor at
    displayHandle = 0, so only a non-zero point separates them). No spec hole.

  * SPEC-TOO-STRONG PROBE (attack E) — the first pass's claim that the
    `if useBlit then blitSupported else false` reshape "VERIFIES" is CORRECTED
    here: under the frozen proof script it FAILS (`Type mismatch … rfl`), because
    that reshape is not definitionally the frozen term. It is not a spec hole —
    a positive control may legitimately re-prove — and it VERIFIES (EXIT 0) once
    the flag equality is re-closed by `cases useBlit <;> cases blitSupported <;>
    rfl`. Re-measured and passing: cons-chain construction, the append-of-halves
    construction, the accessor by pattern match on the structure, and the
    accessor via the explicit `Container.displayHandle` projection (4 of 4,
    EXIT 0). The spec rejects no faithful correct impl that was tried.

  * OWNERSHIP-CASE COLLAPSE, RE-DERIVED — the claim that nagini's
    `weak-return-fresh-empty` collapses onto `weak-empty` was re-built and it
    HOLDS: an impl that constructs the correct state into a local and then
    returns a fresh `[]` is proved equal to the empty rival by `rfl` for all
    inputs (EXIT 0). The first pass's own probe of this had been mis-built (it
    failed on the frozen proof script rather than on the claim); the corrected
    probe strips the proof regions and confirms the collapse. So the ownership
    case really is not a separate discriminator here.

  * DIVERGENCE LANE (attack F′) — `set_option loom.semantics.termination` is a
    VELVET-only option (G-HYGIENE requires it only for that backend) and this
    frozen solution carries none, so the disposition is decided by what the lean
    elaborator actually does. Measured: a self-recursive impl with no decreasing
    measure is REJECTED OUTRIGHT by the elaborator (`fail to show termination
    for implementation_initHandlerState … failed to infer structural
    recursion`), so the carrier behaves as "total" and a diverging impl cannot
    even be spelled without `partial`. With `partial def` the impl elaborates,
    but a witness against it is UNDECIDABLE, not refutable: `decide` reports
    `its Decidable instance instDecidableNot did not reduce to isTrue or
    isFalse` — precisely the `witness-undecided` signature the gate screens for.
    So no shippable diverging reject case exists on this carrier: the impl either
    fails to elaborate (nothing for the spec to reject) or admits no
    discriminating witness. Recorded as a KNOWN HOLE for the `partial` shape
    rather than as a vacuous class.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25311"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring; assert
    it actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — each strictly INSIDE an impl region of Solution.lean and
# unique across the whole file.
# ---------------------------------------------------------------------------

# The full gold impl block for obligation (1) (the Id.run do construction).
_INIT_IMPL = (
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.serial]                            -- the dragged object reference\n"
    "  st := st ++ [Attr.flag false]                        -- \"drag in progress\" flag\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]   -- effective fast-redraw flag\n"
    "  st := st ++ [Attr.serial]                            -- connected callback identifiers\n"
    "  return st"
)

# The full gold impl block for obligation (2).
_ACCESS_IMPL = (
    "def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do\n"
    "  return owner.displayHandle"
)

# The frozen proof BODY for obligation (1) (the tactic script between the
# `correct_initHandlerState … := by` header and the `-- proof-end` marker).
# Unique in the file; only the positive controls that reshape the impl replace
# it, re-emitting the theorem STATEMENT unchanged (it lives above this body).
_INIT_PROOF_BODY = (
    "  intro useBlit blitSupported\n"
    "  have himpl : implementation_initHandlerState useBlit blitSupported\n"
    "      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := rfl\n"
    "  refine ⟨?_, himpl⟩\n"
    "  rw [himpl]\n"
    "  intro a ha\n"
    "  fin_cases ha <;> simp"
)

# The frozen proof's `intro` line for obligation (1), and the whole frozen proof
# body for obligation (2). Both unique in the file and strictly inside a proof
# region, so the admissibility positive can PREPEND ground `have`s without
# touching either theorem STATEMENT or the spec view.
_INIT_INTRO = "  intro useBlit blitSupported"
_ACCESS_PROOF_BODY = "  intro owner\n  rfl"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-init-functional) obligation (1) as a pure functional expression: a
# structurally different construction (no `Id.run do`, no `let mut`, no `for`)
# whose value is the same ordered list. Definitionally equal to the gold list,
# so the frozen proof (`himpl := rfl`) re-closes verbatim — only the impl SHAPE
# changed. If it fails to verify the spec is over-fit to the imperative
# construction shape => SPEC-TOO-STRONG.
_POS_INIT_FUNCTIONAL = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr :=\n"
    "  [Attr.serial, Attr.flag false,\n"
    "   Attr.flag (useBlit && blitSupported), Attr.serial]",
)

# (pos-init-flag-comm) obligation (1) with the effective fast-redraw flag written
# in the COMMUTED boolean form. Semantically identical (`&&` is commutative), a
# different source; the proof re-closes by rewriting with commutativity. Defends
# the flag clause against being over-fit to one syntactic order of the conjuncts.
_POS_INIT_FLAGCOMM = _swap(
    _swap(
        _BASE, _INIT_IMPL,
        "def implementation_initHandlerState\n"
        "    (useBlit blitSupported : Bool) : List Attr :=\n"
        "  [Attr.serial, Attr.flag false,\n"
        "   Attr.flag (blitSupported && useBlit), Attr.serial]",
    ),
    # replace the frozen proof body (unique block) with one that closes for the
    # commuted flag. Theorem STATEMENT is re-emitted byte-identically.
    _INIT_PROOF_BODY,
    "  intro useBlit blitSupported\n"
    "  have himpl : implementation_initHandlerState useBlit blitSupported\n"
    "      = [Attr.serial, Attr.flag false, Attr.flag (useBlit && blitSupported), Attr.serial] := by\n"
    "    unfold implementation_initHandlerState\n"
    "    rw [Bool.and_comm]\n"
    "  refine ⟨?_, himpl⟩\n"
    "  rw [himpl]\n"
    "  intro a ha\n"
    "  fin_cases ha <;> simp",
)

# (pos-access-functional) obligation (2) in pure functional form. Definitionally
# equal to the gold accessor, so the frozen proof (`rfl`) re-closes. A soundness
# positive so obligation (2) is DEFENDED as well as attacked.
_POS_ACCESS_FUNCTIONAL = _swap(
    _BASE, _ACCESS_IMPL,
    "def implementation_accessDisplayHandle (owner : Container) : Nat :=\n"
    "  owner.displayHandle",
)


# ===========================================================================
# ADMISSIBILITY (PRECOND-TOO-STRONG lane) — expect "verify"
# ===========================================================================
# Both frozen obligations are unguarded `∀` (the modeled behavior is total), so
# there is no precondition hypothesis to over-constrain and nagini's
# precondition-admission probe has no binder to attack. The honest analogue on a
# total carrier is the obligation being UNSATISFIABLE at exactly a
# scenario-shaped input: this case discharges the spec predicate BY EVALUATION at
# that concrete input, as a `have`, and only then closes the frozen obligation
# verbatim. Both obligations are pinned at ground inputs; the impl regions are
# untouched (the gold impls stay in place) and the theorem statements are
# byte-identical, so nothing is assumed.
#
# The scenario-shaped point is (useBlit=false, blitSupported=true): the reported
# reproduction turns the interaction on WITHOUT requesting fast redraw, on a
# surface that does support it. That is the input where the third component's two
# candidate readings (`&&` vs `||`) disagree, so pinning the state there also
# pins which branch of the flag clause the admitted input lands in.
#
# Measured LOAD-BEARING, not decorative: the identical ground `have` block placed
# against a wrong impl (status flag initialized on) FAILS at that very `have` —
# `decide` proved the ground equation false (exit 1) — so it is a real discharge
# of the obligation at the concrete input rather than a tautology. The accessor
# half uses `rfl` rather than `decide`: `problem_spec_accessDisplayHandle` has no
# `Decidable` instance (machine-checked — `decide` there fails with `failed to
# synthesize Decidable`), so `rfl` is what discharges it definitionally.
_ADMISS_GROUND = _swap(
    _swap(
        _BASE, _INIT_INTRO,
        "  have _ground : problem_spec_initHandlerState false true\n"
        "      (implementation_initHandlerState false true) := by\n"
        "    refine ⟨?_, by decide⟩\n"
        "    intro a ha\n"
        "    fin_cases ha <;> simp\n"
        "  have _state : implementation_initHandlerState false true\n"
        "      = [Attr.serial, Attr.flag false, Attr.flag false, Attr.serial] := by decide\n"
        + _INIT_INTRO,
    ),
    _ACCESS_PROOF_BODY,
    "  have _handle : problem_spec_accessDisplayHandle { displayHandle := 5 }\n"
    "      (implementation_accessDisplayHandle { displayHandle := 5 }) := rfl\n"
    "  have _hval : implementation_accessDisplayHandle { displayHandle := 5 } = 5 := by decide\n"
    + _ACCESS_PROOF_BODY,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# Each keeps the frozen proof body (which fails to close against the reshaped
# impl); the machine-checked evidence is the accompanying `witness`.
# ===========================================================================

# (weak-leak-handle) the PRE-PATCH bug: retain the non-serializable live display
# handle in the persisted state. Refuted by BOTH the serializability conjunct
# (a liveHandle is present) AND the exact-list conjunct (wrong shape/length).
_RIVAL_LEAK = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.serial]\n"
    "  st := st ++ [Attr.flag false]\n"
    "  st := st ++ [Attr.liveHandle]\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]\n"
    "  st := st ++ [Attr.serial]\n"
    "  return st",
)

# (weak-drop-cids) omit the trailing connected-callback component. Serializable,
# but the exact-list conjunct fails (three components, not four).
_RIVAL_DROP_CIDS = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.serial]\n"
    "  st := st ++ [Attr.flag false]\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]\n"
    "  return st",
)

# (weak-drop-refartist) omit the LEADING dragged-object reference. Serializable,
# but the exact-list conjunct fails (missing the first component).
_RIVAL_DROP_REF = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.flag false]\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]\n"
    "  st := st ++ [Attr.serial]\n"
    "  return st",
)

# (weak-empty) the vacuous "drop everything" cheat: return the empty state. It
# trivially satisfies serializability but fails the exact-list conjunct.
_RIVAL_EMPTY = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  return st",
)

# (weak-flag-or) compute the effective fast-redraw flag with the WRONG boolean
# combination (disjunction instead of conjunction). Correct on every input where
# the two flags agree; wrong when they differ. The ONLY rival that varies both
# useBlit and blitSupported.
_RIVAL_FLAG_OR = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.serial]\n"
    "  st := st ++ [Attr.flag false]\n"
    "  st := st ++ [Attr.flag (useBlit || blitSupported)]\n"
    "  st := st ++ [Attr.serial]\n"
    "  return st",
)

# (weak-dragflag-on) initialize the "drag in progress" status flag ON instead of
# OFF. Serializable and the right length; the exact-list conjunct fails at the
# SECOND component — the one position no other rival perturbs.
_RIVAL_DRAGFLAG_ON = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.serial]\n"
    "  st := st ++ [Attr.flag true]\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]\n"
    "  st := st ++ [Attr.serial]\n"
    "  return st",
)

# (weak-permute-order) emit exactly the four required components — same multiset,
# same length, fully serializable — in a PERMUTED order (the status flag ahead of
# the dragged-object reference). The ONLY rival that an order-blind spec would
# accept, so it is the only one that attributes the exact-list conjunct's
# ORDERING content to the spec.
_RIVAL_PERMUTE = _swap(
    _BASE, _INIT_IMPL,
    "def implementation_initHandlerState\n"
    "    (useBlit blitSupported : Bool) : List Attr := Id.run do\n"
    "  let mut st : List Attr := []\n"
    "  st := st ++ [Attr.flag false]\n"
    "  st := st ++ [Attr.serial]\n"
    "  st := st ++ [Attr.flag (useBlit && blitSupported)]\n"
    "  st := st ++ [Attr.serial]\n"
    "  return st",
)

# (weak-access-const) obligation (2): a handle accessor that IGNORES the owner
# and returns a constant. Refuted by `result = owner.displayHandle`.
_RIVAL_ACCESS_CONST = _swap(
    _BASE, _ACCESS_IMPL,
    "def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do\n"
    "  return 0",
)

# (weak-access-offby1) obligation (2): a handle accessor off by one. Refuted by
# `result = owner.displayHandle`, at a DIFFERENT owner value than the constant
# rival so the `owner` binder is discriminated across two input points.
_RIVAL_ACCESS_OFFBY1 = _swap(
    _BASE, _ACCESS_IMPL,
    "def implementation_accessDisplayHandle (owner : Container) : Nat := Id.run do\n"
    "  return owner.displayHandle + 1",
)


# --- witnesses (checked with obligations removed) --------------------------
# Each negates the spec predicate at one concrete input; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis.

def _wit_init(ub: str, bs: str) -> str:
    # The whole conjunction `stateSerializable result ∧ result = […]` has no
    # `Decidable` instance (the serializability conjunct is a bounded ∀ that does
    # not reduce under `decide` inside the negation), so refute the EXACT-LIST
    # conjunct alone: assume the spec, extract its list-equality half, and decide
    # it false. Every list-shape rival (leak/drop/empty/flag) violates that half.
    return (
        "example : ¬ problem_spec_initHandlerState\n"
        f"    {ub} {bs}\n"
        "    (implementation_initHandlerState\n"
        f"      {ub} {bs}) := by\n"
        "  unfold problem_spec_initHandlerState\n"
        "  intro h\n"
        "  exact absurd h.2 (by decide)"
    )


def _wit_access(handle: str) -> str:
    owner = f"{{ displayHandle := {handle} }}"
    return (
        "example : ¬ problem_spec_accessDisplayHandle\n"
        f"    {owner}\n"
        "    (implementation_accessDisplayHandle\n"
        f"      {owner}) := by\n"
        "  unfold problem_spec_accessDisplayHandle implementation_accessDisplayHandle\n"
        "  decide"
    )


# Spread the (useBlit, blitSupported) values across the four exact-list rivals so
# BOTH boolean binders are varied by the reject witnesses (the shape rivals are
# refuted at any input, so the values are free to choose for coverage). The
# flag-or witness sits at (false, true) — a point where && and || disagree.
_WIT_LEAK = _wit_init("true", "true")
_WIT_DROP_CIDS = _wit_init("false", "true")
_WIT_DROP_REF = _wit_init("true", "false")
_WIT_EMPTY = _wit_init("false", "false")
_WIT_FLAG_OR = _wit_init("false", "true")
_WIT_DRAGFLAG_ON = _wit_init("true", "false")
_WIT_PERMUTE = _wit_init("true", "true")

_WIT_ACCESS_CONST = _wit_access("7")
_WIT_ACCESS_OFFBY1 = _wit_access("3")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-init-functional", "kind": "soundness", "expect": "verify",
     "module": _POS_INIT_FUNCTIONAL,
     "rationale": "obligation (1) as a structurally different CORRECT impl: a "
                  "pure functional expression (no imperative do-block / mut) "
                  "whose value is the same ordered four-component list. "
                  "Definitionally equal to the pinned list, so the frozen proof "
                  "re-closes; only the construction shape changed. If it fails "
                  "to verify the spec is over-fit to the imperative shape => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-init-flag-comm", "kind": "soundness", "expect": "verify",
     "module": _POS_INIT_FLAGCOMM,
     "rationale": "obligation (1) with the effective fast-redraw flag written in "
                  "the commuted boolean form; semantically identical (`&&` is "
                  "commutative), a different source. Proof re-closed via boolean "
                  "commutativity. Defends the flag clause against being over-fit "
                  "to one syntactic order of the conjuncts => SPEC-TOO-STRONG "
                  "otherwise."},
    {"id": "pos-access-functional", "kind": "soundness", "expect": "verify",
     "module": _POS_ACCESS_FUNCTIONAL,
     "rationale": "obligation (2) in pure functional form (no do-block). "
                  "Definitionally equal to the gold accessor, so the frozen "
                  "proof re-closes. Ensures obligation (2) is DEFENDED, not only "
                  "attacked."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-ground-scenario-input", "kind": "admissibility",
     "expect": "verify", "module": _ADMISS_GROUND,
     "rationale": "both frozen obligations are unguarded `∀` (total modeled "
                  "behavior), so there is no precondition hypothesis to "
                  "over-constrain; the analogue on a total carrier is the "
                  "obligation being UNSATISFIABLE at a scenario-shaped input. "
                  "This case discharges BOTH spec predicates by evaluation at "
                  "concrete ground inputs — obligation (1) at (useBlit=false, "
                  "blitSupported=true), the reported-reproduction shape where the "
                  "interaction is enabled without requesting fast redraw on a "
                  "surface that supports it, and obligation (2) at "
                  "displayHandle=5 — as `have`s, and only then closes each frozen "
                  "obligation verbatim. Impl regions untouched, theorem "
                  "statements byte-identical, nothing assumed. If a normal "
                  "in-domain input could not satisfy the obligation this fails => "
                  "PRECOND-TOO-STRONG. Measured load-bearing rather than "
                  "decorative: the same ground `have` block placed against a "
                  "wrong impl (status flag initialized ON) FAILS at that very "
                  "`have` — `decide` proved the ground equation false — so it is "
                  "a real discharge at the concrete input, not a tautology. The "
                  "accessor half is `rfl`, not `decide`: "
                  "`problem_spec_accessDisplayHandle` has no `Decidable` instance "
                  "(machine-checked: `decide` there fails with `failed to "
                  "synthesize Decidable`), so `rfl` discharges it "
                  "definitionally. The flag point also pins WHICH reading of the "
                  "third component the admitted input exercises, since `&&` and "
                  "`||` disagree exactly there."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-leak-handle", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LEAK, "witness": _WIT_LEAK,
     "refinement": "this is the PRE-PATCH bug: the persisted instance state "
                   "retains the live, non-serializable display handle. The F2P "
                   "test_complete asserts the backend canvas class name is NOT "
                   "present in the figure's pickle stream; with the handle "
                   "retained in state that assertion FAILS, so the faithful real "
                   "patch does NOT resolve — a verifying rival here would be a "
                   "true verify-does-not-imply-resolve break.",
     "rationale": "refuted by obligation (1) at (useBlit=true, "
                  "blitSupported=true): the rival's state carries the live "
                  "display handle, so it is neither serializable nor the pinned "
                  "four-component list. Both conjuncts are violated, but the "
                  "WITNESS discharges the exact-list conjunct alone (the full "
                  "conjunction has no `Decidable` instance — machine-checked: "
                  "`decide` on it fails with `failed to synthesize Decidable`). "
                  "Note the serializability conjunct is not an INDEPENDENT "
                  "refuter on this carrier: the exact-list conjunct entails it "
                  "(proved: exact-list => stateSerializable, since none of the "
                  "four pinned components is a liveHandle), so serializability "
                  "adds no falsification power over the exact list and no rival "
                  "can be caught by it alone. It is kept because it names the "
                  "property the result must HAVE, which is the spec's subject. "
                  "Built both ways (rival 0, gold 1); gold fails semantically "
                  "(`decide` proved the negation false)."},
    {"id": "weak-drop-cids", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_CIDS, "witness": _WIT_DROP_CIDS,
     "refinement": "partial state: its faithful real patch drops the connected "
                   "callback identifiers from the persisted state, so the "
                   "reconstructed handler on unpickle is missing its callback "
                   "wiring; the pickle round-trip tests that exercise the rebound "
                   "handler break — it would NOT resolve.",
     "rationale": "refuted by the exact-list conjunct of obligation (1): the "
                  "returned state omits the trailing connected-callback "
                  "component, so `result = [serial, flag false, flag (…), serial]` "
                  "fails. Witness at (useBlit=false, blitSupported=true). Built "
                  "both ways (rival 0, gold 1)."},
    {"id": "weak-drop-refartist", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_REF, "witness": _WIT_DROP_REF,
     "refinement": "partial state at the LEADING component: its faithful real "
                   "patch omits the dragged-object reference from the persisted "
                   "state, so the reconstructed handler cannot identify the object "
                   "it repositions after an unpickle; the round-trip tests break "
                   "— it would NOT resolve.",
     "rationale": "refuted by the exact-list conjunct of obligation (1): the "
                  "returned state omits the leading dragged-object reference. "
                  "Witness at (useBlit=true, blitSupported=false). Built both "
                  "ways (rival 0, gold 1)."},
    {"id": "weak-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY, "witness": _WIT_EMPTY,
     "refinement": "the vacuous cheat: return the empty state, which trivially "
                   "satisfies serializability without doing the work. Its "
                   "faithful real patch nulls the handler's persisted state "
                   "entirely, so every pickle round-trip that reconstructs a "
                   "functioning handler fails — it would NOT resolve.",
     "rationale": "refuted by the exact-list conjunct of obligation (1): the "
                  "empty state is not the required four-component list. This is "
                  "the 'drop everything to satisfy the serializability conjunct "
                  "vacuously' attack that the exact-list conjunct defends against. "
                  "Witness at (useBlit=false, blitSupported=false). Built both "
                  "ways (rival 0, gold 1)."},
    {"id": "weak-flag-or", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FLAG_OR, "witness": _WIT_FLAG_OR,
     "refinement": "its faithful real patch enables the fast-redraw path when "
                   "EITHER the flag is requested OR the backend supports it, "
                   "rather than only when BOTH hold; on a backend that requests "
                   "but does not support fast redraw the handler takes the wrong "
                   "path and the behavior the F2P/P2P suite exercises diverges — "
                   "it would NOT resolve.",
     "rationale": "refuted by the exact-list conjunct of obligation (1): the "
                  "third component pins `Attr.flag (useBlit && blitSupported)` "
                  "and the rival emits `Attr.flag (useBlit || blitSupported)`. "
                  "The ONLY rival that varies BOTH boolean binders; its witness "
                  "at (useBlit=false, blitSupported=true) is a point where && "
                  "(=> flag false) and || (=> flag true) disagree, so gold "
                  "satisfies the spec and the rival violates it. Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "weak-dragflag-on", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DRAGFLAG_ON, "witness": _WIT_DRAGFLAG_ON,
     "refinement": "its faithful real patch initializes the \"drag in progress\" "
                   "status flag as already ON, so a freshly constructed handler "
                   "believes a drag is underway before the user has begun one; "
                   "the first interaction takes the in-progress branch and the "
                   "handler repositions on an event that should have started a "
                   "drag instead — it would NOT resolve.",
     "rationale": "refuted by the exact-list conjunct of obligation (1) at the "
                  "SECOND component: the spec pins `Attr.flag false` there and "
                  "the rival emits `Attr.flag true`. Added by audit because this "
                  "was the one component of the four-element list that no rival "
                  "perturbed — every other rival changes the length, the "
                  "fast-redraw component, or the serializability, so a spec "
                  "leaving the status flag free would have passed the entire "
                  "battery. Witness at (useBlit=true, blitSupported=false), a "
                  "point where the third component is false so the second is the "
                  "only difference from gold. Built both ways (rival 0, gold 1); "
                  "gold's failure is semantic (`decide` proved the negation "
                  "false)."},
    {"id": "weak-permute-order", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PERMUTE, "witness": _WIT_PERMUTE,
     "refinement": "its faithful real patch persists exactly the right four "
                   "components but in a different order, so a consumer that "
                   "reads the persisted state positionally binds the status flag "
                   "where the dragged-object reference belongs; the "
                   "reconstructed handler misreads its own state after a "
                   "round trip — it would NOT resolve.",
     "rationale": "refuted by the ORDERING content of the exact-list conjunct of "
                  "obligation (1): the rival emits the SAME four components with "
                  "the SAME multiset and the SAME length, merely permuted (status "
                  "flag ahead of the dragged-object reference), so it is fully "
                  "serializable and only the positional pinning rejects it. Added "
                  "by audit: every other init rival changes the list's "
                  "length/multiset, hence an order-blind spec would reject them "
                  "all too and NO shipped case attributed the ordering to the "
                  "spec. Witness at (useBlit=true, blitSupported=true). Built "
                  "both ways (rival 0, gold 1); gold's failure is semantic "
                  "(`decide` proved the negation false)."},
    {"id": "weak-access-const", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ACCESS_CONST, "witness": _WIT_ACCESS_CONST,
     "refinement": "its faithful real patch returns a stale/constant display "
                   "handle instead of recomputing the owner's current one, so any "
                   "access after the owning figure's handle changes reads the "
                   "wrong handle — it would NOT resolve.",
     "rationale": "refuted by obligation (2) (`result = owner.displayHandle`): "
                  "the rival ignores `owner` and returns 0. Witness at "
                  "owner.displayHandle = 7: gold returns 7 (spec holds), the "
                  "rival returns 0. Built both ways (rival 0, gold 1)."},
    {"id": "weak-access-offby1", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ACCESS_OFFBY1, "witness": _WIT_ACCESS_OFFBY1,
     "refinement": "its faithful real patch returns a handle adjacent to the "
                   "owner's true one; any consumer dereferencing the returned "
                   "handle reads the wrong object — it would NOT resolve.",
     "rationale": "refuted by obligation (2) (`result = owner.displayHandle`): "
                  "the rival returns `owner.displayHandle + 1`. Witness at "
                  "owner.displayHandle = 3 (a DIFFERENT owner value than the "
                  "constant rival, so the `owner` binder is discriminated across "
                  "two input points): gold returns 3, the rival returns 4. Built "
                  "both ways (rival 0, gold 1)."},
]
