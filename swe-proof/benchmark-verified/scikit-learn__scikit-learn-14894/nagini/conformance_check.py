#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14894
(nagini).

SHADOW: the impl region of model.py's `row_pointer_for_block_layout`, copied
verbatim below with the contract calls (the proof `Assert`s) stripped. The
model IS Python: the row-pointer is a plain `List[int]`, so no PSeq shim is
needed, and there are no @Pure helpers. The single @ContractOnly callee,
`range_step`, calls the REAL repo callee it axiomatizes per mapping.md
(`numpy.arange` of the evaluation image) rather than a re-implementation.

ORACLE: the REAL patched repo code the model models per mapping.md — the
dual-coefficient CSR assembly tail of
`sklearn.svm.base.BaseLibSVM._sparse_fit`. The gate applies patch.diff to
/testbed before this script runs (this script does NOT apply any patch);
PYTHONPATH=/testbed makes the patched module importable. Because the modeled
behaviour is a statement sequence inside a fitting method rather than a
standalone function, the oracle executes the REAL statements: the patched
module's AST is parsed, `_sparse_fit`'s tail from the support-vector-count
assignment onward (exactly the assembly the model covers) is compiled and run
byte-for-byte — the repo's own code, not a transliteration — over controlled
bindings of the names it reads (`self.support_vectors_`, `n_class`,
`dual_coef_data`, `np`, `sp`).

An end-to-end grounding leg additionally drives the FULL patched
`_sparse_fit` through real `.fit(...)` calls on sparse inputs — a regression
fit whose optimum keeps no support vectors (per-row width 0, the regime the
change concerns), a regression fit that keeps some, and a 3-class
classification fit (several coefficient rows) — and diffs the resulting
`dual_coef_` against the shadow on the observed (width, n_rows).

TYPE BRIDGE (mapping.md section 2):
  width   <-> the support-vector count `self.support_vectors_.shape[0]`
              (realized by an empty sparse matrix with that many rows —
              only the shape is read);
  n_rows  <-> `n_class` (>= 1), bound directly;
  Result()<-> the row-pointer of `self.dual_coef_` (its `.indptr`, integer
              values); the shadow list is compared elementwise against it.
              Derived observables cross-checked per case: the stored-entry
              count (`data.size`, the F2P observable) must equal the shadow's
              final entry, and the row count (`shape[0]`) must equal
              `len(shadow) - 1` — the empty layout is a 1-row object with the
              two-boundary row-pointer [0, 0], exactly the model's pin.
  `dual_coef_data` (unread by the row-pointer, present in the assembly) is a
  length-`width*n_rows` array of non-zero floats, the shape the fitting
  backend hands the assembly.

INPUT DOMAIN (the model's Requires): width >= 0, n_rows >= 1. Boundary grid
(width in {0,1,2,3,5,17,100,1000} x n_rows in {1,2,3,7,50}, plus single-row /
single-column extremes) + 100000 fuzz draws. Pinned fuzz seed: 148940
(recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + scipy/sklearn (the repo under test and
its hard dependency) only.
"""
import ast
import inspect
import random
import sys

import numpy as np
import scipy.sparse as sp

SEED = 148940
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def range_step(start, stop, step):
    """@ContractOnly callee: realized by the REAL repo callee it models
    (numpy.arange of the evaluation image), per mapping.md section 3.1."""
    return [int(v) for v in np.arange(start, stop, step)]


def row_pointer_for_block_layout(width, n_rows):
    size = width * n_rows
    if width == 0:
        # Empty per-row width: the layout stores nothing (a valid empty layout).
        return [0, 0]
    else:
        step = width
        indptr = range_step(0, size + 1, step)
        return indptr


# --- oracle: the real patched assembly tail, extracted from the module AST ---

class _SelfProxy(object):
    """Carrier for the attributes the assembly tail reads/writes off self."""
    def __init__(self, support_vectors_):
        self.support_vectors_ = support_vectors_


def extract_real_assembly():
    """Locate, in the PATCHED sklearn.svm.base source, the statement tail of
    `BaseLibSVM._sparse_fit` beginning at the support-vector-count assignment
    (the dual-coefficient CSR assembly the model covers, mapping.md section 1)
    and compile those REAL statements for direct execution."""
    import sklearn.svm.base as svm_base
    src = inspect.getsource(svm_base)
    tree = ast.parse(src)
    func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "BaseLibSVM":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_sparse_fit":
                    func = item
    if func is None:
        raise RuntimeError("could not locate BaseLibSVM._sparse_fit in the "
                           "patched module source")
    start = None
    for i, stmt in enumerate(func.body):
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "n_SV"):
            start = i
            break
    if start is None:
        raise RuntimeError("could not locate the support-vector-count "
                           "assignment opening the assembly tail")
    # Version-agnostic Module construction: reuse an empty parsed module so
    # the node carries whatever fields this interpreter's compile() expects.
    mod = ast.parse("")
    mod.body = func.body[start:]
    return compile(mod, "<real _sparse_fit assembly tail>", "exec")


def real_row_pointer(code, width, n_rows):
    """Execute the real patched assembly over one (width, n_rows) binding and
    return the observables of the CSR object it builds:
    (row-pointer as ints, stored-entry count, row count)."""
    size = width * n_rows
    ns = {
        "self": _SelfProxy(sp.csr_matrix((width, 3))),  # only shape[0] is read
        "n_class": n_rows,
        "dual_coef_data": np.arange(1.0, size + 1.0),   # non-zero floats
        "np": np,
        "sp": sp,
    }
    exec(code, ns)
    m = ns["self"].dual_coef_
    return ([int(v) for v in m.indptr], int(m.data.size), int(m.shape[0]))


# --- per-case diff ------------------------------------------------------------

def check_one(code, width, n_rows):
    """Shadow vs oracle on one input; return an error string on disagreement,
    else None."""
    shadow = row_pointer_for_block_layout(width, n_rows)
    oracle_indptr, oracle_stored, oracle_rows = real_row_pointer(
        code, width, n_rows)
    if shadow != oracle_indptr:
        return ("row-pointer mismatch: (width,n_rows)=(%d,%d) shadow=%r "
                "oracle=%r" % (width, n_rows, shadow, oracle_indptr))
    if shadow[-1] != oracle_stored:
        return ("stored-entry-count mismatch: (width,n_rows)=(%d,%d) "
                "shadow final entry=%d oracle data.size=%d"
                % (width, n_rows, shadow[-1], oracle_stored))
    if len(shadow) - 1 != oracle_rows:
        return ("row-count mismatch: (width,n_rows)=(%d,%d) shadow rows=%d "
                "oracle shape[0]=%d"
                % (width, n_rows, len(shadow) - 1, oracle_rows))
    return None


# --- end-to-end grounding: the full patched fit builds the same object --------

def ground_via_full_fit():
    """Drive the FULL patched `_sparse_fit` through real sparse `.fit` calls
    and diff the resulting `dual_coef_` against the shadow on the observed
    (width, n_rows). Returns a list of error strings (empty iff agreement) and
    the number of fits exercised."""
    from sklearn.svm import SVR, SVC

    errors = []
    fitted = []

    # (a) regression, optimum keeps NO support vectors: every target equals
    # the flat prediction within the default tube, so the kept set is empty —
    # the zero-width regime.
    X_flat = sp.csr_matrix(np.array([[0., 1., 0., 0.],
                                     [0., 0., 0., 1.],
                                     [0., 0., 1., 0.],
                                     [1., 0., 0., 1.]]))
    y_flat = np.zeros(4)
    m = SVR(kernel="linear")
    m.fit(X_flat, y_flat)
    fitted.append(("regression/no-kept-vectors", m))
    if m.support_vectors_.shape[0] != 0:
        errors.append("grounding setup: flat-target regression unexpectedly "
                      "kept %d support vectors" % m.support_vectors_.shape[0])

    # (b) regression with spread-out targets: some vectors kept (width >= 1,
    # a single coefficient row).
    rng = np.random.RandomState(SEED % (2 ** 31))
    X_reg = sp.csr_matrix(rng.rand(24, 5))
    y_reg = rng.rand(24) * 10.0
    m2 = SVR(kernel="linear")
    m2.fit(X_reg, y_reg)
    fitted.append(("regression/kept-vectors", m2))

    # (c) 3-class classification: several coefficient rows.
    X_clf = sp.csr_matrix(np.vstack([rng.rand(10, 4) + off
                                     for off in (0.0, 3.0, 6.0)]))
    y_clf = np.repeat([0, 1, 2], 10)
    m3 = SVC(kernel="linear")
    m3.fit(X_clf, y_clf)
    fitted.append(("classification/3-class", m3))

    for label, model in fitted:
        width = int(model.support_vectors_.shape[0])
        if hasattr(model, "classes_"):
            n_rows = len(model.classes_) - 1
        else:
            n_rows = 1
        shadow = row_pointer_for_block_layout(width, n_rows)
        dc = model.dual_coef_
        real_indptr = [int(v) for v in dc.indptr]
        if shadow != real_indptr:
            errors.append("full-fit row-pointer mismatch [%s]: (width,n_rows)="
                          "(%d,%d) shadow=%r real=%r"
                          % (label, width, n_rows, shadow, real_indptr))
        if shadow[-1] != int(dc.data.size):
            errors.append("full-fit stored-count mismatch [%s]: shadow final "
                          "entry=%d real data.size=%d"
                          % (label, shadow[-1], int(dc.data.size)))
        if len(shadow) - 1 != int(dc.shape[0]):
            errors.append("full-fit row-count mismatch [%s]: shadow rows=%d "
                          "real shape[0]=%d"
                          % (label, len(shadow) - 1, int(dc.shape[0])))
    return errors, len(fitted)


def main():
    code = extract_real_assembly()

    # --- boundary grid over the Requires-satisfying domain -------------------
    cases = []
    for width in [0, 1, 2, 3, 5, 17, 100, 1000]:
        for n_rows in [1, 2, 3, 7, 50]:
            cases.append((width, n_rows))
    cases += [(0, 1), (0, 1000), (1, 1), (9999, 1), (1, 999)]

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        width = rng.randint(0, 60)          # zero-width mass included
        n_rows = rng.randint(1, 12)
        cases.append((width, n_rows))

    disagreements = []
    for width, n_rows in cases:
        err = check_one(code, width, n_rows)
        if err is not None:
            disagreements.append(err)
            if len(disagreements) >= 5:
                break

    ground_errors, n_fits = ground_via_full_fit()
    disagreements += ground_errors

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s):" % len(disagreements))
        for e in disagreements:
            print("  " + e)
        return 1
    print("G-CONF OK: shadow of row_pointer_for_block_layout agrees with the "
          "real patched assembly on %d inputs (seed=%d) and with %d full "
          "patched fits, 0 disagreements." % (len(cases), SEED, n_fits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
