#!/usr/bin/env python3
"""G-AX soundness check for scikit-learn__scikit-learn-12585.

The proof consumes NO @ContractOnly axiom. It instead models the changed
dispatch predicate DEEPLY and relies on two A-reference facts about real
Python that `model.py` encodes; this script validates both against the real
runtime, the way G-AX would, using only the standard library.

A-reference fact 1 (the leaf dispatch predicate — refinement.md A4):
    is_leaf(obj)  ==  (not hasattr(obj, 'get_params')) or isinstance(obj, type)
  i.e. the model's `is_leaf(c) == (not c.has_introspect) or c.is_class_object`
  abstracts EXACTLY the gold guard
  `not hasattr(estimator,'get_params') or isinstance(estimator, type)`.
  In particular a class object that DEFINES get_params still satisfies
  `hasattr(cls,'get_params') == True` (so the old guard alone misclassified it
  as a non-leaf) yet `isinstance(cls, type) == True` makes the new guard
  correctly classify it as a leaf.

A-reference fact 2 (per-disjunct fidelity of the fallback copy — refinement.md
  A6 / mapping.md §3.2). The leaf branch is `return copy.deepcopy(estimator)`;
  the model is faithful over BOTH disjuncts of the leaf predicate:
    * class-object leaf:  copy.deepcopy(cls) is cls
      (classes are atomic to copy.deepcopy, so the `safe=False` fallback returns
      a class parameter reference-identical — exactly the F2P identity
      assertion; the identity postcondition is scoped to this disjunct).
    * non-class state-bearing leaf:  copy.deepcopy(obj) is NOT obj
      (arrays / sparse / plain objects are deep-copied to a distinct object, so
      the spec must NOT demand identity for them — modeled as allocating a fresh
      object and asserting no identity). This per-disjunct check is the fix for
      the prior TOO-STRONG defect (identity asserted for ALL leaves rejected a
      gold-faithful impl).

Exit 0 iff every observation matches the model. stdlib-only imports.
"""
import copy
import sys


# --- A small zoo of real objects covering the dispatch cases ----------------

class EstimatorLike(object):
    """An estimator-like class: defines get_params as a (bound) method, exactly
    as a scikit-learn estimator does. Mirrors `MyEstimator`/`StandardScaler`."""
    def __init__(self, **params):
        self._params = params

    def get_params(self, deep=False):
        return dict(self._params)


class PlainObject(object):
    """A non-estimator: no get_params attribute."""
    pass


def model_is_leaf(has_introspect, is_class_object):
    """The model's is_leaf predicate, transcribed (model.py pure region)."""
    return (not has_introspect) or is_class_object


def real_guard(obj):
    """The gold patch's leaf guard, verbatim (sklearn/base.py:51 post-patch)."""
    return (not hasattr(obj, 'get_params')) or isinstance(obj, type)


def real_old_guard(obj):
    """The pre-patch leaf guard (sklearn/base.py:51 pre-patch)."""
    return not hasattr(obj, 'get_params')


def main():
    failures = []

    # The classification cases the model abstracts. Each entry:
    #   (label, object, expected is_class_object, expected has_introspect)
    instance = EstimatorLike(l1=0, empty=None)
    nested_instance = EstimatorLike(empty=EstimatorLike)  # the F2P shape
    plain = PlainObject()

    cases = [
        # genuine instances: have get_params, not a class -> NOT a leaf
        ("estimator instance", instance, False, True),
        ("nested estimator instance", nested_instance, False, True),
        # class objects: define get_params (so hasattr is True) AND are types
        # -> MUST be a leaf (this is the discriminating case)
        ("estimator CLASS object", EstimatorLike, True, True),
        ("builtin class object int", int, True, hasattr(int, 'get_params')),
        ("builtin class object str", str, True, hasattr(str, 'get_params')),
        ("plain object class", PlainObject, True, hasattr(PlainObject,
                                                          'get_params')),
        # non-estimators: no get_params, not a class -> leaf
        ("plain non-estimator", plain, False, False),
        ("integer value", 7, False, False),
        ("string value", "hello", False, False),
        ("none value", None, False, False),
    ]

    saw_discriminating_class = False
    for label, obj, exp_is_cls, exp_has in cases:
        has_introspect = hasattr(obj, 'get_params')
        is_class_object = isinstance(obj, type)

        # The model's field interpretation matches the real predicates.
        if is_class_object != exp_is_cls:
            failures.append(
                "%s: isinstance(obj,type)=%r expected %r"
                % (label, is_class_object, exp_is_cls))
        if has_introspect != exp_has:
            failures.append(
                "%s: hasattr(obj,'get_params')=%r expected %r"
                % (label, has_introspect, exp_has))

        # A-reference fact 1: model is_leaf == real (post-patch) guard.
        m = model_is_leaf(has_introspect, is_class_object)
        r = real_guard(obj)
        if m != r:
            failures.append(
                "%s: model is_leaf=%r != real guard=%r" % (label, m, r))

        # The discriminating case: a class object that DEFINES get_params is a
        # leaf under the NEW guard but was NOT a leaf under the OLD guard.
        if is_class_object and has_introspect:
            saw_discriminating_class = True
            if not real_guard(obj):
                failures.append(
                    "%s: new guard should classify class as leaf" % label)
            if real_old_guard(obj):
                failures.append(
                    "%s: old guard wrongly classified class as leaf" % label)

    if not saw_discriminating_class:
        failures.append("no discriminating class-with-get_params case exercised")

    # A-reference fact 2a: copy.deepcopy(cls) is cls for class objects (the
    # safe=False fallback returns a class reference-identical). This is the ONLY
    # disjunct the identity postcondition (scoped to is_class_object) covers.
    for cls in (EstimatorLike, PlainObject, int, str, list, dict, type):
        if copy.deepcopy(cls) is not cls:
            failures.append(
                "copy.deepcopy(%r) is not %r (expected reference-identity)"
                % (cls, cls))

    # A-reference fact 2b: copy.deepcopy(obj) is NOT obj for a non-class
    # state-bearing leaf (the OTHER is_leaf disjunct: not hasattr(...,
    # 'get_params') and not isinstance(..., type)). These leaves deep-copy to a
    # DISTINCT object, so the spec must NOT assert identity for them. This is the
    # per-disjunct fidelity check that fixes the prior TOO-STRONG defect.
    non_class_leaves = [
        ("plain non-estimator instance", PlainObject()),
        ("list value", [1, 2, 3]),
        ("dict value", {"a": 1}),
        ("bytearray value", bytearray(b"xyz")),
    ]
    for label, obj in non_class_leaves:
        # confirm it is genuinely a non-class leaf under the real guard
        if isinstance(obj, type):
            failures.append("%s: unexpectedly a class object" % label)
        if not real_guard(obj):
            failures.append("%s: real guard should classify as a leaf" % label)
        if copy.deepcopy(obj) is obj:
            failures.append(
                "%s: copy.deepcopy returned the SAME object; a non-class leaf "
                "must deep-copy to a DISTINCT object (spec must not assert "
                "identity here)" % label)

    # End-to-end identity check mirroring the F2P assertion, on the real
    # dispatch logic (post-patch guard + deepcopy fallback) for the leaf path.
    def reproduce_leaf(obj, safe):
        # the gold leaf branch: leaf and not safe -> deepcopy (atomic for a
        # class -> identity); leaf and safe -> would raise.
        assert real_guard(obj)
        if not safe:
            return copy.deepcopy(obj)
        raise TypeError("not cloneable")

    cloned_class = reproduce_leaf(EstimatorLike, safe=False)
    if cloned_class is not EstimatorLike:
        failures.append("F2P-shape: clone of a class param lost identity")

    if failures:
        for f in failures:
            sys.stderr.write("UNSOUND: " + f + "\n")
        sys.exit(1)

    print("G-AX SOUND: model is_leaf == real dispatch guard on %d cases; "
          "copy.deepcopy(cls) is cls on 7 classes (identity disjunct); "
          "copy.deepcopy(obj) is not obj on %d non-class leaves (distinct "
          "disjunct); F2P identity preserved."
          % (len(cases), len(non_class_leaves)))
    sys.exit(0)


if __name__ == "__main__":
    main()
