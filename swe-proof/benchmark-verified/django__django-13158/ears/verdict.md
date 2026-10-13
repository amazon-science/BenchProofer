# P2 adversarial audit — django__django-13158

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control + Req 1.1: set_empty() on a combined query forces the
# top-level query AND every combined sub-query to select nothing.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'

qs1 = Number.objects.filter(num__lte=1)
qs2 = Number.objects.filter(num__gte=8)
qs3 = qs1.union(qs2)
q = qs3.query
print("combined_queries len:", len(q.combined_queries))
q.set_empty()
top_empty = q.is_empty()
subs_empty = [sub.is_empty() for sub in q.combined_queries]
print("top is_empty:", top_empty)
print("sub is_empty:", subs_empty)
ok = top_empty and len(subs_empty) == 2 and all(subs_empty)
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 + 3.4: .none() on a union() queryset returns zero rows end-to-end;
# count() reflects it. Also checks the non-emptied union still returns rows.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models, connection
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
with connection.schema_editor() as se:
    se.create_model(Number)
Number.objects.bulk_create([Number(num=i) for i in range(10)])

qs1 = Number.objects.filter(num__lte=1)   # 0,1
qs2 = Number.objects.filter(num__gte=8)   # 8,9
qs3 = qs1.union(qs2)
noned = list(qs3.none())
full = sorted(Number.objects.filter(num__in=[o.num for o in qs3]).values_list('num', flat=True))
full_direct = sorted(o.num for o in qs3)
none_count = qs3.none().count()
print("none() rows:", [o.num for o in noned])
print("none() count:", none_count)
print("full union rows:", full_direct)
ok = (noned == []) and (none_count == 0) and (full_direct == [0,1,8,9])
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2/2.3: clone() gives independent copies of combined sub-queries;
# emptying the clone does NOT affect the source's sub-queries, and vice versa.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'

q = Number.objects.filter(num__lte=1).union(Number.objects.filter(num__gte=8)).query
clone = q.clone()
# 2.2 same length
print("src len", len(q.combined_queries), "clone len", len(clone.combined_queries))
# 2.1 not the same objects
distinct_objs = all(a is not b for a, b in zip(q.combined_queries, clone.combined_queries))
print("distinct sub-query objects:", distinct_objs)
# 2.3 empty the clone; source subs must remain non-empty
clone.set_empty()
src_subs_empty = [s.is_empty() for s in q.combined_queries]
clone_subs_empty = [s.is_empty() for s in clone.combined_queries]
print("source subs is_empty:", src_subs_empty)
print("clone subs is_empty:", clone_subs_empty)
ok = (len(q.combined_queries) == len(clone.combined_queries) == 2
      and distinct_objs
      and src_subs_empty == [False, False]
      and clone_subs_empty == [True, True])
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.4 + 3.7: clone() of a NON-combined query -> empty combined_queries;
# set_empty() on a non-combined query only empties the top (no subs), and a
# clone of a non-combined query still returns its rows (set_empty unchanged).
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models, connection
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
with connection.schema_editor() as se:
    se.create_model(Number)
Number.objects.bulk_create([Number(num=i) for i in range(5)])

q = Number.objects.filter(num__gte=0).query
clone = q.clone()
print("non-combined clone combined_queries:", clone.combined_queries)
empty_after_clone = (len(clone.combined_queries) == 0)
# set_empty on non-combined
q2 = Number.objects.all().query
q2.set_empty()
print("non-combined set_empty is_empty:", q2.is_empty(), "subs:", len(q2.combined_queries))
top_only = q2.is_empty() and len(q2.combined_queries) == 0
# simple none() returns empty (Req 3.1)
simple_none = list(Number.objects.all().none())
print("simple none rows:", [o.num for o in simple_none])
ok = empty_after_clone and top_only and simple_none == []
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.2/3.3: union/union(all=True)/intersection/difference semantics
# preserved (non-emptied), and union with an empty operand yields the
# non-empty operand's rows.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models, connection
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
with connection.schema_editor() as se:
    se.create_model(Number)
Number.objects.bulk_create([Number(num=i) for i in range(10)])

a = Number.objects.filter(num__lte=4)   # 0..4
b = Number.objects.filter(num__gte=3)   # 3..9
union = sorted(o.num for o in a.union(b))
union_all = sorted(o.num for o in a.union(b, all=True))
inter = sorted(o.num for o in a.intersection(b))
diff = sorted(o.num for o in a.difference(b))
# union with empty operand
union_empty = sorted(o.num for o in a.union(Number.objects.none()))
print("union:", union)
print("union_all len:", len(union_all))
print("intersection:", inter)
print("difference:", diff)
print("union with empty:", union_empty)
ok = (union == list(range(10))
      and len(union_all) == 12   # 5 + 7
      and inter == [3, 4]
      and diff == [0, 1, 2]
      and union_empty == [0,1,2,3,4])
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req 1.1: set_empty() on a combined query forces the
# top-level query AND every combined sub-query to select nothing.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'

qs1 = Number.objects.filter(num__lte=1)
qs2 = Number.objects.filter(num__gte=8)
qs3 = qs1.union(qs2)
q = qs3.query
print("combined_queries len:", len(q.combined_queries))
q.set_empty()
top_empty = q.is_empty()
subs_empty = [sub.is_empty() for sub in q.combined_queries]
print("top is_empty:", top_empty)
print("sub is_empty:", subs_empty)
ok = top_empty and len(subs_empty) == 2 and all(subs_empty)
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes (all HOLD on gold-patched tree; run in official image):
- probe_1 (Req 1.1, POSITIVE CONTROL): Query.set_empty() on a union() query forces top-level is_empty() AND both combined sub-queries is_empty(). HOLDS patched (sub is_empty [True,True]); FAILS at base (subs [False,False]) => discriminating power confirmed.
- probe_2 (Req 1.2 + 3.4): .none() on a union() qs returns [] end-to-end and count()==0, while the un-emptied union returns [0,1,8,9]. HOLDS patched.
- probe_3 (Req 2.1/2.2/2.3): clone() yields same-length, DISTINCT sub-query objects; emptying the clone leaves the source's subs non-empty. HOLDS patched.
- probe_4 (Req 2.4 + 3.7 + 3.1): clone() of a non-combined query has empty combined_queries; set_empty() on non-combined only empties top (no subs); simple none() returns []. HOLDS patched.
- probe_5 (Req 3.2/3.3): union=[0..9], union(all=True) len 12, intersection=[3,4], difference=[0,1,2], union-with-empty=[0,1,2,3,4]. HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite):
- weak_setempty_only (recurse set_empty but do NOT clone combined_queries): probe_3 VIOLATED (clone shares sub-query objects; emptying clone leaks into source) and probe_2 fails via shared-object leak. Suite discriminates.
- weak_cloneonly (clone combined_queries but do NOT recurse set_empty): probe_1 & probe_2 VIOLATED (none() on union still returns [0,1,8,9]). Suite discriminates.

Gold patch (both set_empty recursion + clone independence) satisfies all 5 probes; each partial fix — the lazy readings a weak spec would permit — is rejected. Requirements are faithful and not too weak. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req 1.1: set_empty() on a combined query forces the
# top-level query AND every combined sub-query to select nothing.
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
django.setup()
from django.db import models
class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'

qs1 = Number.objects.filter(num__lte=1)
qs2 = Number.objects.filter(num__gte=8)
qs3 = qs1.union(qs2)
q = qs3.query
print("combined_queries len:", len(q.combined_queries))
q.set_empty()
top_empty = q.is_empty()
subs_empty = [sub.is_empty() for sub in q.combined_queries]
print("top is_empty:", top_empty)
print("sub is_empty:", subs_empty)
ok = top_empty and len(subs_empty) == 2 and all(subs_empty)
print("CRITERION HOLDS" if ok else "CRITERION VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes (all HOLD on gold-patched tree; run in official image):
- probe_1 (Req 1.1, POSITIVE CONTROL): Query.set_empty() on a union() query forces top-level is_empty() AND both combined sub-queries is_empty(). HOLDS patched (sub is_empty [True,True]); FAILS at base (subs [False,False]) => discriminating power confirmed.
- probe_2 (Req 1.2 + 3.4): .none() on a union() qs returns [] end-to-end and count()==0, while the un-emptied union returns [0,1,8,9]. HOLDS patched.
- probe_3 (Req 2.1/2.2/2.3): clone() yields same-length, DISTINCT sub-query objects; emptying the clone leaves the source's subs non-empty. HOLDS patched.
- probe_4 (Req 2.4 + 3.7 + 3.1): clone() of a non-combined query has empty combined_queries; set_empty() on non-combined only empties top (no subs); simple none() returns []. HOLDS patched.
- probe_5 (Req 3.2/3.3): union=[0..9], union(all=True) len 12, intersection=[3,4], difference=[0,1,2], union-with-empty=[0,1,2,3,4]. HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite):
- weak_setempty_only (recurse set_empty but do NOT clone combined_queries): probe_3 VIOLATED (clone shares sub-query objects; emptying clone leaks into source) and probe_2 fails via shared-object leak. Suite discriminates.
- weak_cloneonly (clone combined_queries but do NOT recurse set_empty): probe_1 & probe_2 VIOLATED (none() on union still returns [0,1,8,9]). Suite discriminates.

Gold patch (both set_empty recursion + clone independence) satisfies all 5 probes; each partial fix — the lazy readings a weak spec would permit — is rejected. Requirements are faithful and not too weak. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch has exactly two hunks: (a) clone() adds obj.combined_queries = tuple(query.clone() for query in self.combined_queries) — independent clones (Req 2.1/2.3/2.4); (b) set_empty() adds a loop `for query in self.combined_queries: query.set_empty()` after adding NothingNode to the top where — recursive emptying of the whole tree (Req 1.1/1.3). Req 1.2 (observable empty result on union/intersection/difference) is the changed observable behavior and is the correct modeling boundary; verified live. Req 3 clauses only assert preservation of pre-existing union/intersection/difference/count/ordering behavior and non-combined set_empty (Req 3.7 correctly notes no recursion when combined_queries is empty). No requirement mandates behavior the patch lacks, forbids behavior it has, or invents behavior. Recursion (Req 1.3) is directly realized by the recursive set_empty call and confirmed via a nested-query probe.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements name only pre-existing symbols to localize the change (Query.set_empty(), Query.clone(), combined_queries, NothingNode, where clause, file django/db/models/sql/query.py) — legitimate localization, none fix-invented. Requirements 1-2 translate the two gold edits (recursive set_empty over combined sub-queries; clone producing independent copies of combined_queries) into behavioral obligations, which is the intended translation, not a transcription of gold code. The hidden F2P test's concrete inputs/values (num__lte=1, num__gte=8, expected [0,1,8,9], the name test_union_none, the test file path) are NOT present. Requirement 3's regression enumeration loosely tracks the PASS_TO_PASS method set (count/ordering-by-alias/f-expression/subcompound/values/extra/unsupported ops), which is the closest thing to a test-shaped enumeration; but each item describes publicly-documented behavior of Django's union()/intersection()/difference() API, derivable from source without the hidden tests, and no test names/ids/code are quoted. Conclusion: no test names, paths, parametrization ids, quoted test/gold code, fix-invented identifiers, or case-value enumerations leak beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
