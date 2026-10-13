#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11740 (nagini).

SHADOW: the impl region of model.py `altered_field_dependencies`, copied
verbatim below with the contract calls (Requires/Ensures) stripped, on top of
a tuple-backed PSeq shim. The one @Pure @ContractOnly callee of the impl,
`fk_dependencies`, is bridged to the REAL repo helper
`MigrationAutodetector._get_dependencies_for_foreign_key` (per mapping.md
section 3.1): the shadow calls the real callee, exactly as the contract
prescribes for @ContractOnly callees.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
dependency list that `MigrationAutodetector.generate_altered_fields` attaches
to each emitted `AlterField` operation, observed as the operation's stored
`_auto_deps` (the value `add_operation` records; mapping.md section 1). The
gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the imported autodetector is the patched one. Each
generated input is a real (before, after) ProjectState pair in which one or
more model fields change definition; a recording autodetector subclass runs
the real `_detect_changes` pipeline and captures every AlterField's attached
dependency list at `add_operation` time.

Type bridge (mapping.md section 2):
  - `FieldDef.is_relation` <-> `hasattr(new_field, "remote_field") and
    getattr(new_field.remote_field, "model", None)` truthy, evaluated on the
    real new-state field object the autodetector used.
  - `PSeq[int]` of opaque dependency codes <-> the repo list of 4-tuples:
    each distinct tuple is interned to an int code; PSeq `+` <-> list extend
    from empty; the shadow's decoded tuple list is compared elementwise
    against the operation's real `_auto_deps`.

Input domain: the model's Requires is a pure access permission, so every
field definition is Requires-satisfying; the realizable inputs are the field
alterations that actually reach the modeled per-field behaviour (the pair
must differ and be m2m-compatible so an AlterField is emitted — enforced by
construction and asserted). Boundary cases cover: plain -> FK other app (the
failure shape), FK -> plain, FK target change, FK same app / self, OneToOne,
m2m target change, m2m auto <-> explicit through, null toggles (including
the not-null questioner path), plain-type changes, and multi-field states
mixing relational and non-relational alters. Fuzz draws random (old, new)
definition pairs from a maker table with randomized attributes.

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz until 100000+
altered-field inputs are diffed. Pinned fuzz seed: 11740.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random fuzzer; hypothesis not required).
"""
import json
import random
import sys

SEED = 11740
TARGET_CHECKS = 100_000


# --- PSeq shim: immutable sequence, the operations the impl uses -------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t


# --- FieldDef carrier (model.py), contract call stripped ----------------------

class FieldDef:
    def __init__(self, is_relation):
        self.is_relation = is_relation


# --- dependency-tuple <-> opaque int code interning (mapping.md section 2) ----

_CODES = {}
_TUPLES = []


def intern_dep(dep):
    dep = tuple(dep)
    if dep not in _CODES:
        _CODES[dep] = len(_TUPLES)
        _TUPLES.append(dep)
    return _CODES[dep]


def decode(seq):
    return [_TUPLES[seq[i]] for i in range(len(seq))]


# --- the @ContractOnly callee, bridged to the REAL repo helper ----------------

def fk_dependencies(field):
    # @ContractOnly: call the REAL unchanged repo helper on the real field
    # object the carrier abstracts (mapping.md section 3.1), lifting its
    # tuple list to a PSeq of interned codes.
    deps = field._autodetector._get_dependencies_for_foreign_key(field._real)
    return PSeq(*[intern_dep(d) for d in deps])


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def altered_field_dependencies(new_field):
    dependencies = PSeq()  # type: PSeq[int]
    if new_field.is_relation:
        dependencies = dependencies + fk_dependencies(new_field)
    return dependencies


# --- oracle plumbing: drive the REAL patched autodetector ---------------------

def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            AUTH_USER_MODEL="auth.User",
        )
    django.setup()


def make_recorder():
    from django.db.migrations.autodetector import MigrationAutodetector

    class RecordingAutodetector(MigrationAutodetector):
        """Captures, at add_operation time, the dependency list each
        AlterField operation is stored with (its _auto_deps)."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.recorded_alter_deps = {}

        def add_operation(self, app_label, operation, dependencies=None,
                          beginning=False):
            super().add_operation(app_label, operation,
                                  dependencies=dependencies,
                                  beginning=beginning)
            if type(operation).__name__ == "AlterField":
                key = (app_label, operation.model_name, operation.name)
                self.recorded_alter_deps[key] = list(operation._auto_deps)

    return RecordingAutodetector


# --- input generation ----------------------------------------------------------
# Each field alteration is one input to the modeled per-field behaviour.
# Makers build fresh field instances; keys pin distinctness of the definition.

def build_makers():
    from django.db import models

    def fk(target, null=True):
        return lambda: models.ForeignKey(
            target, models.CASCADE if not null else models.SET_NULL,
            null=null, related_name="+")

    def o2o(target):
        return lambda: models.OneToOneField(
            target, models.SET_NULL, null=True, related_name="+")

    def m2m(target, blank=False, through=None):
        def make():
            kwargs = {"related_name": "+", "blank": blank}
            if through:
                kwargs["through"] = through
            return models.ManyToManyField(target, **kwargs)
        return make

    plain = {
        "int_null": lambda: models.IntegerField(null=True),
        "int_notnull_default": lambda: models.IntegerField(default=0),
        "int_notnull": lambda: models.IntegerField(),
        "bigint": lambda: models.BigIntegerField(null=True),
        "bool_t": lambda: models.BooleanField(default=True),
        "bool_f": lambda: models.BooleanField(default=False),
        "char10": lambda: models.CharField(max_length=10, null=True),
        "char20": lambda: models.CharField(max_length=20, null=True),
        "char20_notnull": lambda: models.CharField(max_length=20, default=""),
        "text": lambda: models.TextField(null=True),
        "float": lambda: models.FloatField(null=True),
        "date": lambda: models.DateField(null=True),
    }
    relational = {
        "fk_other": fk("otherapp.Target"),
        "fk_other_notnull": fk("otherapp.Target", null=False),
        "fk_other2": fk("otherapp.Target2"),
        "fk_peer": fk("testapp.Peer"),
        "fk_self": fk("testapp.Source"),
        "o2o_other": o2o("otherapp.Target"),
        "o2o_other2": o2o("otherapp.Target2"),
    }
    concrete = {}
    concrete.update(plain)
    concrete.update(relational)
    m2ms = {
        "m2m_target": m2m("otherapp.Target"),
        "m2m_target_blank": m2m("otherapp.Target", blank=True),
        "m2m_target2": m2m("otherapp.Target2"),
        "m2m_through": m2m("otherapp.Target", through="testapp.Through"),
    }
    return concrete, m2ms


def build_states(field_pairs):
    """Build (before, after) ProjectStates for a Source model whose fields
    f<i> change from field_pairs[i][0] to field_pairs[i][1]."""
    from django.db import models
    from django.db.migrations.state import ModelState, ProjectState

    def state(which):
        s = ProjectState()
        s.add_model(ModelState("otherapp", "Target", [
            ("id", models.AutoField(primary_key=True))]))
        s.add_model(ModelState("otherapp", "Target2", [
            ("id", models.AutoField(primary_key=True))]))
        s.add_model(ModelState("testapp", "Peer", [
            ("id", models.AutoField(primary_key=True))]))
        s.add_model(ModelState("testapp", "Through", [
            ("id", models.AutoField(primary_key=True)),
            ("src", models.ForeignKey("testapp.Source", models.CASCADE,
                                      related_name="+")),
            ("dst", models.ForeignKey("otherapp.Target", models.CASCADE,
                                      related_name="+")),
        ]))
        fields = [("id", models.AutoField(primary_key=True))]
        for i, (old_make, new_make) in enumerate(field_pairs):
            make = old_make if which == "old" else new_make
            fields.append(("f%d" % i, make()))
        s.add_model(ModelState("testapp", "Source", fields))
        return s

    return state("old"), state("new")


def check_scenario(recorder_cls, field_pairs, label):
    """Run the real pipeline on one (before, after) pair; diff the shadow
    against the recorded dependency list for every altered field. Returns
    (n_checked, error_or_None)."""
    before, after = build_states(field_pairs)
    ad = recorder_cls(before, after)
    ad._detect_changes()

    n = 0
    for i in range(len(field_pairs)):
        key = ("testapp", "source", "f%d" % i)
        if key not in ad.recorded_alter_deps:
            return n, ("SCENARIO BUG (%s): no AlterField recorded for %s "
                       "(recorded: %r)" % (label, key,
                                           sorted(ad.recorded_alter_deps)))
        real_deps = ad.recorded_alter_deps[key]

        # the real new-state field object the autodetector observed
        real_field = ad.new_apps.get_model("testapp", "Source")._meta.get_field(
            "f%d" % i)
        # bridge: the carrier's single observed property (mapping.md sec. 2)
        is_rel = bool(hasattr(real_field, "remote_field") and
                      getattr(real_field.remote_field, "model", None))
        fd = FieldDef(is_rel)
        fd._real = real_field
        fd._autodetector = ad

        shadow = decode(altered_field_dependencies(fd))
        if shadow != [tuple(d) for d in real_deps]:
            return n, ("DISAGREEMENT (%s, field f%d)\n"
                       "  is_relation=%r\n  shadow=%r\n  real=%r"
                       % (label, i, is_rel, shadow, real_deps))
        n += 1
    return n, None


def boundary_scenarios(concrete, m2ms):
    c, m = concrete, m2ms
    single = [
        ("int_null", "fk_other"),            # plain -> relational (the bug shape)
        ("fk_other", "int_null"),            # relational -> plain
        ("char10", "char20"),                # plain type param change
        ("int_null", "int_notnull"),         # null -> not-null (questioner path)
        ("int_notnull_default", "int_null"),
        ("fk_other", "fk_other2"),           # target change
        ("fk_other", "fk_peer"),             # other app -> same app
        ("fk_peer", "fk_self"),              # same app -> self
        ("o2o_other", "fk_other"),           # o2o <-> fk
        ("fk_other", "o2o_other"),
        ("int_null", "o2o_other2"),
        ("fk_other_notnull", "fk_other"),    # relational null toggle
        ("bool_t", "bool_f"),
        ("int_null", "char10"),
    ]
    scenarios = [([(c[a], c[b])], "boundary %s->%s" % (a, b))
                 for a, b in single]
    m2m_single = [
        ("m2m_target", "m2m_target2"),
        ("m2m_target", "m2m_target_blank"),
        ("m2m_target", "m2m_through"),       # auto -> explicit through
        ("m2m_through", "m2m_target"),       # explicit -> auto through
    ]
    scenarios += [([(m[a], m[b])], "boundary m2m %s->%s" % (a, b))
                  for a, b in m2m_single]
    # multi-field: relational and plain alters side by side in one model
    combo = [(c["int_null"], c["fk_other"]),
             (c["fk_other2"], c["char10"]),
             (c["char10"], c["char20"]),
             (c["fk_peer"], c["fk_other2"])]
    scenarios.append((combo, "boundary multi-field combo"))
    combo2 = [(m["m2m_target"], m["m2m_target2"]),
              (m["m2m_through"], m["m2m_target"])]
    scenarios.append((combo2, "boundary multi-field m2m combo"))
    return scenarios


def fuzz_scenario(rng, concrete, m2ms):
    """Random multi-field scenario: each field picks a group (concrete or
    m2m — never across, so an AlterField is emitted) and two distinct
    definitions within it."""
    pairs = []
    names = []
    k = rng.randint(1, 8)
    ckeys = sorted(concrete)
    mkeys = sorted(m2ms)
    for _ in range(k):
        if rng.random() < 0.8:
            a, b = rng.sample(ckeys, 2)
            pairs.append((concrete[a], concrete[b]))
        else:
            a, b = rng.sample(mkeys, 2)
            pairs.append((m2ms[a], m2ms[b]))
        names.append("%s->%s" % (a, b))
    return pairs, "fuzz " + ", ".join(names)


def main():
    configure_django()
    recorder_cls = make_recorder()
    concrete, m2ms = build_makers()

    checked = 0
    n_boundary = 0
    for pairs, label in boundary_scenarios(concrete, m2ms):
        n, err = check_scenario(recorder_cls, pairs, label)
        checked += n
        n_boundary += n
        if err:
            print(err)
            return 1

    rng = random.Random(SEED)
    while checked < TARGET_CHECKS:
        pairs, label = fuzz_scenario(rng, concrete, m2ms)
        n, err = check_scenario(recorder_cls, pairs, label)
        checked += n
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real patched altered-field dependency "
          "list on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee -> real repo helper)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
