# P2 adversarial audit — django__django-13109

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_positive_hidden_row.py`, `probe_2_reject_nonexistent.py`, `probe_3_limit_choices_to.py`, `probe_4_parent_link_and_none.py`, `probe_5_standard_manager_and_field_match.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_positive_hidden_row.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_positive_hidden_row.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.1,1.2,1.5: FK validate() must accept a value that
points at a genuinely stored target row that the target model's DEFAULT manager
hides (archived=True). HOLDS on patched (uses _base_manager), FAILS at base
(uses _default_manager -> ValidationError)."""
import sys, types
import django
from django.conf import settings

# register a synthetic app package 'p' so models can live in it
p = types.ModuleType('p')
p.__path__ = ['/work']
sys.modules['p'] = p

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection
from django.core.exceptions import ValidationError


class AuthorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Author(models.Model):
    name = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    objects = AuthorManager()

    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

# archived author: hidden by default manager, present in base manager
a = Author.objects.create(name="Randy", archived=True)
# sanity: default manager hides it
assert Author.objects.filter(pk=a.pk).count() == 0, "default manager should hide archived"
assert Author._base_manager.filter(pk=a.pk).count() == 1

art = Article(title="T", author=a)
fk = Article._meta.get_field('author')
try:
    fk.validate(a.pk, art)
    print("HOLDS: FK.validate accepted hidden (archived) target row pk=%s" % a.pk)
    sys.exit(0)
except ValidationError as e:
    print("VIOLATED: FK.validate rejected an existing but hidden row: %r" % (e.messages,))
    sys.exit(1)
```

Attack 2 — `probe_2_reject_nonexistent.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: a FK value matching NO stored target row must raise a
ValidationError with code 'invalid' and params carrying model, field_name,
value, and a 'pk' entry. HOLDS on both base and patched (regression)."""
import sys, types
import django
from django.conf import settings
p = types.ModuleType('p'); p.__path__ = ['/work']; sys.modules['p'] = p
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection
from django.core.exceptions import ValidationError


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

art = Article(title="T", author_id=999)
fk = Article._meta.get_field('author')
try:
    fk.validate(999, art)
    print("VIOLATED: no error raised for non-existent value 999")
    sys.exit(1)
except ValidationError as e:
    ok = True
    if e.code != 'invalid':
        print("VIOLATED: code=%r not 'invalid'" % e.code); ok = False
    params = e.params or {}
    for key in ('model', 'field', 'value', 'pk'):
        if key not in params:
            print("VIOLATED: missing param %r in %r" % (key, params)); ok = False
    if params.get('pk') != 999 or params.get('value') != 999:
        print("VIOLATED: value/pk not 999: %r" % params); ok = False
    if ok:
        print("HOLDS: rejected non-existent, code=invalid, params=%r" % params)
        sys.exit(0)
    sys.exit(1)
```

Attack 3 — `probe_3_limit_choices_to.py` → holds on the patched tree (good)

```python
"""Req1.4 / Req2.1: validate() must apply the field's limit_choices_to to the
existence query — a stored row that matches the referenced-field value but
FAILS limit_choices_to must be rejected; one that satisfies it must pass.
HOLDS on both trees (regression of choice constraint)."""
import sys, types
import django
from django.conf import settings
p = types.ModuleType('p'); p.__path__ = ['/work']; sys.modules['p'] = p
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection
from django.core.exceptions import ValidationError


class Author(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE,
                               limit_choices_to={'active': True})
    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

inactive = Author.objects.create(name="Ina", active=False)
active = Author.objects.create(name="Act", active=True)
fk = Article._meta.get_field('author')

# inactive author violates limit_choices_to -> must be rejected
try:
    fk.validate(inactive.pk, Article(title="T", author=inactive))
    print("VIOLATED: accepted a row that fails limit_choices_to")
    sys.exit(1)
except ValidationError:
    pass

# active author satisfies it -> must pass
try:
    fk.validate(active.pk, Article(title="T", author=active))
except ValidationError as e:
    print("VIOLATED: rejected a row that satisfies limit_choices_to: %r" % e.messages)
    sys.exit(1)

print("HOLDS: limit_choices_to enforced (inactive rejected, active accepted)")
sys.exit(0)
```

Attack 4 — `probe_4_parent_link_and_none.py` → holds on the patched tree (good)

```python
"""Req3.1 & Req3.2: early exits. (a) A parent-link FK returns WITHOUT any
existence check (even for a bogus value). (b) A None value returns without an
existence check. HOLDS on both trees."""
import sys, types
import django
from django.conf import settings
p = types.ModuleType('p'); p.__path__ = ['/work']; sys.modules['p'] = p
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection
from django.core.exceptions import ValidationError


class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        app_label = 'p'


# multi-table inheritance -> Book has an implicit parent_link FK author_ptr
class Book(Author):
    pages = models.IntegerField(default=0)
    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)
    se.create_model(Book)

# (a) parent-link field: pass a bogus value; must NOT raise (early return)
parent_link = Book._meta.get_field('author_ptr')
assert parent_link.remote_field.parent_link, "expected a parent_link field"
try:
    parent_link.validate(999999, Book(pages=1))
except ValidationError as e:
    print("VIOLATED: parent_link field performed existence check: %r" % e.messages)
    sys.exit(1)

# (b) None value on ordinary FK: must NOT raise
fk = Article._meta.get_field('author')
try:
    fk.validate(None, Article(title="T"))
except ValidationError as e:
    print("VIOLATED: None value raised: %r" % e.messages)
    sys.exit(1)

print("HOLDS: parent_link and None both early-exit without existence check")
sys.exit(0)
```

Attack 5 — `probe_5_standard_manager_and_field_match.py` → holds on the patched tree (good)

```python
"""Req3.5 + Req1.3: with a STANDARD default manager (base==default view),
validation of an ordinary FK must accept a value matching a stored row and
reject one that matches none — and the existence query must be RESTRICTED to
the referenced-field value (other, unrelated stored rows must NOT rescue a
non-matching value). HOLDS on both trees."""
import sys, types
import django
from django.conf import settings
p = types.ModuleType('p'); p.__path__ = ['/work']; sys.modules['p'] = p
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection
from django.core.exceptions import ValidationError


class Author(models.Model):  # standard default manager
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

a1 = Author.objects.create(name="A1")
a2 = Author.objects.create(name="A2")  # unrelated extra row
fk = Article._meta.get_field('author')

# matching value passes
try:
    fk.validate(a1.pk, Article(title="T", author=a1))
except ValidationError as e:
    print("VIOLATED: rejected a valid ordinary FK value: %r" % e.messages)
    sys.exit(1)

# non-matching value fails even though OTHER rows exist (query restricted to value)
missing = max(a1.pk, a2.pk) + 1000
try:
    fk.validate(missing, Article(title="T", author_id=missing))
    print("VIOLATED: accepted non-matching value %s despite other rows existing" % missing)
    sys.exit(1)
except ValidationError:
    pass

print("HOLDS: standard-manager FK accepts match, rejects non-match; query restricted to value")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_positive_hidden_row.py`

```python
"""Positive control / Req1.1,1.2,1.5: FK validate() must accept a value that
points at a genuinely stored target row that the target model's DEFAULT manager
hides (archived=True). HOLDS on patched (uses _base_manager), FAILS at base
(uses _default_manager -> ValidationError)."""
import sys, types
import django
from django.conf import settings

# register a synthetic app package 'p' so models can live in it
p = types.ModuleType('p')
p.__path__ = ['/work']
sys.modules['p'] = p

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection
from django.core.exceptions import ValidationError


class AuthorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Author(models.Model):
    name = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    objects = AuthorManager()

    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

# archived author: hidden by default manager, present in base manager
a = Author.objects.create(name="Randy", archived=True)
# sanity: default manager hides it
assert Author.objects.filter(pk=a.pk).count() == 0, "default manager should hide archived"
assert Author._base_manager.filter(pk=a.pk).count() == 1

art = Article(title="T", author=a)
fk = Article._meta.get_field('author')
try:
    fk.validate(a.pk, art)
    print("HOLDS: FK.validate accepted hidden (archived) target row pk=%s" % a.pk)
    sys.exit(0)
except ValidationError as e:
    print("VIOLATED: FK.validate rejected an existing but hidden row: %r" % (e.messages,))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13109 (Django 3.2). Gold fix: ForeignKey.validate() builds its existence query from the target model's _base_manager instead of _default_manager, so a value pointing at a genuinely stored row that a custom default manager hides (e.g. archived=True) is accepted.

Probe suite (all run in the official image; results below):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.5): archived Author hidden by a custom default manager; FK.validate(pk) must accept it. HOLDS patched, VIOLATED at base ('author instance with id 1 does not exist.'). Discriminates. Also REJECTS weak_noop candidate.
- probe_2 (Req2.1/2.2/2.3): non-existent value -> ValidationError with code='invalid' and params {model, field, value, pk}; pk==value==999. HOLDS patched AND base (regression).
- probe_3 (Req1.4/2.1): limit_choices_to enforced on the existence query — a row matching the FK value but failing limit_choices_to is rejected, one satisfying it passes. HOLDS patched AND base. REJECTS weak_drop_limit candidate.
- probe_4 (Req3.1/3.2): parent_link FK early-exits (no existence check even for a bogus value); None value early-exits after base validation. HOLDS patched AND base.
- probe_5 (Req3.5/1.3): standard default manager (base==default) — matching value passes, non-matching value fails even with other unrelated rows present (query restricted to the referenced-field value). HOLDS patched AND base.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite => suite discriminates):
- weak_drop_limit.diff: switches to _base_manager (satisfies the core) but drops the qs.complex_filter(get_limit_choices_to()) line. REJECTED by probe_3 ('accepted a row that fails limit_choices_to').
- weak_noop.diff: comment-only, leaves _default_manager (lazy non-fix). REJECTED by probe_1 (still rejects the hidden row).

No requirements-conforming-but-wrong candidate was found: every alternative that passes the full probe suite must (a) query _base_manager restricted to the value, (b) apply limit_choices_to, (c) preserve early-exits and the invalid-error params — which is exactly the gold behavior. All 5 probes hold on the gold-patched tree; positive control fails at base. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_positive_hidden_row.py`, `probe_2_reject_nonexistent.py`, `probe_3_limit_choices_to.py`, `probe_4_parent_link_and_none.py`, `probe_5_standard_manager_and_field_match.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_positive_hidden_row.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_positive_hidden_row.py` → holds on the patched tree (good)

Attack 2 — `probe_2_reject_nonexistent.py` → holds on the patched tree (good)

Attack 3 — `probe_3_limit_choices_to.py` → holds on the patched tree (good)

Attack 4 — `probe_4_parent_link_and_none.py` → holds on the patched tree (good)

Attack 5 — `probe_5_standard_manager_and_field_match.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_positive_hidden_row.py`

```python
"""Positive control / Req1.1,1.2,1.5: FK validate() must accept a value that
points at a genuinely stored target row that the target model's DEFAULT manager
hides (archived=True). HOLDS on patched (uses _base_manager), FAILS at base
(uses _default_manager -> ValidationError)."""
import sys, types
import django
from django.conf import settings

# register a synthetic app package 'p' so models can live in it
p = types.ModuleType('p')
p.__path__ = ['/work']
sys.modules['p'] = p

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'p'],
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection
from django.core.exceptions import ValidationError


class AuthorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Author(models.Model):
    name = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    objects = AuthorManager()

    class Meta:
        app_label = 'p'


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        app_label = 'p'


with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Article)

# archived author: hidden by default manager, present in base manager
a = Author.objects.create(name="Randy", archived=True)
# sanity: default manager hides it
assert Author.objects.filter(pk=a.pk).count() == 0, "default manager should hide archived"
assert Author._base_manager.filter(pk=a.pk).count() == 1

art = Article(title="T", author=a)
fk = Article._meta.get_field('author')
try:
    fk.validate(a.pk, art)
    print("HOLDS: FK.validate accepted hidden (archived) target row pk=%s" % a.pk)
    sys.exit(0)
except ValidationError as e:
    print("VIOLATED: FK.validate rejected an existing but hidden row: %r" % (e.messages,))
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13109 (Django 3.2). Gold fix: ForeignKey.validate() builds its existence query from the target model's _base_manager instead of _default_manager, so a value pointing at a genuinely stored row that a custom default manager hides (e.g. archived=True) is accepted.

Probe suite (all run in the official image; results below):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.5): archived Author hidden by a custom default manager; FK.validate(pk) must accept it. HOLDS patched, VIOLATED at base ('author instance with id 1 does not exist.'). Discriminates. Also REJECTS weak_noop candidate.
- probe_2 (Req2.1/2.2/2.3): non-existent value -> ValidationError with code='invalid' and params {model, field, value, pk}; pk==value==999. HOLDS patched AND base (regression).
- probe_3 (Req1.4/2.1): limit_choices_to enforced on the existence query — a row matching the FK value but failing limit_choices_to is rejected, one satisfying it passes. HOLDS patched AND base. REJECTS weak_drop_limit candidate.
- probe_4 (Req3.1/3.2): parent_link FK early-exits (no existence check even for a bogus value); None value early-exits after base validation. HOLDS patched AND base.
- probe_5 (Req3.5/1.3): standard default manager (base==default) — matching value passes, non-matching value fails even with other unrelated rows present (query restricted to the referenced-field value). HOLDS patched AND base.

Candidate wrong-fix patches (both apply at base_commit, both REJECTED by the suite => suite discriminates):
- weak_drop_limit.diff: switches to _base_manager (satisfies the core) but drops the qs.complex_filter(get_limit_choices_to()) line. REJECTED by probe_3 ('accepted a row that fails limit_choices_to').
- weak_noop.diff: comment-only, leaves _default_manager (lazy non-fix). REJECTED by probe_1 (still rejects the hidden row).

No requirements-conforming-but-wrong candidate was found: every alternative that passes the full probe suite must (a) query _base_manager restricted to the value, (b) apply limit_choices_to, (c) preserve early-exits and the invalid-error params — which is exactly the gold behavior. All 5 probes hold on the gold-patched tree; positive control fails at base. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified the full patched ForeignKey.validate() source inside the instance image via nl_attack probe (inspect.getsource). The method body matches: parent_link guard, super().validate, None guard, db_for_read routing, _base_manager.using(using).filter(**{field_name: value}), complex_filter(get_limit_choices_to()), and the 'invalid' ValidationError with params model/pk(=value, backwards-compat)/field/value. Issue (problem_statement) describes the archived-article/base-manager scenario, which R1.2 captures faithfully. Requirements correctly model the changed behavior, not an over-narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes ForeignKey.validate() behavior in terms already public via the problem_statement (base vs default manager, custom manager with get_queryset filter, archived-row example, spurious 'does not exist' error) and the visible source module django/db/models/fields/related.py. Elements not spelled out in the problem_statement (limit_choices_to/complex_filter, error code `invalid`, the pk param, parent-link and None early exits, db_for_read routing) are all derivable from the existing validate() source code, not from the hidden tests — legitimate change localization. No test function names/classes/paths (test_FK_validates_using_base_manager, ModelFormBasicTests, WriterManager/AuthorManager, the 'Select a valid choice...' assertion), no parametrization ids, no quoted test or gold code, and no fix-invented identifiers (the gold edit is a single-token _default_manager->_base_manager swap; both are public API). Requirements 1 and 2 translate the two FAIL_TO_PASS behaviors into behavioral requirements rather than transmitting the tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
