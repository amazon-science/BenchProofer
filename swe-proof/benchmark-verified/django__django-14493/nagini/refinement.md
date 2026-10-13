# refinement.md — django__django-14493

The operation-by-operation correspondence between `model.py`'s implementation
(the `run_passes` impl region + the deep model `all_changed` and its proof
lemmas) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`django/contrib/staticfiles/storage.py`, in `post_process`):
```
         paths = {path: paths[path] for path in adjustable_paths}
+        substitutions = False
 
         for i in range(self.max_post_process_passes):
             substitutions = False
```

The single added line initialises the loop flag `substitutions` BEFORE the
`for i in range(self.max_post_process_passes)` loop. The loop body and the
post-loop read `if substitutions:` are unchanged. The defect: when
`self.max_post_process_passes == 0` the loop body never runs, so without the
added line `substitutions` is read undefined at `if substitutions:` →
`UnboundLocalError`.

## Operation correspondence

| # | model.py impl op (`run_passes`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `max_passes: int`, `0 <= max_passes <= len(pass_changed)` | `range(self.max_post_process_passes)` | R | the non-negative pass count; `max_passes == 0` ⇔ `max_post_process_passes == 0` (mapping.md §2). |
| 2 | parameter `pass_changed: List[int]` (read-only, `Acc(list_pred, 1/2)` Required AND Ensured) | the per-pass aggregate `subst` of the inner `self._post_process(...)` generator (`substitutions = substitutions or subst`) | R | one 0/1 flag per pass; `pass_changed[i] != 0` ⇔ pass i produced a substitution (mapping.md §2). Fractional, post-state-preserved permission: the loop only READS the per-pass outcomes. |
| 3 | `substitutions = False` BEFORE the loop | the added line `substitutions = False` (the fix) | I | identical concrete initialisation; this is the whole fix. It makes the flag defined on the zero-iteration path. |
| 4 | `i = 0; while i < max_passes:` | `for i in range(self.max_post_process_passes):` | R | identical bounded iteration over `[0, max_passes)`. |
| 5 | `substitutions = pass_changed[i] != 0` | the per-pass aggregation `substitutions = False; for …: substitutions = substitutions or subst` collapsed to the per-pass net outcome | R | the post-pass value of `substitutions` for pass i equals the OR of that pass's inner `subst` values, i.e. `pass_changed[i] != 0` (mapping.md §2). |
| 6 | `if not substitutions: … return False` (early stop) | `if not substitutions: break` (then fall through to `return`/`yield`) | I | identical early-stop control flow: the first change-free pass stops the loop, and the post-loop flag is False. |
| 7 | `i = i + 1` | the `for` advancing to the next pass | I | identical loop advance, reached only when the pass changed (so the loop continues). |
| 8 | `return substitutions` (post-loop) | the post-loop read `if substitutions:` deciding the `RuntimeError('Max post-process passes exceeded.')` sentinel | R | the model returns the exact post-loop flag value the repo consumes; equality of that value transfers the resolved decision. |

`all_changed`, `lemma_unfold`, `lemma_change_free_kills` are the deep model of
the loop's net effect on `substitutions` and the proof obligations that the
verified `run_passes` produces exactly that value; they have no repo
counterpart (proof-only).

## No axioms, no A-reference to a library callee

The changed operation is a definite-assignment + early-stop loop entirely
inside the function under change. It is modeled **deeply** (`all_changed` spelled
out over the per-pass outcomes; the loop verified against it). There is:
- **no A-consumed axiom** — the proof assumes no external callee's contract; and
- **no A-reference** to a stdlib/library callee — the loop calls none whose
  behaviour the model abstracts. `all_changed` abstracts the in-function loop
  itself, validated by axiom_check.py as a *faithfulness* check (model closed
  form == a byte-faithful reference of the real `post_process` loop, exhaustive
  small + boundary + 50000 fuzz), which is the deep-model analogue of G-AX.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely changed — adding
the pre-loop initialisation so the post-loop flag is defined on the zero-pass
path — is step 3, an **I** (identical concrete assignment). The pre-patch
skeleton (`model_prepatch.py`) deletes exactly that line; reading the flag on
the zero-pass path is then undefined, and Nagini rejects it
(definite-assignment failure — the static analogue of `UnboundLocalError`),
which is precisely the spec sensing the change (G-DIFF).

## verify(model) ⇒ resolved

`run_passes` verifies only if (a) it returns on EVERY path including
`max_passes == 0` (the postcondition `Result()` must be a defined bool — a
prepatch that reads the flag undefined cannot verify), and (b) the returned
flag equals the closed form `max_passes > 0 and all_changed(pass_changed,
max_passes)` AND is `False` when `max_passes == 0`. By R (steps 1–8 above) the
verified flag equals the real post-loop `substitutions` value, which the
post-patch repo reads at `if substitutions:` without crashing — including the
`max_post_process_passes == 0` configuration the F2P test exercises. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement, and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because there is no axiom.
