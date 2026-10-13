# properties.py — PBT falsification battery for django__django-14155.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   resolver_match_repr(func_path, func_repr, is_prebound, url_name, route) -> List[int]
#   builds ResolverMatch.__repr__'s single-line parenthesised description. ALL four
#   list inputs are READ-ONLY at Acc(list_pred(x), 1/2) (the rendering mutates
#   nothing it is given). One load-bearing postcondition clause pins the output:
#       ToSeq(Result()) == built_repr(ToSeq(func_path), ToSeq(func_repr),
#                                     is_prebound, ToSeq(url_name), ToSeq(route))
#   where built_repr is FULLY UNFOLDED (a GROUNDED function of the args):
#       lit_head + func_token(func_path,func_repr,is_prebound)
#                + lit_url_name + quoted(url_name)
#                + lit_route + quoted(route) + lit_tail
#   Two independently-fixed behaviours live in that clause:
#     (A) func_token: is_prebound ? func_repr : func_path   (partial naming)
#     (B) quoted(s) = quoted_with(s, delim(s)) — the text field delimited by
#         delim(s) (apostrophe 39, or double quote 34 when s holds an
#         apostrophe and no double quote), with esc_body marking each
#         backslash (92) and each occurrence of the delimiter by a preceding
#         backslash                                          (quoted rendering)
#
#   ungrounded-oracle echo: N/A. built_repr is NOT an opaque answer-key; it is a
#   concrete concatenation of @Pure literal constants with the SELECTED func token
#   and the QUOTED text fields, every piece a function of the args, fully unfolded
#   by the verifier. There is no wrong value an impl could "echo" — computing
#   built_repr correctly IS doing the work. Hence no echo case; instead the
#   soundness lane carries an honest structurally-different positive control. See
#   'assessment'.
#
# F2P: test_repr (url_name/route now QUOTED — behaviour B),
#      test_repr_functools_partial (a partial shows repr(self.func), not
#      'functools.partial' — behaviour A), test_resolver_match_on_request.
# No @ContractOnly consumed axioms (axioms region empty; meta.axioms == []); the
# func_token/quoted/built_repr deep models are A-reference, validated by
# axiom_check.py / G-AX, not consumed axioms — so AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-14155"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region fragments (must match model.py verbatim; _swap asserts
# uniqueness so any drift is caught at manifest-load).
# ---------------------------------------------------------------------------

# The func-selection block (behaviour A).
_SEL = """    if is_prebound:
        func = func_repr  # type: List[int]
    else:
        func = func_path"""

# The whole url_name quoted-rendering block (behaviour B): delimiter choice,
# the elementwise-marking fold, and the assembly of the delimited field.
_QURL = """    du = delim(ToSeq(url_name))
    ub = []  # type: List[int]
    i = len(url_name)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(url_name), 1 / 2))
        Invariant(Acc(list_pred(ub)))
        Invariant(0 <= i and i <= len(url_name))
        Invariant(du == delim(ToSeq(url_name)))
        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        cu = url_name[i - 1]
        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub
        i = i - 1
    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
    q_url = [du] + ub + [du]  # type: List[int]
    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
    Assert(du == delim(ToSeq(url_name)))
    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))"""

# The whole route quoted-rendering block (behaviour B).
_QROUTE = """    dr = delim(ToSeq(route))
    rb = []  # type: List[int]
    j = len(route)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(route), 1 / 2))
        Invariant(Acc(list_pred(rb)))
        Invariant(0 <= j and j <= len(route))
        Invariant(dr == delim(ToSeq(route)))
        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        cr = route[j - 1]
        Assert(ToSeq(route).drop(j - 1)[0] == cr)
        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
        if cr == 92:
            rb = [92, 92] + rb
        elif cr == dr:
            rb = [92, cr] + rb
        else:
            rb = [cr] + rb
        j = j - 1
    Assert(ToSeq(route).drop(0) == ToSeq(route))
    q_route = [dr] + rb + [dr]  # type: List[int]
    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
    Assert(dr == delim(ToSeq(route)))
    Assert(ToSeq(q_route) == quoted(ToSeq(route)))"""

# The declaration of the two loop-local code-point variables, which precedes
# the url_name block (a rival that drops both fold loops drops these too).
_CHARVARS = """    cu = 0
    cr = 0
"""

# The final assembly + return.
_ASSEMBLE = """    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
    return result"""


# === POSITIVE CONTROL (soundness) =========================================
# Branch-reorder of the func selection: handle the NON-prebound case first, the
# prebound case last. Same executable meaning; the func_token selection Assert is
# kept verbatim and still discharges (func_token unfolds to the same value either
# branch order). This is a pure reorder + local-variable reshape (directive-3
# safe: no loop-direction flip, no forward-append against a front-recursive fold,
# no dropped framing assert). If a faithful correct impl cannot verify here =>
# SPEC-TOO-STRONG.
_POS_SEL = """    if not is_prebound:
        func = func_path  # type: List[int]
    else:
        func = func_repr"""
POS_REORDER = _swap(_BASE, _SEL, _POS_SEL)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region — anything at module level enters the spec signature). So the
# admissibility check lives INSIDE the impl region: right after `# impl-start`,
# before any gold obligation, construct concrete F2P-shaped inputs and assert the
# Requires predicate (list_pred) is establishable on each. A self-recursive call
# would need extra plumbing; exercising the Requires-predicate directly is the
# faithful admissibility probe. If this cannot verify, the precondition is
# unsatisfiable for a normal input -> PRECOND-TOO-STRONG. Every following gold
# obligation is preserved verbatim.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: F2P-shaped inputs (a dotted func path, a non-empty
    # url_name like "no-kwargs", a regex route) establish the Requires predicate
    # at half permission. 'no' == [110, 111]; "x/" route == [120, 47].
    p_url = [110, 111]  # type: List[int]
    Assert(list_pred(p_url))
    Assert(len(p_url) == 2)
    p_route = [120, 47]  # type: List[int]
    Assert(list_pred(p_route))
    Assert(ToSeq(p_route)[1] == 47)"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION (MANDATORY: read-only Acc(.,1/2) inputs) ==============
# url_name (and func_repr/func_path/route) are held at Acc(list_pred(x), 1/2):
# READ-ONLY. A rival that WRITES to such an input cannot hold the write
# permission. Here the rival appends an apostrophe to `url_name` in place and
# then builds q_url from the mutated list — an attempt to produce the quoted
# rendering by mutating the caller's input rather than by allocating a fresh
# list. Every gold invariant/assert is kept verbatim so the rejection is
# attributable to the write: it MUST fail for INSUFFICIENT PERMISSION (the half
# fraction does not admit `url_name.append(...)`), NOT for a value mismatch.
# refinement: the real ResolverMatch.__repr__ takes self.url_name (a shared
# attribute) by reference; a patch that did `self.url_name += "'"` (or otherwise
# mutated the live attribute to fabricate the quoting) would corrupt the resolved
# match object for every subsequent reader — test_resolver_match_on_request reads
# match.url_name back after repr() and other call sites depend on it; such a
# patch would NOT resolve. A byte-fuzzer never thinks to mutate the input.
# rejection source: the PERMISSION SYSTEM — Requires(Acc(list_pred(url_name),1/2))
# grants only half, insufficient for url_name.append.
_FRAME_BLOCK = _swap(_QURL, """    du = delim(ToSeq(url_name))""",
                     """    # FRAME-MUTATION RIVAL: mutate the read-only url_name input
    # in place to fabricate the delimiter, instead of allocating fresh.
    url_name.append(39)
    du = delim(ToSeq(url_name))""")
FRAME_MUTATE_URLNAME = _swap(_BASE, _QURL, _FRAME_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- (A) selection-flip: ignore is_prebound, ALWAYS name by func_path.
# This is literally the PRE-PATCH behaviour (model_prepatch.py): func =
# func_path unconditionally, no partial handling.
# refinement: the faithful patch is the OLD `func = self._func_path` with no
# `isinstance(self.func, functools.partial)` branch — a partial-wrapped view
# would render as the unhelpful 'functools.partial' instead of repr(self.func).
# F2P test_repr_functools_partial asserts the partial shows
# f"functools.partial({views.empty_view!r}, template_name=...)"; the old code
# fails it and does NOT resolve (it is the bug being fixed).
# rejection source: the postcondition func_token selection — when is_prebound the
# spec requires func_repr but this impl emits func_path, so
# ToSeq(Result()) != built_repr(...).
_FLIP_SEL = """    if is_prebound:
        func = func_path  # type: List[int]
    else:
        func = func_path"""
SEL_ALWAYS_PATH = _swap(_BASE, _SEL, _FLIP_SEL)


# --- (A') inverted selection: use func_repr when NOT prebound and func_path
# when prebound (the func_token choice exactly backwards). Wrong on BOTH
# is_prebound values' rendered token.
# refinement: a real patch writing the isinstance test inverted —
# `func = self._func_path if isinstance(self.func, functools.partial) else
# repr(self.func)` — would name a plain dotted view by its repr(<function ...>)
# and a partial by 'functools.partial'; both test_repr and
# test_repr_functools_partial assert the opposite tokens and would fail — NOT
# resolve.
# rejection source: the postcondition func_token selection (both branches wrong).
_INV_SEL = """    if is_prebound:
        func = func_path  # type: List[int]
    else:
        func = func_repr"""
SEL_INVERTED = _swap(_BASE, _SEL, _INV_SEL)


# --- (B) unquoted url_name AND route: emit the bare values (the PRE-PATCH %s).
# This is model_prepatch_2.py: q_url = url_name, q_route = route.
# refinement: the faithful patch keeps the OLD `url_name=%s, ... route=%s` format
# (no str->repr change) — the text fields render unquoted. F2P test_repr asserts
# url_name='no-kwargs' and route='^no_kwargs/([0-9]+)/([0-9]+)/$' (with the
# apostrophes); the old code emits them bare and FAILS — does NOT resolve.
# rejection source: the postcondition quoted() rendering — built_repr requires
# quoted(url_name)/quoted(route) ([39]+s+[39]) but the impl emits bare s.
_BARE_QURL = """    q_url = url_name  # type: List[int]
    Assert(list_pred(url_name))"""
_BARE_QROUTE = """    q_route = route  # type: List[int]
    Assert(list_pred(route))"""
BARE_TEXT_FIELDS = _swap(
    _swap(_swap(_BASE, _QURL, _BARE_QURL), _QROUTE, _BARE_QROUTE),
    _CHARVARS, "")


# --- PARTIAL-DOMAIN: quote url_name correctly but leave ROUTE bare. Correct on
# every input whose route is empty (quoted("") and "" both render as the trailing
# 'route=' with nothing after... NO — even empty route differs: quoted("") = "''"
# vs "" = ""). So it diverges on EVERY input but is "half right": it gets the
# url_name field exactly right and only the route field wrong, so a value-proxy
# that only checked url_name would miss it.
# refinement: a real patch that changed ONLY the url_name field to %r and forgot
# the route field (`url_name=%r, ... route=%s`) would quote the match name but not
# the route. F2P test_repr asserts route='^no_kwargs/([0-9]+)/([0-9]+)/$' WITH the
# apostrophes; an unquoted route fails that assertion — NOT resolve.
# rejection source: the postcondition quoted(route) sub-term of built_repr.
PARTIAL_ROUTE_BARE = _swap(_BASE, _QROUTE, _BARE_QROUTE)


# --- WRONG QUOTE CHARACTER: wrap url_name in DOUBLE quotes (34) instead of the
# apostrophe (39). Structurally identical (delimited text field) but the wrong
# delimiter. A double-mask that only checked "is it wrapped in some quote" would
# pass; the spec pins the exact apostrophe code point.
# refinement: a real patch that rendered the text field with a hand-written
# '"%s"' % s instead of %r (CPython repr uses the apostrophe for these
# apostrophe-free values) would emit double quotes. F2P test_repr asserts
# url_name='no-kwargs' (single quotes); double quotes fail it — NOT resolve.
# rejection source: quoted(url_name) == [39]+url_name+[39] (apostrophe 39, not 34).
_DQ_QURL = """    q_url = [34] + url_name + [34]  # type: List[int]
    Assert(list_pred(url_name))"""
WRONG_QUOTE_CHAR = _swap(_swap(_BASE, _QURL, _DQ_QURL), _CHARVARS,
                         """    cr = 0
""")


# --- NO-MARKING: choose the delimiter correctly and fold over every code point,
# but copy each one through unchanged — no backslash before a backslash, none
# before an embedded delimiter. This is the rendering the model would produce if
# the elementwise marking were dropped while everything else stayed right, so it
# is correct on every value containing neither a backslash nor its own delimiter
# and diverges only on the ones that do (a Django route like '^\\d+/$' is
# exactly such a value).
_NOMARK_QURL = _swap(_QURL, """        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub""",
                     """        ub = [cu] + ub""")
NO_MARKING_URLNAME = _swap(_BASE, _QURL, _NOMARK_QURL)


# --- DELIM-ALWAYS-APOSTROPHE: mark correctly, but always delimit with the
# apostrophe, never switching to the double quote for a value that contains an
# apostrophe and no double quote. Diverges exactly on that class.
_APOS_QURL = _swap(_QURL, """    du = delim(ToSeq(url_name))""",
                   """    du = 39""")
DELIM_ALWAYS_APOSTROPHE = _swap(_BASE, _QURL, _APOS_QURL)


# --- FIELD-ORDER SWAP: assemble route's field where url_name's should go and
# vice-versa (swap the two label/value pairs). Each piece is individually
# well-formed; only their ORDER in the concatenation is wrong.
# refinement: a real patch with the two %r placeholders / arguments transposed
# (`url_name=%r ... route=%r` fed (route, url_name)) would print the route under
# the url_name label and vice-versa. F2P test_repr pins the exact field order
# (url_name='no-kwargs', route='^...$'); the transposition fails — NOT resolve.
# rejection source: built_repr's fixed concatenation ORDER
# (lit_url_name + quoted(url_name) + lit_route + quoted(route)).
_SWAP_ASSEMBLE = """    result = head + func + seg_url_name + q_route + seg_route + q_url + [41]  # type: List[int]
    return result"""
FIELD_ORDER_SWAP = _swap(_BASE, _ASSEMBLE, _SWAP_ASSEMBLE)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (func selection branch "
        "reordered: non-prebound case first, prebound last) keeping the func_token "
        "selection Assert verbatim — must verify, else SPEC-TOO-STRONG. Pure branch "
        "reorder + local reshape (directive-3 safe: no loop flip / forward-append).",
    },
    {
        "id": "admiss-fields",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "an in-region admissibility probe constructs F2P-shaped list "
        "inputs ([110,111]='no', [120,47]='x/') and asserts list_pred holds on each "
        "at half permission — the Requires(Acc(list_pred(x),1/2)) must admit a normal "
        "input, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-urlname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUTATE_URLNAME,
        "refinement": "the real __repr__ takes self.url_name by reference; a patch "
        "mutating the live attribute (e.g. self.url_name += \"'\") to fabricate the "
        "quoting would corrupt the resolved match for every later reader — "
        "test_resolver_match_on_request reads match.url_name back after repr() and "
        "would observe the corruption; such a patch would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: Requires(Acc(list_pred("
        "url_name),1/2)) grants only half permission, insufficient for "
        "url_name.append(39). MUST fail for insufficient permission, NOT a value "
        "mismatch (every gold invariant kept verbatim). #1 weakness class; a "
        "byte-fuzzer never mutates the read-only input.",
    },
    {
        "id": "sel-always-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEL_ALWAYS_PATH,
        "refinement": "this is the PRE-PATCH behaviour (model_prepatch.py): "
        "`func = self._func_path` unconditionally, no functools.partial branch. A "
        "partial-wrapped view renders as the unhelpful 'functools.partial'. F2P "
        "test_repr_functools_partial asserts the partial shows repr(self.func); the "
        "old code fails it — does NOT resolve (it is the bug being fixed).",
        "rationale": "rejected by the postcondition func_token selection: when "
        "is_prebound the spec requires func_repr but this impl emits func_path, so "
        "ToSeq(Result()) != built_repr(...). (behaviour A.)",
    },
    {
        "id": "sel-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEL_INVERTED,
        "refinement": "a real patch with the isinstance test inverted "
        "(func = _func_path if partial else repr(func)) names a plain dotted view by "
        "repr(<function ...>) and a partial by 'functools.partial'; BOTH test_repr "
        "and test_repr_functools_partial assert the opposite tokens — NOT resolve.",
        "rationale": "rejected by the func_token selection on BOTH is_prebound values "
        "(the choice is exactly backwards). (behaviour A, value-level.)",
    },
    {
        "id": "bare-text-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": BARE_TEXT_FIELDS,
        "refinement": "this is the PRE-PATCH behaviour (model_prepatch_2.py): the OLD "
        "`url_name=%s, ... route=%s` format, text fields unquoted. F2P test_repr "
        "asserts url_name='no-kwargs' and route='^no_kwargs/([0-9]+)/([0-9]+)/$' WITH "
        "apostrophes; the old code emits them bare and fails — does NOT resolve.",
        "rationale": "rejected by the postcondition quoted() rendering: built_repr "
        "requires quoted(url_name)=[39]+url_name+[39] and quoted(route) but the impl "
        "emits the bare values. (behaviour B.)",
    },
    {
        "id": "partial-route-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_ROUTE_BARE,
        "refinement": "a real patch that changed ONLY url_name to %r and forgot route "
        "(`url_name=%r, ... route=%s`) quotes the match name but not the route. F2P "
        "test_repr asserts route='^no_kwargs/([0-9]+)/([0-9]+)/$' WITH apostrophes; an "
        "unquoted route fails that assertion — NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct on the url_name field, diverges only on "
        "the route field. Rejected by the quoted(route) sub-term of built_repr; a "
        "value-proxy checking only url_name would miss it.",
    },
    {
        "id": "wrong-quote-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_QUOTE_CHAR,
        "refinement": "a real patch hand-writing '\"%s\"' % s (double quotes) instead "
        "of %r would wrap the apostrophe-free text fields in double quotes; CPython "
        "repr uses the apostrophe for these values. F2P test_repr asserts "
        "url_name='no-kwargs' (single quotes) — double quotes fail it, NOT resolve.",
        "rationale": "value-level double-mask: rejected by quoted(url_name) pinning "
        "the delimiter delim() chooses — the apostrophe [39] for a value holding no "
        "apostrophe — not [34]. A proxy that only checked 'wrapped in some quote' "
        "would pass. Also drops the elementwise marking.",
    },
    {
        "id": "no-marking-urlname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": NO_MARKING_URLNAME,
        "refinement": "a real patch that delimited the text field by hand — wrapping "
        "the value in the right quote character but copying its code points through "
        "unchanged — renders a match name containing a backslash or an embedded "
        "delimiter without the marking the quoted form requires, so the rendering can "
        "no longer be read back. Django route patterns carry regex escapes (\\\\d, \\\\w, "
        "\\\\.) constantly, so this is the ordinary input to this function, and the "
        "rendering it produces differs from the required one — NOT resolve.",
        "rationale": "PARTIAL-DOMAIN, and the sharpest one: agrees with the spec on "
        "every value containing neither a backslash nor its own delimiter (including "
        "every F2P-tested value), and diverges only on the ones that do. Rejected by "
        "the esc_body sub-term of quoted(url_name), which marks code point 92 and each "
        "occurrence of the delimiter.",
    },
    {
        "id": "delim-always-apostrophe",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DELIM_ALWAYS_APOSTROPHE,
        "refinement": "a real patch that always delimited with the apostrophe, never "
        "switching to the double quote for a value that itself contains an apostrophe "
        "and no double quote, renders such a match name with a different delimiter (and "
        "different marking) than the quoted form requires — NOT resolve.",
        "rationale": "PARTIAL-DOMAIN on the delimiter CHOICE rather than the marking: "
        "correct on every value with no apostrophe, wrong exactly on the class delim() "
        "sends to [34]. Rejected by the delim() sub-term of quoted(url_name).",
    },
    {
        "id": "field-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FIELD_ORDER_SWAP,
        "refinement": "a real patch with the two %r placeholders/arguments transposed "
        "prints the route under the url_name label and vice-versa. F2P test_repr pins "
        "the exact field order (url_name='no-kwargs', then route='^...$'); the "
        "transposition fails — NOT resolve.",
        "rationale": "rejected by built_repr's fixed concatenation ORDER "
        "(lit_url_name + quoted(url_name) + lit_route + quoted(route)); each piece is "
        "well-formed but their order in the result is wrong. (structural.)",
    },
]


# No @ContractOnly consumed axioms and no consumed deep-model axioms to probe in
# Docker. The axioms region is EMPTY (meta.json axioms == []); func_token /
# quoted / built_repr are A-reference deep models already validated against real
# CPython repr / %-interpolation by axiom_check.py (G-AX): exhaustive safe-char
# sweep + 20000 fuzz (quoted) + 5005 repr cases (built_repr) + collection-field
# %r==%s identity, exit 0 host-side. There is nothing for the axiom lane to run.
AXIOM_TESTS = []
