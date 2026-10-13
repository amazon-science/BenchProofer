# P2 adversarial audit — django__django-15563

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate 'shared_column_weak' routes ALL non-pk-shared ancestors through a SINGLE shared extra column instead of a distinct column per ancestor (violating Req 1.5). It resolves the single-independent-parent F2P shape (probes 1,2,4 pass) but probe_3 REJECTS it: with Child(Base, OtherB, ThirdB) where the two independent ancestors' pk spaces are made to DIVERGE (4 pre-existing OtherB rows vs 2 ThirdB rows -> children get otherb pks 5,6 and thirdb pks 3,4), the shared column feeds one ancestor's ids to the other, corrupting pre-existing rows. Observed under weak patch: probe_3 VIOLATED (unrelated ancestor rows clobbered), matching the base-tree failure mode.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Probe 1 — POSITIVE CONTROL. Requirement 3.1 + 3.2 + 3.4.

Reproduces the problem-statement diamond: Child(Base, OtherBase). `Base` is the
primary-key-chain parent (Child.pk == base_ptr); `OtherBase` is a
non-primary-key-shared ancestor. Updating `field_otherbase` (owned by OtherBase)
through the Child queryset MUST:
  (3.1) give the child's own rows the new value,
  (3.2) leave unrelated OtherBase rows untouched,
  (3.4) survive a re-read.
On the BUGGY (base) tree the OtherBase UPDATE is filtered by the child's own pk
values, so unrelated OtherBase rows get clobbered and the children are unchanged.
Exit 0 iff the correct behavior holds.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherBase(models.Model):
        otherbase_id = models.AutoField(primary_key=True)
        field_otherbase = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherBase):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherBase, Child):
            ed.create_model(m)

    # Two unrelated OtherBase rows (ids 1,2), holding 100/101.
    o1 = OtherBase.objects.create(field_otherbase=100)
    o2 = OtherBase.objects.create(field_otherbase=101)
    # Two Child rows. Their otherbase_id values are independent (3,4).
    Child.objects.create(field_base=0, field_otherbase=0)
    Child.objects.create(field_base=1, field_otherbase=1)

    Child.objects.update(field_otherbase=55)

    child_vals = sorted(Child.objects.values_list("field_otherbase", flat=True))
    o1r = OtherBase.objects.get(pk=o1.pk).field_otherbase
    o2r = OtherBase.objects.get(pk=o2.pk).field_otherbase
    print(f"child field_otherbase = {child_vals}")
    print(f"unrelated OtherBase rows = {o1r}, {o2r} (expect 100, 101)")

    ok_child = child_vals == [55, 55]           # Req 3.1 / 3.4
    ok_unrelated = (o1r == 100 and o2r == 101)   # Req 3.2
    if ok_child and ok_unrelated:
        print("HOLD: children updated, unrelated ancestor rows preserved")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe 2 — Requirement 3.3. Grandparent-through-child (the F2P
`test_mti_update_grand_parent_through_child` shape).

Tree: Politician (pk politician_id) <- Congressman(Person, Politician) <- Senator.
`title` lives on Politician, reached from Senator through the Person link (NOT a
pk chain). Updating title via Senator.objects.update MUST set the correct
Politician row for the Senator instance. On base, the Politician UPDATE is
filtered by the senator/base pk value, missing the real Politician row.
Exit 0 iff the re-read title equals what was written.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Person(models.Model):
        name = models.CharField(max_length=100, blank=True)
        class Meta: app_label = "contenttypes"

    class Politician(models.Model):
        politician_id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=50, blank=True)
        class Meta: app_label = "contenttypes"

    class Congressman(Person, Politician):
        state = models.CharField(max_length=2, blank=True)
        class Meta: app_label = "contenttypes"

    class Senator(Congressman):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Person, Politician, Congressman, Senator):
            ed.create_model(m)

    # Create a stray Politician first so pk spaces diverge (row 1).
    Politician.objects.create(title="unrelated")
    Senator.objects.create()
    Senator.objects.update(title="senator 1")

    got = Senator.objects.get().title
    stray = Politician.objects.get(politician_id=1).title
    print(f"senator title after update = {got!r} (expect 'senator 1')")
    print(f"unrelated politician row 1 title = {stray!r} (expect 'unrelated')")
    if got == "senator 1" and stray == "unrelated":
        print("HOLD")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe 3 — Requirement 1.5 + 2.4: when MORE THAN ONE ancestor is not
primary-key-shared, each gets a DISTINCT pre-selected key column so no two
ancestors read identifiers from the same column, and each auxiliary UPDATE is
restricted to its own ancestor's identifiers (not another model's).

Tree with TWO independent-pk ancestors:
    Child(Base, OtherB, ThirdB)
Base is the pk-shared parent (child pk == base_ptr). OtherB and ThirdB each have
their own AutoField pk, independent of the child's pk -> both non-pk-shared.
We update a field owned by OtherB and a field owned by ThirdB in one update().

If the two independent ancestors shared one identifier column (no distinct
allocation), one of them would be filtered by the other's ids and update the
wrong rows. Correct routing requires: OtherB's rows and ThirdB's rows are BOTH
set for the children, while unrelated pre-existing rows of each ancestor table
(whose pks numerically coincide with the children's pks) stay unchanged.
Exit 0 iff both independent ancestors are routed to their own rows.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherB(models.Model):
        otherb_id = models.AutoField(primary_key=True)
        field_otherb = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class ThirdB(models.Model):
        thirdb_id = models.AutoField(primary_key=True)
        field_thirdb = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherB, ThirdB):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherB, ThirdB, Child):
            ed.create_model(m)

    # Pre-create DIFFERENT numbers of rows in each independent ancestor so the
    # children's otherb pks and thirdb pks DIVERGE. This is what breaks a naive
    # "single shared extra column" fix: the two ancestors then need different
    # id lists, so a shared column would filter one ancestor on the other's ids.
    for i in range(4):
        OtherB.objects.create(field_otherb=1000 + i)   # otherb ids 1..4
    for i in range(2):
        ThirdB.objects.create(field_thirdb=2000 + i)   # thirdb ids 1..2

    # Two children: otherb pks -> 5,6 ; thirdb pks -> 3,4 (divergent).
    Child.objects.create(field_base=0, field_otherb=0, field_thirdb=0)
    Child.objects.create(field_base=1, field_otherb=1, field_thirdb=1)

    Child.objects.update(field_otherb=55, field_thirdb=66)

    child_o = sorted(Child.objects.values_list("field_otherb", flat=True))
    child_t = sorted(Child.objects.values_list("field_thirdb", flat=True))
    # Pre-existing (non-child) ancestor rows must all keep their original values.
    unrel_o = sorted(OtherB.objects.filter(
        otherb_id__in=[1, 2, 3, 4]).values_list("field_otherb", flat=True))
    unrel_t = sorted(ThirdB.objects.filter(
        thirdb_id__in=[1, 2]).values_list("field_thirdb", flat=True))
    print(f"child field_otherb={child_o} (expect [55,55])")
    print(f"child field_thirdb={child_t} (expect [66,66])")
    print(f"unrelated OtherB ids1-4={unrel_o} (expect [1000,1001,1002,1003])")
    print(f"unrelated ThirdB ids1,2={unrel_t} (expect [2000,2001])")

    ok = (child_o == [55, 55] and child_t == [66, 66]
          and unrel_o == [1000, 1001, 1002, 1003]
          and unrel_t == [2000, 2001])
    if ok:
        print("HOLD: two independent ancestors each routed by their own column")
        return 0
    print("VIOLATED: independent ancestors not given distinct id routing")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe 4 — Requirement 2.2 / 2.4 structural: after pre_sql_setup, the
UpdateQuery's `related_ids` state SHALL be keyed per ancestor model (a mapping
model -> list of that ancestor's identifiers), NOT a single flat list reused for
every ancestor. And get_related_updates SHALL filter each auxiliary UPDATE on
that ancestor's own identifiers.

We drive an update on the diamond and inspect the resulting UpdateQuery.
related_ids: it must be a dict-like mapping keyed by the OtherBase model whose
value is OtherBase's own pk values (the independent ones), distinct from the
child's own pk list. On base, related_ids is a flat list of the child pks.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection
    from django.db.models.sql.subqueries import UpdateQuery
    from django.db.models.sql.compiler import SQLUpdateCompiler

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherBase(models.Model):
        otherbase_id = models.AutoField(primary_key=True)
        field_otherbase = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherBase):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherBase, Child):
            ed.create_model(m)

    # child rows with independent otherbase pks
    OtherBase.objects.create(field_otherbase=100)
    OtherBase.objects.create(field_otherbase=101)
    c1 = Child.objects.create(field_base=0, field_otherbase=0)
    c2 = Child.objects.create(field_base=1, field_otherbase=1)

    # Build the UpdateQuery for the otherbase field manually and run
    # pre_sql_setup so related_ids gets populated.
    uq = UpdateQuery(Child)
    uq.add_update_values({"field_otherbase": 55})
    compiler = uq.get_compiler(using="default")
    compiler.pre_sql_setup()

    rel = uq.related_ids
    print(f"related_ids type = {type(rel).__name__}: {rel!r}")

    # Must be a mapping keyed by model, not a flat list.
    if isinstance(rel, (list, tuple)):
        print("VIOLATED: related_ids is a flat list (old behavior)")
        return 1
    try:
        keys = list(rel.keys())
    except AttributeError:
        print("VIOLATED: related_ids is not a mapping")
        return 1

    # OtherBase must be a key, and its ids must be OtherBase's own pks (the
    # independent otherbase_id values of the two children), not the child pks.
    if OtherBase not in keys:
        print(f"VIOLATED: OtherBase not keyed in related_ids; keys={keys}")
        return 1
    ob_ids = sorted(rel[OtherBase])
    child_ob_pks = sorted(
        Child.objects.values_list("otherbase_id", flat=True))
    child_own_pks = sorted(Child.objects.values_list("pk", flat=True))
    print(f"related_ids[OtherBase] = {ob_ids}")
    print(f"children's otherbase pks = {child_ob_pks}")
    print(f"children's own pks       = {child_own_pks}")

    if ob_ids == child_ob_pks and ob_ids != child_own_pks:
        print("HOLD: per-ancestor identifiers keyed to OtherBase's own pks")
        return 0
    print("VIOLATED: OtherBase identifiers are not its own pk values")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe 5 — Requirement 4.2 (regression): a field owned by a pk-SHARED
ancestor is updated correctly, targeted by the model's own pk. Standard
single-inheritance MTI: Restaurant(Place). Place is the pk-shared parent
(Restaurant.pk == place_ptr). Updating Place's `name` via Restaurant.update
must change exactly the restaurant's Place row, and re-read matches.
Also asserts unrelated Place rows are untouched.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Place(models.Model):
        name = models.CharField(max_length=50, blank=True)
        address = models.CharField(max_length=80, blank=True)
        class Meta: app_label = "contenttypes"

    class Restaurant(Place):
        serves_pizza = models.BooleanField(default=False)
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Place, Restaurant):
            ed.create_model(m)

    stray = Place.objects.create(name="stray", address="x")
    r = Restaurant.objects.create(name="old", address="a", serves_pizza=True)

    Restaurant.objects.update(name="new")

    got = Restaurant.objects.get(pk=r.pk).name
    stray_name = Place.objects.get(pk=stray.pk).name
    print(f"restaurant name after update = {got!r} (expect 'new')")
    print(f"stray Place name = {stray_name!r} (expect 'stray')")
    if got == "new" and stray_name == "stray":
        print("HOLD: pk-shared ancestor updated by model's own pk, no spillover")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Probe 6 — Requirement 4.3: the primary update SHALL keep returning the
number of rows affected by the primary update query, unchanged by per-ancestor
routing. Also Req 4.1/4.4: an update whose changed fields are all owned by the
model itself (no related updates) behaves as before and returns the row count.

Diamond Child(Base, OtherBase). Update field_otherbase for the 3 children ->
update() must return 3 (count of matched primary rows), not the count of
touched ancestor rows nor 0. Also update with a filter matching a subset.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherBase(models.Model):
        otherbase_id = models.AutoField(primary_key=True)
        field_otherbase = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherBase):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherBase, Child):
            ed.create_model(m)

    OtherBase.objects.create(field_otherbase=100)
    for i in range(3):
        Child.objects.create(field_base=i, field_otherbase=i)

    # Full update: 3 children matched.
    n_all = Child.objects.update(field_otherbase=55)
    print(f"update-all returned {n_all} (expect 3)")

    # Subset update: 2 children matched via a filter on the child pk range.
    pks = list(Child.objects.values_list("pk", flat=True))
    subset = pks[:2]
    n_sub = Child.objects.filter(pk__in=subset).update(field_otherbase=77)
    print(f"subset update returned {n_sub} (expect 2)")

    if n_all == 3 and n_sub == 2:
        print("HOLD: update returns matched primary-row count")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 — POSITIVE CONTROL. Requirement 3.1 + 3.2 + 3.4.

Reproduces the problem-statement diamond: Child(Base, OtherBase). `Base` is the
primary-key-chain parent (Child.pk == base_ptr); `OtherBase` is a
non-primary-key-shared ancestor. Updating `field_otherbase` (owned by OtherBase)
through the Child queryset MUST:
  (3.1) give the child's own rows the new value,
  (3.2) leave unrelated OtherBase rows untouched,
  (3.4) survive a re-read.
On the BUGGY (base) tree the OtherBase UPDATE is filtered by the child's own pk
values, so unrelated OtherBase rows get clobbered and the children are unchanged.
Exit 0 iff the correct behavior holds.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherBase(models.Model):
        otherbase_id = models.AutoField(primary_key=True)
        field_otherbase = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherBase):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherBase, Child):
            ed.create_model(m)

    # Two unrelated OtherBase rows (ids 1,2), holding 100/101.
    o1 = OtherBase.objects.create(field_otherbase=100)
    o2 = OtherBase.objects.create(field_otherbase=101)
    # Two Child rows. Their otherbase_id values are independent (3,4).
    Child.objects.create(field_base=0, field_otherbase=0)
    Child.objects.create(field_base=1, field_otherbase=1)

    Child.objects.update(field_otherbase=55)

    child_vals = sorted(Child.objects.values_list("field_otherbase", flat=True))
    o1r = OtherBase.objects.get(pk=o1.pk).field_otherbase
    o2r = OtherBase.objects.get(pk=o2.pk).field_otherbase
    print(f"child field_otherbase = {child_vals}")
    print(f"unrelated OtherBase rows = {o1r}, {o2r} (expect 100, 101)")

    ok_child = child_vals == [55, 55]           # Req 3.1 / 3.4
    ok_unrelated = (o1r == 100 and o2r == 101)   # Req 3.2
    if ok_child and ok_unrelated:
        print("HOLD: children updated, unrelated ancestor rows preserved")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive control (probe_1, the problem-statement Base/OtherBase diamond, Req 3.1/3.2/3.4) FAILS at base (children stay unchanged, unrelated OtherBase rows clobbered to 55,55) and HOLDS patched -> discriminates. Coverage: probe_1 Req3.1/3.2/3.4 (diamond correctness); probe_2 Req3.3 (grandparent-through-child, F2P shape); probe_3 Req1.5/2.4 (two independent ancestors need DISTINCT columns) -- also fails at base and rejects the weak patch; probe_4 Req2.2/2.4 (related_ids is a per-model mapping keyed by ancestor with the ancestor's OWN pk values, not a flat list -> also fails at base); probe_5 Req4.2 (pk-shared single-inheritance ancestor still updated by model's own pk, no spillover); probe_6 Req4.3/4.1 (update() returns matched primary-row count, full=3/subset=2). The weak candidate is a plausible partial fix a loose reading of Req 1.4 permits (pre-select an extra column, but only one); the suite discriminates it via Req 1.5. Verdict SOUND: >=5 probes hold patched, positive control discriminates base vs patched, and >=1 requirements-plausible wrong patch is REJECTED by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate 'shared_column_weak' routes ALL non-pk-shared ancestors through a SINGLE shared extra column instead of a distinct column per ancestor (violating Req 1.5). It resolves the single-independent-parent F2P shape (probes 1,2,4 pass) but probe_3 REJECTS it: with Child(Base, OtherB, ThirdB) where the two independent ancestors' pk spaces are made to DIVERGE (4 pre-existing OtherB rows vs 2 ThirdB rows -> children get otherb pks 5,6 and thirdb pks 3,4), the shared column feeds one ancestor's ids to the other, corrupting pre-existing rows. Observed under weak patch: probe_3 VIOLATED (unrelated ancestor rows clobbered), matching the base-tree failure mode.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe 1 — POSITIVE CONTROL. Requirement 3.1 + 3.2 + 3.4.

Reproduces the problem-statement diamond: Child(Base, OtherBase). `Base` is the
primary-key-chain parent (Child.pk == base_ptr); `OtherBase` is a
non-primary-key-shared ancestor. Updating `field_otherbase` (owned by OtherBase)
through the Child queryset MUST:
  (3.1) give the child's own rows the new value,
  (3.2) leave unrelated OtherBase rows untouched,
  (3.4) survive a re-read.
On the BUGGY (base) tree the OtherBase UPDATE is filtered by the child's own pk
values, so unrelated OtherBase rows get clobbered and the children are unchanged.
Exit 0 iff the correct behavior holds.
"""
import sys


def cfg():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    django.setup()


def main():
    cfg()
    from django.db import models, connection

    class Base(models.Model):
        base_id = models.AutoField(primary_key=True)
        field_base = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class OtherBase(models.Model):
        otherbase_id = models.AutoField(primary_key=True)
        field_otherbase = models.IntegerField(default=0)
        class Meta: app_label = "contenttypes"

    class Child(Base, OtherBase):
        class Meta: app_label = "contenttypes"

    with connection.schema_editor() as ed:
        for m in (Base, OtherBase, Child):
            ed.create_model(m)

    # Two unrelated OtherBase rows (ids 1,2), holding 100/101.
    o1 = OtherBase.objects.create(field_otherbase=100)
    o2 = OtherBase.objects.create(field_otherbase=101)
    # Two Child rows. Their otherbase_id values are independent (3,4).
    Child.objects.create(field_base=0, field_otherbase=0)
    Child.objects.create(field_base=1, field_otherbase=1)

    Child.objects.update(field_otherbase=55)

    child_vals = sorted(Child.objects.values_list("field_otherbase", flat=True))
    o1r = OtherBase.objects.get(pk=o1.pk).field_otherbase
    o2r = OtherBase.objects.get(pk=o2.pk).field_otherbase
    print(f"child field_otherbase = {child_vals}")
    print(f"unrelated OtherBase rows = {o1r}, {o2r} (expect 100, 101)")

    ok_child = child_vals == [55, 55]           # Req 3.1 / 3.4
    ok_unrelated = (o1r == 100 and o2r == 101)   # Req 3.2
    if ok_child and ok_unrelated:
        print("HOLD: children updated, unrelated ancestor rows preserved")
        return 0
    print("VIOLATED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; positive control (probe_1, the problem-statement Base/OtherBase diamond, Req 3.1/3.2/3.4) FAILS at base (children stay unchanged, unrelated OtherBase rows clobbered to 55,55) and HOLDS patched -> discriminates. Coverage: probe_1 Req3.1/3.2/3.4 (diamond correctness); probe_2 Req3.3 (grandparent-through-child, F2P shape); probe_3 Req1.5/2.4 (two independent ancestors need DISTINCT columns) -- also fails at base and rejects the weak patch; probe_4 Req2.2/2.4 (related_ids is a per-model mapping keyed by ancestor with the ancestor's OWN pk values, not a flat list -> also fails at base); probe_5 Req4.2 (pk-shared single-inheritance ancestor still updated by model's own pk, no spillover); probe_6 Req4.3/4.1 (update() returns matched primary-row count, full=3/subset=2). The weak candidate is a plausible partial fix a loose reading of Req 1.4 permits (pre-select an extra column, but only one); the suite discriminates it via Req 1.5. Verdict SOUND: >=5 probes hold patched, positive control discriminates base vs patched, and >=1 requirements-plausible wrong patch is REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement-to-code mapping all correct: Req1.1 always pre-selects meta.pk.name (fields=[meta.pk.name]); Req1.2 classifies pk-shared iff `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))`; Req1.3 pk-shared ancestor uses index 0 (model pk) with no extra column; Req1.4 non-pk-shared appends ancestor._meta.pk.name and records its column index; Req1.5 each non-pk-shared ancestor gets `len(fields)` (a distinct new column); Req1.6 iterates self.query.related_updates in order (related_ids_index preserves order). Req2.1/2.2 build related_ids=defaultdict(list) keyed per parent from r[index]; Req2.3 model UPDATE still filtered pk__in idents; Req2.4 get_related_updates uses self.related_ids[model] not a shared list; Req2.5 related_ids default None -> unfiltered aux updates (subqueries.py:63 self.related_ids=None, guarded by `if self.related_ids is not None`). Req4 regression cases: fast path unchanged, pk-shared ancestors still driven by model pk, count returned unchanged. Boundary is the changed observable behavior (non-pk-shared ancestor UPDATE targeting), not a narrow slice. G-EQ already pass with positive control discriminating base vs patched.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally without transmitting hidden-test content. No test file paths, function/class names (test_mti_update_parent_through_child, test_mti_update_grand_parent_through_child, model_inheritance_regress, ModelInheritanceTest) appear. Hidden-test model names (Politician/Congressman/Senator) are absent; the doc reuses only the public problem_statement's generic ancestor/parent/child framing. Gold-patch-invented identifiers (related_ids_index, get_path_to_parent, related_ids dict) are NOT reproduced — the doc uses descriptive prose ('path from the model to that ancestor', 'primary-key-shared', 'dedicated key column'). Naming SQLUpdateCompiler.pre_sql_setup / UpdateQuery.get_related_updates / Query.related_ids/related_updates is legitimate localization of the changed code (pre-existing public attributes). The only content beyond the public problem_statement is Req 3.3's 'grandparent through a child' indirect-ancestor scenario (which maps to the second FAIL_TO_PASS test), but it is phrased as a behavioral generalization of MTI depth rather than a test-shaped enumeration reproducing parametrization/model setups — that is the legitimate translation of test-checked behavior into requirements, not transmission of the test.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
