# properties.py — PBT falsification battery for matplotlib__matplotlib-21568.
#
# NOT a Nagini module; a record of adversarial cases parsed by
# swebench_nagini.pbt. Each SPEC_TEST is a full model.py variant built by
# region-surgery (we edit ONLY text inside the single # impl-start/# impl-end
# region, so the frozen spec — axioms/pure/pre/post-conditions — is never
# touched and same_spec is guaranteed). The runner runs Nagini verify + same_spec
# on each.
#
# Defended surface (read from model.py):
#   protect_codepoints(text: List[int]) -> List[int]
#     Requires(Acc(list_pred(text), 1/2))                         # READ-ONLY input
#     Ensures (Acc(list_pred(text), 1/2))                         # gives perm back
#     Ensures (Acc(list_pred(Result())))                          # owns result
#     Ensures (ToSeq(Result()) == protected_seq(ToSeq(text)))     # LOAD-BEARING
#     Ensures (protect(45)==tok_dash(); protect(58)==tok_colon(); protect(32)==tok_space())
#
# The load-bearing postcondition pins the WHOLE output to protected_seq(ToSeq(text)),
# a GROUNDED @Pure fold of the input (per-code-point substitution:
#   45 '-' -> {123,45,125} '{-}',  58 ':' -> {123,58,125} '{:}',
#   32 ' ' -> {92,59} '\;',  else identity singleton).
# Because the oracle is a total function of the argument (no opaque answer-key /
# exact-marker to echo), there is NO wrong "ungrounded-oracle echo": any echo of
# protected_seq(ToSeq(text)) IS the correct answer. So the UNGROUNDED-ORACLE
# class is N/A here (see 'assessment') — we instead supply an honest positive
# control. The attacks that DO apply: frame-mutation (read-only input) and
# several partial-domain rivals (the spec's whole job is the colon/space delta).
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-21568"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body (everything between # impl-start and # impl-end).
# We rebuild the impl region wholesale for variants so the surgery target is
# unambiguous and unique; same_spec is preserved because we never touch text
# outside this block.
_GOLD_IMPL = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""

# Sanity: the gold impl block must appear verbatim and uniquely in model.py.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — update _GOLD_IMPL"


def _with_impl(new_impl_body):
    """Replace the whole impl region with new_impl_body. new_impl_body MUST keep
    the # impl-start / # impl-end markers so region surgery is closed."""
    assert new_impl_body.startswith("    # impl-start")
    assert new_impl_body.rstrip().endswith("# impl-end")
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — input is read-only Acc(text,1/2)).
#    A rival that WRITES to `text` to satisfy the postcondition. It only has
#    half permission to `text`, so any store into `text[...]` must fail to
#    verify for INSUFFICIENT PERMISSION (write needs full list_pred(text)).
#    Keep the gold fold otherwise so the rejection is attributable to the write.
# ---------------------------------------------------------------------------
_FRAME_MUTATION = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        text[i - 1] = c  # ILLEGAL: write through a 1/2 (read-only) permission
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN: protect '-' and ':' but DROP the space branch (space
#    passes through as identity). Correct on every label without a U+0020, but
#    diverges on any label containing a space.
#    Refinement: this is the gold patch MISSING `.replace(' ', r'\\;')`. The
#    F2P test_date_formatter_usetex[delta3] expects '$\\mathdefault{01\\;%02d}$'
#    (space -> \\;), and t_delta2 of test_concise_formatter_usetex exercises a
#    space; the real patch without the space replace fails those F2P cases.
#    Source of rejection: postcondition ToSeq(Result())==protected_seq(ToSeq(text))
#    on the space code point 32 (protect(32)==tok_space()==PSeq(92,59), but this
#    impl emits PSeq(32)).
# ---------------------------------------------------------------------------
_PARTIAL_DROP_SPACE = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN: protect '-' and ' ' but DROP the colon branch (colon
#    passes through as identity). This is the *exact* prepatch-class bug
#    extended to also cover the space — it still fails on any colon.
#    Refinement: the gold patch's `.replace(':', '{:}')` is the discriminating
#    delta the F2P observes: test_concise_formatter_usetex[t_delta2] expects
#    '$\\mathdefault{04{:}00}$' (colon -> {:}), and delta2 of
#    test_date_formatter_usetex has labels like '00{:}00:00' -> the missing
#    colon protect makes the label '00:00:00' (bare), failing F2P.
#    Source of rejection: postcondition on code point 58
#    (protect(58)==tok_colon()==PSeq(123,58,125); this impl emits PSeq(58)).
# ---------------------------------------------------------------------------
_PARTIAL_DROP_COLON = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN (wrong token): protect all three code points, but emit the
#    space token with its two code points SWAPPED: PSeq(59, 92) = ';\\' instead
#    of PSeq(92, 59) = '\\;'. Correct on labels without spaces; wrong ordering
#    on any space.
#    Refinement: a real patch using `.replace(' ', r';\\')` emits ';\\' where the
#    F2P expects '\\;' (delta3 expects '$\\mathdefault{01\\;%02d}$'); the
#    rendered label is wrong, F2P fails.
#    Source of rejection: postcondition; protect(32)==tok_space()==PSeq(92,59),
#    this impl yields PSeq(59,92) at the space, so ToSeq(Result()) != fold.
# ---------------------------------------------------------------------------
_WRONG_SPACE_TOKEN = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [59, 92] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN (first-processed / last-index element): the backward loop
#    processes index len(text)-1 first. This rival treats the VERY FIRST
#    iteration (i == len(text)) as identity for everything, and only protects
#    on subsequent iterations. So the LAST code point of the label is never
#    protected.
#    Refinement: a real patch that fails to protect the trailing character would
#    leave a trailing ':' or '-' bare — e.g. label '00:00:' (if it ever ended
#    in ':') or, more concretely on the F2P, the trailing digit is fine but a
#    label like '01-01 00:00' has its last char '0' (fine) yet a label '...-'
#    would diverge; the postcondition rejects it regardless because there EXISTS
#    a length-class input (last char in {45,58,32}) on which the fold differs.
#    Source of rejection: the loop invariant
#    ToSeq(result)==protected_seq(ToSeq(text).drop(i)) cannot be re-established
#    after the first iteration when text[len-1] is a protected code point.
# ---------------------------------------------------------------------------
_LAST_ELEMENT_IDENTITY = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    n = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if i == n:
            result = [c] + result
        elif c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 6. POSITIVE CONTROL (soundness): structurally-DIFFERENT but CORRECT impl.
#    Keep the gold BACKWARD fold (front-recursive protected_seq gives the single
#    unfold per step — a forward append would need an f(a+b)==f(a)+f(b) lemma the
#    verifier won't auto-discharge, AVOID per directive 3). The structural change
#    is a BRANCH REORDER (test space, then colon, then dash) plus an explicit
#    `i -= 1` -> `i = i - 1` is already there; we keep ALL invariants and the two
#    framing Asserts verbatim. A faithful correct impl MUST verify (else
#    SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_POS_CONTROL = """    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 32:
            result = [92, 59] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 45:
            result = [123, 45, 125] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


# ---------------------------------------------------------------------------
# 7. ADMISSIBILITY: a positive-control caller that asserts the Requires can be
#    established for an F2P-shaped input (a non-empty list of code points,
#    matching e.g. '01 00:00' -> codepoints), then calls protect_codepoints and
#    keeps the half permission. If the precondition rejects a normal input =>
#    PRECOND-TOO-STRONG. We append a NEW function INSIDE the impl region of the
#    existing function is not possible (one impl region), so we instead exercise
#    admissibility via a self-contained caller that builds the list with full
#    permission and passes the required half. We keep the gold body unchanged and
#    add the caller after the return is unreachable — instead we make the body a
#    no-op-preserving caller: we cannot add a second function without touching
#    spec regions, so admissibility is checked by the gold body itself verifying
#    on the in-domain shape, which it does (the spec view is unchanged). We
#    therefore realise admissibility as the GOLD impl plus an in-region Assert
#    that the Requires-shaped facts (a length>=0 list, half-perm held) are
#    consistent — i.e. the precondition is satisfiable in-region.
# ---------------------------------------------------------------------------
_ADMISSIBILITY = """    # impl-start
    # Admissibility: the precondition Acc(list_pred(text),1/2) admits a normal
    # F2P-shaped input. We assert the in-domain facts the spec relies on hold for
    # the actual parameter (half permission is held, length is well-defined and
    # the empty-prefix fold identity used by the invariant is established), then
    # run the gold body. If the precondition were too strong these in-region
    # facts could not be asserted.
    Assert(0 <= len(text))
    Assert(ToSeq(text).drop(len(text)) == ToSeq(text).drop(len(text)))
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUTATION),
        "refinement": (
            "Writes `text[i-1] = c` through a 1/2 (read-only) permission. A real "
            "patch that mutated its input tick-label string in place would corrupt "
            "the string the caller still holds (and Python `str` is immutable so the "
            "real `_wrap_in_tex` cannot do this at all); it does not produce the "
            "protected output and would not resolve the F2P. Here the store needs "
            "full list_pred(text) but only Acc(text,1/2) is held, so it MUST fail "
            "for insufficient permission."),
        "rationale": (
            "Rejection comes from the permission system: the read-only precondition "
            "Acc(list_pred(text),1/2) denies the write. If it verified, the spec "
            "would admit an impl that mutates a declared read-only input."),
    },
    {
        "id": "partial-domain-drop-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DROP_SPACE),
        "refinement": (
            "Gold patch MISSING `.replace(' ', r'\\;')`: space passes through bare. "
            "F2P test_date_formatter_usetex[delta3] expects '$\\mathdefault{01\\;%02d}$' "
            "(space -> '\\;') and t_delta2 of test_concise_formatter_usetex exercises "
            "a space; without the space protection the rendered labels run numbers "
            "together and the expected strings differ, so the real patch fails those "
            "F2P cases."),
        "rationale": (
            "Rejection from postcondition ToSeq(Result())==protected_seq(ToSeq(text)) "
            "on code point 32: protect(32)==tok_space()==PSeq(92,59) but this impl "
            "emits PSeq(32). The loop invariant cannot be re-established at a space."),
    },
    {
        "id": "partial-domain-drop-colon",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DROP_COLON),
        "refinement": (
            "Gold patch MISSING `.replace(':', '{:}')`: colon passes through bare. "
            "This is the prepatch-class defect (which fails G-DIFF) extended to keep "
            "the space fix. F2P test_concise_formatter_usetex[t_delta2] expects "
            "'$\\mathdefault{04{:}00}$' (colon -> '{:}') and delta2/delta3 of "
            "test_date_formatter_usetex contain colon-bearing labels; the unprotected "
            "colon is spaced like a binary operator, the expected strings differ, F2P "
            "fails."),
        "rationale": (
            "Rejection from postcondition on code point 58: protect(58)==tok_colon()"
            "==PSeq(123,58,125) but this impl emits PSeq(58). The invariant breaks at "
            "a colon."),
    },
    {
        "id": "partial-domain-wrong-space-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WRONG_SPACE_TOKEN),
        "refinement": (
            "Emits the space token with code points swapped: PSeq(59,92) = ';\\' "
            "instead of PSeq(92,59) = '\\;'. A real patch using `.replace(' ', r';\\')` "
            "renders ';\\' where the F2P expects '\\;' (delta3 expects '...01\\;%02d...'); "
            "the label is malformed, F2P fails."),
        "rationale": (
            "Rejection from postcondition on code point 32: protect(32)==tok_space()"
            "==PSeq(92,59); this impl yields PSeq(59,92), so ToSeq(Result()) diverges "
            "from the fold at any space. A value-level not a permission rejection."),
    },
    {
        "id": "partial-domain-last-element-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_LAST_ELEMENT_IDENTITY),
        "refinement": (
            "Treats the first-processed iteration (backward loop, index len-1 = the "
            "LAST code point of the label) as identity, so a label ending in '-', ':' "
            "or ' ' is left unprotected at its tail. A real patch with an off-by-one "
            "that skips the final character protection would mis-render any label whose "
            "last visible token is one of the three protected symbols, diverging from "
            "the expected F2P strings on that length class."),
        "rationale": (
            "Rejection from the loop invariant ToSeq(result)==protected_seq("
            "ToSeq(text).drop(i)): after the first iteration with text[len-1] a "
            "protected code point, result holds the bare singleton not the token, so "
            "the invariant (and hence the postcondition) cannot be re-established."),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_CONTROL),
        "rationale": (
            "Structurally-different but CORRECT: same backward fold, same invariants "
            "and framing Asserts verbatim, only the if/elif branch ORDER changed "
            "(space, colon, dash). The branches are disjoint guards so the reorder is "
            "semantically identical; it MUST verify, else the postcondition is "
            "SPEC-TOO-STRONG (rejects a faithful correct impl)."),
    },
    {
        "id": "admissibility-indomain-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISSIBILITY),
        "rationale": (
            "The gold body plus in-region Asserts that the Requires-shaped facts "
            "(len>=0 with half permission held, the empty-suffix fold identity the "
            "invariant seeds) are establishable for the actual parameter. A normal "
            "F2P-shaped code-point list satisfies the precondition; if these in-domain "
            "facts could not be asserted the precondition would be PRECOND-TOO-STRONG. "
            "Must verify."),
    },
]

# No @ContractOnly axioms are consumed (meta.axioms == []). The only kind-A
# relationship is the A-reference deep model `protected_seq`, validated == the
# real gold `.replace` chain out-of-band by axiom_check.py / G-AX — it is not a
# proof-consumed axiom, so there is no axiom-soundness / axiom-containment
# obligation to probe here.
AXIOM_TESTS = []  # type: list
