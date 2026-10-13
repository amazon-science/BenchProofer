"""PBT falsification battery for sphinx-doc__sphinx-8593.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TEST is a full model.py variant that shares the FROZEN spec byte-for-byte
(only text inside a # impl-start / # impl-end region is edited, guaranteed by
region-surgery via _swap) and is checked by Nagini verify + markers.same_spec.
Each AXIOM_TEST is a self-contained probe run in the instance Docker image
against the REAL callee.

Defended surface (read off model.py):

  member_effective_doc(attr_doc: List[int], value_doc: List[int]) -> List[int]
    Requires Acc(list_pred(attr_doc), 1/2)   # READ-ONLY input
    Requires Acc(list_pred(value_doc), 1/2)  # READ-ONLY input
    Ensures  Acc(list_pred(attr_doc), 1/2)   # half perm returned => still read-only
    Ensures  Acc(list_pred(value_doc), 1/2)
    Ensures  Acc(list_pred(Result()))        # fresh full-perm result
    Ensures  ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc))
        where effective_doc(a,v) := a if len(a)>0 else v   (@Pure, fully unfolded)

  keep_module_member(name_underscored: bool, name_special: bool, attr_doc, value_doc,
                     want_all: bool, private_mode: int, name_selected: bool) -> bool
    Requires Acc(list_pred(attr_doc), 1/2)   # READ-ONLY input
    Requires Acc(list_pred(value_doc), 1/2)  # READ-ONLY input
    Requires private_mode in {0,1,2}
    Requires len(attr_doc) > 0 or len(value_doc) > 0   # documented member only
    Requires not name_special                # reserved-form names out of slice
    Ensures  Acc(list_pred(attr_doc), 1/2)
    Ensures  Acc(list_pred(value_doc), 1/2)
    Ensures  Result() == ((not want_all)
                          or (not is_private(name_underscored, effective_doc(...)))
                          or in_private_selection(private_mode, name_selected))
    Ensures  Implies(meta_class(effective_doc(...)) == PUBLIC, Result())   # discriminating

ORACLE GROUNDING: the load-bearing postcondition of member_effective_doc pins
ToSeq(Result()) to effective_doc(...), a @Pure function FULLY GROUNDED in the two
inputs (no opaque answer key). keep_module_member's postcondition is parametric
in meta_class — the discriminating clause Implies(meta_class(effective_doc(...))
==PUBLIC, Result()) holds for ANY classifier; meta_class is never pinned to a
value in the spec. So there is NO ungrounded answer-key to ECHO: a "cheapest
impl" that uses the @Pure helpers IS doing the modeled work. The
ungrounded-oracle-echo class therefore does not apply (see assessment); in its
place we ship honest cheapest-impl positive controls + the real partial-domain
attacks (the two prepatch reverts) which a tight spec must reject.

READ-ONLY INPUTS: every modeled function carries attr_doc and value_doc at half
permission (Acc(.,1/2) Required AND Ensured). The FRAME-MUTATION probe is
therefore MANDATORY and present for both functions.

AXIOM lane: one @ContractOnly axiom meta_class (A-consumed). We ship
axiom-soundness (real extract_metadata never violates Ensures (1) result in
{0,1,2}, (2) empty->NONE) and axiom-containment (every doc block the model can
feed to meta_class is a str, exactly the callee's Requires(True) domain).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8593"
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
# Gold impl regions (verbatim, between # impl-start / # impl-end). Every variant
# edits ONLY one of these, so spec_view (=> same_spec) is preserved.
# ---------------------------------------------------------------------------

# member_effective_doc gold impl
_MED_GOLD = (
    "    if len(attr_doc) > 0:\n"
    "        result = list(attr_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(value_doc)\n"
    "    return result\n"
)
assert _MED_GOLD in _BASE, "member_effective_doc gold impl drifted from model.py"

# keep_module_member gold impl
_KMM_GOLD = (
    "    doc = member_effective_doc(attr_doc, value_doc)\n"
    "    private = is_private(name_underscored, ToSeq(doc))\n"
    "    if not want_all:\n"
    "        keep = True\n"
    "    elif not private:\n"
    "        keep = True\n"
    "    else:\n"
    "        keep = in_private_selection(private_mode, name_selected)\n"
    "    return keep\n"
)
assert _KMM_GOLD in _BASE, "keep_module_member gold impl drifted from model.py"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls.
# ===========================================================================

# (1) member_effective_doc: branch-reorder — handle the empty-attr case first.
#     Same value mapping, inverted guard; no loop/lemma => no proof-trigger risk.
_MED_POS_REORDER = (
    "    if len(attr_doc) == 0:\n"
    "        result = list(value_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(attr_doc)\n"
    "    return result\n"
)

# (2) member_effective_doc: local-variable reshape — bind the chosen source to a
#     typed local, then copy it once. Different data shape, identical result.
_MED_POS_LOCALS = (
    "    src = attr_doc  # type: List[int]\n"
    "    if len(attr_doc) == 0:\n"
    "        src = value_doc\n"
    "    result = list(src)  # type: List[int]\n"
    "    return result\n"
)

# (3) keep_module_member: collapse the if/elif/else chain into the single
#     boolean expression that IS the postcondition formula. Keeps the
#     member_effective_doc call (establishes ToSeq(doc)==effective_doc(...)) and
#     the is_private call (so the proof obligations are intact), only the control
#     shape differs. A correct impl => must verify, else SPEC-TOO-STRONG.
_KMM_POS_BOOL = (
    "    doc = member_effective_doc(attr_doc, value_doc)\n"
    "    private = is_private(name_underscored, ToSeq(doc))\n"
    "    keep = (not want_all) or (not private) or in_private_selection(private_mode, name_selected)  # type: bool\n"
    "    return keep\n"
)


# ===========================================================================
# ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# A tautology Assert on each modeled predicate confirms the spec is well-defined
# on the in-domain input under exactly the half permission held; the gold flow
# then runs. If the precondition were too strong the Assert/flow would fail to
# verify => PRECOND-TOO-STRONG.
# ===========================================================================

# member_effective_doc: assert the @Pure selector is total on the held input.
_MED_ADMISS = (
    "    # admissibility: ToSeq is readable under the half permission held, and\n"
    "    # the @Pure effective_doc is total on the in-domain (attr_doc, value_doc).\n"
    "    Assert(effective_doc(ToSeq(attr_doc), ToSeq(value_doc)) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))\n"
    "    if len(attr_doc) > 0:\n"
    "        result = list(attr_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(value_doc)\n"
    "    return result\n"
)

# keep_module_member: assert every @Pure model used in the postcondition is
# well-defined on the F2P-shaped input (private_mode in {0,1,2} held by Requires).
_KMM_ADMISS = (
    "    # admissibility: under Requires(private_mode in {0,1,2}) and the half\n"
    "    # permissions held, every @Pure model in the postcondition is total here.\n"
    "    Assert(in_private_selection(private_mode, name_selected) == in_private_selection(private_mode, name_selected))\n"
    "    doc = member_effective_doc(attr_doc, value_doc)\n"
    "    private = is_private(name_underscored, ToSeq(doc))\n"
    "    if not want_all:\n"
    "        keep = True\n"
    "    elif not private:\n"
    "        keep = True\n"
    "    else:\n"
    "        keep = in_private_selection(private_mode, name_selected)\n"
    "    return keep\n"
)


# ===========================================================================
# FRAME-MUTATION (MANDATORY: read-only inputs) — write a half-permission input
# to satisfy a postcondition vacuously. Must REJECT for insufficient permission
# (mutating a list needs full Acc(list_pred(.)); only 1/2 is held). The gold
# value clauses are kept so the rejection is attributable to the WRITE.
# ===========================================================================

# (a) member_effective_doc: clear attr_doc, then the empty-attr branch returns
#     value_doc. If the write were permitted this trivially routes every input
#     through the value_doc branch; it is NOT (only 1/2 perm on attr_doc).
_MED_FRAME_ATTR = (
    "    attr_doc.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n"
    "    result = list(value_doc)  # type: List[int]\n"
    "    return result\n"
)

# (b) member_effective_doc: append to value_doc (mutate the other read-only
#     input) before copying attr_doc. Same vacuity attempt on the other field.
_MED_FRAME_VALUE = (
    "    value_doc.append(0)              # ILLEGAL write: only Acc(list_pred(value_doc),1/2) held\n"
    "    if len(attr_doc) > 0:\n"
    "        result = list(attr_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(value_doc)\n"
    "    return result\n"
)

# (c) keep_module_member: write attr_doc before classifying. Mutating the
#     read-only input to force a classification is rejected for insufficient perm.
_KMM_FRAME_ATTR = (
    "    attr_doc.append(0)               # ILLEGAL write: only Acc(list_pred(attr_doc),1/2) held\n"
    "    doc = member_effective_doc(attr_doc, value_doc)\n"
    "    private = is_private(name_underscored, ToSeq(doc))\n"
    "    if not want_all:\n"
    "        keep = True\n"
    "    elif not private:\n"
    "        keep = True\n"
    "    else:\n"
    "        keep = in_private_selection(private_mode, name_selected)\n"
    "    return keep\n"
)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN — same-spec WRONG impls that must REJECT.
# ===========================================================================

# (i) member_effective_doc: ALWAYS return value_doc (ignore attr_doc). This is
#     EXACTLY model_prepatch.py (the pre-patch flow: a module member arrived
#     without its inline attribute documentation). Wrong on the sub-domain
#     len(attr_doc)>0 and attr_doc != value_doc.
_MED_WRONG_ALWAYS_VALUE = (
    "    result = list(value_doc)  # type: List[int]\n"
    "    return result\n"
)

# (ii) member_effective_doc: prefer attr_doc only when it is LONGER than one
#      code point — diverges on a length-1 attribute documentation block. A
#      partial-domain near-miss correct on most inputs but wrong on len==1.
_MED_WRONG_LEN1 = (
    "    if len(attr_doc) > 1:\n"
    "        result = list(attr_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(value_doc)\n"
    "    return result\n"
)

# (iii) member_effective_doc: INVERTED precedence — value_doc when attr_doc is
#       present, attr_doc when absent. Wrong across the whole discriminating
#       domain.
_MED_WRONG_SWAP = (
    "    if len(attr_doc) > 0:\n"
    "        result = list(value_doc)  # type: List[int]\n"
    "    else:\n"
    "        result = list(attr_doc)\n"
    "    return result\n"
)

# (iv) keep_module_member: classify on value_doc (the empty intrinsic doc)
#      instead of the effective doc. This is EXACTLY model_prepatch_2.py — the
#      pre-patch flow where the attribute documentation never reached the
#      classifier. Wrong whenever the public/private marker lives in attr_doc.
_KMM_WRONG_CLASSIFY_VALUE = (
    "    private = is_private(name_underscored, ToSeq(value_doc))\n"
    "    if not want_all:\n"
    "        keep = True\n"
    "    elif not private:\n"
    "        keep = True\n"
    "    else:\n"
    "        keep = in_private_selection(private_mode, name_selected)\n"
    "    return keep\n"
)

# (v) keep_module_member: drop the want_all guard — never keep a private member
#     even when not in all-members mode. Wrong on the (not want_all) sub-domain
#     where a private member must still be kept.
_KMM_WRONG_DROP_WANTALL = (
    "    doc = member_effective_doc(attr_doc, value_doc)\n"
    "    private = is_private(name_underscored, ToSeq(doc))\n"
    "    if not private:\n"
    "        keep = True\n"
    "    else:\n"
    "        keep = in_private_selection(private_mode, name_selected)\n"
    "    return keep\n"
)

# (vi) keep_module_member: treat every member as kept (ignore visibility). This
#      verifies the easy clauses but violates the retention formula on a private,
#      unselected, all-members member.
_KMM_WRONG_ALWAYS_KEEP = (
    "    keep = True  # type: bool\n"
    "    return keep\n"
)


SPEC_TESTS = [
    # ---- positive controls (soundness) ------------------------------------
    {
        "id": "med-pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _MED_GOLD, _MED_POS_REORDER),
        "rationale": "member_effective_doc with the empty-attr branch handled first; "
                     "same value mapping (ToSeq(Result())==effective_doc(...)), no "
                     "loop/lemma => must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "med-pos-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _MED_GOLD, _MED_POS_LOCALS),
        "rationale": "member_effective_doc local-variable reshape (bind the chosen "
                     "source, copy once); different data shape, identical result => "
                     "must verify.",
    },
    {
        "id": "kmm-pos-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_POS_BOOL),
        "rationale": "keep_module_member collapsed to the single boolean expression "
                     "that IS the postcondition formula; keeps the member_effective_doc "
                     "and is_private calls (proof obligations intact), only the control "
                     "shape differs => must verify, else SPEC-TOO-STRONG.",
    },
    # ---- admissibility ----------------------------------------------------
    {
        "id": "med-admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _MED_GOLD, _MED_ADMISS),
        "rationale": "the precondition (half perm on both List[int] inputs) must admit "
                     "a normal F2P-shaped input; the tautology Assert proves the @Pure "
                     "effective_doc is total on the in-domain pair under the held "
                     "permission, then the gold flow runs. Else PRECOND-TOO-STRONG.",
    },
    {
        "id": "kmm-admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_ADMISS),
        "rationale": "the precondition (half perm on both inputs, private_mode in "
                     "{0,1,2}) must admit an F2P-shaped input; the tautology Assert "
                     "proves in_private_selection is total on the in-domain mode, then "
                     "the gold flow runs. Else PRECOND-TOO-STRONG.",
    },
    # ---- frame mutation (MANDATORY: read-only inputs) ---------------------
    {
        "id": "med-frame-mut-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MED_GOLD, _MED_FRAME_ATTR),
        "refinement": "A real patch that WRITES to the joined attribute-doc list and "
                      "returns the value's intrinsic doc would discard the inline "
                      "documentation of every member — including _PUBLIC_CONSTANT's "
                      "':meta public:' — so the F2P test_private_field (which expects "
                      "_PUBLIC_CONSTANT rendered with ':meta public:') would NOT "
                      "resolve, and it also mutates the analyzer's shared attr_docs.",
        "rationale": "REJECT for insufficient permission: attr_doc.append(0) needs "
                     "full Acc(list_pred(attr_doc)) but only Acc(.,1/2) is held "
                     "(Requires). The permission system, not a value clause, kills "
                     "this. #1 class. (`clear()` would say the same thing, but Nagini's "
                     "front end does not translate it, so the rejection would be the "
                     "type checker's rather than the prover's -- 43c6680f6.)",
    },
    {
        "id": "med-frame-mut-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MED_GOLD, _MED_FRAME_VALUE),
        "refinement": "Appending to the value's intrinsic-doc list mutates a caller "
                      "object (the value's __doc__-derived sequence) that the gold "
                      "patch never writes; getdoc(member) is a read-only observation. "
                      "A faithful patch never mutates it, so this is not gold behaviour "
                      "and would not resolve.",
        "rationale": "REJECT for insufficient permission: value_doc.append(0) needs "
                     "full Acc(list_pred(value_doc)) but only Acc(.,1/2) is held. "
                     "Permission system.",
    },
    {
        "id": "kmm-frame-mut-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_FRAME_ATTR),
        "refinement": "Writing to the attribute documentation before classifying "
                      "makes an EMPTY attr_doc non-empty, so the member is classified "
                      "on a fabricated doc instead of the value's intrinsic doc and an "
                      "undocumented underscored member is kept rather than dropped; it "
                      "also mutates the analyzer's shared attr_docs, which the gold "
                      "patch never writes. Not gold behaviour, so it would NOT resolve.",
        "rationale": "REJECT for insufficient permission: attr_doc.append(0) needs "
                     "full Acc(list_pred(attr_doc)) but only Acc(.,1/2) is held "
                     "(Requires). Permission system. (`clear()` says the same thing but "
                     "is not translated by Nagini's front end -- 43c6680f6.)",
    },
    # ---- partial-domain / uniqueness --------------------------------------
    {
        "id": "med-wrong-always-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MED_GOLD, _MED_WRONG_ALWAYS_VALUE),
        "refinement": "This is model_prepatch.py exactly: the member arrives WITHOUT "
                      "its inline attribute documentation (effective doc = the value's "
                      "empty intrinsic doc). _PUBLIC_CONSTANT (=None, doc ':meta "
                      "public:' only in attr_doc) then has empty effective doc, so its "
                      "':meta public:' never renders and test_private_field FAILS. "
                      "Does NOT resolve.",
        "rationale": "REJECT by ToSeq(Result())==effective_doc(ToSeq(attr_doc),"
                     "ToSeq(value_doc)): when len(attr_doc)>0 the effective doc is "
                     "attr_doc, but this returns value_doc — violates the load-bearing "
                     "postcondition.",
    },
    {
        "id": "med-wrong-len1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MED_GOLD, _MED_WRONG_LEN1),
        "refinement": "Preferring attr_doc only when longer than one code point drops "
                      "a single-character attribute documentation block (e.g. a "
                      "one-glyph doc). The real callee always uses the joined "
                      "attribute doc when non-empty regardless of length, so a "
                      "len-1-doc member would silently lose its documentation — a "
                      "behavioural divergence that does not resolve.",
        "rationale": "REJECT by ToSeq(Result())==effective_doc(...): effective_doc "
                     "selects attr_doc whenever len(attr_doc)>0 (incl. len==1); "
                     "returning value_doc on a length-1 attr_doc violates it.",
    },
    {
        "id": "med-wrong-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MED_GOLD, _MED_WRONG_SWAP),
        "refinement": "Inverted precedence (value when attr present, attr when "
                      "absent) is the opposite of the gold rule: the attribute "
                      "documentation must take precedence. Every documented member "
                      "would render the wrong text; the F2P expects the attribute doc, "
                      "so it does not resolve.",
        "rationale": "REJECT by ToSeq(Result())==effective_doc(...): when "
                     "len(attr_doc)>0 effective_doc==attr_doc but this returns "
                     "value_doc, and when len(attr_doc)==0 effective_doc==value_doc but "
                     "this returns attr_doc.",
    },
    {
        "id": "kmm-wrong-classify-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_WRONG_CLASSIFY_VALUE),
        "refinement": "This is model_prepatch_2.py exactly: classify on the value's "
                      "intrinsic (empty) doc instead of the effective doc. "
                      "_PUBLIC_CONSTANT carries ':meta public:' only in attr_doc, so "
                      "classifying on value_doc gives NONE and the underscored name "
                      "makes it private => dropped under all-members. test_private_field "
                      "FAILS; does NOT resolve.",
        "rationale": "REJECT by Result()==((not want_all) or (not is_private("
                     "name_underscored, effective_doc(...))) or in_private_selection): "
                     "is_private is pinned to the EFFECTIVE doc, not value_doc; "
                     "classifying on value_doc diverges whenever the marker is in "
                     "attr_doc (and the discriminating Implies(meta_class(effective_doc)"
                     "==PUBLIC, Result()) clause also breaks).",
    },
    {
        "id": "kmm-wrong-drop-wantall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_WRONG_DROP_WANTALL),
        "refinement": "Dropping the (not want_all) guard makes a private member be "
                      "subject to the private-members selection even when all-members "
                      "mode is OFF; the real filter_members keeps every explicitly "
                      "requested member when not want_all. A private member requested "
                      "by :members: would be wrongly dropped, diverging from gold.",
        "rationale": "REJECT by Result()==((not want_all) or ...): when want_all is "
                     "False the result must be True, but this impl returns "
                     "in_private_selection(...) for a private member => violates the "
                     "first disjunct.",
    },
    {
        "id": "kmm-wrong-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _KMM_GOLD, _KMM_WRONG_ALWAYS_KEEP),
        "refinement": "Keeping every member ignores the private-members selection: "
                      "PRIVATE_CONSTANT (':meta private:') must be DROPPED under "
                      "all-members unless explicitly selected. test_private_field "
                      "(default options) expects PRIVATE_CONSTANT absent; always-keep "
                      "renders it, so the test FAILS and it does not resolve.",
        "rationale": "REJECT by Result()==((not want_all) or (not is_private(...)) or "
                     "in_private_selection(...)): for a private member with want_all "
                     "True and in_private_selection False the formula is False, but "
                     "this returns True => violates the retention postcondition.",
    },
]


# ===========================================================================
# AXIOM lane — meta_class (the one @ContractOnly A-consumed axiom).
# The runner mounts ONLY the probe at /work, so axiom_check.py is NOT in the
# container (pilot bug #6): we host-read its source at load time and embed it.
# Files are opened utf-8 already; the probe runs the embedded routine on the
# REAL sphinx.util.docstrings.extract_metadata (pilot bug #4: CALL, never scrape).
# ===========================================================================

# ---- axiom-soundness: the real classifier never violates the Ensures --------
_AX_SOUND_PROBE = (
    "# axiom-soundness probe for sphinx-doc__sphinx-8593 meta_class.\n"
    "# Re-runs the bundle's G-AX oracle (axiom_check.py) against the REAL\n"
    "# sphinx.util.docstrings.extract_metadata inside the instance image,\n"
    "# asserting both Ensures: (1) Result() in {NONE,PUBLIC,PRIVATE}; (2) an\n"
    "# empty/None documentation block -> NONE. Exit 0 iff sound.\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__embedded_axiom_check__'}\n"
    "try:\n"
    "    exec(compile(_SRC, 'axiom_check_embedded.py', 'exec'), g)\n"
    "    rc = g['main']()\n"
    "except AssertionError as e:\n"
    "    print('AXIOM-UNSOUND: real extract_metadata violates a meta_class Ensures:', e)\n"
    "    sys.exit(1)\n"
    "except ImportError as e:\n"
    "    print('PROBE-ENV: sphinx.util.docstrings missing:', e)\n"
    "    sys.exit(1)\n"
    "print('meta_class axiom SOUND vs real extract_metadata (boundary + 20000 fuzz).')\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

# ---- axiom-containment: every doc block the model reaches is in meta_class's
# Requires(True) domain (i.e. a str — including the empty string for which the
# axiom additionally guarantees NONE). The model only ever passes the EFFECTIVE
# documentation (attr_doc when non-empty else value_doc), both of which are
# documentation strings; the real classifier must accept each without error and
# must classify the empty string as NONE (the one nontrivial containment edge).
# ----------------------------------------------------------------------------
_AX_CONTAIN_PROBE = (
    "# axiom-containment probe for sphinx-doc__sphinx-8593 meta_class.\n"
    "# meta_class's Requires is True (domain = every documentation string). The\n"
    "# model only ever feeds it the EFFECTIVE documentation of a module member:\n"
    "# the joined inline attribute-doc string when non-empty, else the value's\n"
    "# intrinsic doc string (possibly empty). Both are plain strings, so each is\n"
    "# trivially inside Requires(True). The only nontrivial axiom edge is the\n"
    "# empty-doc clause (len(doc)==0 -> NONE), which a model member with NO\n"
    "# documentation reaches; we assert the real callee honours it on every\n"
    "# caller-reachable shape (empty, the F2P markers, joined multi-line attr\n"
    "# docs, prose, whitespace). A reachable input outside the covered domain or\n"
    "# an empty doc not classified NONE => AXIOM-TOO-WEAK-FOR-CALLER.\n"
    "import sys\n"
    "try:\n"
    "    from sphinx.util.docstrings import extract_metadata\n"
    "except ImportError as e:\n"
    "    print('PROBE-ENV: sphinx.util.docstrings missing:', e)\n"
    "    sys.exit(1)\n"
    "NONE, PUBLIC, PRIVATE = 0, 1, 2\n"
    "def meta_class_real(doc):\n"
    "    metadata = extract_metadata(doc) if doc else {}\n"
    "    if 'private' in metadata: return PRIVATE\n"
    "    if 'public' in metadata: return PUBLIC\n"
    "    return NONE\n"
    "# every documentation shape the model can feed meta_class (the effective doc):\n"
    "reachable = [\n"
    "    '',                                  # no documentation -> must be NONE\n"
    "    ':meta public:',                     # _PUBLIC_CONSTANT inline attr doc\n"
    "    ':meta private:',                    # PRIVATE_CONSTANT inline attr doc\n"
    "    '\\n'.join([':meta public:']),       # joined single-line attr doc\n"
    "    '\\n'.join(['summary.', '', ':meta public:']),  # joined multi-line attr doc\n"
    "    'a value docstring with no marker',  # intrinsic doc fallback\n"
    "    '   ',                               # whitespace-only intrinsic doc\n"
    "]\n"
    "ok = True\n"
    "for doc in reachable:\n"
    "    try:\n"
    "        r = meta_class_real(doc)\n"
    "    except Exception as e:\n"
    "        print('AXIOM-TOO-WEAK-FOR-CALLER: reachable doc %r raised %r '\n"
    "              '(outside Requires(True))' % (doc, e))\n"
    "        ok = False; continue\n"
    "    if r not in (NONE, PUBLIC, PRIVATE):\n"
    "        print('CONTAINMENT: doc %r classified %r outside {0,1,2}' % (doc, r))\n"
    "        ok = False\n"
    "    if len(doc) == 0 and r != NONE:\n"
    "        print('AXIOM edge violated: empty doc classified %r, axiom guarantees NONE' % r)\n"
    "        ok = False\n"
    "if not ok:\n"
    "    sys.exit(1)\n"
    "print('CONTAINMENT OK: every caller-reachable doc block is in meta_class '\n"
    "      'Requires(True); empty doc -> NONE honoured.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-meta-class-sound",
        "axiom": "meta_class",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "meta_class is the only @ContractOnly axiom; if the real "
                     "extract_metadata (+ public/private branch) ever returns a value "
                     "outside {0,1,2} or classifies an empty/None block as non-NONE, "
                     "the axiom is AXIOM-UNSOUND. Probe executes the real callee on 13 "
                     "boundary + 20000 fuzz blocks (never scrapes source).",
    },
    {
        "id": "ax-meta-class-contain",
        "axiom": "meta_class",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "meta_class's Requires is True (every doc string); the model only "
                     "feeds it the effective documentation (joined attr doc or intrinsic "
                     "doc, both strings, incl. the empty string). Each caller-reachable "
                     "shape must lie in the domain and the empty-doc edge must give "
                     "NONE; otherwise AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
