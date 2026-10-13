#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15503 (nagini).

SHADOW: the impl region of model.py (``compile_final_key_segment``), copied
verbatim below with the contract calls (Requires / Ensures / Invariant)
stripped. The @Pure helpers (``json_string_literal`` / ``member_access_segment``
/ ``in_domain``) copy over as plain functions on top of a small immutable-tuple
PSeq shim; they are contract-side but serve here as an internal cross-check of
the executable shadow. There are no @ContractOnly callees (the axioms region is
empty).

ORACLE: the REAL patched repo method the model models per mapping.md —
``django.db.models.fields.json.HasKeyLookup.compile_json_path_final_key``,
which compiles the final key of a key-membership test into its textual
JSON-path step. The gate applies patch.diff to /testbed before this script
runs, so the method exists and carries the patched behaviour. The method body
does not touch ``self``, so it is invoked on an ``object.__new__`` instance
(no lookup construction needed).

Type bridge (mapping.md section 2): the repo value is a ``str`` key; the model
carrier is ``List[int]`` of Unicode code points via ``ord`` (a bijection on the
modelled domain). Generation happens over ``str`` and is lowered per call; the
oracle's ``str`` result is lifted back to code points for the comparison.

Requires-satisfying inputs: the precondition demands ``in_domain`` — every
code point in printable ASCII 32..126, excluding the double quote (34) and the
backslash (92). Input plan (>= 1e5 inputs): explicit boundary keys (empty key,
single characters, all-digit keys incl. leading zeros, mixed digit/letter,
punctuation-heavy keys), a full single-character sweep over the domain alphabet
in three positional contexts, 100000 random fuzz keys over the domain
alphabet, and 20000 all-digit fuzz keys stressing the numeric-looking corner
of the domain. Pinned fuzz seed: 15503.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json as _json
import random
import sys

SEED = 15503
N_FUZZ = 100000
N_DIGIT_FUZZ = 20000


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

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @Pure helpers from model.py, copied as plain functions -------------------

def is_digit(c):
    return 48 <= c and c <= 57


def all_digits(s):
    if len(s) == 0:
        return False
    if len(s) == 1:
        return is_digit(s[0])
    return is_digit(s[0]) and all_digits(s.drop(1))


def json_string_literal(s):
    return PSeq(34) + s + PSeq(34)


def member_access_segment(key):
    return PSeq(46) + json_string_literal(key)


def in_domain(s):
    return all(32 <= s[i] and s[i] <= 126 and s[i] != 34 and s[i] != 92
               for i in range(len(s)))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def compile_final_key_segment(key):
    result = [46, 34]  # type: list
    i = 0
    while i < len(key):
        result = result + [key[i]]
        i = i + 1
    result = result + [34]
    return result


# --- differential driver -------------------------------------------------------

_ORACLE = None  # bound in main(): the real patched repo method, one instance


def check(s):
    """Run shadow and oracle on one candidate key; return an error string on
    disagreement, else None. Only Requires-satisfying keys are checked."""
    key = [ord(ch) for ch in s]          # bridge: str -> List[int]
    if not in_domain(key):               # Requires: in_domain(ToSeq(key))
        return None
    shadow = compile_final_key_segment(key)
    real = [ord(ch) for ch in _ORACLE(s)]  # lift str result back to code points
    if shadow != real:
        return ("DISAGREEMENT on key %r (code points %r):\n"
                "  shadow (impl region) = %r (%r)\n"
                "  real (patched repo method) = %r (%r)"
                % (s, key, shadow, "".join(chr(c) for c in shadow),
                   real, "".join(chr(c) for c in real)))
    # internal cross-check: executable impl agrees with the pure spec function
    if ToSeq(shadow) != member_access_segment(ToSeq(key)):
        return "INTERNAL: impl region and pure spec disagree on %r" % (s,)
    return None


def boundary_cases():
    cases = [
        "", "a", "z", "A", "Z", "_", " ", "~", "!", ".", "-", "+", "@",
        "0", "9", "00", "000", "007", "1111", "123", "456", "789", "999",
        "777", "42", "0042", "10", "01",
        "42abc", "abc42", "4a2", "a4b2c",
        "nested", "lorem", "ipsum", "array", "foo", "key",
        "a b c", "key.with.dots", "(paren)", "[bracket]", "{brace}",
        "!@#$%^&*()", ";drop table", "o'brien", "a/b", "a=b", "a%b",
        "a" * 64, "5" * 32,
    ]
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
    from django.db.models.fields.json import HasKeyLookup

    global _ORACLE
    # The modeled method reads only its key argument, never self: bind it on a
    # bare instance so no lookup construction (lhs/rhs plumbing) is needed.
    inst = object.__new__(HasKeyLookup)
    _ORACLE = lambda s: HasKeyLookup.compile_json_path_final_key(inst, s)

    checked = 0
    boundary = boundary_cases()
    for s in boundary:
        err = check(s)
        if err:
            print(err)
            return 1
        checked += 1

    # single-character sweep over the whole domain alphabet, in three
    # positional contexts (alone / after a letter / between letters)
    alphabet = [chr(c) for c in range(32, 127) if c not in (34, 92)]
    for ch in alphabet:
        for s in (ch, "a" + ch, "a" + ch + "b"):
            err = check(s)
            if err:
                print(err)
                return 1
            checked += 1

    # randomized fuzz over the full domain alphabet (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 20)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check(s)
        if err:
            print(err)
            return 1
        checked += 1

    # all-digit fuzz: keys whose characters all look numeric (incl. leading
    # zeros), the corner of the domain where the final-key step matters most
    digits = list("0123456789")
    for _ in range(N_DIGIT_FUZZ):
        n = rng.randint(1, 10)
        s = "".join(rng.choice(digits) for _ in range(n))
        err = check(s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched final-key step on "
          "%d keys (%d boundary + %d sweep + %d fuzz + %d digit fuzz, "
          "seed %d); 0 disagreements."
          % (checked, len(boundary), 3 * len(alphabet), N_FUZZ, N_DIGIT_FUZZ,
             SEED))
    print(_json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                       "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
