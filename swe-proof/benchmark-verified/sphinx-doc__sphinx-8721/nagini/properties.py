# properties.py — PBT falsification battery for sphinx-doc__sphinx-8721. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between
# `module_source_pages`'s `# impl-start` / `# impl-end` — which INCLUDES its nested
# invariants region — is edited; the spec view, both functions' signatures, the
# axioms/pure/pre-/post-condition regions, and the `begins_with` impl are never
# touched), checked by Nagini verify + markers.same_spec. Axiom cases probe the two
# A-reference deep models (`prefix_eq`, `suppressed`) against the REAL Python builtin
# `str.startswith` (see AXIOM_TESTS at the bottom).
#
# DEFENDED SURFACE (read from model.py / refinement.md / mapping.md / instance.json):
#   module_source_pages(name: List[int], enable_epub: bool, modules: List[int]) -> List[int]
#   Models the gold collect_pages electronic-book page-suppression gate
#   (sphinx/ext/viewcode.py). Output = the set of yielded per-module source pages
#   (one int carrier per page). The discriminator the F2P/P2P tests observe:
#     - an ELECTRONIC-BOOK target (name begins with "epub") with the preference OFF
#       (enable_epub False, the default) yields NO module pages;
#     - every other target yields exactly one page per recorded module entry, in order.
#
#   PRECONDITION (both inputs READ-ONLY at half permission):
#     (P1) Requires(Acc(list_pred(name),    1 / 2))   # output-target name, READ-ONLY
#     (P2) Requires(Acc(list_pred(modules), 1 / 2))   # recorded module entries, READ-ONLY
#   POSTCONDITION (two framing/permission + ONE full-perm result + two LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(name),    1 / 2))    # returns name's read permission
#     (Q2) Ensures(Acc(list_pred(modules), 1 / 2))    # returns modules' read permission
#     (Q3) Ensures(Acc(list_pred(Result())))          # full ownership of the produced set
#     (Q_EMPTY) Ensures(Implies(suppressed(ToSeq(name), enable_epub), len(Result()) == 0))
#            -- a SUPPRESSED target (epub-prefix AND preference off) yields the EMPTY set.
#     (Q_FULL)  Ensures(Implies(not suppressed(ToSeq(name), enable_epub),
#                               ToSeq(Result()) == ToSeq(modules)))
#            -- every OTHER target yields EXACTLY the module list, IN ORDER.
#   Q_EMPTY and Q_FULL together PIN the gate in BOTH regimes: no slack. A rival that
#   suppresses a non-suppressed target fails Q_FULL; a rival that emits pages for a
#   suppressed target fails Q_EMPTY. The decision predicate `suppressed` is GROUNDED
#   (a @Pure fold over the args, fully unfolded — see UNGROUNDED-ORACLE below).
#
# FRAME-MUTATION lane is MANDATORY: BOTH `name` and `modules` are read-only
#   (Acc(...,1/2)); the `begins_with` helper's `name`/`lit` are read-only too
#   (Acc(...,1/4)). A rival that WRITES `modules` (or `name`) must be REJECTED for
#   INSUFFICIENT PERMISSION. Byte-fuzzers never think to mutate the input; this is the
#   project's #1 weakness class. The real collect_pages only READS env._viewcode_modules
#   and app.builder.name (shared, process-global build state); any write would corrupt
#   the recorded module set / builder name for every subsequent build step.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q_EMPTY/Q_FULL are pinned to
#   `suppressed(ToSeq(name), enable_epub)` and `ToSeq(modules)` — GROUNDED entirely in
#   the arguments. `suppressed = prefix_eq(name, lit_epub()) and not enable_epub`, where
#   `prefix_eq` is a @Pure front-recursive fold FULLY UNFOLDED over the name sequence
#   (no @ContractOnly axiom, no opaque answer-key, no exact marker an impl could echo)
#   and `lit_epub()` is the fixed constant PSeq(101,112,117,98). The pure region COMPUTES
#   the gate decision from the input; it does not assert an answer. There is no value an
#   echo could carry that satisfies Q_EMPTY/Q_FULL yet is wrong — the unique satisfier
#   IS the grounded decision. So the honest control is the cheapest faithful impl that
#   computes that decision (the positive control + admissibility below), not a wrong
#   echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: the real change is a control-flow fork (early `return` —
#   yield-nothing — vs fall through to the page-emission loop). The value abstraction
#   captures it directly: "yield nothing" ↔ empty Result (Q_EMPTY) and "emit a page per
#   module" ↔ Result == modules (Q_FULL). The suppress-all and no-gate rivals ARE the
#   discriminators for this fork (no separate capability token needed — the page-set
#   carrier already distinguishes "emitted" from "not emitted").
#
# PARTIAL-DOMAIN lane: heavily exercised across BOTH the gate dimensions and the module
#   list:
#     - weak-no-gate    : drops the epub gate entirely (the literal pre-patch bug) —
#                         correct on every non-epub target but WRONG on epub-default.
#     - weak-wrong-pol  : suppresses when the preference is ON instead of OFF — inverts
#                         the config semantics.
#     - weak-ignore-pref: suppresses ALL epub targets regardless of the preference —
#                         correct on epub-default but WRONG on epub-enabled.
#     - weak-drop-last  : emits all but the LAST recorded module page — correct on the
#                         empty module list but WRONG on any non-empty one.
#
# AXIOM lane: meta.axioms == [] (no consumed @ContractOnly axiom) but
#   deep_model_references has TWO A-references: `prefix_eq` models the CPython builtin
#   `str.startswith` (single-prefix form), and `suppressed` is the composite gate
#   `name.startswith("epub") and not enable_epub`. Per PBT_PLAN §2.4 / §4a an
#   A-reference deep model is validated == the real callee on every caller-reachable
#   input. The real callee is a Python LANGUAGE/builtin operation (`str.startswith`),
#   available with NO repo import, so the probes run anywhere (Docker or host). The
#   probes mirror axiom_check.py / G-AX: axiom-soundness fuzzes prefix_eq/suppressed ==
#   the real builtin gate; axiom-containment confirms every callee-input the model
#   reaches (any builder name as a code-point list, against the fixed prefix "epub")
#   lies in str.startswith's domain.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8721"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `module_source_pages` impl region body, verbatim — everything strictly
# BETWEEN that function's `# impl-start` / `# impl-end` (INCLUDING its nested invariants
# region). It is unique in model.py (the `begins_with` impl region is a different
# block). Every spec variant _swap()s ONLY this block, so the edit never touches the
# spec (axioms/pure/pre-/post-conditions + both function signatures + the verified
# `begins_with` impl). same_spec is computed over the spec_view, which elides every
# impl region (and nested invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    if begins_with(name, ep) and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    # The guard did not fire: the target is not suppressed.
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    """

assert _BASE.count(_IMPL) == 1, "module_source_pages impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the module_source_pages impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-local-reshape: structurally DIFFERENT but behaviourally identical. The gate
# decision `begins_with(name, ep)` is hoisted into a local boolean `is_epub`, and the
# guard becomes `if is_epub and not enable_epub:`. This is the local-variable reshape
# the directive explicitly endorses (NOT a loop-direction flip / forward-append, which
# would need an f(a+b) lemma the verifier won't auto-discharge). It keeps EVERY gold
# proof obligation verbatim — `Assert(ToSeq(ep) == lit_epub())` still ties the local to
# `prefix_eq(ToSeq(name), lit_epub())` via begins_with's postcondition
# `is_epub == prefix_eq(ToSeq(name), ToSeq(ep))`, both branch asserts hold unchanged,
# and the page-emission loop with its four invariants + two per-step framing asserts +
# the trailing `take(n)==full` assert is byte-identical to gold. If it FAILS =>
# SPEC-TOO-STRONG (a faithful, structurally-different correct impl is rejected).
_POS_RESHAPE = """\
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    is_epub = begins_with(name, ep)
    if is_epub and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    # The guard did not fire: the target is not suppressed.
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    """
assert _POS_RESHAPE != _IMPL, "pos-local-reshape did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is the two
# half-permissions Acc(list_pred(name),1/2) and Acc(list_pred(modules),1/2). This
# control keeps the gold impl VERBATIM but FIRST asserts, under those half-permissions,
# that the reads a normal F2P/P2P-shaped input needs are admitted — both lengths are
# readable and (when non-empty, e.g. the F2P epub build with a recorded `spam.mod1`
# entry) the first elements are readable. No write, so no extra permission demand. If
# the precondition could not admit a legitimate (target-name, module-set) input, this
# would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) target name and module set are\n"
    "    # in-domain; the half-permissions admit reading the lengths and elements.\n"
    "    Assert(len(name) >= 0)\n"
    "    Assert(len(modules) >= 0)\n"
    "    if len(name) > 0:\n"
    "        Assert(name[0] == name[0])        # read admitted under Acc(name,1/2)\n"
    "    if len(modules) > 0:\n"
    "        Assert(modules[0] == modules[0])  # read admitted under Acc(modules,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — both inputs are Acc(...,1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only `modules` input: modules[0] = modules[0]. A no-op store, but a STORE — it
# demands FULL write permission on `modules`, which the caller granted only at 1/2. The
# verifier must reject for insufficient permission. The store is placed FIRST, guarded
# by len>0 so it is reachable on a normal recorded-module set. (A real collect_pages
# that mutated env._viewcode_modules would corrupt the shared, process-global recorded
# module set for every subsequent build step; the spec must forbid ANY write.)
_FRAME_MUT = (
    "    if len(modules) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        modules[0] = modules[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW RIVALS — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only the impl changes.
# Each emits its result via the SAME forward-append loop with the SAME four invariants
# and two per-step framing asserts (the gold proof), so a rejection is attributable to
# the POSTCONDITION (Q_EMPTY / Q_FULL), never to a dropped lemma / proof gap.
# ---------------------------------------------------------------------------

# A reusable, verifiable "emit one page per module" loop body (the gold page-emission
# loop, verbatim) that produces `result == modules`. Used by the rivals that need the
# full module list on a path the spec says must be empty.
_EMIT_FULL = """\
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    """

# weak-no-gate: the LITERAL pre-patch bug (model_prepatch.py). No epub gate at all — it
# emits one page per recorded module entry for EVERY target. For a suppressed
# (epub-prefix, preference-off) target it returns the full, non-empty module list, so
# Q_EMPTY (Implies(suppressed, len(Result())==0)) is violated whenever modules is
# non-empty. This is exactly the gate-less skeleton G-DIFF kills.
_WEAK_NO_GATE = _EMIT_FULL

# weak-wrong-pol: PARTIAL-DOMAIN on the config dimension — suppresses when the
# preference is ON instead of OFF (`begins_with(name, ep) and enable_epub`). For an
# epub target with the preference OFF (the F2P epub-default build) the guard does NOT
# fire, so it emits the full module list, violating Q_EMPTY. (Internal gold asserts
# that no longer hold are removed — the rejection is attributable to Q_EMPTY, not an
# impl-internal assert.)
_WEAK_WRONG_POL = (
    "    ep = [101, 112, 117, 98]  # type: List[int]\n"
    "    empty = []  # type: List[int]\n"
    "    if begins_with(name, ep) and enable_epub:\n"
    "        return empty\n"
    + _EMIT_FULL
)

# weak-ignore-pref: PARTIAL-DOMAIN on the config dimension (the dual) — suppresses ALL
# epub targets, ignoring the preference entirely (`if begins_with(name, ep): return
# empty`). For an epub target with the preference ON (the P2P epub-enabled build,
# test_viewcode_epub_enabled) `suppressed` is FALSE (enable_epub True), so Q_FULL
# (Implies(not suppressed, Result()==modules)) demands the full module list, but the
# rival returns empty => Q_FULL violated for non-empty modules.
_WEAK_IGNORE_PREF = (
    "    ep = [101, 112, 117, 98]  # type: List[int]\n"
    "    empty = []  # type: List[int]\n"
    "    if begins_with(name, ep):\n"
    "        return empty\n"
    + _EMIT_FULL
)

# weak-drop-last: PARTIAL-DOMAIN on the module list — keeps the gold epub gate, but in
# the non-suppressed branch emits all module pages EXCEPT THE LAST (`while i < n - 1`).
# Correct on the empty module set (loop never runs, result == modules == []) but WRONG
# on any non-empty one: result == modules.take(n-1) != modules, so Q_FULL
# (Implies(not suppressed, ToSeq(Result())==ToSeq(modules))) is violated for n>=1. The
# loop uses the SAME per-step framing asserts and the SAME invariant ToSeq(result) ==
# ToSeq(modules).take(i) (just a smaller bound), so it VERIFIES the loop — the rejection
# is purely Q_FULL, not a proof gap. (The trailing gold `take(n)==full` assert is
# dropped because this path never reaches take(n); dropping an assert can only make the
# proof WEAKER, never spuriously fail it.)
_WEAK_DROP_LAST = """\
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    if begins_with(name, ep) and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n - 1:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    return result
    """

# weak-suppress-all: CONTROL-FLOW — removes the page-emission path entirely; always
# returns the empty set (every target suppressed). For any non-suppressed target (a
# plain html build — P2P test_linkcode / test_local_source_files — or an epub build
# with the preference ON — P2P test_viewcode_epub_enabled) Q_FULL demands the full
# module list, but the rival returns empty => Q_FULL violated for non-empty modules.
_WEAK_SUPPRESS_ALL = """\
    empty = []  # type: List[int]
    return empty
    """


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: the gate decision "
            "begins_with(name, ep) is hoisted into a local boolean `is_epub` and the "
            "guard becomes `if is_epub and not enable_epub:` (the local-variable reshape "
            "the directive endorses; NOT a loop-flip / forward-append needing an "
            "f(a+b) lemma). EVERY gold proof obligation is kept verbatim — "
            "Assert(ToSeq(ep)==lit_epub()) still ties is_epub to "
            "prefix_eq(ToSeq(name),lit_epub()) via begins_with's postcondition, both "
            "branch asserts hold, and the page-emission loop (four invariants + two "
            "per-step framing asserts + trailing take(n)==full assert) is byte-identical "
            "to gold. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (Acc(list_pred(name),1/2) + Acc(list_pred(modules),1/2)) "
            "must admit a normal F2P/P2P-shaped input: both lengths are readable and, "
            "when non-empty (the F2P epub build with a recorded spam.mod1 module entry), "
            "the first elements are readable under the half-permissions. The gold impl "
            "is otherwise verbatim (only reads/asserts added inside the impl region, no "
            "write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold collect_pages only READS env._viewcode_modules (the recorded "
            "module set) and app.builder.name; it NEVER mutates them. A faithful real "
            "patch that wrote back into the recorded module set would corrupt that "
            "shared, process-global build state for every subsequent build step and "
            "diverge from the gold's read-only collection — it would not be the gold "
            "patch and would not faithfully resolve. The store here is a no-op only by "
            "coincidence; the point is the spec must forbid ANY write to the input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `modules` is granted at "
            "Acc(list_pred(modules),1/2) (P2); the store modules[0]=modules[0] demands "
            "FULL write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold gate/emission body is kept verbatim so "
            "the rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame is hollow (frame-mutation, the #1 weakness class; a "
            "byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-no-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_GATE),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): collect_pages with no "
            "epub gate, emitting one module page for EVERY target. Its faithful real "
            "patch is the UNCHANGED repo, which yields _modules/spam/mod1.xhtml even for "
            "an epub-default build — exactly the bug. It FAILS the F2P "
            "test_viewcode_epub_default (asserts that file does NOT exist). Does NOT "
            "resolve — the precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q_EMPTY (Implies(suppressed(ToSeq(name),enable_epub), "
            "len(Result())==0)): for a suppressed (epub-prefix, preference-off) target "
            "the rival returns the full, non-empty module list, so len(Result())>0 while "
            "suppressed holds => Q_EMPTY false. PARTIAL-DOMAIN / CONTROL-FLOW: the early "
            "yield-nothing return is removed; the value abstraction senses it via "
            "Q_EMPTY. If it VERIFIES => SPEC-TOO-WEAK (the suppression gate is unpinned)."
        ),
    },
    {
        "id": "weak-wrong-pol",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_POL),
        "refinement": (
            "inverting the preference test (`startswith('epub') and "
            "viewcode_enable_epub` instead of `and not viewcode_enable_epub`) is what a "
            "patch that flipped the config polarity would do. For the F2P epub-default "
            "build (preference OFF) the guard does not fire, so module pages ARE emitted "
            "— _modules/spam/mod1.xhtml exists. It FAILS the F2P "
            "test_viewcode_epub_default. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q_EMPTY: for an epub target with enable_epub False, "
            "suppressed(ToSeq(name),enable_epub) is True, but the rival's guard "
            "(`... and enable_epub`) is False, so it emits the full module list and "
            "len(Result())>0 for non-empty modules => Q_EMPTY false. PARTIAL-DOMAIN on "
            "the config dimension (correct only when the preference is ON). If it "
            "VERIFIES => SPEC-TOO-WEAK (the preference polarity is unpinned)."
        ),
    },
    {
        "id": "weak-ignore-pref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_PREF),
        "refinement": (
            "suppressing ALL epub targets regardless of viewcode_enable_epub (`if "
            "name.startswith('epub'): return`) is what a patch that dropped the `and not "
            "...enable_epub` conjunct would do. For the P2P epub-enabled build "
            "(viewcode_enable_epub=True) it suppresses pages that the test requires to "
            "exist. It FAILS the P2P test_viewcode_epub_enabled (asserts "
            "_modules/spam/mod1.xhtml EXISTS). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q_FULL (Implies(not suppressed(ToSeq(name),enable_epub), "
            "ToSeq(Result())==ToSeq(modules))): for an epub target with enable_epub True, "
            "suppressed is False, so Q_FULL demands Result()==modules, but the rival "
            "returns empty => for non-empty modules ToSeq(Result())!=ToSeq(modules). "
            "PARTIAL-DOMAIN on the config dimension (the dual; correct only when the "
            "preference is OFF). If it VERIFIES => SPEC-TOO-WEAK (the preference is "
            "unpinned in the other direction)."
        ),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_LAST),
        "refinement": (
            "emitting every module page except the LAST is what an off-by-one page loop "
            "(`for entry in modulenames[:-1]`) would do. The recorded set includes "
            "spam.mod1; dropping the last entry means _modules/spam/mod1.xhtml is NOT "
            "written when it is last. It FAILS the P2P test_viewcode_epub_enabled / "
            "test_linkcode / test_local_source_files (assert the module page EXISTS). "
            "Does NOT resolve. A genuine PARTIAL-DOMAIN break: correct on the empty "
            "module set, wrong on any non-empty one."
        ),
        "rationale": (
            "REJECTED by Q_FULL: in the non-suppressed branch the loop runs to n-1, so "
            "ToSeq(result)==ToSeq(modules).take(n-1), which differs from ToSeq(modules) "
            "for n>=1 — Q_FULL demands equality. The loop keeps the gold per-step "
            "framing asserts and the invariant ToSeq(result)==ToSeq(modules).take(i) "
            "(just a smaller bound), so it VERIFIES the loop and the rejection is purely "
            "Q_FULL (NOT a proof gap). PARTIAL-DOMAIN on the module list. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the per-module page count is unpinned)."
        ),
    },
    {
        "id": "weak-suppress-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SUPPRESS_ALL),
        "refinement": (
            "returning nothing for EVERY target is what a patch that put the early "
            "`return` before the gate (unconditionally) would do. It suppresses module "
            "pages for plain html builds (P2P test_linkcode / test_local_source_files) "
            "and for epub-enabled builds (P2P test_viewcode_epub_enabled), all of which "
            "assert the module page EXISTS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q_FULL (Implies(not suppressed(ToSeq(name),enable_epub), "
            "ToSeq(Result())==ToSeq(modules))): for any non-suppressed target (a plain "
            "html name, or an epub name with enable_epub True) suppressed is False, so "
            "Q_FULL demands Result()==modules, but the rival always returns empty => for "
            "non-empty modules the equality fails. CONTROL-FLOW: the page-emission path "
            "is removed entirely. If it VERIFIES => SPEC-TOO-WEAK (the spec would admit "
            "suppress-everything, which the companion clause exists precisely to block)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the two A-reference deep models vs the REAL Python builtin str.startswith.
# meta.axioms == [] (no consumed @ContractOnly axiom); deep_model_references has TWO
# A-references: prefix_eq models the single-prefix str.startswith, and suppressed is the
# composite gate `name.startswith("epub") and not enable_epub`. Per PBT_PLAN §2.4 / §4a
# an A-reference deep model is validated == the real callee on every caller-reachable
# input. The real callee is a Python BUILTIN/language operation (str.startswith), needing
# NO repo import, so the probes run anywhere (Docker or host). The probes embed a
# faithful transcription of model.py's front-recursive prefix_eq fold (over code-point
# lists) and the suppressed composite, and compare them against the LIVE builtin. This
# mirrors axiom_check.py / G-AX, re-run here as the persisted PBT axiom lane.
# ---------------------------------------------------------------------------

# model.py's @Pure front-recursive prefix_eq fold + the suppressed composite,
# transcribed as plain Python over code-point lists (drop(1) is the tail). Shared text.
_PREFIX_SRC = '''
LIT_EPUB = [101, 112, 117, 98]   # model.py lit_epub() == PSeq(101,112,117,98) == "epub"

def prefix_eq(s, lit):
    """Faithful transcription of model.py's @Pure front-recursive prefix_eq fold:
       len(lit)==0 -> True; len(s)==0 -> False; s[0]==lit[0] and recurse on tails."""
    s = list(s)
    lit = list(lit)
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s[1:], lit[1:])

def suppressed_model(name, enable_epub):
    """Reference of model.py's `suppressed` composite predicate over a str name."""
    cps = [ord(c) for c in name]
    return prefix_eq(cps, LIT_EPUB) and (not enable_epub)
'''

_AX_SOUND_PROBE = _PREFIX_SRC + '''
import random
import sys

def suppressed_real(name, enable_epub):
    """The electronic-book gate the gold patch installs in collect_pages."""
    if name.startswith("epub") and not enable_epub:
        return True
    return False

# builder names exercised by the SWE-bench tests + neighbours that pin the exact gate
# boundary (the prefix test must accept epub3 but reject near mistakes such as 'ep' /
# 'Epub' / 'pub'). Mirrors axiom_check.py's boundary set.
boundary = [
    "", "html", "singlehtml", "singlehtm", "singlehtmlx", "ssinglehtml",
    "epub", "epub2", "epub3", "epubfoo", "ep", "e", "Epub", "EPUB",
    "epu", "pub", "dirhtml", "json", "latex", "text", "man", "texinfo",
    "applehelp", "qthelp", "devhelp", "htmlhelp", "linkcheck", "xml",
    "pseudoxml", "gettext", "changes", "singlehtmlepub", "epubsinglehtml",
]

fails = 0
# (axiom-soundness) the deep model prefix_eq == the REAL str.startswith, and the
# composite suppressed == the real electronic-book gate, on every boundary name x both
# preference values.
for name in boundary:
    real_prefix = name.startswith("epub")
    model_prefix = prefix_eq([ord(c) for c in name], LIT_EPUB)
    if real_prefix != model_prefix:
        fails += 1
        print("UNSOUND prefix_eq on %r: real startswith=%r model=%r"
              % (name, real_prefix, model_prefix))
    for enable in (True, False):
        if suppressed_real(name, enable) != suppressed_model(name, enable):
            fails += 1
            print("UNSOUND suppressed on name=%r enable=%r: real=%r model=%r"
                  % (name, enable, suppressed_real(name, enable),
                     suppressed_model(name, enable)))

# randomized fuzz over an alphabet that keeps the boundary near 'epub' interesting.
rng = random.Random(8721)
alphabet = list("epubsinglhtmxz123 ")
for _ in range(50000):
    nlen = rng.randint(0, 14)
    name = "".join(rng.choice(alphabet) for _ in range(nlen))
    enable = rng.choice((True, False))
    if name.startswith("epub") != prefix_eq([ord(c) for c in name], LIT_EPUB):
        fails += 1
        print("UNSOUND fuzz prefix_eq on %r" % name)
    if suppressed_real(name, enable) != suppressed_model(name, enable):
        fails += 1
        print("UNSOUND fuzz suppressed on name=%r enable=%r" % (name, enable))

# the discriminating F2P/P2P facts, explicitly.
checks = [
    (suppressed_model("epub", False) is True, "epub-default target IS suppressed (F2P)"),
    (suppressed_model("epub", True) is False, "epub-enabled target is NOT suppressed (P2P)"),
    (suppressed_model("epub3", False) is True, "epub3-default target IS suppressed"),
    (suppressed_model("html", False) is False, "html target is NOT suppressed (P2P)"),
    (suppressed_model("singlehtml", False) is False,
     "singlehtml is NOT epub-suppressed (its own guard is out of scope)"),
    (suppressed_model("ep", False) is False, "near-prefix 'ep' is NOT suppressed"),
    ("epub".startswith("epub"), "real: 'epub'.startswith('epub')"),
    (not "ep".startswith("epub"), "real: not 'ep'.startswith('epub')"),
]
for ok, desc in checks:
    if not ok:
        fails += 1
        print("FACT FAIL:", desc)

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between deep prefix_eq/suppressed "
          "and real str.startswith gate" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: deep prefix_eq == real str.startswith and the suppression "
      "composite == the real electronic-book gate on %d boundary + 50000 fuzz builder "
      "names; epub-default suppressed, epub-enabled / html / near-prefix not." % len(boundary))
sys.exit(0)
'''

_AX_COVER_PROBE = _PREFIX_SRC + '''
import random
import sys

# (axiom-containment) Which callee-inputs can the MODEL actually reach? The deep model
# prefix_eq / the suppressed composite are applied by module_source_pages (and the
# verified begins_with helper) to exactly:
#   * s   = ToSeq(name), where `name: List[int]` is any FINITE list of Unicode
#           code points (Requires only Acc(list_pred(name),1/2) — no length or value
#           bound; the carrier guarantees each element is a valid code point, mapping.md
#           name[k]==ord(builder_name[k]));
#   * lit = lit_epub() == PSeq(101,112,117,98), the FIXED prefix "epub".
# The real callee is `str.startswith(prefix)` (single-argument form: no start/end at the
# call site, refinement.md §B). Its domain is "self is a str, prefix is a str (or tuple
# of str)". Every reachable operand is a finite sequence of valid Unicode code points,
# which round-trips to a Python str via ''.join(chr(c)), and the prefix is always the
# str "epub" — so every caller-reachable callee-input lies INSIDE str.startswith's
# domain (no start/end args, no TypeError). Covering MORE (e.g. tuple-of-prefixes,
# start/end args) than the caller reaches would be sound, not a defect — we only need
# containment. We CONFIRM it by mapping a heavy sample of the reachable name space back
# to str and asserting str.startswith("epub") raises nothing and the model agrees.
fails = 0
rng = random.Random(2024)

def reachable_names():
    # representative reachable `name` code-point lists: empty, the real builder names,
    # near-prefixes, and random finite code-point lists incl. non-ASCII (a builder name
    # is an arbitrary str; the carrier admits any code point).
    yield []
    for t in ["", "epub", "epub3", "ep", "html", "singlehtml", "EPUB", "epubfoo"]:
        yield [ord(c) for c in t]
    alphabet = "epubsinglhtmxz123 \\u00e9\\u4e2d"   # incl. non-ASCII code points
    for L in range(0, 12):
        for _ in range(3000):
            yield [ord(rng.choice(alphabet)) for _ in range(L)]

for name_cps in reachable_names():
    # ToSeq(name) operand mapped back to the real str the gate would see.
    try:
        name_str = "".join(chr(c) for c in name_cps)
    except (ValueError, OverflowError) as e:
        fails += 1
        print("CONTAINMENT FAIL: code-point list %r not a valid str: %s" % (name_cps, e))
        continue
    try:
        real = name_str.startswith("epub")   # the real callee on a reachable input
    except Exception as e:                    # noqa: BLE001 — any raise is a domain miss
        fails += 1
        print("CONTAINMENT FAIL: str.startswith raised on reachable name %r: %s"
              % (name_str, e))
        continue
    # the deep model must agree on every reachable input (containment + soundness on the
    # reachable slice).
    if prefix_eq(name_cps, LIT_EPUB) != real:
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL on reachable %r: model=%r real=%r"
              % (name_str, prefix_eq(name_cps, LIT_EPUB), real))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside str.startswith "
          "domain or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input the model can reach (ToSeq(name) for a "
      "finite Unicode code-point list `name`, against the fixed prefix \\"epub\\") maps to "
      "a valid str and lies in str.startswith's single-prefix domain (no start/end, no "
      "raise) and the deep model agrees.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-prefix_eq",
        "axiom": "prefix_eq",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "prefix_eq is an A-reference deep model of the CPython builtin "
            "str.startswith (single-prefix form), and suppressed is the composite gate "
            "`name.startswith('epub') and not enable_epub` (no consumed @ContractOnly "
            "axiom in this bundle). AXIOM-SOUNDNESS: the deep fold must equal the REAL "
            "builtin on every input. The probe runs the live str.startswith on 33 "
            "boundary names (incl. epub / epub3 / ep / Epub / singlehtml) x both "
            "preference values + 50000 fuzz names and asserts agreement of both "
            "prefix_eq and the suppressed composite; mirrors axiom_check.py / G-AX. If "
            "the real callee disagrees anywhere => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-prefix_eq",
        "axiom": "prefix_eq",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: module_source_pages / begins_with apply prefix_eq to "
            "exactly (ToSeq(name), lit_epub()==PSeq(101,112,117,98)). `name` is any "
            "finite list of Unicode code points (Requires grants only Acc(...,1/2); no "
            "length or value bound), so every reachable callee operand maps back to a "
            "valid Python str via ''.join(chr(c)), and the prefix is always the str "
            "'epub' — INSIDE str.startswith's single-prefix domain (no start/end args, "
            "refinement.md §B; no TypeError). The probe samples the reachable name space "
            "heavily (empty + real builder names + near-prefixes + random code-point "
            "lists incl. non-ASCII) and asserts str.startswith raises nothing and the "
            "model agrees. A reachable input outside the domain => "
            "AXIOM-TOO-WEAK-FOR-CALLER (none expected: covering more than the caller "
            "reaches is sound, not a defect)."
        ),
    },
]
