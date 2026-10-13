#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14855 (nagini).

SHADOW
------
The `# impl-start` / `# impl-end` region of model.py, copied VERBATIM below with
only the contract calls removed (here: one `Assert`, plus the `# type:` comment
that Nagini needs and CPython does not). Nothing is restructured, renamed or
"simplified" -- the statements appear in the same order with the same names:

    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]
    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
    return url

`ToSeq`/`PSeq` are the Nagini carriers, provided here by the usual immutable-
sequence shim (the shape reused across this corpus's nagini conformance checks).
The model's `pure` region is empty, so no `@Pure` helper needs copying.

`resolve_prefix` is `@ContractOnly` -- it has no body to copy. Per the worker
contract it is bound to the REAL repo callee mapping.md section 3.1 axiomatizes,
`django.urls.reverse(viewname, args=..., current_app=...)`
(`django/urls/base.py:27`), so the axiom is EXERCISED rather than assumed. The
`has_selector` flag becomes "pass `current_app=`" vs "omit it", exactly the
distinction the gold patch turns on, and `NoReverseMatch` folds to the EMPTY
sequence (the model's "no link produced" value; see the ROUTE AXIS section).
The binding IGNORES its `exposes` argument, and that is deliberate: the real
callee decides resolvability from the live resolver itself, so passing a
route-availability table to it could only mask a disagreement. `exposes` is
instead OBSERVED off that same live resolver (below) and fed to the MODEL's
clauses, so leg B compares the model's prediction against what the real callee
independently did.

ORACLE
------
The REAL patched repo function is CALLED, not transliterated:
`AdminReadonlyField.get_admin_url(self, remote_field, remote_obj)` --
`django/contrib/admin/helpers.py:206`, changed body line 212 (mapping.md
section 1). The gate applies patch.diff to /testbed before this script runs, so
the imported `django.contrib.admin.helpers` is the POST-patch source; the check
asserts at startup that the loaded function really does forward `current_app`
(FIDELITY GATE 0 below), so a mis-applied patch fails loudly instead of
producing a vacuous green.

`get_admin_url` reads exactly three things off its receiver and arguments --
`self.model_admin.admin_site.name`, `remote_field.model._meta.{app_label,
model_name}`, and `remote_obj.pk` / `str(remote_obj)` -- so it is driven on a
duck-typed receiver via the unbound function. That is a genuine call into the
patched repo code, not a reimplementation of it: the `url_name` concatenation,
the `quote()` of the pk, the `current_app=` argument, the `format_html` wrap and
the `NoReverseMatch` fallback are all the repo's own, executed as written.

THE ROUTE AXIS (why the registry is a TRIPLE, not a pair)
---------------------------------------------------------
`reverse` narrows to ONE instance namespace and only then looks the view
identifier up inside it (`django/urls/base.py:41-84`, then
`_reverse_with_prefix`). So whether a link is produced at all depends on the
deployment resolution lands in: an identifier a sibling carries but the selected
deployment does not raises `NoReverseMatch`, and `get_admin_url`'s `except
NoReverseMatch: return str(remote_obj)` arm then renders the object with NO
link. Sibling admin deployments really do differ this way -- each `AdminSite`
has its own `_registry`, so `site2.register(Model)` is what makes a model's
change view exist under `site2` at all -- and the gold test_patch has to add
those registrations before the custom-site link renders.

The registry is therefore a TRIPLE of parallel sequences: instance name, mount
prefix, and `exposes[k]` = "deployment k carries a route for the view identifier
and argument at hand". Each sibling gets its OWN patterns object here, built
from its OWN model set, so the route sets genuinely differ between siblings;
`exposes[k]` is then OBSERVED, never assumed, by reversing through deployment
k's own instance namespace (which never consults `current_app`). "No link" is
carried as the EMPTY prefix sequence, which is unambiguous because every
registered deployment's mount prefix is non-empty (it carries at least "/").

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model works over `PSeq[int]` of Unicode code points; the repo works over
`str`. `cps(s) = [ord(c) for c in s]` and `uncps` invert each other, so
generation happens on the concrete side (a registry of sibling admin-site
deployments, each a `(name, mount, model_set)` triple) and is lowered per call:

  * `names[k]`    <-> the k-th deployment's `AdminSite.name`
  * `prefixes[k]` <-> "/" + the k-th deployment's mount prefix
  * `exposes[k]`  <-> whether `reverse('<name_k>:<app>_<model>_change',
    args=[quote(pk)])` resolves, i.e. whether deployment k carries that route
    for that argument. OBSERVED from the live resolver, never assumed.
  * `current_idx` <-> which deployment renders the page (`model_admin.admin_site`)
  * `default_idx` <-> the instance real `reverse` falls back to with no
    `current_app`. DISCOVERED from the live resolver, never hard-coded from
    registration order.
  * the EMPTY `PSeq` result <-> `get_admin_url` produced no `<a href=...>` at all

The registry is built as a real Django URLconf whose entries are the exact
3-tuple `AdminSite.urls` returns -- `(get_urls(), 'admin', self.name)`
(`django/contrib/admin/sites.py:303`): several sibling instance namespaces under
ONE shared app namespace `admin`, mounted at different prefixes, each with its
own route set. That is the multiple-`AdminSite` deployment the bug is about, and
it is the structure real `reverse` resolves against.

FIDELITY GATES (the harness is checked, not trusted)
----------------------------------------------------
0. The loaded `get_admin_url` source must contain `current_app` (patch applied).
1. The lean 3-tuple URLconf + duck-typed receiver must be OBSERVATIONALLY
   IDENTICAL to a URLconf built from real `admin.AdminSite(name=...)` objects
   driven through a real `AdminReadonlyField` on a real `ModelAdmin`, over a
   fixed battery of registry shapes with DIFFERING per-site model registrations
   -- same `app_dict` ordering AND same returned markup, byte for byte. If the
   cheap harness ever drifts from real `AdminSite` wiring, this fails instead of
   silently testing the wrong thing.
2. Every generated `prefixes[current_idx]` and every `exposes[k]` is confirmed
   against deployment k's OWN namespace (`reverse('<name_k>:<view>')`, which
   never consults `current_app`), so the expected value is defined
   independently of the mechanism under test.
3. Mounts within a registry are pairwise non-prefix, so a prefix assertion
   cannot pass spuriously.
4. Both branches of the real function (resolve / `NoReverseMatch`) and the
   discriminating cases -- non-default current deployment, and a deployment that
   does NOT carry a route a sibling DOES carry -- must each be exercised.

WHAT IS DIFFERENTIALLY CHECKED (two legs)
-----------------------------------------
LEG A -- shadow vs oracle. `related_link_target(...)` (the impl region) vs the
href the patched `get_admin_url` emits, and additionally the shadow's URL
re-wrapped with the repo's own `format_html` vs the oracle's full markup. This
pins the composition: WHICH selector reaches `reverse` (the current
deployment's name, not the default's), the `url_name` built from the remote
model, the `quote()`d pk, and the no-link arm.

Because the impl region's only computation IS the `@ContractOnly` call, Leg A
alone could not fail on the selection semantics -- so it is kept honest by an
ANTI-VACUITY control (precedent: django__django-12304's discrimination
self-test). Mutated shadows are run over the same inputs and each MUST be
caught on some input, or this script exits non-zero as vacuous:
  * `mutant_prepatch`  -- `has_selector=False`, i.e. model_prepatch.py / the
    pre-patch `reverse(url_name, args=[...])` with no `current_app`;
  * `mutant_default`   -- selects with `names[default_idx]` instead of
    `names[current_idx]`;
  * `mutant_total`     -- ignores the route axis and always returns the current
    deployment's prefix, i.e. treats resolution as total.

LEG B -- the model's postcondition vs the real patched function. model.py's four
`Ensures` clauses on `Result()` are checked against what the real patched code
actually returns, on inputs satisfying every `Requires`. This is the leg that
carries the refinement claim: with a `@ContractOnly` callee bound to the real
function, the model's behavioural content lives in its postcondition, so an
axiom that over-claims relative to reality means the proof is about the wrong
program. The clause the input's guards select is the one checked -- all four are
checked, none is skipped, INCLUDING the two no-link clauses (the earlier version
of this script returned early when the real code produced no link, which is
exactly how a missing route-axis clause could hide). Leg B is read in the
CHARITABLE "prefix" sense that refinement.md step 6 states (the F2P observable
is the href prefix), so a reported violation is not an artefact of a strict
reading.

INPUT DOMAIN (every input satisfies the model's Requires)
---------------------------------------------------------
Enforced by construction, not by filtering after the fact:
  * `len(names) == len(prefixes) == len(exposes)`;
  * `0 <= default_idx, current_idx < len(names)`;
  * names within a registry are UNIQUE (the model's `Forall2` precondition);
  * every `prefixes[k]` is non-empty (a mount lowers to at least "/");
  * `names[current_idx]` carries no U+003A -- the model's explicit domain
    restriction (mapping.md section 3.1: `reverse` splits `current_app` on ':'
    before matching). Colon-bearing names ARE still generated as non-current
    SIBLINGS, which the Requires permits, so that channel stays covered.
The EMPTY admin-site name is deliberately generated and NOT excluded: `PSeq` of
length 0 satisfies every `Requires` above (the colon `Forall` is vacuous over an
empty sequence), so it is squarely inside the modeled domain. Registries whose
siblings carry DIFFERENT route sets are likewise generated deliberately, and
both no-link clauses have dedicated coverage obligations below.

Boundary cases first (the exact F2P shape `admin` + `namespaced_admin` at the
repo's own `test_admin/admin/` and `test_admin/admin5/` mounts; singleton
registry; root-mounted deployment; empty name as default AND as non-default;
colon sibling; unicode / whitespace / digit / app-namespace-colliding names;
registries where the current deployment lacks a route a sibling has, and where
the default deployment lacks a route the current one has; the `NoReverseMatch`
branch), then seeded fuzz to fill the count. Pinned seed 14855, recorded in
mapping.md under "## G-CONF". Exit 0 iff zero disagreements on both legs.
"""
import json
import random
import re
import sys
import types

SEED = 14855
N_TARGET = 100000

APP_NS = "admin"                  # the shared application namespace
VIEW_SUFFIX = "_change"
HREF_RE = re.compile(r'href="([^"]*)"')


# --------------------------------------------------------------------------
# Nagini carriers: PSeq is an immutable sequence; ToSeq materializes one.
# --------------------------------------------------------------------------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls.__new__(cls)
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def update(self, i, v):
        t = list(self._t)
        t[i] = v
        return PSeq._wrap(t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq(%r)" % ("".join(chr(c) for c in self._t),)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- type bridge (mapping.md section 2): str <-> PSeq[int] of code points ----

def cps(s):
    return [ord(ch) for ch in s]


def uncps(p):
    """PSeq[int] -> str. The EMPTY sequence is the model's "no link produced"
    value, so it lowers to None (the absence of an href), NOT to "". Every
    registered deployment's prefix is non-empty, so the two cannot collide."""
    if p is None or len(p) == 0:
        return None
    return "".join(chr(p[i]) for i in range(len(p)))


EMPTY = PSeq()


# --------------------------------------------------------------------------
# The @ContractOnly axiom, bound to the REAL repo callee it axiomatizes.
# mapping.md section 3.1: django.urls.reverse (django/urls/base.py:27), the
# namespace -> instance selection plus the in-instance identifier lookup.
# has_selector <-> supplying current_app; NoReverseMatch <-> the empty result.
# The `exposes` argument is accepted and IGNORED: the real callee consults the
# live resolver itself, so handing it a route table could only mask a
# disagreement. exposes is observed off that same resolver for the MODEL's side.
# The ambient view identifier / positional argument are the ones the real
# get_admin_url computes for the same input (set by the driver per call).
# --------------------------------------------------------------------------

_AMBIENT = {"url_name": None, "arg": None}


def resolve_prefix(names, prefixes, exposes, default_idx, selector,
                   has_selector):
    from django.urls import reverse, NoReverseMatch
    kwargs = {}
    if has_selector:
        kwargs["current_app"] = uncps(selector) or ""
    try:
        return PSeq._wrap(cps(reverse(_AMBIENT["url_name"],
                                      args=[_AMBIENT["arg"]], **kwargs)))
    except NoReverseMatch:
        return EMPTY


# --------------------------------------------------------------------------
# SHADOW: the impl region of model.py, VERBATIM, contract calls stripped.
# (Stripped: the `Assert(nm[current_idx] == selector)` proof hint and the
#  `# type:` annotation comment. Nothing else changed.)
# --------------------------------------------------------------------------

def related_link_target(names, prefixes, exposes, default_idx, current_idx):
    # impl-start
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]
    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
    # selector == names[current_idx] is a registered instance name (k=current);
    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
    return url
    # impl-end


# --- MUTANTS (anti-vacuity control only; NOT the shadow) ---------------------

def mutant_prepatch(names, prefixes, exposes, default_idx, current_idx):
    """model_prepatch.py / the pre-patch call: no current_app supplied."""
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]
    return resolve_prefix(nm, pf, ex, default_idx, selector, False)


def mutant_default(names, prefixes, exposes, default_idx, current_idx):
    """Selects with the DEFAULT deployment's name instead of the current one."""
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[default_idx]
    return resolve_prefix(nm, pf, ex, default_idx, selector, True)


def mutant_total(names, prefixes, exposes, default_idx, current_idx):
    """Treats resolution as TOTAL: always produces the current deployment's
    prefix, ignoring whether that deployment carries the route at all."""
    pf = ToSeq(prefixes)
    return pf[current_idx]


# --------------------------------------------------------------------------
# Django bootstrap. One settings.configure for the whole process: the full
# INSTALLED_APPS so FIDELITY GATE 1 can build real AdminSite objects, and a
# sqlite :memory: DATABASES entry so model classes import. No query is ever
# issued (every model instance is unsaved; only pk / __str__ are touched).
# --------------------------------------------------------------------------

def configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            USE_TZ=False,
            SECRET_KEY="gconf-14855",
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
                "django.contrib.sessions",
                "django.contrib.messages",
            ],
            TEMPLATES=[{
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [], "APP_DIRS": True,
                "OPTIONS": {"context_processors": []},
            }],
            MIDDLEWARE=[],
            ROOT_URLCONF=None,
        )
    django.setup()


# --- the remote models the read-only field can point at ----------------------
# Plain carriers exposing exactly what get_admin_url reads:
# remote_field.model._meta.{app_label, model_name}.

class _Meta(object):
    __slots__ = ("app_label", "model_name")


class FakeModel(object):
    def __init__(self, app_label, model_name):
        self._meta = _Meta()
        self._meta.app_label = app_label
        self._meta.model_name = model_name

    def key(self):
        return (self._meta.app_label, self._meta.model_name)

    def __repr__(self):
        return "%s.%s" % self.key()


class FakeRemoteField(object):
    __slots__ = ("model",)

    def __init__(self, model):
        self.model = model


class FakeObj(object):
    """A read-only related object: get_admin_url reads .pk and str()."""
    __slots__ = ("pk", "_label")

    def __init__(self, pk, label):
        self.pk = pk
        self._label = label

    def __str__(self):
        return self._label


class _FakeSite(object):
    __slots__ = ("name",)


class _FakeModelAdmin(object):
    __slots__ = ("admin_site",)


# ANCHOR is registered in EVERY generated deployment, so the no-selector probe
# that DISCOVERS default_idx always resolves. Instance selection does not depend
# on which identifier is asked for, so an observation made with the anchor is
# valid for every other target too.
ANCHOR = FakeModel("auth", "user")
OPTIONAL_MODELS = [
    FakeModel("admin_views", "language"),
    FakeModel("admin_views", "chapter"),
    FakeModel("contenttypes", "contenttype"),
]
REMOTE_MODELS = [ANCHOR] + OPTIONAL_MODELS

# route names NO deployment carries; these drive the real function's
# NoReverseMatch branch on a HOMOGENEOUS registry (nothing anywhere resolves).
UNREGISTERED_MODELS = [
    FakeModel("admin_views", "ghost"),
    FakeModel("nope", "missing"),
]

_ALL = frozenset(m.key() for m in REMOTE_MODELS)
_ANCHOR_ONLY = frozenset([ANCHOR.key()])


def _view(request, object_id):
    from django.http import HttpResponse
    return HttpResponse("")


def build_patterns(model_keys):
    """The url patterns of ONE deployment: one '<app>_<model>_change' route per
    model that deployment registers, mirroring AdminSite.get_urls()'s change
    views (path('<path:object_id>/change/', ...) under <app>/<model>/).

    Each deployment gets its OWN patterns list, which is what makes the route
    sets differ between siblings -- the axis a single shared patterns object
    (every sibling carrying identical routes) cannot express."""
    from django.urls import path
    pats = []
    for m in REMOTE_MODELS:
        if m.key() not in model_keys:
            continue
        name = "%s_%s%s" % (m._meta.app_label, m._meta.model_name, VIEW_SUFFIX)
        route = "%s/%s/<path:object_id>/change/" % (m._meta.app_label,
                                                    m._meta.model_name)
        pats.append(path(route, _view, name=name))
    return pats


_SERIAL = [0]


def build_registry(reg):
    """Install a URLconf whose entries are the exact 3-tuple AdminSite.urls
    returns -- (get_urls(), 'admin', self.name), sites.py:303 -- one per
    sibling deployment, each with its OWN route set. Returns
    (module_name, default_idx)."""
    from django.urls import path, set_urlconf, get_resolver, reverse
    from django.urls import NoReverseMatch
    _SERIAL[0] += 1
    modname = "gconf14855_u%d" % _SERIAL[0]
    mod = types.ModuleType(modname)
    mod.urlpatterns = [path(mount, (build_patterns(keys), APP_NS, name))
                       for (name, mount, keys) in reg]
    sys.modules[modname] = mod
    set_urlconf(modname)
    names = [n for (n, _, _) in reg]
    mounts = ["/" + m for (_, m, _) in reg]
    # FIDELITY GATE: `default_idx` is the index the model's axiom characterizes
    # as "the prefix the NO-SELECTOR path returns" (resolve_prefix's
    # `not has_selector` clause). Discover it by OBSERVING the real callee on
    # exactly that path -- never by re-implementing reverse's fallback rule.
    #
    # A previously-assumed rule (`app_dict[APP_NS][0]`) is WRONG when some
    # sibling's instance name equals the app namespace itself: reverse only
    # falls back to `app_list[0]` in its `elif ns not in app_list` arm
    # (django/urls/base.py:59-63), so when `APP_NS in app_list` the instance
    # NAMED like the app namespace is the default instead. Observing the callee
    # is correct under both rules, so the bridge cannot drift from it again.
    #
    # The probe uses ANCHOR, which every deployment carries, so the observation
    # is never confounded by the route axis: selection happens before the
    # in-instance identifier lookup, so the instance the no-selector path picks
    # is the same whichever identifier is asked for.
    probe_view = "%s:%s_%s%s" % (APP_NS, ANCHOR._meta.app_label,
                                 ANCHOR._meta.model_name, VIEW_SUFFIX)
    default_idx = None
    try:
        no_sel = reverse(probe_view, args=["1"])
    except NoReverseMatch:
        no_sel = None
    if no_sel is not None:
        hits = [k for k in range(len(mounts)) if no_sel.startswith(mounts[k])]
        # check_mounts_distinct() guarantees no mount prefixes another, so a
        # successful reverse lands in exactly one registered mount.
        if len(hits) == 1:
            default_idx = hits[0]
    if default_idx is None:
        app_list = get_resolver(modname).app_dict.get(APP_NS, [])
        default_idx = names.index(app_list[0]) if app_list else 0
    return modname, default_idx


_PROBE_MODS = {}


def _probe_urlconf(keys):
    """A one-deployment URLconf carrying exactly `keys`' routes. Reversing
    against it exercises the real `reverse` on a registry with a SINGLE instance,
    so no instance selection happens at all -- which is what makes it a
    selection-independent observation of "does this route set carry the
    identifier, and does it accept this argument?"."""
    from django.urls import path
    if keys not in _PROBE_MODS:
        _SERIAL[0] += 1
        modname = "gconf14855_probe%d" % _SERIAL[0]
        mod = types.ModuleType(modname)
        mod.urlpatterns = [path("probe/",
                                (build_patterns(keys), APP_NS, "probe"))]
        sys.modules[modname] = mod
        _PROBE_MODS[keys] = modname
    return _PROBE_MODS[keys]


def observe_exposes(reg, remote_model, arg):
    """exposes[k], OBSERVED: does deployment k carry a route for this view
    identifier and this argument?

    Observed by driving the real `reverse` against a one-deployment URLconf
    holding deployment k's route set (FIDELITY GATE 2). That isolates the
    property from the selection mechanism under test -- with one instance there
    is nothing to select -- and, unlike reversing through deployment k's own
    instance namespace, it works for EVERY registered deployment. A deployment
    whose instance name embeds ':' is not addressable as `reverse('<name>:...')`
    at all (the view identifier is split on ':' too), so an own-namespace
    observation would report such a deployment as carrying no routes whatever it
    actually carries. Whether a route lives under deployment k's MOUNT is
    cross-checked separately, for the addressable (colon-free) names."""
    from django.urls import reverse, NoReverseMatch
    view = "%s:%s_%s%s" % (APP_NS, remote_model._meta.app_label,
                           remote_model._meta.model_name, VIEW_SUFFIX)
    out = []
    for (_name, _mount, keys) in reg:
        try:
            reverse(view, args=[arg], urlconf=_probe_urlconf(keys))
        except NoReverseMatch:
            out.append(False)
            continue
        out.append(True)
    return out


def oracle_markup(site_name, remote_model, pk, label):
    """CALL the REAL patched AdminReadonlyField.get_admin_url."""
    from django.contrib.admin.helpers import AdminReadonlyField
    recv = AdminReadonlyField.__new__(AdminReadonlyField)
    site = _FakeSite()
    site.name = site_name
    ma = _FakeModelAdmin()
    ma.admin_site = site
    recv.model_admin = ma
    return AdminReadonlyField.get_admin_url(recv, FakeRemoteField(remote_model),
                                            FakeObj(pk, label))


def href_of(markup):
    m = HREF_RE.search(str(markup))
    return m.group(1) if m else None


# --------------------------------------------------------------------------
# FIDELITY GATE 0: the loaded repo function is the PATCHED one.
# --------------------------------------------------------------------------

def gate_patch_applied():
    import inspect
    from django.contrib.admin.helpers import AdminReadonlyField
    try:
        src = inspect.getsource(AdminReadonlyField.get_admin_url)
    except (OSError, TypeError):
        return "cannot read get_admin_url source to confirm patch application"
    if "current_app" not in src:
        return ("the loaded AdminReadonlyField.get_admin_url does NOT pass "
                "current_app -- patch.diff was not applied, so the oracle is "
                "pre-patch code. Refusing to report a vacuous pass.\n" + src)
    return None


# --------------------------------------------------------------------------
# FIDELITY GATE 1: lean harness == real AdminSite wiring, observationally.
# Shapes carry DIFFERING per-site model sets, so the gate also pins that a real
# AdminSite's per-site _registry produces the same route asymmetry the lean
# per-deployment patterns objects do.
# --------------------------------------------------------------------------

# (app_label, model_name) -> the real Django model class registered on the real
# AdminSite side. The lean side builds FakeModel routes for the same keys.
GATE1_KEYS = [("auth", "user"), ("auth", "group"),
              ("contenttypes", "contenttype")]

_G1_ALL = frozenset(GATE1_KEYS)
_G1_USER = frozenset(GATE1_KEYS[:1])
_G1_USER_GROUP = frozenset(GATE1_KEYS[:2])

FIDELITY_SHAPES = [
    # the F2P shape, with the custom site registering FEWER models -- exactly
    # the asymmetry the gold test_patch has to add site2.register(...) to remove
    [("admin", "test_admin/admin/", _G1_ALL),
     ("namespaced_admin", "test_admin/admin5/", _G1_USER)],
    # the same asymmetry with the roles swapped
    [("admin", "test_admin/admin/", _G1_USER),
     ("namespaced_admin", "test_admin/admin5/", _G1_ALL)],
    [("only", "solo/", _G1_USER_GROUP)],                     # singleton
    [("", "emptyname/", _G1_ALL), ("plain", "plain/", _G1_USER),
     ("last", "last/", _G1_USER_GROUP)],
    [("a:b", "colon1/", _G1_ALL), ("cur", "cur/", _G1_USER),
     ("zed", "zed/", _G1_USER_GROUP)],
    [("admin", "firstmount/", _G1_USER),
     ("other", "secondmount/", _G1_ALL)],
    [("\u0395\u03bb\u03bb", "greek/", _G1_USER),
     ("\U0001F600", "emoji/", _G1_ALL), ("a b", "spacey/", _G1_USER_GROUP)],
    [("7", "digit/", _G1_ALL), ("0", "zero/", _G1_USER),
     (" ", "blank/", _G1_USER_GROUP)],
]


def _g1_lean_models(keys):
    """FakeModel carriers for the gate-1 keys a site registers."""
    return [FakeModel(a, m) for (a, m) in GATE1_KEYS if (a, m) in keys]


def _g1_build_lean(shape):
    """Lean URLconf for a gate-1 shape (its keys are GATE1_KEYS, not the main
    lane's REMOTE_MODELS, so it builds its patterns directly)."""
    from django.urls import path, set_urlconf
    _SERIAL[0] += 1
    modname = "gconf14855_g1lean%d" % _SERIAL[0]
    mod = types.ModuleType(modname)
    pats = []
    for (name, mount, keys) in shape:
        inner = []
        for m in _g1_lean_models(keys):
            inner.append(path("%s/%s/<path:object_id>/change/"
                              % (m._meta.app_label, m._meta.model_name),
                              _view,
                              name="%s_%s%s" % (m._meta.app_label,
                                                m._meta.model_name,
                                                VIEW_SUFFIX)))
        pats.append(path(mount, (inner, APP_NS, name)))
    mod.urlpatterns = pats
    sys.modules[modname] = mod
    set_urlconf(modname)
    return modname


def gate_lean_matches_real_adminsite():
    """Build each shape BOTH ways -- lean 3-tuple URLconf + duck-typed
    receiver, and real admin.AdminSite objects driven through a real
    AdminReadonlyField on a real ModelAdmin -- and require byte-identical
    app_dict ordering and returned markup."""
    from django.contrib import admin
    from django.contrib.auth.models import User, Group
    from django.contrib.contenttypes.models import ContentType
    from django.urls import path, set_urlconf, get_resolver, reverse
    from django.urls import NoReverseMatch
    from django.forms import modelform_factory

    real_of = {("auth", "user"): User, ("auth", "group"): Group,
               ("contenttypes", "contenttype"): ContentType}
    form = modelform_factory(User, fields=["username"])()
    probe_pk, probe_label = "no.opinion", "super"
    probes = [FakeModel(a, m) for (a, m) in GATE1_KEYS]

    for shape in FIDELITY_SHAPES:
        # -- lean side
        modname = _g1_build_lean(shape)
        lean_app_dict = get_resolver(modname).app_dict.get(APP_NS)
        lean = []
        for (name, _mount, _keys) in shape:
            for pm in probes:
                lean.append(str(oracle_markup(name, pm, probe_pk, probe_label)))
                try:
                    lean.append(reverse("%s:%s_%s%s"
                                        % (name, pm._meta.app_label,
                                           pm._meta.model_name, VIEW_SUFFIX),
                                        args=[probe_pk]))
                except NoReverseMatch:
                    lean.append(None)

        # -- real side: actual AdminSite instances, actual ModelAdmin
        _SERIAL[0] += 1
        rmod_name = "gconf14855_real%d" % _SERIAL[0]
        rmod = types.ModuleType(rmod_name)
        sites = []
        pats = []
        for (name, mount, keys) in shape:
            site = admin.AdminSite(name=name)
            for key in GATE1_KEYS:
                if key in keys:
                    site.register(real_of[key])
            sites.append(site)
            pats.append(path(mount, site.urls))
        rmod.urlpatterns = pats
        sys.modules[rmod_name] = rmod
        set_urlconf(rmod_name)
        real_app_dict = get_resolver(rmod_name).app_dict.get(APP_NS)
        real = []
        from django.contrib.admin.helpers import AdminReadonlyField
        for i, (name, _mount, _keys) in enumerate(shape):
            arf = AdminReadonlyField(form, "username", True,
                                     sites[i]._registry[User])
            for pm in probes:
                real.append(str(arf.get_admin_url(FakeRemoteField(pm),
                                                  FakeObj(probe_pk,
                                                          probe_label))))
                try:
                    real.append(reverse("%s:%s_%s%s"
                                        % (name, pm._meta.app_label,
                                           pm._meta.model_name, VIEW_SUFFIX),
                                        args=[probe_pk]))
                except NoReverseMatch:
                    real.append(None)

        if lean_app_dict != real_app_dict or lean != real:
            return ("lean harness drifted from real AdminSite wiring on shape "
                    "%r:\n  lean app_dict=%r out=%r\n  real app_dict=%r out=%r"
                    % (shape, lean_app_dict, lean, real_app_dict, real))
    return None


# --------------------------------------------------------------------------
# Boundary registries + pk/label pools
# --------------------------------------------------------------------------

BOUNDARY_SHAPES = [
    # the exact F2P shape, at the repo's own mounts, both deployments current,
    # with the custom site carrying FEWER routes (the asymmetry the gold
    # test_patch has to add site2.register(...) calls to remove)
    [("admin", "test_admin/admin/", _ALL),
     ("namespaced_admin", "test_admin/admin5/", _ANCHOR_ONLY)],
    # the same asymmetry with the roles swapped: the DEFAULT lacks the route
    [("admin", "test_admin/admin/", _ANCHOR_ONLY),
     ("namespaced_admin", "test_admin/admin5/", _ALL)],
    # F2P shape widened with the other sites tests/admin_views/urls.py mounts,
    # staircase route sets
    [("admin", "test_admin/admin/", _ANCHOR_ONLY),
     ("namespaced_admin", "test_admin/admin5/",
      frozenset([ANCHOR.key(), OPTIONAL_MODELS[0].key()])),
     ("admin7", "test_admin/admin7/",
      frozenset([ANCHOR.key(), OPTIONAL_MODELS[0].key(),
                 OPTIONAL_MODELS[1].key()])),
     ("admin10", "test_admin/admin10/", _ALL)],
    [("only", "solo/", _ALL)],                              # singleton
    [("only2", "solo2/", _ANCHOR_ONLY)],        # singleton missing most routes
    # a ROOT-mounted deployment: prefix "/" -- the non-empty-prefix edge
    [("root", "", _ALL)],
    [("rootless", "", _ANCHOR_ONLY)],
    # EMPTY name as a NON-default sibling (registered first => not the default)
    [("", "emptyfirst/", _ALL), ("plain", "plainmount/", _ANCHOR_ONLY),
     ("last", "lastmount/", _ANCHOR_ONLY)],
    # EMPTY name as the default (registered last)
    [("plain", "plainmount/", _ALL), ("last", "lastmount/", _ALL),
     ("", "emptylast/", _ANCHOR_ONLY)],
    # EMPTY current name where the CURRENT deployment carries the route and the
    # DEFAULT one does not: resolution still lands on the default -> no link
    [("", "emptyrich/", _ALL), ("poor", "poormount/", _ANCHOR_ONLY)],
    [("", "onlyempty/", _ALL)],                             # empty name alone
    # colon-bearing SIBLINGS (permitted; only names[current_idx] is restricted)
    [("a:b", "colon1/", _ALL), ("cur", "curmount/", _ANCHOR_ONLY),
     ("zed", "zedmount/", _ALL)],
    [("x:y:z", "colon2/", _ALL), ("plain", "plainmount/", _ANCHOR_ONLY)],
    # a deployment whose name IS the shared app namespace, non-default
    [("admin", "firstmount/", _ANCHOR_ONLY), ("other", "secondmount/", _ALL)],
    [("other", "secondmount/", _ANCHOR_ONLY), ("admin", "firstmount/", _ALL)],
    # unicode / whitespace / digit names, heterogeneous route sets
    [("\u0395\u03bb\u03bb\u03ac\u03b4\u03b1", "greek/", _ANCHOR_ONLY),
     ("na\u00efve", "naive/", _ALL), ("\U0001F600", "emoji/", _ANCHOR_ONLY)],
    [("7", "digit/", _ALL), ("0", "zero/", _ANCHOR_ONLY),
     (" ", "blank/", _ALL), ("\t", "tab/", _ANCHOR_ONLY)],
    [("a-b.c_d", "dotted/", _ANCHOR_ONLY), ("A" * 40, "long/", _ALL)],
    # many siblings, alternating route sets
    [("s%d" % k, "many%d/" % k, _ALL if k % 2 else _ANCHOR_ONLY)
     for k in range(8)],
]

PK_POOL = ["7", "1", "0", "-1", "no.opinion", "a b", "a&b", "x/y", "<id>",
           "\u0395\u03bb\u03bb", "a%2Fb", "..", ".", "  ", "%", "_2F", "\t",
           "\U0001F600", "A" * 60]
# "" drives the real function's NoReverseMatch branch (the path converter
# rejects an empty object_id), i.e. the `except NoReverseMatch: return str(obj)`
# arm of the patched code, with NO deployment able to resolve it.
PK_NOMATCH = [""]
LABEL_POOL = ["super", "Chapter 1", "Fictional duck", "a&b<x>",
              "\u0395\u03bb\u03bb", ""]

NAME_ALPHABET = "abcXYZ019_-.7"


def check_mounts_distinct(reg):
    """FIDELITY GATE 3: no mount may be a prefix of another, else a startswith
    assertion could pass spuriously."""
    mounts = ["/" + m for (_, m, _) in reg]
    for i in range(len(mounts)):
        for j in range(len(mounts)):
            if i != j and mounts[j].startswith(mounts[i]):
                return False
    return True


def gen_registry(rng):
    """A fuzzed registry of sibling deployments with UNIQUE names (the model's
    Forall2 precondition), pairwise non-prefix mounts, and per-deployment route
    sets drawn independently -- so heterogeneous registries (the class where the
    deployment resolution lands in lacks a route a sibling carries) are
    generated, not merely admitted."""
    n = rng.randint(1, 5)
    names = []
    seen = set()
    guard = 0
    while len(names) < n and guard < 200:
        guard += 1
        r = rng.random()
        if r < 0.05:
            cand = ""                                # empty name: IN domain
        elif r < 0.11:
            cand = rng.choice(["a:b", "x:y:z", ":", "p:", ":q"])
        elif r < 0.15:
            cand = rng.choice([" ", "\t", "0", "7", "admin",
                               "\u0395\u03bb\u03bb", "\U0001F600", "a b"])
        else:
            cand = "".join(rng.choice(NAME_ALPHABET)
                           for _ in range(rng.randint(1, 8)))
        if cand not in seen:
            seen.add(cand)
            names.append(cand)
    _SERIAL[0] += 1
    tag = _SERIAL[0]
    out = []
    for k in range(len(names)):
        keys = set([ANCHOR.key()])          # ANCHOR everywhere: see build_registry
        for m in OPTIONAL_MODELS:
            if rng.random() < 0.5:
                keys.add(m.key())
        out.append((names[k], "f%d_%d/" % (tag, k), frozenset(keys)))
    return out


# --------------------------------------------------------------------------
# One differential observation.
# --------------------------------------------------------------------------

def check_one(reg, default_idx, current_idx, remote_model, pk, label, stats):
    """Returns (legA_error, legB_error); either may be None."""
    from django.urls import reverse, NoReverseMatch
    from django.utils.html import format_html
    from django.contrib.admin.utils import quote

    names = [n for (n, _, _) in reg]
    mounts = ["/" + m for (_, m, _) in reg]

    # --- the model's Requires, asserted (never assumed) on every input -------
    assert len(names) == len(mounts)
    assert 0 <= default_idx < len(names)
    assert 0 <= current_idx < len(names)
    assert len(set(names)) == len(names), "names must be unique"
    assert ":" not in names[current_idx], "names[current_idx] must be colon-free"
    assert all(len(m) > 0 for m in mounts), "every prefix must be non-empty"

    # --- oracle: CALL the real patched repo function -------------------------
    oracle = oracle_markup(names[current_idx], remote_model, pk, label)
    oracle_url = href_of(oracle)

    # --- shadow: the impl region, over the PSeq carriers --------------------
    url_name = "%s:%s_%s%s" % (APP_NS, remote_model._meta.app_label,
                               remote_model._meta.model_name, VIEW_SUFFIX)
    arg = quote(pk)
    _AMBIENT["url_name"] = url_name
    _AMBIENT["arg"] = arg

    # exposes[k]: OBSERVED off the live resolver through each deployment's own
    # instance namespace (FIDELITY GATE 2), never assumed from the model set.
    exposes = observe_exposes(reg, remote_model, arg)
    assert len(exposes) == len(names)

    names_c = [PSeq._wrap(cps(n)) for n in names]
    prefixes_c = [PSeq._wrap(cps(m)) for m in mounts]

    shadow = related_link_target(names_c, prefixes_c, exposes, default_idx,
                                 current_idx)
    shadow_url = uncps(shadow)

    if shadow_url is None:
        stats["nomatch_branch"] += 1
    else:
        stats["resolve_branch"] += 1

    # LEG A.1 -- the URL itself
    if shadow_url != oracle_url:
        return (("LEG A (shadow vs real patched get_admin_url) URL mismatch\n"
                 "  registry      = %r\n  current_idx   = %d (name=%r)\n"
                 "  default_idx   = %d (name=%r)\n  remote_model  = %s.%s\n"
                 "  exposes       = %r\n  pk=%r label=%r\n"
                 "  shadow = %r\n  oracle = %r"
                 % (reg, current_idx, names[current_idx], default_idx,
                    names[default_idx], remote_model._meta.app_label,
                    remote_model._meta.model_name, exposes, pk, label,
                    shadow_url, oracle_url)), None)

    # LEG A.2 -- the full markup, re-wrapped with the repo's OWN format_html
    obj = FakeObj(pk, label)
    if shadow_url is None:
        shadow_markup = str(obj)
    else:
        shadow_markup = format_html('<a href="{}">{}</a>', shadow_url, obj)
    if str(shadow_markup) != str(oracle):
        return (("LEG A markup mismatch\n  registry=%r current_idx=%d pk=%r "
                 "label=%r\n  shadow = %r\n  oracle = %r"
                 % (reg, current_idx, pk, label, str(shadow_markup),
                    str(oracle))), None)

    # --- LEG B: the model's Ensures vs the real patched function ------------
    # model.py's four clauses on Result(), read in the charitable "carries that
    # deployment's prefix" sense of refinement.md step 6:
    #   len(names[cur]) > 0  and  exposes[cur]       -> prefixes[cur]
    #   len(names[cur]) > 0  and  not exposes[cur]   -> the empty sequence
    #   len(names[cur]) == 0 and  exposes[default]   -> prefixes[default]
    #   len(names[cur]) == 0 and  not exposes[default] -> the empty sequence
    # The guards are mutually exclusive and jointly total, so exactly one clause
    # applies to every admissible input, and it is checked -- including the two
    # no-link clauses. (An earlier version of this leg returned early when the
    # real code produced no link at all, which is precisely how a missing
    # route-axis clause stays invisible.)
    legB = None
    empty_current = (len(names[current_idx]) == 0)
    sel_idx = default_idx if empty_current else current_idx
    want = mounts[sel_idx] if exposes[sel_idx] else None
    if empty_current:
        stats["empty_selector_witness"] += 1

    # FIDELITY GATE 2 (second, independent confirmation): for a deployment whose
    # instance name is ADDRESSABLE -- colon-free, so `reverse('<name>:<view>')`
    # names it -- confirm both that the route observation agrees and that the
    # route really lives under that deployment's mount. Neither query consults
    # current_app, so the expected value stays independent of the mechanism
    # under test. A colon-bearing instance name is not addressable this way (the
    # view identifier is split on ':'), so only the one-deployment observation
    # above applies to it; names[current_idx] is colon-free by the model's
    # Requires, so the unaddressable case can only ever be the DEFAULT.
    own = None
    if ":" not in names[sel_idx]:
        try:
            own = reverse("%s:%s_%s%s" % (names[sel_idx],
                                          remote_model._meta.app_label,
                                          remote_model._meta.model_name,
                                          VIEW_SUFFIX), args=[arg])
        except NoReverseMatch:
            own = None
        if (own is not None) != bool(exposes[sel_idx]):
            return (("HARNESS: observed exposes[%d]=%r contradicts the "
                     "instance's own-namespace reverse %r (registry=%r)"
                     % (sel_idx, exposes[sel_idx], own, reg)), None)
        if own is not None and not own.startswith(mounts[sel_idx]):
            return (("HARNESS: instance-namespace reverse %r does not carry "
                     "the mount %r it was built at (registry=%r)"
                     % (own, mounts[sel_idx], reg)), None)

    if want is None:
        ok = (oracle_url is None)
    else:
        ok = (oracle_url is not None and oracle_url.startswith(want))
    if not ok:
        legB = ("LEG B: the real patched get_admin_url VIOLATES model.py's "
                "guarded Ensures on Result()\n"
                "  registry        = %r\n  current_idx     = %d  name=%r\n"
                "  default_idx     = %d  name=%r\n"
                "  remote_model    = %s.%s   pk=%r\n"
                "  exposes         = %r\n"
                "  Ensures demands %s  (guard: current name %s, route %s)\n"
                "  real code returned     %r\n"
                "  the selected instance's OWN namespace resolves to %r\n"
                % (reg, current_idx, names[current_idx], default_idx,
                   names[default_idx], remote_model._meta.app_label,
                   remote_model._meta.model_name, pk, exposes,
                   "NO link at all" if want is None else "prefix %r" % (want,),
                   "EMPTY -> the default deployment" if empty_current
                   else "non-empty -> the current deployment",
                   "carried" if exposes[sel_idx] else "absent",
                   oracle_url, own))

    # coverage of the discriminating cases
    if (current_idx != default_idx and not empty_current
            and exposes[current_idx] and oracle_url is not None):
        stats["nondefault_witness"] += 1
    if not empty_current and not exposes[current_idx] and any(exposes):
        # the current deployment lacks a route a SIBLING carries: the class the
        # no-link clause is about, and the one a route-blind spec mispredicts
        stats["unexposed_current_witness"] += 1
    if empty_current and not exposes[default_idx] and exposes[current_idx]:
        # resolution lands on the default, which lacks the route, while the
        # deployment rendering the page carries it: no link even so
        stats["unexposed_default_witness"] += 1
    if len(set(exposes)) > 1:
        stats["heterogeneous"] += 1

    # --- anti-vacuity: do the mutated shadows get caught on this input? -----
    for label_m, fn in (("prepatch", mutant_prepatch),
                        ("default", mutant_default),
                        ("total", mutant_total)):
        mv = uncps(fn(names_c, prefixes_c, exposes, default_idx, current_idx))
        if mv != oracle_url:
            stats["mutant_caught"][label_m] += 1

    return (None, legB)


def main():
    try:
        configure()
    except Exception as exc:
        print("G-CONF ERROR: cannot configure Django: %r" % (exc,))
        return 1

    err = gate_patch_applied()
    if err:
        print("G-CONF FAIL (fidelity gate 0): %s" % err)
        return 1

    err = gate_lean_matches_real_adminsite()
    if err:
        print("G-CONF FAIL (fidelity gate 1): %s" % err)
        return 1

    rng = random.Random(SEED)
    stats = {"resolve_branch": 0, "nomatch_branch": 0,
             "nondefault_witness": 0, "empty_selector_witness": 0,
             "unexposed_current_witness": 0, "unexposed_default_witness": 0,
             "heterogeneous": 0,
             "mutant_caught": {"prepatch": 0, "default": 0, "total": 0}}
    checked = 0
    legA_fail = None
    legB_fails = []
    legB_examples = []

    def consume(reg):
        """Run every in-domain current_idx of one registry, over a spread of
        remote models / pks / labels."""
        nonlocal checked, legA_fail
        if not check_mounts_distinct(reg):
            return
        modname, default_idx = build_registry(reg)
        names = [n for (n, _, _) in reg]
        for current_idx in range(len(reg)):
            # the model's Requires restricts names[current_idx] to be
            # colon-free; colon-bearing siblings stay in the registry.
            if ":" in names[current_idx]:
                continue
            for remote_model in REMOTE_MODELS + UNREGISTERED_MODELS:
                for pk in (PK_POOL[:4] + PK_NOMATCH):
                    a, b = check_one(reg, default_idx, current_idx,
                                     remote_model, pk,
                                     LABEL_POOL[checked % len(LABEL_POOL)],
                                     stats)
                    checked += 1
                    if a is not None and legA_fail is None:
                        legA_fail = a
                    if b is not None:
                        legB_fails.append(b)
                        if len(legB_examples) < 3:
                            legB_examples.append(b)
                    if legA_fail is not None:
                        return

    # ---- boundary cases first ---------------------------------------------
    for reg in BOUNDARY_SHAPES:
        consume(reg)
        if legA_fail is not None:
            break
    boundary_checked = checked

    # ---- seeded fuzz to reach the count -----------------------------------
    while checked < N_TARGET and legA_fail is None:
        reg = gen_registry(rng)
        if not check_mounts_distinct(reg):
            continue
        modname, default_idx = build_registry(reg)
        names = [n for (n, _, _) in reg]
        order = list(range(len(reg)))
        rng.shuffle(order)
        for current_idx in order:
            if ":" in names[current_idx]:
                continue
            for _ in range(6):
                if rng.random() < 0.12:
                    remote_model = rng.choice(UNREGISTERED_MODELS)
                else:
                    remote_model = rng.choice(REMOTE_MODELS)
                pk = "" if rng.random() < 0.04 else rng.choice(PK_POOL)
                a, b = check_one(reg, default_idx, current_idx, remote_model,
                                 pk, rng.choice(LABEL_POOL), stats)
                checked += 1
                if a is not None and legA_fail is None:
                    legA_fail = a
                if b is not None:
                    legB_fails.append(b)
                    if len(legB_examples) < 3:
                        legB_examples.append(b)
                if checked >= N_TARGET or legA_fail is not None:
                    break
            if checked >= N_TARGET or legA_fail is not None:
                break

    # ---- coverage obligations ---------------------------------------------
    coverage_err = None
    if stats["resolve_branch"] == 0:
        coverage_err = "the resolving branch was never exercised"
    elif stats["nomatch_branch"] == 0:
        coverage_err = "the NoReverseMatch branch was never exercised"
    elif stats["nondefault_witness"] == 0:
        coverage_err = ("the discriminating non-default-deployment case was "
                        "never exercised -- the check would pass for the "
                        "pre-patch code too")
    elif stats["empty_selector_witness"] == 0:
        coverage_err = ("the EMPTY-instance-name case was never exercised -- "
                        "that is the falsy-selector clause of the model's "
                        "guarded postcondition, so leaving it uncovered would "
                        "hide exactly the divergence this gate once reported")
    elif stats["heterogeneous"] == 0:
        coverage_err = ("no registry with DIFFERING per-deployment route sets "
                        "was exercised -- with every sibling carrying "
                        "identical routes the route axis is unobservable")
    elif stats["unexposed_current_witness"] == 0:
        coverage_err = ("the case where the CURRENT deployment lacks a route a "
                        "SIBLING carries was never exercised -- that is the "
                        "no-link clause of the model's postcondition, and "
                        "leaving it uncovered hides a spec that mispredicts a "
                        "link where the real code renders none")
    elif stats["unexposed_default_witness"] == 0:
        coverage_err = ("the case where the current deployment has an EMPTY "
                        "identifier and the DEFAULT deployment lacks the route "
                        "was never exercised -- that is the second no-link "
                        "clause, and it is what pins WHICH deployment's route "
                        "set governs the empty-identifier leg")
    for k, v in stats["mutant_caught"].items():
        if v == 0:
            coverage_err = ("mutant %r was NEVER caught -- this differential "
                            "is vacuous" % k)

    # ---- verdict -----------------------------------------------------------
    if legA_fail is not None:
        print("G-CONF FAIL: shadow disagrees with the real patched "
              "get_admin_url.")
        print(legA_fail)
        print(json.dumps({"checked": checked, "leg_a_disagreements": 1,
                          "leg_b_violations": len(legB_fails), "seed": SEED,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 1

    if coverage_err is not None:
        print("G-CONF FAIL (coverage): %s" % coverage_err)
        print(json.dumps({"checked": checked, "coverage_error": coverage_err,
                          "seed": SEED, "stats": stats,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 1

    if legB_fails:
        print("G-CONF FAIL: the MODEL does not agree with the real patched "
              "repo function. Leg A (shadow vs oracle) agreed on all %d "
              "inputs, but Leg B refutes model.py's postcondition on %d of "
              "them: on an input satisfying every Requires, the real patched "
              "get_admin_url does NOT produce what the selected clause demands."
              % (checked, len(legB_fails)))
        for ex in legB_examples:
            print(ex)
        print(json.dumps({"checked": checked, "leg_a_disagreements": 0,
                          "leg_b_violations": len(legB_fails),
                          "boundary": boundary_checked, "seed": SEED,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 1

    print("G-CONF OK: contract-stripped impl region == real patched "
          "AdminReadonlyField.get_admin_url on %d Requires-satisfying inputs "
          "(%d boundary + fuzz, seed %d); resolve/NoReverseMatch branches %d/%d, "
          "non-default-deployment witnesses %d, empty-identifier %d, "
          "heterogeneous registries %d, current-deployment-lacks-route %d, "
          "default-deployment-lacks-route %d, mutants caught %r; 0 "
          "disagreements on both legs."
          % (checked, boundary_checked, SEED, stats["resolve_branch"],
             stats["nomatch_branch"], stats["nondefault_witness"],
             stats["empty_selector_witness"], stats["heterogeneous"],
             stats["unexposed_current_witness"],
             stats["unexposed_default_witness"], stats["mutant_caught"]))
    print(json.dumps({"checked": checked, "leg_a_disagreements": 0,
                      "leg_b_violations": 0, "boundary": boundary_checked,
                      "seed": SEED, "stats": stats,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
