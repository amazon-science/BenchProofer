#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-15863.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Exercises the REAL patched `floatformat` and diffs it
against the Python R-shadow of the Lean `implementation_coerceDecimal` skeleton
(per refinement.md) over the full boundary matrix plus >=1e5 randomized draws.

Modeled function: the coercion of an exact decimal input `text` into the working
`Decimal d` inside `floatformat` (defaultfilters.py:153-159). The Lean model
(`problem_spec_coerceDecimal`) pins `result = text`: the working decimal carries
the EXACT value of the input, every significant digit retained.

Observable: for an exact finite Decimal `text` and a positive precision `p` at
least as large as the number of fractional digits of `text`, the rendered string
`floatformat(text, p)` must reproduce the exact value of `text` to `p` fractional
places (ROUND_HALF_UP). This is the F2P generalization
    floatformat(Decimal("123456.123456789012345678901"), 21)
        == "123456.123456789012345678901".

  * ORACLE  = the REAL patched `floatformat(text, p)`.
  * SHADOW  = the model: coerce `d := text` exactly (the impl's primary-read
              leg returns `text`), then render `d` to `p` places. Because the
              post-coercion rendering is UNCHANGED by the patch, any divergence
              signals a coercion that failed to preserve the exact value (the
              bug). The shadow coerces via `Decimal(str(text))`, which is exactly
              the modeled exact path.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed 15863).
"""
import os
import random
import sys
from decimal import Decimal, ROUND_HALF_UP, Context

SEED = 15863
N_RANDOM = 120_000  # >= 1e5


def render_exact(text: Decimal, p: int) -> str:
    """SHADOW: the modeled exact coercion (d == text) followed by a faithful,
    patch-independent rendering to `p` fractional places. Restricted to the
    positive, no-grouping, p>=fractional-digits regime so the rendering reduces
    to a plain fixed-point quantize — the part of floatformat the patch does not
    touch.

    The quantize is performed under a precision-widened Context, exactly as the
    unchanged rendering stage does (the #15789 fix): the default 28-digit
    context would otherwise raise InvalidOperation for inputs whose digit count
    exceeds 28. `prec` is computed identically to the real code so the SHADOW
    reproduces the rendering byte-for-byte for the exact-coercion input `d ==
    text`."""
    d = Decimal(str(text))            # modeled exact coercion: d == text
    exp = Decimal(1).scaleb(-p)
    # widen the working precision the way the unchanged rendering stage does,
    # so a many-digit exact input does not overflow the default context.
    tupl = d.as_tuple()
    m = int(d) - d
    units = len(tupl[1])
    units += -tupl[2] if m else tupl[2]
    prec = abs(p) + units + 1
    q = d.quantize(exp, ROUND_HALF_UP, Context(prec=prec))
    return f"{q:.{p}f}"


def gen_case(rng):
    """A positive exact finite Decimal with up to ~30 significant digits and a
    definite scale, plus a precision p >= its fractional-digit count."""
    int_digits = rng.randint(1, 12)
    frac_digits = rng.randint(0, 25)
    int_part = "".join(rng.choice("0123456789") for _ in range(int_digits)).lstrip("0") or "0"
    frac_part = "".join(rng.choice("0123456789") for _ in range(frac_digits))
    lit = int_part + ("." + frac_part if frac_part else "")
    text = Decimal(lit)
    # p at least the fractional-digit count, so every input digit is reproducible
    p = rng.randint(frac_digits, frac_digits + 6)
    p = max(1, p)
    return text, p


def main():
    sys.path.insert(0, "/testbed")
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False)
        import django
        django.setup()
    except Exception:
        # floatformat does not need a full app registry for these inputs;
        # configure minimally and continue.
        pass
    from django.template.defaultfilters import floatformat

    def oracle(text, p):
        return str(floatformat(text, p))

    def shadow(text, p):
        return render_exact(text, p)

    # ---- boundary / discrete matrix (incl. the exact F2P case) -------------
    boundary = [
        (Decimal("123456.123456789012345678901"), 21),
        (Decimal("42.12345678901234567890"), 20),
        (Decimal("09.000"), 3),
        (Decimal("555.555"), 2),
        (Decimal("0.1"), 1),
        (Decimal("0"), 1),
        (Decimal("7"), 4),
        (Decimal("1.005"), 2),
        (Decimal("99999999.99999999"), 8),
    ]

    rng = random.Random(SEED)
    disagreements = 0
    shown = 0
    checked = 0

    for text, p in boundary:
        o, s = oracle(text, p), shadow(text, p)
        checked += 1
        if o != s:
            disagreements += 1
            if shown < 20:
                print(f"DISAGREE boundary text={text!r} p={p} oracle={o!r} shadow={s!r}")
                shown += 1

    for _ in range(N_RANDOM):
        text, p = gen_case(rng)
        o, s = oracle(text, p), shadow(text, p)
        checked += 1
        if o != s:
            disagreements += 1
            if shown < 20:
                print(f"DISAGREE rand text={text!r} p={p} oracle={o!r} shadow={s!r}")
                shown += 1

    if disagreements:
        print(f"status=fail disagreements={disagreements}/{checked}")
        sys.exit(1)
    print(f"status=pass checked={checked} seed={SEED}")
    sys.exit(0)


if __name__ == "__main__":
    main()
