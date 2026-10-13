#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10880.

This bundle consumes NO axioms: the changed operation (assembling the rendered
SQL fragment from a printf-style template) is modelled DEEPLY in model.py as the
spelled-out concatenation `fragment(function, operands, distinct)`. G-AX here
validates that deep model (an A-reference) against the REAL operation it stands
in for: the percent-substitution of the very template the repository uses,

    template = '%(function)s(%(distinct)s%(expressions)s)'
    rendered = template % {'function': NAME,
                           'distinct': 'DISTINCT ' if distinct else '',
                           'expressions': OPERANDS}

i.e. the same string the database driver receives. The `%`-operator is the
Python standard library; nothing repo-specific is imported. The check asserts,
over boundary cases and randomized fuzz, that

    fragment(NAME, OPERANDS, distinct)  ==  template % data

as code-point lists, and additionally that the structural separation guarantee
of model.py holds on the real rendering: when `distinct` is requested the
keyword DISTINCT sits right after '(' and the code point immediately after the
keyword is the space separator (so it never fuses with the first operand code
point). Exit 0 iff every observation matches the model.
"""
import random
import sys

# The repository template (django/db/models/expressions.py: Func.template, with
# the Aggregate override '%(function)s(%(distinct)s%(expressions)s)').
TEMPLATE = '%(function)s(%(distinct)s%(expressions)s)'

# model.py deep-model encodings (kept in lock-step with the pure region).
KW_DISTINCT = [ord(c) for c in "DISTINCT"]   # [68,73,83,84,73,78,67,84]
SEP = 32                                     # ' '
OPEN = [40]                                  # '('
CLOSE = [41]                                 # ')'


def modifier(distinct):
    """model.py `modifier`: keyword+separator when distinct, else empty."""
    if distinct:
        return KW_DISTINCT + [SEP]
    return []


def fragment(function, operands, distinct):
    """model.py deep model `fragment` as a list of code points."""
    return function + OPEN + modifier(distinct) + operands + CLOSE


def real_render(function_s, operands_s, distinct):
    """The REAL operation: percent-substitution of the repository template,
    exactly as Func.as_sql performs it (distinct -> 'DISTINCT ' post-patch)."""
    data = {
        'function': function_s,
        'distinct': 'DISTINCT ' if distinct else '',
        'expressions': operands_s,
    }
    return TEMPLATE % data


def check(function_s, operands_s, distinct):
    observed = [ord(ch) for ch in real_render(function_s, operands_s, distinct)]
    expected = fragment([ord(ch) for ch in function_s],
                        [ord(ch) for ch in operands_s], distinct)
    assert observed == expected, (
        "deep model `fragment` unsound on function=%r operands=%r distinct=%r: "
        "real render gave %r, deep model gives %r"
        % (function_s, operands_s, distinct, observed, expected))

    if distinct:
        # Structural separation guarantee (model.py post-conditions).
        base = len(function_s) + 1                 # past NAME + '('
        kw = observed[base:base + len(KW_DISTINCT)]
        assert kw == KW_DISTINCT, (
            "keyword not present right after '(' on %r/%r" % (function_s, operands_s))
        assert observed[base + len(KW_DISTINCT)] == SEP, (
            "keyword DISTINCT is not followed by a separator on "
            "function=%r operands=%r — it would fuse with the operands"
            % (function_s, operands_s))


def main():
    functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "", "F"]
    operands = [
        "",                                   # empty operands
        "CASE WHEN pages > 300 THEN rating END",  # the F2P scenario
        "rating",
        "*",
        "publisher_id",
        "a, b, c",
        "T1.col",
        "x",
    ]

    boundary_pairs = [(f, o) for f in functions for o in operands]
    for f, o in boundary_pairs:
        check(f, o, True)
        check(f, o, False)

    # randomized fuzz over arbitrary printable-ish strings, both modes
    rng = random.Random(10880)
    alphabet = [chr(c) for c in range(33, 127)] + [" ", "\t"]
    for _ in range(20000):
        nf = rng.randint(0, 8)
        no = rng.randint(0, 32)
        f = "".join(rng.choice(alphabet) for _ in range(nf))
        o = "".join(rng.choice(alphabet) for _ in range(no))
        d = rng.random() < 0.5
        check(f, o, d)

    # explicit witness: the F2P scenario fragment must read 'COUNT(DISTINCT CASE...'
    rendered = real_render("COUNT", "CASE WHEN pages > 300 THEN rating END", True)
    assert rendered.startswith("COUNT(DISTINCT CASE"), rendered
    assert "DISTINCTCASE" not in rendered, rendered

    print("G-AX OK: deep model `fragment` == real template substitution on "
          "%d boundary + 20000 fuzz inputs (both modes); separation guarantee "
          "holds (no keyword/operand fusion)." % len(boundary_pairs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
