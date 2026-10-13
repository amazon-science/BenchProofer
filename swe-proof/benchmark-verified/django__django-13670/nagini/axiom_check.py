#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13670.

This bundle has NO axiomatized callee: the abbreviated-year rendering is pure
integer arithmetic and digit emission, modelled DEEPLY in model.py (no
@ContractOnly). What this script validates is the deep-model fidelity (an
A-reference style check): the per-year code-point mapping that model.py's
postcondition pins down —

    result = [ ord('0') + (year % 100) // 10,
               ord('0') + (year % 100) % 10 ]

is exactly the two-character string produced by the real renderer's expression
``'%02d' % (year % 100)`` for every calendar year ``datetime`` admits
(1..9999), including every boundary the issue calls out (years < 1000, < 100,
< 10). It also confirms the *old* expression ``str(year)[2:]`` disagrees on the
discriminating sub-100 / sub-1000 regime, so the spec genuinely senses the
change.

Imports nothing repo-specific (stdlib only). Exit 0 iff every obligation holds.
"""
import sys

ZERO = ord('0')  # 48


def model_render(year):
    """model.py's pinned mapping, as a list of code points."""
    v = year % 100
    return [ZERO + (v // 10), ZERO + (v % 10)]


def real_render(year):
    """The real renderer's post-change expression, as a list of code points."""
    s = '%02d' % (year % 100)
    return [ord(ch) for ch in s]


def old_render(year):
    """The pre-change expression str(year)[2:], as a list of code points."""
    return [ord(ch) for ch in str(year)[2:]]


def main():
    # --- deep-model fidelity: model == real renderer on the full year domain
    for year in range(1, 10000):
        m = model_render(year)
        r = real_render(year)
        assert m == r, (
            "deep model unsound at year %d: model=%r real('%%02d'%%(y%%100))=%r"
            % (year, m, r))
        # structural obligations the postcondition states
        assert len(m) == 2, "render width != 2 at year %d: %r" % (year, m)
        assert all(ZERO <= c <= ZERO + 9 for c in m), (
            "non-digit code point at year %d: %r" % (year, m))

    # --- the discriminating regime: the old expression differs (so the spec
    #     senses the change). The issue's witnesses: 4 -> '04', 42 -> '42',
    #     476 -> '76', plus the originally reported 123 -> '23'.
    witnesses = {4: '04', 42: '42', 476: '76', 123: '23', 99: '99', 9: '09'}
    for year, expected in witnesses.items():
        assert real_render(year) == [ord(c) for c in expected], (
            "real renderer wrong at %d: got %r want %r"
            % (year, real_render(year), expected))
    # every year below 100 is a counterexample to the old expression
    differ = sum(1 for y in range(1, 10000) if old_render(y) != model_render(y))
    assert differ > 0, "old expression never differs — spec would not sense the change"
    for y in (4, 42, 9, 99):
        assert old_render(y) != model_render(y), (
            "old str(year)[2:] unexpectedly matched at year %d" % y)

    print("G-AX OK: deep model == real '%%02d'%%(year%%100) on all 9999 years "
          "(1..9999); width 2 + digit code points; old str(year)[2:] differs "
          "on %d years (incl. all sub-100)." % differ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
