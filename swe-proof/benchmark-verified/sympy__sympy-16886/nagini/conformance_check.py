#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16886 (nagini).

SHADOW: the impl regions of model.py (`encode_morse` and its helper
`morse_list`), copied verbatim below with the contract calls stripped
(Requires/Ensures/Invariant/Assert lines removed; the executable statements
are untouched). The @Pure helpers `dot`/`dash` copy over as plain functions;
`represented`/`sep_accepted` copy over to define the input domain. The impl
regions use only plain Python lists (PSeq appears solely in the spec region),
so no PSeq shim is needed and there are no @ContractOnly callees.

ORACLE: the REAL repo function the model models per mapping.md --
`sympy.crypto.crypto.encode_morse`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable. This script does NOT apply any patch itself.

Type bridge (mapping.md "Type abstraction"):
  * the plaintext word is a List[int] of Unicode code points in the model; the
    real function takes a str -- bridge with ''.join(chr(c) ...);
  * the separator is a single int code point in the model; the real function
    takes a one-character str -- bridge with chr(sep);
  * the model's result is a List[int] of signal code points; the real
    function returns a str -- bridge with [ord(ch) ...] and compare with ==.

Input domain (the model's Requires): ONE WORD -- a possibly-empty plaintext
every symbol of which the representation table represents (`represented`, the
52 keys of char_morse: 'A'..'Z', '0'..'9' and the sixteen punctuation
marks) -- and a separator code point sep in 0..1114111 with sep_accepted(sep)
true and sep distinct from the two signal code points 46 ('.') and 45 ('-').
That is exactly the shape the per-word encoding step is handed: the surrounding
pass deletes unrepresented characters (crypto.py:1570) and splits on whitespace
(crypto.py:1573). Every generated input is asserted to satisfy the domain
before use.

Because the domain is one whitespace-free word of represented symbols, the
whole real function reduces to the per-word step on that word, so the shadow is
compared against the REAL top-level `encode_morse` with no harness in between.

Boundary cases cover: the EMPTY word; every one of the 52 represented
characters alone; every letter/digit/punctuation class in multi-symbol words;
the F2P witnesses '12345', '67890', 'ABC', 'SMS' and the punctuation word;
ascending/descending/repeated runs; a 104-symbol word; and separator extremes
(control chars including whitespace ones, both neighbours of rejected
punctuation, lowercase letters, DEL, the default '|', non-ASCII, non-BMP and
the max code point). Fuzz draws random words over the FULL represented key set
(lengths 0..12, so the empty word is drawn too) crossed with random accepted
separators, mixing full-range draws with near-ASCII draws so both regimes are
exercised; a second fuzz stream draws digits-only words, keeping the pre-patch
discriminator densely covered.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz pairs.
Pinned fuzz seed: 16886.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys

SEED = 16886
N_FUZZ = 100_000


# --- pure helpers from model.py, decorator + docstrings stripped -------------

def dot():
    return 46


def dash():
    return 45


def represented(c):
    return ((65 <= c and c <= 90) or
            (48 <= c and c <= 57) or
            c == 33 or c == 36 or c == 39 or c == 40 or
            c == 41 or c == 43 or c == 44 or c == 45 or
            c == 46 or c == 47 or c == 58 or c == 59 or
            c == 61 or c == 63 or c == 64 or c == 95)


def sep_accepted(c):
    return not (c == 32 or represented(c))


# --- the impl region of model.py's morse_list, verbatim ----------------------

def morse_list(c):
    if c == 65:
        return [dot(), dash()]
    if c == 66:
        return [dash(), dot(), dot(), dot()]
    if c == 67:
        return [dash(), dot(), dash(), dot()]
    if c == 68:
        return [dash(), dot(), dot()]
    if c == 69:
        return [dot()]
    if c == 70:
        return [dot(), dot(), dash(), dot()]
    if c == 71:
        return [dash(), dash(), dot()]
    if c == 72:
        return [dot(), dot(), dot(), dot()]
    if c == 73:
        return [dot(), dot()]
    if c == 74:
        return [dot(), dash(), dash(), dash()]
    if c == 75:
        return [dash(), dot(), dash()]
    if c == 76:
        return [dot(), dash(), dot(), dot()]
    if c == 77:
        return [dash(), dash()]
    if c == 78:
        return [dash(), dot()]
    if c == 79:
        return [dash(), dash(), dash()]
    if c == 80:
        return [dot(), dash(), dash(), dot()]
    if c == 81:
        return [dash(), dash(), dot(), dash()]
    if c == 82:
        return [dot(), dash(), dot()]
    if c == 83:
        return [dot(), dot(), dot()]
    if c == 84:
        return [dash()]
    if c == 85:
        return [dot(), dot(), dash()]
    if c == 86:
        return [dot(), dot(), dot(), dash()]
    if c == 87:
        return [dot(), dash(), dash()]
    if c == 88:
        return [dash(), dot(), dot(), dash()]
    if c == 89:
        return [dash(), dot(), dash(), dash()]
    if c == 90:
        return [dash(), dash(), dot(), dot()]
    if c == 48:
        return [dash(), dash(), dash(), dash(), dash()]
    if c == 49:
        return [dot(), dash(), dash(), dash(), dash()]
    if c == 50:
        return [dot(), dot(), dash(), dash(), dash()]
    if c == 51:
        return [dot(), dot(), dot(), dash(), dash()]
    if c == 52:
        return [dot(), dot(), dot(), dot(), dash()]
    if c == 53:
        return [dot(), dot(), dot(), dot(), dot()]
    if c == 54:
        return [dash(), dot(), dot(), dot(), dot()]
    if c == 55:
        return [dash(), dash(), dot(), dot(), dot()]
    if c == 56:
        return [dash(), dash(), dash(), dot(), dot()]
    if c == 57:
        return [dash(), dash(), dash(), dash(), dot()]
    if c == 46:
        return [dot(), dash(), dot(), dash(), dot(), dash()]
    if c == 44:
        return [dash(), dash(), dot(), dot(), dash(), dash()]
    if c == 58:
        return [dash(), dash(), dash(), dot(), dot(), dot()]
    if c == 59:
        return [dash(), dot(), dash(), dot(), dash(), dot()]
    if c == 63:
        return [dot(), dot(), dash(), dash(), dot(), dot()]
    if c == 45:
        return [dash(), dot(), dot(), dot(), dot(), dash()]
    if c == 95:
        return [dot(), dot(), dash(), dash(), dot(), dash()]
    if c == 40:
        return [dash(), dot(), dash(), dash(), dot()]
    if c == 41:
        return [dash(), dot(), dash(), dash(), dot(), dash()]
    if c == 39:
        return [dot(), dash(), dash(), dash(), dash(), dot()]
    if c == 61:
        return [dash(), dot(), dot(), dot(), dash()]
    if c == 43:
        return [dot(), dash(), dot(), dash(), dot()]
    if c == 47:
        return [dash(), dot(), dot(), dash(), dot()]
    if c == 64:
        return [dot(), dash(), dash(), dot(), dash(), dot()]
    if c == 36:
        return [dot(), dot(), dot(), dash(), dot(), dot(), dash()]
    if c == 33:
        return [dash(), dot(), dash(), dot(), dash(), dash()]
    unrepresented = []  # type: List[int]
    return unrepresented


# --- the impl region of model.py's encode_morse, verbatim
#     (Assert/Invariant proof-scaffolding lines stripped) -----------------

def encode_morse_shadow(msg, sep):
    n = len(msg)
    if n == 0:
        empty = []  # type: List[int]
        return empty
    result = morse_list(msg[n - 1])  # type: List[int]
    i = n - 1
    while i > 0:
        c = msg[i - 1]
        result = morse_list(c) + [sep] + result
        i = i - 1
    return result


# --- oracle: the REAL patched repo function -----------------------------------

def real_encode(msg_cps, sep_cp):
    """Call the real encoder on the bridged str inputs and bridge the str
    result back to a list of code points."""
    from sympy.crypto.crypto import encode_morse
    out = encode_morse("".join(chr(c) for c in msg_cps), sep=chr(sep_cp))
    return [ord(ch) for ch in out]


def in_domain(msg_cps, sep_cp):
    return (all(represented(c) for c in msg_cps) and
            0 <= sep_cp <= 1114111 and
            sep_accepted(sep_cp) and
            sep_cp != dot() and sep_cp != dash())


def check_case(msg_cps, sep_cp):
    assert in_domain(msg_cps, sep_cp), (
        "generator bug: out-of-domain input %r sep=%r" % (msg_cps, sep_cp))
    shadow_out = encode_morse_shadow(list(msg_cps), sep_cp)
    real_out = real_encode(msg_cps, sep_cp)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  msg=%r (str %r) sep=%r (chr %r)\n"
                "  shadow=%r\n  real=%r"
                % (msg_cps, "".join(chr(c) for c in msg_cps), sep_cp,
                   chr(sep_cp), shadow_out, real_out))
    return None


# --- input generation ---------------------------------------------------------

# The 52 represented code points, as the model's `represented` defines them.
REPRESENTED_CPS = [c for c in range(0x110000) if represented(c)]
assert len(REPRESENTED_CPS) == 52, len(REPRESENTED_CPS)
DIGIT_CPS = list(range(48, 58))

# Separator extremes: control chars (incl. the whitespace ones, which are
# ACCEPTED separators -- only the space 32 is excluded), both neighbours of
# rejected punctuation, lowercase letters, DEL, the default '|', non-ASCII,
# non-BMP, max code point.
BOUNDARY_SEPS = [0, 1, 9, 10, 11, 12, 13, 31, 34, 35, 37, 38, 42, 60, 62, 91,
                 92, 93, 94, 96, 97, 106, 122, 123, 124, 125, 126, 127, 128,
                 160, 255, 0x2603, 0xFFFD, 0x10000, 0x1F600, 0x10FFFF]


def _cps(s):
    return [ord(ch) for ch in s]


BOUNDARY_MSGS = (
    # the EMPTY word -- in the domain, and an F2P assertion of its own
    [[]] +
    # every one of the 52 represented characters alone
    [[c] for c in REPRESENTED_CPS] +
    # the F2P witnesses and assorted multi-symbol words
    [_cps('12345'), _cps('67890'), _cps('ABC'), _cps('SMS'),
     _cps('!@$()_+'),    # the represented survivors of F2P's '!@#$%^&*()_+'
     _cps('ATTACKRIGHTFLANK'), _cps('HELLOWORLD'),
     _cps('.,:;?-_()\'=+/@$!'),                     # all 16 punctuation marks
     _cps('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
     _cps('0123456789'), _cps('9876543210'),
     _cps('A'), _cps('1'), _cps('AA'), _cps('11'), _cps('A1'), _cps('1A'),
     _cps('000000000'), _cps('1111111111'),
     _cps('IT\'S3:15P.M.--GO/NO-GO?'),
     REPRESENTED_CPS * 2]                             # a 104-symbol word
)


def boundary_cases():
    for sep in BOUNDARY_SEPS:
        for msg in BOUNDARY_MSGS:
            yield msg, sep


def rand_sep(rng):
    """A random accepted separator (rejection-sampled over the domain)."""
    while True:
        if rng.random() < 0.5:
            c = rng.randint(0, 255)        # near-ASCII regime
        else:
            c = rng.randint(0, 1114111)    # full code-point range
        if sep_accepted(c) and c != dot() and c != dash():
            return c


def rand_msg(rng, pool):
    """A word of 0..12 symbols drawn from `pool` (the empty word included)."""
    return [rng.choice(pool) for _ in range(rng.randint(0, 12))]


def main():
    checked = 0
    n_boundary = 0
    for msg, sep in boundary_cases():
        err = check_case(msg, sep)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for k in range(N_FUZZ):
        # half over the whole represented key set, half digits-only so the
        # pre-patch discriminator stays densely covered
        pool = REPRESENTED_CPS if k % 2 == 0 else DIGIT_CPS
        err = check_case(rand_msg(rng, pool), rand_sep(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real encoder on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
