# P2 adversarial audit — django__django-15467

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 1 (criteria 1,2,3) + positive control:
When a FK is in radio_fields, no widget pre-supplied, model field allows blank,
and caller supplies empty_label in kwargs -> that empty_label survives unchanged
onto the constructed form field (formfield.empty_label == caller value), and the
field's empty choice displays that text.
HOLDS iff the custom empty_label is honored.
"""
import django
from django.conf import settings

if not settings.configured:
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
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib import admin


class Author(models.Model):
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    # blank=True => field allows blank
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        app_label = "probeapp"


site = admin.AdminSite()
db_field = Book._meta.get_field("author")

ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

CUSTOM = "MY CUSTOM EMPTY LABEL"
# supply an empty queryset to avoid any DB access when iterating choices
formfield = ma.formfield_for_foreignkey(
    db_field, request=None, empty_label=CUSTOM, queryset=Author.objects.none()
)

print("formfield.empty_label =", repr(formfield.empty_label))

# criterion 3: empty choice text should display custom label
choices = list(formfield.widget.choices) if hasattr(formfield.widget, "choices") else list(formfield.choices)
print("first choice =", repr(choices[0]) if choices else "NONE")

ok = (formfield.empty_label == CUSTOM)
# also check the rendered empty choice text
empty_choice_text = None
for val, label in choices:
    if val == "":
        empty_choice_text = label
        break
print("empty_choice_text =", repr(empty_choice_text))
ok = ok and (empty_choice_text == CUSTOM)

if ok:
    print("PASS: custom empty_label honored")
    raise SystemExit(0)
print("FAIL: custom empty_label NOT honored")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 2: radio-style blank FK, caller did NOT supply empty_label ->
empty_label defaults to translated "None". HOLDS iff default is "None".
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
            "django.contrib.admin","django.contrib.messages","django.contrib.sessions"],
        USE_TZ=True)
django.setup()
from django.db import models
from django.contrib import admin

class Author(models.Model):
    class Meta: app_label = "probeapp"
class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)
    class Meta: app_label = "probeapp"

site = admin.AdminSite()
db_field = Book._meta.get_field("author")
ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

formfield = ma.formfield_for_foreignkey(db_field, request=None, queryset=Author.objects.none())
print("formfield.empty_label =", repr(formfield.empty_label))
# default "None" - translated; compare to str(_("None"))
from django.utils.translation import gettext as _
expected = _("None")
print("expected default =", repr(expected))
if formfield.empty_label == expected:
    print("PASS: default empty_label is 'None'")
    raise SystemExit(0)
print("FAIL: default empty_label wrong")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3: radio-style FK whose model field does NOT allow blank ->
empty_label set to None, regardless of caller supplying empty_label. Field must
NOT present an empty choice. HOLDS iff empty_label is None even when caller
passes one.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
            "django.contrib.admin","django.contrib.messages","django.contrib.sessions"],
        USE_TZ=True)
django.setup()
from django.db import models
from django.contrib import admin

class Author(models.Model):
    class Meta: app_label = "probeapp"
class Book(models.Model):
    # blank=False (default) => does not allow blank
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)
    class Meta: app_label = "probeapp"

site = admin.AdminSite()
db_field = Book._meta.get_field("author")
print("db_field.blank =", db_field.blank)
ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

# caller supplies empty_label; must be ignored because non-blank
formfield = ma.formfield_for_foreignkey(
    db_field, request=None, empty_label="SHOULD BE IGNORED", queryset=Author.objects.none())
print("formfield.empty_label =", repr(formfield.empty_label))
choices = list(formfield.choices)
has_empty = any(val == "" for val, _lbl in choices)
print("has empty choice =", has_empty)
if formfield.empty_label is None and not has_empty:
    print("PASS: empty label suppressed for non-blank field")
    raise SystemExit(0)
print("FAIL: empty label not suppressed")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 4 (criteria 1,2): non-radio FK path unchanged. A FK NOT in
radio_fields must not gain an empty_label from the radio branch, and a caller
supplied empty_label for a non-radio FK is forwarded normally by ModelChoiceField
constructor (default handling). Also: when a widget IS supplied by caller for a
radio-eligible field name, radio branch logic is not applied.
We check: for a plain FK (not in radio_fields) the widget is NOT a radio widget
and empty_label defaults to the ModelChoiceField default ("---------"), i.e. the
radio-branch never touched it.
HOLDS iff non-radio path behaves as standard ModelChoiceField.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
            "django.contrib.admin","django.contrib.messages","django.contrib.sessions"],
        USE_TZ=True)
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.widgets import AdminRadioSelect

class Author(models.Model):
    class Meta: app_label = "probeapp"
class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)
    class Meta: app_label = "probeapp"

site = admin.AdminSite()
db_field = Book._meta.get_field("author")
ma = admin.ModelAdmin(Book, site)
# NOT adding to radio_fields => non-radio path
formfield = ma.formfield_for_foreignkey(db_field, request=None, queryset=Author.objects.none())
print("widget type =", type(formfield.widget).__name__)
print("empty_label =", repr(formfield.empty_label))
is_radio = isinstance(formfield.widget, AdminRadioSelect)
# default ModelChoiceField empty_label is "---------"
ok = (not is_radio) and (formfield.empty_label == "---------")
if ok:
    print("PASS: non-radio path unchanged (default empty_label, non-radio widget)")
    raise SystemExit(0)
print("FAIL: non-radio path altered")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4 criterion 4: preserve radio-widget selection and its CSS class
derivation for radio fields. For a radio FK, the widget must be an
AdminRadioSelect whose attrs class matches get_ul_class(HORIZONTAL/VERTICAL).
This is a "SHALL keep" regression criterion — must hold on patched tree.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
            "django.contrib.admin","django.contrib.messages","django.contrib.sessions"],
        USE_TZ=True)
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.widgets import AdminRadioSelect
from django.contrib.admin.options import get_ul_class

class Author(models.Model):
    class Meta: app_label = "probeapp"
class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)
    class Meta: app_label = "probeapp"

site = admin.AdminSite()
db_field = Book._meta.get_field("author")

results = []
for orient, name in [(admin.HORIZONTAL, "HORIZONTAL"), (admin.VERTICAL, "VERTICAL")]:
    ma = admin.ModelAdmin(Book, site)
    ma.radio_fields = {"author": orient}
    ff = ma.formfield_for_foreignkey(db_field, request=None, queryset=Author.objects.none())
    is_radio = isinstance(ff.widget, AdminRadioSelect)
    css = ff.widget.attrs.get("class")
    expected = get_ul_class(orient)
    print(f"{name}: radio={is_radio} class={css!r} expected={expected!r}")
    results.append(is_radio and css == expected)

if all(results):
    print("PASS: radio widget + css class preserved")
    raise SystemExit(0)
print("FAIL: radio widget/css derivation broken")
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 4 criterion 1: when a caller pre-supplies a `widget`, the radio
branch (incl. empty_label logic) SHALL NOT be applied even if the field is in
radio_fields. We supply a custom widget for a radio-eligible blank FK and check
the widget is kept as-is and NO radio empty_label was injected.
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth",
            "django.contrib.admin","django.contrib.messages","django.contrib.sessions"],
        USE_TZ=True)
django.setup()
from django.db import models
from django.contrib import admin
from django import forms

class Author(models.Model):
    class Meta: app_label = "probeapp"
class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)
    class Meta: app_label = "probeapp"

site = admin.AdminSite()
db_field = Book._meta.get_field("author")
ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

custom_widget = forms.Select(attrs={"data-probe": "yes"})
ff = ma.formfield_for_foreignkey(
    db_field, request=None, widget=custom_widget, queryset=Author.objects.none())
print("widget is our custom Select =", isinstance(ff.widget, forms.Select) and
      ff.widget.attrs.get("data-probe") == "yes")
print("empty_label =", repr(ff.empty_label))
# Since radio branch was skipped, empty_label was never forced to "None";
# ModelChoiceField default applies => "---------"
ok = (ff.widget.attrs.get("data-probe") == "yes") and (ff.empty_label == "---------")
if ok:
    print("PASS: supplied widget bypasses radio branch")
    raise SystemExit(0)
print("FAIL: radio branch wrongly applied despite supplied widget")
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1 (criteria 1,2,3) + positive control:
When a FK is in radio_fields, no widget pre-supplied, model field allows blank,
and caller supplies empty_label in kwargs -> that empty_label survives unchanged
onto the constructed form field (formfield.empty_label == caller value), and the
field's empty choice displays that text.
HOLDS iff the custom empty_label is honored.
"""
import django
from django.conf import settings

if not settings.configured:
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
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib import admin


class Author(models.Model):
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    # blank=True => field allows blank
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        app_label = "probeapp"


site = admin.AdminSite()
db_field = Book._meta.get_field("author")

ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

CUSTOM = "MY CUSTOM EMPTY LABEL"
# supply an empty queryset to avoid any DB access when iterating choices
formfield = ma.formfield_for_foreignkey(
    db_field, request=None, empty_label=CUSTOM, queryset=Author.objects.none()
)

print("formfield.empty_label =", repr(formfield.empty_label))

# criterion 3: empty choice text should display custom label
choices = list(formfield.widget.choices) if hasattr(formfield.widget, "choices") else list(formfield.choices)
print("first choice =", repr(choices[0]) if choices else "NONE")

ok = (formfield.empty_label == CUSTOM)
# also check the rendered empty choice text
empty_choice_text = None
for val, label in choices:
    if val == "":
        empty_choice_text = label
        break
print("empty_choice_text =", repr(empty_choice_text))
ok = ok and (empty_choice_text == CUSTOM)

if ok:
    print("PASS: custom empty_label honored")
    raise SystemExit(0)
print("FAIL: custom empty_label NOT honored")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 4 requirements. probe_1 (R1 crit 1/2/3 + positive control): custom empty_label survives onto radio blank FK field and its empty choice text — HOLDS gold (empty_label='MY CUSTOM EMPTY LABEL'), VIOLATED at base (empty_label='None'), so it discriminates. probe_2 (R2): default translated 'None' when caller omits empty_label — HOLDS gold. probe_3 (R3): non-blank radio FK gets empty_label=None even when caller passes one, no empty choice — HOLDS gold. probe_4 (R4 crit1/2): non-radio FK path unchanged (non-radio widget, default '---------' empty_label) — HOLDS. probe_5 (R4 crit4 regression): AdminRadioSelect widget + get_ul_class css preserved for HORIZONTAL and VERTICAL — HOLDS. probe_6 (R4 crit1): caller-supplied widget bypasses radio branch, no forced empty_label — HOLDS. All 6 HOLD on gold-patched tree.

CANDIDATE PATCHES: weak2 (empty_label = kwargs.get('empty_label') if blank else None) drops the _('None') default → REJECTED by probe_2 (VIOLATED, empty_label=None when caller omits), while probe_1/probe_3 still hold — demonstrates the suite discriminates a wrong fix on the R2 axis. weak1 (kwargs.get('empty_label', _('None')) with no db_field.blank guard) turned out behaviorally EQUIVALENT to gold: ModelChoiceField.__init__ itself sets empty_label=None when widget is RadioSelect and field is not blank, so all 6 probes HOLD under weak1 — it is NOT a too-weak finding (it would resolve the hidden tests). The R3 suppression is enforced by ModelChoiceField downstream, not solely by the options.py guard, so probe_3 cannot reject weak1; weak2 remains the discriminating rejected candidate.

Run matrix: gold = all HOLD; base = probe_1 VIOLATED (positive control fires); weak2 = probe_2 VIOLATED. Requirements are faithful and adequately strong given the ModelChoiceField semantics.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Requirement 1 (criteria 1,2,3) + positive control:
When a FK is in radio_fields, no widget pre-supplied, model field allows blank,
and caller supplies empty_label in kwargs -> that empty_label survives unchanged
onto the constructed form field (formfield.empty_label == caller value), and the
field's empty choice displays that text.
HOLDS iff the custom empty_label is honored.
"""
import django
from django.conf import settings

if not settings.configured:
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
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.contrib import admin


class Author(models.Model):
    class Meta:
        app_label = "probeapp"


class Book(models.Model):
    # blank=True => field allows blank
    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        app_label = "probeapp"


site = admin.AdminSite()
db_field = Book._meta.get_field("author")

ma = admin.ModelAdmin(Book, site)
ma.radio_fields = {"author": admin.HORIZONTAL}

CUSTOM = "MY CUSTOM EMPTY LABEL"
# supply an empty queryset to avoid any DB access when iterating choices
formfield = ma.formfield_for_foreignkey(
    db_field, request=None, empty_label=CUSTOM, queryset=Author.objects.none()
)

print("formfield.empty_label =", repr(formfield.empty_label))

# criterion 3: empty choice text should display custom label
choices = list(formfield.widget.choices) if hasattr(formfield.widget, "choices") else list(formfield.choices)
print("first choice =", repr(choices[0]) if choices else "NONE")

ok = (formfield.empty_label == CUSTOM)
# also check the rendered empty choice text
empty_choice_text = None
for val, label in choices:
    if val == "":
        empty_choice_text = label
        break
print("empty_choice_text =", repr(empty_choice_text))
ok = ok and (empty_choice_text == CUSTOM)

if ok:
    print("PASS: custom empty_label honored")
    raise SystemExit(0)
print("FAIL: custom empty_label NOT honored")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all 4 requirements. probe_1 (R1 crit 1/2/3 + positive control): custom empty_label survives onto radio blank FK field and its empty choice text — HOLDS gold (empty_label='MY CUSTOM EMPTY LABEL'), VIOLATED at base (empty_label='None'), so it discriminates. probe_2 (R2): default translated 'None' when caller omits empty_label — HOLDS gold. probe_3 (R3): non-blank radio FK gets empty_label=None even when caller passes one, no empty choice — HOLDS gold. probe_4 (R4 crit1/2): non-radio FK path unchanged (non-radio widget, default '---------' empty_label) — HOLDS. probe_5 (R4 crit4 regression): AdminRadioSelect widget + get_ul_class css preserved for HORIZONTAL and VERTICAL — HOLDS. probe_6 (R4 crit1): caller-supplied widget bypasses radio branch, no forced empty_label — HOLDS. All 6 HOLD on gold-patched tree.

CANDIDATE PATCHES: weak2 (empty_label = kwargs.get('empty_label') if blank else None) drops the _('None') default → REJECTED by probe_2 (VIOLATED, empty_label=None when caller omits), while probe_1/probe_3 still hold — demonstrates the suite discriminates a wrong fix on the R2 axis. weak1 (kwargs.get('empty_label', _('None')) with no db_field.blank guard) turned out behaviorally EQUIVALENT to gold: ModelChoiceField.__init__ itself sets empty_label=None when widget is RadioSelect and field is not blank, so all 6 probes HOLD under weak1 — it is NOT a too-weak finding (it would resolve the hidden tests). The R3 suppression is enforced by ModelChoiceField downstream, not solely by the options.py guard, so probe_3 cannot reject weak1; weak2 remains the discriminating rejected candidate.

Run matrix: gold = all HOLD; base = probe_1 VIOLATED (positive control fires); weak2 = probe_2 VIOLATED. Requirements are faithful and adequately strong given the ModelChoiceField semantics.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one line in ModelAdmin.formfield_for_foreignkey (django/contrib/admin/options.py): kwargs['empty_label'] = kwargs.get('empty_label', _('None')) if db_field.blank else None. The requirements pin the changed observable behavior at the correct boundary: the blank-branch precedence (caller value wins), the default fallback, the non-blank suppression, and confinement to the radio branch. Requirement 1 says 'forward that caller-supplied empty_label unchanged' — this correctly matches gold, which uses .get(...,default) rather than the issue's suggested `or` form, so even a falsy '' is preserved; a requirement written around `or` would have been unfaithful, but it was not. No over/under-specification found; boundary is the changed behavior, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavioral fix (honor caller-supplied empty_label for blank radio FK fields; default to _('None'); suppress for non-blank; leave non-radio paths unchanged) without transmitting hidden-test artifacts. The hidden FAIL_TO_PASS test (test_radio_fields_foreignkey_formfield_overrides_empty_label) exercises the change via formfield_overrides={ForeignKey: {'empty_label': 'Custom empty label'}} through formfield_for_dbfield on the Inventory 'parent' field — none of these appear: no test name/path, no literal 'Custom empty label', no Inventory/parent, no formfield_overrides/formfield_for_dbfield mechanism. The doc's 'override formfield_for_foreignkey and set kwargs["empty_label"] before super()' example comes verbatim from the PUBLIC problem_statement, not the test. The gold edit introduces no new identifiers to leak. Req 4.3's field-type enumeration (char/text/int/date/.../m2m) is not a faithful mirror of the PASS_TO_PASS set (omits UUID; framed as generic regression scope) and reflects publicly-known Django field types handled by formfield_for_dbfield, describing behavior rather than reconstructing tests. Naming options.py/formfield_for_foreignkey is legitimate localization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
