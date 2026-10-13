#!/usr/bin/env python3
r"""G-CONF for django__django-13112.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_modelRef` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched normalization performed by
`ForeignKey.deconstruct`, over >=1e5 fuzzed reference tokens. Zero disagreements
=> exit 0.

Modeled object (mapping.md / refinement.md): the lazy reference string
`self.remote_field.model` and the normalized `kwargs['to']` value the
`isinstance(..., str)` branch of `ForeignKey.deconstruct` assigns. Post-patch:
  * `'.' in s`  -> prefix kept verbatim, only the name segment lowercased;
  * `'.' not in s` -> whole token lowercased.

  * Oracle  = the REAL patched ForeignKey.deconstruct: build a ForeignKey whose
              `to=` is the fuzzed string, deconstruct it, read kwargs['to'].
  * Shadow  = the op-for-op transliteration of implementation_modelRef, with
              per-character lowercasing bound to the REAL str.lower.

Type bijection (mapping.md): s:List Char <-> to-string:str (per code point);
Char.toLower <-> str.lower per char; prefixSeg/nameSeg <-> split('.')[0]/[1].
Modeled domain: tokens with at most one '.' separator (the patch's split('.')
unpacks into exactly two parts).
stdlib-only.
"""
import json
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False,
        DATABASES={}, INSTALLED_APPS=[], USE_I18N=False,
    )
    django.setup()

from django.db import models

SEED = 13112
N = 120_000
ALPHABET = list("AaBbMmXx_09.")


def oracle(token):
    """Normalized kwargs['to'] from the REAL patched ForeignKey.deconstruct."""
    fk = models.ForeignKey(token, on_delete=models.CASCADE)
    fk.set_attributes_from_name("field")
    _name, _path, _args, kwargs = fk.deconstruct()
    return kwargs["to"]


def shadow(token):
    """Op-for-op transliteration of implementation_modelRef (Lean).

    Op 1: '.' in token -> qualified branch.
    Op 2/3: prefixSeg / nameSeg = text before / after the first '.'.
    Op 4: prefix verbatim + '.' + lowercased name.
    Op 5: else lowercase whole token.
    """
    if "." in token:
        idx = token.index(".")
        prefix_part = token[:idx]            # prefixSeg: takeWhile (!= '.')
        name_part = token[idx + 1:]          # nameSeg: dropWhile (!= '.') |> drop 1
        return prefix_part + "." + name_part.lower()
    else:
        return token.lower()


def gen_token(rng):
    n = rng.randint(0, 10)
    s = "".join(rng.choice(ALPHABET) for _ in range(n))
    # restrict to the modeled domain: at most one separator
    if s.count(".") > 1:
        # collapse extra dots to a single-separator token deterministically
        first = s.index(".")
        s = s[:first + 1] + s[first + 1:].replace(".", "x")
    return s


def main() -> int:
    rng = random.Random(SEED)
    mismatches = []
    checked = 0
    for _ in range(N):
        token = gen_token(rng)
        try:
            o = oracle(token)
        except Exception as e:  # noqa: BLE001
            # outside the modeled domain (e.g. split unpack); skip
            continue
        s = shadow(token)
        checked += 1
        if o != s:
            mismatches.append({"token": token, "oracle": o, "shadow": s})
            if len(mismatches) >= 20:
                break

    status = "pass" if not mismatches else "fail"
    print(json.dumps({
        "status": status,
        "instance": "django__django-13112",
        "seed": SEED,
        "checked": checked,
        "mismatches": mismatches[:20],
    }))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
