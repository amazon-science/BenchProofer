# P2 adversarial audit — django__django-16901

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Probe R1.1/R1.3/R1.4: n-ary XOR (5 operands) on a non-native-XOR backend
(sqlite) matches a row iff an ODD number of operands are true.

Encodes Requirement 1 acceptance criteria 1,3,4: parity semantics for >2
operands. Uses the exact F2P shape (num__gte thresholds 1,3,5,7,9).
Exit 0 iff observed rows == parity-expected rows.
"""
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)

django.setup()

from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

# sanity: sqlite must NOT support native XOR (else this probe is vacuous)
assert not connections["default"].features.supports_logical_xor, "backend has native XOR"

with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)

from django.db.models import Q
qs = Number.objects.filter(
    Q(num__gte=1) ^ Q(num__gte=3) ^ Q(num__gte=5) ^ Q(num__gte=7) ^ Q(num__gte=9)
)
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(
    i for i in range(10)
    if (i >= 1) ^ (i >= 3) ^ (i >= 5) ^ (i >= 7) ^ (i >= 9)
)
print("observed:", observed)
print("expected(parity):", expected)
if observed == expected:
    print("PASS: 5-operand XOR follows odd parity")
    sys.exit(0)
print("FAIL: 5-operand XOR does not follow odd parity")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R1.5: same true predicate XOR'd n times -> matches iff n is odd.
# num=5 matches Q(num=5). Combine it 1..5 times.
def xor_n(n):
    q = Q(num=5)
    expr = q
    for _ in range(n-1):
        expr = expr ^ Q(num=5)
    return Number.objects.filter(expr).filter(num=5).count()
res = {n: xor_n(n) for n in range(1,6)}
print("counts by #copies:", res)
expected = {1:1, 2:0, 3:1, 4:0, 5:1}
if res == expected:
    print("PASS: odd copies match, even copies don't")
    sys.exit(0)
print("FAIL: repeated-predicate parity wrong; expected", expected)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R1.6 / R1.1: overlapping operands (a row may satisfy several at once) ->
# selected iff #satisfied is odd. Use 3 overlapping thresholds.
qs = Number.objects.filter(Q(num__gte=2) ^ Q(num__gte=4) ^ Q(num__gte=6))
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(i for i in range(10) if (i>=2) ^ (i>=4) ^ (i>=6))
print("observed:", observed, "expected(parity):", expected)
# also confirm it differs from exactly-one for these overlapping operands
exactly_one = sorted(i for i in range(10)
                     if [i>=2, i>=4, i>=6].count(True) == 1)
print("exactly-one would give:", exactly_one)
if observed == expected and expected != exactly_one:
    print("PASS: overlapping 3-operand XOR uses parity, not exactly-one")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R2.1 / R2.3: two-operand XOR = exactly one of the two true. Also equals parity.
qs = Number.objects.filter(Q(num__gte=3) ^ Q(num__gte=7))
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(i for i in range(10) if (i>=3) ^ (i>=7))
print("observed:", observed, "expected:", expected)
if observed == expected:
    print("PASS: two-operand exactly-one preserved")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R4.1: two-operand XOR selects rows matching one operand or the other but not both.
# Use disjoint-ish ranges with overlap to test 'not both'.
qs = Number.objects.filter(Q(num__lt=4) ^ Q(num__gte=2))
observed = sorted(qs.values_list("num", flat=True))
# both true for 2,3 -> excluded; exactly-one for others
expected = sorted(i for i in range(10) if (i<4) ^ (i>=2))
print("observed:", observed, "expected:", expected)
# rows where BOTH hold (2,3) must be absent
both = [i for i in range(10) if (i<4) and (i>=2)]
print("both-true rows (must be excluded):", both)
if observed == expected and all(b not in observed for b in both):
    print("PASS: one-or-other-but-not-both")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R4.3: excluding via XOR yields exactly the complement of selecting via same XOR.
cond = Q(num__gte=1) ^ Q(num__gte=4) ^ Q(num__gte=8)
selected = set(Number.objects.filter(cond).values_list("num", flat=True))
excluded = set(Number.objects.exclude(cond).values_list("num", flat=True))
allrows = set(range(10))
print("selected:", sorted(selected))
print("excluded:", sorted(excluded))
if excluded == (allrows - selected) and (selected & excluded) == set():
    print("PASS: exclude is complement of select")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R4.2: negated predicate as an XOR operand still contributes its truth value
# under parity. Mirrors test_filter_negated: Q(num__lte=7) ^ ~Q(num__lt=3).
qs = Number.objects.filter(Q(num__lte=7) ^ ~Q(num__lt=3))
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(i for i in range(10) if (i<=7) ^ (not (i<3)))
print("observed:", observed, "expected:", expected)
if observed == expected:
    print("PASS: negated operand handled under XOR fallback")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)
django.setup()
from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

assert not connections["default"].features.supports_logical_xor, "backend has native XOR"
with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)
from django.db.models import Q
# R2.2 / R1.2 / R3.3 (structural): the fallback SQL for >2 operands applies a
# modulo-2 reduction; the 2-operand fallback compares the count directly (no MOD).
q3 = Number.objects.filter(Q(num__gte=1) ^ Q(num__gte=3) ^ Q(num__gte=5))
q2 = Number.objects.filter(Q(num__gte=1) ^ Q(num__gte=3))
sql3 = str(q3.query).upper()
sql2 = str(q2.query).upper()
print("3-operand SQL:", sql3)
print("2-operand SQL:", sql2)
has_mod3 = ("MOD" in sql3) or (" % " in sql3) or ("%%" in sql3) or ("% 2" in sql3)
has_mod2 = ("MOD" in sql2) or (" % " in sql2) or ("% 2" in sql2)
# 3-operand must reduce mod 2; 2-operand must NOT
if has_mod3 and not has_mod2:
    print("PASS: >2 uses modulo, 2-operand does not")
    sys.exit(0)
print("FAIL: has_mod3=%s has_mod2=%s" % (has_mod3, has_mod2))
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe R1.1/R1.3/R1.4: n-ary XOR (5 operands) on a non-native-XOR backend
(sqlite) matches a row iff an ODD number of operands are true.

Encodes Requirement 1 acceptance criteria 1,3,4: parity semantics for >2
operands. Uses the exact F2P shape (num__gte thresholds 1,3,5,7,9).
Exit 0 iff observed rows == parity-expected rows.
"""
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)

django.setup()

from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

# sanity: sqlite must NOT support native XOR (else this probe is vacuous)
assert not connections["default"].features.supports_logical_xor, "backend has native XOR"

with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)

from django.db.models import Q
qs = Number.objects.filter(
    Q(num__gte=1) ^ Q(num__gte=3) ^ Q(num__gte=5) ^ Q(num__gte=7) ^ Q(num__gte=9)
)
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(
    i for i in range(10)
    if (i >= 1) ^ (i >= 3) ^ (i >= 5) ^ (i >= 7) ^ (i >= 9)
)
print("observed:", observed)
print("expected(parity):", expected)
if observed == expected:
    print("PASS: 5-operand XOR follows odd parity")
    sys.exit(0)
print("FAIL: 5-operand XOR does not follow odd parity")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16901: n-ary XOR fallback should compute odd-parity (MOD(count,2)==1) for >2 operands on backends lacking native XOR (sqlite here), while keeping exactly-one for 2 operands. Gold patch adds `from django.db.models.functions import Mod` and wraps rhs_sum in Mod(...,2) when len(children)>2.

All probes run on in-memory sqlite (confirmed features.supports_logical_xor is False, so the fallback path is exercised). Number model, rows num=0..9.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/1.3/1.4, POSITIVE CONTROL): 5-operand XOR (num__gte 1,3,5,7,9) matches parity-expected [1,2,5,6,9]. HOLDS patched, FAILS at base (base gives [1,2] = exactly-one). Discriminates.
- probe_2 (R1.5): same true predicate (num=5) XOR'd 1..5 times -> match counts {1:1,2:0,3:1,4:0,5:1} (odd copies match). HOLDS patched; under no-op candidate gives {1:1,2:0,3:0,4:0,5:0}.
- probe_3 (R1.6/R1.1): overlapping 3 operands (num__gte 2,4,6) -> parity [2,3,6,7,8,9], and verified this differs from the exactly-one outcome.
- probe_4 (R2.1/2.3): two-operand XOR (num__gte 3,7) = exactly-one = [3,4,5,6], unchanged.
- probe_5 (R4.1): two-operand one-or-other-but-not-both; both-true rows {2,3} excluded.
- probe_6 (R4.3): exclude(cond) is exact complement of filter(cond) for a 3-operand XOR.
- probe_7 (R4.2): negated operand (Q(num__lte=7) ^ ~Q(num__lt=3)) handled under fallback -> [0,1,2,8,9].
- probe_8 (R2.2/R1.2/R3.3 structural): generated SQL for 3 operands contains MOD; SQL for 2 operands does not (compares count directly against 1).

CANDIDATE PATCH weak_noop.diff: adds the Mod import but does NOT apply the modulo reduction (i.e. leaves the exactly-one buggy behavior). Applies cleanly at base. Probes 1,2,3,8 all REJECT it (VIOLATED). This demonstrates the suite discriminates a requirements-non-conforming implementation.

Floor met: 8 distinct probes all hold on patched; positive control discriminates base vs patched (prepatch reproduced); >=1 candidate exercised and REJECTED. No requirements-conforming candidate found that fails to resolve. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe R1.1/R1.3/R1.4: n-ary XOR (5 operands) on a non-native-XOR backend
(sqlite) matches a row iff an ODD number of operands are true.

Encodes Requirement 1 acceptance criteria 1,3,4: parity semantics for >2
operands. Uses the exact F2P shape (num__gte thresholds 1,3,5,7,9).
Exit 0 iff observed rows == parity-expected rows.
"""
import sys, os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)

import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
    USE_TZ=False,
)

django.setup()

from django.db import models, connection, connections

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

# sanity: sqlite must NOT support native XOR (else this probe is vacuous)
assert not connections["default"].features.supports_logical_xor, "backend has native XOR"

with connection.schema_editor() as se:
    se.create_model(Number)
for i in range(10):
    Number.objects.create(num=i)

from django.db.models import Q
qs = Number.objects.filter(
    Q(num__gte=1) ^ Q(num__gte=3) ^ Q(num__gte=5) ^ Q(num__gte=7) ^ Q(num__gte=9)
)
observed = sorted(qs.values_list("num", flat=True))
expected = sorted(
    i for i in range(10)
    if (i >= 1) ^ (i >= 3) ^ (i >= 5) ^ (i >= 7) ^ (i >= 9)
)
print("observed:", observed)
print("expected(parity):", expected)
if observed == expected:
    print("PASS: 5-operand XOR follows odd parity")
    sys.exit(0)
print("FAIL: 5-operand XOR does not follow odd parity")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16901: n-ary XOR fallback should compute odd-parity (MOD(count,2)==1) for >2 operands on backends lacking native XOR (sqlite here), while keeping exactly-one for 2 operands. Gold patch adds `from django.db.models.functions import Mod` and wraps rhs_sum in Mod(...,2) when len(children)>2.

All probes run on in-memory sqlite (confirmed features.supports_logical_xor is False, so the fallback path is exercised). Number model, rows num=0..9.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/1.3/1.4, POSITIVE CONTROL): 5-operand XOR (num__gte 1,3,5,7,9) matches parity-expected [1,2,5,6,9]. HOLDS patched, FAILS at base (base gives [1,2] = exactly-one). Discriminates.
- probe_2 (R1.5): same true predicate (num=5) XOR'd 1..5 times -> match counts {1:1,2:0,3:1,4:0,5:1} (odd copies match). HOLDS patched; under no-op candidate gives {1:1,2:0,3:0,4:0,5:0}.
- probe_3 (R1.6/R1.1): overlapping 3 operands (num__gte 2,4,6) -> parity [2,3,6,7,8,9], and verified this differs from the exactly-one outcome.
- probe_4 (R2.1/2.3): two-operand XOR (num__gte 3,7) = exactly-one = [3,4,5,6], unchanged.
- probe_5 (R4.1): two-operand one-or-other-but-not-both; both-true rows {2,3} excluded.
- probe_6 (R4.3): exclude(cond) is exact complement of filter(cond) for a 3-operand XOR.
- probe_7 (R4.2): negated operand (Q(num__lte=7) ^ ~Q(num__lt=3)) handled under fallback -> [0,1,2,8,9].
- probe_8 (R2.2/R1.2/R3.3 structural): generated SQL for 3 operands contains MOD; SQL for 2 operands does not (compares count directly against 1).

CANDIDATE PATCH weak_noop.diff: adds the Mod import but does NOT apply the modulo reduction (i.e. leaves the exactly-one buggy behavior). Applies cleanly at base. Probes 1,2,3,8 all REJECT it (VIOLATED). This demonstrates the suite discriminates a requirements-non-conforming implementation.

Floor met: 8 distinct probes all hold on patched; positive control discriminates base vs patched (prepatch reproduced); >=1 candidate exercised and REJECTED. No requirements-conforming candidate found that fails to resolve. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `from django.db.models.functions import Mod` and wraps rhs_sum in `Mod(rhs_sum, 2)` only when len(self.children) > 2, then tests Exact(1, ...). The requirements pin exactly this changed observable behavior (parity for n>2, exactly-one for n==2) at the correct modeling boundary — the >2 vs ==2 operand split — rather than a narrower slice. Requirement 2.2/2.3 and 3.3 correctly describe the preserved two-operand path and the OR+count structure. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the PUBLIC problem_statement (n-ary XOR = odd parity, exactly-one only correct for 2 operands, native MySQL vs PostgreSQL/SQLite/Oracle fallback, and the 1/3/5-repeat example yielding match/no-match — all explicitly in problem_statement). Localization to WhereNode.as_sql in django/db/models/sql/where.py is legitimate. The 'OR of operands AND count==1' rewrite and 'reduce modulo two, equal one' description track the pre-existing code comment / natural behavioral statement, not a smuggled fix identifier (no mention of Mod, Case/When, reduce, or the len>2 guard as code). The hidden FAIL_TO_PASS test (test_filter_multiple, num__gte 1/3/5/7/9) is NOT reconstructed: no thresholds, expected row sets, or comprehension are enumerated. Requirement 4's regression enumeration (negated predicates, pk predicates, exclude-as-complement, incremental building) loosely echoes PASS_TO_PASS topics but is expressed as behavioral prose with no test names, paths, ids, quoted code, or parametrized-case enumerations — i.e., legitimate translation of test intent into requirements, which is explicitly permitted. No test-derivable identifiers, code, or case ids leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
