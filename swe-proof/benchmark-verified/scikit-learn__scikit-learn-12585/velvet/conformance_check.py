#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-12585.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable branch the
`clone` dispatch takes:

  * SHADOW  — `route(isCollection, exposesParams, isClassObject, strict)`, the
              R/I-tagged decision of Solution.lean's impl, transliterated to
              Python. The triple is read from a FIXED per-tag table (the
              mapping.md §2 bijection: each value-kind tag declares its
              `(isCollection, exposesParams, isClassObject)`); `strict` is the
              `safe` flag. The shadow NEVER inspects the real object and never
              calls the real `clone`.

  * ORACLE  — the REAL post-patch `clone` (the gold patch is applied in the
              container) run on the materialized value, with the branch it took
              recovered purely BEHAVIORALLY:
                - the UNCHANGED collection test is replicated on the real value
                  (`type(v) in (list, tuple, set, frozenset)`) -> mapElements;
                - otherwise the CHANGED "non-configurable" decision is observed,
                  not replicated: if `clone(v, safe=True)` raises the
                  "Cannot clone" TypeError, the value is non-configurable
                  (refuse under strict, deepCopy under lenient); if it succeeds,
                  the value was reconstructed.
              The oracle also asserts the F2P observable directly: for a class
              object, `clone(C, safe=False) is C` (identity preserved).

They must agree on every (value-kind, safe) input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sklearn.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import traceback

SEED = 12585
N_FUZZ = 100_000


def main():
    rng = random.Random(SEED)
    try:
        from sklearn.base import BaseEstimator, clone
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import sklearn.base: %r" % e)
        return 2

    # --- value-kind tags + their fixed (isCollection, exposesParams, isClassObject)
    #     triple (mapping.md §2) and a materializer producing a REAL value -------
    class MyEst(BaseEstimator):
        def __init__(self, x=1):
            self.x = x

    class PlainClass:
        pass

    # tag -> (triple, materializer)
    KINDS = {
        # an estimator *instance*: exposes params, is NOT a class -> reconstruct
        "estimator_instance": ((False, True, False), lambda: MyEst(x=7)),
        # an estimator *class*: exposes params AND is a class -> non-configurable
        #   (the discriminating case the patch fixes)
        "estimator_class": ((False, True, True), lambda: MyEst),
        # a plain class object: no params, is a class -> non-configurable
        "plain_class": ((False, False, True), lambda: PlainClass),
        # the `type` metaclass itself: is a class -> non-configurable
        "type_object": ((False, False, True), lambda: type),
        # ordinary non-estimator values -> non-configurable
        "int_value": ((False, False, False), lambda: 7),
        "str_value": ((False, False, False), lambda: "hello"),
        "float_value": ((False, False, False), lambda: 3.5),
        "none_value": ((False, False, False), lambda: None),
        # collections (handled first); use estimator-instance elements so the
        # recursive element clone succeeds under safe=True too
        "list_value": ((True, False, False), lambda: [MyEst(x=1), MyEst(x=2)]),
        "tuple_value": ((True, False, False), lambda: (MyEst(x=1),)),
        "set_value": ((True, False, False), lambda: set()),
        "frozenset_value": ((True, False, False), lambda: frozenset()),
        # empty list: cleanest mapElements (no element recursion)
        "empty_list": ((True, False, False), lambda: []),
    }
    TAGS = list(KINDS.keys())

    # ----- SHADOW: route() transliterated from Solution.lean -------------------
    def route(is_collection, exposes_params, is_class, strict):
        if is_collection:
            return "mapElements"
        if (not exposes_params) or is_class:
            return "refuse" if strict else "deepCopy"
        return "reconstruct"

    def shadow(tag, strict):
        triple, _ = KINDS[tag]
        return route(triple[0], triple[1], triple[2], strict)

    # ----- ORACLE: the real post-patch clone, branch recovered behaviorally ----
    def oracle(tag, strict):
        _, make = KINDS[tag]
        v = make()
        # UNCHANGED collection test (I-tagged op) — replicate on the real value.
        if type(v) in (list, tuple, set, frozenset):
            # sanity: the real clone returns a like collection (not the input).
            r = clone(v, safe=strict)
            if type(r) is not type(v):
                raise AssertionError(
                    "collection arm: clone returned %r, not a %s"
                    % (type(r), type(v)))
            return "mapElements"
        # CHANGED decision — OBSERVE, do not replicate. Is the value
        # non-configurable? <=> the strict clone refuses with "Cannot clone".
        non_configurable = False
        try:
            clone(v, safe=True)
        except TypeError as e:
            if "Cannot clone" in str(e):
                non_configurable = True
            else:
                raise
        if non_configurable:
            # F2P observable: lenient clone of a class preserves identity.
            if isinstance(v, type):
                got = clone(v, safe=False)
                if got is not v:
                    raise AssertionError(
                        "identity VIOLATED: clone(%r, safe=False) is not the "
                        "same object (got %r)" % (v, got))
            return "refuse" if strict else "deepCopy"
        return "reconstruct"

    # ----- differential loop ---------------------------------------------------
    def check(tag, strict, disagreements):
        try:
            s = shadow(tag, strict)
            o = oracle(tag, strict)
        except Exception as e:
            disagreements.append(
                "tag=%s strict=%s: ERROR %r\n%s"
                % (tag, strict, e, traceback.format_exc()))
            return
        if s != o:
            disagreements.append(
                "tag=%s strict=%s: shadow=%s oracle=%s" % (tag, strict, s, o))

    disagreements = []
    # exhaustive pass over every (tag, strict)
    for tag in TAGS:
        for strict in (True, False):
            check(tag, strict, disagreements)
            if disagreements:
                break
        if disagreements:
            break
    # fuzz pass (re-samples the small input space deterministically)
    n = 0
    if not disagreements:
        for _ in range(N_FUZZ):
            tag = rng.choice(TAGS)
            strict = rng.random() < 0.5
            check(tag, strict, disagreements)
            n += 1
            if disagreements:
                break

    total = len(TAGS) * 2 + n
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), total, SEED))
        for d in disagreements[:5]:
            print("  " + d)
        return 1
    print("G-CONF OK: R/I shadow of copyRoute (route) agrees with real "
          "post-patch clone branch behaviour on %d inputs (seed=%d), 0 "
          "disagreements; class-object identity preserved under safe=False."
          % (total, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
