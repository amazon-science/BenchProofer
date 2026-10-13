#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12143 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`str`, list of (key,value)
              pairs), via the mapping.md bijection (`List Char` ↔ `str`,
              `Char.ofNat (ord ch)` ↔ ch). This is matchesKey / stripPrefix /
              takeDigits / atEnd / editedPks spelled out in Python. There are NO
              A-tagged callees in this bundle's impl region (mapping.md §3), so
              the shadow is pure R/I.
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `django.contrib.admin.options.ModelAdmin._get_edited_object_pks`
              applied at base_commit (the harness applies patch.diff before this
              runs). We invoke it unbound with a duck-typed `self`/`request` so
              the actual patched line — re.compile(r'{}-\d+-{}$'.format(
              re.escape(prefix), self.model._meta.pk.name)).match(key) — runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 12143
N_FUZZ = 100_000


def _setup_django():
    """Minimal settings so `django.contrib.admin.options` imports. We only need
    the patched `ModelAdmin._get_edited_object_pks` method object; no DB access,
    no app registry beyond what the import touches."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


# --- the R/I shadow: Solution.lean matchesKey/editedPks, transliterated -------

def _strip_prefix(pat, s):
    """stripPrefix: if `pat` is exactly the leading segment of `s`, return the
    remainder; else None. Exact code-point comparison (literal match)."""
    if s[: len(pat)] == pat:
        return s[len(pat):]
    return None


# isDigit / digitRanges transliterated: the decimal-digit code points of every
# decimal number system (Unicode Nd, per the engine's shipped Unicode data),
# as inclusive scalar-value bounds. Spelled out (NOT delegated to the re
# module) so the shadow stays independent of the oracle.
_DIGIT_RANGES = [
    (0x30, 0x39), (0x660, 0x669), (0x6F0, 0x6F9), (0x7C0, 0x7C9),
    (0x966, 0x96F), (0x9E6, 0x9EF), (0xA66, 0xA6F), (0xAE6, 0xAEF),
    (0xB66, 0xB6F), (0xBE6, 0xBEF), (0xC66, 0xC6F), (0xCE6, 0xCEF),
    (0xD66, 0xD6F), (0xDE6, 0xDEF), (0xE50, 0xE59), (0xED0, 0xED9),
    (0xF20, 0xF29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17E0, 0x17E9),
    (0x1810, 0x1819), (0x1946, 0x194F), (0x19D0, 0x19D9), (0x1A80, 0x1A89),
    (0x1A90, 0x1A99), (0x1B50, 0x1B59), (0x1BB0, 0x1BB9), (0x1C40, 0x1C49),
    (0x1C50, 0x1C59), (0xA620, 0xA629), (0xA8D0, 0xA8D9), (0xA900, 0xA909),
    (0xA9D0, 0xA9D9), (0xA9F0, 0xA9F9), (0xAA50, 0xAA59), (0xABF0, 0xABF9),
    (0xFF10, 0xFF19), (0x104A0, 0x104A9), (0x11066, 0x1106F),
    (0x110F0, 0x110F9), (0x11136, 0x1113F), (0x111D0, 0x111D9),
    (0x112F0, 0x112F9), (0x11450, 0x11459), (0x114D0, 0x114D9),
    (0x11650, 0x11659), (0x116C0, 0x116C9), (0x11730, 0x11739),
    (0x118E0, 0x118E9), (0x11C50, 0x11C59), (0x16A60, 0x16A69),
    (0x16B50, 0x16B59), (0x1D7CE, 0x1D7FF), (0x1E950, 0x1E959),
]


def _is_digit(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _DIGIT_RANGES)


def _take_digits(s):
    """takeDigits: maximal leading run of decimal digits (any decimal number
    system per _DIGIT_RANGES), and the rest."""
    i = 0
    while i < len(s) and _is_digit(s[i]):
        i += 1
    return s[:i], s[i:]


def _at_end(s):
    """atEnd: end-of-input position with re's default trailing-\\n tolerance."""
    return s == "" or s == "\n"


def shadow_matches_key(pfx, pkname, key):
    """matchesKey (pfx pkname key) transliterated."""
    r1 = _strip_prefix(pfx, key)
    if r1 is None:
        return False
    if not r1.startswith("-"):
        return False
    r2 = r1[1:]
    digits, rest = _take_digits(r2)
    if digits == "":
        return False
    if not rest.startswith("-"):
        return False
    r3 = rest[1:]
    tail = _strip_prefix(pkname, r3)
    if tail is None:
        return False
    return _at_end(tail)


def shadow_edited_pks(pfx, pkname, items):
    """editedPks: in-order keep-if-match selection of values."""
    return [v for (k, v) in items if shadow_matches_key(pfx, pkname, k)]


# --- the oracle: the REAL patched _get_edited_object_pks ----------------------

class _FakePk:
    def __init__(self, name):
        self.name = name


class _FakeMeta:
    def __init__(self, name):
        self.pk = _FakePk(name)


class _FakeModel:
    def __init__(self, name):
        self._meta = _FakeMeta(name)


class _FakeSelf:
    def __init__(self, name):
        self.model = _FakeModel(name)


class _FakePOST:
    """Duck-typed request.POST: .items() yields the (key, value) pairs in order
    (the only thing _get_edited_object_pks observes about request.POST)."""
    def __init__(self, pairs):
        self._pairs = list(pairs)

    def items(self):
        return iter(self._pairs)


class _FakeRequest:
    def __init__(self, pairs):
        self.POST = _FakePOST(pairs)


def oracle_edited_pks(pfx, pkname, items):
    """patch.diff's behaviour: run the REAL patched unbound method so the actual
    re.escape(prefix)-built compiled regex does the matching."""
    from django.contrib.admin.options import ModelAdmin
    fake_self = _FakeSelf(pkname)
    fake_request = _FakeRequest(items)
    return list(ModelAdmin._get_edited_object_pks(fake_self, fake_request, pfx))


# --- fuzzing ------------------------------------------------------------------

def _rand_pkname(rng):
    """A Python identifier (what self.model._meta.pk.name always is): a letter or
    underscore, then identifier chars. No regex metacharacters."""
    first = rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    rest = "".join(
        rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")
        for _ in range(rng.randint(0, 4)))
    return first + rest


# key alphabet: ASCII digits, separators, letters, regex metacharacters — so
# the literal-vs-pattern divergence is exercised — PLUS non-Latin decimal
# digits and digit-adjacent non-digits, so the Unicode-aware digit class of
# the matcher (mapping.md §2.2) is exercised against the real engine.
# Includes '\n' to probe the $ / atEnd trailing-newline edge.
_UNI_DIGITS = ["٠", "٩", "۰", "०", "๐", "０",
               "９", "\U000104A0", "\U0001D7CE", "\U0001E950"]
# near-misses: superscripts/fractions/letterlike — NOT decimal digits.
_UNI_NONDIGITS = ["²", "½", "⁰", "①", "〇"]
_KEY_ALPHABET = (list("ab01239-_form") + list(r'$.*+?()[]{}^|\\')
                 + [" ", "\n"] + _UNI_DIGITS + _UNI_NONDIGITS)
# prefix alphabet: heavy on regex metacharacters (the whole point of the fix).
_PFX_ALPHABET = list("abform-_01") + list(r'$.*+?()[]{}^|\\') + ["\n"]


def fuzz_cases(n, rng):
    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    # empty everything
    yield ("", "id", [])
    # the F2P scenario: a '$'-bearing prefix; the matching key must be kept
    yield ("form$", "uuid", [("form$-0-uuid", "PKVAL"), ("form$-0-load", "10")])
    # plain prefix, the original passing test shape
    yield ("form", "id", [("form-0-id", "A"), ("form-1-id", "B"), ("x", "C")])
    # every metacharacter as a lone prefix, with a literally-matching key
    for mc in r'$.*+?()[]{}^|\\':
        pfx = "f" + mc + "g"
        yield (pfx, "id", [(pfx + "-7-id", "M"), (pfx + "Xz-7-id", "N")])
    # trailing-newline tolerance of $ / atEnd
    yield ("p", "id", [("p-3-id\n", "NL"), ("p-3-id\n\n", "NO"), ("p-3-id", "Y")])
    # non-digit / empty digit run must NOT match
    yield ("p", "id", [("p--id", "x"), ("p-a-id", "y"), ("p-12-id", "z")])
    # pkname carrying chars that are identifier-legal
    yield ("pre", "custom_pk_0", [("pre-5-custom_pk_0", "ok"),
                                  ("pre-5-custom_pk_0extra", "no")])
    # non-Latin decimal digits in the index position MUST match (the digit
    # class is Unicode-aware); non-decimal digit-like chars must NOT.
    for d in _UNI_DIGITS:
        yield ("form", "id", [("form-%s-id" % d, "U1"),
                              ("form-%s7-id" % d, "U2"),
                              ("form-7%s-id" % d, "U3")])
    for nd in _UNI_NONDIGITS:
        yield ("form", "id", [("form-%s-id" % nd, "N1"),
                              ("form-3%s-id" % nd, "N2")])

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(n):
        pfx = "".join(rng.choice(_PFX_ALPHABET) for _ in range(rng.randint(0, 5)))
        pkname = _rand_pkname(rng)
        pairs = []
        m = rng.randint(0, 5)
        for _ in range(m):
            k = "".join(rng.choice(_KEY_ALPHABET) for _ in range(rng.randint(0, 14)))
            pairs.append((k, "v%d" % rng.randint(0, 999)))
        # with good probability, inject a key engineered to match literally so
        # the "should match" path is exercised, not only "should not match".
        if rng.random() < 0.6:
            digit_pool = (list("0123456789") + _UNI_DIGITS
                          if rng.random() < 0.3 else "0123456789")
            digits = "".join(rng.choice(digit_pool)
                             for _ in range(rng.randint(1, 3)))
            suffix = "\n" if rng.random() < 0.15 else ""
            pairs.insert(rng.randint(0, len(pairs)),
                         (pfx + "-" + digits + "-" + pkname + suffix, "HIT"))
        yield (pfx, pkname, pairs)


def main():
    _setup_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for pfx, pkname, items in fuzz_cases(N_FUZZ, rng):
        count += 1
        shadow = shadow_edited_pks(pfx, pkname, items)
        oracle = oracle_edited_pks(pfx, pkname, items)
        if shadow != oracle:
            disagreements.append((pfx, pkname, items, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for pfx, pkname, items, sh, orc in disagreements:
            print("  pfx=%r pkname=%r items=%r shadow=%r oracle=%r"
                  % (pfx, pkname, items, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of editedObjectPks agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
