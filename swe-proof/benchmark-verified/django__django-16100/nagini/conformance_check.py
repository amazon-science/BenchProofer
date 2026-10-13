#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16100 (nagini).

SHADOW: the impl region of model.py's ``apply_batch``, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The two
@Pure helpers, ``any_fails`` and ``committed_value``, copy over as plain
functions (``PSeq[int]`` reads only ``len``/``[i]``, which a plain list
provides; ``ToSeq`` becomes a tuple shim so the impl's ghost sequence
snapshots run unchanged). There are no @ContractOnly callees.

ORACLE: the REAL patched repo code the model models per mapping.md — the
list-editable bulk-save block of ``ModelAdmin.changelist_view``
(django/contrib/admin/options.py). The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable. The block is driven end-to-end through a real ``ModelAdmin`` over
an in-memory SQLite database: a POSTed changelist formset submits one
replacement value per row, the real ``save_form``/``save_model`` persist each
edit, and the committed rows are read back afterwards.

TYPE BRIDGE (mapping.md section 2):
  * ``original: List[int]``  <->  the stored integer value of each row before
      the request (row r's pre-request value == original[r]);
  * ``newvals: List[int]``   <->  each form's submitted replacement value,
      posted as the editable field of form r;
  * ``fails: List[int]``     <->  whether processing form r raises: the admin's
      per-edit ``log_change`` hook is overridden to raise for exactly the rows
      with fails[r] == 1 (the same injection point the instance's regression
      test uses); otherwise it is a no-op (its record-keeping side effect is
      unchanged plumbing outside the modeled observable);
  * ``Result(): List[int]``  <->  the committed database value of each row
      after the request, read back in row order.

BRIDGE DOMAIN RESTRICTION: the failure signal means "processing THIS form
raises". A form whose submitted value equals its stored value undergoes no
save processing at all (the loop skips unchanged forms), so no raise can be
attributed to it; the bridge therefore only realizes inputs with
fails[r] == 1  =>  newvals[r] != original[r]. All generated inputs satisfy the
shadow's Requires (equal lengths, fails[r] in {0, 1}).

Per input the script compares, shadow vs real:
  (a) the full committed store (shadow return value vs rows read back);
  (b) whether the request raised == any_fails(fails, 0) (sanity cross-check).

Boundary inputs: batch sizes 0..6 with a failure injected at every single
position and at none, all-fail batches, unchanged-row mixes (submitted value
== stored value with and without failures elsewhere), and the two-row
witnesses shaped like the instance's regression scenarios. Fuzz: random batch
sizes 0..8, random values, random failure placement (respecting the domain
restriction), random unchanged rows.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 16100.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the framework under test, present in
the image) only.
"""
import json
import random
import sys

SEED = 16100
N_FUZZ = 100_000


# --- shims for the spec-language carriers used inside the impl region --------

def ToSeq(l):
    """Sequence snapshot of a list: a plain immutable tuple."""
    return tuple(l)


# --- the pure helpers from model.py, as plain functions ----------------------

def any_fails(fails, i):
    """True iff some edit at index i, i+1, ... carries a failure signal.
    Front-recursive (one unfold per loop step) over the batch tail from i."""
    if i == len(fails):
        return False
    return fails[i] == 1 or any_fails(fails, i + 1)


def committed_value(original, newval, batch_fails):
    """The committed value of one row: its replacement value when the batch as
    a whole succeeds (no failing edit), otherwise its original value (the batch
    rolled back)."""
    if batch_fails:
        return original
    return newval


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def apply_batch(original, newvals, fails):
    # Apply the batch atomically: stage each row's replacement while walking the
    # forms, and only let the staged writes take effect if the whole batch
    # completes without a failure. A failure aborts the batch as a unit.
    failed = False
    i = 0
    while i < len(fails):
        if fails[i] == 1:
            # This edit's processing raises: the batch fails as a whole and the
            # grouped writes are discarded.
            failed = True
            break
        i = i + 1
    # Commit: replacement values iff the batch fully succeeded, otherwise the
    # original values (rollback). The same verdict applies to every row.
    result = []
    j = 0
    while j < len(original):
        old_seq = ToSeq(result)
        if failed:
            result = result + [original[j]]
        else:
            result = result + [newvals[j]]
        j = j + 1
    return result


# --- oracle plumbing: drive the REAL patched changelist save block -----------

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.admin",
            "django.contrib.sessions",
            "django.contrib.messages",
        ],
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3",
                        "NAME": ":memory:"}
        },
        ROOT_URLCONF=None,
        USE_TZ=True,
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]},
        }],
    )

django.setup()

from django.contrib import admin                      # noqa: E402
from django.contrib.auth.models import User           # noqa: E402
from django.core.management import call_command       # noqa: E402
from django.db import connection, models              # noqa: E402
from django.test.client import RequestFactory         # noqa: E402


class Row(models.Model):
    val = models.IntegerField()

    class Meta:
        app_label = "confcheck_app"
        ordering = ["id"]


class _InjectedFailure(Exception):
    pass


class RowAdmin(admin.ModelAdmin):
    """A real ModelAdmin whose list-editable save loop runs unmodified. Only
    the per-edit ``log_change`` hook is overridden: it raises for the rows
    whose failure signal is set (the bridge for fails[r] == 1) and is a no-op
    otherwise (suppressing only its record-keeping side effect, which is
    outside the modeled observable)."""
    list_display = ["id", "val"]
    list_editable = ["val"]
    ordering = ["id"]
    _fail_pks = frozenset()

    def log_change(self, request, obj, message):
        if obj.pk in self._fail_pks:
            raise _InjectedFailure()
        return None


class _MsgStore(list):
    def add(self, level, message, extra_tags="", *args, **kwargs):
        self.append(message)


_site = admin.AdminSite(name="confadmin")
_site.register(Row, RowAdmin)
_MA = _site._registry[Row]
_RF = RequestFactory()
_USER = None


def real_committed(original, newvals, fails):
    """Seed the rows, POST the bulk-edit formset through the REAL patched
    changelist view, and read back the committed values (plus whether the
    injected failure propagated)."""
    n = len(original)
    Row.objects.all().delete()
    Row.objects.bulk_create([Row(id=k + 1, val=original[k]) for k in range(n)])

    data = {
        "form-TOTAL_FORMS": str(n),
        "form-INITIAL_FORMS": str(n),
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "_save": "Save",
    }
    for k in range(n):
        data["form-%d-id" % k] = str(k + 1)
        data["form-%d-val" % k] = str(newvals[k])

    req = _RF.post("/confcheck/", data)
    req.user = _USER
    req._dont_enforce_csrf_checks = True
    req._messages = _MsgStore()
    _MA._fail_pks = frozenset(k + 1 for k in range(n) if fails[k] == 1)

    raised = False
    try:
        _MA.changelist_view(req)
    except _InjectedFailure:
        raised = True
    finally:
        _MA._fail_pks = frozenset()

    committed = list(Row.objects.order_by("id").values_list("val", flat=True))
    return committed, raised


# --- the differential check ---------------------------------------------------

def check(original, newvals, fails):
    shadow = apply_batch(original, newvals, fails)
    observed, raised = real_committed(original, newvals, fails)
    if shadow != observed:
        print("DISAGREEMENT on original=%r newvals=%r fails=%r:\n"
              "  shadow committed store = %r\n"
              "  real committed store   = %r"
              % (original, newvals, fails, shadow, observed))
        return False
    if raised != any_fails(fails, 0):
        print("DISAGREEMENT (verdict) on original=%r newvals=%r fails=%r:\n"
              "  real request raised = %r, any_fails = %r"
              % (original, newvals, fails, raised, any_fails(fails, 0)))
        return False
    return True


def boundary_cases():
    """Batch sizes 0..6: no failure; a failure at each single position; all
    fail; unchanged-row mixes; the two-row regression-shaped witnesses."""
    cases = []
    for n in range(0, 7):
        original = [10 + k for k in range(n)]
        newvals = [100 + k for k in range(n)]
        cases.append((original, newvals, [0] * n))
        for pos in range(n):
            f = [0] * n
            f[pos] = 1
            cases.append((original, newvals, f))
        if n:
            cases.append((original, newvals, [1] * n))
        # unchanged-row mixes: some submitted values equal the stored value
        # (those rows are skipped by the save loop and must carry fails == 0)
        if n >= 2:
            nv = list(original)
            nv[0] = original[0] + 5  # only row 0 actually changes
            cases.append((original, nv, [0] * n))
            f = [0] * n
            f[0] = 1
            cases.append((original, nv, f))
            nv2 = list(original)     # nothing changes at all
            cases.append((original, nv2, [0] * n))
    # two-row witnesses shaped like the instance's regression scenarios:
    # fail on the first edit / fail on the second edit / full success
    cases.append(([4, 2], [9, 5], [1, 0]))
    cases.append(([4, 2], [9, 5], [0, 1]))
    cases.append(([4, 2], [9, 5], [0, 0]))
    return cases


def main():
    global _USER
    call_command("migrate", run_syncdb=True, verbosity=0)
    with connection.schema_editor() as se:
        se.create_model(Row)
    _USER = User.objects.create_superuser(
        username="confcheck", email="confcheck@example.com", password="x")

    checked = 0

    boundaries = boundary_cases()
    for original, newvals, fails in boundaries:
        if not check(original, newvals, fails):
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        original = [rng.randint(-1000, 1000) for _ in range(n)]
        newvals = [rng.randint(-1000, 1000) for _ in range(n)]
        fails = [0] * n
        for k in range(n):
            if rng.random() < 0.5:
                newvals[k] = original[k]  # an unchanged row
            elif rng.random() < 0.3:
                fails[k] = 1              # this edit's processing raises
                if newvals[k] == original[k]:
                    # enforce the bridge domain restriction: a failing edit
                    # must actually change its row (unchanged forms are never
                    # processed, so no raise can be attributed to them)
                    newvals[k] = original[k] + 1
        if not check(original, newvals, fails):
            return 1
        checked += 1

    print("G-CONF OK: shadow apply_batch == real patched changelist "
          "bulk-save committed store on %d inputs (%d boundary + %d fuzz, "
          "seed %d)." % (checked, len(boundaries), N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked, "disagreements": 0, "seed": SEED,
        "shadow": "direct (contract-stripped impl region of apply_batch; "
                  "pure helpers as plain functions; ToSeq -> tuple shim)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
