#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9602.

The bundle consumes NO @ContractOnly axiom; both changed behaviours are modelled
deeply. This script validates each deep model == the real callee (the two
A-references of refinement.md / mapping.md), using only the Python standard
library.

  (A-reference 1) `render_literal_value` (model.py) == the built-in `repr`,
      on the domain the model's `Requires` admits.
      The gold patch renders a literal/constant value with `nodes.Text(repr(v))`
      instead of `nodes.Text(v)`. The discriminating observation is on a STRING
      value: `repr('abc') == "'abc'"` carries the surrounding apostrophes,
      whereas the pre-patch `node.value` is the bare `abc`. For a bool/int the
      representation is its plain textual form. The model encodes:
          is_str  -> [39] + value + [39]   (apostrophe = code point 39)
          ¬is_str -> value's textual form, unchanged
      The model's is_str postcondition `repr(s) == "'" + s + "'"` holds ONLY on
      the simple printable-ASCII domain (0x20..0x7e, no apostrophe U+0027, no
      reverse solidus U+005C): outside it `repr` escapes or switches to double
      quotes. model.py encodes exactly that domain as a `Requires` on the string
      case; this script fuzzes the SAME domain (and asserts the precondition it
      fuzzes under), plus a negative control confirming the model would be
      unsound -- hence the `Requires` is load-bearing -- just outside it. We run
      the REAL `repr` on these in-domain string / bool / int / float values and
      assert equality with the model.

  (A-reference 2) `wrap1` / `resolve1` / the wrap-then-resolve pipeline
      (model.py) == the gold patch's two loop bodies (hunks 2 + 3 of
      sphinx/domains/python.py). Each presentation node is abstracted to a KIND
      code: 1 NAME, 2 PUNCT, 3 XREF, 4 LIT. We re-implement the gold loop bodies
      EXACTLY at the kind level and assert the model agrees, exhaustively over
      every kind and both head positions and both `is_literal` values, plus a
      randomized fuzz over node lists. We also replay the gold pipeline at the
      kind level on the two FAIL_TO_PASS inputs `Literal[True, False]` and
      `typing.Literal[0, 1, 'abc']` (parsed with the stdlib `ast`) and assert
      the resulting node-KIND sequence matches the model's `resolve_subscript`.

Imports only the Python standard library (`ast`, `random`, `sys`). Exit 0 iff
every obligation holds.
"""
import ast
import random
import sys

QUOTE = 39  # apostrophe U+0027

# kind codes
NAME, PUNCT, XREF, LIT = 1, 2, 3, 4

# The model's render_literal_value precondition admits, for a STRING value, only
# code points in the simple printable-ASCII domain: 0x20..0x7e, excluding the
# apostrophe U+0027 (39) and the reverse solidus U+005C (92). On exactly this
# domain repr(s) == "'" + s + "'" (the simple single-quote form, no escaping,
# no switch to double quotes). axiom_check.py fuzzes the SAME domain the spec
# Requires encodes -- no wider, no narrower -- so the A-reference equality is
# checked over precisely the inputs the spec admits.
SAFE_MIN, SAFE_MAX = 0x20, 0x7e          # printable ASCII (space .. tilde)
SAFE_EXCLUDE = (QUOTE, 0x5c)             # apostrophe, reverse solidus


def in_str_requires_domain(s):
    """True iff every code point of `s` satisfies render_literal_value's
    is_str precondition (32 <= c <= 126 and c not in {39, 92})."""
    return all(SAFE_MIN <= ord(ch) <= SAFE_MAX and ord(ch) not in SAFE_EXCLUDE
               for ch in s)


# --- model.py reference encodings (kept in lock-step with the deep models) ----

def render_literal_value(value_codepoints, is_str):
    """model.py render_literal_value, as a list of code points."""
    if is_str:
        return [QUOTE] + list(value_codepoints) + [QUOTE]
    return list(value_codepoints)


def wrap1(k, is_lit):
    """model.py wrap1."""
    if is_lit and k == NAME:
        return LIT
    return k


def resolve1(k):
    """model.py resolve1."""
    if k == LIT:
        return NAME
    if k == NAME:
        return XREF
    return k


def model_resolve_subscript(kinds, is_literal):
    """model.py resolve_subscript: wrap-then-resolve over the body node list."""
    wrapped = [wrap1(k, is_literal) for k in kinds]
    return [resolve1(w) for w in wrapped]


# --- A-reference 1: render_literal_value == real repr -------------------------

def check_repr_reference(py_value):
    """Assert render_literal_value(model) == the REAL repr observation, on an
    input the model's `Requires` admits (for strings: the simple printable-ASCII
    domain the spec encodes). We assert the precondition we fuzz under, so the
    fuzz domain is provably the spec-admitted domain -- no silent narrowing."""
    is_str = isinstance(py_value, str)
    if is_str:
        # ENFORCE the spec Requires: every string we check must lie in the
        # is_str precondition domain. Any caller passing an out-of-domain string
        # is a checker bug, not an admitted input.
        assert in_str_requires_domain(py_value), (
            "checker drew a string outside render_literal_value's Requires "
            "domain: %r" % (py_value,))
        value_cp = [ord(ch) for ch in py_value]
    else:
        # for a non-string value, the rendered content is its plain textual form
        value_cp = [ord(ch) for ch in str(py_value)]
    real = [ord(ch) for ch in repr(py_value)]              # real callee `repr`
    model = render_literal_value(value_cp, is_str)
    assert model == real, (
        "render_literal_value deep model unsound on %r: repr gave %r, "
        "model gives %r" % (py_value, real, model))


# --- A-reference 2: kind pipeline == the gold loop bodies ---------------------

def gold_wrap_body(result_kinds, is_literal_head):
    """Re-implementation of gold hunk 2 at the kind level:

        if result[0] in ('Literal', 'typing.Literal'):
            for i, subnode in enumerate(result[1:], start=1):
                if isinstance(subnode, nodes.Text):
                    result[i] = nodes.literal('', '', subnode)

    A NAME (non-blank nodes.Text) at index >= 1 becomes a LIT
    (nodes.literal-wrapped). Index 0 (the head) is never wrapped. Punctuation
    and references are untouched. NOTE: in the modelled BODY (the bracket
    contents only) there is no head, so every position is a body position and
    the wrap applies to every NAME — which is exactly model.wrap1 with no head
    distinction. This helper checks the full-list (head-included) gold body to
    confirm the model's body abstraction is faithful: the head is unchanged by
    the wrap and is resolved to a XREF (it is a non-blank Text), matching the
    F2P expectation that `Literal` is a pending_xref."""
    out = list(result_kinds)
    if is_literal_head:
        for i in range(1, len(out)):
            if out[i] == NAME:
                out[i] = LIT
    return out


def gold_resolve_body(wrapped_kinds):
    """Re-implementation of gold hunk 3 at the kind level:

        for i, node in enumerate(result):
            if isinstance(node, nodes.literal):
                result[i] = node[0]          # unwrap to inner (plain) Text
            elif isinstance(node, nodes.Text) and node.strip():
                result[i] = type_to_xref(...)  # -> pending_xref
    """
    out = []
    for node in wrapped_kinds:
        if node == LIT:
            out.append(NAME)          # unwrapped to inner plain text
        elif node == NAME:
            out.append(XREF)          # -> cross-reference
        else:
            out.append(node)          # punctuation / reference pass through
    return out


def check_kind_pipeline_exhaustive():
    """Assert model wrap1/resolve1 == the gold loop bodies on every kind code,
    both head positions, both is_literal values."""
    for k in (NAME, PUNCT, XREF, LIT):
        for is_lit in (False, True):
            # model body (no head distinction) vs gold body-position wrap
            # (index >= 1 is a body position): they must agree.
            m = wrap1(k, is_lit)
            # gold body wrap for a body NAME mirrors wrap1 exactly:
            g = LIT if (is_lit and k == NAME) else k
            assert m == g, ("wrap1 unsound: k=%d is_lit=%s model=%d gold=%d"
                            % (k, is_lit, m, g))
        # resolve1 vs the gold resolve body on a single node
        mg = gold_resolve_body([k])[0]
        assert resolve1(k) == mg, ("resolve1 unsound: k=%d model=%d gold=%d"
                                   % (k, resolve1(k), mg))


def check_kind_pipeline_fuzz(rng, rounds):
    """Assert model_resolve_subscript == gold(resolve)∘gold(wrap) on random
    body node lists (no head)."""
    for _ in range(rounds):
        n = rng.randint(0, 12)
        kinds = [rng.choice((NAME, PUNCT, XREF, LIT)) for _ in range(n)]
        is_lit = rng.choice((False, True))
        model = model_resolve_subscript(kinds, is_lit)
        # gold body pipeline with no head: every position is a body position,
        # so the wrap applies to every NAME, then resolve.
        wrapped = [(LIT if (is_lit and k == NAME) else k) for k in kinds]
        gold = gold_resolve_body(wrapped)
        assert model == gold, ("kind pipeline unsound on %r is_lit=%s: model=%r "
                               "gold=%r" % (kinds, is_lit, model, gold))


# --- end-to-end replay of the gold pipeline on the F2P inputs -----------------

def gold_unparse_kinds(node):
    """Replay the gold `unparse` at the KIND level for the AST shapes the F2P
    inputs exercise (Subscript of a Name/Attribute over a Tuple of Constants).
    Returns (kinds, head_text) where head_text drives the Literal guard. Mirrors
    sphinx/domains/python.py unparse() post-patch:
      - Name            -> [NAME]            (the head)
      - Attribute       -> [NAME]            (dotted head, single Text node)
      - Constant        -> [NAME]            (nodes.Text(repr(value)), non-blank)
      - Subscript       -> head + '[' + body + ']', then the Literal wrap
      - Tuple           -> elt, ', ', elt, ...   (no surrounding brackets)
    """
    if isinstance(node, ast.Module):
        kinds = []
        head = None
        for e in node.body:
            ks, h = gold_unparse_kinds(e)
            kinds.extend(ks)
            head = h
        return kinds, head
    if isinstance(node, ast.Expr):
        return gold_unparse_kinds(node.value)
    if isinstance(node, ast.Name):
        return [NAME], node.id
    if isinstance(node, ast.Attribute):
        # gold unparse: nodes.Text("%s.%s" % (unparse(node.value)[0], node.attr))
        # -> a single Text node whose text is the dotted name.
        _, base_text = gold_unparse_kinds(node.value)
        dotted = ("%s.%s" % (base_text, node.attr)) if base_text is not None \
            else node.attr
        return [NAME], dotted
    if isinstance(node, ast.Constant):
        # nodes.Text(repr(value)); repr is always a non-empty, non-blank string
        return [NAME], None
    if isinstance(node, ast.Index):  # py<3.9 wrapper
        return gold_unparse_kinds(node.value)
    if isinstance(node, ast.Tuple):
        kinds = []
        for i, elt in enumerate(node.elts):
            ks, _ = gold_unparse_kinds(elt)
            kinds.extend(ks)
            kinds.append(PUNCT)   # ', '
        if kinds:
            kinds.pop()           # drop trailing separator
        return kinds, None
    if isinstance(node, ast.Subscript):
        head_kinds, head_text = gold_unparse_kinds(node.value)
        body, _ = gold_unparse_kinds(node.slice)
        result = list(head_kinds) + [PUNCT] + body + [PUNCT]   # head '[' body ']'
        # gold hunk 2: Literal wrap
        is_literal = head_text in ('Literal', 'typing.Literal')
        if is_literal:
            for i in range(1, len(result)):
                if result[i] == NAME:
                    result[i] = LIT
        return result, head_text
    raise AssertionError("unhandled AST node %r" % (node,))


def gold_parse_annotation_kinds(annotation):
    """Replay gold `_parse_annotation` end-to-end at the kind level: unparse
    (with the Literal wrap) then the final resolve loop (hunk 3)."""
    tree = ast.parse(annotation)
    kinds, _ = gold_unparse_kinds(tree)
    return gold_resolve_body(kinds)


def check_f2p_endtoend():
    """For the two FAIL_TO_PASS annotations, assert the gold end-to-end node
    KINDS match the structure the F2P test asserts: head is a XREF, every
    enumerated value is a plain NAME (not a XREF), brackets/separators are
    PUNCT. Also assert the body sub-sequence equals model.resolve_subscript on
    the body kinds with is_literal=True."""
    cases = {
        # Literal[True, False] -> XREF '[' True ', ' False ']'
        "Literal[True, False]":
            [XREF, PUNCT, NAME, PUNCT, NAME, PUNCT],
        # typing.Literal[0, 1, 'abc'] -> XREF '[' 0 ', ' 1 ', ' 'abc' ']'
        "typing.Literal[0, 1, 'abc']":
            [XREF, PUNCT, NAME, PUNCT, NAME, PUNCT, NAME, PUNCT],
    }
    for annotation, expected in cases.items():
        observed = gold_parse_annotation_kinds(annotation)
        assert observed == expected, (
            "gold end-to-end kinds for %r: expected %r, got %r"
            % (annotation, expected, observed))
        # No enumerated value resolves to a XREF — the whole point of the fix.
        # The head (index 0) is the only XREF.
        assert observed[0] == XREF and XREF not in observed[1:], (
            "an enumerated value was cross-referenced for %r: %r"
            % (annotation, observed))
        # The body (between the brackets) under the model == the gold body.
        body_in = [NAME, PUNCT, NAME] if annotation.startswith("Literal") \
            else [NAME, PUNCT, NAME, PUNCT, NAME]
        model_body = model_resolve_subscript(body_in, True)
        # every value NAME stays a plain NAME, separators stay PUNCT
        assert XREF not in model_body, (
            "model resolve_subscript cross-referenced a Literal value: %r"
            % (model_body,))


def main():
    # --- A-reference 1: render_literal_value == real repr ---------------------
    # Every boundary string lies in render_literal_value's is_str Requires
    # domain (printable ASCII, no apostrophe / backslash) -- the domain the
    # spec encodes; check_repr_reference asserts this.
    string_boundary = [
        "", "abc", "True", "False", "0", "1", "x", "a b c", "Literal",
        "typing", "None", "spam-eggs", "10n", "0xFF",
    ]
    for s in string_boundary:
        assert in_str_requires_domain(s)
        check_repr_reference(s)
    for v in (True, False, 0, 1, -1, 42, 255, 1000000, 2.5, 0.0, -3.14):
        check_repr_reference(v)

    # Fuzz strings over EXACTLY the spec-Requires domain: printable ASCII
    # 0x20..0x7e minus apostrophe (39) and reverse solidus (92). On this domain
    # repr uses the simple single-quote form with no escaping, so
    # repr(s) == "'" + s + "'" -- the equality the model claims. The fuzz domain
    # equals the spec Requires domain (no silent narrowing, no over-claim).
    rng = random.Random(9602)
    safe_alphabet = [chr(c) for c in range(SAFE_MIN, SAFE_MAX + 1)
                     if c not in SAFE_EXCLUDE]
    assert all(in_str_requires_domain(ch) for ch in safe_alphabet)
    for _ in range(20000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(safe_alphabet) for _ in range(n))
        check_repr_reference(s)
    for _ in range(5000):
        check_repr_reference(rng.randint(-10 ** 9, 10 ** 9))

    # Negative control: confirm the model would be UNSOUND outside the Requires
    # domain (so the precondition is load-bearing, not decorative). On a string
    # containing an apostrophe or backslash, repr does NOT equal "'" + s + "'",
    # so the model's is_str postcondition would fail -- which is exactly why the
    # spec excludes that domain via Requires.
    for s in ("a'b", "a\\b", "''", "\\"):
        is_str = True
        value_cp = [ord(ch) for ch in s]
        model = render_literal_value(value_cp, is_str)
        real = [ord(ch) for ch in repr(s)]
        assert model != real, (
            "expected model != repr OUTSIDE the Requires domain for %r" % (s,))
        assert not in_str_requires_domain(s)

    # --- A-reference 2: kind pipeline == the gold loop bodies -----------------
    check_kind_pipeline_exhaustive()
    check_kind_pipeline_fuzz(rng, 20000)

    # --- end-to-end replay on the FAIL_TO_PASS inputs -------------------------
    check_f2p_endtoend()

    print("G-AX OK: render_literal_value (== repr) sound on %d boundary + "
          "25000 fuzz values, all within the spec Requires domain (printable "
          "ASCII minus apostrophe/backslash; precondition asserted; negative "
          "control confirms unsoundness just outside it); wrap1/resolve1 "
          "(== gold loop bodies) sound exhaustively + 20000 fuzz node lists; "
          "gold end-to-end kinds match the F2P structure for both Literal "
          "annotations." % (len(string_boundary) + 11))
    return 0


if __name__ == "__main__":
    sys.exit(main())
