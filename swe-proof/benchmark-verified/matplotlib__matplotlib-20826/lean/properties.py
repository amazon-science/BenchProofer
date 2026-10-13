# properties.py — G-PBT falsification battery for matplotlib__matplotlib-20826 (lean lane).
#
# PORTED from the nagini sibling's battery (../nagini/properties.py): the
# adversarial ARGUMENTS are carried over, the mechanics re-expressed against this
# backend's carrier. NOT a Lean file — a record of adversarial cases the G-PBT
# gate executes. Each SPEC case is a FULL Solution.lean variant that shares the
# FROZEN spec byte-for-byte (region surgery: only text inside an `-- impl-start`/
# `-- impl-end` region — and, for a case that legitimately re-proves, inside the
# `-- proof-start`/`-- proof-end` region — is changed, so `markers.same_spec`
# holds and every `theorem correct_clear` STATEMENT stays byte-identical).
# `expect="verify"` passes iff (in scope AND the file elaborates with the
# obligation closed); `expect="reject"` passes iff (in scope AND it does NOT
# verify AND the case's refutation `witness` holds of the rival while FAILING on
# the frozen solution).
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json).
#   A single modeled function re-initialises an axis' tick configuration:
#
#     clear (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair
#
#   `s` is the pair of tick-keyword tables (major, minor), each a total map
#   `String → Option Bool` (present key ↦ `some v`, absent ↦ `none`). The single
#   postcondition `problem_spec_clear` pins the result COMPLETELY (frame
#   discipline) with four independent clauses:
#     (C1) the major table's grid entry equals `majorGridOn gridEnabled which`
#          (= gridEnabled AND which ∈ {both, major});
#     (C2) the minor table's grid entry equals `minorGridOn gridEnabled which`
#          (= gridEnabled AND which ∈ {both, minor});
#     (C3) every OTHER key of the major table is unchanged from its prior value;
#     (C4) every OTHER key of the minor table is unchanged from its prior value.
#   majorGridOn/minorGridOn are total, transparent boolean folds over the two
#   inputs — no opaque callee, no answer-key oracle — so a witness reduces them at
#   any literal input with `simp [majorGridOn]` / `Function.update` lemmas.
#
# BINDER / CLAUSE COVERAGE. The spec's input binders are (s, gridEnabled, which).
# The reject witnesses vary them across FIVE distinct input points and exercise
# every top-level clause, in every violation direction the clause admits:
#   * partial-domain     → C1, at (gridEnabled=true, which="minor");
#   * wrong-conjunction  → C1, at (gridEnabled=false, which="major");
#   * value-swap         → C2, at (gridEnabled=true, which="major");
#   * drop-others        → C3, present entry rewritten to ABSENT;
#   * spurious-key       → C4, absent entry rewritten to PRESENT;
#   * cross-table        → C3, present entry rewritten to a DIFFERENT PRESENT
#                          value, at the battery's only input where the two
#                          tables disagree (`s.major ≠ s.minor`) — which is what
#                          pins each preservation clause to ITS OWN table.
# The `which` binder is varied over "minor"/"major", the `gridEnabled` binder
# over true/false, and the `s` binder over tables that DO / DO NOT carry a
# non-grid entry AND that DO / DO NOT agree with each other — so a rival that
# mishandled only one axis, only one flag value, only the preservation of stored
# entries, or only which table an entry came FROM is caught by a witness that
# abuses exactly that input.
#
# SPEC STRENGTH IS MACHINE-CHECKED, not merely sampled (audit wave). The reject
# lane above samples the spec at five points, but this spec admits a stronger
# statement, and it was PROVEN rather than argued:
#
#   theorem audit_spec_unique (s g w) (r1 r2)
#       (h1 : problem_spec_clear s g w r1) (h2 : problem_spec_clear s g w r2) :
#       (∀ k, r1.major k = r2.major k) ∧ (∀ k, r1.minor k = r2.minor k)
#
# plus its corollary against `correct_clear`: ANY result satisfying the
# postcondition is extensionally equal to the frozen impl's, at every input.
# Both elaborate (exit 0, checked against the frozen file). The postcondition is
# therefore FUNCTIONALLY COMPLETE — it determines the result uniquely, so there
# is no wrong impl of the modeled behaviour left for a SPEC-TOO-WEAK rival to
# find, and the reject lane's job is only to demonstrate the clauses BITE at
# concrete inputs. These two theorems are the audit's evidence and deliberately
# do NOT ship in Solution.lean (the frozen artifact is not edited from this lane).
#
# CARRIER NOTE / relation to the nagini sibling. Nagini modeled the step as TWO
# byte-identical functions (`reinit_tick_kw_major` / `reinit_tick_kw_minor`) each
# over a single `Dict[int, bool]` held at Acc(dict_pred,1/2), with THREE post
# clauses — (1) grid value, (2) preservation, (3) no-spurious. This lean carrier
# folds both functions into ONE pure `clear` over a `TickKwPair` (major+minor
# tables together), so nagini's two symmetric functions become the two grid-value
# clauses (C1, C2) and the two preservation clauses (C3, C4). Crucially, nagini's
# clause (2) "preservation" and clause (3) "no-spurious" MERGE on this carrier:
# a total map `String → Option Bool` with `result k = s k` for every non-grid `k`
# forbids BOTH dropping a stored entry (result would be `none ≠ some v`) AND
# injecting a spurious one (result would be `some _ ≠ none`). So the nagini
# `_DROP_OTHERS` rival ports onto C3/C4 (drops a stored entry) and `_SPURIOUS`
# ports onto C4 (injects an entry) — same clause, distinct violation directions,
# each with its own witness. The nagini `_PARTIAL_DOMAIN` and `_WRONG_OR` grid-
# value rivals port onto C1; a value-swap rival additionally pins C2 independently
# (nagini had no cross-table swap because its two functions were separate files).
#
# LANES THAT DO NOT PORT (see 'assessment'):
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_MUT`: `tick_kw` held at
#     Acc(dict_pred,1/2), the rival wrote the grid key into the read-only input
#     and returned it, rejected for insufficient permission). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "store into a read-only input" rival is not expressible and the lane is
#     VACUOUS here. The frame OBLIGATION that survives is instead the explicit
#     preservation of every non-grid entry (C3/C4), attacked by drop-others /
#     spurious-key.
#   * ADMISSIBILITY (nagini's `_ADMISS` defended that Acc(dict_pred,1/2) is
#     establishable for an F2P-shaped input). The lean obligation carries NO
#     precondition hypothesis (the modeled behaviour is total), so nothing could
#     be PRECOND-TOO-STRONG in nagini's permission sense. The lane is NOT dropped:
#     the analogue on a total carrier is the obligation being unsatisfiable — or
#     satisfiable only vacuously — at an F2P-shaped input, and
#     `admiss-ground-instance` tests that directly, by EVALUATION at that concrete
#     input (see its comment; wave a7 rewrote it after finding the port's form was
#     a copy of the frozen theorem at an instance and so untestable).
#   * DIVERGENCE / NON-TERMINATION. Re-derived with a real build in the audit
#     wave rather than argued: `partial def implementation_clear … :=
#     implementation_clear s gridEnabled which` (self-recursive, plus the
#     `Inhabited TickKwPair` instance `partial` requires) is IN SCOPE — it passes
#     variant_problems — and it does NOT verify (exit 1): a `partial def` has no
#     equation lemmas, so `unfold implementation_clear` fails outright and the
#     obligation cannot be discharged at all, let alone vacuously. This backend is
#     NOT the velvet `loom.semantics.termination "partial"` lane where a diverging
#     impl verifies vacuously (the corpus-wide termination-semantics finding, 401 velvet bundles,
#     lean unaffected). So the class is genuinely closed here — by the absence of
#     partial-correctness semantics, not by "you cannot write it".
#   * AXIOM_TESTS (nagini's `ax-*-dict_carry_over`). The axiom lane is G-AX's job;
#     this gate ignores it. Here the copy+preserve behaviour is modeled DEEPLY as
#     the `Function.update` frame, so there is no consumed axiom anyway.
#
# WITNESS DISCRIMINATION IS MACHINE-CHECKED IN BOTH DIRECTIONS (audit wave a7).
# Every reject case's gold-side failure is the shape `unsolved goals … hN : True ⊢
# False` — an application of the destructured conjunct after `simp` reduced it. That
# shape is admissible evidence only if gold's exit code TRACKS THE CLAIM, so it was
# tested by forgery rather than read: for each of the six cases a file differing from
# the witness ONLY in what it claims (the `¬` dropped, i.e. asserting the spec HOLDS
# at that same input, closed by the frozen tactic shape) was built against both
# sides. Result, all six: the flipped claim ELABORATES against the frozen solution
# (exit 0) and FAILS against the rival (exit 1) with a concrete residual goal naming
# the disagreement — e.g. value-swap prints `⊢ some (majorGridOn true "major") =
# some (minorGridOn true "major")`, cross-table prints `⊢ Function.update (fun x =>
# none) "tick1On" (some true) k = Function.update (fun x => none) "tick1On" (some
# false) k`. So the two sides' exit codes are exactly INVERTED by flipping the claim:
# gold's code carries full information about the claim, `hN : True` means `simp`
# genuinely PROVED the equation for the frozen impl, and no case is hollow.
#
# AUDIT-WAVE CORRECTION to the port's omission ledger. The port recorded nagini's
# `pos-commuted-and` as carried over; it was NOT — the port's two positives are
# both DEFINITIONALLY the frozen impl (`rfl` probes elaborate), so neither is the
# commuted-conjunction reshape, and the battery had no positive testing anything
# beyond impl-region surface syntax. `pos-commuted-and` is restored below with a
# real reproof, joined by `pos-shared-rule-helper`. The port also left the
# preservation frame's value-change direction unattacked (drop/inject only); the
# `cross-table-carry-over` rival closes that, and is the only case whose witness
# sits at an input where the two tables disagree.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20826"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique
# in the file. Every rival (and the reshape positives) swap THIS block.
_IMPL = (
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some (majorGridOn gridEnabled which))\n"
    "  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))\n"
    "  return ⟨major, minor⟩"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only
# by the pure-structure positive, whose different impl shape needs an (equally
# cheap, honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro s gridEnabled which\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  simp only [Id.run, pure]\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · rw [Function.update_self]\n"
    "  · rw [Function.update_self]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

# The head of the proof region — for the admissibility ground instance.
_PROOF_HEAD = (
    "theorem correct_clear :\n"
    "    ∀ (s : TickKwPair) (gridEnabled : Bool) (which : String),\n"
    "      problem_spec_clear s gridEnabled which\n"
    "        (implementation_clear s gridEnabled which) := by\n"
    "  intro s gridEnabled which"
)
assert _BASE.count(_PROOF_HEAD) == 1, "proof-head anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-let-bound-values: structurally different but CORRECT — the two grid values
# are bound to locals before the table updates. Output equals the frozen impl's
# on every input; the theorem statement is byte-identical AND the frozen proof
# body still closes (the `let` bindings are definitionally transparent). No
# reproof, no new axiom/lemma/sorry.
#
# STRENGTH CAVEAT (measured, audit wave): this reshape is DEFINITIONALLY the
# frozen impl — `example : implLet = implementation_clear := rfl` elaborates
# (exit 0). So it re-checks only that the spec is not over-fit to the SURFACE
# SYNTAX of the impl region; it cannot detect a spec over-fit to the frozen
# impl's DENOTATION, because there is no denotational difference to detect.
# `pos-commuted-and` below is the positive that carries that weight: it is
# provably NOT defeq to the frozen impl (the `rfl` probe fails, exit 1) and the
# frozen proof body does NOT close it (exit 1), so it must be reproven.
_POS_LET = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mg := majorGridOn gridEnabled which\n"
    "  let mng := minorGridOn gridEnabled which\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some mg)\n"
    "  minor := Function.update minor gridKey (some mng)\n"
    "  return ⟨major, minor⟩",
)

# pos-pure-structure: a structurally different CORRECT impl written as a pure
# structure literal (no `Id.run do`, no `let mut`), directly building the result
# pair. Semantics identical on every input. The theorem STATEMENT is byte-
# identical; its proof is reproven honestly (`dsimp only` to reduce the structure
# projections, then the same frame rewrites) inside proof-start/proof-end — no
# new axiom/lemma/sorry, just the cheapest tactic for the new shape.
#
# STRENGTH CAVEAT (measured, audit wave a7 — CORRECTED). Like pos-let-bound-values,
# this impl is DEFINITIONALLY the frozen one (`example : @implPure =
# @implementation_clear := rfl` elaborates, exit 0) — `Id.run do` with `let mut`
# REDUCES to the structure literal. A previous audit wave claimed this case
# additionally tested "that the obligation survives the loss of the monadic wrapper
# the frozen proof's `simp only [Id.run, pure]` line targets (the reproof NEEDS
# `dsimp only` instead)". That parenthetical is FALSE and was re-measured: putting
# the FROZEN proof body back over this impl verbatim ELABORATES (exit 0; the only
# diagnostics are `unusedSimpArgs` linter warnings that `Id.run` and `pure` are
# unused simp arguments). So the frozen script closes this impl too, and the
# `dsimp only` below is an equivalent alternative rather than a necessity.
# What this case therefore tests is exactly what pos-let-bound-values tests — that
# the spec is not over-fit to the frozen impl's SURFACE SYNTAX — at a second,
# further-away syntactic point (no `Id.run do`, no `let mut`, a bare structure
# literal). It does NOT test denotational tolerance and it does NOT probe a tactic
# the frozen script cannot supply; `pos-commuted-and` and `pos-shared-rule-helper`
# are the positives that carry those two weights (both measured NOT defeq, exit 1,
# and both measured to defeat the frozen proof body, exit 1).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_clear\n"
        "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair :=\n"
        "  ⟨Function.update s.major gridKey (some (majorGridOn gridEnabled which)),\n"
        "   Function.update s.minor gridKey (some (minorGridOn gridEnabled which))⟩",
    ),
    _PROOF,
    "  intro s gridEnabled which\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  dsimp only\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · rw [Function.update_self]\n"
    "  · rw [Function.update_self]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]",
)

# pos-commuted-and: the nagini sibling's `pos-commuted-and`, which the port
# dropped and this audit restored. Each grid value is written with the two
# conjuncts COMMUTED — the which-membership test first, the global enable flag
# second. `&&` is commutative on Bool so the value is identical at every input,
# but the term is NOT definitionally the frozen one: the audit's probe
# `example : implComm = implementation_clear := rfl` FAILS (exit 1), and the
# frozen proof body does NOT close this impl (exit 1, `unsolved goals ⊢ some
# ((which == "both" || which == "major") && gridEnabled) = some (majorGridOn
# gridEnabled which)`). So this is the battery's only positive that tests
# DENOTATIONAL tolerance rather than surface-syntax tolerance: the spec must
# accept a correct impl whose grid term is a genuinely different Bool expression,
# reachable only through `Bool.and_comm`. Reproven honestly with that one lemma —
# no new axiom/lemma/sorry declaration, the theorem statement byte-identical.
_POS_COMMUTE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_clear\n"
        "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
        "  let mut major := s.major\n"
        "  let mut minor := s.minor\n"
        "  major := Function.update major gridKey"
        " (some ((which == \"both\" || which == \"major\") && gridEnabled))\n"
        "  minor := Function.update minor gridKey"
        " (some ((which == \"both\" || which == \"minor\") && gridEnabled))\n"
        "  return ⟨major, minor⟩",
    ),
    _PROOF,
    "  intro s gridEnabled which\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  simp only [Id.run, pure]\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · rw [Function.update_self, majorGridOn, Bool.and_comm]\n"
    "  · rw [Function.update_self, minorGridOn, Bool.and_comm]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]",
)

# pos-shared-rule-helper: a CORRECT impl that factors the two tables' shared rule
# into ONE helper parameterised by the axis selector, and expresses the enable
# flag as an `if … then … else false` rather than a `&&`. Both departures are
# real: the impl-region helper `def` is new vocabulary (admissible — same_spec
# elides the impl region), the grid term is not defeq to the frozen one, and the
# frozen proof body does not close it (case analysis on `gridEnabled` is needed to
# collapse the `if`). Verifies. This is the reshape that would catch a spec
# over-fit to the frozen impl's TWO-SEPARATE-EXPRESSIONS structure — the modeled
# behaviour genuinely IS one rule applied twice (Solution.lean's own docstring
# says so), so a faithful impl is allowed to say that once.
_POS_HELPER = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def selGridOn (sel : String) (gridEnabled : Bool) (which : String) : Bool :=\n"
        "  if gridEnabled then (which == \"both\" || which == sel) else false\n"
        "\n"
        "def implementation_clear\n"
        "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair :=\n"
        "  ⟨Function.update s.major gridKey (some (selGridOn \"major\" gridEnabled which)),\n"
        "   Function.update s.minor gridKey (some (selGridOn \"minor\" gridEnabled which))⟩",
    ),
    _PROOF,
    "  intro s gridEnabled which\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  dsimp only\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · rw [Function.update_self]\n"
    "    cases gridEnabled <;> simp [selGridOn, majorGridOn]\n"
    "  · rw [Function.update_self]\n"
    "    cases gridEnabled <;> simp [selGridOn, minorGridOn]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]\n"
    "  · intro k hk\n"
    "    rw [Function.update_of_ne hk]",
)

# admiss-ground-instance: the frozen impl and proof, PLUS a ground discharge of the
# obligation at a concrete F2P-shaped input, then the frozen obligation closed
# verbatim. Verifies (else the modeled behaviour is unsatisfiable at the normal
# input — the analogue of nagini's PRECOND-TOO-STRONG probe). Nothing is assumed:
# the theorem statement is byte-identical, the ground instance is a `have` inside
# the tactic body, no new declaration.
#
# STRENGTHENED by audit wave a7, because the previous form was HOLLOW. It read
#
#     have _ground : problem_spec_clear <lit> true "both"
#                      (implementation_clear <lit> true "both") := by <frozen tactics>
#
# i.e. the `have`'s statement was literally `correct_clear` instantiated at one
# input, proven by copy-pasting the frozen tactic script. Anything the frozen proof
# closes universally it closes at an instance, so that `have` could not fail unless
# `correct_clear` itself failed — the case degenerated to a second copy of the
# frozen file and tested the admissibility direction not at all. It also
# demonstrated NOTHING about the ground input: the spec predicate stayed folded, so
# no concrete value was ever computed.
#
# The strengthened form is satisfiability stated so it must EVALUATE. It exhibits a
# witness result and pins its four observable projections at the F2P-shaped input (a
# major table carrying the non-grid per-side visibility entry "tick1On" ↦ some false,
# minor empty, gridEnabled=true, which="both") to CONCRETE literals by `simp`:
#   * the major grid entry is `some true`   (the flag is actually computed, not folded)
#   * the major "tick1On" entry is STILL `some false`  (the stored entry survives —
#     this is the F2P-observable content, discharged by evaluation)
#   * the minor grid entry is `some true`
#   * the minor "tick1On" entry is `none`   (nothing spurious appears)
# An `∃ r, problem_spec_clear … r ∧ <four literal equations>` cannot be closed by
# instantiating the frozen theorem alone; the equations force the carrier to reduce
# at that point. Measured: exit 0. Had the obligation been unsatisfiable at an
# F2P-shaped input, or had it been satisfiable only vacuously (with the grid flag or
# the preserved entry not actually reducing to the values the modeled behaviour
# requires), this would fail where the old form could not.
_ADMISS = _swap(
    _BASE,
    _PROOF_HEAD,
    "theorem correct_clear :\n"
    "    ∀ (s : TickKwPair) (gridEnabled : Bool) (which : String),\n"
    "      problem_spec_clear s gridEnabled which\n"
    "        (implementation_clear s gridEnabled which) := by\n"
    "  have _ground :\n"
    "      (∃ r : TickKwPair,\n"
    "          problem_spec_clear\n"
    "            ⟨Function.update (fun _ => none) \"tick1On\" (some false), (fun _ => none)⟩\n"
    "            true \"both\" r\n"
    "          ∧ r.major gridKey = some true\n"
    "          ∧ r.major \"tick1On\" = some false\n"
    "          ∧ r.minor gridKey = some true\n"
    "          ∧ r.minor \"tick1On\" = none) := by\n"
    "    refine ⟨implementation_clear\n"
    "        ⟨Function.update (fun _ => none) \"tick1On\" (some false), (fun _ => none)⟩\n"
    "        true \"both\", ?_, ?_, ?_, ?_, ?_⟩\n"
    "    · unfold problem_spec_clear implementation_clear\n"
    "      simp only [Id.run, pure]\n"
    "      refine ⟨?_, ?_, ?_, ?_⟩\n"
    "      · rw [Function.update_self]\n"
    "      · rw [Function.update_self]\n"
    "      · intro k hk\n"
    "        rw [Function.update_of_ne hk]\n"
    "      · intro k hk\n"
    "        rw [Function.update_of_ne hk]\n"
    "    · simp [implementation_clear, majorGridOn]\n"
    "    · simp [implementation_clear, gridKey, Function.update]\n"
    "    · simp [implementation_clear, minorGridOn]\n"
    "    · simp [implementation_clear, gridKey, Function.update]\n"
    "  intro s gridEnabled which",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is
# left in place (it will not close for the reshaped impl, but the gate reads the
# witness — checked in a file with the obligation removed — not the rival's build).
# ===========================================================================

# partial-domain (nagini _PARTIAL_DOMAIN): pin BOTH grid values using ONLY
# gridEnabled, ignoring `which`. Correct where `which` selects the axis, WRONG on
# the sub-domain {gridEnabled=true, which selects the OTHER axis}, where the
# prescribed value is false but this returns true. Violates C1 (and C2).
_RIV_PARTIAL = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some gridEnabled)\n"
    "  minor := Function.update minor gridKey (some gridEnabled)\n"
    "  return ⟨major, minor⟩",
)

# wrong-conjunction (nagini _WRONG_OR): set each grid value to an OR of the two
# config flags instead of the prescribed AND. Wrong whenever exactly one flag
# holds (e.g. gridEnabled=false but which="major"). Violates C1.
_RIV_OR = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some (gridEnabled || (which == \"both\" || which == \"major\")))\n"
    "  minor := Function.update minor gridKey (some (gridEnabled || (which == \"both\" || which == \"minor\")))\n"
    "  return ⟨major, minor⟩",
)

# value-swap: compute BOTH tables' grid entries from `majorGridOn`, so the minor
# table gets the major rule. Correct on the sub-domain where the two rules agree
# (which ∈ {both} or gridEnabled=false), WRONG when which="major": majorGridOn is
# true but minorGridOn is false. Violates C2 specifically — pins the minor-axis
# clause the C1 rivals leave symmetric.
_RIV_SWAP = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some (majorGridOn gridEnabled which))\n"
    "  minor := Function.update minor gridKey (some (majorGridOn gridEnabled which))\n"
    "  return ⟨major, minor⟩",
)

# drop-others (nagini _DROP_OTHERS, the PRE-PATCH behaviour): re-initialise by
# EMPTYING both tables (fresh `fun _ => none`) then setting only the grid entries.
# Sets C1/C2 correctly but DROPS every other stored entry => violates C3 (and C4):
# a previously-recorded key that was `some v` becomes `none`.
_RIV_DROP = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major : TickKw := fun _ => none\n"
    "  let mut minor : TickKw := fun _ => none\n"
    "  major := Function.update major gridKey (some (majorGridOn gridEnabled which))\n"
    "  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))\n"
    "  return ⟨major, minor⟩",
)

# spurious-key (nagini _SPURIOUS): carry both tables over and set the grid entries
# correctly, but ALSO inject an entry not present on entry (key "tick1On" set to
# true). Satisfies C1/C2/C3 but violates C4: a key absent on entry (`none`) is
# present in the result (`some true`).
_RIV_SPURIOUS = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.major\n"
    "  let mut minor := s.minor\n"
    "  major := Function.update major gridKey (some (majorGridOn gridEnabled which))\n"
    "  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))\n"
    "  minor := Function.update minor \"tick1On\" (some true)\n"
    "  return ⟨major, minor⟩",
)


# cross-table-carry-over (NEW, added by the audit): carries each table over from
# the WRONG side of the pair — the major result is built from the minor input's
# entries and vice versa — then sets both grid entries correctly. Satisfies
# C1/C2, and satisfies C3/C4 on the sub-domain where the two tables agree
# (notably both-empty, which is where every other rival's witness sits). WRONG
# whenever the two tables carry different values at some non-grid key: the major
# result then reports the MINOR table's value. This is the third violation
# direction of the preservation frame, and the one the ported rivals leave
# unattacked: drop-others changes `some v` to `none`, spurious-key changes `none`
# to `some v`, and NEITHER changes a present entry to a DIFFERENT present value.
# It also pins that C3 and C4 are keyed to the correct table — a spec stating
# preservation against "the pair" rather than per-table would admit it.
_RIV_CROSS = _swap(
    _BASE,
    _IMPL,
    "def implementation_clear\n"
    "    (s : TickKwPair) (gridEnabled : Bool) (which : String) : TickKwPair := Id.run do\n"
    "  let mut major := s.minor\n"
    "  let mut minor := s.major\n"
    "  major := Function.update major gridKey (some (majorGridOn gridEnabled which))\n"
    "  minor := Function.update minor gridKey (some (minorGridOn gridEnabled which))\n"
    "  return ⟨major, minor⟩",
)


# --- witnesses ---------------------------------------------------------------
# Each refutes `problem_spec_clear` at one concrete input: it ELABORATES against
# the rival (which contradicts the spec there) and FAILS on the frozen solution
# (which satisfies the spec everywhere). All inputs are literal (no opaque term),
# so no witness binds a hypothesis and there is no consistency obligation. Every
# witness was checked with two real builds (rival: elaborates; gold: fails).

# A concrete empty pair `s`, spelled literally so the coverage reader can parse
# each witness's argument list positionally (a `∀`-quantified head reads as
# unreadable). The two preservation clauses are trivially satisfied here, so the
# grid witnesses isolate the grid-value clause they attack.
_EMPTY_S = "⟨(fun _ => none), (fun _ => none)⟩"


def _wit_grid_major(ge, wh):
    """C1 attack (major grid value): destructure the postcondition, reduce the
    grid entry via `Function.update_self`, and expose the boolean disagreement
    with `simp [majorGridOn]`."""
    return (
        f"example :\n"
        f"    ¬ problem_spec_clear {_EMPTY_S} {ge} {wh}\n"
        f"      (implementation_clear {_EMPTY_S} {ge} {wh}) := by\n"
        f"  unfold problem_spec_clear implementation_clear\n"
        f"  simp only [Id.run, pure]\n"
        f"  rintro ⟨h1, _, _, _⟩\n"
        f"  rw [Function.update_self] at h1\n"
        f"  simp [majorGridOn] at h1"
    )


def _wit_grid_minor(ge, wh):
    """C2 attack (minor grid value)."""
    return (
        f"example :\n"
        f"    ¬ problem_spec_clear {_EMPTY_S} {ge} {wh}\n"
        f"      (implementation_clear {_EMPTY_S} {ge} {wh}) := by\n"
        f"  unfold problem_spec_clear implementation_clear\n"
        f"  simp only [Id.run, pure]\n"
        f"  rintro ⟨_, h2, _, _⟩\n"
        f"  rw [Function.update_self] at h2\n"
        f"  simp [minorGridOn, majorGridOn] at h2"
    )


# C3 attack (major preservation): input major table carries "tick1On" ↦ some
# false; the rival empties the table so the entry is dropped to `none`.
_WIT_DROP = (
    "example :\n"
    "    ¬ problem_spec_clear\n"
    "      ⟨Function.update (fun _ => none) \"tick1On\" (some false), (fun _ => none)⟩ true \"both\"\n"
    "      (implementation_clear\n"
    "        ⟨Function.update (fun _ => none) \"tick1On\" (some false), (fun _ => none)⟩ true \"both\") := by\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  simp only [Id.run, pure]\n"
    "  rintro ⟨_, _, h3, _⟩\n"
    "  have hk := h3 \"tick1On\" (by decide)\n"
    "  rw [Function.update_of_ne (by decide)] at hk\n"
    "  simp [Function.update] at hk"
)

# C4 attack (minor no-spurious): input minor table is empty; the rival injects
# "tick1On" ↦ some true, so the result differs from the input at that absent key.
_WIT_SPURIOUS = (
    "example :\n"
    "    ¬ problem_spec_clear\n"
    "      ⟨(fun _ => none), (fun _ => none)⟩ true \"both\"\n"
    "      (implementation_clear\n"
    "        ⟨(fun _ => none), (fun _ => none)⟩ true \"both\") := by\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  simp only [Id.run, pure]\n"
    "  rintro ⟨_, _, _, h4⟩\n"
    "  have hk := h4 \"tick1On\" (by decide)\n"
    "  simp [Function.update] at hk"
)


# C3 attack, VALUE-CHANGE direction (added by the audit). The two input tables
# DISAGREE at the non-grid key "tick1On": major holds `some false`, minor holds
# `some true`. The cross-table rival's major result therefore reports the minor
# input's `some true` where C3 requires the major input's `some false` — a present
# entry rewritten to a different present value, which neither _WIT_DROP (present →
# absent) nor _WIT_SPURIOUS (absent → present) reaches. Distinct input point from
# every other witness: it is the only one where `s.major ≠ s.minor`.
_WIT_CROSS = (
    "example :\n"
    "    ¬ problem_spec_clear\n"
    "      ⟨Function.update (fun _ => none) \"tick1On\" (some false),\n"
    "       Function.update (fun _ => none) \"tick1On\" (some true)⟩ true \"both\"\n"
    "      (implementation_clear\n"
    "        ⟨Function.update (fun _ => none) \"tick1On\" (some false),\n"
    "       Function.update (fun _ => none) \"tick1On\" (some true)⟩ true \"both\") := by\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  simp only [Id.run, pure]\n"
    "  rintro ⟨_, _, h3, _⟩\n"
    "  have hk := h3 \"tick1On\" (by decide)\n"
    "  rw [Function.update_of_ne (by decide)] at hk\n"
    "  simp [Function.update] at hk"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-let-bound-values",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the two grid values are bound to "
            "locals before the table updates, keeping the carry-over frame and both grid "
            "assignments, so the result equals the frozen impl's on every input. The "
            "theorem statement is byte-identical and the FROZEN proof body still closes "
            "(the `let` bindings are definitionally transparent) — a faithful restructure "
            "with no reproof and no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-pure-structure",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure structure literal (no "
            "`Id.run do`, no `let mut`), directly building the result pair. Semantics "
            "identical on every input. The theorem STATEMENT is byte-identical; the proof "
            "region uses `dsimp only` in place of the frozen `simp only [Id.run, pure]` "
            "before the same frame rewrites — no new axiom/lemma/sorry. STRENGTH, measured "
            "rather than asserted (audit wave a7): this impl is DEFEQ to the frozen one "
            "(`rfl` probe exit 0) AND the frozen proof body closes it unchanged (exit 0), "
            "so the reproof is an equivalent alternative, not a necessity. It therefore "
            "tests the same thing pos-let-bound-values tests — that the spec is not over-fit "
            "to the frozen impl's SURFACE SYNTAX — at a further-away syntactic point, and "
            "nothing more; denotational tolerance is pos-commuted-and's and "
            "pos-shared-rule-helper's job. If it FAILS => SPEC-TOO-STRONG (the postcondition "
            "is bound to the monadic impl shape rather than the behaviour)."
        ),
    },
    {
        "id": "pos-commuted-and",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COMMUTE,
        "rationale": (
            "the nagini sibling's commuted-conjunction positive, restored by the audit. "
            "Each grid value is written with the two conjuncts COMMUTED (which-membership "
            "first, global enable flag second): the same Bool at every input, but a "
            "genuinely different TERM. Measured: it is NOT definitionally the frozen impl "
            "(`example : implComm = implementation_clear := rfl` fails) and the frozen "
            "proof body does NOT close it, so it must be reproven — via `Bool.and_comm`, "
            "one Mathlib lemma, no new declaration. This is the battery's only positive "
            "that tests the spec's tolerance of a different DENOTATION-equal grid "
            "expression rather than merely a different impl-region surface syntax (the "
            "other two positives are defeq to the frozen impl, see their comments). If it "
            "FAILS => SPEC-TOO-STRONG (the postcondition is over-fit to one spelling of "
            "the boolean rule)."
        ),
    },
    {
        "id": "pos-shared-rule-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HELPER,
        "rationale": (
            "a CORRECT impl that factors the two tables' shared rule into ONE "
            "impl-region helper parameterised by the axis selector, and spells the enable "
            "flag as `if gridEnabled then … else false` instead of `&&`. The modeled "
            "behaviour genuinely IS one rule applied twice, so a faithful impl may say it "
            "once; the spec must not require the frozen impl's two-separate-expressions "
            "structure. Not defeq to the frozen impl, and the frozen proof body does not "
            "close it (the `if` needs case analysis on `gridEnabled`), so it is reproven. "
            "No new axiom/lemma/sorry; the added `def` lies inside the impl region, which "
            "same_spec elides, and the theorem statement is byte-identical. If it FAILS "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the re-initialisation obligation is SATISFIABLE at a ground F2P-shaped input, "
            "shown by EVALUATION rather than by re-deriving the frozen theorem. The `have` "
            "exhibits a result at that input (major table carrying the non-grid per-side "
            "visibility entry \"tick1On\" ↦ some false, minor empty, gridEnabled=true, "
            "which=\"both\") and pins its four observable projections to concrete literals: "
            "the two grid entries reduce to some true, the stored \"tick1On\" entry is still "
            "some false (the F2P-observable content — the per-side flag survives the "
            "re-initialisation), and the minor table's \"tick1On\" is still none (nothing "
            "spurious). Verifies (else the modeled behaviour is unsatisfiable, or vacuously "
            "satisfiable, at the normal input — the analogue of the nagini "
            "PRECOND-TOO-STRONG probe). This shape is deliberate: audit wave a7 found the "
            "previous form stated the `have` as `correct_clear` instantiated at one input "
            "and proved it by copying the frozen tactic script, which cannot fail unless "
            "correct_clear itself fails and left the spec predicate folded, so it tested "
            "nothing. The ∃-plus-literal-equations form cannot be closed by instantiating "
            "the frozen theorem; the equations force the carrier to reduce at that point. "
            "Nothing is assumed: no new declaration, the theorem statement is byte-identical, "
            "the ground instance is a `have` inside the existing tactic body."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "partial-domain-ignore-which",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PARTIAL,
        "refinement": (
            "pins the grid flag from `axes.grid` alone, ignoring the which-selection "
            "membership. On the sub-domain grid-enabled but the which-preference NOT "
            "selecting this table's axis (e.g. axes.grid True, axes.grid.which='minor' for "
            "the MAJOR table) it turns the grid on when it must be off — a rendered grid "
            "that should be absent. The check_figures_equal F2P (test_shared_axes_clear) "
            "diverges from the gold image. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (the major grid value must equal `majorGridOn "
            "gridEnabled which` = gridEnabled AND which ∈ {both,major}). At "
            "(gridEnabled=true, which=\"minor\") the spec demands false but the rival "
            "returns gridEnabled=true. Witness probes exactly that sub-domain, varying the "
            "`which` binder to \"minor\". If it VERIFIES => SPEC-TOO-WEAK (the which "
            "dependence is unpinned)."
        ),
        "witness": _wit_grid_major("true", '"minor"'),
    },
    {
        "id": "wrong-conjunction-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OR,
        "refinement": (
            "sets the grid flag to `axes.grid OR which-covers` instead of the prescribed "
            "AND: turns the grid on when only one config flag holds (e.g. axes.grid False "
            "but which='major'), rendering a grid the gold leaves off. Diverges on the "
            "F2P render-equality test. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1. At (gridEnabled=false, which=\"major\") the spec "
            "demands false (false AND _), but the OR returns true. Witness probes the "
            "gridEnabled=false sub-domain — varying the `gridEnabled` binder to false, "
            "distinguishing this near-miss from the partial-domain rival (which agrees "
            "with gold whenever gridEnabled=false). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit_grid_major("false", '"major"'),
    },
    {
        "id": "value-swap-minor-gets-major",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP,
        "refinement": (
            "computes BOTH tables' grid flags from the MAJOR rule, so the minor table's "
            "grid entry follows the major-axis which-membership. When axes.grid.which "
            "selects only 'major', the minor grid is turned on though it must be off — the "
            "minor-axis grid renders when the gold leaves it absent. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (the MINOR grid value must equal `minorGridOn`). At "
            "(gridEnabled=true, which=\"major\") minorGridOn is false but the rival writes "
            "majorGridOn=true. Witness pins the minor-axis clause independently of C1 — the "
            "clause the two C1 rivals leave symmetric. If it VERIFIES => SPEC-TOO-WEAK (the "
            "minor grid value is not independently constrained)."
        ),
        "witness": _wit_grid_minor("true", '"major"'),
    },
    {
        "id": "drop-other-keys-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP,
        "refinement": (
            "this IS the pre-patch behaviour: re-initialise by EMPTYING both tables then "
            "setting only the grid entries. Its faithful real patch drops the inner "
            "shared-axis side-hiding visibility entries on clear, so the F2P "
            "(test_shared_axes_clear) FAILS — hidden ticks/labels reappear and the shared "
            "subplots' images diverge. This is the exact defect the change repairs. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (`result.major k = s.major k` for every non-grid key: "
            "the major table's stored entries are unchanged from their prior value). At an "
            "input whose major table carries \"tick1On\" ↦ some false, the rival returns "
            "none for that key while the spec requires some false. Witness varies the `s` "
            "binder to a table carrying a stored non-grid entry — a binder the grid-value "
            "rivals hold constant. If it VERIFIES => SPEC-TOO-WEAK (the preservation frame "
            "is unconstrained)."
        ),
        "witness": _WIT_DROP,
    },
    {
        "id": "spurious-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SPURIOUS,
        "refinement": (
            "carries both tables over and sets the grid entries correctly, but ALSO injects "
            "a visibility entry the caller never stored. Its faithful real patch adds a "
            "tick-keyword the consumer never expected, changing the rendered tick and "
            "diverging from the gold image. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C4 (`result.minor k = s.minor k` for every non-grid key — "
            "including absent keys, which must stay absent). At an input whose minor table "
            "is empty, the rival returns some true for \"tick1On\" while the spec requires "
            "none. Witness varies `s` to a table where the injected key is absent, "
            "exercising the no-spurious direction of the preservation frame (distinct from "
            "drop-others, which exercises the drop direction). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _WIT_SPURIOUS,
    },
    {
        "id": "cross-table-carry-over",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CROSS,
        "refinement": (
            "carries each table's prior entries over from the wrong side of the pair — the "
            "major table is rebuilt from the minor table's entries and vice versa — then "
            "sets both grid flags correctly. Its faithful real patch swaps the two "
            "keyword tables' preserved contents, so a per-side visibility entry recorded "
            "for the major ticks resurfaces on the minor ticks and vice versa. On the "
            "shared-subplots figure the interior ticks/labels are then suppressed on the "
            "wrong side of each axis, so the rendered figure diverges from the reference. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (`result.major k = s.major k` for every non-grid key — "
            "the MAJOR result's entries must come from the MAJOR input's table). At an "
            "input whose two tables DISAGREE at \"tick1On\" (major ↦ some false, minor ↦ "
            "some true) the rival's major result reports some true where the spec requires "
            "some false. This is the third violation direction of the preservation frame: "
            "drop-others rewrites a present entry to ABSENT, spurious-key rewrites an "
            "absent entry to PRESENT, and only this one rewrites a present entry to a "
            "DIFFERENT PRESENT VALUE. It is also the only case whose witness sits at an "
            "input with `s.major ≠ s.minor`, so it is what pins C3/C4 to their respective "
            "tables — a spec that stated preservation against the pair as a whole, or that "
            "attached each clause to the wrong table, would admit it while every other "
            "rival still failed. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_CROSS,
    },
]


# No consumed axioms and no opaque callees: the grid-flag boolean rule
# (majorGridOn/minorGridOn) and the entry-preservation frame (Function.update) are
# modeled DEEPLY over transparent carriers, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
