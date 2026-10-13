# properties.py — PBT falsification battery for sympy__sympy-23262.
#
# NOT a Nagini module: a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Every spec case is a full model.py variant that
# shares the FROZEN spec exactly (markers.same_spec) and changes ONLY the text inside
# the single `# impl-start` / `# impl-end` region (the elided implementation, which
# includes the nested invariants). The frozen spec — the @Pure region, the
# pre/post-conditions, the signatures — is never touched.
#
# Defended surface (render_container(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]):
#   * Inputs are PURE immutable sequences (PSeq) + a bool. There is NO heap input,
#     NO Acc(...) permission, NO list_pred. Nothing can be mutated => the
#     frame-mutation weakness class does NOT apply here (see 'assessment').
#   * Load-bearing postcondition: Result() == rendered(elems, is_paren), where
#     `rendered` is a fully spelled-out structural fold over the INPUT elems
#     (left_delim + joined + right_delim). It is GROUNDED in the args, not an
#     opaque answer-key oracle => there is no "wrong echo" to build; echoing
#     `rendered` IS the correct answer (positive control instead).
#   * The discriminating clauses (the gold fix): the parenthesis kind closes with
#     the REQUIRED trailing comma ',)' (Result()[-1]==')' & Result()[-2]==',') and
#     a one-element parenthesis container is exactly '(' + elems[0] + ',)'. This is
#     the gh-23224 regression: lambdify([], (1,)) must emit "(1,)" (a 1-tuple), not
#     "(1)" (the bare int). The F2P test test_issue_14941 asserts f2b() == (1,).
from pathlib import Path

INSTANCE = "sympy__sympy-23262"
FLOAT_ENCODING = None  # meta.json float_encoding is null; unused.

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold implementation region body (between the impl markers). Every
# variant is produced by swapping this whole block for a variant block, so the
# edit is GUARANTEED to lie entirely inside the impl region (same_spec holds).
_GOLD_IMPL = '''    # left, right := the delimiter pair for the requested kind. The parenthesis
    # kind's closing delimiter carries the trailing comma.
    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma(), rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
    # body := the ", "-joined element list (front-recursive fold, built back to
    # front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(elems))
        Invariant(body == joined(elems.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
        # its head is elems[i-1] and its tail is elems.drop(i).
        Assert(elems.drop(i - 1)[0] == elems[i - 1])
        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            Assert(len(elems.drop(i - 1)) == 1)
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            Assert(len(elems.drop(i - 1)) >= 2)
            body = elems[i - 1] + sep() + body
        i = i - 1
    result = left + body + right  # type: PSeq[int]
    return result'''

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block not unique"

# The proof skeleton that any loop-based variant must keep VERBATIM (the
# front-recursive `joined` invariant + the per-step unfold bridge asserts). The
# pilot's failure mode #2/#3 is dropping these and failing for a PROOF reason; we
# never touch them in any positive control.
_FOLD_SKELETON = '''    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(elems))
        Invariant(body == joined(elems.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
        # its head is elems[i-1] and its tail is elems.drop(i).
        Assert(elems.drop(i - 1)[0] == elems[i - 1])
        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            Assert(len(elems.drop(i - 1)) == 1)
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            Assert(len(elems.drop(i - 1)) >= 2)
            body = elems[i - 1] + sep() + body
        i = i - 1'''


def _variant(impl_body):
    """Build a full model.py variant by replacing the whole gold impl body."""
    return _swap(_BASE, _GOLD_IMPL, impl_body)


# ----------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls. Each
# MUST verify; if a faithful correct impl cannot, the spec is SPEC-TOO-STRONG.
# Each keeps the front-recursive fold skeleton VERBATIM (so the `joined`
# invariant + per-step unfold asserts still discharge) and only reshapes the
# executable surface around it (pilot bugs #2/#3 avoided).
# ----------------------------------------------------------------------------

# pos-control-1: branch-reorder. The delimiter selection tests `not is_paren`
# first (square-bracket branch leads) instead of `is_paren`. Same delimiter
# values, reordered control flow.
_POS_REORDER = '''    # Delimiter selection with the branch order reversed (square-bracket kind
    # leads). Same delimiter values as gold.
    if not is_paren:
        left = PSeq(lbracket())  # type: PSeq[int]
        right = PSeq(rbracket())  # type: PSeq[int]
    else:
        left = PSeq(lparen())
        right = PSeq(comma(), rparen())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''

# pos-control-2: the parenthesis closing delimiter built by concatenation
# (PSeq(comma()) + PSeq(rparen())) rather than the 2-arg literal
# PSeq(comma(), rparen()). Same sequence value [44, 41]; different construction.
_POS_CONCAT_DELIM = '''    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma()) + PSeq(rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''

# pos-control-3: assemble the result via the pure delimiter helpers (the same
# `left_delim`/`right_delim` the spec uses) over the loop-proven body, instead
# of the local PSeq literals. Reuses `body == joined(elems)` from the invariant
# and `rendered == left_delim + joined + right_delim`, so no new lemma is needed.
_POS_VIA_HELPERS = _FOLD_SKELETON + '''
    # body == joined(elems) by the loop invariant at i == 0; assemble through the
    # SAME pure delimiter helpers the spec's `rendered` uses.
    result = left_delim(is_paren) + body + right_delim(is_paren)  # type: PSeq[int]
    return result'''

# admiss-witness: keep the gold impl and inject a concrete F2P-shaped witness
# assertion — a one-element parenthesis container holding the fragment "1"
# (code point 49) renders to '(' '1' ',)' (= "(1,)"). There is no precondition
# (pure inputs), so admissibility is near-vacuous; this pins that the spec's own
# `rendered` admits the exact gh-23224 F2P input shape and produces the 1-tuple
# literal text. Must verify (else PRECOND/SPEC-TOO-STRONG on the F2P shape).
# The witness statements must be injected BEFORE the trailing `return result`
# (placing them after the return is dead code, which Nagini rejects at
# translation time as `dead.code` — a test-construction error, not a spec
# rejection); they do not depend on `result`.
_ADMISS = _swap(
    _GOLD_IMPL,
    '''    result = left + body + right  # type: PSeq[int]
    return result''',
    '''    result = left + body + right  # type: PSeq[int]
    # Admissibility witness (gh-23224 / F2P test_issue_14941: f2b() == (1,)):
    # the one-element parenthesis container whose only fragment is "1" (49)
    # renders exactly to "(1,)" = '(' '1' ',)'. The precondition (none) admits it.
    one = PSeq(PSeq(49))  # type: PSeq[PSeq[int]]
    Assert(rendered(one, True) == PSeq(lparen()) + PSeq(49) + PSeq(comma(), rparen()))
    Assert(len(rendered(one, True)) == 4)
    return result''')


# ----------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals (wrong impls that share the spec). Each
# MUST be rejected; if any verifies, the spec is SPEC-TOO-WEAK. Each carries the
# refinement argument that its faithful real patch would NOT resolve the F2P/P2P.
# ----------------------------------------------------------------------------

# rej-1: the PRE-PATCH bug verbatim — the parenthesis closing delimiter is the
# lone ')' with NO trailing comma (right = PSeq(rparen())). This is exactly
# `left, right = "()"` (the gold patch reverts FROM this). Fails the
# trailing-comma clauses + the single-element clause + Result()==rendered.
_REJ_NO_TRAILING_COMMA = '''    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''

# rej-2: the parenthesis kind borrows the square-bracket delimiters '[' ']'.
# Fails kind fidelity (Result()[0]==lparen()) and Result()==rendered for the
# paren kind.
_REJ_PAREN_AS_BRACKET = '''    if is_paren:
        left = PSeq(lbracket())  # type: PSeq[int]
        right = PSeq(rbracket())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''

# rej-3: the square-bracket (list) kind borrows the parenthesis delimiters
# '(' ',)'. Correct on tuples, wrong on lists. Fails kind fidelity
# (Implies(not is_paren, Result()[0]==lbracket())).
_REJ_LIST_AS_PAREN = '''    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma(), rparen())  # type: PSeq[int]
    else:
        left = PSeq(lparen())
        right = PSeq(comma(), rparen())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''

# rej-4: PARTIAL-DOMAIN — correct for tuples with >= 2 elements (uses ',)') but
# the one-element parenthesis case drops the trailing comma, emitting '(' elem
# ')'. This is the precise gh-23224 regression sub-domain. Fails the
# single-element clause (and the trailing-comma clauses on that sub-domain).
_REJ_SINGLE_DROPS_COMMA = '''    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma(), rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
''' + _FOLD_SKELETON + '''
    # PARTIAL-DOMAIN bug: special-case the one-element parenthesis container to
    # use the bare ')' (no trailing comma), so it serialises as '(' elem ')'.
    # Correct on every other input; wrong on exactly the gh-23224 F2P case.
    if is_paren and len(elems) == 1:
        right = PSeq(rparen())
    result = left + body + right  # type: PSeq[int]
    return result'''

# rej-5 (SUPPORTING near-miss): the parenthesis closing delimiter swaps the
# order to ')' ',' (PSeq(rparen(), comma())) instead of ',' ')'. Fails the
# Result()[-1]==rparen() / Result()[-2]==comma() clauses and Result()==rendered.
_REJ_DELIM_ORDER = '''    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(rparen(), comma())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
''' + _FOLD_SKELETON + '''
    result = left + body + right  # type: PSeq[int]
    return result'''


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_REORDER),
        "rationale": "A correct impl with the delimiter-selection branch order "
                     "reversed (square-bracket kind leads) keeps every gold "
                     "delimiter value and the full front-recursive fold skeleton "
                     "(invariant + unfold-bridge asserts), so it must verify. If "
                     "it cannot, the spec is SPEC-TOO-STRONG (rejecting a correct "
                     "reorder).",
    },
    {
        "id": "pos-control-concat-delim",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_CONCAT_DELIM),
        "rationale": "The parenthesis closing delimiter built as PSeq(comma()) + "
                     "PSeq(rparen()) is the SAME sequence value [44, 41] as the "
                     "gold 2-arg literal PSeq(comma(), rparen()); a structurally "
                     "different construction of the identical value must verify.",
    },
    {
        "id": "pos-control-via-helpers",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_VIA_HELPERS),
        "rationale": "Assembling the result through the SAME pure delimiter "
                     "helpers the spec's `rendered` uses (left_delim/right_delim) "
                     "over the loop-proven body (body == joined(elems)) reuses the "
                     "exact spec machinery (rendered == left_delim + joined + "
                     "right_delim) and needs no new lemma, so it must verify.",
    },
    {
        "id": "admiss-f2p-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "There is no precondition (pure PSeq inputs), so "
                     "admissibility is near-vacuous; this asserts the spec's own "
                     "`rendered` admits the exact gh-23224 F2P input shape (a "
                     "one-element parenthesis container of fragment '1') and "
                     "produces '(1,)'. If this assertion cannot be established, "
                     "the spec rejects a legitimate F2P input (PRECOND/"
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "rej-prepatch-no-trailing-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_NO_TRAILING_COMMA),
        "refinement": "This is the PRE-PATCH bug verbatim: the parenthesis closing "
                      "delimiter is the lone ')' (PSeq(rparen())), i.e. exactly "
                      "`left, right = \"()\"`, which the gold patch reverts FROM. "
                      "Its faithful real patch emits 'lambdify([], (1,))' -> '(1)' "
                      "which re-parses to the bare int 1, so the F2P test "
                      "test_issue_14941 (assert f2b() == (1,)) FAILS — it does not "
                      "resolve.",
        "rationale": "If it verifies, the spec is SPEC-TOO-WEAK: it would admit the "
                     "very pre-patch behaviour the fix exists to fix. Rejection "
                     "comes from the postcondition trailing-comma clauses "
                     "(Result()[-1]==rparen() & Result()[-2]==comma()), the "
                     "single-element clause, and Result()==rendered (right_delim"
                     "(True)==PSeq(44,41)).",
    },
    {
        "id": "rej-paren-as-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PAREN_AS_BRACKET),
        "refinement": "The parenthesis kind borrows '[' ']'. Its faithful real "
                      "patch emits a tuple as '[1,]' / '[3, 2]', so the lambdified "
                      "code returns a LIST not a tuple: 'f2(2,3) == (3,2)' fails "
                      "([3,2] != (3,2)) and 'f2b() == (1,)' fails — does not "
                      "resolve.",
        "rationale": "If it verifies, SPEC-TOO-WEAK. Rejection comes from the kind "
                     "fidelity clause Implies(is_paren, Result()[0]==lparen()) and "
                     "Result()==rendered for the paren kind.",
    },
    {
        "id": "rej-list-as-paren",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_LIST_AS_PAREN),
        "refinement": "The square-bracket (list) kind borrows '(' ',)'. Its "
                      "faithful real patch emits a list as '(3, 2,)', so the "
                      "lambdified code returns a TUPLE not a list: the P2P "
                      "test_list_args (and F2P f3 = lambdify([x,y],[y,x]); "
                      "f3==[3,2]) fails ((3,2) != [3,2]) — does not resolve.",
        "rationale": "If it verifies, SPEC-TOO-WEAK. Rejection comes from the kind "
                     "fidelity clause Implies(not is_paren, Result()[0]=="
                     "lbracket()) and Result()==rendered for the list kind.",
    },
    {
        "id": "rej-single-drops-comma-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_SINGLE_DROPS_COMMA),
        "refinement": "PARTIAL-DOMAIN: correct on every input EXCEPT the "
                      "one-element parenthesis container, where it drops the "
                      "trailing comma (emits '(' elem ')'). Its faithful real "
                      "patch keeps '(', ',)' for >=2-element tuples but special-"
                      "cases the 1-tuple to '(1)', so 'lambdify([], (1,))' returns "
                      "the int 1 and the F2P assert f2b() == (1,) FAILS, even "
                      "though every other tuple/list test still passes — does not "
                      "resolve.",
        "rationale": "If it verifies, SPEC-TOO-WEAK on exactly the gh-23224 "
                     "sub-domain. Rejection comes from the single-element clause "
                     "Implies(is_paren and len(elems)==1, Result()==PSeq(lparen())"
                     "+elems[0]+PSeq(comma(),rparen())) and the trailing-comma "
                     "clauses on that sub-domain.",
    },
    {
        "id": "rej-delim-order-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_DELIM_ORDER),
        "refinement": "SUPPORTING near-miss: the parenthesis closing delimiter is "
                      "')' ',' (reversed) rather than ',' ')'. Its faithful real "
                      "patch emits 'lambdify([], (1,))' -> '(1),' which is not a "
                      "valid one-tuple literal in the return position (and "
                      "'(3, 2),' re-parses differently), so the F2P does not "
                      "resolve. The closing two code points are 41 then 44.",
        "rationale": "If it verifies, SPEC-TOO-WEAK. Rejection comes from "
                     "Result()[-1]==rparen() (now 44) and Result()[-2]==comma() "
                     "(now 41) and Result()==rendered.",
    },
]

# No @ContractOnly axioms and no A-reference deep model that calls an external
# library callee at runtime: the only A-references (`joined`, `rendered`) are
# deep models of Python's OWN `", ".join` / string concatenation, already
# validated by axiom_check.py (G-AX) on host, and the runner mounts only the
# probe in-container. There is no repo-specific callee to fuzz. The axiom lane is
# therefore vacuous for this instance.
AXIOM_TESTS = []
