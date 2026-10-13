"""properties.py — PBT falsification battery for django__django-12308.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS entry is a FULL model.py variant that shares the frozen spec
(axioms / pure / pre-conditions / post-conditions / signatures byte-identical —
markers.same_spec) and differs ONLY inside an `# impl-start` / `# impl-end`
region (region surgery via `_swap`, which fails loudly on drift or non-unique
anchors). The runner re-runs the Nagini verifier on each variant:
  expect="verify"  passes iff (same_spec AND verifies);
  expect="reject"  passes iff (same_spec AND does NOT verify).

DEFENDED SURFACE (what this spec actually pins):
  - `display_structured_value(value, empty, content, present, encodable)` — the
    rendered dispatch. value (j_pred, 1/2), empty (list_pred, 1/2), content
    (list_pred, 1/2) are ALL READ-ONLY (fractional permission). Three load-
    bearing postconditions:
      not present                -> ToSeq(Result()) == ToSeq(empty)
                                     (`present` is FALSE only when nothing is
                                      stored; an EMPTY stored value is present)
      present and encodable       -> ToSeq(Result()) == interchange_form(value)   <-- discriminating
                                     (`encodable` is TRUE only when the value is
                                      both offered to the encoder and expressible)
      present and not encodable   -> ToSeq(Result()) == fallback_form(ToSeq(content))
                                     (fallback_form = identity: the
                                      general-purpose display text produced for
                                      the value passes through UNCHANGED; this
                                      arm covers BOTH the inexpressible value
                                      and the empty stored value that is never
                                      offered to the encoder)
  - `serialize(node)` / `serialize_list(head)` — the structural recursive
    interchange serialiser, output pinned to node_body / ser_list (the GROUNDED
    pure folds over the JNode tree).  node / head are READ-ONLY (j_pred, 1/2).
  - `append_all(result, src)` — result is WRITABLE (full list_pred), src is
    READ-ONLY (list_pred, 1/2).
  - `append_escaped(result, src)` / `append_esc_char(result, c)` — the TOKEN
    FORM: what goes between the two U+0022 delimiters is not the token's own
    code points but each code point's form in the interchange alphabet, output
    pinned to `esc_seq` / `esc_char` (U+0022 and U+005C each as U+005C followed
    by themselves; U+0008/U+0009/U+000A/U+000C/U+000D as U+005C + b/t/n/f/r;
    every other code point outside U+0020..U+007E as U+005C, U+0075 and four
    lowercase hexadecimal digits most significant first, one above U+FFFF as
    the two such forms of its surrogate halves).  Same frame as `append_all`.
  - TOTALITY (all six functions): every one carries a `MustTerminate` measure
    in its pre-conditions region, `display_structured_value` /
    `serialize` / `serialize_list` bounded by `j_size` (how much value there is
    left to walk), so the three postconditions above are claims about a result
    that ARRIVES rather than claims discharged vacuously on a path that is never
    reached.  A rival that walks forever on an admissible value -- by
    self-calling without shrinking the value, or by looping on a guard that is
    never falsified -- fails the obligation instead of proving the display.

The discriminating clause is STRUCTURAL: an encodable value must render as the
full recursive interchange serialisation (brackets/braces, ", " separators,
double-quote U+0022 = 34 on every token and key), NOT the host-language
single-quote (U+0027 = 39) printout, and NOT a single-token wrap of the whole
value.  It is also LEXICAL: inside the delimiters the token is laid down in the
interchange alphabet, so the clause pins the whole rendered text and not only
its skeleton -- 'a"b' renders as "a\\"b" (six code points), never as "a"b"
(five), and a token carrying U+005C, a control position or a non-ASCII code
point renders in that code point's own form.  The four F2P values: 'a' -> "a",
['a','b'] -> ["a", "b"],
{'a':{'b':'c'}} -> {"a": {"b": "c"}}, and the tuple-keyed dict (TypeError) ->
the general-purpose display text passed through UNCHANGED (fallback_form =
identity; that text's own string tokens are single-quote delimited internally).

There are NO @ContractOnly axioms (meta.axioms == []); the two callees are
A-reference deep models validated == real json.dumps / str by axiom_check.py
(G-AX), never consumed.  => AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "django__django-12308"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — every input of display_structured_value is
#    read-only at 1/2 permission).  In the `not present` branch the gold impl
#    copies `empty` into a fresh owned list and returns the copy.  This rival
#    instead MUTATES the read-only `empty` (appends a copy of itself onto it and
#    returns it) to satisfy ToSeq(Result()) == ToSeq(empty) vacuously.  `empty`
#    is held at Acc(list_pred(empty), 1/2); `empty.append(...)` needs FULL
#    list_pred(empty) => the verifier rejects for INSUFFICIENT PERMISSION.  Gold
#    invariants for the loop are kept verbatim so the rejection is attributable
#    solely to the write.
# ---------------------------------------------------------------------------
_FRAME_OLD = """    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(empty))
            Invariant(ToSeq(result) == ToSeq(empty).take(j))
            Invariant(MustTerminate(len(empty) - j + 1))
            # invariants-end
            result.append(empty[j])
            j = j + 1
        return result"""
_FRAME_NEW = """    if not present:
        # FRAME-MUTATION rival: write back into the read-only `empty` instead of
        # copying into a fresh list.  `empty` is held at 1/2 permission; the
        # mutating `empty.append(...)` needs FULL list_pred(empty) => REJECT for
        # insufficient permission.
        j = 0
        n0 = len(empty)
        while j < n0:
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(0 <= j and j <= n0)
            Invariant(MustTerminate(n0 - j + 1))
            # invariants-end
            empty.append(empty[j])   # write to a read-only (1/2-perm) input
            j = j + 1
        return empty"""

# ---------------------------------------------------------------------------
# 2. POSITIVE CONTROL A (soundness) — structurally DIFFERENT but CORRECT
#    serialize: the four-way kind dispatch is re-ORDERED (ARRAY, OBJECT, STRING,
#    MEMBER last) using elif/else instead of the gold STRING-first fall-through
#    ifs.  Every gold proof obligation it still needs is kept VERBATIM: the
#    per-branch Unfold/Fold(Acc(j_pred(node),1/2)) pairing and the per-branch
#    Assert(ToSeq(...) == node_body(node)) framing pin.  Branch-reorder keeps the
#    gold proof valid (no induction lemma needed).  NOTE: `j_pred` does NOT
#    constrain `kind` to {0,1,2,3}, and `node_body`'s pure conditional has the
#    MEMBER case as its final `else` (kind==3 == "none of 0/1/2").  So the rival's
#    catch-all branch MUST be the MEMBER form (matching node_body's else arm);
#    STRING gets its own explicit `elif node.kind == 0` so the positive kind==0
#    fact reduces node_body to the STRING arm.  A bare STRING-last `else` would
#    lose that fact and could not match node_body (proof gap, not SPEC-TOO-
#    STRONG).  MUST verify (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_POS_SER_OLD = """    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out
    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result
    if node.kind == 2:                          # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result2) == node_body(node))
        return result2
    # MEMBER: "key": value
    result3 = [34]  # type: List[int]
    append_escaped(result3, node.text)
    result3.append(34)
    result3.append(58)
    result3.append(32)
    vbody = serialize_list(node.inner)
    append_all(result3, vbody)
    Fold(Acc(j_pred(node), 1 / 2))
    Assert(ToSeq(result3) == node_body(node))
    return result3"""
_POS_SER_NEW = """    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 1:                          # ARRAY: [ elements ] (reordered first)
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result
    elif node.kind == 2:                        # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result2) == node_body(node))
        return result2
    elif node.kind == 0:                        # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out
    else:                                       # MEMBER: "key": value (reordered last)
        result3 = [34]  # type: List[int]
        append_escaped(result3, node.text)
        result3.append(34)
        result3.append(58)
        result3.append(32)
        vbody = serialize_list(node.inner)
        append_all(result3, vbody)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result3) == node_body(node))
        return result3"""

# ---------------------------------------------------------------------------
# 3. POSITIVE CONTROL B (soundness) — structurally DIFFERENT but CORRECT
#    display_structured_value `not present` loop: same copy semantics, reshaped
#    with a precomputed length local and a different loop variable, gold
#    invariant kept verbatim (rephrased over the same prefix).  MUST verify.
# ---------------------------------------------------------------------------
_POS_DSV_OLD = """    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(empty))
            Invariant(ToSeq(result) == ToSeq(empty).take(j))
            Invariant(MustTerminate(len(empty) - j + 1))
            # invariants-end
            result.append(empty[j])
            j = j + 1
        return result"""
_POS_DSV_NEW = """    if not present:
        # POSITIVE CONTROL: same fresh-copy semantics, reshaped (precomputed
        # length local + different index name).  Gold invariant kept verbatim.
        out0 = []  # type: List[int]
        k = 0
        ln = len(empty)
        while k < ln:
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(out0)))
            Invariant(ln == len(empty))
            Invariant(0 <= k and k <= len(empty))
            Invariant(ToSeq(out0) == ToSeq(empty).take(k))
            Invariant(MustTerminate(len(empty) - k + 1))
            # invariants-end
            out0.append(empty[k])
            k = k + 1
        return out0"""

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN A (uniqueness) — serialize_list DROPS the ", " (44,32)
#    sibling separator.  CORRECT on empty / singleton lists (['a'] -> ["a"],
#    [] -> []) but DIVERGES on multi-element lists: ['a','b'] would serialise as
#    ["a""b"] instead of ["a", "b"].  Fails ToSeq(result) == ser_list(head)
#    (ser_list inserts PSeq(44,32) before every non-head sibling).  expect=reject.
# ---------------------------------------------------------------------------
_PD_SEP_OLD = """    # tail: the rest of the sibling list, comma-and-space separated.
    if head.nxt is not None:
        result.append(44)
        result.append(32)
        rest = serialize_list(head.nxt)
        append_all(result, rest)"""
_PD_SEP_NEW = """    # PARTIAL-DOMAIN rival: drop the ", " (44,32) separator before the tail.
    # Correct for 0- and 1-element lists, wrong for >=2 elements.
    if head.nxt is not None:
        rest = serialize_list(head.nxt)
        append_all(result, rest)"""

# ---------------------------------------------------------------------------
# 5. WRONG-DELIMITER (uniqueness) — serialize STRING branch uses the single
#    quote U+0027 (39) instead of the interchange double quote U+0022 (34).
#    This is the host-language PRINTOUT delimiter, not the interchange one:
#    'a' would render as 'a' (the fallback text form), the EXACT pre-patch behaviour the
#    F2P forbids (F2P expects "a").  Fails ToSeq(out) == node_body(node)
#    (node_body STRING = PSeq(34) + text + PSeq(34)).  expect=reject.
# ---------------------------------------------------------------------------
_WD_OLD = """    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out"""
_WD_NEW = """    if node.kind == 0:                          # STRING: "text"
        # WRONG-DELIMITER rival: single quote (39) = host-language printout,
        # not the interchange double quote (34).  'a' -> 'a' (pre-patch), not "a".
        out = [39]  # type: List[int]
        append_escaped(out, node.text)
        out.append(39)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out"""

# ---------------------------------------------------------------------------
# 6. SINGLE-TOKEN WRAP (uniqueness) — the documented G-EQ kill-criterion at the
#    structural level.  serialize ARRAY branch DROPS the brackets and just
#    returns the element body (no [ ... ]).  ['a','b'] would render as "a", "b"
#    (no brackets) instead of ["a", "b"].  Fails ToSeq(result) == node_body(node)
#    (node_body ARRAY = PSeq(91) + ser_list(inner) + PSeq(93)).  expect=reject.
# ---------------------------------------------------------------------------
_STW_OLD = """    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result"""
_STW_NEW = """    if node.kind == 1:                          # ARRAY: [ elements ]
        # NO-BRACKETS rival: drop the surrounding [ ] structure.  ['a','b'] ->
        # "a", "b" instead of the structural ["a", "b"].
        result = serialize_list(node.inner)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result"""

# ---------------------------------------------------------------------------
# 7. WRONG-FALLBACK (uniqueness) — display_structured_value non-encodable arm
#    WRAPS the fallback display text in an extra single-quote (39) delimiter pair
#    instead of passing it through unchanged.  The real fallback
#    (display_for_value -> general arm str(value)) returns the fallback text
#    AS-IS; wrapping it renders "'{('a', 'b'): 'c'}'" instead of the F2P
#    expected "{('a', 'b'): 'c'}".  Fails Implies(present and not encodable,
#    ToSeq(Result()) == fallback_form(ToSeq(content))) (fallback_form =
#    identity).  expect=reject.
# ---------------------------------------------------------------------------
_WF_OLD = """    # fallback: the general-purpose display text for this value, returned
    # unchanged (a fresh owned copy of it; no delimiters are added).
    out2 = []  # type: List[int]
    m = 0
    while m < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(out2)))
        Invariant(0 <= m and m <= len(content))
        Invariant(ToSeq(out2) == ToSeq(content).take(m))
        Invariant(MustTerminate(len(content) - m + 1))
        # invariants-end
        out2.append(content[m])
        m = m + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    return out2"""
_WF_NEW = """    # WRONG-FALLBACK rival: wrap the fallback display text in an extra single-quote
    # (39) delimiter pair instead of returning it unchanged.
    out2 = [39]  # type: List[int]
    m = 0
    while m < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(out2)))
        Invariant(0 <= m and m <= len(content))
        Invariant(ToSeq(out2) == PSeq(39) + ToSeq(content).take(m))
        Invariant(MustTerminate(len(content) - m + 1))
        # invariants-end
        out2.append(content[m])
        m = m + 1
    out2.append(39)
    return out2"""

# ---------------------------------------------------------------------------
# 8. ADMISSIBILITY — confirm the preconditions admit a normal F2P-shaped input.
#    In display_structured_value's `not present` arm (an impl region), build a
#    fresh F2P-shaped STRING JNode ('a' = [97]) and call serialize on it,
#    asserting the result is well-formed and equals interchange_form (i.e. BOTH
#    Requires Acc(j_pred(node),1/2) AND the TOTALITY budget
#    Requires(MustTerminate(j_size(node)+3)) are satisfiable for a real F2P
#    value).  The probe sits HERE rather than in serialize_list because the
#    budget needs headroom: this caller holds MustTerminate(j_size(value)+4) and
#    a freshly built one-part node needs only j_size(probe)+3 == 4, strictly
#    smaller.  The constructed node is discarded; the gold placeholder copy and
#    return are preserved.  expect=verify (else PRECOND-TOO-STRONG).
# ---------------------------------------------------------------------------
_ADM_OLD = """    if not present:
        result = []  # type: List[int]
        j = 0"""
_ADM_NEW = """    if not present:
        # ADMISSIBILITY probe: build an F2P-shaped STRING node ('a' = [97]) and
        # call serialize on it.  BOTH the permission precondition
        # Acc(j_pred(node),1/2) AND the TOTALITY budget
        # Requires(MustTerminate(j_size(node)+3)) must admit this normal input:
        # this caller holds MustTerminate(j_size(value)+4) and the freshly built
        # one-part node needs only 4, strictly smaller, so the call is legal.
        # Result asserted well-formed + == interchange_form.
        # NOTE: a fresh list literal `[97]` already carries full list_pred, so we
        # do NOT manually Fold(list_pred(txt)) here -- doing so both double-folds
        # and crashes Nagini's Fold translation (FieldAccessPredicate vs
        # PredicateAccessPredicate); JNode.__init__ just needs Acc(list_pred(txt)).
        txt = [97]  # type: List[int]
        probe = JNode(0, txt, None, None)
        rendered = serialize(probe)
        # serialize's own Ensures already pins this; the point is the call site
        # could ESTABLISH both of serialize's preconditions for an F2P value.
        Assert(ToSeq(rendered) == interchange_form(probe))
        result = []  # type: List[int]
        j = 0"""

# ---------------------------------------------------------------------------
# 9. NON-TERMINATING DISPATCH (uniqueness) — display_structured_value's
#    encodable arm never produces a display: it re-asks ITSELF the identical
#    question instead of walking the value, so the walk never runs out of value
#    and the rendered text never arrives.  Partial correctness alone would
#    discharge all three postconditions from the self-call's own Ensures; the
#    MustTerminate(j_size(value) + 4) budget is what refuses it, because the
#    self-call is passed the SAME value and so shrinks nothing.  expect=reject.
# ---------------------------------------------------------------------------
_DIV_SELF_OLD = """    if encodable:
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)"""
_DIV_SELF_NEW = """    if encodable:
        # NON-TERMINATING rival: re-ask the identical question instead of
        # walking the value.  Nothing shrinks, so no display ever arrives.
        return display_structured_value(value, empty, content, present, encodable)"""

# ---------------------------------------------------------------------------
# 10. NON-TERMINATING GUARD (uniqueness) — same defect through a loop instead
#     of a self-call: the encodable arm spins on a guard (k >= 0 over an
#     up-counter) that can never be falsified, so the `return` after it sits on
#     a path control never reaches.  Under partial correctness every
#     postcondition holds vacuously there; the loop must instead exhibit a
#     decreasing measure inside the caller's budget, and an up-counter has
#     none.  expect=reject.
# ---------------------------------------------------------------------------
_DIV_LOOP_OLD = """    if encodable:
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)"""
_DIV_LOOP_NEW = """    if encodable:
        # NON-TERMINATING rival: a guard that is never falsified, so the
        # display below is on a path control never reaches.
        k = 0
        while k >= 0:
            # invariants-start
            Invariant(k >= 0)
            # invariants-end
            k = k + 1
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)"""

# ---------------------------------------------------------------------------
# 11. NON-TERMINATING SERIALISER (uniqueness) — the divergence moved down into
#     the structural walk itself: `serialize` spins before dispatching on the
#     node, so no encoding of any value ever arrives even though its
#     postcondition (== node_body / interchange_form) is discharged vacuously
#     on the unreachable tail.  Rejected by serialize's own
#     MustTerminate(j_size(node) + 3) budget.  expect=reject.
# ---------------------------------------------------------------------------
_DIV_SER_OLD = """    # impl-start
    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:"""
_DIV_SER_NEW = """    # impl-start
    # NON-TERMINATING rival: spin before walking the value, so no encoding of
    # any value ever arrives.
    d = 0
    while d >= 0:
        # invariants-start
        Invariant(d >= 0)
        # invariants-end
        d = d + 1
    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:"""

# ---------------------------------------------------------------------------
# 12. PARTIAL-DOMAIN B (uniqueness) — the token's interchange form is built by
#     escaping ONLY the delimiter U+0022 and splicing every other code point in
#     raw.  CORRECT on all four F2P values and on every token whose remaining
#     code points are printable ASCII, so no test in the suite separates it from
#     gold; it diverges the moment a token carries the escape character U+005C,
#     a control position or a non-ASCII code point ('a\\b' would render as
#     "a\b" -- which reads back as a BACKSPACE -- where the interchange form is
#     "a\\b").  Fails append_escaped's postcondition
#     ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src)).  expect=reject.
# ---------------------------------------------------------------------------
_PD_ESC_OLD = """        append_esc_char(result, src[i])
        i = i + 1"""
_PD_ESC_NEW = """        # PARTIAL-DOMAIN rival: escape ONLY the delimiter U+0022 and splice
        # every other code point in raw.  Correct on the four F2P values and on
        # any all-printable token; diverges on U+005C, on the control positions
        # and on every non-ASCII code point.
        if src[i] == 34:
            result.append(92)
            result.append(34)
        else:
            result.append(src[i])
        i = i + 1"""

# ---------------------------------------------------------------------------
# 13. DIGIT-ORDER (uniqueness) — the six-code-point form of a non-printable
#     code point emits its four hexadecimal digits LEAST significant first.
#     Correct exactly on the code points whose four digits are a palindrome
#     (U+0000, U+0110, ...), wrong on every other one: U+001F would render as
#     the form for U+F100.  Fails append_esc_char's postcondition
#     ToSeq(result) == Old(ToSeq(result)) + esc_char(c), whose `hex_form` pins
#     the digits most significant first.  expect=reject.
# ---------------------------------------------------------------------------
_HEXORD_OLD = """    elif 0 <= c and c <= 65535:
        result.append(92)
        result.append(117)
        result.append(hex_digit(c // 4096))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit(c % 16))"""
_HEXORD_NEW = """    elif 0 <= c and c <= 65535:
        # DIGIT-ORDER rival: emit the four hexadecimal digits least significant
        # first.  U+001F renders as the form for U+F100.
        result.append(92)
        result.append(117)
        result.append(hex_digit(c % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit(c // 4096))"""

# ---------------------------------------------------------------------------
# 14. POSITIVE CONTROL C (soundness) — structurally DIFFERENT but CORRECT
#     append_escaped: the walk over the token is reshaped with a precomputed
#     length local and a different index name, every gold proof hint kept
#     verbatim (rephrased over the same prefix).  Guards against over-fitting
#     the token-form clause to one loop shape.  MUST verify.
# ---------------------------------------------------------------------------
_POS_ESC_OLD = """    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src).take(i)))
        Invariant(MustTerminate(len(src) - i + 3))
        # invariants-end"""
_POS_ESC_NEW = """    # POSITIVE CONTROL: same token-form semantics, reshaped (precomputed length
    # local + different index name).  Gold proof hints kept verbatim.
    i = 0
    n1 = len(src)
    while i < n1:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(n1 == len(src))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src).take(i)))
        Invariant(MustTerminate(len(src) - i + 3))
        # invariants-end"""


SPEC_TESTS = [
    {
        "id": "frame-mutation-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FRAME_OLD, _FRAME_NEW),
        "refinement": (
            "The gold patch returns `empty_value_display` unchanged on a "
            "not-present value (the `elif value is None` arm). This rival "
            "MUTATES the caller's read-only placeholder string in place to "
            "satisfy ToSeq(Result()) == ToSeq(empty) vacuously. The faithful "
            "real patch (appending the placeholder onto itself and returning the "
            "aliased object) corrupts the shared `empty_value_display` and "
            "doubles its length, so display_for_field(None, JSONField(), '-') "
            "would not return '-'; test_null_display_for_field / "
            "test_json_display_for_field would fail. It does NOT resolve."
        ),
        "rationale": (
            "REJECT comes from the PERMISSION SYSTEM: `empty` is held at "
            "Acc(list_pred(empty), 1/2) (read-only); `empty.append(...)` needs "
            "FULL list_pred(empty), so verification fails for insufficient "
            "permission. The frame condition is the #1 weakness class and a "
            "byte-fuzzer never mutates an input."
        ),
    },
    {
        "id": "pos-serialize-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _POS_SER_OLD, _POS_SER_NEW),
        "rationale": (
            "Structurally-different but CORRECT: the four-way kind dispatch is "
            "reordered (ARRAY, OBJECT, STRING, MEMBER-last) with elif/else "
            "instead of the gold STRING-first fall-through ifs. Every gold proof "
            "obligation it still needs is kept verbatim (the per-branch "
            "Unfold/Fold(Acc(j_pred(node),1/2)) and the per-branch "
            "Assert(ToSeq(...) == node_body(node)) framing pin). The MEMBER case "
            "is the catch-all `else` (matching node_body's own final else arm, "
            "since j_pred does not pin kind to {0,1,2,3}); STRING keeps an "
            "explicit `elif node.kind == 0` so the positive fact reduces "
            "node_body. A pure branch-reorder needs no induction lemma; if it "
            "cannot verify the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-dsv-copyloop-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _POS_DSV_OLD, _POS_DSV_NEW),
        "rationale": (
            "Structurally-different but CORRECT: the not-present copy loop is "
            "reshaped (precomputed length local `ln`, renamed index `k`, fresh "
            "result `out0`) keeping the gold prefix invariant "
            "ToSeq(out0) == ToSeq(empty).take(k) verbatim and adding the "
            "framing fact ln == len(empty). Same fresh-copy semantics; must "
            "verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "partial-domain-drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PD_SEP_OLD, _PD_SEP_NEW),
        "refinement": (
            "Drops the ', ' (44,32) sibling separator. CORRECT on the 0- and "
            "1-element F2P shapes ([] -> [], and the str/dict singleton paths) "
            "but DIVERGES on a multi-element list: the F2P value ['a','b'] would "
            "render as [\"a\"\"b\"] instead of [\"a\", \"b\"]. The faithful real "
            "patch (a json.dumps variant without the item separator) gives "
            "'[\"a\"\"b\"]' != '[\"a\", \"b\"]', so test_json_display_for_field's "
            "['a','b'] subtest fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT comes from the postcondition ToSeq(Result()) == "
            "ser_list(head): ser_list prepends PSeq(44,32) before every "
            "non-head sibling, so an impl that omits it cannot match the fold."
        ),
    },
    {
        "id": "wrong-delimiter-single-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _WD_OLD, _WD_NEW),
        "refinement": (
            "Uses the single quote U+0027 (39) for STRING tokens instead of the "
            "interchange double quote U+0022 (34). This is EXACTLY the pre-patch "
            "host-language printout behaviour the change replaces: 'a' renders "
            "as 'a', not \"a\". The faithful real patch (str/repr instead of "
            "json.dumps) fails the F2P, whose expected is '\"a\"', "
            "'[\"a\", \"b\"]', '{\"a\": {\"b\": \"c\"}}'. It does NOT resolve "
            "(it is the prepatch behaviour model_prepatch.py already fails on)."
        ),
        "rationale": (
            "REJECT comes from the discriminating postcondition ToSeq(Result()) "
            "== node_body(node): node_body for a STRING is PSeq(34) + text + "
            "PSeq(34) (double quote), so single-quote output cannot match."
        ),
    },
    {
        "id": "single-token-no-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _STW_OLD, _STW_NEW),
        "refinement": (
            "The documented G-EQ kill-criterion at the structural level: the "
            "ARRAY branch drops the surrounding brackets, returning just the "
            "element body. The F2P value ['a','b'] would render as \"a\", \"b\" "
            "(no brackets) instead of the structural [\"a\", \"b\"]. The faithful "
            "real patch (returning the joined elements without the [ ] wrapper, "
            "the way a single-token wrap of the printed value behaves) gives "
            "'\"a\", \"b\"' != '[\"a\", \"b\"]', so the F2P fails. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT comes from the postcondition ToSeq(Result()) == "
            "node_body(node): node_body for an ARRAY is PSeq(91) + "
            "ser_list(inner) + PSeq(93); omitting the 91/93 brackets cannot "
            "match the structural fold."
        ),
    },
    {
        "id": "wrong-fallback-extra-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _WF_OLD, _WF_NEW),
        "refinement": (
            "The non-encodable fallback wraps the fallback display text in an EXTRA "
            "single-quote (39) delimiter pair instead of returning it "
            "unchanged. The faithful real patch (repr(str(value)) / an extra "
            "quoting layer on the TypeError arm rather than "
            "display_for_value -> str(value) as-is) would render the "
            "tuple-keyed dict as \"'{('a', 'b'): 'c'}'\", contradicting the "
            "F2P expected \"{('a', 'b'): 'c'}\" (no outer quotes). It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT comes from the postcondition Implies(present and not "
            "encodable, ToSeq(Result()) == fallback_form(ToSeq(content))): "
            "fallback_form is the IDENTITY on that display text, so any "
            "added delimiter pair cannot match."
        ),
    },
    {
        "id": "admissibility-f2p-string-node",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _ADM_OLD, _ADM_NEW),
        "rationale": (
            "A real call confirms the preconditions admit a normal F2P-shaped "
            "input: build a STRING JNode for 'a' (= [97]) and call serialize on "
            "it; BOTH Requires(Acc(j_pred(node),1/2)) AND the totality budget "
            "Requires(MustTerminate(j_size(node)+3)) must be establishable for "
            "this real value, and the result is asserted well-formed and == "
            "interchange_form (length 3 = \"a\"). This also proves the totality "
            "clause is not vacuously unsatisfiable: a caller CAN discharge it "
            "for a real value. If either precondition cannot be met for an F2P "
            "value, PRECOND-TOO-STRONG. The gold placeholder copy and return "
            "are preserved."
        ),
    },
    {
        "id": "diverging-dispatch-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DIV_SELF_OLD, _DIV_SELF_NEW),
        "refinement": (
            "The encodable arm never produces a display: it re-asks itself the "
            "identical question on the identical value instead of walking it. "
            "The faithful real patch (the added structured-data branch calling "
            "back into display_for_field with the same arguments rather than "
            "encoding the value) never returns, so the admin page never "
            "renders and BOTH F2P tests fail on the recursion instead of "
            "comparing text. It does NOT resolve — this is the exact shape a "
            "prior audit ran through the official harness "
            "(completed=TRUE, resolved=FALSE, both F2P failing over 3 "
            "attempts, PASS_TO_PASS all green)."
        ),
        "rationale": (
            "REJECT comes from the TOTALITY obligation "
            "Requires(MustTerminate(j_size(value) + 4)): the self-call is "
            "handed the SAME value, so nothing shrinks and the callee's "
            "budget is not strictly below the caller's. Without that clause "
            "the three postconditions are discharged from the self-call's own "
            "Ensures and the rival VERIFIES — the counterexample this case "
            "exists to keep closed."
        ),
    },
    {
        "id": "diverging-dispatch-unfalsifiable-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DIV_LOOP_OLD, _DIV_LOOP_NEW),
        "refinement": (
            "Same defect through a loop: the encodable arm spins on a guard "
            "that can never be falsified, so the correct display below is on a "
            "path control never reaches. The faithful real patch (the added "
            "branch entering an unbounded loop before encoding) hangs the "
            "request, so test_json_display_for_field never observes any text. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT comes from the same TOTALITY obligation: the loop carries "
            "no decreasing measure inside the caller's MustTerminate budget, "
            "so it cannot take the obligation from the context. Under partial "
            "correctness alone the post-loop path is provably infeasible "
            "(a prior audit's Assert(False) control verified there) and every "
            "Ensures held vacuously."
        ),
    },
    {
        "id": "diverging-serialiser",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DIV_SER_OLD, _DIV_SER_NEW),
        "refinement": (
            "The divergence sits inside the structural walk itself: serialize "
            "spins before dispatching on the node, so no encoding of any value "
            "ever arrives. The faithful real patch (the interchange encoder "
            "looping without progress) hangs on every structured value, so all "
            "of 'a', ['a','b'] and {'a':{'b':'c'}} time out rather than "
            "rendering. It does NOT resolve."
        ),
        "rationale": (
            "REJECT comes from serialize's own TOTALITY obligation "
            "Requires(MustTerminate(j_size(node) + 3)): the added loop has no "
            "decreasing measure, so it cannot take the obligation from the "
            "context, and the postcondition ToSeq(Result()) == node_body(node) "
            "can no longer be discharged on an unreachable tail."
        ),
    },
    {
        "id": "delimiter-only-escape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PD_ESC_OLD, _PD_ESC_NEW),
        "refinement": (
            "The gold patch hands the value to the JSONField's own preparation "
            "step (json.dumps), which rewrites EVERY code point of a string "
            "token or key that the interchange alphabet cannot carry raw: the "
            "delimiter U+0022, the escape character U+005C, the five control "
            "positions with two-code-point forms, and everything outside "
            "U+0020..U+007E as a six-code-point form. This rival rewrites only "
            "the delimiter. It agrees with the real callee on all four F2P "
            "values (none of them carries a code point outside the printable "
            "band), so the four assertions of test_json_display_for_field pass "
            "-- this rival is admissible as a WRONG implementation on the "
            "STRENGTH of the spec, not on the strength of the test suite: for "
            "the value 'a\\b' the real get_prep_value returns the six "
            "characters \"a\\\\b\" while the rival renders the five "
            "characters \"a\\b\", which json.loads reads back as a "
            "backspace, so the rendered text is not the interchange encoding of "
            "the stored value at all. The spec is what refuses it."
        ),
        "rationale": (
            "REJECT comes from append_escaped's postcondition "
            "ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src)): "
            "esc_seq replaces each code point by esc_char of it, and esc_char "
            "of U+005C is the two-code-point form, so a raw splice cannot "
            "re-establish the loop invariant."
        ),
    },
    {
        "id": "hex-digits-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _HEXORD_OLD, _HEXORD_NEW),
        "refinement": (
            "json.dumps writes the six-code-point form of a non-printable code "
            "point most significant digit first (U+001F -> the form for 001f). "
            "This rival reverses the four digits, so it renders the form for "
            "U+F100 instead: a DIFFERENT character, and for a code point whose "
            "digits are not a palindrome the rendered text decodes to another "
            "string entirely. It agrees with the real callee on the four F2P "
            "values (all printable, so no six-code-point form is ever emitted) "
            "and is refused by the spec rather than by the suite."
        ),
        "rationale": (
            "REJECT comes from append_esc_char's postcondition "
            "ToSeq(result) == Old(ToSeq(result)) + esc_char(c), whose hex_form "
            "pins the digit order as c // 4096, (c // 256) % 16, (c // 16) % 16, "
            "c % 16."
        ),
    },
    {
        "id": "positive-control-append-escaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _POS_ESC_OLD, _POS_ESC_NEW),
        "refinement": (
            "A correct alternative implementation of the same token form: the "
            "walk over the token is reshaped (precomputed length local, guard "
            "over the local) and lays down exactly the same code points in the "
            "same order, so it renders every value exactly as the real "
            "get_prep_value does and RESOLVES the instance. It must verify: if "
            "it did not, the token-form clause would be over-fitted to one loop "
            "shape rather than pinning the rendered text."
        ),
        "rationale": (
            "VERIFY is the claim under test. The reshaped loop re-establishes "
            "the same invariant over the same prefix and the same MustTerminate "
            "measure, so the postcondition ToSeq(result) == Old(ToSeq(result)) "
            "+ esc_seq(ToSeq(src)) is discharged unchanged."
        ),
    },
]

# No @ContractOnly axioms (meta.axioms == []); the two callees are A-reference
# deep models validated == real json.dumps / str by axiom_check.py (G-AX), never
# consumed. Nothing for the axiom lane to probe.
AXIOM_TESTS = []
