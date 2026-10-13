"""properties.py — PBT falsification manifest for django__django-11141 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

This is a PORT of the nagini falsification battery for the same instance. The
nagini sibling is the design document; the adversarial ARGUMENT is carried over
and re-expressed against this backend's carrier.

AUDIT REVISION. An independent audit rebuilt all 11 witnesses on both sides and
ran the flipped-claim forgery test on each; every one discriminates by plain
evaluation (see below). It found and repaired three gaps in the port, none of
which the gate could see:

  * the `admissibility` lane was recorded as vacuous "because the lean obligation
    has no precondition". That reason is wrong — the total-carrier analogue is
    satisfiability at an F2P-shaped input — and the case is expressible here. It
    is landed as `admiss-fshaped-input` and verifies.
  * both positive controls built their names field out of `filteredNames`, the
    term the postcondition's own RHS names, so neither reshape was far from the
    spec. `pos-structural-recursion` adds one whose discovery step is an
    independent recursion the proof must relate to `filteredNames` by induction.
  * every migrated-sub-clause rival attacked the boolean's SHAPE while leaving
    its dependence on the FILTERED list intact, and each of their witnesses sat
    at an input where the filter is a no-op. `migrated-from-raw-entries` attacks
    that coupling.

The audit also independently re-derived the two omission claims below (frame
mutation, divergence) with real builds and confirms both.

DEFENDED SURFACE
----------------
The modeled function classifies an application's migrations package and reports
the migration files discovered in it:

    implementation_migration_module_status
        (hasFile hasPath ignoreNoMigrations : Bool)
        (entries : List (String × Bool)) : MigrationModuleStatus

pinned by the postcondition, which has TWO independent top-level clauses over
the input binders `hasFile`, `hasPath`, `ignoreNoMigrations`, `entries` (each
entry a `(name, isSubpackage)` pair):

  * NOT-A-PACKAGE (`hasPath = false`): the result is unmigrated and carries NO
    files — `result.migrated = false ∧ result.names = []`.
  * PACKAGE (`hasPath = true`): the discovered files are exactly
    `filteredNames entries` (non-subpackage entries whose name does not begin
    with `_`/`~`, in order), AND the package is migrated iff at least one file
    was discovered OR the treat-as-migrated flag is set —
    `result.migrated = ((! (filteredNames entries).isEmpty) || ignoreNoMigrations)`.

The flavour flag `hasFile` is an INPUT but does NOT appear on either RHS: the
classification is independent of it, which is the load-bearing fact of this fix.
`correct_*` quantifies over all `hasFile`, so any rival that consults it is
refutable.

The carrier is FULLY TRANSPARENT — `validMigrationName` / `filteredNames` are
concrete `def`s, there is no opaque callee — so every rival is refuted by
`decide` at a concrete input; no carrier conditioning is needed and no witness
binds a hypothesis (nothing to be jointly inconsistent).

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
The nagini surface returned a single INT code (0/1); this bundle models the
richer functional core, so it additionally pins the discovered-file LIST
(`result.names = filteredNames entries`) and the not-a-package clause. The four
nagini value-level rivals port directly; seven new rivals attack the structure
nagini did not model — the int-only nagini surface had no discovered-file list, so
its membership, ORDER, multiplicity and per-prefix name guards are all carrier-new
obligations with no upstream case to port.

  * nagini `partial-domain-marker-dependence` (B1 pre-patch) -> `marker-dependence`
    — reintroduces the dropped flavour guard: unmigrated when the flavour flag is
    off, even for a package that exposes a search path and holds a migration
    file. Attacks the PACKAGE clause via `hasFile`-independence; the ONLY rival
    that varies `hasFile=false`.
  * nagini `partial-domain-empty-as-migrated` (B2 pre-patch) -> `empty-as-migrated`
    — a package exposing a search path is migrated UNCONDITIONALLY, ignoring the
    discovered-file count and the flag. Attacks the migrated sub-clause on the
    empty-non-tolerated sub-domain.
  * nagini `partial-domain-drop-tolerate` -> `drop-tolerate` — drops the
    treat-as-migrated disjunct. Attacks the migrated sub-clause on the
    empty-BUT-tolerated sub-domain; the rival that varies `ignoreNoMigrations=true`.
  * nagini `inverted-codes-supporting` -> `inverted-migrated` — negates the
    migrated boolean. Supporting mechanical mirror of the migrated sub-clause.
  * added `not-a-package-migrated` — on `hasPath=false` reports the flag as the
    classification instead of unconditional unmigrated. The ONLY rival that
    varies `hasPath=false`; attacks the NOT-A-PACKAGE clause, which nagini's
    int-only surface did not separately model.
  * added `keep-subpackages` — the file filter drops the not-a-subpackage guard,
    so a discovered subpackage is reported as a migration file. Attacks the
    file-LIST clause (`names = filteredNames`); the rival that varies an entry's
    isSubpackage=true.
  * added `keep-dunder-names` — the file filter drops the admissible-name guard,
    so an entry whose name begins with `_`/`~` is reported. Attacks the file-LIST
    clause on the entry-NAME binder.
  * added `reverse-discovery-order` — accumulates discovered names by PREPENDING
    instead of appending, so the reported list is the reverse of the discovery
    order. The `names = filteredNames entries` clause pins ORDER, not just
    membership; this is the only rival whose witness needs a TWO-entry list (a
    one-entry list is its own reverse, so every other file-LIST rival leaves the
    order component untested).
  * added `keep-last-discovered-only` — overwrites the accumulator each time a
    file is discovered instead of extending it, so only the LAST discovered name
    survives. Attacks the file-LIST clause on multiplicity/accumulation: every
    other rival is refutable at a one-entry list, where "keep the last" and "keep
    all" agree.
  * added `partial-name-guard` — the admissible-name guard rejects only `_` and
    forgets `~`. A strictly WEAKER near-miss than `keep-dunder-names` (which
    drops the guard entirely): it is correct on every `_`-prefixed name and
    diverges only on the `~` branch of `validMigrationName`, which no other rival
    reaches.

  * nagini positive controls `pos-reorder-branch` / `pos-direct-oracle` ->
    `pos-functional-form` / `pos-commuted-or` — two structurally different CORRECT
    impls (a pure functional if/else expression, and the same with the migrated
    disjunction commuted), each with `correct_*` re-closed for the new shape. If
    either fails to verify the spec is over-fit to the imperative shape =>
    SPEC-TOO-STRONG.
  * nagini `admiss-fshaped-input` -> `admiss-fshaped-input`. It PORTS; an earlier
    revision of this manifest recorded it as vacuous because the lean obligation
    carries no precondition hypothesis, and that reason was WRONG. The analogue
    on a total carrier is not "is the precondition too strong" but "is the
    obligation SATISFIABLE at exactly a normal, F2P-shaped input" — which a
    positive that discharges `problem_spec_…` at that concrete input BY
    EVALUATION, as a `have`, before closing the frozen obligation verbatim, tests
    directly. Landed below; it verifies. If it could not, the modeled behavior
    would be unsatisfiable at a normal input, the total-carrier form of
    PRECOND-TOO-STRONG.
  * nagini `frame-mutation-append-names` (fractional-permission mutation of the
    read-only input) is VACUOUS here, and the reason is MEASURED rather than
    asserted: an impl that rebinds `entries` into a local `let mut`, appends an
    entry, and then erases it again VERIFIES against the frozen obligation
    (built: exit 0). `List` is passed by value and Lean has no aliasing, so a
    write to a local copy is unobservable to the postcondition — there is no
    permission clause left to violate, hence no rejection to attribute. The
    frame concern it guarded — that the reported set is not corrupted — is
    instead pinned STRUCTURALLY by `result.names = filteredNames entries`
    (membership AND order AND multiplicity), which `keep-subpackages`,
    `keep-dunder-names`, `partial-name-guard`, `reverse-discovery-order` and
    `keep-last-discovered-only` attack directly.
  * no `diverge-*`/`nonterm-*` case exists in the nagini sibling, and it would be
    vacuous regardless: `implementation_*` is a total Lean `def`, so a diverging
    implementation cannot be written.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it
    (nagini's meta.axioms == [], nothing opaque is consumed here either).

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1).
"""
from pathlib import Path

INSTANCE = "django__django-11141"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region (and, for positives,
# the proof body) of Solution.lean, each verified unique across the whole file.
# ---------------------------------------------------------------------------

# The not-a-package early return (unique in the file).
_NOPATH_BLOCK = (
    "  if !hasPath then\n"
    "    return { migrated := false, names := [] }"
)

# The per-entry file filter condition (unique in the file).
_FILTER_COND = "    if (!entry.2) && validMigrationName entry.1 then"

# The migrated-classification line (unique in the file).
_MIGRATED_LINE = "  let migrated := (!names.isEmpty) || ignoreNoMigrations"

# The accumulator update inside the discovery loop (unique in the file).
_ACCUM_LINE = "      names := names ++ [entry.1]"

# The whole gold impl body (Id.run do block), including the intent comment —
# replaced wholesale by each positive control.
_GOLD_IMPL = (
    "def implementation_migration_module_status\n"
    "    (hasFile hasPath ignoreNoMigrations : Bool)\n"
    "    (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do\n"
    "  -- The package flavour (`hasFile`) is deliberately not consulted.\n"
    "  if !hasPath then\n"
    "    return { migrated := false, names := [] }\n"
    "  let mut names : List String := []\n"
    "  for entry in entries do\n"
    "    if (!entry.2) && validMigrationName entry.1 then\n"
    "      names := names ++ [entry.1]\n"
    "  let migrated := (!names.isEmpty) || ignoreNoMigrations\n"
    "  return { migrated := migrated, names := names }"
)

# The gold proof body, replaced wholesale by each positive.
_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"

# The frozen proof's `intro` line (unique in the file, wholly inside the proof
# region) — so the admissibility positive can PREPEND a ground `have` without
# touching the theorem STATEMENT or the spec view.
_P_INTRO = "  intro hasFile hasPath ignoreNoMigrations entries"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers with
    `new_proof_body`. The `theorem correct_*` STATEMENT is re-emitted
    byte-identically inside `new_proof_body`; only the tactic body (and dropped
    helper lemmas) change, which variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# The theorem statement, re-emitted verbatim so the obligation survives.
_THM_STMT = (
    "theorem correct_migration_module_status :\n"
    "    ∀ (hasFile hasPath ignoreNoMigrations : Bool) (entries : List (String × Bool)),\n"
    "      problem_spec_migration_module_status hasFile hasPath ignoreNoMigrations entries\n"
    "        (implementation_migration_module_status hasFile hasPath ignoreNoMigrations entries) := by"
)

# (pos-functional-form) A structurally different CORRECT impl: a pure functional
# if/else expression (no `Id.run do`, no `for`/`mut`) whose body is exactly the
# reference outcome. The proof discharges each clause by `simp` on the guard.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_migration_module_status\n"
    "    (hasFile hasPath ignoreNoMigrations : Bool)\n"
    "    (entries : List (String × Bool)) : MigrationModuleStatus :=\n"
    "  if hasPath then\n"
    "    { migrated := (! (filteredNames entries).isEmpty) || ignoreNoMigrations,\n"
    "      names := filteredNames entries }\n"
    "  else\n"
    "    { migrated := false, names := [] }"
)
_POS_FUNCTIONAL_PROOF = (
    _THM_STMT + "\n"
    "  intro hasFile hasPath ignoreNoMigrations entries\n"
    "  refine ⟨fun hp => ?_, fun hp => ?_⟩\n"
    "  · simp [implementation_migration_module_status, hp]\n"
    "  · simp [implementation_migration_module_status, hp]\n"
)
_POS_FUNCTIONAL = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUNCTIONAL_IMPL),
    _POS_FUNCTIONAL_PROOF,
)

# (pos-commuted-or) The same functional impl but with the migrated disjunction
# COMMUTED (`ignoreNoMigrations || …` instead of `… || ignoreNoMigrations`).
# Observationally identical; the proof closes the migrated clause modulo
# `Bool.or_comm`. If it fails to verify the spec is over-fit to the operand
# order of a commutative `||` => SPEC-TOO-STRONG.
_POS_COMMUTED_IMPL = (
    "def implementation_migration_module_status\n"
    "    (hasFile hasPath ignoreNoMigrations : Bool)\n"
    "    (entries : List (String × Bool)) : MigrationModuleStatus :=\n"
    "  if hasPath then\n"
    "    { migrated := ignoreNoMigrations || (! (filteredNames entries).isEmpty),\n"
    "      names := filteredNames entries }\n"
    "  else\n"
    "    { migrated := false, names := [] }"
)
_POS_COMMUTED_PROOF = (
    _THM_STMT + "\n"
    "  intro hasFile hasPath ignoreNoMigrations entries\n"
    "  refine ⟨fun hp => ?_, fun hp => ?_⟩\n"
    "  · simp [implementation_migration_module_status, hp]\n"
    "  · simp [implementation_migration_module_status, hp, Bool.or_comm]\n"
)
_POS_COMMUTED = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_COMMUTED_IMPL),
    _POS_COMMUTED_PROOF,
)

# (pos-structural-recursion) A third CORRECT impl whose discovery step is an
# explicit structurally-recursive helper (`discover`, a `match` on the entry
# list) rather than the frozen `for`/`mut` accumulation OR the `filteredNames`
# projection the two positives above reuse. This is the reshape that matters
# most: the other two positives both build their names field FROM
# `filteredNames`, the very term the postcondition's RHS names, so they are
# definitionally close to the spec. `discover` is a genuinely independent
# recursion, and the proof has to EARN `discover entries = filteredNames entries`
# by induction before the clause closes. If it failed, the spec would reject a
# faithful correct impl => SPEC-TOO-STRONG.
_POS_RECURSION_IMPL = (
    "def discover (entries : List (String × Bool)) : List String :=\n"
    "  match entries with\n"
    "  | [] => []\n"
    "  | p :: rest =>\n"
    "    if (!p.2) && validMigrationName p.1 then p.1 :: discover rest else discover rest\n"
    "\n"
    "def implementation_migration_module_status\n"
    "    (hasFile hasPath ignoreNoMigrations : Bool)\n"
    "    (entries : List (String × Bool)) : MigrationModuleStatus :=\n"
    "  if hasPath then\n"
    "    { migrated := ignoreNoMigrations || (! (discover entries).isEmpty),\n"
    "      names := discover entries }\n"
    "  else\n"
    "    { migrated := false, names := [] }"
)
_POS_RECURSION_PROOF = (
    _THM_STMT + "\n"
    "  intro hasFile hasPath ignoreNoMigrations entries\n"
    "  have hd : discover entries = filteredNames entries := by\n"
    "    induction entries with\n"
    "    | nil => simp [discover, filteredNames]\n"
    "    | cons hd tl ih =>\n"
    "      by_cases hc : ((!hd.2) && validMigrationName hd.1) = true\n"
    "      · simp [discover, hc, filteredNames, List.filter_cons, ih]\n"
    "      · simp [discover, hc, filteredNames, List.filter_cons, ih]\n"
    "  refine ⟨fun hp => ?_, fun hp => ?_⟩\n"
    "  · simp [implementation_migration_module_status, hp]\n"
    "  · simp [implementation_migration_module_status, hp, hd, Bool.or_comm]\n"
)
_POS_RECURSION = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_RECURSION_IMPL),
    _POS_RECURSION_PROOF,
)


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================

# (admiss-fshaped-input) Ports nagini's `admiss-fshaped-input`. The frozen
# obligation carries no precondition hypothesis, so "the precondition rejects a
# legitimate input" has no literal analogue; the analogue that DOES exist on a
# total carrier is the obligation being UNSATISFIABLE at exactly a normal,
# F2P-shaped input. So this case discharges `problem_spec_…` at two concrete
# normal inputs BY EVALUATION, as `have`s, and then closes the frozen obligation
# verbatim — the frozen proof body is untouched and follows.
#
#   * the F2P-shaped input: a package that exposes a search path but has NO
#     regular-file flavour marker (`hasFile = false`, an implicit namespace
#     package) holding one discovered migration file, with the treat-as-migrated
#     flag OFF. Both spec clauses must be satisfiable there — this is the exact
#     shape the whole battery's `hasFile`-independence argument rests on, so if
#     the obligation were unsatisfiable at it, every reject case's refutation
#     would be attributing to a clause no impl can meet.
#   * the complementary normal input: a package exposing a search path with no
#     discovered files and the flag OFF (unmigrated, no files).
#
# Nothing is assumed: no new declaration, the theorem STATEMENT stays
# byte-identical, and the ground instances are `have`s prepended inside the
# existing tactic body. `decide` closes them because the carrier is transparent.
_ADMISS = _swap(
    _BASE, _P_INTRO,
    "  -- Ground the obligation at a normal, F2P-shaped input BEFORE closing it\n"
    "  -- in general: search path PRESENT, flavour marker ABSENT, one discovered\n"
    "  -- migration file, treat-as-migrated flag OFF.\n"
    "  have _ground_f2p : problem_spec_migration_module_status\n"
    "      false true false [(\"0001_initial\", false)]\n"
    "      (implementation_migration_module_status\n"
    "        false true false [(\"0001_initial\", false)]) := by\n"
    "    unfold problem_spec_migration_module_status "
    "implementation_migration_module_status\n"
    "    decide\n"
    "  -- and at the complementary normal input: a package exposing a search\n"
    "  -- path with no discovered files and the flag OFF.\n"
    "  have _ground_empty : problem_spec_migration_module_status\n"
    "      true true false []\n"
    "      (implementation_migration_module_status\n"
    "        true true false []) := by\n"
    "    unfold problem_spec_migration_module_status "
    "implementation_migration_module_status\n"
    "    decide\n"
    + _P_INTRO)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (marker-dependence) B1 PRE-PATCH: reintroduce the dropped flavour guard —
# unmigrated (no files) whenever the flavour flag is off, before consulting the
# search path or discovered files. Correct on every input WITH the flavour flag;
# wrong on the sub-domain hasFile=false & hasPath=true, where the postcondition
# (which omits hasFile) requires the normal package classification.
_RIVAL_MARKER = _swap(
    _BASE, _NOPATH_BLOCK,
    "  if !hasFile then\n"
    "    return { migrated := false, names := [] }\n"
    "  if !hasPath then\n"
    "    return { migrated := false, names := [] }",
)

# (empty-as-migrated) B2 PRE-PATCH: a package exposing a search path is migrated
# UNCONDITIONALLY, ignoring the discovered-file count and the flag. Wrong on the
# empty-non-tolerated sub-domain (migrated must be false there).
_RIVAL_EMPTY = _swap(_BASE, _MIGRATED_LINE, "  let migrated := true")

# (drop-tolerate) Drop the treat-as-migrated disjunct: migrated iff files were
# discovered. Wrong on the empty-BUT-tolerated sub-domain (flag set, no files).
_RIVAL_DROPTOL = _swap(_BASE, _MIGRATED_LINE, "  let migrated := !names.isEmpty")

# (inverted-migrated) Supporting mechanical mirror: negate the migrated boolean.
# Diverges on the migrated sub-clause for essentially every input.
_RIVAL_INVERTED = _swap(
    _BASE, _MIGRATED_LINE,
    "  let migrated := !((!names.isEmpty) || ignoreNoMigrations)")

# (not-a-package-migrated) On not-a-package (hasPath=false), report the flag as
# the classification instead of unconditional unmigrated. Wrong on the
# NOT-A-PACKAGE clause whenever the flag is set (migrated must be false).
_RIVAL_NOPATH = _swap(
    _BASE, _NOPATH_BLOCK,
    "  if !hasPath then\n"
    "    return { migrated := ignoreNoMigrations, names := [] }",
)

# (keep-subpackages) Drop the not-a-subpackage guard from the file filter, so a
# discovered SUBPACKAGE with an admissible name is reported as a migration file.
# Wrong on the file-LIST clause for any entry with isSubpackage=true.
_RIVAL_SUBPKG = _swap(
    _BASE, _FILTER_COND, "    if validMigrationName entry.1 then")

# (keep-dunder-names) Drop the admissible-name guard from the file filter, so an
# entry whose name begins with `_`/`~` is reported. Wrong on the file-LIST
# clause for any such entry.
_RIVAL_DUNDER = _swap(_BASE, _FILTER_COND, "    if !entry.2 then")

# (reverse-discovery-order) Accumulate by PREPENDING, so the reported list is the
# reverse of the discovery order. Membership and multiplicity are untouched: only
# the ORDER component of `names = filteredNames entries` is violated, and only on
# a list with at least two discovered files.
_RIVAL_REVORDER = _swap(_BASE, _ACCUM_LINE, "      names := [entry.1] ++ names")

# (keep-last-discovered-only) Overwrite the accumulator instead of extending it,
# so only the LAST discovered file survives. Attacks the MULTIPLICITY component
# of the file-LIST clause; agrees with gold on every list with ≤1 discovered file.
_RIVAL_KEEPLAST = _swap(_BASE, _ACCUM_LINE, "      names := [entry.1]")

# (partial-name-guard) The admissible-name guard rejects only `_` and forgets
# `~`. Strictly WEAKER near-miss than keep-dunder-names: correct on every
# `_`-prefixed name, wrong only on the `~` branch of validMigrationName.
_RIVAL_PARTIALNAME = _swap(
    _BASE, _FILTER_COND,
    "    if (!entry.2) && (entry.1.toList.headD '_' != '_') then")

# (migrated-from-raw-entries) The classification is computed from whether ANY
# entry was discovered at all, instead of from whether any entry survived the
# file filter. Correct on every input where the filter is a no-op (all entries
# admissible, or none present at all) — which is EVERY witness the other rivals
# use except the two name-guard ones — and wrong exactly where entries exist but
# all are filtered out: the migrated sub-clause reads `filteredNames`, not
# `entries`. No other rival attacks WHICH LIST the migrated boolean is derived
# from; they all attack the boolean's shape.
_RIVAL_RAWCOUNT = _swap(
    _BASE, _MIGRATED_LINE,
    "  let migrated := (!entries.isEmpty) || ignoreNoMigrations")

# (not-a-package-names) On not-a-package (hasPath=false), report the filtered
# entries as discovered files instead of the empty list. Wrong on the file-LIST
# component of the NOT-A-PACKAGE clause (`names = []`), which every other rival
# leaves satisfied.
_RIVAL_NOPATH_NAMES = _swap(
    _BASE, _NOPATH_BLOCK,
    "  if !hasPath then\n"
    "    return { migrated := false, names := filteredNames entries }",
)


# --- witnesses (checked with obligation removed) ---------------------------
# Each negates the spec predicate at one concrete input; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis.

def _wit(args: str) -> str:
    return (
        "example : ¬ problem_spec_migration_module_status\n"
        f"    {args}\n"
        "    (implementation_migration_module_status\n"
        f"      {args}) := by\n"
        "  unfold problem_spec_migration_module_status implementation_migration_module_status\n"
        "  decide"
    )


# marker: flavour OFF, a package with one migration file. gold => migrated,
# names=["a"]; rival => unmigrated, names=[]. The ONLY witness at hasFile=false
# (that IS its discriminator); every other witness holds hasFile=true so a rival
# mishandling the flavour flag in the other direction would still be caught.
_WIT_MARKER = _wit('false true false [("a", false)]')
# empty: package, no entries, flag off. gold => migrated=false; rival => true.
_WIT_EMPTY = _wit("true true false []")
# drop-tolerate: package, no entries, flag ON. gold => migrated=true; rival =>
# false. Varies ignoreNoMigrations=true.
_WIT_DROPTOL = _wit("true true true []")
# inverted: package with a migration file, flag off. gold => migrated=true;
# rival => false.
_WIT_INVERTED = _wit('true true false [("b", false)]')
# not-a-package: no search path, flag ON. gold => migrated=false; rival =>
# true. Varies hasPath=false (the NOT-A-PACKAGE migrated sub-clause).
_WIT_NOPATH = _wit("true false true []")
# keep-subpackages: a subpackage entry with an admissible name. gold excludes it
# (names=[]); rival keeps it (names=["a"]). Varies an entry's isSubpackage=true.
_WIT_SUBPKG = _wit('true true false [("a", true)]')
# keep-dunder-names: a non-subpackage entry named "_a". gold excludes it
# (names=[]); rival keeps it (names=["_a"]). Varies the entry-name binder.
_WIT_DUNDER = _wit('true true false [("_a", false)]')
# reverse-discovery-order: TWO admissible non-subpackage entries. gold =>
# names=["a","b"] (discovery order); rival => ["b","a"]. The only witness whose
# entries list has length 2 — a singleton is its own reverse, so this is the sole
# case that tests the ORDER component of the file-LIST clause.
_WIT_REVORDER = _wit('true true false [("a", false), ("b", false)]')
# keep-last-discovered-only: TWO admissible entries. gold => names=["a","b"];
# rival => ["b"] (only the last survives). Tests MULTIPLICITY/accumulation.
_WIT_KEEPLAST = _wit('true true false [("a", false), ("b", false)]')
# partial-name-guard: a non-subpackage entry named "~a" — the `~` branch of the
# admissible-name guard, which no other witness reaches. gold excludes it
# (names=[], migrated=false); rival keeps it (names=["~a"], migrated=true).
_WIT_PARTIALNAME = _wit('true true false [("~a", false)]')
# migrated-from-raw-entries: a package holding ONE entry that the file filter
# excludes (name begins with `_`), flag off. gold => no file was discovered, so
# migrated=false; rival counts the raw entry and reports migrated=true. The names
# clause agrees on both sides, so the refutation lands purely on the migrated
# sub-clause's dependence on `filteredNames` rather than on `entries`.
_WIT_RAWCOUNT = _wit('true true false [("_a", false)]')
# not-a-package-names: no search path, a non-subpackage admissible entry present.
# gold => names=[]; rival => names=["a"]. Attacks the file-LIST component of the
# NOT-A-PACKAGE clause.
_WIT_NOPATH_NAMES = _wit('true false false [("a", false)]')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally-different but correct impl: a pure functional "
                  "if/else expression (no imperative do-block / for / mut) whose "
                  "branches are the reference outcomes, so `correct_` re-closes by "
                  "`simp` on the search-path guard. The carrier is transparent, so "
                  "there is no oracle to echo; this stands as a soundness positive "
                  "of a different impl form. If it fails to verify the spec is "
                  "over-fit to the imperative shape => SPEC-TOO-STRONG."},
    {"id": "pos-commuted-or", "kind": "soundness", "expect": "verify",
     "module": _POS_COMMUTED,
     "rationale": "a second correct impl with the migrated disjunction COMMUTED "
                  "(`flag || hasFiles` vs `hasFiles || flag`). Observationally "
                  "identical; the migrated clause closes modulo `Bool.or_comm`. If "
                  "it fails to verify the spec is over-fit to the operand order of "
                  "a commutative `||` => SPEC-TOO-STRONG."},
    {"id": "pos-structural-recursion", "kind": "soundness", "expect": "verify",
     "module": _POS_RECURSION,
     "rationale": "a third correct impl whose discovery step is an explicit "
                  "structurally-recursive helper (`discover`, a match on the entry "
                  "list) instead of the frozen for/mut accumulation. This is the "
                  "load-bearing positive: the other two both build their names "
                  "field FROM `filteredNames`, the term the postcondition's own RHS "
                  "names, so they are definitionally close to the spec and could "
                  "pass while testing little. `discover` is an independent "
                  "recursion, so the proof must EARN `discover entries = "
                  "filteredNames entries` by induction before the file-LIST clause "
                  "closes. If it failed the spec would reject a faithful correct "
                  "impl => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-fshaped-input", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "ports nagini's admiss-fshaped-input. The frozen obligation has "
                  "no precondition hypothesis, so PRECOND-TOO-STRONG has no literal "
                  "analogue; the analogue on a total carrier is the obligation being "
                  "UNSATISFIABLE at exactly a normal, F2P-shaped input. So the "
                  "obligation is discharged at two concrete normal inputs BY "
                  "EVALUATION, as `have`s, before the frozen obligation is closed "
                  "verbatim: (a) search path PRESENT, flavour marker ABSENT, one "
                  "discovered migration file, flag OFF — the very shape the whole "
                  "battery's hasFile-independence argument rests on, so if the "
                  "obligation were unsatisfiable there every reject case would be "
                  "attributing to a clause no impl can meet; and (b) search path "
                  "PRESENT, no discovered files, flag OFF. Nothing is assumed: no "
                  "new declaration, statement byte-identical, ground instances are "
                  "`have`s inside the existing tactic body."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "marker-dependence", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MARKER, "witness": _WIT_MARKER,
     "refinement": "this is the B1 pre-patch: keeping the flavour guard sends an "
                   "implicit namespace package (flavour flag off) that holds a "
                   "migration file into the unmigrated set, so the file is never "
                   "discovered and the forward plan cannot be built — the F2P "
                   "'migration directories without an __init__.py file are loaded' "
                   "FAILS. So a faithful patch keeping the guard would NOT resolve, "
                   "and a rival that verifies is a true "
                   "verify-does-not-imply-resolve break.",
     "rationale": "attacks the PACKAGE clause via hasFile-independence: the spec "
                  "omits `hasFile` from both RHS, so on (hasFile=false, hasPath=true, "
                  "one migration file) the rival returns unmigrated/[] where the "
                  "postcondition requires migrated/[\"a\"]. The ONLY rival that varies "
                  "hasFile=false. Built both ways (rival 0, gold 1)."},
    {"id": "empty-as-migrated", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY, "witness": _WIT_EMPTY,
     "refinement": "this is the B2 pre-patch: the unconditional add classifies an "
                   "empty package as migrated; the P2P test that an empty migrations "
                   "namespace must NOT be treated as migrated regresses => it would "
                   "NOT resolve.",
     "rationale": "attacks the migrated sub-clause of the PACKAGE clause: on "
                  "(hasPath=true, no entries, flag off) the rival returns "
                  "migrated=true where the postcondition requires false. Built both "
                  "ways (rival 0, gold 1)."},
    {"id": "drop-tolerate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROPTOL, "witness": _WIT_DROPTOL,
     "refinement": "a real patch dropping the treat-as-migrated disjunct classifies "
                   "a tolerate-empty (ignore-no-migrations) package as unmigrated, "
                   "contradicting the documented flag contract that the P2P tests "
                   "bracket => it would NOT resolve.",
     "rationale": "attacks the migrated sub-clause on the empty-BUT-tolerated "
                  "sub-domain: on (hasPath=true, no entries, flag ON) the rival "
                  "returns migrated=false where the postcondition requires true. The "
                  "rival that varies ignoreNoMigrations=true. Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "inverted-migrated", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERTED, "witness": _WIT_INVERTED,
     "refinement": "negating the classification adds every package to the wrong "
                   "set, so essentially all loader F2P+P2P tests fail => it would "
                   "NOT resolve. (Supporting near-miss; carries a real refinement "
                   "but does not replace the reasoned partial-domain attacks.)",
     "rationale": "SUPPORTING mechanical mirror of the migrated sub-clause: negates "
                  "the migrated boolean. Witness at (hasPath=true, one migration "
                  "file, flag off): gold => migrated=true, rival => false. Built both "
                  "ways (rival 0, gold 1)."},
    {"id": "not-a-package-migrated", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOPATH, "witness": _WIT_NOPATH,
     "refinement": "a real patch that let the treat-as-migrated flag classify a "
                   "NON-package (a plain module, no search path) as migrated would "
                   "try to load migrations from a module that has no __path__; the "
                   "P2P test that a non-package module is unmigrated regresses => it "
                   "would NOT resolve.",
     "rationale": "attacks the NOT-A-PACKAGE clause (`hasPath=false → migrated=false "
                  "∧ names=[]`), which nagini's int-only surface did not separately "
                  "model. On (hasPath=false, flag ON) the rival returns "
                  "migrated=true where the postcondition requires false. The ONLY "
                  "rival that varies hasPath=false. Built both ways (rival 0, "
                  "gold 1)."},
    {"id": "keep-subpackages", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SUBPKG, "witness": _WIT_SUBPKG,
     "refinement": "a real patch that dropped the not-a-subpackage guard from file "
                   "discovery would treat a nested subpackage as a migration file "
                   "and try to import it as a migration; the P2P discovery tests that "
                   "pin the exact discovered file list regress => it would NOT "
                   "resolve.",
     "rationale": "attacks the file-LIST clause (`names = filteredNames entries`), "
                  "structurally pinning the discovered set — the analogue of nagini's "
                  "read-only-input frame obligation. On a single subpackage entry "
                  "with an admissible name the rival reports it (names=[\"a\"]) where "
                  "the spec excludes it (names=[]). Varies an entry's "
                  "isSubpackage=true. Built both ways (rival 0, gold 1)."},
    {"id": "keep-dunder-names", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DUNDER, "witness": _WIT_DUNDER,
     "refinement": "a real patch that dropped the admissible-name guard would report "
                   "files whose names begin with `_`/`~` (e.g. `__init__`) as "
                   "migrations; the P2P test that underscore/tilde/dot-prefixed files "
                   "are NOT loaded regresses => it would NOT resolve.",
     "rationale": "attacks the file-LIST clause on the entry-NAME binder: on a "
                  "non-subpackage entry named `_a` the rival reports it "
                  "(names=[\"_a\"]) where the spec excludes it (names=[]). The rival "
                  "that varies the entry name (leading underscore). Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "reverse-discovery-order", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVORDER, "witness": _WIT_REVORDER,
     "refinement": "a real patch that built the discovered-file list in reverse "
                   "would apply an app's migrations in the wrong sequence, since the "
                   "discovered order is what the dependency plan is built from; the "
                   "P2P plan/ordering tests (first, run_before, prefix and "
                   "squashed-plan cases) regress => it would NOT resolve.",
     "rationale": "attacks the ORDER component of the file-LIST clause "
                  "(`names = filteredNames entries` is a LIST equality, so it pins "
                  "sequence and not merely membership). On two admissible entries "
                  "the rival returns names=[\"b\",\"a\"] where the postcondition "
                  "requires [\"a\",\"b\"]. The ONLY case whose witness uses a "
                  "two-entry list — every other file-LIST rival is refuted at a "
                  "singleton, which is its own reverse, so order went untested "
                  "before this case. Built both ways (rival 0, gold 1)."},
    {"id": "keep-last-discovered-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_KEEPLAST, "witness": _WIT_KEEPLAST,
     "refinement": "a real patch that overwrote the discovered set instead of "
                   "accumulating into it would report a single migration per app and "
                   "silently drop the rest, so the multi-migration load and "
                   "squashed-plan P2P tests regress => it would NOT resolve.",
     "rationale": "attacks the MULTIPLICITY/accumulation component of the file-LIST "
                  "clause: the rival keeps only the last discovered file, so on two "
                  "admissible entries it returns names=[\"b\"] where the "
                  "postcondition requires [\"a\",\"b\"]. Agrees with gold on every "
                  "input with at most one discovered file, which is exactly the "
                  "shape every pre-existing file-LIST witness used. Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "partial-name-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIALNAME, "witness": _WIT_PARTIALNAME,
     "refinement": "a real patch whose name guard excluded only one of the two "
                   "reserved prefixes would load a tilde-prefixed editor backup as a "
                   "migration; the P2P test that underscore/tilde/dot-prefixed files "
                   "are not loaded regresses => it would NOT resolve.",
     "rationale": "a strictly WEAKER near-miss than keep-dunder-names, which drops "
                  "the admissible-name guard outright: this rival keeps the `_` half "
                  "and forgets the `~` half, so it is correct on every "
                  "underscore-prefixed name and diverges only on the `~` branch of "
                  "`validMigrationName` — a branch no other rival's witness reaches. "
                  "On a non-subpackage entry named `~a` the rival reports it "
                  "(names=[\"~a\"], migrated=true) where the spec excludes it "
                  "(names=[], migrated=false). Built both ways (rival 0, gold 1)."},
    {"id": "migrated-from-raw-entries", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RAWCOUNT, "witness": _WIT_RAWCOUNT,
     "refinement": "a real patch that classified an app by whether its migrations "
                   "package held ANY entry, rather than by whether any entry "
                   "survived the name/subpackage filter, would treat a package "
                   "holding only excluded entries (an `__init__` module, an editor "
                   "backup, a nested subpackage) as migrated and then find no "
                   "migration to load; the P2P tests that such a package is "
                   "unmigrated regress => it would NOT resolve.",
     "rationale": "attacks WHICH LIST the migrated sub-clause is derived from — "
                  "`filteredNames entries`, not `entries`. Every other rival "
                  "attacks the SHAPE of the migrated boolean (unconditional, "
                  "negated, disjunct dropped) while leaving its dependence on the "
                  "FILTERED list intact, and each of their witnesses is at an input "
                  "where the filter is a no-op, so this coupling went untested. On "
                  "(hasPath=true, one entry named `_a`, flag off) the rival counts "
                  "the raw entry and returns migrated=true where the postcondition "
                  "requires false; the names clause agrees on both sides, so the "
                  "refutation lands purely on the migrated sub-clause. Built both "
                  "ways (rival 0, gold 1)."},
    {"id": "not-a-package-names", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOPATH_NAMES, "witness": _WIT_NOPATH_NAMES,
     "refinement": "a real patch that reported discovered files for a NON-package "
                   "would attribute migration files to a module with no migrations "
                   "directory; the P2P test that a non-package module contributes no "
                   "migrations regresses => it would NOT resolve.",
     "rationale": "attacks the file-LIST component of the NOT-A-PACKAGE clause "
                  "(`hasPath = false → result.migrated = false ∧ result.names = []`), "
                  "which every other rival leaves satisfied. On (hasPath=false, one "
                  "admissible non-subpackage entry) the rival returns names=[\"a\"] "
                  "where the postcondition requires result.names = []. Built both "
                  "ways (rival 0, gold 1)."},
]

# No @ContractOnly axioms and nothing opaque is consumed (nagini meta.axioms ==
# [], deep_model_references == []); the classification and file filter are
# modeled deeply over concrete booleans and a List (String × Bool). The axiom
# lane is G-AX's job and this gate ignores it.
AXIOM_TESTS = []
