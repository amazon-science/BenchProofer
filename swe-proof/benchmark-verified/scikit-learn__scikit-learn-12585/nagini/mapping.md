# mapping.md — scikit-learn__scikit-learn-12585

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bfc4a566423e036fbdc9fb02765fd893e4860c85`, states the type
abstraction, and records callee provenance.

Repo file under change: `sklearn/base.py` (the `clone` function).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reproduce(est, permit_fallback)` | `clone(estimator, safe)` — `sklearn/base.py:30` (dispatch body lines 47-55) | the modeled changed function (the generic deep-copy / reconstruct routine) |
| `Candidate` (class) | the runtime `estimator` argument of `clone` | minimal abstraction carrying only the three dispatch-relevant predicates |
| `Candidate.is_aggregate` | `type(estimator) in (list, tuple, set, frozenset)` — `base.py:49` | whether the candidate takes the container-recursion branch |
| `Candidate.has_introspect` | `hasattr(estimator, 'get_params')` — `base.py:51` | whether the candidate exposes the parameter-introspection capability |
| `Candidate.is_class_object` | `isinstance(estimator, type)` — `base.py:51` (the **added** disjunct) | whether the candidate is a class object rather than an instance |
| `is_leaf(c)` | the `elif` guard `not hasattr(estimator,'get_params') or isinstance(estimator,type)` — `base.py:51` | the changed dispatch predicate: candidate is a non-reconstructable leaf |
| `NotCloneableError` | the `raise TypeError(...)` at `base.py:54-57` | the refusal raised when a leaf meets `safe=True` |
| `Requires(MustTerminate(2))` on `reproduce` (+ `MustTerminate(1)` on the `Candidate` constructor) | `clone()` always returns or raises on the non-aggregate path (no loop over unbounded state); the F2P/P2P tests observe its result, so a non-returning `clone` hangs the test harness | total-correctness obligation: pins that the dispatch DELIVERS its result. Added after the G-PANEL-1 audit exhibited a diverging same-spec impl (correct values, then an infinite loop) that verified under partial correctness while its faithful patch hung the F2P test (not resolved) |
| `permit_fallback` | the `safe` parameter, used as `if not safe:` at `base.py:52` (here carried as `permit_fallback = not safe` semantics: `permit_fallback` True ⇔ a fallback deep-copy is allowed ⇔ `safe is False`) | whether the atomic-copy fallback is permitted |

Note on the `permit_fallback`/`safe` polarity: in the repo, `if not safe:` →
`copy.deepcopy` (atomic fallback) and the `else:` raises. So "fallback
permitted" corresponds to `safe is False`. The model names the *enabling*
condition directly (`permit_fallback`) to keep the contract about the behaviour
rather than the parameter's inverted sense; this is a pure renaming bijection
(`permit_fallback ⇔ not safe`), recorded here and in refinement.md (tag R).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| arbitrary Python object `estimator` | `Candidate` with three booleans | the only properties `clone`'s dispatch reads are the three predicates above; all other object state is irrelevant to which branch is taken and to the tested identity outcome |
| `type(estimator) in (list, tuple, set, frozenset)` | `est.is_aggregate` | True iff the object is one of the four aggregate builtins |
| `hasattr(estimator, 'get_params')` | `est.has_introspect` | True iff the object exposes `get_params` as an attribute (a class exposes it too — see §3) |
| `isinstance(estimator, type)` | `est.is_class_object` | True iff the object is itself a class (an instance of `type`) |
| `safe` (boolean kwarg) | `permit_fallback = not safe` | `safe=False` ⇔ fallback permitted; `safe=True` ⇔ raise on a leaf |
| `copy.deepcopy(estimator)` on a **class object** leaf | identity (`return est`) | a class is an atomic object for `copy.deepcopy` (`_deepcopy_atomic`); `copy.deepcopy(cls) is cls` — see §3.1. Modeled as returning the same reference; the postcondition identity clause is scoped to `est.is_class_object`. |
| `copy.deepcopy(estimator)` on a **non-class** leaf (array / sparse / plain object) | a fresh, distinct `Candidate` | a state-bearing object is deep-copied to a NEW object, so `copy.deepcopy(obj) is not obj` (only value-equality holds, asserted by the P2P tests via `assert_array_equal`). The model allocates a fresh `Candidate` and asserts NO identity for this disjunct — see §3.2. |
| `klass(**estimator.get_params(...))` reconstruction | allocate a fresh `Candidate` | the reconstruction yields a brand-new object, so `Result() is not est`; its own field values are unobserved by the tested behaviour |

## 3. Provenance of the modeled dispatch predicate (the changed operation)

The changed operation is the `elif` **guard** at `sklearn/base.py:51`:

```
-    elif not hasattr(estimator, 'get_params'):
+    elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):
```

This is modeled **deeply** as `is_leaf(c) == (not c.has_introspect) or
c.is_class_object`. There is no axiomatized callee consumed by the proof — the
predicate is spelled out. `axiom_check.py` (G-AX) validates the abstraction by
executing the REAL `clone` dispatch ingredients (`hasattr(obj,'get_params')`,
`isinstance(obj,type)`) on instances, classes, aggregates and non-estimators,
plus the identity outcome of the fallback copy.

### 3.1 Why a class object exposes `get_params` yet must be a leaf
A scikit-learn estimator class (e.g. `StandardScaler`) defines `get_params` as
a method, so the *class object itself* satisfies `hasattr(StandardScaler,
'get_params') == True`. Pre-patch this routed the class into the reconstruction
branch, where `estimator.get_params(deep=False)` is called on the **class** and
raises `TypeError: get_params() missing 1 required positional argument: 'self'`
(an unbound method needs an instance). The added `isinstance(estimator, type)`
disjunct reclassifies any class object as a leaf, so it is reproduced via the
`safe=False` fallback `copy.deepcopy(estimator)` instead.

### 3.2 `copy.deepcopy` of a leaf: per-disjunct fidelity
The leaf branch is `return copy.deepcopy(estimator)`. `copy.deepcopy`'s outcome
depends on the object kind, and the spec must be faithful to gold over the
**entire** in-domain leaf set — both disjuncts of `is_leaf = (not has_introspect)
or is_class_object`, not only the class-object representative the F2P test
exercises:

- **Class-object leaf (identity).** `copy.deepcopy` treats classes (and other
  type objects) as atomic via the `_deepcopy_atomic` dispatch (CPython
  `Lib/copy.py`: `type` is in `_deepcopy_dispatch` mapped to `_deepcopy_atomic`,
  which returns its argument unchanged). Hence `copy.deepcopy(MyEstimator) is
  MyEstimator`. The recursive inner call inside `clone` is `clone(param,
  safe=False)`, so the class parameter takes the `if not safe:` branch and is
  returned reference-identical. This is the exact property the F2P test asserts:

  ```python
  clf = MyEstimator(empty=MyEstimator)   # the `empty` parameter is a CLASS
  clf2 = clone(clf)
  assert clf.empty is clf2.empty          # identity preserved across the clone
  ```

  The model encodes this as the identity clause **scoped to `est.is_class_object`**
  (`Implies(is_leaf(est) and permit_fallback and est.is_class_object,
  Result() is est)`), with the impl returning `est` on that disjunct.

- **Non-class leaf (distinct object).** A leaf reached because `not
  hasattr(obj,'get_params')` and `not isinstance(obj,type)` — a numpy array, a
  sparse matrix, a plain non-estimator object — is **state-bearing**, so
  `copy.deepcopy(obj)` returns a NEW, distinct object: `copy.deepcopy(obj) is
  not obj` (only value-equality holds). These inputs are in-domain (the only
  precondition is `is_aggregate is False`) and are exercised by the P2P tests
  (`test_clone_empty_array`, `test_clone_sparse_matrices`), which assert
  value-equality via `assert_array_equal`, NOT identity. A spec that demanded
  `Result() is est` for ALL leaves would therefore **reject** a gold-faithful
  implementation (the prior TOO-STRONG defect). The model is faithful: it
  allocates a fresh `Candidate` on this disjunct and asserts NO identity, so the
  postcondition is dischargeable by gold's actual semantics on every leaf.

`axiom_check.py` asserts `copy.deepcopy(cls) is cls` for a range of class
objects (the only disjunct the identity guarantee covers) AND
`copy.deepcopy(obj) is not obj` for non-class state-bearing leaves (an array, a
plain object), confirming the per-disjunct modeling above. Docs:
https://docs.python.org/3/library/copy.html (deepcopy of atomic types).

## 4. No consumed axioms
The proof consumes no `@ContractOnly` axiom. The container-recursion branch
(`is_aggregate`) and the full reconstruction machinery are excluded from /
unobserved by the modeled contract; the only changed operation — the leaf
dispatch predicate — is modeled deeply (§3) and validated against the real
dispatch ingredients by `axiom_check.py` (G-AX) as A-reference evidence.

## 5. G-CONF conformance check
`conformance_check.py` (G-CONF) runs the contract-stripped impl region of
`reproduce` differentially against the REAL patched `sklearn.base.clone`
in-container, lowering concrete candidate objects through the §1–§2 bridge
(the three dispatch predicates; `permit_fallback = not safe`;
`NotCloneableError` ↔ the refusal `TypeError`). Observables compared: outcome
kind (return vs refusal) on every probe, plus result identity wherever the
bridge asserts a definite value (class-object leaf ⇒ identical; non-leaf ⇒
distinct; state-bearing non-class leaf ⇒ distinct). Atomic-immutable
non-class leaves (int/str/None/…) are compared on outcome kind only — the
model's fresh-`Candidate` allocation there is deliberate §2 abstraction
slack, not an asserted identity. ≥1e5 Requires-satisfying inputs (boundary
enumeration of all non-aggregate dispatch combinations × both polarities +
100000 randomized candidates). **Pinned fuzz seed: 12585.**
