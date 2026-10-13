#!/usr/bin/env python3
"""G-CONF for django__django-16255.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_latestLastmod` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`Sitemap.get_latest_lastmod`, over >=1e5 fuzzed inputs. Zero disagreements => 0.

Model (refinement.md): `get_latest_lastmod` reports the latest timestamp. Outcome
modeled as Option (Option Int):
  * outer none  <-> the method raised (the ValueError from max([]));
  * outer some v <-> it returned, v: Option Int the optional timestamp
                     (none <-> Python None, some d <-> a date).

  * Oracle = the REAL patched Sitemap.get_latest_lastmod, on a live sitemap whose
            hasattr(lastmod)/callable(lastmod)/items()/lastmod-value are set per
            the fuzzed config. Call it; catch to detect a raise; else read value.
  * Shadow = some(none)            if not hasM
             some(max?(vals))      if hasM and callM   (max? : none for [], else max)
             some(fixedM)          if hasM and not callM

Type bijection (mapping.md): hasM<->hasattr(self,"lastmod"),
callM<->callable(self.lastmod), vals<->[self.lastmod(item) for item in items()]
(date<->int ordinal), fixedM<->self.lastmod when not callable (None<->none),
result<->Option(Option Int) outcome. stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django.contrib.sitemaps import Sitemap

SENTINEL = object()


def make_sitemap(has_m, call_m, vals, fixed_m):
    """A live Sitemap whose get_latest_lastmod config matches the fuzzed tuple.

    has_m   : whether the instance has a `lastmod` attribute at all.
    call_m  : whether `lastmod` is callable (per-item) vs a fixed value.
    vals    : the per-item timestamps (used only when call_m); items() returns a
              range of placeholder items, lastmod(item) maps item->its ordinal.
    fixed_m : the fixed `lastmod` value (used only when not call_m); None or int.
    """
    sm = Sitemap()
    # Base Sitemap has no `lastmod`; only attach one when has_m is True.
    if has_m:
        if call_m:
            # items() yields indices; lastmod(i) returns vals[i]. The real method
            # computes [self.lastmod(item) for item in self.items()] == vals.
            sm.items = lambda vals=vals: list(range(len(vals)))
            sm.lastmod = lambda i, vals=vals: vals[i]
        else:
            # A fixed (non-callable) lastmod value.
            sm.lastmod = fixed_m
    else:
        # Ensure no inherited callable named lastmod exists.
        assert not hasattr(sm, "lastmod")
    return sm


def oracle(sm):
    """Outer none <-> raised; outer (True, v) <-> returned v."""
    try:
        v = sm.get_latest_lastmod()
    except Exception:
        return ("raise",)
    return ("ret", v)


def shadow(has_m, call_m, vals, fixed_m):
    if not has_m:
        return ("ret", None)
    if call_m:
        return ("ret", (max(vals) if vals else None))
    return ("ret", fixed_m)


def main() -> int:
    rng = random.Random(16255)
    N = 100_000
    mism = 0
    for k in range(N):
        has_m = rng.random() < 0.85
        call_m = rng.random() < 0.6
        # vals: empty (the crash boundary) ~25% of the time, else a small list.
        if rng.random() < 0.25:
            vals = []
        else:
            vals = [rng.randint(-5, 30) for _ in range(rng.randint(1, 6))]
        fixed_m = None if rng.random() < 0.3 else rng.randint(-5, 30)

        sm = make_sitemap(has_m, call_m, vals, fixed_m)
        o = oracle(sm)
        s = shadow(has_m, call_m, vals, fixed_m)
        if o != s:
            mism += 1
            if mism <= 10:
                print(f"MISMATCH cfg=(has_m={has_m},call_m={call_m},"
                      f"vals={vals},fixed_m={fixed_m}) oracle={o} shadow={s}")
    if mism:
        print(f"G-CONF FAIL: {mism}/{N} disagreements")
        return 1
    print(f"G-CONF OK: {N} inputs, 0 disagreements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
