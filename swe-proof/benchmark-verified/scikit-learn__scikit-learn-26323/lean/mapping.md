# mapping.md — scikit-learn__scikit-learn-26323

## Symbol binding (file:line @ base_commit 586f4318ffcdfbd9a1093f35ad43e81983740b66)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_setOutput` / `problem_spec_setOutput` / `correct_setOutput` | `ColumnTransformer.set_output` (the propagation of the output container to the contained transformers and the fall-back transformer) | `sklearn/compose/_column_transformer.py:275-306` (added lines 296-298 post-patch) |
| `Transformer` (pure helper) | a transformer slot: an estimator object, or one of the reserved strings `"passthrough"`/`"drop"` | `_column_transformer.py:301` (the `{"passthrough","drop"}` set) |
| `setOutput` (pure helper) | `_safe_set_output(estimator, transform=transform)` applied to one slot (no-op on a sentinel) | `sklearn/utils/_set_output.py:244` |
| input `transformers : List Transformer` | the flattened `trans` elements of `chain(self.transformers, getattr(self,"transformers_",[]))` | `_column_transformer.py:296-302` |
| input `remainder : Transformer` | `self.remainder` (a transformer or the `"passthrough"`/`"drop"` string) | `_column_transformer.py:304 (post-patch)` |
| input `transform : String` | the `transform` keyword argument (`"default"`/`"pandas"`/…) | `_column_transformer.py:275` |
| `result : List Transformer × Transformer` | the composite after `set_output` returns `self` — its contained transformers and remainder, with output containers configured | `_column_transformer.py:306` |

The modeled behavior is the **output-container propagation** in `set_output`. The
patch's only behavior change is whether the fall-back `remainder` estimator also
receives the chosen container; this is the only behavior the FAIL_TO_PASS test
observes.

### What the function does (base_commit, pre-patch)

```python
def set_output(self, *, transform=None):
    super().set_output(transform=transform)          # records the choice on self
    transformers = (
        trans
        for _, trans, _ in chain(self.transformers, getattr(self, "transformers_", []))
        if trans not in {"passthrough", "drop"}
    )
    for trans in transformers:
        _safe_set_output(trans, transform=transform) # propagate to each contained transformer
    return self                                      # <-- remainder NEVER configured (the bug)
```

Post-patch adds, just before `return self`:

```python
    if self.remainder not in {"passthrough", "drop"}:
        _safe_set_output(self.remainder, transform=transform)
```

`_safe_set_output(est, transform=transform)` calls `est.set_output(transform=...)`
which records the chosen output container on the estimator (unless the estimator
cannot transform, in which case it is a no-op — see flag dependencies below). On
the reserved strings `"passthrough"`/`"drop"` the call is never made.

### Lean modeling

- A transformer slot is modeled by `Transformer`: `Transformer.est id output` for
  an estimator (with an opaque identity `id : Nat` and its current output-container
  string `output : String`), and `Transformer.passthrough` / `Transformer.drop`
  for the two reserved sentinels. `id` distinguishes distinct estimators; only
  `output` is mutated by the modeled behavior.
- `setOutput transform t` deeply models `_safe_set_output(t, transform=transform)`:
  on `est id _` it returns `est id transform` (the container is recorded); on a
  sentinel it returns the slot unchanged. This is the deep model of the changed
  op, so it is an A-reference candidate that is in fact never axiomatized — the
  whole impl is R/I, validated by G-CONF.
- `super().set_output` records the choice on the composite itself; that field is
  orthogonal to the modeled propagation and to the F2P test, so it is not modeled.
- The contained collection (`chain(self.transformers, transformers_)` flattened)
  and `self.remainder` enter as grounded inputs. The membership filter on the
  contained collection is subsumed by `setOutput` being a no-op on sentinels.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| an estimator object (with an output-container config) | `Transformer.est (id : Nat) (output : String)` | `id` = object identity; `output` = current container string |
| the reserved string `"passthrough"` | `Transformer.passthrough` | sentinel, no config |
| the reserved string `"drop"` | `Transformer.drop` | sentinel, no config |
| the contained transformers (chain, flattened) | `transformers : List Transformer` | element-wise, order-preserving |
| `self.remainder` | `remainder : Transformer` | identity |
| the `transform` keyword | `transform : String` | identity |
| `(configured transformers, configured remainder)` | `result : List Transformer × Transformer` | element-wise, order-preserving |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** `_safe_set_output` (the per-slot propagation) is
  the op the patch invokes on the remainder, and it is modeled DEEPLY by
  `setOutput`; SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op. The
  `axioms` region is empty and **G-AX skips**.
- **`_safe_set_output` no-op-when-cannot-transform flag.** `_safe_set_output`
  returns early (no config recorded) if the estimator has neither `transform` nor
  `fit_transform`. In the modeled world the relevant inputs are actual
  transformers (the F2P uses `VarianceThreshold`, which transforms), so `setOutput`
  recording the container on every `est` is the faithful behavior. Slots that
  cannot transform are not part of the modeled domain (they would never appear in
  `self.transformers` of a fitted `ColumnTransformer`); G-CONF fuzzes estimator
  slots that transform, matching this domain.
- `super().set_output` is UNCHANGED by the patch and configures only the composite
  itself; orthogonal to the modeled propagation, not modeled, constrains no output
  component the spec leaves free.

## G-CONF fuzz seed

Pinned LCG seed: **26323** (see `conformance_check.py` `SEED`). Corpus: randomized
`transformers` lists mixing estimator slots (random identity + random current
container) and the two sentinels, a randomized `remainder` slot (estimator or
sentinel), and a random `transform` string, plus hand-picked edge cases (empty
`transformers`; `remainder` = each sentinel; `remainder` = estimator whose current
container already equals `transform`; the F2P configuration: one `VarianceThreshold`
contained transformer with a `VarianceThreshold` remainder, `transform="pandas"`
then `"default"`). The R/I shadow of `implementation_setOutput` is diffed against
an in-process replica of the POST-PATCH `set_output` behavior over ≥1e5 fuzzed
inputs.
