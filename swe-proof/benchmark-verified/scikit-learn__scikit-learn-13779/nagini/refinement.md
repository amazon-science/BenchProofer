# refinement.md — scikit-learn__scikit-learn-13779

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_weighting_support` impl region and the live `accepts_weighting`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`/`Requires`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The weighted-fit pre-check — `_BaseVoting.fit` (`sklearn/ensemble/voting.py:79-83`)

Gold hunk (insert two lines before the probe call):
```
         if sample_weight is not None:
             for name, step in self.estimators:
+                if step is None:
+                    continue
                 if not has_fit_parameter(step, 'sample_weight'):
                     raise ValueError('Underlying estimator \'%s\' does not'
                                      ' support sample weights.' % name)
```

| # | model.py impl op (`check_weighting_support`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `roster: List[int]` | `self.estimators` — a list of `(name, step)` tuples (the iterable of `for name, step in self.estimators`) | R | each `(name, step)` ↦ a status tag in `{0,1,2}` (mapping.md §2): 0 absent (`step is None`), 1 present-accepts, 2 present-rejects. The `name` only formats the error message (unobserved by the tests) and is dropped. |
| A2 | `i = len(roster)` … `while i > 0:` … `status = roster[i-1]` … `i = i - 1` (back-to-front scan) | `for name, step in self.estimators:` (forward scan) | R + I | iteration over the roster; the back-to-front order matches the front-recursive `config_supports` (one unfold per step). Order is observationally irrelevant: the loop has no side effect on the roster and the only outcomes are "return normally" vs. "reject", both order-independent (see step A6 / §B). |
| A3 | `if status == 0: supported = supported` (the absent-entry skip; the probe is NOT consulted) | `if step is None: continue` | R + I | the ADDED guard. An absent entry (`step is None` ↔ status 0) is skipped before the probe is consulted; the model's status-0 branch likewise never calls `accepts_weighting`, honouring its precondition (the probe is undefined on an absent entry, mapping.md §3.1). This is the single behavioural change. |
| A4 | `elif not accepts_weighting(status):` | `if not has_fit_parameter(step, 'sample_weight'):` | A-consumed | `accepts_weighting` is the WEAKEST contract on `has_fit_parameter` the proof needs: it is meaningful only for a present entry (`Requires(status in {1,2})`) and reports acceptance exactly on status 1 (`Ensures(Result() == (status == 1))`) (mapping.md §3.1). The proof consumes its `Requires` (the call is reached only for a present `status`, by the status-0 skip in A3) and its `Ensures` (folding `supported`). G-AX confirms it against the real `has_fit_parameter` and confirms the probe RAISES on an absent entry (the precondition's faithfulness). |
| A5 | `supported = False` on a present-rejecting entry; `if not supported: raise WeightingUnsupported()` at the end | `raise ValueError('Underlying estimator ... does not support sample weights.' % name)` (raised on the first present-rejecting entry) | R + I | the rejection. `ValueError` ↦ the user-defined `WeightingUnsupported` (a builtin exception in an `Exsures` crashes the translator, mapping.md §2); the discriminating observable is the exception's identity (a weighting-unsupported rejection, NOT the un-fixed `AttributeError`), which the stand-in preserves. The message text is unobserved. |
| A6 | (full scan, single raise at the end) | (forward scan, raise on the first present-rejecting entry) | I (observationally) | the model folds support over the whole roster and raises once at the end iff some present entry rejects; the real loop raises on the first present-rejecting entry. These are observationally identical: the loop is side-effect-free on the roster and the sole outcome is return-normally (no present entry rejects) vs. raise-the-rejection (some present entry rejects). The full-scan form is used purely so the front-recursive `config_supports` postcondition follows from the final loop invariant (§B); it changes no observable. |

The discriminating content of the change — an ABSENT estimator (`step is None`,
set via `set_params(name=None)`) must be SKIPPED before the probe, not passed to
it — lives in step A3 (`if status == 0` skip ↔ `if step is None: continue`). The
pre-patch consulted the probe on every entry; `model_prepatch.py` reproduces that
(it drops the status-0 skip and calls `accepts_weighting(status)` for every
`status`, including 0) and **fails** verification on the probe's precondition
`status in {1, 2}` — the formal face of `'NoneType' object has no attribute
'fit'`. That is exactly the spec sensing the change (G-DIFF), and the exact F2P
observation: after `set_params(lr=None)`, `voter.fit(X, y, sample_weight=...)`
must not raise `AttributeError` (it must skip the `None` entry and fit the rest).

## B. The full-scan ↔ short-circuit equivalence (why the impl scans the whole roster)

The gold loop raises on the FIRST present-rejecting estimator (a short-circuit).
The model loop instead folds a boolean `supported` over the WHOLE roster and
raises once at the end iff `supported` is false. The two are behaviourally equal
on every input because:

  * the loop body has no side effect on `roster` (read-only, `Acc(.,1/2)`), so
    visiting later entries after the first rejecting one changes nothing;
  * the only outcomes are "return normally" and "raise `WeightingUnsupported`";
  * `supported` becomes false exactly when some present entry has status 2, which
    is exactly the condition under which the short-circuit loop reaches its
    `raise`. So both forms return normally iff every present entry accepts, and
    raise otherwise.

The full-scan form is chosen so the postcondition `config_supports(ToSeq(roster))`
(a front-recursive `@Pure` fold over the whole sequence) follows directly from
the final loop invariant `supported == config_supports(ToSeq(roster).drop(i))`
at `i == 0`. A mid-loop `raise` would require an inductive prefix-implies-suffix
lemma Nagini does not auto-derive; the full scan avoids it without weakening any
contract. The crucial fix — never consulting the probe on an absent entry
(step A3) — is preserved exactly: the status-0 branch skips the probe in both
the gold loop and the model loop.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— inserting the absent-entry guard so the probe is never consulted on a cleared
estimator — is modeled **directly** by the status-0 skip in
`check_weighting_support` (step A3) over the integer status tags. The probe
itself, `has_fit_parameter`, is UNCHANGED by the patch; it is an **A-consumed**
axiom whose present-only precondition and boolean result G-AX validates against
the real callee (and whose raise-on-absent G-AX also confirms, establishing the
precondition's faithfulness). There is no axiom about the function under change
(`_BaseVoting.fit`), and no A-reference deep model (the change is a control-flow
guard, not a value computation, modeled directly).

## D. verify(model) ⇒ resolved

`check_weighting_support` verifies only if it (a) never consults the probe on an
absent entry — the probe's precondition `status in {1,2}` would otherwise be
unprovable on a status-0 entry (this is what `model_prepatch.py` fails on), and
(b) returns normally exactly when every present entry accepts weighting
(`config_supports(ToSeq(roster))`) and raises `WeightingUnsupported` exactly when
some present entry rejects (the `Exsures` clause). By R
(`self.estimators` ↦ status tags; `step is None` ↦ status 0; `has_fit_parameter`
↦ `accepts_weighting`; `ValueError` ↦ `WeightingUnsupported`) the verified
pre-check equals the patched `_BaseVoting.fit` loop on the tested inputs; by G-AX
(A-consumed) the real `has_fit_parameter` returns the right bool on present
estimators and raises on absent ones, so admitting only present statuses to the
probe is sound. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
