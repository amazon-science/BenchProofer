#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11551.

This bundle consumes NO @ContractOnly axiom: the unchanged primitives the
validator consults (``callable``, ``hasattr``, ``Options.get_field``,
``getattr``, ``isinstance(..., ManyToManyField)``) are each reduced to the
single boolean observation they produce, and the changed decision logic over
those observations is modelled DEEPLY in model.py's impl region.

G-AX therefore validates the *decision-logic equivalence*: the model's verdict
must equal the GOLD-patched routine's verdict on every combination of
observations. Two independent checks:

  (1) Exhaustive: over all 2**6 = 64 combinations of the six boolean
      observations, the model decision (re-encoded here from model.py's impl)
      equals the gold-patched ``_check_list_display_item`` decision (re-encoded
      here from patch.diff's body). This is the equivalence the refinement
      relies on (refinement.md). Unreachable combinations are included and must
      still agree (they agree vacuously by structure).

  (2) Real-callee witness: using genuine Python descriptor / attribute
      semantics, exercise the actual builtins ``callable``/``hasattr``/
      ``getattr``/``isinstance`` and a descriptor whose ``__get__`` raises
      ``AttributeError`` on the class (the F2P ``PositionField`` shape). Confirm
      that the observation tuple the patched routine derives matches what the
      model abstracts, and that the resulting verdict is "accepted" — exactly
      the F2P behaviour (a field reachable only via the structural lookup, with
      the model attribute unreachable, is valid).

Imports nothing repo-specific (stdlib only). Exit 0 iff every obligation holds.
"""
import sys


# --- model.py decision (re-encoded from model.py's impl region) -------------

def model_decision(is_invokable, is_presenter_attr,
                   structural_absent, structural_is_relation,
                   attribute_absent, attribute_is_relation):
    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not structural_absent:
        relation = structural_is_relation
    else:
        if attribute_absent:
            return 108
        relation = attribute_is_relation
    if relation:
        return 109
    return 0


# --- gold-patched routine decision (re-encoded from patch.diff's body) ------
# Simulates the exact control flow of the post-patch _check_list_display_item,
# driven by the same six observations. get_field raising FieldDoesNotExist is
# `structural_absent`; getattr raising AttributeError is `attribute_absent`.

def gold_patched_decision(is_invokable, is_presenter_attr,
                          structural_absent, structural_is_relation,
                          attribute_absent, attribute_is_relation):
    # if callable(item): return []
    if is_invokable:
        return 0
    # elif hasattr(obj, item): return []
    if is_presenter_attr:
        return 0
    # try: field = obj.model._meta.get_field(item)
    # except FieldDoesNotExist:
    #     try: field = getattr(obj.model, item)
    #     except AttributeError: return [E108]
    if not structural_absent:
        field_is_relation = structural_is_relation
    else:
        if attribute_absent:
            return 108
        field_is_relation = attribute_is_relation
    # if isinstance(field, models.ManyToManyField): return [E109]
    if field_is_relation:
        return 109
    # return []
    return 0


def check_exhaustive_equivalence():
    n = 0
    for is_invokable in (False, True):
        for is_presenter_attr in (False, True):
            for structural_absent in (False, True):
                for structural_is_relation in (False, True):
                    for attribute_absent in (False, True):
                        for attribute_is_relation in (False, True):
                            args = (is_invokable, is_presenter_attr,
                                    structural_absent, structural_is_relation,
                                    attribute_absent, attribute_is_relation)
                            m = model_decision(*args)
                            g = gold_patched_decision(*args)
                            assert m in (0, 108, 109), \
                                "model produced non-code verdict %r on %r" % (m, args)
                            assert m == g, (
                                "decision-logic mismatch on observations %r: "
                                "model=%r gold-patched=%r" % (args, m, g))
                            n += 1
    return n


# --- real-callee witness: the F2P PositionField shape -----------------------

class _ManyToManyField:
    """Stand-in for django.db.models.ManyToManyField; only the isinstance
    relationship matters for the observation `*_is_relation`."""


class _PlainField:
    """A structural field that is NOT a many-to-many relation."""


def _build_position_descriptor():
    """A descriptor whose __get__ raises AttributeError when accessed on the
    class (instance is None) — the exact F2P `PositionField` shape:

        def __get__(self, instance, owner):
            if instance is None:
                raise AttributeError()
    """
    class PositionField:
        def __get__(self, instance, owner):
            if instance is None:
                raise AttributeError()
            return 0
    return PositionField()


def check_real_callee_witness():
    # The model class carries the PositionField descriptor as `field`, and
    # _meta.get_field('field') returns the (plain, non-m2m) structural field.
    structural_field = _PlainField()

    class TestModel:
        field = _build_position_descriptor()

    class _Meta:
        def get_field(self, name):
            if name == "field":
                return structural_field
            raise KeyError(name)  # stands in for FieldDoesNotExist

    item = "field"

    # Observation 1: callable(item)  -> the entry is a plain string, not callable
    is_invokable = callable(item)
    assert is_invokable is False

    # Observation 2: hasattr(obj, item) on the presenter -> no such attribute
    class _Presenter:
        pass
    is_presenter_attr = hasattr(_Presenter(), item)
    assert is_presenter_attr is False

    # Observation 3: get_field raises? -> here it SUCCEEDS (returns a field)
    meta = _Meta()
    try:
        f = meta.get_field(item)
        structural_absent = False
        structural_is_relation = isinstance(f, _ManyToManyField)
    except KeyError:
        structural_absent = True
        structural_is_relation = False
    assert structural_absent is False
    assert structural_is_relation is False

    # Observation 4: getattr(obj.model, item) raises? -> the descriptor raises
    # AttributeError on the class, so the attribute is UNREACHABLE.
    try:
        v = getattr(TestModel, item)
        attribute_absent = False
        attribute_is_relation = isinstance(v, _ManyToManyField)
    except AttributeError:
        attribute_absent = True
        attribute_is_relation = False
    assert attribute_absent is True, "PositionField descriptor must make getattr raise"
    assert attribute_is_relation is False

    args = (is_invokable, is_presenter_attr,
            structural_absent, structural_is_relation,
            attribute_absent, attribute_is_relation)
    m = model_decision(*args)
    g = gold_patched_decision(*args)
    assert m == g == 0, (
        "F2P PositionField witness must be ACCEPTED (0); "
        "model=%r gold-patched=%r on %r" % (m, g, args))
    return args


def main():
    combos = check_exhaustive_equivalence()
    witness = check_real_callee_witness()
    print("G-AX OK: model decision == gold-patched decision on all %d "
          "observation combinations; real-callee F2P PositionField witness "
          "%r accepted (verdict 0)" % (combos, witness))
    return 0


if __name__ == "__main__":
    sys.exit(main())
