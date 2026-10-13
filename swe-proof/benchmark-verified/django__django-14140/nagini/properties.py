# properties.py — PBT falsification battery for django__django-14140. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region (the spec_view elides that whole
# region, so any in-region edit preserves same_spec); the runner re-runs the
# Nagini verifier on the host and checks the verify/reject outcome against
# `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + instance.json):
#
#   deconstruct_arguments(node: Node) -> Deconstruction
#     # node is READ-ONLY: every field is held at half permission
#     Requires(Acc(node.children, 1/2)); Requires(Acc(list_pred(node.children),1/2))
#     Requires(Acc(node.connector, 1/2)); Requires(Acc(node.default, 1/2))
#     Requires(Acc(node.negated, 1/2))
#     Ensures(...same half perms returned untouched...)         # frame: read-only
#     Ensures(Acc(Result().args) and Acc(list_pred(Result().args)) ...)  # fresh result
#     Ensures(ToSeq(Result().args) == ToSeq(node.children))     # CLAUSE (1) — THE FIX
#     Ensures(Result().connector_kwarg == (node.connector != node.default))  # CLAUSE (2a)
#     Ensures(Result().negated_kwarg == node.negated)           # CLAUSE (2b)
#
# THE FIX (instance.json / refinement.md §B): the gold patch removes the
# single-child special case
#     if len(self.children) == 1 and not isinstance(self.children[0], Q):
#         kwargs = {child[0]: child[1]}     # relocated the lone child into kwargs
# so that single-child Q objects deconstruct into args, not kwargs. Clause (1)
# `ToSeq(Result().args) == ToSeq(node.children)` is precisely this: EVERY child
# (including a single non-Q child such as an Exists) is positional. The F2P
# tests (test_deconstruct, test_deconstruct_negated, test_deconstruct_boolean_
# expression, test_boolean_expression_combined_with_empty_Q) all observe a
# single-child node whose child must now land in args == (child,) with kwargs
# carrying only the two state markers.
#
# Load-bearing clauses and where each rejection comes from:
#   * (1) ToSeq(Result().args) == ToSeq(node.children) — pins args to the WHOLE
#     children sequence in order. Attacks: the single-child special case (the
#     pre-patch bug), a partial-domain off-by-one that drops an element, and the
#     frame-mutation that clears node.children to make args trivially match.
#   * (2a) connector_kwarg == (node.connector != node.default) — grounded boolean
#     of the connector relation. Attacks: a constant flag; a frame-mutation that
#     sets node.connector := node.default to make the flag trivially False.
#   * (2b) negated_kwarg == node.negated — grounded boolean. Attack: a constant
#     flag; a frame-mutation that overwrites node.negated.
#   * PERMISSION: every node field is Acc(..., 1/2) (read-only). A rival that
#     WRITES any node field to satisfy a postcondition vacuously must be REJECTED
#     for INSUFFICIENT PERMISSION (the #1 weakness class; mandatory here).
#
# UNGROUNDED-ORACLE ECHO — N/A. There is NO @Pure answer-key / @ContractOnly
# oracle in the postcondition (the axioms region is empty). All three clauses are
# GROUNDED directly in the node's own observable state (node.children verbatim,
# the int relation connector != default, the bool node.negated), fully unfolded
# in the spec. There is no opaque marker an impl could echo without doing the
# work, so there is no "wrong echo that still verifies". The cheapest honest impl
# (which just copies the children and reads the two flags) is therefore a
# positive control, included below. (See `assessment`.)
#
# CONTROL-FLOW-EFFECT — N/A. deconstruct_arguments is a total pure value
# computation: no raise/return-path or side-effect distinguishes a correct impl
# from a wrong one beyond what the value postcondition already pins (args content
# + two booleans). There is no capability-token surface to discriminate. (The
# real method's pre-patch CRASH on a non-subscriptable child is itself just the
# absence of a valid (args, kwargs) value — captured by clause (1) demanding the
# child be in args; the deep model has no exceptional control flow.)
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-14140"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    # The keyword arguments carry only the connector (when non-default) and the
    # negation flag; never a child.
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Both keep the gold forward-append loop and
# ALL its invariants/framing asserts VERBATIM (pilot pitfalls #2/#3: a reversed
# loop against the front-recursive `.take(i)` helper would need a take/drop lemma
# the verifier won't auto-discharge, so we DO NOT flip the loop direction); they
# reshape only the surrounding scalar computation / local-variable structure.
# ===========================================================================

# pos-reorder-kwargs: compute the two kwargs booleans BEFORE the args loop. They
# are independent of `args` (functions of node.connector/default/negated only),
# so reordering them ahead of the loop is behaviourally identical. The gold loop
# + every invariant + the four closing framing asserts are kept verbatim so the
# prefix-preservation proof (ToSeq(args) == ToSeq(node.children).take(i)) is
# unchanged. Must verify (else SPEC-TOO-STRONG).
_POS_REORDER = """    # impl-start
    # Compute the two state-marker booleans first (independent of args).
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end"""

# pos-inline-flags: a local-variable reshape — drop the `connector_kwarg`/
# `negated_kwarg`/`result` temporaries and pass the two grounded expressions
# directly into the Deconstruction constructor, returning it inline. The args
# loop + invariants + the four closing framing asserts are kept verbatim. The
# constructor's Ensures (ToSeq(self.args) == Old(ToSeq(args))) plus the loop's
# established ToSeq(args) == ToSeq(node.children) discharge clause (1). Must
# verify (else SPEC-TOO-STRONG).
_POS_INLINE = """    # impl-start
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    return Deconstruction(args, node.connector != node.default, node.negated)
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). A new module-level caller def would change the
# projected spec view and break same_spec, so we inject the admissibility witness
# INSIDE the impl region (elided from the spec view): build a concrete F2P-shaped
# single-child node (children == [7], i.e. a single non-Q child — exactly the
# test_deconstruct / test_deconstruct_boolean_expression shape) and assert it
# satisfies the constructor Ensures, then assert deconstruct_arguments's exact
# Requires (the five half-perm accesses) are establishable for it. The real impl
# then runs unchanged over the actual `node`. If the precondition could not be
# established for this legitimate single-child input the Asserts fail =>
# PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped single-child node (elided) ---
    adm_children = [7]  # type: List[int]
    adm = Node(adm_children, 0, 0, False)
    # the function's Requires (all five half accesses) is establishable here:
    Assert(Acc(adm.children, 1 / 2))
    Assert(Acc(list_pred(adm.children), 1 / 2))
    Assert(Acc(adm.connector, 1 / 2))
    Assert(Acc(adm.default, 1 / 2))
    Assert(Acc(adm.negated, 1 / 2))
    # this single-child node has exactly one child (the F2P shape):
    Assert(len(adm.children) == 1)
    # --- end admissibility witness; the real impl follows unchanged ---
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: every node field is read-only
# (Acc(..., 1/2)). A rival that WRITES a node field to satisfy a postcondition
# vacuously MUST be rejected for INSUFFICIENT PERMISSION. The gold clauses are
# kept verbatim so the rejection is attributable to the write, not a value
# mismatch. (A byte-fuzzer never thinks to mutate the input — this is the
# project's #1 weakness class.)
# ===========================================================================

# frame-mutate-children: overwrite node.children to the empty list, then return
# args == [] which now "matches" the (mutated) children. This is the cheapest
# vacuous satisfaction of clause (1): if the write were allowed, ToSeq([]) ==
# ToSeq(node.children) would hold trivially. node.children is held at half
# permission, so the assignment `node.children = ...` is rejected for
# INSUFFICIENT PERMISSION before any value reasoning.
_FRAME_CHILDREN = """    # impl-start
    empty = []  # type: List[int]
    node.children = empty  # WRITE to a read-only (Acc 1/2) field -> rejected
    args = []  # type: List[int]
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# frame-mutate-connector: overwrite node.connector to equal node.default so that
# clause (2a) connector_kwarg == (node.connector != node.default) holds with a
# constant False flag. node.connector is held at half permission, so the write
# `node.connector = node.default` is rejected for INSUFFICIENT PERMISSION.
_FRAME_CONNECTOR = """    # impl-start
    node.connector = node.default  # WRITE to a read-only (Acc 1/2) field -> rejected
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = False
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# frame-mutate-negated: overwrite node.negated to False so that clause (2b)
# negated_kwarg == node.negated holds with a constant False flag. node.negated is
# held at half permission, so the write is rejected for INSUFFICIENT PERMISSION.
_FRAME_NEGATED = """    # impl-start
    node.negated = False  # WRITE to a read-only (Acc 1/2) field -> rejected
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = node.connector != node.default
    negated_kwarg = False
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain (reject) — rivals that share the spec exactly and
# change ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-single-child-special-case: THE PRE-PATCH BUG (= model_prepatch.py). When
# the node has exactly one child, leave args empty (the removed special case
# relocated that lone child into kwargs). For a multi-child node it copies the
# children correctly, so it is correct on most of the domain but DIVERGES on the
# single-child sub-domain — exactly the case every F2P test exercises. Must be
# rejected by clause (1): on a single-child node args == [] while node.children
# has one element, so ToSeq(Result().args) != ToSeq(node.children).
_UNIQ_SINGLE_CHILD = """    # impl-start
    args = []  # type: List[int]
    n = len(node.children)
    if n != 1:
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(node.children, 1 / 2))
            Invariant(Acc(list_pred(node.children), 1 / 2))
            Invariant(0 <= i and i <= n)
            Invariant(n == len(node.children))
            Invariant(n != 1)
            Invariant(Acc(list_pred(args)))
            Invariant(ToSeq(args) == ToSeq(node.children).take(i))
            # invariants-end
            Assert(ToSeq(node.children).take(i + 1) ==
                   ToSeq(node.children).take(i) + PSeq(node.children[i]))
            args = args + [node.children[i]]
            i = i + 1
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# uniq-drop-last: partial-domain off-by-one. Copy every child EXCEPT the last
# (loop to n-1). Correct on the empty-children node and identical-prefix nodes
# but drops the final child for any non-empty node. Must be rejected by clause
# (1): ToSeq(Result().args) == ToSeq(node.children).take(n-1) != the full
# children sequence whenever n >= 1.
_UNIQ_DROP_LAST = """    # impl-start
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    m = n - 1
    while i < m:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= m)
        Invariant(m == n - 1)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# uniq-connector-constant-false: drop the connector relation; always report the
# connector kwarg ABSENT (connector_kwarg = False). The args loop is kept gold so
# clause (1) holds; the rejection is isolated to clause (2a). Must be rejected by
# Ensures(connector_kwarg == (node.connector != node.default)) on any node whose
# connector differs from default (the OR / non-default-connector nodes the G-AX
# fuzz and P2P test_deconstruct_or exercise).
_UNIQ_CONN_FALSE = """    # impl-start
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = False
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# uniq-negated-constant-false: always report the negation kwarg ABSENT
# (negated_kwarg = False). Args loop + connector flag kept gold; rejection
# isolated to clause (2b). Must be rejected by Ensures(negated_kwarg ==
# node.negated) on any negated node (the ~Q(...) F2P test_deconstruct_negated
# fixture).
_UNIQ_NEG_FALSE = """    # impl-start
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = node.connector != node.default
    negated_kwarg = False
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""

# uniq-connector-flip: invert the connector relation (== instead of !=). A
# supporting near-miss for clause (2a): reports the connector kwarg PRESENT
# exactly when the connector EQUALS the default — the opposite of the spec. Must
# be rejected by Ensures(connector_kwarg == (node.connector != node.default)).
_UNIQ_CONN_FLIP = """    # impl-start
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    connector_kwarg = node.connector == node.default
    negated_kwarg = node.negated
    return Deconstruction(args, connector_kwarg, negated_kwarg)
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-reorder-kwargs",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl: compute the two state-"
                     "marker booleans (connector_kwarg, negated_kwarg) BEFORE the "
                     "args loop. They are functions of node.connector/default/"
                     "negated only (independent of args), so reordering is "
                     "behaviourally identical. The gold forward-append loop, all "
                     "six invariants, and the four closing framing asserts are kept "
                     "VERBATIM so the prefix-preservation proof (ToSeq(args) == "
                     "ToSeq(node.children).take(i)) is untouched (pilot pitfalls "
                     "#2/#3). If a faithful correct impl cannot verify => SPEC-TOO-"
                     "STRONG.",
    },
    {
        "id": "pos-inline-flags",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_INLINE),
        "rationale": "local-variable reshape: drop the connector_kwarg/negated_"
                     "kwarg/result temporaries and pass the two grounded "
                     "expressions (node.connector != node.default, node.negated) "
                     "directly into the Deconstruction constructor, returning it "
                     "inline. The args loop + invariants + four closing framing "
                     "asserts are kept verbatim; the constructor Ensures "
                     "(ToSeq(self.args) == Old(ToSeq(args))) plus the loop's "
                     "ToSeq(args) == ToSeq(node.children) discharge clause (1). If "
                     "it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-single-child-node",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds a "
                     "concrete F2P-shaped single-child node Node([7], 0, 0, False) "
                     "(exactly the test_deconstruct / test_deconstruct_boolean_"
                     "expression shape: one non-Q child) and asserts the "
                     "constructor establishes deconstruct_arguments's exact "
                     "Requires (the five Acc(...,1/2) accesses) for it, plus "
                     "len(children) == 1. The real impl then runs unchanged. If the "
                     "precondition could not be established for this legitimate "
                     "single-child input the Asserts fail => PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (must reject for insufficient permission) ----
    {
        "id": "frame-mutate-children",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_CHILDREN),
        "refinement": "overwriting self.children inside Q.deconstruct (clearing the "
                      "node's children) would mutate the very object being "
                      "deconstructed: every F2P/P2P test reuses its Q after "
                      "deconstruct() (e.g. test_reconstruct rebuilds Q(*args, "
                      "**kwargs) and asserts equality with the ORIGINAL q; "
                      "test_boolean_expression_combined_with_empty_Q filters with "
                      "the live Q). A faithful patch that emptied self.children "
                      "would corrupt the node and fail those tests — it does not "
                      "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: node.children is held at "
                     "Acc(node.children, 1/2) (read-only). The assignment "
                     "`node.children = empty` requires FULL write permission, which "
                     "the precondition does not grant — insufficient permission, "
                     "before any value reasoning. Gold clauses kept verbatim so the "
                     "rejection is attributable to the write.",
    },
    {
        "id": "frame-mutate-connector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_CONNECTOR),
        "refinement": "setting self.connector = self.default inside deconstruct "
                      "would silently flip an OR node to AND (mutating the live "
                      "node): test_deconstruct_or and the round-trip "
                      "reconstruction tests observe the node's true connector; a "
                      "patch that overwrote it would lose the connector and fail "
                      "those tests — it does not resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: node.connector is held at "
                     "Acc(node.connector, 1/2). The write `node.connector = "
                     "node.default` needs full permission and is rejected for "
                     "insufficient permission (independent of clause (2a)).",
    },
    {
        "id": "frame-mutate-negated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_NEGATED),
        "refinement": "setting self.negated = False inside deconstruct would clear "
                      "a node's negation in place: test_deconstruct_negated / "
                      "test_reconstruct_negated observe and round-trip the negated "
                      "node; a patch that overwrote self.negated would drop the "
                      "negation and fail those tests — it does not resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: node.negated is held at "
                     "Acc(node.negated, 1/2). The write `node.negated = False` "
                     "needs full permission and is rejected for insufficient "
                     "permission (independent of clause (2b)).",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-single-child-special-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SINGLE_CHILD),
        "refinement": "THIS IS THE PRE-PATCH BUG that model_prepatch.py reproduces "
                      "and G-DIFF flags. The removed special case `if "
                      "len(self.children) == 1 and not isinstance(self.children[0], "
                      "Q): kwargs = {child[0]: child[1]}` left args empty and "
                      "relocated the lone child into kwargs. Every F2P test "
                      "(test_deconstruct, test_deconstruct_negated, test_"
                      "deconstruct_boolean_expression) exercises a single-child "
                      "node and now asserts args == (child,); test_deconstruct_"
                      "boolean_expression's Exists child also CRASHED pre-patch on "
                      "child[0]. The faithful pre-patch single-child branch is "
                      "exactly what does NOT resolve.",
        "rationale": "rejected by clause (1) Ensures(ToSeq(Result().args) == "
                     "ToSeq(node.children)): on a single-child node (n == 1) this "
                     "impl leaves args == [] while node.children has one element, "
                     "so ToSeq([]) != ToSeq(node.children). It is correct on the "
                     "multi-child sub-domain but diverges on the single-child sub-"
                     "domain (partial-domain).",
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_LAST),
        "refinement": "a patch that built args from all but the last child "
                      "(args = tuple(self.children[:-1])) would drop a condition "
                      "from the reconstruction triple: test_deconstruct_and / "
                      "test_deconstruct_multiple_kwargs / test_reconstruct observe "
                      "and rebuild the FULL children list; a deconstruct that "
                      "dropped the final child would lose an argument and the "
                      "round-trip Q(*args, **kwargs) != q — it does not resolve.",
        "rationale": "rejected by clause (1) Ensures(ToSeq(Result().args) == "
                     "ToSeq(node.children)): the loop runs to n-1 so ToSeq(args) == "
                     "ToSeq(node.children).take(n-1), which differs from the full "
                     "children sequence for every non-empty node (partial-domain: "
                     "correct only on the empty-children node).",
    },
    {
        "id": "uniq-connector-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CONN_FALSE),
        "refinement": "always reporting the connector kwarg ABSENT corresponds to a "
                      "patch that never emitted kwargs['_connector']: a non-default "
                      "(OR) node would deconstruct without its connector, so "
                      "Q(*args, **kwargs) would rebuild an AND node — "
                      "test_deconstruct_or / test_reconstruct_or observe the "
                      "'_connector' marker and round-trip it; this does not "
                      "resolve.",
        "rationale": "rejected by clause (2a) Ensures(connector_kwarg == "
                     "(node.connector != node.default)): a constant False cannot "
                     "equal the connector relation on a node whose connector "
                     "differs from default (node.connector != node.default is "
                     "True). Args loop kept gold so the rejection is isolated to "
                     "clause (2a).",
    },
    {
        "id": "uniq-negated-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NEG_FALSE),
        "refinement": "always reporting the negation kwarg ABSENT corresponds to a "
                      "patch that never emitted kwargs['_negated']: a negated node "
                      "would deconstruct without its negation, so Q(*args, "
                      "**kwargs) would rebuild a non-negated node — "
                      "test_deconstruct_negated / test_reconstruct_negated observe "
                      "the '_negated' marker and round-trip it; this does not "
                      "resolve.",
        "rationale": "rejected by clause (2b) Ensures(negated_kwarg == "
                     "node.negated): a constant False cannot equal node.negated on "
                     "a negated node (node.negated is True). Args loop + connector "
                     "flag kept gold so the rejection is isolated to clause (2b).",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-connector-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CONN_FLIP),
        "refinement": "inverting the connector guard (emit '_connector' iff "
                      "connector == default) would attach the connector marker to "
                      "DEFAULT (AND) nodes and drop it from non-default (OR) nodes: "
                      "exactly backwards. test_deconstruct (default AND node, "
                      "kwargs == {}) and test_deconstruct_or (OR node, kwargs has "
                      "'_connector') both observe the correct presence; the "
                      "inverted patch fails both — it does not resolve. Supporting "
                      "near-miss for the connector clause.",
        "rationale": "rejected by clause (2a) Ensures(connector_kwarg == "
                     "(node.connector != node.default)): node.connector == "
                     "node.default is the negation of the required relation; they "
                     "disagree on every node (whether connector equals default or "
                     "not).",
    },
]


# ===========================================================================
# AXIOM LANE — EMPTY. meta.json `axioms: []`: there is NO @ContractOnly axiom in
# this bundle. The changed operation (Q.deconstruct's args/kwargs computation) is
# modelled DEEPLY in the impl region (deconstruct_arguments), not consumed as an
# axiom. The deep model is an A-reference, validated == the real Q.deconstruct
# out-of-band by axiom_check.py / G-AX (already PASS in meta.json: exit 0 on the
# patched worktree over 18 boundary + 5000 fuzz nodes, and raises the exact
# problem-statement TypeError pre-patch). The spec-lane battery above does not
# CONSUME any axiom Ensures, so there is no axiom-soundness or axiom-containment
# obligation to discharge here. (Per PLAN §3: AXIOM_TESTS present only if the
# bundle has @ContractOnly axioms / A-refs consumed by the proof.)
# ===========================================================================
AXIOM_TESTS = []
