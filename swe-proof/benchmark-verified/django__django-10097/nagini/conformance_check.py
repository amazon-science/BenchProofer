#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10097 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
``is_whitespace`` / ``is_uchar`` copy over as plain functions; the
sequence-valued pure predicates ``body_ok`` / ``colons`` / ``accepts`` copy
over on top of a small immutable-tuple PSeq shim (they are contract-side but
serve here as an internal cross-check of the shadow). There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo object the model models per mapping.md — the
user:pass authentication group of ``django.core.validators.URLValidator.regex``.
The gate applies patch.diff to /testbed before this script runs, so the class
attribute is the patched compiled pattern. The authentication subpattern is
EXTRACTED FROM THE REAL COMPILED PATTERN AT RUNTIME (balanced-group scan just
after the scheme separator, dropping the group's trailing terminator literal
and its optionality suffix) and recompiled with the validator's own flags; the
modeled decision "is this authentication segment well-formed" is a full match
of that subpattern, exactly as mapping.md section 1 states. No pattern text is
hard-coded here.

Type bridge (mapping.md section 2): a candidate segment is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``. The bridge is a
bijection, so generation happens over ``str`` and is lowered per call.

Input domain: the precondition demands only a readable list of code points, so
every ``str`` lowers to a Requires-satisfying input. Generation stresses the
decision boundary: every Unicode-whitespace code point (the class where the
model and a whitespace-based matcher could diverge) alone and embedded, the
separator code points, ordinary segment text, and astral/accented code points.

>= 1e5 Requires-satisfying inputs: boundary cases + per-code-point sweep +
100000 fuzz strings. Pinned fuzz seed: 20097.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (the container is Python 3.5; no f-strings).
"""
import json
import random
import re
import sys

SEED = 20097
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

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def is_whitespace(c):
    return ((9 <= c and c <= 13) or c == 32
            or (0x1c <= c and c <= 0x1f) or c == 0x85 or c == 0xa0
            or c == 0x1680 or (0x2000 <= c and c <= 0x200a)
            or c == 0x2028 or c == 0x2029 or c == 0x202f
            or c == 0x205f or c == 0x3000)


def is_uchar(c):
    return not is_whitespace(c) and c != 58 and c != 64 and c != 47


def body_ok(s):
    if len(s) == 0:
        return True
    return (is_uchar(s[0]) or s[0] == 58) and body_ok(s.drop(1))


def colons(s):
    if len(s) == 0:
        return 0
    return (1 if s[0] == 58 else 0) + colons(s.drop(1))


def accepts(s):
    return len(s) > 0 and body_ok(s) and colons(s) <= 1 and s[0] != 58


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def validate_authsegment(seg):
    n = len(seg)
    if n == 0:
        return False
    if seg[0] == 58:
        return False
    good = True
    ncolon = 0
    i = n
    while i > 0:
        c = seg[i - 1]
        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
        if c == 58:
            ncolon = ncolon + 1
        elif not is_uchar(c):
            good = False
        i = i - 1
    return good and ncolon <= 1
    # (the stripped Assert lines carried only proof-side sequence facts)


# --- oracle: the real patched validator's authentication subgroup -------------

def real_matcher():
    """Extract the authentication subpattern from the REAL compiled
    URLValidator regex (patched /testbed) and recompile it standalone with the
    validator's own flags. The full pattern is
    ``^<scheme>://<authgroup><host>...``; the authentication group is the first
    balanced ``(?:...)`` group right after the scheme separator literal and has
    the shape ``(?:<segment><terminator>)?`` where the terminator is the
    one-character literal that ends the segment. A well-formed segment is a
    FULL match of ``<segment>``."""
    from django.core.validators import URLValidator
    rx = URLValidator.regex  # lazy; attribute access forces the real compile
    pat = rx.pattern
    flags = rx.flags
    start = pat.index('://') + 3
    if not pat.startswith('(?:', start):
        raise AssertionError("unexpected validator pattern shape: %r" % pat)
    depth = 0
    k = start
    in_class = False
    while k < len(pat):
        ch = pat[k]
        if ch == '\\':
            k += 2
            continue
        if in_class:
            if ch == ']':
                in_class = False
        else:
            if ch == '[':
                in_class = True
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
        k += 1
    inner = pat[start + 3:k]          # '<segment><terminator>'
    if not inner.endswith('@'):
        raise AssertionError("unexpected authentication group shape: %r" % inner)
    segment_pat = inner[:-1]
    return re.compile(segment_pat, flags)


# --- differential driver -------------------------------------------------------

def check(matcher, s):
    """Run shadow and oracle on one candidate segment; return an error string
    on disagreement, else None."""
    seg = [ord(ch) for ch in s]       # bridge: str -> List[int]
    shadow = validate_authsegment(seg)
    real = matcher.fullmatch(s) is not None
    if shadow != real:
        return ("DISAGREEMENT on segment %r (code points %r):\n"
                "  shadow (impl region) = %r\n"
                "  real (patched validator authentication group fullmatch) = %r"
                % (s, seg, shadow, real))
    # internal cross-check: the executable impl agrees with the pure predicate
    if shadow != accepts(ToSeq(seg)):
        return ("INTERNAL: impl region and pure predicate disagree on %r" % s)
    return None


# The full Unicode-whitespace class the model enumerates (29 code points).
_WS = (set(range(9, 14)) | {32}
       | set(range(0x1c, 0x20)) | {0x85, 0xa0, 0x1680}
       | set(range(0x2000, 0x200b)) | {0x2028, 0x2029, 0x202f, 0x205f, 0x3000})


def boundary_cases():
    ws_chars = [chr(c) for c in sorted(_WS)]
    forbidden = [':', '@', '/'] + ws_chars
    cases = [""]
    cases += forbidden                              # each forbidden char alone
    cases += [c + c for c in forbidden]             # doubled
    cases += ['foo' + c for c in forbidden]         # after a user run
    cases += ['foo' + c + 'bar' for c in forbidden]  # mid-segment
    cases += ['foo:ba' + c + 'r' for c in forbidden]  # in the password run
    cases += [
        "a", "Z", "0",
        "foo", "foo:bar", "foo:", "foo::", "foo:bar:baz",
        "foo/bar", "foo@bar", "foo:bar@baz", "foo:bar/baz",
        ":", ":pass", "::", "user:", "a:b",
        "-.~_!$&'()*+,;=%40:80%2f",
        "-.~_!$&'()*+,;=:%40:80%2f::::::",
        "m=foo", "m=foo@example.com",
        "foo\xa0bar", "foo bar", "user　pass", " x", "x ",
        "\U0001F600", "\U0001F600:\U0001F600", "é", "•",
    ]
    return cases


def main():
    matcher = real_matcher()

    checked = 0
    boundary = boundary_cases()
    for s in boundary:
        err = check(matcher, s)
        if err:
            print(err)
            return 1
        checked += 1

    # per-code-point sweep over the whole modeled whitespace class plus a band
    # of neighbours around each class boundary
    sweep_cps = sorted(_WS)
    for w in sorted(_WS):
        sweep_cps += [w - 1, w + 1]
    sweep_cps += [46, 47, 48, 57, 58, 59, 63, 64, 65]
    for cp in sweep_cps:
        if cp < 0 or 0xd800 <= cp <= 0xdfff:
            continue
        ch = chr(cp)
        for s in (ch, "foo" + ch, "foo" + ch + "bar", "foo:b" + ch + "ar"):
            err = check(matcher, s)
            if err:
                print(err)
                return 1
            checked += 1

    # randomized fuzz: separators + full whitespace block + ordinary text +
    # astral/accented code points (pinned seed)
    rng = random.Random(SEED)
    alphabet = ([':', '@', '/'] + [chr(c) for c in sorted(_WS)]
                + ['a', 'Z', '0', '9', '-', '.', '%', 'f', '!', '$', '&',
                   "'", '(', ')', '*', '+', ',', ';', '=', '~', '_']
                + ['\U0001F600', 'é', '•'])
    for _ in range(N_FUZZ):
        n = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check(matcher, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched authentication matcher on "
          "%d inputs (%d boundary + sweep + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
