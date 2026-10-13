#!/usr/bin/env python3
"""G-CONF for django__django-15741.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_localizedFormat` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`django.utils.formats.get_format`, over >=1e5 fuzzed inputs.

Shadow (Lean impl):  realizeName(name) then the unchanged downstream resolution
  -> `get_format(str(format_type), lang)` (pre-coerce the name to a concrete str,
     then defer to the unchanged resolution = the real callee on a concrete name).
Oracle (real patched function): `get_format(format_type, lang)` on the RAW name
  (possibly a lazy proxy).

Type bijection (mapping.md): name<->format_type (str OR lazy proxy),
realizeName<->str(format_type), lang<->lang (str), result<->return value.

Each fuzzed name is presented BOTH as a plain `str` and as a lazy proxy (so the
`deferred` shape is exercised — the shape that raised TypeError pre-patch).
use_l10n=False routes through the settings / FORMAT_SETTINGS fallback, i.e. the
`getattr(settings, format_type)` and `return format_type` paths that the lazy
proxy broke. stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=False,
        DATABASES={},
        INSTALLED_APPS=[],
        # a couple of format settings so the FORMAT_SETTINGS branch returns a
        # concrete value rather than the name itself
        DATE_FORMAT="N j, Y",
        TIME_FORMAT="P",
    )
    django.setup()

from django.utils.formats import get_format
from django.utils.functional import lazy

# A lazy string proxy: defers str() materialization, exactly like gettext_lazy.
_lazystr = lazy(lambda s: s, str)


def oracle(format_type, lang):
    """Behavior of the patched repo function on the raw (possibly lazy) name."""
    return get_format(format_type, lang, use_l10n=False)


def shadow(format_type, lang):
    """R/I transliteration of implementation_localizedFormat (Lean):
    realize the name to a concrete str, then the unchanged downstream
    resolution."""
    key = str(format_type)  # realizeName
    return get_format(key, lang, use_l10n=False)  # lookupFormat (unchanged callee)


# format names: some in FORMAT_SETTINGS (resolve via getattr(settings,...)),
# some absent (return the name itself), plus random noise.
NAME_POOL = [
    "DATE_FORMAT", "TIME_FORMAT", "DATETIME_FORMAT", "YEAR_MONTH_FORMAT",
    "DECIMAL_SEPARATOR", "THOUSAND_SEPARATOR", "NUMBER_GROUPING",
    "NOT_A_FORMAT", "custom_key", "X", "",
]
LANG_POOL = ["en", "de", "fr", "en-us", None]


def rand_name(rng):
    n = rng.randint(0, 8)
    alpha = "ABCDEF_abc0123"
    return "".join(rng.choice(alpha) for _ in range(n))


def main():
    rng = random.Random(15741)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        base = rng.choice(NAME_POOL) if rng.random() < 0.7 else rand_name(rng)
        lang = rng.choice(LANG_POOL)
        # present the name BOTH as a plain str and as a lazy proxy
        format_type = base if (i % 2 == 0) else _lazystr(base)
        try:
            o = oracle(format_type, lang)
        except Exception as e:
            o = ("EXC", type(e).__name__)
        try:
            s = shadow(format_type, lang)
        except Exception as e:
            s = ("EXC", type(e).__name__)
        if o != s:
            disagreements += 1
            if first is None:
                first = (repr(format_type), lang, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
