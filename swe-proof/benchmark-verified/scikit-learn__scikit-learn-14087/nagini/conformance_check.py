#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14087
(nagini).

SHADOW: the impl regions of model.py's `gather_per_class` and `mixing_record`,
copied verbatim below with the contract calls stripped, plus the @Pure helpers
`table_rank` / `gather_arity` copied as plain functions. The model IS Python:
ints/bools/Optional carry over directly; no PSeq shim is needed. The single
@ContractOnly callee, `read_across_folds`, is realized by the REAL repo
operation it axiomatizes per mapping.md section 1: the across-folds indexed
mean over the per-class coefficient array (`np.mean([...[i, best[i], :] ...],
axis=0)` at index arity 3, or the 4-axis variant), executed on the real numpy
array of the current test case — not a re-implementation.

ORACLE: the REAL patched repo code the model models per mapping.md — the
no-refit summary tail of `LogisticRegressionCV.fit`
(sklearn/linear_model/logistic.py). The gate applies patch.diff to /testbed
before this script runs (this script does NOT apply any patch);
PYTHONPATH=/testbed makes the patched module importable. Because the modeled
behaviour is a statement block inside a fitting method rather than a
standalone function, the oracle executes the REAL statements: the patched
module's AST is parsed, the `else:` body of `fit`'s `if self.refit:` (exactly
the block both modeled sites live in) is compiled and run byte-for-byte over
controlled bindings of the names it reads (`self`, `multi_class`, `scores`,
`coefs_paths`, `folds`, `l1_ratios_`, `np`).

An end-to-end grounding leg additionally drives the FULL patched `fit`
through real `LogisticRegressionCV(refit=False).fit(...)` calls — elasticnet
and l2 penalties crossed with ovr / multinomial / auto multi_class — and
diffs the per-class `l1_ratio_` records against the shadow (via the
recomputed per-class selection from the fitted `scores_`), checks the
attribute shapes, and confirms the auto-resolved multinomial gather completes
(the site-1 observable).

TYPE BRIDGE (mapping.md section 2):
  resolved_strategy <-> the resolved local `multi_class`
      ('ovr' <-> INDEPENDENT=0, 'multinomial' <-> JOINT=1);
  unresolved_form   <-> the attribute `self.multi_class`
      ('ovr'/'multinomial'/'auto' <-> 0/1/UNRESOLVED=2);
  table_axes        <-> `coefs_paths.ndim` (3 for the ovr layout, 4 for the
      multinomial layout; the Requires ties it to the resolved strategy,
      matching the real reshape);
  summary_token     <-> the gathered vector `w`: the shadow's token is
      realized as the real across-folds read on the case's actual array, so
      the shadow-vs-oracle diff compares the full numeric vectors;
  family_has_mixing <-> `self.penalty == 'elasticnet'`;
  candidates_len    <-> `len(l1_ratios_)` (the `[None]` sentinel has length 1
      in the non-elasticnet case, satisfying the Requires). It is the ACTUAL
      extent the held `candidate_table(_, candidates_len)` resource carries,
      so the bridge does not merely pass it: on every case it checks that the
      real ratio table accepts every position the resource admits and REFUSES
      position `candidates_len` (see `_check_extent_boundary`);
  selected_index    <-> a flat best index divided by the C-grid length. Its
      in-range-ness is not assumed: the bridge confirms the real per-fold flat
      decomposition lands inside the real table's extent on every case, which
      is the fact the model's `0 <= selected_index < candidates_len` Requires
      and the resource's extent parameter jointly stand for;
  mixing_value / the Optional None <-> the per-class value appended to
      `self.l1_ratio_`: the real averaged ratio for the mixing family, the
      literal None otherwise. The shadow's mixing_value token is bound to the
      independently recomputed real average, so the diff compares real values.

INPUT DOMAIN (the model's Requires): resolved_strategy in {0,1};
unresolved_form in {0,1,2}; table_axes == table_rank(resolved_strategy);
candidates_len >= 1; 0 <= selected_index < candidates_len;
not family_has_mixing => candidates_len == 1. Boundary grid: all 6
(resolved, unresolved) combos x penalty in {elasticnet, l2} x uniform-fold /
varied-fold selections x minimal dims (1 fold / 1 class / 1 C / 1 ratio) —
plus 100000 fuzz draws over random small dims, scores, and coefficient
arrays. Pinned fuzz seed: 140870 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + sklearn (the repo under test) only.
"""
import ast
import sys

import numpy as np

SEED = 140870
N_FUZZ = 100_000


# --- the pure region of model.py, verbatim (decorators/contracts stripped) ---

INDEPENDENT = 0   # per-class-independent strategy
JOINT = 1         # joint strategy (one extra leading layout axis)
UNRESOLVED = 2    # the deferred "decide later" form (never a concrete value)


def table_rank(resolved_strategy):
    assert resolved_strategy in (INDEPENDENT, JOINT)
    if resolved_strategy == INDEPENDENT:
        return 3
    return 4


def gather_arity(use_joint_layout):
    if use_joint_layout:
        return 4
    return 3


# --- the @ContractOnly callee, realized by the REAL repo operation ------------

# Per-case context: the real per-class coefficient array (whose ndim is the
# case's table_axes) and the per-fold best indices, set by the driver before
# each shadow call.
_CTX = {}


def read_across_folds(use_joint_layout, table_rank_, summary_token):
    """Realized by the REAL operation the axiom models (mapping.md section 1):
    the across-folds indexed mean over the case's actual numpy array, at the
    index arity selected by `use_joint_layout`. The returned real vector is
    the realization of the summary token."""
    arr = _CTX["coefs_paths"]
    best = _CTX["best_indices"]
    n_folds = _CTX["n_folds"]
    assert arr.ndim == table_rank_  # the table the read is checked against
    if use_joint_layout:
        return np.mean([arr[:, i, best[i], :] for i in range(n_folds)],
                       axis=0)
    return np.mean([arr[i, best[i], :] for i in range(n_folds)], axis=0)


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def gather_per_class(resolved_strategy, unresolved_form, table_axes,
                     summary_token):
    # Address the table with the arity determined by the strategy actually in
    # effect, so the index arity always equals the table's axis rank.
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w
    # (impl region verbatim; the token return is realized as the real vector)


def mixing_record(family_has_mixing, selected_index, candidates_len,
                  mixing_value):
    if family_has_mixing:
        # The family carries a mixing parameter: record the selected value.
        entry = mixing_value
    else:
        # No mixing parameter for this family: record the explicit absent
        # marker.
        entry = None
    return entry


# --- oracle: the real patched no-refit tail, extracted from the module AST ---

class _SelfProxy(object):
    """Carrier for the attributes the no-refit tail reads/writes off self."""
    def __init__(self, Cs_, penalty, multi_class_attr):
        self.Cs_ = Cs_
        self.penalty = penalty
        self.multi_class = multi_class_attr
        self.C_ = []
        self.l1_ratio_ = []


def extract_real_tail():
    """Locate, in the PATCHED sklearn/linear_model/logistic.py source, the
    `else:` body of `LogisticRegressionCV.fit`'s `if self.refit:` (the
    no-refit summary block both modeled sites live in, mapping.md section 1)
    and compile those REAL statements for direct execution."""
    import inspect

    import sklearn.linear_model.logistic as lm
    src = inspect.getsource(lm)
    tree = ast.parse(src)
    func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LogisticRegressionCV":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "fit":
                    func = item
    if func is None:
        raise RuntimeError("could not locate LogisticRegressionCV.fit in the "
                           "patched module source")
    tail = None
    for node in ast.walk(func):
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Attribute)
                and isinstance(node.test.value, ast.Name)
                and node.test.value.id == "self"
                and node.test.attr == "refit" and node.orelse):
            tail = node.orelse
    if tail is None:
        raise RuntimeError("could not locate the no-refit else-branch")
    # Version-agnostic Module construction: reuse an empty parsed module so
    # the node carries whatever fields this interpreter's compile() expects.
    mod = ast.parse("")
    mod.body = tail
    return compile(mod, "<real fit no-refit tail>", "exec")


def run_real_tail(code, resolved, unresolved, penalty, scores, coefs_paths,
                  n_folds, Cs_, l1_ratios_):
    """Execute the real patched no-refit statements over one binding and
    return (w, the per-class mixing record appended, or an exception repr)."""
    proxy = _SelfProxy(Cs_, penalty, unresolved)
    ns = {
        "self": proxy,
        "multi_class": resolved,
        "scores": scores,
        "coefs_paths": coefs_paths,
        "folds": list(range(n_folds)),
        "l1_ratios_": l1_ratios_,
        "np": np,
    }
    exec(code, ns)
    return ns["w"], proxy.l1_ratio_[0]


# --- per-case diff ------------------------------------------------------------

STR_OF = {INDEPENDENT: "ovr", JOINT: "multinomial", UNRESOLVED: "auto"}


def _check_extent_boundary(l1_ratios_, best_indices, n_cs, family_has_mixing,
                           candidates_len, selected_index, label):
    """Exercise the two parameters the site-2 shadow body does not read.

    The shadow's OUTPUT is independent of `selected_index` / `candidates_len`
    (the recorded value is the real average, or the absent marker), so a
    shadow-vs-oracle value diff alone would leave both parameters dead. They
    are not output parameters: they are the ADMISSIBILITY parameters that the
    held `candidate_table(family_has_mixing, candidates_len)` resource carries.
    What has to hold of the real callee is therefore a boundary, checked here
    on every case:

      * every position the resource admits (0 <= i < candidates_len) is a
        position the real ratio table ACCEPTS, averaging to a real number;
      * position `candidates_len` is one the real table REFUSES (IndexError) --
        so the extent the resource carries is exactly the real table's, not a
        bound loose enough to permit an out-of-range read;
      * the real per-fold flat decomposition `best_indices // len(Cs_)` lands
        inside that extent, so the model's in-range Requires is a fact about
        the real code and not a restriction imposed on it.

    Returns an error string on disagreement, else None.
    """
    table = np.asarray(l1_ratios_)
    if candidates_len != len(table):
        return ("candidate-extent mismatch [%s]: model carries %d, real table "
                "has %d entries" % (label, candidates_len, len(table)))
    # the real selection positions the block actually forms, all of them
    real_positions = best_indices // n_cs
    for pos in np.atleast_1d(real_positions):
        if not (0 <= int(pos) < candidates_len):
            return ("real flat decomposition leaves the table extent [%s]: "
                    "position %d not in [0, %d)"
                    % (label, int(pos), candidates_len))
    if not (0 <= selected_index < candidates_len):
        return ("selected_index outside the real extent [%s]: %d not in "
                "[0, %d)" % (label, selected_index, candidates_len))
    if family_has_mixing:
        # every admitted position is accepted by the real table
        for pos in range(candidates_len):
            try:
                val = np.mean(table[pos])
            except Exception as e:
                return ("real table REFUSED a position the resource admits "
                        "[%s]: index %d raised %r" % (label, pos, e))
            if not np.isfinite(val):
                return ("real table gave a non-finite value at an admitted "
                        "position [%s]: index %d -> %r" % (label, pos, val))
    else:
        # the placeholder table: one entry, and the only admitted position is 0
        if candidates_len != 1 or selected_index != 0:
            return ("placeholder table not single-entry [%s]: len=%d index=%d"
                    % (label, candidates_len, selected_index))
    # the first position PAST the extent must be refused by the real table
    try:
        table[candidates_len]
    except IndexError:
        pass
    else:
        return ("real table ACCEPTED position %d, one past its extent [%s]: "
                "the extent the resource carries would be unsound"
                % (candidates_len, label))
    return None


def check_one(code, rng, resolved_tag, unresolved_tag, penalty,
              n_classes, n_folds, n_cs, n_l1, n_feat, uniform_best):
    """Build one Requires-satisfying input, run oracle and shadow, return an
    error string on disagreement else None."""
    ncol = n_cs * n_l1
    Cs_ = np.logspace(-2, 2, n_cs)
    if penalty == "elasticnet":
        # an ndarray, exactly as the repo's own callers hand it in
        l1_ratios_ = np.linspace(0.0, 1.0, n_l1) if n_l1 > 1 \
            else np.asarray([float(rng.rand())])
    else:
        l1_ratios_ = [None]
        n_l1 = 1
        ncol = n_cs
    scores = rng.rand(n_folds, ncol)
    if uniform_best:
        # every fold selects the same flat best column
        b = rng.randint(0, ncol)
        scores[:, b] = 2.0
    if resolved_tag == INDEPENDENT:
        coefs_paths = rng.rand(n_folds, ncol, n_feat)
    else:
        coefs_paths = rng.rand(n_classes, n_folds, ncol, n_feat)
    table_axes = coefs_paths.ndim

    resolved = STR_OF[resolved_tag]
    unresolved = STR_OF[unresolved_tag]

    label = ("resolved=%s unresolved=%s penalty=%s dims=(cls=%d,folds=%d,"
             "Cs=%d,l1=%d,feat=%d) uniform=%s"
             % (resolved, unresolved, penalty, n_classes, n_folds, n_cs,
                n_l1, n_feat, uniform_best))

    # oracle: the real patched statements
    try:
        w_oracle, l1_oracle = run_real_tail(
            code, resolved, unresolved, penalty, scores, coefs_paths,
            n_folds, Cs_, l1_ratios_)
    except Exception as e:
        return ("oracle raised on an admissible input [%s]: %r" % (label, e))

    # shadow site 1: gather_per_class over the same real arrays
    best_indices = np.argmax(scores, axis=1)
    _CTX["coefs_paths"] = coefs_paths
    _CTX["best_indices"] = best_indices
    _CTX["n_folds"] = n_folds
    try:
        w_shadow = gather_per_class(resolved_tag, unresolved_tag,
                                    table_axes, None)
    except Exception as e:
        return ("shadow gather raised [%s]: %r" % (label, e))
    if not np.array_equal(w_shadow, w_oracle):
        return ("gather mismatch [%s]: shadow=%r oracle=%r"
                % (label, w_shadow, w_oracle))
    expected_ndim = 1 if table_axes == 3 else 2
    if w_oracle.ndim != expected_ndim:
        return ("gathered-vector rank mismatch [%s]: got ndim=%d expected %d"
                % (label, w_oracle.ndim, expected_ndim))

    # shadow site 2: mixing_record with the token bound to the real average
    family_has_mixing = (penalty == "elasticnet")
    candidates_len = len(l1_ratios_)
    selected_index = int(best_indices[0]) // n_cs
    # the two parameters the shadow body does not read are ADMISSIBILITY
    # parameters of the held candidate table: check them against the real table
    err = _check_extent_boundary(l1_ratios_, best_indices, n_cs,
                                 family_has_mixing, candidates_len,
                                 selected_index, label)
    if err is not None:
        return err
    if family_has_mixing:
        real_value = np.mean(np.asarray(l1_ratios_)[best_indices // n_cs])
    else:
        real_value = None  # token unused on this side of the branch
    entry_shadow = mixing_record(family_has_mixing, selected_index,
                                 candidates_len, real_value)
    if family_has_mixing:
        if entry_shadow is None or l1_oracle is None \
                or entry_shadow != l1_oracle:
            return ("mixing-record mismatch [%s]: shadow=%r oracle=%r"
                    % (label, entry_shadow, l1_oracle))
        if not np.isfinite(l1_oracle):
            return ("mixing family recorded a non-finite value [%s]: %r"
                    % (label, l1_oracle))
    else:
        if entry_shadow is not None or l1_oracle is not None:
            return ("absent-marker mismatch [%s]: shadow=%r oracle=%r"
                    % (label, entry_shadow, l1_oracle))
    return None


# --- end-to-end grounding: the full patched fit builds the same records ------

def ground_via_full_fit():
    """Drive the FULL patched fit through real refit=False calls and diff the
    per-class mixing records against the shadow (recomputed from the fitted
    scores_); check attribute shapes and that the auto-resolved joint gather
    completes. Returns (error list, number of fits)."""
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegressionCV

    errors = []
    n_classes, n_features = 3, 20
    X, y = make_classification(n_samples=120, n_classes=n_classes,
                               n_informative=n_classes,
                               n_features=n_features, random_state=0)
    Cs = np.logspace(-2, 2, 2)
    l1_ratios = np.linspace(0, 1, 2)
    configs = []
    for mc in ("ovr", "multinomial", "auto"):
        configs.append(dict(penalty="elasticnet", solver="saga", Cs=Cs,
                            l1_ratios=l1_ratios, multi_class=mc,
                            random_state=0, refit=False, max_iter=60,
                            cv=3, tol=1e-2))
        configs.append(dict(penalty="l2", solver="saga", Cs=Cs,
                            multi_class=mc, random_state=0, refit=False,
                            max_iter=60, cv=3, tol=1e-2))
    for cfg in configs:
        label = "full-fit multi_class=%s penalty=%s" % (cfg["multi_class"],
                                                        cfg["penalty"])
        model = LogisticRegressionCV(**cfg)
        try:
            model.fit(X, y)
        except Exception as e:
            errors.append("%s: fit raised %r" % (label, e))
            continue
        if model.coef_.shape != (n_classes, n_features):
            errors.append("%s: coef_ shape %r" % (label, model.coef_.shape))
        if model.l1_ratio_.shape != (n_classes,):
            errors.append("%s: l1_ratio_ shape %r"
                          % (label, model.l1_ratio_.shape))
            continue
        mixing = cfg["penalty"] == "elasticnet"
        n_l1 = len(l1_ratios) if mixing else 1
        for k, cls in enumerate(model.classes_):
            sc = np.asarray(model.scores_[cls])
            # after fitting, the per-class score table may have been reshaped
            # to a per-axis layout; flatten back to the per-fold flat columns
            # the summary step selected over
            sc = sc.reshape(sc.shape[0], -1)
            best_indices = np.argmax(sc, axis=1)
            if mixing:
                expected = np.mean(
                    np.asarray(l1_ratios)[best_indices // len(Cs)])
            else:
                expected = None
            shadow_entry = mixing_record(mixing,
                                         int(best_indices[0]) // len(Cs),
                                         n_l1, expected)
            real_entry = model.l1_ratio_[k]
            if mixing:
                if real_entry is None or shadow_entry != real_entry:
                    errors.append("%s class %r: shadow=%r real=%r"
                                  % (label, cls, shadow_entry, real_entry))
            else:
                if real_entry is not None or shadow_entry is not None:
                    errors.append("%s class %r: shadow=%r real=%r (expected "
                                  "the absent marker)"
                                  % (label, cls, shadow_entry, real_entry))
    return errors, len(configs)


def main():
    code = extract_real_tail()
    rng = np.random.RandomState(SEED)

    # --- boundary grid over the Requires-satisfying domain -------------------
    cases = []
    for resolved_tag in (INDEPENDENT, JOINT):
        for unresolved_tag in (INDEPENDENT, JOINT, UNRESOLVED):
            for penalty in ("elasticnet", "l2"):
                for uniform in (True, False):
                    # minimal dims and small non-trivial dims
                    cases.append((resolved_tag, unresolved_tag, penalty,
                                  1, 1, 1, 1, 1, uniform))
                    cases.append((resolved_tag, unresolved_tag, penalty,
                                  3, 2, 3, 2, 5, uniform))
                    cases.append((resolved_tag, unresolved_tag, penalty,
                                  2, 4, 1, 3, 2, uniform))

    # --- randomized fuzz ------------------------------------------------------
    for _ in range(N_FUZZ):
        resolved_tag = rng.randint(0, 2)
        unresolved_tag = rng.randint(0, 3)
        penalty = "elasticnet" if rng.randint(0, 2) else "l2"
        n_classes = rng.randint(1, 5)
        n_folds = rng.randint(1, 4)
        n_cs = rng.randint(1, 4)
        n_l1 = rng.randint(1, 3)
        n_feat = rng.randint(1, 4)
        uniform = bool(rng.randint(0, 2))
        cases.append((resolved_tag, unresolved_tag, penalty, n_classes,
                      n_folds, n_cs, n_l1, n_feat, uniform))

    disagreements = []
    for tup in cases:
        err = check_one(code, rng, *tup)
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
    print("G-CONF OK: shadow of gather_per_class + mixing_record agrees with "
          "the real patched no-refit statements on %d inputs (seed=%d) and "
          "with %d full patched refit=False fits, 0 disagreements; on every "
          "one of those inputs the real ratio table also accepted every "
          "position the held candidate_table extent admits, refused position "
          "candidates_len, and contained the real flat decomposition, so the "
          "site-2 admissibility parameters are checked against reality and "
          "not merely passed."
          % (len(cases), SEED, n_fits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
