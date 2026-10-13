# mapping.md — scikit-learn__scikit-learn-10908

## Modeled function

| Lean | Python | file:line @ base_commit `67d06b18c6` |
|---|---|---|
| `implementation_getFeatureNames` / `problem_spec_getFeatureNames` / `correct_getFeatureNames` | `CountVectorizer.get_feature_names(self)` — the index-ordered feature-name list (or the documented error) | `sklearn/feature_extraction/text.py:995-999` (post-patch body inserts a vocabulary-establishment step before the availability check) |

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| the vectorizer object's relevant state | `structure VecState` | only the two touched fields are modeled |
| `vocabulary_` attribute present (a `dict {term: int}`) | `learned : Option (List (String × Nat))` | `some v` ↔ attribute set; pairs are (term, index). `hasattr(self, 'vocabulary_')` ↔ `learned.isSome` |
| `vocabulary` constructor parameter (ordered list of terms) | `param : Option (List String)` | `some p` ↔ a list vocabulary was supplied at construction; `none` ↔ not supplied |
| `_validate_vocabulary()` on a list vocabulary | `validateList : List String → Except VErr (List (String × Nat))` | empty → `empty`; repeated term → `dup`; else `{t: i for i,t in enumerate(p)}` i.e. `p.zipIdx` |
| `[t for t,i in sorted(vocab.items(), key=itemgetter(1))]` | `featureNames : List (String × Nat) → List String` | terms in increasing index order; `mergeSort` is a stable sort by `.2` |
| `NotFittedError` | `Except.error VErr.notFitted` | raised by `_check_vocabulary` when no `vocabulary_` is available |
| `ValueError("...empty...")` | `Except.error VErr.empty` | empty vocabulary |
| `ValueError("Duplicate term...")` | `Except.error VErr.dup` | repeated term in a supplied list vocabulary |

The String index of a term in the supplied list (`enumerate`) is modeled by
`List.zipIdx`, which pairs each element with its 0-based position — exactly the
`vocab.setdefault(t, i)` indexing in `_validate_vocabulary`.

## Callee provenance / flag deps

- `_validate_vocabulary` (`text.py:273-298` @ base) — UNCHANGED by this patch.
  Modeled DEEPLY as `validateList` on its **list-vocabulary** branch (the branch
  the F2P custom-vocabulary test and the issue exercise). Flag/shape dependency:
  the modeled branch is the one taken when `self.vocabulary` is a non-Mapping
  iterable of terms (a list). The Mapping/dict-vocabulary and set branches are
  out of the modeled domain (no F2P input exercises them via `get_feature_names`)
  and are not asserted by the deep model. **A-reference** — validated ==
  the real callee by G-AX (`axiom_check.py`).
- `_check_vocabulary` (`text.py:301-307` @ base) — UNCHANGED. Its observable
  effect is folded into the spec: it raises `NotFittedError` when no `vocabulary_`
  is available (→ `notFitted`) and `ValueError` on an empty vocabulary (→ `empty`).
- the index-ordered list comprehension in the post-patch body — the extraction of
  names from `vocabulary_`. Modeled DEEPLY as `featureNames`. **A-reference**.

No UNCHANGED callee is left `opaque`/axiomatized; both relevant callees are
modeled deeply and validated against the real repo by G-AX.

## G-CONF / G-AX fuzz seed

`seed = 10908` (pinned; see conformance_check.py, axiom_check.py, meta.json).
