# mapping.md — django__django-14053

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 179ee13eb37348cd87169a198aec18fedccc8668`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the one unchanged callee whose output stream is the modeled
function's input.

Repo file under change: `django/contrib/staticfiles/storage.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reportCollected (events : List Obs)` | `HashedFilesMixin.post_process(self, paths, dry_run=False, **options)` — `django/contrib/staticfiles/storage.py:203` (changed body lines 226-256) | the modeled changed function: the generator whose *yield stream* is the report passed back to `collectstatic`'s `collect()` |
| `events : List Obs` (read-only input) | the flattened sequence of `(name, hashed_name, processed)` tuples that the **unchanged** callee `self._post_process(...)` emits across the initial pass and every adjustable pass (`storage.py:227`, `238` — both call sites of `_post_process`) | the stream the changed function consumes; see §3 |
| `collect (events)` *(deep model)* | the *post-patch* yield behavior of `post_process`: build `processed_adjustable_paths` (an insertion-ordered `dict` keyed by `name`), overwriting on each later observation, then `yield from processed_adjustable_paths.values()` (`storage.py` post-patch lines 229-262) | pure spec: the order-preserving, keep-last collapse of the stream by key |
| `upsert`, `collectStep` *(pure)* | `processed_adjustable_paths[name] = (name, hashed_name, processed)` — a Python `dict` assignment (`storage.py` post-patch lines 234, 245) | pure spec: one order-preserving keyed upsert |

There are **no axioms** in this bundle and no `axiom_check.py`: the changed
function's new behavior (dict-keyed dedup of its own yield stream) is modeled
**deeply** by `collect`/`upsert` over the input stream `events`. The only callee
involved, `_post_process`, is **unchanged** by the patch and is *not*
axiomatized — its entire relevant effect is the value of the read-only input
`events` (§3). G-AX therefore reports `skip` (no axioms); G-CONF carries the
soundness load.

The pre-patch repo behavior the change removes (refinement audit only, not in
the consumer spec view): the two unconditional `yield name, hashed_name,
processed` statements (`storage.py:228` and `storage.py:239` pre-patch) that
re-emit the same `name` once per pass. `Solution_prepatch.lean` reproduces that
"yield every observation raw" skeleton and fails both `ensures` clauses.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one yielded record `(name, hashed_name, processed)` restricted to the two fields that drive the dedup (`name` as identity key; `hashed_name` as the reported value) | `Obs = Int × Int` | `name` (a `str` path) ↔ `fst : Int` via an injective interning of the finite set of paths present in one `post_process` call (mapping.md §3 — equal paths ↔ equal ints, distinct ↔ distinct); `hashed_name` (a `str`) ↔ `snd : Int` via the same interning of the finite set of hashed names. The dedup logic observes only key-equality and last-value, never string content, so the interning is faithful. |
| the full ordered stream of records, flattened across all passes | `events : List Obs` | Python list-of-tuples ↔ `List Obs`, element-wise via the row bijection; `len` ↔ `.length`; order preserved |
| the post-patch return: `list(post_process(...))` (the materialized generator) | `out : List Obs` | element-wise via the row bijection; order preserved |

`processed : bool` and the per-pass `subst : bool` are **not** carried into
`Obs`: they affect only *control* (which records the callee emits and when the
pass loop stops), and that control is fully reflected in the *contents and order*
of `events`. The two fields that the patched dedup keys/values on are `name`
(key) and `hashed_name` (value) — exactly `fst`/`snd`. The exception leg
(`isinstance(processed, Exception)`) is discussed in §3.3.

## 3. Callee provenance and the input-stream abstraction

### 3.1 `_post_process` is the unchanged event producer (NOT axiomatized)
`self._post_process(paths, adjustable_paths, hashed_files)` (`storage.py:251`) is
**not modified** by the gold patch (the patch touches only `post_process`,
`storage.py:203-262`). Its only role in the modeled behavior is to *produce* the
stream of `(name, hashed_name, processed, subst)` tuples. The modeled function
consumes that stream; it is the read-only input `events` (with `subst`/`processed`
projected out per §2). Because the callee is unchanged and only its *output
sequence* matters — not any contract on it — there is nothing to axiomatize: any
concrete stream is a valid `events`. G-CONF fuzzes over all stream shapes the
real driver can produce (§4).

### 3.2 The two post-patch behaviors that `collect` captures
The gold patch makes `post_process`:
1. **not** yield an adjustable file during the initial pass or any adjustable
   pass; instead record it into `processed_adjustable_paths[name] = (name,
   hashed_name, processed)` — an insertion-ordered dict, overwriting on repeats;
2. after all passes, `yield from processed_adjustable_paths.values()`.

Net observable for the adjustable files: each `name` is reported **exactly once**,
in **first-encounter order**, carrying the **last** `(hashed_name, processed)`
observed for it. That is precisely `collect events` = `events.foldl collectStep
[]` (order-preserving, keep-last upsert) and `collect_nodup` (no key twice).

### 3.3 Scope: adjustable files (the F2P-discriminating leg)
The F2P assertion `assertCountEqual(stats['post_processed'], set(stats['post_processed']))`
demands **no `name` is reported twice**. The pre-patch bug duplicated exactly the
**adjustable** files (each yielded once per pass). Non-adjustable files were and
remain yielded once (initial pass only); exceptions (`isinstance(processed,
Exception)`) are still yielded immediately post-patch. The model scopes to the
adjustable-file stream — the locus of the change and of the duplicate yields —
where `events` is the sequence of adjustable observations across all passes and
`out` is the deduped report. The non-adjustable/exception legs are pass-through
(identity, single yield) under both pre- and post-patch and carry no
discriminating behavior, so they are excluded from `Obs` (mapping §2) rather than
modeled redundantly. G-CONF's oracle exercises the **real** patched
`post_process` over streams that include non-adjustable and exception records and
confirms the adjustable-file report equals the shadow's `collect`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14053`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`collect`/`upsert` (R/I-tagged ops) to Python over the real repo types; the
oracle drives the **real patched** `HashedFilesMixin.post_process` (gold patch
applied by the harness) with a stub `_post_process` emitting the fuzzed stream,
and compares the adjustable-file report against the shadow over ≥10⁵ inputs.
