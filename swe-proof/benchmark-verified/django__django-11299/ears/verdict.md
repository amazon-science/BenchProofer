# P2 adversarial audit — django__django-11299

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

q = Q(num__gt=2, name__isnull=False) | Q(num__lt=F("id"))
where = Query(Author).build_where(q)
andgrp = where.children[0]
print("and-group children types:", [type(c).__name__ for c in andgrp.children])
lhs_types = [type(c.lhs).__name__ for c in andgrp.children]
print("nested AND-group leaf lhs types:", lhs_types)
ok = all(isinstance(c.lhs, SimpleCol) for c in andgrp.children)
print("all nested AND leaves SimpleCol:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

q = Q(num__gt=2, name__isnull=False) | Q(num__lt=F("id"))
where = Query(Author).build_where(q)
num_lt = where.children[1]
print("top-level OR term:", type(num_lt).__name__, "lhs:", type(num_lt.lhs).__name__, "rhs:", type(num_lt.rhs).__name__)
ok = isinstance(num_lt.lhs, SimpleCol) and isinstance(num_lt.rhs, SimpleCol)
print("both operands (lhs field & rhs F-ref) SimpleCol:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

def walk(node):
    from django.db.models.sql.where import WhereNode
    for c in node.children:
        if isinstance(c, WhereNode):
            yield from walk(c)
        else:
            for side in ("lhs","rhs"):
                v=getattr(c,side,None)
                if isinstance(v,(SimpleCol,Col)):
                    yield (side, type(v).__name__)
q = Q(num__gt=2, name__isnull=False) | Q(num__lt=F("id"))
where = Query(Author).build_where(q)
cols = list(walk(where))
print("all column refs in tree:", cols)
has_col = any(t=="Col" for _,t in cols)
all_simple = cols and not has_col
print("no qualified Col anywhere, at least one col ref:", all_simple)
import sys; sys.exit(0 if all_simple else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

query = Query(Author)
# default simple_col=False path
clause, _ = query._add_q(Q(num__gt=2), used_aliases=set(), allow_joins=True)
leaf = clause.children[0]
print("default-form leaf lhs type:", type(leaf.lhs).__name__)
ok = isinstance(leaf.lhs, Col) and not isinstance(leaf.lhs, SimpleCol)
print("default form yields table-qualified Col:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

q = Q(num__gt=2) | Q(num__lt=0)
where = Query(Author).build_where(q)
print("connector:", where.connector, "n children:", len(where.children))
types=[type(c).__name__ for c in where.children]
print("children:", types)
lhs_ok = all(isinstance(c.lhs, SimpleCol) for c in where.children)
struct_ok = where.connector=="OR" and len(where.children)==2 and isinstance(where.children[0],GreaterThan) and isinstance(where.children[1],LessThan)
print("structure preserved:", struct_ok, "lhs all SimpleCol:", lhs_ok)
import sys; sys.exit(0 if (struct_ok and lhs_ok) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

# simple single clause (Req 4.1)
w1 = Query(Author).build_where(Q(num__gt=2))
leaf = w1.children[0]
print("single clause:", type(leaf).__name__, "rhs=", leaf.rhs, "lhs.target=", leaf.lhs.target.name)
single_ok = isinstance(leaf, GreaterThan) and leaf.rhs==2 and leaf.lhs.target == Author._meta.get_field("num") and isinstance(leaf.lhs, SimpleCol)
# deep nesting: OR( AND( num>2, OR(name isnull, num<5) ), num<0 )
q = Q(num__gt=2) & (Q(name__isnull=False) | Q(num__lt=5)) | Q(num__lt=0)
where = Query(Author).build_where(q)
from django.db.models.sql.where import WhereNode
def deepest(node, d=0):
    res=[]
    for c in node.children:
        if isinstance(c, WhereNode):
            res+=deepest(c, d+1)
        else:
            res.append((d, type(getattr(c,"lhs",None)).__name__))
    return res
leaves=deepest(where)
print("leaf depths/lhs types:", leaves)
maxd=max(d for d,_ in leaves)
deep_ok = maxd>=2 and all(t=="SimpleCol" for _,t in leaves)
print("single_ok:",single_ok,"deep leaves all SimpleCol (maxdepth %d):"%maxd, deep_ok)
import sys; sys.exit(0 if (single_ok and deep_ok) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

from django.db.models.sql.where import WhereNode
query = Query(Author)
# nested mixed Q, default simple_col=False (ordinary query building)
q = Q(num__gt=2, name__isnull=False) | Q(num__lt=0)
clause, _ = query._add_q(q, used_aliases=set(), allow_joins=True)
def walk(node):
    for c in node.children:
        if isinstance(c, WhereNode):
            yield from walk(c)
        else:
            v=getattr(c,"lhs",None)
            if isinstance(v,(SimpleCol,Col)):
                yield type(v).__name__
types=list(walk(clause))
print("default-form nested leaf lhs types:", types)
# default form: NONE should be SimpleCol; all plain Col
ok = types and all(t=="Col" for t in types)
print("all leaves table-qualified Col under default form:", ok)
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

q = Q(num__gt=2, name__isnull=False) | Q(num__lt=F("id"))
where = Query(Author).build_where(q)
andgrp = where.children[0]
print("and-group children types:", [type(c).__name__ for c in andgrp.children])
lhs_types = [type(c.lhs).__name__ for c in andgrp.children]
print("nested AND-group leaf lhs types:", lhs_types)
ok = all(isinstance(c.lhs, SimpleCol) for c in andgrp.children)
print("all nested AND leaves SimpleCol:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11299: gold forwards the simple_col column-form flag into the recursive _add_q call on nested Q/Node children (query.py:1338-1340). All 7 probes HOLD on the gold-patched tree.

Probes (criterion -> patched / base):
- probe_1 (Req 1.2, 2.1 nested AND-group leaf lhs = SimpleCol) POSITIVE CONTROL: HOLDS patched / VIOLATED base (nested leaves are Col). Discriminates.
- probe_2 (Req 2.3 top-level OR term, both lhs field and rhs F() ref = SimpleCol): HOLDS patched / HOLDS base (top-level leaves were already bare pre-fix; non-discriminating but a real criterion).
- probe_3 (Req 1.3, 3.3 uniformity: NO qualified Col anywhere in tree): HOLDS patched / VIOLATED base (two Col at depth 1). Discriminates.
- probe_4 (Req 4.3 default form yields table-qualified Col): HOLDS both.
- probe_5 (Req 4.2 top-level OR of two simple comparisons: structure + SimpleCol leaves preserved): HOLDS both (regression).
- probe_6 (Req 4.1 single-clause lowering + Req 1.2 depth>=2 leaves all SimpleCol): HOLDS patched / VIOLATED base (depth-1/2 leaves Col). Discriminates.
- probe_7 (Req 4.3/4.4 nested Q under DEFAULT non-simple form -> all leaves table-qualified Col): HOLDS both patched and base (regression guard against over-forwarding simple_col).

Candidate wrong patches, both apply at base and are REJECTED by the suite:
- weak_typo.diff (forwards branch_negated instead of simple_col into recursion): REJECTED by probes 1,3,6 (nested leaves become Col since branch_negated is False here) — behaves like base for this shape; would not resolve the F2P test.
- hardcode_true.diff (recursion always simple_col=True): passes the fix probes but REJECTED by regression probe_7 (nested leaves become SimpleCol even under default query building), which breaks ordinary query construction and PASS_TO_PASS behavior.

Suite discriminates wrong implementations in both directions (too-weak/typo and too-strong/hardcode). No requirements-conforming alternative found that fails the hidden tests. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.db.models import Q, F
from django.db.models.expressions import SimpleCol, Col
from django.db.models.sql.query import Query
from django.db.models.lookups import GreaterThan, LessThan, IsNull
class Author(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=100)
    class Meta:
        app_label = "auth"

q = Q(num__gt=2, name__isnull=False) | Q(num__lt=F("id"))
where = Query(Author).build_where(q)
andgrp = where.children[0]
print("and-group children types:", [type(c).__name__ for c in andgrp.children])
lhs_types = [type(c.lhs).__name__ for c in andgrp.children]
print("nested AND-group leaf lhs types:", lhs_types)
ok = all(isinstance(c.lhs, SimpleCol) for c in andgrp.children)
print("all nested AND leaves SimpleCol:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11299: gold forwards the simple_col column-form flag into the recursive _add_q call on nested Q/Node children (query.py:1338-1340). All 7 probes HOLD on the gold-patched tree.

Probes (criterion -> patched / base):
- probe_1 (Req 1.2, 2.1 nested AND-group leaf lhs = SimpleCol) POSITIVE CONTROL: HOLDS patched / VIOLATED base (nested leaves are Col). Discriminates.
- probe_2 (Req 2.3 top-level OR term, both lhs field and rhs F() ref = SimpleCol): HOLDS patched / HOLDS base (top-level leaves were already bare pre-fix; non-discriminating but a real criterion).
- probe_3 (Req 1.3, 3.3 uniformity: NO qualified Col anywhere in tree): HOLDS patched / VIOLATED base (two Col at depth 1). Discriminates.
- probe_4 (Req 4.3 default form yields table-qualified Col): HOLDS both.
- probe_5 (Req 4.2 top-level OR of two simple comparisons: structure + SimpleCol leaves preserved): HOLDS both (regression).
- probe_6 (Req 4.1 single-clause lowering + Req 1.2 depth>=2 leaves all SimpleCol): HOLDS patched / VIOLATED base (depth-1/2 leaves Col). Discriminates.
- probe_7 (Req 4.3/4.4 nested Q under DEFAULT non-simple form -> all leaves table-qualified Col): HOLDS both patched and base (regression guard against over-forwarding simple_col).

Candidate wrong patches, both apply at base and are REJECTED by the suite:
- weak_typo.diff (forwards branch_negated instead of simple_col into recursion): REJECTED by probes 1,3,6 (nested leaves become Col since branch_negated is False here) — behaves like base for this shape; would not resolve the F2P test.
- hardcode_true.diff (recursion always simple_col=True): passes the fix probes but REJECTED by regression probe_7 (nested leaves become SimpleCol even under default query building), which breaks ordinary query construction and PASS_TO_PASS behavior.

Suite discriminates wrong implementations in both directions (too-weak/typo and too-strong/hardcode). No requirements-conforming alternative found that fails the hidden tests. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement boundary matches the F2P test test_simplecol_query verbatim (asserts SimpleCol for both nested-AND lhs, top OR lhs, and F() rhs) and the issue's OR/AND CheckConstraint scenario. Req 3 (constraint enforcement/bare-column SQL) and Req 4 (regression protection: single clause, top-level OR, default table-qualified form, FK/negated cases, migration ops) correspond to the migrations test_add_or_constraint F2P and PASS_TO_PASS coverage; they describe genuine consequences of the fix without over- or under-constraining. No invented behavior, no wrong boundary, no forbidden/mandated behavior absent from the patch. Probe: gold-patched HOLDS (exit 0), base VIOLATED at nested num_gt.lhs.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to real, pre-existing symbols (Query._add_q, build_where, build_filter, resolve_lookup_value, _get_col, the simple_col flag, SimpleCol/Col) — all legitimate and public-ish; the gold patch invents NO new identifier (it merely forwards the existing simple_col into the recursive _add_q call), so there is no fix-invented identifier to leak. No test names, file paths, parametrization ids, or test/gold field names (num/name/pink/weight/field_1/flag/id) appear anywhere. Requirement 2 (mixed inner-AND / OR-term shape) and Requirement 3 (constraint accept/reject) are direct behavioral translations of the publicly-described CheckConstraint-with-OR defect in the problem_statement. R2.3's statement that a right-hand field reference is also rendered as SimpleCol extends slightly past the problem_statement (which discusses only LHS columns) and matches the hidden test_simplecol_query rhs=F('id') assertion, but it is a faithful behavioral description of the fix's effect, not a transmission of the test. R4.4/R4.5 enumerate regression categories (foreign keys, multiple fields, negated nullable, partial unique, percent-escaped) that loosely echo PASS_TO_PASS method names, but they are generic ORM-feature/behavioral descriptions, not verbatim names, ids, or parametrized-case enumerations — the closest call, still within legitimate 'describe behavior to protect against regression.' Conclusion: behavioral translation + legitimate localization only; no reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
