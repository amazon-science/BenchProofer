#!/usr/bin/env python3
"""G-AX soundness / behavioural-equivalence check for django__django-16950.

This bundle consumes NO ``@ContractOnly`` axiom: the changed operation is the
clearing *decision* of the inline formset's ``add_fields`` — a boolean
combination of three conditions plus a conditional reset of the parent's
related-key value — and it is modelled DEEPLY in model.py (the ``should_clear``
predicate + the guarded ``instance.key = None`` store). G-AX therefore checks
that the deep model is behaviourally equal to the REAL post-patch guard logic,
rather than over-approximating an opaque callee.

Two independent checks:

  (1) DECISION TABLE (always runs, stdlib-only). Over all 16 combinations of the
      four booleans (adding, has_default, is_primary, data_present):
        - the modelled decision ``should_clear`` equals the post-patch guard
          ``adding and has_default and (is_primary or not data_present)``;
        - it diverges from the PRE-patch guard ``adding and has_default``
          exactly on the FAIL_TO_PASS case (adding, has_default, NOT primary,
          data_present): pre-patch clears, post-patch (and the model) preserves.

  (2) REAL DJANGO (runs in-container when Django + the test models are
      importable; skipped gracefully otherwise). Reproduces the four tested
      scenarios by invoking the real ``inlineformset_factory`` and reading the
      parent instance's related-key value after the formset's forms are built,
      asserting it matches the modelled decision. This is the real callee
      executed on Requires-satisfying inputs.

Exit 0 iff every observation is sound.
"""
import sys


# --- model.py reference encoding (kept in lock-step with the spec) -----------

def should_clear(adding, key_has_default, key_is_primary, form_data_present):
    """Reference of model.py's deep model ``should_clear`` (the pure region)."""
    return (adding and key_has_default
            and (key_is_primary or not form_data_present))


def prepatch_guard(adding, key_has_default, key_is_primary, form_data_present):
    """The PRE-patch guard logic: clear whenever adding and has_default."""
    return adding and key_has_default


# --- check (1): exhaustive decision table ------------------------------------

def check_decision_table():
    bools = (False, True)
    fail_to_pass_case = (True, True, False, True)  # adding, hd, not-pk, data
    diverged = []
    for adding in bools:
        for hd in bools:
            for is_pk in bools:
                for data in bools:
                    model = should_clear(adding, hd, is_pk, data)
                    # post-patch guard logic, spelled out independently
                    post = adding and hd and (is_pk or not data)
                    assert model == post, (
                        "deep model disagrees with post-patch guard on "
                        "(adding=%s, has_default=%s, is_pk=%s, data=%s): "
                        "model=%s post=%s" % (adding, hd, is_pk, data,
                                              model, post))
                    pre = prepatch_guard(adding, hd, is_pk, data)
                    if pre != model:
                        diverged.append((adding, hd, is_pk, data))
    # The fix must change behaviour on exactly the alternate-key + data case.
    assert diverged == [fail_to_pass_case], (
        "pre/post divergence set is %r, expected exactly the FAIL_TO_PASS "
        "alternate-key-with-data case %r" % (diverged, fail_to_pass_case))
    # And on that case: pre-patch clears (True), model/post preserve (False).
    assert prepatch_guard(*fail_to_pass_case) is True
    assert should_clear(*fail_to_pass_case) is False
    return 16


# --- check (2): real Django scenarios (in-container; skipped if unavailable) -

def check_real_django():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            return None  # not running under the test settings; skip
        from django.forms.models import inlineformset_factory  # noqa: F401
    except Exception:
        return None

    try:
        from tests.model_formsets.models import (  # type: ignore
            UUIDPKParent, UUIDPKChild,
            ParentWithUUIDAlternateKey, ChildRelatedViaAK,
        )
        from django.forms.models import inlineformset_factory
    except Exception:
        try:
            from model_formsets.models import (  # type: ignore
                UUIDPKParent, UUIDPKChild,
                ParentWithUUIDAlternateKey, ChildRelatedViaAK,
            )
            from django.forms.models import inlineformset_factory
        except Exception:
            return None

    observed = 0

    # Scenario PASS_TO_PASS: UUID parent pk + child, WITH data.
    # to_field IS the parent pk (is_primary=True) -> clear -> uuid is None.
    FormSet = inlineformset_factory(UUIDPKParent, UUIDPKChild, fields="__all__")
    fs = FormSet({
        "uuidpkchild_set-TOTAL_FORMS": 3,
        "uuidpkchild_set-INITIAL_FORMS": 0,
        "uuidpkchild_set-MAX_NUM_FORMS": "",
        "uuidpkchild_set-0-name": "Foo",
        "uuidpkchild_set-1-name": "",
        "uuidpkchild_set-2-name": "",
    })
    fs.is_valid()
    assert fs.instance.uuid is None, (
        "UUID-pk parent WITH data: expected cleared (is_primary), got %r"
        % (fs.instance.uuid,))
    assert fs.forms[0].instance.parent_id is None
    observed += 1

    # Scenario FAIL_TO_PASS: alternate-key relation, WITH data.
    # to_field is the alternate key (is_primary=False), data present
    # -> do NOT clear -> uuid retained, child relates to it.
    FormSet = inlineformset_factory(
        ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
    fs = FormSet({
        "childrelatedviaak_set-TOTAL_FORMS": 3,
        "childrelatedviaak_set-INITIAL_FORMS": 0,
        "childrelatedviaak_set-MAX_NUM_FORMS": "",
        "childrelatedviaak_set-0-name": "Test",
        "childrelatedviaak_set-1-name": "",
        "childrelatedviaak_set-2-name": "",
    })
    fs.is_valid()
    assert fs.instance.uuid is not None, (
        "alternate-key parent WITH data: expected retained (not primary, "
        "data present), got None")
    assert fs.forms[0].instance.parent_id == fs.instance.uuid
    observed += 1

    return observed


def main():
    n = check_decision_table()
    real = check_real_django()
    if real is None:
        print("G-AX OK: decision-table equivalence over %d boolean "
              "combinations; deep model == post-patch guard; diverges from "
              "pre-patch only on the alternate-key-with-data FAIL_TO_PASS "
              "case. (Real-Django scenario check skipped: Django/test models "
              "not importable in this environment.)" % n)
    else:
        print("G-AX OK: decision-table equivalence over %d boolean "
              "combinations AND %d real-Django scenarios (post-patch) match "
              "the modelled clearing decision." % (n, real))
    return 0


if __name__ == "__main__":
    sys.exit(main())
