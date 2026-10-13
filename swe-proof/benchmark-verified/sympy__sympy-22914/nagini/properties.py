"""properties.py — PBT falsification battery for sympy__sympy-22914.

NOT a Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
executes and stamps with RESULT.

Defended surface (read model.py):
  print_function_call(name_code: int, joined_args: List[int],
                      fallback: List[int]) -> List[int]
  Requires: 0 <= name_code <= 3 ; Acc(list_pred(joined_args), 1/2) [READ-ONLY]
            Acc(list_pred(fallback), 1/2)                          [READ-ONLY]
  Ensures:
    (E0) Acc(list_pred(joined_args), 1/2)           frame: input returned intact
    (E0b) Acc(list_pred(fallback), 1/2)             frame: fallback intact
    (E1) Acc(list_pred(Result()))                   full perm on a fresh result
    (E2) is_supported(nc)  -> Result == call_render(nc, joined_args)   [supported pinned exactly]
    (E3) nc == name_min()  -> Result == 'min(' joined_args ')'
    (E4) nc == name_max()  -> Result == 'max(' joined_args ')'
    (E5) !is_supported(nc) -> Result == fallback    [unsupported pinned exactly:
         the unchanged machinery's output is returned verbatim — nothing but
         the supported-call emission may change]

Oracle grounding: call_render / target_name / is_supported are @Pure functions of
the ACTUAL args (name_code, joined_args), fully unfolded.  So the supported-case
oracle (E2) is GROUNDED in the inputs — echoing call_render(name_code, joined_args)
IS the correct answer, there is no "wrong echo" to build.  The unsupported case is
now pinned EXACTLY: the result must equal the read-only `fallback` input (the
unchanged surrounding machinery's output), so no rival can smuggle divergent
behaviour into the unsupported path (the earlier "not any supported call form"
under-constraint that G-PANEL-1 exploited is gone).  The genuine attack surface is
the DOMAIN PARTITION on name_code {abs=0, min=1, max=2, other=3}: each supported
code is pinned by E2/E3/E4 and the unsupported code by E5; an impl correct on a
subset but diverging on one name code must be rejected.

Axiom lane: the axioms region is EMPTY (no @ContractOnly).  The changed operation
(extending the supported table) is an A-reference deep model (is_supported /
target_name / call_render) validated == the real PythonCodePrinter by
axiom_check.py / G-AX.  The axiom-lane probes re-run that real-callee check
(soundness + caller-domain containment), reusing axiom_check.py embedded at
host load time (it is NOT mounted in-container).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22914"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region of model.py (everything between # impl-start / impl-end,
# the markers themselves excluded).  Every rival is built by _swap-ing this exact
# block, so same_spec is GUARANTEED (the spec view elides the impl region).
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # Mirror the printer dispatch: a supported function identity renders as a
    # call; everything else is emitted exactly as the unchanged surrounding
    # machinery emits it (its pre-rendered output `fallback`).
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    # An unsupported function keeps the unchanged machinery's rendering: return
    # (a fresh copy of) its pre-rendered output, unaltered.
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _impl(new_body: str) -> str:
    """Return the full model source with the gold impl block replaced by new_body
    (which must be the executable body that sits between the impl markers)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# === positive controls (soundness / admissibility): MUST verify ============

# pos-control-1: structurally-different but CORRECT.  Invert the dispatch — test
# the UNSUPPORTED predicate first and return the fallback copy, then handle the
# supported codes via a different (flat) name selection.  Keeps every value the
# gold proof needs; only the executable shape changes (branch reorder + flat
# if-chain instead of nested if/elif/else).  No induction lemma needed: result is
# still nm + [40] + joined_args + [41], matching call_render's PSeq '+' per element.
_POS1 = """    # Structurally different, behaviourally identical: handle the unsupported
    # identity FIRST, then pick the target name with a flat if-chain.
    if not (name_code == 0 or name_code == 1 or name_code == 2):
        empty = []  # type: List[int]
        out = empty + fallback  # type: List[int]
        return out
    nm = []  # type: List[int]
    if name_code == 1:
        nm = [109, 105, 110]
    if name_code == 2:
        nm = [109, 97, 120]
    if name_code == 0:
        nm = [97, 98, 115]
    result = nm + [40] + joined_args + [41]  # type: List[int]
    return result"""

# admiss-1: an in-region admissibility witness.  The impl asserts the
# precondition is satisfiable for an F2P-shaped input (name_code == name_min(),
# a non-trivial joined_args), then runs the gold logic so the postcondition still
# holds.  If the Requires rejected a normal input this assert/verify would fail
# => PRECOND-TOO-STRONG.
_ADMISS1 = """    # admissibility witness: name_min() (==1) is in the declared name_code domain
    # 0..3, and is_supported(name_min()) holds, so the supported branch is
    # reachable for a normal F2P-shaped input.  (F2P: doprint(Min(x, y)).)
    Assert(0 <= name_min() and name_min() <= 3)
    Assert(is_supported(name_min()))
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""


# === uniqueness / completeness (wrong impls): MUST be rejected =============

# weak-frame-mutate: FRAME-MUTATION (MANDATORY — joined_args is Acc(...,1/2)).
# A rival that WRITES to the read-only joined_args before reading it.  It keeps
# the gold value computation verbatim, so any rejection is attributable purely to
# the write: only Acc(...,1/2) (read) permission is held, so the .append fails for
# INSUFFICIENT PERMISSION.  Refinement: the real stringify(expr.args, ", ")
# produces the comma-joined argument text; the gold patch never mutates that
# sub-computation.  An impl that appends a code point to joined_args would render
# e.g. "min(x, y\x07)" — corrupting the printed arguments — and FAIL the F2P
# assert prntr.doprint(Min(x, y)) == "min(x, y)".
_FRAME = """    # ADVERSARIAL: mutate the read-only input (held at 1/2 permission).
    joined_args.append(7)
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""

# weak-drop-max: PARTIAL-DOMAIN.  Correct on abs(0), min(1) and unsupported(3),
# but treats max(2) as unsupported and returns the fallback copy for it.  Must
# fail clause E2 (is_supported(2) -> Result == call_render(2, ...)) AND E4 (the
# explicit name_max() clause).  Refinement: the real patch adds BOTH 'Min':'min'
# and 'Max':'max'; an impl missing 'Max' renders Max(x, y) via the Piecewise
# rewrite (a non-call form), not "max(x, y)" — FAILS the F2P
# assert prntr.doprint(Max(x, y)) == "max(x, y)".
_DROP_MAX = """    # ADVERSARIAL: only abs and min are supported; max falls through.
    if name_code == 0 or name_code == 1:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        else:
            nm = [109, 105, 110]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""

# weak-swap-minmax: PARTIAL-DOMAIN / value-level.  Supported set is exactly
# {0,1,2} (so is_supported is honoured and the unsupported clause is vacuous),
# but the min/max TARGET NAMES are swapped: min -> 'max', max -> 'min'.  Must fail
# E3 (name_min -> 'min(...') because it renders 'max(...'), and symmetrically E4.
# Refinement: a real printer that mapped 'Min' to 'max' would render
# doprint(Min(x, y)) == "max(x, y)" — FAILS the F2P assert ... == "min(x, y)".
_SWAP = """    # ADVERSARIAL: min and max target names swapped.
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 97, 120]
        else:
            nm = [109, 105, 110]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""

# weak-abs-wrong-name: PARTIAL-DOMAIN on the single pre-existing supported code.
# min/max/unsupported all correct, but abs(0) renders with the WRONG target name
# 'ans' ([97,110,115]) instead of 'abs' ([97,98,115]).  Must fail E2 for nc==0:
# Result == call_render(0, ...) requires the literal 'abs(' prefix.  Refinement:
# this would render doprint(Abs(x)) == "ans(x)", breaking the long-standing
# Abs->abs behavior the P2P suite (and table) relies on; not a faithful patch.
_ABS_WRONG = """    # ADVERSARIAL: abs renders as 'ans(' instead of 'abs('.
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 110, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out"""

# weak-unsupported-diverge: UNSUPPORTED-PATH DIVERGENCE — exactly the class of
# rival the pre-repair spec ADMITTED (its unsupported clause only forbade the
# three supported call forms, so any other divergent text slipped through; that
# was the G-PANEL-1 finding).  This rival returns '#'-prefixed text
# ([35] + joined_args) instead of the machinery's `fallback`.  Must now fail E5:
# !is_supported(3) -> Result == fallback.  Refinement: the gold patch changes
# ONLY the supported table; any impl that alters what an unsupported identity
# prints diverges from the real unchanged fallback machinery (e.g. the Piecewise
# rewrite text) and is not a faithful patch — it would mis-print unknown
# functions while still passing the old under-constrained clause.
_UNSUP_DIVERGE = """    # ADVERSARIAL: the unsupported path emits '#'-prefixed text instead of the
    # unchanged machinery's fallback output.
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    diverged = [35] + joined_args  # type: List[int]
    return diverged"""

# weak-unsupported-as-min: the unsupported case (nc==3) rendered AS the min call
# form.  Must fail E5: !is_supported(3) -> Result == fallback (the min call form
# built from joined_args is not the machinery's fallback text in general).
# Refinement: rendering an arbitrary unsupported f(x) as "min(x)" is a wrong
# printer — an unsupported identity must NOT collapse to a supported target's
# call; not a faithful patch and would mis-print every unknown function.
_UNSUP_MIN = """    # ADVERSARIAL: the unsupported fallback is rendered as the 'min(' call form.
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    forged = [109, 105, 110] + [40] + joined_args + [41]  # type: List[int]
    return forged"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS1),
        "rationale": "A structurally-different but behaviourally-identical impl "
                     "(unsupported-first dispatch + flat if-chain name selection) "
                     "must verify against E2/E3/E4/E5. Only the executable shape "
                     "changes; the supported result is still nm + [40] + "
                     "joined_args + [41] matching call_render's PSeq concatenation "
                     "and the unsupported result is a fresh copy of fallback, so "
                     "no induction lemma is needed. If this fails => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-min",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS1),
        "rationale": "Asserts 0<=name_min()<=3 and is_supported(name_min()) inside "
                     "the impl, witnessing that the precondition admits a normal "
                     "F2P-shaped input (doprint(Min(x, y))). The gold logic still "
                     "runs so the postcondition holds. If the Requires rejected "
                     "this => PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-frame-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME),
        "refinement": "The real stringify(expr.args, ', ') produces the "
                      "comma-joined argument text as a fresh string; the gold "
                      "patch (adding two table keys) never mutates that "
                      "sub-computation. An impl that appends to joined_args would "
                      "render e.g. 'min(x, y\\x07)', corrupting the printed "
                      "arguments, and FAIL the F2P assert doprint(Min(x, y)) == "
                      "'min(x, y)'. So a verifying mutator is verify-without-resolve.",
        "rationale": "FRAME-MUTATION. joined_args is held at Acc(list_pred(.),1/2) "
                     "(read-only). The .append requires WRITE permission the caller "
                     "does not grant => rejected for INSUFFICIENT PERMISSION "
                     "(precondition Requires(Acc(...,1/2)) / permission system). "
                     "Gold value computation kept verbatim so the rejection is "
                     "attributable solely to the write.",
    },
    {
        "id": "weak-drop-max",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_MAX),
        "refinement": "The gold patch adds BOTH 'Min':'min' and 'Max':'max'. An "
                      "impl that supports only abs/min renders Max(x, y) via the "
                      "_rewriteable_functions Piecewise branch (a non-call form), "
                      "NOT 'max(x, y)', so it FAILS the F2P assert "
                      "doprint(Max(x, y)) == 'max(x, y)'. A faithful real patch "
                      "would not resolve.",
        "rationale": "PARTIAL-DOMAIN. For name_code==2, is_supported(2) is True "
                     "(frozen spec) so postcondition E2 demands Result == "
                     "call_render(2, joined_args) and E4 demands the 'max(' form; "
                     "returning the fallback copy violates both => reject.",
    },
    {
        "id": "weak-swap-minmax",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP),
        "refinement": "A real table mapping 'Min'->'max' (and vice versa) would "
                      "render doprint(Min(x, y)) == 'max(x, y)', FAILING the F2P "
                      "assert doprint(Min(x, y)) == 'min(x, y)'. Not a faithful patch.",
        "rationale": "PARTIAL-DOMAIN / value-level. is_supported is honoured, but "
                     "the explicit clauses E3 (name_min -> 'min(' prefix) and E4 "
                     "(name_max -> 'max(' prefix) pin the target names; swapping "
                     "them yields ToSeq(Result()) starting 'max(' for name_min => "
                     "E3 fails => reject.",
    },
    {
        "id": "weak-abs-wrong-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABS_WRONG),
        "refinement": "Rendering Abs(x) as 'ans(x)' instead of 'abs(x)' breaks the "
                      "long-standing Abs->abs behavior the table and the existing "
                      "test suite depend on (P2P), and is not the gold edit (which "
                      "leaves 'Abs':'abs' untouched). Not a faithful patch.",
        "rationale": "PARTIAL-DOMAIN on the pre-existing supported code. For "
                     "name_code==0, postcondition E2 demands Result == "
                     "call_render(0, joined_args) whose target_name(0) is "
                     "PSeq(97,98,115) ('abs'); emitting [97,110,115] ('ans') makes "
                     "ToSeq(Result()) != call_render(0, ...) => E2 fails => reject.",
    },
    {
        "id": "weak-unsupported-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNSUP_DIVERGE),
        "refinement": "The gold patch changes ONLY the supported table. An impl "
                      "that alters what an unsupported identity prints (here "
                      "'#'-prefixed text instead of the unchanged machinery's "
                      "output) diverges from the real fallback (Piecewise rewrite "
                      "/ not-supported text) and would mis-print every unknown "
                      "function. Not a faithful patch. This is EXACTLY the rival "
                      "class the pre-repair spec admitted (the G-PANEL-1 finding).",
        "rationale": "UNSUPPORTED-PATH PINNED. For name_code==3, is_supported is "
                     "False, so postcondition E5 demands ToSeq(Result()) == "
                     "ToSeq(fallback); emitting [35]+joined_args differs from an "
                     "arbitrary fallback => E5 fails => reject.",
    },
    {
        "id": "weak-unsupported-as-min",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNSUP_MIN),
        "refinement": "Rendering an unsupported identity f(x) as 'min(x)' is a "
                      "wrong printer: an unknown function must not collapse to a "
                      "supported target's call form. The gold patch leaves the "
                      "unsupported path as the Piecewise/not-supported fallback; "
                      "this rival would mis-print every unknown function. Not faithful.",
        "rationale": "For name_code==3, is_supported is False, so postcondition E5 "
                     "demands ToSeq(Result()) == ToSeq(fallback); emitting the "
                     "forged min-call form differs from an arbitrary fallback => "
                     "E5 fails => reject.",
    },
]


# === axiom lane: A-reference deep-model soundness + containment ============
# No @ContractOnly axiom (axioms region empty), but the changed operation is an
# A-reference deep model (is_supported / target_name / call_render) validated ==
# the real PythonCodePrinter.  Re-run that real-callee check in the instance image
# (apply_gold=True: the deep model encodes the POST-patch table).  axiom_check.py
# is NOT mounted in-container, so it is read on the HOST and embedded below.

# Soundness probe: run the real PythonCodePrinter (post-patch table) and assert
# deep model == real renderer on Min/Max/Abs + unsupported negatives.  This is
# exactly axiom_check.main(); we embed its source and invoke main().
_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '_embedded_axiom_check'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom-soundness probe: main() returned', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

# Containment probe: enumerate EXACTLY the name codes the model can pass to the
# deep model.  The model's Requires is 0 <= name_code <= 3, so the reachable set
# is {0,1,2,3}.  is_supported / target_name / call_render are TOTAL @Pure helpers:
# is_supported is defined for all four codes (True for 0/1/2, False for 3);
# target_name is consulted by call_render ONLY when is_supported holds (E2/E3/E4
# guard on is_supported(nc); the unsupported clause E5 pins the result to the
# read-only `fallback` input and consults NO deep-model helper).  So every
# callee-input the model can reach (name codes 0/1/2 into target_name via
# call_render) lies in the deep model's domain {0,1,2}.  The real printer must
# agree on each.  We assert the real callee is defined and call-renders for each
# reachable supported code, and that name code 3 routes to the unchanged
# machinery's NON-call output (the `fallback` the model returns verbatim).
_AX_CONTAIN_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys, importlib\n"
    "from itertools import chain\n"
    "import sympy\n"
    "pc = importlib.import_module('sympy.printing.pycode')\n"
    "# apply the gold edit (the deep model encodes the POST-patch table)\n"
    "pc._known_functions['Min'] = 'min'\n"
    "pc._known_functions['Max'] = 'max'\n"
    "pc.AbstractPythonCodePrinter._kf = dict(chain(\n"
    "    pc._known_functions.items(),\n"
    "    [(k, 'math.' + v) for k, v in pc._known_functions_math.items()]))\n"
    "from sympy import Min, Max, Abs, Symbol, Function\n"
    "x, y, z = Symbol('x'), Symbol('y'), Symbol('z')\n"
    "TARGET = {0: 'abs', 1: 'min', 2: 'max'}\n"
    "# reachable supported name codes the model feeds call_render: {0,1,2}\n"
    "checks = 0\n"
    "for nc, expr in [(0, Abs(x)), (1, Min(x, y)), (2, Max(x, y))]:\n"
    "    prntr = pc.PythonCodePrinter()\n"
    "    joined = ', '.join(prntr._print(a) for a in expr.args)\n"
    "    observed = prntr.doprint(expr)\n"
    "    expected = TARGET[nc] + '(' + joined + ')'\n"
    "    assert observed == expected, (\n"
    "        'reachable supported code %d outside deep-model domain: %r != %r'\n"
    "        % (nc, observed, expected))\n"
    "    checks += 1\n"
    "# name code 3 (unsupported) is reachable but the model NEVER calls\n"
    "# call_render(3,...); its result is pinned to the `fallback` input — the\n"
    "# unchanged machinery's output.  Confirm the real printer routes an unknown\n"
    "# function to a NON-call form (so containment to {0,1,2} is the full\n"
    "# reachable set and the fallback carrier abstracts a real, non-call text).\n"
    "f = Function('f_unknown')\n"
    "prntr = pc.PythonCodePrinter()\n"
    "joined = ', '.join(prntr._print(a) for a in (x, y))\n"
    "observed = prntr.doprint(f(x, y))\n"
    "for nc in (0, 1, 2):\n"
    "    assert observed != TARGET[nc] + '(' + joined + ')', (\n"
    "        'unsupported identity rendered as supported call form %r' % observed)\n"
    "checks += 1\n"
    "print('axiom-containment probe OK: every model-reachable callee input in the '\n"
    "      'deep-model domain over %d checks' % checks)\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodel",
        "axiom": "is_supported/target_name/call_render",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "The A-reference deep model encodes the POST-patch supported "
                     "table; G-AX (axiom_check.py) runs the real PythonCodePrinter "
                     "over 600 Min/Max/Abs renderings + 40 unsupported negatives "
                     "and asserts deep model == real printer. If the real callee "
                     "disagrees on any input in the deep-model domain under the "
                     "default printer config => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-deepmodel",
        "axiom": "is_supported/target_name/call_render",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "The model's Requires is 0<=name_code<=3; call_render/"
                     "target_name are consulted only on the supported codes "
                     "{0,1,2} (E2 guards on is_supported; E5 pins the unsupported "
                     "result to the read-only fallback input and consults no "
                     "deep-model helper). Every callee-input the model can reach "
                     "lies in the deep-model domain {0,1,2}; name code 3 is "
                     "reachable but pinned to the unchanged machinery's output "
                     "(a non-call form in the real printer). A reachable input "
                     "outside the covered domain => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
