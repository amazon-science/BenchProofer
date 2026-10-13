#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13212 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `refinement.md`: the deep
error-construction model of `Solution.lean` (`buildReport` / `checkOutcome` —
on a failing input the rejection report binds the input to the `"value"` key)
transliterated to Python, differential-tested against `patch.diff`'s behaviour
driven through the REAL patched validators at base_commit+gold.

ORACLE — the gold-patched validators themselves. We run each real validator on
each input and observe, via the SAME rendering the placeholder change targets, a
custom `%(value)s` message template: the rendered error text. The patch's whole
content is that this rendered text now equals the offending input
(`str(value)`); pre-patch it raised `KeyError`/left `%(value)s` unbound. The
unchanged per-site validity TEST is exercised by the real validator; the spec's
free `isValid` is whichever branch the real test takes.

SHADOW — `Solution.lean`'s `checkOutcome`/`buildReport`, transliterated: on a
rejected input the report's `"value"` binding renders to `str(value)`; an
accepted input raises nothing.

For each (validator, value) we compare the pair
  (accepted?, rendered "%(value)s" text on rejection)
between ORACLE and SHADOW. Exit 0 iff zero disagreements.

stdlib + Django only; the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
from decimal import Decimal

# Minimal settings so importing the validators + ValidationError rendering is
# safe: lazy translation of the messages and `%`-templating touch neither the
# database nor the app registry, so `django.setup()` is deliberately avoided.
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_I18N=False,
    )

from django.core import validators                       # patched
from django.core.exceptions import ValidationError

SEED = 13212

# A custom message that interpolates ONLY the value placeholder — exactly the
# capability the patch adds (problem_statement's `%(value)s`).
VALUE_TEMPLATE = "%(value)s"


# ---- ORACLE: run the real patched validator, render %(value)s ---------------
def oracle_observe(make_validator, code, value):
    """Run the real validator on `value`. On rejection (the failing branch),
    render the custom `%(value)s` template against the raised error's params —
    the observable the patch changes. Returns (accepted, rendered_or_None)."""
    validator = make_validator()
    try:
        validator(value)
        return (True, None)
    except ValidationError as e:
        # Reproduce ValidationError.__iter__'s `message %= error.params` for the
        # error whose code matches the templated code (the one the test targets).
        err = _select_error(e, code)
        if err is None or err.params is None:
            return (False, "__no_params__")
        try:
            return (False, VALUE_TEMPLATE % err.params)
        except KeyError:
            return (False, "__value_unbound__")


def _select_error(exc, code):
    for err in exc.error_list:
        if getattr(err, "code", None) == code:
            return err
    # fall back to the sole error if codes are not annotated
    return exc.error_list[0] if exc.error_list else None


# ---- SHADOW: Solution.lean checkOutcome / buildReport, transliterated --------
def shadow_observe(is_valid, value):
    """checkOutcome(isValid, code, oldParams, value): accept with no report, or
    reject with a report binding `"value"` -> str(value). Rendering `%(value)s`
    against that binding yields exactly `str(value)` (buildReport appends
    ("value", value); lookupKey finds it)."""
    if is_valid:
        return (True, None)
    return (False, str(value))


# ---- the validators under test (mapping.md §1.1) ----------------------------
# Each entry: (label, make_validator, code, value-generator). The `code` is the
# ValidationError code whose custom message the F2P tests override.
class _NamedFile:
    """Minimal stand-in for an uploaded file: only `.name` is read by
    FileExtensionValidator (`Path(value.name).suffix`)."""
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name


def _decimal_validator():
    return validators.DecimalValidator(max_digits=2, decimal_places=1)


def cases(rng):
    """Yield (label, make_validator, code, value) test points. Boundary cases
    from the F2P matrix first, then fuzz."""
    # --- string validators -------------------------------------------------
    str_specs = [
        ("validate_integer", lambda: validators.validate_integer, "invalid"),
        ("validate_email", lambda: validators.validate_email, "invalid"),
        ("validate_slug", lambda: validators.validate_slug, "invalid"),
        ("validate_unicode_slug", lambda: validators.validate_unicode_slug, "invalid"),
        ("validate_ipv4_address", lambda: validators.validate_ipv4_address, "invalid"),
        ("validate_ipv6_address", lambda: validators.validate_ipv6_address, "invalid"),
        ("validate_ipv46_address", lambda: validators.validate_ipv46_address, "invalid"),
        ("validate_comma_separated_integer_list",
         lambda: validators.validate_comma_separated_integer_list, "invalid"),
        ("int_list_validator", lambda: validators.int_list_validator(), "invalid"),
        ("URLValidator", lambda: validators.URLValidator(), "invalid"),
        ("RegexValidator", lambda: validators.RegexValidator('[0-9]+'), "invalid"),
        ("ProhibitNull",
         lambda: validators.ProhibitNullCharactersValidator(), "null_characters_not_allowed"),
    ]
    str_values = [
        "-42.5", "a", "a@b\n.com", "a\n@b.com", "你 好", "256.1.1.1", "1:2",
        "a,b,c", "-1,2,3", "no_scheme", "http://test[.com", "http://[::1:2::3]/",
        "http://" + ".".join(["a" * 35 for _ in range(9)]), "xxxxxx",
        "a\0b", "", "valid", "123", "abc@example.com", "192.168.0.1",
        "::1", "1,2,3", "http://example.com", "01", "0",
    ]
    for label, mk, code in str_specs:
        for v in str_values:
            yield (label, mk, code, v)

    # --- DecimalValidator (Decimal inputs) ---------------------------------
    dec_values = ["NaN", "123", "0.12", "12", "1.0", "0", "-5", "9.9", "100",
                  "0.01", "Infinity", "-Infinity"]
    for v in dec_values:
        try:
            d = Decimal(v)
        except Exception:                                # noqa: BLE001
            continue
        for code in ("invalid", "max_digits", "max_decimal_places",
                     "max_whole_digits"):
            yield ("DecimalValidator", _decimal_validator, code, d)

    # --- FileExtensionValidator (objects with .name) -----------------------
    file_names = ["myfile.txt", "image.png", "a.jpg", "noext", "x.PDF",
                  "archive.tar.gz", "data.csv"]
    for name in file_names:
        yield ("FileExtensionValidator",
               lambda: validators.FileExtensionValidator(allowed_extensions=["png", "jpg"]),
               "invalid_extension", _NamedFile(name))

    # --- fuzz: random strings through every string validator ---------------
    alphabet = list("abcABC0123 .@:/-_,\n\0[]:你好") + ["é", "•"]
    for _ in range(4000):
        k = rng.randint(0, 20)
        v = "".join(rng.choice(alphabet) for _ in range(k))
        label, mk, code = rng.choice(str_specs)
        yield (label, mk, code, v)


def _rendered_value(observe_pair, value):
    """Normalize the observed rendering: the SHADOW renders to str(value); the
    ORACLE renders %(value)s which for a non-finite Decimal etc. is also
    str(value). We compare the (accepted, rendered) pairs directly."""
    return observe_pair


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for label, mk, code, value in cases(rng):
        count += 1
        oracle = oracle_observe(mk, code, value)
        # the real validator decides validity; the shadow mirrors that branch.
        is_valid = oracle[0]
        shadow = shadow_observe(is_valid, value)
        # On rejection both must render the value to str(value); on acceptance
        # neither raises.
        if oracle[0] != shadow[0]:
            disagreements.append((label, value, shadow, oracle))
        elif not oracle[0]:
            # rejected: the gold-patched error MUST bind value -> str(value)
            if oracle[1] != shadow[1]:
                disagreements.append((label, value, shadow, oracle))
        if len(disagreements) >= 8:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for label, v, sh, orc in disagreements:
            print("  validator=%s input=%s shadow=%s oracle=%s"
                  % (label, ascii(v), ascii(sh), ascii(orc)))
        return 1
    print("G-CONF OK: R/I shadow of checkValue (value-carrying rejection report) "
          "agrees with patch.diff behaviour through the real validators on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
