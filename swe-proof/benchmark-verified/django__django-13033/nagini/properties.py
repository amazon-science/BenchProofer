# properties.py — PBT manifest for django__django-13033. NOT a Nagini module; a
# record of adversarial spec/axiom cases the runner (swebench_nagini.pbt) parses
# and executes. Spec cases are full model.py variants that share the FROZEN spec
# byte-for-byte (region-surgery: only the text strictly inside # impl-start /
# # impl-end is edited) and are checked by Nagini verify + same_spec. There are
# no @ContractOnly axioms / deep-model references in this bundle, so AXIOM_TESTS
# is empty.
#
# Defended surface (read from model.py + refinement.md):
#   ordering_mode(name, path_segments, relation_own_column,
#                 points_to_relation, has_default_ordering) -> int
#   Requires: len(path_segments) > 0
#            Implies(len(path_segments) > 1, name != path_terminal(path_segments))
#   Ensures: Result() == 0 or Result() == 1
#            (Result() == 1) ==
#                (points_to_relation and has_default_ordering
#                 and relation_own_column != path_terminal(path_segments)
#                 and name != PK())
#
# The load-bearing postcondition is the BICONDITIONAL: it pins Result() exactly
# (a 4-way conjunction equals mode==1). It is fully GROUNDED in the inputs — the
# @Pure helpers PK() (the constant PSeq(112,107)) and path_terminal (a pure
# index) are not opaque oracles, so there is no "wrong echo" to construct
# (justified in 'assessment'); instead the positive controls are honest
# structurally-different correct impls. All inputs are immutable value types
# (PSeq / bool) — there is NO Acc(x,1/2) read-only heap input, so the
# frame-mutation class does not apply (justified in 'assessment'). The rich
# attack surface is PARTIAL-DOMAIN: rivals that get the conjunction right on most
# of the domain but flip the answer on a specific sub-domain.
from pathlib import Path

INSTANCE = "django__django-13033"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl region (between the markers). Every variant is produced
# by _swap on this block, so the spec view (everything outside the markers) is
# never touched and same_spec is GUARANTEED.
_GOLD_IMPL = """    # impl-start
    if (points_to_relation and has_default_ordering
            and relation_own_column != path_terminal(path_segments)
            and name != PK()):
        return 1
    return 0
    # impl-end"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_impl_body):
    """Replace the whole gold impl region with a new one (markers preserved)."""
    new_region = "    # impl-start\n" + new_impl_body.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _GOLD_IMPL, new_region)


# Sanity: the gold impl block must be present verbatim exactly once.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted"


SPEC_TESTS = [
    # ----------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness): structurally-different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the Ensures,
    # the spec is SPEC-TOO-STRONG. These are pure-logic reshapes that keep the
    # exact same boolean function, so no induction lemma / framing assert is
    # needed (avoids the front-recursive-fold and dropped-assert pitfalls).
    # ----------------------------------------------------------------------
    {
        "id": "pos-control-nested-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Same boolean function, expressed as a guard ladder with the\n"
            "    # conjuncts reordered and the early-return shape inverted.\n"
            "    if not points_to_relation:\n"
            "        return 0\n"
            "    if not has_default_ordering:\n"
            "        return 0\n"
            "    if name == PK():\n"
            "        return 0\n"
            "    if relation_own_column == path_terminal(path_segments):\n"
            "        return 0\n"
            "    return 1"
        ),
        "rationale": "a correct impl built from short-circuit guards (conjuncts "
                     "reordered, returns inverted) computes the identical boolean "
                     "function and must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-local-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Same function via a named boolean local then a single branch.\n"
            "    substitute = (points_to_relation and has_default_ordering\n"
            "                  and relation_own_column != path_terminal(path_segments)\n"
            "                  and name != PK())  # type: bool\n"
            "    if substitute:\n"
            "        return 1\n"
            "    else:\n"
            "        return 0"
        ),
        "rationale": "binding the predicate to a typed local and branching on it "
                     "is a local-variable reshape that keeps the gold proof valid; "
                     "must verify (else SPEC-TOO-STRONG).",
    },
    # ----------------------------------------------------------------------
    # ADMISSIBILITY: a positive-control caller invokes ordering_mode on an
    # F2P-shaped in-domain input. If the Requires cannot be established for a
    # legitimate input, PRECOND-TOO-STRONG. We assert the precondition holds for
    # the issue's reproducer-shaped input: a 2-segment path record__root_id
    # whose terminal is root_id != the whole name (split invariant).
    # ----------------------------------------------------------------------
    {
        "id": "admiss-reproducer-caller",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # Gold body, unchanged.\n"
            "    if (points_to_relation and has_default_ordering\n"
            "            and relation_own_column != path_terminal(path_segments)\n"
            "            and name != PK()):\n"
            "        return 1\n"
            "    return 0\n"
            "\n"
            "\n"
            "def admiss_reproducer_caller() -> int:\n"
            "    # The admissibility probe: a real call to ordering_mode on a\n"
            "    # reproducer-shaped input -- a 2-segment lookup path whose final\n"
            "    # segment differs from the whole joined name (record__root_id).\n"
            "    # The call site must establish the Requires for this legitimate\n"
            "    # input, INCLUDING the termination obligation.\n"
            "    #\n"
            "    # Level 3, strictly above ordering_mode's level 2: a caller must\n"
            "    # outrank its obligated callee or the callee has no room beneath it\n"
            "    # ('Obligation leak check failed'). This probe used to make the call\n"
            "    # from INSIDE ordering_mode's own body at level 2 -- an unguarded\n"
            "    # self-call on constant arguments, i.e. unbounded recursion, which\n"
            "    # the termination obligation rightly refuses. Hoisting the call site\n"
            "    # into its own higher-level method keeps the probe's full strength\n"
            "    # (same arguments, same asserted preconditions, a real call that\n"
            "    # must discharge Requires) while giving the level ordering room.\n"
            "    Requires(MustTerminate(3))\n"
            "    Ensures(Result() == 0 or Result() == 1)\n"
            "    record = PSeq(114, 101, 99, 111, 114, 100)        # 'record'  # type: PSeq[int]\n"
            "    root_id = PSeq(114, 111, 111, 116, 95, 105, 100)  # 'root_id' # type: PSeq[int]\n"
            "    sep = PSeq(95, 95)                                 # '__'      # type: PSeq[int]\n"
            "    whole = record + sep + root_id  # type: PSeq[int]\n"
            "    segs = PSeq(record, root_id)  # type: PSeq[PSeq[int]]\n"
            "    Assert(len(segs) > 0)\n"
            "    Assert(len(segs) > 1)\n"
            "    Assert(path_terminal(segs) == root_id)\n"
            "    Assert(whole != path_terminal(segs))  # split invariant: whole carries the sep\n"
            "    sub = ordering_mode(whole, segs, root_id, True, True)  # type: int\n"
            "    Assert(sub == 0 or sub == 1)\n"
            "    return sub"
        ),
        "rationale": "the precondition must admit the issue's reproducer-shaped "
                     "2-segment path (record__root_id). The call establishes "
                     "Requires for a legitimate input; if it can't, PRECOND-TOO-STRONG. "
                     "The caller sits at MustTerminate level 3 so that ordering_mode's "
                     "level-2 obligation has room beneath it.",
    },
    # ----------------------------------------------------------------------
    # UNIQUENESS / PARTIAL-DOMAIN rivals (expect reject). Each shares the spec
    # exactly and changes only the impl; each diverges from the gold boolean
    # function on a NAMED sub-domain, so the biconditional postcondition must
    # reject it. Each carries the refinement argument that its faithful real
    # patch would NOT resolve the F2P.
    # ----------------------------------------------------------------------
    {
        "id": "rival-prepatch-operand-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # THE pre-patch bug: compare relation_own_column against the WHOLE\n"
            "    # joined name instead of the final segment path_terminal(...).\n"
            "    if (points_to_relation and has_default_ordering\n"
            "            and relation_own_column != name\n"
            "            and name != PK()):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "this is the literal pre-patch operand getattr(field,'attname',"
                      "None) != name. On the F2P reproducer record__root_id the "
                      "relation's attname is root_id == pieces[-1] != name, so this "
                      "predicate is True and wrongly substitutes the related model's "
                      "default '-id' ordering (extra join, descending) — exactly the "
                      "bug; test_order_by_self_referential_fk FAILS. verify⇏resolve.",
        "rationale": "rejected by the third conjunct of the biconditional "
                     "(relation_own_column != path_terminal(path_segments)): on a "
                     "multi-segment input with relation_own_column == path_terminal "
                     "but != name, the precondition forces name != path_terminal so "
                     "the impl returns 1 while the postcondition requires 0.",
    },
    {
        "id": "rival-drop-pk-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Drop the name != PK() conjunct. Diverges on the sub-domain where\n"
            "    # name == 'pk' (the primary-key shortcut) but the other three hold.\n"
            "    if (points_to_relation and has_default_ordering\n"
            "            and relation_own_column != path_terminal(path_segments)):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "dropping `name != 'pk'` means ordering by the bare 'pk' "
                      "shortcut on a relation with default ordering would wrongly "
                      "expand the related model's ordering instead of sorting by the "
                      "pk column directly — a real regression the patch's pk guard "
                      "prevents; would not resolve the suite (pk handling).",
        "rationale": "rejected by the biconditional: when name == PK() and the "
                     "first three conjuncts hold, the impl returns 1 but the "
                     "postcondition's RHS is False (name != PK() is False), so it "
                     "requires 0.",
    },
    {
        "id": "rival-drop-default-ordering-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Drop the has_default_ordering conjunct. Diverges when the related\n"
            "    # model declares NO default ordering but the other three hold.\n"
            "    if (points_to_relation\n"
            "            and relation_own_column != path_terminal(path_segments)\n"
            "            and name != PK()):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "a relation with NO Meta.ordering must sort by the named "
                      "column directly (mode 0); substituting a nonexistent default "
                      "ordering (mode 1) is wrong — the gold guard requires "
                      "opts.ordering truthy. Would not resolve.",
        "rationale": "rejected by the biconditional: with has_default_ordering "
                     "False but the other three True, impl returns 1 while the RHS "
                     "is False, so the postcondition requires 0.",
    },
    {
        "id": "rival-drop-relation-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Drop the points_to_relation conjunct. Diverges when the target is\n"
            "    # NOT a relation but the other three happen to hold.\n"
            "    if (has_default_ordering\n"
            "            and relation_own_column != path_terminal(path_segments)\n"
            "            and name != PK()):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "a non-relation target has no related model to expand an "
                      "ordering from; mode 1 is meaningless/wrong there. The gold "
                      "guard requires field.is_relation. Would not resolve.",
        "rationale": "rejected by the biconditional: points_to_relation False with "
                     "the other three True yields impl 1 but RHS False ⇒ requires 0.",
    },
    {
        "id": "rival-pk-operand-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Operand confusion on the pk conjunct: compare relation_own_column\n"
            "    # against PK() instead of name. Diverges when name == PK() but\n"
            "    # relation_own_column != PK() (and the other conjuncts hold).\n"
            "    if (points_to_relation and has_default_ordering\n"
            "            and relation_own_column != path_terminal(path_segments)\n"
            "            and relation_own_column != PK()):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "comparing the attname against 'pk' instead of comparing the "
                      "lookup name against 'pk' mis-guards the pk shortcut: ordering "
                      "by 'pk' on a relation whose attname is not 'pk' would wrongly "
                      "substitute the default ordering. Would not resolve.",
        "rationale": "rejected by the biconditional: choose name == PK() and "
                     "relation_own_column != PK() with the first three True — impl "
                     "returns 1 but RHS requires name != PK() (False) ⇒ 0.",
    },
    {
        "id": "rival-relation-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Cheap supporting near-miss: collapse the 4-conjunction to just\n"
            "    # points_to_relation. Correct only on the sub-domain where the\n"
            "    # other three always agree with points_to_relation.\n"
            "    if points_to_relation:\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "returning the related-default-ordering branch for EVERY "
                      "relation field ignores the attname/pk/ordering guards — the "
                      "exact over-substitution the issue reports; fails the F2P.",
        "rationale": "rejected by the biconditional on many sub-domains (e.g. "
                     "relation with relation_own_column == path_terminal): impl 1, "
                     "RHS 0.",
    },
    {
        "id": "rival-always-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Cheap supporting near-miss: never substitute the default ordering.\n"
            "    return 0"
        ),
        "refinement": "always taking the direct-target branch never expands ANY "
                      "related model's default ordering — the original feature "
                      "(ordering by a relation adopts its default order) breaks; "
                      "P2P ordering tests that rely on mode 1 fail. Would not resolve.",
        "rationale": "rejected by the biconditional whenever the 4-conjunction is "
                     "True (impl returns 0, RHS requires 1).",
    },
]

# No @ContractOnly axioms / deep-model references in this bundle (meta.axioms ==
# [], deep_model_references == []). The one external fact — the split invariant
# encoded by the precondition — is a precondition on the caller, not a consumed
# axiom; it is audited out-of-band by axiom_check.py against real str.split('__').
AXIOM_TESTS = []
