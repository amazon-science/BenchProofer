# P2 adversarial audit — django__django-12858

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
"""Positive control / Req1 AC1: local field followed by a registered lookup
('test__isnull') SHALL NOT emit models.E015. Holds patched, fails at base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Model(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('test__isnull',)


errs = Model.check()
e015 = [e for e in errs if e.id == 'models.E015']
print("errors:", errs)
print("E015 count:", len(e015))
sys.exit(0 if len(e015) == 0 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 AC2: relation-spanning entry whose final segment is a registered
lookup of the last resolved field SHALL NOT emit models.E015.
Uses parent__test__isnull (FK traversal then lookup)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Parent(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class Meta:
        app_label = 'probeapp'
        ordering = ('parent__test__isnull',)


errs = Child.check()
e015 = [e for e in errs if e.id == 'models.E015']
print("errors:", errs)
print("E015 count:", len(e015))
sys.exit(0 if len(e015) == 0 else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 AC1: a registered TRANSFORM as final segment SHALL NOT emit E015
(preserved). Register Lower transform on CharField and order by test__lower.
Note: 'lower' is a transform, not a lookup — must still pass."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models
from django.db.models.functions import Lower
from django.test.utils import register_lookup


class Model(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('test__lower',)


with register_lookup(models.CharField, Lower):
    errs = Model.check()

e015 = [e for e in errs if e.id == 'models.E015']
print("errors:", errs)
print("E015 count:", len(e015))
sys.exit(0 if len(e015) == 0 else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3 AC1/AC2: genuinely nonexistent final segment (neither field, transform,
nor lookup) MUST still emit E015; and a first segment that names nothing MUST
emit E015."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Model(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('test__nonexistent_thing',)


class Model2(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('firstsegdoesnotexist',)


e1 = [e for e in Model.check() if e.id == 'models.E015']
e2 = [e for e in Model2.check() if e.id == 'models.E015']
print("bad-lookup E015:", e1)
print("bad-first-seg E015:", e2)
ok = len(e1) == 1 and len(e2) == 1
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 AC3/AC4: relation-spanning entry whose INTERMEDIATE segment is invalid
must still emit E015 (parent__nofield__isnull); and referencing a field on a
non-relational field as if it were a relation (test__isnull__x) must emit E015.
This guards against an over-broad fix that swallows any '__lookup'-like tail."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Parent(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class Meta:
        app_label = 'probeapp'
        # intermediate 'nofield' does not exist on Parent
        ordering = ('parent__nofield__isnull',)


e1 = [e for e in Child.check() if e.id == 'models.E015']
print("intermediate-invalid E015:", e1)
sys.exit(0 if len(e1) == 1 else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4 regressions: E014 for non-list ordering; '?' and pk and '-'-prefixed
valid entries accepted; no errors when no ordering. Combines several 'SHALL keep'
criteria into structural checks."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models

results = {}


class BadType(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = 'test'  # not a list/tuple -> E014


class Valid(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('?', 'pk', '-test', 'test__isnull')


class NoOrder(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'


bad = BadType.check()
e014 = [e for e in bad if e.id == 'models.E014']
e015_bad = [e for e in bad if e.id == 'models.E015']
valid_e015 = [e for e in Valid.check() if e.id == 'models.E015']
noorder_ord = [e for e in NoOrder.check() if e.id in ('models.E014', 'models.E015')]

print("E014 on non-list:", e014)
print("E015 leaked on non-list:", e015_bad)
print("E015 on valid('?','pk','-test','test__isnull'):", valid_e015)
print("ordering errs when no ordering:", noorder_ord)

ok = (len(e014) == 1 and len(e015_bad) == 0
      and len(valid_e015) == 0 and len(noorder_ord) == 0)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1 AC1: local field followed by a registered lookup
('test__isnull') SHALL NOT emit models.E015. Holds patched, fails at base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Model(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('test__isnull',)


errs = Model.check()
e015 = [e for e in errs if e.id == 'models.E015']
print("errors:", errs)
print("E015 count:", len(e015))
sys.exit(0 if len(e015) == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12858: gold fix adds `fld.get_lookup(part) is None` alongside the existing `fld.get_transform(part) is None` in Model._check_ordering, so an ordering entry ending in a registered lookup (e.g. test__isnull) no longer wrongly reports models.E015.

Probe results (all run in the instance Docker image via nl_attack):
- probe_1 (Req1 AC1, POSITIVE CONTROL): local field + lookup 'test__isnull' -> no E015. HOLDS patched, VIOLATED (E015 count 1) at base -> discriminates.
- probe_2 (Req1 AC2): relation-spanning 'parent__test__isnull' -> no E015 patched (fields.E300 present but that's an unrelated app-registration artifact, not E015); VIOLATED at base. HOLDS patched.
- probe_3 (Req2 AC1): registered transform 'test__lower' (Lower via register_lookup) -> no E015. HOLDS patched & base (transform already accepted).
- probe_4 (Req3 AC1/AC2): 'test__nonexistent_thing' and bad first segment -> each still emits exactly one E015. HOLDS patched.
- probe_5 (Req3 AC3/AC4): intermediate invalid segment 'parent__nofield__isnull' still emits E015. HOLDS patched.
- probe_6 (Req4): E014 for non-list ordering (no E015 leak), '?'/pk/-test/test__isnull all accepted, no ordering errors when no ordering declared. HOLDS patched; VIOLATED at base (valid entry with lookup wrongly flagged).

Candidate wrong patches, both REJECTED by the suite (suite discriminates):
- weak.diff (drop the whole condition -> `if fld is None:`, accepts every unresolved segment): REJECTED by probe_4 and probe_5 (genuinely nonexistent fields/lookups no longer reported -> Req3 violated).
- weak2.diff (replace transform check with lookup check `fld.get_lookup(part) is None`, i.e. accept lookups but stop accepting transforms): REJECTED by probe_3 (transform 'test__lower' regresses to E015 -> Req2 violated).

All 5+ probes hold on the gold-patched tree; positive control fails at base and holds patched; >=1 candidate exercised and >=1 rejected (both rejected). No requirements-conforming alternative patch found that would fail the hidden test.

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
"""Positive control / Req1 AC1: local field followed by a registered lookup
('test__isnull') SHALL NOT emit models.E015. Holds patched, fails at base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class Model(models.Model):
    test = models.CharField(max_length=100)

    class Meta:
        app_label = 'probeapp'
        ordering = ('test__isnull',)


errs = Model.check()
e015 = [e for e in errs if e.id == 'models.E015']
print("errors:", errs)
print("E015 count:", len(e015))
sys.exit(0 if len(e015) == 0 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12858: gold fix adds `fld.get_lookup(part) is None` alongside the existing `fld.get_transform(part) is None` in Model._check_ordering, so an ordering entry ending in a registered lookup (e.g. test__isnull) no longer wrongly reports models.E015.

Probe results (all run in the instance Docker image via nl_attack):
- probe_1 (Req1 AC1, POSITIVE CONTROL): local field + lookup 'test__isnull' -> no E015. HOLDS patched, VIOLATED (E015 count 1) at base -> discriminates.
- probe_2 (Req1 AC2): relation-spanning 'parent__test__isnull' -> no E015 patched (fields.E300 present but that's an unrelated app-registration artifact, not E015); VIOLATED at base. HOLDS patched.
- probe_3 (Req2 AC1): registered transform 'test__lower' (Lower via register_lookup) -> no E015. HOLDS patched & base (transform already accepted).
- probe_4 (Req3 AC1/AC2): 'test__nonexistent_thing' and bad first segment -> each still emits exactly one E015. HOLDS patched.
- probe_5 (Req3 AC3/AC4): intermediate invalid segment 'parent__nofield__isnull' still emits E015. HOLDS patched.
- probe_6 (Req4): E014 for non-list ordering (no E015 leak), '?'/pk/-test/test__isnull all accepted, no ordering errors when no ordering declared. HOLDS patched; VIOLATED at base (valid entry with lookup wrongly flagged).

Candidate wrong patches, both REJECTED by the suite (suite discriminates):
- weak.diff (drop the whole condition -> `if fld is None:`, accepts every unresolved segment): REJECTED by probe_4 and probe_5 (genuinely nonexistent fields/lookups no longer reported -> Req3 violated).
- weak2.diff (replace transform check with lookup check `fld.get_lookup(part) is None`, i.e. accept lookups but stop accepting transforms): REJECTED by probe_3 (transform 'test__lower' regresses to E015 -> Req2 violated).

All 5+ probes hold on the gold-patched tree; positive control fails at base and holds patched; >=1 candidate exercised and >=1 rejected (both rejected). No requirements-conforming alternative patch found that would fail the hidden test.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch changes exactly one line in Model._check_ordering: the accept-condition on an unresolved trailing/intermediate segment goes from `fld.get_transform(part) is None` to `fld.get_transform(part) is None and fld.get_lookup(part) is None`, i.e. accept a segment naming a transform OR a registered lookup. The requirements pin the CHANGED observable behavior at the correct boundary: R1 mandates that lookup-ending entries (local and relation-spanning) stop producing E015 — confirmed the delta is E015 present at base_commit and absent on the patch for both local ('name__isnull') and relation-span ('supply__product__parent__isnull', the exact issue case). R2 preserves transform acceptance (get_transform branch untouched) and R4.2 phrasing 'transform OR registered lookup' matches the disjunction added. R3 keeps genuine E015 reporting (nonexistent leaf, first-segment-invalid, non-relation-as-relation) — all still emit E015. R4 covers untouched behavior (E014 for non-list, pk, '?' skip, descending '-' stripped). No requirement mandates behavior the patched code lacks, forbids behavior it has, invents behavior, or pins an over-narrow slice; the boundary is the full changed behavior, biconditional (accept transform/lookup, still reject truly nonexistent). Probes run via nl_attack on the instance image for both --base and gold-patched trees.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavior of Model._check_ordering as a contract, which is the legitimate purpose of the spec. Nothing is derivable only from the hidden test/gold:

- The example `supply__product__parent__isnull` and the lookup `isnull` are BOTH taken verbatim from the PUBLIC problem_statement — not from the hidden test (whose case is `test__isnull` on a CharField, which the document never mentions).
- The gold edit's identifiers `get_transform`/`get_lookup` are NOT reproduced; the document uses the public domain concepts 'transform' and 'registered lookup'. Naming the target module/function (`django/db/models/base.py`, `_check_ordering`) is legitimate localization.
- No test names, paths, class names (OtherModelTests), parametrization ids, or quoted test code appear.
- The enumerations in Requirements 3 and 4 (missing field, non-relational field treated as relation, E014 for non-list ordering, `?` random skip, pk, `-` descending marker, order_with_respect_to) describe the full existing contract of _check_ordering / the PASS_TO_PASS surface as 'preserve unaffected behavior'. These are derivable from the public function's documented behavior and the changed-code region, not from reading the hidden tests; they translate behavior rather than transmit the tests. No case is test-shaped in a way that reconstructs a specific hidden parametrization (the sole FAIL_TO_PASS case, CharField `test__isnull`, is described only generically as 'local field followed by a registered lookup').

This is a faithful behavioral translation, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
