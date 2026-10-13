#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-12682.

This bundle consumes NO @ContractOnly axioms and references NO deep model of a
library callee: the fix is pure integer parameter propagation, modelled
directly. There is therefore no callee-behaviour over-approximation to falsify.

What still admits an executable check is the PROVENANCE of the two numeric
constants the model uses to characterise the bug (model.py `pure` region):

  * `lars_builtin_default() == 500`  -- the least-angle lasso solver class's own
    built-in iteration default, silently used pre-patch when the budget is not
    threaded into its constructor (model_prepatch_2.py, behaviour B2).
  * `coder_param_default() == 1000`  -- the generic coder routine's own
    iteration-budget parameter default, silently used pre-patch when the
    transform path does not forward the configured budget (model_prepatch.py,
    behaviour B1).

These are facts about the real library at this version. The check introspects
the real signatures (no fitting, no numeric work) and asserts the modelled
constants equal the library's actual defaults. If a future library default
drifted, the discriminating prepatch values would be stale and this check would
catch it. Imports only the package under test; exit 0 iff every constant holds.
"""
import inspect
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---
LARS_BUILTIN_DEFAULT = 500     # lars_builtin_default()
CODER_PARAM_DEFAULT = 1000     # coder_param_default()


def _default_of(func, param_name):
    """The default value bound to `param_name` in `func`'s signature."""
    sig = inspect.signature(func)
    p = sig.parameters[param_name]
    assert p.default is not inspect.Parameter.empty, (
        "%s has no default for %r" % (func, param_name))
    return p.default


def main():
    from sklearn.linear_model import LassoLars
    from sklearn.decomposition.dict_learning import (
        _sparse_encode, sparse_encode)

    # B2 provenance: the least-angle lasso solver's built-in iteration default.
    lars_default = _default_of(LassoLars.__init__, "max_iter")
    assert lars_default == LARS_BUILTIN_DEFAULT, (
        "lars_builtin_default() unsound: model uses %d, LassoLars default is %r"
        % (LARS_BUILTIN_DEFAULT, lars_default))

    # B1 provenance: the generic coder routines' own iteration-budget default,
    # which is what is silently used pre-patch when transform does not forward
    # the configured value. Both layers of the coder default to 1000.
    se_default = _default_of(_sparse_encode, "max_iter")
    assert se_default == CODER_PARAM_DEFAULT, (
        "coder_param_default() unsound: model uses %d, _sparse_encode default "
        "is %r" % (CODER_PARAM_DEFAULT, se_default))

    pub_default = _default_of(sparse_encode, "max_iter")
    assert pub_default == CODER_PARAM_DEFAULT, (
        "coder_param_default() unsound: model uses %d, sparse_encode default "
        "is %r" % (CODER_PARAM_DEFAULT, pub_default))

    print("G-AX OK: provenance constants sound -- LassoLars.max_iter default "
          "== %d (B2), _sparse_encode/sparse_encode max_iter default == %d "
          "(B1)." % (LARS_BUILTIN_DEFAULT, CODER_PARAM_DEFAULT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
