#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11999 (nagini).

SHADOW — the impl region of `model.py`, copied VERBATIM with only the contract
calls stripped. Both modelled functions (`preserve_existing_accessor`,
`install_missing_accessor`) share one byte-identical impl region

    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()

which is plain executable Python over a `Dict[int, int]`, so it runs as-is; the
two `@Pure` helpers it depends on (`generated_accessor`, `other_name`) are
copied over minus their contracts. No `PSeq`/`ToSeq` carrier appears in this
model, so no sequence shim is needed. There is no `@ContractOnly` callee
(mapping.md §3: "no consumed axioms" — the guarded installation is modelled
deeply), so nothing here is assumed; every branch is executed.

ORACLE — the REAL patched repo function is CALLED, not transliterated:
`django.db.models.fields.Field.contribute_to_class`
(`django/db/models/fields/__init__.py:749-767` @ base_commit; the gold patch
rewrites lines 765-767 into the guarded form). The gate applies patch.diff to
/testbed and sets PYTHONPATH before this script runs; the script additionally
ASSERTS via `inspect.getsource` that the ambient `contribute_to_class` really
carries the patched guard `if not hasattr(cls, 'get_%s_display' % self.name)`,
and exits non-zero if not. That guard matters: the stock instance image is
checked out at base_commit, where the install is UNCONDITIONAL, so a script
that silently ran against unpatched code would be diffing the shadow against
the bug. The real function is driven by real Django model-class assembly: a
`models.IntegerField(choices=...)` is contributed to a real `ModelBase` class
built with `type(...)`, exactly as `ModelBase.__new__` does via
`add_to_class`. No reimplementation of the patched line exists in this file.

TYPE BRIDGE (mapping.md §2, inverted) — the model carrier is a
`Dict[int, int]` from an attribute-NAME token to a method-IDENTITY token; the
repo reality is a real class whose attribute namespace is read along its MRO.
Concretisation: name token -> a real attribute name string (token 1 =
`other_name()` -> an unrelated method already on the class; token 2 = the
accessor name `'get_%s_display' % field.name`; tokens 3..5 = further unrelated
names, optionally inherited); identity token -> a real bound object (0 =
`generated_accessor()` -> the `partialmethod(cls._get_FIELD_display,
field=self)` the patched `setattr` installs, recognised structurally by
`.func`/`.keywords`; 101..104 = distinct author-defined accessors/attributes,
all `!= 0`). Abstraction: a real class is lifted back to `Dict[int, int]` by
looking each tracked name up along `cls.__mro__` (`hasattr` <-> key membership)
and mapping the bound object to its identity token. The model's `Old(cls)` is
obtained by assembling the SAME class shape with `choices=None`, which makes
the patched branch a no-op, so the observed difference is exactly the modelled
operation and nothing else.

WHICH modelled function runs is decided by the concretised pre-state, so every
generated input satisfies the chosen function's `Requires` by construction:
`preserve_existing_accessor` when token 2 is already a key (the class already
provides `get_<field>_display`, from its own body or inherited), else
`install_missing_accessor`. The remaining Requires (`other_name() in cls`,
`other_name() != accessor_name`) are guaranteed by the bridge and re-checked at
runtime; an input that fails them is not counted.

OBSERVABLE — the full post-state, not just the accessor: the tracked
name->identity dict is compared key-for-key, AND the whole flattened MRO
key-set of the assembled class is diffed pre/post, requiring the only added
name to be the accessor (nothing else added, removed or rebound). That is the
executable reading of the model's whole-namespace frame `Ensures`.

INPUT DOMAIN — the structural space is finite and enumerated EXHAUSTIVELY
first (4 accessor placements x 4 accessor identities x 4 unrelated-attribute
identities x 8 tracked-extra configurations x 5 field names = 2560 shapes,
covering both modelled functions and both impl branches, plus the exact F2P
shape `get_foo_bar_display` defined in the model body), then seeded fuzz over
the same space fills the count to >= 1e5. Exhaustive coverage of the finite
structural space is a stronger check than 1e5 samples of it, not a weaker one.
Pinned seed: 11999 (recorded in mapping.md §G-CONF).

DISCRIMINATION SELF-TEST — after the differential passes, the check re-runs a
handful of accessor-present shapes with the display-accessor install forced
into its base_commit UNGUARDED form (wrapping the real method, reusing the real
`partialmethod`/`cls._get_FIELD_display` internals, restoring it afterwards)
and requires the differential to REPORT a disagreement there. If the shadow
were to agree with the buggy code too, this check would be vacuous, so failing
to catch it exits non-zero.

Exit 0 iff zero disagreements against the patched function (and the
discrimination self-test fires). On a disagreement the input shape and both
outputs are printed and the exit status is 1. stdlib + Django only.
"""
import functools
import inspect
import json
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={},
    )
    django.setup()

from django.db import models                        # noqa: E402
from django.db.models.base import Model             # noqa: E402
from django.db.models.fields import Field           # noqa: E402

SEED = 11999
N_TOTAL = 100_000          # >= 1e5 Requires-satisfying inputs

# ---------------------------------------------------------------------------
# SHADOW: model.py's impl region, verbatim, contracts stripped.
# ---------------------------------------------------------------------------
# pure-start (model.py @Pure helpers, minus contracts)
def generated_accessor() -> int:
    # The method-identity token of the generated display accessor that
    # assembly would install for a field offering selectable values.
    return 0


def other_name() -> int:
    # A representative pre-existing, unrelated class-attribute name (some other
    # method or attribute the class already carries). It witnesses that the
    # operation leaves attributes other than the accessor name untouched.
    return 1
# pure-end


def preserve_existing_accessor(cls, accessor_name):
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end


def install_missing_accessor(cls, accessor_name):
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end


# ---------------------------------------------------------------------------
# TYPE BRIDGE (mapping.md §2, inverted)
# ---------------------------------------------------------------------------
CHOICES = [(1, "first"), (2, "second")]

# name tokens: 1 == other_name(), 2 == the accessor name, 3..5 == further
# unrelated attribute names (the accessor token must differ from other_name()).
NAME_OTHER = 1
NAME_ACCESSOR = 2
NAME_EXTRAS = (3, 4, 5)

# concrete attribute-name strings for the non-accessor tokens
NAME_STRINGS = {
    NAME_OTHER: "unrelated_helper",
    3: "aux_method",
    4: "zeta_attr",
    5: "label_helper",
}

# identity tokens for author-defined bindings: every one differs from
# generated_accessor() == 0.
IDENT_GENERATED = 0


def _author_one(self):
    return "author-one"


def _author_two(self):
    return "author-two"


def _author_three(self):
    return "author-three"


AUTHOR_IDENTITIES = {
    101: _author_one,
    102: _author_two,
    103: _author_three,
    104: "author-plain-attribute-value",   # a non-callable binding
}

PLACEMENTS = ("absent", "own", "parent", "grandparent")
FIELD_NAMES = ("foo_bar", "x", "status", "field_1", "a")
MODULE = "django.contrib.contenttypes.models"
MISSING = object()

# names Django itself binds during assembly; excluded from the untracked
# key-set frame diff only where they legitimately differ between two distinct
# class objects built for the same shape.
_SKIP_KEYS = frozenset({"__qualname__", "__doc__", "__dict__", "__weakref__"})


def accessor_name_str(field_name):
    """mapping.md §2: the accessor name is `'get_%s_display' % self.name`."""
    return "get_%s_display" % field_name


def _mro_lookup(cls, name):
    for klass in cls.__mro__:
        if name in klass.__dict__:
            return klass.__dict__[name]
    return MISSING


def _identity_token(obj, field):
    """Concrete bound object -> model identity token (mapping.md §2)."""
    if isinstance(obj, functools.partialmethod):
        # the generated accessor: partialmethod(cls._get_FIELD_display, field=self)
        if obj.func is Model._get_FIELD_display and obj.keywords.get("field") is field:
            return IDENT_GENERATED
        return -2                       # some other partialmethod: not modelled
    for token, value in AUTHOR_IDENTITIES.items():
        if obj is value:
            return token
    return -1                           # an unmodelled binding


def _namespace_keys(cls):
    """Flattened MRO key-set of the assembled class (the whole namespace whose
    frame the model's Forall clauses constrain)."""
    keys = set()
    for klass in cls.__mro__:
        keys |= set(klass.__dict__) - _SKIP_KEYS
    return keys


_counter = [0]


def assemble(shape, with_choices):
    """Concretise a shape into a REAL Django model class and contribute a real
    field to it via the REAL `Field.contribute_to_class`.

    with_choices=False makes the patched branch a no-op (`self.choices is None`),
    which yields the model's `Old(cls)`; with_choices=True runs the modelled
    operation.
    """
    _counter[0] += 1
    idx = _counter[0]
    field_name = shape["field_name"]
    accessor = accessor_name_str(field_name)

    own, parent, grandparent = {}, {}, {}
    where = {"own": own, "parent": parent, "grandparent": grandparent}

    # token 1 (other_name()) is always present on the class: a Requires.
    own[NAME_STRINGS[NAME_OTHER]] = AUTHOR_IDENTITIES[shape["other_ident"]]
    for token, (ident, place) in shape["extras"].items():
        where[place][NAME_STRINGS[token]] = AUTHOR_IDENTITIES[ident]
    if shape["accessor_where"] != "absent":
        where[shape["accessor_where"]][accessor] = \
            AUTHOR_IDENTITIES[shape["accessor_ident"]]

    def ns(extra):
        d = {"__module__": MODULE,
             "Meta": type("Meta", (), {"app_label": "contenttypes",
                                       "abstract": True})}
        d.update(extra)
        return d

    base = models.Model
    if grandparent:
        base = type("GP%d" % idx, (base,), ns(grandparent))
    if parent or grandparent:
        base = type("P%d" % idx, (base,), ns(parent))
    cls = type("C%d" % idx, (base,), ns(own))

    field = models.IntegerField(choices=CHOICES if with_choices else None)
    # >>> the real patched repo function under test <<<
    field.contribute_to_class(cls, field_name)
    return cls, field, accessor


def abstract(cls, field, accessor):
    """Real class -> the model's `Dict[int, int]` carrier."""
    carrier = {}
    names = dict(NAME_STRINGS)
    names[NAME_ACCESSOR] = accessor
    for token, name in names.items():
        obj = _mro_lookup(cls, name)
        if obj is not MISSING:
            carrier[token] = _identity_token(obj, field)
    return carrier


# ---------------------------------------------------------------------------
# the differential
# ---------------------------------------------------------------------------
def differential(shape):
    """Run both sides on one shape. Returns (which_function, ok, detail)."""
    pre_cls, pre_field, accessor = assemble(shape, with_choices=False)
    pre = abstract(pre_cls, pre_field, accessor)
    pre_keys = _namespace_keys(pre_cls)

    # Requires of both modelled functions (mapping.md §2 keeps these exact):
    #   dict_pred(cls); other_name() in cls; other_name() != accessor_name
    if NAME_OTHER not in pre or NAME_ACCESSOR == NAME_OTHER:
        return None, True, "requires-unsatisfied"
    # the pre-state must not already carry a generated accessor: the modelled
    # operation has not run yet.
    if pre.get(NAME_ACCESSOR) == IDENT_GENERATED:
        return None, False, ("pre-state already carries the generated accessor "
                             "(choices=None did not neutralise the branch): %r" % pre)

    # SHADOW: dispatch on the Requires that distinguishes the two cases.
    shadow = dict(pre)
    if NAME_ACCESSOR in shadow:
        which = "preserve_existing_accessor"
        preserve_existing_accessor(shadow, NAME_ACCESSOR)
    else:
        which = "install_missing_accessor"
        install_missing_accessor(shadow, NAME_ACCESSOR)

    # ORACLE: the same shape assembled with the field offering choices, i.e.
    # the real patched `contribute_to_class` branch actually taken.
    post_cls, post_field, _ = assemble(shape, with_choices=True)
    oracle = abstract(post_cls, post_field, accessor)
    post_keys = _namespace_keys(post_cls)

    if shadow != oracle:
        return which, False, ("carrier mismatch: pre=%r shadow=%r oracle=%r"
                              % (pre, shadow, oracle))
    # frame: the ONLY namespace name the operation may add is the accessor.
    added = post_keys - pre_keys
    removed = pre_keys - post_keys
    expected_added = set() if NAME_ACCESSOR in pre else {accessor}
    if added != expected_added or removed:
        return which, False, ("namespace frame violated: added=%r removed=%r "
                              "expected_added=%r" % (sorted(added), sorted(removed),
                                                     sorted(expected_added)))
    return which, True, ""


# ---------------------------------------------------------------------------
# inputs: exhaustive over the finite structural space, then seeded fuzz
# ---------------------------------------------------------------------------
EXTRA_CONFIGS = []
for _mask in range(8):
    _cfg = tuple(NAME_EXTRAS[i] for i in range(3) if _mask & (1 << i))
    EXTRA_CONFIGS.append(_cfg)


def _shape(field_name, accessor_where, accessor_ident, other_ident,
           extra_tokens, extra_idents, extra_places):
    return {
        "field_name": field_name,
        "accessor_where": accessor_where,
        "accessor_ident": accessor_ident,
        "other_ident": other_ident,
        "extras": {t: (extra_idents[i], extra_places[i])
                   for i, t in enumerate(extra_tokens)},
    }


def enumerate_shapes():
    """The finite structural space, exhaustively (2560 shapes)."""
    idents = sorted(AUTHOR_IDENTITIES)
    for field_name in FIELD_NAMES:
        for accessor_where in PLACEMENTS:
            for accessor_ident in idents:
                for other_ident in idents:
                    for cfg in EXTRA_CONFIGS:
                        n = len(cfg)
                        yield _shape(
                            field_name, accessor_where, accessor_ident,
                            other_ident, cfg,
                            [idents[(accessor_ident + i) % len(idents)]
                             for i in range(n)],
                            [PLACEMENTS[1 + ((accessor_ident + i) % 3)]
                             for i in range(n)],
                        )


def boundary_shapes():
    """Named boundary cases, first — including the exact F2P shape."""
    idents = sorted(AUTHOR_IDENTITIES)
    out = [
        # the F2P: a model body that defines its own get_foo_bar_display
        _shape("foo_bar", "own", 101, 102, (), [], []),
        # the same accessor inherited from a parent / grandparent
        _shape("foo_bar", "parent", 101, 102, (), [], []),
        _shape("foo_bar", "grandparent", 101, 102, (), [], []),
        # no accessor anywhere: the generated one must be installed
        _shape("foo_bar", "absent", 101, 102, (), [], []),
        # singleton namespace: only the required unrelated attribute
        _shape("x", "absent", 101, 101, (), [], []),
        # accessor present alongside every tracked extra, all placements
        _shape("status", "own", 104, 103, NAME_EXTRAS, idents[:3],
               ["own", "parent", "grandparent"]),
        _shape("status", "absent", 104, 103, NAME_EXTRAS, idents[:3],
               ["own", "parent", "grandparent"]),
        # a non-callable author binding under the accessor name
        _shape("field_1", "own", 104, 104, (), [], []),
    ]
    return out


def fuzz_shape(rng):
    idents = sorted(AUTHOR_IDENTITIES)
    cfg = rng.choice(EXTRA_CONFIGS)
    return _shape(
        rng.choice(FIELD_NAMES),
        rng.choice(PLACEMENTS),
        rng.choice(idents),
        rng.choice(idents),
        cfg,
        [rng.choice(idents) for _ in cfg],
        [rng.choice(PLACEMENTS[1:]) for _ in cfg],
    )


# ---------------------------------------------------------------------------
# discrimination self-test: the base_commit UNGUARDED install must be caught
# ---------------------------------------------------------------------------
_ORIG_CONTRIBUTE = Field.contribute_to_class


def _unguarded_contribute(self, cls, name, private_only=False):
    """base_commit's unconditional install, reusing the real internals: the
    original runs with the display branch neutralised, then we install
    unconditionally (the bug the gold patch removes)."""
    saved = self.choices
    self.choices = None
    try:
        _ORIG_CONTRIBUTE(self, cls, name, private_only=private_only)
    finally:
        self.choices = saved
    if self.choices is not None:
        setattr(cls, "get_%s_display" % self.name,
                functools.partialmethod(cls._get_FIELD_display, field=self))


def discrimination_self_test():
    """With the buggy unguarded install in place, the differential MUST report a
    disagreement for accessor-present shapes; otherwise it is vacuous."""
    shapes = [_shape("foo_bar", w, 101, 102, (), [], [])
              for w in ("own", "parent", "grandparent")]
    Field.contribute_to_class = _unguarded_contribute
    try:
        return [differential(s)[1] for s in shapes]
    finally:
        Field.contribute_to_class = _ORIG_CONTRIBUTE


def main():
    # The oracle must be the PATCHED function; refuse to run against base_commit.
    src = inspect.getsource(Field.contribute_to_class)
    if "if not hasattr(cls, 'get_%s_display' % self.name)" not in src:
        print("G-CONF ERROR: ambient Field.contribute_to_class is NOT the "
              "patched (guarded) version; the oracle would be the base_commit "
              "bug. Refusing to run.")
        print(json.dumps({"checked": 0, "disagreements": 0,
                          "unsupported": "oracle not patched"}))
        return 1

    rng = random.Random(SEED)
    checked = 0
    per_function = {"preserve_existing_accessor": 0, "install_missing_accessor": 0}
    skipped = 0

    n_boundary = 0
    n_enumerated = 0

    def run(shape, kind):
        nonlocal checked, skipped
        which, ok, detail = differential(shape)
        if not ok:
            print("G-CONF FAIL (%s case): shadow of model.py impl region "
                  "disagrees with the real patched "
                  "django.db.models.fields.Field.contribute_to_class" % kind)
            print("  shape    = %r" % (shape,))
            print("  function = %s" % which)
            print("  %s" % detail)
            return False
        if which is None:
            skipped += 1
            return True
        per_function[which] += 1
        checked += 1
        return True

    for shape in boundary_shapes():
        n_boundary += 1
        if not run(shape, "boundary"):
            return 1

    for shape in enumerate_shapes():
        n_enumerated += 1
        if not run(shape, "exhaustive"):
            return 1

    n_fuzz = 0
    while checked < N_TOTAL:
        n_fuzz += 1
        if not run(fuzz_shape(rng), "fuzz"):
            return 1

    if min(per_function.values()) == 0:
        print("G-CONF FAIL: one modelled function was never exercised: %r"
              % per_function)
        return 1

    caught = discrimination_self_test()
    if not all(not ok for ok in caught):
        print("G-CONF FAIL: discrimination self-test did not fire — the shadow "
              "agrees with the base_commit UNGUARDED install too, so the "
              "differential is vacuous (results=%r)" % (caught,))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py "
          "(preserve_existing_accessor / install_missing_accessor) agrees with "
          "the real patched Field.contribute_to_class on %d inputs "
          "(%d boundary + %d exhaustive over the finite structural space + %d "
          "fuzz, seed=%d); preserve=%d install=%d; 0 disagreements; the same "
          "differential catches the base_commit unguarded install 3/3."
          % (checked, n_boundary, n_enumerated, n_fuzz, SEED,
             per_function["preserve_existing_accessor"],
             per_function["install_missing_accessor"]))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "boundary": n_boundary,
        "exhaustive": n_enumerated,
        "fuzz": n_fuzz,
        "requires_unsatisfied_skipped": skipped,
        "per_function": per_function,
        "oracle": "django.db.models.fields.Field.contribute_to_class (called, patched)",
        "shadow": "direct (contract-stripped impl region)",
        "discrimination_self_test": "unguarded base_commit install caught 3/3",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
