# P2 adversarial audit — django__django-14752

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
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 1: Req 1.1/1.2/1.3 serialize_result extension point exists & correct ---
import inspect
V=AutocompleteJsonView
assert hasattr(V,'serialize_result'), "no serialize_result method (Req1.1)"
sig=inspect.signature(V.serialize_result)
params=[p for p in sig.parameters]  # includes self
print("signature params:", params)
assert len(params)==3, "expected (self,obj,to_field_name), got %r"%params
site=make_site()
view=V(); view.admin_site=site
a=Author.objects.create(name="Zed", code="Z9")
out=view.serialize_result(a, 'code')
print("serialize_result(a,'code') ->", out)
assert isinstance(out, dict), "must return dict"
assert out.get('id')==str(getattr(a,'code')), "id must be str(getattr(obj,to_field)): %r"%out
assert out.get('text')==str(a), "text must be str(obj): %r"%out
out2=view.serialize_result(a,'id')
assert out2.get('id')==str(a.id), "id must follow to_field_name arg: %r"%out2
print("PROBE1_OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 2: Req 2.1/2.3/1.4 get() delegates to overriding serialize_result ---
class CustomView(AutocompleteJsonView):
    def serialize_result(self, obj, to_field_name):
        base=super().serialize_result(obj, to_field_name)
        return {**base, 'extra': 'notes:'+obj.name}
site=make_site()
for n in ["Ann","Amy","Abe"]:
    Author.objects.create(name=n, code="C"+n)
resp=call_view(CustomView, site, field_model='book', term='A')
data=json.loads(resp.content.decode())
print("status", resp.status_code)
print("results", data['results'])
assert resp.status_code==200
res=data['results']
assert len(res)==3, "expected 3 results, got %d"%len(res)
for entry in res:
    assert 'extra' in entry, "override key missing (Req1.4/2.3): %r"%entry
    assert 'id' in entry and 'text' in entry, "default keys must remain: %r"%entry
    assert entry['extra']=='notes:'+entry['text']
print("PROBE2_OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 3: Req 3.1/3.2/3.3 default response contract ---
site=make_site()
for i in range(3):
    Author.objects.create(name="Bob%d"%i, code="b%d"%i)
resp=call_view(AutocompleteJsonView, site, field_model='book', term='Bob')
assert resp.status_code==200, "status must be 200"
assert resp['Content-Type']=='application/json', resp['Content-Type']
data=json.loads(resp.content.decode())
print("keys", sorted(data.keys()))
assert set(data.keys())=={'results','pagination'}, data.keys()
assert isinstance(data['results'], list)
for e in data['results']:
    assert set(e.keys())=={'id','text'}, "entry must have exactly id,text: %r"%e
assert 'more' in data['pagination']
assert isinstance(data['pagination']['more'], bool), "more must be bool: %r"%data['pagination']
print("results", data['results'], "pag", data['pagination'])
assert len(data['results'])==3
print("PROBE3_OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 4: Req 3.4/4.5 id = str(getattr(obj, resolved_to_field)); to_field resolution honored ---
site=make_site()
a=Author.objects.create(name="Carol", code="XYZ123")
# BookByCode has FK to Author.to_field='code'
resp=call_view(AutocompleteJsonView, site, field_model='bookbycode', term='Carol')
assert resp.status_code==200, resp.status_code
data=json.loads(resp.content.decode())
print("results", data['results'])
assert len(data['results'])==1
entry=data['results'][0]
# id must be the 'code' value, NOT the pk
assert entry['id']==str(a.code)=="XYZ123", "id must be to_field(code) value: %r"%entry
assert entry['id']!=str(a.pk), "id must NOT be pk when to_field differs"
assert entry['text']==str(a)
print("PROBE4_OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 5: Req 3.2/4.7 pagination 'more' flag via ModelAdmin paginator + page size ---
site=make_site()
# paginate_by default 20; create 25 matching authors
for i in range(25):
    Author.objects.create(name="Dan%02d"%i, code="d%02d"%i)
# page 1 -> more True
r1=call_view(AutocompleteJsonView, site, field_model='book', term='Dan', page=1)
d1=json.loads(r1.content.decode())
print("page1 n=", len(d1['results']), "more=", d1['pagination']['more'])
assert d1['pagination']['more'] is True, "page1 should have more=True"
assert len(d1['results'])==20, "page size 20 expected, got %d"%len(d1['results'])
# page 2 -> more False (25 total -> 5 remain)
r2=call_view(AutocompleteJsonView, site, field_model='book', term='Dan', page=2)
d2=json.loads(r2.content.decode())
print("page2 n=", len(d2['results']), "more=", d2['pagination']['more'])
assert d2['pagination']['more'] is False, "page2 should have more=False"
assert len(d2['results'])==5
print("PROBE5_OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 6: Req 4.1/4.2/4.4 validation & permission & no-search-fields behavior preserved ---
from django.core.exceptions import PermissionDenied
from django.http import Http404
site=make_site()
Author.objects.create(name="Eve", code="e1")

def expect_perm_denied(label, req):
    req.user_checked=True
    try:
        AutocompleteJsonView.as_view(admin_site=site)(req)
        return False
    except PermissionDenied:
        return True

# (a) missing field_name param -> PermissionDenied (Req4.1)
req=_factory.get('/autocomplete/', {'term':'','app_label':'contenttypes','model_name':'book'})
req.user=_su
r=expect_perm_denied('missing field_name', req)
print("missing field_name -> PermissionDenied:", r)
assert r, "Req4.1: missing field_name must raise PermissionDenied"

# (b) non-superuser lacking perms -> permission-denied, NO results (Req4.2)
from django.contrib.auth.models import User
plain=User.objects.create_user('plain','p@p.com','pw')
returned_results=None
raised=False
try:
    resp=call_view(AutocompleteJsonView, site, field_model='book', term='', user=plain)
    d=json.loads(resp.content.decode())
    returned_results = d.get('results')
    print("no-perm status:", resp.status_code, "body:", d)
    # if it did not raise, it must be a 403 and must NOT contain results
    assert resp.status_code==403, "no-perm must be permission-denied (403 or raise)"
    assert 'results' not in d, "must not return results"
except PermissionDenied:
    raised=True
    print("no-perm -> PermissionDenied raised")
assert raised or (returned_results is None), "Req4.2: lacking perm must deny & not return results"

# (c) admin with NO search_fields -> Http404 (Req4.4)
site2=admin.AdminSite(name='auto2')
class NoSearchAuthorAdmin(admin.ModelAdmin):
    search_fields=[]
class BookAdmin2(admin.ModelAdmin):
    autocomplete_fields=['author']
site2.register(Author, NoSearchAuthorAdmin)
site2.register(Book, BookAdmin2)
raised404=False
try:
    call_view(AutocompleteJsonView, site2, field_model='book', term='')
except Http404:
    raised404=True
print("no search_fields -> Http404:", raised404)
assert raised404, "Req4.4: no search_fields must raise Http404"
print("PROBE6_OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 1: Req 1.1/1.2/1.3 serialize_result extension point exists & correct ---
import inspect
V=AutocompleteJsonView
assert hasattr(V,'serialize_result'), "no serialize_result method (Req1.1)"
sig=inspect.signature(V.serialize_result)
params=[p for p in sig.parameters]  # includes self
print("signature params:", params)
assert len(params)==3, "expected (self,obj,to_field_name), got %r"%params
site=make_site()
view=V(); view.admin_site=site
a=Author.objects.create(name="Zed", code="Z9")
out=view.serialize_result(a, 'code')
print("serialize_result(a,'code') ->", out)
assert isinstance(out, dict), "must return dict"
assert out.get('id')==str(getattr(a,'code')), "id must be str(getattr(obj,to_field)): %r"%out
assert out.get('text')==str(a), "text must be str(obj): %r"%out
out2=view.serialize_result(a,'id')
assert out2.get('id')==str(a.id), "id must follow to_field_name arg: %r"%out2
print("PROBE1_OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14752 (admin AutocompleteJsonView serialize_result extension point). No verifier; probes executed in the official image on base/gold-patched/candidate trees via nl_attack.

Harness (inlined in every probe): configures a minimal in-memory Django (contenttypes/auth/admin), defines Author(name,code-unique)+Book(FK->pk)+BookByCode(FK to_field='code'), registers an AdminSite with search_fields/autocomplete_fields, and drives AutocompleteJsonView.as_view(admin_site=site) with RequestFactory. End-to-end response construction confirmed working.

Probes (each standalone python, exit 0 iff criterion holds):
- probe_1 (POSITIVE CONTROL) — Req 1.1/1.2/1.3: serialize_result exists as bound instance method sig (self,obj,to_field_name), returns {id:str(getattr(obj,to_field)), text:str(obj)} and honors the to_field_name arg. HOLDS patched; FAILS at base (no such method) => discriminating.
- probe_2 — Req 2.1/2.3/1.4: a subclass overriding serialize_result to add 'extra' key => the endpoint's results entries all carry that key alongside id/text; proves get() dispatches to the (overriding) method rather than an inline dict. HOLDS patched; FAILS at base.
- probe_3 — Req 3.1/3.2/3.3: default response is JSON 200, keys exactly {results,pagination}, each entry exactly {id,text}, pagination.more is a bool. HOLDS both trees (regression).
- probe_4 — Req 3.4/4.5: with FK to a non-pk unique to_field ('code'), id equals str(getattr(obj,'code')) and NOT the pk. HOLDS both trees (regression).
- probe_5 — Req 3.2/4.7: 25 matches, paginate_by 20 => page1 more=True/len 20, page2 more=False/len 5. HOLDS both trees (regression).
- probe_6 — Req 4.1/4.2/4.4: missing field_name => PermissionDenied; non-superuser lacking view perm => permission-denied and no results; admin with empty search_fields => Http404. HOLDS both trees (regression).

All 6 probes HOLD on the gold-patched tree. Positive control failed at base and holds patched (prepatch_reproduced=true).

Candidate wrong-fix patches (both apply at base_commit; runner re-checks):
- weak_A (adds serialize_result but does NOT wire get() to call it — leaves inline dict): REJECTED by probe_2 (override has no effect; get() still builds inline). Also would not resolve the hidden test which asserts the override propagates.
- weak_B (wires get() -> serialize_result but the method uses str(obj.pk) instead of str(getattr(obj,to_field_name))): REJECTED by probe_1 (ignores to_field arg) and probe_4 (id becomes pk not the to_field value). Would break custom-to_field behavior.

Suite discriminates wrong implementations in two independent directions (dispatch wiring; to_field fidelity). No probe-conforming alternative patch found that would fail to resolve => no TOO-WEAK finding. Verdict advisory: SOUND.

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
# ---- shared harness (inlined into each probe) ----
import json, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        MIDDLEWARE=[], DEFAULT_AUTO_FIELD='django.db.models.AutoField', ROOT_URLCONF=None,
    )
    django.setup()
from django.db import models, connection
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.management import call_command

class Author(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    class Meta:
        app_label='contenttypes'
        ordering=['id']
    def __str__(self): return self.name
class Book(models.Model):
    # default FK -> pk
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'
class BookByCode(models.Model):
    # FK to a non-pk unique field -> exercises to_field resolution
    author = models.ForeignKey(Author, to_field='code', on_delete=models.CASCADE)
    class Meta: app_label='contenttypes'

with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(Book); se.create_model(BookByCode)
call_command('migrate', run_syncdb=True, verbosity=0)

_su = User.objects.create_superuser('admin','a@a.com','pw')
_factory = RequestFactory()

def make_site(author_admin_cls=None):
    site = admin.AdminSite(name='auto')
    class AuthorAdmin(admin.ModelAdmin):
        search_fields=['name']
    class BookAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    class BookByCodeAdmin(admin.ModelAdmin):
        autocomplete_fields=['author']
    site.register(Author, author_admin_cls or AuthorAdmin)
    site.register(Book, BookAdmin)
    site.register(BookByCode, BookByCodeAdmin)
    return site

def call_view(view_cls, site, *, field_model='book', field_name='author', term='',
              page=None, user=None):
    params={'term':term,'app_label':'contenttypes','model_name':field_model,'field_name':field_name}
    if page is not None: params['page']=str(page)
    req=_factory.get('/autocomplete/', params)
    req.user = _su if user is None else user
    resp=view_cls.as_view(admin_site=site)(req)
    return resp
# --- Probe 1: Req 1.1/1.2/1.3 serialize_result extension point exists & correct ---
import inspect
V=AutocompleteJsonView
assert hasattr(V,'serialize_result'), "no serialize_result method (Req1.1)"
sig=inspect.signature(V.serialize_result)
params=[p for p in sig.parameters]  # includes self
print("signature params:", params)
assert len(params)==3, "expected (self,obj,to_field_name), got %r"%params
site=make_site()
view=V(); view.admin_site=site
a=Author.objects.create(name="Zed", code="Z9")
out=view.serialize_result(a, 'code')
print("serialize_result(a,'code') ->", out)
assert isinstance(out, dict), "must return dict"
assert out.get('id')==str(getattr(a,'code')), "id must be str(getattr(obj,to_field)): %r"%out
assert out.get('text')==str(a), "text must be str(obj): %r"%out
out2=view.serialize_result(a,'id')
assert out2.get('id')==str(a.id), "id must follow to_field_name arg: %r"%out2
print("PROBE1_OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14752 (admin AutocompleteJsonView serialize_result extension point). No verifier; probes executed in the official image on base/gold-patched/candidate trees via nl_attack.

Harness (inlined in every probe): configures a minimal in-memory Django (contenttypes/auth/admin), defines Author(name,code-unique)+Book(FK->pk)+BookByCode(FK to_field='code'), registers an AdminSite with search_fields/autocomplete_fields, and drives AutocompleteJsonView.as_view(admin_site=site) with RequestFactory. End-to-end response construction confirmed working.

Probes (each standalone python, exit 0 iff criterion holds):
- probe_1 (POSITIVE CONTROL) — Req 1.1/1.2/1.3: serialize_result exists as bound instance method sig (self,obj,to_field_name), returns {id:str(getattr(obj,to_field)), text:str(obj)} and honors the to_field_name arg. HOLDS patched; FAILS at base (no such method) => discriminating.
- probe_2 — Req 2.1/2.3/1.4: a subclass overriding serialize_result to add 'extra' key => the endpoint's results entries all carry that key alongside id/text; proves get() dispatches to the (overriding) method rather than an inline dict. HOLDS patched; FAILS at base.
- probe_3 — Req 3.1/3.2/3.3: default response is JSON 200, keys exactly {results,pagination}, each entry exactly {id,text}, pagination.more is a bool. HOLDS both trees (regression).
- probe_4 — Req 3.4/4.5: with FK to a non-pk unique to_field ('code'), id equals str(getattr(obj,'code')) and NOT the pk. HOLDS both trees (regression).
- probe_5 — Req 3.2/4.7: 25 matches, paginate_by 20 => page1 more=True/len 20, page2 more=False/len 5. HOLDS both trees (regression).
- probe_6 — Req 4.1/4.2/4.4: missing field_name => PermissionDenied; non-superuser lacking view perm => permission-denied and no results; admin with empty search_fields => Http404. HOLDS both trees (regression).

All 6 probes HOLD on the gold-patched tree. Positive control failed at base and holds patched (prepatch_reproduced=true).

Candidate wrong-fix patches (both apply at base_commit; runner re-checks):
- weak_A (adds serialize_result but does NOT wire get() to call it — leaves inline dict): REJECTED by probe_2 (override has no effect; get() still builds inline). Also would not resolve the hidden test which asserts the override propagates.
- weak_B (wires get() -> serialize_result but the method uses str(obj.pk) instead of str(getattr(obj,to_field_name))): REJECTED by probe_1 (ignores to_field arg) and probe_4 (id becomes pk not the to_field value). Would break custom-to_field behavior.

Suite discriminates wrong implementations in two independent directions (dispatch wiring; to_field fidelity). No probe-conforming alternative patch found that would fail to resolve => no TOO-WEAK finding. Verdict advisory: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch is a pure extract-method refactor of AutocompleteJsonView.get(): it lifts the inline `{'id': str(getattr(obj, to_field_name)), 'text': str(obj)}` dict into a new overridable serialize_result(self, obj, to_field_name) and calls it in the results comprehension. The requirements pin exactly this changed observable behavior — not a narrower slice: Req1 pins the method's signature/return, Req2 pins get()'s delegation and ordering, Req4.5 correctly requires the resolved to_field_name to be passed as the method argument (matching the diff), and Req1.4/2.3 pin the override propagation that the F2P test test_serialize_result exercises (subclass adds 'posted' via super().serialize_result). Req3 pins the unchanged default contract. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior, correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit (the serialize_result(self, obj, to_field_name) method, its exact body, and the `notes` override example) is fully present in the PUBLIC problem_statement, so the doc's description of an overridable per-object serialization method and merging extra keys is derivable from public material, not the hidden tests. The requirements deliberately avoid even naming `serialize_result` (calling it 'the extension point'). None of the hidden test's distinguishing specifics leak: no `posted` field, no `datetime.date(2021,8,9)`, no `Question` objects, no `order_by('-posted')`, no test/class names (test_serialize_result, AutocompleteJsonSerializeResultView), no file path. Requirement 4's enumeration of error conditions and query behavior mirrors PASS_TO_PASS coverage but is described as behavioral guarantees of the endpoint (all inherent, public behavior), not test cases. No case-enumeration reconstructs the parametrization. Naming AutocompleteJsonView / get() / to_field resolution is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
