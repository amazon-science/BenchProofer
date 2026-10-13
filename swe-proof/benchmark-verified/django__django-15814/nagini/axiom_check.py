#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15814.

This bundle consumes NO `@ContractOnly` axioms: the changed behaviour — keying
a related model's passthrough primary key by the model's CANONICAL (concrete)
identity while accumulating the per-model fields to fetch — is modelled DEEPLY
in `model.py` (the `canonical_of` map application and the impl accumulation).
There is therefore no axiom to over-approximate.

What G-AX must establish is that the DEEP MODEL matches reality:

  (A-reference) `canonical_of(canonical, model)` (model.py pure region) == the
      real Django attribute `model._meta.concrete_model`. For a proxy model it
      is the concrete (non-proxy) model the proxy is backed by; for a concrete
      (non-proxy) model it is the model itself; and it is idempotent
      (`concrete_model._meta.concrete_model is concrete_model`). These are
      exactly the properties `canonical_of` and its idempotence precondition
      encode.

  (deep-model content, the discriminating behaviour) replaying the abstract
      `deferred_to_data`-style accumulation `related_reported_fields`, the
      related model's primary key lands in the reported field set keyed by the
      related model's CONCRETE identity (alongside the chosen `.only` attribute)
      IFF the canonical normalization is applied (the gold fix). Without it, the
      pk is keyed by the proxy and is absent from the concrete model's reported
      set — exactly the `'id' is not in list` failure the issue reports.

Imports only Django (the repo under test, importable in-container) plus stdlib.
Constructing model classes and reading `_meta.concrete_model` runs only Python
metaclass machinery; it never opens a database connection. Exit 0 iff every
obligation holds.
"""
import sys


def configure_django():
    """Configure Django just enough to define and introspect model classes.
    Reading `_meta.concrete_model` never touches a DB; an in-memory sqlite
    config with the contenttypes/auth apps is more than sufficient.

    A throwaway app `axiom_check_app` (the concrete/proxy models below live in
    it) is written to a real temp directory and put on `sys.path` so Django's
    app-loading machinery (which expects a filesystem module with a spec) is
    satisfied."""
    import os
    import tempfile

    app_dir = tempfile.mkdtemp(prefix="axiom_check_15814_")
    pkg_dir = os.path.join(app_dir, "axiom_check_app")
    os.makedirs(pkg_dir, exist_ok=True)
    open(os.path.join(pkg_dir, "__init__.py"), "w").close()
    # The models are defined in this checker (build_models); an empty models.py
    # is enough for the app to load.
    open(os.path.join(pkg_dir, "models.py"), "w").close()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "axiom_check_app",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=False,
        )

    import django
    django.setup()


def build_models():
    """Define a concrete model, a proxy of it, and a proxy-of-proxy, mirroring
    the F2P scenario (`Issue.assignee -> ProxyTrackerUser` proxy of
    `TrackerUser`)."""
    from django.db import models

    class TrackerUserAC(models.Model):
        status = models.CharField(max_length=50)

        class Meta:
            app_label = "axiom_check_app"

    class ProxyTrackerUserAC(TrackerUserAC):
        class Meta:
            app_label = "axiom_check_app"
            proxy = True

    class ProxyOfProxyAC(ProxyTrackerUserAC):
        class Meta:
            app_label = "axiom_check_app"
            proxy = True

    return TrackerUserAC, ProxyTrackerUserAC, ProxyOfProxyAC


# --- A-reference: canonical_of == _meta.concrete_model -----------------------

def canonical_of(canonical_map, model_token):
    """model.py's pure deep model, over an int-token map."""
    if model_token in canonical_map:
        return canonical_map[model_token]
    return model_token


def check_concrete_model(concrete, proxy, proxy2):
    # A concrete (non-proxy) model is its own concrete_model.
    assert concrete._meta.concrete_model is concrete, (
        "concrete model is not its own concrete_model: %r" % concrete)
    # A proxy collapses to the concrete model it is backed by.
    assert proxy._meta.concrete_model is concrete, (
        "proxy %r concrete_model is %r, expected %r"
        % (proxy, proxy._meta.concrete_model, concrete))
    # A proxy of a proxy still collapses to the single concrete model.
    assert proxy2._meta.concrete_model is concrete, (
        "proxy-of-proxy %r concrete_model is %r, expected %r"
        % (proxy2, proxy2._meta.concrete_model, concrete))
    # Idempotence: concrete_model of a concrete_model is itself (the
    # `canonical_of(canonical_of(m)) == canonical_of(m)` precondition).
    for m in (concrete, proxy, proxy2):
        c = m._meta.concrete_model
        assert c._meta.concrete_model is c, (
            "concrete_model not idempotent for %r" % m)

    # The int-token deep model agrees with reality. Token each class by id();
    # canonical map sends each token to its concrete model's token.
    tok = {concrete: 1, proxy: 2, proxy2: 3}
    canonical_map = {
        tok[proxy]: tok[concrete],
        tok[proxy2]: tok[concrete],
        tok[concrete]: tok[concrete],  # idempotent self-entry
    }
    for m in (concrete, proxy, proxy2):
        real = tok[m._meta.concrete_model]
        modelled = canonical_of(canonical_map, tok[m])
        assert real == modelled, (
            "canonical_of disagrees with concrete_model for %r: real=%r model=%r"
            % (m, real, modelled))
        # idempotence of the model
        assert canonical_of(canonical_map, canonical_of(canonical_map, tok[m])) \
            == canonical_of(canonical_map, tok[m])


# --- deep-model content: the accumulation discriminator ----------------------

def accumulate(related_concrete, related_pk, chosen_attr, related_token,
               normalize):
    """Replay model.py's `related_reported_fields` accumulation as plain Python.
    `related_token` is the related model's raw identity (the proxy);
    `related_concrete` its concrete identity. With `normalize=True` the
    passthrough pk is keyed by the concrete model (the gold fix); with
    `normalize=False` it is keyed by the raw (proxy) identity (pre-patch).
    Returns the reported attname set for the related model's concrete identity.
    """
    must_include = {}
    cur_model = related_token
    if normalize:
        cur_model = related_concrete
    must_include[cur_model] = {related_pk}

    seen = {}
    seen[related_concrete] = {chosen_attr}

    # per-key merge (defer == False branch)
    if cur_model in seen:
        seen[cur_model] |= must_include[cur_model]
    else:
        seen[cur_model] = set(must_include[cur_model])

    return seen[related_concrete]


def check_accumulation():
    CONCRETE, PROXY, PK, ATTR = 100, 200, 1, 2  # distinct tokens; PK != ATTR
    # Gold (normalized): the pk is in the concrete model's reported set.
    fixed = accumulate(CONCRETE, PK, ATTR, related_token=PROXY, normalize=True)
    assert PK in fixed and ATTR in fixed, (
        "normalized accumulation missing pk/attr: %r" % fixed)
    # Pre-patch (raw proxy key): the pk is scattered out of the concrete set.
    buggy = accumulate(CONCRETE, PK, ATTR, related_token=PROXY, normalize=False)
    assert ATTR in buggy and PK not in buggy, (
        "raw-key accumulation should drop the pk from the concrete set: %r"
        % buggy)
    # When the related model is already concrete (not an alias), both agree.
    same = accumulate(CONCRETE, PK, ATTR, related_token=CONCRETE, normalize=False)
    assert PK in same and ATTR in same, (
        "non-alias accumulation should keep pk regardless: %r" % same)


def main():
    configure_django()
    concrete, proxy, proxy2 = build_models()
    check_concrete_model(concrete, proxy, proxy2)
    check_accumulation()
    print("G-AX OK: canonical_of == _meta.concrete_model (proxy->concrete, "
          "concrete->self, idempotent) and the related-model pk lands in the "
          "concrete reported set iff the canonical normalization is applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
