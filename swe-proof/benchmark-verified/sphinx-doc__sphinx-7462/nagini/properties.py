# properties.py — PBT falsification battery for sphinx-doc__sphinx-7462.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# a # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec. There are TWO impl regions (one per modeled function), and
# each is edited in isolation by a unique _swap.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   tuple_tokens(elts: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]   (site A, token surface)
#   tuple_text(elts: PSeq[PSeq[int]]) -> PSeq[int]           (site B, text surface)
#   Both render a parsed comma-separated member group. No precondition (a group
#   may have zero or more members). Each is pinned by TWO postcondition clauses:
#     NON-EMPTY  Implies(len(elts) > 0, Result() == join_tokens(elts))   [A]
#                Implies(len(elts) > 0, Result() == join_comma(elts))    [B]
#     EMPTY      Implies(len(elts) == 0, Result() == PSeq(open_paren(), close_paren()))  [A]
#                Implies(len(elts) == 0, Result() == PSeq(40, 41))                       [B]
#   The EMPTY clause is the discriminating fix (the empty-tuple `Tuple[()]` case
#   that crashed with IndexError pre-patch). join_tokens/join_comma are GROUNDED
#   @Pure front-recursive folds over the input `elts` (fully unfoldable, NOT an
#   opaque answer-key oracle) — see 'assessment' re ungrounded-oracle echo.
#
#   READ-ONLY INPUT / FRAME-MUTATION: `elts` is a plain PSeq VALUE parameter, an
#   immutable mathematical Viper sequence carrying NO Acc(...) heap permission —
#   there is no half-permission heap object to overwrite, so the fractional-
#   permission frame-mutation attack does not apply here (and is not constructible).
#   See 'assessment'. The analogue here is the partial-domain regression on the
#   empty sub-domain, which IS attacked (the prepatch rivals + wrong-render rivals).
#
# F2P:
#   tests/test_domain_py.py::test_parse_annotation  — adds `Tuple[()]` asserting
#     the token surface emits TWO separate desc_sig_punctuation nodes '(' then ')'.
#   tests/test_pycode_ast.py::test_unparse[()-()]   — adds `()` -> `"()"` on the
#     text surface.
# Pre-patch: site A did result.pop() on [] -> IndexError; site B returned
#   ", ".join(()) == "".  Both prepatch models (model_prepatch.py / _2.py) fail
#   exactly the EMPTY clause (G-DIFF) — the reject rivals re-express those holes.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7462"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two frozen impl blocks (textually distinct: helper name + empty render).
# Every rival edits ONLY one of these, in isolation.
# ---------------------------------------------------------------------------
_IMPL_A = """    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    else:
        result = PSeq(open_paren(), close_paren())
    return result"""

_IMPL_B = """    if len(elts) > 0:
        result = join_comma(elts)  # type: PSeq[int]
    else:
        result = PSeq(40, 41)
    return result"""


# === POSITIVE CONTROL (soundness) =========================================
# Branch-reorder: handle the EMPTY case FIRST, fall through to the non-empty
# return last. Same executable meaning; the front-recursive fold call is kept
# verbatim (no loop-direction flip, no f(a+b) lemma needed — directive-3 safe).
# A correct, structurally-different impl MUST verify, else SPEC-TOO-STRONG.
# Both sites are reordered in the one positive-control module.
_POS_A = """    if len(elts) == 0:
        result = PSeq(open_paren(), close_paren())  # type: PSeq[PSeq[int]]
    else:
        result = join_tokens(elts)
    return result"""

_POS_B = """    if len(elts) == 0:
        result = PSeq(40, 41)  # type: PSeq[int]
    else:
        result = join_comma(elts)
    return result"""

POS_REORDER = _swap(_swap(_BASE, _IMPL_A, _POS_A), _IMPL_B, _POS_B)


# === ADMISSIBILITY ========================================================
# No precondition is declared ("a group may have zero or more members"), so a
# call site cannot fail to establish a Requires. The risk a too-strong PRECOND
# poses is therefore re-expressed as: both the empty AND a representative
# non-empty F2P-shaped input must flow through the impl without contradiction.
# We assert (inside the impl region, before any gold obligation) that the
# representative shapes are well-formed values the contract admits. If the block
# cannot verify, an F2P-shaped input is not admissible -> PRECOND-TOO-STRONG.
# (A self-recursive call would need a Decreases the spec doesn't carry — proof
#  gap, not spec defect — so we exercise the value shapes directly instead.)
_ADMISS_A = """    # ADMISSIBILITY PROBE (site A): representative F2P-shaped inputs are
    # well-formed values the no-precondition contract admits — the empty group
    # and a two-member group ("int","int").
    empty_a = PSeq()  # type: PSeq[PSeq[int]]
    Assert(len(empty_a) == 0)
    two_a = PSeq(PSeq(105, 110, 116), PSeq(105, 110, 116))  # type: PSeq[PSeq[int]]
    Assert(len(two_a) == 2)
    Assert(two_a[0] == PSeq(105, 110, 116))
    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    else:
        result = PSeq(open_paren(), close_paren())
    return result"""

ADMISS = _swap(_BASE, _IMPL_A, _ADMISS_A)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 (site A) PRE-PATCH regression: drop the empty special-case and assemble
# unconditionally (return join_tokens(elts)). Correct on every NON-EMPTY group;
# DIVERGES only on the empty sub-domain, where join_tokens([]) is the empty token
# sequence (the abstract image of `result.pop()` on [] — the IndexError crash).
# This is exactly model_prepatch.py.
# refinement: the faithful real patch is the literal pre-patch code
# `for elem in node.elts: ...; result.append(', ')  ; result.pop()` with NO
# `if node.elts:` guard. On `Tuple[()]` it executes result.pop() on the empty
# list and raises IndexError (the crash in the bug report); F2P
# test_parse_annotation would error, not emit '(' ')' — it does NOT resolve.
# rejection source: Ensures(Implies(len(elts)==0, Result()==PSeq(open_paren(),
# close_paren()))) — the empty clause; the empty token sequence != ('(' ')').
_W1_PREPATCH_A = """    result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    return result"""

W1_PREPATCH_TOK = _swap(_BASE, _IMPL_A, _W1_PREPATCH_A)


# --- W2 (site B) PRE-PATCH regression: drop the empty special-case and join
# unconditionally (return join_comma(elts)). Correct on every NON-EMPTY group;
# DIVERGES only on the empty sub-domain, where join_comma([]) is "" not "()".
# This is exactly model_prepatch_2.py.
# refinement: the faithful real patch is the literal pre-patch
# `return ", ".join(unparse(e) for e in node.elts)` with NO `if node.elts:`
# guard. On `()` it returns ", ".join(()) == "" not "()"; F2P
# test_unparse[()-()] asserts "()" — it gets "" and does NOT resolve.
# rejection source: Ensures(Implies(len(elts)==0, Result()==PSeq(40,41))) — the
# empty clause; "" (the empty PSeq) != PSeq(40,41).
_W2_PREPATCH_B = """    result = join_comma(elts)  # type: PSeq[int]
    return result"""

W2_PREPATCH_TXT = _swap(_BASE, _IMPL_B, _W2_PREPATCH_B)


# --- W3 (site A) WRONG empty rendering, ONE token: render the empty group as a
# SINGLE token whose text is "()" (PSeq(40,41)) rather than the TWO separate
# tokens '(' ')'. Correct on every non-empty group; wrong only on empty, and
# wrong in a way the value abstraction of the token surface specifically defends:
# the count and identity of the punctuation tokens.
# refinement: a real patch writing `result = [desc_sig_punctuation('', '()')]`
# (one punctuation node carrying "()") instead of two separate '(' and ')'
# nodes. F2P test_parse_annotation's assert_node expects exactly two
# desc_sig_punctuation nodes, '(' then ')' (positionally, by text), inside the
# Tuple[...] brackets; one combined node fails assert_node — it does NOT resolve.
# rejection source: empty clause Result()==PSeq(open_paren(), close_paren());
# a length-1 token sequence != the length-2 ('(' ')') token sequence.
_W3_WRONGTOK_A = """    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    else:
        result = PSeq(PSeq(40, 41))
    return result"""

W3_WRONGTOK = _swap(_BASE, _IMPL_A, _W3_WRONGTOK_A)


# --- W4 (site A) WRONG empty rendering, SWAPPED order: render the empty group as
# the two tokens ')' '(' (close then open) instead of '(' ')'. Correct on every
# non-empty group; wrong only on empty, in token ORDER.
# refinement: a real patch writing `result = [desc_sig_punctuation('', ')'),
# desc_sig_punctuation('', '(')]` would emit the brackets reversed; F2P
# test_parse_annotation asserts '(' BEFORE ')' positionally — reversed order
# fails assert_node, does NOT resolve.
# rejection source: empty clause Result()==PSeq(open_paren(), close_paren());
# PSeq(close_paren(), open_paren()) is element-wise reversed and != it.
_W4_SWAPTOK_A = """    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    else:
        result = PSeq(close_paren(), open_paren())
    return result"""

W4_SWAPTOK = _swap(_BASE, _IMPL_A, _W4_SWAPTOK_A)


# --- W5 (site B) WRONG empty rendering, ONE char: render the empty group as the
# single character '(' (PSeq(40)) instead of "()" (PSeq(40,41)). Correct on every
# non-empty group; wrong only on empty by a missing ')'.
# refinement: a real patch writing `else: return "("` would produce malformed
# output for an empty tuple annotation; F2P test_unparse[()-()] asserts exactly
# "()" — it gets "(" and does NOT resolve.
# rejection source: empty clause Result()==PSeq(40,41); PSeq(40) (length 1) != it.
_W5_WRONGTXT_B = """    if len(elts) > 0:
        result = join_comma(elts)  # type: PSeq[int]
    else:
        result = PSeq(40)
    return result"""

W5_WRONGTXT = _swap(_BASE, _IMPL_B, _W5_WRONGTXT_B)


# --- W6 (site B) SWAPPED-char empty rendering: render the empty group as ")("
# (PSeq(41, 40)) instead of "()" (PSeq(40,41)). Correct on every non-empty group;
# wrong only on empty, in character ORDER.
# refinement: a real patch writing `else: return ")("` emits a reversed bracket
# pair for an empty tuple; F2P test_unparse[()-()] asserts "()" exactly — it gets
# ")(" and does NOT resolve.
# rejection source: empty clause Result()==PSeq(40,41); PSeq(41,40) != it.
_W6_SWAPTXT_B = """    if len(elts) > 0:
        result = join_comma(elts)  # type: PSeq[int]
    else:
        result = PSeq(41, 40)
    return result"""

W6_SWAPTXT = _swap(_BASE, _IMPL_B, _W6_SWAPTXT_B)


# --- W7 (site A) UNIVERSAL empty rendering for ALL groups: always emit the two
# tokens '(' ')' regardless of members. Correct on the empty sub-domain; DIVERGES
# on every NON-EMPTY group (drops the members entirely). This attacks the
# NON-EMPTY clause from the opposite side of the prepatch rivals.
# refinement: a real patch unconditionally writing `result = [
# desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]` would render
# every tuple annotation as a bare '(' ')' losing all members; the P2P
# test_unparse[Tuple[int, ...]] and the existing parse_annotation cases assert
# the member tokens — it does NOT resolve.
# rejection source: non-empty clause Result()==join_tokens(elts); a fixed
# 2-token output != the member interleaving for any non-empty group.
_W7_ALWAYSEMPTY_A = """    empty = PSeq(open_paren(), close_paren())  # type: PSeq[PSeq[int]]
    return empty"""

W7_ALWAYSEMPTY_TOK = _swap(_BASE, _IMPL_A, _W7_ALWAYSEMPTY_A)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl at BOTH sites (empty "
        "branch handled FIRST, non-empty return last); the front-recursive fold "
        "call is kept verbatim so no auto-undischargeable lemma is needed "
        "(directive-3 safe). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "no precondition is declared; the probe (inside impl-start, "
        "before any gold obligation) builds the empty group and a two-member "
        '("int","int") F2P-shaped group and asserts they are well-formed values '
        "the contract admits. If it cannot verify, a normal input is inadmissible "
        "-> PRECOND-TOO-STRONG.",
    },
    {
        "id": "w1-prepatch-tok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_PREPATCH_TOK,
        "refinement": "the faithful real patch is the literal pre-patch token loop "
        "with NO `if node.elts:` guard (`for elem in node.elts: ...; "
        "result.append(', '); result.pop()`). On Tuple[()] it does result.pop() on "
        "the empty list and raises IndexError (the crash in the bug report); F2P "
        "test_parse_annotation errors instead of emitting '(' ')' — does NOT resolve.",
        "rationale": "rejected by the EMPTY clause Implies(len(elts)==0, "
        "Result()==PSeq(open_paren(),close_paren())): join_tokens([]) is the empty "
        "token sequence, != ('(' ')'). Partial-domain (empty sub-domain). This is "
        "model_prepatch.py re-expressed in the impl region.",
    },
    {
        "id": "w2-prepatch-txt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_PREPATCH_TXT,
        "refinement": "the faithful real patch is the literal pre-patch "
        '`return ", ".join(unparse(e) for e in node.elts)` with NO `if node.elts:` '
        'guard. On `()` it returns ", ".join(()) == "" not "()"; F2P '
        "test_unparse[()-()] asserts \"()\" — gets \"\" and does NOT resolve.",
        "rationale": "rejected by the EMPTY clause Implies(len(elts)==0, "
        "Result()==PSeq(40,41)): join_comma([]) is the empty PSeq, != PSeq(40,41). "
        "Partial-domain (empty sub-domain). This is model_prepatch_2.py re-expressed.",
    },
    {
        "id": "w3-wrongtok-one-node",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_WRONGTOK,
        "refinement": "a real patch writing `result = [desc_sig_punctuation('', "
        "'()')]` (ONE punctuation node carrying the text '()') instead of two "
        "separate '(' and ')' nodes. F2P test_parse_annotation's assert_node expects "
        "exactly TWO desc_sig_punctuation nodes ('(' then ')') positionally; one "
        "combined node fails assert_node — does NOT resolve.",
        "rationale": "rejected by the EMPTY clause Result()==PSeq(open_paren(), "
        "close_paren()): a length-1 token sequence PSeq(PSeq(40,41)) != the length-2 "
        "('(' ')') token sequence. Defends the token COUNT/identity the F2P checks.",
    },
    {
        "id": "w4-swaptok-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_SWAPTOK,
        "refinement": "a real patch writing the bracket nodes reversed (`[..., "
        "')'-node, '('-node]`). F2P test_parse_annotation asserts '(' BEFORE ')' "
        "positionally; reversed order fails assert_node — does NOT resolve.",
        "rationale": "rejected by the EMPTY clause Result()==PSeq(open_paren(), "
        "close_paren()): PSeq(close_paren(), open_paren()) is element-wise reversed "
        "and != it. Value-level order defense on the empty sub-domain.",
    },
    {
        "id": "w5-wrongtxt-one-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_WRONGTXT,
        "refinement": "a real patch writing `else: return \"(\"` produces malformed "
        "output for an empty tuple annotation; F2P test_unparse[()-()] asserts "
        'exactly "()" — gets "(" and does NOT resolve.',
        "rationale": "rejected by the EMPTY clause Result()==PSeq(40,41): PSeq(40) "
        "(length 1) != it. Partial-domain (empty sub-domain), missing ')'.",
    },
    {
        "id": "w6-swaptxt-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W6_SWAPTXT,
        "refinement": "a real patch writing `else: return \")(\"` emits a reversed "
        "bracket pair for an empty tuple; F2P test_unparse[()-()] asserts \"()\" "
        "exactly — gets \")(\" and does NOT resolve.",
        "rationale": "rejected by the EMPTY clause Result()==PSeq(40,41): PSeq(41,40) "
        "!= it. Value-level char-order defense on the empty sub-domain.",
    },
    {
        "id": "w7-always-empty-tok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W7_ALWAYSEMPTY_TOK,
        "refinement": "a real patch unconditionally writing `result = ["
        "desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]` (no member "
        "loop) renders every tuple annotation as a bare '(' ')', dropping all "
        "members; the existing test_parse_annotation / test_unparse[Tuple[...]] "
        "cases assert the member tokens — does NOT resolve.",
        "rationale": "rejected by the NON-EMPTY clause Implies(len(elts)>0, "
        "Result()==join_tokens(elts)): a fixed 2-token output != the member "
        "interleaving for any non-empty group. Partial-domain attacking the "
        "non-empty sub-domain (the opposite side of the prepatch rivals).",
    },
]


# No @ContractOnly axioms are consumed (meta.json axioms == []). The two member-
# joining operations are A-reference DEEP MODELS (join_tokens, join_comma),
# already validated == their real callees (the upstream token loop / ', '.join)
# by axiom_check.py / G-AX on 8 boundary + 30000 fuzz non-empty inputs, with the
# empty-group discrimination proven at both sites. The G-AX check is the standing
# soundness/containment guarantee for those deep models; there is no @ContractOnly
# Requires-domain to fuzz here (the folds are total over PSeq[PSeq[int]] and the
# model reaches them only on the non-empty branch, exactly the validated domain).
# Nothing additional for the axiom lane to run.
AXIOM_TESTS = []
