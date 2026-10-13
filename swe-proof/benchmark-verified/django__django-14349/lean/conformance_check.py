#!/usr/bin/env python3
"""G-CONF for django__django-14349.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_validateUrl` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `URLValidator.__call__`,
over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

The single behavioral edit is the raw-character GUARD added before the structural
checks:
  * value contains any of {'\\t','\\r','\\n'}  -> rejected
                                                 (containsForbidden <-> unsafe_chars.intersection)
  * otherwise                                  -> the unchanged structural verdict
                                                 (structurallyValid <-> the rest of __call__)

Type bijection (mapping.md): value<->value (str via List Char), result<->verdict
(True = does not raise ValidationError, False = raises).

The shadow realizes `structurallyValid` by running the REAL patched validator
with the guard neutralized (instance.unsafe_chars = frozenset()), so the only
difference exercised is the guard itself. Validation is deterministic for a fixed
input.

stdlib-only; no hypothesis required.
"""
import random
import sys


def main() -> int:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY="conf-check-secret-key-14349",
            USE_I18N=False,
            USE_TZ=True,
            DATABASES={},
            INSTALLED_APPS=[],
        )
        django.setup()

    from django.core.validators import URLValidator
    from django.core.exceptions import ValidationError

    def verdict(validator, value):
        """True iff the validator accepts (does not raise ValidationError)."""
        try:
            validator(value)
            return True
        except ValidationError:
            return False

    # The real patched validator (guard active).
    real = URLValidator()

    # A validator whose guard is neutralized: realizes `structurallyValid`, the
    # UNCHANGED rest of __call__ (scheme/regex/IDN/IPv6) with no raw-char guard.
    structural = URLValidator()
    structural.unsafe_chars = frozenset()

    def contains_unsafe(value):
        """R model of `containsForbidden` <-> unsafe_chars.intersection(value)."""
        return any(c in ("\t", "\r", "\n") for c in value)

    def oracle(value):
        """Behavior of the patched repo `__call__` for this input."""
        return verdict(real, value)

    def shadow(value):
        """R/I transliteration of implementation_validateUrl (Lean).

        containsForbidden <-> the real unsafe_chars.intersection truthiness;
        structurallyValid <-> the real validator with the guard neutralized."""
        if contains_unsafe(value):
            return False
        return verdict(structural, value)

    # Pool of URL bodies spanning valid, invalid-scheme, IDN, IPv6, and junk.
    BODY_POOL = [
        "http://www.djangoproject.com/",
        "https://www.example.com/path?q=1#frag",
        "ftp://files.example.com/a/b",
        "ftps://secure.example.com/",
        "http://[::ffff:192.9.5.5]",
        "http://[::ffff:192.9.5.5]/path",
        "http://localhost:8000/",
        "http://127.0.0.1/",
        "http://www.djangoéproject.com/",
        "no_scheme",
        "foo://bar.com",
        "http://",
        "http://www.asdasdasdasdsadfm.com.br ",
        "http://www.asdasdasdasdsadfm.com.br z",
        "",
        "http://example.com",
        "javascript:alert(1)",
        "http://[::1]",
    ]
    UNSAFE = ["\t", "\r", "\n"]
    # Near-misses: other whitespace that is NOT in the disallowed set.
    SAFE_WS = [" ", "\x0b", "\x0c", "\xa0", ""]

    def rand_value(rng):
        body = rng.choice(BODY_POOL)
        mode = rng.randint(0, 3)
        if mode == 0:
            # inject one or more disallowed control chars at random positions
            chars = list(body)
            k = rng.randint(1, 3)
            for _ in range(k):
                pos = rng.randint(0, len(chars))
                chars.insert(pos, rng.choice(UNSAFE))
            return "".join(chars)
        if mode == 1:
            # inject a safe-whitespace near-miss (must NOT trigger the guard)
            chars = list(body)
            pos = rng.randint(0, len(chars))
            chars.insert(pos, rng.choice(SAFE_WS))
            return "".join(chars)
        # mode 2/3: leave the body unchanged
        return body

    rng = random.Random(14349)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        value = rand_value(rng)
        try:
            o = oracle(value)
        except Exception as e:  # pragma: no cover
            o = ("EXC", type(e).__name__)
        try:
            s = shadow(value)
        except Exception as e:  # pragma: no cover
            s = ("EXC", type(e).__name__)
        if o != s:
            disagreements += 1
            if first is None:
                first = (value, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
