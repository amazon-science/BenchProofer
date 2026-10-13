#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15098 (plan §4).

Executes the REAL unchanged callee the modeled `resolvePathLanguage` relies on
(`get_supported_language_variant`, the opaque `listedLanguage` axiom) and asserts
every observation meets the axiom's contract (Solution.lean axioms region), as
bound in mapping.md §3.2.

The one A-consumed axiom:

  (A-consumed) `listedLanguage : List Char -> Bool -> Option (List Char)`
      ↔  `django.utils.translation.trans_real.get_supported_language_variant`
         (trans_real.py:464). Modeled OPAQUELY — the spec asserts NO property of
         its output, only that the resolved language is *whatever this callee
         returns* for the extracted tag, with its `LookupError` folded into
         `none` (the `except LookupError: return None` of get_language_from_path).

Modeling an effectful Python callee as a Lean *function* `List Char -> Bool ->
Option (List Char)` is sound iff, under a fixed LANGUAGES/LANGUAGE_CODE
configuration, the callee is:

  (a) DETERMINISTIC / FUNCTIONAL — same (lang_code, strict) -> equal result,
      across repeated calls AND across cache resets (no hidden state beyond the
      configuration); and
  (b) a TOTAL DICHOTOMY into Option — every call either returns a `str`
      (-> some) or raises `LookupError` (-> none); never another exception,
      never `None`, never a non-`str`. So `Option (List Char)` losslessly
      captures the only two observable outcomes (mapping.md §3.2).

This is the WEAKEST sufficient contract (directive 7): we claim nothing about
*which* language a tag resolves to, only that the resolution is a deterministic
partial function with exactly two outcome shapes. The change under spec is the
prefix matcher (validated by G-CONF), NOT this callee.

Imports the repo's own `django.utils.translation` module (in-container) + stdlib.
Exit 0 iff every obligation holds.
"""
import random
import string
import sys


def _configure(languages, language_code="en-us"):
    """Configure Django settings (idempotent across configs via reset)."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=True,
            LANGUAGE_CODE=language_code,
            LANGUAGES=list(languages),
            INSTALLED_APPS=[],
            DATABASES={},
        )
        import django
        django.setup()
    else:
        settings.LANGUAGES = list(languages)
        settings.LANGUAGE_CODE = language_code


def _reset_caches():
    """Clear every lru_cache the callee and its helpers carry, so a 'fresh'
    resolution recomputes from the current configuration (determinism test (a))."""
    from django.utils.translation import trans_real
    for fn in (trans_real.get_supported_language_variant,
               trans_real.get_languages,
               trans_real.check_for_language):
        try:
            fn.cache_clear()
        except AttributeError:
            pass


def _observe(g, tag, strict):
    """Run the real callee; map its outcome to the Option-shaped observation the
    axiom models: ('some', str) or ('none',). Assert TOTAL DICHOTOMY (b)."""
    try:
        r = g(tag, strict=strict)
    except LookupError:
        return ("none",)
    except Exception as e:  # noqa: BLE001 — any other effect breaks the model
        raise AssertionError(
            "listedLanguage unsound: get_supported_language_variant(%r, strict=%r) "
            "raised %r — the model admits only str-return or LookupError"
            % (tag, strict, e))
    assert isinstance(r, str), (
        "listedLanguage unsound: get_supported_language_variant(%r, strict=%r) "
        "returned non-str %r (model: some <List Char>)" % (tag, strict, r))
    return ("some", r)


def _check_config(languages, language_code, tags, fuzz_tags):
    from django.utils.translation import trans_real
    g = trans_real.get_supported_language_variant

    all_tags = list(tags) + list(fuzz_tags)
    n = 0
    for tag in all_tags:
        for strict in (False, True):
            n += 1
            # (a) determinism across a cache reset + repeated calls.
            _reset_caches()
            o1 = _observe(g, tag, strict)
            o2 = _observe(g, tag, strict)          # warm cache
            _reset_caches()
            o3 = _observe(g, tag, strict)          # fresh recompute
            assert o1 == o2 == o3, (
                "listedLanguage unsound: get_supported_language_variant(%r, "
                "strict=%r) not deterministic: %r vs %r vs %r"
                % (tag, strict, o1, o2, o3))
            # (b) total dichotomy already asserted inside _observe.
    return n


def main():
    # --- F2P override configuration (tests.py:test_get_language_from_path_real,
    #     and the broadened LANGUAGES of the test_patch) -----------------------
    f2p_languages = [
        ('en', 'English'),
        ('en-latn-us', 'Latin English'),
        ('en-Latn-US', 'BCP 47 case format'),
        ('de', 'German'),
        ('de-1996', 'German, orthography of 1996'),
        ('de-at', 'Austrian German'),
        ('de-ch-1901', 'German, Swiss variant, traditional orthography'),
        ('i-mingo', 'Mingo'),
        ('kl-tunumiit', 'Tunumiisiut'),
        ('nan-hani-tw', 'Hanji'),
        ('pl', 'Polish'),
    ]
    # boundary tags: the F2P + issue tags, generic-fallback tags, sentinels.
    boundary_tags = [
        'en', 'en-gb', 'en-latn-us', 'en-Latn-US', 'de', 'de-1996', 'de-at',
        'de-ch', 'de-ch-1901', 'i-mingo', 'kl-tunumiit', 'nan-hani-tw', 'pl',
        'xyz', 'de-simple-page-test', 'de-simple', 'pt', 'pt-br', 'zh-hant-tw',
        '', 'en-us', 'EN', 'En-Gb',
    ]

    _configure(f2p_languages, language_code='en-us')

    # randomized ASCII langtag fuzz (mapping.md §2 domain): lang[-sub[-sub]].
    rng = random.Random(15098)
    letters = string.ascii_lowercase
    fuzz_tags = []
    for _ in range(2000):
        def subtag():
            k = rng.randint(1, 4)
            return "".join(rng.choice(letters + string.digits) for _ in range(k))
        parts = [subtag()]
        for _ in range(rng.randint(0, 3)):
            parts.append(subtag())
        fuzz_tags.append("-".join(parts))

    n1 = _check_config(f2p_languages, 'en-us', boundary_tags, fuzz_tags)

    # --- default-ish configuration: a second LANGUAGES set, to confirm the
    #     callee remains a deterministic total-dichotomy function under a
    #     different ambient configuration (no hidden global state beyond it) ---
    alt_languages = [
        ('en', 'English'), ('en-us', 'American English'),
        ('fr', 'French'), ('fr-ca', 'Canadian French'),
        ('pt-br', 'Brazilian Portuguese'), ('zh-hans', 'Simplified Chinese'),
    ]
    _configure(alt_languages, language_code='en')
    _reset_caches()
    n2 = _check_config(alt_languages, 'en',
                       boundary_tags + ['fr', 'fr-ca', 'fr-fr', 'pt', 'zh-hans-cn'],
                       fuzz_tags[:500])

    print("G-AX OK: listedLanguage (get_supported_language_variant) is a "
          "deterministic total-dichotomy function (str-return -> some / "
          "LookupError -> none) on %d (tag,strict) observations across 2 "
          "configurations (seed=15098)." % (n1 + n2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
