#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10914 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (this bundle's impl has none — no Requires/Ensures live inside
the impl region) and the @Pure helper `default_mode` copied over as a plain
function. There are no @ContractOnly callees and no PSeq usage in this bundle;
the carrier is a plain Optional[int] scalar, so no shim is needed.

ORACLE: the REAL patched repo resolution the model models per mapping.md —
`django.core.files.storage.FileSystemStorage.file_permissions_mode`, the
property that resolves a per-store override against the project-wide default
setting via `_value_or_setting`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable. A fresh FileSystemStorage is constructed per input (the property
is cached per instance) with the candidate override passed as the
`file_permissions_mode` constructor argument, mirroring the per-store
override the model's `override` parameter abstracts.

Type bridge (mapping.md section 2): identity. The model carrier Optional[int]
maps None <-> an unconfigured mode and int <-> the numeric mode verbatim, and
the property returns exactly such an Optional[int], so shadow and oracle
outputs compare with `==` (plus a None/not-None kind check so None never
compares equal to a falsy int by accident — it cannot with `==` on
int/None, but the kind check keeps the comparison explicit).

Input domain: the model's preconditions place no constraint on `override`
beyond its Optional[int] type, so every int and None is Requires-satisfying.
Boundary cases cover None, 0, the common octal permission modes, negatives,
and large magnitudes; fuzz draws mixed-magnitude ints plus None at ~1/8
frequency.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz values.
Pinned fuzz seed: 10914.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 10914
N_FUZZ = 100_000


# --- pure helper from model.py, decorator stripped -----------------------------

def default_mode():
    return 420  # 0o644


# --- the impl region of model.py, verbatim -------------------------------------

def resolve_storage_mode(override):
    # The project-wide default mode handed back when nothing is configured.
    default = 420  # type: Optional[int]   # 0o644
    # Resolution: an absent override falls back to the project-wide default;
    # otherwise the override is used verbatim.
    if override is None:
        return default
    return override


# --- oracle + differential ------------------------------------------------------

def check_case(make_storage, override):
    """Run shadow and oracle on one Optional[int] override; return an error
    string on disagreement, else None."""
    shadow_out = resolve_storage_mode(override)
    real_out = make_storage(override).file_permissions_mode
    same_kind = (shadow_out is None) == (real_out is None)
    if not same_kind or shadow_out != real_out:
        return ("DISAGREEMENT\n  override=%r\n  shadow=%r\n  real=%r"
                % (override, shadow_out, real_out))
    return None


def boundary_cases():
    return [
        None,
        0, 1, -1,
        0o644, 0o600, 0o640, 0o664, 0o666, 0o755, 0o777, 0o444, 0o000,
        420, 511, 384,
        7, 8, 63, 64, 4095, 4096,          # around octal digit boundaries
        2 ** 15, 2 ** 16, 2 ** 31 - 1, 2 ** 31, 2 ** 63,
        -420, -(2 ** 31),
    ]


def rand_override(rng):
    if rng.random() < 0.125:
        return None
    kind = rng.random()
    if kind < 0.5:
        return rng.randint(0, 0o777)       # plausible permission modes
    if kind < 0.8:
        return rng.randint(-4096, 4096)    # small mixed-sign ints
    return rng.randint(-2 ** 40, 2 ** 40)  # large magnitudes


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched callee: the storage class whose property resolves the
    # per-store override against the project-wide default setting.
    from django.core.files.storage import FileSystemStorage

    def make_storage(override):
        # Fresh instance per input: the resolution is cached per instance,
        # and the override is a per-store constructor argument.
        return FileSystemStorage(location="/tmp",
                                 file_permissions_mode=override)

    checked = 0
    for override in boundary_cases():
        err = check_case(make_storage, override)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(make_storage, rand_override(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real storage-mode resolution on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
