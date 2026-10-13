"""Twin-artifact model for scikit-learn__scikit-learn-10297.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validated ridge classifier exposes an optional flag requesting that
  the per-alpha cross-validation values be retained after fitting. Two things
  must hold:

    (1) The flag supplied when the classifier is configured is honoured: the
        retention setting the caller requested is the retention setting used
        when fitting.

    (2) When retention is requested, the classifier produces a
        three-dimensional record of cross-validation values whose axes are, in
        order, the number of samples, the number of targets (n_targets >= 1),
        and the number of candidate penalty strengths. It is never the
        flattened two-dimensional (samples, penalties) form.

The configuration the classifier hands to its engine is modelled as a small
object carrying only the touched field (the retention flag). The retained
record is modelled as a small object carrying its axis count and the three
axis lengths.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class EngineConfig:
    """The configuration handed to the underlying cross-validation engine.
    Only the touched field is modelled: whether the per-alpha values are
    retained."""

    def __init__(self, retain_values: bool) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.retain_values))  # type: ignore
        Ensures(self.retain_values == retain_values)  # type: ignore
        # post-conditions-end
        # impl-start
        self.retain_values = retain_values  # type: bool
        # impl-end


class CvRecord:
    """The retained cross-validation values record. Modelled by its axis count
    and the three axis lengths (samples, targets, penalties)."""

    def __init__(self, rank: int, n_samples: int, n_targets: int,
                 n_alphas: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
                and Acc(self.n_targets) and Acc(self.n_alphas))  # type: ignore
        Ensures(self.rank == rank)  # type: ignore
        Ensures(self.n_samples == n_samples)  # type: ignore
        Ensures(self.n_targets == n_targets)  # type: ignore
        Ensures(self.n_alphas == n_alphas)  # type: ignore
        # post-conditions-end
        # impl-start
        self.rank = rank            # type: int
        self.n_samples = n_samples  # type: int
        self.n_targets = n_targets  # type: int
        self.n_alphas = n_alphas    # type: int
        # impl-end


# axioms-start
# (no unchanged-callee axioms are required for this behaviour)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(12))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().retain_values))
    # (1) The retention flag the caller requested is forwarded unchanged to the
    # engine configuration: the engine retains values iff the caller asked it to.
    Ensures(Result().retain_values == store_cv_values)
    # post-conditions-end
    # impl-start
    cfg = EngineConfig(False)
    return cfg
    # impl-end


def stored_cv_values(cfg: EngineConfig, n_samples: int, n_targets: int,
                     n_alphas: int) -> Optional[CvRecord]:
    # pre-conditions-start
    Requires(Acc(cfg.retain_values, 1 / 2))
    Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(cfg.retain_values, 1 / 2))
    # A record is retained exactly when the engine is configured to retain.
    Ensures((Result() is not None) == cfg.retain_values)
    # (2) When retained, the record is three-dimensional with axes
    # (samples, targets, penalties) -- the target axis is always present.
    Ensures(Implies(Result() is not None,
                    Acc(Result().rank) and Acc(Result().n_samples)
                    and Acc(Result().n_targets) and Acc(Result().n_alphas)))
    Ensures(Implies(Result() is not None, Result().rank == 3))
    Ensures(Implies(Result() is not None, Result().n_samples == n_samples))
    Ensures(Implies(Result() is not None, Result().n_targets == n_targets))
    Ensures(Implies(Result() is not None, Result().n_alphas == n_alphas))
    # post-conditions-end
    # impl-start
    if cfg.retain_values:
        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
        return record
    return None
    # impl-end
