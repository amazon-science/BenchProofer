#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-11333 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. The one
op in Solution.lean's impl region is pure R/I (no A-tagged callee).

The modeled observable is OBJECT IDENTITY, refined to KEY EQUALITY (mapping.md
§2): two requests are served the very same shared object iff their resolved
storage keys are equal. So:

  * SHADOW  — `sharedHandle` transliterated to Python over the real repo types
              (mapping.md bijection: `Option String` <-> `urlconf` arg, where
              Lean `none` <-> Python `None` and `some s` <-> the str `s`;
              `ambient` <-> `settings.ROOT_URLCONF`):
                  shadow_key(requested, ambient)
                      = ambient            if requested is None
                      = requested          otherwise
              i.e. the resolved key the patched lookup memoizes on.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.urls.resolvers.get_resolver`. Its observable identity is
              `id(get_resolver(requested))` — the lru_cache shares one object
              per resolved key.

Equivalence checked on every fuzzed input PAIR (r1, r2):

      (shadow_key(r1) == shadow_key(r2))  ==  (id(oracle(r1)) == id(oracle(r2)))

Both directions matter: equal keys must coalesce to one object (the fix); and
distinct keys must stay distinct objects (no over-coalescing). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

No URLconf module is ever imported: `URLResolver.__init__` only STORES the
dotted name (it imports lazily in `_populate`, which we never trigger), so
arbitrary urlconf strings are safe fuzz inputs. stdlib + django only. The fuzz
seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 11333
N_FUZZ = 100_000

ROOT = "conf_check.root_urlconf"   # the value installed as settings.ROOT_URLCONF


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            ROOT_URLCONF=ROOT,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


# --- the R/I shadow: sharedHandle / lookupKey, transliterated ----------------
def shadow_key(requested, ambient):
    """lookupKey: resolve an omitted identifier to the ambient default BEFORE
    taking the storage key (the patched behaviour)."""
    if requested is None:
        return ambient
    return requested


def fuzz_requests(n, rng, ambient):
    """A stream of `urlconf`-style requests: None (omitted) or a dotted string.
    Biased toward the discriminating cases — None vs an explicit mention of the
    ambient default — which is exactly what the F2P test exercises."""
    # boundary cases first (plan §4.1 step 4)
    yield None
    yield ambient                      # explicit mention of the default
    yield ambient                      # again: must coalesce with the above
    yield "other.urlconf"
    yield "other.urlconf"              # again: must coalesce with itself
    yield ""                           # empty string is a distinct key from None
    pool = [None, ambient, "other.urlconf", "a.b", "a.c", "", "x"]
    for _ in range(n):
        # mostly draw from the small pool (to force many identity collisions),
        # occasionally a fresh random dotted name
        if rng.random() < 0.85:
            yield rng.choice(pool)
        else:
            k = rng.randint(0, 4)
            yield ".".join(rng.choice("abcdefghij") for _ in range(k + 1))


def main():
    _bootstrap_django()
    from django.conf import settings
    from django.urls.resolvers import get_resolver

    ambient = settings.ROOT_URLCONF
    rng = random.Random(SEED)

    requests = list(fuzz_requests(N_FUZZ, rng, ambient))

    # Map each shadow key -> the set of oracle object ids seen for it, and each
    # oracle id -> the set of shadow keys seen for it. A sound R refinement
    # gives a bijection: one key <-> one object id.
    key_to_ids = {}
    id_to_keys = {}
    disagreements = []
    for req in requests:
        k = shadow_key(req, ambient)
        obj_id = id(get_resolver(req))      # real patched callee
        key_to_ids.setdefault(k, set()).add(obj_id)
        id_to_keys.setdefault(obj_id, set()).add(k)

    # direction 1: equal keys must map to exactly one object (the coalescing fix)
    for k, ids in key_to_ids.items():
        if len(ids) != 1:
            disagreements.append(
                ("one key -> many objects", k, sorted(ids)))
            if len(disagreements) >= 5:
                break
    # direction 2: distinct keys must map to distinct objects (no over-merge)
    for obj_id, keys in id_to_keys.items():
        if len(keys) != 1:
            disagreements.append(
                ("one object -> many keys", obj_id, sorted(map(repr, keys))))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d requests:"
              % (len(disagreements), len(requests)))
        for kind, a, b in disagreements:
            print("  [%s] %r <-> %r" % (kind, a, b))
        return 1

    print("G-CONF OK: object-identity <-> key-equality R refinement of "
          "sharedHandle agrees with patch.diff behaviour on %d requests "
          "(%d distinct keys, seed=%d), 0 disagreements."
          % (len(requests), len(key_to_ids), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
