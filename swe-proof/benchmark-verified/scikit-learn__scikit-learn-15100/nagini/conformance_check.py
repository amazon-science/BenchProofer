#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-15100
(nagini).

SHADOW: the impl region of model.py (`strip_marks`), copied VERBATIM below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
three @ContractOnly callees are delegated to the REAL callees the model maps
them to (mapping.md section 3) — all standard-library, the very functions the
repo code calls:
  - `decompose(s)`          -> `unicodedata.normalize('NFKD', .)` on the
                               lifted string, lowered back to code points;
  - `is_combining(c)`       -> `unicodedata.combining(chr(c)) != 0`;
  - `is_fixed_form_guard(s)`-> `str.encode('ASCII', errors='strict')` in a
                               try/except, True iff it succeeds.
The @Pure helpers of the pure region (`all_ascii`, `strip_combining`) copy
over on a small immutable-tuple PSeq shim and serve as an internal
cross-check of the shadow against the model's own postcondition fold
(`strip_combining` iteratively here to sidestep recursion limits on long
inputs; extensionally the same front fold as model.py's recursion).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — `sklearn.feature_extraction.text.strip_accents_unicode`. The
gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the import resolves to the patched in-tree source.

TYPE BRIDGE (mapping.md section 2): the repo argument and return are `str`;
the model carrier is `List[int]` of Unicode code points via `ord`, and the
returned `str` lowers back the same way. The model's ASCII fast path returns
a fresh code-point copy where the repo returns the input object — `str` is
immutable, so comparing code-point content is exactly the documented
bijection.

INPUT DOMAIN: the precondition demands only a readable list of code points,
so every surrogate-free `str` lowers to a Requires-satisfying input.
Generation stresses the two branch regimes and the mark-dropping selection:
pure-ASCII strings (fast path), strings with precomposed accented letters,
strings ALREADY in decomposed form carrying combining marks, bare combining
marks, compatibility-decomposable characters (ligatures, enclosed and
fullwidth forms, Hangul), the 127/128 code-point boundary, and astral
characters, plus a per-code-point sweep and randomized fuzz.

>= 1e5 Requires-satisfying inputs: boundary cases + code-point sweep +
100000 fuzz strings. Pinned fuzz seed: 15100 (the instance number).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only.
"""
import json
import random
import sys
import unicodedata


SEED = 15100
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


# --- @ContractOnly callees, delegated to the REAL mapped callees --------------
# (mapping.md section 3: all three are standard-library calls, the same
# functions the repo body invokes.)

def is_combining(c):
    """Real combining-mark classifier: canonical combining class != 0."""
    return unicodedata.combining(chr(c)) != 0


def nfkd(s):
    """Pure spec face of the decomposition, on the PSeq carrier (used only by
    the internal cross-check fold below)."""
    lifted = "".join(chr(c) for c in s._t)
    return PSeq._wrap(ord(ch) for ch in unicodedata.normalize("NFKD", lifted))


def decompose(s):
    """Runtime carrier of the decomposition: real normalize on the lifted
    string, lowered back to a fresh code-point list."""
    lifted = "".join(chr(c) for c in s)
    return [ord(ch) for ch in unicodedata.normalize("NFKD", lifted)]


def is_fixed_form_guard(s):
    """Real fast-path guard: strict-ASCII encodability of the lifted string."""
    lifted = "".join(chr(c) for c in s)
    try:
        lifted.encode("ASCII", errors="strict")
        return True
    except UnicodeEncodeError:
        return False


# --- pure region of model.py, contracts stripped -------------------------------

def all_ascii(s):
    """Every code point of the sequence is below 128."""
    return all(s[k] < 128 for k in range(len(s)))


def strip_combining(s):
    """The mark-dropping selection: the order-preserving sub-sequence of `s`
    obtained by removing every combining mark. (Iterative here to sidestep
    recursion limits on long fuzz inputs; extensionally the same front-
    recursive fold as model.py's.)"""
    out = []
    i = 0
    while i < len(s):
        if not is_combining(s[i]):
            out.append(s[i])
        i = i + 1
    return PSeq._wrap(out)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def strip_marks(s):
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            out = out + [s[j]]
            j = j + 1
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        c = normalized[i - 1]
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result


# --- oracle: the real patched repo function -----------------------------------

def real_stripper():
    from sklearn.feature_extraction.text import strip_accents_unicode
    return strip_accents_unicode


# --- differential driver -------------------------------------------------------

def check(oracle, s):
    """Run shadow and oracle on one input string; return an error string on
    disagreement, else None."""
    text = [ord(ch) for ch in s]      # bridge: str -> List[int]
    shadow = strip_marks(text)
    real = [ord(ch) for ch in oracle(s)]
    if shadow != real:
        return ("DISAGREEMENT on input %r (code points %r):\n"
                "  shadow (impl region)          = %r\n"
                "  real (patched repo stripper)  = %r"
                % (s, text, shadow, real))
    # internal cross-check: the executable impl agrees with the pure
    # postcondition fold strip_combining(nfkd(.))
    if ToSeq(shadow) != strip_combining(nfkd(ToSeq(text))):
        return ("INTERNAL: impl region and pure fold disagree on %r" % s)
    return None


# some code points expand under decomposition or carry marks; a small mixed
# palette for boundary construction
COMBINING = [chr(c) for c in range(0x0300, 0x0370)]          # combining marks
PRECOMPOSED = ["é", "ñ", "ö", "ȫ", "À", "ẛ",
               "ῲ", "Ǖ", "й", "ṩ"]
COMPAT = ["ﬁ", "①", "ℌ", "Ａ", "½", "²",
          "ᴬ", "㎂"]
HANGUL = ["가", "힣", "까"]
ASTRAL = ["\U0001F600", "\U0001D400", "\U00010000"]


def boundary_cases():
    cases = [""]
    # pure-ASCII: every single ASCII code point, words, whitespace, long runs
    cases += [chr(c) for c in range(128)]
    cases += ["hello", "Hello World", "abc def ghi", "a" * 500,
              "\t\n\r\x00\x1f", "0123456789", "!@#$%^&*()_+-=[]{};:,.<>/?"]
    # precomposed accented letters, alone and embedded in ASCII
    for ch in PRECOMPOSED:
        cases += [ch, "a" + ch, ch + "a", "a" + ch + "b", ch * 5]
    # already-decomposed sequences: base letter + combining mark(s)
    for mark in COMBINING[:24]:
        cases += ["n" + mark, "a" + mark + "b", mark, mark * 3,
                  "o" + mark + mark]
    cases += ["ñ", "ö", "ȫ", "̀́̂̃"]
    # mixed precomposed + decomposed in one string
    cases += ["ññ", "ññ", "aééb"]
    # compatibility decompositions (ligatures, enclosed, fullwidth, ...)
    for ch in COMPAT:
        cases += [ch, "x" + ch + "y"]
    # Hangul syllables (decompose to Jamo, none combining)
    for ch in HANGUL:
        cases += [ch, "k" + ch]
    # 127/128 boundary and other non-ASCII non-accent characters
    cases += ["\x7f", "\x80", "\x7f\x80", " ", "•", "　",
              "￿", "￾"]
    # astral code points, alone and mixed with marks
    for ch in ASTRAL:
        cases += [ch, ch + "́", "a" + ch + "b"]
    # long non-ASCII runs
    cases += ["é" * 300, ("ñ" * 200), ("éa" * 150)]
    return cases


def sweep_strings():
    """Per-code-point sweep: every code point of the first Unicode planes'
    accent-relevant ranges, alone and embedded, plus a coarse full-range
    stride."""
    cps = list(range(0x0000, 0x0530))          # ASCII..Latin/Greek/Cyrillic
    cps += list(range(0x1E00, 0x1F00))         # Latin extended additional
    cps += list(range(0x3040, 0x3100))         # kana (voiced marks decompose)
    cps += list(range(0xFB00, 0xFB10))         # ligatures
    cps += list(range(0xFF00, 0xFFF0))         # fullwidth forms
    cps += list(range(0x0530, 0xD800, 97))     # coarse stride, pre-surrogate
    cps += list(range(0xE000, 0x110000, 997))  # coarse stride, post-surrogate
    out = []
    for cp in cps:
        ch = chr(cp)
        out.append(ch)
        out.append("a" + ch + "b")
    return out


def main():
    oracle = real_stripper()

    checked = 0
    boundary = boundary_cases()
    for s in boundary:
        err = check(oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    sweep = sweep_strings()
    for s in sweep:
        err = check(oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over an alphabet weighted toward the interesting
    # regimes: plain ASCII, combining marks, precomposed accents,
    # compatibility characters, boundary and astral code points (pinned seed)
    rng = random.Random(SEED)
    alphabet = ([chr(c) for c in range(32, 127)]
                + COMBINING * 2
                + PRECOMPOSED * 6
                + COMPAT * 2
                + HANGUL
                + ASTRAL
                + ["\x7f", "\x80", " ", "n", "o", "a", " "] * 4)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 32)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check(oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched stripper on %d inputs "
          "(%d boundary + %d sweep + %d fuzz, seed %d); internal pure-fold "
          "cross-check holds; 0 disagreements."
          % (checked, len(boundary), len(sweep), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
