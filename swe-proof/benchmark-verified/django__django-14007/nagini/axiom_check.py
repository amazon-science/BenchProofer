#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14007.

This bundle has ONE @ContractOnly axiom and ONE deep-model reference.

  (1) The axiom `step(converter_id, value)` (model.py axioms region) models a
      single value converter (an unchanged callee of the value-conversion
      pipeline). Its contract is `Ensures(True)` -- the WEAKEST possible: it
      asserts NOTHING about the converter's output (in particular it does NOT
      assume the converter is the identity). Any real, total converter trivially
      satisfies `Ensures(True)`. We confirm soundness in the only way a
      no-claim contract can be unsound -- by the callee failing to return a
      value (raising) -- is irrelevant here because the model never relies on a
      return value's properties; we nonetheless exercise representative real
      converters (including a field's `from_db_value` wrapper) to show they
      return a value, i.e. meet `Ensures(True)`.

  (2) The deep model `execute_returning` / `apply_row` / `fold_chain`
      (model.py) reproduces the semantics of the REAL unchanged callee
      `django.db.models.sql.compiler.SQLCompiler.apply_converters`: for each
      returned row, at each column position, the observed value is the LEFT
      FOLD of that column's converter chain over the raw value, applied
      independently per row/column, with an empty chain acting as the identity.
      This is the A-reference: G-AX validates `execute_returning == the real
      apply_converters` on boundary + randomized fuzz.

We exercise the REAL `apply_converters` source. We import it from Django if
importable in-container; otherwise we fall back to the verbatim algorithm
(reproduced below from compiler.py @ base_commit 619f26d2 -- a self-contained
nested left-fold) so the check is robust and stdlib-only. Either way the model
is validated against the real fold semantics. Exit 0 iff every observation
matches the model.
"""
import random
import sys


# --- the deep model, reproduced exactly from model.py (lock-step) ------------

def fold_chain(chain, value):
    """model.py `fold_chain`: left-fold the column's converter chain over the
    raw value; empty chain is the identity. `chain` is a list of converter
    callables (the model abstracts a converter id; here we apply the callables
    directly so we compare against the real per-converter fold)."""
    v = value
    for conv in chain:
        v = conv(v)
    return v


def execute_returning_model(rows, chains):
    """model.py `execute_returning` / `apply_row`: row count and width preserved;
    each column value is `fold_chain(chains[p], rows[j][p])`. `chains[p]` is the
    converter chain for column p (empty list = identity)."""
    out = []
    for row in rows:
        out.append([fold_chain(chains[p], row[p]) for p in range(len(row))])
    return out


# --- the REAL callee: apply_converters --------------------------------------

def _apply_converters_verbatim(rows, converters):
    """Verbatim transcription of
    django.db.models.sql.compiler.SQLCompiler.apply_converters
    @ base_commit 619f26d2 (connection/expression args are opaque pass-throughs
    here; our converters ignore them, matching the per-value fold the model
    pins). `converters` is a dict pos -> (convs, expression)."""
    connection = None
    converters = list(converters.items())
    for row in map(list, rows):
        for pos, (convs, expression) in converters:
            value = row[pos]
            for converter in convs:
                value = converter(value, expression, connection)
            row[pos] = value
        yield row


def get_real_apply_converters():
    """Return a callable apply_converters(rows, converters) -> iterator. Prefer
    the REAL Django method; fall back to the verbatim transcription."""
    try:
        from django.db.models.sql.compiler import SQLCompiler

        def real(rows, converters):
            # apply_converters is an unbound method that only uses
            # self.connection; bind a tiny stand-in exposing connection=None.
            class _Stub:
                connection = None
            return SQLCompiler.apply_converters(_Stub(), rows, converters)
        # smoke-test it works under the stub (no DB needed)
        list(real([[1]], {0: ([lambda v, e, c: v], None)}))
        return real, "django.db.models.sql.compiler.SQLCompiler.apply_converters"
    except Exception:
        return _apply_converters_verbatim, "verbatim transcription (compiler.py)"


# --- the soundness check -----------------------------------------------------

def check_one(rows, chains, real_apply):
    """Assert model == real for one (rows, chains). `chains[p]` is a list of
    1-arg converters; the real callee takes 3-arg converters, so wrap."""
    # model
    model_out = execute_returning_model(rows, chains)
    # real: build the `converters` dict exactly as get_converters would --
    # only positions with a non-empty chain appear (mirrors `if ... converters`)
    converters = {}
    for p, chain in enumerate(chains):
        if chain:
            wrapped = [(lambda f: (lambda value, expression, connection: f(value)))(f)
                       for f in chain]
            converters[p] = (wrapped, ("expr", p))
    real_out = [list(r) for r in real_apply([list(r) for r in rows], converters)]
    assert real_out == model_out, (
        "deep model disagrees with real apply_converters\n rows=%r\n "
        "chains(as ids)=%r\n real=%r\n model=%r"
        % (rows, [[id(f) for f in c] for c in chains], real_out, model_out))


def main():
    real_apply, provenance = get_real_apply_converters()

    # representative real converters (1-arg model view):
    #   identity (empty-chain stand-in is handled by an empty list)
    #   a from_db_value-style wrapper: int -> a wrapper carrying the int
    #   a scaling/composition converter; a string-coercing converter
    class Wrapper:
        __slots__ = ("v",)
        def __init__(self, v): self.v = v
        def __eq__(self, o): return isinstance(o, Wrapper) and o.v == self.v
        def __hash__(self): return hash(("W", self.v))
        def __repr__(self): return "Wrapper(%r)" % (self.v,)

    def _unwrap(v):
        while isinstance(v, Wrapper):
            v = v.v
        return v

    wrap = lambda v: Wrapper(_unwrap(v))    # the from_db_value hook in the issue
    add1 = lambda v: _unwrap(v) + 1
    times2 = lambda v: _unwrap(v) * 2
    to_neg = lambda v: -_unwrap(v)

    converter_pool = [wrap, add1, times2, to_neg]

    checked = 0

    # --- boundary cases ------------------------------------------------------
    # 0 rows, 1 col, empty chain (identity passthrough)
    check_one([], [[]], real_apply); checked += 1
    # the issue's create case: 1 row, 1 col, single from_db_value wrapper
    check_one([[2]], [[wrap]], real_apply); checked += 1
    # bulk_create case: several rows, single returning column, wrapper
    check_one([[1], [2], [3]], [[wrap]], real_apply); checked += 1
    # empty chain => identity (the no-converter column passes raw value through)
    check_one([[7], [8]], [[]], real_apply); checked += 1
    # multi-column: one converted column, one identity column
    check_one([[5, 9], [6, 10]], [[wrap], []], real_apply); checked += 1
    # multi-step chain: order matters (left fold)
    check_one([[3]], [[add1, times2]], real_apply); checked += 1      # (3+1)*2=8
    check_one([[3]], [[times2, add1]], real_apply); checked += 1      # 3*2+1=7
    # several columns each with their own chain
    check_one([[1, 2, 3]], [[wrap], [add1, add1], [to_neg]], real_apply); checked += 1
    # zero columns
    check_one([[], []], [], real_apply); checked += 1

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(14007)
    for _ in range(20000):
        ncols = rng.randint(0, 4)
        nrows = rng.randint(0, 4)
        rows = [[rng.randint(-50, 50) for _ in range(ncols)] for _ in range(nrows)]
        chains = []
        for _ in range(ncols):
            clen = rng.randint(0, 3)               # empty chains common
            chains.append([rng.choice(converter_pool) for _ in range(clen)])
        check_one(rows, chains, real_apply)
        checked += 1

    print("G-AX OK: deep model execute_returning/apply_row/fold_chain == real "
          "apply_converters [%s] on %d boundary + fuzz cases; "
          "step axiom Ensures(True) trivially met by all exercised converters."
          % (provenance, checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
