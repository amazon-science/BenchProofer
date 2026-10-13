#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7205 (nagini).

SHADOW: the impl region of model.py's `render_param_token`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant) stripped. The impl
region itself uses only plain list operations (literal, append, indexing), so
no PSeq shim is needed at runtime: PSeq/ToSeq appear only inside the stripped
contract lines. The @Pure helper `repr_quote` is specification-only (it is
consumed by Ensures, never by the impl), so it does not enter the shadow.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo callee the model models per mapping.md — the
size-limited representation helper `saferepr` from `_pytest._io.saferepr`,
called as `saferepr(s, maxsize=maxsize)`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched tree
importable (the helper module ships with the repo either way; the patch is
what makes it the rendering the modeled call site uses).

Type bridge (mapping.md §2): a Python `str` value maps to `List[int]` of its
Unicode code points (`param[k] == ord(s[k])`); `maxsize` is the identical
integer. The shadow's `List[int]` result compares code point for code point
against `[ord(ch) for ch in saferepr(s, maxsize=maxsize)]`.

Input domain — exactly the model's Requires:
    maxsize >= 2
    len(param) + 2 <= maxsize
    every code point in 32..126, and none equal to 39 (') or 92 (\\)
Generation draws strings over the printable-ASCII alphabet minus those two
code points, with maxsize varied across 2..60 and a heavy slice pinned at the
call-site value 42; lengths sweep the full admissible range including the
exact boundary len == maxsize - 2 and the empty string.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 72050.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 72050
N_FUZZ = 100_000

QUOTE = 39  # the apostrophe delimiter code point U+0027


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def render_param_token(param, maxsize):
    result = [QUOTE]  # type: List[int]
    i = 0
    while i < len(param):
        result.append(param[i])
        i = i + 1
    result.append(QUOTE)
    return result


# --- input domain (the model's Requires) --------------------------------------

def in_domain(codepoints, maxsize):
    if maxsize < 2 or len(codepoints) + 2 > maxsize:
        return False
    return all(32 <= c <= 126 and c != QUOTE and c != 92 for c in codepoints)


def check_one(saferepr, s, maxsize):
    """Run shadow and oracle on one (s, maxsize); return an error string on
    disagreement, else None."""
    param = [ord(ch) for ch in s]           # bridge: str -> List[int]
    assert in_domain(param, maxsize), "generator left the Requires domain"
    shadow = render_param_token(param, maxsize)
    real = [ord(ch) for ch in saferepr(s, maxsize=maxsize)]  # REAL callee
    if shadow != real:
        return ("DISAGREEMENT\n  s=%r maxsize=%d\n  shadow=%r\n  real=%r"
                % (s, maxsize, shadow, real))
    return None


def boundary_cases():
    cases = [
        # the parameter texts the instance's tests exercise, at the call-site
        # size limit
        ("foo", 42), ("bar", 42), ("spam", 42), ("ham", 42),
        ("FOO", 42), ("BAR", 42),
        # empty and single-character values, at the minimal and typical limits
        ("", 2), ("", 3), ("", 42),
        ("a", 3), ("a", 4), ("Z", 42), (" ", 42), ("~", 42), ("0", 42),
        # exact length boundary len == maxsize - 2
        ("ab", 4), ("A" * 40, 42), ("x" * 8, 10), ("q" * 58, 60),
        # alphabet edges (32 and 126) and delimiter-adjacent code points
        (chr(32) * 5, 42), (chr(126) * 5, 42),
        (chr(38) + chr(40), 42),   # code points bracketing the apostrophe
        (chr(91) + chr(93), 42),   # code points bracketing the backslash
        # mixed printable content
        ("Hello World", 42), ("abc def", 42), ("under_score", 42),
        ("CamelCase", 42), ("a-b-c", 42), ("0123456789", 42),
        ("!@#$%^&*()=+~", 42), ("[brackets]", 42), ("{braces}", 42),
        ('"double"', 42),          # double quotes are in-domain content
    ]
    for s, m in cases:
        assert in_domain([ord(ch) for ch in s], m)
    return cases


def main():
    from _pytest._io.saferepr import saferepr  # REAL patched-repo callee

    checked = 0
    for s, maxsize in boundary_cases():
        err = check_one(saferepr, s, maxsize)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    alphabet = [chr(c) for c in range(32, 127) if c not in (QUOTE, 92)]
    for _ in range(N_FUZZ):
        if rng.random() < 0.5:
            maxsize = 42                     # the call-site limit, half the time
        else:
            maxsize = rng.randint(2, 60)
        n = rng.randint(0, maxsize - 2)      # keeps len(param) + 2 <= maxsize
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check_one(saferepr, s, maxsize)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real size-limited representation helper "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
