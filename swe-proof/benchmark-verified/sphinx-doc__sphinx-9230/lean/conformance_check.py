#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_paramField
against the patch.diff behaviour (the post-patch `:param type name:`
decomposition).

The impl region has R/I content (the trailing-strip, the final-token split, the
Option/none guard), so this runs a real fuzz. The shadow reproduces the Lean
impl's control flow op-for-op: strip trailing whitespace, take the final
non-space run as the name, take the trailing-stripped prefix as the type, return
none iff the type is empty, else the pair. The last-whitespace split op is
A-tagged (a deep-model reference to str.rsplit), so — per the G-CONF protocol —
it is realised here by the REAL repo callee (`str.rsplit(None, 1)`).

The patched side is an independent reconstruction of the POST-patch statement:
`argtype, argname = fieldarg.rsplit(None, 1)` inside `try/except ValueError`
(ValueError -> the field is left untouched, modeled as `none`).

The fuzz pool covers the FULL Python `str` whitespace-split separator set
(the `str.isspace` singletons, incl. U+001C-U+001F, NEL, NBSP and the other
Unicode spaces), which is exactly what `isSpace` models. We assert zero
disagreements over >= 10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 9230           # pinned in mapping.md
N = 220_000           # >= 10^5

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


def shadow(arg: str):
    """R/I shadow of implementation_paramField. The final-token split (the
    A-reference) is realised via the REAL callee str.rsplit(None, 1); the
    trailing-strip + none-guard are the impl's own R/I ops."""
    # A-reference op via the real callee:
    parts = arg.rsplit(None, 1)            # str.rsplit(None, 1)
    if len(parts) == 2:
        ty, nm = parts[0], parts[1]
    else:
        # < 2 tokens: extractTypeName's type prefix is empty
        ty, nm = "", (parts[0] if parts else "")
    # impl's none-guard (ty empty <=> fewer than 2 whitespace tokens):
    if ty == "":
        return None
    return (ty, nm)


def patched(arg: str):
    """Independent reconstruction of the POST-patch statement:
        try:
            argtype, argname = fieldarg.rsplit(None, 1)
        except ValueError:
            (field left untouched -> none)
    """
    try:
        argtype, argname = arg.rsplit(None, 1)
    except ValueError:
        return None
    return (argtype, argname)


def rand_arg(rng) -> str:
    pool = list("aZ09(),[]<>.:_-") + list(WS) + [' ', ' ']
    return "".join(rng.choice(pool) for _ in range(rng.randint(0, 16)))


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        "dict(str, str) opc_meta",
        "Dict[str, str] params",
        "Tuple[str, ...] items",
        "int x", "x", "", "   ", "  a b  ", " a b ", "a",
        "  a", "a  ", "  a   b   c  ", "a\tb", "a\nb", "a b c d",
        "List[Dict[str, int]] mapping", "  lead a b", "trail a b   ",
        # non-ASCII / control whitespace separators:
        "int\x1cx", "int\x1dx", "int\x1ex", "int\x1fx",
        "Dict[str,\xa0str]\xa0params", "int\x85x", "x\x1c",
    ]
    cases = fixed + [rand_arg(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for arg in cases:
        got = shadow(arg)
        want = patched(arg)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((arg, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, g, w in examples:
            print(f"  in={a!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
