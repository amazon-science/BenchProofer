# properties.py — PBT falsification battery for astropy__astropy-7336.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region of finalize_return, which
# spec_view elides — so same_spec holds by construction) and are checked by
# Nagini verify. There are no @ContractOnly axioms (meta.axioms == []), so the
# Docker axiom lane is empty (see AXIOM_TESTS / 'assessment').
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   finalize_return(ret: RetVal, target: int) -> RetVal
#     Requires Acc(ret.is_none, 1/2) and Acc(ret.unit, 1/2)   <-- READ-ONLY input
#     Requires ret.is_none == (ret.unit == NO_UNIT())         <-- domain fact
#     Ensures  Acc(ret.is_none, 1/2) and Acc(ret.unit, 1/2)   <-- frame-back
#     Ensures  Acc(Result().is_none) and Acc(Result().unit)
#     Ensures  Implies(not is_genuine_target(target),         <-- PASS-THROUGH clause
#                      Result().is_none == ret.is_none and Result().unit == ret.unit)
#     Ensures  Implies(is_genuine_target(target),             <-- CONVERT clause
#                      (not Result().is_none)
#                      and Result().unit == convert_unit(ret.unit, target))
#
#   The decision is pinned BOTH ways. is_genuine_target(t) == (t != -1 and t != -2).
#   convert_unit(q_unit, target) is @Pure with body `return target`, Requires
#   is_genuine_target(target), Ensures Result() == target. It is GROUNDED ENTIRELY
#   in `target` (fully unfoldable; NOT an opaque answer-key oracle) — its precond
#   is_genuine_target(target) is the load-bearing guard: any impl that calls
#   convert_unit on a NON-genuine target (the -> None case) is rejected at the
#   call site for a precondition violation. Hence the "wrong ungrounded-oracle
#   echo" class is N/A (see 'assessment'); the positive control instead is a
#   branch-reorder / local-reshape, and a cheapest-honest positive control is
#   covered by it.
#
#   The BEHAVIOURAL DISCRIMINATOR (the bug fix, the F2P test
#   test_return_annotation_none): the `-> None` return target (TARGET_NOVALUE) is
#   treated like the unspecified sentinel (PASS THROUGH), NOT like a genuine unit
#   target. The pre-patch wrapper only excluded inspect.Signature.empty, so it
#   attempted None.to(None) on a `-> None` function and raised AttributeError.
#   model_prepatch.py reproduces that (convert whenever target != UNSPECIFIED) and
#   fails verification on convert_unit's precondition for target == TARGET_NOVALUE
#   (G-DIFF). The always-convert rival below IS that pre-patch behaviour.
#
#   READ-ONLY input present (Acc(ret.*,1/2)) -> the frame-mutation reject case is
#   MANDATORY and included.
from pathlib import Path

INSTANCE = "astropy__astropy-7336"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The single impl region of finalize_return (between # impl-start / # impl-end).
# Editing ONLY this text keeps spec_view (hence same_spec) byte-identical.
# ===========================================================================
_IMPL_GOLD = """    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: finalize_return body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Reorder the branches (test the NON-genuine / pass-through case first) and stage
# both returns through named locals. Same observable values on both branches;
# the convert branch still calls convert_unit(ret.unit, target) under its
# is_genuine_target precondition (established because the else-branch of
# `not is_genuine_target(target)` makes is_genuine_target(target) hold). No loop
# / fold / induction lemma is involved. If a faithful correct impl could NOT
# verify against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    if not is_genuine_target(target):
        passthrough = RetVal(ret.is_none, ret.unit)  # type: RetVal
        return passthrough
    else:
        converted = RetVal(False, convert_unit(ret.unit, target))  # type: RetVal
        return converted"""

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: read BOTH half-permission fields (ret.is_none,
# ret.unit) and re-derive the domain fact the Requires grants, then reach a
# normal (non-raising) return via the gold logic. If the Requires were vacuous /
# over-strong the impl could not both consume the half-permissions, observe the
# domain invariant, and return => PRECOND-TOO-STRONG. Source: the two Requires.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: both half-permission fields are readable and the domain
    # fact the Requires grants is observable; a normal return is reachable.
    Assert(ret.is_none == (ret.unit == NO_UNIT()))
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        Assert(Implies(ret.is_none, ret.unit == NO_UNIT()))
        return RetVal(ret.is_none, ret.unit)"""

# ===========================================================================
# (3) FRAME-MUTATION — write to the read-only input `ret` (reject). MANDATORY.
# finalize_return holds only Acc(ret.unit, 1/2). The write `ret.unit = ret.unit`
# is value-NEUTRAL (it stores the same id back) and well-typed, yet a WRITE needs
# FULL permission. With only the half-permission the Requires grants, Nagini
# rejects for INSUFFICIENT PERMISSION. The gold decision is kept VERBATIM after
# the write, so the rejection is attributable to the write, not a spec change.
# A byte-fuzzer never thinks to mutate a read-only input — this is the #1 class.
# ===========================================================================
_IMPL_FRAME = """    # FRAME MUTATION: write back into the read-only half-permission input.
    ret.unit = ret.unit
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)"""

# ===========================================================================
# (4) ALWAYS-CONVERT (pre-patch bug) — convert whenever target is not the
# UNSPECIFIED sentinel (reject). This is model_prepatch.py's impl exactly: it
# fails to exclude TARGET_NOVALUE, so on the `-> None` target it calls
# convert_unit(ret.unit, TARGET_NOVALUE) whose precondition is_genuine_target
# (target) does NOT hold => the call site is rejected. This IS the discriminating
# bug (the real None.to(None) misuse). expect=reject.
# ===========================================================================
_IMPL_ALWAYS_CONVERT = """    if target != TARGET_UNSPECIFIED():
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)"""

# ===========================================================================
# (5) ALWAYS-PASSTHROUGH — never convert, even on a genuine unit target (reject).
# Pass the value through on every target. On a genuine unit target this violates
# the CONVERT clause: the postcondition pins Result().unit == convert_unit(
# ret.unit, target) == target, but here Result().unit == ret.unit which is the
# SOURCE unit (!= target in general). expect=reject.
#
# Written as an UNGUARDED single return, NOT as `if True: passthrough / else:
# convert`. The two are semantically the same impl -- a constant-true guard is
# not control flow -- but nagini type-checks with mypy in strict mode BEFORE it
# translates, and mypy reports the unreachable else arm as `Type error:
# dead.code`. Nagini then exits 1 -- its REJECTION code -- having printed
# `Translation failed` and never having reached Viper. That is a hollow pass, not
# a rejection: nagini is in the complement of pbt.WITNESS_REQUIRED precisely
# because Viper discharges the postcondition itself, so "did not verify" ALONE is
# this backend's whole reject argument, and a rival that fails to TRANSLATE
# certifies no spec strength whatever. Measured on this cell: the guarded form
# failed the front end in 7.2s at rival line 135 with no Viper verdict; the
# unguarded form below is refuted BY VIPER on the CONVERT clause in 11.5s. Keep
# this region free of any statically dead branch.
# ===========================================================================
_IMPL_ALWAYS_PASS = """    return RetVal(ret.is_none, ret.unit)"""

# ===========================================================================
# (6) WRONG-UNIT ON CONVERT (value double-mask) — convert branch keeps the SOURCE
# unit instead of the target (reject). The branch DECISION is correct (it only
# fires on a genuine target) and the result is a genuine quantity (is_none ==
# False), but it returns ret.unit instead of convert_unit(ret.unit, target).
# The CONVERT clause pins Result().unit == convert_unit(ret.unit, target) ==
# target; ret.unit != target in general, so it is rejected. Isolates the
# `Result().unit == target` sub-clause (without touching the precondition guard).
# expect=reject.
# ===========================================================================
_IMPL_WRONG_UNIT = """    if is_genuine_target(target):
        return RetVal(False, ret.unit)
    else:
        return RetVal(ret.is_none, ret.unit)"""

# ===========================================================================
# (7) CONTROL-FLOW / is_none ON PASS-THROUGH — force a genuine (non-none) result
# on the pass-through branch (reject). On the NON-genuine branch (including the
# `-> None` target == TARGET_NOVALUE) the value must pass through UNTOUCHED: the
# PASS-THROUGH clause pins Result().is_none == ret.is_none. Here the impl returns
# RetVal(False, ret.unit), forcing is_none == False. When ret.is_none is True
# (the F2P scenario: a `-> None` function returns the None object), this violates
# Result().is_none == ret.is_none. This is the value-abstraction-visible analogue
# of the real bug "the result is no longer None": the F2P test asserts
# `solarx is None`. expect=reject.
#
# NOTE the RetVal(False, ret.unit) constructor is admissible: is_none == False
# imposes NO constraint on the unit field, so the constructor's
# Requires(Implies(is_none, unit == NO_UNIT())) holds vacuously and the rejection
# lands on the PASS-THROUGH postcondition clause, not the constructor.
# ===========================================================================
_IMPL_CF_NOTNONE = """    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(False, ret.unit)"""

# ===========================================================================
# (8) NON-VACUITY CONTROL for the impl site — Assert(False) (reject).
# Every reject case above concludes from "Viper turned this rival down", and there
# is one way that conclusion can be hollow even with a genuine Viper verdict: if
# the impl site were UNREACHABLE -- an unsatisfiable precondition, or a guard no
# input can satisfy -- then the postconditions are discharged vacuously and a
# rival can be "rejected" (or verify) for reasons that say nothing about the spec.
# Assert(False) is the control that decides it, and it is the only case here whose
# INFORMATIVE outcome is the one it is expected to produce:
#
#   Assert(False) FAILS   => the site is REACHABLE. The obligations at that site
#                            are real, so every rejection above is real.  <-- want
#   Assert(False) VERIFIES => no input reaches the site. finalize_return's two
#                            Requires (Acc(ret.*,1/2) + the domain fact
#                            ret.is_none == (ret.unit == NO_UNIT())) are jointly
#                            unsatisfiable and the whole battery is vacuous
#                            => PRECOND-TOO-STRONG, hence kind=admissibility.
#
# Distinct from (2) admissibility-readonly-retval, which cannot detect this: a
# contradictory precondition makes an expect="verify" case verify VACUOUSLY, so it
# passes either way. Only a claim that must FAIL separates the two worlds.
# The gold decision is kept verbatim after the Assert so that, in the reachable
# world, the Assert is the sole reason for the rejection. expect=reject.
# ===========================================================================
_IMPL_NONVACUITY = """    # NON-VACUITY CONTROL: must FAIL, proving this site is reachable.
    Assert(False)
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the pass-through (NON-"
                     "genuine) branch is tested first and both returns are staged "
                     "through named locals (RetVal locals). On the else-branch "
                     "is_genuine_target(target) holds, so the convert_unit precondition "
                     "is met; both branches produce the same observable RetVal as gold. "
                     "No loop / fold / induction lemma is introduced. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-retval",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that BOTH half-permission fields "
                     "(ret.is_none, ret.unit) are readable and the domain fact "
                     "ret.is_none == (ret.unit == NO_UNIT()) the Requires grants is "
                     "observable, then reaches a normal non-raising return via the gold "
                     "decision for an in-domain (F2P-shaped) input. If either Requires "
                     "were vacuous or over-strong the impl could not both consume the "
                     "permissions and return => PRECOND-TOO-STRONG. Source: the two "
                     "Requires (Acc(ret.*,1/2) + the domain fact).",
    },
    {
        "id": "frame-mutation-write-ret-unit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which the wrapper wrote back into the "
                      "wrapped function's return value object (e.g. mutated return_ in "
                      "place rather than constructing a new converted Quantity) would "
                      "corrupt the object the caller of the decorated function still "
                      "holds. The gold tail only READS return_ (its annotation decision) "
                      "and calls return_.to(...) which returns a NEW Quantity, never "
                      "mutating return_; the F2P/P2P tests observe the returned object "
                      "(`solarx is None`, `solarx.unit == u.deg`) and a mutating wrapper "
                      "could not faithfully reproduce pass-through (it would alter the "
                      "very object the assertions inspect). So a mutating patch would "
                      "not faithfully resolve test_return_annotation_none.",
        "rationale": "finalize_return holds only Acc(ret.unit, 1/2). The value-neutral "
                     "write ret.unit = ret.unit needs FULL permission => Nagini rejects "
                     "for INSUFFICIENT PERMISSION. Source: the permission system + the "
                     "Acc(ret.*,1/2) Requires. The gold decision is kept verbatim after "
                     "the write so the rejection is attributable to the write.",
    },
    {
        "id": "always-convert-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ALWAYS_CONVERT),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py / the real "
                      "guard `return_annotation is not inspect.Signature.empty`): it "
                      "excludes only the unspecified sentinel, so on a `-> None` "
                      "function it attempts return_.to(None) i.e. None.to(None), which "
                      "raises AttributeError at runtime. The F2P test "
                      "test_return_annotation_none calls a `-> None` decorated function "
                      "and asserts the result is None; the pre-patch wrapper raises "
                      "instead, so this faithful patch does NOT resolve.",
        "rationale": "On target == TARGET_NOVALUE the guard target != TARGET_UNSPECIFIED "
                     "is True, so the impl calls convert_unit(ret.unit, TARGET_NOVALUE) "
                     "whose precondition is_genuine_target(target) does NOT hold => the "
                     "call site is rejected. Source: convert_unit's precondition (the "
                     "load-bearing guard the fix installs). This matches G-DIFF.",
    },
    {
        "id": "always-passthrough-never-convert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ALWAYS_PASS),
        "refinement": "A faithful real patch that dropped the conversion entirely "
                      "(`return return_` for every annotation) would never convert a "
                      "genuine unit target. test_return_annotation (a P2P, `-> u.deg`) "
                      "asserts solarx.unit is u.deg; an always-passthrough wrapper "
                      "returns the source unit (u.arcsec) unconverted, so that test "
                      "FAILS and the patch does not resolve.",
        "rationale": "Passes the value through on EVERY target, as one unguarded "
                     "return (no constant-true guard: mypy rejects the dead else arm as "
                     "`Type error: dead.code` and nagini then exits 1 without Viper ever "
                     "reaching a verdict, which on this backend would score as a "
                     "rejection while proving nothing). On a genuine unit target the "
                     "result unit is ret.unit (the SOURCE) rather than convert_unit("
                     "ret.unit, target) == target, so the CONVERT clause fails. Viper: "
                     "\"Postcondition of finalize_return might not hold. Assertion "
                     "Implies(is_genuine_target(target), ((not Result().is_none) and "
                     "(Result().unit == convert_unit(ret.unit, target)))) might not "
                     "hold.\" at model.py:127-129 in 11.5s. Source: the convert "
                     "(is_genuine_target) postcondition clause — the SAME clause under "
                     "an added Requires(not ret.is_none), which discharges the "
                     "`not Result().is_none` sub-clause trivially, is still refuted, so "
                     "the unit sub-clause named here is genuinely load-bearing. "
                     "Non-vacuity control: Assert(False) at this site FAILS (\"Assert "
                     "might fail. Assertion False might not hold.\"), so the region is "
                     "reachable and the rejection is real, not a vacuous path.",
    },
    {
        "id": "wrong-unit-on-convert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_WRONG_UNIT),
        "refinement": "A faithful real patch that returned the wrapped value unchanged "
                      "on the convert branch (e.g. `return return_` after deciding to "
                      "convert, or `return_.to(return_.unit)` keeping the source unit) "
                      "would leave a `-> u.deg` function's result in u.arcsec. "
                      "test_return_annotation asserts solarx.unit is u.deg, so the "
                      "patch does NOT resolve.",
        "rationale": "The decision is correct (only fires on a genuine target) and the "
                     "result is a genuine quantity (is_none == False), but it returns "
                     "ret.unit (the SOURCE unit) instead of convert_unit(ret.unit, "
                     "target) == target. The CONVERT clause pins Result().unit == "
                     "target; ret.unit != target in general, so it is rejected. Source: "
                     "the Result().unit == convert_unit(...) sub-clause.",
    },
    {
        "id": "control-flow-notnone-on-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_CF_NOTNONE),
        "refinement": "A faithful real patch that, on the pass-through branch, returned "
                      "a fabricated non-None object instead of `return return_` would "
                      "break a `-> None` function: the F2P test_return_annotation_none "
                      "asserts `solarx is None`, but the patched wrapper would yield a "
                      "non-None object. So the patch does NOT resolve the F2P.",
        "rationale": "On the NON-genuine branch (incl. TARGET_NOVALUE, the `-> None` "
                     "case) the PASS-THROUGH clause pins Result().is_none == ret.is_none. "
                     "Here the impl returns RetVal(False, ret.unit), forcing is_none == "
                     "False; when ret.is_none is True (the no-value object the F2P "
                     "returns) this violates Result().is_none == ret.is_none. The "
                     "RetVal(False, ...) constructor is admissible (is_none False "
                     "imposes no unit constraint), so the rejection lands on the "
                     "PASS-THROUGH postcondition clause. Source: the not-genuine "
                     "(pass-through) is_none sub-clause — the F2P discriminator.",
    },
    {
        "id": "nonvacuity-impl-site-reachable",
        "kind": "admissibility",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NONVACUITY),
        "rationale": "Non-vacuity control for the site every reject case above is "
                     "judged at. Assert(False) with the gold decision kept verbatim "
                     "after it. Viper: \"Assert might fail. Assertion False might not "
                     "hold.\" — the assert FAILS, so the impl site is REACHABLE under "
                     "finalize_return's two Requires (Acc(ret.*,1/2) + the domain fact "
                     "ret.is_none == (ret.unit == NO_UNIT())) and the obligations "
                     "discharged there are not vacuous. Were it to VERIFY instead, no "
                     "input would reach the site, the postconditions would hold "
                     "vacuously, and every rejection in this battery would prove "
                     "nothing => PRECOND-TOO-STRONG. Case (2) cannot substitute: a "
                     "contradictory precondition makes an expect=verify case verify "
                     "vacuously, so only a claim that must FAIL separates the two "
                     "worlds. Source: the precondition's satisfiability at the impl "
                     "site.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom consumed inside
# any Ensures; the axioms region of model.py is empty). The two deep-model
# references (convert_unit == real Quantity.to; the finalize_return decision ==
# the real quantity_input wrapper post-fix) are A-references already validated
# against the REAL astropy callees in-container by axiom_check.py (G-AX): it
# converts a genuine unit target (.unit == target over 8 (quantity, target)
# pairs), passes through a `-> None` target (result is None / unit unchanged) and
# an unspecified target (unit unchanged), importing only astropy.units + stdlib
# with the gold patch applied. That established real-callee check IS the axiom
# lane for this instance; re-encoding it as a Docker probe would duplicate, not
# strengthen, it. See 'assessment' in the structured return.
AXIOM_TESTS = []
