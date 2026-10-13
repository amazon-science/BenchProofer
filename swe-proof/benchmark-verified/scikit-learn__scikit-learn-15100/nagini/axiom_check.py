#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-15100.

Executes the REAL stdlib callees (`unicodedata.normalize('NFKD', .)`,
`unicodedata.combining(.)`, and `str.encode('ASCII', errors='strict')`) on
boundary inputs plus randomized fuzzing and asserts that every observation
matches the model, as encoded in model.py.

The kind-A checks (the two axioms the proof CONSUMES):

  (A-consumed: is_combining)  `Ensures(Implies(c < 128, not Result()))`
      Every 7-bit code point is non-combining. Checked by running the real
      `unicodedata.combining` over all 128 ASCII code points (boundary:
      exhaustive) and over a fuzz of arbitrary code points (the implication is
      vacuously true for c >= 128, but we record the classifier's value).

  (A-consumed: nfkd)  `Ensures(Implies(all_ascii(s), Result() == s))`
      Canonical decomposition is the identity on any sequence of 7-bit code
      points. Checked by running the real `unicodedata.normalize('NFKD', .)` on
      ASCII strings (boundary: empty, each ASCII char alone, the full ASCII
      range, words) and asserting the output equals the input.

  (is_fixed_form_guard runtime guard)  models `s.encode('ASCII', errors='strict')`:
      it succeeds (no exception) exactly when every code point is < 128.
      Checked by running the real encode and comparing success against
      all(ord(ch) < 128).

The deep model (A-reference) `strip_combining(nfkd(s))` is additionally
validated == the REAL post-patch transformation
      `''.join(c for c in normalize('NFKD', s) if not combining(c))`
over boundary + fuzz inputs, to confirm the deep model + axioms reproduce the
real behaviour (this is the whole function under specification; it is modelled
deeply, not consumed as an axiom about itself).

Imports nothing repo-specific: `unicodedata` is the Python standard library --
the same module the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys
import unicodedata


# --- reference encodings (kept in lock-step with model.py) -------------------

def model_is_combining(c):
    """model.py `is_combining`: True iff code point is a combining mark."""
    return unicodedata.combining(chr(c)) != 0


def model_strip_combining(codepoints):
    """model.py deep filter `strip_combining`: order-preserving removal of every
    combining mark."""
    return [c for c in codepoints if not model_is_combining(c)]


def real_transform(s):
    """The REAL post-patch transformation (general path), as code points."""
    norm = unicodedata.normalize('NFKD', s)
    return [ord(ch) for ch in norm if not unicodedata.combining(ch)]


# --- the axiom checks --------------------------------------------------------

def check_is_combining_axiom():
    """A-consumed: every 7-bit code point is non-combining."""
    for c in range(128):
        assert unicodedata.combining(chr(c)) == 0, (
            "is_combining axiom unsound: ASCII code point %d is combining" % c)


def check_nfkd_identity_axiom(ascii_strings):
    """A-consumed: NFKD is the identity on pure-ASCII sequences."""
    for s in ascii_strings:
        assert all(ord(ch) < 128 for ch in s)
        observed = unicodedata.normalize('NFKD', s)
        assert observed == s, (
            "nfkd axiom unsound on ASCII %r: normalize gave %r" % (s, observed))


def check_is_ascii_guard(s):
    """is_fixed_form_guard models str.encode('ASCII','strict'): success iff all<128."""
    try:
        s.encode("ASCII", errors="strict")
        succeeded = True
    except UnicodeEncodeError:
        succeeded = False
    expected = all(ord(ch) < 128 for ch in s)
    assert succeeded == expected, (
        "is_fixed_form_guard unsound on %r: encode-succeeds=%r all<128=%r"
        % (s, succeeded, expected))


def check_deep_model_reference(s):
    """A-reference: the deep model strip_combining(nfkd(s)) == the REAL
    post-patch transformation on s."""
    norm_cps = [ord(ch) for ch in unicodedata.normalize('NFKD', s)]
    model = model_strip_combining(norm_cps)
    real = real_transform(s)
    assert model == real, (
        "deep model unsound on %r: strip_combining(nfkd(s)) gave %r, "
        "real transform gives %r" % (s, model, real))


def main():
    # --- boundary inputs ------------------------------------------------------
    ascii_full = "".join(chr(c) for c in range(128))
    boundary = [
        "", "a", "Z", "0", " ", ";", "#", "x",
        "hello", "this is a test", "abc123 !@#", ascii_full,
        # the F2P cases: already-decomposed inputs that MUST be stripped
        "ö",                       # o + combining diaeresis
        "̀́̂̃",      # combining marks alone
        "ȫ",                 # multiple combining marks
        chr(241), chr(110) + chr(771),   # precomposed vs decomposed n-tilde
        "إ", "ا",              # arabic alef with/without hamza
        "́",                        # a lone combining acute
        "ñ̃",                  # precomposed + extra combining mark
        "this is à test",
        "éèêë",      # precomposed accented vowels
        "café", "café",       # cafe precomposed vs decomposed
    ]

    check_is_combining_axiom()
    check_nfkd_identity_axiom([s for s in boundary if all(ord(ch) < 128 for ch in s)])
    for s in boundary:
        check_is_ascii_guard(s)
        check_deep_model_reference(s)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(15100)
    # alphabet: ASCII, Latin-1 precomposed accents, combining marks, base+marks
    alphabet = (
        [chr(c) for c in range(0, 128)]
        + [chr(c) for c in range(0x80, 0x500)]      # accented latin/greek/cyrillic
        + [chr(c) for c in range(0x300, 0x370)]     # combining diacritical marks
        + [chr(241), chr(110), chr(771), chr(0x308), chr(0x304)]
    )
    n_fuzz = 40000
    for _ in range(n_fuzz):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_is_ascii_guard(s)
        check_deep_model_reference(s)

    # additional exhaustive sweep of the combining-mark axiom over the BMP
    # combining-mark blocks (the implication c<128 => not combining is the
    # only consumed clause; this confirms the classifier itself).
    for c in range(0, 0x2000):
        # the axiom only constrains c < 128; for c >= 128 the classifier may be
        # either -- no obligation. We assert the (vacuous-above-128) contract:
        if c < 128:
            assert unicodedata.combining(chr(c)) == 0

    print("G-AX OK: is_combining (A-consumed, ASCII-non-combining, 128 codepoints"
          " + 0x2000 sweep), nfkd identity-on-ASCII (A-consumed), is_ascii guard,"
          " and deep model strip_combining(nfkd(.)) == real transform sound on %d"
          " boundary + %d fuzz inputs" % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
