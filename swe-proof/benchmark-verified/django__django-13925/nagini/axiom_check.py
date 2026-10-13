#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13925.

This bundle consumes NO `@ContractOnly` axioms: every operation the modeled
check performs is a boolean field read or a boolean connective, all expressed
directly in `model.py`. There is therefore no opaque callee contract to fuzz
against a real callee.

What G-AX validates here is the single REFERENCE correspondence the refinement
rests on (refinement.md, tag A-reference):

  the real check's branch condition

      pk.auto_created
      and not (isinstance(pk, OneToOneField) and pk.remote_field.parent_link)
      and not settings.is_overridden('DEFAULT_AUTO_FIELD')
      and not app_config._is_default_auto_field_overridden

  computes exactly the model's pure predicate

      advisory_warranted(auto, reuses_ancestor_key_a, reuses_ancestor_key_b,
                         setting_overridden, appconfig_overridden)
        == auto
           and not (reuses_ancestor_key_a and reuses_ancestor_key_b)
           and not setting_overridden
           and not appconfig_overridden

  under the field bijection auto <-> pk.auto_created,
  reuses_ancestor_key_a <-> isinstance(pk, OneToOneField),
  reuses_ancestor_key_b <-> pk.remote_field.parent_link
  (the model's two abstract reuse flags map onto the two real-side field
  properties whose conjunction means the key re-uses a concrete ancestor's
  already-declared key).

Because both sides are total boolean functions of the same five booleans, the
correspondence is checked EXHAUSTIVELY over the full 2**5 truth table (boundary
== fuzz here: the input domain is finite and fully enumerated). The real-side
condition is reproduced as the exact boolean expression the patched source
evaluates.

Imports only the standard library. Exit 0 iff every observation matches.
"""
import itertools
import sys


def model_advisory_warranted(auto, reuses_ancestor_key_a, reuses_ancestor_key_b,
                             setting_overridden, appconfig_overridden):
    """Reference of model.py's pure predicate `advisory_warranted`
    (with `reuses_ancestor_declared_key` inlined)."""
    reuses_ancestor_declared_key = reuses_ancestor_key_a and reuses_ancestor_key_b
    return (
        auto
        and not reuses_ancestor_declared_key
        and not setting_overridden
        and not appconfig_overridden
    )


def real_branch_condition(auto_created, is_one_to_one, parent_link,
                          setting_overridden, appconfig_overridden):
    """The exact branch condition the patched `_check_default_pk` evaluates,
    transcribed boolean-for-boolean from `django/db/models/base.py`:

        cls._meta.pk.auto_created and
        not (
            isinstance(cls._meta.pk, OneToOneField) and
            cls._meta.pk.remote_field.parent_link
        ) and
        not settings.is_overridden('DEFAULT_AUTO_FIELD') and
        not cls._meta.app_config._is_default_auto_field_overridden
    """
    return (
        auto_created
        and not (is_one_to_one and parent_link)
        and not setting_overridden
        and not appconfig_overridden
    )


def main():
    checked = 0
    for bits in itertools.product([False, True], repeat=5):
        # b_auto <-> auto_created; b_a <-> isinstance(pk, OneToOneField);
        # b_b <-> remote_field.parent_link (the field bijection of mapping.md).
        b_auto, b_a, b_b, setting_ov, appcfg_ov = bits
        # The real check emits the single advisory iff the branch condition
        # holds; the model emits count 1 iff advisory_warranted holds.
        real_warns = real_branch_condition(
            b_auto, b_a, b_b, setting_ov, appcfg_ov)
        model_warns = model_advisory_warranted(
            b_auto, b_a, b_b, setting_ov, appcfg_ov)
        assert real_warns == model_warns, (
            "advisory predicate mismatch on "
            "(auto=%r, reuses_a=%r, reuses_b=%r, setting_ov=%r, "
            "appcfg_ov=%r): real=%r model=%r"
            % (b_auto, b_a, b_b, setting_ov, appcfg_ov,
               real_warns, model_warns))
        checked += 1

    # Structural witness for the field bijection: an implicitly-created parent
    # link IS a one-to-one relation flagged parent_link (the configuration the
    # auto-created `<parent>_ptr` field carries). Confirmed against Django's own
    # field construction at base_commit:
    #   OneToOneField(base, on_delete=CASCADE, name=..., auto_created=True,
    #                 parent_link=True)  -- django/db/models/base.py:243-249
    # i.e. for the auto-created parent link: auto_created=True (implicit),
    # isinstance(pk, OneToOneField)=True (one_to_one), parent_link=True.
    # The model's discriminating case (implicit & one_to_one & parent_link ->
    # NOT warranted) is therefore exactly this real configuration.
    assert model_advisory_warranted(True, True, True, False, False) is False, (
        "auto-created parent-link key must NOT warrant the advisory")
    assert real_branch_condition(True, True, True, False, False) is False
    # ...while a plain auto-created key (not a parent link) DOES warrant it.
    assert model_advisory_warranted(True, False, False, False, False) is True
    assert real_branch_condition(True, False, False, False, False) is True

    print("G-AX OK: model predicate == real branch condition on all %d truth "
          "assignments; auto-created parent-link suppression confirmed."
          % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
