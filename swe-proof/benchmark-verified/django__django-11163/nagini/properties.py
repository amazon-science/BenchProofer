# properties.py — PBT falsification battery for django__django-11163.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes. Each SPEC_TEST is a full model.py variant
# that shares the FROZEN spec byte-for-byte (region surgery: only the text
# strictly BETWEEN `# impl-start` and `# impl-end` is ever edited — the nested
# `# invariants-start/-end` block lives inside the impl region, so loop
# invariants/asserts are editable, but positive controls KEEP every gold proof
# obligation so a verify never fails for a proof-trigger reason) and swaps the
# impl; the runner checks `same_spec` + Nagini verify. `expect:"verify"` passes
# iff (same_spec AND verifies); `expect:"reject"` passes iff (same_spec AND does
# NOT verify).
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / G-AX):
#
#   project_record(names: List[int], edit: List[int],
#                  allowed: Optional[List[int]], blocked: Optional[List[int]])
#       -> List[int]
#
#   * ALL FOUR inputs are READ-ONLY: names/edit at Acc(list_pred(.),1/2) and
#     allowed/blocked at Implies(. is not None, Acc(list_pred(.),1/2)). The
#     postcondition re-ensures each at 1/2 — the projection mutates nothing it
#     is given. => FRAME-MUTATION is MANDATORY (the #1 weakness class). A rival
#     that WRITES any of these inputs to satisfy the postcondition vacuously
#     must be REJECTED for INSUFFICIENT PERMISSION (only a 1/2 share is held;
#     append/element-write needs the full predicate). Two frame-mut rivals below
#     (names, edit) confirm both stream carriers are protected; the optional
#     lists are exercised by the value rivals.
#
#   * The load-bearing postcondition clause is
#         Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit),
#                                                allowed, blocked))
#     where `projection` is a @Pure deep model that is FULLY UNFOLDED as a
#     function of the args (front-recursive fold over the two parallel streams,
#     consulting passes_restriction / is_removed / contains). It is GROUNDED in
#     the inputs — NOT an opaque @ContractOnly answer-key oracle. There is
#     therefore NO wrong echo to build: `return materialize(projection(...))`
#     would BE doing the work, and any value that satisfies the equality is the
#     correct projected key sequence. UNGROUNDED-ORACLE-ECHO is N/A; instead the
#     grounded-oracle lane is covered by a structurally-different positive
#     control (pos-reorder) that must verify.
#
#   * The discriminating content of the gold change (refinement.md §A4): a
#     PRESENT-but-EMPTY restriction list (allowed=[]) must keep NOTHING
#     (presence gating via passes_restriction), whereas the pre-patch truthiness
#     gating `if fields and ...` (model_prepatch.py) let every editable,
#     non-removed name through. Every value rival below attacks one filter clause
#     of `projection`: the restriction presence-vs-truthiness gating (A4), the
#     None=>keep-all branch (A4), the editability filter (A3), or the
#     per-element source-order/multiplicity (A7).
#
#   * TOTALITY is a load-bearing part of the contract:
#         Requires(MustTerminate(2))
#     The F2P observation is an assertion ABOUT A RETURNED VALUE on a specific
#     in-domain input (a present-but-empty restriction list), so "a result is
#     delivered" is part of the behaviour, not a meta-property. Without this
#     obligation every value clause above is only a partial-correctness claim:
#     an impl may compute the gold projection on every input it answers and
#     simply never answer the one input the change is about, discharging the
#     postcondition vacuously. Two NON-DELIVERY rivals below (recursive
#     self-delegation; an unmeasured inner loop) reach that hole by DIFFERENT
#     routes and must both be REJECTED. A standing reachability control
#     (nonvacuity-nodeliver-inner-site-reachable) pins the program point both are
#     judged at -- after the loop, under a present-but-empty restriction list --
#     as REACHABLE, so neither rejection is a claim about a branch Viper never
#     has to consider. Note the consequence for the
#     admissibility lane: a self-call witness is no longer available (it cannot
#     present a decreasing measure), so admiss-fshaped establishes the
#     precondition on an F2P-shaped input instead of invoking through it.
#
#   * Raise / side-effect class: project_record mutates nothing (all four inputs
#     read-only, above) and the value abstraction (the projected key sequence) is
#     the entire value observable (the F2P observes sorted(model_to_dict), i.e.
#     the key set). The one non-value observable that IS load-bearing —
#     whether an answer arrives at all — is covered by the totality lane. No
#     capability-token rival is needed. Justified in the structured 'assessment'.
#
# AXIOM_TESTS = []: meta.json axioms == [] (no @ContractOnly consumed axiom; the
# `axioms` region is empty). The lone deep-model reference (`projection`,
# A-reference) is validated == the real post-patch model_to_dict filtering loop
# by axiom_check.py / G-AX on the HOST (stdlib-only; no DB/settings); it is the
# deep-model membership/structure logic itself, with no callee whose Ensures the
# runner must re-check in Docker. Per PBT_PLAN §3 the axiom lane is empty for
# this bundle.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-11163"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl body — everything strictly BETWEEN the impl markers
# (lines 117-140 of model.py). Each variant is produced by _swap-ing this whole
# block, so the edit is provably confined to the impl region and `same_spec` is
# preserved. The nested invariants/asserts are reproduced verbatim here and kept
# verbatim in every positive control (they discharge the front-recursive
# `projection` fold for the backward loop; deleting one would fail the loop
# invariant for a PROOF reason, not a spec reason — pilot bug #2).
_GOLD_IMPL = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: old block appears {src.count(old)}x")
    return src.replace(old, new, 1)


# Sanity: the gold block must be present exactly once in the frozen base.
assert _GOLD_IMPL in _BASE, "drift: _GOLD_IMPL not byte-identical to model.py impl region"
assert _BASE.count(_GOLD_IMPL) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ===========================================================================

# pos-reorder: a structurally-DIFFERENT but CORRECT impl. The three filter
# conjuncts in the keep guard are REORDERED (removal-first, then restriction,
# then editability) — boolean conjunction is commutative so the truth value is
# identical, but the executable shape differs. The backward loop direction is
# UNCHANGED (a forward loop would need an f(a+b)==f(a)+f(b) lemma against the
# front-recursive `projection` fold — pilot bug #3 — so we do NOT flip it), and
# every gold invariant + framing Assert is kept VERBATIM so the proof stays
# valid (pilot bug #2). Must verify (else SPEC-TOO-STRONG).
_POS_REORDER = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # Reordered conjuncts (commutative): removal, then restriction, then editable.
        if (not is_removed(blocked, n)) and passes_restriction(allowed, n) and e != 0:
            result = [n] + result
        i = i - 1
    return result"""

# pos-localvar: a structurally-different CORRECT impl that hoists each filter
# decision into a named local boolean before the keep test. Same backward loop,
# same gold invariants/asserts verbatim; only the executable shape (three locals
# + a combined guard) differs. Must verify (else SPEC-TOO-STRONG).
_POS_LOCALVAR = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        is_editable = e != 0  # type: bool
        keep_restr = passes_restriction(allowed, n)  # type: bool
        keep_rem = not is_removed(blocked, n)  # type: bool
        if is_editable and keep_restr and keep_rem:
            result = [n] + result
        i = i - 1
    return result"""

# admiss-fshaped: an admissibility probe on a normal F2P-shaped in-domain input —
# the headline case fields=[] (present-empty restriction => empty projection),
# exclude=None, two editable attributes — built as locally-owned full-perm lists.
# The fresh list literals carry the FULL list_pred, from which the required read
# fractions Acc(.,1/2) follow, and the equal-length requirement is asserted
# directly. If the value precondition cannot be established for this ordinary
# input => PRECOND-TOO-STRONG.
#
# NOTE: a literal SELF-CALL is no longer usable as the witness. The frozen spec
# now carries a termination obligation, and a recursive self-invocation cannot
# present a strictly smaller measure — by design, since an operation that never
# hands a result back was exactly the vacuous-satisfaction escape. So the probe
# establishes the precondition without invoking, which is what admissibility
# actually asks. The gold body is kept verbatim after it.
_ADMISS_FSHAPED = """    # --- admissibility probe on an F2P-shaped input (fields=[] headline) ---
    a_names = [1, 2]  # type: List[int]
    a_edit = [1, 1]  # type: List[int]   # both editable
    a_allowed = []  # type: List[int]    # present-but-empty restriction list
    Assert(len(a_names) == len(a_edit))
    Assert(Acc(list_pred(a_names), 1 / 2))
    Assert(Acc(list_pred(a_edit), 1 / 2))
    Assert(Acc(list_pred(a_allowed), 1 / 2))
    # --- the real (gold) resolution for the actual inputs ---
    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""


# ===========================================================================
# FRAME-MUTATION rivals (uniqueness, MANDATORY — read-only inputs) — REJECT.
# Each writes a half-permission input; append needs the FULL list predicate, of
# which only Acc(.,1/2) is held => insufficient permission. The write is placed
# at the TOP, before the loop/invariants, so the rejection is attributable to
# the permission failure and not to any disturbed invariant.
# ===========================================================================

_FRAME_MUT_NAMES = """    # ADVERSARY: write the read-only input `names` (Acc(list_pred(names),1/2)).
    # `append` requires the FULL list predicate -> insufficient permission.
    names.append(0)
    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""

_FRAME_MUT_EDIT = """    # ADVERSARY: write the read-only input `edit` (Acc(list_pred(edit),1/2)).
    # `append` requires the FULL list predicate -> insufficient permission.
    edit.append(1)
    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""


# ===========================================================================
# UNIQUENESS value rivals — same spec, WRONG impl — must be REJECTED.
# Each replaces the keep guard with a divergent predicate and KEEPS the
# backward loop + gold invariants/asserts (so the rejection is the value
# divergence against Ensures(ToSeq(Result())==projection(...)), not a proof gap).
# Loop invariant 8 (ToSeq(result)==projection(...)) is the clause that bites.
# ===========================================================================

# weak-truthiness: THE pre-patch bug (model_prepatch.py). The restriction filter
# uses TRUTHINESS gating instead of presence gating: a present-but-empty list is
# treated like an absent one (keeps all). Correct on every input EXCEPT a
# present-empty restriction list (allowed=[], len 0), where it keeps all editable
# non-removed names rather than nothing.
_WEAK_TRUTHINESS = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # BUG: truthiness gating — present-empty restriction list keeps everything.
        keep_restr = allowed is None or len(allowed) == 0 or contains(ToSeq(allowed), n)  # type: bool
        if e != 0 and keep_restr and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""

# weak-restrict-none-drops: drops the `allowed is None => keep all` branch — a
# present-or-absent list is always treated as a membership filter. Correct only
# when allowed is a present list whose members cover the kept names; WRONG on the
# overwhelmingly common allowed=None case (keeps nothing instead of all editable
# non-removed names). Attacks the A4 None=>True branch of passes_restriction.
_WEAK_RESTRICT_NONE = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # BUG: an absent (None) restriction list is treated as a membership filter
        # too (drops the None=>keep-all branch); keeps nothing when allowed is None.
        keep_restr = allowed is not None and contains(ToSeq(allowed), n)  # type: bool
        if e != 0 and keep_restr and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""

# weak-drop-editability: drops the editability filter (e != 0). Correct on every
# input with no non-editable surviving attribute; WRONG whenever a non-editable
# attribute (edit[k]==0) passes the restriction + removal filters — it is kept,
# violating the editability clause (A3). Attacks the editable skip that the
# baseline P2P sorted(model_to_dict(bw)) and the F2P all depend on.
_WEAK_DROP_EDIT = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # BUG: editability filter dropped — a non-editable attribute survives.
        if passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""

# weak-partial-first: a partial-domain attack on the FIRST source element. The
# keep test gains an extra guard `i != 1`, so the attribute at index 0 is NEVER
# kept even when it survives all three filters. Correct on every input whose
# first attribute would not survive; WRONG (drops a surviving names[0]) otherwise.
# Attacks the per-element source-order/multiplicity pinned by A7 / invariant 8.
_WEAK_PARTIAL_FIRST = """    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # BUG: never keep the first source attribute (extra `i != 1` guard).
        if i != 1 and e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result"""


# ===========================================================================
# NON-DELIVERY rivals (totality) — REJECT. Each computes the RIGHT value on
# every input it answers, but on the headline in-domain case (a present-but-
# empty restriction list) it never hands a result back. Under a partial-
# correctness reading alone these satisfy every value/permission clause
# vacuously; the termination obligation in the precondition is what rejects
# them. The gold loop (with its measure) is kept verbatim so the rejection is
# attributable to the non-delivery and not to a disturbed invariant.
# ===========================================================================

# nodeliver-selfcall: unbounded self-delegation on the present-empty restriction
# list, placed AFTER the real work so the value clause is already established.
# The obligation cannot be re-presented to a recursive invocation at the same
# measure, so it is rejected.
_NODELIVER_SELFCALL = _GOLD_IMPL.replace(
    "    return result",
    """    if allowed is not None and len(allowed) == 0:
        return project_record(names, edit, allowed, blocked)
    return result""",
    1,
)

# nodeliver-inner-loop: same non-delivery reached through an inner loop with no
# measure, entered only on the present-empty restriction list.
#
# The spin body is an INT increment of the already-declared loop cursor `i`. It
# deliberately does NOT rebind `result`: an earlier version spun on
# `result = []  # type: List[int]`, which REDECLARES the `result` introduced at
# the top of the gold body, and Nagini's front end refused the whole file with
# "Type error: Name result already defined" and exited 1 BEFORE Viper saw
# anything. nagini is not in pbt.WITNESS_REQUIRED, so a reject case's entire
# argument is "the verifier did not verify it" -- a front-end refusal exits
# non-zero too, so that variant was a HOLLOW rejection that said nothing at all
# about the spec. `i` is a plain local int, still in scope after the outer loop
# and needing no permission, so incrementing it adds no declaration and leaves
# the spin's ONLY defect the missing measure -- the divergence this case is for.
# Measured: rejected in 40.0s, inside the 15.7-46s band a genuine Viper
# rejection takes on this corpus (a front-end refusal returns in under 8s).
_NODELIVER_INNER = _GOLD_IMPL.replace(
    "    return result",
    """    if allowed is not None and len(allowed) == 0:
        while True:
            # invariants-start
            Invariant(Acc(list_pred(result)))
            # invariants-end
            i = i + 1
    return result""",
    1,
)

# nonvacuity-nodeliver-inner-site-reachable: standing reachability control for the
# program point BOTH non-delivery rivals are judged at. Their rejections are
# claims about the state AFTER the outer loop under the guard
# `allowed is not None and len(allowed) == 0`; were that state unreachable the
# obligation checks there would discharge under a false path condition and
# neither rejection would be evidence about the spec -- a guarded branch goes
# vacuous in exactly this way. The probe is the GOLD body with `Assert(False)`
# spliced under the SAME guard (byte-identical path condition) and the gold
# `return result` kept after it, so a failing Assert is the only obligation that
# can break and the reject is unambiguously about reachability.
_NONVACUITY_INNER_SITE = _GOLD_IMPL.replace(
    "    return result",
    """    if allowed is not None and len(allowed) == 0:
        Assert(False)
    return result""",
    1,
)


SPEC_TESTS = [
    # ---------------- positive controls (verify) ----------------
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": "Structurally different but equivalent CORRECT impl: the "
                     "three keep-guard conjuncts are reordered (commutative "
                     "conjunction). Same backward loop direction (so the "
                     "front-recursive `projection` fold needs no append lemma) "
                     "and every gold invariant + framing Assert kept verbatim. "
                     "Must verify (else SPEC-TOO-STRONG). This is also the "
                     "grounded-oracle positive control: `projection` is a "
                     "transparent function of the args, so there is no wrong "
                     "echo — a correct different shape must verify.",
    },
    {
        "id": "pos-localvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_LOCALVAR),
        "rationale": "Structurally different CORRECT impl: hoist each filter "
                     "decision into a named local bool then combine. Same loop, "
                     "gold invariants/asserts verbatim; only the executable shape "
                     "differs. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-fshaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_FSHAPED),
        "rationale": "Admissibility probe on a normal F2P-shaped in-domain "
                     "input (names=[1,2], edit=[1,1] equal-length editable "
                     "streams, a present-empty restriction list a_allowed=[], no "
                     "removal), built as locally-owned full-perm lists that lend "
                     "the 1/2 shares Requires demands. The precondition must "
                     "admit this input (else PRECOND-TOO-STRONG); gold body kept "
                     "verbatim. A literal self-call is deliberately NOT used: the "
                     "spec's termination obligation forbids a recursive "
                     "invocation from presenting a smaller measure, which is the "
                     "point of that obligation, so the witness establishes the "
                     "precondition rather than invoking through it.",
    },
    # ---------------- frame-mutation rivals (reject) ----------------
    {
        "id": "frame-mut-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT_NAMES),
        "refinement": "A real patch that WRITES the iterated attribute stream "
                      "(`opts.concrete_fields`/chain) to coerce the projection is "
                      "not the gold edit at all — the gold hunk only changes a "
                      "single `if` condition (`fields and` -> `fields is not "
                      "None and`) and mutates no field collection. Mutating the "
                      "model's field metadata would corrupt every other "
                      "model_to_dict call and the P2P suite, so it would NOT "
                      "resolve the F2P the way the gold patch does.",
        "rationale": "FRAME-MUTATION (#1 weakness class): `names` is read-only "
                     "(Acc(list_pred(names),1/2)). `names.append(0)` needs the "
                     "FULL list predicate; only a 1/2 share is held -> rejected "
                     "for INSUFFICIENT PERMISSION (the permission system, not a "
                     "value clause). Confirms the read-only carrier is protected.",
    },
    {
        "id": "frame-mut-edit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT_EDIT),
        "refinement": "A real patch that writes the per-attribute editability "
                      "stream (`getattr(f,'editable',False)`) to force survivors "
                      "is not the gold edit (a single `if` condition change); it "
                      "would mutate shared field metadata and break the P2P "
                      "editability tests, so it would NOT resolve the F2P.",
        "rationale": "FRAME-MUTATION: `edit` is read-only "
                     "(Acc(list_pred(edit),1/2)). `edit.append(1)` needs the FULL "
                     "predicate -> rejected for INSUFFICIENT PERMISSION. Confirms "
                     "the SECOND stream carrier is protected (distinct from "
                     "frame-mut-names).",
    },
    # ---------------- value uniqueness rivals (reject) ----------------
    {
        "id": "weak-truthiness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WEAK_TRUTHINESS),
        "refinement": "This IS the pre-patch model_to_dict skeleton "
                      "(model_prepatch.py): the restriction filter uses "
                      "truthiness gating `if fields and f.name not in fields` "
                      "(present-empty `fields=[]` treated like absent). Its "
                      "faithful real patch is the UNPATCHED line, which the F2P "
                      "assertion `sorted(model_to_dict(bw, fields=[])) == []` "
                      "FAILS (it returns all editable names). A verifying rival "
                      "here would be a true verify-not-resolve break (G-DIFF "
                      "documents this exact divergence).",
        "rationale": "Partial-domain attack on the headline change (A4). Violates "
                     "Ensures(ToSeq(Result())==projection(...)) / loop invariant 8 "
                     "on EXACTLY the present-empty restriction list "
                     "(allowed=[],len 0): keeps all editable non-removed names "
                     "where projection (presence gating) keeps none.",
    },
    {
        "id": "weak-restrict-none-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WEAK_RESTRICT_NONE),
        "refinement": "Treats an ABSENT restriction list (fields=None, the "
                      "default and most common call) as a membership filter that "
                      "matches nothing. The faithful real patch would be a "
                      "`if f.name not in fields` test WITHOUT the `fields is not "
                      "None` guard — it raises/keeps-nothing for the default "
                      "`model_to_dict(bw)` call, breaking the P2P baseline "
                      "`sorted(model_to_dict(bw)) == ['id','name','score',"
                      "'writer_ptr']`, so it does NOT resolve.",
        "rationale": "Attacks the A4 `allowed is None => True` branch of "
                     "passes_restriction. Violates loop invariant 8 whenever "
                     "allowed is None: keeps nothing where projection keeps all "
                     "editable, non-removed names.",
    },
    {
        "id": "weak-drop-editability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WEAK_DROP_EDIT),
        "refinement": "Drops the editability skip. The faithful real patch would "
                      "delete `if not getattr(f,'editable',False): continue` "
                      "(models.py:84, UNCHANGED by the gold hunk) — it would emit "
                      "non-editable fields (e.g. auto/derived columns) into the "
                      "dict, breaking the P2P baseline keyset and the F2P "
                      "`exclude=[]` -> all-EDITABLE-names assertion, so it does "
                      "NOT resolve.",
        "rationale": "Partial-domain attack on the editability clause (A3). "
                     "Violates loop invariant 8 whenever a non-editable attribute "
                     "(edit[k]==0) passes the other two filters: it is kept where "
                     "projection drops it.",
    },
    {
        "id": "weak-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WEAK_PARTIAL_FIRST),
        "refinement": "Never keeps the first source attribute. The faithful real "
                      "patch would special-case the head of "
                      "chain(concrete_fields,...) to skip it (e.g. an off-by-one "
                      "drop of the leading column) — for BetterWriter the first "
                      "concrete field is `id`, so `model_to_dict(bw)` would lose "
                      "'id' and the P2P/F2P `['id','name',...]` assertions FAIL, "
                      "so it does NOT resolve.",
        "rationale": "Partial-domain attack on the first source element / the "
                     "per-element source-order + multiplicity pinned by A7 and "
                     "loop invariant 8. Violates ToSeq(Result())==projection(...) "
                     "whenever names[0] would survive all three filters (drops it).",
    },
    # ---------------- non-delivery rivals (reject) ----------------
    {
        "id": "nodeliver-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NODELIVER_SELFCALL),
        "refinement": "Its faithful real patch is the gold-filtered loop guarded "
                      "by a branch that re-enters the record projection with the "
                      "same arguments whenever an empty restriction list is "
                      "supplied. That patch applies cleanly and keeps every other "
                      "call working, but the F2P assertion "
                      "sorted(model_to_dict(bw, fields=[])) == [] never gets an "
                      "answer (RecursionError), so it does NOT resolve — this is "
                      "the exact verify-not-resolve shape a totality-free spec "
                      "admits.",
        "rationale": "NON-DELIVERY / totality. Computes the correct projection "
                      "for every input it answers, so no value clause can catch "
                      "it; only Requires(MustTerminate(2)) does. A recursive "
                      "self-invocation cannot be handed the obligation at a "
                      "non-decreasing measure, so it is rejected. If it verified "
                      "=> SPEC-TOO-WEAK (the projection could be claimed without "
                      "ever being delivered).",
    },
    {
        "id": "nodeliver-inner-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NODELIVER_INNER),
        "refinement": "Its faithful real patch is the gold-filtered loop followed "
                      "by an unbounded spin entered only when an empty "
                      "restriction list is supplied; the F2P observation on that "
                      "input hangs instead of returning [], so it does NOT "
                      "resolve. A DISTINCT route to non-delivery from "
                      "nodeliver-selfcall (an unmeasured loop rather than "
                      "recursion), so the two together confirm the obligation is "
                      "not merely blocking one syntactic path.",
        "rationale": "NON-DELIVERY / totality, second route. The inner loop "
                     "presents no decreasing measure, so it cannot consume the "
                     "caller's termination obligation and the obligation leaks "
                     "=> rejected. Value clauses are all satisfied on every "
                     "answered input, so this rival is invisible to them. "
                     "MEASURED (40.0s, a real Viper verdict -- not a front-end "
                     "refusal): the SINGLE error is \"Obligation leak check "
                     "failed. Loop might not take all unsatisfied obligations "
                     "from the context.\" reported at the inner `while True`, "
                     "i.e. exactly the obligation this case claims. ATTRIBUTED "
                     "by ablation: with Requires(MustTerminate(2)) deleted from "
                     "the spec (in a throwaway copy, never landed) this "
                     "identical rival VERIFIES in 44.5s, so the rejection comes "
                     "from that clause and from nothing else. NON-VACUOUS: the "
                     "site is reachable, pinned by "
                     "`nonvacuity-nodeliver-inner-site-reachable` below.",
    },
    {
        "id": "nonvacuity-nodeliver-inner-site-reachable",
        "kind": "admissibility",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NONVACUITY_INNER_SITE),
        "refinement": "Not a candidate patch at all: a reachability probe. An "
                      "implementation that asserts False once a present-but-empty "
                      "restriction list has been projected delivers nothing and "
                      "would NOT resolve the F2P; it exists only to show that the "
                      "program point the two non-delivery rivals are judged at is "
                      "actually executed.",
        "rationale": "NON-VACUITY control for the site `nodeliver-inner-loop` and "
                     "`nodeliver-selfcall` are judged at; not a spec attack. Gold "
                     "body verbatim with `Assert(False)` spliced under the same "
                     "`allowed is not None and len(allowed) == 0` guard, so the "
                     "path condition is byte-identical to the rivals' and the "
                     "failing Assert is the only obligation that can break. "
                     "MEASURED (32.7s): the single error is \"Assert might fail. "
                     "Assertion False might not hold.\" -- the Assert FAILS, so a "
                     "present-but-empty restriction list DOES reach that point "
                     "under the frozen Requires, and the obligation both "
                     "non-delivery rivals fail there is not discharged under a "
                     "false path condition. If this ever VERIFIES the branch has "
                     "gone dead, both non-delivery rejections stop being evidence "
                     "and the totality lane is empty => PRECOND-TOO-STRONG.",
    },
]


# No @ContractOnly axiom (meta.json axioms == []) and no Docker-checkable callee
# Ensures: the lone A-reference deep model `projection` is host-validated by
# axiom_check.py / G-AX (stdlib-only reconstruction of the real post-patch
# model_to_dict filtering loop over 20000 fuzz configs + the boundary battery,
# plus the pre-patch divergence-on-fields=[] check). The axiom lane is empty per
# PBT_PLAN §3.
AXIOM_TESTS = []
