# properties.py — PBT manifest for pytest-dev__pytest-8399. NOT a Nagini module;
# a record of adversarial spec-falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT. Spec cases are full model.py variants that share
# the frozen spec (markers.same_spec) and differ ONLY inside the # impl-start/#
# impl-end region (region-surgery GUARANTEES same_spec); each is checked by Nagini
# verify. There are no axioms in this bundle (the only repo logic referenced is the
# unchanged, deeply-modeled listing rule `listed`, an A-reference — no @ContractOnly
# the proof consumes), so AXIOM_TESTS = [].
#
# Defended surface (from model.py):
#   generated_fixture_name(label: List[int]) -> List[int]
#   Requires: Acc(list_pred(label), 1/2)          <- READ-ONLY input (frame probe!)
#             len(label) > 0
#             label[0] != PRIVACY_MARKER (95 == '_')
#             MustTerminate(len(label) + 2)        <- TOTAL correctness (no diverge)
#   Ensures:  Acc(list_pred(label), 1/2)           (returns the borrow)
#             Acc(list_pred(Result()))
#             len(Result()) == len(label) + 1                      [LEN]
#             ToSeq(Result())[0] == PRIVACY_MARKER                 [MARKER]
#             ToSeq(Result()).drop(1) == ToSeq(label)              [CARRY]
#             begins_private(ToSeq(Result()))                      [PRIV]
#             not listed(ToSeq(Result()), 0)                       [OMIT@default]
#             listed(ToSeq(Result()), 1)                           [SHOW@verbose]
# The output is pinned STRUCTURALLY (LEN + CARRY + MARKER), then those pins are
# tied to the observable listing consequence via the *grounded* predicate `listed`
# (which reads name[0]==95, not an opaque oracle). The cheapest wrong impl cannot
# echo a free answer key; it must actually produce "[95] ++ label".
from pathlib import Path

INSTANCE = "pytest-dev__pytest-8399"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats in this bundle)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} occurs {src.count(old)} times")
    return src.replace(old, new, 1)


# The exact gold impl region (between # impl-start and # impl-end). Every variant
# is produced by _swap-ing a sub-string of THIS block, so the edit is provably
# confined to the impl region and the frozen spec is never touched.
_GOLD_IMPL = """    result = [PRIVACY_MARKER]  # type: List[int]
    i = 0
    while i < len(label):
        # invariants-start
        Invariant(Acc(list_pred(label), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(label))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(result)[0] == PRIVACY_MARKER)
        Invariant(ToSeq(result).drop(1) == ToSeq(label).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(label) - i,
        # discharging MustTerminate(len(label) + 2) from the precondition.
        Invariant(MustTerminate(len(label) - i + 1))
        # invariants-end
        result = result + [label[i]]
        i = i + 1
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
#     must verify; else SPEC-TOO-STRONG. We do a local-variable reshape of the
#     append step (compute the element into a temp, build a one-element tail,
#     concatenate) and KEEP every gold invariant verbatim — so the gold proof
#     obligations (prefix-preservation + the [0]==95 / len pins) still discharge.
#     This is the safe positive control per the doctrine: NOT a loop-direction
#     flip (which would need an f(a+b)==f(a)+f(b) lemma against a front-recursive
#     fold), just a reshape of the executable statements around the same append.
# ---------------------------------------------------------------------------
_POS = _swap(
    _BASE,
    "        result = result + [label[i]]\n        i = i + 1",
    "        c = label[i]\n        tail = [c]  # type: List[int]\n"
    "        result = result + tail\n        i = i + 1",
)

# ---------------------------------------------------------------------------
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input;
#     else PRECOND-TOO-STRONG. The descriptive labels at every gold site begin
#     with an ordinary letter ('u'/'x') and are non-empty, exactly the Requires.
#     We add two Asserts at the top of the impl that re-state the in-domain facts
#     (len>0, first code point != 95); they are discharged from Requires and so
#     confirm the precondition is consistent (not vacuously False) and accepts a
#     genuine label. (If Requires were contradictory the whole spec would be
#     vacuous; if it were unsatisfiable for a real label this would fail.) Gold
#     construction is otherwise unchanged, so the postcondition is also met.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE,
    "    result = [PRIVACY_MARKER]  # type: List[int]\n    i = 0",
    "    Assert(len(label) > 0)\n    Assert(label[0] != PRIVACY_MARKER)\n"
    "    result = [PRIVACY_MARKER]  # type: List[int]\n    i = 0",
)

# ---------------------------------------------------------------------------
# (FRAME-MUTATION) — MANDATORY: `label` is Acc(list_pred(label), 1/2), a
#     read-only borrow. A rival that WRITES to `label` to do its work must be
#     rejected for INSUFFICIENT PERMISSION (a half-permission borrow cannot be
#     mutated). We keep the entire gold construction and rejection-attributing
#     invariants verbatim and add a single self-assignment write to label[0] at
#     the top of the impl. It must fail with a permission error.
#     Refinement: a faithful real patch that mutated the descriptive name string
#     in place is impossible/incorrect (Python strs are immutable; the framework
#     builds the f-string fresh) — and if it somehow aliased and mutated a shared
#     object it would corrupt the caller's name, not produce the gold fixture
#     name, so it would NOT resolve the F2P (--fixtures listing). A verifying
#     mutation here would mean the spec lets an impl satisfy the postcondition
#     by clobbering its read-only input => SPEC-TOO-WEAK (frame defect).
# ---------------------------------------------------------------------------
_FRAME = _swap(
    _BASE,
    "    result = [PRIVACY_MARKER]  # type: List[int]\n    i = 0",
    "    label[0] = label[0]  # illegal write to a read-only (1/2) borrow\n"
    "    result = [PRIVACY_MARKER]  # type: List[int]\n    i = 0",
)

# ---------------------------------------------------------------------------
# (WRONG-MARKER) — uniqueness / the load-bearing MARKER clause. Prepend a
#     DIFFERENT separator code point 46 ('.') instead of 95 ('_'). LEN and CARRY
#     still hold, but ToSeq(Result())[0]==95 (MARKER), begins_private (PRIV) and
#     not listed(.,0) (OMIT) must all FAIL — the verifier must reject.
#     Refinement: a real patch that prefixed the fixture name with '.' instead of
#     '_' would NOT be omitted by the listing rule (it omits only names whose
#     first char is '_': `if verbose<=0 and argname[0]=="_": continue`), so the
#     generated fixture would still print its "no docstring available" line at
#     default verbosity — the F2P test (no_fnmatch_line under --fixtures) would
#     FAIL. A verifying '.'-prefix => SPEC-TOO-WEAK (marker not pinned to '_').
# ---------------------------------------------------------------------------
_WRONG_MARKER = _swap(
    _BASE,
    "    result = [PRIVACY_MARKER]  # type: List[int]",
    "    result = [46]  # type: List[int]  # prepend '.' (46), not '_' (95)",
)

# ---------------------------------------------------------------------------
# (PARTIAL-DOMAIN) — correct on most of the domain but corrupts ONE interior
#     element of the carried label. Prepend '_' correctly and copy every label
#     code point EXCEPT the last, which is overwritten with a constant (90 ='Z').
#     MARKER/PRIV/OMIT and even LEN still hold, but CARRY
#     (ToSeq(Result()).drop(1) == ToSeq(label)) fails on the last index whenever
#     label[-1] != 90 (true for every gold label, which end in a qualname char) =>
#     the verifier must reject.
#     Refinement: a real patch that prepended '_' but mangled the final char of
#     the descriptive name (e.g. produced "_xunit_setup_class_fixture_TesZ"
#     from "...Test") would change the fixture's identity/uniqueness; it is NOT
#     the gold edit (which carries the label through verbatim) and would not
#     match the framework's name= for the injected fixture. A verifying corruption
#     => SPEC-TOO-WEAK (label not carried verbatim).
# ---------------------------------------------------------------------------
_PARTIAL = _swap(
    _BASE,
    "        result = result + [label[i]]\n        i = i + 1",
    "        if i + 1 == len(label):\n"
    "            result = result + [90]  # corrupt the LAST label code point\n"
    "        else:\n"
    "            result = result + [label[i]]\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# (DIVERGE) — uniqueness / the termination obligation. Build the correct
#     '_'-prefixed name, then loop forever BEFORE returning it. Under partial
#     correctness every Ensures holds vacuously (the return is unreachable), so
#     without a termination obligation this rival VERIFIES — that is exactly
#     the P1 attack the audit constructed (compute the right name, `while True:
#     pass`, never register the fixture). With Requires(MustTerminate(...)) in
#     the frozen spec the inserted loop carries no MustTerminate invariant, so
#     the obligation leaks and the verifier must REJECT.
#     Refinement: a real patch that computed the '_'-prefixed name and then
#     diverged before passing it to @pytest.fixture(name=...) would hang the
#     collection phase; the fixture is never registered and the --fixtures F2P
#     never passes. A verifying divergence => SPEC-TOO-WEAK (partiality hole).
# ---------------------------------------------------------------------------
_DIVERGE = _swap(
    _BASE,
    "    return result\n    # impl-end",
    "    spin = 0\n"
    "    while spin >= 0:\n"
    "        spin = spin + 1  # never exits; no MustTerminate invariant\n"
    "    return result\n    # impl-end",
)

# ---------------------------------------------------------------------------
# (NO-PREPEND) — cheap SUPPORTING case = the pre-patch behaviour itself: return
#     the label unchanged (no marker prepended). LEN (len==len(label)+1) and
#     MARKER fail immediately => reject. This is exactly model_prepatch.py's
#     reverted behaviour (the base_commit f-strings without the leading '_').
#     Refinement: this IS the unfixed code — the generated fixture name keeps its
#     ordinary-letter prefix, so the listing rule SHOWS it at default verbosity
#     ("no docstring available" line present) and the F2P test fails. By
#     construction it does not resolve (it is the bug). A verifying no-op would
#     be the most basic SPEC-TOO-WEAK.
# ---------------------------------------------------------------------------
_NOPREPEND = _swap(
    _BASE,
    _GOLD_IMPL,
    "    return label",
)


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "structurally-different but correct impl (append step reshaped "
                     "into temp element + one-element tail; gold invariants kept "
                     "verbatim so prefix-preservation still discharges). Must verify; "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-fstring-label",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the precondition (len>0, label[0]!=95) admits a normal F2P-shaped "
                     "descriptive label (every gold f-string begins with 'u'/'x', "
                     "non-empty). Asserts re-state the in-domain facts (discharged from "
                     "Requires) + the gold construction completes. Must verify; else "
                     "PRECOND-TOO-STRONG / vacuous precondition.",
    },
    {
        "id": "frame-mutate-readonly-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME,
        "refinement": "Python str is immutable and the framework builds each name "
                      "f-string fresh, so no faithful real patch mutates the descriptive "
                      "label in place; any aliasing mutation would corrupt the caller's "
                      "name rather than produce the gold '_'-prefixed fixture name, so it "
                      "would NOT resolve the --fixtures F2P. A verify here = the spec lets "
                      "an impl satisfy the postcondition by clobbering its read-only input.",
        "rationale": "REJECT from the permission system: label is Acc(list_pred(label), "
                     "1/2); a write to label[0] needs full permission => 'insufficient "
                     "permission to access label'. This is the #1 frame-mutation probe.",
    },
    {
        "id": "wrong-marker-dot-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_MARKER,
        "refinement": "a real patch prefixing the fixture name with '.' (or any char != "
                      "'_') is NOT omitted by the listing rule (`if verbose<=0 and "
                      "argname[0]==\"_\": continue` fires only for '_'), so the generated "
                      "fixture still prints 'no docstring available' at default verbosity "
                      "and the F2P `no_fnmatch_line('*no docstring available*')` FAILS.",
        "rationale": "REJECT from MARKER clause ToSeq(Result())[0]==95 (also PRIV "
                     "begins_private and OMIT not listed(.,0)); code point 46 != 95.",
    },
    {
        "id": "partial-domain-corrupt-last-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL,
        "refinement": "a real patch that prepended '_' but replaced the last char of the "
                      "descriptive name would produce a fixture name that is NOT the gold "
                      "'_' + descriptive-label string; the framework's injected fixture "
                      "name= would differ from the intended one, breaking the modeled edit. "
                      "It carries the marker but mangles the carried label, so it is not "
                      "the gold behaviour and would not faithfully resolve.",
        "rationale": "REJECT from CARRY clause ToSeq(Result()).drop(1)==ToSeq(label): the "
                     "last code point becomes 90 ('Z') instead of label[-1], which differs "
                     "for every real label (qualname tail char).",
    },
    {
        "id": "diverge-before-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DIVERGE,
        "refinement": "the audited P1 attack: compute the correct '_'-prefixed name, "
                      "then `while True: pass` before it reaches @pytest.fixture(name=...). "
                      "The fixture is never registered, collection hangs, and the "
                      "--fixtures F2P never passes; under partial correctness the spec "
                      "admitted it. Requires(MustTerminate(len(label)+2)) closes the hole.",
        "rationale": "REJECT from the termination obligation: the inserted infinite loop "
                     "has no MustTerminate invariant, so the caller's obligation leaks "
                     "(Nagini reports the loop might not terminate / obligation not met).",
    },
    {
        "id": "no-prepend-prepatch-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NOPREPEND,
        "refinement": "this IS the pre-patch behaviour (base_commit f-strings with no "
                      "leading '_'); it is the reported bug. The generated fixture keeps "
                      "its ordinary-letter prefix, so the listing rule shows it at default "
                      "verbosity and the F2P fails by construction. Verbatim model_prepatch.",
        "rationale": "REJECT from LEN clause len(Result())==len(label)+1 (also MARKER): "
                     "returning label unchanged has no extra leading code point.",
    },
]

# No @ContractOnly axioms and no consumed callee in this bundle. `listed` is an
# A-reference deep model of the framework's UNCHANGED listing rule, validated
# equal to the real rule by axiom_check.py (G-AX); it is grounded (reads
# name[0]==95 structurally), not an opaque oracle, so there is no wrong echo to
# build. The axiom lane is therefore vacuous here.
AXIOM_TESTS = []
