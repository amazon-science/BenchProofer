#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-15315 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled digest `pyHash (fieldHashKey intrinsicId)`
              transliterated to Python over the mapping.md §2 bijection:
                  pyHash         <->  the builtin `hash`
                  intrinsicId    <->  field.creation_counter (assignment-indep.)
                  HashKey.solo i <->  the bare key `i` handed to `hash`
              i.e. `shadow_hash(field) == hash(field.creation_counter)`. There
              are NO A-tagged ops (no consumed axioms; `pyHash` is a free input),
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.db.models.fields.Field.__hash__`, i.e. `hash(field)`.

Two observables are differential-tested:

  (1) shadow == oracle      (the R/I transliteration is faithful), checked over
      the FULL fuzz population (>=10^5 standalone fields), AND
  (2) oracle is UNCHANGED across the model-association event (the immutability
      the modeled postcondition `∀ a, out = pyHash (fieldKeyAt intrinsicId a)`
      pins) — exactly what the F2P `test_hash_immutability` asserts — checked
      both standalone and AFTER the field is associated with a fresh model class.

PERFORMANCE NOTE (why the two observables are checked on different population
sizes): observable (1) is microseconds per field. Observable (2) must MUTATE
the field's lifecycle by building a real Django model class
(`type(name, (models.Model,), {...})`), which registers the model in Django's
app registry — orders of magnitude more expensive and super-linear as the
registry grows. Folding (2) into a 10^5 loop is what times the gate out (the
earlier revision timed out at 1800s). So observable (1) runs over the full
>=10^5 population (the SPEC_GUIDE >=10^5 R/I requirement), and observable (2) —
the genuinely expensive model-association/immutability scenario — runs over a
bounded sample of `N_ASSOC` fields. The cap is LOGGED, not silent: the final
line reports exactly how many association/immutability scenarios ran.

No database is touched: only `__hash__`, `creation_counter`, and `_meta`
attributes are read. stdlib + django only. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 15315
N_FUZZ = 100_000     # R/I fidelity leg (cheap: standalone hash == hash(counter))
N_ASSOC = 1_000      # immutability/association leg (expensive: builds a model)


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


# --- the R/I shadow: Solution.lean fieldHashMethod, transliterated ----------
def shadow_hash(field):
    """`pyHash (fieldHashKey intrinsicId)` with pyHash = builtin hash,
    intrinsicId = field.creation_counter, fieldHashKey = solo (intrinsic only)."""
    return hash(field.creation_counter)


# --- the oracle: the REAL gold-patched Field.__hash__ -----------------------
def oracle_hash(field):
    return hash(field)


def main():
    _bootstrap_django()
    from django.db import models

    rng = random.Random(SEED)

    # A pool of field factories spanning several concrete Field subclasses, so
    # the differential test is not specific to one type. Each call creates a
    # fresh field with a fresh creation_counter.
    def make_field():
        kind = rng.randint(0, 4)
        if kind == 0:
            return models.IntegerField()
        if kind == 1:
            return models.CharField(max_length=rng.randint(1, 255))
        if kind == 2:
            return models.BooleanField()
        if kind == 3:
            return models.TextField()
        return models.FloatField()

    disagreements = []
    ri_checks = 0       # observable (1) count
    assoc_checks = 0    # observable (2) count
    model_idx = 0

    def check_ri(field, label):
        """Observable (1): standalone shadow == oracle (pure R/I, cheap)."""
        nonlocal ri_checks
        ri_checks += 1
        s0 = shadow_hash(field)
        o0 = oracle_hash(field)
        if s0 != o0:
            disagreements.append(("%s standalone shadow!=oracle" % label, s0, o0))

    def check_assoc(field, label):
        """Observable (2): build a model class around `field`, then verify the
        oracle digest is faithful AND unchanged across the association event
        (the immutability the F2P test observes). EXPENSIVE — bounded run."""
        nonlocal assoc_checks, model_idx
        # standalone first, so we can compare across the association event.
        s0 = shadow_hash(field)
        o0 = oracle_hash(field)
        if s0 != o0:
            disagreements.append(("%s pre-assoc shadow!=oracle" % label, s0, o0))
            return
        model_idx += 1
        # A distinct app_label/model_name per model so the PRE-patch __hash__
        # (which folded those in) would have produced a DIFFERENT digest here —
        # the very mutation the fix removes.
        attrs = {
            "__module__": "conf_check_models",
            "Meta": type("Meta", (), {"app_label": "auth"}),
            "f_%d" % model_idx: field,
        }
        type("ConfModel_%d" % model_idx, (models.Model,), attrs)
        # Sanity: the field really did become associated with a model.
        assert getattr(field, "model", None) is not None, (
            "%s: field not associated after model creation" % label)
        assoc_checks += 1
        s1 = shadow_hash(field)
        o1 = oracle_hash(field)
        if s1 != o1:
            disagreements.append(("%s associated shadow!=oracle" % label, s1, o1))
            return
        # immutability: the oracle digest did not change across association
        # (the modeled `∀ a, out = pyHash (fieldKeyAt intrinsicId a)`).
        if o0 != o1:
            disagreements.append(("%s NOT immutable across assignment" % label,
                                  o0, o1))

    # --- boundary: the explicit F2P scenario (hashed before/after assignment) -
    boundary = [models.IntegerField(), models.CharField(max_length=200),
                models.BooleanField()]
    for i, f in enumerate(boundary):
        check_assoc(f, "boundary[%d]" % i)

    # --- observable (2): bounded immutability/association leg -----------------
    for _ in range(N_ASSOC):
        if len(disagreements) >= 8:
            break
        check_assoc(make_field(), "assoc")

    # --- observable (1): full-scale R/I fidelity leg --------------------------
    for _ in range(N_FUZZ):
        if len(disagreements) >= 8:
            break
        check_ri(make_field(), "fuzz")

    total = ri_checks + assoc_checks
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checks (seed=%d):"
              % (len(disagreements), total, SEED))
        for d in disagreements:
            print("  %r got %r vs %r" % d)
        return 1
    print("G-CONF OK: R/I shadow of fieldHashMethod agrees with patch.diff "
          "behaviour (real Field.__hash__) on %d checks (seed=%d), 0 "
          "disagreements: %d standalone shadow==oracle fidelity checks and %d "
          "model-association immutability checks (hash == hash(creation_counter) "
          "and unchanged across model assignment)." %
          (total, SEED, ri_checks, assoc_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
