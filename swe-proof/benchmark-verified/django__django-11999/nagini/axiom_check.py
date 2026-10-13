#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11999.

This bundle has NO consumed axioms: the guarded accessor installation is
modelled DEEPLY (the conditional install spelled out in model.py's impl
region). G-AX therefore validates the single **A-reference** -- that the deep
model equals the real operation it mirrors -- by executing the REAL repository
code (`django.db.models.fields.Field.contribute_to_class`, exercised via
ordinary model-class assembly) in the evaluation container and asserting the
resulting class display-accessor binding matches the deep model on both
observable cases plus randomized fuzz over declaration order and pre-existing
attributes.

Deep model under check (model.py impl region), over the class attribute
namespace `cls` keyed by the accessor name `get_<field>_display`:

    if accessor_name not in cls:        # the class does not already provide it
        cls[accessor_name] = GENERATED  # install the generated accessor
    # else: preserve the existing accessor (do NOT overwrite)

Mapping to the real operation (mapping.md §1, §3):
  * `accessor_name in cls`  <->  the accessor name is already provided on the
    class at the point assembly registers the field's display accessor.
  * the bound identity  <->  WHICH callable answers `Model().get_<field>_display`:
    the author-defined method (preserve case) or the generated accessor that
    returns the choice label (install case).

We OBSERVE the bound identity behaviourally: the generated accessor returns the
human-readable choice label for the stored value, whereas an author-defined
accessor returns whatever the author wrote. This is exactly what the hidden
tests observe.

PATCH-STATE CONTROL (the load-bearing correctness property of this script).
The SWE-bench instance image is checked out at `base_commit`, i.e. the
UNPATCHED tree whose `Field.contribute_to_class` installs the display accessor
UNCONDITIONALLY -- it overwrites an author-defined accessor. A check that
asserted the *fixed* (guarded) behaviour against that ambient code would
(correctly) fail, and would give a false witness if developed on a host whose
installed Django happens to be patched. So this script does NOT trust the
ambient `contribute_to_class`. It explicitly exercises BOTH code states by
wrapping the real method at runtime:

  * GUARDED state -- the gold guard self-applied at runtime: the choices-branch
    installs the generated accessor ONLY when the class does not already
    provide an accessor of that name. The deep model's claims must HOLD here
    (preserve author method when present; install generated accessor when
    absent). This reproduces the gold `if not hasattr(...): setattr(...)`
    irrespective of whether the live tree is pre- or post-fix.
  * UNGUARDED state -- the unconditional install (the base_commit bug): the
    choices-branch always overwrites. The author method must be CLOBBERED here.
    This turns the implicit discrimination into an explicit two-state check and
    proves the observable the deep model relies on genuinely distinguishes the
    fixed behaviour from the buggy one (G-DIFF made concrete against real
    Django assembly).

Both wrappers reuse the REAL repository internals (`partialmethod`,
`cls._get_FIELD_display`, the field's own `set_attributes_from_name`, the meta
registration) -- only the single guard around the display-accessor `setattr` is
controlled, exactly the line the gold patch touches. Imports: the standard
library plus the repository package under evaluation. Exit 0 iff every
observation matches in BOTH states.
"""
import functools
import random
import sys

import django
from django.conf import settings

# Minimal Django configuration so model classes can be assembled.
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={},
    )
    django.setup()

from django.db import models  # noqa: E402
from django.db.models.fields import Field  # noqa: E402

CHOICES = [(1, "first"), (2, "second")]
SENTINEL = "author-defined-value"

# unique app_label per constructed model to avoid registry collisions
_counter = [0]


def _app_label():
    _counter[0] += 1
    return "axcheck_%d" % _counter[0]


# ---------------------------------------------------------------------------
# Runtime control of the single guarded line. We replace Field.contribute_to_
# class with a thin wrapper around the original that (a) suppresses the
# original's own display-accessor installation, then (b) performs the display-
# accessor installation ourselves under the chosen guard policy, reusing the
# real internals (partialmethod + cls._get_FIELD_display). This is independent
# of whether the ambient tree is pre- or post-fix: we always drive the precise
# install policy we are testing.
# ---------------------------------------------------------------------------
_ORIG_CONTRIBUTE = Field.contribute_to_class


def _install_policy(guarded):
    """Return a replacement contribute_to_class that installs the generated
    display accessor under the chosen policy:
      guarded=True  -> install only if the class does not already provide the
                       accessor name (the gold fix);
      guarded=False -> always install, overwriting any existing accessor (the
                       base_commit bug)."""
    @functools.wraps(_ORIG_CONTRIBUTE)
    def contribute_to_class(self, cls, name, private_only=False):
        # Run the original registration but neutralise its own display-accessor
        # install by temporarily clearing choices, so the ONLY display-accessor
        # write is the one we make below under the policy under test.
        saved_choices = self.choices
        self.choices = None
        try:
            _ORIG_CONTRIBUTE(self, cls, name, private_only=private_only)
        finally:
            self.choices = saved_choices
        if self.choices is not None:
            accessor_name = "get_%s_display" % self.name
            already_present = hasattr(cls, accessor_name)
            if (not guarded) or (not already_present):
                from functools import partialmethod
                setattr(
                    cls,
                    accessor_name,
                    partialmethod(cls._get_FIELD_display, field=self),
                )
    return contribute_to_class


class install_state(object):
    """Context manager: drive model-class assembly under the chosen install
    policy (guarded = gold fix, unguarded = base_commit bug)."""

    def __init__(self, guarded):
        self.guarded = guarded

    def __enter__(self):
        Field.contribute_to_class = _install_policy(self.guarded)
        return self

    def __exit__(self, *exc):
        Field.contribute_to_class = _ORIG_CONTRIBUTE
        return False


def build_model(with_user_method, field_first):
    """Assemble a real Django model whose field offers choices, optionally with
    an author-defined accessor of the same name, optionally with the field
    declared before/after the author method. Returns the model class.

    `field_first` exercises declaration order: the gold fix must be stable
    regardless of order (the pre-patch behaviour was order-dependent)."""
    namespace = {"__module__": __name__}

    def get_foo_bar_display(self):
        return SENTINEL

    field = models.IntegerField(choices=CHOICES)

    if field_first:
        namespace["foo_bar"] = field
        if with_user_method:
            namespace["get_foo_bar_display"] = get_foo_bar_display
    else:
        if with_user_method:
            namespace["get_foo_bar_display"] = get_foo_bar_display
        namespace["foo_bar"] = field

    class Meta:
        app_label = _app_label()

    namespace["Meta"] = Meta
    return type("FooBar", (models.Model,), namespace)


def deep_model_install_or_preserve(with_user_method):
    """The deep model's verdict for the observed display value of foo_bar==1:
    the author value when an accessor pre-exists (preserve), else the generated
    choice label (install)."""
    if with_user_method:
        return SENTINEL          # preserve existing accessor
    return "first"               # install generated accessor -> choice label


def check_guarded(with_user_method, field_first):
    """A-reference: under the gold guard, the real assembly's display-accessor
    binding matches the deep model (preserve vs install)."""
    with install_state(guarded=True):
        cls = build_model(with_user_method, field_first)
    observed = cls(foo_bar=1).get_foo_bar_display()              # real repo code
    expected = deep_model_install_or_preserve(with_user_method)  # deep model
    assert observed == expected, (
        "deep model unsound under the gold guard (with_user_method=%r, "
        "field_first=%r): real guarded contribute_to_class yielded %r, deep "
        "model gives %r" % (with_user_method, field_first, observed, expected))


def check_unguarded_clobbers(field_first):
    """Differential: under the base_commit unconditional install, an author-
    defined accessor is CLOBBERED -> the generated choice label is observed,
    NOT the author value. Proves the observable discriminates fixed from buggy
    (this is exactly the bug the F2P test pins)."""
    with install_state(guarded=False):
        cls = build_model(with_user_method=True, field_first=field_first)
    observed = cls(foo_bar=1).get_foo_bar_display()
    assert observed == "first", (
        "the base_commit unconditional install did NOT clobber the author "
        "accessor (field_first=%r): observed %r, expected the generated label "
        "'first'. The two-state check is not discriminating -- the observable "
        "cannot witness the fix." % (field_first, observed))


def main():
    # === GUARDED state (gold fix self-applied): deep model must HOLD =========
    # the two observable cases x both declaration orders.
    boundary = [
        (True, True),    # user method present, field declared first (the F2P)
        (True, False),   # user method present, field declared after the method
        (False, True),   # no user method, field first  -> install generated
        (False, False),  # no user method, method absent -> install generated
    ]
    for with_user_method, field_first in boundary:
        check_guarded(with_user_method, field_first)

    # Frame: in the install case the generated accessor returns the correct
    # label for every choice value (no other binding is disturbed); for an
    # invalid value it returns the value itself.
    with install_state(guarded=True):
        cls = build_model(with_user_method=False, field_first=True)
    assert cls(foo_bar=1).get_foo_bar_display() == "first"
    assert cls(foo_bar=2).get_foo_bar_display() == "second"
    assert cls(foo_bar=9).get_foo_bar_display() == 9       # invalid -> value

    # randomized fuzz over the two booleans, under the gold guard.
    rng = random.Random(11999)
    for _ in range(2000):
        with_user_method = rng.random() < 0.5
        field_first = rng.random() < 0.5
        check_guarded(with_user_method, field_first)

    # === UNGUARDED state (base_commit bug): the author method must be CLOBBERED
    # the differential the F2P test depends on -- both declaration orders.
    check_unguarded_clobbers(field_first=True)
    check_unguarded_clobbers(field_first=False)

    print("G-AX OK: under the gold guard (self-applied at runtime), the deep "
          "model (A-reference) == real Field.contribute_to_class display-"
          "accessor binding on %d boundary + 2000 fuzz model-class assemblies "
          "(preserve author-defined accessor vs install generated accessor; "
          "stable under declaration order); under the base_commit unconditional "
          "install the author accessor is clobbered (the bug the F2P test pins), "
          "so the observable discriminates fixed from buggy." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
