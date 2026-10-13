# P2 adversarial audit — django__django-15280

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control -- Requirement 1.3 / F2P core behavior.

A House prefetches its rooms; the rooms queryset nests a prefetch back to
house restricted to only('address'). After the outer prefetch, reading
room.house.address must trigger NO extra query, because the nested prefetch
already cached a House(only address) on the room and the loop must NOT
overwrite it with the outer House(only name).

Holds (exit 0) iff reading room.house.address performs 0 queries.
FAILS at base (overwrite discards the nested prefetch -> extra query).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext


class House(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(House)
    se.create_model(Room)

h = House.objects.create(name="Big house", address="123 Main St")
room = Room.objects.create(name="Kitchen", house=h)

queryset = House.objects.only("name").prefetch_related(
    Prefetch("rooms", queryset=Room.objects.prefetch_related(
        Prefetch("house", queryset=House.objects.only("address")),
    )),
)
house = queryset.first()

fetched_room = list(house.rooms.all())[0]
with CaptureQueriesContext(connection) as ctx:
    _ = fetched_room.house.address
n = len(ctx.captured_queries)
print("queries when reading nested room.house.address:", n)
for q in ctx.captured_queries:
    print("  QUERY:", q["sql"])

if n == 0:
    print("PASS: nested prefetched parent preserved, 0 extra queries")
    raise SystemExit(0)
else:
    print("FAIL: extra query -> nested prefetch was overwritten")
    raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.2 / 1.3 / 3.4 -- the PRESERVED instance is the nested one,
with its OWN field selection (only 'address'), not the outer House(only name).

After the outer prefetch, the cached room.house must be the nested-prefetch
House which loaded only 'address'. Therefore:
  - reading room.house.address -> 0 queries (loaded)
  - reading room.house.name    -> 1 query (deferred by only('address'))
On base (overwrite) room.house is the outer House(only 'name'): name loaded,
address deferred -> the deferred-field pattern is reversed.

Holds iff address loaded (0 q) AND name deferred (>=1 q). Discriminates.
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext

class House(models.Model):
    name = models.CharField(max_length=50); address = models.CharField(max_length=50)
    class Meta: app_label = "contenttypes"
class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta: app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(House); se.create_model(Room)
h = House.objects.create(name="Big house", address="123 Main St")
Room.objects.create(name="Kitchen", house=h)

qs = House.objects.only("name").prefetch_related(
    Prefetch("rooms", queryset=Room.objects.prefetch_related(
        Prefetch("house", queryset=House.objects.only("address")))))
house = qs.first()
room = list(house.rooms.all())[0]

assert Room.house.is_cached(room) is True, "house not cached on room"

with CaptureQueriesContext(connection) as c1:
    _ = room.house.address
n_addr = len(c1.captured_queries)
with CaptureQueriesContext(connection) as c2:
    _ = room.house.name
n_name = len(c2.captured_queries)
print("queries reading address:", n_addr, "| reading name:", n_name)

if n_addr == 0 and n_name >= 1:
    print("PASS: nested instance preserved with only('address') selection")
    raise SystemExit(0)
print("FAIL: field selection is not the nested one (instance was overwritten)")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 / 2.2 / 3.1 / 3.5 -- the ordinary reverse-FK case still
populates the reverse link.

No nested prefetch back to parent: a plain reverse-FK prefetch. Each fetched
child must have its .house cached and point to the correct parent WITHOUT any
extra query. This is the "SHALL keep" regression leg (the branch guarded by
`if not is_cached`).

Holds iff, for every prefetched room, room.house is the right parent and
reading it costs 0 queries. Should hold on BOTH base and patched (regression).
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.test.utils import CaptureQueriesContext

class House(models.Model):
    name = models.CharField(max_length=50); address = models.CharField(max_length=50)
    class Meta: app_label = "contenttypes"
class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta: app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(House); se.create_model(Room)
h1 = House.objects.create(name="H1", address="A1")
h2 = House.objects.create(name="H2", address="A2")
Room.objects.create(name="r1a", house=h1)
Room.objects.create(name="r1b", house=h1)
Room.objects.create(name="r2a", house=h2)

houses = list(House.objects.prefetch_related("rooms").order_by("id"))
expected = {"r1a": h1.id, "r1b": h1.id, "r2a": h2.id}
ok = True
with CaptureQueriesContext(connection) as ctx:
    for house in houses:
        for room in house.rooms.all():
            cached = Room.house.is_cached(room)
            parent = room.house
            print(f"room {room.name}: cached={cached} house.id={parent.id} expect={expected[room.name]}")
            if not cached or parent.id != expected[room.name]:
                ok = False
n = len(ctx.captured_queries)
print("extra queries traversing to parents:", n)
if ok and n == 0:
    print("PASS: reverse link populated correctly with no extra queries")
    raise SystemExit(0)
print("FAIL: reverse link not populated / extra query")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 (reverse one-to-one) -- reverse O2O prefetch still
populates the reverse link on children with no cached forward relation.

Place has a OneToOne to House (reverse accessor). Prefetching the reverse O2O
must cache the forward relation and cost 0 queries to traverse back.
Regression leg: holds on base and patched.
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.test.utils import CaptureQueriesContext

class House(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "contenttypes"
class Deed(models.Model):
    code = models.CharField(max_length=50)
    house = models.OneToOneField(House, on_delete=models.CASCADE, related_name="deed")
    class Meta: app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(House); se.create_model(Deed)
h1 = House.objects.create(name="H1")
h2 = House.objects.create(name="H2")
Deed.objects.create(code="D1", house=h1)
Deed.objects.create(code="D2", house=h2)

# Prefetch the REVERSE one-to-one accessor from House ('deed').
houses = list(House.objects.prefetch_related("deed").order_by("id"))
expect = {"H1": "D1", "H2": "D2"}
ok = True
with CaptureQueriesContext(connection) as ctx:
    for house in houses:
        code = house.deed.code
        print(f"house {house.name}: deed.code={code} expect={expect[house.name]}")
        if code != expect[house.name]:
            ok = False
n = len(ctx.captured_queries)
print("extra queries traversing reverse-o2o:", n)
if ok and n == 0:
    print("PASS: reverse one-to-one prefetched, 0 extra queries")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.3 -- get_prefetch_queryset() still returns the same 6-element
prefetch descriptor (queryset, rel_obj_attr, instance_attr, single-bool,
cache_name, fetched-bool) unchanged in shape and meaning.

Directly invoke RelatedManager.get_prefetch_queryset and assert the tuple
shape/types/values: 6 elements, elements 3 (single) and 5 (fetched) are the
False booleans the reverse-FK case uses, cache_name matches the field's remote
cache name, and rel_obj_attr/instance_attr are callables that align a child's
FK value with a parent's pk.
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection

class House(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "contenttypes"
class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta: app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(House); se.create_model(Room)
h = House.objects.create(name="H1")
Room.objects.create(name="r1", house=h)

mgr = h.rooms
res = mgr.get_prefetch_queryset([h])
print("descriptor length:", len(res))
ok = True
if len(res) != 6:
    ok = False
qs, rel_obj_attr, instance_attr, single, cache_name, fetched = res
print("single flag:", single, "| fetched flag:", fetched, "| cache_name:", cache_name)
expected_cache = Room.house.field.remote_field.get_cache_name()
print("expected cache_name:", expected_cache)
if single is not False or fetched is not False:
    ok = False
if cache_name != expected_cache:
    ok = False
# accessor semantics: rel_obj_attr(room) should equal instance_attr(house)
room = list(qs)[0]
print("rel_obj_attr(room):", rel_obj_attr(room), "| instance_attr(house):", instance_attr(h))
if rel_obj_attr(room) != instance_attr(h):
    ok = False
if ok:
    print("PASS: descriptor shape/meaning preserved")
    raise SystemExit(0)
print("FAIL: descriptor changed")
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.2 / 3.3 -- forward+reverse many-to-many and multi-level
nested chains still prefetch without duplicate queries.

Author <-> Book (M2M). Prefetch books, and nested prefetch each book's authors
back. Assert traversal from author->books->authors performs 0 extra queries and
returns the correct related sets. Regression leg (holds base+patched).
"""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models, connection
from django.test.utils import CaptureQueriesContext

class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label = "contenttypes"
class Book(models.Model):
    title = models.CharField(max_length=50)
    authors = models.ManyToManyField(Author, related_name="books")
    class Meta: app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book)
a1 = Author.objects.create(name="A1")
a2 = Author.objects.create(name="A2")
b1 = Book.objects.create(title="B1"); b1.authors.add(a1, a2)
b2 = Book.objects.create(title="B2"); b2.authors.add(a1)

authors = list(Author.objects.prefetch_related("books__authors").order_by("id"))
ok = True
with CaptureQueriesContext(connection) as ctx:
    got = {}
    for au in authors:
        titles = sorted(b.title for b in au.books.all())
        got[au.name] = titles
        for bk in au.books.all():
            _ = sorted(x.name for x in bk.authors.all())
    print("author->books:", got)
n = len(ctx.captured_queries)
print("extra queries during nested m2m traversal:", n)
if got != {"A1": ["B1", "B2"], "A2": ["B1"]}:
    ok = False
if ok and n == 0:
    print("PASS: nested m2m prefetch, no duplicate queries")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control -- Requirement 1.3 / F2P core behavior.

A House prefetches its rooms; the rooms queryset nests a prefetch back to
house restricted to only('address'). After the outer prefetch, reading
room.house.address must trigger NO extra query, because the nested prefetch
already cached a House(only address) on the room and the loop must NOT
overwrite it with the outer House(only name).

Holds (exit 0) iff reading room.house.address performs 0 queries.
FAILS at base (overwrite discards the nested prefetch -> extra query).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext


class House(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(House)
    se.create_model(Room)

h = House.objects.create(name="Big house", address="123 Main St")
room = Room.objects.create(name="Kitchen", house=h)

queryset = House.objects.only("name").prefetch_related(
    Prefetch("rooms", queryset=Room.objects.prefetch_related(
        Prefetch("house", queryset=House.objects.only("address")),
    )),
)
house = queryset.first()

fetched_room = list(house.rooms.all())[0]
with CaptureQueriesContext(connection) as ctx:
    _ = fetched_room.house.address
n = len(ctx.captured_queries)
print("queries when reading nested room.house.address:", n)
for q in ctx.captured_queries:
    print("  QUERY:", q["sql"])

if n == 0:
    print("PASS: nested prefetched parent preserved, 0 extra queries")
    raise SystemExit(0)
else:
    print("FAIL: extra query -> nested prefetch was overwritten")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15280 (Django 4.1): reverse-FK/O2O prefetch population loop in create_reverse_many_to_one_manager().RelatedManager.get_prefetch_queryset() unconditionally overwrote each child's cached forward relation, discarding a nested prefetch. Gold guards the setattr with `if not self.field.is_cached(rel_obj)`.

Probes (all run in the official image; exit 0 = criterion holds):
- probe_1 (POSITIVE CONTROL, R1.3/F2P): House.only('name').prefetch_related(Prefetch('rooms', Room.prefetch_related(Prefetch('house', House.only('address'))))); reading nested room.house.address must cost 0 queries. PATCHED=HOLDS(0q); BASE=VIOLATED(1q). Discriminates.
- probe_2 (R1.2/1.3/3.4): the preserved instance is the NESTED House(only address) not outer House(only name) -> address loaded(0q) AND name deferred(>=1q). PATCHED=HOLDS(addr 0/name 1). Also discriminates vs base (would be reversed).
- probe_3 (R2.1/2.2/3.1/3.5): plain reverse-FK prefetch still caches reverse link, correct parent, 0 extra queries. PATCHED=HOLDS.
- probe_4 (R3.1): reverse one-to-one prefetch still populates & 0 queries. PATCHED=HOLDS.
- probe_5 (R2.3): get_prefetch_queryset() returns unchanged 6-tuple (len 6, single=False, fetched=False, cache_name==field.remote cache name, rel_obj_attr(child)==instance_attr(parent)). PATCHED=HOLDS.
- probe_6 (R3.2/3.3): nested forward+reverse M2M (books__authors) prefetch, correct sets, 0 duplicate queries. PATCHED=HOLDS.

All 6 probes HOLD on the gold-patched tree.

Wrong-fix candidates (both apply at base_commit, both REJECTED by suite):
- weak_A (drop back-linking entirely — the lazy reading of R1 that just stops overwriting): probe_1/probe_2 pass but probe_3 FAILS (reverse link never populated for the ordinary case, cached=False) -> violates R2.1. Rejected.
- weak_B (guard with `self.field.name not in rel_obj.__dict__` instead of the field's own is_cached): probe_3/probe_5 pass but probe_1 AND probe_2 FAIL (1 extra query; wrong field selection) -> the __dict__ presence test doesn't match the descriptor cache slot that setattr writes to, violating R1.4. Rejected.

Suite discriminates both a too-weak fix (weak_A) and a wrong cache-check (weak_B), and the positive control separates base from patched. No requirements violation found; no probe-conforming alternative patch found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
"""Positive control -- Requirement 1.3 / F2P core behavior.

A House prefetches its rooms; the rooms queryset nests a prefetch back to
house restricted to only('address'). After the outer prefetch, reading
room.house.address must trigger NO extra query, because the nested prefetch
already cached a House(only address) on the room and the loop must NOT
overwrite it with the outer House(only name).

Holds (exit 0) iff reading room.house.address performs 0 queries.
FAILS at base (overwrite discards the nested prefetch -> extra query).
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models, connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext


class House(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    class Meta:
        app_label = "contenttypes"


class Room(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(House)
    se.create_model(Room)

h = House.objects.create(name="Big house", address="123 Main St")
room = Room.objects.create(name="Kitchen", house=h)

queryset = House.objects.only("name").prefetch_related(
    Prefetch("rooms", queryset=Room.objects.prefetch_related(
        Prefetch("house", queryset=House.objects.only("address")),
    )),
)
house = queryset.first()

fetched_room = list(house.rooms.all())[0]
with CaptureQueriesContext(connection) as ctx:
    _ = fetched_room.house.address
n = len(ctx.captured_queries)
print("queries when reading nested room.house.address:", n)
for q in ctx.captured_queries:
    print("  QUERY:", q["sql"])

if n == 0:
    print("PASS: nested prefetched parent preserved, 0 extra queries")
    raise SystemExit(0)
else:
    print("FAIL: extra query -> nested prefetch was overwritten")
    raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15280 (Django 4.1): reverse-FK/O2O prefetch population loop in create_reverse_many_to_one_manager().RelatedManager.get_prefetch_queryset() unconditionally overwrote each child's cached forward relation, discarding a nested prefetch. Gold guards the setattr with `if not self.field.is_cached(rel_obj)`.

Probes (all run in the official image; exit 0 = criterion holds):
- probe_1 (POSITIVE CONTROL, R1.3/F2P): House.only('name').prefetch_related(Prefetch('rooms', Room.prefetch_related(Prefetch('house', House.only('address'))))); reading nested room.house.address must cost 0 queries. PATCHED=HOLDS(0q); BASE=VIOLATED(1q). Discriminates.
- probe_2 (R1.2/1.3/3.4): the preserved instance is the NESTED House(only address) not outer House(only name) -> address loaded(0q) AND name deferred(>=1q). PATCHED=HOLDS(addr 0/name 1). Also discriminates vs base (would be reversed).
- probe_3 (R2.1/2.2/3.1/3.5): plain reverse-FK prefetch still caches reverse link, correct parent, 0 extra queries. PATCHED=HOLDS.
- probe_4 (R3.1): reverse one-to-one prefetch still populates & 0 queries. PATCHED=HOLDS.
- probe_5 (R2.3): get_prefetch_queryset() returns unchanged 6-tuple (len 6, single=False, fetched=False, cache_name==field.remote cache name, rel_obj_attr(child)==instance_attr(parent)). PATCHED=HOLDS.
- probe_6 (R3.2/3.3): nested forward+reverse M2M (books__authors) prefetch, correct sets, 0 duplicate queries. PATCHED=HOLDS.

All 6 probes HOLD on the gold-patched tree.

Wrong-fix candidates (both apply at base_commit, both REJECTED by suite):
- weak_A (drop back-linking entirely — the lazy reading of R1 that just stops overwriting): probe_1/probe_2 pass but probe_3 FAILS (reverse link never populated for the ordinary case, cached=False) -> violates R2.1. Rejected.
- weak_B (guard with `self.field.name not in rel_obj.__dict__` instead of the field's own is_cached): probe_3/probe_5 pass but probe_1 AND probe_2 FAIL (1 extra query; wrong field selection) -> the __dict__ presence test doesn't match the descriptor cache slot that setattr writes to, violating R1.4. Rejected.

Suite discriminates both a too-weak fix (weak_A) and a wrong cache-check (weak_B), and the positive control separates base from patched. No requirements violation found; no probe-conforming alternative patch found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: one hunk in RelatedManager.get_prefetch_queryset (from create_reverse_many_to_one_manager) wrapping the back-link with `if not self.field.is_cached(rel_obj): instance = instances_dict[rel_obj_attr(rel_obj)]; setattr(rel_obj, self.field.name, instance)`. Requirement mapping verified: R1.1/1.4 -> `self.field.is_cached(rel_obj)` (field's own cache-presence check on the same slot setattr writes) - exact; R1.2/1.3 -> skip assignment when cached, preserving nested instance (confirmed by preserved deferred {'email'}); R2.1 -> lookup instances_dict[rel_obj_attr(rel_obj)] + setattr when not cached - exact; R2.2 -> matching by rel_obj_attr/instance_attr correspondence unchanged; R2.3 -> return tuple (queryset, rel_obj_attr, instance_attr, False, cache_name, False) unchanged in shape/meaning - exact. Boundary check: requirements correctly pin RelatedManager / create_reverse_many_to_one_manager (reverse many-to-one), NOT a narrower branch or helper. Potential concern examined and cleared: issue headline uses OneToOneField and reverse-O2O still overwrites (ReverseOneToOneDescriptor.get_prefetch_queryset is unchanged by the patch; O2O probe showed base==patched==1 query). Requirements do NOT claim the fix covers reverse-O2O overwrite; they only reference reverse-one-to-one in R3.1's regression clause ('continue to correctly prefetch ... reverse one-to-one relations, populating the reverse link'), which stays true. No invented/forbidden behavior; modeling boundary is the changed observable behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements name the gold-patch site (related_descriptors.py, create_reverse_many_to_one_manager, RelatedManager.get_prefetch_queryset) and describe the fix mechanism (skip overwriting when the forward relation is already cached via the field's cache-presence check, mirroring `if not self.field.is_cached(rel_obj)`). Both are legitimate: localization is required, `is_cached` is a pre-existing Django API described in prose (not quoted, not fix-invented), and the cached-vs-uncached branching is a behavioral translation. No hidden-test artifacts are transmitted: no test path (tests/prefetch_related/tests.py), no class/method names (NestedPrefetchTests, test_nested_prefetch_is_not_overwritten_by_related_object), no House/Room models, no assertNumQueries counts, no docstring/gold code quotes. The public problem_statement already discloses the nested Prefetch + only()/defer() scenario, the deferred-field/extra-query symptom, and both O2O and FK cases, so the document's examples stay within public bounds. Requirement 3's feature enumeration (m2m/generic/to_attr/only-defer/multi-db) is the standard documented prefetch_related feature surface framed as regression protection, not a reconstruction of the PASS_TO_PASS parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
