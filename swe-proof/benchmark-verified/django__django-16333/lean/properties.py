# properties.py — G-PBT falsification battery for django__django-16333 (lean lane).
# NOT a Lean module; a manifest of adversarial cases the gate elaborates against
# the frozen spec. PORTED from the nagini sibling's properties.py, with the
# adversarial ARGUMENT carried over and the mechanics re-expressed against this
# backend's carrier.
#
# DEFENDED SURFACE (read from Solution.lean):
#   implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome
#   Persisting a model-backed form. Three INDEPENDENT top-level postcondition
#   conjuncts pin the whole output record:
#     (C1) result.user.passwordSet = true
#          — the returned instance always carries its derived password,
#            whichever way the commit choice went.
#     (C2) result.instanceSaved = commit
#          — the instance row is written exactly when the caller asked for an
#            immediate commit, and NOT when the commit is deferred.
#     (C3) result.relatedSaved = (if commit then f.m2m else [])
#          — on a committed save the FULL set of the form's own multi-valued
#            related selections is written; on a deferred save none is. This is
#            the discriminating clause: it is grounded in `f.m2m` (the form's own
#            collected selections) rather than in an oracle, so it pins both
#            THAT the selections are written and WHICH ones.
#   Input binders: `f.m2m` (the collected selections), `f.password` (the raw
#   secret the stored password is derived from), and `commit`.
#
# AUDIT FINDING (structural, recorded here because it bounds what the reject lane
# can possibly show). The frozen spec is provably the GRAPH of the frozen impl:
#   theorem (f) (commit) (r) :
#     problem_spec_persistForm f commit r ↔ r = implementation_persistForm f commit
# elaborates (built by the audit lane, exit 0; the reverse direction is
# ⟨rfl,rfl,rfl⟩ and the forward one is `simp_all` after destructuring the record).
# The three conjuncts pin all three fields of `SaveOutcome` by equations whose
# right-hand sides mention only `f` and `commit`, and `UserObj` has exactly one
# field, so the spec leaves no output component free. Consequences, both worth
# stating plainly rather than leaving for a reader to assume:
#   * SPEC-TOO-WEAK is structurally IMPOSSIBLE here, not merely unobserved. Any
#     impl that differs from the frozen one at any input violates the spec at that
#     input, so no rival can verify. The eleven ported rivals plus the three added
#     below therefore do not establish spec strength by sampling; they establish
#     that each named wrong behaviour is observably different on this carrier, and
#     the theorem above is what makes the reject lane exhaustive.
#   * The reject lane's remaining value is CARRIER FAITHFULNESS, not strength: a
#     rival that turned out to be definitionally equal to gold would be vacuous,
#     which is what each witness's gold-side failure rules out case by case.
#   * The graph theorem cuts the OTHER way too, and this is where the residual
#     risk on this cell actually lives: because the spec is the impl's graph,
#     SPEC-TOO-STRONG is the only failure direction still open, and it is tested
#     by the positive lane alone. A second audit pass measured that the four
#     ported positives all agree with the frozen impl DEFINITIONALLY — each
#     closes by `rfl` after casing on the commit choice — so they could not have
#     distinguished "the spec admits every correct impl" from "the spec admits
#     every impl that REDUCES to the frozen one". pos-accumulated-selection was
#     added to close that: its selection set is only extensionally `f.m2m` and
#     its proof needs an induction, no `rfl`.
#
# CARRIER NARROWING vs the nagini sibling — the reason the case shapes differ.
#   The nagini model carried the discriminating fact as an abstract per-form
#   CAPABILITY: a body-less contract-only predicate granted SOLELY by the
#   deferred-relations sub-operation, plus a permission-carrying abstraction
#   predicate over two observable booleans. Nine of its cases are built on that
#   machinery (fabricate the capability by hand; earn it on a throwaway object
#   and hope it transfers; poke the underlying fields and refold; re-derive the
#   whole contract from the routine's own contract under partial correctness).
#   This bundle instead models the outcome VALUE-LEVEL: the selections that were
#   written are a `List Int` in the returned record, determined by the form's own
#   selections. That is a strictly more observable carrier, so the capability
#   attacks do not port as-is — but their ARGUMENT does, and it becomes sharper
#   rather than weaker:
#     * "fabricate the fact instead of doing the work" ports to a rival that
#       writes a selection set it did not get from the form (weak-fiat-selection,
#       weak-foreign-selection) — the value-level twin of forging the capability,
#       and now refutable at a concrete input rather than only by a permission
#       failure.
#     * "earn it on a throwaway object" has NO counterpart: there is no object
#       identity in this carrier at all, only the returned record, so a rival
#       cannot write to "a different form". Omitted; see `assessment`.
#     * "re-derive it from the routine's own contract via self-recursion" has no
#       counterpart either: see the divergence note below.
#   Conversely the value-level carrier exposes an attack surface nagini never
#   had — the CONTENT of the written selection set (a subset, a re-ordering, an
#   added element). Those rivals have no nagini counterpart and are added here so
#   that C3's "the FULL set, as collected" half is a measured claim and not just
#   an "it wrote something" check.
#
# VACUOUS / DROPPED CLASSES (stated per directive, never silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini file's own
#     note records that its input enters with FULL permission (the routine
#     legitimately mutates the form), so "overwrite a read-only input to satisfy
#     a postcondition vacuously" already had no target there; and lean is
#     referentially transparent — there is no aliasable input and no fractional
#     permission to abuse. Nothing to port. The nagini file's designated
#     substitute for this class was the capability-fabrication family, which IS
#     ported, value-level, as weak-fiat-selection / weak-foreign-selection.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean, and vacuous for the
#     carrier's reason, not for the spec's. The nagini sibling carries one such
#     case (weak-self-echo-recursion: under partial correctness a
#     non-terminating body vacuously satisfies every postcondition, so it hands
#     back the discriminating fact for free, while its faithful patch recurses
#     forever and persists nothing). Here `implementation_persistForm` is a
#     TOTAL Lean `def` — a diverging implementation cannot be written at all, so
#     the rival does not exist on this carrier. This is NOT the velvet situation,
#     where `loom.semantics.termination "partial"` makes the same rival verify
#     against a spec that admits it (a known spec hole, measured across the
#     corpus: the corpus-wide termination-semantics finding). On lean the class is genuinely
#     absent; no witness is fabricated for it.
#   * AXIOM lane — DROPPED. `meta.axioms == []`: there is no consumed
#     callee-`opaque`/`axiom` on this path (the persistence sub-operations are
#     A-reference deep models). The axiom lane is G-AX's job and this gate
#     ignores it. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-16333"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly if the
# frozen solution ever changes. The impl region body and the proof TACTIC body
# are the only regions a variant may edit; the spec view, the signature and the
# byte-identical `theorem correct_persistForm` statement are never touched, so
# same_spec holds by construction.

_IMPL_OLD = """\
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  Id.run do
    -- super().save(commit=False): build the instance and install the deferred
    -- related-selection writer (so a writer is always present afterwards).
    let mut user := buildInstance f
    let hasRelatedWriter := true
    -- derive the stored password from the form's raw password (always).
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      -- write the instance row …
      instanceSaved := true
      -- … and, when the related-selection writer is present, write the form's
      -- multi-valued related selections so they are not lost.
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro f commit
  unfold problem_spec_persistForm implementation_persistForm
  cases commit <;> exact ⟨rfl, rfl, rfl⟩"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body and — for a
    soundness positive whose reshaped impl needs a matching tactic script — the
    proof body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


_HEAD = ("def implementation_persistForm (f : FormData) (commit : Bool) : "
         "SaveOutcome :=\n  Id.run do\n")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG. Each is a
# structurally different but behaviourally identical correct impl, shipped WITH
# a tactic script that closes for the new shape. The theorem statement is
# byte-identical; no new lemma, axiom, sorry, or native_decide.
# ---------------------------------------------------------------------------

# pos-guard-dropped: the direct port of the nagini positive control. The inner
# guard on "a related-selection writer is present" is provably true on this code
# path (the build step installs it unconditionally), so dropping it is a
# faithful, structurally different shape that still writes the selections inside
# the committed branch. Verified with the frozen tactic script, which still
# closes because both branches reduce definitionally.
_POS_GUARD = _HEAD + """\
    -- CORRECT, structurally different: the writer-present guard is dropped. The
    -- build step installs the writer unconditionally, so the guard is provably
    -- true here and writing the selections unconditionally inside the committed
    -- branch is behaviourally identical.
    let mut user := buildInstance f
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# pos-pure-functional: the same outcome written as a single record literal — no
# Id.run, no `let mut`, no branch at all (the commit choice is threaded straight
# into the two components that depend on it). Confirms the spec does not
# secretly depend on the imperative encoding or on the branch structure. The
# result is definitionally the spec's RHS, so `exact ⟨rfl, rfl, rfl⟩` closes
# without even casing on the commit choice.
_POS_PURE = """\
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  { user := { buildInstance f with passwordSet := true },
    instanceSaved := commit,
    relatedSaved := if commit then f.m2m else [] }"""

_POS_PURE_PROOF = """\
  intro f commit
  unfold problem_spec_persistForm implementation_persistForm
  exact ⟨rfl, rfl, rfl⟩"""

# pos-step-order-swapped: inside the committed branch, write the related
# selections FIRST and the instance row second. This is the shape whose nagini
# counterpart is a REJECT (there the deferred-relations sub-operation carried a
# precondition demanding the record already written, so reordering broke it).
# On this carrier the two writes are independent components of the returned
# record with no ordering precondition between them, so the reordering is
# behaviourally identical and must VERIFY. Shipping it as a positive rather than
# silently dropping the nagini reject is what makes the carrier difference
# measured instead of assumed — see `assessment`.
_POS_ORDER = _HEAD + """\
    -- CORRECT, structurally different: within the committed branch the two
    -- writes are performed in the opposite order. They are independent output
    -- components, so the order is not observable.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      if hasRelatedWriter then
        relatedSaved := f.m2m
      instanceSaved := true
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# pos-branch-match: the same resolution dispatched by an explicit `match` on the
# commit choice, with each arm building its whole record literally — the two
# observable behaviours spelled out side by side instead of accumulated. A third
# distinct shape (neither the frozen accumulator nor the branch-free literal).
_POS_MATCH = """\
def implementation_persistForm (f : FormData) (commit : Bool) : SaveOutcome :=
  match commit with
  | true  => { user := { buildInstance f with passwordSet := true },
               instanceSaved := true,  relatedSaved := f.m2m }
  | false => { user := { buildInstance f with passwordSet := true },
               instanceSaved := false, relatedSaved := [] }"""

# pos-accumulated-selection: the EXTENSIONAL positive. Every other positive in
# this battery agrees with the frozen impl DEFINITIONALLY — each closes by `rfl`
# (or `exact ⟨rfl, rfl, rfl⟩`) once the two branches are cased, so the whole
# soundness lane could have been passing merely because every shape it tries
# reduces to the frozen one by computation. That is a weaker claim than the lane
# is supposed to make: it leaves untested whether the spec admits a correct impl
# whose written selection set is only EXTENSIONALLY `f.m2m`.
#
# This impl builds the selection set by accumulating the form's collected
# selections one at a time (`acc := acc ++ [i]` in a `for`), which is the shape a
# real relation writer has. `acc` is provably `f.m2m` but not definitionally so:
# the proof needs a genuine induction (the `key` lemma below, an in-proof `have`
# so no new top-level declaration appears) plus the `Id.run`/`forIn` unfolding.
# If the spec admitted only impls that reduce to the frozen one, this would fail;
# it verifies, so C3's equality is a real extensional constraint rather than a
# demand for the frozen syntactic form.
_POS_ACCUM = _HEAD + """\
    -- CORRECT, structurally different, and only EXTENSIONALLY equal to the
    -- frozen impl: the selections to write are accumulated one at a time rather
    -- than handed over as the collected list. The accumulated list is provably
    -- but not definitionally `f.m2m`.
    let mut user := buildInstance f
    user := { user with passwordSet := true }
    let mut acc : List Int := []
    for i in f.m2m do
      acc := acc ++ [i]
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      relatedSaved := acc
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

_POS_ACCUM_PROOF = """\
  intro f commit
  have key : ∀ (l pre : List Int),
      (l.foldl (fun acc i => acc ++ [i]) pre) = pre ++ l := by
    intro l
    induction l with
    | nil => intro pre; simp
    | cons a t ih => intro pre; simp [ih]
  unfold problem_spec_persistForm implementation_persistForm
  cases commit <;>
    (simp [Id.run, key]; try exact ⟨rfl, rfl, rfl⟩)"""


# admiss-both-commit-choices: the port of the nagini admissibility control.
# Nagini asserted the entry/exit shape in-body with `Assert(...)` at the
# F2P-shaped input; the lean analogue states the corresponding claims as in-body
# `have`s discharged by `decide`. `theorem correct_persistForm` is a bare ∀ over
# both binders with NO precondition hypothesis, so there is no
# precondition-satisfiability claim to make; admissibility on this carrier is
# instead the pair of claims that the spec ADMITS the intended outcome at each
# exercised input (satisfiable there, not over-constrained) and is NOT VACUOUS
# there (at the committed input it rejects the outcome that writes the row but
# drops the form's collected selections).
#
# AUDIT NOTE (repaired). The ported form of this case stated its two `have`s as
# `(if true then [7] else []) = [7]` and `(if false then [7] else []) = []`.
# Those are `ite`-reduction tautologies of Lean itself: both were re-derived in a
# file importing only Mathlib, with no spec, no impl and no `FormData` in scope,
# and elaborated (exit 0). They therefore mention neither
# `problem_spec_persistForm` nor any input the case claims to exercise, and would
# have held verbatim against an arbitrarily weakened spec — so the case verified
# honestly while attesting nothing. Measured: with C3 deleted from the spec view,
# the old `have`s still produced no error, whereas the replacements below fail on
# `_hCommittedNotVacuous` (`decide` proves the negation false). Each `have` now
# names the concrete outcome record, since `implementation_persistForm` cannot
# occur inside its own body, and each unfolds the spec before deciding because
# `problem_spec_persistForm` is a `def ... : Prop` with no `Decidable` instance
# until unfolded (`decide` alone fails to synthesize one).
_ADMISS = _HEAD + """\
    -- Admissibility witness, stated against the SPEC ITSELF at the two shapes the
    -- caller actually exercises: a committed save of a form carrying a selection,
    -- and a deferred save. (a) the spec admits the intended outcome at each; and
    -- (b) at the committed input it is not vacuous — it rejects the outcome that
    -- writes the row but drops the collected selections.
    have _hCommittedAdmitted :
        problem_spec_persistForm { password := "s3cr3t", m2m := [7] } true
          { user := { passwordSet := true }, instanceSaved := true,
            relatedSaved := [7] } := by
      unfold problem_spec_persistForm; decide
    have _hDeferredAdmitted :
        problem_spec_persistForm { password := "s3cr3t", m2m := [7] } false
          { user := { passwordSet := true }, instanceSaved := false,
            relatedSaved := [] } := by
      unfold problem_spec_persistForm; decide
    have _hCommittedNotVacuous :
        ¬ problem_spec_persistForm { password := "s3cr3t", m2m := [7] } true
          { user := { passwordSet := true }, instanceSaved := true,
            relatedSaved := [] } := by
      unfold problem_spec_persistForm; decide
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each edits ONLY the
# impl region and ships a `witness` that has been SEEN to discriminate: it
# elaborates against the rival and FAILS against the frozen solution.
# ---------------------------------------------------------------------------

# weak-selections-dropped: the pre-change behaviour. On a committed save the
# instance row is written but the form's collected multi-valued selections never
# are — they are silently discarded. Ports nagini weak-prepatch-no-deferred.
_WEAK_DROPPED = _HEAD + """\
    -- WRONG (pre-change): the committed branch writes the instance row only; the
    -- form's collected multi-valued selections are never written.
    let mut user := buildInstance f
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let relatedSaved : List Int := []
    if commit then
      instanceSaved := true
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-dead-guard: keeps the selection-write call SHAPE but guards it on a
# condition that is provably false wherever it is evaluated (the instance row
# has just been written, so "the row is not yet written" never holds), making
# the write dead code. Ports nagini weak-dead-guard-skips-deferred.
_WEAK_DEAD_GUARD = _HEAD + """\
    -- WRONG: the selection write is guarded on the instance row NOT having been
    -- written, which is false right after writing it — so the write is dead code
    -- and the selections are never persisted.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter && instanceSaved = false then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-selections-always: writes the collected selections regardless of the
# commit choice, so a DEFERRED save persists them anyway. Ports the deferred-save
# half of nagini weak-unconditional-persist, aimed at C3's `else []` arm.
_WEAK_ALWAYS_REL = _HEAD + """\
    -- WRONG: the selections are written whatever the commit choice, so a
    -- deferred save persists them instead of postponing them.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
    if hasRelatedWriter then
      relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-row-always: writes the instance row regardless of the commit choice, so a
# deferred save persists it. Ports the instance-row half of nagini
# weak-unconditional-persist, aimed at C2.
_WEAK_UNCOND_ROW = _HEAD + """\
    -- WRONG: the instance row is written whatever the commit choice, so a
    -- deferred save persists it instead of postponing it.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let instanceSaved := true
    let mut relatedSaved : List Int := []
    if commit then
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-password-undone: never applies the derived password to the built
# instance. No nagini counterpart at the value level (nagini's carrier tracked
# the password step as having no observable persistence effect and so could not
# attack it); on this carrier it is C1, an independent conjunct that would
# otherwise be attacked by no rival at all.
_WEAK_NO_PASSWORD = _HEAD + """\
    -- WRONG: the derived password is never applied to the built instance, so the
    -- returned instance does not carry it.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-fiat-selection: the value-level port of the nagini fiat/fabrication
# family. Instead of writing the selections the form collected, it writes a
# fixed selection set of its own — "the relations are done" asserted by fiat,
# with nothing read from the form.
_WEAK_FIAT = _HEAD + """\
    -- WRONG (fiat): on a committed save it writes a fixed selection set of its
    -- own rather than the one the form collected.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := [0]
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-foreign-selection: the tighter fiat near-miss. It DOES read the form's
# collected selections and writes exactly as many, but writes different
# identities (each shifted). This is the value-level twin of nagini's
# cross-object token transfer: the right amount of work done against the wrong
# targets.
_WEAK_FOREIGN = _HEAD + """\
    -- WRONG: on a committed save it writes as many selections as the form
    -- collected, but not the ones the form collected — each identity is
    -- systematically substituted for another.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m.map (fun i => i + 1)
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-first-selection-only: writes only the FIRST collected selection. No
# nagini counterpart — its carrier had no selection-set content to be partial
# about. Correct for every form carrying at most one selection (which is exactly
# the shape the discriminating regression test uses), wrong from two upward.
_WEAK_TRUNCATE = _HEAD + """\
    -- WRONG (partial domain): on a committed save only the FIRST collected
    -- selection is written; any further ones are dropped.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m.take 1
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-selection-order: writes exactly the collected selections, but in reverse
# order. No nagini counterpart. Correct on every form carrying fewer than two
# selections; wrong from two upward, and wrong in a way that no membership- or
# cardinality-level check would catch. This is what makes C3's equality (rather
# than "the same elements in some order") a measured claim.
_WEAK_REVERSE = _HEAD + """\
    -- WRONG (ordering): on a committed save exactly the collected selections are
    -- written, but in the opposite order to the one the form collected.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m.reverse
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-extra-selection: writes the collected selections AND one extra of its
# own. No nagini counterpart. Every other content rival writes too few or the
# wrong ones; this one writes a superset, so it is the case that pins C3's upper
# bound. Notably it is wrong even for a form that collected NOTHING, a point at
# which the selection-dropping rivals are all correct.
_WEAK_EXTRA = _HEAD + """\
    -- WRONG: on a committed save it writes the collected selections plus one
    -- further selection that the form never collected.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m ++ [0]
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-row-only-if-selections: writes the instance row only when the form
# actually collected some selection, so a committed save of a form that
# collected none writes nothing. No nagini counterpart. It attacks C2 on the
# EMPTY-selection boundary, and it is the only C2 rival that is correct whenever
# any selection is present — so it is refuted at a point no other rival reaches.
_WEAK_ROW_IF_SEL = _HEAD + """\
    -- WRONG (partial domain): the instance row is written only when the form
    -- collected at least one selection, so a committed save of a form that
    -- collected none writes no row.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      if f.m2m ≠ [] then
        instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""


# --- AUDIT ADDITIONS. Three rivals added by the audit lane, each aimed at a
# point no ported rival reaches. All three were built and refuted by hand before
# being added (rival build exit 0 with its witness, frozen solution exit 1 on the
# same witness, by `decide` proving the negation false — a semantic refutation,
# not a missing identifier or a stuck reduction).

# weak-password-on-commit-only: derives the stored password ONLY on a committed
# save. Strictly tighter than weak-password-undone, which never derives it at
# all: this rival AGREES with the frozen impl on the entire committed arm and is
# wrong only on the deferred one. It is the near-miss for the documented fact
# that the returned instance carries its derived password "regardless of whether
# the save was committed" — a reading of C1 as "…on a committed save" would admit
# it, and no other rival distinguishes those two readings.
_WEAK_PW_COMMIT_ONLY = _HEAD + """\
    -- WRONG: the derived password is applied only inside the committed branch, so
    -- a deferred save hands back an instance that does not carry it.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      user := { user with passwordSet := true }
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-selections-deduped: writes the collected selections with duplicates
# removed. Refutable ONLY at a form that collected the same selection twice —
# a multiplicity point every ported content rival misses, since take 1 / reverse
# / map(+1) / ++[0] are each already wrong on a duplicate-free list and so never
# force the question of whether C3 pins the collected sequence or merely its set.
_WEAK_DEDUP = _HEAD + """\
    -- WRONG (multiplicity): on a committed save the collected selections are
    -- written with duplicates collapsed, so a form that collected the same
    -- selection twice has it written once.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m.eraseDups
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""

# weak-row-needs-password: conditions the instance-row write on the raw password
# being non-empty. This is the only rival in the battery that makes `f.password`
# OBSERVABLE: every other case is correct for every value of it, so before this
# case the manifest's claim that `f.password` is an input binder was carried
# entirely by the signature and by no measured point.
_WEAK_ROW_NEEDS_PW = _HEAD + """\
    -- WRONG (partial domain): the instance row is written only when the supplied
    -- raw password is non-empty, so a committed save of a form whose raw password
    -- is empty writes no row.
    let mut user := buildInstance f
    let hasRelatedWriter := true
    user := { user with passwordSet := true }
    let mut instanceSaved := false
    let mut relatedSaved : List Int := []
    if commit then
      if f.password ≠ "" then
        instanceSaved := true
      if hasRelatedWriter then
        relatedSaved := f.m2m
    return { user := user, instanceSaved := instanceSaved, relatedSaved := relatedSaved }"""


# --- Witness helper. Each reject case states the frozen spec predicate directly
# at a concrete, `decide`-able input; the negation elaborates iff the rival's
# output contradicts the spec there. The carrier is fully transparent (a record
# of a Bool, a Bool and a List Int, with no opaque callee), so no conditioning
# on hypotheses is needed and every witness is a closed, literal-input claim —
# there are no binders that could be jointly unsatisfiable.
def _witness(form, commit):
    args = f"{form} {commit}"
    return (f"example : ¬ problem_spec_persistForm {args}\n"
            f"    (implementation_persistForm {args}) := by\n"
            f"  unfold problem_spec_persistForm implementation_persistForm\n"
            f"  decide")


SPEC_TESTS = [
    # ---------------- soundness / admissibility positives ----------------
    {
        "id": "pos-guard-dropped",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_GUARD, _PROOF_OLD),
        "rationale": (
            "Direct port of the nagini positive control. The inner "
            "writer-present guard is provably true on this path (the build step "
            "installs the writer unconditionally), so dropping it is a faithful, "
            "structurally-different correct impl. Must satisfy all three "
            "conjuncts — C1 (derived password applied), C2 (row written exactly "
            "on commit), C3 (the collected selections written exactly on "
            "commit). The frozen tactic script still closes because each branch "
            "reduces definitionally. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE, _POS_PURE_PROOF),
        "rationale": (
            "The same outcome as one record literal — no Id.run, no let mut, no "
            "branch: the commit choice is threaded straight into the two "
            "components that depend on it. Confirms none of C1/C2/C3 secretly "
            "depends on the imperative encoding or on the branch structure. The "
            "result is definitionally the spec's RHS, so the obligation closes "
            "with `exact ⟨rfl, rfl, rfl⟩` and no casing at all. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-step-order-swapped",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ORDER, _PROOF_OLD),
        "rationale": (
            "Within the committed branch the two writes happen in the opposite "
            "order. This is the shape whose nagini counterpart is a REJECT: "
            "there the deferred-relations sub-operation carried a precondition "
            "demanding the row already written, so the reordering was refuted by "
            "that precondition. On this carrier the two writes are independent "
            "components of the returned record with no ordering relation between "
            "them, so the reordering is behaviourally identical and must verify. "
            "Shipped as a positive precisely so the carrier difference is "
            "measured rather than assumed. If it fails => SPEC-TOO-STRONG (the "
            "spec would be pinning an unobservable step order)."
        ),
    },
    {
        "id": "pos-branch-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MATCH, _PROOF_OLD),
        "rationale": (
            "A third distinct shape: an explicit match on the commit choice with "
            "each arm building its whole record literally — the two observable "
            "behaviours spelled out side by side instead of accumulated into "
            "mutable locals. Neither the frozen accumulator nor the branch-free "
            "literal. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-accumulated-selection",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ACCUM, _POS_ACCUM_PROOF),
        "rationale": (
            "The EXTENSIONAL positive, added by the audit lane to close a real "
            "gap in the soundness lane: the other four positives all agree with "
            "the frozen impl DEFINITIONALLY (each closes by `rfl` / "
            "`exact ⟨rfl, rfl, rfl⟩` after casing on the commit choice), so on "
            "their evidence alone the lane could be passing merely because every "
            "shape it tries reduces to the frozen one by computation. Here the "
            "selections to write are ACCUMULATED one at a time (`acc := acc ++ "
            "[i]` over the form's collected selections) — the shape a real "
            "relation writer has. The accumulated list is provably but not "
            "definitionally `f.m2m`, so the obligation needs a genuine induction "
            "(an in-proof `have`, no new top-level declaration) plus the "
            "Id.run/forIn unfolding; no `rfl` closes C3. Verifying therefore "
            "shows C3's list equality is an extensional constraint and not a "
            "demand for the frozen syntactic form. If it fails => "
            "SPEC-TOO-STRONG: the spec would admit only impls that reduce to the "
            "frozen one."
        ),
    },
    {
        "id": "admiss-both-commit-choices",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS, _PROOF_OLD),
        "rationale": (
            "Ports the nagini admissibility control (in-body `Assert(...)` at the "
            "exercised input -> in-body `have ... := by decide`). The obligation "
            "here is a bare ∀ over both binders with NO precondition hypothesis, "
            "so there is no precondition-satisfiability claim to make; "
            "admissibility on this carrier is instead that the spec ADMITS the "
            "intended outcome at each exercised input (satisfiable, not "
            "over-constrained) and is NOT VACUOUS at the committed one (it "
            "rejects the outcome that writes the row but drops the collected "
            "selections). All three `have`s name `problem_spec_persistForm` at a "
            "concrete input, so — unlike the ported form they replace, which were "
            "`ite` tautologies provable with nothing from the bundle in scope — "
            "this case cannot verify while the spec is weakened: with C3 deleted "
            "from the spec view `_hCommittedNotVacuous` fails. Impl body and "
            "frozen tactic script are otherwise verbatim."
        ),
    },

    # ---------------- uniqueness rivals ----------------
    {
        "id": "weak-selections-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROPPED),
        "witness": _witness('{ password := "s3cr3t", m2m := [7] }', "true"),
        "refinement": (
            "This IS the pre-change behaviour: a committed save writes the "
            "instance row and silently discards the form's collected "
            "multi-valued selections. Its faithful real patch is the unpatched "
            "routine, under which the F2P test — which submits a form carrying "
            "one related selection, commits the save, and then asserts the "
            "persisted instance's related set equals that selection — reads back "
            "an EMPTY related set and fails. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [7] but the rival returns []. Witness at "
            "(m2m := [7], commit := true). If it verifies => SPEC-TOO-WEAK on "
            "the discriminating clause."
        ),
    },
    {
        "id": "weak-dead-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DEAD_GUARD),
        "witness": _witness('{ password := "pw", m2m := [3, 4] }', "true"),
        "refinement": (
            "Behaviourally identical to the pre-change routine while keeping the "
            "selection-write call shape: the guard it is placed under cannot hold "
            "where it is evaluated. A faithful patch that adds the write under a "
            "condition that never fires persists no related rows, so the F2P "
            "test's read-back of the persisted related set is still empty and it "
            "fails. Does NOT resolve. This is the case that distinguishes 'the "
            "write appears in the source' from 'the write happens'."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [3, 4] but the dead guard leaves it []. Witness at "
            "(m2m := [3, 4], commit := true) — a two-element selection set, so "
            "it is refuted at a point distinct from weak-selections-dropped's "
            "single-element one even though the two agree in effect. If it "
            "verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-selections-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_REL),
        "witness": _witness('{ password := "s3cr3t", m2m := [7] }', "false"),
        "refinement": (
            "Writing the collected selections whatever the commit choice breaks "
            "the documented deferred-save contract, under which a deferred save "
            "persists NOTHING now and hands back an unsaved instance for the "
            "caller to save later. A faithful patch that always writes them "
            "would, for every existing caller that defers the commit, persist "
            "related rows that must not exist yet — and would attempt them "
            "against an instance whose row has not been written. The P2P suite "
            "covering the deferred-save path does not survive it. Does NOT "
            "preserve behaviour."
        ),
        "rationale": (
            "Rejected by C3's deferred arm: with commit = false relatedSaved "
            "must be [] but the rival returns f.m2m = [7]. Witness at "
            "(m2m := [7], commit := false) — the only reject case aimed at that "
            "arm of C3 with a non-empty selection set. If it verifies => "
            "SPEC-TOO-WEAK on the deferred arm."
        ),
    },
    {
        "id": "weak-row-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_UNCOND_ROW),
        "witness": _witness('{ password := "hunter2", m2m := ([] : List Int) }',
                            "false"),
        "refinement": (
            "Ports the instance-row half of nagini's unconditional-persist "
            "attack. A faithful patch that writes the instance row regardless of "
            "the commit choice contradicts the deferred-save contract — the "
            "P2P-covered deferred path asserts that deferring does not write, "
            "and callers that deferred in order to adjust the instance first "
            "would find it already persisted. Does NOT preserve behaviour."
        ),
        "rationale": (
            "Rejected by C2: instanceSaved must equal commit, so with "
            "commit = false it must be false, but the rival returns true. "
            "Witness at (m2m := [], commit := false) — an EMPTY selection set, a "
            "point at which every C3 rival is correct, so this witness isolates "
            "C2. If it verifies => SPEC-TOO-WEAK on the row-write clause."
        ),
    },
    {
        "id": "weak-password-undone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_PASSWORD),
        "witness": _witness('{ password := "pw", m2m := [2] }', "false"),
        "refinement": (
            "Never applying the derived password to the built instance. A "
            "faithful patch that dropped that step would hand back — and, on a "
            "committed save, persist — an instance whose stored password was "
            "never derived from the supplied one, so the account could not be "
            "authenticated with the password just submitted. The P2P tests that "
            "assert the derivation happens exactly once per save (and not on a "
            "deferred save) fail. Does NOT preserve behaviour. This clause is "
            "untouched by the change, which is exactly why a rival is needed: "
            "the spec must pin it or a 'fix' free to break it would verify."
        ),
        "rationale": (
            "Rejected by C1: result.user.passwordSet must be true and the rival "
            "leaves it false. Witness at (m2m := [2], commit := false) — the "
            "deferred arm, where C1 is nevertheless required, so the witness "
            "attributes the rejection to C1 alone and not to either "
            "commit-dependent clause. C1 is attacked by no other rival. If it "
            "verifies => SPEC-TOO-WEAK on the returned instance."
        ),
    },
    {
        "id": "weak-fiat-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_FIAT),
        "witness": _witness('{ password := "pw", m2m := [7] }', "true"),
        "refinement": (
            "The value-level port of the nagini fiat/fabrication family (fold the "
            "capability by hand; poke the observable fields). Here the analogue is "
            "asserting 'the related selections are written' by writing a fixed set "
            "of the implementation's own choosing, with nothing read from the form. "
            "A faithful patch that persists a hardcoded related row rather than the "
            "submitted one leaves the F2P read-back showing a related object the "
            "form never selected, so the equality against the submitted selection "
            "fails. Does NOT resolve — and it is the case that shows C3 is grounded "
            "in the form's own contents rather than merely demanding non-emptiness."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [7], and the rival returns the fixed [0]. Witness at "
            "(m2m := [7], commit := true). If it verifies => SPEC-TOO-WEAK: C3 "
            "would be satisfiable by writing something rather than by writing "
            "the collected selections (ungrounded-oracle hole)."
        ),
    },
    {
        "id": "weak-foreign-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_FOREIGN),
        "witness": _witness('{ password := "pw", m2m := [5] }', "true"),
        "refinement": (
            "The tighter fiat near-miss, and the closest thing this carrier has "
            "to nagini's cross-object token transfer: the right amount of work "
            "done against the wrong targets. It reads the form's collected "
            "selections and writes exactly as many, but each identity is "
            "systematically substituted for another. A faithful patch that "
            "persisted related rows pointing at neighbouring objects would leave "
            "the F2P read-back non-empty and correctly sized but unequal to the "
            "submitted selection, so the assertion still fails. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [5], and the rival returns [6]. Strictly tighter than "
            "weak-fiat-selection, which ignores the form entirely and so could "
            "be refuted by any cardinality check — this rival matches the "
            "cardinality and misses only the identities, so it demonstrates C3 "
            "pins WHICH selections. Witness at (m2m := [5], commit := true), a "
            "point no other rival probes. If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-first-selection-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRUNCATE),
        "witness": _witness('{ password := "pw", m2m := [8, 9] }', "true"),
        "refinement": (
            "PARTIAL-DOMAIN attack with no nagini counterpart (its carrier had no "
            "selection-set content to be partial about). A faithful patch that "
            "persisted only the first of the submitted selections is correct for "
            "every form carrying at most one — which is exactly the shape the "
            "discriminating regression test submits, so it would pass that test "
            "while silently dropping selections for any form submitting two or "
            "more. That is a fix that resolves the cited F2P and is still wrong, "
            "which is the strongest reason the spec must pin the FULL set rather "
            "than 'at least one selection was written'."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm at a selection set of size two: "
            "relatedSaved must equal f.m2m = [8, 9] but the rival returns [8]. "
            "Witness at (m2m := [8, 9], commit := true). If it verifies => "
            "SPEC-TOO-WEAK: C3 would not require the complete collected set."
        ),
    },
    {
        "id": "weak-selection-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REVERSE),
        "witness": _witness('{ password := "pw", m2m := [1, 2] }', "true"),
        "refinement": (
            "No nagini counterpart. It writes exactly the collected selections, "
            "in the opposite order. A faithful patch that persisted the submitted "
            "selections in reverse would satisfy any membership- or "
            "cardinality-level expectation, but the discriminating regression "
            "test compares the persisted related set as an ORDERED sequence, so "
            "for a form submitting two or more selections the comparison fails. "
            "Does NOT resolve on that sub-domain."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [1, 2] but the rival returns [2, 1]. This is the case that makes "
            "C3's list EQUALITY a measured claim rather than a same-elements "
            "claim — no other rival is refutable only by order. Witness at "
            "(m2m := [1, 2], commit := true), a point no other rival probes. If "
            "it verifies => SPEC-TOO-WEAK on the order of the written set."
        ),
    },
    {
        "id": "weak-extra-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EXTRA),
        "witness": _witness('{ password := "pw", m2m := [6] }', "true"),
        "refinement": (
            "No nagini counterpart. Every other content rival writes too few "
            "selections or the wrong ones; this one writes a SUPERSET — the "
            "collected selections plus one the form never collected. A faithful "
            "patch that persisted an extra related row would associate the new "
            "account with an object nobody selected (a real privacy/authorization "
            "consequence, not just a failed assertion), and the F2P read-back — "
            "an ordered comparison against exactly the submitted selection — "
            "fails on the extra element. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm: relatedSaved must equal f.m2m "
            "= [6] but the rival returns [6, 0]. It pins C3's UPPER bound, which "
            "every dropping/substituting rival leaves open, and it is wrong even "
            "for a form that collected nothing — a point at which all the "
            "dropping rivals are correct. Witness at (m2m := [6], commit := "
            "true), a point no other rival probes. If it verifies => "
            "SPEC-TOO-WEAK: C3 would permit writing selections the form never "
            "collected."
        ),
    },
    {
        "id": "weak-row-only-if-selections",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ROW_IF_SEL),
        "witness": _witness('{ password := "pw", m2m := ([] : List Int) }',
                            "true"),
        "refinement": (
            "PARTIAL-DOMAIN attack on the row write, no nagini counterpart. It "
            "conditions the instance-row write on the form having collected at "
            "least one selection — the mistake of folding the new "
            "related-selection handling into the row write instead of adding it "
            "after. A faithful patch shaped that way passes the discriminating "
            "regression test (whose form DOES carry a selection) while a "
            "committed save of a form that carries none — i.e. every ordinary "
            "account registration, and the P2P-covered committed-save path — "
            "persists no account at all. Resolves the cited F2P and is still "
            "badly wrong."
        ),
        "rationale": (
            "Rejected by C2 on the empty-selection boundary: instanceSaved must "
            "equal commit = true, but with f.m2m = [] the rival returns false. "
            "The only C2 rival that is correct whenever any selection is "
            "present, so it is refuted at a point weak-row-always cannot reach "
            "(that rival is wrong only on the deferred arm). Witness at "
            "(m2m := [], commit := true). If it verifies => SPEC-TOO-WEAK: C2 "
            "would permit the row write to depend on the selection set."
        ),
    },

    # ---------------- uniqueness rivals added by the audit lane ----------------
    {
        "id": "weak-password-on-commit-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PW_COMMIT_ONLY),
        "witness": _witness('{ password := "pw", m2m := [1] }', "false"),
        "refinement": (
            "Applying the derived password only inside the committed branch. A "
            "faithful patch shaped this way is INDISTINGUISHABLE from correct on "
            "every committed save — including the discriminating regression test — "
            "and hands back an instance with no derived password whenever the "
            "caller defers. Callers that defer in order to adjust the instance "
            "before persisting it would then persist an account whose stored "
            "password was never derived from the submitted one, so the account "
            "cannot be authenticated with the password just supplied; the "
            "P2P-covered deferred-save path does not survive it. Does NOT preserve "
            "behaviour."
        ),
        "rationale": (
            "Rejected by C1 on the deferred arm: result.user.passwordSet must be "
            "true for BOTH commit choices, and the rival leaves it false when "
            "commit = false. Strictly tighter than weak-password-undone, which "
            "never derives the password at all and so is refuted on either arm: "
            "this rival agrees with the frozen impl across the whole committed "
            "arm, so it is the case that pins C1's 'regardless of the commit "
            "choice' half rather than merely 'the password is derived'. Witness "
            "at (m2m := [1], commit := false). If it verifies => SPEC-TOO-WEAK: "
            "C1 would be readable as applying only to a committed save."
        ),
    },
    {
        "id": "weak-selections-deduped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DEDUP),
        "witness": _witness('{ password := "pw", m2m := [5, 5] }', "true"),
        "refinement": (
            "MULTIPLICITY attack, no nagini counterpart. It writes the collected "
            "selections with duplicates collapsed, so it is correct for every form "
            "whose collected selections are distinct — which is every form the "
            "regression suite submits. A faithful patch that de-duplicated before "
            "persisting would resolve the cited F2P and still silently alter what "
            "is written for any form that collected a repeated selection. Does NOT "
            "resolve on that sub-domain."
        ),
        "rationale": (
            "Rejected by C3 on the committed arm at a form collecting a repeated "
            "selection: relatedSaved must equal f.m2m = [5, 5] but the rival "
            "returns [5]. Every other content rival is already wrong on a "
            "duplicate-free selection set, so none of them forces the question "
            "this one settles: whether C3 pins the collected SEQUENCE (with "
            "multiplicity) or merely its set of elements. Witness at "
            "(m2m := [5, 5], commit := true), a point no other rival probes. If "
            "it verifies => SPEC-TOO-WEAK on the multiplicity of the written set."
        ),
    },
    {
        "id": "weak-row-needs-password",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ROW_NEEDS_PW),
        "witness": _witness('{ password := "", m2m := [1] }', "true"),
        "refinement": (
            "PARTIAL-DOMAIN attack on the row write via the raw password, no "
            "nagini counterpart. A faithful patch that skipped the row write when "
            "the supplied raw password is empty passes every test whose form "
            "carries a password — i.e. the whole suite — while dropping the "
            "account entirely on the empty-password input. The row write is "
            "unconditional on the raw password in the routine under spec, so this "
            "is a behaviour change the spec must exclude. Does NOT preserve "
            "behaviour."
        ),
        "rationale": (
            "Rejected by C2: instanceSaved must equal commit = true, but with "
            "f.password = \"\" the rival returns false. This is the ONLY rival in "
            "the battery at which `f.password` is observable at all — every other "
            "case's outcome is independent of it, so the manifest's claim that "
            "`f.password` is an input binder was otherwise carried by the "
            "signature and by no measured point. Witness at "
            "(password := \"\", m2m := [1], commit := true). If it verifies => "
            "SPEC-TOO-WEAK: C2 would permit the row write to depend on the raw "
            "password."
        ),
    },
]

# No consumed axiom and no opaque callee on this path (meta.axioms == []); the
# persistence sub-operations are A-reference deep models validated against the
# real persistence layer by G-AX, not axiomatized properties this spec consumes.
# The axiom lane is G-AX's job and this gate ignores it.
AXIOM_TESTS = []
