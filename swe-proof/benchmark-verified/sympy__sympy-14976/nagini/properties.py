"""PBT manifest for sympy__sympy-14976 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec exactly (region-surgery: only the
text strictly between `# impl-start` and `# impl-end` is edited, so `same_spec`
is guaranteed) and are checked by Nagini verify. Axiom cases would be
real-callee probes in Docker — there are NONE here (no consumed @ContractOnly
axioms; `ctor`/`rendered` are A-references already covered by axiom_check.py /
G-AX), so AXIOM_TESTS = [].

Defended surface (read carefully before editing any case):

  render_mpf_ratio(p_digits, q_digits) -> List[int]
    Requires Acc(list_pred(p_digits), 1/2)   # READ-ONLY numerator carrier
    Requires Acc(list_pred(q_digits), 1/2)   # READ-ONLY denominator carrier
    Ensures  Acc(list_pred(p_digits), 1/2)   # framing: inputs returned intact
    Ensures  Acc(list_pred(q_digits), 1/2)
    Ensures  Acc(list_pred(Result()))
    Ensures  ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits))

  where the LOAD-BEARING postcondition pins the result to the @Pure deep model

    rendered(p, q) = ctor() '(' p ')' '/' ctor() '(' q ')'
                   = mpmath.mpf '(' p ')' '/' mpmath.mpf '(' q ')'

  i.e. BOTH operands wrapped in the mpmath.mpf(...) constructor, divided. This
  is the discriminating content of the gold patch
    '{0}({1})/{0}({2})'.format(self._module_format('mpmath.mpf'), e.p, e.q)
  vs the pre-patch inherited bare '%s/%s' % (p, q).

  `rendered` is GROUNDED in the inputs (a fully-unfolded function of p and q,
  not an opaque answer-key oracle), so the dangerous "echo a @Pure oracle that
  could be wrong" attack does not apply — there is no wrong echo to build (see
  the cheapest-impl positive control `pos-cheapest` instead). The F2P test
  `test_MpmathPrinter` asserts doprint(Rational(1,2)) == 'mpmath.mpf(1)/mpmath.mpf(2)'.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14976"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl body (everything strictly between the markers, excluding
# the marker lines themselves). Every variant is built by _swap-ing this block.
_GOLD_IMPL = """    out = []  # type: List[int]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # numerator digits
    out = out + p_digits
    # ')' '/'
    out = out + [41]
    out = out + [47]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # denominator digits
    out = out + q_digits
    # ')'
    out = out + [41]
    return out"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Return the full model source with the impl region body replaced by
    new_body (only the text strictly inside # impl-start/# impl-end changes)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# Positive controls (soundness): structurally-DIFFERENT but CORRECT impls that
# MUST verify. If a faithful correct impl cannot satisfy Ensures => SPEC-TOO-STRONG.
# Both are fold-free concatenations matching `rendered`'s structure exactly, so
# they avoid the forward-append-vs-front-recursive-fold proof trap entirely.
# ---------------------------------------------------------------------------

# Single-expression concatenation: the gold builds the same sequence with a
# left-to-right chain of `out = out + ...`; this assembles it as ONE expression
# in a different associativity / write shape. Equal sequence, no loop.
_POS_SINGLE = """    ctor1 = [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]  # type: List[int]
    ctor2 = [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]  # type: List[int]
    out = ctor1 + [40] + p_digits + [41] + [47] + ctor2 + [40] + q_digits + [41]  # type: List[int]
    return out"""

# Reverse build order: assemble the denominator-side tail FIRST into a local,
# the numerator-side head SECOND, then concatenate head + tail. Different write
# order / data shape, identical resulting sequence. Keeps no loop -> no lemma.
_POS_REORDER = """    head = [109, 112, 109, 97, 116, 104, 46, 109, 112, 102] + [40] + p_digits + [41] + [47]  # type: List[int]
    tail = [109, 112, 109, 97, 116, 104, 46, 109, 112, 102] + [40] + q_digits + [41]  # type: List[int]
    out = head + tail  # type: List[int]
    return out"""


# ---------------------------------------------------------------------------
# Admissibility: a self-call on an F2P-shaped input (the literal '1' / '2' digit
# carriers of the hidden test Rational(1,2)) confirming the Requires admits it.
# A second contracted function builds fresh lists (full perm), calls the modeled
# function (consuming the 1/2 it needs), and asserts the rendered postcondition
# holds for the F2P case. Lives entirely INSIDE the impl region of a helper that
# is appended after render_mpf_ratio; the frozen spec is untouched.
# ---------------------------------------------------------------------------
_ADMISS = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    # admissibility witness: a normal F2P-shaped input ('1' digits, '2' digits)
    # establishes the precondition and the call verifies, so Requires is not
    # over-strong. Assert the discriminating postcondition for that input.
    p1 = [49]  # type: List[int]
    q1 = [50]  # type: List[int]
    Assert(ToSeq(p1) == PSeq(49))
    Assert(ToSeq(q1) == PSeq(50))
    Assert(Acc(list_pred(p1), 1 / 2))
    Assert(Acc(list_pred(q1), 1 / 2))
    return out"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY: both inputs are Acc(.,1/2) read-only). A rival that
# WRITES to a read-only input. Must REJECT for INSUFFICIENT PERMISSION (you only
# hold 1/2 of list_pred(p_digits); a mutating append/setitem needs full perm).
# Gold postcondition is kept verbatim so the rejection is attributable to the
# write, not to a value mismatch. Refinement: a faithful real patch that mutates
# its int operand makes no sense (e.p/e.q are immutable ints), and any patch
# that rebuilt e.p in place would diverge from the F2P expected string.
# ---------------------------------------------------------------------------
_FRAME_APPEND = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    # WRITE to a read-only (1/2-permission) input: needs FULL permission on
    # list_pred(p_digits), which the caller never grants. Must reject.
    p_digits.append(48)
    return out"""

_FRAME_SETITEM = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    # WRITE via index assignment to the read-only denominator input: needs FULL
    # permission on list_pred(q_digits). The caller holds only 1/2. Must reject.
    q_digits[0] = 48
    return out"""


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN / discriminating-content rivals (uniqueness => SPEC-TOO-WEAK if
# any verifies). Each builds a WRONG rendered text that diverges from
# rendered(p,q) on exactly the property the gold patch defends.
# ---------------------------------------------------------------------------

# (a) Only the NUMERATOR wrapped; denominator divided bare. This is the closest
# near-miss to the fix: '{0}({1})/{2}'.format(C, p, q) -> 'mpmath.mpf(1)/2'.
# Refinement: faithful patch returns 'mpmath.mpf(1)/2' for Rational(1,2); the
# F2P asserts == 'mpmath.mpf(1)/mpmath.mpf(2)', so it does NOT resolve.
_DROP_DEN_WRAP = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [47]
    # denominator NOT wrapped in ctor '(' ... ')' -- bare digits after '/'.
    out = out + q_digits
    return out"""

# (b) Only the DENOMINATOR wrapped; numerator bare. '{1}/{0}({2})' ->
# '1/mpmath.mpf(2)'. Refinement: F2P expects 'mpmath.mpf(1)/mpmath.mpf(2)'.
_DROP_NUM_WRAP = """    out = []  # type: List[int]
    out = out + p_digits
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    return out"""

# (c) NEITHER wrapped -- the actual pre-patch bug: bare 'p/q' -> '1/2'.
# Refinement: this IS model_prepatch behaviour; F2P fails (G-DIFF confirms).
_BARE = """    out = []  # type: List[int]
    out = out + p_digits
    out = out + [47]
    out = out + q_digits
    return out"""

# (d) Operands SWAPPED: ctor(q) '/' ctor(p) -> 'mpmath.mpf(2)/mpmath.mpf(1)'.
# Both wrapped but numerator/denominator transposed. Refinement: F2P expects
# 'mpmath.mpf(1)/mpmath.mpf(2)'; the swap yields the reciprocal text -> wrong.
_SWAP = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    return out"""

# (e) WRONG constructor token (drop the final code point 'f'=102, leaving
# 'mpmath.mp'). Same structure, wrong CTOR. Refinement: real patch calling a
# typo'd module path renders 'mpmath.mp(1)/mpmath.mp(2)' -> F2P mismatch (and
# the lambdified code would NameError). Value-level near miss with real teeth.
_WRONG_CTOR = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [47]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    return out"""

# (f) Missing the division SLASH '/' (47) between the two wrapped operands ->
# 'mpmath.mpf(1)mpmath.mpf(2)'. Structural near miss; the / is the operator that
# makes it a quotient. Refinement: F2P expects the '/' -> mismatch (and the
# rendered source would be a syntax error in the lambdified function).
_NO_SLASH = """    out = []  # type: List[int]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + p_digits
    out = out + [41]
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    out = out + q_digits
    out = out + [41]
    return out"""

# (g) Empty output -> 'mpmath.mpf' nowhere. Cheapest possible cheat; supporting
# near miss. A typed-local empty list (NOT a bare `return []`, per pilot bug #1).
_EMPTY = """    empty = []  # type: List[int]
    return empty"""


SPEC_TESTS = [
    # ---- Positive controls (soundness) --------------------------------------
    {
        "id": "pos-single-expr",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_SINGLE),
        "rationale": "structurally-different CORRECT impl (one fold-free "
                     "concatenation expression with two named ctor locals, "
                     "different write/associativity shape) builds exactly "
                     "rendered(p,q); must verify, else SPEC-TOO-STRONG. No loop "
                     "=> no induction lemma needed (avoids the front-recursive-"
                     "fold proof trap).",
    },
    {
        "id": "pos-reorder-build",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "CORRECT impl that assembles the numerator head and "
                     "denominator tail into separate locals (reversed-ish build "
                     "order) then concatenates head+tail; same resulting "
                     "sequence as gold, different data shape. Must verify.",
    },
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_SINGLE),
        "rationale": "Honest cheapest-impl positive control standing in for the "
                     "ungrounded-oracle slot: `rendered` is GROUNDED in the args "
                     "(a fully-unfolded function of p,q, no opaque answer key), "
                     "so there is no WRONG echo to build -- the cheapest impl "
                     "that satisfies the postcondition must actually construct "
                     "rendered(p,q). It does, and must verify.",
    },
    # ---- Admissibility -------------------------------------------------------
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "a self-call on the F2P-shaped input (p='1'=[49], q='2'="
                     "[50], the hidden-test Rational(1,2)) establishes the "
                     "Requires (Acc(list_pred,1/2) on fresh full-perm lists) and "
                     "the call verifies, asserting ToSeq(r)==rendered(PSeq(49),"
                     "PSeq(50)); so the precondition admits a normal input, else "
                     "PRECOND-TOO-STRONG.",
    },
    # ---- Frame-mutation (MANDATORY: both inputs are Acc(.,1/2) read-only) ----
    {
        "id": "frame-append-p",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_APPEND),
        "refinement": "The numerator operand in the gold patch is e.p, an "
                      "immutable Python int -- the faithful real patch cannot "
                      "and does not mutate it. A 'patch' that appended a digit "
                      "to the numerator would render e.g. 'mpmath.mpf(10)/...' "
                      "for Rational(1,2), diverging from the F2P expected "
                      "'mpmath.mpf(1)/mpmath.mpf(2)', so it would NOT resolve.",
        "rationale": "appends to p_digits, a READ-ONLY input held at 1/2 "
                     "permission; the write needs FULL list_pred(p_digits) perm. "
                     "Rejected by the PERMISSION SYSTEM (insufficient permission), "
                     "not a value mismatch -- gold postcondition kept verbatim.",
    },
    {
        "id": "frame-setitem-q",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_SETITEM),
        "refinement": "The denominator operand e.q is an immutable int; the "
                      "faithful real patch never assigns into it. An impl that "
                      "overwrote a denominator digit would change the rendered "
                      "string (e.g. 'mpmath.mpf(1)/mpmath.mpf(0...)') and fail "
                      "the F2P observation, so it would NOT resolve.",
        "rationale": "index-assigns q_digits[0], a READ-ONLY input at 1/2 "
                     "permission; needs FULL list_pred(q_digits). Rejected by the "
                     "PERMISSION SYSTEM. Also the Ensures Acc(list_pred(q_digits),"
                     "1/2) framing requires the input to be returned intact.",
    },
    # ---- Partial-domain / discriminating-content (uniqueness) ---------------
    {
        "id": "drop-den-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_DEN_WRAP),
        "refinement": "Faithful patch '{0}({1})/{2}'.format(C,e.p,e.q) renders "
                      "Rational(1,2) as 'mpmath.mpf(1)/2'. The F2P asserts "
                      "== 'mpmath.mpf(1)/mpmath.mpf(2)', so it does NOT resolve "
                      "(and the lambdified quotient loses precision -- the very "
                      "bug the issue reports).",
        "rationale": "result lacks the ctor '(' ... ')' wrapping around the "
                     "denominator, so ToSeq(Result()) != rendered(p,q) "
                     "(rendered prepends ct() '(' before q and closes ')'). "
                     "Rejected by the load-bearing postcondition clause.",
    },
    {
        "id": "drop-num-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_NUM_WRAP),
        "refinement": "Faithful patch '{1}/{0}({2})'.format(C,e.p,e.q) renders "
                      "Rational(1,2) as '1/mpmath.mpf(2)' != F2P expected "
                      "'mpmath.mpf(1)/mpmath.mpf(2)', so it does NOT resolve.",
        "rationale": "numerator not wrapped; ToSeq(Result()) != rendered(p,q). "
                     "Rejected by the postcondition.",
    },
    {
        "id": "bare-division",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BARE),
        "refinement": "This is the pre-patch behaviour itself (inherited "
                      "StrPrinter '%s/%s' % (p,q) -> '1/2'); model_prepatch.py "
                      "reproduces it and G-DIFF confirms it FAILS the "
                      "postcondition. F2P does NOT resolve.",
        "rationale": "neither operand wrapped -> ToSeq(Result()) == p '/' q != "
                     "rendered(p,q). Rejected by the postcondition (the exact "
                     "clause that senses the change).",
    },
    {
        "id": "swap-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP),
        "refinement": "Faithful patch '{0}({2})/{0}({1})'.format(C,e.p,e.q) "
                      "renders Rational(1,2) as 'mpmath.mpf(2)/mpmath.mpf(1)' "
                      "(the reciprocal), != F2P expected. Numerically wrong "
                      "(2/1 vs 1/2), so it does NOT resolve.",
        "rationale": "operands transposed: ToSeq(Result()) wraps q then p, != "
                     "rendered(p,q) which wraps p then q. Rejected by the "
                     "postcondition's positional structure.",
    },
    {
        "id": "wrong-ctor-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_CTOR),
        "refinement": "A patch using a typo'd token (e.g. _module_format("
                      "'mpmath.mp')) renders 'mpmath.mp(1)/mpmath.mp(2)' != F2P "
                      "expected 'mpmath.mpf(1)/mpmath.mpf(2)'; and the lambdified "
                      "code would NameError on mpmath.mp. Does NOT resolve.",
        "rationale": "ctor token is 'mpmath.mp' (missing final 'f'=102) so "
                     "ToSeq(Result()) != rendered(p,q) (which uses ctor()=="
                     "[...,109,112,102]). Rejected by the postcondition.",
    },
    {
        "id": "no-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_SLASH),
        "refinement": "Dropping the '/' renders 'mpmath.mpf(1)mpmath.mpf(2)', "
                      "not a quotient; != F2P expected and a syntax error in the "
                      "lambdified function. Does NOT resolve.",
        "rationale": "the [47] '/' token between the two wrapped operands is "
                     "absent, so ToSeq(Result()) != rendered(p,q) (rendered "
                     "interleaves PSeq(47)). Rejected by the postcondition.",
    },
    {
        "id": "empty-output",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY),
        "refinement": "Returning '' renders nothing for any Rational; trivially "
                      "!= the F2P expected string. Supporting cheapest cheat; "
                      "does NOT resolve.",
        "rationale": "empty result; ToSeq(Result())==PSeq() (empty) != "
                     "rendered(p,q) (length 23 for the F2P input). Rejected by "
                     "the postcondition. (typed-local empty list, not a bare "
                     "`return []`, per the type-comment authoring rule).",
    },
]

# No consumed @ContractOnly axioms; `ctor`/`rendered` are A-references validated
# by axiom_check.py (G-AX) out-of-band. The PBT axiom lane covers consumed
# axioms only, so it is vacuous here.
AXIOM_TESTS = []
