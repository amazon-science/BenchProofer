# mapping.md — scikit-learn__scikit-learn-12682

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d360ffa7c5896a91ae498b3fb9cf464464ce8f34`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. `spec_provenance: cold` — the spec was derived only from
`problem_statement`, the gold `patch`, and the repo source at `base_commit`.

Repo file under change: `sklearn/decomposition/dict_learning.py`.

## 1. Symbol ↔ repo binding

The behavior under spec is a **data-flow** property: a user-configurable
iteration budget for the underlying iterative solver, accepted at estimator
construction, must be **recorded** on the estimator and then **forwarded
unchanged** to the solver — instead of being dropped so the solver falls back on
its fixed built-in default. The gold patch threads one new value through the
construction → encode → solver chain.

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `CodingConfig.iterationBudget` | the estimator attribute set by `SparseCodingMixin._set_sparse_coding_params` — `sklearn/decomposition/dict_learning.py:864` — read in `SparseCodingMixin.transform` — `:877` | the recorded per-estimator solver iteration budget (post-patch `self.transform_max_iter`) |
| `recordIterationBudget (userBudget : Nat)` | the construction path `SparseCoder.__init__` (`:992`) → `_set_sparse_coding_params` (`:864`) that stores the construction-time budget on the estimator | the modeled changed step: record the user-requested budget on the configuration |
| `encodeWithConfig (cfg)` | `SparseCodingMixin.transform` (`:877`) reading the recorded budget and calling `sparse_encode(..., max_iter=...)` (`:898`), whose argument is handed straight to the solver via `_sparse_encode` (`:128`,`:140`) | the modeled changed step: read the configured budget and forward it to the solver as its iteration limit |
| `configuredBudgetReachesSolver (userBudget)` | the composition construct→transform→`sparse_encode`→solver | end-to-end: the user-configured budget is the iteration limit the solver runs with |

The pre-patch repo facts the change removes (refinement audit only, not in the
consumer spec view): `_set_sparse_coding_params`, `SparseCoder.__init__`,
`SparseCoder.transform` accepted/stored/forwarded **no** iteration-budget
argument, so `sparse_encode` was called without `max_iter`, defaulting to the
fixed `max_iter=1000` (`sparse_encode` signature default, `:189`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the iteration budget (`transform_max_iter` / `max_iter`, a Python `int ≥ 1`) | `Nat` | the integer `b` ↔ the natural `b`; iteration counts are non-negative whole numbers, total and exact. The value forwarded is pinned exactly (no rounding/precision involved). |
| the estimator's recorded configuration (only the budget field is touched by this behavior) | `structure CodingConfig` with the single field `iterationBudget` | `self.transform_max_iter` ↔ `cfg.iterationBudget`; all other estimator attributes are orthogonal to this behavior and omitted (SPEC_GUIDE §2 "rich object → structure with only the touched fields"). |
| `sparse_encode(..., max_iter=v, ...)` argument reaching the solver (`Lasso(max_iter=v)` / `LassoLars(max_iter=v)`) | the return value of `encodeWithConfig` (`solverBudget : Nat`) | the `max_iter` kwarg value that arrives at the underlying solver constructor ↔ `solverBudget`. G-CONF observes it by intercepting the solver constructor. |

## 3. Callee provenance

There are **no axiomatized callees and no deep-model references** in this bundle.
The behavior is purely the threading of one value; nothing is claimed about the
numerical behavior of any callee.

- The underlying iterative solver (`Lasso` / `LassoLars`) is an UNCHANGED callee.
  The spec makes **no** claim about its output — only about which `max_iter`
  value reaches it — so there is no callee property to consume as an axiom and
  nothing for G-AX to validate (G-AX **skips**: no `axiom_check.py`, matching the
  no-axiom precedent `django__django-11276`'s sibling `django__django-11149`).
- `sparse_encode` / `_sparse_encode` already forwarded their `max_iter` argument
  to the solver verbatim **before** the patch (`_sparse_encode(..., max_iter=...)`
  → `Lasso(max_iter=max_iter, ...)`, `:140`). The patch's content is upstream:
  giving the construction path a budget to store and the `transform` path that
  stored budget to pass. `encodeWithConfig` models this verbatim forwarding as a
  concrete read (I), not a callee axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12682`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`recordIterationBudget` (store the budget) and `encodeWithConfig` (read it back
and forward), i.e. the identity `configuredBudgetReachesSolver(b) = b`. The
oracle constructs the patched `SparseCoder(transform_max_iter=b)` and intercepts
the `max_iter` value that arrives at the underlying solver constructor when
`transform` runs — the real end-to-end budget the gold patch delivers.
