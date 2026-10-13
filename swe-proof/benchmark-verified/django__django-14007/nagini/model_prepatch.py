"""Twin-artifact model for django__django-14007.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row-returning database write hands back the freshly assigned column
  values, those raw values must be run through the per-column value-conversion
  pipeline before they reach the caller -- exactly as every other read path
  already does. Each returned column carries an ordered chain of value
  converters (possibly empty). The value the caller observes at a column is the
  left-fold of that column's converter chain over the raw value:

      observed = c_k(... c_2(c_1(raw)) ...)              for a chain c_1..c_k
      observed = raw                                     for an empty chain

  applied independently to every returned row and every column. A column whose
  chain is empty is therefore the identity (the raw value passes through), and a
  column whose chain is non-empty yields the converted value -- never the raw
  one. The number and shape of the returned rows is preserved exactly.

Rows are modelled as a pure sequence of pure rows, `PSeq[PSeq[int]]` (each row a
`PSeq[int]` of column values). Pure sequences carry no heap permission, so the
specification quantifies over rows and columns directly. A single converter step
is an opaque unchanged callee, `step(converter_id, value)`, axiomatized as a
@Pure @ContractOnly function; the conversion chain `fold_chain` and the row/grid
application are modelled deeply (front-recursive fold + verified loops) and
pinned element-wise by the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def step(converter_id: int, value: int) -> int:
    """One value converter applied to one value (an unchanged callee of the
    conversion pipeline; e.g. a field's stored value-restoration hook). Opaque:
    no relation between input and output is assumed, in particular it is NOT
    assumed to be the identity. Provenance + executable soundness: mapping.md /
    axiom_check.py (G-AX)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def fold_chain(chain: PSeq[int], value: int) -> int:
    """Left-fold one column's converter chain over a raw value (front-recursive
    so a single unfold is available per loop step). An empty chain is the
    identity; otherwise each converter id is applied in order via `step`."""
    if len(chain) == 0:
        return value
    return fold_chain(chain.drop(1), step(chain[0], value))
# pure-end


def apply_row(row: PSeq[int], chains: PSeq[PSeq[int]], ncols: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(ncols >= 0)
    Requires(len(row) == ncols)
    Requires(len(chains) == ncols)
    # pre-conditions-end
    # post-conditions-start
    # The converted row has the same width, and each column holds the fold of
    # that column's converter chain over the raw column value.
    Ensures(len(Result()) == ncols)
    Ensures(Forall(int, lambda p: (Implies(0 <= p and p < ncols,
        Result()[p] == fold_chain(chains[p], row[p])), [[Result()[p]]])))
    # post-conditions-end
    # impl-start
    out = PSeq(0).take(0)  # type: PSeq[int]
    p = 0
    while p < ncols:
        # invariants-start
        Invariant(0 <= p and p <= ncols)
        Invariant(len(row) == ncols)
        Invariant(len(chains) == ncols)
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[int]
        nv = fold_chain(chains[p], row[p])
        out = out + PSeq(nv)
        Assert(out[p] == nv)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == old[k]), [[out[k]]])))
        p = p + 1
    return out
    # impl-end


def execute_returning(rows: PSeq[PSeq[int]], chains: PSeq[PSeq[int]],
                      ncols: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(ncols >= 0)
    # one converter chain per returned column
    Requires(len(chains) == ncols)
    # every raw row has one value per returned column
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(rows[j]) == ncols), [[rows[j]]])))
    # pre-conditions-end
    # post-conditions-start
    # Row count and width are preserved exactly.
    Ensures(len(Result()) == len(rows))
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(Result()[j]) == ncols), [[Result()[j]]])))
    # Every observed value is the converter-chain fold over the raw value:
    # identity for an empty chain, the converted value for a non-empty chain.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        Forall(int, lambda p: (Implies(0 <= p and p < ncols,
            Result()[j][p] == fold_chain(chains[p], rows[j][p])),
            [[Result()[j][p]]]))), [[Result()[j]]])))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: the freshly returned raw rows are handed straight
    # back to the caller WITHOUT running them through the per-column converter
    # chains, so every observed value is the raw value rather than the fold.
    out = rows.take(0)  # type: PSeq[PSeq[int]]
    j = 0
    while j < len(rows):
        # invariants-start
        Invariant(0 <= j and j <= len(rows))
        Invariant(len(chains) == ncols)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
            len(rows[k]) == ncols), [[rows[k]]])))
        Invariant(len(out) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            out[k] == rows[k]), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[PSeq[int]]
        out = out + PSeq(rows[j])
        Assert(out[j] == rows[j])
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
            out[k] == old[k]), [[out[k]]])))
        j = j + 1
    return out
    # impl-end
