#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13328
(nagini).

SHADOW: the impl region of model.py `fit_robust_regressor`, copied verbatim
below with the contract calls (Requires/Ensures) stripped. The impl region
invokes two @ContractOnly callees, realized here by their REAL repo
counterparts per mapping.md sections 3.0a / 3.0:

  - `validate_matrix(input_rep, request_floating)` -> the input-validation
        routine the fitting code runs the feature matrix through
        (sklearn's check_X_y / check_array), exercised on a matrix of the
        given element representation, with the floating-representation
        request mapped per mapping.md section 2 (request_floating=True <->
        the floating dtype list handed to the validator; False <-> the
        default request). Returns the representation tag of the VALIDATED
        matrix (numpy dtype kind -> tag, mapping.md section 2).
  - `negate_rows(input_rep, rep, row_values)` -> numpy's unary `-` operator
        applied to the selected row values carried at the representation
        `rep` the matrix actually has after validation (the downstream
        gradient step's negation). Raises for a logical representation --
        the runtime image of the axiom's precondition -- so the shadow run
        itself witnesses that the patched validation makes the negation
        well-defined for every input representation.

The two capability tokens (`matrix_rep`, `negation_performed`) are
proof-level and value-free; their runtime image is exactly "the negation
step ran to completion rather than raising", which this script observes
directly on both the shadow and the oracle paths.

Type bridge (mapping.md section 2): numpy dtype kind <-> integer tag
{0=logical, 1=integral, 2=floating}; the selected row slice <-> List[int] of
element values (logical-representation values are drawn from {0,1}, the only
values that representation carries). @Pure helpers (`supports_negation`,
`validated_rep`, `negated`) copy over as plain functions on a PSeq shim and
are used as redundant spec-consistency probes.

ORACLE: the REAL patched repo function the model models per mapping.md --
`HuberRegressor.fit` (sklearn/linear_model/huber.py). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. Two oracle layers:

  1. end-to-end boundary fits: the real patched `fit` is run on feature
     matrices of all three element representations (including the logical
     one) and must complete without raising -- the runtime image of the
     `negation_performed` token being grantable for EVERY input. The
     validation callee inside `fit` is instrumented (wrap-and-restore, no
     repo edit) to capture the representation the matrix ACTUALLY has after
     in-fit validation, which must equal the shadow's `validate_matrix`
     observation and the pure `validated_rep` model.
  2. per-case value oracle (the >=1e5 diff): for each fuzzed
     (input_rep, row_values), the value-bearing matrix is pushed through the
     real validation routine exactly as the patched `fit` invokes it, the
     validated slice is negated by real numpy `-` (must not raise), and the
     resulting element values must equal the shadow's output and the pure
     `negated` model.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 13328.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys
import warnings

import numpy as np
from sklearn.utils import check_X_y

SEED = 13328
N_FUZZ = 100_000


# --- PSeq shim (only the operations `negated` uses) ---------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    """Materialize a list as a pure sequence (the Nagini ToSeq bridge)."""
    return PSeq._wrap(lst)


# --- representation-tag bridge (mapping.md section 2) --------------------------

REP_LOGICAL = 0
REP_INTEGRAL = 1
REP_FLOATING = 2

# representation tag -> the numpy dtype carrying that element representation
_REP_DTYPE = {
    REP_LOGICAL: np.bool_,
    REP_INTEGRAL: np.int64,
    REP_FLOATING: np.float64,
}


def _kind_to_rep(kind):
    """numpy dtype kind char -> modelled representation tag."""
    if kind == "b":
        return REP_LOGICAL
    if kind in ("i", "u"):
        return REP_INTEGRAL
    if kind == "f":
        return REP_FLOATING
    raise AssertionError("unexpected dtype kind %r" % kind)


def _validate(X, y, request_floating):
    """The REAL validation callee, invoked with the same argument set the
    fitting routine uses (mapping.md section 1: the call site in `fit`),
    parameterised by whether a floating representation is requested of it."""
    if request_floating:
        return check_X_y(X, y, copy=False, accept_sparse=["csr"],
                         y_numeric=True, dtype=[np.float64, np.float32])
    return check_X_y(X, y, copy=False, accept_sparse=["csr"], y_numeric=True)


# --- the @ContractOnly callees, realized by their REAL repo counterparts ------

def validate_matrix(input_rep, request_floating):
    """REAL callee: the input-validation step. The model threads no element
    values through validation (values are preserved by the coercion), so the
    representation observation is made on a fixed small matrix of the input
    representation; the returned tag is the dtype kind of the VALIDATED
    matrix. (The `matrix_rep` token this grants is proof-level; its runtime
    content is exactly this observation.)"""
    dtype_in = _REP_DTYPE[input_rep]
    X = np.array([[1, 0], [0, 1], [1, 1]], dtype=dtype_in)
    y = np.arange(3, dtype=np.float64)
    Xv, _ = _validate(X, y, request_floating)
    return _kind_to_rep(Xv.dtype.kind)


def negate_rows(input_rep, rep, row_values):
    """REAL callee: numpy's unary `-` on the selected row values carried at
    the representation `rep` the matrix actually has here. numpy raises for
    the logical representation -- the runtime image of the axiom's
    `supports_negation` precondition -- and returns the element-wise
    negation otherwise. (The `negation_performed` token is proof-level; its
    runtime content is this call returning rather than raising.)"""
    X = np.array(row_values, dtype=_REP_DTYPE[rep])
    neg = -X  # raises TypeError when the representation does not support it
    return [int(v) for v in neg]


# --- pure helpers from model.py, contracts stripped ----------------------------

def supports_negation(rep):
    return rep != 0  # REP_LOGICAL == 0


def validated_rep(input_rep, request_floating):
    if request_floating:
        return 2  # REP_FLOATING
    return input_rep


def negated(vals):
    if len(vals) == 0:
        return PSeq(0).take(0)
    return PSeq(-vals[0]) + negated(vals.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def fit_robust_regressor(input_rep, row_values):
    # Validation: request a floating representation so that the subsequent
    # negation is well-defined regardless of the input representation.
    rep = validate_matrix(input_rep, True)
    result = negate_rows(input_rep, rep, row_values)
    return result
    # (impl region ends)


# --- oracle layer 2: real validation + real negation on value-bearing rows ----

def oracle_negate(input_rep, row_values):
    """Push the ACTUAL value-bearing matrix through the real validation
    routine exactly as the patched fitting code invokes it, then negate the
    validated slice with real numpy `-` (must not raise for any input
    representation). Returns the element values of the negation."""
    X = np.array(row_values, dtype=_REP_DTYPE[input_rep]).reshape(-1, 1)
    y = np.arange(len(row_values), dtype=np.float64)
    Xv, _ = _validate(X, y, True)
    neg = -Xv  # the downstream gradient step's negation; must be defined
    return [int(v) for v in neg.ravel()], _kind_to_rep(Xv.dtype.kind)


def check_case(input_rep, row_values):
    """Diff shadow vs oracle on one (representation, row values) input;
    return an error string on disagreement, else None."""
    try:
        shadow = fit_robust_regressor(input_rep, row_values)
    except TypeError as e:
        return ("DISAGREEMENT (shadow negation raised)\n"
                "  input_rep=%r row_values=%r\n  shadow raised: %r"
                % (input_rep, row_values, e))
    if len(row_values) == 0:
        # the validator requires a nonempty matrix; the negation oracle for
        # the empty slice is real numpy `-` on the empty validated-
        # representation slice (defined, empty result)
        real = [int(v) for v in -np.array([], dtype=np.float64)]
        real_rep = REP_FLOATING
    else:
        try:
            real, real_rep = oracle_negate(input_rep, row_values)
        except TypeError as e:
            return ("DISAGREEMENT (real negation raised after validation)\n"
                    "  input_rep=%r row_values=%r\n  real raised: %r"
                    % (input_rep, row_values, e))
    if shadow != real:
        return ("DISAGREEMENT\n  input_rep=%r row_values=%r\n"
                "  shadow=%r\n  real=%r"
                % (input_rep, row_values, shadow, real))
    # redundant spec-consistency probes: pure models vs both paths
    if ToSeq(shadow) != negated(ToSeq(row_values)):
        return ("DISAGREEMENT (pure `negated` model)\n"
                "  input_rep=%r row_values=%r\n  shadow=%r\n  negated=%r"
                % (input_rep, row_values, shadow,
                   list(negated(ToSeq(row_values))._t)))
    if real_rep != validated_rep(input_rep, True) or not supports_negation(real_rep):
        return ("DISAGREEMENT (validated representation)\n"
                "  input_rep=%r\n  real validated rep=%r\n  model=%r"
                % (input_rep, real_rep, validated_rep(input_rep, True)))
    return None


# --- oracle layer 1: the real patched fit, end-to-end --------------------------

def _rows_to_matrix(input_rep, values, n_features=2):
    """A small 2-D feature matrix of the given representation built from the
    value pool (logical values restricted to {0,1})."""
    n = max(len(values), n_features * 3)
    vals = [values[i % len(values)] if values else i for i in range(n * n_features)]
    return np.array(vals, dtype=_REP_DTYPE[input_rep]).reshape(n, n_features)


def check_end_to_end_fit(input_rep, values, seed):
    """Run the REAL patched fitting routine on a matrix of this
    representation. It must complete without raising (the runtime image of
    the `negation_performed` token for every input representation, i.e. the
    behaviour the modeled contract demands). The in-fit validation callee is
    wrapped (and restored) to capture the representation the matrix ACTUALLY
    has after validation, diffed against the shadow's observation."""
    from sklearn.linear_model import HuberRegressor
    import sklearn.linear_model.huber as huber_mod

    X = _rows_to_matrix(input_rep, values)
    rng = np.random.RandomState(seed)
    y = rng.uniform(-3.0, 3.0, size=X.shape[0])

    captured = {}
    real_cxy = getattr(huber_mod, "check_X_y", None)

    def recorder(Xa, ya, **kw):
        Xv, yv = real_cxy(Xa, ya, **kw)
        captured["rep"] = _kind_to_rep(Xv.dtype.kind)
        return Xv, yv

    if real_cxy is not None:
        huber_mod.check_X_y = recorder
    try:
        HuberRegressor(max_iter=20).fit(X, y)
    except TypeError as e:
        return ("DISAGREEMENT (real patched fit raised)\n"
                "  input_rep=%r X.dtype=%r\n  fit raised: %r"
                % (input_rep, X.dtype, e))
    finally:
        if real_cxy is not None:
            huber_mod.check_X_y = real_cxy

    shadow_rep = validate_matrix(input_rep, True)
    if "rep" in captured and captured["rep"] != shadow_rep:
        return ("DISAGREEMENT (in-fit validated representation)\n"
                "  input_rep=%r\n  real in-fit rep=%r\n  shadow rep=%r"
                % (input_rep, captured["rep"], shadow_rep))
    if not supports_negation(shadow_rep):
        return ("DISAGREEMENT (shadow validated rep does not support "
                "negation)\n  input_rep=%r rep=%r" % (input_rep, shadow_rep))
    return None


# --- input domain --------------------------------------------------------------

def _draw_values(rng, input_rep, n):
    """Element values the representation can carry (mapping.md section 2:
    the logical representation carries only {0,1})."""
    if input_rep == REP_LOGICAL:
        return [rng.randint(0, 1) for _ in range(n)]
    return [rng.randint(-10**6, 10**6) for _ in range(n)]


def boundary_cases():
    """(input_rep, row_values) boundaries: every representation; empty,
    singleton and longer slices; zero / extreme / mixed-sign values."""
    cases = []
    for rep in (REP_LOGICAL, REP_INTEGRAL, REP_FLOATING):
        cases.append((rep, []))
        cases.append((rep, [0]))
        cases.append((rep, [1]))
        cases.append((rep, [0, 1, 1, 0]))
    for rep in (REP_INTEGRAL, REP_FLOATING):
        cases.append((rep, [-1]))
        cases.append((rep, [-10**6, 10**6, 0, -1, 1]))
        cases.append((rep, [7, -3, 0, 0, 12, -12]))
    return cases


def main():
    warnings.simplefilter("ignore")

    checked = 0

    # boundary + fuzz value diff (shadow vs real validation + real negation)
    for (input_rep, row_values) in boundary_cases():
        err = check_case(input_rep, row_values)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        input_rep = rng.randint(0, 2)
        n = rng.randint(1, 12)
        row_values = _draw_values(rng, input_rep, n)
        err = check_case(input_rep, row_values)
        if err:
            print(err)
            return 1
        checked += 1

    # end-to-end: the real patched fit completes for EVERY representation
    # (including the logical one) and its in-fit validated representation
    # matches the shadow's observation
    n_fits = 0
    for input_rep in (REP_LOGICAL, REP_INTEGRAL, REP_FLOATING):
        for k in range(8):
            fit_rng = random.Random(SEED + 7 * k + input_rep)
            vals = _draw_values(fit_rng, input_rep, 8)
            if input_rep != REP_LOGICAL:
                vals = [v % 97 - 48 for v in vals]  # keep fits well-scaled
            err = check_end_to_end_fit(input_rep, vals, seed=SEED + k)
            if err:
                print(err)
                return 1
            n_fits += 1

    print("G-CONF OK: shadow impl (real validation + real numpy negation "
          "callees) == real patched pipeline on %d inputs (%d boundary + %d "
          "fuzz, seed %d), and the real patched fit completed on %d "
          "end-to-end matrices across all 3 representations."
          % (checked, len(boundary_cases()), N_FUZZ, SEED, n_fits))
    print(json.dumps({"checked": checked, "end_to_end_fits": n_fits,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees call the real repo "
                                "functions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
