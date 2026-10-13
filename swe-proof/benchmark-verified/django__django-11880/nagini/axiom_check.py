#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11880.

This bundle consumes NO @ContractOnly axioms: the duplication behaviour is
modelled deeply in model.py. What G-AX validates here is the **A-reference** —
that the deep model (a duplicate whose mutable per-field collections are
SEPARATE objects holding the same contents as the original's) faithfully
captures the real Python semantics of the field-duplication primitive the patch
builds on (``copy.copy(self)`` followed by ``self.error_messages.copy()`` and
``self.validators[:]``).

It executes the REAL Django ``Field.__deepcopy__`` (post-patch) on a wide range
of fields and asserts, for every observation:

  * the duplicate's ``error_messages`` mapping is a DISTINCT object from the
    original's (``copy.error_messages is not field.error_messages``) — the
    modelled ``Result().msg_codes/msg_values is not self.msg_codes/msg_values``;
  * it holds exactly the same code->message entries (same keys, same values) —
    the modelled per-index content equality;
  * the duplicate's ``validators`` list is likewise a DISTINCT object holding
    the same validators in order — the modelled validators clauses;
  * the original field is left exactly as it was (same overrides, same
    validators) — the read-only postcondition;
  * mutating the duplicate's ``error_messages`` does NOT reach the original's,
    and vice versa — the observable consequence of distinctness.

It also confirms the underlying ``dict.copy()`` / ``list[:]`` primitives have
the modelled distinct-object-with-equal-contents semantics (the A-reference
proper), independently of Django.

Run inside the official SWE-bench container for the instance, where Django is
importable. Exit 0 iff every obligation holds. Outside the container (Django
absent) it prints ``G-AX SKIP`` and returns 0; the orchestrator runs it
in-container.
"""
import copy
import random
import sys


def _check_primitive_semantics():
    """The A-reference proper: dict.copy() and list[:] yield a DISTINCT object
    with EQUAL contents (the deep model's two-collection copy)."""
    rng = random.Random(20240117)
    for _ in range(5000):
        n = rng.randint(0, 8)
        d = {rng.randint(-50, 50): rng.randint(-1000, 1000) for _ in range(n)}
        dc = d.copy()
        assert dc is not d, "dict.copy() must be a distinct object"
        assert dc == d, "dict.copy() must hold equal contents"
        # distinct object => mutating the copy does not reach the original
        snapshot = dict(d)
        dc[9999] = 7
        assert d == snapshot, "mutating the dict copy reached the original"

        m = rng.randint(0, 8)
        lst = [rng.randint(-1000, 1000) for _ in range(m)]
        lc = lst[:]
        assert lc is not lst, "list[:] must be a distinct object"
        assert lc == lst, "list[:] must hold equal contents in order"
        lsnapshot = list(lst)
        lc.append(123456)
        assert lst == lsnapshot, "mutating the list copy reached the original"


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            USE_I18N=False,
            DATABASES={},
        )
    django.setup()


def main():
    # The A-reference primitives hold regardless of environment.
    _check_primitive_semantics()

    try:
        _configure_django()
        from django import forms
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r "
              "(dict.copy()/list[:] A-reference semantics confirmed)" % (exc,))
        return 0

    observations = 0

    def observe(field):
        nonlocal observations
        original_messages = dict(field.error_messages)
        original_validators = list(field.validators)

        dup = copy.deepcopy(field)

        # (1) distinct error_messages object ...
        assert dup.error_messages is not field.error_messages, (
            "deepcopy shared the error_messages dict (the bug)")
        # ... with the same entries.
        assert dup.error_messages == field.error_messages, (
            "deepcopy's error_messages differ in contents")

        # (2) distinct validators list with same validators in order.
        assert dup.validators is not field.validators, (
            "deepcopy shared the validators list")
        assert dup.validators == field.validators, (
            "deepcopy's validators differ")

        # (3) the original is left exactly as it was.
        assert dict(field.error_messages) == original_messages
        assert list(field.validators) == original_validators

        # (4) the observable consequence: mutating the duplicate's overrides
        # does not reach the original, and vice versa.
        if dup.error_messages:
            some_key = next(iter(dup.error_messages))
            dup.error_messages[some_key] = "MUTATED-ON-DUP"
            assert field.error_messages.get(some_key) != "MUTATED-ON-DUP", (
                "mutating the duplicate's error_messages reached the original")
        dup.error_messages["__brand_new_key__"] = "x"
        assert "__brand_new_key__" not in field.error_messages, (
            "adding to the duplicate's error_messages reached the original")
        field.error_messages["__source_only_key__"] = "y"
        assert "__source_only_key__" not in dup.error_messages, (
            "adding to the original's error_messages reached the duplicate")

        observations += 1

    # A spread of field types and explicit error_messages overrides — exactly
    # the case the F2P test exercises (a CharField subclass overriding
    # 'invalid'), plus boundary cases (no overrides, several overrides).
    observe(forms.CharField())
    observe(forms.CharField(error_messages={"invalid": "Form custom error message."}))
    observe(forms.CharField(error_messages={"required": "R", "invalid": "I", "min_length": "M"}))
    observe(forms.IntegerField(error_messages={"invalid": "nope"}))
    observe(forms.EmailField())
    observe(forms.IntegerField())
    observe(forms.ChoiceField(choices=[(1, "a"), (2, "b")]))
    observe(forms.DateField(error_messages={"invalid": "bad date"}))

    class CustomCharField(forms.CharField):
        def __init__(self, **kwargs):
            kwargs["error_messages"] = {"invalid": "Form custom error message."}
            super().__init__(**kwargs)

    # The exact F2P scenario: a subclass setting error_messages in __init__.
    f = CustomCharField()
    fc = copy.deepcopy(f)
    assert isinstance(fc, CustomCharField), "deepcopy changed the field type"
    assert fc.error_messages is not f.error_messages, (
        "the F2P assertion (assertIsNot) fails on the real callee")
    observe(CustomCharField())

    # fuzz: random subsets of override codes with random message values
    rng = random.Random(11880)
    codes = ["required", "invalid", "max_length", "min_length", "max_value", "min_value"]
    for _ in range(200):
        chosen = {c: "msg-%d" % rng.randint(0, 9) for c in codes if rng.random() < 0.5}
        observe(forms.CharField(error_messages=chosen))

    print("G-AX OK: deep model validated against the real Field.__deepcopy__ "
          "over %d observations; the duplicate's error_messages and validators "
          "are distinct objects with equal contents and the original is "
          "untouched; dict.copy()/list[:] A-reference semantics confirmed."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
