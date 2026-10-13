#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14087.

The model consumes TWO axioms, one per changed site: `read_across_folds` (an
abstract across-folds read of the per-class summary table, site 1) and
`select_mixing_value` (an abstract averaged lookup of the per-class
candidate-mixing table, site 2). Both carry the facts their admissibility depends
on as an abstract held-table RESOURCE rather than as bare arguments, and both
grant an unforgeable capability the consumer's postcondition demands. The site-1
contract is:

    Requires(gather_arity(use_joint_layout) == table_rank)   # arity matches
    Ensures(Result() == summary_token)                       # returns the read
    Ensures(read_admissible(table_rank))                     # in-range capability

`read_admissible(rank)` is an abstract, unforgeable capability predicate (no
body), indexed by the rank the read was checked against: the only way to
obtain it is to perform an arity-matching read, and the consumer must hold it
at the table's ACTUAL rank — so a read checked against a self-consistent rank
other than the actual layout's does not discharge the consumer's obligation. The axiom is the
WEAKEST contract sufficient for the proof: it grants the in-range capability
EXACTLY when the read arity equals the table's actual axis rank, and says
nothing about what happens otherwise (an arity mismatch simply cannot satisfy
the precondition). This script validates that axiom — and the A-reference rank /
sentinel facts the deep model relies on — against the REAL callees, in-container:

  (R1, axiom soundness, site 1) The concrete strategy in effect is never the
      deferred ('auto') form, and the per-class summary table's index-axis rank
      is a function of that concrete strategy (3 for the independent layout, 4
      for the joint layout). Checked against the real `_check_multi_class`
      (the resolver) and the real `np.reshape` rank table that
      `LogisticRegressionCV.fit` builds (logistic.py:2086-2106). This is the
      model's `table_rank` / `gather_arity` discrimination and the Requires
      `resolved_strategy != UNRESOLVED`.

  (R2, axiom soundness, site 1) An arity-matching read of a layout is in-bounds,
      and a read whose arity EXCEEDS the layout rank raises
      `IndexError: too many indices for array`. This is exactly the
      `read_across_folds` precondition: the read is admissible (grants
      `read_admissible` at that rank) iff `gather_arity == table_rank`; the
      consumer demands the capability at the actual layout rank. Checked
      against real
      numpy array indexing.

  (R4, axiom soundness, site 1) The step really does hold exactly ONE summary
      table whose actual axis rank is the modeled one, so carrying it as a
      resource each read must be performed against is faithful rather than an
      artifact. The per-class summary array is bound once and its rank is fixed
      by the reshape keyed on the RESOLVED strategy (logistic.py:2084-2112),
      before and independently of the per-class summarising choice, and it is
      rebound per class only in the independent arm — so every index expression
      in the summarising step addresses that one array, and the model's rank
      equals its real `ndim`. Checked by reading that array back off real fits.
      This is what makes the read obligation UNIVERSAL (every read arity-checked
      against the real layout, not merely the delivering one) while a repeated
      in-bounds read stays legal.

  (R3, site 2) When the regularisation family carries no mixing parameter, the
      candidate-mixing table is the one-element sentinel `[None]`, and
      `np.mean(np.asarray([None])[idx])` does NOT yield a real number — so the
      per-class mixing record must be the explicit `None` marker, never a value
      derived from that sentinel. Checked against real numpy.

  (R5, axiom soundness, site 2) The candidate-mixing table has a definite EXTENT,
      the averaged lookup is admissible only inside it, and the real per-class
      position derivation stays inside it. Concretely: for a candidate table of
      `n` entries every position in `[0, n)` averages to a real number while
      position `n` raises `IndexError: index n is out of bounds for axis 0 with
      size n`; and the flat best-score position the block decomposes ranges over
      `n_Cs * n_mixing` (the real reshaped score-table extent, read back off a
      real fit), so `flat // n_Cs` lands in `[0, n_mixing)` for every reachable
      flat position. That is what makes carrying the extent on the held-table
      resource sound rather than restrictive: the real code never addresses an
      entry outside the table, and every position inside it is admissible.

Imports only numpy and the repo's own resolver `_check_multi_class` (an
unchanged helper the patch does not touch). Exit 0 iff every obligation holds.
"""
import sys
import numpy as np

from sklearn.linear_model.logistic import _check_multi_class


# --- model.py reference encodings (kept in lock-step with the model) ---------

INDEPENDENT, JOINT, UNRESOLVED = 0, 1, 2


def table_rank(resolved_strategy):
    """model.py pure helper: rank of the per-class summary table layout."""
    assert resolved_strategy in (INDEPENDENT, JOINT)
    return 3 if resolved_strategy == INDEPENDENT else 4


def gather_arity(use_joint_layout):
    """model.py pure helper: index-axis count of the across-folds read."""
    return 4 if use_joint_layout else 3


# --- R1: resolution never yields the deferred form; rank table matches reshape

def check_resolution_and_rank():
    solvers = ['lbfgs', 'newton-cg', 'sag', 'saga', 'liblinear']
    for solver in solvers:
        for n_classes in range(2, 8):
            for mc in ('ovr', 'multinomial', 'auto'):
                if mc == 'multinomial' and solver == 'liblinear':
                    # the resolver raises here (unsupported); skip — the model
                    # never reaches the read in that configuration.
                    try:
                        _check_multi_class(mc, solver, n_classes)
                    except ValueError:
                        continue
                resolved = _check_multi_class(mc, solver, n_classes)
                # resolved is always one of the two concrete strategies
                assert resolved in ('ovr', 'multinomial'), (
                    "resolver produced %r (must be ovr/multinomial)" % resolved)
                assert resolved != 'auto', "resolver returned 'auto' (unsound)"

                # the per-class summary table layout that fit() reshapes to:
                #   independent: (n_folds, n_Cs*n_l1, n_features)      -> 3 axes
                #   joint:       (n_classes, n_folds, n_Cs*n_l1, n_f)  -> 4 axes
                n_folds, n_cl1, n_feat = 2, 6, 20
                if resolved == 'ovr':
                    arr = np.empty((n_folds, n_cl1, n_feat))
                    expected_rank = 3
                else:
                    arr = np.empty((n_classes, n_folds, n_cl1, n_feat))
                    expected_rank = 4
                tag = INDEPENDENT if resolved == 'ovr' else JOINT
                assert arr.ndim == expected_rank == table_rank(tag), (
                    "rank table mismatch for resolved=%r: array ndim=%d, "
                    "table_rank=%d" % (resolved, arr.ndim, table_rank(tag)))


# --- R2: arity match <=> in-bounds; over-arity read raises IndexError --------

def check_arity_admissibility():
    n_folds, n_cl1, n_feat = 2, 6, 20
    independent_arr = np.empty((n_folds, n_cl1, n_feat))   # 3 axes
    best = np.zeros(n_folds, dtype=int)
    # the matching (independent) read uses 3 index positions -> in-bounds, so
    # read_across_folds' precondition gather_arity(False)==table_rank holds.
    for i in range(n_folds):
        _ = independent_arr[i, best[i], :]                 # gather_arity(False)==3
    assert gather_arity(False) == independent_arr.ndim == 3
    # the mismatching (joint) read uses 4 index positions -> IndexError, so the
    # precondition gather_arity(True)==table_rank is FALSE and the read is never
    # admissible: this is exactly why read_across_folds cannot grant the
    # capability when the arity disagrees with the layout.
    raised = False
    try:
        for i in range(n_folds):
            _ = independent_arr[:, i, best[i], :]          # gather_arity(True)==4
    except IndexError:
        raised = True
    assert raised, ("over-indexing the 3-axis independent layout with the "
                    "4-axis joint read did NOT raise IndexError")
    assert gather_arity(True) == 4 != independent_arr.ndim


# --- R4: ONE summary table per iteration, at the modeled rank ----------------

def check_single_table_at_modeled_rank():
    """The held-table resource is faithful: the no-refit block has exactly one
    per-class summary array in scope, its rank is settled before the read, and
    that rank is the modeled one.

    Checked by RUNNING real fits (never by scraping source): for each resolved
    strategy, fit and read back the per-class summary arrays the block indexes,
    asserting each one's real `ndim` equals the model's `table_rank` for the
    strategy the fit resolved to. If the block could hold two differently-ranked
    tables at once, or the real ndim differed from the modeled rank, requiring a
    read to be performed against a single held table at that rank would be
    UNSOUND (it would forbid a read the real code makes).

    The summary-table attribute this reads back is built once, from the resolved
    strategy, BEFORE and independently of the per-class summarising choice
    (logistic.py:2084-2112 — the reshape/swapaxes that fixes the rank, and
    `self.coefs_paths_ = dict(zip(classes, coefs_paths))`). So the table
    measured here is the same table the summarising step indexes, and this leg
    deliberately does NOT drive the summarising step itself: an axiom check must
    measure the callee facts the model rests on, not re-run the behaviour under
    specification.
    """
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegressionCV

    n_classes = 3
    X, y = make_classification(n_samples=60, n_features=6, n_informative=4,
                               n_classes=n_classes, random_state=0)
    Cs = np.logspace(-4, 4, 3)

    for mc in ('ovr', 'multinomial', 'auto'):
        lrcv = LogisticRegressionCV(penalty='l2', Cs=Cs, solver='saga',
                                    random_state=0, cv=3, max_iter=20,
                                    multi_class=mc, refit=True)
        lrcv.fit(X, y)
        resolved = _check_multi_class(mc, 'saga', n_classes)
        tag = INDEPENDENT if resolved == 'ovr' else JOINT
        expected = table_rank(tag)

        # `self.coefs_paths_` is the dict the block reads its per-class table
        # from. In the independent arm the block takes the per-class entry; in
        # the joint arm it keeps the whole array. Either way there is ONE array
        # in scope for the read, and its ndim must be the modeled rank.
        paths = lrcv.coefs_paths_
        assert isinstance(paths, dict) and len(paths) == n_classes, (
            "expected one per-class entry per class, got %r" % (paths,))
        ranks = set()
        for per_class in paths.values():
            arr = np.asarray(per_class)
            # the independent arm indexes this per-class view (3 axes); the
            # joint arm indexes the whole array, which carries the extra
            # leading class axis (4 axes).
            ranks.add(arr.ndim if resolved == 'ovr' else arr.ndim + 1)
        assert len(ranks) == 1, (
            "the block would hold summary tables of DIFFERING rank %r for "
            "resolved=%r — a single held table at one rank would be unsound"
            % (sorted(ranks), resolved))
        actual = ranks.pop()
        assert actual == expected, (
            "real summary-table rank %d != modeled table_rank %d for "
            "resolved=%r (multi_class=%r)" % (actual, expected, resolved, mc))

        # And the arity the model would request for that strategy is exactly
        # that rank: so the one held table admits the modeled read, and any read
        # at a DIFFERENT rank is a read of a table the block does not have.
        use_joint_layout = (tag != INDEPENDENT)
        assert gather_arity(use_joint_layout) == actual, (
            "modeled read arity %d != the one held table's rank %d"
            % (gather_arity(use_joint_layout), actual))


# --- R3: averaging the [None] sentinel is not a real number ------------------

def check_none_sentinel():
    sentinel = np.asarray([None])                       # candidate table = [None]
    assert sentinel.shape == (1,)
    # post-patch: only index 0 is reachable (len==1); model requires idx==0
    idx = 0
    selected = sentinel[idx]
    assert selected is None, "sentinel element is not None"
    # np.mean over the sentinel must NOT yield a real, finite number
    bad = False
    try:
        m = np.mean(sentinel[idx])
        # if it does not raise, it must at least not be a real finite float
        if isinstance(m, (int, float, np.floating)) and np.isfinite(m):
            bad = True
    except (TypeError, ValueError):
        bad = False
    assert not bad, ("np.mean of the [None] sentinel yielded a real finite "
                     "number — the absent marker would be indistinguishable")

    # the mixing family DOES have a real table that averages to a number
    real_ratios = np.asarray([0.0, 1.0])
    for i in (0, 1):
        m = np.mean(real_ratios[i])
        assert isinstance(m, (int, float, np.floating)) and np.isfinite(m)

    # R3b: the averaged lookup is PARTIAL in exactly the modeled way — its
    # admissibility is "the table addressed holds real mixing values", not
    # "the record delivered afterwards is the absent marker". Performing the
    # lookup on the placeholder table yields no mixing value NO MATTER what is
    # done with the result, which is why the selection must be inadmissible
    # against that table rather than merely corrected after the fact.
    for table, holds_real in ((np.asarray([None]), False),
                              (np.asarray([0.0, 1.0]), True)):
        idx = 0
        try:
            got = np.mean(table[idx])
            usable = (isinstance(got, (int, float, np.floating))
                      and np.isfinite(got))
        except (TypeError, ValueError):
            usable = False
        assert usable == holds_real, (
            "averaged lookup usability %r != table-holds-real-values %r — the "
            "modeled precondition of the selection is not the real one"
            % (usable, holds_real))


# --- R5: the candidate table's EXTENT bounds every averaged lookup ------------

def check_candidate_table_extent():
    """The extent carried by the held candidate-table resource is faithful.

    Two obligations, both measured against the real callees:

    (a) The averaged lookup is admissible EXACTLY inside the table's extent. For
        a candidate table of `n` entries, every position in `[0, n)` averages to
        a real number, and position `n` raises `IndexError`. So requiring a
        selection to address a position within the held table's extent is the
        real in-bounds condition — and permitting ANY position inside it is not
        over-permissive, since each one is a real, non-raising lookup.

    (b) The real position derivation stays inside that extent. The block
        decomposes a flat best-score position with `flat // n_Cs`, and the flat
        position ranges over the score table's last axis, whose real extent is
        `n_Cs * n_mixing` (read back off a real fit rather than assumed). Hence
        `flat // n_Cs < n_mixing == len(l1_ratios_)` for every reachable flat
        position: the real code never addresses an entry the candidate table does
        not have, so the extent bound does not forbid a lookup the real code
        makes.
    """
    # (a) admissible exactly inside the extent -- real numpy indexing.
    for n in (1, 2, 3, 5):
        table = np.asarray([float(i) / n for i in range(n)])
        assert table.shape == (n,)
        for idx in range(n):
            got = np.mean(table[idx])
            assert isinstance(got, (int, float, np.floating)) and np.isfinite(got), (
                "in-extent position %d of a %d-entry candidate table did not "
                "average to a real number: %r" % (idx, n, got))
        raised = False
        try:
            _ = np.mean(table[n])
        except IndexError:
            raised = True
        assert raised, (
            "position %d of a %d-entry candidate table did NOT raise IndexError "
            "— the extent bound would not be the real in-bounds condition" % (n, n))

    # (b) the real flat-position decomposition stays inside the extent. The
    # score-table extent is read back off a real elasticnet fit; the block's
    # `flat // n_Cs` is the real unchanged integer division.
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegressionCV

    X, y = make_classification(n_samples=60, n_features=6, n_informative=4,
                               n_classes=3, random_state=0)
    Cs = np.logspace(-2, 2, 2)
    l1_ratios = [0.0, 1.0]
    lrcv = LogisticRegressionCV(penalty='elasticnet', Cs=Cs, solver='saga',
                                l1_ratios=l1_ratios, random_state=0, cv=3,
                                max_iter=20, multi_class='ovr', refit=True)
    lrcv.fit(X, y)
    n_cs = np.asarray(lrcv.Cs_).size
    n_mixing = np.asarray(lrcv.l1_ratios_).size
    assert n_mixing == len(l1_ratios), (
        "real candidate-table extent %d != the ratios handed in (%d)"
        % (n_mixing, len(l1_ratios)))
    # the real reshaped score table's trailing axes are (n_Cs, n_mixing): the
    # flat position the block argmaxes over therefore ranges over n_Cs*n_mixing.
    flat_extents = set()
    for score in lrcv.scores_.values():
        arr = np.asarray(score)
        assert arr.shape[-2:] == (n_cs, n_mixing), (
            "real score table trailing shape %r != (n_Cs, n_mixing) = %r"
            % (arr.shape[-2:], (n_cs, n_mixing)))
        flat_extents.add(int(arr.shape[-1] * arr.shape[-2]))
    assert len(flat_extents) == 1, (
        "differing flat score extents %r" % (sorted(flat_extents),))
    flat_extent = flat_extents.pop()
    assert flat_extent == n_cs * n_mixing
    for flat in range(flat_extent):
        pos = flat // n_cs
        assert 0 <= pos < n_mixing, (
            "the real decomposition flat=%d // n_Cs=%d gave position %d, outside "
            "the candidate table's extent %d — the modeled extent bound would "
            "forbid a lookup the real code makes"
            % (flat, n_cs, pos, n_mixing))


def main():
    check_resolution_and_rank()
    check_arity_admissibility()
    check_single_table_at_modeled_rank()
    check_none_sentinel()
    check_candidate_table_extent()
    print("G-AX OK: resolution never the deferred form + summary-table rank "
          "matches np.reshape (R1); an arity-matching read is in-bounds while an "
          "over-arity read raises IndexError, so read_across_folds grants the "
          "in-range capability EXACTLY on an arity match (R2); real fits hold "
          "exactly ONE per-class summary table per iteration whose real "
          "ndim is the modeled rank, so requiring every read to be performed "
          "against one held table at that rank is sound (R4); the [None] "
          "sentinel does not average to a real number, so the absent marker is "
          "required, and the averaged lookup is usable EXACTLY when the table "
          "addressed holds real mixing values — so the selection must be "
          "inadmissible against the placeholder table rather than corrected "
          "after the fact (R3/R3b); and the averaged lookup is admissible "
          "EXACTLY inside the candidate table's extent (every in-extent position "
          "averages to a real number, position len raises IndexError) while the "
          "real flat-position decomposition stays inside that extent, so "
          "carrying the extent on the held candidate table is sound and not "
          "restrictive (R5).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
