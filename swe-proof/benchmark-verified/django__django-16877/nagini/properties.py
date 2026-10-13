"""PBT falsification battery for django__django-16877.

Instance under attack: the new Django template filter ``escapeseq`` =
``[conditional_escape(obj) for obj in value]``. The twin-artifact models it as

  * ``escape_each(value: List[Elem]) -> List[Elem]``  (the sequence map),
  * ``escape_when_unsafe_item(item: Elem) -> Elem``   (per-item conditional escape),
  * ``escape_codepoints(text: PSeq[int]) -> PSeq[int]`` (verified deep escape),
  * ``escaped_seq`` / ``entity`` (the @Pure per-code-point fold, A-reference to
    the real ``html.escape``, validated out-of-band by axiom_check.py / G-AX).

Defended surface (what the spec actually pins):
  - **READ-ONLY inputs.** ``escape_when_unsafe_item`` holds ``item`` at 1/4
    permission (``Acc(item.chars, 1/4) and Acc(item.is_safe, 1/4)``); ``escape_each``
    holds ``value`` at ``Acc(list_pred(value), 1/2)`` + per-element ``1/4``. An impl
    that WRITES to an input to fake the postcondition must be rejected for
    INSUFFICIENT PERMISSION  =>  frame-mutation lane (MANDATORY here).
  - **Per-branch content pins** (the load-bearing clauses):
      Implies(item.is_safe,     Result().chars == item.chars)        # no re-escape
      Implies(not item.is_safe, Result().chars == escaped_seq(...))  # escape once
      Result().is_safe                                               # always safe
    plus, in ``escape_each``: length/order alignment
      len(Result()) == len(value) and per-index Forall pinning each output item.
  - **Grounded oracle.** ``escaped_seq`` is a @Pure FUNCTION OF THE INPUT
    (``item.chars``), fully unfolded by the front-recursion. It is NOT an opaque
    answer-key: an impl that "echoes" ``escaped_seq(item.chars)`` is EXACTLY the
    correct escape, so there is no *wrong* echo to build (see ASSESSMENT). The
    ungrounded-oracle-echo lane therefore degenerates to an honest cheapest-impl
    positive control, included below.

Authoring discipline: every SPEC variant is built by region-surgery on model.py
(``_swap`` edits ONLY text strictly inside a ``# impl-start`` / ``# impl-end``
region), so the frozen spec is byte-identical (same_spec holds) and every reject
is attributable to the impl, never to a spec edit.

No ``@ContractOnly`` axioms exist in this bundle (meta.axioms == []); the single
kind-A construct is the A-reference deep model ``escaped_seq``. We carry ONE
axiom-soundness probe that re-runs the REAL ``html.escape`` callee (the routine
``conditional_escape`` invokes) and asserts it equals the deep model on the
caller-reachable code-point domain -- because ``verify => resolve`` depends on
that equality holding. (axiom_check.py is the bundle's own G-AX oracle; this
probe reuses its logic, self-contained, stdlib-only.)
"""
from pathlib import Path

INSTANCE = "django__django-16877"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (verbatim text strictly inside impl regions of model.py).
# ---------------------------------------------------------------------------

# escape_when_unsafe_item impl region (between its # impl-start / # impl-end):
_EWUI_IMPL = """    if item.is_safe:
        return Elem(item.chars, True)
    return Elem(escape_codepoints(item.chars), True)"""

# escape_each impl region body head (the result-init + loop setup), unique:
_EE_INIT = """    result = []  # type: List[Elem]
    i = 0
    while i < len(value):"""

# escape_codepoints impl region (its backward fold), unique anchor on the body:
_EC_IMPL = """    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        result = entity(c) + result
        i = i - 1
    return result"""


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = []

# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness, expect=verify)
#     A structurally-different but CORRECT impl. We reorder the branch in
#     escape_when_unsafe_item (handle the NOT-safe case first, then the safe
#     passthrough) -- a different control-flow shape that is observationally the
#     same map. The spec (postconditions) is untouched; the gold proof stays
#     valid because each branch still establishes its own clause. If a faithful
#     correct impl could NOT verify, the spec would be SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_EWUI_REORDER = """    if not item.is_safe:
        return Elem(escape_codepoints(item.chars), True)
    return Elem(item.chars, True)"""

SPEC_TESTS.append({
    "id": "pos-control-branch-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _EWUI_IMPL, _EWUI_REORDER),
    "rationale": (
        "A correct impl with the two conditional_escape branches written in the "
        "opposite order (escape-then-passthrough vs passthrough-then-escape) must "
        "still verify: each branch independently discharges its clause "
        "(not-safe -> escaped_seq; safe -> identity; both -> is_safe). It needs no "
        "new lemma (no fold direction flip), so it cannot fail for a proof reason. "
        "If it failed, SPEC-TOO-STRONG."),
})

# ---------------------------------------------------------------------------
# (1b) POSITIVE CONTROL on escape_each (soundness, expect=verify)
#     Same correct map, different executable shape: bind the per-item result to
#     a typed local before appending (instead of appending the call directly).
#     Loop invariants are kept VERBATIM (directive: keep the gold proof
#     obligations). Only the executable shape changes.
# ---------------------------------------------------------------------------
_EE_LOOP_ORIG = """        # invariants-end
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result"""
_EE_LOOP_LOCAL = """        # invariants-end
        marked = escape_when_unsafe_item(value[i])  # type: Elem
        result.append(marked)
        i = i + 1
    return result"""

SPEC_TESTS.append({
    "id": "pos-control-local-bind",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _EE_LOOP_ORIG, _EE_LOOP_LOCAL),
    "rationale": (
        "Binding escape_when_unsafe_item(value[i]) to a typed local 'marked' and "
        "appending the local is the same length/order-preserving map; the gold "
        "loop invariants are kept verbatim so the proof still goes through. A "
        "correct restructure must verify (else SPEC-TOO-STRONG)."),
})

# ---------------------------------------------------------------------------
# (2) ADMISSIBILITY (expect=verify)
#     Inside escape_each's impl region, build a fresh F2P-shaped item ("x&y",
#     NOT yet safe -- exactly the test_basic input a=["x&y","<p>"]) and call
#     escape_when_unsafe_item on it, asserting its postcondition is usable. This
#     proves the per-item precondition Acc(item.chars,1/4)&Acc(item.is_safe,1/4)
#     ADMITS a normal input and the postcondition yields the escaped content. If
#     this could not verify, PRECOND-TOO-STRONG. The loop + invariants below are
#     kept verbatim so escape_each still satisfies its own postcondition.
# ---------------------------------------------------------------------------
_EE_ADMISS = """    result = []  # type: List[Elem]
    # admissibility: a fresh F2P-shaped item ("x&y", not yet safe) is in-domain
    # for escape_when_unsafe_item's precondition, and its postcondition gives the
    # escaped content (x & y -> x &amp; y).
    probe = Elem(PSeq(120, 38, 121), False)
    escaped = escape_when_unsafe_item(probe)
    Assert(escaped.is_safe)
    Assert(escaped.chars == escaped_seq(PSeq(120, 38, 121)))
    i = 0
    while i < len(value):"""

SPEC_TESTS.append({
    "id": "admiss-fresh-unsafe-item",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _EE_INIT, _EE_ADMISS),
    "rationale": (
        "Constructing a fresh Elem(PSeq('x&y'), is_safe=False) and calling "
        "escape_when_unsafe_item on it establishes the callee's 1/4-permission "
        "precondition for a real F2P input and lets the asserts use its "
        "postcondition. If the precondition could not be established for a "
        "normal input, PRECOND-TOO-STRONG."),
})

# ---------------------------------------------------------------------------
# (3) FRAME-MUTATION on escape_when_unsafe_item (uniqueness, expect=reject)
#     MANDATORY: item is a READ-ONLY input (Acc(item.chars,1/4)). A rival tries
#     to satisfy the postcondition by WRITING the escaped content back into the
#     INPUT item and returning the input -- i.e. mutate-in-place. With only 1/4
#     permission this write is rejected for INSUFFICIENT PERMISSION. The spec is
#     byte-identical; the rejection is attributable purely to the write.
#     (A faithful real patch CANNOT mutate the caller's object in place: the gold
#     `[conditional_escape(obj) for obj in value]` returns NEW SafeString objects
#     and leaves the input items untouched; an in-place-mutating escapeseq would
#     corrupt the caller's list and fail the F2P render -- it would not resolve.)
# ---------------------------------------------------------------------------
_EWUI_FRAME = """    if item.is_safe:
        return item
    item.chars = escape_codepoints(item.chars)
    return item"""

SPEC_TESTS.append({
    "id": "frame-mutate-input-item",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EWUI_IMPL, _EWUI_FRAME),
    "refinement": (
        "The faithful real version of 'mutate the input in place' would assign "
        "the escaped string back onto the caller's own sequence elements rather "
        "than returning fresh SafeString objects. The gold filter returns a NEW "
        "list of NEW SafeString objects and never touches the input; an "
        "in-place-mutating escapeseq would (a) not mark the result safe via a "
        "fresh SafeString so autoescape-off rendering differs, and (b) destroy "
        "the caller's data -- the F2P tests (which keep using `a`) would not "
        "render 'x&amp;y, &lt;p&gt; -- x&y, <p>'. So it would NOT resolve."),
    "rationale": (
        "item is held at 1/4 permission, so `item.chars = ...` requires write "
        "permission the precondition does not grant => rejected for INSUFFICIENT "
        "PERMISSION (the permission system, not a value clause). This is the #1 "
        "weakness class a byte-fuzzer never finds."),
})

# ---------------------------------------------------------------------------
# (3b) FRAME-MUTATION on escape_each (uniqueness, expect=reject)
#     value is READ-ONLY: Acc(list_pred(value),1/2) + per-element 1/4. A rival
#     tries to mutate an input element's content before returning the result.
#     1/4 element permission forbids the write => INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------
_EE_FRAME = """        # invariants-end
        value[i].chars = escape_codepoints(value[i].chars)
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result"""

SPEC_TESTS.append({
    "id": "frame-mutate-input-list-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EE_LOOP_ORIG, _EE_FRAME),
    "refinement": (
        "Writing escaped content back onto value[i] mutates the CALLER's list "
        "elements. The gold comprehension never mutates its input; a version that "
        "did would corrupt `a` (re-used across the F2P assertions) and would not "
        "produce the expected joined output, so it would NOT resolve."),
    "rationale": (
        "value's elements are held at 1/4 permission per the Forall precondition, "
        "so `value[i].chars = ...` is rejected for INSUFFICIENT PERMISSION."),
})

# ---------------------------------------------------------------------------
# (4) PARTIAL-DOMAIN — safe-passthrough only on the FIRST element (reject)
#     A rival that escapes the WRONG branch for one sub-domain: it correctly
#     escapes unsafe items, but for an ALREADY-SAFE item it re-escapes the
#     content instead of passing it through. This is the model_prepatch.py bug
#     (double-escape) -- it is wrong precisely on the safe sub-domain. It must be
#     rejected by clause `Implies(item.is_safe, Result().chars == item.chars)`.
# ---------------------------------------------------------------------------
_EWUI_REESCAPE_SAFE = """    if item.is_safe:
        return Elem(escape_codepoints(item.chars), True)
    return Elem(escape_codepoints(item.chars), True)"""

SPEC_TESTS.append({
    "id": "partial-domain-reescape-safe",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EWUI_IMPL, _EWUI_REESCAPE_SAFE),
    "refinement": (
        "Escaping every item unconditionally (the `escape` instead of "
        "`conditional_escape` mistake = model_prepatch.py) DOUBLE-escapes "
        "already-safe items. On the F2P input b=[mark_safe('x&y'), mark_safe('<p>')] "
        "the expected output is the UNCHANGED 'x&y, <p>', but this rival renders "
        "'x&amp;y, &lt;p&gt;'. So its faithful patch FAILS test_basic / "
        "test_autoescape_off => NOT resolve."),
    "rationale": (
        "Wrong on the is_safe sub-domain only; rejected by "
        "`Implies(item.is_safe, Result().chars == item.chars)` in the "
        "post-conditions of escape_when_unsafe_item."),
})

# ---------------------------------------------------------------------------
# (4b) PARTIAL-DOMAIN — escape skipped for unsafe items (reject)
#     The dual sub-domain bug (model_prepatch_2.py / the safeseq mistake): it
#     marks every item safe but never escapes, so unsafe items keep raw HTML
#     characters. Rejected by the unsafe-escape clause.
# ---------------------------------------------------------------------------
_EWUI_NOESCAPE = """    if item.is_safe:
        return Elem(item.chars, True)
    return Elem(item.chars, True)"""

SPEC_TESTS.append({
    "id": "partial-domain-skip-escape-unsafe",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EWUI_IMPL, _EWUI_NOESCAPE),
    "refinement": (
        "Merely marking items safe without escaping (the safeseq mistake = "
        "model_prepatch_2.py). On the F2P input a=['x&y','<p>'] the expected "
        "output is the ESCAPED 'x&amp;y, &lt;p&gt;', but this rival renders the "
        "raw 'x&y, <p>'. So its faithful patch FAILS every F2P test => NOT resolve."),
    "rationale": (
        "Wrong on the not-is_safe sub-domain; rejected by "
        "`Implies(not item.is_safe, Result().chars == escaped_seq(item.chars))`."),
})

# ---------------------------------------------------------------------------
# (5) VALUE-LEVEL / ARITY — drop the last element (uniqueness, expect=reject)
#     A rival whose escape_each is correct per-item but truncates the output by
#     one (stops the loop one short), violating the order/arity alignment. This
#     is the classic "value proxy that drops a disagreeing index" attack at the
#     sequence level: the per-item content for the survivors is right, but the
#     length and per-index alignment is wrong. Rejected by
#     `len(Result()) == len(value)` (the loop would also fail its own
#     `len(result) == i` exit reasoning, so it cannot verify the postcondition).
# ---------------------------------------------------------------------------
_EE_LOOP_TRUNC = """        # invariants-end
        if i + 1 < len(value):
            result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result"""

SPEC_TESTS.append({
    "id": "arity-drop-last-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EE_LOOP_ORIG, _EE_LOOP_TRUNC),
    "refinement": (
        "Dropping the final item makes `[conditional_escape(obj) for obj in value]` "
        "return one element short. On the F2P input a=['x&y','<p>'] (then joined "
        "with ', ') the expected output is 'x&amp;y, &lt;p&gt;' but a truncated "
        "list renders only 'x&amp;y'. So its faithful patch FAILS the F2P join "
        "assertions => NOT resolve."),
    "rationale": (
        "Skipping the last append breaks `len(Result()) == len(value)` and the "
        "per-index Forall alignment of escape_each's postcondition; the loop also "
        "cannot re-establish `len(result) == i`, so it does not verify."),
})

# ---------------------------------------------------------------------------
# (6) CONTROL-FLOW / SAFETY-FLAG — return item NOT marked safe (uniqueness,
#     reject). A rival that escapes correctly but forgets to mark the result
#     safe (is_safe=False). Content is right, but the safety flag is the new
#     behaviour's whole point (escapeseq vs autoescape-off). Rejected by
#     `Result().is_safe`. This is the safety-state analogue of a control-flow
#     difference the per-content value alone would miss.
# ---------------------------------------------------------------------------
_EWUI_NOTSAFE = """    if item.is_safe:
        return Elem(item.chars, False)
    return Elem(escape_codepoints(item.chars), False)"""

SPEC_TESTS.append({
    "id": "flag-result-not-marked-safe",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EWUI_IMPL, _EWUI_NOTSAFE),
    "refinement": (
        "conditional_escape returns a SafeString (is_safe). A version that escaped "
        "content but returned a PLAIN (unsafe) string would be re-escaped by the "
        "autoescape-ON path: the F2P test_basic (autoescape on) would render "
        "'x&amp;amp;y' (double-escaped) instead of 'x&amp;y'. So its faithful "
        "patch FAILS test_basic => NOT resolve."),
    "rationale": (
        "Rejected by `Ensures(Result().is_safe)` in escape_when_unsafe_item "
        "(and propagated by escape_each's per-index is_safe Forall)."),
})

# ---------------------------------------------------------------------------
# (7) WRONG-ENTITY (supporting near-miss, uniqueness, expect=reject)
#     A targeted divergence inside the deep escape: emit the apostrophe as the
#     DECIMAL reference &#39; instead of the required hex &#x27;. This is the
#     exact discriminator the spec defends (the ' -> &#x27; clause) and the one
#     real-world ambiguity for this filter (markupsafe uses &#39;, Django/CPython
#     html.escape uses &#x27;). Rejected by the escaped_seq pin.
# ---------------------------------------------------------------------------
_EC_WRONG_APOS = """    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        if c == 39:
            result = PSeq(38, 35, 51, 57, 59) + result
        else:
            result = entity(c) + result
        i = i - 1
    return result"""

SPEC_TESTS.append({
    "id": "wrong-apostrophe-decimal-ref",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EC_IMPL, _EC_WRONG_APOS),
    "refinement": (
        "Emitting the apostrophe as decimal &#39; (PSeq 38,35,51,57,59) instead of "
        "hex &#x27; matches markupsafe but NOT CPython html.escape (which Django "
        "calls). On an input containing an apostrophe the rendered output would be "
        "&#39; where the real callee produces &#x27;; that differs from what "
        "html.escape yields, so a faithful patch using this escaper would diverge "
        "from conditional_escape and would NOT match the harness oracle. (G-AX "
        "pins html.escape's &#x27;.)"),
    "rationale": (
        "On a code point 39 the result is PSeq(38,35,51,57,59), but escaped_seq(39) "
        "= entity(39) = PSeq(38,35,120,50,55,59); the loop invariant "
        "`result == escaped_seq(text.drop(i))` fails to re-establish, so the "
        "escape_codepoints postcondition `Result() == escaped_seq(text)` is "
        "rejected."),
})

# ---------------------------------------------------------------------------
# (8) AMPERSAND-LAST DOUBLE-ESCAPE (supporting near-miss, uniqueness, reject)
#     The single subtlety html.escape calls out ("Must be done first!"): if you
#     escaped '<' '>' etc. before '&', the '&' in the emitted entities would be
#     re-escaped (double escaping). escaped_seq encodes ampersand-first. A rival
#     escape_codepoints that emits &amp; then re-runs the &-pass over its own
#     output would diverge. We model the divergence directly: when escaping '<'
#     emit the WRONG double-escaped form '&amp;lt;' (as if '&' were escaped after
#     '<'). Rejected by the escaped_seq pin.
# ---------------------------------------------------------------------------
_EC_AMP_LAST = """    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        if c == 60:
            result = PSeq(38, 97, 109, 112, 59, 108, 116, 59) + result
        else:
            result = entity(c) + result
        i = i - 1
    return result"""

SPEC_TESTS.append({
    "id": "ampersand-last-double-escape-lt",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EC_IMPL, _EC_AMP_LAST),
    "refinement": (
        "Emitting '<' as '&amp;lt;' (the double-escaped form you get if '&' is "
        "replaced AFTER '<') is exactly the bug html.escape's '&'-first ordering "
        "prevents. On F2P input '<p>' the expected escape is '&lt;p&gt;' but this "
        "renders '&amp;lt;p&amp;gt;'; a faithful patch with this ordering would "
        "FAIL every F2P test => NOT resolve."),
    "rationale": (
        "entity(60) = seq_lt() = PSeq(38,108,116,59); emitting "
        "PSeq(38,97,109,112,59,108,116,59) breaks the loop invariant "
        "`result == escaped_seq(text.drop(i))`, so escape_codepoints' "
        "postcondition is rejected."),
})


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.axioms == [] -> NO @ContractOnly axiom is consumed by the proof. The one
# kind-A construct is the A-reference deep model escaped_seq, whose equality to
# the real callee (CPython html.escape, which conditional_escape invokes) is what
# `verify => resolve` rests on. We carry ONE axiom-soundness probe that EXECUTES
# the real html.escape callee (never scrapes source) and asserts:
#   (i)   escaped_seq == html.escape (quote=True, Django's default) over the
#         caller-reachable code-point domain (boundary + fuzz), AND
#   (ii)  containment: every code point the model can pass through entity()/the
#         fold is a valid in-domain input to html.escape (i.e. the model never
#         constructs an input html.escape rejects -- it cannot: any Unicode code
#         point is in html.escape's domain). This is the A-reference soundness +
#         caller-domain check.
# The probe is stdlib-only (imports `html`) and reuses axiom_check.py's logic.

_AXIOM_SOUNDNESS_PROBE = r'''
import html
import random
import sys

# deep model reference (lock-step with model.py escaped_seq / entity)
_ENTITY = {
    38: [38, 97, 109, 112, 59],        # & -> &amp;
    60: [38, 108, 116, 59],            # < -> &lt;
    62: [38, 103, 116, 59],            # > -> &gt;
    34: [38, 113, 117, 111, 116, 59],  # " -> &quot;
    39: [38, 35, 120, 50, 55, 59],     # ' -> &#x27;
}

def escaped_seq(codepoints):
    out = []
    for c in codepoints:
        out.extend(_ENTITY.get(c, [c]))
    return out

def check(s):
    # (i) SOUNDNESS: real callee == deep model on this input
    observed = [ord(ch) for ch in html.escape(s)]          # REAL html.escape, quote=True
    expected = escaped_seq([ord(ch) for ch in s])          # deep model
    if observed != expected:
        print("AXIOM-UNSOUND on %r: html.escape -> %r, deep model -> %r"
              % (s, observed, expected))
        sys.exit(1)

significant = ['&', '<', '>', '"', "'"]
ordinary = ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
            'e', 'q', 'u', 'o', 't', 'l', 'g', 'm', 'p']

boundary = [""]
boundary += significant
boundary += [c + c for c in significant]
boundary += ["".join(significant), "".join(reversed(significant))]
boundary += [
    "a&b<c>d\"e'f",
    "x=1&amp;y=&lt;2&gt;",
    "&amp;", "&#39;", "&#x27;", "&quot;",
    "Joe's Crab Shack",
    "<script>alert('xss')</script>",
    "Can't find my keys",
    "!$&'()*+,;=~:@,",
    "x&y", "<p>",   # the exact F2P items
]
for s in boundary:
    check(s)

# (ii) CONTAINMENT + soundness over the fuzz domain. The model's entity() maps
# EVERY code point (the five significant + identity for all others); html.escape
# accepts ANY str, so every caller-reachable input is in-domain. Fuzz to confirm
# the real callee never diverges from the per-code-point substitution, including
# code points OUTSIDE the alphabet (identity branch).
rng = random.Random(16877)
alphabet = significant + ordinary
for _ in range(20000):
    n = rng.randint(0, 24)
    s = "".join(rng.choice(alphabet) for _ in range(n))
    check(s)

# stress the identity branch over arbitrary BMP + astral code points the model
# would pass through unchanged (entity(c) = PSeq(c) for c not in the five).
for _ in range(5000):
    cps = [rng.randint(0, 0x10FFFF) for _ in range(rng.randint(0, 8))]
    cps = [c for c in cps if not (0xD800 <= c <= 0xDFFF)]  # skip lone surrogates
    s = "".join(chr(c) for c in cps)
    check(s)

print("AXIOM-SOUND/COVERED: deep model escaped_seq == real html.escape "
      "(quote=True) on 25 boundary + 20000 alphabet fuzz + 5000 arbitrary-"
      "code-point inputs; every caller-reachable code point is in html.escape's "
      "domain (identity branch confirmed).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-ref-escaped_seq-vs-html-escape",
        "axiom": "escaped_seq (A-reference deep model of html.escape)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_SOUNDNESS_PROBE,
        "rationale": (
            "verify => resolve rests on the deep model escaped_seq equalling the "
            "REAL escaper conditional_escape calls (CPython html.escape, "
            "quote=True). The probe EXECUTES html.escape (never scrapes source) and "
            "asserts equality on boundary + fuzz + arbitrary-code-point inputs, and "
            "confirms html.escape's domain contains every caller-reachable code "
            "point (the identity branch). Any divergence => AXIOM-UNSOUND."),
    },
]
