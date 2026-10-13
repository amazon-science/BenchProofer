#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13794.

This bundle consumes NO `@ContractOnly` axiom. The single changed operation —
a deferred-evaluation proxy participating in the binary `+` on both sides — is
modelled DEEPLY as ordered sequence concatenation (`forward_combine` / `reverse_combine`
in model.py). G-AX therefore validates that deep model against the REAL patched
methods (`__proxy__.__add__` / `__proxy__.__radd__`) executed on a live
`lazy()` proxy:

  (A-reference, __add__)   realized(self) + other        == concat(realized, other)
  (A-reference, __radd__)  other + realized(self)        == concat(other, realized)

It builds proxies the way the real code does (`lazy(func, *resultclasses)`) and
exercises the two F2P-relevant carriers: text (the `add` template-filter cases,
`str` operands) and int (the `test_lazy_add` case). It imports only the module
the patch edits (`django.utils.functional`), which is present in the eval
container; nothing test-specific. Exit 0 iff every observation matches the
model.
"""
import random
import sys

from django.utils.functional import lazy


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def model_add(realized, other):
    """Reference for model.py `forward_combine`: realized ++ other (ordered concat)."""
    return realized + other


def model_radd(realized, other):
    """Reference for model.py `reverse_combine`: other ++ realized (ordered concat)."""
    return other + realized


def lazy_str(value):
    """A text proxy whose realized value is `value` (mirrors gettext_lazy)."""
    return lazy(lambda: value, str)()


def lazy_int(value):
    """An int proxy whose realized value is `value` (mirrors lazy(lambda:4,int))."""
    return lazy(lambda: value, int)()


# --- the checks --------------------------------------------------------------

def check_text(realized, other):
    """Real proxy.__add__ / __radd__ on str operands == the deep model."""
    p = lazy_str(realized)
    # LEFT operand: proxy + other  ->  realized ++ other
    observed_add = p + other
    expected_add = model_add(realized, other)
    assert observed_add == expected_add, (
        "forward_combine unsound on (%r, %r): real %r, model %r"
        % (realized, other, observed_add, expected_add))
    # RIGHT operand: other + proxy  ->  other ++ realized
    observed_radd = other + p
    expected_radd = model_radd(realized, other)
    assert observed_radd == expected_radd, (
        "reverse_combine unsound on (%r, %r): real %r, model %r"
        % (realized, other, observed_radd, expected_radd))


def check_int(realized, other):
    """Real proxy participates in int + (the test_lazy_add carrier)."""
    p = lazy_int(realized)
    assert p + other == realized + other, (
        "forward_combine unsound (int) on (%r,%r)" % (realized, other))
    assert other + p == other + realized, (
        "reverse_combine unsound (int) on (%r,%r)" % (realized, other))
    # both operands lazy (test_lazy_add: lazy_4() + lazy_5())
    q = lazy_int(other)
    assert p + q == realized + other, (
        "forward_combine unsound (lazy+lazy int) on (%r,%r)" % (realized, other))


def main():
    # --- boundary text cases (the F2P add08/add09 shapes + edges) ----------
    text_boundary = [
        ("string", "lazy"),          # test_add08 / add09 ('string' + 'lazy')
        ("", ""),
        ("", "x"),
        ("x", ""),
        ("a", "b"),
        ("Joe's", " Crab Shack"),
        ("<b>", "</b>"),
        ("café", "  ☕"),
        ("multi\nline", "\ttabbed"),
        ("123", "456"),
    ]
    for a, b in text_boundary:
        check_text(a, b)

    # --- randomized text fuzz ---------------------------------------------
    rng = random.Random(13794)
    alphabet = list("abcXYZ0 \t\n&<>'\"é☕;#x39")
    for _ in range(20000):
        a = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        b = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        check_text(a, b)

    # --- int cases (test_lazy_add) ----------------------------------------
    int_boundary = [(4, 5), (0, 0), (-3, 7), (5, 4), (1000000, -1)]
    for a, b in int_boundary:
        check_int(a, b)
    for _ in range(5000):
        check_int(rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6))

    print("G-AX OK: deep concatenation model (forward_combine/reverse_combine) == real "
          "__proxy__.__add__/__radd__ on %d text boundary + 20000 text fuzz + "
          "%d int boundary + 5000 int fuzz inputs"
          % (len(text_boundary), len(int_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
