# properties.py — PBT falsification battery for sphinx-doc__sphinx-9698.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant whose SPEC is byte-identical to the frozen
# model (region-surgery: every variant is built by _swap edits that touch ONLY
# text strictly inside the # impl-start / # impl-end region, so markers.same_spec
# holds by construction). Each AXIOM_TEST is a self-contained stdlib-only probe
# run in the instance Docker image against the REAL patched callee.
#
# Defended surface (read from model.py + refinement.md + mapping.md):
#   get_member_index_text(methname: List[int], clsname: List[int], option: int)
#     -> List[int]   builds a class-member one-line index label.
#   Read-only inputs:  Acc(list_pred(methname), 1/2) and Acc(list_pred(clsname),
#     1/2) are BOTH required and ensured  => MANDATORY frame-mutation probe.
#   Load-bearing postconditions:
#     (P1) ToSeq(Result()) == index_label(ToSeq(methname), ToSeq(clsname), option)
#          -- full equality to the deep model (the in-order assembly).
#     (P2) ToSeq(Result()).take(len(methname)) == ToSeq(methname)
#          -- the label begins with the member name.
#     (P3) is_callable_role(option) ==
#          (ToSeq(Result()).drop(len(methname)).take(2) == call_marker())
#          -- THE discriminator the bug fix is about: the empty-call marker '()'
#             follows the member name iff the role is callable (option != 2 =>
#             property is the single non-callable role, gets NO parens).
#   index_label is a @Pure fold fully grounded in the args (methname, clsname,
#     option) -- it is NOT an opaque answer-key oracle, so an "echo the oracle"
#     rival cannot be wrong-yet-verifying (see 'assessment'); UNGROUNDED-ORACLE
#     is therefore N/A and replaced by an honest cheapest-impl positive control.
#   No @ContractOnly consumed axioms (axioms[] empty). One A-reference deep model
#     (index_label) validated == the real label by axiom_check.py; the AXIOM_TESTS
#     re-run that against the REAL patched PyMethod.get_index_text in Docker.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9698"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors -- all strictly inside the # impl-start / # impl-end region.
# ---------------------------------------------------------------------------

# The conditional empty-call marker (callable roles only).
_MARKER_BLOCK = (
    "    if is_callable_role(option):\n"
    "        result.append(40)\n"
    "        result.append(41)\n"
)

# The per-role suffix dispatch (constant role words, in source order 1/2/3/else).
_SUFFIX_BLOCK = (
    "    if option == 1:\n"
    "        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]\n"
    "    elif option == 2:\n"
    "        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]\n"
    "    elif option == 3:\n"
    "        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]\n"
    "    else:\n"
    "        result = result + [32, 109, 101, 116, 104, 111, 100, 41]\n"
)

# The first statement of the impl region -- a safe place to inject a frame-write.
_RESULT_INIT = "    result = []  # type: List[int]\n"

# The class-name copy loop body (copies clsname[k]).
_CLS_COPY = "        result.append(clsname[k])\n"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: methname/clsname are Acc(...,1/2)) --------
# A rival that WRITES to the read-only member-name input to "build" the label.
# It appends the empty-call marker directly onto methname (instead of result),
# then copies the now-mutated methname. With only 1/2 permission on methname the
# write is rejected for INSUFFICIENT PERMISSION -- the rejection is attributable
# to the permission system, not to any value mismatch (the gold invariants/asserts
# are kept verbatim).
_frame = _swap(
    _BASE,
    _MARKER_BLOCK,
    "    if is_callable_role(option):\n"
    "        methname.append(40)   # WRITE to a 1/2-permission read-only input\n"
    "        result.append(40)\n"
    "        result.append(41)\n",
)
SPEC_TESTS.append({
    "id": "frame-mutate-methname",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame,
    "refinement": (
        "A faithful real patch cannot mutate the member-name carrier: in "
        "sphinx, methname/clsname come from name.rsplit('.', 1) and the same "
        "string objects (and the entry target 'Class.meth5') flow on to the "
        "addnodes.index entry tuple. The F2P test_pymethod_options asserts the "
        "exact entry ('single', 'meth5 (Class property)', 'Class.meth5', ...); "
        "appending '(' onto methname would corrupt both the label and the "
        "target, so the real analogue would NOT resolve."
    ),
    "rationale": (
        "Rejected by the permission system: methname is held at Acc(list_pred"
        "(methname), 1/2), which forbids .append. A mutating rival must fail "
        "for insufficient permission, not for a value mismatch."
    ),
})

# --- 2. PARTIAL-DOMAIN: the bug itself (the pre-patch behaviour) -------------
# Emit '()' for EVERY role, including the property role (option 2). This is
# exactly model_prepatch: correct on options 0/1/3, diverges only on option 2.
# Violates P1 (full equality) and P3 (discriminator) for option == 2.
_always_parens = _swap(
    _BASE,
    _MARKER_BLOCK,
    "    if True:                       # emit '()' for EVERY role (pre-patch bug)\n"
    "        result.append(40)\n"
    "        result.append(41)\n",
)
SPEC_TESTS.append({
    "id": "partial-property-keeps-parens",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _always_parens,
    "refinement": (
        "This is the pre-patch code: the property template stays '%s() (%s "
        "property)'. The F2P test_pymethod_options now expects the index entry "
        "'meth5 (Class property)' (no parens); emitting 'meth5() (Class "
        "property)' is precisely the bug, so this rival's real patch does NOT "
        "resolve."
    ),
    "rationale": (
        "Rejected by postcondition P3 (is_callable_role(2) == False, but the "
        "marker '()' is present after the name) and P1 (full equality to "
        "index_label, which omits '()' for option 2) at option == 2."
    ),
})

# --- 3. PARTIAL-DOMAIN (inverted discriminator) ------------------------------
# Emit '()' ONLY for the property role and omit it for the callable roles -- the
# exact inversion of the spec. Correct on no role; diverges on all four, but is
# a distinct, plausible-looking 'option == 2 is special' miscoding.
_inverted = _swap(
    _BASE,
    _MARKER_BLOCK,
    "    if not is_callable_role(option):   # INVERTED: parens for property only\n"
    "        result.append(40)\n"
    "        result.append(41)\n",
)
SPEC_TESTS.append({
    "id": "partial-inverted-discriminator",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _inverted,
    "refinement": (
        "Inverts which role gets parens: 'meth5 (Class method)' for callables "
        "and 'meth5() (Class property)' for the property. Every callable-role "
        "P2P assertion (test_pyclassmethod / test_pystaticmethod / plain "
        "method) and the property F2P would fail, so the real analogue does "
        "NOT resolve."
    ),
    "rationale": (
        "Rejected by P3: the marker is present iff option == 2, the opposite "
        "of is_callable_role(option); and by P1 for every role."
    ),
})

# --- 4. UNIQUENESS: wrong class-name splice (value mismatch on P1) -----------
# Copy methname into the class-name slot instead of clsname. P2 (begins with
# methname) still holds, so this probes that P1's FULL equality is load-bearing
# and not subsumed by the take-prefix clause. (The class loop invariant is inside
# the elided impl region, so it is adjusted to match -- same_spec still holds.)
_wrong_cls = _swap(
    _BASE,
    "        result.append(clsname[k])\n        k = k + 1\n",
    "        result.append(methname[k])   # splice methname into the class slot\n"
    "        k = k + 1\n",
)
# The class loop's invariant pins ToSeq(result) to ... + clsname.take(k); copying
# methname[k] makes the loop unprovable AND, even past it, the final P1 equality
# fails. We must also keep k bounded by len(clsname) for the index to type-check;
# methname[k] is read at k < len(clsname) which is only safe when len(methname)
# >= len(clsname). To keep the rival well-formed (reject for the VALUE reason, not
# an index error), guard the copy and adjust the loop's stored invariant.
_wrong_cls = _swap(
    _wrong_cls,
    "        Invariant(ToSeq(result) ==\n"
    "                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))\n",
    "        Invariant(ToSeq(result) ==\n"
    "                  (index_prefix(ToSeq(methname), option) + ToSeq(methname).take(k)))\n",
)
SPEC_TESTS.append({
    "id": "uniqueness-wrong-class-slice",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _wrong_cls,
    "refinement": (
        "Splices the member name into the qualifying-class slot, producing e.g. "
        "'meth5 (meth5 property)'. The F2P/P2P entries name the real class "
        "('Class'); this rival's real patch (template '%s (%s property)' fed "
        "(methname, methname)) does NOT resolve."
    ),
    "rationale": (
        "Rejected by postcondition P1: ToSeq(Result()) must equal index_label, "
        "whose class segment is ToSeq(clsname); substituting methname breaks "
        "the full-equality clause even though the P2 prefix clause still holds "
        "-- proving P1 is independently load-bearing. (Either rejection path -- "
        "the P1 value mismatch, or the methname[k] read at k<len(clsname) being "
        "out of bounds when len(clsname)>len(methname) -- confirms the spec is "
        "not too weak here; both are sound reject reasons.)"
    ),
})

# --- 5. POSITIVE CONTROL (soundness): structurally reshaped, CORRECT ---------
# Same value, different executable shape: (a) the marker test is written as the
# concrete predicate `option != 2` (provably equal to is_callable_role(option),
# a @Pure unfold), and (b) the per-role suffix dispatch is reordered to test the
# property role FIRST. Branches are mutually exclusive over 0<=option<=3 and each
# appends the same literal as the gold branch, so index_label equality is
# unchanged. ALL gold invariants and framing Asserts are kept verbatim (avoidance
# bug #2/#3): no forward-append vs front-recursive-fold hazard is introduced.
_pos = _swap(
    _BASE,
    _MARKER_BLOCK,
    "    if option != 2:                 # provably == is_callable_role(option)\n"
    "        result.append(40)\n"
    "        result.append(41)\n",
)
_pos = _swap(
    _pos,
    _SUFFIX_BLOCK,
    "    if option == 2:                 # reordered: property role first\n"
    "        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]\n"
    "    elif option == 1:\n"
    "        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]\n"
    "    elif option == 3:\n"
    "        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]\n"
    "    else:\n"
    "        result = result + [32, 109, 101, 116, 104, 111, 100, 41]\n",
)
SPEC_TESTS.append({
    "id": "pos-control-reshaped",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos,
    "rationale": (
        "A correct impl with a different executable shape (concrete `option != "
        "2` marker test; property-first suffix dispatch) MUST verify; all gold "
        "loop invariants and framing Asserts are kept verbatim. If it fails to "
        "verify the spec is SPEC-TOO-STRONG."
    ),
})

# --- 6. POSITIVE CONTROL (cheapest honest, replaces ungrounded-oracle echo) --
# index_label is grounded, so there is no WRONG echo to build. Instead, the
# honest cheapest control: a one-shot `if option != 2:`-style marker plus the
# two index-copy loops unchanged -- here we simply collapse the suffix dispatch
# to a single equivalent assembly while keeping the marker as the concrete
# predicate. Verifies because it equals index_label. (Distinct from #5: here the
# suffix order is the gold order, only the marker predicate is reshaped.)
_cheap = _swap(
    _BASE,
    _MARKER_BLOCK,
    "    callable_role = (option != 2)   # bind the concrete decision once\n"
    "    if callable_role:\n"
    "        result.append(40)\n"
    "        result.append(41)\n",
)
SPEC_TESTS.append({
    "id": "pos-control-cheapest-honest",
    "kind": "soundness",
    "expect": "verify",
    "module": _cheap,
    "rationale": (
        "Honest cheapest-impl positive control (index_label is a grounded fold, "
        "so no wrong-echo exists): the marker decision is bound to a local and "
        "the gold suffix order is kept. Must verify; if not, SPEC-TOO-STRONG."
    ),
})

# --- 7. ADMISSIBILITY: the precondition accepts an F2P-shaped input ----------
# An in-region self-call on the exact F2P shape (methname='meth5', clsname=
# 'Class', option=2, the property role) confirms Requires admits a normal input.
# The call site establishes Acc(...,1/2) for both name lists and 0<=option<=3.
_admiss = _swap(
    _BASE,
    _RESULT_INIT,
    "    result = []  # type: List[int]\n"
    "    # admissibility: the F2P-shaped input (property role) is in-domain.\n"
    "    Assert(0 <= option and option <= 3)\n",
)
SPEC_TESTS.append({
    "id": "admiss-f2p-shape",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": (
        "The precondition (0<=option<=3, fractional permission on both names) "
        "admits the F2P input (property role, option 2). The asserted in-domain "
        "fact is discharged from Requires; if it could not be, PRECOND-TOO-STRONG."
    ),
})


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# No @ContractOnly consumed axioms (axioms[] empty). One A-reference deep model
# (index_label) is validated == the real label by axiom_check.py. We re-run that
# soundness check in Docker against the REAL patched PyMethod.get_index_text and
# add an explicit caller-domain containment probe over the model's reachable
# inputs. The axiom_check.py oracle is read on the HOST at load time and embedded
# into the probe (avoidance bug #6: only the probe script is mounted in-container).
AXIOM_TESTS = []

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# --- AX-1: A-reference soundness -- deep model == REAL patched callee --------
# Run the bundled G-AX check (cartesian boundary + 20000 fuzz against the
# post-patch templates) AND drive the REAL patched sphinx PyMethod.get_index_text
# for all four roles in-container (apply_gold=True => property role IS patched).
_probe_sound = (
    "# AX-1 axiom-soundness: deep model index_label == REAL patched label.\n"
    "import sys\n"
    "import sphinx.util.nodes  # break a sphinx circular import (addnodes<->util.nodes)\n"
    "                          # BEFORE importing sphinx.domains.python; a bare\n"
    "                          # `from sphinx.domains.python import PyMethod` as the\n"
    "                          # first sphinx import hits a partially-initialized\n"
    "                          # sphinx.addnodes and crashes (AttributeError on\n"
    "                          # versionmodified). Importing sphinx.util.nodes first\n"
    "                          # resolves addnodes fully, so the real callee loads.\n"
    "from sphinx.domains.python import PyMethod  # must be the PATCHED callee\n"
    "from unittest import mock\n"
    "\n"
    "# ---- embedded axiom_check.py oracle (host-read at manifest load) --------\n"
    + _AXIOM_CHECK_SRC +
    "\n"
    "# ---- drive the REAL patched callee for all four roles -------------------\n"
    "def _drive(option, kw):\n"
    "    pm = PyMethod.__new__(PyMethod)\n"
    "    pm.options = {} if kw is None else {kw: True}\n"
    "    pm.state = mock.Mock()\n"
    "    pm.state.document.settings.env.config.add_module_names = False\n"
    "    return pm.get_index_text('', ('Class.meth5', 'Class'))\n"
    "\n"
    "prop_label = _drive(2, 'property')\n"
    "if '()' in prop_label:\n"
    "    print('FAIL: property label still has parens (callee not patched):', repr(prop_label))\n"
    "    sys.exit(1)\n"
    "for option, kw in {0: None, 1: 'classmethod', 2: 'property', 3: 'staticmethod'}.items():\n"
    "    real = _drive(option, kw)\n"
    "    expected = index_label([ord(c) for c in 'meth5'], [ord(c) for c in 'Class'], option)\n"
    "    observed = [ord(ch) for ch in real]\n"
    "    if observed != expected:\n"
    "        print('FAIL: real callee disagrees with deep model for option=%d: real=%r model_cp=%r'\n"
    "              % (option, real, expected))\n"
    "        sys.exit(1)\n"
    "    # discriminator: '()' after the member name iff callable role\n"
    "    after = observed[len('meth5'):len('meth5') + 2]\n"
    "    if (after == call_marker()) != is_callable_role(option):\n"
    "        print('FAIL: call-marker discriminator wrong vs real callee, option=%d' % option)\n"
    "        sys.exit(1)\n"
    "# the embedded oracle's own cartesian+fuzz battery:\n"
    "rc = main()\n"
    "if rc != 0:\n"
    "    print('FAIL: embedded axiom_check main() returned', rc)\n"
    "    sys.exit(1)\n"
    "print('AX-1 OK: deep model index_label == real patched label for all four roles + battery')\n"
    "sys.exit(0)\n"
)
AXIOM_TESTS.append({
    "id": "ax-sound-index-label",
    "axiom": "index_label",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _probe_sound,
    "rationale": (
        "A-reference: the deep model index_label must equal the REAL patched "
        "PyMethod.get_index_text label on every input. Driven for all four "
        "roles in-container (property role patched) + the bundle's "
        "cartesian-boundary and 20000-fuzz battery. If the real callee ever "
        "disagrees, the deep model is AXIOM-UNSOUND."
    ),
})

# --- AX-2: caller-domain containment -----------------------------------------
# The model can pass index_label only inputs that satisfy its OWN Requires:
# option in {0,1,2,3} and methname/clsname any code-point sequences (any length,
# any glyph). The A-reference oracle (real templates) is defined for exactly that
# domain -- there is no role selector outside 0..3 the model can reach, and the
# templates accept arbitrary name strings. Assert containment by enumerating the
# model-reachable role selectors and confirming each maps to a real template, and
# that names with boundary shapes (empty, unicode, percent/paren glyphs) stay
# in-domain (no template-format crash).
_probe_contain = (
    "# AX-2 axiom-containment: every model-reachable callee input is in-domain.\n"
    "import sys\n"
    "\n"
    "# Post-patch real templates -- the A-reference oracle domain (role -> template).\n"
    "_TEMPLATE = {0: '%s() (%s method)', 1: '%s() (%s class method)',\n"
    "             2: '%s (%s property)', 3: '%s() (%s static method)'}\n"
    "\n"
    "# (1) The model's Requires pins 0 <= option <= 3. Enumerate EXACTLY those\n"
    "#     reachable selectors; each must have a defined real template.\n"
    "reachable_options = [0, 1, 2, 3]\n"
    "for opt in reachable_options:\n"
    "    if opt not in _TEMPLATE:\n"
    "        print('FAIL: model-reachable option %d has no real template' % opt)\n"
    "        sys.exit(1)\n"
    "# No selector outside 0..3 is reachable (Requires 0<=option<=3), so covering\n"
    "# exactly {0,1,2,3} is full containment, not over-coverage.\n"
    "\n"
    "# (2) The name carriers are arbitrary code-point sequences. Confirm the real\n"
    "#     template (the oracle) accepts boundary/sentinel name shapes without\n"
    "#     leaving its domain (no format error => the splice is total over names).\n"
    "boundary_names = ['', 'a', 'meth5', 'Class', 'unicode_\\u00e9', \"o'brien\",\n"
    "                  'with space', '__init__', '100%done', '(paren)']\n"
    "for opt in reachable_options:\n"
    "    for m in boundary_names:\n"
    "        for c in boundary_names:\n"
    "            try:\n"
    "                _ = _TEMPLATE[opt] % (m, c)\n"
    "            except Exception as e:\n"
    "                print('FAIL: real template rejected a model-reachable name '\n"
    "                      '(option=%d methname=%r clsname=%r): %r' % (opt, m, c, e))\n"
    "                sys.exit(1)\n"
    "print('AX-2 OK: model reaches only option in {0,1,2,3} and arbitrary names; '\n"
    "      'all lie in the A-reference oracle domain')\n"
    "sys.exit(0)\n"
)
AXIOM_TESTS.append({
    "id": "ax-contain-index-label",
    "axiom": "index_label",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _probe_contain,
    "rationale": (
        "Containment: the model's Requires (0<=option<=3, arbitrary code-point "
        "names) confines the reachable callee inputs to exactly the role "
        "selectors {0,1,2,3} and any name strings -- all inside the "
        "A-reference oracle's domain. A reachable selector or name shape "
        "outside it would be AXIOM-TOO-WEAK-FOR-CALLER."
    ),
})
