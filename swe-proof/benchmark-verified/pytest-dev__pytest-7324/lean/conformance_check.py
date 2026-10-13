#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_resolveIdent
against the patch.diff behaviour (post-patch single-identifier resolution).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The A-reference ops are realised by the REAL Python path: the name node is
built with the '$' prefix, compiled in eval-mode, and evaluated through a
Mapping adapter that strips the prefix and consults the matcher — exactly the
post-patch code. The shadow reproduces the post-patch behaviour op-for-op; we
assert zero disagreements vs the real path over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import ast
import random
import sys
from collections.abc import Mapping

SEED = 7324          # pinned in mapping.md
N = 120_000          # >= 10^5
IDENT_PREFIX = "$"
RESERVED = {"True", "False", "None"}

ALPHA = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:+-.[]")


def shadow(name: str, matcher):
    """R/I shadow of implementation_resolveIdent (returns ('some', b) | ('none',)).

    key := '$' ++ name; if isReservedConst key: none;
    else some (matcher (key.drop 1)).
    """
    key = IDENT_PREFIX + name
    if key in RESERVED:
        return ("none",)
    return ("some", matcher(key[len(IDENT_PREFIX):]))


class MatcherAdapter(Mapping):
    """The real post-patch MatcherAdapter."""
    def __init__(self, matcher):
        self.matcher = matcher

    def __getitem__(self, key):
        return self.matcher(key[len(IDENT_PREFIX):])

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


def real_post_patch(name: str, matcher):
    """The REAL post-patch resolution: ast.Name('$'+name) -> compile -> eval."""
    node = ast.fix_missing_locations(
        ast.Expression(ast.Name(IDENT_PREFIX + name, ast.Load())))
    try:
        code = compile(node, filename="<pytest match expression>", mode="eval")
    except (ValueError, SyntaxError):
        return ("none",)
    return ("some", bool(eval(code, {"__builtins__": {}}, MatcherAdapter(matcher))))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    fixed = ["a", "True", "False", "None", "true", "false", "and", "or",
             "not", "if", "else", "while", "1234", "123.232", "notandor",
             "Truee", "xTrue", "Nonexyz", "abc_def", "a:::c"]
    cases = list(fixed)
    for _ in range(N):
        # oversample reserved spellings so the discriminating region is hit hard
        r = rng.random()
        if r < 0.05:
            cases.append(rng.choice(["True", "False", "None"]))
        else:
            n = rng.randint(1, 10)
            cases.append("".join(rng.choice(ALPHA) for _ in range(n)))

    for name in cases:
        # random matcher truth-table keyed on the (stripped) identifier
        salt = rng.randrange(1 << 30)
        matcher = lambda k, _s=salt: ((hash((k, _s)) >> 3) & 1) == 0
        s = shadow(name, matcher)
        r = real_post_patch(name, matcher)
        if s != r:
            disagreements += 1
            if len(examples) < 10:
                examples.append((name, s, r))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements (seed={SEED})")
        for name, s, r in examples:
            print(f"  name={name!r} shadow={s!r} real={r!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
