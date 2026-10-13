#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16877 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an
immutable tuple shim. The @Pure helpers (seq_amp .. seq_apos_hex, entity,
escaped_seq) copy over as plain functions. There are no @ContractOnly callees
in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.template.defaultfilters.escapeseq`, applied to a list whose items are
plain `str` (an item the transform must escape) or `mark_safe(str)` (an item
already marked safe for HTML output). The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md section 2): an item is Elem(chars, is_safe) where
`chars` is the PSeq[int] of the string's Unicode code points and `is_safe`
mirrors "the item exposes __html__" (a safe string). A real input item is
built as `mark_safe(s)` when is_safe else the plain `s`; a real output item's
content is `[ord(c) for c in str(out)]` and its safety flag is
`hasattr(out, "__html__")`. The input list maps index-for-index.

Input domain: the Requires of escape_each only demands read access to a list
of items, so every list of (string, flag) pairs is Requires-satisfying.
Strings are drawn over an alphabet that mixes the five HTML-significant code
points with ordinary ASCII, entity-fragment characters and non-ASCII; flags
are drawn uniformly. Boundary cases cover the empty list, empty strings, each
significant character alone/doubled/combined, already-escaped text, and
mixed safe/unsafe lists.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz lists.
Pinned fuzz seed: 16877.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 16877
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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


# --- Elem carrier from model.py, contracts stripped ---------------------------

class Elem:
    def __init__(self, chars, is_safe):
        self.chars = chars      # type: PSeq
        self.is_safe = is_safe  # type: bool


# --- pure helpers from model.py, decorators/contracts stripped ----------------

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
    # '&#x27;'
    return PSeq(38, 35, 120, 50, 55, 59)


def entity(c):
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
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def escape_codepoints(text):
    result = PSeq(0).take(0)  # type: PSeq
    i = len(text)
    while i > 0:
        c = text[i - 1]
        result = entity(c) + result
        i = i - 1
    return result


def escape_when_unsafe_item(item):
    if item.is_safe:
        return Elem(item.chars, True)
    return Elem(escape_codepoints(item.chars), True)


def escape_each(value):
    result = []  # type: list
    i = 0
    while i < len(value):
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result


# --- bridge: (str, flag) items <-> Elem ----------------------------------------

def to_elem(s, safe):
    return Elem(PSeq._wrap(ord(ch) for ch in s), safe)


def pseq_to_str(m):
    return "".join(chr(m[k]) for k in range(len(m)))


def check_case(escapeseq_filter, mark_safe, items):
    """Run shadow and oracle on one list of (string, safe_flag) items; return
    an error string on disagreement, else None."""
    shadow_in = [to_elem(s, safe) for s, safe in items]
    shadow_out = escape_each(shadow_in)

    real_in = [mark_safe(s) if safe else s for s, safe in items]
    real_out = escapeseq_filter(real_in)

    if not isinstance(real_out, list) or len(real_out) != len(items):
        return ("DISAGREEMENT (arity/type)\n  items=%r\n  shadow_len=%d\n"
                "  real=%r" % (items, len(shadow_out), real_out))
    for k in range(len(items)):
        s_chars = pseq_to_str(shadow_out[k].chars)
        s_safe = shadow_out[k].is_safe
        r_chars = str(real_out[k])
        r_safe = hasattr(real_out[k], "__html__")
        if s_chars != r_chars or s_safe != r_safe:
            return ("DISAGREEMENT at index %d\n  items=%r\n"
                    "  shadow=(%r, safe=%r)\n  real=(%r, safe=%r)"
                    % (k, items, s_chars, s_safe, r_chars, r_safe))
    return None


def boundary_cases():
    sig = ['&', '<', '>', '"', "'"]
    cases = [
        [],                                        # empty list
        [("", False)], [("", True)],               # empty strings
        [("x&y", False), ("<p>", False)],          # unsafe pair
        [("x&y", True), ("<p>", True)],            # safe pair (passthrough)
        [("x&y", True), ("<p>", False)],           # mixed
        [("a&b<c>d\"e'f", False)],
        [("a&b<c>d\"e'f", True)],
        [("x=1&amp;y=&lt;2&gt;", False)],          # already-escaped text
        [("x=1&amp;y=&lt;2&gt;", True)],
        [("&amp;", False), ("&#x27;", False), ("&quot;", False)],
        [("Joe's Crab Shack", False)],
        [("<script>alert('xss')</script>", False)],
        [("plain", False), ("plain", True)],
        [("café", False), ("你好<>", False)],
    ]
    for c in sig:
        cases.append([(c, False)])
        cases.append([(c, True)])
        cases.append([(c + c, False)])
    cases.append([("".join(sig), False), ("".join(reversed(sig)), True)])
    return cases


ALPHABET = ['&', '<', '>', '"', "'",
            'a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
            'é', '•', 'q', 'u', 'o', 't', 'l', 'g', 'm', 'p']


def rand_items(rng):
    n = rng.randint(0, 5)
    items = []
    for _ in range(n):
        m = rng.randint(0, 16)
        s = "".join(rng.choice(ALPHABET) for _ in range(m))
        items.append((s, rng.random() < 0.5))
    return items


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        django.setup()
    from django.template.defaultfilters import escapeseq  # REAL patched callee
    from django.utils.safestring import mark_safe

    checked = 0
    for items in boundary_cases():
        err = check_case(escapeseq, mark_safe, items)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(escapeseq, mark_safe, rand_items(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real sequence filter on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
