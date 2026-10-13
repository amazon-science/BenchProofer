#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7324 (nagini).

SHADOW: the impl regions of model.py (`encode_ident`, `lookup_key`), copied
verbatim below with the contract calls (Requires/Ensures/Invariant) stripped.
PSeq is realized as an immutable tuple shim and ToSeq as list->PSeq; the @Pure
helpers `sentinel` / `strip_sentinel` copy over as plain functions. The single
@ContractOnly callee `match` (the user-supplied membership predicate) is
bridged to the REAL predicate instance handed to the repo machinery for the
same trial, decoding the code-point sequence back to str.

ORACLE: the REAL patched repo operations the model models per mapping.md —
  site 1: the identifier branch of `_pytest.mark.expression.expression`
          (via `Scanner`), observed as the id of the single ast.Name node the
          identifier produces (the AST node is modeled by its id content;
          mapping.md section 2);
  site 2: `_pytest.mark.expression.MatcherAdapter.__getitem__`, observed as
          the boolean returned for a key under a concrete predicate.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2): str <-> List[int] of Unicode code points
(s[k] <-> xs[k] == ord(s[k])); the shadow's code-point lists compare against
the oracle's strings after decoding.

Input domain:
  site 1: `encode_ident`'s Requires admits any code-point list, but the
    R-bridge binds the input to the scanned identifier, so generation is
    restricted to the identifier alphabet the scanner accepts (word chars,
    ':', '+', '-', '.', '[', ']', incl. non-ASCII word chars), excluding the
    three operator spellings the scanner tokenizes specially ("and", "or",
    "not") and the empty string — the callee's operating domain. The three
    reserved constant spellings ARE identifiers and are fuzzed + boundary-
    pinned.
  site 2: `lookup_key`'s Requires demands a non-empty key whose first code
    point is the sentinel (36); the rest is arbitrary. Keys are generated as
    36 ++ arbitrary code points (incl. empty tails, embedded sentinels,
    spaces, punctuation, non-ASCII). The per-trial predicate is a
    deterministic function of its argument (the axiom's only obligation),
    drawn from set-membership and arithmetic-hash families.

>= 1e5 Requires-satisfying inputs: boundary cases + 55000 fuzz identifiers
(site 1) + 55000 fuzz keys (site 2). Pinned fuzz seed: 7324.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import ast
import json
import random
import sys

SEED = 7324
N_FUZZ_SITE1 = 55_000
N_FUZZ_SITE2 = 55_000


# --- PSeq / ToSeq shim: the operations the impl + pure regions use -----------

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


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- @ContractOnly callee bridge ----------------------------------------------
# `match` models the user-supplied membership predicate. Each trial installs
# the SAME concrete predicate here (over str) and into the real MatcherAdapter;
# the shadow decodes its code-point argument and consults it.

CURRENT_PRED = None


def match(name):
    return CURRENT_PRED("".join(chr(c) for c in name))


# --- pure helpers from model.py, contracts stripped ----------------------------

def sentinel():
    return 36


def strip_sentinel(name):
    return name.drop(1)


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def encode_ident(ident):
    result = [sentinel()]  # type: list
    i = 0
    while i < len(ident):
        result = result + [ident[i]]
        i = i + 1
    return result


def lookup_key(key):
    recovered = []  # type: list
    i = 1
    while i < len(key):
        recovered = recovered + [key[i]]
        i = i + 1
    return match(ToSeq(recovered))


# --- bridges: str <-> code points ----------------------------------------------

def to_codepoints(s):
    return [ord(c) for c in s]


def from_codepoints(xs):
    return "".join(chr(c) for c in xs)


# --- deterministic predicate families (the axiom's only obligation) ------------

def make_predicates(rng, ident_pool):
    member_set = frozenset(rng.sample(ident_pool, min(8, len(ident_pool))))
    k = rng.randint(0, 6)
    return [
        lambda s: True,
        lambda s: False,
        lambda s, m=member_set: s in m,
        lambda s, k=k: (len(s) + sum(ord(c) for c in s)) % 7 == k,
        lambda s: len(s) % 2 == 0,
    ]


# --- site 1: identifier -> emitted program name --------------------------------

def oracle_site1_name(Scanner, expression_fn, ident):
    """The id of the single Name node the real parser emits for an identifier."""
    tree = expression_fn(Scanner(ident))
    names = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name)]
    if len(names) != 1:
        return None, "expected exactly one Name node, got %r" % (names,)
    return names[0], None


def check_site1(Scanner, expression_fn, ident):
    shadow = encode_ident(to_codepoints(ident))
    real, err = oracle_site1_name(Scanner, expression_fn, ident)
    if err is not None:
        return "ORACLE ANOMALY (site 1)\n  ident=%r\n  %s" % (ident, err)
    if shadow != to_codepoints(real):
        return ("DISAGREEMENT (site 1)\n  ident=%r\n  shadow=%r (%r)\n  real=%r"
                % (ident, shadow, from_codepoints(shadow), real))
    return None


# --- site 2: key lookup ---------------------------------------------------------

def check_site2(MatcherAdapter, key_str, pred):
    global CURRENT_PRED
    key = to_codepoints(key_str)
    assert len(key) >= 1 and key[0] == sentinel()  # Requires holds
    CURRENT_PRED = pred
    shadow = lookup_key(key)
    real = MatcherAdapter(pred)[key_str]
    if bool(shadow) != bool(real):
        return ("DISAGREEMENT (site 2)\n  key=%r\n  shadow=%r\n  real=%r"
                % (key_str, shadow, real))
    return None


# --- input generation ------------------------------------------------------------

IDENT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    ":+-.[]"
    "אבגéü"
)
SCANNER_OPERATORS = {"and", "or", "not"}  # tokenized specially, never IDENT

BOUNDARY_IDENTS = [
    "True", "False", "None",              # the reserved constant spellings
    "x", "_", "0", "1234", "1234abcd", "abc123",
    "true", "false", "none", "TRUE", "NONE",
    "if", "else", "while", "class", "lambda", "import", "def",
    "not_and_or", "notandor", "andor", "nott", "ornot",
    "a:::c", "a+-b", "a[bcd]", "123.232", "...", ":::", ".", "-", "+",
    "[", "]", "[]", "a" * 200,
    "אבגד", "aaאבגדcc",
]

BOUNDARY_KEY_TAILS = [
    "",                                    # key is the bare sentinel
    "True", "False", "None",
    "$", "$$", "$True",                    # embedded sentinels
    "x", " ", "  ", "a b", "(paren)", "not", "and", "or",
    "line\nbreak", "tab\tchar", "'quoted'", '"dq"',
    "אבג", "\x00nul", "a" * 300,
]


def rand_ident(rng):
    while True:
        n = rng.randint(1, 12)
        s = "".join(rng.choice(IDENT_ALPHABET) for _ in range(n))
        if s not in SCANNER_OPERATORS:
            return s


KEY_TAIL_ALPHABET = IDENT_ALPHABET + "$ ()'\"!@#%^&*,;<>?/\\\n\t\x00☃"


def rand_key(rng):
    n = rng.randint(0, 12)
    return chr(sentinel()) + "".join(rng.choice(KEY_TAIL_ALPHABET)
                                     for _ in range(n))


def main():
    # REAL patched callees (the gate applied patch.diff to /testbed)
    from _pytest.mark.expression import Scanner, expression, MatcherAdapter

    rng = random.Random(SEED)
    checked = 0

    # site 1: boundary + fuzz identifiers
    for ident in BOUNDARY_IDENTS:
        err = check_site1(Scanner, expression, ident)
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FUZZ_SITE1):
        err = check_site1(Scanner, expression, rand_ident(rng))
        if err:
            print(err)
            return 1
        checked += 1

    # site 2: boundary + fuzz keys, over several deterministic predicates
    ident_pool = BOUNDARY_IDENTS + [rand_ident(rng) for _ in range(64)]
    boundary_preds = make_predicates(rng, ident_pool)
    for tail in BOUNDARY_KEY_TAILS:
        key_str = chr(sentinel()) + tail
        for pred in boundary_preds:
            err = check_site2(MatcherAdapter, key_str, pred)
            if err:
                print(err)
                return 1
            checked += 1
    for _ in range(N_FUZZ_SITE2):
        preds = make_predicates(rng, ident_pool)
        err = check_site2(MatcherAdapter, rand_key(rng),
                          preds[rng.randrange(len(preds))])
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real callees on %d inputs "
          "(site-1 %d boundary + %d fuzz; site-2 %d boundary x %d preds "
          "+ %d fuzz; seed %d)."
          % (checked, len(BOUNDARY_IDENTS), N_FUZZ_SITE1,
             len(BOUNDARY_KEY_TAILS), len(boundary_preds), N_FUZZ_SITE2, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
