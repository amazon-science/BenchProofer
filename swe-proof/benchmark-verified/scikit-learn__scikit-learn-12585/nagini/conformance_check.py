#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-12585
(nagini).

SHADOW: the impl region of model.py (``reproduce``), copied VERBATIM below
with only the contract calls (Requires / Ensures / Exsures / MustTerminate)
stripped. The ``Candidate`` constructor and the ``NotCloneableError``
refusal class copy over the same way; the @Pure helper ``is_leaf`` copies
over as a plain function and is kept as an internal cross-check of the
executable shadow's branch decision. There are no @ContractOnly callees
(mapping.md section 4: no consumed axioms).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- ``sklearn.base.clone``. The gate applies patch.diff to /testbed
before this script runs and sets PYTHONPATH=/testbed, so the import resolves
to the patched module.

TYPE BRIDGE (mapping.md sections 1-2): a concrete candidate object lowers to
the three dispatch-relevant booleans via the documented bijections --
``is_aggregate = type(obj) in (list, tuple, set, frozenset)``,
``has_introspect = hasattr(obj, 'get_params')``,
``is_class_object = isinstance(obj, type)`` -- and the ``safe`` kwarg lowers
via the polarity bijection ``permit_fallback = not safe``. The model's
``NotCloneableError`` refusal corresponds to the repo routine raising
``TypeError``. The observables compared per probe:

  * outcome kind -- returned normally vs refused -- always;
  * result identity (``result is input``) exactly where the mapping asserts
    a definite value: a class-object leaf with the fallback permitted must be
    reference-identical on BOTH sides; a genuine instance (non-leaf) must be
    a distinct object on BOTH sides; a STATE-BEARING non-class leaf is
    atomically reproduced to a distinct object on both sides (mapping.md
    section 3.2). For an atomic-immutable non-class leaf (int / str / None /
    bytes / float / bool) the mapping asserts NO identity -- the model's
    fresh-``Candidate`` allocation is deliberate abstraction slack there --
    so only the outcome kind is compared for those representatives.

The reconstruction machinery a genuine instance delegates to is unobserved
by the contract beyond distinct identity (mapping.md section 4), so the
instance representatives are well-behaved parameterised objects whose
``get_params``/constructor round-trip cleanly, as the routine's domain
expects.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): the precondition admits any
non-aggregate candidate, i.e. every (has_introspect, is_class_object)
combination crossed with both ``permit_fallback`` values. Boundary cases
enumerate concrete representatives of all four combinations (plain values,
state-bearing objects, arrays / sparse matrices when available, classes
without the capability, metaclass-made classes, parameterised classes
exposing the capability, live instances with nested / class-valued / array
parameters) crossed with both fallback polarities; then 100000 randomized
probes draw a weighted mix of freshly built candidates (fresh dynamic
classes included) with a random fallback polarity. Pinned fuzz seed: 12585
(recorded in mapping.md section 5).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (numpy / scipy / sklearn representatives
are used when importable, as they are in the instance image).
"""
import random
import sys

SEED = 12585
N_FUZZ = 100000


# --- shadow: model.py declarations, contract calls stripped -------------------

class Candidate:
    def __init__(self, is_aggregate, has_introspect, is_class_object):
        self.is_aggregate = is_aggregate        # type: bool
        self.has_introspect = has_introspect      # type: bool
        self.is_class_object = is_class_object    # type: bool


class NotCloneableError(Exception):
    """Signals that the candidate is a leaf that cannot be reproduced
    atomically because the caller forbade the fallback copy (stands in for
    the repo routine's refusal exception; mapping.md section 1)."""
    pass


# @Pure helper (pure region), contracts stripped -- internal cross-check only.
def is_leaf(c):
    return (not c.has_introspect) or c.is_class_object


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reproduce(est, permit_fallback):
    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        # Atomic reproduction of a leaf. A class object has no internal
        # parameter state, so its atomic copy is reference-identical (returned
        # as the same reference). A non-class leaf carries state, so its atomic
        # copy is a fresh, distinct object.
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # Genuine instance: take apart and rebuild into a fresh, distinct object.
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt


# --- oracle: the real patched repo function -----------------------------------

def real_clone():
    from sklearn.base import clone
    return clone


# --- representative candidate objects ------------------------------------------

class PlainThing(object):
    """State-bearing object without the introspection capability."""
    def __init__(self, x=0):
        self.x = x


class MetaKlass(type):
    """Custom metaclass; its products are class objects."""
    pass


class DictParamEstimator(object):
    """Generic parameterised object: exposes the introspection capability and
    round-trips through take-apart / rebuild for any kwargs."""
    def __init__(self, **kw):
        self._p = dict(kw)
        for k, v in kw.items():
            setattr(self, k, v)

    def get_params(self, deep=False):
        return dict(self._p)


class ClassMethodParams(object):
    """Exposes the capability as a classmethod: the CLASS itself carries the
    attribute, exercising the class-object dispatch combination."""
    @classmethod
    def get_params(cls, deep=False):
        return {}


def make_fuzz_class(idx, with_introspect):
    """A freshly created class object (optionally exposing the capability)."""
    ns = {'marker': idx}
    if with_introspect:
        def __init__(self, **kw):
            self._p = dict(kw)
            for k, v in kw.items():
                setattr(self, k, v)

        def get_params(self, deep=False):
            return dict(self._p)
        ns['__init__'] = __init__
        ns['get_params'] = get_params
    return type('Fuzz%s%d' % ('E' if with_introspect else 'P', idx),
                (object,), ns)


# --- differential driver --------------------------------------------------------

def _describe(obj):
    try:
        r = repr(obj)
    except Exception:
        r = '<unreprable %s>' % type(obj).__name__
    if len(r) > 200:
        r = r[:200] + '...'
    return '%s : %s' % (type(obj).__name__, r)


def check(oracle, obj, permit_fallback, compare_identity, label):
    """Run shadow and oracle on one candidate; return an error string on
    disagreement, else None. compare_identity=False for atomic-immutable
    non-class leaves, where the bridge asserts no identity."""
    is_agg = type(obj) in (list, tuple, set, frozenset)
    if is_agg:
        return 'INTERNAL: aggregate candidate %s outside the precondition' % label
    est = Candidate(is_agg,
                    hasattr(obj, 'get_params'),
                    isinstance(obj, type))

    # internal cross-check: the pure predicate matches the impl's branch guard
    if is_leaf(est) != ((not est.has_introspect) or est.is_class_object):
        return 'INTERNAL: is_leaf disagrees with the impl guard on %s' % label

    s_refused = False
    s_res = None
    try:
        s_res = reproduce(est, permit_fallback)
    except NotCloneableError:
        s_refused = True

    o_refused = False
    o_res = None
    try:
        o_res = oracle(obj, safe=(not permit_fallback))
    except TypeError:
        o_refused = True
    except Exception as exc:  # any other escape is a disagreement in kind
        return ('DISAGREEMENT on %s [%s], permit_fallback=%r (safe=%r):\n'
                '  shadow (impl region)     = %s\n'
                '  real (patched repo clone) raised unexpected %s: %s'
                % (label, _describe(obj), permit_fallback, not permit_fallback,
                   'refused' if s_refused else 'returned',
                   type(exc).__name__, exc))

    if s_refused != o_refused:
        return ('DISAGREEMENT on %s [%s], permit_fallback=%r (safe=%r):\n'
                '  shadow (impl region)      = %s\n'
                '  real (patched repo clone) = %s'
                % (label, _describe(obj), permit_fallback, not permit_fallback,
                   'refused' if s_refused else 'returned normally',
                   'refused (TypeError)' if o_refused else 'returned normally'))

    if not s_refused and compare_identity:
        s_id = s_res is est
        o_id = o_res is obj
        if s_id != o_id:
            return ('DISAGREEMENT on %s [%s], permit_fallback=%r (safe=%r):\n'
                    '  shadow (impl region)      result is input: %r\n'
                    '  real (patched repo clone) result is input: %r'
                    % (label, _describe(obj), permit_fallback,
                       not permit_fallback, s_id, o_id))
    return None


def boundary_cases():
    """(object, compare_identity, label) triples covering every non-aggregate
    dispatch combination with several concrete representatives each."""
    cases = []

    # atomic-immutable non-class leaves: outcome kind only (bridge asserts no
    # identity for the non-class-leaf disjunct; these reproduce atomically to
    # the SAME object, which the model deliberately leaves unconstrained)
    for obj in (0, 5, -1, 10 ** 30, 3.14, float('nan'), float('inf'),
                True, False, None, '', 'abc', b'', b'bytes', 1 + 2j):
        cases.append((obj, False, 'atomic leaf'))

    # state-bearing non-class leaves: atomic copy is a distinct object
    state_leaves = [({}, 'empty dict'), ({'a': 1, 'b': [2, 3]}, 'dict'),
                    (PlainThing(), 'plain object'),
                    (PlainThing(x=[1, 2]), 'plain object with state'),
                    (bytearray(b'xy'), 'bytearray'),
                    (object(), 'bare object')]
    for obj, tag in state_leaves:
        cases.append((obj, True, 'state leaf (%s)' % tag))
    try:
        import numpy as np
        cases.append((np.array([]), True, 'state leaf (empty array)'))
        cases.append((np.arange(6).reshape(2, 3), True, 'state leaf (array)'))
        cases.append((np.float64(2.5), False, 'atomic-ish leaf (np scalar)'))
    except ImportError:
        np = None
    try:
        from scipy import sparse
        cases.append((sparse.csr_matrix((3, 3)), True, 'state leaf (sparse)'))
    except ImportError:
        pass

    # class objects WITHOUT the introspection capability
    for cls, tag in ((dict, 'builtin dict'), (int, 'builtin int'),
                     (type, 'type itself'), (object, 'object'),
                     (PlainThing, 'plain class'), (MetaKlass, 'metaclass'),
                     (MetaKlass('MetaMade', (), {}), 'metaclass product'),
                     (NotCloneableError, 'exception class')):
        cases.append((cls, True, 'class leaf (%s)' % tag))

    # class objects WITH the introspection capability (the discriminating
    # dispatch combination: the capability is exposed on the class yet the
    # candidate must be treated as a leaf, reproduced reference-identically)
    est_classes = [(DictParamEstimator, 'generic param class'),
                   (ClassMethodParams, 'classmethod-capability class'),
                   (make_fuzz_class(0, True), 'fresh dynamic param class')]
    try:
        from sklearn.preprocessing import StandardScaler
        est_classes.append((StandardScaler, 'repo estimator class'))
    except ImportError:
        StandardScaler = None
    try:
        from sklearn.base import BaseEstimator

        class SkEst(BaseEstimator):
            def __init__(self, alpha=1.0, ref=None):
                self.alpha = alpha
                self.ref = ref
        est_classes.append((SkEst, 'repo-base subclass'))
    except ImportError:
        SkEst = None
    for cls, tag in est_classes:
        cases.append((cls, True, 'introspectable class (%s)' % tag))

    # genuine instances (capability exposed, not a class): rebuilt distinct
    instances = [(DictParamEstimator(), 'no params'),
                 (DictParamEstimator(a=1, b='x'), 'scalar params'),
                 (DictParamEstimator(cls_param=DictParamEstimator),
                  'class-valued param'),
                 (DictParamEstimator(inner=DictParamEstimator(k=2)),
                  'nested instance param'),
                 (DictParamEstimator(seq=[1, 2, 3], tup=(4, 5)),
                  'aggregate params'),
                 (DictParamEstimator(none=None), 'None param'),
                 (ClassMethodParams(), 'classmethod-capability instance')]
    if SkEst is not None:
        instances.append((SkEst(alpha=2.0), 'repo-base instance'))
        instances.append((SkEst(alpha=1.0, ref=PlainThing),
                          'repo-base instance, class-valued param'))
    if StandardScaler is not None:
        instances.append((StandardScaler(), 'repo estimator instance'))
    for obj, tag in instances:
        cases.append((obj, True, 'instance (%s)' % tag))

    return cases


def fuzz_candidate(rng, pools, counter):
    """Build one random non-aggregate candidate; returns
    (object, compare_identity, label)."""
    kind = rng.choices(('atomic', 'state', 'plain_class', 'est_class',
                        'instance'),
                       weights=(15, 25, 15, 15, 30))[0]
    if kind == 'atomic':
        obj = rng.choice((rng.randint(-10 ** 9, 10 ** 9),
                          rng.random(),
                          ''.join(rng.choice('abcXYZ09_') for _ in
                                  range(rng.randint(0, 12))),
                          None, True, False,
                          bytes([rng.randint(0, 255)])))
        return obj, False, 'fuzz atomic leaf'
    if kind == 'state':
        pick = rng.randrange(4 if pools['np'] is not None else 3)
        if pick == 0:
            obj = {('k%d' % i): rng.randint(0, 99)
                   for i in range(rng.randint(0, 4))}
        elif pick == 1:
            obj = PlainThing(x=rng.randint(0, 99))
        elif pick == 2:
            obj = bytearray(rng.randint(0, 255)
                            for _ in range(rng.randint(0, 8)))
        else:
            obj = pools['np'].arange(rng.randint(0, 10))
        return obj, True, 'fuzz state leaf'
    if kind == 'plain_class':
        if rng.random() < 0.3:
            obj = make_fuzz_class(counter, False)
        else:
            obj = rng.choice(pools['plain_classes'])
        return obj, True, 'fuzz class leaf'
    if kind == 'est_class':
        if rng.random() < 0.3:
            obj = make_fuzz_class(counter, True)
        else:
            obj = rng.choice(pools['est_classes'])
        return obj, True, 'fuzz introspectable class'
    # instance: random parameter bag over the value kinds the rebuild
    # machinery handles (scalars, None, classes, nested instances, aggregates)
    params = {}
    for i in range(rng.randint(0, 4)):
        v_kind = rng.randrange(6)
        if v_kind == 0:
            v = rng.randint(-100, 100)
        elif v_kind == 1:
            v = 'v%d' % rng.randint(0, 999)
        elif v_kind == 2:
            v = None
        elif v_kind == 3:
            v = rng.choice(pools['plain_classes'] + pools['est_classes'])
        elif v_kind == 4:
            v = DictParamEstimator(q=rng.randint(0, 9))
        else:
            v = [rng.randint(0, 9) for _ in range(rng.randint(0, 3))]
        params['p%d' % i] = v
    return DictParamEstimator(**params), True, 'fuzz instance'


def main():
    oracle = real_clone()

    try:
        import numpy as np
    except ImportError:
        np = None
    pools = {
        'np': np,
        'plain_classes': [PlainThing, MetaKlass, dict, int, object,
                          make_fuzz_class(999901, False)],
        'est_classes': [DictParamEstimator, ClassMethodParams,
                        make_fuzz_class(999902, True)],
    }

    checked = 0
    boundary = boundary_cases()
    for obj, compare_identity, label in boundary:
        for permit_fallback in (True, False):
            err = check(oracle, obj, permit_fallback, compare_identity, label)
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        obj, compare_identity, label = fuzz_candidate(rng, pools, i)
        permit_fallback = rng.random() < 0.5
        err = check(oracle, obj, permit_fallback, compare_identity, label)
        if err:
            print(err)
            return 1
        checked += 1

    print('G-CONF OK: shadow impl == real patched clone dispatch on %d '
          'candidates (%d boundary x 2 polarities + %d fuzz, seed %d); '
          '0 disagreements.'
          % (checked, len(boundary), N_FUZZ, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == '__main__':
    sys.exit(main())
