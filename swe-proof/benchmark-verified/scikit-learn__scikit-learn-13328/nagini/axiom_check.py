#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13328.

model.py has TWO consumed @ContractOnly axioms:

`validate_matrix`, modelling the input-validation step (the routine the
fitting code runs the feature matrix through), whose contract is:

  - precondition  `0 <= input_rep <= 2` : the three modelled representations;
  - postcondition `Result() == validated_rep(input_rep, request_floating)` :
        the validated representation is exactly the deep model (A-reference 1
        below), which this script validates against the REAL validation callee;
  - postcondition `matrix_rep(input_rep, Result())` : an abstract capability
        token with NO runtime content. It records that the matrix ACTUALLY HAS
        the returned representation after validation, so a representation tag
        handed to the downstream negation step cannot be fabricated (its sole
        producer is this axiom, and the value clause pins the tag to the real
        validator's output). Nothing to fuzz at runtime beyond A-reference 1,
        which grounds the value the token names.

`negate_rows`, modelling the downstream gradient negation step (numpy unary
`-` on the validated row-slice). Its contract is the WEAKEST sufficient for
the proof and is grounded entirely in the deep models this script validates
against the REAL callees:

  - precondition  `matrix_rep(input_rep, rep)` : token evidence that the matrix
        ACTUALLY has representation `rep` here (see above -- only the
        validation step grants it, so the tag is honest);
  - precondition  `supports_negation(rep)` : the negation can only run when the
        actual representation supports negation (numpy `-` raises otherwise);
  - postcondition `ToSeq(Result()) == negated(...)` : the element-wise negation;
  - postcondition `negation_performed(input_rep, row_values)` : an abstract capability token
        with NO runtime content -- it carries no value and asserts nothing about
        the data. It exists purely to make the negation step MANDATORY in the
        caller's contract (the control-flow effect "the negation actually ran
        for this input, rather than raising", which has no value-level witness).
        It is sound by construction: it is granted ONLY on the success path of
        `negate_rows`, whose preconditions already demand real negation-
        definedness for the representation the matrix actually has, so the
        token can never over-claim a negation that the real numpy `-` would
        have refused. Nothing to fuzz at runtime; the obligation it discharges
        is the runtime "fit must not raise" of `test_huber_bool`.

The remaining models (`validated_rep`, `supports_negation`, `negated`) are
A-references validated against the REAL callees they stand in for:

  (A-reference 1) `validated_rep(input_rep, request_floating)` == the element
      representation (numpy dtype kind) produced by the REAL
      `sklearn.utils.check_array` validation step. The model claims:
        - request_floating == True  -> always a FLOATING representation,
          regardless of input representation (logical / integral / floating);
        - request_floating == False -> the input representation is preserved.
      The real validator is exercised with and without the floating-dtype
      request `dtype=[np.float64, np.float32]` (the gold patch's argument) over
      logical (bool), integral (int) and floating (float) input arrays.

  (A-reference 2) `supports_negation(rep)` == whether numpy's unary `-`
      operator is actually defined for an array of that representation. The
      model claims negation is undefined exactly for the logical (bool)
      representation. This is checked by attempting `-array` for each dtype.

  (A-reference 3) `negated(vals)` == the element-wise numpy unary negation of a
      float row-slice (the gradient step `-axis0_safe_slice(X, ...)`).

  (end-to-end) the modelled contract -- "for EVERY input representation,
      including logical, fitting succeeds and the selected rows can be negated"
      -- holds for the REAL validator + numpy negation iff the floating
      representation is requested (the patched behaviour), and FAILS for a
      logical input without it (the pre-patch behaviour, i.e. the reported bug).

Imports only numpy and sklearn.utils.check_array -- the very validator the gold
patch passes the new dtype argument to. Exit 0 iff every obligation holds.
"""
import sys

import numpy as np
from sklearn.utils import check_array


# --- model.py reference encodings (kept in lock-step with model.py) ----------

REP_LOGICAL = 0
REP_INTEGRAL = 1
REP_FLOATING = 2

# input representation tag  ->  (constructor dtype, numpy dtype kind)
_REP_DTYPE = {
    REP_LOGICAL: np.bool_,
    REP_INTEGRAL: np.int64,
    REP_FLOATING: np.float64,
}


def supports_negation_model(rep):
    """model.py: negation defined iff the representation is not logical."""
    return rep != REP_LOGICAL


def validated_rep_model(input_rep, request_floating):
    """model.py: floating request coerces every input to floating; otherwise
    the input representation is preserved."""
    if request_floating:
        return REP_FLOATING
    return input_rep


def negated_model(vals):
    """model.py: element-wise negation of the sequence."""
    return [-v for v in vals]


# --- real-callee observation helpers -----------------------------------------

def _kind_to_rep(kind):
    """numpy dtype kind char -> modelled representation tag."""
    if kind == "b":
        return REP_LOGICAL
    if kind in ("i", "u"):
        return REP_INTEGRAL
    if kind == "f":
        return REP_FLOATING
    raise AssertionError("unexpected dtype kind %r" % kind)


def real_validated_rep(input_rep, request_floating):
    """Run the REAL sklearn validator and report the representation tag of the
    validated array. `request_floating` mirrors the gold patch's
    `dtype=[np.float64, np.float32]`; otherwise the default (`dtype='numeric'`,
    i.e. no floating request) is used -- the pre-patch behaviour."""
    dtype_in = _REP_DTYPE[input_rep]
    X = np.array([[1, 0], [0, 1], [1, 1]], dtype=dtype_in)
    if request_floating:
        validated = check_array(X, copy=False, accept_sparse=["csr"],
                                dtype=[np.float64, np.float32])
    else:
        validated = check_array(X, copy=False, accept_sparse=["csr"])
    return _kind_to_rep(validated.dtype.kind)


def real_supports_negation(rep):
    """Whether numpy's unary `-` is actually defined for this representation."""
    X = np.array([[1, 0], [0, 1]], dtype=_REP_DTYPE[rep])
    try:
        (-X)
        return True
    except TypeError:
        return False


# --- the checks --------------------------------------------------------------

def main():
    reps = [REP_LOGICAL, REP_INTEGRAL, REP_FLOATING]

    # (A-reference 1) validated_rep == real check_array dtype behaviour
    for input_rep in reps:
        for request_floating in (False, True):
            model = validated_rep_model(input_rep, request_floating)
            real = real_validated_rep(input_rep, request_floating)
            assert model == real, (
                "validated_rep deep model unsound: input_rep=%d "
                "request_floating=%s -> model=%d real=%d"
                % (input_rep, request_floating, model, real))

    # (A-reference 2) supports_negation == real numpy negation definedness
    for rep in reps:
        model = supports_negation_model(rep)
        real = real_supports_negation(rep)
        assert model == real, (
            "supports_negation deep model unsound: rep=%d model=%s real=%s"
            % (rep, model, real))

    # (A-reference 3) negated == real numpy element-wise negation, on the
    # float row-slice the gradient step actually negates.
    import random
    rng = random.Random(13328)
    for _ in range(5000):
        n = rng.randint(0, 16)
        vals = [rng.randint(-5, 5) for _ in range(n)]
        Xf = np.array(vals, dtype=np.float64)
        real = list((-Xf).astype(np.int64))
        model = negated_model(vals)
        assert model == [int(x) for x in real], (
            "negated deep model unsound on %r: model=%r real=%r"
            % (vals, model, real))

    # (end-to-end) the modelled contract holds for the REAL validator + numpy
    # negation: requesting the floating representation lets EVERY input
    # representation (including logical) be validated then negated; the
    # pre-patch behaviour (no floating request) fails for the logical input.
    for input_rep in reps:
        # patched: floating requested -> negation always succeeds
        patched_rep = real_validated_rep(input_rep, True)
        assert real_supports_negation(patched_rep), (
            "patched validation does not support negation for input_rep=%d"
            % input_rep)
    # pre-patch logical input: validation preserves logical -> negation fails
    prepatch_logical = real_validated_rep(REP_LOGICAL, False)
    assert not real_supports_negation(prepatch_logical), (
        "expected pre-patch logical input to be un-negatable, but it was not "
        "(the reported bug would not reproduce)")

    print("G-AX OK: validated_rep / supports_negation / negated deep models "
          "== real sklearn.utils.check_array + numpy negation over %d "
          "representation x request combos, 5000 negation fuzz inputs, and the "
          "end-to-end patched/pre-patch contract." % (len(reps) * 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
