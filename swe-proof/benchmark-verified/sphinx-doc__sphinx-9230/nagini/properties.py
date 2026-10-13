# properties.py — PBT manifest for sphinx-doc__sphinx-9230. NOT a Nagini module;
# a record of adversarial cases. The runner (swebench_nagini.pbt) executes each
# and stamps RESULT. Spec cases are full model.py variants (SAME frozen spec,
# only the impl region swapped) checked by Nagini verify + markers.same_spec.
#
# Defended surface (read model.py + refinement.md + mapping.md):
#   The gold patch is the one-liner `fieldarg.split(None,1)` -> `.rsplit(None,1)`
#   in sphinx/util/docfields.py. Two observable outputs of that single split are
#   modeled as two functions over the token run `tokens: List[int]`:
#     * parsed_argument_name -> the FINAL token  t(n-1)               (argname)
#     * parsed_argument_type -> the ordered PREFIX t0..t(n-2), single-space
#                               rendered via the front-recursive @Pure `joined`  (argtype)
#   Both take `tokens` READ-ONLY: Requires(Acc(list_pred(tokens), 1/2)) and
#   re-Ensure that same half permission, so the input is non-writable.
#
#   The two load-bearing postconditions are
#     name:  ToSeq(Result()) == PSeq(encode_name(last_token(ToSeq(tokens))))
#     type:  ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1))
#   BOTH oracles (`last_token`, `joined`) are @Pure and fully GROUNDED in the
#   input args (they unfold to functions of `tokens`); there is NO opaque
#   answer-key / @ContractOnly marker to echo, so the ungrounded-oracle-echo
#   class is N/A here (echoing the grounded oracle IS the correct answer — see
#   'assessment'; an honest cheapest-impl positive control stands in its place).
#
#   There are NO @ContractOnly axioms and NO consumed axioms (the deep helpers
#   `joined`/`last_token` are A-reference deep models, fully unfolded @Pure, NOT
#   consumed). meta.json axioms == []. So AXIOM_TESTS = [] (the str.rsplit
#   A-reference is validated out-of-band by axiom_check.py / G-AX, not in this
#   lane).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9230"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact gold impl bodies (the text BETWEEN # impl-start / # impl-end). Every
# _swap below targets text strictly inside one of these two impl regions; the
# frozen spec (signatures, pre/post-conditions, pure helpers, axioms comment) is
# never touched, so markers.same_spec stays True for every case.
# ---------------------------------------------------------------------------

_GOLD_NAME_IMPL = """    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result"""

_GOLD_TYPE_IMPL = """    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result"""

# sanity: both gold bodies must be present verbatim and unique in _BASE.
assert _BASE.count(_GOLD_NAME_IMPL) == 1, "name impl drift"
assert _BASE.count(_GOLD_TYPE_IMPL) == 1, "type impl drift"


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY (both inputs are Acc(tokens, 1/2) read-only).
# A rival that WRITES to the read-only input `tokens` to satisfy/short-circuit
# the postcondition must be REJECTED for INSUFFICIENT PERMISSION (only 1/2 of
# list_pred(tokens) is held; a write needs the full 1/1). Gold invariants/asserts
# kept verbatim so the rejection is attributable to the write, not a proof gap.
# ===========================================================================

# name: overwrite the last slot before reading it. A write to tokens[k] requires
# full permission; the spec only grants 1/2 -> reject.
_FRAME_NAME = _swap(
    _BASE, _GOLD_NAME_IMPL,
    """    tokens[len(tokens) - 1] = tokens[len(tokens) - 1]  # WRITE to read-only input
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result""")

# type: same frame violation inside the prefix loop's function body.
_FRAME_TYPE = _swap(
    _BASE, _GOLD_TYPE_IMPL,
    """    tokens[0] = tokens[0]  # WRITE to read-only input (only 1/2 perm held)
    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result""")


# ===========================================================================
# (2) POSITIVE CONTROLS (soundness). Structurally-DIFFERENT but CORRECT impls
# that MUST verify (else SPEC-TOO-STRONG). Each keeps every gold proof
# obligation it still needs.
# ===========================================================================

# name: local-variable reshape — compute the last index into a named local and
# read through it, and keep the framing Asserts. Same value, different shape.
_POS_NAME = _swap(
    _BASE, _GOLD_NAME_IMPL,
    """    n = len(tokens)  # type: int
    idx = n - 1  # type: int
    last = tokens[idx]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    encoded = encode_name(last)  # type: int
    result = [encoded]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result""")

# type: branch-REORDER positive control. The gold loop is BACKWARD (i from
# prefix_len down to 1, prepending) to match the FRONT-recursive @Pure `joined`;
# a forward-append control would need a joined(a+b)==joined(a)+joined(b) lemma
# the verifier won't auto-discharge (pilot directive #3) — so we KEEP the
# backward loop and only reorder the if/else (test the non-last branch first)
# and reshape locals, preserving every gold Invariant/Assert.
_POS_TYPE = _swap(
    _BASE, _GOLD_TYPE_IMPL,
    """    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i != prefix_len:
            # reordered: handle the NON-last prefix element first
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result""")


# ===========================================================================
# (3) PARTIAL-DOMAIN rivals (uniqueness). Correct on most of the F2P/P2P domain
# but diverging on a sub-domain. Must be REJECTED by the all-inputs postcondition.
# ===========================================================================

# name, partial-domain: return the FIRST token's encoding when n == 2, otherwise
# the (correct) last token. Diverges on the 2-token sub-domain (e.g. `int age`):
# yields `int` where the spec/gold demand `age`. The all-n>=2 postcondition
# ToSeq(Result()) == PSeq(encode_name(last_token(...))) must reject it.
_PD_NAME = _swap(
    _BASE, _GOLD_NAME_IMPL,
    """    n = len(tokens)  # type: int
    if n == 2:
        first = tokens[0]  # type: int
        wrong = [encode_name(first)]  # type: List[int]
        return wrong
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result""")

# type, partial-domain (off-by-one truncation): take only the FIRST prefix_len-1
# tokens, dropping the LAST token of the type. Correct when the type is a single
# token (n == 2, prefix has length 1 -> ... but then it drops to empty); diverges
# for every multi-token type (n >= 3, e.g. `Dict[str, str] params` -> drops the
# `str]` chunk). Pins only part of the prefix; the full-prefix postcondition
# ToSeq(Result()) == joined(take(len(tokens)-1)) must reject it.
_PD_TYPE = _swap(
    _BASE, _GOLD_TYPE_IMPL,
    """    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    short_len = len(tokens) - 2  # type: int   # off-by-one: drops the last type token
    result = []  # type: List[int]
    i = short_len
    while i > 0:
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(short_len == len(tokens) - 2)
        Invariant(0 <= i and i <= short_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(short_len).drop(i)))
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(short_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(short_len).drop(i - 1).drop(1)
               == tokens_s.take(short_len).drop(i))
        if i == short_len:
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(short_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(short_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(short_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(short_len)))
    return result""")


# ===========================================================================
# (4) SUPPORTING near-misses (uniqueness). The exact pre-patch bug (LEFT split)
# re-expressed inside the impl region — a faithful real patch (keeping
# `split(None,1)`) does NOT resolve the F2P. Cheap supporting cases that still
# carry a real refinement (they ARE model_prepatch's behaviour).
# ===========================================================================

# name = the WHOLE remainder after the first token (old split(None,1) name side).
# Identical in shape to model_prepatch.py's parsed_argument_name impl.
_PREPATCH_NAME = _swap(
    _BASE, _GOLD_NAME_IMPL,
    """    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    n = len(tokens)  # type: int
    result = []  # type: List[int]
    i = n
    while i > 1:
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(n == len(tokens))
        Invariant(1 <= i and i <= n)
        Invariant(ToSeq(result) == joined(tokens_s.drop(i)))
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.drop(i - 1)[0] == elt)
        Assert(tokens_s.drop(i - 1).drop(1) == tokens_s.drop(i))
        if i == n:
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.drop(1)))
    return result""")

# type = only the FIRST token (old split(None,1) type side). Identical in shape
# to model_prepatch_2.py's parsed_argument_type impl.
_PREPATCH_TYPE = _swap(
    _BASE, _GOLD_TYPE_IMPL,
    """    first = tokens[0]  # type: int
    result = [encode_name(first)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(first)))
    return result""")


# ===========================================================================
# (5) ADMISSIBILITY (precondition not too strong). Keep the gold impl and add an
# in-region assertion that a representative F2P-shaped fact is derivable from the
# precondition (Requires len>=2 + half permission) — proving the precondition
# admits a normal input rather than being vacuously unsatisfiable. expect verify.
# ===========================================================================

_ADMISS_NAME = _swap(
    _BASE, _GOLD_NAME_IMPL,
    """    Assert(len(tokens) >= 2)            # precond admits an n>=2 input
    Assert(len(ToSeq(tokens)) == len(tokens))
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    Assert(len(ToSeq(result)) == 1)     # F2P-shaped: name is one token
    return result""")


SPEC_TESTS = [
    {
        "id": "frame-mut-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_NAME,
        "refinement": (
            "A faithful real patch that overwrites the parsed token run to "
            "force the name does not exist in gold (gold only reads fieldarg via "
            "rsplit). If such a write verified, the read-only contract would be "
            "vacuous; the actual behaviour (mutating the field-argument tokens) "
            "would corrupt the type side and not resolve test_info_field_list."),
        "rationale": (
            "REJECT comes from the PERMISSION SYSTEM: tokens is held at "
            "Acc(list_pred(tokens), 1/2); a store tokens[k]=... requires the full "
            "1/1, so Nagini rejects for insufficient permission. #1 weakness class."),
    },
    {
        "id": "frame-mut-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_TYPE,
        "refinement": (
            "Gold never writes the token run; a patch that mutates fieldarg's "
            "tokens to satisfy the type postcondition vacuously would change the "
            "parsed name/type observably and fail the F2P assertion on "
            "`:param Dict[str, str] params:`."),
        "rationale": (
            "REJECT from the PERMISSION SYSTEM: only Acc(list_pred(tokens),1/2) "
            "is held; tokens[0]=... needs full permission -> insufficient "
            "permission. Gold invariants/asserts kept verbatim so the failure is "
            "attributable to the write."),
    },
    {
        "id": "pos-control-name",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NAME,
        "rationale": (
            "A structurally-different but CORRECT name impl (named index + "
            "encoded local), keeping the framing Asserts, MUST verify — else the "
            "name postcondition would be SPEC-TOO-STRONG. Same value t(n-1)."),
    },
    {
        "id": "pos-control-type",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TYPE,
        "rationale": (
            "Branch-reordered (non-last case first) backward construction "
            "preserving every gold Invariant/Assert MUST verify. Backward loop "
            "kept deliberately to match the FRONT-recursive @Pure `joined` (a "
            "forward-append control would need an un-auto-dischargeable fold "
            "lemma, pilot directive #3) — else SPEC-TOO-STRONG."),
    },
    {
        "id": "partial-domain-name-n2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_NAME,
        "refinement": (
            "Real patch: when there are exactly two whitespace tokens take the "
            "FIRST as the name. For `:param int age:` (fieldarg `int age`, n==2) "
            "this yields name `int` instead of `age` — the F2P test asserts the "
            "parameter name is `age`, so this patch does NOT resolve."),
        "rationale": (
            "REJECT from the name POSTCONDITION ToSeq(Result()) == "
            "PSeq(encode_name(last_token(...))), which pins the name to t(n-1) "
            "for ALL n>=2 including n==2; returning t0 there violates it."),
    },
    {
        "id": "partial-domain-type-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_TYPE,
        "refinement": (
            "Real patch: drop the last token of the type prefix (off-by-one). "
            "For `:param Dict[str, str] params:` (tokens `Dict[str,` `str]` "
            "`params`, n==3) it renders the type as `Dict[str,` dropping `str]` "
            "— the truncated-type bug the issue reports — so the F2P type text "
            "`Dict[str, str]` is wrong and the patch does NOT resolve."),
        "rationale": (
            "REJECT from the type POSTCONDITION ToSeq(Result()) == "
            "joined(take(len(tokens)-1)): it pins the FULL leading run; "
            "joined(take(len(tokens)-2)) drops t(n-2), violating the equality "
            "for every n>=3."),
    },
    {
        "id": "prepatch-name-split-remainder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PREPATCH_NAME,
        "refinement": (
            "This IS the pre-patch behaviour: name = whole remainder after the "
            "first token (old split(None,1)). A faithful patch that keeps "
            "split(None,1) leaves `:param Dict[str, str] params:` parsing the "
            "name as `str] params`, exactly the bug — does NOT resolve the F2P. "
            "(model_prepatch.py's parsed_argument_name, verbatim.)"),
        "rationale": (
            "REJECT from the name POSTCONDITION pinning t(n-1): the join of "
            "t1..t(n-1) is a >1-token sequence for n>=3, != PSeq(encode_name("
            "last_token)). Supporting near-miss with a real refinement."),
    },
    {
        "id": "prepatch-type-first-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PREPATCH_TYPE,
        "refinement": (
            "This IS the pre-patch behaviour: type = first token only (old "
            "split(None,1) head). Keeping split(None,1) parses the type of "
            "`:param Dict[str, str] params:` as `Dict[str,` — the reported bug — "
            "so it does NOT resolve the F2P. (model_prepatch_2.py's "
            "parsed_argument_type, verbatim.)"),
        "rationale": (
            "REJECT from the type POSTCONDITION ToSeq(Result()) == "
            "joined(take(len(tokens)-1)): a single-token type drops every later "
            "prefix token for n>=3, violating the equality. Supporting near-miss "
            "with a real refinement."),
    },
    {
        "id": "admiss-name",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_NAME,
        "rationale": (
            "Gold name impl + in-region Asserts deriving F2P-shaped facts "
            "(len(tokens)>=2, len(ToSeq(tokens))==len(tokens), one-token result) "
            "from the precondition. Must verify — else PRECOND-TOO-STRONG (the "
            "Requires would be vacuously unsatisfiable for a normal input)."),
    },
]


# No @ContractOnly axioms and no consumed axioms in this bundle (meta.json
# axioms == []). The str.rsplit(None,1) correspondence is an A-reference deep
# model validated out-of-band by axiom_check.py (G-AX), not consumed in the
# proof — so there is nothing for the in-Docker axiom lane to probe.
AXIOM_TESTS = []
