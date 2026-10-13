#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13964 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List KeyRef` ↔ a list of (stored, target) references, `PyVal`
              ↔ Python value shapes). The per-reference decision
              `resolvedKey stored target = if isEmpty stored then target else
              stored` and the fold `resolvedKeys` are R/I-tagged; the shadow is
              pure R/I (no A-consumed axiom — `isEmpty` is a deep model whose
              soundness vs `x in field.empty_values` is G-AX's concern, but here
              the shadow uses the SAME structural recognizer the spec freezes,
              so the leg under test is the fold's transliteration).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `Model._prepare_related_fields_for_save` applied at base_commit
              (the real correctness oracle, G-RESOLVE), driven per reference on
              a live FK relation and read back through the post-state attname.

They must agree on every Requires-satisfying input (the related object always
carries a key: `target is not None`). Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict. The decision
is DB-free (pure attribute manipulation), so conf_skip is FALSE.
"""
import random
import sys

SEED = 13964
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean isEmpty / resolvedKey / resolvedKeys -------

def shadow_is_empty(v):
    """isEmpty over the PyVal bijection (mapping.md §2)."""
    if v is None:
        return True
    if isinstance(v, str):
        return len(v) == 0
    if isinstance(v, (list, tuple, dict)):
        return len(v) == 0
    if isinstance(v, int) and not isinstance(v, bool):
        return False
    raise AssertionError("value %r outside the modeled PyVal shapes" % (v,))


def shadow_resolved_key(stored, target):
    """resolvedKey stored target = if isEmpty stored then target else stored."""
    return target if shadow_is_empty(stored) else stored


def shadow_resolved_keys(refs):
    """resolvedKeys: the per-reference resolution, element by element (the
    backward `while` fold of fillEmptyKeyRefs computes exactly this)."""
    return [shadow_resolved_key(stored, target) for (stored, target) in refs]


# --- the oracle: patch.diff behaviour on a live FK relation ------------------

def _build_oracle():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={'default': {
                'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        )
    django.setup()
    from django.db import models

    class P(models.Model):
        sku = models.CharField(primary_key=True, max_length=50)

        class Meta:
            app_label = 'conf13964'

    class O(models.Model):
        product = models.ForeignKey(P, on_delete=models.CASCADE)

        class Meta:
            app_label = 'conf13964'

    def oracle_resolve(stored, target):
        """patch.diff's behaviour for ONE reference: reconcile a cached relation
        whose related object carries key `target` and whose locally-stored key
        is `stored`; return the post-state stored key (product_id). The attname
        is poked into __dict__ to keep the relation cached (assigning through the
        descriptor would clear it — see axiom_check.py)."""
        o = O()
        p = P()
        p.sku = target
        o.product = p                          # cache the relation
        o.__dict__['product_id'] = stored      # override stored key, keep cache
        o._prepare_related_fields_for_save('save')
        return o.product_id

    return oracle_resolve


# --- value generation over the modeled PyVal shapes --------------------------

def gen_target(rng):
    """A related-object key: always present (precondition target != None). For
    a CharField primary key it is a non-empty string; we also exercise other
    non-empty key shapes the bijection covers."""
    kind = rng.randint(0, 1)
    if kind == 0:
        n = rng.randint(1, 6)
        return ''.join(rng.choice('abjeff09') for _ in range(n))
    return rng.randint(1, 9999)               # a numeric (non-empty) key


def gen_stored(rng):
    """A locally-stored key, spanning empty (None, '', empty collections) and
    non-empty shapes."""
    kind = rng.randint(0, 5)
    if kind == 0:
        return None
    if kind == 1:
        return ''                              # the issue's empty-string pk
    if kind == 2:
        n = rng.randint(0, 6)                  # str (empty or not)
        return ''.join(rng.choice('abjeff09') for _ in range(n))
    if kind == 3:
        return rng.randint(-9999, 9999)        # int (never empty)
    if kind == 4:
        n = rng.randint(0, 3)                  # collection (empty or not)
        return [0] * n
    return rng.choice([(), {}, (1,), {1: 2}])  # tuple/dict boundaries


def boundary_refs():
    """Boundary references (stored, target) — target always present."""
    cases = []
    for target in ['foo', 'jeff', 123]:
        for stored in [None, '', 'foo', 'jeff', 'existing', 0, 5,
                       [], (), {}, [1], (1,), {1: 2}]:
            cases.append((stored, target))
    return cases


def main():
    oracle_resolve = _build_oracle()
    rng = random.Random(SEED)

    disagreements = []
    count = 0

    def check(refs):
        nonlocal count
        # SHADOW: the fold over the whole reference list
        shadow = shadow_resolved_keys(refs)
        # ORACLE: the patched routine, per reference (each ref is an independent
        # field on its own object; the routine's loop is element-wise)
        oracle = [oracle_resolve(stored, target) for (stored, target) in refs]
        count += 1
        if shadow != oracle:
            disagreements.append((refs, shadow, oracle))

    # boundary cases first (plan §4.1 step 4)
    check(boundary_refs())
    for stored, target in boundary_refs():
        check([(stored, target)])
        if disagreements:
            break

    # randomized fuzz: each iteration is a fresh reference list
    while count < N_FUZZ and not disagreements:
        k = rng.randint(0, 5)
        refs = [(gen_stored(rng), gen_target(rng)) for _ in range(k)]
        check(refs)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for refs, sh, orc in disagreements[:5]:
            print("  refs=%r shadow=%r oracle=%r" % (refs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of fillEmptyKeyRefs agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
