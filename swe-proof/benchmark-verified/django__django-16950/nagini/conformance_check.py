#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16950 (nagini).

Refutes (does not prove) the R/I refinement leg of `model.py`'s impl region:
does the MODEL's clearing decision agree with the REAL patched repository
function it claims to model?  G-VERIFY says the impl meets the spec and G-PBT
says no wrong impl meets it; neither looks at django/forms/models.py at all.
This script is the only evidence that the theorem is about the right program.

======================================================================
ORACLE CHOICE: the REAL patched function, CALLED (not transliterated)
======================================================================
Oracle = `django.forms.models.BaseInlineFormSet.add_fields`
(mapping.md §1 -> `django/forms/models.py:1173-1181` at base_commit
f64fd47a7627ed6ffe2df2a32ded6ee528a784eb; the gold patch qualifying the
clearing guard has already been applied to /testbed by the gate).

Both sibling bundles (velvet/, lean/) TRANSLITERATE the patched decision block,
each justifying it as "we do NOT stand up a Django FormSet / model / ORM
(heavy)".  That justification does not hold in this container, and a
transliterated oracle only tests our reading of the patch, so this bundle does
NOT reuse it.  We measured it instead: an in-memory sqlite3 `DATABASES` plus
`connection.schema_editor().create_model(...)` stands up real parent/child
models, `inlineformset_factory` builds a real `BaseInlineFormSet` subclass, and
each `formset.add_fields(form, 0)` call costs ~45-115 us.  At 1e5 calls that is
seconds, so we drive the REAL METHOD on REAL Django model instances and observe
the REAL attribute it mutates via `setattr(self.instance, to_field.attname,
None)`.  Nothing about the patched guard is re-implemented here.

Two consequences worth stating, because they are what makes this check able to
fail:
  * We never compute the guard ourselves.  The oracle's answer is whatever the
    patched bytecode in /testbed does to `getattr(instance, attname)`.
  * We do not even hard-code WHICH attribute that is.  `to_field` resolution
    (`django/forms/models.py:1176-1179`, unchanged by the patch) is read back
    out of the real `InlineForeignKeyField` the real `add_fields` installed into
    `form.fields`, so our copy of that resolution is not in the trust chain.

SHADOW = the `# impl-start` / `# impl-end` region of model.py, copied VERBATIM
with only the contract calls deleted (`Requires`/`Ensures`/`Acc`/
`MustTerminate`).  Not restructured, not renamed, not simplified -- see
`shadow_reset_default_related_key` below, which is byte-for-byte the three
impl lines.  `ParentObject` and the `# pure-start` helper `should_clear` are
carried over the same way.  mapping.md §3 records NO `@ContractOnly` callee, so
there is no axiomatized callee to bridge.

======================================================================
TYPE BRIDGE (mapping.md §2, INVERTED)
======================================================================
The model works over the abstract carrier; the real function wants real Django
objects.  Both directions are written out explicitly.

  abstract -> concrete (input; `_CONFIGS`, `_plant`):
    adding=True/False       <- an UNSAVED parent instance (`_state.adding` is
                               naturally True) / a `parent.objects.create(...)`
                               row loaded as `instance=` (naturally False).
                               The flag is never poked by hand.
    key_has_default=T/F     <- a parent model whose related key is
                               `UUIDField(default=uuid.uuid4)` / one with no
                               field default (`AutoField` pk, plain
                               `BigIntegerField` alternate key).
    key_is_primary=T/F      <- the child's FK targets the parent's pk / targets
                               a unique non-pk column via `to_field=`.
    form_data_present=T/F   <- a BOUND formset built with a real management-form
                               data dict / an UNBOUND formset (`form.data` is
                               empty and falsey).
    instance.key: int       <- the generated default actually sitting in the
                               attribute: `uuid.UUID(int=k)` for a UUIDField,
                               `int(k)` for an integer column.

  concrete -> abstract (output; `_abstract`):
    getattr(instance, attname) is None  ->  None      (the cleared state)
    ... == the value we planted        ->  that same k (preserved unchanged)
    ... anything else                  ->  a poison sentinel that can only
                                           MISMATCH and be reported, so an
                                           oracle that rewrote the key to some
                                           third value cannot pass silently.

The four booleans are then RE-READ off the real objects immediately before each
call (`_observe`) rather than trusted from the table, so the shadow is fed the
observables the real guard itself reads.  A bridge that mis-realizes a combo is
caught at setup by `_verify_bridge`, which asserts every requested combo equals
the combo the real objects actually exhibit.

======================================================================
INPUTS: the modeled space is FINITE, so it is ENUMERATED EXHAUSTIVELY
======================================================================
The model's `Requires` is `Acc(instance.key)` + `MustTerminate(2)` -- it
constrains no value, so every (4 booleans x key value) input is admissible.
The BOOLEAN part of that space has exactly 2^4 = 16 points and all 16 are
realized by real Django objects (4 parent/child shapes x adding/saved x
bound/unbound), so we ENUMERATE ALL 16 rather than sample them: that is a
stronger check than 1e5 random draws, not a weaker one, because it leaves no
boolean combination unvisited.  Each of the impl's branches (outer `if adding`
not taken; taken with the guard false; taken with the guard true) is therefore
hit by construction.  We then fuzz the SAME space (uniformly over the 16
configs x random planted key values, pinned seed) to reach the >= 1e5 count.

Named boundary cases asserted explicitly, so the check cannot pass by avoiding
the branch the gold patch changed:
  * F2P `test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data`
    -- adding + default + ALTERNATE key + data present: the key must be
    PRESERVED.  `_assert_patch_branch_live` makes this a HARD precondition of
    the run: if the real oracle CLEARS here, the patched guard is not in
    /testbed and we exit 1 instead of reporting a vacuous pass.  This is the
    positive control that the input generator exercises the changed behaviour.
  * P2P `...ignores_default_pks_on_submit` -- adding + default + pk + data:
    CLEARED.
  * P2P `...nulls_default_pks_alternate_key_relation` -- adding + default +
    alternate key + NO data: CLEARED.

Exit 0 iff zero disagreements.  stdlib only (hypothesis adds no power over an
exhaustively enumerated finite space; the fuzz uses a pinned `random.Random`).
Pinned seed: 16950 -- also recorded in mapping.md under `## G-CONF`.
"""
import itertools
import json
import random
import sys
import uuid

SEED = 16950
N_FUZZ = 100_000

# =====================================================================
# SHADOW -- model.py's impl region, contracts stripped, otherwise verbatim.
# =====================================================================

# `class ParentObject` from model.py, minus Requires/Ensures.
class ParentObject:
    def __init__(self, key):
        self.key = key


# The `# pure-start` region of model.py, verbatim (the @Pure decorator and its
# docstring are contract-level; the returned expression is untouched).  Not
# called by the impl region -- carried so the deep model recorded in meta.json
# (`deep_model_references[0]`) is itself differentially checked against the real
# function's observable clear/preserve decision.
def should_clear(adding, key_has_default, key_is_primary, form_data_present):
    return (adding and key_has_default
            and (key_is_primary or not form_data_present))


def shadow_reset_default_related_key(instance, adding, key_has_default,
                                     key_is_primary, form_data_present):
    """`reset_default_related_key` from model.py with the pre/post-condition
    regions removed.  The three lines below are the `# impl-start` /
    `# impl-end` region copied character-for-character."""
    # impl-start
    if adding:
        if key_has_default and (key_is_primary or not form_data_present):
            instance.key = None
    # impl-end


# =====================================================================
# ORACLE -- real Django, real patched BaseInlineFormSet.add_fields.
# =====================================================================

def _boot_django():
    """Stand up a minimal real Django with an in-memory sqlite3 backend."""
    import django
    from django.conf import settings

    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    django.setup()


_APP = "auth"  # borrow an installed app label; these models are test-local


def _build_models():
    """Four real parent/child shapes spanning key_has_default x key_is_primary.

    key_has_default is realized by a real field default (UUIDField(default=
    uuid.uuid4), exactly the shape the F2P test uses); key_is_primary by whether
    the child's ForeignKey targets the parent pk or a unique non-pk column via
    to_field=.
    """
    from django.db import models

    class UUIDPKParent(models.Model):            # default + IS pk
        uuid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                editable=False)
        name = models.CharField(max_length=255)

        class Meta:
            app_label = _APP

    class UUIDPKChild(models.Model):
        name = models.CharField(max_length=255)
        parent = models.ForeignKey(UUIDPKParent, models.CASCADE)

        class Meta:
            app_label = _APP

    class AutoPKParent(models.Model):            # no default + IS pk
        name = models.CharField(max_length=255)

        class Meta:
            app_label = _APP

    class AutoPKChild(models.Model):
        name = models.CharField(max_length=255)
        parent = models.ForeignKey(AutoPKParent, models.CASCADE)

        class Meta:
            app_label = _APP

    class AKParent(models.Model):                # default + alternate key
        uuid = models.UUIDField(unique=True, default=uuid.uuid4,
                                editable=False)
        name = models.CharField(max_length=50)

        class Meta:
            app_label = _APP

    class AKChild(models.Model):
        name = models.CharField(max_length=255)
        parent = models.ForeignKey(AKParent, models.CASCADE, to_field="uuid")

        class Meta:
            app_label = _APP

    class PlainAKParent(models.Model):           # no default + alternate key
        code = models.BigIntegerField(unique=True)
        name = models.CharField(max_length=50)

        class Meta:
            app_label = _APP

    class PlainAKChild(models.Model):
        name = models.CharField(max_length=255)
        parent = models.ForeignKey(PlainAKParent, models.CASCADE,
                                   to_field="code")

        class Meta:
            app_label = _APP

    shapes = [
        # (label, parent, child, extra kwargs to create a SAVED parent row)
        ("pk+default", UUIDPKParent, UUIDPKChild, {"name": "p"}),
        ("pk+nodefault", AutoPKParent, AutoPKChild, {"name": "p"}),
        ("ak+default", AKParent, AKChild, {"name": "p"}),
        ("ak+nodefault", PlainAKParent, PlainAKChild, {"name": "p",
                                                       "code": 1}),
    ]
    from django.db import connection
    with connection.schema_editor() as se:
        for _, parent, child, _kw in shapes:
            se.create_model(parent)
            se.create_model(child)
    return shapes


class Config:
    """One realized point of the boolean input space: a real formset + form
    whose real observables are a specific (adding, has_default, is_primary,
    data_present) combination."""

    __slots__ = ("label", "formset", "form", "field", "attname", "is_uuid")

    def __init__(self, label, formset, form, field, attname, is_uuid):
        self.label = label
        self.formset = formset
        self.form = form
        self.field = field          # the real to_field, resolved by real code
        self.attname = attname
        self.is_uuid = is_uuid

    def observe(self):
        """Re-read the four booleans the patched guard reads, off the real
        objects, right now.  mapping.md §2 says each abstraction is the
        identity on these, so this IS the bridge, not a restatement of it."""
        fs = self.formset
        return (
            fs.instance._state.adding,                                   # adding
            self.field.has_default(),                                     # default
            self.attname == fs.fk.remote_field.model._meta.pk.name,       # is pk
            bool(self.form.data),                                         # data
        )


def _resolve_to_field(formset, form):
    """Read `to_field` back out of the real `InlineForeignKeyField` that the
    real `add_fields` installed, instead of re-implementing the (unchanged)
    resolution at django/forms/models.py:1176-1179.  Keeps our copy of that
    resolution out of the trust chain."""
    from django.forms.models import InlineForeignKeyField

    formset.add_fields(form, 0)
    inline = [f for f in form.fields.values()
              if isinstance(f, InlineForeignKeyField)]
    if len(inline) != 1:
        raise RuntimeError("expected exactly one InlineForeignKeyField, got %d"
                           % len(inline))
    to_field_name = inline[0].to_field
    if to_field_name is not None:
        field = formset.instance._meta.get_field(to_field_name)
    else:
        field = formset.instance._meta.pk
    return field


def _build_configs():
    """All 16 boolean combinations, each realized by real Django objects."""
    from django.db import models
    from django.forms.models import inlineformset_factory

    configs = {}
    for label, parent, child, create_kwargs in _build_models():
        FormSet = inlineformset_factory(parent, child, fields="__all__")
        prefix = FormSet.get_default_prefix()
        data = {
            "%s-TOTAL_FORMS" % prefix: "3",
            "%s-INITIAL_FORMS" % prefix: "0",
            "%s-MAX_NUM_FORMS" % prefix: "",
            "%s-0-name" % prefix: "Test",
            "%s-1-name" % prefix: "",
            "%s-2-name" % prefix: "",
        }
        saved = parent.objects.create(**create_kwargs)
        for want_adding, instance in ((True, None), (False, saved)):
            for want_data in (False, True):
                formset = (FormSet(data, instance=instance) if want_data
                           else FormSet(instance=instance))
                form = formset.forms[0]
                field = _resolve_to_field(formset, form)
                attname = field.attname
                is_uuid = isinstance(field, models.UUIDField)
                cfg = Config("%s/%s/%s" % (label,
                                           "adding" if want_adding else "saved",
                                           "data" if want_data else "nodata"),
                             formset, form, field, attname, is_uuid)
                combo = cfg.observe()
                if combo in configs:
                    raise RuntimeError("duplicate combo %r: %s vs %s"
                                       % (combo, configs[combo].label,
                                          cfg.label))
                configs[combo] = cfg
    return configs


def _verify_bridge(configs):
    """The inverted bridge must realize EVERY one of the 16 combos, and each
    config's real observables must be the combo we filed it under."""
    missing = [c for c in itertools.product((False, True), repeat=4)
               if c not in configs]
    if missing:
        raise RuntimeError("bridge failed to realize combos: %r" % (missing,))
    for combo, cfg in configs.items():
        if cfg.observe() != combo:
            raise RuntimeError("config %s drifted: filed %r observes %r"
                               % (cfg.label, combo, cfg.observe()))


_POISON = "<oracle wrote an unexpected third value>"


def _plant(cfg, k):
    """abstract key `k` (a non-None int) -> the concrete generated default that
    really sits in the attribute."""
    return uuid.UUID(int=k) if cfg.is_uuid else int(k)


def _abstract(post, planted, k):
    """concrete post-state -> the model carrier.  Anything that is neither the
    cleared state nor the value we planted becomes a poison value that can only
    mismatch, so a rewritten key cannot slip through as "preserved"."""
    if post is None:
        return None
    if post == planted:
        return k
    return _POISON


def run_trial(cfg, k):
    """One differential trial: shadow post-state vs REAL patched add_fields.

    Returns None on agreement, else a dict describing the disagreement.
    """
    planted = _plant(cfg, k)
    setattr(cfg.formset.instance, cfg.attname, planted)

    # Read the real observables at the moment of the call (the bridge).
    adding, has_default, is_primary, data_present = cfg.observe()

    # --- shadow: model.py's impl region, verbatim ---
    parent = ParentObject(k)
    shadow_reset_default_related_key(parent, adding, has_default, is_primary,
                                     data_present)

    # --- oracle: the REAL patched repo function ---
    cfg.formset.add_fields(cfg.form, 0)
    post_real = getattr(cfg.formset.instance, cfg.attname)
    post_abs = _abstract(post_real, planted, k)

    # The pure region's deep model must also match what really happened.
    pure = should_clear(adding, has_default, is_primary, data_present)

    if parent.key != post_abs or pure != (post_real is None):
        return {
            "config": cfg.label,
            "attname": cfg.attname,
            "inputs": {"adding": adding, "key_has_default": has_default,
                       "key_is_primary": is_primary,
                       "form_data_present": data_present,
                       "instance.key": k, "planted": repr(planted)},
            "shadow_post": parent.key,
            "oracle_post_real": repr(post_real),
            "oracle_post_abstract": post_abs,
            "should_clear": pure,
            "oracle_cleared": post_real is None,
        }
    return None


# F2P / P2P boundary shapes, as (adding, has_default, is_primary, data_present)
# -> the post-state the real patched code must produce.
_NAMED = [
    # FAIL_TO_PASS: "If form data is provided, a parent's auto-generated
    # alternate key is set."  The branch the gold patch changed.
    ((True, True, False, True), "preserve",
     "F2P test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data"),
    # PASS_TO_PASS companions.
    ((True, True, True, True), "clear",
     "P2P test_inlineformset_factory_ignores_default_pks_on_submit"),
    ((True, True, False, False), "clear",
     "P2P test_inlineformset_factory_nulls_default_pks_alternate_key_relation"),
    ((False, True, True, False), "preserve",
     "P2P existing (persisted) parent keeps its key"),
]


def _assert_patch_branch_live(configs):
    """Positive control: the patch-discriminating branch must be REACHED and
    must behave post-patch.  Pre-patch code clears whenever adding+has_default,
    so if the alternate-key-with-data case clears here, the oracle is not the
    patched function and any "pass" would be vacuous."""
    problems = []
    for combo, expect, why in _NAMED:
        cfg = configs[combo]
        planted = _plant(cfg, 424242)
        setattr(cfg.formset.instance, cfg.attname, planted)
        cfg.formset.add_fields(cfg.form, 0)
        post = getattr(cfg.formset.instance, cfg.attname)
        got = "clear" if post is None else "preserve"
        if got != expect:
            problems.append("%s: combo %r expected %s, real oracle %s (%r)"
                            % (why, combo, expect, got, post))
    return problems


def main():
    _boot_django()
    configs = _build_configs()
    _verify_bridge(configs)

    problems = _assert_patch_branch_live(configs)
    if problems:
        print("G-CONF ERROR: oracle is not the patched function / named "
              "boundary case wrong:")
        for p in problems:
            print("  " + p)
        print(json.dumps({"status": "fail",
                          "reason": "patch-branch positive control failed",
                          "problems": problems}))
        return 1

    combos = sorted(configs)
    checked = 0
    disagreements = []

    # 1. Exhaustive: all 16 boolean combinations (the modeled boolean space is
    #    finite and this enumerates it), each with a distinct planted key.
    for i, combo in enumerate(combos):
        d = run_trial(configs[combo], 1000 + i)
        checked += 1
        if d:
            disagreements.append(d)

    # 2. The named F2P / P2P shapes again, through the full differential.
    for combo, _expect, _why in _NAMED:
        d = run_trial(configs[combo], 777)
        checked += 1
        if d:
            disagreements.append(d)

    # 3. Seeded fuzz over the SAME space to reach >= 1e5 inputs.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        cfg = configs[combos[rng.randrange(16)]]
        d = run_trial(cfg, rng.randrange(1, 1_000_000_000))
        checked += 1
        if d:
            disagreements.append(d)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) between the model's impl region "
              "and the real patched BaseInlineFormSet.add_fields:"
              % len(disagreements))
        for d in disagreements:
            print("  " + json.dumps(d, sort_keys=True))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(disagreements),
                          "first": disagreements[0]}, sort_keys=True))
        return 1

    print("G-CONF OK: model.py impl region (verbatim shadow) vs REAL patched "
          "django.forms.models.BaseInlineFormSet.add_fields on %d inputs "
          "(16/16 boolean combos enumerated exhaustively + %d fuzz, seed=%d); "
          "F2P alternate-key-with-data branch exercised and PRESERVED; "
          "0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "disagreements": 0,
        "oracle": "django.forms.models.BaseInlineFormSet.add_fields "
                  "(real patched function, called)",
        "oracle_provenance": "django/forms/models.py:1173-1181 @ "
                             "f64fd47a7627ed6ffe2df2a32ded6ee528a784eb + gold patch",
        "shadow": "model.py # impl-start/# impl-end region, verbatim, "
                  "contracts stripped",
        "boolean_space": "finite: 16/16 combinations enumerated exhaustively",
        "seed": SEED,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
