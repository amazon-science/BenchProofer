# mapping.md — django__django-14053

## Modeled function

| Lean | Python | file:line @ base_commit `179ee13eb3` |
|---|---|---|
| `implementation_postProcess` / `problem_spec_postProcess` / `correct_postProcess` | `HashedFilesMixin.post_process(paths, dry_run, **options)` — the orchestration that runs the per-file processing pass(es) and reports one result per file to the caller | `django/contrib/staticfiles/storage.py:203-249` |

`post_process` is a generator. The modeled behavior is the **sequence of items it
yields** (the `(name, hashed_name, processed)` triples handed to the caller),
**split at the one point in that sequence its caller can distinguish**: the
`self.hashed_files.update(hashed_files)` that commits the accumulated name mapping
to the storage instance (`storage.py:246` at base_commit, `storage.py:257`
post-patch). Items yielded while the passes are still running are delivered with
the shared mapping still holding its pre-call contents; items yielded after that
statement are delivered only once the mapping has been committed. This is
observable rather than internal because the caller is
`collectstatic.Command.collect` (`django/contrib/staticfiles/management/commands/collectstatic.py`),
which raises on the first item whose `processed` is an `Exception` and never
resumes the generator — so it can be handed a strict prefix of the sequence, and
what the storage instance holds at that moment depends on which side of the commit
the prefix ended on. Hence the modeled output is
`OutReport := List OutItem × List OutItem`: `.1` the items yielded before the
commit, `.2` the items yielded after it, each in caller-visible order.
The `dry_run=True` early return (`if dry_run: return`, `storage.py:218-219`, byte-identical
before and after the gold patch) is **not modeled and carries no precondition**: `dry_run`
is not an input to `postProcessModel`, so the modeled function is `post_process` under
`dry_run=False` — the only branch the patch touches, and the branch the graded tests drive
(`'dry_run': False`, test_storage.py:194; no test in the graded set calls `post_process`
with `dry_run=True`). Stating it as a precondition would be false of the spec as written:
`problem_pre_postProcess` constrains `laterPasses` only. Nor does the omission leave a
hole a same-spec rival could hide in — the Lean signature cannot express the dry-run
branch at all, so a rival's faithful refinement leaves it exactly as gold wrote it.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| a record `(name, hashed_name, processed, subst)` produced by `self._post_process(...)` | `PassRecord { name, storedName, outcome, rewrote }` | `rewrote` ↔ the 4th component: the per-pass flag saying that pass still had to rewrite a reference inside that file. It is **not** part of the reported item (`toItem` drops it), but it is what decides whether the run continues past this pass and hence whether the allowance of passes was used up while the run was still moving — which is caller-observable (see the terminal item below). So it is carried on the record. The pass-level fixed point is the input `laterPasses` list (one inner list per executed pass). |
| `name : str` | `name : String` | original source file name (the dict key) |
| `hashed_name` (`str` or `None`) | `storedName : Option String` | `None` ↔ `none` (the error-yield case yields `None`) |
| `processed` — a `bool`, OR an `Exception` instance (the `isinstance(processed, Exception)` branch) | `outcome : Except String Bool` | `bool` ↔ `Except.ok b`; an exception ↔ `Except.error msg`. `isinstance(processed, Exception)` ↔ `PassRecord.isError` (`.error _`). |
| the yielded triple `(name, hashed_name, processed)` | `OutItem := String × Option String × Except String Bool` | the 3-component item reported to the caller (`subst` dropped) |
| the full generator trace, cut at `self.hashed_files.update(hashed_files)` | `OutReport := List OutItem × List OutItem` | `.1` = items yielded before that statement executes (the caller holds them while the storage instance is still un-updated), `.2` = items yielded after it. The cut is a property of the *real* generator's control flow, not of the Lean encoding: driving `post_process` with `itertools.islice` and reading `storage.hashed_files` between items recovers exactly this pair. |
| `adjustable_paths : list[str]` | `adjustable : List String` | files matching `self._patterns`; `name in adjustable_paths` ↔ `adjustable.contains r.name` |
| `processed_adjustable_paths : dict` keyed by name, insertion-ordered, value overwritten in place | `List (String × OutItem)` via `upsertItem` | Python dict preserves insertion order and overwrites value in place on re-assignment to an existing key — exactly `upsertItem` (append-if-new, replace-in-place-if-present). `processed_adjustable_paths.values()` ↔ `dict.map (·.2)`. |

## Callee provenance / flag deps

- The inner per-file processor `self._post_process(paths, adjustable_paths,
  hashed_files)` (`storage.py:251`) is **UNCHANGED** by the gold patch. The patch
  edits only how `post_process` *consumes and re-reports* the records this
  producer yields. Therefore the record stream is taken as an **INPUT** to the
  modeled orchestration (`firstPass`, `laterPasses`), not invoked inside it. There
  is no `opaque` callee and no consumed `_prop` axiom (`axioms` region empty;
  G-AX = skip).
- Pass structure: `post_process` runs `_post_process` once for the first pass,
  then up to `max_post_process_passes` (=5) more times, breaking early when a pass
  reports no substitutions. The orchestration's reporting logic is independent of
  *how many* passes run and *which* records each produces — it is a pure function
  of the observed record lists. We model that record structure directly:
  `firstPass : List PassRecord` and `laterPasses : List (List PassRecord)` (one
  inner list per executed later pass). Because `laterPasses` is by construction the
  passes that *executed*, the `substitutions`-driven early break is already encoded
  in it: every pass but the last reported at least one rewrite (`rewrote = true` on
  some record), since a pass reporting none ends the run. Whether the **last**
  executed pass reported one is free, and that is exactly the difference between
  "the run settled" and "the allowance of passes was used up with the run still
  moving". `conformance_check.py`'s `rand_case` generates `later_passes` under that
  same truncation rule.
- The terminal `yield 'All', None, RuntimeError('Max post-process passes
  exceeded.')` (`storage.py:243-244` at base_commit) is reported exactly when the
  allowance of passes was used up with the run still rewriting — i.e. when the last
  executed later pass reported a rewrite. It is an error item standing for no
  single source file, and it sits *before*
  `self.hashed_files.update(hashed_files)` in the generator, i.e. on the `.1` side.
  It is **not** representable as an ordinary `firstPass`/`laterPasses` record,
  because its presence, position and payload are not free — they are a function of
  the record stream — so it is modeled explicitly (`allowanceItem`, and the
  `unsettled` component of `laterStep`). Fuzzing the real post-patch `post_process`
  body over 20000 randomized record streams, the item was exercised on 5023 of them
  and the model matched on all 20000; the same fuzz against a model without it
  mismatched on exactly those 5023. Both edges of the item are also graded by the
  resolve oracle, on hand-written variants of the post-patch body: reporting it
  whenever ANY pass rewrote (a run-wide flag, instead of the last executed pass's
  own) does **NOT resolve** — 3/3 attempts, F2P 0/1, P2P 6/31; reporting it in
  exactly gold's place but under the name `'all'` instead of `'All'` does **NOT
  resolve** either — 3/3 attempts, P2P 30/31, the one failure being
  `test_import_loop`, which compares the caller's error stream literally against
  `"Post-processing 'All' failed!\n\n"` (test_storage.py:176, the name coming
  straight from the yielded item via collectstatic.py:130). So the guard AND the
  payload are both test-observed, not modeling slack.
- `substitutions` is bound *inside* the `for i in range(self.max_post_process_passes)`
  loop while the `if substitutions:` that guards the terminal item is outside it, so
  an invocation allowed **no** later pass at all raises `UnboundLocalError` and
  produces no report. That is the domain the precondition
  `problem_pre_postProcess : laterPasses ≠ []` excludes; every allowance of one or
  more passes is admissible, including one whose passes report nothing at all.
- Which side of the commit an item falls on is the *only* additional observable
  the pair encoding exposes: within each component the order is the real yield
  order, and the pair carries no information about the storage instance's contents
  beyond the fact that the commit happened between the components. In particular a
  correct alternative implementation is free to reorder work, use a different
  collection type, or flatten the later-pass loops, as long as no item whose value
  a later pass could still change is handed over before every pass has ended.

## G-CONF fuzz seed

`conf_seed = 14053` (pinned; see conformance_check.py and meta.json).
