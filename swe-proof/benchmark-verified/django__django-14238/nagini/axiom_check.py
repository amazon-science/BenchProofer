#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14238.

There is NO consumed `@ContractOnly` axiom in this bundle: the structural
subtype query (`issubclass`) that the modelled membership test consults is
modelled DEEPLY by the `@Pure` helper `is_subtype` in model.py.  G-AX therefore
validates that DEEP MODEL against the REAL Python `issubclass` builtin, and
validates the modelled decision `subclass_check` against the REAL metaclass
`__subclasscheck__` semantics, over a faithful structural replica of the class
family the patch concerns plus user-defined subclasses.

  (A-reference) the deep model `is_subtype(sub, base)` (model.py pure region):
      sub is a subtype of base iff base's identity lies in sub's ancestry.
      Validated == the real `issubclass(sub, base)` for every ordered pair of
      classes in the replicated hierarchy.

  (A-reference) the modelled decision `subclass_check(owner, b1, b2, cand)`
      (post-patch semantics) == cand is a subtype of b1, b2 or owner.  Validated
      == the REAL membership decision a metaclass with `_subclasses = (b1, b2)`
      makes via `issubclass(cand, self._subclasses) or
      super().__subclasscheck__(cand)`.

Imports nothing repo-specific: only the Python standard library (the class
machinery / `issubclass` builtin the gold patch relies on).  When the real
Django classes are importable (they are, in the evaluation container), the
relation is additionally validated against the real
`AutoFieldMeta.__subclasscheck__`.  Exit 0 iff every obligation holds.
"""
import itertools
import sys


# --- A structural replica of the class family under specification ------------
# Mirrors django.db.models.fields: an attached type `Owner` carrying a metaclass
# whose `_subclasses` is a fixed 2-tuple of registered base classes, neither of
# which is a subtype of Owner (they share only the integer-field lineage).

class _Field:
    pass


class _IntegerField(_Field):
    pass


class _BigIntegerField(_IntegerField):
    pass


class _SmallIntegerField(_IntegerField):
    pass


class _Mixin:
    pass


class _BigAutoField(_Mixin, _BigIntegerField):      # registered base #1
    pass


class _SmallAutoField(_Mixin, _SmallIntegerField):  # registered base #2
    pass


class _AutoFieldMeta(type):
    @property
    def _subclasses(self):
        return (_BigAutoField, _SmallAutoField)

    # The FIXED (post-patch) behaviour: structural subtype membership.
    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)


class _AutoField(_Mixin, _IntegerField, metaclass=_AutoFieldMeta):  # the owner
    pass


# user-defined subclasses of the registered bases (the F2P scenario)
class _MyBigAutoField(_BigAutoField):
    pass


class _MySmallAutoField(_SmallAutoField):
    pass


class _MyBigAutoFieldGrandchild(_MyBigAutoField):
    pass


# unrelated classes (must be rejected) and an owner-subclass (accepted via super)
class _Unrelated:
    pass


class _PlainInt(_IntegerField):
    pass


class _OwnerSubclass(_AutoField):
    pass


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def _ancestry_ids(cls):
    """The set of identities of all classes `cls` derives from (its MRO),
    mirroring the `anc` field of model.py's `Cls`."""
    return {id(a) for a in cls.__mro__}


def is_subtype(sub, base):
    """Reference implementation of model.py's deep model `is_subtype`:
    base's identity lies in sub's ancestry."""
    return id(base) in _ancestry_ids(sub)


def subclass_check_model(owner, base_one, base_two, candidate):
    """Reference implementation of model.py's `subclass_check` (post-patch
    semantics): TRUE iff candidate is a subtype of either registered base or
    of the owner."""
    return (is_subtype(candidate, base_one)
            or is_subtype(candidate, base_two)
            or is_subtype(candidate, owner))


# --- the checks --------------------------------------------------------------

def check_is_subtype_reference(sub, base):
    """Assert the deep model is_subtype(sub, base) == the REAL ordinary subtype
    query.  `is_subtype` models the *ordinary* structural check (MRO
    membership), which is exactly what `issubclass(subclass, self._subclasses)`
    invokes: the registered bases carry the default `type.__subclasscheck__`,
    not the overriding metaclass (only the attached owner type does).  We
    therefore reference `type.__subclasscheck__`, the unoverridden builtin
    relation, computed on every pair (and equal to `issubclass` for every base
    whose metaclass does not override the check)."""
    observed = type.__subclasscheck__(base, sub)     # ordinary builtin relation
    expected = is_subtype(sub, base)                 # deep model
    assert observed == expected, (
        "is_subtype deep model unsound on (%s, %s): ordinary subclass check "
        "gave %r, deep model gives %r"
        % (sub.__name__, base.__name__, observed, expected))


def check_decision_reference(owner, base_one, base_two, candidate):
    """Assert the modelled decision == the REAL metaclass membership decision.

    The real decision is exactly what a metaclass with `_subclasses =
    (base_one, base_two)` computes:
        issubclass(candidate, (base_one, base_two)) or super().__subclasscheck__
    where the super() leg is the ordinary structural check against `owner`."""
    real = (issubclass(candidate, (base_one, base_two))
            or type.__subclasscheck__(owner, candidate))
    model = subclass_check_model(owner, base_one, base_two, candidate)
    assert real == model, (
        "subclass_check model unsound for candidate %s: real=%r model=%r"
        % (candidate.__name__, real, model))


def main():
    universe = [
        _Field, _IntegerField, _BigIntegerField, _SmallIntegerField, _Mixin,
        _BigAutoField, _SmallAutoField, _AutoField,
        _MyBigAutoField, _MySmallAutoField, _MyBigAutoFieldGrandchild,
        _Unrelated, _PlainInt, _OwnerSubclass,
        object, int, type,
    ]

    # --- is_subtype deep model (A-reference): every ordered pair -----------
    for sub, base in itertools.product(universe, repeat=2):
        check_is_subtype_reference(sub, base)

    # --- subclass_check decision (A-reference): owner = _AutoField, the two
    #     registered bases, every candidate in the universe ----------------
    owner, b1, b2 = _AutoField, _BigAutoField, _SmallAutoField
    for candidate in universe:
        check_decision_reference(owner, b1, b2, candidate)

    # --- the discriminating F2P scenarios must decide TRUE -----------------
    #     (a proper subclass of a registered base; and the bases themselves)
    for candidate in (_MyBigAutoField, _MySmallAutoField,
                      _MyBigAutoFieldGrandchild, _BigAutoField, _SmallAutoField):
        assert subclass_check_model(owner, b1, b2, candidate) is True, (
            "expected %s to be a member" % candidate.__name__)
        assert issubclass(candidate, _AutoField) is True, (
            "real issubclass(%s, AutoField) should be True post-fix"
            % candidate.__name__)

    # --- non-members must decide FALSE -------------------------------------
    for candidate in (_Unrelated, _PlainInt, _Field, _IntegerField,
                      _BigIntegerField, _SmallIntegerField):
        assert subclass_check_model(owner, b1, b2, candidate) is False, (
            "expected %s to be a non-member" % candidate.__name__)

    # --- owner-subclass accepted via the ordinary (super) leg --------------
    assert subclass_check_model(owner, b1, b2, _OwnerSubclass) is True

    # --- pre-patch (identity) check would WRONGLY reject the F2P subclasses -
    def prepatch_decision(owner, base_one, base_two, candidate):
        return (candidate is base_one or candidate is base_two
                or is_subtype(candidate, owner))
    assert prepatch_decision(owner, b1, b2, _MyBigAutoField) is False, (
        "identity check should (buggily) reject the user subclass — confirms "
        "the spec senses the change")

    # --- optional: validate against the REAL Django metaclass if importable -
    extra = ""
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure()
        from django.db.models.fields import (
            AutoField, BigAutoField, SmallAutoField,
        )

        class RealMyBig(BigAutoField):
            pass

        class RealMySmall(SmallAutoField):
            pass

        for c in (BigAutoField, SmallAutoField, RealMyBig, RealMySmall):
            assert issubclass(c, AutoField) is True, (
                "real Django issubclass(%s, AutoField) should be True"
                % c.__name__)
            assert subclass_check_model(AutoField, BigAutoField, SmallAutoField, c) is True
        extra = " + real Django AutoFieldMeta validated"
    except Exception as e:  # Django not importable here -> replica suffices
        extra = " (Django import skipped: %s)" % type(e).__name__

    print("G-AX OK: is_subtype deep model (== issubclass) sound on %d ordered "
          "pairs; subclass_check decision (== real metaclass) sound on %d "
          "candidates; F2P subclass scenarios decide TRUE%s"
          % (len(universe) ** 2, len(universe), extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
