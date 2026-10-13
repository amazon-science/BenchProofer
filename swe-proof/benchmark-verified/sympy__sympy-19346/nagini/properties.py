# properties.py — PBT manifest for sympy__sympy-19346. NOT a Nagini module; a
# record of adversarially-reasoned falsification cases. The runner
# (swebench_nagini.pbt) writes each `module` to a temp file and checks it with
# Nagini verify + markers.same_spec; each `probe` is run in the instance Docker
# image against the real sympy callee.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   Two modeled functions, BOTH with a READ-ONLY input:
#     render_collection_codepoints(elems): Requires Acc(list_pred(elems), 1/2)
#         Ensures ToSeq(Result()) == set_seq(ToSeq(elems))
#     render_mapping_codepoints(flat):     Requires Acc(list_pred(flat), 1/2)
#                                                 and len(flat) % 2 == 0
#         Ensures ToSeq(Result()) == dict_seq(ToSeq(flat))
#   The load-bearing postcondition pins the output to set_seq / dict_seq, which
#   are FULLY GROUNDED @Pure folds (joined_elems / joined_pairs over the input
#   tokens + the brace/separator/empty-literal structure) — NOT an opaque
#   @ContractOnly answer key. There is therefore no wrong-echo of an ungrounded
#   oracle to build (see 'assessment' / the ungrounded-oracle entry below); the
#   two opaque callees are elem_repr/doprint_elem and elem_str/str_elem, and
#   BOTH are wholly uninterpreted — neither carries any constraint on the
#   length or content of its result (`Ensures(True)`). The proof consumes only
#   doprint_elem's VALUE link `ToSeq(Result()) == elem_repr(t)`, never any
#   property of elem_repr itself; in particular NO non-emptiness is assumed,
#   because the real per-element routine does render some elements as the empty
#   sequence (see ax-sound-elem-repr).
#
# same_spec is GUARANTEED because every variant is produced by `_swap` edits
# strictly INSIDE one of the two `# impl-start` / `# impl-end` regions (which
# include the nested invariants); the frozen Requires/Ensures live OUTSIDE those
# regions and are never touched.

from pathlib import Path

INSTANCE = "sympy__sympy-19346"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the set-renderer impl region (lines 173-207).
# ---------------------------------------------------------------------------

_SET_ELT_FETCH = (
    "        elt = elems[i - 1]  # type: int\n"
    "        Assert(elems_s.drop(i - 1)[0] == elt)\n"
    "        Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))\n"
)

_SET_PIECE = (
    "        piece = doprint_elem(elt)  # type: List[int]\n"
    "        Assert(ToSeq(piece) == elem_repr(elt))\n"
)

# ---------------------------------------------------------------------------
# Anchors INSIDE the dict-renderer impl region (lines 225-268).
# ---------------------------------------------------------------------------

_DICT_KV_FETCH = (
    "        key = flat[i - 2]  # type: int\n"
    "        val = flat[i - 1]  # type: int\n"
    "        Assert(len(flat_s.drop(i - 2)) % 2 == 0)\n"
    "        Assert(flat_s.drop(i - 2)[0] == key)\n"
    "        Assert(flat_s.drop(i - 2)[1] == val)\n"
    "        Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))\n"
)

_DICT_PIECE = (
    "        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]\n"
    "        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)\n"
    "               + elem_repr(val))\n"
)


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally different but CORRECT.
#    Read the element through a renamed-local indirection (`cur` -> `elt`), a
#    genuinely different SSA shape than model.py's direct `elt = elems[i-1]`.
#    The two prefix asserts are kept in model.py's ORDER (NOT reordered): the
#    asserts are independent so any order is sound, but Z3's quantifier-
#    instantiation search is order-sensitive and an arbitrary reorder pushed the
#    proof past the 300s budget (a proof-engineering timeout, not a spec
#    rejection — see the adjudication note below). The backward loop, every
#    Invariant and the load-bearing fold asserts stay VERBATIM (gold proof
#    obligations survive, per AVOID-bug #2). A correct reshape MUST verify (else
#    SPEC-TOO-STRONG).
# ===========================================================================

_pos_set = _swap(
    _BASE,
    _SET_ELT_FETCH,
    "        cur = elems[i - 1]  # type: int\n"
    "        elt = cur  # type: int\n"
    "        Assert(elems_s.drop(i - 1)[0] == elt)\n"
    "        Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))\n",
)

# ===========================================================================
#    A second positive control on the DICT renderer: read key/value through
#    renamed-local indirections (`k0`/`v0` -> `key`/`val`), a different SSA
#    shape than model.py's direct reads. The four prefix asserts are kept in
#    model.py's ORDER (same rationale as the set control: reordering them is
#    sound but order-sensitive in Z3 and the original arbitrary reorder timed
#    out at >600s single-process, whereas the same-order reshape discharges in
#    ~46s).
# ===========================================================================

_pos_dict = _swap(
    _BASE,
    _DICT_KV_FETCH,
    "        k0 = flat[i - 2]  # type: int\n"
    "        v0 = flat[i - 1]  # type: int\n"
    "        key = k0  # type: int\n"
    "        val = v0  # type: int\n"
    "        Assert(len(flat_s.drop(i - 2)) % 2 == 0)\n"
    "        Assert(flat_s.drop(i - 2)[0] == key)\n"
    "        Assert(flat_s.drop(i - 2)[1] == val)\n"
    "        Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))\n",
)

# ===========================================================================
# 2. FRAME-MUTATION (MANDATORY — both inputs are Acc(...,1/2) read-only).
#    A rival that WRITES to the read-only input. With only half permission on
#    list_pred(elems) / list_pred(flat) a heap write requires FULL permission,
#    so it must be REJECTED for INSUFFICIENT PERMISSION (not for a value
#    mismatch). The illegal write is the FIRST impl statement so Nagini reports
#    the permission error up front and rejects FAST (~36s) — placing it later
#    (e.g. before the loop, with the full fold body still ahead) made the
#    verifier explore the entire backward-fold proof before reporting the same
#    error, blowing the 300s budget; a timeout-as-rejection is not a sound
#    "reject" signal (and it starved the co-scheduled positive control). Failing
#    fast on the permission error makes the rejection unambiguously attributable
#    to the write, not a proof-search timeout.
# ===========================================================================

# Set: overwrite element 0 of the read-only `elems` as the first impl op.
_frame_set = _swap(
    _BASE,
    "    # impl-start\n    elems_s = ToSeq(elems)  # type: PSeq[int]\n",
    "    # impl-start\n"
    "    elems[0] = 0  # frame-mutation: write to a 1/2-permission input -> reject\n"
    "    elems_s = ToSeq(elems)  # type: PSeq[int]\n",
)

# Dict: overwrite element 0 of the read-only `flat` as the first impl op.
_frame_dict = _swap(
    _BASE,
    "    # impl-start\n    flat_s = ToSeq(flat)  # type: PSeq[int]\n",
    "    # impl-start\n"
    "    flat[0] = 0  # frame-mutation: write to a 1/2-permission input -> reject\n"
    "    flat_s = ToSeq(flat)  # type: PSeq[int]\n",
)

# ===========================================================================
# 3a. UNIQUENESS — the prepatch discriminator (THE bug). Render each element by
#     the plain display form `str_elem` (elem_str) instead of the executable
#     representation `doprint_elem` (elem_repr). elem_str and elem_repr are
#     distinct uninterpreted @ContractOnly callees with NO relation, so the
#     str_elem-built `inner` cannot discharge the elem_repr-built fold invariant
#     `ToSeq(inner) == joined_elems(...)`. MUST be rejected; if it verified the
#     spec would admit the pre-patch str() fallback => SPEC-TOO-WEAK.
#     Refinement: the faithful real patch is exactly the pre-patch state
#     (emptyPrinter -> str(expr), each element via str) which fails F2P test_dict
#     ( srepr({x:y}) would be "{x: y}" not "{Symbol('x'): Symbol('y')}" ).
# ===========================================================================

_wrong_str_set = _swap(
    _BASE,
    _SET_PIECE,
    "        piece = str_elem(elt)  # type: List[int]\n"
    "        Assert(ToSeq(piece) == elem_str(elt))\n",
)

_wrong_str_dict = _swap(
    _BASE,
    _DICT_PIECE,
    "        piece = str_elem(key) + [COLON, SPACE] + str_elem(val)  # type: List[int]\n"
    "        Assert(ToSeq(piece) == elem_str(key) + PSeq(COLON, SPACE)\n"
    "               + elem_str(val))\n",
)

# ===========================================================================
# 3b. PARTIAL-DOMAIN (set) — render the FIRST element by the plain display form
#     and the rest correctly. Correct on the whole tail; diverges only on the
#     i == 1 (last loop step / first element) sub-domain. Output equals the gold
#     on every multi-element input EXCEPT the leading element's spelling, so a
#     value-proxy that ignored the first element would miss it. MUST reject (the
#     fold invariant pins EVERY element to elem_repr).
#     Refinement: a real patch that srepr-ed all but the first element would
#     print str(first) (e.g. "{x, Symbol('y')}") and fail test_set / test_dict.
# ===========================================================================

_partial_set = _swap(
    _BASE,
    _SET_PIECE,
    "        if i == 1:\n"
    "            piece = str_elem(elt)  # type: List[int]\n"
    "            Assert(ToSeq(piece) == elem_str(elt))\n"
    "        else:\n"
    "            piece = doprint_elem(elt)\n"
    "            Assert(ToSeq(piece) == elem_repr(elt))\n",
)

# ===========================================================================
# 3c. VALUE-LEVEL SWAP (dict) — render each pair as VALUE: KEY instead of
#     KEY: VALUE (swap the two doprint_elem calls). Structurally a valid dict
#     rendering shape, but the pairing is reversed: dict_seq pins position 2j ->
#     key-repr, 2j+1 -> value-repr. MUST reject because elem_repr(key) and
#     elem_repr(val) are distinct for distinct tokens.
#     Refinement: a real patch emitting "%s: %s" % (doprint(value), doprint(key))
#     prints "{Symbol('y'): Symbol('x')}" for {x: y} and fails test_dict.
# ===========================================================================

_swap_kv_dict = _swap(
    _BASE,
    _DICT_PIECE,
    "        piece = doprint_elem(val) + [COLON, SPACE] + doprint_elem(key)  # type: List[int]\n"
    "        Assert(ToSeq(piece) == elem_repr(val) + PSeq(COLON, SPACE)\n"
    "               + elem_repr(key))\n",
)

# ===========================================================================
# 3d. SEPARATOR DROP (set) — assemble WITHOUT the ", " between elements
#     (inner = piece + inner). joined_elems pins a COMMA,SPACE between
#     consecutive renderings; the no-separator assembly cannot match. MUST
#     reject. Refinement: a real patch using "".join instead of ", ".join would
#     print "{Symbol('x')Symbol('y')}" and fail test_set.
# ===========================================================================

_no_sep_set = _swap(
    _BASE,
    "            inner = piece + [COMMA, SPACE] + inner\n"
    "            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)\n"
    "                   + joined_elems(elems_s.drop(i)))\n"
    "            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))\n",
    "            inner = piece + inner\n"
    "            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)\n"
    "                   + joined_elems(elems_s.drop(i)))\n"
    "            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))\n",
)

# ===========================================================================
# 3e. WRONG EMPTY LITERAL (set) — return "{}" for the empty collection instead
#     of "set()". set_seq pins the empty form to the five code points of
#     "set()". MUST reject. Refinement: a real _print_set returning "{}" for an
#     empty set fails test_set (srepr(set()) must be "set()").
# ===========================================================================

_empty_lit_set = _swap(
    _BASE,
    '        out_empty = [115, 101, 116, 40, 41]  # type: List[int]  # "set()"\n'
    "        Assert(ToSeq(out_empty) == set_seq(elems_s))\n",
    '        out_empty = [LBRACE, RBRACE]  # type: List[int]  # wrong: "{}"\n'
    "        Assert(ToSeq(out_empty) == set_seq(elems_s))\n",
)


SPEC_TESTS = [
    # --- soundness (positive controls) -------------------------------------
    {
        "id": "pos-control-set",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_set,
        "rationale": "structurally-different CORRECT set renderer: the element "
        "is read through a renamed-local indirection (different SSA shape than "
        "model.py), while the backward loop, every Invariant, the prefix asserts "
        "(kept in model.py order for Z3 stability) and the load-bearing fold "
        "asserts are kept verbatim. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-dict",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_dict,
        "rationale": "structurally-different CORRECT dict renderer: key/value "
        "are read through renamed-local indirections (different SSA shape than "
        "model.py); the four prefix asserts are kept in model.py order (Z3 "
        "stability) and loop/Invariants/fold asserts verbatim. Must verify; "
        "else SPEC-TOO-STRONG.",
    },
    # --- frame-mutation (read-only inputs) ---------------------------------
    {
        "id": "frame-mut-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_set,
        "refinement": "writing into the rendered set is not part of any "
        "faithful _print_set (a printer never mutates the object it prints); a "
        "real impl mutating expr would corrupt the set and is not the gold "
        "patch, so it would not resolve test_set/test_dict.",
        "rationale": "elems has only Acc(list_pred(elems), 1/2); the heap write "
        "elems[0] = 0 needs FULL permission, so Nagini rejects for INSUFFICIENT "
        "PERMISSION (the half-permission Requires/Ensures/Invariant on elems is "
        "kept verbatim). A verify here would be a frame-condition hole.",
    },
    {
        "id": "frame-mut-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_dict,
        "refinement": "a faithful _print_dict never mutates the dict it prints; "
        "a real impl writing into expr is not the gold patch and would not "
        "resolve test_dict.",
        "rationale": "flat has only Acc(list_pred(flat), 1/2); flat[0] = 0 needs "
        "FULL permission -> rejected for INSUFFICIENT PERMISSION. A verify here "
        "would be a frame-condition hole.",
    },
    # --- uniqueness: the prepatch discriminator (THE bug) ------------------
    {
        "id": "wrong-str-elem-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_str_set,
        "refinement": "this IS the pre-patch behaviour: each element rendered by "
        "the plain display form str() (emptyPrinter -> str(expr)) instead of the "
        "executable srepr. srepr({x,y}) would print '{x, y}' not "
        "'{Symbol('x'), Symbol('y')}' and fail test_set/test_dict — exactly the "
        "F2P the gold patch fixes.",
        "rationale": "elem_str and elem_repr are distinct uninterpreted "
        "@ContractOnly callees with no relation; the str_elem-built `inner` "
        "cannot discharge the elem_repr-built fold invariant "
        "ToSeq(inner)==joined_elems(...). A verify here => SPEC-TOO-WEAK "
        "(admits the prepatch).",
    },
    {
        "id": "wrong-str-elem-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_str_dict,
        "refinement": "the pre-patch dict behaviour: each key/value via str() "
        "instead of srepr; srepr({x:y}) would be '{x: y}' not "
        "'{Symbol('x'): Symbol('y')}' — fails test_dict (the graded F2P).",
        "rationale": "str_elem-built inner cannot discharge the elem_repr-built "
        "joined_pairs fold invariant (line 243). A verify => SPEC-TOO-WEAK.",
    },
    # --- partial-domain ----------------------------------------------------
    {
        "id": "partial-domain-first-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_set,
        "refinement": "renders the FIRST element by str() and the rest by srepr "
        "(correct on the whole tail, wrong only on the leading element). A real "
        "patch that srepr-ed all but the first element would print "
        "'{x, Symbol('y')}' and fail test_set/test_dict.",
        "rationale": "the fold invariant pins EVERY element (including the first, "
        "reached at i==1) to elem_repr; the i==1 branch uses elem_str, which is "
        "a distinct uninterpreted callee, so the last loop step's invariant "
        "ToSeq(inner)==joined_elems(elems_s.drop(0)) cannot be re-established. "
        "A verify => SPEC-TOO-WEAK on the first-element sub-domain.",
    },
    {
        "id": "swap-key-value-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_kv_dict,
        "refinement": "renders each pair as value: key instead of key: value. A "
        "real patch '%s: %s' % (doprint(value), doprint(key)) prints "
        "'{Symbol('y'): Symbol('x')}' for {x: y} and fails test_dict.",
        "rationale": "dict_seq pins position 2j -> elem_repr(key), 2j+1 -> "
        "elem_repr(value); elem_repr(key) and elem_repr(val) are distinct for "
        "distinct tokens so the swapped piece cannot match joined_pairs. "
        "A verify => SPEC-TOO-WEAK on key/value ordering.",
    },
    # --- supporting mechanical near-misses (still carry a refinement) ------
    {
        "id": "no-separator-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_sep_set,
        "refinement": "assembles elements with no ', ' separator. A real patch "
        "using ''.join instead of ', '.join prints '{Symbol('x')Symbol('y')}' "
        "and fails test_set.",
        "rationale": "joined_elems pins COMMA,SPACE between consecutive "
        "renderings; the no-separator assembly fails the per-element fold assert "
        "ToSeq(inner)==elem_repr(elt)+PSeq(COMMA,SPACE)+joined_elems(...). "
        "Supporting near-miss; a verify => SPEC-TOO-WEAK on the separator.",
    },
    {
        "id": "wrong-empty-literal-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _empty_lit_set,
        "refinement": "returns '{}' for the empty collection. A real _print_set "
        "returning '{}' for an empty set fails test_set (srepr(set()) must be "
        "'set()').",
        "rationale": "set_seq pins the empty form to the five code points of "
        "'set()'; the [LBRACE,RBRACE] empty literal fails "
        "Assert(ToSeq(out_empty)==set_seq(elems_s)). Supporting near-miss; "
        "a verify => SPEC-TOO-WEAK on the empty literal.",
    },
]


# ===========================================================================
# AXIOM lane. The A-consumed link is doprint_elem's VALUE
# (ToSeq(Result()) == elem_repr(t)); elem_repr itself is uninterpreted
# (Ensures(True)), as is the contrast callee elem_str/str_elem. Plus the
# A-reference deep model (set_seq/dict_seq). All checks call the REAL sympy
# callee in the instance image; none scrape source (AVOID-bug #4). Files opened
# utf-8 (AVOID-bug #5). The probes are self-contained (stdlib + public sympy api
# only) — they do NOT read any bundle file in-container (AVOID-bug #6).
# ===========================================================================

# --- ax-sound-elem-repr: the A-consumed obligation. The ONLY property the
# proof uses is the value link doprint_elem == the recursive representation
# routine (ReprPrinter().doprint == public srepr); elem_repr carries no
# constraint at all. Checked on the FULL element pool the model can reach,
# INCLUDING the constant/singleton/boolean/None/empty-name class AND the class
# whose representation is the EMPTY sequence — the class that makes a
# `len(Result()) >= 1` claim on elem_repr unsound, so this probe ALSO asserts
# that no such non-emptiness claim is sound (guarding its re-introduction, the
# same way ax-sound-elem-str guards its siblings). apply_gold False: srepr/
# doprint of a single element is UNCHANGED by the patch (the patch only adds the
# two container methods), so the per-element axiom holds pre- and post-patch.
_PROBE_ELEM_REPR = r'''
import sys
from sympy import (srepr, Symbol, Integer, Rational, Float, oo, zoo, nan,
                   pi, E, I, S)
from sympy.printing.repr import ReprPrinter

x, y, z = Symbol('x'), Symbol('y'), Symbol('z')
discriminating = [x, y, z, Symbol('alpha'), Integer(0), Integer(5),
                  Integer(-3), Rational(1, 2), Rational(-7, 4), Float(1.5),
                  Symbol('x', positive=True)]
coincident = [oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.Pi, S.EmptySet,
              True, False, None]
# Elements whose executable representation is the EMPTY sequence: the printer
# has no dedicated method for these classes, so the dispatch scan falls through
# to a branch that returns the object's plain text, which is empty here.
empty_rep = []
try:
    from sympy.physics.units import Quantity
    empty_rep.append(Quantity(''))
except Exception:
    pass
try:
    from sympy.printing.pretty.stringpict import stringPict
    empty_rep.append(stringPict(''))
except Exception:
    pass
try:
    from sympy.assumptions.cnf import CNF
    empty_rep.append(CNF())
except Exception:
    pass
pool = discriminating + coincident + [Symbol(''), {x: y}, {x, y}] + empty_rep

rp = ReprPrinter()
bad = []
for elem in pool:
    rep = srepr(elem)
    # the modeled `doprint_elem` is ReprPrinter().doprint; the consumed
    # obligation is exactly this value link. NO length claim is asserted.
    dp = rp.doprint(elem)
    if dp != rep:
        bad.append(("doprint!=srepr", elem, dp, rep))
# NEGATIVE witness for the dropped `len(elem_repr(t)) >= 1` over-claim: the real
# routine DOES return the empty sequence for these elements, so a non-emptiness
# Ensures on elem_repr would be AXIOM-UNSOUND. Assert at least one witness is
# genuinely empty (skipped only if none of the classes could be imported).
n_empty = sum(1 for e in empty_rep if len(srepr(e)) == 0)
if empty_rep and n_empty == 0:
    bad.append(("expected an empty-representation witness; none was empty",
                [srepr(e) for e in empty_rep]))
if bad:
    print("AXIOM-UNSOUND elem_repr:", bad)
    sys.exit(1)
print("ax-sound-elem-repr OK: doprint==srepr on %d elements incl. constant/"
      "singleton/None/empty-name class and %d element(s) whose representation "
      "is EMPTY (%d confirmed empty) -> elem_repr is correctly uninterpreted, "
      "no len>=1 over-claim" % (len(pool), len(empty_rep), n_empty))
sys.exit(0)
'''

# --- ax-sound-elem-str-existential: str != srepr on the discriminating class
# AND str == srepr on the constant class (so NO universal inequality / no
# len>=1 over-claim is sound). Mirrors axiom_check.py's existential witness.
_PROBE_ELEM_STR = r'''
import sys
from sympy import (srepr, Symbol, Integer, Rational, Float, oo, zoo, nan,
                   pi, E, I, S)

x, y, z = Symbol('x'), Symbol('y'), Symbol('z')
discriminating = [x, y, z, Symbol('alpha'), Integer(0), Integer(5),
                  Integer(-3), Rational(1, 2), Rational(-7, 4), Float(1.5),
                  Symbol('x', positive=True)]
coincident = [oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.Pi, S.EmptySet,
              True, False, None]

bad = []
for e in discriminating:
    if str(e) == srepr(e):
        bad.append(("expected str!=srepr", e, str(e), srepr(e)))
for e in coincident:
    if str(e) != srepr(e):
        bad.append(("expected str==srepr (so NOT universal)", e, str(e), srepr(e)))
# the dropped len(elem_str)>=1 over-claim: str(Symbol('')) == '' has length 0.
if str(Symbol('')) != '' or len(str(Symbol(''))) != 0:
    bad.append(("expected str(Symbol(''))==''", str(Symbol(''))))
if len(srepr(Symbol(''))) < 1:
    bad.append(("srepr(Symbol('')) empty",))
if bad:
    print("AXIOM-UNSOUND elem_str (existential witness violated):", bad)
    sys.exit(1)
print("ax-sound-elem-str OK: str!=srepr on %d discriminating, str==srepr on %d "
      "constant-class, str(Symbol(''))=='' -> no universal inequality, no "
      "len>=1 over-claim" % (len(discriminating), len(coincident)))
sys.exit(0)
'''

# --- ax-cover-set-dict: the A-reference deep model. The model can ONLY pass to
# set_seq/dict_seq token sequences derived from a real set/dict's iteration
# order; assert the deep model (token substitution by real srepr, mirroring the
# documented assembly) equals the real assembly AND the live _print_set /
# _print_dict on boundary + fuzz inputs over the FULL pool. apply_gold True:
# _print_set/_print_dict only exist after the patch (the deep model describes
# the post-gold container assembly). Containment: every callee-reachable input
# (any finite ordered list of element tokens; flat even-length key/value list)
# is in the assembly's domain — the deep model is total over those.
_PROBE_DEEP_MODEL = r'''
import random
import sys
from sympy import (srepr, Symbol, Integer, Rational, Float, oo, zoo, nan,
                   pi, E, I, S)
from sympy.printing.repr import ReprPrinter

def model_set_seq(elems):
    if len(elems) == 0:
        return "set()"
    return "{%s}" % ", ".join(srepr(e) for e in elems)

def model_dict_seq(pairs):
    if len(pairs) == 0:
        return "{}"
    return "{%s}" % ", ".join("%s: %s" % (srepr(k), srepr(v)) for (k, v) in pairs)

rp = ReprPrinter()
have_set = hasattr(rp, "_print_set")
have_dict = hasattr(rp, "_print_dict")
if not (have_set and have_dict):
    print("AXIOM-MISSING: _print_set/_print_dict absent (gold not applied?)")
    sys.exit(1)

x, y, z = Symbol('x'), Symbol('y'), Symbol('z')
discriminating = [x, y, z, Symbol('alpha'), Integer(0), Integer(5),
                  Integer(-3), Rational(1, 2), Rational(-7, 4), Float(1.5)]
coincident = [oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.Pi, True, False, None]
pool = discriminating + coincident + [Symbol('')]

def check_set(elems):
    real_set = set(elems)
    order = list(real_set)            # the model's reachable token order
    expected = model_set_seq(order)
    live = rp._print_set(real_set)
    assert live == expected, ("set deep model mismatch: model %r vs live %r"
                              % (expected, live))

def check_dict(pairs):
    d = dict(pairs)
    real_pairs = list(d.items())      # the model's reachable flat order
    expected = model_dict_seq(real_pairs)
    live = rp._print_dict(d)
    assert live == expected, ("dict deep model mismatch: model %r vs live %r"
                              % (expected, live))

# boundary
check_set([]); check_set([x]); check_set([Integer(5)]); check_set([x, y, z])
check_set([oo, pi]); check_set([Symbol(''), x])
check_dict([]); check_dict([(x, y)]); check_dict([(x, y), (y, z)])
check_dict([(x, {y: z})]); check_dict([(oo, nan), (pi, E)])
check_dict([(Symbol(''), x)])

rng = random.Random(19346)
n_set = n_dict = 0
for _ in range(2000):
    k = rng.randint(0, 5)
    elems = rng.sample(pool, min(k, len(pool)))
    check_set(elems); n_set += 1
for _ in range(2000):
    k = rng.randint(0, 5)
    keys = rng.sample(pool, min(k, len(pool)))
    vals = [rng.choice(pool) for _ in keys]
    check_dict(list(zip(keys, vals))); n_dict += 1

print("ax-cover-set-dict OK: set_seq/dict_seq == live _print_set/_print_dict "
      "on boundary + %d set + %d dict fuzz inputs over the full pool" %
      (n_set, n_dict))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-elem-repr",
        "axiom": "elem_repr / doprint_elem",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _PROBE_ELEM_REPR,
        "rationale": "the only consumed obligation is the VALUE link "
        "doprint_elem == the recursive srepr routine; elem_repr itself is "
        "uninterpreted (Ensures(True)). The real ReprPrinter().doprint equals "
        "public srepr on EVERY reachable element class (symbolic/numeric, "
        "constant/singleton/None/empty-name, AND the class whose representation "
        "is the EMPTY sequence). The probe also witnesses that empty class, "
        "because a `len(elem_repr(t)) >= 1` Ensures would be AXIOM-UNSOUND on "
        "it -- this guards against re-introducing that over-claim, exactly as "
        "ax-sound-elem-str guards its siblings. Per-element srepr is unchanged "
        "by the patch.",
    },
    {
        "id": "ax-sound-elem-str-existential",
        "axiom": "elem_str / str_elem",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _PROBE_ELEM_STR,
        "rationale": "elem_str carries NO Ensures relating it to elem_repr and no "
        "len>=1. The real callee witnesses str!=srepr on the discriminating "
        "class but str==srepr on the constant class and str(Symbol(''))=='' — so "
        "a universal inequality or len>=1 would be AXIOM-UNSOUND. This guards "
        "against re-introducing the over-claim the prior bundle shipped.",
    },
    {
        "id": "ax-cover-set-dict",
        "axiom": "set_seq / dict_seq (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_DEEP_MODEL,
        "rationale": "every callee-reachable input (any ordered element-token "
        "list for set_seq; any flat even-length key/value list for dict_seq) is "
        "in the assembly's domain and the deep model equals the live "
        "_print_set/_print_dict (the post-gold container methods) on boundary + "
        "fuzz over the full pool. A live output diverging from the deep model "
        "would be AXIOM-TOO-WEAK-FOR-CALLER / a refinement break.",
    },
]
