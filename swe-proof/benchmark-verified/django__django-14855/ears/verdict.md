# P2 adversarial audit — django__django-14855

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / criteria 1,2,3: readonly FK link on a CUSTOM admin site
resolves under that site's namespace + URL prefix (/custom-admin/...)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.admin",
        "django.contrib.messages",
        "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__",
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


custom_site = AdminSite(name="custom-admin")
custom_site.register(Author)
custom_site.register(Book)

from django.contrib import admin as default_admin
default_admin.site.register(Author)
default_admin.site.register(Book)

urlpatterns = [
    path("admin/", default_admin.site.urls),
    path("custom-admin/", custom_site.urls),
]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = custom_site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=7, name="Jane")

html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
print("custom-site html:", html)

ok = ("/custom-admin/probeapp/author/7/change/" in html) and html.startswith("<a href=")
if not ok:
    print("FAIL: link did not resolve under custom site namespace/prefix")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Criterion R1.4 (regression): on the DEFAULT admin site the link still
resolves under the default 'admin' namespace and /admin/ prefix."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.admin",
        "django.contrib.messages", "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__", USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


custom_site = AdminSite(name="custom-admin")
custom_site.register(Author); custom_site.register(Book)
from django.contrib import admin as default_admin
default_admin.site.register(Author); default_admin.site.register(Book)

urlpatterns = [
    path("admin/", default_admin.site.urls),
    path("custom-admin/", custom_site.urls),
]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = default_admin.site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=7, name="Jane")
html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
print("default-site html:", html)

ok = ("/admin/probeapp/author/7/change/" in html) and ("/custom-admin/" not in html) and html.startswith("<a href=")
if not ok:
    print("FAIL: default site link wrong")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Criterion R1.5: string PK requiring URL-encoding is quoted, AND namespace
resolution of R1.3 still applies (custom site prefix present)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.admin",
        "django.contrib.messages", "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__", USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class SKey(models.Model):
    key = models.CharField(max_length=50, primary_key=True)
    class Meta:
        app_label = "probeapp"


class Ref(models.Model):
    parent = models.ForeignKey(SKey, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


custom_site = AdminSite(name="custom-admin")
custom_site.register(SKey); custom_site.register(Ref)

urlpatterns = [path("custom-admin/", custom_site.urls)]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = custom_site._registry[Ref]


remote_field = Ref._meta.get_field("parent").remote_field
# pk with a character needing url-encoding
obj = SKey(pk="a b/c")
import re
html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, obj)
print("string-pk html:", html)

# Extract the href only (visible text legitimately contains the raw pk).
m = re.search(r'href="([^"]*)"', html)
href = m.group(1) if m else ""
print("href:", href)

# custom-admin namespace/prefix present in the href
ok = ("/custom-admin/probeapp/skey/" in href) and html.startswith("<a href=")
# pk must be url-encoded in the href: raw 'a b/c' path segment must NOT appear
ok = ok and ("a b/c" not in href)
# an encoded form must appear (space -> %20, '/' -> admin quote _2F)
ok = ok and ("%20" in href or "_2F" in href or "%2F" in href)
if not ok:
    print("FAIL: string pk not encoded and/or namespace not applied")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Criteria R2.3 / R2.4: when related model is NOT registered (NoReverseMatch),
get_admin_url must NOT raise and returns plain-text display (no anchor)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.admin",
        "django.contrib.messages", "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__", USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return "AUTHOR-%s" % self.pk
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


# register only Book, NOT Author -> reverse for author change fails
custom_site = AdminSite(name="custom-admin")
custom_site.register(Book)

urlpatterns = [path("custom-admin/", custom_site.urls)]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = custom_site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=7)
try:
    html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
except Exception as e:
    print("FAIL: raised", repr(e))
    sys.exit(1)
print("unregistered html:", repr(html))

ok = ("<a " not in html) and ("href" not in html) and (html == "AUTHOR-7")
if not ok:
    print("FAIL: expected plain-text fallback")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Criteria R2.1 / R2.2: route name is built from related model's app_label and
model_name (admin:<app>_<model>_change) and returns an anchor whose visible text
is the related object's str(). Checked on default site."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.admin",
        "django.contrib.messages", "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__", USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return "MY-DISPLAY-TEXT"
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


from django.contrib import admin as default_admin
default_admin.site.register(Author); default_admin.site.register(Book)

urlpatterns = [path("admin/", default_admin.site.urls)]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = default_admin.site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=42)
html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
print("html:", html)

# route based on app_label 'probeapp' and model_name 'author'
ok = ("/admin/probeapp/author/42/change/" in html)
# anchor + visible display text
ok = ok and html.startswith("<a href=") and (">MY-DISPLAY-TEXT</a>" in html)
if not ok:
    print("FAIL: route-name construction or anchor text wrong")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / criteria 1,2,3: readonly FK link on a CUSTOM admin site
resolves under that site's namespace + URL prefix (/custom-admin/...)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.admin",
        "django.contrib.messages",
        "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__",
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


custom_site = AdminSite(name="custom-admin")
custom_site.register(Author)
custom_site.register(Book)

from django.contrib import admin as default_admin
default_admin.site.register(Author)
default_admin.site.register(Book)

urlpatterns = [
    path("admin/", default_admin.site.urls),
    path("custom-admin/", custom_site.urls),
]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = custom_site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=7, name="Jane")

html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
print("custom-site html:", html)

ok = ("/custom-admin/probeapp/author/7/change/" in html) and html.startswith("<a href=")
if not ok:
    print("FAIL: link did not resolve under custom site namespace/prefix")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: get_admin_url passes current_app=self.model_admin.admin_site.name to reverse(). Probes cover: (1) POSITIVE CONTROL — custom admin site link resolves under /custom-admin/ namespace (HOLDS patched, FAILS at base producing /admin/... -> discriminates, R1.1-1.3); (2) default site regression -> /admin/ prefix (R1.4); (3) string PK url-encoded in href AND namespace still applied, checking only the href since visible anchor text legitimately contains the raw pk (R1.5); (4) unregistered related model -> NoReverseMatch swallowed, plain-text fallback, no anchor (R2.3/R2.4); (5) route-name from app_label/model_name + anchor visible text = str(obj) (R2.1/R2.2). All 5 HOLD on gold-patched tree. Candidate wrong-fix 'weak_hardcoded' hard-codes current_app='admin' (a lazy reading of 'pass the current admin site' that ignores criterion R1.2 requiring derivation from the model admin): probe_1 REJECTS it (link resolves to /admin/ on the custom site), while probes 2-5 pass — demonstrating the suite discriminates the too-weak/wrong implementation. Positive control verified to fail at base and hold patched.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / criteria 1,2,3: readonly FK link on a CUSTOM admin site
resolves under that site's namespace + URL prefix (/custom-admin/...)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.admin",
        "django.contrib.messages",
        "django.contrib.sessions",
    ],
    ROOT_URLCONF="__main__",
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.contrib.admin import AdminSite
from django.urls import path


class Author(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta:
        app_label = "probeapp"


custom_site = AdminSite(name="custom-admin")
custom_site.register(Author)
custom_site.register(Book)

from django.contrib import admin as default_admin
default_admin.site.register(Author)
default_admin.site.register(Book)

urlpatterns = [
    path("admin/", default_admin.site.urls),
    path("custom-admin/", custom_site.urls),
]

from django.contrib.admin.helpers import AdminReadonlyField


class FakeField:
    model_admin = custom_site._registry[Book]


remote_field = Book._meta.get_field("author").remote_field
author = Author(pk=7, name="Jane")

html = AdminReadonlyField.get_admin_url(FakeField(), remote_field, author)
print("custom-site html:", html)

ok = ("/custom-admin/probeapp/author/7/change/" in html) and html.startswith("<a href=")
if not ok:
    print("FAIL: link did not resolve under custom site namespace/prefix")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: get_admin_url passes current_app=self.model_admin.admin_site.name to reverse(). Probes cover: (1) POSITIVE CONTROL — custom admin site link resolves under /custom-admin/ namespace (HOLDS patched, FAILS at base producing /admin/... -> discriminates, R1.1-1.3); (2) default site regression -> /admin/ prefix (R1.4); (3) string PK url-encoded in href AND namespace still applied, checking only the href since visible anchor text legitimately contains the raw pk (R1.5); (4) unregistered related model -> NoReverseMatch swallowed, plain-text fallback, no anchor (R2.3/R2.4); (5) route-name from app_label/model_name + anchor visible text = str(obj) (R2.1/R2.2). All 5 HOLD on gold-patched tree. Candidate wrong-fix 'weak_hardcoded' hard-codes current_app='admin' (a lazy reading of 'pass the current admin site' that ignores criterion R1.2 requiring derivation from the model admin): probe_1 REJECTS it (link resolves to /admin/ on the custom site), while probes 2-5 pass — demonstrating the suite discriminates the too-weak/wrong implementation. Positive control verified to fail at base and hold patched.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via inspect.getsource on both patched and base trees. Requirements correctly model the changed observable behavior (namespace-correct URL resolution) rather than a narrow slice, and enumerate the preserved invariants accurately.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement. The problem_statement already discloses the file (helpers.py), method (get_admin_url), the exact defective line reverse(url_name, args=[quote(remote_obj.pk)]), the precise fix current_app=self.model_admin.admin_site.name, NoReverseMatch handling, and the /admin/ vs /custom-admin/ default-vs-custom distinction. The doc reuses only these public facts plus generic behavioral translation. No hidden-test artifacts leak: test names (test_readonly_foreignkey_links_custom_admin_site/_default_admin_site), the 'namespaced_admin' namespace, site2, models ReadOnlyRelatedField/Language, ReadOnlyRelatedFieldAdmin, and fixture strings ('super','Chapter 1') are all absent. Req1#5 (string PK encoding) follows from the public quote(remote_obj.pk); Req2#5's enumeration (ManyToMany, reverse OneToOne, text readonly) is generic documented admin behavior stated as a no-regression boundary, not a mirror of test parametrization ids or invented identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
