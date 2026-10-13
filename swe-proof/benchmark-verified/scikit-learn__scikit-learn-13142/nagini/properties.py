# properties.py — PBT falsification battery for scikit-learn__scikit-learn-13142.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only the impl region differs,
# guaranteed by region-surgery via _swap on substrings that lie ENTIRELY inside
# # impl-start ... # impl-end) and are checked by Nagini verify + markers.same_spec.
# Axiom cases are real-callee probes run in the instance image (Docker).
#
# ---------------------------------------------------------------------------
# Defended surface — fit_and_label(inst, run_config, run_score) -> int
#   (models BaseMixture.fit_predict: fit n_init trials, persist the selected-best
#    parameters, return the labels derived from the PERSISTED configuration; the
#    gold patch MOVES the final e-step to run AFTER _set_parameters(best_params)).
#
#   Signature / permissions:
#     inst.config        : Acc(inst.config)               -> WRITABLE (the held
#                          parameter state the routine selects + persists).
#     run_config:List[int]: Requires Acc(list_pred(run_config), 1/2) -> READ-ONLY
#     run_score :List[int]: Requires Acc(list_pred(run_score),  1/2) -> READ-ONLY
#     => directive-5 FRAME-MUTATION is MANDATORY (two read-only list inputs).
#
#   Requires: len(run_config) == len(run_score); len(run_config) >= 1.
#
#   Ensures (the two LOAD-BEARING clauses):
#     (P1)  inst.config == best_config(ToSeq(run_config), ToSeq(run_score))
#             -> the PERSISTED config is the earliest-largest-score trial.
#     (P2)  Result()    == labels_of(inst.config)
#             -> the RETURNED labels are the label assignment of the config the
#                object holds ON RETURN (persist-then-derive). This is the entire
#                content of the fix: predict(X) is labels_of(persisted config), so
#                (P2) is "fit-time labels agree with query-time labels".
#     (plus frame: Acc(inst.config); Acc(list_pred(run_config),1/2);
#                  Acc(list_pred(run_score),1/2); the two length facts.)
#
# Oracle grounding: labels_of is @Pure @ContractOnly of `config` with NO Ensures
# body — the proof consumes only its PURITY (config1==config2 => labels_of(config1)
# ==labels_of(config2)). (P2) pins Result to labels_of(inst.config) where inst.config
# is itself pinned by (P1) to best_config(...). So labels_of is GROUNDED in the
# inputs (a function of the args via best_config) — there is no opaque answer-key to
# echo with a wrong value. The ungrounded-oracle-echo class therefore has no wrong
# echo; the attack that DOES exist is the prepatch order-swap (return labels_of of
# the *transient* config while persisting the best) — see weak-order-swap below,
# plus an honest cheapest-impl positive control (pos-control-tail-local). See
# 'assessment'.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13142"
FLOAT_ENCODING = None   # meta.json float_encoding is null (scores modeled as int)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold tail (inside the impl region): persist the selected config, THEN
# derive labels from the persisted config, then return. Every variant below edits
# only text inside # impl-start ... # impl-end, so the spec view is untouched.
_GOLD_TAIL = ("    inst.config = selected\n"
              "    labels = labels_of(inst.config)\n"
              "    return labels")

_GOLD_PREAMBLE = (
    "    n = len(run_config)\n"
    "    # The transient configuration the object holds after the final trial is the\n"
    "    # final trial's configuration (may differ from the selected one).\n"
    "    inst.config = run_config[n - 1]")


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY) — write to the READ-ONLY input run_config.
#    Keep the ENTIRE correct computation verbatim (the backward scan + all
#    invariants/asserts + the correct persist-then-derive tail), and insert a
#    single write `run_config[0] = selected` before returning. Writing a list
#    element needs FULL Acc(list_pred(run_config)); the precondition grants only
#    Acc(...,1/2). => REJECT for INSUFFICIENT PERMISSION, attributable solely to
#    the write (nothing else changed). A byte-fuzzer never thinks to mutate the
#    input; this is the project's #1 weakness class.
# ===========================================================================
_frame_mutate = _swap(
    _BASE,
    _GOLD_TAIL,
    "    inst.config = selected\n"
    "    # FRAME-MUTATION rival: overwrite the read-only input list to (vacuously)\n"
    "    # try to satisfy the spec. run_config has only Acc(..., 1/2) (read-only),\n"
    "    # so this write has insufficient permission and must be rejected.\n"
    "    run_config[0] = selected\n"
    "    labels = labels_of(inst.config)\n"
    "    return labels",
)


# ===========================================================================
# 2. UNIQUENESS / partial-domain — DROP THE SELECTION LOOP. Persist the FINAL
#    trial's config and return its labels. Correct only when n == 1 OR the last
#    trial is the best; diverges on every input whose best trial is not the last.
#    => REJECT on (P1) inst.config == best_config(...): the final-trial config is
#    not best_config unless the last trial is the earliest-max.
# ===========================================================================
_drop_selection = _swap(
    _BASE,
    _GOLD_PREAMBLE + "\n"
    "    # Select the highest-scoring (earliest-on-tie) configuration over all trials\n"
    "    # by scanning the trials from last to first; the running selection equals\n"
    "    # best_config / best_score over the already-scanned suffix.\n"
    "    selected = run_config[n - 1]  # type: int\n"
    "    selected_score = run_score[n - 1]  # type: int\n"
    "    i = n\n"
    "    while i > 1:",
    _GOLD_PREAMBLE + "\n"
    "    # PARTIAL-DOMAIN rival: skip the selection scan entirely; keep the final\n"
    "    # trial's config as the 'selection'. Correct only when the LAST trial is\n"
    "    # the best (incl. n == 1), wrong on every other input.\n"
    "    selected = run_config[n - 1]  # type: int\n"
    "    selected_score = run_score[n - 1]  # type: int\n"
    "    i = 1\n"
    "    while i > 1:",
)


# ===========================================================================
# 3. UNIQUENESS / order-swap (THE prepatch bug) — persist the selected-best
#    correctly (so (P1) holds) but RETURN the labels of the TRANSIENT final-trial
#    config (`run_config[n-1]`), the pre-change query position. => REJECT on (P2)
#    Result() == labels_of(inst.config): inst.config == selected (best) while the
#    returned value is labels_of(final-trial config), and these differ whenever
#    the best trial is not the last. This is exactly model_prepatch.py (G-DIFF),
#    restated as a uniqueness rival.
# ===========================================================================
_order_swap = _swap(
    _BASE,
    "    # Persist the selected configuration, THEN derive the labels from the\n"
    "    # persisted (retained) configuration.\n"
    + _GOLD_TAIL,
    "    # ORDER-SWAP rival (prepatch position): derive the labels from the\n"
    "    # TRANSIENT final-trial config, THEN persist the selected best.\n"
    "    n2 = len(run_config)\n"
    "    labels = labels_of(run_config[n2 - 1])\n"
    "    inst.config = selected\n"
    "    return labels",
)


# ===========================================================================
# 4. UNIQUENESS / tie-break — STRICT comparison in the scan. The gold scan goes
#    LAST->FIRST and updates on `s >= selected_score`, so on a tie the EARLIER
#    forward index overwrites (earliest-largest, matching best_config's >= at the
#    front-recursion head and the real loop's strict `>` forward selection). Using
#    `s > selected_score` never overwrites on a tie, so the scan keeps the LATER
#    forward index's config on ties. => REJECT on (P1): selected != best_config(...)
#    on any input with a tie for the maximum score (a tie-only subdomain).
# ===========================================================================
_strict_tiebreak = _swap(
    _BASE,
    "        if s >= selected_score:",
    "        # TIE-BREAK rival: strict `>` keeps the LATER forward index on a tie,\n"
    "        # but best_config selects the EARLIEST-max. Diverges on tied scores.\n"
    "        if s > selected_score:",
)


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — BRANCH-REORDER inside the loop. Rewrite the
#    update guard `s >= selected_score` as the logically-identical `not (s <
#    selected_score)` (for ints, s >= t  <=>  not (s < t)). Keeps the EXACT loop,
#    every Invariant and every framing Assert verbatim — only the guard's
#    surface shape changes. Behaviourally identical, so (P1) and (P2) still hold;
#    no loop-direction flip / induction lemma needed. MUST VERIFY, else SPEC-TOO-
#    STRONG. (Directive-2/3 safe: gold proof obligations all preserved.)
# ===========================================================================
_pos_reorder = _swap(
    _BASE,
    "        s = run_score[i - 2]\n"
    "        if s >= selected_score:\n"
    "            selected = run_config[i - 2]\n"
    "            selected_score = s",
    "        s = run_score[i - 2]\n"
    "        # branch-reorder positive control: same condition, surface-different.\n"
    "        if not (s < selected_score):\n"
    "            selected = run_config[i - 2]\n"
    "            selected_score = s",
)


# ===========================================================================
# 6. POSITIVE CONTROL (soundness, cheapest honest tail) — LOCAL-VARIABLE RESHAPE
#    of the persist-then-derive tail: persist `selected`, read inst.config into a
#    local `c`, derive labels from `c`. Since c == inst.config == selected, by
#    labels_of purity labels_of(c) == labels_of(inst.config). Preserves the
#    persist-BEFORE-derive order (the content of the fix) — only the executable
#    shape of the tail changes. Doubles as the grounded-oracle positive control:
#    (P2) pins Result to labels_of(the persisted config), so the honest impl that
#    derives from the persisted config is exactly what satisfies it (no wrong echo
#    exists). MUST VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================
_pos_tail_local = _swap(
    _BASE,
    _GOLD_TAIL,
    "    inst.config = selected\n"
    "    # local-variable reshape: read the PERSISTED config into c, derive from c.\n"
    "    c = inst.config  # type: int\n"
    "    labels = labels_of(c)\n"
    "    return labels",
)


# ===========================================================================
# 7. ADMISSIBILITY — a self-call witness inside the impl establishes that the
#    precondition admits a normal F2P-shaped (n_init>1) input and the postcondition
#    is usable. Build a concrete in-domain input list (length 3, with a tie and a
#    non-last best), call fit_and_label on a fresh Estimator, and Assert the
#    post-condition facts (the returned labels equal labels_of of the persisted
#    selected-best config). Modular verification uses fit_and_label's OWN contract.
#    MUST VERIFY, else PRECOND-TOO-STRONG (the precondition would reject a normal
#    multi-trial input). The original computation is kept verbatim after the witness.
# ===========================================================================
_admiss = _swap(
    _BASE,
    "    n = len(run_config)\n"
    "    # The transient configuration the object holds after the final trial is the",
    "    # ADMISSIBILITY witness: the precondition admits a normal multi-trial input\n"
    "    # (n_init = 3, a tie for the max, best NOT last), and the postcondition\n"
    "    # yields labels == labels_of(the persisted selected-best config).\n"
    "    cfgs = [10, 11, 12]      # type: List[int]\n"
    "    scrs = [7, 9, 9]         # type: List[int]\n"
    "    probe = Estimator(0)\n"
    "    lab = fit_and_label(probe, cfgs, scrs)\n"
    "    Assert(probe.config == best_config(ToSeq(cfgs), ToSeq(scrs)))\n"
    "    Assert(lab == labels_of(probe.config))\n"
    "    n = len(run_config)\n"
    "    # The transient configuration the object holds after the final trial is the",
)


SPEC_TESTS = [
    {
        "id": "frame-mutate-readonly-run_config",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mutate,
        "refinement": (
            "The faithful real analogue writes into the trial inputs / data X that "
            "fit_predict only reads — e.g. mutating X (or a trial's _get_parameters "
            "snapshot) to force fit-time labels to match. But predict(X) reads the "
            "ORIGINAL X and held params, so corrupting the read-only input makes "
            "fit_predict(X) disagree with predict(X) on the real (uncorrupted) data: "
            "the F2P assert_array_equal(fit_predict(X), predict(X)) FAILS -> would NOT "
            "resolve. The selection/label computation is otherwise identical to gold."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM, not a value clause: "
            "run_config has Requires(Acc(list_pred(run_config), 1/2)) (read-only). "
            "The write run_config[0] = selected needs full Acc(list_pred(run_config)), "
            "which is not held -> insufficient permission. Every value clause (P1/P2) "
            "and all invariants are kept verbatim, so the failure is attributable "
            "solely to the write."
        ),
    },
    {
        "id": "drop-selection-keep-final-trial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_selection,
        "refinement": (
            "Persisting the FINAL trial's params and returning their labels is the "
            "pre-patch behaviour for n_init>1: the EM loop leaves self at the last "
            "init's params, and without selecting/persisting best_params the object "
            "holds the wrong (non-best) config. predict(X) then differs from the "
            "fit_predict labels whenever the best init is not the last; the F2P test "
            "(GaussianMixture n_init=5 / BayesianGaussianMixture n_init=10, "
            "random_state=0) FAILS -> would NOT resolve."
        ),
        "rationale": (
            "Rejection from (P1) inst.config == best_config(ToSeq(run_config), "
            "ToSeq(run_score)). The loop is dead (`i = 1` so `while i > 1` never "
            "runs), leaving selected = run_config[n-1] = the final trial. For an input "
            "whose earliest-max trial is not the last, run_config[n-1] != "
            "best_config(...), so (P1) cannot discharge."
        ),
    },
    {
        "id": "weak-order-swap-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _order_swap,
        "refinement": (
            "This is model_prepatch.py exactly (G-DIFF): derive labels from the "
            "transient FINAL-trial config, then persist the selected best. In the "
            "repo this is the pre-patch e-step position — the labels returned by "
            "fit_predict are log_resp.argmax computed BEFORE _set_parameters(best_"
            "params), i.e. from the last init's params, while the object ends holding "
            "best_params. predict(X) (on best_params) then disagrees with the returned "
            "labels for n_init>1 -> the reported bug, the F2P test FAILS -> would NOT "
            "resolve."
        ),
        "rationale": (
            "Rejection from (P2) Result() == labels_of(inst.config). inst.config is "
            "persisted to `selected` (= best_config, so (P1) holds), but Result() is "
            "labels_of(run_config[n-1]) (the final-trial config). By labels_of purity "
            "these are equal ONLY if run_config[n-1] == selected, which fails whenever "
            "the best trial is not the last -> (P2) cannot discharge."
        ),
    },
    {
        "id": "strict-tiebreak-wrong-earliest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _strict_tiebreak,
        "refinement": (
            "The real loop updates best_params only on a STRICT increase "
            "(`if lower_bound > max_lower_bound`), scanning trials FORWARD, so the "
            "EARLIEST trial achieving the maximum is retained. A rival that, in the "
            "backward scan, also uses strict `>` keeps the LATER forward index on a "
            "tie — the wrong trial's params are persisted. With a tie for the maximum "
            "lower_bound, the persisted params differ from the canonical earliest-max "
            "selection, so fit_predict's labels (and the object's predict) reflect a "
            "different trial than the gold -> diverges on tied-score inputs -> would "
            "NOT resolve on a tie-bearing run."
        ),
        "rationale": (
            "Rejection from (P1) inst.config == best_config(...). best_config encodes "
            "earliest-max (>= at the front-recursion head); the backward scan must use "
            "`>=` so a tie overwrites with the earlier forward index. Strict `>` "
            "leaves the loop invariant selected == best_config(...drop(i-1)) "
            "unprovable at the tie step, so (P1) cannot discharge."
        ),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_reorder,
        "rationale": (
            "Structurally different but behaviourally identical: the update guard "
            "`s >= selected_score` is rewritten as `not (s < selected_score)` (for "
            "ints these are equivalent). The exact loop, every Invariant and every "
            "framing Assert are kept verbatim, so the gold proof obligations all still "
            "discharge and (P1)/(P2) hold. MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-tail-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_tail_local,
        "rationale": (
            "Cheapest honest tail: persist `selected`, read inst.config into a local "
            "`c`, derive labels from `c`. Since c == inst.config == selected, "
            "labels_of(c) == labels_of(inst.config) by purity; the persist-before-"
            "derive order (the fix) is preserved. Doubles as the grounded-oracle "
            "positive control: (P2) pins Result to labels_of(the PERSISTED config), so "
            "deriving from the persisted config is exactly what satisfies it (no wrong "
            "echo exists). MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-multitrial-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Self-call on a normal F2P-shaped multi-trial input (n_init=3, a tie for "
            "the max, best NOT last) establishes the precondition (equal-length lists, "
            "len >= 1) and uses the postcondition (persisted == best_config; returned "
            "== labels_of(persisted)). The original computation is kept verbatim after "
            "the witness. MUST verify, else PRECOND-TOO-STRONG (the precondition would "
            "reject a normal n_init>1 input)."
        ),
    },
]


# ===========================================================================
# AXIOM lane.
#
#   labels_of (A-consumed, @Pure @ContractOnly, NO Ensures body): models the
#     label-assignment query primitive `_e_step(X) -> log_resp.argmax(axis=1)`,
#     equivalently predict's `_estimate_weighted_log_prob(X).argmax(axis=1)`. The
#     ONLY guarantee the proof consumes is PURITY: same held configuration => same
#     labels. So the soundness obligation is exactly: the real query primitive is a
#     deterministic function of the held parameter configuration (and equals predict
#     on those held params, the standing equivalence the fix restores).
#
#   best_config / best_score (A-reference deep model): the trial-selection loop
#     `if lower_bound > max_lower_bound: best_params = self._get_parameters()`.
#     Validated == the real loop: after a full fit with n_init>1 the RETAINED
#     params are the largest-lower-bound trial's (retained-best labels == predict),
#     and the operation ORDER is observable (pre-patch final-trial labels differ
#     from retained-best labels — the reported discrepancy).
#
# Both are checked by EXECUTING the real callees in the instance image. We reuse
# axiom_check.py's logic verbatim (embedded into the probe; the runner mounts only
# the probe at /work, so axiom_check.py is NOT in-container — we inline it). The
# primitive's purity + the selection loop are UNCHANGED by the patch, and the
# differential witness reproduces the PRE-patch fit_predict, so apply_gold=False
# (run against the base_commit estimator).
#
#   Containment: labels_of is typed int->int with NO Requires on config (totally
#   unconstrained domain); the model passes inst.config == best_config(...) (one of
#   the input run_config[i] values). Every such config is a real fitted-parameter
#   snapshot that _set_parameters/_e_step accepts. So every callee-input the model
#   reaches is in the (unconstrained) axiom domain — verified below by feeding the
#   query primitive each of the n_init trial snapshots (the selected-best is always
#   one of them). Covering more than the caller reaches is sound, not a defect.
# ===========================================================================

# Embed axiom_check.py's executable soundness logic so the probe is self-contained
# (the runner mounts ONLY the probe at /work). Read on the HOST at manifest load.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# === embedded axiom_check.py (host-read at manifest load; /work mounts only\n"
    "# this probe, so the bundle oracle is inlined) ===\n"
    "_NS = {'__name__': '_axc'}\n"
    "exec(compile(" + repr(_AXIOM_CHECK_SRC) + ", 'axiom_check.py', 'exec'), _NS)\n"
    "\n"
    "import numpy as np\n"
    "from sklearn.mixture import GaussianMixture, BayesianGaussianMixture\n"
    "\n"
    "rng = np.random.RandomState(0)\n"
    "X = rng.randn(1000, 5)\n"
    "\n"
    "# (A-consumed) labels_of: the query primitive is a deterministic pure function\n"
    "# of the held configuration, and equals predict on those held params.\n"
    "for make in (\n"
    "    lambda: GaussianMixture(n_components=5, random_state=0),\n"
    "    lambda: GaussianMixture(n_components=3, covariance_type='tied', random_state=1),\n"
    "    lambda: GaussianMixture(n_components=4, covariance_type='diag', random_state=2),\n"
    "    lambda: BayesianGaussianMixture(n_components=5, random_state=0),\n"
    "):\n"
    "    _NS['check_query_is_pure_function_of_config'](make, X)\n"
    "\n"
    "# (A-reference) selection deep model + differential witness over n_init>1 seeds.\n"
    "any_observable = False\n"
    "n_checked = 0\n"
    "for seed in range(8):\n"
    "    for make_ninit in (\n"
    "        (lambda s=seed: GaussianMixture(n_components=5, n_init=5, random_state=s)),\n"
    "        (lambda s=seed: BayesianGaussianMixture(n_components=5, n_init=10, random_state=s)),\n"
    "    ):\n"
    "        any_observable |= _NS['check_selection_and_order_observable'](make_ninit, X)\n"
    "        n_checked += 1\n"
    "\n"
    "if not any_observable:\n"
    "    print('AXIOM-UNSOUND: operation order never observable (no differential witness)')\n"
    "    sys.exit(1)\n"
    "\n"
    "print('axiom-soundness OK: labels_of is a deterministic pure function of the '\n"
    "      'held configuration (determinism + configuration-functionality + e-step '\n"
    "      'argmax == predict on the held params); the best_config/best_score '\n"
    "      'selection deep model is sound (retained-best labels == predict) and the '\n"
    "      'persist-then-derive order is observable across %d n_init>1 configs.' % n_checked)\n"
    "sys.exit(0)\n"
)


_AX_CONTAIN_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "import numpy as np\n"
    "from sklearn.mixture import GaussianMixture, BayesianGaussianMixture\n"
    "\n"
    "# AXIOM-CONTAINMENT for labels_of. labels_of is typed int->int with NO Requires\n"
    "# on config (unconstrained domain). The model passes inst.config == best_config(\n"
    "# run_config, run_score) -- which is ALWAYS one of the input run_config[i] values\n"
    "# (best_config returns config[k] for some k). In the repo, each run_config[i] is a\n"
    "# per-trial _get_parameters() snapshot, and the selected-best is one of them. So\n"
    "# every config the model can hand to the query primitive is a real fitted snapshot\n"
    "# that _e_step / _set_parameters accepts. We confirm this directly: feed the query\n"
    "# primitive EACH of the n_init trial snapshots (every candidate the selection could\n"
    "# pick) and confirm it produces labels with no error -- i.e. every reachable\n"
    "# callee-input lies in the callee's accepted domain. A reachable input that the\n"
    "# callee rejected would be AXIOM-TOO-WEAK-FOR-CALLER.\n"
    "fail = []\n"
    "rng = np.random.RandomState(0)\n"
    "X = rng.randn(400, 4)\n"
    "\n"
    "def trial_snapshots(make, n_init):\n"
    "    # Reproduce the per-trial _get_parameters() snapshots the selection ranges over\n"
    "    # by fitting single-init estimators from each per-trial init (the candidates\n"
    "    # best_config selects among). Each is a config the model could hold + query.\n"
    "    snaps = []\n"
    "    for r in range(n_init):\n"
    "        est = make(r)\n"
    "        est.fit(X)\n"
    "        snaps.append(est._get_parameters())\n"
    "    return snaps\n"
    "\n"
    "for maker, n_init in (\n"
    "    (lambda r: GaussianMixture(n_components=5, n_init=1, random_state=r), 5),\n"
    "    (lambda r: GaussianMixture(n_components=3, covariance_type='diag', n_init=1, random_state=r), 4),\n"
    "    (lambda r: BayesianGaussianMixture(n_components=5, n_init=1, random_state=r), 6),\n"
    "):\n"
    "    snaps = trial_snapshots(maker, n_init)\n"
    "    host = maker(0)\n"
    "    host.fit(X)\n"
    "    for k, snap in enumerate(snaps):\n"
    "        try:\n"
    "            host._set_parameters(snap)\n"
    "            _, log_resp = host._e_step(X)   # the labels_of callee\n"
    "            labels = log_resp.argmax(axis=1)\n"
    "            # determinism on this reachable config (purity, the consumed guarantee)\n"
    "            _, log_resp2 = host._e_step(X)\n"
    "            if not np.array_equal(labels, log_resp2.argmax(axis=1)):\n"
    "                fail.append('non-deterministic labels on trial snapshot %d' % k)\n"
    "            if not np.array_equal(labels, host.predict(X)):\n"
    "                fail.append('e-step argmax != predict on trial snapshot %d' % k)\n"
    "        except Exception as e:\n"
    "            fail.append('query primitive rejected a reachable config (snapshot %d): %r' % (k, e))\n"
    "\n"
    "if fail:\n"
    "    print('AXIOM-TOO-WEAK-FOR-CALLER:', '; '.join(fail[:6]))\n"
    "    sys.exit(1)\n"
    "print('axiom-containment OK: every config the model can hand to labels_of is one '\n"
    "      'of the per-trial parameter snapshots (best_config returns an input config); '\n"
    "      'the real query primitive accepts every such snapshot and is deterministic '\n"
    "      'on it (== predict). labels_of has an unconstrained domain, so every '\n"
    "      'reachable callee-input is covered.')\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-labels_of-selection",
        "axiom": "labels_of (+ best_config/best_score A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,   # the query primitive + selection loop are UNCHANGED by
                               # the patch; the differential witness reproduces the
                               # PRE-patch fit_predict (final-trial labels).
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The only guarantee the proof consumes from labels_of is PURITY (same "
            "held config => same labels). Executing the real query primitive on real "
            "GaussianMixture/BayesianGaussianMixture fits confirms determinism + "
            "configuration-functionality (equal _set_parameters snapshots => equal "
            "labels) + the standing equivalence e-step.argmax == predict, and the "
            "best_config/best_score deep model (retained-best labels == predict, order "
            "observable). Any disagreement => AXIOM-UNSOUND. Reuses axiom_check.py."
        ),
    },
    {
        "id": "ax-contain-labels_of-reachable-configs",
        "axiom": "labels_of",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Every config the model hands to labels_of is inst.config == "
            "best_config(run_config, run_score) — one of the input run_config[i] "
            "values, i.e. a per-trial _get_parameters snapshot. The real query "
            "primitive accepts every such snapshot and is deterministic (== predict). "
            "labels_of has an unconstrained (int) domain, so every reachable "
            "callee-input is covered; a rejected reachable config would be "
            "AXIOM-TOO-WEAK-FOR-CALLER (none exists)."
        ),
    },
]
