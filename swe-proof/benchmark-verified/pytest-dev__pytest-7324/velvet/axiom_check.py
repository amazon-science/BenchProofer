#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7324.

The single kind-A leg is the **A-reference** `compileName` (Solution.lean `pure`
region): the deep model of the UNCHANGED callee that turns one bound-name node
into evaluable code, i.e.

    compile(ast.fix_missing_locations(ast.Expression(ast.Name(name, Load()))),
            "<pytest match expression>", mode="eval")

— exactly the call `Expression.compile` runs (src/_pytest/mark/expression.py:
201-203) on the `ast.Name` node built in `not_expr` (line 164/169). The patch
changes only the *argument* of this callee (the name string), never the callee.

Model (Solution.lean):
    isReservedName name := name in {"True","False","None"}
    compileName name    := error  if isReservedName name   else  ok ()

G-AX asserts `compileName == the real callee` over:
  * the boundary — the three reserved spellings (must FAIL) and their
    near-misses (must SUCCEED);
  * the F2P / test-suite identifiers (valid + the keyword-like ones);
  * randomized fuzz drawn from the match-ident grammar plus prefixed names.

`compile` failure is observed as a raised exception (CPython raises ValueError
"identifier field can't represent '<X>' constant"; on a debug interpreter the
same input trips the `compiler_nameop` assertion in the problem statement). We
treat "raised" as `error` and "produced a code object" as `ok`. stdlib-only;
exit 0 iff every observation matches the model.
"""
import ast
import random
import sys

RESERVED = {"True", "False", "None"}


def model_rejects(name):
    """Solution.lean `compileName name == error` <=> isReservedName name."""
    return name in RESERVED


def real_rejects(name):
    """Run the REAL unchanged callee on a single bound name; return True iff it
    fails to produce a code object (the `compileName == error` observation)."""
    try:
        node = ast.fix_missing_locations(
            ast.Expression(ast.Name(name, ast.Load())))
        compile(node, filename="<pytest match expression>", mode="eval")
        return False           # produced code -> ok ()
    except ValueError:
        return True            # reserved-constant spelling -> error
    # Any other exception is NOT modeled as `error`; let it propagate so the
    # check fails loudly rather than silently masking an unmodeled behavior.


def check(name):
    obs = real_rejects(name)
    exp = model_rejects(name)
    assert obs == exp, (
        "compileName deep model unsound on %r: real compile rejects=%r, "
        "model rejects=%r" % (name, obs, exp))


def main():
    # --- boundary: the three reserved spellings MUST be rejected ----------
    boundary_reject = ["True", "False", "None"]
    # --- boundary: near-misses MUST be accepted ---------------------------
    boundary_ok = [
        "", "true", "false", "none", "TRUE", "FALSE", "NONE",
        "Truex", "xTrue", " True", "True ", "NoneType", "_", "__debug__",
        "$True", "$False", "$None", "$",        # the prefixed names (site A)
    ]
    # --- the test-suite identifiers (PASS_TO_PASS test_valid_idents) -------
    test_idents = [
        ".", "...", ":::", "a:::c", "a+-b", "אבגד", "aaאבגדcc", "a[bcd]",
        "1234", "1234abcd", "1234and", "notandor", "not_and_or", "not[and]or",
        "1234+5678", "123.232", "if", "else", "while", "and", "or", "not",
        "True", "False", "None",
    ]
    for name in boundary_reject + boundary_ok + test_idents:
        check(name)

    # --- the F2P invariant: prefixing ANY reserved spelling makes it OK ----
    for r in RESERVED:
        assert not real_rejects("$" + r), (
            "prefixing %r should make it compilable, but real compile still "
            "rejects it" % r)

    # --- randomized fuzz over the match-ident grammar + reserved spellings -
    rng = random.Random(7324)
    # the grammar char classes from expression.py lex: (\w|:|\+|-|\.|\[|\])+
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789_:+-.[]") + ["א", "ב", "•", "é"]
    n_fuzz = 100000
    for _ in range(n_fuzz):
        # occasionally force a reserved spelling / prefixed variant
        roll = rng.random()
        if roll < 0.02:
            name = rng.choice(["True", "False", "None"])
        elif roll < 0.04:
            name = "$" + rng.choice(["True", "False", "None"])
        else:
            k = rng.randint(0, 12)
            name = "".join(rng.choice(alphabet) for _ in range(k))
        check(name)

    print("G-AX OK: compileName deep model (== real compile-of-Name) sound on "
          "%d boundary + %d test idents + %d fuzz inputs; reserved spellings "
          "{True,False,None} reject, all else (incl. prefixed) compile."
          % (len(boundary_reject) + len(boundary_ok), len(test_idents), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
