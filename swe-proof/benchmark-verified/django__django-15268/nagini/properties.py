"""PBT manifest for django__django-15268 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  commutes_through(self_op: Operation, other: Operation) -> bool
    Requires: Acc(self_op.kind,1/2) and Acc(self_op.model_id,1/2)   -- READ-ONLY
              Acc(other.kind,1/2)   and Acc(other.model_id,1/2)     -- READ-ONLY
              is_constraint_alteration(self_op.kind)                -- self is an alter
    Ensures (frame): the four 1/2 perms are RETURNED unchanged.
    Ensures (DECISION, load-bearing):
        Result() == alter_commutes_through(self_op.kind, self_op.model_id,
                                           other.kind, other.model_id)
      plus three pinned consequences:
        - not touches_model(other,self)                  => Result()   (clause 1)
        - is_constraint_alteration(other) & other!=self  => Result()   (clause 2)
        - touches_model(other,self) & other==self        => not Result() (no same-family)

  pair_collapses_through(first, between, second) -> bool
    Requires: the three ops are read-only (1/2); first/second a same-family pair on
              one model; between a constraint-altering op on that model.
    Ensures (frame): the six 1/2 perms returned unchanged.
    Ensures (load-bearing):
        Result() == alter_commutes_through(between.kind, between.model_id,
                                            second.kind, second.model_id)
        Result() == (between.kind != first.kind)        -- the optimizer observable

This models the gold AlterTogetherOptionOperation.can_reduce_through fix: a
constraint-altering operation may additionally commute through a SAME-MODEL
neighbour that is itself a constraint-altering operation of a DIFFERENT family.
The four-step [clear-unique, clear-index, set-unique, set-index] sequence then
collapses to [set-unique, set-index] (the F2P observable).

GROUNDED-ORACLE NOTE: the postcondition oracle alter_commutes_through(...) is
GROUNDED in the arguments -- it is a flat @Pure boolean expression over the four
ints kind/model_id (NOT an opaque answer-key, NOT a recursive fold). There is no
WRONG echo a rival can return: `return alter_commutes_through(...)` is the honest
cheapest CORRECT impl (positive control below), and any wrong constant/echo fails
the postcondition. So the uniqueness lane is NOT about echo; it is about whether a
rival can be right on the F2P four-step domain while DIVERGING on a discriminating
sub-domain -- specifically the same-model different-family case the gold newly
allows (clause 2), the same-model same-family case the rule must keep forbidding
(clause 4), and the read-only frame the permission system must protect.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty;
meta.axioms == [], deep_model_references == []). The changed decision is a pure
boolean computation modelled DEEPLY (is_constraint_alteration / touches_model /
base_commutes_through / alter_commutes_through). references_model and
super().can_reduce_through are themselves trivial equality tests, not axiomatized.
There is no real callee to fuzz and no axiom Requires-domain to contain. Hence
AXIOM_TESTS = []  (axiom lane vacuous, consistent with G-AX status "vacuous").

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside a # impl-start/# impl-end region (one per modeled function). The frozen
spec (axioms/pure/pre/post-conditions/signatures) is never touched, so same_spec
holds for every spec case by construction.
"""
from pathlib import Path

INSTANCE = "django__django-15268"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors -- the FULL impl region of each modeled function (each present
# exactly once in _BASE; verified by the count check below).
# ---------------------------------------------------------------------------
_CT_IMPL = (
    "    if not touches_model(other.model_id, self_op.model_id):\n"
    "        return True\n"
    "    return is_constraint_alteration(other.kind) and "
    "other.kind != self_op.kind\n"
)
_PC_IMPL = (
    "    Assert(touches_model(second.model_id, between.model_id))\n"
    "    res = is_constraint_alteration(second.kind) and \\\n"
    "        second.kind != between.kind\n"
    "    return res\n"
)

for _a in (_CT_IMPL, _PC_IMPL):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- branch reorder + local-variable reshape of
# commutes_through. The gold early-return `if not touches: return True` is folded
# into a single boolean OR over a named local; semantically identical to the gold
# decision (base rule OR different-family-alteration). The spec helpers are flat
# @Pure boolean expressions (no recursion / no fold), so there is NO induction
# lemma to discharge -- a reshape verifies directly against Result()==
# alter_commutes_through. MUST verify; else the postcondition is over-fit to the
# early-return FORM => SPEC-TOO-STRONG.
_POS_CT_RESHAPE = _swap(
    _BASE, _CT_IMPL,
    "    base = not touches_model(other.model_id, self_op.model_id)\n"
    "    diff_family = is_constraint_alteration(other.kind) and \\\n"
    "        other.kind != self_op.kind\n"
    "    decision = base or diff_family  # type: bool\n"
    "    return decision\n",
)

# (5b) POSITIVE CONTROL -- the cheapest HONEST impl of commutes_through. The
# oracle alter_commutes_through(...) is GROUNDED in the arguments (a flat @Pure
# expression over the four ints), so directly returning it is a correct,
# fully-grounded implementation, NOT an ungrounded-oracle echo. MUST verify (the
# postcondition is literally Result()==alter_commutes_through(...)); else
# SPEC-TOO-STRONG. Also demonstrates the spec is not echo-vulnerable: any WRONG
# constant/echo would fail the postcondition.
_POS_CT_DIRECT = _swap(
    _BASE, _CT_IMPL,
    "    return alter_commutes_through(\n"
    "        self_op.kind, self_op.model_id, other.kind, other.model_id)\n",
)

# (5c) POSITIVE CONTROL -- reshape of pair_collapses_through. The gold inlines the
# in-between commute decision; this variant keeps the SAME framing Assert (the
# proof obligation that `second` touches `between`'s model, needed to drop the
# base clause) but reshapes the boolean into a single returned expression rather
# than a named local. Semantically identical; MUST verify; else SPEC-TOO-STRONG.
_POS_PC_RESHAPE = _swap(
    _BASE, _PC_IMPL,
    "    Assert(touches_model(second.model_id, between.model_id))\n"
    "    return is_constraint_alteration(second.kind) and \\\n"
    "        between.kind != second.kind\n",
)

# (6) ADMISSIBILITY -- a call on a fresh, F2P-shaped input pair: a
# set-uniqueness op (kind=FAMILY_UNIQUE=0, model 7) commuting through a
# set-index op (kind=FAMILY_INDEX=1, model 7) on the SAME model -- exactly the
# different-family same-model case the four-step sequence collapses on. Both ops
# are freshly constructed (full perm available, so the 1/2 Requires is
# establishable) and the callee's self_op is a constraint-alteration (kind 0 >=
# 0). MUST verify; else the precondition rejects a normal F2P input =>
# PRECOND-TOO-STRONG.
#
# TERMINATION NOTE (why this probe is hosted in pair_collapses_through, not in
# commutes_through itself): the spec now carries a termination obligation, and
# MustTerminate levels must STRICTLY DECREASE from caller to callee. A probe
# spliced into commutes_through would be a *self*-call, Requires(MustTerminate(6))
# invoking Requires(MustTerminate(6)) -- never strictly decreasing at any level,
# so it is unprovable by construction rather than because the precondition is too
# strong ("Obligation leak check failed. Callee commutes_through might not take
# all unsatisfied obligations from the caller."). Hosting the identical probe in
# pair_collapses_through (level 10 -> level 6, and level 10 -> level 2 for the two
# Operation() constructions) gives the call the room the obligation requires. The
# claim under test is unchanged and unweakened: the same fresh F2P-shaped pair,
# the same call, and the same two result-property asserts -- only the enclosing
# frame differs, which is a fact about the proof, not about the property.
_POS_ADMISS = _swap(
    _BASE, _PC_IMPL,
    "    a = Operation(FAMILY_UNIQUE, 7)\n"
    "    b = Operation(FAMILY_INDEX, 7)\n"
    "    r = commutes_through(a, b)\n"
    "    Assert(r == alter_commutes_through(a.kind, a.model_id, b.kind, b.model_id))\n"
    "    Assert(r)  # different-family same-model => commutes (clause 2)\n"
    "    Assert(touches_model(second.model_id, between.model_id))\n"
    "    res = is_constraint_alteration(second.kind) and \\\n"
    "        second.kind != between.kind\n"
    "    return res\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). self_op/other are
# read-only at 1/2. This rival WRITES `other.kind = self_op.kind` before deciding,
# attempting to vacuously satisfy the decision by NORMALIZING the neighbour's
# family (making other look same-family so a base-only impl is "correct"). Under
# Acc(other.kind,1/2) a store needs FULL permission, so it MUST be rejected for
# INSUFFICIENT PERMISSION (not a value mismatch). The decision returned is still
# the gold body, so the rejection is attributable solely to the write.
_RIVAL_FRAME = _swap(
    _BASE, _CT_IMPL,
    "    other.kind = self_op.kind\n"
    "    if not touches_model(other.model_id, self_op.model_id):\n"
    "        return True\n"
    "    return is_constraint_alteration(other.kind) and "
    "other.kind != self_op.kind\n",
)

# (1b) FRAME MUTATION on pair_collapses_through -- same #1 class, second function.
# Writes `between.kind = first.kind` (normalize the in-between step to the pair's
# family). Under Acc(between.kind,1/2) this store needs full permission and MUST
# be rejected for INSUFFICIENT PERMISSION.
_RIVAL_FRAME_PC = _swap(
    _BASE, _PC_IMPL,
    "    between.kind = first.kind\n"
    "    Assert(touches_model(second.model_id, between.model_id))\n"
    "    res = is_constraint_alteration(second.kind) and \\\n"
    "        second.kind != between.kind\n"
    "    return res\n",
)

# (3a) PARTIAL-DOMAIN -- base rule only (== model_prepatch.py for this function).
# Returns `not touches_model(other, self)`: the pre-patch behaviour with NO
# different-family allowance. Correct on every non-touching neighbour (clause 1)
# and on same-model same-family (clause 4, both give False), but WRONG on the
# same-model DIFFERENT-family case (clause 2 requires True; base-only gives
# False). The postcondition Result()==alter_commutes_through cannot be closed on
# that sub-domain.
_RIVAL_BASE_ONLY = _swap(
    _BASE, _CT_IMPL,
    "    return not touches_model(other.model_id, self_op.model_id)\n",
)

# (3b) PARTIAL-DOMAIN -- over-permissive: commute through ANY same-model
# constraint-alteration, dropping the `other.kind != self_op.kind` family-distinct
# guard. Correct on the F2P four-step sequence (every in-between neighbour there is
# a DIFFERENT family) but WRONG on a same-model SAME-family neighbour (clause 4
# requires not Result(); this returns True). Diverges exactly on the case the rule
# must keep forbidding.
_RIVAL_OVERPERMISSIVE = _swap(
    _BASE, _CT_IMPL,
    "    if not touches_model(other.model_id, self_op.model_id):\n"
    "        return True\n"
    "    return is_constraint_alteration(other.kind)\n",
)

# (3c) PARTIAL-DOMAIN on pair_collapses_through -- drop the family-distinct guard.
# Returns is_constraint_alteration(second.kind) (always True under the Requires),
# so the pair ALWAYS collapses regardless of whether `between` is a different
# family. Correct on the F2P cross-family in-between step but WRONG whenever
# between.kind == first.kind (clause Result()==(between.kind != first.kind) then
# requires False, but this returns True).
_RIVAL_PC_OVERPERMISSIVE = _swap(
    _BASE, _PC_IMPL,
    "    Assert(touches_model(second.model_id, between.model_id))\n"
    "    res = is_constraint_alteration(second.kind)  # type: bool\n"
    "    return res\n",
)

# (3d) PARTIAL-DOMAIN -- constant True (the maximal over-collapse). The single
# cheapest spec-too-weak attack: ignore the inputs entirely. Correct only where
# the answer happens to be True; WRONG on same-model same-family (commutes_through)
# / on same-family between (pair_collapses_through). Fails the main pin and the
# clause-4 / observable Implies. Cheap supporting near-miss, still carries a real
# refinement (a patch that always reduces would over-collapse same-family pairs).
_RIVAL_CT_TRUE = _swap(
    _BASE, _CT_IMPL,
    "    res = True  # type: bool\n    return res\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-ct-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_CT_RESHAPE,
     "rationale": "structurally-different but CORRECT impl of commutes_through "
                  "(early-return folded into a single boolean OR over named locals; "
                  "the spec helpers are flat @Pure expressions so no induction lemma "
                  "is needed). Must verify against Result()==alter_commutes_through; "
                  "else the postcondition is over-fit to the early-return FORM => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-control-ct-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_CT_DIRECT,
     "rationale": "the oracle alter_commutes_through(...) is GROUNDED in the four int "
                  "args (a flat @Pure expression), so `return alter_commutes_through(...)` "
                  "is the honest cheapest CORRECT impl, not an ungrounded echo. Must "
                  "verify (postcondition is literally Result()==alter_commutes_through); "
                  "else SPEC-TOO-STRONG. Also shows there is no WRONG echo to build."},
    {"id": "pos-control-pc-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_PC_RESHAPE,
     "rationale": "structurally-different but CORRECT impl of pair_collapses_through, "
                  "keeping the framing Assert(touches_model(second,between)) that drops "
                  "the base clause and reshaping into a single returned boolean "
                  "(between.kind != second.kind == between.kind != first.kind under the "
                  "Requires). Must verify; else SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a call on a fresh F2P-shaped input pair (set-uniqueness op "
                  "commuting through a set-index op on the SAME model -- the different-"
                  "family same-model case the four-step sequence collapses on) must "
                  "establish the 1/2 Requires and is_constraint_alteration(self), and "
                  "the result-property asserts (Result()==alter_commutes_through and "
                  "Result() true). If the precondition rejects this normal input => "
                  "PRECOND-TOO-STRONG. Hosted in pair_collapses_through (level 10) "
                  "rather than spliced into commutes_through (level 6), because the "
                  "spec's MustTerminate levels must strictly decrease caller->callee: "
                  "a self-call at 6->6 leaks the obligation by construction and would "
                  "report a spurious PRECOND-TOO-STRONG that is really a fact about "
                  "level arithmetic, not about the precondition. The probed claim is "
                  "identical; only the enclosing frame supplies the level room."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-other-kind", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: can_reduce_through "
                   "inspects the neighbour operation's concrete class via isinstance / "
                   "type(operation) -- it never REWRITES the neighbour's class or its "
                   "target model. A patch that mutated the operation it is merely "
                   "deciding about would corrupt the migration optimizer's operation "
                   "list; there is no resolving patch that does this, so a verifying "
                   "rival here is a pure verify-not-resolve artifact (vacuous "
                   "satisfaction by normalizing the neighbour's family).",
     "rationale": "MANDATORY frame-mutation probe. `other.kind = self_op.kind` writes "
                   "through a 1/2 (read-only) reference and MUST fail for INSUFFICIENT "
                   "PERMISSION (a store needs full Acc(other.kind)), NOT a value "
                   "mismatch; the returned decision is still the gold body so the "
                   "rejection is attributable to the write. Rejection source: the "
                   "PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (frame protection "
                   "hollow)."},
    {"id": "frame-mutate-between-kind", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_PC,
     "refinement": "same as the commutes_through frame probe, on the optimizer-"
                   "consequence function: the optimizer's left-reduction guard reads "
                   "each in-between operation's reduce/can_reduce_through decision; it "
                   "never rewrites the in-between operation's family. No resolving patch "
                   "mutates the operation it inspects, so a verifying rival is a pure "
                   "verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe (second function). `between.kind = "
                   "first.kind` writes through a 1/2 reference and MUST fail for "
                   "INSUFFICIENT PERMISSION. Rejection source: the PERMISSION SYSTEM. If "
                   "it verified => SPEC-TOO-WEAK."},
    {"id": "weak-base-rule-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BASE_ONLY,
     "refinement": "this is EXACTLY the pre-patch behaviour (== model_prepatch.py): "
                   "reduce returning `not operation.references_model(self.name, "
                   "app_label)` with NO can_reduce_through different-family override. "
                   "A faithful patch keeping the base rule only never commutes a "
                   "constraint-alteration past a same-model neighbour of a different "
                   "family, so the four-step AlterUnique/AlterIndex sequence is NOT "
                   "reduced and the autodetector F2P tests (which now expect the "
                   "collapsed two-operation sequence) FAIL -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition Result()==alter_commutes_through "
                   "(and clause 2 Implies(is_constraint_alteration(other) & other!=self, "
                   "Result())). On a same-model different-family neighbour the base-only "
                   "result is False while alter_commutes_through is True, so the verifier "
                   "cannot close the postcondition. If it verified => SPEC-TOO-WEAK (the "
                   "different-family allowance would be unenforced)."},
    {"id": "weak-overpermissive-samefamily", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERPERMISSIVE,
     "refinement": "dropping the `other.kind != self_op.kind` guard lets a "
                   "constraint-alteration commute past a SAME-MODEL SAME-FAMILY "
                   "neighbour. A faithful patch dropping `type(operation) is not "
                   "type(self)` from can_reduce_through would reduce e.g. two "
                   "AlterUniqueTogether on the same model that must NOT be commuted "
                   "past each other (they are ordered constraint passes on the same "
                   "family), corrupting the migration and failing the PASS_TO_PASS "
                   "optimizer/autodetector invariants -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition clause Implies(touches_model(other,"
                   "self) and other.kind==self_op.kind, not Result()) (clause 4). On a "
                   "same-model same-family neighbour this rival returns "
                   "is_constraint_alteration(other)==True while the spec requires not "
                   "Result(); the verifier cannot close it. If it verified => "
                   "SPEC-TOO-WEAK (same-family neighbours would wrongly commute)."},
    {"id": "weak-pc-overpermissive", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PC_OVERPERMISSIVE,
     "refinement": "the optimizer would collapse the redundant pair even when the "
                   "in-between step is the SAME family as the pair, i.e. it would "
                   "reduce a sequence that must stay un-reduced. A faithful patch "
                   "making the pair always collapse over-reduces same-family "
                   "sequences and fails the autodetector/optimizer P2P invariants "
                   "-- verify-not-resolve.",
     "rationale": "rejection source: the postcondition Result()==(between.kind != "
                   "first.kind). This rival returns is_constraint_alteration(second.kind) "
                   "(True under the Requires) regardless of between's family; when "
                   "between.kind==first.kind the spec requires False, so the verifier "
                   "cannot close it. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-ct-constant-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CT_TRUE,
     "refinement": "always-commute is the maximal over-collapse: a patch whose "
                   "can_reduce_through unconditionally returns True would reduce every "
                   "neighbouring operation pair, including same-model same-family pairs "
                   "and ordering-sensitive sequences, breaking the autodetector F2P "
                   "(which checks index/unique_together also trigger on ordering "
                   "changes and that removed fields / renamed fields are handled in "
                   "order) -- verify-not-resolve.",
     "rationale": "cheap supporting near-miss (constant). rejection source: the main pin "
                   "Result()==alter_commutes_through AND clause 4 Implies(touches_model & "
                   "same family, not Result()): a same-model same-family neighbour makes "
                   "alter_commutes_through False while this returns True. If it verified "
                   "=> SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- VACUOUS. There is no @ContractOnly axiom and no A-reference deep
# model in this bundle (meta.axioms == [], deep_model_references == [],
# G-AX status "vacuous"). The changed decision is a pure boolean computation
# modelled DEEPLY in the pure region; references_model and super().can_reduce_through
# are trivial equality tests, not axiomatized callees. There is no real callee to
# fuzz for soundness and no axiom Requires-domain to check for containment.
# ===========================================================================

AXIOM_TESTS = []  # type: list
