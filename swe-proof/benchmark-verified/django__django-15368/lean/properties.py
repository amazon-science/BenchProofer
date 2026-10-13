# properties.py — G-PBT falsification battery for django__django-15368 (lean).
#
# NOT a Lean module; a record of adversarial spec cases parsed by the G-PBT gate.
# Each case is a FULL Solution.lean variant with the FROZEN spec untouched: only
# the impl region body (and, for verifying cases, the proof body) is swapped, so
# `same_spec` holds by construction and the `theorem correct_bulkUpdateBranches`
# STATEMENT stays byte-identical across every case.
#
# Ported from the nagini sibling battery. CARRIER NOTE: the nagini bundle
# contracted `build_wrap_flags(in_family, resolvable) -> List[bool]` — a fold that
# pins one boolean per element, keyed on `resolvable` alone. THIS bundle models
# the same loop body more richly: it consumes `objs : List (Nat × AttrValue)` and
# produces `List CaseBranch`, pinning for EVERY record its identity (`pk`), the
# carried value identity (`valueIdent`), and the wrap flag (`wrapped`). The
# nagini "decide on resolvable, not on membership" argument survives verbatim as
# the wrapped-flag clause of the postcondition; the pk/valueIdent clauses are new
# structural surface this bundle exposes and the battery attacks them too.
#
# Defended surface (spec view): the produced branch list is fully pinned to the
# input batch — one branch per record in order (length clause), each keeping its
# record identity, each carrying the same underlying value identity, and each
# wrapped as a literal EXACTLY when the value does NOT resolve to a database
# reference. The whole carrier is TRANSPARENT: `ValueKind` derives DecidableEq
# and `resolvesToReference` is a concrete def, so every reject witness is a
# `decide`-checkable disequality at a concrete input — no opaque callee, so no
# carrier-conditioning is needed.
#
# ADMISSIBILITY: landed as `admiss-f2p-input`. The frozen obligation carries no
# precondition, and that alone is NOT a reason to drop this lane — the analogue on
# a total carrier is the obligation being unsatisfiable at exactly an F2P-shaped
# input, which the case tests by discharging the spec at one concrete
# discriminating-kind record by EVALUATION before closing the frozen obligation
# verbatim. Without it this battery would test only two of the three directions
# the gate exists to test.
#
# VACUOUS classes (stated, not fabricated):
#  * Frame / permission-mutation rivals (nagini's mandatory pair, writing the
#    read-only inputs): the PERMISSION half is vacuous here — Lean is
#    referentially transparent, so there is no fractional permission to be
#    insufficient and no aliasing to observe a write through. But the two nagini
#    cases do NOT both collapse, and an earlier revision of this note wrongly
#    wrote off both:
#      - nagini's write to the RESOLVABILITY input has a live VALUE-level shadow
#        on this carrier: an impl may overwrite the behavioral kind it was handed
#        before deciding, forcing every value to look reference-resolving. That is
#        observable through the wrapped-flag clause, so it is landed below as
#        `rival-input-kind-overwritten` — not written off.
#      - nagini's write to the MEMBERSHIP input genuinely collapses: the wrap
#        decision never reads narrow-category membership, so remapping a direct
#        query node to a field reference is invisible to the spec. Machine-checked
#        on this carrier: `∀ k, resolvesToReference (if k = directExpression then
#        fieldReference else k) = resolvesToReference k` closes by `cases k <;> rfl`
#        (elaborated, exit 0). No observable rival exists for that half, so it is
#        dropped for a demonstrated reason rather than an asserted one.
#  * Divergence / non-termination: NOT shippable here, and the earlier note gave
#    the wrong reason ("a diverging impl cannot be written at all"). Both halves
#    were re-measured with real builds:
#      - as a TOTAL `def`, a body with no decreasing measure is not an admissible
#        variant at all: the module itself fails to elaborate with `fail to show
#        termination for implementation_bulkUpdateBranches / failed to infer
#        structural recursion` (exit 1), so there is no rival file to witness
#        against — the rejection is the elaborator refusing the variant, not the
#        spec refuting it.
#      - as a `partial def`, the diverging impl IS writable and IS rejected, but no
#        witness can discriminate it: the frozen `decide` witness fails with
#        `Tactic decide failed … instDecidableNot did not reduce to isTrue or
#        isFalse` (reduction stuck at the opaque `partial` constant), which is the
#        gate's own `witness-undecided` screen — an exit code that carries no
#        information about the claim.
#    So the class is a KNOWN HOLE on this carrier (no discriminating witness
#    exists), not a vacuous class, and it is recorded as such rather than as
#    "unwritable". Contrast velvet, whose `partial` semantics makes it vacuous by
#    a different route (the corpus-wide termination-semantics finding).
#  * AXIOM_TESTS: dropped — the axiom lane is G-AX's job; this gate ignores it.
#    (This bundle has no consumed callee axiom anyway; the wrapping decision is
#    modeled deeply.)
from pathlib import Path

INSTANCE = "django__django-15368"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Anchors that lie ENTIRELY inside the region they edit and are unique. ---

# The per-record wrap DECISION (inside the impl region). Rivals that keep the
# gold loop shape and only change WHICH values get wrapped swap this line alone.
# The frozen proof body is left in place: the reshaped impl no longer matches the
# frozen tactic script, so `correct_bulkUpdateBranches` fails to close and the
# case is REJECTED. Attribution to the spec is supplied by the per-case witness,
# not by the tactic breakage.
_DECISION = "    if !resolvesToReference attr.kind then\n      wrapped := true"

# The per-record branch APPEND (inside the impl region). Rivals attacking the
# pk / valueIdent preservation clauses swap this line alone.
_BRANCH = "whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]"

# The impl-region return (inside the impl region). The length-clause rival swaps
# this line alone.
_RETURN = "  return whenStatements\n"

# The full frozen impl-region and proof-region blocks (for the positive controls,
# which need a matching reproof).
_IMPL_BLOCK = _BASE[_BASE.index("-- impl-start"):_BASE.index("-- impl-end") + len("-- impl-end")]
_PROOF_BLOCK = _BASE[_BASE.index("-- proof-start"):_BASE.index("-- proof-end") + len("-- proof-end")]
assert _BASE.count(_IMPL_BLOCK) == 1
assert _BASE.count(_PROOF_BLOCK) == 1


def _rival_line(anchor, replacement):
    """Swap a single decision/append/return line; leave the frozen proof in place."""
    return _swap(_BASE, anchor, replacement)


def _rival_impl(new_impl_block):
    """Swap the whole impl region (for rivals whose shape changes beyond one line);
    leave the frozen proof in place."""
    return _swap(_BASE, _IMPL_BLOCK, new_impl_block)


def _pos(new_impl_block, new_proof_block):
    m = _swap(_BASE, _IMPL_BLOCK, new_impl_block)
    return _swap(m, _PROOF_BLOCK, new_proof_block)


# ---------------------------------------------------------------------------
# Witnesses. The carrier is transparent, so each witness states the spec
# predicate at a concrete input and derives False. The universal clause is
# instantiated at the failing index; `decide` closes the concrete disequality.
# Confirmed to elaborate against the named rival and FAIL against the frozen
# solution (the two required halves).
# ---------------------------------------------------------------------------

def _wit_wrapped(objs, i, pk, attr):
    """Refute the wrapped/pk/valueIdent clause at record index `i`."""
    return (
        f"example : ¬ problem_spec_bulkUpdateBranches\n"
        f"    {objs}\n"
        f"    (implementation_bulkUpdateBranches\n"
        f"      {objs}) := by\n"
        "  unfold problem_spec_bulkUpdateBranches\n"
        "  rintro ⟨_, h⟩\n"
        f"  have hb := h {i} {pk} {attr} rfl\n"
        "  simp only [implementation_bulkUpdateBranches, Id.run, pure] at hb\n"
        "  exact absurd hb (by decide)"
    )


def _wit_length(objs):
    """Refute the length clause."""
    return (
        f"example : ¬ problem_spec_bulkUpdateBranches\n"
        f"    {objs}\n"
        f"    (implementation_bulkUpdateBranches\n"
        f"      {objs}) := by\n"
        "  unfold problem_spec_bulkUpdateBranches\n"
        "  rintro ⟨hlen, _⟩\n"
        "  simp only [implementation_bulkUpdateBranches, Id.run, pure] at hlen\n"
        "  exact absurd hlen (by decide)"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (expect verify). A structurally-different CORRECT impl of the
# modeled behavior MUST satisfy the frozen spec. Each swaps the impl body AND
# supplies a proof that closes for the new shape (theorem STATEMENT preserved).
# ---------------------------------------------------------------------------

# pos-collapsed-branch: keep the imperative `Id.run do … for …` loop but collapse
# the `if …then wrapped := true` mutation into a single computed boolean
# `let wrapped := !resolvesToReference obj.2.kind`. Same value per element as gold;
# the reproof mirrors the frozen forIn-induction with the branch collapsed.
_POS_COLLAPSED_IMPL = """-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let wrapped := !resolvesToReference obj.2.kind
    whenStatements := whenStatements ++ [⟨obj.1, wrapped, obj.2.ident⟩]
  return whenStatements
-- impl-end"""

_POS_COLLAPSED_PROOF = """-- proof-start
private theorem bulkUpdateBranches_forIn
    (objs : List (Nat × AttrValue)) (init : List CaseBranch) :
    (Id.run (forIn objs init fun obj r =>
      pure (ForInStep.yield (r ++ [(⟨obj.1, !resolvesToReference obj.2.kind, obj.2.ident⟩ : CaseBranch)]))))
    = init ++ objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  induction objs generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

private theorem bulkUpdateBranches_impl_eq (objs : List (Nat × AttrValue)) :
    implementation_bulkUpdateBranches objs
      = objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch)) := by
  unfold implementation_bulkUpdateBranches
  have h2 : (Id.run do
      let r ← forIn objs ([] : List CaseBranch) fun obj r =>
            do
              let wrapped := !resolvesToReference obj.2.kind
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [(⟨obj.1, wrapped, obj.2.ident⟩ : CaseBranch)]))
      pure r)
      = (Id.run (forIn objs ([] : List CaseBranch) fun obj r =>
          pure (ForInStep.yield (r ++ [(⟨obj.1, !resolvesToReference obj.2.kind, obj.2.ident⟩ : CaseBranch)])))) := rfl
  rw [h2, bulkUpdateBranches_forIn]
  simp

theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]
  refine ⟨by simp, ?_⟩
  intro i pk attr hi
  rw [List.getElem?_map, hi]
  rfl
-- proof-end"""

# pos-functional: the cheapest honest impl — drop the loop entirely and return the
# grounded `List.map` the spec pins to. Structurally different from the frozen
# imperative loop; the reproof is `rfl` per element after unfolding the map.
_POS_FUNCTIONAL_IMPL = """-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch :=
  objs.map (fun o => (⟨o.1, !resolvesToReference o.2.kind, o.2.ident⟩ : CaseBranch))
-- impl-end"""

# admiss-f2p-input: the analogue of the sibling battery's `admiss-self-call` on a
# TOTAL carrier. The frozen obligation carries no precondition, so there is no
# `Requires` to establish at a call site; the shippable analogue is the obligation
# being UNSATISFIABLE at exactly an F2P-shaped input, which this case tests
# directly. It keeps the frozen impl AND the frozen proof, and prepends a `have`
# that discharges `problem_spec_bulkUpdateBranches` at one concrete batch whose
# single record carries the discriminating kind (a value that resolves to a
# reference without being a direct query node) — BY EVALUATION (`decide`), so
# nothing is inherited from the frozen tactic script. If the spec could not be
# satisfied at that input the `have` would not close and the case would fail =>
# PRECOND-TOO-STRONG. The `have` is `clear`ed before the frozen obligation is
# closed verbatim, so it cannot contribute to the main proof.
_ADMISS_HAVE = """  have hadmissible : problem_spec_bulkUpdateBranches
      [(4, (⟨42, ValueKind.fieldReference⟩ : AttrValue))]
      (implementation_bulkUpdateBranches
        [(4, (⟨42, ValueKind.fieldReference⟩ : AttrValue))]) := by
    refine ⟨by decide, ?_⟩
    intro i pk attr hi
    match i with
    | 0 =>
      simp only [List.getElem?_cons_zero, Option.some.injEq, Prod.mk.injEq] at hi
      obtain ⟨rfl, rfl⟩ := hi
      decide
    | (n + 1) => simp at hi
  clear hadmissible
"""

_ADMISS_ANCHOR = """        (implementation_bulkUpdateBranches objs) := by
  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]"""

_ADMISS_PROOF = _swap(
    _PROOF_BLOCK, _ADMISS_ANCHOR,
    """        (implementation_bulkUpdateBranches objs) := by
"""
    + _ADMISS_HAVE +
    """  intro objs
  rw [problem_spec_bulkUpdateBranches, bulkUpdateBranches_impl_eq]""")


_POS_FUNCTIONAL_PROOF = """-- proof-start
theorem correct_bulkUpdateBranches :
    ∀ (objs : List (Nat × AttrValue)),
      problem_spec_bulkUpdateBranches objs
        (implementation_bulkUpdateBranches objs) := by
  intro objs
  unfold problem_spec_bulkUpdateBranches implementation_bulkUpdateBranches
  refine ⟨by simp, ?_⟩
  intro i pk attr hi
  rw [List.getElem?_map, hi]
  rfl
-- proof-end"""


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (expect reject). A WRONG impl of the modeled behavior sharing
# the frozen spec must NOT verify; the witness attributes the rejection to the
# spec. Each `refinement` argues why the faithful real patch would still fail F2P.
# ---------------------------------------------------------------------------

# THE BUG (partial-domain, the discriminator). Decide wrapping on membership in
# the narrow "direct query node" category instead of on resolvability — exactly
# the pre-patch behavior. CORRECT on plain values and direct query nodes; WRONG on
# a field reference (resolves to a reference yet is not a direct node), which it
# wraps as a literal instead of passing through.
_RIVAL_MEMBERSHIP = "    if attr.kind != ValueKind.directExpression then\n      wrapped := true"

# Inverted decision: wrap iff the value DOES resolve to a reference — the exact
# opposite of the spec. Wrong on every non-empty batch.
_RIVAL_INVERTED = "    if resolvesToReference attr.kind then\n      wrapped := true"

# Last-element override (partial-domain, tail). Correct on every record except the
# last processed one, whose flag is forced unwrapped regardless of its kind.
_RIVAL_LAST_IMPL = """-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let n := objs.length
  let mut idx := 0
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    if !resolvesToReference attr.kind then
      wrapped := true
    if idx == n - 1 then
      wrapped := false
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
    idx := idx + 1
  return whenStatements
-- impl-end"""

# pk not preserved: key every branch on a constant identity (0) rather than the
# record's own — attacks the pk-preservation clause (a binder no wrapped-flag
# rival exercises).
_RIVAL_PK_CONST = "whenStatements := whenStatements ++ [⟨0, wrapped, attr.ident⟩]"

# valueIdent not preserved: drop the carried value identity (0) — attacks the
# valueIdent-preservation clause.
_RIVAL_IDENT_DROP = "whenStatements := whenStatements ++ [⟨pk, wrapped, 0⟩]"

# Length wrong: drop the first produced branch — attacks the "one branch per
# record" length clause (and per-index alignment).
_RIVAL_DROP_FIRST = "  return whenStatements.tail\n"

# Input-kind overwritten (the value-level shadow of nagini's write-to-the-
# read-only-resolvability-input case). Instead of classifying the value it was
# handed, the impl REPLACES the behavioral kind with a reference-resolving one
# before deciding, so every value is carried through unwrapped. Keeps the value
# identity and the pk, so it is refuted only through the wrapped-flag clause, and
# only at a plain stored value.
_RIVAL_KIND_OVERWRITE = (
    "    let attr := ({ ident := obj.2.ident, kind := ValueKind.fieldReference }"
    " : AttrValue)\n")

# Branch ORDER reversed: prepend instead of append. Every branch is individually
# correct AND the length is right, so this is refuted only by the "in record
# order" reading of the per-index clause — a surface no other rival here attacks
# (the length rival changes the count; the flag/pk/ident rivals corrupt a
# component). Landed after machine-checking that the per-index clause really does
# pin ORDER and not just multiset content.
_RIVAL_REVERSED_IMPL = """-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    if !resolvesToReference attr.kind then
      wrapped := true
    whenStatements := [⟨pk, wrapped, attr.ident⟩] ++ whenStatements
  return whenStatements
-- impl-end"""

# Per-index flag flip at ONE interior position: correct on every single-record
# batch and on every index but the second, so it is invisible to a witness taken
# at index 0 (which is where most of this battery's witnesses sit). Probes that
# the universally quantified index binder really does bind EVERY index rather
# than just the head.
_RIVAL_INDEX1_FLIP_IMPL = """-- impl-start
def implementation_bulkUpdateBranches
    (objs : List (Nat × AttrValue)) : List CaseBranch := Id.run do
  let mut whenStatements : List CaseBranch := []
  let mut idx := 0
  for obj in objs do
    let pk := obj.1
    let attr := obj.2
    let mut wrapped := false
    if !resolvesToReference attr.kind then
      wrapped := true
    if idx == 1 then
      wrapped := !wrapped
    whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]
    idx := idx + 1
  return whenStatements
-- impl-end"""


SPEC_TESTS = [

    # ---------------------------------------------------------------- soundness
    {
        "id": "pos-collapsed-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_COLLAPSED_IMPL, _POS_COLLAPSED_PROOF),
        "rationale": "A correct impl with a DIFFERENT executable shape must verify: "
                     "the gold loop's `if …then wrapped := true` mutation is "
                     "collapsed into one computed boolean `!resolvesToReference "
                     "obj.2.kind`, producing the identical per-record branch. The "
                     "reproof mirrors the frozen forIn-induction with the branch "
                     "collapsed. Else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_FUNCTIONAL_IMPL, _POS_FUNCTIONAL_PROOF),
        "rationale": "Cheapest honest impl: drop the imperative loop and return the "
                     "grounded `List.map` the spec pins to directly. The wrapping "
                     "decision is a transparent def, so this IS the correct answer "
                     "(no oracle echo); the reproof is per-element `rfl` after "
                     "unfolding the map. Structurally different from the frozen "
                     "loop. Must verify (else the spec over-constrains proof shape).",
    },

    # ------------------------------------------------------------ admissibility
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _pos(_IMPL_BLOCK, _ADMISS_PROOF),
        "rationale": "The obligation must be SATISFIABLE at an F2P-shaped input. "
                     "The frozen obligation is precondition-free, so the analogue of "
                     "the sibling battery's admissibility self-call on this total "
                     "carrier is exactly this: discharge "
                     "`problem_spec_bulkUpdateBranches` at one concrete batch whose "
                     "single record carries the discriminating kind — a value that "
                     "resolves to a database reference without being a direct query "
                     "node, at pk 4 with value identity 42 — as a `have`, BY "
                     "EVALUATION (`decide`, not by reusing the frozen script), then "
                     "`clear` it and close the frozen obligation verbatim. If the "
                     "spec's clauses were jointly unsatisfiable at that ordinary "
                     "input (a length clause and a per-index clause that cannot both "
                     "hold, or a wrapped-flag clause contradicting itself on the "
                     "discriminating kind) the `have` would not close => "
                     "PRECOND-TOO-STRONG. This is the third direction the gate "
                     "exists to test and it is NOT vacuous merely because the "
                     "obligation has no precondition.",
    },

    # --------------------------------------------------------------- uniqueness
    {
        "id": "rival-decide-on-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line(_DECISION, _RIVAL_MEMBERSHIP),
        "rationale": "Violates the wrapped-flag clause: it keys the wrap decision on "
                     "membership in the narrow direct-query-node category instead of "
                     "on resolvability. Diverges on any record that resolves to a "
                     "reference without being a direct node (a field reference), "
                     "wrapping (true) what the spec passes through (false). This is "
                     "the precise spec discriminator.",
        "refinement": "This is the pre-patch predicate (decide on the narrow type "
                      "membership). A field reference is wrapped as a verbatim "
                      "literal storing its textual form instead of resolving to the "
                      "named column, so the F2P `test_f_expression` — which asserts "
                      "the rows now match the resolved column value — FAILS. The "
                      "faithful real patch (the unchanged narrow check) does NOT "
                      "resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.fieldReference⟩ : AttrValue))]",
            0, 0, "⟨7, ValueKind.fieldReference⟩"),
    },
    {
        "id": "rival-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line(_DECISION, _RIVAL_INVERTED),
        "rationale": "Violates the wrapped-flag clause on every non-empty batch: it "
                     "wraps iff the value DOES resolve to a reference — the exact "
                     "inverse of the spec. Supporting near-miss with a real "
                     "refinement (the catastrophic inversion); given a distinct "
                     "witness (a plain value) from the membership rival's.",
        "refinement": "The inversion wraps every resolvable expression (storing its "
                      "textual form) and leaves plain values unwrapped (emitting a "
                      "raw datum where a bound literal is required). Both the F2P and "
                      "every existing bulk_update test with plain data would FAIL. "
                      "The faithful real patch does NOT resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue))]",
            0, 0, "⟨7, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-last-element-unwrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_impl(_RIVAL_LAST_IMPL),
        "rationale": "Violates the wrapped-flag clause at the LAST record only: its "
                     "flag is forced unwrapped regardless of kind. Correct on every "
                     "batch whose final value resolves to a reference; wrong "
                     "whenever the final value is a plain stored value that must be "
                     "wrapped. Tail-of-list partial-domain miss; the witness places "
                     "the plain value in a non-initial position so only the "
                     "last-index override refutes it.",
        "refinement": "This carries the final record's plain value through unwrapped, "
                      "emitting a raw datum instead of a bound literal for the last "
                      "branch — diverging from gold on any batch with a "
                      "non-resolvable last value, so the existing bulk_update tests "
                      "with plain last values FAIL. The faithful real patch does NOT "
                      "resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨5, ValueKind.directExpression⟩ : AttrValue)), "
            "(1, (⟨9, ValueKind.plainValue⟩ : AttrValue))]",
            1, 1, "⟨9, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-pk-not-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line(_BRANCH, _RIVAL_PK_CONST),
        "rationale": "Violates the pk-preservation clause: every branch is keyed on a "
                     "constant identity (0) instead of the record's own. This binder "
                     "is exercised by NO wrapped-flag rival; the witness uses a "
                     "record with pk ≠ 0 so the constant-key rival is refuted while "
                     "the frozen impl holds.",
        "refinement": "Keying every WHEN branch on the same record identity makes the "
                      "conditional update rewrite the wrong rows (all-but-one records "
                      "get no branch, or the wrong one), so every bulk_update test "
                      "that updates more than one object FAILS. The faithful real "
                      "patch does NOT resolve.",
        "witness": _wit_wrapped(
            "[(3, (⟨7, ValueKind.plainValue⟩ : AttrValue))]",
            0, 3, "⟨7, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-value-identity-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line(_BRANCH, _RIVAL_IDENT_DROP),
        "rationale": "Violates the valueIdent-preservation clause: the carried "
                     "underlying value identity is replaced by a constant (0) rather "
                     "than passed through. Attacks a binder distinct from pk and the "
                     "wrap flag; witness uses a record with valueIdent ≠ 0.",
        "refinement": "Discarding the underlying value identity stores a wrong "
                      "constant value in every branch, so the updated rows hold the "
                      "wrong data and every bulk_update value-assertion test FAILS. "
                      "The faithful real patch does NOT resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue))]",
            0, 0, "⟨7, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-drop-first-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line(_RETURN, _RIVAL_DROP_FIRST),
        "rationale": "Violates the length clause `result.length = objs.length` (one "
                     "branch per record) and the per-index alignment: it drops the "
                     "first produced branch. "
                     "Wrong on every batch of ≥ 1 record; witness uses a two-record "
                     "batch so the length mismatch is decidable.",
        "refinement": "Emitting one fewer WHEN branch than there are records leaves "
                      "the first object without a conditional branch, so its row is "
                      "not updated — every multi-object bulk_update test FAILS. The "
                      "faithful real patch does NOT resolve.",
        "witness": _wit_length(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue)), "
            "(1, (⟨8, ValueKind.plainValue⟩ : AttrValue))]"),
    },
    {
        "id": "rival-input-kind-overwritten",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_line("    let attr := obj.2\n", _RIVAL_KIND_OVERWRITE),
        "rationale": "Violates the wrapped-flag clause by refusing to classify the "
                     "value it was GIVEN: it overwrites the behavioral kind with a "
                     "reference-resolving one before deciding, so every value is "
                     "carried through unwrapped no matter what it actually was. This "
                     "is the value-level counterpart of the sibling battery's "
                     "write-to-the-read-only-input probe — the permission half of "
                     "that class is vacuous on a referentially transparent carrier, "
                     "but the observable half is NOT, and this case lands it. "
                     "Distinct from the inverted rival, which still reads the real "
                     "kind and merely negates the decision; this one discards the "
                     "input's kind entirely, so it is wrong on plain stored values "
                     "while agreeing with the inversion nowhere on reference values.",
        "refinement": "Treating every value as reference-resolving stops wrapping "
                      "plain stored data as a literal, so an ordinary string/number "
                      "attribute is emitted as a raw datum where a bound literal is "
                      "required instead of being stored verbatim. Every existing "
                      "batched-update test that writes plain data FAILS, so the "
                      "faithful real patch does NOT resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue))]",
            0, 0, "⟨7, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-branch-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_impl(_RIVAL_REVERSED_IMPL),
        "rationale": "Violates the ORDER half of the per-index clause: every branch "
                     "is individually well-formed (right pk, right carried value "
                     "identity, right wrap flag) and the length is right, so no "
                     "component is corrupted — only the record-to-position "
                     "correspondence is. `objs[i]? = some (pk, attr) → result[i]? = "
                     "some ⟨…⟩` pins branch i to record i, so emitting the branches "
                     "in reverse refutes it at index 0 of any batch of ≥ 2 records "
                     "whose two records differ. This surface is attacked by no other "
                     "rival here: the length rival changes the count, and the flag / "
                     "pk / valueIdent rivals each corrupt a component.",
        "refinement": "Each record still gets exactly one branch carrying its own "
                      "value, so the assembled conditional update is order-permuted "
                      "rather than malformed. That is invisible whenever the branches "
                      "are keyed on distinct record identities — which is why it is a "
                      "genuine near-miss and not a catastrophic break — but the "
                      "modeled contract is per-position, and a batch whose records "
                      "must be emitted in batch order (the `pk` of branch i belonging "
                      "to record i) diverges from gold on the first record. The "
                      "faithful real patch, which touches only which values get "
                      "wrapped and never the emission order, does NOT resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue)), "
            "(1, (⟨8, ValueKind.directExpression⟩ : AttrValue))]",
            0, 0, "⟨7, ValueKind.plainValue⟩"),
    },
    {
        "id": "rival-interior-index-flag-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_impl(_RIVAL_INDEX1_FLIP_IMPL),
        "rationale": "Violates the wrapped-flag clause at ONE interior index only "
                     "(the second record), whose flag is inverted while every other "
                     "index is decided correctly. Correct on every single-record "
                     "batch, so it is invisible to a witness taken at index 0 — where "
                     "most of this battery's witnesses sit — and to the last-element "
                     "rival's tail probe on a 2-record batch only by coincidence of "
                     "position. It probes that the universally quantified index "
                     "binder binds EVERY index rather than just the head; the witness "
                     "is therefore taken at index 1, on the discriminating kind (a "
                     "value that resolves to a reference without being a direct "
                     "query node), so it refutes through the reference-passthrough "
                     "direction rather than the wrap-a-plain-value direction.",
        "refinement": "The second record in each batch gets the opposite carrying "
                      "decision from the one the behavior requires: its "
                      "reference-resolving value is wrapped as a verbatim literal "
                      "(storing its textual form instead of resolving to the named "
                      "column) and, symmetrically, a plain value there is emitted as "
                      "a raw datum. Any batched update of two or more records whose "
                      "second value is a reference FAILS, which includes the F2P "
                      "scenario as soon as the batch is not a singleton. The faithful "
                      "real patch, which decides on resolvability uniformly at every "
                      "position, does NOT resolve.",
        "witness": _wit_wrapped(
            "[(0, (⟨7, ValueKind.plainValue⟩ : AttrValue)), "
            "(1, (⟨8, ValueKind.fieldReference⟩ : AttrValue))]",
            1, 1, "⟨8, ValueKind.fieldReference⟩"),
    },
]

# AXIOM_TESTS: dropped — the axiom lane is G-AX's job and this gate ignores it.
# (This bundle also has no consumed callee axiom: the wrapping decision is modeled
# deeply by `resolvesToReference`, and the `axioms` region is empty.)
AXIOM_TESTS = []
