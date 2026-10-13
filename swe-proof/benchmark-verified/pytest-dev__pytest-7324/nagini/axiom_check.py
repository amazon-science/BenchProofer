#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7324.

Executes the REAL match-expression machinery in-container
(`_pytest.mark.expression`) and asserts that every observation matches the
model encoded in model.py. There is exactly one consumed axiom and two deep
models to validate:

  (A-consumed) `match` — the unchanged user membership predicate. The proof
      relies ONLY on it being a deterministic function of its argument. We
      record every identifier the real machinery passes to the predicate and
      assert (a) determinism (same identifier => same answer) and (b) that the
      predicate is always asked about the ORIGINAL identifier the user wrote
      (the round-trip property the strip site exists to guarantee).

  (A-reference, site 1) `encode_ident(ident) == sentinel ++ ident`, where the
      sentinel is the dollar sign U+0024 (code point 36). The real callee is
      pytest's `not_expr`, which builds `ast.Name(IDENT_PREFIX + ident, Load())`
      with `IDENT_PREFIX == "$"`. We assert the name node placed into the AST is
      exactly `"$" + ident` for every identifier, including the three reserved
      constant spellings, and that the resulting expression COMPILES (the bug
      this fixes is a debug-build interpreter abort in `compile()` on a bare
      `ast.Name("True"/"False"/"None")`).

  (A-reference, site 2) `lookup_key(key) == match(strip_sentinel(key))`, i.e.
      the real `MatcherAdapter.__getitem__` strips exactly the one leading
      sentinel code point before consulting the predicate.

`_pytest.mark.expression` is the module the gold patch edits; it is importable
in the official evaluation container. Exit 0 iff every obligation holds.
"""
import ast
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

SENTINEL = 36  # the '$' code point prepended to every identifier


def encode_ident_model(ident):
    """Reference implementation of model.py `encode_ident` as code points."""
    return [SENTINEL] + [ord(ch) for ch in ident]


def strip_sentinel_model(name):
    """Reference implementation of model.py `strip_sentinel` as code points."""
    assert len(name) >= 1 and name[0] == SENTINEL
    return name[1:]


# --- the checks --------------------------------------------------------------

def check_site1_encode(exprmod, ident):
    """Assert the real `not_expr` emits an ast.Name whose id == '$' + ident,
    matching the deep model, and that the whole expression compiles."""
    from _pytest.mark.expression import Scanner, expression

    astexpr = expression(Scanner(ident))
    # locate the single Name node the identifier produced
    names = [n.id for n in ast.walk(astexpr) if isinstance(n, ast.Name)]
    assert names == ["$" + ident], (
        "site-1 deep model unsound on %r: real not_expr produced Name ids %r, "
        "model gives %r" % (ident, names, ["$" + ident]))
    # the model encoding as code points must equal '$' + ident too
    assert [ord(c) for c in names[0]] == encode_ident_model(ident), (
        "site-1 code-point encoding mismatch on %r" % (ident,))
    # the safety property: this must compile (no debug-build abort on
    # True/False/None) — exactly the crash the fix removes.
    compile(astexpr, filename="<pytest match expression>", mode="eval")


def check_site2_strip_and_axiom(exprmod, ident):
    """Assert the real MatcherAdapter strips the one leading sentinel before
    consulting the predicate (site-2 deep model) AND that the predicate is
    asked about the original identifier (the `match` axiom round-trip)."""
    from _pytest.mark.expression import Expression

    seen = []

    def recording_matcher(name):
        # the predicate must be consulted on the ORIGINAL identifier
        seen.append(name)
        return name == ident

    result = Expression.compile(ident).evaluate(recording_matcher)

    # determinism of the axiom: a second evaluation asks the same question and
    # gets the same answer.
    seen2 = []

    def recording_matcher2(name):
        seen2.append(name)
        return name == ident

    result2 = Expression.compile(ident).evaluate(recording_matcher2)

    assert seen == [ident], (
        "site-2 / match-axiom unsound on %r: predicate was consulted on %r, "
        "must be the original identifier %r" % (ident, seen, [ident]))
    assert seen2 == seen, "match axiom non-deterministic on %r" % (ident,)
    assert result is True and result2 is True, (
        "round trip broken on %r: a matcher accepting exactly %r returned %r"
        % (ident, ident, result))

    # cross-check against the model: the key the adapter strips is '$' + ident,
    # and strip_sentinel recovers ident.
    key_codepoints = encode_ident_model(ident)
    recovered = strip_sentinel_model(key_codepoints)
    assert recovered == [ord(c) for c in ident], (
        "site-2 strip model mismatch on %r" % (ident,))


def main():
    import _pytest.mark.expression as exprmod

    # IDENT_PREFIX must be the single '$' the model encodes as code point 36.
    assert exprmod.IDENT_PREFIX == "$", (
        "sentinel mismatch: model assumes '$' (U+0024) but real IDENT_PREFIX "
        "is %r" % (exprmod.IDENT_PREFIX,))

    # the three reserved constant spellings are the crux of the bug + the F2P
    # tests; plus a spread of ordinary and exotic identifiers the grammar
    # accepts (word chars, ':', '+', '-', '.', '[', ']', non-ASCII).
    reserved = ["True", "False", "None"]
    ordinary = [
        "true", "false", "foo", "bar_baz", "x", "abc123", "1234", "1234abcd",
        "notandor", "not_and_or", "if", "else", "while", "class", "lambda",
        "a:::c", "a+-b", "a[bcd]", "123.232", "...", ":::", ".",
        "אבגד", "aaאבגדcc",
    ]
    idents = reserved + ordinary

    for ident in idents:
        check_site1_encode(exprmod, ident)
        check_site2_strip_and_axiom(exprmod, ident)

    print("G-AX OK: encode (site 1, '$'+ident, compiles incl. True/False/None) "
          "+ strip (site 2) + match axiom (round-trip on original identifier, "
          "deterministic) sound on %d identifiers (incl. the 3 reserved)"
          % len(idents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
