#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
`implementation_reconstructString` against the post-patch behaviour.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The Lean impl models the argument-reconstruction round-trip
of the atomic `codegen.ast` string value, INDEXED BY THE ARGUMENT-PASSING
CONVENTION under which the value reports its own reconstruction data:

    args       := stringArgs s   # the value's positional arg list (always [])
    kwargNames := []             # the value's keyword arg names
    positional => reconstructPositional args        # expr.func(*expr.args)
    keyword    => reconstructKeyword  kwargNames    # expr.func(**expr.kwargs())

i.e. the prediction is "on EVERY convention the round-trip reproduces `obj`
exactly" (`∀ c, result c = some s`). The real-behaviour leg is the ACTUAL patched
`codegen.ast.String`: we build a real `String(text)`, take its real self-reported
argument data under each convention (the positional tuple `obj.args` and the
keyword mapping `obj.kwargs()`), hand each to its real reconstruction callable
`obj.func`, and observe whether the rebuilt object equals the original.

BOTH conventions are observed, because the spec quantifies over both: a value
that round-trips positionally while refusing the keyword data it publishes about
itself violates the modeled behaviour, and a shadow watching only one convention
would not see that. Each convention is compared separately, so a disagreement is
attributed to the convention it occurred on.

We assert zero disagreements between the Lean prediction (always `some s` on each
convention) and the observed CPython round-trips over >= 10^5 fuzzed string
values (plus a boundary catalogue). exit 0 iff zero disagreements. stdlib-only
fuzzing (pinned seed).
"""
import random
import sys

SEED = 22456          # pinned in mapping.md / meta.json
N = 120_000           # >= 10^5

CONVENTIONS = ("positional", "keyword")


def lean_shadow(text, convention):
    """R/I shadow of implementation_reconstructString at one convention.

    Lean: on `positional` the callable is handed `stringArgs s` (empty) and on
    `keyword` it is handed the value's keyword names (empty); in both cases it
    yields the value itself. Returns the predicted reconstructed text, or None if
    the model predicts a failed round-trip (it never does, on either
    convention)."""
    assert convention in CONVENTIONS
    # stringArgs s = [] and kwargNames = []: the reconstruction callable admits
    # exactly the data the value publishes, and yields the value.
    return text


def cpython_observed(text, convention):
    """Build the REAL patched `codegen.ast.String` and OBSERVE its
    argument-reconstruction round-trip at one convention:

        positional -> obj.func(*obj.args)
        keyword    -> obj.func(**obj.kwargs())

    Returns the rebuilt object's text if the round-trip reproduces an equal
    object, else None (round-trip raised, or produced a non-equal object)."""
    from sympy.codegen.ast import String
    obj = String(text)
    try:
        if convention == "positional":
            rebuilt = obj.func(*obj.args)
        else:
            rebuilt = obj.func(**obj.kwargs())
    except Exception:
        return None
    if rebuilt == obj and isinstance(rebuilt, String):
        return rebuilt.text
    return None


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    alphabet = "abcABC_0123 .,(){}[]<>\t\n\\\"'+-*/=:;"

    def rand_text():
        n = rng.randint(0, 20)
        return "".join(rng.choice(alphabet) for _ in range(n))

    fixed = [
        "foo", "foobar", "", "x", " ", "a b c",
        "String('foo')", "multi\nline", "with'quote", 'with"dq',
        "café", "tab\there", "\\backslash",
    ]
    cases = fixed + [rand_text() for _ in range(N)]

    checked = 0
    for text in cases:
        for convention in CONVENTIONS:
            checked += 1
            predicted = lean_shadow(text, convention)
            observed = cpython_observed(text, convention)
            # The Lean spec says `∀ c, result c = some s`, i.e. on EVERY
            # convention the round-trip yields a value equal to the original
            # (same text). Disagreement iff the real round-trip at this
            # convention fails or yields a different text.
            if observed != predicted:
                disagreements += 1
                if len(examples) < 10:
                    examples.append((text, convention, predicted, observed))

    if disagreements:
        print("G-CONF FAIL: %d disagreements over %d observations (%d values x %d "
              "conventions)" % (disagreements, checked, len(cases), len(CONVENTIONS)))
        for text, convention, pred, obs in examples:
            print("  text=%r convention=%s predicted=%r observed=%r"
                  % (text, convention, pred, obs))
        return 1

    print("G-CONF PASS: 0 disagreements over %d observations (%d fuzzed string "
          "values x %d argument-passing conventions, seed=%d)"
          % (checked, len(cases), len(CONVENTIONS), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
