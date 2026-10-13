"""properties.py — PBT falsification manifest for django__django-13406.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    attach_description(rs: ResultSet, value: LookupDescription) -> None

= the gold-patched `QuerySet.query` setter
(`django/db/models/query.py:211-213`):

    @query.setter
    def query(self, value):
        if value.values_select:                 # <- the two added gold lines
            self._iterable_class = ValuesIterable
        self._query = value

with `QuerySet -> ResultSet` (touched fields: `producer_tag:int` =
ModelIterable<->0 / ValuesIterable<->1; `description:Optional[LookupDescription]`
= the stored `_query`) and `sql.Query -> LookupDescription` (one touched
read-only field `value_field_count:int` = count of selected value-fields;
`bool(values_select) <-> count > 0`).

The load-bearing contract:

    Requires(Acc(rs.producer_tag)); Requires(Acc(rs.description))
    Requires(Acc(value.value_field_count, 1 / 2))            # READ-ONLY input
    Ensures (Acc(rs.producer_tag)); Ensures(Acc(rs.description))
    Ensures (Acc(value.value_field_count, 1 / 2))            # returns the read perm
    Ensures (rs.description is value)                        # (C1) identity store
    Ensures (value.value_field_count == Old(value.value_field_count))  # (C2) read-only
    Ensures (Implies(value.value_field_count > 0,            # (C3) the FIX:
                     rs.producer_tag == PRODUCES_VALUE_MAPPINGS))  # value-bearing -> value-mapping
    Ensures (Implies(value.value_field_count == 0,           # (C4) preserve on empty
                     rs.producer_tag == Old(rs.producer_tag)))

What the spec defends, and the attacks it must survive:

  * The discriminator is GROUNDED entirely in the argument `value.value_field_count`
    (an int >= 0). There is NO opaque @Pure answer-key / exact-marker in the
    contract that an impl could echo without doing the work (axioms == [], pure
    region empty). So there is no "echo a wrong oracle" SPEC-TOO-WEAK shortcut —
    the honest cheapest impl (pos-control-direct) IS the work. (Hence no
    ungrounded-echo reject case; see 'assessment'.)

  * Two independent behaviours are pinned, exactly the bug + its complement:
      (C3) value-bearing -> value-mapping producer (tag 1). This is THE fix;
           model_prepatch.py (stores `description` only, never switches) FAILS
           exactly C3 at count>0. Rival `partial-prepatch-no-switch` reproduces
           that bug; rival `partial-off-by-one` (switch only when count>1) is a
           subtler partial-domain miss on the count==1 sub-domain.
      (C4) empty selection -> producer preserved. Rival `partial-uncond-switch`
           (switch unconditionally) is correct on count>0 but FAILS C4 at
           count==0 with Old(producer_tag) != 1.
      (C1) the description is stored by identity. Rival `drop-store` omits the
           store and FAILS C1.

  * `value.value_field_count` is held READ-ONLY (`Acc(..., 1/2)`). The MANDATORY
    attack is FRAME MUTATION (`frame-mutate-count`): an impl that WRITES to
    `value.value_field_count` (e.g. to vacuously satisfy C3 by zeroing the count)
    MUST fail for INSUFFICIENT PERMISSION, not for a wrong value.

  * TERMINATION. The spec carries `Requires(MustTerminate(6))` on
    `attach_description` and `Requires(MustTerminate(2))` on both constructors
    (level 2 < 6 leaves the room a caller needs to build its arguments; at level 1
    `list.__init__`-style callees leak). Without it Nagini proves only PARTIAL
    correctness: C1-C4 are claimed of runs that REACH the return, so an impl that
    never returns satisfies all four vacuously and VERIFIES while its faithful
    patch hangs. That is a property of the SPEC, so no property test can close it,
    and the two rivals `diverging-loop` (postconditions established, then an
    unbounded loop) and `diverging-self-call` (unconditional recursion) pin it:
    both were MEASURED to VERIFY against the obligation-free spec and to be
    rejected by the obligation system once it is present. `diverging-self-call` is
    the shape the admissibility case used to have — it was an accept-lane case
    asserting the spec ADMITS unbounded recursion, which is the hole itself.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY the impl body between `# impl-start` / `# impl-end`, so
`markers.same_spec` is GUARANTEED and a rejection comes from the POSTCONDITION
catching wrong behaviour (or the permission system), never a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P/P2P. The axiom lane re-runs the single
A-reference (the deep model == the REAL post-patch `QuerySet.query` setter) in
Docker (a faithful port of axiom_check.py) plus a caller-domain containment
probe.
"""
from pathlib import Path

INSTANCE = "django__django-13406"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark: the entire gold impl body (everything strictly INSIDE the
# # impl-start / # impl-end markers of attach_description). Every variant below
# is a _swap of this exact block, so the spec view (and same_spec) is preserved.
# ---------------------------------------------------------------------------
_GOLD_BODY = """    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Cheapest honest correct impl, structurally different: store the
# description FIRST, then apply the conditional switch. The store
# (rs.description = value) does not touch producer_tag, so reordering is
# behaviourally identical; C1/C3/C4/C2 all still hold. If this fails to verify
# the spec is over-fit to the gold statement order => SPEC-TOO-STRONG.
_POS_REORDER_BODY = """    rs.description = value
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS"""
_POS_REORDER = _swap(_BASE, _GOLD_BODY, _POS_REORDER_BODY)

# (5b) Structurally-different but CORRECT: an explicit two-armed if/else whose
# empty-selection arm re-asserts the preservation by writing producer_tag back
# to its own current value (a value-preserving self-assignment). Behaviourally
# identical (the else writes the same tag), so C3 (count>0 arm sets tag 1) and
# C4 (count==0 arm keeps Old) both hold. A branch-reshape, NOT a loop-direction
# flip (no induction lemma needed). If it fails => the spec is over-fit to the
# implicit-else shape => SPEC-TOO-STRONG.
_POS_EXPLICIT_ELSE_BODY = """    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    else:
        rs.producer_tag = rs.producer_tag
    rs.description = value"""
_POS_EXPLICIT_ELSE = _swap(_BASE, _GOLD_BODY, _POS_EXPLICIT_ELSE_BODY)

# (6) ADMISSIBILITY. Builds the F2P-shaped input — a freshly-created result set
# whose default producer yields model instances (ResultSet(PRODUCES_MODEL_INSTANCES))
# given a value-bearing description (LookupDescription(1), one selected
# value-field — the `values('name')` case of F2P test_annotation_values) — and
# then ASSERTS exactly the conjuncts of attach_description's Requires on it. The
# constructors establish full permission on the new objects' fields and
# value_field_count == 1 >= 0, so the precondition (Acc(rs.producer_tag),
# Acc(rs.description), Acc(value.value_field_count,1/2)) must be establishable
# for this normal input. If these Asserts cannot be discharged for an F2P-shaped
# input => PRECOND-TOO-STRONG.
#
# NOTE on the shape. This case previously discharged the same claim by making an
# actual self-call `attach_description(probe_rs, probe_desc)`. That formulation
# is UNSOUND as an admissibility probe now that the spec carries a termination
# obligation, and deliberately is not restored: the self-call is UNCONDITIONAL,
# so it is unbounded recursion (see the `diverging-self-call` reject case below),
# and MustTerminate levels are per-method constants — a self-call needs the
# callee's level to be strictly LESS than the caller's, which a single constant
# level (6) can never satisfy. So the old shape conflated two claims: "the
# precondition is establishable" (true, and what admissibility must test) with
# "the method may call itself unboundedly" (false). Asserting the Requires
# conjuncts directly tests the former without asserting the latter. Verified
# non-vacuous: splicing `Assert(False)` after these Asserts FAILS, so the probe
# path is reachable and the Asserts prove real facts rather than passing under an
# infeasible path condition.
_ADMISS_HEAD_NEW = (
    "    probe_rs = ResultSet(PRODUCES_MODEL_INSTANCES)\n"
    "    probe_desc = LookupDescription(1)\n"
    "    Assert(Acc(probe_rs.producer_tag) and Acc(probe_rs.description))\n"
    "    Assert(Acc(probe_desc.value_field_count, 1 / 2))\n"
    "    Assert(probe_desc.value_field_count == 1)\n"
    "    Assert(probe_rs.producer_tag == PRODUCES_MODEL_INSTANCES)\n"
    + _GOLD_BODY
)
_ADMISS = _swap(_BASE, _GOLD_BODY, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `value.value_field_count`
# is read-only (Acc(value.value_field_count, 1/2)). This rival WRITES to it
# (value.value_field_count = 0) before the guard, attempting to vacuously satisfy
# C3 (with count zeroed, count>0 is false so the producer need never switch) and
# C2 only via Old. A store to value.value_field_count needs FULL permission, so
# it MUST fail for INSUFFICIENT PERMISSION (not a value mismatch). Rejection
# source: the PERMISSION SYSTEM (the 1/2 read-only access forbids the store);
# C2 (value_field_count == Old) would additionally catch the value change if the
# permission somehow held. The rest of the body is the gold body verbatim so the
# failure is attributable solely to the write.
_FRAME_BODY = "    value.value_field_count = 0\n" + _GOLD_BODY
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (3a) PARTIAL-DOMAIN — the EXACT pre-patch bug (== model_prepatch.py): store the
# description but NEVER switch the producer. Correct on every empty-selection
# input (count==0 preserves the producer, C4 holds) but on every value-bearing
# input the producer is left at its prior value instead of PRODUCES_VALUE_MAPPINGS.
# Diverges only on the count>0 sub-domain. Rejection source: C3
# (Implies(value_field_count > 0, producer_tag == PRODUCES_VALUE_MAPPINGS)).
_PREPATCH_BODY = "    rs.description = value"
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_BODY, _PREPATCH_BODY)

# (3b) PARTIAL-DOMAIN — switch UNCONDITIONALLY (drop the guard): always set the
# value-mapping producer. Correct on every value-bearing input (C3 holds) but on
# an empty-selection input it overwrites the prior producer instead of preserving
# it. Diverges only on the count==0 sub-domain (when Old(producer_tag) != 1).
# Rejection source: C4 (Implies(value_field_count == 0,
# producer_tag == Old(producer_tag))).
_UNCOND_BODY = """    rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value"""
_RIVAL_UNCOND = _swap(_BASE, _GOLD_BODY, _UNCOND_BODY)

# (3c) PARTIAL-DOMAIN — off-by-one guard: switch only when count > 1, so a
# description with EXACTLY ONE selected value-field (count == 1 — the common
# `values('name')` case, F2P test_annotation_values) is wrongly left at the prior
# producer. Correct on count==0 (preserved) and count>=2 (switched), diverges
# only on the count==1 sub-domain. Rejection source: C3 at count==1
# (value_field_count > 0 holds but producer_tag is not set to 1).
_OFFBYONE_BODY = """    if value.value_field_count > 1:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value"""
_RIVAL_OFFBYONE = _swap(_BASE, _GOLD_BODY, _OFFBYONE_BODY)

# (1') VALUE-IDENTITY MISS — drop the store entirely: switch the producer
# correctly but never set rs.description, so the active query is NOT the attached
# value. Correct on the producer tags (C3/C4 hold) but C1 (rs.description is value)
# fails because rs.description keeps its pre-call (arbitrary) value. Rejection
# source: C1 (rs.description is value).
_DROP_STORE_BODY = """    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS"""
_RIVAL_DROP_STORE = _swap(_BASE, _GOLD_BODY, _DROP_STORE_BODY)

# (7) NON-TERMINATION — a DIVERGING rival, the exact hole the termination
# obligation exists to close. The gold body runs verbatim and is followed by an
# unbounded counting loop, so every postcondition (C1-C4) is established on the
# state before the loop and the method then never returns. Under PARTIAL
# correctness this rival is indistinguishable from gold: the Ensures are claimed
# only of runs that REACH the return, so a run that never reaches it satisfies
# them vacuously. MEASURED: with the MustTerminate precondition REMOVED from the
# spec, this exact module VERIFIES; with it present, Nagini rejects it with
# "Obligation leak check failed. Loop might not take all unsatisfied obligations
# from the context." Rejection source: the OBLIGATION SYSTEM (the loop carries no
# MustTerminate invariant, so it cannot discharge the caller's obligation) — not a
# postcondition, which is precisely why no property test could ever close it.
_DIVERGE_BODY = _GOLD_BODY + """
    spin = 0
    while spin >= 0:
        Invariant(spin >= 0)
        spin = spin + 1"""
_RIVAL_DIVERGE = _swap(_BASE, _GOLD_BODY, _DIVERGE_BODY)

# (8) DIVERGING SELF-CALL — the rival the old admissibility case (6) accidentally
# was. An UNCONDITIONAL self-call at the head of the impl: `attach_description`
# calls itself on freshly-built arguments with no guard and no decreasing measure,
# so the recursion has no base case and the method never returns. MEASURED: with
# the MustTerminate precondition REMOVED, this module VERIFIES (the old spec
# admitted unbounded recursion — this is the concrete divergence the obligation
# closes); with it present it is rejected with "Obligation leak check failed.
# Callee attach_description might not take all unsatisfied obligations from the
# caller", because a self-call would need the callee's level strictly below the
# caller's and the level is one shared constant. Established (not assumed) that
# it cannot be made to terminate: guarding the recursion so it descends at most
# one level (recurse only when count>0, passing LookupDescription(0)) STILL leaks,
# and that guarded form is not vacuous (an `Assert(False)` inside the guard
# fails, so the recursive branch is genuinely reachable). Rejection source: the
# OBLIGATION SYSTEM.
_DIVERGE_SELFCALL_BODY = (
    "    probe_rs = ResultSet(PRODUCES_MODEL_INSTANCES)\n"
    "    probe_desc = LookupDescription(1)\n"
    "    attach_description(probe_rs, probe_desc)\n"
    + _GOLD_BODY
)
_RIVAL_DIVERGE_SELFCALL = _swap(_BASE, _GOLD_BODY, _DIVERGE_SELFCALL_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct: store the description FIRST, then "
                  "apply the conditional producer switch. The store does not touch "
                  "producer_tag so the reorder is behaviourally identical; C1/C2/C3/C4 all "
                  "hold. If this fails to verify => the spec is over-fit to the gold "
                  "statement order (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo "
                  "control: the discriminator is the argument value_field_count, so doing "
                  "the conditional switch IS the work, not an echo."},
    {"id": "pos-control-explicit-else", "kind": "soundness", "expect": "verify",
     "module": _POS_EXPLICIT_ELSE,
     "rationale": "structurally-different but correct: an explicit two-armed if/else whose "
                  "empty-selection arm re-writes producer_tag to its own current value "
                  "(value-preserving self-assignment). Behaviourally identical to the gold "
                  "implicit-else, so C3 (count>0 -> tag 1) and C4 (count==0 -> Old preserved) "
                  "both hold. A branch-reshape, not a loop-direction flip. If it fails => the "
                  "spec is over-fit to the implicit-else shape (SPEC-TOO-STRONG)."},
    {"id": "admiss-value-bearing", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the F2P-shaped input: a freshly-created result set "
                  "(ResultSet(PRODUCES_MODEL_INSTANCES), the model-instance default) given a "
                  "value-bearing description (LookupDescription(1), the values('name') case of "
                  "F2P test_annotation_values). The constructors establish full permission on "
                  "the new objects and value_field_count == 1 >= 0, so the precondition "
                  "(Acc(rs.producer_tag), Acc(rs.description), Acc(value.value_field_count,1/2)) "
                  "must hold. If these Asserts cannot be discharged for this normal input "
                  "=> PRECOND-TOO-STRONG. The probe ASSERTS the Requires conjuncts rather "
                  "than making a self-call: an unconditional self-call is unbounded "
                  "recursion (now caught by the termination obligation, and kept as the "
                  "'diverging-self-call' reject case), which is a different and false "
                  "claim from 'the precondition is establishable'. Non-vacuous: splicing "
                  "Assert(False) after these Asserts fails, so the path is reachable."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-count", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: the real `QuerySet.query` "
                   "setter only READS `value.values_select` (the `if value.values_select:` "
                   "guard) and never mutates the incoming `sql.Query`'s value-field selection "
                   "(it would corrupt the pickled query being reattached). The rival exists "
                   "only to test whether the read-only (1/2) precondition on "
                   "value.value_field_count can be subverted by writing to it. No resolving "
                   "patch zeroes the selection count of the query it is attaching, so a "
                   "verifying rival here would be a pure verify-not-resolve artifact (vacuous "
                   "satisfaction via self-mutation of the discriminator).",
     "rationale": "MANDATORY frame-mutation probe. `value.value_field_count = 0` writes "
                   "through a 1/2 (read-only) reference and MUST fail for insufficient "
                   "permission. Rejection source: the PERMISSION SYSTEM (store needs full "
                   "perm); secondarily C2 (value_field_count == Old(value_field_count)) would "
                   "catch the value change. The gold body follows verbatim. If it verified => "
                   "SPEC-TOO-WEAK (frame protection hollow — an impl could dodge the C3 "
                   "discriminator by editing the input it is supposed to honour)."},
    {"id": "partial-prepatch-no-switch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this is the EXACT pre-patch behaviour (== model_prepatch.py): the "
                   "pre-patch setter was `self._query = value` only, leaving _iterable_class at "
                   "its __init__ default ModelIterable. Its faithful real patch is the "
                   "pre-patch setter, which FAILS the F2P tests test_annotation_values / "
                   "test_annotation_values_list (a reloaded value-bearing query then yields "
                   "model instances, so reloaded.get() is a model object, not the expected "
                   "dict {'name':'test', ...}). So it would NOT resolve.",
     "rationale": "partial-domain: correct on every empty-selection input (C4 holds) but on "
                  "every value-bearing input it leaves the producer at its prior value. "
                  "Rejection source: C3 (Implies(value_field_count > 0, producer_tag == "
                  "PRODUCES_VALUE_MAPPINGS)). If it verified => SPEC-TOO-WEAK (admits the "
                  "pre-patch no-switch bug)."},
    {"id": "partial-uncond-switch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNCOND,
     "refinement": "this corresponds to dropping the `if value.values_select:` guard so the "
                   "setter installs ValuesIterable for EVERY attached query, including plain "
                   "model querysets (all()/filter()/order_by()). Its faithful real patch would "
                   "make a reloaded plain query yield value mappings (dicts) instead of model "
                   "instances, breaking the PASS_TO_PASS model-instance pickle tests "
                   "(e.g. test_filter_deferred / test_manager_pickle, which expect the "
                   "reloaded queryset to still produce model objects). So it would NOT resolve.",
     "rationale": "partial-domain: correct on every value-bearing input (C3 holds) but on an "
                  "empty-selection input it overwrites the prior producer. Rejection source: "
                  "C4 (Implies(value_field_count == 0, producer_tag == Old(producer_tag))) — "
                  "when Old(producer_tag) != PRODUCES_VALUE_MAPPINGS the unconditional write "
                  "violates it. If it verified => SPEC-TOO-WEAK (admits the guard-dropped bug)."},
    {"id": "partial-off-by-one", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OFFBYONE,
     "refinement": "this corresponds to a guard `if len(value.values_select) > 1:` instead of "
                   "the real truthiness test `if value.values_select:`. A single-value-field "
                   "query (e.g. `values('name')`, the F2P test_annotation_values case, whose "
                   "values_select has exactly one entry) would be left at ModelIterable, so the "
                   "reloaded query yields a model instance instead of the expected dict "
                   "{'name':'test', 'latest_time':...}. So it would FAIL the F2P and NOT resolve.",
     "rationale": "partial-domain off-by-one: correct on count==0 (preserved) and count>=2 "
                  "(switched), diverges only on the count==1 sub-domain (the common "
                  "single-value-field case). Rejection source: C3 at count==1 "
                  "(value_field_count > 0 holds, but producer_tag is not set to "
                  "PRODUCES_VALUE_MAPPINGS). If it verified => SPEC-TOO-WEAK (drops the "
                  "single-value-field case)."},
    {"id": "drop-store", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_STORE,
     "refinement": "this corresponds to dropping `self._query = value` from the setter: the "
                   "producer is configured but the pickled query is never actually attached, "
                   "so `reloaded.query` is not the reloaded query and the reattachment is a "
                   "no-op on the active query. A faithful real patch that omitted the store "
                   "would leave the reloaded queryset running its original (empty) query, so "
                   "reloaded.get() would not reflect the pickled annotation/values query at "
                   "all and the F2P tests would FAIL. So it would NOT resolve.",
     "rationale": "value-identity miss: the producer tags are set correctly (C3/C4 hold) but "
                  "the store is omitted, so rs.description keeps its pre-call value. Rejection "
                  "source: C1 (rs.description is value) — the description is not the attached "
                  "value. If it verified => SPEC-TOO-WEAK (the identity-store guarantee is "
                  "hollow)."},
    {"id": "diverging-loop", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE,
     "refinement": "no faithful real patch corresponds to this: the real `QuerySet.query` "
                   "setter is one if and two assignments and contains no loop at all, so a "
                   "patch that spun forever after assigning would hang the first "
                   "`queryset.query = value` reattachment. Every F2P and P2P test that "
                   "unpickles a queryset (test_annotation_values, test_filter_deferred, "
                   "test_manager_pickle) would time out rather than fail, so it would NOT "
                   "resolve. It exists to pin TOTAL correctness: the rival DIVERGES.",
     "rationale": "the gold body runs verbatim, then an unbounded `while spin >= 0` loop, so "
                  "C1-C4 all hold where they are established and the method never returns. "
                  "Under partial correctness the postconditions are claimed only of runs that "
                  "REACH the return, so this VERIFIES against a spec with no termination "
                  "obligation (measured: it does) — verify failing to imply correct. Rejection "
                  "source: the OBLIGATION SYSTEM (the loop carries no MustTerminate invariant "
                  "and so cannot take the caller's obligation). If it verified => "
                  "SPEC-TOO-WEAK (the spec proves only partial correctness and admits an "
                  "implementation that hangs)."},
    {"id": "diverging-self-call", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE_SELFCALL,
     "refinement": "no faithful real patch corresponds to this: the real setter never calls "
                   "itself — `self._query = value` is a plain attribute store, not a "
                   "reattachment through the same property. A patch whose setter re-entered "
                   "itself unconditionally would recurse until the stack blew on the very "
                   "first `queryset.query = value`, so the F2P unpickling tests would error "
                   "out rather than pass. So it would NOT resolve.",
     "rationale": "an UNCONDITIONAL self-call with no base case and no decreasing measure: "
                  "unbounded recursion. This shape was previously the ACCEPT-lane "
                  "admissibility case, which is exactly the hole the obligation closes — "
                  "measured to VERIFY against the spec without MustTerminate. Established "
                  "that it cannot be made to terminate: even guarded to descend at most one "
                  "level it still leaks (levels are per-method constants, so a self-call can "
                  "never sit strictly below itself), and that guarded form is non-vacuous "
                  "(Assert(False) in the recursive branch fails, so the branch is reachable). "
                  "Rejection source: the OBLIGATION SYSTEM. If it verified => SPEC-TOO-WEAK "
                  "(the spec admits non-terminating recursion)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real callee) — A-reference deep-model soundness + containment
# ===========================================================================
#
# This bundle has NO @ContractOnly axiom (meta.axioms == []). The changed
# behaviour is modeled DEEPLY (the conditional producer switch over integer tags),
# an A-reference validated == the real callee by axiom_check.py / G-AX. The axiom
# lane re-runs that soundness check in Docker (a faithful port of axiom_check.py:
# the REAL post-patch QuerySet.query setter on an in-memory sqlite DB over every
# values()/values_list() flavour + plain queries + tuple-truthiness fuzz), and a
# caller-domain containment probe. Both probes guard for Django absence (the host
# self-validate has no Django) by printing a SKIP and exiting 0 — in the instance
# image Django is importable and the full check runs.

# (A) A-reference SOUNDNESS: the deep model (count>0 -> value-mapping producer;
# count==0 -> producer preserved; description stored; bool(values_select) <->
# count>0) == the REAL post-patch QuerySet.query setter. Port of axiom_check.py.
# Opens no file; imports only Django (the package the patch lives in) + stdlib.
_AX_REF_SOUND = r'''
import random, sys

# (A-reference proper) tuple-truthiness <-> non-emptiness <-> count > 0, the
# discriminator the deep model relies on. Holds regardless of Django.
rng = random.Random(13406)
for _ in range(5000):
    n = rng.randint(0, 8)
    values_select = tuple("f%d" % i for i in range(n))
    if bool(values_select) != (len(values_select) > 0) or bool(values_select) != (n > 0):
        print("tuple-truthiness mismatch: n=%d sel=%r" % (n, values_select)); sys.exit(1)

try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', '__main__'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
    from django.db import models, connection
    from django.db.models.query import (
        ModelIterable, ValuesIterable, ValuesListIterable,
        FlatValuesListIterable, NamedValuesListIterable,
    )
except Exception as exc:  # pragma: no cover - environment guard (host has no Django)
    print("AX-REF-SOUND SKIP: Django not configurable (%r); tuple-truthiness "
          "A-reference confirmed on 5000 fuzz tuples" % (exc,))
    sys.exit(0)

class Toy(models.Model):
    name = models.CharField(max_length=16)
    material = models.CharField(max_length=16)
    price = models.PositiveIntegerField()
    class Meta:
        app_label = '__main__'

with connection.schema_editor() as editor:
    editor.create_model(Toy)
Toy.objects.create(name='foo', price=10, material='wood')
Toy.objects.create(name='bar', price=20, material='plastic')

bad = []
obs = 0

def attach(value_query):
    """Run the REAL post-patch QuerySet.query setter on a fresh QuerySet."""
    fresh = Toy.objects.all()
    if fresh._iterable_class is not ModelIterable:
        bad.append(("fresh queryset not model-instance-default", fresh._iterable_class)); return None
    fresh.query = value_query  # the setter under test (the gold-patched property)
    return fresh

# value-bearing queries: every values()/values_list() flavour -> count>0 -> switch.
value_qs = [
    Toy.objects.values('material'),
    Toy.objects.values('name', 'material'),
    Toy.objects.values('material').annotate(total=models.Sum('price')),
    Toy.objects.values_list('name'),
    Toy.objects.values_list('name', flat=True),
    Toy.objects.values_list('name', named=True),
    Toy.objects.values_list('name', 'material'),
]
for qs in value_qs:
    obs += 1
    count = len(qs.query.values_select)  # the modeled value_field_count
    if not (count > 0):
        bad.append(("value-bearing query had empty values_select", qs.query.values_select)); continue
    fresh = attach(qs.query)
    if fresh is None:
        continue
    # deep model: count > 0 -> producer_tag == PRODUCES_VALUE_MAPPINGS (ValuesIterable, tag 1)
    if fresh._iterable_class is not ValuesIterable:
        bad.append(("count>0 did NOT switch to value-mapping producer", count, fresh._iterable_class))
    if fresh._iterable_class is ModelIterable:
        bad.append(("count>0 left model-instance producer (the bug)", count))
    # deep model: rs.description is value
    if fresh.query is not qs.query:
        bad.append(("attached query not stored", count))

# plain queries: model-instance lookups -> count==0 -> producer preserved (default).
plain_qs = [Toy.objects.all(), Toy.objects.filter(material='wood'), Toy.objects.order_by('name')]
for qs in plain_qs:
    obs += 1
    count = len(qs.query.values_select)
    if count != 0:
        bad.append(("plain query had non-empty values_select", qs.query.values_select)); continue
    fresh = attach(qs.query)
    if fresh is None:
        continue
    # deep model: count == 0 -> producer_tag == Old(producer_tag) (the ModelIterable default)
    if fresh._iterable_class is not ModelIterable:
        bad.append(("count==0 did NOT preserve the default producer", fresh._iterable_class))
    if fresh.query is not qs.query:
        bad.append(("attached query not stored (plain)", count))

if bad:
    print("A-REFERENCE-UNSOUND: deep model != real post-patch QuerySet.query setter on", bad[:8])
    sys.exit(1)
print("A-REFERENCE SOUND: real post-patch QuerySet.query setter matches the deep "
      "model on %d observations (count>0 -> value-mapping producer; count==0 -> "
      "default preserved; query stored) + 5000 tuple-truthiness fuzz" % obs)
sys.exit(0)
'''

# (B) CALLER-DOMAIN CONTAINMENT. The model's Requires on `value` is exactly
# value_field_count >= 0 (a count). Every (rs, value) the modeled function can
# reach has value.value_field_count an int >= 0 — the count of a real
# Query.values_select tuple (len >= 0 always). The deep model branches only on
# count==0 vs count>0, and the real setter branches only on bool(values_select),
# so the two reachable sub-domains are {empty tuple} and {non-empty tuple}. This
# probe confirms (i) every real values()/values_list() query reaches the count>0
# branch and every plain query reaches the count==0 branch (both branches are
# exercised, neither is silently skipped) and (ii) len(values_select) is always a
# non-negative int (in the model's Requires domain) — there is no reachable
# Query whose values_select count lies outside [0, inf). A reachable Query the
# deep model's branch space could not classify => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import sys

try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', '__main__'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
    from django.db import models, connection
except Exception as exc:  # pragma: no cover - environment guard (host has no Django)
    print("AX-CONTAINMENT SKIP: Django not configurable (%r)" % (exc,))
    sys.exit(0)

class Toy(models.Model):
    name = models.CharField(max_length=16)
    material = models.CharField(max_length=16)
    price = models.PositiveIntegerField()
    class Meta:
        app_label = '__main__'

with connection.schema_editor() as editor:
    editor.create_model(Toy)
Toy.objects.create(name='foo', price=10, material='wood')

problems = []
reached_positive = False
reached_zero = False

# every query the caller can reach: its values_select is a tuple, so the modeled
# value_field_count = len(values_select) is ALWAYS a non-negative int (in the
# model Requires domain value_field_count >= 0). Enumerate both branches.
value_qs = [
    Toy.objects.values('name'),                       # count 1 (the common F2P case)
    Toy.objects.values('name', 'material'),           # count 2
    Toy.objects.values_list('name'),                  # count 1
    Toy.objects.values_list('name', flat=True),       # count 1
    Toy.objects.values_list('name', named=True),      # count 1
    Toy.objects.values('material').annotate(total=models.Sum('price')),  # GROUP BY
]
plain_qs = [Toy.objects.all(), Toy.objects.filter(material='wood'), Toy.objects.order_by('name')]

for qs in value_qs + plain_qs:
    vs = qs.query.values_select
    count = len(vs)                                   # the modeled carrier
    if not isinstance(count, int) or count < 0:
        problems.append(("reachable value_field_count outside Requires (>=0)", count, vs))
        continue
    # tuple-truthiness <-> count>0 is exactly the deep model's branch test.
    if bool(vs) != (count > 0):
        problems.append(("real bool(values_select) != (count>0)", vs, count))
    if count > 0:
        reached_positive = True
    else:
        reached_zero = True

if not reached_positive:
    problems.append(("the count>0 branch was never exercised by a reachable query",))
if not reached_zero:
    problems.append(("the count==0 branch was never exercised by a reachable query",))

if problems:
    print("CONTAINMENT FAIL:", problems[:8]); sys.exit(1)
print("CONTAINMENT OK: every caller-reachable query has value_field_count = "
      "len(values_select) a non-negative int (in the model Requires), real "
      "tuple-truthiness == (count>0), and both deep-model branches (count>0 and "
      "count==0) are exercised by a reachable query (none silently skipped).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-ref-sound", "axiom": "attach_description (the conditional producer switch)",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_REF_SOUND,
     "rationale": "the A-reference deep model (count>0 -> value-mapping producer; count==0 -> "
                  "producer preserved; description stored; bool(values_select) <-> count>0) "
                  "must equal the REAL post-patch QuerySet.query setter over every "
                  "values()/values_list() flavour + plain queries on an in-memory sqlite DB, "
                  "plus 5000 tuple-truthiness fuzz tuples. Any mismatch => the deep model is "
                  "unsound (A-REFERENCE-UNSOUND). Faithful port of axiom_check.py; "
                  "Django + stdlib only, opens no file."},
    {"id": "ax-containment", "axiom": "attach_description (the conditional producer switch)",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every Query the modeled function can reach has value_field_count = "
                  "len(values_select) a non-negative int (always in the model Requires domain "
                  "value_field_count >= 0); the deep model's two branches (count>0 / count==0) "
                  "exactly partition tuple-truthiness, and both are exercised by a reachable "
                  "query. No reachable Query falls outside the deep model's branch space => "
                  "no AXIOM-TOO-WEAK-FOR-CALLER."},
]
