#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13401 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions
              (`fieldEq`, and `fieldLtSpec`/`ownerLt` for `fieldLt`)
              transliterated to Python over real `Field` records, via the
              mapping.md bijection (`owner : Option (String×String)` ↔ model
              identity, `hasattr(...,'model')` ↔ `owner.isSome`, tuple `<` ↔
              `ownerLt`). `fieldHash`'s digest leg is A-tagged (opaque `pyHash`)
              and is out of scope here (it stays with G-AX); but the
              equal/unequal RELATION of the real `hash` is pure-R observable, so
              we additionally diff `hash` equality against key equality.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Field.__eq__` /
              `Field.__lt__` / `Field.__hash__` applied at base_commit (the real
              correctness oracle, G-RESOLVE), on the corresponding real Field
              records.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django importable,
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 13401
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    django.setup()


# --- the Lean↔Python bridge (mapping.md §2) ----------------------------------

class _Meta:
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name


class _FakeModel:
    def __init__(self, app_label, model_name):
        self._meta = _Meta(app_label, model_name)
    def __eq__(self, other):
        return (isinstance(other, _FakeModel)
                and self._meta.app_label == other._meta.app_label
                and self._meta.model_name == other._meta.model_name)
    def __hash__(self):
        return hash((self._meta.app_label, self._meta.model_name))


_MODEL_CACHE = {}


def _model_for(owner):
    if owner is None:
        return None
    if owner not in _MODEL_CACHE:
        _MODEL_CACHE[owner] = _FakeModel(owner[0], owner[1])
    return _MODEL_CACHE[owner]


def _build_field(Field, counter, owner):
    f = Field()
    f.creation_counter = counter
    if owner is not None:
        f.model = _model_for(owner)
    return f


# --- the R/I shadow: Solution.lean fieldEq / fieldLtSpec, transliterated ------

def shadow_eq(a, b):
    """fieldEq (a b): counters agree AND owners agree (mapping.md §2)."""
    ca, oa = a
    cb, ob = b
    return (ca == cb) and (oa == ob)


def _owner_lt(p, q):
    """ownerLt: lexicographic on (app_label, model_name)."""
    return p[0] < q[0] or (p[0] == q[0] and p[1] < q[1])


def shadow_lt(a, b):
    """fieldLtSpec a b, transliterated."""
    ca, oa = a
    cb, ob = b
    if ca != cb or (oa is None and ob is None):
        return ca < cb
    else:
        if (oa is not None) != (ob is not None):
            return oa is None      # no-owner record first
        else:
            # both attached, equal counters
            return _owner_lt(oa, ob)


# --- the oracle: patch.diff behaviour on real Field instances ----------------

def oracle_eq(Field, a, b):
    return bool(_build_field(Field, *a) == _build_field(Field, *b))


def oracle_lt(Field, a, b):
    return bool(_build_field(Field, *a) < _build_field(Field, *b))


def oracle_hash_eq(Field, a, b):
    return hash(_build_field(Field, *a)) == hash(_build_field(Field, *b))


# --- inputs ------------------------------------------------------------------

def fuzz_records(n, rng):
    labels = ["model_fields", "app", "other", "auth", "x", "abc", "m_1"]
    names = ["abstractmodel", "inheritabstractmodel1", "inheritabstractmodel2",
             "a", "b", "field", "z9", "m"]
    counters = [0, 1, 2, 7, 12]
    # boundary records first
    boundary = []
    for c in counters:
        boundary.append((c, None))
        boundary.append((c, ("model_fields", "abstractmodel")))
        boundary.append((c, ("model_fields", "inheritabstractmodel1")))
        boundary.append((c, ("model_fields", "inheritabstractmodel2")))
    for r in boundary:
        yield r
    for _ in range(n):
        c = rng.randint(0, 12)        # small range so counter ties are frequent
        if rng.random() < 0.3:
            o = None
        else:
            o = (rng.choice(labels), rng.choice(names))
        yield (c, o)


def main():
    _setup_django()
    from django.db.models.fields import Field

    rng = random.Random(SEED)
    records = list(fuzz_records(N_FUZZ, rng))

    disagreements = []
    count = 0
    # Pair consecutive records (and each with the next) so equal-counter,
    # different-owner pairs — the discriminating case — occur frequently.
    for i in range(len(records)):
        a = records[i]
        b = records[(i * 2654435761 + 1) % len(records)]
        count += 1

        se, oe = shadow_eq(a, b), oracle_eq(Field, a, b)
        if se != oe:
            disagreements.append(("eq", a, b, se, oe))

        sl, ol = shadow_lt(a, b), oracle_lt(Field, a, b)
        if sl != ol:
            disagreements.append(("lt", a, b, sl, ol))

        # pure-R observable: hash-equality relation matches key equality
        key_eq = (a == b)
        if key_eq:
            if not oracle_hash_eq(Field, a, b):
                disagreements.append(("hasheq", a, b, True, False))

        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d input pairs:"
              % (len(disagreements), count))
        for kind, a, b, sh, orc in disagreements:
            print("  [%s] a=%r b=%r shadow=%r oracle=%r" % (kind, a, b, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of fieldEq/fieldLt agrees with patch.diff "
          "behaviour on %d input pairs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
