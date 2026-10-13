# P2 adversarial audit — django__django-12050

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control + Req1.4: build_where(Q(name=['a','b'])) -> Exact.rhs == str of a LIST.
# base coerces list->tuple so rhs=="('a', 'b')" (FAIL); patched keeps list -> "['a', 'b']" (HOLD).
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query
from django.db.models import Q
from django.db.models.lookups import Exact

q = Query(Item)
where = q.build_where(Q(name=['a', 'b']))
node = where.children[0]
print("node type:", type(node).__name__, "rhs:", repr(node.rhs))
assert isinstance(node, Exact), "expected Exact lookup, got %r" % type(node)
assert node.rhs == "['a', 'b']", "rhs must be str of list, got %r" % (node.rhs,)
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1 & 1.3 & 2.1/2.2/2.5: resolve_lookup_value(list of scalars) returns a list, same values/order.
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query

q = Query(Item)
out = q.resolve_lookup_value(['a', 'b', 'c'], can_reuse=set(), allow_joins=True, simple_col=False)
print("in=list -> out:", repr(out), type(out).__name__)
assert type(out) is list, "list input must resolve to a list, got %r" % type(out)
assert out == ['a', 'b', 'c'], "value/order/arity mismatch: %r" % (out,)
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.2 & 2.2: resolve_lookup_value(tuple) returns a tuple, preserving arity/order.
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query

q = Query(Item)
out = q.resolve_lookup_value(('x', 'y'), can_reuse=set(), allow_joins=True, simple_col=False)
print("in=tuple -> out:", repr(out), type(out).__name__)
assert type(out) is tuple, "tuple input must resolve to a tuple, got %r" % type(out)
assert out == ('x', 'y'), "value/order/arity mismatch: %r" % (out,)
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.3/2.4/2.5: F element inside a collection resolved; scalar passes through; list stays list.
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query
from django.db.models import F

q = Query(Item)
q.get_initial_alias()
out = q.resolve_lookup_value([F('num'), 'plain'], can_reuse=set(), allow_joins=True, simple_col=True)
print("out:", repr(out), type(out).__name__)
assert type(out) is list, "container must stay list, got %r" % type(out)
assert len(out) == 2, "arity mismatch: %r" % (out,)
assert not isinstance(out[0], F), "F element should be resolved, still F: %r" % (out[0],)
assert hasattr(out[0], 'as_sql'), "resolved F should be a compilable expression: %r" % (out[0],)
assert out[1] == 'plain', "scalar element changed: %r" % (out[1],)
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.6: nested collection resolves recursively preserving its OWN container type/arity/order.
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query

q = Query(Item)
val = [('a', 'b'), ['c', 'd'], 'e']
out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True, simple_col=False)
print("out:", repr(out))
assert type(out) is list, "outer must stay list, got %r" % type(out)
assert type(out[0]) is tuple, "inner tuple must stay tuple, got %r" % type(out[0])
assert type(out[1]) is list, "inner list must stay list, got %r" % type(out[1])
assert out == [('a', 'b'), ['c', 'd'], 'e'], "value/order/arity mismatch: %r" % (out,)
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3.1/3.2/3.3/3.4: non-collection values handled as before: scalar unchanged; F resolved.
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query
from django.db.models import F

q = Query(Item)
q.get_initial_alias()
s = "hello"
out_s = q.resolve_lookup_value(s, can_reuse=set(), allow_joins=True, simple_col=False)
print("scalar:", repr(out_s))
assert out_s is s, "scalar must be returned unchanged (identity)"
out_i = q.resolve_lookup_value(42, can_reuse=set(), allow_joins=True, simple_col=False)
assert out_i == 42 and type(out_i) is int, "int scalar changed: %r" % (out_i,)
out_f = q.resolve_lookup_value(F('num'), can_reuse=set(), allow_joins=True, simple_col=True)
print("F ->", repr(out_f))
assert not isinstance(out_f, F), "F must be resolved"
assert hasattr(out_f, 'as_sql'), "resolved F must be compilable"
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req1.4: build_where(Q(name=['a','b'])) -> Exact.rhs == str of a LIST.
# base coerces list->tuple so rhs=="('a', 'b')" (FAIL); patched keeps list -> "['a', 'b']" (HOLD).
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query
from django.db.models import Q
from django.db.models.lookups import Exact

q = Query(Item)
where = q.build_where(Q(name=['a', 'b']))
node = where.children[0]
print("node type:", type(node).__name__, "rhs:", repr(node.rhs))
assert isinstance(node, Exact), "expected Exact lookup, got %r" % type(node)
assert node.rhs == "['a', 'b']", "rhs must be str of list, got %r" % (node.rhs,)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

django__django-12050: resolve_lookup_value must preserve caller's container type (list->list, tuple->tuple) while resolving each element independently.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (Req1.4, POSITIVE CONTROL): build_where(Q(name=['a','b'])) -> Exact.rhs == "['a', 'b']" (str of a list). PATCHED: HOLDS. BASE: VIOLATED (rhs=="('a', 'b')" — list coerced to tuple). Discriminates base vs patched.
- probe_2 (Req1.1/1.3/2.x): resolve_lookup_value(['a','b','c']) returns a list with same values/order. PATCHED HOLDS; BASE VIOLATED (returns tuple).
- probe_3 (Req1.2/2.2): resolve_lookup_value(('x','y')) returns a tuple. PATCHED HOLDS; BASE HOLDS (regression criterion — tuple was already tuple at base).
- probe_4 (Req2.3/2.4/2.5): [F('num'),'plain'] -> list; F resolved to SimpleCol (compilable), scalar unchanged. PATCHED HOLDS; BASE VIOLATED (list->tuple).
- probe_5 (Req2.6): nested [('a','b'),['c','d'],'e'] preserves outer list, inner tuple, inner list. PATCHED HOLDS; BASE VIOLATED (all coerced to tuple).
- probe_6 (Req3.1/3.2/3.3/3.4): scalar returned unchanged (identity), int unchanged, top-level F resolved. PATCHED HOLDS; BASE HOLDS (regression criterion, non-collection branch unchanged).

Wrong-fix candidate (coerce_to_list / weak.diff): replaces the branch with `return list(self.resolve_lookup_value(sub) for sub in value)` — always coerces to list. A weak reading of Req1 ("preserve list-ness") would permit it, but it violates Req1.2/2.6. REJECTED by probe_3 (tuple->list, exit 1) and probe_5 (inner tuple->list, exit 1). Demonstrates the suite discriminates wrong implementations that don't resolve the F2P test. probes 1,2,4,6 still hold under it.

All runs completed in the official Docker image. 6/6 probes hold patched; positive control fails at base (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND. (Note: meta.json shows G-PANEL-3 fail on a leakage concern re Req3-style regression enumeration, but that is a separate leakage judgment; the requirements as encoded here are faithful and discriminating for G-EQ.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Positive control + Req1.4: build_where(Q(name=['a','b'])) -> Exact.rhs == str of a LIST.
# base coerces list->tuple so rhs=="('a', 'b')" (FAIL); patched keeps list -> "['a', 'b']" (HOLD).
import os, sys, tempfile, django
from django.conf import settings
_appdir = tempfile.mkdtemp(prefix="probeapp_")
_pkg = os.path.join(_appdir, "probeapp"); os.makedirs(_pkg, exist_ok=True)
open(os.path.join(_pkg, "__init__.py"), "w").close()
with open(os.path.join(_pkg, "models.py"), "w") as f:
    f.write("from django.db import models\n"
            "class Item(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
            "    num = models.IntegerField(default=0)\n")
sys.path.insert(0, _appdir)
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from probeapp.models import Item
from django.db.models.sql.query import Query
from django.db.models import Q
from django.db.models.lookups import Exact

q = Query(Item)
where = q.build_where(Q(name=['a', 'b']))
node = where.children[0]
print("node type:", type(node).__name__, "rhs:", repr(node.rhs))
assert isinstance(node, Exact), "expected Exact lookup, got %r" % type(node)
assert node.rhs == "['a', 'b']", "rhs must be str of list, got %r" % (node.rhs,)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

django__django-12050: resolve_lookup_value must preserve caller's container type (list->list, tuple->tuple) while resolving each element independently.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (Req1.4, POSITIVE CONTROL): build_where(Q(name=['a','b'])) -> Exact.rhs == "['a', 'b']" (str of a list). PATCHED: HOLDS. BASE: VIOLATED (rhs=="('a', 'b')" — list coerced to tuple). Discriminates base vs patched.
- probe_2 (Req1.1/1.3/2.x): resolve_lookup_value(['a','b','c']) returns a list with same values/order. PATCHED HOLDS; BASE VIOLATED (returns tuple).
- probe_3 (Req1.2/2.2): resolve_lookup_value(('x','y')) returns a tuple. PATCHED HOLDS; BASE HOLDS (regression criterion — tuple was already tuple at base).
- probe_4 (Req2.3/2.4/2.5): [F('num'),'plain'] -> list; F resolved to SimpleCol (compilable), scalar unchanged. PATCHED HOLDS; BASE VIOLATED (list->tuple).
- probe_5 (Req2.6): nested [('a','b'),['c','d'],'e'] preserves outer list, inner tuple, inner list. PATCHED HOLDS; BASE VIOLATED (all coerced to tuple).
- probe_6 (Req3.1/3.2/3.3/3.4): scalar returned unchanged (identity), int unchanged, top-level F resolved. PATCHED HOLDS; BASE HOLDS (regression criterion, non-collection branch unchanged).

Wrong-fix candidate (coerce_to_list / weak.diff): replaces the branch with `return list(self.resolve_lookup_value(sub) for sub in value)` — always coerces to list. A weak reading of Req1 ("preserve list-ness") would permit it, but it violates Req1.2/2.6. REJECTED by probe_3 (tuple->list, exit 1) and probe_5 (inner tuple->list, exit 1). Demonstrates the suite discriminates wrong implementations that don't resolve the F2P test. probes 1,2,4,6 still hold under it.

All runs completed in the official Docker image. 6/6 probes hold patched; positive control fails at base (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND. (Note: meta.json shows G-PANEL-3 fail on a leakage concern re Req3-style regression enumeration, but that is a separate leakage judgment; the requirements as encoded here are faithful and discriminating for G-EQ.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces the manual per-element resolver that always coerced to tuple with `return type(value)(self.resolve_lookup_value(sub, ...) for sub in value)`. This is a faithful recursive re-expression: container type preserved (Req1), element-wise/arity/order preserved and expression+F(simple_col) handling delegated to the same method so nested collections recurse (Req2), and non-collection branches (expression/F/scalar) are untouched so Req3's 'confine to collection branch' holds. Probes: patched HOLDS (exit 0), base VIOLATED (list resolved to tuple). Requirements pin the changed observable behavior, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally (preserve container type of list/tuple collection lookup values; resolve each element independently; recurse into nested collections) and localize it to Query.resolve_lookup_value in django/db/models/sql/query.py. The list->tuple coercion, 'exact value queries', and PickledField-style type sensitivity are all already public in the problem_statement (#30687). Identifiers named (resolve_expression, F, simple_col, resolve_lookup_value) are pre-existing signature/API elements needed for localization, not fix-invented. The gold's `type(value)(...)` recursive rewrite is captured only as behavior (Req 2.6 nested recursion), not quoted. No test path (tests/queries/test_query.py), test/class name (TestQuery/test_iterable_lookup_value), parametrization ids, or verbatim test/gold lines appear. Req 1.4 is the closest to the F2P test but leaks none of the test's specifics — not the ['a','b'] values, not the Exact class, and not the quirk that rhs is compared as a string repr "['a', 'b']". It is a legitimate behavioral translation of what the test verifies.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
