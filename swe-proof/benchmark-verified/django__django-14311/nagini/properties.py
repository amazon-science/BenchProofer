# properties.py — PBT manifest for django__django-14311.
#
# NOT a Nagini module: an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses. Each SPEC_TESTS case is a full model.py variant
# that shares the FROZEN spec (axioms/pure/pre/post-conditions byte-identical)
# and edits ONLY the impl region; it is checked by Nagini verify + markers.same_spec.
#
# Defended surface (select_module_name(name, parent) -> List[int]):
#   - Inputs name, parent are BOTH read-only: Acc(list_pred(_), 1/2). The
#     postcondition re-asserts the same 1/2 perm, so a mutating impl cannot frame
#     the write (frame-mutation probe MANDATORY).
#   - Load-bearing postconditions, three clauses:
#       (M)  ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent))
#       (D)  Implies(not marks_entry(ToSeq(name)),                 Result()==name)
#       (P)  Implies(marks_entry(ToSeq(name)) and len(parent)>0,   Result()==parent)
#     module_arg is the @Pure deep model:
#       module_arg(name,parent) = parent if marks_entry(name) and len(parent)>0 else name
#     grounded over the real inputs on top of the OPAQUE @ContractOnly classifier
#     marks_entry. There are THREE behaviour sub-domains:
#       (1) not marks_entry(name)                  -> Result == name   (F2P bug domain)
#       (2) marks_entry(name) and len(parent)>0    -> Result == parent
#       (3) marks_entry(name) and len(parent)==0   -> Result == name   (parent ignored)
#   - The opaque marks_entry forbids any constant-echo: an impl MUST branch on
#     the real classifier and copy the actually-selected sequence. Echoing
#     module_arg is CORRECT (deep model grounded in the inputs), so there is no
#     "wrong ungrounded-oracle echo" to build — see UNGROUNDED-ORACLE note below.
#
# AXIOM lane: the bundle has exactly one @ContractOnly callee, marks_entry, an
# A-reference (no contract consumed). axiom_check.py (G-AX) is the persisted
# A-reference oracle. We re-run its real-str-operation obligation in Docker as an
# axiom-soundness probe (does the real classifier+selection equal the deep model
# code-point-for-code-point) and add a containment probe (every callee-input the
# model can reach lies in marks_entry's Requires domain — which is trivially all
# of PSeq[int], so containment is vacuously total; documented below).

from pathlib import Path

INSTANCE = "django__django-14311"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim impl region body (between # impl-start and # impl-end). Every
# variant is produced by replacing exactly this block, so the swap is unique and
# touches ONLY the impl region (same_spec is guaranteed by region surgery).
_IMPL = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel and len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    return result
    # impl-end"""

assert _IMPL in _BASE, "drift: impl region body does not match model.py verbatim"
assert _BASE.count(_IMPL) == 1, "impl region body is not unique in model.py"


def _impl(new_body: str) -> str:
    """Return a full model.py source with the impl region body replaced by
    new_body (which MUST itself open with '    # impl-start' and close with
    '    # impl-end'), guaranteeing same_spec by region surgery."""
    if not new_body.startswith("    # impl-start"):
        raise AssertionError("impl body must start with the impl-start marker")
    if not new_body.rstrip().endswith("# impl-end"):
        raise AssertionError("impl body must end with the impl-end marker")
    return _BASE.replace(_IMPL, new_body, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# Flip the branch ORDER: handle the (not entry / empty-parent) `name` case FIRST
# by testing `not (sentinel and len(parent) > 0)`, then the parent case. Same two
# verified take-loops, same gold invariants + framing asserts kept verbatim
# (only reordered). A faithful correct impl MUST verify — else SPEC-TOO-STRONG.
# (Reorder, not a loop-direction flip: avoids the f(a+b)==f(a)+f(b) lemma trap.)
# ---------------------------------------------------------------------------
_POS_REORDER = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if not (sentinel and len(parent) > 0):
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    else:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    return result
    # impl-end"""

# POSITIVE CONTROL #2 — local-variable reshape: bind the selected source sequence
# to a single local `src` (a read-only alias), then run ONE copy loop over it.
# Structurally one loop instead of two, framed against module_arg directly. The
# spec helper module_arg is itself the front of the recursion (take(i) over the
# selected sequence), so the single loop keeps the same prefix invariant. Must
# verify (correct, different shape).
_POS_SINGLE_LOOP = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    if sentinel and len(parent) > 0:
        src = parent
    else:
        src = name
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 4))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result = result + [src[i]]
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # `src` aliases `name` or `parent`; the loop only borrows Acc(src,1/4), so the
    # full 1/2 perm on name/parent survives the loop. Bridge to module_arg here
    # (where both inputs are readable) rather than inside the invariant, which
    # would be ill-formed: an invariant holding only Acc(src,1/4) cannot read
    # ToSeq(name)/ToSeq(parent) under module_arg.
    Assert(ToSeq(src) == module_arg(ToSeq(name), ToSeq(parent)))
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY — a positive-control caller that constructs an F2P-shaped input
# (a directly-named module: name = "ab", parent = "a", with marks_entry false on
# this name in general is NOT assertable since marks_entry is opaque; instead we
# only exercise that the precondition Acc(list_pred(_),1/2) is establishable for
# fresh lists and the call site type-checks). We append a helper function in the
# impl region (still inside markers => same_spec) that allocates two fresh lists
# and calls select_module_name, asserting the result permission is returned. If
# the call site fails to verify, PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel and len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    return result


def _admiss_caller() -> None:
    # An F2P-shaped input: a directly-named module whose qualified name is two
    # code points and whose enclosing package is one code point. Fresh lists, so
    # the full predicate (hence the Requires Acc(...,1/2)) is establishable.
    nm = [97, 98]   # type: List[int]
    pa = [97]       # type: List[int]
    # A fresh list literal already carries Acc(list_pred(...)) in full; the
    # Requires Acc(...,1/2) is therefore directly establishable. (A manual
    # Fold(list_pred(nm)) on a literal-built list both is unnecessary and trips a
    # Nagini translator crash on the Fold-of-list_pred constructor overload.)
    out = select_module_name(nm, pa)
    # The post returns Acc(list_pred(Result())) in full and our 1/2 of each input.
    Assert(Acc(list_pred(out)))
    Assert(Acc(list_pred(nm), 1 / 2))
    Assert(Acc(list_pred(pa), 1 / 2))
    # impl-end"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION (uniqueness / reject) — MANDATORY: name is a read-only input
# (Acc(list_pred(name), 1/2)). This rival tries to satisfy the postcondition by
# WRITING into `name` (clearing it then copying parent into it) — exactly the
# move a mutating impl would make to dodge the result allocation. It MUST be
# rejected for INSUFFICIENT PERMISSION (only 1/2 of list_pred(name) is held; a
# write needs the full predicate). Gold postcondition + the result-copy loop are
# kept verbatim so the rejection is attributable solely to the write.
# refinement: a real patch that mutated __main__.__spec__.name in place would
# corrupt the live module spec object (a shared, read-only interpreter datum) and
# break every later read of __spec__.name in get_child_arguments and the test's
# own assertion — it would not resolve the F2P (and would crash P2P run_as tests).
# ---------------------------------------------------------------------------
_FRAME_MUTATE = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel and len(parent) > 0:
        # Attempt to overwrite the read-only input `name` in place rather than
        # allocate a fresh result. Requires full list_pred(name); only 1/2 held.
        name[0] = parent[0]
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN #1 (uniqueness / reject) — ALWAYS copy `name`. Correct on
# sub-domains (1) [not marks_entry] and (3) [marks_entry & empty parent], but
# WRONG on sub-domain (2) [marks_entry & non-empty parent], where module_arg ==
# parent. This is the natural "forgot to branch on the entry sentinel" bug. It
# fails postcondition clause (M)/(P) when marks_entry(name) holds with a
# non-empty parent.
# refinement: a real patch `name = spec.name` (drop the entry-file branch) would
# relaunch a package run through its __main__.py (e.g. `python -m django`,
# spec.name == 'django.__main__', parent == 'django') as `-m django.__main__`
# instead of `-m django` — breaking the P2P run_as-package tests
# (test_run_as_module / test_run_as_non_django_module).
# ---------------------------------------------------------------------------
_PARTIAL_ALWAYS_NAME = """    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(name):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 4))
        Invariant(Acc(list_pred(parent), 1 / 4))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        Invariant(MustTerminate(len(name) - i + 1))
        # invariants-end
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN #2 (uniqueness / reject) — when marks_entry(name) holds, copy
# `parent` REGARDLESS of whether parent is empty (drops the `len(parent) > 0`
# guard). Correct on sub-domains (1) [not marks_entry] and (2) [entry & non-empty
# parent], but WRONG on sub-domain (3) [entry & EMPTY parent], where module_arg
# == name (not parent == []). Fails clause (M)/(D): when marks_entry(name) and
# parent empty, module_arg == name but this returns [].
# refinement: a real patch `name = spec.parent if marks_entry(spec.name) else
# spec.name` (no `and spec.parent` truthiness guard) would relaunch a top-level
# `python -m __main__` (spec.name == '__main__', spec.parent == '') as `-m ''`
# (empty module name) instead of `-m __main__` — breaking the bare-entry-point
# relaunch (the entrypoint fallback / run_as tests with an empty parent).
# ---------------------------------------------------------------------------
_PARTIAL_PARENT_IGNORES_EMPTY = """    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN #3 / PRE-PATCH (uniqueness / reject) — the exact pre-patch bug:
# copy `parent` whenever it is NON-EMPTY, ignoring marks_entry entirely. Correct
# on sub-domain (2) [entry & non-empty parent] and (3-with-empty-parent collapses
# to name), but WRONG on sub-domain (1) when parent non-empty [a directly-named
# module: not marks_entry but parent non-empty -> module_arg == name, this
# returns parent]. This is precisely the F2P-failing behaviour (model_prepatch.py).
# refinement: this is the literal pre-patch code
# `if spec.parent: args += ['-m', spec.parent]` — it relaunches the directly-named
# module `utils_tests.test_module.main_module` as `-m utils_tests.test_module`,
# the exact failure the F2P test_run_as_non_django_module_non_package asserts
# against. Verbatim non-resolution.
# ---------------------------------------------------------------------------
_PARTIAL_PREPATCH = """    # impl-start
    result = []  # type: List[int]
    if len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# SUPPORTING near-miss (uniqueness / reject) — return an empty list always. A
# cheap mechanical near-miss: fails clause (M) on every non-empty selection. Kept
# only as a supporting tripwire that the runner's reject path works; the reasoned
# attacks above are the substance.
# refinement: a patch `name = ''` would relaunch as `-m ''`, resolving nothing.
# ---------------------------------------------------------------------------
_EMPTY_ALWAYS = """    # impl-start
    result = []  # type: List[int]
    return result
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "structurally-different CORRECT impl (branch order flipped: "
                     "name/else-case handled first), gold invariants + framing "
                     "asserts kept verbatim. Must verify or SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-single-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_SINGLE_LOOP),
        "rationale": "structurally-different CORRECT impl (one copy loop over a "
                     "selected-source alias `src`, framed directly against "
                     "module_arg). Must verify or SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fresh-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "a positive-control caller allocates two fresh lists (an "
                     "F2P-shaped directly-named module) -- each list literal "
                     "already carries Acc(list_pred(...)) -- and calls "
                     "select_module_name. If the Requires Acc(...,1/2) "
                     "cannot be established for a normal input => PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUTATE),
        "refinement": "a real patch that mutated __main__.__spec__.name in place "
                      "(name[0]=parent[0]) would corrupt the shared, read-only "
                      "interpreter ModuleSpec, breaking every later read of "
                      "spec.name in get_child_arguments and the test's own "
                      "assertion. It would not resolve the F2P and would crash the "
                      "P2P run_as tests.",
        "rationale": "rejected by the PERMISSION system: name is held at "
                     "Acc(list_pred(name),1/2) (read-only) by the Requires; the "
                     "in-place write name[0]=... needs the FULL predicate. "
                     "Insufficient permission, not a value mismatch.",
    },
    {
        "id": "partial-always-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_ALWAYS_NAME),
        "refinement": "the patch `name = spec.name` (no entry-file branch) "
                      "relaunches a package run through its __main__.py "
                      "(spec.name=='django.__main__', parent=='django') as "
                      "`-m django.__main__` instead of `-m django` — breaks the "
                      "P2P run_as-package tests (test_run_as_module / "
                      "test_run_as_non_django_module).",
        "rationale": "rejected by postcondition clause (M)/(P): on sub-domain "
                     "marks_entry(name) and len(parent)>0, module_arg==parent but "
                     "this returns name. Opaque marks_entry can be true there, so "
                     "Nagini cannot prove Result()==parent.",
    },
    {
        "id": "partial-parent-ignores-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_PARENT_IGNORES_EMPTY),
        "refinement": "the patch `name = spec.parent if marks_entry(spec.name) "
                      "else spec.name` (drops the `and spec.parent` guard) "
                      "relaunches a top-level entry point (spec.name=='__main__', "
                      "spec.parent=='') as `-m ''` (empty module name) instead of "
                      "`-m __main__` — breaks the bare-entry-point relaunch "
                      "(entrypoint fallback / run_as tests with empty parent).",
        "rationale": "rejected by postcondition clause (M)/(D): on sub-domain "
                     "marks_entry(name) and len(parent)==0, module_arg==name but "
                     "this returns parent ([]). The else-pin "
                     "Assert(module_arg==name) of the gold proof is exactly what "
                     "fails — but here even the rewritten impl cannot satisfy (M).",
    },
    {
        "id": "partial-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_PREPATCH),
        "refinement": "this is the literal PRE-PATCH code "
                      "`if spec.parent: args += ['-m', spec.parent]` — it "
                      "relaunches the directly-named module "
                      "`utils_tests.test_module.main_module` as "
                      "`-m utils_tests.test_module`, the exact non-resolution the "
                      "F2P test_run_as_non_django_module_non_package asserts "
                      "against (this is model_prepatch.py, G-DIFF-confirmed FAIL).",
        "rationale": "rejected by postcondition clause (M)/(D): on sub-domain "
                     "not marks_entry(name) with non-empty parent, module_arg==name "
                     "but this returns parent. The opaque marks_entry may be false "
                     "there, so Nagini cannot establish Result()==name.",
    },
    {
        "id": "empty-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_ALWAYS),
        "refinement": "a patch `name = ''` would relaunch as `-m ''`, resolving "
                      "nothing. Supporting tripwire only.",
        "rationale": "rejected by clause (M): returns [] but module_arg is "
                     "non-empty whenever the selected sequence is non-empty.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — exactly one @ContractOnly callee: marks_entry, an A-reference (no
# contract consumed). The persisted oracle is axiom_check.py (G-AX). We read it on
# the HOST at load time and embed its source into the probe so the probe is
# self-contained (the runner mounts only the probe at /work).
#
# axiom-soundness: re-run the A-reference obligation against the REAL Python str
# operations (the very ops the gold patch performs): the real classifier
# `name=='__main__' or name.endswith('.__main__')` and its selection equal the
# deep model module_arg code-point-for-code-point on boundary + 40000 fuzz inputs.
# Flag dependency: NONE (meta.axioms[0].flag_dependency / mapping.md §3.1 — plain
# single-suffix str.endswith / str.__eq__, no kwargs). apply_gold=True because the
# obligation describes the post-gold selection.
#
# axiom-containment: marks_entry's Requires domain is ALL of PSeq[int] (the
# @ContractOnly callee has no Requires — vacuously total). select_module_name only
# ever passes ToSeq(name) (a code-point sequence) to marks_entry, which is in the
# domain by construction. So containment is trivially total; we encode it as an
# explicit assertion (every reachable callee-input is a valid str/code-point
# sequence and lies in the unconstrained domain) so a future tightening of the
# Requires would be caught.
# ---------------------------------------------------------------------------
_AXIOM_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-soundness for marks_entry (A-reference): the real str classifier +\n"
    "# selection equal the deep model module_arg code-point-for-code-point. The\n"
    "# bundle oracle axiom_check.py is embedded verbatim (runner mounts only this\n"
    "# probe), then its main() is executed and its exit code is the verdict.\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_SRC) + "\n"
    "ns = {'__name__': '_embedded_axiom_check'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), ns)\n"
    "rc = ns['main']()\n"
    "print('axiom-soundness marks_entry A-reference: rc=%r' % rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

_AX_CONTAIN_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-containment for marks_entry: every callee-input select_module_name\n"
    "# can reach lies in marks_entry's Requires domain. marks_entry is\n"
    "# @Pure @ContractOnly with NO Requires => its domain is all of PSeq[int]\n"
    "# (every finite int sequence). select_module_name only ever evaluates\n"
    "# marks_entry(ToSeq(name)); ToSeq(name) is always a finite code-point\n"
    "# sequence, so it is in-domain by construction. We make this explicit by\n"
    "# checking that every name the model/G-AX exercises maps to a finite list of\n"
    "# Unicode code points (a valid PSeq[int] element), i.e. nothing the caller\n"
    "# reaches escapes the (unconstrained) callee domain.\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_SRC) + "\n"
    "ns = {'__name__': '_embedded_axiom_check'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), ns)\n"
    "to_codepoints = ns['to_codepoints']\n"
    "# Reconstruct the boundary names the caller can reach (same set as G-AX).\n"
    "boundary_names = [\n"
    "    '', '__main__', '.__main__', 'foo.__main__',\n"
    "    'utils_tests.test_module.__main__', 'django.__main__',\n"
    "    'utils_tests.test_module.main_module', 'foo.bar.baz', 'foo.bar', 'foo',\n"
    "    'foo.my__main__', 'my__main__', '__main__x', 'x__main__',\n"
    "    'a.b.__main__c', 'pkg.__main__.sub',\n"
    "]\n"
    "import random\n"
    "rng = random.Random(14311)\n"
    "segments = ['foo','bar','baz','main_module','manage','__main__','main__',\n"
    "            '__main','a','mod','pkg','sub']\n"
    "samples = list(boundary_names)\n"
    "for _ in range(5000):\n"
    "    k = rng.randint(0, 5)\n"
    "    samples.append('.'.join(rng.choice(segments) for _ in range(k)) if k else '')\n"
    "bad = []\n"
    "for nm in samples:\n"
    "    cps = to_codepoints(nm)\n"
    "    # in-domain iff a finite sequence of valid Unicode code points\n"
    "    if not (isinstance(cps, list) and all(isinstance(c, int) and 0 <= c <= 0x10FFFF for c in cps)):\n"
    "        bad.append(nm)\n"
    "if bad:\n"
    "    print('axiom-containment VIOLATION: caller-reachable name outside callee domain: %r' % bad[:5])\n"
    "    sys.exit(1)\n"
    "print('axiom-containment marks_entry: all %d caller-reachable names map to '\n"
    "      'finite Unicode code-point sequences (in marks_entry domain, which is '\n"
    "      'unconstrained PSeq[int])' % len(samples))\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-marks_entry",
        "axiom": "marks_entry",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "A-reference obligation: the real str classifier "
                     "`name=='__main__' or name.endswith('.__main__')` and its "
                     "selection equal the deep model module_arg "
                     "code-point-for-code-point on 16 boundary names x 6 parents + "
                     "40000 fuzz inputs (no flag dependency). If the real callee "
                     "disagrees, AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-marks_entry",
        "axiom": "marks_entry",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "marks_entry is @ContractOnly with no Requires (domain = all "
                     "PSeq[int]); select_module_name only passes ToSeq(name), a "
                     "finite code-point sequence, so every caller-reachable input "
                     "is in-domain. Covering more than the caller reaches is sound; "
                     "a reachable input outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER (impossible here).",
    },
]
