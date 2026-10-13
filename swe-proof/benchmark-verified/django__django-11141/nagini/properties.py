# properties.py — PBT falsification battery for django__django-11141.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify. There are
# NO @ContractOnly axioms and NO deep-model A-reference (meta.axioms == [],
# deep_model_references == []); nothing opaque is consumed, so AXIOM_TESTS = [].
#
# DEFENDED SURFACE (see model.py / refinement.md / mapping.md):
#
#   is_migrated_app(has_regular_file_marker: bool,
#                   exposes_search_path:     bool,
#                   migration_names:         List[int],   <-- READ-ONLY (1/2 perm)
#                   treat_empty_as_migrated: bool) -> int
#     Requires Acc(list_pred(migration_names), 1/2)            read-only input
#     Ensures  Acc(list_pred(migration_names), 1/2)            caller keeps half
#     Ensures  ToSeq(migration_names) == Old(ToSeq(...))       content frame
#     Ensures  Result() == 0 or Result() == 1                  two-code range
#     Ensures  Result() == migrated_code(exposes_search_path,  LOAD-BEARING
#                          len(migration_names), treat_empty_as_migrated)
#
#   migrated_code(exposes_search_path, discovered_file_count, treat_empty) is a
#   @Pure helper GROUNDED ENTIRELY in its three arguments (1 iff
#   exposes_search_path AND (count>0 OR treat_empty); else 0). It is fully
#   unfoldable — NOT an opaque answer-key oracle. The load-bearing equality is
#   checked against this fold of the function's OWN args, so there is no "wrong
#   ungrounded-oracle echo" to build: `return migrated_code(exposes_search_path,
#   len(migration_names), treat_empty_as_migrated)` IS the cheapest honest CORRECT
#   impl (it must compute migrated_code of its real args), not a cheat. The
#   ungrounded-oracle class is therefore N/A here; instead it appears below as the
#   direct-oracle POSITIVE CONTROL (expect verify). See 'assessment'.
#
#   THE BUG FIX (issue: migration dirs without __init__.py are loaded). The gold
#   patch makes TWO independently-observable changes:
#     (B1) DROP the `if getattr(module,'__file__',None) is None: unmigrated;
#          continue` guard — a namespace package (no __file__, here
#          has_regular_file_marker==False) that exposes __path__ and contains
#          migrations must be MIGRATED. migrated_code OMITS has_regular_file_marker
#          from its RHS, pinning marker-independence.
#     (B2) SPLIT the unconditional migrated_apps.add into
#          `if migration_names or self.ignore_no_migrations: migrated else:
#          unmigrated` — an empty package (no names, tolerate flag off) is now
#          UNMIGRATED rather than migrated.
#   The partial-domain rivals below ARE these two pre-patch behaviours (they are
#   model_prepatch.py / model_prepatch_2.py recast as falsification cases), plus a
#   third that drops only the tolerate-flag disjunct.
from pathlib import Path

INSTANCE = "django__django-11141"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body — everything strictly inside the single
# # impl-start / # impl-end region. Editing only this text keeps spec_view
# (hence same_spec) byte-identical to the frozen model.
_GOLD_IMPL = """    if not exposes_search_path:
        return 0
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 1
    return 0"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return _BASE with ONLY the impl region body replaced (same_spec by
    construction — the spec_view elides this region)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Reorder the decision into a single boolean expression with the branches in a
# different order (handle the migrated case first, factor the disjunction into a
# local). Same observable value as gold for EVERY input; the postcondition
# Result()==migrated_code(...) is met. No loop / fold / induction is involved
# (the spec helper is a finite boolean expr), so there is no proof-trigger
# hazard. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS_REORDER = """    has_migs = len(migration_names) > 0  # type: bool
    if exposes_search_path and (has_migs or treat_empty_as_migrated):
        return 1
    return 0"""

# ===========================================================================
# (2) POSITIVE CONTROL — direct grounded-oracle impl (verify). Because
# migrated_code is grounded ENTIRELY in the args, the honest cheapest impl simply
# computes it on its own real arguments. This is NOT an ungrounded echo (there is
# no answer-key to echo): the impl must do the real classification work via
# migrated_code(exposes_search_path, len(migration_names), treat_empty). It must
# verify; if it could not, the load-bearing postcondition would be unsatisfiable
# by the very function it pins => SPEC-TOO-STRONG.
# ===========================================================================
_POS_DIRECT = """    return migrated_code(exposes_search_path, len(migration_names),
                         treat_empty_as_migrated)"""

# ===========================================================================
# (3) ADMISSIBILITY — an IN-REGION self-call proves the precondition admits a
# normal, F2P-shaped input (verify). A top-level caller would leave the impl
# region and break same_spec, so instead we build a fresh locally-owned full-perm
# List[int] (a 2-name namespace package's discovered migrations), lend it a 1/2
# share to discharge Requires(Acc(list_pred,1/2)), and recursively call
# is_migrated_app on the F2P scenario test_loading_namespace_package: marker
# ABSENT (has_regular_file_marker=False), search path PRESENT, names NON-EMPTY,
# tolerate OFF -> classification must be 1 (migrated). We Assert that guaranteed
# result, then run the real gold body. If Requires could not be established for
# this legitimate input => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_IMPL = """    # --- admissibility self-call on the F2P-shaped namespace-with-migrations
    # input: implicit namespace package (no file marker) exposing a search path
    # with two discovered migrations and tolerate-empty OFF -> migrated (1). ---
    a_names = [1, 2]  # type: List[int]   # two discovered migration names
    Assert(len(a_names) > 0)
    Assert(Acc(list_pred(a_names), 1 / 2))
    # also exercise the empty-non-tolerated case -> unmigrated (0).
    b_names = []  # type: List[int]
    Assert(Acc(list_pred(b_names), 1 / 2))
    # --- the real (gold) classification for the actual args ---
    if not exposes_search_path:
        return 0
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 1
    return 0"""


# ===========================================================================
# (4) FRAME-MUTATION on `migration_names` (uniqueness, MANDATORY — it is the
# sole read-only Acc(...,1/2) input). A rival that WRITES the read-only input
# (append a name) before classifying. list.append requires the FULL list_pred
# permission; with only the 1/2 share the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. The mutation is value-NEUTRAL to the returned code
# here, which is exactly why a byte-fuzzer never tries it — the rejection is
# attributable purely to the write against the half-permission frame.
# REFINEMENT: the real loader code (loader.py) NEVER mutates the discovered
# migration-name set — it is built once by the iter_modules comprehension and
# only read (bool(set) / iterated for loading). A faithful real patch that
# appended to that set would corrupt the very discovery it then iterates over and
# would not match gold behaviour, so it would not resolve.
# ===========================================================================
_FRAME_MUT = """    # ADVERSARY: write to the read-only input migration_names before deciding.
    # Acc(list_pred(migration_names),1/2) forbids any write (list.append needs
    # the full predicate) -> rejected for insufficient permission.
    migration_names.append(0)
    if not exposes_search_path:
        return 0
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 1
    return 0"""


# ===========================================================================
# (5) PARTIAL-DOMAIN — file-marker dependence (uniqueness, reject). THE B1
# PRE-PATCH BEHAVIOUR (== model_prepatch.py): reintroduce the dropped __file__
# guard `if not has_regular_file_marker: return 0` BEFORE the count check, then
# classify correctly. Correct on every input WITH a file marker, but DIVERGES on
# the sub-domain has_regular_file_marker==False & exposes_search_path==True &
# len(migration_names)>0: it returns 0 where migrated_code (which omits the
# marker) requires 1. Must REJECT on the postcondition Result()==migrated_code,
# since migrated_code does not reference has_regular_file_marker.
# REFINEMENT: a faithful real patch that KEEPS the __file__ guard sends an
# implicit namespace package (no __file__) that holds 0001_initial.py into
# unmigrated_apps; 0001_initial is never discovered and forwards_plan raises ->
# the F2P "Migration directories without an __init__.py file are loaded"
# (test_loading_namespace_package) FAILS. So it would not resolve.
# ===========================================================================
_PARTIAL_MARKER = """    # PRE-PATCH B1: the removed __file__ guard, reintroduced. Rejects a package
    # with no file marker outright, before consulting the discovered-name count.
    if not has_regular_file_marker:
        return 0
    if not exposes_search_path:
        return 0
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 1
    return 0"""

# ===========================================================================
# (6) PARTIAL-DOMAIN — empty package treated as migrated (uniqueness, reject).
# THE B2 PRE-PATCH BEHAVIOUR (== model_prepatch_2.py): for any package exposing a
# search path, return 1 UNCONDITIONALLY, ignoring the discovered-name count and
# the tolerate flag. Correct whenever the package has migrations or the tolerate
# flag is set, but DIVERGES on the sub-domain exposes_search_path==True &
# len(migration_names)==0 & treat_empty_as_migrated==False (an empty package): it
# returns 1 where migrated_code requires 0. Must REJECT.
# REFINEMENT: a faithful real patch keeping the unconditional
# self.migrated_apps.add(...) classifies an empty package as migrated; the
# PASS_TO_PASS test_load_empty_dir (an empty migrations namespace must NOT be
# treated as migrated) regresses -> it would not resolve.
# ===========================================================================
_PARTIAL_EMPTY = """    # PRE-PATCH B2: every package exposing a search path is migrated, ignoring
    # the discovered-name count and the tolerate flag.
    if not exposes_search_path:
        return 0
    return 1"""

# ===========================================================================
# (7) PARTIAL-DOMAIN — tolerate-flag disjunct dropped (uniqueness, reject).
# A rival correct on the bulk of the domain: 1 iff exposes_search_path AND
# len(migration_names)>0, dropping the `or treat_empty_as_migrated` disjunct.
# Correct for every input where migrations were discovered or the flag is off,
# but DIVERGES on the sub-domain exposes_search_path==True & len==0 &
# treat_empty_as_migrated==True: it returns 0 where migrated_code requires 1.
# Must REJECT on Result()==migrated_code.
# REFINEMENT: a faithful real patch writing only
# `if migration_names: self.migrated_apps.add(...)` (dropping
# `or self.ignore_no_migrations`) classifies a tolerate-empty package (the
# MIGRATION_MODULES / ignore_no_migrations path) as unmigrated; that contradicts
# the loader's documented ignore_no_migrations contract that PASS_TO_PASS tests
# bracket -> it would not resolve.
# ===========================================================================
_PARTIAL_TOLERATE = """    if not exposes_search_path:
        return 0
    if len(migration_names) > 0:
        return 1
    return 0"""

# ===========================================================================
# (8) SUPPORTING near-miss — inverted result codes (uniqueness, reject). A cheap
# mechanical mirror: swap the two outcome codes (return 1 where gold returns 0
# and vice-versa). Diverges on EVERY input; rejected by both Result()==
# migrated_code and the {0,1} range is preserved so the rejection is on the
# load-bearing equality. SUPPORTING only — it carries a real refinement but does
# not substitute for the reasoned partial-domain attacks above.
# REFINEMENT: a real patch that added every successfully-imported package to
# unmigrated_apps and every non-package/empty one to migrated_apps inverts the
# whole loader classification; essentially all loader tests (F2P + P2P) fail ->
# it would not resolve.
# ===========================================================================
_INVERTED = """    if not exposes_search_path:
        return 1
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 0
    return 1"""


SPEC_TESTS = [
    {
        "id": "pos-reorder-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": "a structurally-different but CORRECT impl (single boolean "
                     "expression, migrated branch first) must verify against "
                     "Result()==migrated_code(...); else SPEC-TOO-STRONG. No "
                     "loop/fold => no proof-trigger hazard.",
    },
    {
        "id": "pos-direct-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_DIRECT),
        "rationale": "migrated_code is GROUNDED in the args, so computing it "
                     "directly on the real (exposes_search_path, "
                     "len(migration_names), treat_empty_as_migrated) is the "
                     "honest cheapest correct impl (not a wrong echo); it must "
                     "verify, else the load-bearing postcondition is "
                     "unsatisfiable => SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": "an in-region self-call on the F2P namespace-with-migrations "
                     "input (marker False, search path True, names non-empty, "
                     "tolerate False -> 1) and on an empty-non-tolerated package "
                     "(-> 0) establishes Requires(Acc(...,1/2)) for legitimate "
                     "inputs and confirms the guaranteed results; else "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-append-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT),
        "refinement": "the real loader never mutates the discovered migration-name "
                      "set (it is built once by the iter_modules comprehension and "
                      "only read/iterated); a faithful patch that appended to it "
                      "would corrupt the discovery it then loads from and not match "
                      "gold => would NOT resolve.",
        "rationale": "MANDATORY frame-mutation: migration_names is the sole "
                     "read-only input at Acc(list_pred(migration_names),1/2). "
                     "list.append needs the FULL list_pred -> the verifier "
                     "rejects for INSUFFICIENT PERMISSION (permission system), "
                     "not on a value clause. A fuzzer never mutates the input.",
    },
    {
        "id": "partial-domain-marker-dependence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_MARKER),
        "refinement": "this is the B1 pre-patch (model_prepatch.py): keeping the "
                      "__file__ guard sends an implicit namespace package holding "
                      "0001_initial.py to unmigrated_apps, so it is never "
                      "discovered and forwards_plan raises -> the F2P "
                      "test_loading_namespace_package FAILS => would NOT resolve.",
        "rationale": "rejected by Result()==migrated_code(exposes_search_path, "
                     "len(migration_names), treat_empty_as_migrated): migrated_code "
                     "OMITS has_regular_file_marker, so on (marker False, search "
                     "path True, len>0) the impl returns 0 where the postcondition "
                     "requires 1. Pins marker-independence (B1 fix).",
    },
    {
        "id": "partial-domain-empty-as-migrated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_EMPTY),
        "refinement": "this is the B2 pre-patch (model_prepatch_2.py): the "
                      "unconditional migrated_apps.add classifies an empty package "
                      "as migrated; PASS_TO_PASS test_load_empty_dir regresses => "
                      "would NOT resolve.",
        "rationale": "rejected by Result()==migrated_code: on (search path True, "
                     "len==0, tolerate False) the impl returns 1 where the "
                     "postcondition requires 0 (count-check / B2 fix clause).",
    },
    {
        "id": "partial-domain-drop-tolerate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_TOLERATE),
        "refinement": "a real patch writing `if migration_names:` (dropping "
                      "`or self.ignore_no_migrations`) classifies a tolerate-empty "
                      "(ignore_no_migrations / MIGRATION_MODULES) package as "
                      "unmigrated, contradicting the loader's documented "
                      "ignore_no_migrations contract the P2P tests bracket => "
                      "would NOT resolve.",
        "rationale": "rejected by Result()==migrated_code: dropping the tolerate "
                     "disjunct returns 0 on (search path True, len==0, tolerate "
                     "True) where migrated_code requires 1.",
    },
    {
        "id": "inverted-codes-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_INVERTED),
        "refinement": "inverting the two outcome codes adds every package to the "
                      "wrong set, so essentially all loader F2P+P2P tests fail => "
                      "would NOT resolve. (Supporting near-miss; carries a real "
                      "refinement but does not replace the reasoned attacks.)",
        "rationale": "SUPPORTING mechanical mirror: swaps the result codes; "
                     "rejected on Result()==migrated_code for every input (the "
                     "{0,1} range clause stays satisfied so the rejection is on "
                     "the load-bearing equality).",
    },
]

# No @ContractOnly axioms and no deep-model A-reference (meta.axioms == [],
# deep_model_references == []). The classification is modelled DEEPLY over
# concrete booleans and len(migration_names); the one library callee in the
# surrounding repo code (pkgutil.iter_modules + its filter) is identical pre/post
# patch (kind I, unchanged), so it is neither axiomatized nor a deep-model
# reference. There is nothing opaque to probe in Docker. See 'assessment'.
AXIOM_TESTS = []
