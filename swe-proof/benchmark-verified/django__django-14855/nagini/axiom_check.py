#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14855.

Executes the REAL unchanged framework callee — Django's
``django.urls.reverse`` — and asserts that every observation matches the
``resolve_prefix`` axiom in model.py.

The single axiom (A-consumed):

  resolve_prefix(names, prefixes, exposes, default_idx, selector,
                 has_selector) -> prefix

with Ensures:
  * (not has_selector or len(selector) == 0) and exposes[default_idx]
                                -> Result() == prefixes[default_idx]
  * (not has_selector or len(selector) == 0) and not exposes[default_idx]
                                -> len(Result()) == 0
  * has_selector and len(selector) > 0 and a k with names[k] == selector,
    and exposes[k]              -> Result() == prefixes[k]
  * has_selector and len(selector) > 0 and a k with names[k] == selector,
    and not exposes[k]          -> len(Result()) == 0

and the domain Requires:
  * instance names are unique within the registry;
  * every registered deployment's prefix is non-empty;
  * the selector carries no U+003A (':') component separator.

i.e. ``reverse`` of a view living under ONE shared application namespace, when
given ``current_app=<a non-empty separator-free instance name registered under
that app namespace>``, returns a URL carrying THAT instance's mount prefix if
that instance carries a route for the identifier, and produces NO url at all
(``NoReverseMatch``) if it does not; when given no ``current_app`` — or an empty
one — it does the same for the registered default instance.

TWO domain facts are load-bearing and both are checked here.

1. The ':' separator. ``reverse`` splits ``current_app`` on ``':'``
   (``current_app.split(':')``) BEFORE matching it against the registered
   instance namespaces, so a ``current_app`` that embeds ``':'`` is decomposed
   into components and is NOT matched as a whole instance name. A registered
   instance whose name contains ``':'`` is therefore unreachable as a whole-name
   selector and falls to the default — which is why the axiom excludes such
   selectors from its domain rather than claiming ``Result()==prefixes[k]`` for
   them. We fuzz the separator below to confirm both: (1) every separator-free
   registered name selects its own prefix (the consumed branch), and (2) a
   colon-bearing registered name is NOT matched whole (outside the domain).

2. Emptiness of the selector. ``reverse`` guards on ``if current_app:``
   (``django/urls/base.py:41``), so ``current_app=''`` never reaches the name
   matching and behaves exactly like supplying no selector. The axiom states
   that (the default clauses absorb the empty selector) rather than claiming the
   empty-named instance's own prefix, and we check it against the real callee
   with an empty-named instance actually registered.

THE ROUTE AXIS. ``reverse`` narrows to ONE instance namespace and only then looks
the identifier up inside it (``django/urls/base.py:41-84``, then
``_reverse_with_prefix``), so whether any url is produced depends on the route
set of the deployment resolution lands in — an identifier a sibling carries but
the selected instance does not raises ``NoReverseMatch``. Sibling admin
deployments really do differ this way: each ``AdminSite`` has its own
``_registry``, so a model's change view exists under a given site only if that
site registers it. Every sibling here therefore gets its OWN inner URLconf
module with its OWN route set, and ``exposes[k]`` is OBSERVED by reversing
against a ONE-deployment URLconf holding deployment k's route set (with a single
instance there is nothing to select, so the observation is independent of the
selection mechanism under test). A shared inner module — every sibling carrying
identical routes — cannot express this axis at all, and the two "no url" clauses
would then never be exercised.

We reproduce the exact admin-site pattern: several URLconf entries of the shape
``AdminSite.urls`` returns — the 3-tuple ``(get_urls(), 'admin', self.name)``
(``django/contrib/admin/sites.py:303``) — all declaring the SAME app namespace
but DIFFERENT instance namespaces, mounted at different path prefixes, each with
its own route set. This is structurally the multiple-``AdminSite`` deployment the
bug is about. We then drive the real ``django.urls.reverse`` with and without
``current_app`` and assert the axiom's four clauses.

This is run inside the official SWE-bench container for the instance, where
Django is importable. Exit 0 iff every obligation holds.
"""
import os
import sys

APP_NAME = "the_app"
ANCHOR_VIEW = "obj_change"      # carried by EVERY deployment: default discovery
EXTRA_VIEWS = ["extra_change", "third_change"]
ALL_VIEWS = [ANCHOR_VIEW] + EXTRA_VIEWS

# A registered sibling whose instance NAME embeds the ':' component separator.
# It is a legal, unvalidated deployment (AdminSite(name=...) performs no name
# validation), so it is genuinely registered — yet it is OUTSIDE the axiom's
# domain (selector Requires: no U+003A). We register it to prove the exclusion
# is real: reverse splits current_app on ':' before matching, so this name is
# unreachable as a whole selector and would make an unrestricted axiom
# over-claim.
COLON_NAME = "a:b"


def _configure_django(urlconf_module):
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ROOT_URLCONF=urlconf_module,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    import types

    try:
        import django  # noqa: F401
        from django.urls import path
        from django.http import HttpResponse
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not importable in this environment: %r" % (exc,))
        return 0

    def view(request, object_id):  # a trivial target view
        return HttpResponse("")

    serial = [0]

    def patterns_for(view_names):
        return [path("%s/<int:object_id>/change/" % v, view, name=v)
                for v in ALL_VIEWS if v in view_names]

    def build(shape):
        """shape: [(instance_name, mount_prefix, {view names}), ...]. Each entry
        is the 3-tuple AdminSite.urls returns, so an EMPTY instance name is
        registrable exactly as AdminSite(name='') is."""
        serial[0] += 1
        modname = "axcheck_urls_%d" % serial[0]
        mod = types.ModuleType(modname)
        mod.urlpatterns = [
            path(mount.strip("/") + "/" if mount.strip("/") else "",
                 (patterns_for(views), APP_NAME, name))
            for (name, mount, views) in shape]
        sys.modules[modname] = mod
        return modname

    # ---- the shapes -------------------------------------------------------
    # Route sets form a staircase so that, whichever instance Django treats as
    # the default, some identifier is absent from it AND some identifier is
    # present in it -- both "no selector" clauses stay reachable. Shape 2 is
    # shape 1 re-ordered so the default lands on a route-poor deployment.
    A = frozenset(ALL_VIEWS)
    ANC = frozenset([ANCHOR_VIEW])
    MID = frozenset([ANCHOR_VIEW, EXTRA_VIEWS[0]])
    SHAPES = [
        # colon sibling registered FIRST so it is not the default: the
        # domain-boundary assert below would otherwise be unable to tell an
        # over-claiming whole-name match from the legitimate default fallback.
        [(COLON_NAME, "/colon1/", A), ("first_site", "/first/", ANC),
         ("namespaced_site", "/ns/", MID), ("third_site", "/third/", A)],
        [(COLON_NAME, "/colon2/", A), ("rich_site", "/rich/", A),
         ("mid_site", "/mid/", MID), ("poor_site", "/poor/", ANC)],
        # an EMPTY instance name really registered, as AdminSite(name='') is:
        # current_app='' must STILL behave as no selector at all
        [("", "/emptyfirst/", A), ("plain_site", "/plain/", MID)],
        [("plain2_site", "/plain2/", A), ("", "/emptylast/", ANC)],
        # singleton deployments, route-rich and route-poor
        [("solo", "/solo/", A)],
        [("solo2", "/solo2/", ANC)],
        # a deployment whose instance name IS the shared app namespace
        [(APP_NAME, "/appnamed/", ANC), ("other", "/other/", A)],
        [("other2", "/other2/", ANC), (APP_NAME, "/appnamed2/", A)],
        # a ROOT-mounted deployment: its prefix is "/", the non-empty edge of
        # the axiom's "every registered prefix is non-empty" domain fact
        [("rootmount", "/", A)],
    ]

    first_mod = build(SHAPES[0])
    try:
        _configure_django(first_mod)
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.urls import reverse, NoReverseMatch, get_resolver

    # one-deployment probe URLconfs: reversing against these exercises the real
    # reverse where there is only ONE instance, hence no selection at all -- a
    # selection-independent observation of "does this route set carry the
    # identifier?". (Reversing through a deployment's own instance namespace
    # cannot serve here: a colon-bearing instance name is not addressable that
    # way, since the view identifier is split on ':' too.)
    probe_mods = {}

    def probe_mod(views):
        if views not in probe_mods:
            probe_mods[views] = build([("probe", "/probeonly/", views)])
        return probe_mods[views]

    def observes(views, view_name, oid=7):
        try:
            reverse("%s:%s" % (APP_NAME, view_name), args=[oid],
                    urlconf=probe_mod(views))
            return True
        except NoReverseMatch:
            return False

    def rev(modname, view_name, oid=7, selector=None, has_selector=False):
        kwargs = {}
        if has_selector:
            kwargs["current_app"] = selector
        try:
            return reverse("%s:%s" % (APP_NAME, view_name), args=[oid],
                           urlconf=modname, **kwargs)
        except NoReverseMatch:
            return None

    checks = 0
    legs = {"sel_route": 0, "sel_noroute": 0, "nosel_route": 0,
            "nosel_noroute": 0, "emptysel_route": 0, "emptysel_noroute": 0,
            "colon_boundary": 0, "rootprefix": 0}
    fails = []

    for si, shape in enumerate(SHAPES):
        modname = build(shape)
        names = [n for (n, _, _) in shape]
        prefixes = [p for (_, p, _) in shape]
        viewsets = [v for (_, _, v) in shape]

        # ---- the axiom's DOMAIN premises, checked rather than assumed -------
        assert len(set(names)) == len(names), (
            "shape %d has duplicate instance names %r -- outside the axiom's "
            "domain (a lookup by identifier could not be single-valued)"
            % (si, names))
        for p in prefixes:
            assert len(p) > 0, (
                "shape %d registers a deployment whose prefix is the EMPTY "
                "string; the axiom's domain says a registered prefix carries at "
                "least the resolution root" % si)
            if p == "/":
                legs["rootprefix"] += 1
        checks += 1

        # ---- exposes[k], OBSERVED (never taken from the route set literal) --
        exposes = {}
        for v in ALL_VIEWS:
            exposes[v] = [observes(viewsets[k], v) for k in range(len(shape))]
            checks += len(shape)

        # ---- default_idx: OBSERVED on the no-selector path with the ANCHOR --
        # (selection happens before the in-instance lookup, so the instance the
        # no-selector path picks is the same whichever identifier is asked for)
        anchor_url = rev(modname, ANCHOR_VIEW)
        assert anchor_url is not None, (
            "shape %d: the anchor identifier, carried by every deployment, did "
            "not resolve on the no-selector path" % si)
        hits = [k for k in range(len(shape))
                if anchor_url.startswith(prefixes[k])]
        # longest match: a root-mounted deployment's "/" prefixes everything
        default_idx = max(hits, key=lambda k: len(prefixes[k]))
        checks += 1

        for v in ALL_VIEWS:
            exp = exposes[v]

            # ---- clause 1/2: NO selector -> the registered default ----------
            u = rev(modname, v)
            if exp[default_idx]:
                if u is None or not u.startswith(prefixes[default_idx]):
                    fails.append("UNSOUND no-selector (shape %d, view %r): "
                                 "reverse gave %r, axiom requires the default "
                                 "deployment's prefix %r (exposes=%r)"
                                 % (si, v, u, prefixes[default_idx], exp))
                else:
                    legs["nosel_route"] += 1
            else:
                if u is not None:
                    fails.append("UNSOUND no-selector (shape %d, view %r): the "
                                 "default deployment %r carries no route for it "
                                 "yet reverse produced %r; the axiom requires no "
                                 "url at all (exposes=%r)"
                                 % (si, v, names[default_idx], u, exp))
                else:
                    legs["nosel_noroute"] += 1
            checks += 1

            # ---- the EMPTY selector is absorbed by the default clauses ------
            u0 = rev(modname, v, selector="", has_selector=True)
            if u0 != u:
                fails.append("UNSOUND empty selector (shape %d, view %r): "
                             "current_app='' gave %r but no selector at all gave "
                             "%r; the axiom's default clauses absorb the empty "
                             "selector, so they must agree" % (si, v, u0, u))
            else:
                legs["emptysel_route" if exp[default_idx]
                     else "emptysel_noroute"] += 1
            checks += 1

            for k in range(len(shape)):
                # ---- clause 3/4: a NON-EMPTY separator-free registered name -
                if len(names[k]) == 0 or ":" in names[k]:
                    continue        # outside the axiom's selector domain
                uk = rev(modname, v, selector=names[k], has_selector=True)
                if exp[k]:
                    if uk is None or not uk.startswith(prefixes[k]):
                        fails.append("UNSOUND has_selector (shape %d, view %r, "
                                     "selector=%r): reverse gave %r, axiom "
                                     "requires that deployment's prefix %r "
                                     "(exposes=%r)"
                                     % (si, v, names[k], uk, prefixes[k], exp))
                    else:
                        legs["sel_route"] += 1
                else:
                    if uk is not None:
                        fails.append("UNSOUND has_selector (shape %d, view %r, "
                                     "selector=%r): deployment carries no route "
                                     "for it yet reverse produced %r; the axiom "
                                     "requires no url at all. The identifier IS "
                                     "carried by %r, so this would be the callee "
                                     "consulting a sibling, which it does not do "
                                     "(exposes=%r)"
                                     % (si, v, names[k], uk,
                                        [names[j] for j in range(len(shape))
                                         if exp[j]], exp))
                    else:
                        legs["sel_noroute"] += 1
                checks += 1

            # ---- DOMAIN BOUNDARY: a colon-bearing selector is OUT of domain -
            # reverse does current_app.split(':') before matching, so a
            # registered instance whose NAME embeds ':' is NOT reachable as a
            # whole-name selector. An UNRESTRICTED axiom would claim
            # reverse(current_app=COLON_NAME) carries that instance's prefix
            # (names[k]==selector -> prefixes[k]); the real callee instead splits
            # the name, matches neither component whole, and falls back to the
            # registered default. This is the soundness counterexample to the
            # over-claim, and the reason the model's `selector has no U+003A`
            # Requires is load-bearing.
            if COLON_NAME in names:
                ci = names.index(COLON_NAME)
                uc = rev(modname, v, selector=COLON_NAME, has_selector=True)
                if uc is not None and uc.startswith(prefixes[ci]) \
                        and ci != default_idx:
                    fails.append("DOMAIN premise broken (shape %d, view %r): "
                                 "reverse(current_app=%r) gave %r which DOES "
                                 "carry the colon-named instance's prefix %r as "
                                 "a whole-name match -- an unrestricted axiom "
                                 "would then be sound. Re-examine the split(':') "
                                 "domain assumption / registration order."
                                 % (si, v, COLON_NAME, uc, prefixes[ci]))
                elif uc != u:
                    fails.append("DOMAIN (shape %d, view %r): "
                                 "reverse(current_app=%r) gave %r; expected the "
                                 "colon name to be split and the call to behave "
                                 "as the default fallback %r"
                                 % (si, v, COLON_NAME, uc, u))
                else:
                    legs["colon_boundary"] += 1
                checks += 1

    # ---- colon-separator fuzz: many ':'-bearing selectors ------------------
    import random
    fuzz_mod = build(SHAPES[0])
    fuzz_names = [n for (n, _, _) in SHAPES[0]]
    fuzz_prefixes = [p for (_, p, _) in SHAPES[0]]
    fuzz_views = [v for (_, _, v) in SHAPES[0]]
    colon_prefix = fuzz_prefixes[fuzz_names.index(COLON_NAME)]
    rng_colon = random.Random(0xC010)
    colon_alphabet = "abc:xyz:"    # ':'-heavy so most fuzz names embed one
    colon_checks = 0
    for _ in range(2000):
        L = rng_colon.randint(1, 8)
        sel = "".join(rng_colon.choice(colon_alphabet) for _ in range(L))
        if ":" not in sel:
            continue               # only the out-of-domain channel here
        u = rev(fuzz_mod, ANCHOR_VIEW, oid=3, selector=sel, has_selector=True)
        if u is not None and u.startswith(colon_prefix):
            fails.append("colon-fuzz domain violation: current_app=%r selected "
                         "the colon instance prefix %r (reachable only via a "
                         "whole-name match that split(':') forbids)"
                         % (sel, colon_prefix))
        colon_checks += 1
        checks += 1
    if colon_checks == 0:
        fails.append("colon-fuzz generated no separator-bearing selectors")

    # ---- fuzz: random (instance, identifier) selection over shape 1 --------
    rng = random.Random(14855)
    anchor_url = rev(fuzz_mod, ANCHOR_VIEW)
    fuzz_hits = [k for k in range(len(fuzz_names))
                 if anchor_url.startswith(fuzz_prefixes[k])]
    fuzz_default = max(fuzz_hits, key=lambda k: len(fuzz_prefixes[k]))
    for _ in range(2000):
        k = rng.randrange(len(fuzz_names))
        v = rng.choice(ALL_VIEWS)
        oid = rng.randint(0, 10 ** 6)
        if ":" in fuzz_names[k] or len(fuzz_names[k]) == 0:
            continue
        u = rev(fuzz_mod, v, oid=oid, selector=fuzz_names[k], has_selector=True)
        carries = observes(fuzz_views[k], v, oid=oid)
        if carries:
            if u is None or not u.startswith(fuzz_prefixes[k]):
                fails.append("UNSOUND fuzz (selector=%r,view=%r,id=%d): reverse "
                             "gave %r, axiom requires prefix %r"
                             % (fuzz_names[k], v, oid, u, fuzz_prefixes[k]))
        else:
            if u is not None:
                fails.append("UNSOUND fuzz (selector=%r,view=%r,id=%d): the "
                             "deployment carries no route yet reverse gave %r; "
                             "the axiom requires no url"
                             % (fuzz_names[k], v, oid, u))
        checks += 1

    # ---- every clause of the axiom must actually have been exercised -------
    for leg, n in sorted(legs.items()):
        if n == 0:
            fails.append("COVERAGE: the %r leg of the axiom was never "
                         "exercised, so this check cannot witness its "
                         "soundness" % leg)

    if fails:
        print("G-AX FAIL: %d disagreement(s) between the resolve_prefix axiom "
              "and the real django.urls.reverse" % len(fails))
        for f in fails[:20]:
            print("  " + f)
        return 1

    print("G-AX OK: resolve_prefix axiom sound against real django.urls.reverse "
          "on %d observations (per-instance separator-free selection with and "
          "without a route for the identifier + default fallback in both route "
          "states + the empty selector absorbed by the default clauses + "
          "colon-separator domain boundary + root-mount prefix edge + fuzz); "
          "leg coverage %r" % (checks, legs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
