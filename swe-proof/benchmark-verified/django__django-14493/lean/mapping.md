# mapping.md — django__django-14493

## Symbol binding (file:line @ base_commit 7272e1963f)
Modeled function: the bounded refinement-pass loop and the post-loop flag test
in `ManifestFilesMixin.post_process(self, paths, dry_run=False, **options)`,
`django/contrib/staticfiles/storage.py:224-280`. The relevant fragment
(`storage.py:262-275` @ base):

```python
        paths = {path: paths[path] for path in adjustable_paths}

        for i in range(self.max_post_process_passes):
            substitutions = False
            for name, hashed_name, processed, subst in self._post_process(paths, adjustable_paths, hashed_files):
                processed_adjustable_paths[name] = (name, hashed_name, processed)
                substitutions = substitutions or subst

            if not substitutions:
                break

        if substitutions:
            yield 'All', None, RuntimeError('Max post-process passes exceeded.')
```

The gold patch inserts `substitutions = False` immediately before the
`for i in range(self.max_post_process_passes):` loop (`storage.py:263` post-patch),
so the post-loop `if substitutions:` test always reads a defined value — even
when `self.max_post_process_passes` is `0` and the loop body never executes.

Lean modeled function name: `postProcess` (names the *behavior* — the outcome of
the bounded refinement loop; `post_process` and `max_post_process_passes` are
already public in the `problem_statement`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `maxPasses : Nat` | `self.max_post_process_passes` (`storage.py:46` default `5`; the subclass under test sets `0`), the iteration count of `for i in range(self.max_post_process_passes)` (`storage.py:264`) |
| `passSubst i : Bool` | the aggregated `substitutions` value computed by pass `i` of the inner loop — `substitutions = substitutions or subst` over `self._post_process(...)` (`storage.py:265-269`), i.e. whether pass `i` still rewrote any reference. The inner loop reinitializes `substitutions = False` each pass, so pass `i`'s value is a function of pass `i` alone (modeled as the input `passSubst i`). |
| `result : Option Bool` | the value the post-loop flag `substitutions` holds at `if substitutions:` (`storage.py:274`). `some b` = the variable is bound to boolean `b`; `none` = the variable is referenced with no value assigned (`UnboundLocalError`). |
| early `break` | `if not substitutions: break` (`storage.py:271-272`) — stop at the first pass producing no substitutions. |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.max_post_process_passes : int` (≥ 0) | `maxPasses : Nat` |
| pass `i`'s aggregated `substitutions or subst` result : `bool` | `passSubst i : Bool` |
| `range(self.max_post_process_passes)` | `List.range maxPasses` |
| `substitutions` bound to `True`/`False` at `if substitutions:` | `some true` / `some false` |
| `substitutions` referenced before assignment (`UnboundLocalError`) | `none` |

### Result-type modeling note
The real post-loop code reads the local `substitutions`. In Python a local that
was only ever assigned inside a loop body is *unbound* when that body never ran;
reading it raises `UnboundLocalError` rather than yielding a value. We model the
flag's runtime state as `Option Bool`: a bound boolean is `some b`, the unbound
state is `none`. The post-patch code assigns `substitutions = False` before the
loop, so the flag is `some _` for every configuration (in particular `some false`
when `maxPasses = 0`); the pre-patch code leaves it `none` when `maxPasses = 0`.
The `if substitutions:` truthiness test and the subsequent
`RuntimeError('Max post-process passes exceeded.')` yield are downstream of this
flag and are not part of the modeled value — the modeled behavior is the flag's
definedness and value, which is exactly what the FAIL_TO_PASS test exercises
(with `max_post_process_passes = 0`, post-processing must complete and report
files as `post-processed` instead of crashing).

### Per-pass abstraction note
The inner loop (`for name, hashed_name, processed, subst in self._post_process(...)`)
performs the actual content rewriting over the collected files and folds each
file's `subst` flag into the pass-level `substitutions` via `or`. Because the
pass reinitializes `substitutions = False` at its top, the pass-level outcome
depends only on that pass's own `_post_process` results; we abstract it as the
input `passSubst i` (the aggregated substitution outcome of pass `i`). This keeps
the model focused on the control-flow defect — the definedness of the post-loop
flag across the bounded loop — without standing up the staticfiles storage stack.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The modeled behavior is the
  loop's own control flow: a flag initialized before the loop, overwritten once
  per pass, with an early `break` when a pass produces no substitutions, and the
  loop bounded by `maxPasses`. The per-pass content work (`self._post_process`)
  is abstracted as the input `passSubst`, not axiomatized. So `axioms = []`,
  `deep_model_references = []`, and `axiom_check.py` is a skip stub (G-AX skips).
- No flag dependency beyond `maxPasses` itself (the iteration bound). The defect
  surfaces precisely when `maxPasses = 0` (zero-trip loop).

## G-LEAK
The solver-visible `problem_statement` publicly names
`ManifestStaticFilesStorage`, `max_post_process_passes`, `post_process`,
`collectstatic`, and even quotes the crashing line `if substitutions:` and the
`local variable 'substitutions' referenced before assignment` traceback. The
spec view names none of the patched file path
(`django/contrib/staticfiles/storage.py`) nor reproduces any gold-diff line; it
describes the abstract loop behavior (bounded refinement passes, early
convergence, a post-loop flag) without narrating the edit or the diagnosis. No
diff marker, no `bug`/`fix`/`unbound` narration.

## Pinned G-CONF fuzz seed
`14493`.
