"""properties.py — PBT falsification manifest for django__django-10880.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    render_fragment(function: List[int], operands: List[int], distinct: bool)
        -> List[int]          # the rendered SQL fragment NAME(<modifier><operands>)

with the load-bearing contract

    Requires(Acc(list_pred(function), 1/2))    # read-only input
    Requires(Acc(list_pred(operands), 1/2))    # read-only input
    Ensures (Acc(list_pred(function), 1/2))
    Ensures (Acc(list_pred(operands), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (ToSeq(Result()) == fragment(ToSeq(function), ToSeq(operands), distinct))   # WHOLE pin
    Ensures (Implies(distinct, Result-slice[func+1 .. func+1+8] == kw_distinct()))       # keyword slice
    Ensures (Implies(distinct, Result[func+1+8] == sep()))                               # the SEPARATOR
    Ensures (Implies(not distinct, Result == function + "(" + operands + ")"))

What the spec actually defends, and the attacks it must survive:

  * The output pin `ToSeq(Result()) == fragment(ToSeq(function), ToSeq(operands),
    distinct)` is GROUNDED in the inputs: `fragment` is a @Pure deep model (NOT
    @ContractOnly), fully unfolded by Viper as
    `function + "(" + modifier(distinct) + operands + ")"`, and
    `modifier(True) == kw_distinct() + PSeq(sep())` (the keyword then a space).
    It is a function OF the args, not an opaque answer-key marker — there is no
    executable materialization of a @Pure PSeq into a list_pred list, so you
    cannot "echo the oracle"; the only way to make `ToSeq(result)` equal it is to
    build the list element-by-element, which IS the real render work. Case
    `pos-master-assert` confirms this (the cheapest impl satisfying the pin still
    does the work). So UNGROUNDED-ORACLE-ECHO does NOT apply here; the honest
    cheapest-impl positive control stands in for it.

  * The entire content of the gold fix is the trailing SEPARATOR after DISTINCT
    (`'DISTINCT'` -> `'DISTINCT '`). That separator lives in
    `modifier(True) == kw_distinct() + PSeq(sep())` and is pinned three ways: by
    the whole-sequence equality, by the keyword-slice clause, and explicitly by
    `Result[len(function)+1+len(kw_distinct())] == sep()`. Every uniqueness rival
    targets one of those.

  * `function` and `operands` are held read-only (1/2). The MANDATORY attack is
    FRAME MUTATION (`frame-mutate-operands`): an impl that WRITES to a read-only
    input must fail for INSUFFICIENT PERMISSION.

  * There is NO control-flow / raise / side-effect difference invisible to the
    value abstraction: render_fragment is a total pure render with a single
    return path and no exceptions, so CONTROL-FLOW-EFFECT is N/A (the value
    equality captures everything observable).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants live there
too), so `markers.same_spec` is guaranteed and a rejection comes from the
POSTCONDITION catching wrong behaviour (or the permission system), never from a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P. The axiom lane runs the REAL
percent-template substitution (`template % data`, the stdlib `%`-operator) in
Docker — exactly the operation axiom_check.py / G-AX validates.
"""
from pathlib import Path

INSTANCE = "django__django-10880"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The DISTINCT branch as written in gold: 8 keyword bytes, the separator (32),
# then the closing assert. Used as a single replaceable block.
_DISTINCT_BRANCH = (
    "    if distinct:\n"
    "        result.append(68)\n"
    "        result.append(73)\n"
    "        result.append(83)\n"
    "        result.append(84)\n"
    "        result.append(73)\n"
    "        result.append(78)\n"
    "        result.append(67)\n"
    "        result.append(84)\n"
    "        result.append(32)\n"
    "        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))\n"
    "    else:\n"
    "        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))\n"
)

# the impl head (before the NAME copy loop) — insertion point for admissibility.
_HEAD = "    result = []  # type: List[int]\n    # NAME\n    j = 0\n"

# the single separator append inside the DISTINCT branch.
_SEP_APPEND = "        result.append(32)\n"

# the tail (closing delimiter + return) — insertion point for the master assert.
_TAIL = "    result.append(41)\n    return result\n"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT: the modifier branch is REORDERED so
# the `not distinct` arm comes FIRST (`if not distinct: ... else: <keyword+sep>`).
# Semantically identical, different source; keeps BOTH gold framing asserts
# (modifier(False)/modifier(True)) so the operands-loop invariant still closes.
# If this fails to verify, the postcondition is over-fit to one branch order =>
# SPEC-TOO-STRONG.
_BRANCH_REORDER = (
    "    if not distinct:\n"
    "        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))\n"
    "    else:\n"
    "        result.append(68)\n"
    "        result.append(73)\n"
    "        result.append(83)\n"
    "        result.append(84)\n"
    "        result.append(73)\n"
    "        result.append(78)\n"
    "        result.append(67)\n"
    "        result.append(84)\n"
    "        result.append(32)\n"
    "        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))\n"
)
_POS_REORDER = _swap(_BASE, _DISTINCT_BRANCH, _BRANCH_REORDER)

# (2/5b) HONEST cheapest impl / no-echo demonstration. The most direct "echo the
# @Pure oracle" attack would be `result = <materialize fragment(...)>`. There is
# NO executable materialization of a @Pure PSeq into a list_pred list, so the
# cheapest impl satisfying the GROUNDED pin still builds the list element-by-
# element (the real work). This control asserts, AFTER the closing delimiter is
# appended (i.e. when `result` is the COMPLETE fragment) and right before the
# return, that the result it built EQUALS the spec oracle `fragment(...)`. (The
# assert must follow `result.append(41)`: before the closing paren `result` is
# only `function + "(" + modifier + operands`, which is NOT yet `fragment(...)`.)
# It is CORRECT (expect="verify"); its purpose is to show there is no wrong echo
# that verifies — the oracle is grounded in the args, not an opaque marker. (If a
# wrong echo could verify, this would instead be a SPEC-TOO-WEAK reject case;
# none exists.)
_POS_MASTER = _swap(
    _BASE, "    return result\n",
    "    Assert(ToSeq(result) == fragment(ToSeq(function), ToSeq(operands), distinct))\n"
    "    return result\n",
)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped input — function="COUNT"
# ([67,79,85,78,84]), operands="rating" ([114,97,116,105,110,103]), distinct=True
# (the exact F2P `Count(..., distinct=True)` shape) — must establish the
# precondition `Acc(list_pred(.),1/2)` (a pure read-only list_pred, no value
# restriction). If the self-call fails to verify the precondition for a normal
# input => PRECOND-TOO-STRONG. The result is discarded; the gold body that
# follows is unchanged.
_ADMISS = _swap(
    _BASE, _HEAD,
    "    pf = [67, 79, 85, 78, 84]  # type: List[int]\n"
    "    po = [114, 97, 116, 105, 110, 103]  # type: List[int]\n"
    "    Assert(Acc(list_pred(pf), 1 / 2))\n"
    "    Assert(Acc(list_pred(po), 1 / 2))\n"
    + _HEAD,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `operands` is read-only
# (1/2). This rival appends to `operands` at the impl head (a write through a 1/2
# reference) before doing the gold render. Under Acc(list_pred(operands),1/2) a
# mutation of the list_pred requires FULL permission, so it MUST fail for
# INSUFFICIENT PERMISSION (not a value mismatch). The gold body is kept verbatim
# after the write, so the rejection is attributable solely to the illegal store.
# Rejection source: the PERMISSION SYSTEM.
_RIVAL_FRAME = _swap(
    _BASE, _HEAD,
    "    operands.append(32)\n" + _HEAD,
)

# (3, primary partial-domain == the discriminating BUG) DROP THE SEPARATOR. Omit
# the `result.append(32)` after DISTINCT — exactly the pre-gold behaviour
# (`'DISTINCT'` with no trailing space; this is model_prepatch.py). Correct on the
# whole `distinct=False` sub-domain, WRONG on every `distinct=True` input. Its
# faithful real patch is the pre-patch `extra_context['distinct'] = 'DISTINCT'`,
# which renders `COUNT(DISTINCTCASE WHEN ...)` for the F2P
# `Count(Case(When(...)), distinct=True)` — a SQL syntax error — so the F2P
# `test_count_distinct_expression` FAILS; it would NOT resolve. Rejection source:
# the operands-loop invariant `ToSeq(result) == function + "(" + modifier(distinct)
# + operands.take(k)` (modifier(True) carries the separator the impl never
# appended), equivalently the separator postcondition `Result[..]==sep()` and the
# keyword-slice clause.
_RIVAL_DROP_SEP = _BASE.replace(_SEP_APPEND, "", 1)
assert _BASE.count(_SEP_APPEND) == 1, "drift: separator append not unique"

# (4, wrong-separator) Append a COMMA (44) instead of a space (32) after DISTINCT.
# The keyword is present and a delimiter follows, but it is the WRONG code point.
# Its faithful real patch (`'DISTINCT,'`) renders `COUNT(DISTINCT,CASE WHEN ...)`
# — invalid SQL — so the F2P FAILS; it would NOT resolve. Rejection source: the
# explicit separator postcondition `Result[len(function)+1+len(kw_distinct())] ==
# sep()` (sep()==32, not 44) AND the whole-sequence pin (modifier(True) ends in a
# space, not a comma).
_RIVAL_WRONG_SEP = _swap(_BASE, _SEP_APPEND, "        result.append(44)\n")

# (4b, wrong-keyword) Emit the keyword with its final 'T' (code 84) DROPPED, then
# the correct space: `DISTINC ` instead of `DISTINCT `. A delimiter is present and
# in the right relative place, but the keyword bytes are wrong. Its faithful real
# patch (`'DISTINC '`) renders `COUNT(DISTINC CASE WHEN ...)` — an invalid SQL
# keyword — so the F2P FAILS; it would NOT resolve. Rejection source: the
# keyword-slice postcondition
# `Result.take(func+1+8).drop(func+1) == kw_distinct()` (the 8th keyword byte must
# be 84) AND the whole-sequence pin. (The separator clause indexes
# `Result[func+1+8]`, which here holds the space's-displaced byte, so it is the
# keyword-slice/whole-pin that catches it.)
_RIVAL_WRONG_KW = _swap(
    _BASE,
    "        result.append(84)\n        result.append(32)\n",
    "        result.append(32)\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (modifier branch reordered, `not distinct` arm "
                  "first) but correct impl must verify; both gold framing asserts "
                  "(modifier(False)/modifier(True)) are kept so the operands-loop invariant "
                  "still closes. If it fails to verify, the spec is over-fit to one branch "
                  "order => SPEC-TOO-STRONG."},
    {"id": "pos-master-assert", "kind": "soundness", "expect": "verify",
     "module": _POS_MASTER,
     "rationale": "the cheapest impl satisfying the GROUNDED master pin still does the real "
                  "render work (no executable materialization of the @Pure oracle `fragment` "
                  "into a list_pred list exists). Asserting result == fragment(...) before "
                  "return is redundant with the gold proof and must verify. Demonstrates the "
                  "spec is NOT echo-vulnerable: there is no wrong oracle-echo that verifies "
                  "(else this would be a reject case)."},
    {"id": "admiss-fshape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the exact F2P-shaped input (function='COUNT', "
                  "operands='rating', distinct=True) must establish the precondition "
                  "Acc(list_pred(.),1/2) for both list args; if not, PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-operands", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: Django's render never mutates "
                   "the already-compiled operand text (`%(expressions)s`, a Python str — "
                   "immutable — produced by the compiler). The rival exists only to test "
                   "whether the read-only (1/2) precondition can be subverted by writing to "
                   "`operands`. No resolving patch overwrites its operand input, so a verifying "
                   "rival here would be a pure verify⇏resolve artifact (vacuous satisfaction "
                   "via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `operands.append(32)` mutates a list held "
                  "at 1/2 (read-only) permission and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (the append needs full perm), not a "
                  "value mismatch; the gold body is kept verbatim after the write. If it "
                  "verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "drop-separator", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_SEP,
     "refinement": "omits the trailing space after DISTINCT — the exact pre-gold behaviour "
                   "(`extra_context['distinct'] = 'DISTINCT'`, model_prepatch.py). Its faithful "
                   "real patch renders `COUNT(DISTINCTCASE WHEN ...)` for the F2P "
                   "`Count(Case(When(...)), distinct=True)` — a SQL syntax error — so "
                   "test_count_distinct_expression FAILS; it would NOT resolve. This is the bug "
                   "the gold patch fixes.",
     "rationale": "the discriminating bug / partial-domain on the distinct sub-domain (correct "
                  "for distinct=False, wrong for distinct=True). Rejection source: the "
                  "operands-loop invariant `ToSeq(result) == function + '(' + modifier(distinct) "
                  "+ operands.take(k)` (modifier(True) carries the separator the impl never "
                  "appends), equivalently the separator postcondition Result[..]==sep() and the "
                  "keyword-slice clause. If it verified => SPEC-TOO-WEAK (admits the bug)."},
    {"id": "wrong-separator-comma", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_SEP,
     "refinement": "uses a comma (44) as the delimiter after DISTINCT instead of a space. Its "
                   "faithful real patch (`'DISTINCT,'`) renders `COUNT(DISTINCT,CASE WHEN ...)` "
                   "— invalid SQL — so the F2P FAILS; it would NOT resolve.",
     "rationale": "targets the explicit separator postcondition "
                  "Result[len(function)+1+len(kw_distinct())] == sep() (sep()==32, not 44), and "
                  "the whole-sequence pin (modifier(True) ends in a space). If it verified => "
                  "SPEC-TOO-WEAK (the separator is unpinned to its exact code point)."},
    {"id": "wrong-keyword", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_KW,
     "refinement": "emits `DISTINC ` (final 'T' dropped) instead of `DISTINCT `. Its faithful "
                   "real patch (`'DISTINC '`) renders `COUNT(DISTINC CASE WHEN ...)` — an "
                   "invalid SQL keyword — so the F2P FAILS; it would NOT resolve.",
     "rationale": "targets the keyword-slice postcondition "
                  "Result.take(func+1+8).drop(func+1) == kw_distinct() (the keyword bytes must "
                  "be exactly DISTINCT) and the whole-sequence pin. If it verified => "
                  "SPEC-TOO-WEAK (the keyword content is unpinned)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real percent-template substitution)
# ===========================================================================
# No @ContractOnly axioms are CONSUMED (the axioms region is empty). The deep
# model `fragment`/`modifier` is an A-REFERENCE: validated equal to the REAL
# render operation `template % data` (the stdlib `%`-operator on the repository
# Aggregate template). These probes reuse axiom_check.py's logic, executing the
# real operation (never scraping source) and reading its observed values.

# (1) axiom-soundness: the deep model `fragment` must equal the REAL
# `template % data` over boundary + heavy fuzz in BOTH modes, AND the separation
# guarantee must hold (when distinct, the code point right after DISTINCT is a
# space) under the post-gold modifier value 'DISTINCT '. apply_gold=True so the
# probe describes post-gold behaviour (it pins the modifier value directly, so it
# does not actually need the repo, but we keep apply_gold for fidelity). The
# `%`-operator is stdlib; nothing repo-specific is imported.
_AX_FRAGMENT_SOUND = r'''
import random, sys
# The repository Aggregate template (expressions.py Func.template overridden in
# aggregates.py): '%(function)s(%(distinct)s%(expressions)s)'.
TEMPLATE = "%(function)s(%(distinct)s%(expressions)s)"
KW = [ord(c) for c in "DISTINCT"]   # [68,73,83,84,73,78,67,84]
SEP = 32
def modifier(d):
    return KW + [SEP] if d else []
def deep_model(fn, op, d):                       # model.py `fragment`
    return fn + [40] + modifier(d) + op + [41]
def real_render(fn_s, op_s, d):                  # the REAL operation
    return TEMPLATE % {"function": fn_s,
                       "distinct": "DISTINCT " if d else "",
                       "expressions": op_s}
def check(fn_s, op_s, d):
    observed = [ord(c) for c in real_render(fn_s, op_s, d)]
    expected = deep_model([ord(c) for c in fn_s], [ord(c) for c in op_s], d)
    assert observed == expected, ("A-REFERENCE-UNSOUND fragment != template %% data on "
        "fn=%r op=%r distinct=%r: real=%r model=%r" % (fn_s, op_s, d, observed, expected))
    if d:
        base = len(fn_s) + 1                      # past NAME + '('
        assert observed[base:base + len(KW)] == KW, ("keyword absent after '(' on %r/%r" % (fn_s, op_s))
        assert observed[base + len(KW)] == SEP, ("DISTINCT not followed by a space on "
            "fn=%r op=%r — it would fuse with the operands" % (fn_s, op_s))
bad = 0
functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "", "F"]
operands = ["", "CASE WHEN pages > 300 THEN rating END", "rating", "*",
            "publisher_id", "a, b, c", "T1.col", "x"]
boundary = [(f, o) for f in functions for o in operands]
for f, o in boundary:
    check(f, o, True); check(f, o, False)
rng = random.Random(10880)
alphabet = [chr(c) for c in range(33, 127)] + [" ", "\t"]
for _ in range(20000):
    f = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
    o = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 32)))
    check(f, o, rng.random() < 0.5)
# the F2P witness must read 'COUNT(DISTINCT CASE...', never 'DISTINCTCASE'.
w = real_render("COUNT", "CASE WHEN pages > 300 THEN rating END", True)
assert w.startswith("COUNT(DISTINCT CASE"), w
assert "DISTINCTCASE" not in w, w
print("AXIOM-SOUND: deep model `fragment` == real template substitution on",
      len(boundary), "boundary + 20000 fuzz (both modes); separation guarantee holds.")
sys.exit(0)
'''

# (2) axiom-containment: every callee-input the MODEL can reach lies in the REAL
# operation's domain. The model reaches `template % data` with the three named
# fields function/distinct/expressions where distinct ∈ {'DISTINCT ', ''} (the
# only two values modifier produces) and function/expressions are arbitrary code-
# point strings. The real operation `template % data` is total over ANY str values
# for the three named keys (the template names exactly those three fields, in the
# fixed order, with two literal parens). So the model's reachable inputs are a
# subset of the callee's domain — covering MORE (any str) is sound. The probe
# confirms: (a) the template references EXACTLY {function, distinct, expressions};
# (b) the substitution succeeds (no KeyError / no extra unfilled field) for both
# reachable distinct values across a spread of function/expressions; (c) the two
# distinct values are exactly the ones modifier(True/False) produce.
_AX_CONTAINMENT = r'''
import re, sys
TEMPLATE = "%(function)s(%(distinct)s%(expressions)s)"
# (a) the template's named fields, in order.
fields = re.findall(r"%\((\w+)\)s", TEMPLATE)
assert fields == ["function", "distinct", "expressions"], fields
# (b)/(c) the only modifier values the model can produce.
reachable_distinct = {"DISTINCT ", ""}   # modifier(True), modifier(False)
funcs = ["COUNT", "", "SUM", "A_VERY_LONG_FUNCTION_NAME"]
exprs = ["", "rating", "CASE WHEN pages > 300 THEN rating END", "*", "a, b, c"]
for d in reachable_distinct:
    for f in funcs:
        for e in exprs:
            # substitution must succeed for every reachable (function, distinct,
            # expressions) triple - i.e. each reachable callee-input is IN domain.
            data = {"function": f, "distinct": d, "expressions": e}
            out = TEMPLATE % data            # raises if any reachable input is out of domain
            assert out == f + "(" + d + e + ")", (out, f, d, e)
# a reachable input outside the callee domain would have raised above; none does.
print("CONTAINMENT OK: template names exactly", fields,
      "; both reachable distinct values", sorted(reachable_distinct),
      "substitute for every probed (function, expressions); model-reachable is a subset of callee domain.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-fragment-ref-sound", "axiom": "fragment", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_FRAGMENT_SOUND,
     "rationale": "the A-reference deep model `fragment`/`modifier` must equal the REAL "
                  "percent-template substitution `template % data` (the stdlib %-operator on "
                  "the repository Aggregate template, post-gold modifier value 'DISTINCT ') "
                  "over boundary + 20000 fuzz in both modes, and the separation guarantee must "
                  "hold (the code point after DISTINCT is a space). Any mismatch => AXIOM-UNSOUND "
                  "(deep model unsound). Executes the real operation; never scrapes source."},
    {"id": "ax-containment", "axiom": "fragment", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (the three named template fields with "
                  "distinct ∈ {'DISTINCT ', ''} and arbitrary function/expressions strings) lies "
                  "in the real substitution's domain (the template names exactly those three "
                  "fields and is total over any str). A reachable input outside that domain => "
                  "AXIOM-TOO-WEAK-FOR-CALLER; covering more (any str) is sound."},
]
