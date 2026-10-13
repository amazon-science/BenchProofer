#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15973 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `resolveRef` (deep model of the relation resolver, an
              A-reference — here transliterated, NOT substituted by an axiom, so
              the differential test exercises the real R/I data-flow), `baseDep`,
              and the `relationDeps` through-branch logic. Built over the real
              repo carriers (model reference strings / model objects, the
              dependency 4-tuple), via the mapping.md §2 bijection.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, patched
              `MigrationAutodetector._get_dependencies_for_foreign_key`
              (the correctness oracle, G-RESOLVE). The harness applies patch.diff
              at base_commit before this runs, so the live callee resolves the
              through dependency from `field.remote_field.through`.

The modeled function reads only `field.remote_field.{model,through}` and
`field.swappable_setting` on the F2P path (`project_state` is consulted only in a
branch unreachable for relational fields — mapping.md §1), so the oracle is
driven DB-free with duck-typed field objects. This bundle therefore has a
runnable R/I shadow (`conf_skip = false`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15973
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


# --- the R/I shadow: Solution.lean resolveRef / baseDep / relationDeps --------
# A RelRef is a tuple: ("selfRef",) | ("qualified", a, n) | ("bare", n) |
#                      ("resolved", a, n).

def resolve_ref(ref, app_label, model_name):
    """Transliteration of Solution.lean `resolveRef`."""
    kind = ref[0]
    if kind == "selfRef":
        return (app_label, model_name)
    if kind == "qualified":
        return (ref[1], ref[2].lower())
    if kind == "bare":
        return (app_label, ref[1].lower())
    if kind == "resolved":
        return (ref[1], ref[2])
    raise AssertionError("unknown RelRef %r" % (ref,))


def mk_dep(pair):
    """Transliteration of `mkDep`: a create-time dependency 4-tuple."""
    return (pair[0], pair[1], None, True)


def base_dep(target, swappable, app_label, model_name):
    """Transliteration of `baseDep`."""
    if swappable is not None:
        return ("__setting__", swappable, None, True)
    return mk_dep(resolve_ref(target, app_label, model_name))


def shadow_deps(target, through, swappable, app_label, model_name):
    """Transliteration of `relationDeps` (the R/I shadow of the impl)."""
    d = base_dep(target, swappable, app_label, model_name)
    if through is None:
        return [d]
    return [d, mk_dep(resolve_ref(through, app_label, model_name))]


# --- the bijection to the REAL field object (mapping.md §2) -------------------

class _FakeMeta:
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name


class _FakeModel:
    def __init__(self, app_label, model_name):
        self._meta = _FakeMeta(app_label, model_name)


def real_reference(ref):
    """Build the REAL value resolve_relation receives for a RelRef."""
    kind = ref[0]
    if kind == "selfRef":
        return "self"
    if kind == "qualified":
        return "%s.%s" % (ref[1], ref[2])
    if kind == "bare":
        return ref[1]
    if kind == "resolved":
        return _FakeModel(ref[1], ref[2])
    raise AssertionError("unknown RelRef %r" % (ref,))


class _RemoteField:
    def __init__(self, model, through):
        self.model = model
        self.through = through


class _Field:
    def __init__(self, target, through, swappable):
        self.remote_field = _RemoteField(real_reference(target),
                                         None if through is None
                                         else real_reference(through))
        self.swappable_setting = swappable


def make_oracle():
    from django.db.migrations.autodetector import MigrationAutodetector
    fn = MigrationAutodetector._get_dependencies_for_foreign_key

    def oracle(target, through, swappable, app_label, model_name):
        field = _Field(target, through, swappable)
        return [tuple(t) for t in fn(app_label, model_name, field, None)]
    return oracle


# --- fuzz generation ----------------------------------------------------------

def fuzz_inputs(n, rng):
    scopes = [("authors", "author"), ("fonte", "fontemodel"),
              ("testapp", "publisher"), ("app1", "modela")]
    idents = ["Publisher", "Contract", "VariavelModel", "FonteVariavelModel",
              "Author", "lower", "MiXeD", "X"]
    apps = ["testapp", "contract", "variavel", "fonte_variavel", "authors",
            "fonte", "app2"]

    def rand_ref():
        k = rng.randint(0, 3)
        if k == 0:
            return ("selfRef",)
        if k == 1:
            return ("qualified", rng.choice(apps), rng.choice(idents))
        if k == 2:
            return ("bare", rng.choice(idents))
        return ("resolved", rng.choice(apps), rng.choice(idents).lower())

    # boundary cases first (plan §4.1 step 4)
    boundary = [
        # the issue / F2P shape: M2M through an intermediary in a DIFFERENT app
        (("qualified", "testapp", "Publisher"),
         ("qualified", "contract", "Contract"), None, "authors", "author"),
        # through in the SAME app
        (("qualified", "testapp", "Publisher"),
         ("qualified", "authors", "Through"), None, "authors", "author"),
        # no through (plain FK / O2O)
        (("qualified", "testapp", "Publisher"), None, None, "authors", "author"),
        # bare references
        (("bare", "Publisher"), ("bare", "Contract"), None, "authors", "author"),
        # self reference target with through
        (("selfRef",), ("qualified", "contract", "Contract"), None, "fonte",
         "fontemodel"),
        # resolved (model object) refs
        (("resolved", "testapp", "publisher"),
         ("resolved", "contract", "contract"), None, "authors", "author"),
        # swappable target, with through (base dep is __setting__, through still
        # resolved from the intermediary)
        (("qualified", "testapp", "Publisher"),
         ("qualified", "contract", "Contract"), "AUTH_USER_MODEL", "authors",
         "author"),
        # swappable, no through
        (("qualified", "testapp", "Publisher"), None, "AUTH_USER_MODEL",
         "authors", "author"),
    ]
    for case in boundary:
        yield case

    for _ in range(n):
        target = rand_ref()
        through = rand_ref() if rng.random() < 0.6 else None
        swappable = rng.choice([None, None, None, "AUTH_USER_MODEL", "MY_SETTING"])
        app_label, model_name = rng.choice(scopes)
        yield (target, through, swappable, app_label, model_name)


def main():
    _setup_django()
    oracle = make_oracle()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (target, through, swappable, app_label, model_name) in \
            fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_deps(target, through, swappable, app_label, model_name)
        orc = oracle(target, through, swappable, app_label, model_name)
        if shadow != orc:
            disagreements.append((target, through, swappable, app_label,
                                  model_name, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for t, th, sw, al, mn, sh, orc in disagreements:
            print("  target=%r through=%r swappable=%r scope=(%r,%r)\n"
                  "    shadow=%r\n    oracle=%r" % (t, th, sw, al, mn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of relationDependencies agrees with patch.diff "
          "behaviour (real _get_dependencies_for_foreign_key) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
