# properties.py — PBT manifest for django__django-11299. NOT a Nagini module; a
# record of adversarial, instance-specific falsification cases. The runner
# (swebench_nagini.pbt) writes each `module` to a temp file, verifies it with
# Nagini, and checks markers.same_spec against the frozen model.py. Every spec
# case edits ONLY text inside an `# impl-start`/`# impl-end` region, so the
# frozen spec (axioms/pure/pre/post/invariants) is provably untouched.
#
# Defended surface (read from model.py + refinement.md + instance.json):
#   compile_children(head: Optional[QNode], plain: bool) -> List[bool]
#     * head is a READ-ONLY input: Requires(Implies(head is not None,
#       Acc(q_pred(head), 1/2)))  -- only half permission, so the impl may NOT
#       write any field of the tree.
#     * load-bearing postcondition: Ensures(ToSeq(Result()) == leaf_modes(head, plain))
#       leaf_modes is a @Pure fold GROUNDED in (head, plain): a leaf contributes
#       PSeq(plain); a group contributes leaf_modes(inner, plain) +
#       leaf_modes(nxt, plain) -- the mode is forwarded unchanged at EVERY depth.
#   append_all(result: List[bool], src: List[bool]) -> None
#     * src is a READ-ONLY input: Requires(Acc(list_pred(src), 1/2)); result is
#       full-permission (genuinely mutated by append).
#     * Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src)).
#
# The gold edit (A5) is forwarding `plain` (not False) into the group descent;
# the prepatch reverts exactly that and fails the postcondition on nested leaves.

from pathlib import Path

INSTANCE = "django__django-11299"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors (each unique inside its own impl region) -----------------------

# compile_children group branch (the gold A5 descent + accumulation):
_GROUP_GOLD = (
    "    # group -> descend with the SAME mode, then continue with siblings.\n"
    "    sub = compile_children(head.inner, plain)\n"
    "    tail = compile_children(head.nxt, plain)\n"
    "    Fold(Acc(q_pred(head), 1 / 2))\n"
    "    append_all(result, sub)\n"
    "    append_all(result, tail)\n"
    "    return result"
)

# compile_children leaf branch:
_LEAF_GOLD = (
    "    if head.kind == 0:                          # leaf -> one column reference\n"
    "        result.append(plain)\n"
    "        rest = compile_children(head.nxt, plain)\n"
    "        append_all(result, rest)\n"
    "        Fold(Acc(q_pred(head), 1 / 2))\n"
    "        return result"
)

# compile_children head-is-None branch:
_NONE_GOLD = (
    "    result = []  # type: List[bool]\n"
    "    if head is None:\n"
    "        return result"
)

# append_all loop body:
_APPEND_BODY = (
    "        result.append(src[i])\n"
    "        i = i + 1"
)


# ============================================================================
# SPEC_TESTS
# ============================================================================

SPEC_TESTS = []

# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION on `head` (MANDATORY: head is Acc(q_pred(head),1/2)).
#    A rival that WRITES to the read-only tree to satisfy the postcondition
#    vacuously. After Unfold we hold full perm to head.kind/inner/nxt only
#    INSIDE the unfolding context; assigning head.kind here writes to the tree
#    field while the function holds only 1/2 of q_pred. The write needs FULL
#    permission to that field (the predicate body grants the field at the
#    fraction of the predicate instance held = 1/2), so it must be rejected for
#    INSUFFICIENT PERMISSION. Gold invariants kept verbatim => the rejection is
#    attributable solely to the write.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "frame-mut-head-field",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _LEAF_GOLD,
        "    if head.kind == 0:                          # leaf -> one column reference\n"
        "        head.kind = 0                           # WRITE to read-only tree (1/2 perm)\n"
        "        result.append(plain)\n"
        "        rest = compile_children(head.nxt, plain)\n"
        "        append_all(result, rest)\n"
        "        Fold(Acc(q_pred(head), 1 / 2))\n"
        "        return result"),
    "refinement": "The faithful real patch corresponding to this rival would mutate the "
                  "input Q/WhereNode tree node during compilation. _add_q must not rewrite "
                  "the user's condition tree; a patch that does so corrupts the shared Q "
                  "object and would break re-use of the same Q across queries (PASS_TO_PASS "
                  "query-construction tests build_where the same trees repeatedly), so it "
                  "would NOT resolve. This is a verify-without-doing-the-work attempt that "
                  "must fail on permissions.",
    "rationale": "head is held at Acc(q_pred(head),1/2); writing head.kind needs full "
                 "permission to that field, which the impl does not hold -> Nagini rejects "
                 "for insufficient permission. (permission system)",
})

# ---------------------------------------------------------------------------
# 2. FRAME-MUTATION on `src` in append_all (src is Acc(list_pred(src),1/2)).
#    A rival that writes to the read-only `src` list. The append on `src` needs
#    full list_pred(src) permission; only 1/2 is held => reject for insufficient
#    permission. Gold loop invariants kept verbatim.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "frame-mut-src-append",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _APPEND_BODY,
        "        result.append(src[i])\n"
        "        src.append(False)             # WRITE to read-only src (1/2 perm)\n"
        "        i = i + 1"),
    "refinement": "The corresponding real patch would mutate the source list of compiled "
                  "child clauses while accumulating them into the parent WhereNode. The "
                  "real accumulator (target_clause.add) must not append to the child's own "
                  "clause list; doing so would duplicate/garble the WhereNode and fail the "
                  "PASS_TO_PASS where-tree-shape assertions, so it would NOT resolve.",
    "rationale": "src is Acc(list_pred(src),1/2); src.append needs full list_pred(src) "
                 "permission -> rejected for insufficient permission. (permission system)",
})

# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN: the prepatch defect (A5 reverted). Group descent uses
#    `False` instead of `plain`, so nested (depth>=1) leaves get the wrong flag.
#    Correct on the depth-0 sub-domain (flat lists, leaf children), diverges on
#    any nested group. This is EXACTLY model_prepatch.py.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "partial-prepatch-descent-false",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _GROUP_GOLD,
        "    # group -> descend with the SAME mode, then continue with siblings.\n"
        "    sub = compile_children(head.inner, False)\n"
        "    tail = compile_children(head.nxt, plain)\n"
        "    Fold(Acc(q_pred(head), 1 / 2))\n"
        "    append_all(result, sub)\n"
        "    append_all(result, tail)\n"
        "    return result"),
    "refinement": "This is the literal pre-patch _add_q: the recursive call omits "
                  "simple_col (defaults False) so nested-group leaves resolve to Col not "
                  "SimpleCol. F2P test_simplecol_query asserts the nested-AND leaves "
                  "(where.children[0].children) have SimpleCol lhs; the prepatch yields Col "
                  "there -> FAIL_TO_PASS fails -> does NOT resolve.",
    "rationale": "postcondition ToSeq(Result()) == leaf_modes(head, plain): the group "
                 "clause is leaf_modes(head.inner, plain), but this impl produces "
                 "leaf_modes(head.inner, False); for plain=True and a leaf inside the "
                 "group these disagree (True != False). (postcondition group clause)",
})

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN: leaf emits a hardcoded True instead of `plain`. Correct
#    only on the plain=True sub-domain; wrong whenever plain=False. The
#    postcondition for a leaf is PSeq(plain), so True != False when plain=False.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "partial-leaf-hardcode-true",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _LEAF_GOLD,
        "    if head.kind == 0:                          # leaf -> one column reference\n"
        "        result.append(True)                     # hardcode plain regardless of mode\n"
        "        rest = compile_children(head.nxt, plain)\n"
        "        append_all(result, rest)\n"
        "        Fold(Acc(q_pred(head), 1 / 2))\n"
        "        return result"),
    "refinement": "The real patch counterpart always builds a bare SimpleCol regardless of "
                  "simple_col. That breaks every normal (non-check-constraint) query, which "
                  "needs the fully-qualified Col with its table alias for joins/SELECTs; "
                  "PASS_TO_PASS test_complex_query / test_foreign_key build_where with the "
                  "default mode and assert Col, so it would NOT resolve.",
    "rationale": "postcondition leaf clause is PSeq(plain); emitting True gives PSeq(True), "
                 "which differs from leaf_modes(head, plain) when plain is False. "
                 "(postcondition leaf clause)",
})

# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN: drop the nested-group descent entirely (omit `sub`). The
#    output then misses every leaf inside a group: correct on group-free input,
#    diverges (too few flags) whenever any group is present. Append order kept
#    valid; only `sub` is dropped. We keep the gold proof shape by computing sub
#    but never appending it -> the result misses the group's leaves.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "partial-drop-group-leaves",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _GROUP_GOLD,
        "    # group -> (BUG) skip the nested children, only continue with siblings.\n"
        "    sub = compile_children(head.inner, plain)\n"
        "    tail = compile_children(head.nxt, plain)\n"
        "    Fold(Acc(q_pred(head), 1 / 2))\n"
        "    append_all(result, tail)\n"
        "    return result"),
    "refinement": "The real patch counterpart would compile a nested group but never add "
                  "its child clause to the parent WhereNode, dropping the entire AND "
                  "sub-expression of the OR. The F2P check constraint OR(AND(...), ...) "
                  "would lose its AND branch -> wrong SQL / missing columns -> the "
                  "test_simplecol_query nested-leaf assertions fail -> does NOT resolve.",
    "rationale": "postcondition group clause is leaf_modes(inner, plain) + "
                 "leaf_modes(nxt, plain); dropping sub yields only leaf_modes(nxt, plain), "
                 "shorter than required whenever the group has >=1 leaf. (postcondition "
                 "group clause / sequence length)",
})

# ---------------------------------------------------------------------------
# 6. POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
#    Reorder the two recursive descents in the group branch (compute `tail`
#    before `sub`) while keeping the gold APPEND order (sub then tail) and the
#    Fold in the same place. Both calls run under the same 1/2 permission and
#    the accumulation order is unchanged, so the gold proof obligations all
#    still hold -- this MUST verify (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-control-reorder-descents",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _GROUP_GOLD,
        "    # group -> compute the descents in a different order; append unchanged.\n"
        "    tail = compile_children(head.nxt, plain)\n"
        "    sub = compile_children(head.inner, plain)\n"
        "    Fold(Acc(q_pred(head), 1 / 2))\n"
        "    append_all(result, sub)\n"
        "    append_all(result, tail)\n"
        "    return result"),
    "rationale": "A correct impl that only reorders the two independent recursive calls "
                 "(the appends stay sub-then-tail, Fold unchanged) computes the same "
                 "result == leaf_modes(head, plain) and must verify; if it cannot, the "
                 "spec would be SPEC-TOO-STRONG. (soundness)",
})

# ---------------------------------------------------------------------------
# 7. POSITIVE CONTROL / ADMISSIBILITY: confirm the precondition admits the
#    canonical F2P-shaped input shape. In the head-is-None branch, add a
#    self-call compile_children(None, plain) before returning -- this exercises
#    the Requires on a None head (Implies(None is not None, ...) is trivially
#    satisfiable) and asserts the empty-list result matches leaf_modes(None,...)
#    via the postcondition. It must verify (else PRECOND-TOO-STRONG on None).
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "admiss-none-head-selfcall",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _NONE_GOLD,
        "    result = []  # type: List[bool]\n"
        "    if head is None:\n"
        "        probe = compile_children(None, plain)   # admissibility: None is in-domain\n"
        "        Assert(ToSeq(probe) == leaf_modes(None, plain))\n"
        "        return result"),
    "rationale": "The precondition Implies(head is not None, Acc(q_pred(head),1/2)) must "
                 "admit head=None (the empty child-list base case the recursion actually "
                 "reaches). The self-call on None verifies and its postcondition pins the "
                 "empty result; if the call could not establish the Requires, the spec "
                 "would be PRECOND-TOO-STRONG. (admissibility)",
})


# ============================================================================
# AXIOM_TESTS
# ============================================================================
# meta.json axioms == [] : there is NO consumed @ContractOnly axiom. The
# changed behaviour is modelled DEEPLY (the @Pure leaf_modes fold + the verified
# recursive compile_children). The deep model leaf_modes is an A-REFERENCE,
# validated == the real Django Query.build_where by axiom_check.py / G-AX.
#
# An A-reference soundness probe is still meaningful here: run the REAL Django
# build_where in Docker and assert every leaf column is SimpleCol at every depth
# (i.e. observed flags == leaf_modes(tree, True) == all True) -- and that the
# pre-patch compiler (mode not forwarded) diverges on a nested leaf. This
# reuses/strengthens axiom_check.py's logic, embedded self-contained.

AXIOM_TESTS = [
    {
        "id": "axref-leaf_modes-vs-build_where",
        "axiom": "leaf_modes",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
    )
django.setup()

from django.db import models
from django.db.models import F, Q
from django.db.models.expressions import Col, SimpleCol
from django.db.models.sql.query import Query
from django.utils.tree import Node


class AxModel(models.Model):
    num = models.IntegerField()
    other = models.IntegerField()
    name = models.CharField(max_length=20)
    flag = models.BooleanField(default=False)

    class Meta:
        app_label = 'axch'


def _is_node(obj):
    return hasattr(obj, 'children') and hasattr(obj, 'connector')


def _leaf_cols(node, out):
    for child in node.children:
        if _is_node(child):
            _leaf_cols(child, out)
        else:
            for side in ('lhs', 'rhs'):
                expr = getattr(child, side, None)
                if isinstance(expr, (Col, SimpleCol)):
                    out.append(expr)
                else:
                    inner = getattr(expr, 'lhs', None)
                    if isinstance(inner, (Col, SimpleCol)):
                        out.append(inner)


def observed_flags(q_object):
    where = Query(AxModel).build_where(q_object)
    cols = []
    _leaf_cols(where, cols)
    assert cols, "no leaf columns collected for %r" % (q_object,)
    return [isinstance(c, SimpleCol) for c in cols]


cases = [
    (Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id')),
     "OR(AND(num>2, name isnull), num<F(id))  (issue/F2P shape)"),
    (Q(num__gt=2, flag=True) | Q(flag=False),
     "OR(AND(num>2, flag), flag=False)"),
    (Q(num__gt=2), "single"),
    (Q(num__gt=2) | Q(num__lt=0), "flat OR"),
    ((Q(num__gt=2) | Q(num__lt=0)) & (Q(other__gt=5) | Q(other__lt=1)),
     "AND(OR,OR) depth 1"),
    (Q(num__gt=2) | (Q(other__gt=1) & (Q(num__lt=9) | Q(other__lt=0))),
     "OR(leaf, AND(leaf, OR(leaf, leaf))) depth 2"),
    (~Q(num__gt=2, name__isnull=False) | Q(other__lt=0),
     "OR(NOT AND(...), leaf)"),
    (Q(num__gt=F('other')) | Q(num__lt=F('other'), other__gt=1),
     "OR(leaf, AND(num<F(other), other>1))"),
]

total = 0
for q, label in cases:
    flags = observed_flags(q)
    # axiom-soundness: under build_where (top mode simple_col=True), leaf_modes
    # predicts every flag True at every depth.
    assert all(flags), (
        "A-reference UNSOUND for %s: a nested leaf is Col (not SimpleCol); "
        "flags=%r" % (label, flags))
    total += len(flags)

# Discriminator: the pre-patch compiler (mode not forwarded into nested groups)
# must leave a nested leaf as a fully-qualified Col -- exactly what the frozen
# postcondition forbids and model_prepatch.py predicts.
def add_q_prepatch(query, q_object, simple_col):
    target = query.where_class(connector=q_object.connector,
                               negated=q_object.negated)
    for child in q_object.children:
        if isinstance(child, Node):
            cc, _ = query._add_q(child, set(), False, False, True, True)
        else:
            cc, _ = query.build_filter(
                child, can_reuse=set(), allow_joins=False,
                split_subq=True, simple_col=simple_col)
        if cc:
            target.add(cc, q_object.connector)
    return target


q_nested = Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id'))
buggy_where = add_q_prepatch(Query(AxModel), q_nested, True)
buggy_cols = []
_leaf_cols(buggy_where, buggy_cols)
buggy_flags = [isinstance(c, SimpleCol) for c in buggy_cols]
assert not all(buggy_flags), (
    "discriminator failed: pre-patch should leave a nested leaf as Col; "
    "flags=%r" % buggy_flags)
assert any(isinstance(c, Col) and not isinstance(c, SimpleCol)
           for c in buggy_cols), "expected a Col leaf in the buggy tree"

print("AX-REF OK: deep model leaf_modes == real build_where on %d trees "
      "(%d leaves, all SimpleCol at every depth); pre-patch discriminator "
      "yields a nested Col the frozen spec forbids." % (len(cases), total))
sys.exit(0)
''',
        "rationale": "No consumed @ContractOnly axiom (axioms==[]); leaf_modes is an "
                     "A-reference deep model. The probe runs the REAL Django build_where "
                     "(top mode simple_col=True, the caller's actual config) on 8 trees of "
                     "varying depth and asserts every leaf is SimpleCol (== leaf_modes(.,True) "
                     "all True); if the real callee produced a nested Col, the deep model "
                     "would be AXIOM-UNSOUND. The pre-patch discriminator confirms the spec "
                     "senses the change. Caller-domain containment is trivially satisfied: "
                     "the only top mode build_where uses is simple_col=True, and leaf_modes "
                     "is total over (Optional[QNode], bool).",
    },
]
