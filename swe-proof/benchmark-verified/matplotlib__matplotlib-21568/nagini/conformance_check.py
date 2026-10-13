#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-21568 (nagini).

SHADOW: the impl region of model.py (`protect_codepoints`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers (`tok_dash`/`tok_colon`/`tok_space`/`protect`/
`protected_seq`) copy over as plain functions with PSeq realized as an
immutable tuple shim. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`matplotlib.dates._wrap_in_tex`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md §2): the repo function takes/returns `str`; the model
carrier is `List[int]` of Unicode code points (`text[k] == ord(s[k])`). The
verified function is the per-code-point protection substitution; the repo
function additionally performs framing that mapping.md §2 documents as I/R
(omitted from the verified function): a regex wrapping of alphabetic runs
BEFORE the substitution, and a fixed wrapper + empty-fragment strip AFTER it.
The bridge therefore composes that documented framing around the shadow:

    bridge(text) = strip(wrap(shadow(codepoints(regex_frame(text)))))

and diffs bridge(text) against the real repo function end-to-end. The framing
strings come straight from mapping.md §2 (rows 3-4), which also argues they
never touch the protected code points — this check refutes/confirms that
observationally on every input.

Input domain: the Requires is only read access to the code-point list, so any
str is admissible. Generation covers boundary shapes (empty, each protected
code point alone/doubled/mixed, date/tick-label shapes, brace/backslash/dollar
collisions with the framing alphabet) plus fuzz over an alphabet that
exercises both the substitution and the framing (letters trigger the regex
path; '{' '}' '$' '\\' collide with framing characters; a slice of wider
non-ASCII code points checks pass-through).

>= 1e5 Requires-satisfying inputs: 40 boundary + 100000 fuzz. Pinned fuzz
seed: 21568.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import re
import sys

SEED = 21568
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, contracts stripped ---------------------------

def tok_dash():
    # '{-}'  = '{' '-' '}'
    return PSeq(123, 45, 125)


def tok_colon():
    # '{:}'  = '{' ':' '}'
    return PSeq(123, 58, 125)


def tok_space():
    # '\;'   = '\\' ';'
    return PSeq(92, 59)


def protect(c):
    if c == 45:        # '-'
        return tok_dash()
    if c == 58:        # ':'
        return tok_colon()
    if c == 32:        # ' '
        return tok_space()
    return PSeq(c)


def protected_seq(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return protect(s[0]) + protected_seq(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def protect_codepoints(text):
    result = []  # type: list
    i = len(text)
    while i > 0:
        c = text[i - 1]
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result


# --- bridge: str <-> List[int] + the documented I/R framing (mapping.md §2) ---

def bridge(text):
    """Compose the framing mapping.md §2 documents as omitted-I/R around the
    shadow: regex wrapping of alphabetic runs first, then the modeled
    substitution via the shadow (over code points), then the fixed wrapper and
    empty-fragment removal."""
    framed = re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)
    protected = protect_codepoints([ord(ch) for ch in framed])
    out = '$\\mathdefault{' + "".join(chr(c) for c in protected) + '}$'
    return out.replace('$\\mathdefault{}$', '')


def check_one(real_fn, text):
    """Run shadow-with-bridge and oracle on one input; return an error string
    on disagreement, else None."""
    shadow_out = bridge(text)
    real_out = real_fn(text)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  input=%r\n  shadow=%r\n  real=%r"
                % (text, shadow_out, real_out))
    return None


def boundary_inputs():
    significant = ['-', ':', ' ']
    cases = [""]
    cases += significant                          # each protected char alone
    cases += [c + c for c in significant]         # doubled
    cases += ["".join(significant), "".join(reversed(significant))]
    cases += [
        "1990",
        "1990-01-01",
        "01-01 00",
        "01 00:00",
        "00:00:00",
        "04:00",
        "16:00",
        "20:00",
        "59.5",
        "00.5",
        "01.0",
        "Jan-01",
        "Jan 01 1990",
        "Jan",
        "01-01 12",
        "1990-01-31",
        "1990{-}01",       # pre-braced text must round-trip unchanged
        "a-b:c d",
        "-:- :- ",
        ":::",
        "   ",
        "---",
        "{}",              # collisions with the framing alphabet
        "$",
        "\\",
        "$\\mathdefault{}$",
        "mathdefault",
        "a",
        "Z9z",
        "é 12:30",    # non-ASCII pass-through next to protected chars
        "–:—",
    ]
    return cases


def rand_input(rng, alphabet):
    n = rng.randint(0, 24)
    return "".join(rng.choice(alphabet) for _ in range(n))


def main():
    from matplotlib.dates import _wrap_in_tex  # REAL patched repo function

    # sanity: the shadow agrees with the pure-region fold on a few inputs
    # (impl region vs pure region internal consistency, not the oracle diff)
    for probe in ("", "-", ":", " ", "12:30", "a-b c"):
        cps = [ord(ch) for ch in probe]
        assert protect_codepoints(cps) == list(protected_seq(PSeq(*cps))._t)

    checked = 0
    boundary = boundary_inputs()
    for text in boundary:
        err = check_one(_wrap_in_tex, text)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    significant = ['-', ':', ' ']
    ordinary = ['0', '1', '2', '5', '9', '.', 'a', 'J', 'n', 'e', 'b',
                'F', 'M', 'd', 'y', 'A', 'C', 'z',
                '{', '}', '$', '\\', ';', 'x',
                'é', '–']
    alphabet = significant + ordinary
    for _ in range(N_FUZZ):
        err = check_one(_wrap_in_tex, rand_input(rng, alphabet))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (+ documented I/R framing bridge) == real "
          "patched function on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
