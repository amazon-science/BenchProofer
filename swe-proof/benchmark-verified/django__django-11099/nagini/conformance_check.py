#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11099 (nagini).

SHADOW: the impl regions of model.py (``accepts_ascii`` / ``accepts_unicode``),
copied verbatim below with the contract calls (Requires / Ensures / Invariant /
Assert) stripped. The @Pure fold helpers ``all_ascii_permitted`` /
``all_unicode_permitted`` copy over as plain functions on top of a small
immutable-tuple PSeq shim; they are contract-side but serve here as an internal
cross-check of the executable shadow. The @ContractOnly callees
``permitted_ascii`` / ``permitted_unicode`` (single-code-point membership in
the validators' character class) call the REAL repo class: the class subpattern
is EXTRACTED AT RUNTIME from each real compiled validator pattern and
recompiled standalone with that validator's own flags — no pattern text is
hard-coded here.

ORACLE: the REAL patched repo objects the model models per mapping.md — the
acceptance decisions of ``django.contrib.auth.validators``'s two username
validators (``RegexValidator.__call__``: accepted iff no ValidationError). The
gate applies patch.diff to /testbed before this script runs, so the instances
carry the patched patterns.

Type bridge (mapping.md section 2): the repo value is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``. The bridge is a
bijection, so generation happens over ``str`` and is lowered per call. The
precondition demands only a readable list of code points, so every
surrogate-free ``str`` lowers to a Requires-satisfying input.

Input plan (>= 1e5 Requires-satisfying inputs): explicit boundary values
stressing the end-of-string decision (terminal line feed / carriage return,
doubled terminators, embedded whitespace), a single-code-point sweep over
0..0x2100 in three positional contexts, and 100000 random fuzz strings whose
alphabet mixes admissible and inadmissible code points with an extra
terminal-line-feed variant every few draws. Pinned fuzz seed: 11099.

Every value is checked against BOTH regimes (each validator has its own flag
regime). Exit 0 iff zero disagreements; on disagreement prints the input and
both outputs and exits 1. stdlib only.
"""
import json
import random
import re
import sys

SEED = 11099
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


# --- @ContractOnly callees: call the REAL repo character class ----------------

def _extract_class_matcher(rx):
    """Extract the (single) character-class subpattern from the real compiled
    validator pattern and recompile it standalone with the validator's own
    flags. Membership of one code point is then a fullmatch of one char."""
    pat = rx.pattern
    i = 0
    while i < len(pat):
        if pat[i] == '\\':
            i += 2
            continue
        if pat[i] == '[':
            break
        i += 1
    else:
        raise AssertionError("no character class in validator pattern: %r" % pat)
    j = i + 1
    if j < len(pat) and pat[j] == '^':
        j += 1
    if j < len(pat) and pat[j] == ']':
        j += 1
    while j < len(pat):
        if pat[j] == '\\':
            j += 2
            continue
        if pat[j] == ']':
            break
        j += 1
    if j >= len(pat):
        raise AssertionError("unterminated character class in: %r" % pat)
    return re.compile(pat[i:j + 1], rx.flags)


_CLS_ASCII = None   # bound in main() from the real ASCII validator
_CLS_UNI = None     # bound in main() from the real Unicode validator


def permitted_ascii(c):
    """@ContractOnly callee -> the REAL repo class under the ASCII regime."""
    return _CLS_ASCII.fullmatch(chr(c)) is not None


def permitted_unicode(c):
    """@ContractOnly callee -> the REAL repo class under the wider regime."""
    return _CLS_UNI.fullmatch(chr(c)) is not None


# --- pure fold helpers from model.py, contracts stripped ----------------------

def all_ascii_permitted(s):
    if len(s) == 0:
        return True
    return permitted_ascii(s[0]) and all_ascii_permitted(s.drop(1))


def all_unicode_permitted(s):
    if len(s) == 0:
        return True
    return permitted_unicode(s[0]) and all_unicode_permitted(s.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def accepts_ascii(value):
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        c = value[i - 1]
        # (stripped Assert lines carried only proof-side sequence facts)
        if not permitted_ascii(c):
            ok = False
        i = i - 1
    return ok


def accepts_unicode(value):
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        c = value[i - 1]
        # (stripped Assert lines carried only proof-side sequence facts)
        if not permitted_unicode(c):
            ok = False
        i = i - 1
    return ok


# --- oracle: the real patched validators --------------------------------------

def real_accept(validator, exc_type, s):
    """The modeled acceptance decision: True iff the validator call raises
    nothing (mapping.md section 2: accepted <=> no ValidationError)."""
    try:
        validator(s)
        return True
    except exc_type:
        return False


# --- differential driver -------------------------------------------------------

def check(regimes, s):
    """Run shadow and oracle on one candidate value under both regimes;
    return an error string on the first disagreement, else None."""
    value = [ord(ch) for ch in s]     # bridge: str -> List[int]
    for name, shadow_fn, fold_fn, validator, exc_type in regimes:
        shadow = shadow_fn(value)
        real = real_accept(validator, exc_type, s)
        if shadow != real:
            return ("DISAGREEMENT [%s] on value %r (code points %r):\n"
                    "  shadow (impl region) = %r\n"
                    "  real (patched validator decision) = %r"
                    % (name, s, value, shadow, real))
        # internal cross-check: executable impl agrees with the pure fold spec
        spec = len(value) >= 1 and fold_fn(ToSeq(value))
        if shadow != spec:
            return ("INTERNAL [%s]: impl region and pure fold disagree on %r"
                    % (name, s))
    return None


def boundary_cases():
    LF, CR = "\n", "\r"
    core = ["glenn", "jean-marc", "user.name@host+x_1", "a", "Z", "0", "_",
            ".", "@", "+", "-", "é", "Ré", "أحمد", "user名"]
    cases = ["", LF, CR, LF + LF, CR + LF, " ", "\t", "\x0b", "\x0c",
             " ", " ", "​"]
    for w in core:
        cases += [w, w + LF, w + LF + LF, w + CR, w + CR + LF,
                  LF + w, w[:1] + LF + w[1:], w + " ", " " + w,
                  w + " ", w + "​"]
    cases += ["a b", "a\tb", "a\nb", "a:b", "a;b", "a'b", "a\"b",
              "a/b", "a\\b", "a*b", "a=b", "a%b", "a#b", "a?b", "a!b"]
    return cases


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from django.contrib.auth.validators import (ASCIIUsernameValidator,
                                                UnicodeUsernameValidator)
    from django.core.exceptions import ValidationError

    v_ascii = ASCIIUsernameValidator()
    v_uni = UnicodeUsernameValidator()

    global _CLS_ASCII, _CLS_UNI
    _CLS_ASCII = _extract_class_matcher(v_ascii.regex)
    _CLS_UNI = _extract_class_matcher(v_uni.regex)

    regimes = [
        ("ascii", accepts_ascii, all_ascii_permitted, v_ascii, ValidationError),
        ("unicode", accepts_unicode, all_unicode_permitted, v_uni,
         ValidationError),
    ]

    checked = 0
    boundary = boundary_cases()
    for s in boundary:
        err = check(regimes, s)
        if err:
            print(err)
            return 1
        checked += 1

    # single-code-point sweep: each code point alone, after a letter, and
    # between two letters — catches membership disagreements anywhere plus the
    # positional (end-of-string) decision for every swept point
    for cp in range(0, 0x2100):
        ch = chr(cp)
        for s in (ch, "a" + ch, "a" + ch + "b"):
            err = check(regimes, s)
            if err:
                print(err)
                return 1
            checked += 1

    # randomized fuzz over a mixed admissible/inadmissible alphabet (pinned
    # seed); every fourth draw also gets a terminal-line-feed variant so the
    # end-of-string decision is stressed heavily
    rng = random.Random(SEED)
    alphabet = ["\n", "\r", " ", "\t", " ", "​", " ",
                "a", "z", "A", "Z", "0", "9", "_", ".", "@", "+", "-",
                "é", "ü", "م", "名", ":", ";", "'", "/", "\\", "*", "%",
                "!", "?", "=", "#", "\U0001F600"]
    for k in range(N_FUZZ):
        n = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if k % 4 == 0:
            s = s + "\n"
        err = check(regimes, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched validator decision on "
          "%d values x 2 regimes (%d boundary + 0x2100*3 sweep + %d fuzz, "
          "seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "regimes": 2, "disagreements": 0,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
