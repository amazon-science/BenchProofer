# mapping.md — scikit-learn__scikit-learn-10908

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 67d06b18c68ee4452768f8a1e868565dd4354abf`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `sklearn/feature_extraction/text.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `getFeatureInventory (mut st) (supplied)` | `VectorizerMixin.get_feature_names(self)` — `sklearn/feature_extraction/text.py:994` (body 996-999) | the modeled changed function (read back the index→term inventory) |
| `materializeIndex (supplied) (st)` *(deep model — A-reference)* | `VectorizerMixin._validate_vocabulary(self)` — `sklearn/feature_extraction/text.py:273` | unchanged callee newly invoked by the guard; establishes `vocabulary_` from the explicit `vocabulary` param and records `fixed_vocabulary_` |
| `readinessGuard (st)` *(deep model — A-reference)* | `VectorizerMixin._check_vocabulary(self)` — `sklearn/feature_extraction/text.py:301` | unchanged readiness guard; raises `NotFittedError` if `vocabulary_` unset, `ValueError` if it is empty |
| `featureList (m)` | the return comprehension `[t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` — `text.py:998-999` | pure spec: index→term map projected to terms in ascending index order (unchanged op, I) |
| `featureNamesRun` | the whole post-patch `get_feature_names` body (guard ∘ validate ∘ check ∘ return) | pure transition `(state, result)` the method's `ensures` pins |

The change itself (the added two lines, `text.py:972-974` post-patch) is the
guard `if not hasattr(self, 'vocabulary_'): self._validate_vocabulary()` placed
before `self._check_vocabulary()` — i.e. the new orchestration / control flow,
which is R/I (concrete, transliterated by G-CONF). No repo symbol is *redefined*
by the patch; the two callees it newly invokes are unchanged (A-references).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the estimator's `vocabulary_` attribute (a `dict[str,int]`), or its absence | `InvState.index : Option (List (String × Nat))` | attribute absent ↔ `none`; `{t:i, …}` ↔ `some [(t,i), …]` as an association list; `len(vocabulary_)` ↔ `(index.getD []).length`; the empty dict ↔ `some []` |
| the estimator's `fixed_vocabulary_` attribute (a `bool`), or its absence | `InvState.explicit : Option Bool` | attribute absent ↔ `none`; `True`/`False` ↔ `some true`/`some false`. Only written by `_validate_vocabulary`; tracked because the F2P test observes it (`assert_false(cv.fixed_vocabulary_)` / `assert_true(cv.fixed_vocabulary_)`). |
| the `vocabulary` constructor parameter: a list of terms, or `None` | `supplied : Option (List String)` | `None` ↔ `none`; `['beer','burger',…]` ↔ `some ["beer","burger",…]`. A `set` is sorted to a list by the real callee first; a `Mapping` is the already-built dict path (out of this bundle's modeled domain — see §3.1). |
| a single feature term (`str`) | Lean `String` | identity on the value (terms are opaque labels; only equality and the index ordering matter) |
| `NotFittedError` raised by the guard | `Except.error InvErr.notReady` | `NotFittedError` (subclass of `ValueError`) ↔ `notReady` |
| `ValueError("Vocabulary is empty")` | `Except.error InvErr.emptyIndex` | the empty-`vocabulary_` rejection ↔ `emptyIndex` |
| the returned term list | `Except.ok (List String)` | `[t0, t1, …]` (index order) ↔ `ok [t0, t1, …]` |

`materializeIndex some terms = some terms.zipIdx`: `List.zipIdx` pairs each term
with its 0-based position, i.e. `[(t0,0),(t1,1),…]` — exactly the dict
`_validate_vocabulary` builds from a list via `enumerate` (`vocab.setdefault(t,i)`
for `i,t in enumerate(vocabulary)`), on the well-formed (unique, non-empty) domain
the `require` pins.

## 3. Callee provenance (A-references — checked by G-AX / axiom_check.py)

### 3.1 `materializeIndex` deep model ↔ `_validate_vocabulary` (A-reference)
**Callee:** `VectorizerMixin._validate_vocabulary` (`text.py:273-299`). On the
modeled domain — `vocabulary` is either `None` or a well-formed **list** of
unique, non-empty terms (the `require`) — the real callee:
- `vocabulary is None` ⇒ sets `self.fixed_vocabulary_ = False`, leaves
  `vocabulary_` unset ⇒ model `{ st with explicit := some false }` (index
  unchanged, here `none`);
- `vocabulary` a list ⇒ builds `vocab = {t:i for i,t in enumerate(vocabulary)}`,
  sets `self.fixed_vocabulary_ = True`, `self.vocabulary_ = dict(vocab)` ⇒ model
  `{ index := some terms.zipIdx, explicit := some true }`.

Out of modeled domain (validated by the `require`, not by an axiom): a `set`
(sorted first), a `Mapping` (repeated-index / gap-index checks), an empty
collection or a list with a duplicate term (each raises `ValueError` inside
`_validate_vocabulary`). G-AX exercises the in-domain cases and confirms the two
attribute writes match the model.

### 3.2 `readinessGuard` deep model ↔ `_check_vocabulary` (A-reference)
**Callee:** `VectorizerMixin._check_vocabulary` (`text.py:301-307`). It calls
`check_is_fitted(self, 'vocabulary_')` — raising `NotFittedError` when
`vocabulary_` is unset — then `raise ValueError("Vocabulary is empty")` when
`len(self.vocabulary_) == 0`; otherwise returns. Model:
`none ⇒ error notReady`, `some [] ⇒ error emptyIndex`, `some _ ⇒ ok ()`.
`NotFittedError` is a subclass of `ValueError`, so the F2P
`assert_raises(ValueError, cv.get_feature_names)` catches the unfitted case.

### 3.3 `featureList` ↔ the return comprehension (I, content-checked by G-AX/G-CONF)
`[t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]`
sorts the `(term, index)` pairs by index and projects the terms — exactly
`(m.mergeSort (·.2 ≤ ·.2)).map (·.1)`. On a well-formed index (unique indices,
here `0..n-1` for the list path) the ordering is total and the result is the
terms in ascending index order. G-AX confirms `featureList == get_feature_names`
content for established indices.

**Soundness check (G-AX):** `axiom_check.py` constructs real `CountVectorizer`
objects (the concrete `VectorizerMixin` subclass), drives `_validate_vocabulary`,
`_check_vocabulary`, and `get_feature_names` over boundary + fuzzed vocabularies
and fit/unfit states, and asserts each observation (the two attribute writes, the
raise kind, the returned term order) matches the deep models. Imports only
`sklearn` (already in the instance image) + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10908`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the impl region's orchestration (`featureNamesRun`: the
`hasattr`-guarded establishment step, the readiness guard, the index-ordered
projection) to Python over the real repo types, and runs the real patched
`CountVectorizer.get_feature_names` as the oracle.
