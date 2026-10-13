#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13023 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `refinement.md`: the deep
outcome model of `Solution.lean` (`toDecimalResult` — null and float inputs take
their fast paths; otherwise the interpretation attempt's outcome decides, and
EVERY recoverable interpretation failure becomes the field's invalid-value error
rather than escaping) transliterated to Python, differential-tested against
`patch.diff`'s behaviour driven through the REAL patched function at
base_commit+gold.

ORACLE — the gold-patched `DecimalField.to_python` itself. We run it on each
input and observe its outcome, classified into the four `PyResult` kinds:
  * a returned `Decimal` value          -> ("ret", str(decimal))
  * the null fast path returning `None`  -> ("none",)
  * the field's `ValidationError`        -> ("verr",)
  * any other exception escaping uncaught-> ("prop", ExceptionTypeName)

SHADOW — `Solution.lean`'s `toDecimalResult`, transliterated. The free
observations are derived exactly as the real code derives them (mapping.md §2):
  * isNone   = value is None
  * isFloat  = isinstance(value, float)
  * floatRes = the field-context float conversion (unchanged fast path)
  * conv     = the outcome of `decimal.Decimal(value)`: a produced value, or a
               failure classified into invalidOperation / typeError / valueError
               (the recoverable family) / other.
`isRecoverable` maps the first three to `validationError`; `other` propagates.

For each input we compare the (kind, payload) pair between ORACLE and SHADOW.
Exit 0 iff zero disagreements over >=10^5 inputs.

stdlib + Django only; the fuzz seed is pinned (mapping.md §4).
"""
import decimal
import random
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_I18N=False,
    )

from django.core.exceptions import ValidationError      # noqa: E402
from django.db import models                             # noqa: E402

SEED = 13023

# A field instance whose max_digits drives the shared decimal context (mirrors
# the F2P test: DecimalField(max_digits=4, decimal_places=2)). The context only
# affects the float fast path, which is the unchanged path modeled as free.
FIELD = models.DecimalField(max_digits=4, decimal_places=2)


# ---- ORACLE: run the real gold-patched to_python, classify the outcome ------
def oracle_observe(value):
    try:
        out = FIELD.to_python(value)
    except ValidationError:
        return ("verr",)
    except Exception as e:                               # noqa: BLE001
        return ("prop", type(e).__name__)
    if out is None:
        return ("none",)
    return ("ret", str(out))


# ---- SHADOW: Solution.lean toDecimalResult, transliterated ------------------
def _classify_conv(value):
    """conv: attempt to read `value` as a decimal; return either ('converted', d)
    or ('raised', kind) with kind in the ExcKind family."""
    try:
        d = decimal.Decimal(value)
    except decimal.InvalidOperation:
        return ("raised", "invalidOperation")
    except TypeError:
        return ("raised", "typeError")
    except ValueError:
        return ("raised", "valueError")
    except Exception:                                    # noqa: BLE001
        return ("raised", "other")
    return ("converted", d)


_RECOVERABLE = {"invalidOperation", "typeError", "valueError"}


def shadow_observe(value):
    # free observations, derived exactly as the real code derives them
    if value is None:
        return ("none",)
    if isinstance(value, float):
        # unchanged float fast path (free abstraction): reuse the real callee
        return ("ret", str(FIELD.context.create_decimal_from_float(value)))
    conv = _classify_conv(value)
    if conv[0] == "converted":
        return ("ret", str(conv[1]))
    kind = conv[1]
    if kind in _RECOVERABLE:
        return ("verr",)
    return ("prop", _exc_name_for_kind(kind))


def _exc_name_for_kind(kind):
    # `other` is any failure outside the recoverable family. The shadow does not
    # predict its concrete Python type; only the ORACLE path that produces it is
    # compared. `decimal.Decimal` raises only InvalidOperation/TypeError/ValueError
    # for the inputs reachable here, so `other` is unreached in practice — but we
    # keep the leg explicit so an unexpected escape surfaces as a disagreement.
    return "__other__"


# ---- inputs: the F2P matrix + a broad fuzz ----------------------------------
def boundary_values():
    return [
        None,
        # the F2P test_invalid_value matrix (dict/list/set/tuple/bytes/...):
        (), [], {}, set(), object(), complex(),
        "non-numeric string", b"non-numeric byte-string",
        # the original test_to_python cases (must keep passing):
        3, "3.14", 2.0625, 2.1875, 2.4, 3.1415926535897, "abc",
        # really-big / extreme values used by the lookup F2P:
        100000000000, "1e4000", "1E-4000", "-100000000000",
        # decimals, bools, more odd types:
        decimal.Decimal("2"), decimal.Decimal("NaN"), True, False,
        "  1.5  ", "+1.5", "-0", "0", "", "   ", "nan", "inf", "-inf",
        "1_000", "1,000", "1.2.3", "0x10", "1e10", "1.5j",
        float("inf"), float("-inf"), float("nan"), 0.0, -0.0, 1e300,
        b"123", bytearray(b"4.5"), frozenset(), [1, 2], {"a": 1},
        (1,), {1, 2}, range(3), iter([1]),
    ]


def fuzz_values(rng, n):
    digits = "0123456789"
    junk = "abcdefXYZ .,-+eE_/:你好\t\n"
    for _ in range(n):
        kind = rng.randint(0, 9)
        if kind == 0:
            yield rng.randint(-10**18, 10**18)
        elif kind == 1:
            yield rng.uniform(-1e6, 1e6)
        elif kind == 2:
            k = rng.randint(0, 12)
            yield "".join(rng.choice(digits) for _ in range(k))
        elif kind == 3:
            k = rng.randint(0, 12)
            yield "".join(rng.choice(digits + junk) for _ in range(k))
        elif kind == 4:
            k = rng.randint(0, 12)
            yield "".join(rng.choice(junk) for _ in range(k)).encode("utf-8", "replace")
        elif kind == 5:
            yield [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]
        elif kind == 6:
            yield {rng.choice("abc"): rng.randint(0, 9)
                   for _ in range(rng.randint(0, 3))}
        elif kind == 7:
            yield tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 4)))
        elif kind == 8:
            yield {rng.randint(0, 9) for _ in range(rng.randint(0, 3))}
        else:
            yield rng.choice([None, object(), complex(rng.random()),
                              True, False, bytearray(b"x")])


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    inputs = list(boundary_values()) + list(fuzz_values(rng, 100000))
    for value in inputs:
        count += 1
        try:
            oracle = oracle_observe(value)
        except Exception as e:                           # noqa: BLE001
            disagreements.append((ascii(value), "ORACLE-CRASH:" + repr(e), None))
            if len(disagreements) >= 8:
                break
            continue
        shadow = shadow_observe(value)
        if oracle != shadow:
            disagreements.append((ascii(value)[:60], shadow, oracle))
            if len(disagreements) >= 8:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  input=%s shadow=%s oracle=%s" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of toDecimal (recoverable-failure normalisation) "
          "agrees with patch.diff behaviour through the real DecimalField.to_python "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
