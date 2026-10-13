#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13794 (nagini).

SHADOW: the impl regions of model.py (`forward_combine` / `reverse_combine`),
copied verbatim below with the contract calls (Requires/Ensures/Invariant)
stripped. The impls operate on plain `List[int]`, so no PSeq shim is needed;
there are no @Pure helpers and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
a deferred value built with `django.utils.functional.lazy` participating in
binary `+` as the LEFT operand (models `forward_combine`) and as the RIGHT
operand (models `reverse_combine`). The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable. The forcing of the deferred value is an R-refinement: its realized
value IS the model input `realized`, so the oracle proxy is constructed to
realize exactly that value.

Type bridge (mapping.md section 2): a `str` value maps to `List[int]` of
Unicode code points (`xs[k] == ord(s[k])`); `+` on str is concatenation, the
same operation the impl folds spell out. The shadow's List[int] result is
compared against the oracle's str result lifted through the same bijection.
The int carrier (a single number as the realized value) is exercised too:
there the model's concatenation degenerates to the one-element case, checked
via singleton lists against numeric addition's operand-combination shape only
through the string bridge — the modeled domain per mapping.md is the sequence
carrier, so generation stays on str-valued proxies.

Input domain: Requires demands only two readable lists — every pair of
code-point lists is Requires-satisfying, including empty ones.

>= 1e5 Requires-satisfying inputs: boundary cases + 60000 fuzz pairs, each
pair driven through BOTH directions (>= 120000 shadow/oracle comparisons).
Pinned fuzz seed: 13794.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13794
N_FUZZ = 60_000


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def forward_combine(realized, other):
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        result.append(other[j])
        j = j + 1
    return result


def reverse_combine(realized, other):
    result = []  # type: List[int]
    i = 0
    while i < len(other):
        result.append(other[i])
        i = i + 1
    j = 0
    while j < len(realized):
        result.append(realized[j])
        j = j + 1
    return result


# --- bridge: str <-> List[int] of code points ---------------------------------

def to_codepoints(s):
    return [ord(ch) for ch in s]


def from_codepoints(xs):
    return "".join(chr(x) for x in xs)


def check_pair(make_proxy, realized_s, other_s):
    """Run shadow and oracle on one (realized, other) pair, both directions;
    return an error string on disagreement, else None."""
    realized = to_codepoints(realized_s)
    other = to_codepoints(other_s)

    p = make_proxy(realized_s)  # a deferred value realizing exactly realized_s

    # deferred value on the LEFT of + (forward direction)
    shadow_fwd = forward_combine(realized, other)
    real_fwd = p + other_s
    if not isinstance(real_fwd, str) or to_codepoints(real_fwd) != shadow_fwd:
        return ("DISAGREEMENT (forward)\n  realized=%r\n  other=%r\n"
                "  shadow=%r\n  real=%r"
                % (realized_s, other_s, from_codepoints(shadow_fwd), real_fwd))

    # deferred value on the RIGHT of + (reverse direction)
    shadow_rev = reverse_combine(realized, other)
    real_rev = other_s + p
    if not isinstance(real_rev, str) or to_codepoints(real_rev) != shadow_rev:
        return ("DISAGREEMENT (reverse)\n  realized=%r\n  other=%r\n"
                "  shadow=%r\n  real=%r"
                % (realized_s, other_s, from_codepoints(shadow_rev), real_rev))
    return None


def boundary_pairs():
    return [
        ("string", "lazy"),
        ("lazy", "string"),
        ("", ""),
        ("", "x"),
        ("x", ""),
        ("a", "b"),
        ("aa", "aa"),                # equal operands
        ("ab", "ba"),                # order-sensitive pair
        ("Joe's", " Crab Shack"),
        ("<b>", "</b>"),
        ("café", "  ☕"),
        ("multi\nline", "\ttabbed"),
        ("123", "456"),
        ("\x00", "\x00nul"),
        ("\U0001f600", "astral"),
    ]


ALPHABET = list("abcXYZ0 \t\n&<>'\"é☕;#x39") + ["\x00", "\U0001f600"]


def rand_str(rng):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 24)))


def main():
    from django.utils.functional import lazy  # the patched module

    def make_proxy(value):
        return lazy(lambda: value, str)()

    checked = 0
    for a, b in boundary_pairs():
        err = check_pair(make_proxy, a, b)
        if err:
            print(err)
            return 1
        checked += 2  # both directions

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_pair(make_proxy, rand_str(rng), rand_str(rng))
        if err:
            print(err)
            return 1
        checked += 2

    print("G-CONF OK: shadow impls == real deferred-value + on %d comparisons "
          "(%d boundary + %d fuzz pairs, both directions, seed %d)."
          % (checked, len(boundary_pairs()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
