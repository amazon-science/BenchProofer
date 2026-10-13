#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15741 (nagini).

SHADOW: the impl region of `lookup_format` from model.py, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The model IS Python; the `List[int]` carrier is a plain Python list here, so
no PSeq shim is needed (the impl region uses only lists). `FormatType` copies
over as a plain attribute holder. The single @ContractOnly callee,
`do_lookup`, calls the REAL repo function: it models the unchanged downstream
localisation lookup keyed on a fully-resolved name (mapping.md section 3.2),
which is exactly `django.utils.formats.get_format` applied to a real `str`
(the placeholder-to-text coercion is the identity on an already-resolved
name, so on that domain the whole function IS its unchanged downstream part).

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.utils.formats.get_format(format_type)` — called on the name in the
form the input specifies: an already-resolved `str` (deferred == False) or a
lazy string proxy built with the repo's own `django.utils.functional.lazy`
(deferred == True). The gate applies patch.diff to /testbed before this
script runs (PYTHONPATH=/testbed); this script never applies any diff itself.

TYPE BRIDGE (mapping.md section 2, all R-refinements):
  FormatType(deferred, content) <-> the format_type argument: content is the
      list of Unicode code points of the string the argument denotes;
      deferred == False <-> a real str, deferred == True <-> a lazy proxy
      whose resolution yields that same string.
  List[int] result <-> the value get_format returns, under an injective
      encoding (code points for a str value; a tagged canonical serialisation
      for the list/tuple values of the *_INPUT_FORMATS names). The observable
      is value equality, exactly what the downstream users compare.

Requires-satisfying inputs: the model's preconditions are permissions only
(read access to the name), which every concrete FormatType satisfies; the
domain is (deferred flag) x (name string). Inputs: structured boundary names
(known localisation names in both forms, incl. lazy-translation-shaped
proxies, empty and unicode names, names that are not known formats) plus
50,000 fuzzed names, each exercised in BOTH forms => > 1e5 inputs total.
Pinned fuzz seed: 15741002 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 15741002
N_FUZZ_NAMES = 50_000


# --- @ContractOnly callee bridge: calls the REAL repo function ---------------
#
# do_lookup models the unchanged downstream lookup as "given a fully-resolved
# name, return the value for that name" (read-only in the name). On a real
# str the coercion at the top of the real function is the identity, so
# calling the real get_format on the decoded str IS that downstream lookup.

_real_get_format = None  # bound in main() after Django settings are ready


def _encode_value(value):
    """Injective List[int] encoding of a returned format value (the model's
    result carrier). str values map to their code points; other values (the
    list/tuple *_INPUT_FORMATS values) map to a tagged canonical form."""
    if isinstance(value, str):
        return [ord(ch) for ch in value]
    return [-1] + [ord(ch) for ch in repr(value)]


def do_lookup(name):
    resolved = "".join(chr(c) for c in name)
    return _encode_value(_real_get_format(resolved))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class FormatType:
    def __init__(self, deferred, content):
        self.deferred = deferred
        self.content = content


def lookup_format(requested_name):
    # Resolve the requested name to its character sequence FIRST, then look it
    # up — so the downstream lookup never sees the deferred form.
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        name.append(requested_name.content[i])
        i = i + 1
    result = do_lookup(name)
    return result

# --- end of impl region -------------------------------------------------------


def shadow_outcome(deferred, s):
    """Bridge one real input (form flag + name string) to the model's input,
    run the shadow, and return its observable outcome."""
    ft = FormatType(deferred, [ord(ch) for ch in s])
    try:
        return ("normal", lookup_format(ft))
    except Exception as exc:  # the shadow has no exceptional path
        return ("unexpected-shadow-exception: %r" % (exc,), None)


def real_outcome(get_format, make_deferred, deferred, s):
    """Run the REAL repo function on the name in the requested form and
    return its observable outcome under the same value encoding."""
    arg = make_deferred(s) if deferred else s
    try:
        value = get_format(arg)
    except Exception as exc:  # any exception disagrees with the shadow
        return ("unexpected-exception: %r" % (exc,), None)
    return ("normal", _encode_value(value))


def check_one(get_format, make_deferred, deferred, s):
    shadow = shadow_outcome(deferred, s)
    real = real_outcome(get_format, make_deferred, deferred, s)
    if shadow != real:
        return ("DISAGREEMENT\n  input name=%r deferred=%r\n  shadow=%r\n"
                "  real=%r" % (s, deferred, shadow, real))
    return None


# Structured boundary names: known localisation names (str values and the
# list-valued input-format names), plus adversarial strings.
BOUNDARY_NAMES = [
    "DATE_FORMAT",
    "TIME_FORMAT",
    "DATETIME_FORMAT",
    "SHORT_DATE_FORMAT",
    "SHORT_DATETIME_FORMAT",
    "YEAR_MONTH_FORMAT",
    "MONTH_DAY_FORMAT",
    "DECIMAL_SEPARATOR",
    "THOUSAND_SEPARATOR",
    "NUMBER_GROUPING",
    "FIRST_DAY_OF_WEEK",
    "DATE_INPUT_FORMATS",
    "TIME_INPUT_FORMATS",
    "DATETIME_INPUT_FORMATS",
    "H:i",
    "Y-m-d",
    "N j, Y",
    "",                        # boundary: empty name
    "NOT_A_REAL_FORMAT_NAME",  # unknown name: value is the name itself
    "héllo",                   # unicode
    "a b c",
]

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdef:,- éç•0123456789"


def main():
    global _real_get_format

    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            USE_I18N=True,
            USE_L10N=True,
            USE_TZ=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
        django.setup()

    # REAL repo symbols (the function the model models, per mapping.md, and
    # the repo's own deferred-string constructors):
    from django.utils.formats import get_format, reset_format_cache
    from django.utils.functional import lazy
    from django.utils.translation import gettext_lazy

    _real_get_format = get_format
    # The deferred form: a lazy str proxy resolving to the name unchanged
    # (the shape of every deferred string the function can receive).
    make_deferred = lazy(lambda s: s, str)

    checked = 0
    n_boundary = 0
    for s in BOUNDARY_NAMES:
        for deferred in (False, True):
            err = check_one(get_format, make_deferred, deferred, s)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
        # Also exercise the translation-shaped deferred form on each
        # boundary name (a second constructor for the same deferred case).
        reset_format_cache()
        err = check_one(get_format, gettext_lazy, True, s)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for k in range(N_FUZZ_NAMES):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(ALPHABET) for _ in range(n))
        for deferred in (False, True):
            err = check_one(get_format, make_deferred, deferred, s)
            if err:
                print(err)
                return 1
            checked += 1
        if k % 10_000 == 9_999:
            reset_format_cache()  # bound the cache; re-exercise cold paths

    print("G-CONF OK: shadow impl == real lookup on %d inputs "
          "(%d boundary + %d fuzz names x 2 forms, seed %d)."
          % (checked, n_boundary, N_FUZZ_NAMES, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly do_lookup -> real callee)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
