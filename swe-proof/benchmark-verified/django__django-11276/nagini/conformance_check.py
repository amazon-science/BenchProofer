#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11276 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers of the
pure region (``entity`` / ``escaped_seq`` and the entity-token constants) copy
over on top of a small immutable-tuple PSeq shim; they are contract-side but
serve here as an internal cross-check of the shadow. The one @ContractOnly
callee (``entity_decode``) is exercised against the REAL decoder the model
maps it to (the stdlib ``html.unescape``, per mapping.md section 3.2) on the
round-trip obligations the postconditions state.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.utils.html.escape``. The gate applies patch.diff to
/testbed before this script runs and sets PYTHONPATH=/testbed, so the import
resolves to the patched module.

Type bridge (mapping.md section 2): the repo argument is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``, and the return
``str`` lifts back the same way. ``mark_safe`` / ``str()`` are identities on
code-point content for str inputs, so comparing code points of the returned
value against the shadow's output list is exactly the documented bijection.

Input domain: the precondition demands only a readable list of code points,
so every ``str`` (surrogate-free) lowers to a Requires-satisfying input.
Generation stresses the substitution boundary: each significant code point
alone / doubled / embedded, already-escaped text (must double-escape),
mixtures with ordinary ASCII, accented and astral code points, plus a
per-code-point sweep around each significant character.

>= 1e5 Requires-satisfying inputs: boundary cases + code-point sweep +
100000 fuzz strings. Pinned fuzz seed: 11276.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import html
import json
import random
import sys

SEED = 11276
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def seq_amp():
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


def seq_lt():
    # '&lt;'
    return PSeq(38, 108, 116, 59)


def seq_gt():
    # '&gt;'
    return PSeq(38, 103, 116, 59)


def seq_quot():
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


def seq_apos_hex():
    # '&#x27;'  (the apostrophe entity required of the escaper)
    return PSeq(38, 35, 120, 50, 55, 59)


def seq_apos_dec():
    # '&#39;'  (legacy decimal apostrophe entity)
    return PSeq(38, 35, 51, 57, 59)


def entity(c):
    """Entity sequence emitted for a single code point: the five significant
    ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"  -> &#x27;
        return seq_apos_hex()
    return PSeq(c)


def escaped_seq(s):
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. (Iterative here to sidestep recursion limits on long fuzz
    inputs; extensionally the same fold as model.py's front recursion.)"""
    out = ()
    i = 0
    while i < len(s):
        out = out + entity(s[i])._t
        i = i + 1
    return PSeq._wrap(out)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def escape_codepoints(text):
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        c = text[i - 1]
        if c == 38:
            result = [38, 97, 109, 112, 59] + result
        elif c == 60:
            result = [38, 108, 116, 59] + result
        elif c == 62:
            result = [38, 103, 116, 59] + result
        elif c == 34:
            result = [38, 113, 117, 111, 116, 59] + result
        elif c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result


# --- @ContractOnly callee: the REAL decoder (mapping.md section 3.2) ----------

def entity_decode(tok):
    """The axiomatized decoder, delegated to the REAL repo-relied callee:
    the stdlib ``html.unescape`` (the module the patched code calls)."""
    s = "".join(chr(c) for c in tok._t)
    return PSeq._wrap(ord(ch) for ch in html.unescape(s))


# --- oracle: the real patched repo function -----------------------------------

def real_escape():
    from django.utils.html import escape
    return escape


# --- differential driver -------------------------------------------------------

def check(oracle, s):
    """Run shadow and oracle on one input string; return an error string on
    disagreement, else None."""
    text = [ord(ch) for ch in s]      # bridge: str -> List[int]
    shadow = escape_codepoints(text)
    real = [ord(ch) for ch in str(oracle(s))]  # SafeString -> code points
    if shadow != real:
        return ("DISAGREEMENT on input %r (code points %r):\n"
                "  shadow (impl region)      = %r\n"
                "  real (patched repo escape) = %r"
                % (s, text, shadow, real))
    # internal cross-check: the executable impl agrees with the pure fold
    if ToSeq(shadow) != escaped_seq(ToSeq(text)):
        return ("INTERNAL: impl region and pure fold disagree on %r" % s)
    return None


def check_roundtrip():
    """The remaining postcondition clauses: entity_decode inverts entity() on
    every significant code point (checked against the REAL decoder)."""
    for cp in (38, 60, 62, 34, 39):
        got = entity_decode(entity(cp))
        if got != PSeq(cp):
            return ("ROUND-TRIP DISAGREEMENT on code point %d: "
                    "entity_decode(entity(%d)) = %r, expected [%d]"
                    % (cp, cp, got._t, cp))
    # the legacy decimal apostrophe token also decodes to U+0027
    if entity_decode(seq_apos_dec()) != PSeq(39):
        return "ROUND-TRIP DISAGREEMENT on the legacy decimal apostrophe token"
    return None


def boundary_cases():
    significant = ['&', '<', '>', '"', "'"]
    cases = [""]
    cases += significant                          # each significant char alone
    cases += [c + c for c in significant]         # doubled
    cases += ["".join(significant)]               # all five together
    cases += ["".join(reversed(significant))]
    cases += ['a' + c for c in significant]       # after ordinary text
    cases += [c + 'a' for c in significant]       # before ordinary text
    cases += ['a' + c + 'b' for c in significant]  # embedded
    cases += [
        "a&b<c>d\"e'f",
        "x=1&amp;y=&lt;2&gt;",       # already-escaped input must double-escape
        "&amp;", "&#39;", "&#x27;", "&quot;", "&lt;", "&gt;",
        "Joe's Crab Shack",
        "<script>alert('xss')</script>",
        "Can't find my keys",
        "!$&'()*+,;=~:@,",
        "plain ascii text with spaces",
        "\t\n\r\x00\x1f",
        "é", "•", " ", " ", "\U0001F600",
        "\U0001F600&'\U0001F600",
        "a" * 500,
        "&" * 200,
        "'" * 200,
    ]
    return cases


def main():
    oracle = real_escape()

    err = check_roundtrip()
    if err:
        print(err)
        return 1

    checked = 0
    boundary = boundary_cases()
    for s in boundary:
        err = check(oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    # per-code-point sweep: each significant code point and a neighbour band,
    # plus low/high representatives, alone and embedded
    sweep_cps = []
    for cp in (34, 38, 39, 60, 62):
        sweep_cps += [cp - 1, cp, cp + 1]
    sweep_cps += [0, 1, 9, 10, 13, 32, 35, 51, 57, 59, 97, 109, 112,
                  120, 0x7f, 0x80, 0xff, 0x100, 0x2027, 0x10FFFF]
    for cp in sweep_cps:
        ch = chr(cp)
        for s in (ch, "a" + ch, ch + "a", "a" + ch + "b", ch + "&" + ch):
            err = check(oracle, s)
            if err:
                print(err)
                return 1
            checked += 1

    # randomized fuzz: significant chars over-weighted against ordinary text,
    # entity fragments, and non-ASCII code points (pinned seed)
    rng = random.Random(SEED)
    alphabet = (['&', '<', '>', '"', "'"] * 3
                + ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
                   'q', 'u', 'o', 't', 'l', 'g', 'm', 'p', '\t', '\n']
                + ['é', '•', ' ', '\U0001F600'])
    for _ in range(N_FUZZ):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check(oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched escape on %d inputs "
          "(%d boundary + sweep + %d fuzz, seed %d); round-trip clauses hold "
          "against the real decoder; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
