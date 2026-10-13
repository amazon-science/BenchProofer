#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14983.

This bundle consumes NO @ContractOnly axioms: the changed behaviour (the
per-parameter value resolution of `_build_repr`) is modelled DEEPLY by the
`@Pure` helper `resolved_value` in model.py. G-AX therefore validates that
deep model against the REAL Python semantics it stands for, as an A-reference:

    real resolution per key, for an object `self` and parameter name `key`:
        value = getattr(self, key, None)            # primary attribute lookup
        if value is None and hasattr(self, 'cvargs'):
            value = self.cvargs.get(key, None)      # secondary store fallback
        # `value` is the reported value (None == absent)

    deep model resolved_value(attr, none, has_store, store, key):
        attr != none            -> attr             # present attribute wins
        has_store and key in store -> store[key]    # store fallback
        else                    -> none             # absent

under the bijection: `none` <-> Python None; `attr` <-> getattr(self,key,None);
`has_store` <-> hasattr(self, 'cvargs'); `store` <-> self.cvargs.

Two layers of evidence:
  (1) End-to-end oracle: the public repr of the real RepeatedKFold /
      RepeatedStratifiedKFold (with the gold __repr__ + _build_repr in place)
      equals the string the FAIL_TO_PASS test demands. This is checked only
      when sklearn is importable in the container.
  (2) Reference equality: a faithful Python transcription of the real per-key
      resolution (`real_resolution`) is compared, on boundary + randomized
      fuzz objects (including objects WITHOUT a cvargs store, the
      test_build_repr / MockSplitter case), against the deep model
      `resolved_value`. Exit 0 iff every observation agrees.

stdlib-only imports; the sklearn import is optional and guarded so the
reference-equality core always runs. Exit 0 iff sound.
"""
import random
import sys

# A sentinel int standing for Python None in the deep model. Real parameter
# values used below are non-negative; the sentinel is negative and distinct.
NONE = -999999


# --- deep model transcription (kept in lock-step with model.py) --------------

def resolved_value(attr, none, has_store, store, key):
    """Faithful transcription of model.py's @Pure resolved_value."""
    if attr != none:
        return attr
    if has_store and (key in store):
        return store[key]
    return none


# --- real per-key resolution (the A-reference: real Python semantics) --------

def real_resolution(self, name):
    """The REAL _build_repr per-key value resolution (gold), in Python.

    Mirrors, line for line, the patched body (with `name` the string attribute
    / store key):
        value = getattr(self, name, None)
        if value is None and hasattr(self, 'cvargs'):
            value = self.cvargs.get(name, None)
    Returns the reported value (None == absent).
    """
    value = getattr(self, name, None)
    if value is None and hasattr(self, 'cvargs'):
        value = self.cvargs.get(name, None)
    return value


def to_model_inputs(self, name):
    """Map the real object/name to the deep model's (attr, none, has_store,
    store, key) arguments, encoding None as the NONE sentinel. `store` is keyed
    by the same string name (the model `key`)."""
    raw_attr = getattr(self, name, None)
    attr = NONE if raw_attr is None else raw_attr
    has_store = hasattr(self, 'cvargs')
    store = {}
    if has_store:
        # only concrete (non-None) entries, matching the model precondition
        for k, v in self.cvargs.items():
            if v is not None:
                store[k] = v
    return attr, NONE, has_store, store, name


def real_to_sentinel(value):
    """Encode the real reported value (None == absent) as a model int."""
    return NONE if value is None else value


class Obj(object):
    """Minimal stand-in object: arbitrary direct attributes, optional cvargs.

    Model `int` keys are parameter NAMES; real Python attribute/dict keys are
    strings, so each int key `k` is materialised as the attribute/store name
    `str(k)`. The resolution logic is key-agnostic, so this renaming is an
    exact bijection (model.py §"Parameter names are int keys").
    """

    def __init__(self, attrs, cvargs=None):
        for k, v in attrs.items():
            setattr(self, str(k), v)
        if cvargs is not None:
            self.cvargs = {str(k): v for k, v in cvargs.items()}


def check_reference(self, key):
    """Assert deep model == real per-key resolution for (self, key).

    `key` is an int model name; the real object uses the string name str(key).
    """
    name = str(key)
    attr, none, has_store, store, k = to_model_inputs(self, name)
    model_out = resolved_value(attr, none, has_store, store, k)
    real_out = real_to_sentinel(real_resolution(self, name))
    assert model_out == real_out, (
        "resolved_value deep model unsound: object attrs=%r cvargs=%r key=%r: "
        "real gives %r, deep model gives %r"
        % (vars(self), getattr(self, 'cvargs', '<none>'), name,
           real_out, model_out))


def main():
    rng = random.Random(14983)

    # --- (2) reference equality: boundary objects ------------------------
    # Names are int keys (as in model.py); value None == absent.
    boundary = [
        # attribute present directly -> wins
        (Obj({1: 2}), 1),
        # attribute absent, NO cvargs store -> absent (the MockSplitter /
        # test_build_repr case: c=None stays None)
        (Obj({1: 5}), 2),
        (Obj({1: 5}, cvargs=None), 2),   # cvargs=None -> no store attr at all
        # attribute absent, cvargs store HAS the key -> store value (the bug
        # being fixed: n_splits lives in cvargs, must NOT be reported absent)
        (Obj({}, cvargs={7: 2}), 7),
        # attribute absent, cvargs store does NOT have key -> absent
        (Obj({}, cvargs={7: 2}), 9),
        # attribute present AND store has key -> attribute wins
        (Obj({7: 11}, cvargs={7: 2}), 7),
        # attribute explicitly None, store has key -> store value
        (Obj({3: None}, cvargs={3: 4}), 3),
        # attribute explicitly None, no store -> absent
        (Obj({3: None}), 3),
    ]
    for self, key in boundary:
        check_reference(self, key)

    # --- (2) reference equality: randomized fuzz -------------------------
    for _ in range(20000):
        keys = list(range(rng.randint(1, 6)))
        # random direct attributes (some present, some None, some absent)
        attrs = {}
        for k in keys:
            r = rng.random()
            if r < 0.34:
                attrs[k] = rng.randint(0, 50)
            elif r < 0.5:
                attrs[k] = None
            # else: absent
        has_store = rng.random() < 0.6
        cvargs = None
        if has_store:
            cvargs = {}
            for k in keys:
                if rng.random() < 0.6:
                    cvargs[k] = rng.randint(0, 50)  # concrete (non-None)
        self = Obj(attrs, cvargs=cvargs)
        for key in keys + [rng.randint(0, 8)]:
            check_reference(self, key)

    # --- (1) end-to-end oracle (only if sklearn is importable) -----------
    e2e = "skipped (sklearn not importable here)"
    try:
        from sklearn.model_selection import (RepeatedKFold,
                                             RepeatedStratifiedKFold)
        for cls in (RepeatedKFold, RepeatedStratifiedKFold):
            obj = cls(n_splits=2, n_repeats=6)
            expected = ('%s(n_repeats=6, n_splits=2, random_state=None)'
                        % cls.__name__)
            got = repr(obj)
            assert got == expected, (
                "end-to-end repr mismatch for %s: expected %r, got %r"
                % (cls.__name__, expected, got))
            # and the real per-key resolution must agree with the deep model
            # for the introspected parameters n_repeats / n_splits / random_state
            from sklearn.model_selection._split import _build_repr  # noqa: F401
            for key in ('n_splits', 'n_repeats', 'random_state'):
                raw = getattr(obj, key, None)
                attr = NONE if raw is None else raw
                has_store = hasattr(obj, 'cvargs')
                store = {}
                if has_store:
                    for k, v in obj.cvargs.items():
                        if v is not None:
                            store[k] = v
                model_out = resolved_value(attr, NONE, has_store, store, key)
                real_out = real_to_sentinel(real_resolution(obj, key))
                assert model_out == real_out, (
                    "deep model vs real _build_repr disagree on %s.%s: "
                    "real=%r model=%r" % (cls.__name__, key, real_out, model_out))
        e2e = "PASS (RepeatedKFold + RepeatedStratifiedKFold repr == F2P string)"
    except ImportError:
        pass

    print("G-AX OK: resolved_value deep model == real _build_repr per-key "
          "resolution on %d boundary + ~%d fuzz observations; end-to-end: %s"
          % (len(boundary), 20000, e2e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
