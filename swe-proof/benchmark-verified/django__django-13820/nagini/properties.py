# properties.py — PBT falsification battery for django__django-13820.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that shares the FROZEN spec exactly
# (region-surgery: only text strictly inside # impl-start / # impl-end is ever
# changed, so same_spec is guaranteed) and is checked by Nagini verify.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   treat_as_migration_source(is_package, file_is_set, path_is_ordinary_list) -> bool
#   * All three inputs are `bool` value parameters — IMMUTABLE scalars passed by
#     value. There is NO Acc(x,1/2) read-only HEAP input, hence NO frame to
#     mutate: the FRAME-MUTATION class is N/A for this instance (see assessment).
#   * The load-bearing postcondition `Result() == is_source(...)` pins the result
#     to a @Pure helper that is FULLY GROUNDED in the inputs:
#         is_source = is_package and (file_is_set or path_is_ordinary_list)
#     `is_source` is a transparent boolean function of the args (no opaque
#     answer-key / marker), so there is no WRONG echo to build: echoing
#     is_source(...) IS the correct answer. UNGROUNDED-ORACLE ECHO is therefore
#     N/A; instead we ship an honest cheapest-impl positive control that returns
#     the grounded oracle directly (expect=verify).
#   * Precondition: Implies(not is_package, not path_is_ordinary_list) — pins the
#     vacuous list-ness fact of a non-package.
#
# The full FAITHFUL input space (6 rows; the precondition removes the two
# (is_package=False, path_is_ordinary_list=True) rows):
#   (P, F, L) -> is_source
#   (F, F, F) -> F        non-package, skipped
#   (F, T, F) -> F        non-package, skipped
#   (T, F, F) -> F        package, no __file__, non-list __path__  => NAMESPACE pkg, skip
#   (T, F, T) -> T        package, no __file__, list __path__       => the DISCRIMINATING row (F2P)
#   (T, T, F) -> T        package, __file__ set, non-list __path__  => load
#   (T, T, T) -> T        package, __file__ set, list __path__      => normal pkg, load
#
# Each expect="reject" rival flips EXACTLY one of these rows and carries the
# refinement argument that its faithful real patch would NOT resolve the
# F2P/P2P — so a verifying rival is a true verify-not-resolve break.
from pathlib import Path

INSTANCE = "django__django-13820"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region, verbatim (text strictly between the markers).
_GOLD_IMPL = """    if not is_package:
        return False
    if (not file_is_set) and (not path_is_ordinary_list):
        return False
    return True"""


def _swap(src, old, new):
    """Replace the UNIQUE occurrence of `old` in `src` with `new`.

    `old` is always the gold impl body, so every variant edits ONLY inside the
    # impl-start / # impl-end region; the spec view (axioms/pure/pre/post +
    signatures) is never touched => same_spec is guaranteed True."""
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    return _swap(_BASE, _GOLD_IMPL, new_impl)


SPEC_TESTS = [
    # ---------------------------------------------------------------- POSITIVE
    # 1. Positive control — structurally different but CORRECT impl. The gold
    #    impl uses two early-return guards; this reshapes the SAME decision into
    #    a single boolean expression bound to a typed local, then returns it.
    #    No loop / no fold, so there is no induction lemma to discharge; the
    #    @Pure postcondition is established directly by Nagini's boolean theory.
    #    MUST verify (else SPEC-TOO-STRONG: a faithful correct impl is rejected).
    {
        "id": "pos-control-expr",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    decision = is_package and (file_is_set or path_is_ordinary_list)  # type: bool\n"
            "    return decision"
        ),
        "rationale": "A correct impl written as one boolean expression (different "
                     "shape from the gold two-guard form) must satisfy "
                     "Result()==is_source(...). If it cannot verify, the "
                     "postcondition is SPEC-TOO-STRONG.",
    },
    # 2. Positive control — cheapest honest impl: return the GROUNDED @Pure
    #    oracle directly. Because is_source is a transparent function of the
    #    args (NOT an opaque answer-key), echoing it is the CORRECT behaviour,
    #    not an ungrounded-oracle cheat. This is the honest positive control the
    #    plan asks for when oracle-echo is N/A. MUST verify.
    {
        "id": "pos-control-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant("    return is_source(is_package, file_is_set, path_is_ordinary_list)"),
        "rationale": "is_source is GROUNDED in the inputs (is_package and "
                     "(file_is_set or path_is_ordinary_list)); returning it is the "
                     "correct answer, so this honest cheapest impl must verify. "
                     "There is no WRONG echo to build => UNGROUNDED-ORACLE N/A.",
    },
    # 3. Positive control — branch-reorder: handle the LOAD cases first, then the
    #    two skip cases, in a different order than gold. Same total function.
    #    MUST verify (keeps the spec's full pinning satisfiable under reordering).
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    if is_package and (file_is_set or path_is_ordinary_list):\n"
            "        return True\n"
            "    return False"
        ),
        "rationale": "Branch-reorder (LOAD case tested first) computing the same "
                     "total function. Must verify; else SPEC-TOO-STRONG.",
    },

    # ----------------------------------------------------------- ADMISSIBILITY
    # 4. Admissibility — a positive-control caller invokes the modeled function
    #    on the EXACT F2P-shaped input (the discriminating frozen-package row
    #    is_package=True, file_is_set=False, path_is_ordinary_list=True) and
    #    asserts the precondition admits it and the result is True (migration
    #    source). If the Requires cannot be established for this legitimate F2P
    #    input, PRECOND-TOO-STRONG. The self-call body keeps the gold impl so the
    #    callee itself still verifies.
    {
        "id": "admiss-f2p-discriminating-row",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            _GOLD_IMPL
            + "\n\n\n"
            + "def _admiss_caller() -> None:\n"
            + "    # F2P test_loading_package_without__file__: a regular package whose\n"
            + "    # __file__ was deleted is_package=True, file_is_set=False, and its\n"
            + "    # __path__ stays an ordinary list path_is_ordinary_list=True.\n"
            + "    res = treat_as_migration_source(True, False, True)\n"
            + "    Assert(res)\n"
        ),
        "rationale": "The precondition Implies(not is_package, not "
                     "path_is_ordinary_list) is vacuously satisfied when "
                     "is_package=True, so the F2P input is admitted and the call "
                     "returns True. If this caller fails to verify, "
                     "PRECOND-TOO-STRONG.",
    },

    # --------------------------------------------------------- PARTIAL-DOMAIN
    # 5. THE discriminating-row rival = the pre-patch behaviour. Wrong on exactly
    #    one row, (is_package=True, file_is_set=False, path_is_ordinary_list=True):
    #    returns False (skip) where the spec demands True. Reproduces the
    #    pre-patch skeleton's `__file__ is None => skip` for a list __path__.
    #    If it VERIFIES, SPEC-TOO-WEAK (the spec failed to sense the very change
    #    the patch makes).
    {
        "id": "weak-prepatch-discriminating-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if not is_package:\n"
            "        return False\n"
            "    if not file_is_set:\n"
            "        return False\n"
            "    return True"
        ),
        "refinement": "This is the pre-patch logic (skip whenever __file__ is None, "
                      "ignoring whether __path__ is a list). Its faithful real "
                      "patch keeps `if getattr(module,'__file__',None) is None: "
                      "unmigrated_apps.add(...); continue`, so the frozen-environment "
                      "regular package (no __file__, list __path__) is wrongly "
                      "skipped and the F2P test_loading_package_without__file__ "
                      "(which asserts migrations ['0001_initial','0002_second'] load) "
                      "FAILS. So verify-here would be verify-not-resolve.",
        "rationale": "Violates Ensures clause 4 "
                     "(Implies(is_package and not file_is_set and "
                     "path_is_ordinary_list, Result())) and the master clause "
                     "Result()==is_source(...) on row (True,False,True). Must reject.",
    },
    # 6. Namespace-package rival: wrong on exactly (True, False, False) — returns
    #    True (load) for the package with no __file__ AND non-list __path__, i.e.
    #    it LOADS PEP-420 namespace packages. If it verifies, SPEC-TOO-WEAK.
    {
        "id": "weak-loads-namespace-pkg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if not is_package:\n"
            "        return False\n"
            "    return True"
        ),
        "refinement": "Drops the namespace-package skip entirely: a faithful patch "
                      "removing `getattr(module,'__file__',None) is None and not "
                      "isinstance(module.__path__,list): continue` would LOAD "
                      "namespace packages, regressing the P2P tests that assert a "
                      "namespace package (no __file__, _NamespacePath __path__) "
                      "stays in unmigrated_apps "
                      "(test_load_unmigrated_dependency / namespace-package P2P). "
                      "So verify-here would be verify-not-resolve.",
        "rationale": "Violates Ensures clause 3 "
                     "(Implies(is_package, Result()==(file_is_set or "
                     "path_is_ordinary_list))) and the master clause on row "
                     "(True,False,False): spec demands False, rival returns True. "
                     "Must reject.",
    },
    # 7. Non-package rival: wrong on the non-package rows — returns True for a
    #    module that is NOT a package (no __path__). If it verifies, SPEC-TOO-WEAK.
    {
        "id": "weak-loads-non-package",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if (not file_is_set) and (not path_is_ordinary_list):\n"
            "        return False\n"
            "    return True"
        ),
        "refinement": "Drops the `if not hasattr(module,'__path__'): continue` "
                      "guard, so a plain non-package module (e.g. a migrations.py "
                      "file, or any app whose migrations module is not a package) "
                      "is treated as a migration source and Django would call "
                      "pkgutil.iter_modules(module.__path__) on an object with no "
                      "__path__, crashing / mis-loading. The P2P "
                      "test_load_module_file (a migrations *module*, not package, "
                      "must be unmigrated) FAILS. So verify-here would be "
                      "verify-not-resolve.",
        "rationale": "Violates Ensures clause 2 (Implies(not is_package, not "
                     "Result())) on rows (False,T,F) and (False,F,F): rival returns "
                     "True for is_package=False. Must reject.",
    },
    # 8. Always-True rival (cheap supporting partial-domain): returns True for
    #    EVERY input, including both non-package rows and the namespace row.
    #    Wrong on 3 of 6 rows. Supporting near-miss; carries a real refinement.
    {
        "id": "weak-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant("    return True"),
        "refinement": "Loads every module as a migration source. A faithful patch "
                      "that always falls through to migrated_apps would load "
                      "non-packages and namespace packages alike, breaking the P2P "
                      "unmigrated-apps assertions and crashing on iter_modules of a "
                      "non-package. So verify-here would be verify-not-resolve.",
        "rationale": "Violates Ensures clause 1 (Result()==is_source) on every "
                     "skip row. Supporting partial-domain. Must reject.",
    },
    # 9. Always-False rival (cheap supporting partial-domain): returns False for
    #    EVERY input, so it never loads ANY migration source — including the F2P
    #    discriminating row and the two normal-load rows. Wrong on 3 of 6 rows.
    {
        "id": "weak-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant("    return False"),
        "refinement": "Skips every module, so NO app has migrations loaded — the "
                      "F2P test_loading_package_without__file__ (and every "
                      "migrations-loading P2P) FAILS. So verify-here would be "
                      "verify-not-resolve.",
        "rationale": "Violates the master clause Result()==is_source on every load "
                     "row (True,F,T)/(True,T,F)/(True,T,T). Supporting "
                     "partial-domain. Must reject.",
    },
    # 10. Negated-list rival (subtle partial-domain): uses `path_is_ordinary_list`
    #     with the WRONG polarity for the namespace test — loads a package iff
    #     file_is_set OR NOT path_is_ordinary_list. Correct on the file_is_set
    #     rows but FLIPS the two no-__file__ package rows: it now LOADS the
    #     namespace package (T,F,F)->True and SKIPS the frozen regular package
    #     (T,F,T)->False. Doubly wrong; if it verifies, SPEC-TOO-WEAK.
    {
        "id": "weak-list-polarity-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if not is_package:\n"
            "        return False\n"
            "    if (not file_is_set) and path_is_ordinary_list:\n"
            "        return False\n"
            "    return True"
        ),
        "refinement": "Inverts the list test: a faithful patch using `isinstance("
                      "module.__path__, list)` (without the `not`) in the skip "
                      "condition would SKIP frozen regular packages (list __path__, "
                      "no __file__) and LOAD namespace packages (non-list __path__, "
                      "no __file__) — exactly backwards. The F2P fails (regular "
                      "frozen package skipped) AND the namespace P2P regresses. So "
                      "verify-here would be verify-not-resolve.",
        "rationale": "Violates the master clause on BOTH (True,False,True) "
                     "(spec True, rival False) and (True,False,False) (spec False, "
                     "rival True). Must reject.",
    },
]

# No @ContractOnly axioms and no A-reference deep models (meta.json axioms == [],
# deep_model_references == []). The changed operation is boolean predicate logic
# modelled deeply; the three module introspections are unchanged builtins refined
# to truth values (kind R). There is no axiom Ensures to fuzz and no callee
# contract to contain, so the axiom lane is empty by construction. (axiom_check.py
# separately validates the two R-refinements in-container as a G-AX R-soundness
# oracle; that is the bundle's existing check, not a PBT axiom obligation.)
AXIOM_TESTS = []
