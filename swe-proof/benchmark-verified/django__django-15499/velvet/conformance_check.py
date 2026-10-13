#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-15499 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (CreateModel <-> ModelCreate, AlterModelManagers <-> AlterManagers,
              component-object identity <-> opaque token).  Concretely the shadow
              is `reduceManagersSpec self op`:
                  self.nameLower == op.nameLower
                      -> replace [{ self with managers := op.managers }]
                         (a single creation: name/fields/options/bases from
                          `self`, managers from `op`)
                  otherwise
                      -> reduceThrough
              There are NO A-tagged callees in the computed output (no consumed
              axioms — refinement.md §C), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched real
              `CreateModel.reduce(AlterModelManagers(...), app_label)` applied at
              base_commit (the real correctness oracle, G-RESOLVE).  The harness
              applies patch.diff before this runs.

Both sides are classified into a comparable tag drawn from the same vocabulary:
  ('replace', managers_src, fields_src, options_src, bases_src, name)
        -- a single collapsed creation; each *_src is 'self' or 'op', recording
           which input the result reuses that component object from (identity).
  ('reduceThrough',)   -- the optimizer may reorder across the alteration (True)
  ('cannotReduce',)    -- the two operations cannot be combined (False)

The component sources are read by OBJECT IDENTITY (`is`) against the exact list
objects handed to the constructors, so any wrong routing (managers from `self`,
a dropped/duplicated component, or `cannotReduce` where the gold collapses) is a
mechanical R/I counterexample.  Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15499
N_FUZZ = 100_000

APP_LABEL = "testapp"


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_I18N=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        from django.db import models
        from django.db.migrations.operations.models import (
            CreateModel, AlterModelManagers,
        )
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load patched django operations: %r" % e)
        return 2

    # ---- a pool of names, exercising the case-fold bijection (name_lower) -----
    name_pool = ["Foo", "Bar", "Baz", "foo", "BAR", "Qux", "model_a", "Model_A"]

    def make_managers(tag):
        # a non-empty, identity-trackable managers list of (name, Manager) pairs
        return [("objects_%d" % tag, models.Manager())]

    def make_fields(tag):
        # non-empty so CreateModel keeps the exact list object (identity)
        return [("f_%d" % tag, models.IntegerField())]

    def make_options(tag):
        return {"verbose_name": "vn_%d" % tag}

    # ---- SHADOW: reduceManagersSpec over the bijection ------------------------
    def shadow(create_name, op_name):
        # name_lower comparison (mapping.md §2: case-folded on both sides)
        if create_name.lower() == op_name.lower():
            # replace [{ self with managers := op.managers }]
            return ("replace", "op", "self", "self", "self", create_name)
        return ("reduceThrough",)

    # ---- ORACLE: patched CreateModel.reduce(AlterModelManagers, app_label) ----
    def oracle(create_name, op_name, fields, options, cm_managers,
               am_managers):
        cm = CreateModel(
            create_name, fields=fields, options=options, bases=None,
            managers=cm_managers,
        )
        am = AlterModelManagers(name=op_name, managers=am_managers)
        result = cm.reduce(am, APP_LABEL)

        if result is False:
            return ("cannotReduce",)
        if result is True:
            return ("reduceThrough",)
        if isinstance(result, list):
            if len(result) != 1 or not isinstance(result[0], CreateModel):
                return ("replace-unexpected", repr(result))
            out = result[0]

            # Identify which input each output component object came from, by
            # OBJECT IDENTITY against the constructed cm/am attributes (robust to
            # the constructors' `x or default` defaulting).
            def src(out_obj, self_obj, op_obj):
                if out_obj is op_obj:
                    return "op"
                if out_obj is self_obj:
                    return "self"
                return "other:%r" % (out_obj,)

            return (
                "replace",
                src(out.managers, cm.managers, am.managers),
                src(out.fields, cm.fields, am.managers),
                src(out.options, cm.options, am.managers),
                src(out.bases, cm.bases, am.managers),
                out.name,
            )
        return ("unexpected", repr(result))

    # ---- input stream ---------------------------------------------------------
    def inputs(n):
        # boundary cases first (plan §4.1 step 4)
        # same model, exact name
        yield ("Foo", "Foo")
        # same model, case-differing names (name_lower bijection)
        yield ("Foo", "foo")
        yield ("BAR", "bar")
        # different models
        yield ("Foo", "Bar")
        yield ("model_a", "model_b")
        for _ in range(n):
            cn = rng.choice(name_pool)
            # bias toward same-model collapses to stress the changed arm
            if rng.random() < 0.5:
                on = cn if rng.random() < 0.5 else cn.swapcase()
            else:
                on = rng.choice(name_pool)
            yield (cn, on)

    disagreements = []
    count = 0
    tag = 0
    for cn, on in inputs(N_FUZZ):
        count += 1
        tag += 1
        fields = make_fields(tag)
        options = make_options(tag)
        cm_managers = make_managers(tag)
        am_managers = make_managers(tag + 10_000_000)
        sh = shadow(cn, on)
        try:
            orc = oracle(cn, on, fields, options, cm_managers, am_managers)
        except Exception as e:
            disagreements.append(((cn, on), sh, "ORACLE-RAISED:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append(((cn, on), sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reduceManagers (reduceManagersSpec) agrees "
          "with patch.diff (patched CreateModel.reduce + AlterModelManagers) on "
          "%d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
