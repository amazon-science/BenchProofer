#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16255 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The bundle has no @Pure helpers
and no @ContractOnly callees, so the shadow is the single loop body.

ORACLE: the REAL patched repo function the model models per mapping.md —
``django.contrib.sitemaps.Sitemap.get_latest_lastmod`` on the branch where the
per-entry stamp attribute is a callable. The gate applies patch.diff to
/testbed before this script runs, so the imported class carries the patched
body. The oracle drives the real method through a minimal section subclass
whose ``items()`` enumerates the generated entries and whose ``lastmod``
callable maps each entry to its stamp, exactly the shape the model's input
``stamps`` abstracts (mapping.md section 1: the input list IS the per-entry
stamp collection).

Type bridge (mapping.md section 2): the repo's stamps are date/datetime values
under their total order; the model carrier is ``List[int]``. Every input list
is exercised through the oracle TWICE:
  (a) directly as ints (Python ints are totally ordered, so they are a valid
      stamp type for the real method's reduction), and
  (b) lifted through the order-preserving bijection int k -> epoch + k seconds
      into real ``datetime`` stamps, with the result mapped back — validating
      that the documented carrier abstraction is faithful on the real callee.

Input domain: the precondition demands only a readable list of ints, so every
generated list is Requires-satisfying. Boundary cases stress the empty section
(the behavioural delta), singletons, duplicates, negatives, and sorted/reversed
runs; fuzzing covers lengths 0..16 (length 0 re-fuzzes the empty section).

>= 1e5 Requires-satisfying inputs: boundary + 100000 fuzz. Pinned seed: 16255.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys

SEED = 16255
N_FUZZ = 100000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def latest_stamp(stamps):
    result = None  # type: Optional[int]
    i = 0
    while i < len(stamps):
        v = stamps[i]
        if result is None or v > result:
            result = v
        i = i + 1
    return result


# --- oracle: the real patched section class ----------------------------------

from django.contrib.sitemaps import Sitemap  # noqa: E402  (real /testbed code)

_EPOCH = datetime.datetime(2001, 1, 1)


class _Section(Sitemap):
    """Minimal concrete section: enumerates preset entries; the per-entry
    stamp callable maps an entry to its stamp via a preset function."""

    def __init__(self, entries, stamp_of):
        self._entries = list(entries)
        self._stamp_of = stamp_of

    def items(self):
        return self._entries

    def lastmod(self, item):
        return self._stamp_of(item)


def _to_dt(k):
    """Order-preserving bijection int -> datetime (k seconds from a fixed
    epoch; negative k maps before the epoch, so order is preserved exactly)."""
    return _EPOCH + datetime.timedelta(seconds=k)


def _from_dt(d):
    if d is None:
        return None
    return int((d - _EPOCH).total_seconds())


def real_latest_int(stamps):
    """Real patched method over int stamps (identity stamp callable)."""
    return _Section(stamps, lambda item: item).get_latest_lastmod()


def real_latest_dt(stamps):
    """Real patched method over datetime stamps (the repo's actual stamp
    type), lifted through the order-preserving bijection and mapped back."""
    return _from_dt(_Section(stamps, _to_dt).get_latest_lastmod())


# --- differential driver ------------------------------------------------------

def check(stamps):
    """Run shadow and oracle (both carriers) on one stamp list; return an
    error string on disagreement, else None."""
    shadow = latest_stamp(stamps)
    try:
        real_i = real_latest_int(stamps)
    except Exception as e:  # the shadow never raises; a raise is a divergence
        return ("DISAGREEMENT on stamps %r:\n  shadow (impl region) = %r\n"
                "  real (int carrier) raised %r" % (stamps, shadow, e))
    if shadow != real_i:
        return ("DISAGREEMENT on stamps %r:\n  shadow (impl region) = %r\n"
                "  real (int carrier) = %r" % (stamps, shadow, real_i))
    try:
        real_d = real_latest_dt(stamps)
    except Exception as e:
        return ("DISAGREEMENT on stamps %r:\n  shadow (impl region) = %r\n"
                "  real (datetime carrier) raised %r" % (stamps, shadow, e))
    if shadow != real_d:
        return ("DISAGREEMENT on stamps %r:\n  shadow (impl region) = %r\n"
                "  real (datetime carrier, mapped back) = %r"
                % (stamps, shadow, real_d))
    return None


def boundary_cases():
    return [
        [],                        # the empty section: the behavioural delta
        [0],
        [5],
        [-1],
        [0, 0],
        [1, 2, 3],
        [3, 2, 1],
        [2, 2, 2],
        [-5, -3, -10],
        [10, -10, 0],
        [-1, -1, -2],
        [1000000000, 999999999],
        [999999999, 1000000000],
        list(range(50)),
        list(range(50, 0, -1)),
        [7] * 20,
        [-1000, 1000, -1000, 1000],
    ]


def main():
    checked = 0
    boundary = boundary_cases()
    for v in boundary:
        err = check(v)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 16)           # n == 0 re-fuzzes the empty section
        v = [rng.randint(-100000, 100000) for _ in range(n)]
        err = check(v)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched get_latest_lastmod on "
          "%d inputs (%d boundary + %d fuzz, seed %d; int + datetime "
          "carriers); 0 disagreements." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
