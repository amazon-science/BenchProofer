#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-12325 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's impl region transliterated to Python over the real
              repo types, via the mapping.md §2 bijection:
                  refs        <->  the class's DECLARED OneToOneField list, in
                                   declaration order (base._meta.local_fields
                                   filtered to isinstance(field, OneToOneField),
                                   scanned BEFORE the auto `<model>_ptr` is
                                   synthesised)
                  Ref.isLink  <->  field.remote_field.parent_link  (bool)
                  Ref.target  <->  make_model_tuple(resolve_relation(...))
                  LinkMap     <->  the `parent_links` dict
                  selectRef   <->  the patched guarded write
                                   `if isinstance(..) and parent_link: dict[k]=f`
                  collectLinks<->  the left-to-right fold over the scanned fields
              chained with the UNCHANGED downstream selection/synthesis step
              (mapping.md §2.1, an I-tagged op): the end-to-end observable is
              `child._meta.parents[<ancestor>].name` — the selected field's name
              if the ancestor key is in `parent_links`, else the synthesised
              `'<ancestor model_name>_ptr'`.
              There are NO A-tagged ops (no consumed axioms / deep-model refs),
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched ModelBase.__new__ run by
              constructing the class, read back as `child._meta.parents[anc].name`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: only class construction and `_meta` inspection. stdlib +
django only; in-memory sqlite. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 12325
N_FUZZ = 100_000
MAX_FIELDS = 4


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


# --- the R/I shadow: Solution.lean selectRef / collectLinks + §2.1 synthesis ---
def shadow_parent_name(spec, ptr_name):
    """spec : list of bool — the declared OneToOneFields' parent_link flags, in
    declaration order; field i is named 'f%d'. Single ancestor (one target), so
    `collectLinks` reduces to: last declared field with isLink == True wins;
    none -> no entry. Then the §2.1 selection/synthesis (I): selected field's
    name if present, else the synthesised '<model>_ptr'."""
    selected = None  # collectLinks: last-writer-wins among isLink == True
    for i, is_link in enumerate(spec):
        if is_link:                      # selectRef's `if f.isLink` guard
            selected = "f%d" % i         # overwrite under f.target (one target)
    if selected is not None:
        return selected
    return ptr_name                      # synthesised parent link


def main():
    _bootstrap_django()
    from django.db import models
    from django.apps import apps

    class Place(models.Model):
        class Meta:
            app_label = "auth"

    ptr_name = "%s_ptr" % Place._meta.model_name   # synthesised name ('place_ptr')

    def build_and_observe(idx, spec):
        """Construct a child of Place declaring OneToOneFields per `spec` (a list
        of parent_link bools, declaration order), return the patched metaclass's
        `child._meta.parents[Place].name` (the ORACLE), then unregister it."""
        attrs = {
            "__module__": "conf_%d" % idx,
            "Meta": type("Meta", (), {"app_label": "auth"}),
        }
        for j, is_link in enumerate(spec):
            kw = dict(on_delete=models.CASCADE, related_name="+")
            if is_link:
                kw["parent_link"] = True
            attrs["f%d" % j] = models.OneToOneField(Place, **kw)
        cls = type("ConfChild_%d" % idx, (Place,), attrs)
        try:
            return cls._meta.parents[Place].name
        finally:
            apps.all_models["auth"].pop(cls._meta.model_name, None)

    rng = random.Random(SEED)

    def fuzz_specs(n):
        # boundary: every spec up to length 3 (all 2^0+..+2^3 = 15 patterns)
        from itertools import product
        for length in range(0, 4):
            for spec in product((False, True), repeat=length):
                yield list(spec)
        # randomized fuzz
        for _ in range(n):
            k = rng.randint(0, MAX_FIELDS)
            yield [rng.random() < 0.5 for _ in range(k)]

    disagreements = []
    count = 0
    for spec in fuzz_specs(N_FUZZ):
        count += 1
        shadow = shadow_parent_name(spec, ptr_name)
        oracle = build_and_observe(count, spec)
        if shadow != oracle:
            disagreements.append((spec, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for spec, sh, orc in disagreements:
            print("  spec(parent_link)=%r shadow=%r oracle=%r" % (spec, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of collectParentLinks + the unchanged "
          "selection/synthesis step agrees with patch.diff behaviour "
          "(child._meta.parents[Place].name) on %d field configurations "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
