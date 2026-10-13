"""properties.py — PBT falsification manifest for django__django-16819.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    reduce_add_index(index_name: List[int], self_elidable: bool,
                     operation: Operand) -> int

modelling the gold `AddIndex.reduce`:

    def reduce(self, operation, app_label):
        if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
            return []
        return super().reduce(operation, app_label)

with the mixed list/bool return tag-encoded {0:False, 1:[], 2:[operation],
3:[self]}. The load-bearing contract is

    # read-only inputs, held at HALF permission:
    Requires/Ensures Acc(list_pred(index_name), 1/2)
    Requires/Ensures Acc(operation.is_remove_index, 1/2)
    Requires/Ensures Acc(operation.name, 1/2) and Acc(list_pred(operation.name), 1/2)
    Requires/Ensures Acc(operation.elidable, 1/2)
    # the discriminating CANCELLATION clause:
    Ensures Implies(operation.is_remove_index and names_equal(index_name, operation.name),
                    Result() == 1)
    # the GENERIC-RULE clause (grounded in the args via the @Pure deep model):
    Ensures Implies(not (operation.is_remove_index and names_equal(index_name, operation.name)),
                    Result() == base_combine(self_elidable, operation.elidable))
    # the LEGAL-TAG clause:
    Ensures Result() == 0 or 1 or 2 or 3

What the spec actually defends, and the attacks it must survive:

  * UNGROUNDED-ORACLE-ECHO does NOT apply. The two outcome oracles are BOTH
    grounded in the args, not opaque answer-keys: `base_combine(self_elidable,
    operation.elidable)` is a @Pure deep model (NOT @ContractOnly) fully unfolded
    by Viper into a 3-branch function of the two boolean flags, and
    `names_equal(index_name, operation.name)` unfolds to
    `ToSeq(index_name) == ToSeq(operation.name)`. There is no marker an impl can
    return to "satisfy the pin without doing the work" — the only value that
    satisfies clause 2 (cancellation) is 1 and the only value that satisfies
    clause 3 is `base_combine(...)`. So instead of a wrong-echo reject case we
    carry an HONEST cheapest-impl positive control (`pos-master-assert`) that
    asserts, before each return, that the value it produces equals the grounded
    oracle — it must verify, demonstrating the spec is not echo-vulnerable.

  * FOUR read-only inputs are held at HALF permission (1/2): the index name
    `index_name`, and the three operation facets `is_remove_index`, `name`,
    `elidable`. The MANDATORY attack is FRAME MUTATION: an impl that WRITES to any
    of them to satisfy a postcondition vacuously must fail for INSUFFICIENT
    PERMISSION, never a value mismatch. Two frame rivals are included
    (`frame-mutate-is-remove`, an attribute store at 1/2; `frame-mutate-name`, a
    list_pred store at 1/2), each keeping the gold body verbatim after the illegal
    write so the rejection is attributable solely to the store.

  * CONTROL-FLOW-EFFECT is N/A. `reduce_add_index` is a total, exception-free,
    side-effect-free function with a single observable channel — the integer tag
    it returns — and that tag is fully pinned by clauses 1+2+3. There is no
    raise/return/side-effect distinction the value abstraction misses, so a
    capability-token rival would discriminate nothing. (Stated here per directive
    4's "omit if N/A".)

  * PARTIAL-DOMAIN is where a near-correct rival can hide, so it gets the heaviest
    coverage: a rival can be right on the whole cancellation sub-domain yet wrong
    on a base-rule sub-case, or right on the base rule yet mis-scope the
    cancellation guard. Five uniqueness rivals each target one sub-domain of the
    {0,1,2,3} outcome lattice.

  * TERMINATION. The spec carries `Requires(MustTerminate(6))` on
    `reduce_add_index` and `Requires(MustTerminate(2))` on the Operand constructor
    (level 2 < 6 leaves the room a caller needs to build the counterpart operation
    it passes in). Without the obligation Nagini proves only PARTIAL correctness:
    clauses 1-3 are claimed of runs that REACH the return, so an implementation
    that never returns satisfies all three vacuously and VERIFIES while its
    faithful patch hangs the optimiser. That is a property of the SPEC, so no
    property test can close it; the `diverging-self-call` rival pins it (measured
    to VERIFY against the obligation-free spec and to be rejected by the
    obligation system once the obligation is present). Because a method holding an
    unsatisfied obligation may only call callees that promise to terminate too,
    accept-lane cases that BUILD a probe input need the constructor obligation, and
    an accept-lane case may not self-call at all: levels are per-method constants
    and a call needs the callee's level strictly below the caller's.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION catching wrong behaviour
(or the permission system), never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P (`test_add_remove_index`: `[AddIndex("Pony", idx),
RemoveIndex("Pony", idx.name)]` must optimise to `[]`).

AXIOM LANE: empty. This bundle has NO @ContractOnly axioms and NO A-reference
deep models. The only callee (`super().reduce`) is the function-under-spec's own
base-class generic rule (`Operation.reduce`), three boolean branches modeled
DEEPLY as the @Pure `base_combine` — a transcription audited line-for-line in
refinement.md (step A6), not an opaque external callee. There is therefore no
axiom-soundness or axiom-containment obligation, so `AXIOM_TESTS = []`.
"""
from pathlib import Path

INSTANCE = "django__django-16819"
FLOAT_ENCODING = None

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
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body (cancellation guard + 3-branch base rule).
_GOLD_BODY = (
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n"
    "        return 1\n"
    "    if self_elidable:\n"
    "        return 2\n"
    "    if operation.elidable:\n"
    "        return 3\n"
    "    return 0\n"
)

# the base-rule tail (everything after the cancellation guard's `return 1`).
_BASE_RULE = (
    "    if self_elidable:\n"
    "        return 2\n"
    "    if operation.elidable:\n"
    "        return 3\n"
    "    return 0\n"
)

# the cancellation guard line (the discriminating early return).
_CANCEL_GUARD = (
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n"
    "        return 1\n"
)

# the impl head landmark — insertion point for frame-mutation / admissibility.
_IMPL_HEAD = (
    "    # impl-start\n"
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-different but CORRECT. The base rule is rewritten as a single
# nested if/else chain (no early `return` for the elidable branches; one return
# of a local `tag`), and the cancellation guard is restructured into a nested
# `if is_remove_index: if names_equal: return 1`. Semantically identical, a
# different source shape, and — crucially — it needs NO induction lemma the
# verifier can't discharge (no loops, no fold; each branch is a direct boolean
# read pinned by clause 2/3). If this fails to verify, the postcondition is
# over-fit to the exact gold branch order/shape => SPEC-TOO-STRONG.
_POS_RESHAPE_BODY = (
    "    if operation.is_remove_index:\n"
    "        if names_equal(index_name, operation.name):\n"
    "            return 1\n"
    "    tag = 0  # type: int\n"
    "    if self_elidable:\n"
    "        tag = 2\n"
    "    else:\n"
    "        if operation.elidable:\n"
    "            tag = 3\n"
    "        else:\n"
    "            tag = 0\n"
    "    return tag\n"
)
_POS_RESHAPE = _swap(_BASE, _GOLD_BODY, _POS_RESHAPE_BODY)

# (2/5b) HONEST cheapest-impl / no-echo demonstration. The outcome oracles are
# grounded in the args (base_combine is a @Pure function of the two flags;
# names_equal unfolds to ToSeq equality), so there is no opaque marker to echo.
# This control keeps the gold body but, on EACH return path, first asserts that
# the tag it is about to return equals the grounded oracle for that path:
#   - on the cancellation path, the guard premise holds, so clause 1 pins 1;
#   - on every fall-through path, the guard premise is false, so clause 2 pins
#     base_combine(self_elidable, operation.elidable), which equals the tag.
# It is CORRECT (expect="verify"); its purpose is to show there is no wrong echo
# that verifies — the oracle is a function of the args, not an answer-key. (If a
# wrong echo could verify, this would instead be a SPEC-TOO-WEAK reject case;
# none exists.)
_POS_MASTER_BODY = (
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n"
    "        return 1\n"
    "    Assert(not (operation.is_remove_index and names_equal(index_name, operation.name)))\n"
    "    if self_elidable:\n"
    "        Assert(base_combine(self_elidable, operation.elidable) == 2)\n"
    "        return 2\n"
    "    if operation.elidable:\n"
    "        Assert(base_combine(self_elidable, operation.elidable) == 3)\n"
    "        return 3\n"
    "    Assert(base_combine(self_elidable, operation.elidable) == 0)\n"
    "    return 0\n"
)
_POS_MASTER = _swap(_BASE, _GOLD_BODY, _POS_MASTER_BODY)

# (6) ADMISSIBILITY. Builds the F2P-shaped input — the exact
# `[AddIndex("Pony", idx_pony_weight_pink), RemoveIndex("Pony",
# "idx_pony_weight_pink")]` shape: index_name = "idx" (a non-empty code-point
# list) and, as the counterpart, a fresh removal Operand carrying that same name,
# both operations non-elidable — and then ASSERTS exactly the conjuncts of
# reduce_add_index's Requires on it, as one separating conjunction so the
# fractions must genuinely add up. Fresh local lists/objects carry FULL
# permission, so handing out the 1/2 fractions the precondition asks for (the
# name's list_pred is split between `index_name` and `operation.name`, which are
# the same name here) is admissible, and the shape facts the cancellation clause
# keys on (is_remove_index, equal names) hold. If these Asserts cannot be
# discharged for this normal input => PRECOND-TOO-STRONG. The gold body that
# follows is unchanged.
#
# NOTE on the shape. This case previously discharged the same claim with an
# actual self-call `reduce_add_index(pname, False, pop)`. That formulation is
# unsound as an admissibility probe now that the spec carries a termination
# obligation, and deliberately is not restored: the self-call is UNCONDITIONAL,
# so it is unbounded recursion (kept below as the `diverging-self-call` reject
# case), and MustTerminate levels are per-method constants — a call needs the
# callee's level strictly BELOW the caller's, which one shared constant (6) can
# never give a self-call. The old shape therefore conflated two claims: "a caller
# can establish the precondition for a normal input" (true, and the only thing
# admissibility must test) with "the operation may combine by calling itself
# unboundedly" (false). Asserting the Requires conjuncts directly tests the
# former without asserting the latter. Verified non-vacuous: splicing
# `Assert(False)` after these Asserts FAILS, so the probe path is reachable and
# the Asserts pin real facts rather than passing under an infeasible path
# condition.
_ADMISS_HEAD_NEW = (
    "    pname = [105, 100, 120]  # type: List[int]\n"
    "    pop = Operand(True, pname, False)\n"
    "    Assert(Acc(list_pred(pname), 1 / 2) and Acc(pop.is_remove_index, 1 / 2)\n"
    "           and Acc(pop.name, 1 / 2) and Acc(list_pred(pop.name), 1 / 2)\n"
    "           and Acc(pop.elidable, 1 / 2))\n"
    "    Assert(pop.is_remove_index and names_equal(pname, pop.name))\n"
    "    Assert(not pop.elidable)\n"
    + _GOLD_BODY
)
_ADMISS = _swap(_BASE, _GOLD_BODY, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1a) FRAME MUTATION — MANDATORY, the #1 weakness class. `operation.is_remove_index`
# is held at Acc(..., 1/2) (read-only). This rival STORES to it at the impl head
# (a write through a 1/2 reference) before doing the gold work. A store to a field
# held at half permission requires FULL permission, so it MUST fail for
# INSUFFICIENT PERMISSION — not a value mismatch. The gold body is kept verbatim
# after the write, so the rejection is attributable solely to the illegal store.
# Rejection source: the PERMISSION SYSTEM.
_RIVAL_FRAME_ATTR = _swap(
    _BASE, _IMPL_HEAD,
    "    # impl-start\n"
    "    operation.is_remove_index = False\n"
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n",
)

# (1b) FRAME MUTATION on a list_pred input. `index_name` is held at
# Acc(list_pred(index_name), 1/2). This rival appends to it at the impl head — a
# store into the list's predicate, which needs FULL list_pred permission. With
# only 1/2 it MUST fail for INSUFFICIENT PERMISSION. The gold body follows
# verbatim. Rejection source: the PERMISSION SYSTEM (the list mutation needs full
# perm), not a value mismatch.
_RIVAL_FRAME_LIST = _swap(
    _BASE, _IMPL_HEAD,
    "    # impl-start\n"
    "    index_name.append(0)\n"
    "    if operation.is_remove_index and names_equal(index_name, operation.name):\n",
)

# (3a, partial-domain == the discriminating BUG / pre-gold behaviour) DROP THE
# CANCELLATION GUARD. The operation always defers to the base rule (this is
# model_prepatch.py: AddIndex has no reduce override). Correct on the entire
# `not (is_remove_index and names_equal)` sub-domain, WRONG on every matching
# RemoveIndex (returns base_combine instead of 1). Its faithful real patch is the
# pre-patch state, where the F2P `[AddIndex("Pony", idx), RemoveIndex("Pony",
# idx.name)]` is NOT optimised to `[]` (both non-elidable -> base returns False),
# so test_add_remove_index FAILS; it would NOT resolve. Rejection source: the
# cancellation postcondition Implies(is_remove_index and names_equal, Result()==1)
# (here Result()==base_combine(False,False)==0 on the witness).
_RIVAL_DROP_CANCEL = _swap(_BASE, _CANCEL_GUARD, "")

# (3b, partial-domain) MIS-SCOPE THE CANCELLATION GUARD: cancel on name equality
# ALONE, dropping the `is_remove_index` conjunct. Correct whenever the names
# differ OR the counterpart IS a removal, but WRONG on a NON-removal counterpart
# whose name happens to equal the index name (returns 1 where the generic rule
# should apply). Its faithful real patch (`if self.index.name == operation.name:
# return []`, no isinstance check) would cancel an AddIndex against ANY operation
# carrying an equal `.name` — e.g. another AddIndex or a CreateModel with a like
# attribute — silently dropping a real add and corrupting later migrations; that
# is not the issue's behaviour, so it would NOT resolve (and breaks P2P optimizer
# invariants). Rejection source: the generic-rule postcondition
# Implies(not (is_remove_index and names_equal), Result()==base_combine(...)) —
# on a non-removal with equal name the rival returns 1 but the spec demands
# base_combine(self_elidable, operation.elidable).
_RIVAL_GUARD_DROP_ISREMOVE = _swap(
    _BASE, _CANCEL_GUARD,
    "    if names_equal(index_name, operation.name):\n"
    "        return 1\n",
)

# (3c, partial-domain) MIS-SCOPE THE CANCELLATION GUARD the other way: cancel on
# `is_remove_index` ALONE, dropping the names_equal conjunct. Correct whenever the
# names match OR the counterpart is not a removal, but WRONG on a removal of a
# DIFFERENT-named index (returns 1 where the generic rule should apply). Its
# faithful real patch (`if isinstance(operation, RemoveIndex): return []`) would
# cancel an AddIndex against a RemoveIndex of an UNRELATED index, dropping a real
# index addition the migration needs — wrong behaviour that would NOT resolve and
# would break optimizer P2P tests that combine independent index ops. Rejection
# source: the generic-rule postcondition — on a removal with a different name the
# rival returns 1 but the spec demands base_combine(self_elidable,
# operation.elidable).
_RIVAL_GUARD_DROP_NAMEEQ = _swap(
    _BASE, _CANCEL_GUARD,
    "    if operation.is_remove_index:\n"
    "        return 1\n",
)

# (4, partial-domain on the base rule) SWAP THE BASE-RULE TAGS 2<->3. The
# cancellation is correct, but the generic combination rule returns [self] where
# it should return [operation] and vice-versa. Its faithful real patch swaps the
# `self.elidable -> [operation]` / `operation.elidable -> [self]` branches of
# Operation.reduce, mis-optimising every elidable combination (the optimizer would
# keep the wrong operation), breaking the optimizer's reduce contract on the
# elidable sub-domain — it would NOT resolve P2P optimizer tests that exercise
# elidable operations. Rejection source: the generic-rule postcondition
# Implies(not (is_remove_index and names_equal), Result()==base_combine(...)) —
# base_combine(True, _)==2 and base_combine(False, True)==3, but the rival returns
# 3 resp. 2.
_RIVAL_SWAP_TAGS = _swap(
    _BASE, _BASE_RULE,
    "    if self_elidable:\n"
    "        return 3\n"
    "    if operation.elidable:\n"
    "        return 2\n"
    "    return 0\n",
)

# (7) DIVERGING SELF-CALL — the shape the admissibility case (6) accidentally
# was, kept here as a reject case so the claim it now carries is pinned. An
# UNCONDITIONAL self-call at the head of the impl: reduce_add_index combines by
# calling itself on freshly-built arguments, with no guard and no decreasing
# measure, so the recursion has no base case and the call never returns. Under
# PARTIAL correctness that is indistinguishable from gold — every Ensures is
# claimed only of runs that REACH the return, so a run that never reaches it
# satisfies all of them vacuously. MEASURED: with the MustTerminate precondition
# REMOVED from the spec this exact module VERIFIES; with it present Nagini rejects
# it with "Obligation leak check failed. Callee reduce_add_index might not take
# all unsatisfied obligations from the caller". Established (not assumed) that the
# recursion cannot be made to terminate here: guarding it to descend at most one
# level (recurse only when the names differ, passing a matching pair) STILL leaks,
# because levels are per-method constants and a call needs the callee's level
# strictly below the caller's, which a self-call can never have; and that guarded
# form is not vacuous (an Assert(False) in the recursive branch fails, so the
# branch is genuinely reachable). Rejection source: the OBLIGATION SYSTEM — not a
# postcondition, which is exactly why no property test could close this hole.
_RIVAL_DIVERGE_SELFCALL = _swap(
    _BASE, _GOLD_BODY,
    "    pname = [105, 100, 120]  # type: List[int]\n"
    "    pop = Operand(True, pname, False)\n"
    "    _probe = reduce_add_index(pname, False, pop)\n"
    + _GOLD_BODY,
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "structurally-different but correct: the cancellation guard is nested "
                  "(if is_remove_index: if names_equal: return 1) and the base rule is a single "
                  "nested if/else writing a local `tag` returned once, instead of three early "
                  "returns. No loop/fold/induction lemma is needed (each branch is a direct "
                  "boolean read pinned by clauses 2/3), so it must verify. If it fails => the "
                  "spec is over-fit to the exact gold branch order/shape => SPEC-TOO-STRONG."},
    {"id": "pos-master-assert", "kind": "soundness", "expect": "verify",
     "module": _POS_MASTER,
     "rationale": "the outcome oracles are GROUNDED in the args (base_combine is a @Pure "
                  "function of the two flags; names_equal unfolds to ToSeq equality), so the "
                  "cheapest impl satisfying the pins still computes them. This control asserts on "
                  "every return path that its tag equals the grounded oracle (1 on the "
                  "cancellation path; base_combine(self_elidable, operation.elidable) on each "
                  "fall-through path) and must verify — demonstrating the spec is NOT "
                  "echo-vulnerable (there is no wrong oracle-echo that verifies; else this would "
                  "be a reject case)."},
    {"id": "admiss-fshape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the exact F2P-shaped input (a matching RemoveIndex: index_name and "
                  "operation.name both 'idx', operation.is_remove_index True, both "
                  "non-elidable) must satisfy the precondition (Acc(list_pred,1/2) on the "
                  "names, Acc(.,1/2) on the three operation facets), so the probe builds it and "
                  "ASSERTS those conjuncts as one separating conjunction plus the shape facts "
                  "the cancellation clause keys on. If they cannot be discharged for this "
                  "normal input => PRECOND-TOO-STRONG. The probe ASSERTS the Requires conjuncts "
                  "rather than making a self-call: an unconditional self-call is unbounded "
                  "recursion (a different and false claim, now caught by the termination "
                  "obligation and kept as the 'diverging-self-call' reject case). Non-vacuous: "
                  "splicing Assert(False) after these Asserts fails, so the path is reachable."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-is-remove", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_ATTR,
     "refinement": "no faithful real patch corresponds to this: the gold AddIndex.reduce never "
                   "writes to the counterpart operation's `is_remove_index`/type — the operation "
                   "is another migration op the optimizer passes in read-only. The rival exists "
                   "only to test whether the read-only (1/2) precondition on operation.is_remove_index "
                   "can be subverted by writing to it. No resolving patch mutates its operation "
                   "input, so a verifying rival here would be a pure verify⇏resolve artifact "
                   "(vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `operation.is_remove_index = False` stores to "
                  "a field held at 1/2 (read-only) permission and MUST fail for INSUFFICIENT "
                  "PERMISSION. Rejection source: the PERMISSION SYSTEM (an attribute store needs "
                  "full perm), not a value mismatch; the gold body is kept verbatim after the "
                  "write. If it verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "frame-mutate-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_LIST,
     "refinement": "no faithful real patch corresponds to this: the gold reduce never mutates "
                   "the managed index name (`self.index.name`, a Python str — immutable). The "
                   "rival exists only to test whether the read-only (1/2) list_pred precondition "
                   "on index_name can be subverted by appending to it. No resolving patch "
                   "overwrites its name input, so a verifying rival would be a pure verify⇏resolve "
                   "artifact.",
     "rationale": "MANDATORY frame-mutation probe (list_pred variant). `index_name.append(0)` "
                  "stores into a list held at Acc(list_pred(index_name),1/2) and MUST fail for "
                  "INSUFFICIENT PERMISSION (the mutation needs full list_pred perm). Rejection "
                  "source: the PERMISSION SYSTEM, not a value mismatch; the gold body follows "
                  "verbatim. If it verified => SPEC-TOO-WEAK."},
    {"id": "drop-cancellation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_CANCEL,
     "refinement": "drops the cancellation guard entirely — the exact pre-gold state "
                   "(model_prepatch.py: AddIndex has no reduce override, always defers to the "
                   "base rule). For the F2P `[AddIndex('Pony', idx), RemoveIndex('Pony', "
                   "idx.name)]` (both non-elidable) the base rule returns False (tag 0), so the "
                   "pair is NOT optimised to [] — test_add_remove_index FAILS; it would NOT "
                   "resolve. This is the exact bug the gold patch fixes.",
     "rationale": "partial-domain == the discriminating bug. Correct on the whole non-cancelling "
                  "sub-domain, WRONG on every matching RemoveIndex (returns base_combine instead "
                  "of 1). Rejection source: the cancellation postcondition "
                  "Implies(is_remove_index and names_equal, Result()==1) — on the F2P witness the "
                  "rival returns base_combine(False,False)==0 != 1. If it verified => "
                  "SPEC-TOO-WEAK (admits the bug)."},
    {"id": "guard-drop-isremove", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_GUARD_DROP_ISREMOVE,
     "refinement": "cancels on name equality ALONE (drops the is_remove_index conjunct). Its "
                   "faithful real patch (`if self.index.name == operation.name: return []`, no "
                   "isinstance check) would cancel an AddIndex against ANY operation carrying an "
                   "equal `.name` — another AddIndex, or any op exposing a matching name — "
                   "silently dropping a real index addition and corrupting later migrations. That "
                   "is not the issue's behaviour and breaks optimizer P2P invariants, so it would "
                   "NOT resolve.",
     "rationale": "partial-domain. Correct unless the counterpart is a NON-removal with an equal "
                  "name, where it wrongly returns 1. Rejection source: the generic-rule "
                  "postcondition Implies(not (is_remove_index and names_equal), "
                  "Result()==base_combine(...)) — on a non-removal with equal name the guard "
                  "premise (is_remove_index and names_equal) is FALSE, so the spec demands "
                  "base_combine(self_elidable, operation.elidable), but the rival returns 1. If it "
                  "verified => SPEC-TOO-WEAK (cancellation under-guarded)."},
    {"id": "guard-drop-nameeq", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_GUARD_DROP_NAMEEQ,
     "refinement": "cancels on is_remove_index ALONE (drops the names_equal conjunct). Its "
                   "faithful real patch (`if isinstance(operation, RemoveIndex): return []`) would "
                   "cancel an AddIndex against a RemoveIndex of an UNRELATED, differently-named "
                   "index, dropping an index addition the migration genuinely needs — wrong "
                   "behaviour that breaks optimizer P2P tests combining independent index ops, so "
                   "it would NOT resolve.",
     "rationale": "partial-domain. Correct unless the counterpart is a removal of a "
                  "DIFFERENT-named index, where it wrongly returns 1. Rejection source: the "
                  "generic-rule postcondition — on a removal with a different name the guard "
                  "premise is FALSE (names_equal is false), so the spec demands "
                  "base_combine(self_elidable, operation.elidable), but the rival returns 1. If it "
                  "verified => SPEC-TOO-WEAK (cancellation over-broad)."},
    {"id": "swap-base-tags", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP_TAGS,
     "refinement": "swaps the base-rule branches 2<->3 (self_elidable -> [self] instead of "
                   "[operation]; operation.elidable -> [operation] instead of [self]). Its "
                   "faithful real patch transposes Operation.reduce's two elidable branches, so "
                   "the optimizer keeps the WRONG operation whenever either op is elidable — "
                   "mis-optimising on the elidable sub-domain and breaking optimizer P2P tests "
                   "that exercise elidable operations; it would NOT resolve.",
     "rationale": "partial-domain on the base (non-cancellation) rule. Cancellation is correct; "
                  "the generic rule is transposed. Rejection source: the generic-rule "
                  "postcondition Implies(not (is_remove_index and names_equal), "
                  "Result()==base_combine(self_elidable, operation.elidable)) — base_combine(True,_) "
                  "==2 and base_combine(False,True)==3, but the rival returns 3 resp. 2. If it "
                  "verified => SPEC-TOO-WEAK (the base-rule outcome is unpinned)."},
    {"id": "diverging-self-call", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE_SELFCALL,
     "refinement": "no faithful real patch corresponds to this: the gold AddIndex.reduce "
                   "answers with `return []` or `super().reduce(...)` and never re-enters "
                   "itself — the optimizer asks each operation whether it combines with the "
                   "next one, it does not ask the operation to re-ask itself. A patch whose "
                   "reduce called itself unconditionally would recurse until the stack blew on "
                   "the very first optimisation pass, so test_add_remove_index (and every P2P "
                   "optimizer test) would error out rather than pass. So it would NOT resolve.",
     "rationale": "an UNCONDITIONAL self-call with no base case and no decreasing measure: "
                  "unbounded recursion. This shape was previously the ACCEPT-lane admissibility "
                  "case, which is exactly the hole the termination obligation closes — measured "
                  "to VERIFY against the spec without MustTerminate, where the postconditions "
                  "are claimed only of runs that REACH the return. Established that it cannot "
                  "be made to terminate: even guarded to descend at most one level it still "
                  "leaks (levels are per-method constants, so a self-call can never sit "
                  "strictly below itself), and that guarded form is non-vacuous (Assert(False) "
                  "in the recursive branch fails, so the branch is reachable). Rejection "
                  "source: the OBLIGATION SYSTEM. If it verified => SPEC-TOO-WEAK (the spec "
                  "proves only partial correctness and admits an implementation that hangs)."},
]

# ===========================================================================
# AXIOM LANE — empty (no @ContractOnly axioms, no A-reference deep models).
# ===========================================================================
# The only callee (`super().reduce`) is the function-under-spec's own base-class
# generic rule (Operation.reduce, base.py:129-139), three boolean branches modeled
# DEEPLY as the @Pure `base_combine` — a direct transcription audited line-for-line
# (refinement.md A6, mapping.md §3), NOT an opaque external library callee. There
# is no axiom-soundness or axiom-containment obligation. (meta.json: axioms = [];
# deep_model_references[0].kind = "deep-model (not an A-reference, not a consumed
# axiom)".)
AXIOM_TESTS = []
