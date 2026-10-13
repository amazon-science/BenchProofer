#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11099.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable accept/reject:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `validateName` impl region
              transliterated to Python over the *real* repo type (`str`), via
              the mapping.md bijection (`List Char` <-> `str`):
                  validName(isAllowed, s) = (s != "") and all(isAllowed(ch) for ch in s)
              with the FREE parameter `isAllowed` instantiated at each
              validator's real class per mapping.md §2 (the R instantiation
              leg): a "word" char (ASCII for the ASCII validator:
              [A-Za-z0-9_]; Unicode str.isalnum()|'_' for the Unicode
              validator) OR one of '.', '@', '+', '-'. No faithful class
              contains the newline code point, so the quantification through
              the LAST code point rejects trailing newlines (the `\\Z` fix).
  * ORACLE  — the patched validator behaviour: the real patched
              `ASCIIUsernameValidator` / `UnicodeUsernameValidator`, where
              raising `ValidationError` == reject and returning normally ==
              accept. FALLBACK (documented): if the live Django validators
              cannot be imported, transliterate the patched regex with the
              `re` module as the oracle:
                  ASCII   : re.search(r'^[\\w.@+-]+\\Z', value, re.ASCII)
                  Unicode : re.search(r'^[\\w.@+-]+\\Z', value)
              (`RegexValidator.__call__` accepts iff `regex.search(value)`
              matches; the patched `regex` is exactly `^[\\w.@+-]+\\Z`.)

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz set is biased toward the
discriminating trailing-newline cases.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import re
import sys

SEED = 11099
N_FUZZ = 100_000

PATTERN = r'^[\w.@+-]+\Z'
_PUNCT = set('.@+-')


# --- the R/I shadow: validName transliterated ------------------------------
def _is_allowed_ascii(ch):
    return (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9")
            or ch == "_" or ch in _PUNCT)


def _is_allowed_unicode(ch):
    # \w under Unicode: alphanumeric (str.isalnum covers Unicode letters/digits)
    # or underscore; plus the four explicit punctuation marks.
    return (ch.isalnum() or ch == "_" or ch in _PUNCT)


def shadow_valid(value, ascii_mode):
    is_allowed = _is_allowed_ascii if ascii_mode else _is_allowed_unicode
    if value == "":
        return False
    return all(is_allowed(ch) for ch in value)


# --- the oracle: patched validator behaviour --------------------------------
def _live_oracle_factory():
    """Return (ascii_oracle, unicode_oracle) backed by the real patched Django
    validators, or None if Django cannot be imported."""
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(USE_I18N=False)
        django.setup()
        from django.contrib.auth import validators as v
        from django.core.exceptions import ValidationError
        a = v.ASCIIUsernameValidator()
        u = v.UnicodeUsernameValidator()

        def accepts(validator, value):
            try:
                validator(value)
                return True
            except ValidationError:
                return False

        # sanity: confirm the patch is in place (\Z rejects trailing newline)
        if accepts(a, "abc\n") or accepts(u, "abc\n"):
            return None  # unpatched / unexpected; use re fallback instead
        return (lambda s: accepts(a, s)), (lambda s: accepts(u, s))
    except Exception:
        return None


def _re_oracle_factory():
    rx_ascii = re.compile(PATTERN, re.ASCII)
    rx_uni = re.compile(PATTERN)
    return (lambda s: rx_ascii.search(s) is not None), \
           (lambda s: rx_uni.search(s) is not None)


def fuzz_inputs(n, rng):
    base = list("aZ0_.@+-glennJEANmarc")
    weird = ["é", "É", "ä", "•", "​", " ", "–", "أ", " ", "'"]
    alphabet = base + weird
    # boundary / discriminating cases first
    yield ""
    yield "glenn"
    yield "GLEnN"
    yield "jean-marc"
    yield "o'connell"
    yield "jean marc"
    yield "trailingnewline\n"          # the ASCII F2P discriminator
    yield "trailingnewline\u000A"  # the Unicode F2P discriminator (\n)
    yield "abc\n"
    yield "\n"
    yield "\nabc"
    yield "ab\ncd"
    yield "abc\n\n"
    yield "abc\r\n"
    yield "abc\r"
    yield "a.b@c+d-e_f"
    for _ in range(n):
        k = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(k))
        # bias toward trailing line-terminators
        r = rng.random()
        if r < 0.30:
            s = s + "\n"
        elif r < 0.40:
            s = s + "\r\n"
        elif r < 0.45:
            s = s + "\r"
        yield s


def run(label, oracle, ascii_mode, rng):
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_valid(s, ascii_mode)
        orc = oracle(s)
        if shadow != orc:
            disagreements.append((s, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL [%s]: %d disagreement(s) over %d inputs:"
              % (label, len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return None
    return count


def main():
    live = _live_oracle_factory()
    if live is not None:
        ascii_oracle, uni_oracle = live
        oracle_kind = "live patched Django validators"
    else:
        ascii_oracle, uni_oracle = _re_oracle_factory()
        oracle_kind = "re fallback (transliterated patched regex %r)" % PATTERN

    rng = random.Random(SEED)
    ca = run("ASCII", ascii_oracle, True, rng)
    if ca is None:
        return 1
    cu = run("Unicode", uni_oracle, False, rng)
    if cu is None:
        return 1
    print("G-CONF OK: R/I shadow of validateName agrees with %s on %d ASCII + "
          "%d Unicode inputs (seed=%d), 0 disagreements." % (oracle_kind, ca, cu, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
