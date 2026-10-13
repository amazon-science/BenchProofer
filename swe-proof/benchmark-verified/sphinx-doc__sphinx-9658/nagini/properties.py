# properties.py — PBT falsification battery for sphinx-doc__sphinx-9658.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# exactly ONE `# impl-start` .. `# impl-end` block (of one of the three modeled
# functions) for a new body and leave the frozen spec (pure / pre / post-
# conditions / signatures) byte-identical. spec_view elides every impl region
# (its nested invariants included), so same_spec is GUARANTEED for every case
# regardless of the proof scaffolding inside the body.
#
# DEFENDED SURFACE (read from model.py / refinement.md / mapping.md / meta.json):
#   Three modeled functions, all carrying identifiers as List[int] of Unicode
#   code points, specified over PSeq[int] via ToSeq.
#
#   subclass_short_name(name) -> List[int]        [models _make_subclass attrs '__name__': name]
#     Requires Acc(list_pred(name), 1/2)          # name is READ-ONLY (half perm)
#     Requires MustTerminate(2)                   # (T) result must actually be delivered
#     Ensures  Acc(list_pred(name), 1/2)          # hands the half back
#     Ensures  Acc(list_pred(Result()))
#     Ensures  ToSeq(Result()) == ToSeq(name)     # (S) the SHORT identifier IS the attribute name
#
#   placeholder_display_name(short_name) -> List[int]   [models __qualname__ = self.__name__]
#     Requires Acc(list_pred(short_name), 1/2)    # short_name is READ-ONLY (half perm)
#     Requires MustTerminate(2)                   # (T) result must actually be delivered
#     Ensures  Acc(list_pred(short_name), 1/2)
#     Ensures  Acc(list_pred(Result()))
#     Ensures  ToSeq(Result()) == ToSeq(short_name)  # (D) DISPLAY identifier IS the short identifier (NOT '')
#
#   qualified_reference(name, module) -> List[int]   [models restify: '<module>.<__qualname__>']
#     Requires Acc(list_pred(name), 1/2)          # name   is READ-ONLY (half perm)
#     Requires Acc(list_pred(module), 1/2)        # module is READ-ONLY (half perm)
#     Requires MustTerminate(3)                   # (T) room to invoke the two helpers (measure 2)
#     Ensures  Acc(list_pred(name), 1/2); Acc(list_pred(module), 1/2); Acc(list_pred(Result()))
#     Ensures  ToSeq(Result()) == render_qualified(ToSeq(module), ToSeq(name))   # (Q1)
#     Ensures  ToSeq(Result()) == ToSeq(module) + dot() + ToSeq(name)            # (Q2) explicit dotted join
#     Ensures  Implies(len(name) > 0, len(Result()) > len(module) + 1)           # (Q3) ANTI-DANGLING-DOT
#
#   The (T) clauses are the termination discipline: every impl must DISCHARGE
#   the caller's MustTerminate obligation (loops carry a strictly decreasing,
#   bounded-below MustTerminate measure; callees carry a strictly smaller
#   obligation). A non-terminating body (frozen loop / self-recursion) can no
#   longer satisfy the value clauses vacuously.
#
#   render_qualified(module, display) == module + dot() + display is @Pure and
#   FULLY GROUNDED / transparent in its arguments (a structural concatenation,
#   not an opaque answer-key). dot() == PSeq(46) is the literal '.'. Because the
#   oracle is transparent, there is NO "wrong echo": any impl that satisfies Q1
#   has actually built `module + '.' + name`. See 'assessment' (ungrounded-oracle
#   class is N/A here; replaced by an honest cheapest-impl positive control).
#
#   The discriminating fix the F2P (tests/test_util_typing.py::test_restify_mock)
#   exercises is precisely (S)+(D)+(Q3): a placeholder reached by attribute `name`
#   records __name__ == name (S), propagates it to __qualname__ (D), so the
#   renderer restify composes '<module>.<name>' (Q2) and NEVER the dangling
#   '<module>.' (Q3). The pre-patch hard-set __qualname__ = '' (model_prepatch.py)
#   and recorded no __name__ (model_prepatch_2.py); each FAILS its (D)/(S) clause.
#
# READ-ONLY INPUTS (Acc(...,1/2)) -> FRAME-MUTATION IS MANDATORY:
#   `name` in subclass_short_name and qualified_reference; `short_name` in
#   placeholder_display_name; `module` in qualified_reference. Each modeled
#   function reads its identifier inputs and hands the half-permission back in
#   its Ensures. Any impl that WRITES to one of these inputs holds only half
#   permission and MUST be rejected for INSUFFICIENT PERMISSION (frame-mutation
#   cases below). The gold post-conditions/invariants are kept verbatim so the
#   rejection is attributable solely to the illegal write, not a value mismatch.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9658"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The three whole-impl anchors, verified verbatim from model.py. Each is unique
# in _BASE (block 1 reads `name`, block 2 reads `short_name`, block 3 opens with
# `subclass_short_name(name)`), so a _swap on any one block targets exactly that
# function and leaves the other two — and the entire frozen spec — untouched.
# Each replacement re-emits `# impl-start` first and `# impl-end` last so the
# region boundary is preserved exactly; spec_view elides all of it.
# ---------------------------------------------------------------------------
_IMPL_SHORT = (
    "# impl-start\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(name):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(name))\n"
    "        Invariant(ToSeq(result) == ToSeq(name).take(i))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(name) - i.\n"
    "        Invariant(MustTerminate(len(name) - i))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))\n"
    "        result = result + [name[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(name).take(len(name)) == ToSeq(name))\n"
    "    return result\n"
    "    # impl-end"
)

_IMPL_DISPLAY = (
    "# impl-start\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(short_name):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(short_name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(short_name))\n"
    "        Invariant(ToSeq(result) == ToSeq(short_name).take(i))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(short_name) - i.\n"
    "        Invariant(MustTerminate(len(short_name) - i))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))\n"
    "        result = result + [short_name[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(short_name).take(len(short_name)) == ToSeq(short_name))\n"
    "    return result\n"
    "    # impl-end"
)

_IMPL_QREF = (
    "# impl-start\n"
    "    short = subclass_short_name(name)\n"
    "    display = placeholder_display_name(short)\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(module):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(module), 1 / 2))\n"
    "        Invariant(Acc(list_pred(display)))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(module))\n"
    "        Invariant(ToSeq(display) == ToSeq(name))\n"
    "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(module) - i.\n"
    "        Invariant(MustTerminate(len(module) - i))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
    "        result = result + [module[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
    "    result = result + [46]\n"
    "    result = result + display\n"
    "    return result\n"
    "    # impl-end"
)

# Cross-check the anchors are exactly the three blocks in the frozen model.
assert _BASE.count(_IMPL_SHORT) == 1, "short-name impl anchor drift"
assert _BASE.count(_IMPL_DISPLAY) == 1, "display impl anchor drift"
assert _BASE.count(_IMPL_QREF) == 1, "qref impl anchor drift"


def _short(body: str) -> str:
    return _swap(_BASE, _IMPL_SHORT,
                 "# impl-start\n" + body.rstrip("\n") + "\n    # impl-end")


def _display(body: str) -> str:
    return _swap(_BASE, _IMPL_DISPLAY,
                 "# impl-start\n" + body.rstrip("\n") + "\n    # impl-end")


def _qref(body: str) -> str:
    return _swap(_BASE, _IMPL_QREF,
                 "# impl-start\n" + body.rstrip("\n") + "\n    # impl-end")


SPEC_TESTS = [

    # ======================================================= soundness (1 of 3)
    # POSITIVE CONTROL A (low-risk local-variable reshape on qualified_reference,
    # the end-to-end observable). The module-copy loop's index is renamed i -> k
    # and the post-loop appends are spelled as a single combined concatenation
    # `result = result + ([46] + display)` instead of two statements. Every gold
    # invariant/assert is kept VERBATIM (with i->k inside the loop) so no framing
    # is dropped; the spec helper render_qualified is front-structured exactly as
    # this forward build, so no associativity/fold lemma is introduced. A
    # structurally-different but CORRECT impl. If it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-qref-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _qref(
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    k = 0\n"
            "    while k < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= k and k <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(k))\n"
            "        Invariant(MustTerminate(len(module) - k))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(k + 1).drop(k) == PSeq(module[k]))\n"
            "        result = result + [module[k]]\n"
            "        k = k + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    result = result + ([46] + display)\n"
            "    return result\n"
        ),
        "rationale": "a CORRECT impl with a different executable shape (loop index "
                     "i->k; the two trailing appends folded into one "
                     "`result + ([46] + display)`) must verify. Keeps every gold "
                     "invariant/assert; the forward build matches the front-structured "
                     "render_qualified (no fold lemma needed). Else SPEC-TOO-STRONG.",
    },

    # ======================================================= soundness (2 of 3)
    # POSITIVE CONTROL B (low-risk local-variable reshape on subclass_short_name).
    # Rename the loop index i -> k throughout, keeping each invariant/assert
    # verbatim (with k). The carrier copy still builds ToSeq(name); a genuinely
    # different local shape that is CORRECT. If it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-short-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _short(
            "    result = []  # type: List[int]\n"
            "    k = 0\n"
            "    while k < len(name):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= k and k <= len(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(name).take(k))\n"
            "        Invariant(MustTerminate(len(name) - k))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(name).take(k + 1).drop(k) == PSeq(name[k]))\n"
            "        result = result + [name[k]]\n"
            "        k = k + 1\n"
            "    Assert(ToSeq(name).take(len(name)) == ToSeq(name))\n"
            "    return result\n"
        ),
        "rationale": "honest cheapest-impl positive control (the grounded-oracle class "
                     "has no wrong echo): the short identifier IS the name, so the "
                     "cheapest correct impl rebuilds ToSeq(name); a local index reshape "
                     "(i->k) that keeps every gold invariant/assert must verify. Else "
                     "SPEC-TOO-STRONG.",
    },

    # =========================================================== admissibility
    # A self-call caller, strictly inside qualified_reference's impl region (spec
    # untouched), builds a fresh F2P-shaped input (`Class` reached under module
    # `unknown` -> code points) and invokes subclass_short_name and
    # placeholder_display_name on it. The fresh lists are constructed via append
    # so the constructor establishes FULL permission; each callee Requires only a
    # half plus a termination obligation strictly below the caller's measure
    # (2 < 3), both of which are admissible from an ordinary caller. If the
    # precondition could not be established for a normal input, these call sites
    # would fail to verify => PRECOND-TOO-STRONG. (No same-measure self-call of
    # qualified_reference itself: the termination discipline correctly forbids
    # it.) The modeled body still returns the gold result.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _qref(
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    result = result + [46]\n"
            "    result = result + display\n"
            "    # Admissibility self-call: a fresh F2P-shaped input (attribute\n"
            "    # `Class` under module `unknown`). If the Requires of the helper\n"
            "    # functions could not be established for it, these call sites would\n"
            "    # fail => PRECOND-TOO-STRONG.\n"
            "    probe_name = [67, 108, 97, 115, 115]  # type: List[int]\n"
            "    probe_short = subclass_short_name(probe_name)\n"
            "    probe_display = placeholder_display_name(probe_short)\n"
            "    Assert(Acc(list_pred(probe_short)))\n"
            "    Assert(Acc(list_pred(probe_display)))\n"
            "    Assert(ToSeq(probe_short) == ToSeq(probe_name))\n"
            "    Assert(ToSeq(probe_display) == ToSeq(probe_name))\n"
            "    return result\n"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input: a literal "
                     "code-point identifier `Class` (the F2P `unknown.secret.Class` "
                     "leaf). The self-calls establish each helper's Requires (half of a "
                     "fresh full permission + a strictly smaller termination measure, "
                     "2 < 3) and the post facts (short==name; display==short) are "
                     "derivable; else PRECOND-TOO-STRONG.",
    },

    # ====================================================== uniqueness: FRAME-MUTATION
    # ATTACK 1 (FRAME-MUTATION on subclass_short_name's read-only `name` -- the #1
    # weakness class). The impl OVERWRITES `name` (clears it) before copying, so
    # an empty `name` would trivially satisfy any value claim derived from it. Only
    # Acc(list_pred(name), 1/2) is held, so a WRITE to name's contents requires full
    # permission and the verifier MUST reject this for INSUFFICIENT PERMISSION --
    # not for a value mismatch. The gold post/invariants are kept verbatim so the
    # rejection is attributable solely to the illegal write.
    {
        "id": "frame-mutate-short-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _short(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input's contents.\n"
            "    name.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(name):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(name).take(i))\n"
            "        Invariant(MustTerminate(len(name) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))\n"
            "        result = result + [name[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(name).take(len(name)) == ToSeq(name))\n"
            "    return result\n"
        ),
        "refinement": "in the real sphinx code `name` is the attribute name string the "
                      "placeholder is reached by (`_make_subclass(name, module)`); it is "
                      "read only to be stored as `__name__`/`__display_name__`. A patch "
                      "that mutates the incoming `name` would corrupt the attribute "
                      "string the caller (`__getattr__`) still holds and record an empty "
                      "`__name__`, reproducing the dangling-dot bug -- so restify would "
                      "yield `<module>.` and the F2P test_restify_mock would NOT pass. "
                      "The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(list_pred(name), 1/2); writing name's contents (name.clear()) "
                     "needs full permission. Insufficient permission, not a value "
                     "mismatch. Mandatory frame-mutation probe (read-only input).",
    },

    # ATTACK 2 (FRAME-MUTATION on qualified_reference's read-only `module`). Same
    # class, second read-only input: the impl clears `module` to force the leading
    # segment empty. Only Acc(list_pred(module), 1/2) is held => insufficient
    # permission to write its contents.
    {
        "id": "frame-mutate-qref-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _qref(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input's contents.\n"
            "    module.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n"
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    result = result + [46]\n"
            "    result = result + display\n"
            "    return result\n"
        ),
        "refinement": "`module` is the placeholder's owning module path "
                      "(`obj.__module__`), which the renderer reads but never writes. A "
                      "patch that clears it would render `.<name>` (no module prefix) "
                      "instead of `<module>.<name>` for EVERY mock cross-reference, so "
                      "test_restify_mock (expecting `unknown.secret.Class`) and the "
                      "restify/stringify P2P tests would diverge. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(list_pred(module), "
                     "1/2) is held; writing module's contents requires full permission. "
                     "Insufficient permission. Second mandatory frame-mutation probe.",
    },

    # ATTACK 3 (FRAME-MUTATION on qualified_reference's read-only `name`). Third
    # read-only input, the one that carries the discriminating short identifier:
    # clearing `name` would make `display == name == []` and collapse the trailing
    # component. Only Acc(list_pred(name), 1/2) is held => insufficient permission.
    {
        "id": "frame-mutate-qref-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _qref(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input's contents.\n"
            "    name.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n"
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    result = result + [46]\n"
            "    result = result + display\n"
            "    return result\n"
        ),
        "refinement": "`name` is the discriminating attribute name (`Class`) that the "
                      "fix propagates to `__qualname__`. A patch that clears it before "
                      "rendering produces a dangling `<module>.` -- exactly the bug the "
                      "F2P test_restify_mock detects (it expects `unknown.secret.Class`, "
                      "not `unknown.secret.`). The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(list_pred(name), 1/2) "
                     "is held; writing name's contents requires full permission. "
                     "Insufficient permission. Third mandatory frame-mutation probe "
                     "(qualified_reference's second read-only input).",
    },

    # ======================================== uniqueness: PARTIAL-DOMAIN / the bug
    # ATTACK 4 (THE F2P BUG: dangling dot). qualified_reference copies the module
    # and appends the dot, then RETURNS without appending `display`. This is the
    # exact pre-patch symptom: restify produces `<module>.` with the trailing
    # component dropped. Must reject: Q2 demands ToSeq(Result()) == module+dot()+name,
    # and Q3 demands len(Result()) > len(module)+1 for a non-empty name -- here
    # the result is module+dot() (length len(module)+1), so Q3 is violated.
    {
        "id": "weak-dangling-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _qref(
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    # BUG: the dot is appended but the display identifier is dropped,\n"
            "    # so the reference dangles as `<module>.` (the pre-patch symptom).\n"
            "    result = result + [46]\n"
            "    return result\n"
        ),
        "refinement": "this is the PRE-PATCH behaviour through the renderer: the "
                      "placeholder's `__qualname__` is empty, so restify joins "
                      "`<module>.` + '' = `unknown.secret.` -- the dangling dot the "
                      "issue reports (`Bases: torch.nn.` instead of `torch.nn.Module`). "
                      "The F2P test_restify_mock asserts the reference is "
                      "`unknown.secret.Class`; a dangling dot FAILS it. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "violates Q2 (ToSeq(Result()) == module+dot() != module+dot()+name "
                     "for a non-empty name) and Q3 (len(Result())==len(module)+1, not "
                     "> len(module)+1). The anti-dangling-dot clause Q3 is the explicit "
                     "guard against exactly this bug.",
    },

    # ATTACK 5 (PARTIAL-DOMAIN: empty display = model_prepatch.py). The display
    # site returns the empty list (modelling __qualname__ = ''), correct on no
    # non-empty short_name. Must reject: (D) ToSeq(Result()) == ToSeq(short_name)
    # fails whenever short_name is non-empty.
    {
        "id": "weak-display-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _display(
            "    # BUG (= model_prepatch.py): the display identifier is hard-set to\n"
            "    # the empty string, ignoring the short identifier entirely.\n"
            "    empty = []  # type: List[int]\n"
            "    return empty\n"
        ),
        "refinement": "this is model_prepatch.py: `self.__qualname__ = ''`. The "
                      "placeholder's display identifier is empty, so restify (which "
                      "reads __qualname__) renders the dangling `<module>.` and the F2P "
                      "test_restify_mock FAILS. The faithful real patch does NOT resolve "
                      "(G-DIFF: this prepatch FAILS the (D) postcondition).",
        "rationale": "violates (D) ToSeq(Result()) == ToSeq(short_name): returning the "
                     "empty list equals ToSeq(short_name) only when short_name is empty, "
                     "so it is rejected for any non-empty short identifier.",
    },

    # ATTACK 6 (PARTIAL-DOMAIN: short identifier not recorded = model_prepatch_2.py).
    # The short-name site returns the empty list (modelling attrs records no
    # '__name__': name). Must reject: (S) ToSeq(Result()) == ToSeq(name) fails for
    # any non-empty name.
    {
        "id": "weak-short-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _short(
            "    # BUG (= model_prepatch_2.py): the placeholder does not record the\n"
            "    # attribute name as its short identifier.\n"
            "    empty = []  # type: List[int]\n"
            "    return empty\n"
        ),
        "refinement": "this is model_prepatch_2.py: `_make_subclass` records no "
                      "`'__name__': name`, so `self.__name__` falls through "
                      "`__getattr__` to a fresh placeholder rather than the string "
                      "name; the propagated __qualname__ is then not the attribute name "
                      "and restify dangles. test_restify_mock FAILS. The faithful real "
                      "patch does NOT resolve (G-DIFF: this prepatch FAILS the (S) "
                      "postcondition).",
        "rationale": "violates (S) ToSeq(Result()) == ToSeq(name): the empty list "
                     "equals ToSeq(name) only when name is empty, so it is rejected for "
                     "any non-empty attribute name.",
    },

    # ATTACK 7 (PARTIAL-DOMAIN, off-by-one trailing component). qualified_reference
    # appends the dot and the display BUT drops the display's LAST code point
    # (loops the display copy to len(display)-1). Correct only when name is empty;
    # WRONG on every non-empty name (the trailing component is one code point
    # short). Targets Q2 specifically: the result tail would be display.take(len-1)
    # != name. Note: this rebuilds the trailing copy explicitly (no extra spec
    # helper) so it stays inside the impl region.
    {
        "id": "weak-truncated-display-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _qref(
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    result = result + [46]\n"
            "    # BUG: copy the display identifier but DROP its last code point.\n"
            "    j = 0\n"
            "    while j < len(display) - 1:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= j and j <= len(display))\n"
            "        Invariant(MustTerminate(len(display) - j))\n"
            "        # invariants-end\n"
            "        result = result + [display[j]]\n"
            "        j = j + 1\n"
            "    return result\n"
        ),
        "refinement": "this drops the final character of the attribute name from the "
                      "rendered reference (e.g. `Class` -> `Clas`), so restify yields "
                      "`unknown.secret.Clas` instead of `unknown.secret.Class`. The F2P "
                      "test_restify_mock asserts the exact `unknown.secret.Class`, so a "
                      "truncated trailing component FAILS it. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "violates Q2 ToSeq(Result()) == module+dot()+name: the trailing "
                     "component equals display.take(len(display)-1) != name on any "
                     "non-empty name. (Q3's len bound alone would not catch a 1-char "
                     "drop when len(name)>1; Q2's exact-concatenation clause does.)",
    },

    # ATTACK 8 (PARTIAL-DOMAIN / wrong separator: missing dot). qualified_reference
    # copies the module and appends the display but OMITS the dot separator -- the
    # reference is `<module><name>` (e.g. `unknownsecretClass`). Targets Q2: the
    # exact concatenation requires dot() between module and name. Correct on no
    # input (the dot is always required). Must reject.
    {
        "id": "weak-missing-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _qref(
            "    short = subclass_short_name(name)\n"
            "    display = placeholder_display_name(short)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(module):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(name), 1 / 2))\n"
            "        Invariant(Acc(list_pred(module), 1 / 2))\n"
            "        Invariant(Acc(list_pred(display)))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(module))\n"
            "        Invariant(ToSeq(display) == ToSeq(name))\n"
            "        Invariant(ToSeq(result) == ToSeq(module).take(i))\n"
            "        Invariant(MustTerminate(len(module) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))\n"
            "        result = result + [module[i]]\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(module).take(len(module)) == ToSeq(module))\n"
            "    # BUG: omit the '.' separator; the reference reads `<module><name>`.\n"
            "    result = result + display\n"
            "    return result\n"
        ),
        "refinement": "this composes `<module><name>` with no separator (e.g. "
                      "`unknownsecretClass`), but the renderer joins with '.' "
                      "(`'%s.%s' % (module, qualname)`). restify would no longer produce "
                      "a valid dotted cross-reference, so test_restify_mock (expecting "
                      "`unknown.secret.Class`) FAILS. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates Q2 ToSeq(Result()) == module + dot() + name: the result "
                     "is module + name (no dot), differing at index len(module) for any "
                     "module/name where the boundary code point != 46.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE.
#
# This bundle has NO @ContractOnly value-axiom (meta.axioms == []; the axioms
# region is the empty singleton). The ONLY callee-level obligation is the single
# A-reference deep model: the three modeled functions + the pure render_qualified
# must equal the REAL sphinx placeholder-build (_make_subclass / _MockObject.
# __init__) and renderer (restify / stringify) on every input the model reaches.
# render_qualified is itself a transparent @Pure concatenation inside the verified
# spec module -- there is no separate runtime callee whose Ensures could drift and
# no caller-reachable input outside an axiom domain (no axiom domain exists). The
# A-reference is validated on the HOST by axiom_check.py (G-AX): it BUILDS the real
# placeholder via sphinx.ext.autodoc.mock.mock([...]) + attribute access (the F2P
# input `unknown.secret.Class` + 200 randomized identifier chains), reads the real
# __module__/__qualname__, and runs the real restify/stringify, asserting the deep
# model matches AND the F2P discriminator (dangling `<module>.` at base_commit vs
# `<module>.<name>` at gold). We re-run that HOST-validated oracle IN-CONTAINER (on
# the gold testbed) as the single axiom-lane probe, so the A-reference is grounded
# in the REAL python callee chain (it CALLS the real callees; it does not regex
# inspect source for values -- it only inspects source to DECIDE which commit is
# installed). It reads no bundle files (sphinx is imported from the installed
# package), so there is no utf-8 codec or mount concern; the probe is the verbatim
# HOST axiom_check.py source embedded at manifest-load time.
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-placeholder-render",
        "axiom": "render_qualified + subclass_short_name + placeholder_display_name "
                 "(A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness/containment on the gold testbed: the deep "
                     "model (short==name, display==short, render=module+'.'+display) "
                     "must equal the REAL sphinx placeholder + restify/stringify on the "
                     "F2P input `unknown.secret.Class` and 200 randomized identifier "
                     "chains (all in the model's reachable domain: non-empty Unicode "
                     "identifiers). It also pins the F2P discriminator: on gold restify "
                     "ends in `.<name>` (never the dangling `.`), and stringify's "
                     "value == `<module>.<name>` (P2P). Any mismatch => the A-reference "
                     "is unsound. There is no @ContractOnly axiom, hence no axiom domain "
                     "and no caller-reachable input outside it.",
    },
]
