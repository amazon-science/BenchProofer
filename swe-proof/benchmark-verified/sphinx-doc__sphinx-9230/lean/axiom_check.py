#!/usr/bin/env python3
"""G-AX — validate the deep-model A-reference for sphinx-doc__sphinx-9230.

The modeled `:param type name:` decomposition delegates (post-patch) to the
stdlib string method `str.rsplit(None, 1)` — a last-whitespace split with one
split. That method is modeled DEEPLY in Solution.lean as `extractTypeName`
(an A-reference, not a consumed axiom). This check runs the REAL stdlib callee
(`str.rsplit(None, 1)`, exactly what the post-patch body calls) on boundary +
fuzzed inputs and asserts the deep model reproduces it.

Property validated (the A-reference contract):
  extractTypeName(arg) == (None if len(arg.rsplit(None, 1)) < 2
                           else tuple(arg.rsplit(None, 1)))
where extractTypeName strips trailing whitespace, takes the final non-space run
as the name, and the trailing-stripped prefix as the type (None iff the prefix
is empty, i.e. fewer than two whitespace-delimited tokens).

The fuzz pool covers the FULL Python `str` whitespace-split separator set
(the `str.isspace` singletons: U+0009-U+000D, U+001C-U+001F, space, U+0085,
U+00A0, U+1680, U+2000-U+200A, U+2028, U+2029, U+202F, U+205F, U+3000), which
is exactly what `isSpace` models. stdlib-only. exit 0 iff the deep model
matches the real callee on every input.
"""
import random
import sys

SEED = 9230           # pinned in mapping.md
N = 220_000           # >= 2 * 10^5

# isSpace's separator set == the full Python str-split whitespace set
WS = tuple(
    chr(n) for n in (
        list(range(0x09, 0x0e)) + list(range(0x1c, 0x21)) +
        [0x85, 0xa0, 0x1680] + list(range(0x2000, 0x200b)) +
        [0x2028, 0x2029, 0x202f, 0x205f, 0x3000]
    )
)


def is_space(c: str) -> bool:
    return c in WS


def drop_trailing_spaces(cs: str) -> str:
    i = len(cs)
    while i > 0 and is_space(cs[i - 1]):
        i -= 1
    return cs[:i]


def extract_type_name(arg: str):
    """Python mirror of Lean `extractTypeName` (the deep model)."""
    stripped = drop_trailing_spaces(arg)
    revd = stripped[::-1]
    # takeWhile non-space on the reversed string, then reverse -> name
    k = 0
    while k < len(revd) and not is_space(revd[k]):
        k += 1
    nm = revd[:k][::-1]
    ty = drop_trailing_spaces(revd[k:][::-1])
    if ty == "":
        return None
    return (ty, nm)


def real_callee(arg: str):
    """The REAL post-patch callee: str.rsplit(None, 1). Returns a (type, name)
    pair iff it yields two parts (else the tuple-unpack raises ValueError)."""
    parts = arg.rsplit(None, 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return None


def rand_arg(rng) -> str:
    # oversample structure: parens/brackets/commas (the dict(str, str) shape),
    # letters/digits, and the FULL whitespace-separator set (incl. U+001C-1F,
    # NEL, NBSP and the other Unicode spaces).
    pool = list("aZ09(),[]<>.:_-") + list(WS) + [' ', ' ']
    return "".join(rng.choice(pool) for _ in range(rng.randint(0, 16)))


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        "dict(str, str) opc_meta",          # the exact issue discriminator
        "Dict[str, str] params",            # the F2P test discriminator
        "Tuple[str, ...] items",
        "int x", "x", "", "   ", "  a b  ", " a b ", "a",
        "  a", "a  ", "  a   b   c  ", "a\tb", "a\nb", "a b c d",
        "List[Dict[str, int]] mapping", "  lead a b", "trail a b   ",
        # non-ASCII / control whitespace separators (the past unfaithfulness):
        "int\x1cx", "int\x1dx", "int\x1ex", "int\x1fx",
        "Dict[str,\xa0str]\xa0params", "int\x85x", "a b", "a　b",
        "a b c", " a ", "x\x1c",
    ]
    cases = fixed + [rand_arg(rng) for _ in range(N)]

    mismatches = 0
    examples = []
    for arg in cases:
        model = extract_type_name(arg)
        real = real_callee(arg)
        if model != real:
            mismatches += 1
            if len(examples) < 10:
                examples.append((arg, model, real))

    if mismatches:
        print(f"G-AX FAIL: deep model diverges from real callee on "
              f"{mismatches} inputs")
        for a, m, r in examples:
            print(f"  in={a!r} model={m!r} real={r!r}")
        return 1

    print(f"G-AX OK: deep model == str.rsplit(None,1) on {len(cases)} inputs "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
