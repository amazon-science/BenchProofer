#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11095 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helper ``kept``
copies over as a plain function on top of a small immutable-tuple PSeq shim
(it is contract-side but serves here as an internal cross-check of the
materialisation shadow). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo functions the model models per mapping.md —
``django.contrib.admin.options.ModelAdmin.get_inlines`` (the selection hook;
modelled by ``select_applicable_editors``) and
``ModelAdmin.get_inline_instances`` (the materialisation; modelled by
``materialize_editors``). The gate applies the patch to /testbed before this
script runs; the script only imports and drives the patched code.

Type bridge (mapping.md section 2): an inline editor CLASS is carried as an
int class identifier. Concretely, a pool of distinct generic-inline classes is
built once, each tagged with its identifier; a ``List[int]`` lifts to the
corresponding list of classes and an editor-instance list lowers back through
``type(instance)`` to the identifiers. The per-entry permission flag
``granted`` is realised on the oracle side by overriding the three permission
predicates the materialisation consults, driven by a per-request set of
granted identifiers — the real permission decision is class-determined for a
given access context, so generation keeps duplicate identifiers flag-
consistent (that IS the concrete domain the abstraction maps). Which of the
three predicates carries the grant is varied independently (the decision is
their disjunction). A falsy access context, under which the real
materialisation skips the permission filter entirely, bridges to an all-set
flag vector. ``request``/``obj`` tags are otherwise opaque.

Input domain: the preconditions demand readable collections with
``len(reported) == len(granted)``; every generated tuple satisfies them.
Generation stresses the discriminating boundary: reports that are empty,
narrowed, reordered, duplicated, or disjoint from the configured collection
(where sourcing the materialisation from the configured collection instead of
the hook's report would disagree), plus the non-overridden default (report ==
configured) composed end-to-end.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz tuples, each
driving BOTH modelled operations. Pinned fuzz seed: 110950.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (no f-strings: older container Pythons).
"""
import json
import random
import sys

SEED = 110950
N_FUZZ = 100000
POOL_SIZE = 6


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- the model's minimal view class (contract calls stripped) -----------------

class AdminView(object):
    def __init__(self):
        self.configured = []
        self.reported = []
        self.granted = []


# --- pure helper from model.py, contracts stripped ----------------------------

def kept(reported, granted):
    if len(reported) == 0:
        return PSeq(0).take(0)
    if granted[0] != 0:
        return PSeq(reported[0]) + kept(reported.drop(1), granted.drop(1))
    return kept(reported.drop(1), granted.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def select_applicable_editors(self, request, obj):
    result = []
    i = len(self.configured)
    while i > 0:
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result


def materialize_editors(self, request, obj):
    result = []
    j = len(self.reported)
    while j > 0:
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result


# --- oracle plumbing -----------------------------------------------------------

def build_oracle():
    """Configure Django (same minimal app set as axiom_check.py), build the
    identifier-tagged inline-class pool and the two reusable admin objects.
    Returns (pool, default_admin, bridge_admin)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.contrib import admin
    from django.contrib.admin.sites import AdminSite
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes.admin import GenericTabularInline
    from django.db import models

    class Host(models.Model):
        class Meta:
            app_label = "contenttypes"

    class Child(models.Model):
        content_type = models.ForeignKey(ContentType, models.CASCADE)
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey()

        class Meta:
            app_label = "contenttypes"

    # Per-class permission predicates driven by the request: the access
    # context grants identifier k iff k is in request.granted_ids, through
    # whichever of the three channels request.grant_channels enables. The
    # materialisation's decision is their disjunction.
    class PermBridge(object):
        def _granted_via(self, request, channel):
            return (channel in request.grant_channels
                    and self._bridge_id in request.granted_ids)

        def has_view_or_change_permission(self, request, obj=None):
            return self._granted_via(request, "view")

        def has_add_permission(self, request, obj=None):
            return self._granted_via(request, "add")

        def has_delete_permission(self, request, obj=None):
            return self._granted_via(request, "delete")

    pool = []
    for k in range(POOL_SIZE):
        pool.append(type("BridgeInline%d" % k, (PermBridge, GenericTabularInline),
                         {"model": Child, "_bridge_id": k}))

    site = AdminSite()

    # Default admin: the non-overridden selection hook (its default report).
    default_admin = admin.ModelAdmin(Host, site)

    # Bridge admin: the hook's report is set per input, so an arbitrary
    # reported collection is observable by the materialisation.
    class BridgeAdmin(admin.ModelAdmin):
        def get_inlines(self, request, obj):
            return list(self._reported_classes)

    bridge_admin = BridgeAdmin(Host, site)
    return pool, default_admin, bridge_admin


class Ctx(object):
    """Minimal truthy access context carrying the grant decision."""
    def __init__(self, granted_ids, grant_channels):
        self.granted_ids = granted_ids
        self.grant_channels = grant_channels


def ids_of(instances):
    return [type(i)._bridge_id for i in instances]


# --- differential driver --------------------------------------------------------

def check_one(pool, default_admin, bridge_admin, configured, reported,
              granted, channels, falsy_request):
    """Drive both modelled operations on one input tuple; return an error
    string on any disagreement, else None."""
    view = AdminView()
    view.configured = list(configured)
    view.reported = list(reported)
    view.granted = list(granted)

    # (1) selection hook, default report: shadow vs real get_inlines.
    ctx = Ctx(frozenset(k for k, g in zip(reported, granted) if g), channels)
    request = None if falsy_request else ctx
    default_admin.inlines = [pool[k] for k in configured]
    shadow_sel = select_applicable_editors(view, 0, None)
    real_sel = [c._bridge_id for c in default_admin.get_inlines(request, None)]
    if shadow_sel != real_sel:
        return ("DISAGREEMENT (selection hook) on configured=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (patched get_inlines) = %r"
                % (configured, shadow_sel, real_sel))

    # (2) materialisation: shadow vs real get_inline_instances, with the
    # hook's report lifted through the bridge admin's override.
    bridge_admin.inlines = [pool[k] for k in configured]
    bridge_admin._reported_classes = [pool[k] for k in reported]
    shadow_mat = materialize_editors(view, 0, None)
    real_mat = ids_of(bridge_admin.get_inline_instances(request))
    if shadow_mat != real_mat:
        return ("DISAGREEMENT (materialisation) on configured=%r reported=%r "
                "granted=%r channels=%r falsy_request=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (patched get_inline_instances) = %r"
                % (configured, reported, granted, channels, falsy_request,
                   shadow_mat, real_mat))

    # internal cross-check: the executable impl agrees with the pure fold.
    if ToSeq(shadow_mat) != kept(ToSeq(reported), ToSeq(granted)):
        return ("INTERNAL: impl region and pure fold disagree on reported=%r "
                "granted=%r" % (reported, granted))
    return None


ALL = ("view", "add", "delete")


def boundary_cases():
    """(configured, reported, granted, channels, falsy_request) tuples.
    granted stays class-consistent (duplicate identifiers share a flag) and,
    under a falsy context, all-set — the concrete domain of the bridge."""
    cases = []

    def add(configured, reported, grants, channels=ALL, falsy=False):
        if falsy:
            granted = [1] * len(reported)
        else:
            granted = [1 if k in grants else 0 for k in reported]
        cases.append((configured, reported, granted, channels, falsy))

    add([], [], set())
    add([0], [], set())                       # empty report, nonempty config
    add([0, 1], [0, 1], {0, 1})               # report == configured, all kept
    add([0, 1], [0, 1], set())                # all dropped
    add([0, 1], [0], {0})                     # narrowed report (head)
    add([0, 1], [1], {1})                     # narrowed report (tail)
    add([0, 1], [1, 0], {0, 1})               # reordered report
    add([0, 1], [2, 3], {2, 3})               # report disjoint from configured
    add([0, 1, 2], [2, 2, 2], {2})            # duplicated identifier, kept
    add([0, 1, 2], [2, 2, 2], set())          # duplicated identifier, dropped
    add([0, 1, 2, 3, 4, 5], [5, 4, 3, 2, 1, 0], {0, 2, 4})  # alternating
    add([3], [3, 3], {3})                     # report longer than configured
    add([0, 1], [0, 1], {0, 1}, channels=("view",))
    add([0, 1], [0, 1], {0, 1}, channels=("add",))
    add([0, 1], [0, 1], {0, 1}, channels=("delete",))
    add([0, 1], [0, 1], {0}, channels=("view", "delete"))
    add([0, 1, 2], [0, 1, 2], set(), falsy=True)   # falsy context keeps all
    add([0, 1], [1], set(), falsy=True)
    add([], [2, 5, 2], {2, 5})
    return cases


def main():
    try:
        import django  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable: %r" % (exc,))
        return 1

    pool, default_admin, bridge_admin = build_oracle()

    checked = 0
    boundary = boundary_cases()
    for configured, reported, granted, channels, falsy in boundary:
        err = check_one(pool, default_admin, bridge_admin, configured,
                        reported, granted, channels, falsy)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    channel_choices = [ALL, ("view",), ("add",), ("delete",),
                       ("view", "add"), ("view", "delete"), ("add", "delete")]
    for t in range(N_FUZZ):
        configured = [rng.randrange(POOL_SIZE)
                      for _ in range(rng.randint(0, POOL_SIZE))]
        reported = [rng.randrange(POOL_SIZE)
                    for _ in range(rng.randint(0, POOL_SIZE))]
        if t % 5 == 0:
            reported = list(configured)       # the non-overridden composition
        grants = set(k for k in range(POOL_SIZE) if rng.random() < 0.5)
        falsy = (rng.random() < 0.05)
        if falsy:
            granted = [1] * len(reported)
        else:
            granted = [1 if k in grants else 0 for k in reported]
        channels = channel_choices[rng.randrange(len(channel_choices))]
        err = check_one(pool, default_admin, bridge_admin, configured,
                        reported, granted, channels, falsy)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched get_inlines/"
          "get_inline_instances on %d inputs (%d boundary + %d fuzz, seed %d), "
          "each driving both modelled operations; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
