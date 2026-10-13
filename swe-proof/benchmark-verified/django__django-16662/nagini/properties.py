# properties.py — PBT falsification battery for django__django-16662.
#
# NOT a Nagini module. A manifest the runner swebench_nagini.pbt parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only the text BETWEEN `# impl-start` and
# `# impl-end` is edited) and a swapped impl; the runner checks it with Nagini
# verify + markers.same_spec. expect="verify" passes iff (same_spec AND
# verifies); expect="reject" passes iff (same_spec AND does NOT verify).
#
# Defended surface of this instance (see model.py / refinement.md / mapping.md):
#   arrange_lines(flags, modules) arranges 3 import lines into output order.
#   * flags  : Acc(list_pred(flags),  1/2)  -> READ-ONLY (frame-mutation target)
#   * modules: Acc(list_pred(modules), 1/2)  -> READ-ONLY (frame-mutation target)
#   The load-bearing postcondition is TWO clauses that together pin the output:
#     (M) multiset preservation:
#         ToMS(ToSeq(Result())) == ToMS(PSeq(compkey(f0,m0),compkey(f1,m1),
#                                            compkey(f2,m2)))   -- grounds the
#         result in EXACTLY the three input keys (no add/drop/duplicate);
#     (S) sortedness: Result()[0] <= Result()[1] <= Result()[2]  -- ascending in
#         compkey, which (compkey = is_from*1e9 + module, group flag dominating)
#         is exactly "plain imports before from-imports, module-ordered within".
#   compkey is GROUNDED: its Ensures is fully unfolded (a function of the args),
#   so there is no opaque answer-key oracle to echo (see 'assessment').
#
# The F2P (#24155, tests/migrations/test_writer.py::test_sorted_imports) asserts
# the rendered output contains
#   "import datetime\nimport time\nfrom django.db import migrations, models\n"
# i.e. the two plain imports precede the from-import even though the from-import
# module token "django.db" sorts lexicographically before "time". This is the
# discriminating configuration: flags=(0,0,1), modules=(datetime,time,django.db)
# with code(django.db) < code(time). Every reject rival below is paired with the
# real patch it corresponds to and an argument that that real patch would NOT
# resolve this F2P.

from pathlib import Path

INSTANCE = "django__django-16662"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# The frozen gold impl region (between # impl-start / # impl-end), verbatim. We
# only ever edit text inside this block, so spec_signature is preserved.
_GOLD_IMPL = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res"""

# sanity: the gold impl block must appear once in the frozen model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted from model.py"


def _with_impl(new_impl_body):
    """Return _BASE with the gold impl body replaced by new_impl_body (both are
    the lines strictly between the markers). same_spec is preserved because the
    swap is confined to the impl region."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# --------------------------------------------------------------------------
# SPEC LANE
# --------------------------------------------------------------------------

# (1) POSITIVE CONTROL (soundness). A structurally-DIFFERENT but CORRECT sort:
#     the gold uses the comparison network CS(x,y); CS(y,z); CS(x,y); this uses
#     the equally-valid 3-element network CS(y,z); CS(x,y); CS(y,z) with renamed
#     locals. Both produce the unique ascending permutation. The per-step
#     multiset framing asserts are KEPT (each compare-swap preserves the
#     multiset regardless of which pair it touches), so the gold proof
#     obligations the verifier needs still hold. If a faithful correct impl
#     cannot verify => SPEC-TOO-STRONG.
_POS_NETWORK = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    a = k0
    b = k1
    c = k2
    if b > c:
        s = b
        b = c
        c = s
    Assert(ToMS(PSeq(a, b, c)) == ToMS(PSeq(k0, k1, k2)))
    if a > b:
        s2 = a
        a = b
        b = s2
    Assert(ToMS(PSeq(a, b, c)) == ToMS(PSeq(k0, k1, k2)))
    if b > c:
        s3 = b
        b = c
        c = s3
    Assert(ToMS(PSeq(a, b, c)) == ToMS(PSeq(k0, k1, k2)))
    out = [a, b, c]  # type: List[int]
    Assert(ToSeq(out) == PSeq(a, b, c))
    return out"""

# (2) ADMISSIBILITY (precondition not vacuous / accepts an F2P-shaped input).
#     Keep the gold sort, then ADD asserts that the precondition genuinely
#     admits the F2P-shaped configuration flags=(0,0,1) with
#     modules[0] < modules[1] and modules[2] < modules[1] (code(django.db) <
#     code(time)): i.e. the discriminating input is in-domain and the sorted
#     result is reachable. If this cannot verify => PRECOND-TOO-STRONG.
_ADMISS = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    # the precondition admits the F2P-shaped grouped configuration:
    # two plain imports (flag 0) then a from-import (flag 1), with the
    # from-import's module token sorting before the second plain import's.
    Assert(Implies(flags[0] == 0 and flags[1] == 0 and flags[2] == 1,
                   k0 < 1000000000 and k1 < 1000000000 and k2 >= 1000000000))
    Assert(Implies(flags[0] == 0 and flags[1] == 0 and flags[2] == 1,
                   k0 <= k2 and k1 <= k2))
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res"""

# (3) FRAME-MUTATION (MANDATORY: flags / modules are Acc(...,1/2) read-only).
#     A rival that WRITES the read-only input `flags` (assigning a list element
#     needs FULL permission). The gold sort + invariants are kept verbatim so
#     the rejection is attributable to the write, not to a value defect. This
#     MUST fail for INSUFFICIENT PERMISSION.
_FRAME_FLAGS = """    flags[0] = 0  # FRAME VIOLATION: writes read-only input (needs full perm)
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res"""

# (3b) FRAME-MUTATION on `modules` (the secondary read-only carrier), supporting.
_FRAME_MODULES = """    modules[2] = 0  # FRAME VIOLATION: writes read-only input (needs full perm)
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res"""

# (4) PARTIAL-DOMAIN — the most behaviourally-meaningful rival: arrange by
#     MODULE NAME ALONE, ignoring the group flag (this is the PRE-PATCH key
#     `sorted(imports, key=lambda i: i.split()[1])`). Correct on inputs where
#     the module-only order already happens to be grouped, but on the F2P
#     configuration (modules: datetime < django.db < time, flags 0,0,1) it
#     interleaves the from-import "django.db" between the two plain imports,
#     violating clause (S) (the result is NOT ascending in compkey: a flag-1
#     key ~1e9 lands before a flag-0 key ~time). expect="reject".
_PARTIAL_MODULE_ONLY = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    m0 = modules[0]
    m1 = modules[1]
    m2 = modules[2]
    x = k0
    y = k1
    z = k2
    mx = m0
    my = m1
    mz = m2
    if mx > my:
        t = x
        x = y
        y = t
        tm = mx
        mx = my
        my = tm
    if my > mz:
        t2 = y
        y = z
        z = t2
        tm2 = my
        my = mz
        mz = tm2
    if mx > my:
        t3 = x
        x = y
        y = t3
        tm3 = mx
        mx = my
        my = tm3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res"""

# (5) IDENTITY (sortedness dropped) — return the input keys in INPUT order with
#     no sort. Multiset-preserving (clause M holds) but violates clause (S) on
#     any input whose key sequence is not already ascending (e.g. the F2P
#     configuration after the renderer assembles imports: a from-import key
#     ~1e9 can precede a plain-import key). expect="reject".
_IDENTITY = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    res = [k0, k1, k2]  # type: List[int]
    Assert(ToSeq(res) == PSeq(k0, k1, k2))
    return res"""

# (6) VALUE DROP/DUPLICATE — a sorted-LOOKING output that drops one key and
#     duplicates another: return [min, min, max]. After the gold network
#     (x<=y<=z) this is ascending (clause S holds) but the multiset {x,x,z} !=
#     {x,y,z} when y differs (clause M FAILS). Pins that clause (M) genuinely
#     grounds the result. expect="reject".
_DROP_DUP = """    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    if y > z:
        t2 = y
        y = z
        z = t2
    if x > y:
        t3 = x
        x = y
        y = t3
    res = [x, x, z]  # type: List[int]  # drops y, duplicates x (sorted-looking)
    Assert(ToSeq(res) == PSeq(x, x, z))
    return res"""

# (7) CONSTANT — supporting cheap near-miss: return [0,0,0]. Ascending (S holds)
#     but its multiset is {0,0,0}, not the input keys (M FAILS unless all keys
#     are 0, impossible since at most one line can key 0). expect="reject".
_CONST = """    empty = [0, 0, 0]  # type: List[int]
    return empty"""


SPEC_TESTS = [
    {
        "id": "pos-control-sort-network",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_NETWORK),
        "rationale": (
            "A structurally-different but CORRECT 3-element sorting network "
            "(CS(y,z); CS(x,y); CS(y,z) instead of the gold CS(x,y); CS(y,z); "
            "CS(x,y)), with renamed locals and the gold per-step multiset "
            "framing asserts kept. It computes the same unique ascending "
            "permutation, so it MUST verify against both postcondition clauses; "
            "if it cannot, the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": (
            "Gold sort plus asserts that the precondition admits the F2P-shaped "
            "grouped configuration flags=(0,0,1) (two plain imports keying "
            "below 1e9, a from-import keying at/above 1e9 dominating both). If "
            "the verifier cannot establish these for an in-domain input the "
            "precondition is PRECOND-TOO-STRONG (rejects a normal input)."
        ),
    },
    {
        "id": "frame-mutation-flags",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_FLAGS),
        "refinement": (
            "Corresponds to a real patch that mutates an element of the "
            "read-only `imports` collection (e.g. rewriting a line in place) "
            "before/while sorting. The gold patch only changes the sort KEY and "
            "never mutates a line; a mutating patch would alter the rendered "
            "import text and fail the F2P assertion "
            "'import datetime\\nimport time\\nfrom django.db import migrations, "
            "models\\n'. So a verifying mutator would be a verify-without-resolve "
            "break."
        ),
        "rationale": (
            "Writing flags[0] requires FULL permission on list_pred(flags), but "
            "the precondition grants only Acc(list_pred(flags), 1/2). The "
            "rejection comes from the PERMISSION SYSTEM (insufficient "
            "permission), not a value defect — the gold sort + invariants are "
            "kept verbatim. This is the project's #1 weakness class."
        ),
    },
    {
        "id": "frame-mutation-modules",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MODULES),
        "refinement": (
            "Same family as frame-mutation-flags but on the secondary read-only "
            "carrier `modules` (the module-name codes). A real patch overwriting "
            "a module token would change which line keys where and corrupt the "
            "rendered output, failing the F2P assertion. Supporting case for the "
            "second half-permission input."
        ),
        "rationale": (
            "Assigning modules[2] needs full permission on list_pred(modules); "
            "the precondition grants only Acc(list_pred(modules), 1/2). Rejected "
            "by the PERMISSION SYSTEM for insufficient permission."
        ),
    },
    {
        "id": "partial-domain-module-only-sort",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_MODULE_ONLY),
        "refinement": (
            "This IS the pre-patch behaviour: real key "
            "`lambda i: i.split()[1]` (module name only), the exact code the "
            "gold patch replaced. On the F2P configuration it interleaves "
            "'from django.db import ...' (module django.db) BETWEEN 'import "
            "datetime' and 'import time' because django.db < time, producing "
            "'import datetime\\nfrom django.db import migrations, models\\n"
            "import time' — NOT the asserted "
            "'import datetime\\nimport time\\nfrom django.db import ...'. The "
            "real patch (= reverting the key) demonstrably FAILS the F2P "
            "(model_prepatch.py reproduces this), so it cannot resolve."
        ),
        "rationale": (
            "Sorting by module code alone places a from-import key (flag 1, "
            "~1e9) before a plain-import key (flag 0, ~time) when its module "
            "code is smaller, so Result()[i] are NOT ascending in compkey: "
            "clause (S) Result()[0] <= Result()[1] <= Result()[2] is violated. "
            "Rejection comes from the SORTEDNESS postcondition — exactly the "
            "discriminating clause (G-DIFF)."
        ),
    },
    {
        "id": "identity-no-sort",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_IDENTITY),
        "refinement": (
            "Corresponds to a real patch that drops the sort entirely "
            "(`sorted_imports = imports` / `list(imports)`). Multiset-correct "
            "but emits import lines in arbitrary/assembly order, so it cannot "
            "guarantee the F2P-asserted grouped, ascending substring and would "
            "not resolve."
        ),
        "rationale": (
            "Returns the keys in input order; for any input whose key sequence "
            "is not already ascending (the verifier considers all in-domain "
            "inputs, incl. a from-import key preceding a plain-import key) clause "
            "(S) Result()[0] <= Result()[1] <= Result()[2] fails. Rejection from "
            "the SORTEDNESS postcondition."
        ),
    },
    {
        "id": "value-drop-duplicate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_DUP),
        "refinement": (
            "Corresponds to a real patch that drops one import line and "
            "duplicates another (e.g. a buggy de-dup) while keeping things "
            "sorted. The rendered output would be missing 'import time' and "
            "duplicate 'import datetime', failing the F2P substring assertion."
        ),
        "rationale": (
            "After the gold network (x<=y<=z) the output [x, x, z] is ascending "
            "so clause (S) holds, but its multiset {x, x, z} differs from the "
            "input multiset {x, y, z} whenever the three keys are distinct. "
            "Clause (M) ToMS(ToSeq(Result())) == ToMS(PSeq(compkey...)) fails. "
            "Rejection from the MULTISET-PRESERVATION postcondition — proving it "
            "genuinely grounds the result in the input keys."
        ),
    },
    {
        "id": "constant-zeros",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_CONST),
        "refinement": (
            "Supporting cheap near-miss: a real impl returning a fixed canned "
            "ordering would emit unrelated text and never reproduce any F2P "
            "import lines; it cannot resolve."
        ),
        "rationale": (
            "[0,0,0] is ascending (clause S holds) but its multiset {0,0,0} is "
            "not the input key multiset (at most one input key can equal 0, since "
            "two zero keys would require two identical (flag,module) pairs). "
            "Clause (M) fails. Rejection from the MULTISET-PRESERVATION "
            "postcondition (and grounds why the oracle is not echo-able)."
        ),
    },
]


# --------------------------------------------------------------------------
# AXIOM LANE
# --------------------------------------------------------------------------
# meta.json axioms == [] : there is NO @ContractOnly axiom. The single
# out-of-text trust point is the A-reference of compkey (validated by
# axiom_check.py / G-AX, NOT consumed inside the proof). Per PLAN §4 the axiom
# lane covers @ContractOnly axioms / A-consumed deep models; an A-reference that
# is never consumed by the verified proof is not an axiom obligation the spec
# leans on. It is exercised below as a single soundness probe purely as defence
# in depth (re-running axiom_check.py's host-side oracle: compkey order == real
# Python tuple key, and real sorted(gold_key) == ascending-compkey order incl.
# the F2P configuration, plus the pre-fix key rejected). This needs NO repo code
# (sorted + the one-line gold key are plain Python), so it runs anywhere.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "aref-compkey-order-vs-real-sorted",
        "axiom": "compkey",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,  # the gold key + sorted are plain Python; no repo code needed
        "probe": _AXIOM_CHECK_SRC,
        "rationale": (
            "The A-reference of refinement.md step A2: ascending compkey order "
            "must equal ascending real Python tuple-key order "
            "((i.split()[0]=='from', i.split()[1])), and the real "
            "sorted(gold_key) must produce the grouped/ascending order the model "
            "encodes (incl. the F2P config import datetime/import time/from "
            "django.db ...), with the pre-fix module-only key rejected. Runs "
            "axiom_check.py verbatim (host-side oracle, stdlib only); exit 0 iff "
            "the reference holds. If it disagreed the deep model compkey would be "
            "UNSOUND vs the real sort."
        ),
    },
]
