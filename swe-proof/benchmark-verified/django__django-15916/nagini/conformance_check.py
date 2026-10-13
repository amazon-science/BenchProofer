#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15916 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The single @Pure helper ``resolve_attr``
copies over as a plain function. There are no @ContractOnly callees and no
PSeq usage in this bundle (all carriers are ints).

ORACLE: the REAL patched repo behaviour the model models per mapping.md --
which per-field builder ends up driving field construction:

  * ``declared_form_callback``  <->  a directly-declared model form class
    (real metaclass + options object) whose inner options ``Meta`` may carry a
    builder of its own and may inherit one through its parent ``Meta`` type;
  * ``factory_form_callback``   <->  a form class produced by the run-time
    factory from a base form (real ``modelform_factory``), optionally handed a
    builder, with the base form's options carrying an (own, inherited) pair;
    a further plain subclass of the produced class is asserted to resolve the
    same builder (the model's docstring covers subclasses of the produced
    class).

The gate applies patch.diff to /testbed before this script runs, so the
imported ``django.forms`` machinery is the patched code.

TYPE BRIDGE (mapping.md section 2): builder callables <-> positive integer
identity codes, ``None``/absent <-> 0. Realised with distinct stand-in
callables, one per code, each tagging the form field it builds; the code of
the builder that drove construction is read back off the produced field
(absence of a tag == 0 == the model default built the field). The
``staticmethod`` wrapper is identity on builder identity. The options pair
(own, inherited) is realised as a ``Meta`` type whose parent type carries the
inherited builder -- ordinary attribute resolution, exactly the carrier the
model abstracts.

INPUT DOMAIN: the preconditions demand only non-negative codes. Coverage:
exhaustive grid over codes 0..7 for both functions (every presence/absence/
shadowing configuration, far beyond the 2-identity minimum needed to
distinguish the branches) + 50000 fuzz draws per function mixing small codes
with large random codes (fresh callable identities minted on demand, so large
codes are genuinely distinct identities). Total >= 1e5 Requires-satisfying
inputs. Pinned fuzz seed: 15916. Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15916
N_FUZZ = 50000  # iterations; each checks both modeled functions (2 inputs)


# --- pure helper from model.py, contracts stripped ----------------------------

def resolve_attr(own, inherited):
    """Ordinary attribute resolution on an options object: an attribute set
    directly on the object (own != 0) shadows the one inherited from its
    parent (inherited); when the object sets nothing of its own (own == 0) the
    inherited value is seen. 0 denotes "attribute absent" on either level."""
    if own != 0:
        return own
    return inherited


# --- impl regions of model.py, verbatim, contract calls stripped --------------

def declared_form_callback(meta_own, meta_inherited):
    # The options object stores its resolved builder; the constructor reads it
    # straight from there to drive field construction.
    stored = resolve_attr(meta_own, meta_inherited)
    return stored


def factory_form_callback(passed, base_meta_own, base_meta_inherited):
    # The factory records the passed builder on the produced options object
    # only when one was given; it never injects an overriding "no builder".
    # The produced options object therefore resolves (passed shadows the
    # inherited base builder), and the constructor reads that resolved value.
    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
    produced_own = passed  # 0 when nothing was passed -> inherited is seen
    stored = resolve_attr(produced_own, produced_inherited)
    return stored


# --- oracle: the real patched form machinery ----------------------------------

def _django_setup():
    import django
    from django.conf import settings
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
    django.setup()


class _Bridge(object):
    """code <-> distinct builder callable; the builder tags the field it
    builds so the driving builder's identity is observable on the class."""

    def __init__(self):
        self._pool = {}

    def builder_of(self, code):
        if code == 0:
            return None
        fn = self._pool.get(code)
        if fn is None:
            def fn(db_field, _code=code, **kwargs):
                ff = db_field.formfield(**kwargs)
                ff._conf_code = _code
                return ff
            self._pool[code] = fn
        return fn


def _make_oracle():
    _django_setup()
    from django import forms
    from django.db import models
    from django.forms.models import modelform_factory

    class ConfThing(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "conf_shadow"

    bridge = _Bridge()

    def code_of(form_cls):
        return getattr(form_cls.base_fields["name"], "_conf_code", 0)

    def meta_type(bases, own_fn, with_model=False):
        attrs = {}
        if with_model:
            attrs["model"] = ConfThing
            attrs["fields"] = ["name"]
        if own_fn is not None:
            attrs["formfield_callback"] = staticmethod(own_fn)
        return type("Meta", tuple(bases), attrs)

    def real_declared(meta_own, meta_inherited):
        """Directly-declared form: its options Meta may carry a builder of its
        own and inherits through its parent Meta type."""
        parent = meta_type((), bridge.builder_of(meta_inherited))
        meta = meta_type((parent,), bridge.builder_of(meta_own),
                         with_model=True)
        form_cls = type("DeclaredForm", (forms.ModelForm,), {"Meta": meta})
        return code_of(form_cls)

    def real_factory(passed, base_meta_own, base_meta_inherited):
        """Factory-produced form: base form's options carry (own, inherited);
        the factory is handed `passed` (0 == none). Also asserts a further
        plain subclass of the produced class resolves the same builder."""
        base_parent = meta_type((), bridge.builder_of(base_meta_inherited))
        base_meta = meta_type((base_parent,),
                              bridge.builder_of(base_meta_own),
                              with_model=True)
        base_form = type("BaseForm", (forms.ModelForm,), {"Meta": base_meta})
        kwargs = {}
        passed_fn = bridge.builder_of(passed)
        if passed_fn is not None:
            kwargs["formfield_callback"] = passed_fn
        produced = modelform_factory(ConfThing, form=base_form, **kwargs)
        got = code_of(produced)
        sub = type("SubForm", (produced,), {})
        sub_got = code_of(sub)
        if sub_got != got:
            raise AssertionError(
                "subclass of the produced form resolves a different builder: "
                "produced=%d subclass=%d" % (got, sub_got))
        return got

    return real_declared, real_factory


# --- differential driver -------------------------------------------------------

def _check_declared(real_declared, mo, mi):
    shadow = declared_form_callback(mo, mi)
    real = real_declared(mo, mi)
    if shadow != real:
        print("DISAGREEMENT declared_form_callback(meta_own=%d, "
              "meta_inherited=%d):\n  shadow (impl region) = %d\n"
              "  real (patched repo, builder driving field construction) = %d"
              % (mo, mi, shadow, real))
        return False
    return True


def _check_factory(real_factory, p, bo, bi):
    shadow = factory_form_callback(p, bo, bi)
    real = real_factory(p, bo, bi)
    if shadow != real:
        print("DISAGREEMENT factory_form_callback(passed=%d, "
              "base_meta_own=%d, base_meta_inherited=%d):\n"
              "  shadow (impl region) = %d\n"
              "  real (patched repo, builder driving field construction) = %d"
              % (p, bo, bi, shadow, real))
        return False
    return True


def main():
    real_declared, real_factory = _make_oracle()
    checked = 0

    # exhaustive boundary grid: every presence/absence/shadowing configuration
    # over 8 distinct identities per slot (0 == absent)
    for mo in range(8):
        for mi in range(8):
            if not _check_declared(real_declared, mo, mi):
                return 1
            checked += 1
    for p in range(8):
        for bo in range(8):
            for bi in range(8):
                if not _check_factory(real_factory, p, bo, bi):
                    return 1
                checked += 1
    n_boundary = checked

    # pinned-seed fuzz: mostly small codes (dense shadowing interactions),
    # sometimes large random codes (fresh distinct identities)
    rng = random.Random(SEED)

    def draw():
        return rng.randint(0, 3) if rng.random() < 0.8 \
            else rng.randint(4, 10 ** 9)

    for _ in range(N_FUZZ):
        if not _check_declared(real_declared, draw(), draw()):
            return 1
        if not _check_factory(real_factory, draw(), draw(), draw()):
            return 1
        checked += 2

    print("G-CONF OK: shadow impl == real patched builder selection on %d "
          "inputs (%d exhaustive-grid + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, 2 * N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
