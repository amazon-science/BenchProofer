# refinement.md — scikit-learn__scikit-learn-13124

The operation-by-operation correspondence between `model.py`'s implementation
(the `per_class_draw_states` impl region and the deep `state_stream` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (abstracted callee — **A-consumed** where the proof uses the callee's
`Ensures`, **A-reference** where a deep model / abstract symbol is validated
against the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `StratifiedKFold._make_test_folds`

Gold hunk (`sklearn/model_selection/_split.py:622-623`):
```
  def _make_test_folds(self, X, y=None):
-     rng = self.random_state
+     rng = check_random_state(self.random_state)
```

The single changed line decides whether the per-class loop (lines 653-656,
`per_cls_cvs = [KFold(..., random_state=rng).split(...) for count in y_counts]`)
draws each class from **one shared, advancing** source (fix) or **re-seeds a
fresh source from the identical raw seed** for every class (bug). model.py
captures exactly that data-flow in `per_class_draw_states`.

| # | model.py impl op (`per_class_draw_states`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `seed: int` | `self.random_state` (an `int` seed in the tested configuration) | R | identity on the integer seed (mapping.md §2). |
| A2 | parameter `n_classes: int` | the per-class loop length `len(y_counts)` | R | the number of classes; identity on a non-negative count (mapping.md §2). |
| A3 | `start = seed_state(seed)` (the source's initial state, computed **once**) | `rng = check_random_state(self.random_state)` — convert the seed to a source **once** | A-reference | `check_random_state(int)` is `RandomState(seed)`; `seed_state(seed)` is that source's initial state. Abstract symbol, validated against the real callee by G-AX (mapping.md §3.1). The "once" is the load-bearing skeleton fact: the conversion is hoisted out of the per-class loop. |
| A4 | the loop threads one `cur`, emitting `cur` for each class then `cur = advance(cur)` — `Result()[k]` is the k-fold advance of `start` | the per-class loop draws each class from the **same** `rng`, whose state advances per draw; `Result()` ≅ the per-class draw stream | A-reference | `advance` abstracts the per-draw state move of the one shared `RandomState` (numpy `.shuffle` in `KFold._iter_test_indices`). The deep model `state_stream` IS the advancing stream; G-AX validates that the real shared source advances (per-class draws differ) — A-reference 1, §3.1. |
| A5 | `Result()` returned (a `List[int]` of per-class draw states) | the assembled `per_cls_cvs` (one split per class) feeding `test_folds` | R | element k ↔ class k's draw; the downstream fold bookkeeping (`test_folds`, trim, `np.unique`) is unchanged and orthogonal (mapping.md §2). |

The discriminating content of the change — each class draws from a **distinct,
advanced** state rather than the **same** state — lives in
`Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes))`
(model) ⇔ sharing the one `check_random_state(...)` source across the per-class
loop (real). The pre-patch keeps `rng = self.random_state` (the raw int),
re-converting a fresh source from the identical seed for every class;
`model_prepatch.py` reproduces that (every class emits `seed_state(seed)`) and
**fails** the postcondition above — exactly the spec sensing the change
(G-DIFF), because a constant list `[start, start, …]` cannot be proven equal to
the advancing stream `[start, advance(start), …]` for the abstract `advance`.

## B. No consumed axioms; no kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. There is **no A-consumed axiom**: the
proof consumes no callee `Ensures`. `seed_state` and `advance` are abstract pure
symbols with no claimed contract; the postcondition and the front-recursive
`state_stream` are phrased purely structurally over them, and the proof goes
through by definitional unfolding of `state_stream` (no value claim about
`seed_state`/`advance` is needed). The single changed operation — whether the
per-class source advances or repeats — is modelled **deeply** (`state_stream`
spelled out as the advancing fold, threaded by the impl loop), not hidden behind
an axiom about the function under change. The abstract symbols are the
**A-reference**: their real counterparts (numpy `RandomState` seeded by
`check_random_state`, advanced by per-class `.shuffle`) are validated by G-AX,
including the discriminating fact that `advance` is a genuine state move.

## C. verify(model) ⇒ resolved

`per_class_draw_states` verifies only if its output is the advancing stream
`state_stream(seed_state(seed), n_classes)` (A3+A4): class k draws from the
k-fold-advanced state, never all from one fixed state. By R (int seed identity;
class-count identity; per-class-draw ↔ element correspondence) the verified
function equals the patched `_make_test_folds`'s per-class source handling on
the tested inputs; by G-AX the abstract `advance`/`seed_state` correspond to a
real advancing source (so the per-class draws genuinely differ) and the real
patched `StratifiedKFold` yields seed-dependent sorted test sets. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: A-reference soundness (G-AX)
and refinement fidelity (this document, G-EQ).
