# refinement.md — django__django-15987

Operation correspondence between the Lean `implementation_fixtureDirs` skeleton
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the changed behavior is modeled deeply with
concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a skip
stub; the R/I legs are differential-tested by G-CONF.)

## `implementation_fixtureDirs` ↔ the collision loop in `Command.fixture_dirs`

The gold patch changes one predicate inside the per-app loop:

```python
 for app_config in apps.get_app_configs():
     app_label = app_config.label
     app_dir = os.path.join(app_config.path, "fixtures")
-    if app_dir in fixture_dirs:
+    if app_dir in [str(d) for d in fixture_dirs]:
         raise ImproperlyConfigured(
             "'%s' is a default fixture directory for the '%s' app "
             "and cannot be listed in settings.FIXTURE_DIRS." % (app_dir, app_label)
         )
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `for c in comps do` | `for app_config in apps.get_app_configs():` | R | `apps.get_app_configs()` ↦ `comps : List Component`; iteration order preserved (first match determines which `app_label` is raised) |
| `c.defaultDir` | `app_dir = os.path.join(app_config.path, "fixtures")` | R | the component's intrinsic default fixtures dir ↦ `defaultDir : String` (always plain text) |
| `collides dirs c.defaultDir` = `dirs.any (fun d => d.value == c.defaultDir)` | `app_dir in [str(d) for d in fixture_dirs]` | R | **This is the changed predicate.** `[str(d) for d in fixture_dirs]` ↦ comparing each entry by its textual form `d.value`; `in` ↦ `List.any (· == ·)`. The `str(...)` coercion is exactly what makes the type tag `isObject` irrelevant to the comparison. |
| `if … then return some c` | `if …: raise ImproperlyConfigured(… app_label …)` | R | raising on the first colliding component ↦ early `return some c` (the offending component, carrying its `label`) |
| `return none` (loop falls through) | the loop completes without raising; the property proceeds to build its list | R | no per-app collision ↦ `none` |

The `for d in fixture_dirs` list-comprehension that produces `[str(d) …]` is
folded into the `collides` membership predicate rather than materialized — the
observable is identical (membership of `app_dir` in the string-coerced set), and
modeling the predicate directly keeps the impl a faithful skeleton of the single
changed `if`.

### Out-of-frame (UNCHANGED by the patch)
* The whole-list duplicate guard `len(fixture_dirs) != len(set(fixture_dirs))`
  above the loop (a separate, unchanged check).
* The message string of `ImproperlyConfigured` (its content is unchanged; only
  whether/which component triggers it is modeled).
* `os.path.isdir(app_dir)` filtering, `dirs.extend(fixture_dirs)`,
  `dirs.append("")`, and the final `[os.path.realpath(d) for d in dirs]` — all
  downstream of and unaffected by the changed predicate.

## Independently-observable behaviors (G-DIFF)

The fix is a single one-line predicate change with one observable behavior, so
there is ONE prepatch:

- `Solution_prepatch.lean`: the collision test only matches configured entries
  supplied as plain text (`!d.isObject && d.value == c.defaultDir`), mirroring
  the pre-patch raw membership `app_dir in fixture_dirs` (a `str` is never `==`
  to a `Path`, so `Path`-typed entries are skipped). The carried gold proof of
  `correct_fixtureDirs` fails to close: when a collision arises only through a
  structured-object entry (`isObject = true`), the spec's `collides` is `true`
  but the buggy loop yields `none`, so the `pos` case is no longer `rfl`.
  Observable: a `Path` duplicate of an app's default fixtures dir goes
  undetected (FAIL_TO_PASS `test_fixture_dirs_with_default_fixture_path_as_pathlib`).
