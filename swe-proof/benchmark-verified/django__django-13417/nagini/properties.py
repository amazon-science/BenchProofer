# properties.py — PBT manifest for django__django-13417. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) executes + stamps.
#
# Defended surface (read from model.py / refinement.md / instance.json):
#   `ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped)`
#   is a PURE boolean decision over five `bool` signals. There are:
#     * NO heap-carried / read-only (Acc(x,1/2)) inputs — every param is a `bool`
#       passed by value, so the FRAME-MUTATION class is N/A (nothing to overwrite,
#       no permission to violate).
#     * NO @ContractOnly axioms and NO A-reference deep models (axioms region is
#       empty; meta.axioms == []) — so AXIOM_TESTS = [].
#     * NO raise / return-vs-side-effect distinction invisible to the value
#       abstraction — the function only returns a bool; CONTROL-FLOW-EFFECT N/A.
#   The @Pure oracle `is_ordered` IS GROUNDED: it is a total boolean function of
#   the five args, fully unfolded in the contract (return (is_empty or
#   has_raw_order or (default_on and model_has_order and not is_grouped))). There
#   is therefore NO "wrong echo": `return is_ordered(...)` is the CORRECT answer,
#   not an answer-key the impl could cheat with. Per directive 2 we instead carry
#   that as an honest cheapest-impl POSITIVE CONTROL (expect=verify).
#
# The postcondition pins Result() == is_ordered(...) over all 2**5 = 32 input
# combinations, PLUS four pinned consequence clauses. The live falsification
# surface is therefore PARTIAL-DOMAIN: a rival correct on 31/32 combos but
# wrong on one combo (above all the discriminating combo the gold patch fixes:
# not-empty + no-raw-order + default_on + model_has_order + is_grouped -> the
# flag must be FALSE; the pre-patch body reports True). Those rivals MUST be
# rejected; the positive controls (structurally different but correct) MUST
# verify; an admissibility self-call MUST verify.
from pathlib import Path

INSTANCE = "django__django-13417"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of model.py (the gold-faithful body). Region surgery
# edits ONLY between # impl-start and # impl-end, so the frozen spec_view (and
# thus same_spec) is never touched.
_IMPL_GOLD = """    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _with_impl(new_impl_body):
    """Return _BASE with the gold impl region replaced by new_impl_body
    (which MUST itself begin with the indented '# impl-start' and end with
    '# impl-end' so the markers — and thus the impl region span — are preserved
    exactly; only the executable lines between them change)."""
    return _swap(_BASE, _IMPL_GOLD, new_impl_body)


# --------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls.
# These keep the same spec and MUST verify; if a faithful correct impl could
# not verify, the spec would be SPEC-TOO-STRONG.
# --------------------------------------------------------------------------

# pos-control-1: the cheapest honest impl — a single boolean return of the same
# disjunction the @Pure oracle unfolds. This is `return is_ordered(...)` written
# inline (the grounded oracle echo, which here is simply the correct answer).
_POS_SINGLE_RETURN = """    # impl-start
    return (
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )
    # impl-end"""

# pos-control-2: structurally different control flow — reorder the independent
# guards (test has_raw_order first, then is_empty) and split the conjunction
# into a nested branch. Logically identical truth table; no induction lemma or
# framing assert is needed (pure boolean), so this is a clean structural variant.
_POS_REORDER = """    # impl-start
    if has_raw_order:
        return True
    if is_empty:
        return True
    if default_on and model_has_order:
        if is_grouped:
            return False
        return True
    return False
    # impl-end"""

# pos-control-3: De Morgan / negated-form structural variant. Compute the single
# boolean via an intermediate typed local (the result), then return it. Same
# truth table, different shape.
_POS_LOCAL = """    # impl-start
    res = is_empty or has_raw_order  # type: bool
    if not res:
        res = default_on and model_has_order and not is_grouped
    return res
    # impl-end"""


# --------------------------------------------------------------------------
# ADMISSIBILITY — a self-call on an F2P-shaped input. The F2P regression test
# (`test_annotated_default_ordering`) exercises a queryset that is non-empty,
# has no explicit/raw ordering, inherits the model default ordering, AND is
# grouped (annotate -> GROUP BY): the flag MUST be False. We assert the
# precondition admits that exact input by calling `ordered(...)` with it and
# asserting the value abstraction's expected result. The precondition is now
# `MustTerminate(3 if is_empty else 2)` — a termination obligation, which
# constrains the CALLER's obligation level but admits every one of the 32 input
# combinations, so it must still accept these; else PRECOND-TOO-STRONG.
#
# The probes sit under `if is_empty:` deliberately. Nagini requires a callee's
# obligation level to be strictly BELOW the caller's, so a self-call can only
# discharge where the caller holds a higher level than the arguments it passes:
# on the empty branch the caller is at 3 and the probe's non-empty arguments put
# the callee at 2. An UNGUARDED probe fails the leak check under ANY level
# function, because the caller's own domain includes the probe's arguments and
# there the two levels coincide (measured). The guard is not vacuous: replacing
# these asserts with `Assert(False)` in the same position is REJECTED, so the
# branch is genuinely reachable and the probe really discharges.
# --------------------------------------------------------------------------
_ADMISS = """    # impl-start
    if is_empty:
        # F2P-shaped admissibility: annotate() result set with a Meta default
        # ordering and a GROUP BY (is_grouped=True) -> NOT ordered (the bug fix).
        Assert(not ordered(False, False, True, True, True))
        # And the same default ordering WITHOUT grouping IS ordered (PASS_TO_PASS
        # test_annotated_ordering's sibling: order_by('name') / non-grouped).
        Assert(ordered(False, False, True, True, False))
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end"""


# --------------------------------------------------------------------------
# PARTIAL-DOMAIN rivals (uniqueness) — each is correct on most of the 32-combo
# domain but diverges on a sub-domain. Each MUST be rejected by the
# postcondition. Each carries the refinement argument that its faithful real
# patch would NOT resolve the F2P/P2P.
# --------------------------------------------------------------------------

# weak-prepatch: the actual pre-patch bug — drop the `and not is_grouped`
# conjunct. Diverges on exactly the discriminating combo (grouped + default
# only). This is the bug the gold patch fixes; it MUST be rejected.
_RIVAL_PREPATCH = """    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order:
        return True
    else:
        return False
    # impl-end"""

# weak-flip-grouped: report a grouped default-only result set as ORDERED only
# when also model_has_order — i.e. uses `is_grouped` with the WRONG polarity
# (drops the `not`). Diverges on the grouped sub-domain in the opposite way to
# the gold (it would call a NON-grouped default-ordered set NOT ordered).
_RIVAL_FLIP = """    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and is_grouped:
        return True
    else:
        return False
    # impl-end"""

# weak-empty-misses-grouped: correct on every combo EXCEPT it forgets that an
# empty result set is always ordered when it is ALSO grouped (returns False for
# is_empty=True, is_grouped=True). Pins the is_empty consequence clause.
_RIVAL_EMPTY = """    # impl-start
    if is_empty and not is_grouped:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end"""

# weak-ignore-model-order: report ordered whenever default ordering is active
# and not grouped, even if the model declares NO default ordering
# (model_has_order=False). Diverges on the (default_on, not model_has_order,
# not grouped) sub-domain — claims ordered where there is no ordering to honour.
_RIVAL_NO_META = """    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and not is_grouped:
        return True
    else:
        return False
    # impl-end"""

# weak-constant-true: always-ordered. Trivially wrong (admits a grouped
# default-only set, a no-ordering set, etc.). Cheap supporting near-miss but it
# still carries a real refinement: its faithful patch (`return True`) would make
# every QuerysetOrderedTests negative-ordering assertion fail.
_RIVAL_TRUE = """    # impl-start
    return True
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-single-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_SINGLE_RETURN),
        "rationale": "the cheapest honest impl — a single boolean return of the "
                     "grounded disjunction (= is_ordered fully unfolded). Since "
                     "the oracle is grounded (a total function of the five args, "
                     "not an opaque answer key), this IS the correct answer and "
                     "MUST verify. A structurally-minimal correct impl failing "
                     "here would be SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": "structurally-different control flow (raw-order guard first, "
                     "then empty, then a nested is_grouped branch); same truth "
                     "table, no induction lemma or framing assert needed for a "
                     "pure boolean. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-local-var",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_LOCAL),
        "rationale": "compute the result into a typed local and return it; same "
                     "truth table, different shape. Must verify (else "
                     "SPEC-TOO-STRONG). Guards against a spec that only accepts "
                     "the exact gold branch structure.",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": "the (trivially-true) precondition must admit the F2P-shaped "
                     "input: a non-empty, raw-order-free, default-ordered, GROUPED "
                     "result set (annotate -> GROUP BY) for which the flag is "
                     "False, and the same set non-grouped for which it is True. "
                     "Asserting ordered(...) on these in-domain inputs must "
                     "verify (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "weak-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RIVAL_PREPATCH),
        "refinement": "this is the verbatim pre-patch property body (omits the "
                      "'and not is_grouped' conjunct). Its faithful real patch is "
                      "the UN-patched query.py, which FAILS the F2P tests "
                      "test_annotated_default_ordering / "
                      "test_annotated_values_default_ordering (it reports the "
                      "annotated GROUP-BY queryset as ordered=True when it must be "
                      "False). So a verifying rival here would be a true "
                      "verify-not-resolve break.",
        "rationale": "rejected by the postcondition clause Result() == "
                     "is_ordered(...), specifically the pinned "
                     "Implies(not is_empty and not has_raw_order and is_grouped, "
                     "not Result()): on (F,F,T,T,T) it returns True but the "
                     "oracle is False. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-flip-grouped-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RIVAL_FLIP),
        "refinement": "uses is_grouped with inverted polarity (drops the 'not'): "
                      "its faithful patch would report a NON-grouped default-"
                      "ordered queryset as not ordered and a grouped one as "
                      "ordered — failing both test_annotated_ordering "
                      "(non-grouped default ordering must stay ordered after "
                      "order_by) and the F2P grouped-default tests. Does not "
                      "resolve.",
        "rationale": "rejected by Result() == is_ordered(...): diverges on the "
                     "grouped sub-domain (e.g. (F,F,T,T,F): oracle True, rival "
                     "False; (F,F,T,T,T): oracle False, rival True). "
                     "SPEC-TOO-WEAK if it verified.",
    },
    {
        "id": "weak-empty-misses-grouped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RIVAL_EMPTY),
        "refinement": "drops the unconditional 'empty => ordered' guarantee for "
                      "grouped empty sets. Its faithful patch would report an "
                      "EmptyQuerySet that is also grouped as not ordered, failing "
                      "test_empty_queryset (P2P) for any grouped empty set. Does "
                      "not resolve.",
        "rationale": "rejected by the pinned clause Implies(is_empty, Result()): "
                     "on (T,*,*,*,T) it returns False but the oracle is True. "
                     "SPEC-TOO-WEAK if it verified.",
    },
    {
        "id": "weak-ignore-model-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RIVAL_NO_META),
        "refinement": "reports ordered when default ordering is active even if "
                      "the model declares no Meta.ordering (model_has_order=False). "
                      "Its faithful patch would report a queryset with no actual "
                      "ordering as ordered, failing "
                      "test_no_default_or_explicit_ordering / "
                      "test_cleared_default_ordering (P2P). Does not resolve.",
        "rationale": "rejected by Result() == is_ordered(...): diverges on "
                     "(F,F,T,F,F) (oracle False since model_has_order is False; "
                     "rival True). SPEC-TOO-WEAK if it verified.",
    },
    {
        "id": "weak-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RIVAL_TRUE),
        "refinement": "always returns True (cheap supporting near-miss). Its "
                      "faithful patch (`return True`) makes every negative-"
                      "ordering assertion fail: test_no_default_or_explicit_"
                      "ordering, test_cleared_default_ordering, and the F2P "
                      "grouped-default tests. Does not resolve.",
        "rationale": "rejected by Implies(not is_empty and not has_raw_order and "
                     "is_grouped, not Result()) on (F,F,T,T,T) and by "
                     "Result() == is_ordered(...) on the all-False input. "
                     "SPEC-TOO-WEAK if it verified.",
    },
]

# No @ContractOnly axioms / A-reference deep models in this bundle
# (meta.axioms == [], deep_model_references == []). The axiom lane is N/A.
AXIOM_TESTS = []
