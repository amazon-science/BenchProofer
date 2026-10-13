# properties.py — G-PBT falsification battery for django__django-13033 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against the
# frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier.
#
# Defended surface (read from Solution.lean):
#   orderingExpandsRelation
#     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
#     (path : String) : Bool
#   ONE obligation, `theorem correct_orderingExpandsRelation`, over a spec that is
#   a single BICONDITIONAL pinning the result exactly:
#     result = true ↔ (fieldIsRelation = true ∧ relatedHasOrdering = true ∧
#                      fieldAttr ≠ some (lastSegment path) ∧ path ≠ "pk")
#   Four independent conjuncts on the RHS, each attackable on its own sub-domain,
#   over four input binders. `lastSegment` is a `pure`-region `def` (split the path
#   on the lookup separator, take the last piece), so the third conjunct is
#   GROUNDED in the inputs — it is not an opaque oracle and there is no "wrong
#   echo" of an answer key to construct. Consequently the positive controls are
#   honest structurally-different correct impls, exactly as in the nagini sibling.
#
# Carrier notes vs the nagini sibling (what the port had to re-express):
#   * Nagini modeled `ordering_mode(...) -> int` returning 0/1 with a `PSeq[int]`
#     path already SPLIT into segments by the caller, plus a precondition tying the
#     whole name to its terminal segment. This bundle's carrier is narrower and
#     more faithful: the path is a `String` and the split is performed INSIDE the
#     modeled surface by `lastSegment`, and the result is a `Bool` rather than a
#     0/1 code. So:
#       - nagini's two-part `Ensures` (a range clause `Result() == 0 or 1` plus the
#         biconditional) collapses to the biconditional alone: the `Bool` return
#         type discharges the range clause by construction. Nothing to attack
#         there, and no rival is shipped for it.
#       - nagini's `Requires` (non-empty segment list; whole-name ≠ terminal for
#         multi-segment paths) has NO counterpart: the obligation here has no
#         precondition hypothesis, because `String.splitOn` on a non-empty
#         separator always yields at least one piece, so the final segment is total
#         for every `path`. There is therefore no PRECOND-TOO-STRONG risk to probe
#         by establishing a precondition at a call site. Nagini's
#         `admiss-reproducer-caller` is ported in the only form the carrier admits:
#         an in-body assertion that the spec HOLDS at the reproducer-shaped points
#         (admiss-spec-shape below).
#       - because the split is inside the surface, this carrier exposes attack
#         surface nagini's did not: rivals may split on the WRONG separator, take
#         the WRONG piece of the split, or apply the final-segment reading to the
#         wrong conjunct. Three such rivals are added (weak-single-underscore-sep,
#         weak-first-segment, weak-pk-on-final-segment); they have no nagini
#         counterpart and exist so the `path` binder is abused structurally and not
#         only as an opaque atom.
#   * `fieldAttr : Option String` replaces nagini's `relation_own_column : PSeq`.
#     The `none` case (a resolved field with no stored attribute) is new carrier
#     structure with no nagini analogue, and is attacked by weak-absent-attr.
#
# Witness mechanics on this carrier (the part with no nagini counterpart). The
# spec's third conjunct goes through `lastSegment`, and `String.splitOn` does NOT
# reduce in the kernel: measured here, `decide`, `rfl`, `simp` and
# `simp [String.splitOn, String.splitOnAux]` all fail on
# `lastSegment "record__root_id" = "root_id"` — `decide` gets stuck at
# `("record__root_id".splitOn "__" ...).data.hasDecEq`, and the simp route loops
# (`Possibly looping simp theorem: String.splitOn.eq_1`, then a whnf heartbeat
# timeout even at 2,000,000 heartbeats). So the witnesses come in two shapes:
#   * fully CONCRETE (`decide`) where the refutation needs no split value at all —
#     the sub-domain where a boolean conjunct or the literal pk exclusion decides
#     the disagreement, and `none ≠ some _` / literal String comparison reduce;
#   * CONDITIONED on the carrier where the refutation genuinely needs the split —
#     one hypothesis naming the split of one concrete literal path, e.g.
#     `(hs : "record__root_id".splitOn "__" = ["record", "root_id"])`. That is the
#     weakest assumption the refutation needs (a single true fact about a single
#     literal), it is jointly satisfiable by construction, and it is not two
#     hypotheses about the same term — checked: the gate's consistency probe
#     (`first | omega | simp_all | decide | (simp_all; omega)`) cannot derive
#     `False` from any of these binder sets (`simp_all made no progress`).
#     weak-single-underscore-sep carries two hypotheses because it needs the split
#     on BOTH separators; they are about DIFFERENT terms
#     (`"root_id".splitOn "__"` and `"root_id".splitOn "_"`) and are both true.
#
# Vacuous / dropped classes (stated per directive, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini sibling
#     already records this class as inapplicable (all inputs immutable value
#     types, no fractional-permission heap input). Lean is referentially
#     transparent: there is no aliasable read-only input to overwrite. Nothing to
#     port, and no substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION lane — a KNOWN GAP for a TOOLING reason, not a
#     vacuous class. The audit corrected this entry: the port claimed "a diverging
#     implementation cannot be written at all", and that is measurably FALSE. This
#     bundle sets no `loom.semantics.termination` at all (plain Lean, where every
#     `def` must terminate), but `partial def` is an admissible escape hatch and
#     variant_scope does not ban it — a rival whose impl calls a `partial`
#     self-recursive spinner builds as an in-scope variant and IS rejected by the
#     verifier (measured: variant_problems == [], build exit 1). So the class
#     exists. What blocks SHIPPING it is the witness, and precisely: `partial`
#     makes the spinner opaque to the kernel, so `decide` on the witness is stuck
#     against the RIVAL (measured: "Tactic `decide` failed ... if spinForever 0 =
#     true", exit 1) — i.e. witness-unproven, the half that must succeed. The
#     conditioned form cannot rescue it either, because conditioning requires
#     naming the spinner, and witness_scope_problems correctly refuses a witness
#     referencing a name only the variant declares (measured: it reports exactly
#     that). Recorded as a hole in the battery's coverage, therefore, rather than
#     as a property of the carrier. The nagini sibling ships no such case either,
#     so nothing is dropped in the port; this is an independent gap in both.
#   * AXIOM lane — DROPPED. `meta.axioms == []` and `deep_model_references == []`:
#     no opaque callee is consumed, the split and the comparisons are modeled
#     directly. The axiom lane is G-AX's job and this gate ignores it.
#     AXIOM_TESTS = [], matching the nagini sibling.
#
# Independent audit (post-port), machine-checked. Recorded here because the gate
# re-derives outcomes but not the reasons:
#   * All 16 `theorem correct_*` statements are BYTE-identical to the frozen file,
#     and every case's text outside the impl region and the proof tactic body is
#     byte-identical too — no reformatted statement, no weakened hypothesis.
#   * All 11 reject witnesses were rebuilt both ways: each holds of its rival
#     (exit 0) and FAILS on the frozen solution (exit 1), and every gold-side
#     failure is SEMANTIC — either `decide` proving the negation false, or a goal
#     reduced to a bare `⊢ False` under the split hypothesis. No unknown
#     identifier, no type error, no stuck reduction, no timeout. The 7 witnesses
#     that bind hypotheses also had their consistency probes rebuilt (all exit 1,
#     `simp_all made no progress`), and each assumed split fact was independently
#     confirmed TRUE by `#eval`.
#   * SECOND, INDEPENDENT AUDIT (the forgery test, attack B′) — this found a real
#     defect the first audit's "the error looks semantic" reading missed, and the
#     fix is the `pure` hint now in `_w_split`. The test: build a file differing
#     from the witness ONLY in dropping the `¬`, i.e. claiming the frozen impl is
#     CORRECT at that input, and see whether gold's exit code CHANGES.
#     - the 4 concrete `_w_decide` witnesses: flipped claim exit 0 on gold. Gold's
#       code tracks the claim perfectly; `decide` decides both directions.
#     - 4 of the 7 `_w_split` witnesses (whole-path-operand, pk-operand-confusion,
#       relation-only, single-underscore-sep): flipped claim exit 0 on gold.
#     - the OTHER 3 (first-segment, pk-on-final-segment, absent-attr): flipped
#       claim ALSO failed on gold, exit 1. Not hollow — the two errors differed
#       (`⊢ False` for the witness vs `⊢ pure true = true` for the flip), so gold's
#       failure did carry information — but the flip's failure was a TACTIC gap,
#       not a refutation: `simp` had reduced the goal to the imperative body's
#       residual `pure true = true` and stopped. Adding `pure` to the simp set (the
#       frozen proof script's own hint, which `_w_split` had omitted) closes that
#       residue. Re-measured for all 7 split witnesses after the fix: witness holds
#       of the rival (exit 0), fails on gold with a bare `⊢ False` (exit 1), and the
#       FLIPPED claim now VERIFIES on gold (exit 0) for every one of them. That is
#       the strongest gold-side evidence obtainable: one tactic script proves the
#       claim true of the frozen impl and proves its negation of the rival, so the
#       exit codes cannot be explained by anything but the claim's truth value.
#       Consistency probes re-run after the fix: all 7 still exit 1.
#   * All 11 rivals are OBSERVABLY different from the frozen impl (exhaustive
#     search over the four binders: 17 paths x 14 attrs x 2 x 2); none is a mere
#     reshape. All 5 positives are behaviourally EQUAL to it. The 11 witness
#     points are pairwise distinct.
#   * SPEC-TOO-WEAK probe: 6 NEW wrong impls not in this battery (collapse `none`
#     to "" via `Option.getD`; special-case the empty path; suffix test instead of
#     final-segment equality; polarity flip on the third conjunct; `||` for `&&`
#     on the two booleans; pk exclusion widened to a prefix test) were all
#     REJECTED. No spec hole found.
#   * SPEC-TOO-STRONG probe: 5 NEW correct reshapes (pure `ite` with conjuncts
#     reversed; dispatch on the Option rather than the Bools; `decide` over the
#     spec's own RHS; De Morgan negation-normal form; `Option.all`) were all
#     PROVEN. The two that dispatch on `fieldAttr` need `cases fieldAttr` added to
#     the case ladder — a proof-script matter, not a spec rejection. No soundness
#     hole found.
#   * Second audit, SPEC-TOO-WEAK, 7 further NEW wrong impls aimed at what the
#     shipped rivals leave alone: the stored-attribute comparison applied only to
#     multi-segment paths; the shortcut exclusion given a second spelling; a suffix
#     test with the attribute as the suffix; the PENULTIMATE segment instead of the
#     last; an empty stored attribute treated as absent; the empty path suppressed;
#     `||` on the two booleans only in the absent-attribute arm. Six differ from
#     the frozen decision on the exhaustive grid (9, 40, 4, 15, 46 and 9 inputs
#     respectively) and all six were REJECTED; the seventh (second spelling of the
#     shortcut) has ndiff=0 on the grid, i.e. it is a CORRECT reshape rather than a
#     rival — it was rejected too, but as a tactic mismatch, so it is reported as a
#     reshape and not counted as a uniqueness result. No spec hole found.
#   * Second audit, SPEC-TOO-STRONG, 5 further NEW correct reshapes, each first
#     confirmed ndiff=0 against the frozen impl over the exhaustive grid so that
#     "correct" is measured and not assumed. Three PROVEN: De Morgan NNF (closes
#     under the frozen script unchanged); a cascade testing the shortcut FIRST
#     (needs the case ladder reordered and `beq_iff_eq`); the two now shipped as
#     pos-other-split-default and pos-option-dispatch (need the splitOn-nonempty
#     `have`). One NOT closed and reported UNCERTAIN rather than as a hole:
#     `(path.splitOn "__") != ["pk"]` in place of `path != "pk"` — behaviourally
#     identical on the grid, but bridging it needs splitOn's INJECTIVITY on that
#     literal, which `@[irreducible] splitOnAux` blocks; a carrier limit on the
#     proof, with no evidence the spec rejects the function. No soundness hole
#     found.
#   * Three FALSE prose claims were found and corrected: weak-relation-only's
#     witness point failed one conjunct while its rationale claimed two (the
#     witness was moved to a point where two genuinely fail, and rebuilt both
#     ways); weak-never-expands claimed to be the only rival refuted in the ⇐
#     direction (three others are); weak-absent-attr claimed to be wrong on the
#     ENTIRE `none` half (it is wrong on the part of it where the frozen decision
#     is true). No rival was dropped and no case was vacuous.
#   * The two nagini cases with no counterpart here were re-derived independently
#     and are genuinely inexpressible: the range clause is a Bool tautology
#     (`cases result <;> simp` closes it, so no impl can violate it) and the
#     Requires has nothing to constrain (`lastSegment` is total — verified at
#     "", "__" and "a__").
#   * The header's carrier claim was re-measured: `decide` on
#     `lastSegment "record__root_id" = "root_id"` fails with reduction stuck at
#     `(match "record__root_id".splitOn "__", "" with ...)`, confirming the
#     conditioned-witness shape is necessary and not an evasion.

from pathlib import Path

INSTANCE = "django__django-13033"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region (the whole `def implementation_*`, which is the entire region
# strictly between the impl markers) and the proof TACTIC BODY (everything after
# the `theorem correct_*` statement's `:= by`) are the ONLY regions a variant may
# edit. The spec view and the byte-identical theorem statement are never touched,
# so same_spec holds by construction.

_IMPL_OLD = """\
def implementation_orderingExpandsRelation
    (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
    (path : String) : Bool := Id.run do
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (path != "pk") then
    return true
  return false"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro fieldIsRelation relatedHasOrdering fieldAttr path
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some (lastSegment path) <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure]"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl region, and (for a
    reshaped soundness positive whose proof needs adjusting) the proof tactic
    body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


def _def(body, pure_fn=False):
    """A full `implementation_*` definition with the given body."""
    head = (":=" if pure_fn else ":= Id.run do")
    return (
        "def implementation_orderingExpandsRelation\n"
        "    (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)\n"
        f"    (path : String) : Bool {head}\n" + body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Structurally different but
# behaviourally identical correct impls, each shipped with a proof that actually
# closes for the new shape. The `theorem correct_orderingExpandsRelation`
# statement is byte-identical in every one; no new lemma, axiom, sorry, admit or
# native_decide. Ports the nagini pos-control-* pair, plus one extra control the
# nagini carrier could not express (pos-inline-split).
# ---------------------------------------------------------------------------

# pos-guard-ladder — ports nagini pos-control-nested-branches: the same boolean
# function as a short-circuit guard ladder with the conjuncts reordered and the
# early-return polarity inverted. The frozen `by_cases … simp_all [pure]` script
# needs one extra unfolding hint (`bind`/`Id.run`) because the ladder leaves a
# chain of `pure PUnit.unit` binds where the frozen shape had none; the theorem
# statement and the case split are unchanged.
_POS_LADDER = _def("""\
  if !fieldIsRelation then
    return false
  if !relatedHasOrdering then
    return false
  if fieldAttr == some (lastSegment path) then
    return false
  if path == "pk" then
    return false
  return true""")

_POS_LADDER_PROOF = """\
  intro fieldIsRelation relatedHasOrdering fieldAttr path
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some (lastSegment path) <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure, bind, Id.run]"""

# pos-pure-match — ports nagini pos-control-local-bool onto this carrier: drop the
# imperative `Id.run do` wrapper entirely and dispatch the two boolean
# observations by pattern match, returning the remaining two conjuncts as a plain
# `Bool` expression. Confirms the obligation does not secretly depend on the
# imperative encoding. The frozen proof script closes unchanged.
_POS_PURE_MATCH = _def("""\
  match fieldIsRelation, relatedHasOrdering with
  | true, true => (fieldAttr != some (lastSegment path)) && (path != "pk")
  | _, _ => false""", pure_fn=True)

# pos-let-binding — the other half of nagini pos-control-local-bool: name the
# final segment and the two-boolean part in `let`s and branch on the conjunction
# once. `let`-inlining is definitional, so the frozen proof script closes
# unchanged.
_POS_LET = _def("""\
  let seg := lastSegment path
  let relational := fieldIsRelation && relatedHasOrdering
  if relational && (fieldAttr != some seg) && (path != "pk") then
    return true
  return false""")

# pos-inline-split — NO nagini counterpart (nagini's caller pre-split the path, so
# the split was outside the modeled surface). This impl never mentions the
# `pure`-region helper the spec's third conjunct names; it inlines the same split
# expression instead. If the third conjunct were satisfiable only by a syntactic
# echo of the spec's own helper symbol rather than by its VALUE, this would fail —
# so this is what makes "the third conjunct is grounded, not an oracle echo" a
# measured claim rather than an assertion. The proof needs the helper unfolded and
# the case-split restated over the inlined form; statement unchanged.
_POS_INLINE_SPLIT = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some ((path.splitOn "__").getLastD "")) && (path != "pk") then
    return true
  return false""")

_POS_INLINE_SPLIT_PROOF = """\
  intro fieldIsRelation relatedHasOrdering fieldAttr path
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
    lastSegment
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some ((path.splitOn "__").getLastD "") <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure]"""

# --- The `String.splitOn` nonemptiness fact, proven inline. Two of the positives
# below need it, and it is the ONE non-obvious step on this carrier: `splitOnAux`
# is `@[irreducible]`, so `simp`/`decide`/`omega` cannot see through it and
# `exact?` finds nothing. `fun_induction` on its equation lemma closes it. Stated
# as a `have` inside the proof tactic body (NOT a new top-level lemma, which
# variant_scope bans) so the variant stays in scope.
_SPLIT_NONEMPTY = """\
  have hne : (path.splitOn "__") ≠ [] := by
    have key : ∀ (s sep : String) (b i j : String.Pos) (r : List String),
        s.splitOnAux sep b i j r ≠ [] := by
      intro s sep b i j r
      fun_induction String.splitOnAux s sep b i j r <;> simp_all
    unfold String.splitOn
    exact key _ _ _ _ _ _"""

# pos-other-split-default — NO nagini counterpart, and added by the independent
# audit as a soundness probe the original battery did not carry. The spec's helper
# reads the split's last piece with a DEFAULT for the empty-list case
# (`getLastD ""`); this impl supplies a different, deliberately absurd default.
# The two agree at every input because the split is never empty, but that is a
# THEOREM about the carrier and not a definitional identity, so the frozen proof
# script alone cannot close it. Verifying establishes that the third conjunct is
# pinned to the observable final segment and not to the particular unreachable
# default the frozen helper happens to name — a distinction the original battery's
# pos-inline-split (which copies the default verbatim) could not make.
_POS_OTHER_DEFAULT = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some ((path.splitOn "__").getLastD "IMPOSSIBLE")) &&
      (path != "pk") then
    return true
  return false""")

_POS_OTHER_DEFAULT_PROOF = f"""\
  intro fieldIsRelation relatedHasOrdering fieldAttr path
{_SPLIT_NONEMPTY}
  have hd : (path.splitOn "__").getLastD "IMPOSSIBLE" = lastSegment path := by
    unfold lastSegment
    cases h : (path.splitOn "__") with
    | nil => exact absurd h hne
    | cons a l => induction l generalizing a <;> simp_all [List.getLastD]
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  rw [hd]
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some (lastSegment path) <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure]"""

# pos-option-dispatch — NO nagini counterpart; also added by the audit. Reads the
# split's last piece as an `Option` (`getLast?`) and dispatches on it, so the
# empty-split branch is a REAL branch in the impl rather than an unreachable
# default, and the two-boolean conjunction lives inside the `some` arm. This is
# the shape the original battery's rationale claimed to have probed ("dispatch on
# the Option") but shipped no case for. Needs the same nonemptiness fact.
_POS_OPTION_DISPATCH = _def("""\
  match (path.splitOn "__").getLast? with
  | none => false
  | some seg =>
    fieldIsRelation && relatedHasOrdering && (fieldAttr != some seg) &&
      (path != "pk")""", pure_fn=True)

_POS_OPTION_DISPATCH_PROOF = f"""\
  intro fieldIsRelation relatedHasOrdering fieldAttr path
{_SPLIT_NONEMPTY}
  have hg : (path.splitOn "__").getLast? = some (lastSegment path) := by
    unfold lastSegment
    cases h : (path.splitOn "__") with
    | nil => exact absurd h hne
    | cons a l =>
      induction l generalizing a <;> simp_all [List.getLastD, List.getLast?]
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  rw [hg]
  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
  by_cases hr : fieldIsRelation = true <;>
  by_cases ho : relatedHasOrdering = true <;>
  by_cases ha : fieldAttr = some (lastSegment path) <;>
  by_cases hp : path = "pk" <;>
  simp_all [pure]"""

# admiss-spec-shape — the only form nagini's admiss-reproducer-caller can take on
# this carrier. The obligation has no precondition hypothesis (see the header
# note), so there is no Requires to establish at a call site; what remains of the
# nagini control's content is the claim that the spec is SATISFIABLE at the
# legitimate, issue-shaped points, which nagini made with in-body `Assert(...)` and
# which becomes an in-body `have … := by decide` here. Three points are asserted:
# the primary-key shortcut resolving to no expansion, an ordinary single-segment
# lookup on a relation with a declared default ordering resolving to expansion,
# and a relation WITHOUT a declared default ordering resolving to no expansion —
# plus the separation fact that a multi-segment path differs from its own final
# segment (the distinction the whole biconditional's third conjunct turns on).
# The impl body is otherwise the frozen one and the frozen proof is kept verbatim,
# so the only thing this can fail on is a spec-shape regression at those points.
_ADMISS_SHAPE = _def("""\
  have _hPkShortcut : problem_spec_orderingExpandsRelation true true none "pk"
      false := by
    unfold problem_spec_orderingExpandsRelation
    decide
  have _hExpands : problem_spec_orderingExpandsRelation true true none "author"
      true := by
    unfold problem_spec_orderingExpandsRelation
    decide
  have _hNoOrdering : problem_spec_orderingExpandsRelation true false none
      "author" false := by
    unfold problem_spec_orderingExpandsRelation
    decide
  have _hSeparation : (("record__root_id" : String) ≠ "root_id") := by decide
  have _hMultiSegNoExpand : "record__root_id".splitOn "__" = ["record", "root_id"] →
      problem_spec_orderingExpandsRelation true true (some "root_id")
        "record__root_id" false := by
    intro hs
    unfold problem_spec_orderingExpandsRelation lastSegment
    simp [hs]
  have _hMultiSegExpands : "record__root".splitOn "__" = ["record", "root"] →
      problem_spec_orderingExpandsRelation true true (some "root_id")
        "record__root" true := by
    intro hs
    unfold problem_spec_orderingExpandsRelation lastSegment
    simp [hs]
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (path != "pk") then
    return true
  return false""")


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region and keeps the frozen proof script, and each ships a `witness` that
# was BUILT BOTH WAYS before shipping: it elaborates against the rival and fails
# against the frozen solution. Nothing here relies on the frozen tactic script
# merely failing to match a reshaped impl.
# ---------------------------------------------------------------------------

# weak-whole-path-operand — ports nagini rival-prepatch-operand-name, the central
# rival: compare the field's stored attribute against the WHOLE lookup path
# instead of the path's final segment.
_WEAK_WHOLE_PATH = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some path) && (path != "pk") then
    return true
  return false""")

# weak-drop-pk — ports nagini rival-drop-pk-conjunct: drop the primary-key
# shortcut exclusion.
_WEAK_DROP_PK = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) then
    return true
  return false""")

# weak-drop-ordering — ports nagini rival-drop-default-ordering-conjunct: drop the
# requirement that the related model actually declares a default ordering.
_WEAK_DROP_ORDERING = _def("""\
  if fieldIsRelation &&
      (fieldAttr != some (lastSegment path)) && (path != "pk") then
    return true
  return false""")

# weak-drop-relation — ports nagini rival-drop-relation-conjunct: drop the
# requirement that the resolved field is a relation at all.
_WEAK_DROP_RELATION = _def("""\
  if relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (path != "pk") then
    return true
  return false""")

# weak-pk-operand-confusion — ports nagini rival-pk-operand-confusion: test the
# field's stored attribute against the primary-key shortcut name instead of
# testing the lookup path against it.
_WEAK_PK_OPERAND = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (fieldAttr != some "pk") then
    return true
  return false""")

# weak-relation-only — ports nagini rival-relation-only: collapse the whole
# four-way conjunction to the relation observation alone.
_WEAK_RELATION_ONLY = _def("""\
  if fieldIsRelation then
    return true
  return false""")

# weak-never-expands — ports nagini rival-always-zero: never expand.
_WEAK_NEVER = _def("""\
  return false""")

# weak-single-underscore-sep — NO nagini counterpart (nagini's caller performed
# the split, so the separator was not part of the modeled surface). Splits the
# path on a SINGLE underscore rather than on the two-character lookup separator.
# Agrees with the frozen decision on every path containing no single underscore
# outside the separator — a large majority of realistic lookups — and diverges
# exactly where a segment itself contains an underscore.
_WEAK_SINGLE_SEP = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some ((path.splitOn "_").getLastD "")) && (path != "pk") then
    return true
  return false""")

# weak-first-segment — NO nagini counterpart. Takes the FIRST piece of the split
# instead of the last: the right separator, the right comparison, the wrong end of
# the path. Agrees with the frozen decision on every single-segment path (where
# first and last coincide) and diverges only on multi-segment ones.
_WEAK_FIRST_SEGMENT = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != (path.splitOn "__").head?) && (path != "pk") then
    return true
  return false""")

# weak-pk-on-final-segment — NO nagini counterpart, and the tightest near-miss in
# the battery. It gets the third conjunct exactly right and applies the SAME
# final-segment reading to the primary-key exclusion as well, testing the final
# segment against the shortcut name rather than the whole path. Agrees with the
# frozen decision everywhere except on a multi-segment path whose final segment is
# itself the shortcut name.
_WEAK_PK_ON_SEGMENT = _def("""\
  if fieldIsRelation && relatedHasOrdering &&
      (fieldAttr != some (lastSegment path)) && (lastSegment path != "pk") then
    return true
  return false""")

# weak-absent-attr — NO nagini counterpart: nagini's carrier had no absent-value
# case for the stored attribute (it was an unconditional PSeq). Here `fieldAttr`
# is an `Option String`, and this rival treats an ABSENT stored attribute as
# though it matched the final segment, suppressing expansion. Correct on the whole
# `some` half of that binder (checked exhaustively over the four binders); on the
# `none` half it is wrong exactly where the other three conjuncts hold — i.e. at
# every input whose frozen decision is `true`. It only ever under-expands.
_WEAK_ABSENT_ATTR = _def("""\
  match fieldAttr with
  | none => return false
  | some a =>
    if fieldIsRelation && relatedHasOrdering &&
        (a != lastSegment path) && (path != "pk") then
      return true
    return false""")


# --- Witness helpers.
#
# `_w_decide`: the refutation needs no split value, so state the spec predicate at
# a fully concrete input and close with `decide`. Used where a boolean conjunct or
# the literal path/shortcut comparison decides the disagreement.
def _w_decide(args_1, args_2=None):
    a2 = args_2 if args_2 is not None else args_1
    return f"""\
example : ¬ problem_spec_orderingExpandsRelation {args_1}
    (implementation_orderingExpandsRelation {a2}) := by
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
  decide"""


# `_w_split`: the refutation genuinely needs the path's split, which does not
# reduce in the kernel (see the header note). Condition on it instead — one true
# hypothesis per DISTINCT split term, naming the split of one concrete literal
# path. The claim made is exactly "at this input, given how this literal path
# splits, the rival's answer contradicts the spec".
#
# The `pure` hint is LOAD-BEARING and was added by the independent audit; see the
# "forgery" note in the header. Without it, `simp` leaves the imperative body's
# residual `pure true = true` unreduced on the frozen impl, so the gold-side
# build fails for a tactic reason on three of these cases and its EXIT CODE stops
# tracking the claim. With it, the flipped claim (the same statement without the
# `¬`, i.e. "gold is correct here") ELABORATES against the frozen solution, which
# is the strongest gold-side evidence available: the same tactic script proves the
# claim true of gold and proves its negation of the rival.
def _w_split(binders, hyps, args):
    return f"""\
example {binders} :
    ¬ problem_spec_orderingExpandsRelation {args}
      (implementation_orderingExpandsRelation {args}) := by
  unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
    lastSegment
  simp [Id.run, pure, {hyps}]"""


_SPLIT_RECORD_ROOT_ID = '(hs : "record__root_id".splitOn "__" = ["record", "root_id"])'
_SPLIT_RECORD_ROOT = '(hs : "record__root".splitOn "__" = ["record", "root"])'
_SPLIT_RECORD_PK = '(hs : "record__pk".splitOn "__" = ["record", "pk"])'
_SPLIT_PK = '(hs : "pk".splitOn "__" = ["pk"])'
_SPLIT_ROOT_ID_BOTH = ('(hs : "root_id".splitOn "__" = ["root_id"])\n'
                       '    (hs1 : "root_id".splitOn "_" = ["root", "id"])')


SPEC_TESTS = [
    # ------------------------------------------------------------------ POSITIVES
    {
        "id": "pos-guard-ladder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LADDER, _POS_LADDER_PROOF),
        "rationale": (
            "ports nagini pos-control-nested-branches. A correct impl built from "
            "short-circuit guards — conjuncts reordered, early-return polarity "
            "inverted — computes the identical boolean function, so the "
            "biconditional must still hold and the obligation must close. The "
            "proof is the frozen case split with one extra unfolding hint for the "
            "bind chain the ladder introduces; the theorem statement is "
            "byte-identical and no lemma/axiom is added. If it fails => "
            "SPEC-TOO-STRONG (the spec would be pinned to the frozen syntactic "
            "shape rather than to the function)."
        ),
    },
    {
        "id": "pos-pure-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE_MATCH),
        "rationale": (
            "ports nagini pos-control-local-bool onto this carrier: the imperative "
            "wrapper is dropped entirely and the two boolean observations are "
            "dispatched by pattern match, with the remaining two conjuncts "
            "returned as a plain Bool expression. Definitionally the same "
            "function, so the frozen proof script closes unchanged. Confirms the "
            "obligation does not depend on the imperative encoding. If it fails "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-let-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LET),
        "rationale": (
            "the other half of nagini pos-control-local-bool: bind the final "
            "segment and the two-boolean part to locals and branch on the "
            "conjunction once. let-inlining is definitional so the frozen proof "
            "script closes unchanged. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-inline-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_INLINE_SPLIT, _POS_INLINE_SPLIT_PROOF),
        "rationale": (
            "no nagini counterpart — nagini's caller pre-split the path, so this "
            "shape did not exist there. This impl never names the helper symbol "
            "the spec's third conjunct names, inlining the same split expression "
            "instead. Verifying shows that conjunct is pinned to the helper's "
            "VALUE and is not satisfiable only by a syntactic echo of the spec's "
            "own symbol — which is what makes the header's 'grounded, not an "
            "oracle' claim measured. The proof unfolds the helper and restates the "
            "case split over the inlined form; statement byte-identical. If it "
            "fails => SPEC-TOO-STRONG (the conjunct would demand the echo)."
        ),
    },
    {
        "id": "pos-other-split-default",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_OTHER_DEFAULT, _POS_OTHER_DEFAULT_PROOF),
        "rationale": (
            "no nagini counterpart; added by the independent audit to close a "
            "soundness-probe gap. The spec's helper reads the split's last piece "
            "with a DEFAULT for the empty-list case; this impl supplies a "
            "different, deliberately absurd default. The two agree everywhere "
            "because the split is never empty — but that is a theorem about the "
            "carrier, not a definitional identity, so this cannot pass by "
            "coincidence of syntax the way an impl copying the default verbatim "
            "can. Verifying establishes the third conjunct is pinned to the "
            "OBSERVABLE final segment rather than to the particular unreachable "
            "default the frozen helper names. The proof supplies the nonemptiness "
            "fact as a `have` (splitOnAux is @[irreducible], so simp/decide/omega "
            "cannot see through it; `fun_induction` on its equation lemma can) and "
            "otherwise keeps the frozen case ladder; statement byte-identical. If "
            "it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-option-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_OPTION_DISPATCH, _POS_OPTION_DISPATCH_PROOF),
        "rationale": (
            "no nagini counterpart; added by the independent audit. Reads the "
            "split's last piece as an Option and dispatches on it, so the "
            "empty-split case is a REAL branch of the impl rather than an "
            "unreachable default, and the two-boolean conjunction sits inside the "
            "`some` arm. This is the shape the battery's own prose claimed to have "
            "probed while shipping no case for it. Same nonemptiness `have`; "
            "statement byte-identical. If it fails => SPEC-TOO-STRONG (the spec "
            "would demand the total-default reading of the final segment)."
        ),
    },
    {
        "id": "admiss-spec-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_SHAPE),
        "rationale": (
            "the only form nagini admiss-reproducer-caller can take here: this "
            "obligation carries NO precondition hypothesis (the final segment is "
            "total for every path), so there is no Requires to establish at a call "
            "site, and what survives of the nagini control is the claim that the "
            "spec is satisfiable at the legitimate issue-shaped points. Nagini's "
            "in-body Assert(...) becomes an in-body `have … := by decide`: the "
            "primary-key shortcut resolving to no expansion, an ordinary lookup on "
            "a relation with a declared default ordering resolving to expansion, "
            "a relation with no declared default ordering resolving to no "
            "expansion, and the separation fact that a multi-segment path differs "
            "from its own final segment. The audit added the two that carry the "
            "issue's actual shape, which the `decide`-only form could not reach: "
            "the spec is discharged AT the two-segment reproducer path in both "
            "directions — no expansion when its final segment is the stored "
            "attribute, expansion when it is not — conditioned on that path's "
            "split, since splitOn does not reduce in the kernel. That is the "
            "unsatisfiable-at-an-F2P-shaped-input test this lane exists for on a "
            "total carrier. Impl otherwise frozen and the frozen proof kept "
            "verbatim, so the only failure mode is a spec-shape regression at "
            "those points => PRECOND-TOO-STRONG / unsatisfiable spec."
        ),
    },

    # -------------------------------------------------------------------- RIVALS
    {
        "id": "weak-whole-path-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WHOLE_PATH),
        "witness": _w_split(
            _SPLIT_RECORD_ROOT_ID, "hs",
            'true true (some "root_id") "record__root_id"'),
        "refinement": (
            "this is the behaviour the change replaces: the stored attribute is "
            "compared against the whole lookup path rather than against the path's "
            "final segment. Its faithful real patch is the unpatched comparison, "
            "and on the F2P reproducer — a self-referential relation ordered by its "
            "own stored column through a two-segment lookup — the whole path "
            "differs from the bare attribute, so the guard fires and the related "
            "model's declared default ordering is expanded instead of the column "
            "being ordered directly. test_order_by_self_referential_fk observes "
            "the extra join and the wrong direction and FAILS. verify⇏resolve."
        ),
        "rationale": (
            "rejected by the third conjunct (fieldAttr ≠ some (lastSegment path)). "
            "At fieldIsRelation=true, relatedHasOrdering=true, "
            "fieldAttr=some \"root_id\", path=\"record__root_id\": the final "
            "segment IS the stored attribute so the spec requires false, but the "
            "rival compares against the whole path, finds them different, and "
            "returns true. Witness conditions on the one split it needs (that "
            "literal path splits into two named pieces) because splitOn does not "
            "reduce in the kernel; that single hypothesis is true and consistent."
        ),
    },
    {
        "id": "weak-drop-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_PK),
        "witness": _w_decide('true true none "pk"'),
        "refinement": (
            "dropping the primary-key shortcut exclusion. A real patch without it "
            "would, for an ordering written as the bare shortcut on a relation "
            "that declares a default ordering, expand that related model's "
            "ordering instead of sorting by the primary-key column directly — "
            "changing the result order of existing shortcut orderings, which this "
            "change does not touch. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the fourth conjunct (path ≠ \"pk\"): at "
            "fieldIsRelation=true, relatedHasOrdering=true, fieldAttr=none, "
            "path=\"pk\" the spec requires false (the RHS's last conjunct is "
            "false) but the rival returns true. Witness is fully concrete and "
            "closes by `decide` — the refutation never needs the split value, "
            "since `none ≠ some _` and the literal path comparison both reduce."
        ),
    },
    {
        "id": "weak-drop-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_ORDERING),
        "witness": _w_decide('true false none "author"'),
        "refinement": (
            "dropping the requirement that the related model declares a default "
            "ordering. A real patch without it would try to expand an ordering "
            "that does not exist, so a relation with no declared default ordering "
            "would no longer be ordered by the named column at all. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by the second conjunct: at fieldIsRelation=true, "
            "relatedHasOrdering=false, fieldAttr=none, path=\"author\" the spec "
            "requires false but the rival returns true. Varies the "
            "relatedHasOrdering binder, which no other reject witness holds at "
            "false except weak-relation-only's. Concrete `decide` witness."
        ),
    },
    {
        "id": "weak-drop-relation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_RELATION),
        "witness": _w_decide('false true none "author"'),
        "refinement": (
            "dropping the requirement that the resolved field is a relation. A "
            "non-relation field has no related model whose default ordering could "
            "be expanded, so a real patch without this conjunct would attempt the "
            "expansion for ordinary concrete columns. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the first conjunct: at fieldIsRelation=false, "
            "relatedHasOrdering=true, fieldAttr=none, path=\"author\" the spec "
            "requires false but the rival returns true. The ONLY reject witness "
            "that holds fieldIsRelation at false, so it is what varies that "
            "binder. Concrete `decide` witness."
        ),
    },
    {
        "id": "weak-pk-operand-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PK_OPERAND),
        "witness": _w_split(
            _SPLIT_PK, "hs",
            'true true (some "parent_ptr_id") "pk"'),
        "refinement": (
            "testing the field's own stored attribute against the shortcut name "
            "instead of testing the lookup against it. A real patch with this "
            "operand swap mis-guards the shortcut in both directions: a shortcut "
            "ordering on a relation whose stored attribute is not the shortcut "
            "name would wrongly expand the related default ordering. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by the fourth conjunct at a point where the rival's "
            "substituted operand disagrees with it: fieldIsRelation=true, "
            "relatedHasOrdering=true, fieldAttr=some \"parent_ptr_id\", "
            "path=\"pk\". The spec requires false (path IS the shortcut) but the "
            "rival's test (stored attribute ≠ shortcut) passes and it returns "
            "true. Distinct from weak-drop-pk's witness: this one holds fieldAttr "
            "at a `some`, exercising the operand the rival actually substituted, "
            "where weak-drop-pk holds it at `none`. Conditions on the split of "
            "\"pk\" (one true hypothesis) because the third conjunct is still "
            "present and must be evaluated."
        ),
    },
    {
        "id": "weak-relation-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RELATION_ONLY),
        "witness": _w_split(
            _SPLIT_RECORD_ROOT_ID, "hs",
            'true false (some "root_id") "record__root_id"'),
        "refinement": (
            "expanding the related default ordering for EVERY relation field, "
            "ignoring the declared-ordering, shortcut and stored-attribute guards "
            "alike. This is the over-expansion the issue reports, in its most "
            "extreme form; it fails the F2P and would additionally change the "
            "order of relations that declare no default ordering. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the biconditional on a wide sub-domain; the witness picks "
            "a point where TWO of the RHS conjuncts genuinely fail at once — "
            "relatedHasOrdering=false AND fieldAttr=some \"root_id\" equal to the "
            "final segment of the multi-segment path \"record__root_id\" — so the "
            "spec requires false while the rival, reading only the relation "
            "observation, returns true. (Audit note: the earlier form of this "
            "witness held fieldAttr=some \"id\", which does NOT equal that path's "
            "final segment \"root_id\"; only ONE conjunct failed there, so the "
            "'two conjuncts' claim was false as written. Corrected to a point "
            "where it is true; rebuilt both ways — holds of the rival, fails on "
            "the frozen solution with a semantic `⊢ False`.) Probed at a point no "
            "other witness uses — a multi-segment path combined with "
            "relatedHasOrdering=false — so the cheap collapse is not refuted at a "
            "point already covered by the drop-conjunct rivals."
        ),
    },
    {
        "id": "weak-never-expands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NEVER),
        "witness": _w_decide('true true none "author"'),
        "refinement": (
            "never expanding any related model's default ordering. A real patch "
            "that removed the branch entirely would break the pre-existing "
            "behaviour the change deliberately preserves — ordering by a relation "
            "that declares a default ordering adopts that ordering — so the "
            "ordering tests that depend on the expansion fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the biconditional's forward direction wherever the "
            "four-way conjunction holds: at fieldIsRelation=true, "
            "relatedHasOrdering=true, fieldAttr=none, path=\"author\" the spec "
            "requires true and the rival returns false, so this case pins the ⇐ "
            "half of the biconditional. It is the only rival that under-expands "
            "EVERYWHERE (it never over-expands at any input); weak-first-segment, "
            "weak-pk-on-final-segment and weak-absent-attr are also refuted in "
            "the ⇐ direction at their own witness points, so the ⇐ half is pinned "
            "at four distinct points rather than only here. (Audit note: this "
            "rationale previously claimed to be the ONLY rival refuted in that "
            "direction — measured false over the four binders; corrected.) "
            "Concrete `decide` witness — `none ≠ some _` reduces without the "
            "split value."
        ),
    },
    {
        "id": "weak-single-underscore-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SINGLE_SEP),
        "witness": _w_split(
            _SPLIT_ROOT_ID_BOTH, "hs, hs1",
            'true true (some "root_id") "root_id"'),
        "refinement": (
            "splitting the lookup on a single underscore rather than on the "
            "two-character lookup separator. A real patch reading the path that "
            "way agrees with the intended decision for every lookup whose segments "
            "contain no underscore, but for a stored-column lookup whose attribute "
            "name itself contains one — precisely the `_id`-suffixed attribute the "
            "F2P reproducer orders by — it compares the attribute against a "
            "fragment of itself, finds them different, and expands the related "
            "default ordering. The F2P then still observes the extra join. Does "
            "NOT resolve. PARTIAL-DOMAIN attack."
        ),
        "rationale": (
            "rejected by the third conjunct on the sub-domain of paths whose final "
            "segment contains an underscore: at fieldIsRelation=true, "
            "relatedHasOrdering=true, fieldAttr=some \"root_id\", "
            "path=\"root_id\" the final segment under the real separator IS the "
            "stored attribute so the spec requires false, while the rival's "
            "single-underscore split yields a proper fragment and it returns true. "
            "This rival probes the separator itself, which no ported nagini case "
            "could (the caller pre-split there). The witness carries two "
            "hypotheses because it needs both splits of that literal — they are "
            "about DIFFERENT terms and both true, and the gate's consistency probe "
            "cannot derive False from them (checked)."
        ),
    },
    {
        "id": "weak-first-segment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_FIRST_SEGMENT),
        "witness": _w_split(
            _SPLIT_RECORD_ROOT_ID, "hs",
            'true true (some "record") "record__root_id"'),
        "refinement": (
            "taking the FIRST piece of the split instead of the last: right "
            "separator, right comparison, wrong end of the path. A real patch "
            "reading the leading segment agrees with the intended decision for "
            "every single-segment lookup, but for a multi-segment one it compares "
            "the stored attribute against the relation traversed rather than the "
            "column named — so it both suppresses the expansion where it is wanted "
            "and performs it where the F2P requires the direct column. Does NOT "
            "resolve. PARTIAL-DOMAIN attack."
        ),
        "rationale": (
            "rejected by the third conjunct on the multi-segment sub-domain: at "
            "fieldIsRelation=true, relatedHasOrdering=true, fieldAttr=some "
            "\"record\", path=\"record__root_id\" the FINAL segment differs from "
            "the stored attribute so the spec requires true, while the rival's "
            "leading segment equals it and it returns false. Note the direction: "
            "this is a ⇐-half violation at a multi-segment path, whereas "
            "weak-whole-path-operand violates the ⇒ half at one — the same binder "
            "abused from the opposite side, at a distinct fieldAttr value."
        ),
    },
    {
        "id": "weak-pk-on-final-segment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PK_ON_SEGMENT),
        "witness": _w_split(
            _SPLIT_RECORD_PK, "hs",
            'true true none "record__pk"'),
        "refinement": (
            "applying the final-segment reading to the shortcut exclusion as well "
            "as to the stored-attribute comparison. A real patch that did so would "
            "treat a multi-segment lookup ending in the shortcut name as if the "
            "ordering were the bare shortcut, suppressing an expansion that the "
            "unchanged behaviour performs — the shortcut exclusion is about the "
            "lookup as a whole, not about its final segment. Does NOT resolve."
        ),
        "rationale": (
            "the TIGHTEST near-miss here: it gets the third conjunct exactly right "
            "and differs from the frozen decision only on multi-segment paths whose "
            "final segment is the shortcut name. Rejected by the fourth conjunct at "
            "fieldIsRelation=true, relatedHasOrdering=true, fieldAttr=none, "
            "path=\"record__pk\": the whole path is NOT the shortcut so the spec "
            "requires true, but the rival's final-segment test fires and it returns "
            "false. Its own point, distinct from every other witness, because a "
            "rival that agrees with gold over this much of the domain would "
            "otherwise claim a sub-domain the manifest never demonstrates."
        ),
    },
    {
        "id": "weak-absent-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT_ATTR),
        "witness": _w_split(
            _SPLIT_RECORD_ROOT, "hs",
            'true true none "record__root"'),
        "refinement": (
            "treating a field with NO stored attribute as though its attribute "
            "matched the path's final segment, suppressing the expansion. A real "
            "patch doing so would stop expanding the declared default ordering for "
            "exactly those relations that have no stored attribute of their own — "
            "the reverse-relation traversals whose ordering the unchanged behaviour "
            "expands — so orderings that pass today would change. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the third conjunct on the `none` half of the fieldAttr "
            "binder — specifically at those of its points where the other three "
            "conjuncts hold, which is where the frozen decision is true: at "
            "fieldIsRelation=true, relatedHasOrdering=true, "
            "fieldAttr=none, path=\"record__root\" the spec requires true (an "
            "absent attribute can never equal a segment, so the conjunct holds) "
            "but the rival returns false. (Audit note: 'wrong on the ENTIRE none "
            "half' as previously written overstated it — on the rest of the none "
            "half both answers are false and the rival agrees; corrected.) This "
            "is the only rival that treats the "
            "ABSENT case of that binder specially — every other one either passes "
            "it through or is refuted at a `some` — so without it the `none ≠ "
            "some _` half of the third conjunct would be pinned only where gold "
            "and rival happen to agree."
        ),
    },
]

# No axiomatized callee on this path (meta.axioms == [], deep_model_references ==
# []): the split and both comparisons are modeled directly, so there is nothing
# for the axiom lane to execute. Matches the nagini sibling's empty AXIOM_TESTS.
AXIOM_TESTS = []
