# properties.py — PBT falsification battery for django__django-14376.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region — which, per markers.spec_view, also elides
# the nested invariants region, so editing the loop invariants stays same_spec.
# The runner checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   resolve_db_arg(opt_database, opt_db: Optional[List[int]],
#                  settings_name: List[int]) -> Tuple[bool, List[int]]
#   models DatabaseClient.settings_to_cmd_args_env: pick the database name with a
#   THREE-LEVEL precedence then decide the trailing positional argument. The
#   load-bearing postcondition clauses:
#     (P1) ToSeq(Result()[1]) == select_name(opt_database, opt_db, ToSeq(settings_name))
#          — the selected name follows non-deprecated > legacy > settings precedence.
#     (P2) Result()[0] == (len(select_name(...)) > 0)   — appended iff non-empty.
#     (P3) Result()[0] == (len(Result()[1]) > 0)         — consistency.
#     (FRAME) Acc(list_pred(opt_database),1/2)/Acc(...opt_db,1/2)/Acc(settings_name,1/2)
#          Required AND Ensured: the three candidate names are READ-ONLY inputs.
#   `select_name` is a @Pure helper but it is GROUNDED in the inputs (fully
#   unfolded: returns ToSeq(opt_primary)/ToSeq(opt_legacy)/settings_name). There
#   is NO opaque answer-key to echo — see 'assessment' re ungrounded-oracle.
#
# F2P (all in tests/dbshell/test_mysql.py, calling only settings_to_cmd_args_env):
#   - test_options_non_deprecated_keys_preferred: OPTIONS has BOTH
#     database='optiondbname' AND db='deprecateddbname' -> expects 'optiondbname'
#     (the non-deprecated 'database' key WINS). THE discriminator.
#   - test_options_override_settings_proper_values: subTest over ('database',...)
#     and ('db',...) — the option db-name overrides the settings NAME.
#   - test_parameters: trailing db argument present iff a name is selected.

from pathlib import Path

INSTANCE = "django__django-14376"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold selection branch (top of the impl region). Every selection-shaped
# rival edits ONLY this block; the forward copy-loop + append decision below it
# are left verbatim so a rejection is attributable to the swap, not a proof gap.
# ---------------------------------------------------------------------------
_SELECT = """    if opt_database is not None:
        chosen = opt_database  # type: List[int]
    elif opt_db is not None:
        chosen = opt_db
    else:
        chosen = settings_name"""

# The append-decision tail (after the copy loop).
_APPEND_TAIL = """    appended = len(database) > 0
    return appended, database"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but semantically IDENTICAL selection: reshape the
# flat if/elif/else into a nested form (compute "primary present?" first, then
# branch on the legacy option inside the else). Same chosen-list identity in
# every case, same forward copy loop (the gold proof shape — no loop-direction
# flip, so no auto-undischargeable fold lemma; directive-3 safe), every gold
# invariant/assert kept verbatim. MUST verify, else SPEC-TOO-STRONG.
_SELECT_REORDER = """    if opt_database is None:
        if opt_db is not None:
            chosen = opt_db  # type: List[int]
        else:
            chosen = settings_name
    else:
        chosen = opt_database"""
POS_REORDER = _swap(_BASE, _SELECT, _SELECT_REORDER)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would enter the spec signature and break
# same_spec (spec_view only elides the impl region). So the admissibility check
# lives INSIDE the impl region, inserted right after `# impl-start`, before any
# gold obligation: build F2P-shaped candidate names and assert the Requires
# predicates (list_pred at the half-permission the contract demands) are
# establishable. A self-recursive call needs no Decreases here, but exercising
# the Requires predicates directly is cleaner and cannot introduce a proof gap.
# If this block cannot verify, the precondition rejects a normal input ->
# PRECOND-TOO-STRONG.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: an F2P-shaped configuration — both option keys
    # present (the discriminator) with a settings name — establishes every
    # Requires predicate the contract demands. Each Requires is guarded by a
    # presence test, so it is expressed as an Implies: an accessibility
    # predicate is impure, and Nagini forbids an impure disjunction
    # (`x is None or Acc(...)`) — it must be written `Implies(x is not None, Acc(...))`.
    Assert(Implies(opt_database is not None, Acc(list_pred(opt_database), 1 / 2)))
    Assert(Implies(opt_db is not None, Acc(list_pred(opt_db), 1 / 2)))
    Assert(Acc(list_pred(settings_name), 1 / 2))"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION (MANDATORY — read-only inputs at Acc(.,1/2)) ==========
# opt_db is a READ-ONLY input held at half permission (Required AND Ensured).
# This rival WRITES to it (opt_db.append(...)) before the selection. A write
# needs FULL permission; only 1/2 is held -> the verifier rejects for
# INSUFFICIENT PERMISSION (it cannot even establish the frame Ensures
# Acc(list_pred(opt_db),1/2) afterwards, having mutated through a fractional
# handle it does not own enough of). The gold selection/loop are kept verbatim
# so the rejection is attributable solely to the inserted write.
# refinement: a faithful real patch that MUTATED the OPTIONS dict's stored
# value (e.g. settings_dict['OPTIONS']['db'].append(...) or rebinding the
# value in place) would corrupt the caller's connection-options mapping; the
# same settings_dict is reused across the test's other assertions / subTests
# (test_options_override_settings_proper_values reruns over both key spellings
# on freshly-built dicts but the OPTIONS values are shared literals), so the
# mutation would leak a wrong db-name into a later observation and the F2P/P2P
# assertions on exact argv lists would FAIL — it would NOT resolve.
# rejection source: the permission system — opt_db is Acc(.,1/2); a write
# requires full permission, and the frame Ensures Acc(list_pred(opt_db),1/2)
# cannot be re-established after writing through a half-owned handle.
_FRAME_WRITE = """    # FRAME-MUTATION RIVAL: write to the read-only half-permission input opt_db.
    if opt_db is not None:
        opt_db.append(0)
    if opt_database is not None:
        chosen = opt_database  # type: List[int]
    elif opt_db is not None:
        chosen = opt_db
    else:
        chosen = settings_name"""
FRAME_WRITE_OPTDB = _swap(_BASE, _SELECT, _FRAME_WRITE)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 partial-domain: the PRE-PATCH bug (== model_prepatch.py). Consult the
# legacy option first and NEVER examine the non-deprecated option, so a present
# 'database' option does NOT take precedence. Correct whenever opt_database is
# absent; DIVERGES exactly on the F2P discriminator (both present -> it returns
# opt_db, the spec/gold return opt_database).
# refinement: this is literally the base_commit code
# `db = OPTIONS.get('db', NAME)` (mapping.md §1; the non-deprecated key never
# examined — the bug). F2P test_options_non_deprecated_keys_preferred puts
# database='optiondbname' AND db='deprecateddbname' and asserts the trailing
# argv entry is 'optiondbname'; the pre-patch selection yields 'deprecateddbname'
# — the test FAILS, so it does NOT resolve.
# rejection source: postcondition (P1)
# ToSeq(Result()[1]) == select_name(opt_database, opt_db, ToSeq(settings_name)):
# when opt_database is present, select_name returns ToSeq(opt_database) but this
# impl copied opt_db.
_SELECT_PREPATCH = """    if opt_db is not None:
        chosen = opt_db  # type: List[int]
    else:
        chosen = settings_name"""
W1_PREPATCH = _swap(_BASE, _SELECT, _SELECT_PREPATCH)


# --- W2 partial-domain (dict.get short-circuit): treat a PRESENT-BUT-EMPTY
# non-deprecated option as absent (fall through to opt_db / settings_name).
# Correct on every input EXCEPT when opt_database is present with an empty value
# AND a different fallback exists. The gold/select_name semantics: a present key
# short-circuits the fallback even when its stored value is the empty string
# (dict.get membership) — so the selected name must be the empty opt_database,
# NOT the fallback.
# refinement: a faithful real patch checking truthiness instead of membership,
# e.g. `OPTIONS.get('database') or OPTIONS.get('db', NAME)`, would, for
# OPTIONS={'database':'', 'db':'x'}, pick 'x' where dict.get-precedence picks ''
# (no trailing argument). The behaviour-under-spec mirrors dict.get exactly
# (mapping.md §2: "a present option short-circuits the fallback even when its
# value is the empty string"); the `or`-based patch diverges on that
# present-empty sub-domain and would mis-assemble argv for such a config — it
# does NOT faithfully implement the documented dict.get semantics the gold has.
# rejection source: postcondition (P1) — when opt_database is present (even
# empty) select_name returns ToSeq(opt_database) ( == [] ), but this impl
# selects the fallback, so ToSeq(Result()[1]) != select_name(...).
_SELECT_EMPTY_AS_ABSENT = """    if opt_database is not None and len(opt_database) > 0:
        chosen = opt_database  # type: List[int]
    elif opt_db is not None:
        chosen = opt_db
    else:
        chosen = settings_name"""
W2_EMPTY_AS_ABSENT = _swap(_BASE, _SELECT, _SELECT_EMPTY_AS_ABSENT)


# --- W3 partial-domain (legacy short-circuit dropped): when the non-deprecated
# option is ABSENT but the legacy option is PRESENT-BUT-EMPTY, fall through to
# the settings name instead of selecting the (empty) legacy value. Correct
# everywhere except opt_database absent & opt_db present-empty & settings
# non-empty: gold selects '' (no trailing arg); this selects settings_name.
# refinement: a real patch writing `OPTIONS.get('db') or NAME` (truthiness, not
# the documented membership get) would, for OPTIONS={'db':''} NAME='settingdb',
# pick 'settingdb' where the gold .get('db', NAME) on a present empty 'db' picks
# '' (no db argument). dict.get returns the present empty value; the test
# battery's empty-value configurations (axiom_check.py exercises present-empty
# options as a first-class case) would observe the wrong argv — does NOT resolve.
# rejection source: postcondition (P1) — opt_database absent, opt_db present
# => select_name returns ToSeq(opt_db) (== []); this impl selects settings_name.
_SELECT_LEGACY_EMPTY = """    if opt_database is not None:
        chosen = opt_database  # type: List[int]
    elif opt_db is not None and len(opt_db) > 0:
        chosen = opt_db
    else:
        chosen = settings_name"""
W3_LEGACY_EMPTY = _swap(_BASE, _SELECT, _SELECT_LEGACY_EMPTY)


# --- W4 control-flow / append-decision: ALWAYS append (appended := True), even
# when the selected name is empty. Selection is correct; the trailing-argument
# decision is wrong on the empty-name sub-domain. The gold appends the database
# positional ONLY when non-empty (`if database: args += [database]`).
# refinement: a real patch dropping the `if database:` guard
# (`args += [database]` unconditionally) would append an EMPTY positional
# argument when no db name is configured (all of OPTIONS db keys absent and
# NAME==''). The argv lists the F2P/P2P assert are exact (test_parameters
# asserts `['mysql']` with no trailing entry for the no-name config); an extra
# '' entry makes the assertion FAIL — it does NOT resolve.
# rejection source: postcondition (P2)
# Result()[0] == (len(select_name(...)) > 0): when the selected name is empty,
# Result()[0] must be False, but this impl returns True. (Also (P3).)
_APPEND_ALWAYS = """    appended = True
    return appended, database"""
W4_ALWAYS_APPEND = _swap(_BASE, _APPEND_TAIL, _APPEND_ALWAYS)


# --- W5 value-level: append from the chosen list one element too FEW, then
# report `appended` from `chosen` rather than the copied result, so the returned
# argument value drops the last code point of any non-empty selected name while
# `appended` still reads true. Correct on empty names; wrong on every non-empty
# name (returns a truncated db-name argument).
# refinement: a real patch that sliced the database name (`database[:-1]`) or
# off-by-one'd the argv assembly would pass a truncated db name to the mysql
# client — every F2P assertion compares the EXACT trailing argv entry
# ('optiondbname', 'optiondbname', etc.); a truncated 'optiondbnam' FAILS — it
# does NOT resolve.
# rejection source: postcondition (P1) ToSeq(Result()[1]) == select_name(...):
# the returned sequence must equal the FULL selected name, but a one-short copy
# drops the last element. We implement it by stopping the copy loop one early;
# the loop invariant ToSeq(database)==ToSeq(chosen).take(i) still holds, but the
# post-loop value no longer equals the full selected name. To keep the loop
# invariant discharging we replace the loop bound, not the invariant.
_COPY_LOOP = """    database = []  # type: List[int]
    i = 0
    while i < len(chosen):"""
_COPY_LOOP_SHORT = """    database = []  # type: List[int]
    i = 0
    while i < len(chosen) - 1:"""
W5_TRUNCATE = _swap(_BASE, _COPY_LOOP, _COPY_LOOP_SHORT)


SPEC_TESTS = [
    {
        "id": "pos-reorder-selection",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl: the flat if/elif/else "
        "selection reshaped into a nested form (primary-present test first, legacy "
        "branch nested in the else); identical chosen-list identity in every case, "
        "same forward copy loop, every gold invariant/assert kept verbatim — must "
        "verify, else SPEC-TOO-STRONG. Reorder only (directive-3 safe; no loop "
        "flip, no fold lemma).",
    },
    {
        "id": "admiss-both-keys",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control block asserts each Requires predicate "
        "(list_pred at 1/2 for present options, list_pred(settings_name) at 1/2) is "
        "establishable for an F2P-shaped input — the precondition must admit a "
        "normal config (both option keys present + a settings name), else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-optdb",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_OPTDB,
        "refinement": "a faithful real patch that mutated the OPTIONS dict's stored "
        "db value in place would corrupt the caller's connection-options mapping "
        "shared across the test's argv assertions; a wrong db-name would leak into a "
        "later observation and the exact-argv F2P/P2P checks would FAIL — it would "
        "NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: opt_db is a read-only input "
        "held at Acc(list_pred(opt_db),1/2); the inserted opt_db.append(0) needs FULL "
        "permission, and the frame Ensures Acc(list_pred(opt_db),1/2) cannot be "
        "re-established after writing through a half-owned handle. MANDATORY "
        "frame-mutation probe (directive 5).",
    },
    {
        "id": "prepatch-legacy-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_PREPATCH,
        "refinement": "this is the base_commit bug `db = OPTIONS.get('db', NAME)` "
        "(the non-deprecated 'database' key never examined; == model_prepatch.py). "
        "F2P test_options_non_deprecated_keys_preferred puts database='optiondbname' "
        "AND db='deprecateddbname' and asserts trailing argv == 'optiondbname'; this "
        "selection yields 'deprecateddbname' — the test FAILS, so it does NOT resolve.",
        "rationale": "rejected by postcondition (P1) ToSeq(Result()[1]) == "
        "select_name(opt_database, opt_db, ToSeq(settings_name)): when opt_database "
        "is present select_name returns ToSeq(opt_database) but this impl copied "
        "opt_db. THE F2P discriminator (partial-domain: both options present).",
    },
    {
        "id": "empty-primary-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_EMPTY_AS_ABSENT,
        "refinement": "a real patch using truthiness instead of membership "
        "(`OPTIONS.get('database') or OPTIONS.get('db', NAME)`) would, for "
        "OPTIONS={'database':'', 'db':'x'}, pick 'x' where the gold dict.get-precedence "
        "picks '' (no trailing arg). The behaviour-under-spec mirrors dict.get exactly "
        "(mapping.md §2); the `or`-based patch diverges on the present-empty primary "
        "sub-domain and mis-assembles argv there — it does NOT faithfully implement "
        "the documented selection.",
        "rationale": "rejected by postcondition (P1): when opt_database is present "
        "(even empty), select_name returns ToSeq(opt_database)==[] but this impl falls "
        "through to the fallback. partial-domain: present-but-empty primary option.",
    },
    {
        "id": "empty-legacy-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_LEGACY_EMPTY,
        "refinement": "a real patch writing `OPTIONS.get('db') or NAME` (truthiness, "
        "not the documented membership get) would, for OPTIONS={'db':''} NAME='settingdb', "
        "pick 'settingdb' where the gold .get('db', NAME) on a present empty 'db' picks "
        "'' (no db argument); the present-empty option configs (axiom_check.py exercises "
        "these) would observe the wrong argv — does NOT resolve.",
        "rationale": "rejected by postcondition (P1): opt_database absent & opt_db "
        "present => select_name returns ToSeq(opt_db)==[] but this impl selects "
        "settings_name. partial-domain: present-but-empty legacy option.",
    },
    {
        "id": "always-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_ALWAYS_APPEND,
        "refinement": "a real patch dropping the `if database:` guard "
        "(`args += [database]` unconditionally) would append an EMPTY positional "
        "argument when no db name is configured (all OPTIONS db keys absent and "
        "NAME==''); test_parameters asserts the exact argv `['mysql']` with no "
        "trailing entry — an extra '' entry FAILS it, so it does NOT resolve.",
        "rationale": "rejected by postcondition (P2) Result()[0] == "
        "(len(select_name(...)) > 0) (and (P3) Result()[0] == (len(Result()[1])>0)): "
        "for an empty selected name appended must be False but this impl returns True. "
        "control-flow-effect: the append decision is the second gold hunk.",
    },
    {
        "id": "truncate-db-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_TRUNCATE,
        "refinement": "a real patch that sliced/off-by-one'd the assembled db name "
        "(`database[:-1]`) would pass a truncated db name to the mysql client; every "
        "F2P assertion compares the EXACT trailing argv entry ('optiondbname', ...), "
        "and a truncated 'optiondbnam' FAILS — it does NOT resolve.",
        "rationale": "rejected by postcondition (P1) ToSeq(Result()[1]) == "
        "select_name(...): the returned sequence must equal the FULL selected name, "
        "but stopping the copy loop one element early (bound `len(chosen)-1`) drops "
        "the last code point of any non-empty name. value-level: the loop invariant "
        "ToSeq(database)==ToSeq(chosen).take(i) still holds, the POST-loop value no "
        "longer equals the full name.",
    },
]


# No @ContractOnly axioms and NO consumed axiom in this bundle (meta.json
# axioms == []; axioms region is an empty comment). The lone deep-model
# reference `select_name` is an A-REFERENCE validated == the real gold-patched
# DatabaseClient.settings_to_cmd_args_env out-of-band by axiom_check.py / G-AX
# (3100 observations incl. the non-deprecated-preferred discriminator), NOT
# consumed inside any Ensures via a @ContractOnly contract. The PBT axiom lane
# checks @ContractOnly soundness/containment; there is no such axiom here, so the
# axiom lane is vacuous. (The A-reference is already discharged by G-AX, status
# pass in meta.json.)
AXIOM_TESTS = []
