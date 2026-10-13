# properties.py — G-PBT falsification battery for django__django-14376 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   This bundle models TWO small, independent purely-functional behaviors:
#
#   (A) dbArg (optDatabase optDb : Option String) (name : String) -> Option String
#       The trailing database-name argument. A THREE-LEVEL precedence selection over
#       optional sources — primary option if its key is PRESENT, else fallback option
#       if present, else the configured name — followed by an emptiness test that
#       drops an empty chosen value. The single postcondition clause pins the whole
#       output:
#         result = (let chosen := optDatabase.getD (optDb.getD name);
#                   if chosen = "" then none else some chosen)
#       Presence is `Option` (`some ""` is still chosen and short-circuits — it does
#       NOT fall through), the emptiness test decides whether a trailing token exists.
#       This is the clause the nagini battery attacked; its (P1) precedence and (P2)
#       append-iff-nonempty split into the two structural sub-behaviours below.
#
#   (B) connParams (name password : Option String) -> List (String × String)
#       The connection-parameter mapping entries for the database name and password.
#       The non-empty configured name is carried under the key "database", the
#       non-empty configured password under the key "password", in that order:
#         result = (name-entry-under-"database") ++ (password-entry-under-"password")
#       Each entry is present exactly when its setting is a non-empty value.
#       The nagini sibling did NOT model this second file's behavior at all (its
#       carrier abstracted only the client.py selection); it is modeled here, so it
#       gets its own defend + attack lane below.
#
#   Both specs are TRANSPARENT (Option.getD, string emptiness, list append over
#   literal keys/values) — there is no opaque callee and no answer-key oracle, so
#   witnesses need no conditioning on the carrier: `decide` computes both specs at any
#   literal input after unfolding the `Id.run do` wrapper.
#
# The dbArg clause pins several INDEPENDENT sub-behaviours a rival attacks one at a
# time (carried over from nagini W1/W2/W3/W4/W5):
#   (a) PRIMARY precedence: a present primary option wins over a present fallback
#       (the F2P discriminator — both keys present);
#   (b) PRESENT-EMPTY short-circuit: a present-but-empty primary/fallback is chosen
#       (does not fall through to the lower-precedence source);
#   (c) APPEND-iff-nonempty: a trailing token exists exactly when the chosen value is
#       non-empty;
#   (d) VALUE fidelity: the trailing token equals the FULL chosen value (not truncated).
# The connParams clause pins:
#   (e) KEY fidelity: the name/password entries use the keys "database"/"password"
#       (the exact keys the F2P demands), not the deprecated spellings;
#   (f) EMPTY-guard: an empty setting contributes no entry.
#
# F2P (all in tests/dbshell/test_mysql.py + the base.py kwargs change):
#   - test_options_non_deprecated_keys_preferred: OPTIONS carries BOTH the primary and
#     the fallback key -> the primary WINS. THE dbArg discriminator (sub-behaviour a).
#   - test_options_override_settings_proper_values: subTest over both key spellings —
#     the option name overrides the settings NAME, under the non-deprecated keys.
#   - test_parameters: trailing db argument present iff a name is selected (c).
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION (nagini's mandatory `_FRAME_WRITE`: opt_db held at Acc(.,1/2),
#     the rival wrote opt_db.append(0) through the half-owned handle). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "store into a read-only input" rival is not expressible; the lane is VACUOUS.
#   * (ADMISSIBILITY IS NOT ONE OF THEM — see `adm-f2p-shaped-points` below. An
#     earlier revision of this manifest recorded the lane as N/A on the ground that
#     each lean obligation is `∀ args, problem_spec … (implementation … args)` with
#     no precondition hypothesis. That reason was wrong, and the audit measured it:
#     the analogue on a TOTAL carrier is not a precondition that rejects an input,
#     it is the obligation being UNSATISFIABLE at an F2P-shaped concrete input. A
#     positive that discharges the postcondition AT those points — by evaluation,
#     as `have`s, before closing the frozen obligation verbatim — tests that
#     directly, and it is expressible here because both specs are `decide`-able at
#     any literal. Landed in audit.)
#   * DIVERGENCE / non-termination. Not present in the nagini sibling, and on lean it
#     is genuinely vacuous: `implementation_*` is a total Lean `def`, so a diverging
#     implementation cannot be written at all.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. Both behaviors
#     are modeled DEEPLY (no opaque callee, no consumed axiom), so it is vacuous anyway.
from pathlib import Path

INSTANCE = "django__django-14376"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# Each anchor lies ENTIRELY inside an impl-start/impl-end (or proof-start/proof-end)
# region and is unique in the file, so a variant edits only the region it names and
# `same_spec` holds by construction.

# The full dbArg impl body (selection + emptiness test).
_DBARG_IMPL = """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some database
  return none"""
assert _BASE.count(_DBARG_IMPL) == 1, "dbArg impl anchor drifted"

# The frozen dbArg proof body (only the tactic lines).
_DBARG_PROOF = """  intro optDatabase optDb name
  unfold problem_spec_dbArg implementation_dbArg
  simp only [Id.run, bind, pure]
  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
    simp [h]"""
assert _BASE.count(_DBARG_PROOF) == 1, "dbArg proof anchor drifted"

# The full connParams impl body.
_CONN_IMPL = """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs"""
assert _BASE.count(_CONN_IMPL) == 1, "connParams impl anchor drifted"

# The frozen connParams proof body.
_CONN_PROOF = """  intro name password
  unfold problem_spec_connParams implementation_connParams
  simp only [Id.run, bind, pure]
  cases name with
  | none =>
    cases password with
    | none => rfl
    | some p => by_cases hp : p = "" <;> simp [hp]
  | some n =>
    cases password with
    | none => by_cases hn : n = "" <;> simp [hn]
    | some p =>
      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]"""
assert _BASE.count(_CONN_PROOF) == 1, "connParams proof anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG). Each is a
# structurally-DIFFERENT but behaviourally IDENTICAL impl; the `theorem correct_*`
# STATEMENT is kept byte-identical and the proof body is honestly reproven for the
# reshaped impl (no new axiom/lemma/sorry).
# ===========================================================================

# pos-dbArg-nested-select: the flat precedence collapse `optDatabase.getD (optDb.getD
# name)` is reshaped into an explicit nested match (primary-present test first, the
# fallback branch nested in its `none` case), then the same emptiness test. Same chosen
# value in every case (nagini's POS_REORDER, carried over). Reproven by case-splitting
# the two options and the emptiness of the chosen value.
_POS_DBARG = _swap(
    _swap(
        _BASE,
        _DBARG_IMPL,
        """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let chosen : String :=
    match optDatabase with
    | some d => d
    | none => match optDb with
              | some d => d
              | none => name
  if chosen = "" then
    return none
  return some chosen""",
    ),
    _DBARG_PROOF,
    """  intro optDatabase optDb name
  unfold problem_spec_dbArg implementation_dbArg
  simp only [Id.run, bind, pure]
  cases optDatabase with
  | none =>
    cases optDb with
    | none => by_cases h : name = "" <;> simp [h]
    | some d => by_cases h : d = "" <;> simp [h]
  | some d => by_cases h : d = "" <;> simp [h]""",
)

# pos-connParams-entry-lists: the mutable-accumulator loop is reshaped into two
# early-computed entry lists concatenated at the end — same result on every input.
# The proof collapses after unfolding (`simp only [Id.run, bind, pure]` closes it,
# the two branches being definitionally the entry lists).
_POS_CONN = _swap(
    _swap(
        _BASE,
        _CONN_IMPL,
        """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let dbEntry : List (String × String) :=
    match name with
    | some n => if n = "" then [] else [("database", n)]
    | none => []
  let pwEntry : List (String × String) :=
    match password with
    | some p => if p = "" then [] else [("password", p)]
    | none => []
  return dbEntry ++ pwEntry""",
    ),
    _CONN_PROOF,
    """  intro name password
  unfold problem_spec_connParams implementation_connParams
  simp only [Id.run, bind, pure]""",
)


# ===========================================================================
# ADMISSIBILITY (must VERIFY, else PRECOND-TOO-STRONG / spec-shape regression).
# ===========================================================================
# adm-f2p-shaped-points: ports nagini's `_ADMISS_BLOCK`. On that carrier the lane
# asserted the Requires predicates were establishable; here the obligations carry
# no precondition, so the analogue is the obligation being SATISFIABLE at exactly
# the F2P-shaped concrete inputs — a spec that is unsatisfiable at a normal
# configuration is the total-carrier form of PRECOND-TOO-STRONG. Each `have`
# applies `problem_spec_*` ITSELF at that point and closes it by evaluation, so
# what is checked there is the postcondition and not a definitional identity; the
# impl bodies and both frozen proof scripts are otherwise verbatim.
#
# NON-DEGENERACY, measured rather than argued: flipping the first `have`'s expected
# output to the OTHER source's value (`some "otherdb"`) makes the case FAIL with
# ``decide` proved that the proposition … is false`. So the points measure the
# spec's verdict and are not tautologies that would hold in any file.
#
# Points chosen to mirror the F2P configurations: both option keys present (the
# discriminator — primary wins), primary absent so the fallback overrides the
# configured name, no option at all so the name is used, and every source
# empty/absent so no trailing token exists; plus, for connParams, both entries
# present and the empty-name-contributes-nothing shape.
_ADM = _swap(
    _swap(
        _BASE,
        _DBARG_IMPL,
        """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  have _hBothPresentPrimaryWins :
      problem_spec_dbArg (some "chosendb") (some "otherdb") "settingdb"
        (some "chosendb") := by
    unfold problem_spec_dbArg; decide
  have _hOptionOverridesName :
      problem_spec_dbArg none (some "chosendb") "settingdb"
        (some "chosendb") := by
    unfold problem_spec_dbArg; decide
  have _hNameUsedWhenNoOption :
      problem_spec_dbArg none none "settingdb" (some "settingdb") := by
    unfold problem_spec_dbArg; decide
  have _hNoSourceNoToken : problem_spec_dbArg none none "" none := by
    unfold problem_spec_dbArg; decide
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some database
  return none""",
    ),
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  have _hBothEntries :
      problem_spec_connParams (some "settingdb") (some "settingpw")
        [("database", "settingdb"), ("password", "settingpw")] := by
    unfold problem_spec_connParams; decide
  have _hEmptyNameContributesNothing :
      problem_spec_connParams (some "") (some "settingpw")
        [("password", "settingpw")] := by
    unfold problem_spec_connParams; decide
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs""",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only ONE impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the witness — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# --- dbArg rivals ---

# W1 prepatch-fallback-first: consult the fallback option first and NEVER examine the
# primary, so a present primary option does NOT take precedence. This is the
# base_commit shape (`db = OPTIONS.get('db', NAME)`; the non-deprecated key never
# examined). Correct whenever the primary is absent; wrong exactly on the F2P
# discriminator. Attacks sub-behaviour (a).
_RIV_DBARG_PREPATCH = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDb.getD name
  if database ≠ "" then
    return some database
  return none""",
)

# W2 empty-primary-as-absent: treat a PRESENT-BUT-EMPTY primary option as absent
# (fall through to the fallback / name) instead of selecting it. Correct everywhere
# except present-empty primary with a different fallback. Attacks sub-behaviour (b).
_RIV_DBARG_EMPTY_PRIMARY = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database :=
    match optDatabase with
    | some s => if s = "" then optDb.getD name else s
    | none => optDb.getD name
  if database ≠ "" then
    return some database
  return none""",
)

# W3 empty-fallback-as-absent: when the primary is absent but the fallback is
# present-but-empty, fall through to the configured name instead of selecting the
# (empty) fallback. Attacks sub-behaviour (b) on the fallback source.
_RIV_DBARG_EMPTY_FALLBACK = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database :=
    match optDatabase with
    | some s => s
    | none => match optDb with
              | some s => if s = "" then name else s
              | none => name
  if database ≠ "" then
    return some database
  return none""",
)

# W4 always-append: drop the emptiness guard — always emit a trailing token, even
# when the chosen value is empty. Selection correct; the append decision is wrong on
# the empty-name sub-domain. Attacks sub-behaviour (c).
_RIV_DBARG_ALWAYS = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  return some database""",
)

# W5 truncate-name: return the chosen value with its last character dropped — the
# trailing token is a truncated db name. Correct on empty names; wrong on every
# non-empty name. Attacks sub-behaviour (d) (value fidelity).
_RIV_DBARG_TRUNCATE = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some (database.dropRight 1)
  return none""",
)

# --- connParams rivals ---

# R1 deprecated-name-key: carry the database name under the deprecated key "db"
# instead of "database" (the base_commit shape). Attacks sub-behaviour (e) on the name
# entry.
_RIV_CONN_NAMEKEY = _swap(
    _BASE,
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("db", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs""",
)

# R2 deprecated-password-key: carry the password under the deprecated key "passwd"
# instead of "password". Attacks sub-behaviour (e) on the password entry.
_RIV_CONN_PWKEY = _swap(
    _BASE,
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("passwd", p)]
  return kwargs""",
)

# R3 drop-empty-guard-name: emit the name entry even when the configured name is the
# empty string. Attacks sub-behaviour (f) (empty-guard) on the name entry.
_RIV_CONN_EMPTYGUARD = _swap(
    _BASE,
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs""",
)


# W6 ignore-configured-name: the two option sources are consulted as gold does, but
# the THIRD precedence level is dropped — the configured name is never reached (the
# fallback's default is hard-wired empty instead). Correct whenever an option key is
# present; wrong exactly when both are absent and a name IS configured. Added in
# audit: every shipped dbArg selection rival held the primary/fallback pair under
# attack, so nothing exercised the name as the SELECTED source (the shipped
# always-append and empty-fallback rivals only ever reach it at `""`, where the
# emptiness test masks the difference). Attacks sub-behaviour (a) on the third level.
_RIV_DBARG_IGNORE_NAME = _swap(
    _BASE,
    _DBARG_IMPL,
    """def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD "")
  if database ≠ "" then
    return some database
  return none""",
)

# R4 entry-order-swapped: both entries carry the right key and the right value, and
# each is still guarded on its own non-emptiness — only the ORDER is reversed
# (password entry before the name entry). Added in audit: the spec pins the order
# (`name-entry ++ password-entry`) and no shipped rival attacked it, so a permuted
# assembly was unprobed. Observably distinct from gold exactly when BOTH settings
# are non-empty — the only input where two entries coexist. Attacks the ORDER of
# sub-behaviour (e).
_RIV_CONN_ORDER = _swap(
    _BASE,
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  return kwargs""",
)

# R5 drop-empty-guard-password: emit the password entry even when the configured
# password is the empty string. Added in audit: the shipped empty-guard rival
# attacks the NAME entry only, so the password entry's own guard was pinned by no
# rival. Attacks sub-behaviour (f) on the PASSWORD entry.
_RIV_CONN_PW_EMPTYGUARD = _swap(
    _BASE,
    _CONN_IMPL,
    """def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
      kwargs := kwargs ++ [("password", p)]
  return kwargs""",
)


def _wit_dbarg(od, odb, name, note):
    """Refutation witness for a dbArg rival: `¬ problem_spec_dbArg … (implementation_dbArg …)`
    at a concrete literal input, closed by `decide` after unfolding the `Id.run do`
    wrapper. Elaborates against a rival that diverges from the spec there, and FAILS on
    gold (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_dbArg {od} {odb} {name}\n"
        f"    (implementation_dbArg {od} {odb} {name}) := by\n"
        f"  unfold problem_spec_dbArg implementation_dbArg\n"
        f"  simp only [Id.run, bind, pure]\n"
        f"  decide"
    )


def _wit_conn(name, pw, note):
    """Refutation witness for a connParams rival, same two-way discriminator shape."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_connParams {name} {pw}\n"
        f"    (implementation_connParams {name} {pw}) := by\n"
        f"  unfold problem_spec_connParams implementation_connParams\n"
        f"  simp only [Id.run, bind, pure]\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-dbArg-nested-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DBARG,
        "rationale": (
            "structurally-different but CORRECT dbArg impl: the flat precedence collapse "
            "is reshaped into an explicit nested match (primary-present test first, "
            "fallback nested in its none case), then the same emptiness test — identical "
            "chosen value in every case, so the output equals the frozen impl's on every "
            "input. The `theorem correct_dbArg` statement is byte-identical and the proof "
            "is honestly reproven for the reshaped impl (case-split on the two options + "
            "emptiness), no new axiom/lemma/sorry. Carries over nagini POS_REORDER. If it "
            "FAILS => SPEC-TOO-STRONG (postcondition over-fit to one syntactic shape)."
        ),
    },
    {
        "id": "pos-connParams-entry-lists",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONN,
        "rationale": (
            "structurally-different but CORRECT connParams impl: the mutable-accumulator "
            "loop is reshaped into two early-computed entry lists concatenated at the end "
            "— same result on every input. The `theorem correct_connParams` statement is "
            "byte-identical and the proof collapses after unfolding (the two branches are "
            "definitionally the spec's entry lists). No nagini counterpart (nagini did not "
            "model this behavior); it defends the connParams obligation. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "adm-f2p-shaped-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "ports nagini's admiss-both-keys control to a TOTAL carrier. The frozen "
            "obligations carry no precondition hypothesis, so the analogue of "
            "PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at an "
            "F2P-shaped concrete input; this case discharges `problem_spec_dbArg` / "
            "`problem_spec_connParams` AT those points as `have`s (both option keys "
            "present — the discriminator; fallback overriding the configured name; "
            "the name used when no option is present; every source empty/absent so "
            "no trailing token; both connParams entries; empty name contributing "
            "nothing) by EVALUATION, then closes the frozen obligation verbatim. "
            "Each `have` applies the postcondition itself rather than asserting a "
            "definitional identity, so it is the spec's verdict that is measured: "
            "flipping the first point's expected output to the other source's value "
            "makes the case FAIL (`decide` proved … is false), which is what shows "
            "the points are not tautologies. If it FAILS => PRECOND-TOO-STRONG or a "
            "spec-shape regression at a normal configuration."
        ),
    },

    # ---- dbArg uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-dbArg-fallback-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_PREPATCH,
        "refinement": (
            "consulting the fallback option first and never examining the primary is the "
            "base_commit bug (the non-deprecated key never examined). On the F2P "
            "discriminator — both option keys present — it selects the fallback where the "
            "fix selects the primary, so the trailing argv token is the wrong db name and "
            "test_options_non_deprecated_keys_preferred's exact-argv assertion FAILS. A "
            "faithful patch of this shape does NOT resolve; a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (a) PRIMARY "
            "precedence. Witness holds the PRIMARY binder present at a value distinct from "
            "the FALLBACK binder (`optDatabase=some \"A\"`, `optDb=some \"B\"`); gold "
            "selects \"A\", the rival selects \"B\". If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (some "A", some "B", ""): gold -> some "A"; rival -> some "B".
        "witness": _wit_dbarg('(some "A")', '(some "B")', '""',
                              "both keys present: gold picks the primary, rival picks the fallback"),
    },
    {
        "id": "weak-dbArg-empty-primary-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_EMPTY_PRIMARY,
        "refinement": (
            "treating a present-but-empty primary option as absent is a truthiness (not "
            "membership) test: for a primary supplied empty with a non-empty fallback, it "
            "falls through and emits the fallback where the documented get-precedence "
            "selects the empty primary (no trailing token). Such a patch mis-assembles "
            "argv on the present-empty sub-domain and does NOT faithfully implement the "
            "selection — it would diverge from the fixed behavior there."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (b) PRESENT-EMPTY "
            "short-circuit on the primary source. Witness holds the PRIMARY binder present "
            "but EMPTY with a present non-empty FALLBACK (`optDatabase=some \"\"`, "
            "`optDb=some \"x\"`); gold -> none (empty chosen), rival -> some \"x\". If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (some "", some "x", ""): gold -> none; rival -> some "x".
        "witness": _wit_dbarg('(some "")', '(some "x")', '""',
                              "present-empty primary: gold selects it (empty->none), rival falls through"),
    },
    {
        "id": "weak-dbArg-empty-fallback-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_EMPTY_FALLBACK,
        "refinement": (
            "when the primary is absent and the fallback is present-but-empty, this falls "
            "through to the configured name instead of selecting the empty fallback — the "
            "same truthiness-vs-membership divergence on the fallback source. A patch of "
            "this shape emits the settings name where the documented get selects the "
            "present empty fallback (no trailing token); it mis-assembles argv on that "
            "sub-domain and does NOT resolve faithfully."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (b) on the "
            "FALLBACK source, at a point disjoint from the empty-primary witness. Witness: "
            "primary ABSENT, fallback present-EMPTY, name NON-EMPTY (`optDatabase=none`, "
            "`optDb=some \"\"`, `name=\"settingdb\"`); gold -> none, rival -> some "
            "\"settingdb\". If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (none, some "", "settingdb"): gold -> none; rival -> some "settingdb".
        "witness": _wit_dbarg('none', '(some "")', '"settingdb"',
                              "present-empty fallback: gold selects it (empty->none), rival falls to name"),
    },
    {
        "id": "weak-dbArg-always-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_ALWAYS,
        "refinement": (
            "dropping the emptiness guard emits a trailing token even when no db name is "
            "configured (all option keys absent and an empty name). test_parameters "
            "asserts the exact argv with NO trailing entry for the no-name config; an "
            "extra empty token makes that assertion FAIL — it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (c) APPEND-iff-"
            "nonempty. Witness holds every source empty/absent (`optDatabase=none`, "
            "`optDb=none`, `name=\"\"`) so the chosen value is empty; gold -> none, rival "
            "-> some \"\". If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (none, none, ""): gold -> none; rival -> some "".
        "witness": _wit_dbarg('none', 'none', '""',
                              "empty chosen value: gold emits no token, rival emits an empty token"),
    },
    {
        "id": "weak-dbArg-truncate-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_TRUNCATE,
        "refinement": (
            "returning the chosen value with its last character dropped passes a truncated "
            "db name to the client. Every F2P assertion compares the EXACT trailing argv "
            "token; a truncated name FAILS — it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (d) VALUE "
            "fidelity: the trailing token must equal the FULL chosen value. Witness holds "
            "the primary present with a MULTI-character value (`optDatabase=some \"AB\"`); "
            "gold -> some \"AB\", rival -> some \"A\". If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (some "AB", none, ""): gold -> some "AB"; rival -> some "A".
        "witness": _wit_dbarg('(some "AB")', 'none', '""',
                              "multi-char name: gold keeps the full value, rival drops the last char"),
    },

    {
        "id": "weak-dbArg-ignore-configured-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DBARG_IGNORE_NAME,
        "refinement": (
            "consulting the two option sources but never reaching the connection's "
            "own configured name drops the LAST precedence level: for a connection "
            "configured with a name and no option key at all, no trailing db token "
            "is emitted where the documented selection emits the configured name. "
            "test_parameters asserts the exact argv for exactly that configuration "
            "(a name, no options), so a patch of this shape FAILS it — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the dbArg postcondition. Attacks sub-behaviour (a) on the "
            "THIRD precedence level, which no shipped rival reached: the other "
            "selection rivals hold the primary/fallback pair under attack, and the "
            "two that do let the name through only ever see it at `\"\"`, where the "
            "emptiness test masks the divergence. Witness holds BOTH option keys "
            "ABSENT with a NON-EMPTY configured name (`optDatabase=none`, "
            "`optDb=none`, `name=\"settingdb\"`); gold -> some \"settingdb\", rival "
            "-> none. Added in audit. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (none, none, "settingdb"): gold -> some "settingdb"; rival -> none.
        "witness": _wit_dbarg('none', 'none', '"settingdb"',
                              "no option key, name configured: gold emits the name, rival emits nothing"),
    },

    # ---- connParams uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-connParams-deprecated-name-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN_NAMEKEY,
        "refinement": (
            "carrying the database name under the deprecated key is the base_commit shape. "
            "The connection kwargs would record the name under the wrong key, so the "
            "driver receives no recognized database name — the behavior the issue and its "
            "test demand (the non-deprecated key) is not delivered, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the connParams postcondition. Attacks sub-behaviour (e) KEY "
            "fidelity on the NAME entry. Witness holds the NAME binder present non-empty "
            "and the PASSWORD binder absent (`name=some \"n\"`, `password=none`); gold "
            "emits the name-under-\"database\" entry, the rival emits a different key. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (some "n", none): gold -> [("database","n")]; rival -> [("db","n")].
        "witness": _wit_conn('(some "n")', 'none',
                             "name present: gold uses the non-deprecated key, rival uses the deprecated one"),
    },
    {
        "id": "weak-connParams-deprecated-password-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN_PWKEY,
        "refinement": (
            "carrying the password under the deprecated key is the base_commit shape for "
            "the password entry. The kwargs record the password under the wrong key, so "
            "the non-deprecated behavior the issue demands is not delivered — does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the connParams postcondition. Attacks sub-behaviour (e) KEY "
            "fidelity on the PASSWORD entry, exercising the PASSWORD binder (which the "
            "name-key witness holds absent). Witness: NAME absent, PASSWORD present "
            "non-empty (`name=none`, `password=some \"p\"`); gold emits the "
            "password-under-\"password\" entry, the rival emits a different key. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (none, some "p"): gold -> [("password","p")]; rival -> [("passwd","p")].
        "witness": _wit_conn('none', '(some "p")',
                             "password present: gold uses the non-deprecated key, rival uses the deprecated one"),
    },
    {
        "id": "weak-connParams-drop-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN_EMPTYGUARD,
        "refinement": (
            "emitting the name entry even when the configured name is empty records an "
            "empty value under \"database\" where a non-empty guard would contribute "
            "nothing; the driver receives a spurious empty database name, diverging from "
            "the fixed behavior (each entry present exactly when its setting is non-empty)."
        ),
        "rationale": (
            "REJECTED by the connParams postcondition. Attacks sub-behaviour (f) "
            "EMPTY-guard on the NAME entry. Witness holds the NAME binder present but "
            "EMPTY, PASSWORD absent (`name=some \"\"`, `password=none`); gold -> [] (empty "
            "setting contributes nothing), rival -> [(\"database\",\"\")]. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # (some "", none): gold -> []; rival -> [("database","")].
        "witness": _wit_conn('(some "")', 'none',
                             "present-empty name: gold contributes nothing, rival emits an empty entry"),
    },
    {
        "id": "weak-connParams-drop-empty-guard-password",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN_PW_EMPTYGUARD,
        "refinement": (
            "emitting the password entry even when the configured password is empty "
            "records an empty value under \"password\" where a non-empty guard "
            "contributes nothing, so the driver is handed a spurious empty "
            "credential instead of none at all — a divergence from the fixed "
            "behavior (each entry present exactly when its setting is non-empty) on "
            "the empty-password sub-domain."
        ),
        "rationale": (
            "REJECTED by the connParams postcondition. Attacks sub-behaviour (f) "
            "EMPTY-guard on the PASSWORD entry — the shipped empty-guard rival "
            "attacks the NAME entry only, so this entry's own guard was pinned by no "
            "rival. Witness holds NAME absent, PASSWORD present but EMPTY "
            "(`name=none`, `password=some \"\"`); gold -> [], rival -> "
            "[(\"password\",\"\")]. Added in audit. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (none, some ""): gold -> []; rival -> [("password","")].
        "witness": _wit_conn('none', '(some "")',
                             "present-empty password: gold contributes nothing, rival emits an empty entry"),
    },
    {
        "id": "weak-connParams-entry-order-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN_ORDER,
        "refinement": (
            "assembling the two entries in the reverse order still records both "
            "correct keys with both correct values, so it is the weakest divergence "
            "of the connParams lane — but the specified assembly is ordered "
            "(name entry, then password entry), and a patch that reverses it does not "
            "reproduce the fixed behavior's mapping construction. Kept as a rival "
            "rather than a positive precisely because the spec PINS the order: if "
            "the intended behavior were order-agnostic the spec would be too strong, "
            "and this case is what forces that question to be answered explicitly."
        ),
        "rationale": (
            "REJECTED by the connParams postcondition, which pins the concatenation "
            "ORDER (`name-entry ++ password-entry`) — a clause no shipped rival "
            "attacked, since each of the others changes a key or a guard. Observably "
            "distinct from gold on exactly one shape: BOTH settings non-empty, the "
            "only input where two entries coexist (with either absent the lists "
            "coincide, so this rival is definitionally gold there — the witness must "
            "and does use both). Witness `name=some \"n\"`, `password=some \"p\"`; "
            "gold -> [(\"database\",\"n\"),(\"password\",\"p\")], rival -> the "
            "transposition. Added in audit. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (some "n", some "p"): gold -> [("database","n"),("password","p")];
        # rival -> [("password","p"),("database","n")].
        "witness": _wit_conn('(some "n")', '(some "p")',
                             "both settings non-empty: gold's entry order is the spec's, rival transposes"),
    },
]


# No @ContractOnly axioms and no opaque callees: both behaviours (the database-name
# precedence selection + emptiness test, and the connection-kwargs key/value entries)
# are modeled DEEPLY over transparent carriers (Option.getD, string emptiness, list
# append over literal keys), so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
