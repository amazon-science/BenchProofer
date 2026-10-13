# P2 adversarial audit — django__django-12663

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_e2e.py`, `probe_2_target.py`, `probe_3_fallback.py`, `probe_4_precedence.py`, `probe_5_regression.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_e2e.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_e2e.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL + Requirement 3.1/3.2/3.3.
End-to-end: filter a Subquery-annotated (over OuterRef) queryset by a
SimpleLazyObject wrapping a related Manager instance. Must NOT raise
TypeError and SHALL return the matching row (same as concrete instance).
Holds on gold-patched tree; fails at base (TypeError)."""
import os, sys, tempfile


def setup():
    d = tempfile.mkdtemp(prefix="probeapp_")
    pkg = os.path.join(d, "probeapp")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "models.py"), "w") as f:
        f.write(
            "from django.db import models\n"
            "class Manager(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Employee(models.Model):\n"
            "    firstname = models.CharField(max_length=50)\n"
            "    lastname = models.CharField(max_length=50)\n"
            "    manager = models.ForeignKey(Manager, models.CASCADE, null=True)\n"
            "class Company(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "    ceo = models.ForeignKey(Employee, models.CASCADE, related_name='company_ceo')\n"
        )
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=False,
    )
    django.setup()
    from django.core.management import call_command
    call_command("migrate", run_syncdb=True, verbosity=0)
    from probeapp.models import Manager, Employee, Company
    return Manager, Employee, Company


def main():
    Manager, Employee, Company = setup()
    from django.db.models import Subquery, OuterRef
    from django.utils.functional import SimpleLazyObject

    mgr = Manager.objects.create(name="Manager")
    emp = Employee.objects.create(firstname="Max", lastname="M", manager=mgr)
    gmbh = Company.objects.create(name="GmbH", ceo=emp)
    # a company whose ceo has no manager -> should NOT match
    emp2 = Employee.objects.create(firstname="Other", lastname="O", manager=None)
    Company.objects.create(name="Other", ceo=emp2)

    lazy = SimpleLazyObject(lambda: Manager.objects.get(pk=mgr.pk))
    qs = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=lazy)

    got_lazy = list(qs)
    print("lazy result:", [c.name for c in got_lazy])

    # concrete comparison
    qs2 = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=mgr)
    got_concrete = list(qs2)
    print("concrete result:", [c.name for c in got_concrete])

    assert [c.pk for c in got_lazy] == [gmbh.pk], "lazy filter did not return the GmbH row"
    assert [c.pk for c in got_lazy] == [c.pk for c in got_concrete], "lazy != concrete result"
    print("OK: lazy subquery filter returned matching row, no TypeError")


if __name__ == "__main__":
    main()
```

Attack 2 — `probe_2_target.py` → holds on the patched tree (good)

```python
"""Requirement 1.1: WHEN exactly one selected column, output_field SHALL
return that column's `target` when present (not None), not its `field`.
Invokes Query.output_field.fget on a stub with a single fake Col that has
distinct target and field sentinels."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
                   DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   INSTALLED_APPS=[], USE_TZ=False)
django.setup()

from django.db.models.sql.query import Query

TARGET = object()
FIELD = object()


class FakeCol:
    target = TARGET
    field = FIELD


class Stub:
    select = (FakeCol(),)
    annotation_select = {}


out = Query.output_field.fget(Stub())
print("output_field is target?", out is TARGET, "is field?", out is FIELD)
assert out is TARGET, "expected the column's target, got %r" % (out,)
print("OK: single column reports target when present")
```

Attack 3 — `probe_3_fallback.py` → holds on the patched tree (good)

```python
"""Requirement 1.2: IF the single selected column's target is absent/None,
THEN output_field SHALL fall back to the column's `field`."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
                   DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   INSTALLED_APPS=[], USE_TZ=False)
django.setup()

from django.db.models.sql.query import Query

FIELD = object()


class FakeColNoTarget:
    target = None
    field = FIELD


class Stub:
    select = (FakeColNoTarget(),)
    annotation_select = {}


out = Query.output_field.fget(Stub())
print("output_field is field?", out is FIELD)
assert out is FIELD, "expected fallback to field, got %r" % (out,)

# Also cover the case where `target` attribute is entirely absent.
class FakeColNoAttr:
    field = FIELD


class Stub2:
    select = (FakeColNoAttr(),)
    annotation_select = {}


out2 = Query.output_field.fget(Stub2())
assert out2 is FIELD, "expected fallback to field when target attr missing, got %r" % (out2,)
print("OK: falls back to field when target is None or absent")
```

Attack 4 — `probe_4_precedence.py` → holds on the patched tree (good)

```python
"""Requirement 1.4 & 2.3: the single-column branch is evaluated BEFORE the
single-annotation branch and derives the descriptor SOLELY from the column,
never consulting annotation_select. Stub has one column AND one annotation;
result must come from the column's target."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
                   DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   INSTALLED_APPS=[], USE_TZ=False)
django.setup()

from django.db.models.sql.query import Query

COL_TARGET = object()
COL_FIELD = object()
ANN_OUTPUT = object()


class FakeCol:
    target = COL_TARGET
    field = COL_FIELD


class FakeAnn:
    output_field = ANN_OUTPUT


class Stub:
    select = (FakeCol(),)
    annotation_select = {"a": FakeAnn()}


out = Query.output_field.fget(Stub())
print("result is col target?", out is COL_TARGET, "is annotation?", out is ANN_OUTPUT)
assert out is COL_TARGET, "column branch must win and use column target, got %r" % (out,)
print("OK: single-column branch precedes annotation branch, uses only the column")
```

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

```python
"""Requirement 1.3 & 2.1 & 2.2 (SHALL-keep regressions):
- zero columns + exactly one annotation -> annotation's output_field
- zero columns + zero/multiple annotations -> None
- multiple columns -> NOT the target-selection branch; falls to annotation
  logic (here: None)."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
                   DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   INSTALLED_APPS=[], USE_TZ=False)
django.setup()

from django.db.models.sql.query import Query

ANN = object()


class FakeAnn:
    output_field = ANN


class FakeCol:
    target = object()
    field = object()


# (a) zero columns, one annotation -> annotation output (Req 2.1)
class S1:
    select = ()
    annotation_select = {"a": FakeAnn()}


r1 = Query.output_field.fget(S1())
assert r1 is ANN, "one annotation should give annotation output, got %r" % (r1,)

# (b) zero columns, zero annotations -> None (Req 2.2)
class S2:
    select = ()
    annotation_select = {}


r2 = Query.output_field.fget(S2())
assert r2 is None, "no col / no annotation should be None, got %r" % (r2,)

# (c) two columns -> single-column branch NOT applied; two annotations too -> None (Req 1.3, 2.2)
class S3:
    select = (FakeCol(), FakeCol())
    annotation_select = {"a": FakeAnn(), "b": FakeAnn()}


r3 = Query.output_field.fget(S3())
assert r3 is None, "multi-column/multi-annotation should be None, got %r" % (r3,)

# (d) two columns but exactly one annotation -> annotation output (Req 1.3: strictly one column)
class S4:
    select = (FakeCol(), FakeCol())
    annotation_select = {"a": FakeAnn()}


r4 = Query.output_field.fget(S4())
assert r4 is ANN, "two columns must skip col branch, use single annotation, got %r" % (r4,)

print("OK: annotation/empty/multi-column regressions preserved")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_e2e.py`

```python
"""POSITIVE CONTROL + Requirement 3.1/3.2/3.3.
End-to-end: filter a Subquery-annotated (over OuterRef) queryset by a
SimpleLazyObject wrapping a related Manager instance. Must NOT raise
TypeError and SHALL return the matching row (same as concrete instance).
Holds on gold-patched tree; fails at base (TypeError)."""
import os, sys, tempfile


def setup():
    d = tempfile.mkdtemp(prefix="probeapp_")
    pkg = os.path.join(d, "probeapp")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "models.py"), "w") as f:
        f.write(
            "from django.db import models\n"
            "class Manager(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Employee(models.Model):\n"
            "    firstname = models.CharField(max_length=50)\n"
            "    lastname = models.CharField(max_length=50)\n"
            "    manager = models.ForeignKey(Manager, models.CASCADE, null=True)\n"
            "class Company(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "    ceo = models.ForeignKey(Employee, models.CASCADE, related_name='company_ceo')\n"
        )
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=False,
    )
    django.setup()
    from django.core.management import call_command
    call_command("migrate", run_syncdb=True, verbosity=0)
    from probeapp.models import Manager, Employee, Company
    return Manager, Employee, Company


def main():
    Manager, Employee, Company = setup()
    from django.db.models import Subquery, OuterRef
    from django.utils.functional import SimpleLazyObject

    mgr = Manager.objects.create(name="Manager")
    emp = Employee.objects.create(firstname="Max", lastname="M", manager=mgr)
    gmbh = Company.objects.create(name="GmbH", ceo=emp)
    # a company whose ceo has no manager -> should NOT match
    emp2 = Employee.objects.create(firstname="Other", lastname="O", manager=None)
    Company.objects.create(name="Other", ceo=emp2)

    lazy = SimpleLazyObject(lambda: Manager.objects.get(pk=mgr.pk))
    qs = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=lazy)

    got_lazy = list(qs)
    print("lazy result:", [c.name for c in got_lazy])

    # concrete comparison
    qs2 = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=mgr)
    got_concrete = list(qs2)
    print("concrete result:", [c.name for c in got_concrete])

    assert [c.pk for c in got_lazy] == [gmbh.pk], "lazy filter did not return the GmbH row"
    assert [c.pk for c in got_lazy] == [c.pk for c in got_concrete], "lazy != concrete result"
    print("OK: lazy subquery filter returned matching row, no TypeError")


if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree.

Probe -> requirement -> results:
- probe_1_e2e (POSITIVE CONTROL; Req 3.1/3.2/3.3): end-to-end Company.annotate(ceo_manager=Subquery(Employee.filter(lastname=OuterRef('ceo__lastname')).values('manager'))).filter(ceo_manager=SimpleLazyObject(...)). HOLDS patched ('GmbH', == concrete result); VIOLATED at base with the exact TypeError: Field 'id' expected a number but got <SimpleLazyObject ...>. Discriminates.
- probe_2_target (Req 1.1): single fake Col with distinct target/field sentinels; output_field.fget must return target. HOLDS patched; VIOLATED under weak_base (returns .field).
- probe_3_fallback (Req 1.2): single col with target=None AND a col with no target attr -> must fall back to field. HOLDS patched; VIOLATED under weak_notfallback (returns target unconditionally, i.e. None).
- probe_4_precedence (Req 1.4/2.3): stub with one col AND one annotation; result must be the col target, never the annotation output. HOLDS patched.
- probe_5_regression (Req 1.3/2.1/2.2): zero-col+one-ann -> annotation output; zero/zero -> None; two-col+two-ann -> None; two-col+one-ann -> annotation output (single-column branch strictly one entry). HOLDS patched.

Candidate wrong patches, both REJECTED by the suite (so it discriminates):
- weak_base (keeps original `return self.select[0].field`): rejected by probe_1_e2e (TypeError) and probe_2_target. This is the base/regression behavior and would not resolve the hidden test.
- weak_notfallback (`return getattr(select,'target',None)` with NO `or select.field` fallback): rejected by probe_3_fallback — violates Req 1.2. A requirements-conforming-looking but partial fix.

No requirements-conforming patch was found that passes all probes yet fails to resolve; no VIOLATION found on the patched tree. Verdict SOUND: >=5 probes hold, positive control discriminates (holds patched, fails base), and >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_e2e.py`, `probe_2_target.py`, `probe_3_fallback.py`, `probe_4_precedence.py`, `probe_5_regression.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_e2e.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_e2e.py` → holds on the patched tree (good)

Attack 2 — `probe_2_target.py` → holds on the patched tree (good)

Attack 3 — `probe_3_fallback.py` → holds on the patched tree (good)

Attack 4 — `probe_4_precedence.py` → holds on the patched tree (good)

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_e2e.py`

```python
"""POSITIVE CONTROL + Requirement 3.1/3.2/3.3.
End-to-end: filter a Subquery-annotated (over OuterRef) queryset by a
SimpleLazyObject wrapping a related Manager instance. Must NOT raise
TypeError and SHALL return the matching row (same as concrete instance).
Holds on gold-patched tree; fails at base (TypeError)."""
import os, sys, tempfile


def setup():
    d = tempfile.mkdtemp(prefix="probeapp_")
    pkg = os.path.join(d, "probeapp")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "models.py"), "w") as f:
        f.write(
            "from django.db import models\n"
            "class Manager(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "class Employee(models.Model):\n"
            "    firstname = models.CharField(max_length=50)\n"
            "    lastname = models.CharField(max_length=50)\n"
            "    manager = models.ForeignKey(Manager, models.CASCADE, null=True)\n"
            "class Company(models.Model):\n"
            "    name = models.CharField(max_length=50)\n"
            "    ceo = models.ForeignKey(Employee, models.CASCADE, related_name='company_ceo')\n"
        )
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "probeapp"],
        USE_TZ=False,
    )
    django.setup()
    from django.core.management import call_command
    call_command("migrate", run_syncdb=True, verbosity=0)
    from probeapp.models import Manager, Employee, Company
    return Manager, Employee, Company


def main():
    Manager, Employee, Company = setup()
    from django.db.models import Subquery, OuterRef
    from django.utils.functional import SimpleLazyObject

    mgr = Manager.objects.create(name="Manager")
    emp = Employee.objects.create(firstname="Max", lastname="M", manager=mgr)
    gmbh = Company.objects.create(name="GmbH", ceo=emp)
    # a company whose ceo has no manager -> should NOT match
    emp2 = Employee.objects.create(firstname="Other", lastname="O", manager=None)
    Company.objects.create(name="Other", ceo=emp2)

    lazy = SimpleLazyObject(lambda: Manager.objects.get(pk=mgr.pk))
    qs = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=lazy)

    got_lazy = list(qs)
    print("lazy result:", [c.name for c in got_lazy])

    # concrete comparison
    qs2 = Company.objects.annotate(
        ceo_manager=Subquery(
            Employee.objects.filter(lastname=OuterRef("ceo__lastname")).values("manager"),
        ),
    ).filter(ceo_manager=mgr)
    got_concrete = list(qs2)
    print("concrete result:", [c.name for c in got_concrete])

    assert [c.pk for c in got_lazy] == [gmbh.pk], "lazy filter did not return the GmbH row"
    assert [c.pk for c in got_lazy] == [c.pk for c in got_concrete], "lazy != concrete result"
    print("OK: lazy subquery filter returned matching row, no TypeError")


if __name__ == "__main__":
    main()
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree.

Probe -> requirement -> results:
- probe_1_e2e (POSITIVE CONTROL; Req 3.1/3.2/3.3): end-to-end Company.annotate(ceo_manager=Subquery(Employee.filter(lastname=OuterRef('ceo__lastname')).values('manager'))).filter(ceo_manager=SimpleLazyObject(...)). HOLDS patched ('GmbH', == concrete result); VIOLATED at base with the exact TypeError: Field 'id' expected a number but got <SimpleLazyObject ...>. Discriminates.
- probe_2_target (Req 1.1): single fake Col with distinct target/field sentinels; output_field.fget must return target. HOLDS patched; VIOLATED under weak_base (returns .field).
- probe_3_fallback (Req 1.2): single col with target=None AND a col with no target attr -> must fall back to field. HOLDS patched; VIOLATED under weak_notfallback (returns target unconditionally, i.e. None).
- probe_4_precedence (Req 1.4/2.3): stub with one col AND one annotation; result must be the col target, never the annotation output. HOLDS patched.
- probe_5_regression (Req 1.3/2.1/2.2): zero-col+one-ann -> annotation output; zero/zero -> None; two-col+two-ann -> None; two-col+one-ann -> annotation output (single-column branch strictly one entry). HOLDS patched.

Candidate wrong patches, both REJECTED by the suite (so it discriminates):
- weak_base (keeps original `return self.select[0].field`): rejected by probe_1_e2e (TypeError) and probe_2_target. This is the base/regression behavior and would not resolve the hidden test.
- weak_notfallback (`return getattr(select,'target',None)` with NO `or select.field` fallback): rejected by probe_3_fallback — violates Req 1.2. A requirements-conforming-looking but partial fix.

No requirements-conforming patch was found that passes all probes yet fails to resolve; no VIOLATION found on the patched tree. Verdict SOUND: >=5 probes hold, positive control discriminates (holds patched, fails base), and >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: `return self.select[0].field` -> `select = self.select[0]; return getattr(select,'target',None) or select.field`. The `getattr(..., None)` covers R1.2's 'target absent/None' fallback (probed with both target=None and no target attribute). Requirements pin the actual changed observable behavior (output_field descriptor selection) at the correct boundary, not a narrow slice. R3 describes the downstream lazy-object/subquery consequence, which is the motivating issue behavior enabled by the R1 change — consistent with the fix and F2P test. Requirements match code exactly.

Counterexample / evidence:

```
N/A — no divergence. Base probe confirms the twin fails (single-col path returns field='FakeField' pre-patch), and every patched-behavior probe returned exit 0 ('ALL OK').
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to Query.output_field and refers to Col.target/Col.field — all pre-existing Django API names, legitimate for localization, not fix-invented identifiers (the gold edit's only new token is the trivial local `select`, absent here). No test function/class names (test_subquery_filter_by_lazy, BasicExpressionsTests), no test file paths (tests/expressions/tests.py / models.py), no hidden-test model names (Manager, Company, Employee, ceo_manager), and no parametrization ids appear. Requirement 3's scenario (SimpleLazyObject + nested Subquery/OuterRef, TypeError on int() coercion of a related column) is already fully public in problem_statement, which includes the model/testcase sketch and the exact traceback; the document is a strictly-more-general behavioral restatement (return target when present else field; single-column before single-annotation; None otherwise) rather than an enumeration mirroring the hidden test. Requirements are behavioral, not test-shaped.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
